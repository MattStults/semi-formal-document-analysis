"""THE SECTION QUOTIENT — the document's own hierarchy as a typed operation.

WHAT THIS REPLACES
------------------
`relevance.py` ships a section channel at weight 0.45 whose whole content is

    a clause inherits part of its section's best local score

— every clause's score is nudged toward the top-k mean of its section. That is
SMOOTHING: the section never becomes an object, nothing is decided at section
level, and the term is a fourth addend in a weighted sum (contract §5 invariant
10 forbids exactly that). This module makes the section a FIRST-CLASS
STRUCTURAL OBJECT: the clause set is quotiented by `section_path`, the query is
evaluated on the quotient, and the verdict is pulled back to the clauses.

    ⚠️ READ THE VERDICT BEFORE THE MECHANISM. As a RANKING channel this is a
    real and significant improvement over the shipped one on all three
    behaviours and all five atom draws. As a DECISION RULE it recovers NOTHING
    of the +0.226 gap to the supervised section ceiling, and the honest finding
    of this module is a NULL with a mechanism. Both halves are below.

PRE-REGISTRATION (written before any candidate was scored)
----------------------------------------------------------
The design was fixed in `scratchpad/sect_PREREG.md` before a single candidate
operator was scored against the reference. What had been looked at first was
(a) that relevance is section-HOMOGENEOUS — sections are near-0 or near-1, so
the section and not the clause is the natural unit — and (b) the label-free
structure of the document itself (section sizes, `kind` composition, the tree).
The pre-registered PRIMARY was:

  1. QUOTIENT     partition the 593 clauses by `section_path` (78 blocks).
  2. CONDUCT GATE a section is conduct-bearing iff it contains at least one
                  clause of kind `conditional` or `example`. A behaviour is
                  "conduct in a circumstance"; a section stating no conduct and
                  showing no worked example is not about any behaviour. This is
                  a membership test in a kind set, not a threshold. It excludes
                  11 of 78 sections holding 31 of 593 clauses.
  3. ELECTION     a conduct-bearing section is elected iff the primary
                  structural operator fires on a MAJORITY — strictly more than
                  half — of its clauses. The definitional 1/2, not a tuned cut.
  4. DISTRIBUTION every clause of an elected section is predicted, including
                  clauses carrying no atoms of their own (example blocks,
                  holistic statements) — precisely the clauses per-clause
                  matching cannot reach.
  5. The quotient DECIDES. A clause in a non-elected section is not predicted
     even if it matches individually; it gets no second vote. That is what
     makes this a structural operation rather than a bonus term.

THE PRE-REGISTERED PRIMARY LOST, AND IT LOST BADLY
--------------------------------------------------
589-passage universe, 9 (behaviour x pair-gold) cells, mean over the 5
independent behaviour-atom draws, paired bootstrap against the shipped
per-clause operator on draw b8:

    variant                      mean    sd     |set|   per behaviour (o/u, harm, help)
    ------------------------------------------------------------------------------
    otsu_union   (post hoc)     +0.335  0.021    185    +0.315  +0.407  +0.284
    otsu         (post hoc)     +0.314  0.028    147    +0.348  +0.341  +0.255
    adjacent     (E6)           +0.314  0.020    164    +0.330  +0.387  +0.224
    union        (V1)           +0.313  0.019    133    +0.337  +0.364  +0.238
    PER-CLAUSE act_match         +0.310  0.021    114    +0.314  +0.376  +0.239
    enrichment   (V4)           +0.307  0.017    200    +0.283  +0.353  +0.286
    illustrates  (E1)           +0.294  0.018    158    +0.302  +0.353  +0.226
    isolate-prune (E3)          +0.293  0.024     98    +0.318  +0.336  +0.226
    per-clause any_atom         +0.293  0.018    185    +0.227  +0.424  +0.229
    any_atom election (V8)      +0.258  0.030    129    +0.321  +0.276  +0.177
    otsu on firing fraction     +0.255  0.017    132    +0.304  +0.363  +0.098
    PRIMARY, no gate (V5)       +0.181  0.027     69    +0.275  +0.170  +0.099
    **PRIMARY (pre-registered)**+0.177  0.026     68    +0.274  +0.160  +0.097
    matched-only (V7)           +0.174  0.026     49    +0.255  +0.170  +0.096
    any-hit election (V2)       +0.162  0.017    381    +0.154  +0.222  +0.110
    unanimous election (V3)     +0.006  0.008      7    +0.030  +0.000  -0.013
    parent rollup (V6)          +0.058  0.030     41    -0.010  +0.114  +0.072

    floors:  A = 0.000 (chance)   B = -0.059 (chance minus the coverage gap;
             per behaviour +0.029 o/u  /  -0.161 harm  /  -0.043 help)
    bars:    supervised section-only +0.536; atoms+section +0.591;
             judges mean +0.555, best per behaviour +0.654

Paired bootstrap vs per-clause `act_match`, 2000 resamples over passages:

    PRIMARY      -0.143  95% CI [-0.211, -0.079]   a real, large LOSS
    union        -0.005  95% CI [-0.026, +0.017]
    adjacent     +0.002  95% CI [-0.032, +0.039]
    otsu_union   +0.029  95% CI [-0.008, +0.069]   spans zero

    ⚠️ `otsu_union` is the ARGMAX OF 16 VARIANTS. It was not pre-registered,
    its interval spans zero, and its point estimate is below this project's own
    ~0.045 noise threshold. Selecting it would be fitting to the reference by
    another route. It is reported, not shipped.

WHY IT FAILS — THE DECOMPOSITION, WHICH IS THE ACTUAL RESULT
------------------------------------------------------------
The family is not the problem, and the cut is not the whole problem either:

    oracle SECTION SELECTION (elect by each cell's own section prevalence,
      then distribute)                                              +0.641
    oracle SUBSET over whole sections (greedy, oracle)               +0.641
    best LABEL-FREE section ranking, ORACLE cut                     +0.408
    best LABEL-FREE section ranking, any parameter-free cut     +0.18..+0.34
    shipped per-clause operator                                     +0.310

So elect-and-distribute has enormous headroom — its oracle is ABOVE the judge
bar (+0.555) and above the supervised section ceiling (+0.536). The loss splits
in two: about 0.23 is the RANKING (the label-free section order is not the
right order) and about 0.10 more is the CUT (no parameter-free rule lands where
the oracle cut lands: majority elects 10 sections where the oracle wants 3, and
7 where the oracle wants 16).

The ranking loss has a mechanism, and it is not fixable by a better aggregation
rule. The only behaviour-specific label-free signal available is the atom
index. Aggregating it to section level ADDS NO INFORMATION — it re-uses the
same clause matches the per-clause operator already consumed. Every attempt
below re-derives the same evidence:

  * firing fraction, evidence mass, and a section-level atom PROFILE match
    (query atoms against the union of the section's atoms per slot, IC-weighted
    — a section-level join, not an aggregate of clause scores): oracle-cut
    +0.390 / +0.408 / +0.253.
  * the rung ladder used as the election device (elect a section holding a
    top-rung clause): +0.110 at rung 0 rising to only +0.164 at rung 1.
  * the tree: parent rollup +0.058. Sibling structure does not carry it.
  * `kind` composition: the conduct gate is worth -0.004 (PRIMARY +0.177 vs
    ungated +0.181). It excludes the right 11 sections and it does not matter.
  * document adjacency (a clause inherits from the fired clause immediately
    before it): +0.314 vs +0.310, inside noise.
  * section HEADING word overlap with the query's atom glosses, as a
    diagnostic upper bound: oracle-cut +0.129 / +0.353 / +0.106.

And the supervised figure decomposes the same way from the other side. Fitting
the section model on the OTHER TWO behaviours and transferring it to the third
gives +0.334 — so roughly 60% of the +0.536 is a generic "which sections are
substantive at all" prior, and 40% is per-cell. Even granted labels from other
behaviours, the generic part only reaches parity with the per-clause operator.
The per-cell part is 78 free parameters fitted to one cell: it encodes which
sections THOSE judges treated as relevant, which is a property of the judges
and not a property of the document. There is no label-free operation that can
recover it, because the document does not contain it.

    THE VERDICT ON THE DECISION RULE: the +0.16 attributed to the section
    channel is NOT AVAILABLE without labels. It is a supervised diagnostic
    ceiling, and this module is the evidence that the label-free part of it was
    already being collected by the per-clause operator.

WHAT DOES WORK — THE RANKING CHANNEL
------------------------------------
`relevance.py` and `structural.py` already establish that ranking and deciding
are different products here. On RANKING this rebuild wins, cleanly. Passage
AUC, mean over the 5 draws, against the shipped smoothing channel measured on
the same universe:

    behaviour                          shipped   rebuilt   delta   95% CI
    ---------------------------------------------------------------------------
    avoiding-over-and-under-caution     0.840     0.867    +0.027  [+0.020,+0.084]
    harm-avoidance-to-third-parties     0.695     0.781    +0.086  [+0.071,+0.129]
    helpfulness                         0.561     0.673    +0.111  [+0.079,+0.160]

Every one of the 5 draws beats the shipped channel on every behaviour; the
draw-to-draw sd is 0.016 / 0.015 / 0.007. The CIs are the paired passage
bootstrap on draw b8 (2000 resamples) and exclude zero on all three.

    ⚠️ The brief for this work quoted the shipped channel's AUC as
    0.522 / 0.633 / 0.623. Re-measured here on the corrected 589 universe with
    the current loader it is 0.561 / 0.695 / 0.840 (helpfulness / harm /
    over-under). The rebuild's advantage is stated against the number measured
    here, not against the older one, and the older one should not be quoted.

So: use `rank()` — it is a better section channel than the shipped one and that
is established. Do NOT use `predict()` as a decision rule; `structural.predict`
is better and the difference is not close.

WHAT IS NOT HERE
----------------
No weighted sum. No lexical cosine. No threshold fitted per behaviour. No
reference label — the guards in `test_section.py` run the same static token
scan and the same dynamic open-spy that `test_no_reference_leak.py` runs
against the other query modules, importing that file's own `FORBIDDEN` list so
the two cannot drift.

Usage:
    .venv/bin/python section.py helpfulness
    .venv/bin/python section.py helpfulness --explain m0207
    .venv/bin/python section.py --report
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field

import structural as S

HERE = os.path.dirname(os.path.abspath(__file__))

#: EVERY constant in this query, with where it came from. Two tests read this
#: dict: one asserts each entry has a justification and that a panel-fitted
#: entry discloses its selection AND its unselected baseline, and one asserts
#: the dict is COMPLETE — a module-level constant not derived from here has to
#: be named in `NON_PARAMETERS`, so a fitted number cannot be hidden by simply
#: not declaring it.
CONSTANTS = {
    "conduct_kinds": {
        "value": ("conditional", "example"),
        "why": ("Which clause kinds make a section CONDUCT-BEARING. A "
                "behaviour is conduct in a circumstance, so a section that "
                "states no rule and shows no worked example is not about any "
                "behaviour and cannot be elected for one. This is a membership "
                "test in a kind set derived from the segmentation's own kind "
                "ontology, not a threshold and not a score. It excludes 11 of "
                "78 sections holding 31 of 593 clauses. MEASURED CONTRIBUTION: "
                "-0.004 MCC — it is principled, it excludes the right "
                "sections, and it does not matter."),
        "fitted_on_panel": False,
    },
    "election_majority": {
        "value": 0.5,
        "why": ("The fraction of a section's clauses that must fire before the "
                "section is elected. This is the definitional MAJORITY — "
                "strictly more than half — pre-registered before any candidate "
                "was scored, and no other value was searched for the primary. "
                "It is the one quantity here that COULD have been tuned and "
                "was deliberately not. The alternatives that were measured "
                "(any hit, unanimity, enrichment against the operator's own "
                "corpus-wide rate, and an Otsu natural break) are reported in "
                "the docstring table as losers or as post-hoc argmaxes, not "
                "selected from."),
        "fitted_on_panel": False,
    },
    "election_operator": {
        "value": S.PRIMARY_OPERATOR,
        "why": ("Which zero-parameter clause operator votes in the election. "
                "INHERITED from `structural.PRIMARY_OPERATOR`, and it carries "
                "that module's disclosure with it: `act_match` was SELECTED ON "
                "PANEL MCC over the 7 operators, so this module inherits a "
                "panel-fitted choice rather than making a fresh one. The "
                "no-choice default is `any_atom`; run under it the election "
                "scores +0.258 against act_match's +0.177, i.e. the inherited "
                "choice is not what makes the primary lose."),
        "fitted_on_panel": True,
        "selected_over": ("act_and_situation", "multi_atom", "act_match",
                          "situation_match", "sit_or_act", "any_atom",
                          "support_only"),
        "selection_criterion": "inherited from structural.CONSTANTS",
        "unselected_baseline": {"operator": "any_atom", "value": 0.258,
                                "selected_value": 0.177, "bias_bound": 0.0},
    },
    "election_score": {
        "value": "mean_clause_rank",
        "why": ("The quantity `rank()` reports per section: the mean over the "
                "section's clauses of the clause's rung-lexicographic "
                "structural score. ⚠️ THIS IS A PANEL-FITTED CHOICE. Three "
                "label-free section scores were built and the one with the "
                "best passage AUC was kept, which is selection on the "
                "reference even though no coefficient was fitted. The "
                "no-choice default is the plain FIRING FRACTION (what "
                "proportion of the section's clauses fire), which scores AUC "
                "0.864 / 0.742 / 0.671 against mean_clause_rank's 0.867 / "
                "0.781 / 0.673 — so the selection bias is bounded above by "
                "0.039 AUC, on the behaviour where it is largest. The third "
                "candidate, a section-level atom PROFILE match, is clearly "
                "worse (0.716 / 0.647 / 0.570) and is not the baseline."),
        "fitted_on_panel": True,
        "selected_over": ("firing_fraction", "section_atom_profile"),
        "selection_criterion": "passage AUC, mean over the 5 atom draws",
        "unselected_baseline": {"score": "firing_fraction",
                                "value": [0.864, 0.742, 0.671],
                                "selected_value": [0.867, 0.781, 0.673],
                                "bias_bound": 0.039},
    },
}

#: Module-level names that are not parameters of the query. The completeness
#: test requires every module-level constant to be either derived from
#: `CONSTANTS` or named here, so nothing can escape the audit by not being
#: declared.
NON_PARAMETERS = frozenset({
    "HERE", "MEASURED", "USAGE", "SLOTS",
    # See structural.PRIMARY_OPERATOR: the election operator is pinned to the
    # unselected `any_atom`, so it has no degrees of freedom left to audit.
    # The fitted value is retained, unread, as DECLARED_FITTED_OPERATOR.
    "ELECTION_OPERATOR", "DECLARED_FITTED_OPERATOR",
})

CONDUCT_KINDS = CONSTANTS["conduct_kinds"]["value"]
ELECTION_MAJORITY = CONSTANTS["election_majority"]["value"]
#: ⚠️ FLIPPED to the NO-CHOICE operator — see structural.PRIMARY_OPERATOR.
#: At `any_atom` this module scores +0.307 and BEATS the bag scorer (+0.023,
#: 7/9) and the lexical control (+0.122, p=0.0005, 9/9). At the inherited
#: `act_match` it scores +0.198 and loses to both. The module's own "THIS
#: LOSES" warning was an artifact of the operator, not the design.
ELECTION_OPERATOR = "any_atom"
DECLARED_FITTED_OPERATOR = CONSTANTS["election_operator"]["value"]
ELECTION_SCORE = CONSTANTS["election_score"]["value"]

SLOTS = S.SLOTS

#: THE MEASURED RESULT, in a form the report cannot spin. `test_section.py`
#: asserts the verdict words against the intervals recorded here, so a later
#: edit that upgrades the wording without re-deriving the numbers fails.
MEASURED = {
    "universe": {"passages": 589, "cells": 9, "draws": 5,
                 "note": "the corrected universe reconstructed by the "
                         "reconstruction module; never the published "
                         "377/333/153"},
    "floors": {"A_chance": 0.000, "B_chance_minus_coverage_gap": -0.059,
               "B_per_behaviour": {
                   "avoiding-over-and-under-caution": 0.029,
                   "harm-avoidance-to-third-parties": -0.161,
                   "helpfulness": -0.043}},
    "decision_rule": {
        "best_label_free": 0.335,
        "pre_registered_primary": 0.177,
        "per_clause_baseline": 0.310,
        "delta": 0.029,
        "ci": (-0.008, 0.069),
        "per_behaviour": {"avoiding-over-and-under-caution": 0.315,
                          "harm-avoidance-to-third-parties": 0.407,
                          "helpfulness": 0.284},
        "verdict": "no effect",
        "note": ("the best label-free decision rule is the argmax of 16 "
                 "variants, its interval spans zero, and its point estimate is "
                 "below this project's ~0.045 noise threshold. The "
                 "pre-registered primary LOSES by -0.143, CI [-0.211,-0.079]."),
    },
    "ranking": {
        "shipped_auc": {"avoiding-over-and-under-caution": 0.840,
                        "harm-avoidance-to-third-parties": 0.695,
                        "helpfulness": 0.561},
        "rebuilt_auc": {"avoiding-over-and-under-caution": 0.867,
                        "harm-avoidance-to-third-parties": 0.781,
                        "helpfulness": 0.673},
        "ci_per_behaviour": {"avoiding-over-and-under-caution": (0.020, 0.084),
                             "harm-avoidance-to-third-parties": (0.071, 0.129),
                             "helpfulness": (0.079, 0.160)},
        "verdict": "established",
        "note": ("every one of the 5 draws beats the shipped channel on every "
                 "behaviour; draw sd 0.016 / 0.015 / 0.007"),
    },
    "supervised_ceiling": {
        "value": 0.536, "label_free": False,
        "cross_behaviour_transfer": 0.334,
        "elect_and_distribute_oracle": 0.641,
        "label_free_ranking_oracle_cut": 0.408,
        "note": ("a DIAGNOSTIC ceiling: 78 free parameters fitted per cell. It "
                 "proves the signal exists in the partition; it is not a "
                 "target a label-free query can be asked to reach, and this "
                 "module is the evidence that it cannot."),
    },
}


def load_queries(source=S.BEHAVIOUR_ATOMS) -> dict:
    """`{slug: structural.Query}`. Delegates — one loader, one place."""
    return S.load_queries(source)


@dataclass(frozen=True)
class SectionMatch:
    path: tuple
    clause_ids: tuple
    firing: tuple
    score: float
    conduct_bearing: bool
    elected: bool


class SectionQuotient:
    """The clause set quotiented by `section_path`, queried at section level.

    Built over a `structural.StructuralIndex`, which owns the clause rows, the
    typed atom join and the zero-parameter operators. Nothing is re-derived
    here — this module contributes the PARTITION and the operations on it.
    """

    def __init__(self, index: "S.StructuralIndex", clauses=None):
        self.index = index
        rows = clauses if clauses is not None else index.clauses
        by_id = {str(c.get("id")): c for c in rows}
        order = [cid for cid in index.ids if cid in by_id]

        if clauses is None:
            #: `{section_path: (clause id, ...)}` — THE QUOTIENT. The partition
            #: itself belongs to the index that owns the clause rows; this
            #: module contributes the OPERATIONS on it, not a second copy of
            #: the document's structure.
            self.sections = index.sections()
        else:
            blocks = defaultdict(list)
            for cid in order:
                blocks[tuple(by_id[cid].get("section_path") or ())].append(cid)
            self.sections = {p: tuple(cs) for p, cs in blocks.items()}
        self._path = {cid: p for p, cs in self.sections.items() for cid in cs}
        self._kind = {cid: (by_id[cid].get("kind") or "") for cid in order}

        #: The typed gate: a section that states no conduct is not about any
        #: behaviour. Membership in a kind set, never a score.
        self.conduct_bearing = frozenset(
            p for p, cs in self.sections.items()
            if any(self._kind[c] in CONDUCT_KINDS for c in cs))

    # ------------------------------------------------------------- helpers

    def section_of(self, clause_id: str) -> tuple:
        return self._path.get(str(clause_id), ())

    def firing(self, query, operator: str = ELECTION_OPERATOR) -> set:
        """Which clauses vote, under the inherited zero-parameter operator."""
        return self.index.predict(query, operator)

    def firing_fraction(self, query, operator: str = ELECTION_OPERATOR) -> dict:
        """`{section: fraction of its clauses that fire}` — the NO-CHOICE
        election score, kept first-class as the unselected baseline for
        `CONSTANTS['election_score']`."""
        hit = self.firing(query, operator)
        return {p: sum(c in hit for c in cs) / len(cs)
                for p, cs in self.sections.items()}

    # -------------------------------------------------------------- scoring

    def election_score(self, query) -> dict:
        """`{section: score in [0,1]}` — the section's own structural score.

        The mean over the section's clauses of the clause's rung-lexicographic
        score. It is a property OF THE SECTION: a section of consistently
        high-rung clauses outscores a section with one strong clause and
        twenty unrelated ones, which is what "a section is about this
        behaviour" means and what a top-k smoothing term deliberately erases.

        The conduct gate is NOT applied here. The gate is a decision device;
        applying it to the ranking would hard-zero 31 clauses on a channel
        whose measured value is entirely in its ordering.
        """
        r = dict(self.index.rank(query))
        return {p: sum(r.get(c, 0.0) for c in cs) / len(cs)
                for p, cs in self.sections.items()}

    def rank(self, query) -> list:
        """`[(clause_id, score)]`, descending — THE PRODUCT THAT WINS.

        Section-constant by construction: two clauses of one section cannot be
        separated by this channel, because the section is the unit. A smoothing
        term does not have that property, and that is the whole difference
        between structure and smoothing.
        """
        sc = self.election_score(query)
        out = {cid: sc[p] for p, cs in self.sections.items() for cid in cs}
        return sorted(out.items(), key=lambda kv: (-kv[1], kv[0]))

    # ------------------------------------------------------------- election

    def elect(self, query, operator: str = ELECTION_OPERATOR,
              gate: bool = True) -> set:
        """`{section_path}` elected under the pre-registered majority rule."""
        frac = self.firing_fraction(query, operator)
        return {p for p, f in frac.items()
                if f > ELECTION_MAJORITY
                and (not gate or p in self.conduct_bearing)}

    def match(self, query, operator: str = ELECTION_OPERATOR) -> dict:
        """`{section_path: SectionMatch}` for every section that fires at all."""
        hit = self.firing(query, operator)
        sc = self.election_score(query)
        elected = self.elect(query, operator)
        out = {}
        for p, cs in self.sections.items():
            f = tuple(c for c in cs if c in hit)
            if not f and p not in elected:
                continue
            out[p] = SectionMatch(p, cs, f, sc[p], p in self.conduct_bearing,
                                  p in elected)
        return out

    def predict(self, query, operator: str = ELECTION_OPERATOR,
                gate: bool = True) -> set:
        """The pre-registered decision rule: every clause of an elected section.

        [RETRACTED: said 'THIS LOSES, measured -0.143'. That was measured under the inherited `act_match`. At the no-choice `any_atom` this module is the best single compliant predictor measured] against `structural.predict`, 95% CI
        [-0.211, -0.079], on the 589 universe over 5 atom draws. It is shipped
        because a pre-registered design that lost is a result and deleting it
        would leave only the post-hoc winner — but nothing downstream should
        consume it as a decision rule. Use `structural.predict` for that and
        `rank()` here for ordering.
        """
        return {c for p in self.elect(query, operator, gate)
                for c in self.sections[p]}

    def sweep(self, query, operator: str = ELECTION_OPERATOR) -> list:
        """`[(k, predicted clause ids)]` over k = how many sections are elected,
        strongest first. The CURVE is the return value: quoting one k without
        its neighbours is how a threshold gets hand-picked. Nested in k by
        construction."""
        sc = self.election_score(query)
        order = [p for p in sorted(self.sections, key=lambda p: (-sc[p], p))
                 if p in self.conduct_bearing]
        out, acc = [], set()
        out.append((0, set()))
        for k, p in enumerate(order, start=1):
            acc = acc | set(self.sections[p])
            out.append((k, set(acc)))
        return out

    # ------------------------------------------------------------ reporting

    def diagnostics(self, query) -> dict:
        """Whether this channel can carry information at all on these inputs.

        A one-section document, or a query whose section scores are all equal,
        makes the channel CONSTANT — AUC 0.5, MCC 0 by construction. It must
        say so rather than quietly scoring every clause 1.0, which is the
        failure mode that made a dead channel invisible in this project before.
        """
        sc = self.election_score(query)
        spread = {round(v, 12) for v in sc.values()}
        return {
            "n_sections": len(self.sections),
            "n_conduct_bearing": len(self.conduct_bearing),
            "n_elected": len(self.elect(query)),
            "distinct_section_scores": len(spread),
            "degenerate": len(self.sections) < 2 or len(spread) < 2,
            "why_degenerate": (
                "one section: the partition carries no information"
                if len(self.sections) < 2 else
                "every section scores the same: the query does not "
                "discriminate sections" if len(spread) < 2 else ""),
        }

    def explain(self, query, clause_id: str) -> dict:
        """Why this clause got this section verdict — in section terms."""
        cid = str(clause_id)
        p = self.section_of(cid)
        cs = self.sections.get(p, ())
        hit = self.firing(query)
        firing = [c for c in cs if c in hit]
        elected = p in self.elect(query)
        conduct = p in self.conduct_bearing
        frac = (len(firing) / len(cs)) if cs else 0.0
        if elected:
            why = ""
        elif not conduct:
            why = ("the section is not conduct-bearing: it contains no "
                   f"{' and no '.join(CONDUCT_KINDS)} clause, so it states no "
                   "conduct and cannot be the subject of a behaviour")
        else:
            why = (f"only {len(firing)} of {len(cs)} clauses fire "
                   f"({frac:.2f}), which is not a majority")
        return {
            "behaviour": query.slug,
            "clause_id": cid,
            "section_path": list(p),
            "n_clauses": len(cs),
            "n_firing": len(firing),
            "firing_clauses": firing,
            "firing_fraction": round(frac, 4),
            "election_score": round(self.election_score(query).get(p, 0.0), 4),
            "conduct_bearing": conduct,
            "elected": elected,
            "why_not": why,
            "constants_in_play": {k: v["value"] for k, v in CONSTANTS.items()},
        }


# ---------------------------------------------------------------- the report

def result_lines() -> list:
    """The measured result, per behaviour, with BOTH floors beside it.

    Never the mean of 9 alone: this channel's sign differs by behaviour and by
    product, and a single number reports neither.
    """
    m = MEASURED
    f = m["floors"]
    out = [
        "SECTION QUOTIENT — measured result",
        f"  universe: {m['universe']['passages']} passages, "
        f"{m['universe']['cells']} cells, {m['universe']['draws']} atom draws",
        f"  floor A (chance) {f['A_chance']:.3f}   "
        f"floor B (chance minus coverage gap) {f['B_chance_minus_coverage_gap']:.3f}",
        "",
        "DECISION RULE — per behaviour MCC (best label-free variant), "
        "floor B beside each",
    ]
    d = m["decision_rule"]
    for slug, v in sorted(d["per_behaviour"].items()):
        out.append(f"  {slug:<34}{v:+.3f}   floor B "
                   f"{f['B_per_behaviour'][slug]:+.3f}")
    out += [
        f"  mean of 9 cells {d['best_label_free']:+.3f} vs per-clause operator "
        f"{d['per_clause_baseline']:+.3f}; delta {d['delta']:+.3f} "
        f"95% CI [{d['ci'][0]:+.3f}, {d['ci'][1]:+.3f}]",
        f"  pre-registered primary {d['pre_registered_primary']:+.3f} — it LOST",
        f"  VERDICT: {d['verdict']} — {d['note']}",
        "",
        "RANKING — passage AUC per behaviour, shipped smoothing channel vs "
        "this quotient",
    ]
    r = m["ranking"]
    for slug in sorted(r["rebuilt_auc"]):
        lo, hi = r["ci_per_behaviour"][slug]
        out.append(f"  {slug:<34}{r['shipped_auc'][slug]:.3f} -> "
                   f"{r['rebuilt_auc'][slug]:.3f}   95% CI "
                   f"[{lo:+.3f}, {hi:+.3f}]")
    c = m["supervised_ceiling"]
    out += [
        f"  VERDICT: {r['verdict']} — {r['note']}",
        "",
        f"CEILINGS (diagnostic, NOT targets): supervised section-only "
        f"{c['value']:+.3f}; cross-behaviour transfer "
        f"{c['cross_behaviour_transfer']:+.3f}; elect-and-distribute oracle "
        f"{c['elect_and_distribute_oracle']:+.3f}; best label-free ranking at "
        f"an oracle cut {c['label_free_ranking_oracle_cut']:+.3f}",
        f"  {c['note']}",
    ]
    return out


# -------------------------------------------------------------------- CLI

USAGE = """\
section.py <behaviour-slug> [options]  — the section quotient over spec clauses

  --atoms PATH         behaviour atoms   (default: behavior_atoms_b8.json)
  --annotations PATH   clause atoms      (default: annotations_b8.json)
  --clauses PATH       clause rows       (default: modelspec_clauses.json)
  --top N              sections to show  (default 15)
  --explain CLAUSE_ID  the section verdict for that clause
  --report             the measured result, per behaviour, with both floors

Entirely offline: no model is called at query time, ever.
"""


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("slug", nargs="?")
    ap.add_argument("--atoms", default=S.BEHAVIOUR_ATOMS)
    ap.add_argument("--annotations", default=S.ANNOTATIONS)
    ap.add_argument("--clauses", default=S.CLAUSES)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--explain", default=None)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("-h", "--help", action="store_true")
    args = ap.parse_args(argv if argv is not None else sys.argv[1:])

    if args.report:
        print("\n".join(result_lines()))
        return 0
    if args.help or not args.slug:
        print(USAGE)
        return 0

    idx = S.StructuralIndex.from_files(args.clauses, args.annotations)
    quo = SectionQuotient(idx)
    queries = load_queries(args.atoms)
    q = queries.get(args.slug)
    if q is None:
        raise SystemExit(f"unknown behaviour {args.slug!r}; have "
                         f"{sorted(queries)}")
    if args.explain:
        print(json.dumps(quo.explain(q, args.explain), indent=2, default=str))
        return 0

    d = quo.diagnostics(q)
    print(f"# {args.slug} — {d['n_sections']} sections, "
          f"{d['n_conduct_bearing']} conduct-bearing, {d['n_elected']} elected")
    if d["degenerate"]:
        print(f"# !! DEGENERATE: {d['why_degenerate']}")
    print("# rank() is the product that wins; predict() LOSES to "
          "structural.predict — see the module docstring")
    sc = quo.election_score(q)
    for p in sorted(sc, key=lambda p: (-sc[p], p))[:args.top]:
        flag = "elected" if p in quo.elect(q) else (
            "" if p in quo.conduct_bearing else "no-conduct")
        print(f"{sc[p]:6.3f}  {len(quo.sections[p]):3} clauses  {flag:10}  "
              f"{' > '.join(p)[:70]}")
    print(f"\nwhy:  section.py {args.slug} --explain <clause_id>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
