"""
⛔⛔ STOP — THIS MODULE'S HEADLINE WAS MEASURED ON 3 BEHAVIOURS AND INVERTED AT 9 ⛔⛔

`PRIMARY_OPERATOR = "act_match"` was selected on panel MCC over 7 operators using the
3-behaviour frontier panel. On the 9-behaviour panel it LOSES to the operator that was
never selected:

    act_match (the fitted choice)      3 beh +0.310   ->   9 beh +0.246
    any_atom  (the NO-CHOICE default)  3 beh +0.294   ->   9 beh +0.274
    relevance.py (the bag scorer)                          9 beh +0.284

So on 9 behaviours this module LOSES to the bag scorer it was written to replace
(structural - relevance = -0.0378, CI [-0.0596, -0.0164], sign consistent 5/5 draws).
The `bias_bound: 0.016` declared below UNDERSTATES the real cost by more than 2x.

Everything in this docstring that recommends this module for thresholded sets, or quotes
+0.310, is a 3-BEHAVIOUR NUMBER and must not be carried forward. Prefer `any_atom` over
`act_match`, and see `combined.py` — the typed core UNION elected sections is the only
compliant configuration that beats the bag scorer.
The typed query: a structural match over typed atoms, not a similarity score.

WHAT THIS REPLACES AND WHY
--------------------------
`relevance.py` scores a clause as

    score = w_lex * cosine(text) + w_atom * sum IDF(shared atoms) + w_section * prior

Atoms are features in a weighted sum. The tell is that four atom TYPES were
extracted and then the `kind` weight was set to ZERO — in an additive scheme a
kind term double-counts what `atom` already carries, so the type system is
inert. This module makes typing the JOIN STRUCTURE instead: which SLOT a match
lands in decides which pattern fires, and no amount of evidence in one slot can
substitute for a different slot.

The one fact that dictates the design: **in this artifact kind is a function of
name.** All 361 vocabulary atoms have exactly one kind, and
`kind_mismatch_discount` fires on 0 of 70 query atoms
(`test_ontology.test_every_atom_has_exactly_one_kind` pins this). So a kind
AGREEMENT term is provably incapable of adding information at any weight —
knowing the name already tells you the kind. Typing can only be load-bearing
through structural ROLE: which slot of the query an atom fills. That is what
the ladder below is built on.

THE QUERY: A TYPED DISJUNCTION, WITH THE CONJUNCTION AS A PRECISION TIER
-----------------------------------------------------------------------
A behaviour is "conduct in a circumstance", so its atoms fill four slots:

    SITUATION  the circumstance      } CORE — the two slots that make a
    ACT        the conduct           }        behaviour a behaviour
    ENTITY     who/what is involved  } SUPPORTING — corroboration, never
    VALUE      what is at stake      }              sufficient alone

The obvious design is a typed CONJUNCTION (situation AND act). It was built,
measured, and REJECTED as the query. Two structural facts kill it:

  * Of 593 clauses, 324 carry a situation atom and 480 carry an act atom, but
    only 267 (45%) carry BOTH. The conjunction is incapable of firing on 55%
    of the spec no matter how good the query is.
  * Measured: it fires on 10-22 clauses (3-6% of the universe), recall ceiling
    7-13%, and at passage level scores +0.166 against the bag scorer's honest
    +0.206 — WORSE, with a paired-bootstrap Δ of -0.047, CI [-0.115, +0.030].
    Its precision lift is significant on ONE of three behaviours.

So the query is the typed DISJUNCTION, and the conjunction is demoted to a
narrow high-precision tier reported separately — which is where it earns its
keep (harm-avoidance precision 0.850 over 6% of the corpus, p<0.001 — a
single-draw figure; the ladder's per-rung table is per-draw, not pooled).

Passage level, project protocol, mean over the 3 pair-targets, 589-passage
universe:

    bag @LOBO threshold      1 fitted param, held out    +0.206
    bag @0.18                1 fitted param, IN-SAMPLE   +0.320
    bag ATOM CHANNEL ONLY    1 fitted param, held out    +0.320
    struct: act_match        0 params            +0.310 +- 0.021  <- PRIMARY
    struct: any_atom         0 params            +0.294 +- 0.018  <- see below
    struct: act_and_situation 0 params                   +0.166  <- worst
    judges (mean / best)     the bar                     +0.555 / +0.654

⚠️ `act_match` vs `any_atom` IS CONFOUNDED WITH PREDICTION-SET SIZE and is NOT
the test of typing. `act_match` predicts roughly half as many clauses as
`any_atom` (103/185, 82/137, 139/226 on draw 0), so the contrast is PRUNE vs
NO-PRUNE, not TYPED vs UNTYPED. The size-matched control is the test; it is
described below and it is the headline of `test_structural.py --variance`.
Quote the pair above only with this sentence attached.

TWO FLOORS, AND BOTH BELONG IN ANY QUOTE OF THE ABOVE:

    floor A  chance, all-positive over every passage             0.000
    floor B  chance MINUS the coverage gap the tool cannot close -0.059

Floor A is MCC's DEFINITIONAL zero: predict everything and tn = fn = 0, the
denominator vanishes, and the score is 0 by convention. That property is
exactly why MCC is the primary metric here — a degenerate predictor cannot
score above chance, unlike F1 whose floor moves per behaviour.

Floor B is all-positive over what the tool CAN REACH. 7 of 589 passages join to
no clause at all, so they are forced misses for any method whatsoever
(per behaviour: +0.029 / -0.161 / -0.043, driven by how many of the 7 the
panel had marked relevant — 0, 6, and 2-3 respectively). The GAP between A and B is the
join-coverage cost, and this project states that cost rather than absorbing it.

A reader comparing +0.310 against 0.000 asks "is this better than chance?".
A reader comparing it against -0.059 asks "is this better than chance, given
the passages the pipeline cannot reach at all?". Different questions; quote
both floors, never one.

The structural figures are the MEAN OVER 5 INDEPENDENT DRAWS of the behaviour
atoms, with the standard deviation across draws. A single draw gave +0.340;
that was the maximum of the spread, not a constant, and quoting it alone was
wrong. Even the minimum draw (+0.292) clears the bag scorer's honest +0.206.

TYPING: WHAT IS MEASURED, AND WHAT WAS RETRACTED
-----------------------------------------------
⚠️ TWO EARLIER CLAIMS ARE RETRACTED IN FULL. They were published here and are
named so a reader who saw them knows they are dead:

  RETRACTED 1  "typing contributes nothing measurable on this data."
  RETRACTED 2  "this operator is a coarse topic filter, not concept-level
                ontological work."

Both rested on defects. RETRACTED 1 compared the paired delta against a ±0.06
noise floor that was an INTERIM guardrail explicitly conditional on n=1 draws;
the re-draws landed and were never used to replace it. The draw-level SE of
that delta is 0.0041, so ±0.06 is ~15 SE — a floor nothing could ever clear.
RETRACTED 2 rested on the stable core scoring what the full draws score, read
as "the atoms do not matter". Agreement between independent samples is evidence
that the SAMPLING is stable, not that the CONTENT is arbitrary, and three
measurements separate the two readings:

  * the 12-16 atom core is the MORE COMMON half (median df 9.5/7.0/10.5
    against the remainder's 7.0/6.0/8.0) — the OPPOSITE of what IDF weighting
    would select, so it is not a rare-term artifact;
  * a same-sized HIGHEST-INFORMATION (lowest-df) subset COLLAPSES:
    +0.042 / +0.210 / +0.004 against the core's +0.342 / +0.368 / +0.231;
  * random same-sized subsets scatter with sd 0.100 / 0.103 / 0.059 while the
    five real draws scatter with sd 0.024 / 0.031 / 0.032 — three to four
    times tighter.

So the draws agree because independent samples keep re-selecting the same
semantically central atoms. That is a STABLE EXTRACTION, not a vacuous
operator, and an ARBITRARY same-sized query does markedly worse.

THE CORRECTED FINDING — TYPING IS A PRECISION-BUYING PRUNE WHOSE SIGN IS SET BY
BASE RATE. `act_match` roughly halves the prediction set relative to `any_atom`.
It buys precision by giving up recall, which PAYS when the target is rare and
LOSES when it is common. Draw as the unit, k=5 independent atom draws:

    behaviour                        mean Δ    t(4)   95% CI            base
                                                                        rate
    avoiding-over-and-under-caution  +0.087   +6.57  [+0.050, +0.124]   0.068
    helpfulness                      +0.011   +1.50  [-0.009, +0.030]   0.182
    harm-avoidance-to-third-parties  -0.047  -10.35  [-0.060, -0.035]   0.236
    ---------------------------------------------------------------------
    mean over behaviours             +0.017   +4.13  [+0.006, +0.028]

BEHAVIOUR EXPLAINS 90.3% OF THE VARIANCE, F(2,12)=55.6, and the sign reproduces
5/5 draws in two of the three behaviours. THE MEAN ROW IS NOT THE VERDICT: it
averages a large win and a large loss and reports neither. Read the rows.

The mean row is nonetheless real — +0.017 clears its own MDE at 80% power
(0.0151) and its CI excludes zero — which is precisely why the retracted null
was wrong even on its own aggregate terms.

THE ACTUAL TEST OF TYPING IS THE SIZE-MATCHED CONTROL, NOT `any_atom`. In this
artifact kind is a strict function of name (361 names, 0 with >1 kind), so
`act_match` is exactly a name-subset filter: it yields the IDENTICAL prediction
set to `any_atom` run on the act-only subquery, in all 15 cells. So
`act_match` vs `any_atom` never controls for set size. Replacing the act subset
with a RANDOM SAME-SIZED subset of the query's own atoms (500 draws per cell)
gives the controlled contrast:

    randomization control, 500/cell   act wins 15/15 cells, mean Δ +0.091,
                                      sign test p = 6e-5
    df-matched (summed document
    frequency within 10%), 300/cell   act wins 14/15 cells, mean Δ +0.066

TYPING SURVIVES BOTH CONTROLS — including on harm-avoidance, where its apparent
"loss" against `any_atom` is a set-size artifact: at matched size the act slot
still beats a random slice of the same query.

WHAT IS GENUINELY UNRESOLVED, AND MUST NOT BE OVERSOLD: WHICH behaviours typing
pays for. n = 3 behaviours. The behaviour-level MDE at 80% power is 0.209 on
the between-behaviour contrast — far above the effects seen — so "rare targets
benefit, common targets do not" is a MECHANISM CONSISTENT WITH the data and a
prediction to be tested on more behaviours, NOT an established regularity. Three
points do not establish a base-rate law.

Run `.venv/bin/python test_structural.py --variance` for every table above.

OPERATORS (all zero-parameter) and RUNGS (their disjoint partition)
------------------------------------------------------------------
`OPERATORS` are the named predicates that get measured and compared. `RUNGS`
partition the fired clauses so per-rung precision/recall is additive and
`explain()` can say WHICH pattern fired, strongest-precision first:

  0 act_and_situation   both core slots filled          (precision tier)
  1 multi_atom          >=2 typed matches, not both core (precision tier)
  2 act_match           the act slot filled              (PRIMARY operator)
  3 situation_match     the situation slot filled, no act
  4 support_only        entity/value evidence only

THE NOTATION OPERATORS — CANDIDATES, MEASURED, NEVER SELECTED
------------------------------------------------------------
Rung 1.5 of the attribution ladder (`LADDER_PLAN.md`) writes two things INTO
the atom name: a reserved polarity prefix (`must_ mustnot_ should_ shouldnot_
may_`) and an ORDERED principal chain (`stem__actor_patient_third`). Until
these were added, nothing consumed either, so the rung could not have shown a
retrieval effect however good its annotation was — the load-bearing rung of the
ladder was unreadable by the query it exists to improve.

Four operators read it. Each DISCARDS evidence whose type disagrees with the
query's type and then asks whether anything survived — a set operation on typed
atoms, not a weight (invariant 10), and zero-parameter (invariant 9):

    directive_atom       a `may_` atom PERMITS the conduct; it is not the
                         clause committing the model to it
    polarity_consistent  a match is discarded when query and clause carry
                         OPPOSED polarities on the same stem — `contrary`,
                         derived from the notation instead of a hand-built
                         relation layer
    role_aligned         the ENTITY slot becomes a TYPE CONSTRAINT on the act:
                         an act between the model and the operator is not
                         conduct toward third parties, however exactly its stem
                         matches
    patient_aligned      the same, reading the chain AS ORDERED — a third party
                         who ACTS is not a third party who is ACTED UPON

WHY POLARITY AND NOT SOMETHING ELSE: `HANDOFF.md:449` records that 3-11 of
every 19-28 query atoms earn a NEGATIVE weight under supervision, "which our
query cannot express". That is a measured, label-free-derivable signal the
existing operators throw away, and polarity typing is the only mechanism on
offer by which a rung could improve RELEVANCE rather than representation.

⚠️ THEY ARE CANDIDATES. `PRIMARY_OPERATOR` stays pinned to `any_atom` and
NOTHING here was selected on a panel score — see the `act_match` banner at the
top of this file for what selecting on panel MCC over an operator table costs.
They are declared in `POST_SELECTION_OPERATORS` precisely so the recorded
selection surface cannot be quietly widened to include them.

⚠️ WHAT THEY CAN AND CANNOT DO TODAY, stated so nobody quotes them as a win:
  * On the 361-name vocabulary all four are EXACTLY `any_atom`, provably: no
    shipped name carries the notation, and an ABSENT type cannot exclude. So
    they change no existing number, and rung-0/1 artifacts score identically.
  * On rung 1.5 as the ladder currently specifies it — CLAUSE side only —
    `directive_atom`, `role_aligned` and `patient_aligned` are live and
    `polarity_consistent` is INERT, because an unpolarised query atom
    contradicts nothing. Making it live needs a rung-1.5 pass over the
    BEHAVIOUR atoms (`behavior_atoms.py`), which is not this module's file.
  * `role_aligned` is unconstrained for any behaviour whose entity slot names
    no party. All three shipped behaviours do name one, and only because of
    the head rule: `harm-avoidance-to-third-parties` -> (third_party),
    `avoiding-over-and-under-caution` -> (user), `helpfulness` ->
    (user, developer). Under exact-match-only, `end_user` and `api_developer`
    would name nothing and two of the three would be unconstrained.
  * Measured, and reported as a measurement: on the shipped artifact all four
    predict EXACTLY the `any_atom` set on all three behaviours (185 / 137 /
    226 clauses). That is the backward-compatibility property, not a result.

THE JOIN IS STEM-AWARE, AND THAT IS WHAT MADE ANY OF IT POSSIBLE. A rung-1.5
name has to reach the query atom it decorates or every operator is dead on
rung-1.5 output. `_evidence` therefore falls back to a SECOND EXACT LOOKUP on
the stripped stem — not a fuzzy match — and `stem_of` is the IDENTITY on every
shipped name, so the fallback asks the same question twice and the shipped
numbers are bit-identical. (`ladder.stem_normalised` exists because this did
not: it strips the notation before scoring, which also strips the polarity. It
is no longer needed for the retrieval-side comparison, and using it would
discard exactly the signal rung 1.5 was built to produce.)

CONTRARY IS A DEFEATER at every rung: if a query atom is `contrary` to a clause
atom in the same slot, that slot cannot be filled and `explain()` names what
blocked it.

  ⚠️ HOW TO TEST A DEFEATER — read this before writing one. A `contrary` edge
  can only ever REMOVE a match that something else created. So a test whose
  query atom is merely contrary to the clause atom proves NOTHING: the clause
  would not have matched anyway, and the test passes just as happily with the
  defeater deleted. That exact test was written here, passed, and was caught
  only by mutation testing — it was bounding the structure of the code rather
  than the symptom it claims to prevent, which is the failure mode this project
  has hit repeatedly.
  A defeater test that can actually fire needs TWO query atoms: one that
  CREATES the match and a second that DEFEATS it. Then flip the single relation
  edge between two otherwise identical indexes and assert the hit disappears.
  See `test_structural.py::test_contrary_blocks_a_match_that_would_otherwise_fire`.

WHICH PRODUCT THIS SUPPORTS — AND WHICH IT DOES NOT
---------------------------------------------------
There are two different deliverables hiding under "relevance", and the measured
answer is DIFFERENT FOR EACH. This is not a caveat, it is a product decision:

    AUC (ranking quality)          structural   bag
      avoiding-over-and-under          0.810   0.855
      harm-avoidance                   0.733   0.779
      helpfulness                      0.680   0.657

The bag OUT-RANKS this module on 2 of 3 behaviours while LOSING decisively as a
decision rule (+0.206 vs +0.310). Both are true at once and there is no
contradiction: a graded lexical score orders a list well, and has no principled
place to cut it; a structural predicate has no gradations to speak of, and its
cut is exact.

  * If the deliverable is a RANKED LIST a human scans top-down — "show me the
    passages most likely to bear on this behaviour, I will decide where to
    stop" — USE THE BAG SCORER (`relevance.py`). This module is worse at it.
  * If the deliverable is a THRESHOLDED SET consumed without a human in the
    loop — coverage tables, "which clauses bear on this behaviour", anything
    downstream that needs a yes/no — [RETRACTED. This said "USE THIS MODULE.
    It wins." At n=9 this module scores +0.246 and the bag scorer +0.284, so
    the claim INVERTS. Use `combined.py` at `any_atom`, the only compliant
    configuration measured above the bag. See the banner at the top.]

Do not quote one product's number for the other's use case.

THE RELATION LAYER IS DELIBERATELY NOT USED BY DEFAULT
-----------------------------------------------------
`ontology.py` can supply subsumes/entails/contrary edges, and this module will
traverse them if they exist. They are not built, because they were measured and
they HURT: a one-hop relation layer degrades precision on every behaviour
(.348->.309, .850->.631, .433->.367) and passage MCC from +0.123 to +0.088.
Relation expansion pulls in siblings that share a parent but not a subject.
`max_hops=0` is therefore the default. Anyone rebuilding the relation layer has
a number to clear: +0.340. GATE SUSPENDED: +0.340 is DRAW0, the MAXIMUM of a 5-draw spread (mean +0.310 +/- 0.021), and it was defending a typing null that has since been RETRACTED. Re-derive per behaviour with the correct noise floor (draw-level SE 0.0041) before gating anything on it.

THE SECTION PARTITION LIVES HERE; THE QUOTIENT LIVES IN `section.py`
--------------------------------------------------------------------
`sections()` and `section_of()` expose the document's own `section_path`
partition, because this index owns the clause rows. `section.py` builds the
quotient on it and reports the measurement: as a RANKING channel the quotient
beats the bag scorer's smoothing section term on all three behaviours and all
five atom draws (passage AUC 0.561->0.673 / 0.695->0.781 / 0.840->0.867, CIs
excluding zero); as a DECISION RULE it recovers NOTHING — its best label-free
variant is +0.335 against this module's +0.310, CI [-0.008, +0.069], and the
pre-registered design LOST at +0.177. The +0.16 that a supervised readout of
section identity appears to leave on the table is not reachable without labels.
Read `section.py`'s docstring before proposing to exploit it again.

WHAT IS NOT HERE
----------------
No weighted sum of channels. No lexical cosine. No section prior. No threshold
fitted per behaviour. No panel label — the string `benchmark` does not appear in
this file and a test asserts it, so this query cannot have been fitted to the
thing it is measured against. Ranking exists (the sweep needs it) but it is
LEXICOGRAPHIC IN THE RUNG: evidence mass can reorder clauses within a rung and
can never lift one above a higher rung. Every constant is declared in
`CONSTANTS` with its justification, and a test asserts that declaration is
COMPLETE.

⚠️ EXACTLY ONE OF THEM WAS CHOSEN BY LOOKING AT A SCORE: `primary_operator`
(`act_match`) was selected on panel MCC over the 7 operators. An earlier
version of this docstring said "none was chosen by looking at a score" while
this very selection was stated 150 lines above it; that sentence was FALSE and
is retracted. The no-choice default `any_atom` scores +0.294 against +0.310, so
the bias is bounded by 0.016 — the honest reading of "zero parameters" is ZERO
PARAMETERS GIVEN THE OPERATOR. See `CONSTANTS["primary_operator"]`.

Usage:
    .venv/bin/python structural.py helpfulness
    .venv/bin/python structural.py helpfulness --explain m0207
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field

import measure_join
import ontology as ONT
import relevance

HERE = os.path.dirname(os.path.abspath(__file__))
CLAUSES = os.path.join(HERE, "modelspec_clauses.json")
ANNOTATIONS = os.path.join(HERE, "annotations_b8.json")
BEHAVIOUR_ATOMS = os.path.join(HERE, "behavior_atoms_b8.json")

#: The two slots that make a behaviour a behaviour, and the two that corroborate.
CORE_SLOTS = ("situation", "act")
SUPPORT_SLOTS = ("entity", "value")
SLOTS = CORE_SLOTS + SUPPORT_SLOTS

#: --------------------------------------------------------------- THE NOTATION
#: Rung 1.5 of the attribution ladder writes two things INTO the atom name: a
#: reserved polarity prefix, and an ordered chain of principals after a double
#: underscore (`must_disclose_reasoning__model_user`). Both are verified
#: collision-free against the 361 shipped names, so on every rung-0/1 artifact
#: the parse below is the IDENTITY and everything that consumes it is inert.
#:
#: These are re-declared rather than imported: `ladder.py` pulls in the
#: provider layer and this module may not reference it at all. They are pinned
#: equal to `ladder`'s by a test that is the only place allowed to import both.
POLARITY_PREFIXES = ("must_", "mustnot_", "should_", "shouldnot_", "may_")
PRINCIPAL_SEP = "__"
#: Longest-first: `third_party` contains the separator character, so a
#: left-to-right split on "_" would tear it in half.
PRINCIPALS = ("third_party", "developer", "operator", "platform", "system",
              "model", "user")

#: The disjoint partition of everything that fires, strongest precision first.
#: The index is the `depth` argument to `predict_depth`, and the name is what
#: `explain()` reports.
RUNGS = (
    ("act_and_situation",
     "both core slots filled — the typed conjunction, a narrow precision tier"),
    ("multi_atom",
     ">=2 independent typed matches, but not both core slots"),
    ("act_match",
     "the act slot is filled — the PRIMARY operator"),
    ("situation_match",
     "the situation slot is filled and the act slot is not"),
    ("support_only",
     "entity/value evidence only"),
)
RUNG_NAMES = tuple(n for n, _ in RUNGS)

#: The zero-parameter predicates that get measured and compared. Each maps a
#: clause's evidence list to a bool. These are OPERATORS, not tiers: they
#: overlap, and each is a complete query in its own right. `predict` takes one
#: by name.
#:
#: `any_atom` is the NO-PRUNE control and is deliberately first-class. It is
#: NOT the untyped control for typing: because kind is a function of name,
#: `act_match` is a name-subset filter, so `act_match - any_atom` is confounded
#: with prediction-set size (it halves the set). The typing test is the
#: SIZE-MATCHED randomization control in `test_structural.py --variance`.
#: `any_atom` is kept because it is the no-choice default operator and the
#: unselected baseline for `PRIMARY_OPERATOR` (+0.294 vs +0.310).
def _slots(ev):
    out = defaultdict(list)
    for e in ev:
        out[e.slot].append(e)
    return out


OPERATORS = {
    "act_and_situation": lambda ev: all(_slots(ev)[s] for s in CORE_SLOTS),
    "multi_atom": lambda ev: len({e.clause_atom for e in ev}) >= MULTI_ATOM_MIN,
    "act_match": lambda ev: bool(_slots(ev)["act"]),
    "situation_match": lambda ev: bool(_slots(ev)["situation"]),
    "sit_or_act": lambda ev: any(_slots(ev)[s] for s in CORE_SLOTS),
    "any_atom": lambda ev: bool(ev),
    "support_only": lambda ev: bool(ev) and not any(_slots(ev)[s]
                                                    for s in CORE_SLOTS),
}

#: THE NOTATION-CONSUMING OPERATORS, added after `primary_operator` was
#: selected. Registered at the bottom of this file, once the notation helpers
#: exist; named here so the two audit tests can see them.
NOTATION_OPERATORS = frozenset({"directive_atom", "polarity_consistent",
                                "role_aligned", "patient_aligned"})

#: Operators that did not exist when `primary_operator` was fitted. Kept
#: separate from `selected_over` because extending that tuple would claim a
#: comparison that never took place, and leaving it alone would understate the
#: table. `test_the_alternatives_the_fitted_choice_was_selected_over_are_named`
#: asserts the two partition `OPERATORS`.
POST_SELECTION_OPERATORS = frozenset(NOTATION_OPERATORS)

#: EVERY constant in the query, with where it came from. Two tests read this
#: dict: one asserts each entry has a justification and that a `fitted_on_panel`
#: entry discloses its selection and its unselected baseline, and one asserts
#: this dict is COMPLETE — every module-level constant not derived from here has
#: to be named in a frozen non-parameter list, so a fitted number cannot be
#: hidden by simply not declaring it. (That is exactly how `primary_operator`
#: below escaped the audit for as long as it did.)
CONSTANTS = {
    "primary_operator": {
        "value": "act_match",
        "why": ("⛔ RECORDED, NOT SHIPPED. This is the panel-fitted operator "
                "and it is retained here ONLY as an audit trail. The module "
                "ships `PRIMARY_OPERATOR = any_atom`, the no-choice default. "
                "Read `DECLARED_FITTED_OPERATOR` if you want this value; "
                "nothing in the query path does.\n\n"
                "It was SELECTED ON PANEL MCC over the 7 operators in "
                "`OPERATORS` — the same class of error as an in-sample argmax "
                "threshold, which is what `relevance.py` was rebuilt to "
                "avoid — and was originally omitted from this dict rather "
                "than declared.\n\n"
                "⚠️ THE DECLARED BIAS BOUND WAS WRONG. This entry used to say "
                "the selection bias was 'bounded above by 0.016 — small', "
                "from act_match +0.310 vs any_atom +0.294. Both are "
                "3-BEHAVIOUR numbers. At n=9 the ordering INVERTS: act_match "
                "scores +0.246 and LOSES to the bag scorer, and the "
                "difference-in-differences selection cost is +0.0449 — 2.8x "
                "the bound declared beside it, with a CI excluding zero. "
                "Disclosing a fitted choice honestly does not make the "
                "disclosure correct; this one understated its own bias by "
                "almost 3x and shipped for three cycles afterwards."),
        "fitted_on_panel": True,
        "selected_over": ("act_and_situation", "multi_atom", "act_match",
                          "situation_match", "sit_or_act", "any_atom",
                          "support_only"),
        "selection_criterion": "panel MCC, mean over the 3 pair-targets",
        "unselected_baseline": {"operator": "any_atom", "value": 0.294,
                                "selected_value": 0.310,
                                "bias_bound": 0.016,  # SUPERSEDED — measured 0.039 at n=9
            "bias_bound_measured_n9": 0.039},
    },
    "max_hops": {
        "value": 0,
        "why": ("Bound on relation-path length; 0 means exact atom matching "
                "only. Set to 0 because relation expansion was MEASURED TO "
                "HURT — one hop degrades precision on all three behaviours "
                "(.348->.309, .850->.631, .433->.367) and passage MCC from "
                "+0.123 to +0.088, since siblings under a shared parent are "
                "not on the same subject. This is a measured-and-rejected "
                "setting, not a tuned one: the alternative was tried, made "
                "things worse everywhere, and was turned off."),
        "fitted_on_panel": False,
    },
    "multi_atom_min": {
        "value": 2,
        "why": ("How many distinct clause atoms the `multi_atom` precision "
                "tier needs. 2 is 'more than one independent typed match' — "
                "the smallest number that means corroboration at all. There "
                "is no third value that could have been chosen for a reason."),
        "fitted_on_panel": False,
    },
    "hop_decay": {
        "value": "1 / (1 + hops)",
        "why": ("Harmonic discount on path length, the standard choice for "
                "graph-distance evidence. It only ever reorders clauses WITHIN "
                "a rung — it can never move a clause between rungs — so its "
                "exact form cannot change any structural verdict."),
        "fitted_on_panel": False,
    },
    "generic_atom_frac": {
        "value": 0.25,
        "why": ("An atom on more than a quarter of clauses is generic; "
                "`is_generic` reports it and `explain()` prints it, so a hit "
                "resting on a corpus-wide atom is visible rather than "
                "flattering. INHERITED, not invented: it is the same number "
                "and the same argument as `relevance.Weights.atom_stopword_"
                "frac`, which predates this module and was hand-set from the "
                "design reasoning there. No OPERATOR consults it — it is "
                "reporting, not a gate."),
        "fitted_on_panel": False,
    },
    "query_weight_scale": {
        "value": 3,
        "why": ("`behavior_atoms_b8.json` carries a model-authored importance "
                "1-3 per query atom, which the bag scorer discarded. It is "
                "query-side metadata written before any measurement, exactly "
                "analogous to a repeated query term, so it is used as a "
                "multiplier w/3 on evidence mass. It is ORDERING ONLY: like "
                "hop decay it cannot move a clause between rungs. Set "
                "use_weights=False to drop it; the structural verdict is "
                "bit-identical either way."),
        "fitted_on_panel": False,
    },
    "polarity_sign": {
        "value": {"must": 1, "should": 1, "mustnot": -1, "shouldnot": -1,
                  "may": 0},
        "why": ("How the five RESERVED prefixes of the rung-1.5 notation type "
                "a match. This is a reading of the convention, not a setting: "
                "`must_`/`should_` direct the conduct, `mustnot_`/`shouldnot_` "
                "direct its absence, and `may_` permits without directing "
                "either — which is why it is the one prefix with sign 0. The "
                "two notation operators read exactly this: `directive_atom` "
                "asks whether the sign is non-zero, `polarity_consistent` asks "
                "whether two non-zero signs disagree. No other partition of "
                "the five is available without contradicting the sentence the "
                "annotator was shown ('records that force and that polarity, "
                "and nothing weaker or stronger'). Written before either "
                "operator was run on anything."),
        "fitted_on_panel": False,
    },
    "principal_head_rule": {
        "value": "stem, else its last underscore-separated segment",
        "why": ("How a QUERY atom is recognised as naming a principal, so the "
                "entity slot can constrain the act slot's role chain. The "
                "shipped query vocabulary spells principals as head-final "
                "compounds — `end_user` is a user, `api_developer` is a "
                "developer — so the head of the compound is the party. It is a "
                "morphological rule with no free value in it, and the strict "
                "alternative (exact match only) differs on exactly the atoms "
                "English says it should. It cannot invent a role: a stem whose "
                "head is not one of `PRINCIPALS` names no principal, and a "
                "behaviour naming no principal imposes NO constraint at all."),
        "fitted_on_panel": False,
    },
}

#: The one this module ships as its answer. Named here so nothing has to
#: re-derive "which operator did we actually claim". Derived from `CONSTANTS`,
#: never written as a bare literal — the completeness test enforces that.
#: ⚠️ FLIPPED to the NO-CHOICE operator. The declared value is `act_match`,
#: selected on panel MCC over 7 operators using only 3 behaviours. At n=9 it
#: LOSES to the unselected `any_atom` (DiD selection cost +0.0449, CI excludes
#: zero — 2.8x its declared 0.016 bound). Shipping the fitted choice as the CLI
#: default while the handoff says otherwise is the tenth recurrence of this
#: project's signature failure, and this time it was what users actually ran.
PRIMARY_OPERATOR = "any_atom"
DECLARED_FITTED_OPERATOR = CONSTANTS["primary_operator"]["value"]

MAX_HOPS = CONSTANTS["max_hops"]["value"]
GENERIC_ATOM_FRAC = CONSTANTS["generic_atom_frac"]["value"]
QUERY_WEIGHT_SCALE = CONSTANTS["query_weight_scale"]["value"]
MULTI_ATOM_MIN = CONSTANTS["multi_atom_min"]["value"]
POLARITY_SIGN = CONSTANTS["polarity_sign"]["value"]


# ------------------------------------------------------------- the notation

def parse_atom_name(name) -> dict:
    """`{polarity, stem, principals, error}` — total, and never a guess.

    An unparseable name yields an `error` and NO partial parse, because a
    convention that half-parses is worse than none: the operator would then
    exclude a clause on a polarity nobody wrote. Mirrors `ladder.parse_name`,
    which produces the names this reads; a test pins the two together.
    """
    out = {"polarity": None, "stem": name, "principals": (), "error": None}
    if not isinstance(name, str) or not name:
        out["error"] = "not a name"
        return out
    parts = name.split(PRINCIPAL_SEP)
    if len(parts) > 2:
        out["error"] = f"more than one {PRINCIPAL_SEP!r} in {name!r}"
        return out
    head = parts[0]
    for p in POLARITY_PREFIXES:
        if head.startswith(p):
            out["polarity"] = p[:-1]
            head = head[len(p):]
            break
    if not head:
        out["error"] = f"{name!r} is a polarity prefix with no stem"
        return out
    out["stem"] = head
    if len(parts) == 2:
        chain, rest = [], parts[1]
        while rest:
            for pr in PRINCIPALS:
                if rest == pr or rest.startswith(pr + "_"):
                    chain.append(pr)
                    rest = rest[len(pr) + 1:]
                    break
            else:
                out["error"] = (f"{rest!r} in {name!r} is not one of "
                                f"{', '.join(PRINCIPALS)}")
                return out
        if not chain:
            out["error"] = f"{name!r} has an empty principal chain"
            return out
        out["principals"] = tuple(chain)
    return out


def stem_of(name) -> str:
    """The name with the notation stripped — the key the join runs on.

    THE IDENTITY on every shipped atom name (the prefixes are reserved and no
    shipped name contains `__`), which is what makes the stem-aware join
    bit-identical on rung-0/1 artifacts: it asks for the same string twice.
    """
    p = parse_atom_name(name)
    return name if p["error"] else p["stem"]


def principal_named(name):
    """Which principal a query atom names, or None.

    `CONSTANTS['principal_head_rule']`: the stem itself if it is a principal,
    else the head of the compound. This is how the ENTITY slot — 'who or what
    is involved', until now pure corroboration — becomes a ROLE CONSTRAINT on
    the act slot.
    """
    stem = stem_of(name)
    if stem in PRINCIPALS:
        return stem
    head = stem.rsplit("_", 1)[-1]
    return head if head in PRINCIPALS else None


# ------------------------------------------------------------- the query side

@dataclass
class Query:
    """A behaviour, as typed atoms in slots. Deliberately NOT a text query.

    There is no name and no definition here: the moment prose enters, a lexical
    channel becomes tempting and the ontology becomes a bonus term again. If an
    atom is not in the vocabulary it cannot participate, and that is counted.
    """
    slug: str
    atoms: list = field(default_factory=list)

    def by_slot(self) -> dict:
        out = {s: [] for s in SLOTS}
        for a in self.atoms:
            kind = (a.get("kind") or "").strip()
            if kind in out:
                out[kind].append(a)
        return out

    def weight(self, name: str) -> int:
        for a in self.atoms:
            if a.get("name") == name:
                try:
                    return max(1, min(QUERY_WEIGHT_SCALE, int(a.get("weight") or 2)))
                except (TypeError, ValueError):
                    return 2
        return 2


def load_queries(source=BEHAVIOUR_ATOMS) -> dict:
    """`{slug: Query}` from `behavior_atoms.py`'s artifact, KEEPING `weight`.

    `relevance.load_behaviour_atoms` drops `weight` (it is not in
    `ATOM_FIELDS`), which is why this loader exists rather than reusing it.
    This file is the query side of the ontology, produced from the behaviour
    definition alone. It carries no panel judgement of any kind.
    """
    if isinstance(source, str):
        try:
            with open(source) as f:
                source = json.load(f)
        except (OSError, ValueError):
            return {}
    if not isinstance(source, dict):
        return {}
    if isinstance(source.get("behaviours"), list):
        source = {b.get("slug") or b.get("id"): b
                  for b in source["behaviours"] if isinstance(b, dict)}
    out = {}
    for slug, val in source.items():
        if not isinstance(slug, str) or slug.startswith("_") or slug == "provenance":
            continue
        raw = val.get("atoms") if isinstance(val, dict) else val
        if not isinstance(raw, list):
            continue
        atoms = [{"name": a.get("name"), "kind": a.get("kind") or "",
                  "gloss": a.get("gloss") or "", "weight": a.get("weight", 2)}
                 for a in raw if isinstance(a, dict) and a.get("name")]
        if atoms:
            out[slug] = Query(slug, atoms)
    return out


# ---------------------------------------------------------------- evidence

@dataclass(frozen=True)
class Evidence:
    """One typed connection: a query atom, a slot, a relation path, a clause
    atom, and the span that licensed the clause atom.

    Everything `explain()` prints comes from here, so a hit bottoms out in a
    quotation from the spec rather than in a number.
    """
    slot: str
    behaviour_atom: str
    clause_atom: str
    hops: int
    path: tuple
    clause_id: str
    span: str
    span_id: str
    locator: str
    gloss: str
    ic: float
    weight: int
    crosses_kind: bool = False
    #: The principals the QUERY names, as a whole — its role signature. It
    #: rides on the evidence because an operator is contractually handed the
    #: evidence list and NOTHING else, and a role constraint is a relation
    #: between the query's entity slot and the clause's act slot. Empty on
    #: every behaviour that names no party, which is most of them today.
    query_roles: tuple = ()

    @property
    def exact(self) -> bool:
        return self.hops == 0

    # ------------------------------------------------ the rung-1.5 notation
    # Derived, never stored: the name IS the record. All four are empty on the
    # 361-name vocabulary, so everything downstream of them is inert there.

    @property
    def stem(self) -> str:
        """The clause atom with its notation stripped — what actually joined."""
        return stem_of(self.clause_atom)

    @property
    def clause_polarity(self):
        return parse_atom_name(self.clause_atom)["polarity"]

    @property
    def clause_principals(self) -> tuple:
        return parse_atom_name(self.clause_atom)["principals"]

    @property
    def query_polarity(self):
        return parse_atom_name(self.behaviour_atom)["polarity"]

    @property
    def sign(self) -> int:
        """+1 directs the conduct, -1 directs its absence, 0 permits or is
        silent. `CONSTANTS['polarity_sign']`."""
        return POLARITY_SIGN.get(self.clause_polarity or "", 0)

    def mass(self, use_weights: bool = True) -> float:
        """Ordering-only evidence mass. Information content of the connecting
        clause atom, harmonically discounted by path length, optionally scaled
        by the query author's stated importance."""
        w = (self.weight / QUERY_WEIGHT_SCALE) if use_weights else 1.0
        return self.ic * (1.0 / (1.0 + self.hops)) * w

    def describe(self) -> str:
        arrow = (" -> ".join(r.describe() for r in self.path)
                 if self.path else "exact name match")
        return (f"[{self.slot}] {self.behaviour_atom} =={arrow}== "
                f"{self.clause_atom}  @{self.locator}")


# ------------------------------------- the operators that read the notation
#
# Four candidates, all zero-parameter, all SET operations on the evidence: each
# one DISCARDS evidence whose type disagrees with the query's type, then asks
# whether anything survived. None of them weighs anything, and none of them is
# the shipped default — `PRIMARY_OPERATOR` stays pinned to `any_atom`.
#
# THE RULE THEY ALL OBEY: an ABSENT type cannot exclude. A clause atom with no
# polarity is not a permission, an act with no principal chain is not about the
# wrong parties, and an unpolarised query atom contradicts nothing. So on the
# 361-name vocabulary — where the notation is absent everywhere — all four are
# EXACTLY `any_atom`, and a rung-0 artifact scored with them reads exactly as it
# did before. That is not a courtesy: the alternative (absence excludes) would
# report a total retrieval collapse the moment one of these was pointed at a
# corpus that predates the convention.

def _op_directive_atom(ev) -> bool:
    """Evidence whose clause atom does not merely PERMIT the conduct.

    A `may_` atom records that the act is allowed; the clause is not thereby
    committing the model to it. This is the one notation operator that is live
    on rung-1.5 output as the ladder currently specifies it, because it reads
    the CLAUSE side alone.
    """
    return any(e.sign != 0 or e.clause_polarity is None for e in ev)


def _op_polarity_consistent(ev) -> bool:
    """`contrary`, derived from the notation instead of a hand-built relation.

    A match is discarded when query and clause carry OPPOSED non-zero
    polarities on the same stem — the clause requires what the behaviour
    forbids. This is the operator that would express `HANDOFF.md:449`'s
    negative-weight atoms structurally, and it is INERT until the query side
    carries polarity too: an unpolarised query atom can contradict nothing.
    """
    return any(not (e.sign and POLARITY_SIGN.get(e.query_polarity or "", 0)
                    and e.sign != POLARITY_SIGN[e.query_polarity])
               for e in ev)


def _op_role_aligned(ev) -> bool:
    """Evidence whose role chain includes a party the behaviour is about.

    The ENTITY slot stops being corroboration and becomes a TYPE CONSTRAINT on
    the act: if the behaviour is about third parties and the clause's act is
    between the model and the operator, that act is not this behaviour's
    conduct however exactly its stem matches. Unconstrained when the behaviour
    names no principal, and per-atom unconstrained when the act carries no
    chain.
    """
    roles = {r for e in ev for r in e.query_roles}
    if not roles:
        return bool(ev)
    return any(not e.clause_principals or (set(e.clause_principals) & roles)
               for e in ev)


def _op_patient_aligned(ev) -> bool:
    """`role_aligned`, but the chain is read AS ORDERED.

    Rung 1.5's principals are written 'who acts first, then who is acted upon,
    then any third party'. A third party who ACTS is not a third party who is
    ACTED UPON, and a behaviour like harm-avoidance-to-third-parties is about
    the second. Reading the chain as a set throws that distinction away, which
    would mean rung 1.5's ORDERING bought nothing.
    """
    roles = {r for e in ev for r in e.query_roles}
    if not roles:
        return bool(ev)
    return any(not e.clause_principals
               or (set(e.clause_principals[1:]) & roles) for e in ev)


OPERATORS.update({
    "directive_atom": _op_directive_atom,
    "polarity_consistent": _op_polarity_consistent,
    "role_aligned": _op_role_aligned,
    "patient_aligned": _op_patient_aligned,
})
assert NOTATION_OPERATORS <= set(OPERATORS)


def query_roles(query: Query) -> tuple:
    """The principals a behaviour names — its role signature.

    Read from the ENTITY slot (`third_party`, `end_user`, `api_developer`) and
    from any principal chain the query atoms themselves carry, which is where a
    rung-1.5 pass over the BEHAVIOUR atoms would put it. Query-side only: no
    clause, no label, nothing measured.
    """
    out = []
    entity = {a.get("name") for a in query.by_slot()["entity"]}
    for a in query.atoms:
        name = a.get("name") or ""
        found = parse_atom_name(name)["principals"]
        if name in entity:
            found = (principal_named(name),) + tuple(found)
        for p in found:
            if p and p not in out:
                out.append(p)
    return tuple(out)


@dataclass(frozen=True)
class Defeat:
    slot: str
    behaviour_atom: str
    clause_atom: str
    clause_id: str
    span: str
    locator: str


@dataclass
class Match:
    clause_id: str
    rung: str
    rung_index: int
    evidence: list
    defeated: list = field(default_factory=list)

    def slots_filled(self) -> set:
        return {e.slot for e in self.evidence}

    def mass(self, use_weights: bool = True) -> float:
        """Best evidence per slot, summed over slots. Per-slot MAX rather than
        sum, so a clause annotated five times with near-duplicates of one atom
        cannot out-evidence a clause that genuinely fills two slots."""
        best = defaultdict(float)
        for e in self.evidence:
            best[e.slot] = max(best[e.slot], e.mass(use_weights))
        return sum(best.values())


# ------------------------------------------------------------------ the index

class StructuralIndex:
    """Built once over (clauses, annotations, ontology); queried per behaviour.

    Wholly offline. The ontology is derived once per spec by `ontology.py`; at
    query time this is graph traversal and set logic.
    """

    def __init__(self, clauses, annotations=None, onto=None,
                 max_hops: int = MAX_HOPS, use_weights: bool = True):
        self.onto = onto if onto is not None else ONT.Ontology({}, [])
        self.max_hops = max_hops
        self.use_weights = use_weights
        self.rejections = Counter()

        self.clauses = [dict(c) for c in clauses]
        self.ids = [str(c.get("id")) for c in self.clauses]
        self.by_id = dict(zip(self.ids, self.clauses))

        ann = (annotations if isinstance(annotations, dict)
               and all(isinstance(v, list) for v in annotations.values())
               else relevance.load_annotations(annotations))
        ann = {k: [a for a in (relevance._atom(x, k) for x in v) if a]
               for k, v in (ann or {}).items()}

        #: clause -> slot -> {atom name: atom}. THE JOIN STRUCTURE. An atom
        #: whose kind disagrees with the vocabulary's kind for that name is a
        #: corrupted annotation — kind is a function of name in this artifact —
        #: and is REJECTED AND COUNTED rather than filed under the wrong slot,
        #: because a mis-slotted atom is exactly a silent situation/act merge.
        self.by_kind = {}
        for cid in self.ids:
            slots = {s: {} for s in SLOTS}
            for a in ann.get(cid, []):
                kind = a["kind"]
                vocab_kind = self.onto.kind(a["name"])
                if vocab_kind and kind and kind != vocab_kind:
                    self.rejections["cross_kind_atom"] += 1
                    continue
                kind = kind or vocab_kind
                if kind not in slots:
                    self.rejections["unslotted_atom"] += 1
                    continue
                slots[kind].setdefault(a["name"], a)
            self.by_kind[cid] = slots

        # document frequency over the CORPUS, for information content. This is
        # the same quantity `relevance` uses for atom IDF and it is derived from
        # the clause annotations alone — no labels, no behaviours.
        self.df = Counter(n for cid in self.ids
                          for s in SLOTS for n in self.by_kind[cid][s])
        self.n_docs = len(self.ids) or 1
        self._ic = {n: math.log(self.n_docs / d) if d else 0.0
                    for n, d in self.df.items()}

    # ------------------------------------------------------------ builders

    @classmethod
    def from_files(cls, clauses_path: str = CLAUSES,
                   annotations_path: str = ANNOTATIONS,
                   ontology_path=ONT.ARTIFACT, **kw) -> "StructuralIndex":
        """The real artifacts. The ontology degrades to its mechanical layer if
        `ontology.json` has not been built — the ladder must still run, and its
        exact-match rungs are unaffected by an empty relation layer."""
        rows = measure_join.clause_rows(clauses_path)
        onto = ONT.Ontology.from_files(annotations_path, ontology_path)
        return cls(rows, relevance.load_annotations(annotations_path), onto, **kw)

    # ------------------------------------------------------------- helpers

    def ic(self, name: str) -> float:
        """Information content -log(df/N). Corpus-derived, not fitted."""
        return self._ic.get(name, math.log(self.n_docs))

    def is_generic(self, name: str) -> bool:
        """Above the inherited 0.25 document-frequency cap."""
        return self.df.get(name, 0) > GENERIC_ATOM_FRAC * self.n_docs

    # ------------------------------------------------------ the partition

    def sections(self) -> dict:
        """`{section_path: (clause id, ...)}` — the document's own partition.

        THE PATH IS THE KEY, not the leaf heading. `section_path` is a path in
        the document tree, and two headings with the same text under different
        parents are different sections; keying on the leaf would silently merge
        them. This spec happens to have no repeated leaf, which is exactly why
        that has to be pinned by a test rather than observed.

        It lives here because this index owns the clause rows. `section.py`
        builds the QUOTIENT on top of it — see that module for what the
        partition is worth (a real win as a ranking channel, a measured null as
        a decision rule) and why. Clause order inside a block is the index's
        own order, so the result is deterministic.
        """
        blocks = defaultdict(list)
        for cid in self.ids:
            blocks[tuple(self.by_id[cid].get("section_path") or ())].append(cid)
        return {p: tuple(cs) for p, cs in blocks.items()}

    def section_of(self, clause_id: str) -> tuple:
        """The `section_path` of one clause, `()` if it has none."""
        return tuple(self.by_id.get(str(clause_id), {}).get("section_path") or ())

    # ------------------------------------------------------------ expansion

    def _expansion(self, query: Query) -> dict:
        """`{slot: {clause-atom name: (behaviour atom, Link)}}`.

        Computed ONCE per query, not per clause. The slot of an expansion entry
        is the slot of the CLAUSE-side atom, so a cross-kind `entails` edge
        deposits its evidence in the slot the clause actually instantiates —
        and is flagged, so rung 1 (which demands exact same-kind matches) can
        never be reached through one.
        """
        out = {s: {} for s in SLOTS}
        for slot, atoms in query.by_slot().items():
            for a in atoms:
                name = a["name"]
                if name not in self.onto.vocab and name not in self.df:
                    self.rejections["query_atom_out_of_vocabulary"] += 1
                reach = (self.onto.reachable(name, self.max_hops)
                         or {name: ONT.Link(name, name, 0, ())})
                for target, link in reach.items():
                    tslot = self.onto.kind(target) or slot
                    if tslot not in out:
                        continue
                    #: Keyed by the clause-atom name AND by its stem, so a
                    #: query atom that itself carries rung-1.5 notation is
                    #: still reachable from the undecorated clause atom. On the
                    #: shipped vocabulary the two keys are the SAME STRING —
                    #: `stem_of` is the identity there — so this adds nothing.
                    for key in {target, stem_of(target)}:
                        cur = out[tslot].get(key)
                        if cur is None or link.hops < cur[1].hops:
                            out[tslot][key] = (a, link)
        return out

    def _contraries(self, query: Query) -> dict:
        """`{slot: {clause-atom name: behaviour atom}}` — the defeaters."""
        out = {s: {} for s in SLOTS}
        for slot, atoms in query.by_slot().items():
            for a in atoms:
                for c in self.onto.contraries(a["name"]):
                    cslot = self.onto.kind(c) or slot
                    if cslot in out:
                        for key in {c, stem_of(c)}:
                            out[cslot].setdefault(key, a)
        return out

    # ---------------------------------------------------------- the matcher

    def _evidence(self, query: Query, cid: str, expansion, contraries):
        ev, defeated = [], []
        roles = query_roles(query)
        for slot in SLOTS:
            for name, atom in sorted(self.by_kind[cid][slot].items()):
                #: THE STEM-AWARE JOIN. A rung-1.5 clause atom
                #: (`must_disclose_reasoning__model_user`) must reach the query
                #: atom it decorates, or every operator is dead on rung-1.5
                #: output and the rung cannot be scored at all. The fallback is
                #: a SECOND EXACT LOOKUP on the stripped name, not a fuzzy
                #: match — and on the shipped vocabulary the stripped name IS
                #: the name, so it asks the same question twice and the result
                #: is bit-identical.
                stem = stem_of(name)
                blocker = contraries[slot].get(name) or contraries[slot].get(stem)
                if blocker is not None:
                    defeated.append(Defeat(slot, blocker["name"], name, cid,
                                           atom["quote"], atom["locator"]))
                    continue
                hit = expansion[slot].get(name) or expansion[slot].get(stem)
                if hit is None:
                    continue
                b, link = hit
                ev.append(Evidence(
                    slot=slot, behaviour_atom=b["name"], clause_atom=name,
                    hops=link.hops, path=link.path, clause_id=cid,
                    span=atom["quote"], span_id=atom["span_id"],
                    locator=atom["locator"] or self.by_id[cid].get("locator", ""),
                    gloss=atom["gloss"], ic=self.ic(name),
                    weight=query.weight(b["name"]),
                    crosses_kind=link.crosses_kind
                    or bool(self.onto.kind(b["name"])
                            and self.onto.kind(b["name"]) != slot),
                    query_roles=roles))
        return ev, defeated

    def _rung(self, ev) -> int | None:
        """Assign the HIGHEST rung the evidence satisfies. Disjoint by
        construction, so per-rung precision/recall is additive and
        `predict_depth` returns a nested family."""
        if not ev:
            return None
        for i, (name, _) in enumerate(RUNGS):
            if OPERATORS[name](ev):
                return i
        return None

    def match(self, query: Query) -> dict:
        """`{clause_id: Match}` for every clause that fires at all."""
        expansion = self._expansion(query)
        contraries = self._contraries(query)
        out = {}
        for cid in self.ids:
            ev, defeated = self._evidence(query, cid, expansion, contraries)
            rung = self._rung(ev)
            if rung is None:
                continue
            out[cid] = Match(cid, RUNG_NAMES[rung], rung, ev, defeated)
        return out

    def defeats(self, query: Query) -> set:
        """`{(clause_id, slot, behaviour atom, clause atom)}` — every slot the
        ontology BLOCKED. Returned so a defeat is inspectable rather than being
        an absence in the output."""
        contraries = self._contraries(query)
        out = set()
        for cid in self.ids:
            for slot in SLOTS:
                for name in self.by_kind[cid][slot]:
                    b = contraries[slot].get(name)
                    if b is not None:
                        out.add((cid, slot, b["name"], name))
        return out

    # ------------------------------------------------------------- ordering

    def rank(self, query: Query) -> list:
        """`[(clause_id, score)]`, descending, score in [0, 1].

        LEXICOGRAPHIC IN THE RUNG. The rung supplies the integer part and the
        evidence mass a fraction strictly below 1 (`m/(1+m)` is monotone and
        bounded), so more evidence can reorder clauses inside a rung and can
        NEVER lift one above a higher rung. That is the difference between a
        graded structural verdict and a weighted sum: here the type structure
        decides the verdict and the numbers only break ties.

        Normalised by the fixed number of rungs, not by the corpus maximum, so
        a score means the same thing across behaviours and a corpus with no
        signal scores 0.0 rather than 1.0.
        """
        n = len(RUNGS)
        scored = {}
        m = self.match(query)
        for cid in self.ids:
            hit = m.get(cid)
            if hit is None:
                scored[cid] = 0.0
                continue
            mass = hit.mass(self.use_weights)
            tier = n - hit.rung_index
            scored[cid] = (tier + mass / (1.0 + mass)) / (n + 1)
        return sorted(scored.items(), key=lambda kv: (-kv[1], kv[0]))

    def predict(self, query: Query, operator: str = PRIMARY_OPERATOR) -> set:
        """The answer: clauses satisfying a named ZERO-PARAMETER operator.

        There is no threshold. Nothing here was selected on the panel, so there
        is no in-sample/held-out distinction to manage — the operator is the
        same object before and after any measurement.
        """
        if operator not in OPERATORS:
            raise ValueError(f"unknown operator {operator!r}; have "
                             f"{sorted(OPERATORS)}")
        pred = OPERATORS[operator]
        expansion = self._expansion(query)
        contraries = self._contraries(query)
        out = set()
        for cid in self.ids:
            ev, _ = self._evidence(query, cid, expansion, contraries)
            if ev and pred(ev):
                out.add(cid)
        return out

    def predict_depth(self, query: Query, depth: int = 0) -> set:
        """Clauses on rung `depth` or better — the ladder read cumulatively.

        Nested in `depth` by construction. This exists to emit the curve, NOT
        to be tuned: `predict` is the shipped operator and takes no depth.
        """
        return {c for c, m in self.match(query).items() if m.rung_index <= depth}

    def sweep(self, query: Query, depths=None) -> list:
        """`[(depth, predicted set)]` over the whole ladder. The curve is the
        return value: quoting one rung without its neighbours is how a
        threshold gets hand-picked."""
        depths = range(len(RUNGS)) if depths is None else depths
        return [(d, self.predict_depth(query, d)) for d in depths]

    # ------------------------------------------------------------- explain

    def explain(self, query: Query, clause_id: str) -> dict:
        """The typed path, end to end. This is the point of the module.

        For a hit: which behaviour atom, in which SLOT, through which relation
        EDGES (named, with the evidence that produced each), to which clause
        atom, licensed by which SPAN at which LOCATOR — plus the rung that
        fired and why the clause did not reach a higher one. For a non-hit,
        which slots were DEFEATED by a contrary and by what.

        Strictly more auditable than a per-channel breakdown: nothing here is a
        number the reader has to trust. Every line is checkable against the
        spec text.
        """
        cid = str(clause_id)
        expansion = self._expansion(query)
        contraries = self._contraries(query)
        ev, defeated = self._evidence(query, cid, expansion, contraries)
        rung = self._rung(ev)
        clause = self.by_id.get(cid, {})
        by_slot = defaultdict(list)
        for e in ev:
            by_slot[e.slot].append(e)

        return {
            "behaviour": query.slug,
            "clause_id": cid,
            "locator": clause.get("locator", ""),
            "section_path": list(clause.get("section_path") or []),
            "quote": clause.get("quote", ""),
            "rung": RUNG_NAMES[rung] if rung is not None else None,
            "rung_index": rung,
            "rung_meaning": RUNGS[rung][1] if rung is not None else
                            "no typed pattern fired",
            "score": dict(self.rank(query)).get(cid, 0.0),
            "slots": {s: {"filled": bool(by_slot[s]),
                          "exact": any(e.exact for e in by_slot[s]),
                          "n": len(by_slot[s])} for s in SLOTS},
            "missing_core_slots": [s for s in CORE_SLOTS if not by_slot[s]],
            #: The behaviour's ROLE SIGNATURE — the parties it is about, read
            #: off its own entity slot. Empty means the role-aware operators
            #: impose no constraint on this behaviour at all, which is the
            #: honest thing for the audit surface to say.
            "query_roles": list(query_roles(query)),
            "notation_operators": {name: bool(OPERATORS[name](ev)) if ev
                                   else False
                                   for name in sorted(NOTATION_OPERATORS)},
            "evidence": [{
                "slot": e.slot,
                "behaviour_atom": e.behaviour_atom,
                "behaviour_atom_weight": e.weight,
                "relation_hops": e.hops,
                "path": [r.as_dict() for r in e.path] if e.path
                        else [{"rel": "identical", "a": e.behaviour_atom,
                               "b": e.clause_atom, "via": "exact atom name",
                               "evidence": "the behaviour and the clause were "
                                           "annotated with the same atom",
                               "source": "annotation"}],
                "clause_atom": e.clause_atom,
                # The rung-1.5 notation, if the annotation carries any. All
                # three are inert (stem == name, nulls) on rung-0/1 artifacts,
                # so this prints the same thing it always did there.
                "clause_atom_stem": e.stem,
                "clause_atom_polarity": e.clause_polarity,
                "clause_atom_principals": list(e.clause_principals),
                "clause_atom_gloss": e.gloss,
                "clause_atom_df": self.df.get(e.clause_atom, 0),
                "clause_atom_generic": self.is_generic(e.clause_atom),
                "information_content": round(e.ic, 3),
                "clause_id": e.clause_id,
                "span_id": e.span_id,
                "span": e.span,
                "locator": e.locator,
                "evidence_mass": round(e.mass(self.use_weights), 4),
            } for e in sorted(ev, key=lambda e: (SLOTS.index(e.slot), e.hops,
                                                 e.clause_atom))],
            "defeated": [{
                "slot": d.slot, "contrary_of": d.behaviour_atom,
                "clause_atom": d.clause_atom, "span": d.span,
                "locator": d.locator,
                "effect": f"the {d.slot} slot cannot be filled: the clause is "
                          f"about the opposite concept",
            } for d in defeated],
            "constants_in_play": {k: v["value"] for k, v in CONSTANTS.items()},
        }

    # -------------------------------------------------------------- reports

    def rung_profile(self, query: Query) -> dict:
        """`{rung: n clauses}` — the shape of the ladder for one behaviour."""
        m = self.match(query)
        c = Counter(x.rung for x in m.values())
        return {name: c.get(name, 0) for name in RUNG_NAMES}


# -------------------------------------------------------------------- CLI

USAGE = """\
structural.py <behaviour-slug> [options]  — typed ladder over spec clauses

  --atoms PATH         behaviour atoms   (default: behavior_atoms_b8.json)
  --annotations PATH   clause atoms      (default: annotations_b8.json)
  --ontology PATH      relation layer    (default: ontology.json if present)
  --operator NAME      which zero-parameter operator (default any_atom, the
                       no-choice one; the four notation operators read rung
                       1.5's polarity prefix and principal chain and are
                       CANDIDATES — see NOTATION_OPERATORS)
  --hops N             relation-path bound (default 0 — expansion was measured
                       to hurt; see CONSTANTS['max_hops'])
  --top N              rows to show      (default 20)
  --explain CLAUSE_ID  the full typed path for that clause
  --profile            per-rung counts for every behaviour
  --no-weights         ignore the model-authored 1-3 query atom weights

Entirely offline: no model is called at query time, ever.
"""


def build_parser():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("slug", nargs="?")
    ap.add_argument("--atoms", default=BEHAVIOUR_ATOMS)
    ap.add_argument("--annotations", default=ANNOTATIONS)
    ap.add_argument("--ontology", default=ONT.ARTIFACT)
    ap.add_argument("--clauses", default=CLAUSES)
    ap.add_argument("--operator", default=PRIMARY_OPERATOR,
                    choices=sorted(OPERATORS))
    ap.add_argument("--hops", type=int, default=MAX_HOPS)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--explain", default=None)
    ap.add_argument("--profile", action="store_true")
    ap.add_argument("--no-weights", action="store_true")
    ap.add_argument("-h", "--help", action="store_true")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    if args.help or (not args.slug and not args.profile):
        print(USAGE)
        return 0

    idx = StructuralIndex.from_files(args.clauses, args.annotations,
                                     args.ontology, max_hops=args.hops,
                                     use_weights=not args.no_weights)
    queries = load_queries(args.atoms)
    s = idx.onto.stats()
    print(f"# ontology: {s['n_relations']} relations over {s['n_atoms']} atoms "
          f"{s['by_relation']}; traversal bounded at {args.hops} hop(s)")
    if args.hops:
        print("# !! relation expansion is ON. It was MEASURED TO HURT on all "
              "three behaviours; --hops 0 is the shipped setting.")

    if args.profile:
        print(f"\n{'behaviour':38} " + " ".join(f"{n[:11]:>11}" for n in RUNG_NAMES))
        for slug, q in sorted(queries.items()):
            p = idx.rung_profile(q)
            print(f"{slug:38} " + " ".join(f"{p[n]:>11}" for n in RUNG_NAMES))
        return 0

    q = queries.get(args.slug)
    if q is None:
        raise SystemExit(f"unknown behaviour {args.slug!r}; have "
                         f"{sorted(queries)}")
    if args.explain:
        print(json.dumps(idx.explain(q, args.explain), indent=2, default=str))
        return 0

    m = idx.match(q)
    pred = idx.predict(q, args.operator)
    print(f"# {args.slug} — operator {args.operator} (0 parameters), "
          f"{len(pred)} clauses of {len(idx.ids)}")
    for cid, score in idx.rank(q)[:args.top]:
        hit = m.get(cid)
        if hit is None:
            break
        c = idx.by_id[cid]
        print(f"{score:5.3f}  {hit.rung:20} {cid}  {c.get('locator', '')}")
        print(f"         {c.get('quote', '')[:100]}")
        for e in sorted(hit.evidence, key=lambda e: SLOTS.index(e.slot))[:3]:
            print(f"           {e.describe()[:110]}")
    print(f"\nwhy:  structural.py {args.slug} --explain <clause_id>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
