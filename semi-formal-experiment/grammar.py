"""THE NOTATION — single source of truth for what an atom name may encode.

WHY THIS MODULE EXISTS
----------------------
The read-back measured that the atom index is an adequate INDEX and a poor
REPRESENTATION: 91 of 125 clauses are identifiable from their atoms while a
reader of those atoms would not know what the clause requires
(`sufficient` = 0.16). The missing content is concentrated in the three things
the grammar has no slot for — the obligated party (23% of missing phrases), the
deontic force (15%) and the triggering condition (10%). Conditionals sit at
1/25 sufficient because "if X then Y", "Y unless X" and "never Y" all render as
the same unordered set {X, Y}.

That is a VALIDITY problem, not a performance problem. The capacity bound says
representation was never the relevance ceiling (534 equivalence classes over
589 passages bound any function of the atom set at +0.972 against a +0.555
bar), and a supervised readout of identical atoms reaches +0.591. So expect
little or no MCC movement from this. A representation of a normative document
that cannot distinguish "must" from "must not" is not a semi-formal ontology
whatever it retrieves, and the conflict half of the project cannot proceed
without it.

THE THREE FEATURES, AND WHERE EACH LIVES
----------------------------------------
1. POLARITY / DEONTIC FORCE — a reserved prefix on the NAME.
       `mustnot_disclose_reasoning`
2. THE ORDERED PRINCIPAL CHAIN — after a double underscore, agent first.
       `mustnot_disclose_reasoning__model_user`
   Order is the relation: `..__model_user` and `..__user_model` are different
   atoms, exactly as `vocab_key` already refuses to merge
   `model_defers_to_operator` with `operator_defers_to_model`.
3. CONDITION vs CONSEQUENT — ONE NEW FIELD, `role`.

WHY `role` IS A NEW FIELD AND NOT THE SPAN GROUPING
---------------------------------------------------
`readback.render` already groups atoms by `span_id` and prints the partition,
so the span grouping was the obvious candidate. It is the wrong one, for three
independent reasons, any one of which is sufficient:

  * The grouping is UNLABELLED and UNORDERED. `render` prints "Group 1" and
    "Group 2" and says in terms that the order carries no meaning. "if X then
    Y" and "Y unless X" produce the same two groups in the same order — which
    is precisely the failure being fixed.
  * `span_id` is PROVENANCE, chosen under a different instruction ("the span
    that ESTABLISHES the concept, not merely one that mentions it"). Making it
    carry role too would put the extractor in a conflict: to mark a defeater it
    would have to cite a span it was told not to cite. Provenance is verified
    by lookup against the clause's own span table, so corrupting it is
    expensive and invisible.
  * Many conditionals put trigger and consequent in ONE span ("Never do X").
    A span-derived role cannot represent that clause at all, and it is the
    modal case in the 1/25 stratum.

So: one new optional field, one closed four-member vocabulary, no nesting, no
references between atoms. Deliberately the smallest thing that separates a
trigger from what it triggers and from what defeats it.

BACKWARD COMPATIBILITY IS THE POINT OF THE PREFIX RESERVATION
--------------------------------------------------------------
Verified over `annotations_b8.json` + `behavior_atoms_b8.json`: 0 shipped names
begin with a reserved prefix, 0 contain `__`, and `stem_of` is therefore the
IDENTITY on all of them. `role` is optional and absent everywhere, and
`role_of` reports None rather than defaulting — a default would make every
legacy atom assert a structure nobody wrote. An existing artifact decoded
through this module is bit-identical to the same artifact decoded without it.

RE-DECLARATION, NOT IMPORT
--------------------------
`ladder.py` and `structural.py` each already carry a hand copy of the constants
and the parse, pinned equal to each other by a test. They are NOT edited to
import this module: `ladder` pulls in the provider layer and `structural` may
not reference it, and rewiring either is out of scope for a notation change.
`test_grammar.py` pins both copies to this one, so the three are now checked
pairwise in two places rather than one.
"""
from __future__ import annotations

# --------------------------------------------------------------------------
# THE CONSTANTS. Byte-equal to ladder.py's and structural.py's copies.

#: Reserved. No shipped atom name begins with one — verified over the real
#: vocabulary in `test_grammar.py` — so the parse is unambiguous and the
#: decode of a legacy artifact is a no-op. (`no_` was a candidate and was
#: dropped: `no_authority_content` and `no_moral_ambiguity` already exist.)
POLARITY_PREFIXES = ("must_", "mustnot_", "should_", "shouldnot_", "may_")

#: `__` separates the stem from the ordered principal chain. No shipped name
#: contains it, so it is free to mean this.
PRINCIPAL_SEP = "__"

#: Longest-first, because `third_party` contains the separator character and a
#: left-to-right split on "_" would tear it in half.
#:
#: `root` REPLACES `platform`, and the replacement is a correction, not a
#: synonym. The Model Spec's own CHANGELOG: "Renames the top authority level
#: from Platform to Root, and specifies that Root > System … Previously, the
#: Model Spec stated that Platform principles and System messages had the same
#: authority." So `platform` was not merely the old word for `root`; it named a
#: level that was DEFINED AS EQUAL to `system`, and the rename introduced a
#: distinction our vocabulary predated. Keeping both would have offered the
#: extractor a token for a level the current document does not have.
#:
#: The two are separated by exactly what can override them:
#:   root   — comes ONLY from the Model Spec; no system message, developer or
#:            user can override it; identical across all model instances.
#:   system — set by OpenAI but transmissible and overridable THROUGH system
#:            messages, so it can vary by serving surface and by user; still
#:            above developer and user.
#:
#: Safe to rename outright: 0 of the 330 shipped atom names carry a principal
#: chain at all (the chain is a prospective feature, unused by any existing
#: artifact), so `stem_of` remains the identity and no join key moves.
#:
#: NOT an authority ORDERING. This tuple is ordered for parse correctness —
#: longest-first — and nothing more. Which level outranks which is a fact about
#: a particular document, not about the notation, and it belongs in extracted
#: clauses (m0040 states it) rather than hardcoded here, or the grammar could
#: not be pointed at the Anthropic constitution without lying about it. The
#: grammar can now NAME the level; it still cannot express the ORDER, because
#: that needs a relation between atoms. See LADDER_PLAN.md.
PRINCIPALS = ("third_party", "developer", "operator", "system", "model",
              "root", "user")

#: The deontic force each prefix denotes, in the words a reader needs. The
#: read-back renders these, so "must" and "mustnot" MUST NOT decode alike —
#: that identity is the defect this whole change exists to remove.
POLARITY_ENGLISH = {
    "must": "REQUIRED — the passage says to do this",
    "mustnot": "FORBIDDEN — the passage says not to do this",
    "should": "recommended — the passage prefers this, without requiring it",
    "shouldnot": "discouraged — the passage prefers not, without forbidding",
    "may": "permitted — the passage allows this without calling for it",
}

# --------------------------------------------------------------------------
# THE ROLE FIELD

#: Closed. Four members, chosen to be the smallest set that can tell "if X then
#: Y" from "Y unless X" from "never Y":
#:   condition  — the trigger; the passage applies only when this holds
#:   exception  — a defeater; where this holds the passage does NOT apply
#:   consequent — what the passage calls for once it applies
#:   topic      — none of the above: what the passage is about
#: `topic` is explicit rather than implied so that "this atom is background"
#: and "this annotator did not use the field" stay distinguishable. Absent is
#: absent; it never becomes `topic` by default.
ROLES = ("condition", "exception", "consequent", "topic")
ROLE_FIELD = "role"

ROLE_ENGLISH = {
    "condition": "a TRIGGER: the passage applies only when this holds",
    "exception": "an EXCEPTION: where this holds, the passage does not apply",
    "consequent": "what the passage CALLS FOR once it applies",
    "topic": "background: what the passage is about, outside any trigger",
}

#: Every field this grammar adds to the shipped atom shape. Named so a caller
#: can price them, strip them, or assert their absence without re-deriving the
#: list from prose.
NOTATION_FIELDS = (ROLE_FIELD,)


# --------------------------------------------------------------------------
# parse — TOTAL, and never a guess

def _unparseable(name, why):
    """The ONLY shape an errored parse may take.

    ⚠️ DISCREPANCY WITH THE TWO HAND COPIES, DELIBERATE AND REPORTED.
    `ladder.parse_name("must_")` and `structural.parse_atom_name("must_")`
    return `polarity="must"` ALONGSIDE their error — they set the field before
    discovering there is no stem left and return without clearing it. Every
    caller in the repo checks `error` first, so nothing is wrong today, but the
    task's requirement is "unparseable yields error, NEVER a plausible parse",
    and a half-filled dict beside an error is exactly the shape that becomes a
    plausible parse the first time someone reads the field without the guard.
    So this module clears the derived fields, and `test_grammar.py` pins the
    two copies only where they are meaningful: error-ness always, the parsed
    fields whenever the parse succeeded.
    """
    return {"polarity": None, "stem": name, "principals": [], "error": why}


def parse_name(name):
    """`{polarity, stem, principals, error}` for one atom name.

    Total: an unparseable name yields an `error` string and NO partial parse,
    because a convention that silently half-parses is worse than none — the
    render would then assert a deontic force nobody wrote, and the join would
    key on a stem nobody chose.
    """
    out = {"polarity": None, "stem": name, "principals": [], "error": None}
    if not isinstance(name, str) or not name:
        return _unparseable(name, "not a name")
    parts = name.split(PRINCIPAL_SEP)
    if len(parts) > 2:
        return _unparseable(name,
                            f"more than one {PRINCIPAL_SEP!r} in {name!r}")
    head = parts[0]
    for p in POLARITY_PREFIXES:
        if head.startswith(p):
            out["polarity"] = p[:-1]
            head = head[len(p):]
            break
    if not head:
        return _unparseable(name, f"{name!r} is a polarity prefix with no stem")
    out["stem"] = head
    if len(parts) == 2:
        chain, rest = [], parts[1]
        while rest:
            for pr in PRINCIPALS:
                if rest == pr or rest.startswith(pr + "_"):
                    chain.append(pr)
                    rest = rest[len(pr) + 1:]
                    break
            else:
                return _unparseable(
                    name, f"{rest!r} in {name!r} is not one of "
                          f"{', '.join(PRINCIPALS)}")
        if not chain:
            return _unparseable(name, f"{name!r} has an empty principal chain")
        out["principals"] = chain
    return out


def format_name(stem, polarity=None, principals=()):
    """The inverse, so the convention has exactly one spelling."""
    head = (f"{polarity}_" if polarity else "") + stem
    if principals:
        head += PRINCIPAL_SEP + "_".join(principals)
    return head


def stem_of(name) -> str:
    """The name with the notation stripped — the key every join runs on.

    THE IDENTITY on every shipped atom name, which is what makes every existing
    artifact keep working: the second lookup asks for the same string as the
    first. An unparseable name returns itself rather than a guessed stem,
    because rewriting the join key on a name we could not read is the one
    failure that would be invisible downstream.
    """
    p = parse_name(name)
    return name if p["error"] else p["stem"]


def valid_role(role) -> bool:
    return isinstance(role, str) and role.strip().lower() in ROLES


def role_of(atom):
    """The atom's declared role, or None.

    None means "nothing recorded" and is returned for an absent field, an empty
    field AND an unrecognised value. Coercing an unknown value to a role would
    let a typo become an assertion about the document's conditional structure.
    """
    if not isinstance(atom, dict):
        return None
    r = atom.get(ROLE_FIELD)
    if not isinstance(r, str):
        return None
    r = r.strip().lower()
    return r if r in ROLES else None


# --------------------------------------------------------------------------
# decode — the English the read-back reads

def describe(atom):
    """One line of English for everything the NOTATION holds, or "".

    Empty on an atom in the shipped shape. That is the backward-compatibility
    contract in one function: a legacy artifact renders byte-identically,
    because there is nothing to say about it.
    """
    if not isinstance(atom, dict):
        return ""
    bits = []
    p = parse_name(atom.get("name"))
    if not p["error"]:
        if p["polarity"]:
            bits.append(f"FORCE: {POLARITY_ENGLISH[p['polarity']]}")
        chain = list(p["principals"])
        if chain:
            who = _readable(chain[0])
            if len(chain) == 1:
                bits.append(f"WHO: {who} is the party concerned")
            else:
                rest = ", then ".join(_readable(c) for c in chain[1:])
                bits.append(f"WHO: {who} acts, upon {rest}")
    role = role_of(atom)
    if role:
        bits.append(f"ROLE: {ROLE_ENGLISH[role]}")
    return ". ".join(bits) + "." if bits else ""


def _readable(principal):
    return principal.replace("_", " ")


def records(atoms):
    """Which of the three features this annotation actually uses.

    `{polarity, principals, condition}` — booleans. The read-back's closing
    paragraph is composed from this, so it denies holding only what it does not
    hold. `condition` covers the whole role field, since a role is what makes
    the trigger/consequent structure readable at all.
    """
    got = {"polarity": False, "principals": False, "condition": False}
    for a in atoms or []:
        if not isinstance(a, dict):
            continue
        p = parse_name(a.get("name"))
        if not p["error"]:
            got["polarity"] = got["polarity"] or bool(p["polarity"])
            got["principals"] = got["principals"] or bool(p["principals"])
        got["condition"] = got["condition"] or role_of(a) is not None
    return got


def carries_notation(atoms) -> bool:
    """Does this annotation use ANY of the three features? False on every
    shipped artifact, which is what keeps the legacy render unchanged."""
    return any(records(atoms).values())
