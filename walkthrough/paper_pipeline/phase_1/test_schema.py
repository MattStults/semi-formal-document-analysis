"""Tests for the stage-1 output contract.

    ../../../semi-formal-experiment/.venv/bin/python -m pytest \
        walkthrough/paper_pipeline/phase_1/ -q

⚠️ HOW THESE WERE VERIFIED, stated because the ordinary claim would be false.
These were written AFTER the fixes they cover, so they were never RED-in-time.
Each one is instead verified by MUTATION — `mutate_schema.py` deletes the guard
it targets and asserts the test goes red. A test that survives its own guard's
deletion is pinning nothing, and the `mutation` marker on each test names the
guard that must kill it.

Run `python3 mutate_schema.py` to re-verify. That is the honest substitute for
RED-first and it is stronger in one way: it re-checks on every run, whereas a
red seen once in the past is a memory.
"""

import json
import re
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fixtures  # noqa: E402  ⭐ the shared fixtures — see its module docstring
import schema  # noqa: E402

VENV_PY = HERE.parents[2] / "semi-formal-experiment" / ".venv" / "bin" / "python"

# ⭐ ONE definition of the contract, in `fixtures.py`, shared with
# `test_checks.py`, `test_repair.py` and `../../test_link.py`. Four private
# copies of `module()` used to disagree about what a valid module was, and one
# of them was WRONG for months with nothing to compare it against.
LIC = fixtures.WORLD
RB = fixtures.NO_SLOTS

module = fixtures.module
abstention = fixtures.abstention
beat = fixtures.beat


IDS = {"m0001", "m0002", "m0255", "m0204", "m0203", "m0208", "m0252"}


def bad(obj, fragment, clause_id=None, ids=None):
    """Assert the contract rejects `obj`, and rejects it for the right reason.

    Matching the MESSAGE, not just the exception class, is deliberate: three of
    this harness's own self-test checks were found passing because an unrelated
    guard raised the same class first.
    """
    with pytest.raises(schema.ModuleValidationError) as exc:
        schema.validate(obj, clause_id=clause_id, known_clause_ids=ids)
    assert fragment.lower() in str(exc.value).lower(), (
        f"rejected, but for the wrong reason.\nexpected to mention: "
        f"{fragment!r}\ngot: {exc.value}")


# ---------------------------------------------------------------- the happy path

def test_minimal_module_is_accepted():
    """A check that fires on everything is useless."""
    m = schema.validate(module(), clause_id="m0001", known_clause_ids=IDS)
    assert m.outcome == "translated" and len(m.asserts) == 1


def test_every_shared_fixture_is_a_module_the_contract_ACCEPTS():
    """⭐ THE ONE PLACE a contract change breaks the shared fixtures.

    `fixtures.py` is a SPECIFICATION of the stage-1 output contract, used by
    four test files. Before it existed each file carried its own copy, so a
    contract change broke all four in four different ways with four different
    error messages — and, worse, the copies could disagree about what was valid
    without anything noticing. One of them did: `test_link.py`'s `political()`
    declared its predicates only as `concepts`, a module whose single rule can
    never fire, and it sat in a test asserting it was correct.

    This asserts every named variant still validates, naming the one that
    stopped. `module_json()` is checked to be a SERIALISATION of `module()`
    rather than a second definition of it — that is the duplication in the
    smallest form it could come back in.
    """
    for name, build in sorted(fixtures.VALID_MODULES.items()):
        obj = build()
        try:
            schema.validate(obj, clause_id=obj["clause_id"],
                            known_clause_ids=IDS | {obj["clause_id"]})
        except schema.ModuleValidationError as exc:
            pytest.fail(f"the shared fixture `fixtures.{name}()` is no longer "
                        f"a valid module: {exc}")

    assert json.loads(fixtures.module_json()) == fixtures.module()
    assert json.loads(fixtures.abstention_json()) == fixtures.abstention()


def test_the_shape_we_teach_is_a_shape_the_contract_accepts():
    """The prompt's worked examples must validate, or we teach a rejected shape.

    This is the check whose absence let the earlier contract ship an example
    that did not compile.
    """
    doc = (HERE / "prompt" / "20_worked_example.md").read_text()
    blocks = re.findall(r"```json\n(.*?)```", doc, re.S)
    assert len(blocks) >= 2, "the worked-example file lost its JSON blocks"
    for blk in blocks[:2]:
        obj = json.loads(blk)
        schema.validate(obj, clause_id=obj["clause_id"], known_clause_ids=IDS)


@pytest.mark.parametrize("which", [0, 1])
def test_the_worked_examples_compile_in_clingo(which, tmp_path):
    """Rendering is not enough: the file has to be one clingo will load.

    `act(produce(M)).` and `asserts(m1, permit, produce(M)).` both passed every
    validator and both made clingo reject the WHOLE file. Only running it
    catches that.
    """
    doc = (HERE / "prompt" / "20_worked_example.md").read_text()
    obj = json.loads(re.findall(r"```json\n(.*?)```", doc, re.S)[which])
    mod = schema.validate(obj, clause_id=obj["clause_id"], known_clause_ids=IDS)
    lp = tmp_path / "m.lp"
    lp.write_text(schema.render_lp(
        mod, {"section_id": "s", "kind": "conditional", "quote": "text"}))
    r = subprocess.run([str(VENV_PY), "-m", "clingo", str(lp), "--outf=3"],
                       capture_output=True, text=True)
    errs = [ln for ln in (r.stdout + r.stderr).splitlines()
            if "error" in ln.lower()]
    assert not errs, f"clingo rejected the rendered module: {errs[:2]}"


# --------------------------- `_` in a HEAD term slot: the SOLVER's rule, ours
# mutation: _check_term's _ANON branch
#
# ⚠️ THE GROUND UNDER THIS TEST CHANGED ON 2026-08-07, and so did its scope.
# It used to say `_` "breaks the explainer" (failure mode 7). That is false:
# clingo derives `p(a)` from `p(X) :- q(X,_). q(a,b).`, and ASP2CNL renders `_`
# by skipping hidden terms. The BODY half of the old guard was deleted for that
# reason.
#
# ⭐ The term-slot half survives on an independent ground that nobody had run:
# every slot `_check_term` guards is rendered into a rule HEAD, and `_` in a
# head is unsafe however the body is written —
#
#     q(a). p(_) :- q(X).   ->   error: unsafe variables in: p(#Anon0):-…;q(X).
#
# so this is clingo refusing the whole file, not a tool we wrote being fussy.
# ⚠️ Note the `act` case below carries a BODY: under the old renderer ground
# that was the same failure as the others, and under the real one it is the
# case that shows the body does not rescue a head.

@pytest.mark.parametrize("field,obj", [
    ("act", module(acts=["produce(_)"],
                   asserts=[dict(status="forbid", act="produce(_)", body="x(M)",
                                 read_back="r", read_back_slots=[],
                                 licence="textual", cites="m0001",
                                 inference=None, toggleable=False)],
                   closure=[dict(act_class="produce", closure="cepa",
                                 reason="r")], requires=["x/1"])),
    ("ontology atom", module(ontology=[dict(
        atom="restricted(_)", gloss="g", body=None, **LIC)])),
    ("defines term", module(defines=[dict(
        kind="prohibited", term="csam(_)", **LIC)])),
])
def test_anonymous_variable_rejected_in_every_HEAD_term_slot(field, obj):
    bad(obj, "anonymous variable")


def test_an_anonymous_variable_in_a_BODY_is_rejected_BECAUSE_XCLINGO_DIES(
        tmp_path):
    """⛔ This guard was withdrawn on 2026-08-07 and restored the same day, and
    this test exists so that cannot happen a third time.

    The withdrawal argued "the renderer can cope", evidenced with bare clingo
    (which does derive from `p(X) :- q(X,_)`) and with the published ASP2CNL
    renderer (which skips hidden terms). Both claims were TRUE and both were
    about the wrong tool. `03_pipeline.md` names **xclingo**, and stage 4's R3
    derivation layer is built on it.

    ⭐ So this test does not merely assert that the validator complains — that
    is what the old test did, and it is exactly what let the guard be withdrawn
    on a false premise. It RUNS XCLINGO and pins the ground itself, with a
    named-variable control proving the failure is caused by the `_` and not by
    the fixture.
    """
    assert_raises_on = module(ontology=[dict(
        atom="disallowed(M)", gloss="the material is disallowed",
        body="restricted(M), tag(M, _)", **ASSUMED)], requires=["restricted/1", "tag/2"])
    bad(assert_raises_on, "anonymous variable")

    # ---- and the reason, executed ----
    xclingo = os.path.join(os.path.dirname(str(VENV_PY)), "xclingo")
    assert os.path.exists(xclingo), (
        "xclingo is missing from the venv, so this test cannot verify its own "
        "ground. It must not pass quietly: install it or delete this test "
        "deliberately (DEBUGGING_TIPS entry 8)")

    def run(body):
        f = tmp_path / f"probe_{abs(hash(body))}.lp"
        f.write_text('q(a,b).\n%!trace_rule {"p holds of %", X}.\n'
                     f"p(X) :- {body}.\n" '%!show_trace {p(X)}.\n')
        r = subprocess.run([xclingo, "--output", "ascii-trees", "-n", "0", "0",
                            str(f)], capture_output=True, text=True)
        return r.stdout + r.stderr

    anon, named = run("q(X,_)"), run("q(X,Y)")
    assert "unsafe" in anon.lower(), (
        "xclingo accepted an anonymous variable in a rule body — the ground for "
        "this guard has changed and the guard should be RE-EXAMINED, not this "
        f"test relaxed. Output:\n{anon[:400]}")
    assert "p holds of a" in named, (
        "the named-variable control did not render either, so the fixture is "
        f"broken and the assertion above proves nothing. Output:\n{named[:400]}")


# ------------------------------------------------- unsafe variables kill files
# mutation: _check_term's allow_vars branch

def test_unbound_variable_with_no_body_is_rejected():
    """`asserts(m1, forbid, produce(M)).` is `unsafe variables` to clingo.

    Not a warning — clingo refuses the entire file, so one such assertion makes
    every other clause in the link set unreadable.
    """
    bad(module(asserts=[dict(status="forbid", act="produce(M)", body=None,
                             read_back="r", read_back_slots=[],
                             licence="textual", cites="m0001",
                             inference=None, toggleable=False)]),
        "unsafe")


def test_a_variable_WITH_a_body_to_bind_it_is_fine():
    """The guard must not reject the ordinary case."""
    schema.validate(module(), clause_id="m0001", known_clause_ids=IDS)


def test_a_ground_act_needs_no_body():
    schema.validate(module(
        acts=["say_cannot_answer"],
        asserts=[dict(status="oblige", act="say_cannot_answer", body=None,
                      read_back="r", read_back_slots=[], licence="textual",
                      cites="m0001", inference=None, toggleable=False)],
        closure=[dict(act_class="say_cannot_answer", closure="cnpa",
                      reason="r")], ontology=[], requires=[]),
        clause_id="m0001", known_clause_ids=IDS)


# ------------------------------------------------------- Invariant 2, licences
# mutation: Licensed._licence_obligations

def test_textual_without_a_citation():
    bad(module(ontology=[dict(atom="p(M)", gloss="g", body=None,
                              licence="textual", cites=None, inference=None,
                              toggleable=False)]),
        "no citation")


def test_assumed_without_a_named_inference():
    bad(module(ontology=[dict(atom="p(M)", gloss="g", body=None,
                              licence="assumed", cites=None, inference="  ",
                              toggleable=False)]),
        "unnamed inference")


def test_world_that_is_not_toggleable():
    bad(module(ontology=[dict(atom="p(M)", gloss="g", body=None,
                              licence="world", cites=None, inference=None,
                              toggleable=False)]),
        "toggleable")


def test_a_licensed_world_fact_is_ACCEPTED():
    """The graded licence marks non-textual facts; it does not ban them.

    Rejecting this would re-create the binary rule `03_pipeline.md` records as
    wrong twice over — it contradicts a standing ruling and rejects the only
    translation ever built for this pipeline.
    """
    schema.validate(module(ontology=[dict(
        atom="protects_third_party(M)", gloss="the policy protects a party "
        "outside the conversation", body="disallowed(M)", **LIC)],
        requires=["disallowed/1"]),
        clause_id="m0001", known_clause_ids=IDS)


# ------------------------------------------------------------- Invariant 1
# mutation: OntologyFact gloss branch

def test_ontology_predicate_without_a_gloss():
    """A symbol must resolve to a concept with a WRITTEN DEFINITION.

    Without it the read-back renders the label, and a clause pointing at the
    wrong concept produces a paraphrase that reads correctly.
    """
    bad(module(ontology=[dict(atom="p(M)", gloss="   ", body="disallowed(M)",
                              **LIC)], requires=["disallowed/1"]),
        "gloss")


# ---------------------------------------------------- the link-check distinction
# mutation: Module._coherent overlap branch

def test_requires_and_inputs_must_be_disjoint():
    """Measured: the model put all seven predicates in BOTH lists.

    Without the distinction, "a name nothing defines" cannot be told from "a
    name supplied at query time", and every translation looks broken or every
    one looks fine.
    """
    bad(module(requires=["restricted/1"], inputs=["restricted/1"]), "both")


def test_predicates_carry_arity():
    bad(module(requires=["restricted"]), "name/arity")


def test_a_body_predicate_nothing_declares():
    """D4b level 1: an undeclared name cannot be told from a typo."""
    bad(module(requires=[]), "nothing declares it")


# ------------------------------------------------- the FORCED closure (the ruling)
# mutation: Module._coherent closure branch

def test_missing_closure_declaration_is_rejected():
    """An absent declaration reads as CEPA silently.

    Measured: the contradiction verdict FLIPS on the closure, and `open` and
    `cepa` are bit-identical — nothing recorded that a commitment was made.
    """
    bad(module(closure=[]), "closure")


def test_closure_for_an_act_class_not_governed():
    bad(module(closure=[
        dict(act_class="produce", closure="cepa", reason="r"),
        dict(act_class="interject", closure="cnpa", reason="r")]),
        "does not govern")


def test_closure_without_a_reason():
    bad(module(closure=[dict(act_class="produce", closure="cepa",
                             reason="  ")]), "reason")


# ------------------------------------------------------- namespace separation
# mutation: _check_body / OntologyFact BEHAVIOUR_NS branch

def test_the_behaviour_namespace_is_rejected():
    """Stage 1 is denied any behaviour, and the separation is mandatory.

    One cross-namespace `beats` fact silently ERASES a real conflict —
    satisfiably, with the acyclicity guard quiet.
    """
    bad(module(asserts=[dict(status="forbid", act="produce(M)",
                             body="b_asserts(h, forbid, produce(M))",
                             read_back="r", read_back_slots=[],
                             licence="textual", cites="m0001",
                             inference=None, toggleable=False)]),
        "behaviour")


def test_the_relation_schema_cannot_be_redefined_as_ontology():
    bad(module(ontology=[dict(atom="asserts(x)", gloss="g", body=None, **LIC)]),
        "relation schema")


# ------------------------------------------------------- identity and citation
# mutation: validate()'s clause_id / known_clause_ids branches

def test_a_module_that_renames_itself():
    bad(module(clause_id="m0002"), "two identities", clause_id="m0001")


def test_a_fabricated_citation():
    """Invariant 2's error text claimed this protection before it existed."""
    bad(module(asserts=[dict(status="forbid", act="produce(M)",
                             body="disallowed(M)", read_back="r",
                             read_back_slots=[], licence="textual",
                             cites="m9999", inference=None,
                             toggleable=False)]),
        "not a clause in this corpus", ids=IDS)


def test_citation_checking_is_OFF_when_no_corpus_is_supplied():
    """Silently skipping is fine only if the caller chose to skip."""
    schema.validate(module(asserts=[dict(
        status="forbid", act="produce(M)", body="disallowed(M)",
        read_back="r", read_back_slots=[], licence="textual", cites="m9999",
        inference=None, toggleable=False)]))


# ------------------------------------------------------------------ read-backs
# mutation: ReadBack._readback_ok

def test_read_back_with_a_newline():
    """A `\\n` produces a file clingo cannot parse, from a run reporting OK."""
    bad(module(asserts=[dict(status="forbid", act="produce(M)",
                             body="disallowed(M)",
                             read_back="line one\nline two", read_back_slots=[],
                             licence="textual", cites="m0001", inference=None,
                             toggleable=False)]),
        "newline")


def test_read_back_slot_count_must_match_its_arguments():
    bad(module(asserts=[dict(status="forbid", act="produce(M)",
                             body="disallowed(M)",
                             read_back="% and %", read_back_slots=["M"],
                             licence="textual", cites="m0001", inference=None,
                             toggleable=False)]),
        "slot")


# ----------------------------------------------------------------- abstention

def test_abstention_needs_a_reason():
    bad(abstention(abstain_reason="  "), "no reason")


def test_abstention_carrying_content_is_neither():
    bad(abstention(claims=["C1"]), "abstention with content")


def test_a_valid_abstention_renders_as_one():
    m = schema.validate(abstention())
    lp = schema.render_lp(m, {"section_id": "s", "kind": "meta", "quote": "x"})
    assert "%% ABSTAIN:" in lp and "asserts(" not in lp


def test_a_translation_that_emitted_nothing():
    bad(module(asserts=[], ontology=[], beats=[], defines=[], requires=[],
               acts=[], closure=[]),
        "abstention that did not say so")


# ---------------------------------------------------------------- superiority

def test_a_clause_cannot_beat_itself():
    bad(module(beats=[beat(loser="m0002")]), "beat itself")


def test_a_module_may_only_record_superiority_its_own_clause_states():
    bad(module(beats=[beat(sayer="m0002")]), "not this clause")


# ------------------------------------------------------------- the wire schema

def test_wire_schema_is_flat_and_strict_at_every_level():
    """Checked at EVERY level, not just the top.

    The earlier assertions inspected only the root, and would have passed with
    an optional nested model silently collapsed to a string.
    """
    sch = schema.json_schema()
    blob = json.dumps(sch)
    assert "$ref" not in blob and "$defs" not in blob

    seen = 0
    def walk(node):
        nonlocal seen
        if isinstance(node, list):
            return [walk(x) for x in node]
        if not isinstance(node, dict):
            return node
        t = node.get("type")
        if t == "object" or (isinstance(t, list) and "object" in t):
            seen += 1
            assert node.get("additionalProperties") is False, node.get("title")
            if "properties" in node:
                assert set(node["required"]) == set(node["properties"])
        for v in node.values():
            walk(v)
    walk(sch)
    assert seen >= 5, f"only {seen} object levels found; nesting was lost"


def test_optional_fields_render_as_nullable_types_not_anyOf():
    sch = schema.json_schema()
    assert sch["properties"]["abstain_reason"]["type"] == ["string", "null"]


def test_optional_list_keeps_its_items():
    """The nullable rewrite used to drop the surviving branch's body."""
    for prop in schema.json_schema()["properties"].values():
        if isinstance(prop.get("type"), list) and "array" in prop["type"]:
            assert "items" in prop, "an optional list lost its items schema"


# --------------------------------------------------------------- rendering

def test_rendering_is_deterministic():
    m = schema.validate(module(), clause_id="m0001", known_clause_ids=IDS)
    clause = {"section_id": "s", "kind": "conditional", "quote": "text"}
    assert schema.render_lp(m, clause) == schema.render_lp(m, clause)


def test_rendering_carries_the_licence_of_every_fact():
    """The licence must survive into the artifact, not be lost in the object."""
    m = schema.validate(module(), clause_id="m0001", known_clause_ids=IDS)
    lp = schema.render_lp(m, {"section_id": "s", "kind": "c", "quote": "x"})
    assert "% [T] m0001" in lp and "% [A] named step" in lp


def test_rendering_carries_the_closure_and_the_interface():
    m = schema.validate(module(), clause_id="m0001", known_clause_ids=IDS)
    lp = schema.render_lp(m, {"section_id": "s", "kind": "c", "quote": "x"})
    assert "%% closure: produce = cepa" in lp
    assert "%% requires: restricted/1" in lp
    assert "%!trace_rule" in lp


# ==========================================================================
#  Concepts — the declaration form, split from the classification facts.
#  Written BEFORE the implementation. These are RED until `Concept` exists.
# ==========================================================================

concept = fixtures.concept


def test_a_concept_declaration_is_accepted():
    """4 of 4 live clauses returned exactly this and the contract rejected it.

    The model was not asserting a classification; it was introducing a concept
    and its meaning. There was no slot for that, so the only expressible shape
    was `assistant_entity(E)` with no body — which clingo refuses outright.
    """
    m = schema.validate(fixtures.definitional_module(),
                        clause_id="m0001", known_clause_ids=IDS)
    assert m.concepts[0].name == "assistant_entity"


def test_a_concept_does_NOT_declare_the_predicate_for_the_undeclared_check():
    """Inverted. A concept says what a predicate MEANS, not that anything
    defines it. Counting it as a declaration let a rule pass whose body could
    never be satisfied — measured on a real module."""
    bad(module(concepts=[concept(name="restricted", arity=1,
                                 gloss="falls under the restricted policy")],
               requires=[]),
        "nothing declares it")


def test_a_concept_carries_a_licence_like_everything_else():
    bad(module(concepts=[concept(licence="textual", cites=None)],
               requires=[]),
        "no citation")


def test_a_concept_needs_a_gloss():
    bad(module(concepts=[concept(gloss="   ")], requires=[]), "gloss")


def test_a_concept_its_own_clause_does_not_use_is_ACCEPTED():
    """Introducing vocabulary it does not itself use is what a definition DOES.

    This test inverts an earlier one. A hard "declared but unreferenced" check
    fired on 2 of the first 4 live clauses and was WRONG on both: m0053
    introduces both `assistant` and `agent` and defines only `assistant`.
    Deadness is a corpus-level property — see DEFERRED.md D-3.
    """
    schema.validate(
        module(concepts=[concept(name="agent_entity", arity=1,
                                 gloss="sometimes used for autonomous "
                                       "deployments")]),
        clause_id="m0001", known_clause_ids=IDS)


def test_concepts_do_NOT_appear_in_the_rendered_lp():
    """The concept dictionary is its own artifact, not a comment in a logic file.

    Burying it in `.lp` comments means every consumer — the read-back, the
    normaliser, a human reading the vocabulary — has to regex ASP to recover
    it. `05_practice` §2.3 records a published ontology that did exactly this:
    60+ citations in prose, and *"you cannot ask which classes derive from
    Article 5 without regexing English."*
    """
    # A DISTINCTIVE gloss: an earlier version of this test used "g", which
    # occurs in half the lines of any file, so the containment check passed
    # vacuously in one direction and failed spuriously in the other.
    GLOSS = "ZZQ the material falls under the restricted-content policy ZZQ"
    m = schema.validate(
        module(concepts=[concept(name="restricted", arity=1, gloss=GLOSS)],
               requires=["restricted/1"]),
        clause_id="m0001", known_clause_ids=IDS)
    lp = schema.render_lp(m, {"section_id": "s", "kind": "c", "quote": "x"})
    # The DEFINITION must not be here — that is the artifact-splitting rule.
    assert not any(m.concepts[0].gloss in ln for ln in lp.splitlines()), \
        "the gloss belongs to the concept table, not the logic file"
    # A signature POINTER is wanted: a reader should see that concepts exist
    # and where to look, without the content being duplicated here.
    assert "%% concepts: restricted/1" in lp
    assert schema.concept_rows(m)[0]["gloss"] == m.concepts[0].gloss


def test_the_concept_table_is_emitted_as_data():
    """One row per concept, joinable across clauses, with its provenance."""
    m = schema.validate(
        module(concepts=[concept(name="restricted", arity=1, gloss="g")],
               requires=["restricted/1"]),
        clause_id="m0001", known_clause_ids=IDS)
    rows = schema.concept_rows(m)
    assert rows == [dict(concept="restricted/1", clause_id="m0001",
                         gloss="g", licence="textual", cites="m0001",
                         inference=None)]


# ==========================================================================
#  The 21 SURVIVORS of the first mutation run — guards nothing pinned.
#
#  `mutate_schema.py` reported 46 guards, 25 killed, 21 SURVIVORS: guards a
#  refactor could delete with the whole suite staying green. Each test below
#  closes exactly one, and each was driven RED by deleting its own guard with
#     mutate_schema.py --only "<a fragment of the guard's source>"
#  and reading the test's name out of the `tests killed` column. Passing
#  against the real file is worth nothing on its own — that is the defect
#  these tests exist to repair, not the standard they have to meet.
#
#  ⚠️ Every fixture here is checked for the message it actually produces, not
#  just for rejection. `module()` is a minimal valid module, so a mutation of
#  it that trips a DIFFERENT guard first looks pinned and is not. Where a
#  fixture needed extra `ontology`/`requires` entries, they are there to keep
#  the module valid ONCE THE GUARD IS DELETED — so the mutated run reaches a
#  clean accept and the test fails for its own reason.
# ==========================================================================

ASSUMED = fixtures.ASSUMED
TEXTUAL = fixtures.TEXTUAL

#: `module()`'s own assertion, so one field can be varied in isolation.
an_assert = fixtures.assertion


# ------------------------------------------------- _TERM itself, not just _ANON
# mutation: _check_term / "is not a term at all"
#
# The regex was tightened from `.*` because `.*` "admitted an entire rule as a
# fact" — and nothing tested the tightening. Under `.*` (or with the raise
# deleted) both fixtures below VALIDATE, and a whole rule is smuggled into a
# term slot where the renderer will interpolate it into `asserts/3`.

@pytest.mark.parametrize("case", ["ontology atom", "defines term"])
def test_a_whole_rule_in_a_term_slot_is_not_a_term(case):
    if case == "ontology atom":
        obj = module(
            ontology=[dict(atom="restricted(M) :- material(M)",
                           gloss="the material falls under the policy",
                           body="material(M)", **ASSUMED),
                      dict(atom="disallowed(M)",
                           gloss="the material is disallowed",
                           body="restricted(M)", **ASSUMED)],
            requires=["material/1", "restricted/1"])
    else:
        obj = module(defines=[dict(kind="prohibited",
                                   term="csam :- restricted", **LIC)])
    bad(obj, "is not a term")


# ----------------------------------------------------- _check_body, all three
# mutation: _check_body / empty body · newline · trailing full stop
#
# ⚠️ There used to be a fourth: an anonymous-variable rejection, whose stated
# ground was that the read-back tool cannot process `_`. It is GONE, together
# with `test_an_anonymous_variable_in_a_BODY` which pinned it, because the
# ground is false — clingo derives `p(a)` from `p(X) :- q(X,_). q(a,b).`, and
# ASP2CNL renders `_` by skipping hidden terms. A body binds its own variables,
# so there is no safety ground for it either — unlike a HEAD term slot, where
# `_` is unsafe and `_check_term` still rejects it. The newly permitted case is
# pinned positively by
# `test_an_anonymous_variable_in_a_BODY_is_accepted_and_clingo_loads_it`.

def test_a_body_that_is_present_but_empty():
    """`""` is not `null`: a renderer would emit `... :- .` and clingo balks."""
    bad(module(asserts=[an_assert(body="   ")]), "present but empty")


def test_a_body_with_a_newline():
    """⚠️ NARROWED from newline-or-brace. Braces are legal ASP in a body —
    aggregates, pooling, choice bodies — and the guard rejected them on a
    justification that applies only to the read-back. The newline half stays:
    it genuinely breaks `.lp` line structure."""
    bad(module(asserts=[an_assert(body="disallowed(M),\nrestricted(M)")]),
        "newline")


def test_a_body_carrying_its_own_full_stop():
    """The renderer appends one; two produce an empty rule after it."""
    bad(module(asserts=[an_assert(body="disallowed(M).")]),
        "trailing full stop")


# ------------------------------------- Invariant 2's fourth arm: toggleable
# mutation: Licensed / "toggleable is for `world` facts only"

def test_toggleable_set_on_a_fact_that_is_not_world_licensed():
    """`toggleable` is the switch the world-knowledge ablation flips.

    A textual fact carrying it would be silently switched off with the world
    facts, dropping a clause's own content out of the run.
    """
    bad(module(ontology=[dict(atom="p(M)", gloss="a stated gloss",
                              body="disallowed(M)", licence="textual",
                              cites="m0001", inference=None, toggleable=True)],
               requires=["disallowed/1"]),
        "for `world` facts only")


# ------------------------------------------------------------ empty read-back
# mutation: ReadBack / "no read-back annotation"

def test_an_empty_read_back():
    """The read-back is what a reviewer sees INSTEAD of the formal item.

    Blank, it is not caught by the slot-count check (0 slots == 0 args), so
    nothing else in the contract notices.
    """
    bad(module(asserts=[an_assert(read_back="   ", read_back_slots=[])]),
        "no read-back annotation")


# ---------------------------------------------- OntologyFact, the two survivors
# mutation: OntologyFact / gloss has a quote or brace · BEHAVIOUR namespace

def test_an_ontology_gloss_with_a_brace_or_a_quote():
    bad(module(ontology=[dict(atom="disallowed(M)",
                              gloss='the material is {disallowed}',
                              body="restricted(M)", **ASSUMED)]),
        "ontology gloss for")


def test_the_behaviour_namespace_is_rejected_in_an_ONTOLOGY_ATOM():
    """The other half of the mandatory separation.

    `test_the_behaviour_namespace_is_rejected` claims to cover both and covers
    only the `_check_body` copy: it puts `b_asserts` in a rule BODY. An
    `OntologyFact` whose own ATOM is `seed/1` walked straight through.
    """
    bad(module(ontology=[dict(atom="seed(M)", gloss="the behaviour's seed act",
                              body="restricted(M)", **ASSUMED),
                         dict(atom="disallowed(M)",
                              gloss="the material is disallowed",
                              body="restricted(M)", **ASSUMED)]),
        "is in the behaviour namespace")


# ------------------------------------------------- Concept, the four survivors
# mutation: Concept / name is not a predicate name · redeclares a reserved name
#           · gloss has a quote or brace · negative arity

def test_a_concept_name_that_is_not_a_predicate_name():
    """`Restricted/1` is a VARIABLE to clingo, not a predicate."""
    bad(module(concepts=[concept(name="Restricted")]),
        "is not a predicate name")


@pytest.mark.parametrize("name", ["asserts", "seed"])
def test_a_concept_may_not_redeclare_the_schema_or_the_behaviour_namespace(name):
    """Redeclaring `asserts` gives the relation schema a second, private meaning.

    `seed` is the behaviour namespace: stage 1 is denied any behaviour, and the
    declaration form is the one door into it left unguarded.
    """
    bad(module(concepts=[concept(name=name)]), "may not be redeclared")


def test_a_concept_gloss_with_a_brace_or_a_quote():
    bad(module(concepts=[concept(gloss='the entity the user "interacts" with')]),
        "gloss contains a quote")


def test_a_concept_with_negative_arity():
    bad(module(concepts=[concept(arity=-1)]), "negative arity")


# ------------------------------------------------------- Superiority slot shape
# mutation: Superiority / "is not a clause id or a"
#
# No `known_clause_ids` is passed on purpose: with the corpus supplied, the
# `validate()` check below would raise for a DIFFERENT reason and this test
# would pass with the shape guard deleted.

def test_a_beats_slot_that_is_not_a_clause_id():
    bad(module(beats=[beat(winner="not a clause id")]), "is not a clause id")


# ---------------------------------------------------------------- ForbidBody
# mutation: ForbidBody / "is not a bare predicate name"
#
# The whole class was unpinned: no test constructed a `forbid_body` entry at
# all, valid or invalid.

@pytest.mark.parametrize("slot", ["head", "banned"])
def test_a_forbid_body_slot_that_is_not_a_bare_predicate_name(slot):
    entry = dict(head="permit", banned="asserts")
    entry[slot] = "permit(X)"          # a term, not a bare name
    bad(module(forbid_body=[entry]), "is not a bare predicate name")


def test_a_well_formed_forbid_body_is_ACCEPTED():
    """The guard must not reject the shape the contract is asking for."""
    m = schema.validate(
        module(forbid_body=[dict(head="permit", banned="asserts")]),
        clause_id="m0001", known_clause_ids=IDS)
    assert m.forbid_body[0].head == "permit"


# --------------------------------------------------- Module._coherent, four more
# mutation: Module / translated with no claims · acts entry is not an act term
#           · assertion names an undeclared act · two closures for one act class

def test_translated_with_no_claims():
    """Four claims tested against one case is failure mode 12.

    `claims` is the only thing that makes the count visible, so an empty list
    is the failure mode with its detector removed.
    """
    bad(module(claims=[]), "no `claims`")


def test_an_acts_entry_that_is_not_an_act_term():
    """The second entry shares `produce`'s act class, so the FORCED-closure
    check still passes once this guard is deleted — the mutated run reaches a
    clean accept and this test fails for its own reason, not another's."""
    # ⚠️ Fragment is "acts entry", not "is not a term": acts now route through
    # the shared `_check_term`, whose message is used by five slots. "acts
    # entry" is the part unique to this one, and matching the shared half would
    # let another slot's guard satisfy this test.
    bad(module(acts=["produce(M)", "produce(M) and anything else"]),
        "acts entry")


def test_an_assertion_naming_an_act_that_was_never_declared():
    """Every act is declared once so the closure declaration has a referent."""
    bad(module(asserts=[an_assert(act="interject(U)", body="disallowed(U)")]),
        "which is not in `acts`")


def test_two_closure_declarations_for_one_act_class():
    """`cepa` and `cnpa` for the same act class is not a commitment.

    The last one silently wins in any consumer that builds a dict, and the
    probe's whole finding is that the verdict turns on this bit.
    """
    bad(module(closure=[dict(act_class="produce", closure="cepa", reason="r"),
                        dict(act_class="produce", closure="cnpa", reason="r")]),
        "two closure declarations")


# ------------------------------------------- validate(): the `beats` corpus loop
# mutation: validate / "beats {slot} {val!r} is not a clause"
#
# The `cites` loop directly above it is pinned by `test_a_fabricated_citation`;
# this one was not. The fragment must include "no body binds it" — the `cites`
# message ends "…is not a clause in this corpus" too, so the short phrase would
# match the wrong guard.

@pytest.mark.parametrize("slot", ["sayer", "winner", "loser"])
def test_a_beats_slot_naming_a_clause_outside_the_corpus(slot):
    b = beat()
    b[slot] = "m9999"
    # `_coherent` requires the sayer to be this module's OWN clause, so the
    # only way to reach validate()'s check on that slot is to rename both —
    # otherwise "is not this clause" fires first and this test would pass with
    # the corpus check deleted.
    obj = module(beats=[b], clause_id="m9999" if slot == "sayer" else "m0001")
    bad(obj, "no body binds it as a variable", ids=IDS)


def test_a_quantified_beats_needs_no_corpus_membership():
    """A body binds the slots as variables; that is m0255's own case."""
    schema.validate(fixtures.module_with_quantified_beat(),
                    clause_id="m0001", known_clause_ids=IDS)


# ------------------------------------------------------- the wire flattener
# mutation: json_schema / "recursive $ref to"
#
# ⚠️ JUDGEMENT CALL, recorded rather than hidden. `Module` is not recursive, so
# this guard cannot fire on today's model. It is not dead code: `json_schema()`
# is a general flattener whose documented contract is that a recursive `$ref`
# is a LOUD refusal rather than a hang, and the day a nested model gains a
# self-reference is exactly the day nobody will be watching. The test supplies
# the flattener a recursive raw schema instead of inventing a recursive field
# on `Module` — with the guard deleted it does not fail an assertion, it
# recurses until Python stops it.

def test_a_recursive_ref_is_refused_rather_than_inlined_forever(monkeypatch):
    def recursive_raw():
        node = {"type": "object",
                "properties": {"child": {"$ref": "#/$defs/Node"}}}
        return {"type": "object",
                "properties": {"root": {"$ref": "#/$defs/Node"}},
                "$defs": {"Node": json.loads(json.dumps(node))}}

    monkeypatch.setattr(schema.Module, "model_json_schema",
                        lambda *a, **k: recursive_raw())
    with pytest.raises(ValueError) as exc:
        schema.json_schema()
    assert "recursive $ref" in str(exc.value)


# ==========================================================================
#  Three contract fixes, from the live runs. Tests written FIRST.
# ==========================================================================

def test_an_empty_paren_act_is_normalised_to_a_bare_functor():
    """`foo()` and `foo` are ONE atom to clingo and TWO strings to us.

    Measured: clingo reads `asserts(m1, oblige, follow_remaining_instructions())`
    back as `asserts(m1,oblige,follow_remaining_instructions)` — it drops the
    empty parens. The model wrote `follow_remaining_instructions()` and
    `refuse_comply()` in the second live run. Left alone, one concept becomes
    two everywhere we compare act terms as strings: that is problem #8 inside
    the act namespace, self-inflicted, and silent.
    """
    m = schema.validate(
        module(acts=["say_cannot_answer()"],
               asserts=[dict(status="oblige", act="say_cannot_answer()",
                             body=None, read_back="the assistant says so",
                             read_back_slots=[], licence="textual",
                             cites="m0001", inference=None, toggleable=False)],
               closure=[dict(act_class="say_cannot_answer", closure="cnpa",
                             reason="the clause is silent on volunteering it")],
               ontology=[], requires=[]),
        clause_id="m0001", known_clause_ids=IDS)
    assert m.acts == ["say_cannot_answer"], m.acts
    assert m.asserts[0].act == "say_cannot_answer"
    lp = schema.render_lp(m, {"section_id": "s", "kind": "c", "quote": "x"})
    assert "say_cannot_answer()" not in lp


def test_an_aggregate_in_a_body_is_ACCEPTED():
    """Braces are legal ASP and the ban on them was over-broad.

    ⓘ Verified: clingo accepts `p(X) :- n(X), #count{ Y : n(Y) } > 0.` The
    stated reason for the ban — that braces break the `%!trace_rule {"..."}`
    annotation — applies to the READ-BACK, which is interpolated into that
    line. A rule BODY is emitted as `head :- <body>.` where braces are fine.

    This is the third over-broad guard found today by live data. The other two
    were removed for the same reason: a guard that rejects correct input is
    worse than no guard, because it teaches the writer to avoid correct forms.
    """
    schema.validate(
        module(asserts=[dict(
            status="forbid", act="produce(M)",
            body="disallowed(M), #count{ P : policy(P) } > 0",
            read_back="producing % is forbidden", read_back_slots=["M"],
            licence="textual", cites="m0001", inference=None,
            toggleable=False)],
            requires=["restricted/1", "policy/1"]),
        clause_id="m0001", known_clause_ids=IDS)


def test_a_newline_in_a_body_is_still_REJECTED():
    """The newline half of that guard IS load-bearing: it breaks .lp lines."""
    bad(module(asserts=[dict(status="forbid", act="produce(M)",
                             body="disallowed(M),\nrestricted(M)",
                             read_back="producing % is forbidden",
                             read_back_slots=["M"], licence="textual",
                             cites="m0001", inference=None,
                             toggleable=False)]),
        "newline")


def test_read_back_slots_is_named_for_what_it_holds():
    """`read_back_slots` was read as 'the arguments of this rule', 6 times of 6.

    Measured across both live clauses: the value returned was ALWAYS exactly
    the set of variables in the ACT term, whether or not the sentence had any
    `%` at all. That is a coherent reading of the field NAME — so the fix is
    the name and its description, not relaxing the count check.

        act=ignore(I)                    -> args=['I']  slots=0   (wrong)
        act=follow_remaining_instructions() -> args=[]  slots=0   (right)
        act=produce(M)                   -> args=['M']  slots=1   (right)
    """
    m = schema.validate(module(), clause_id="m0001", known_clause_ids=IDS)
    assert hasattr(m.asserts[0], "read_back_slots")
    assert not hasattr(m.asserts[0], "read_back_args")
    desc = schema.Assertion.model_fields["read_back_slots"].description
    assert "%" in desc and "empty" in desc.lower()


# ==========================================================================
#  `validate_all` — the COLLECTING path.
#
#  `validate()` stops at the first breach. That is not a cosmetic difference:
#  a module with three read-back breaches and a fabricated citation costs four
#  paid repair round-trips at one-breach-per-call, and one at all-of-them.
#
#  ⚠️ Every test below asserts the SPECIFIC message fragment at the SPECIFIC
#  `where`, never a count alone. `module()` is minimal, so a fixture that trips
#  a different guard first would otherwise look pinned and would not be.
#  Every test has a negative control — the same shape, clean, must be silent.
# ==========================================================================


def where_of(breaches, fragment):
    """The `where` of the single breach mentioning `fragment`. Fails loudly."""
    hits = [b for b in breaches if fragment.lower() in b.message.lower()]
    assert len(hits) == 1, (
        f"expected exactly one breach mentioning {fragment!r}, got "
        f"{[(b.where, b.message[:70]) for b in breaches]}")
    return hits[0].where


def test_validate_all_reports_a_breach_in_EACH_of_three_sub_models():
    """Three different sub-model types, three breaches, one call.

    Under `validate()` this object costs three round-trips: pydantic reports
    everything it collects, but `validate()` re-raises only a joined string
    through one exception and the caller gets no structure to key off.
    """
    obj = module(
        ontology=[dict(atom="disallowed(M)", gloss="   ", body="restricted(M)",
                       licence="assumed", cites=None, inference="named step",
                       toggleable=False)],
        asserts=[dict(status="forbid", act="produce(M)", body="disallowed(M)",
                      read_back="   ", read_back_slots=[], licence="textual",
                      cites="m0001", inference=None, toggleable=False)],
        concepts=[concept(arity=-1)])
    mod, breaches = schema.validate_all(obj, clause_id="m0001",
                                        known_clause_ids=IDS)
    assert mod is None, "the object cannot be constructed, so there is no module"
    assert where_of(breaches, "has no gloss") == "ontology[0]"
    assert where_of(breaches, "no read-back annotation") == "asserts[0]"
    assert where_of(breaches, "negative arity") == "concepts[0]"
    assert len(breaches) == 3, [(b.where, b.message[:60]) for b in breaches]


def test_validate_all_is_SILENT_on_the_same_module_made_clean():
    """The negative control for the test above.

    A collector that reported breaches on a valid module would make every
    repair loop run forever, and the count assertions above would pass for a
    reason that has nothing to do with the fixture.
    """
    mod, breaches = schema.validate_all(module(), clause_id="m0001",
                                        known_clause_ids=IDS)
    assert breaches == []
    assert mod is not None and mod.outcome == "translated"


def test_validate_all_collects_EVERY_corpus_breach_not_just_the_first():
    """The `known_clause_ids` loop in `validate()` raises on the first hit.

    Two fabricated citations and a `beats` slot outside the corpus are three
    independent defects in one artifact; serialising them is three paid calls.
    """
    obj = module(
        asserts=[dict(status="forbid", act="produce(M)", body="disallowed(M)",
                      read_back="producing % is forbidden",
                      read_back_slots=["M"], licence="textual", cites="m9998",
                      inference=None, toggleable=False)],
        ontology=[dict(atom="disallowed(M)", gloss="the material is disallowed",
                       body="restricted(M)", licence="textual", cites="m9997",
                       inference=None, toggleable=False)],
        beats=[beat(loser="m9996")])
    mod, breaches = schema.validate_all(obj, clause_id="m0001",
                                        known_clause_ids=IDS)
    assert where_of(breaches, "m9998") == "asserts[0]"
    assert where_of(breaches, "m9997") == "ontology[0]"
    assert where_of(breaches, "m9996") == "beats[0]"
    assert all("not a clause" in b.message for b in breaches), breaches
    assert len(breaches) == 3, [(b.where, b.message[:60]) for b in breaches]
    # ⭐ The module is STILL RETURNED: it constructed, it is merely mis-cited.
    # A caller that has to render the `.lp` to run the link checks needs it,
    # and dropping it here would serialise stage 2 behind stage 1 again.
    assert mod is not None and mod.clause_id == "m0001"


def test_validate_all_is_SILENT_when_every_citation_resolves():
    """The control that must kill the test above."""
    mod, breaches = schema.validate_all(
        fixtures.module_with_beat(), clause_id="m0001", known_clause_ids=IDS)
    assert breaches == [] and mod is not None


def test_validate_all_reports_the_identity_breach_ALONGSIDE_the_citations():
    """A renamed module and a fabricated citation are one round-trip, not two.

    `where` is `<root>` for the identity breach: it is a property of the whole
    artifact, not of any one item, and a repair prompt keyed on `asserts[0]`
    would point the model at the wrong place.
    """
    obj = module(clause_id="m0002",
                 asserts=[dict(status="forbid", act="produce(M)",
                               body="disallowed(M)", read_back="r",
                               read_back_slots=[], licence="textual",
                               cites="m9999", inference=None,
                               toggleable=False)])
    mod, breaches = schema.validate_all(obj, clause_id="m0001",
                                        known_clause_ids=IDS)
    assert where_of(breaches, "two identities") == "<root>"
    assert where_of(breaches, "m9999") == "asserts[0]"
    assert len(breaches) == 2, [(b.where, b.message[:60]) for b in breaches]


def test_validate_all_leaves_the_corpus_checks_OFF_when_no_corpus_is_given():
    """The control for the identity/citation pair: skipping is the caller's
    choice, exactly as in `validate()`. If these fired unconditionally the two
    tests above would pass with the `known_clause_ids is not None` gate gone."""
    mod, breaches = schema.validate_all(
        module(asserts=[dict(status="forbid", act="produce(M)",
                             body="disallowed(M)", read_back="r",
                             read_back_slots=[], licence="textual",
                             cites="m9999", inference=None,
                             toggleable=False)]))
    assert breaches == [] and mod is not None


def test_validate_all_reports_the_ROOT_coherence_breach_with_root_as_its_where():
    """`Module._coherent`'s breaches are about the module, not about an item."""
    mod, breaches = schema.validate_all(module(requires=[]), clause_id="m0001",
                                        known_clause_ids=IDS)
    assert mod is None
    assert where_of(breaches, "nothing declares it") == "<root>"


def test_validate_all_reports_a_TYPE_breach_at_the_field_that_carries_it():
    """A wrong type is a breach like any other and must not crash the collector.

    Repair sees `asserts[0].status` rather than a traceback, which is the
    difference between a repairable finding and a dead run.
    """
    obj = module(asserts=[dict(status="banish", act="produce(M)",
                               body="disallowed(M)", read_back="r",
                               read_back_slots=[], licence="textual",
                               cites="m0001", inference=None,
                               toggleable=False)])
    mod, breaches = schema.validate_all(obj)
    assert mod is None
    assert any(b.where == "asserts[0].status" for b in breaches), breaches


@pytest.mark.parametrize("obj,fragment", [
    (module(requires=["restricted"]), "name/arity"),
    (module(requires=["restricted/1"], inputs=["restricted/1"]), "both"),
    (module(closure=[]), "closure"),
    (module(claims=[]), "no `claims`"),
    (module(ontology=[dict(atom="restricted(_)", gloss="a gloss", body=None,
                           **LIC)]), "anonymous variable"),
    (module(concepts=[concept(name="asserts")]), "may not be redeclared"),
    (module(beats=[beat(loser="m0002")]), "beat itself"),
])
def test_validate_all_and_validate_agree_on_what_is_a_breach(obj, fragment):
    """⭐ The anti-drift pin.

    `validate_all` re-implements `validate()`'s post-construction corpus and
    identity checks (it cannot share them: `validate()` raises, and every one
    of its raises is a mutation anchor in `mutate_schema.py`, so refactoring
    the message out of the raise would break the coupling loudly). Two copies
    of a rule drift. This asserts that anything `validate()` rejects for a
    named reason, `validate_all` reports for the same named reason.
    """
    with pytest.raises(schema.ModuleValidationError) as exc:
        schema.validate(obj, clause_id="m0001", known_clause_ids=IDS)
    assert fragment.lower() in str(exc.value).lower()
    _mod, breaches = schema.validate_all(obj, clause_id="m0001",
                                         known_clause_ids=IDS)
    assert any(fragment.lower() in b.message.lower() for b in breaches), (
        f"validate() rejected for {fragment!r}; validate_all reported "
        f"{[b.message[:70] for b in breaches]}")


def test_validate_itself_is_UNCHANGED_and_still_raises_on_the_first_breach():
    """`validate()` keeps its contract: a lot depends on it, including every
    mutation anchor. The collecting path is added ALONGSIDE, never in place."""
    obj = module(asserts=[dict(status="forbid", act="produce(M)",
                               body="disallowed(M)", read_back="   ",
                               read_back_slots=[], licence="textual",
                               cites="m0001", inference=None,
                               toggleable=False)],
                 concepts=[concept(arity=-1)])
    with pytest.raises(schema.ModuleValidationError):
        schema.validate(obj, clause_id="m0001", known_clause_ids=IDS)


def test_a_breach_carries_where_and_message_and_no_suggested_fix():
    """The same denial `link.Finding` is under: a stage-2 finding says WHAT and
    WHERE. A `fix` or `expected` field would put the answer into the prompt
    that is supposed to produce it."""
    import dataclasses
    fields = set(f.name for f in dataclasses.fields(schema.Breach))
    assert fields == {"where", "message"}, fields


def test_a_breach_message_is_the_GUARDS_own_sentence_not_pydantics_wrapper():
    """pydantic prefixes every `ValueError` from a validator with `Value error, `.

    Found by deleting the strip and watching nothing go red. The message is
    rendered verbatim into a repair prompt, so the wrapper is noise the model
    has to read past on every finding of every attempt — and `Value error` is
    the one phrase in the log that names no guard.

    The control is the second half: a TYPE breach is pydantic's OWN sentence,
    not a guard's, and must come through untouched rather than be trimmed by a
    prefix rule that happens to match.
    """
    _mod, breaches = schema.validate_all(module(concepts=[concept(arity=-1)]))
    hits = [b for b in breaches if "negative arity" in b.message]
    assert len(hits) == 1 and hits[0].message.startswith("concept "), hits
    assert "value error" not in hits[0].message.lower()

    _mod, breaches = schema.validate_all(module(asserts=[dict(
        status="banish", act="produce(M)", body="disallowed(M)", read_back="r",
        read_back_slots=[], licence="textual", cites="m0001", inference=None,
        toggleable=False)]))
    typed = [b for b in breaches if b.where == "asserts[0].status"]
    assert len(typed) == 1 and typed[0].message.startswith("Input should be"), \
        typed


def test_a_CONCEPT_declaration_alone_does_not_satisfy_a_body_reference():
    """Three declaration sites, not four: ontology, requires, inputs.

    A concept says what a predicate MEANS. It does not say that anything
    DEFINES it — no fact, no rule, no other clause. A rule whose body rests
    only on concept declarations can never fire, and it passed with zero
    errors: measured on a real module whose single rule depended on three
    such predicates with `requires` and `inputs` both empty.

    That is the `requires`-to-`inputs` dodge one field over, and it is worse,
    because a concept costs nothing to declare.
    """
    bad(module(concepts=[concept(name="restricted", arity=1,
                                 gloss="falls under the restricted policy")],
               requires=[], inputs=[]),
        "nothing declares it")


def test_a_concept_that_is_ALSO_declared_properly_is_accepted():
    """The negative control: concepts are not banned from bodies, they are
    just not a substitute for saying who defines the predicate."""
    schema.validate(
        module(concepts=[concept(name="restricted", arity=1,
                                 gloss="falls under the restricted policy")],
               requires=["restricted/1"]),
        clause_id="m0001", known_clause_ids=IDS)
