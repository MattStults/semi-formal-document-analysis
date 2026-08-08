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
