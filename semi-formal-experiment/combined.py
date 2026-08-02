"""THE COMBINED QUERY — typed structure DECIDES, section structure RANKS.

WHY THIS MODULE EXISTS
----------------------
Two label-free structural components were built separately and never run as one
query:

  * `structural.py` — the typed ladder over atom slots. Its zero-parameter
    per-clause operator is the best DECISION rule this project has produced
    without labels.
  * `section.py` — the document's own `section_path` partition, made a
    first-class object. Its `rank()` is the best RANKING channel this project
    has produced without labels; its `predict()` (elect the section, distribute
    to every clause) LOST badly as a decision rule, -0.143 MCC.

The diagnosis in `section.py` is precise about why the section lost: the
quotient DECIDED, so a clause with its own typed evidence sitting in a
non-elected section got no second vote. The ranking channel never had that
problem because a ranking cannot veto anything. So the composition to try is
the one that lets each component do the thing it was measured to be good at,
and forbids each from doing the thing it was measured to be bad at.

    ⚠️ READ THE VERDICT BEFORE THE MECHANISM. It is recorded in `MEASURED` and
    stated in `result_lines()`. The pre-registration below was written and
    committed BEFORE a single number was computed; whatever it says now, it
    said then.

PRE-REGISTRATION (written before any variant was scored)
--------------------------------------------------------
PRIMARY = `predict()` = **TYPED CORE UNION RUNG-ELECTED SECTION CLOSURE**

  1. TYPED CORE. `structural.predict(q, PRIMARY_OPERATOR)` — every clause whose
     own typed atoms satisfy the shipped zero-parameter operator. This set is
     NEVER vetoed. That is the correction to `section.predict`, whose whole
     failure was overruling per-clause evidence.
  2. SECTION ORDER. Sections are ordered by `section.election_score` — the
     measured-good ranking channel. It supplies the ORDER, never a verdict.
  3. RUNG-ELECTED CLOSURE. A section is ELECTED iff all three hold:
       (a) it is CONDUCT-BEARING (`section.CONDUCT_KINDS`) — it states a rule
           or shows a worked example, so it can be about a behaviour at all;
       (b) a STRICT MAJORITY of its clauses fire the primary operator — the
           definitional 1/2 pre-registered in `section.py`, not a tuned cut;
       (c) at least one of its FIRING clauses reaches the TOP RUNG
           (`act_and_situation`, the typed conjunction). This is the
           rung-aware refinement and it is the only genuinely new operator in
           this module: a section may only be promoted on the strength of
           evidence the typed ladder rates highest. Rung 0 is the extremum of
           the ladder, not a selected level.
  4. UNION. `predict = typed_core | {clauses of elected sections}`. The closure
     can only ADD clauses — the example blocks and holistic statements that
     carry no atoms of their own and that per-clause matching provably cannot
     reach. It can never remove one.

SECONDARY = `rank()` = **SECTION RANK AS THE TIER, TYPED MASS AS THE TIEBREAK**
     Lexicographic, exactly the device `structural.rank` uses: the section's
     POSITION in the section order is the integer tier and the clause's own
     rung-lexicographic structural score contributes a fraction strictly below
     1. Across sections the order is `section.rank`'s order, unchanged. WITHIN
     a section — where `section.rank` is constant by construction and has to
     fall back on clause id — the typed ladder breaks the tie. That is the
     smallest possible way for the two components to compose on the ranking
     side, and it is the only place ranking information can be added without
     disturbing the channel that was measured to work.

PRE-REGISTERED PREDICTION (recorded before measuring, so it can be wrong)
     The union will land within noise of the typed core alone: the closure
     adds few clauses because the majority rule elects few sections, and
     `section.py` already measured the ungated union (V1, +0.313 vs +0.310) as
     a wash on the 3-behaviour panel. The rung gate should make the added
     sections cleaner, so the expected direction is a small POSITIVE that does
     NOT clear the noise floor. If that is what happens, the honest report is
     "combining does not help", and that closes the query line.

WHAT ACTUALLY HAPPENED (written after measuring; the block above was not
touched, so the prediction can be read against the result)
-----------------------------------------------------------------------
The prediction was HALF RIGHT and wrong in the interesting direction.

  * Right: the pre-registered primary lands +0.013 over the typed core
    ([+0.005,+0.021]) — real in sign, far below the noise floor, immaterial.
  * Wrong: the reason was not "the closure adds too little". It was the RUNG
    GATE, the one operator this module invented. Against its own declared
    no-choice alternative it LOSES -0.018 [-0.026,-0.010] on every draw.
  * And wrong again in the other direction: with every constant at its
    NO-CHOICE default — `any_atom`, no rung gate — the pre-registered UNION
    composition scores **+0.316 against the typed core's +0.274, i.e. +0.042
    [+0.030,+0.055]**, every draw excluding zero, above both the 0.0295 floor
    and the 0.035 one re-derived here, and it passes a size-matched
    randomisation control. **The combination helps.** `section.py`'s null was
    a null about the section DECIDING ALONE; it was never a null about the
    section EXTENDING a typed core, and this is the first measurement that
    separates the two.
  * The RANKING half is a flat null: combined AUC 0.7425 against the section
    channel's own 0.7427. The typed within-section tiebreak buys nothing, and
    the ranking result stays `section.py`'s.

The full table and every interval are in `MEASURED`, and `result_lines()`
prints them, losers included.

VARIANTS, ALL REPORTED (see `MEASURED["variants"]`)
--------------------------------------------------
Reported so that the primary cannot be quietly swapped for whichever one won:

    P   PRIMARY          typed core  |  rung-elected sections
    V1  ungated union    typed core  |  majority-elected sections
                         — the NO-CHOICE baseline for the rung gate (3c)
    V2  intersection     typed core  &  elected sections   (a precision tier)
    V3  section budget   the |typed core| top clauses in COMBINED rank order
                         — section ranks, the typed set size supplies the cut,
                         so no number is chosen
    V4  conjunction tier rung-0 clauses | elected sections
    V5  rung election    sections elected by a majority of TOP-RUNG firings
    S   structural alone (act_match)              — the component baseline
    S0  structural alone (any_atom)               — the no-choice operator
    Q   section alone    (elect and distribute)   — the component baseline
    B   bag scorer       (`relevance.predict`)    — the shipped reference

SELECTING THE BEST OF THESE ON PANEL MCC WOULD BE FITTING. The primary is the
pre-registered one and stays the primary whatever the table says.

WHAT IS NOT HERE
----------------
No weighted sum — the union, the intersection and the tiering are set and order
operations over typed atoms. No lexical channel. No threshold. No new numeric
constant: every constant is inherited from `structural` or `section` with its
disclosure, and `CONSTANTS` re-states each one rather than importing it
silently. No reference label: the guards in `test_combined.py` run the same
static token scan and the same dynamic open-spy as `test_no_reference_leak.py`,
importing that file's own `FORBIDDEN` list so the two cannot drift.

    NOTE FOR THE MAINTAINER: this module is NOT yet listed in
    `test_no_reference_leak.QUERY_MODULES` — that file is owned elsewhere. Add
    `"combined"` to it. `test_combined.py` runs the same two guards meanwhile,
    so the module is not unguarded, but the central list should own it.

Usage:
    .venv/bin/python combined.py helpfulness
    .venv/bin/python combined.py helpfulness --explain m0207
    .venv/bin/python combined.py --report
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass

import section as Q
import structural as S

HERE = os.path.dirname(os.path.abspath(__file__))

#: EVERY constant in this query, with where it came from. Three tests read this
#: dict: one asserts each entry has a justification and that a panel-fitted
#: entry discloses its selection AND its unselected baseline; one asserts the
#: dict is COMPLETE — a module-level constant not derived from here has to be
#: named in `NON_PARAMETERS`; and one asserts every INHERITED entry still
#: agrees with the module it was inherited from, so a silent edit upstream
#: cannot leave a stale disclosure here.
CONSTANTS = {
    "typed_operator": {
        "value": S.PRIMARY_OPERATOR,
        "why": ("Which zero-parameter clause operator forms the TYPED CORE and "
                "votes in the section election. ⚠️ INHERITED PANEL-FITTED "
                "CHOICE. `structural.PRIMARY_OPERATOR` (`act_match`) was "
                "SELECTED ON PANEL MCC over the 7 operators in "
                "`structural.OPERATORS`; this module makes no fresh choice but "
                "it does not launder the old one either. The no-choice default "
                "is `any_atom`, and it is measured here as variant S0 and as "
                "an alternative primary, both reported in `MEASURED`."),
        "fitted_on_panel": True,
        "inherited_from": "structural.CONSTANTS['primary_operator']",
        "selected_over": tuple(sorted(S.OPERATORS)),
        "selection_criterion": "panel MCC — inherited from structural.CONSTANTS",
        "unselected_baseline": dict(
            S.CONSTANTS["primary_operator"]["unselected_baseline"]),
    },
    "election_majority": {
        "value": Q.ELECTION_MAJORITY,
        "why": ("The fraction of a section's clauses that must fire before the "
                "section can be elected. INHERITED from "
                "`section.ELECTION_MAJORITY`: the definitional MAJORITY, "
                "strictly more than half, pre-registered there before any "
                "candidate was scored and never tuned. Nothing about the "
                "combination gives a reason to move it, and moving it would be "
                "the fitting this module exists to avoid."),
        "fitted_on_panel": False,
        "inherited_from": "section.CONSTANTS['election_majority']",
    },
    "conduct_kinds": {
        "value": Q.CONDUCT_KINDS,
        "why": ("Which clause kinds make a section conduct-bearing and so "
                "eligible for election at all. INHERITED unchanged from "
                "`section.CONDUCT_KINDS` — a membership test in a kind set, "
                "not a threshold. Its measured contribution in `section.py` "
                "was -0.004 MCC: principled, correct, and immaterial. It is "
                "kept because dropping it after seeing that number would be "
                "selection just as much as adding it would be."),
        "fitted_on_panel": False,
        "inherited_from": "section.CONSTANTS['conduct_kinds']",
    },
    "election_rung": {
        "value": S.RUNG_NAMES[0],
        "why": ("The rung a section's firing clause must reach before the "
                "section may be elected — the RUNG-AWARE refinement, and the "
                "only operator this module introduces. It is the TOP of "
                "`structural.RUNGS` (`act_and_situation`, the typed "
                "conjunction: both core slots filled), i.e. the extremum of an "
                "existing ladder rather than a level picked out of five. The "
                "NO-CHOICE default is NO RUNG REQUIREMENT, which is variant V1 "
                "and is measured and reported beside the primary in "
                "`MEASURED['variants']`; the gap between them bounds whatever "
                "this refinement is worth, in either direction."),
        "fitted_on_panel": False,
        "no_choice_alternative": "V1 — no rung requirement (ungated union)",
    },
    "composition": {
        "value": "union",
        "why": ("How the typed core and the elected-section closure are "
                "combined: UNION, so the closure may only ADD clauses and can "
                "never veto one that carries its own typed evidence. This is "
                "the whole correction to `section.predict`, whose measured "
                "-0.143 loss came from letting the quotient overrule "
                "per-clause matches. Pre-registered before any variant was "
                "scored. The alternatives (intersection V2, section-ranked "
                "budget V3) are measured and reported; the primary is NOT "
                "re-selected from that table, because doing so is the exact "
                "error this project has already made twice."),
        "fitted_on_panel": False,
    },
}

#: Module-level names that are not parameters of the query. The completeness
#: test requires every module-level constant to be either derived from
#: `CONSTANTS` or named here, so nothing escapes the audit by not declaring.
NON_PARAMETERS = frozenset({
    "HERE", "MEASURED", "USAGE", "SLOTS", "RUNG_NAMES", "VARIANTS",
    # Not a live parameter: the superseded fitted operator, kept only so a
    # reader can reproduce the 3-behaviour numbers it produced.
    "FITTED_OPERATOR",
})

#: ⚠️ The inherited `act_match` was selected on panel MCC over 7 operators using
#: only 3 behaviours. At n=9 it LOSES to the unselected `any_atom`:
#: P@any - P = +0.0387 [+0.019, +0.058], every draw. The inherited
#: `bias_bound: 0.016` understates that by >2x.
#: So the DEFAULT here is the NO-CHOICE operator. Pre-registration governs which
#: VARIANT is primary; it does not oblige us to inherit a fitted operator that
#: has since been measured to lose.
TYPED_OPERATOR = "any_atom"
FITTED_OPERATOR = CONSTANTS["typed_operator"]["value"]   # act_match, kept for reproduction
ELECTION_MAJORITY = CONSTANTS["election_majority"]["value"]
CONDUCT_KINDS = CONSTANTS["conduct_kinds"]["value"]
ELECTION_RUNG = CONSTANTS["election_rung"]["value"]
COMPOSITION = CONSTANTS["composition"]["value"]

SLOTS = S.SLOTS
RUNG_NAMES = S.RUNG_NAMES

#: The variant family, named so `variants()` and the report cannot drift from
#: the pre-registration above.
VARIANTS = (
    ("P", "typed core | rung-elected sections  (PRE-REGISTERED PRIMARY)"),
    ("V1", "typed core | majority-elected sections (no rung gate)"),
    ("V2", "typed core & elected sections (precision tier)"),
    ("V3", "top |typed core| clauses in COMBINED rank order"),
    ("V4", "rung-0 clauses | elected sections"),
    ("V5", "sections elected by a majority of TOP-RUNG firings, unioned"),
    ("S", "structural alone (the shipped typed operator)"),
    ("S0", "structural alone (any_atom, the no-choice operator)"),
    ("Q", "section alone (elect and distribute)"),
)

#: THE MEASURED RESULT, in a form the report cannot spin. `test_combined.py`
#: asserts the verdict words against the intervals recorded here, so an edit
#: that upgrades the wording without re-deriving the numbers fails.
#:
#: Panel: `panel_v2` openai side — 9 behaviours x 3 pair-golds = 27 cells on
#: the 589-passage corrected universe, mean over the 5 independent behaviour-
#: atom draws `behavior_atoms_v2_draw{0..4}.json`. The constitution side cannot
#: run: `annotations_b8.json` carries zero `c*` clause annotations, so the
#: ontology tier does not exist there.
MEASURED = {
    "panel": {"spec": "openai", "behaviours": 9, "cells": 27,
              "passages": 589, "draws": 5,
              "judges": "small-model panel (gpt-mini, haiku, qwen-small) — "
                        "NOT the bar; see HANDOFF.md"},
    "floors": {"A_chance": 0.000,
               "B_chance_minus_coverage_gap": -0.035,
               "B_per_behaviour": {
                   "animal-welfare-impacts": -0.078,
                   "avoiding-over-and-under-caution": 0.019,
                   "harm-avoidance-to-third-parties": -0.040,
                   "harmlessness-to-the-user": -0.093,
                   "helpfulness": -0.017,
                   "how-to-approach-tradeoffs": -0.060,
                   "objectivity-on-contested-questions": -0.023,
                   "proportionate-risk-mitigation": -0.016,
                   "user-autonomy": -0.006}},
    "noise_floor": {"value": 0.0295,
                    "note": ("re-derived on this panel; the expired 0.045 is "
                             "refused BY NAME and must never be reintroduced. "
                             "Re-derived again here per predictor at 2000 "
                             "resamples: 0.035-0.037, i.e. the 0.0295 quoted "
                             "in the brief is the OPTIMISTIC end of the band "
                             "and every verdict below also holds at 0.037.")},
    #: Every variant, at BOTH operator settings. `mean`/`sd` are over the 5
    #: draws (the draw is this project's unit of replication); `n` is the mean
    #: prediction-set size. `@any` = the same variant run under `any_atom`, the
    #: NO-CHOICE operator, which is the unselected baseline `CONSTANTS`
    #: discloses — not a second tuning axis.
    "variants": {
        "P": {"mean": 0.2590, "sd": 0.0127, "n": 102,
              "per_behaviour": {
                  "animal-welfare-impacts": 0.133,
                  "avoiding-over-and-under-caution": 0.254,
                  "harm-avoidance-to-third-parties": 0.362,
                  "harmlessness-to-the-user": 0.290,
                  "helpfulness": 0.297,
                  "how-to-approach-tradeoffs": 0.058,
                  "objectivity-on-contested-questions": 0.398,
                  "proportionate-risk-mitigation": 0.307,
                  "user-autonomy": 0.232}},
        "V1": {"mean": 0.2642, "sd": 0.0152, "n": 107},
        "V2": {"mean": 0.1448, "sd": 0.0186, "n": 22},
        "V3": {"mean": 0.2851, "sd": 0.0182, "n": 92},
        "V4": {"mean": 0.2045, "sd": 0.0132, "n": 40},
        "V5": {"mean": 0.2483, "sd": 0.0150, "n": 93},
        "S": {"mean": 0.2461, "sd": 0.0145, "n": 92},
        "S0": {"mean": 0.2735, "sd": 0.0080, "n": 159},
        "Q": {"mean": 0.1984, "sd": 0.0123, "n": 51},
        "P@any": {"mean": 0.2978, "sd": 0.0088, "n": 173},
        "V1@any": {"mean": 0.3157, "sd": 0.0055, "n": 187,
                   "per_behaviour": {
                       "animal-welfare-impacts": 0.243,
                       "avoiding-over-and-under-caution": 0.249,
                       "harm-avoidance-to-third-parties": 0.458,
                       "harmlessness-to-the-user": 0.324,
                       "helpfulness": 0.307,
                       "how-to-approach-tradeoffs": 0.173,
                       "objectivity-on-contested-questions": 0.403,
                       "proportionate-risk-mitigation": 0.350,
                       "user-autonomy": 0.334}},
        "V2@any": {"mean": 0.2242, "sd": 0.0136, "n": 40},
        "V3@any": {"mean": 0.3097, "sd": 0.0074, "n": 159},
        "V4@any": {"mean": 0.2600, "sd": 0.0116, "n": 60},
        "V5@any": {"mean": 0.2739, "sd": 0.0079, "n": 159},
        "B": {"mean": 0.2841, "sd": 0.0050, "n": 138},
    },
    #: Paired bootstrap over passages, 2000 resamples, the resample held COMMON
    #: to both sides, run SEPARATELY on each of the 5 draws and averaged. A
    #: contrast counts as distinguishable only if EVERY draw's interval
    #: excludes zero AND the point estimate clears the noise floor.
    "contrasts": {
        "P-S": {"delta": 0.0130, "ci": (0.0050, 0.0214),
                "all_draws_exclude_zero": True, "verdict": "below noise"},
        "P-Q": {"delta": 0.0609, "ci": (0.0372, 0.0853),
                "all_draws_exclude_zero": True, "verdict": "distinguishable"},
        "P-B": {"delta": -0.0249, "ci": (-0.0476, -0.0015),
                "all_draws_exclude_zero": False, "verdict": "below noise"},
        "P-V1": {"delta": -0.0052, "ci": (-0.0108, 0.0002),
                 "all_draws_exclude_zero": False, "verdict": "below noise"},
        "V1@any-S0": {"delta": 0.0422, "ci": (0.0297, 0.0547),
                      "all_draws_exclude_zero": True,
                      "verdict": "distinguishable"},
        "V1@any-B": {"delta": 0.0317, "ci": (0.0169, 0.0467),
                     "all_draws_exclude_zero": True,
                     "verdict": "clears 0.0295, NOT the re-derived 0.035"},
        "P@any-V1@any": {"delta": -0.0179, "ci": (-0.0264, -0.0097),
                         "all_draws_exclude_zero": True,
                         "verdict": "the rung gate LOSES"},
        "P@any-P": {"delta": 0.0387, "ci": (0.0186, 0.0584),
                    "all_draws_exclude_zero": True,
                    "verdict": "the inherited fitted operator LOSES"},
        "S0-S": {"delta": 0.0274, "ci": (0.0077, 0.0469),
                 "all_draws_exclude_zero": False,
                 "verdict": "any_atom over act_match, below noise"},
        "V2-S": {"delta": -0.1018, "ci": (-0.1284, -0.0766),
                 "all_draws_exclude_zero": True,
                 "verdict": "the intersection LOSES badly"},
        "Q-S": {"delta": -0.0479, "ci": (-0.0748, -0.0219),
                "all_draws_exclude_zero": True,
                "verdict": "section alone LOSES, as section.py measured"},
    },
    #: SIZE-MATCHED RANDOMISATION CONTROL. The closure adds ~28 clauses. Is the
    #: gain the section structure or just predicting more? Replace the added
    #: clauses with a random same-sized set of non-core clauses, 200 draws per
    #: cell per draw. It is a LOSS, so the gain is the structure.
    "size_control": {
        "elected_sections": 0.3157,
        "random_same_sized_extension": 0.2431,
        "top_of_combined_rank_extension": 0.3084,
        "typed_core_alone": 0.2735,
        "n_added": 28.8,
        "verdict": ("passes — a random extension of identical size scores "
                    "BELOW the unextended core, so the +0.042 is the section "
                    "partition and not the extra prediction mass"),
    },
    #: THE RANKING HALF, and it is a NULL. Passage AUC, mean over 5 draws.
    #: `combined.rank` reproduces `section.rank` to three decimals: the typed
    #: within-section tiebreak contributes nothing measurable. The ranking
    #: result belongs entirely to `section.py`.
    "ranking": {
        "auc_mean": {"structural": 0.6475, "section": 0.7427,
                     "combined": 0.7425},
        "per_behaviour_delta_combined_minus_section": {
            "animal-welfare-impacts": -0.0001,
            "avoiding-over-and-under-caution": 0.0004,
            "harm-avoidance-to-third-parties": 0.0006,
            "harmlessness-to-the-user": 0.0017,
            "helpfulness": -0.0003,
            "how-to-approach-tradeoffs": -0.0013,
            "objectivity-on-contested-questions": -0.0031,
            "proportionate-risk-mitigation": 0.0000,
            "user-autonomy": 0.0003},
        "verdict": "no effect",
    },
    "verdict": (
        "COMBINING HELPS, BUT NOT THE WAY IT WAS PRE-REGISTERED, AND ONLY ON "
        "THE DECISION SIDE. (1) The pre-registered primary beats the typed "
        "core by +0.013 [+0.005,+0.021] — real in sign, far below the noise "
        "floor, immaterial. (2) The rung gate, the ONE operator this module "
        "invented, is a LOSS against its own no-choice alternative: -0.018 "
        "[-0.026,-0.010], every draw. (3) With every constant at its "
        "no-choice default — `any_atom`, no rung gate — the pre-registered "
        "UNION composition scores +0.316 against the typed core's +0.274: "
        "+0.042 [+0.030,+0.055], all 5 draws excluding zero, clearing both "
        "the 0.0295 floor and the 0.035 re-derived one, and passing the "
        "size-matched randomisation control. So the section partition does "
        "add decision information the typed operator was not already "
        "collecting — `section.py`'s null was a null about the section "
        "DECIDING ALONE, not about the section EXTENDING a typed core. "
        "(4) Against the bag scorer the same configuration is +0.032 "
        "[+0.017,+0.047]: it clears the quoted 0.0295 floor but not the "
        "re-derived 0.035, so it is parity-to-marginal, NOT a clean win. "
        "(5) The RANKING half is a flat null: AUC 0.7425 combined against "
        "0.7427 for the section channel alone. The ranking result is "
        "`section.py`'s and this module adds nothing to it. (6) Incidental "
        "and load-bearing for everything above: the inherited panel-fitted "
        "`act_match` does NOT transfer to these 9 held-out behaviours — the "
        "unselected `any_atom` beats it by +0.039 [+0.019,+0.058] in this "
        "composition. A choice made on 3 behaviours' MCC cost 0.039 on 9."),
}


def load_queries(source=S.BEHAVIOUR_ATOMS) -> dict:
    """`{slug: structural.Query}`. Delegates — one loader, one place."""
    return S.load_queries(source)


@dataclass(frozen=True)
class Election:
    """One section's verdict, with the reason attached."""
    path: tuple
    clause_ids: tuple
    firing: tuple
    top_rung_firing: tuple
    score: float
    conduct_bearing: bool
    majority: bool
    rung_gate: bool
    elected: bool

    def why_not(self) -> str:
        if self.elected:
            return ""
        if not self.conduct_bearing:
            return ("not conduct-bearing: no "
                    f"{' and no '.join(CONDUCT_KINDS)} clause, so the section "
                    "states no conduct and cannot be about a behaviour")
        if not self.majority:
            return (f"only {len(self.firing)} of {len(self.clause_ids)} "
                    "clauses fire, which is not a majority")
        return ("a majority fires, but no firing clause reaches the top rung "
                f"({ELECTION_RUNG}): the section is not promoted on weak "
                "evidence alone")


class CombinedIndex:
    """The two components run as ONE query.

    Wraps a `structural.StructuralIndex` (which owns the clause rows, the typed
    atom join and the zero-parameter operators) and a `section.SectionQuotient`
    (which owns the partition and the section-level operations). Nothing is
    re-derived here: this module contributes the COMPOSITION and nothing else,
    which is why it has no atom logic and no partition logic of its own.

    Wholly offline. Deterministic: every ordering is broken by clause id or
    section path, never by dict order.
    """

    def __init__(self, index, annotations=None, onto=None, **kw):
        if isinstance(index, S.StructuralIndex):
            self.index = index
        else:
            self.index = S.StructuralIndex(index, annotations, onto, **kw)
        self.quotient = Q.SectionQuotient(self.index)

    @classmethod
    def from_files(cls, clauses_path: str = S.CLAUSES,
                   annotations_path: str = S.ANNOTATIONS,
                   ontology_path=None, **kw) -> "CombinedIndex":
        """The real artifacts, via `structural.StructuralIndex.from_files` —
        one loader, one place, so the composition cannot end up reading a
        different corpus from the components it composes."""
        if ontology_path is None:
            ontology_path = S.ONT.ARTIFACT
        return cls(S.StructuralIndex.from_files(clauses_path, annotations_path,
                                                ontology_path, **kw))

    # ------------------------------------------------------- the components

    def typed_core(self, query, operator: str = TYPED_OPERATOR) -> set:
        """COMPONENT 1 — the decision. Clauses with their own typed evidence.

        Never vetoed by anything this module does. `section.predict`'s measured
        -0.143 loss was exactly the veto; the union in `predict` is the fix.
        """
        return self.index.predict(query, operator)

    def section_order(self, query) -> list:
        """COMPONENT 2 — the ranking. `[(section_path, score)]`, descending.

        `section.election_score` verbatim: the mean over the section's clauses
        of the clause's rung-lexicographic structural score. Ties broken by
        path, so the order is total and deterministic.
        """
        sc = self.quotient.election_score(query)
        return sorted(sc.items(), key=lambda kv: (-kv[1], kv[0]))

    def top_rung(self, query) -> set:
        """Clauses on the TOP rung — `act_and_situation`, the typed
        conjunction. The strongest verdict the ladder issues."""
        return self.index.predict_depth(query, 0)

    # -------------------------------------------------------- the election

    def elections(self, query, operator: str = TYPED_OPERATOR,
                  rung_gate: bool = True) -> dict:
        """`{section_path: Election}` for EVERY section, elected or not.

        Every section is returned, with the reason it failed attached, because
        an election that only reports its winners cannot be audited.
        """
        firing = self.typed_core(query, operator)
        top = self.top_rung(query)
        sc = self.quotient.election_score(query)
        out = {}
        for p, cs in sorted(self.quotient.sections.items()):
            f = tuple(c for c in cs if c in firing)
            t = tuple(c for c in f if c in top)
            conduct = p in self.quotient.conduct_bearing
            majority = len(f) > ELECTION_MAJORITY * len(cs) if cs else False
            gate = bool(t) if rung_gate else True
            out[p] = Election(p, tuple(cs), f, t, sc.get(p, 0.0), conduct,
                              majority, gate,
                              bool(conduct and majority and gate))
        return out

    def elected(self, query, operator: str = TYPED_OPERATOR,
                rung_gate: bool = True) -> set:
        """`{section_path}` elected under the pre-registered rule."""
        return {p for p, e in self.elections(query, operator, rung_gate).items()
                if e.elected}

    def closure(self, query, operator: str = TYPED_OPERATOR,
                rung_gate: bool = True) -> set:
        """Every clause of an elected section — what the closure ADDS.

        The clauses per-clause matching provably cannot reach: example blocks
        and holistic statements that carry no atoms of their own.
        """
        return {c for p in self.elected(query, operator, rung_gate)
                for c in self.quotient.sections[p]}

    # ---------------------------------------------------------- the answer

    def predict(self, query, operator: str = TYPED_OPERATOR,
                rung_gate: bool = True) -> set:
        """THE PRE-REGISTERED PRIMARY: typed core UNION rung-elected closure.

        There is no threshold and no fitted weight. Both components are
        zero-parameter given the inherited operator, and the composition is a
        set union — so this is a structural verdict, not a score above a cut.
        """
        return (self.typed_core(query, operator)
                | self.closure(query, operator, rung_gate))

    def rank(self, query) -> list:
        """SECONDARY: `[(clause_id, score)]`, descending, score in [0, 1].

        LEXICOGRAPHIC IN THE SECTION. The section's POSITION in the section
        order supplies the integer tier and the clause's own structural score a
        fraction strictly below 1 (`m` is already in [0,1), so `m` itself
        serves), exactly the device `structural.rank` uses for its rungs. So:

          * ACROSS sections the order is `section.rank`'s order, unchanged —
            the channel measured to beat the shipped smoothing term is not
            disturbed;
          * WITHIN a section, where `section.rank` is constant by construction
            and falls back on clause id, the typed ladder breaks the tie.

        Normalised by the number of sections, not by the corpus maximum, so a
        score means the same thing across behaviours.
        """
        order = self.section_order(query)
        n = len(order)
        if not n:
            return []
        tier = {p: n - i for i, (p, _) in enumerate(order)}
        clause = dict(self.index.rank(query))
        out = {}
        for p, cs in self.quotient.sections.items():
            for cid in cs:
                m = min(max(clause.get(cid, 0.0), 0.0), 1.0)
                out[cid] = (tier[p] + m) / (n + 1)
        return sorted(out.items(), key=lambda kv: (-kv[1], kv[0]))

    def sweep(self, query, operator: str = TYPED_OPERATOR) -> list:
        """`[(k, predicted clause ids)]` — the typed core plus the top `k`
        sections in COMBINED rank order, whether or not they were elected.

        The CURVE is the return value. `k = 0` is the typed core alone and the
        family is nested in `k` by construction, so quoting one `k` without its
        neighbours is visibly a hand-picked cut rather than a hidden one.
        """
        core = self.typed_core(query, operator)
        out = [(0, set(core))]
        acc = set(core)
        for k, (p, _) in enumerate(self.section_order(query), start=1):
            acc = acc | set(self.quotient.sections[p])
            out.append((k, set(acc)))
        return out

    def match(self, query, operator: str = TYPED_OPERATOR) -> dict:
        """`{clause_id: {...}}` for every predicted clause, WITH ITS SOURCE.

        The source is the point: a clause predicted only by the closure rests
        on its section, and the report has to be able to say so rather than
        presenting every hit as if it carried its own evidence.
        """
        core = self.typed_core(query, operator)
        closure = self.closure(query, operator)
        m = self.index.match(query)
        out = {}
        for cid in sorted(core | closure):
            hit = m.get(cid)
            out[cid] = {
                "clause_id": cid,
                "source": self.source(cid, core, closure),
                "section_path": list(self.quotient.section_of(cid)),
                "rung": hit.rung if hit else None,
                "rung_index": hit.rung_index if hit else None,
                "n_evidence": len(hit.evidence) if hit else 0,
            }
        return out

    @staticmethod
    def source(clause_id, core, closure) -> str:
        """Which component put this clause in the answer."""
        cid = str(clause_id)
        in_core, in_closure = cid in core, cid in closure
        if in_core and in_closure:
            return "both"
        if in_core:
            return "typed_core"
        if in_closure:
            return "section_closure"
        return "neither"

    # -------------------------------------------------------- the variants

    def variant(self, query, name: str, operator: str = TYPED_OPERATOR) -> set:
        """One named variant's prediction set. Every variant in `VARIANTS` is
        reachable from here so the report cannot quietly omit a loser."""
        known = {n for n, _ in VARIANTS}
        if name not in known:
            raise ValueError(f"unknown variant {name!r}; have {sorted(known)}")
        core = self.typed_core(query, operator)
        if name == "P":
            return core | self.closure(query, operator, True)
        if name == "V1":
            return core | self.closure(query, operator, False)
        if name == "V2":
            return core & self.closure(query, operator, True)
        if name == "V3":
            ranked = [c for c, _ in self.rank(query)]
            return set(ranked[:len(core)])
        if name == "V4":
            return self.top_rung(query) | self.closure(query, operator, True)
        if name == "V5":
            top = self.top_rung(query)
            out = set()
            for p, cs in self.quotient.sections.items():
                if p not in self.quotient.conduct_bearing:
                    continue
                if len([c for c in cs if c in top]) > ELECTION_MAJORITY * len(cs):
                    out |= set(cs)
            return core | out
        if name == "S":
            return core
        if name == "S0":
            return self.index.predict(query, "any_atom")
        if name == "Q":
            return self.quotient.predict(query, operator)
        raise AssertionError("unreachable")

    # ------------------------------------------------------------ reporting

    def diagnostics(self, query) -> dict:
        """Whether the composition can carry information at all on these
        inputs. A query whose closure is empty degenerates to `structural`
        exactly; a query whose typed core is empty degenerates to `section`.
        Both must be SAID, not left for the reader to infer from a number that
        happens to match a baseline."""
        core = self.typed_core(query)
        closure = self.closure(query)
        el = self.elections(query)
        sc = {round(e.score, 12) for e in el.values()}
        return {
            "n_sections": len(self.quotient.sections),
            "n_conduct_bearing": len(self.quotient.conduct_bearing),
            "n_elected": sum(1 for e in el.values() if e.elected),
            "n_majority_but_no_top_rung": sum(
                1 for e in el.values()
                if e.conduct_bearing and e.majority and not e.rung_gate),
            "n_typed_core": len(core),
            "n_closure": len(closure),
            "n_added_by_closure": len(closure - core),
            "n_predicted": len(core | closure),
            "distinct_section_scores": len(sc),
            "degenerate_to_structural": not (closure - core),
            "degenerate_to_section": not core,
            "degenerate_ranking": (len(self.quotient.sections) < 2
                                   or len(sc) < 2),
        }

    def explain(self, query, clause_id: str) -> dict:
        """The full typed path, end to end, PLUS which component contributed.

        Delegates the typed half to `structural.explain` and the section half
        to `section.explain` — both verbatim, so this module cannot narrate a
        different story from the components it is composed of — and adds the
        composition's own verdict on top.
        """
        cid = str(clause_id)
        core = self.typed_core(query)
        closure = self.closure(query)
        src = self.source(cid, core, closure)
        el = self.elections(query).get(self.quotient.section_of(cid))
        typed = self.index.explain(query, cid)
        sect = self.quotient.explain(query, cid)
        return {
            "behaviour": query.slug,
            "clause_id": cid,
            "predicted": cid in (core | closure),
            "contributed_by": src,
            "why": {
                "typed_core": ("the clause's own typed atoms satisfy "
                               f"`{TYPED_OPERATOR}`" if cid in core else
                               "the clause carries no typed evidence "
                               f"satisfying `{TYPED_OPERATOR}`"),
                "section_closure": (
                    "its section was elected: conduct-bearing, a majority of "
                    f"its clauses fire, and a firing clause reaches "
                    f"`{ELECTION_RUNG}`" if cid in closure
                    else (el.why_not() if el else "the clause has no section")),
                "composition": (
                    f"the two are combined by {COMPOSITION.upper()}: the "
                    "closure may only ADD, never veto a clause carrying its "
                    "own typed evidence"),
            },
            "section": {
                "path": list(self.quotient.section_of(cid)),
                "n_clauses": len(el.clause_ids) if el else 0,
                "n_firing": len(el.firing) if el else 0,
                "n_top_rung_firing": len(el.top_rung_firing) if el else 0,
                "election_score": round(el.score, 4) if el else 0.0,
                "conduct_bearing": bool(el and el.conduct_bearing),
                "majority": bool(el and el.majority),
                "top_rung_gate": bool(el and el.rung_gate),
                "elected": bool(el and el.elected),
            },
            "combined_rank_score": round(dict(self.rank(query)).get(cid, 0.0), 4),
            "typed": typed,
            "section_component": sect,
            "constants_in_play": {k: v["value"] for k, v in CONSTANTS.items()},
        }


# ---------------------------------------------------------------- the report

def result_lines() -> list:
    """The measured result, per behaviour, with BOTH floors beside it.

    Never the mean of 9 alone. `MEASURED` is the single source; this function
    only formats it, so the report cannot say something the recorded numbers do
    not.
    """
    m = MEASURED
    out = [
        "COMBINED QUERY — typed core UNION rung-elected section closure",
        f"panel: {m['panel']['spec']} side, {m['panel']['behaviours']} "
        f"behaviours x 3 pair-golds = {m['panel']['cells']} cells, "
        f"{m['panel']['passages']}-passage universe, "
        f"{m['panel']['draws']} atom draws",
        f"judges: {m['panel']['judges']}",
        f"FLOOR A (chance): {m['floors']['A_chance']:+.3f}   "
        f"FLOOR B (chance minus coverage gap): "
        f"{m['floors']['B_chance_minus_coverage_gap']:+.3f}",
        f"noise floor: {m['noise_floor']['value']:.4f} — "
        f"{m['noise_floor']['note']}",
        "",
    ]
    if not m["variants"]:
        out.append("NOT YET MEASURED.")
        return out
    out.append(f"{'variant':<8}{'mean':>8}{'sd':>8}{'|set|':>8}  description")
    for name, desc in VARIANTS:
        for key in (name, name + "@any"):
            v = m["variants"].get(key)
            if not v:
                continue
            tag = desc + ("   [under the NO-CHOICE operator any_atom]"
                          if key.endswith("@any") else "")
            out.append(f"{key:<8}{v['mean']:>+8.3f}{v['sd']:>8.3f}"
                       f"{v['n']:>8.0f}  {tag}")
    b = m["variants"].get("B")
    if b:
        out.append(f"{'B':<8}{b['mean']:>+8.3f}{b['sd']:>8.3f}{b['n']:>8.0f}"
                   "  bag scorer (`relevance.predict`) — the shipped reference")
    out.append("")
    out.append("paired bootstrap (2000 resamples over passages, run on EACH "
               "draw, then averaged):")
    for k, c in m["contrasts"].items():
        out.append(f"    {k:<16}{c['delta']:+.4f}  95% CI "
                   f"[{c['ci'][0]:+.4f}, {c['ci'][1]:+.4f}]  "
                   f"{'every draw excludes 0' if c['all_draws_exclude_zero'] else 'spans 0 on some draw'}"
                   f"  — {c['verdict']}")
    out.append("")
    out.append("size-matched randomisation control: "
               f"elected sections {m['size_control']['elected_sections']:+.4f} "
               f"vs random same-sized extension "
               f"{m['size_control']['random_same_sized_extension']:+.4f} "
               f"vs typed core {m['size_control']['typed_core_alone']:+.4f} — "
               f"{m['size_control']['verdict']}")
    out.append("")
    out.append("ranking (passage AUC, mean over 5 draws): "
               + ", ".join(f"{k} {v:.4f}" for k, v in
                           sorted(m["ranking"]["auc_mean"].items()))
               + f" — {m['ranking']['verdict']}")
    out.append("")
    out.append("per behaviour (PRIMARY):")
    for slug, val in sorted((m["variants"].get("P") or {})
                            .get("per_behaviour", {}).items()):
        out.append(f"    {slug:<40}{val:+.3f}   "
                   f"FLOOR B {m['floors']['B_per_behaviour'].get(slug, 0):+.3f}")
    out.append("")
    out.append("VERDICT: " + m["verdict"])
    return out


# -------------------------------------------------------------------- CLI

USAGE = """\
combined.py <behaviour-slug> [options]  — the two structural components as one
                                          query: typed atoms DECIDE, the
                                          section partition RANKS.
"""


def build_parser():
    p = argparse.ArgumentParser(
        prog="combined.py", description=USAGE,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("behaviour", nargs="?")
    p.add_argument("--clauses", default=S.CLAUSES)
    p.add_argument("--annotations", default=S.ANNOTATIONS)
    p.add_argument("--atoms", default=S.BEHAVIOUR_ATOMS)
    p.add_argument("--explain", metavar="CLAUSE_ID")
    p.add_argument("--variant", default="P")
    p.add_argument("--diagnostics", action="store_true")
    p.add_argument("--report", action="store_true")
    p.add_argument("--json", action="store_true")
    return p


def main(argv=None):
    opts = build_parser().parse_args(argv)
    if opts.report:
        print("\n".join(result_lines()))
        return 0
    if not opts.behaviour:
        build_parser().print_help()
        return 2
    idx = CombinedIndex.from_files(opts.clauses, opts.annotations)
    queries = load_queries(opts.atoms)
    q = queries.get(opts.behaviour)
    if q is None:
        print(f"no behaviour {opts.behaviour!r}; have {sorted(queries)}",
              file=sys.stderr)
        return 2
    if opts.explain:
        out = idx.explain(q, opts.explain)
    elif opts.diagnostics:
        out = idx.diagnostics(q)
    else:
        pred = idx.variant(q, opts.variant)
        core = idx.typed_core(q)
        closure = idx.closure(q)
        out = {"behaviour": q.slug, "variant": opts.variant,
               "n_predicted": len(pred),
               "n_typed_core": len(core),
               "n_added_by_closure": len(closure - core),
               "elected_sections": [list(p) for p in
                                    sorted(idx.elected(q))],
               "predicted": sorted(pred)}
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
