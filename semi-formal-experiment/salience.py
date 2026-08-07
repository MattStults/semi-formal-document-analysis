"""SPEECH-ACT SALIENCE — the fourth tier of the lexicographic grade (R4).

WHAT THIS IS
------------
`HARNESS_REDESIGN.md` §0.0 grades a (clause, behaviour) pair lexicographically
over four discrete tiers — match completeness, derivation directness, license
strength, and **salience** — and §0.0a R4 rules what salience is:

    Salience is grounded in SPEECH ACT, never in a score. Core paragraphs state
    the rule; examples illustrate it. That is structural, not a weight.

This module is that tier and nothing else. It takes a ranking produced by the
existing label-free channel (`section.SectionQuotient.rank`, the best single
compliant ranker measured) and REORDERS it by the clause's `kind` — the speech
act the document itself records on all 593 clauses (conditional 188 · example
183 · definitional 84 · meta 72 · holistic 66).

⛔ WHAT IT MUST NEVER DO — ORDER, NEVER DROP
--------------------------------------------
R4 is explicit, and the number is why: examples carry **39.1%** of the
relevance-weighted hits, MORE than conditionals at 38.2%. Demoting examples out
of the result set would remove the largest single source of relevant material
and reinstate the conditional-only recall ceiling that `annotate.py` escapes.

So `rank()` is a PERMUTATION of the baseline's output. It receives the baseline
list and sorts it; it never filters, never adds, never rescores. R4 guard 1 —
*"set and order computed independently"* — is satisfied structurally: the set
comes from the baseline, this module only chooses the order, and `rank()`
asserts the identity before returning. `predict()` delegates untouched.

THE DEFAULT PRECEDENCE, AND WHY IT IS A DEFAULT AND NOT A POLICY
----------------------------------------------------------------
R4: *"make precedence configurable like any human-facing sort"* — and *"the
default is a product decision, the ordering nearly every user ever sees."*

Two things are configurable, and both are declared here:

* `kind_precedence` — the order of the speech acts inside the salience tier.
* `tier_order` — whether salience is applied inside the baseline's tiers
  (`("base", "salience")`, the default) or outside them
  (`("salience", "base")`).

DEFAULT_KIND_PRECEDENCE = conditional · definitional · holistic · example · meta

  R4 names four of the five kinds and their band structure directly:
  *"rule-stating (conditional, definitional) outranks illustrating (example)
  outranks commentary (meta)."* That fixes conditional and definitional above
  example above meta, and it is taken literally — including the order of the
  named pair, which is not reordered here.

  `holistic` is the one kind R4 does not name, so its placement is a judgment
  and is flagged as one. A holistic clause states a standing, unconditioned
  commitment; it is rule-stating, not illustration or commentary, so it belongs
  in the rule-stating band and above `example`. It is placed LAST within that
  band because the endorsed use case (§0.0b) is finding *the* governing passage
  — *"the initial strongest expression should outrank the others"* — and an
  unconditioned document-wide statement is the broadest, least site-specific
  expression of a rule. A user who wants the standing principle first changes
  one argument.

DEFAULT_TIER_ORDER = ("base", "salience")

  §0.0 lists salience as tier **4**, last. Under the default, salience refines
  the baseline's ties and can never lift a clause over a better-scoring one.
  That is not a cosmetic choice: `section.rank` is SECTION-CONSTANT by
  construction — every clause of a section carries the same number — so under
  the default this tier does its work exactly where the baseline is silent,
  ordering the rule above the example *inside* the elected section. That is
  §0.0b's *"many related + ~one core"* stated as a sort.

  `("salience", "base")` is offered for the user who wants every rule-stating
  clause in the document before any example. It is a real ordering, not a
  degenerate one, which is why it is exposed rather than hard-coded away.

THE FINAL TIE-BREAK IS DOCUMENT ORDER
-------------------------------------
§0.0: *"the final tie-break, after every configurable tier, is document order —
zero-parameter, document-grounded, deterministic."* It replaces the baseline's
clause-id sort, which is an artifact of how ids were minted, not a property of
the document. Document order is read from the index's own row order.

⛔ NOT MEASURED. This module ships unmeasured on purpose. Its default was fixed
from the speech-act argument above BEFORE any AUC/MCC/panel comparison existed,
and R4 guard 2 requires every reported number to name its ordering — see
`sort_order()`, which returns exactly the record a result must carry.

USAGE
-----
    import salience, section, structural
    base = section.SectionQuotient(structural.StructuralIndex.from_files())
    ranked = salience.Index(base).rank(query)          # [(clause_id, score)]
"""
from __future__ import annotations

import os

import section as SEC
import structural as S

HERE = os.path.dirname(os.path.abspath(__file__))

#: The speech acts the document records, strongest-stating first. R4 fixes
#: conditional/definitional > example > meta; `holistic` is placed by the
#: argument in the module docstring. This is a DEFAULT, not a policy — pass
#: `kind_precedence=` to change it.
DEFAULT_KIND_PRECEDENCE = ("conditional", "definitional", "holistic",
                           "example", "meta")

#: Which grade tier is the outer sort key. §0.0 puts salience last (tier 4).
DEFAULT_TIER_ORDER = ("base", "salience")

#: The tiers this module knows how to sort on. `base` is the incoming
#: label-free ranking; `salience` is this module's contribution.
TIERS = ("base", "salience")

#: Zero-parameter, always last, never configurable — see §0.0.
TIE_BREAK = "document_order"


def kind_tier(kind, precedence=None) -> int:
    """The salience tier of a speech act: 0 is the strongest stating act.

    A kind the precedence does not name — including a clause with no `kind` at
    all — gets the single trailing tier `len(precedence)`. It is ORDERED LAST,
    never dropped: an unrecognised speech act is a gap in the precedence, not a
    reason to remove a clause from a result set (R4).
    """
    prec = tuple(precedence or DEFAULT_KIND_PRECEDENCE)
    k = (kind or "").strip()
    return prec.index(k) if k in prec else len(prec)


def validate_precedence(precedence) -> tuple:
    """A precedence must be a duplicate-free sequence of names."""
    prec = tuple(str(k) for k in precedence)
    if not prec:
        raise ValueError("kind_precedence is empty: nothing would be ordered")
    if len(set(prec)) != len(prec):
        raise ValueError(
            f"kind_precedence names a kind twice: {prec}. A speech act has one "
            "tier; a duplicate makes the order depend on which one is found.")
    return prec


def validate_tier_order(tier_order) -> tuple:
    """A tier order must be a permutation of `TIERS` — every tier used once."""
    order = tuple(str(t) for t in tier_order)
    if sorted(order) != sorted(TIERS):
        raise ValueError(
            f"tier_order must be a permutation of {TIERS}, got {order}. "
            "Dropping a tier silently discards a grade dimension; repeating "
            "one makes the second copy dead.")
    return order


def load_queries(source=S.BEHAVIOUR_ATOMS) -> dict:
    """`{slug: structural.Query}`. Delegates — one loader, one place."""
    return SEC.load_queries(source)


class Index:
    """The salience tier layered over an existing label-free ranking.

    Wraps `section.SectionQuotient` (or anything exposing `rank(query)` and
    `predict(query)` over the same clause set). Accepts a `SectionQuotient`, a
    `structural.StructuralIndex`, or raw clause rows, so the repo's guard
    drivers can construct it the same way they construct every other query
    module.
    """

    def __init__(self, base, annotations=None, *, clauses=None,
                 kind_precedence=None, tier_order=None):
        if isinstance(base, SEC.SectionQuotient):
            self.base = base
        elif isinstance(base, S.StructuralIndex):
            self.base = SEC.SectionQuotient(base)
        else:
            self.base = SEC.SectionQuotient(
                S.StructuralIndex(base, annotations))

        self.kind_precedence = validate_precedence(
            kind_precedence if kind_precedence is not None
            else DEFAULT_KIND_PRECEDENCE)
        self.tier_order = validate_tier_order(
            tier_order if tier_order is not None else DEFAULT_TIER_ORDER)

        idx = self.base.index
        rows = {str(c.get("id")): c for c in idx.clauses}
        #: DOCUMENT ORDER — the index's own row order, which is the order the
        #: clauses appear in the document. Not the clause id: ids are minted,
        #: position is documented.
        self._doc_order = {cid: i for i, cid in enumerate(idx.ids)}
        self._kind = {cid: (rows.get(cid, {}).get("kind") or "")
                      for cid in idx.ids}

    # ------------------------------------------------------------- the tier

    def kind_of(self, clause_id) -> str:
        """The speech act the document records on this clause, `""` if none."""
        return self._kind.get(str(clause_id), "")

    def salience_tier(self, clause_id) -> int:
        """This clause's speech-act tier under the configured precedence."""
        return kind_tier(self.kind_of(clause_id), self.kind_precedence)

    def tiers(self) -> dict:
        """`{clause_id: tier}` for EVERY clause the index holds.

        Total by construction — a clause with an unknown or absent `kind` has
        the trailing tier, never no tier and never no entry. Whether a clause
        appears in a result is the derivation's business, not this map's.
        """
        return {cid: self.salience_tier(cid) for cid in self._doc_order}

    def _kind_key(self, clause_id):
        """Sub-key inside the salience tier.

        Unknown kinds share one tier, so they are further ordered by the kind
        STRING to stay deterministic when a document carries several of them.
        Known kinds contribute `""` and are separated by the tier alone.
        """
        t = self.salience_tier(clause_id)
        return (t, self.kind_of(clause_id) if t == len(self.kind_precedence)
                else "")

    def sort_order(self) -> dict:
        """⛔ R4 guard 2: the record a reported number must carry.

        *"Every reported number names its ordering... otherwise 'the core
        passage came first' is a claim about an order chosen after seeing it."*
        """
        return {
            "tier_order": list(self.tier_order),
            "kind_precedence": list(self.kind_precedence),
            "tie_break": TIE_BREAK,
            "baseline": "section.SectionQuotient.rank",
        }

    # ------------------------------------------------------------- ordering

    def _sort_key(self, clause_id, score):
        parts = {"base": (-float(score),), "salience": self._kind_key(clause_id)}
        key = ()
        for tier in self.tier_order:
            key = key + parts[tier]
        return key + (self._doc_order.get(clause_id, len(self._doc_order)),)

    def rank(self, query, baseline=None) -> list:
        """`[(clause_id, score)]` — the baseline's pairs, REORDERED.

        ⛔ ORDERING ONLY. The input list is permuted: no clause is added, no
        clause is dropped, and no score is touched. The assertion below is a
        cheap standing check of R4 guard 1, not documentation of one.
        """
        pairs = list(self.base.rank(query) if baseline is None else baseline)
        out = sorted(pairs, key=lambda kv: self._sort_key(kv[0], kv[1]))
        assert len(out) == len(pairs) and {c for c, _ in out} == {
            c for c, _ in pairs}, (
            "the salience sort changed the SET — membership is fixed by the "
            "derivation and this tier may only order within it (R4 guard 1)")
        return out

    # ----------------------------------------------------------- delegation

    def predict(self, query, *a, **kw) -> set:
        """The baseline's decision, untouched. Set and order are computed
        independently (R4 guard 1); this module owns only the order."""
        return self.base.predict(query, *a, **kw)

    def match(self, query, *a, **kw) -> dict:
        return self.base.match(query, *a, **kw)

    def sweep(self, query, *a, **kw) -> list:
        return self.base.sweep(query, *a, **kw)

    def diagnostics(self, query) -> dict:
        """The baseline's diagnostics plus whether THIS tier can discriminate.

        A result set whose clauses all share one speech act is a tier that
        cannot order anything, and it must say so rather than look like work.
        """
        out = dict(self.base.diagnostics(query))
        seen = {self.salience_tier(c) for c in self._doc_order}
        out.update({
            "distinct_salience_tiers": len(seen),
            "salience_degenerate": len(seen) < 2,
            "sort_order": self.sort_order(),
        })
        return out

    def explain(self, query, clause_id) -> dict:
        """Why this clause sits where it does — in speech-act terms."""
        cid = str(clause_id)
        base = self.base.explain(query, cid) if hasattr(self.base, "explain") \
            else {}
        prec = self.kind_precedence
        tier = self.salience_tier(cid)
        known = tier < len(prec)
        return {
            "clause_id": cid,
            "kind": self.kind_of(cid),
            "salience_tier": tier,
            "salience_of": (f"{prec[tier]} — position {tier + 1} of "
                            f"{len(prec)} in the configured precedence")
            if known else
            ("speech act not named by the configured precedence: ordered last, "
             "never dropped (R4)"),
            "document_order": self._doc_order.get(cid),
            "sort_order": self.sort_order(),
            "base": base,
        }


#: Alias — the repo's other query modules expose their ranker under a name that
#: says what it ranks.
SalienceIndex = Index
