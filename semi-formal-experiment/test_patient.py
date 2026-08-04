"""Tests for patient.py — patient-aware match pricing (pricing v2.0).

Spec: CYCLE5_REVIEW.md (the MUST list WINS over CYCLE5_DESIGN.md wherever
they disagree). What is pinned, and which review finding pins it:

  * CHAIN SEMANTICS (review F1) — grammar chains are AGENT-FIRST; patients
    are read ONLY from length->=2 chains, as chain[1:]. A length-1 chain
    records NO patient (patient-free), because the sole member is the AGENT
    ("the party concerned"), not the protected party — the m0276 annotation
    `must_advise_immediate_help__user` misused exactly that convention.
  * I1 — OPT-IN IDENTITY. query_patients None/{}/no entry for the queried
    slug => bit-identical to ContainmentIndex, pinned at recorded precision
    on the REAL artifacts exactly like containment's empty-overlay test
    (byte-level on the canonically serialized PRECISION-rounded channels).
  * I2 — MONOTONE-DOWNWARD ON RAW SCORES ONLY (review F3). All factors lie
    in [d, 1.0], so every raw channel and raw total can only go down or hold,
    and stays >= 0. NORMALIZED scores are EXEMPT by design: rank() divides by
    the corpus max, and when the argmax clause is itself tainted the
    normalizer shrinks, so every UNTOUCHED clause's normalized score RISES —
    monotonicity is a raw-score property, and normalizer-driven bystander
    flips are a threshold/normalizer question (the amended design's
    normalizer_drift annotation), never a match_change.
  * PER-ATOM FACTOR d = 0.25 — module constant, HAND-SET, UNSWEEPABLE
    (sweeping it selects against the panel, contract invariant 9).
  * CLAUSE TAINT (the m0276 mechanism) — a clause whose every length->=2
    chained atom is patient-mismatched taints ALL atom credits on it
    (patient-free matches included) by d; ONE consistent chain defeats the
    taint (the m0248 guard).
  * SINGLE APPLICATION — a credited match pays d ONCE, for (own mismatch) OR
    (clause taint), never d^2.
  * I4 / P4 COMPOSITION — the patient factor multiplies INSIDE the
    min-idf-capped subsumption credit; subsumers are chain-free by licensing,
    so the subsumption path is UNREACHABLE by per-atom mismatch: only clause
    taint can discount it. MUTANT TARGET: dropping the patient factor from
    the subsumption path must turn test_tainted_clause_discounts_subsumption
    _credit_inside_the_cap red.
  * EXPLAIN SUM-EXACTNESS — explain()'s patient_pricing records are the
    objects the scorer summed: priced atom channel ==
    base_atom - sum(base_credit - priced_credit over discounted records) /
    atom_norm, exactly.

MERGE RECONCILIATION (S3, 2026-08-04): pricing 2.0 is defined ON TOP of the
S1 decoration-blind join (containment PRICING_VERSION "1.2"), which landed
AFTER this suite was written in the worktree. Under 1.2 every clause-side
name is DECHAINED and the stripped chains survive only as pricing metadata
(ContainmentIndex.chains); patient.py reads patient structure from that
metadata, and every explain record names the DECHAINED clause atom (the
name actually priced — containment's own v1.2 explain policy). The
fixtures below that pin explain-record keys therefore pin dechained names;
and the pre-1.2 claim that the subsumption path is unreachable by per-atom
mismatch is superseded — under the join, a dechained clause atom credited
through an edge MAY carry recorded chains, and the design's operative rule
(CYCLE5_DESIGN §1.6, first sentence: the patient factor reads THAT clause
atom's chain) governs. Both directions are pinned below.
"""
from __future__ import annotations

import json
import os

import pytest

import containment
import patient
import relevance
import snapshot

HERE = os.path.dirname(os.path.abspath(__file__))
REAL_ANN = os.path.join(HERE, "annotations_b8.json")
REAL_ATOMS = os.path.join(HERE, "behavior_atoms_b8.json")
REAL_OVERLAY = os.path.join(HERE, "containment.json")

#: Wide stopword ceiling so tiny fixtures exercise idf pricing rather than
#: the stopword floor — same accommodation test_containment.py ships.
W = relevance.Weights(atom_stopword_frac=1.0)

FAMILY_EDGES = (("psychological_manipulation", "manipulation"),
                ("targeted_political_manipulation", "manipulation"))

D = 0.10  # the pinned constant, restated locally so the pin is two-sided
          # (derived: DISCOUNT_DERIVATION.md, sha-pinned below)


def _rp(x):
    """Round at the RECORDED precision (snapshot.PRECISION). Multiplicative
    x == D * y pins are compared here: the scorer applies the discount as a
    subtraction from the base sum (so undiscounted paths stay bit-identical),
    which differs from a literal 0.25*y by float associativity in the last
    ulp — far below the precision every snapshot freezes and every diff
    compares (same rationale as containment's empty-overlay test). Bit-level
    identity claims (factor-1.0 paths) still use raw ==."""
    return round(x, snapshot.PRECISION) + 0.0


def _clauses(n, sect="s"):
    return [{"id": f"c{i}", "quote": f"filler text number {i} entirely bland",
             "section_path": [sect], "locator": f"L{i}"}
            for i in range(1, n + 1)]


def _atom(name, kind="act"):
    return {"name": name, "kind": kind, "gloss": f"gloss of {name}"}


def _beh(*names, slug="q"):
    return relevance.Behaviour(slug=slug, name="query", definition="",
                               atoms=[_atom(n) for n in names])


def _pair(clauses, ann, patients, *, edges=()):
    """(ContainmentIndex, PatientIndex) over identical inputs; `patients` is
    the declared set for slug 'q'."""
    base = containment.ContainmentIndex(clauses, ann, W, edges=edges)
    idx = patient.PatientIndex(clauses, ann, W, edges=edges,
                               query_patients={"q": patients})
    return base, idx


# ------------------------------------------------------- chain semantics (F1)

def test_patients_read_only_from_length_2_chains():
    """Review F1: agent-first; patients = chain[1:]; length-1 = patient-free."""
    assert patient.patients_of("must_advise_help__model_user") == {"user"}
    assert patient.patients_of(
        "x__model_user_third_party") == {"user", "third_party"}
    # a length-1 chain names the AGENT, not a patient — the m0276 misreading
    assert patient.patients_of("must_advise_immediate_help__user") is None
    assert patient.patients_of("advise_help__user") is None


def test_chainless_and_unparseable_names_are_patient_free():
    assert patient.patients_of("human_safety") is None
    assert patient.patients_of("must_") is None          # unparseable
    assert patient.patients_of("x__nobody_state") is None  # bad chain token
    assert patient.patients_of("") is None


# ----------------------------------------------------------- module identity

def test_pricing_version_is_2_0_and_distinct_from_containment():
    assert patient.PRICING_VERSION == "2.0"
    assert patient.PRICING_VERSION != containment.PRICING_VERSION


def test_discount_constant_is_a_pinned_module_constant():
    """d = 0.25, module-level, NOT a Weights field: it must never enter any
    sweep surface (unsweepable by construction, contract invariant 9)."""
    assert patient.PATIENT_MISMATCH_DISCOUNT == D
    assert "patient_mismatch_discount" not in vars(relevance.Weights())


def test_constructor_rejects_a_patient_outside_grammar_principals():
    with pytest.raises(ValueError):
        patient.PatientIndex(_clauses(2), {}, W,
                             query_patients={"q": {"stranger"}})


# --------------------------------------------------------- I1: opt-in identity

def _frozen_channels(idx, behaviours) -> bytes:
    """Canonical bytes of every behaviour's rounded channel decomposition —
    the same numbers a snapshot records, serialized the same way (the byte
    standard test_containment.py's empty-overlay test pins)."""
    out = {}
    for slug in sorted(behaviours):
        ch = idx.channel_scores(behaviours[slug])
        out[slug] = {cid: {k: round(v, snapshot.PRECISION) + 0.0
                           for k, v in ch[cid].items()}
                     for cid in sorted(ch)}
    return json.dumps(out, sort_keys=True).encode()


@pytest.mark.parametrize("qp", [None, {}])
def test_I1_no_patients_is_byte_identical_to_containment_on_real_artifacts(qp):
    """The I1 invariant, pinned byte-level on the real artifacts exactly like
    containment's empty-overlay test: no declared patients => the recorded
    (PRECISION-rounded, canonically serialized) channels are IDENTICAL."""
    if not (os.path.exists(REAL_ANN) and os.path.exists(REAL_ATOMS)):
        pytest.skip("real artifacts not present")
    edges = containment.load_edges(REAL_OVERLAY) \
        if os.path.exists(REAL_OVERLAY) else ()
    base = containment.ContainmentIndex.from_files(
        annotations_path=REAL_ANN, edges=edges)
    over = patient.PatientIndex.from_files(
        annotations_path=REAL_ANN, edges=edges, query_patients=qp)
    behs = snapshot.load_behaviours(REAL_ATOMS)
    assert behs, "no behaviours with atoms — the comparison would be vacuous"
    assert base.atom_df == over.atom_df
    assert base.atom_idf == over.atom_idf
    assert _frozen_channels(base, behs) == _frozen_channels(over, behs)


def test_I1_slug_without_declared_patients_is_bit_identical():
    """Patients declared for ANOTHER slug leave this query's scores the exact
    floats the base class computes (same code path, not just same rounding)."""
    clauses = _clauses(3)
    ann = {"c1": [_atom("human_safety"),
                  _atom("must_advise_help__model_user")]}
    base = containment.ContainmentIndex(clauses, ann, W)
    idx = patient.PatientIndex(clauses, ann, W,
                               query_patients={"other": {"third_party"}})
    beh = _beh("human_safety")
    assert idx.channel_scores(beh) == base.channel_scores(beh)
    assert idx.raw_scores(beh) == base.raw_scores(beh)


def test_I1_empty_declared_set_disables_pricing_for_that_slug():
    clauses = _clauses(3)
    ann = {"c1": [_atom("human_safety"),
                  _atom("must_advise_help__model_user")]}
    base = containment.ContainmentIndex(clauses, ann, W)
    idx = patient.PatientIndex(clauses, ann, W, query_patients={"q": ()})
    beh = _beh("human_safety")
    assert idx.channel_scores(beh) == base.channel_scores(beh)


# ------------------------------------------------- the per-atom factor + taint

def test_mismatched_chained_exact_match_pays_d_once_never_d_squared():
    """The clause's only chained atom is mismatched, so the clause is ALSO
    uniformly mismatch-attested — and the credited match still pays exactly
    d, once: factor = d if (mismatched OR tainted), NEVER d^2."""
    clauses = _clauses(3)
    ann = {"c1": [_atom("shouldnot_lie__model_user")]}
    base, idx = _pair(clauses, ann, {"third_party"})
    beh = _beh("shouldnot_lie__model_user")
    cb = base.channel_scores(beh)
    cp = idx.channel_scores(beh)
    assert _rp(cp["c1"]["atom"]) == _rp(D * cb["c1"]["atom"])
    assert cb["c1"]["atom"] > 0.0


def test_consistent_chained_exact_match_is_bit_identical():
    """I1's per-match face: a patient-consistent match is priced bit-identical
    to today — and a clause carrying a consistent chain is never tainted."""
    clauses = _clauses(3)
    ann = {"c1": [_atom("shouldnot_lie__model_user"), _atom("human_safety")]}
    base, idx = _pair(clauses, ann, {"user"})
    beh = _beh("shouldnot_lie__model_user", "human_safety")
    assert idx.channel_scores(beh) == base.channel_scores(beh)
    assert idx.raw_scores(beh) == base.raw_scores(beh)


def test_uniformly_mismatched_clause_taints_patient_free_matches():
    """The m0276 mechanism: the clause's every chained atom names a patient
    outside P, so the patient-free stock atoms on it inherit the recorded
    context and pay d."""
    clauses = _clauses(3)
    ann = {"c1": [_atom("must_advise_help__model_user"),
                  _atom("human_safety")],
           "c2": [_atom("human_safety")]}
    base, idx = _pair(clauses, ann, {"third_party"})
    beh = _beh("human_safety")
    cb = base.channel_scores(beh)
    cp = idx.channel_scores(beh)
    assert _rp(cp["c1"]["atom"]) == _rp(D * cb["c1"]["atom"])
    assert cb["c1"]["atom"] > 0.0
    # the chain-free clause is untouched: absence of decoration is never
    # penalized (option B rejected, CYCLE5_DESIGN.md section 1.3)
    assert cp["c2"]["atom"] == cb["c2"]["atom"]


def test_one_consistent_chain_defeats_the_taint():
    """The m0248 guard: ANY consistent chain on the clause defeats the taint,
    so its patient-free matches are priced bit-identically to today."""
    clauses = _clauses(3)
    ann = {"c1": [_atom("must_advise_help__model_user"),
                  _atom("may_lie_by_omission__model_third_party"),
                  _atom("human_safety")]}
    base, idx = _pair(clauses, ann, {"third_party"})
    beh = _beh("human_safety")
    assert idx.channel_scores(beh)["c1"]["atom"] \
        == base.channel_scores(beh)["c1"]["atom"]


def test_length_1_chains_never_produce_mismatch_or_taint():
    """Review F1 at the mechanism level: length-1 chains are PATIENT-FREE, so
    the shipped m0276-shaped annotation (`..__user`) neither mismatches nor
    taints — it prices bit-identically until the backfill re-chains it."""
    clauses = _clauses(3)
    ann = {"c1": [_atom("must_advise_immediate_help__user"),
                  _atom("human_safety")]}
    base, idx = _pair(clauses, ann, {"third_party"})
    beh = _beh("human_safety", "must_advise_immediate_help__user")
    assert idx.channel_scores(beh) == base.channel_scores(beh)


# ------------------------------------------------------- I2 on RAW scores (F3)

def test_I2_raw_scores_monotone_downward_and_never_below_zero():
    """Restated per review F3: for every clause, raw_v2.0 <= raw_v1.1, every
    channel >= 0. Normalized scores are EXEMPT (see module docstring: the
    corpus-max normalizer moves when the argmax clause is tainted, so
    untouched clauses' normalized scores RISE — a normalizer fact, not a
    pricing regression)."""
    clauses = _clauses(4)
    ann = {"c1": [_atom("must_advise_help__model_user"),
                  _atom("human_safety")],
           "c2": [_atom("shouldnot_lie__model_user")],
           "c3": [_atom("human_safety")]}
    base, idx = _pair(clauses, ann, {"third_party"})
    beh = _beh("human_safety", "shouldnot_lie__model_user")
    rb, rp = base.raw_scores(beh), idx.raw_scores(beh)
    for cid in rb:
        assert rp[cid] <= rb[cid], cid
        assert rp[cid] >= 0.0, cid
    for cid, ch in idx.channel_scores(beh).items():
        for name, v in ch.items():
            assert v >= 0.0, (cid, name)
    # the discount really fired somewhere, or this test is vacuous
    assert rp["c1"] < rb["c1"]


def test_I2_normalized_scores_are_exempt_by_design():
    """The F3 fact itself, constructed: taint the argmax clause and an
    UNTOUCHED clause's normalized score rises. Pinned so nobody 'fixes' raw
    monotonicity by asserting it on rank()'s output."""
    clauses = _clauses(4)
    ann = {"c1": [_atom("must_advise_help__model_user"),
                  _atom("rare_treasure"), _atom("human_safety")],
           "c2": [_atom("human_safety")]}
    base, idx = _pair(clauses, ann, {"third_party"})
    beh = _beh("human_safety", "rare_treasure")
    nb, np_ = dict(base.rank(beh)), dict(idx.rank(beh))
    # c1 (tainted) is the argmax on both sides; untouched c2 RISES normalized
    assert np_["c2"] > nb["c2"]


# --------------------------------------- I4/P4: composition with containment

def test_tainted_clause_discounts_subsumption_credit_inside_the_cap():
    """P4: the patient factor multiplies INSIDE the min-idf-capped credit —
    priced subsumption credit == d * containment's credit, exactly once.
    I4 MUTANT TARGET: dropping the patient factor from the subsumption path
    (or applying it twice) turns this red."""
    clauses = _clauses(4)
    ann = {"c1": [_atom("targeted_political_manipulation"),
                  _atom("must_guard__model_user")],
           "c2": [_atom("psychological_manipulation")]}
    base, idx = _pair(clauses, ann, {"third_party"}, edges=FAMILY_EDGES)
    beh = _beh("psychological_manipulation")  # no exact match on c1
    cb = base.channel_scores(beh)
    cp = idx.channel_scores(beh)
    assert cb["c1"]["atom"] > 0.0, "subsumption never fired — vacuous"
    assert _rp(cp["c1"]["atom"]) == _rp(D * cb["c1"]["atom"])


def test_chain_free_subsumption_clause_atom_is_never_itself_mismatched():
    """A subsumption match through a clause atom with NO recorded chain can
    only be discounted by clause taint, never per-atom mismatch. Pinned on
    the explain records' `why`. (Edge NAMES still cannot carry chains —
    _license_edge rejects them — but under the 1.2 join that no longer makes
    the subsumption path unreachable by mismatch: see the next test.)"""
    clauses = _clauses(4)
    ann = {"c1": [_atom("targeted_political_manipulation"),
                  _atom("must_guard__model_user")]}
    _, idx = _pair(clauses, ann, {"third_party"}, edges=FAMILY_EDGES)
    beh = _beh("psychological_manipulation")
    recs = idx.explain(beh, "c1")["patient_pricing"]["matches"]
    subs = [r for r in recs if r["match"] == "subsumption"]
    assert subs, "no subsumption record — vacuous"
    for r in subs:
        assert r["why"] in ("patient_free", "clause_taint")
        assert r["why"] != "mismatched"
    # and licensing still rejects any chained edge-end NAME
    with pytest.raises(ValueError):
        containment._license_edge("bad_guard__model_user", "guard",
                                  "shared_head")


def test_subsumption_match_reads_the_credited_clause_atoms_own_chain():
    """The 1.2-seam consequence of CYCLE5_DESIGN §1.6's operative rule: the
    patient factor reads THE CREDITED CLAUSE ATOM's recorded chain. Under
    the decoration-blind join a chained annotation instance is stored under
    its dechained name, so it CAN be edge-licensed — and when its own chain
    mismatches P while the clause taint is defeated by a consistent chain
    elsewhere, the subsumption credit still pays d for the atom's OWN
    mismatch (per-atom, not taint)."""
    clauses = _clauses(4)
    ann = {"c1": [_atom("targeted_political_manipulation__model_user"),
                  _atom("may_lie_by_omission__model_third_party")]}
    base, idx = _pair(clauses, ann, {"third_party"}, edges=FAMILY_EDGES)
    beh = _beh("psychological_manipulation")   # no exact match on c1
    cb = base.channel_scores(beh)
    cp = idx.channel_scores(beh)
    assert cb["c1"]["atom"] > 0.0, "subsumption never fired — vacuous"
    assert _rp(cp["c1"]["atom"]) == _rp(D * cb["c1"]["atom"])
    recs = idx.explain(beh, "c1")["patient_pricing"]["matches"]
    subs = [r for r in recs if r["match"] == "subsumption"]
    assert subs and all(r["why"] == "mismatched" for r in subs)
    assert all(r["clause_atom"] == "targeted_political_manipulation"
               for r in subs), "records must name the DECHAINED clause atom"
    # taint really was defeated — the discount above is per-atom, not taint
    assert idx.explain(beh, "c1")["patient_pricing"]["clause_tainted"] \
        is False


def test_consistent_chain_leaves_subsumption_bit_identical():
    clauses = _clauses(4)
    ann = {"c1": [_atom("targeted_political_manipulation"),
                  _atom("may_lie_by_omission__model_third_party"),
                  _atom("must_guard__model_user")]}
    base, idx = _pair(clauses, ann, {"third_party"}, edges=FAMILY_EDGES)
    beh = _beh("psychological_manipulation")
    assert idx.channel_scores(beh)["c1"]["atom"] \
        == base.channel_scores(beh)["c1"]["atom"]


# ------------------------------------------------------------------- explain

def test_explain_patient_pricing_records_are_sum_exact():
    """The records ARE the objects the scorer summed: priced atom channel ==
    w.atom * (base_atom - sum(base-priced over discounted records)/norm),
    float-exactly."""
    clauses = _clauses(4)
    ann = {"c1": [_atom("must_advise_help__model_user"),
                  _atom("human_safety"),
                  _atom("shouldnot_lie__model_user")]}
    base, idx = _pair(clauses, ann, {"third_party"})
    beh = _beh("human_safety", "shouldnot_lie__model_user")
    info = idx.explain(beh, "c1")
    pp = info["patient_pricing"]
    assert pp["declared_patients"] == ["third_party"]
    assert pp["clause_tainted"] is True
    # chained_atoms name the DECHAINED clause atoms (the names actually
    # priced under the 1.2 join), each carrying its recorded chains
    assert {a["name"] for a in pp["chained_atoms"]} == {
        "must_advise_help", "shouldnot_lie"}
    assert all(a["chains"] and a["patients"] == ["user"]
               for a in pp["chained_atoms"])
    penalty = sum(r["base_credit"] - r["priced_credit"]
                  for r in pp["matches"] if r["factor"] != 1.0)
    qatoms = {(a["name"], a["kind"]) for a in beh.norm_atoms}
    expected = base._atom_score(qatoms, "c1") - penalty / idx._atom_norm
    assert info["channels"]["atom"] == W.atom * expected
    # every record carries the audit fields, factor in {0.0, d, 1.0} (0.0
    # only for taint-capped non-argmax credits — the S3 amendment)
    for r in pp["matches"]:
        assert r["factor"] in (0.0, D, 1.0)
        assert r["why"] in ("consistent", "mismatched", "clause_taint",
                            "patient_free", "taint_capped")


def test_explain_omits_patient_pricing_when_no_patients_declared():
    """Absent is absent (the role_of contract): no declared patients, no
    patient_pricing key — the payload is the ContainmentIndex payload."""
    clauses = _clauses(3)
    ann = {"c1": [_atom("human_safety")]}
    idx = patient.PatientIndex(clauses, ann, W)
    out = idx.explain(_beh("human_safety"), "c1")
    assert "patient_pricing" not in out


def test_explain_why_classification_per_record():
    clauses = _clauses(3)
    ann = {"c1": [_atom("shouldnot_lie__model_user"), _atom("human_safety"),
                  _atom("may_lie_by_omission__model_third_party")]}
    _, idx = _pair(clauses, ann, {"third_party"})
    beh = _beh("shouldnot_lie__model_user", "human_safety",
               "may_lie_by_omission__model_third_party")
    recs = idx.explain(beh, "c1")["patient_pricing"]["matches"]
    # records key by the DECHAINED clause atom — the name actually priced
    why = {r["clause_atom"]: r["why"] for r in recs}
    assert why["may_lie_by_omission"] == "consistent"
    assert why["shouldnot_lie"] == "mismatched"
    assert why["human_safety"] == "patient_free"   # taint defeated


# ----------------------- the taint cap + the derived constant (S3 amendment)

#: The frozen derivation artifact that LICENSES the constant (designer
#: ruling, patient-pricing-2026-08-04): golden patient-contrast cases pinch
#: the amended-mechanism interval to the degenerate [0.10, 0.11]; tie-break
#: as recorded there. Editing the derivation IS editing the license — the
#: sha pin below makes that a loud test event, never a drive-by.
DERIVATION = os.path.join(HERE, "cycles", "patient-pricing-2026-08-04",
                          "DISCOUNT_DERIVATION.md")
DERIVATION_SHA = ("7e1979bc4505103eea58a138053e78a72ecdd7620a13f80cdc"
                  "369a3d81df283e")


def test_discount_constant_is_derived_0_10_pinned_to_the_derivation():
    """d = 0.10 per DISCOUNT_DERIVATION.md §4 (the golden-derived degenerate
    interval under the taint cap), pinned against the derivation's bytes."""
    import hashlib
    assert patient.PATIENT_MISMATCH_DISCOUNT == 0.10
    with open(DERIVATION, "rb") as f:
        assert hashlib.sha256(f.read()).hexdigest() == DERIVATION_SHA


def test_tainted_clause_mass_is_capped_not_linear_in_match_count():
    """The F-linearity defect (DISCOUNT_DERIVATION §3): under d·Σ, a densely
    decorated uniformly-mismatched clause retains residual atom mass
    PROPORTIONAL to how much of it the query matches — the clauses the
    document most wants suppressed retain the most. Amended rule: under
    clause taint the surviving atom mass is ONE discounted credit,
    d · max(base credits), never d · Σ. Three equal-idf mismatched matches
    must therefore price at d·(base/3), not d·base."""
    d = patient.PATIENT_MISMATCH_DISCOUNT
    clauses = _clauses(3)
    ann = {"c1": [_atom("must_advise_help__model_user"),
                  _atom("shouldnot_lie__model_user"),
                  _atom("must_guard__model_user")]}
    base, idx = _pair(clauses, ann, {"third_party"})
    beh = _beh("must_advise_help__model_user", "shouldnot_lie__model_user",
               "must_guard__model_user")
    cb = base.channel_scores(beh)
    cp = idx.channel_scores(beh)
    assert cb["c1"]["atom"] > 0.0
    # equal df (each name only on c1) => equal idf => max = sum/3
    assert _rp(cp["c1"]["atom"]) == _rp(d * cb["c1"]["atom"] / 3)
    assert _rp(cp["c1"]["atom"]) != _rp(d * cb["c1"]["atom"]), \
        "d*sum and d*max coincide — fixture is vacuous"
    # the explain records ARE the capped objects: exactly one survivor at
    # factor d, the rest zeroed with why == taint_capped
    recs = idx.explain(beh, "c1")["patient_pricing"]["matches"]
    assert sorted(r["factor"] for r in recs) == sorted([d, 0.0, 0.0])
    capped = [r for r in recs if r["factor"] == 0.0]
    assert all(r["why"] == "taint_capped" and r["priced_credit"] == 0.0
               for r in capped)


def test_mixed_clause_per_atom_pricing_is_uncapped():
    """The cap is a TAINT rule only (designer ruling): on a mixed clause
    (taint defeated by a consistent chain) every mismatched match still pays
    d per match — two mismatched matches lose two discounted credits."""
    d = patient.PATIENT_MISMATCH_DISCOUNT
    clauses = _clauses(3)
    ann = {"c1": [_atom("must_advise_help__model_user"),
                  _atom("shouldnot_lie__model_user"),
                  _atom("may_lie_by_omission__model_third_party")]}
    base, idx = _pair(clauses, ann, {"third_party"})
    beh = _beh("must_advise_help__model_user", "shouldnot_lie__model_user",
               "may_lie_by_omission__model_third_party")
    recs = idx.explain(beh, "c1")["patient_pricing"]["matches"]
    why = {r["clause_atom"]: (r["why"], r["factor"]) for r in recs}
    assert why["may_lie_by_omission"] == ("consistent", 1.0)
    assert why["must_advise_help"] == ("mismatched", d)
    assert why["shouldnot_lie"] == ("mismatched", d)
    # sum-exact: BOTH mismatched credits are discounted (no cap here)
    cb = base.channel_scores(beh)
    cp = idx.channel_scores(beh)
    assert cp["c1"]["atom"] < cb["c1"]["atom"]
    penalty = sum(r["base_credit"] - r["priced_credit"] for r in recs
                  if r["factor"] != 1.0)
    assert len([r for r in recs if r["factor"] != 1.0]) == 2
    assert _rp(cp["c1"]["atom"]) == _rp(cb["c1"]["atom"]
                                        - W.atom * penalty / idx._atom_norm)


# ------------------------------------------------- predicted-set consequence

def test_predicted_set_shrinks_or_holds_at_a_fixed_cut():
    """I2's corollary at a FIXED cut on RAW scores: predicted_v2.0 is a subset
    of predicted_v1.1. Stated on raw scores for the F3 reason — under the
    per-query normalizer the corollary is NOT a theorem."""
    clauses = _clauses(4)
    ann = {"c1": [_atom("must_advise_help__model_user"),
                  _atom("human_safety")],
           "c2": [_atom("human_safety")],
           "c3": [_atom("shouldnot_lie__model_user")]}
    base, idx = _pair(clauses, ann, {"third_party"})
    beh = _beh("human_safety", "shouldnot_lie__model_user")
    rb, rp = base.raw_scores(beh), idx.raw_scores(beh)
    for cut in (0.01, 0.05, 0.1, 0.3, 0.6):
        pred_b = {c for c, s in rb.items() if s > 0 and s >= cut}
        pred_p = {c for c, s in rp.items() if s > 0 and s >= cut}
        assert pred_p <= pred_b, cut
