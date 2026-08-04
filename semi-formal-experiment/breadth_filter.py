"""breadth_filter.py — DOES A LABEL-FREE FILTER ON ATOM BREADTH HELP RETRIEVAL?

⚠️ THIS MODULE IS A PANEL-READING DIAGNOSTIC. NOTHING IT MEASURES MAY SHIP. ⚠️
=============================================================================
It scores retrieval against the judges' pair-gold, so it consults the answer key
(contract §5 invariant 9: the panel is a measuring instrument, never an input).
Its output **may never inform the ontology, the vocabulary, a prompt or a
threshold** — in particular the filtered vocabulary it computes must never be
applied to the shipped annotations or the shipped behaviour atoms.
`weight_diag.py`, `sufficiency_vs_retrieval.py` and `unsupported_ablation.py`
carry the same fence; this module imports none of them, and no module imports
this one (`test_no_reference_leak.FORBIDDEN` names it).

WHY THIS QUESTION AND NOT ANOTHER
---------------------------------
Three measurements converged on the query side:

* Supervised readout over the IDENTICAL atoms scores +0.591; the label-free
  query gets +0.32. The information is already in the atoms; the query cannot
  extract it.
* The capacity bound (534 equivalence classes over 589 passages) caps ANY
  function of the atom set at +0.972 against a +0.555 judge bar.
  Expressiveness is not the constraint.
* `unsupported_ablation.py` measured that deleting the judge-flagged
  `unsupported` atoms buys **-0.0001** against a matched random control — i.e.
  nothing — while deleting the HIGHEST-DOCUMENT-FREQUENCY atoms bought -0.0601
  against a control mean of -0.0363 (SD 0.0099), roughly 2.4 SD out.

Document frequency was the only intervention that beat its control, and DF
needs no labels. So the live question is whether a **label-free,
document-derived filter on atom BREADTH improves retrieval**. A vocabulary
filter is a structural SET OPERATION, not a weighting, so it is invariant-9 and
invariant-10 clean: it deletes names from the shared vocabulary and changes
nothing else.

THE INTERVENTION
----------------
`atom_df` counts, for each atom NAME, how many clauses carry it — document
frequency of the join key. `broad_names` takes every name at or above a cut and
`apply_filter` removes those names from BOTH sides of the join: the clause
annotations and the behaviour-atom query. Nothing is reweighted; the surviving
atoms are byte-identical to the ones they replace.

⚠️ THE CUTOFF IS NOT CHOSEN ON PANEL MCC ⚠️
--------------------------------------------
This is the single most-repeated failure in this project. `act_match` was
picked as the argmax over 7 operators x 3 behaviours, shipped as the default,
and at n=9 it LOST, with a measured selection cost 2.8x its declared bound. The
same mistake has recurred eleven times.

So the cut here comes from a **PRE-DECLARED LABEL-FREE RULE**, fixed in code
before any score was computed:

    CUTOFF_RULE = threshold.PREFERRED   # "otsu"
    applied to the DF DISTRIBUTION ITSELF (one value per vocabulary name)

`threshold.otsu` has ZERO free parameters — there is no q, no k, no c, no
window that could be tuned to the answer — and it predates this project by
fifty years. `cutoff()` takes the annotations and nothing else: no panel, no
scorer, no behaviour. `test_breadth_filter` asserts mechanically that computing
it opens no file and calls neither `universe()` nor `score()`.

A DF SWEEP IS ALSO REPORTED. It is a **CURVE FOR UNDERSTANDING AND EXPLICITLY
NOT A SELECTION**; its argmax is never promoted, and `run()` takes its
operating point from `cutoff()` alone.

THE CONTROL, WHICH IS AGAIN THE POINT
-------------------------------------
Deleting atoms shrinks the prediction set, and 86% of the errors are false
positives, so **deleting ANYTHING lowers the error rate**. Every arm is
therefore compared against size-matched RANDOM deletion over `--draws`
independent seeds, reported as a DISTRIBUTION, and the MDE comes from that
distribution's own spread.

Matching is on ATOM OCCURRENCES, not on vocabulary names. The 43 broad names
the rule selects carry 674 of the corpus's 1629 atom occurrences; 43 RANDOM
names carry about 190. A name-matched control would compare a large deletion
with a small one and call the difference an effect.

The LOWEST-DF arm deletes the same occurrence budget from the opposite end of
the breadth distribution. **If breadth is the mechanism, high-DF and low-DF
must move in opposite directions.** That contrast is the real test; either arm
alone is just "deleting helps".

POWER — n=9 IS THE BINDING CONSTRAINT
-------------------------------------
Nine (behaviour x held-out judge) cells. The project's re-derived noise floor is
0.0316-0.037 MCC (HANDOFF.md:594-598). The MDE below is 2.8 x the SD of the
random control's own null distribution — measured, not assumed — and is printed
BEFORE any effect. An effect smaller than it is NOT RESOLVABLE by this design,
which is a legitimate and important answer.

MCC IS THE PRIMARY OUTCOME
--------------------------
`unsupported_ablation` improved the error rate while MCC got slightly WORSE
(-0.0074), because the deletion traded 76 false positives for 29 false
negatives. Any intervention that only moves the error rate is not an
improvement, so mean per-cell MCC is the headline here and the error rate is
reported beside it.

MEASURED — THE ANSWER IS NO, AND THE SWEEP CLOSES THE ESCAPE HATCH
-----------------------------------------------------------------
Regenerate with `python3 breadth_filter.py`; the table it prints is the
deliverable and no number is hand-transcribed here, so this text cannot drift
from the code. In words:

1. **The filter does not improve retrieval; it harms it.** Under the primary
   compliant module the treatment's MCC change is negative with a bootstrap CI
   entirely below zero, and it sits below the great majority of the
   size-matched random draws.

2. **The sweep removes the "wrong cutoff" objection entirely.** EVERY DF cut on
   the curve loses MCC against baseline, monotonically worse the more is
   deleted, and the curve's own best row is the no-filter end. Even the
   forbidden move — promoting the sweep's argmax — selects "do not filter".
   There is no operating point at which this works, so the null is not an
   artifact of the pre-registered rule.

3. **The breadth contrast fails.** Under both compliant modules the high-DF and
   low-DF arms move in the SAME (negative) direction at a matched occurrence
   budget. Breadth predicts OPPOSITE directions. What the arms actually track
   is how much was deleted, not from which end — which is the mechanical
   deletion effect the control exists to remove.

4. **The prior DF signal was the error-rate artifact again, at scale.** The
   treatment lowers the error rate substantially while MCC falls, because it
   trades a large number of false positives for a large number of false
   negatives. `unsupported_ablation`'s "-0.0601, DF beats the judge's flag" was
   an ERROR-RATE number; carried onto MCC and given a size-matched control, the
   apparent lead disappears. This is the same trade that module already flagged
   in its own treatment arm, seen here seven times larger.

5. **It would be expensive even if it worked.** See the interpretability block:
   the filter empties a substantial number of clauses of ALL atoms — those
   clauses become both unretrievable and unexplainable — and it cuts the citable
   query atoms per GOLD passage by roughly two thirds. The project sells
   auditability; this deletes the audit surface.

6. **Power, stated honestly.** Deleting ~40% of the corpus mass at random is
   itself wildly variable, so the random control's SD is large and the MDE is
   far bigger than the noise floor. The TREATMENT-vs-BASELINE comparison is
   resolved (the CI excludes zero, in the wrong direction); the
   TREATMENT-vs-RANDOM contrast is NOT — this design cannot tell whether the
   extra harm is specifically about breadth or just about deleting more. Both
   readings answer the question that was asked: no improvement, either way.

Consistent with `HANDOFF.md:453-462`, which had already measured that the
supervised weighting is ANTI-correlated with IDF (positively-weighted atoms have
HIGHER DF than negatively-weighted ones) and that 54 label-free re-weighting
variants bought at most +0.016. The broad atoms are carrying signal, not noise.
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.abspath(__file__))
ANNOTATIONS = os.path.join(REPO, "annotations_b8.json")
BEHAVIOUR_ATOMS = os.path.join(REPO, "behavior_atoms_b8.json")
SPEC = "model-spec"
SPEC_KEY = "openai"

#: PRIMARY first. `relevance` is last and flagged because it VIOLATES
#: invariant 10 (HANDOFF.md:573) — it is a comparison, not the answer.
MODULES = ("combined", "structural", "relevance")
PRIMARY_MODULE = "combined"
SECONDARY_MODULES = ("relevance",)

#: ============ THE PRE-DECLARED CUTOFF RULE. DECLARED BEFORE ANY SCORE. =====
#: `threshold.PREFERRED` is Otsu: zero free parameters, per-distribution by
#: construction, fifty years older than this project. Applied to the DF
#: distribution itself — one value per vocabulary name.
#: Changing this constant changes the pre-registration and must be argued for
#: on label-free grounds, never on a panel number.
CUTOFF_RULE = "otsu"

#: What the rule is applied to, named so a reader cannot mistake it for a
#: score distribution.
CUTOFF_INPUT = "document frequency of each vocabulary name"

#: 80% power, two-sided .05, against a MEASURED null SD.
Z = 1.959964 + 0.8416212

#: The project's re-derived noise floor on mean MCC over the 9 cells. Quoted so
#: a verdict cannot be stated at a resolution the instrument does not have.
NOISE_FLOOR = (0.0316, 0.037)

DEFAULT_DRAWS = 40

#: The DF cuts the CURVE is evaluated at. A curve, NOT a selection: its argmax
#: is never promoted to the operating point.
SWEEP_CUTS = (2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 44)


# ------------------------------------------------------------- the artifacts

_ANN = {}
_QA = {}


def annotations(path: str = ANNOTATIONS) -> dict:
    """`{clause_id: [atom, ...]}` — the CLAUSE side, read once."""
    if path not in _ANN:
        with open(path) as fh:
            _ANN[path] = json.load(fh)["by_clause"]
    return _ANN[path]


def query_atoms(path: str = BEHAVIOUR_ATOMS) -> dict:
    """`{slug: {"atoms": [...]}}` — the QUERY side, read once."""
    if path not in _QA:
        with open(path) as fh:
            _QA[path] = json.load(fh)
    return _QA[path]


# ------------------------------------------------------ breadth of an atom

def atom_df(ann: dict) -> dict:
    """`{atom name: number of clauses carrying it}`.

    Document frequency of the NAME, because the name is what the query joins
    on: a name in one clause is a hapax the query can only reach through that
    clause; a name in forty-three is a near-universal match.
    """
    df = defaultdict(int)
    for _cid, ats in ann.items():
        for name in {a.get("name") for a in ats if a.get("name")}:
            df[name] += 1
    return dict(df)


def atom_occurrences(ann: dict) -> dict:
    """`{atom name: number of (clause, atom) rows}` — the deletion MASS.

    Distinct from DF only when a clause carries the same name twice; it is the
    quantity the size-matched control has to match, because it is what "how
    much was deleted" means.
    """
    occ = defaultdict(int)
    for _cid, ats in ann.items():
        for a in ats:
            if a.get("name"):
                occ[a["name"]] += 1
    return dict(occ)


def cutoff(ann: dict, rule: str = CUTOFF_RULE) -> float:
    """The BREADTH cut, from the DF distribution and NOTHING ELSE.

    Pure arithmetic over `ann`. It takes no panel, no gold, no score vector and
    no behaviour, opens no file, and calls neither `universe()` nor `score()` —
    which `test_breadth_filter` asserts with a spy, because "I did not peek" is
    not a testable claim. The mutant this shape rules out is the one this
    project has shipped eleven times: sweep the cut, score each value against
    the panel, keep the best, call it a rule.
    """
    import threshold
    df = atom_df(ann)
    if not df:
        return threshold.DEGENERATE_CUT
    return threshold.RULES[rule](list(df.values()))


def broad_names(ann: dict, cut: float | None = None) -> set:
    """THE TREATMENT VOCABULARY: every name at or above the cut."""
    df = atom_df(ann)
    c = cutoff(ann) if cut is None else cut
    return {n for n, v in df.items() if v >= c}


def occurrence_budget(ann: dict, names) -> int:
    """How many atom occurrences a vocabulary drop removes — the SIZE of the
    deletion, and therefore what every control arm must match."""
    occ = atom_occurrences(ann)
    return sum(occ.get(n, 0) for n in names)


def _accumulate(ann: dict, order, budget: int) -> set:
    """The first names of `order` whose occurrences reach `budget`."""
    occ = atom_occurrences(ann)
    out, total = set(), 0
    for n in order:
        if total >= budget:
            break
        out.add(n)
        total += occ.get(n, 0)
    return out


def df_names(ann: dict, budget: int, highest: bool) -> set:
    """CONTROL ARM: the same occurrence budget taken from the broad end
    (`highest=True`) or the rare end (`highest=False`) of the DF distribution.

    The rare end needs far MORE names to reach the same mass — 111 of the 361
    names are hapaxes — which is the point: the arms are matched on how much
    was deleted, not on how many distinct names were touched.
    """
    df = atom_df(ann)
    order = sorted(df, key=lambda n: ((-df[n]) if highest else df[n], n))
    return _accumulate(ann, order, budget)


def random_names(ann: dict, budget: int, seed: int) -> set:
    """THE PRIMARY CONTROL: the same occurrence budget, chosen uniformly at
    random over the vocabulary, reproducibly per seed.

    Reported as a DISTRIBUTION over seeds, never as a single draw — its spread
    IS the null, and the MDE is derived from it.
    """
    names = sorted(atom_df(ann))
    random.Random(seed).shuffle(names)
    return _accumulate(ann, names, budget)


def df_profile(ann: dict, names) -> dict:
    """What an arm actually deleted, in DF terms — so a reader can check that
    the 'random' arm really is DF-typical and the DF arms really are extreme."""
    df = atom_df(ann)
    vals = sorted(df.get(n, 0) for n in names)
    if not vals:
        return {"n": 0, "mean": 0.0, "median": 0, "max": 0,
                "occ": 0}
    return {"n": len(vals), "mean": sum(vals) / len(vals),
            "median": vals[len(vals) // 2], "max": vals[-1],
            "occ": occurrence_budget(ann, names)}


# ------------------------------------------------------------- the filter

def apply_filter(ann: dict, atoms: dict, drop: set):
    """`(ann', atoms')` with every name in `drop` removed from BOTH sides.

    A SET OPERATION on the shared vocabulary. Nothing is scaled, scored or
    re-ranked, and every surviving atom dict is passed through unchanged — that
    is what keeps this invariant-10 clean. Neither input is mutated.
    """
    drop = set(drop)
    out_ann = {cid: [a for a in ats if a.get("name") not in drop]
               for cid, ats in ann.items()}
    out_atoms = {}
    for slug, val in atoms.items():
        if isinstance(val, dict) and isinstance(val.get("atoms"), list):
            out_atoms[slug] = dict(val)
            out_atoms[slug]["atoms"] = [a for a in val["atoms"]
                                        if a.get("name") not in drop]
        else:
            out_atoms[slug] = val
    return out_ann, out_atoms


def clauses_emptied(ann: dict, drop: set) -> int:
    """Clauses left with NO atoms at all — unreachable by any atom query and
    unexplainable to a human. The interpretability bill, in its bluntest form.
    """
    drop = set(drop)
    return sum(1 for ats in ann.values()
               if ats and all(a.get("name") in drop for a in ats))


# ------------------------------------------------------------- the universe

class Universe:
    """The join and the gold, built once, independent of the annotations — so
    every arm below differs in exactly one moving part."""

    def __init__(self):
        self.passages = []
        self.joins = {}
        self.panel = None
        self.slugs = []
        self.cells = []
        self.gold = {}
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


def score(ann: dict, atoms: dict, module: str, U: Universe) -> dict:
    """Retrieval of one (annotation map, query vocabulary) pair, one module.

    Routed through `benchmark.build_query_module` so the configuration is the
    SHIPPED one — `combined` V1@`any_atom`, `structural` at `any_atom` — and
    cannot drift from what the project reports. Returns per-cell MCCs as well
    as the pooled counts, because the confidence intervals are paired over the
    nine cells and n=9 is the binding constraint on everything here.
    """
    if module not in MODULES:
        raise ValueError(f"unknown module {module!r}; have {list(MODULES)}")
    sys.path.insert(0, REPO)
    import benchmark as B
    qm = B.build_query_module(module, U.panel, U.clauses, annotations=ann,
                              atoms=atoms)
    fp = fn = 0
    cells = []
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
            fp += a
            fn += b
            cells.append(_mcc(tp, a, b, tn))
    trials = len(U.passages) * len(U.cells)
    return {"module": module, "fp": fp, "fn": fn, "err": fp + fn,
            "trials": trials, "rate": (fp + fn) / trials,
            "mcc": sum(cells) / len(cells), "cells": cells}


# ------------------------------------------------------- interpretability

def tp_evidence(ann: dict, atoms: dict, U: Universe) -> float:
    """Mean number of query atoms that a TRUE gold passage's clauses share with
    the behaviour query — the atoms an `explain()` could actually cite.

    This is the audit surface. A filter that improves retrieval by deleting the
    atoms a human would have been shown has not improved the product the
    project is selling.
    """
    tot = n = 0
    for s in U.slugs:
        qn = {a.get("name") for a in (atoms.get(s) or {}).get("atoms", [])}
        gold = set()
        for (slug, _j), g in U.gold.items():
            if slug == s:
                gold |= g
        for loc in gold:
            names = set()
            for cid in U.joins.get(loc, []):
                names |= {a.get("name") for a in ann.get(cid, [])}
            tot += len(names & qn)
            n += 1
    return tot / n if n else 0.0


def query_atom_count(atoms: dict) -> int:
    return sum(len(v.get("atoms", [])) for v in atoms.values()
               if isinstance(v, dict))


# ------------------------------------------------------------- statistics

def boot_ci(vals, n: int = 2000, seed: int = 12345, alpha: float = 0.05):
    """Percentile bootstrap CI of the MEAN, resampling the nine cells.

    With n=9 this interval is wide and it is supposed to be. Reporting a point
    estimate without it is how a null becomes a finding.
    """
    vals = list(vals)
    if not vals:
        return (0.0, 0.0)
    rng = random.Random(seed)
    means = []
    k = len(vals)
    for _ in range(n):
        s = [vals[rng.randrange(k)] for _ in range(k)]
        means.append(sum(s) / k)
    means.sort()
    lo = means[int(alpha / 2 * n)]
    hi = means[min(n - 1, int((1 - alpha / 2) * n))]
    return (lo, hi)


def _sd(vals) -> float:
    if len(vals) < 2:
        return 0.0
    m = sum(vals) / len(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def _arm_delta(base: dict, arm: dict, names, ann) -> dict:
    """Signed change. POSITIVE MCC is an improvement; NEGATIVE error rate is.
    Both directions are printed so nobody has to remember which way it runs."""
    cells = [a - b for a, b in zip(arm["cells"], base["cells"])]
    lo, hi = boot_ci(cells)
    return {"mcc": arm["mcc"] - base["mcc"], "rate": arm["rate"] - base["rate"],
            "fp": arm["fp"] - base["fp"], "fn": arm["fn"] - base["fn"],
            "mcc_ci": (lo, hi), "cells": cells,
            "n_names": len(names), "n_occ": occurrence_budget(ann, names),
            "delta": arm["mcc"] - base["mcc"]}


# --------------------------------------------------------------- the sweep

def sweep_curve(ann: dict, atoms: dict, U: Universe,
                cuts=SWEEP_CUTS, module: str = PRIMARY_MODULE) -> list:
    """A CURVE FOR UNDERSTANDING — EXPLICITLY NOT A SELECTION.

    Retrieval as a function of the DF cut, so a reader can see the shape of the
    relationship rather than one point on it. Its best value is NEVER promoted
    to the operating point: that is the `act_match` failure, and `run()`
    structurally cannot do it because it takes its cut from `cutoff()`.
    """
    base = score(ann, atoms, module, U)
    out = []
    for c in cuts:
        names = broad_names(ann, c)
        a2, q2 = apply_filter(ann, atoms, names)
        s = score(a2, q2, module, U)
        out.append({"cut": c, "n_names": len(names),
                    "n_occ": occurrence_budget(ann, names),
                    "mcc": s["mcc"], "delta": s["mcc"] - base["mcc"],
                    "rate": s["rate"]})
    return out


# ---------------------------------------------------------- the experiment

def run(draws: int = DEFAULT_DRAWS, modules=MODULES, sweep: bool = True) -> dict:
    """Baseline, treatment, the random-control DISTRIBUTION, and the low-DF arm.

    ORDER MATTERS AND IS THE WHOLE DESIGN: the operating point is fixed by the
    label-free rule on the first line, before a single passage is scored, and
    the panel is scored ONCE per arm at the end.
    """
    ann = annotations()
    atoms = query_atoms()

    # ---- LABEL-FREE, PRE-DECLARED, AND FIRST. Nothing below can reach back.
    cut = cutoff(ann)
    treat = broad_names(ann, cut)
    budget = occurrence_budget(ann, treat)
    lo_names = df_names(ann, budget, highest=False)
    ctrl_names = [random_names(ann, budget, seed=s) for s in range(draws)]

    U = universe()
    t_ann, t_q = apply_filter(ann, atoms, treat)
    out = {
        "cutoff": cut, "cutoff_rule": CUTOFF_RULE, "cutoff_input": CUTOFF_INPUT,
        "draws": draws, "budget": budget, "metric": "mcc",
        "vocab": len(atom_df(ann)), "clauses": len(ann),
        "corpus_occurrences": sum(atom_occurrences(ann).values()),
        "df": {"treatment": df_profile(ann, treat),
               "lowest_df": df_profile(ann, lo_names),
               "random": df_profile(ann, ctrl_names[0] if ctrl_names else [])},
        "interpretability": {
            "names_removed": len(treat), "occ_removed": budget,
            "clauses_emptied": clauses_emptied(ann, treat), "clauses": len(ann),
            "mean_atoms_before": sum(len(v) for v in ann.values()) / len(ann),
            "mean_atoms_after": sum(len(v) for v in t_ann.values()) / len(ann),
            "tp_evidence_before": tp_evidence(ann, atoms, U),
            "tp_evidence_after": tp_evidence(t_ann, t_q, U),
            "query_atoms_before": query_atom_count(atoms),
            "query_atoms_after": query_atom_count(t_q)},
        "sweep": sweep_curve(ann, atoms, U) if sweep else [],
        "modules": {}}

    for m in modules:
        base = score(ann, atoms, m, U)
        t = _arm_delta(base, score(t_ann, t_q, m, U), treat, ann)
        l_ann, l_q = apply_filter(ann, atoms, lo_names)
        lo = _arm_delta(base, score(l_ann, l_q, m, U), lo_names, ann)
        # QUERY-SIDE ONLY: the same names struck from the behaviour query but
        # left in the clause annotations. Separates "the query stopped asking
        # for broad atoms" from "the corpus stopped offering them".
        _, q_only = apply_filter(ann, atoms, treat)
        qo = _arm_delta(base, score(ann, q_only, m, U), treat, ann)
        ds = []
        for names in ctrl_names:
            c_ann, c_q = apply_filter(ann, atoms, names)
            ds.append(_arm_delta(base, score(c_ann, c_q, m, U), names, ann))
        vals = sorted(d["mcc"] for d in ds)
        rates = [d["rate"] for d in ds]
        mean = sum(vals) / len(vals) if vals else 0.0
        sd = _sd(vals)
        out["modules"][m] = {
            "baseline": base, "treatment": t, "lowest_df": lo,
            "query_side_only": qo,
            "control": {"n_draws": len(vals), "deltas": vals, "mean": mean,
                        "sd": sd, "lo": vals[0] if vals else 0.0,
                        "hi": vals[-1] if vals else 0.0,
                        "mean_rate": (sum(rates) / len(rates)) if rates else 0.0,
                        "sd_rate": _sd(rates),
                        "pct_below": (sum(1 for v in vals if v < t["mcc"])
                                      / len(vals)) if vals else 0.0},
            "adjusted": t["mcc"] - mean,
            "mde": Z * sd if sd > 0 else float("inf"),
            "n_cells": len(base["cells"]),
        }
    return out


# ---------------------------------------------------------------- reporting

def _arm_line(label, d) -> str:
    return ("  {:<28} MCC {:+.4f} [{:+.4f}, {:+.4f}]   "
            "(err rate {:+.4f}, FP {:+d} / FN {:+d}, "
            "{} names / {} occurrences)").format(
        label, d["mcc"], d["mcc_ci"][0], d["mcc_ci"][1], d["rate"],
        d["fp"], d["fn"], d["n_names"], d["n_occ"])


def report(r: dict) -> list:
    out = [
        "=" * 78,
        "breadth_filter — does a LABEL-FREE filter on atom BREADTH help?",
        "⚠️ DIAGNOSTIC. Reads the panel. Its output may never inform the "
        "ontology,",
        "   the vocabulary, a prompt or a threshold. The filtered vocabulary "
        "below must",
        "   NEVER be applied to the shipped annotations or behaviour atoms.",
        "=" * 78,
        "",
        "PRIMARY OUTCOME: mean per-cell MCC. The error rate is reported beside "
        "it and never",
        "  instead of it — the previous ablation improved the error rate while "
        "MCC got WORSE,",
        "  by trading 76 false positives for 29 false negatives.",
        "",
        "OPERATING POINT — PRE-DECLARED, LABEL-FREE, FIXED BEFORE ANY SCORE",
        f"  rule: {r['cutoff_rule']} (threshold.PREFERRED, zero free "
        f"parameters) over {r.get('cutoff_input', 'DF')}",
        f"  cut:  DF >= {r['cutoff']:.4f}",
    ]
    interp = r.get("interpretability") or {}
    if interp:
        out += [f"  drops {interp['names_removed']} of {r['vocab']} vocabulary "
                f"names, {interp['occ_removed']} of "
                f"{r['corpus_occurrences']} atom occurrences "
                f"({interp['occ_removed'] / max(1, r['corpus_occurrences']):.1%}"
                f" of the corpus mass)"]
    out += [
        "",
        "POWER — READ THIS BEFORE THE EFFECT.",
        f"  n = 9 (behaviour x held-out judge) cells. That is the binding "
        f"constraint on everything here.",
        f"  The project's re-derived noise floor on mean MCC is "
        f"{NOISE_FLOOR[0]}-{NOISE_FLOOR[1]}; state no verdict that fails at "
        f"{NOISE_FLOOR[1]}.",
        f"  The null is the RANDOM control's own spread over {r['draws']} "
        f"occurrence-matched draws;",
        f"  MDE = {Z:.2f} x its SD, measured rather than assumed. An effect "
        f"smaller than the MDE is",
        "  NOT RESOLVABLE by this design — a legitimate and important answer.",
    ]
    for m, d in r["modules"].items():
        out.append(f"    {m:<12} control SD {d['control']['sd']:.4f}   "
                   f"MDE {d['mde']:.4f}")

    if r.get("df"):
        out += ["",
                "WHAT EACH ARM DELETES — corpus document frequency of the atom "
                "NAME.",
                "  {:<14} {:>6} {:>9} {:>9} {:>7} {:>7}".format(
                    "arm", "names", "mean DF", "median DF", "max DF", "occ")]
        for k in ("treatment", "lowest_df", "random"):
            p = r["df"].get(k)
            if not p:
                continue
            out.append("  {:<14} {:>6} {:>9.2f} {:>9} {:>7} {:>7}".format(
                k, p["n"], p["mean"], p.get("median", 0), p.get("max", 0),
                p.get("occ", 0)))

    for m, d in r["modules"].items():
        tag = ("  [SECONDARY — VIOLATES invariant 10]" if m in SECONDARY_MODULES
               else ("  [PRIMARY]" if m == PRIMARY_MODULE else ""))
        b = d["baseline"]
        out += ["", f"MODULE: {m}{tag}",
                f"  baseline  MCC {b['mcc']:+.4f}  err rate {b['rate']:.4f} "
                f"(FP {b['fp']} / FN {b['fn']}), {d['n_cells']} cells",
                "  arms, as CHANGE from baseline (POSITIVE MCC = better):",
                _arm_line("FILTER broad atoms (treatment)", d["treatment"]),
                ("  {:<28} MCC {:+.4f}   ({} draws, SD {:.4f}, range "
                 "{:+.4f}..{:+.4f})").format(
                    "  control: random mean", d["control"]["mean"],
                    d["control"]["n_draws"], d["control"]["sd"],
                    d["control"]["lo"], d["control"]["hi"]),
                _arm_line("  contrast: lowest-DF", d["lowest_df"])]
        if "query_side_only" in d:
            out.append(_arm_line("  variant: query-side only",
                                 d["query_side_only"]))
        out += [f"  TREATMENT vs control (adjusted effect): {d['adjusted']:+.4f}"
                f"   against MDE {d['mde']:.4f}",
                f"  the treatment sits below "
                f"{d['control']['pct_below']:.0%} of the random draws"]
        hi, lo = d["treatment"]["mcc"], d["lowest_df"]["mcc"]
        out.append(f"  BREADTH CONTRAST high-DF {hi:+.4f} vs low-DF {lo:+.4f}: "
                   + ("OPPOSITE directions (consistent with breadth)"
                      if hi * lo < 0 else
                      "SAME direction (NOT consistent with a breadth "
                      "mechanism — both are just deletion)"))
        if abs(d["adjusted"]) < d["mde"]:
            v = ("CANNOT RESOLVE — the treatment is inside the random "
                 "control's own noise")
        elif d["adjusted"] > 0:
            v = "IMPROVES retrieval beyond the size-matched control"
        else:
            v = "WORSENS retrieval relative to the size-matched control"
        out.append(f"  VERDICT ({m}): {v}")

    if interp:
        out += ["",
                "INTERPRETABILITY COST — the project's value proposition is "
                "AUDITABILITY, and the broad",
                "  atoms are often exactly the ones that explain a match to a "
                "human.",
                f"  clauses left with NO atoms at all (emptied, therefore "
                f"unretrievable AND unexplainable): "
                f"{interp['clauses_emptied']} of {interp['clauses']}",
                f"  mean atoms per clause  {interp['mean_atoms_before']:.2f} "
                f"-> {interp['mean_atoms_after']:.2f}",
                f"  behaviour-query atoms  {interp['query_atoms_before']} "
                f"-> {interp['query_atoms_after']}",
                f"  citable query atoms per GOLD passage "
                f"{interp['tp_evidence_before']:.2f} -> "
                f"{interp['tp_evidence_after']:.2f}"]

    out += ["",
            "DF SWEEP — A CURVE FOR UNDERSTANDING. THIS IS **NOT A SELECTION**.",
            "  Its best row is NOT the operating point and must never be "
            "quoted as one: choosing a",
            "  cut on panel MCC is the `act_match` failure this project has "
            "now committed eleven times.",
            f"  The operating point above came from `{r['cutoff_rule']}` on "
            f"the DF distribution alone."]
    if r.get("sweep"):
        out.append("  {:>6} {:>7} {:>7} {:>10} {:>10}".format(
            "DF>=", "names", "occ", "MCC", "delta"))
        for row in r["sweep"]:
            out.append("  {:>6} {:>7} {:>7} {:>10.4f} {:>+10.4f}".format(
                row["cut"], row["n_names"], row["n_occ"], row["mcc"],
                row["delta"]))
    return out


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    fast = "--fast" in argv
    draws = 6 if fast else DEFAULT_DRAWS
    mods = (PRIMARY_MODULE,) if fast else MODULES
    print("\n".join(report(run(draws=draws, modules=mods, sweep=not fast))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
