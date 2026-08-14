"""Pins for the 2026-08-14 promise items: item A (promise_repair.py, the
targeted broken-promise regeneration stage) and item B (leaf-time
promise-delivery enforcement in validate_leaf). Offline throughout --
MockClient, $0."""
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
import recurse_driver as R      # noqa: E402
import dispatch_core as DC      # noqa: E402
import promise_repair as PR     # noqa: E402

TOY = os.path.join(HERE, "toy_doc.md")

SEED = {"name": "promised_x", "prose": "the promised thing",
        "established_around": [3, 4]}


def _leaf_graph(lo, hi, provides=(), needs=(), jcs=None):
    g = {"nodes": [{"id": f"L{lo}-{hi}_n001", "establishes": "claim",
                    "needs": [dict(d) for d in needs],
                    "provides": [dict(p) for p in provides],
                    "spans": [{"lines": [lo, hi]}]}],
         "uncovered": []}
    if jcs is not None:
        g["judgment_calls"] = list(jcs)
    return g


# ================================== item B: validate_leaf enforcement
def test_missing_promised_provide_is_a_validation_error():
    """RED (THE ds7 DEFECT CLASS): a leaf whose inherited seed is
    established inside its span said nothing about it and validated
    clean -- 45 broken promises reached the root unchallenged."""
    g = _leaf_graph(1, 12)
    errs = R.validate_leaf(g, 1, 12, ["x"] * 12, seeds=[SEED],
                           enforce_promise_delivery=True)
    assert any("promised_x" in e and "judgment_calls" in e for e in errs), \
        errs


def test_judgment_calls_explanation_suppresses_the_error():
    """The escape hatch stays model-shaped (cover-or-explain, the ds3
    uncovered-content pattern): a judgment_calls entry naming the seed
    passes."""
    g = _leaf_graph(1, 12, jcs=["promised_x: the span paraphrases it; "
                                "the establishment is in the appendix"])
    errs = R.validate_leaf(g, 1, 12, ["x"] * 12, seeds=[SEED],
                           enforce_promise_delivery=True)
    assert not any("promised_x" in e for e in errs), errs


def test_delivered_promise_passes_and_outside_span_is_not_owed():
    g = _leaf_graph(1, 12, provides=[{"name": "promised_x", "prose": "p"}])
    assert not any("promised_x" in e for e in R.validate_leaf(
        g, 1, 12, ["x"] * 12, seeds=[SEED],
        enforce_promise_delivery=True))
    # established OUTSIDE [lo, hi]: this leaf owes nothing
    far = {"name": "promised_x", "prose": "p",
           "established_around": [40, 41]}
    assert not any("promised_x" in e for e in R.validate_leaf(
        _leaf_graph(1, 12), 1, 12, ["x"] * 12, seeds=[far],
        enforce_promise_delivery=True))


def test_flag_off_is_byte_identical():
    """Default False: the exact graphs the pinned builds validated stay
    valid -- even with the seeds handed through."""
    g = _leaf_graph(1, 12)
    base = R.validate_leaf(json.loads(json.dumps(g)), 1, 12, ["x"] * 12)
    with_seeds = R.validate_leaf(json.loads(json.dumps(g)), 1, 12,
                                 ["x"] * 12, seeds=[SEED])
    assert base == with_seeds == []


def _reply(lo, hi, n, provides=(), needs=(), jcs=None):
    g = _leaf_graph(lo, hi, provides, needs, jcs)
    g["uncovered"] = []
    g["nodes"][0]["spans"] = [{"lines": [lo, hi]}]
    return g


def test_enforcement_is_wired_through_both_leaf_paths(tmp_path):
    """Item B wiring: a reply that ignores an in-span seed must cost a
    repair round on the SERIAL path (Driver.leaf) and the CORE path
    (_want_leaf) alike -- the D1 one-path-only lesson."""
    lines = R.load_doc(TOY)
    n = len(lines)
    bad = _reply(1, n, n)
    good = _reply(1, n, n,
                  provides=[{"name": "promised_x", "prose": "p"}])
    cfg = {"leaf_max_lines": 100, "enforce_promise_delivery": True}
    seeds = [SEED]
    a = tmp_path / "serial"
    a.mkdir()
    drv = R.Driver(cfg, R.MockClient([bad, good]), lines, str(a))
    g = drv.leaf(1, n, seeds, str(a))
    assert drv.client.calls == 2, "the missing promise must cost a repair"
    assert any(R.nm(p) == "promised_x" for nd in g["nodes"]
               for p in nd.get("provides", []))
    b = tmp_path / "core"
    b.mkdir()
    drv2 = R.Driver(cfg, R.MockClient([bad, good]), lines, str(b))
    g2 = DC.run_build(drv2, 1, n, seeds, str(b), "serial")
    assert drv2.client.calls == 2
    assert any(R.nm(p) == "promised_x" for nd in g2["nodes"]
               for p in nd.get("provides", []))


# ==================================== item A: the promise-repair stage
def _repair_run(tmp_path, root_nodes=None):
    run = tmp_path / "run"
    run.mkdir()
    R.write_json(os.path.join(str(run), "division.json"),
                 {"decision": "divide", "seed_vocabulary": [dict(SEED)],
                  "children": [{"span": [1, 12]}, {"span": [13, 20]}]})
    g = {"nodes": root_nodes if root_nodes is not None else [
        {"id": "L1-12_n001", "establishes": "the establishing span",
         "needs": [], "provides": [], "spans": [{"lines": [1, 6]}]},
        {"id": "L13-20_n001", "establishes": "the needer",
         "needs": [{"name": "promised_x", "prose": "needs it"}],
         "provides": [], "spans": [{"lines": [13, 14]}]}]}
    R.write_json(os.path.join(str(run), "root_graph.json"), g)
    R.write_json(os.path.join(str(run), "fixup_queue.json"),
                 {"items": [{"kind": "broken_promise", "verdict": "reject",
                             "detail": {"unwind": str(run),
                                        "name": "promised_x"},
                             "reason": "needs regeneration"}]})
    return str(run)


_CFG = {"leaf_max_lines": 15, "price_per_mtok": [0.14, 0.28],
        "promise_repair": {"max_cost_usd": 0.25}}


def test_delivered_promise_is_spliced_into_a_repaired_copy(tmp_path):
    """The mechanical merge: the redraw's provides entry (and its new
    needs) land on the node covering the establishment lines, in
    root_graph.repaired.json -- NEVER in place -- with provenance in the
    artifact, a health line, and the danglings recount."""
    run = _repair_run(tmp_path)
    before = open(os.path.join(run, "root_graph.json"), "rb").read()
    reply = _reply(1, 12, 12,
                   provides=[{"name": "promised_x",
                              "prose": "the promised thing"}],
                   needs=[{"name": "extra_need", "prose": "new dep"}])
    lines = R.load_doc(TOY)
    rep = PR.run_repair(run, _CFG, R.MockClient([reply]), lines)
    assert rep["repaired"] == 1 and rep["failed"] == 0
    assert rep["needers_resolved"] == 1, \
        "the promised_x needer must resolve after the splice"
    fixed = json.load(open(os.path.join(run, "root_graph.repaired.json")))
    tgt = fixed["nodes"][0]
    assert any(R.nm(p) == "promised_x" for p in tgt["provides"])
    assert any(R.nm(d) == "extra_need" for d in tgt["needs"]), \
        "validator-accepted new needs splice too"
    assert fixed["promise_repairs"][0]["name"] == "promised_x"
    assert fixed["promise_repairs"][0]["target"] == "L1-12_n001"
    # never in place
    assert open(os.path.join(run, "root_graph.json"), "rb").read() \
        == before
    # the redraw's scratch artifact exists, and health carries the line
    assert os.path.exists(os.path.join(run, "promise_repair",
                                       "promised_x", "graph.json"))
    health = [json.loads(l) for l in open(os.path.join(run,
                                                       "health.jsonl"))]
    assert health[-1]["artifact"] == "promise_repair"
    assert health[-1]["repaired"] == 1


def test_declined_promise_is_recorded_honestly_undeliverable(tmp_path):
    """The redraw declines with a judgment_calls reason: no splice, the
    graph copy is content-identical, and the report says so."""
    run = _repair_run(tmp_path)
    reply = _reply(1, 12, 12,
                   jcs=["promised_x: the span paraphrases it; the real "
                        "establishment is elsewhere"])
    rep = PR.run_repair(run, _CFG, R.MockClient([reply]),
                        R.load_doc(TOY))
    assert rep["repaired"] == 0 and rep["declined_honestly"] == 1
    assert rep["needers_resolved"] == 0
    item = rep["items"][0]
    assert item["status"] == "declined"
    assert "paraphrases" in item["why"]
    fixed = json.load(open(os.path.join(run, "root_graph.repaired.json")))
    orig = json.load(open(os.path.join(run, "root_graph.json")))
    assert fixed["nodes"] == orig["nodes"], "a decline must splice nothing"
    disk = json.load(open(os.path.join(run,
                                       "promise_repair_report.json")))
    assert disk["declined_honestly"] == 1


def test_budget_gate_refuses_before_any_call(tmp_path):
    run = _repair_run(tmp_path)
    cfg = dict(_CFG, promise_repair={"max_cost_usd": 0.0})
    client = R.MockClient([])
    with pytest.raises(T.CostGateError, match="promise_repair"):
        PR.run_repair(run, cfg, client, R.load_doc(TOY))
    assert client.calls == 0, "the gate must fire before any spend"
    assert not os.path.exists(os.path.join(run,
                                           "root_graph.repaired.json"))


def test_redraw_prompt_carries_the_promise_instruction(tmp_path):
    """The appended instruction names the seed, its prose and its
    establishment lines -- the redraw is TOLD what it owes."""
    run = _repair_run(tmp_path)
    reply = _reply(1, 12, 12,
                   provides=[{"name": "promised_x", "prose": "p"}])
    seen = []

    class Spy(R.MockClient):
        def complete(self, system, user):
            seen.append(user)
            return R.MockClient.complete(self, system, user)
        complete_messages = complete

    PR.run_repair(run, _CFG, Spy([reply]), R.load_doc(TOY))
    assert "PROMISE REPAIR" in seen[0]
    assert "'promised_x'" in seen[0] and "the promised thing" in seen[0]
    assert "lines 3-4" in seen[0]


def test_unlocatable_promise_is_a_failed_item_not_a_crash(tmp_path):
    run = _repair_run(tmp_path)
    q = json.load(open(os.path.join(run, "fixup_queue.json")))
    q["items"][0]["detail"]["name"] = "never_seeded"
    R.write_json(os.path.join(run, "fixup_queue.json"), q)
    rep = PR.run_repair(run, _CFG, R.MockClient([]), R.load_doc(TOY))
    assert rep["failed"] == 1 and rep["repaired"] == 0
    assert "established_around" in rep["items"][0]["why"]


def test_cli_refuses_without_yes(capsys):
    assert PR.main(["runs/nowhere"]) == 2
    assert "--yes" in capsys.readouterr().out
