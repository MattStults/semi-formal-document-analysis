"""Patient-aware match pricing — the pricing-v2.0 overlay (cycle 5 core).

Built to CYCLE5_REVIEW.md's MUST list; where CYCLE5_DESIGN.md disagrees with
the review, THE REVIEW WINS. This module houses the review-stable mechanism
only — the query-side `patients` declarations, the cycle manifest, and the
snapshot wiring land with the amended cycle, not here.

WHY THIS EXISTS. The atom channel cannot see WHO a clause protects: an
unmatched atom contributes 0, never a penalty, so a chain naming the WRONG
patient (`shouldnot_lie__model_user` on a query about third parties) prices
exactly like a right one. This overlay makes recorded patient structure PAY:
a mismatched chain discounts its own match, and a clause whose every chain is
mismatched taints all its atom credits — clause-side presence as
counter-evidence, the m0276 mechanism.

CHAIN SEMANTICS (review F1 — the finding that killed the design as written).
grammar.py's principal chains are AGENT-FIRST: `..__model_user` reads "the
MODEL acts, upon the USER" (grammar.describe). The patients of an atom are
therefore chain[1:], and ONLY for chains of length >= 2. A length-1 chain
records the agent — "the party concerned" — and carries NO patient: reading
its sole member as the patient is exactly the inversion the review computed
(m0276's `must_advise_immediate_help__user` parses as "the USER advises").
Length-1 chains price bit-identically to today (post-repair the artifact
carries exactly five, grandfathered and census-pinned).

VERSION LINEAGE: 2.0 IS DEFINED ON TOP OF 1.2 (PORTFOLIO_REVIEW F1; merge
reconciliation, S3). Under containment's PRICING_VERSION "1.2" — the S1
decoration-blind join — every principal chain is stripped from the match
key, the atom df/idf and the lexical documents BEFORE the base index is
built: `self._names` holds DECHAINED names only, and the stripped chains
survive solely as pricing metadata in `self.chains` ({clause_id:
{dechained name: [chain, ...]}}), preserved by containment expressly for
this layer. This module therefore reads clause-side patient structure from
`self.chains`, NEVER from the clause name set (which by 1.2's construction
can no longer carry a chain — reading names there is the dead-channel
failure, silently pricing nothing). A dechained clause atom can carry more
than one recorded chain (1.2's df-merge collapses a chained and a
chain-free spelling of one name); its patients are the union over its
length->=2 chains, so it is CONSISTENT when any of its chains names a
declared patient — the same one-consistent-chain-wins reading as the
clause-level taint guard. All explain records name the DECHAINED clause
atom: the name actually priced (containment's v1.2 explain policy).

THE RULE (PRICING_VERSION "2.0"), for a query with non-empty declared
patients P, on each clause:

  * PER-ATOM FACTOR. Each credited atom match through a clause atom `a`:
    patients_of(a) & P nonempty -> consistent, factor 1.0, bit-identical;
    patients_of(a) nonempty and disjoint from P -> mismatched, factor
    PATIENT_MISMATCH_DISCOUNT; patients_of(a) None (patient-free) -> 1.0
    from this layer.
  * CLAUSE TAINT. If the clause's annotation carries >= 1 patient-bearing
    (length->=2) chained atom and EVERY such atom is mismatched with P, the
    clause is uniformly mismatch-attested: every atom credit on it —
    patient-free matches included — is discounted. ONE consistent chain
    anywhere on the clause defeats the taint (the m0248 guard).
  * THE TAINT CAP (S3 mechanism amendment, DISCOUNT_DERIVATION.md §3-4).
    Under clause taint the clause's surviving atom mass is ONE discounted
    credit: tainted atom channel = d · max(base credits) / atom_norm, never
    d · Σ. Rationale (the F-linearity defect): d per match makes a densely
    decorated, uniformly wrong-patient clause retain residual mass LINEAR
    in how much of it the query matches — the clauses the document most
    wants suppressed retain the most. Uniform mismatch attestation is the
    strongest patient evidence a clause can carry; more mismatched chains
    mean more suppression, not linearly more residual. Mechanically: the
    argmax credited match keeps factor d; every other credited match on the
    tainted clause is zeroed (factor 0.0, why "taint_capped"). The capped
    mass is <= the per-match d·Σ, so monotone-downward (I2) and
    never-outprice are strictly preserved. Per-atom mismatch pricing on
    MIXED clauses (taint defeated by a consistent chain) is uncapped and
    unchanged: each mismatched match pays d.
  * SINGLE APPLICATION. Effective factor per credited match = d if (that
    atom mismatched) OR (clause tainted, argmax survivor), 0.0 for capped
    non-argmax credits on a tainted clause, else 1.0. Never d^2.
  * COMPOSITION WITH CONTAINMENT (review P4). A subsumption match's patient
    factor reads the CLAUSE atom's chain — the evidence actually paid for —
    and multiplies INSIDE the min-idf-capped credit:
        credit = min(idf(subsumer), idf(clause_atom)) * kind_factor
                 * patient_factor
    Both discounts <= 1, so the never-outprice invariant is UNWEAKENED, and
    the overlay cannot become a discount-dodging route: a patient-mismatched
    exact match and a subsumption through the same atom discount equally.
    `_license_edge` still rejects principal chains on either end of an edge
    NAME — but under the 1.2 join edge names are dechained spellings, and a
    dechained clause atom credited through an edge MAY carry recorded
    chains in `self.chains`. The design's operative rule (§1.6, first
    sentence) governs: the patient factor reads THAT clause atom's recorded
    chain — so under 1.2 the subsumption path IS reachable by per-atom
    mismatch whenever the credited clause atom's own chains mismatch. (The
    pre-1.2 worktree text claimed unreachability; that was a fact about the
    pre-join artifact shape, not a rule, and is superseded by this merge
    reconciliation.)
  * PATIENT-FREE CLAUSES (no length->=2 chains at all — the large majority)
    are priced exactly as today. Absence of decoration is never penalized
    (the design's option B, rejected with numbers).

MONOTONICITY IS A RAW-SCORE PROPERTY (review F3). All factors lie in
{0.0} ∪ [d, 1.0] (0.0 only for taint-capped non-argmax credits), so every
raw channel and raw total is monotone downward and stays >= 0 (invariant
I2, restated on RAW scores). Normalized scores are EXEMPT:
rank() divides by the corpus max, and when the argmax clause is tainted the
normalizer shrinks, so every untouched clause's NORMALIZED score rises.
Normalizer-driven bystander flips are a normalizer_drift fact for the
dossier, never a match_change.

THE CONSTANT. PATIENT_MISMATCH_DISCOUNT = 0.10, DERIVED and UNSWEEPABLE —
deliberately a module constant rather than a Weights field, so it can never
enter a sweep surface (any sweep selects against the panel and violates
contract invariant 9). LICENSING BASIS: cycles/patient-pricing-2026-08-04/
DISCOUNT_DERIVATION.md (frozen, sha-pinned in test_patient.py) — the
original hand-set 0.25 lost its license when the OPEN recomputation broke
the pre-registered d-plateau, and the design's own §1.4/Q6 remedy fired:
re-derivation from golden patient-contrast cases. Six contrast cases plus
two controls pinch the amended-mechanism (taint-capped) interval to the
degenerate [0.10, 0.11]; the recorded tie-break (equalize the binding (a)
single-atom ceilings 0.114/0.119 against the (b) floor 0.108; canonical
one-decimal value) gives d = 0.10. At d = 0.10 a wrong-patient match
prices at the corpus's incidental-lexical-overlap line: gone as a score
driver, present in the explain trail with an exact priced_credit. The
population is ADJUDICATED (109/109 chain-audit instances reviewed against
clause text; 264 S2-backfilled chains each with a validator-checked
verbatim license_quote and golden review). 0.0 is rejected: even over an
adjudicated population, outright exclusion would let one later-found-wrong
chain erase a clause's whole atom channel, where 0.10 leaves the error
bounded, visible, and repairable by a single rechain migration.

WHAT THIS MODULE MUST NEVER DO.
  * DEFAULT ON. `query_patients` is explicit and defaults to None; nothing
    here — or anywhere — silently reads a `patients` field off the query
    file. None/empty, or a slug with no declared patients, is BIT-IDENTICAL
    to ContainmentIndex (invariant I1) — which with edges=() is
    bit-identical to RelevanceIndex. Opt-in forever.
  * JUSTIFY A DECLARATION BY PANEL OUTCOMES. Declared patients are licensed
    by the query file's own prose (validate_query.py's anchor check, housed
    panel-blind per review F4), never by a panel number.
  * TOUCH THE EVALUATION PANEL. Query module outright: panel-blind, scanned
    forever by test_no_reference_leak.py.
"""
from __future__ import annotations

import containment
import grammar
import relevance

#: The pricing regime this module implements. "2.0" = patient-aware match
#: pricing over containment's "1.1" (unanimous-child kind inheritance).
#: Recorded in every patient-active snapshot's config identity by the cycle
#: wiring; snapshots recording <= 1.1 reconstruct through the old classes.
PRICING_VERSION = "2.0"

#: The per-atom mismatch factor d. DERIVED (DISCOUNT_DERIVATION.md — the
#: golden-derived degenerate interval [0.10, 0.11] under the taint cap,
#: tie-break as recorded there), UNSWEEPABLE — see the module docstring
#: (THE CONSTANT) before touching this; a sweep here is a contract
#: invariant 9 violation, not a tuning opportunity, and the derivation's
#: sha is test-pinned so a silent re-licensing is a loud test event.
PATIENT_MISMATCH_DISCOUNT = 0.10


def patients_of(name):
    """The patients an atom NAME records, or None when it records none.

    Review F1's reading, and only that reading: chains are agent-first, so
    patients exist ONLY on chains of length >= 2 and are frozenset(chain[1:])
    ("WHO: X acts, upon Y" — grammar.describe). A chainless name, an
    unparseable name, and a length-1 chain (agent only, "the party
    concerned") are all PATIENT-FREE: None, absent-is-absent, never
    defaulted — the same contract as grammar.role_of.
    """
    p = grammar.parse_name(name)
    if p["error"]:
        return None
    chain = p["principals"]
    if len(chain) < 2:
        return None
    return frozenset(chain[1:])


class PatientIndex(containment.ContainmentIndex):
    """ContainmentIndex plus patient-aware pricing in the atom channel.

    `query_patients` maps slug -> iterable of grammar.PRINCIPALS members (the
    declared patients of that query). None/empty — or a queried slug absent
    from the map, or mapped to an empty set — prices BIT-IDENTICALLY to
    ContainmentIndex: the discount path is not entered at all. Nothing
    constructs this with patients unless a caller opted in by name.
    """

    def __init__(self, clauses, annotations=None, weights=None, *,
                 edges=(), query_patients=None):
        super().__init__(clauses, annotations, weights, edges=edges)
        qp = {}
        for slug, pats in (query_patients or {}).items():
            pats = frozenset(str(p) for p in (pats or ()))
            unknown = sorted(pats - set(grammar.PRINCIPALS))
            if unknown:
                raise ValueError(
                    f"query_patients[{slug!r}] names {unknown} — declared "
                    f"patients must come from grammar.PRINCIPALS "
                    f"({', '.join(grammar.PRINCIPALS)}); the anchor check "
                    "lives in validate_query.py")
            if pats:
                qp[str(slug)] = pats
        self.query_patients = qp
        #: The declared set of the query being scored RIGHT NOW — empty
        #: outside channel_scores/explain, so a bare _atom_score call prices
        #: exactly as the base class does.
        self._active_patients = frozenset()
        #: Per clause: {DECHAINED atom name -> its patients} for every
        #: clause atom carrying at least one length->=2 chain. Read from the
        #: 1.2 join's preserved metadata (`self.chains`) — NEVER from
        #: `self._names`, which post-join holds dechained names only (a name
        #: read there can never carry a chain; reading names would silently
        #: price nothing — the dead-channel failure). Patients are the union
        #: over the name's length->=2 chains (one consistent chain wins,
        #: matching the taint guard). Length-1 chains are patient-free
        #: (review F1) and deliberately contribute NOTHING here.
        self._chain_patients = {}
        for cid, by_name in self.chains.items():
            m = {}
            for nm, chains in by_name.items():
                pa = frozenset(p for ch in chains if len(ch) >= 2
                               for p in ch[1:])
                if pa:
                    m[nm] = pa
            self._chain_patients[cid] = m

    @classmethod
    def from_files(cls, clauses_path=relevance.CLAUSES, annotations_path=None,
                   weights=None, *, edges=(), query_patients=None):
        """Same loading path as the base classes, plus the declared patients."""
        base = relevance.RelevanceIndex.from_files(
            clauses_path=clauses_path, annotations_path=annotations_path,
            weights=weights)
        return cls(base.clauses, base.annotations, weights, edges=edges,
                   query_patients=query_patients)

    # ------------------------------------------------------------- pricing

    def _clause_tainted(self, cid, P):
        """Uniformly mismatch-attested: >= 1 patient-bearing chain and none
        consistent. One consistent chain defeats the taint (m0248 guard)."""
        chains = self._chain_patients.get(cid) or {}
        return bool(chains) and all(not (pa & P) for pa in chains.values())

    def _priced_record(self, query_atom, clause_atom, match, base_credit,
                       tainted, P, d, cid):
        """One credited match, priced. Single application: d for (own
        mismatch) OR (clause taint), never d^2. On a tainted clause every
        patient-bearing chain is mismatched by definition, so `consistent`
        and `clause_taint` can never collide. `clause_atom` is the DECHAINED
        name actually priced; its patients come from this clause's recorded
        chain metadata (the 1.2 seam), never from the name itself."""
        pa = self._chain_patients.get(cid, {}).get(clause_atom)
        if pa is None:
            why = "clause_taint" if tainted else "patient_free"
            factor = d if tainted else 1.0
        elif pa & P:
            why, factor = "consistent", 1.0
        else:
            why, factor = "mismatched", d
        return {"query_atom": query_atom, "clause_atom": clause_atom,
                "match": match,
                "atom_patients": sorted(pa) if pa else [],
                "factor": factor, "why": why,
                "base_credit": base_credit,
                "priced_credit": base_credit * factor}

    def _patient_pricing(self, query_atoms, cid):
        """(tainted, chained_names, records) for one clause under the active
        declared set. The records mirror the base channel's crediting
        term-for-term: one exact record per (name, kind) query entry with a
        clause-side name match (idf * kind factor, the base formula), plus
        one record per subsumption match, base_credit = the containment
        credit (min-idf-capped, kind-priced). They are the objects
        _atom_score discounts, so explain can never drift from what scored.

        v1.2 seam: query atom names are DECHAINED at entry — the join key
        applies at every entry point, exactly as containment._atom_score
        dechains — so the records mirror the base crediting name-for-name
        (a chained and a chain-free spelling of one query name collapse to
        the single entry the base channel credits)."""
        query_atoms = {(containment.dechain_name(n), k)
                       for n, k in (query_atoms or ())}
        P = self._active_patients
        chains = self._chain_patients.get(cid) or {}
        tainted = bool(chains) and all(not (pa & P) for pa in chains.values())
        d = PATIENT_MISMATCH_DISCOUNT
        recs = []
        nk = self._name_kinds.get(cid) or {}
        if query_atoms and nk:
            kd = self.weights.kind_mismatch_discount
            for qname, qkind in sorted(query_atoms):
                kinds = nk.get(qname)
                if kinds is None:
                    continue
                idf = self.atom_idf.get(qname, 0.0)
                base = idf * (1.0 if (not qkind or qkind in kinds) else kd)
                recs.append(self._priced_record(
                    qname, qname, "exact", base, tainted, P, d, cid))
        for m in self._subsumption_matches(query_atoms, cid):
            recs.append(self._priced_record(
                m["query_atom"], m["clause_atom"], "subsumption",
                m["credit"], tainted, P, d, cid))
        if tainted and len(recs) > 1:
            # THE TAINT CAP (module docstring; DISCOUNT_DERIVATION.md §4):
            # on a uniformly mismatch-attested clause the surviving atom
            # mass is ONE discounted credit — the argmax base credit keeps
            # factor d, every other credited match is zeroed. Deterministic
            # survivor: highest base_credit, ties broken lexicographically
            # on (clause_atom, query_atom, match). On a tainted clause no
            # record can be consistent, so the cap zeroes only discounted
            # records — factors after the cap lie in {0.0, d}.
            survivor = min(range(len(recs)),
                           key=lambda i: (-recs[i]["base_credit"],
                                          recs[i]["clause_atom"],
                                          recs[i]["query_atom"],
                                          recs[i]["match"]))
            for i, r in enumerate(recs):
                if i != survivor:
                    r["factor"] = 0.0
                    r["why"] = "taint_capped"
                    r["priced_credit"] = 0.0
        return tainted, sorted(chains), recs

    def _atom_score(self, query_atoms, cid):
        """The base (containment) score, minus exactly the penalties the
        patient_pricing records carry:

            priced = base - sum(base_credit - priced_credit
                                over discounted records) / atom_norm

        Written as a SUBTRACTION from the base sum — not a re-summation — so
        that when no record is discounted the returned float is the base
        class's float, bit for bit (invariants I1 and I2-equality), and so
        the explain records reconstruct the priced score exactly."""
        score = super()._atom_score(query_atoms, cid)
        P = self._active_patients
        if not P:
            return score
        _, _, recs = self._patient_pricing(query_atoms, cid)
        penalty = sum(r["base_credit"] - r["priced_credit"]
                      for r in recs if r["factor"] != 1.0)
        if penalty == 0.0:
            return score
        return score - penalty / self._atom_norm

    # ------------------------------------------------------------- surface

    def channel_scores(self, behaviour):
        """The base decomposition, scored under this behaviour's declared
        patients. The section channel recomputes from the discounted local
        totals exactly as it always has — section is defined over local
        scores, not frozen against them — so taint propagates to
        section-mates monotonically (all factors <= 1)."""
        self._active_patients = self.query_patients.get(
            behaviour.slug, frozenset())
        try:
            return super().channel_scores(behaviour)
        finally:
            self._active_patients = frozenset()

    def explain(self, behaviour, clause_id):
        """The containment payload plus `patient_pricing` (only when this
        behaviour declares patients — absent is absent, the I1 surface):
        the clause-level taint status, the chained atoms that produced it,
        and one sum-exact record per credited match {query_atom, clause_atom,
        match, atom_patients, factor, why, base_credit, priced_credit} with
        why in consistent|mismatched|clause_taint|patient_free. The records
        ARE the objects _atom_score discounted (the Unit 4.1 contract)."""
        out = super().explain(behaviour, clause_id)
        P = self.query_patients.get(behaviour.slug, frozenset())
        if not P:
            return out
        qatoms = {(a["name"], a["kind"]) for a in behaviour.norm_atoms}
        cid = str(clause_id)
        self._active_patients = P
        try:
            tainted, chained, recs = self._patient_pricing(qatoms, cid)
        finally:
            self._active_patients = frozenset()
        cp = self._chain_patients.get(cid, {})
        out["patient_pricing"] = {
            "declared_patients": sorted(P),
            "clause_tainted": tainted,
            "chained_atoms": [
                {"name": n, "patients": sorted(cp[n]),
                 "chains": [list(ch) for ch in self.chains[cid][n]
                            if len(ch) >= 2]}
                for n in chained],
            "matches": recs,
        }
        return out


#: The drivable query surface, so the repo's anti-cheat spy
#: (test_no_reference_leak.py) can exercise this module like every other
#: query module — the same accommodation containment.py ships.
Index = PatientIndex
