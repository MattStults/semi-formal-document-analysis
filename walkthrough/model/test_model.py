"""Integration tests for the staleness guard.

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

⚠️ The assertion layer this file used to test (`pipeline.lp`, `rules.lp`,
`check.py`) was retired on 2026-08-07 — see `RETIRED.md`. The tests that
exercised it are gone. What is left, and what has been widened, is the guard.
"""

import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
WALK = os.path.dirname(HERE)
REPO = os.path.dirname(WALK)
sys.path.insert(0, HERE)

import guard   # noqa: E402


# --------------------------------------------------------------------------
# the watch list is DATA, not code
# --------------------------------------------------------------------------

def test_watch_list_lives_in_a_data_file():
    """Widening the watch list must be an edit to a list, not to code."""
    assert os.path.exists(guard.WATCH_FILE), "watch.json is missing"
    raw = json.load(open(guard.WATCH_FILE))
    assert isinstance(raw.get("watch"), list) and raw["watch"], \
        "watch.json must carry a non-empty `watch` list"
    for e in raw["watch"]:
        assert e.get("path"), f"entry without a path: {e}"
        assert str(e.get("why", "")).strip(), \
            f"{e['path']} is watched with no stated reason — a STALE report on " \
            f"it would tell the reader nothing to do"


def test_watch_list_covers_the_transcribed_files():
    """⭐ THE FINDING. Three of five conformance failures happened in files
    TRANSCRIBED from the design and never re-checked when it moved. The design
    document alone is not the watch list."""
    watched = set(guard.current())
    assert "resources/03_pipeline.md" in watched
    assert "paper_pipeline/phase_1/schema.py" in watched
    prompts = [w for w in watched if w.startswith("paper_pipeline/phase_1/prompt/")]
    assert len(prompts) >= 4, f"prompt files not watched: {sorted(watched)}"


def test_guard_does_not_require_the_retired_assertion_layer():
    src = open(os.path.join(HERE, "guard.py")).read()
    assert "pipeline.lp" not in src, "guard.py still refers to the retired model"
    assert "import check" not in src, "guard.py still imports the retired checker"
    assert not os.path.exists(os.path.join(HERE, "pipeline.lp"))
    assert not os.path.exists(os.path.join(HERE, "rules.lp"))
    assert not os.path.exists(os.path.join(HERE, "check.py"))


# --------------------------------------------------------------------------
# ⭐ a "pass" that is indistinguishable from "did not run" is the failure
# this directory exists to prevent
# --------------------------------------------------------------------------

def _watchfile(tmp_path, obj):
    p = tmp_path / "watch.json"
    p.write_text(json.dumps(obj))
    return str(p)


def test_an_empty_watch_list_is_a_loud_error_not_a_silent_pass(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(guard, "WATCH_FILE", _watchfile(tmp_path, {"watch": []}))
    rc = guard.check()
    out = capsys.readouterr().out
    assert rc == 2, "an empty watch list must not exit 0"
    assert "⛔ ERROR" in out and "watch" in out.lower()


def test_a_missing_watch_file_is_a_loud_error(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(guard, "WATCH_FILE", str(tmp_path / "nope.json"))
    rc = guard.check()
    assert rc == 2
    assert "⛔ ERROR" in capsys.readouterr().out


def test_an_unreadable_watch_file_is_a_loud_error(tmp_path, monkeypatch, capsys):
    p = tmp_path / "watch.json"
    p.write_text("{ not json")
    monkeypatch.setattr(guard, "WATCH_FILE", str(p))
    rc = guard.check()
    assert rc == 2
    assert "⛔ ERROR" in capsys.readouterr().out


def test_a_pattern_matching_no_file_is_an_error():
    """A watched file that is renamed away must not silently stop being watched
    — that is the same 'pass == did not run' shape at the level of one entry."""
    with pytest.raises(guard.WatchListError, match="matched no file"):
        guard.resolve([{"path": "no/such/dir/*.md", "why": "x"}])


# --------------------------------------------------------------------------
# staleness — per file
# --------------------------------------------------------------------------

def test_staleness_fires_for_exactly_the_changed_file():
    """Guards a real regression: `stale` was bound twice and the second binding
    silently replaced the file-staleness result with the waiver-staleness one."""
    now = guard.current()
    assert now, "nothing watched"
    then = {k: {"digest": v} for k, v in now.items()}
    key = sorted(then)[0]
    then[key]["digest"] = "0" * 16
    assert guard.stale(now, then) == [key]


def test_never_reviewed_files_are_reported_apart_from_changed_ones():
    """A file added to the watch list has never been reviewed. That is a
    different sentence to 'this file changed', and reads differently."""
    now = {"a.md": "1111", "b.md": "2222"}
    then = {"a.md": {"digest": "ffff"}}
    assert guard.stale(now, then) == ["a.md"]
    assert guard.unreviewed(now, then) == ["b.md"]


def test_accept_is_per_file(tmp_path, monkeypatch):
    """⭐ Accepting one file's change must not silently accept another's — a
    whole-list accept is how an unreviewed transcription rides in on a typo fix."""
    stamp = tmp_path / "reviewed.json"
    monkeypatch.setattr(guard, "STAMP", str(stamp))
    monkeypatch.setattr(guard, "current",
                        lambda: {"a.md": "aaaa", "b.md": "bbbb"})
    guard.accept(["a.md"], who="test")
    rec = guard.recorded()
    assert rec["a.md"]["digest"] == "aaaa"
    assert "b.md" not in rec, "accepting a.md silently accepted b.md"
    guard.accept(["b.md"], who="test")
    assert set(guard.recorded()) == {"a.md", "b.md"}


def test_accept_records_who_and_when(tmp_path, monkeypatch):
    stamp = tmp_path / "reviewed.json"
    monkeypatch.setattr(guard, "STAMP", str(stamp))
    monkeypatch.setattr(guard, "current", lambda: {"a.md": "aaaa"})
    guard.accept(["a.md"], who="test")
    e = guard.recorded()["a.md"]
    assert e["by"] == "test" and e["at"]


def test_accept_refuses_a_path_it_does_not_watch(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(guard, "STAMP", str(tmp_path / "reviewed.json"))
    monkeypatch.setattr(guard, "current", lambda: {"a.md": "aaaa"})
    assert guard.accept(["not/watched.md"], who="test") == 2
    assert "not watched" in capsys.readouterr().out


def test_stale_report_states_why_the_file_is_watched(capsys):
    """A guard that cries wolf gets ignored. The cure is not a weaker check —
    it is a report that says what to re-read."""
    guard.check()
    out = capsys.readouterr().out
    if "STALE" in out or "NEVER REVIEWED" in out:
        whys = [e["why"] for e in guard.load_watch()]
        assert any(w[:40] in out for w in whys), \
            "STALE report names files but never says what to re-check"


def test_recorded_entries_no_longer_watched_are_surfaced(capsys):
    """A digest for a file nobody watches is dead weight and hides a rename."""
    assert guard.orphans({"a.md": "1"}, {"a.md": {"digest": "1"},
                                         "gone.lp": {"digest": "2"}}) == ["gone.lp"]


# --------------------------------------------------------------------------
# the hooks ask the guard; they do not keep their own copy of the list
# --------------------------------------------------------------------------

def test_watched_list_is_not_duplicated_in_the_hooks():
    """The list lived in three places once. The hooks must ask, not copy."""
    hook = open(os.path.join(HERE, "hooks", "pre-commit")).read()
    assert "--watches" in hook, "pre-commit should query guard.py for the list"
    body = hook.split("Install:")[-1]
    assert "03_pipeline.md" not in body, "pre-commit hardcodes a watched path again"
    py = open(os.path.join(HERE, "hooks", "guard_hook.py")).read()
    assert "03_pipeline.md" not in py, "guard_hook.py hardcodes a watched path"
    assert "--watches" in py, "guard_hook.py should query guard.py for the list"


def test_watches_query_discriminates():
    assert guard.watches(["walkthrough/resources/03_pipeline.md"]) == 0
    assert guard.watches(["walkthrough/paper_pipeline/phase_1/schema.py"]) == 0
    assert guard.watches(["walkthrough/paper_pipeline/phase_1/prompt/00_task.md"]) == 0
    assert guard.watches(["walkthrough/README.md"]) == 1
    assert guard.watches(["walkthrough/link.py"]) == 1


def test_watches_matches_on_the_whole_path_not_the_basename():
    """`00_task.md` under some other directory is not the watched file."""
    assert guard.watches(["somewhere/else/00_task.md"]) == 1
    assert guard.watches(["other/schema.py"]) == 1


# --------------------------------------------------------------------------
# the pre-commit hook, exercised without running git
# --------------------------------------------------------------------------

def _run_hook(staged):
    env = dict(os.environ, GUARD_STAGED_FILES=staged)
    return subprocess.run(["sh", os.path.join(HERE, "hooks", "pre-commit")],
                          capture_output=True, text=True, cwd=REPO, env=env)


def test_pre_commit_is_silent_when_nothing_watched_is_staged():
    r = _run_hook("walkthrough/README.md walkthrough/link.py")
    assert r.returncode == 0
    assert r.stdout.strip() == "", f"hook spoke when it should not: {r.stdout}"


def test_pre_commit_is_silent_on_an_empty_stage():
    r = _run_hook("")
    assert r.returncode == 0 and r.stdout.strip() == ""


def test_pre_commit_fires_when_a_watched_file_is_staged():
    r = _run_hook("walkthrough/paper_pipeline/phase_1/schema.py")
    assert "a watched file changed" in r.stdout, r.stdout + r.stderr


def test_pre_commit_blocks_EXACTLY_WHEN_the_guard_is_unhappy():
    """The contract, stated without reference to today's review state.

    ⛔ This used to assert `returncode == 1` with the comment "schema.py has
    never been reviewed, so this must also BLOCK". The moment schema.py was
    legitimately reviewed the test failed and reported a completed review as a
    defect — the third instance of pinning a live value that this repo's brief
    already warns about. What is actually worth asserting is that the hook and
    the guard never disagree, which holds in both states.
    """
    guard = subprocess.run(
        [sys.executable, os.path.join(HERE, "guard.py")],
        capture_output=True, text=True, cwd=REPO)
    hook = _run_hook("walkthrough/paper_pipeline/phase_1/schema.py")
    if guard.returncode == 0:
        assert hook.returncode == 0, (
            "the guard is happy but the hook blocked:\n" + hook.stdout)
        assert "COMMIT BLOCKED" not in hook.stdout
    else:
        assert hook.returncode == 1, (
            "the guard is unhappy and the hook let the commit through — the "
            "failure this whole mechanism exists to prevent:\n" + hook.stdout)
        assert "COMMIT BLOCKED" in hook.stdout


def test_pre_commit_fires_for_a_prompt_file():
    r = _run_hook("walkthrough/paper_pipeline/phase_1/prompt/30_failure_modes.md")
    assert "a watched file changed" in r.stdout, r.stdout + r.stderr


def test_pre_commit_self_test_passes():
    r = subprocess.run([sys.executable, os.path.join(HERE, "guard.py"), "--self-test"],
                       capture_output=True, text=True, cwd=HERE)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "FAIL" not in r.stdout, r.stdout
