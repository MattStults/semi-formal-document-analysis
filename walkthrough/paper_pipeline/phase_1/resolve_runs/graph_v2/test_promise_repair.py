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

    def bad_locate(udir, name, seed=None):
        (seed, lo, hi, wdir, seeds), why = orig(udir, name, seed)
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


# ============ 2026-08-14 prep guards (opus_recheck_report.md §4 ruling)
#: a fixture document with the REAL shapes the matcher must handle: the
#: `[?](#anchor)` and `[text](#anchor)` cross-reference forms, and the
#: `## Title {#slug authority=x}` heading form. The real model_spec is
#: read-only evidence -- the pins never depend on it.
FIXTURE_DOC = [
    "# Overview {#overview}",                                  # 1
    "",                                                        # 2
    "As outlined in the [?](#risk_taxonomy) section, the "      # 3
    "assistant balances empowerment and safety.",
    "",                                                        # 4
    "## Specific risks {#risk_taxonomy}",                       # 5
    "",                                                        # 6
    "The taxonomy of risks the assistant weighs.",              # 7
    "",                                                        # 8
    "The assistant must avoid [overstepping](#avoid_overstepping) "  # 9
    "or being judgmental.",
    "",                                                        # 10
    "## Avoid overstepping {#avoid_overstepping authority=user}",    # 11
    "",                                                        # 12
    "The assistant should follow explicit instructions without "     # 13
    "overstepping.",
    "",                                                        # 14
    "See [?](#nowhere_at_all) for more.",                      # 15
    "",                                                        # 16
    "## When appropriate, be helpful when refusing "           # 17
    "{#refusal_style authority=guideline}",
    "",                                                        # 18
    "How the assistant should style refusals.",                # 19
]


def _guard_run(tmp_path, seed, root_nodes, queue_name=None):
    """A run whose division seeds exactly `seed` and whose queue carries
    one broken_promise row for it."""
    run = tmp_path / "run"
    run.mkdir()
    R.write_json(os.path.join(str(run), "division.json"),
                 {"decision": "divide", "seed_vocabulary": [dict(seed)],
                  "children": [{"span": [1, 10]}, {"span": [11, 19]}]})
    R.write_json(os.path.join(str(run), "root_graph.json"),
                 {"nodes": root_nodes})
    R.write_json(os.path.join(str(run), "fixup_queue.json"),
                 {"items": [{"kind": "broken_promise", "verdict": "reject",
                             "detail": {"unwind": str(run),
                                        "name": queue_name
                                        or seed["name"]},
                             "reason": "needs regeneration"}]})
    return str(run)


# ------------------------------------------- GUARD 1: same referent
def test_same_referent_export_is_skipped_not_duplicated(tmp_path):
    """RED (ds7 real case, opus_recheck_report §2b idx 97-105): seed
    `authority_level_ordering`'s prose is VERBATIM the prose of the
    provided name `authority_levels_hierarchy` on L1-170_n042. The
    exact-name filter misses it, so nine queue rows planned a redraw that
    would have created a duplicate export."""
    prose = ("The ranking of instruction authority levels: root > system "
             "> developer > user > guideline.")
    seed = {"name": "authority_level_ordering", "prose": prose,
            "established_around": [7, 7]}
    run = _guard_run(tmp_path, seed, [
        {"id": "L1-170_n042", "establishes": "the hierarchy",
         "needs": [],
         "provides": [{"name": "authority_levels_hierarchy",
                       "prose": prose}],
         "spans": [{"lines": [1, 10]}]}])
    client = R.MockClient([])
    rep = PR.run_repair(run, _CFG, client, list(FIXTURE_DOC))
    assert client.calls == 0, "a duplicate export must cost nothing"
    row = next(r for r in rep["items"] if r["class"] == "promise")
    assert row["status"] == "skipped_same_referent"
    assert row["matched_name"] == "authority_levels_hierarchy"
    assert row["matched_node"] == "L1-170_n042"
    assert row["match_kind"] == "verbatim"
    assert rep["by_class"]["promise"]["skipped_same_referent"] == 1


def test_same_referent_matches_on_token_overlap_and_uses_risk_queue_sim():
    """The overlap arm rides risk_queue.sim (ONE source, not a copy), at
    the >= 0.5 threshold; below it, nothing matches."""
    import risk_queue as RQ
    g = {"nodes": [{"id": "n1", "spans": [{"lines": [856, 860]}],
                    "provides": [
        {"name": "information_hazards_prohibition",
         "prose": "The assistant must not provide detailed actionable "
                  "information hazards that enable serious harm."}]}]}
    near = ("must not provide detailed actionable information hazards "
            "enabling serious harm")
    assert RQ.sim(near, g["nodes"][0]["provides"][0]["prose"]) >= 0.5
    hit = PR.same_referent_provider(near, g, [856, 856])
    assert hit[0] == "information_hazards_prohibition"
    assert hit[2] == "token-overlap"
    assert PR.same_referent_provider("zebra quagga okapi tapir", g,
                                     [856, 856]) is None
    # verbatim containment wins even when the token overlap is low
    long_g = {"nodes": [{"id": "n2", "spans": [{"lines": [10, 10]}],
                         "provides": [
        {"name": "big_export",
         "prose": "Preamble sentence.  The  promised thing.  Plus many "
                  "further unrelated clauses about quagga okapi tapir "
                  "wildebeest springbok."}]}]}
    v = PR.same_referent_provider("The promised thing.", long_g, [10, 10])
    assert v is not None and v[2] == "verbatim" and v[0] == "big_export"


def test_same_referent_leaves_a_genuinely_missing_concept_alone(tmp_path):
    """The guard must not swallow a real defect: unrelated prose on every
    existing export leaves the plan standing."""
    seed = {"name": "promised_x", "prose": "zebra quagga okapi tapir",
            "established_around": [7, 7]}
    run = _guard_run(tmp_path, seed, [
        {"id": "L1-10_n001", "establishes": "the establishing span",
         "needs": [], "provides": [{"name": "other", "prose": "wombat"}],
         "spans": [{"lines": [5, 8]}]}])
    reply = _reply(1, 10, 10,
                   provides=[{"name": "promised_x", "prose": "p"}])
    rep = PR.run_repair(run, _CFG, R.MockClient([reply]),
                        list(FIXTURE_DOC))
    assert rep["repaired"] == 1


# -------------------------------------------- GUARD 2: citation sites
def test_citation_site_detection_and_heading_lookup():
    """The matcher, against the real shapes: `[?](#slug)`,
    `[text](#slug)`, and `## Title {#slug authority=x}`. A heading is
    never itself a citation site."""
    assert PR.heading_line_for_slug(FIXTURE_DOC, "avoid_overstepping") == 11
    assert PR.heading_line_for_slug(FIXTURE_DOC, "risk_taxonomy") == 5
    assert PR.heading_line_for_slug(FIXTURE_DOC, "refusal_style") == 17
    assert PR.heading_line_for_slug(FIXTURE_DOC, "nowhere_at_all") is None
    # [text](#slug) form (line 9) and [?](#slug) form (line 3)
    assert PR.is_citation_site(FIXTURE_DOC, 9, "avoid_overstepping")
    assert PR.is_citation_site(FIXTURE_DOC, 3, "risk_taxonomy_section")
    # the heading itself is the establishment, never a citation
    assert not PR.is_citation_site(FIXTURE_DOC, 11, "avoid_overstepping")
    # a line citing SOME OTHER anchor is left alone -- this file must not
    # decide which of several anchors a passage is "really" about
    assert not PR.is_citation_site(FIXTURE_DOC, 9, "risk_taxonomy")
    assert not PR.is_citation_site(FIXTURE_DOC, 13, "avoid_overstepping")
    assert not PR.is_citation_site(FIXTURE_DOC, 999, "avoid_overstepping")
    assert PR.concept_slug("refusal_style_section") == "refusal_style"
    assert PR.concept_slug("avoid_overstepping") == "avoid_overstepping"


def test_citation_site_plan_is_reaimed_at_the_section_heading(tmp_path):
    """RED (opus_recheck_report §4, `avoid_overstepping`): the seed's ea
    1422 is the imminent-harm rule CITING `(#avoid_overstepping)`; the
    section itself is L3239. Un-guarded, the redraw attached the concept
    to the wrong passage. Fixture analogue: ea 9 (the citation) must be
    re-aimed to the heading at 11, planning that leaf and that target."""
    seed = {"name": "avoid_overstepping",
            "prose": "the policy section on avoiding overstepping",
            "established_around": [9, 9]}
    run = _guard_run(tmp_path, seed, [
        {"id": "L1-10_n001", "establishes": "the imminent harm rule",
         "needs": [], "provides": [], "spans": [{"lines": [9, 9]}]},
        {"id": "L11-19_n001", "establishes": "the overstepping section",
         "needs": [], "provides": [], "spans": [{"lines": [11, 13]}]}])
    reply = _reply(11, 19, 19,
                   provides=[{"name": "avoid_overstepping",
                              "prose": "p"}])
    rep = PR.run_repair(run, _CFG, R.MockClient([reply]),
                        list(FIXTURE_DOC))
    row = next(r for r in rep["items"] if r["class"] == "promise")
    assert row["status"] == "repaired"
    assert row["establishment"] == "reaimed_citation_site"
    assert row["span"] == [11, 19], "the redraw must move to the section"
    assert row["target"] == "L11-19_n001", \
        "the citation node must NOT receive the splice"
    assert rep["by_class"]["promise"]["reaimed_citation_site"] == 1
    fixed = json.load(open(os.path.join(run, "root_graph.repaired.json")))
    cite = next(n for n in fixed["nodes"] if n["id"] == "L1-10_n001")
    assert cite["provides"] == []


def test_citation_site_without_a_heading_is_skipped_unpaid(tmp_path):
    """No heading carries the cited anchor: the plan is dropped with its
    own kind rather than aimed at the citation."""
    seed = {"name": "nowhere_at_all", "prose": "a dangling anchor",
            "established_around": [15, 15]}
    run = _guard_run(tmp_path, seed, [
        {"id": "L11-19_n001", "establishes": "x", "needs": [],
         "provides": [], "spans": [{"lines": [15, 15]}]}])
    client = R.MockClient([])
    rep = PR.run_repair(run, _CFG, client, list(FIXTURE_DOC))
    assert client.calls == 0
    row = next(r for r in rep["items"] if r["class"] == "promise")
    assert row["status"] == "skipped_citation_site_unresolved"
    assert rep["by_class"]["promise"][
        "skipped_citation_site_unresolved"] == 1


def test_citation_guard_covers_the_underexport_class_too(tmp_path):
    """RED (opus_recheck_report §4, the one under-export misaim):
    `sexual_content_involving_minors_section` ea 4576 is the U18
    section's cross-reference; the prohibition is established at L826, so
    the scan's target sat ~3750 lines away. The guard is ONE resolver and
    both classes call it."""
    run = tmp_path / "run"
    run.mkdir()
    R.write_json(os.path.join(str(run), "division.json"),
                 {"decision": "divide", "seed_vocabulary": [
                     {"name": "risk_taxonomy_section", "prose": "p",
                      "established_around": [3, 3]}],
                  "children": [{"span": [1, 10]}, {"span": [11, 19]}]})
    # the scan picks the CITING node (its span contains the seed's ea 3);
    # nothing overlaps by prose, so `via` is established_around -- exactly
    # the minors shape, where the target sat far from the establishment
    g = {"nodes": [
        {"id": "L1-10_n001", "establishes": "the citing overview line",
         "needs": [], "provides": [], "spans": [{"lines": [3, 3]}]},
        {"id": "L5-8_n002", "establishes": "the taxonomy of risks the "
                                           "assistant weighs",
         "needs": [], "provides": [], "spans": [{"lines": [5, 8]}]},
        {"id": "L11-19_n003", "establishes": "the needer",
         "needs": [{"name": "risk_taxonomy_section",
                    "prose": "zebra quagga okapi tapir"}],
         "provides": [], "spans": [{"lines": [11, 13]}]}]}
    R.write_json(os.path.join(str(run), "root_graph.json"), g)
    R.write_json(os.path.join(str(run), "fixup_queue.json"), {"items": []})
    reply = _reply(1, 10, 10,
                   provides=[{"name": "risk_taxonomy_section",
                              "prose": "p"}])
    rep = PR.run_repair(str(run), _CFG, R.MockClient([reply]),
                        list(FIXTURE_DOC))
    row = next(r for r in rep["items"] if r["class"] == "underexport")
    assert row["establishment"] == "reaimed_citation_site"
    assert row["status"] == "repaired"
    assert row["target"] == "L5-8_n002", \
        "the splice must land on the section, not the citing node"


def test_reaimed_plan_descends_the_RUN_ROOT_not_the_promising_unwind(
        tmp_path):
    """RED (found on the ds7 dry run): the re-aimed line lands wherever
    the DOCUMENT establishes the concept, routinely OUTSIDE the span of
    the unwind that promised it -- avoid_overstepping was promised under
    the [1368, 1541] unwind and is established at L3239. Descending the
    promising unwind fails with "no child span covers line N" and the
    guard buys nothing; the run root must be descended instead."""
    run = tmp_path / "run"
    (run / "c1").mkdir(parents=True)
    R.write_json(os.path.join(str(run), "division.json"),
                 {"decision": "divide", "seed_vocabulary": [],
                  "children": [{"span": [1, 10]}, {"span": [11, 19]}]})
    # the PROMISING unwind covers [1, 10] only -- the citation site
    R.write_json(os.path.join(str(run), "c1", "division.json"),
                 {"decision": "divide", "seed_vocabulary": [
                     {"name": "avoid_overstepping", "prose": "p",
                      "established_around": [9, 9]}],
                  "children": [{"span": [1, 5]}, {"span": [6, 10]}]})
    R.write_json(os.path.join(str(run), "root_graph.json"), {"nodes": [
        {"id": "L11-19_n001", "establishes": "the overstepping section",
         "needs": [], "provides": [], "spans": [{"lines": [11, 13]}]}]})
    R.write_json(os.path.join(str(run), "fixup_queue.json"),
                 {"items": [{"kind": "broken_promise", "verdict": "reject",
                             "detail": {"unwind": os.path.join(str(run),
                                                               "c1"),
                                        "name": "avoid_overstepping"},
                             "reason": "r"}]})
    reply = _reply(11, 19, 19,
                   provides=[{"name": "avoid_overstepping", "prose": "p"}])
    rep = PR.run_repair(str(run), _CFG, R.MockClient([reply]),
                        list(FIXTURE_DOC))
    row = next(r for r in rep["items"] if r["class"] == "promise")
    assert row["status"] == "repaired", row
    assert row["span"] == [11, 19]
    assert row["establishment"] == "reaimed_citation_site"


# ------------------------- GUARD 3: section seeds with no established_around
def test_section_seed_without_ea_plans_from_its_heading(tmp_path):
    """RED (opus_recheck_report §4 "Confirmed defects with NO plan"):
    control_side_effects_section / risk_taxonomy_section /
    red_line_principles_section / refusal_style_section all failed prep
    with "no usable established_around" -- four confirmed defects with no
    plan at all. The fallback slugs the seed name (stripping a trailing
    `_section`) and finds that section's heading. GENERAL: no name is
    hardcoded."""
    seed = {"name": "refusal_style_section",
            "prose": "how the assistant should style refusals"}
    run = _guard_run(tmp_path, seed, [
        {"id": "L11-19_n001", "establishes": "the refusal style section",
         "needs": [], "provides": [], "spans": [{"lines": [17, 19]}]}])
    reply = _reply(11, 19, 19,
                   provides=[{"name": "refusal_style_section",
                              "prose": "p"}])
    rep = PR.run_repair(run, _CFG, R.MockClient([reply]),
                        list(FIXTURE_DOC))
    row = next(r for r in rep["items"] if r["class"] == "promise")
    assert row["status"] == "repaired"
    assert row["establishment"] == "section_heading_fallback"
    assert "line 17" in row["establishment_why"]
    assert row["target"] == "L11-19_n001"
    assert rep["by_class"]["promise"]["section_heading_fallback"] == 1


def test_seed_with_no_ea_and_no_heading_still_fails_as_before(tmp_path):
    """The fallback is additive: a seed whose slug names no section keeps
    the pre-guard failure row (and its message)."""
    seed = {"name": "never_a_section_anywhere", "prose": "p"}
    run = _guard_run(tmp_path, seed, [
        {"id": "L1-10_n001", "establishes": "x", "needs": [],
         "provides": [], "spans": [{"lines": [1, 3]}]}])
    client = R.MockClient([])
    rep = PR.run_repair(run, _CFG, client, list(FIXTURE_DOC))
    row = next(r for r in rep["items"] if r["class"] == "promise")
    assert row["status"] == "failed"
    assert "no usable established_around" in row["why"]
    assert client.calls == 0


def test_resolve_establishment_is_the_one_resolver():
    """All four outcomes off one function -- the coherence lesson."""
    keep = {"name": "avoid_overstepping", "prose": "p",
            "established_around": [13, 13]}
    assert PR.resolve_establishment(keep, FIXTURE_DOC) == \
        ([13, 13], None, None)
    ea, kind, _ = PR.resolve_establishment(
        dict(keep, established_around=[9, 9]), FIXTURE_DOC)
    assert (ea, kind) == ([11, 16], "reaimed_citation_site"), \
        "a re-derived ea is the section BODY range, never the bare " \
        "heading line (review B2a)"
    ea, kind, _ = PR.resolve_establishment(
        {"name": "refusal_style_section", "prose": "p"}, FIXTURE_DOC)
    assert (ea, kind) == ([17, 19], "section_heading_fallback")
    ea, kind, _ = PR.resolve_establishment(
        {"name": "nowhere_at_all", "prose": "p",
         "established_around": [15, 15]}, FIXTURE_DOC)
    assert (ea, kind) == (None, "skipped_citation_site_unresolved")
    ea, kind, _ = PR.resolve_establishment(
        {"name": "unknown_thing", "prose": "p"}, FIXTURE_DOC)
    assert (ea, kind) == (None, "no_establishment")


# ------------------------------------- optional opus_verdicts intersection
def test_opus_verdicts_narrows_the_scope_to_confirmed_defects(tmp_path):
    """The evidence intersection (EXPERIMENTS "OPUS RECHECK" ruling: the
    repair scope is the 14 evidence-confirmed defects, not the 45
    reject-default rows). An `uphold` row is dropped unpaid."""
    seed = {"name": "promised_x", "prose": "zebra quagga",
            "established_around": [7, 7]}
    run = _guard_run(tmp_path, seed, [
        {"id": "L1-10_n001", "establishes": "x", "needs": [],
         "provides": [], "spans": [{"lines": [5, 8]}]}])
    vp = tmp_path / "verdicts.json"
    vp.write_text(json.dumps({"items": [
        {"idx": 0, "kind": "broken_promise",
         "detail": {"name": "promised_x"}, "opus_decision": "uphold"},
        {"idx": 1, "kind": "broken_promise",
         "detail": {"name": "someone_else"}, "opus_decision": "reject"},
        {"idx": 2, "kind": "dropped_merge",
         "detail": {"name": "promised_x"}, "opus_decision": "reject"}]}))
    assert PR.opus_confirmed_names(str(vp)) == {"someone_else"}
    cfg = dict(_CFG, promise_repair=dict(_CFG["promise_repair"],
                                         opus_verdicts=str(vp)))
    client = R.MockClient([])
    rep = PR.run_repair(run, cfg, client, list(FIXTURE_DOC))
    assert client.calls == 0
    row = next(r for r in rep["items"] if r["class"] == "promise")
    assert row["status"] == "skipped_not_opus_confirmed"
    assert rep["by_class"]["promise"]["skipped_not_opus_confirmed"] == 1


def test_opus_verdicts_absent_leaves_behaviour_unchanged(tmp_path):
    """Default absent: the same run repairs exactly as before the key
    existed."""
    run = _repair_run(tmp_path)
    reply = _reply(1, 12, 12,
                   provides=[{"name": "promised_x",
                              "prose": "the promised thing"}])
    rep = PR.run_repair(run, _CFG, R.MockClient([reply]),
                        R.load_doc(TOY))
    assert rep["repaired"] == 1 and "opus_verdicts" not in \
        json.dumps(_CFG)


# ================= convergence review B1/B2: the two blocking findings
#: the per-section authority TEMPLATE, verbatim from ds7. Any two of
#: these score sim 0.545 against each other -- the shape that gave the
#: 0.5 threshold no discriminating power.
_AUTH_TEMPLATE = "Rules in the #{} section carry user-level instruction " \
                 "authority."


def test_B1_same_referent_requires_locality_not_just_prose(tmp_path):
    """RED (convergence review B1 -- a FALSE SKIP of an evidence-confirmed
    defect): `user_authority_section_rules` (ea 3150, the #avoid_errors
    heading) was skipped against `user_authority` on L3239-3382_n001 --
    a DIFFERENT section 89 lines away -- because the document's
    per-section authority TEMPLATE scores sim 0.545 for ANY two such
    claims. Opus lists this name as a confirmed defect. The providing
    NODE must cover the establishment."""
    import risk_queue as RQ
    seed_prose = ("Rules in sections marked authority=user carry "
                  "user-level instruction authority")
    far = _AUTH_TEMPLATE.format("avoid_overstepping")
    assert RQ.sim(seed_prose, far) >= 0.5, \
        "the template really does clear the threshold -- that is the bug"
    g = {"nodes": [
        {"id": "L3239-3382_n001", "establishes": far,
         "needs": [], "provides": [{"name": "user_authority",
                                    "prose": far}],
         "spans": [{"lines": [3239, 3239]}]}]}
    assert PR.same_referent_provider(seed_prose, g, [3150, 3150]) is None, \
        "a provider 89 lines from the establishment must NOT skip the plan"
    # ... and the very same provider DOES skip when it is local
    assert PR.same_referent_provider(seed_prose, g, [3239, 3239]) is not None


def test_B1_the_two_correct_verbatim_skips_still_skip():
    """The fix must not cost the guard its true positives: both correct
    ds7 skips already satisfy locality (L1-170_n042 covers
    `authority_level_ordering`'s ea 69; L3505-3953_n001 covers
    `section_authority_level`'s ea 3506)."""
    p1 = "which of two authority levels outranks the other"
    g1 = {"nodes": [{"id": "L1-170_n042", "provides": [
        {"name": "authority_levels_hierarchy", "prose": p1}],
        "spans": [{"lines": [69, 69]}, {"lines": [186, 191]}]}]}
    hit = PR.same_referent_provider(p1, g1, [69, 101])
    assert hit and hit[0] == "authority_levels_hierarchy"
    assert hit[2] == "verbatim"
    p2 = ("The authority level assigned to a section's rules by its "
          "heading metadata.")
    g2 = {"nodes": [{"id": "L3505-3953_n001", "provides": [
        {"name": "user_authority", "prose": p2}],
        "spans": [{"lines": [3506, 3506]}, {"lines": [3629, 3629]}]}]}
    hit = PR.same_referent_provider(p2, g2, [3506, 3506])
    assert hit and hit[0] == "user_authority" and hit[2] == "verbatim"
    # no usable ea => no locality to test => the guard declines to fire
    assert PR.same_referent_provider(p1, g1, None) is None


#: the reviewer's own three reproduction cases, node spans and establishes
#: copied from runs/ds7/root_graph.json
def _ds7_avoid_overstepping_nodes():
    return [
        {"id": "L3147-3238_n014", "provides": [], "needs": [],
         "establishes": "A worked example about search.",
         "spans": [{"lines": [3220, 3237]}]},
        {"id": "L3239-3382_n001", "needs": [],
         "establishes": _AUTH_TEMPLATE.format("avoid_overstepping"),
         "provides": [{"name": "user_authority", "prose": "p"}],
         "spans": [{"lines": [3239, 3239]}]},
        {"id": "L3239-3382_n002", "provides": [], "needs": [],
         "establishes": "The assistant should help the developer and user "
                        "by following explicit instructions without "
                        "overstepping.",
         "spans": [{"lines": [3241, 3241]}]},
        {"id": "L3239-3382_n007", "provides": [], "needs": [],
         "establishes": "A worked example of transformation.",
         "spans": [{"lines": [3245, 3281]}]}]


def _ds7_overview_nodes():
    return [
        {"id": "L1-170_n016", "provides": [], "needs": [],
         "establishes": "In the main body of the Model Spec, commentary "
                        "that is not directly instructing the model will "
                        "be placed in blocks like this one.",
         "spans": [{"lines": [26, 26]}]},
        {"id": "L1-170_n017", "provides": [], "needs": [],
         "establishes": "Human safety and human rights are paramount to "
                        "OpenAI's mission.",
         "spans": [{"lines": [30, 30]}]},
        {"id": "L1-170_n032", "provides": [], "needs": [],
         "establishes": "The Model Spec includes root-level rules as well "
                        "as user- and guideline-level defaults.",
         "spans": [{"lines": [51, 51]}]},
        {"id": "L1-170_n033", "provides": [], "needs": [],
         "establishes": "OpenAI considers three broad categories of risk, "
                        "each with its own set of potential mitigations.",
         "spans": [{"lines": [55, 55]}]}]


def test_B2_section_mode_declines_the_authority_assignment_node():
    """RED (convergence review B2b -- THE CORRUPTING ONE): ea
    [3239, 3239] selects L3239-3382_n001, whose only export is
    `user_authority` -- the section's authority ASSIGNMENT. Splicing the
    section's substance there merges assignment with definition, which
    this repo has ruled distinct (the 16/16 dropped_merge upholds). The
    substantive node is L3239-3382_n002."""
    nodes = _ds7_avoid_overstepping_nodes()
    assert PR._select_target(nodes, [3239, 3239])["id"] \
        == "L3239-3382_n001", "the un-guarded ranking picks the assignment"
    picked = PR._select_target(nodes, [3239, 3318], section=True)
    assert picked["id"] == "L3239-3382_n002", picked["id"]


def test_B2_section_mode_excludes_nodes_above_the_heading():
    """RED (convergence review B2a): both off-by-two misses came from the
    +-2 tolerance reaching BACKWARDS past the heading into the previous
    section, then graph order handing back the earlier node.
    risk_taxonomy heading 53 -> L1-170_n033 (not n032 at 51);
    red_line_principles heading 28 -> L1-170_n017 (not n016 at 26)."""
    nodes = _ds7_overview_nodes()
    assert PR._select_target(nodes, [53, 53])["id"] == "L1-170_n032", \
        "the un-guarded ranking picks the commentary two lines above"
    assert PR._select_target(nodes, [53, 62], section=True)["id"] \
        == "L1-170_n033"
    assert PR._select_target(nodes, [28, 28])["id"] == "L1-170_n016", \
        "the un-guarded ranking picks the commentary two lines above"
    assert PR._select_target(nodes, [28, 44], section=True)["id"] \
        == "L1-170_n017"


def test_B2_section_mode_ranks_earliest_not_widest():
    """The body range must not simply hand max-overlap the widest node:
    the worked example L3239-3382_n007 spans 37 lines of the section and
    would win the default ranking outright."""
    nodes = _ds7_avoid_overstepping_nodes()
    assert PR._select_target(nodes, [3239, 3318])["id"] \
        == "L3239-3382_n007", "max-overlap picks the worked example"
    assert PR._select_target(nodes, [3239, 3318], section=True)["id"] \
        == "L3239-3382_n002"


def test_B2_authority_class_test_rides_recurse_drivers_constants():
    """ONE source for what counts as authority-class -- the constants the
    validator and the autofix already share, canonical names AND the
    `X_section_<level>_authority` coinage shape."""
    assert PR.is_authority_export("user_authority")
    assert PR.is_authority_export("authority_levels_hierarchy")
    assert PR.is_authority_export(
        "ask_clarifying_questions_section_guideline_authority")
    assert not PR.is_authority_export("implicit_biases")
    assert PR._is_authority_assignment(
        {"provides": [{"name": "user_authority"}]})
    # MIXED provides is not a pure assignment node -- it carries substance
    assert not PR._is_authority_assignment(
        {"provides": [{"name": "user_authority"},
                      {"name": "avoid_overstepping"}]})
    assert not PR._is_authority_assignment({"provides": []})


def test_B2_section_mode_reports_rather_than_splicing_wrongly(tmp_path):
    """"If that leaves no candidate, report rather than splice": a
    section whose only node is the authority assignment yields an
    infeasible row and costs nothing."""
    seed = {"name": "refusal_style_section", "prose": "zebra quagga"}
    run = _guard_run(tmp_path, seed, [
        {"id": "L11-19_n001", "establishes": "assignment only",
         "needs": [], "provides": [{"name": "guideline_authority",
                                    "prose": "a"}],
         "spans": [{"lines": [17, 17]}]}])
    client = R.MockClient([])
    rep = PR.run_repair(run, _CFG, client, list(FIXTURE_DOC))
    assert client.calls == 0
    row = next(r for r in rep["items"] if r["class"] == "promise")
    assert row["status"] == "infeasible"
    assert "authority-assignment" in row["why"]


def test_B2_section_span_is_the_body_to_the_next_same_level_heading():
    """The range: heading through the line before the next heading of the
    same-or-higher level, capped."""
    assert PR.section_span(FIXTURE_DOC, 5) == [5, 10]     # ## .. next ##
    assert PR.section_span(FIXTURE_DOC, 11) == [11, 16]
    assert PR.section_span(FIXTURE_DOC, 17) == [17, 19]   # to EOF
    # a heading closes only at the SAME-or-higher level: the level-1
    # heading at 1 is not closed by the level-2 headings below it
    assert PR.section_span(FIXTURE_DOC, 1) == [1, 19]
    assert PR.section_span(FIXTURE_DOC, 5, cap=2) == [5, 6]
    assert PR.heading_level(FIXTURE_DOC[4]) == 2
    assert PR.heading_level("plain prose") is None


def test_B2_section_body_is_clipped_to_the_redraw_leaf():
    """A body range that outruns the leaf is clipped: a seed whose ea
    straddles the leaf boundary is owed by NO leaf (validate_leaf's
    boundary ruling), so the redraw would never be told what it owes."""
    seed = {"name": "x", "prose": "p", "established_around": [17, 40]}
    assert PR._clip_ea(seed, 11, 19)["established_around"] == [17, 19]
    errs = R.validate_leaf(_leaf_graph(11, 19), 11, 19, ["x"] * 19,
                           seeds=[PR._clip_ea(seed, 11, 19)],
                           enforce_promise_delivery=True)
    assert any("x" in e for e in errs), \
        "after clipping the leaf must OWE the promise"


def test_B3_underexport_class_gets_the_same_referent_filter(tmp_path):
    """Review B3 (non-blocking): the under-export scan aims at a node
    with EMPTY provides, but a NEIGHBOURING node at the same
    establishment can already export the referent --
    `sexual_content_involving_minors_section` re-aims onto L826 where
    `sexual_content_minors_prohibition` already exports it. One
    function, both classes."""
    run = tmp_path / "run"
    run.mkdir()
    R.write_json(os.path.join(str(run), "division.json"),
                 {"decision": "divide", "seed_vocabulary": [
                     {"name": "risk_taxonomy_section",
                      "prose": "the taxonomy of risks the assistant weighs",
                      "established_around": [3, 3]}],
                  "children": [{"span": [1, 10]}, {"span": [11, 19]}]})
    R.write_json(os.path.join(str(run), "root_graph.json"), {"nodes": [
        {"id": "L1-10_n001", "establishes": "the citing overview line",
         "needs": [], "provides": [], "spans": [{"lines": [3, 3]}]},
        {"id": "L5-8_n002", "establishes": "the section body",
         "needs": [],
         "provides": [{"name": "risk_taxonomy_prohibition",
                       "prose": "the taxonomy of risks the assistant "
                                "weighs"}],
         "spans": [{"lines": [7, 7]}]},
        {"id": "L11-19_n003", "establishes": "the needer",
         "needs": [{"name": "risk_taxonomy_section",
                    "prose": "the taxonomy of risks the assistant "
                             "weighs"}],
         "provides": [], "spans": [{"lines": [11, 13]}]}]})
    R.write_json(os.path.join(str(run), "fixup_queue.json"), {"items": []})
    client = R.MockClient([])
    rep = PR.run_repair(str(run), _CFG, client, list(FIXTURE_DOC))
    assert client.calls == 0, "a duplicate export must cost nothing"
    row = next(r for r in rep["items"] if r["class"] == "underexport")
    assert row["status"] == "skipped_same_referent"
    assert row["matched_name"] == "risk_taxonomy_prohibition"
    assert rep["by_class"]["underexport"]["skipped_same_referent"] == 1


def test_B3_underexport_target_that_already_exports_is_skipped(tmp_path):
    """RED (review B3, the residual the prose test cannot see): the
    under-export class is DEFINED as a dangling whose content exists as a
    node with EMPTY provides. `sexual_content_involving_minors_section`
    re-aims onto L797-830_n014, which already exports
    `sexual_content_minors_prohibition` -- but that prose pair scores
    0.364 against the 0.5 threshold, so only the class's own contract
    catches it. Authority-only exports do NOT count as substance."""
    import risk_queue as RQ
    assert round(RQ.sim(
        "The section of the Model Spec that prohibits sexual content "
        "involving minors.",
        "the prohibition on producing sexual content involving minors"),
        3) == 0.364, "the prose signal really is below threshold"
    assert PR._exports_substance(
        {"provides": [{"name": "sexual_content_minors_prohibition"}]})
    assert not PR._exports_substance(
        {"provides": [{"name": "user_authority"}]})
    assert not PR._exports_substance({"provides": []})
    run = tmp_path / "run"
    run.mkdir()
    R.write_json(os.path.join(str(run), "division.json"),
                 {"decision": "divide", "seed_vocabulary": [],
                  "children": [{"span": [1, 10]}, {"span": [11, 19]}]})
    R.write_json(os.path.join(str(run), "root_graph.json"), {"nodes": [
        {"id": "L1-10_n014", "establishes": "the prohibition itself",
         "needs": [],
         "provides": [{"name": "minors_prohibition", "prose": "zebra"}],
         "spans": [{"lines": [7, 7]}]},
        {"id": "L11-19_n003", "establishes": "the U18 needer",
         "needs": [{"name": "minors_section",
                    "prose": "the prohibition itself"}],
         "provides": [], "spans": [{"lines": [11, 13]}]}]})
    R.write_json(os.path.join(str(run), "fixup_queue.json"), {"items": []})
    client = R.MockClient([])
    rep = PR.run_repair(str(run), _CFG, client, list(FIXTURE_DOC))
    assert client.calls == 0, "a duplicate export must cost nothing"
    row = next(r for r in rep["items"] if r["class"] == "underexport")
    assert row["status"] == "skipped_same_referent"
    assert row["match_kind"] == "target-already-exports"
    assert row["matched_name"] == "minors_prohibition"


def test_B3_promise_class_keeps_targets_that_export_adjacent_names(
        tmp_path):
    """The contract arm is scoped to the under-export class: a promise
    plan stands on a recorded division promise, and `refusal_style_section`
    legitimately aims at a node exporting `safe_complete_rule` -- Opus
    confirms nothing refusal-style is exported there."""
    seed = {"name": "refusal_style_section", "prose": "zebra quagga"}
    run = _guard_run(tmp_path, seed, [
        {"id": "L11-19_n018", "establishes": "the refusal style section",
         "needs": [],
         "provides": [{"name": "safe_complete_rule", "prose": "okapi"}],
         "spans": [{"lines": [17, 19]}]}])
    reply = _reply(11, 19, 19,
                   provides=[{"name": "refusal_style_section",
                              "prose": "p"}])
    rep = PR.run_repair(run, _CFG, R.MockClient([reply]),
                        list(FIXTURE_DOC))
    row = next(r for r in rep["items"] if r["class"] == "promise")
    assert row["status"] == "repaired", row
    assert row["target"] == "L11-19_n018"


def test_default_budget_fallback_matches_config():
    assert PR.DEFAULT_BUDGET == pytest.approx(0.40)


def test_cli_refuses_without_yes(capsys):
    assert PR.main(["runs/nowhere"]) == 2
    assert "--yes" in capsys.readouterr().out
