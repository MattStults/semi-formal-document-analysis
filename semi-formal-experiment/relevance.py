"""Behaviour -> spec-clause relevance, computed entirely offline.

The premise of the whole spike is **annotate once, query many times instantly**.
So nothing in this module may call a model, load an embedding model, or touch
the network: a query-time model call would just BE the baseline we are trying
to beat. What is left is lexical retrieval over the annotation artifact, which
is fast, deterministic, auditable, and swappable across specs.

Signals combined (none of them is exact atom-name overlap alone — that channel
is far too sparse to compete on its own):

  lex       IDF-weighted cosine between the behaviour's text (name + definition
            + its atoms' names and glosses) and the clause's text (quote + its
            atoms' names and glosses), after light stemming. Short queries are
            the failure mode of bare cosine, so the query is first expanded by
            Rocchio pseudo-relevance feedback over its own top hits — still
            pure arithmetic over the corpus, no model.
  atom      shared (name, kind) atom pairs, IDF-WEIGHTED by how many clauses
            each atom appears on, with a stopword floor. This is not optional
            polish: a clause annotated only with `user`/`model` is fully
            "covered" and discriminates nothing, and unweighted atom overlap
            fires on those everywhere. A name match under a drifted kind gets
            partial credit rather than nothing, because kind is unstable
            across annotation batches.
  kind      agreement between the atom KINDS the behaviour is about and the
            kinds the clause's atoms carry.
  section   proximity: a clause inherits part of its section's best local
            score. This is what reaches example blocks and framing prose, which
            carry almost no shared vocabulary with a behaviour definition but
            are exactly what the panel cites (313 of 863 panel passages sit in
            example blocks).

`rank` returns a continuous score for ranking; `predict` thresholds it into the
binary relevant/not decision the panel makes; `sweep` returns the whole curve so
no single threshold can be quoted without its neighbours.

--------------------------------------------------------------------------
INTERFACE REQUIRED FROM annotate.py  (this is the contract; adapt to it)
--------------------------------------------------------------------------
An atom is a dict. The ONLY required key is `name`. Every other key is optional
and its absence must never raise:

    {"name":     "third_party_harm",   # required, snake_case identifier
     "kind":     "situation",          # optional, small closed set
     "gloss":    "someone outside the conversation is harmed",   # optional
     "span_id":  "s12",                # optional
     "quote":    "...verbatim span...",# optional
     "clause_id": "m0207",             # required in atom-major/flat shapes
     "locator":  "model_spec@... > ¶4"}# optional

`load_annotations` accepts any of three container shapes, so annotate.py may
emit whichever is natural:

  clause-major  {"clauses": [{"clause_id": "m0207", "atoms": [atom, ...]}, ...]}
  atom-major    {"atoms": [{...atom..., "quote_spans": [{"clause_id": ...}]}]}
                (this is the shape `vocabulary_pilot.json` already uses)
  flat          [atom, ...]  with `clause_id` on each atom

Anything unparseable is skipped, not fatal. A clause with no annotation still
ranks — it falls back to its own quote text.

Usage:
    .venv/bin/python relevance.py helpfulness      # top 20 clauses, offline
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import warnings
from collections import Counter, defaultdict
from dataclasses import dataclass, field

import measure_join

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = "relevance_fixture.json"
CLAUSES = os.path.join(HERE, "modelspec_clauses.json")

#: Keys every atom carries after loading. Only `name` is required upstream;
#: the loader fills the rest with "" so downstream code never guards.
ATOM_FIELDS = ("name", "kind", "gloss", "span_id", "quote", "clause_id",
               "locator")

#: annotate.py's closed kind set. A behaviour description reads "in SITUATION
#: the model performs ACT toward ENTITY at the expense of VALUE", so kind is
#: load-bearing for matching: `refuse_request` (act) and `request_refused`
#: (situation) are deliberately distinct atoms.
ATOM_KINDS = ("situation", "act", "entity", "value")

DEFAULT_SWEEP = tuple(round(0.02 * i, 2) for i in range(51))  # 0.00 .. 1.00


def replace_weights(w: "Weights", **kw) -> "Weights":
    """`dataclasses.replace` for Weights, so ablations name only what changes."""
    import dataclasses
    return dataclasses.replace(w, **kw)

#: Operating point, selected on **MCC**, not F1.
#:
#: Selecting on F1 and reporting MCC is self-defeating on this task: F1's floor
#: is 0.44-0.59 (the all-relevant predictor), so its argmax sits at or beside
#: the predict-everything point — where MCC is 0 BY CONSTRUCTION. The previous
#: default (0.30, F1-derived) did exactly that and produced a reported MCC of
#: ~0.04, which was read as "the method learned nothing".
#:
#: Mean MCC: +0.274 at 0.18; +0.1876 at the old 0.30. NOTE what that second
#: number is: THIS scorer at the OLD threshold. It is **not** a pre-fix number.
#: The real pre-fix default was +0.1526 and pre-fix LOBO was +0.1635.
#: Per-behaviour optima differ (+0.215 @0.18, +0.358 @0.18, +0.443 @0.58), so
#: one constant is a compromise; fit per-behaviour where you can.
#:
#: ⚠️ DO NOT QUOTE +0.274 AS A RESULT. It is the maximum of a 51-point grid
#: selected on the very panel it is then evaluated against — an IN-SAMPLE
#: CEILING. Under leave-one-behaviour-out selection the honest figure was
#: **+0.187**, and the median over the sane threshold band +0.222.
#:
#: ⛔ AND DO NOT REPORT +0.187 EITHER — THIS BANNER USED TO INSTRUCT YOU TO.
#: Every number in this block is on the PUBLISHED universe, which deleted each
#: passage the panel scored 0 and with it the true-negative credit the panel
#: had earned. All of them are inflated, roughly 2x, in the tool's favour.
#: They are kept because the RELATIVE argument (in-sample argmax vs held-out)
#: is still correct and still worth reading; the levels are not quotable
#: against anything. For a reportable number use the true 589-passage universe
#: via `benchmark.load_true_panel` — never `load_panel`.
#:
#: The shipped path no longer takes a threshold constant at all: `predict()`
#: derives its operating point label-free (Otsu). Nested selection remains the
#: correct treatment for the swept path and is still NOT implemented.
#:
#: ⚠️ AND DO NOT CLAIM THE section_path FIX RECOVERED THE METHOD. Best-MCC
#: *over the sweep* moved only +0.2637 → +0.2743 (Δ +0.011). The bug was a
#: CALIBRATION defect — it moved where the good operating point sits on the
#: threshold axis (0.36 → 0.18), not how well the method discriminates.
#: Like-for-like: pre-fix LOBO +0.1635 → post-fix +0.1867, Δ **+0.023**.
#: (An earlier version of this comment compared post-fix LOBO against +0.1876
#: and called them indistinguishable. That comparison was never run — +0.1876
#: is this scorer at the old threshold, not the pre-fix scorer. The conclusion
#: survives but the fix is slightly BETTER than that framing implied.)
#: An earlier version also claimed "calibration is worth ~0.26 MCC"; that
#: compared the grid maximum against a trough (0.30 ranks 26th of 30 in the
#: sane band) and was wrong.
#:
#: The earlier note here claimed "the curve is FLAT from 0.00 to 0.30". That was
#: not a property of the scorer — it was the fingerprint of a bug
#: (`benchmark._clause_rows` dropped `section_path`, collapsing the section
#: channel to a constant that pinned the minimum score at ~0.30).
DEFAULT_THRESHOLD = 0.18


# ------------------------------------------------------------ tokenisation

STOPWORDS = frozenset("""
a an and are as at be been being but by can could do does doing for from had
has have having he her here hers him his how i if in into is it its itself may
me might must my no nor not of off on once only or other our out over own same
shall she should so some such than that the their them then there these they
this those through to too under until up very was we were what when where
which while who whom why will with would you your yours it's don't
""".split())

_WORD = re.compile(r"[a-z][a-z']+")
_SUFFIXES = ("iveness", "fulness", "ations", "ation", "ements", "ement",
             "ingly", "edly", "ally", "ness", "ions", "ing", "ies", "ful",
             "ive", "ion", "ers", "est", "ed", "es", "ly", "er", "s")


def stem(word: str) -> str:
    """Deliberately crude suffix stripping.

    It exists to collapse `helpful`/`helpfulness`/`unhelpfulness` and
    `harm`/`harming`/`harmful` onto one term, because behaviour definitions and
    spec prose describe the same idea in different parts of speech. It is not a
    linguistics claim; over-stemming costs precision on rare terms, which IDF
    already down-weights. Nothing below a 4-character root is touched, so short
    words are never mangled.
    """
    w = word.strip("'")
    changed = True
    while changed and len(w) > 4:
        changed = False
        for suf in _SUFFIXES:
            if w.endswith(suf) and len(w) - len(suf) >= 4:
                w = w[:-len(suf)]
                if w.endswith("i"):
                    w = w[:-1] + "y" if len(w) > 4 else w
                changed = True
                break
    return w


def tokens(text: str) -> set:
    """Stemmed content tokens. Underscores split (atom names are snake_case)."""
    text = (text or "").lower().replace("_", " ")
    return {stem(w) for w in _WORD.findall(text) if w not in STOPWORDS} - {""}


def _counts(text: str) -> Counter:
    text = (text or "").lower().replace("_", " ")
    return Counter(stem(w) for w in _WORD.findall(text) if w not in STOPWORDS)


# ---------------------------------------------------------------- vectors

def _tfidf(counts: Counter, idf: dict) -> dict:
    """Sub-linear tf, IDF weight, L2-normalized. Terms absent from the corpus
    get no weight at all — they cannot discriminate between clauses."""
    v = {t: (1.0 + math.log(c)) * idf[t] for t, c in counts.items() if t in idf}
    norm = math.sqrt(sum(w * w for w in v.values()))
    return {t: w / norm for t, w in v.items()} if norm else {}


def _cosine(a: dict, b: dict) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(w * b[t] for t, w in a.items() if t in b)


# ------------------------------------------------------------ annotations

def _atom(raw, clause_id: str = "") -> dict | None:
    if not isinstance(raw, dict):
        return None
    name = raw.get("name")
    if not isinstance(name, str) or not name.strip():
        return None
    out = {k: raw.get(k) or "" for k in ATOM_FIELDS}
    out["name"] = name.strip()
    out["clause_id"] = str(out["clause_id"] or clause_id)
    return out


def load_annotations(source) -> dict:
    """`{clause_id: [atom, ...]}` from a path, a parsed object, or nothing.

    Tolerant on purpose: annotate.py is being built concurrently and this must
    not become the thing that blocks on its exact output shape. A missing file,
    a malformed record, an atom with only a `name` — all survive. See the module
    docstring for the three accepted container shapes.
    """
    if source is None:
        return {}
    if isinstance(source, str):
        try:
            with open(source) as f:
                source = json.load(f)
        except (OSError, ValueError):
            return {}

    records = source
    if isinstance(source, dict):
        for key in ("clauses", "annotations", "rows"):
            if isinstance(source.get(key), list):
                records = source[key]
                break
        else:
            records = source.get("atoms") if isinstance(source.get("atoms"), list) else []
    if not isinstance(records, list):
        return {}

    out: dict = defaultdict(list)
    for rec in records:
        if not isinstance(rec, dict):
            continue
        # clause-major: a record carrying an `atoms` list
        if isinstance(rec.get("atoms"), list):
            cid = rec.get("clause_id") or rec.get("id")
            if not cid:
                continue
            for a in rec["atoms"]:
                atom = _atom(a, str(cid))
                if atom:
                    out[str(cid)].append(atom)
            continue
        # atom-major: one atom, many spans, each naming its clause
        spans = rec.get("quote_spans")
        if isinstance(spans, list) and spans:
            for sp in spans:
                if not isinstance(sp, dict):
                    continue
                cid = sp.get("clause_id")
                if not cid:
                    continue
                atom = _atom({**rec, **{k: sp.get(k) for k in
                                        ("quote", "locator", "span_id")}}, str(cid))
                if atom:
                    out[str(cid)].append(atom)
            continue
        # flat: one atom that names its own clause
        atom = _atom(rec)
        if atom and atom["clause_id"]:
            out[atom["clause_id"]].append(atom)
    return dict(out)


def _atom_text(atoms) -> str:
    return " ".join(f"{a['name']} {a['gloss']}" for a in atoms)


#: Every distinct reason the atom channel was found inert, in call order.
#: Kept as module state so a caller (or a test) can assert the warning fired
#: rather than trusting that someone saw it scroll past.
ATOM_CHANNEL_WARNINGS: list = []


def warn_atom_channel_disabled(reason: str) -> None:
    """Shout when the ontology channel is switched off.

    The atom channel carries 0.6 of the scoring weight. When it is inert the
    tool is a pure lexical baseline wearing an ontology's name, and every
    number it produces is a control number. That has to be impossible to miss:
    a silent empty query-atom set is precisely how this hid before.
    """
    msg = f"ATOM CHANNEL DISABLED — {reason}. Scores are a LEXICAL BASELINE, " \
          f"not an ontology result; do not attribute them to annotate.py."
    if msg not in ATOM_CHANNEL_WARNINGS:
        ATOM_CHANNEL_WARNINGS.append(msg)
        warnings.warn(msg, RuntimeWarning, stacklevel=2)
        print(f"WARNING: {msg}", file=sys.stderr)


# ------------------------------------------------------------- behaviours

@dataclass
class Behaviour:
    """The query side. `atoms` is optional — a bare name + definition works,
    which is exactly the 'given a behaviour description' entry point."""
    slug: str
    name: str = ""
    definition: str = ""
    atoms: list = field(default_factory=list)

    @property
    def text(self) -> str:
        return f"{self.name} {self.definition} {_atom_text(self.norm_atoms)}"

    @property
    def norm_atoms(self) -> list:
        out = []
        for a in self.atoms:
            n = _atom(a)
            if n:
                out.append(n)
        return out

    @property
    def atom_names(self) -> set:
        return {a["name"] for a in self.norm_atoms}

    @property
    def atom_kinds(self) -> set:
        return {a["kind"] for a in self.norm_atoms if a["kind"]}


BEHAVIOUR_ATOMS = "behavior_atoms.json"


def load_behaviour_atoms(source=None) -> dict:
    """`{slug: [atom, ...]}` — the QUERY side of the ontology.

    This artifact exists because the panel file has no `atoms` key: its
    behaviours carry only `category`/`coverage`/`definition`/`id`/`name`/`slug`.
    Sourcing query atoms from the panel therefore yielded the empty set on
    every real query, which silently multiplied the whole atom channel by zero
    — the ontology was built for a matcher that never ran. Behaviour atoms are
    produced ONCE PER BEHAVIOUR by `behavior_atoms.py` and cached to disk, so
    queries stay offline and "annotate once, query many" is preserved.

    Accepted shapes (tolerant, like `load_annotations`):
        {"helpfulness": {"atoms": [{name, kind, gloss}, ...]}, ...}
        {"behaviours": [{"slug": ..., "atoms": [...]}, ...]}
        {"helpfulness": [{name, kind, gloss}, ...]}
    """
    if source is None:
        source = os.path.join(HERE, BEHAVIOUR_ATOMS)
    if isinstance(source, str):
        try:
            with open(source) as f:
                source = json.load(f)
        except (OSError, ValueError):
            return {}
    out: dict = {}
    if isinstance(source, dict) and isinstance(source.get("behaviours"), list):
        source = {b.get("slug") or b.get("id"): b
                  for b in source["behaviours"] if isinstance(b, dict)}
    if not isinstance(source, dict):
        return {}
    for slug, val in source.items():
        if not isinstance(slug, str) or slug.startswith("_"):
            continue
        raw = val.get("atoms") if isinstance(val, dict) else val
        if not isinstance(raw, list):
            continue
        atoms = [a for a in (_atom(x) for x in raw) if a]
        if atoms:
            out[slug] = atoms
    return out


def behaviour_from_panel(raw: dict, atoms=None) -> Behaviour:
    """Adapt one entry of the panel's `behaviours` list.

    `atoms` is either the behaviour's own atom list or the whole
    `{slug: [atom]}` map from `load_behaviour_atoms`. It is NOT read from
    `raw` — the panel file has no atoms and never did.
    """
    slug = raw.get("slug") or raw.get("id") or ""
    if isinstance(atoms, dict):
        atoms = atoms.get(slug)
    return Behaviour(slug=slug,
                     name=raw.get("name") or "",
                     definition=raw.get("definition") or "",
                     atoms=list(atoms or []))


def behaviours_from_panel(panel: dict, atoms_source=None) -> dict:
    """`{slug: Behaviour}` for a whole panel, with behaviour atoms attached.

    Warns LOUDLY, once, if the atom artifact is missing — a silent empty set
    here is exactly the failure that hid the dead atom channel.
    """
    atoms = load_behaviour_atoms(atoms_source)
    if not atoms:
        warn_atom_channel_disabled(
            f"no behaviour atoms found (looked for {atoms_source or BEHAVIOUR_ATOMS!r})")
    return {slug: behaviour_from_panel(b, atoms) for slug, b in panel.items()}


# ----------------------------------------------------------------- weights

@dataclass(frozen=True)
class Weights:
    """Every knob in one place, so a reported number can name the setting that
    produced it.

    ⚠️ PROVENANCE — corrected. An earlier version of this docstring said "these
    defaults were HAND-SET … not fitted or swept. Only `DEFAULT_THRESHOLD` is
    sweep-derived." **That was false, and it was contradicted twenty lines below
    in this same class.** TWO constants were selected by reading results off the
    panel that scores the tool:

      * `DEFAULT_THRESHOLD = 0.18` — in-sample argmax of a 51-point grid.
      * `kind = 0.0` — justified below by a panel MCC sweep.

    Contract §5 invariant 9 says **nothing may be fitted to the panel**: it is a
    measuring instrument, not training data. Both of the above violate it.
    Disclosure is not compliance — the fit is worth +0.274 (in-sample) versus
    +0.187 (LOBO), i.e. **0.087 MCC, ~47% of the quoted headline.**

    Everything else here IS hand-set from the design reasoning in the module
    docstring. `benchmark.py --ablate` measures what each channel actually
    contributes; run it before attributing a result to any weight.

    Note also that three of the four type-related knobs below are provably dead
    on this artifact: `kind` is 0.0; `kind_mismatch_discount` fires on 0 of 70
    query atoms because kind is a *function of name* here (all 361 names have
    exactly one kind); and `atom_stopword_frac` implies a cutoff of 148 clauses
    while the maximum atom document frequency is 43, so nothing is ever
    stopworded. **No kind-AGREEMENT operation can add information on this
    artifact at any weight.** Typing can only be load-bearing through structural
    ROLE — which slot an atom fills in a typed query — which is what
    `structural.py` is for."""
    lex: float = 1.0
    atom: float = 0.6
    #: Set to 0.0. The ORIGINAL justification here ("removing it improves mean
    #: best-F1 from 0.511 to 0.524, so it is net-harmful") is VOID: those
    #: numbers came from the broken loader and from F1 ranking, both since
    #: corrected. Note also that with this weight at 0.0 the `-kind` ablation
    #: row is *vacuous* — it is bit-identical to `full` (+0.339, diff exactly
    #: 0.000), so it cannot evidence anything about this channel either way.
    #:
    #: Re-derived honestly under the repaired loader, ranking on MCC:
    #:     kind=0.00  best MCC +0.3387   @0.18 +0.2743
    #:     kind=0.30  best MCC +0.3261   @0.18 +0.1918
    #:     kind=1.00  best MCC +0.2802   @0.18 +0.0611
    #: On a COARSE grid this looks monotone, and an earlier version of this
    #: comment concluded "monotone degradation, so 0.0 is correct". That
    #: overstates it. On a finer grid the curve is NOT monotone
    #: (0.05 +0.3289, 0.10 +0.3263, 0.15 +0.3328, 0.20 +0.3231, 0.30 +0.3261),
    #: and the paired bootstrap for full vs kind=0.30 is +0.0126,
    #: 95% CI [-0.0097, +0.0339], P(>0)=0.82 — it SPANS ZERO. Only kind=1.00 is
    #: distinguishable (+0.0585, CI [+0.0109, +0.0812]).
    #: Honest statement: **0.0 is indistinguishable from 0.30 within noise;
    #: 1.0 is clearly worse; 0.0 is retained as the simplest of the
    #: indistinguishable settings.** Not because it was shown better. The mechanism: kind agreement is already carried by
    #: `atom`, which matches on (name, kind); scoring it again double-counts and
    #: rewards clauses sharing a kind distribution without sharing a concept.
    kind: float = 0.0
    section: float = 0.45
    section_top_k: int = 3
    expansion_docs: int = 12
    expansion_terms: int = 25
    expansion_beta: float = 0.5
    #: Credit for a name match whose KIND disagrees. Kind instability across
    #: annotation batches (the same concept filed `situation` here and `act`
    #: there) would otherwise turn a real match into a total miss; a discount
    #: keeps the signal without erasing the deliberate act/situation contrast.
    kind_mismatch_discount: float = 0.4
    #: An atom on more than this fraction of clauses is treated as a stopword
    #: and contributes nothing at all.
    atom_stopword_frac: float = 0.25


# --------------------------------------------------------------- the index

class RelevanceIndex:
    """Built once over (clauses, annotations); queried per behaviour.

    `clauses` rows need `id` and `quote`; `section_path`, `kind` and `locator`
    are used when present and tolerated when absent.
    """

    def __init__(self, clauses, annotations=None, weights: Weights | None = None):
        self.weights = weights or Weights()
        self.annotations = load_annotations(annotations) if not isinstance(
            annotations, dict) or annotations is None else {
                k: [a for a in (_atom(x, k) for x in v) if a]
                for k, v in annotations.items()}
        self.clauses = [dict(c) for c in clauses]
        self.ids = [str(c.get("id")) for c in self.clauses]
        self.by_id = dict(zip(self.ids, self.clauses))

        self._atoms = {cid: self.annotations.get(cid, []) for cid in self.ids}
        self._names = {cid: {a["name"] for a in ats}
                       for cid, ats in self._atoms.items()}
        self._kinds = {cid: {a["kind"] for a in ats if a["kind"]}
                       for cid, ats in self._atoms.items()}
        #: (name -> kinds it was filed under) per clause, for the discounted
        #: kind-mismatch match.
        self._name_kinds = {}
        for cid, ats in self._atoms.items():
            d = defaultdict(set)
            for a in ats:
                d[a["name"]].add(a["kind"])
            self._name_kinds[cid] = dict(d)

        # ATOM IDF. Flagged by the annotate.py agent as the single most likely
        # way a good-looking artifact yields a bad F1: a clause annotated only
        # with `user`/`model`/`helpfulness` is fully "covered" and discriminates
        # nothing. An atom on 400 of 593 clauses is a stopword and must
        # contribute ~0; an atom on 3 clauses must dominate. Same treatment
        # terms get — because it is the same problem.
        self.atom_df = Counter(n for cid in self.ids for n in self._names[cid])
        n_docs = len(self.ids) or 1
        cutoff = self.weights.atom_stopword_frac * n_docs
        #: Atoms above the cutoff are FLOORED to zero, not merely down-weighted.
        #: IDF alone still leaves a stopword atom a third of a rare atom's
        #: weight, which at a 9-17% base rate is enough to fire everywhere and
        #: sink precision.
        self.atom_stopwords = {n for n, df in self.atom_df.items() if df > cutoff}
        self.atom_idf = {n: (0.0 if n in self.atom_stopwords
                             else math.log(1.0 + n_docs / (1.0 + df)))
                         for n, df in self.atom_df.items()}
        self._atom_norm = max(self.atom_idf.values(), default=0.0) or 1.0

        docs = {cid: _counts(f"{c.get('quote', '')} {_atom_text(self._atoms[cid])}")
                for cid, c in zip(self.ids, self.clauses)}
        n = len(docs) or 1
        df = Counter(t for d in docs.values() for t in d)
        # smoothed idf; a term in every clause still gets a small positive
        # weight rather than exactly zero, so an all-common-words query is
        # ranked (badly) instead of collapsing to an undefined vector.
        self.idf = {t: math.log(1.0 + n / (1.0 + c)) for t, c in df.items()}
        self.vectors = {cid: _tfidf(d, self.idf) for cid, d in docs.items()}

        self._section = {}
        for cid, c in zip(self.ids, self.clauses):
            path = tuple(c.get("section_path") or [])
            self._section[cid] = path
        self._members = defaultdict(list)
        for cid, path in self._section.items():
            self._members[path].append(cid)

    # ---------------------------------------------------------- construction

    @classmethod
    def from_files(cls, clauses_path: str = CLAUSES, annotations_path=None,
                   weights: Weights | None = None) -> "RelevanceIndex":
        """Real clause file + whatever annotation artifact exists.

        Defaults to the shipped fixture so the module is runnable today; point
        `annotations_path` at annotate.py's output when it lands.
        """
        rows = measure_join.clause_rows(clauses_path)
        # The 6-clause fixture is explicitly OPT-IN. Defaulting to it made
        # `relevance.py helpfulness` return the fixture's own m0450
        # ("Be creative") at 1.000 — a demo of the fixture, not of the tool.
        ann = load_annotations(annotations_path) if annotations_path else {}
        if not ann:
            warn_atom_channel_disabled(
                f"no clause annotations at {annotations_path!r}"
                if annotations_path else
                "RelevanceIndex.from_files() called with no annotations_path")
        return cls(rows, ann, weights)

    # --------------------------------------------------------------- scoring

    def _query_vector(self, behaviour: Behaviour) -> dict:
        q = _tfidf(_counts(behaviour.text), self.idf)
        w = self.weights
        if not q or w.expansion_terms <= 0 or w.expansion_docs <= 0:
            return q
        # Rocchio pseudo-relevance feedback. No model, no supervision: the
        # corpus's own top hits supply the vocabulary the short definition
        # lacks ("refusal" -> "decline", "comply", "request").
        top = sorted(self.ids, key=lambda c: -_cosine(q, self.vectors[c]))
        top = [c for c in top[:w.expansion_docs] if _cosine(q, self.vectors[c]) > 0]
        if not top:
            return q
        centroid: dict = defaultdict(float)
        for cid in top:
            for t, wt in self.vectors[cid].items():
                centroid[t] += wt / len(top)
        extra = sorted(((t, v) for t, v in centroid.items() if t not in q),
                       key=lambda kv: (-kv[1], kv[0]))[:w.expansion_terms]
        merged = dict(q)
        for t, v in extra:
            merged[t] = w.expansion_beta * v
        norm = math.sqrt(sum(x * x for x in merged.values()))
        return {t: v / norm for t, v in merged.items()} if norm else q

    def _atom_score(self, query_atoms: set, cid: str) -> float:
        """IDF-weighted (name, kind) overlap.

        Full credit when the kind agrees, `kind_mismatch_discount` when only
        the name does, zero otherwise. Weighted by atom IDF so generic atoms
        cannot fire everywhere — with the base rates at 9-17% precision is the
        hard side, and unweighted atom overlap destroys it.
        """
        if not query_atoms:
            return 0.0
        nk = self._name_kinds.get(cid) or {}
        if not nk:
            return 0.0
        d = self.weights.kind_mismatch_discount
        num = 0.0
        for name, kind in query_atoms:
            kinds = nk.get(name)
            if kinds is None:
                continue
            idf = self.atom_idf.get(name, 0.0)
            num += idf * (1.0 if (not kind or kind in kinds) else d)
        # Scale by the corpus's rarest-atom weight, NOT by the query's own IDF
        # mass: dividing by the query mass would renormalize the IDF straight
        # back out, so a query made of one stopword atom would score 1.0.
        return num / self._atom_norm

    def vocabulary(self, top: int | None = None) -> list:
        """`[(atom name, n_clauses)]`, commonest first.

        Printed in the benchmark report: if the top entries cover most of the
        corpus the vocabulary has collapsed into stopwords and the atom channel
        is worthless, which is visible here at a glance and nowhere else.
        """
        items = sorted(self.atom_df.items(), key=lambda kv: (-kv[1], kv[0]))
        return items[:top] if top else items

    def channel_scores(self, behaviour: Behaviour) -> dict:
        """`{clause_id: {lex, atom, kind, section}}` — the score decomposed.

        Kept separate from `raw_scores` so `explain()` reports exactly the
        numbers that were summed, rather than a re-derivation that could drift
        away from what actually ranked.
        """
        w = self.weights
        q = self._query_vector(behaviour)
        qkinds = behaviour.atom_kinds

        qatoms = {(a["name"], a["kind"]) for a in behaviour.norm_atoms}
        if not qatoms and (w.atom or w.kind):
            warn_atom_channel_disabled(
                f"behaviour {behaviour.slug!r} has no atoms, so the atom "
                f"(weight {w.atom}) and kind (weight {w.kind}) channels "
                f"contribute exactly 0.0")
        if qatoms and not self.atom_df:
            warn_atom_channel_disabled(
                "no clause annotations loaded, so no query atom can ever match")
        # THE THIRD CASE, and the one that still slipped through: atoms exist on
        # BOTH sides but their intersection is empty — a vocabulary mismatch
        # (query atoms coined rather than selected, a stale artifact pairing, a
        # renamed vocabulary). Scores then fall back to lexical-only while every
        # label still says "tool". A silent empty query-atom set is precisely how
        # the dead channel hid the first time; an empty INTERSECTION hides it
        # just as well.
        if qatoms and self.atom_df and not any(
                n in self.atom_df for n, _ in qatoms):
            warn_atom_channel_disabled(
                f"behaviour {behaviour.slug!r} has {len(qatoms)} atoms but NONE "
                "appears in the clause vocabulary — the atom channel "
                "contributes 0.0 and these scores are a lexical baseline")

        channels = {}
        for cid in self.ids:
            lex = _cosine(q, self.vectors[cid]) if q else 0.0
            atom = self._atom_score(qatoms, cid)
            kind = (len(qkinds & self._kinds[cid]) / len(qkinds)
                    if qkinds and self._kinds[cid] else 0.0)
            channels[cid] = {"lex": w.lex * lex, "atom": w.atom * atom,
                             "kind": w.kind * kind, "section": 0.0}

        if w.section > 0:
            local = {cid: sum(c.values()) for cid, c in channels.items()}
            sec = {}
            for path, members in self._members.items():
                vals = sorted((local[c] for c in members), reverse=True)
                k = max(1, min(w.section_top_k, len(vals)))
                sec[path] = sum(vals[:k]) / k
            for cid in self.ids:
                channels[cid]["section"] = w.section * sec[self._section[cid]]
        return channels

    def raw_scores(self, behaviour: Behaviour) -> dict:
        """Unnormalized total score per clause id."""
        return {cid: sum(c.values())
                for cid, c in self.channel_scores(behaviour).items()}

    def explain(self, behaviour: Behaviour, clause_id: str) -> dict:
        """Why this clause scored what it did.

        Auditability is half the point of the tool — a hit that bottoms out in
        a bare number is no more inspectable than a model's say-so. Returns the
        per-channel contributions (which sum to the raw score), the atoms that
        actually matched with the spans licensing them, and the query terms
        carrying the lexical weight.
        """
        cid = str(clause_id)
        channels = self.channel_scores(behaviour)[cid]
        raw = self.raw_scores(behaviour)
        top = max(raw.values(), default=0.0)
        clause = self.by_id.get(cid, {})

        qatoms = {(a["name"], a["kind"]) for a in behaviour.norm_atoms}
        nk = self._name_kinds.get(cid) or {}
        matched = []
        for a in self._atoms.get(cid, []):
            for qname, qkind in qatoms:
                if qname != a["name"]:
                    continue
                matched.append({
                    "name": a["name"],
                    "behaviour_kind": qkind, "clause_kind": a["kind"],
                    "kind_agrees": bool(not qkind or qkind in nk.get(qname, set())),
                    "idf": self.atom_idf.get(a["name"], 0.0),
                    "stopworded": a["name"] in self.atom_stopwords,
                    "span_id": a["span_id"], "quote": a["quote"],
                    "locator": a["locator"], "gloss": a["gloss"],
                })

        q = self._query_vector(behaviour)
        overlap = sorted(
            ((t, q[t] * self.vectors[cid][t]) for t in q
             if t in self.vectors[cid]), key=lambda kv: -kv[1])[:10]

        return {
            "clause_id": cid,
            "locator": clause.get("locator", ""),
            "quote": clause.get("quote", ""),
            "section_path": list(clause.get("section_path") or []),
            "score": (raw[cid] / top) if top > 0 else 0.0,
            "raw": raw[cid],
            "channels": dict(channels),
            "channel_share": {k: (v / raw[cid] if raw[cid] else 0.0)
                              for k, v in channels.items()},
            "matched_atoms": matched,
            "atom_channel_live": bool(qatoms and self.atom_df),
            "top_lexical_terms": overlap,
            "section_peers": len(self._members[self._section[cid]]),
        }

    def rank(self, behaviour: Behaviour) -> list:
        """`[(clause_id, score)]` descending, score in [0, 1].

        Normalized by the corpus maximum so one threshold is comparable across
        behaviours. A corpus with no signal at all scores every clause 0.0 —
        NOT 1.0. That direction matters: the mirror bug (a degenerate run
        reading as a perfect one) is the failure this project already hit once.
        """
        raw = self.raw_scores(behaviour)
        top = max(raw.values(), default=0.0)
        scaled = {c: (v / top if top > 0 else 0.0) for c, v in raw.items()}
        return sorted(scaled.items(), key=lambda kv: (-kv[1], kv[0]))

    def predict(self, behaviour: Behaviour, threshold=None) -> set:
        """The binary decision, comparable to one panel judge's verdict.

        A clause needs a STRICTLY POSITIVE score as well as one at or above the
        threshold, so `threshold=0.0` means "everything with any signal" rather
        than "everything" — an all-zero run predicts the empty set.

        `threshold=None` (the default) derives the cut LABEL-FREE from this
        query's own score distribution via `threshold.PREFERRED` (Otsu). That
        replaces `DEFAULT_THRESHOLD = 0.18`, which was the in-sample argmax of a
        51-point grid **on the panel the tool is scored against** — a live
        violation of contract §5 invariant 9 (nothing may be fitted to the
        panel). Otsu has zero free parameters, so no knob can be turned to pick
        the answer; measured honestly it scores +0.278 against the fitted
        constant's +0.320 and the held-out LOBO's +0.206, and it beats LOBO in
        9 of 9 cells.

        Pass an explicit float to reproduce a historical number or to sweep.
        """
        scored = self.rank(behaviour)
        if threshold is None:
            import threshold as _t
            vals = [s for _, s in scored if s > 0]
            threshold = _t.apply_rule(_t.PREFERRED, vals) if vals else 0.0
        return {c for c, s in scored if s > 0 and s >= threshold}

    def sweep(self, behaviour: Behaviour, thresholds=DEFAULT_SWEEP) -> list:
        """`[(threshold, predicted_set)]` over the whole curve, ascending.

        Sets are nested by construction, so recall is monotone non-increasing
        and precision generally rises: quoting one point without the curve is
        how a threshold gets hand-picked, so the curve is the return value.
        """
        ranked = self.rank(behaviour)
        return [(t, {c for c, s in ranked if s > 0 and s >= t})
                for t in sorted(thresholds)]


# -------------------------------------------------------------------- CLI

USAGE = """\
relevance.py <behaviour-slug> [options]   — rank spec clauses for a behaviour

  --annotations PATH   clause atoms      (default: annotations_b8.json)
  --atoms PATH         behaviour atoms   (default: behavior_atoms_b8.json)
  --top N              rows to show      (default 20)
  --explain CLAUSE_ID  why that clause scored what it did
  --baseline           run WITHOUT the ontology (lexical only), for comparison

Defaults load the real artifacts. Passing neither annotations nor behaviour
atoms used to silently run the degraded lexical baseline while calling itself
the tool; --baseline now makes that an explicit request.
"""


def _resolve(path, default):
    p = path or os.path.join(HERE, default)
    return p if os.path.exists(p) else None


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv or argv[0] in ("-h", "--help"):
        print(USAGE)
        return 0

    slug, opts = argv[0], argv[1:]

    def opt(name, default=None):
        return opts[opts.index(name) + 1] if name in opts else default

    baseline = "--baseline" in opts
    top = int(opt("--top", 20))
    ann_path = None if baseline else _resolve(opt("--annotations"),
                                              "annotations_b8.json")
    atoms_path = None if baseline else _resolve(opt("--atoms"),
                                                "behavior_atoms_b8.json")

    # Read the QUERY-SIDE file only: slug, name, definition. The reference
    # lives in a different file and this module must never open it — the two
    # used to be one file, which put a label leak one line away and made it
    # invisible to every test in the repo (it scored +0.71 against an honest
    # +0.27 while 642 tests passed). See test_no_reference_leak.py.
    queries = json.load(open(os.path.join(HERE, "behaviours_query.json")))
    raw = next((b for b in queries["behaviours"] if b["slug"] == slug), None)
    if raw is None:
        known = ", ".join(b["slug"] for b in queries["behaviours"])
        raise SystemExit(f"unknown behaviour {slug!r}; known: {known}")

    if not baseline and (ann_path is None or atoms_path is None):
        raise SystemExit(
            "missing artifacts — run annotate.py and behavior_atoms.py first, "
            "or pass --baseline to run the lexical-only comparison deliberately")

    idx = RelevanceIndex.from_files(annotations_path=ann_path)
    beh = behaviour_from_panel(raw, load_behaviour_atoms(atoms_path)
                               if atoms_path else None)

    mode = "LEXICAL BASELINE (no ontology)" if baseline else "tool"
    # main() only ranks/explains; it applies no cut, so printing a
    # threshold here was wrong in both directions.
    print(f"# {slug} — {mode} (ranking; no threshold applied)")

    if opt("--explain"):
        cid = opt("--explain")
        info = idx.explain(beh, cid)
        print(json.dumps(info, indent=2, default=str))
        return 0

    for cid, score in idx.rank(beh)[:top]:
        c = idx.by_id[cid]
        print(f"{score:5.3f}  {cid}  {c.get('locator', '')}")
        print(f"         {c.get('quote', '')[:110]}")
    print(f"\nwhy a clause scored what it did:  "
          f"relevance.py {slug} --explain <clause_id>")


if __name__ == "__main__":
    main()
