"""Pins for recurse_driver.py. Every guard is proven RED here (DEBUGGING_TIPS
S8): each test feeds the checker the defect it exists to catch, most of them
taken verbatim from failures the 2026-08-10 build actually produced."""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import recurse_driver as R  # noqa: E402


# ---------------------------------------------------------------- validators
def test_division_blank_line_gap_is_RED():
    # the c21/c23a/c23c failure class: a blank line owned by no child
    d = {"decision": "divide",
         "children": [{"span": [1, 10]}, {"span": [12, 20]}],
         "seed_vocabulary": [], "expected_cross_links": []}
    errs = R.validate_division(d, 1, 20)
    assert any("gap" in e for e in errs)


def test_division_unseeded_cross_link_is_RED():
    d = {"decision": "divide",
         "children": [{"span": [1, 10]}, {"span": [11, 20]}],
         "seed_vocabulary": [],
         "expected_cross_links": [{"name": "orphan_concept"}]}
    assert any("orphan_concept" in e for e in R.validate_division(d, 1, 20))


TOY = ["alpha line one", "the rule must hold", "gamma"]


def test_leaf_nonverbatim_quote_is_RED():
    g = {"nodes": [{"id": "n1", "establishes": "x", "needs": [], "provides": [],
                    "spans": [{"lines": [2, 2],
                               "quote": "the rule should hold"}]}],
         "uncovered": [{"lines": [1, 1]}, {"lines": [3, 3]}]}
    assert any("verbatim" in e for e in R.validate_leaf(g, 1, 3, TOY))


def test_leaf_bare_string_provides_is_RED():
    # the run-4 format regression: names without prose
    g = {"nodes": [{"id": "n1", "establishes": "x", "needs": [],
                    "provides": ["bare_name"],
                    "spans": [{"lines": [1, 3]}]}], "uncovered": []}
    assert any("name, prose" in e for e in R.validate_leaf(g, 1, 3, TOY))


def test_leaf_coverage_identity_is_RED():
    g = {"nodes": [{"id": "n1", "establishes": "x", "needs": [], "provides": [],
                    "spans": [{"lines": [1, 1]}]}], "uncovered": []}
    assert any("coverage identity" in e for e in R.validate_leaf(g, 1, 3, TOY))


# ------------------------------------------------------------- merge checker
def test_merge_loss_catches_the_historical_tier_case():
    """The exact n028/n008 loss: survivor lacks the retired 'No Authority'
    tier. Uses the preserved build artifacts when present; a hand-copied
    excerpt otherwise, so the pin never silently stops testing (S8a)."""
    surv = ("The authority hierarchy ranked from highest to lowest: Root > "
            "System > Developer > User > Guideline.")
    c1 = os.path.join(HERE, "recurse", "c1", "graph.json")
    if os.path.exists(c1):
        n28 = next(n for n in json.load(open(c1))["nodes"]
                   if n["id"] == "L1-170_n028")
        surv = n28["establishes"]
    retired = ("The authority levels are ranked: (1) Root, (2) System, "
               "(3) Developer, (4) User, (5) Guideline; (6) No Authority is "
               "given to assistant and tool messages.")
    assert any("No Authority" in el for el in R.merge_loss(surv, retired))


def test_merge_loss_passes_when_content_absorbed():
    surv = ("Ranked Root > System > Developer > User > Guideline, with a "
            "sixth tier No Authority for assistant and tool messages.")
    retired = "(6) No Authority: assistant and tool messages"
    assert R.merge_loss(surv, retired) == []


# -------------------------------------------------------------- decisions
def _nodes():
    return [
        {"id": "a", "establishes": "provider establishes X",
         "needs": [], "provides": [{"name": "x", "prose": "the X concept"}],
         "spans": [{"lines": [1, 1]}]},
        {"id": "b", "establishes": "needer uses X",
         "needs": [{"name": "x_alias", "prose": "the X concept"}],
         "provides": [], "spans": [{"lines": [2, 2]}]},
    ]


def test_resolution_rename_to_provided_name_applies():
    nodes = _nodes()
    provides = {"x": ["a"]}
    log, errs = R.apply_decisions(
        nodes, {"resolutions": [{"needer": "b", "name": "x_alias",
                                 "rename_to": "x"}]}, provides)
    assert not errs and nodes[1]["needs"][0]["name"] == "x"


def test_resolution_to_unprovided_name_is_RED():
    nodes = _nodes()
    log, errs = R.apply_decisions(
        nodes, {"resolutions": [{"needer": "b", "name": "x_alias",
                                 "rename_to": "phantom"}]}, {"x": ["a"]})
    assert errs


def test_merge_that_loses_content_is_RED():
    nodes = [
        {"id": "s", "establishes": "the short claim", "needs": [],
         "provides": [], "spans": [{"lines": [1, 1]}]},
        {"id": "r", "establishes": "the short claim plus the Vital Tier item",
         "needs": [], "provides": [], "spans": [{"lines": [2, 2]}]},
    ]
    log, errs = R.apply_decisions(
        nodes, {"merges": [{"survivor": "s", "retired": "r"}]}, {})
    assert errs and len(nodes) == 2  # retired node NOT removed on failure


# -------------------------------------------------------------- line count
def test_unterminated_final_line_is_counted(tmp_path):
    # the 4691-vs-4692 lesson: last line without trailing newline still counts
    p = tmp_path / "d.md"
    p.write_bytes(b"one\ntwo\n~~~")
    assert len(R.load_doc(str(p))) == 3


# -------------------------------------------------------------- end to end
def test_mock_end_to_end(tmp_path):
    toy = os.path.join(HERE, "toy_doc.md")
    replies = json.load(open(os.path.join(HERE, "mock_replies.json")))
    lines = R.load_doc(toy)
    drv = R.Driver({"leaf_max_lines": 15}, R.MockClient(replies), lines,
                   str(tmp_path))
    g = drv.build(1, len(lines), [], str(tmp_path))
    assert len(g["nodes"]) == 10
    # the cross-child edge resolves mechanically: needer name has a provider
    provs = {R.nm(p) for n in g["nodes"] for p in n.get("provides", [])}
    assert "clearance_order" in provs
    dang = {R.nm(d) for n in g["nodes"] for d in n.get("needs", [])
            if R.nm(d) not in provs}
    assert dang == {"house_rules"}          # the honest external survives
    # resumability: a second build with a client that would fail loudly
    class Boom:
        calls = 0

        def complete(self, *a):
            raise AssertionError("resume must not re-call the model")
        complete_messages = complete
    g2 = R.Driver({"leaf_max_lines": 15}, Boom(), lines,
                  str(tmp_path)).build(1, len(lines), [], str(tmp_path))
    assert len(g2["nodes"]) == 10


# ------------------------- review-driven pins (adversarial review 2026-08-10)
def test_empty_child_span_is_RED():                                    # F15
    d = {"decision": "divide",
         "children": [{"span": [1, 10]}, {"span": [11, 10]}],
         "seed_vocabulary": [], "expected_cross_links": []}
    assert any("empty or outside" in e for e in R.validate_division(d, 1, 10))


def test_dropped_inherited_seed_is_RED():                              # F17
    d = {"decision": "divide",
         "children": [{"span": [1, 10]}, {"span": [11, 20]}],
         "seed_vocabulary": [], "expected_cross_links": []}
    inherited = [{"name": "x", "prose": "p", "established_around": [3, 5]}]
    assert any("dropped" in e
               for e in R.validate_division(d, 1, 20, inherited))


def test_provenance_violation_is_RED():                                # F17b
    d = {"decision": "divide",
         "children": [{"span": [1, 10]}, {"span": [11, 20]}],
         "seed_vocabulary": [{"name": "x", "prose": "p",
                              "established_around": [3, 5]}],
         "expected_cross_links": [{"name": "x", "provides_side_child": 2,
                                   "needs_side_child": 1}]}
    assert any("does not contain established_around" in e
               for e in R.validate_division(d, 1, 20))


def test_merge_unions_needs():                                         # F4
    nodes = [
        {"id": "s", "establishes": "claim", "needs": [], "provides": [],
         "spans": [{"lines": [1, 1]}]},
        {"id": "r", "establishes": "claim", "provides": [],
         "needs": [{"name": "k", "prose": "the k concept"}],
         "spans": [{"lines": [2, 2]}]},
    ]
    log, errs = R.apply_decisions(
        nodes, {"merges": [{"survivor": "s", "retired": "r"}]}, {})
    assert not errs and [R.nm(d) for d in nodes[0]["needs"]] == ["k"]


def test_structure_node_out_of_span_is_RED():                          # F5
    nodes = []
    sn = {"id": "L1-3_x", "establishes": "e", "needs": ["bare"],
          "provides": [], "spans": [{"lines": [999, 9999]}]}
    log, errs = R.apply_decisions(nodes, {"structure_nodes": [sn]}, {},
                                  1, 3, TOY)
    assert errs and not nodes


def test_empty_nodes_leaf_is_RED():                                    # F6
    g = {"nodes": [], "uncovered": [{"lines": [1, 3]}]}
    assert any("empty" in e for e in R.validate_leaf(g, 1, 3, TOY))


def test_out_of_span_uncovered_is_RED():                               # F6
    g = {"nodes": [{"id": "L1-3_n1", "establishes": "x", "needs": [],
                    "provides": [], "spans": [{"lines": [1, 3]}]}],
         "uncovered": [{"lines": [1, 99]}]}
    assert any("outside span" in e for e in R.validate_leaf(g, 1, 3, TOY))


def test_wrong_id_prefix_is_RED():                                     # F18
    g = {"nodes": [{"id": "n1", "establishes": "x", "needs": [],
                    "provides": [], "spans": [{"lines": [1, 3]}]}],
         "uncovered": []}
    assert any("must start with" in e for e in R.validate_leaf(g, 1, 3, TOY))


def test_noop_resolution_is_RED():                                     # F20
    nodes = [{"id": "a", "establishes": "e", "provides": [
                  {"name": "x", "prose": "p"}],
              "needs": [], "spans": [{"lines": [1, 1]}]},
             {"id": "b", "establishes": "e", "provides": [],
              "needs": [{"name": "real", "prose": "p"}],
              "spans": [{"lines": [2, 2]}]}]
    log, errs = R.apply_decisions(
        nodes, {"resolutions": [{"needer": "b", "name": "typo",
                                 "rename_to": "x"}]}, {"x": ["a"]})
    assert any("matched no needs entry" in e for e in errs)


def test_validator_exception_becomes_repairable(tmp_path):             # F12
    lines = ["a", "b", "c"]
    bad = {"decision": "divide", "children": [{"span": "1-3"}],
           "seed_vocabulary": [], "expected_cross_links": []}
    good = {"decision": "leaf"}
    drv = R.Driver({}, R.MockClient([bad, good]), lines, str(tmp_path))
    d = drv.call("dispatch", lambda o: R.validate_division(o, 1, 3))
    assert d == good        # first reply's bad shape repaired, not crashed


def test_atomic_write_replaces_and_cleans(tmp_path):                   # F13
    p = str(tmp_path / "x.json")
    R.write_json(p, {"v": 1})
    R.write_json(p, {"v": 2})
    assert json.load(open(p)) == {"v": 2}
    assert not os.path.exists(p + ".tmp")


def test_cross_sibling_id_collision_is_RED():                          # F18
    kids = [{"nodes": [{"id": "dup", "establishes": "a", "needs": [],
                        "provides": [], "spans": [{"lines": [1, 1]}]}],
             "uncovered": []},
            {"nodes": [{"id": "dup", "establishes": "b", "needs": [],
                        "provides": [], "spans": [{"lines": [2, 2]}]}],
             "uncovered": []}]
    nodes, *_ = R.unwind_mechanics(kids)
    log, errs = R.apply_decisions(nodes, {}, {})
    assert any("duplicate node id" in e for e in errs)


# ------------------------- json_schema forcing (2026-08-10, Matt's request)
def test_phase_calls_carry_their_reply_schema(tmp_path):
    """Each phase must SET the schema; a client left on json_object gets the
    weak forcing back silently, which is the defect this pins."""
    seen = []

    class Spy(R.MockClient):
        reply_schema = None
        _schema_rejected = False

        def complete(self, system, user):
            seen.append(self.reply_schema and self.reply_schema[0])
            return super().complete(system, user)
        def complete_messages(self, system, messages):
            return self.complete(system, "")

    toy = os.path.join(HERE, "toy_doc.md")
    replies = json.load(open(os.path.join(HERE, "mock_replies.json")))
    lines = R.load_doc(toy)
    drv = R.Driver({"leaf_max_lines": 15}, Spy(replies), lines, str(tmp_path))
    drv.build(1, len(lines), [], str(tmp_path))
    assert "division" in seen and "leaf_graph" in seen, seen
    assert "unwind_decisions" in seen, seen
    assert None not in seen, "a phase call went out with NO reply schema"


def test_body_carries_json_schema_and_downgrades_on_rejection(monkeypatch):
    monkeypatch.setattr(R.T.Client, "_body",
                        lambda self, s, u: {"messages": []}, raising=True)
    c = R.GraphClient.__new__(R.GraphClient)
    c.reply_schema = ("division", R.DIVISION_SCHEMA)
    c._schema_rejected = False
    b = c._body("s", "u")
    assert b["response_format"]["type"] == "json_schema"
    assert "decision" in b["response_format"]["json_schema"]["schema"][
        "required"]
    c._schema_rejected = True
    b2 = c._body("s", "u")
    assert b2["response_format"] == {"type": "json_object"}


def test_schemas_are_serializable_and_typed():
    for name, sch in [("division", R.DIVISION_SCHEMA),
                      ("leaf", R.LEAF_SCHEMA), ("unwind", R.UNWIND_SCHEMA)]:
        json.dumps(sch)
        assert sch["type"] == "object", name
    # the span type that bit us (span as a string "1-3") is excluded by type
    span = R.DIVISION_SCHEMA["properties"]["children"]["items"][
        "properties"]["span"]
    assert span["items"]["type"] == "integer"


def test_division_schema_states_the_child_cardinality():
    """Root probe 2026-08-10: DeepSeek returned 47- and 191-child divisions
    against prose saying 2-3. The schema is the layer that can refuse."""
    kids = R.DIVISION_SCHEMA["properties"]["children"]
    assert kids["minItems"] == 2 and kids["maxItems"] == 3


def test_whole_document_leaf_dodge_is_RED():
    """Root re-probe 2026-08-10: a 4692-line span declared 'leaf' validated
    clean and would have sent Phase L a whole document."""
    errs = R.validate_division({"decision": "leaf"}, 1, 4692)
    assert any("must divide" in e for e in errs)
    # near leaf scale the declaration stays legitimate
    assert R.validate_division({"decision": "leaf"}, 1, 400) == []


# ---------------------------------------------------- caching (Matt, 2026-08-10)
def test_system_prompt_is_byte_identical_across_all_phases(tmp_path):
    """The provider's prefix cache only covers the system prompt if every
    call sends EXACTLY the same bytes — one reordered word forfeits the ~50x
    cached-input discount on every subsequent call. Phases must vary the
    USER turn only."""
    systems, users = [], []

    class Spy(R.MockClient):
        def complete(self, system, user):
            systems.append(system); users.append(user)
            return super().complete(system, user)
        def complete_messages(self, system, messages):
            systems.append(system)
            users.append(messages[0]["content"])
            return super().complete(system, "")

    toy = os.path.join(HERE, "toy_doc.md")
    replies = json.load(open(os.path.join(HERE, "mock_replies.json")))
    lines = R.load_doc(toy)
    drv = R.Driver({"leaf_max_lines": 15}, Spy(replies), lines, str(tmp_path))
    drv.build(1, len(lines), [], str(tmp_path))
    assert len(systems) >= 3, "expected calls across phases"
    assert len(set(systems)) == 1, "system prompt varies across calls -- " \
        "the prefix cache is forfeited"
    assert systems[0] == open(os.path.join(HERE, "RECURSE_PROMPT.md")).read(), \
        "system prompt is not the brief verbatim"
    assert len(set(users)) == len(users), "two calls sent identical user " \
        "turns -- phases are not distinguished where they should be"


def test_cache_tally_counts_hits_and_misses_from_usage():
    """review F9: the tally must read the CACHED token count from the
    envelope usage, not infer it -- a dead tally reports 0% forever and the
    cost model silently overstates."""
    lines = ["a"]
    drv = R.Driver({}, R.MockClient([]), lines, ".")
    drv._tally({"usage": {"prompt_tokens": 1000, "cached_input_tokens": 900}})
    drv._tally({"usage": {"prompt_tokens": 500, "cached_input_tokens": 0}})
    assert drv.cache_hits == 900 and drv.cache_misses == 600
    # an envelope with NO usage must not crash and must not fabricate hits
    drv._tally({})
    assert drv.cache_hits == 900


def test_provenance_autofix_repairs_the_live_root_failure():
    """2026-08-10 build abort: provider child did not contain
    established_around. The correct child is derivable, so code fixes it."""
    d = {"decision": "divide",
         "children": [{"span": [1, 170]}, {"span": [171, 800]},
                      {"span": [801, 900]}],
         "seed_vocabulary": [{"name": "applicable_instruction", "prose": "p",
                              "established_around": [181, 195]}],
         "expected_cross_links": [{"name": "applicable_instruction",
                                   "provides_side_child": 1,
                                   "needs_side_child": 3}]}
    R.autofix_division(d)
    assert d["expected_cross_links"][0]["provides_side_child"] == 2
    assert d["driver_autofixes"]
    assert R.validate_division(d, 1, 900) == []
    # a seed whose established_around sits in NO child is untouched and
    # still fails validation (autofix must not mask a real defect)
    d2 = {"decision": "divide",
          "children": [{"span": [1, 170]}, {"span": [171, 900]}],
          "seed_vocabulary": [{"name": "x", "prose": "p",
                               "established_around": [950, 960]}],
          "expected_cross_links": [{"name": "x", "provides_side_child": 1,
                                    "needs_side_child": 2}]}
    R.autofix_division(d2)
    assert "driver_autofixes" not in d2


def test_truncated_draw_is_resampled_not_fatal(tmp_path):
    """2026-08-10: the root dispatch truncated twice at 32K and completed at
    8K on another draw -- truncation is a bad draw, not a bad prompt."""
    class Flaky:
        calls = 0
        def complete(self, system, user):
            Flaky.calls += 1
            if Flaky.calls == 1:
                raise R.T.ProviderError("completion was TRUNCATED "
                                        "(finish_reason=length). ...")
            if Flaky.calls == 2:
                raise R.T.ProviderError("HTTP 503: service unavailable")
            return {"text": json.dumps({"decision": "leaf"}), "usage": {}}
        complete_messages = complete
    drv = R.Driver({}, Flaky(), ["a"], str(tmp_path))
    d = drv.call("dispatch", lambda o: [])
    assert d == {"decision": "leaf"} and Flaky.calls == 3


def test_contiguity_autofix_extends_but_never_shrinks():
    """2026-08-11 live: last child ended 4089 of 4692 through 4 repair
    rounds. Extending is safe (oversized children re-divide next level);
    overlaps must stay errors."""
    d = {"decision": "divide", "_span_lo": 1, "_span_hi": 4692,
         "children": [{"span": [10, 2000]}, {"span": [2005, 4089]}],
         "seed_vocabulary": [], "expected_cross_links": []}
    R.autofix_division(d)
    assert d["children"][0]["span"] == [1, 2004]
    assert d["children"][1]["span"] == [2005, 4692]
    assert len(d["driver_autofixes"]) == 3
    assert R.validate_division(d, 1, 4692) == []
    # overlap is untouched and still fails
    d2 = {"decision": "divide", "_span_lo": 1, "_span_hi": 100,
          "children": [{"span": [1, 60]}, {"span": [50, 100]}],
          "seed_vocabulary": [], "expected_cross_links": []}
    R.autofix_division(d2)
    assert d2["children"][0]["span"] == [1, 60]
    assert any("gap/overlap" in e for e in R.validate_division(d2, 1, 100))


def test_degenerate_duplicate_nodes_are_deduped_and_density_bounced():
    """2026-08-11: 969 byte-identical nodes under distinct ids passed every
    id-based check. Dedupe removes exact copies; the density band catches
    non-identical spam."""
    node = {"id": "L1-100_n001", "establishes": "the one claim",
            "needs": [], "provides": [], "spans": [{"lines": [3, 3]}]}
    g = {"nodes": [dict(node, id=f"L1-100_n{i:03d}") for i in range(200)],
         "uncovered": [{"lines": [1, 2]}, {"lines": [4, 100]}]}
    removed = R.dedupe_nodes(g)
    assert removed == 199 and len(g["nodes"]) == 1
    # non-identical spam: distinct establishes, still absurd density
    g2 = {"nodes": [{"id": f"L1-100_n{i:03d}", "establishes": f"claim {i}",
                     "needs": [], "provides": [],
                     "spans": [{"lines": [1 + i % 100, 1 + i % 100]}]}
                    for i in range(90)],
          "uncovered": []}
    errs = R.validate_leaf(g2, 1, 100, ["text"] * 100)
    assert any("density" in e for e in errs)


def test_per_dispatch_budget_stops_expensive_redraws(tmp_path):
    """2026-08-11: one leaf burned ~$0.35 in redraws with only the aggregate
    ceiling watching. The budget is per-call(), measured, and loud."""
    class Pricey(R.MockClient):
        spent_usd = 0.0
        def complete(self, system, user):
            Pricey.spent_usd = self.spent_usd = self.spent_usd + 0.31
            return {"text": "not json {", "usage": {}}
        complete_messages = complete
    drv = R.Driver({"per_dispatch_usd": 0.30}, Pricey([]), ["a"],
                   str(tmp_path))
    with pytest.raises(R.T.Phase1Error) as exc:
        drv.call("dispatch", lambda o: [])
    assert "spend budget" in str(exc.value)


def test_driver_layer_review_guards():
    """Pins for driver_layer_review.md F1/F2/F4/F5/F7 (probe-demonstrated)."""
    # F1: self-merge is RED, node survives
    nodes = [{"id": "a", "establishes": "e", "needs": [], "provides": [],
              "spans": [{"lines": [1, 1]}]}]
    log, errs = R.apply_decisions(nodes, {"merges": [
        {"survivor": "a", "retired": "a"}]}, {})
    assert errs and len(nodes) == 1
    # F2: an all-lowercase claim vanishing in a merge is caught
    assert R.merge_loss("the assistant maintains a warm tone.",
                        "escalation to a human reviewer happens whenever "
                        "verification fails")
    # F4: duplicate structure nodes collide
    sn = {"id": "L1-3_x", "establishes": "e", "needs": [], "provides": [],
          "spans": [{"lines": [1, 2]}]}
    nodes2 = []
    log, errs = R.apply_decisions(nodes2, {"structure_nodes": [sn, dict(sn)]},
                                  {}, 1, 3, ["a", "b", "c"])
    assert any("duplicate" in e for e in errs)
    # F5: self-satisfying resolution is RED
    nodes3 = [{"id": "b", "establishes": "e",
               "provides": [{"name": "x", "prose": "p"}],
               "needs": [{"name": "y", "prose": "p"}],
               "spans": [{"lines": [1, 1]}]}]
    log, errs = R.apply_decisions(nodes3, {"resolutions": [
        {"needer": "b", "name": "y", "rename_to": "x"}]}, {"x": ["b"]})
    # promoted to autofix-drop 2026-08-11: not an error, but never applied
    assert not errs
    assert any("DROPPED self-satisfying" in l for l in log)
    assert nodes3[0]["needs"][0]["name"] == "y"    # need untouched, dangling
    # F7: out-of-range cross-link child index is RED
    d = {"decision": "divide",
         "children": [{"span": [1, 10]}, {"span": [11, 20]}],
         "seed_vocabulary": [{"name": "x", "prose": "p"}],
         "expected_cross_links": [{"name": "x", "provides_side_child": 7,
                                   "needs_side_child": 1}]}
    assert any("outside 1..2" in e for e in R.validate_division(d, 1, 20))
    # F3a: a coined seed established outside the span is RED
    d2 = {"decision": "divide",
          "children": [{"span": [1, 10]}, {"span": [11, 20]}],
          "seed_vocabulary": [{"name": "z", "prose": "p",
                               "established_around": [500, 505]}],
          "expected_cross_links": []}
    assert any("cannot see" in e for e in R.validate_division(d2, 1, 20))

# ---------------- ds3 determinization flags (queued 2026-08-11, default OFF)
def _spy_build(cfg, out_dir):
    """Mock e2e with prompt capture; returns (user_turns, final_graph)."""
    users = []

    class Spy(R.MockClient):
        def complete(self, system, user):
            users.append(user)
            return super().complete(system, user)

        def complete_messages(self, system, messages):
            users.append(messages[0]["content"])
            return super().complete(system, "")

    toy = os.path.join(HERE, "toy_doc.md")
    replies = json.load(open(os.path.join(HERE, "mock_replies.json")))
    lines = R.load_doc(toy)
    drv = R.Driver(cfg, Spy(replies), lines, str(out_dir))
    g = drv.build(1, len(lines), [], str(out_dir))
    return users, g


def test_derive_uncovered_flag_off_is_byte_identical(tmp_path):
    """Flag absent and flag false must both be the pinned ds2 path: same
    prompt bytes, same artifact bytes, no derive wording anywhere."""
    base_users, _ = _spy_build({"leaf_max_lines": 15}, tmp_path / "a")
    off_users, _ = _spy_build({"leaf_max_lines": 15,
                               "derive_uncovered": False}, tmp_path / "b")
    assert off_users == base_users
    assert (open(tmp_path / "a" / "graph.json", "rb").read()
            == open(tmp_path / "b" / "graph.json", "rb").read())
    assert not any("do NOT emit `uncovered`" in u for u in base_users)


def test_rename_candidates_flag_off_is_byte_identical(tmp_path):
    base_users, _ = _spy_build({"leaf_max_lines": 15}, tmp_path / "a")
    off_users, _ = _spy_build({"leaf_max_lines": 15,
                               "rename_candidates": False}, tmp_path / "b")
    assert off_users == base_users
    assert (open(tmp_path / "a" / "graph.json", "rb").read()
            == open(tmp_path / "b" / "graph.json", "rb").read())
    assert not any("CANDIDATES (lexical suggestions ONLY" in u
                   for u in base_users)


DS3_LINES = [
    "# Access Rules",          # L1 heading
    "",                        # L2 blank
    "Staff must sign in.",     # L3 content, covered
    "---",                     # L4 horizontal rule
    "```",                     # L5 fence
    "```",                     # L6 fence
    "Visitors must wait.",     # L7 content
]


def _ds3_leaf(cover_l7=False, jcs=()):
    spans = [{"lines": [3, 3]}] + ([{"lines": [7, 7]}] if cover_l7 else [])
    return {"nodes": [{"id": "L1-7_n001", "establishes": "staff sign in",
                       "needs": [], "provides": [], "spans": spans}],
            "judgment_calls": list(jcs)}


def test_derived_uncovered_labels_formatting_runs_as_ranges():
    g = _ds3_leaf(cover_l7=True)
    assert R.validate_leaf(g, 1, 7, DS3_LINES, derive_uncovered=True) == []
    assert g["uncovered"] == [
        {"lines": [1, 1], "reason": "heading"},
        {"lines": [2, 2], "reason": "blank"},
        {"lines": [4, 4], "reason": "horizontal-rule"},
        {"lines": [5, 6], "reason": "fence"},
    ]


def test_derived_uncovered_content_residue_is_RED_with_cover_or_explain():
    # single-line residue is now RECORDED not blocked (2026-08-12
    # containment ruling: <=2 record honestly, 3+ hard-fail); this pin's
    # cover-or-explain claim is preserved via the discharge path below and
    # the 3+ case is pinned in test_tiny_unclaimed_residue_records_not_blocks
    g = _ds3_leaf(cover_l7=False)
    errs = R.validate_leaf(g, 1, 7, DS3_LINES, derive_uncovered=True)
    assert errs == []
    assert any(u.get("reason", "").startswith("unclaimed-content")
               for u in g["uncovered"])
    # the coverage-identity class is GONE when the flag is on
    assert not any("coverage identity" in e for e in errs)
    # a judgment_calls entry naming the line discharges the residue
    g2 = _ds3_leaf(cover_l7=False,
                   jcs=["L0007: sign-off aside, establishes nothing"])
    assert R.validate_leaf(g2, 1, 7, DS3_LINES, derive_uncovered=True) == []
    assert {"lines": [7, 7], "reason": "explained in judgment_calls"} \
        in g2["uncovered"]


def test_rename_candidates_ranking_top3_ordered():
    def prov(pid, name, prose):
        return {"id": pid, "establishes": "e", "needs": [],
                "provides": [{"name": name, "prose": prose}],
                "spans": [{"lines": [1, 1]}]}
    nodes = [
        prov("p1", "clearance_order",
             "the clearance levels ranked from highest to lowest"),
        prov("p2", "room_entry_rule",
             "who may enter a room given clearance levels"),
        prov("p3", "founding_fact", "the year the archive was founded"),
        prov("p4", "level_list", "the list of levels"),
        prov("p5", "top_tier", "highest tier definition"),
    ]
    dangling = [{"needer": "x", "name": "levels",
                 "prose": "ordering of clearance levels from highest "
                          "to lowest"}]
    table = R.rename_candidates(dangling, nodes)
    assert table[0]["needer"] == "x" and table[0]["name"] == "levels"
    names = [c["name"] for c in table[0]["candidates"]]
    # jaccard: clearance_order .714 > room_entry_rule .222 > level_list .143
    # > top_tier .125 (cut by top-3); founding_fact overlaps nothing
    assert names == ["clearance_order", "room_entry_rule", "level_list"]
    scores = [c["overlap"] for c in table[0]["candidates"]]
    assert scores == sorted(scores, reverse=True) and scores[0] > scores[-1]
    assert "founding_fact" not in names and "top_tier" not in names


def test_rename_candidates_appear_in_unwind_prompt_when_on(tmp_path):
    users, g = _spy_build({"leaf_max_lines": 15, "rename_candidates": True},
                          tmp_path)
    unwinds = [u for u in users if "Phase: U" in u]
    assert unwinds, "toy build must reach Phase U"
    assert any("CANDIDATES (lexical suggestions ONLY" in u
               for u in unwinds)
    # prompt-only change: the built graph is unchanged
    assert len(g["nodes"]) == 10


def test_leaf_schema_grammar_caps_the_loop():
    """Matt's format-level question 2026-08-11: the density band lives in
    the GRAMMAR too, so a repetition loop cannot emit node N+1."""
    name, sch = R.leaf_schema(1542, 1800)
    assert sch["properties"]["nodes"]["maxItems"] == int(0.7 * 259)
    # tiny spans keep the +8 floor
    _, sch2 = R.leaf_schema(1, 5)
    assert sch2["properties"]["nodes"]["maxItems"] == 8
    # the shared extra is the single source (drift killer)
    assert "cross-reference" in R.leaf_extra(1, 5)


def test_transcript_continuity_resumes_the_divider(tmp_path):
    """Matt's architecture: same instance divides then links. The unwind
    request must carry [D-user, D-reply, U-user] when the flag is on."""
    seen = []

    class Spy(R.MockClient):
        def complete_messages(self, system, messages):
            seen.append(messages)
            return super().complete(system, "")
    toy = os.path.join(HERE, "toy_doc.md")
    replies = json.load(open(os.path.join(HERE, "mock_replies.json")))
    lines = R.load_doc(toy)
    drv = R.Driver({"leaf_max_lines": 15, "transcript_continuity": True},
                   Spy(replies), lines, str(tmp_path))
    drv.build(1, len(lines), [], str(tmp_path))
    tri = [m for m in seen if len(m) >= 3]
    assert tri, "no unwind carried the divider transcript"
    assert tri[0][0]["content"].startswith("YOUR DISPATCH\nPhase: D")
    assert json.loads(tri[0][1]["content"])["decision"] == "divide"
    assert "Phase: U" in tri[0][2]["content"]


def test_provided_elsewhere_cross_link_is_dropped_not_errored():
    """ds3 live: provides_side_child 0 for an inherited out-of-span seed =
    the model saying 'provided by neither child'. Correct encoding is
    absence; the entry drops, the need dangles and escalates."""
    d = {"decision": "divide", "_span_lo": 100, "_span_hi": 200,
         "children": [{"span": [100, 150]}, {"span": [151, 200]}],
         "seed_vocabulary": [{"name": "chain_of_command", "prose": "p",
                              "established_around": [69, 101]}],
         "expected_cross_links": [{"name": "chain_of_command",
                                   "provides_side_child": 0,
                                   "needs_side_child": 2}]}
    R.autofix_division(d)
    assert R.validate_division(d, 100, 200,
        inherited=[{"name": "chain_of_command", "prose": "p",
                    "established_around": [69, 101]}]) == []
    assert d["expected_cross_links"] == []
    assert any("provided-elsewhere" in a for a in d["driver_autofixes"])


def test_index_zero_cross_link_drops_even_without_seed_metadata():
    """ds3 second strike: the inherited seed was absent from the division's
    own vocabulary, so the ea-gated drop never fired. Index 0 is
    unambiguous regardless of metadata."""
    d = {"decision": "divide", "_span_lo": 100, "_span_hi": 200,
         "children": [{"span": [100, 150]}, {"span": [151, 200]}],
         "seed_vocabulary": [],
         "expected_cross_links": [{"name": "chain_of_command",
                                   "provides_side_child": 0,
                                   "needs_side_child": 2}]}
    R.autofix_division(d)
    assert R.validate_division(d, 100, 200) == []
    assert d["expected_cross_links"] == []   # filtered at validation


def test_unwind_schema_is_grammar_capped():
    """2026-08-11 (Matt): the unwind was the last unbounded reply shape."""
    name, sch = R.unwind_schema(7, 100)
    p = sch["properties"]
    assert p["resolutions"]["maxItems"] == 7
    assert p["judgment_calls"]["maxItems"] == 12
    assert p["merges"]["maxItems"] == 50


def test_unwind_prompt_carries_the_size_contract(tmp_path):
    """2026-08-11 (Matt): grammar caps contain damage; the PROMPT must
    prevent the state. Point-of-action placement is the pattern that has
    worked every time this campaign."""
    seen = []

    class Spy(R.MockClient):
        def complete(self, system, user):
            seen.append(user); return super().complete(system, user)
        def complete_messages(self, system, messages):
            seen.append(messages[-1]["content"])
            return super().complete(system, "")
    toy = os.path.join(HERE, "toy_doc.md")
    replies = json.load(open(os.path.join(HERE, "mock_replies.json")))
    lines = R.load_doc(toy)
    drv = R.Driver({"leaf_max_lines": 15}, Spy(replies), lines, str(tmp_path))
    drv.build(1, len(lines), [], str(tmp_path))
    u = [x for x in seen if "Phase: U" in x]
    assert u and all("REPLY SIZE CONTRACT" in x for x in u)


def test_per_phase_output_caps_are_set(monkeypatch):
    """Matt 2026-08-11: fail-and-fix beats burn-and-wait."""
    monkeypatch.setattr(R.T.Client, "_body",
                        lambda self, s, u: {"messages": []}, raising=True)
    c = R.GraphClient.__new__(R.GraphClient)
    c.reply_schema = None
    c._schema_rejected = False
    c.max_tokens_override = 8192
    assert c._body("s", "u")["max_tokens"] == 8192


def test_verified_fixes_are_integrated(tmp_path):
    """2026-08-11: authority convention lives in the shared leaf extra;
    the resolution pass runs post-build and resolves via rename."""
    assert "AUTHORITY CONVENTION" in R.leaf_extra(1, 100)
    assert "per-section coinage" in R.leaf_extra(1, 100)
    # resolution pass: a mock reply resolves the dangling
    g = {"nodes": [
        {"id": "a", "establishes": "provider", "needs": [],
         "provides": [{"name": "real_name", "prose": "the concept"}],
         "spans": [{"lines": [1, 1]}]},
        {"id": "b", "establishes": "needer",
         "needs": [{"name": "other_name", "prose": "the concept"}],
         "provides": [], "spans": [{"lines": [2, 2]}]}]}
    reply = {"resolutions": [{"needer": "b", "name": "other_name",
                              "rename_to": "real_name"}],
             "merges": [], "structure_nodes": [], "judgment_calls": []}
    drv = R.Driver({}, R.MockClient([reply]), ["x", "y"], str(tmp_path))
    g2 = R.run_resolution_pass(drv, g, str(tmp_path))
    assert g2["nodes"][1]["needs"][0]["name"] == "real_name"
    assert os.path.exists(os.path.join(str(tmp_path),
                                       "root_graph.pre_resolution.json"))


def test_d6_stage1_overflow_classifier():
    """D6 bisect stage 1: dense vs malfunction, pinned on the REAL 969-dup
    reply shape and a synthetic clean-dense reply."""
    dup = "".join(f'{{"id": "L1-100_n{i:03d}", "establishes": "The assistant '
                  f'should not provide harmful info"}}' for i in range(200))
    assert R.classify_cap_overflow(dup) == "malfunction"
    dense = "".join(f'{{"id": "L1-100_n{i:03d}", "establishes": "claim '
                    f'number {i} about a distinct topic"}}'
                    for i in range(120))
    assert R.classify_cap_overflow(dense) == "dense"
    assert R.classify_cap_overflow("garbage {{{") == "malfunction"


def test_division_schema_requires_the_structural_fields():
    """ds4 2026-08-12: a lawful omission of `children` under enforced
    grammar produced complete divisions with no children."""
    req = set(R.DIVISION_SCHEMA["required"])
    assert {"decision", "children", "seed_vocabulary",
            "expected_cross_links"} <= req


def test_admonition_marker_is_formatting():
    """ds4 2026-08-12: `!!! meta "Commentary"` is a structural marker."""
    assert R.formatting_reason('!!! meta "Commentary"') == "admonition-marker"
    assert R.formatting_reason('    The commentary text itself.') is None
    assert R.formatting_reason('<comparison>') == "example-markup"
    assert R.formatting_reason('</assistant>') == "example-markup"
    assert R.formatting_reason('<assistant> hello there') is None
    # prerun review F1: attribute-carrying tags (4 in the document)
    assert R.formatting_reason('<comparison min_relevant="1">') \
        == "example-markup"
    assert R.formatting_reason('<br/>') == "example-markup"


def test_dropped_inherited_seed_is_restored_by_carriage_autofix():
    """ds4 2026-08-12: carriage is copying known data through -- autofix."""
    inh = [{"name": "avoid_errors", "prose": "p",
            "established_around": [3150, 3150]}]
    d = {"decision": "divide", "_span_lo": 3000, "_span_hi": 3400,
         "children": [{"span": [3000, 3200]}, {"span": [3201, 3400]}],
         "seed_vocabulary": [], "expected_cross_links": []}
    R.autofix_division(d, inh)
    assert R.validate_division(d, 3000, 3400, inherited=inh) == []
    assert any(s["name"] == "avoid_errors" for s in d["seed_vocabulary"])


def test_tiny_unclaimed_residue_records_not_blocks():
    """ds4 2026-08-12: <=2 unclaimed content lines record honestly as
    uncovered; 3+ stay a hard failure."""
    lines = ["content %d" % i for i in range(1, 11)]
    def leaf(cover_to):
        return {"nodes": [{"id": "L1-10_n001", "establishes": "e",
                           "needs": [], "provides": [],
                           "spans": [{"lines": [1, cover_to]}]}],
                "uncovered": []}
    g = leaf(8)     # 2 residue lines
    errs = R.validate_leaf(g, 1, 10, lines, derive_uncovered=True)
    assert not [e for e in errs if "belongs to no node" in e]
    assert any(u.get("reason", "").startswith("unclaimed-content")
               for u in g["uncovered"])
    g2 = leaf(6)    # 4 residue lines -> still hard failure
    errs2 = R.validate_leaf(g2, 1, 10, lines, derive_uncovered=True)
    assert any("belongs to no node" in e for e in errs2)


def test_resolution_pass_gates_dissimilar_renames(tmp_path):
    """ds4_divergence_analysis: the content_definition mis-rename class."""
    g = {"nodes": [
        {"id": "a", "establishes": "p",
         "provides": [{"name": "content_definition",
                       "prose": "the content field of a message object in "
                                "the API request format"}],
         "needs": [], "spans": [{"lines": [1, 1]}]},
        {"id": "b", "establishes": "n",
         "needs": [{"name": "stay_in_bounds_content_categories",
                    "prose": "the categories of disallowed and restricted "
                             "content the assistant must not produce"}],
         "provides": [], "spans": [{"lines": [2, 2]}]}]}
    reply = {"resolutions": [{"needer": "b",
                              "name": "stay_in_bounds_content_categories",
                              "rename_to": "content_definition"}],
             "merges": [], "structure_nodes": [], "judgment_calls": []}
    drv = R.Driver({}, R.MockClient([reply]), ["x", "y"], str(tmp_path))
    g2 = R.run_resolution_pass(drv, g, str(tmp_path))
    # the dissimilar rename is GATED: need keeps its name, stays dangling
    assert g2["nodes"][1]["needs"][0]["name"] == \
        "stay_in_bounds_content_categories"
    assert any("gated on prose" in a for a in g2["driver_autofixes"])


def test_duplicate_seed_names_autofix_validator_coherence():
    """ds5 2026-08-12: same-name seeds at two establishment sites; autofix
    (last-wins) and validator (first-wins) consulted different entries --
    unfixable loop. Both must read the first."""
    d = {"decision": "divide", "_span_lo": 1414, "_span_hi": 3147,
         "children": [{"span": [1414, 1797]}, {"span": [1798, 1973]},
                      {"span": [1974, 3147]}],
         "seed_vocabulary": [
             {"name": "chain_of_command", "prose": "p",
              "established_around": [1799, 1799]},
             {"name": "chain_of_command", "prose": "p2",
              "established_around": [2488, 2488]}],
         "expected_cross_links": [{"name": "chain_of_command",
                                   "needs_side_child": 1,
                                   "provides_side_child": 3}]}
    R.autofix_division(d)
    assert R.validate_division(d, 1414, 3147) == []
    assert d["expected_cross_links"][0]["provides_side_child"] == 2


# ------- serial-path mirrors of the ds5 2026-08-12 guard fixes ------------
# Coverage measurement (2026-08-12) showed the Driver.call twins of the
# dispatch_core pins were themselves latent -- the exact defect class that
# bit ds5 twice. These execute them.

def test_call_oversize_malfunction_resamples_once_serial(tmp_path):
    """Driver.call twin of the dispatch_core pin: an oversize first draw the
    classifier calls MALFUNCTION gets one fresh resample."""
    good = {"fixed": True}
    drv = R.Driver({"model": {"max_tokens": 4}},
                   R.MockClient([{"x": "y" * 100}, good]),
                   ["a"], str(tmp_path))
    out = drv.call("dispatch", lambda o: ["bad"] if "x" in o else [])
    assert out == good
    assert drv.client.calls == 2


def test_call_oversize_dense_fails_serial(tmp_path):
    """Driver.call twin: a DENSE oversize first draw fails loudly, no
    resample."""
    dense = [{"id": f"L1-9_n{i:03d}",
              "establishes": f"distinct claim number {i} about a different "
                             f"obligation"} for i in range(30)]
    drv = R.Driver({"model": {"max_tokens": 4}},
                   R.MockClient([dense]), ["a"], str(tmp_path))
    with pytest.raises(R.T.Phase1Error, match="dense span"):
        drv.call("dispatch", lambda o: ["bad"])
    assert drv.client.calls == 1


def test_call_identical_repair_reply_restarts_fresh_serial(tmp_path):
    """Driver.call twin: a repair reply byte-identical to the reply it was
    asked to correct restarts the dispatch fresh once."""
    bad, good = {"a": 1}, {"fixed": True}
    # max_repairs=1 makes this DISCRIMINATING: without the restart, the
    # identical round-1 reply exhausts the repair budget and raises; only
    # the fresh restart reaches the third draw
    drv = R.Driver({"max_repairs": 1},
                   R.MockClient([bad, bad, good]), ["a"], str(tmp_path))
    out = drv.call("dispatch", lambda o: [] if o.get("fixed") else ["wrong"])
    assert out == good
    assert drv.client.calls == 3


def test_broken_promises_names_undelivered_cross_links(tmp_path):
    """Promise-vs-delivery (Matt-approved 2026-08-12): ds5's c3/c2 division
    promised `chain_of_command` via expected_cross_links and no leaf of any
    child provided it -- discovered only as 24 danglings at the root. The
    check names undelivered promises at unwind time; delivered ones are
    silent."""
    division = {"expected_cross_links": [
        {"name": "chain_of_command", "needs_side_child": 1,
         "provides_side_child": 2},
        {"name": "user_authority", "needs_side_child": 2,
         "provides_side_child": 1}]}
    children = [
        {"nodes": [{"id": "a", "provides": [{"name": "user_authority"}]}]},
        {"nodes": [{"id": "b", "provides": [
            {"name": "protect_privileged_information"}]}]}]
    assert R.broken_promises(division, children) == ["chain_of_command"]
    assert R.broken_promises({"expected_cross_links": []}, children) == []
    # the health row carries the break and warns
    drv = R.Driver({}, R.MockClient([]), ["a"], str(tmp_path))
    drv._health({"nodes": [], "uncovered": []}, 1, 1, "unwind",
                str(tmp_path), promises=["chain_of_command"])
    row = json.loads(open(os.path.join(str(tmp_path),
                                       "health.jsonl")).read())
    assert row["broken_promises"] == ["chain_of_command"]


def _dense_reply():
    # oversize under a tiny cap, classifier verdict "dense": distinct ids,
    # distinct establishes -- and it fails leaf validation (no coverage)
    return {"nodes": [
        {"id": f"L1-9_n{i:03d}",
         "establishes": f"distinct claim number {i} about an obligation",
         "needs": [], "provides": [], "spans": [{"lines": [1, 1]}]}
        for i in range(20)], "uncovered": []}


def test_dense_leaf_recurses_via_phase_d_serial(tmp_path):
    """Matt's ruling 2026-08-12: a leaf whose content overflows the cap
    re-enters the NORMAL division path -- same machinery, connectivity by
    the ordinary unwind. (Rejected by name: D6 stages 2-3 mechanical
    bisect.) Toy doc with leaf_max >= doc so the root goes straight to
    leaf; the dense draw falls back to the stored D/L/L/U flow."""
    toy = os.path.join(HERE, "toy_doc.md")
    lines = R.load_doc(toy)
    replies = [_dense_reply()] + json.load(
        open(os.path.join(HERE, "mock_replies.json")))
    drv = R.Driver({"leaf_max_lines": 100, "model": {"max_tokens": 4}},
                   R.MockClient(replies), lines, str(tmp_path))
    g = drv.build(1, len(lines), [], str(tmp_path))
    assert len(g["nodes"]) == 10            # the normal toy result
    assert os.path.exists(os.path.join(str(tmp_path), "division.json"))
    assert drv.client.calls == 5            # dense draw + D + L + L + U


def test_dense_leaf_recurses_via_phase_d_core(tmp_path):
    """The dispatch_core twin: the leaf state MORPHS into the division
    dispatch in place; the scheduler then runs children and unwind as
    usual. Byte-identical artifacts to the serial fallback."""
    import dispatch_core as DC
    toy = os.path.join(HERE, "toy_doc.md")
    lines = R.load_doc(toy)
    replies = [_dense_reply()] + json.load(
        open(os.path.join(HERE, "mock_replies.json")))
    a, b = os.path.join(str(tmp_path), "ser"), os.path.join(str(tmp_path),
                                                            "core")
    os.makedirs(a), os.makedirs(b)
    cfg = {"leaf_max_lines": 100, "model": {"max_tokens": 4}}
    R.Driver(cfg, R.MockClient(list(replies)), lines, a).build(
        1, len(lines), [], a)
    drv = R.Driver(cfg, R.MockClient(list(replies)), lines, b)
    g = DC.run_build(drv, 1, len(lines), [], b, "serial")
    assert len(g["nodes"]) == 10
    assert (open(os.path.join(a, "graph.json"), "rb").read()
            == open(os.path.join(b, "graph.json"), "rb").read())
