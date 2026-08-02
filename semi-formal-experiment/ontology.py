"""The relation layer over the atom vocabulary — derived ONCE PER SPEC.

WHY THIS EXISTS
---------------
`annotations_b8.json` gives 361 atom names, each with a kind and a gloss. Those
names are FLAT: `creative_assistance` and `brainstorming_help` are unrelated
strings, so any matcher over them collapses to string equality. A behaviour
selects ~25 atoms and a clause carries ~2.75, so exact overlap is sparse and
brittle — which is exactly why the previous scorer had to smuggle in a lexical
cosine and then weight the ontology at 0.6 of a sum.

This module adds the missing structure: a typed relation graph over the
vocabulary. It is derived from the vocabulary's own names, glosses and kinds.
It is NEVER derived per behaviour, never per query, and never from panel
labels — the panel is a measuring instrument, not training data (contract §5
invariant 8). Nothing in this file may read the panel file; a test asserts that
its filename, its loader and its verdict field appear nowhere in this module.

THE RELATION SET (four relations, and why exactly these)
-------------------------------------------------------
    same_as(a, b)    genuine synonyms the vocabulary failed to merge.
                     SYMMETRIC. Same kind only.
    subsumes(a, b)   a is the broader concept, b the narrower
                     (`harm` subsumes `third_party_harm`).
                     DIRECTED, ACYCLIC. **Same kind only** — a taxonomy is a
                     partition per kind, and a situation that "subsumes" an act
                     is a type error that would let the query count a
                     circumstance as a behaviour.
    entails(a, b)    an instance of a is necessarily an instance of b.
                     DIRECTED, ACYCLIC. **This is the only relation permitted
                     to cross kinds**, and that is its whole job: performing
                     `refuse_request` (act) entails that `request_refused`
                     (situation) obtains. Without it the type discipline would
                     also be a wall, and the act and situation halves of the
                     vocabulary could never talk to each other.
    contrary(a, b)   mutually exclusive. SYMMETRIC. Same kind only.
                     This is the relation that lets the ontology say a clause
                     is about the OPPOSITE situation, which no similarity score
                     can express: `avoid_topic_censorship` and
                     `topic_censorship` are maximally similar as strings and
                     maximally opposed as concepts.

Four is the minimum set that supports the typed query in `structural.py`:
two "connect" relations of different strength (same_as / subsumes), one
type-crossing bridge (entails), and one defeater (contrary). A fifth
("related_to", "co-occurs") was deliberately NOT added: an untyped association
edge is a similarity score wearing an ontology's clothes, and re-introducing it
is how this project drifted the first time.

TWO DERIVATION PATHS — AND WHICH ONE THE DATA SUPPORTS
-----------------------------------------------------
(a) MECHANICAL — `derive_mechanical`. No model at all: morphology over names
    and glosses. Deterministic, auditable, free. **On this spec it is a
    measured null result: 20 edges over 361 atoms, ~5% of the vocabulary
    touched, and two of its three headline rules fire ZERO times.** See
    `MECHANICAL_NULL_RESULT`. It is retained as the baseline the annotated
    layer is measured against, and is written up as a null result rather than
    deleted — "the obvious cheap thing does not work here" is a finding.

(b) ANNOTATED — `run_annotation_pass`. THE PRIMARY PATH. One pass over the
    VOCABULARY (not the corpus, not per behaviour, not per query): the 361
    atoms with kinds and glosses, asked for typed relation triples whose
    endpoints must BOTH already be in the vocabulary — the same anti-fabrication
    device as span-id selection in `annotate.py`, so nothing can be invented.
    Four calls partition the RELATION SPACE (situation subsumption, act
    subsumption, act/situation correspondence, contrary) while every call sees
    the whole vocabulary, because the interesting pairs are exactly the ones
    that would straddle a vocabulary split. ~$0.04, once per spec, cached to
    `ontology.json`. `--live` is required; the default is a dry run that writes
    prompts and calls nothing.

Both produce the same `Relation` type and both go through the same `validate`,
so they can be compared (`agreement`) or combined (`merge`).

GUARDRAILS (all counted, never silent)
--------------------------------------
    unknown_atom         an endpoint outside the vocabulary — nothing invented
    self_loop            a == b
    cross_kind_subsumes  / _same_as / _contrary  — type errors
    cycle                the edge would close a subsumption/entailment cycle
    contradictory_pair   a pair asserted both contrary and connected; contrary
                         wins, because a false contrary costs only recall while
                         a false subsumption MANUFACTURES matches
    duplicate            same triple twice

Usage:
    .venv/bin/python ontology.py --stats            # mechanical only, offline
    .venv/bin/python ontology.py --print-prompt     # what the model would see
    .venv/bin/python ontology.py --live --out ontology.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, replace

import annotate
import relevance

HERE = os.path.dirname(os.path.abspath(__file__))
ANNOTATIONS = os.path.join(HERE, "annotations_b8.json")
ARTIFACT = os.path.join(HERE, "ontology.json")

KINDS = relevance.ATOM_KINDS                      # situation / act / entity / value
RELATIONS = ("same_as", "subsumes", "entails", "contrary")
SYMMETRIC = ("same_as", "contrary")
#: Relations whose endpoints must share a kind. `entails` is deliberately absent.
SAME_KIND_ONLY = ("same_as", "subsumes", "contrary")
#: Relations that must stay acyclic (a taxonomy with a cycle is not a taxonomy).
ACYCLIC = ("subsumes", "entails")
#: Relations a query may TRAVERSE to connect two atoms. `contrary` is excluded
#: by construction: walking it would connect a concept to its own opposite.
TRAVERSABLE = ("same_as", "subsumes", "entails")


# --------------------------------------------------------------- the datum

@dataclass(frozen=True, order=True)
class Relation:
    """One edge, with the evidence that produced it.

    `via` names the rule (mechanical) or the model; `evidence` is the literal
    material the rule fired on. Both exist so `structural.explain()` can print
    a path a reader can check by hand rather than a number they must trust.
    """
    rel: str
    a: str
    b: str
    via: str = ""
    evidence: str = ""
    source: str = "mechanical"     # mechanical | model | both

    @property
    def key(self):
        return (self.rel, self.a, self.b)

    def as_dict(self):
        return {"rel": self.rel, "a": self.a, "b": self.b, "via": self.via,
                "evidence": self.evidence, "source": self.source}

    def describe(self):
        arrow = "<->" if self.rel in SYMMETRIC else "->"
        return f"{self.a} {arrow}[{self.rel}] {self.b}  ({self.via})"


@dataclass(frozen=True)
class Link:
    """A connection between two atoms: the path, its length, and whether it
    crossed a kind boundary (and if so, by which licensed edge)."""
    source: str
    target: str
    hops: int
    path: tuple = ()

    @property
    def crosses_kind(self) -> bool:
        return any(r.rel == "entails" for r in self.path)

    def describe(self):
        if not self.path:
            return f"{self.source} == {self.target} (identical atom)"
        return " ; ".join(r.describe() for r in self.path)


# -------------------------------------------------------------- vocabulary

def load_vocabulary(source=ANNOTATIONS) -> dict:
    """`{name: {kind, gloss, n_clauses, clauses}}` from an annotate.py artifact.

    Tolerant in the same way `relevance.load_annotations` is: the artifact's own
    `vocabulary` block is used when present, otherwise the vocabulary is rebuilt
    from the atom records themselves, so a differently-shaped artifact still
    yields an ontology rather than an exception.
    """
    if isinstance(source, str):
        try:
            with open(source) as f:
                source = json.load(f)
        except (OSError, ValueError):
            return {}
    if not isinstance(source, dict):
        source = {"atoms": source}

    vocab = {}
    raw = source.get("vocabulary")
    if isinstance(raw, dict):
        for name, e in raw.items():
            if not isinstance(name, str) or not isinstance(e, dict):
                continue
            clauses = e.get("clauses") or []
            vocab[name] = {"kind": e.get("kind") or "",
                           "gloss": e.get("gloss") or "",
                           "n_clauses": int(e.get("n_clauses") or len(clauses)),
                           "clauses": list(clauses)}
    if vocab:
        return vocab

    # rebuild from atoms: {name -> kind (most common), gloss (longest), clauses}
    by_clause = relevance.load_annotations(source)
    seen = defaultdict(lambda: {"kinds": Counter(), "gloss": "", "clauses": set()})
    for cid, atoms in by_clause.items():
        for a in atoms:
            e = seen[a["name"]]
            if a["kind"]:
                e["kinds"][a["kind"]] += 1
            if len(a["gloss"]) > len(e["gloss"]):
                e["gloss"] = a["gloss"]
            e["clauses"].add(cid)
    for name, e in seen.items():
        vocab[name] = {"kind": (e["kinds"].most_common(1) or [("", 0)])[0][0],
                       "gloss": e["gloss"],
                       "n_clauses": len(e["clauses"]),
                       "clauses": sorted(e["clauses"])}
    return vocab


# ------------------------------------------------------- name normalisation

def name_tokens(name: str) -> frozenset:
    """The meaning-bearing tokens of a snake_case atom name.

    Reuses `annotate`'s synonym table and singulariser so this module and the
    annotator agree on what two names have in common — a second, divergent
    normaliser is how `refusal` and `refuse` end up as unrelated concepts in
    one file and the same concept in another.
    """
    toks = []
    for t in str(name or "").lower().split("_"):
        if not t:
            continue
        t = annotate._SYNONYMS.get(t) or annotate._SYNONYMS.get(
            annotate._singular(t)) or annotate._singular(t)
        if t in annotate._STOP:
            continue
        toks.append(t)
    return frozenset(toks)


#: Tokens that INVERT a name rather than narrowing it. `avoid_topic_censorship`
#: is a superset of `topic_censorship` by tokens and its OPPOSITE by meaning,
#: so the subsumption rule must never see these as modifiers. This list is a
#: property of English, written down once; it is not tuned on anything.
NEGATION_TOKENS = frozenset("""
avoid avoids avoiding not no non without absent lack lacking refrain prevent
prevents preventing anti un
""".split())

#: Polarity pairs. Same discipline as `annotate._SYNONYMS`: deliberately small
#: and conservative, each entry a claim about English (not about this spec, and
#: certainly not about the panel). A wrong entry costs recall by asserting a
#: false contrary — the cheap direction of error, since contraries only ever
#: block matches, never create them.
ANTONYMS = frozenset(frozenset(p) for p in [
    ("over", "under"), ("accept", "refuse"), ("comply", "refuse"),
    ("allow", "prohibit"), ("allow", "forbid"), ("permit", "deny"),
    ("disclose", "conceal"), ("disclose", "hide"), ("reveal", "hide"),
    ("honest", "deceptive"), ("honest", "deceive"), ("help", "harm"),
    ("explicit", "implicit"), ("public", "private"), ("known", "unknown"),
    ("ambiguous", "clear"), ("certain", "uncertain"), ("safe", "harm"),
    ("increase", "decrease"), ("follow", "violate"), ("obey", "violate"),
    ("enable", "disable"), ("include", "exclude"), ("present", "absent"),
    ("more", "less"), ("grant", "revoke"), ("trusted", "untrusted"),
    ("success", "failure"), ("agree", "disagree"), ("required", "optional"),
])


def _antonymous(x: str, y: str) -> bool:
    if frozenset((x, y)) in ANTONYMS:
        return True
    for pre in ("un", "non", "dis", "in", "im"):
        if x == pre + y or y == pre + x:
            return True
    return False


def gloss_tokens(gloss: str) -> frozenset:
    """Stemmed content tokens of a gloss, via `relevance.tokens` — again, one
    tokeniser shared with the rest of the pipeline rather than a private one."""
    return frozenset(relevance.tokens(gloss or ""))


# ------------------------------------------------------ mechanical derivation

#: Rule order is PRIORITY order. Contrary rules run first so a polarity pair can
#: never be mistaken for a genus/species pair; the frequency-ordered subsumption
#: rules run before the gloss rules because a name is a definition the annotator
#: chose, while a gloss is prose that happens to overlap.
#:
#: ⚠️ THIS WHOLE PATH IS A MEASURED NULL RESULT ON THIS SPEC. See
#: `MECHANICAL_NULL_RESULT` below before reading further — the rules are correct
#: and they find almost nothing, and that fact is the finding.
DEFAULT_RULES = ("contrary_negation", "contrary_antonym", "same_as_key",
                 "entails_nominalisation", "subsumes_name_tokens",
                 "subsumes_gloss_names", "subsumes_gloss_tokens")

#: What the mechanical path actually yields on `annotations_b8.json`
#: (361 atoms). Pinned by `test_mechanical_path_is_a_measured_null_result`, so
#: the null result is asserted against the real spec rather than asserted in a
#: docstring and demonstrated on a hand-written fixture:
#:
#:   contrary_negation        0   — 22 atoms carry `avoid_`, and NOT ONE of them
#:                                  has its un-negated partner in the vocabulary
#:   entails_nominalisation   0   — every one of the 361 names has exactly one
#:                                  kind, so there is no act/situation pair to
#:                                  bridge
#:   contrary_antonym         1
#:   subsumes_name_tokens    14   — only 14 same-kind proper token-subset pairs
#:   subsumes_gloss_names     5
#:   -------------------------------------------------------------------------
#:   20 edges over 361 atoms, touching ~5% of the vocabulary.
#:
#: The vocabulary is FLAT AND MORPHOLOGICALLY PARALLEL: the annotator produced
#: sibling names (`refuse_answer`, `good_answer`, `engaging_answer`) rather than
#: nested ones, so containment morphology has nothing to bite on.
#:
#: The relation the data DOES have in bulk is shared name tokens (1,625 pairs,
#: 317/361 atoms). That is lexical overlap wearing a relation's name, and using
#: it would re-create the very bag-of-atoms scorer this module replaces —
#: contract §5 invariant 10. It is deliberately NOT a rule.
MECHANICAL_NULL_RESULT = {
    "n_atoms": 361, "n_relations": 20,
    "contrary_negation": 0, "entails_nominalisation": 0, "same_as_key": 0,
    "contrary_antonym": 1, "subsumes_name_tokens": 14, "subsumes_gloss_names": 5,
    "subsumes_gloss_tokens": 0,
}


def derive_mechanical(vocab: dict, rules=DEFAULT_RULES):
    """`(relations, rejections)` from names, glosses and kinds. No model.

    Every rule is stated in its own branch below with the linguistic claim it
    rests on. The result is deterministic: same vocabulary, same edges, in the
    same order, on any machine. On this spec it is also nearly empty — see
    `MECHANICAL_NULL_RESULT`. Kept as the BASELINE the annotated layer is
    measured against, not as the product.
    """
    names = sorted(vocab)
    toks = {n: name_tokens(n) for n in names}
    keys = {n: annotate.vocab_key(n) for n in names}
    gtoks = {n: gloss_tokens(vocab[n].get("gloss")) for n in names}
    kind = {n: vocab[n].get("kind") or "" for n in names}
    df = {n: int(vocab[n].get("n_clauses") or 0) for n in names}

    by_key = defaultdict(list)
    for n in names:
        by_key[keys[n]].append(n)

    out = []

    def emit(rel, a, b, via, evidence):
        if rel in SYMMETRIC and b < a:
            a, b = b, a
        out.append(Relation(rel, a, b, via, evidence, "mechanical"))

    # ---- 1. contrary: X vs avoid_X / not_X. The token sets differ ONLY by a
    #         negation token, so the names denote the same act under opposite
    #         polarity.
    if "contrary_negation" in rules:
        for a in names:
            for b in names:
                if a >= b or kind[a] != kind[b]:
                    continue
                diff = toks[a] ^ toks[b]
                if not diff or not diff <= NEGATION_TOKENS:
                    continue
                if not (toks[a] <= toks[b] or toks[b] <= toks[a]):
                    continue
                emit("contrary", a, b, "contrary_negation",
                     f"token sets differ only by negation {sorted(diff)}")

    # ---- 2. contrary: one token each, and those two tokens are antonyms.
    if "contrary_antonym" in rules:
        for a in names:
            for b in names:
                if a >= b or kind[a] != kind[b]:
                    continue
                da, db = toks[a] - toks[b], toks[b] - toks[a]
                if len(da) != 1 or len(db) != 1:
                    continue
                x, y = next(iter(da)), next(iter(db))
                if _antonymous(x, y):
                    emit("contrary", a, b, "contrary_antonym",
                         f"antonymous tokens {x!r}/{y!r} in otherwise identical names")

    # ---- 3. same_as: identical vocab_key AND identical kind. annotate.py
    #         already aliases within a batch, so survivors are cross-batch
    #         duplicates it could not see.
    if "same_as_key" in rules:
        for key, group in sorted(by_key.items()):
            for i, a in enumerate(sorted(group)):
                for b in sorted(group)[i + 1:]:
                    if kind[a] == kind[b]:
                        emit("same_as", a, b, "same_as_key",
                             f"identical vocab_key {key!r}")

    # ---- 4. entails across kinds: the same concept filed once as an act and
    #         once as a situation (`refuse_request` / `request_refused`). Doing
    #         the act entails the situation obtaining. THE ONLY cross-kind rule.
    if "entails_nominalisation" in rules:
        for key, group in sorted(by_key.items()):
            acts = sorted(n for n in group if kind[n] == "act")
            sits = sorted(n for n in group if kind[n] == "situation")
            for a in acts:
                for s in sits:
                    emit("entails", a, s, "entails_nominalisation",
                         f"same vocab_key {key!r} filed as act and situation")

    # ---- 5. subsumes: a's tokens are a proper subset of b's, same kind, and
    #         the extra tokens are MODIFIERS (no negation). Adding a modifier
    #         narrows: `harm` -> `third_party_harm`.
    if "subsumes_name_tokens" in rules:
        for a in names:
            if not toks[a]:
                continue
            for b in names:
                if a == b or kind[a] != kind[b] or not toks[a] < toks[b]:
                    continue
                extra = toks[b] - toks[a]
                if extra & NEGATION_TOKENS:
                    continue
                emit("subsumes", a, b, "subsumes_name_tokens",
                     f"{sorted(toks[a])} + modifiers {sorted(extra)}")

    # ---- 6. subsumes: b's GLOSS names a. The annotator wrote the broader
    #         concept into the narrower one's definition — a genus statement.
    if "subsumes_gloss_names" in rules:
        for a in names:
            if len(toks[a]) < 2:
                continue            # a single generic token matches everywhere
            for b in names:
                if a == b or kind[a] != kind[b] or toks[a] < toks[b]:
                    continue        # rule 5 already owns the token-subset case
                if toks[a] <= gtoks[b] and not toks[a] <= gtoks[a] - toks[a]:
                    emit("subsumes", a, b, "subsumes_gloss_names",
                         f"gloss of {b} contains every token of {a}")

    # ---- 7. subsumes: a's gloss is a proper token-subset of b's gloss — b's
    #         definition says everything a's does and more. Weakest rule, kept
    #         last so the cycle-breaker prefers the stronger evidence.
    if "subsumes_gloss_tokens" in rules:
        for a in names:
            if len(gtoks[a]) < 3:
                continue
            for b in names:
                if a == b or kind[a] != kind[b]:
                    continue
                if gtoks[a] < gtoks[b]:
                    emit("subsumes", a, b, "subsumes_gloss_tokens",
                         f"gloss tokens of {a} are a proper subset of {b}'s")

    # Cycle-breaking is order-dependent, so fix a principled order: rule
    # priority first, then BROADER-BY-CORPUS-FREQUENCY first. An atom on more
    # clauses is the more general one, so when two rules disagree about
    # direction the frequency-consistent edge is the one that survives.
    prio = {r: i for i, r in enumerate(DEFAULT_RULES)}
    out.sort(key=lambda r: (prio.get(r.via, 99), -df.get(r.a, 0),
                            df.get(r.b, 0), r.a, r.b))
    return validate(out, vocab)


# ------------------------------------------------------------- guardrails

def validate(relations, vocab: dict):
    """`(kept, rejections)` — every guardrail, every rejection counted.

    Order of checks matters and is deliberate: contraries are collected FIRST
    over the whole input, so a pair asserted both contrary and connected loses
    its connection regardless of which came first in the list. A false contrary
    costs recall; a false connection manufactures a match.
    """
    rej = Counter()
    kept, seen = [], set()

    contrary_pairs = {frozenset((r.a, r.b)) for r in relations
                      if r.rel == "contrary" and r.a != r.b
                      and r.a in vocab and r.b in vocab
                      and (vocab[r.a].get("kind") == vocab[r.b].get("kind"))}

    # incremental transitive closure per acyclic relation
    reach = {rel: defaultdict(set) for rel in ACYCLIC}

    for r in relations:
        if r.rel not in RELATIONS:
            rej["bad_relation"] += 1
            continue
        if r.a not in vocab or r.b not in vocab:
            rej["unknown_atom"] += 1
            continue
        if r.a == r.b:
            rej["self_loop"] += 1
            continue
        ka, kb = vocab[r.a].get("kind", ""), vocab[r.b].get("kind", "")
        if r.rel in SAME_KIND_ONLY and ka != kb:
            rej[f"cross_kind_{r.rel}"] += 1
            continue
        rr = r
        if r.rel in SYMMETRIC and r.b < r.a:
            rr = replace(r, a=r.b, b=r.a)
        if rr.rel != "contrary" and frozenset((rr.a, rr.b)) in contrary_pairs:
            rej["contradictory_pair"] += 1
            continue
        k = rr.key if rr.rel not in SYMMETRIC else (rr.rel, rr.a, rr.b)
        if k in seen:
            rej["duplicate"] += 1
            continue
        if rr.rel in ACYCLIC:
            if rr.a in reach[rr.rel][rr.b] or rr.a == rr.b:
                rej["cycle"] += 1
                continue
        seen.add(k)
        kept.append(rr)
        if rr.rel in ACYCLIC:
            R = reach[rr.rel]
            # b (and everything b reaches) is now reachable from a and from
            # everything that reaches a.
            closure = {rr.b} | R[rr.b]
            for src in [rr.a] + [s for s in list(R) if rr.a in R[s]]:
                R[src] |= closure
    return kept, rej


def merge(*relation_lists):
    """Union of relation sets, marking triples BOTH paths produced.

    Agreement is the interesting quantity: an edge both a morphological rule
    and a model independently assert is far better evidenced than either alone,
    and the `both` tag is what lets `explain()` say so.
    """
    out, order = {}, []
    for rels in relation_lists:
        for r in rels:
            rr = replace(r, a=min(r.a, r.b), b=max(r.a, r.b)) \
                if r.rel in SYMMETRIC else r
            if rr.key in out:
                prev = out[rr.key]
                if prev.source != rr.source:
                    out[rr.key] = replace(
                        prev, source="both",
                        via=f"{prev.via}+{rr.via}" if rr.via not in prev.via else prev.via,
                        evidence=prev.evidence or rr.evidence)
            else:
                out[rr.key] = rr
                order.append(rr.key)
    return [out[k] for k in order]


def agreement(mechanical, model):
    """How much the two derivation paths overlap. Reported, never optimised."""
    def keys(rs):
        return {(r.rel, min(r.a, r.b), max(r.a, r.b)) if r.rel in SYMMETRIC
                else r.key for r in rs}
    m, g = keys(mechanical), keys(model)
    both = m & g
    return {"mechanical": len(m), "model": len(g), "both": len(both),
            "mechanical_only": len(m - g), "model_only": len(g - m),
            "jaccard": len(both) / len(m | g) if (m | g) else 0.0}


# ------------------------------------------------------------- the ontology

class Ontology:
    """The relation graph, queried offline.

    Construction is per spec. `reachable` is the only thing the query layer
    needs, and it returns PATHS, not scores, so every match stays auditable.
    """

    def __init__(self, vocab: dict, relations=(), rejections=None,
                 provenance=None):
        self.vocab = dict(vocab)
        self.relations = list(relations)
        self.rejections = Counter(rejections or {})
        self.provenance = dict(provenance or {})

        self._out = defaultdict(list)     # traversable adjacency, undirected
        self._contrary = defaultdict(set)
        self._by_rel = defaultdict(list)
        for r in self.relations:
            self._by_rel[r.rel].append(r)
            if r.rel == "contrary":
                self._contrary[r.a].add(r.b)
                self._contrary[r.b].add(r.a)
            elif r.rel in TRAVERSABLE:
                self._out[r.a].append((r.b, r))
                self._out[r.b].append((r.a, r))
        for n in self._out:
            self._out[n].sort(key=lambda t: (t[0], t[1].rel))

    # -------------------------------------------------------- construction

    @classmethod
    def mechanical(cls, vocab: dict, rules=DEFAULT_RULES) -> "Ontology":
        rels, rej = derive_mechanical(vocab, rules)
        return cls(vocab, rels, rej,
                   {"paths": ["mechanical"], "rules": list(rules)})

    @classmethod
    def from_annotations(cls, source=ANNOTATIONS, model_relations=None,
                         rules=DEFAULT_RULES) -> "Ontology":
        """Mechanical relations over an annotate.py artifact, optionally merged
        with a cached model pass. This is the offline entry point: it never
        calls anything."""
        vocab = load_vocabulary(source)
        rels, rej = derive_mechanical(vocab, rules)
        paths = ["mechanical"]
        if model_relations:
            gm, grej = validate(list(model_relations), vocab)
            rej.update(grej)
            rels, _ = validate(merge(rels, gm), vocab)
            paths.append("model")
        return cls(vocab, rels, rej, {"paths": paths, "rules": list(rules),
                                      "source": str(source)[-60:]})

    @classmethod
    def from_files(cls, annotations=ANNOTATIONS, artifact=ARTIFACT,
                   rules=DEFAULT_RULES) -> "Ontology":
        """Mechanical + the cached model pass IF `ontology.json` exists.

        Missing artifact is not an error: the mechanical layer is the floor and
        must always work, so the tool degrades to it rather than failing.
        """
        model = None
        if artifact and os.path.exists(artifact):
            try:
                with open(artifact) as f:
                    model = [Relation(**{k: d.get(k, "") for k in
                                         ("rel", "a", "b", "via", "evidence", "source")})
                             for d in (json.load(f).get("relations") or [])
                             if d.get("source") in ("model", "both")]
            except (OSError, ValueError, TypeError):
                model = None
        return cls.from_annotations(annotations, model_relations=model, rules=rules)

    # -------------------------------------------------------------- access

    def kind(self, name: str) -> str:
        return (self.vocab.get(name) or {}).get("kind", "")

    def df(self, name: str) -> int:
        return int((self.vocab.get(name) or {}).get("n_clauses") or 0)

    def gloss(self, name: str) -> str:
        return (self.vocab.get(name) or {}).get("gloss", "")

    def by_relation(self, rel: str) -> list:
        return list(self._by_rel.get(rel, ()))

    def contraries(self, name: str) -> set:
        """Atoms mutually exclusive with `name`. Symmetric by construction."""
        return set(self._contrary.get(name, ()))

    def is_acyclic(self, rel: str) -> bool:
        adj = defaultdict(list)
        for r in self._by_rel.get(rel, ()):
            adj[r.a].append(r.b)
        colour = {}

        def visit(n):
            colour[n] = 1
            for m in adj.get(n, ()):
                c = colour.get(m, 0)
                if c == 1 or (c == 0 and not visit(m)):
                    return False
            colour[n] = 2
            return True

        sys.setrecursionlimit(max(3000, len(self.vocab) * 20))
        return all(colour.get(n, 0) or visit(n) for n in sorted(adj))

    # -------------------------------------------------------- reachability

    def reachable(self, name: str, max_hops: int = 2) -> dict:
        """`{atom: Link}` for every atom within `max_hops` traversable edges.

        BFS, so the recorded path is a SHORTEST one. `contrary` is not in the
        adjacency at all — it is a defeater, and traversing it would connect a
        concept to its own negation. The atom itself is included at 0 hops so
        callers do not special-case exact matches.
        """
        if name not in self.vocab:
            return {}
        out = {name: Link(name, name, 0, ())}
        if max_hops <= 0:
            return out
        q = deque([(name, ())])
        while q:
            cur, path = q.popleft()
            if len(path) >= max_hops:
                continue
            for nxt, r in self._out.get(cur, ()):
                if nxt in out:
                    continue
                p = path + (r,)
                out[nxt] = Link(name, nxt, len(p), p)
                q.append((nxt, p))
        return out

    def expand(self, names, max_hops: int = 2) -> dict:
        """`{target: Link}` for a SET of source atoms, keeping the shortest
        link to each target. This is what a behaviour's atom set needs."""
        best = {}
        for n in sorted(set(names)):
            for t, link in self.reachable(n, max_hops).items():
                cur = best.get(t)
                if cur is None or (link.hops, link.source) < (cur.hops, cur.source):
                    best[t] = link
        return best

    # ------------------------------------------------------------- reports

    def stats(self, max_hops: int = 2) -> dict:
        connected = {n for r in self.relations if r.rel in TRAVERSABLE
                     for n in (r.a, r.b)}
        sizes = [len(self.reachable(n, max_hops)) for n in sorted(self.vocab)]
        return {
            "n_atoms": len(self.vocab),
            "n_relations": len(self.relations),
            "by_relation": dict(Counter(r.rel for r in self.relations)),
            "by_rule": dict(Counter(r.via for r in self.relations)),
            "by_source": dict(Counter(r.source for r in self.relations)),
            "connected_fraction": len(connected) / (len(self.vocab) or 1),
            "mean_reachable": sum(sizes) / (len(sizes) or 1),
            "max_reachable": max(sizes, default=0),
            "rejections": dict(self.rejections),
        }

    def save(self, path: str = ARTIFACT):
        with open(path, "w") as f:
            json.dump({"provenance": self.provenance,
                       "rejections": dict(self.rejections),
                       "vocabulary": self.vocab,
                       "relations": [r.as_dict() for r in self.relations]},
                      f, indent=1)
        return path

    @classmethod
    def load(cls, path: str = ARTIFACT) -> "Ontology":
        with open(path) as f:
            d = json.load(f)
        rels = [Relation(**{k: r.get(k, "") for k in
                            ("rel", "a", "b", "via", "evidence", "source")})
                for r in d.get("relations") or []]
        return cls(d.get("vocabulary") or {}, rels, d.get("rejections"),
                   d.get("provenance"))


# ------------------------------------------- the annotation pass (PRIMARY)

#: The pass structure. Each call sees the WHOLE vocabulary and is asked for ONE
#: relation type. Splitting the relation space rather than the vocabulary is
#: deliberate: the pairs worth having are precisely the ones that would straddle
#: a vocabulary split (`harm_prevention` and `third_party_harm` are 200 names
#: apart alphabetically), so a vocabulary-batched pass can never propose them.
#: Four focused calls also each get the model's full output budget for one
#: relation, instead of one call rationing its budget across four.
PASSES = (
    ("situation_subsumption",
     "Emit ONLY `subsumes` relations where BOTH concepts have kind `situation`. "
     "a must be the strictly BROADER circumstance."),
    ("act_subsumption",
     "Emit ONLY `subsumes` relations where BOTH concepts have kind `act`. "
     "a must be the strictly BROADER act."),
    ("act_situation_correspondence",
     "Emit ONLY `entails` relations from an `act` to the `situation` it brings "
     "about or presupposes, and from an `act` to the `value` it serves. This is "
     "the only place a relation may cross kinds."),
    ("contrariety",
     "Emit ONLY `contrary` relations: pairs that CANNOT both hold. Both "
     "concepts must have the SAME kind. Polarity pairs (doing X / avoiding X, "
     "over-X / under-X) are the clearest cases. Also emit `same_as` for any "
     "pair that are genuine synonyms filed twice."),
)

SYSTEM = """\
You are building a small ontology over a fixed, CLOSED vocabulary of concepts
extracted from a policy document. Each concept has a KIND:

  situation  a circumstance that obtains
  act        something the assistant does
  entity     a party, object or artifact
  value      a goal or principle being served

Return relations between concepts THAT ARE BOTH IN THE LIST BELOW. You may not
introduce, rename or invent a concept; a triple naming anything not in the list
is discarded.

Relations:
  subsumes  a is strictly BROADER than b (a covers b and more). Both concepts
            must have the SAME kind.
  entails   an instance of a is necessarily also an instance of b. This is the
            only relation that may cross kinds (an act may entail a situation).
  contrary  a and b are mutually exclusive: if one holds the other does not.
            Same kind. Include polarity pairs (doing X / avoiding X).
  same_as   genuine synonyms that should have been one concept. Same kind.

Be conservative. A wrong `subsumes` is worse than a missing one. Do not emit a
relation merely because two concepts are topically related — "both about
safety" is NOT a relation. Do not emit the reverse of a relation you already
gave, and do not emit cycles.

Output STRICT JSON and nothing else:
{"relations": [{"rel": "subsumes", "a": "<name>", "b": "<name>",
                "evidence": "<short reason>"}, ...]}
"""


def render_vocabulary(items) -> str:
    return "\n".join(f"- {n} [{e.get('kind','')}]: {e.get('gloss','')}"
                     for n, e in items)


def render_prompt(items, task: str = "", name: str = "all_relations"):
    """`(system, user)` for one pass over the vocabulary.

    The vocabulary block is the ENTIRE input; there is no corpus, no behaviour
    and no panel in this prompt. That is not just economy — it is what makes
    invariants 8 and 9 structural rather than a promise: a prompt that never
    sees a label cannot be fitted to one.
    """
    user = (f"TASK ({name}): {task}\n\n" if task else "") + (
        f"CONCEPT LIST ({len(items)} concepts). Relations may only name "
        f"concepts from THIS list.\n\n"
        + render_vocabulary(items)
        + "\n\nReturn the JSON object now.")
    return SYSTEM, user


def parse_response(text, vocab: dict):
    """`(relations, rejections)` from one model reply. Nothing invented."""
    rej = Counter()
    if not text:
        return [], rej
    s = str(text)
    i, j = s.find("{"), s.rfind("}")
    if i < 0 or j <= i:
        rej["unparseable"] += 1
        return [], rej
    try:
        data = json.loads(s[i:j + 1])
    except ValueError:
        rej["unparseable"] += 1
        return [], rej
    out = []
    for d in (data.get("relations") or []) if isinstance(data, dict) else []:
        if not isinstance(d, dict):
            rej["malformed"] += 1
            continue
        rel, a, b = d.get("rel"), d.get("a"), d.get("b")
        if rel not in RELATIONS:
            rej["bad_relation"] += 1
            continue
        if a not in vocab or b not in vocab:
            rej["unknown_atom"] += 1
            continue
        out.append(Relation(rel, a, b, "model",
                            str(d.get("evidence") or "")[:200], "model"))
    return out, rej


def run_annotation_pass(client, vocab: dict, passes=PASSES):
    """Ask a model to ANNOTATE relations over the vocabulary. Once per spec.

    This is the primary derivation path; `derive_mechanical` is its baseline.
    `client` follows providers.py's `complete(system, user) -> str | None`; the
    dry-run client returns None, which is handled rather than crashed on, so a
    dry run exercises the whole path including parse and validation.
    """
    items = sorted(vocab.items())
    rels, rej = [], Counter()
    per_pass = {}
    for name, task in passes:
        system, user = render_prompt(items, task, name)
        text = client.complete(system, user)
        if not text:
            rej["no_response"] += 1
            per_pass[name] = 0
            continue
        got, r = parse_response(text, vocab)
        per_pass[name] = len(got)
        rels.extend(got)
        rej.update(r)
    return rels, rej, per_pass


def estimate_cost(vocab: dict, passes=PASSES, price_per_mtok=None,
                  max_tokens: int = 8000):
    n = max(1, len(passes))
    chars = (len(render_vocabulary(sorted(vocab.items()))) + len(SYSTEM)) * n
    in_tok = chars / 4
    out_tok = max_tokens * n
    if not price_per_mtok:
        return {"calls": n, "input_tokens": int(in_tok),
                "output_tokens": int(out_tok), "usd": None}
    return {"calls": n, "input_tokens": int(in_tok), "output_tokens": int(out_tok),
            "usd": round(in_tok / 1e6 * price_per_mtok[0]
                         + out_tok / 1e6 * price_per_mtok[1], 4)}


# -------------------------------------------------------------------- CLI

def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--annotations", default=ANNOTATIONS)
    ap.add_argument("--out", default=ARTIFACT)
    ap.add_argument("--pass", dest="passes", action="append", default=None,
                    help=f"restrict to these passes (repeatable); "
                         f"default all {len(PASSES)}: "
                         + ", ".join(n for n, _ in PASSES))
    ap.add_argument("--max-tokens", type=int, default=8000)
    ap.add_argument("--provider", default="luna")
    ap.add_argument("--providers", default="providers.json")
    ap.add_argument("--prompt-log", default="prompt_log")
    ap.add_argument("--live", action="store_true",
                    help="make the ONE real vocabulary call; without this "
                         "nothing leaves the machine")
    ap.add_argument("--print-prompt", action="store_true")
    ap.add_argument("--stats", action="store_true",
                    help="mechanical derivation only, offline, no artifact write")
    ap.add_argument("--show", default=None,
                    help="print every relation touching this atom")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    vocab = load_vocabulary(args.annotations)
    if not vocab:
        print(f"no vocabulary in {args.annotations}", file=sys.stderr)
        return 1
    onto = Ontology.mechanical(vocab)
    s = onto.stats()
    print(f"{s['n_atoms']} atoms — MECHANICAL BASELINE: {s['n_relations']} "
          f"relations {s['by_relation']}")
    print(f"    by rule: {s['by_rule']}")
    print(f"    connected {s['connected_fraction']:.1%} of atoms; "
          f"mean reachable within 2 hops {s['mean_reachable']:.1f}")
    print(f"    rejections: {ldict(s['rejections'])}")
    if s["n_relations"] < 0.1 * s["n_atoms"]:
        print("    !! NULL RESULT on this vocabulary (see "
              "MECHANICAL_NULL_RESULT). Note the annotated pass below is NOT "
              "a justified fix: relation expansion was measured to HURT the "
              "query on every behaviour. See structural.CONSTANTS['max_hops'].")

    if args.show:
        for r in onto.relations:
            if args.show in (r.a, r.b):
                print("   ", r.describe(), "|", r.evidence)
        return 0
    if args.stats:
        return 0

    passes = ([p for p in PASSES if p[0] in set(args.passes)]
              if args.passes else list(PASSES))
    if args.print_prompt:
        name, task = passes[0]
        system, user = render_prompt(sorted(vocab.items()), task, name)
        print("### SYSTEM\n" + system + "\n\n### USER\n" + user)
        return 0

    cfg = annotate.provider_config(args.provider, args.providers)
    cfg.max_tokens = args.max_tokens
    est = estimate_cost(vocab, passes, cfg.price_per_mtok, args.max_tokens)
    print(f"    annotation pass: {est['calls']} call(s), ~{est['input_tokens']} "
          f"in / {est['output_tokens']} out tokens"
          + (f" ≈ ${est['usd']:.4f}" if est["usd"] is not None else ""))
    client = annotate.make_annotate_client(cfg, live=args.live,
                                           log_dir=args.prompt_log)
    if not args.live:
        print("DRY RUN (no network). Prompts written to "
              f"{args.prompt_log}/. Pass --live to make the real calls.")
    model_rels, mrej, per_pass = run_annotation_pass(client, vocab, passes)
    kept, vrej = validate(model_rels, vocab)
    mrej.update(vrej)
    print(f"    annotator returned {len(model_rels)} triples {per_pass}, "
          f"{len(kept)} survived validation; rejections {ldict(mrej)}")
    if not kept:
        print("    nothing to merge — no annotated relations")
    merged, mergerej = validate(merge(onto.relations, kept), vocab)
    ag = agreement(onto.relations, kept)
    print(f"    agreement: {ag}")
    final = Ontology(vocab, merged, onto.rejections + mrej + mergerej,
                     {"paths": ["mechanical"] + (["model"] if kept else []),
                      "provider": cfg.name, "model": cfg.model,
                      "live": bool(args.live), "agreement": ag,
                      "annotations": os.path.basename(args.annotations)})
    if args.live:
        final.save(args.out)
        print(f"    -> {args.out}")
    else:
        print("    artifact NOT written (dry run)")
    return 0


def ldict(d):
    return {k: v for k, v in sorted(d.items()) if v} or "none"


if __name__ == "__main__":
    raise SystemExit(main())
