"""Tests for the mutation verifier itself.

`mutate_schema.py` is the thing that makes `test_schema.py`'s docstring true
rather than aspirational. So it needs its own RED-first evidence, and these
were written before it existed.

⚠️ THE FAILURE MODE THESE ARE DESIGNED AGAINST. A mutator whose "every guard is
pinned" answer is indistinguishable from "no mutation was actually applied".
This project has shipped that shape three times. So the three properties that
matter most here are:

  * a guard nothing pins is reported as a SURVIVOR (test_detects_a_survivor)
  * a mutation that cannot be applied is an ERROR, never a silent pass
    (test_unapplicable_mutation_is_an_error_not_a_survivor)
  * `schema.py` on disk is byte-identical afterwards (test_..._byte_identical)

Run:
    semi-formal-experiment/.venv/bin/python -m pytest \
        walkthrough/paper_pipeline/phase_1/test_mutate.py -q
"""

import hashlib
import sys
import textwrap
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import mutate_schema as M  # noqa: E402

REAL_SCHEMA = HERE / "schema.py"
REAL_TESTS = HERE / "test_schema.py"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# --------------------------------------------------------------- the fake pair
#
# A two-guard module where the test file pins ONE of them. The mutator must say
# so: guard A killed, guard B survived. Anything that reports "all pinned" here
# is the exact defect this file exists to catch.

FAKE_SCHEMA = textwrap.dedent('''\
    """A tiny stand-in for schema.py: two guards, one of them unpinned."""


    class ModuleValidationError(RuntimeError):
        pass


    def validate(obj):
        if obj.get("a") == "bad":
            raise ModuleValidationError("guard A is pinned by a test")
        if obj.get("b") == "bad":
            raise ModuleValidationError("guard B is pinned by nothing at all")
        return obj
''')

FAKE_TESTS = textwrap.dedent('''\
    import pytest

    import schema


    def test_guard_a_fires():
        with pytest.raises(schema.ModuleValidationError):
            schema.validate({"a": "bad"})


    def test_the_happy_path():
        assert schema.validate({}) == {}
''')


@pytest.fixture
def fake(tmp_path):
    s = tmp_path / "schema.py"
    t = tmp_path / "test_fake_guards.py"
    s.write_text(FAKE_SCHEMA)
    t.write_text(FAKE_TESTS)
    return s, t


# ------------------------------------------------------------------ discovery

def test_discovery_finds_every_raise_structurally():
    """Guards are located by AST, not by line number, which drifts."""
    muts = M.discover(REAL_SCHEMA.read_text())
    assert len(muts) >= 20, f"only {len(muts)} raise sites found"
    for m in muts:
        assert m.segment.lstrip().startswith("raise ")
        assert m.qual, "every mutation must name the function it guards"


def test_every_required_guard_maps_to_exactly_one_raise():
    """The brief's floor of 20 guards must each resolve to a unique site.

    If a phrase stops matching — because the message was reworded — that is a
    LOUD failure here rather than a mutation quietly dropped from the run.
    """
    muts = M.discover(REAL_SCHEMA.read_text())
    for name, phrase in M.REQUIRED.items():
        hits = [m for m in muts if phrase in m.segment]
        assert len(hits) == 1, (
            f"required guard {name!r} (phrase {phrase!r}) matched "
            f"{len(hits)} raise sites, expected exactly 1")


# ------------------------------------------------------------------ applying

def test_apply_removes_the_raise_and_keeps_the_file_parseable():
    src = REAL_SCHEMA.read_text()
    mut = next(m for m in M.discover(src) if "beat itself" in m.segment)
    out = M.apply(src, mut)
    assert "beat itself" not in out
    assert out != src
    compile(out, "<mutated>", "exec")  # still importable


def test_apply_refuses_when_the_segment_does_not_match():
    """A mutation whose anchor has drifted must be a loud error.

    Not a no-op that then reports "no tests died" — that reads as a survivor
    and would be exactly backwards.
    """
    src = REAL_SCHEMA.read_text()
    mut = next(iter(M.discover(src)))
    drifted = M.Mutation(name=mut.name, qual=mut.qual, lineno=mut.lineno,
                         end_lineno=mut.end_lineno,
                         segment="raise ValueError('never in this file')")
    with pytest.raises(M.MutationError):
        M.apply(src, drifted)


def test_apply_refuses_a_mutation_that_changes_nothing():
    src = "x = 1\n"
    mut = M.Mutation(name="bogus", qual="none", lineno=99, end_lineno=99,
                     segment="raise ValueError('x')")
    with pytest.raises(M.MutationError):
        M.apply(src, mut)


# --------------------------------------------------- the survivor, end to end

def test_detects_a_survivor(fake):
    schema_path, test_path = fake
    rep = M.run_all(schema_path, test_path)

    by_status = {r.status for r in rep.results}
    assert "survivor" in by_status, (
        "the unpinned guard B was not reported as a survivor — this is the "
        "failure mode the whole tool exists to detect")

    survivors = [r for r in rep.results if r.status == "survivor"]
    assert len(survivors) == 1
    assert "guard B" in survivors[0].mutation.segment

    killed = [r for r in rep.results if r.status == "killed"]
    assert len(killed) == 1
    assert "guard A" in killed[0].mutation.segment
    assert killed[0].killed == ["test_guard_a_fires"]

    assert rep.exit_code != 0, "a survivor must make the run exit non-zero"


def test_all_guards_pinned_exits_zero(tmp_path):
    """The green case must be reachable, or a red result proves nothing."""
    s = tmp_path / "schema.py"
    t = tmp_path / "test_both.py"
    s.write_text(FAKE_SCHEMA)
    t.write_text(FAKE_TESTS + textwrap.dedent('''

        def test_guard_b_fires():
            with pytest.raises(schema.ModuleValidationError):
                schema.validate({"b": "bad"})
    '''))
    rep = M.run_all(s, t)
    assert [r.status for r in rep.results] == ["killed", "killed"]
    assert rep.exit_code == 0


# ------------------------------------------------- errors are not survivors

def test_unapplicable_mutation_is_an_error_not_a_survivor(fake):
    """⭐ The load-bearing one.

    A mutation that never got applied kills no test. If the tool counts that as
    "no survivors" the report is inverted: an unapplied mutation would read as
    a *pinned* guard. It must be an ERROR, distinct from both statuses, and it
    must still fail the run.
    """
    schema_path, test_path = fake
    bogus = M.Mutation(name="drifted", qual="validate", lineno=1, end_lineno=1,
                       segment="raise ValueError('this anchor has drifted')")
    rep = M.run_all(schema_path, test_path, mutations=[bogus])

    assert [r.status for r in rep.results] == ["error"]
    assert rep.results[0].killed == []
    assert rep.results[0].status != "survivor"
    assert rep.n_errors == 1 and rep.n_survivors == 0
    assert rep.exit_code != 0


def test_a_red_baseline_is_refused(tmp_path):
    """If the suite is not green before mutating, every result is meaningless."""
    s = tmp_path / "schema.py"
    t = tmp_path / "test_broken.py"
    s.write_text(FAKE_SCHEMA)
    t.write_text(FAKE_TESTS + "\n\ndef test_already_red():\n    assert False\n")
    with pytest.raises(M.MutationError, match="baseline"):
        M.run_all(s, t)


def test_a_suite_that_collects_nothing_is_refused(tmp_path):
    s = tmp_path / "schema.py"
    t = tmp_path / "test_empty.py"
    s.write_text(FAKE_SCHEMA)
    t.write_text("import schema\n")
    with pytest.raises(M.MutationError):
        M.run_all(s, t)


# ------------------------------------------------------------------ reporting

def test_the_report_names_every_survivor_loudly(fake):
    """A hole that is not named in the output is a hole nobody acts on."""
    schema_path, test_path = fake
    text = M.format_report(M.run_all(schema_path, test_path))
    assert "SURVIVOR" in text
    assert "1 SURVIVORS" in text or "1 SURVIVOR" in text
    assert "guard B" in text, "the surviving guard's own source is not shown"


def test_the_report_separates_errors_from_survivors(fake):
    schema_path, test_path = fake
    bogus = M.Mutation(name="drifted", qual="validate", lineno=1, end_lineno=1,
                       segment="raise ValueError('this anchor has drifted')")
    text = M.format_report(M.run_all(schema_path, test_path, mutations=[bogus]))
    assert "ERROR" in text and "0 SURVIVORS" in text
    assert "NOT evidence" in text


# ------------------------------------------------------------------ isolation

def test_the_real_schema_is_byte_identical_after_a_run():
    """Never modify schema.py in place. Verified, not assumed."""
    before = _sha(REAL_SCHEMA)
    src = REAL_SCHEMA.read_text()
    one = next(m for m in M.discover(src) if "beat itself" in m.segment)
    rep = M.run_all(REAL_SCHEMA, REAL_TESTS, mutations=[one])
    assert _sha(REAL_SCHEMA) == before, "schema.py was modified in place"
    assert rep.results[0].status == "killed"
    assert "test_a_clause_cannot_beat_itself" in rep.results[0].killed


def test_the_mutated_copy_is_what_the_tests_import():
    """Isolation is real: the guard deleted in the COPY is the one that dies.

    If the import were pointing at the file on disk, every mutation would be a
    survivor and the tool would report a green run over a corpse.
    """
    src = REAL_SCHEMA.read_text()
    one = next(m for m in M.discover(src) if "two identities" in m.segment)
    rep = M.run_all(REAL_SCHEMA, REAL_TESTS, mutations=[one])
    assert rep.results[0].status == "killed"
    assert "test_a_module_that_renames_itself" in rep.results[0].killed


# ==========================================================================
#  ⭐ `mutate_seats.py`'s engine — the instrument that certifies stage 4.
#
#  It shipped reporting `83 mutants applied, 0 survivor(s)`, exit 0, against a
#  RED suite: the whole kill rule was `returncode != 0`. These pin the three
#  guards it did not have, in the same order `mutate_schema.py`'s docstring
#  lists them. ⛔ Without these the guards themselves would be unpinned — the
#  same shape, one level up.
# ==========================================================================

import mutate_seats as S  # noqa: E402

FAKE_MOD = textwrap.dedent('''\
    """Two guards; the fake test file pins exactly one of them."""


    class Refused(RuntimeError):
        pass


    def check(obj):
        if obj.get("a") == "bad":
            raise Refused("guard A is pinned by a test")
        if obj.get("b") == "bad":
            raise Refused("guard B is pinned by nothing at all")
        return obj
''')

FAKE_MOD_TESTS = textwrap.dedent('''\
    import pytest

    import fakeguards


    def test_guard_a_fires():
        with pytest.raises(fakeguards.Refused):
            fakeguards.check({"a": "bad"})


    def test_the_happy_path():
        assert fakeguards.check({}) == {}
''')

_A = ('    if obj.get("a") == "bad":\n'
      '        raise Refused("guard A is pinned by a test")')
_B = ('    if obj.get("b") == "bad":\n'
      '        raise Refused("guard B is pinned by nothing at all")')


@pytest.fixture
def fake_pair(tmp_path):
    m = tmp_path / "fakeguards.py"
    t = tmp_path / "test_fakeguards_for_mutate_seats.py"
    m.write_text(FAKE_MOD)
    t.write_text(FAKE_MOD_TESTS)
    return m, t


def _by_name(results):
    return {r.name: r.status for r in results}


def test_seats_engine_reports_a_survivor_as_a_survivor(fake_pair):
    """The whole point. Guard B is pinned by nothing and must say so."""
    m, t = fake_pair
    results, n = S.run_all(
        [("guard-a-deleted", _A, "    pass"),
         ("guard-b-deleted", _B, "    pass")], str(m), str(t))
    assert n == 2
    assert _by_name(results) == {"guard-a-deleted": "killed",
                                "guard-b-deleted": "survivor"}


def test_seats_engine_REFUSES_a_red_baseline(fake_pair):
    """⛔ THE DEFECT THIS FILE WAS REWRITTEN FOR. `[RAN]` 2026-08-08 against
    `29e018c`: one always-failing test appended to `test_seats.py`, and the
    sweep printed `83 mutants applied, 0 survivor(s)` and exited 0. A red suite
    kills every mutant, so every guard reads as pinned."""
    m, t = fake_pair
    t.write_text(FAKE_MOD_TESTS + "\n\ndef test_already_red():\n"
                                  "    assert False\n")
    with pytest.raises(M.MutationError, match="baseline"):
        S.run_all([("guard-a-deleted", _A, "    pass")], str(m), str(t))


def test_seats_engine_calls_a_COLLECTION_ERROR_an_error_not_a_kill(fake_pair):
    """⛔ `rc=2` is pytest saying *the suite did not run*. The old rule
    (`killed = returncode != 0`) reported a mutant that broke the import as
    KILLED — the flattering direction, and the one this repo names as its
    signature failure."""
    m, t = fake_pair
    results, _n = S.run_all(
        [("import-raises", 'class Refused(RuntimeError):',
          'raise RuntimeError("the module cannot be imported")\n'
          'class Refused(RuntimeError):')],
        str(m), str(t))
    assert [r.status for r in results] == ["error"]
    assert "did not run comparably" in results[0].detail


def test_seats_engine_calls_a_DRIFTED_ANCHOR_an_error_not_a_kill(fake_pair):
    """A mutation that was never applied kills nothing and proves nothing. The
    old version counted it separately as `NOT APPLIED` and still printed
    `0 survivor(s)` on the headline line."""
    m, t = fake_pair
    results, _n = S.run_all(
        [("anchor-drifted", "a guard that was reworded months ago", "pass")],
        str(m), str(t))
    assert [r.status for r in results] == ["error"]
    assert "matches 0 times" in results[0].detail


def test_seats_engine_leaves_the_real_source_byte_identical(fake_pair):
    """⛔ The old sweep rewrote `seats.py` IN PLACE and restored it in a
    `finally`; an interrupted run left the working tree mutated. Nothing is
    written outside the mirror now, and the digest is asserted."""
    m, t = fake_pair
    before = _sha(HERE / "seats.py")
    S.run_all([("guard-a-deleted", _A, "    pass")], str(m), str(t))
    assert _sha(HERE / "seats.py") == before


def test_the_seats_mutant_table_still_anchors_on_the_real_source():
    """⚠️ Anchors are source fragments, so an ordinary edit to `seats.py` can
    silently drop a mutant from the run. A short run reports fewer holes than
    exist, so it fails HERE, cheaply, instead of in a sweep that prints 0."""
    src = (HERE / "seats.py").read_text()
    drifted = {name: src.count(old) for name, old, _new in S.MUTANTS
               if src.count(old) != 1}
    assert not drifted, drifted


def test_the_r3_mutant_table_still_anchors_on_the_real_source():
    import mutate_readback_r3 as R3
    src = (HERE / "readback_r3.py").read_text()
    drifted = {name: src.count(old) for name, old, _new in R3.MUTANTS
               if src.count(old) != 1}
    assert not drifted, drifted
