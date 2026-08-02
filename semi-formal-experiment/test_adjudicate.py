"""Tests for adjudicate.py (Agent C): worksheet rendering and --score."""
import json

import pytest

import adjudicate
import delta
from test_delta import doc, A, B, C, D, E

LONG = ("The assistant must follow all applicable instructions from the "
        "system prompt, the developer, and the user, resolving conflicts by "
        "the priority order set out above, unless doing so would violate a "
        "root-level principle.")


def inv_rows():
    return [
        {"id": A, "source_id": "a", "locator": "chain_of_command:173",
         "quote": LONG, "marked_span": "must follow all applicable instructions",
         "kind": "conditional", "modality": ["must"], "has_defeater": True},
        {"id": B, "source_id": "b", "locator": "chain_of_command:181",
         "quote": "The assistant should default to inaction when two "
                  "root-level principles conflict.",
         "marked_span": "", "kind": "conditional", "modality": ["should"],
         "has_defeater": False},
        {"id": C, "source_id": "c", "locator": "chain_of_command:190",
         "quote": "The assistant may decline a request it judges unsafe.",
         "marked_span": "", "kind": "conditional", "modality": ["may"],
         "has_defeater": False},
        {"id": D, "source_id": "d", "locator": "chain_of_command:201",
         "quote": "The assistant must not deceive the user.",
         "marked_span": "", "kind": "conditional", "modality": ["must not"],
         "has_defeater": False},
    ]


@pytest.fixture
def inv(tmp_path):
    p = tmp_path / "inventory.json"
    p.write_text(json.dumps(inv_rows()))
    return adjudicate.load_inventory(str(p), section=None)


@pytest.fixture
def setup():
    tool = [doc("tool", "t1", [[A, B], [A, C]]),
            doc("tool", "t2", [[A, B], [A, C]])]
    base = [doc("baseline", "b1", [[A, B], [B, D]]),
            doc("baseline", "b2", [[A, B]]),
            doc("baseline", "b3", [[A, B], [B, D]])]
    m = delta.compute(tool, base)
    return tool, base, m


# ------------------------------------------------------------- rendering

def test_worksheet_renders_all_deltas_and_no_both_items(inv, setup):
    tool, base, m = setup
    ws = adjudicate.render_worksheet(m, inv, tool, base)
    items = adjudicate.parse_worksheet(ws)
    assert [tuple(i["pair"]) for i in items] == [(A, C), (B, D)]
    assert {i["bucket"] for i in items} == {"tool_only", "baseline_only"}
    # the both-found pair appears nowhere as an item
    assert "<!-- ITEM tool_only fa_a fa_b -->" not in ws
    assert "<!-- ITEM baseline_only fa_a fa_b -->" not in ws


def test_worksheet_prints_the_full_clause_never_truncated(inv, setup):
    tool, base, m = setup
    ws = adjudicate.render_worksheet(m, inv, tool, base)
    assert LONG in ws.replace("\n> ", " ").replace("> ", "")
    assert "..." not in ws.split("### 1.")[1].split("Verdict")[0]
    # the marked span is shown in addition to, not instead of, the clause
    assert "anchor span" in ws


def test_every_item_has_locators_ids_verdict_slots_and_the_found_question(
        inv, setup):
    tool, base, m = setup
    ws = adjudicate.render_worksheet(m, inv, tool, base)
    body = ws.split("---\n\n", 1)[1]
    assert body.count(adjudicate.FOUND_Q) == 2
    for v in adjudicate.VERDICTS:
        assert body.count(f"- [ ] {v}") == 2
    assert "responsible atom or rule: ____" in body
    assert "clause id: ____" in body
    assert "missing atom: ____" in body
    assert "chain_of_command:190" in body and "chain_of_command:201" in body


def test_tool_only_shows_ctx_atoms_and_baseline_only_does_not(inv, setup):
    tool, base, m = setup
    ws = adjudicate.render_worksheet(m, inv, tool, base)
    first, second = ws.split("<!-- ITEM ")[1], ws.split("<!-- ITEM ")[2]
    assert "Witness atoms (`ctx`)" in first and "`ctx_fa_a`" in first
    assert "Witness atoms (`ctx`)" not in second
    assert "situation for fa_b+fa_d" in second


def test_header_shows_metrics_and_stop_rules_before_the_items(inv, setup):
    tool, base, m = setup
    ws = adjudicate.render_worksheet(m, inv, tool, base)
    head = ws.split("<!-- ITEM")[0]
    assert "baseline_self_agreement" in head and "C_tool" in head
    assert "Stop rules" in head and "attribution_rate" in head
    assert "Coverage < 70%" in head


def test_missing_inventory_row_is_flagged_not_silently_dropped(setup):
    tool, base, m = setup
    ws = adjudicate.render_worksheet(m, {}, tool, base)
    assert "not found in inventory" in ws
    assert len(adjudicate.parse_worksheet(ws)) == 2


def test_identical_conflict_sets_render_no_items():
    tool = [doc("tool", "t1", [[A, B]])]
    base = [doc("baseline", "b1", [[A, B]])]
    m = delta.compute(tool, base)
    ws = adjudicate.render_worksheet(m, {}, tool, base)
    assert adjudicate.parse_worksheet(ws) == []
    assert "No deltas" in ws


def test_load_inventory_accepts_raw_focus_areas():
    inv = adjudicate.load_inventory()          # modelspec_focus_areas.json
    assert len(inv) == 62
    row = inv["fa_8ep1"]
    assert row["quote"].startswith("Above all else")
    # Locators carry the focus id: 259 focus areas share only 158 bare line
    # locators, so the id is what makes them unique (and resolvable) — see
    # inventory.locator_is_unique.
    assert row["locator"] == \
        "model_spec@2025-12-18 > The chain of command > L173 [fa_8ep1]"


def test_locator_comes_from_agent_a_not_resynthesized():
    """The worksheet must print A's exact locator format so ids stay
    resolvable across the pipeline."""
    import inventory
    inv = adjudicate.load_inventory()
    a_rows = {r["id"]: r for r in inventory.load_section()}
    assert len(a_rows) == 62
    for rid, row in inv.items():
        assert row["locator"] == a_rows[rid]["locator"]
        assert row["quote"] == a_rows[rid]["quote"]


def test_agent_a_rows_pass_straight_through(tmp_path):
    import inventory
    p = tmp_path / "inv.json"
    p.write_text(json.dumps(inventory.load_section()))
    inv = adjudicate.load_inventory(str(p), section=None)
    assert inv["fa_8ep1"]["locator"].startswith("model_spec@2025-12-18 > ")


# ---------------------------------------------------------------- scoring

def fill(ws, answers):
    """answers: [(verdict, slot_or_None, 'Y'/'N'), ...] one per item, in order."""
    chunks = ws.split("<!-- ITEM ")
    out = [chunks[0]]
    for chunk, (verdict, slot, yn) in zip(chunks[1:], answers):
        if verdict:
            lab = adjudicate.SLOT_LABEL.get(verdict)
            old = f"- [ ] {verdict}" + (f" --- {lab}: ____" if lab else "")
            new = f"- [x] {verdict}" + (f" --- {lab}: {slot}" if lab else "")
            chunk = chunk.replace(old, new)
        if yn:
            chunk = chunk.replace("answer: __", f"answer: {yn}")
        out.append(chunk)
    return "<!-- ITEM ".join(out)


def test_score_round_trips_a_filled_worksheet(inv, setup):
    tool, base, m = setup
    ws = adjudicate.render_worksheet(m, inv, tool, base)
    filled = fill(ws, [("ARTIFACT", "atom_root_authority", "Y"),
                       ("REAL", None, "N")])
    items = adjudicate.parse_worksheet(filled)
    assert [i["verdict"] for i in items] == ["ARTIFACT", "REAL"]
    assert items[0]["slot"] == "atom_root_authority"
    assert [i["would_have_found"] for i in items] == ["Y", "N"]

    s = adjudicate.score(items, m)
    assert s["verdict_distribution"] == {"ARTIFACT": 1, "REAL": 1}
    assert s["verdict_distribution_by_bucket"]["tool_only"]["ARTIFACT"] == 1
    assert s["verdict_distribution_by_bucket"]["baseline_only"]["REAL"] == 1
    assert s["attribution_rate"] == 1.0
    assert s["real_and_would_not_have_found"] == 1
    assert s["n_adjudicated"] == 2 and s["unfilled"] == []


def test_unfilled_and_double_checked_items_are_reported_not_counted(inv, setup):
    tool, base, m = setup
    ws = adjudicate.render_worksheet(m, inv, tool, base)
    # item 1 left blank; item 2 has two boxes checked
    filled = fill(ws, [(None, None, None), ("REAL", None, "Y")])
    head, i1, i2 = filled.split("<!-- ITEM ")
    i2 = i2.replace("- [ ] ARTIFACT", "- [x] ARTIFACT", 1)
    filled = "<!-- ITEM ".join([head, i1, i2])
    s = adjudicate.score(adjudicate.parse_worksheet(filled), m)
    assert s["n_adjudicated"] == 0
    assert s["unfilled"] == [[A, C]]
    assert s["ambiguous_multi_check"] == [[B, D]]


def test_attribution_rate_counts_only_single_named_causes(inv, setup):
    tool, base, m = setup
    items = [
        {"bucket": "tool_only", "pair": [A, C], "verdicts": ["ARTIFACT"],
         "verdict": "ARTIFACT", "slot": "atom_x", "would_have_found": "Y"},
        {"bucket": "tool_only", "pair": [A, D], "verdicts": ["ARTIFACT"],
         "verdict": "ARTIFACT", "slot": "atom_x and rule_y",
         "would_have_found": "Y"},
        {"bucket": "tool_only", "pair": [B, C], "verdicts": ["ARTIFACT"],
         "verdict": "ARTIFACT", "slot": "____", "would_have_found": "Y"},
        {"bucket": "baseline_only", "pair": [B, D], "verdicts": ["ARTIFACT"],
         "verdict": "ARTIFACT", "slot": "atom_z", "would_have_found": "Y"},
    ]
    s = adjudicate.score(items, m)
    assert s["tool_only_artifacts"] == 3          # baseline-only ones excluded
    assert s["attribution_rate"] == pytest.approx(1 / 3)
    assert s["stop_rules"]["attribution_rate_below_half"]["fired"] is True


def test_coverage_cost_is_reported_apart_from_artifacts_and_misses():
    """A baseline-only OUT OF ENCODED SCOPE item is the coverage cost in
    conflict terms: it must not be pooled with ARTIFACT or with genuine
    misses, and tool-only out-of-scope items must not inflate it."""
    def it(bucket, verdict, slot=None):
        return {"bucket": bucket, "pair": [A, B], "verdicts": [verdict],
                "verdict": verdict, "slot": slot, "would_have_found": "Y"}
    items = [it("baseline_only", "OUT OF ENCODED SCOPE", "atom_p"),
             it("baseline_only", "OUT OF ENCODED SCOPE", "atom_q"),
             it("baseline_only", "REAL"),
             it("baseline_only", "ARTIFACT", "rule_r"),
             it("baseline_only", "RESOLVED ELSEWHERE", "fa_z"),
             it("tool_only", "OUT OF ENCODED SCOPE", "atom_s")]
    s = adjudicate.score(items)
    assert s["coverage_cost_conflicts"] == 2          # not 3: tool-only excluded
    assert s["baseline_only_genuine_misses"] == 1
    assert s["baseline_only_artifacts"] == 1
    assert s["baseline_only_resolved_elsewhere"] == 1
    assert s["baseline_only_adjudicated"] == 5
    assert s["verdict_distribution"]["OUT OF ENCODED SCOPE"] == 3
    md = adjudicate.score_markdown(s)
    assert "Coverage cost, in conflict terms" in md
    assert "2 of 5 adjudicated baseline-only items are OUT OF ENCODED SCOPE" in md


def test_coverage_cost_is_zero_when_nothing_is_out_of_scope():
    s = adjudicate.score([{"bucket": "baseline_only", "pair": [A, B],
                           "verdicts": ["REAL"], "verdict": "REAL",
                           "slot": None, "would_have_found": "N"}])
    assert s["coverage_cost_conflicts"] == 0
    assert s["baseline_only_genuine_misses"] == 1


def test_stop_rule_coverage_below_70_percent():
    m = {"coverage": {"coverage": 0.5}, "baseline_self_agreement": 0.8}
    s = adjudicate.score([], m)
    assert s["stop_rules"]["coverage_below_70pct"]["fired"] is True
    assert s["any_stop_rule_fired"] is True


def test_stop_rule_baseline_self_agreement_near_zero():
    s = adjudicate.score([], {"baseline_self_agreement": 0.0})
    assert s["stop_rules"]["baseline_self_agreement_near_zero"]["fired"] is True


def test_stop_rule_noise_without_insight_needs_ten_adjudications():
    def it(v, found="Y"):
        return {"bucket": "tool_only", "pair": [A, B], "verdicts": [v],
                "verdict": v, "slot": "atom_x", "would_have_found": found}
    nine = [it("ARTIFACT")] * 6 + [it("REAL")] * 3
    assert adjudicate.score(nine)["stop_rules"][
        "noise_without_insight"]["evaluated"] is False
    ten = nine + [it("REAL")]
    assert adjudicate.score(ten)["stop_rules"][
        "noise_without_insight"]["fired"] is True
    # one REAL that the reader would not have found defuses it
    ten_ok = nine + [it("REAL", "N")]
    assert adjudicate.score(ten_ok)["stop_rules"][
        "noise_without_insight"]["fired"] is False


def test_no_stop_rule_fires_on_healthy_numbers(inv, setup):
    tool, base, m = setup
    m["coverage"] = {"coverage": 0.85}
    items = [{"bucket": "tool_only", "pair": [A, C], "verdicts": ["REAL"],
              "verdict": "REAL", "slot": None, "would_have_found": "N"}]
    s = adjudicate.score(items, m)
    assert s["any_stop_rule_fired"] is False
    assert "No stop rule fired" in adjudicate.score_markdown(s)


def test_score_markdown_reports_every_stop_rule(inv, setup):
    s = adjudicate.score([], {"baseline_self_agreement": 0.0})
    md = adjudicate.score_markdown(s)
    for name in s["stop_rules"]:
        assert name in md


def test_cli_render_then_score_round_trip(tmp_path, setup):
    tool, base, m = setup
    paths = []
    for d in tool + base:
        p = tmp_path / f"{d['source']}_{d['run_id']}.json"
        p.write_text(json.dumps(d))
        paths.append(str(p))
    invp = tmp_path / "inv.json"
    invp.write_text(json.dumps(inv_rows()))
    wsp = tmp_path / "ws.md"
    adjudicate.main(["--tool", *paths[:2], "--baseline", *paths[2:],
                     "--inventory", str(invp), "--out", str(wsp)])
    filled = fill(wsp.read_text(), [("REAL", None, "N"),
                                    ("OUT OF ENCODED SCOPE", "atom_q", "Y")])
    wsp.write_text(filled)
    outp = tmp_path / "scores.json"
    adjudicate.main(["--score", str(wsp), "--out-json", str(outp)])
    s = json.loads(outp.read_text())
    assert s["verdict_distribution"] == {"REAL": 1, "OUT OF ENCODED SCOPE": 1}


# ==========================================================================
# Regressions from the first REAL chain run (gpt-oss-20b, smoke_live2).
# ==========================================================================

import os

import filter_extraction

HERE = os.path.dirname(os.path.abspath(__file__))
REAL_EXTRACTION = os.path.join(
    HERE, "smoke_live2", "extraction_openai_gpt-oss-20b_s0-21da64d9.json")
REAL_BASELINES = [os.path.join(HERE, "smoke_live2", f"conflicts_baseline_run{i}.json")
                  for i in (1, 2, 3)]

real = pytest.mark.skipif(not os.path.exists(REAL_EXTRACTION),
                          reason="real artifacts not present")


def _ext(rules, unencoded=()):
    return {"section": "chain_of_command", "atoms": [],
            "rules": [dict(id=i, modality=m, act="x", tier=1)
                      for i, m in rules],
            "incompat": [], "exclusions": [],
            "unencoded": [{"focus_id": f, "reason": r} for f, r in unencoded]}


# -- B3: a baseline_only item gave no basis for the out-of-scope call -------

def test_encoding_status_labels_each_provision():
    """§7: `C_baseline \\ C_tool` conflates tool bug with out-of-scope, and the
    worksheet is supposed to force that call. It cannot be made without knowing
    whether the tool even encoded the two provisions."""
    ext = _ext([(A, "oblige"), (B, "forbid")], unencoded=[(C, "no clear act")])
    st = adjudicate.encoding_status(ext, rejected=[{"kind": "rule", "id": D,
                                                    "reason": "bad act atom"}])
    assert st[A]["state"] == "encoded"
    assert st[B]["state"] == "encoded"
    assert st[C]["state"] == "unencoded"
    assert "no clear act" in st[C]["detail"]
    assert st[D]["state"] == "rejected"
    assert "bad act atom" in st[D]["detail"]
    assert st[E]["state"] == "absent"


def test_worksheet_shows_encoding_status_for_baseline_only_items():
    ext = _ext([(A, "oblige")], unencoded=[(D, "truncated batch")])
    tool = [doc("tool", "t1", [])]
    base = [doc("baseline", "b1", [[A, D]])]
    m = delta.compute(tool, base, extraction=ext)
    ws = adjudicate.render_worksheet(m, inv_index(), tool, base, extraction=ext)
    assert "encoding status" in ws.lower()
    assert "unencoded" in ws
    assert "truncated batch" in ws


def test_worksheet_marks_an_item_the_tool_could_not_possibly_find():
    """Neither provision is in the encoding, so the tool could not have raised
    this pair whatever its logic. That must not be counted against it."""
    ext = _ext([(A, "oblige")], unencoded=[(C, "r1"), (D, "r2")])
    tool = [doc("tool", "t1", [])]
    base = [doc("baseline", "b1", [[C, D]])]
    m = delta.compute(tool, base, extraction=ext)
    ws = adjudicate.render_worksheet(m, inv_index(), tool, base, extraction=ext)
    assert "outside the encoding" in ws.lower()


def test_worksheet_marks_an_item_both_of_whose_provisions_are_encoded():
    """Both encoded: the tool *could* have found it, so a miss here is a real
    candidate defect rather than a coverage cost."""
    ext = _ext([(A, "oblige"), (B, "forbid")])
    tool = [doc("tool", "t1", [])]
    base = [doc("baseline", "b1", [[A, B]])]
    m = delta.compute(tool, base, extraction=ext)
    ws = adjudicate.render_worksheet(m, inv_index(), tool, base, extraction=ext)
    assert "both provisions are encoded" in ws.lower()


def test_worksheet_without_an_extraction_is_unchanged():
    """The status block is additive; the pre-existing call signature still
    renders exactly the same worksheet."""
    ext = _ext([(A, "oblige")])
    tool = [doc("tool", "t1", [])]
    base = [doc("baseline", "b1", [[A, D]])]
    m = delta.compute(tool, base, extraction=ext)
    ws = adjudicate.render_worksheet(m, inv_index(), tool, base)
    assert "encoding status" not in ws.lower()


def inv_index():
    return {r["id"]: r for r in (adjudicate._norm_row(x) for x in inv_rows())}


# -- stop rules on the real numbers ----------------------------------------

def test_stop_rule_uses_effective_coverage_not_the_claimed_one():
    """22 of 42 rules survive validation but the extraction claims 24. The
    coverage stop rule must key on what actually reached the solver."""
    m = {"coverage": {"coverage": 22 / 42, "coverage_claimed": 24 / 42},
         "baseline_self_agreement": 0.5}
    s = adjudicate.score([], m)
    r = s["stop_rules"]["coverage_below_70pct"]
    assert r["fired"] is True and r["value"] == pytest.approx(22 / 42)


@real
def test_real_worksheet_renders_and_scores_end_to_end(tmp_path):
    with open(REAL_EXTRACTION) as f:
        ext = json.load(f)
    filtered, rep = filter_extraction.filter_extraction(ext)
    base = [delta.load_conflicts(p) for p in REAL_BASELINES]
    tool = [{"source": "tool", "model": ext["model"], "run_id": ext["run_id"],
             "conflicts": []}]
    m = delta.compute(tool, base, extraction=ext,
                      rejected_rule_ids=[r["id"] for r in rep["rejected"]
                                         if r["kind"] == "rule"])
    inv = adjudicate.load_inventory(adjudicate.FOCUS_AREAS)
    ws = adjudicate.render_worksheet(m, inv, tool, base, extraction=ext,
                                     rejected=rep["rejected"])
    items = adjudicate.parse_worksheet(ws)
    assert len(items) == 6
    assert all(i["bucket"] == "baseline_only" for i in items)
    # every provision the baseline cited must resolve to a real inventory row
    assert "not found in inventory" not in ws
    # and every item must carry an encoding-status call
    assert ws.count("**Encoding status.**") == 6
    s = adjudicate.score(items, m)
    assert s["n_items"] == 6 and s["n_adjudicated"] == 0
    assert s["stop_rules"]["coverage_below_70pct"]["fired"] is True


# -- B3b: "absent" conflated out-of-design-scope with extraction failure ----

def test_non_conditional_provisions_are_not_reported_as_extraction_gaps():
    """§2: only the 42 *conditional* provisions are encodable. A baseline pair
    citing a `holistic` provision is out of scope by design --- calling it
    'absent from the extraction' reads as an extraction failure and would be
    counted against the tool. Real case: the baseline's most-repeated pair
    cites fa_0prn, which is holistic."""
    ext = _ext([(A, "oblige")])
    inv = {A: adjudicate._norm_row({"id": A, "quote": "q", "kind": "conditional"}),
           B: adjudicate._norm_row({"id": B, "quote": "q", "kind": "holistic"})}
    tool = [doc("tool", "t1", [])]
    base = [doc("baseline", "b1", [[A, B]])]
    m = delta.compute(tool, base, extraction=ext)
    ws = adjudicate.render_worksheet(m, inv, tool, base, extraction=ext)
    assert "holistic" in ws
    assert "not among the 42 conditional provisions" in ws
    assert "absent from the extraction" not in ws


def test_a_conditional_provision_missing_from_the_extraction_is_still_a_gap():
    ext = _ext([(A, "oblige")])
    inv = {A: adjudicate._norm_row({"id": A, "quote": "q", "kind": "conditional"}),
           B: adjudicate._norm_row({"id": B, "quote": "q", "kind": "conditional"})}
    tool = [doc("tool", "t1", [])]
    base = [doc("baseline", "b1", [[A, B]])]
    m = delta.compute(tool, base, extraction=ext)
    ws = adjudicate.render_worksheet(m, inv, tool, base, extraction=ext)
    assert "absent from the extraction" in ws


@real
def test_real_worksheet_separates_design_scope_from_extraction_gaps():
    with open(REAL_EXTRACTION) as f:
        ext = json.load(f)
    filtered, rep = filter_extraction.filter_extraction(ext)
    base = [delta.load_conflicts(p) for p in REAL_BASELINES]
    tool = [{"source": "tool", "run_id": ext["run_id"], "conflicts": []}]
    m = delta.compute(tool, base, extraction=ext)
    inv = adjudicate.load_inventory(adjudicate.FOCUS_AREAS)
    ws = adjudicate.render_worksheet(m, inv, tool, base, extraction=ext,
                                     rejected=rep["rejected"])
    # fa_0prn and fa_a9sh are holistic: out of the encodable set by design
    assert "not among the 42 conditional provisions" in ws
    assert "absent from the extraction" not in ws
