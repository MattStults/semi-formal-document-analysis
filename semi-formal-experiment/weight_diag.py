"""weight_diag.py — WHAT DOES A SUPERVISED READOUT DO THAT OUR QUERY DOES NOT?

⚠️ THIS MODULE IS A DIAGNOSTIC. NOTHING IT FITS MAY EVER SHIP. ⚠️
=================================================================
Contract §5 invariant 10 permits statistical methods **as a ceiling instrument,
never as the product**. Every classifier here exists to answer one question:
*is the +0.20 MCC between our label-free query (+0.278) and a supervised readout
of the identical features (+0.591) reachable by a document-grounded, label-free
derivation?* The fitted coefficients are measurement apparatus. They are not a
scorer, they are not exported, and no consumer imports them. If this module
finds a label-free derivation, **the derivation is the deliverable** — it is
implemented as a re-weighting of the existing query (see `LABEL_FREE_VARIANTS`)
and measured label-free, and only that re-weighting could ever be proposed for
`relevance.py`. The weights themselves are throwaway.

WHY THIS RUN EXISTS
-------------------
Everything else on the relevance line is closed. Measured on the corrected
589-passage universe over 9 (behaviour × pair-gold) cells, mean MCC:

    label-free tool                              +0.278
    tool at an ORACLE threshold                  +0.396   (calibration; 40% recovered)
    SUPERVISED readout of the IDENTICAL features +0.591
    judges (mean / best-per-behaviour)           +0.555 / +0.654
    information bound of the atom index          +0.972

Closed by proof and not revisited here: threshold rules (three behaviours'
score distributions are near-identical while their optimal cuts differ by 0.40);
the section channel (~40% of its supervised signal encodes which sections THOSE
JUDGES treated as relevant); frontier re-annotation (text-only scores BELOW the
atom index); the relation layer.

THE DECISIVE TEST — and the confound that makes it two tests, not one
--------------------------------------------------------------------
"Does the learned weighting TRANSFER?" is under-specified, because our query is
*behaviour-conditioned* (per-behaviour query atoms) while the supervised model
is fitted per (behaviour × judge-pair) cell. Two different transfers are
possible and they mean opposite things:

  A. **Leave-one-behaviour-out (LOBO).** Fit on the other behaviours' cells,
     apply to the held-out behaviour. What survives is a *behaviour-agnostic*
     prior — "which passages are substantive at all". This is the transfer the
     section work measured (+0.334 transferred vs +0.536 in-cell).
     ⚠️ A LOBO failure does NOT prove judge idiosyncrasy: a behaviour-specific
     but perfectly document-grounded signal also fails LOBO, by construction.

  B. **Cross-judge, within behaviour.** Fit on judge *j*'s own positive set;
     evaluate against gold[j] = the OTHER TWO judges' intersection — a label
     source disjoint from the training labels. This isolates exactly the
     judge-idiosyncrasy question at fixed behaviour. If a weighting learned from
     one judge predicts two different judges' consensus about as well as a
     weighting learned from that consensus itself, the signal is judge-generic —
     i.e. a property of the DOCUMENT-plus-behaviour, and a label-free derivation
     may exist. If it collapses, the gap is judge-specific and unreachable.

  (A variant of B — train on gold[j1], test on gold[j2] — is reported for
  completeness but is CONFOUNDED: pair-golds share a judge by construction
  (gold[j1] = j2∩j3, gold[j2] = j1∩j3 share j3), so their overlap inflates
  transfer. Label Jaccard is printed alongside so the reader can discount it.)

The honest verdict needs both: A tests document-genericity across behaviours,
B tests judge-genericity within one. "MIXED, with the split quantified" is the
expected shape of the answer, and the split is what matters.

PRE-REGISTERED EXPECTATIONS (written before any number below was computed)
--------------------------------------------------------------------------
P1. The learned per-atom weights will correlate WEAKLY or NEGATIVELY with our
    IDF weighting. Reason: `HANDOFF.md` already records that the 12–16 atom
    "common core" that carries the structural query's signal is the MORE common
    atoms (median df 9.5/7.0/10.5 vs 7.0/6.0/8.0 for the remainder) and that a
    same-sized *highest-information* subset collapses (+0.042/+0.186/+0.004 vs
    +0.342/+0.368/+0.231). If that is right, rare-is-important is the wrong
    prior on this artifact and IDF is actively costing us.
P2. Sign flips WILL occur among the query atoms: some behaviour atoms will earn
    negative learned weight (they mark passages the judges rejected). Our query
    cannot express a negative weight at all.
P3. LOBO transfer will be POOR (< ~40% of in-cell) for atoms+section, because
    the labels are behaviour-specific and the only behaviour-agnostic content is
    the generic-salience prior the section work already found and already
    matched with the clause operator.
P4. Cross-judge transfer (B) will be MODERATE — better than LOBO, worse than
    in-cell. Inter-judge Jaccard is 0.16–0.62, so a substantial share of each
    cell's fit must be judge-specific.
P5. Attribution of the +0.20: threshold/calibration ≈ +0.12 (already measured
    as tool@label-free → tool@oracle), the section block ≈ +0.05–0.16, and
    per-atom re-weighting the remainder. I expect NO single large recoverable
    term to survive once calibration is removed.
P6. Of the label-free re-weightings, a *flatter-than-IDF* weight (uniform, or
    df-proportional) will beat IDF. Direct consequence of P1.

Every variant tried is reported, losers included. Deltas under ~0.045 are noise
on this panel; paired bootstrap CIs accompany every claim.

MEASURED — THE ANSWER
---------------------
**MIXED, and predominantly a DOCUMENT property. The central question is NOT
closed by judge idiosyncrasy — but the label-free derivation it licenses does
not exist among anything the corpus supplies, and that is the real wall.**

Transfer, atoms+section, 9 cells, fold-wise everywhere (mean MCC, bootstrap CI):

    incell (fit on gold[j])          +0.583  [+0.520, +0.659]   AUC 0.888
    samefamily (one CONTRIBUTING j)  +0.527  [+0.472, +0.597]   AUC 0.882
    crossjudge (one DISJOINT judge)  +0.404  [+0.348, +0.458]   AUC 0.835
    lobo (other behaviours)          +0.241  [+0.196, +0.281]   AUC 0.702
    crossgold (CONFOUNDED)           +0.545  [+0.482, +0.612]   AUC 0.873
    memo_crossjudge (NOT fold-wise)  +0.511  [+0.422, +0.598]   AUC 0.887

Read it as a decomposition of the in-cell +0.583:

    behaviour-agnostic document prior (lobo)                +0.241   41%
    behaviour-specific, judge-generic increment             +0.163   28%
      (crossjudge − lobo)
    single-judge label NOISE, not judge identity            +0.106   18%
      (incell − samefamily-mean; samefamily trains on ONE judge like
       crossjudge does, so this is the cost of a noisier training label)
    judge IDENTITY, upper bound                             +0.073   12%
      (samefamily-mean +0.477 − crossjudge +0.404; samefamily is biased UP by
       containment, gold[j] ⊆ jset[j2], so 12% is a ceiling on the share)

69% of the supervised ceiling survives being learned from a judge who did not
write the gold — it is a function of the document, not of the panel. Atoms-only
gives the same shape and slightly MORE judge-genericity (in-cell +0.472,
crossjudge +0.353 = 75%, lobo +0.221), consistent with the section channel being
the judge-laden half. **P3 held (LOBO poor); P4 was too pessimistic.**

REPLICATED ON 9 BEHAVIOURS (panel v2, 27 cells, `weight_diag.py transfer --v2`)
--------------------------------------------------------------------------------
n=3 behaviours was the binding constraint on exactly this question. The
small-model panel settles it — the same universe, the same features, the same
folds, only the labels change:

    incell     +0.644 [+0.623,+0.665]     crossjudge +0.437 [+0.404,+0.467]
    samefamily +0.559 (alt choice +0.603) lobo       +0.224 [+0.203,+0.247]

**crossjudge / incell = 68%, against 69% on the frontier panel.** The
judge-generic share replicates to within one point across two panels, two judge
tiers and 3 → 9 behaviours, and LOBO stays low in both (35% vs 41%). Every one of
the 9 behaviours is in the +0.29…+0.54 crossjudge band; none is degenerate.
The one number that moves is the judge-identity upper bound: 22% here against
12% on the frontier panel (samefamily-mean +0.581 − crossjudge +0.437, over
in-cell), which is the expected direction — v2's judges are small models and its
export destroyed the score-1 rows, so both idiosyncrasy and label noise are
higher. Take the honest range as **judge identity 12–22%, document-and-behaviour
signal 68–69%.** v2 is NOT a bar and no bar is quoted off it.

THE MEMORISATION CONTROL EARNED ITS KEEP. Fitted on all 589 rows instead of
fold-wise, cross-judge transfer reads +0.511 — and its per-cell values correlate
with the TRAINING JUDGE's own MCC at r = 0.962 (fold-wise: r = 0.813). The naive
number is mostly the model reciting the judge it was trained on. Anyone running
this test without holding out rows would have concluded "transfers beautifully"
from an artifact.

WEIGHT DIVERGENCE — P1 AND P2 BOTH CONFIRMED
--------------------------------------------
Restricted to the atoms the query actually fires on, the learned weighting is
ANTI-correlated with our IDF weighting in 8 of 9 cells (Spearman −0.00 to −0.50;
harm-avoidance −0.41 to −0.50). Over the full vocabulary the correlation is
weakly positive (+0.03 to +0.52) only because never-firing rare atoms all sit
near zero coefficient. Positively-weighted atoms have HIGHER clause-df than
negatively-weighted ones in every cell (5.9–9.7 vs 3.3–4.0) — the "common core"
finding again, and the opposite of rare-is-important. 3–11 of every 19–28 query
atoms earn a NEGATIVE weight; our query cannot express that at all.

**And the weighting is not a function of anything we compute.** Regressing the
learned coefficient on log clause-df, log passage-df, gloss length, clause count
and atom kind gives **R² = 0.039 [0.029, 0.054]**. It encodes atom IDENTITY,
which no corpus statistic supplies.

WHAT THE MECHANISM ACTUALLY IS (atoms only, OOF, oracle cut)
------------------------------------------------------------
    tool atom channel, IDF-weighted             +0.357
    supervised, QUERY atoms only, NON-NEGATIVE  +0.437   (+0.080)
    supervised, QUERY atoms only, signs free    +0.427   (−0.010 vs above)
    supervised, ALL atoms, NON-NEGATIVE         +0.444   (+0.007)
    supervised, ALL atoms, signs free           +0.482   (+0.038, under noise)

So the gain is **better magnitudes on the atoms we already select** — not
negative "anti-atoms" (worth ≤ +0.038, inside noise) and not atoms we failed to
select (+0.007). That is the most shippable-sounding shape the answer could have
taken, and it is exactly the shape R² = 0.039 says is unreachable without labels.

ATTRIBUTION OF THE GAP (tool +0.278 → supervised +0.583, total +0.305)
-----------------------------------------------------------------------
    calibration, label-free cut → oracle cut            +0.118
    dropping lex+section from the tool score            −0.039
    per-atom RE-WEIGHTING of the atom channel           +0.141
      of which reachable label-free                     +0.009
    section block on top of atoms                       +0.118
    the supervised model's OWN calibration cost         −0.034
P5 was right that no single large recoverable term survives.

LABEL-FREE DERIVATIONS TRIED — ALL LOSERS, NONE OUTSIDE NOISE
--------------------------------------------------------------
18 atom re-weightings × 3 normalisations (54 measurements), scored at an oracle
cut so only the RANKING is under test. Best gain over shipped IDF: **+0.016**
(`df-sqrt`, passage-normalised); worst −0.107. The entire spread of the 13
corpus-statistic variants is 0.023 MCC — half the noise floor. Notable:
  * `df-log`, `df-linear`, `mid-df bell` — the shapes P6 predicted would WIN
    because the useful atoms are the common ones: +0.006, +0.001, +0.002. **P6
    is refuted.** The learned weighting is anti-IDF, but not by being pro-df;
    monotone df transforms cannot express it.
  * `beh-weight` — `behavior_atoms_b8.json` already carries a declared 1/2/3
    salience per query atom, produced offline from the behaviour definition and
    IGNORED by `relevance._atom_score`. It was the single best label-free
    candidate for "better magnitudes on the atoms we already picked". Alone
    −0.013, times IDF +0.007, thresholded at ≥3 −0.107. **Dead.**
  * `act-only` −0.013, `flat` −0.013, `gloss-length` +0.009, `bm25-sat` +0.001.
8 behaviour-agnostic passage priors (atom count, is-example, passage length,
section size, section atom-mean, section depth, position, clause count), each
alone and rank-combined with the query: **every one LOSES**, by −0.098 to −0.318.
The LOBO-transferable component is real but is not any of these.

WHAT THIS MEANS FOR THE PROJECT
-------------------------------
A target exists in principle — 69% of the supervised ceiling is judge-generic,
so it is not idiosyncrasy and no proof forbids reaching it. But the quantity to
be approximated is a per-behaviour, per-atom magnitude that R² = 0.039 shows is
not a function of any corpus statistic we hold, and 62 measured label-free
variants (54 re-weightings + 8 priors) recover +0.009 of the +0.141 available.
The remaining honest lead is therefore NOT a scorer change: it is whether the
per-atom salience can be obtained OFFLINE from the behaviour definition at
higher fidelity than `behavior_atoms.py`'s current 1/2/3 field — which is an
annotation-quality question about that field. **That question is now priced**
(`report_declared_vs_learned`): the declared salience is directionally RIGHT in
9 of 9 cells (mean Spearman vs the learned coefficient **+0.17**, range +0.04 to
+0.36) while IDF — the thing we actually ship — is directionally WRONG in 8 of 9
(mean **−0.30**). So the field we ignore beats the field we use, in sign, in
every cell; it is simply far too coarse (3 levels, ρ ≈ 0.17) to move MCC, which
is why substituting it measured −0.013. The lead is therefore: raise the rank
fidelity of that offline salience field, with ρ against the learned weights as
the cheap offline progress metric and a pre-registered MCC gate before anything
is bought. Nothing here licenses shipping a fitted weight.

PROTOCOL (identical to the run that produced the +0.591 figure)
---------------------------------------------------------------
* Universe: `panel_universe.spec_passages("model-spec")` — 589 passages.
* Join: `panel_universe.citation_quote` + `inventory.match_passage`, the same
  quote-containment join every benchmark number uses.
* Features: atom-set indicator over the `annotations_b8.json` vocabulary (+ an
  atom-count column) and a section one-hot. Both are behaviour-agnostic
  properties of the passage, so they are shared across every cell — which is
  what makes the transfer tests possible at all.
* Model: L2 logistic (liblinear). Trees were measured worse and are not used.
* Scoring: repeated stratified 5-fold OOF; the operating threshold comes from an
  inner 4-fold on the TRAINING rows only. Oracle-threshold and AUC are reported
  alongside so discrimination and calibration are never conflated.
* Control: label permutation.

DEPENDENCIES. numpy + sklearn are imported LAZILY inside the functions that
need them, because the repo `.venv` has neither and must still be able to
collect `test_weight_diag.py`. Run the analysis with the SYSTEM python3.
No module here makes a network call.
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.abspath(__file__))
ANNOTATIONS = os.path.join(REPO, "annotations_b8.json")
BEHAVIOUR_ATOMS = os.path.join(REPO, "behavior_atoms_b8.json")
SPEC = "model-spec"
SPEC_KEY = "openai"

#: Deltas below this are noise on a 589-passage / 9-cell panel.
#:
#: ⚠️ SCOPE. `benchmark.py` REFUSES the literal `0.045` by name in any report
#: prose, because it is expired for the panel v2 surface (18 cells, two
#: universe sizes, a different gold base rate). That ban is correct and this
#: constant is not a violation of it: this module runs on `annotations_b8` +
#: `behavior_atoms_b8` over `model-spec` alone — the 3-behaviour, 9-cell panel
#: the constant was actually derived on. `test_weight_diag.py` asserts that,
#: so the constant cannot outlive its scope by someone repointing the module
#: at a wider panel and leaving the floor behind.
#:
#: If you widen this module's panel, DELETE this constant and call
#: `benchmark.noise_floor()`, which re-derives the floor from the data. Do not
#: carry the number across. An expired noise constant is how a false null gets
#: published, and this project has already mis-specified a floor once — an
#: unpaired null applied to paired contrasts, 2.1-6.5x too wide.
NOISE = 0.045
NOISE_SCOPE = {"behaviours": 3, "cells": 9, "passages": 589,
               "spec_keys": ("openai",)}


# --------------------------------------------------------------- statistics
# Pure python on purpose: these are the pieces `test_weight_diag.py` pins, and
# the repo `.venv` (which runs the suite) has no numpy.

def mcc(tp: int, fp: int, fn: int, tn: int) -> float:
    """Matthews correlation coefficient. 0.0 for a degenerate confusion table —
    the same convention `benchmark.mcc` and `sk_base.mcc` use, so numbers here
    are comparable to every other number in the project."""
    den = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    if den <= 0:
        return 0.0
    return (tp * tn - fp * fn) / math.sqrt(den)


def mcc_pred(pred, y) -> float:
    """MCC of two equal-length 0/1 sequences."""
    tp = fp = fn = tn = 0
    for p, t in zip(pred, y):
        if p and t:
            tp += 1
        elif p and not t:
            fp += 1
        elif not p and t:
            fn += 1
        else:
            tn += 1
    return mcc(tp, fp, fn, tn)


def best_threshold(scores, y):
    """`(threshold, mcc)` maximising MCC. ONLY legitimate on training rows or
    when explicitly labelled an ORACLE number — it reads the labels."""
    order = sorted(range(len(y)), key=lambda i: -scores[i])
    P = sum(y)
    N = len(y) - P
    tp = fp = 0
    best, bt = -2.0, 0.5
    for k, i in enumerate(order):
        if y[i]:
            tp += 1
        else:
            fp += 1
        nxt = order[k + 1] if k + 1 < len(order) else None
        if nxt is not None and scores[nxt] == scores[i]:
            continue
        m = mcc(tp, fp, P - tp, N - fp)
        if m > best:
            best = m
            bt = scores[i] if nxt is None else (scores[i] + scores[nxt]) / 2
    return bt, best


def auc(scores, y) -> float:
    """Rank AUC with ties averaged. Threshold-free, so it separates
    DISCRIMINATION from CALIBRATION — the distinction this whole file turns on."""
    P = sum(y)
    N = len(y) - P
    if P == 0 or N == 0:
        return 0.5
    order = sorted(range(len(y)), key=lambda i: scores[i])
    ranks = [0.0] * len(y)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    s = sum(r for r, t in zip(ranks, y) if t)
    return (s - P * (P + 1) / 2.0) / (P * N)


def spearman(a, b) -> float:
    """Rank correlation, ties averaged. Used to compare a learned weight vector
    with IDF — a monotone comparison, because only the ORDER of atom weights
    matters to a ranking query."""
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    return pearson(rank(a), rank(b))


def pearson(a, b) -> float:
    n = len(a)
    if n < 2:
        return 0.0
    ma = sum(a) / n
    mb = sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return num / (da * db) if da and db else 0.0


def jaccard(a, b) -> float:
    a, b = set(a), set(b)
    u = a | b
    return len(a & b) / len(u) if u else 1.0


def paired_bootstrap(pred_a, pred_b, ys, n: int = 2000, seed: int = 20260801):
    """Paired PASSAGE bootstrap of (mean MCC of A) − (mean MCC of B) over cells.

    `pred_a`/`pred_b` are `[per-cell 0/1 sequence]`, `ys` the matching golds.
    Resamples PASSAGES (the shared unit across cells) so the two arms see the
    identical resample — the pairing is the whole point; an unpaired CI on this
    panel is roughly twice as wide and would call every real effect noise.
    """
    rng = random.Random(seed)
    N = len(ys[0])
    out = []
    for _ in range(n):
        idx = [rng.randrange(N) for _ in range(N)]
        da = sum(mcc_pred([p[i] for i in idx], [y[i] for i in idx])
                 for p, y in zip(pred_a, ys)) / len(ys)
        db = sum(mcc_pred([p[i] for i in idx], [y[i] for i in idx])
                 for p, y in zip(pred_b, ys)) / len(ys)
        out.append(da - db)
    out.sort()
    lo = out[int(0.025 * n)]
    hi = out[int(0.975 * n)]
    return sum(out) / n, lo, hi


def ci(vals, n: int = 2000, seed: int = 7):
    """Nonparametric bootstrap mean + 95% CI of a list of per-cell values."""
    rng = random.Random(seed)
    k = len(vals)
    b = sorted(sum(vals[rng.randrange(k)] for _ in range(k)) / k for _ in range(n))
    return sum(vals) / k, b[int(0.025 * n)], b[int(0.975 * n)]


# ---------------------------------------------------------------- the data

class Data:
    """The 589-passage universe with everything both arms need.

    Built once. `atoms[loc]` and `section[loc]` are behaviour-AGNOSTIC — that is
    what makes a cross-behaviour transfer test meaningful at all; if the feature
    matrix carried behaviour information the LOBO arm would be leaking.
    """

    def __init__(self, annotations=ANNOTATIONS, behaviour_atoms=BEHAVIOUR_ATOMS,
                 panel="v1"):
        sys.path.insert(0, REPO)
        import benchmark as B
        import inventory
        import panel_universe as PU

        ps = PU.spec_passages(SPEC)
        self.locs = [l for l, _, _ in ps]
        self.index = {l: i for i, l in enumerate(self.locs)}
        self.section = {l: s for l, s, _ in ps}
        self.text = {l: t for l, _, t in ps}
        self.N = len(self.locs)

        clauses, _ = B.load_clauses()
        self.clauses = clauses
        self.joins = {}
        for loc, _sec, text in ps:
            q, _ = PU.citation_quote(text)
            self.joins[loc] = [r["id"] for r in inventory.match_passage(q, clauses)]

        ann = json.load(open(annotations))
        self.vocab = sorted(ann["vocabulary"])
        self.vi = {n: i for i, n in enumerate(self.vocab)}
        self.clause_names = defaultdict(set)
        self.atom_kind = {}
        self.atom_gloss = {}
        for cid, ats in ann["by_clause"].items():
            for a in ats:
                self.clause_names[cid].add(a["name"])
                self.atom_kind[a["name"]] = a.get("kind")
                g = a.get("gloss") or ""
                if len(g) > len(self.atom_gloss.get(a["name"], "")):
                    self.atom_gloss[a["name"]] = g
        #: passage -> the atom names reachable through its clause join
        self.atoms = {l: set().union(*[self.clause_names.get(c, set())
                                       for c in self.joins[l]] or [set()])
                      for l in self.locs}

        #: CLAUSE document frequency — the df `relevance.RelevanceIndex` uses.
        self.clause_df = Counter(n for cid in [c["id"] for c in clauses]
                                 for n in self.clause_names.get(cid, ()))
        self.n_clauses = len(clauses) or 1
        #: PASSAGE document frequency — the df of the analysis unit.
        self.passage_df = Counter(n for l in self.locs for n in self.atoms[l])
        self.clause_count = Counter()
        for cid, names in self.clause_names.items():
            for n in names:
                self.clause_count[n] += 1

        # `v2` is the 9-behaviour / 2-spec SMALL-MODEL panel. It is NOT a bar —
        # its judges are gpt-mini/haiku/qwen-small — and it is used here for
        # exactly one thing: n=3 behaviours is the binding constraint on the
        # transfer question, and 9 settles it. Its universe is the SAME 589
        # passages (`panel_universe.spec_passages`), so features and folds are
        # unchanged and only the label source differs.
        # ⚠️ Its export dropped summed score 1 as well as 0, and score-1 rows
        # come back as all-zero: a real "tangentially related" verdict is
        # silently recorded as "not related". That makes v2 golds NOISIER than
        # v1's, which biases every v2 arm DOWN. Read v2 as a floor on transfer.
        if panel == "v2":
            import panel_v2
            panel_obj = panel_v2.load_panel(spec_keys=(SPEC_KEY,))
        else:
            panel_obj = B.load_true_panel(spec_keys=(SPEC_KEY,))
        panel = panel_obj
        self.slugs = sorted(s for s, b in panel.items()
                            if SPEC_KEY in (b.get("coverage") or {}))
        self.panel = panel
        self.golds = {}      # (slug, judge) -> [0/1] over locs
        self.jsets = {}      # (slug, judge) -> [0/1] judge's OWN positives
        self.judges = {}
        for s in self.slugs:
            t = B.pair_targets(panel[s], spec_key=SPEC_KEY)
            self.judges[s] = sorted(t)
            for j, d in t.items():
                self.golds[(s, j)] = [1 if l in d["gold"] else 0 for l in self.locs]
                self.jsets[(s, j)] = [1 if l in d["pred"] else 0 for l in self.locs]

        self.behaviour_atoms = json.load(open(behaviour_atoms))

    def atom_weight(self, slug) -> dict:
        """`{atom name: declared salience 1..3}` from `behavior_atoms_b8.json`.

        Produced offline, from the behaviour definition, with no panel label
        anywhere in its provenance — and currently UNUSED by `relevance.py`.
        """
        raw = self.behaviour_atoms.get(slug) or {}
        rows = raw.get("atoms", []) if isinstance(raw, dict) else raw
        return {a["name"]: a.get("weight", 1)
                for a in rows if isinstance(a, dict) and a.get("name")}

    # ------------------------------------------------------------- cells
    def cells(self):
        """`[(slug, judge)]` — the 9 (behaviour × pair-gold) cells."""
        return [(s, j) for s in self.slugs for j in self.judges[s]]

    def query_atoms(self, slug) -> set:
        """The behaviour's query atom NAMES — what our label-free query fires on."""
        raw = self.behaviour_atoms.get(slug) or {}
        rows = raw.get("atoms", raw) if isinstance(raw, dict) else raw
        out = set()
        for a in rows:
            n = a.get("name") if isinstance(a, dict) else a
            if n:
                out.add(n)
        if not out:
            raise ValueError(
                f"no query atoms for {slug!r} — a silently empty query scores "
                f"every passage 0.0 and every variant below would tie at "
                f"chance while still being labelled a result")
        return out

    def judge_mcc(self, slug, judge) -> float:
        y = self.golds[(slug, judge)]
        return mcc_pred(self.jsets[(slug, judge)], y)

    # ---------------------------------------------------------- features
    def matrices(self):
        """`(X_atoms, X_section)` as numpy float32. Lazy numpy import."""
        import numpy as np
        Xa = np.zeros((self.N, len(self.vocab) + 1), dtype=np.float32)
        for l in self.locs:
            i = self.index[l]
            for n in self.atoms[l]:
                Xa[i, self.vi[n]] = 1.0
            Xa[i, -1] = len(self.atoms[l])
        secs = sorted({self.section[l] for l in self.locs})
        si = {s: k for k, s in enumerate(secs)}
        Xs = np.zeros((self.N, len(secs)), dtype=np.float32)
        for l in self.locs:
            Xs[self.index[l], si[self.section[l]]] = 1.0
        self.sections = secs
        return Xa, Xs


_DATA = {}


def data(panel="v1") -> Data:
    if panel not in _DATA:
        _DATA[panel] = Data(panel=panel)
    return _DATA[panel]


# ------------------------------------------------------- supervised arms

def _model(seed=0, kind="logit"):
    """`logit` is the model every headline number in this project used.

    `ridge` / `ridge+` exist only for ONE contrast: same family, same
    regularisation, differing ONLY in whether a coefficient may go negative.
    Our query cannot express a negative weight at all — an atom either fires or
    does not — so that constraint is the exact shape of one candidate mechanism.
    """
    from sklearn.linear_model import LogisticRegression, Ridge
    if kind == "logit":
        return LogisticRegression(C=1.0, max_iter=2000, solver="liblinear")
    if kind == "ridge":
        return Ridge(alpha=1.0)
    if kind == "ridge+":
        return Ridge(alpha=1.0, positive=True, solver="lbfgs")
    raise KeyError(kind)


def oof(X, y, seed=11, folds=5):
    """`(scores, binary)` — out-of-fold probabilities plus a binary prediction
    whose threshold came from an inner 4-fold on the TRAINING rows ONLY.

    This is the protocol that produced the +0.591 figure; it is reproduced here
    rather than re-invented so the transfer arms are measured on the same scale.
    """
    import numpy as np
    from sklearn.model_selection import StratifiedKFold
    y = np.asarray(y)
    skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    sc = np.zeros(len(y))
    bp = np.zeros(len(y), dtype=int)
    for tr, te in skf.split(X, y):
        m = _model(seed)
        m.fit(X[tr], y[tr])
        sc[te] = m.predict_proba(X[te])[:, 1]
        inner = StratifiedKFold(n_splits=4, shuffle=True, random_state=seed + 1)
        isc = np.zeros(len(tr))
        for itr, ite in inner.split(X[tr], y[tr]):
            im = _model(seed)
            im.fit(X[tr][itr], y[tr][itr])
            isc[ite] = im.predict_proba(X[tr][ite])[:, 1]
        t, _ = best_threshold(list(isc), list(y[tr]))
        bp[te] = (sc[te] >= t).astype(int)
    return list(sc), list(bp)


def fit_transfer(X, train_labels, seed=11):
    """Fit on POOLED training cells, return `(score_fn_output, threshold)`.

    `train_labels` is a list of per-cell 0/1 label vectors over the SAME rows
    (the features are behaviour-agnostic, so every cell shares X). Rows are
    concatenated, which weights each training cell equally. The threshold is
    chosen by cross-validation INSIDE the training cells — the held-out cell's
    labels are never touched, not even to calibrate.
    """
    import numpy as np
    from sklearn.model_selection import StratifiedKFold
    Xs = np.vstack([X] * len(train_labels))
    ys = np.concatenate([np.asarray(v) for v in train_labels])
    m = _model(seed)
    m.fit(Xs, ys)
    scores = list(m.predict_proba(X)[:, 1])
    # threshold: inner CV over the pooled training rows
    skf = StratifiedKFold(n_splits=4, shuffle=True, random_state=seed + 1)
    isc = np.zeros(len(ys))
    for itr, ite in skf.split(Xs, ys):
        im = _model(seed)
        im.fit(Xs[itr], ys[itr])
        isc[ite] = im.predict_proba(Xs[ite])[:, 1]
    t, _ = best_threshold(list(isc), list(ys))
    return scores, t, m


# ------------------------------------------ the label-free query, rebuilt
# These are candidate DERIVATIONS, not fitted models. Each is a weight function
# over atom names computable from the corpus alone (no labels anywhere), applied
# as a re-weighting of the existing query: a passage scores the total weight of
# the query atoms it carries. `idf` reproduces what `relevance.py` ships.

def _idf(df, n):
    return math.log(1.0 + n / (1.0 + df))


def LABEL_FREE_VARIANTS():
    """`{name: weight_fn(atom_name, D) -> float}` — every candidate tried.

    Losers stay in this dict. A variant removed after it lost is a variant the
    next reader will propose again.
    """
    def idf(n, D):
        return _idf(D.clause_df.get(n, 0), D.n_clauses)

    def flat(n, D):
        return 1.0

    def df_lin(n, D):
        return float(D.clause_df.get(n, 0))

    def df_log(n, D):
        return math.log(1.0 + D.clause_df.get(n, 0))

    def df_sqrt(n, D):
        return math.sqrt(D.clause_df.get(n, 0))

    def idf_sq(n, D):
        return _idf(D.clause_df.get(n, 0), D.n_clauses) ** 2

    def idf_sqrt(n, D):
        return math.sqrt(_idf(D.clause_df.get(n, 0), D.n_clauses))

    def bm25(n, D, k=1.5):
        d = D.clause_df.get(n, 0)
        i = _idf(d, D.n_clauses)
        return i * (k + 1) / (k + i)

    def passage_idf(n, D):
        return _idf(D.passage_df.get(n, 0), D.N)

    def act_only(n, D):
        return 1.0 if D.atom_kind.get(n) == "act" else 0.0

    def act_boost(n, D):
        return (2.0 if D.atom_kind.get(n) == "act" else 1.0)

    def gloss_len(n, D):
        return math.log(1.0 + len(D.atom_gloss.get(n, "")))

    def mid_df(n, D):
        """Bell over log-df: neither stopwords nor hapaxes. The shape the
        'common core' finding implies if rare-is-bad AND ubiquitous-is-bad."""
        d = math.log(1.0 + D.clause_df.get(n, 0))
        peak = math.log(1.0 + 9.0)      # the measured common-core median df
        return math.exp(-((d - peak) ** 2) / 0.5)

    return {"idf (SHIPPED)": idf, "flat": flat, "df-linear": df_lin,
            "df-log": df_log, "df-sqrt": df_sqrt, "idf^2": idf_sq,
            "sqrt-idf": idf_sqrt, "bm25-sat": bm25, "passage-idf": passage_idf,
            "act-only": act_only, "act-boost": act_boost,
            "gloss-length": gloss_len, "mid-df bell": mid_df}


def BEHAVIOUR_WEIGHT_VARIANTS():
    """Weight functions that may also look at the BEHAVIOUR — still label-free.

    `beh-weight` is the important one: `behavior_atoms_b8.json` already carries a
    declared salience `weight` (1/2/3) for every query atom, produced offline by
    the same behaviour-agnostic-annotation / offline-query design the contract
    requires — AND `relevance._atom_score` ignores it completely, weighting only
    by corpus IDF. If the supervised gain is "better magnitudes on the atoms we
    already picked", this field is the one label-free source of exactly that.
    """
    def declared(n, D, slug):
        return float(D.atom_weight(slug).get(n, 1.0))

    def declared_sq(n, D, slug):
        return float(D.atom_weight(slug).get(n, 1.0)) ** 2

    def declared_x_idf(n, D, slug):
        return (float(D.atom_weight(slug).get(n, 1.0))
                * _idf(D.clause_df.get(n, 0), D.n_clauses))

    def declared_only_top(n, D, slug):
        return 1.0 if D.atom_weight(slug).get(n, 0) >= 3 else 0.0

    def declared_top2(n, D, slug):
        return 1.0 if D.atom_weight(slug).get(n, 0) >= 2 else 0.0

    return {"beh-weight": declared, "beh-weight^2": declared_sq,
            "beh-weight x idf": declared_x_idf,
            "beh-weight>=3 only": declared_only_top,
            "beh-weight>=2 only": declared_top2}


def query_scores(D, slug, wfn, normalise="none"):
    """Passage scores from the LABEL-FREE query under weight function `wfn`.

    `normalise`:
      * `none`      — total weight of matched query atoms (what the tool does,
                      up to a constant scale)
      * `query`     — divided by the query's total weight (coverage fraction)
      * `passage`   — divided by the passage's own atom count (length control)
    """
    q = D.query_atoms(slug)
    try:
        w = {n: wfn(n, D) for n in q}
    except TypeError:
        w = {n: wfn(n, D, slug) for n in q}
    tot = sum(w.values()) or 1.0
    out = []
    for l in D.locs:
        hit = D.atoms[l] & q
        s = sum(w[n] for n in hit)
        if normalise == "query":
            s /= tot
        elif normalise == "passage":
            s /= max(1, len(D.atoms[l]))
        out.append(s)
    return out


# ------------------------------------------------------------- reporting

def _fmt(x):
    return f"{x:+.3f}"


def report_tool(D):
    """The SHIPPED tool on the same 9 cells — the anchor the whole ladder hangs
    from. Passage score = max over the clauses it joins to, exactly as
    `benchmark.passage_scores` does it, so this is the tool as consumers run it
    and not a re-implementation that could drift.

    Returns `{(slug, judge): {label_free, oracle, auc, atom_oracle, atom_auc}}`.
    """
    sys.path.insert(0, REPO)
    import relevance as R
    idx = R.RelevanceIndex.from_files(annotations_path=ANNOTATIONS)
    beh = R.behaviours_from_panel(D.panel, atoms_source=BEHAVIOUR_ATOMS)
    out = {}
    for s in D.slugs:
        ranked = dict(idx.rank(beh[s]))
        ch = idx.channel_scores(beh[s])
        full = [max([ranked.get(c, 0.0) for c in D.joins[l]], default=0.0)
                for l in D.locs]
        atom = [max([ch[c]["atom"] for c in D.joins[l] if c in ch], default=0.0)
                for l in D.locs]
        pred = idx.predict(beh[s])          # label-free cut, as shipped
        lf = [1 if any(c in pred for c in D.joins[l]) else 0 for l in D.locs]
        for j in D.judges[s]:
            y = D.golds[(s, j)]
            out[(s, j)] = {
                "label_free": mcc_pred(lf, y),
                "oracle": best_threshold(full, y)[1],
                "auc": auc(full, y),
                "atom_oracle": best_threshold(atom, y)[1],
                "atom_auc": auc(atom, y),
                "pred_label_free": lf,
            }
    return out


def report_incell(D, seeds=(11, 23, 37)):
    """Reproduce the supervised ceiling per cell: atoms, section, atoms+section."""
    import numpy as np
    Xa, Xs = D.matrices()
    sets = {"atoms": Xa, "section": Xs, "atoms+section": np.hstack([Xa, Xs])}
    out = {}
    for name, X in sets.items():
        rows = {}
        for s, j in D.cells():
            y = D.golds[(s, j)]
            vals, aucs, orac = [], [], []
            for sd in seeds:
                sc, bp = oof(X, y, sd)
                vals.append(mcc_pred(bp, y))
                aucs.append(auc(sc, y))
                orac.append(best_threshold(sc, y)[1])
            rows[(s, j)] = (float(np.mean(vals)), float(np.mean(aucs)),
                            float(np.mean(orac)))
        out[name] = rows
    return out


def oof_transfer(X, train_labels, seed=11, folds=5):
    """Transfer WITHOUT row memorisation: `(scores, threshold)`.

    ⚠️ THE CONFOUND THIS EXISTS TO KILL. A model fitted on all 589 rows under a
    DIFFERENT label vector can still memorise row identity — the atom + section
    one-hots very nearly identify a passage. Evaluated against a label that
    correlates with the training label (judge j's own calls correlate with the
    other two judges' consensus by construction), memorisation alone reproduces
    much of the target: a perfect memoriser of `jset[j]` scores exactly the
    JUDGE's MCC (+0.555 mean), which would be read as "the weighting transfers"
    when nothing had been learned about the document at all.

    So every transfer arm is fold-wise: rows are split 5 ways, each fold's
    prediction comes from a model fitted only on the OTHER folds' rows (under
    the transfer labels), and the threshold comes from an inner CV on those
    training rows under the training labels. The ONLY difference from
    `oof()` is then the label source — which is the contrast we want to measure.
    """
    import numpy as np
    from sklearn.model_selection import StratifiedKFold
    L = [np.asarray(v) for v in train_labels]
    strat = L[0]
    skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    sc = np.zeros(X.shape[0])
    bp = np.zeros(X.shape[0], dtype=int)
    for tr, te in skf.split(X, strat):
        Xs = np.vstack([X[tr]] * len(L))
        ys = np.concatenate([v[tr] for v in L])
        m = _model(seed)
        m.fit(Xs, ys)
        sc[te] = m.predict_proba(X[te])[:, 1]
        inner = StratifiedKFold(n_splits=4, shuffle=True, random_state=seed + 1)
        isc = np.zeros(len(ys))
        for itr, ite in inner.split(Xs, ys):
            im = _model(seed)
            im.fit(Xs[itr], ys[itr])
            isc[ite] = im.predict_proba(Xs[ite])[:, 1]
        t, _ = best_threshold(list(isc), list(ys))
        bp[te] = (sc[te] >= t).astype(int)
    return list(sc), list(bp)


def report_transfer(D, seeds=(11, 23, 37), features="atoms+section"):
    """The decisive tests. Returns `{arm: {(slug, judge): (mcc, auc, oracle)}}`.

    Arms (all fold-wise — see `oof_transfer` for why):
      `incell`      fit on gold[j] itself: the ceiling, for reference
      `lobo`        fit on the other behaviours' 6 cells, apply here (A)
      `crossjudge`  fit on judge j's OWN positives, evaluate on gold[j] (B)
      `crossgold`   fit on the sibling cells' golds (CONFOUNDED — shares a judge)
      `memo_crossjudge`  the SAME as crossjudge but fitted on all rows at once,
                    kept to show how much of a naive transfer number is row
                    memorisation rather than a learned document function
    """
    import numpy as np
    Xa, Xs = D.matrices()
    X = {"atoms": Xa, "section": Xs,
         "atoms+section": np.hstack([Xa, Xs])}[features]
    arms = {k: {} for k in ("incell", "samefamily", "crossjudge", "lobo",
                            "crossgold", "memo_crossjudge")}
    preds = {k: {} for k in arms}
    for s, j in D.cells():
        y = D.golds[(s, j)]

        def record(arm, sc, bp):
            arms[arm][(s, j)] = (mcc_pred(bp, y), auc(sc, y),
                                 best_threshold(sc, y)[1])
            preds[arm][(s, j)] = bp

        sc, bp = oof(X, y, seeds[0])
        record("incell", sc, bp)
        # A ---------------------------------------------------------- LOBO
        sc, bp = oof_transfer(X, [D.golds[c] for c in D.cells() if c[0] != s],
                              seeds[0])
        record("lobo", sc, bp)
        # B ---------------------------------------------------- cross-judge
        # judge j is NOT in gold[j] (gold[j] = the other two's intersection),
        # so this label source is disjoint from the evaluation label.
        sc, bp = oof_transfer(X, [D.jsets[(s, j)]], seeds[0])
        record("crossjudge", sc, bp)
        # B's CONTROL — the same thing with a judge that IS in the pair.
        # `crossjudge` trains on ONE judge while `incell` trains on a two-judge
        # intersection, so part of the crossjudge deficit could be nothing but
        # a noisier training label. `samefamily` holds training-label quality
        # fixed (also one judge) and varies only WHICH judge, isolating judge
        # identity. It is biased UP by containment (gold[j] ⊆ jset[j2] for a
        # contributing j2), so treat it as an upper reference, not a ceiling.
        # Uses the FIRST contributing judge in sorted order — an arbitrary but
        # fixed choice, so the point estimate and its paired bootstrap describe
        # the same predictor. `samefamily_spread` records what the other choice
        # would have given, so the arbitrariness is visible rather than hidden.
        fam = sorted(j2 for j2 in D.judges[s] if j2 != j)
        sc, bp = oof_transfer(X, [D.jsets[(s, fam[0])]], seeds[0])
        record("samefamily", sc, bp)
        alt = [mcc_pred(oof_transfer(X, [D.jsets[(s, j2)]], seeds[0])[1], y)
               for j2 in fam[1:]]
        arms.setdefault("samefamily_spread", {})[(s, j)] = (
            max(alt, default=0.0), 0.0, 0.0)
        # confounded sibling-gold arm
        sc, bp = oof_transfer(X, [D.golds[(s, j2)] for j2 in D.judges[s]
                                  if j2 != j], seeds[0])
        record("crossgold", sc, bp)
        # the memorisation control
        sc, t, _ = fit_transfer(X, [D.jsets[(s, j)]], seeds[0])
        record("memo_crossjudge", sc, [1 if v >= t else 0 for v in sc])
    return arms, preds


def report_weights(D, seed=11):
    """Learned per-atom weights vs our IDF weighting, per cell.

    Fitted on ALL rows — these coefficients are never used to predict anything,
    only to be looked at, so out-of-fold discipline does not apply. Predictions
    everywhere else in this module are strictly OOF.
    """
    import numpy as np
    Xa, _ = D.matrices()
    out = {}
    for s, j in D.cells():
        y = np.asarray(D.golds[(s, j)])
        m = _model(seed)
        m.fit(Xa, y)
        coef = m.coef_[0][:len(D.vocab)]
        idfs = [_idf(D.clause_df.get(n, 0), D.n_clauses) for n in D.vocab]
        dfs = [D.clause_df.get(n, 0) for n in D.vocab]
        # restrict to atoms the corpus actually carries
        keep = [k for k, n in enumerate(D.vocab) if D.passage_df.get(n, 0) > 0]
        q = D.query_atoms(s)
        qk = [k for k in keep if D.vocab[k] in q]
        out[(s, j)] = {
            "coef": {D.vocab[k]: float(coef[k]) for k in keep},
            "rho_idf": spearman([float(coef[k]) for k in keep],
                                [idfs[k] for k in keep]),
            "rho_df": spearman([float(coef[k]) for k in keep],
                               [float(dfs[k]) for k in keep]),
            "rho_idf_query": spearman([float(coef[k]) for k in qk],
                                      [idfs[k] for k in qk]) if len(qk) > 2 else 0.0,
            "n_query": len(qk),
            "n_query_negative": sum(1 for k in qk if coef[k] < 0),
            "mean_df_positive": (sum(dfs[k] for k in keep if coef[k] > 0) /
                                 max(1, sum(1 for k in keep if coef[k] > 0))),
            "mean_df_negative": (sum(dfs[k] for k in keep if coef[k] < 0) /
                                 max(1, sum(1 for k in keep if coef[k] < 0))),
        }
    return out


def learned_weight_model(D, seed=11):
    """Is the learned per-atom weighting a MONOTONE FUNCTION OF ANYTHING WE
    ALREADY COMPUTE?

    Regresses the learned coefficient on the label-free covariates the tool has
    on hand — log clause-df, log passage-df, atom kind (one-hot), gloss length,
    and the number of clauses the atom appears on — and reports R². A high R²
    would mean the supervised weighting is reachable by a formula; a low one
    means the weights encode atom IDENTITY, which no corpus statistic supplies.
    """
    import numpy as np
    Xa, _ = D.matrices()
    kinds = sorted({k for k in D.atom_kind.values() if k})
    rows = {}
    for s, j in D.cells():
        y = np.asarray(D.golds[(s, j)])
        m = _model(seed)
        m.fit(Xa, y)
        coef = m.coef_[0][:len(D.vocab)]
        keep = [k for k, n in enumerate(D.vocab) if D.passage_df.get(n, 0) > 0]
        F, t = [], []
        for k in keep:
            n = D.vocab[k]
            f = [1.0,
                 math.log(1.0 + D.clause_df.get(n, 0)),
                 math.log(1.0 + D.passage_df.get(n, 0)),
                 math.log(1.0 + len(D.atom_gloss.get(n, ""))),
                 float(D.clause_count.get(n, 0))]
            f += [1.0 if D.atom_kind.get(n) == kk else 0.0 for kk in kinds]
            F.append(f)
            t.append(float(coef[k]))
        F = np.asarray(F)
        t = np.asarray(t)
        beta, *_ = np.linalg.lstsq(F, t, rcond=None)
        resid = t - F @ beta
        ss = float(((t - t.mean()) ** 2).sum())
        rows[(s, j)] = 1.0 - float((resid ** 2).sum()) / ss if ss else 0.0
    return rows


def oof_regress(X, y, kind, seed=11, folds=5):
    """OOF continuous scores from a regression model. Scored at an ORACLE
    threshold downstream, because the only thing under test here is the RANKING
    a weight vector induces — calibration is a separately closed problem."""
    import numpy as np
    from sklearn.model_selection import StratifiedKFold
    y = np.asarray(y, dtype=float)
    skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    sc = np.zeros(len(y))
    for tr, te in skf.split(X, y):
        m = _model(seed, kind)
        m.fit(X[tr], y[tr])
        sc[te] = m.predict(X[te])
    return list(sc)


def report_mechanism(D, seed=11):
    """WHAT, MECHANICALLY, DOES THE SUPERVISED READOUT HAVE THAT WE DO NOT?

    Two candidate mechanisms, each measured by removing exactly it:

      * NEGATIVE WEIGHTS. Our query is a union of positive evidence; an atom
        fires or it does not. A fitted model may give an atom a negative weight,
        i.e. "this atom marks passages the judges REJECT". `ridge+` forbids that
        and is otherwise identical to `ridge`.
      * ATOMS OUTSIDE THE QUERY. `behavior_atoms.py` picks 19–28 atoms per
        behaviour. The supervised model sees all 361. Restricting the feature
        matrix to the query's own atoms measures how much of the gain needs
        atoms we never selected.

    All arms: atoms only, OOF, ORACLE threshold — so the comparison is against
    the tool's atom channel at ITS oracle (rung 3 of the attribution ladder),
    and no arm is being rewarded for calibration.
    """
    import numpy as np
    Xa, _ = D.matrices()
    cols = {}
    for s in D.slugs:
        q = D.query_atoms(s)
        cols[s] = [D.vi[n] for n in sorted(q) if n in D.vi]
    out = {}
    for s, j in D.cells():
        y = D.golds[(s, j)]
        Xq = Xa[:, cols[s]]
        row = {}
        for name, X, kind in (("all/free", Xa, "ridge"),
                              ("all/nonneg", Xa, "ridge+"),
                              ("query/free", Xq, "ridge"),
                              ("query/nonneg", Xq, "ridge+")):
            sc = oof_regress(X, y, kind, seed)
            row[name] = (best_threshold(sc, y)[1], auc(sc, y))
        out[(s, j)] = row
    return out


def report_declared_vs_learned(D, seed=11):
    """Does the DECLARED salience in `behavior_atoms_b8.json` point the same way
    as the learned weighting — and does IDF?

    This is the only place the remaining lead can be priced. If the declared
    weight is directionally right but too coarse, the lead is an
    annotation-QUALITY question with a measurable target (raise this rank
    fidelity) rather than a scorer change. If it were directionally wrong, the
    lead would be dead.
    """
    import numpy as np
    Xa, _ = D.matrices()
    out = {}
    for s, j in D.cells():
        y = np.asarray(D.golds[(s, j)])
        m = _model(seed)
        m.fit(Xa, y)
        coef = m.coef_[0][:len(D.vocab)]
        aw = D.atom_weight(s)
        ks = [D.vi[n] for n in sorted(D.query_atoms(s)) if n in D.vi]
        learned = [float(coef[k]) for k in ks]
        out[(s, j)] = {
            "rho_declared": spearman([float(aw.get(D.vocab[k], 1)) for k in ks],
                                     learned),
            "rho_idf": spearman(
                [_idf(D.clause_df.get(D.vocab[k], 0), D.n_clauses) for k in ks],
                learned),
            "n": len(ks),
        }
    return out


def _z(vals):
    m = sum(vals) / len(vals)
    sd = math.sqrt(sum((v - m) ** 2 for v in vals) / max(1, len(vals) - 1)) or 1.0
    return [(v - m) / sd for v in vals]


def _ranknorm(vals):
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    r = [0.0] * len(vals)
    for k, i in enumerate(order):
        r[i] = k / max(1, len(vals) - 1)
    return r


def label_free_priors(D):
    """Behaviour-AGNOSTIC, corpus-computable passage priors.

    These are candidates for the component that LOBO shows transfers across
    behaviours — the "which passages are substantive at all" prior. Each is a
    pure function of the document plus its own annotations; none touches a label.
    """
    n_sec = Counter(D.section[l] for l in D.locs)
    sec_atoms = defaultdict(list)
    for l in D.locs:
        sec_atoms[D.section[l]].append(len(D.atoms[l]))
    sec_mean = {s: sum(v) / len(v) for s, v in sec_atoms.items()}
    depth = {l: D.section[l].count(">") for l in D.locs}
    return {
        "atom-count": [float(len(D.atoms[l])) for l in D.locs],
        "is-example": [0.0 if "~~~" in D.text[l] else 1.0 for l in D.locs],
        "passage-length": [float(len(D.text[l])) for l in D.locs],
        "section-size": [float(n_sec[D.section[l]]) for l in D.locs],
        "section-atom-mean": [sec_mean[D.section[l]] for l in D.locs],
        "section-depth": [float(depth[l]) for l in D.locs],
        "position": [i / D.N for i in range(D.N)],
        "n-clauses": [float(len(D.joins[l])) for l in D.locs],
    }


def report_priors(D, wfn=None):
    """Each label-free prior alone, and rank-combined with the query.

    The combination is a plain mean of normalised RANKS — parameter-free on
    purpose. Any mixing weight would be a knob, and a knob chosen by looking at
    this table is a panel fit (invariant 9), not a derivation.
    """
    variants = LABEL_FREE_VARIANTS()
    wfn = wfn or variants["idf (SHIPPED)"]
    priors = label_free_priors(D)
    out = {}
    for s in D.slugs:
        q = _ranknorm(query_scores(D, s, wfn))
        for name, p in priors.items():
            pr = _ranknorm(p)
            for mode, sc in (("alone", pr),
                             ("query+prior", [(a + b) / 2 for a, b in zip(q, pr)])):
                for j in D.judges[s]:
                    y = D.golds[(s, j)]
                    out.setdefault((name, mode), {})[(s, j)] = (
                        best_threshold(sc, y)[1], auc(sc, y))
        for j in D.judges[s]:
            y = D.golds[(s, j)]
            out.setdefault(("QUERY alone", "-"), {})[(s, j)] = (
                best_threshold(q, y)[1], auc(q, y))
    return out


def report_label_free(D, normalise="none"):
    """Every label-free re-weighting, per cell, at an ORACLE threshold and AUC.

    The oracle threshold is used ON PURPOSE: it removes calibration, which is a
    separately-measured and separately-closed problem, so the table isolates the
    only thing a re-weighting can change — the RANKING.
    """
    res = {}
    for name, fn in (LABEL_FREE_VARIANTS() | BEHAVIOUR_WEIGHT_VARIANTS()).items():
        rows = {}
        for s, j in D.cells():
            y = D.golds[(s, j)]
            sc = query_scores(D, s, fn, normalise)
            rows[(s, j)] = (best_threshold(sc, y)[1], auc(sc, y))
        res[name] = rows
    return res


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    what = argv[0] if argv else "all"
    which = "v2" if "--v2" in argv else "v1"
    argv = [a for a in argv if a != "--v2"]
    D = data(which)
    if which == "v2":
        print("[panel] v2 — 9 behaviours, SMALL-MODEL judges "
              "(gpt-mini/haiku/qwen-small). NOT a bar; used for power only. "
              "Score-1 rows are irrecoverable, so these arms are a FLOOR.")
    print(f"[data] {D.N} passages, {len(D.cells())} cells, "
          f"{len(D.vocab)} atoms, slugs={D.slugs}")
    if what in ("all", "incell"):
        print("\n=== IN-CELL SUPERVISED CEILING (5-fold OOF, train-only threshold)")
        r = report_incell(D)
        for name, rows in r.items():
            v = [x[0] for x in rows.values()]
            print(f"  {name:<16}{_fmt(sum(v) / len(v))}  "
                  f"AUC {sum(x[1] for x in rows.values()) / len(rows):.3f}  "
                  f"oracle {_fmt(sum(x[2] for x in rows.values()) / len(rows))}")
            for (s, j), x in rows.items():
                print(f"      {s[:26]:<28}{j:<9}{_fmt(x[0])}  AUC {x[1]:.3f}  "
                      f"oracle {_fmt(x[2])}  judge {_fmt(D.judge_mcc(s, j))}")
    if what in ("all", "transfer"):
        feats = argv[1] if len(argv) > 1 else "atoms+section"
        print(f"\n=== TRANSFER — THE DECISIVE TEST  [features: {feats}]")
        arms, preds = report_transfer(D, features=feats)
        cells = D.cells()
        ys = [D.golds[c] for c in cells]
        print(f"  {'arm':<18}{'meanMCC':>9}{'95% CI':>20}{'AUC':>7}"
              f"{'oracle':>9}{'vs in-cell (paired)':>26}")
        for name, rows in arms.items():
            v = [rows[c][0] for c in cells]
            m, lo, hi = ci(v)
            if name not in preds:
                print(f"  {name:<18}{m:>+9.3f}  [{lo:+.3f},{hi:+.3f}]"
                      f"{'':>7}{'':>9}   (diagnostic, no paired arm)")
                continue
            d, dlo, dhi = paired_bootstrap([preds[name][c] for c in cells],
                                           [preds["incell"][c] for c in cells], ys)
            print(f"  {name:<18}{m:>+9.3f}  [{lo:+.3f},{hi:+.3f}]"
                  f"{sum(rows[c][1] for c in cells) / len(cells):>7.3f}"
                  f"{sum(rows[c][2] for c in cells) / len(cells):>+9.3f}"
                  f"   {d:+.3f} [{dlo:+.3f},{dhi:+.3f}]")
        print("\n  per behaviour (never quote the mean of 9 alone):")
        for s in D.slugs:
            cs = [c for c in cells if c[0] == s]
            line = f"    {s[:30]:<32}"
            for name in arms:
                v = sum(arms[name][c][0] for c in cs) / len(cs)
                line += f"{name[:9]} {v:+.3f}  "
            jb = max(D.judge_mcc(*c) for c in cs)
            print(line + f"bestjudge {jb:+.3f}")
        print("\n  per cell:")
        for c in cells:
            print(f"    {c[0][:26]:<28}{c[1]:<9}" + "".join(
                f"{arms[n][c][0]:+.3f}  " for n in arms)
                + f"judge {D.judge_mcc(*c):+.3f}")
        print("\n  label overlap (why `crossgold` is confounded and "
              "`crossjudge` is not):")
        for s in D.slugs:
            js = D.judges[s]
            gg = [jaccard([i for i, v in enumerate(D.golds[(s, a)]) if v],
                          [i for i, v in enumerate(D.golds[(s, b)]) if v])
                  for a in js for b in js if a < b]
            jg = [jaccard([i for i, v in enumerate(D.jsets[(s, j)]) if v],
                          [i for i, v in enumerate(D.golds[(s, j)]) if v])
                  for j in js]
            print(f"    {s[:30]:<32}gold~gold {sum(gg) / len(gg):.3f}   "
                  f"jset~its own gold {sum(jg) / len(jg):.3f}")
    if what in ("all", "weights"):
        print("\n=== WEIGHT DIVERGENCE")
        for (s, j), d in report_weights(D).items():
            print(f"  {s[:26]:<28}{j:<9}rho(coef,idf)={d['rho_idf']:+.3f}  "
                  f"query rho={d['rho_idf_query']:+.3f}  "
                  f"neg query atoms {d['n_query_negative']}/{d['n_query']}  "
                  f"df+ {d['mean_df_positive']:.1f} df- {d['mean_df_negative']:.1f}")
    if what in ("all", "weights"):
        print("\n  is the learned weighting a function of what we compute?")
        r2 = learned_weight_model(D)
        m, lo, hi = ci(list(r2.values()))
        print(f"    coef ~ (log df, log passage-df, gloss len, n-clauses, kind): "
              f"R^2 = {m:.3f} [{lo:.3f},{hi:.3f}]")
    if what in ("all", "weights"):
        print("\n  declared salience vs learned coefficient (query atoms only):")
        r = report_declared_vs_learned(D)
        cells = D.cells()
        for c in cells:
            print(f"    {c[0][:26]:<28}{c[1]:<9}"
                  f"rho(declared) {r[c]['rho_declared']:+.3f}   "
                  f"rho(idf) {r[c]['rho_idf']:+.3f}   n={r[c]['n']}")
        m, lo, hi = ci([r[c]["rho_declared"] for c in cells])
        m2, lo2, hi2 = ci([r[c]["rho_idf"] for c in cells])
        print(f"    mean rho(declared) {m:+.3f} [{lo:+.3f},{hi:+.3f}]   "
              f"mean rho(idf) {m2:+.3f} [{lo2:+.3f},{hi2:+.3f}]")
    if what in ("all", "labelfree"):
        print("\n=== LABEL-FREE RE-WEIGHTINGS (oracle threshold, ranking only)")
        base = None
        for norm in ("none", "query", "passage"):
            r = report_label_free(D, norm)
            if base is None:
                base = r["idf (SHIPPED)"]
            print(f"  -- normalise={norm}")
            for name, rows in sorted(r.items(),
                                     key=lambda kv: -sum(x[0] for x in kv[1].values())):
                v = [rows[c][0] for c in D.cells()]
                a = [rows[c][1] for c in D.cells()]
                d = sum(v) / len(v) - sum(base[c][0] for c in D.cells()) / len(v)
                flag = "" if abs(d) < NOISE else "  <-- outside noise"
                print(f"    {name:<18}{_fmt(sum(v) / len(v))}  "
                      f"AUC {sum(a) / len(a):.3f}  vs shipped {d:+.3f}{flag}")
    if what in ("all", "attribution"):
        print("\n=== ATTRIBUTION OF THE +0.20 (per cell, then per behaviour)")
        T = report_tool(D)
        cells = D.cells()
        sup = report_incell(D, seeds=(11,))
        variants = LABEL_FREE_VARIANTS()
        best_lf = max(
            ((n, sum(best_threshold(query_scores(D, s, f), D.golds[(s, j)])[1]
                     for s, j in cells) / len(cells))
             for n, f in variants.items()), key=lambda kv: kv[1])

        def mean(f):
            return sum(f(c) for c in cells) / len(cells)
        rungs = [
            ("1 shipped tool, label-free cut", mean(lambda c: T[c]["label_free"])),
            ("2 shipped tool, ORACLE cut", mean(lambda c: T[c]["oracle"])),
            ("3 atom channel only, ORACLE", mean(lambda c: T[c]["atom_oracle"])),
            (f"4 best label-free re-weight ({best_lf[0]})", best_lf[1]),
            ("5 supervised atoms, honest cut", mean(lambda c: sup["atoms"][c][0])),
            ("6 supervised atoms, ORACLE", mean(lambda c: sup["atoms"][c][2])),
            ("7 supervised section, ORACLE", mean(lambda c: sup["section"][c][2])),
            ("8 supervised atoms+section, honest",
             mean(lambda c: sup["atoms+section"][c][0])),
            ("9 supervised atoms+section, ORACLE",
             mean(lambda c: sup["atoms+section"][c][2])),
            ("  judges (mean of 9)", mean(lambda c: D.judge_mcc(*c))),
        ]
        for n, v in rungs:
            print(f"  {n:<42}{_fmt(v)}")
        r = dict(rungs)
        print("\n  decomposition of shipped(label-free) -> supervised(honest):")
        print(f"    total gap                       "
              f"{r['8 supervised atoms+section, honest'] - r['1 shipped tool, label-free cut']:+.3f}")
        print(f"    calibration (rung 1->2)         "
              f"{r['2 shipped tool, ORACLE cut'] - r['1 shipped tool, label-free cut']:+.3f}")
        print(f"    per-atom RE-WEIGHTING (3->6)    "
              f"{r['6 supervised atoms, ORACLE'] - r['3 atom channel only, ORACLE']:+.3f}")
        print(f"      of which label-free reachable (3->4) "
              f"{r['4 best label-free re-weight (' + best_lf[0] + ')'] - r['3 atom channel only, ORACLE']:+.3f}")
        print(f"    section block (6->9)            "
              f"{r['9 supervised atoms+section, ORACLE'] - r['6 supervised atoms, ORACLE']:+.3f}")
        print(f"    supervised own calibration cost (9->8) "
              f"{r['8 supervised atoms+section, honest'] - r['9 supervised atoms+section, ORACLE']:+.3f}")
        print("\n  per behaviour (the mean of 9 hides that the ceiling LOSES on "
              "helpfulness):")
        for s in D.slugs:
            cs = [c for c in cells if c[0] == s]
            def m2(f):
                return sum(f(c) for c in cs) / len(cs)
            print(f"    {s[:30]:<32}tool {m2(lambda c: T[c]['label_free']):+.3f}  "
                  f"tool@oracle {m2(lambda c: T[c]['oracle']):+.3f}  "
                  f"sup {m2(lambda c: sup['atoms+section'][c][0]):+.3f}  "
                  f"judges {m2(lambda c: D.judge_mcc(*c)):+.3f}  "
                  f"best judge {max(D.judge_mcc(*c) for c in cs):+.3f}")
    if what in ("all", "mechanism"):
        print("\n=== MECHANISM: negative weights vs atoms outside the query")
        print("    (atoms only, OOF, ORACLE threshold — compare to the tool's "
              "atom channel at ITS oracle, +0.357)")
        r = report_mechanism(D)
        cells = D.cells()
        for name in ("all/free", "all/nonneg", "query/free", "query/nonneg"):
            v = [r[c][name][0] for c in cells]
            m, lo, hi = ci(v)
            print(f"  {name:<16}{m:+.3f}  [{lo:+.3f},{hi:+.3f}]  "
                  f"AUC {sum(r[c][name][1] for c in cells) / len(cells):.3f}")
        for s in D.slugs:
            cs = [c for c in cells if c[0] == s]
            print(f"    {s[:30]:<32}" + "  ".join(
                f"{n} {sum(r[c][n][0] for c in cs) / len(cs):+.3f}"
                for n in ("all/free", "all/nonneg", "query/free", "query/nonneg")))
    if what in ("all", "priors"):
        print("\n=== LABEL-FREE PASSAGE PRIORS (oracle threshold, ranking only)")
        r = report_priors(D)
        cells = D.cells()
        q = sum(r[("QUERY alone", "-")][c][0] for c in cells) / len(cells)
        for (name, mode), rows in sorted(
                r.items(), key=lambda kv: -sum(x[0] for x in kv[1].values())):
            v = sum(rows[c][0] for c in cells) / len(cells)
            a = sum(rows[c][1] for c in cells) / len(cells)
            d = v - q
            flag = "" if abs(d) < NOISE else "  <-- outside noise"
            print(f"  {name:<20}{mode:<14}{_fmt(v)}  AUC {a:.3f}  "
                  f"vs query alone {d:+.3f}{flag}")
        print("\n  per behaviour, best combination vs query alone:")
        for s in D.slugs:
            cs = [c for c in cells if c[0] == s]
            qa = sum(r[("QUERY alone", "-")][c][0] for c in cs) / len(cs)
            best = max(((k, sum(rows[c][0] for c in cs) / len(cs))
                        for k, rows in r.items() if k[1] == "query+prior"),
                       key=lambda kv: kv[1])
            print(f"    {s[:30]:<32}query {qa:+.3f}  best {best[0][0]} "
                  f"{best[1]:+.3f}  ({best[1] - qa:+.3f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
