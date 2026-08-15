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
validate at all.

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
        # Both inputs glossed — a borrow with no gloss is its own schema
        # breach (2026-08-12 ruling, READBACK_SMOKE.md) and this test needs
        # the FABRICATED-CITATION breach to be the schema finding.
        concepts=[concept(),
                  dict(name="lifted_by_purpose", arity=1,
                       gloss="a stated aim the user offers as taking the "
                             "material outside the prohibition", **TEXTUAL)],
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
    design calls load-bearing, and is attack A in `resources/03_pipeline.md`,
    "the repair guard is TYPED, not sized". A loop driven by notes therefore
    does not terminate; it terminates by
    teaching the model to make every translation look fine.
    """
    r = run(module(requires=["restricted/1"], inputs=["new_material/1"],
                   # every borrow glossed (2026-08-12 ruling): this test is
                   # about the note/error split, not the gloss rule.
                   concepts=[concept(),
                             dict(name="restricted", arity=1,
                                  gloss="the material falls under a policy "
                                        "class another clause defines",
                                  **TEXTUAL)],
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
                   concepts=[concept(),   # the input's own gloss stays present
                             concept(name="restricted", arity=1,
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
                    # glossed like its twin above, so the ONLY breach is the
                    # self-beating `beats` entry this test is about.
                    concepts=[concept(),
                              concept(name="restricted", arity=1,
                                      gloss="falls under the restricted-content "
                                            "policy")],
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


# ==========================================================================
#  8. The declaration check is ARITY-AWARE  (DC-5)
# ==========================================================================
#
# ⭐ THE DEFECT THIS SECTION PINS. `schema.py`'s D4b builds its declaration set
# from predicate NAMES ONLY, so `inputs: ['conflict/2']` legalises a body atom
# `conflict(P1, P2, C)` and the module passes stage 2's contract half with ZERO
# breaches. The mismatch surfaces one stage later as a LINK finding — "`conflict/3`
# is used in a body, defined nowhere in this link scope" — which reads like a
# missing upstream module, and the repair rounds are spent looking for someone
# else's export. Four instances corpus-wide, all four on `unrepaired` clauses.
#
# ⚠️ THE JUDGEMENT CALL, RECORDED. Tightening this was NOT assumed to be right;
# the surrounding contract was read for a reason the permissive behaviour might
# be deliberate, and it says the opposite three times over: the requires/inputs
# format guard refuses an entry that is not `name/arity` *because* "two
# predicates sharing a name but taking different numbers of arguments are
# different predicates"; D4b's own message says "`{name}/N` must ALSO appear in
# one of those three"; and `link._atom_id` exists so a body atom and a header
# entry can be compared BY IDENTITY, name and arity together. No contract text,
# fixture or ruling anywhere permits a module to declare one arity and use
# another. It is an implementation slip in one expression, not a tolerance.

ARITY_MARK = checks.ARITY_MESSAGE_MARK

GRAVEYARD = (HERE / "resolve_runs" / "graph_v2" / "translation_sample"
             / "repair_graveyard")


def arity_errors(result):
    return [f for f in result.findings if ARITY_MARK in f.message]


def test_a_name_used_at_the_wrong_arity_is_an_ERROR_that_names_BOTH():
    """The message has to carry the declared arity AND the used one.

    "`new_material/2` is used in a body and declared nowhere" sends the model
    hunting for another module. "declared at /1, used at /2" is repairable from
    inside this module, which is where the defect actually is.
    """
    r = run(module(asserts=[dict(status="forbid", act="produce(M)",
                                 body="new_material(M, sensitive)",
                                 read_back="producing % is forbidden",
                                 read_back_slots=["M"], **TEXTUAL)]))
    assert r.outcome == "invalid"
    f = one(r, "schema-breach", ARITY_MARK)
    assert f.origin == "schema" and f.severity == "error"
    assert "`new_material/1`" in f.message and "`new_material/2`" in f.message
    assert f.where == "asserts[0]"
    assert r.repair_needed is True


def test_the_arity_check_is_SILENT_when_the_declared_arity_is_the_one_used():
    """The negative control. A check that fires on every declared name would
    pass the test above and reject every correct module in the corpus."""
    r = run()
    assert arity_errors(r) == []
    assert r.outcome == "translated"


def test_a_name_declared_at_TWO_arities_is_silent_at_both():
    """The second control, and the reason membership is tested against a SET.

    Declaring `new_material/1` and `new_material/2` and using both is legal —
    they are two predicates, and both are declared.
    """
    obj = module(
        inputs=["new_material/1", "new_material/2"],
        concepts=[concept(), concept(arity=2)],
        asserts=[dict(status="forbid", act="produce(M)",
                      body="new_material(M), new_material(M, sensitive)",
                      read_back="producing % is forbidden",
                      read_back_slots=["M"], **TEXTUAL)])
    r = run(obj)
    assert arity_errors(r) == []
    assert r.outcome == "translated", [f.message for f in r.errors]


def test_an_UNDECLARED_name_still_gets_the_old_message_and_only_that_one():
    """⛔ THE MASKING CONTROL. The new check must not take over
    `undeclared-body-name`: a name declared NOWHERE is one defect and must
    produce ONE message. If the arity check fired on it too, the model would be
    told both "nothing declares it" and "declared at /1, used at /2" about a
    single name, and the second would be a lie.
    """
    obj = module(inputs=[], concepts=[])
    r = run(obj)
    assert r.outcome == "invalid"
    old = one(r, "schema-breach", "nothing declares it")
    assert "new_material" in old.message
    assert arity_errors(r) == []
    # ⚠️ ASSERTED ON THE PURE FUNCTION TOO. A D4b breach means the module never
    # CONSTRUCTS, so `run_checks` returns before the arity check runs and the
    # line above would hold for an implementation that masks freely. This is
    # the line that actually tests the rule.
    assert checks.arity_mismatches(obj) == []


def test_an_undeclared_name_used_at_a_second_arity_is_STILL_only_the_old_one():
    """The sharper half of the masking control: the name is absent from every
    declaration site AND the body uses two different arities of it. Still one
    mechanism, still `undeclared-body-name`."""
    obj = module(inputs=[], concepts=[],
                 asserts=[dict(status="forbid", act="produce(M)",
                               body="new_material(M), new_material(M, x)",
                               read_back="producing % is forbidden",
                               read_back_slots=["M"], **TEXTUAL)])
    r = run(obj)
    assert r.outcome == "invalid"
    assert arity_errors(r) == []
    # D4b reports the name once per occurrence; what matters is that EVERY
    # message about it is the undeclared one and none is an arity claim.
    assert all("nothing declares it" in f.message for f in r.findings)
    assert checks.arity_mismatches(obj) == []


def test_an_abstention_never_acquires_an_arity_finding():
    """An abstention is forced empty on every content field, so it has no body
    to check — and the check is placed AFTER the terminal return so it could
    not turn one into a repair round even if it did."""
    r = run(ABSTENTION)
    assert r.outcome == "abstained" and r.findings == []


def test_the_arity_finding_is_DISCLOSABLE_to_the_repair_prompt():
    """⭐ The check exists to change what the model is TOLD. `translate.py`
    filters the repair log by `origin`, and only `DISCLOSABLE_ORIGINS` reach
    it — a new origin invented for this finding would be withheld from the one
    prompt it is for, silently and with the test suite green.
    """
    import translate                       # read-only: the consumer's filter
    r = run(module(asserts=[dict(status="forbid", act="produce(M)",
                                 body="new_material(M, sensitive)",
                                 read_back="producing % is forbidden",
                                 read_back_slots=["M"], **TEXTUAL)]))
    f = one(r, "schema-breach", ARITY_MARK)
    assert f.origin in translate.DISCLOSABLE_ORIGINS
    log = translate.render_error_log([("attempt 1", r.findings)])
    assert ARITY_MARK in log and "new_material/2" in log


# ---- the pure core, over the FOUR REAL INSTANCES -------------------------
#
# ⭐ READ-ONLY, FROM THE CORPUS, AND NOT THROUGH `schema.Module`. These are the
# four stored modules the mechanism was measured on. Three of them validate
# TODAY with zero breaches — which is the defect stated as an experiment — and
# the fourth (`l1_170_n088`) no longer CONSTRUCTS, because it also trips D4b on
# a different, undeclared name. That is exactly why `arity_mismatches` takes the
# raw dict as well as a module: the instance that proves the two checks coexist
# is one that cannot be built. Nothing under `resolve_runs/` is written.

def stored(path):
    import json
    return json.loads((GRAVEYARD / path).read_text(encoding="utf-8"))


def stored_last_attempt(path):
    """The final assistant turn of a graveyard transcript, as the module dict."""
    import json
    turns = stored(path)
    last = [t for t in turns if t.get("role") == "assistant"][-1]
    return json.loads(last["content"])


REAL = [
    # clause                   file                                name                 declared used
    ("l1_170_n047", "l1_170_n047-20260815-040445/module.json", "conflict", 2, 3),
    ("l1_170_n087", "l1_170_n087-20260815-040444/module.json",
     "output_consumed_by", 2, 1),
    ("l171_426_n024", "l171_426_n024-20260815-073255/module.json",
     "user_request", 1, 2),
]


@pytest.mark.parametrize("clause_id,path,name,declared,used", REAL)
def test_the_real_corpus_instances_are_caught(clause_id, path, name,
                                              declared, used):
    obj = stored(path)
    assert obj["clause_id"] == clause_id
    hits = [h for h in checks.arity_mismatches(obj) if h[1] == name]
    assert hits, f"{clause_id}: {name} mismatch not detected"
    for _where, _n, known, got in hits:
        assert known == [declared] and got == used
    msgs = [f.message for f in checks.arity_findings(obj)]
    assert any(f"`{name}/{declared}`" in m and f"`{name}/{used}`" in m
               and ARITY_MARK in m for m in msgs), msgs


def test_the_fourth_instance_n088_is_caught_on_a_module_that_cannot_be_BUILT():
    """`l1_170_n088` declares `sequence_of_messages/3` and writes it at /4, and
    separately references an undeclared name — so `schema.validate_all` returns
    no module at all and reports only the undeclared one. The arity defect is
    still there, still invisible, and still what the model was never told."""
    obj = stored_last_attempt("l1_170_n088-20260815-040444/transcript.json")
    mod, breaches = schema.validate_all(obj)
    assert mod is None
    assert any("nothing declares it" in b.message for b in breaches)
    assert not any(ARITY_MARK in b.message for b in breaches), \
        "schema.py grew the check; this pin now belongs there"
    hits = checks.arity_mismatches(obj)
    assert [(h[1], h[2], h[3]) for h in hits] == \
        [("sequence_of_messages", [3], 4)]


def test_the_three_buildable_instances_pass_schema_with_ZERO_breaches():
    """⭐ THE DEFECT, STATED AS A MEASUREMENT. If this ever fails, the
    name-only matching in `schema.py` was fixed and the check moved upstream —
    which is the intended end state, not a regression. Read
    `_debug_gen11/PROPOSED_schema_arity.md` before deleting anything here.
    """
    for _cid, path, _n, _d, _u in REAL:
        mod, breaches = schema.validate_all(stored(path))
        assert mod is not None and breaches == [], \
            f"{path}: {[b.message for b in breaches]}"
        assert checks.arity_mismatches(mod), \
            f"{path}: the mismatch is invisible through the module object too"


def test_the_corpus_instances_are_not_a_general_indictment():
    """The control on the corpus pins. A detector that flagged every stored
    module would satisfy every test above. Over the whole stored translation
    sample the rate must be SMALL and the four known clauses must be the ones
    it names.
    """
    import json
    flagged = set()
    scanned = 0
    for path in sorted(GRAVEYARD.parent.rglob("*.json")):
        if path.name in ("run.json", "concepts.json", "findings.json",
                         "entry.json") or path.name.endswith(".version.json"):
            continue
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if not isinstance(obj, dict) or "asserts" not in obj:
            continue
        scanned += 1
        if checks.arity_mismatches(obj):
            flagged.add(obj.get("clause_id"))
    assert scanned > 100, f"only {scanned} stored modules found — path drift?"
    assert flagged == {"l1_170_n047", "l1_170_n087", "l171_426_n024"}, flagged
    # ⚠️ NOT pinned as a count of a live artifact — the SET is what is claimed,
    # and `n088` is absent from it because its module was never stored.


# ---- the two pure helpers, pinned on their own ---------------------------

def test_body_uses_counts_arity_at_paren_depth_zero():
    """`p(f(a, b), C)` is arity 2, not 3. Counting commas would make every
    nested term a false mismatch, and the corpus is full of them."""
    assert checks.body_uses("p(f(a, b), C)") == [("p", 2), ("f", 2)]
    assert checks.body_uses("q(X), not r(X, Y)") == [("q", 1), ("r", 2)]
    assert checks.body_uses("") == []


def test_declared_arities_reads_all_three_sites_and_NOT_concepts():
    """⛔ `concepts` is not a declaration site — the contract is explicit that a
    concept says what a name MEANS, never that anything defines it. A version
    that read arities off the concept table would silence the real instances,
    every one of which declares its concept at the arity it uses.
    """
    obj = module(ontology=[dict(atom="restricted(csam)", body=None,
                                gloss="the material is restricted", **TEXTUAL)],
                 requires=["policy/2"], inputs=["new_material/1"])
    got = checks.declared_arities(obj)
    assert got["restricted"] == {1}
    assert got["policy"] == {2}
    assert got["new_material"] == {1}
    # the module's concept table declares `new_material/1`; a concept-reading
    # implementation would be indistinguishable here without this line
    assert set(got) == {"restricted", "policy", "new_material"}
