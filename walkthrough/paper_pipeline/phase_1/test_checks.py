"""Tests for `checks.py` — stage 2's single entry point.

    semi-formal-experiment/.venv/bin/python -m pytest \
        walkthrough/paper_pipeline/phase_1/test_checks.py -q

⚠️ pytest run from `semi-formal-experiment/` does NOT reach `walkthrough/`; this
file has to be named on the command line (or reached by a path that covers
`walkthrough/`).

⭐ FIXTURES ARE CONSTRUCTED THROUGH THE CONTRACT, never hand-written `.lp` text
and never a committed live-run output. A hand-written fixture drifts from what
stage 1 emits and then the test pins a shape nothing produces; the live-run
outputs on disk were produced under two superseded contracts and no longer
validate at all (`STEP_stage2_and_repair.md` §6).

⚠️ EVERY test asserts a specific `check_id` AND a distinctive message fragment,
never a count or an outcome alone, and every test has a NEGATIVE CONTROL — the
paired case where the same check must stay silent. Both rules are here because
of specific incidents in this repository: sixteen checks in a sibling harness
were green because a different guard raised the same class first, and one test
was satisfied by another component's message that contained the same words.
"""

import dataclasses
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
WALKTHROUGH = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(WALKTHROUGH))

import checks                     # noqa: E402  the module under test
import fixtures                   # noqa: E402  ⭐ the shared stage-1 fixtures
import link                       # noqa: E402  read-only: the other half
import schema                     # noqa: E402  read-only: the contract


IDS = {"m0001", "m0002", "m0255", "m0204", "m0203", "m0208", "m0252"}

CLAUSE = dict(id="m0001", section_id="restricted_content", kind="conditional",
              quote="The assistant should not produce new material of this "
                    "kind, whatever the stated purpose.")

TEXTUAL = fixtures.TEXTUAL

# ⭐ ONE definition of the contract, in `fixtures.py`, shared with
# `test_schema.py`, `test_repair.py` and `../../test_link.py`. This file needs
# the SITUATION-INPUT variant: its one assertion depends on `new_material/1`,
# declared as a situation input rather than derived through the ontology — so a
# clean run has notes and no errors, which is what makes the error/note
# distinction testable at all.
module = fixtures.situation_module
concept = fixtures.material_concept
ABSTENTION = fixtures.abstention()


def run(obj=None, **kw):
    kw.setdefault("clause", CLAUSE)
    kw.setdefault("corpus_ids", IDS)
    return checks.run_checks(module() if obj is None else obj, **kw)


def of(result, check_id):
    return [f for f in result.findings if f.check_id == check_id]


def one(result, check_id, fragment):
    """The single finding with this id AND this fragment. Fails loudly."""
    hits = [f for f in of(result, check_id)
            if fragment.lower() in f.message.lower()]
    assert len(hits) == 1, (
        f"expected exactly one {check_id!r} finding mentioning {fragment!r}; "
        f"got {[(f.check_id, f.origin, f.message[:70]) for f in result.findings]}")
    return hits[0]


# ==========================================================================
#  1. A clean module, and the check that fires on everything
# ==========================================================================

def test_a_clean_module_produces_no_error_findings():
    """A check that fires on everything is useless, and this is the control
    every other test in this file leans on."""
    r = run()
    assert r.outcome == "translated", [f.message for f in r.errors]
    assert r.errors == []
    assert r.module is not None and r.module.clause_id == "m0001"
    assert r.repair_needed is False


def test_a_module_with_an_undeclared_name_is_INVALID_and_says_which_name():
    """The negative control's other half: the same module, one declaration
    removed, must produce the named link error rather than merely a non-zero
    count."""
    r = run(module(inputs=[]))
    # `inputs=[]` leaves `new_material/1` undeclared at BOTH levels, and the
    # schema catches it first — which is itself the contract working.
    assert r.outcome == "invalid"
    f = one(r, "schema-breach", "nothing declares it")
    assert f.origin == "schema" and f.severity == "error"


# ==========================================================================
#  2. `origin` — required, positional, never defaulted
# ==========================================================================

def test_origin_is_required_and_positional_on_Finding():
    """⭐ Later stages feed the same repair log, and two of them carry the
    expected answers a translator is explicitly denied (stage 3's probe cases
    with their must-forbid/must-permit labels, and the four review seats).

    A DEFAULTED marker means a future producer silently inherits
    `origin="schema"`, the log admits it, and the denial dissolves with nothing
    to notice it. So the constructor must REFUSE a Finding with no origin.
    """
    with pytest.raises(TypeError):
        checks.Finding("unresolved-reference", "error", "m0001.lp", "a message")
    ok = checks.Finding("unresolved-reference", "error", "m0001.lp",
                        "a message", "link")
    assert ok.origin == "link"

    origin = {f.name: f for f in dataclasses.fields(checks.Finding)}["origin"]
    assert origin.default is dataclasses.MISSING, \
        "origin acquired a default; the leak this field exists to stop is back"
    assert origin.default_factory is dataclasses.MISSING


def test_an_empty_origin_is_refused_too():
    """The control on the control. `origin=""` satisfies "positional, passed"
    and marks nothing, so a producer that has not decided what it is would slip
    through the field-set assertion above."""
    with pytest.raises(ValueError):
        checks.Finding("x", "error", "w", "m", "")
    with pytest.raises(ValueError):
        checks.Finding("x", "error", "w", "m", None)


# ==========================================================================
#  3. The boundary with `link.py` — adapt, never modify
# ==========================================================================

def test_link_findings_are_carried_across_with_every_field_intact():
    """`link.Finding` has no `origin`, and `link.py --self-test` asserts its
    field set by EQUALITY — so the adaptation happens HERE, at the boundary.

    The set comparison is the point: if `link.Finding` ever grows a field, this
    fails rather than silently dropping it on the way into the repair log.
    """
    link_fields = {f.name for f in dataclasses.fields(link.Finding)}
    ours = {f.name for f in dataclasses.fields(checks.Finding)}
    assert link_fields <= ours, f"a link.Finding field is dropped: {link_fields - ours}"
    assert ours - link_fields == {"origin"}

    src = link.Finding("requires-unprovided", "note", "m0001.lp", "a sentence")
    out = checks.Finding.from_link(src)
    for name in link_fields:
        assert getattr(out, name) == getattr(src, name), name
    assert out.origin == "link"


def test_both_origins_appear_in_ONE_result():
    """The merge is the whole point of the entry point.

    A fabricated citation is a SCHEMA breach on a module that still constructs,
    so the `.lp` renders and the link checks run over it too — one attempt, one
    findings list, two origins. Serialised, this is two paid round-trips.
    """
    r = run(module(
        asserts=[dict(status="forbid", act="produce(M)",
                      body="new_material(M), lifted_by_purpose(M)",
                      read_back="producing % is forbidden",
                      read_back_slots=["M"], licence="textual", cites="m9999",
                      inference=None, toggleable=False)],
        inputs=["new_material/1", "lifted_by_purpose/1"],
        forbid_body=[dict(head="forbid", banned="lifted_by_purpose")]))
    schema_f = one(r, "schema-breach", "m9999")
    assert schema_f.origin == "schema" and schema_f.where == "asserts[0]"
    link_f = one(r, "rule-shape", "lifted_by_purpose")
    assert link_f.origin == "link" and link_f.where.endswith(".lp")
    assert r.outcome == "invalid"


def test_a_clean_module_produces_findings_from_NEITHER_origin():
    """The control for the merge: a merger that always yields both origins
    would satisfy the test above without merging anything."""
    r = run()
    assert [f for f in r.findings if f.severity == "error"] == []


# ==========================================================================
#  4. Abstention is a terminal OUTCOME, not a findings list
# ==========================================================================

def test_an_abstention_is_terminal_and_carries_no_findings():
    """An abstention is forced empty on every content field, so it passes every
    deterministic check TRIVIALLY. Both defaults are harmful: pass it through
    and it enters stage 3 as a passing module with the rate never computed;
    fire a check on it and the loop re-prompts a model that has already said it
    cannot translate faithfully — producing exactly what abstention exists to
    prevent.
    """
    r = run(ABSTENTION)
    assert r.outcome == "abstained"
    assert r.findings == []
    assert r.repair_needed is False
    assert r.abstain_reason.startswith("the clause is a section heading")
    assert r.module is not None and r.module.outcome == "abstained"


def test_a_TRANSLATED_module_is_never_reported_as_an_abstention():
    """The control that must kill the test above: an implementation returning
    `abstained` unconditionally would pass it."""
    assert run().outcome == "translated"
    assert run(module(inputs=[])).outcome == "invalid"


def test_an_abstention_that_carries_content_is_INVALID_not_abstained():
    """The other control. `abstained` is read off the VALIDATED module, never
    off the raw dict — an object that says `abstained` and carries claims is
    neither, and reading the raw field would let it terminate the loop as a
    first-class answer."""
    obj = dict(ABSTENTION, claims=["C1 something"])
    r = run(obj)
    assert r.outcome == "invalid"
    f = one(r, "schema-breach", "abstention with content")
    assert f.origin == "schema"


def test_an_abstention_that_RENAMES_ITSELF_is_invalid_not_abstained():
    """Found by deleting `and not findings` and watching nothing go red.

    An abstention is coherent on its own terms — every content field empty, a
    reason given — so it CONSTRUCTS even when its `clause_id` disagrees with the
    clause it was asked to translate. That breach is caught after construction,
    and without this guard the abstention branch returns first: the loop
    terminates on a first-class answer that is filed against the wrong clause,
    and the abstention rate — the reliability signal the mechanism exists for —
    is credited to a clause nobody asked about.

    The control is the identical abstention with its own id, which must still
    terminate the loop.
    """
    r = run(dict(ABSTENTION, clause_id="m0002"))
    assert r.outcome == "invalid"
    assert one(r, "schema-breach", "two identities").origin == "schema"
    assert run(ABSTENTION).outcome == "abstained"


def test_the_ATTEMPT_an_abstention_was_produced_on_is_recorded():
    """⚠️ A first-attempt abstention and one produced after failed repairs are
    not the same answer. The second is a repair-pressure artifact — the model
    was told three times it was wrong and took the exit — and treating the two
    alike lets a model abstain its way out of the hard clauses while the rate,
    which is the reliability signal, reads as if it had judged them.
    """
    assert run(ABSTENTION, attempt=1).first_attempt is True
    late = run(ABSTENTION, attempt=3)
    assert late.attempt == 3 and late.first_attempt is False


def test_an_unrecorded_attempt_is_UNKNOWN_and_not_silently_the_first():
    """⭐ The same lesson as `origin`, applied to the same class of field.

    Defaulting `attempt` to 1 would make a repair loop that forgot to pass it
    report every late abstention as a first-class first answer — a silent
    misclassification with nothing to notice it. Unrecorded is its own value.
    """
    r = run(ABSTENTION)
    assert r.attempt is None
    assert r.first_attempt is None, \
        "an unrecorded attempt was reported as the first one"


# ==========================================================================
#  5. Severity — which findings drive a repair
# ==========================================================================

def test_a_note_is_REPORTED_but_does_not_drive_a_repair():
    """⭐ THE RULING: only `error` drives repair. `note` is visible and inert.

    `requires-unprovided` is the case that forces it. At single-module scope a
    `requires` predicate is head-less BY DESIGN, so the finding fires on every
    correct module in this pipeline. Its only convergent repair is to move the
    predicate into `inputs` — which destroys the requires/inputs distinction the
    design calls load-bearing, and is attack A in `STEP_stage2_and_repair.md`
    §4. A loop driven by notes therefore does not terminate; it terminates by
    teaching the model to make every translation look fine.
    """
    r = run(module(requires=["restricted/1"], inputs=["new_material/1"],
                   asserts=[dict(status="forbid", act="produce(M)",
                                 body="new_material(M), restricted(M)",
                                 read_back="producing % is forbidden",
                                 read_back_slots=["M"], **TEXTUAL)]))
    f = one(r, "requires-unprovided", "restricted/1")
    assert f.severity == "note" and f.origin == "link"
    assert f in r.notes and f not in r.errors
    assert r.outcome == "translated", [x.message for x in r.errors]
    assert r.repair_needed is False


def test_an_error_DOES_drive_a_repair():
    """The control that must kill the test above: a `repair_needed` that is
    always False would pass it. `%% requires:` is dropped, so the same
    predicate becomes a name nothing declares at all."""
    # `restricted/1` is a policy classification another clause is expected to
    # define, so it is declared in `requires` — the schema now demands a real
    # declaration site (a concept-table row alone no longer counts), and
    # `requires` is head-less by design at single-module scope, exactly like
    # the old concept-only shape this test used to exercise.
    r = run(module(requires=["restricted/1"], inputs=["new_material/1"],
                   concepts=[concept(name="restricted", arity=1,
                                     gloss="falls under the restricted-content "
                                           "policy")],
                   asserts=[dict(status="forbid", act="produce(M)",
                                 body="new_material(M), restricted(M)",
                                 read_back="producing % is forbidden",
                                 read_back_slots=["M"], **TEXTUAL)]))
    # Declared in `requires` (schema) and in the concept table (link scope
    # has no provider), so `link.py` reports it — as a NOTE, because the
    # concept table declares it. That is `concept-declared`.
    assert one(r, "concept-declared", "restricted/1").severity == "note"
    assert r.repair_needed is False
    # ... and now the erroring twin: nothing declares it anywhere.
    r2 = run(module(requires=["restricted/1"], inputs=["new_material/1"],
                    asserts=[dict(status="forbid", act="produce(M)",
                                  body="new_material(M), restricted(M)",
                                  read_back="producing % is forbidden",
                                  read_back_slots=["M"], **TEXTUAL)],
                    beats=[fixtures.beat(loser="m0002")]))
    assert one(r2, "schema-breach", "beat itself").severity == "error"
    assert r2.repair_needed is True and r2.outcome == "invalid"


def test_the_severities_that_exist_are_the_two_link_py_emits():
    """A third severity invented here would silently escape the ruling above:
    `repair_needed` is defined as "any error", so an `error`-but-not-really
    level would drive repair and a `warning` level would not, with no test
    noticing which."""
    assert checks.SEVERITIES == ("error", "note")
    with pytest.raises(ValueError):
        checks.Finding("x", "warning", "w", "m", "schema")


# ==========================================================================
#  6. The concept table — the default that avoids the known flood
# ==========================================================================

def test_the_modules_own_concept_table_is_used_when_none_is_supplied():
    """⚠️ Running `link.collect` with NO table is the failure mode to avoid,
    not a neutral default: every declared concept then reads as undeclared and
    the tool floods with false positives that look exactly like real findings.
    That is what it did on the first live run — 7 UNRESOLVED REFERENCE(S), all
    seven declared.

    `run_checks` always holds the validated module, so the table is derivable
    (`schema.concept_rows`) and there is no reason to run without one.

    `new_material/1` keeps `module()`'s default `inputs` declaration here —
    the schema now requires a real declaration site (ontology/requires/inputs)
    for every body predicate, a concept-table row alone no longer counts — but
    it is ALSO carried in the concept table below, and the assertion that
    matters (`concept-declared`, a note) only fires when the module's own
    table is actually the one consulted, so the fallback this test targets is
    still exercised.
    """
    obj = module(concepts=[concept()])
    r = run(obj)
    assert of(r, "concept-table-absent") == []
    assert [f for f in of(r, "unresolved-reference")
            if "new_material/1" in f.message] == []
    assert one(r, "concept-declared", "new_material/1").severity == "note"


def test_a_SUPPLIED_table_is_used_instead_of_the_modules_own():
    """The control that must kill the test above.

    A corpus-wide table is the reason the parameter exists, and an
    implementation that ignored it in favour of the module's own rows would
    pass the test above and quietly disable the cross-clause checks. An EMPTY
    supplied table is the sharpest form: the module's pointer header then
    dangles, which is `concept-not-in-table`. That check reads only the
    `%% concepts:` pointer against the supplied table, so `new_material/1`
    keeps `module()`'s default `inputs` declaration (needed for schema to
    accept the module at all) without affecting it.
    """
    obj = module(concepts=[concept()])
    r = run(obj, concepts=[])
    f = one(r, "concept-not-in-table", "new_material/1")
    assert f.severity == "error" and f.origin == "link"
    assert r.repair_needed is True


# ==========================================================================
#  7. The finding record carries no answer
# ==========================================================================

def test_a_Finding_has_no_field_that_could_carry_an_expected_verdict():
    """Asserted as a FIELD SET, not as a natural-language property.

    `link.Finding` is pinned the same way by `link.py --self-test`. Stage 1 is
    denied the expected verdicts; a `fix` or `expected` field would put the
    answer into the prompt that is supposed to produce it, and every later
    measurement of whether repair worked would be measuring the hint.
    """
    fields = {f.name for f in dataclasses.fields(checks.Finding)}
    assert fields == {"check_id", "severity", "where", "message", "origin"}
