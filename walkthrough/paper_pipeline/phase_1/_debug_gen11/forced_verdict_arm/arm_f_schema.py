#!/usr/bin/env python3
"""ARM F — the review list as REQUIRED OUTPUT FIELDS, not as prose.

⛔ `schema.py` IS GUARD-WATCHED AND IS NOT EDITED BY THIS ARM.  Everything here
DERIVES from what `translate.py` already sends: `schema.response_format(strict)`
is called, its output is deep-copied, and the copy is extended.  The production
function is never patched, never shadowed and never written to.

WHY A DERIVED COPY RATHER THAN A HAND-WRITTEN SCHEMA.  `schema.json_schema()`
does three things a hand copy would silently get wrong — it inlines `$defs`,
rewrites `Optional[X]` to a nullable type keeping the whole body, and forces
`additionalProperties: false` plus `required == list(properties)` at EVERY
object level.  A hand-written arm-F schema would be a second implementation of
that flattening, and the first time the two disagreed the arm would be
measuring the schema difference instead of the coercion.

THE STRIP, AND WHY IT IS SAFE.  `schema.Module` is `extra="forbid"`, so the
returned object cannot be handed to `schema.validate_all` with `checks` still
on it.  `strip()` deletes exactly one TOP-LEVEL key and rebinds every other
value BY IDENTITY — no copy, no re-serialisation, no normalisation.
`strip_proof()` then states that as a checkable fact per field.
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
if PHASE1 not in sys.path:
    sys.path.insert(0, PHASE1)

import schema                                                 # noqa: E402

#: The one key arm F adds to the wire schema.  Nothing else is added anywhere.
EXTRA_KEY = "checks"


# ==========================================================================
#  THE SIX ENTRIES, AND WHY THESE SIX
# ==========================================================================
#
# `_debug_gen11/list_in_prompt/ORDERING.md` ranks the shipped 20 by the number
# of DISTINCT CLAUSES on which each produced an actual finding, over the same
# 17 clauses this arm draws.  Five entries carry 48 of the 82 findings and 20
# of the 27 CAUGHT: P8, N7, N10, P6, N1 — shipped as list entries 1, 2, 3, 4
# and 5.  Those five are C1..C5 here.
#
# ⛔ SHIPPED ENTRY 5 (N1) IS NOT SHIPPED AS WRITTEN.  It is the one entry
# MEASURED to manufacture defects: `list_in_prompt_insample/RESULT.md` §7
# records four clauses where obeying it correctly turned a HARMLESS inert
# constant into a VACUOUS bodied rule — `no_moral_ambiguity(S) :- scenario(S)`
# makes a clause scoped to "scenarios where there's no moral ambiguity" govern
# every scenario.  Excluding it was rejected: the harm is exactly the thing a
# forced field can be built to block, and dropping the entry would drop the
# arm's only test of whether structure fixes an instruction that prose could
# not.  C5 is REWRITTEN in two ways, both stated so a reader can check them:
#   (i)  the entry's headline is inverted.  The shipped text's headline asks
#        for the bodied rule and buries the document-atom exception in its
#        last sentence; C5 leads with the ASYMMETRY OF HARM (inert = concludes
#        less; vacuous = concludes more, in the dangerous direction) and makes
#        the conversion CONDITIONAL on carrying the span's own discriminating
#        condition into the body.
#   (ii) the fix is itself STRUCTURAL, which is this arm's whole thesis.
#        `excluded_case` is a required field and is mandatory on C5: name one
#        concrete situation that satisfies the body's type predicate but NOT
#        the head.  `scenario(S)` admits no such case, so the vacuous rule
#        cannot be written and its verdict filled in at the same time.
#
# C6 is NOT in the evidence-ranked top five — shipped entry 12 (P1) is rank 13
# with 3 findings.  It is included anyway, and the reason is specific to what
# this arm measures: `l4252_4482_n016` is the sharpest MEASURED "held the entry
# and ignored it" cell in the whole programme — the in-sample arm shipped entry
# 12 quoting this clause's own span as the remedy, and the model reproduced all
# three inverted `prefer`s VERBATIM.  A forced verdict on that exact clause is
# the highest-information single cell available for the coercion hypothesis, so
# it is bought at the price of one extra check.
#
# Everything else on the shipped list is left out.  Grounds: 20 forced verdicts
# is a ritual, not a review — and the tail is where the measured mis-directions
# live (N6 and P2 found nothing in 17; P4, P10 and N4 fired only in-sample, N4
# and P4 with recorded mis-directions).  Coercing a verdict on an entry that has
# never found anything buys nothing and spends output tokens that the checks the
# evidence supports would otherwise have.

_C1 = (
    "C1 — DOES A GLOSS RESTATE ITS PREDICATE'S NAME? Found something on 12 of "
    "17 reviewed clauses; the highest-yield check there is. Read every `gloss` "
    "you wrote in `concepts` and `ontology` ABOVE. `safety_precaution_"
    "suggestion/1` glossed 'S is a suggestion that the user take safety "
    "precautions' is the name, re-spaced, and passes zero information; a gloss "
    "is the only way another module's definition can ever be matched to yours. "
    "Does each gloss say what makes the predicate TRUE, in words that are not "
    "the name? For a relation of arity >= 2, does it say which argument is "
    "which? Also: does any rule's head appear in its own body? "
    "(`forbid X(R) :- X(R)` is SCHEMA-FORCED and is NOT a violation of this.)"
)

_C2 = (
    "C2 — IS AN 'UNLESS' ARM BEING TREATED AS A RULE, AND IS A `closure` "
    "DECIDING WHAT THE SPAN LEFT OPEN? Found something on 10 of 17. 'should "
    "honor ... unless it conflicts' WITHDRAWS a requirement on the excepted "
    "branch; it does not create a prohibition there, so a `forbid` on that "
    "branch asserts something the span never says. The same reasoning governs "
    "`closure`: if the clause states a duty inside one trigger and takes no "
    "position outside it, reading its silence as blanket permission (`cepa`) "
    "is a commitment the clause never made — use `unclear`. Measured: `cepa` "
    "was the wrong value on four separate clauses, and circular on a fifth. "
    "Check the `closure` entries and `reason` fields you wrote ABOVE."
)

_C3 = (
    "C3 — DOES EVERY SYMBOL YOU COINED TRACE TO A SUBSTRING OF THE NARROWED "
    "TEXT? Found something on 10 of 17. If the node prints '[node narrows this "
    "span to: ...]', the text around it is CONTEXT, NOT LICENCE. "
    "`tiananmen_example` was fluent and unanchored — the narrowed text named no "
    "event; `answers_user_question` was coined for a span containing neither "
    "'user' nor 'question'. For each name in the module ABOVE, which substring "
    "of the NARROWED text does it come from? Two known blind spots, so run it "
    "wider than the name: (i) run it on the GLOSS too — a name can trace while "
    "its gloss imports material from a neighbouring sentence; (ii) a FUSED name "
    "(`exaggerated_or_stereotypical`) can be assembled from three legitimate "
    "substrings and still weld a disjunction into one opaque symbol."
)

_C4 = (
    "C4 — IS EVERY ASSERTED PREDICATE SUPPORTED BY THE NARROWED TEXT? Found "
    "something on 8 of 17. Where `ESTABLISHES` and the narrowed SOURCE TEXT "
    "conflict, the narrowed SOURCE TEXT GOVERNS. `ESTABLISHES` may direct WHICH "
    "claim of the span you express; it may not ADD content the span does not "
    "state, and it may not DROP a qualifier the span does state (measured: it "
    "restated a permission with the span's own parenthetical deleted). Ask in "
    "BOTH directions of the module ABOVE: what does `ESTABLISHES` say that the "
    "span does not, and what does the span say that `ESTABLISHES` drops? "
    "Anything `ESTABLISHES` adds is still expressible — as `assumed`, with the "
    "`inference` naming `ESTABLISHES` as its source. Nothing is lost, only "
    "marked. Vocabulary appearing in the node's own PROVIDES/NEEDS glosses is "
    "NOT thereby 'outside the narrowing' — check the source text, not the "
    "node header."
)

_C5 = (
    "C5 — DOES THE ATOM DISCRIMINATE BETWEEN CASES, AND DOES ITS BODY DO WORK? "
    "Two failures, and they are NOT symmetric. (a) An arity-0 or fully ground "
    "atom (`no_moral_ambiguity`, `side_effect_examples(sending_email)`) is "
    "INERT: nothing in a real situation unifies with it, so the module simply "
    "concludes LESS than the span. (b) A bodied rule whose body is a bare TYPE "
    "DECLARATION — `no_moral_ambiguity(S) :- scenario(S)`, "
    "`repeats_user_prompt(R) :- response(R)` — is WORSE: it derives the span's "
    "discriminating condition OF EVERY CASE, so the module concludes MORE than "
    "the span, in the dangerous direction. A clause scoped to 'scenarios where "
    "there is no moral ambiguity' would now govern all scenarios. "
    "⛔ SO: do NOT convert an inert constant into a bodied rule unless you can "
    "carry the SPAN'S OWN discriminating condition into that body. A vacuous "
    "body is a worse defect than the constant it replaced. "
    "⛔ And a ground atom ABOUT THE DOCUMENT (`root_authority(section_x)`) is "
    "CORRECT — there is no situation to match — so leave it alone. "
    "`excluded_case` is MANDATORY on this check: name one concrete situation "
    "that satisfies your body's type predicate but NOT its head. If you cannot "
    "name one, the body is vacuous and you must not write it."
)

_C6 = (
    "C6 — DOES A `prefer` NAME THE ACT TO AVOID? `status` has NO NEGATIVE "
    "POLE. Faced with 'avoid X' the natural move is `prefer X` with a "
    "`read_back` that negates it — so the compiled rule states the OPPOSITE of "
    "the document, and every deterministic check still passes. Name the "
    "AVOIDANCE as the act (`prefer minimize_redundant_phrases`, not "
    "`prefer include_redundant_phrases`), or use `forbid` where the span is "
    "that strong and the thing is not a gradient. Never leave `status` and "
    "`read_back` disagreeing — and never fix that by rewriting the "
    "`read_back`: the honest prose is the evidence, the formal item is the "
    "defect."
)

ENTRIES = [("C1", _C1), ("C2", _C2), ("C3", _C3),
           ("C4", _C4), ("C5", _C5), ("C6", _C6)]

ENTRY_IDS = [e for e, _ in ENTRIES]

VERDICTS = ["applies_and_handled", "applies_and_not_handled", "does_not_apply"]


def _check_item_schema():
    """One element of `checks`.

    ⭐ FIELD ORDER INSIDE THE ITEM IS DELIBERATE: `evidence` PRECEDES `verdict`.
    A verdict emitted first can be produced without consulting the object at
    all; a quotation cannot. `ORDERING.md`'s own reading of why the top entries
    scored is that they 'could only be answered by looking at the finished
    text', so the field that forces the look comes first.
    """
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "entry_id": {
                "type": "string", "enum": ENTRY_IDS,
                "description": "which check this is. Emit all six, in order, "
                               "exactly once each: " + ", ".join(ENTRY_IDS),
            },
            "evidence": {
                "type": "string",
                "description": "FIRST, and before you rule: quote the exact "
                               "text from the module you just wrote ABOVE that "
                               "this check bears on — the gloss, the rule, the "
                               "coined name, the status. If nothing in the "
                               "module bears on it, say which field you looked "
                               "at and that it is empty. One line.",
            },
            "verdict": {
                "type": "string", "enum": VERDICTS,
                "description": "`applies_and_handled`: the check bears on this "
                               "module and the object above already satisfies "
                               "it. `applies_and_not_handled`: it bears and the "
                               "object above does NOT satisfy it — say so; a "
                               "declared defect is worth more than a hidden "
                               "one. `does_not_apply`: nothing in this module "
                               "can trigger it. ⚠️ Rule on the OBJECT ABOVE, "
                               "not on your intentions.",
            },
            "action": {
                "type": "string",
                "description": "one line. When the verdict is "
                               "`applies_and_handled`, state what you DID about "
                               "it and where in the module it is visible. When "
                               "`applies_and_not_handled`, state what is wrong "
                               "and why you left it. When `does_not_apply`, "
                               "write 'n/a — ' and the reason nothing in this "
                               "module triggers it.",
            },
            "excluded_case": {
                "type": ["string", "null"],
                "description": "MANDATORY ON C5, null on every other check. "
                               "Name one concrete situation that satisfies the "
                               "body's type predicate but NOT the head of the "
                               "bodied `ontology` rule you wrote. If no such "
                               "case exists, the body is vacuous — write "
                               "'NONE — the body is vacuous' and repair the "
                               "module above before returning it.",
            },
        },
        "required": ["entry_id", "evidence", "verdict", "action",
                     "excluded_case"],
    }


def checks_property():
    """The `checks` property itself."""
    return {
        "type": "array",
        "minItems": len(ENTRIES),
        "maxItems": len(ENTRIES),
        "description":
            "⭐ REQUIRED. Six verdicts on the module you have just written, in "
            "order C1..C6, exactly one each. These are not advice: they are "
            "part of the object, and a module without them is malformed. Each "
            "was MEASURED on this corpus by a reviewer reading finished "
            "modules against their spans. Rule on THE OBJECT ABOVE, not on "
            "your intentions — and if a check finds something, GO BACK AND FIX "
            "THE MODULE, then rule on the fixed version. Saying "
            "`applies_and_not_handled` is better than saying "
            "`does_not_apply` about a defect that is there.\n\n"
            + "\n\n".join(f"{eid}. {text}" for eid, text in ENTRIES),
        "items": _check_item_schema(),
    }


def request_json_schema(strict=True):
    """`schema.response_format(strict)`, DEEP-COPIED, plus one property.

    The copy is what is mutated; `schema.json_schema()` builds a fresh dict on
    every call anyway, but the deep copy makes that independent of that fact.
    """
    rf = copy.deepcopy(schema.response_format(strict))
    root = rf["json_schema"]["schema"]
    if root.get("type") != "object" or "properties" not in root:
        raise SystemExit("the production wire schema is not the object this "
                         "arm assumed; refusing to extend it blind")
    if EXTRA_KEY in root["properties"]:
        raise SystemExit(f"production already has a {EXTRA_KEY!r} property — "
                         f"the arm's name would collide with a real field")
    # ⭐ APPENDED LAST, AFTER `forbid_body`, AND THAT IS A DECISION.
    # A structured decoder emits properties in schema order, so placement
    # decides whether the verdict is a PLAN or a REVIEW. Placed first, the
    # model would rule on a module it has not written — a prediction about
    # its own intentions, which is exactly the thing the shipped prose
    # already failed to convert into behaviour, and which cannot be
    # falsified against the object. Placed last, every verdict is about
    # bytes already committed on the wire, so "it said clean and the defect
    # is there" becomes a checkable statement. The cost is accepted and
    # stated: last placement is also the placement most exposed to
    # rubber-stamping, because the module is already written and the cheap
    # continuation is to ratify it. THAT IS THE MEASUREMENT.
    root["properties"][EXTRA_KEY] = checks_property()
    # `schema.json_schema()` sets `required = list(properties)` at every object
    # level; the append has to be mirrored or the field is optional.
    root["required"] = list(root["properties"])
    return rf


# ==========================================================================
#  THE STRIP
# ==========================================================================

def strip(obj):
    """Return the object `schema.validate_all` / `checks.run_checks` get.

    Exactly one top-level key is dropped. Every surviving value is the SAME
    OBJECT, rebound — not copied, not re-serialised, not normalised.
    """
    if not isinstance(obj, dict):
        return obj, None
    extra = obj.get(EXTRA_KEY)
    return {k: v for k, v in obj.items() if k != EXTRA_KEY}, extra


def strip_proof(obj, stripped):
    """State the strip's safety as facts a reader can check.

    * `keys_removed` is exactly {EXTRA_KEY}, nothing else left or arrived;
    * every surviving field is IDENTICAL BY `is` — not merely equal;
    * every surviving field re-serialises to the same bytes.

    The third is redundant given the second and is kept anyway: identity is the
    strong claim, byte-equality is the one a sceptic can re-run from the files
    on disk without trusting this process's object graph.
    """
    if not isinstance(obj, dict):
        return {"applicable": False}
    removed = sorted(set(obj) - set(stripped))
    added = sorted(set(stripped) - set(obj))
    ident = all(stripped[k] is obj[k] for k in stripped)
    bytes_eq = all(
        json.dumps(stripped[k], sort_keys=True, ensure_ascii=False)
        == json.dumps(obj[k], sort_keys=True, ensure_ascii=False)
        for k in stripped)
    return {
        "applicable": True,
        "keys_removed": removed,
        "keys_added": added,
        "removed_is_exactly_the_arm_key": removed == [EXTRA_KEY] and not added,
        "every_surviving_field_identical_by_is": ident,
        "every_surviving_field_byte_identical": bytes_eq,
        "n_fields_before": len(obj),
        "n_fields_after": len(stripped),
    }


def checks_wellformed(extra):
    """Shape report on the returned `checks` — the provider's `enum`/`minItems`
    honouring is UNVERIFIED for this model, so it is measured, not assumed."""
    rep = {"present": extra is not None, "n": None, "ids": None,
           "ids_exact": None, "verdicts_in_enum": None,
           "c5_excluded_case": None}
    if not isinstance(extra, list):
        return rep
    rep["n"] = len(extra)
    ids = [e.get("entry_id") for e in extra if isinstance(e, dict)]
    rep["ids"] = ids
    rep["ids_exact"] = ids == ENTRY_IDS
    rep["verdicts_in_enum"] = all(
        isinstance(e, dict) and e.get("verdict") in VERDICTS for e in extra)
    for e in extra:
        if isinstance(e, dict) and e.get("entry_id") == "C5":
            rep["c5_excluded_case"] = e.get("excluded_case")
    return rep


if __name__ == "__main__":
    rf = request_json_schema(True)
    root = rf["json_schema"]["schema"]
    prod = schema.response_format(True)["json_schema"]["schema"]
    print("production top-level properties:", list(prod["properties"]))
    print("arm F      top-level properties:", list(root["properties"]))
    print("arm F required == properties:",
          root["required"] == list(root["properties"]))
    same = all(
        json.dumps(root["properties"][k], sort_keys=True)
        == json.dumps(prod["properties"][k], sort_keys=True)
        for k in prod["properties"])
    print("every PRODUCTION property untouched in the arm-F copy:", same)
    print("production object still intact after deriving:",
          json.dumps(schema.response_format(True), sort_keys=True)
          == json.dumps(prod and schema.response_format(True), sort_keys=True))
    print("wire schema size: production %d c, arm F %d c"
          % (len(json.dumps(prod)), len(json.dumps(root))))
    demo = {"outcome": "translated", "clause_id": "x", "abstain_reason": None,
            "claims": ["a"], "acts": [], "concepts": [], "ontology": [],
            "asserts": [], "beats": [], "defines": [], "closure": [],
            "requires": [], "inputs": [], "forbid_body": [],
            "checks": [{"entry_id": "C1", "evidence": "e", "verdict":
                        "does_not_apply", "action": "n/a", "excluded_case":
                        None}]}
    s, extra = strip(demo)
    print("strip proof:", json.dumps(strip_proof(demo, s)))
    print("checks shape:", json.dumps(checks_wellformed(extra)))
