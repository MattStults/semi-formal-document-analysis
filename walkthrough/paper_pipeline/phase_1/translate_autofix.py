#!/usr/bin/env python3
"""translate_autofix.py -- deterministic repairs that must never cost a call.

NEW FILE. Pure functions over the raw module dict. No network, no I/O, no
imports from translate.py / dispatch_core.py / promise_repair.py.

WHY THIS EXISTS
---------------
`TRANSLATION_REPAIR_CENSUS.md` measures every repair round on disk. 60% of
translation spend is repair rounds, and a large share of those rounds are
NOTATIONAL: the model wrote the right content in the wrong rendering of a name,
or supplied a list the format rules say should be empty. Re-prompting a model to
convert `authority_level/1` into `name: authority_level, arity: 1` is a paid call
buying an edit with no content decision in it.

⛔ THE LINE THIS FILE MUST NOT CROSS.
A rule belongs here ONLY if the corrected value is fully determined by what the
model already wrote, so that applying it invents nothing and deletes nothing a
reader could have meant. Anything that requires CHOOSING -- which of
ontology/requires/inputs a name belongs in, what a borrowed predicate means,
whether silence permits or prohibits, which variable fills a `%` -- stays with
the model and costs a call. That is the correct price for a decision.

Every rule below names the instruction it is enforcing, because the campaign's
standing lesson is that a stated rule is not an enforced rule.

Each rule is individually addressable by name so a caller can enable a subset,
and `autofix` is IDEMPOTENT: running it twice changes nothing the second time.
"""
from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field

#: `name/arity`, the reference rendering of a predicate.
_NAME_ARITY = re.compile(r"^([a-z][A-Za-z0-9_]*)/(\d+)$")
#: `f(A, B)` or `f`, the term rendering.
_TERM = re.compile(r"^([a-z][A-Za-z0-9_]*)\s*\((.*)\)$")
_BARE = re.compile(r"^[a-z][A-Za-z0-9_]*$")


@dataclass
class Fix:
    """One deterministic edit, located, with the instruction it enforces."""
    rule: str
    where: str
    before: str
    after: str
    enforces: str


def _arity_of(args: str) -> int:
    """Count top-level comma-separated arguments of a term's argument string."""
    args = args.strip()
    if not args:
        return 0
    depth = n = 0
    for ch in args:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif ch == "," and depth == 0:
            n += 1
    return n + 1


def _functor(term: str):
    """Bare functor name of a term, or None if the string is not a term."""
    term = (term or "").strip().rstrip(".")
    if term.endswith("()"):
        term = term[:-2]
    if _BARE.match(term):
        return term
    m = _TERM.match(term)
    return m.group(1) if m else None


# ===========================================================================
#  RULES
# ===========================================================================

def _fix_readback_empty_slots(mod, fixes):
    """read_back with NO `%` but a non-empty read_back_slots -> slots = [].

    ENFORCES 10_output_format.md: "If the sentence needs no substitution, write
    it with no `%` and no arguments -- that is a perfectly good read-back and is
    not an error", and schema.ReadBack's own field text: "This is not the list of
    the rule's variables: a read-back with no substitution point is a good
    read-back and takes an empty list".

    DETERMINISM: the rendered sentence is byte-identical before and after. The
    slot list is unreachable -- there is no `%` for any entry to fill. Nothing a
    reader could have meant is lost, because nothing was ever rendered from it.
    """
    for fld in ("asserts", "beats"):
        for i, item in enumerate(mod.get(fld) or []):
            if not isinstance(item, dict):
                continue
            rb = item.get("read_back") or ""
            slots = item.get("read_back_slots")
            if isinstance(slots, list) and slots and rb.count("%") == 0:
                fixes.append(Fix("readback-empty-slots", f"{fld}[{i}]",
                                 repr(slots), "[]",
                                 "10_output_format.md: a read-back with no "
                                 "substitution point takes []"))
                item["read_back_slots"] = []


def _fix_readback_trailing_slots(mod, fixes):
    """More slot entries than `%` markers -> drop the unreachable trailing ones.

    ENFORCES 10_output_format.md: "Put one `%` where each argument goes, in
    order... The count must match: N slots, N arguments."

    DETERMINISM: slots fill `%` positionally and in order, so entries past the
    last `%` are unreachable. The rendered sentence is unchanged.

    ⚠️ The MIRROR case -- more `%` than entries -- is NOT fixed here and must
    not be: choosing which variable fills the extra `%` is a content decision.
    """
    for fld in ("asserts", "beats"):
        for i, item in enumerate(mod.get(fld) or []):
            if not isinstance(item, dict):
                continue
            rb = item.get("read_back") or ""
            slots = item.get("read_back_slots")
            n = rb.count("%")
            if isinstance(slots, list) and n and len(slots) > n:
                fixes.append(Fix("readback-trailing-slots", f"{fld}[{i}]",
                                 repr(slots), repr(slots[:n]),
                                 "10_output_format.md: N slots, N arguments"))
                item["read_back_slots"] = slots[:n]


def _fix_concept_name_arity(mod, fixes):
    """concepts[i].name written as `name/arity` -> bare name.

    ENFORCES 00_task.md rule 10: "The `/arity` notation never enters a value
    slot: a `concepts` entry's `name` is the bare name (its arity is the entry's
    own `arity` field)".

    DETERMINISM: applied ONLY when the suffix agrees with the entry's own
    `arity` field, so the fix asserts nothing the model did not already say
    twice. A DISAGREEMENT (`overrides/2` with `arity: 1`) is left alone -- which
    of the two the model meant is a content decision.
    """
    for i, c in enumerate(mod.get("concepts") or []):
        if not isinstance(c, dict):
            continue
        m = _NAME_ARITY.match((c.get("name") or "").strip())
        if m and c.get("arity") == int(m.group(2)):
            fixes.append(Fix("concept-name-arity", f"concepts[{i}].name",
                             c["name"], m.group(1),
                             "00_task.md r10: `/arity` never enters a value slot"))
            c["name"] = m.group(1)


def _fix_reference_to_name_arity(mod, fixes):
    """`requires`/`inputs` entry written as a TERM -> `name/arity`.

    ENFORCES 00_task.md rule 10: "Include arity everywhere a predicate is named
    as a reference -- in `requires`, in `inputs`... `forbids/2`, never
    `forbids`", and schema.Module._coherent's "entry is not name/arity".

    DETERMINISM: the arity is read off the term the model wrote. `request(R)`
    can only mean `request/1`.
    """
    for fld in ("requires", "inputs"):
        lst = mod.get(fld)
        if not isinstance(lst, list):
            continue
        for i, p in enumerate(lst):
            if not isinstance(p, str) or _NAME_ARITY.match(p.strip()):
                continue
            m = _TERM.match(p.strip())
            if m:
                new = f"{m.group(1)}/{_arity_of(m.group(2))}"
                fixes.append(Fix("reference-name-arity", f"{fld}[{i}]", p, new,
                                 "00_task.md r10: references carry /arity"))
                lst[i] = new


def _fix_act_class_to_functor(mod, fixes):
    """`closure[i].act_class` written as `name/arity` -> the bare functor.

    ENFORCES 00_task.md rule 10: "`closure.act_class` / `forbid_body` slots take
    the bare functor name."

    DETERMINISM: schema compares act_class against `{a.split("(")[0] for a in
    acts}` -- the bare functor is the only value that can ever match, and the
    name is already written.
    """
    for i, c in enumerate(mod.get("closure") or []):
        if not isinstance(c, dict):
            continue
        m = _NAME_ARITY.match((c.get("act_class") or "").strip())
        if m:
            fixes.append(Fix("act-class-functor", f"closure[{i}].act_class",
                             c["act_class"], m.group(1),
                             "00_task.md r10: closure.act_class is the bare "
                             "functor name"))
            c["act_class"] = m.group(1)
        else:
            f = _functor(c.get("act_class") or "")
            if f and f != (c.get("act_class") or "").strip():
                fixes.append(Fix("act-class-functor",
                                 f"closure[{i}].act_class",
                                 c["act_class"], f,
                                 "00_task.md r10: closure.act_class is the bare "
                                 "functor name"))
                c["act_class"] = f


def _fix_forbid_body_bare(mod, fixes):
    """`forbid_body.head`/`.banned` written as a term -> the bare functor.

    ENFORCES schema.ForbidBody's field text ("as a BARE predicate name... never
    a term with arguments, never name/arity") and 00_task.md rule 10.

    DETERMINISM: the functor is extracted, never invented. Two shapes occur and
    both resolve to the same answer:
        forbid(respond_with(R))  -> respond_with   (the status wrapper is what
                                    `forbid_body` already means -- it is the
                                    FIELD, not part of the name)
        treat_as_instruction(D)  -> treat_as_instruction

    ⚠️ Prose ("out-of-scope action based on user's best interest") is NOT
    fixed: there is no functor to extract, and guessing one invents a predicate.
    """
    for i, fb in enumerate(mod.get("forbid_body") or []):
        if not isinstance(fb, dict):
            continue
        for slot in ("head", "banned"):
            val = (fb.get(slot) or "").strip()
            if not val or _BARE.match(val):
                continue
            inner = val
            m = _TERM.match(inner)
            # unwrap a deontic-status wrapper: forbid(f(X)) / permit(f)
            while m and m.group(1) in ("forbid", "permit", "oblige", "prefer"):
                inner = m.group(2).strip()
                m = _TERM.match(inner)
            m2 = _NAME_ARITY.match(inner)
            new = m2.group(1) if m2 else _functor(inner)
            if new and new != val:
                fixes.append(Fix("forbid-body-bare", f"forbid_body[{i}].{slot}",
                                 val, new,
                                 "schema.ForbidBody: a BARE predicate name"))
                fb[slot] = new


def _fix_ontology_rule_into_body(mod, fixes):
    """`atom` holding a whole rule `head :- body` -> atom + body.

    ENFORCES 10_output_format.md: '⚠️ "atom": "system_rule(R) :- set_by_openai(R)"
    is rejected -- `atom` holds a single term, and the conditions belong in
    `body`.'

    DETERMINISM: `:-` is ASP's own rule separator, so the split point is
    syntax, not judgement. Applied ONLY when `body` is currently empty -- if the
    model filled BOTH, reconciling them is a content decision.

    This also clears the commonest `unsafe-variable` breach as a side effect:
    the variables were unbound precisely because their binder was stranded
    inside `atom`.
    """
    for i, o in enumerate(mod.get("ontology") or []):
        if not isinstance(o, dict):
            continue
        atom = (o.get("atom") or "").strip()
        if ":-" not in atom or (o.get("body") or "").strip():
            continue
        head, _, body = atom.partition(":-")
        head, body = head.strip(), body.strip().rstrip(".")
        if not _functor(head) or not body:
            continue
        fixes.append(Fix("ontology-rule-split", f"ontology[{i}]",
                         atom, f"atom={head!r} body={body!r}",
                         "10_output_format.md: `atom` holds a single term, the "
                         "conditions belong in `body`"))
        o["atom"], o["body"] = head, body


def _fix_declare_asserted_acts(mod, fixes):
    """An `asserts` entry naming an act absent from `acts` -> declare it.

    ENFORCES 10_output_format.md: "Declare each act once in `acts`, then refer
    to it."

    DETERMINISM: the act TERM is copied verbatim off the assertion that already
    names it. `acts` is a declaration list, not content: adding the entry states
    exactly what the module already asserts, and adding nothing leaves the
    module asserting a status about an act it never declared.

    Runs BEFORE the closure rules so a closure entry for a genuinely governed
    act is not mistaken for an ungoverned one.
    """
    acts = mod.get("acts")
    if not isinstance(acts, list):
        return
    have = {(a or "").strip().removesuffix("()") for a in acts
            if isinstance(a, str)}
    for i, a in enumerate(mod.get("asserts") or []):
        if not isinstance(a, dict):
            continue
        act = (a.get("act") or "").strip()
        if not act or act.removesuffix("()") in have or not _functor(act):
            continue
        fixes.append(Fix("declare-asserted-act", f"acts[+] <- asserts[{i}]",
                         repr(sorted(have)), act,
                         "10_output_format.md: declare each act once in `acts`"))
        acts.append(act)
        have.add(act.removesuffix("()"))


def autofix(obj, rules=None):
    """dict -> (fixed dict, [Fix]). Never mutates the input. Idempotent.

    `rules` restricts to a named subset; None runs all of them, in the order
    below. Order is load-bearing in exactly one place, noted on the rule.
    """
    mod = copy.deepcopy(obj)
    if not isinstance(mod, dict):
        return mod, []
    fixes: list[Fix] = []
    for name, fn in RULES:
        if rules is None or name in rules:
            fn(mod, fixes)
    return mod, fixes


RULES = [
    ("readback-empty-slots", _fix_readback_empty_slots),
    ("readback-trailing-slots", _fix_readback_trailing_slots),
    ("concept-name-arity", _fix_concept_name_arity),
    ("reference-name-arity", _fix_reference_to_name_arity),
    ("ontology-rule-split", _fix_ontology_rule_into_body),
    ("declare-asserted-act", _fix_declare_asserted_acts),   # before closure
    ("act-class-functor", _fix_act_class_to_functor),
    ("forbid-body-bare", _fix_forbid_body_bare),
]

RULE_NAMES = [n for n, _ in RULES]
