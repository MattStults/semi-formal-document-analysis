"""Tests for the graveyard — entries written when repair does not converge.

A clause that fails to converge carries a signal about the PROMPT, not only
about that clause, and the signal is only visible by comparing failures against
each other. Reading two transcripts by hand found one shared cause behind both;
that does not scale to 593.

⚠️ This is PERSISTENCE ONLY. Nothing here diagnoses, aggregates, or changes a
prompt. Those steps involve design decisions that are not settled.
"""

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import graveyard as G  # noqa: E402


def outcome(status="unrepaired", attempts=3, flags=(), per_attempt=(1, 1, 1)):
    class O:
        pass
    o = O()
    o.status, o.attempts = status, attempts
    o.flags, o.per_attempt = list(flags), list(per_attempt)
    o.transcript = [{"role": "user", "content": "clause"},
                    {"role": "assistant", "content": "{}"}]
    o.findings, o.module = [], None
    return o


CLAUSE = {"id": "m0036", "quote": "text", "section_id": "s", "kind": "conditional"}


# ------------------------------------------------------------------ sampling

@pytest.mark.parametrize("status,flags,attempts,keep,why", [
    ("unrepaired", (), 3, True, "the case the graveyard exists for"),
    ("translated", ("shrank",), 2, True,
     "converged, was flagged, and was garbage — a failures-only graveyard "
     "would never contain it"),
    ("translated", ("declaration-edit",), 2, True, "same"),
    ("translated", (), 3, True,
     "converged on the LAST available attempt — one more defect and it fails; "
     "the budget is hiding it"),
    ("abstained_under_repair", (), 2, True, "repair pressure, not an answer"),
])
def test_these_are_always_kept(status, flags, attempts, keep, why):
    assert G.should_keep(outcome(status, attempts, flags), max_attempts=3,
                         rates={"repaired": 0.0, "first_try": 0.0})[0] is keep, why


def test_a_clean_first_try_is_kept_only_at_its_configured_RATE():
    """A graveyard of only trouble makes every diagnosis read as 'the prompt is
    broken'. A diagnosing agent needs cases where it WORKED to tell a real
    defect from an unlucky clause."""
    o = outcome("translated", attempts=1, per_attempt=(0,))
    assert G.should_keep(o, 3, {"repaired": 0.0, "first_try": 0.0})[0] is False
    assert G.should_keep(o, 3, {"repaired": 0.0, "first_try": 1.0})[0] is True


def test_sampling_is_DETERMINISTIC_for_a_given_clause_and_seed():
    """Two runs of the same corpus must produce the same population, or the
    graveyard is not a reproducible artifact and no comparison over it means
    anything."""
    o = outcome("translated", attempts=1, per_attempt=(0,))
    a = [G.should_keep(o, 3, {"first_try": 0.5}, clause_id=f"m{i:04d}", seed=7)[0]
         for i in range(40)]
    b = [G.should_keep(o, 3, {"first_try": 0.5}, clause_id=f"m{i:04d}", seed=7)[0]
         for i in range(40)]
    assert a == b
    assert 0 < sum(a) < 40, f"a 0.5 rate kept {sum(a)}/40"


# -------------------------------------------------------------------- entries

def test_an_entry_records_what_it_takes_to_reproduce_the_failure(tmp_path):
    e = G.write_entry(tmp_path, CLAUSE, outcome(), reason="unrepaired",
                      contract_hash="c0ffee", provenance_hash="beef")
    meta = json.load(open(Path(e) / "entry.json"))
    assert meta["clause_id"] == "m0036"
    assert meta["reason"] == "unrepaired"
    assert meta["contract_hash"] == "c0ffee"
    assert meta["provenance_hash"] == "beef"
    assert meta["per_attempt"] == [1, 1, 1]
    assert (Path(e) / "transcript.json").exists()


def test_the_two_hashes_answer_DIFFERENT_questions():
    """`contract_hash` = clause + schema: changes mean the artifact may no
    longer VALIDATE. `provenance_hash` = prompt + model: changes mean it is not
    REPRODUCIBLE but is still valid. A prompt fix must not invalidate a corpus."""
    a = G.contract_hash("clause text", "schema source")
    b = G.contract_hash("clause text", "schema source CHANGED")
    c = G.provenance_hash("prompt", "model", 0.2)
    d = G.provenance_hash("prompt CHANGED", "model", 0.2)
    assert a != b and c != d
    assert G.contract_hash("clause text", "schema source") == a


def test_an_entry_is_NOT_cleared_without_a_verdict(tmp_path):
    """Clearing is per entry and requires a written diagnosis. There is no
    clear-all: a graveyard that gets bulk-emptied is worse than none, and this
    project has watched a warning become invisible exactly that way."""
    e = Path(G.write_entry(tmp_path, CLAUSE, outcome(), reason="unrepaired",
                           contract_hash="x", provenance_hash="y"))
    assert G.open_entries(tmp_path) == [e.name]
    with pytest.raises(G.GraveyardError, match="VERDICT"):
        G.clear(tmp_path, e.name)
    (e / "VERDICT.md").write_text("cause: the read-back convention\n")
    G.clear(tmp_path, e.name)
    assert G.open_entries(tmp_path) == []


def test_reaching_the_cap_BLOCKS_rather_than_overflowing(tmp_path):
    """A hundred uninspected non-convergences is not a corpus, it is one prompt
    defect repeated a hundred times. The one mechanism that worked in this
    project blocked; the one that failed only printed."""
    for i in range(3):
        G.write_entry(tmp_path, {**CLAUSE, "id": f"m{i:04d}"}, outcome(),
                      reason="unrepaired", contract_hash="x",
                      provenance_hash="y")
    assert G.at_cap(tmp_path, cap=3) is True
    assert G.at_cap(tmp_path, cap=4) is False
    with pytest.raises(G.GraveyardError, match="cap"):
        G.check_cap(tmp_path, cap=3)


# ------------------------------------------------- wired into a real run

def test_a_run_WRITES_an_entry_for_a_clause_that_does_not_converge(tmp_path):
    """Otherwise the transcript survives only in the run directory, mixed in
    with the successes, and nothing marks it as needing a look."""
    import copy
    import translate as T
    import test_repair as TR

    cfg = copy.deepcopy(T.load_config(str(HERE / "config.json")))
    cfg["select"] = {"clause_ids": ["m0091"], "section_id": None, "kinds": [],
                     "limit": None}
    cfg["output"] = {"dir": str(tmp_path), "run_name": "t"}
    cfg["repair"] = {"max_attempts": 2}
    cfg["graveyard"] = {"dir": str(tmp_path / "gy"), "cap": 50,
                        "rates": {"repaired": 0.0, "first_try": 0.0}}

    class Stub:
        def __init__(self, *a, **k): pass
        def complete(self, s, u):
            return {"text": TR.BROKEN, "in": 1, "out": 1,
                    "finish_reason": "stop"}
        def complete_messages(self, s, m):
            return {"text": TR.BROKEN, "in": 1, "out": 1,
                    "finish_reason": "stop"}

    class A:
        clause = section = kinds = limit = provider = model = max_tokens = None
        live = True
        show_prompt = 0

    T.run(cfg, A(), client_factory=Stub)
    entries = G.open_entries(str(tmp_path / "gy"))
    assert len(entries) == 1, entries
    meta = json.load(open(tmp_path / "gy" / entries[0] / "entry.json"))
    assert meta["clause_id"] == "m0091"
    assert meta["reason"].startswith("repair ran out")
    assert meta["contract_hash"] and meta["provenance_hash"]
    assert meta["contract_hash"] != meta["provenance_hash"]


# The repo-graveyard leak check lives in conftest.py, not here: as a test it
# passed vacuously, because pytest runs this file before the one that leaked.
