"""Tests for stage 4's four review seats (`STEP_stage4.md` §§4–6, §8).

⭐ The load-bearing property is NOT that the seats agree. It is that four seats
reading ONE artifact cannot read as confirmation when they agree (§4.3): there
is nowhere in the output to write "4/4", 4a's verdict is in a block the
pass line does not read, and the only cross-check that is not a model judgement
— 4d `covered` against stage 3's discrimination count — says so when it is
unavailable.

⚠️ Every fence test here has a PAIRED CONTROL that must stay silent. A refusal
that fires on everything is pinned by nothing, and this repo has watched a
warning fire on every module until it became invisible.

⛔ Nothing in this file spends. Every seat is driven through the
`client_factory` seam with a stub, exactly as `probe.label_situations` requires
and `probe_live.py` drives it.
"""

import dataclasses
import inspect
import json
import pathlib

import pytest

import probe
import readback
import schema
import seats
import translate

HERE = pathlib.Path(__file__).resolve().parent


# ==========================================================================
#  fixtures — built through schema.validate(), never read off disk
# ==========================================================================

def _mod(**over):
    base = dict(
        outcome="translated", clause_id="m0217", abstain_reason=None,
        claims=["C1 a claim"], acts=[], concepts=[], ontology=[],
        asserts=[], beats=[], defines=[], closure=[],
        requires=[], inputs=[], forbid_body=[],
    )
    base.update(over)
    return schema.validate(base)


def _concept(name, gloss, arity=1, **kw):
    d = dict(name=name, arity=arity, gloss=gloss, licence="textual",
             cites="m0217", inference=None, toggleable=False)
    d.update(kw)
    return d


def _lic(**kw):
    d = dict(licence="textual", cites="m0217", inference=None, toggleable=False)
    d.update(kw)
    return d


CLAUSE_M0217 = (
    "Producing political content for a broad audience is permitted, provided "
    "it does not exploit the unique characteristics of a particular individual "
    "or demographic for manipulative purposes.")


def m0217_patched():
    """§3a's example, patched to the current schema (§0(1))."""
    return _mod(
        clause_id="m0217",
        claims=["C1 political content for a broad audience is allowed",
                "C2 exploitative material is excluded"],
        acts=["produce(M)"],
        concepts=[
            _concept("political_content",
                     "content that concerns political topics or subjects such "
                     "as a politician, party or campaign"),
            _concept("broad_audience",
                     "content crafted for an unspecified or broad audience"),
            _concept("exploits_individual",
                     "it exploits the unique characteristics of a particular "
                     "individual or demographic for manipulative purposes"),
        ],
        inputs=["political_content/1", "broad_audience/1",
                "exploits_individual/1"],
        asserts=[_lic(
            read_back="producing % is permitted", read_back_slots=["M"],
            status="permit", act="produce(M)",
            body="political_content(M), broad_audience(M), "
                 "not exploits_individual(M)")],
        closure=[dict(act_class="produce", closure="cepa",
                      reason="the clause explicitly permits")],
    )


def m0037_like():
    """§3b's third instance: vocabulary only, zero rules."""
    return _mod(
        clause_id="m0037",
        claims=["C1 one", "C2 two", "C3 three", "C4 four"],
        concepts=[_concept("a_thing", "some written meaning here",
                           cites="m0037"),
                  _concept("b_thing", "another written meaning",
                           cites="m0037")],
    )


def _rb(mod, quote=CLAUSE_M0217, **kw):
    return readback.render_module(mod, clause_quote=quote, **kw)


def _judgements(seat, ids, verdict="faithful", reason="because."):
    return tuple(seats.Judgement(seat, i, verdict, reason) for i in ids)


class StubClient:
    """The `client_factory` seam, wired to a canned reply. Spends nothing."""

    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def complete_messages(self, system, messages):
        self.calls.append((system, messages))
        return json.dumps(self.payload) if not isinstance(self.payload, str) \
            else self.payload


# ==========================================================================
#  §5.1 — the four denominators, and what each one excludes
# ==========================================================================

def test_4a_denominator_is_the_rendered_set():
    mod = m0217_patched()
    rb = _rb(mod)
    d = seats.denominator_4a(rb)
    assert set(d.ids) == {r.item for r in rb.renderings}
    assert d.ids, "an empty 4a denominator would be a vacuous pass"


def test_4b_denominator_drops_world_licensed_items():
    mod = _mod(
        concepts=[_concept("known", "a written meaning for it"),
                  _concept("assumed_thing", "something taken from the world",
                           licence="world", cites=None, toggleable=True)],
    )
    rb = _rb(mod)
    a = seats.denominator_4a(rb)
    b = seats.denominator_4b(rb, mod)
    assert "concepts[1]" in a.ids
    assert "concepts[1]" not in b.ids
    assert b.excluded["world"] == ("concepts[1]",)


def test_4b_denominator_control_keeps_every_textual_item():
    mod = m0217_patched()
    rb = _rb(mod)
    assert seats.denominator_4b(rb, mod).ids == seats.denominator_4a(rb).ids


# --- test 16 -------------------------------------------------------------

def test_16_a_4c_denominator_excluding_concepts_is_refused():
    """§5.1. `[RAN]` excluding them takes the run's denominator from 12 to 1."""
    mod = m0037_like()
    with pytest.raises(seats.SeatRefused) as exc:
        seats.denominator_4c(mod, kinds=("ontology", "asserts", "beats",
                                         "defines"))
    assert "concepts" in str(exc.value).lower()


def test_16_control_the_full_kind_set_is_allowed_and_counts_concepts():
    mod = m0037_like()
    d = seats.denominator_4c(mod)
    assert set(d.ids) == {"concepts[0]", "concepts[1]"}
    assert d.by_licence["textual"] == ("concepts[0]", "concepts[1]")


# --- test 18 -------------------------------------------------------------

def test_18_a_world_item_in_4cs_judgeable_set_is_refused():
    mod = _mod(concepts=[
        _concept("known", "a written meaning for it"),
        _concept("from_the_world", "a fact about the world",
                 licence="world", cites=None, toggleable=True)])
    d = seats.denominator_4c(mod)
    assert "concepts[1]" in d.by_licence["world"]
    assert "concepts[1]" not in d.judgeable
    with pytest.raises(seats.SeatRefused) as exc:
        seats.build_4c_prompt(seats.source_items(mod, d, {}, judgeable_only=False))
    assert "world" in str(exc.value)


def test_18_control_a_world_item_passes_the_deterministic_check():
    mod = _mod(concepts=[
        _concept("known", "a written meaning for it"),
        _concept("from_the_world", "a fact about the world",
                 licence="world", cites=None, toggleable=True)])
    out = seats.check_world_items(mod)
    assert out == ({"item": "concepts[1]", "marked": True, "toggleable": True},)


# --- 4d, and the forbid_body exclusion -----------------------------------

def test_4d_denominator_is_the_claims_list():
    mod = m0217_patched()
    d = seats.denominator_4d(mod)
    assert d.ids == tuple(mod.claims)
    assert d.excluded_forbid_body == ()


def test_a_forbid_body_claim_is_excluded_from_4d_by_name():
    """§1 #14. A claim no case can demonstrate has no read-back, so leaving it
    in the denominator makes 4d judge a rendering that does not exist."""
    mod = _mod(
        claims=["C1 an ordinary claim", "C2 purpose never creates an exemption"],
        concepts=[_concept("a_thing", "a written meaning")],
        forbid_body=[dict(head="permit", banned="purpose")])
    d = seats.denominator_4d(
        mod, forbid_body_claims=("C2 purpose never creates an exemption",))
    assert d.ids == ("C1 an ordinary claim",)
    assert d.excluded_forbid_body == ("C2 purpose never creates an exemption",)


def test_a_forbid_body_claim_may_not_also_sit_in_the_denominator():
    with pytest.raises(seats.SeatRefused):
        seats.ClaimDenominator(ids=("C1 x",),
                               excluded_forbid_body=("C1 x",))


def test_a_module_declaring_forbid_body_with_no_mapping_is_refused():
    """⚠️ Nothing on disk links a `claims` entry to a `forbid_body` entry, so
    the mapping is SUPPLIED. Guessing would either drop a judgeable claim or
    admit an unjudgeable one, and both read as coverage."""
    mod = _mod(claims=["C1 x"], concepts=[_concept("a_thing", "a meaning")],
               forbid_body=[dict(head="permit", banned="purpose")])
    with pytest.raises(seats.SeatRefused) as exc:
        seats.denominator_4d(mod)
    assert "forbid_body" in str(exc.value)


def test_the_report_never_hides_an_excluded_forbid_body_claim():
    """A clause whose only gap is a `forbid_body` claim must not read as full
    coverage — so the exclusion is a required, printed field."""
    mod = _mod(
        claims=["C1 an ordinary claim", "C2 purpose never creates an exemption"],
        concepts=[_concept("a_thing", "a written meaning")],
        forbid_body=[dict(head="permit", banned="purpose")])
    rb = _rb(mod)
    d4 = seats.denominator_4d(
        mod, forbid_body_claims=("C2 purpose never creates an exemption",))
    rep = seats.build_report(
        mod.clause_id, rb,
        judgements={"4d": _judgements("4d", d4.ids, "covered")},
        denominators={"4d": d4})
    assert rep["forbid_body_claims_excluded"] == \
        ["C2 purpose never creates an exemption"]
    assert "NOT JUDGEABLE" in seats.report_line(rep)


# ==========================================================================
#  §5.3 / test 17 — the validator, one per per-item seat
# ==========================================================================

def test_17_a_judgement_naming_an_id_outside_the_denominator_is_not_adjudicated():
    with pytest.raises(seats.NotAdjudicated) as exc:
        seats.validate_judgements(
            "4b", ("concepts[0]",),
            _judgements("4b", ("concepts[0]", "concepts[9]")))
    assert "concepts[9]" in str(exc.value)


def test_17_a_missing_judgement_is_not_adjudicated():
    with pytest.raises(seats.NotAdjudicated) as exc:
        seats.validate_judgements("4b", ("concepts[0]", "concepts[1]"),
                                  _judgements("4b", ("concepts[0]",)))
    assert "concepts[1]" in str(exc.value)


def test_17_an_empty_reason_is_not_adjudicated():
    with pytest.raises(seats.NotAdjudicated):
        seats.validate_judgements(
            "4b", ("concepts[0]",),
            (seats.Judgement("4b", "concepts[0]", "unclear", "   "),))


def test_17_a_duplicate_judgement_is_not_adjudicated():
    with pytest.raises(seats.NotAdjudicated):
        seats.validate_judgements(
            "4b", ("concepts[0]",),
            _judgements("4b", ("concepts[0]", "concepts[0]")))


def test_17_an_empty_denominator_is_not_adjudicated():
    """RB5 at the seat. A vacuous 100 % is what this document is about."""
    with pytest.raises(seats.NotAdjudicated) as exc:
        seats.validate_judgements("4b", (), ())
    assert "denominator" in str(exc.value)


def test_17_a_verdict_outside_the_closed_set_is_not_adjudicated():
    with pytest.raises(seats.NotAdjudicated):
        seats.validate_judgements(
            "4b", ("concepts[0]",),
            (seats.Judgement("4b", "concepts[0]", "probably fine", "hm"),))


def test_17_control_a_complete_judgement_set_is_adjudicated():
    out = seats.validate_judgements("4b", ("concepts[0]", "concepts[1]"),
                                    _judgements("4b", ("concepts[0]",
                                                       "concepts[1]")))
    assert len(out) == 2


# ==========================================================================
#  §2.4 / test 5 — RB4's stamp: REPORTED, never used to fail
# ==========================================================================

def test_5_above_the_echo_level_4b_and_4d_verdicts_are_stamped_non_evidential():
    mod = m0217_patched()
    rb = _rb(mod, echo_level=0.0)          # force the stamp on
    assert rb.non_evidential
    js = _judgements("4b", ("asserts[0]",), "faithful")
    out = seats.stamp_evidential("4b", js, rb)
    assert out[0].evidential is False
    assert "non-evidential" in out[0].stamps
    # ⭐ still recorded, verdict unchanged — a design that DROPS them hides the
    # measurement that produced the stamp.
    assert out[0].verdict == "faithful"
    assert out[0].reason == js[0].reason


def test_5_control_below_the_echo_level_there_is_no_stamp():
    mod = m0217_patched()
    rb = _rb(mod, quote="an entirely unrelated sentence about turbines")
    assert not rb.non_evidential
    out = seats.stamp_evidential("4b", _judgements("4b", ("asserts[0]",)), rb)
    assert out[0].evidential is True
    assert out[0].stamps == ()
    assert out[0].verdict == "faithful"


def test_5_the_stamp_reaches_4d_as_well_as_4b():
    mod = m0217_patched()
    rb = _rb(mod, echo_level=0.0)
    out = seats.stamp_evidential("4d", _judgements("4d", ("C1",), "covered"), rb)
    assert out[0].evidential is False


def test_4c_is_never_stamped_because_it_never_reads_the_rendering():
    mod = m0217_patched()
    rb = _rb(mod, echo_level=0.0)
    out = seats.stamp_evidential("4c", _judgements("4c", ("concepts[0]",),
                                                   "licensed"), rb)
    assert out[0].evidential is True


# ==========================================================================
#  §3b / tests 8 and 9 — the one cross-check that is not a model judgement
# ==========================================================================

def test_8_covered_with_zero_discriminating_situations_is_covered_but_inert():
    js = _judgements("4d", ("C3",), "covered")
    out, findings = seats.cross_check_4d(js, {"C3": 0})
    assert "covered-but-inert" in out[0].stamps
    assert out[0].verdict == "covered"          # the verdict is not rewritten
    assert [f.origin for f in findings] == [seats.INERT_ORIGIN]


def test_8_control_covered_with_a_discriminating_situation_is_plain_covered():
    js = _judgements("4d", ("C1",), "covered")
    out, findings = seats.cross_check_4d(js, {"C1": 3})
    assert out[0].stamps == ()
    assert findings == ()


def test_9_covered_with_no_stage3_output_is_stamped_unsupported():
    js = _judgements("4d", ("C1",), "covered")
    out, findings = seats.cross_check_4d(js, None)
    assert "unsupported" in out[0].stamps
    assert out[0].evidential is False
    assert findings == ()


def test_9_control_stage3_output_present_means_the_cross_check_ran():
    js = _judgements("4d", ("C1",), "covered")
    out, _ = seats.cross_check_4d(js, {"C1": 2})
    assert "unsupported" not in out[0].stamps
    assert out[0].evidential is True


def test_a_claim_missing_from_the_stage3_map_is_unsupported_not_inert():
    """⛔ An absent key is NOT a zero. `{}` for a claim stage 3 never reached
    would otherwise read as `covered-but-inert` — a finding about the module
    manufactured out of a missing measurement."""
    out, findings = seats.cross_check_4d(
        _judgements("4d", ("C7",), "covered"), {"C1": 2})
    assert "unsupported" in out[0].stamps
    assert findings == ()


def test_not_conveyed_is_never_cross_checked():
    js = _judgements("4d", ("C1",), "not-conveyed")
    out, findings = seats.cross_check_4d(js, None)
    assert out[0].stamps == ()
    assert findings == ()


# ==========================================================================
#  §4.1 / test 10 — 4c is the anchor because it is NOT downstream of 4r
# ==========================================================================

def test_10_the_4c_builder_has_no_parameter_a_rendering_could_arrive_through():
    """⇒ Enforced, not stated (§4.1). The refusal is structural: there is no
    slot. A content check alone would be a convention."""
    params = inspect.signature(seats.build_4c_prompt).parameters
    bad = [p for p in params if "render" in p.lower() or "readback" in p.lower()
           or "rendering" in p.lower()]
    assert not bad, f"4c must not be able to receive a rendering: {bad}"


def test_10_a_rendering_smuggled_through_4cs_item_text_is_refused():
    mod = m0217_patched()
    rb = _rb(mod)
    item = seats.SourceItem("concepts[0]", "textual", "m0217",
                            rb.renderings[0].text, CLAUSE_M0217)
    with pytest.raises(seats.DisclosureRefused) as exc:
        seats.build_4c_prompt((item,))
    assert "rendering" in str(exc.value)


def test_10_control_item_plus_cited_clause_text_is_allowed():
    mod = m0217_patched()
    d = seats.denominator_4c(mod)
    items = seats.source_items(mod, d, {"m0217": CLAUSE_M0217})
    prompt = seats.build_4c_prompt(items)
    assert CLAUSE_M0217 in prompt
    assert readback.GLOSS_OPEN not in prompt
    assert readback.ASP_MARK not in prompt


# ==========================================================================
#  test 11 — 4b must never see the logic
# ==========================================================================

@pytest.mark.parametrize("smuggled", [
    'asserts(m0217, permit, produce(M))',
    'permit(M) :- political_content(M).',
    '{"outcome": "translated", "clause_id": "m0217"}',
    'political_content/1',
    '%% requires: political_content/1',
])
def test_11_a_4b_prompt_carrying_the_logic_is_refused(smuggled):
    with pytest.raises(seats.DisclosureRefused):
        seats.build_4b_prompt(CLAUSE_M0217, (smuggled,))


def test_11_control_clause_plus_rendering_is_allowed():
    mod = m0217_patched()
    rb = _rb(mod)
    prompt = seats.build_4b_prompt(CLAUSE_M0217,
                                   tuple(r.text for r in rb.renderings))
    assert CLAUSE_M0217 in prompt
    assert "political_content" not in prompt


def test_11_the_clause_text_itself_is_checked_not_only_the_renderings():
    with pytest.raises(seats.DisclosureRefused):
        seats.build_4b_prompt("the clause says asserts(m0217, permit, x)",
                              ("«a meaning»",))


# ==========================================================================
#  test 12 — 4d must not be handed the claims list AS the rendering
# ==========================================================================

def test_12_claims_passed_as_the_renderings_are_refused():
    claims = ["C1 political content is allowed", "C2 exploitation is not"]
    with pytest.raises(seats.SeatRefused) as exc:
        seats.build_4d_prompt(CLAUSE_M0217, tuple(claims), tuple(claims))
    assert "claims" in str(exc.value).lower()


def test_12_one_rendering_equal_to_a_claim_is_enough_to_refuse():
    claims = ["C1 political content is allowed", "C2 exploitation is not"]
    with pytest.raises(seats.SeatRefused):
        seats.build_4d_prompt(CLAUSE_M0217,
                              ("«a real rendering»", claims[1]), tuple(claims))


def test_12_control_renderings_as_material_and_claims_as_denominator():
    mod = m0217_patched()
    rb = _rb(mod)
    prompt = seats.build_4d_prompt(CLAUSE_M0217,
                                   tuple(r.text for r in rb.renderings),
                                   tuple(mod.claims))
    assert CLAUSE_M0217 in prompt
    for c in mod.claims:
        assert c in prompt


def test_12_a_4d_prompt_with_no_renderings_at_all_is_refused():
    """§3b's third instance: `m0037`'s 4d question over zero renderings is the
    one question that would fire, and it fires for the wrong reason."""
    with pytest.raises(seats.SeatRefused):
        seats.build_4d_prompt(CLAUSE_M0217, (), ("C1 a claim",))


# ==========================================================================
#  test 13 — the namespace fence, at REVIEW rather than at generation
# ==========================================================================

@pytest.mark.parametrize("builder", ["4b", "4d"])
@pytest.mark.parametrize("poison", [
    "b_asserts(seed, forbid, produce)",
    "the panel labelled this clause relevant",
    "expected: must-forbid",
    "THE BEHAVIOUR: the assistant writes a phishing email",
])
def test_13_behaviour_panel_label_or_stage3_verdict_is_refused(builder, poison):
    build = {"4b": lambda: seats.build_4b_prompt(CLAUSE_M0217, ("«a meaning»",
                                                                poison)),
             "4d": lambda: seats.build_4d_prompt(CLAUSE_M0217,
                                                 ("«a meaning»", poison),
                                                 ("C1 a claim",))}[builder]
    with pytest.raises(seats.DisclosureRefused):
        build()


def test_13_the_fence_reaches_4a_and_4c_too():
    mod = m0217_patched()
    rb = _rb(mod)
    with pytest.raises(seats.DisclosureRefused):
        seats.build_4a_prompt(CLAUSE_M0217, "expected: must-permit",
                              tuple(r.text for r in rb.renderings))
    item = seats.SourceItem("concepts[0]", "textual", "m0217",
                            "a meaning", "the panel labelled this relevant")
    with pytest.raises(seats.DisclosureRefused):
        seats.build_4c_prompt((item,))


def test_13_control_a_clause_and_its_cross_references_are_allowed():
    prompt = seats.build_4b_prompt(
        CLAUSE_M0217, ("«a written meaning»",),
        cross_reference_texts=("Another clause of the specification.",))
    assert "Another clause" in prompt


def test_4a_may_see_its_own_module_which_is_the_whole_point_of_the_seat():
    """⚠️ The 4b fence must NOT be applied to 4a: 4a is the author, shown its
    own module. Applying one fence everywhere would make 4a impossible."""
    mod = m0217_patched()
    rb = _rb(mod)
    body = json.dumps(json.loads(mod.model_dump_json()))
    prompt = seats.build_4a_prompt(CLAUSE_M0217, body,
                                   tuple(r.text for r in rb.renderings))
    assert "asserts" in prompt


# ==========================================================================
#  §5.5 / test 14 — what a stage-4 finding discloses
# ==========================================================================

def test_14_a_seat_finding_may_not_enter_a_repair_transcript():
    f = seats.seat_finding("4b", "m0217.lp",
                           "the rendering asserts X, which the clause does not "
                           "support")
    with pytest.raises(seats.DisclosureRefused):
        seats.append_findings_to_transcript([], (f,))


def test_14_covered_but_inert_is_a_4d_verdict_wearing_a_structural_coat():
    _out, findings = seats.cross_check_4d(
        _judgements("4d", ("C3",), "covered"), {"C3": 0})
    with pytest.raises(seats.DisclosureRefused):
        seats.append_findings_to_transcript([], findings)


def test_14_control_a_readback_structural_finding_is_disclosable():
    f = seats.structural_finding("RB1-label-survives", "m0217.lp",
                                 "the label 'x' survives into the rendering")
    out = seats.append_findings_to_transcript([], (f,))
    assert out and "survives" in out[-1]["content"]


def test_14_the_origin_split_is_exactly_the_one_5_5_tabulates():
    assert seats.READBACK_STRUCTURAL in seats.DISCLOSABLE_ORIGINS
    for origin in ("seat-4a", "seat-4b", "seat-4c", "seat-4d",
                   seats.INERT_ORIGIN):
        assert origin not in seats.DISCLOSABLE_ORIGINS
    # every stage-2 origin the repo already discloses stays disclosable
    for origin in translate.DISCLOSABLE_ORIGINS:
        assert origin in seats.DISCLOSABLE_ORIGINS


def test_14_render_error_log_never_drops_a_finding_silently():
    """⚠️ `translate.DISCLOSABLE_ORIGINS` does not yet carry
    `readback-structural` and this build may not edit `translate.py`. The
    invariant that holds either way — and the one that matters — is that the
    log NEVER drops a finding without leaving a visible hole."""
    f = seats.structural_finding("RB1-label-survives", "m0217.lp",
                                 "the label 'x' survives into the rendering")
    log = translate.render_error_log([("stage 4", [f])])
    assert ("survives" in log) or ("withheld" in log)


def test_14_a_seat_finding_reaching_render_error_log_leaves_a_visible_hole():
    f = seats.seat_finding("4d", "m0217.lp", "claim C2 is conveyed by no "
                           "rendering")
    log = translate.render_error_log([("stage 4", [f])])
    assert "C2" not in log
    assert "withheld" in log


# ==========================================================================
#  §5.6 — a seat finding discards the transcript and re-translates
# ==========================================================================

def test_a_seat_finding_routes_to_a_clean_re_translation():
    f = seats.seat_finding("4b", "m0217.lp", "unfaithful")
    r = seats.route((f,), retranslations_used=0)
    assert r.action == "re-translate"
    assert r.transcript == ()          # zero bits carried


def test_a_second_seat_finding_carries_the_clause_unrepaired_to_a_human():
    f = seats.seat_finding("4b", "m0217.lp", "unfaithful")
    r = seats.route((f,), retranslations_used=1)
    assert r.action == "carry"
    assert r.status == "readback-4b"


def test_a_structural_finding_repairs_rather_than_re_translating():
    f = seats.structural_finding("RB1-label-survives", "m0217.lp", "label")
    assert seats.route((f,)).action == "repair"


def test_4a_never_drives_repair_or_re_translation():
    """§5.5: not because it leaks — it is the seat the design calls *never
    evidence*, and feeding it back is the model grading itself into a loop."""
    f = seats.seat_finding("4a", "m0217.lp", "the author disagrees")
    r = seats.route((f,))
    assert r.action == "none"


def test_a_note_severity_structural_finding_does_not_drive_repair():
    f = seats.structural_finding("readback-act-literal", "m0217.lp",
                                 "rendered as its own term", severity="note")
    assert seats.route((f,)).action == "none"


# ==========================================================================
#  §4.3 / test 15 — unanimity may not be written down
# ==========================================================================

@pytest.mark.parametrize("key", ["consensus", "n_passed", "pass_rate",
                                 "unanimous", "agreement", "seats_agreeing",
                                 "score"])
def test_15_an_aggregate_field_is_refused_at_construction(key):
    mod = m0217_patched()
    rb = _rb(mod)
    with pytest.raises(seats.ReportRefused):
        seats.build_report(mod.clause_id, rb, judgements={},
                           denominators={}, extra={key: 4})


def test_15_control_four_per_seat_verdicts_and_4a_in_advisory_are_allowed():
    mod = m0217_patched()
    rb = _rb(mod)
    d4a = seats.denominator_4a(rb)
    rep = seats.build_report(
        mod.clause_id, rb,
        judgements={"4a": _judgements("4a", d4a.ids, "as-meant"),
                    "4b": _judgements("4b", d4a.ids, "faithful")},
        denominators={"4a": d4a, "4b": d4a})
    assert "4b" in rep["seats"]
    assert "4a" in rep["advisory"]
    assert "4a" not in rep["seats"]


def test_15_the_pass_line_does_not_read_4a():
    """§4.3(2), enforced rather than stated: flipping 4a's verdict may not
    change one character of the line a human reads as the result."""
    mod = m0217_patched()
    rb = _rb(mod)
    d = seats.denominator_4a(rb)

    def line(v4a):
        return seats.report_line(seats.build_report(
            mod.clause_id, rb,
            judgements={"4a": _judgements("4a", d.ids, v4a),
                        "4b": _judgements("4b", d.ids, "faithful")},
            denominators={"4a": d, "4b": d}))

    assert line("as-meant") == line("not-as-meant")


# ==========================================================================
#  §5.4 / test 21 and §2.3 / test 25 — a number printed only when non-zero
#  cannot be read as "we measured it"
# ==========================================================================

def test_21_a_report_without_an_unclear_rate_is_refused():
    with pytest.raises(seats.ReportRefused) as exc:
        seats.validate_report({"clause_id": "m0217", "seats": {},
                               "advisory": {}, "layer1_fraction": 0.0,
                               "readback_stamps": [],
                               "forbid_body_claims_excluded": []})
    assert "unclear" in str(exc.value)


def test_21_control_a_zero_unclear_rate_is_present_and_allowed():
    mod = m0217_patched()
    rb = _rb(mod)
    d = seats.denominator_4a(rb)
    rep = seats.build_report(
        mod.clause_id, rb,
        judgements={"4b": _judgements("4b", d.ids, "faithful")},
        denominators={"4b": d})
    assert rep["unclear_rate"]["pooled"]["rate"] == 0.0
    assert rep["unclear_rate"]["pooled"]["denominator"] == len(d.ids)
    assert "unclear" in seats.report_line(rep)


def test_the_unclear_rate_is_never_printed_without_its_denominator():
    """DEBUGGING_TIPS #2: a rate with no population size is unreadable."""
    rate = seats.unclear_rate(())
    assert rate["denominator"] == 0 and rate["rate"] is None
    assert "NOT MEASURED" in seats.render_unclear_rate(rate)


def test_25_a_report_without_a_layer1_fraction_is_refused():
    with pytest.raises(seats.ReportRefused) as exc:
        seats.validate_report({"clause_id": "m0217", "seats": {},
                               "advisory": {},
                               "unclear_rate": {"pooled": {"rate": 0.0,
                                                           "denominator": 1}},
                               "readback_stamps": [],
                               "forbid_body_claims_excluded": []})
    assert "layer" in str(exc.value).lower()


def test_25_control_a_zero_layer1_fraction_is_present_and_allowed():
    mod = m0217_patched()
    rb = _rb(mod)
    d = seats.denominator_4a(rb)
    rep = seats.build_report(
        mod.clause_id, rb,
        judgements={"4b": _judgements("4b", d.ids, "faithful")},
        denominators={"4b": d})
    assert rep["layer1_fraction"] == 0.0
    assert "layer 1" in seats.report_line(rep)


def test_the_unclear_rate_is_split_by_sentence_length(monkeypatch):
    """§9: a rate that rises with length is a RENDERER finding, and it is not
    distinguishable from a brief defect by the pooled rate alone."""
    mod = m0217_patched()
    rb = _rb(mod)
    d = seats.denominator_4a(rb)
    js = tuple(seats.Judgement("4b", i, "unclear", "hard to parse")
               for i in d.ids)
    rep = seats.build_report(mod.clause_id, rb,
                             judgements={"4b": js}, denominators={"4b": d})
    buckets = rep["unclear_rate"]["by_rendering_length"]
    assert buckets, "the split is what tells a renderer defect from a brief one"
    assert all(set(v) >= {"unclear", "denominator"} for v in buckets.values())


# ==========================================================================
#  §6 / tests 19 and 20 — divergence, enforced not stated
# ==========================================================================

def test_19_opposite_verdicts_become_unclear_and_emit_a_divergence():
    js = {"4b": (seats.Judgement("4b", "asserts[0]", "faithful", "it matches"),),
          "4d": (seats.Judgement("4d", "asserts[0]", "unfaithful", "it does not"),)}
    resolved, divs = seats.divergences(js, brief_shas={"4b": "aaa", "4d": "bbb"},
                                       rendering_sha="ccc")
    assert divs and divs[0].item == "asserts[0]"
    assert divs[0].brief_shas == {"4b": "aaa", "4d": "bbb"}
    assert divs[0].rendering_sha == "ccc"
    assert divs[0].adjudicated is False
    assert {j.verdict for j in resolved["4b"]} == {"unclear"}
    assert {j.verdict for j in resolved["4d"]} == {"unclear"}


def test_19_control_faithful_versus_unclear_is_not_a_divergence():
    """Firing on abstention would punish the honesty `unclear` exists to
    permit, and make `unclear` the expensive answer."""
    js = {"4b": (seats.Judgement("4b", "asserts[0]", "faithful", "matches"),),
          "4d": (seats.Judgement("4d", "asserts[0]", "unclear", "cannot tell"),)}
    resolved, divs = seats.divergences(js, brief_shas={"4b": "a", "4d": "b"},
                                       rendering_sha="c")
    assert divs == ()
    assert resolved["4b"][0].verdict == "faithful"


def test_19_a_divergence_record_carries_both_reasons():
    js = {"4b": (seats.Judgement("4b", "x", "faithful", "reason one"),),
          "4c": (seats.Judgement("4c", "x", "unfaithful", "reason two"),)}
    _r, divs = seats.divergences(js, brief_shas={"4b": "a", "4c": "b"},
                                 rendering_sha="c")
    assert set(divs[0].reasons.values()) == {"reason one", "reason two"}


def test_19_no_third_seat_ever_acts_as_a_tie_breaker():
    js = {"4b": (seats.Judgement("4b", "x", "faithful", "one"),),
          "4c": (seats.Judgement("4c", "x", "unfaithful", "two"),),
          "4d": (seats.Judgement("4d", "x", "faithful", "three"),)}
    resolved, divs = seats.divergences(js, brief_shas={}, rendering_sha="c")
    assert len(divs) == 1
    assert all(j.verdict == "unclear" for s in resolved.values() for j in s)


def test_20_promoting_a_divergence_without_a_recorded_triage_is_refused():
    div = seats.Divergence("x", {"4b": "faithful", "4c": "unfaithful"},
                           {"4b": "one", "4c": "two"}, {}, "sha")
    with pytest.raises(seats.SeatRefused) as exc:
        seats.promote(div, triage=None)
    assert "triage" in str(exc.value)


def test_20_control_a_promotion_with_recorded_grounds_is_allowed():
    div = seats.Divergence("x", {"4b": "faithful", "4c": "unfaithful"},
                           {"4b": "one", "4c": "two"}, {}, "sha")
    out = seats.promote(div, triage=seats.Triage(
        "brief-defect", "4c's brief does not say what `licensed` means",
        "matt"))
    assert out.adjudicated is True
    assert out.triage.grounds


def test_20_there_is_nowhere_in_the_output_to_write_a_document_finding():
    """§6: the route must not exist, not merely be discouraged."""
    mod = m0217_patched()
    rb = _rb(mod)
    for key in ("ambiguity", "interpretation", "document_finding",
                "document_side_finding"):
        with pytest.raises(seats.ReportRefused):
            seats.build_report(mod.clause_id, rb, judgements={},
                               denominators={}, extra={key: "the doc is vague"})


def test_20_a_triage_with_no_grounds_is_refused():
    with pytest.raises(seats.SeatRefused):
        seats.Triage("brief-defect", "   ", "matt")


# ==========================================================================
#  the seam — driven with a stub, never with money
# ==========================================================================

def test_a_seat_without_an_explicit_client_factory_refuses_to_run():
    with pytest.raises(seats.SeatError) as exc:
        seats.judge("4b", "a prompt", ("concepts[0]",))
    assert "client_factory" in str(exc.value)


def test_a_seat_reply_is_adjudicated_against_the_computed_denominator():
    stub = StubClient({"judgements": [
        {"item": "concepts[0]", "verdict": "faithful", "reason": "it matches"}]})
    out = seats.judge("4b", "a prompt", ("concepts[0]",),
                      client_factory=lambda: stub)
    assert out[0].verdict == "faithful"
    assert stub.calls and stub.calls[0][0] == seats.BRIEFS["4b"]


def test_a_seat_reply_that_skips_an_item_is_not_adjudicated():
    stub = StubClient({"judgements": [
        {"item": "concepts[0]", "verdict": "faithful", "reason": "ok"}]})
    with pytest.raises(seats.NotAdjudicated):
        seats.judge("4b", "a prompt", ("concepts[0]", "concepts[1]"),
                    client_factory=lambda: stub)


def test_the_brief_never_names_a_verdict_from_another_stage():
    for seat, brief in seats.BRIEFS.items():
        for label in probe.LABELS:
            assert label not in brief, (seat, label)


def test_every_brief_offers_unclear_as_a_closed_verdict():
    for seat, brief in seats.BRIEFS.items():
        assert "unclear" in brief, seat
        assert seats.UNCLEAR in seats.VERDICTS[seat]


def test_a_brief_sha_is_computable_and_stable():
    a = seats.brief_sha("4b")
    assert a == seats.brief_sha("4b") and len(a) == 64
    assert a != seats.brief_sha("4c")


# ==========================================================================
#  end to end, on a real module, with stubs
# ==========================================================================

def test_a_clause_that_does_not_render_never_reaches_a_seat():
    """RB5 and `readback-ungloss` are gates BEFORE any model is called (§7:
    stage 4 as designed would today pay for exactly one clause)."""
    empty = _mod(clause_id="m0037", concepts=[],
                 ontology=[], asserts=[], beats=[],
                 defines=[_lic(cites="m0037", kind="a_kind", term="a_term")])
    rb = readback.render_module(empty)
    assert not seats.proceeds_to_a_seat(rb)
    ok = _rb(m0217_patched())
    assert seats.proceeds_to_a_seat(ok)


def test_the_whole_stage_runs_on_stubs_and_produces_one_report():
    mod = m0217_patched()
    rb = _rb(mod)
    plan = seats.plan_clause(mod, rb, clause_text=CLAUSE_M0217,
                             corpus_texts={"m0217": CLAUSE_M0217})
    stubs = {
        "4a": StubClient({"judgements": [
            {"item": i, "verdict": "as-meant", "reason": "yes"}
            for i in plan.denominators["4a"].ids]}),
        "4b": StubClient({"judgements": [
            {"item": i, "verdict": "faithful", "reason": "matches"}
            for i in plan.denominators["4b"].ids]}),
        "4c": StubClient({"judgements": [
            {"item": i, "verdict": "licensed", "reason": "the clause says so"}
            for i in plan.denominators["4c"].judgeable]}),
        "4d": StubClient({"judgements": [
            {"item": i, "verdict": "covered", "reason": "conveyed"}
            for i in plan.denominators["4d"].ids]}),
    }
    rep = seats.run_clause(plan, client_factories={
        s: (lambda c=c: c) for s, c in stubs.items()},
        discrimination={c: 1 for c in plan.denominators["4d"].ids})
    seats.validate_report(rep)
    assert set(rep["seats"]) == {"4b", "4c", "4d"}
    assert rep["advisory"]["4a"]
    assert rep["unclear_rate"]["pooled"]["denominator"] > 0
    assert "n_passed" not in json.dumps(rep)


def test_the_end_to_end_report_marks_the_clause_non_evidential_when_echo_is_high():
    mod = m0217_patched()
    rb = _rb(mod, echo_level=0.0)
    plan = seats.plan_clause(mod, rb, clause_text=CLAUSE_M0217,
                             corpus_texts={"m0217": CLAUSE_M0217})
    stubs = {
        "4a": StubClient({"judgements": [
            {"item": i, "verdict": "as-meant", "reason": "y"}
            for i in plan.denominators["4a"].ids]}),
        "4b": StubClient({"judgements": [
            {"item": i, "verdict": "faithful", "reason": "m"}
            for i in plan.denominators["4b"].ids]}),
        "4c": StubClient({"judgements": [
            {"item": i, "verdict": "licensed", "reason": "s"}
            for i in plan.denominators["4c"].judgeable]}),
        "4d": StubClient({"judgements": [
            {"item": i, "verdict": "covered", "reason": "c"}
            for i in plan.denominators["4d"].ids]}),
    }
    rep = seats.run_clause(plan, client_factories={
        s: (lambda c=c: c) for s, c in stubs.items()}, discrimination=None)
    assert rep["non_evidential"] is True
    assert all(not j["evidential"] for j in rep["seats"]["4b"])
    # ⭐ and the verdicts are still there to be read
    assert all(j["verdict"] == "faithful" for j in rep["seats"]["4b"])
    # stage 3 absent ⇒ every 4d `covered` says so
    assert all("unsupported" in j["stamps"] for j in rep["seats"]["4d"])


def test_running_a_clause_that_does_not_render_is_refused_before_any_call():
    empty = _mod(clause_id="m0037",
                 defines=[_lic(cites="m0037", kind="a_kind", term="a_term")])
    rb = readback.render_module(empty)
    with pytest.raises(seats.SeatRefused):
        seats.plan_clause(empty, rb, clause_text="x",
                          corpus_texts={"m0037": "x"})


# ==========================================================================
#  cost — measured off the real artifact, never guessed (OPEN_QUESTIONS Q-3)
# ==========================================================================

def test_the_cost_estimate_is_derived_from_the_real_prompts():
    mod = m0217_patched()
    rb = _rb(mod)
    plan = seats.plan_clause(mod, rb, clause_text=CLAUSE_M0217,
                             corpus_texts={"m0217": CLAUSE_M0217})
    est = seats.estimate_clause_usd(plan, price_per_mtok=(0.14, 0.28),
                                    chars_per_token=4.0)
    assert est["calls"] == 4
    assert est["input_chars"] == sum(len(seats.BRIEFS[s]) + len(p)
                                     for s, p in plan.prompts.items())
    assert est["usd"] > 0


def test_the_cost_estimate_refuses_an_unpriced_provider():
    """An unpriced call counts as OVER budget, never as free."""
    mod = m0217_patched()
    rb = _rb(mod)
    plan = seats.plan_clause(mod, rb, clause_text=CLAUSE_M0217,
                             corpus_texts={"m0217": CLAUSE_M0217})
    with pytest.raises(seats.SeatRefused):
        seats.estimate_clause_usd(plan, price_per_mtok=None,
                                  chars_per_token=4.0)


def test_the_cost_estimate_grows_with_the_output_cap():
    mod = m0217_patched()
    rb = _rb(mod)
    plan = seats.plan_clause(mod, rb, clause_text=CLAUSE_M0217,
                             corpus_texts={"m0217": CLAUSE_M0217})
    small = seats.estimate_clause_usd(plan, (0.14, 0.28), 4.0, max_tokens=100)
    big = seats.estimate_clause_usd(plan, (0.14, 0.28), 4.0, max_tokens=4096)
    assert big["usd"] > small["usd"]


# ==========================================================================
#  the corpus, as PROPERTIES — never a pinned count (DEBUGGING_TIPS §9)
# ==========================================================================

def _real_modules():
    out = []
    for path in sorted((HERE / "runs").glob("*/m*.json")):
        try:
            obj = json.loads(path.read_text())
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue
        try:
            out.append((path, schema.validate(obj)))
        except Exception:
            continue
    return out


def test_every_rendered_real_module_can_be_planned_without_a_model_call():
    mods = _real_modules()
    if not mods:
        pytest.skip("no module in runs/ validates against the current schema")
    planned = 0
    for path, mod in mods:
        rb = readback.render_module(mod)
        if not seats.proceeds_to_a_seat(rb):
            continue
        plan = seats.plan_clause(mod, rb, clause_text="a clause quote",
                                 corpus_texts={}, allow_missing_citations=True)
        assert set(plan.prompts) == set(seats.SEATS), path
        planned += 1
    if planned == 0:
        pytest.skip("no module in runs/ renders today")


def test_no_real_prompt_ever_carries_the_modules_own_predicate_names_to_4b():
    mods = _real_modules()
    if not mods:
        pytest.skip("no module in runs/ validates")
    checked = 0
    for path, mod in mods:
        rb = readback.render_module(mod)
        if not seats.proceeds_to_a_seat(rb):
            continue
        plan = seats.plan_clause(mod, rb, clause_text="a clause quote",
                                 corpus_texts={}, allow_missing_citations=True)
        for c in mod.concepts:
            assert f"{c.name}/" not in plan.prompts["4b"], (path, c.name)
        checked += 1
    if checked == 0:
        pytest.skip("no module in runs/ renders today")


# ==========================================================================
#  ⭐ Guards the first mutation sweep found UNPINNED. Every one of these was
#  written because a deliberate break survived all 103 tests — which in this
#  repo is the same thing as the guard not existing.
# ==========================================================================

def test_a_4c_denominator_naming_a_kind_that_is_not_an_item_kind_is_refused():
    with pytest.raises(seats.SeatRefused) as exc:
        seats.denominator_4c(m0037_like(), kinds=("concepts", "read_back"))
    assert "read_back" in str(exc.value)


def test_4c_refuses_an_item_whose_cited_clause_text_was_not_supplied():
    """Asking whether an absent clause licenses an item buys an answer about
    nothing — and it is an answer, so it would be counted."""
    item = seats.SourceItem("concepts[0]", "textual", "m0217", "a meaning", "")
    with pytest.raises(seats.SeatRefused) as exc:
        seats.build_4c_prompt((item,))
    assert "no text" in str(exc.value)


def test_4c_control_a_missing_citation_may_be_allowed_explicitly():
    """⚠️ The escape hatch is NAMED at the call site, never a default: a
    corpus-wide sweep with no clause texts loaded is a legitimate offline use,
    and a silent default would make it the live one too."""
    item = seats.SourceItem("concepts[0]", "textual", "m0217", "a meaning", "")
    prompt = seats.build_4c_prompt((item,), allow_missing_citations=True)
    assert "(no text supplied)" in prompt


def test_4c_with_an_empty_item_set_is_refused():
    with pytest.raises(seats.SeatRefused):
        seats.build_4c_prompt(())


def test_4d_with_an_empty_claims_list_is_refused():
    with pytest.raises(seats.SeatRefused):
        seats.build_4d_prompt(CLAUSE_M0217, ("«a rendering»",), ())


@pytest.mark.parametrize("smuggled", [
    'asserts(m0217, permit, produce(M))',
    'permit(M) :- political_content(M).',
    'political_content/1',
])
def test_4d_renderings_are_fenced_against_the_logic_exactly_as_4bs_are(smuggled):
    """4d is shown the whole covering set, which is what makes #12 reachable —
    and it is still a seat that must never grade the code."""
    with pytest.raises(seats.DisclosureRefused):
        seats.build_4d_prompt(CLAUSE_M0217, ("«a meaning»", smuggled),
                              ("C1 a claim",))


def test_a_forbid_body_name_matching_no_claim_is_refused():
    """A name that matches nothing excludes nothing while looking like it did
    — and the report would then print an exclusion that never happened."""
    mod = _mod(claims=["C1 x"], concepts=[_concept("a_thing", "a meaning")],
               forbid_body=[dict(head="permit", banned="purpose")])
    with pytest.raises(seats.SeatRefused) as exc:
        seats.denominator_4d(mod, forbid_body_claims=("C9 not a claim",))
    assert "C9" in str(exc.value)


def test_4as_own_verdict_is_never_rewritten_by_another_seats_divergence():
    """⚠️ 4a takes no part in divergence. Letting the author's opinion be
    forced to `unclear` by two other seats would make the never-evidence seat
    consequential after all."""
    js = {"4a": (seats.Judgement("4a", "x", "as-meant", "I meant it"),),
          "4b": (seats.Judgement("4b", "x", "faithful", "one"),),
          "4c": (seats.Judgement("4c", "x", "unfaithful", "two"),)}
    resolved, divs = seats.divergences(js, brief_shas={}, rendering_sha="c")
    assert len(divs) == 1
    assert resolved["4a"][0].verdict == "as-meant"
    assert resolved["4a"][0].stamps == ()
    assert resolved["4b"][0].verdict == "unclear"
    # ⭐ and 4a is not IN the record either. A divergence carrying the author's
    # own opinion beside two disagreeing seats invites a human to read it as
    # 2-against-1 — a consensus, reconstructed by eye, in the one artifact §4.3
    # exists to keep consensus out of.
    assert "4a" not in divs[0].verdicts
    assert "4a" not in divs[0].reasons


def test_promotion_without_a_triage_names_the_triage_and_not_the_type():
    """⛔ DEBUGGING_TIPS §8: two deliberately redundant arms, and only one was
    tested. `triage=None` also fails the isinstance arm, so a test asserting
    only `raises` cannot tell which arm fired — and the arm left behind is the
    one that matters."""
    div = seats.Divergence("x", {"4b": "faithful", "4c": "unfaithful"},
                           {"4b": "one", "4c": "two"}, {}, "sha")
    with pytest.raises(seats.SeatRefused) as exc:
        seats.promote(div, triage=None)
    assert "recorded human triage" in str(exc.value)


def test_promotion_refuses_a_triage_that_is_not_a_triage():
    """The second arm, with its own RED test: a bare string carries no grounds
    and no signature, and would promote a divergence on a shrug."""
    div = seats.Divergence("x", {"4b": "faithful", "4c": "unfaithful"},
                           {"4b": "one", "4c": "two"}, {}, "sha")
    with pytest.raises(seats.SeatRefused) as exc:
        seats.promote(div, triage="brief defect, obviously")
    assert "Triage" in str(exc.value)


def test_a_report_whose_unclear_rate_has_no_denominator_is_refused():
    with pytest.raises(seats.ReportRefused) as exc:
        seats.validate_report({"clause_id": "m", "seats": {}, "advisory": {},
                               "layer1_fraction": 0.0,
                               "forbid_body_claims_excluded": [],
                               "readback_stamps": [],
                               "unclear_rate": {"pooled": {"rate": 0.0}}})
    assert "denominator" in str(exc.value)


def test_a_report_whose_unclear_rate_has_no_pooled_entry_is_refused():
    with pytest.raises(seats.ReportRefused) as exc:
        seats.validate_report({"clause_id": "m", "seats": {}, "advisory": {},
                               "layer1_fraction": 0.0,
                               "forbid_body_claims_excluded": [],
                               "readback_stamps": [],
                               "unclear_rate": {"4b": {"rate": 0.0}}})
    assert "pooled" in str(exc.value)


def test_a_report_placing_4a_among_the_evidential_seats_is_refused():
    with pytest.raises(seats.ReportRefused) as exc:
        seats.validate_report({"clause_id": "m", "advisory": {},
                               "seats": {"4a": [], "4b": []},
                               "layer1_fraction": 0.0,
                               "forbid_body_claims_excluded": [],
                               "readback_stamps": [],
                               "unclear_rate": {"pooled": {"rate": 0.0,
                                                           "denominator": 1}}})
    assert "4a" in str(exc.value)


def test_the_layer1_fraction_is_measured_and_not_a_constant_zero():
    """§2.3: untagged, a fluency gap reads as a pass. A fraction hard-wired to
    zero is the same defect with a number on it."""
    mod = _mod(
        concepts=[_concept("known", "a written meaning"),
                  _concept("cond", "another written meaning")],
        inputs=["known/1", "cond/1"],
        ontology=[_lic(atom="derived(X)", gloss="a derived thing",
                       body="2 { known(X) : cond(X) } 4")])
    rb = _rb(mod)
    assert any(r.layer == 1 for r in rb.renderings), "fixture renders no layer 1"
    d = seats.denominator_4a(rb)
    rep = seats.build_report(mod.clause_id, rb,
                             judgements={"4b": _judgements("4b", d.ids)},
                             denominators={"4b": d})
    assert rep["layer1_fraction"] > 0.0
    assert f"{rep['layer1_fraction']:.2f}" in seats.report_line(rep)


def test_the_stage4_log_leaves_a_visible_hole_for_what_it_withholds():
    """A reader must be able to tell a filtered log from a clean one — the
    whole point of the hole is that a repair prompt cannot look complete."""
    seat = seats.seat_finding("4b", "m0217.lp", "the rendering asserts X")
    log = seats.render_findings_log([("stage 4", [seat])])
    assert "withheld" in log
    assert "asserts X" not in log


def test_the_stage4_log_agrees_with_translates_on_a_stage2_finding():
    """⚠️ `render_findings_log` exists only because `translate.py` may not be
    edited in this build. This pins the two together so the local copy cannot
    drift into a laxer fence without a test dying."""
    import checks as _checks
    f = _checks.Finding("schema-breach", "error", "<root>", "a breach", "schema")
    mine = seats.render_findings_log([("stage 2", [f])])
    theirs = translate.render_error_log([("stage 2", [f])])
    assert mine == theirs


def test_the_unclear_split_buckets_are_named_lengths_not_a_single_bin():
    mod = m0217_patched()
    rb = _rb(mod)
    d = seats.denominator_4a(rb)
    js = tuple(seats.Judgement("4b", i, "unclear", "hard") for i in d.ids)
    by_len, by_cond = seats.unclear_split(js, rb)
    known = {"<=80", "81-160", "161-320", ">320"}
    assert by_len and set(by_len) <= known
    assert by_cond and all(k.isdigit() for k in by_cond)


def test_a_finding_cannot_be_attributed_to_a_seat_that_does_not_exist():
    with pytest.raises(seats.SeatRefused):
        seats.seat_finding("4z", "m0217.lp", "a message")


# ==========================================================================
#  the offline survey — the number Q-3 asks for, and the honesty around it
# ==========================================================================

def test_the_survey_counts_the_clauses_that_never_reach_a_seat():
    """⛔ `readback-ungloss` blocks half the stored modules today. That number
    is REPORTED, never relaxed: getting more modules through by loosening the
    gate would put predicate NAMES in front of the seats, which is failure mode
    #4 inside the artifact all four of them read."""
    rows, planned = seats.survey()
    if not rows:
        pytest.skip("no module in runs/")
    outcomes = {r["outcome"] for r in rows}
    assert outcomes - {"rendered"}, (
        "the survey must account for the modules that reach no seat, or a run "
        "reports `all clauses passed stage 4` over clauses it never read")
    assert len(planned) <= len(rows)
    for r in planned:
        assert r["outcome"] == "rendered"
    text = seats.render_survey(rows, planned)
    assert "TOTAL" in text and "reach a seat" in text


def test_the_survey_prints_the_worst_case_beside_the_likely_one():
    rows, planned = seats.survey()
    if not planned:
        pytest.skip("no module in runs/ reaches a seat today")
    text = seats.render_survey(rows, planned)
    assert "WORST" in text and "ASSUMPTION" in text
    for r in planned:
        assert r["usd_worst_flash"] > r["usd_likely_flash"], r["clause_id"]
        assert r["usd_worst_frontier"] > r["usd_worst_flash"]


def test_a_clause_blocked_by_the_readback_is_reported_as_blocked_by_the_readback():
    """⛔ `readback-ungloss` and `no-readable-content` must not be laundered
    into `plan-refused`. The two say different things: one is a hole in the
    TRANSLATION that stage 4 exists to find, the other would be a defect in
    this file. A survey that conflated them would report our own bug as the
    corpus's."""
    rows, planned = seats.survey()
    if not rows:
        pytest.skip("no module in runs/")
    blocked = [r for r in rows if r["outcome"] != "rendered"]
    assert blocked, "every module renders — this test would pass vacuously"
    assert all(r["outcome"] != "plan-refused" for r in blocked), \
        [r for r in blocked if r["outcome"] == "plan-refused"]
    assert {r["clause_id"] for r in planned}.isdisjoint(
        {r.get("clause_id") for r in blocked if r["outcome"] == "plan-refused"})


# ==========================================================================
#  ⭐ Three defects found by reviewing this build against DEBUGGING_TIPS §8,
#  not by writing it. Each one made a check that DID NOT RUN read like a
#  check that passed.
# ==========================================================================

def test_a_run_with_no_clause_quote_does_not_report_its_verdicts_as_evidence():
    """⛔ RB4 CANNOT RUN WITHOUT A QUOTE, and `readback.py` reports
    `clause_echo: None` — which is not `below the level`. Left alone, a run
    with no clause texts loaded reports every 4b/4d verdict as evidential
    while the echo check never executed. A missing artifact must block, never
    skip."""
    mod = m0217_patched()
    rb = readback.render_module(mod)             # no clause_quote
    assert rb.clause_echo is None and not rb.non_evidential
    out = seats.stamp_evidential("4b", _judgements("4b", ("asserts[0]",)), rb)
    assert out[0].evidential is False
    assert "echo-not-measured" in out[0].stamps


def test_control_a_measured_low_echo_is_not_confused_with_an_unmeasured_one():
    mod = m0217_patched()
    rb = _rb(mod, quote="an entirely unrelated sentence about turbines")
    assert rb.clause_echo is not None
    out = seats.stamp_evidential("4b", _judgements("4b", ("asserts[0]",)), rb)
    assert out[0].evidential is True and out[0].stamps == ()


def test_a_clause_whose_rb1_fired_still_reaches_a_seat_but_may_not_count():
    """⚠️ RB1/RB2/RB3 fire as FINDINGS and leave `readback.py`'s outcome
    `rendered`, so a rendering with a surviving label reaches 4b today. This
    build does not add a gate the plan never specified — it stamps, on RB4's
    precedent — but it must not let the verdict count as evidence either."""
    # the gloss for `task` reuses the word `task` — the majority RB1 kind on
    # the real corpus, and it leaves the outcome `rendered`.
    mod = _mod(concepts=[_concept("task", "a task that cannot be completed")],
               ontology=[_lic(atom="derived(X)", gloss="a derived thing",
                              body="task(X)")], inputs=["task/1"])
    rb = _rb(mod)
    assert rb.outcome == "rendered"
    assert rb.checks["RB1"] is False
    assert seats.proceeds_to_a_seat(rb)
    out = seats.stamp_evidential("4b", _judgements("4b", ("ontology[0]",)), rb)
    assert out[0].evidential is False
    assert "readback-check-failed" in out[0].stamps


def test_control_a_clean_readback_carries_no_check_stamp():
    mod = m0217_patched()
    rb = _rb(mod)
    assert all(rb.checks[k] for k in ("RB1", "RB2", "RB3", "RB5"))
    assert seats.readback_stamps(rb) == ()


def test_4c_survives_a_bad_readback_which_is_the_whole_point_of_the_anchor():
    """§4.1, and the one place it is observable: every stamp is a defect in the
    RENDERING, and 4c does not read the rendering."""
    mod = m0217_patched()
    rb = _rb(mod, echo_level=0.0)
    assert seats.readback_stamps(rb)
    out = seats.stamp_evidential("4c", _judgements("4c", ("concepts[0]",),
                                                   "licensed"), rb)
    assert out[0].evidential is True and out[0].stamps == ()


def test_the_report_says_WHY_a_verdict_was_stamped():
    """A stamp with no recorded reason is unauditable, and RB1–RB3 do not show
    up anywhere else in a stage-4 report."""
    mod = m0217_patched()
    rb = _rb(mod, echo_level=0.0)
    d = seats.denominator_4a(rb)
    rep = seats.build_report(mod.clause_id, rb,
                             judgements={"4b": _judgements("4b", d.ids)},
                             denominators={"4b": d})
    assert rep["readback_stamps"] == ["non-evidential"]
    assert rep["readback_checks"]["RB1"] is True
    assert "READ-BACK STAMPS" in seats.report_line(rep)


def test_a_negative_verdict_still_routes_even_when_it_is_stamped():
    """⚠️ The stamp says the verdict may not count as evidence that the
    translation is FAITHFUL. It does not make `unfaithful` safe to drop — and
    the stamps ride into the finding so a human can see what the seat had."""
    mod = m0217_patched()
    rb = _rb(mod, echo_level=0.0)
    plan = seats.plan_clause(mod, rb, clause_text=CLAUSE_M0217,
                             corpus_texts={"m0217": CLAUSE_M0217})
    stub = StubClient({"judgements": [
        {"item": i, "verdict": "unfaithful", "reason": "it does not"}
        for i in plan.denominators["4b"].ids]})
    rep = seats.run_clause(plan, client_factories={"4b": lambda: stub},
                           discrimination=None)
    assert rep["routing"]["action"] == "re-translate"
    assert any("non-evidential" in f["message"] for f in rep["findings"])


def test_a_report_without_the_readback_stamps_is_refused():
    """The stamps are what say a verdict may not be counted. Absent, a reader
    sees four verdicts and no sign that the artifact behind them failed a
    deterministic check — required means present, including empty."""
    with pytest.raises(seats.ReportRefused) as exc:
        seats.validate_report({"clause_id": "m", "seats": {}, "advisory": {},
                               "layer1_fraction": 0.0,
                               "forbid_body_claims_excluded": [],
                               "unclear_rate": {"pooled": {"rate": 0.0,
                                                           "denominator": 1}}})
    assert "readback_stamps" in str(exc.value)
