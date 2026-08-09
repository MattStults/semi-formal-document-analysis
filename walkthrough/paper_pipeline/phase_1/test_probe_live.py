"""The live driver for stage 3's LABELLED half — every guard, with its control.

⭐ SAME BAR AS `test_probe.py`: every test names the guard it pins AND a paired
negative control that must stay SILENT. A check that fires on everything is
pinned by nothing.

⛔ NOTHING HERE TOUCHES THE NETWORK. The one test that would — the fence over
the shipped clause-spec file — reads artifacts already on disk and builds
prompts offline. It FAILS, never skips, when the runs are missing: a check that
cannot run must not exit like a check that passed (DEBUGGING_TIPS #8).
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

import link                                                    # noqa: E402
import probe                                                   # noqa: E402
import probe_live                                              # noqa: E402
import translate                                               # noqa: E402

SPECS = os.path.join(HERE, "probe_live_clauses.json")


# ==========================================================================
#  Stubs. They mirror `translate.Client._send`'s ORDERING, which is the thing
#  under test: `response_envelope` runs on the parsed body BEFORE any guard.
# ==========================================================================

class _Prov:
    name, model = "stub", "stub-model"
    price_per_mtok = [0.14, 0.28]
    max_tokens = 4096


def _payload(text, prompt_tokens=100, completion_tokens=50):
    return {"choices": [{"message": {"content": text},
                         "finish_reason": "stop"}],
            "usage": {"prompt_tokens": prompt_tokens,
                      "completion_tokens": completion_tokens}}


class _StubClient:
    """Answers every situation `must-be-silent`, in the shape the seat asks."""

    def __init__(self, label="must-be-silent", raise_after_envelope=False,
                 text=None):
        self.label = label
        self.raise_after_envelope = raise_after_envelope
        self.text = text
        self.calls = 0

    def complete_messages(self, system, messages):
        self.calls += 1
        ids = [ln.strip() for ln in messages[-1]["content"].splitlines()
               if ln.strip().startswith("S") and ln.strip()[1:].isdigit()]
        body = self.text if self.text is not None else json.dumps(
            {"labels": [{"situation": i, "label": self.label,
                         "reason": "stub"} for i in ids]})
        env = translate.response_envelope(_Prov(), _payload(body))
        if self.raise_after_envelope:
            raise translate.ProviderError("completion was TRUNCATED (stub)")
        return env


class _ExplodingClient:
    def complete_messages(self, system, messages):
        raise AssertionError("a dry run must not reach a client at all")


def _specs(n=1):
    cfg = translate.load_config(os.path.join(HERE, "config.json"))
    return probe_live.load_specs(SPECS, cfg)[:n]


# ==========================================================================
#  1 — a driver that spends unless told not to is the mistake a revert
#      cannot undo
# ==========================================================================

def test_1_a_dry_run_never_reaches_a_client(tmp_path):
    boom = _ExplodingClient()
    out = probe_live.run(_specs(2), str(tmp_path), live=False, repeats=2,
                         client_factory=lambda: boom)
    assert out["measured_usd"] == 0.0
    assert all(r["status"].startswith("dry-run") for r in out["results"])


def test_1_control_a_live_run_with_a_stub_DOES_call(tmp_path):
    stub = _StubClient()
    out = probe_live.run(_specs(1), str(tmp_path), live=True, repeats=2,
                         client_factory=lambda: stub)
    assert stub.calls == 2
    assert [r["status"] for r in out["results"]] == ["adjudicated"] * 2


def test_1_control_label_situations_still_refuses_a_missing_factory(tmp_path):
    """The seam the driver drives must not have been widened to build one."""
    spec = _specs(1)[0]
    rep, rows, _rendered, _prompt = probe_live.build(spec)
    with pytest.raises(probe.ProbeError, match="client_factory"):
        probe.label_situations(rep, spec.clause_text,
                               list(spec.cross_reference_texts),
                               spec.act_phrase, rows, client_factory=None)


# ==========================================================================
#  2 — ⛔ RAW FIRST. `eval.py` made 36 paid calls and kept only findings.
# ==========================================================================

def test_2_the_raw_payload_survives_a_call_that_RAISES_after_billing(tmp_path):
    seat = probe_live.RawFirstSeatClient(
        _StubClient(raise_after_envelope=True), str(tmp_path / "m9999"))
    with pytest.raises(translate.ProviderError):
        seat.complete_messages("sys", [{"role": "user", "content": "S0"}])
    raw = tmp_path / "m9999.r0.raw.json"
    assert raw.exists(), ("the call was billed and the bytes are gone; that is "
                          "the eval.py defect, reproduced")
    assert "choices" in json.loads(raw.read_text())


def test_2_control_a_successful_call_writes_the_raw_and_the_envelope(tmp_path):
    seat = probe_live.RawFirstSeatClient(_StubClient(),
                                         str(tmp_path / "m9999"))
    text = seat.complete_messages("sys", [{"role": "user", "content": "S0"}])
    assert json.loads(text)["labels"][0]["situation"] == "S0"
    assert (tmp_path / "m9999.r0.raw.json").exists()
    assert (tmp_path / "m9999.r0.envelope.json").exists()


def test_2_the_WIRE_REQUEST_is_saved_even_when_the_call_raises(tmp_path):
    """The fence can only be audited against what was SENT."""
    seat = probe_live.RawFirstSeatClient(
        _StubClient(raise_after_envelope=True), str(tmp_path / "m9999"))
    with pytest.raises(translate.ProviderError):
        seat.complete_messages("sys", [{"role": "user", "content": "S0"}])
    req = json.loads((tmp_path / "m9999.r0.request.json").read_text())
    assert req["system"] == "sys"
    assert req["messages"][0]["content"] == "S0"


def test_2_control_the_spy_is_removed_again(tmp_path):
    before = translate.response_envelope
    seat = probe_live.RawFirstSeatClient(
        _StubClient(raise_after_envelope=True), str(tmp_path / "m9999"))
    with pytest.raises(translate.ProviderError):
        seat.complete_messages("sys", [{"role": "user", "content": "S0"}])
    assert translate.response_envelope is before


# ==========================================================================
#  3 — the act phrase is SUPPLIED. §5 denies the seat the coined act term.
# ==========================================================================

def test_3_a_spec_without_an_act_phrase_is_REFUSED(tmp_path):
    with pytest.raises(probe_live.LiveProbeError, match="act_phrase"):
        probe_live.ClauseSpec(clause_id="m0217", module="x.lp",
                              act_phrase="", clause_text="text")


def test_3_control_a_supplied_phrase_constructs(tmp_path):
    s = probe_live.ClauseSpec(clause_id="m0217", module="x.lp",
                              act_phrase="produce the material described",
                              clause_text="text")
    assert s.act_phrase


def test_3_a_spec_without_clause_text_is_REFUSED():
    with pytest.raises(probe_live.LiveProbeError, match="clause text"):
        probe_live.ClauseSpec(clause_id="m0217", module="x.lp",
                              act_phrase="produce it", clause_text="")


# ==========================================================================
#  4 — ⭐ THE FENCE, on the prompts actually sent
# ==========================================================================

def test_4_every_shipped_spec_builds_a_prompt_that_passes_the_fence():
    """FAILS, never skips, if the committed runs are missing."""
    cfg = translate.load_config(os.path.join(HERE, "config.json"))
    specs = probe_live.load_specs(SPECS, cfg)
    assert specs, "the clause-spec file selects nothing"
    built = 0
    for spec in specs:
        assert os.path.exists(spec.module), spec.module
        # ⚠️ A spec BLOCKED on an unglossed borrow is not a pass and not a
        # skip. `test_q22_blocked_specs_are_blocked_for_a_REAL_reason` proves
        # each block is genuine; this test asserts the rest still build, and
        # that the set is not empty — otherwise "every spec builds" would be
        # vacuously true the moment everything blocked.
        try:
            _rep, _rows, _rendered, prompt = probe_live.build(spec)
        except probe_live.UnglossedSignature:
            continue
        built += 1
        body = prompt[len(probe.SEAT_BRIEF):]
        # `build_seat_prompt` already refused the module; this re-checks the
        # ASSEMBLED text, which is what actually goes on the wire.
        probe._refuse_disclosure(body, "the assembled seat prompt")
        assert spec.clause_text.strip()[:40] in prompt
    assert built, ("every shipped spec is blocked, so this test asserted "
                   "nothing — see DEBUGGING_TIPS §8")


def test_4_control_a_prompt_carrying_a_coined_name_is_refused():
    with pytest.raises(probe.DisclosureRefused):
        probe.build_seat_prompt("clause", [], "produce it",
                                ["S0\n  yes: political_content/1"])


def test_4_control_a_prompt_carrying_the_closure_is_refused():
    with pytest.raises(probe.DisclosureRefused):
        probe.build_seat_prompt("clause", [], "produce it",
                                ["S0", "closure: produce = cepa"])


# ==========================================================================
#  5 — the budget. An estimate is printed before every batch and enforced
#      while the batch runs.
# ==========================================================================

def test_5_an_estimate_over_the_budget_sends_NOTHING(tmp_path):
    boom = _ExplodingClient()
    with pytest.raises(probe_live.BudgetExceeded):
        probe_live.run(_specs(1), str(tmp_path), live=True, repeats=1,
                       budget=0.0000001, client_factory=lambda: boom)


def test_5_control_an_estimate_under_the_budget_proceeds(tmp_path):
    stub = _StubClient()
    out = probe_live.run(_specs(1), str(tmp_path), live=True, repeats=1,
                         budget=0.50, client_factory=lambda: stub)
    assert out["measured_usd"] > 0
    assert stub.calls == 1


def test_5_measured_spend_stops_the_run_at_the_ceiling(tmp_path):
    """The estimate is worst-case; the MEASURED total is what binds."""

    class _Expensive(_StubClient):
        def complete_messages(self, system, messages):
            self.calls += 1
            ids = [ln.strip() for ln in messages[-1]["content"].splitlines()
                   if ln.strip().startswith("S") and ln.strip()[1:].isdigit()]
            body = json.dumps({"labels": [
                {"situation": i, "label": "must-be-silent", "reason": "s"}
                for i in ids]})
            return translate.response_envelope(
                _Prov(), _payload(body, prompt_tokens=10 ** 7,
                                  completion_tokens=10 ** 7))

    exp = _Expensive()
    with pytest.raises(probe_live.BudgetExceeded, match="reached"):
        probe_live.run(_specs(1), str(tmp_path), live=True, repeats=4,
                       budget=0.50, client_factory=lambda: exp)
    assert exp.calls >= 1, "it must stop AFTER a call, not before any"
    assert exp.calls < 4, "and it must stop BEFORE the batch finishes"


def test_5_cost_is_read_from_BOTH_shapes_the_envelope_can_take(tmp_path):
    """⛔ It read only the nested key and printed $0.0000 on 7 billed calls.

    `response_envelope` puts `cost_usd` inside `usage`; `Client._send` returns
    `_check_envelope`'s rebuilt `{text, in, out}` with `cost_usd` beside them.
    A total that reads "free" because it looked in one place is the
    measured-nothing failure DEBUGGING_TIPS #2 is about.
    """
    seat = probe_live.RawFirstSeatClient(None, str(tmp_path / "m"))
    seat.envelopes = [{"cost_usd": 0.25}, {"usage": {"cost_usd": 0.25}}]
    assert seat.spent_usd == 0.5


def test_5_control_a_call_with_no_cost_at_all_is_OVER_budget(tmp_path):
    seat = probe_live.RawFirstSeatClient(None, str(tmp_path / "m"))
    seat.envelopes = [{"text": "hi"}]
    with pytest.raises(probe_live.BudgetExceeded, match="never as free"):
        seat.spent_usd


def test_5_control_an_unpriced_provider_counts_as_OVER_budget():
    class _Unpriced:
        name = "unpriced"
        price_per_mtok = None
    cfg = translate.load_config(os.path.join(HERE, "config.json"))
    with pytest.raises(probe_live.BudgetExceeded, match="price_per_mtok"):
        probe_live.estimate_usd(["prompt"], _Unpriced(), cfg)


# ==========================================================================
#  6 — ⭐ the silent-rate, and DEBUGGING_TIPS #2: never a rate without its
#      denominator
# ==========================================================================

def test_6_a_rate_over_nothing_reads_NOT_MEASURED_not_zero():
    sr = probe_live.silent_rate([])
    assert sr["rate"] is None and sr["denominator"] == 0
    assert "NOT MEASURED" in probe_live.render_silent_rate(sr)
    assert "0.000" not in probe_live.render_silent_rate(sr)


def test_6_control_a_real_rate_prints_its_denominator():
    labs = [probe.Labelling("S0", "must-be-silent", "r"),
            probe.Labelling("S1", "must-permit", "r")]
    sr = probe_live.silent_rate(labs)
    assert sr == {"silent": 1, "denominator": 2, "rate": 0.5,
                  "distribution": probe.label_distribution(labs)}
    rendered = probe_live.render_silent_rate(sr)
    assert "1/2" in rendered and "0.500" in rendered


# ==========================================================================
#  7 — ⭐ the k histogram. It REPORTS; it never re-sets the cap.
# ==========================================================================

_TWO_ATOMS_ONE_PREDICATE = """\
%% clause: m9002   section: s   kind: conditional
%% acts: produce(M)
%% concepts:
%% requires:
%% inputs: kindof/2
%% closure: produce = cepa
kind(a).
kind(b).
asserts(m9002, permit, produce(M)) :- kindof(M, K), kind(K).
"""


def test_7_k_counts_GROUND_ATOMS_not_predicates(tmp_path):
    p = tmp_path / "m9002.lp"
    p.write_text(_TWO_ATOMS_ONE_PREDICATE)
    rows, hist = probe_live.k_histogram([str(p)])
    assert rows[0]["predicates"] == 1
    assert rows[0]["k"] == 2, ("one predicate, two ground atoms — the cap "
                               "bounds the atoms (DECISION_stage3_build R1)")
    assert hist == {2: 1}


def test_7_control_the_histogram_does_not_touch_the_cap(tmp_path):
    before = probe.PROBE_DEFAULTS["max_signature"]
    p = tmp_path / "m9002.lp"
    p.write_text(_TWO_ATOMS_ONE_PREDICATE)
    probe_live.k_histogram([str(p)])
    assert probe.PROBE_DEFAULTS["max_signature"] == before
    assert "REPORTED, NOT ACTED ON" in probe_live.render_k_histogram(
        *probe_live.k_histogram([str(p)]))


def test_7_a_module_with_NO_RULES_is_a_row_with_no_k_not_a_k_of_ZERO(tmp_path):
    """⛔ `|R| = 0` returns before the signature is built.

    Counted as `k = 0` it lands in the smallest bucket and makes the
    distribution look comfortably under the cap — a histogram whose
    "did not measure" is indistinguishable from its smallest measurement.
    """
    p = tmp_path / "nope.lp"
    p.write_text("this is not asp at all (((")
    rows, hist = probe_live.k_histogram([str(p)])
    assert len(rows) == 1 and rows[0]["k"] is None
    assert rows[0]["outcome"] == "no-testable-content"
    assert hist == {}, "a module with no rules must not be counted as k = 0"


def test_7_control_a_module_WITH_rules_is_counted(tmp_path):
    p = tmp_path / "m9002.lp"
    p.write_text(_TWO_ATOMS_ONE_PREDICATE)
    _rows, hist = probe_live.k_histogram([str(p)])
    assert hist == {2: 1}


# ==========================================================================
#  8 — an unadjudicable reply is a REFUSAL, recorded with its raw
# ==========================================================================

def test_8_an_incomplete_reply_is_NOT_ADJUDICATED_and_never_a_mismatch(
        tmp_path):
    partial = _StubClient(text=json.dumps(
        {"labels": [{"situation": "S1", "label": "must-permit",
                     "reason": "r"}]}))
    out = probe_live.run(_specs(1), str(tmp_path), live=True, repeats=1,
                         client_factory=lambda: partial)
    row = out["results"][0]
    assert row["status"] == "NOT ADJUDICATED"
    assert "mismatches" not in row
    assert os.path.exists(row["raw"][0]), "the raw must survive a refusal"


def test_8_control_a_complete_reply_is_adjudicated(tmp_path):
    out = probe_live.run(_specs(1), str(tmp_path), live=True, repeats=1,
                         client_factory=lambda: _StubClient())
    row = out["results"][0]
    assert row["status"] == "adjudicated"
    assert "mismatches" in row and "silent_rate" in row


# ==========================================================================
#  9 — the covering set is what the seat is shown; an empty one is a refusal
# ==========================================================================

_NO_COVERING = """\
%% clause: m9003   section: s   kind: conditional
%% acts: produce(M)
%% concepts:
%% requires:
%% inputs:
%% closure: produce = cepa
asserts(m9003, permit, produce(nothing)) :- 1 = 1.
"""


def test_9_an_empty_covering_set_is_refused_before_any_call(tmp_path):
    p = tmp_path / "m9003.lp"
    p.write_text(_NO_COVERING)
    spec = probe_live.ClauseSpec(clause_id="m9003", module=str(p),
                                 act_phrase="produce it",
                                 clause_text="a clause")
    with pytest.raises(probe_live.LiveProbeError, match="covering set"):
        probe_live.build(spec)


def test_9_control_every_shipped_spec_has_a_non_empty_covering_set():
    cfg = translate.load_config(os.path.join(HERE, "config.json"))
    seen = 0
    for spec in probe_live.load_specs(SPECS, cfg):
        try:
            rep, _rows, _r, _p = probe_live.build(spec)
        except probe_live.UnglossedSignature:
            continue
        seen += 1
        assert rep.covering, spec.tag


# ==========================================================================
#  Q-22/Q-23 — "blocked" must be a REPORTED state, never a silent skip
# ==========================================================================
#
# ⛔ THE RISK THIS GUARDS. Q-22's fix put unsatisfied `requires` predicates
# into the situation signature, which is correct — without them the module's
# rules cannot fire and the probe reports green on inert content. But a
# borrowed predicate has no gloss (Q-6), so `render_situation` now refuses,
# and two shipped-spec tests began to fail.
#
# ⚠️ The tempting repair is to let those tests skip the spec. That is how a
# floor gets lowered: with every spec blocked, "every shipped spec builds"
# is vacuously true. So blocking is allowed ONLY where it is provably real —
# the predicate must actually be in `requires`, and actually unglossed
# everywhere in scope. A block for any other reason fails here.
#
# ⭐ NO COUNT IS PINNED (anti-rule: never pin an exact count of a live
# artifact). Q-23 landing will legitimately empty this set, and that must not
# fail the suite.

def test_q22_blocked_specs_are_blocked_for_a_REAL_reason():
    cfg = translate.load_config(os.path.join(HERE, "config.json"))
    for spec in probe_live.load_specs(SPECS, cfg):
        rows, _l, _m = link.discover_concept_table(
            [spec.module] + list(spec.links))
        rep = probe.probe_clause(spec.module, list(spec.links), rows or [])
        gaps = probe_live.blocking_gaps(rep, rows)
        if not gaps:
            continue
        declared = probe.header_of(
            open(spec.module, encoding="utf-8").read())["requires"]
        glossed = {str(r.get("concept") or "").strip() for r in (rows or [])
                   if str(r.get("gloss") or "").strip()}
        for g in gaps:
            assert g in declared, (
                f"{spec.clause_id} is blocked on {g!r}, which is NOT a "
                f"`requires` entry. Blocking is only legitimate for an "
                f"unglossed borrow; anything else is a bug being skipped")
            assert g not in glossed, (
                f"{spec.clause_id} is blocked on {g!r} but it IS glossed — "
                f"the gap detector is wrong and a buildable spec is being "
                f"dropped")


def test_q22_a_blocked_spec_carries_the_PREDICATE_in_its_error():
    """A count cannot be acted on; the name can."""
    cfg = translate.load_config(os.path.join(HERE, "config.json"))
    for spec in probe_live.load_specs(SPECS, cfg):
        try:
            probe_live.build(spec)
        except probe_live.UnglossedSignature as exc:
            assert "/" in str(exc), (
                "the refusal must name the predicate/arity that blocked it")
            assert spec.clause_id in str(exc)
