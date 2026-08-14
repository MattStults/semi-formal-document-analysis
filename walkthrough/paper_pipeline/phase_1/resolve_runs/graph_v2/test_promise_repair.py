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


def test_boundary_straddling_seed_is_owed_by_no_leaf():
    """Re-review 3-note (ruling recorded in the validate_leaf comment): a
    seed whose established_around CROSSES the leaf boundary is owed by no
    leaf -- accepted gap; the division-promise check catches it
    post-unwind."""
    straddler = {"name": "promised_x", "prose": "p",
                 "established_around": [10, 13]}     # hi is 12
    errs = R.validate_leaf(_leaf_graph(1, 12), 1, 12, ["x"] * 12,
                           seeds=[straddler],
                           enforce_promise_delivery=True)
    assert not any("promised_x" in e for e in errs)


def test_decline_matching_is_word_boundary_not_substring():
    """Re-review 2-note: a judgment_calls entry naming
    support_mental_health_rule must NOT suppress the promise check for
    support_mental_health."""
    assert R.name_mentioned("support_mental_health",
                            "L3: support_mental_health: covered elsewhere")
    assert not R.name_mentioned(
        "support_mental_health",
        "L3: support_mental_health_rule: covered elsewhere")
    assert not R.name_mentioned("support_mental_health", "")
    seed = {"name": "support_mental_health", "prose": "p",
            "established_around": [3, 4]}
    near_miss_jc = _leaf_graph(1, 12, jcs=[
        "support_mental_health_rule: declined for its own reasons"])
    errs = R.validate_leaf(near_miss_jc, 1, 12, ["x"] * 12, seeds=[seed],
                           enforce_promise_delivery=True)
    assert any("support_mental_health" in e for e in errs), \
        "a LONGER name's decline suppressed the shorter seed's check"


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
    """The promise item fails to locate; the under-export scan (which
    still finds promised_x via its division seed) proceeds independently
    -- per-class accounting keeps the two stories separate."""
    run = _repair_run(tmp_path)
    q = json.load(open(os.path.join(run, "fixup_queue.json")))
    q["items"][0]["detail"]["name"] = "never_seeded"
    R.write_json(os.path.join(run, "fixup_queue.json"), q)
    reply = _reply(1, 12, 12,
                   provides=[{"name": "promised_x", "prose": "p"}])
    rep = PR.run_repair(run, _CFG, R.MockClient([reply]), R.load_doc(TOY))
    assert rep["by_class"]["promise"]["failed"] == 1
    assert "established_around" in rep["items"][0]["why"]
    assert rep["by_class"]["underexport"]["repaired"] == 1


# ------------------- item A extension: the under-export scan (class b)
def test_underexport_scan_repairs_a_dangling_with_existing_content(
        tmp_path):
    """THE DEFECT (delta_investigation cause 3): the establishing content
    exists as a node with EMPTY provides (ds7: 92 exported names vs the
    golden's 230; the self-harm rule class). The deterministic scan
    (establishes-prose overlap >= 0.25) must find that node, aim the
    same must-provide-or-explain redraw at its leaf, and splice onto
    exactly that node -- reported under its own class."""
    run = _repair_run(tmp_path, root_nodes=[
        {"id": "L1-12_n001",
         "establishes": "The assistant must not encourage or enable "
                        "self harm.",
         "needs": [], "provides": [], "spans": [{"lines": [1, 6]}]},
        {"id": "L13-20_n001", "establishes": "the needer",
         "needs": [{"name": "self_harm_rule",
                    "prose": "must not encourage self harm behaviour"}],
         "provides": [], "spans": [{"lines": [13, 14]}]}])
    # no broken_promise items at all: class (b) stands alone
    R.write_json(os.path.join(run, "fixup_queue.json"), {"items": []})
    reply = _reply(1, 12, 12,
                   provides=[{"name": "self_harm_rule",
                              "prose": "no encouraging self harm"}])
    rep = PR.run_repair(run, _CFG, R.MockClient([reply]), R.load_doc(TOY))
    bc = rep["by_class"]
    assert bc["underexport"]["repaired"] == 1
    assert bc["underexport"]["needers_resolved"] == 1
    assert bc["promise"]["planned"] == 0
    assert bc["promise"]["needers_resolved"] == 0
    item = next(r for r in rep["items"] if r["class"] == "underexport")
    assert item["status"] == "repaired" and item["target"] == "L1-12_n001"
    fixed = json.load(open(os.path.join(run, "root_graph.repaired.json")))
    tgt = next(n for n in fixed["nodes"] if n["id"] == "L1-12_n001")
    assert any(R.nm(p) == "self_harm_rule" for p in tgt["provides"])


def test_underexport_scan_is_deterministic_and_bounded():
    """One candidate per dangling name, best overlap wins, provided names
    and no-candidate danglings excluded."""
    g = {"nodes": [
        {"id": "a", "establishes": "encourage self harm rule text",
         "needs": [], "provides": [], "spans": [{"lines": [1, 2]}]},
        {"id": "b", "establishes": "totally unrelated content here",
         "needs": [], "provides": [], "spans": [{"lines": [3, 4]}]},
        {"id": "c", "establishes": "the needer",
         "needs": [{"name": "self_harm_rule",
                    "prose": "encourage self harm rule"},
                   {"name": "opaque_thing", "prose": "zebra quagga"},
                   {"name": "provided_thing", "prose": "irrelevant"}],
         "provides": [], "spans": [{"lines": [5, 6]}]},
        {"id": "d", "establishes": "provider",
         "needs": [], "provides": [{"name": "provided_thing",
                                    "prose": "x"}],
         "spans": [{"lines": [7, 8]}]}]}
    cands = PR.underexport_candidates("/nonexistent", g)
    assert [c["name"] for c in cands] == ["self_harm_rule"]
    assert cands[0]["target_id"] == "a"
    assert cands[0]["via"] == "establishes-overlap"


# ------------------------- re-review 1a-1d: prep filters and coherence
def test_already_provided_name_is_skipped_with_a_record(tmp_path):
    """Re-review 1a (ds7 real case: scope_of_autonomy was already
    provided; 3/26 queue names stale): a plan whose name is provided
    ANYWHERE in the root graph is skipped at prep, recorded, unpaid."""
    run = _repair_run(tmp_path, root_nodes=[
        {"id": "L1-12_n001", "establishes": "already exports it",
         "needs": [], "provides": [{"name": "promised_x", "prose": "p"}],
         "spans": [{"lines": [1, 6]}]}])
    client = R.MockClient([])
    rep = PR.run_repair(run, _CFG, client, R.load_doc(TOY))
    assert client.calls == 0, "a stale queue row must cost nothing"
    row = rep["items"][0]
    assert row["status"] == "skipped_already_provided"
    assert rep["by_class"]["promise"]["skipped_already_provided"] == 1
    assert rep["repaired"] == 0 and rep["failed"] == 0


def test_promise_items_dedupe_per_name(tmp_path):
    """Re-review 1d (chain_of_command_principle x6 in the ds7 queue):
    one plan per name, max."""
    run = _repair_run(tmp_path)
    q = json.load(open(os.path.join(run, "fixup_queue.json")))
    q["items"] = q["items"] * 3
    R.write_json(os.path.join(run, "fixup_queue.json"), q)
    reply = _reply(1, 12, 12,
                   provides=[{"name": "promised_x", "prose": "p"}])
    client = R.MockClient([reply])
    rep = PR.run_repair(run, _CFG, client, R.load_doc(TOY))
    assert client.calls == 1, "duplicate queue rows must not redraw twice"
    assert rep["repaired"] == 1
    assert sum(1 for r in rep["items"]
               if r.get("class") == "promise") == 1


def test_overlap_picked_target_derives_ea_from_the_target_span(tmp_path):
    """Re-review 1b (4/23 ds7 candidates incoherent): when the scan picks
    a target by establishes OVERLAP, the redraw location comes from the
    TARGET's own span -- the stale seed ea (pointing at a different leaf)
    is dropped."""
    run = tmp_path / "run"
    run.mkdir()
    # the division seeds the name at [13, 14] -- but the content actually
    # lives on the node spanning [1, 6]
    R.write_json(os.path.join(str(run), "division.json"),
                 {"decision": "divide", "seed_vocabulary": [
                     {"name": "self_harm_rule", "prose": "x",
                      "established_around": [13, 14]}],
                  "children": [{"span": [1, 12]}, {"span": [13, 20]}]})
    g = {"nodes": [
        {"id": "L1-12_n001",
         "establishes": "must not encourage or enable self harm",
         "needs": [], "provides": [], "spans": [{"lines": [1, 6]}]},
        {"id": "L13-20_n001", "establishes": "the needer",
         "needs": [{"name": "self_harm_rule",
                    "prose": "must not encourage self harm"}],
         "provides": [], "spans": [{"lines": [13, 14]}]}]}
    cands = PR.underexport_candidates(str(run), g)
    assert cands and cands[0]["via"] == "establishes-overlap"
    assert cands[0]["target_id"] == "L1-12_n001"
    assert cands[0]["established_around"] == [1, 6], \
        "the stale seed ea [13,14] must be dropped for the target's span"


def test_covers_tolerance_admits_the_flagship_case():
    """Re-review 1c: ea containment carries +-2 tolerance -- the
    interactive_vs_programmatic case (ea [3384,3386], nodes starting
    3386) must be feasible."""
    assert PR._covers([3386, 3400], [3384, 3386])     # contains ea1
    assert PR._covers([3388, 3400], [3384, 3386])     # within +2
    assert not PR._covers([3389, 3400], [3384, 3386])
    assert PR._covers([1, 3382], [3384, 3386])        # within -2
    assert not PR._covers([1, 3381], [3384, 3386])


def test_infeasible_plan_is_reported_and_never_paid(tmp_path,
                                                    monkeypatch):
    """Re-review 1c: splice feasibility is computed at PREP -- a plan
    whose redraw leaf cannot cover the establishment lines becomes a
    report row and costs nothing."""
    run = _repair_run(tmp_path)
    orig = PR.locate_leaf

    def bad_locate(udir, name):
        (seed, lo, hi, wdir, seeds), why = orig(udir, name)
        seed = dict(seed, established_around=[50, 51])   # far outside
        return (seed, lo, hi, wdir, seeds), None
    monkeypatch.setattr(PR, "locate_leaf", bad_locate)
    client = R.MockClient([])
    rep = PR.run_repair(run, _CFG, client, R.load_doc(TOY))
    assert client.calls == 0
    row = next(r for r in rep["items"] if r["status"] == "infeasible")
    assert "does not cover" in row["why"]
    assert rep["by_class"]["promise"]["infeasible"] == 1


# ----------------- final re-review 1c: splice-target displacement
def _span_node(nid, a, b):
    return {"id": nid, "establishes": nid, "needs": [], "provides": [],
            "spans": [{"lines": [a, b]}]}


def test_select_target_prefers_exact_cover_over_adjacent_tolerance():
    """THE FLAGSHIP DISPLACEMENT (ds7 review): ea [3384,3386] with the
    adjacent worked-example node L3239-3382_n017 (spans [3354,3382],
    inside the +-2 tolerance) listed FIRST must still select
    L3383-3501_n001 -- first-cover-in-graph-order spliced onto the
    neighbour."""
    n017 = _span_node("L3239-3382_n017", 3354, 3382)
    n001 = _span_node("L3383-3501_n001", 3383, 3390)
    picked = PR._select_target([n017, n001], [3384, 3386])
    assert picked["id"] == "L3383-3501_n001"
    # the do_not_facilitate case: exact cover of ea 1543 beats the
    # adjacent [1523,1541] node
    adj = _span_node("L1523-1541_n009", 1523, 1541)
    exact = _span_node("L1542-1706_n001", 1542, 1560)
    picked = PR._select_target([adj, exact], [1543, 1543])
    assert picked["id"] == "L1542-1706_n001"


def test_select_target_tiebreaks_overlap_then_narrowest_never_order():
    wide = _span_node("wide", 3380, 3400)          # overlap 3, width 20
    narrow = _span_node("narrow", 3384, 3386)      # overlap 3, width 2
    assert PR._select_target([wide, narrow],
                             [3384, 3386])["id"] == "narrow"
    partial = _span_node("partial", 3386, 3400)    # overlap 1
    full = _span_node("full", 3370, 3386)          # overlap 3, wider
    assert PR._select_target([partial, full],
                             [3384, 3386])["id"] == "full", \
        "maximum line-overlap outranks narrowness"
    # tolerance fallback fires ONLY when no exact cover exists
    only_adj = _span_node("adj", 3354, 3382)
    assert PR._select_target([only_adj], [3384, 3386])["id"] == "adj"
    assert PR._select_target([_span_node("far", 1, 100)],
                             [3384, 3386]) is None


def test_splice_promise_branch_uses_the_shared_selector(tmp_path):
    """Both call sites ride ONE selector (the coherence lesson): the
    splice itself, fed the flagship layout with the neighbour first,
    lands the provides entry on the exact-cover node."""
    g = {"nodes": [_span_node("L3239-3382_n017", 3354, 3382),
                   _span_node("L3383-3501_n001", 3383, 3390)]}
    seed = {"name": "interactive_vs_programmatic",
            "prose": "p", "established_around": [3384, 3386]}
    redraw = {"nodes": [{"id": "L3383-3501_n001", "establishes": "x",
                         "needs": [],
                         "provides": [{"name":
                                       "interactive_vs_programmatic",
                                       "prose": "p"}],
                         "spans": [{"lines": [3383, 3390]}]}]}
    status, target = PR.splice(g, seed, redraw, "u",
                               str(tmp_path / "scratch"))
    assert status == "repaired" and target == "L3383-3501_n001"
    n017 = g["nodes"][0]
    assert n017["provides"] == [], "the neighbour must stay untouched"


def test_default_budget_fallback_matches_config():
    assert PR.DEFAULT_BUDGET == pytest.approx(0.40)


def test_cli_refuses_without_yes(capsys):
    assert PR.main(["runs/nowhere"]) == 2
    assert "--yes" in capsys.readouterr().out
