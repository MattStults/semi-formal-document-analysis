"""Stage 3 — the 19 checks `STEP_stage3.md` §8 names, each with its control.

⭐ EVERY TEST HERE NAMES A GUARD **AND** A PAIRED NEGATIVE CONTROL THAT MUST
STAY SILENT. A check that fires on everything is pinned by nothing, and three
times in this project a check was built that measured the wrong thing and
reported success. The control is the real test.

⚠️ Fixtures are hand-written `.lp` text or `schema.validate` + `render_lp`,
never the committed `.raw.txt` files (produced under superseded contracts).
Two tests DO read the committed `.lp` outputs of `runs/20260807-154618-…`,
because that run is the only corpus that exists and `m0217`'s legacy shape —
body predicates declared ONLY in the concept table — is no longer constructible
through today's schema (see `DECISION_stage3_build.md` §3, and the finding at
the head of `probe.py`). Those two tests FAIL, never skip, if the run is
missing: a check that cannot run must not exit like a check that passed.
"""

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
WALKTHROUGH = os.path.dirname(os.path.dirname(HERE))
for _p in (HERE, WALKTHROUGH):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import checks                                                  # noqa: E402
import probe                                                   # noqa: E402
import translate                                               # noqa: E402

RUN = os.path.join(HERE, "runs", "20260807-154618-together-deepseek-v4-flash")
M0255 = os.path.join(WALKTHROUGH, "m0255.lp")
M0255_LINK = [os.path.join(WALKTHROUGH, "clauses", f"m{n}.lp")
              for n in ("0200", "0201", "0203")]


# ==========================================================================
#  Fixtures — hand-written, so an ordinary edit elsewhere cannot break them
# ==========================================================================

#: `m0217` in its LEGACY shape: `inputs` empty, the three body predicates
#: declared only in the concept table. This is what the committed run emitted
#: and it is the shape §2's signature rule was derived from.
M0217_LEGACY = """\
%% clause: m0217   section: avoid_targeted_political_manipulation   kind: conditional
%% acts: produce(M)
%% concepts: political_content/1, broad_audience/1, exploits_individual/1
%% requires:
%% inputs:
%% closure: produce = cepa
asserts(m0217, permit, produce(M)) :- political_content(M), broad_audience(M),
                                      not exploits_individual(M).
"""

M0217_CONCEPTS = [
    dict(concept="political_content/1", clause_id="m0217",
         gloss="the material concerns a political topic or subject",
         licence="textual", cites="m0217", inference=None),
    dict(concept="broad_audience/1", clause_id="m0217",
         gloss="the material is crafted for an unspecified or broad audience",
         licence="textual", cites="m0217", inference=None),
    dict(concept="exploits_individual/1", clause_id="m0217",
         gloss="the material exploits the unique characteristics of a "
               "particular individual or demographic for manipulative purposes",
         licence="textual", cites="m0217", inference=None),
]

#: `m0037`: four claims, five concepts, and NOT ONE RULE. `link.py` passes it
#: clean. It is 1 of the 4 clauses in the cited run.
M0037_NO_RULES = """\
%% clause: m0037   section: levels_of_authority   kind: definitional
%% acts:
%% concepts: system_rule/1
%% requires:
%% inputs:
"""

#: Acts declared, still no mutable rule — the case that keeps tests 14 and 17
#: from collapsing into one another.
ACTS_BUT_NO_RULES = """\
%% clause: m9001   section: s   kind: definitional
%% acts: produce(M)
%% concepts:
%% requires:
%% inputs: new_material/1
%% closure: produce = cepa
asserts(m9001, forbid, produce(nothing)).
"""


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def _m0217_report(tmp_path, text=M0217_LEGACY, concepts=M0217_CONCEPTS, **kw):
    p = _write(tmp_path, "m0217.lp", text)
    return probe.probe_clause(p, [], concepts, **kw)


def _labelling(sit_id, label, reason="because the clause says so"):
    return probe.Labelling(sit_id, label, reason)


def _m0217_labels(rep):
    """The labels a seat SHOULD return, read off the CLAUSE TEXT.

    ⚠️ Deliberately NOT read off the module's derived statuses — that would
    make test 4 circular, since the mutant is the module. The clause says
    political content for a broad audience is allowed as long as it does not
    exploit an individual; it says nothing about anything else.
    """
    out = []
    for s in rep.covering:
        t = s.true_atoms
        permit = ("political_content(x)" in t and "broad_audience(x)" in t
                  and "exploits_individual(x)" not in t)
        out.append(probe.Labelling(
            s.id, "must-permit" if permit else "must-be-silent",
            "read off the clause text"))
    return tuple(out)


# ==========================================================================
#  Registration — the same diff, every time
# ==========================================================================

def test_registration_structural_disclosable_verdict_never():
    """⛔ THE LEAK PERIMETER, as a test.

    `probe-structural` must be admitted to the repair log and `probe-verdict`
    must never be. The control is the second half: a filter that admits
    everything is as wrong as one that admits nothing.
    """
    assert probe.STRUCTURAL_ORIGIN in translate.DISCLOSABLE_ORIGINS
    assert probe.VERDICT_ORIGIN not in translate.DISCLOSABLE_ORIGINS


def test_registration_no_new_severity(tmp_path):
    """§8: `checks.SEVERITIES` is NOT extended. Probe findings are error/note."""
    assert checks.SEVERITIES == ("error", "note")
    rep = _m0217_report(tmp_path, text=OVER_CONSTRAINED)
    assert rep.findings, "this fixture must produce findings to check"
    for f in rep.findings:
        assert f.severity in checks.SEVERITIES
        assert f.origin == probe.STRUCTURAL_ORIGIN


def test_registration_only_two_outcomes_aggregate():
    assert set(probe.OUTCOMES) == {"passed", "failed", "no-testable-content",
                                   "signature-too-large"}
    assert probe.AGGREGATING_OUTCOMES == ("passed", "failed")
    for o in ("no-testable-content", "signature-too-large"):
        assert o not in probe.AGGREGATING_OUTCOMES


# ==========================================================================
#  1 — the signature, and the guard whose fire condition revision 2 got wrong
# ==========================================================================

def test_1_signature_from_inputs_only_is_EMPTY_and_that_is_an_error(tmp_path):
    """⭐ FIRES: an empty situation signature is an ERROR, never a green run.

    ⚠️ Revision 2 wrote this guard as `|enumeration| == 0`. That guard never
    fires on the bug it names: an empty signature yields 2^0 = ONE situation,
    not zero, so an `inputs`-only build of `m0217` sails past it reporting one
    all-false situation and green.
    """
    # The bug, reproduced: the signature built from `inputs` alone.
    naive = probe.situation_signature(M0217_LEGACY, [], concepts=[])
    assert naive == (), "m0217's inputs are empty; this is the bug's input"
    assert len(probe.ground_atoms(naive, [M0217_LEGACY])) == 0
    # ... and the enumeration over it is NOT empty. This is why the old guard
    # was vacuous.
    enum = probe.enumerate_situations(M0217_LEGACY, [], ())
    assert enum.candidates == 1

    rep = _m0217_report(tmp_path, concepts=[])
    assert rep.outcome == "failed"
    ids = {f.check_id for f in rep.findings if f.severity == "error"}
    assert "signature-empty" in ids


def test_1_control_signature_reads_the_concept_table(tmp_path):
    """SILENT: with the concept table, the signature is the three predicates."""
    sig = probe.situation_signature(M0217_LEGACY, [], M0217_CONCEPTS)
    assert set(sig) == {"political_content/1", "broad_audience/1",
                        "exploits_individual/1"}
    rep = _m0217_report(tmp_path)
    assert "signature-empty" not in {f.check_id for f in rep.findings}


def test_1_control_m0255_shaped_all_predicates_in_inputs():
    """SILENT: a module whose predicates genuinely are all in `inputs`.

    ⚠️ This is the branch that matters going forward: today's schema REFUSES
    the legacy shape (`body references political_content but nothing declares
    it`), so every module translated from now on is m0255-shaped.
    """
    text = open(M0255, encoding="utf-8").read()
    links = [open(p, encoding="utf-8").read() for p in M0255_LINK]
    sig = probe.situation_signature(text, links, concepts=[])
    assert "forbids/2" in sig and "new_material/1" in sig
    # `policy_class/2` is REQUIRED and PROVIDED at link scope — not free.
    assert "policy_class/2" not in sig


# ==========================================================================
#  2, 3 — suppression is data, never a silent filter
# ==========================================================================

OVER_CONSTRAINED = M0217_LEGACY + """\
:- political_content(x).
:- not political_content(x).
"""


def test_2_empty_coherent_set_is_an_error(tmp_path):
    """FIRES: an over-constrained module enumerates nothing → ERROR.

    "All 0 situations matched" is the pass-looks-like-did-not-run shape.
    """
    rep = _m0217_report(tmp_path, text=OVER_CONSTRAINED)
    assert rep.coherent == 0
    assert rep.outcome == "failed"
    assert "coherent-set-empty" in {f.check_id for f in rep.findings}


def test_2_control_suppression_is_reported_not_errored():
    """SILENT: m0255 suppresses real states and that is NOT an error."""
    rep = probe.probe_clause(M0255, M0255_LINK, concepts=[])
    assert rep.suppressed > 0, "m0255's own constraints reject states"
    ids = {f.check_id for f in rep.findings if f.severity == "error"}
    assert "coherent-set-empty" not in ids
    assert "suppression-excessive" not in ids


def test_3_suppressed_count_is_printed_even_when_zero(tmp_path):
    rep = _m0217_report(tmp_path)
    assert rep.suppressed == 0
    assert "suppressed" in rep.to_json()
    assert rep.to_json()["suppressed"] == 0
    assert "suppressed 0" in rep.render() or "suppressed: 0" in rep.render()


def test_3_control_zero_suppression_acquires_no_warning(tmp_path):
    """SILENT: a warning on every run becomes invisible — link.py's own lesson."""
    rep = _m0217_report(tmp_path)
    assert [f for f in rep.findings if f.check_id == "suppression-excessive"] == []


# ==========================================================================
#  4 — ⭐ THE TEST THIS WHOLE DOCUMENT EXISTS FOR
# ==========================================================================

M0217_EMPTIED = "\n".join(
    ln for ln in M0217_LEGACY.splitlines()
    if not ln.startswith("asserts(") and "not exploits_individual" not in ln
) + "\n"


def test_4_deleting_the_only_rule_MISMATCHES_under_three_valued_labels(tmp_path):
    """⭐ FIRES: the emptied module loses its one derived atom → mismatch.

    ⚠️ Under the naive closure-resolved comparison the SAME module scores
    8 of 8: `m0217` declares `produce = cepa`, silence permits, and every
    situation still resolves to `permit`. That is the failure this comparison
    is built to avoid, and it is asserted below as the control's negative.
    """
    good = _m0217_report(tmp_path)
    labels = _m0217_labels(good)
    assert probe.compare(good.covering, labels, "m0217") == ()

    bad_path = _write(tmp_path, "m0217_emptied.lp", M0217_EMPTIED)
    bad = probe.enumerate_situations(M0217_EMPTIED, [],
                                     probe.ground_atoms(
                                         probe.situation_signature(
                                             M0217_LEGACY, [], M0217_CONCEPTS),
                                         [M0217_LEGACY]))
    # Every situation in the good covering set, re-solved against the mutant.
    mutant_cover = tuple(s for s in bad.situations
                         if s.id in {c.id for c in good.covering})
    mm = probe.compare(mutant_cover, labels, "m0217")
    assert mm, ("the emptied module must mismatch; if this is empty the "
                "comparison has been folded through the closure again")
    assert any(m.label == "must-permit" for m in mm)
    assert os.path.exists(bad_path)


def test_4_control_the_unmutated_module_matches_and_reports_a_vector(tmp_path):
    """SILENT: 1 must-permit · 0 must-forbid · 3 must-be-silent, 0 mismatches."""
    good = _m0217_report(tmp_path)
    labels = _m0217_labels(good)
    dist = probe.label_distribution(labels)
    assert dist["must-permit"] == 1
    assert dist["must-forbid"] == 0          # printed as a NUMBER, not omitted
    assert dist["must-be-silent"] == 3
    assert probe.compare(good.covering, labels, "m0217") == ()


def test_4_the_naive_closure_resolved_comparison_would_have_passed_the_mutant():
    """⚠️ The measurement behind test 4, kept as an executable statement.

    `resolve_through_closure` exists ONLY here, is never used by the report,
    and is what §3 measured: 0 of 8 differ. If someone "fixes" the comparison
    to resolve silence, this test still passes and test 4 goes red — which is
    the pairing that makes test 4 mean something.
    """
    atoms = probe.ground_atoms(
        probe.situation_signature(M0217_LEGACY, [], M0217_CONCEPTS),
        [M0217_LEGACY])
    good = probe.enumerate_situations(M0217_LEGACY, [], atoms)
    bad = probe.enumerate_situations(M0217_EMPTIED, [], atoms)
    differ = [s.id for s in good.situations
              if probe.resolve_through_closure(s, "m0217", "cepa")
              != probe.resolve_through_closure(
                  {x.id: x for x in bad.situations}[s.id], "m0217", "cepa")]
    assert differ == [], "the naive comparison is blind here — that is the point"


# ==========================================================================
#  5 — the closure declaration is carried, never resolved through
# ==========================================================================

def test_5_a_closure_resolved_projection_is_refused_at_construction(tmp_path):
    good = _m0217_report(tmp_path)
    labels = _m0217_labels(good)
    with pytest.raises(ValueError, match="closure"):
        probe.compare(good.covering, labels, "m0217",
                      projection="closure-resolved")


def test_5_control_the_report_carries_the_closure_verbatim_untested(tmp_path):
    rep = _m0217_report(tmp_path)
    assert rep.closure_declared == {"produce": "cepa"}
    assert "produce = cepa" in rep.render()
    assert "NOT TESTED HERE" in rep.render()


# ==========================================================================
#  6, 7 — discrimination coverage, and the criterion that does not work
# ==========================================================================

def _c3_rule_indices(text):
    return [i for i, st in probe.module_rules(text)
            if st.strip().startswith("binds(") and "new_material" in st]


def test_6_deleting_m0255s_C3_rules_leaves_C3_UNCOVERED():
    """⭐ FIRES: discrimination coverage names C3 as uncovered.

    A whole claim of the walkthrough's flagship clause is behaviourally dead.
    Neither `link.py` nor the five hand-written probe cases caught it.
    """
    text = open(M0255, encoding="utf-8").read()
    c3 = _c3_rule_indices(text)
    assert len(c3) == 2, "m0255 encodes C3 as two rules"
    claims_map = {i: "C3" for i in c3}
    rep = probe.probe_clause(M0255, M0255_LINK, concepts=[],
                             claims_map=claims_map)
    assert rep.coverage.rules_mutated >= 2
    assert set(c3) <= set(rep.coverage.uncovered_rules)
    assert "C3" in rep.coverage.claim_coverage.uncovered
    assert "C3: uncovered" in rep.render()


def test_6_control_RULE_coverage_calls_the_same_rules_covered():
    """SILENT — and this control IS the finding.

    The rules FIRE. Rule coverage passes them. That is why `03_pipeline.md`
    Part 1 #12's named remedy is substituted, and why the substitution is
    recorded in `STATE.md` as a departure rather than described as conformance.
    """
    text = open(M0255, encoding="utf-8").read()
    links = [open(p, encoding="utf-8").read() for p in M0255_LINK]
    atoms = probe.ground_atoms(
        probe.situation_signature(text, links, concepts=[]), [text] + links)
    fired = probe.rule_coverage(text, links, atoms)
    for i in _c3_rule_indices(text):
        assert fired[i] is True, "rule coverage is satisfied by these rules"


def test_7_an_input_with_no_discriminating_pair_is_NAMED():
    rep = probe.probe_clause(M0255, M0255_LINK, concepts=[])
    named = set(rep.undiscriminated_inputs)
    assert "new_material(x)" in named
    assert "new_material(x)" in rep.render()


def test_7_control_an_input_with_a_discriminating_pair_is_not_named():
    rep = probe.probe_clause(M0255, M0255_LINK, concepts=[])
    named = set(rep.undiscriminated_inputs)
    assert "transformation_of_user_content(x)" not in named
    assert named != set(rep.enumeration.atoms), "a check that names everything"


# ==========================================================================
#  8 — #14 claims are counted and EXCLUDED from the denominator
# ==========================================================================

def test_7b_the_covering_set_actually_REDUCES(tmp_path):
    """⭐ FIRES on a "reduction" that returns the whole enumeration.

    ⚠️ FOUND BY RUNNING IT, not by review. The first implementation took every
    situation belonging to any discriminating pair; on `m0255` that is 180 of
    180 coherent situations — the enumeration, renamed. The covering set is
    what the labelling seat is SHOWN and what the [L] half is PRICED on, so a
    reduction that reduces nothing turns one cheap call into a 180-row table
    and reports it as a covering set. MC/DC takes ONE pair per input.
    """
    rep = probe.probe_clause(M0255, M0255_LINK, concepts=[])
    k = len(rep.enumeration.atoms)
    assert len(rep.covering) <= 2 * k, "an MC/DC covering set is bounded by 2k"
    assert len(rep.covering) < rep.coherent, "this is a reduction or it is not"


def test_7b_control_m0217s_covering_set_is_the_firing_situation_plus_neighbours(
        tmp_path):
    """SILENT: 4 of 8 — and every one of them is a real single-flip neighbour."""
    rep = _m0217_report(tmp_path)
    assert len(rep.covering) == 4
    assert rep.coherent == 8
    firing = [s for s in rep.covering
              if probe.derived_status(s, "m0217") == frozenset({"permit"})]
    assert len(firing) == 1
    for s in rep.covering:
        if s.id != firing[0].id:
            assert len(s.true_atoms ^ firing[0].true_atoms) == 1


def test_8_a_forbid_body_claim_inside_the_denominator_is_refused():
    with pytest.raises(ValueError, match="forbid_body"):
        probe.ClaimCoverage(covered=("C1",), uncovered=("C3",),
                            forbid_body_claims=("C3",))


def test_8_control_forbid_body_claims_counted_outside_the_denominator():
    cc = probe.ClaimCoverage(covered=("C1",), uncovered=("C3",),
                             forbid_body_claims=("C4",))
    assert cc.denominator == 2
    assert cc.forbid_body_claims == ("C4",)


# ==========================================================================
#  9, 10 — what crosses into a repair prompt, and what re-runs stage 1
# ==========================================================================

def _structural():
    return checks.Finding("probe-impossible-situation", "error", "m0217.lp",
                          "the module admits a situation the clause treats as "
                          "impossible: S6", probe.STRUCTURAL_ORIGIN)


def _verdict():
    return checks.Finding("probe-verdict-mismatch", "error", "m0217.lp",
                          "situation S6 derived permit but is labelled "
                          "must-forbid", probe.VERDICT_ORIGIN)


def test_9_a_probe_verdict_finding_is_withheld_with_a_visible_hole():
    log = translate.render_error_log([("attempt 1", [_verdict()])])
    assert "must-forbid" not in log
    assert "S6" not in log
    assert "withheld" in log


def test_9_control_a_probe_structural_finding_is_rendered_in_full():
    log = translate.render_error_log([("attempt 1", [_structural()])])
    assert "impossible" in log
    assert "withheld" not in log


def test_10_routing_a_verdict_finding_into_the_transcript_is_refused():
    with pytest.raises(probe.DisclosureRefused):
        probe.append_findings_to_transcript([{"role": "user", "content": "x"}],
                                            [_verdict()])


def test_10_control_re_translation_carries_an_EMPTY_transcript():
    r = probe.route([_verdict()], retranslations_used=0, max_retranslations=1)
    assert r.action == "re-translate"
    assert r.transcript == ()
    # The label text must appear in NO message of the next call.
    for msg in r.transcript:
        assert "must-forbid" not in json.dumps(msg)
    r2 = probe.route([_verdict()], retranslations_used=1, max_retranslations=1)
    assert r2.action == "carry" and r2.status == "probe-mismatch"
    r3 = probe.append_findings_to_transcript([], [_structural()])
    assert r3 and "impossible" in json.dumps(r3)


# ==========================================================================
#  11 — the denominator is computed here, never supplied by the seat
# ==========================================================================

def _cover_ids(tmp_path):
    return [s.id for s in _m0217_report(tmp_path).covering]


def test_11_an_incomplete_or_unreasoned_labelling_is_NOT_ADJUDICATED(tmp_path):
    rep = _m0217_report(tmp_path)
    ids = [s.id for s in rep.covering]
    full = tuple(_labelling(i, "must-be-silent") for i in ids)

    with pytest.raises(probe.NotAdjudicated, match="missing"):
        probe.adjudicate(rep.covering, full[:-1])
    with pytest.raises(probe.NotAdjudicated, match="not enumerated"):
        probe.adjudicate(rep.covering, full + (_labelling("S999", "must-permit"),))
    with pytest.raises(probe.NotAdjudicated, match="reason"):
        probe.adjudicate(rep.covering,
                         full[:-1] + (probe.Labelling(ids[-1], "must-permit", "  "),))


def test_11_control_a_complete_labelling_with_reasons_is_adjudicated(tmp_path):
    rep = _m0217_report(tmp_path)
    full = tuple(_labelling(s.id, "must-be-silent") for s in rep.covering)
    assert probe.adjudicate(rep.covering, full) == full


# ==========================================================================
#  12, 13 — what the seat is shown, and what it is denied
# ==========================================================================

CLAUSE_TEXT = ("However, political content that is crafted for an unspecified "
               "or broad audience is allowed, as long as it does not exploit "
               "the unique characteristics of a particular individual.")


def _prompt(**over):
    kw = dict(clause_text=CLAUSE_TEXT, cross_reference_texts=(),
              act_phrase="produce this material",
              situations=("S6\n  yes: the material concerns a political topic",))
    kw.update(over)
    return probe.build_seat_prompt(**kw)


@pytest.mark.parametrize("leak", [
    "political_content/1",                       # 12 — a coined signature
    "asserts(m0217, permit, produce(M))",        # 13 — the module
    "derived: permit",                           # 13 — the derived status
    "closure: produce = cepa",                   # 13 — the closure declaration
    "CLAIMS: C1 political content is allowed",   # 13 — the translator's reading
])
def test_12_13_a_seat_prompt_carrying_the_module_is_refused(leak):
    with pytest.raises(probe.DisclosureRefused):
        _prompt(situations=("S6\n  yes: " + leak,))


def test_12_13_control_glosses_and_cross_references_are_allowed():
    p = _prompt(cross_reference_texts=("Prohibited content should never be "
                                       "produced by the assistant.",))
    assert "political topic" in p
    assert "must-be-silent" in p, "the seat is told silence is a real answer"
    assert "political_content" not in p


# ==========================================================================
#  14, 17 — the two independent refusals, which must not collapse
# ==========================================================================

def test_14_a_module_with_no_acts_is_NO_TESTABLE_CONTENT(tmp_path):
    p = _write(tmp_path, "m0037.lp", M0037_NO_RULES)
    rep = probe.probe_clause(p, [], concepts=[])
    assert rep.outcome == "no-testable-content"
    assert "no-acts" in rep.reasons
    assert rep.outcome not in probe.AGGREGATING_OUTCOMES


def test_17_a_module_with_ACTS_and_zero_rules_is_still_refused(tmp_path):
    """⭐ The refusal keys on `|R|`, NOT on the empty acts list.

    Without this the two paths collapse and `m0037` is the only witness — so a
    future module carrying acts and no mutable rule would score `0 uncovered of
    0` and pass.
    """
    p = _write(tmp_path, "m9001.lp", ACTS_BUT_NO_RULES)
    rep = probe.probe_clause(p, [], concepts=[])
    assert rep.outcome == "no-testable-content"
    assert "zero-rules" in rep.reasons
    assert "no-acts" not in rep.reasons
    assert rep.coverage is None


def test_14_17_control_m0217_has_both_and_passes(tmp_path):
    rep = _m0217_report(tmp_path)
    assert rep.outcome == "passed"
    assert rep.reasons == ()
    assert rep.coverage.rules_mutated == 1
    assert rep.coverage.uncovered_rules == ()


# ==========================================================================
#  15 — a single-number pass rate is refused anywhere in the output
# ==========================================================================

def test_15_a_per_clause_pass_rate_is_refused(tmp_path):
    with pytest.raises(ValueError, match="pass rate"):
        probe.refuse_pass_rate({"clause": "m0217", "pass_rate": 1.0})
    with pytest.raises(ValueError, match="pass rate"):
        probe.refuse_pass_rate({"clause": "m0217", "situations_passed": "8/8"})
    rep = _m0217_report(tmp_path)
    rep.extra["pass_rate"] = 1.0
    with pytest.raises(ValueError, match="pass rate"):
        rep.to_json()


def test_15_control_the_label_vector_and_discriminating_count_are_allowed(tmp_path):
    probe.refuse_pass_rate({"labels": {"must-permit": 1, "must-forbid": 0},
                            "discriminating_situations": 1})
    rep = _m0217_report(tmp_path)
    j = rep.to_json()
    assert j["discriminating_situations"] == 1
    assert not any("pass_rate" in k for k in j)


# ==========================================================================
#  16 — the one label that is not a verdict is the one that may be disclosed
# ==========================================================================

def test_16_an_impossible_label_produces_a_STRUCTURAL_finding(tmp_path):
    rep = _m0217_report(tmp_path)
    ids = [s.id for s in rep.covering]
    labels = (probe.Labelling(ids[0], "impossible", "both cannot hold"),) + \
        tuple(_labelling(i, "must-be-silent") for i in ids[1:])
    fs = probe.impossible_findings(rep.covering, labels, "m0217")
    assert len(fs) == 1
    assert fs[0].origin == probe.STRUCTURAL_ORIGIN
    assert ids[0] in fs[0].message
    for verdict_word in ("permit", "forbid", "silent"):
        assert verdict_word not in fs[0].message


def test_16_control_a_must_label_produces_no_structural_finding(tmp_path):
    rep = _m0217_report(tmp_path)
    labels = tuple(_labelling(s.id, "must-permit") for s in rep.covering)
    assert probe.impossible_findings(rep.covering, labels, "m0217") == ()


# ==========================================================================
#  18 — |R| is not decoration
# ==========================================================================

def test_18_a_coverage_report_without_R_is_refused():
    with pytest.raises(ValueError, match=r"\|R\|"):
        probe.CoverageReport(criterion="discrimination", rules_mutated=None,
                             per_rule={}, uncovered_rules=())


def test_18_control_R_renders_next_to_the_coverage_line(tmp_path):
    """SILENT — and the control is the real test: `0/0 covered` and
    `11/11 covered` must never render the same way."""
    rep = _m0217_report(tmp_path)
    out = rep.render()
    assert "|R| = 1" in out
    zero = probe.CoverageReport(criterion="discrimination", rules_mutated=0,
                                per_rule={}, uncovered_rules=())
    assert "|R| = 0" in zero.render()
    assert zero.render() != rep.coverage.render()


# ==========================================================================
#  19 — the cap, printed on every report
# ==========================================================================

def _wide(n):
    preds = [f"p{i}" for i in range(n)]
    head = ("%% clause: m9002   section: s   kind: conditional\n"
            "%% acts: produce(M)\n%% concepts:\n%% requires:\n"
            "%% inputs: " + ", ".join(f"{p}/1" for p in preds) + "\n"
            "%% closure: produce = cepa\n")
    body = ", ".join(f"{p}(M)" for p in preds)
    return head + f"asserts(m9002, forbid, produce(M)) :- {body}.\n"


def test_19_a_signature_over_the_cap_is_refused_and_nothing_is_enumerated(tmp_path):
    cfg = {"probe": {"max_signature": 10}}
    p = _write(tmp_path, "m9002.lp", _wide(11))
    rep = probe.probe_clause(p, [], concepts=[], cfg=cfg)
    assert rep.outcome == "signature-too-large"
    assert rep.outcome not in probe.AGGREGATING_OUTCOMES
    assert rep.ground_atom_count == 11
    assert rep.enumeration is None, "no truncated or sampled enumeration"
    assert rep.covering == ()
    assert "cap 2^10" in rep.render()


def test_19_control_exactly_at_the_cap_enumerates_and_prints_WITHIN_CAP(tmp_path):
    cfg = {"probe": {"max_signature": 10}}
    p = _write(tmp_path, "m9003.lp", _wide(10))
    rep = probe.probe_clause(p, [], concepts=[], cfg=cfg)
    assert rep.outcome in probe.AGGREGATING_OUTCOMES
    assert rep.candidates == 1024
    assert "WITHIN CAP" in rep.render()


def test_19_control_the_cap_prints_when_well_under_it(tmp_path):
    """A cap visible only on failure is indistinguishable from no cap."""
    rep = _m0217_report(tmp_path)
    assert "cap 2^10" in rep.render()
    assert "WITHIN CAP" in rep.render()


# ==========================================================================
#  The committed run — these FAIL, never skip, if it is missing
# ==========================================================================

def test_the_committed_m0217_passes_stage_3_end_to_end():
    assert os.path.isdir(RUN), (
        f"{RUN} is missing: this check cannot run, and a check that cannot run "
        f"must not exit like a check that passed")
    concepts = json.load(open(os.path.join(RUN, "concepts.json"),
                              encoding="utf-8"))
    rep = probe.probe_clause(os.path.join(RUN, "m0217.lp"), [], concepts)
    assert rep.outcome == "passed"
    assert rep.coverage.rules_mutated == 1
    assert rep.discriminating == 1


def test_the_committed_m0037_is_no_testable_content():
    assert os.path.isdir(RUN)
    concepts = json.load(open(os.path.join(RUN, "concepts.json"),
                              encoding="utf-8"))
    rep = probe.probe_clause(os.path.join(RUN, "m0037.lp"), [], concepts)
    assert rep.outcome == "no-testable-content"
    assert rep.outcome not in probe.AGGREGATING_OUTCOMES


# ==========================================================================
#  The [L] seam — driven by a stub, and nothing here may spend
# ==========================================================================

class _StubSeat:
    """Returns a complete labelling. The ONLY labeller any test ever sees."""

    def __init__(self, labels):
        self.labels = labels
        self.calls = []

    def complete_messages(self, system, messages):
        self.calls.append((system, messages))
        return json.dumps({"labels": [dict(situation=i, label=l, reason="r")
                                      for i, l in self.labels]})


def test_the_labelling_half_runs_entirely_through_the_client_factory(tmp_path):
    rep = _m0217_report(tmp_path)
    ids = [s.id for s in rep.covering]
    stub = _StubSeat([(i, "must-be-silent") for i in ids])
    out = probe.label_situations(rep, CLAUSE_TEXT, (), "produce this material",
                                 M0217_CONCEPTS,
                                 client_factory=lambda: stub)
    assert len(out) == len(ids)
    assert stub.calls, "the seam was not used"
    sent = json.dumps(stub.calls)
    assert "political_content" not in sent
    assert "asserts(" not in sent


def test_no_labelling_path_can_reach_a_live_client(tmp_path):
    """⛔ Omitting the factory must RAISE, never silently build a real client."""
    rep = _m0217_report(tmp_path)
    with pytest.raises(probe.ProbeError, match="client_factory"):
        probe.label_situations(rep, CLAUSE_TEXT, (), "produce this material",
                               M0217_CONCEPTS, client_factory=None)
