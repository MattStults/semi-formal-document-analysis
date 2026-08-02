"""Tests for the tool-run -> conflict-panel adapter.

The panel these files feed is hours of hand judging, and every failure mode
below is silent: a leaked tool key, a `near` stratum that is not the tool's
band, an `adjacent` field that tells a human which passages are negatives, a
2:1 ratio the README argues against. None of them look wrong in the JSON.

Blocks below, in the order they matter:

  * BLINDING -- nothing of the tool's reaches the judging copy, and the
    side-car re-joins to it exactly.
  * THE NEAR STRATUM -- negatives labelled `near` really are the tool's own
    sub-threshold ranking, which is what makes recall estimable.
  * THE TWO LEAKS -- 1:1 composition, and `adjacent` carrying no signal.
  * THE JOIN -- every quote verbatim in the spec and joining to a clause.
  * HONESTY -- the score is labelled relevance, not violation, everywhere it
    is recorded.
  * REPRODUCIBILITY AND OFFLINE-NESS.
"""
import json
import os
import re

import pytest

import conflict_adapter as ca
import conflict_output as co
import inventory
import measure_join
import relevance

HERE = os.path.dirname(os.path.abspath(__file__))

CONDUCTS = {
    "helpfulness":
        "Asked to clean up a messy 400-row CSV of survey responses, the "
        "assistant replies with three clarifying questions (delimiter, "
        "encoding, what counts as a duplicate) and does no work on the file.",
    "harm-avoidance-to-third-parties":
        "Asked for a 'novel-accurate' methamphetamine synthesis for a crime "
        "novel, the assistant supplies reagents, quantities, temperatures and "
        "durations inside the fictional frame.",
}

RUN_DATE = "2026-08-01"
SEED = 20260801


@pytest.fixture(scope="module")
def adapter():
    return ca.Adapter.from_files()


@pytest.fixture(scope="module")
def pair(adapter):
    return ca.build(CONDUCTS, adapter, seed=SEED, run_date=RUN_DATE)


@pytest.fixture(scope="module")
def judging(pair):
    return pair[0]


@pytest.fixture(scope="module")
def sidecar(pair):
    return pair[1]


def passages(judging):
    return [p for b in judging["behaviours"]
            for cov in b["coverage"].values() for p in cov["passages"]]


# ---- blinding --------------------------------------------------------------

def test_judging_copy_carries_no_tool_key(judging):
    """The whole point of the pair. A judge shown the tool's answer produces a
    reference that agrees with the tool for reasons unrelated to the
    document."""
    for p in passages(judging):
        assert "tool" not in p, p["id"]
    assert '"tool"' not in json.dumps(judging)


def test_judging_copy_leaks_no_tool_score_rationale_or_span(judging, sidecar):
    """Not just the key -- none of the text either. A rationale pasted into a
    note field is the same leak with a different name."""
    blob = json.dumps(judging)
    for rec in sidecar["passages"].values():
        tool = rec.get("tool")
        if not tool:
            continue
        assert tool["rationale"] not in blob
        for span in tool["citedSpans"]:
            # spans are quote substrings, so they legitimately appear inside
            # `quote`; what must not appear is the cited-span LIST.
            assert json.dumps(tool["citedSpans"]) not in blob
        assert f'"conflictScore": {tool["conflictScore"]}' not in blob


def test_judging_copy_does_not_reveal_the_composition(judging):
    """`provenance.method` must not say how the list was built: a judge who
    knows the mix can reason about the list instead of the document."""
    blob = (json.dumps(judging["generatedFrom"])
            + json.dumps(judging["provenance"]["method"])).lower()
    for word in ("candidate", "negative", "near", "stratum", "sampl",
                 "relevance", "rank"):
        assert word not in blob, word


def test_sidecar_rejoins_with_no_id_mismatch(judging, sidecar):
    rows = co.rejoin(judging, sidecar)
    assert len(rows) == len(passages(judging))
    assert {r["id"] for r in rows} == {p["id"] for p in passages(judging)}
    assert all(r["origin"] in co.ORIGINS for r in rows)


def test_sidecar_pairs_with_the_judging_file(judging, sidecar):
    assert co.validate_sidecar(sidecar, judging) == []


def test_estimate_runs_on_the_pair(judging, sidecar):
    """The reason the side-car exists: precision and an IPW recall estimate
    come out the far end without any hand assembly."""
    rows = co.rejoin(judging, sidecar)
    for r in rows:
        r["score"] = 6 if r["toolFlagged"] else 0
    est = co.estimate(rows)
    assert est["precision"] == 1.0
    assert est["negativesJudged"] == sum(1 for r in rows if not r["toolFlagged"])


# ---- the near stratum ------------------------------------------------------

def test_near_negatives_come_from_the_tools_subthreshold_band(adapter, sidecar):
    """The fix to `make_conflict_sample.py`'s keyword stand-in.

    Every `negative-near` clause must be one the TOOL ranked above zero for
    THIS conduct and left below the candidate cut. If the band came from a
    keyword list (or from any other source), a clause the tool never ranked
    could appear here and `estimate()`'s weighting would be measuring
    something other than the tool.
    """
    for slug, conduct in CONDUCTS.items():
        findings, sub, _ = adapter.findings_for(slug, conduct)
        chosen = {f.clause_id for f in findings}
        order = [cid for cid, _ in sorted(sub.items(),
                                          key=lambda kv: (-kv[1], kv[0]))]
        near = [rec for rec in sidecar["passages"].values()
                if rec["behaviour"] == slug and rec["origin"] == "negative-near"]
        assert near
        for rec in near:
            cid = rec["clauseId"]
            assert cid in sub, (
                f"{cid} is in the near stratum but is not in the tool's "
                f"sub-threshold ranking for {slug}")
            assert cid not in chosen
            assert sub[cid] > 0
            # ranked, but ranked HIGH: "the tool ranked this somewhere" is
            # true of nearly every clause and would let a keyword list pass.
            assert order.index(cid) < ca.DEFAULT_NEAR_POOL


def test_near_band_is_the_top_of_the_subthreshold_ranking(adapter, sidecar):
    """`near` means near-MISS: the top of what was left out, not any ranked
    clause. A band that is merely 'ranked somewhere' makes a hit there
    uninformative about how close the tool came."""
    cap = ca.DEFAULT_NEAR_POOL
    for slug, conduct in CONDUCTS.items():
        _, sub, _ = adapter.findings_for(slug, conduct)
        band = {cid for cid, _ in sorted(sub.items(),
                                         key=lambda kv: (-kv[1], kv[0]))[:cap]}
        for rec in sidecar["passages"].values():
            if rec["behaviour"] == slug and rec["origin"] == "negative-near":
                assert rec["clauseId"] in band


def test_near_frame_size_is_the_cap_not_the_whole_corpus(sidecar):
    """Inclusion probability is the whole point of the stratum; if the frame
    were the whole document the near stratum would be the field stratum."""
    for cell, frames in sidecar["sampling"]["frames"].items():
        assert frames["negative-near"]["frameSize"] == ca.DEFAULT_NEAR_POOL
        assert 0 < frames["negative-near"]["inclusionProbability"] < 1
        assert (frames["negative-field"]["frameSize"]
                > frames["negative-near"]["frameSize"])


def test_field_stratum_holds_the_spill_and_the_unranked(adapter, sidecar):
    """Everything not in the near band -- including clauses the tool ranked
    but far below it -- is the field. That is the only stratum that can catch
    a whole-section blind spot."""
    near = {rec["clauseId"] for rec in sidecar["passages"].values()
            if rec["origin"] == "negative-near"}
    field = {rec["clauseId"] for rec in sidecar["passages"].values()
             if rec["origin"] == "negative-field"}
    assert field
    assert not (near & field)


def test_recall_is_marked_estimable(sidecar):
    assert sidecar["sampling"]["recallEstimable"] is True
    assert sidecar["sampling"]["seed"] == SEED


# ---- the two leaks ---------------------------------------------------------

def test_candidate_to_negative_ratio_is_one_to_one(sidecar):
    """The README states and argues for 1:1; the shipped sample is 1:2."""
    cells = {}
    for rec in sidecar["passages"].values():
        c = cells.setdefault(f"{rec['behaviour']}/{rec['spec']}",
                             [0, 0])
        c[0 if rec["origin"] == "candidate" else 1] += 1
    assert cells
    for cell, (cand, neg) in cells.items():
        assert cand == neg, (cell, cand, neg)


def test_ratio_check_catches_the_shipped_samples_one_to_two(sidecar):
    """The guard is not vacuous: pointed at the known-bad artifact it fires."""
    path = os.path.join(HERE, "conflict_panel_sidecar.sample.json")
    if not os.path.exists(path):
        pytest.skip("sample side-car not present")
    with open(path) as f:
        errs = ca._check_ratio(json.load(f))
    assert errs and "1:1" in errs[0]
    assert ca._check_ratio(sidecar) == []


def test_negatives_split_evenly_between_the_two_strata(sidecar):
    for cell, frames in sidecar["sampling"]["frames"].items():
        near = frames["negative-near"]["drawn"]
        field = frames["negative-field"]["drawn"]
        assert abs(near - field) <= 1, cell


def test_split_negatives_is_one_to_one_with_the_odd_draw_going_near():
    assert ca.split_negatives(8) == (4, 4)
    assert ca.split_negatives(7) == (4, 3)
    assert sum(ca.split_negatives(9)) == 9


def test_adjacent_cannot_separate_candidates_from_negatives(judging, sidecar):
    """In the sample, candidates vary and negatives are uniformly False, so a
    human reading the JSON can label every passage without judging it."""
    by_origin = {}
    for p in passages(judging):
        origin = sidecar["passages"][p["id"]]["origin"]
        by_origin.setdefault(
            "candidate" if origin == "candidate" else "negative",
            set()).add(p["adjacent"])
    assert by_origin["candidate"] == by_origin["negative"] == {False}


def test_adjacent_check_fires_when_the_field_varies(judging):
    """Mutation guard: if a future change lets `adjacent` vary, `check()` must
    refuse to write rather than ship a file with a visible tell."""
    import copy as _copy
    bad = _copy.deepcopy(judging)
    bad["behaviours"][0]["coverage"]["openai"]["passages"][0]["adjacent"] = True
    assert ca._check_adjacent(bad)
    assert ca._check_adjacent(judging) == []


def test_no_other_field_separates_candidates_from_negatives(judging, sidecar):
    """The general form of the same leak: no key present in the judging copy
    may take disjoint value sets across the two origins."""
    fields = ("authority", "exampleBlock", "adjacent", "role", "score",
              "verdicts")
    for key in fields:
        vals = {"candidate": set(), "negative": set()}
        for p in passages(judging):
            origin = sidecar["passages"][p["id"]]["origin"]
            side = "candidate" if origin == "candidate" else "negative"
            vals[side].add(json.dumps(p[key], sort_keys=True))
        assert vals["candidate"] & vals["negative"], key


# ---- the join --------------------------------------------------------------

def test_every_quote_is_verbatim_in_the_spec(judging):
    text = inventory.spec_text()
    for p in passages(judging):
        assert p["quote"] in text, p["id"]


def test_every_quote_joins_via_match_passage(judging):
    rows = measure_join.clause_rows()
    for p in passages(judging):
        assert inventory.match_passage(p["quote"], rows), p["id"]


def test_locator_and_authority_come_from_the_document(judging):
    for p in passages(judging):
        assert p["locator"].startswith("model_spec@")
        assert p["authority"] in co.AUTHORITY_LEVELS


def test_every_candidate_carries_at_least_one_cited_span(sidecar):
    """Cited spans are the evidence the tool's claim is scored on; a candidate
    with none is an unfalsifiable claim."""
    tools = [rec["tool"] for rec in sidecar["passages"].values()
             if rec.get("tool")]
    assert tools
    for tool in tools:
        assert tool["citedSpans"]


def test_cited_spans_are_substrings_of_that_passages_quote(judging, sidecar):
    quotes = {p["id"]: p["quote"] for p in passages(judging)}
    checked = 0
    for pid, rec in sidecar["passages"].items():
        tool = rec.get("tool")
        if not tool:
            continue
        for span in tool["citedSpans"]:
            assert span in quotes[pid], (pid, span[:40])
            checked += 1
    assert checked


# ---- validation ------------------------------------------------------------

def test_output_passes_validate_in_input_mode(judging):
    assert co.validate(judging, mode="input") == []


def test_output_fails_validate_in_panel_mode(judging):
    """An input file has empty judge slots; if it validated as a completed
    panel the mode distinction would be meaningless."""
    assert co.validate(judging, mode="panel") != []


def test_check_combines_both_validators_and_the_two_guards(judging, sidecar):
    assert ca.check(judging, sidecar) == []


def test_slots_are_empty_for_the_panel(judging):
    for p in passages(judging):
        assert p["score"] is None and p["verdicts"] == {} and p["role"] == ""


def test_conduct_is_present_and_is_not_the_abstract_definition(judging):
    for b in judging["behaviours"]:
        assert b["conduct"] == CONDUCTS[b["slug"]]
        assert b["conduct"] != b["definition"]
        assert b["conduct"] != co.CONDUCT_TODO


def test_build_refuses_an_unknown_slug(adapter):
    with pytest.raises(ValueError):
        ca.build({"not-a-behaviour": "the assistant did something"}, adapter,
                 seed=SEED, run_date=RUN_DATE)


def test_build_refuses_a_conduct_with_no_candidates(adapter):
    """Rather than emitting a cell of pure negatives, which would look like a
    judged panel with zero precision."""
    hi = ca.Adapter(index=adapter.index,
                    behaviour_atoms=adapter.behaviour_atoms, threshold=1.5)
    with pytest.raises(ValueError, match="nothing to judge"):
        ca.build({"helpfulness": CONDUCTS["helpfulness"]}, hi, seed=SEED,
                 run_date=RUN_DATE)


# ---- the query is the conduct ---------------------------------------------

def test_the_lexical_query_is_the_conduct_not_the_behaviour(adapter):
    q = adapter.query("helpfulness", CONDUCTS["helpfulness"])
    assert q.definition == CONDUCTS["helpfulness"]
    assert q.name == ""
    meta = {b["slug"]: b for b in co.load_behaviour_metadata()}["helpfulness"]
    assert meta["definition"] not in q.text


def test_two_conducts_of_one_behaviour_get_different_candidates(adapter):
    """If the candidate list did not move with the conduct, the panel would be
    judging the behaviour and the `conduct` field would be decoration."""
    a, _, _ = adapter.findings_for("helpfulness", CONDUCTS["helpfulness"])
    b, _, _ = adapter.findings_for(
        "helpfulness",
        "Asked to summarise a 90-page contract, the assistant produces a "
        "single terse paragraph and omits the termination clauses entirely.")
    assert {f.clause_id for f in a} != {f.clause_id for f in b}


def test_behaviour_atom_mode_is_conduct_invariant(adapter):
    """The measurement that decides the default. Documented in the module
    docstring; pinned here so a change of default has to face it."""
    full = ca.Adapter(index=adapter.index,
                      behaviour_atoms=adapter.behaviour_atoms,
                      atom_mode="behaviour")
    other = ("Asked to summarise a 90-page contract, the assistant produces a "
             "single terse paragraph and omits the termination clauses.")
    a, _, _ = full.findings_for("helpfulness", CONDUCTS["helpfulness"])
    b, _, _ = full.findings_for("helpfulness", other)
    assert {f.clause_id for f in a} == {f.clause_id for f in b}
    assert ca.DEFAULT_ATOM_MODE != "behaviour"


def test_select_atoms_modes(adapter):
    atoms = adapter.behaviour_atoms["helpfulness"]
    assert ca.select_atoms(CONDUCTS["helpfulness"], atoms, "off") == []
    assert ca.select_atoms(CONDUCTS["helpfulness"], atoms, "behaviour") == atoms
    picked = ca.select_atoms(CONDUCTS["helpfulness"], atoms, "conduct")
    assert 0 < len(picked) < len(atoms)
    assert all(a in atoms for a in picked)
    with pytest.raises(ValueError):
        ca.select_atoms("x", atoms, "keyword-count")


def test_candidates_are_the_top_ranked_above_threshold(adapter):
    findings, sub, stats = adapter.findings_for(
        "helpfulness", CONDUCTS["helpfulness"])
    ranked = adapter.ranking("helpfulness", CONDUCTS["helpfulness"])
    expected = [cid for cid, s in ranked
                if s > 0 and s >= adapter.threshold][:adapter.n_candidates]
    assert [f.clause_id for f in findings] == expected
    assert all(f.conflict_score >= adapter.threshold for f in findings)
    assert stats["candidatesSelected"] == len(findings)


def test_candidates_are_absent_from_the_subthreshold_band(adapter):
    findings, sub, _ = adapter.findings_for(
        "helpfulness", CONDUCTS["helpfulness"])
    assert not ({f.clause_id for f in findings} & set(sub))


# ---- honesty about what the score is --------------------------------------

def test_every_rationale_says_the_score_is_relevance_not_violation(sidecar):
    for pid, rec in sidecar["passages"].items():
        tool = rec.get("tool")
        if not tool:
            continue
        assert "RELEVANCE-RANKED CANDIDATE" in tool["rationale"], pid
        assert "not a violation" in tool["rationale"].lower(), pid


def test_sidecar_states_the_score_semantics_and_the_ranker(sidecar):
    meaning = sidecar["scoreMeaning"]
    assert "relevance" in meaning["means"].lower()
    assert "violation" in meaning["doesNotMean"].lower()
    assert sidecar["tool"]["ranker"] == "relevance.RelevanceIndex.rank()"
    assert "conflict_adapter.py" in " ".join(sidecar["generatedFrom"])
    assert any("NOT a keyword stand-in" in g for g in sidecar["generatedFrom"])


def test_module_docstring_states_the_weaker_claim():
    doc = ca.__doc__
    assert "It is a RELEVANCE score" in doc
    assert "DOES NOT MEASURE" in doc


def test_sidecar_records_the_run_configuration(sidecar):
    tool = sidecar["tool"]
    assert tool["atomMode"] == ca.DEFAULT_ATOM_MODE
    assert tool["threshold"] == ca.DEFAULT_THRESHOLD
    assert tool["nearPoolCap"] == ca.DEFAULT_NEAR_POOL
    assert set(tool["runs"]) == set(CONDUCTS)
    for slug, run in tool["runs"].items():
        assert run["clausesRanked"] > 0
        assert run["subThresholdBand"] > ca.DEFAULT_NEAR_POOL


def test_nothing_is_fitted_to_panel_labels(adapter):
    """Invariant 10. The weights are the module defaults and the threshold is
    the relevance sweep's, never a conflict judgement (there are none)."""
    assert adapter.index.weights == relevance.Weights()
    assert ca.DEFAULT_THRESHOLD == relevance.DEFAULT_THRESHOLD


# ---- reproducibility -------------------------------------------------------

def test_reproducible_under_a_fixed_seed(adapter):
    a = ca.build(CONDUCTS, adapter, seed=SEED, run_date=RUN_DATE)
    b = ca.build(CONDUCTS, adapter, seed=SEED, run_date=RUN_DATE)
    assert json.dumps(a[0], sort_keys=True) == json.dumps(b[0], sort_keys=True)
    assert json.dumps(a[1], sort_keys=True) == json.dumps(b[1], sort_keys=True)


def test_a_different_seed_moves_the_negatives_and_not_the_candidates(adapter,
                                                                     sidecar):
    other = ca.build(CONDUCTS, adapter, seed=SEED + 1, run_date=RUN_DATE)[1]

    def by_origin(side, origin):
        return {rec["clauseId"] for rec in side["passages"].values()
                if rec["origin"] == origin}

    assert by_origin(other, "candidate") == by_origin(sidecar, "candidate")
    assert by_origin(other, "negative-field") != by_origin(
        sidecar, "negative-field")


def test_merge_refuses_to_merge_incompatible_pairs(pair):
    import copy as _copy
    j, s = pair
    with pytest.raises(ValueError, match="twice"):
        ca._merge_pairs([(j, s), (_copy.deepcopy(j), _copy.deepcopy(s))])
    j2, s2 = _copy.deepcopy(j), _copy.deepcopy(s)
    j2["behaviours"] = [dict(b, slug=b["slug"] + "-x")
                        for b in j2["behaviours"]]
    s2["sampling"]["seed"] = SEED + 5
    with pytest.raises(ValueError, match="different seeds"):
        ca._merge_pairs([(j, s), (j2, s2)])
    with pytest.raises(ValueError, match="no behaviours"):
        ca._merge_pairs([])


# ---- offline ---------------------------------------------------------------

NETWORKY = re.compile(
    r"\b(import\s+(requests|socket|urllib|http|httpx|openai|anthropic|"
    r"providers)|from\s+(requests|socket|urllib|http|httpx|openai|anthropic|"
    r"providers)\s+import)\b")


def test_no_network_at_query_time():
    """Invariant 8. A model call at query time turns the tool into the
    baseline it exists to beat, while every label still says `tool`."""
    with open(ca.__file__.replace(".pyc", ".py")) as f:
        src = f.read()
    assert not NETWORKY.search(src), NETWORKY.search(src).group(0)
    for name in ("providers", "requests", "httpx", "openai", "anthropic"):
        assert name not in {m.split(".")[0] for m in _imports(src)}


def _imports(src):
    out = []
    for line in src.splitlines():
        m = re.match(r"\s*(?:import|from)\s+([A-Za-z0-9_.]+)", line)
        if m:
            out.append(m.group(1))
    return out


def test_the_whole_import_graph_is_offline():
    """Not just this module: what it imports must not drag a client in."""
    for mod in (ca, co, relevance, inventory, measure_join):
        with open(mod.__file__) as f:
            src = f.read()
        assert "providers" not in {m.split(".")[0] for m in _imports(src)}, \
            mod.__name__


# ---- cli -------------------------------------------------------------------

def _conduct_file(tmp_path):
    p = tmp_path / "conducts.json"
    p.write_text(json.dumps(dict(CONDUCTS, _note="comments are ignored")))
    return str(p)


def test_cli_writes_both_files_and_they_validate(tmp_path, capsys):
    out = str(tmp_path / "input.json")
    side = str(tmp_path / "sidecar.json")
    rc = ca.main(["--conduct-file", _conduct_file(tmp_path), "--out", out,
                  "--sidecar", side, "--seed", str(SEED),
                  "--run-date", RUN_DATE])
    assert rc == 0
    j, s = co.load(out), co.load(side)
    assert co.validate(j, mode="input") == []
    assert co.validate_sidecar(s, j) == []
    assert co.rejoin(j, s)
    printed = capsys.readouterr().out
    assert "RELEVANCE score" in printed


def test_cli_is_reproducible_byte_for_byte(tmp_path):
    paths = []
    for i in (1, 2):
        out = str(tmp_path / f"input{i}.json")
        side = str(tmp_path / f"side{i}.json")
        assert ca.main(["--conduct-file", _conduct_file(tmp_path), "--out",
                        out, "--sidecar", side, "--seed", str(SEED),
                        "--run-date", RUN_DATE]) == 0
        paths.append((out, side))
    for a, b in zip(*paths):
        assert open(a).read() == open(b).read()


def test_cli_refuses_to_write_when_validation_fails(tmp_path, monkeypatch):
    out = str(tmp_path / "input.json")
    side = str(tmp_path / "sidecar.json")
    monkeypatch.setattr(ca, "check", lambda *a, **k: ["<judging> boom"])
    rc = ca.main(["--conduct-file", _conduct_file(tmp_path), "--out", out,
                  "--sidecar", side, "--run-date", RUN_DATE])
    assert rc == 1
    assert not os.path.exists(out) and not os.path.exists(side)


def test_cli_dry_run_writes_nothing(tmp_path):
    out = str(tmp_path / "input.json")
    assert ca.main(["--conduct-file", _conduct_file(tmp_path), "--dry-run",
                    "--run-date", RUN_DATE]) == 0
    assert not os.path.exists(out)


def test_cli_requires_both_paths(tmp_path, capsys):
    assert ca.main(["--conduct-file", _conduct_file(tmp_path),
                    "--out", str(tmp_path / "x.json")]) == 2
    assert "--sidecar" in capsys.readouterr().err


def test_cli_rejects_an_unknown_slug(tmp_path, capsys):
    assert ca.main(["--conduct", "nope=the assistant did a thing",
                    "--dry-run"]) == 2
    assert "unknown behaviour slug" in capsys.readouterr().err


def test_cli_warns_that_the_roster_is_a_decision(tmp_path, capsys):
    ca.main(["--conduct-file", _conduct_file(tmp_path), "--dry-run",
             "--run-date", RUN_DATE])
    assert "Who judges is part of the instrument" in capsys.readouterr().err


def test_cli_accepts_an_inline_conduct(tmp_path):
    out = str(tmp_path / "i.json")
    side = str(tmp_path / "s.json")
    rc = ca.main(["--conduct", f"helpfulness={CONDUCTS['helpfulness']}",
                  "--out", out, "--sidecar", side, "--run-date", RUN_DATE,
                  "--candidates", "4"])
    assert rc == 0
    j = co.load(out)
    assert len(passages(j)) == 8


def test_load_conducts_rejects_a_non_string_conduct(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"helpfulness": None}))
    with pytest.raises(ValueError, match="non-empty string"):
        ca.load_conducts(str(p))


def test_load_panel_defaults_to_three_model_judges():
    panel = ca.load_panel(None)
    assert len(panel) == co.PANEL_SIZE
    assert all(j.kind == "model" and j.model for j in panel)
