"""Tests for `link.py` against the stage-1 contract that landed 2026-08-07.

Run:  semi-formal-experiment/.venv/bin/python -m pytest walkthrough/test_link.py -q

⭐ WHY THESE FIXTURES ARE RENDERED, NOT HAND-WRITTEN.  Every `.lp` under test is
built by putting a dict through `phase_1/schema.py`'s `validate()` and rendering
it with `render_lp()`. A hand-written fixture drifts from what stage 1 actually
emits, and then the test pins a shape nothing produces. Where a fixture CANNOT
be schema-rendered (the schema forbids the very defect under test), the test
says so in a comment and says what still produces that shape.

⚠️ Every test asserts on the FINDING — its check id and its message — never on
the exit code alone. An exit code collapses distinct defects into one integer.
"""

import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PHASE1 = os.path.join(HERE, "paper_pipeline", "phase_1")
PY = os.path.join(REPO, "semi-formal-experiment", ".venv", "bin", "python")

sys.path.insert(0, HERE)
sys.path.insert(0, PHASE1)

import fixtures                   # noqa: E402  ⭐ the shared stage-1 fixtures
import link                       # noqa: E402  the module under test
import schema                     # noqa: E402  the stage-1 contract (read-only)


# ==========================================================================
#  Fixture construction: real modules, through the real contract
# ==========================================================================
#
# ⭐ ONE definition of the contract, in `paper_pipeline/phase_1/fixtures.py`,
# shared with `test_schema.py`, `test_checks.py` and `test_repair.py`. This
# file's private copy is what disagreed silently: `political()` declared its
# predicates ONLY as concepts, a module whose single rule could never fire, and
# nothing compared it against the other three builders. The correction now
# lives with the fixture, and `test_schema` validates every variant.

def T(cite="m0255"):
    """A `textual` licence, defaulting to m0255 — this file's own clause."""
    return fixtures.textual(cite)


module_dict = fixtures.m0255_module


def render(tmp_path, name, **over):
    """Validate a module through the contract and render it to a real `.lp`."""
    d = module_dict(**over)
    mod = schema.validate(d)
    clause = dict(section_id="transformation_exception", kind="conditional",
                  quote="The transformation exception does not override any "
                        "policies other than those on restricted content.")
    p = tmp_path / name
    p.write_text(schema.render_lp(mod, clause), encoding="utf-8")
    return str(p)


def write_raw(tmp_path, name, text):
    """A hand-written `.lp`. Used ONLY where the schema forbids the defect
    under test, and each use says what really produces that shape."""
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def ids(findings):
    return [f.check_id for f in findings]


def by_id(findings, check_id):
    return [f for f in findings if f.check_id == check_id]


# ==========================================================================
#  DEFECT 7 — collect() / report() split
# ==========================================================================

def test_d7_collect_returns_structured_findings(tmp_path):
    """`collect(paths)` must return Finding records, not print."""
    p = render(tmp_path, "ok.lp")
    findings = link.collect([p])
    assert isinstance(findings, list)
    for f in findings:
        assert isinstance(f.check_id, str) and f.check_id
        assert f.severity in ("error", "note")
        assert isinstance(f.where, str)
        assert isinstance(f.message, str) and f.message


def test_d7_finding_carries_no_suggested_fix(tmp_path):
    """⛔ A Finding must NOT carry a suggested fix or an expected value.

    These findings feed a repair prompt, and stage 1 is denied the expected
    verdicts. A `fix=` or `expected=` field leaks the answer into the prompt
    that is supposed to produce it.
    """
    banned = {"fix", "suggested_fix", "suggestion", "expected", "expected_value",
              "correct", "answer", "repair"}
    fields = set(getattr(link.Finding, "__dataclass_fields__", {}))
    assert fields, "Finding must be a dataclass with declared fields"
    assert not (fields & banned), f"Finding leaks the answer via {fields & banned}"


def test_d7_report_prints_and_returns_exit_code(tmp_path, capsys):
    """`report(findings)` is the only thing that prints; it returns the code."""
    p = render(tmp_path, "ok.lp")
    findings = link.collect([p])
    rc = link.report(findings)
    out = capsys.readouterr().out
    assert "linked" in out
    assert rc == (1 if any(f.severity == "error" for f in findings) else 0)


# ==========================================================================
#  DEFECT 1 — `%% requires:` is invisible
# ==========================================================================

def test_d1_requires_is_not_reported_as_unresolved(tmp_path):
    """A `requires` predicate is head-less BY DESIGN at single-module scope.

    Reporting it as an UNRESOLVED REFERENCE destroys the three-way diagnosis in
    03_pipeline.md Part 4 §2 (linkage / not yet translated / genuinely dead).
    """
    p = render(
        tmp_path, "needs.lp",
        concepts=[dict(**T(), name="asserts_policy", arity=2,
                       gloss="clause R asserts the policy named P")],
        asserts=[dict(**T(), status="forbid", act="produce(M)",
                      body="new_material(M), policy_class(P, K)",
                      read_back="producing % is still forbidden",
                      read_back_slots=["M"])],
        requires=["policy_class/2"],
        inputs=["new_material/1"],
    )
    findings = link.collect([p])
    unresolved = [f for f in by_id(findings, "unresolved-reference")
                  if "policy_class/2" in f.message]
    assert not unresolved, (
        "a declared `requires` entry was reported as an unresolved reference: "
        + "; ".join(f.message for f in unresolved))


def test_d1_unprovided_requires_is_its_own_non_error_status(tmp_path):
    """It must still be VISIBLE — as a distinct, non-error status."""
    p = render(
        tmp_path, "needs.lp",
        asserts=[dict(**T(), status="forbid", act="produce(M)",
                      body="new_material(M), policy_class(P, K)",
                      read_back="producing % is still forbidden",
                      read_back_slots=["M"])],
        requires=["policy_class/2"],
        inputs=["new_material/1"],
    )
    findings = link.collect([p])
    hits = by_id(findings, "requires-unprovided")
    assert len(hits) == 1, f"expected one requires-unprovided, got {ids(findings)}"
    assert hits[0].severity == "note", "a declared requires is NOT an error"
    assert "policy_class/2" in hits[0].message


def test_d1_provided_requires_is_silent(tmp_path):
    """Once the providing clause is linked in, the status must clear.

    The control for the test above: if `requires-unprovided` fired regardless
    of the link set it would be pinning nothing.
    """
    consumer = render(
        tmp_path, "consumer.lp",
        asserts=[dict(**T(), status="forbid", act="produce(M)",
                      body="new_material(M), policy_class(P, K)",
                      read_back="producing % is still forbidden",
                      read_back_slots=["M"])],
        requires=["policy_class/2"],
        inputs=["new_material/1"],
    )
    provider = render(
        tmp_path, "provider.lp",
        clause_id="m0200",
        concepts=[dict(**T("m0200"), name="policy_class", arity=2,
                       gloss="policy P is of kind K")],
        ontology=[dict(**T("m0200"), atom="policy_class(restricted_content, restricted)",
                       gloss="policy P is of kind K", body=None)],
        asserts=[], acts=[], closure=[], inputs=[],
        claims=["C1 restricted content is a policy class"],
    )
    findings = link.collect([consumer, provider])
    assert not by_id(findings, "requires-unprovided"), (
        "policy_class/2 IS provided by the linked module; the status must clear")


# ==========================================================================
#  DEFECT 2 — the rule-shape check went silently vacuous
# ==========================================================================

def test_d2_forbid_body_fires_on_a_status_head(tmp_path):
    """⛔ THE IMPORTANT ONE.

    `%% forbid-body: permit <- purpose` means: no rule deriving `permit` may
    depend on `purpose`. Under the fixed vocabulary `permit` is never a rule
    HEAD — it is the second argument of `asserts/3`. The old check compared it
    against the head predicate name, which is always asserts/beats/defines, so
    it could never match and reported ZERO violations on a plain violation.
    """
    p = render(
        tmp_path, "violator.lp",
        asserts=[dict(**T(), status="permit", act="produce(M)",
                      body="new_material(M), purpose(M, research)",
                      read_back="producing % is permitted",
                      read_back_slots=["M"])],
        inputs=["new_material/1", "purpose/2"],
        forbid_body=[dict(head="permit", banned="purpose")],
    )
    findings = link.collect([p])
    hits = by_id(findings, "rule-shape")
    assert len(hits) == 1, (
        f"a rule deriving `permit` from `purpose` produced no rule-shape "
        f"finding; got {ids(findings)}")
    assert hits[0].severity == "error"
    assert "permit" in hits[0].message and "purpose" in hits[0].message


def test_d2_forbid_body_silent_on_a_clean_module(tmp_path):
    """The guard that must kill the test above.

    Same declaration, same status, NO `purpose` in the body. If deleting the
    rule-shape check leaves both tests green, the check is pinning nothing —
    this one is what makes the previous one specific rather than a constant.
    """
    p = render(
        tmp_path, "clean.lp",
        asserts=[dict(**T(), status="permit", act="produce(M)",
                      body="new_material(M), disallowed(M)",
                      read_back="producing % is permitted",
                      read_back_slots=["M"])],
        forbid_body=[dict(head="permit", banned="purpose")],
    )
    assert not by_id(link.collect([p]), "rule-shape")


def test_d2_forbid_body_fires_on_a_relation_head(tmp_path):
    """`X` may also be a RELATION name, not only a status — `beats <- purpose`.

    The hand-written m0255.lp uses the relation form (`lifted <- purpose`), so
    both readings have to work off one declaration.
    """
    p = render(
        tmp_path, "relation.lp",
        concepts=[dict(**T(), name="purpose", arity=2,
                       gloss="the stated purpose of request M is P")],
        beats=[dict(**T(), sayer="m0255", winner="m0203", loser="m0252",
                    body="purpose(M, research)",
                    read_back="the content policy beats the exception",
                    read_back_slots=[])],
        forbid_body=[dict(head="beats", banned="purpose")],
        # `purpose/2` is a fact about the case being judged (the stated
        # purpose of the request), so it belongs in `inputs`; the concept
        # entry above supplies its gloss, not its declaration.
        inputs=["new_material/1", "disallowed/1", "purpose/2"],
    )
    hits = by_id(link.collect([p]), "rule-shape")
    assert len(hits) == 1, "a `beats` rule bodied on `purpose` must be caught"
    assert "beats" in hits[0].message and "purpose" in hits[0].message


def test_d2_rule_parser_sees_new_contract_rules(tmp_path):
    """The root cause, pinned directly.

    `RULE` could not match `asserts(m0255, forbid, produce(M)) :- ... .   % [T]`
    at all: `[^)]*` stops at the first `)` inside the compound act, and the
    trailing licence comment defeats the `\\.\\s*$` anchor. Head extraction
    returned the empty list, so EVERY head-shaped check downstream was vacuous.
    """
    txt = ("asserts(m0255, forbid, produce(M)) :- new_material(M).   % [T] m0255\n"
           "beats(m0255, R, m0252) :- content_policy_rule(R).   % [T] m0255\n"
           "defines(m0255, prohibited, csam).   % [T] m0255\n")
    heads = {h for h, _args, _body in link.rules(txt)}
    assert heads == {"asserts", "beats"}, f"parser saw {heads}"
    assert "defines/3" in link.defined_predicates(txt)
    assert "asserts/3" in link.defined_predicates(txt)


# ==========================================================================
#  DEFECT 3 — the `provides` path is dead code
# ==========================================================================

def test_d3_no_provides_machinery_on_a_new_contract_module(tmp_path, capsys):
    """`Module` has no `provides` field and `render_lp` emits no such header.

    Nothing stage 1 produces can carry one, so the check could not fire on real
    input — and it printed a `no %% provides: header` warning on EVERY module.
    """
    p = render(tmp_path, "ok.lp")
    findings = link.collect([p])
    assert not [f for f in findings if "provides" in f.check_id]
    link.report(findings)
    assert "provides" not in capsys.readouterr().out


# ==========================================================================
#  DEFECT 4 — clingo's refusal was ignored
# ==========================================================================

def test_d4_a_file_clingo_refuses_is_a_loud_failure(tmp_path):
    """An unsafe variable makes clingo refuse the WHOLE file. link() printed
    `✅ no unresolved references` and returned 0.

    This module is schema-valid: `allow_vars` is keyed off the body being
    present, and nothing checks that the body BINDS the act's variable.
    """
    p = render(
        tmp_path, "unsafe.lp",
        asserts=[dict(**T(), status="forbid", act="produce(M)",
                      body="new_material(X)",          # X, not M -- M unsafe
                      read_back="producing % is forbidden",
                      read_back_slots=["M"])],
        inputs=["new_material/1"],
    )
    findings = link.collect([p])
    hits = by_id(findings, "clingo-error")
    assert len(hits) == 1, f"clingo refused this file; got {ids(findings)}"
    assert hits[0].severity == "error"
    assert "unsafe" in hits[0].message
    assert link.report(findings) == 1


def test_d4_clean_file_has_no_clingo_error(tmp_path):
    """The guard that must kill the test above."""
    p = render(tmp_path, "ok.lp")
    assert not by_id(link.collect([p]), "clingo-error")


# ==========================================================================
#  DEFECT 5 — closure / acts / concepts headers were unreadable
# ==========================================================================

def test_d5_headers_are_parsed(tmp_path):
    p = render(
        tmp_path, "hdr.lp",
        concepts=[dict(**T(), name="asserts_policy", arity=2,
                       gloss="clause R asserts the policy named P")],
        requires=["policy_class/2"],
    )
    h = link.header(p)
    assert h["acts"] == {"produce(M)"}
    assert h["concepts"] == {"asserts_policy/2"}
    assert h["requires"] == {"policy_class/2"}
    assert h["closure"] == {"produce": "cepa"}


def test_d5_conflicting_closure_across_a_link_set(tmp_path):
    """Two modules governing the same act class, one CEPA and one CNPA.

    The probe showed the contradiction verdict flips on the closure, so a
    disagreement is a real finding and not bookkeeping.
    """
    a = render(tmp_path, "cepa.lp")
    b = render(tmp_path, "cnpa.lp", clause_id="m0253",
               closure=[dict(act_class="produce", closure="cnpa",
                             reason="the clause reads silence as prohibition")])
    hits = by_id(link.collect([a, b]), "closure-conflict")
    assert len(hits) == 1, "cepa vs cnpa on `produce` must be reported"
    assert hits[0].severity == "error"
    assert "produce" in hits[0].message
    assert "cepa" in hits[0].message and "cnpa" in hits[0].message


def test_d5_agreeing_closure_is_silent(tmp_path):
    """The guard that must kill the test above."""
    a = render(tmp_path, "a.lp")
    b = render(tmp_path, "b.lp", clause_id="m0253")
    assert not by_id(link.collect([a, b]), "closure-conflict")


def test_d5_act_class_with_no_closure_declaration(tmp_path):
    """⚠️ NOT schema-renderable: `Module._coherent` FORCES a closure for every
    governed act class, so a generated module can never lack one. The shape
    still reaches link scope from hand-written and pre-contract modules —
    `contradiction_probe/doc.lp` governs nine act classes and declares none —
    and those are exactly the files the ruling wants covered.
    """
    p = write_raw(
        tmp_path, "handwritten.lp",
        "%% clause: m0263   section: prevent_imminent_harm   kind: conditional\n"
        "%% acts: interject(W)\n"
        "%% requires:\n"
        "%% inputs: on_camera/1\n"
        "asserts(m0263, oblige, interject(W)) :- on_camera(W).\n")
    hits = by_id(link.collect([p]), "closure-missing")
    assert len(hits) == 1, "an act class governed with no closure declaration"
    assert "interject" in hits[0].message


# ==========================================================================
#  DEFECT 6 — Problem #17, a cyclic `beats` relation
# ==========================================================================

def test_d6_two_cycle_in_beats_is_detected(tmp_path):
    """03_pipeline.md Part 1 #17: A beats B and B beats A produces a confident
    WRONG answer rather than an error. `kernel.lp` has the acyclicity guard but
    a bare module never loads it, and `schema.py` rejects only `winner == loser`.
    """
    a = render(tmp_path, "a.lp", clause_id="m0252",
               beats=[dict(**T("m0252"), sayer="m0252", winner="m0252",
                           loser="m0208", body=None,
                           read_back="the exception beats the restriction",
                           read_back_slots=[])])
    b = render(tmp_path, "b.lp", clause_id="m0208",
               beats=[dict(**T("m0208"), sayer="m0208", winner="m0208",
                           loser="m0252", body=None,
                           read_back="the restriction beats the exception",
                           read_back_slots=[])])
    hits = by_id(link.collect([a, b]), "beats-cycle")
    assert len(hits) == 1, "m0252 -> m0208 -> m0252 is a cycle"
    assert hits[0].severity == "error"
    assert "m0252" in hits[0].message and "m0208" in hits[0].message


def test_d6_acyclic_beats_is_silent(tmp_path):
    """The guard that must kill the test above: same two modules, one edge
    reversed so the relation is a chain. If deleting the cycle check leaves
    both green, the check is pinning nothing."""
    a = render(tmp_path, "a.lp", clause_id="m0252",
               beats=[dict(**T("m0252"), sayer="m0252", winner="m0252",
                           loser="m0208", body=None,
                           read_back="the exception beats the restriction",
                           read_back_slots=[])])
    b = render(tmp_path, "b.lp", clause_id="m0203",
               beats=[dict(**T("m0203"), sayer="m0203", winner="m0203",
                           loser="m0252", body=None,
                           read_back="the prohibition beats the exception",
                           read_back_slots=[])])
    assert not by_id(link.collect([a, b]), "beats-cycle")


def test_d6_longer_cycle_is_detected(tmp_path):
    """Three-clause cycle: transitivity, not just a mutual pair."""
    files = []
    for cid, loser in (("m0252", "m0208"), ("m0208", "m0203"), ("m0203", "m0252")):
        files.append(render(
            tmp_path, f"{cid}.lp", clause_id=cid,
            beats=[dict(**T(cid), sayer=cid, winner=cid, loser=loser, body=None,
                        read_back="one clause beats another",
                        read_back_slots=[])]))
    hits = by_id(link.collect(files), "beats-cycle")
    assert hits, "m0252 -> m0208 -> m0203 -> m0252 is a cycle"


# ==========================================================================
#  D4b-3 — the CONCEPT TABLE is data, and `collect()` reads it
# ==========================================================================
#
# ⭐ The `.lp` carries concepts only as a POINTER header
# (`%% concepts: political_content/1, ...   (glosses in the concept table,
# not here)`). The dictionary itself is `concepts.json`, written per run by
# `translate.py` (`schema.concept_rows`). link.py must take that table AS DATA
# — `collect(paths, concepts=rows)` — and let a row declare its predicate,
# exactly as `%% inputs:` and `%% requires:` do.
#
# ⛔ THE FIX THIS FORBIDS: parsing the `%% concepts:` header. That re-creates
# the regex-the-comments pattern the split exists to avoid (05_practice §2.3),
# and throws away the gloss, the licence and the citation. The mix test below
# is what catches it: the module's HEADER declares two concepts, the TABLE
# declares one, and the one the table does not carry must STILL be reported.

CONC_POL = fixtures.CONC_POL
CONC_AUD = fixtures.CONC_AUD

#: The m0217 shape. ⚠️ The fixture that was silently WRONG — see
#: `fixtures.political_module`, which carries the correction and its reason.
#: It returns a whole module, so `render(..., **political())` and
#: `table_of(political())` both still take it as an override set.
political = fixtures.political_module


def table_of(*overrides):
    """The concept table, built the way `translate.py` builds it: validate the
    module through the contract and take `schema.concept_rows`. Hand-writing
    the rows would let the fixture drift from what a run actually writes."""
    rows = []
    for over in overrides:
        rows.extend(schema.concept_rows(schema.validate(module_dict(**over))))
    return rows


def messages(findings, check_id):
    return " | ".join(f.message for f in by_id(findings, check_id))


def test_d4b_table_row_declares_the_predicate(tmp_path):
    """⭐ THE DEFECT. Every concept in m0217 and m0037 is declared — in the
    module's `concepts` list, hence in `concepts.json` — and link.py reported
    all seven as UNRESOLVED because it never read the table."""
    p = render(tmp_path, "m0217.lp", **political())
    findings = link.collect([p], concepts=table_of(political()))
    assert not by_id(findings, "unresolved-reference"), (
        "a concept declared in the concept table was reported unresolved: "
        + messages(findings, "unresolved-reference"))


def test_d4b_table_row_is_visible_not_merely_suppressed(tmp_path):
    """A name that stops being an error must not simply vanish: `%% inputs:`
    gets a `situation-input` note, and a table row gets its own."""
    p = render(tmp_path, "m0217.lp", **political())
    hits = by_id(link.collect([p], concepts=table_of(political())),
                 "concept-declared")
    sigs = {s for f in hits for s in re.findall(r"`([a-z_]+/\d+)`", f.message)}
    assert {"political_content/1", "broad_audience/1"} <= sigs, (
        f"the table's declarations must be reported, not silently dropped; "
        f"saw {sigs}")
    assert all(f.severity == "note" for f in hits)


def test_d4b_a_concept_the_table_does_not_carry_still_fires(tmp_path):
    """⛔ THE MIX. The module's header declares BOTH concepts; the table
    carries only `political_content/1`. `broad_audience/1` must still be an
    unresolved reference.

    This kills two wrong fixes at once: suppressing the check whenever a table
    is supplied, and reading the `%% concepts:` HEADER instead of the table.

    ⚠️ NOT schema-renderable through `political()` any more: that helper now
    declares both signatures as `inputs` (schema requires a real declaration
    site for every body predicate), and an `inputs` entry alone is enough to
    keep `broad_audience/1` out of `unresolved-reference` regardless of what
    the concept table carries -- it would no longer isolate the MIX this test
    exists to catch. So `p` is hand-written here: header declares both
    concepts, `%% inputs:` carries only `political_content/1`, matching the
    shape a pre-contract or hand-edited module can still produce.
    """
    p = write_raw(
        tmp_path, "m0217.lp",
        "%% clause: m0217   section: political_content   kind: conditional\n"
        "%% acts: produce(M)\n"
        "%% concepts: political_content/1, broad_audience/1   "
        "(glosses in the concept table, not here)\n"
        "%% requires: \n"
        "%% inputs: political_content/1\n"
        "%% closure: produce = cepa   % the clause speaks only of what it "
        "permits\n"
        "asserts(m0217, permit, produce(M)) :- political_content(M), "
        "broad_audience(M).   % [T] m0217\n")
    partial = table_of(political(
        concepts=[dict(**T("m0217"), **CONC_POL)],
        asserts=[dict(**T("m0217"), status="permit", act="produce(M)",
                      body="political_content(M)",
                      read_back="producing % is permitted",
                      read_back_slots=["M"])]))
    hits = by_id(link.collect([p], concepts=partial), "unresolved-reference")
    assert len(hits) == 1, (
        f"exactly the concept the table omits must be reported; got "
        f"{[f.message for f in hits]}")
    assert "broad_audience/1" in hits[0].message
    assert "political_content/1" not in hits[0].message


def test_d4b_no_table_supplied_is_reported_not_silent(tmp_path):
    """⚠️ THE FAILURE MODE TO AVOID. Running without the table makes every
    declared concept read as undeclared, and the tool floods with false
    positives that look exactly like real findings. Proceeding silently is what
    it did today, so the absence must itself be a finding."""
    p = render(tmp_path, "m0217.lp", **political())
    findings = link.collect([p])                       # concepts=None
    hits = by_id(findings, "concept-table-absent")
    assert len(hits) == 1, (
        f"a module that declares concepts, linked with no table, must say so; "
        f"got {ids(findings)}")
    assert "m0217.lp" in hits[0].where


def test_d4b_no_table_and_no_concepts_declared_is_silent(tmp_path):
    """The guard that must kill the test above: the m0255 worked example
    declares no concepts at all, and must not acquire a new complaint.

    ⚠️ A warning that fires on every run is how the old `no %% provides:`
    message became invisible, so the CLI must not shout here either — while
    still saying where it stands on the table.
    """
    p = render(tmp_path, "plain.lp")                   # module_dict: concepts=[]
    assert not by_id(link.collect([p]), "concept-table-absent")
    r = subprocess.run([PY, "link.py", p], cwd=HERE,
                       capture_output=True, text=True)
    first = (r.stdout.splitlines() or [""])[0]
    assert "concept table" in first.lower(), r.stdout + r.stderr
    assert not re.search(r"⚠️|NO CONCEPT TABLE", first), (
        f"nothing here needs a concept table; a warning would be noise:\n{first}")


# ---- D4b-3, problem #1: referenced, but in no table ----------------------

def test_d4b_concept_declared_by_a_module_but_absent_from_the_table(tmp_path):
    """`03_pipeline.md` stage 2 D4: *every fact cites a real clause and a real
    concept*. A module pointing at a concept row that does not exist is problem
    #1 (made-up things) at the table seam — the gloss cannot be recovered."""
    p = render(tmp_path, "m0217.lp", **political())
    partial = table_of(political(
        concepts=[dict(**T("m0217"), **CONC_POL)],
        asserts=[dict(**T("m0217"), status="permit", act="produce(M)",
                      body="political_content(M)",
                      read_back="producing % is permitted",
                      read_back_slots=["M"])]))
    hits = by_id(link.collect([p], concepts=partial), "concept-not-in-table")
    assert len(hits) == 1, f"broad_audience/1 has no row in the supplied table"
    assert hits[0].severity == "error"
    assert "broad_audience/1" in hits[0].message
    assert "political_content/1" not in hits[0].message


def test_d4b_a_complete_table_raises_no_missing_row(tmp_path):
    """The guard that must kill the test above."""
    p = render(tmp_path, "m0217.lp", **political())
    assert not by_id(link.collect([p], concepts=table_of(political())),
                     "concept-not-in-table")


# ---- D4b-3, problem #9: same name, different meanings --------------------

def test_d4b_same_name_different_gloss_is_a_candidate_not_an_error(tmp_path):
    """Problem #9. ⚠️ Reported as a CANDIDATE: `03_pipeline.md` Part 1 #9
    measures 46 of 228 reused names (20%) carrying more than one definition, so
    a second gloss is the ORDINARY rate for this task, not a defect."""
    p = render(tmp_path, "a.lp")
    rows = table_of(
        dict(clause_id="m0217",
             concepts=[dict(**T("m0217"), name="user", arity=1,
                            gloss="the person interacting with the assistant")]),
        dict(clause_id="m0053",
             concepts=[dict(**T("m0053"), name="user", arity=1,
                            gloss="the party whose instructions rank below the "
                                  "developer")]))
    hits = by_id(link.collect([p], concepts=rows), "concept-multi-gloss")
    assert len(hits) == 1, "user/1 carries two different definitions"
    assert hits[0].severity == "note", (
        "20% is the measured ordinary rate; an error severity would overclaim")
    assert "user/1" in hits[0].message
    assert "m0217" in hits[0].message and "m0053" in hits[0].message


def test_d4b_same_name_same_gloss_is_silent(tmp_path):
    """The guard that must kill the test above: a concept two clauses declare
    IDENTICALLY is reuse working, which is the point of a shared vocabulary."""
    p = render(tmp_path, "a.lp")
    same = "the person interacting with the assistant"
    rows = table_of(
        dict(clause_id="m0217",
             concepts=[dict(**T("m0217"), name="user", arity=1, gloss=same)]),
        dict(clause_id="m0053",
             concepts=[dict(**T("m0053"), name="user", arity=1, gloss=same)]))
    assert not by_id(link.collect([p], concepts=rows), "concept-multi-gloss")


# ---- the CLI half: find the table, and SAY whether you found it ----------

def test_d4b_cli_loads_concepts_json_beside_the_lp_files(tmp_path):
    """`link.py <run>/*.lp` must find `concepts.json` in that directory."""
    import json
    render(tmp_path, "m0217.lp", **political())
    (tmp_path / "concepts.json").write_text(
        json.dumps(table_of(political()), indent=1), encoding="utf-8")
    r = subprocess.run([PY, "link.py", str(tmp_path / "m0217.lp")],
                       cwd=HERE, capture_output=True, text=True)
    assert re.search(r"concept table: \d+ row\(s\) from \S*concepts\.json",
                     r.stdout), (
        f"the CLI must SAY it loaded a table, and which one — a message that "
        f"merely mentions the filename also matches the 'not found' warning:"
        f"\n{r.stdout}{r.stderr}")
    assert "UNRESOLVED" not in r.stdout, r.stdout
    assert r.returncode == 0, r.stdout + r.stderr


def test_d4b_cli_says_so_loudly_when_there_is_no_table(tmp_path):
    """⚠️ Silently proceeding without a table is the failure mode. The run
    directory at the top of this brief has no `concepts.json`, and the tool
    reported seven declared concepts as unresolved without a word about it."""
    render(tmp_path, "m0217.lp", **political())
    r = subprocess.run([PY, "link.py", str(tmp_path / "m0217.lp")],
                       cwd=HERE, capture_output=True, text=True)
    # ⚠️ THE FIRST LINE, not `in r.stdout`. `collect()`'s own
    # `concept-table-absent` message also contains "no concept table", so the
    # loose assertion passed with the CLI's warning DELETED — found by the
    # mutation run, which is the only reason this is line-anchored.
    first = (r.stdout.splitlines() or [""])[0]
    assert re.search(r"no concept table", first, re.I), (
        f"the CLI itself must say the table is missing, before anything "
        f"else:\n{r.stdout}{r.stderr}")
    assert str(tmp_path) in first, "and must name where it looked"


def test_d4b_acceptance_the_live_run_directory(tmp_path):
    """⭐ THE ACCEPTANCE CASE, run against the real artifact rather than a
    fixture. Every concept the run's modules declare must resolve.

    ⚠️ Pins no COUNT of a live artifact — it reads the run's own module JSON
    for what those modules declare, so a run that legitimately grows still
    passes."""
    import glob
    import json
    runs = sorted(glob.glob(os.path.join(
        PHASE1, "runs", "20260807-143853-*")))
    if not runs:
        pytest.skip("the 20260807-143853 run directory is not present")
    run = runs[0]
    lps = sorted(glob.glob(os.path.join(run, "*.lp")))
    assert lps, f"no .lp files in {run}"
    declared = set()
    for j in sorted(glob.glob(os.path.join(run, "m*.json"))):
        for c in json.load(open(j, encoding="utf-8")).get("concepts", []):
            declared.add(f"{c['name']}/{c['arity']}")
    assert declared, "this run's modules declare concepts"
    r = subprocess.run([PY, "link.py"] + lps, cwd=HERE,
                       capture_output=True, text=True)
    leaked = [s for s in declared
              if re.search(r"`%s`[^\n]*declared neither" % re.escape(s),
                           r.stdout)]
    assert not leaked, (
        f"declared concepts still reported as unresolved: {sorted(leaked)}\n"
        f"{r.stdout}")


# ==========================================================================
#  REGRESSION — the one hand-written linked translation
# ==========================================================================

def test_regression_m0255_worked_example_stays_green():
    """`link.py m0255.lp clauses/m0200.lp clauses/m0201.lp clauses/m0203.lp`
    from `walkthrough/`. The only worked example the project has."""
    r = subprocess.run(
        [PY, "link.py", "m0255.lp", "clauses/m0200.lp",
         "clauses/m0201.lp", "clauses/m0203.lp"],
        cwd=HERE, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "no unresolved references" in r.stdout


def test_self_test_still_passes():
    r = subprocess.run([PY, "link.py", "--self-test"], cwd=HERE,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
