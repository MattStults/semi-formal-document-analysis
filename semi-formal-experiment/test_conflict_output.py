"""Tests for the priority-2 (behaviour-vs-document conflict) panel contract.

The panel file we must interoperate with is the relevance panel at
`conflict_output.PANEL_JSON`. These tests pin the parts of its shape we copy,
the parts we deliberately change (score semantics, id infix, role header), and
the validator's error messages -- the user runs the validator on a
hand-collected file, so an error that does not name a JSON path is a bug.

Three properties are load-bearing for the panel to be usable as a REFERENCE
against which the tool is scored, and each has its own block below:

  * BLINDING -- the judging copy carries no tool verdict, rationale or cited
    span. Anything the tool believes lives in the side-car.
  * NEGATIVE SAMPLING -- passages the tool did NOT flag are mixed in, so
    prevalence and recall are estimable rather than undefined.
  * ROSTER -- exactly three named judges, the same three on every passage
    within a behaviour, or the pair-gold protocol silently degrades.
"""
import copy
import json
import os

import pytest

import conflict_output as co
import inventory

HERE = os.path.dirname(os.path.abspath(__file__))


# ---- fixtures ----

def _panel():
    return [
        co.Judge("sol", "GPT-5.6 Sol", "model", model="gpt-5.6-sol"),
        co.Judge("kimi", "Kimi-K3", "model", model="moonshotai/Kimi-K3"),
        co.Judge("fable", "Claude Fable 5", "model", model="claude-fable-5"),
    ]


def _findings():
    return [
        co.ConflictFinding(
            behaviour_slug="helpfulness",
            spec="openai",
            clause_id="m0163",
            locator="model_spec@2025-12-18 > The chain of command > "
                    "Assume best intentions > ¶2",
            quote="It should generally assume users have goals and preferences "
                  "similar to an average, reasonable human being, avoiding "
                  "unnecessary or trivial clarifying questions[^agd3].",
            conflict_score=0.86,
            rationale="The conduct asks three clarifying questions before doing "
                      "any work on a request the clause treats as answerable.",
            cited_spans=["avoiding unnecessary or trivial clarifying questions"],
        ),
        co.ConflictFinding(
            behaviour_slug="helpfulness",
            spec="openai",
            clause_id="m0537",
            locator="model_spec@2025-12-18 > Use appropriate style > "
                    "Be thorough but efficient, while respecting length limits > ¶4",
            quote="The assistant should take on laborious tasks without "
                  "complaint or hesitation[^8uz1].",
            conflict_score=0.41,
            rationale="Deferring the work back to the user reads as hesitation.",
            cited_spans=["without complaint or hesitation"],
            example_block=False,
            adjacent=True,
        ),
    ]


def _emit(findings=None, **kw):
    kw.setdefault("panel", _panel())
    return co.emit(findings if findings is not None else _findings(), **kw)


def _frame(**kw):
    """A synthetic clause pool: 40 rows carry a tool score (the ranked band the
    near-miss stratum is drawn from), 80 do not."""
    rows = [{"clauseId": f"z{i:04d}",
             "locator": f"model_spec@2025-12-18 > Synthetic > ¶{i}",
             "quote": f"synthetic clause number {i}",
             "exampleBlock": False,
             "toolScore": round(0.60 - i * 0.001, 4) if i < 40 else None}
            for i in range(120)]
    kw.setdefault("n_near", 2)
    kw.setdefault("n_field", 2)
    return co.SamplingFrame(rows=rows, **kw)


# ---- contract discovery: the real panel file ----

def test_panel_file_has_the_shape_we_copy():
    data = json.load(open(co.PANEL_JSON))
    assert set(data) == {"generatedFrom", "provenance", "behaviours"}
    assert len(data["behaviours"]) == 3
    for b in data["behaviours"]:
        assert set(b) == {"id", "slug", "name", "definition", "category", "coverage"}
        assert set(b["coverage"]) == {"anthropic", "openai"}
        for cov in b["coverage"].values():
            assert set(cov) == {"verdict", "depth", "note", "verifiedDate", "passages"}
            for p in cov["passages"]:
                assert set(p) == {"id", "locator", "quote", "exampleBlock",
                                  "role", "adjacent", "score", "verdicts"}
                assert 0 <= p["score"] <= 6
                assert p["score"] == sum(p["verdicts"].values())


def test_panel_metadata_loads_and_is_reused_not_retyped():
    meta = co.load_behaviour_metadata()
    assert [b["slug"] for b in meta] == [
        "helpfulness", "harm-avoidance-to-third-parties",
        "avoiding-over-and-under-caution"]
    assert all(set(b) == {"id", "slug", "name", "definition", "category"}
               for b in meta)


# ---- emitter ----

def test_emit_matches_panel_shape_exactly():
    data = _emit()
    assert set(data) == {"generatedFrom", "provenance", "behaviours"}
    b = [x for x in data["behaviours"] if x["slug"] == "helpfulness"][0]
    assert set(b) >= {"id", "slug", "name", "definition", "category", "coverage"}
    cov = b["coverage"]["openai"]
    assert set(cov) == {"verdict", "depth", "note", "verifiedDate", "passages"}
    p = cov["passages"][0]
    assert set(p) == {"id", "locator", "quote", "exampleBlock", "role",
                      "adjacent", "score", "verdicts", "authority"}


def test_emit_leaves_panel_slots_empty():
    p = _emit()["behaviours"][0]["coverage"]["openai"]["passages"][0]
    assert p["score"] is None
    assert p["verdicts"] == {}
    assert p["role"] == ""


def test_emit_records_conflict_score_semantics_in_provenance():
    prov = _emit()["provenance"]
    assert prov["relation"] == co.RELATION
    assert prov["scoreSemantics"]["dimension"] == "conflict"
    anchors = prov["scoreSemantics"]["anchors"]
    assert anchors["0"] and anchors["6"]
    assert prov["joinKey"] == "quote"


def test_emit_ids_are_unique_and_not_confusable_with_panel_ids():
    data = _emit(_findings() + [
        co.ConflictFinding("harm-avoidance-to-third-parties", "openai", "m0165",
                           "model_spec@2025-12-18 > Stay in bounds > ¶1",
                           "q", 1, "r", [])])
    ids = [p["id"] for b in data["behaviours"]
           for cov in b["coverage"].values() for p in cov["passages"]]
    assert len(ids) == len(set(ids))
    assert all("-conflict-" in i for i in ids)
    assert not any("-panel-" in i for i in ids)


def test_emit_keeps_our_locator_and_never_translates_it():
    p = _emit()["behaviours"][0]["coverage"]["openai"]["passages"][0]
    assert p["locator"].startswith("model_spec@2025-12-18 > ")
    assert p["quote"]  # the join key travels with it


def test_emit_requires_a_conduct_description_per_behaviour():
    data = _emit(conduct={"helpfulness": "Asks three clarifying questions and "
                                         "does no work."})
    b = data["behaviours"][0]
    assert b["conduct"] == "Asks three clarifying questions and does no work."


def test_emit_rejects_unknown_behaviour_slug():
    with pytest.raises(ValueError) as e:
        _emit([co.ConflictFinding("not-a-behaviour", "openai", "m1", "l", "q",
                                  1, "r", [])])
    assert "not-a-behaviour" in str(e.value)


def test_emit_rejects_unknown_spec_key():
    with pytest.raises(ValueError) as e:
        _emit([co.ConflictFinding("helpfulness", "deepmind", "m1", "l", "q",
                                  1, "r", [])])
    assert "deepmind" in str(e.value)


# ---- F5a: BLINDING ----

def test_emit_is_blinded_by_default():
    """The judge must not see the tool's verdict, rationale or cited spans:
    a judge shown the answer cannot produce an independent gold."""
    text = json.dumps(_emit())
    assert "tool" not in {k for b in _emit()["behaviours"]
                          for cov in b["coverage"].values()
                          for p in cov["passages"] for k in p}
    assert "rationale" not in text
    assert "citedSpans" not in text
    assert "conflictScore" not in text


def test_emit_includes_tool_claims_only_when_explicitly_asked():
    p = _emit(include_tool_claims=True)["behaviours"][0][
        "coverage"]["openai"]["passages"][0]
    assert p["tool"]["conflictScore"] == 0.86
    assert p["tool"]["clauseId"] == "m0163"
    assert p["tool"]["rationale"].startswith("The conduct asks")
    assert p["tool"]["citedSpans"] == [
        "avoiding unnecessary or trivial clarifying questions"]


def test_emit_pair_returns_a_blinded_copy_and_a_side_car_keyed_by_id():
    judging, side = co.emit_pair(_findings(), panel=_panel())
    assert co.validate(judging, mode="input") == []
    ids = {p["id"] for b in judging["behaviours"]
           for cov in b["coverage"].values() for p in cov["passages"]}
    assert set(side["passages"]) == ids
    for pid, rec in side["passages"].items():
        assert rec["origin"] in co.ORIGINS
        assert rec["behaviour"] and rec["spec"]
    assert side["passages"][sorted(ids)[0]]["tool"] is not None


def test_side_car_holds_the_tool_claim_and_the_judging_copy_holds_none_of_it():
    judging, side = co.emit_pair(_findings(), panel=_panel())
    jtext = json.dumps(judging)
    for needle in ("m0163", "0.86", "citedSpans", "rationale", "origin",
                   "candidate"):
        assert needle not in jtext, f"{needle!r} leaked into the judging copy"
    stext = json.dumps(side)
    assert "m0163" in stext and "rationale" in stext


def test_validator_rejects_a_tool_key_in_a_judging_file():
    data = _emit(include_tool_claims=True)
    errs = co.validate(data, mode="input")
    _has(errs, "behaviours[0].coverage.openai.passages[0].tool")
    assert any("side-car" in e for e in errs)


def test_validator_accepts_tool_claims_when_blinding_is_explicitly_waived():
    data = _emit(include_tool_claims=True)
    assert co.validate(data, mode="input", blinded=False) == []


def test_side_car_validates_and_must_match_the_judging_copy():
    judging, side = co.emit_pair(_findings(), panel=_panel())
    assert co.validate_sidecar(side, judging) == []
    side["passages"].pop(sorted(side["passages"])[0])
    errs = co.validate_sidecar(side, judging)
    assert errs and any("passages" in e for e in errs)


# ---- F5b: NEGATIVE SAMPLING ----

def test_negatives_are_drawn_and_recorded_only_in_the_side_car():
    judging, side = co.emit_pair(_findings(), panel=_panel(),
                                 negatives=_frame())
    ps = judging["behaviours"][0]["coverage"]["openai"]["passages"]
    assert len(ps) == 2 + 2 + 2  # 2 candidates + n_near + n_field
    origins = [side["passages"][p["id"]]["origin"] for p in ps]
    assert origins.count("candidate") == 2
    assert origins.count("negative-near") == 2
    assert origins.count("negative-field") == 2


def test_negatives_are_interleaved_not_appended():
    judging, side = co.emit_pair(_findings(), panel=_panel(),
                                 negatives=_frame(n_near=4, n_field=4))
    ps = judging["behaviours"][0]["coverage"]["openai"]["passages"]
    origins = [side["passages"][p["id"]]["origin"] for p in ps]
    # a candidate must appear after at least one negative, otherwise the
    # ordering itself tells the judge which passages the tool flagged
    first_neg = min(i for i, o in enumerate(origins) if o != "candidate")
    last_cand = max(i for i, o in enumerate(origins) if o == "candidate")
    assert last_cand > first_neg, origins


def test_passage_ids_do_not_encode_whether_the_tool_flagged_the_passage():
    judging, side = co.emit_pair(_findings(), panel=_panel(), negatives=_frame())
    ps = judging["behaviours"][0]["coverage"]["openai"]["passages"]
    assert [p["id"] for p in ps] == [
        f"openai-helpfulness-conflict-{i}" for i in range(1, len(ps) + 1)]


def test_negative_sampling_is_reproducible_from_the_recorded_seed():
    a, sa = co.emit_pair(_findings(), panel=_panel(), negatives=_frame(seed=7))
    b, sb = co.emit_pair(_findings(), panel=_panel(), negatives=_frame(seed=7))
    assert a == b
    assert sa["sampling"]["seed"] == 7
    c, _ = co.emit_pair(_findings(), panel=_panel(), negatives=_frame(seed=8))
    assert c != a


def test_side_car_records_inclusion_probability_and_frame_size():
    _, side = co.emit_pair(_findings(), panel=_panel(), negatives=_frame())
    near = [r for r in side["passages"].values()
            if r["origin"] == "negative-near"]
    field = [r for r in side["passages"].values()
             if r["origin"] == "negative-field"]
    assert near and field
    assert near[0]["frameSize"] == 40 and near[0]["inclusionProbability"] == 2 / 40
    assert field[0]["frameSize"] == 80 and field[0]["inclusionProbability"] == 2 / 80


def test_negatives_never_repeat_a_flagged_clause_id():
    frame = _frame()
    frame.rows.append({"clauseId": "m0163", "locator": "x",
                       "quote": _findings()[0].quote, "exampleBlock": False,
                       "toolScore": 0.99})
    judging, side = co.emit_pair(_findings(), panel=_panel(), negatives=frame)
    quotes = [p["quote"] for b in judging["behaviours"]
              for cov in b["coverage"].values() for p in cov["passages"]]
    assert len(quotes) == len(set(quotes))
    assert all(r["clauseId"] != "m0163"
               for r in side["passages"].values() if r["origin"] != "candidate")


def test_negatives_never_repeat_a_flagged_QUOTE_under_another_clause_id():
    """Our segmentation gives the same sentence more than one id in places, and
    a tool finding's clause id need not be in the pool at all. A duplicated
    passage is worse than a wasted one: the same text lands in the panel twice
    with two different true labels."""
    dup = dict(clauseId="OTHER-ID", locator="model_spec@2025-12-18 > X > ¶1",
               quote=_findings()[0].quote, exampleBlock=False, toolScore=0.99)
    other = dict(clauseId="z0001", locator="model_spec@2025-12-18 > Y > ¶1",
                 quote="a different clause entirely", exampleBlock=False,
                 toolScore=0.98)
    # near frame is exactly these two and both are drawn, so the duplicate can
    # only be kept out by the quote check
    frame = co.SamplingFrame(rows=[dup, other], n_near=2, n_field=0)
    judging, side = co.emit_pair(_findings(), panel=_panel(), negatives=frame)
    quotes = [p["quote"] for b in judging["behaviours"]
              for cov in b["coverage"].values() for p in cov["passages"]]
    assert len(quotes) == len(set(quotes)), quotes
    assert all(r["clauseId"] != "OTHER-ID"
               for r in side["passages"].values() if r["origin"] != "candidate")


def test_rejoin_pairs_verdicts_with_true_labels():
    judging, side = co.emit_pair(_findings(), panel=_panel(), negatives=_frame())
    _fill(judging)
    rows = co.rejoin(judging, side)
    assert len(rows) == len(side["passages"])
    r = rows[0]
    assert set(r) >= {"id", "behaviour", "spec", "origin", "toolFlagged",
                      "score", "verdicts", "weight"}
    assert all(x["score"] == 4 for x in rows)
    assert sum(1 for x in rows if x["toolFlagged"]) == 2


def test_rejoin_refuses_a_side_car_that_does_not_match():
    judging, side = co.emit_pair(_findings(), panel=_panel())
    lost = sorted(side["passages"])[0]
    side["passages"].pop(lost)
    with pytest.raises(ValueError) as e:
        co.rejoin(_fill(judging), side)
    assert lost in str(e.value)


def test_estimate_reports_precision_and_an_inverse_probability_recall():
    judging, side = co.emit_pair(_findings(), panel=_panel(), negatives=_frame())
    for b in judging["behaviours"]:
        for cov in b["coverage"].values():
            for p in cov["passages"]:
                flagged = side["passages"][p["id"]]["origin"] == "candidate"
                p["verdicts"] = {"sol": 2 if flagged else 0,
                                 "kimi": 2 if flagged else 0,
                                 "fable": 2 if flagged else 0}
                p["score"] = sum(p["verdicts"].values())
                p["role"] = co.render_role(p["verdicts"])
    est = co.estimate(co.rejoin(judging, side))
    assert est["candidates"] == 2
    assert est["precision"] == 1.0
    assert est["estimatedMissed"] == 0.0
    assert est["recall"] == 1.0
    assert "caveat" in est


def test_estimate_recall_uses_the_sampling_weights_not_raw_counts():
    judging, side = co.emit_pair(_findings(), panel=_panel(), negatives=_frame())
    for b in judging["behaviours"]:
        for cov in b["coverage"].values():
            for p in cov["passages"]:
                rec = side["passages"][p["id"]]
                pos = rec["origin"] in ("candidate", "negative-field")
                p["verdicts"] = {j: (2 if pos else 0) for j in
                                 ("sol", "kimi", "fable")}
                p["score"] = sum(p["verdicts"].values())
                p["role"] = co.render_role(p["verdicts"])
    est = co.estimate(co.rejoin(judging, side))
    # 2 field negatives judged positive, each standing for 80/2 = 40 clauses
    assert est["estimatedMissed"] == 80.0
    assert est["naiveMissed"] == 2
    assert est["recall"] == pytest.approx(2 / 82)


# ---- F6: the roster ----

def test_emit_refuses_to_build_a_file_with_no_named_judges():
    with pytest.raises(ValueError) as e:
        co.emit(_findings())
    assert "panel" in str(e.value).lower()


def test_emit_records_the_roster_in_provenance():
    prov = _emit()["provenance"]
    assert [j["id"] for j in prov["panel"]] == ["sol", "kimi", "fable"]
    assert prov["panel"][0]["kind"] == "model"
    assert prov["panel"][0]["model"] == "gpt-5.6-sol"


def test_validator_rejects_an_empty_roster():
    def m(d):
        d["provenance"]["panel"] = []
    errs = _errs(m)
    _has(errs, "provenance.panel")
    assert any("non-empty" in e for e in errs), errs


def test_validator_rejects_a_roster_that_is_not_three_judges():
    def m(d):
        d["provenance"]["panel"] = d["provenance"]["panel"][:2]
    errs = _errs(m)
    _has(errs, "provenance.panel")
    assert any("3" in e for e in errs)


def test_validator_rejects_a_model_judge_with_no_model_id():
    def m(d):
        d["provenance"]["panel"][0].pop("model")
    _has(_errs(m), "provenance.panel[0].model")


def test_validator_rejects_an_unknown_kind_of_judge():
    def m(d):
        d["provenance"]["panel"][0]["kind"] = "committee"
    _has(_errs(m), "provenance.panel[0].kind")


def test_validator_rejects_an_unknown_judge_key_in_verdicts():
    def m(d):
        _fill(d)
        p = d["behaviours"][0]["coverage"]["openai"]["passages"][0]
        p["verdicts"] = {"sol": 2, "kimi": 1, "bob": 1}
    errs = _errs(m, mode="panel")
    _has(errs, "behaviours[0].coverage.openai.passages[0].verdicts")
    assert any("bob" in e for e in errs)


def test_validator_rejects_roster_drift_between_passages():
    def m(d):
        _fill(d)
        p = d["behaviours"][0]["coverage"]["openai"]["passages"][1]
        p["verdicts"] = {"sol": 2, "kimi": 1}
        p["score"] = 3
        p["role"] = co.render_role(p["verdicts"])
    errs = _errs(m, mode="panel")
    _has(errs, "behaviours[0].coverage.openai.passages[1].verdicts")


def test_a_one_judge_passage_is_rejected_rather_than_rescaled():
    """`hi = 2 * len(verdicts)` let a 1-judge passage validate against a 0..2
    range while `scoreSemantics.scale` promised 0..6. The roster check is what
    forbids it now; the scale itself is stated in terms of PANEL_SIZE and never
    floats with how many judges happened to answer."""
    assert co.SCORE_SEMANTICS["scale"] == "sum over 3 judges of 0/1/2 = 0..6"

    def m(d):
        _fill(d)
        p = d["behaviours"][0]["coverage"]["openai"]["passages"][0]
        p["verdicts"] = {"sol": 2}
        p["score"] = 2
        p["role"] = co.render_role({"sol": 2})
    errs = _errs(m, mode="panel")
    _has(errs, "behaviours[0].coverage.openai.passages[0].verdicts")


# ---- F6: authority of the quoted provision ----

def test_authority_is_attached_to_every_passage():
    data = _emit()
    ps = data["behaviours"][0]["coverage"]["openai"]["passages"]
    assert ps[0]["authority"] == "root"          # Assume best intentions
    assert ps[1]["authority"] == "guideline"     # Be thorough but efficient


def test_authority_for_reads_the_specs_own_markers():
    a = co.authority_for("model_spec@2025-12-18 > Stay in bounds > Do not "
                         "generate disallowed content > Restricted content > "
                         "Don't provide information hazards > ¶3")
    assert a == "root"
    b = co.authority_for("model_spec@2025-12-18 > Seek the truth together > "
                         "Don't have an agenda > No topic is off limits > ¶1")
    assert b == "guideline"
    assert co.authority_for("model_spec@2025-12-18 > Nowhere at all > ¶1") == \
        "unmarked"


def test_authority_levels_say_which_are_overridable():
    assert co.OVERRIDABLE["root"] is False
    assert co.OVERRIDABLE["guideline"] is True
    assert co.OVERRIDABLE["user"] is True


def test_validator_rejects_an_unknown_authority_value():
    def m(d):
        d["behaviours"][0]["coverage"]["openai"]["passages"][0][
            "authority"] = "supreme"
    _has(_errs(m), "behaviours[0].coverage.openai.passages[0].authority")


# ---- F6: the judge prompt and the calibration examples ----

def test_a_ready_to_use_judge_prompt_is_supplied():
    p = co.render_judge_prompt(
        conduct="The assistant does X.",
        passage={"quote": "Q", "locator": "L", "authority": "guideline"})
    assert "The assistant does X." in p and "Q" in p
    assert "guideline" in p
    for needle in ("2", "1", "0", "authority", "JSON"):
        assert needle in p


def test_judge_prompt_carries_the_three_calibration_examples():
    p = co.render_judge_prompt(conduct="c", passage={
        "quote": "q", "locator": "l", "authority": "root"})
    for ex in co.CALIBRATION_EXAMPLES:
        assert ex["quote"][:40] in p
        assert ex["reasoning"][:40] in p


def test_there_are_three_calibration_examples_one_per_level():
    labels = [ex["label"] for ex in co.CALIBRATION_EXAMPLES]
    assert sorted(labels) == [0, 1, 2]
    for ex in co.CALIBRATION_EXAMPLES:
        assert ex["conduct"] and ex["reasoning"] and ex["locator"]


def test_calibration_example_quotes_are_verbatim_model_spec_text():
    text = inventory.spec_text()
    for ex in co.CALIBRATION_EXAMPLES:
        assert ex["quote"] in text, ex["label"]


def test_calibration_example_authority_matches_the_document():
    """The example's stated authority must be the one the spec actually marks,
    or the prompt teaches the authority rule with a wrong instance."""
    for ex in co.CALIBRATION_EXAMPLES:
        assert co.authority_for(ex["locator"]) == ex["authority"], ex["label"]


def test_calibration_examples_are_not_items_in_the_panel():
    """An example is an answer. A (conduct, passage) pair that appears both in
    the prompt and in the file being judged is a contaminated item."""
    pairs = set()
    for b in co.load(SAMPLE)["behaviours"]:
        for cov in b["coverage"].values():
            for p in cov["passages"]:
                pairs.add((b["conduct"], p["quote"]))
    for ex in co.CALIBRATION_EXAMPLES:
        assert (ex["conduct"], ex["quote"]) not in pairs, ex["label"]
        assert ex["conduct"] not in {c for c, _ in pairs}, ex["label"]


def test_validator_rejects_a_conduct_that_is_a_calibration_example():
    """Judging a vignette whose answer is printed in the judge prompt does not
    measure anything."""
    def m(d):
        d["behaviours"][0]["conduct"] = co.CALIBRATION_EXAMPLES[0]["conduct"]
    errs = _errs(m)
    _has(errs, "behaviours[0].conduct")
    assert any("calibration" in e for e in errs), errs


def test_the_zero_example_is_relevant_but_not_violated():
    zero = [e for e in co.CALIBRATION_EXAMPLES if e["label"] == 0][0]
    assert "relevan" in zero["reasoning"].lower()


def test_provenance_records_which_judge_prompt_was_used():
    prov = _emit()["provenance"]
    assert prov["judgePrompt"]["id"] == co.JUDGE_PROMPT_ID
    assert prov["judgePrompt"]["sha256"] == co.judge_prompt_sha256()


def test_validator_rejects_a_missing_judge_prompt_record():
    def m(d):
        d["provenance"].pop("judgePrompt")
    _has(_errs(m), "provenance.judgePrompt")


def test_validator_rejects_a_judge_prompt_record_with_no_digest():
    """An id alone does not identify the rubric the judges actually saw."""
    def m(d):
        d["provenance"]["judgePrompt"] = {"id": co.JUDGE_PROMPT_ID}
    _has(_errs(m), "provenance.judgePrompt")


def test_cli_prints_the_judge_prompt(capsys):
    assert co.main(["prompt"]) == 0
    assert "conflict" in capsys.readouterr().out.lower()


# ---- validator: happy paths ----

def test_emitted_file_validates_in_input_mode(tmp_path):
    path = tmp_path / "c.json"
    co.write(str(path), _emit())
    assert co.validate(str(path), mode="input") == []


def test_filled_panel_validates_in_panel_mode():
    data = _fill(_emit())
    assert co.validate(data, mode="panel") == []


def _fill(data, score=4):
    """Simulate the human panel filling the empty slots."""
    for b in data["behaviours"]:
        for cov in b["coverage"].values():
            for p in cov["passages"]:
                p["verdicts"] = {"sol": 2, "kimi": 1, "fable": 1}
                p["score"] = 4
                p["role"] = co.render_role(p["verdicts"], {
                    "sol": "GPT-5.6 Sol", "kimi": "Kimi-K3",
                    "fable": "Claude Fable 5"})
    return data


def test_round_trip_preserves_every_field(tmp_path):
    data = _fill(_emit(conduct={"helpfulness": "Asks and stalls."}))
    path = tmp_path / "rt.json"
    co.write(str(path), data)
    assert co.validate(str(path), mode="panel") == []
    back = co.load(str(path))
    assert back == data
    p2 = tmp_path / "rt2.json"
    co.write(str(p2), back)
    assert open(str(p2), "rb").read() == open(str(path), "rb").read()


def test_findings_round_trip_through_an_unblinded_file():
    data = _emit(include_tool_claims=True, conduct={"helpfulness": "Asks."})
    findings, conduct = co.findings_from(data)
    again = co.emit(findings, conduct=conduct, panel=_panel(),
                    include_tool_claims=True,
                    generated_from=data["generatedFrom"],
                    run_date=data["provenance"]["runDate"],
                    coverage_notes=co.coverage_notes_from(data))
    assert again == data


def test_render_role_header_says_conflict_not_relevance():
    role = co.render_role({"sol": 2, "kimi": 2, "fable": 2},
                          {"sol": "GPT-5.6 Sol", "kimi": "Kimi-K3",
                           "fable": "Claude Fable 5"})
    assert role.startswith("Model determined conflict (score 6/6):")
    assert "violation" in role
    assert "relevance" not in role


# ---- validator: rejections, each naming a JSON path ----

def _errs(mutate, mode="input", **kw):
    data = _emit()
    mutate(data)
    return co.validate(data, mode=mode, **kw)


def _has(errs, path):
    assert any(path in e for e in errs), f"no error naming {path!r}; got {errs}"


def test_rejects_missing_passages_key():
    def m(d):
        del d["behaviours"][0]["coverage"]["openai"]["passages"]
    _has(_errs(m), "behaviours[0].coverage.openai.passages")


def test_rejects_empty_passage_list():
    def m(d):
        d["behaviours"][0]["coverage"]["openai"]["passages"] = []
    _has(_errs(m), "behaviours[0].coverage.openai.passages")


def test_rejects_score_out_of_range():
    def m(d):
        _fill(d)
        d["behaviours"][0]["coverage"]["openai"]["passages"][1]["score"] = 7
    errs = _errs(m, mode="panel")
    _has(errs, "behaviours[0].coverage.openai.passages[1].score")
    assert any("0..6" in e for e in errs)


def test_rejects_score_not_matching_verdicts():
    def m(d):
        _fill(d)
        d["behaviours"][0]["coverage"]["openai"]["passages"][0]["score"] = 5
    _has(_errs(m, mode="panel"),
         "behaviours[0].coverage.openai.passages[0].score")


def test_rejects_missing_quote():
    def m(d):
        del d["behaviours"][0]["coverage"]["openai"]["passages"][1]["quote"]
    errs = _errs(m)
    _has(errs, "behaviours[0].coverage.openai.passages[1].quote")
    assert any("join key" in e for e in errs)


def test_rejects_empty_quote():
    def m(d):
        d["behaviours"][0]["coverage"]["openai"]["passages"][0]["quote"] = "  "
    _has(_errs(m), "behaviours[0].coverage.openai.passages[0].quote")


def test_rejects_duplicate_passage_ids():
    def m(d):
        ps = d["behaviours"][0]["coverage"]["openai"]["passages"]
        ps[1]["id"] = ps[0]["id"]
    _has(_errs(m), "behaviours[0].coverage.openai.passages[1].id")


def test_rejects_filled_verdicts_in_input_mode():
    def m(d):
        d["behaviours"][0]["coverage"]["openai"]["passages"][0]["verdicts"] = {
            "sol": 2}
    _has(_errs(m), "behaviours[0].coverage.openai.passages[0].verdicts")


def test_rejects_unfilled_verdicts_in_panel_mode():
    _has(co.validate(_emit(), mode="panel"),
         "behaviours[0].coverage.openai.passages[0].verdicts")


def test_rejects_verdict_value_outside_0_2():
    def m(d):
        _fill(d)
        p = d["behaviours"][0]["coverage"]["openai"]["passages"][0]
        p["verdicts"]["sol"] = 3
        p["score"] = 5
    _has(_errs(m, mode="panel"),
         "behaviours[0].coverage.openai.passages[0].verdicts.sol")


def test_rejects_bad_spec_key():
    def m(d):
        d["behaviours"][0]["coverage"]["mistral"] = d["behaviours"][0][
            "coverage"]["openai"]
    _has(_errs(m), "behaviours[0].coverage.mistral")


def test_rejects_non_bool_flags():
    def m(d):
        d["behaviours"][0]["coverage"]["openai"]["passages"][0][
            "exampleBlock"] = "no"
    _has(_errs(m), "behaviours[0].coverage.openai.passages[0].exampleBlock")


def test_rejects_missing_conduct():
    def m(d):
        del d["behaviours"][0]["conduct"]
    _has(_errs(m), "behaviours[0].conduct")


def test_rejects_an_unknown_behaviour_slug_in_a_hand_edited_file():
    """emit() raises on this; the validator has to as well, or our own output
    is guarded and the user's hand-edited file is not."""
    def m(d):
        d["behaviours"][0]["slug"] = "not-a-real-behaviour"
    errs = _errs(m)
    _has(errs, "behaviours[0].slug")


def test_rejects_two_behaviours_with_the_same_slug():
    """Every consumer keys on slug, so a duplicate silently drops one entry
    and all the judging inside it."""
    def m(d):
        d["behaviours"].append(copy.deepcopy(d["behaviours"][0]))
        for cov in d["behaviours"][1]["coverage"].values():
            for i, p in enumerate(cov["passages"]):
                p["id"] = p["id"] + "-b"
    _has(_errs(m), "behaviours[1].slug")


def test_conduct_never_silently_falls_back_to_the_abstract_definition():
    """A construct is not conduct. If `conduct` is missing the file must carry
    a visible TODO, never the behaviour's definition dressed up as behaviour."""
    data = _emit()
    b = data["behaviours"][0]
    meta = {x["slug"]: x for x in co.load_behaviour_metadata()}
    assert b["conduct"] != meta[b["slug"]]["definition"]
    assert b["conduct"].startswith("TODO")


def test_write_is_atomic_and_leaves_no_temp_file(tmp_path, monkeypatch):
    """A truncating write of a hand-filled panel is unrecoverable."""
    path = tmp_path / "panel.json"
    co.write(str(path), _fill(_emit()))
    good = path.read_text()

    class Boom(Exception):
        pass

    def explode(*a, **k):
        raise Boom()

    monkeypatch.setattr(co.json, "dump", explode)
    with pytest.raises(Boom):
        co.write(str(path), {"anything": True})
    assert path.read_text() == good
    assert not os.path.exists(str(path) + ".tmp")


def test_rejects_bad_verified_date():
    def m(d):
        d["behaviours"][0]["coverage"]["openai"]["verifiedDate"] = "24 July"
    _has(_errs(m), "behaviours[0].coverage.openai.verifiedDate")


# ---- validator: damage that would waste the collection ----

def test_rejects_a_quote_that_is_not_verbatim_in_the_spec():
    def m(d):
        d["behaviours"][0]["coverage"]["openai"]["passages"][0]["quote"] = (
            "It should always assume users have goals and preferences similar "
            "to an average, reasonable human being.")
    errs = _errs(m)
    _has(errs, "behaviours[0].coverage.openai.passages[0].quote")
    # specifically the verbatim check, not the join check downstream of it
    assert any("not found verbatim" in e for e in errs), errs


def test_names_smart_quote_damage_specifically():
    def m(d):
        p = d["behaviours"][0]["coverage"]["openai"]["passages"][0]
        p["quote"] = ("“It should generally assume users have goals and "
                      "preferences similar to an average, reasonable human "
                      "being, avoiding unnecessary or trivial clarifying "
                      "questions[^agd3].”")
    errs = _errs(m)
    _has(errs, "behaviours[0].coverage.openai.passages[0].quote")
    assert any("curly" in e or "smart quote" in e for e in errs), errs


def test_names_non_breaking_space_damage_specifically():
    def m(d):
        p = d["behaviours"][0]["coverage"]["openai"]["passages"][0]
        p["quote"] = p["quote"].replace(" ", " ", 1)
    errs = _errs(m)
    _has(errs, "behaviours[0].coverage.openai.passages[0].quote")
    assert any("non-breaking" in e for e in errs), errs


def test_rejects_a_quote_that_joins_to_no_clause():
    """Verbatim in the spec but matching no clause: the passage is invisible to
    every downstream metric, which is worse than an error."""
    def m(d):
        d["behaviours"][0]["coverage"]["openai"]["passages"][0]["quote"] = (
            "# Overview {#overview}")
    errs = _errs(m)
    _has(errs, "behaviours[0].coverage.openai.passages[0].quote")
    assert any("match_passage" in e for e in errs), errs


def test_spec_checks_can_be_switched_off_for_synthetic_files():
    def m(d):
        d["behaviours"][0]["coverage"]["openai"]["passages"][0]["quote"] = "zzz"
    assert _errs(m, check_spec=False) == []


# ---- the failure mode this module exists to prevent ----

def test_rejects_the_real_relevance_panel_as_a_conflict_file():
    data = json.load(open(co.PANEL_JSON))
    errs = co.validate(data, mode="panel", check_spec=False)
    assert errs
    joined = "\n".join(errs)
    assert "provenance.relation" in joined
    assert "relevance" in joined.lower()


def test_rejects_relevance_role_text_inside_an_otherwise_valid_conflict_file():
    def m(d):
        _fill(d)
        d["behaviours"][0]["coverage"]["openai"]["passages"][0]["role"] = (
            "Model determined relevance (score 4/6):\n✓ GPT-5.6 Sol "
            "— core\n~ Kimi-K3 — related\n~ Claude Fable 5 "
            "— related")
    errs = _errs(m, mode="panel")
    _has(errs, "behaviours[0].coverage.openai.passages[0].role")
    assert any("relevance" in e for e in errs)


def test_rejects_conflict_provenance_with_relevance_score_semantics():
    def m(d):
        d["provenance"]["scoreSemantics"]["dimension"] = "relevance"
    _has(_errs(m), "provenance.scoreSemantics.dimension")


# ---- the sample artifacts ----

SAMPLE = os.path.join(HERE, "conflict_panel_input.sample.json")
SIDECAR = os.path.join(HERE, "conflict_panel_sidecar.sample.json")


def test_sample_file_validates_in_input_mode():
    assert co.validate(SAMPLE, mode="input") == []


def test_sample_is_blinded():
    data = co.load(SAMPLE)
    ps = [p for b in data["behaviours"] for cov in b["coverage"].values()
          for p in cov["passages"]]
    assert ps and all("tool" not in p for p in ps)
    assert data["provenance"]["blinded"] is True
    assert "toolScoreScale" not in data["provenance"]
    # everything except the spec quotes themselves, which are the document's
    # own words and may legitimately contain any of these
    scaffold = json.dumps({**data, "behaviours": [
        {**b, "coverage": {s: {**c, "passages": [
            {k: v for k, v in p.items() if k != "quote"}
            for p in c["passages"]]}
            for s, c in b["coverage"].items()}} for b in data["behaviours"]]})
    for needle in ("rationale", "citedSpans", "conflictScore", "origin",
                   "candidate", "negative-"):
        assert needle not in scaffold, f"{needle!r} is visible to the judge"


def test_sample_side_car_exists_and_pairs_with_the_sample():
    side = co.load(SIDECAR)
    assert co.validate_sidecar(side, co.load(SAMPLE)) == []


def test_sample_contains_negatives_the_tool_did_not_flag():
    side = co.load(SIDECAR)
    origins = [r["origin"] for r in side["passages"].values()]
    assert origins.count("candidate") >= 3
    assert sum(1 for o in origins if o != "candidate") >= 3
    assert side["sampling"]["seed"] is not None


def test_sample_covers_all_three_behaviours():
    data = co.load(SAMPLE)
    assert {b["slug"] for b in data["behaviours"]} == {
        "helpfulness", "harm-avoidance-to-third-parties",
        "avoiding-over-and-under-caution"}


def test_sample_quotes_are_verbatim_in_the_real_spec():
    text = inventory.spec_text()
    for b in co.load(SAMPLE)["behaviours"]:
        for spec, cov in b["coverage"].items():
            for i, p in enumerate(cov["passages"]):
                assert p["quote"] in text, f"{b['slug']}/{spec} passage {i}"


def test_sample_quotes_join_back_to_clauses_by_quote_text():
    rows = [dict(c, marked_span=None)
            for c in json.load(open(os.path.join(
                HERE, "modelspec_clauses.json")))["clauses"]]
    for b in co.load(SAMPLE)["behaviours"]:
        for cov in b["coverage"].values():
            for p in cov["passages"]:
                assert inventory.match_passage(p["quote"], rows), p["id"]


# ---- README ----

def test_readme_documents_join_key_and_rubric_anchors():
    text = open(os.path.join(HERE, "CONFLICT_PANEL_README.md")).read()
    for needle in ["quote", "0", "6", "conflict score", "validate"]:
        assert needle in text.lower()
    assert "conflict_output.py" in text


def test_readme_has_the_three_worked_calibration_examples():
    text = open(os.path.join(HERE, "CONFLICT_PANEL_README.md")).read()
    for ex in co.CALIBRATION_EXAMPLES:
        assert ex["quote"][:50] in text, ex["label"]
        assert ex["reasoning"][:50] in text, ex["label"]


def test_readme_states_the_authority_policy_and_defines_depth():
    text = open(os.path.join(HERE, "CONFLICT_PANEL_README.md")).read()
    low = text.lower()
    assert "authority" in low and "overrid" in low
    assert "root" in low and "guideline" in low
    for anchor in co.DEPTH_ANCHORS.values():
        assert anchor in low


def test_readme_gives_sample_size_guidance_and_names_the_judges():
    text = open(os.path.join(HERE, "CONFLICT_PANEL_README.md")).read()
    low = text.lower()
    assert "how many" in low or "sample size" in low
    assert "conduct" in low and "vignette" in low
    assert "human" in low and "model" in low


def test_readme_never_tells_the_judge_the_tools_answer():
    text = open(os.path.join(HERE, "CONFLICT_PANEL_README.md")).read()
    assert "conflictScore" not in text or "side-car" in text
    assert "it is\nthere as context" not in text
    assert "there as context" not in text


def test_cli_validate_reports_errors(tmp_path, capsys):
    bad = _emit()
    del bad["behaviours"][0]["coverage"]["openai"]["passages"][0]["quote"]
    path = tmp_path / "bad.json"
    co.write(str(path), bad)
    rc = co.main(["validate", str(path), "--mode", "input"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "behaviours[0].coverage.openai.passages[0].quote" in out


def test_cli_validate_accepts_the_sample(capsys):
    assert co.main(["validate", SAMPLE, "--mode", "input"]) == 0
    assert "ok" in capsys.readouterr().out.lower()


def test_cli_validate_checks_the_side_car_when_given_one(capsys):
    assert co.main(["validate", SAMPLE, "--mode", "input",
                    "--sidecar", SIDECAR]) == 0
    assert "ok" in capsys.readouterr().out.lower()


def test_validate_accepts_a_path_or_a_dict():
    assert co.validate(SAMPLE, mode="input") == []
    assert co.validate(co.load(SAMPLE), mode="input") == []


def test_validate_reports_unreadable_file(tmp_path):
    p = tmp_path / "nope.json"
    p.write_text("{not json")
    errs = co.validate(str(p), mode="input")
    assert errs and "<file>" in errs[0]


def test_validator_does_not_mutate_input():
    data = _emit()
    before = copy.deepcopy(data)
    co.validate(data, mode="panel")
    assert data == before
