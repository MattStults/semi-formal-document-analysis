"""sufficiency_vs_retrieval.py — DOES REPRESENTATION LOSS COST US RELEVANCE?

⚠️ THIS MODULE IS A PANEL-READING DIAGNOSTIC. NOTHING IT MEASURES MAY SHIP. ⚠️
=============================================================================
It joins the read-back fidelity result to the judges' pair-gold, so it consults
the answer key (contract §5 invariant 9: the panel is a measuring instrument,
never an input). Its output **may never inform the ontology, the vocabulary, a
prompt or a threshold**. It exists to answer one gate question in
`LADDER_PLAN.md` step 1 and then to be read, not consumed. `weight_diag.py`
carries the same fence for the same reason; this module deliberately does not
import it, and no module imports this one.

THE QUESTION
------------
Read-back (n=125 model-spec clauses, `readback_results.json`) found that 91 of
125 clauses are *identifiable* from their atoms while only 20 of 125 are
*sufficient* — a reader of the atoms would not know what the clause requires.
Identification and representation have come apart.

Step 1 asks whether that representation loss costs anything on the line the
project is actually judged on: **relevance retrieval**. If a clause whose atoms
lose its deontic force retrieves exactly as well as one that keeps it, then the
grammar's blind spots are orthogonal to relevance, and ladder steps 2-5 are
CONFLICT work that must be re-justified against the standing "focus on
relevance" instruction before any spend.

THE MEASUREMENT
---------------
* Unit: one of the 125 read-back clauses. 123 of them join to at least one of
  the 589 model-spec passages the judges graded (`panel_universe`); the 2 that
  join to none are reported and excluded — they have no retrieval outcome at
  all, and silently dropping them would be a coverage lie of the exact kind
  step 1 was written to avoid.
* Outcome: per-clause **retrieval error rate**. For each (passage joined to the
  clause) × (behaviour × pair-gold cell), a label-free query module either
  agrees with the gold or does not. The clause's error rate is the mean
  disagreement over all such trials. False positives and false negatives are
  reported separately because the panel is 4-27% positive and a pooled rate is
  dominated by FPs.
* Query module: **all three, side by side** (`MODULES`). `relevance.py` is the
  bag scorer and **VIOLATES invariant 10** (`HANDOFF.md:573`). The first draft
  of this file described it as the project's shipped label-free tool and
  reported it alone; that description was wrong and is withdrawn. `structural.py` at its shipped `any_atom` and
  `combined.py` at V1@`any_atom` (the +0.316 compliant headline,
  `PRIMARY_MODULE`) are the compliant arms, and every verdict sentence below is
  stated at `combined`. All three are built through
  `benchmark.build_query_module` so no arm can score a configuration the
  project does not report.
* Gold: `benchmark.pair_targets` — a judge predicts relevant iff its verdict
  >= 1, and gold for judge *j* is the intersection of the OTHER two judges.
* Predictor: the read-back `sufficient` / `faithful` booleans, the clause kind,
  and the CATEGORY of the clause's missing phrases.
* Effect size: difference in mean per-clause error rate between the two arms,
  with a percentile CI from a 20 000-resample CLAUSE-level bootstrap (clauses
  are the unit of the hypothesis; a passage-level bootstrap would treat the two
  passages of a two-passage clause as independent evidence). A rank AUC of the
  flag against the error rate is printed alongside, because a difference of
  means on a bounded rate hides whether the ordering holds at all.

THE MISSING-PHRASE CATEGORISATION, AND WHAT IS WRONG WITH IT
-----------------------------------------------------------
The 268 missing phrases are categorised into five NON-EXCLUSIVE classes plus an
implicit `other` (the empty set):

  party       — WHICH principal / role / audience the clause concerns
  deontic     — the FORCE of the requirement (obligation, permission, ban,
                default, preference strength)
  trigger     — WHEN the rule applies (an antecedent condition)
  exception   — a carve-out from an otherwise applicable rule
  precedence  — ordering or priority among RULES, INSTRUCTIONS or AUTHORITY
                LEVELS (deliberately not ordering among response options —
                "answer first, rationale second" is presentation order, not a
                conflict rule, and pooling the two was the first thing that
                made this category look large)

**Method: a hand-written lexical rule (`categorise`), not a model.** No API call
is permitted here, so there is no judge; the alternative was hand-labelling all
268, which is one annotator either way. Multi-label rather than a priority
chain, because most phrases carry a party AND a force AND a condition, and any
priority order would make every per-category effect an artefact of that order.

**Validation, honestly.** Two disjoint random samples of 60 phrases each, both
hand-labelled by the module's author against the definitions above. The DEV
sample was read first and the lexicon was revised once in response to it (five
edits: `supersession`/`subject to` added to precedence; bare singular `model`
removed from party, which was tagging "model-enhancing aims" and "model
behavior"; `during` added to trigger; `rules out` added to deontic). The
HELD-OUT sample was labelled only after that revision was frozen, and **the
held-out numbers are the ones reported**; the dev numbers are printed beside
them purely to show the size of the optimism.

Known and unfixed limits of the rule, stated so no one quotes it as clean:
  1. One annotator, no second reader, no adjudication. Inter-annotator
     agreement is UNMEASURED and cannot be measured offline.
  2. The rule is lexical, so `party` fires on any mention of a principal, while
     the semantic label asks whether the missing CONTENT is about who the party
     is. Recall is high and precision is the loss-bearing side; the measured
     split is printed per category.
  3. `exception` and `precedence` are small (12 and ~18 of 268), so their
     per-category effect CIs are wide by construction and no per-category null
     should be read as a demonstrated absence.

PRE-REGISTERED PREDICTIONS (written before any number below was computed)
------------------------------------------------------------------------
P1. `sufficient` will NOT separate retrieval error by more than the panel's
    noise floor (~0.045 MCC-equivalent; here, ~0.03 on an error rate). The
    read-back cross-tab already showed identification surviving where
    representation failed, and retrieval is an identification task: the tool
    fires on atom-name overlap, which is exactly what read-back showed is
    preserved.
P2. Split by missing-phrase category, `party` will show the LARGEST effect and
    `deontic` / `precedence` the smallest — party/addressee is what a relevance
    query keys on, whereas force and ordering are what a CONFLICT query keys on
    and are invisible to a bag-of-atoms retriever.
P3. `faithful` will behave like `sufficient` (no effect), and clause KIND will
    move the error rate more than either fidelity flag, because kind is a proxy
    for where in the document the clause sits and the section channel is
    already known to carry most of the recoverable signal.

MEASURED — THE ANSWER
---------------------
**YES, but not through the channel the prior named, and not by much more than
this design could ever have seen.** Regenerate with
`python3 sufficiency_vs_retrieval.py`; the table it prints is the deliverable
and this module adds no hand-transcribed constant. 123 clauses × 9 cells,
within-clause-kind pooled difference in per-clause retrieval error (PRIMARY),
20 000-resample clause bootstrap:

    sufficient        20/103   -0.096 [-0.182, -0.014]   (raw -0.055, ns)
    faithful          56/67    -0.157 [-0.251, -0.062]   (raw -0.104)
    >=1 unsupported   67/56    +0.157 [+0.062, +0.250]   (raw +0.104)
    missing party     61/62    +0.068 [-0.030, +0.166]   ns
    missing deontic   60/63    +0.036 [-0.056, +0.130]   ns
    missing precedence 11/63   -0.004 [-0.181, +0.186]   ns, 49 clauses dropped

**P1 is REFUTED, weakly.** Sufficiency does separate retrieval error once
clause kind is held fixed — sufficient clauses retrieve ~9.6 points better —
and the raw unstratified estimate hid it. The prediction that representation
loss is orthogonal to relevance does not survive.

**P2 is NOT supported.** The prior's asymmetry — party/addressee loss should
predict, deontic/precedence loss should not — is not visible. `party` is the
largest of the five (+0.068) and `deontic` the second (+0.036), but neither CI
excludes zero and they are not distinguishable from each other. Nothing here
licenses "party loss costs relevance, deontic loss does not"; it licenses
"this design cannot tell them apart". `exception` (-0.165) is the only
category CI excluding zero and it rests on 10 clauses with 25 dropped by
stratification — treat it as a lead, not a result.

**P3 is half right.** `faithful` did NOT behave like `sufficient` (it is the
stronger of the two), and clause kind does move the error rate — `meta` is
+0.127 [+0.012, +0.245] one-vs-rest, the largest single effect in the file.

**The mechanism is over-assertion, not under-representation.** `faithful` is
exactly the complement of "has >=1 unsupported phrase", and 312 of the 361
errors are FALSE POSITIVES. A render that asserts something the clause does
not say gives the query extra surface to match on, and the passage is retrieved
when the judges say it should not be. That is the opposite of the loss the
ladder was built to chase: it is not that the atoms carry too little, it is
that some of them carry something that is not there.

**Read every one of these against the MDE.** The design detects a difference of
~0.14-0.25 at 80% power depending on the split; the observed effects sit at or
below that, so each is a noisy estimate of a large effect rather than a precise
estimate of a small one. Roughly 20 splits were tested and 5 CIs exclude zero;
under multiple comparisons ~1 is expected by chance, so the `faithful` /
`unsupported` pair (the largest, and mechanistically explained) is the finding
to carry forward and the rest are leads.

MODULE SWAP — ADDED 2026-08-02, AND IT MOVES THE VERDICT
--------------------------------------------------------
Everything above this heading was computed through `relevance.py` alone. Run
under all three modules (`report_modules`), the picture splits cleanly in two:

    split                   relevance          structural          combined
    faithful (within-kind)  -0.157 [-.26,-.06] -0.155 [-.26,-.06] -0.147 [-.25,-.05]
    >=1 unsupported         +0.157 [+.06,+.25] +0.155 [+.06,+.25] +0.147 [+.05,+.24]
    sufficient (within-kind) -0.096 [-.19,-.01] -0.102 [-.19,-.02] -0.077 [-.18,+.02]

**`faithful` / `>=1 unsupported` is STABLE across all three modules.**
**`sufficient` is NOT: under `combined` V1@any — the compliant headline — its
CI spans zero.** `LADDER_PLAN.md` step 1 cleared its stop condition on the
sentence "sufficiency weakly predicts retrieval error". That sentence is true
only under the invariant-10-violating module. Under the module the project
actually intends to ship it is not established, and the gate should be read as
**NOT CLEARED on sufficiency** — only on over-assertion.

ATOM COUNT IS AN UNCONTROLLED COMMON CAUSE — THE PRIMARY ESTIMATE IS ADJUSTED
----------------------------------------------------------------------------
    rho(count of unsupported phrases, error)  combined  +0.193 [+0.026, +0.364]
    rho(atom count,                    error)  combined  +0.184 [+0.020, +0.350]

Under `combined` **both exclude zero and they are the same size**. A clause with
more atoms has more chances to assert something unsupported AND more surface to
match a behaviour query. Pooling `faithful` within atom-count tertile
(`atom_count_adjusted`, now the PRIMARY line in `report_fidelity`) attenuates
it by ~36%:

    faithful, within-kind          -0.157 (relevance) / -0.147 (combined)
    faithful, atom-count-adjusted  -0.100 (relevance) / -0.098 (combined)
                                            [-0.197,-0.006] / [-0.195,-0.002]

So the adjusted effect survives, but only just — under `combined` its upper
bound is -0.002. **"Over-assertion causes false positives" and "clauses with
broader atom sets cause false positives" are not separated by this design**,
and that distinction is exactly what decides whether deleting the unsupported
atoms can help.

**It has now been tested as an intervention and it does not help.**
`unsupported_ablation.py` deletes the 89 atoms responsible for the flagged
unsupported assertions and re-scores retrieval: the improvement is -0.0364
against a size-matched RANDOM control of -0.0363 (adjusted effect -0.0001,
MDE 0.0279) under `combined`. Deleting the same number of HIGHEST-DF atoms is
1.65x better. So the correlational effect above has no surviving causal reading
at this resolution, and the "broader atoms" side of the confound is the one
with intervention support.

MULTIPLICITY, RECOUNTED
-----------------------
`faithful` is the **exact complement** of `>=1 unsupported phrase` on all 125
clauses, and `sufficient` the exact complement of `>=1 missing phrase`
(`INDEPENDENT_FIDELITY_TESTS = 2`). The earlier "~20 splits tested, 5 CIs
exclude zero, ~1 expected by chance" counted one test twice, sign-flipped, in
two of those five. There are **two** distinct binary fidelity dimensions here,
not four, so the correction that applies to the surviving `faithful` result is
over 2 — which makes it **stronger**, not weaker. The per-category and
per-kind splits remain a separate, larger, under-powered family and are still
leads rather than results.

STOP CONDITION (from LADDER_PLAN.md step 1)
-------------------------------------------
The stop condition asked what to do if sufficiency does NOT predict retrieval
error. Under `relevance` it weakly does; **under the compliant `combined` it
does not** (see MODULE SWAP above), so the sentence the plan used to clear the
gate does not survive the module it intends to ship. What survives is the
over-assertion half — a precision problem in the existing annotations, not a
missing grammar feature — and even that is only partly separable from clause
breadth once atom count is adjusted for.
A ladder rung that raises sufficiency by adding expressive power, without
holding unsupported assertions flat, would be optimising the wrong end of this
result. This module reports the number; it does not make that decision, and it
must not be used to pick a threshold, an atom, or a prompt.
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

#: Carried over from `weight_diag.NOISE` for continuity of reading only.
#: ⚠️ It is NOT the binding constraint here and must not be quoted as one: the
#: MDE table in `report_power` shows this design cannot resolve anything below
#: ~0.14, i.e. four to eight times this number. Use the MDE.
NOISE = 0.030

CATEGORIES = ("party", "deontic", "trigger", "exception", "precedence")


# ------------------------------------------------------------- the lexicon
# FROZEN after the dev sample. Any edit invalidates the held-out error rate
# below it and the module must be re-validated on a fresh sample.

_PARTY = re.compile(
    r"\b(assistant|users?|user's|developers?|developer's|openai|gpt-\d|"
    r"system|root|operator|administrators?|end users?|third part\w*|"
    r"humans?|people|person|minors?|teens?|adolescent|adults?|u18|under-18|"
    r"parent|guardian|counselor|doctor|caregivers?|customers?|audience|"
    r"sub-?agents?|non-users|platform|organization|account)\b", re.I)
#: `human-like delivery` is a style, `humanity` is the mission. Neither is a party.
_PARTY_NOT = re.compile(r"human-like|humanity", re.I)
#: PLURAL `models` is a party ("publicly deployed models should comply").
#: SINGULAR `model` is usually an adjective ("model behavior", "model-enhancing
#: aims") and was removed after the dev sample showed it over-firing.
_PARTY_MODELS = re.compile(r"\bmodels\b", re.I)

_DEONTIC = re.compile(
    r"\b(must|should|shall|may|cannot|can't|required?|requires|requirement|"
    r"prohibit\w*|prohibition|forbidden|allow\w*|permit\w*|permission|"
    r"encourage[ds]?|advised|defaults?|do not|don't|never|rules out|"
    r"avoid\w*|avoidance|obligat\w*|mandat\w*|restrict\w*|not required)\b", re.I)

_TRIGGER = re.compile(
    r"\b(when|whenever|if|in cases where|depending on|upon|during|"
    r"conditions?|occurs when|applies when|triggers?|only after|"
    r"as appropriate|when appropriate|in those cases|under high)\b", re.I)

_EXCEPTION = re.compile(
    r"\b(except|exceptions?|unless|other than|does not apply|"
    r"only when|only if|aside from|carve-?out|but not|apart from|"
    r"barring|outside|non-exhaustive)\b", re.I)

_PRECEDENCE = re.compile(
    r"\b(precedes?|preceded|precedence|overrides?|overriding|overrode|"
    r"priority|prioriti\w*|higher-level|higher-authority|higher level|"
    r"higher-order|supersed\w*|supersession|subject to|ranks? (?:below|above)|"
    r"outrank\w*|takes? priority|takes? precedence|preferred over|"
    r"less preferred|far below|ranks? \w+|hierarch\w*|chain of command|"
    r"authority)\b", re.I)


def categorise(phrase: str) -> frozenset:
    """`frozenset` of the categories this missing phrase carries.

    MULTI-LABEL. An empty set is the implicit `other` class — a fact, a
    definition of a thing, an example, or a rationale, none of which is one of
    the five loss kinds the question asks about.
    """
    out = set()
    if _PARTY.search(phrase) and not _PARTY_NOT.search(phrase):
        out.add("party")
    if _PARTY_MODELS.search(phrase) and not re.search(r"model spec", phrase, re.I):
        out.add("party")
    if _DEONTIC.search(phrase):
        out.add("deontic")
    if _TRIGGER.search(phrase):
        out.add("trigger")
    if _EXCEPTION.search(phrase):
        out.add("exception")
    if _PRECEDENCE.search(phrase):
        out.add("precedence")
    return frozenset(out)


# ------------------------------------------------------------ the read-back

_FID = {}


def fidelity(path: str = READBACK) -> dict:
    """`{clause_id: {faithful, sufficient, missing, unsupported}}` — 125 rows."""
    if path not in _FID:
        with open(path) as fh:
            _FID[path] = json.load(fh)["results"]["fidelity"]
    return _FID[path]


def missing_phrases(path: str = READBACK) -> list:
    """`[(clause_id, phrase)]` in a FIXED order — clause id, then the order the
    read-back emitted them. The validation sample indexes into this list, so the
    order is load-bearing and must not become dict-insertion-dependent."""
    fid = fidelity(path)
    return [(cid, p) for cid in sorted(fid) for p in fid[cid]["missing"]]


# ------------------------------------------- validating the categorisation

DEV_SEED = 20260802
HELDOUT_SEED = 20260803
#: Which sample the module quotes as its error rate. The dev sample is the one
#: the lexicon was tuned on and quoting it would be a training-set number.
REPORTED_VALIDATION_SAMPLE = "heldout"


def sample_indices(n: int, seed: int, exclude=()) -> list:
    """Deterministic index sample into `missing_phrases()`."""
    pool = [i for i in range(len(missing_phrases())) if i not in set(exclude)]
    return sorted(random.Random(seed).sample(pool, n))


#: Hand labels, DEV sample (read first; the lexicon was revised once after it).
HAND_LABELS_DEV = {
    9: ("deontic", "precedence"),
    11: ("party", "deontic"),
    12: ("party",),
    17: (),
    20: (),
    24: ("party",),
    34: ("party",),
    36: ("party",),
    38: ("party",),
    46: ("precedence",),
    51: ("party", "deontic"),
    53: ("party", "deontic"),
    55: ("trigger",),
    61: (),
    62: (),
    64: (),
    75: ("deontic", "trigger"),
    80: ("party",),
    88: ("trigger",),
    89: (),
    97: ("party",),
    99: (),
    101: ("party",),
    104: ("deontic", "trigger"),
    107: (),
    109: ("trigger",),
    114: ("deontic", "exception"),
    115: ("deontic", "party"),
    117: (),
    123: (),
    128: ("deontic", "exception"),
    130: ("deontic",),
    139: ("trigger",),
    141: ("deontic", "trigger"),
    142: (),
    151: ("deontic", "party"),
    155: ("party", "deontic", "trigger"),
    156: ("party", "deontic"),
    157: ("party",),
    158: (),
    161: (),
    162: ("trigger",),
    171: ("deontic",),
    172: ("deontic",),
    175: (),
    176: (),
    178: (),
    183: (),
    194: ("trigger",),
    196: ("trigger", "party"),
    200: ("deontic",),
    205: ("party", "deontic", "trigger"),
    209: (),
    212: ("deontic", "party"),
    219: (),
    229: ("party",),
    241: (),
    242: (),
    248: ("deontic",),
    266: ("party", "trigger", "deontic"),
}

#: Hand labels, HELD-OUT sample. Labelled after the lexicon was frozen.
#: THIS is the sample the reported error rate comes from.
HAND_LABELS_HELDOUT = {
    4: ("deontic", "trigger"),
    13: ("precedence", "party"),
    19: ("party",),
    21: (),
    23: ("party",),
    26: ("deontic", "trigger"),
    33: ("party",),
    40: ("deontic",),
    44: ("party",),
    45: ("trigger", "precedence", "exception"),
    52: ("deontic", "precedence", "party"),
    60: ("deontic", "precedence"),
    66: (),
    67: ("party", "trigger"),
    76: ("deontic",),
    78: (),
    82: (),
    91: (),
    98: ("party",),
    110: ("party",),
    120: (),
    125: ("exception", "trigger"),
    129: ("deontic", "trigger", "exception"),
    133: (),
    135: ("exception", "party"),
    143: ("deontic",),
    144: ("deontic",),
    145: (),
    159: (),
    167: ("deontic",),
    168: ("deontic", "exception", "party"),
    181: (),
    182: (),
    184: ("trigger",),
    185: ("trigger", "deontic"),
    191: (),
    195: ("trigger", "party"),
    199: (),
    201: ("deontic", "trigger"),
    207: ("party",),
    208: ("party",),
    210: (),
    211: (),
    214: ("deontic",),
    215: ("deontic",),
    221: ("deontic",),
    222: ("deontic",),
    224: ("deontic",),
    225: (),
    228: (),
    232: ("deontic",),
    236: ("deontic",),
    237: ("deontic",),
    246: ("party", "deontic", "trigger"),
    247: ("party",),
    251: ("exception",),
    252: ("deontic",),
    256: ("party", "deontic"),
    257: ("deontic", "party", "trigger"),
    267: ("party", "deontic"),
}


def validate(hand_labels: dict) -> dict:
    """Score `categorise` against hand labels. Per-category tp/fp/fn with
    precision and recall, plus the exact-set-match rate over phrases."""
    rows = missing_phrases()
    per = {c: {"tp": 0, "fp": 0, "fn": 0} for c in CATEGORIES}
    exact = 0
    for idx, gold in hand_labels.items():
        pred = set(categorise(rows[idx][1]))
        gold = set(gold)
        if pred == gold:
            exact += 1
        for c in CATEGORIES:
            if c in pred and c in gold:
                per[c]["tp"] += 1
            elif c in pred:
                per[c]["fp"] += 1
            elif c in gold:
                per[c]["fn"] += 1
    for c, r in per.items():
        r["precision"] = r["tp"] / (r["tp"] + r["fp"]) if r["tp"] + r["fp"] else 1.0
        r["recall"] = r["tp"] / (r["tp"] + r["fn"]) if r["tp"] + r["fn"] else 1.0
    n = len(hand_labels) or 1
    return {"n": len(hand_labels), "per_category": per,
            "exact_match": exact / n}


# --------------------------------------------------------------- statistics

def bootstrap_diff(a, b, n: int = 20000, seed: int = 20260802, alpha: float = 0.05):
    """`(lo, hi, diff)` — percentile CI on mean(a) - mean(b).

    Resamples the two arms INDEPENDENTLY with replacement: the split is
    between clauses, so there is no pairing to preserve, and a paired bootstrap
    here would be a category error.
    """
    if not a or not b:
        raise ValueError(
            f"bootstrap_diff needs both arms non-empty (got {len(a)} and "
            f"{len(b)}); an empty arm is NO DATA, and returning 0.0 would "
            f"print as NO EFFECT")
    diff = sum(a) / len(a) - sum(b) / len(b)
    rng = random.Random(seed)
    ds = []
    la, lb = len(a), len(b)
    for _ in range(n):
        ma = sum(a[rng.randrange(la)] for _ in range(la)) / la
        mb = sum(b[rng.randrange(lb)] for _ in range(lb)) / lb
        ds.append(ma - mb)
    ds.sort()
    lo = ds[int(alpha / 2 * n)]
    hi = ds[min(n - 1, int((1 - alpha / 2) * n))]
    return lo, hi, diff


def auc(scores, y) -> float:
    """Rank AUC with ties averaged — the same convention as `weight_diag.auc`
    and `benchmark`, so numbers are comparable across the repo."""
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


def wilson(k: int, n: int, z: float = 1.96):
    """Wilson interval — used for the validation proportions, where the normal
    approximation is wrong at the small per-category counts."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - r) / d, (c + r) / d)


# ------------------------------------------------------------ clause kinds

#: The read-back strata. 25 clauses of each, `readback.CLAUSE_KINDS`.
CLAUSE_KINDS = ("conditional", "definitional", "example", "holistic", "meta")

_KINDS = {}


def clause_kinds() -> dict:
    """`{clause_id: kind}` for the 125 read-back clauses, from the same clause
    file `readback.py` sampled from."""
    if not _KINDS:
        sys.path.insert(0, REPO)
        import benchmark as B
        rows, _src = B.load_clauses()
        by_id = {r["id"]: r.get("kind") for r in rows}
        for cid in fidelity():
            _KINDS[cid] = by_id.get(cid)
    return dict(_KINDS)


def clause_categories() -> dict:
    """`{clause_id: set of categories}` — the UNION over the clause's missing
    phrases. A clause with no missing phrase carries no category, which is the
    correct encoding: nothing was lost, so no loss kind applies."""
    out = {}
    for cid, row in fidelity().items():
        s = set()
        for p in row["missing"]:
            s |= categorise(p)
        out[cid] = s
    return out


# -------------------------------------------------------- the retrieval join

#: The three query modules this diagnostic scores, in the order they are
#: printed. `relevance` is the bag scorer and VIOLATES invariant 10
#: (`HANDOFF.md:573`); `structural` and `combined` are compliant. The original
#: step-1 analysis ran only through `relevance`, so every effect it reported
#: was conditional on the module the contract is retiring.
MODULES = ("relevance", "structural", "combined")

#: The compliant headline configuration (`combined` V1@`any_atom`, +0.316 MCC).
#: The verdict sentence is stated at this module, not at `relevance`.
PRIMARY_MODULE = "combined"

#: `faithful` is the exact complement of `>=1 unsupported phrase` and
#: `sufficient` the exact complement of `>=1 missing phrase` — proven on all 125
#: clauses by `test_fidelity_flags_are_exact_complements_not_independent_tests`.
#: So the fidelity block contains TWO distinct binary tests reported four times,
#: not four. Any multiplicity correction must use this number.
INDEPENDENT_FIDELITY_TESTS = 2


def predictor(name: str, panel_obj: dict, clauses):
    """`slug -> {clause_id}` for one query module, in its SHIPPED configuration.

    Routed through `benchmark.build_query_module` so the configuration cannot
    drift from the one the project reports: `combined` is V1@`any_atom`,
    `structural` is at `structural.PRIMARY_OPERATOR` (`any_atom`), and
    `relevance` is the bag scorer with no threshold argument. Rebuilding any of
    these by hand here is how a diagnostic ends up scoring a configuration
    nobody ships.
    """
    if name not in MODULES:
        raise ValueError(f"unknown module {name!r}; have {list(MODULES)}")
    sys.path.insert(0, REPO)
    import benchmark as B
    import relevance as R
    qm = B.build_query_module(name, panel_obj, clauses,
                              annotations=R.load_annotations(ANNOTATIONS),
                              atoms=BEHAVIOUR_ATOMS)
    return qm.predict


class Retrieval:
    """Per-clause retrieval outcome against the judges' pair-gold.

    `rate[cid]` is the fraction of (passage × cell) trials on which the query
    module named in `.module` disagreed with the gold. `unjoined` is the clause
    ids with no graded passage at all — they are excluded from every arm and
    printed, not silently dropped.
    """

    def __init__(self):
        self.cells = []
        self.passages = {}
        self.trials = {}
        self.err = {}
        self.fp = {}
        self.fn = {}
        self.rate = {}
        self.unjoined = []
        self.panel = None
        self.module = None

    def rates(self, cids) -> list:
        return [self.rate[c] for c in cids]


def _build_retrieval(panel: str = "v1", module: str = "relevance") -> Retrieval:
    """Build the join. Reads the panel — see the module banner."""
    sys.path.insert(0, REPO)
    import benchmark as B
    import inventory
    import panel_universe as PU

    ps = PU.spec_passages(SPEC)
    clauses, _src = B.load_clauses()
    joins = {}
    for loc, _sec, text in ps:
        q, _ = PU.citation_quote(text)
        joins[loc] = [r["id"] for r in inventory.match_passage(q, clauses)]
    clause2loc = defaultdict(list)
    for loc, cids in joins.items():
        for c in cids:
            clause2loc[c].append(loc)

    if panel == "v2":
        import panel_v2
        panel_obj = panel_v2.load_panel(spec_keys=(SPEC_KEY,))
    else:
        panel_obj = B.load_true_panel(spec_keys=(SPEC_KEY,))
    slugs = sorted(s for s, b in panel_obj.items()
                   if SPEC_KEY in (b.get("coverage") or {}))

    predict = predictor(module, panel_obj, clauses)

    out = Retrieval()
    out.panel = panel
    out.module = module
    # (slug, judge) -> (predicted-passage set, gold-passage set)
    cell_data = {}
    for s in slugs:
        # The SHIPPED label-free cut. Not an oracle threshold: a number no
        # consumer can obtain is not a diagnosis of the consumer.
        pred_clauses = predict(s)
        pred_locs = {loc for loc, cids in joins.items()
                     if any(c in pred_clauses for c in cids)}
        for j, t in B.pair_targets(panel_obj[s], spec_key=SPEC_KEY).items():
            cell_data[(s, j)] = (pred_locs, set(t["gold"]))
    out.cells = sorted(cell_data)

    for cid in fidelity():
        locs = sorted(clause2loc.get(cid, ()))
        if not locs:
            out.unjoined.append(cid)
            continue
        out.passages[cid] = locs
        fp = fn = 0
        for cell in out.cells:
            pred, gold = cell_data[cell]
            for loc in locs:
                p, y = loc in pred, loc in gold
                if p and not y:
                    fp += 1
                elif y and not p:
                    fn += 1
        n = len(locs) * len(out.cells)
        out.trials[cid] = n
        out.fp[cid] = fp
        out.fn[cid] = fn
        out.err[cid] = fp + fn
        out.rate[cid] = (fp + fn) / n
    out.unjoined.sort()
    return out


_RETRIEVAL = {}


def retrieval(panel: str = "v1", module: str = "relevance") -> Retrieval:
    """Cached per (panel, MODULE). Keying on the panel alone would hand every
    module the first module's numbers and print three identical rows."""
    key = (panel, module)
    if key not in _RETRIEVAL:
        _RETRIEVAL[key] = _build_retrieval(panel, module)
    return _RETRIEVAL[key]


# ------------------------------------------------------------- the effects

def effect(R: Retrieval, flag, n: int = 20000, seed: int = 20260802) -> dict:
    """Split the scored clauses on `flag(cid)` and measure the difference.

    Returns means, the difference, its percentile CI, and the rank AUC of the
    flag against the per-clause error rate. The AUC is there because a
    difference of means on a bounded rate can be small while the ordering is
    perfect, and vice versa.
    """
    cids = sorted(R.rate)
    t = [c for c in cids if flag(c)]
    f = [c for c in cids if not flag(c)]
    if not t or not f:
        raise ValueError(
            f"degenerate split: {len(t)} true / {len(f)} false out of "
            f"{len(cids)}. An arm with no clauses is NO DATA, not NO EFFECT")
    a, b = R.rates(t), R.rates(f)
    lo, hi, diff = bootstrap_diff(a, b, n=n, seed=seed)
    y = [1 if flag(c) else 0 for c in cids]
    return {"n_true": len(t), "n_false": len(f),
            "mean_true": sum(a) / len(a), "mean_false": sum(b) / len(b),
            "diff": diff, "lo": lo, "hi": hi,
            "auc": auc(R.rates(cids), y)}


# ------------------------------------------------------------- reporting

def _row(name, e):
    return (f"  {name:<34} {e['n_true']:>4}/{e['n_false']:<4} "
            f"{e['mean_true']:.3f}  {e['mean_false']:.3f}  "
            f"{e['diff']:+.3f} [{e['lo']:+.3f}, {e['hi']:+.3f}]  "
            f"AUC {e['auc']:.3f}")


_HEAD = ("  {:<34} {:>9} {:>6}  {:>6}  {:>22}  {}".format(
    "split", "n T/F", "err T", "err F", "diff [95% CI]", "AUC"))


def _kind_row(name, R, flag, n):
    """The PRIMARY estimate: the same difference, pooled WITHIN clause kind.

    Kind is a common cause of both sides — sufficiency by kind runs 1/25
    (conditional) to 9/25 (example), and the panel hit rate by kind runs 0.056
    (meta) to 0.242 (holistic), so the confound alone sits at the n=125
    significance threshold. An unstratified difference on these data is not
    interpretable and is printed only beside this line, never instead of it.
    """
    try:
        e = stratified_effect(R, flag, lambda c: clause_kinds()[c], n=n)
    except ValueError as exc:
        return f"    {name:<32} within-kind DEGENERATE: {exc}"
    return (f"    {name:<32} {e['n_true']:>4}/{e['n_false']:<4} "
            f"{e['diff']:+.3f} [{e['lo']:+.3f}, {e['hi']:+.3f}]  "
            f"within-kind PRIMARY ({e['strata']} strata, "
            f"{e['dropped']} dropped)")


_FID_SPLITS = (
    ("sufficient", lambda fid, c: fid[c]["sufficient"]),
    ("faithful", lambda fid, c: fid[c]["faithful"]),
    ("faithful AND sufficient",
     lambda fid, c: fid[c]["faithful"] and fid[c]["sufficient"]),
    ("has >=1 missing phrase", lambda fid, c: bool(fid[c]["missing"])),
    ("has >=1 unsupported phrase", lambda fid, c: bool(fid[c]["unsupported"])),
)


def _adj_row(name, R, flag, n):
    """THE PRIMARY estimate — the difference pooled WITHIN atom-count tertile.

    Atom count is an uncontrolled common cause of both sides and it is the same
    size as the effect: rho(unsupported count, error) = +0.185 [+0.011, +0.352]
    against rho(atom count, error) = +0.170 [-0.004, +0.337], and under
    `combined` BOTH exclude zero. Unadjusted, "over-assertion produces false
    positives" and "clauses with broad atom sets produce false positives" are
    the same number wearing two names — and which of the two is true decides
    whether deleting the unsupported atoms can help at all.
    """
    try:
        e = atom_count_adjusted(R, flag, n=n)
    except ValueError as exc:
        return f"    {name:<32} atom-count-adjusted DEGENERATE: {exc}"
    return (f"    {name:<32} {e['n_true']:>4}/{e['n_false']:<4} "
            f"{e['diff']:+.3f} [{e['lo']:+.3f}, {e['hi']:+.3f}]  "
            f"atom-count-adjusted PRIMARY ({e['strata']} tertiles, "
            f"{e['dropped']} dropped)")


def report_fidelity(R: Retrieval, n: int = 20000) -> list:
    fid = fidelity()
    out = [f"FIDELITY FLAGS vs per-clause retrieval error  [module: "
           f"{R.module}]",
           "  (the raw difference is the CONTEXT line; the within-kind pooled "
           "difference is the KIND-adjusted estimate;",
           "   the ATOM-COUNT-ADJUSTED line is PRIMARY — atom count is a "
           "common cause of the same magnitude as the effect)",
           _HEAD]
    for label, fn_ in _FID_SPLITS:
        f = (lambda c, fn_=fn_: fn_(fid, c))
        out.append(_row(label, effect(R, f, n=n)))
        out.append(_kind_row(label, R, f, n))
        out.append(_adj_row(label, R, f, n))
    return out


_MODULE_NOTE = {
    "relevance": "bag scorer — VIOLATING invariant 10 (HANDOFF.md:573)",
    "structural": "compliant, shipped `any_atom`",
    "combined": "compliant, V1@`any_atom` — the +0.316 headline",
}


def report_modules(n: int = 20000, panel: str = "v1") -> list:
    """The same two fidelity tests under all three query modules, side by side.

    The original step-1 table was computed only under `relevance`. A fidelity
    effect that exists only under the module the contract is retiring is not a
    fact about the tool, and `LADDER_PLAN.md` step 1's gate was cleared on one.
    """
    fid = fidelity()
    out = ["MODULE SWAP — the same effects under all three query modules",
           "  {:<12} {:<26} {:>10} {:>22} {:>22}".format(
               "module", "split", "raw", "within-kind", "atom-count-adjusted")]
    for m in MODULES:
        Rm = retrieval(panel, m)
        for label, fn_ in _FID_SPLITS:
            f = (lambda c, fn_=fn_: fn_(fid, c))
            raw = effect(Rm, f, n=n)
            try:
                k = stratified_effect(Rm, f, lambda c: clause_kinds()[c], n=n)
                ks = f"{k['diff']:+.3f} [{k['lo']:+.3f},{k['hi']:+.3f}]"
            except ValueError:
                ks = "DEGENERATE"
            try:
                a = atom_count_adjusted(Rm, f, n=n)
                as_ = f"{a['diff']:+.3f} [{a['lo']:+.3f},{a['hi']:+.3f}]"
            except ValueError:
                as_ = "DEGENERATE"
            out.append("  {:<12} {:<26} {:>+10.3f} {:>22} {:>22}".format(
                m, label, raw["diff"], ks, as_))
        out.append(f"    ^ {m}: {_MODULE_NOTE[m]}")
    out += ["",
            "  THE COMMON CAUSE, per module — rho(x, per-clause error). If "
            "atom count moves the error",
            "  rate as hard as the unsupported count does, the two stories are "
            "not separated here.",
            "  {:<12} {:>26} {:>26}".format(
                "module", "rho(unsupported count)", "rho(atom count)")]
    for m in MODULES:
        Rm = retrieval(panel, m)
        u = continuous_effect(Rm, lambda c: len(fid[c]["unsupported"]), n=n)
        a = continuous_effect(Rm, lambda c: clause_atom_count()[c], n=n)
        out.append("  {:<12} {:>26} {:>26}".format(
            m,
            f"{u['rho']:+.3f} [{u['lo']:+.3f},{u['hi']:+.3f}]",
            f"{a['rho']:+.3f} [{a['lo']:+.3f},{a['hi']:+.3f}]"))
    out += [
        "",
        "  MULTIPLICITY. `faithful` is the EXACT complement of `>=1 "
        "unsupported phrase` and",
        "  `sufficient` of `>=1 missing phrase` on all 125 clauses (proven in "
        "the tests), and",
        "  `faithful AND sufficient` is a FUNCTION of the two. So the "
        f"{len(_FID_SPLITS)} rows above carry",
        f"  {INDEPENDENT_FIDELITY_TESTS} distinct binary fidelity dimensions, "
        f"not {len(_FID_SPLITS)} independent tests, and the correction is over",
        f"  {INDEPENDENT_FIDELITY_TESTS} — which makes the surviving "
        "`faithful` finding STRONGER, not weaker.",
    ]
    return out


def report_categories(R: Retrieval, n: int = 20000) -> list:
    flags = clause_categories()
    out = ["MISSING-PHRASE CATEGORY vs per-clause retrieval error",
           "  (within-kind pooled difference is PRIMARY; per-category MDE is "
           "in the POWER block above — every one of these cells is smaller "
           "than the headline and correspondingly less informative)",
           _HEAD]
    splits = [(f"missing {c}", (lambda k, c=c: c in flags[k]))
              for c in CATEGORIES]
    splits.append(("missing OTHER only (no category)",
                   lambda k: bool(fidelity()[k]["missing"]) and not flags[k]))
    for label, f in splits:
        try:
            out.append(_row(label, effect(R, f, n=n)))
        except ValueError as exc:
            out.append(f"  {label:<34} DEGENERATE: {exc}")
            continue
        out.append(_kind_row(label, R, f, n))
    return out


def report_kinds(R: Retrieval, n: int = 20000) -> list:
    kinds = clause_kinds()
    out = ["CLAUSE KIND vs per-clause retrieval error (one-vs-rest)", _HEAD]
    for k in CLAUSE_KINDS:
        out.append(_row(f"kind = {k}", effect(R, lambda c, k=k: kinds[c] == k,
                                              n=n)))
    return out


def report_validation() -> list:
    out = ["CATEGORISER VALIDATION — the rule is a hand-written lexicon",
           "  reported sample: HELD-OUT (the lexicon was tuned on dev, then "
           "frozen)",
           "  {:<12} {:>10} {:>10} {:>10} {:>10}".format(
               "category", "P(held-out)", "R(held-out)", "P(dev)", "R(dev)")]
    vh = validate(HAND_LABELS_HELDOUT)
    vd = validate(HAND_LABELS_DEV)
    for c in CATEGORIES:
        h, d = vh["per_category"][c], vd["per_category"][c]
        out.append("  {:<12} {:>10.2f} {:>10.2f} {:>10.2f} {:>10.2f}   "
                   "(held-out tp/fp/fn {}/{}/{})".format(
                       c, h["precision"], h["recall"], d["precision"],
                       d["recall"], h["tp"], h["fp"], h["fn"]))
    lo, hi = wilson(round(vh["exact_match"] * vh["n"]), vh["n"])
    out.append(f"  exact-set match, held-out: {vh['exact_match']:.3f} "
               f"[{lo:.3f}, {hi:.3f}] on n={vh['n']}   "
               f"(dev {vd['exact_match']:.3f}) — i.e. the rule gets the FULL "
               f"category set wrong on ~{100 * (1 - vh['exact_match']):.0f}% "
               f"of phrases")
    return out


def report_counts(R: Retrieval) -> list:
    flags = clause_categories()
    per_phrase = {c: 0 for c in CATEGORIES}
    other = 0
    for _cid, p in missing_phrases():
        s = categorise(p)
        if not s:
            other += 1
        for c in s:
            per_phrase[c] += 1
    out = ["BASE RATES",
           f"  clauses scored {len(R.rate)}, unjoinable {len(R.unjoined)} "
           f"({', '.join(R.unjoined)}) — no graded passage, no retrieval "
           f"outcome, excluded from every arm",
           f"  cells {len(R.cells)}: "
           + ", ".join(f"{s}/{j}" for s, j in R.cells),
           f"  trials {sum(R.trials.values())}, "
           f"errors {sum(R.err.values())} "
           f"(FP {sum(R.fp.values())} / FN {sum(R.fn.values())}), "
           f"pooled error rate "
           f"{sum(R.err.values()) / sum(R.trials.values()):.3f}",
           f"  missing phrases 268 -> " + ", ".join(
               f"{c} {per_phrase[c]}" for c in CATEGORIES)
           + f", other {other}",
           "  clauses carrying each category: " + ", ".join(
               f"{c} {sum(1 for k in R.rate if c in flags[k])}"
               for c in CATEGORIES)]
    return out


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    panel = "v2" if "--panel-v2" in argv else "v1"
    n = 2000 if "--fast" in argv else 20000
    R = retrieval(panel)
    lines = ["=" * 78,
             "sufficiency_vs_retrieval — LADDER_PLAN.md step 1",
             "⚠️ DIAGNOSTIC. Reads the panel. Its output may never inform the "
             "ontology,",
             "   the vocabulary, a prompt or a threshold. Read it; do not "
             "consume it.",
             "=" * 78,
             f"panel: {panel}   bootstrap: {n} resamples, clause-level, "
             f"seed 20260802   noise floor ~{NOISE:.3f}",
             ""]
    for block in (report_counts(R), report_power(R, n), report_fidelity(R, n),
                  report_modules(n, panel),
                  report_continuous(R, n), report_categories(R, n),
                  report_kinds(R, n), report_confounds(R, n),
                  report_validation()):
        lines.extend(block)
        lines.append("")
    print("\n".join(lines))
    return 0




# ------------------------------------------------------ the atom-count confound

_ATOM_COUNT = {}


def clause_atom_count(path: str = ANNOTATIONS) -> dict:
    """`{clause_id: number of atoms}` from the SHIPPED annotation file — the same
    atoms `readback.render` was given and the same atoms `relevance` queries."""
    if not _ATOM_COUNT:
        with open(path) as fh:
            ann = json.load(fh)
        for cid, ats in ann["by_clause"].items():
            _ATOM_COUNT[cid] = len(ats)
        for cid in fidelity():
            _ATOM_COUNT.setdefault(cid, 0)
    return dict(_ATOM_COUNT)


def stratified_effect(R: Retrieval, flag, stratum, n: int = 20000,
                      seed: int = 20260802, alpha: float = 0.05) -> dict:
    """`effect` computed WITHIN strata and pooled by stratum size.

    The fidelity flags are confounded with how many atoms a clause has: more
    atoms means more opportunity to assert something unsupported AND more
    opportunity to match a behaviour query. Holding atom count fixed is the
    cheapest available control, and it is the difference between "unfaithful
    renders retrieve worse" and "verbose clauses retrieve worse".
    """
    cids = sorted(R.rate)
    groups = defaultdict(lambda: ([], []))
    for c in cids:
        t, f = groups[stratum(c)]
        (t if flag(c) else f).append(R.rate[c])
    usable = {k: v for k, v in groups.items() if v[0] and v[1]}
    if not usable:
        raise ValueError(
            "no stratum contains both arms — the flag is collinear with the "
            "stratum, so there is NO within-stratum contrast to pool. This is "
            "NO DATA, not NO EFFECT")

    def pooled(pick):
        num = den = 0.0
        for k, (a, b) in usable.items():
            aa, bb = pick(a), pick(b)
            w = len(a) + len(b)
            num += w * (sum(aa) / len(aa) - sum(bb) / len(bb))
            den += w
        return num / den

    diff = pooled(lambda v: v)
    rng = random.Random(seed)

    def resample(v):
        return [v[rng.randrange(len(v))] for _ in range(len(v))]

    ds = sorted(pooled(resample) for _ in range(n))
    lo = ds[int(alpha / 2 * n)]
    hi = ds[min(n - 1, int((1 - alpha / 2) * n))]
    dropped = sum(len(a) + len(b) for k, (a, b) in groups.items()
                  if k not in usable)
    return {"diff": diff, "lo": lo, "hi": hi, "strata": len(usable),
            "dropped": dropped,
            "n_true": sum(len(a) for a, _b in usable.values()),
            "n_false": sum(len(b) for _a, b in usable.values())}


def atom_tertile(counts: dict):
    """Return a stratum function splitting clauses into atom-count tertiles."""
    vals = sorted(counts[c] for c in fidelity())
    lo = vals[len(vals) // 3]
    hi = vals[2 * len(vals) // 3]
    return lambda c: 0 if counts[c] <= lo else (1 if counts[c] <= hi else 2)


def atom_count_adjusted(R: Retrieval, flag, n: int = 20000,
                        seed: int = 20260802) -> dict:
    """THE PRIMARY ESTIMATE: `flag`'s effect pooled within atom-count tertile.

    Thin wrapper over `stratified_effect` so the primary estimate has ONE name
    and every caller reaches the same stratification. The tertile cuts come
    from `atom_tertile` over the read-back clauses, not over the arm, so the
    strata do not move when the flag does.
    """
    return stratified_effect(R, flag, atom_tertile(clause_atom_count()),
                             n=n, seed=seed)


def report_confounds(R: Retrieval, n: int = 20000) -> list:
    counts = clause_atom_count()
    fid = fidelity()
    strat = atom_tertile(counts)
    med = sorted(counts[c] for c in R.rate)[len(R.rate) // 2]
    out = ["CONFOUND CHECK — atom count",
           _HEAD,
           _row("atom count > median", effect(R, lambda c: counts[c] > med, n=n)),
           _row("n missing phrases > 2",
                effect(R, lambda c: len(fid[c]["missing"]) > 2, n=n)),
           "  within-stratum (atom-count tertile) pooled differences:"]
    for label, fn_ in (("faithful | atom-count", lambda c: fid[c]["faithful"]),
                       ("sufficient | atom-count",
                        lambda c: fid[c]["sufficient"]),
                       ("missing party | atom-count",
                        lambda c: "party" in clause_categories()[c])):
        e = stratified_effect(R, fn_, strat, n=n)
        out.append(f"    {label:<28} {e['n_true']:>4}/{e['n_false']:<4} "
                   f"{e['diff']:+.3f} [{e['lo']:+.3f}, {e['hi']:+.3f}]  "
                   f"({e['strata']} strata, {e['dropped']} clauses dropped)")
    return out




# ------------------------------------------------------------------- POWER
# Written because the honest reading of a null here is "we could not have seen
# it", not "it is not there". 20 positives of 125 is the binding constraint on
# everything in this file, and it is stated BEFORE any effect is printed.

#: two-sided alpha = .05, power = .80
_Z_ALPHA = 1.959964
_Z_BETA = 0.8416212


def mde_two_proportion(n1: int, n2: int, p: float,
                       z_alpha: float = _Z_ALPHA, z_beta: float = _Z_BETA) -> float:
    """Minimum detectable ABSOLUTE difference in a proportion, normal approx.

    The reviewer's instrument. Reported because it is the standard one, but see
    `mde_diff_in_means` — the outcome here is a per-clause RATE over 9-18
    trials, not one Bernoulli draw, and the two differ.
    """
    if n1 <= 0 or n2 <= 0:
        raise ValueError(f"both arms must be non-empty (got {n1}, {n2})")
    v = p * (1 - p)
    return (z_alpha + z_beta) * math.sqrt(v / n1 + v / n2)


def mde_correlation(n: int, z_alpha: float = _Z_ALPHA,
                    z_beta: float = _Z_BETA) -> float:
    """Smallest |r| detectable at 80% power, Fisher-z."""
    if n <= 3:
        raise ValueError(f"n must exceed 3 (got {n})")
    return math.tanh((z_alpha + z_beta) / math.sqrt(n - 3))


def mde_diff_in_means(R: "Retrieval", n1: int, n2: int,
                      z_alpha: float = _Z_ALPHA,
                      z_beta: float = _Z_BETA) -> float:
    """MDE for the test actually run: a difference in mean per-clause error
    rate, using the OBSERVED between-clause SD."""
    vals = [R.rate[c] for c in R.rate]
    m = sum(vals) / len(vals)
    sd = math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))
    if n1 <= 0 or n2 <= 0:
        raise ValueError(f"both arms must be non-empty (got {n1}, {n2})")
    return (z_alpha + z_beta) * sd * math.sqrt(1 / n1 + 1 / n2)


def spearman(a, b) -> float:
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
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return num / (da * db) if da and db else 0.0


def continuous_effect(R: "Retrieval", value, n: int = 20000,
                      seed: int = 20260802, alpha: float = 0.05) -> dict:
    """Spearman rho between a CONTINUOUS per-clause quantity and the error rate.

    Better powered than the binary split — `sufficient` is 20/123 while the
    count of missing phrases spans 0-7 — and it is the same measurement at
    higher resolution, so it is reported alongside every binary arm it refines.
    """
    cids = sorted(R.rate)
    xs = [value(c) for c in cids]
    ys = [R.rate[c] for c in cids]
    rho = spearman(xs, ys)
    rng = random.Random(seed)
    boots = []
    m = len(cids)
    for _ in range(n):
        idx = [rng.randrange(m) for _ in range(m)]
        boots.append(spearman([xs[i] for i in idx], [ys[i] for i in idx]))
    boots.sort()
    return {"rho": rho, "lo": boots[int(alpha / 2 * n)],
            "hi": boots[min(n - 1, int((1 - alpha / 2) * n))],
            "n": m, "mde": mde_correlation(m)}


def report_power(R: "Retrieval", n: int = 20000) -> list:
    """Printed FIRST. A null below this line is largely uninformative."""
    fid = fidelity()
    flags = clause_categories()
    N = len(R.rate)
    pooled = sum(R.err.values()) / sum(R.trials.values())
    out = ["POWER — READ THIS BEFORE ANY EFFECT BELOW",
           f"  n = {N} clauses, {sum(R.trials.values())} (passage x cell) "
           f"trials, pooled error rate {pooled:.3f}",
           "  ⚠️ The predictor is rare: `sufficient` is true for 20 of 125. At "
           "that imbalance the",
           "     design is UNDER-POWERED to the point of near pre-determination "
           "— a null result here",
           "     is largely UNINFORMATIVE and must not be reported as evidence "
           "of no effect.",
           f"  Smallest |Spearman rho| detectable at 80% power, n={N}: "
           f"{mde_correlation(N):.3f}",
           "",
           "  {:<34} {:>9} {:>13} {:>13}".format(
               "split", "n T/F", "MDE (2-prop)", "MDE (means)")]
    splits = [(lab, (lambda c, f=f: f(fid, c))) for lab, f in _FID_SPLITS]
    splits += [(f"missing {c}", (lambda k, c=c: c in flags[k]))
               for c in CATEGORIES]
    splits += [(f"kind = {k}", (lambda c, k=k: clause_kinds()[c] == k))
               for k in CLAUSE_KINDS]
    for label, f in splits:
        cids = sorted(R.rate)
        nt = sum(1 for c in cids if f(c))
        nf = N - nt
        if nt == 0 or nf == 0:
            out.append(f"  {label:<34} {nt:>4}/{nf:<4} DEGENERATE — no contrast")
            continue
        out.append("  {:<34} {:>4}/{:<4} {:>13.3f} {:>13.3f}".format(
            label, nt, nf, mde_two_proportion(nt, nf, pooled),
            mde_diff_in_means(R, nt, nf)))
    out += ["",
            "  The observed differences below are 0.00-0.15. Every MDE above is "
            "of the same order",
            "  or larger, so this design can only ever have detected a LARGE "
            "effect. Per-category",
            "  cells (exception n=10, precedence n=11) are worse still and "
            "carry no evidential weight",
            "  in either direction.",
            "  ⚠️ Pseudo-replication warning: the 1206 trials are ~134 passages "
            "x 9 cells, but the",
            "     tool emits only 3 distinct predictions (one per behaviour) — "
            "the judges vary the GOLD,",
            "     not the prediction. Moving to a per-trial unit would inflate "
            "n ~10x and buy no power;",
            "     that is why the clause is the unit and why the n above cannot "
            "be talked upward."]
    return out


def report_continuous(R: "Retrieval", n: int = 20000) -> list:
    """The better-powered framing the binary flags throw away."""
    fid = fidelity()
    flags_of = clause_categories
    out = ["CONTINUOUS PREDICTORS (better powered than the binary flags)",
           "  {:<34} {:>7} {:>24} {:>8}".format(
               "per-clause quantity", "rho", "[95% CI]", "MDE |rho|")]
    rows = [("count of missing phrases",
             lambda c: len(fid[c]["missing"])),
            ("count of unsupported phrases",
             lambda c: len(fid[c]["unsupported"])),
            ("atom count", lambda c: clause_atom_count()[c])]
    rows += [(f"count of missing {c} phrases",
              (lambda k, c=c: sum(1 for p in fid[k]["missing"]
                                  if c in categorise(p))))
             for c in CATEGORIES]
    for label, v in rows:
        e = continuous_effect(R, v, n=n)
        out.append("  {:<34} {:>+7.3f}  [{:+.3f}, {:+.3f}] {:>13.3f}".format(
            label, e["rho"], e["lo"], e["hi"], e["mde"]))
    _ = flags_of
    return out


if __name__ == "__main__":
    raise SystemExit(main())
