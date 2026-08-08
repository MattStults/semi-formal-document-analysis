"""Tests for `eval.py` — written before it exists.

    ../../../semi-formal-experiment/.venv/bin/python -m pytest \
        walkthrough/paper_pipeline/phase_1/test_eval.py -q

`eval.py` exists to make a prompt change ARGUABLE instead of plausible. Every
test below pins one of the ways a harness like that reports a number that means
nothing:

  * it reports a before/after with no idea how big the run-to-run noise is
    (temperature is 0.2 — the same prompt twice is two different results);
  * it scores the REPAIRED module, so a good repair loop launders a bad prompt;
  * it clusters findings by `check_id`, which is `schema-breach` for every
    schema failure, so every distinct cause lands in one bucket;
  * it compares two arms that are secretly the same prompt and reports
    "no significant difference";
  * it forgets which clauses it ran on, so nobody can check the eval set was
    not the diagnosis set.

⛔ NOTHING HERE SPENDS. Every model call goes through a stub `client_factory` —
the same seam `translate.run` already exposes for its own self-test.
"""

import json
import shutil
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import checks  # noqa: E402
import eval as E  # noqa: E402  (a module named `eval`; the builtin is a function)
import fixtures  # noqa: E402


# ==========================================================================
#  Stubs and fixtures
# ==========================================================================

CLAUSES = ["m0014", "m0036"]


class StubClient:
    """A scripted transport that RECORDS what it was asked.

    `script` is a callable `(system, user, n) -> text`, so an arm can return a
    different module per repeat — which is how the noise measurement is given
    something to measure.
    """

    def __init__(self, prov, cfg, script):
        self.script, self.calls = script, []
        self.spent_usd, self.n = 0.0, 0

    def complete(self, system, user):
        self.n += 1
        self.calls.append((system, user))
        return {"text": self.script(system, user, self.n), "in": 10, "out": 10}

    def complete_messages(self, system, messages):
        raise AssertionError(
            "eval.py asked for a repair turn. It measures the FIRST attempt: a "
            "repair loop in the harness hides the prompt defect being measured")


def good(cid, **over):
    """A module the checks accept, for clause `cid`."""
    return fixtures.module_json(clause_id=cid, **over)


def rule_in_atom_slot(cid):
    """`schema-breach`: a whole rule written into a slot holding one term."""
    return fixtures.module_json(clause_id=cid, ontology=[dict(
        atom=f"disallowed_{cid}(M) :- restricted(M)", gloss="g", body=None,
        licence="assumed", cites=None, inference="a step", toggleable=False)])


def readback_slot_mismatch(cid):
    """`schema-breach`: the read-back's `%` count does not match its slots."""
    return fixtures.module_json(clause_id=cid, asserts=[fixtures.assertion(
        read_back="producing this is forbidden", read_back_slots=["M"])])


def _abs_config(tmp_path, name, prompt_dir=None, **over):
    """A copy of `config.json` with every relative path made absolute.

    ⚠️ `translate.rel()` resolves against the config's OWN directory, so a
    config copied elsewhere would otherwise read a corpus and a prompt set that
    are not there. Absolutising is what lets a test build two arms without
    touching the real config.
    """
    cfg = json.loads((HERE / "config.json").read_text())
    cfg["corpus"]["path"] = str((HERE / cfg["corpus"]["path"]).resolve())
    cfg["model"]["providers_json"] = str(
        (HERE / cfg["model"]["providers_json"]).resolve())
    base = Path(prompt_dir) if prompt_dir else HERE
    cfg["prompt"]["system_files"] = [
        str((base / Path(f).name).resolve()) if prompt_dir
        else str((HERE / f).resolve())
        for f in cfg["prompt"]["system_files"]]
    cfg["output"]["dir"] = str(tmp_path / "runs")
    for k, v in over.items():
        cfg[k] = {**cfg.get(k, {}), **v} if isinstance(v, dict) else v
    path = tmp_path / name
    path.write_text(json.dumps(cfg))
    return str(path)


def _edited_prompt_dir(tmp_path, name="prompt_b"):
    """The real prompt set, changed by a sentinel line. Arm B.

    ⛔ THE EDIT MUST NOT DEPEND ON WHAT THE PROMPT SAYS. This deleted a named
    sentence from `00_task.md` until someone deleted that sentence from the
    prompt for real — the replace became a no-op, both arms went byte-identical
    and three tests failed. `assert_arms_differ` was right; the fixture was
    wrong. Appending changes the bytes whatever the file happens to contain.
    """
    d = tmp_path / name
    d.mkdir()
    for f in (HERE / "prompt").glob("*.md"):
        shutil.copy(f, d / f.name)
    task = d / "00_task.md"
    task.write_text(task.read_text() + "\n<!-- arm B sentinel -->\n")
    return d


def _findings(msgs, check_id=checks.SCHEMA_CHECK_ID, where="<root>"):
    return [checks.Finding(check_id, "error", where, m, "schema") for m in msgs]


# ==========================================================================
#  1.  Clustering — by NORMALISED MESSAGE, never by check_id
# ==========================================================================

def test_clustering_separates_the_two_schema_breaches_the_brief_names():
    """⭐ The sanity check the brief demands, run against REAL check output.

    A read-back slot mismatch and a rule written into an atom slot are both
    `check_id == "schema-breach"`. Clustering on the id reports one cause where
    there are two, and the whole point of the report is to rank causes.
    """
    clause = {"id": "m0001", "quote": "Clause text.", "section_id": "s",
              "kind": "conditional"}
    a = checks.run_checks(json.loads(rule_in_atom_slot("m0001")), clause,
                          {"m0001"}, attempt=1).findings
    b = checks.run_checks(json.loads(readback_slot_mismatch("m0001")), clause,
                          {"m0001"}, attempt=1).findings
    assert {f.check_id for f in a + b} == {checks.SCHEMA_CHECK_ID}, \
        "precondition: both are schema-breach, so check_id cannot separate them"

    clusters = E.cluster_findings(a + b)
    assert len(clusters) == 2, [c.key for c in clusters]


def test_clustering_MERGES_one_cause_across_different_clauses():
    """The signal is about the prompt, not about a clause.

    The rule-in-a-term-slot message interpolates the offending term with
    `{term!r}` — SINGLE QUOTES, not backticks. Normalising backticks alone
    leaves this cause fragmented one-cluster-per-clause, which is exactly the
    shared cause `PROPOSAL_graveyard.md` found by hand across two clauses.
    """
    clause_a = {"id": "m0001", "quote": "A.", "section_id": "s",
                "kind": "conditional"}
    clause_b = {"id": "m0002", "quote": "B.", "section_id": "s",
                "kind": "conditional"}
    fa = checks.run_checks(json.loads(rule_in_atom_slot("m0001")), clause_a,
                           {"m0001"}, attempt=1).findings
    fb = checks.run_checks(json.loads(rule_in_atom_slot("m0002")), clause_b,
                           {"m0002"}, attempt=1).findings
    assert {f.message for f in fa} != {f.message for f in fb}, \
        "precondition: the raw messages differ, or there is nothing to merge"

    clusters = E.cluster_findings(fa + fb)
    assert len(clusters) == 1, [c.key for c in clusters]
    assert clusters[0].count == 2


def test_normalisation_erases_tempdir_paths_and_line_numbers():
    """`clingo-error` embeds the temp `.lp` path stage 2 rendered to.

    That path is new on every single run, so without this every clingo failure
    is its own cluster and the commonest hard failure is invisible in the rank.
    """
    one = ("/var/folders/jh/T/stage2_checks_abc/m0134.lp:39:1-75: error: "
           "unsafe variables in:")
    two = ("/var/folders/jh/T/stage2_checks_xyz/m0221.lp:41:1-77: error: "
           "unsafe variables in:")
    assert E.normalise_message(one) == E.normalise_message(two)


def test_clusters_are_RANKED_and_carry_a_verbatim_example():
    """A rank with no example is unactionable; an example with no count is an
    anecdote. Both, or the report is not a report."""
    fs = _findings(["cause A number 1", "cause A number 2", "cause B"])
    clusters = E.cluster_findings(fs)
    assert [c.count for c in clusters] == [2, 1]
    assert clusters[0].example in {"cause A number 1", "cause A number 2"}


# ==========================================================================
#  2.  ⭐ First-attempt only
# ==========================================================================

def test_the_harness_never_repairs(tmp_path):
    """⭐ The prompt's report card is what it produces before anyone tells it
    anything. `StubClient.complete_messages` raises if a repair turn is asked
    for, and one call per clause per repeat is the whole budget."""
    cfg_path = _abs_config(tmp_path, "a.json")
    arm = E.load_arm("A", cfg_path, CLAUSES)
    seen = []

    def factory(prov, cfg):
        c = StubClient(prov, cfg, lambda s, u, n: rule_in_atom_slot(
            CLAUSES[(n - 1) % len(CLAUSES)]))
        seen.append(c)
        return c

    E.run_arm(arm, repeats=2, client_factory=factory)
    assert sum(c.n for c in seen) == len(CLAUSES) * 2


def test_findings_are_read_off_attempt_1(tmp_path):
    """A first attempt that breaches must be counted as a breach even though a
    repair would have cleared it. The `attempt` field says which attempt the
    finding set belongs to, and it is 1."""
    cfg_path = _abs_config(tmp_path, "a.json")
    arm = E.load_arm("A", cfg_path, CLAUSES)
    res = E.run_arm(arm, repeats=1, client_factory=lambda p, c: StubClient(
        p, c, lambda s, u, n: readback_slot_mismatch(
            CLAUSES[(n - 1) % len(CLAUSES)])))
    outcomes = res.repeats[0].clauses
    assert [o.attempt for o in outcomes] == [1, 1]
    assert all(o.errors for o in outcomes)


def test_clean_rate_counts_clauses_with_zero_ERROR_findings(tmp_path):
    """`requires-unprovided` is a NOTE and fires on every correct module this
    pipeline emits (`checks.py` severity ruling). A clean rate that counted
    notes would read 0% on a perfect run."""
    cfg_path = _abs_config(tmp_path, "a.json")
    arm = E.load_arm("A", cfg_path, CLAUSES)
    res = E.run_arm(arm, repeats=1, client_factory=lambda p, c: StubClient(
        p, c, lambda s, u, n: good(CLAUSES[(n - 1) % len(CLAUSES)])))
    m = res.repeats[0].metrics
    assert m["first_attempt_clean_rate"] == 1.0
    assert m["error_findings_per_clause"] == 0.0
    assert m["findings_per_clause"] > 0.0, \
        "the notes are still counted and reported; they just do not fail a clause"


# ==========================================================================
#  3.  ⭐ Noise — the default mode, and the number that makes an A/B readable
# ==========================================================================

def test_repeats_of_the_SAME_prompt_report_a_spread(tmp_path):
    """⭐ The first thing the harness must do. Two repeats of one prompt that
    disagree must produce a non-zero spread, or a later A/B has no yardstick."""
    cfg_path = _abs_config(tmp_path, "a.json")
    arm = E.load_arm("A", cfg_path, CLAUSES)
    # repeat 1: both clauses clean. repeat 2: both breach.
    res = E.run_arm(arm, repeats=2, client_factory=lambda p, c: StubClient(
        p, c, lambda s, u, n: (good if n <= 2 else readback_slot_mismatch)(
            CLAUSES[(n - 1) % len(CLAUSES)])))
    sp = res.spread["first_attempt_clean_rate"]
    assert sp["n"] == 2
    assert sp["mean"] == pytest.approx(0.5)
    assert sp["sd"] > 0.0
    assert (sp["min"], sp["max"]) == (0.0, 1.0)


def test_a_single_repeat_reports_UNKNOWN_spread_not_zero(tmp_path):
    """One sample has no spread. Reporting 0.0 would make a single before/after
    read as noise-free, which is the claim this harness exists to refuse."""
    cfg_path = _abs_config(tmp_path, "a.json")
    arm = E.load_arm("A", cfg_path, CLAUSES)
    res = E.run_arm(arm, repeats=1, client_factory=lambda p, c: StubClient(
        p, c, lambda s, u, n: good(CLAUSES[(n - 1) % len(CLAUSES)])))
    assert res.spread["first_attempt_clean_rate"]["sd"] is None


# ==========================================================================
#  4.  ⛔ Two arms that are the same prompt is an ERROR, never a null result
# ==========================================================================

def test_identical_arms_are_an_ERROR(tmp_path):
    """A harness that reports "no significant difference" because it never
    varied anything is the failure mode this whole file is designed against."""
    a = _abs_config(tmp_path, "a.json")
    b = _abs_config(tmp_path, "b.json")          # different file, same content
    arm_a, arm_b = E.load_arm("A", a, CLAUSES), E.load_arm("B", b, CLAUSES)
    with pytest.raises(E.IdenticalArmsError):
        E.assert_arms_differ(arm_a, arm_b)


def test_arms_whose_PROMPT_TEXT_differs_are_accepted(tmp_path):
    """The comparison is over the prompt bytes, not the config filename."""
    a = _abs_config(tmp_path, "a.json")
    b = _abs_config(tmp_path, "b.json",
                    prompt_dir=_edited_prompt_dir(tmp_path))
    arm_a, arm_b = E.load_arm("A", a, CLAUSES), E.load_arm("B", b, CLAUSES)
    assert arm_a.inputs_sha != arm_b.inputs_sha
    E.assert_arms_differ(arm_a, arm_b)           # must not raise


def test_identical_arms_exit_2_from_the_command_line(tmp_path, capsys):
    """And loudly. Exit 0 with a null result is the outcome to prevent."""
    a = _abs_config(tmp_path, "a.json")
    b = _abs_config(tmp_path, "b.json")
    code = E.main(["--config", a, "--compare", b,
                   "--clauses", ",".join(CLAUSES)])
    assert code == 2
    assert "IDENTICAL" in capsys.readouterr().out.upper()


# ==========================================================================
#  5.  ⚠️ The held-out clause set is RECORDED, always
# ==========================================================================

def test_the_eval_set_is_recorded_in_the_output(tmp_path):
    """A prompt change validated on the clauses that motivated it is fitting.
    A later reader can only check that if the run says which clauses it used."""
    cfg_path = _abs_config(tmp_path, "a.json")
    arm = E.load_arm("A", cfg_path, CLAUSES)
    res = E.run_arm(arm, repeats=1, client_factory=lambda p, c: StubClient(
        p, c, lambda s, u, n: good(CLAUSES[(n - 1) % len(CLAUSES)])))
    rep = E.build_report([res], CLAUSES, source="--clauses")
    assert rep["eval_set"]["clause_ids"] == CLAUSES
    assert rep["eval_set"]["source"] == "--clauses"
    assert rep["eval_set"]["n"] == 2


def test_a_report_with_no_clause_set_REFUSES(tmp_path):
    """Recording is mandatory, not best-effort."""
    cfg_path = _abs_config(tmp_path, "a.json")
    arm = E.load_arm("A", cfg_path, CLAUSES)
    res = E.run_arm(arm, repeats=1, client_factory=lambda p, c: StubClient(
        p, c, lambda s, u, n: good(CLAUSES[(n - 1) % len(CLAUSES)])))
    with pytest.raises(E.EvalError):
        E.build_report([res], [], source="--clauses")


def test_no_clause_set_on_the_command_line_is_a_usage_error(tmp_path, capsys):
    cfg_path = _abs_config(tmp_path, "a.json")
    assert E.main(["--config", cfg_path]) == 2
    assert "clause" in capsys.readouterr().out.lower()


# ==========================================================================
#  6.  Per-change metrics — the licence one, and the registry
# ==========================================================================

def test_licence_metric_counts_assumed_world_and_unresolved_citations(tmp_path):
    """⭐ The first real use. Deleting the licence sentence from `00_task.md`
    should not move the pass rate — its claim is about LICENCES."""
    cfg_path = _abs_config(tmp_path, "a.json")
    arm = E.load_arm("A", cfg_path, CLAUSES)
    # The canonical module: 1 ontology fact `assumed`, 1 assertion `textual`
    # citing m0001 (which is in the corpus).
    res = E.run_arm(arm, repeats=1, metrics=["licences"],
                    client_factory=lambda p, c: StubClient(
                        p, c, lambda s, u, n: good(
                            CLAUSES[(n - 1) % len(CLAUSES)])))
    m = res.repeats[0].metrics
    assert m["non_textual_fact_rate"] == pytest.approx(0.5)
    assert m["assumed_fact_rate"] == pytest.approx(0.5)
    assert m["world_fact_rate"] == 0.0
    assert m["unresolved_citation_rate"] == 0.0


def test_licence_metric_catches_a_citation_that_resolves_to_nothing(tmp_path):
    """A manufactured citation looks exactly like a real one in the module."""
    cfg_path = _abs_config(tmp_path, "a.json")
    arm = E.load_arm("A", cfg_path, CLAUSES)
    res = E.run_arm(arm, repeats=1, metrics=["licences"],
                    client_factory=lambda p, c: StubClient(
                        p, c, lambda s, u, n: good(
                            CLAUSES[(n - 1) % len(CLAUSES)],
                            asserts=[fixtures.assertion(
                                licence="textual", cites="m9999",
                                inference=None, toggleable=False)])))
    assert res.repeats[0].metrics["unresolved_citation_rate"] == 1.0


def test_licence_rates_of_zero_are_distinguishable_from_NOTHING_MEASURED(
        tmp_path):
    """⛔ Found by replaying two real runs. A module that fails the schema does
    not construct, carries no licensed items, and every licence rate reads
    0.0000 — which looks exactly like "the model wrote no assumed facts". All
    three first attempts in that replay were unbuildable. The count is what
    tells the two apart, so it is part of the metric."""
    cfg_path = _abs_config(tmp_path, "a.json")
    arm = E.load_arm("A", cfg_path, CLAUSES)
    res = E.run_arm(arm, repeats=1, metrics=["licences"],
                    client_factory=lambda p, c: StubClient(
                        p, c, lambda s, u, n: rule_in_atom_slot(
                            CLAUSES[(n - 1) % len(CLAUSES)])))
    m = res.repeats[0].metrics
    assert m["unbuildable_rate"] == 1.0
    assert m["non_textual_fact_rate"] == 0.0
    assert m["licence_modules_scored"] == 0.0, \
        "0.0 rates with no count beside them are unreadable"


def test_adding_a_metric_is_one_registration(tmp_path):
    """"Make adding another a small edit, not a redesign." One decorator."""
    assert "licences" in E.METRICS and "findings" in E.METRICS
    try:
        @E.metric("smoke")
        def _smoke(outcomes, arm):
            return {"n_clauses_seen": float(len(outcomes))}

        cfg_path = _abs_config(tmp_path, "a.json")
        arm = E.load_arm("A", cfg_path, CLAUSES)
        res = E.run_arm(arm, repeats=1, metrics=["smoke"],
                        client_factory=lambda p, c: StubClient(
                            p, c, lambda s, u, n: good(
                                CLAUSES[(n - 1) % len(CLAUSES)])))
        assert res.repeats[0].metrics["n_clauses_seen"] == 2.0
    finally:
        E.METRICS.pop("smoke", None)


def test_an_unknown_metric_name_REFUSES(tmp_path):
    cfg_path = _abs_config(tmp_path, "a.json")
    with pytest.raises(E.EvalError):
        E.load_metrics(["licences", "nope"])


# ==========================================================================
#  7.  Cost — dry run by default, estimate printed, --live required
# ==========================================================================

def test_dry_run_sends_NOTHING_and_prints_the_estimate(tmp_path, capsys):
    def refuse(prov, cfg):
        raise AssertionError("a dry run built a client")

    code = E.main(["--config", _abs_config(tmp_path, "a.json"),
                   "--clauses", ",".join(CLAUSES), "--repeats", "3"],
                  client_factory=refuse)
    out = capsys.readouterr().out
    assert code == 0
    assert "DRY RUN" in out
    assert "$" in out and "repeats" in out.lower()


def test_the_LIVE_cli_path_runs_end_to_end(tmp_path, capsys):
    """⚠️ Nothing else exercises `print_report` or `--out`, and a formatting
    error there would surface for the first time on a run that cost money. It
    already did: the spend line summed `client.calls`, which is an int on a
    real `Client` and a list of sent messages on a stub."""
    a = _abs_config(tmp_path, "a.json")
    b = _abs_config(tmp_path, "b.json",
                    prompt_dir=_edited_prompt_dir(tmp_path))
    out = tmp_path / "report.json"
    code = E.main(["--config", a, "--compare", b, "--live",
                   "--clauses", ",".join(CLAUSES), "--repeats", "3",
                   "--metric", "licences", "--out", str(out)],
                  client_factory=lambda p, c: StubClient(
                      p, c, lambda s, u, n: (
                          good if n % 3 else readback_slot_mismatch)(
                              CLAUSES[(n - 1) % len(CLAUSES)])))
    assert code == 0
    printed = capsys.readouterr().out
    assert "NOISE" in printed and "B minus A" in printed
    rep = json.loads(out.read_text())
    assert rep["eval_set"]["clause_ids"] == CLAUSES
    assert set(rep["arms"]) == {"A", "B"} and "comparison" in rep

    # ⭐ Every paid call left its response on disk, beside the report. Nothing
    # asserted this before, and the first live run kept none of 36.
    raws = sorted(p.name for p in (tmp_path / "report_raw").rglob("*.raw.txt"))
    assert len(raws) == len(CLAUSES) * 3 * 2, (
        f"expected one raw per clause per repeat per arm, got {len(raws)}")
    assert (tmp_path / "report_raw" / "A" / "r3").is_dir()
    assert (tmp_path / "report_raw" / "B" / "r1").is_dir()


def test_the_estimate_scales_with_repeats_and_arms(tmp_path):
    """`--repeats 3` over two arms is six passes over the clause set. An
    estimate that priced one pass would understate a hard cap sixfold."""
    a = E.load_arm("A", _abs_config(tmp_path, "a.json"), CLAUSES)
    b = E.load_arm("B", _abs_config(tmp_path, "b.json",
                                    prompt_dir=_edited_prompt_dir(tmp_path)),
                   CLAUSES)
    one = E.estimate([a], repeats=1)
    six = E.estimate([a, b], repeats=3)
    assert six == pytest.approx(one * 6, rel=0.05)


def test_over_the_ceiling_REFUSES_before_anything_is_sent(tmp_path):
    """An unrepeatable run that costs money must not start."""
    cfg_path = _abs_config(tmp_path, "a.json", cost={"max_cost_usd": 0.0001})
    arm = E.load_arm("A", cfg_path, CLAUSES)
    with pytest.raises(E.EvalError):
        E.gate(E.estimate([arm], repeats=3), arm)


# ==========================================================================
#  8.  The comparison, once both arms have run
# ==========================================================================

def test_a_delta_inside_the_noise_is_reported_as_such(tmp_path):
    """The number the whole harness exists to produce: a delta, WITH the
    spread it has to beat."""
    a = E.load_arm("A", _abs_config(tmp_path, "a.json"), CLAUSES)
    b = E.load_arm("B", _abs_config(tmp_path, "b.json",
                                    prompt_dir=_edited_prompt_dir(tmp_path)),
                   CLAUSES)

    def flaky(prov, cfg):
        return StubClient(prov, cfg, lambda s, u, n: (
            good if n % 3 else readback_slot_mismatch)(
                CLAUSES[(n - 1) % len(CLAUSES)]))

    ra = E.run_arm(a, repeats=3, client_factory=flaky)
    rb = E.run_arm(b, repeats=3, client_factory=flaky)
    rep = E.build_report([ra, rb], CLAUSES, source="--clauses")
    row = rep["comparison"]["first_attempt_clean_rate"]
    assert "delta" in row and "within_noise" in row
    assert row["within_noise"] is True


# ==========================================================================
# Raw responses are the one thing a paid run cannot regenerate
# ==========================================================================

def test_raw_responses_are_written_for_every_paid_call(tmp_path):
    """⛔ The regression this pins: the first live eval made 36 paid calls and
    kept nothing but finding strings. The raw responses were captured in memory
    and dropped, so a question the report did not anticipate — what did the
    model actually write? — could only be answered by paying again.

    `translate.py` already treats this as non-negotiable ("the raw responses of
    a run that cost money are the one thing that cannot be regenerated").
    """
    outcomes = [
        E.ClauseOutcome("m0001", "valid", None, [], raw='{"a": 1}'),
        E.ClauseOutcome("m0002", "invalid", None, [], raw="not json at all"),
    ]
    root = tmp_path / "raws"
    E.persist_raw(str(root), "A", 1, outcomes)
    assert (root / "A" / "r1" / "m0001.raw.txt").read_text() == '{"a": 1}'
    assert (root / "A" / "r1" / "m0002.raw.txt").read_text() == "not json at all"


def test_raw_persistence_keeps_arms_and_repeats_apart(tmp_path):
    # Two arms writing the same clause id must not overwrite each other: the
    # whole point of the run is that A and B differ.
    root = tmp_path / "raws"
    for arm in ("A", "B"):
        for rep in (1, 2):
            E.persist_raw(str(root), arm, rep, [
                E.ClauseOutcome("m0001", "valid", None, [],
                                   raw=f"{arm}{rep}")])
    seen = {p.read_text() for p in root.rglob("*.raw.txt")}
    assert seen == {"A1", "A2", "B1", "B2"}


def test_a_provider_error_still_records_its_slot(tmp_path):
    # A failed call has no raw text, but MUST leave a trace: an absent file
    # would be indistinguishable from a clause that was never attempted.
    root = tmp_path / "raws"
    E.persist_raw(str(root), "A", 1, [
        E.ClauseOutcome("m0001", "error", None, [], raw="")])
    body = (root / "A" / "r1" / "m0001.raw.txt").read_text()
    assert body != "", "an empty file cannot be told from a call never made"
    assert "no response" in body.lower()


# ==========================================================================
#  The gloss metric — bad worked example #6
# ==========================================================================

class _C:
    def __init__(self, name, gloss): self.name, self.gloss = name, gloss


class _M:
    def __init__(self, concepts): self.concepts = concepts


def _out(concepts):
    o = E.ClauseOutcome("m0001", "translated", _M(concepts), [])
    return o


def test_a_gloss_that_only_restates_the_name_counts_as_empty():
    m = E.gloss_metric([_out([_C("terrorism_act", "an act of terrorism")])], None)
    assert m["empty_gloss_rate"] == 1.0
    assert m["gloss_concepts_scored"] == 1.0


def test_a_gloss_that_adds_content_does_not_count():
    m = E.gloss_metric([_out([_C(
        "terrorism_act",
        "X is an act intended to intimidate a population or coerce a "
        "government, grouped here with war crimes")])], None)
    assert m["empty_gloss_rate"] == 0.0


def test_stopwords_and_single_letters_do_not_rescue_an_empty_gloss():
    # "C is a system message" must not score as contentful merely because of
    # the variable letter and the articles.
    m = E.gloss_metric([_out([_C("system_message", "C is a system message")])], None)
    assert m["empty_gloss_rate"] == 1.0


def test_a_module_that_failed_to_build_is_SCORED_AS_NOTHING_not_as_clean():
    """⛔ The `licence_modules_scored` failure, repeated for glosses: an
    unbuildable module carries no concepts, so every rate reads 0.0000 and
    "nothing measured" looks exactly like "no empty glosses"."""
    m = E.gloss_metric([E.ClauseOutcome("m0001", "invalid", None, [])], None)
    assert m["gloss_concepts_scored"] == 0.0, (
        "the denominator must show that nothing was scored")
    assert m["empty_gloss_rate"] == 0.0      # reads clean...
    # ...which is only safe BECAUSE the denominator above is reported with it.


def test_the_rate_is_over_concepts_and_the_per_clause_count_over_clauses():
    outs = [_out([_C("a_thing", "a thing"), _C("b_thing", "B is measured in metres")]),
            _out([_C("c_thing", "a c thing")])]
    m = E.gloss_metric(outs, None)
    assert m["empty_gloss_rate"] == 2 / 3
    assert m["empty_glosses_per_clause"] == 1.0
    assert m["gloss_concepts_scored"] == 1.5


# ==========================================================================
#  ⭐ The RAW gloss metric — the censoring that invalidated RESULT_bad_example_6
# ==========================================================================

_RAW_EMPTY = json.dumps({
    "outcome": "translated", "clause_id": "m0001",
    "concepts": [{"name": "terrorism_act", "gloss": "an act of terrorism"},
                 {"name": "critical_harm", "gloss": "conduct the document "
                  "groups with genocide and torture"}],
})


def test_raw_gloss_metric_counts_a_module_that_failed_the_schema():
    """⛔ THE WHOLE POINT. `glosses` sees `module=None` and reports 0.000; the
    empty gloss is sitting in the raw response on disk. A control arm read
    0.000 that way and the run was written up as "no incidence"."""
    o = E.ClauseOutcome("m0001", "invalid", None, [], raw=_RAW_EMPTY)
    censored = E.gloss_metric([o], None)
    raw = E.gloss_raw_metric([o], None)
    assert censored["gloss_concepts_scored"] == 0.0
    assert censored["empty_gloss_rate"] == 0.0, "the censored reading"
    assert raw["raw_gloss_concepts_scored"] == 2.0
    assert raw["raw_empty_gloss_rate"] == 0.5, "the uncensored reading"
    assert raw["raw_empty_glosses_per_clause"] == 1.0


def test_raw_gloss_metric_reports_how_many_responses_it_could_parse():
    """A rate over nothing must not read as a rate of zero — tip 2."""
    outs = [E.ClauseOutcome("m0001", "invalid", None, [], raw="not json at all"),
            E.ClauseOutcome("m0002", "translated", None, [], raw=_RAW_EMPTY)]
    m = E.gloss_raw_metric(outs, None)
    assert m["raw_responses_parsed"] == 1.0
    m0 = E.gloss_raw_metric(
        [E.ClauseOutcome("m0001", "error", None, [], raw="")], None)
    assert m0["raw_responses_parsed"] == 0.0
    assert m0["raw_empty_gloss_rate"] == 0.0    # only readable next to the 0.0 above


def test_raw_gloss_metric_reads_a_fenced_response():
    o = E.ClauseOutcome("m0001", "invalid", None, [],
                        raw="```json\n" + _RAW_EMPTY + "\n```")
    assert E.gloss_raw_metric([o], None)["raw_gloss_concepts_scored"] == 2.0


def test_both_gloss_metrics_share_one_emptiness_definition():
    """Two copies of this predicate drift by a stopword and then report two
    different rates for the same run."""
    assert E.gloss_is_empty("terrorism_act", "an act of terrorism")
    assert not E.gloss_is_empty("terrorism_act", "an act intended to coerce")
    o_mod = E.ClauseOutcome("m0001", "translated",
                            _M([_C("terrorism_act", "an act of terrorism")]), [],
                            raw=json.dumps({"concepts": [
                                {"name": "terrorism_act",
                                 "gloss": "an act of terrorism"}]}))
    assert (E.gloss_metric([o_mod], None)["empty_gloss_rate"]
            == E.gloss_raw_metric([o_mod], None)["raw_empty_gloss_rate"] == 1.0)


def test_raw_gloss_metric_is_registered_and_selectable():
    assert "glosses_raw" in E.METRICS
    assert E.load_metrics(["glosses_raw"]) == ["findings", "glosses_raw"]
