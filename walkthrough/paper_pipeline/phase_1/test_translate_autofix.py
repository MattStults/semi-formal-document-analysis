"""Pins for translate_autofix, anchored on MODULES THAT ACTUALLY FAILED ON DISK.

Every fixture below is a verbatim excerpt of an assistant turn from a stored
transcript in runs/ or repair_graveyard/, together with the finding that turn
actually drew from schema.py. The RED assertion in each test is the check
firing on the stored artifact; the GREEN assertion is the same check passing
after `autofix`, with the content assertions unchanged.

⚠️ NO COUNT OF A LIVE ARTIFACT IS PINNED HERE (REPO_TRAPS / AGENTS.md). The
corpus-wide numbers live in TRANSLATION_REPAIR_CENSUS.md and are recomputed,
never asserted. What is pinned is a FROZEN input and a subset property.
"""
import copy

import pytest

import schema
import translate_autofix as A


def _breaches(obj, clause_id=None, ids=None):
    _mod, br = schema.validate_all(obj, clause_id=clause_id,
                                   known_clause_ids=ids)
    return [f"{b.where}: {b.message}" for b in br]


def _has(br, needle):
    return any(needle in b for b in br)


# ---------------------------------------------------------------------------
# A minimal module that PASSES, so each test can perturb exactly one thing and
# attribute the breach to that perturbation.
# ---------------------------------------------------------------------------
CLAUSE = "l1_170_n003"
IDS = {CLAUSE}


def base():
    return {
        "outcome": "translated",
        "clause_id": CLAUSE,
        "abstain_reason": None,
        "claims": ["C1 the assistant must not produce disallowed material"],
        "acts": ["produce(M)"],
        "concepts": [
            {"name": "disallowed", "arity": 1,
             "gloss": "M is material the restricted-content policy rules out",
             "licence": "textual", "cites": CLAUSE, "inference": None,
             "toggleable": False},
            {"name": "material", "arity": 1,
             "gloss": "M is a span of content the assistant could emit in reply",
             "licence": "textual", "cites": CLAUSE, "inference": None,
             "toggleable": False},
        ],
        "ontology": [],
        "requires": [],
        "inputs": ["material/1", "disallowed/1"],
        "asserts": [
            {"status": "forbid", "act": "produce(M)",
             "body": "material(M), disallowed(M)",
             "read_back": "producing disallowed material is forbidden",
             "read_back_slots": [],
             "licence": "textual", "cites": CLAUSE, "inference": None,
             "toggleable": False},
        ],
        "beats": [],
        "defines": [],
        "forbid_body": [],
        "closure": [
            {"act_class": "produce", "closure": "cnpa",
             "reason": "the clause rules out the material rather than listing "
                       "what is allowed"},
        ],
    }


def test_base_module_is_clean():
    """The unperturbed fixture must pass, or every test below proves nothing."""
    assert _breaches(base(), CLAUSE, IDS) == []


def test_autofix_is_a_no_op_on_a_clean_module():
    obj = base()
    fixed, fixes = A.autofix(obj)
    assert fixes == []
    assert fixed == obj


def test_autofix_does_not_mutate_its_input():
    obj = base()
    obj["asserts"][0]["read_back_slots"] = ["M"]
    before = copy.deepcopy(obj)
    A.autofix(obj)
    assert obj == before


def test_autofix_is_idempotent():
    obj = base()
    obj["asserts"][0]["read_back_slots"] = ["M"]
    obj["concepts"][0]["name"] = "disallowed/1"
    once, _ = A.autofix(obj)
    twice, fixes2 = A.autofix(once)
    assert twice == once
    assert fixes2 == []


# ===========================================================================
#  readback-empty-slots
#  On disk: 61 of the 65 read_back findings are this exact shape.
#  Verbatim from runs/.../l4572_4691_n011.transcript.json, attempt 1:
# ===========================================================================
DISK_READBACK = {
    "read_back": "for U18 users, the assistant cannot engage in immersive "
                 "romantic roleplay",
    "read_back_slots": ["U"],
}


def test_disk_readback_module_fails_the_slot_check_RED():
    obj = base()
    obj["asserts"][0]["read_back"] = DISK_READBACK["read_back"]
    obj["asserts"][0]["read_back_slots"] = list(DISK_READBACK["read_back_slots"])
    br = _breaches(obj, CLAUSE, IDS)
    assert _has(br, "read_back has 0 `%` slot(s) but 1 slot entr"), br


def test_autofix_clears_it_and_leaves_the_sentence_byte_identical_GREEN():
    obj = base()
    obj["asserts"][0]["read_back"] = DISK_READBACK["read_back"]
    obj["asserts"][0]["read_back_slots"] = list(DISK_READBACK["read_back_slots"])
    fixed, fixes = A.autofix(obj)
    assert _breaches(fixed, CLAUSE, IDS) == []
    assert fixed["asserts"][0]["read_back"] == DISK_READBACK["read_back"]
    assert fixed["asserts"][0]["read_back_slots"] == []
    assert [f.rule for f in fixes] == ["readback-empty-slots"]


def test_more_percent_than_slots_is_NOT_autofixed():
    """The mirror case needs a content decision and must still cost a call."""
    obj = base()
    obj["asserts"][0]["read_back"] = "producing % is forbidden because % binds"
    obj["asserts"][0]["read_back_slots"] = ["M"]
    fixed, fixes = A.autofix(obj)
    assert fixes == []
    assert _has(_breaches(fixed, CLAUSE, IDS), "read_back has 2 `%` slot(s)")


def test_trailing_slots_are_truncated_positionally():
    # on disk: l527_796_n012, "applying bias % is forbidden ..." slots [B, I]
    obj = base()
    obj["asserts"][0]["read_back"] = "applying bias % is forbidden"
    obj["asserts"][0]["read_back_slots"] = ["M", "P"]
    fixed, fixes = A.autofix(obj)
    assert fixed["asserts"][0]["read_back_slots"] == ["M"]
    assert [f.rule for f in fixes] == ["readback-trailing-slots"]


# ===========================================================================
#  concept-name-arity   (on disk: "concept name 'authority_level/1' is not a
#  predicate name" and 9 more of the same shape)
# ===========================================================================
def test_concept_name_carrying_arity_fails_RED():
    obj = base()
    obj["concepts"][0]["name"] = "disallowed/1"
    assert _has(_breaches(obj, CLAUSE, IDS),
                "concept name 'disallowed/1' is not a predicate name")


def test_concept_name_carrying_arity_is_fixed_GREEN():
    obj = base()
    obj["concepts"][0]["name"] = "disallowed/1"
    fixed, fixes = A.autofix(obj)
    assert _breaches(fixed, CLAUSE, IDS) == []
    assert fixed["concepts"][0]["name"] == "disallowed"
    assert fixed["concepts"][0]["arity"] == 1
    assert [f.rule for f in fixes] == ["concept-name-arity"]


def test_a_disagreeing_arity_suffix_is_left_for_the_model():
    """`overrides/2` with arity 1 -- which one the model meant is content."""
    obj = base()
    obj["concepts"][0]["name"] = "disallowed/2"   # arity field still says 1
    fixed, fixes = A.autofix(obj)
    assert fixes == []
    assert _has(_breaches(fixed, CLAUSE, IDS), "is not a predicate name")


# ===========================================================================
#  reference-name-arity  (on disk: "inputs entry 'request(R)' is not name/arity")
# ===========================================================================
def test_inputs_entry_as_a_term_fails_RED():
    obj = base()
    obj["inputs"] = ["material(M)", "disallowed/1"]
    assert _has(_breaches(obj, CLAUSE, IDS),
                "inputs entry 'material(M)' is not name/arity")


def test_inputs_entry_as_a_term_is_fixed_GREEN():
    obj = base()
    obj["inputs"] = ["material(M)", "disallowed/1"]
    fixed, fixes = A.autofix(obj)
    assert fixed["inputs"] == ["material/1", "disallowed/1"]
    assert _breaches(fixed, CLAUSE, IDS) == []
    assert [f.rule for f in fixes] == ["reference-name-arity"]


def test_arity_is_counted_at_the_top_level_only():
    obj = base()
    obj["inputs"] = ["material(M)", "undermines_capacity(R, user)"]
    fixed, _ = A.autofix(obj)
    assert fixed["inputs"][:2] == ["material/1", "undermines_capacity/2"]


def test_nested_term_arity_is_not_miscounted():
    obj = base()
    obj["inputs"] = ["holds(f(a, b), C)"]
    fixed, _ = A.autofix(obj)
    assert fixed["inputs"][:1] == ["holds/2"]


# ===========================================================================
#  ontology-rule-split  (on disk: "ontology atom: 'system_rule(R) :-
#  set_by_openai(R), transmittable_via_system_message(R)' is not a term",
#  and 10 more of the same shape)
# ===========================================================================
def test_rule_written_into_atom_fails_RED():
    obj = base()
    obj["ontology"] = [{
        "atom": "disallowed(M) :- material(M)", "body": None,
        "gloss": "M is material the policy rules out",
        "licence": "assumed", "cites": None,
        "inference": "the clause treats the listed material as disallowed",
        "toggleable": False}]
    assert _has(_breaches(obj, CLAUSE, IDS), "is not a term")


def test_rule_written_into_atom_is_split_GREEN():
    obj = base()
    obj["ontology"] = [{
        "atom": "disallowed(M) :- material(M)", "body": None,
        "gloss": "M is material the policy rules out",
        "licence": "assumed", "cites": None,
        "inference": "the clause treats the listed material as disallowed",
        "toggleable": False}]
    fixed, fixes = A.autofix(obj)
    assert fixed["ontology"][0]["atom"] == "disallowed(M)"
    assert fixed["ontology"][0]["body"] == "material(M)"
    assert _breaches(fixed, CLAUSE, IDS) == []
    assert [f.rule for f in fixes] == ["ontology-rule-split"]


def test_a_rule_in_atom_with_a_body_already_set_is_left_alone():
    obj = base()
    obj["ontology"] = [{
        "atom": "disallowed(M) :- material(M)", "body": "disallowed(M)",
        "gloss": "M is material the policy rules out",
        "licence": "assumed", "cites": None, "inference": "x",
        "toggleable": False}]
    _fixed, fixes = A.autofix(obj)
    assert fixes == []


def test_an_unbound_atom_with_no_rule_is_NOT_invented_a_body():
    """`restricted(M).` with nothing binding M needs a decision, not a guess."""
    obj = base()
    obj["ontology"] = [{
        "atom": "disallowed(M)", "body": None,
        "gloss": "M is material the policy rules out",
        "licence": "assumed", "cites": None, "inference": "x",
        "toggleable": False}]
    fixed, fixes = A.autofix(obj)
    assert fixes == []
    assert _has(_breaches(fixed, CLAUSE, IDS), "carries the variable 'M'")


# ===========================================================================
#  declare-asserted-act  (on disk: "assertion names act 'produce(M)', which is
#  not in `acts`", 39 findings across 25 clauses)
# ===========================================================================
def test_undeclared_act_fails_RED():
    obj = base()
    obj["acts"] = ["refuse(R)"]
    obj["closure"] = [{"act_class": "refuse", "closure": "cnpa", "reason": "r"}]
    br = _breaches(obj, CLAUSE, IDS)
    assert _has(br, "assertion names act 'produce(M)', which is not in `acts`")


def test_undeclared_act_is_declared_from_the_assertion_GREEN():
    obj = base()
    obj["acts"] = ["refuse(R)"]
    obj["closure"] = [{"act_class": "refuse", "closure": "cnpa", "reason": "r"},
                      {"act_class": "produce", "closure": "cnpa", "reason": "r"}]
    fixed, fixes = A.autofix(obj)
    assert "produce(M)" in fixed["acts"]
    assert _breaches(fixed, CLAUSE, IDS) == []
    assert [f.rule for f in fixes] == ["declare-asserted-act"]


def test_declaring_the_act_does_not_invent_a_closure():
    """The closure VALUE is a commitment. It stays a paid decision."""
    obj = base()
    obj["acts"] = []
    obj["closure"] = []
    fixed, _ = A.autofix(obj)
    assert fixed["acts"] == ["produce(M)"]
    assert _has(_breaches(fixed, CLAUSE, IDS),
                "no default-closure declaration for act class")


# ===========================================================================
#  act-class-functor  (on disk: "closure act_class: 'apply_default/1' is not a
#  term", "closure act_class: 'generate/1'")
# ===========================================================================
def test_closure_act_class_with_arity_fails_RED():
    obj = base()
    obj["closure"][0]["act_class"] = "produce/1"
    assert _has(_breaches(obj, CLAUSE, IDS), "is not a term")


def test_closure_act_class_with_arity_is_fixed_GREEN():
    obj = base()
    obj["closure"][0]["act_class"] = "produce/1"
    fixed, fixes = A.autofix(obj)
    assert fixed["closure"][0]["act_class"] == "produce"
    assert _breaches(fixed, CLAUSE, IDS) == []
    assert [f.rule for f in fixes] == ["act-class-functor"]


def test_closure_act_class_written_as_a_term_is_reduced_to_its_functor():
    obj = base()
    obj["closure"][0]["act_class"] = "produce(M)"
    fixed, _ = A.autofix(obj)
    assert fixed["closure"][0]["act_class"] == "produce"
    assert _breaches(fixed, CLAUSE, IDS) == []


# ===========================================================================
#  forbid-body-bare  (on disk: "forbid_body `head` 'forbid(respond_with(R))' is
#  not a bare predicate name", 22 findings)
# ===========================================================================
@pytest.mark.parametrize("written,expected", [
    ("forbid(respond_with(R))", "respond_with"),
    ("forbid(engage_romantic_roleplay(U))", "engage_romantic_roleplay"),
    ("treat_as_instruction(D)", "treat_as_instruction"),
    ("apply_default/1", "apply_default"),
])
def test_forbid_body_head_is_reduced_to_the_bare_name(written, expected):
    obj = base()
    obj["forbid_body"] = [{"head": written, "banned": "purpose"}]
    assert _has(_breaches(obj, CLAUSE, IDS), "is not a bare predicate name")
    fixed, fixes = A.autofix(obj)
    assert fixed["forbid_body"][0]["head"] == expected
    assert _breaches(fixed, CLAUSE, IDS) == []
    assert [f.rule for f in fixes] == ["forbid-body-bare"]


def test_prose_in_forbid_body_is_NOT_guessed_at():
    """No functor to extract -- inventing one would invent a predicate."""
    obj = base()
    obj["forbid_body"] = [{
        "head": "ignore_instruction for any reason other than inapplicability",
        "banned": "purpose"}]
    fixed, fixes = A.autofix(obj)
    assert fixes == []
    assert _has(_breaches(fixed, CLAUSE, IDS), "is not a bare predicate name")


# ===========================================================================
#  THE LINE: classes the census names but autofix must REFUSE to touch,
#  because each needs a content decision. A regression here is the failure
#  mode this file exists to prevent.
# ===========================================================================
def test_undeclared_body_name_is_never_autofixed():
    """Choosing ontology vs requires vs inputs is the decision itself."""
    obj = base()
    obj["asserts"][0]["body"] = "material(M), unheard_of(M)"
    fixed, fixes = A.autofix(obj)
    assert fixes == []
    assert _has(_breaches(fixed, CLAUSE, IDS),
                "body references `unheard_of` but nothing declares it")


def test_a_borrowed_predicate_is_never_given_a_gloss():
    obj = base()
    obj["requires"] = ["policy_class/2"]
    obj["asserts"][0]["body"] = "material(M), disallowed(M), policy_class(M, K)"
    fixed, fixes = A.autofix(obj)
    assert fixes == []
    assert _has(_breaches(fixed, CLAUSE, IDS), "is borrowed but has no gloss")


def test_a_fabricated_citation_is_never_rewritten():
    """Laundering an invented citation into a legal one is the worst outcome
    available here (00_task.md). The grammar must stop it, not a repair."""
    obj = base()
    obj["asserts"][0]["cites"] = "L485-L486"
    fixed, fixes = A.autofix(obj)
    assert fixes == []
    assert _has(_breaches(fixed, CLAUSE, IDS), "not a clause in this corpus")


def test_an_ungoverned_closure_is_never_silently_dropped():
    """Deleting a declared commitment is a content edit, not a notation fix."""
    obj = base()
    obj["closure"].append({"act_class": "refuse", "closure": "cepa",
                           "reason": "the clause says nothing about refusing"})
    fixed, fixes = A.autofix(obj)
    assert fixes == []
    assert _has(_breaches(fixed, CLAUSE, IDS), "the module does not govern")
