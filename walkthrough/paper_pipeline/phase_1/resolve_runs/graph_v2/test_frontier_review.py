"""Pins for frontier_review.py (EXPERIMENTS.md 2026-08-14: "frontier
review moves INTO the pipeline"). Offline throughout: stub transport,
mocked judges, $0 -- exactly the recorded design's testability seam."""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (PHASE1, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import translate as T           # noqa: E402
import rename_seat as RS        # noqa: E402
import frontier_review as FR    # noqa: E402


ITEMS = [
    {"kind": "seat_accepted_rename", "risk": 1.2,
     "detail": {"needer": "L1-4_n01", "name": "house_rules",
                "rename_to": "root_authority"},
     "grounds": "seat said same_concept"},
    {"kind": "broken_promise", "risk": 0.9,
     "detail": {"unwind": "root", "name": "chain_of_command"}},
    {"kind": "low_sim_edge", "risk": 0.8,
     "detail": {"needer": "L1-4_n02", "name": "x", "prose": "p"}},
]


def _run_dir(tmp_path, items=ITEMS):
    run = tmp_path / "run"
    run.mkdir()
    (run / "risk_queue.json").write_text(json.dumps(
        {"run": str(run), "items": items, "total": len(items)}))
    return str(run)


def _fcfg(**kw):
    base = dict(FR.DEFAULTS, parity_n=2, slice=3, max_cost_usd=1.0,
                price_per_mtok=[3.0, 15.0])
    base.update(kw)
    return base


def _agreeing(system, user):
    """Both judges say 'the decision stands', in the brief's own vocab."""
    v = "same_concept" if system == RS.BRIEF else "uphold"
    return {"text": json.dumps({"verdict": v, "grounds": "g"})}


def _disagreeing(system, user):
    v = "different_concept" if system == RS.BRIEF else "reject"
    return {"text": json.dumps({"verdict": v, "grounds": "g"})}


class StubTransport:
    """The CurlTransport surface, offline."""

    def __init__(self, rows):
        self.rows, self.calls = rows, []

    def upload(self, path, name):
        self.calls.append("upload")
        self.jsonl = open(path).read()
        return "file-1"

    def create(self, fid):
        self.calls.append("create")
        return {"id": "batch-1"}

    def status(self, bid):
        self.calls.append("status")
        return {"id": bid, "status": "COMPLETED", "output_file_id": "of-1"}

    def list_batches(self):
        self.calls.append("list")
        return getattr(self, "listing", [])

    def content(self, fid):
        return "\n".join(json.dumps(r) for r in self.rows)


def _row(i, verdict):
    return {"custom_id": f"fr-{i}", "response": {"body": {
        "choices": [{"message": {"content": json.dumps(
            {"verdict": verdict, "grounds": "frontier grounds"})},
            "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5}}}}


# ------------------------------------------------------------- brief reuse
def test_rename_kinds_reuse_the_adopted_seat_brief():
    """The recorded design: rename-kind items are judged under
    rename_seat.BRIEF (the swept, adopted brief) -- never a fork."""
    assert FR.brief_for("seat_accepted_rename") is RS.BRIEF
    assert FR.brief_for("dangling_near_miss") is RS.BRIEF
    for kind in ("low_sim_edge", "dropped_merge", "modal_drift",
                 "broken_promise"):
        brief = FR.brief_for(kind)
        assert brief is not RS.BRIEF
        assert '"uphold"' in brief and '"reject"' in brief


# ------------------------------------------------------------------ parity
def test_parity_below_band_proceeds_and_is_reported():
    rep = FR.parity_stage(ITEMS, _agreeing, _agreeing, _fcfg())
    assert rep["divergence"] == 0.0 and rep["decided_pairs"] == 2
    assert len(rep["rows"]) == 2


def test_parity_above_band_stops_loudly_with_the_report_attached():
    """Seat-defect doctrine: total frontier/flash disagreement must STOP
    the stage, never quietly review 150 items with a broken judge pair.
    Review item 9: the exception carries the promised .report rows."""
    with pytest.raises(FR.ParityStopError, match="PARITY STOP") as ei:
        FR.parity_stage(ITEMS, _agreeing, _disagreeing, _fcfg())
    assert ei.value.report["divergence"] == 1.0
    assert len(ei.value.report["rows"]) == 2


# ----------------------------------------------------------------- judging
def test_judge_item_propagates_terminal_transport(monkeypatch):
    import time
    monkeypatch.setattr(time, "sleep", lambda s: None)

    def dead(system, user):
        raise T.ProviderError("HTTP 402: credit exhausted")
    with pytest.raises(T.ProviderError):
        FR.judge_item(dead, ITEMS[0])

    def gated(system, user):
        raise T.CostGateError("ceiling")
    with pytest.raises(T.CostGateError):
        FR.judge_item(gated, ITEMS[0])


def test_judge_item_no_verdict_on_unparseable_reply():
    v = FR.judge_item(lambda s, u: {"text": "not json"}, ITEMS[0])
    assert v["verdict"] == "no_verdict"


def test_parity_with_zero_decided_pairs_stops_not_proceeds():
    """Re-review N1 (THE DEFECT: '0% divergence over 0 decided pairs --
    proceeding'): a judge pair that cannot produce verdicts is as
    defective as one that diverges. Zero decided must STOP, with the
    no_verdict evidence in .report."""
    broken = lambda s, u: {"text": "not json at all"}   # noqa: E731
    with pytest.raises(FR.ParityStopError, match="decided pair") as ei:
        FR.parity_stage(ITEMS, broken, broken, _fcfg())
    assert ei.value.report["decided_pairs"] == 0
    assert all(r["frontier"]["verdict"] == "no_verdict"
               for r in ei.value.report["rows"])


def test_parse_verdict_tolerates_a_markdown_fence():
    """Re-review N1: a fenced frontier reply must still DECIDE (the
    driver's own fence-tolerant parse), not swell the no_verdict pile
    that used to fail parity open."""
    fenced = ('```json\n{"verdict": "same_concept", '
              '"grounds": "same referent"}\n```')
    v = FR.parse_verdict(fenced, "same_concept", "different_concept")
    assert v == {"verdict": "uphold", "grounds": "same referent"}
    v2 = FR.parse_verdict("noise before {\"verdict\": \"reject\", "
                          "\"grounds\": \"g\"} after", "uphold", "reject")
    assert v2["verdict"] == "reject"


# ------------------------------------------------------------- batch stage
def test_run_review_end_to_end_offline(tmp_path):
    """The whole stage for $0: parity passes, the slice ships as one batch
    through the stub transport, verdicts + health line land on the run,
    and the in-flight record is cleared once results are routed."""
    run = _run_dir(tmp_path)
    rows = [_row(0, "same_concept"),      # rename kind: uphold
            _row(1, "reject")]            # broken_promise: reject
    #                                       fr-2 OMITTED -> no_verdict
    tr = StubTransport(rows)
    out = FR.run_review(run, _fcfg(), _agreeing, _agreeing,
                        transport=tr, poll_s=0)
    assert out["counts"] == {"uphold": 1, "reject": 1, "no_verdict": 1}
    assert out["parity"]["divergence"] == 0.0
    # the verdict rows carry the item identity fixup.py consumes
    v0 = out["verdicts"][0]
    assert v0["kind"] == "seat_accepted_rename"
    assert v0["detail"]["rename_to"] == "root_authority"
    disk = json.load(open(os.path.join(run, "frontier_verdicts.json")))
    assert disk["counts"] == out["counts"]
    health = [json.loads(l) for l in open(os.path.join(run,
                                                       "health.jsonl"))]
    assert health[-1]["artifact"] == "frontier_review"
    assert health[-1]["reject"] == 1
    assert not os.path.exists(os.path.join(run, "frontier_inflight.json"))
    # per-request bodies carried per-kind briefs (F4 doctrine)
    sent = [json.loads(l) for l in tr.jsonl.splitlines()]
    assert sent[0]["body"]["messages"][0]["content"] == RS.BRIEF
    assert sent[1]["body"]["messages"][0]["content"] != RS.BRIEF


def test_submit_gate_refuses_over_ceiling(tmp_path):
    """Worst-case cost gate AT SUBMIT (the recorded design): nothing may
    reach the provider when the arithmetic exceeds max_cost_usd."""
    run = _run_dir(tmp_path)
    tr = StubTransport([])
    with pytest.raises(T.CostGateError, match="worst case"):
        FR.batch_stage(run, ITEMS, tr, _fcfg(max_cost_usd=0.0), poll_s=0)
    assert tr.calls == [], "a gated submit still hit the provider"


def test_inflight_record_resumes_the_same_job(tmp_path):
    """Lossless recovery: a record with a batch_id means money is already
    committed -- the sweep polls THAT job and never uploads or creates a
    second one (the manifest doctrine, F2). Review item 3b: batch_stage
    itself must NOT clear the record -- only run_review does, after the
    verdicts are on disk."""
    run = _run_dir(tmp_path)
    with open(os.path.join(run, "frontier_inflight.json"), "w") as f:
        json.dump({"batch_id": "batch-1", "n": 3}, f)
    tr = StubTransport([_row(0, "same_concept"), _row(1, "uphold"),
                        _row(2, "uphold")])
    verdicts, gate = FR.batch_stage(run, ITEMS, tr, _fcfg(), poll_s=0)
    assert "upload" not in tr.calls and "create" not in tr.calls
    assert gate is None
    assert [v["verdict"] for v in verdicts] == ["uphold"] * 3
    assert os.path.exists(os.path.join(run, "frontier_inflight.json")), \
        "the committed-money record must outlive batch_stage (item 3b)"


def test_create_kill_window_adopts_the_live_job(tmp_path):
    """Review item 3a: a record with an input_file_id but no batch_id is
    indeterminate -- the provider listing is asked, the live job adopted,
    and nothing is uploaded or created a second time."""
    run = _run_dir(tmp_path)
    with open(os.path.join(run, "frontier_inflight.json"), "w") as f:
        json.dump({"input_file_id": "file-1", "n": 3}, f)
    tr = StubTransport([_row(0, "same_concept"), _row(1, "uphold"),
                        _row(2, "uphold")])
    tr.listing = [{"id": "batch-9", "input_file_id": "file-1"}]
    verdicts, _gate = FR.batch_stage(run, ITEMS, tr, _fcfg(), poll_s=0)
    assert "upload" not in tr.calls and "create" not in tr.calls
    assert "list" in tr.calls
    rec = json.load(open(os.path.join(run, "frontier_inflight.json")))
    assert rec["batch_id"] == "batch-9"
    assert len(verdicts) == 3


def test_create_kill_window_unlistable_refuses_to_resubmit(tmp_path):
    """The listing cannot answer: keep the record, refuse to double-pay."""
    run = _run_dir(tmp_path)
    with open(os.path.join(run, "frontier_inflight.json"), "w") as f:
        json.dump({"input_file_id": "file-1", "n": 3}, f)

    class Unlistable(StubTransport):
        def list_batches(self):
            raise T.ProviderError("WAF 403 intermittent")
    tr = Unlistable([])
    with pytest.raises(T.ProviderError, match="never resubmit blind"):
        FR.batch_stage(run, ITEMS, tr, _fcfg(), poll_s=0)
    assert "upload" not in tr.calls and "create" not in tr.calls
    assert os.path.exists(os.path.join(run, "frontier_inflight.json"))


def test_statusless_polls_become_a_transport_error(tmp_path):
    run = _run_dir(tmp_path)

    class NoStatus(StubTransport):
        def status(self, bid):
            self.calls.append("status")
            return {"error": {"message": "x"}}
    with open(os.path.join(run, "frontier_inflight.json"), "w") as f:
        json.dump({"batch_id": "batch-1", "n": 3}, f)
    with pytest.raises(T.ProviderError, match="no status field"):
        FR.batch_stage(run, ITEMS, NoStatus([]), _fcfg(), poll_s=0)


# --------------------------------------- review items 1, 2, 3c, 5 (fix set)
def _never(system, user):
    raise AssertionError("no judge call may happen here")


def test_refuses_to_run_without_a_configured_price(tmp_path):
    """Review item 1a: the worst-case gate is only as honest as its price;
    an unset price is a refusal BEFORE any spend, never a guessed gate."""
    run = _run_dir(tmp_path)
    with pytest.raises(T.ConfigError, match="price_per_mtok"):
        FR.run_review(run, _fcfg(price_per_mtok=None), _never, _never,
                      transport=StubTransport([]), poll_s=0)


def test_whole_stage_gated_before_parity_spends(tmp_path):
    """Review item 1c (THE DEFECT: parity money spent, then the submit
    gate refused the slice): the parity+slice worst case is gated up
    front -- with a ceiling of $0 no judge is ever called and nothing
    reaches the transport."""
    run = _run_dir(tmp_path)
    tr = StubTransport([])
    with pytest.raises(T.CostGateError, match="BEFORE any spend"):
        FR.run_review(run, _fcfg(max_cost_usd=0.0), _never, _never,
                      transport=tr, poll_s=0)
    assert tr.calls == []


def test_passed_parity_persists_and_resume_skips_it(tmp_path):
    """Review item 3c: a passed parity report rides the inflight record;
    a resumed run must not re-pay the parity sample."""
    run = _run_dir(tmp_path)
    with open(os.path.join(run, "frontier_inflight.json"), "w") as f:
        json.dump({"parity": {"n": 2, "decided_pairs": 2,
                              "divergence": 0.0, "band": 0.4, "rows": []},
                   "batch_id": "batch-1", "n": 3}, f)
    tr = StubTransport([_row(0, "same_concept"), _row(1, "uphold"),
                        _row(2, "uphold")])
    out = FR.run_review(run, _fcfg(), _never, _never,
                        transport=tr, poll_s=0)
    assert out["parity"]["divergence"] == 0.0
    assert out["counts"] == {"uphold": 3}


def test_fresh_run_persists_parity_before_submit(tmp_path, monkeypatch):
    """The persistence half of 3c: the record carries the parity report
    from the moment it passes (a kill during the batch keeps it)."""
    run = _run_dir(tmp_path)
    seen = {}
    orig = FR.batch_stage

    def spy(*a, **kw):
        rec = json.load(open(os.path.join(run, "frontier_inflight.json")))
        seen["parity"] = rec.get("parity")
        return orig(*a, **kw)
    monkeypatch.setattr(FR, "batch_stage", spy)
    tr = StubTransport([_row(0, "same_concept")])
    FR.run_review(run, _fcfg(), _agreeing, _agreeing, transport=tr,
                  poll_s=0)
    assert seen["parity"] and seen["parity"]["divergence"] == 0.0


def test_near_miss_vocab_is_inverted():
    """Review item 2: for dangling_near_miss the RECORDED decision is the
    non-rename -- `different_concept` upholds it; `same_concept` (the
    rename should have happened) rejects it onto the fix queue."""
    assert FR.vocab_for("dangling_near_miss") == ("different_concept",
                                                  "same_concept")
    assert FR.vocab_for("seat_accepted_rename") == ("same_concept",
                                                    "different_concept")


def test_near_miss_batch_verdicts_route_by_the_inverted_vocab(tmp_path):
    items = [{"kind": "dangling_near_miss", "risk": 0.9,
              "detail": {"needer": "n1", "name": "x"}},
             {"kind": "dangling_near_miss", "risk": 0.8,
              "detail": {"needer": "n2", "name": "y"}}]
    run = _run_dir(tmp_path, items=items)
    with open(os.path.join(run, "frontier_inflight.json"), "w") as f:
        json.dump({"batch_id": "batch-1", "n": 2}, f)
    tr = StubTransport([_row(0, "same_concept"),      # rename SHOULD happen
                        _row(1, "different_concept")])  # honest dangling
    verdicts, _g = FR.batch_stage(run, items, tr, _fcfg(), poll_s=0)
    assert [v["verdict"] for v in verdicts] == ["reject", "uphold"]


class LedgerClient:
    """The _log_usage duck surface item 5 feeds."""

    def __init__(self, raise_after=None):
        self.envs, self.raise_after = [], raise_after

    def _log_usage(self, env):
        self.envs.append(env)
        if (self.raise_after is not None
                and len(self.envs) > self.raise_after):
            raise T.CostGateError("measured spend exceeds the run ceiling")


def test_batch_rows_reach_the_ledger_with_measured_cost(tmp_path):
    """Review item 5: frontier batch spend must be visible -- every
    returned row is ledgered through client._log_usage with a cost_usd
    computed from the configured price."""
    run = _run_dir(tmp_path)
    with open(os.path.join(run, "frontier_inflight.json"), "w") as f:
        json.dump({"batch_id": "batch-1", "n": 3}, f)
    tr = StubTransport([_row(0, "same_concept"), _row(1, "uphold")])
    client = LedgerClient()
    verdicts, gate = FR.batch_stage(run, ITEMS, tr, _fcfg(), poll_s=0,
                                    client=client)
    assert gate is None and len(verdicts) == 3
    assert len(client.envs) == 2, "one ledger row per RETURNED batch row"
    cost = (client.envs[0].get("usage") or {}).get("cost_usd")
    assert cost == pytest.approx(10 / 1e6 * 3.0 + 5 / 1e6 * 15.0)
    # re-review N2: the ledgered flag reached the record BEFORE the loop
    rec = json.load(open(os.path.join(run, "frontier_inflight.json")))
    assert rec["ledgered"] is True


def test_resume_after_ledgering_never_ledgers_twice(tmp_path):
    """Re-review N2 (THE DEFECT: a kill between batch_stage's ledger loop
    and run_review's verdict write re-ledgered the WHOLE batch on
    resume): with `ledgered` persisted in the record, the resume
    re-parses the verdicts for free and makes ZERO _log_usage calls."""
    run = _run_dir(tmp_path)
    with open(os.path.join(run, "frontier_inflight.json"), "w") as f:
        json.dump({"batch_id": "batch-1", "n": 3, "ledgered": True}, f)
    tr = StubTransport([_row(0, "same_concept"), _row(1, "uphold"),
                        _row(2, "uphold")])
    client = LedgerClient()
    verdicts, gate = FR.batch_stage(run, ITEMS, tr, _fcfg(), poll_s=0,
                                    client=client)
    assert client.envs == [], "resume double-ledgered an already-" \
                              "ledgered batch"
    assert gate is None
    assert [v["verdict"] for v in verdicts] == ["uphold"] * 3, \
        "verdicts must still re-parse on the ledger-skipping resume"


def test_ledger_cost_gate_is_deferred_until_verdicts_persist(tmp_path):
    """Item 5 x item 4's pattern: a CostGateError from the ledger must not
    lose the paid verdicts -- frontier_verdicts.json is written first,
    then the gate re-raises out of run_review."""
    run = _run_dir(tmp_path)
    with open(os.path.join(run, "frontier_inflight.json"), "w") as f:
        json.dump({"parity": {"n": 2, "decided_pairs": 2,
                              "divergence": 0.0, "band": 0.4, "rows": []},
                   "batch_id": "batch-1", "n": 3}, f)
    tr = StubTransport([_row(0, "same_concept"), _row(1, "uphold"),
                        _row(2, "uphold")])
    client = LedgerClient(raise_after=0)      # every ledger call raises
    with pytest.raises(T.CostGateError):
        FR.run_review(run, _fcfg(), _never, _never, transport=tr,
                      poll_s=0, client=client)
    disk = json.load(open(os.path.join(run, "frontier_verdicts.json")))
    assert disk["counts"] == {"uphold": 3}, \
        "the paid verdicts must persist before the gate raises"
    assert len(client.envs) == 3, "every paid row still reached the ledger"


def test_batch_false_runs_the_slice_live(tmp_path):
    run = _run_dir(tmp_path)
    out = FR.run_review(run, _fcfg(batch=False), _agreeing, _agreeing,
                        transport=None, poll_s=0)
    assert out["counts"] == {"uphold": 3}


# ------------------------- item C: evidence-bearing prompts (k3 report)
_DOC = [f"DOCLINE-{i} content of the document" for i in range(1, 21)]

_GRAPH = {"nodes": [
    {"id": "L1-12_n001", "establishes": "establishes the root authority",
     "needs": [], "provides": [{"name": "root_authority",
                                "prose": "the top level of authority"}],
     "spans": [{"lines": [3, 4]}]},
    {"id": "L13-20_n001", "establishes": "relies on the household rules",
     "needs": [{"name": "house_rules",
                "prose": "the household regulations"}],
     "provides": [], "spans": [{"lines": [13, 14]}]}]}


def _ev(run_dir="/nowhere"):
    return FR.Evidence(json.loads(json.dumps(_GRAPH)), _DOC, run_dir)


def test_rename_kind_prompts_carry_the_span_text_the_brief_promises():
    """THE DEFECT (k3_validity_report): rename_seat.BRIEF tells the judge
    to weigh 'the passages' quoted text' and item_prompt never sent any.
    Both rename kinds must now ship the seat's own evidence prompt --
    claims, prose, and the document lines."""
    ev = _ev()
    rename = {"kind": "seat_accepted_rename",
              "detail": {"needer": "L13-20_n001", "name": "house_rules",
                         "rename_to": "root_authority"}}
    p = FR.item_prompt(rename, ev)
    assert "DOCLINE-13" in p and "DOCLINE-3" in p, "span text missing"
    assert "relies on the household rules" in p
    assert "establishes the root authority" in p
    assert "the household regulations" in p
    assert "the top level of authority" in p
    near = {"kind": "dangling_near_miss",
            "detail": {"needer": "L13-20_n001", "name": "house_rules",
                       "candidates": [{"name": "root_authority",
                                       "sim": 0.9}]}}
    p2 = FR.item_prompt(near, ev)
    assert "DOCLINE-13" in p2 and "DOCLINE-3" in p2
    assert "the household regulations" in p2


def test_dropped_merge_prompt_carries_both_nodes(tmp_path):
    """THE DEFECT: 16/16 ds7 dropped_merge verdicts were judged on a
    node-id pair alone -- rubber-stamp-by-construction."""
    item = {"kind": "dropped_merge",
            "detail": "L1-12_n001->L13-20_n001"}
    p = FR.item_prompt(item, _ev())
    assert "establishes the root authority" in p
    assert "relies on the household rules" in p
    assert "DOCLINE-3" in p and "DOCLINE-13" in p


def test_broken_promise_prompt_carries_seed_and_covering_nodes(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    with open(os.path.join(str(run), "division.json"), "w") as f:
        json.dump({"decision": "divide", "seed_vocabulary": [
            {"name": "promised_x", "prose": "the promised thing",
             "established_around": [3, 4]}],
            "children": [{"span": [1, 12]}, {"span": [13, 20]}]}, f)
    item = {"kind": "broken_promise",
            "detail": {"unwind": str(run), "name": "promised_x"}}
    p = FR.item_prompt(item, _ev(run_dir=str(run)))
    assert "the promised thing" in p, "the seed's prose is the promise"
    assert "establishes the root authority" in p, \
        "the nodes covering the establishment lines are the context"
    assert "DOCLINE-3" in p


def test_low_sim_edge_prompt_carries_both_sides():
    item = {"kind": "low_sim_edge",
            "detail": {"needer": "L13-20_n001", "name": "root_authority",
                       "prose": "needs the top level"}}
    p = FR.item_prompt(item, _ev())
    assert "relies on the household rules" in p
    assert "establishes the root authority" in p
    assert "the top level of authority" in p
    assert "DOCLINE-13" in p and "DOCLINE-3" in p


def test_unconstructable_evidence_raises_instead_of_defaulting():
    """The pin the coordinator named: a no-evidence prompt construction is
    a FAILURE, never another silent uncertainty-default."""
    ev = _ev()
    with pytest.raises(T.Phase1Error, match="no evidence"):
        FR.item_prompt({"kind": "seat_accepted_rename",
                        "detail": {"needer": "GHOST", "name": "x",
                                   "rename_to": "root_authority"}}, ev)
    with pytest.raises(T.Phase1Error, match="no evidence"):
        FR.item_prompt({"kind": "dropped_merge",
                        "detail": "GHOST->ALSO_GHOST"}, ev)


def test_judge_item_skips_unconstructable_evidence_without_transport(
        ):
    """Re-review item 4: unconstructable evidence is a skip-with-record
    -- a no_verdict row naming the reason, never a transport retry, never
    a stage abort. The judge callable is never invoked."""
    def never(system, user):
        raise AssertionError("no judge call may happen")
    v = FR.judge_item(never, {"kind": "seat_accepted_rename",
                              "detail": {"needer": "GHOST", "name": "x",
                                         "rename_to": "root_authority"}},
                      _ev())
    assert v["verdict"] == "no_verdict"
    assert v["grounds"].startswith("evidence unconstructable")
    assert "transport" not in v["grounds"]


def test_batch_slice_excludes_unconstructable_items_at_prep(tmp_path):
    """Item 4's batch half: the ghost item leaves the slice at prep as a
    no_verdict report row; the judgeable item still ships and the stage
    completes."""
    good = {"kind": "seat_accepted_rename", "risk": 1.2,
            "detail": {"needer": "L13-20_n001", "name": "house_rules",
                       "rename_to": "root_authority"}}
    ghost = {"kind": "seat_accepted_rename", "risk": 1.0,
             "detail": {"needer": "GHOST", "name": "x",
                        "rename_to": "root_authority"}}
    run = _run_dir(tmp_path, items=[good, ghost])
    with open(os.path.join(run, "root_graph.json"), "w") as f:
        json.dump(_GRAPH, f)
    tr = StubTransport([_row(0, "same_concept")])
    out = FR.run_review(run, _fcfg(parity_n=1), _agreeing, _agreeing,
                        transport=tr, poll_s=0, lines=_DOC)
    assert out["excluded_no_evidence"] == 1
    assert out["counts"] == {"uphold": 1, "no_verdict": 1}
    ghost_row = next(v for v in out["verdicts"]
                     if v["verdict"] == "no_verdict")
    assert ghost_row["grounds"].startswith("evidence unconstructable")
    # the batch carried ONLY the judgeable item
    sent = [json.loads(l) for l in tr.jsonl.splitlines()]
    assert len(sent) == 1


def test_grounds_cap_is_1200_chars():
    long = json.dumps({"verdict": "uphold", "grounds": "g" * 2000})
    v = FR.parse_verdict(long, "uphold", "reject")
    assert len(v["grounds"]) == 1200


# --------------------------------------------------------------------- CLI
def test_cli_refuses_without_yes(capsys):
    """The one stage that is deliberately NOT push-button: it spends real
    money, so --yes is required (repo rule: consequential spends prompt)."""
    assert FR.main(["runs/nowhere"]) == 2
    assert "--yes" in capsys.readouterr().out
