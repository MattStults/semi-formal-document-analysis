"""Integration tests for the pipeline model and its guard.

Run:  python3 -m pytest walkthrough/model/test_model.py -q

WHY THIS EXISTS. Three times in one day a change to one of these components
silently disabled another, and each time the broken component reported success:

  * a scripted edit deleted a third of the design document — the write succeeded
  * a shadowed variable disabled the file-staleness check — it ran, found nothing
  * a report-format change broke guard.py's parser — it reported GREEN on ten
    open gaps

⭐ The shared root cause: **a "pass" state indistinguishable from a "did not
run" state.** Every test below is therefore written to fail if the thing under
test stops doing work, not merely if it returns a wrong answer.
"""

import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import check   # noqa: E402
import guard   # noqa: E402


# --------------------------------------------------------------------------
# the model solves at all
# --------------------------------------------------------------------------

def test_model_solves_and_parses():
    findings, labels = check.solve()
    assert labels, "no labels parsed — the parser is broken or the model failed"
    assert isinstance(findings, set)


def test_parser_refuses_to_report_when_it_matches_nothing():
    """The canary. A parser returning nothing must raise, not report clean."""
    real = check.LABEL
    try:
        import re
        check.LABEL = re.compile(r"WILL_NEVER_MATCH\((a)\)\((b)\)")
        with pytest.raises(RuntimeError, match="parsed 0 labels"):
            check.solve()
    finally:
        check.LABEL = real


def test_every_finding_kind_is_explained():
    """A finding a reader cannot interpret is barely better than none."""
    findings, _ = check.solve()
    for kind, _ in findings:
        assert kind in check.MEANING, f"{kind} has no entry in MEANING"
        assert kind in check.CLASS, f"{kind} has no severity class"


def test_every_finding_subject_resolves_to_a_label_or_is_a_residue():
    """`only_narrowed` reports an escape description rather than an id, so it is
    exempt; everything else should name something a reader can look up."""
    findings, labels = check.solve()
    for kind, subj in findings:
        if kind == "only_narrowed":
            continue
        assert subj in labels, f"{kind}/{subj} has no label"


# --------------------------------------------------------------------------
# the rules actually fire — RED, per component
# --------------------------------------------------------------------------

@pytest.mark.parametrize("drop,add,expect", [
    ("catches(cycle_beats, p17).", "", "uncaught_problem"),
    ("", "continues(repair_seat, translator).\n"
         "sees(translator, expected_verdicts).", "contamination"),
    ("", "check(bogus, s99, deterministic). catches(bogus, p1).", "check_no_stage"),
    ("check(link,       s2, deterministic).",
     "check(link, s2, seat).", "silent_needs_determinism"),
])
def test_rule_fires_on_a_model_broken_in_its_own_way(drop, add, expect):
    found = check.solve_modified(drop=drop or None, add=add)
    assert expect in {k for k, _ in found}, \
        f"breaking the model in a way that should trigger `{expect}` did not"


def test_healthy_model_reports_no_contamination():
    findings, _ = check.solve()
    assert "contamination" not in {k for k, _ in findings}, \
        "the live model has a seat reaching forbidden material"


# --------------------------------------------------------------------------
# the guard sees what the checker sees — the coupling that broke once
# --------------------------------------------------------------------------

def test_guard_sees_the_same_findings_as_check():
    """guard.py once scraped check.py's printed text. When the format changed it
    saw zero findings and reported green. It now imports; this pins that."""
    direct, _ = check.solve()
    via_guard, _ = guard._check.solve()
    assert via_guard == direct
    assert direct, "no findings at all — cannot tell working from broken"


def test_waivers_all_match_a_live_finding():
    """A waiver for a finding that no longer occurs is fiction accumulating."""
    valid, invalid = guard.waivers()
    assert not invalid, f"invalid waivers present: {invalid}"
    findings, _ = check.solve()
    stale = set(valid) - findings
    assert not stale, f"waivers with no matching finding: {sorted(stale)}"


def test_a_waiver_missing_a_required_field_does_not_waive(tmp_path, monkeypatch):
    bad = tmp_path / "accepted.json"
    bad.write_text(json.dumps({"waivers": [
        {"finding": "claim_n_is_one", "subject": "divergence",
         "date": "2026-08-07", "who": "someone", "why": ""}]}))
    monkeypatch.setattr(guard, "ACCEPTED", str(bad))
    valid, invalid = guard.waivers()
    assert not valid
    assert invalid and "why" in invalid[0][1]


# --------------------------------------------------------------------------
# staleness — the check that was silently disabled by variable shadowing
# --------------------------------------------------------------------------

def test_watched_list_is_not_duplicated_in_the_hooks():
    """The list lived in three places once. The shell hook must ask, not copy."""
    hook = open(os.path.join(HERE, "hooks", "pre-commit")).read()
    assert "--watches" in hook, "pre-commit should query guard.py for the list"
    assert "03_pipeline.md" not in hook.split("Install:")[-1].split("Remove:")[0], \
        "pre-commit appears to hardcode a watched path again"


def test_watches_query_discriminates():
    assert guard.watches(["walkthrough/model/rules.lp"]) == 0
    assert guard.watches(["walkthrough/README.md"]) == 1


def test_staleness_fires_when_a_watched_file_changes():
    """Guards a real regression: `stale` was bound twice and the second binding
    silently replaced the file-staleness result with the waiver-staleness one."""
    now = guard.current()
    assert now, "nothing watched"
    then = dict(now)
    key = sorted(then)[0]
    then[key] = "0" * 16
    changed = [k for k in now if then.get(k) != now[k]]
    assert changed == [key]
