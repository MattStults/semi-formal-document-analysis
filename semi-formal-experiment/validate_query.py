"""Panel-blind validation of the QUERY-SIDE behaviour file (review F4).

WHY A NEW MODULE. CYCLE5_DESIGN.md housed the patients-field license check in
validate_behaviours.py — a module that opens the reference file, which is
FORBIDDEN territory for anything the query path depends on (review F4). This
module reads ONLY behaviours_query.json (slug/name/definition — the file
whose split from the reference exists precisely so this is checkable) and is
registered in test_no_reference_leak.py's QUERY_MODULES, scanned forever.

THE ANCHOR CHECK. A `patients` list on a query-side behaviour entry is the
document-anchored declaration patient pricing (patient.py) reads — BY EXPLICIT
CALLER OPT-IN ONLY; nothing loads it silently. It is REFUSED, loudly and by
name, unless:

  * every entry is a member of grammar.PRINCIPALS, and
  * every entry is ANCHORED in that behaviour's own name+definition text:
    its readable surface form, or an enumerated synonym from SURFACE_FORMS,
    appears there (word-bounded, case-insensitive).

The declaration is authored by us and licensed by the query file's OWN PROSE
— never by a panel number, and never by mechanical extraction (a silent
extraction failure would be a silently disabled pricing channel, the
dead-channel failure mode this repo has hit twice; a declared field with a
mechanical anchor check keeps the declaration loud and the license
checkable).

THE SYNONYM TABLE is written against the REAL definition strings shipped in
behaviours_query.json (e.g. harm-avoidance says "third parties" and "those
outside the conversation"; helpfulness says "the users and developers it
works with") — it enumerates surface forms, it does not paraphrase. Growing
it is a reviewed vocabulary change, not a convenience edit: every added form
widens what a declaration can be licensed by.

An EMPTY or ABSENT list is valid and means patient pricing is DISABLED for
that behaviour (bit-identical scores — patient.py's I1 invariant). Absent is
absent; it is never defaulted.

Definition-editing is gameable inside a declared diff (smuggle an anchor
word into the definition, then "anchor" anything): that attack is closed by
the definition-freeze gate (review F5) in test_validate_query.py, which pins
name+definition to their cycle-4-closure bytes with `patients` as the only
permitted delta.
"""
from __future__ import annotations

import json
import os
import re

import grammar

HERE = os.path.dirname(os.path.abspath(__file__))

#: The query-side behaviour file — the ONLY artifact this module reads.
QUERIES = os.path.join(HERE, "behaviours_query.json")

#: principal -> lowercase surface forms that anchor it in behaviour prose.
#: Written against the REAL shipped definition strings (module docstring);
#: the readable form (underscores -> spaces) plus its plural, and the one
#: definitional periphrasis the harm definition actually uses. Matching is
#: word-bounded, so none of these can fire from inside another word.
SURFACE_FORMS = {
    "third_party": ("third party", "third parties",
                    "those outside the conversation"),
    "user": ("user", "users"),
    "developer": ("developer", "developers"),
    "operator": ("operator", "operators"),
    "system": ("system", "systems"),
    "model": ("model", "models"),
    "root": ("root",),
}


def _anchored(form: str, text: str) -> bool:
    """Word-bounded, case-insensitive presence of `form` in `text` — a
    substring inside another word ('user' in 'perusers') is no anchor."""
    return re.search(r"(?<![a-z])" + re.escape(form) + r"(?![a-z])",
                     text) is not None


def _load(source):
    if source is None:
        source = QUERIES
    if isinstance(source, str):
        with open(source) as f:
            return json.load(f)
    return source


def check_patients(source=None) -> dict:
    """`{slug: tuple(declared patients)}` for every behaviour in the
    query-side file — or ValueError, naming the behaviour and the reason, on
    the first unlicensable declaration. An absent or empty `patients` field
    yields () (pricing disabled; always valid). Order and first-occurrence
    de-duplication of the declared list are preserved."""
    doc = _load(source)
    out = {}
    for b in doc.get("behaviours", []):
        if not isinstance(b, dict):
            continue
        slug = b.get("slug") or b.get("id") or ""
        raw = b.get("patients")
        if raw is None:
            out[slug] = ()
            continue
        if not isinstance(raw, list) or not all(
                isinstance(p, str) for p in raw):
            raise ValueError(
                f"behaviour {slug!r}: `patients` must be a list of "
                f"principal strings, got {raw!r}")
        text = f"{b.get('name') or ''} {b.get('definition') or ''}".lower()
        seen = []
        for p in raw:
            if p not in grammar.PRINCIPALS:
                raise ValueError(
                    f"behaviour {slug!r}: declared patient {p!r} is not a "
                    f"grammar principal ({', '.join(grammar.PRINCIPALS)})")
            forms = SURFACE_FORMS.get(p, (p.replace("_", " "),))
            if not any(_anchored(f, text) for f in forms):
                raise ValueError(
                    f"behaviour {slug!r} declares patient {p!r}, but none "
                    f"of its surface forms ({', '.join(forms)}) appears in "
                    "the behaviour's own name+definition text — the "
                    "declaration is unlicensed (CYCLE5_REVIEW.md F4: the "
                    "license is the query file's own prose, never a panel "
                    "number)")
            if p not in seen:
                seen.append(p)
        out[slug] = tuple(seen)
    return out


def load_query_patients(source=None) -> dict:
    """`{slug: frozenset(patients)}` for behaviours declaring a NON-EMPTY
    patients list, validated through check_patients. This is the explicit
    opt-in loader a caller hands to PatientIndex(query_patients=...) — no
    index constructor calls it, ever (patient.py's DEFAULT-ON prohibition)."""
    return {slug: frozenset(pats)
            for slug, pats in check_patients(source).items() if pats}
