#!/usr/bin/env python3
"""ontology_fit.py — the ontology-fit test (set-valued placement).

ONE question, answered mechanically:

    Can THIS model place concepts from THIS text into THIS ontology's upper
    classes, CONSISTENTLY enough to be usable?

Run it as part of ontology setup — whenever a specification is added, a
specification changes, the ontology changes, or the model changes.

WHY PLACEMENT INTO A SET, NOT CLASSIFICATION INTO ONE LABEL
    Naming is unbounded, so inter-run agreement on a free-text name is not a
    quantity. That much is why this test exists at all. But the first draft
    over-corrected into single-label classification, on the premise that a
    closed set "has a definite right one". THAT PREMISE IS FALSE. `developer`
    is an Agent AND a Role, and instantiated, a Person. LKIF is itself a
    multiple-inheritance ontology (Person is a subclass of Agent and of
    Natural_Object), so one label cannot represent a correct placement.
    Forcing one does two bad things: it throws away the structure that is the
    whole reason to use an ontology, and it MANUFACTURES DISAGREEMENT — two
    runs answering `Agent` and `Role` are both right, and a low agreement
    score would be an artifact of the forced choice, not a property of the
    model.

    So the task is: return the MOST SPECIFIC classes in the closed set that
    subsume this concept — one or more. The answer is a SET. The set is still
    drawn from a closed vocabulary, which is what keeps it measurable.

WHAT IT MEASURES
    SELF-CONSISTENCY ONLY. Mean pairwise Jaccard between the sets returned by
    repeated runs on the same concept, with a bootstrap confidence interval
    over concepts and a Monte-Carlo p-value against an explicitly stated null.

WHAT IT CANNOT MEASURE
    * ⛔ CORRECTNESS. There is no ground truth in this run and none is
      claimed. A stable-but-WRONG mapping — every concept placed under the
      same wrong classes, every time — scores a PERFECT 1.0. Consistency is
      necessary, never sufficient. The dry run exists to let a human write
      down expected placements FIRST so that correctness can be judged
      separately, as a pre-registration.
    * Whether the ontology is the right ontology. The NONE_OF_THESE rate is a
      coverage signal, nothing more.
    * Whether a human would agree with any of it.
    * Steps 2 (PARENT) and 3 (MINT) of the concept phase.

THE REFERENCE LINE IS NOT CHANCE
    The MIREL project's annotated ECHR data gives concept-vocabulary Jaccard
    of 0.30 / 0.24 / 0.29 between pairs of TRAINED HUMAN ANNOTATORS on legal
    text. The question is therefore "is this within reach of two trained
    people", not "is this better than guessing". ⚠️ That band is a reference
    from a DIFFERENT corpus and a DIFFERENT ontology, and it measures
    agreement between two different people, whereas this measures one model
    against itself — an easier task. It is a rough floor, not a strict
    baseline, and not a pass mark.

FAIL-CLOSED CONTRACT
    Every failure raises. There is no code path on which "the API broke", "the
    ontology did not load", "nothing parsed" or "the closed set is empty" can
    come out looking like a clean result. `--self-test` proves each check goes
    RED for its own named reason before you are asked to trust its GREEN.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys
import urllib.request
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(HERE, "ontology_fit_config.json")

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
NONE_LABEL = "NONE_OF_THESE"


# --------------------------------------------------------------------------
# Errors.  Every one of these is a REFUSAL TO REPORT, never a warning.
# --------------------------------------------------------------------------
class OntologyFitError(RuntimeError):
    """Base: the test could not be run, so there is no result."""


class ConfigError(OntologyFitError):
    pass


class OntologyParseError(OntologyFitError):
    """Ontology missing, unreadable, or yielded zero classes (parse canary)."""


class ClosedSetError(OntologyFitError):
    """The closed set is empty or degenerate."""


class CorpusError(OntologyFitError):
    """Corpus missing, unreadable, empty, or too small to sample from."""


class ProviderError(OntologyFitError):
    """The model call failed, or produced nothing."""


class ResponseParseError(OntologyFitError):
    """A response could not be resolved to a subset of the closed set."""


class CostGateError(OntologyFitError):
    """Estimated spend exceeds the configured ceiling.  Nothing was sent."""


class DegenerateAgreementError(OntologyFitError):
    """Agreement is undefined or uninformative as computed."""


# ==========================================================================
# 1.  Ontology loading.  Turtle + RDF/XML, stdlib only (no rdflib).
#
# ⚠️ This is not a stylistic choice. EVERY owl:imports in LKIF-Core is dead:
# estrellaproject.org 301s and then 404s. Any loader that resolves imports
# fails to load LKIF at all. Parsing vendored module files directly is the
# only thing that works.
# ==========================================================================
_WS_RE = re.compile(r"(?:\s+|#[^\n]*)+")
_IRIREF_RE = re.compile(r"<([^<>\"{}|^`\\\x00-\x20]*)>")
_PNAME_RE = re.compile(r"([A-Za-z_][\w.\-]*)?:([\w\-.%]*)")
_BNODE_RE = re.compile(r"_:([\w][\w.\-]*)")
_NUM_RE = re.compile(r"[+-]?(?:\d+\.\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?"
                     r"|\d+(?:[eE][+-]?\d+)?)")
_ESCAPES = {"t": "\t", "b": "\b", "n": "\n", "r": "\r", "f": "\f",
            '"': '"', "'": "'", "\\": "\\"}


def _unescape(s):
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c != "\\":
            out.append(c)
            i += 1
            continue
        nxt = s[i + 1] if i + 1 < len(s) else ""
        if nxt in _ESCAPES:
            out.append(_ESCAPES[nxt])
            i += 2
        elif nxt in ("u", "U"):
            n = 4 if nxt == "u" else 8
            out.append(chr(int(s[i + 2:i + 2 + n], 16)))
            i += 2 + n
        else:
            out.append(nxt)
            i += 2
    return "".join(out)


class _TurtleParser:
    """Just enough Turtle to recover an OWL class hierarchy.

    Deliberately not a conformant Turtle processor: it recognises prefixes,
    IRIs, blank-node property lists, collections and literals, which is what
    an OWL/Turtle ontology serialisation actually uses.  Anything it cannot
    tokenise raises — a silent skip is how a parse canary gets defeated.
    """

    def __init__(self, text, base=""):
        self.s = text
        self.i = 0
        self.base = base
        self.prefixes = {}
        self.triples = []
        self._bn = 0

    def _skip(self):
        m = _WS_RE.match(self.s, self.i)
        while m:
            self.i = m.end()
            m = _WS_RE.match(self.s, self.i)

    def _eof(self):
        self._skip()
        return self.i >= len(self.s)

    def _peek(self, n=1):
        self._skip()
        return self.s[self.i:self.i + n]

    def _expect(self, ch):
        if self._peek(len(ch)) != ch:
            raise OntologyParseError(
                f"turtle: expected {ch!r} at offset {self.i}, saw "
                f"{self.s[self.i:self.i + 30]!r}")
        self.i += len(ch)

    def _fresh_bnode(self):
        self._bn += 1
        return f"_:auto{self._bn}"

    def _resolve_pname(self, prefix, local):
        prefix = prefix or ""
        if prefix not in self.prefixes:
            raise OntologyParseError(f"turtle: unknown prefix {prefix!r}:")
        return self.prefixes[prefix] + _unescape(local)

    def _literal(self):
        for q in ('"""', "'''", '"', "'"):
            if self.s.startswith(q, self.i):
                j = self.i + len(q)
                buf = []
                while True:
                    if j >= len(self.s):
                        raise OntologyParseError("turtle: unterminated literal")
                    if self.s[j] == "\\":
                        buf.append(self.s[j:j + 2])
                        j += 2
                        continue
                    if self.s.startswith(q, j):
                        break
                    buf.append(self.s[j])
                    j += 1
                self.i = j + len(q)
                val = _unescape("".join(buf))
                if self._peek(2) == "^^":
                    self.i += 2
                    self._term()
                elif self.s[self.i:self.i + 1] == "@":
                    m = re.match(r"@[A-Za-z\-0-9]+", self.s[self.i:])
                    self.i += m.end()
                return ("lit", val)
        raise OntologyParseError("turtle: not a literal")

    def _term(self):
        self._skip()
        c = self.s[self.i:self.i + 1]
        if c == "<":
            m = _IRIREF_RE.match(self.s, self.i)
            if not m:
                raise OntologyParseError(f"turtle: bad IRI at {self.i}")
            self.i = m.end()
            iri = m.group(1)
            if iri and not re.match(r"^[A-Za-z][A-Za-z0-9+.\-]*:", iri):
                iri = self.base + iri
            return ("iri", iri)
        if c in "\"'":
            return self._literal()
        if self.s.startswith("_:", self.i):
            m = _BNODE_RE.match(self.s, self.i)
            self.i = m.end()
            return ("bnode", "_:" + m.group(1))
        if c == "[":
            self.i += 1
            node = self._fresh_bnode()
            if self._peek() == "]":
                self.i += 1
                return ("bnode", node)
            self._predicate_object_list(node)
            self._expect("]")
            return ("bnode", node)
        if c == "(":
            self.i += 1
            items = []
            while self._peek() != ")":
                items.append(self._term())
            self.i += 1
            head = ("iri", RDF + "nil")
            for it in reversed(items):
                node = self._fresh_bnode()
                self.triples.append((node, RDF + "first", it))
                self.triples.append((node, RDF + "rest", head))
                head = ("bnode", node)
            return head
        m = _NUM_RE.match(self.s, self.i)
        if m and c not in "abcdefghijklmnopqrstuvwxyz":
            self.i = m.end()
            return ("lit", m.group(0))
        if self.s.startswith("true", self.i) or self.s.startswith("false",
                                                                 self.i):
            m2 = re.match(r"(true|false)\b", self.s[self.i:])
            if m2:
                self.i += m2.end()
                return ("lit", m2.group(1))
        m = _PNAME_RE.match(self.s, self.i)
        if m:
            self.i = m.end()
            return ("iri", self._resolve_pname(m.group(1), m.group(2)))
        raise OntologyParseError(
            f"turtle: unparsable term at offset {self.i}: "
            f"{self.s[self.i:self.i + 40]!r}")

    def _verb(self):
        self._skip()
        if self.s[self.i] == "a" and (self.i + 1 >= len(self.s)
                                      or not re.match(r"[\w:]",
                                                      self.s[self.i + 1])):
            self.i += 1
            return RDF + "type"
        kind, val = self._term()
        if kind != "iri":
            raise OntologyParseError(f"turtle: non-IRI predicate {val!r}")
        return val

    def _predicate_object_list(self, subject):
        while True:
            self._skip()
            if self._peek() in ("]", ""):
                return
            pred = self._verb()
            while True:
                obj = self._term()
                self.triples.append((subject, pred, obj))
                if self._peek() == ",":
                    self.i += 1
                    continue
                break
            if self._peek() == ";":
                while self._peek() == ";":
                    self.i += 1
                continue
            return

    def parse(self):
        while not self._eof():
            c = self._peek()
            low = self.s[self.i:self.i + 7].lower()
            if c == "@" or low.startswith("prefix") or low.startswith("base"):
                if c == "@":
                    self.i += 1
                word = re.match(r"[A-Za-z]+", self.s[self.i:])
                if not word:
                    raise OntologyParseError("turtle: bad directive")
                kw = word.group(0).lower()
                self.i += word.end()
                if kw == "prefix":
                    self._skip()
                    m = _PNAME_RE.match(self.s, self.i)
                    if not m:
                        raise OntologyParseError("turtle: bad @prefix name")
                    self.i = m.end()
                    kind, iri = self._term()
                    self.prefixes[m.group(1) or ""] = iri
                elif kw == "base":
                    kind, iri = self._term()
                    self.base = iri
                else:
                    raise OntologyParseError(f"turtle: unknown directive {kw}")
                if self._peek() == ".":
                    self.i += 1
                continue
            kind, subj = self._term()
            if kind not in ("iri", "bnode"):
                raise OntologyParseError("turtle: literal in subject position")
            self._predicate_object_list(subj)
            self._expect(".")
        return self.triples


def _triples_from_turtle(text):
    return _TurtleParser(text).parse()


def _tag_to_iri(tag):
    if tag.startswith("{"):
        ns, local = tag[1:].split("}", 1)
        return ns + local
    return tag


def _triples_from_rdfxml(text):
    """RDF/XML — enough of it for owl:Class / rdfs:subClassOf / annotations."""
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise OntologyParseError(f"rdf/xml: {e}") from e
    base = root.attrib.get("{http://www.w3.org/XML/1998/namespace}base", "")
    triples = []

    def about(el):
        a = el.attrib
        if f"{{{RDF}}}about" in a:
            return a[f"{{{RDF}}}about"]
        if f"{{{RDF}}}ID" in a:
            return base + "#" + a[f"{{{RDF}}}ID"]
        return None

    for el in root.iter():
        subj = about(el)
        if subj is None:
            continue
        if el.tag != f"{{{RDF}}}Description":
            triples.append((subj, RDF + "type", ("iri", _tag_to_iri(el.tag))))
        for child in el:
            pred = _tag_to_iri(child.tag)
            res = child.attrib.get(f"{{{RDF}}}resource")
            if res is not None:
                triples.append((subj, pred, ("iri", res)))
            elif child.text and child.text.strip():
                triples.append((subj, pred, ("lit", child.text.strip())))
            else:
                for gc in child:
                    gs = about(gc)
                    if gs:
                        triples.append((subj, pred, ("iri", gs)))
    return triples


class OntologyClass:
    __slots__ = ("iri", "name", "gloss", "parents", "module", "depth",
                 "vocabulary_only")

    def __init__(self, iri, name, gloss, parents, module):
        self.iri = iri
        self.name = name
        self.gloss = gloss
        self.parents = parents
        self.module = module
        self.depth = None
        self.vocabulary_only = False


def _module_of(iri):
    ns = iri.split("#")[0]
    seg = ns.rstrip("/").split("/")[-1]
    return re.sub(r"\.(owl|ttl|rdf|xml)$", "", seg) or "?"


def _local_name(iri):
    if "#" in iri:
        return iri.rsplit("#", 1)[1]
    return iri.rstrip("/").rsplit("/", 1)[-1]


def parse_ontology_text(text, fmt, source_label):
    if fmt == "turtle":
        triples = _triples_from_turtle(text)
    elif fmt == "rdfxml":
        triples = _triples_from_rdfxml(text)
    else:
        raise ConfigError(f"unknown ontology format {fmt!r}")
    declared, labels, comments = {}, {}, {}
    parents = defaultdict(set)
    for s, p, o in triples:
        kind, val = o
        if p == RDF + "type" and kind == "iri" and val in (OWL + "Class",
                                                           RDFS + "Class"):
            if not s.startswith("_:"):
                declared.setdefault(s, True)
        elif p == RDFS + "label" and kind == "lit":
            labels.setdefault(s, val)
        elif p == RDFS + "comment" and kind == "lit":
            comments.setdefault(s, val)
        elif p == RDFS + "subClassOf" and kind == "iri":
            parents[s].add(val)
    out = {}
    for iri in declared:
        if iri.startswith(OWL) or iri.startswith(RDFS) or iri.startswith(RDF):
            continue          # owl:Thing et al. are not domain upper classes
        out[iri] = OntologyClass(iri=iri,
                                 name=labels.get(iri) or _local_name(iri),
                                 gloss=comments.get(iri, ""),
                                 parents=set(parents.get(iri, ())),
                                 module=_module_of(iri))
    if not out:
        raise OntologyParseError(
            f"PARSE CANARY: {source_label} parsed to ZERO classes. "
            "An ontology with no classes is an error, not an empty result — "
            "the closed set would be empty and every downstream number "
            "meaningless.")
    return out


def _read_module(mod, src):
    """Local cache first; download only if the config allows it."""
    path = None
    if src.get("path"):
        base = src["path"] if os.path.isabs(src["path"]) \
            else os.path.join(HERE, src["path"])
        cand = os.path.join(base, mod + src.get("suffix", ".ttl"))
        if os.path.exists(cand):
            path = cand
    if path:
        with open(path, encoding="utf-8") as f:
            return f.read(), path
    tmpl = src.get("url_template")
    if not tmpl:
        raise OntologyParseError(
            f"ontology module {mod!r}: not in the local cache "
            f"({src.get('path')}) and no url_template configured")
    if not src.get("allow_download", False):
        raise OntologyParseError(
            f"ontology module {mod!r}: absent from the local cache and "
            "allow_download is false — refusing to guess at its content")
    url = tmpl.format(module=mod)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            text = r.read().decode("utf-8")
    except Exception as e:
        raise OntologyParseError(f"ontology module {mod!r}: {url}: {e}") from e
    if src.get("path"):
        base = src["path"] if os.path.isabs(src["path"]) \
            else os.path.join(HERE, src["path"])
        os.makedirs(base, exist_ok=True)
        cand = os.path.join(base, mod + src.get("suffix", ".ttl"))
        with open(cand, "w", encoding="utf-8") as f:
            f.write(text)
        return text, cand
    return text, url


class Ontology:
    def __init__(self, name, classes, modules_loaded, sources):
        self.name = name
        self.classes = classes
        self.modules_loaded = modules_loaded
        self.sources = sources

    @property
    def total_class_count(self):
        return len(self.classes)


def load_ontology(cfg):
    oc = cfg["ontology"]
    src = oc["source"]
    fmt = src.get("format", "turtle")
    tiers = oc.get("tiers") or list(oc.get("modules", {}))
    mods = []
    for t in tiers:
        if t not in oc["modules"]:
            raise ConfigError(f"tier {t!r} is not defined in ontology.modules")
        mods += oc["modules"][t]
    vocab_only = list(oc.get("vocabulary_only_modules", []))
    for m in vocab_only:
        if m not in mods:
            mods.append(m)
    if not mods:
        raise ConfigError("no ontology modules selected")

    classes, sources = {}, []
    for m in mods:
        text, where = _read_module(m, src)
        got = parse_ontology_text(text, fmt, where)
        sources.append({"module": m, "source": where, "classes": len(got)})
        for iri, c in got.items():
            # MERGE, do not first-wins. LKIF re-declares foreign classes in
            # importing modules with only their local axioms — role.ttl
            # declares action:Action with no rdfs:subClassOf at all. Keeping
            # the first declaration seen silently orphans Action from Process
            # and every depth below it is then wrong.
            if iri in classes:
                cur = classes[iri]
                cur.parents |= c.parents
                if not cur.gloss:
                    cur.gloss = c.gloss
            else:
                classes[iri] = c
    for c in classes.values():
        if c.module in vocab_only:
            c.vocabulary_only = True

    # Depth over the SELECTED set only, by relaxation to a fixpoint. (Not
    # recursion with memoisation: a memo filled while a cycle is unwound
    # caches a value that depends on traversal order.)
    INF = float("inf")
    depth = {iri: (0 if not [p for p in c.parents if p in classes] else INF)
             for iri, c in classes.items()}
    changed, rounds = True, 0
    while changed and rounds <= len(classes) + 1:
        changed, rounds = False, rounds + 1
        for iri, c in classes.items():
            ps = [depth[p] for p in c.parents if p in classes]
            if ps and 1 + min(ps) < depth[iri]:
                depth[iri], changed = 1 + min(ps), True
    for iri in classes:
        classes[iri].depth = 0 if depth[iri] == INF else depth[iri]

    ont = Ontology(oc.get("name", "ontology"), classes, mods, sources)
    if ont.total_class_count == 0:
        raise OntologyParseError("PARSE CANARY: zero classes across all modules")
    return ont


def build_closed_set(ont, cfg):
    """The vocabulary a placement may be drawn from.  Closed and declared.

    Two selection modes:

    * `include_classes` non-empty  -> the closed set is EXACTLY that list. A
      name not present in the loaded modules RAISES. A typo must not silently
      shrink the vocabulary, because its size sets the null distribution.
    * otherwise                    -> a structural cut at `max_depth`.

    The default uses the explicit list. LKIF's own tier and depth structure
    does not yield the upper-class set the concept phase assumes: Action sits
    at depth 2, Role at 2, Norm at 3, Prohibition at 5, while a depth<=1 cut
    hands you mereology's Atom/Part/Whole and drops Action entirely.
    """
    oc = cfg["ontology"]
    max_depth = oc.get("max_depth")
    include = list(oc.get("include_classes") or [])
    exclude = set(oc.get("exclude_classes", []))
    by_name = defaultdict(list)
    for c in ont.classes.values():
        by_name[c.name].append(c)
    if include:
        missing = [n for n in include if n not in by_name]
        if missing:
            raise ClosedSetError(
                f"ontology.include_classes names {len(missing)} class(es) that "
                f"are NOT in the loaded modules: {missing}. Refusing to run: a "
                "silently smaller closed set changes the null distribution and "
                "every statistic computed against it. Fix the name, or load "
                "the module that defines it.")
        chosen = [by_name[n][0] for n in include if n not in exclude]
    else:
        chosen = [c for c in ont.classes.values()
                  if c.name not in exclude
                  and (max_depth is None or c.depth <= max_depth)]
    seen, members = set(), []
    for c in sorted(chosen, key=lambda c: (c.name.lower(), c.iri)):
        if c.name not in seen:
            seen.add(c.name)
            members.append(c)
    if len(members) < 2:
        raise ClosedSetError(
            f"closed set has {len(members)} member(s). A placement test needs "
            "at least two options. Widen ontology.max_depth or the module "
            "selection.")
    return members


def closed_set_labels(members, cfg):
    labels = [c.name for c in members]
    if cfg["prompt"].get("allow_none", True):
        labels = labels + [NONE_LABEL]
    return labels


# ==========================================================================
# 2.  Corpus
# ==========================================================================
def load_corpus(cfg):
    cc = cfg["corpus"]
    path = cc["path"]
    if not os.path.isabs(path):
        path = os.path.normpath(os.path.join(HERE, path))
    if not os.path.exists(path):
        raise CorpusError(f"corpus not found: {path}")
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        raise CorpusError(f"corpus {path}: {e}") from e
    key = cc.get("records_key")
    if key and not isinstance(raw, dict):
        raise CorpusError(f"corpus {path}: records_key set but top level is "
                          f"{type(raw).__name__}, not an object")
    records = raw[key] if key else raw
    if not isinstance(records, list):
        raise CorpusError(f"corpus {path}: expected a list of records at "
                          f"{key or '<root>'}")
    id_key, text_key = cc["id_key"], cc["text_key"]
    excl = cc.get("exclude_where", {})
    incl = cc.get("include_where", {})
    min_chars = cc.get("min_text_chars", 1)
    items, seen = [], set()
    dedupe = cc.get("dedupe_by")
    for r in records:
        if id_key not in r or text_key not in r:
            continue
        if any(r.get(k) == v for k, v in excl.items()):
            continue
        if incl and not all(r.get(k) == v for k, v in incl.items()):
            continue
        text = (r.get(text_key) or "").strip()
        if len(text) < min_chars:
            continue
        if dedupe:
            dk = r.get(dedupe)
            if dk in seen:
                continue
            seen.add(dk)
        items.append({"id": str(r[id_key]), "text": text, "record": r})
    if not items:
        raise CorpusError(
            f"corpus {path}: ZERO eligible items after filtering "
            f"(include={incl}, exclude={excl}, min_text_chars={min_chars}). "
            "An empty corpus is an error, not an empty result.")
    return items, path


def sample_items(items, n, seed):
    """Deterministic given (corpus content, n, seed)."""
    if n < 2:
        raise CorpusError(f"--n-items {n}: need at least 2 items")
    if n > len(items):
        raise CorpusError(
            f"--n-items {n} exceeds the {len(items)} eligible corpus items")
    ordered = sorted(items, key=lambda it: it["id"])
    rng = random.Random(seed)
    return sorted(rng.sample(ordered, n), key=lambda it: it["id"])


# ==========================================================================
# 3.  Prompts
# ==========================================================================
def build_system_prompt(members, cfg):
    p = cfg["prompt"]
    lines = [p["preamble"].strip(), "",
             f"THE CLOSED SET ({len(members)} classes):"]
    for c in members:
        gloss = " ".join((c.gloss or "").split())
        if p.get("gloss_max_chars"):
            gloss = gloss[:p["gloss_max_chars"]]
        tag = " [vocabulary-only]" if c.vocabulary_only else ""
        lines.append(f"- {c.name}{tag}" + (f" — {gloss}" if gloss else ""))
    if p.get("allow_none", True):
        lines.append(f"- {NONE_LABEL} — no class above subsumes this concept. "
                     "Use it alone, never alongside another class.")
    lines += ["", p["answer_instruction"].strip()]
    if p.get("vocabulary_only_note") and any(c.vocabulary_only for c in members):
        lines += ["", p["vocabulary_only_note"].strip()]
    return "\n".join(lines)


def build_user_prompt(item, cfg):
    """⚠️ Deliberately does NOT include the hand-rolled `kind`. That label is
    shown on the WORKSHEET, for the human's comparison, and withheld from the
    model — feeding it in would anchor the placement on the very four-category
    scheme the ontology is meant to replace."""
    p = cfg["prompt"]
    rec = item["record"]
    keys = cfg["corpus"].get("prompt_context_keys", [])
    prior = cfg["corpus"].get("worksheet_fields", {}).get("prior_label")
    if prior and prior in keys:
        raise ConfigError(
            f"corpus.prompt_context_keys includes {prior!r}, which is the "
            "hand-rolled prior label shown on the worksheet. Feeding it to "
            "the model anchors the placement on the very four-category "
            "scheme the ontology is meant to replace, and the comparison "
            "between the two becomes circular. Remove it from "
            "prompt_context_keys.")
    ctx = "\n".join(f"{k}: {rec[k]}" for k in keys if rec.get(k))
    return p["item_template"].format(
        id=item["id"], text=item["text"], context=ctx).strip()


# ==========================================================================
# 4.  Model access.  Reuse the repo's providers.py when it is there.
# ==========================================================================
class _ProviderShim:
    def __init__(self, name, model, base_url, api_key_env, kind,
                 temperature, max_tokens, price_per_mtok, native=None):
        self.name = name
        self.model = model
        self.base_url = base_url
        self.api_key_env = api_key_env
        self.kind = kind
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.price_per_mtok = price_per_mtok
        self.native = native

    def key(self):
        if self.native is not None and hasattr(self.native, "key"):
            return self.native.key()
        return os.environ.get(self.api_key_env) if self.api_key_env else None


def resolve_provider(cfg, overrides):
    mc = dict(cfg["model"])
    mc.update({k: v for k, v in overrides.items() if v is not None})
    native = None
    pj = mc.get("providers_json")
    if pj:
        pj_path = pj if os.path.isabs(pj) else os.path.normpath(
            os.path.join(HERE, pj))
        if os.path.exists(pj_path) and mc.get("provider_name"):
            repo = os.path.dirname(pj_path)
            if repo not in sys.path:
                sys.path.insert(0, repo)
            try:
                import providers as _p                      # noqa: WPS433
                for cand in _p.ProviderConfig.load_all(pj_path):
                    if cand.name == mc["provider_name"]:
                        native = cand
                        break
                if native is None:
                    raise ConfigError(
                        f"provider {mc['provider_name']!r} not in {pj_path}")
            except ImportError:
                native = None
    if native is not None:
        return _ProviderShim(
            name=native.name, model=mc.get("model") or native.model,
            base_url=native.base_url, api_key_env=native.api_key_env,
            kind=native.kind,
            temperature=mc.get("temperature", native.temperature),
            max_tokens=mc.get("max_tokens") or 256,
            price_per_mtok=native.price_per_mtok, native=native)
    if not mc.get("model"):
        raise ConfigError(
            "no model: set model.provider_name against a providers.json, or "
            "give model.model + model.base_url + model.api_key_env explicitly")
    return _ProviderShim(
        name=mc.get("provider_name") or mc["model"], model=mc["model"],
        base_url=mc.get("base_url"), api_key_env=mc.get("api_key_env"),
        kind=mc.get("kind", "openai-compatible"),
        temperature=mc.get("temperature", 1.0),
        max_tokens=mc.get("max_tokens", 256),
        price_per_mtok=mc.get("price_per_mtok"))


def reject_if_truncated(finish):
    """A cut-off completion can still contain class names, so it would score
    as a real placement — with the tail of the set missing."""
    if str(finish or "").lower() in ("length", "max_tokens",
                                     "max_output_tokens"):
        raise ProviderError(
            f"response was TRUNCATED (finish_reason={finish!r}). A cut-off "
            "completion may still contain class names and would score as a "
            "real placement with its tail missing. Raise model.max_tokens; "
            "do not score this run.")


class MiniClient:
    """Fallback transport when providers.py is unavailable.  stdlib only.
    Raises on every failure — there is no empty-response return path."""

    def __init__(self, prov):
        self.p = prov
        if not prov.key():
            raise ProviderError(
                f"provider {prov.name}: no API key in ${prov.api_key_env}")

    def complete(self, system, user):
        p = self.p
        if p.kind == "openai-compatible":
            url = p.base_url.rstrip("/") + "/chat/completions"
            headers = {"Authorization": f"Bearer {p.key()}",
                       "Content-Type": "application/json"}
            body = {"model": p.model, "max_tokens": p.max_tokens,
                    "temperature": p.temperature,
                    "messages": [{"role": "system", "content": system},
                                 {"role": "user", "content": user}]}
        elif p.kind == "anthropic":
            url = "https://api.anthropic.com/v1/messages"
            headers = {"x-api-key": p.key(), "anthropic-version": "2023-06-01",
                       "Content-Type": "application/json"}
            body = {"model": p.model, "max_tokens": p.max_tokens,
                    "temperature": p.temperature, "system": system,
                    "messages": [{"role": "user", "content": user}]}
        else:
            raise ConfigError(f"unknown provider kind {p.kind!r}")
        req = urllib.request.Request(url, json.dumps(body).encode(),
                                     headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.load(r)
        except Exception as e:
            raise ProviderError(f"{p.name}/{p.model}: {e}") from e
        try:
            if p.kind == "anthropic":
                text = "".join(b.get("text", "") for b in data["content"])
                u = data.get("usage", {})
                usage = {"in": u.get("input_tokens", 0),
                         "out": u.get("output_tokens", 0)}
                finish = data.get("stop_reason")
            else:
                text = data["choices"][0]["message"]["content"]
                u = data.get("usage", {})
                usage = {"in": u.get("prompt_tokens", 0),
                         "out": u.get("completion_tokens", 0)}
                finish = data["choices"][0].get("finish_reason")
        except Exception as e:
            raise ProviderError(
                f"{p.name}/{p.model}: unreadable response envelope: "
                f"{json.dumps(data)[:400]}") from e
        reject_if_truncated(finish)
        return {"text": text, "usage": usage}


class RepoClient:
    """Wraps providers.LiveClient so its envelope shape matches MiniClient."""

    def __init__(self, prov, usage_log):
        import providers as _p                              # noqa: WPS433
        self.inner = _p.LiveClient(prov.native)
        self.usage_log = usage_log

    def complete(self, system, user):
        try:
            env = self.inner.complete_envelope(system, user,
                                               usage_log=self.usage_log)
        except Exception as e:
            raise ProviderError(str(e)) from e
        reject_if_truncated(env.get("finish_reason"))
        u = env.get("usage") or {}
        return {"text": env.get("text"),
                "usage": {"in": u.get("prompt_tokens")
                          or u.get("input_tokens") or 0,
                          "out": u.get("completion_tokens")
                          or u.get("output_tokens") or 0}}


def make_client(prov, cfg):
    if prov.native is not None:
        try:
            return RepoClient(prov, cfg["model"].get("usage_log", "DEFAULT"))
        except ImportError:
            pass
    return MiniClient(prov)


# ==========================================================================
# 5.  Response parsing — a SET, strictly inside the closed vocabulary
# ==========================================================================
_SPLIT_RE = re.compile(r"[,\n;/|]+")


def parse_placement(text, labels, item_id, run_idx):
    """Returns a frozenset of closed-set labels.  Raises on anything else."""
    if text is None or not str(text).strip():
        raise ResponseParseError(
            f"item {item_id} run {run_idx}: EMPTY response. An empty response "
            "is a failed call, not an empty placement.")
    canon = {l.lower(): l for l in labels}
    cleaned = str(text).strip()
    # Use the last non-empty line that yields any in-set token: models that
    # narrate then answer put the answer last.
    for line in reversed([l for l in cleaned.splitlines() if l.strip()]):
        toks, unknown = [], []
        for piece in _SPLIT_RE.split(line):
            t = re.sub(r"^[\s\-*>#\d.)]+", "", piece).strip()
            t = t.strip("`\"'*.,;:!? ")
            if not t:
                continue
            if t.lower() in canon:
                toks.append(canon[t.lower()])
            else:
                unknown.append(t)
        if toks and not unknown:
            s = frozenset(toks)
            if NONE_LABEL in s and len(s) > 1:
                raise ResponseParseError(
                    f"item {item_id} run {run_idx}: response combines "
                    f"{NONE_LABEL} with {sorted(s - {NONE_LABEL})}. That is "
                    "incoherent — either the closed set covers the concept or "
                    "it does not. Refusing to score it.")
            return s
    raise ResponseParseError(
        f"item {item_id} run {run_idx}: no line of the response is a clean "
        f"subset of the closed set of {len(labels)}. Raw response: "
        f"{cleaned[:300]!r}. Refusing to score an out-of-set answer — a "
        "closed-vocabulary test whose answers are not closed measures nothing.")


# ==========================================================================
# 6.  Statistics — Jaccard over sets
# ==========================================================================
def jaccard(a, b):
    u = a | b
    if not u:
        raise DegenerateAgreementError(
            "Jaccard of two empty sets is undefined; an empty placement "
            "should have raised at parse time")
    return len(a & b) / len(u)


def mean_pairwise_jaccard(runs):
    """Mean Jaccard over all unordered pairs of runs for ONE item."""
    n = len(runs)
    if n < 2:
        raise DegenerateAgreementError(
            "runs_per_item must be >= 2: with one run there are no pairs to "
            "compare, and inter-run agreement is undefined")
    tot = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            tot += jaccard(runs[i], runs[j])
    return tot / (n * (n - 1) / 2)


def agreement(per_item_runs):
    """Per-item mean pairwise Jaccard, and the mean over items."""
    if not per_item_runs:
        raise DegenerateAgreementError("no items to score")
    per_item = [mean_pairwise_jaccard(r) for r in per_item_runs]
    return sum(per_item) / len(per_item), per_item


def bootstrap_ci(per_item, seed, B=2000, alpha=0.05):
    """Percentile bootstrap over ITEMS — the unit that was sampled."""
    rng = random.Random(seed ^ 0x5EED)
    N = len(per_item)
    vals = []
    for _ in range(B):
        draw = [per_item[rng.randrange(N)] for _ in range(N)]
        vals.append(sum(draw) / N)
    vals.sort()
    lo = vals[int(math.floor((alpha / 2) * len(vals)))]
    hi = vals[min(len(vals) - 1, int(math.ceil((1 - alpha / 2) * len(vals))) - 1)]
    return lo, hi


def null_pvalue(observed, per_item_runs, k_labels, seed, M=20000):
    """Monte-Carlo p against the EXPLICIT null, restated for set answers:

        H0: each run returns a set of the SAME SIZE the model actually
            returned, but its members are drawn uniformly at random without
            replacement from the closed vocabulary of k_labels classes.

    Sizes are held fixed deliberately. A null that also randomised set size
    would be beaten by nothing more than the model's consistent verbosity,
    and "the model reliably answers with two classes" is not evidence that it
    places concepts consistently. Fixing sizes asks the sharper question:
    GIVEN how many classes it returns, does it return the SAME ones?

    Statistic: mean over items of mean pairwise Jaccard.
    p = (1 + #{null >= observed}) / (M + 1) — never reported as exactly 0.
    """
    rng = random.Random(seed ^ 0xA11CE)
    sizes = [[len(r) for r in runs] for runs in per_item_runs]
    universe = list(range(k_labels))
    ge = 0
    for _ in range(M):
        tot = 0.0
        for item_sizes in sizes:
            runs = [frozenset(rng.sample(universe, s)) for s in item_sizes]
            tot += mean_pairwise_jaccard(runs)
        if tot / len(sizes) >= observed - 1e-12:
            ge += 1
    return (1 + ge) / (M + 1)


def per_class_table(per_item_runs):
    """For sets, 'confusion' is instability, and it has TWO distinct shapes
    that must not be conflated:

    * SUBSTITUTION — one run said A where another said B. That points at two
      classes whose glosses do not separate, and it is what `swapped_with`
      counts: only genuine A-for-B trades within a pair of runs.
    * SOLO add/drop — one run included A and the other simply left it out,
      with nothing offered in its place. That points at disagreement about how
      MANY classes apply, not about which. `solo_add_drop` counts it.

    An earlier version counted every class co-present in an unstable item as a
    "swap", which reported `Agent swapped_with Role` when Role was in fact
    stable across every run and only Agent came and went. The two failures
    call for different fixes, so they are counted separately.
    """
    rows = defaultdict(lambda: {"appearances": 0, "items_any": 0,
                                "items_all_runs": 0, "items_unstable": 0,
                                "solo_add_drop": 0, "swapped_with": Counter()})
    for runs in per_item_runs:
        n = len(runs)
        counts = Counter()
        for r in runs:
            for l in r:
                counts[l] += 1
        for l, c in counts.items():
            rows[l]["appearances"] += c
            rows[l]["items_any"] += 1
            if c == n:
                rows[l]["items_all_runs"] += 1
            else:
                rows[l]["items_unstable"] += 1
        for i in range(n):
            for j in range(i + 1, n):
                d1, d2 = runs[i] - runs[j], runs[j] - runs[i]
                if d1 and d2:
                    for a in d1:
                        for b in d2:
                            rows[a]["swapped_with"][b] += 1
                            rows[b]["swapped_with"][a] += 1
                else:
                    for a in d1 | d2:
                        rows[a]["solo_add_drop"] += 1
    return rows


def instability_pairs(per_item_runs):
    """Unordered pairs (a, b) where a run had a and another had b instead."""
    pairs = Counter()
    for runs in per_item_runs:
        for i in range(len(runs)):
            for j in range(i + 1, len(runs)):
                for a in runs[i] - runs[j]:
                    for b in runs[j] - runs[i]:
                        pairs[tuple(sorted((a, b)))] += 1
    return pairs


def verdict(ci_lo, p, cfg):
    v = cfg["verdict"]
    band = cfg["reference"]["human_pair_jaccard"]
    lo_b, hi_b = min(band), max(band)
    if p > v["max_p"]:
        return ("unusable",
                f"p={p:.4g} > {v['max_p']} — the run is not distinguishable "
                "from same-sized random subsets of the closed vocabulary")
    if ci_lo >= hi_b:
        return ("usable",
                f"Jaccard CI lower bound {ci_lo:.3f} >= {hi_b:.2f}, the TOP of "
                "the trained-human-pair band")
    if ci_lo >= lo_b:
        return ("marginal",
                f"Jaccard CI lower bound {ci_lo:.3f} sits inside the "
                f"trained-human-pair band [{lo_b:.2f}, {hi_b:.2f}]")
    return ("unusable",
            f"Jaccard CI lower bound {ci_lo:.3f} < {lo_b:.2f}, below the "
            "bottom of the trained-human-pair band")


# ==========================================================================
# 7.  Cost
# ==========================================================================
def estimate_cost(system, user_prompts, prov, cfg, runs):
    cpt = cfg["cost"]["chars_per_token"]
    out_tok = cfg["cost"]["assumed_output_tokens"]
    calls = len(user_prompts) * runs
    in_tok = int(sum(len(system) + len(u) for u in user_prompts) / cpt * runs)
    out_total = out_tok * calls
    price = prov.price_per_mtok
    if not price:
        return {"calls": calls, "in_tokens": in_tok, "out_tokens": out_total,
                "usd": None,
                "note": "provider has no price_per_mtok — cost UNKNOWN, "
                        "which the gate treats as over budget"}
    usd = in_tok / 1e6 * price[0] + out_total / 1e6 * price[1]
    return {"calls": calls, "in_tokens": in_tok, "out_tokens": out_total,
            "usd": usd,
            "note": f"@ ${price[0]}/${price[1]} per Mtok in/out, "
                    f"{cpt} chars/token, worst-case output"}


def cost_gate(est, max_cost):
    if est["usd"] is None:
        raise CostGateError(
            "estimated cost is UNKNOWN (no price_per_mtok for this provider). "
            "Refusing to spend against an unpriced provider — set "
            "model.price_per_mtok explicitly.")
    if est["usd"] > max_cost:
        raise CostGateError(
            f"estimated ${est['usd']:.4f} exceeds the ${max_cost:.2f} ceiling "
            f"({est['calls']} calls). Nothing was sent. Lower --n-items or "
            "--runs-per-item, pick a cheaper model, or raise --max-cost "
            "deliberately.")


# ==========================================================================
# 8.  Expected-placement worksheet (pre-registration)
# ==========================================================================
def worksheet_rows(items, cfg):
    wf = cfg["corpus"]["worksheet_fields"]
    rows = []
    for it in items:
        r = it["record"]
        rows.append({
            "id": it["id"],
            "concept": r.get(wf.get("concept", "")) or it["id"],
            "gloss": it["text"],
            "source_sentence": r.get(wf.get("source_sentence", ""), ""),
            "prior_label": r.get(wf.get("prior_label", ""), ""),
            "source_ref": r.get(wf.get("source_ref", ""), ""),
            "expected_placement": [],
        })
    return rows


def load_expected(path, labels):
    """A filled-in worksheet.  Names must be in the closed set, or it raises —
    a pre-registration that scores against a class the model was never offered
    is not a comparison."""
    if not os.path.exists(path):
        raise CorpusError(f"expected-placement file not found: {path}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    rows = data["items"] if isinstance(data, dict) else data
    out, bad = {}, []
    for r in rows:
        placement = r.get("expected_placement") or []
        if not placement:
            continue
        for name in placement:
            if name not in labels:
                bad.append((r.get("id"), name))
        out[str(r["id"])] = frozenset(placement)
    if bad:
        raise ClosedSetError(
            f"expected_placement uses {len(bad)} name(s) outside the closed "
            f"set: {bad[:5]}. Scoring against a class the model was never "
            "offered is not a comparison.")
    if not out:
        raise CorpusError(
            f"{path}: no row has a non-empty expected_placement. An unfilled "
            "worksheet is an error, not a score of zero.")
    return out


# ==========================================================================
# 9.  The run
# ==========================================================================
def run_test(cfg, args):
    ont = load_ontology(cfg)
    members = build_closed_set(ont, cfg)
    labels = closed_set_labels(members, cfg)
    items_all, corpus_path = load_corpus(cfg)
    items = sample_items(items_all, cfg["sampling"]["n_items"],
                         cfg["sampling"]["seed"])
    prov = resolve_provider(cfg, {
        "provider_name": getattr(args, "provider", None),
        "model": getattr(args, "model", None),
        "base_url": getattr(args, "base_url", None),
        "api_key_env": getattr(args, "api_key_env", None),
        "temperature": getattr(args, "temperature", None)})
    system = build_system_prompt(members, cfg)
    users = [build_user_prompt(it, cfg) for it in items]
    runs = cfg["sampling"]["runs_per_item"]
    est = estimate_cost(system, users, prov, cfg, runs)
    band = cfg["reference"]["human_pair_jaccard"]

    header = {
        "measures": "SELF-CONSISTENCY ONLY. No ground truth is used and none "
                    "is claimed: a stable but WRONG placement scores 1.0.",
        "ontology": {
            "name": ont.name,
            "modules_loaded": ont.modules_loaded,
            "classes_in_loaded_modules": ont.total_class_count,
            "closed_set_size": len(labels),
            "closed_set": labels,
            "closed_set_with_glosses": [
                {"name": c.name, "module": c.module, "depth": c.depth,
                 "vocabulary_only": c.vocabulary_only,
                 "gloss": " ".join((c.gloss or "").split())} for c in members],
            "selection": ("explicit include_classes"
                          if cfg["ontology"].get("include_classes")
                          else f"structural cut at max_depth="
                               f"{cfg['ontology'].get('max_depth')}"),
            "sources": ont.sources,
            "vocabulary_only_modules": cfg["ontology"].get(
                "vocabulary_only_modules", []),
        },
        "corpus": {"path": corpus_path, "eligible": len(items_all),
                   "sampled": len(items), "seed": cfg["sampling"]["seed"]},
        "model": {"provider": prov.name, "model": prov.model,
                  "base_url": prov.base_url, "temperature": prov.temperature,
                  "runs_per_item": runs},
        "reference": {"human_pair_jaccard": band,
                      "source": cfg["reference"]["source"],
                      "caveat": cfg["reference"]["caveat"]},
        "cost_estimate": est,
    }

    if getattr(args, "dry_run", False):
        return {"mode": "dry-run", **header,
                "worksheet": worksheet_rows(items, cfg),
                "system_prompt": system,
                "user_prompts": {it["id"]: u for it, u in zip(items, users)},
                "note": "NO API CALL WAS MADE. Nothing here is a result."}

    cost_gate(est, cfg["cost"]["max_cost_usd"])
    client = getattr(args, "client", None) or make_client(prov, cfg)

    per_item_runs, raw, usage_in, usage_out = [], [], 0, 0
    for it, user in zip(items, users):
        sets = []
        for r in range(runs):
            env = client.complete(system, user)
            if env is None:
                raise ProviderError(
                    f"item {it['id']} run {r}: client returned None. A "
                    "no-response path must never reach the statistics.")
            s = parse_placement(env.get("text"), labels, it["id"], r)
            sets.append(s)
            u = env.get("usage") or {}
            usage_in += u.get("in", 0)
            usage_out += u.get("out", 0)
            raw.append({"item": it["id"], "run": r, "placement": sorted(s),
                        "raw": str(env.get("text"))[:200]})
        per_item_runs.append(sets)

    if not raw:
        raise ProviderError(
            "PARSE CANARY: zero model responses were collected. That is an "
            "error, not an empty result.")

    obs, per_item = agreement(per_item_runs)
    lo, hi = bootstrap_ci(per_item, cfg["sampling"]["seed"],
                          B=cfg["statistics"]["bootstrap_resamples"],
                          alpha=cfg["statistics"]["ci_alpha"])
    p = null_pvalue(obs, per_item_runs, len(labels), cfg["sampling"]["seed"],
                    M=cfg["statistics"]["null_simulations"])
    vd, why = verdict(lo, p, cfg)

    sizes = [len(s) for runs_ in per_item_runs for s in runs_]
    none_answers = sum(1 for runs_ in per_item_runs for s in runs_
                       if s == frozenset({NONE_LABEL}))
    identical = sum(1 for runs_ in per_item_runs
                    if all(s == runs_[0] for s in runs_))

    price = prov.price_per_mtok
    actual = (usage_in / 1e6 * price[0] + usage_out / 1e6 * price[1]
              if price and (usage_in or usage_out) else None)

    report = {
        "mode": "live", **header,
        "results": {
            "n_items": len(items), "runs_per_item": runs,
            "mean_pairwise_jaccard": obs,
            "jaccard_ci": [lo, hi],
            "ci_alpha": cfg["statistics"]["ci_alpha"],
            "items_with_identical_placements": identical,
            "mean_classes_per_answer": sum(sizes) / len(sizes),
            "answer_size_distribution": dict(sorted(Counter(sizes).items())),
            "null_hypothesis": (
                "each run returns a set of the SAME SIZE the model actually "
                f"returned, but drawn uniformly at random from the {len(labels)}"
                "-class closed vocabulary; sizes are held fixed so that "
                "consistent verbosity alone cannot beat the null"),
            "null_p_value": p,
            "none_of_these_rate": none_answers / (len(items) * runs),
            "per_item_jaccard": {it["id"]: j
                                 for it, j in zip(items, per_item)},
        },
        "verdict": {
            "verdict": vd, "reason": why,
            "measures": "self-consistency only; correctness is NOT measured",
            "thresholds": {"usable_at_or_above": max(band),
                           "marginal_at_or_above": min(band),
                           "max_p": cfg["verdict"]["max_p"]},
            "what_would_change_it": _what_would_change(lo, hi, p, cfg),
        },
        "per_class": {k: {"appearances": v["appearances"],
                          "items_any": v["items_any"],
                          "items_all_runs": v["items_all_runs"],
                          "items_unstable": v["items_unstable"],
                          "solo_add_drop": v["solo_add_drop"],
                          "swapped_with": dict(v["swapped_with"])}
                      for k, v in sorted(per_class_table(per_item_runs).items())},
        "instability_pairs": [{"pair": list(k), "occurrences": v}
                              for k, v in
                              instability_pairs(per_item_runs).most_common()],
        "cost_actual": {"usd": actual, "in_tokens": usage_in,
                        "out_tokens": usage_out,
                        "note": "from provider-reported usage" if actual
                                is not None else
                                "provider reported no usage or no price"},
        "responses": raw,
    }

    exp_path = getattr(args, "expected", None)
    if exp_path:
        expected = load_expected(exp_path, set(labels))
        scored = {}
        for it, runs_ in zip(items, per_item_runs):
            if it["id"] in expected:
                e = expected[it["id"]]
                scored[it["id"]] = sum(jaccard(e, s) for s in runs_) / len(runs_)
        if not scored:
            raise CorpusError(
                f"{exp_path}: no expected placement matched any sampled item "
                "id. The worksheet and the sample have diverged — check the "
                "seed and --n-items.")
        report["vs_expected"] = {
            "source": exp_path,
            "items_scored": len(scored),
            "mean_jaccard_vs_expected": sum(scored.values()) / len(scored),
            "per_item": scored,
            "caveat": "ONE human's placements, written before the run. This "
                      "is a pre-registered sanity check, not ground truth and "
                      "not an inter-annotator statistic.",
        }
    return report


def _what_would_change(lo, hi, p, cfg):
    band = cfg["reference"]["human_pair_jaccard"]
    lo_b, hi_b = min(band), max(band)
    msgs = []
    if lo < hi_b:
        msgs.append(f"to reach 'usable', the Jaccard CI LOWER BOUND must rise "
                    f"from {lo:.3f} to {hi_b:.2f}.")
    else:
        msgs.append(f"the verdict falls to 'marginal' if the lower bound drops "
                    f"below {hi_b:.2f}; it is {lo:.3f}, "
                    f"{lo - hi_b:.3f} of margin.")
    msgs.append(f"CI half-width is {(hi - lo) / 2:.3f}; it shrinks roughly as "
                "1/sqrt(n_items), so quadrupling --n-items halves it.")
    msgs.append(f"any p above {cfg['verdict']['max_p']} forces 'unusable' "
                f"whatever the Jaccard; p is {p:.4g}.")
    msgs.append("NOTHING here would change a verdict about CORRECTNESS, which "
                "this test does not measure. Fill in the worksheet's "
                "expected_placement fields and rerun with --expected for that.")
    return msgs


# ==========================================================================
# 10.  Rendering
# ==========================================================================
def _wrap(text, width, indent):
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return ("\n" + " " * indent).join(lines) or ""


def render_worksheet(report):
    """⭐ The dry run IS the worksheet. Everything needed to write down an
    expected placement BEFORE any call is made."""
    out = []
    w = out.append
    o, c, m = report["ontology"], report["corpus"], report["model"]
    w("=" * 78)
    w("ONTOLOGY-FIT WORKSHEET   [DRY RUN — NO API CALL, NOTHING SPENT]")
    w("=" * 78)
    w("")
    w(_wrap("HOW TO USE THIS. Read each concept below and write, on its "
            "expected_placement line, the most specific classes from the "
            "closed set that subsume it — one or more. Do it BEFORE the model "
            "runs. That is the whole point: the expectation is pre-registered, "
            "so comparing it afterwards is a real check rather than a "
            "rationalisation.", 76, 0))
    w("")
    w(_wrap("WHAT THE LIVE RUN MEASURES: self-consistency only — whether "
            "repeated runs return the same set. It does NOT measure "
            "correctness; a stable but wrong placement scores a perfect 1.0. "
            "This worksheet is how correctness gets judged, by a person.",
            76, 0))
    w("")
    w(f"ontology     : {o['name']}")
    w(f"               modules: {', '.join(o['modules_loaded'])}")
    w(f"               {o['classes_in_loaded_modules']} classes parsed; closed "
      f"set of {o['closed_set_size']} ({o['selection']})")
    w(f"corpus       : {c['path']}")
    w(f"               {c['eligible']} eligible concepts, {c['sampled']} "
      f"sampled, seed={c['seed']}")
    w(f"model        : {m['provider']} / {m['model']}  T={m['temperature']}  "
      f"runs/item={m['runs_per_item']}")
    e = report["cost_estimate"]
    usd = "UNKNOWN" if e["usd"] is None else f"${e['usd']:.4f}"
    w(f"cost ESTIMATE: {usd}  ({e['calls']} calls, ~{e['in_tokens']} in / "
      f"{e['out_tokens']} out tokens)")
    w(f"               {e['note']}")
    r = report["reference"]
    w(f"reference    : trained-human-pair Jaccard "
      f"{' / '.join(f'{x:.2f}' for x in r['human_pair_jaccard'])} "
      f"({r['source']})")
    w(f"               {_wrap(r['caveat'], 60, 15)}")

    w("")
    w("=" * 78)
    w(f"THE CLOSED SET — {o['closed_set_size']} options, and what each means")
    w("=" * 78)
    for cl in o["closed_set_with_glosses"]:
        tag = "  [vocabulary-only: name taken, axioms NOT imported]" \
            if cl["vocabulary_only"] else ""
        w(f"  {cl['name']}   ({cl['module']}, depth {cl['depth']}){tag}")
        if cl["gloss"]:
            w(f"      {_wrap(cl['gloss'], 68, 6)}")
    w(f"  {NONE_LABEL}")
    w("      No class above subsumes this concept. Alone, never combined.")

    w("")
    w("=" * 78)
    w("CONCEPTS TO PLACE")
    w("=" * 78)
    for i, row in enumerate(report["worksheet"], 1):
        w("")
        w(f"--- {i:02d}/{len(report['worksheet'])} "
          + "-" * 60)
        w(f"  concept          : {row['concept']}")
        w(f"  gloss            : {_wrap(row['gloss'], 58, 21)}")
        w(f"  source sentence  : {_wrap(row['source_sentence'], 58, 21)}")
        if row["source_ref"]:
            w(f"  from             : {row['source_ref']}")
        w(f"  hand-rolled kind : {row['prior_label']}"
          "        <- the existing 4-category label, for comparison")
        w("")
        w("  expected_placement: ______________________________________________")
        w("")
        w("  exact prompt that will be sent (system prompt is the closed set "
          "above):")
        for line in report["user_prompts"][row["id"]].splitlines():
            w(f"    | {line}")
    w("")
    w("=" * 78)
    w("*** " + report["note"])
    w("*** Fill expected_placement in the JSON stub (--worksheet-json), then "
      "run")
    w("*** with --expected <that file> to score the model against it.")
    w("=" * 78)
    return "\n".join(out)


def render(report):
    if report["mode"] == "dry-run":
        return render_worksheet(report)
    out = []
    w = out.append
    o, c, m = report["ontology"], report["corpus"], report["model"]
    r = report["results"]
    w("=" * 78)
    w("ONTOLOGY-FIT TEST — SELF-CONSISTENCY ONLY")
    w("=" * 78)
    w(_wrap(report["measures"], 76, 0))
    w("")
    w(f"ontology     : {o['name']}  modules={','.join(o['modules_loaded'])}")
    w(f"               {o['classes_in_loaded_modules']} classes parsed; closed "
      f"set of {o['closed_set_size']} ({o['selection']})")
    w(f"  {', '.join(o['closed_set'])}")
    if o["vocabulary_only_modules"]:
        w(f"  vocabulary-only modules (names taken, axioms NOT imported): "
          f"{', '.join(o['vocabulary_only_modules'])}")
    w(f"corpus       : {c['path']}")
    w(f"               {c['eligible']} eligible, {c['sampled']} sampled, "
      f"seed={c['seed']}")
    w(f"model        : {m['provider']} / {m['model']}  T={m['temperature']}  "
      f"runs/item={m['runs_per_item']}")
    w("")
    w("-" * 78)
    w("AGREEMENT  (set-valued placement, Jaccard between runs)")
    w("-" * 78)
    w(f"mean pairwise Jaccard    : {r['mean_pairwise_jaccard']:.4f}   "
      f"{int((1 - r['ci_alpha']) * 100)}% CI [{r['jaccard_ci'][0]:.4f}, "
      f"{r['jaccard_ci'][1]:.4f}]  (bootstrap over concepts)")
    ref = report["reference"]
    w(f"trained-human-pair band  : "
      f"{' / '.join(f'{x:.2f}' for x in ref['human_pair_jaccard'])}  "
      f"({ref['source']})")
    w(f"  {_wrap(ref['caveat'], 74, 2)}")
    w(f"identical placements     : {r['items_with_identical_placements']}"
      f"/{r['n_items']} concepts had every run return the same set")
    w(f"classes per answer       : mean {r['mean_classes_per_answer']:.2f}, "
      f"distribution {r['answer_size_distribution']}")
    w(f"NULL                     : {_wrap(r['null_hypothesis'], 50, 27)}")
    w(f"p vs that null           : {r['null_p_value']:.5g}")
    w(f"{NONE_LABEL} rate        : {r['none_of_these_rate']:.3f}   "
      "(coverage signal: high = the ontology may not cover this text)")
    w("")
    w("-" * 78)
    w("PER CLASS  (a good overall number can hide one unstable class)")
    w("-" * 78)
    w(f"  {'class':24} {'uses':>5} {'items':>6} {'stable':>7} {'unstab':>7} "
      f"{'solo':>5}  swapped for")
    for k, v in report["per_class"].items():
        sw = ", ".join(f"{a}({b})" for a, b in
                       sorted(v["swapped_with"].items(),
                              key=lambda x: -x[1])[:3])
        w(f"  {k:24} {v['appearances']:5} {v['items_any']:6} "
          f"{v['items_all_runs']:7} {v['items_unstable']:7} "
          f"{v['solo_add_drop']:5}  {sw}")
    w("    stable = in EVERY run of that concept; unstab = in some runs only;")
    w("    solo   = came and went with nothing offered in its place "
      "(disagreement about")
    w("             HOW MANY classes apply, not which one).")
    if report["instability_pairs"]:
        w("")
        w("  most common SUBSTITUTIONS (one run had A exactly where another "
          "had B):")
        for cf in report["instability_pairs"][:10]:
            w(f"    {cf['pair'][0]} <-> {cf['pair'][1]}: {cf['occurrences']}")
    else:
        w("")
        w("  no substitutions at all: every disagreement was a solo add/drop. "
          "The model")
        w("  agrees on WHICH classes apply and differs on HOW MANY — read the "
          "solo column.")
    if "vs_expected" in report:
        ve = report["vs_expected"]
        w("")
        w("-" * 78)
        w("VS PRE-REGISTERED EXPECTATION")
        w("-" * 78)
        w(f"  mean Jaccard vs expected : {ve['mean_jaccard_vs_expected']:.4f} "
          f"over {ve['items_scored']} concepts  ({ve['source']})")
        w(f"  {_wrap(ve['caveat'], 74, 2)}")
    v = report["verdict"]
    w("")
    w("=" * 78)
    w(f"VERDICT: {v['verdict'].upper()}  — {v['reason']}")
    w(f"⚠️  {v['measures']}")
    w(f"thresholds (on the Jaccard CI LOWER bound): usable >= "
      f"{v['thresholds']['usable_at_or_above']:.2f}, marginal >= "
      f"{v['thresholds']['marginal_at_or_above']:.2f}, and p <= "
      f"{v['thresholds']['max_p']}")
    for msg in v["what_would_change_it"]:
        w(f"  - {_wrap(msg, 72, 4)}")
    ca = report["cost_actual"]
    w("cost ACTUAL: "
      + ("UNKNOWN" if ca["usd"] is None else f"${ca['usd']:.4f}")
      + f"  ({ca['in_tokens']} in / {ca['out_tokens']} out tokens) — "
      f"{ca['note']}")
    w("=" * 78)
    return "\n".join(out)


# ==========================================================================
# 11.  Self-test.  RED first: every check must fail for its named reason.
# ==========================================================================
class _ScriptedClient:
    def __init__(self, script, usage=(10, 4)):
        self.script = script if isinstance(script, Exception) else list(script)
        self.usage = usage
        self.i = 0

    def complete(self, system, user):
        if isinstance(self.script, Exception):
            raise self.script
        if self.i >= len(self.script):
            raise AssertionError("scripted client exhausted")
        t = self.script[self.i]
        self.i += 1
        return {"text": t, "usage": {"in": self.usage[0], "out": self.usage[1]}}


class _NoneClient:
    def complete(self, system, user):
        return None


class _Args:
    def __init__(self, dry_run=False, client=None, expected=None, **kw):
        self.dry_run = dry_run
        self.client = client
        self.expected = expected
        for k in ("provider", "model", "base_url", "api_key_env",
                  "temperature"):
            setattr(self, k, kw.get(k))


def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)


def _cfg_with(cfg, patch):
    out = json.loads(json.dumps(cfg))
    for k, v in patch.items():
        if isinstance(v, dict):
            out.setdefault(k, {}).update(v)
        else:
            out[k] = v
    return out


def _red(name, reason, fn, expect):
    try:
        fn()
    except expect as e:
        print(f"  RED  {name:38} raised {type(e).__name__}")
        print(f"       reason: {reason}")
        print(f"       said  : {str(e).splitlines()[0][:140]}")
        return True
    except Exception as e:                                    # noqa: BLE001
        print(f"  ****  {name}: raised {type(e).__name__} "
              f"(expected {expect.__name__}): {e}")
        return False
    print(f"  ****  {name}: DID NOT RAISE. This check has never been red and "
          "must not be trusted.")
    return False


def _green(name, fn):
    try:
        fn()
    except Exception as e:                                    # noqa: BLE001
        print(f"  ****  {name}: GREEN case raised {type(e).__name__}: {e}")
        return False
    print(f"  GREEN {name:38} passes on valid input")
    return True


def self_test(cfg):
    import tempfile
    print("=" * 78)
    print("SELF-TEST — every check is shown failing for its own named reason")
    print("=" * 78)
    ok = []

    # -- ontology --------------------------------------------------------
    ok.append(_red(
        "ontology parse canary",
        "an ontology with zero classes must be an error, not an empty set",
        lambda: parse_ontology_text(
            "@prefix : <http://x#> .\n:a :b :c .\n", "turtle", "<synthetic>"),
        OntologyParseError))
    ok.append(_green("ontology parses a real class", lambda: _assert(
        len(parse_ontology_text(
            '@prefix : <http://x#> .\n@prefix owl: <%s> .\n'
            '@prefix rdfs: <%s> .\n'
            ':Action a owl:Class ; rdfs:comment "a doing" .\n' % (OWL, RDFS),
            "turtle", "<synthetic>")) == 1, "expected exactly one class")))
    _rdfxml = ('<rdf:RDF xmlns:rdf="%s" xmlns:rdfs="%s" xmlns:owl="%s" '
               'xml:base="http://x">'
               '<owl:Class rdf:ID="Action"><rdfs:comment>a doing</rdfs:comment>'
               '<rdfs:subClassOf rdf:resource="http://x#Change"/></owl:Class>'
               '<owl:Class rdf:ID="Change"/></rdf:RDF>' % (RDF, RDFS, OWL))
    ok.append(_green("RDF/XML parses too (not just Turtle)", lambda: _assert(
        sorted(c.name for c in parse_ontology_text(
            _rdfxml, "rdfxml", "<synthetic>").values()) == ["Action", "Change"],
        "rdf/xml parse did not recover both classes")))
    ok.append(_red(
        "ontology module missing",
        "LKIF's owl:imports are all dead, so a missing module file must raise "
        "rather than be silently skipped",
        lambda: _read_module("nope", {"path": "/nonexistent",
                                      "url_template": "http://x/{module}",
                                      "allow_download": False}),
        OntologyParseError))
    ok.append(_green(
        "multiple inheritance survives the parse (the reason for set answers)",
        lambda: _assert(
            len([p for p in load_ontology(cfg).classes[
                "http://www.estrellaproject.org/lkif-core/action.owl#Person"
            ].parents]) >= 2,
            "Person should have more than one named superclass in LKIF")))

    # -- closed set ------------------------------------------------------
    tiny = Ontology("t", {"http://x#A": OntologyClass(
        "http://x#A", "A", "", set(), "x")}, ["x"], [])
    tiny.classes["http://x#A"].depth = 0
    ok.append(_red(
        "closed set degenerate (<2)",
        "one option means every placement is identical and agreement is empty",
        lambda: build_closed_set(tiny, _cfg_with(cfg, {"ontology": {
            "max_depth": 0, "include_classes": [], "exclude_classes": []}})),
        ClosedSetError))
    ok.append(_red(
        "closed-set member does not exist",
        "a mistyped class name must not silently shrink the vocabulary the "
        "null is computed over",
        lambda: build_closed_set(load_ontology(cfg), _cfg_with(cfg, {
            "ontology": {"include_classes": ["Action", "Aktion", "Role"]}})),
        ClosedSetError))

    # -- corpus ----------------------------------------------------------
    tmp = tempfile.mkdtemp()
    empty = os.path.join(tmp, "empty.json")
    with open(empty, "w") as f:
        json.dump({"atoms": []}, f)
    ok.append(_red(
        "corpus empty after filtering",
        "zero eligible concepts is an error, not an empty result",
        lambda: load_corpus(_cfg_with(cfg, {"corpus": {"path": empty}})),
        CorpusError))
    ok.append(_red(
        "corpus missing",
        "a missing corpus must never read as 'nothing to test'",
        lambda: load_corpus(_cfg_with(cfg, {"corpus": {
            "path": os.path.join(tmp, "nope.json")}})),
        CorpusError))
    three = [{"id": f"c{i}", "text": "t" * 20, "record": {}} for i in range(3)]
    ok.append(_red(
        "sample larger than corpus",
        "asking for more concepts than exist must raise, not shrink n",
        lambda: sample_items(three, 10, 0), CorpusError))
    ok.append(_green("deterministic sampling", lambda: _assert(
        [i["id"] for i in sample_items(three, 2, 7)]
        == [i["id"] for i in sample_items(three, 2, 7)],
        "same seed produced different samples")))
    forty = [{"id": f"c{j:03d}", "text": "x" * 20, "record": {}}
             for j in range(40)]
    ok.append(_green("seed actually varies the sample", lambda: _assert(
        any([i["id"] for i in sample_items(forty, 5, s)]
            != [i["id"] for i in sample_items(forty, 5, 0)]
            for s in (1, 2, 3)),
        "every seed gave the same sample — sampling ignores the seed")))
    ok.append(_green("dedupe_by collapses repeated concept names",
                     lambda: _assert(
                         len(load_corpus(cfg)[0])
                         < len(load_corpus(_cfg_with(cfg, {"corpus": {
                             "dedupe_by": None}}))[0]),
                         "dedupe_by had no effect on a corpus with repeats")))

    # -- placement parsing -------------------------------------------------
    labels = ["Action", "Artifact", "Role", "Agent", NONE_LABEL]
    ok.append(_red(
        "out-of-set token in a placement",
        "one invented class in an otherwise valid set must reject the whole "
        "answer, not be quietly dropped",
        lambda: parse_placement("Action, Speech_Act", labels, "c1", 0),
        ResponseParseError))
    ok.append(_red(
        "empty response",
        "an empty completion is a failed call, not an empty placement",
        lambda: parse_placement("   ", labels, "c1", 0), ResponseParseError))
    ok.append(_red(
        f"{NONE_LABEL} mixed with real classes",
        "either the closed set covers the concept or it does not; both is "
        "incoherent",
        lambda: parse_placement("NONE_OF_THESE, Action", labels, "c1", 0),
        ResponseParseError))
    ok.append(_green("multi-class placement parses", lambda: _assert(
        parse_placement("Agent, Role", labels, "c1", 0)
        == frozenset({"Agent", "Role"}), "failed to recover a two-class set")))
    ok.append(_green("single-class placement parses", lambda: _assert(
        parse_placement("Answer:\n`Action`.", labels, "c1", 0)
        == frozenset({"Action"}), "failed to recover Action")))

    # -- provider ---------------------------------------------------------
    two = _cfg_with(cfg, {"sampling": {"n_items": 2, "runs_per_item": 2}})
    ok.append(_red(
        "API error propagates",
        "an API failure must abort the run, never yield a clean report",
        lambda: run_test(two, _Args(
            client=_ScriptedClient(ProviderError("HTTP 500 boom")))),
        ProviderError))
    ok.append(_red(
        "client returns None",
        "a no-response path must never reach the statistics",
        lambda: run_test(two, _Args(client=_NoneClient())), ProviderError))
    ok.append(_red(
        "truncated response",
        "a cut-off completion can contain a partial set and must not score",
        lambda: reject_if_truncated("length"), ProviderError))
    ok.append(_green("a normal stop is not truncation",
                     lambda: reject_if_truncated("stop")))

    # -- cost gate ---------------------------------------------------------
    ok.append(_red(
        "cost gate",
        "an estimate over the ceiling must stop the run before any call",
        lambda: cost_gate({"usd": 4.0, "calls": 999}, 0.50), CostGateError))
    ok.append(_red(
        "unpriced provider",
        "unknown cost must be treated as over budget, not as free",
        lambda: cost_gate({"usd": None, "calls": 9}, 0.50), CostGateError))

    # -- statistics --------------------------------------------------------
    ok.append(_red(
        "one run per item",
        "with a single run there are no pairs and agreement is undefined",
        lambda: agreement([[frozenset({"Action"})]]),
        DegenerateAgreementError))
    ok.append(_red(
        "no items to score",
        "an empty result set must raise rather than average over nothing",
        lambda: agreement([]), DegenerateAgreementError))
    # Jaccard by hand: {A,B} vs {B,C} = 1/3 ; {A,B} vs {A,B} = 1
    ok.append(_green("Jaccard matches hand computation", lambda: _assert(
        abs(jaccard(frozenset("AB"), frozenset("BC")) - 1 / 3) < 1e-12
        and jaccard(frozenset("AB"), frozenset("AB")) == 1.0
        and jaccard(frozenset("A"), frozenset("B")) == 0.0,
        "Jaccard is not computing |A&B|/|A|B|")))
    ok.append(_green(
        "mean pairwise Jaccard over 3 runs matches hand computation",
        lambda: _assert(
            abs(mean_pairwise_jaccard(
                [frozenset("AB"), frozenset("AB"), frozenset("BC")])
                - (1 + 1 / 3 + 1 / 3) / 3) < 1e-12,
            "3-run mean is wrong")))
    ok.append(_green(
        "⭐ set answers do NOT manufacture disagreement (the whole correction)",
        lambda: _assert(
            mean_pairwise_jaccard([frozenset({"Agent", "Role"}),
                                   frozenset({"Agent", "Role"})]) == 1.0
            and mean_pairwise_jaccard([frozenset({"Agent"}),
                                       frozenset({"Role"})]) == 0.0,
            "two runs naming Agent and Role separately should score 0 under "
            "forced single choice; agreeing on the set should score 1")))
    perfect = [[frozenset({"Action"})] * 3 for _ in range(15)]
    obs_p, pi_p = agreement(perfect)
    p_perfect = null_pvalue(obs_p, perfect, 22, 0, M=2000)
    ok.append(_green(
        f"p is tiny for perfect agreement (J={obs_p:.3f}, p={p_perfect:.4g})",
        lambda: _assert(p_perfect < 0.01, f"p={p_perfect}")))
    rng = random.Random(11)
    noise = [[frozenset(rng.sample(range(22), 2)) for _ in range(3)]
             for _ in range(20)]
    obs_n, pi_n = agreement(noise)
    p_noise = null_pvalue(obs_n, noise, 22, 0, M=2000)
    ok.append(_green(
        f"p is NOT significant for random sets (J={obs_n:.3f}, p={p_noise:.3g})",
        lambda: _assert(p_noise > 0.01, f"p={p_noise}")))
    ok.append(_green("verdict flips at the human band, both edges",
                     lambda: _assert(
                         verdict(0.31, 0.001, cfg)[0] == "usable"
                         and verdict(0.26, 0.001, cfg)[0] == "marginal"
                         and verdict(0.10, 0.001, cfg)[0] == "unusable"
                         and verdict(0.95, 0.9, cfg)[0] == "unusable",
                         "verdict does not respect its own thresholds")))

    # -- expected-placement worksheet --------------------------------------
    bad_exp = os.path.join(tmp, "bad_expected.json")
    with open(bad_exp, "w") as f:
        json.dump({"items": [{"id": "x", "expected_placement": ["Nonsense"]}]},
                  f)
    ok.append(_red(
        "expected placement outside the closed set",
        "scoring against a class the model was never offered is not a "
        "comparison",
        lambda: load_expected(bad_exp, {"Action"}), ClosedSetError))
    unfilled = os.path.join(tmp, "unfilled.json")
    with open(unfilled, "w") as f:
        json.dump({"items": [{"id": "x", "expected_placement": []}]}, f)
    ok.append(_red(
        "unfilled worksheet",
        "an unfilled pre-registration is an error, not a score of zero",
        lambda: load_expected(unfilled, {"Action"}), CorpusError))

    # -- end-to-end --------------------------------------------------------
    script = ["Agent, Role", "Agent, Role", "Agent, Role",
              "Action", "Action", "Action, Process",
              "Norm, Prohibition", "Norm, Prohibition", "Norm",
              "NONE_OF_THESE", "NONE_OF_THESE", "NONE_OF_THESE"]
    four = _cfg_with(cfg, {"sampling": {"n_items": 4, "runs_per_item": 3}})
    rep = run_test(four, _Args(client=_ScriptedClient(script)))
    ok.append(_green(
        f"end-to-end on a scripted model (J="
        f"{rep['results']['mean_pairwise_jaccard']:.3f}, verdict="
        f"{rep['verdict']['verdict']})",
        lambda: _assert(rep["results"]["n_items"] == 4
                        and rep["cost_actual"]["usd"] is not None
                        and rep["results"]["none_of_these_rate"] == 0.25,
                        "end-to-end report is malformed")))
    dry = run_test(cfg, _Args(dry_run=True))
    ok.append(_green("dry-run makes no call and says so", lambda: _assert(
        dry["note"].startswith("NO API CALL"), "dry run did not declare itself")))
    ok.append(_green(
        "worksheet carries gloss, source sentence, prior label and a blank",
        lambda: _assert(
            all(r["gloss"] and r["source_sentence"] and r["prior_label"]
                and r["expected_placement"] == []
                for r in dry["worksheet"]),
            "a worksheet row is missing what a reviewer needs")))
    ok.append(_red(
        "⚠️ hand-rolled prior label leaked into the prompt",
        "showing the model the four-category label anchors the placement on "
        "the scheme the ontology replaces, and makes the comparison circular",
        lambda: run_test(_cfg_with(cfg, {"corpus": {
            "prompt_context_keys": ["quote", "kind"]}}), _Args(dry_run=True)),
        ConfigError))
    ok.append(_green(
        "the default prompt withholds the prior label",
        lambda: _assert(
            all("kind:" not in p for p in dry["user_prompts"].values())
            and all(r["prior_label"] for r in dry["worksheet"]),
            "prior label is either in the prompt or missing from the "
            "worksheet; it must be exactly the other way round")))

    print("-" * 78)
    passed = sum(1 for x in ok if x)
    print(f"{passed}/{len(ok)} self-test checks behaved as declared")
    print("=" * 78)
    return 0 if passed == len(ok) else 1


# ==========================================================================
# 12.  CLI
# ==========================================================================
def load_config(path):
    if not os.path.exists(path):
        raise ConfigError(f"config not found: {path}")
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    for req in ("ontology", "corpus", "model", "sampling", "prompt",
                "statistics", "verdict", "cost", "reference"):
        if req not in cfg:
            raise ConfigError(f"config is missing the {req!r} block")
    return cfg


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="ontology_fit.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__)
    ap.add_argument("--config", default=DEFAULT_CONFIG,
                    help="JSON config; every knob has a default there")
    ap.add_argument("--n-items", type=int,
                    help="how many concepts to sample (default from config)")
    ap.add_argument("--runs-per-item", type=int,
                    help="repeat count per concept; >=2 or agreement is "
                         "undefined")
    ap.add_argument("--temperature", type=float,
                    help="sampling temperature for the model")
    ap.add_argument("--seed", type=int,
                    help="seed for concept sampling, bootstrap and null sim")
    ap.add_argument("--corpus", help="path to the concept corpus JSON")
    ap.add_argument("--ontology-dir", help="local cache of ontology modules")
    ap.add_argument("--tiers", help="comma-separated ontology tiers to load")
    ap.add_argument("--max-depth", type=int,
                    help="structural cut, used only if include_classes is empty")
    ap.add_argument("--provider", help="provider name in providers.json")
    ap.add_argument("--model", help="model id (overrides the provider's)")
    ap.add_argument("--base-url", help="OpenAI-compatible base_url")
    ap.add_argument("--api-key-env", help="env var holding the API key")
    ap.add_argument("--max-cost", type=float,
                    help="hard ceiling on the ESTIMATE; over it nothing is sent")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the reviewable WORKSHEET: every sampled "
                         "concept with its gloss, source sentence, prior label "
                         "and a blank expected_placement, plus the closed set "
                         "with glosses and the exact prompts. No API call. "
                         "This is the DEFAULT when no key is set.")
    ap.add_argument("--worksheet-json", metavar="PATH",
                    help="write the worksheet as a fillable JSON stub")
    ap.add_argument("--expected", metavar="PATH",
                    help="a filled worksheet; scores the model against the "
                         "pre-registered placements (n=1 human, not truth)")
    ap.add_argument("--live", action="store_true",
                    help="actually call the API (costs money)")
    ap.add_argument("--self-test", action="store_true",
                    help="prove every check fails for its named reason")
    ap.add_argument("--list-classes", action="store_true",
                    help="print the parsed ontology classes and exit")
    ap.add_argument("--json", metavar="PATH", help="write the full report JSON")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    if args.n_items is not None:
        cfg["sampling"]["n_items"] = args.n_items
    if args.runs_per_item is not None:
        cfg["sampling"]["runs_per_item"] = args.runs_per_item
    if args.seed is not None:
        cfg["sampling"]["seed"] = args.seed
    if args.corpus:
        cfg["corpus"]["path"] = args.corpus
    if args.ontology_dir:
        cfg["ontology"]["source"]["path"] = args.ontology_dir
    if args.tiers:
        cfg["ontology"]["tiers"] = [t.strip() for t in args.tiers.split(",")]
    if args.max_depth is not None:
        cfg["ontology"]["max_depth"] = args.max_depth
    if args.max_cost is not None:
        cfg["cost"]["max_cost_usd"] = args.max_cost
    if args.temperature is not None:
        cfg["model"]["temperature"] = args.temperature

    if args.self_test:
        return self_test(cfg)

    if args.list_classes:
        ont = load_ontology(cfg)
        members = build_closed_set(ont, cfg)
        chosen = {m.iri for m in members}
        print(f"{ont.total_class_count} classes parsed from "
              f"{len(ont.modules_loaded)} modules; closed set = "
              f"{len(closed_set_labels(members, cfg))}")
        for c in sorted(ont.classes.values(),
                        key=lambda c: (c.depth, c.module, c.name)):
            mark = "*" if c.iri in chosen else " "
            print(f" {mark} d{c.depth} {c.module:16} {c.name:34} "
                  f"{' '.join((c.gloss or '').split())[:70]}")
        return 0

    prov = resolve_provider(cfg, {"provider_name": args.provider,
                                  "model": args.model,
                                  "base_url": args.base_url,
                                  "api_key_env": args.api_key_env,
                                  "temperature": args.temperature})
    if args.live and not prov.key():
        raise ProviderError(
            f"--live requested but no API key in ${prov.api_key_env}. "
            "Refusing to pretend a run happened.")
    args.dry_run = args.dry_run or not args.live
    args.client = None

    report = run_test(cfg, args)
    print(render(report))
    if args.worksheet_json:
        if report["mode"] != "dry-run":
            raise ConfigError("--worksheet-json is a dry-run artifact")
        with open(args.worksheet_json, "w", encoding="utf-8") as f:
            json.dump({
                "_": "Fill expected_placement on each row with class names "
                     "from closed_set, then rerun with --expected <this file>. "
                     "Write them BEFORE looking at any model output.",
                "closed_set": report["ontology"]["closed_set"],
                "seed": report["corpus"]["seed"],
                "n_items": report["corpus"]["sampled"],
                "items": report["worksheet"]}, f, indent=2)
        print(f"\n[fillable worksheet written to {args.worksheet_json}]")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\n[report written to {args.json}]")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except OntologyFitError as e:
        print(f"\nREFUSING TO REPORT — {type(e).__name__}\n{e}\n",
              file=sys.stderr)
        sys.exit(2)
