"""unsupported_ablation.py — RUNG "-1": DELETE THE OVER-ASSERTING ATOMS.

⚠️ THIS MODULE IS A PANEL-READING DIAGNOSTIC. NOTHING IT MEASURES MAY SHIP. ⚠️
=============================================================================
It scores retrieval against the judges' pair-gold, so it consults the answer key
(contract §5 invariant 9: the panel is a measuring instrument, never an input).
Its output **may never inform the ontology, the vocabulary, a prompt or a
threshold** — in particular the drop set it computes must never be applied to
the shipped annotations. `weight_diag.py` and `sufficiency_vs_retrieval.py`
carry the same fence; this module imports neither, and no module imports this
one (`test_no_reference_leak.FORBIDDEN` names it).

THE QUESTION
------------
`sufficiency_vs_retrieval.py` found that what predicts per-clause retrieval
error is content the atoms **add**, not content they drop:

    faithful                  -0.157 [-0.251, -0.062]   (within clause kind)
    >=1 unsupported phrase    +0.157 [+0.062, +0.250]
    86% of retrieval errors are FALSE POSITIVES (312 FP / 49 FN)

The reading offered was mechanistic: an unsupported atom gives the behaviour
query extra surface to match on, so the passage fires when the judges say it
should not. That has never been tested as an **intervention**. This module runs
it: identify the atoms responsible for the judge-flagged `unsupported`
assertions, DELETE them, and re-score retrieval offline.

It is rung "-1" of `LADDER_PLAN.md` because every rung above it makes the
annotations RICHER. This one makes them poorer, in the one direction step 1
says should help.

THE MEASUREMENT
---------------
* Universe: the TRUE 589-passage evaluation universe
  (`benchmark.load_true_panel` + `panel_universe.spec_passages`), 9 (behaviour x
  held-out judge) cells. Never the graded subset.
* Modules: `combined` V1@`any_atom` (PRIMARY — the compliant +0.316 headline)
  and `structural` at its shipped `any_atom`. `relevance.py` is reported as a
  SECONDARY comparison only, because it VIOLATES invariant 10
  (`HANDOFF.md:573`).
* Outcome: total retrieval errors (FP + FN) over (passage x cell), as a rate,
  plus mean per-cell MCC. Reported twice: over the whole universe, and
  restricted to the passages that join to one of the 125 read-back clauses —
  the only passages a deletion can move. The whole-universe number is diluted
  ~5x by construction and must not be read as the effect size.

THE CONTROL, WHICH IS THE POINT
-------------------------------
Deleting atoms shrinks the prediction set, and 86% of the errors are false
positives, so **deleting ANYTHING will lower the error rate**. An arm that only
compares treatment to baseline measures "fewer atoms" and could not have come
out any other way. This project has already lost one "decisive" measurement to
exactly that hole, so the controls are:

  RANDOM (primary)  — the same NUMBER of atoms deleted from the SAME clauses,
                      chosen uniformly at random, over `--draws` independent
                      seeds. Reported as a DISTRIBUTION, and its spread is
                      where the MDE comes from.
  LOWEST-DF         — the same per-clause counts, taking the atoms whose names
  HIGHEST-DF          are rarest / commonest across the corpus. These separate
                      "deleted the unsupported ones" from "deleted the hapaxes"
                      and from "deleted the atoms that match everything".

The reported effect is **treatment delta MINUS the control's mean delta**. The
MDE is 2.8 x the SD of the control's own null distribution — measured, not
assumed.

ATTRIBUTING A PHRASE TO AN ATOM, AND ITS ERROR RATE
---------------------------------------------------
`readback_results.json` gives free-text `unsupported` phrases per clause, not
atom ids. Attribution is a judgement call and is made as follows:

  `best_atom` scores each of the clause's atoms by the fraction of the phrase's
  content tokens (stopped, crudely de-pluralised) that appear in the atom's
  NAME + GLOSS — exactly the two fields `readback.render` prints — and takes
  the argmax, declining below `MIN_ATTRIBUTION_SCORE`. Containment rather than
  Jaccard because a phrase is typically a fragment of a longer gloss.

**Validation.** A frozen random sample of 30 of the 95 phrases
(`attribution_sample`) was read by hand against the clause's full atom list and
the correct atom (or `None`) recorded in `HAND_ATTRIBUTION`. Measured accuracy
is printed by `report_attribution` and is **29/30 = 0.967 [0.833, 0.994]**
(Wilson). The single miss is a phrase asserting the CONJUNCTION of two atoms
("All violent-extremism content is prohibited" over `prohibited_content` +
`violent_extremism`), which no single-atom attribution can represent — the
known and expected failure mode, and it is rare.

Because attribution is reliable, the atom-level arm is the primary analysis.
The clause-level fallback (delete ALL atoms of every clause with >=1 unsupported
phrase) is reported beside it as an upper bound on what attribution error could
be hiding.

Known limits, so nobody quotes this as clean:
  1. One annotator, no second reader; inter-annotator agreement UNMEASURED.
  2. 22 of the 95 unsupported phrases are written from the clause's side
     ("X is not mentioned"). They are still over-assertion reports — the render
     asserted X and the clause does not — but their wording is a reminder that
     the read-back judge is itself unvalidated (`LADDER_PLAN.md` A5).
  3. Deletion is applied to 68 of 587 clauses. Whatever the true per-clause
     effect, the universe-level statistic sees ~1/5 of it.

MEASURED — THE ANSWER IS NO
---------------------------
Regenerate with `python3 unsupported_ablation.py`; the table it prints is the
deliverable and this module adds no hand-transcribed constant. 89 atoms deleted
over 68 clauses (26.8% of the read-back clauses' atoms, 5.5% of the corpus),
40 random control draws, change in the read-back-restricted error rate
(negative = better):

    module      DELETE unsupported   random control (SD)     adjusted    MDE
    combined        -0.0364          -0.0363  (0.0099)       -0.0001   0.0279
    structural      -0.0419          -0.0357  (0.0092)       -0.0061   0.0258
    relevance       -0.0410          -0.0363  (0.0091)       -0.0047   0.0254

**Deleting the judge-flagged unsupported atoms is indistinguishable from
deleting the same number of RANDOM atoms.** Under the primary compliant module
the adjusted effect is -0.0001 against an MDE of 0.0279 — the treatment lands
essentially ON the control mean, below 38% of the individual random draws. The
raw -0.036 improvement is real and is entirely the mechanical "fewer atoms"
effect the control exists to remove: 86% of errors are false positives, so
deleting anything helps. **This is the measurement that would have been called
decisive without a control.**

Two further readings, both against the over-assertion story:

1. **DF beats the judge's flag.** Deleting the same number of HIGHEST-DF atoms
   is ~1.65x better than deleting the flagged ones (-0.0601 vs -0.0364 under
   `combined`), and deleting the LOWEST-DF atoms is ~3x worse (-0.0118). What
   moves retrieval is how BROADLY an atom matches, not whether the clause
   supports it. The flagged atoms are DF-typical (mean DF 9.46 against 10.39
   for a random draw), which is exactly why they behave like a random draw.
   This is the same confound `sufficiency_vs_retrieval` reports as
   rho(atom count, error) = +0.184 [+0.020, +0.350] under `combined`, now seen
   from the intervention side.
2. **MCC gets slightly WORSE** under the treatment (-0.0074 `combined`,
   -0.0011 `structural`). The error-rate gain is bought by trading 76 false
   positives for 29 false negatives; a balanced statistic does not call that an
   improvement.

WHAT THIS DOES AND DOES NOT ESTABLISH
-------------------------------------
It does NOT show over-assertion is harmless. The design deletes 5.5% of corpus
atoms and the MDE is 0.028 on a 0.271 baseline, so a real per-atom effect below
~10% of the deletion's mechanical size is invisible here. What it DOES show is
that the correlational finding "unsupported atoms predict false positives" has
**no surviving causal reading at this resolution once atom count / breadth is
controlled**, and that the specific intervention it implied — find the
over-asserting atoms and remove them — buys nothing a coin flip would not.
"""
from __future__ import annotations

import json
import math
import os
import random
import re
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.abspath(__file__))
READBACK = os.path.join(REPO, "readback_results.json")
ANNOTATIONS = os.path.join(REPO, "annotations_b8.json")
BEHAVIOUR_ATOMS = os.path.join(REPO, "behavior_atoms_b8.json")
SPEC = "model-spec"
SPEC_KEY = "openai"

#: PRIMARY first. `relevance` is last and flagged because it violates
#: invariant 10 — it is a comparison, not the answer.
MODULES = ("combined", "structural", "relevance")
PRIMARY_MODULE = "combined"
SECONDARY_MODULES = ("relevance",)

#: Below this fraction of the phrase's content tokens matched, the phrase is
#: UNATTRIBUTED. Defaulting to atom 0 instead would delete a well-supported atom
#: from every clause the judge wrote something unusual about.
MIN_ATTRIBUTION_SCORE = 0.2

#: 80% power, two-sided .05, against a measured null SD.
_Z = 1.959964 + 0.8416212


# --------------------------------------------------------------- tokenising

_STOP = set(
    "a an the of to and or in on for with by is are be as that this it its not "
    "no any all from at should must may can will their they them what which "
    "who whom when where how than then so if unless while about into more most "
    "other others such over under between within without".split())


def tokens(text: str) -> set:
    """Content tokens: lowercased, stopped, min length 3, crudely singularised.

    Deliberately crude and deliberately hand-written — there is no API call
    permitted here and no stemmer in the `.venv`. Its error rate is measured
    rather than assumed (`validate_attribution`).
    """
    out = set()
    for w in re.findall(r"[a-z0-9]+", (text or "").lower()):
        if len(w) < 3 or w in _STOP:
            continue
        if len(w) > 4 and w.endswith("s"):
            w = w[:-1]
        out.add(w)
    return out


def best_atom(phrase: str, atoms) -> tuple:
    """`(index or None, score)` — which atom of `atoms` this phrase came from.

    CONTAINMENT, not Jaccard: an unsupported phrase is normally a fragment of a
    longer gloss, and Jaccard would penalise the correct atom for being more
    specific than the phrase. Ties break on atom order, which is the render
    order, so the result does not depend on dict iteration.
    """
    pt = tokens(phrase)
    if not pt:
        return None, 0.0
    best_i, best_s = None, 0.0
    for i, a in enumerate(atoms):
        at = tokens((a.get("name") or "").replace("_", " ")) | \
            tokens(a.get("gloss") or "")
        s = len(pt & at) / len(pt)
        if s > best_s:
            best_i, best_s = i, s
    if best_i is None or best_s < MIN_ATTRIBUTION_SCORE:
        return None, best_s
    return best_i, best_s


# ------------------------------------------------------------- the artifacts

_FID = {}
_ANN = {}


def fidelity(path: str = READBACK) -> dict:
    if path not in _FID:
        with open(path) as fh:
            _FID[path] = json.load(fh)["results"]["fidelity"]
    return _FID[path]


def annotations(path: str = ANNOTATIONS) -> dict:
    """`{clause_id: [atom, ...]}` — the SHIPPED annotation map, read once."""
    if path not in _ANN:
        with open(path) as fh:
            _ANN[path] = json.load(fh)["by_clause"]
    return _ANN[path]


def unsupported_phrases(path: str = READBACK) -> list:
    """`[(clause_id, phrase)]` in a FIXED order — clause id, then the order the
    read-back emitted them. `HAND_ATTRIBUTION` indexes into this list, so the
    order is load-bearing and must never become dict-insertion-dependent."""
    fid = fidelity(path)
    return [(cid, p) for cid in sorted(fid) for p in fid[cid]["unsupported"]]


def atom_df() -> dict:
    """`{atom name: number of clauses carrying it}` over the WHOLE corpus.

    Document frequency of the NAME, because that is what the query joins on:
    a name in one clause is a hapax the query can only ever reach through that
    clause, a name in eighty is a near-universal match.
    """
    df = defaultdict(int)
    for _cid, ats in annotations().items():
        for name in {a.get("name") for a in ats}:
            df[name] += 1
    return dict(df)


# ------------------------------------------------------------ attribution

_ATTR = {}


def attribution() -> dict:
    """`{phrase index: atom index or None}` — one decision per phrase."""
    if not _ATTR:
        ann = annotations()
        for i, (cid, p) in enumerate(unsupported_phrases()):
            _ATTR[i] = best_atom(p, ann.get(cid, []))[0]
    return dict(_ATTR)


ATTRIBUTION_SAMPLE_N = 30
ATTRIBUTION_SAMPLE_SEED = 7


def attribution_sample(n: int = ATTRIBUTION_SAMPLE_N,
                       seed: int = ATTRIBUTION_SAMPLE_SEED) -> list:
    """The frozen indices that were read by hand. Regenerable from the seed so
    the sample cannot be quietly extended after the answer is known."""
    return sorted(random.Random(seed).sample(
        range(len(unsupported_phrases())), n))


#: HAND-CHECKED. `{phrase index: correct atom index, or None if no single atom
#: owns the assertion}`. Read against the clause's FULL atom list, not against
#: the automatic answer, and recorded before the ablation was scored.
#:
#: Index 46 ("All violent-extremism content is prohibited") is the deliberate
#: `None`: the assertion is the CONJUNCTION of `prohibited_content` and
#: `violent_extremism` and no single-atom attribution can be right.
HAND_ATTRIBUTION = {
    4: 2, 5: 0, 6: 1, 7: 1, 8: 0, 9: 0, 11: 2, 12: 0, 15: 1, 19: 0,
    27: 2, 28: 1, 30: 3, 41: 3, 46: None, 50: 0, 53: 3, 54: 3, 55: 3, 64: 0,
    68: 0, 70: 2, 72: 2, 74: 0, 80: 0, 83: 0, 84: 0, 85: 0, 90: 2, 92: 1,
}


def wilson(k: int, n: int, z: float = 1.96) -> tuple:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - r) / d, (c + r) / d)


def validate_attribution() -> dict:
    """Accuracy of the automatic attribution against the hand check."""
    att = attribution()
    hits = [i for i, gold in HAND_ATTRIBUTION.items() if att[i] == gold]
    misses = sorted(set(HAND_ATTRIBUTION) - set(hits))
    n = len(HAND_ATTRIBUTION)
    lo, hi = wilson(len(hits), n)
    return {"n": n, "correct": len(hits), "accuracy": len(hits) / n,
            "lo": lo, "hi": hi, "misses": misses}


#: Phrases the read-back wrote from the CLAUSE's side ("X is not mentioned")
#: rather than the render's. Still over-assertion reports; counted because the
#: wording is a standing reminder that the judge is unvalidated.
_NEGATED = re.compile(
    r"\b(not|never|no)\b.*\b(mentioned|stated|specified|required|present|said)\b",
    re.I)


def negated_phrase_count() -> int:
    return sum(1 for _c, p in unsupported_phrases() if _NEGATED.search(p))


# --------------------------------------------------------------- drop sets

def drop_size(drop: dict) -> int:
    return sum(len(v) for v in drop.values())


def drop_unsupported() -> dict:
    """TREATMENT: `{clause_id: {atom index}}` — the attributed atoms."""
    out = {}
    rows = unsupported_phrases()
    att = attribution()
    for i, (cid, _p) in enumerate(rows):
        if att[i] is not None:
            out.setdefault(cid, set()).add(att[i])
    return out


def drop_clause_level(drop: dict = None) -> dict:
    """FALLBACK: every atom of every clause the treatment touches.

    The upper bound on what attribution error could be hiding — if the
    attributed atom is sometimes the wrong one, this arm deletes it anyway.
    """
    ann = annotations()
    src = drop_unsupported() if drop is None else drop
    return {cid: set(range(len(ann[cid]))) for cid in src}


def drop_random(like: dict, seed: int) -> dict:
    """THE CONTROL: same clauses, same per-clause counts, chosen at random.

    Matched per clause rather than pooled, because the treatment's clauses are
    not a random sample of clauses — they are the ones a judge flagged, which
    skews kind, atom count and section. A pooled-random control would confound
    the deletion with that skew.
    """
    ann = annotations()
    rng = random.Random(seed)
    out = {}
    for cid, idxs in sorted(like.items()):
        pool = list(range(len(ann[cid])))
        out[cid] = set(rng.sample(pool, min(len(idxs), len(pool))))
    return out


def drop_by_df(like: dict, highest: bool) -> dict:
    """CONTROL: same per-clause counts, taking the rarest / commonest names."""
    ann = annotations()
    df = atom_df()
    out = {}
    for cid, idxs in sorted(like.items()):
        order = sorted(range(len(ann[cid])),
                       key=lambda i: ((-df.get(ann[cid][i]["name"], 0)) if highest
                                      else df.get(ann[cid][i]["name"], 0),
                                      ann[cid][i].get("name") or ""))
        out[cid] = set(order[:len(idxs)])
    return out


def df_profile(drop: dict) -> dict:
    """Corpus document frequency of the atoms an arm deletes.

    THE DECISIVE COMPARISON is not treatment-vs-baseline; it is what the
    treatment deletes against what the DF arms delete. If deleting the
    highest-DF atoms beats deleting the judge-flagged ones, the mechanism is
    atom BREADTH — the same confound `sufficiency_vs_retrieval` found as
    rho(atom count, error) — and not over-assertion.
    """
    ann = annotations()
    df = atom_df()
    vals = sorted(df.get(ann[cid][i]["name"], 0)
                  for cid, idxs in drop.items() for i in idxs)
    if not vals:
        return {"n": 0, "mean": 0.0, "median": 0.0, "max": 0, "hapax": 0}
    return {"n": len(vals), "mean": sum(vals) / len(vals),
            "median": vals[len(vals) // 2], "max": vals[-1],
            "hapax": sum(1 for v in vals if v == 1)}


def ablate(ann: dict, drop: dict) -> dict:
    """A COPY of `ann` with the named atom indices removed. Never mutates."""
    out = {}
    for cid, ats in ann.items():
        d = drop.get(cid)
        out[cid] = list(ats) if not d else [a for i, a in enumerate(ats)
                                            if i not in d]
    return out


# ------------------------------------------------------------- the universe

class Universe:
    """The join and the gold, built once. Independent of the annotations, which
    is what makes every ablation below a comparison of one moving part."""

    def __init__(self):
        self.passages = []
        self.joins = {}
        self.panel = None
        self.slugs = []
        self.cells = []
        self.gold = {}
        self.readback_locs = set()
        self.clauses = None


_U = {}


def universe() -> Universe:
    """Reads the panel — see the module banner."""
    if "u" in _U:
        return _U["u"]
    sys.path.insert(0, REPO)
    import benchmark as B
    import inventory
    import panel_universe as PU

    U = Universe()
    ps = PU.spec_passages(SPEC)
    clauses, _src = B.load_clauses()
    U.clauses = clauses
    for loc, _sec, text in ps:
        q, _ = PU.citation_quote(text)
        U.joins[loc] = [r["id"] for r in inventory.match_passage(q, clauses)]
    U.passages = sorted(U.joins)

    rb = set(fidelity())
    U.readback_locs = {loc for loc, cids in U.joins.items()
                       if any(c in rb for c in cids)}

    U.panel = B.load_true_panel(spec_keys=(SPEC_KEY,))
    U.slugs = sorted(s for s, b in U.panel.items()
                     if SPEC_KEY in (b.get("coverage") or {}))
    for s in U.slugs:
        for j, t in B.pair_targets(U.panel[s], spec_key=SPEC_KEY).items():
            U.gold[(s, j)] = set(t["gold"])
    U.cells = sorted(U.gold)
    _U["u"] = U
    return U


def _mcc(tp, fp, fn, tn) -> float:
    d = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    return 0.0 if d == 0 else (tp * tn - fp * fn) / math.sqrt(d)


def score(ann: dict, module: str, U: Universe) -> dict:
    """Retrieval error of one annotation map under one query module.

    Routed through `benchmark.build_query_module` so the configuration is the
    shipped one (`combined` V1@`any_atom`, `structural` at `any_atom`) and
    cannot drift from what the project reports.
    """
    if module not in MODULES:
        raise ValueError(f"unknown module {module!r}; have {list(MODULES)}")
    sys.path.insert(0, REPO)
    import benchmark as B
    qm = B.build_query_module(module, U.panel, U.clauses, annotations=ann,
                              atoms=BEHAVIOUR_ATOMS)
    fp = fn = 0
    rfp = rfn = 0
    mccs = []
    for s in U.slugs:
        pred_clauses = qm.predict(s)
        pred = {loc for loc, cids in U.joins.items()
                if any(c in pred_clauses for c in cids)}
        for j in sorted(k[1] for k in U.cells if k[0] == s):
            gold = U.gold[(s, j)]
            tp = tn = a = b = 0
            for loc in U.passages:
                p, y = loc in pred, loc in gold
                if p and y:
                    tp += 1
                elif p:
                    a += 1
                elif y:
                    b += 1
                else:
                    tn += 1
                if loc in U.readback_locs:
                    if p and not y:
                        rfp += 1
                    elif y and not p:
                        rfn += 1
            fp += a
            fn += b
            mccs.append(_mcc(tp, a, b, tn))
    trials = len(U.passages) * len(U.cells)
    rtrials = len(U.readback_locs) * len(U.cells)
    return {"module": module, "fp": fp, "fn": fn, "err": fp + fn,
            "trials": trials, "rate": (fp + fn) / trials,
            "mcc": sum(mccs) / len(mccs),
            "readback_fp": rfp, "readback_fn": rfn, "readback_err": rfp + rfn,
            "readback_trials": rtrials,
            "readback_rate": (rfp + rfn) / rtrials}


# ------------------------------------------------------------- the experiment

DEFAULT_DRAWS = 40


def _delta(base: dict, arm: dict) -> dict:
    """Signed change. NEGATIVE is an improvement on the error rates and
    POSITIVE is an improvement on MCC — both directions are printed so nobody
    has to remember which way the sign runs."""
    return {"rate": arm["rate"] - base["rate"],
            "readback_rate": arm["readback_rate"] - base["readback_rate"],
            "mcc": arm["mcc"] - base["mcc"],
            "fp": arm["fp"] - base["fp"], "fn": arm["fn"] - base["fn"]}


def run(draws: int = DEFAULT_DRAWS, modules=MODULES, metric: str = "readback_rate") -> dict:
    """Baseline, treatment, the random-control DISTRIBUTION, and the DF arms.

    `metric` is the read-back-restricted error rate by default: it is the only
    statistic the deletion can move without ~5x dilution, and the diluted
    whole-universe number is reported beside it rather than instead of it.
    """
    U = universe()
    ann = annotations()
    t_drop = drop_unsupported()
    c_drop = drop_clause_level(t_drop)
    lo_drop = drop_by_df(t_drop, highest=False)
    hi_drop = drop_by_df(t_drop, highest=True)
    out = {"draws": draws, "metric": metric,
           "drop_size": drop_size(t_drop),
           "clauses_touched": len(t_drop),
           "atoms_in_readback_clauses": sum(len(ann[c]) for c in fidelity()
                                            if c in ann),
           "corpus_atoms": sum(len(v) for v in ann.values()),
           "attribution": validate_attribution(),
           "negated_phrases": negated_phrase_count(),
           "df": {"treatment": df_profile(t_drop),
                  "lowest_df": df_profile(lo_drop),
                  "highest_df": df_profile(hi_drop),
                  "random": df_profile(drop_random(t_drop, seed=0))},
           "modules": {}}
    for m in modules:
        base = score(ann, m, U)
        treat = _delta(base, score(ablate(ann, t_drop), m, U))
        clause = _delta(base, score(ablate(ann, c_drop), m, U))
        lo = _delta(base, score(ablate(ann, lo_drop), m, U))
        hi = _delta(base, score(ablate(ann, hi_drop), m, U))
        ds = [_delta(base, score(ablate(ann, drop_random(t_drop, seed=s)), m, U))
              for s in range(draws)]
        vals = sorted(d[metric] for d in ds)
        mean = sum(vals) / len(vals)
        sd = (math.sqrt(sum((v - mean) ** 2 for v in vals) / (len(vals) - 1))
              if len(vals) > 1 else 0.0)
        out["modules"][m] = {
            "baseline": base,
            "treatment": {**treat, "delta": treat[metric]},
            "clause_level": {**clause, "delta": clause[metric]},
            "lowest_df": {**lo, "delta": lo[metric]},
            "highest_df": {**hi, "delta": hi[metric]},
            "control": {"n_draws": len(vals), "deltas": vals, "mean": mean,
                        "sd": sd, "lo": vals[0], "hi": vals[-1],
                        "pct_below": sum(1 for v in vals
                                         if v < treat[metric]) / len(vals)},
            "adjusted": treat[metric] - mean,
            "mde": _Z * sd if sd > 0 else float("inf"),
        }
    return out


# ---------------------------------------------------------------- reporting

def report_attribution() -> list:
    v = validate_attribution()
    rows = unsupported_phrases()
    att = attribution()
    return [
        "ATTRIBUTION — free-text `unsupported` phrase -> a specific atom",
        f"  method: content-token CONTAINMENT of the phrase in the atom's "
        f"NAME + GLOSS (the two fields",
        f"          `readback.render` prints), argmax, declining below "
        f"{MIN_ATTRIBUTION_SCORE}",
        f"  phrases {len(rows)}, attributed "
        f"{sum(1 for i in att if att[i] is not None)}, "
        f"unattributed {sum(1 for i in att if att[i] is None)}",
        f"  hand-checked sample: {v['n']} phrases, frozen seed "
        f"{ATTRIBUTION_SAMPLE_SEED}",
        f"  attribution accuracy {v['accuracy']:.3f} "
        f"[{v['lo']:.3f}, {v['hi']:.3f}]  (misses: {v['misses'] or 'none'})",
        f"  {negated_phrase_count()} of {len(rows)} phrases are written from "
        f"the clause's side (\"X is not mentioned\").",
        "  They are still over-assertion reports, but the read-back judge is "
        "itself unvalidated (LADDER_PLAN A5).",
    ]


def _arm(label, d, metric):
    return (f"  {label:<26} {d[metric]:+.4f}   "
            f"(universe {d['rate']:+.4f}, MCC {d['mcc']:+.4f}, "
            f"FP {d['fp']:+d} / FN {d['fn']:+d})")


def report(r: dict) -> list:
    m0 = r["metric"]
    out = ["=" * 78,
           "unsupported_ablation — LADDER_PLAN.md rung \"-1\"",
           "⚠️ DIAGNOSTIC. Reads the panel. Its output may never inform the "
           "ontology,",
           "   the vocabulary, a prompt or a threshold. In particular the drop "
           "set below",
           "   must NEVER be applied to the shipped annotations.",
           "=" * 78,
           "",
           f"DROP SET: {r['drop_size']} atoms over {r['clauses_touched']} "
           f"clauses "
           f"({r['drop_size'] / max(1, r['atoms_in_readback_clauses']):.1%} of "
           f"the read-back clauses' atoms, "
           f"{r['drop_size'] / max(1, r['corpus_atoms']):.1%} of the corpus). "
           f"Deletion cannot touch the other "
           f"{r['corpus_atoms'] - r['atoms_in_readback_clauses']} atoms, so "
           f"the universe-level statistic is ~5x diluted BY CONSTRUCTION.",
           ""]
    out += report_attribution()
    out += ["",
            "WHAT EACH ARM DELETES — corpus document frequency of the atom "
            "NAME. If the effect tracks DF",
            "  rather than the judge's flag, the mechanism is atom BREADTH, "
            "not over-assertion.",
            "  {:<20} {:>6} {:>9} {:>9} {:>7} {:>7}".format(
                "arm", "n", "mean DF", "median DF", "max DF", "hapax")]
    for k in ("treatment", "random", "lowest_df", "highest_df"):
        p = r["df"][k]
        out.append("  {:<20} {:>6} {:>9.2f} {:>9} {:>7} {:>7}".format(
            k, p["n"], p["mean"], p["median"], p["max"], p["hapax"]))
    out += ["",
            f"POWER — READ BEFORE THE EFFECT. The null is the RANDOM control's "
            f"own spread over {r['draws']} draws;",
            "  the MDE below is 2.8 x its SD, measured rather than assumed. An "
            "effect smaller than this",
            "  is NOT RESOLVABLE by this design, which is a legitimate answer."]
    for m, d in r["modules"].items():
        out.append(f"    {m:<12} control SD {d['control']['sd']:.4f}   "
                   f"MDE {d['mde']:.4f}")
    out.append("")
    for m, d in r["modules"].items():
        tag = "  [SECONDARY — VIOLATES invariant 10]" if m in SECONDARY_MODULES \
            else ("  [PRIMARY]" if m == PRIMARY_MODULE else "")
        out += ["", f"MODULE: {m}{tag}",
                f"  baseline  err rate {d['baseline']['rate']:.4f} "
                f"(FP {d['baseline']['fp']} / FN {d['baseline']['fn']}), "
                f"read-back-restricted {d['baseline']['readback_rate']:.4f}, "
                f"MCC {d['baseline']['mcc']:+.4f}",
                f"  arms, as CHANGE in the read-back-restricted error rate "
                f"(negative = better):",
                _arm("DELETE unsupported", d["treatment"], m0),
                (f"  {'  control: random mean':<26} "
                 f"{d['control']['mean']:+.4f}   "
                 f"({d['control']['n_draws']} draws, SD "
                 f"{d['control']['sd']:.4f}, range "
                 f"{d['control']['lo']:+.4f}..{d['control']['hi']:+.4f})"),
                _arm("  control: lowest-DF", d["lowest_df"], m0),
                _arm("  control: highest-DF", d["highest_df"], m0),
                _arm("  bound: whole clause", d["clause_level"], m0),
                f"  TREATMENT vs control (adjusted effect): "
                f"{d['adjusted']:+.4f}   against MDE {d['mde']:.4f}",
                f"  the treatment sits below {d['control']['pct_below']:.0%} "
                f"of the random draws"]
        if abs(d["adjusted"]) < d["mde"]:
            v = ("CANNOT RESOLVE — the treatment is inside the random "
                 "control's own noise")
        elif d["adjusted"] < 0:
            v = "IMPROVES retrieval beyond the size-matched control"
        else:
            v = "WORSENS retrieval relative to the size-matched control"
        out.append(f"  VERDICT ({m}): {v}")
    return out


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    draws = 6 if "--fast" in argv else DEFAULT_DRAWS
    mods = (PRIMARY_MODULE,) if "--fast" in argv else MODULES
    print("\n".join(report(run(draws=draws, modules=mods))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
