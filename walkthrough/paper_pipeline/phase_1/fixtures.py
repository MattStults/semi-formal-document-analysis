"""Shared stage-1 module fixtures — ONE definition of the output contract.

Imported by `test_schema.py`, `test_checks.py`, `test_repair.py`,
`test_mutate.py` and `../../test_link.py`.

⭐ WHY THIS FILE EXISTS. Four test files each carried their own "minimal valid
stage-1 module" builder — `module()`, `module_dict()`, `module()` again and
`module_json()` — because four different agents each owned one file. Two costs
were paid repeatedly:

  * A contract change broke all four, in four different ways, with four
    different error messages. One change turned 17 tests red and took several
    rounds to repair.
  * ⭐ THE COPIES DISAGREED SILENTLY, AND DID. `test_link.py`'s `political()`
    encoded a module whose predicates were declared ONLY as `concepts`, with
    `requires` and `inputs` both empty — a shape whose single rule can never
    fire, and which the contract now rejects. That wrong shape sat in a test
    asserting it was correct, and nothing compared it against the other three
    builders. See `political_module()` below, which records the correction.

These fixtures are a SPECIFICATION of the stage-1 output contract. There is now
one copy, and `test_schema.test_every_shared_fixture_is_a_module_the_contract_ACCEPTS`
puts every named variant through `schema.validate()` AT TEST TIME — so a
contract change fails in one place, with one message naming the fixture.

⚠️ THE FAILURE MODE THIS FILE IS DESIGNED AGAINST is the opposite one: a single
over-general fixture that satisfies every check by construction, so the guards
stop being exercised and the suite goes green while testing nothing. `module()`
is therefore MINIMAL — one assertion, one ontology fact, one closure, one
`requires` entry — and every test still mutates exactly one thing off it. Where
a test needs a different shape, it gets a NAMED VARIANT here rather than a
looser base. `mutate_schema.py` is the check on this: if a change here makes a
mutation stop being caught, a guard has stopped being pinned.

⚠️ THIS MODULE IMPORTS NOTHING FROM THE PIPELINE, on purpose. `mutate_schema.py`
substitutes a MUTATED copy of `schema.py` before pytest collects, so a fixture
that validated itself at import time would run against whichever copy won the
race. Fixtures here are inert data; validating them is a test's job.

⚠️ Some fixtures in the test files are deliberately INVALID, or hand-written
because the schema can no longer render the shape under test
(`test_link.test_d4b_a_concept_the_table_does_not_carry_still_fires` uses a raw
`.lp` on purpose, and says why). Those are NOT here and must not be forced
through this builder.
"""

import json

#: Mirrors `schema.RESERVED`. ⚠️ NOT imported — this file imports nothing from
#: the pipeline so `mutate_schema.py` can swap a mutated schema in before
#: collection without a fixture racing it. Kept short and checked by
#: `test_every_shared_fixture_is_a_module_the_contract_ACCEPTS`.
_RESERVED_NAMES = {"asserts", "beats", "defines", "closure", "silent",
                   "because", "status", "violation", "fulfils", "live",
                   "passage", "deontic", "opposite", "beats_tc", "a", "b"}

# ==========================================================================
#  Licence blocks — Invariant 2's four arms, in one place each
# ==========================================================================


def textual(cites="m0001"):
    """A `textual` licence: the fact is in the clause, and cites it."""
    return dict(licence="textual", cites=cites, inference=None,
                toggleable=False)


TEXTUAL = textual()

#: `assumed`: not stated, but reached by a step the module NAMES.
ASSUMED = dict(licence="assumed", cites=None, inference="named step",
               toggleable=False)

#: `world`: outside knowledge, and therefore ablatable — hence `toggleable`.
WORLD = dict(licence="world", cites=None, inference=None, toggleable=True)

#: A read-back with no `%` slots, for facts whose sentence takes no arguments.
NO_SLOTS = dict(read_back="a sentence", read_back_slots=[])


# ==========================================================================
#  The canonical module
# ==========================================================================


def module(**over):
    """⭐ THE minimal VALID stage-1 module. Every test mutates one thing off it.

    Its single rule `forbid produce(M) :- disallowed(M)` rests on `disallowed/1`,
    which the ontology DERIVES from `restricted/1`, which `requires` declares as
    another clause's job. That is the ordinary translated shape: a rule, a
    derivation, and one name left to the link set.

    Keep it minimal. A fixture that satisfies more checks than it has to is how
    a guard stops being exercised without any test going red.
    """
    # ⚠️ `concepts` CARRIES THE BORROW'S MEANING, and it is not optional
    # padding. D4b level 2 requires every `requires`/`inputs` entry to have a
    # gloss: the borrow is enumerated into the situation signature, a seat is
    # shown situations built from it, and `render_situation` refuses a bare
    # predicate name. The minimal VALID module therefore includes this — the
    # minimum moved when the rule landed, and leaving it out would make every
    # test in the suite exercise a module that cannot be translated.
    base = dict(
        outcome="translated", clause_id="m0001", abstain_reason=None,
        claims=["C1 something"], acts=["produce(M)"],
        concepts=[dict(name="restricted", arity=1,
                       gloss="the material falls under a restricted policy",
                       **TEXTUAL)],
        ontology=[dict(atom="disallowed(M)", gloss="the material is disallowed",
                       body="restricted(M)", **ASSUMED)],
        asserts=[dict(status="forbid", act="produce(M)", body="disallowed(M)",
                      read_back="producing % is forbidden",
                      read_back_slots=["M"], **TEXTUAL)],
        beats=[], defines=[],
        closure=[dict(act_class="produce", closure="cepa",
                      reason="the clause carves out from a prohibition")],
        requires=["restricted/1"], inputs=[], forbid_body=[])
    base.update(over)
    return _gloss_the_borrows(base)


def _gloss_the_borrows(mod):
    """Give every `requires`/`inputs` entry a gloss, if it lacks one.

    ⭐ WHY THIS IS A FIXTURE CONVENIENCE AND NOT A HOLE. D4b level 2 requires a
    gloss for every borrow. Without this helper the rule's arrival broke **54
    tests**, none of them about glosses — they override `concepts` or
    `requires` for their own reasons and thereby drop a description they never
    meant to carry. Editing all 54 would have been 54 chances to quietly weaken
    an unrelated assertion.

    ⚠️ THE ESCAPE HATCH, AND IT IS LOAD-BEARING. A test that wants to exercise
    the rule must be able to build a module that BREAKS it, so it passes
    `_no_auto_gloss=True` and this helper stands aside.
    `test_a_borrowed_predicate_must_carry_a_gloss` depends on that, and
    `mutate_schema.py` proves the branch is still killed without it.
    """
    if mod.pop("_no_auto_gloss", False):
        return mod
    have = {f"{c['name']}/{c['arity']}" for c in mod.get("concepts") or []}
    # ⛔ MUST NOT CONTAIN THE PREDICATE'S OWN NAME. Two separate rules bite
    # here: D4b level 2 rejects a gloss that merely restates the name, and
    # RB1 (Invariant 1) rejects a rendering in which the label survives into
    # its own definition. A generated gloss built FROM the name fails the
    # second even when it passes the first — found by running it.
    # The two borrow fields get DIFFERENT sentences because they mean
    # different things: `requires` points at another clause, `inputs` at the
    # case being judged.
    generic = {
        "requires": "a condition the surrounding clause treats as given "
                    "and does not itself establish",
        # `inputs` covered since 2026-08-12 (Matt's ruling, from the first
        # live R3 render on node modules — READBACK_SMOKE.md): the schema now
        # requires a gloss for every borrow, both fields alike.
        "inputs": "a fact supplied with the case being judged, not "
                  "established by any clause of the corpus",
    }
    for field, gloss in generic.items():
        for p in list(mod.get(field) or []):
            if p in have or "/" not in p or p.split("/")[0] in _RESERVED_NAMES:
                continue
            name, _, ar = p.partition("/")
            have.add(p)
            mod.setdefault("concepts", []).append(
                dict(name=name, arity=int(ar), gloss=gloss, **TEXTUAL))
    return mod


def module_json(**over):
    """The canonical module as the model returns it: a JSON string.

    ⚠️ A THIN SERIALISER, never a second definition. `test_repair.py` needs wire
    text and everything else needs dicts; two hand-kept copies of the same shape
    is the duplication this file exists to remove.
    """
    return json.dumps(module(**over))


# ==========================================================================
#  Named variants — derived from `module()`, never re-declared
# ==========================================================================
#
# Each is `module()` with a stated set of fields replaced, so a new top-level
# field is added in exactly one place. `over` is applied LAST, so a caller can
# still bend any field of a variant.


def _variant(fixed, over):
    base = module(**fixed)
    base.update(over)
    return base


def situation_module(**over):
    """The shape `test_checks.py` needs: the body predicate is a situation INPUT.

    Its one assertion depends on `new_material/1`, declared as a situation
    input rather than derived through the ontology — so a clean run has notes
    and no errors, which is what makes the error/note distinction testable at
    all.
    """
    return _variant(dict(
        claims=["C1 producing new material of this kind is forbidden"],
        ontology=[],
        # The input's gloss is written here, not auto-generated: D4b level 2
        # requires every borrow — `inputs` included since the 2026-08-12
        # ruling (READBACK_SMOKE.md) — to say what the module needs it to MEAN.
        concepts=[material_concept()],
        asserts=[dict(status="forbid", act="produce(M)",
                      body="new_material(M)",
                      read_back="producing % is forbidden",
                      read_back_slots=["M"], **TEXTUAL)],
        closure=[dict(act_class="produce", closure="cnpa",
                      reason="the clause speaks of what may not be produced")],
        requires=[], inputs=["new_material/1"]), over)


def m0255_module(**over):
    """The worked example's clause — the shape `test_link.py` renders.

    Both body predicates arrive with the case, so `requires` is empty and the
    link checks see a module with no outstanding cross-clause dependency.
    """
    return _variant(dict(
        clause_id="m0255",
        claims=["C1 the exception's scope is exactly restricted and sensitive"],
        ontology=[],
        # Both inputs carry real glosses — required for every borrow since the
        # 2026-08-12 ruling (READBACK_SMOKE.md).
        concepts=[material_concept(**textual("m0255")),
                  dict(**textual("m0255"), name="disallowed", arity=1,
                       gloss="the material falls under a policy that bars "
                             "its production")],
        asserts=[dict(**textual("m0255"), status="forbid", act="produce(M)",
                      body="new_material(M), disallowed(M)",
                      read_back="producing % is still forbidden",
                      read_back_slots=["M"])],
        closure=[dict(act_class="produce", closure="cepa",
                      reason="the clause speaks only of what it forbids")],
        requires=[], inputs=["new_material/1", "disallowed/1"]), over)


#: The two concepts m0217 declares. Kept apart so a test can supply one of them
#: to a concept table and leave the other dangling.
CONC_POL = dict(name="political_content", arity=1,
                gloss="content that is political in nature")
CONC_AUD = dict(name="broad_audience", arity=1,
                gloss="content crafted for an unspecified or broad audience")


def political_module(**over):
    """The m0217 shape, with concepts declared — the concept-table fixture.

    ⚠️ THE FIXTURE THAT WAS SILENTLY WRONG. The live module declared these
    predicates ONLY as concepts, with `requires` and `inputs` both empty — so
    its single rule could never fire. That is now rejected, so the fixture
    declares them as `inputs`, which is what they are: facts about the case
    being judged. A concept says what a predicate MEANS; it does not say that
    anything DEFINES it.
    """
    return _variant(dict(
        clause_id="m0217",
        claims=["C1 political content for a broad audience is allowed"],
        ontology=[],
        concepts=[dict(**textual("m0217"), **CONC_POL),
                  dict(**textual("m0217"), **CONC_AUD)],
        asserts=[dict(**textual("m0217"), status="permit", act="produce(M)",
                      body="political_content(M), broad_audience(M)",
                      read_back="producing % is permitted",
                      read_back_slots=["M"])],
        closure=[dict(act_class="produce", closure="cepa",
                      reason="the clause speaks only of what it forbids")],
        requires=[], inputs=["political_content/1", "broad_audience/1"]), over)


def definitional_module(**over):
    """A clause that introduces vocabulary and asserts no status.

    4 of 4 live clauses returned this and the earlier contract rejected it: the
    model was not asserting a classification, it was naming a concept and
    saying what it means. No acts, no assertions, no closure — and still a
    TRANSLATION, not an abstention, because `defines` carries content.
    """
    return _variant(dict(
        concepts=[concept()], ontology=[], asserts=[], acts=[], closure=[],
        requires=[],
        defines=[dict(kind="assistant", term="assistant_entity", **TEXTUAL)]),
        over)


def module_with_beat(**over):
    """A module recording a superiority its own clause states."""
    return _variant(dict(beats=[beat()]), over)


def module_with_quantified_beat(**over):
    """A `beats` whose slots are VARIABLES bound by a body — m0255's own case.

    It needs no corpus membership for `winner`/`loser`, which is the whole
    difference from `module_with_beat()`.
    """
    return _variant(dict(beats=[quantified_beat()],
                         requires=["restricted/1", "ranked/1"]), over)


def abstention(**over):
    """A VALID abstention: a reason, and every content field forced empty.

    An abstention passes every deterministic check trivially, so it is a
    terminal outcome rather than a findings list — which is why it is a fixture
    of its own and not `module(outcome="abstained")`.
    """
    base = dict(
        outcome="abstained", clause_id="m0001",
        abstain_reason="the clause is a section heading and attaches no status",
        claims=[], acts=[], concepts=[], ontology=[], asserts=[], beats=[],
        defines=[], closure=[], requires=[], inputs=[], forbid_body=[])
    base.update(over)
    return base


def abstention_json(**over):
    """The abstention on the wire. Serialises `abstention()`; defines nothing."""
    return json.dumps(abstention(**over))


# ==========================================================================
#  Entry builders — the sub-records, so one field can be varied in isolation
# ==========================================================================


def assertion(**over):
    """`module()`'s own assertion, extracted so one field can be bent alone."""
    base = dict(status="forbid", act="produce(M)", body="disallowed(M)",
                read_back="producing % is forbidden", read_back_slots=["M"],
                **TEXTUAL)
    base.update(over)
    return base


def concept(**over):
    """A concept DECLARATION: a name, an arity, and a written definition."""
    base = dict(name="assistant_entity", arity=1,
                gloss="the entity that the end user or developer interacts with",
                **TEXTUAL)
    base.update(over)
    return base


def material_concept(**over):
    """`situation_module()`'s own predicate, as a concept declaration."""
    base = concept(name="new_material", arity=1,
                   gloss="material the assistant would be creating rather "
                         "than transforming")
    base.update(over)
    return base


def beat(**over):
    """A superiority this module's own clause states, over corpus clauses."""
    base = dict(sayer="m0001", winner="m0002", loser="m0255", body=None,
                **NO_SLOTS, **TEXTUAL)
    base.update(over)
    return base


def quantified_beat(**over):
    """A superiority whose slots are variables the body binds."""
    base = beat(winner="W", loser="L", body="ranked(W), ranked(L)")
    base.update(over)
    return base


# ==========================================================================
#  The registry the validation test reads
# ==========================================================================
#
# ⭐ Every entry is put through `schema.validate()` by
# `test_schema.test_every_shared_fixture_is_a_module_the_contract_ACCEPTS`.
# A new variant added here is checked by that test with no further wiring; a
# variant that stops validating names itself in the failure message.

VALID_MODULES = {
    "module": module,
    "situation_module": situation_module,
    "m0255_module": m0255_module,
    "political_module": political_module,
    "definitional_module": definitional_module,
    "module_with_beat": module_with_beat,
    "module_with_quantified_beat": module_with_quantified_beat,
    "abstention": abstention,
}
