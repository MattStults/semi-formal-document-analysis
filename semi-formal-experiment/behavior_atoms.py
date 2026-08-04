"""Behaviour -> atoms: the QUERY side of the ontology, built once per behaviour.

WHY THIS MODULE EXISTS
----------------------
annotate.py annotates 593 clauses into an atom index, and relevance.py scores a
behaviour against it with 0.6 of its weight on shared (name, kind) atoms. But
the query side of that comparison did not exist: behaviour atoms were read from
`behaviours.json`, whose entries carry only category/coverage/definition/id/
name/slug. `raw.get("atoms")` was therefore ALWAYS empty, the atom channel was
always multiplied by zero, and the ontology tier could only ever contribute
clause-side bag-of-words expansion. The tool looked like an ontology and scored
like a lexical baseline.

This module produces the missing side and caches it to `behavior_atoms.json`,
which relevance.load_behaviour_atoms reads offline.

THE CACHE INVARIANT (contract invariant #8) — ONE CALL PER BEHAVIOUR, EVER
--------------------------------------------------------------------------
The whole value proposition is "annotate once, query many, instantly". A model
call at query time would just BE the baseline this project exists to beat. So
the model is called once per BEHAVIOUR (three behaviours = three calls, ever),
the result is written to disk, and every relevance query afterwards is pure
arithmetic over that file. relevance.py must never import this module; there is
a test asserting it does not.

THE HARD PART: VOCABULARY ALIGNMENT
-----------------------------------
Atoms coined independently from a one-sentence definition do not match atoms
coined from 593 clauses. `helpful_response` and `assistant_helpfulness` share
nothing under exact (name, kind) matching, so free generation leaves the channel
dead in a subtler and more flattering way than an empty set: the artifact looks
full and matches nothing.

So this is a CONSTRAINED SELECTION problem, not a generation problem. Four
defences, in order of how much they are trusted:

  1. SELECT, DON'T COIN. The model is shown the clause-side vocabulary — every
     atom name, its kind, its gloss, how many clauses carry it — and picks names
     off that list. This is the same trick as the span-id selection in
     annotate.py: the model chooses an identifier and never authors the thing
     that has to match. Matching then works by construction.
  2. GLOSSES FROM THE INDEX. A selected atom's gloss is copied from the clause
     side, never from the model, so the two sides cannot drift apart in wording.
  3. MECHANICAL ALIASING. A name coined anyway is run through
     annotate.vocab_key: `ambiguous_user_query` resolves onto the existing
     `user_request_ambiguous` instead of splitting the concept. Kind-scoped, so
     `refuse_request` (act) never merges into `request_refused` (situation).
  4. MEASURE IT. The artifact reports `in_vocabulary_rate` — the fraction of
     emitted atoms that a clause could actually carry — plus the fraction of
     the vocabulary that was never shown. An atom that was not shown can never
     be selected, and that is a silent recall cap unless it is a number.

The vocabulary is small enough (~600-1000 atoms, ~20k tokens with glosses) to
show ENTIRELY in one request at $0.20/Mtok, so `unshown_fraction` is normally
0.0. `--max-vocab` prefilters by lexical similarity if it ever is not, and the
artifact says so.

DEGRADATION
-----------
With no annotations artifact there is nothing to select from, so the module
falls back to FREE GENERATION and says so extremely loudly — a RuntimeWarning,
a line on stderr, a string in the artifact's `_warnings`, and
`vocabulary_aligned: false` in provenance. Alignment is not guaranteed in that
mode and the numbers it produces should not be attributed to the ontology.

CONDUCT
-------
conflict_output.py distinguishes a behaviour's abstract `definition` from the
concrete `conduct` a panel actually judges. A vignette yields far more specific
atoms than a construct, so conduct sentences are accepted as additional input
and folded in; each atom records whether it came from the definition, the
conduct, or both, and the artifact keeps the conduct text alongside.

THE RUNG-1.5 NOTATION ON THE QUERY SIDE (`--notation`)
------------------------------------------------------
`structural.py` ships four operators that read a polarity prefix and an ordered
principal chain off an atom name. Three of them can read a clause-side rung-1.5
pass. `polarity_consistent` cannot, and says so: *"it is INERT until the query
side carries polarity too: an unpolarised query atom can contradict nothing.
Making it live needs a rung-1.5 pass over the BEHAVIOUR atoms
(`behavior_atoms.py`), which is not this module's file."* This is that file.

THE PROBLEM. This module is CONSTRAINED SELECTION, and that is the whole reason
the two sides of the ontology share a vocabulary. But the shipped clause
vocabulary is UNPOLARISED — there is no polarised name on the list to select.
"Select, but polarised" therefore has no referent, and the obvious repairs are
both wrong:

  * FREE GENERATION of notated names. Rejected. It is the exact failure this
    module exists to prevent — the artifact looks full and matches nothing —
    and it would make the query's stem set a function of the model's phrasing
    rather than of the document.
  * SELECT FROM A POLARISED CLAUSE VOCABULARY once the clause side is
    re-annotated. Rejected, twice over: it makes the query side hostage to a
    paid pass that has not run, and a re-annotation's vocabulary is a DRAW —
    `HANDOFF.md` measures 21% vocabulary overlap between two runs of the SAME
    model — so the query would be bound to one draw of the clause side.

THE RESOLUTION: DECORATE A SELECTED STEM. The model still picks a name off the
closed list, exactly as before. Separately it picks, from two CLOSED ENUMS
owned by `grammar.py`, a polarity (5 values + null) and an ORDERED principal
chain (7 values, at most `MAX_PRINCIPALS` long). The emitted name is then
CONSTRUCTED BY THIS MODULE with `grammar.format_name` and verified by round
trip through `grammar.parse_name`; a model-written notated name is not a
vocabulary entry and is rejected as one. So the query atom is a point in

    V (361 stems)  x  polarity (6)  x  ordered chains (259)

— a product of closed sets, enumerable, with the model choosing a row and never
authoring the string that has to match. That is the same discipline as before,
extended to two more dimensions, and it is the resolution the ladder already
chose for the clause side (`LADDER_PLAN.md`: *"Resolved by decorating a closed
stem (`[polarity_]stem__principals`)"*). Using the same one on both sides is
what keeps them in one vocabulary.

WHY THE ORDER IS LOAD-BEARING. `mustnot_cause_harm__model_third_party` is a
third party who is HARMED; `mustnot_cause_harm__third_party_model` is a third
party who HARMS. A behaviour called harm-avoidance-to-third-parties is about
the first. Any implementation that sorts, de-duplicates or set-ifies the chain
collapses them, and `annotate.vocab_key` already refuses to make exactly that
merge (`model_defers_to_operator` vs `operator_defers_to_model`).

WHAT THE DECORATION CAN AND CANNOT DO. The STEM SET IS UNCHANGED, so every
consumer that joins on the stem sees the same query it saw before
(`grammar.stem_of` is the identity on all 361 shipped names, and
`structural._evidence` falls back to a stem lookup). The decoration can
therefore only ever REMOVE a match, never add one — it is defeater-shaped,
which is what the four notation operators are. `stem_view()` is the bridge for
consumers that join on the name with NO stem fallback (`relevance.py` is one),
and `--emit-stem-view` writes it.

NOT CARRIED: `grammar.ROLES`. The role field distinguishes a clause's trigger
from its consequent. A behaviour definition is not a conditional and nothing in
the query path reads the field, so writing it here would be free generation with
no consumer.

INVARIANT 9. The polarity and the chain are chosen from the behaviour's own
definition and conduct — the same inputs the unpolarised pass already takes.
No panel judgement reaches the prompt, and the format demonstrations in
`behavior_atoms_notation_prompt.md` are synthetic and asserted not to be
substrings of either spec.

    .venv/bin/python behavior_atoms.py --print-prompt
    .venv/bin/python behavior_atoms.py --dry-run --notation      # measured cost
    .venv/bin/python behavior_atoms.py --spread behavior_atoms_v2_draw*.json
    .venv/bin/python behavior_atoms.py --live --provider luna --annotations annotations.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import warnings

import annotate
import extract_section as ex

# --------------------------------------------------------------------------
# constants

PROMPT_TEMPLATE_PATH = "behavior_atoms_prompt.md"
OUT_PATH = "behavior_atoms.json"
ANNOTATIONS_PATH = "annotations.json"

#: The panel's behaviour file. Its entries have no `atoms` key — that absence
#: is the whole reason this module exists.
#: Vendored into this repo; was a relative path into a third checkout.
BEHAVIOURS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data",
    "behaviours.json")

#: annotate.py's closed taxonomy, re-exported so a drift shows up as an import
#: error rather than as two modules quietly disagreeing.
ATOM_KINDS = annotate.ATOM_KINDS
IDENT_RE = annotate.IDENT_RE

MIN_WEIGHT, DEFAULT_WEIGHT, MAX_WEIGHT = 1, 2, 3

#: Coined atoms match nothing in the current index, so they are a report of a
#: gap, not a way to phrase the query. Capped hard — but only when there IS a
#: vocabulary; in free-generation mode the cap would zero the run.
MAX_NEW_ATOMS = 6

#: Whole-vocabulary display is affordable (~20k input tokens ≈ $0.004/call);
#: this bound only exists so the prompt cannot grow without limit.
DEFAULT_MAX_VOCAB = 1500

DEFAULT_MAX_TOKENS = 3000

SOURCES = ("definition", "conduct", "both")

_HERE = os.path.dirname(os.path.abspath(__file__))


def _p(path):
    return path if os.path.isabs(path) else os.path.join(_HERE, path)


# --------------------------------------------------------------------------
# the notation — IMPORTED from grammar.py, never re-declared
#
# `structural.py` re-declares the prefix list deliberately (it may not import
# the provider layer) and pins it with a test. This module has no such excuse:
# a second copy is how two modules quietly disagree about what a name means,
# and the query side is the one place where disagreeing with the clause side
# costs the whole join. `test_the_notation_is_imported_from_grammar_and_never
# _re_declared` reads this file's source and asserts the constants are absent.

NOTATION_PROMPT_PATH = "behavior_atoms_notation_prompt.md"

#: Polarity is deontic force ON AN ACT and principals are the parties TO an
#: act. A polarised `value` is a category error, so the decoration is confined
#: to this slot. Declared, not fitted: nothing was measured to choose it.
NOTATION_KINDS = ("act",)

#: Chain-length ceiling. Three, because the ladder's own reading of the chain
#: is "who acts first, then who is acted upon, then any third party" — the
#: longest chain that reading can name. Declared before any run; no score was
#: consulted. A longer chain is refused, not truncated: truncating would drop
#: the last principal silently, and the last principal is a patient.
MAX_PRINCIPALS = 3

#: Fields the notation adds to the shipped atom shape. A caller can strip them
#: (`stem_view`) or assert their absence without re-deriving the list.
NOTATION_ATOM_FIELDS = ("stem", "polarity", "principals")

SHIPPED_ATOM_FIELDS = ("name", "kind", "gloss", "weight", "source", "new")


class NotationUnavailable(RuntimeError):
    """`grammar.py` is not importable and a polarised run was asked for.

    An explicit refusal, never a silent downgrade to an unpolarised run: that
    would produce an artifact that looks right, carries none of the signal, and
    reports a null for the operator it was built to make live.
    """


def grammar_module(strict=True):
    """The notation module. Imported; this module defines no copy of it."""
    try:
        import grammar
    except ImportError as e:                      # pragma: no cover - env only
        if strict:
            raise NotationUnavailable(
                "the polarised query pass needs grammar.py (the notation "
                f"contract) and it could not be imported: {e}")
        return None
    return grammar


def polarities(g=None):
    """The reserved polarity VALUES — the prefixes without their underscore."""
    g = g or grammar_module()
    return tuple(p[:-1] for p in g.POLARITY_PREFIXES)


def principal_names(g=None):
    g = g or grammar_module()
    return tuple(g.PRINCIPALS)


def decorate(stem, polarity=None, principals=(), g=None):
    """`(name, error)` — the notated name, CONSTRUCTED and then VERIFIED.

    The construction is only trusted because it is round-tripped through the
    peer module's own parser: if `parse_name` does not return exactly the
    polarity, stem and chain that went in, the decoration is refused and the
    BARE selected name comes back. Degrading to the bare stem is deliberate —
    dropping the atom instead would be a silent recall cap, and this module's
    rule is that a defect is counted, never paid for in recall.
    """
    g = g or grammar_module()
    if not isinstance(stem, str) or not stem:
        return stem, "stem is not a name"
    chain = list(principals or ())
    if polarity is not None and polarity not in polarities(g):
        return stem, f"{polarity!r} is not a reserved polarity"
    if len(chain) > MAX_PRINCIPALS:
        return stem, f"chain of {len(chain)} exceeds MAX_PRINCIPALS"
    if any(not isinstance(p, str) or p not in g.PRINCIPALS for p in chain):
        return stem, "chain contains a party outside the closed list"
    if len(set(chain)) != len(chain):
        # `model_model` parses, and means nothing: an actor who is also the
        # patient is not a relation. A name that parses but denotes nothing is
        # the worst outcome, because everything downstream believes it.
        return stem, "chain repeats a party"
    name = g.format_name(stem, polarity, chain)
    p = g.parse_name(name)
    if (p["error"] or p["polarity"] != polarity or p["stem"] != stem
            or list(p["principals"]) != chain or g.stem_of(name) != stem):
        return stem, f"{name!r} does not round-trip: {p['error'] or p}"
    return name, None


def actor_of(atom, g=None):
    """Who acts, per the ORDERED chain, or None."""
    return (_chain_of(atom, g) or (None,))[0]


def patients_of(atom, g=None):
    """Who is acted upon, in order. Empty when the chain names only an actor."""
    return tuple(_chain_of(atom, g)[1:])


def _chain_of(atom, g=None):
    if isinstance(atom, dict) and isinstance(atom.get("principals"), list):
        return [p for p in atom["principals"] if isinstance(p, str)]
    g = g or grammar_module()
    name = atom.get("name") if isinstance(atom, dict) else atom
    p = g.parse_name(name)
    return [] if p["error"] else list(p["principals"])


def role_signature(atoms, g=None):
    """`{actors, patients}` for a whole query, ORDER PRESERVED.

    Deliberately two ordered tuples and not one set. `structural.query_roles`
    flattens the chain into a set, which is correct for `role_aligned` and
    throws away exactly what `patient_aligned` exists to read; this keeps the
    distinction available on the query side so that operator can be made to
    read it without re-deriving anything.
    """
    g = g or grammar_module()
    actors, patients = [], []
    for a in atoms or []:
        chain = _chain_of(a, g)
        if not chain:
            continue
        if chain[0] not in actors:
            actors.append(chain[0])
        for p in chain[1:]:
            if p not in patients:
                patients.append(p)
    return {"actors": tuple(actors), "patients": tuple(patients)}


def _zero_notation_stats():
    return {"decorated": 0, "bad_polarity": 0, "bad_principal": 0,
            "non_act_decoration": 0, "round_trip_failed": 0,
            "undecorated_act": 0, "conflicting_polarity": 0,
            "polarity_counts": {}, "chain_counts": {}}


# --------------------------------------------------------------------------
# inputs

def load_behaviours(path=BEHAVIOURS_PATH, slugs=None):
    """The panel's behaviours, in file order. Never raises on a missing file."""
    try:
        with open(_p(path), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    rows = data.get("behaviours") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        return []
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        slug = r.get("slug") or r.get("id")
        if not slug or (slugs and slug not in slugs):
            continue
        out.append({"slug": str(slug), "name": r.get("name") or "",
                    "definition": r.get("definition") or "",
                    "category": r.get("category") or ""})
    return out


def load_conduct(source=None):
    """`{slug: [sentence, ...]}` from a path or a parsed object.

    Accepts a bare string per slug (the common case: one vignette), a list, or
    a conflict-panel-shaped entry carrying a `conduct` key.
    """
    if source is None:
        return {}
    if isinstance(source, str):
        try:
            with open(_p(source), encoding="utf-8") as f:
                source = json.load(f)
        except (OSError, ValueError):
            return {}
    if isinstance(source, dict) and isinstance(source.get("behaviours"), list):
        source = {b.get("slug"): b for b in source["behaviours"]
                  if isinstance(b, dict) and b.get("slug")}
    if not isinstance(source, dict):
        return {}
    out = {}
    for slug, val in source.items():
        if isinstance(val, dict):
            val = val.get("conduct")
        if isinstance(val, str):
            val = [val]
        if isinstance(val, list):
            items = [s.strip() for s in val if isinstance(s, str) and s.strip()]
            if items:
                out[str(slug)] = items
    return out


def load_vocabulary(source=None):
    """`[{name, kind, gloss, n_clauses}]` from annotate.py's artifact.

    Returns [] — never raises — when the artifact is absent, which is what puts
    the run into the loud free-generation fallback. Prefers the artifact's
    `vocabulary` index; falls back to counting the flat `atoms` list, because
    an artifact assembled by hand or by an older build may carry only that.
    """
    if source is None:
        source = ANNOTATIONS_PATH
    if isinstance(source, str):
        try:
            with open(_p(source), encoding="utf-8") as f:
                source = json.load(f)
        except (OSError, ValueError):
            return []
    if not isinstance(source, dict):
        return []

    out = []
    index = source.get("vocabulary")
    if isinstance(index, dict) and index:
        for name, rec in index.items():
            if not isinstance(name, str) or not isinstance(rec, dict):
                continue
            if rec.get("kind") not in ATOM_KINDS:
                continue
            out.append({"name": name, "kind": rec["kind"],
                        "gloss": rec.get("gloss") or "",
                        "n_clauses": int(rec.get("n_clauses") or 0)})
        return out

    atoms = source.get("atoms")
    if not isinstance(atoms, list):
        return []
    seen = {}
    for a in atoms:
        if not isinstance(a, dict):
            continue
        name, kind = a.get("name"), a.get("kind")
        if not isinstance(name, str) or kind not in ATOM_KINDS:
            continue
        rec = seen.setdefault(name, {"name": name, "kind": kind,
                                     "gloss": a.get("gloss") or "",
                                     "n_clauses": 0, "_clauses": set()})
        cid = a.get("clause_id")
        if cid:
            rec["_clauses"].add(cid)
        if not rec["gloss"]:
            rec["gloss"] = a.get("gloss") or ""
    for rec in seen.values():
        rec["n_clauses"] = len(rec.pop("_clauses"))
        out.append(rec)
    return out


# --------------------------------------------------------------------------
# what the model is shown

def behaviour_text(behaviour, conduct=()):
    return " ".join([behaviour.get("name") or "", behaviour.get("definition") or "",
                     " ".join(conduct or ())])


def prefilter_vocabulary(vocab, text, max_vocab=DEFAULT_MAX_VOCAB):
    """`(shown, meta)` — the vocabulary, truncated to `max_vocab` by lexical
    similarity to the behaviour text if and only if it does not fit.

    An atom that is never shown can never be selected, so `unshown_fraction` is
    a recall cap and belongs in the artifact rather than in a comment. Ranking
    is by stemmed token overlap between the behaviour text and the atom's
    name+gloss (relevance.py's own stemmer, so the two tiers agree on what a
    word is), length-normalised so a wordy gloss is not favoured.
    """
    vocab = list(vocab)
    total = len(vocab)
    meta = {"vocabulary_total": total, "vocabulary_shown": total,
            "unshown_fraction": 0.0, "prefiltered": False}
    if total <= max_vocab or max_vocab <= 0:
        return vocab, meta

    import relevance
    q = relevance.tokens(text)

    def score(a):
        t = relevance.tokens(f"{a['name']} {a.get('gloss', '')}")
        if not t:
            return 0.0
        return len(q & t) / (len(t) ** 0.5)

    ranked = sorted(vocab, key=lambda a: (-score(a), a["name"]))[:max_vocab]
    meta.update(vocabulary_shown=len(ranked), prefiltered=True,
                unshown_fraction=round(1 - len(ranked) / total, 4) if total else 0.0)
    return ranked, meta


VOCAB_HEADER = (
    "===== CLAUSE VOCABULARY ({n} atoms) =====\n"
    "These are the atoms the specification document is ALREADY indexed with,\n"
    "each with the kind it is filed under, its gloss, and how many clauses\n"
    "carry it. SELECT from this list, copying names exactly. A name you invent\n"
    "matches no clause at all.\n\n")

FREE_GENERATION_HEADER = (
    "===== NO CLAUSE VOCABULARY AVAILABLE =====\n"
    "The document's atom index could not be loaded, so there is nothing to\n"
    "select from. Coin atoms directly, using the four kinds and the naming\n"
    "rules. Names should be the most ORDINARY, obvious phrasing of each\n"
    "concept, since they must later match names coined independently.\n\n")


def render_vocabulary(vocab):
    """The vocabulary grouped by kind, commonest atoms last within a kind.

    Glosses are always shown: deciding "is this atom what my behaviour is
    about?" cannot be made from a name alone, and that judgement is exactly
    what produces a private variant when the right name was right there.
    """
    if not vocab:
        return FREE_GENERATION_HEADER
    out = [VOCAB_HEADER.format(n=len(vocab))]
    for kind in ATOM_KINDS:
        got = [a for a in vocab if a["kind"] == kind]
        got.sort(key=lambda a: (-int(a.get("n_clauses") or 0), a["name"]))
        out.append(f"{kind.upper()} atoms ({len(got)}):")
        if not got:
            out.append("  (none)")
        else:
            out += [f"  - {a['name']} [{a.get('n_clauses', 0)} clauses]: "
                    f"{a.get('gloss', '')}" for a in got]
        out.append("")
    return "\n".join(out) + "\n"


def render_conduct(conduct):
    if not conduct:
        return ""
    lines = ["", "===== CONDUCT (concrete described behaviour) =====",
             "These are concrete episodes of the behaviour, not the abstract",
             "definition. They are the richer source of situation and act",
             "atoms: prefer what they DEPICT over what the definition asserts.",
             "Mark atoms drawn from them \"conduct\" (or \"both\").", ""]
    lines += [f"  {i}. {s}" for i, s in enumerate(conduct, start=1)]
    return "\n".join(lines) + "\n"


MODE_SELECT = ("The vocabulary below is CLOSED. Copy names from it. You may "
               "coin at most {max_new} atoms it genuinely lacks, in the "
               "separate \"new\" list.")
MODE_FREE = ("NO vocabulary is available, so \"selected\" must be empty and "
             "every atom goes in \"new\" with a gloss. Nothing constrains your "
             "names to match the document's, so choose the most ordinary "
             "phrasing of each concept.")


def load_template(path=PROMPT_TEMPLATE_PATH):
    return ex.load_template(_p(path))


def render_notation_block(g=None, path=NOTATION_PROMPT_PATH):
    """`(system_tail, user_tail)` — the notation instructions, from their own
    file so the unnotated prompt is byte-identical and this block diffs alone.

    The two closed enums are substituted FROM `grammar.py`, so a change there
    reaches the prompt without anybody remembering to edit prose.
    """
    g = g or grammar_module()
    sys_tail, user_tail = ex.load_template(_p(path))
    subs = {"{{POLARITIES}}": ", ".join(polarities(g)),
            "{{PRINCIPALS}}": ", ".join(principal_names(g)),
            "{{MAX_PRINCIPALS}}": str(MAX_PRINCIPALS)}
    for k, v in subs.items():
        sys_tail = sys_tail.replace(k, v)
        user_tail = user_tail.replace(k, v)
    return sys_tail, user_tail


def notation_demonstrations(path=NOTATION_PROMPT_PATH):
    """The synthetic atom names demonstrated in the notation prompt.

    Returned so a test can assert none of them is a string of either spec: a
    demonstration lifted from the document under evaluation is a channel from
    somebody who has read the panel, and is a blocking review finding.
    """
    sys_tail, _ = ex.load_template(_p(path))
    out = []
    for line in sys_tail.splitlines():
        line = line.strip()
        if line.startswith('{"name": "'):
            out.append(line.split('"')[3])
    return tuple(out)


def render_prompt(behaviour, vocab, conduct=(), max_new=MAX_NEW_ATOMS,
                  notation=False):
    """`(system, user)` for ONE behaviour.

    Note what this takes and what it does not: exactly one behaviour, and no
    clause text. Rendering it per query is what the cache invariant forbids;
    rendering several behaviours at once would make one truncation cost all of
    them and would stop the artifact being rebuildable a behaviour at a time.

    `notation=True` APPENDS the rung-1.5 block rather than substituting into
    the base template, so the unnotated prompt is bit-identical to the one that
    produced every shipped artifact.
    """
    system, user = load_template()
    lines = [f"slug: {behaviour.get('slug', '')}",
             f"name: {behaviour.get('name', '')}",
             f"definition: {behaviour.get('definition', '')}"]
    if behaviour.get("category"):
        lines.append(f"category: {behaviour['category']}")
    user = (user
            .replace("{{MODE_LINE}}", MODE_SELECT.format(max_new=max_new)
                     if vocab else MODE_FREE)
            .replace("{{BEHAVIOUR}}", "\n".join(lines))
            .replace("{{CONDUCT_BLOCK}}", render_conduct(conduct))
            .replace("{{VOCABULARY_BLOCK}}", render_vocabulary(vocab)))
    system = system.replace("{{MAX_NEW}}", str(max_new))
    if notation:
        sys_tail, user_tail = render_notation_block()
        system = system + "\n" + sys_tail
        user = user + "\n" + user_tail
    return system, user


# --------------------------------------------------------------------------
# verification — reject and COUNT, never silently drop

REJECTIONS = ("malformed_response", "malformed_atom", "bad_name", "bad_kind",
              "unknown_atom", "excess_new", "duplicate")


def _zero_rejections():
    return {r: 0 for r in REJECTIONS}


def _weight(raw):
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return DEFAULT_WEIGHT
    return max(MIN_WEIGHT, min(MAX_WEIGHT, int(round(raw))))


def _source(raw, has_conduct):
    if not has_conduct:
        return "definition"
    return raw if raw in SOURCES else "definition"


def verify_selection(obj, vocab, fail, max_new=MAX_NEW_ATOMS, has_conduct=False,
                     notation=False):
    """`(atoms, stats)` from one parsed response. Never raises.

    Selected atoms are checked against the vocabulary by name; the KIND and the
    GLOSS are then taken from the vocabulary, not from the model, because those
    are what the clause side will be matched on and the model is not the
    authority on them. A near-duplicate name is resolved through
    annotate.vocab_key before being called new.

    `notation=True` additionally reads two CLOSED-ENUM fields off each `act`
    atom and constructs the notated name from them. The name the model wrote is
    never the notated name: a pre-notated string is not a vocabulary entry and
    falls out as `unknown_atom`, which is what keeps this selection rather than
    generation. A refused polarity or chain costs the DECORATION, never the
    atom — every such event is counted in `stats["notation"]`.
    """
    by_name = {a["name"]: a for a in vocab if isinstance(a, dict) and a.get("name")}
    canonical = {}
    for a in by_name.values():
        canonical.setdefault((a["kind"], annotate.vocab_key(a["name"])), a["name"])
    any_kind = {}
    for a in by_name.values():
        any_kind.setdefault(annotate.vocab_key(a["name"]), a["name"])

    stats = {"atoms_seen": 0, "atoms_accepted": 0, "atoms_rejected": 0,
             "atoms_selected": 0, "atoms_new": 0, "atoms_aliased": 0,
             "kind_snapped": 0, "missing_gloss": 0, "atoms_from_conduct": 0,
             "rejections": _zero_rejections()}
    g = grammar_module() if notation else None
    if notation:
        stats["notation"] = _zero_notation_stats()
    polarity_by_stem = {}
    out, seen = [], set()

    def reject(reason, detail, stage="atom"):
        stats["atoms_rejected"] += 1
        stats["rejections"][reason] = stats["rejections"].get(reason, 0) + 1
        fail(stage, reason, detail)

    if not isinstance(obj, dict):
        return out, stats
    sel = obj.get("selected") if isinstance(obj.get("selected"), list) else []
    new = obj.get("new") if isinstance(obj.get("new"), list) else []
    if not sel and not new and obj:
        stats["rejections"]["malformed_response"] += 1
        fail("response", "response carries neither \"selected\" nor \"new\"",
             {"keys": sorted(k for k in obj if isinstance(k, str))[:10]})

    # In free-generation mode there is nothing to select from, so the cap that
    # protects a real vocabulary from being diluted would zero the run instead.
    cap = max_new if vocab else len(new)

    for is_new, group in ((False, sel), (True, new)):
        for raw in group:
            stats["atoms_seen"] += 1
            if not isinstance(raw, dict):
                reject("malformed_atom", {"new": is_new})
                continue
            name = raw.get("name")
            if not isinstance(name, str) or not IDENT_RE.match(name.strip()):
                reject("bad_name", {"name": str(name), "new": is_new})
                continue
            name = name.strip()
            kind = raw.get("kind")
            if kind not in ATOM_KINDS:
                reject("bad_kind", {"name": name, "kind": str(kind)})
                continue

            known = by_name.get(name)
            aliased = False
            if known is None:
                canon = (canonical.get((kind, annotate.vocab_key(name)))
                         or any_kind.get(annotate.vocab_key(name)))
                if canon:
                    # A private variant of a name the document already uses.
                    # Resolve it rather than emit an atom no clause can carry.
                    known, aliased = by_name[canon], True
                    fail("vocabulary",
                         "behaviour-side name resolved onto an existing "
                         "clause-side atom",
                         {"from": name, "to": canon, "kind": kind})
                    name = canon

            if known is None and not is_new:
                # Selection was supposed to be from a closed list; a name that
                # is neither on it nor a variant of anything on it is a
                # hallucinated selection and matches nothing.
                reject("unknown_atom", {"name": name, "kind": kind})
                continue

            if known is not None:
                kind_out = known["kind"]
                if kind_out != kind:
                    stats["kind_snapped"] += 1
                gloss = known.get("gloss") or ""
                genuinely_new = False
            else:
                kind_out = kind
                gloss = raw.get("gloss")
                gloss = gloss.strip() if isinstance(gloss, str) else ""
                genuinely_new = True

            if genuinely_new and stats["atoms_new"] >= cap:
                reject("excess_new", {"name": name, "cap": cap})
                continue

            emitted, polarity, chain = name, None, []
            if notation:
                emitted, polarity, chain = _decorate_selection(
                    name, kind_out, raw, g, stats["notation"], fail)
                prior = polarity_by_stem.get(name)
                if polarity and prior is None:
                    # Only a STATED polarity is remembered: seeding this with
                    # None would make the first unpolarised atom on a stem
                    # suppress every later conflict on it.
                    polarity_by_stem[name] = polarity
                if polarity and prior and prior != polarity:
                    # Two opposed forces on one stem make `polarity_consistent`
                    # unable to exclude anything for that stem. Counted, not
                    # silently resolved: dropping one would be this module
                    # picking which half of the behaviour to believe.
                    stats["notation"]["conflicting_polarity"] += 1
                    fail("notation", "two opposed polarities on one stem",
                         {"stem": name, "first": prior, "second": polarity})

            if emitted in seen:
                reject("duplicate", {"name": emitted})
                continue
            seen.add(emitted)

            if not gloss:
                stats["missing_gloss"] += 1
            src = _source(raw.get("source"), has_conduct)
            if src in ("conduct", "both"):
                stats["atoms_from_conduct"] += 1
            if aliased:
                stats["atoms_aliased"] += 1
            if genuinely_new:
                stats["atoms_new"] += 1
            else:
                stats["atoms_selected"] += 1
            stats["atoms_accepted"] += 1
            atom = {"name": emitted, "kind": kind_out, "gloss": gloss,
                    "weight": _weight(raw.get("weight")), "source": src,
                    "new": genuinely_new}
            if notation:
                # `stem` is what every existing consumer joins on, carried
                # explicitly so recovering it needs no parser at all.
                atom.update(stem=name, polarity=polarity, principals=chain)
            out.append(atom)
    return out, stats


def _decorate_selection(name, kind, raw, g, nstats, fail):
    """`(emitted_name, polarity, chain)` for ONE selected atom.

    Everything here refuses rather than repairs. A polarity outside the
    reserved five, a party outside the closed seven, a chain over the declared
    ceiling or one that repeats a party: the decoration is dropped and counted,
    and the bare vocabulary name survives. The alternative — coercing the
    nearest legal value — would put an assertion about the document's deontic
    structure into the query that nobody wrote.
    """
    pol = raw.get("polarity")
    chain = raw.get("principals")
    chain = [p for p in chain if isinstance(p, str)] if isinstance(chain, list) else []
    if isinstance(pol, str):
        pol = pol.strip().lower() or None
    elif pol is not None:
        pol = None

    if kind not in NOTATION_KINDS:
        if pol or chain:
            nstats["non_act_decoration"] += 1
            fail("notation", "polarity/principals on a non-act atom",
                 {"name": name, "kind": kind, "polarity": pol,
                  "principals": chain})
        return name, None, []

    if pol is not None and pol not in polarities(g):
        nstats["bad_polarity"] += 1
        fail("notation", "polarity outside the reserved set",
             {"name": name, "polarity": pol})
        pol = None
    if chain and (len(chain) > MAX_PRINCIPALS
                  or len(set(chain)) != len(chain)
                  or any(p not in g.PRINCIPALS for p in chain)):
        nstats["bad_principal"] += 1
        fail("notation", "principal chain outside the closed list, over "
                         f"MAX_PRINCIPALS={MAX_PRINCIPALS}, or repeating",
             {"name": name, "principals": chain})
        chain = []

    emitted, err = decorate(name, pol, chain, g=g)
    if err:
        nstats["round_trip_failed"] += 1
        fail("notation", f"decoration refused: {err}",
             {"name": name, "polarity": pol, "principals": chain})
        return name, None, []

    if pol or chain:
        nstats["decorated"] += 1
        if pol:
            nstats["polarity_counts"][pol] = \
                nstats["polarity_counts"].get(pol, 0) + 1
        if chain:
            key = ">".join(chain)
            nstats["chain_counts"][key] = nstats["chain_counts"].get(key, 0) + 1
    if not chain:
        nstats["undecorated_act"] += 1
    return emitted, pol, chain


def atoms_for_behaviour(response, behaviour, vocab, fail, conduct=(),
                        max_new=MAX_NEW_ATOMS, notation=False):
    """One response -> that behaviour's atoms. Never raises.

    Truncation and malformed JSON are different defects with different fixes
    (fewer atoms requested vs. a tighter format instruction), so they are
    reported separately and a truncated reply is never allowed to read as "the
    model selected nothing".
    """
    env = ex.as_envelope(response)
    truncated = ex.is_truncated(env)
    obj, err = ex.parse_response(env["text"])

    if truncated:
        usage = env.get("usage") or {}
        fail("truncated_output",
             "model hit its output cap before finishing the JSON",
             {"behaviour": behaviour.get("slug"),
              "finish_reason": env.get("finish_reason"),
              "completion_tokens": usage.get("completion_tokens"),
              "content_chars": len(env["text"] or "")})
    elif err:
        fail("response", err,
             {"behaviour": behaviour.get("slug"),
              "head": (env["text"] or "")[:300]
              if isinstance(env["text"], str) else None})
    if err:
        obj = {}

    atoms, stats = verify_selection(obj, vocab, fail, max_new=max_new,
                                    has_conduct=bool(conduct),
                                    notation=notation)
    stats["truncated"] = 1 if truncated else 0
    stats["parsed"] = 0 if err else 1
    stats["calls"] = 1
    return {"atoms": atoms, "stats": stats, "truncated": truncated,
            "parsed": err is None, "envelope": env}


# --------------------------------------------------------------------------
# the run

FREE_GENERATION_WARNING = (
    "FREE GENERATION MODE: no clause vocabulary was loaded (looked for {path}), "
    "so behaviour atoms are coined from scratch. VOCABULARY ALIGNMENT IS NOT "
    "GUARANTEED — a coined name like `assistant_helpfulness` matches no clause "
    "annotated `helpful_response`, and the atom channel can be dead while the "
    "artifact looks full. Run annotate.py first.")

ALIGNMENT_WARNING = (
    "ONLY {rate:.0%} of behaviour atoms ({hit}/{total}) exist in the clause "
    "vocabulary. The rest can never match any clause, so the atom channel is "
    "carrying {rate:.0%} of the weight it appears to carry.")

MIN_IN_VOCAB_RATE = 0.5


def _add_stats(into, more):
    """Recursive, because the notation block nests one level deeper.

    The flat version summed `dict + int` the moment `polarity_counts` appeared
    inside `notation` and raised on the first polarised run.
    """
    for k, v in more.items():
        if isinstance(v, dict):
            _add_stats(into.setdefault(k, {}), v)
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            into[k] = into.get(k, 0) + v
    return into


def run(client, behaviours, vocab, conduct=None, out=None, out_dir=".",
        log_path=None, model="", provider=None, seed=0,
        max_new=MAX_NEW_ATOMS, max_vocab=DEFAULT_MAX_VOCAB,
        max_tokens=DEFAULT_MAX_TOKENS, annotations_path=ANNOTATIONS_PATH,
        return_path=False, notation=False):
    """One pass over the behaviours: ONE call each, then write the cache.

    `notation=False` is the shipped default and reproduces the shipped artifact
    shape exactly — not because the polarised pass is suspected of being worse,
    but because NOTHING HAS MEASURED IT, and this project's signature failure is
    a default flipped on an unmeasured (or panel-measured) preference.
    """
    behaviours = [b for b in behaviours if isinstance(b, dict)]
    conduct = dict(conduct or {})
    vocab = list(vocab or [])
    vocab_names = {a["name"] for a in vocab if isinstance(a, dict) and a.get("name")}
    if notation:
        grammar_module()                       # refuse early, not per behaviour

    warns = []
    if not vocab:
        msg = FREE_GENERATION_WARNING.format(path=annotations_path)
        warns.append(msg)
        warnings.warn(msg, RuntimeWarning, stacklevel=2)
        print(f"WARNING: {msg}", file=sys.stderr)

    first = behaviours[0] if behaviours else {"slug": ""}
    _, first_user = render_prompt(first, vocab,
                                  conduct.get(first.get("slug"), []), max_new,
                                  notation=notation)
    run_id = ex.make_run_id(model, seed, first_user)
    log_path = log_path or os.path.join(out_dir, "behavior_atoms_failures.jsonl")
    fail = ex.FailureLog(log_path, run_id=run_id, model=model)

    art, stats = {}, {}
    any_response, n_calls = False, 0
    atoms_total = atoms_in_vocab = 0
    unshown_max, shown_min = 0.0, None

    for b in behaviours:
        slug = b.get("slug") or b.get("id") or ""
        cond = conduct.get(slug, [])
        shown, meta = prefilter_vocabulary(
            vocab, behaviour_text(b, cond), max_vocab)
        unshown_max = max(unshown_max, meta["unshown_fraction"])
        shown_min = (meta["vocabulary_shown"] if shown_min is None
                     else min(shown_min, meta["vocabulary_shown"]))
        system, user = render_prompt(b, shown, cond, max_new, notation=notation)
        try:
            resp = ex.call_client(client, system, user)
            n_calls += 1
        except Exception as e:                      # noqa: BLE001 — never raise
            fail("call", f"provider call failed: {type(e).__name__}: {e}",
                 {"behaviour": slug})
            resp = None
        env = ex.as_envelope(resp)
        if env["text"] is not None:
            any_response = True

        part = atoms_for_behaviour(resp, b, shown, fail, conduct=cond,
                                   max_new=max_new, notation=notation)
        atoms = part["atoms"]
        # Always measured on the STEM. `in_vocabulary_rate` answers "could a
        # clause carry this?", and the join every consumer runs is stem-aware;
        # measuring the decorated name would report a 0% alignment collapse
        # caused by the notation rather than by the selection.
        in_vocab = sum(1 for a in atoms
                       if (a.get("stem") or a["name"]) in vocab_names)
        atoms_total += len(atoms)
        atoms_in_vocab += in_vocab
        _add_stats(stats, part["stats"])

        counts = dict(part["stats"])
        counts.pop("rejections", None)
        counts["atoms_total"] = len(atoms)
        counts["atoms_in_clause_vocabulary"] = in_vocab
        art[slug] = {
            "atoms": atoms,
            "source": "definition+conduct" if cond else "definition",
            "name": b.get("name") or "",
            "definition": b.get("definition") or "",
            "conduct": list(cond),
            "counts": counts,
            "rejections": part["stats"].get("rejections", _zero_rejections()),
            "vocabulary_shown": meta,
            "truncated": bool(part["truncated"]),
        }

    rate = round(atoms_in_vocab / atoms_total, 4) if atoms_total else 0.0
    if vocab and atoms_total and rate < MIN_IN_VOCAB_RATE:
        w = ALIGNMENT_WARNING.format(rate=rate, hit=atoms_in_vocab,
                                     total=atoms_total)
        warns.append(w)
        fail("alignment", w, {"in_vocabulary_rate": rate})
    trunc = stats.get("truncated", 0)
    if trunc:
        warns.append(f"{trunc} of {len(behaviours)} behaviours hit the output "
                     f"cap — their atoms are lost. Re-run those slugs.")

    counts = {k: v for k, v in stats.items() if not isinstance(v, dict)}
    counts["atoms_total"] = atoms_total
    counts["failures"] = fail.count()
    counts["call_failures"] = fail.count("call")
    art["provenance"] = {
        "model": model,
        "provider": provider,
        "run_id": run_id,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_behaviours": len(behaviours),
        "n_calls": n_calls,
        "calls_per_behaviour": round(n_calls / len(behaviours), 2) if behaviours else 0,
        "seed": seed,
        "max_new": max_new,
        "max_tokens": max_tokens,
        "annotations": annotations_path,
        "vocabulary_aligned": bool(vocab),
        "counts": counts,
        "rejections": stats.get("rejections", _zero_rejections()),
        "alignment": {
            "in_vocabulary_rate": rate,
            "atoms_in_clause_vocabulary": atoms_in_vocab,
            "atoms_total": atoms_total,
            "vocabulary_total": len(vocab),
            "vocabulary_shown_min": shown_min if shown_min is not None else 0,
            "unshown_fraction_max": round(unshown_max, 4),
        },
        "dry_run": not any_response and fail.count("call") == 0,
        "notation": _notation_provenance(notation, stats, art),
    }
    art["_warnings"] = warns

    os.makedirs(out_dir, exist_ok=True)
    if out is None:
        out = os.path.join(out_dir, OUT_PATH)
    try:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(art, f, indent=1, ensure_ascii=False)
    except OSError as e:
        fail("write", f"could not write artifact: {e}", {"path": out})
        out = None
    return (art, out) if return_path else art


def _notation_provenance(enabled, stats, art):
    """What the notation did, as numbers, in the artifact.

    `stem_join_preserved` is the backward-compatibility claim, CHECKED rather
    than asserted: every emitted name must strip back to the stem that was
    selected, or the join every consumer runs has been broken by this pass.
    """
    out = {"enabled": bool(enabled)}
    if not enabled:
        return out
    g = grammar_module()
    n = stats.get("notation") or _zero_notation_stats()
    atoms = [a for slug, e in art.items()
             if not slug.startswith("_") and slug != "provenance"
             for a in (e.get("atoms") or [])]
    bad = [a["name"] for a in atoms
           if g.stem_of(a["name"]) != (a.get("stem") or a["name"])]
    total = len(atoms)
    acts = [a for a in atoms if a.get("kind") in NOTATION_KINDS]
    out.update(
        grammar="grammar.py",
        max_principals=MAX_PRINCIPALS,
        kinds=list(NOTATION_KINDS),
        atoms_total=total,
        act_atoms=len(acts),
        decorated=n["decorated"],
        decorated_fraction=round(n["decorated"] / total, 4) if total else 0.0,
        polarised_act_fraction=(round(sum(1 for a in acts if a.get("polarity"))
                                      / len(acts), 4) if acts else 0.0),
        chained_act_fraction=(round(sum(1 for a in acts if a.get("principals"))
                                    / len(acts), 4) if acts else 0.0),
        polarity_counts=dict(n["polarity_counts"]),
        chain_counts=dict(n["chain_counts"]),
        refused={"bad_polarity": n["bad_polarity"],
                 "bad_principal": n["bad_principal"],
                 "non_act_decoration": n["non_act_decoration"],
                 "round_trip_failed": n["round_trip_failed"],
                 "conflicting_polarity": n["conflicting_polarity"]},
        stem_join_preserved=not bad,
        stem_join_broken_on=bad[:10],
    )
    return out


def stem_view(source):
    """The undecorated view of a polarised artifact — the compatibility bridge.

    `relevance.py` joins query atoms to clause atoms by EXACT name with NO stem
    fallback, so handing it a polarised artifact would silently zero the atom
    channel: 0.6 of the weight, multiplied by nothing, with the artifact
    looking full. That is the precise failure this module was built to fix, and
    it would be reintroduced by the fix to a different one.

    Returns a new object; the input is not mutated.
    """
    if isinstance(source, str):
        with open(_p(source), encoding="utf-8") as f:
            source = json.load(f)
    if not isinstance(source, dict):
        return {}
    out = {}
    for slug, entry in source.items():
        if slug == "provenance" and isinstance(entry, dict):
            prov = dict(entry)
            prov["notation"] = {"enabled": False,
                                "stem_view_of": entry.get("run_id"),
                                "was_notated": bool(
                                    (entry.get("notation") or {}).get("enabled"))}
            out[slug] = prov
            continue
        if slug.startswith("_") or not isinstance(entry, dict):
            out[slug] = entry
            continue
        e = dict(entry)
        atoms = []
        for a in (entry.get("atoms") or []):
            if not isinstance(a, dict):
                continue
            b = {k: v for k, v in a.items() if k not in NOTATION_ATOM_FIELDS}
            b["name"] = a.get("stem") or a.get("name")
            atoms.append(b)
        e["atoms"] = atoms
        out[slug] = e
    return out


# --------------------------------------------------------------------------
# DRAWS — one draw is not a result
#
# The five shipped v2 draws exist because vocabulary selection is stochastic:
# the model is sampled, and two runs of the SAME model over the SAME vocabulary
# share only part of their selection. Anything built here has to be runnable as
# n seeded draws and reported with its spread, or a single number will be read
# as a result.

def run_draws(client, behaviours, vocab, draws=5, out_dir=".", out=None,
              **kw):
    """`[path, ...]` — `draws` seeded passes, each to its own artifact."""
    pattern = out or os.path.join(out_dir, "behavior_atoms_draw{seed}.json")
    paths = []
    for seed in range(int(draws)):
        target = pattern.format(seed=seed) if "{seed}" in pattern else pattern
        _, path = run(client, behaviours, vocab, out=target, out_dir=out_dir,
                      seed=seed, return_path=True, **kw)
        paths.append(path)
    return paths


def _selected(art):
    """`{slug: {stem, ...}}` — the STEM set, which is what the join uses."""
    out = {}
    for slug, entry in (art or {}).items():
        if slug.startswith("_") or slug == "provenance" or not isinstance(entry, dict):
            continue
        out[slug] = {(a.get("stem") or a.get("name"))
                     for a in (entry.get("atoms") or [])
                     if isinstance(a, dict) and (a.get("stem") or a.get("name"))}
    return out


def spread(paths):
    """Draw-to-draw agreement, per behaviour and overall.

    Reported on STEMS, so a polarised run and an unpolarised one are comparable
    — and, when the runs are polarised, on the decorated names too, so the
    extra variance the notation introduces is separated from the variance the
    selection already had rather than being blamed on it.
    """
    arts = []
    for p in paths:
        if isinstance(p, str):
            try:
                with open(_p(p), encoding="utf-8") as f:
                    arts.append(json.load(f))
            except (OSError, ValueError):
                continue
        elif isinstance(p, dict):
            arts.append(p)
    stems = [_selected(a) for a in arts]

    def _names(art):
        out = {}
        for slug, e in art.items():
            if slug.startswith("_") or slug == "provenance" or not isinstance(e, dict):
                continue
            out[slug] = {a["name"] for a in (e.get("atoms") or [])
                         if isinstance(a, dict) and a.get("name")}
        return out

    names = [_names(a) for a in arts]
    slugs = sorted(set().union(*[set(s) for s in stems]) if stems else [])

    def jac(sets):
        pairs = [(sets[i], sets[j]) for i in range(len(sets))
                 for j in range(i + 1, len(sets))]
        vals = [len(a & b) / len(a | b) for a, b in pairs if (a | b)]
        return sum(vals) / len(vals) if vals else 0.0

    rows, all_j, all_jn = {}, [], []
    for slug in slugs:
        got = [s[slug] for s in stems if slug in s]
        gotn = [n[slug] for n in names if slug in n]
        counts = [len(x) for x in got]
        core = set.intersection(*got) if got else set()
        union = set.union(*got) if got else set()
        j, jn = jac(got), jac(gotn)
        rows[slug] = {
            "n_draws": len(got),
            "atoms_mean": round(sum(counts) / len(counts), 2) if counts else 0,
            "atoms_min": min(counts) if counts else 0,
            "atoms_max": max(counts) if counts else 0,
            "mean_jaccard": round(j, 4),
            "mean_jaccard_notated": round(jn, 4),
            "core": len(core), "union": len(union),
        }
        all_j.append(j)
        all_jn.append(jn)
    return {"n_draws": len(arts), "paths": list(paths), "behaviours": rows,
            "mean_jaccard": round(sum(all_j) / len(all_j), 4) if all_j else 0.0,
            "mean_jaccard_notated": (round(sum(all_jn) / len(all_jn), 4)
                                     if all_jn else 0.0)}


# --------------------------------------------------------------------------
# COST — measured tokens, never chars/4
#
# This project has mis-priced the SAME operation three times and every error
# pointed toward spending (`LADDER_PLAN.md`). There is no tokenizer in this
# environment, so the conversion comes from this repo's OWN logged calls: the
# five v2 draws are 45 logged calls whose prompts are deterministic and fully
# reconstructible offline from the artifacts themselves.

USAGE_PATH = os.path.join(_HERE, "usage.jsonl")

CALIBRATION_ARTIFACTS = tuple(f"behavior_atoms_v2_draw{i}.json"
                              for i in range(5))


def _usage_rows(path=USAGE_PATH):
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        pass
    except OSError:
        return []
    return out


def _artifact_behaviours(art):
    """The behaviour dicts a run was given, RECOVERED FROM ITS OWN ARTIFACT.

    Name, definition and conduct are all stored per slug, in call order, so the
    prompts of a past run are reconstructible without knowing which behaviours
    file it was pointed at — which provenance does not record.
    """
    out = []
    for slug, e in art.items():
        if slug.startswith("_") or slug == "provenance" or not isinstance(e, dict):
            continue
        out.append(({"slug": slug, "name": e.get("name") or "",
                     "definition": e.get("definition") or "", "category": ""},
                    list(e.get("conduct") or [])))
    return out


def calibrate_chars_per_token(usage_path=USAGE_PATH,
                              artifacts=CALIBRATION_ARTIFACTS,
                              annotations=None):
    """Characters of prompt per input token, MEASURED on this module's calls.

    Each shipped draw records `created` and `n_calls`; its calls are the last
    `n_calls` rows logged at or before that timestamp. The prompts are rebuilt
    from the artifact's own behaviour entries and paired with those rows IN
    ORDER, which is exact rather than distributional — the artifact stores its
    behaviours in call order.

    Returns `chars_per_token: None` rather than a default when nothing usable
    is on disk. A silent fallback constant is how a cost estimate becomes a
    guess wearing the word "measured".
    """
    rows = sorted(_usage_rows(usage_path), key=lambda r: r.get("ts") or 0)
    ratios, completions, n_calls, models = [], [], 0, set()
    for name in artifacts:
        path = _p(name)
        try:
            with open(path, encoding="utf-8") as f:
                art = json.load(f)
        except (OSError, ValueError):
            continue
        prov = art.get("provenance") or {}
        created = prov.get("created")
        n = int(prov.get("n_calls") or 0)
        if not created or not n:
            continue
        try:
            import datetime
            end = datetime.datetime.fromisoformat(created).timestamp()
        except ValueError:
            continue
        before = [r for r in rows if (r.get("ts") or 0) <= end + 1]
        block = before[-n:]
        if len(block) != n:
            continue
        vocab = load_vocabulary(annotations or prov.get("annotations")
                                or ANNOTATIONS_PATH)
        if not vocab:
            continue
        pairs = _artifact_behaviours(art)
        if len(pairs) != n:
            continue
        for (b, cond), row in zip(pairs, block):
            tok = row.get("prompt_tokens")
            if not tok:
                continue
            system, user = render_prompt(b, vocab, cond,
                                         int(prov.get("max_new") or MAX_NEW_ATOMS))
            ratios.append((len(system) + len(user)) / tok)
            if row.get("completion_tokens"):
                completions.append(int(row["completion_tokens"]))
            models.add(row.get("model"))
            n_calls += 1
    if not ratios:
        return {"chars_per_token": None, "n_calls": 0, "source": usage_path,
                "method": "UNAVAILABLE — no reconstructible logged call",
                "completion": {}}
    ratios.sort()
    completions.sort()

    def q(xs, p):
        return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else None

    return {
        "chars_per_token": round(ratios[len(ratios) // 2], 4),
        "chars_per_token_min": round(ratios[0], 4),
        "chars_per_token_max": round(ratios[-1], 4),
        "n_calls": n_calls,
        "source": usage_path,
        "models": sorted(m for m in models if m),
        "method": "exact pairing: reconstructed prompt chars / logged "
                  "prompt_tokens, per call, over the shipped draws",
        "completion": {"mean": round(sum(completions) / len(completions), 1)
                       if completions else None,
                       "p90": q(completions, 0.9), "max": q(completions, 1.0),
                       "n": len(completions)},
    }


def dry_run_cost(behaviours, vocab, model="gpt-5.6-luna", conduct=None,
                 max_new=MAX_NEW_ATOMS, max_tokens=DEFAULT_MAX_TOKENS,
                 notation=False, draws=1, calibration=None, prices=None):
    """What a live run of THIS configuration would cost. Never a guess.

    Two numbers, both reported, because reasoning is billed as completion and
    scales with the budget it is given:

      usd_likely   completion at the MEASURED mean of this module's own calls
      usd_ceiling  every call running to `--max-tokens`

    The ceiling is the number to approve against. The three mis-pricings in
    this project's history were all "likely" figures quoted as if they bounded
    the bill.
    """
    import spend
    conduct = dict(conduct or {})
    cal = calibration or calibrate_chars_per_token()
    px = prices if prices is not None else spend.prices()
    cpt = cal.get("chars_per_token")
    per_behaviour, chars_total = [], 0
    for b in behaviours:
        system, user = render_prompt(b, vocab, conduct.get(b.get("slug"), []),
                                     max_new, notation=notation)
        chars = len(system) + len(user)
        chars_total += chars
        per_behaviour.append({"slug": b.get("slug"), "chars": chars,
                              "input_tokens": int(round(chars / cpt)) if cpt
                              else None})
    if not cpt:
        return {"measured": False, "reason": cal.get("method"),
                "input_tokens": None, "usd_likely": None, "usd_ceiling": None,
                "calibration": cal, "per_behaviour": per_behaviour}

    out_mean = cal["completion"].get("mean") or max_tokens
    in_tok = sum(r["input_tokens"] for r in per_behaviour) * int(draws)
    likely = ceiling = 0.0
    for r in per_behaviour:
        for _ in range(int(draws)):
            likely += spend.cost_of({"model": model, "provider": model,
                                     "prompt_tokens": r["input_tokens"],
                                     "completion_tokens": int(round(out_mean))},
                                    px) or 0.0
            ceiling += spend.cost_of({"model": model, "provider": model,
                                      "prompt_tokens": r["input_tokens"],
                                      "completion_tokens": int(max_tokens)},
                                     px) or 0.0
    return {
        "measured": True,
        "model": model,
        "notation": bool(notation),
        "draws": int(draws),
        "n_calls": len(per_behaviour) * int(draws),
        "chars": chars_total,
        "input_tokens": in_tok,
        "output_tokens_likely": int(round(out_mean)) * len(per_behaviour) * int(draws),
        "output_tokens_ceiling": int(max_tokens) * len(per_behaviour) * int(draws),
        "usd_likely": round(likely, 4),
        "usd_ceiling": round(ceiling, 4),
        "calibration": cal,
        "per_behaviour": per_behaviour,
    }


# --------------------------------------------------------------------------
# CLI

def estimate_cost(behaviours, vocab, price_per_mtok=None,
                  max_tokens=DEFAULT_MAX_TOKENS):
    """Rough per-run cost. Input dominated by the vocabulary block, which is
    re-sent once per behaviour; output bounded by the token cap."""
    chars = len(render_vocabulary(vocab)) + 4000
    in_tok = chars / 4 * max(1, len(behaviours))
    out_tok = max_tokens * max(1, len(behaviours))
    if not price_per_mtok:
        return {"input_tokens": int(in_tok), "output_tokens": int(out_tok),
                "usd": None}
    p_in, p_out = price_per_mtok[0], price_per_mtok[1]
    return {"input_tokens": int(in_tok), "output_tokens": int(out_tok),
            "usd": round(in_tok / 1e6 * p_in + out_tok / 1e6 * p_out, 4)}


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--behaviours", default=BEHAVIOURS_PATH,
                    help="panel behaviours JSON (the query side's input)")
    ap.add_argument("--annotations", default=ANNOTATIONS_PATH,
                    help="annotate.py artifact supplying the clause vocabulary; "
                         "without it the run falls back to free generation")
    ap.add_argument("--conduct", default=None,
                    help="JSON mapping slug -> conduct sentence(s)")
    ap.add_argument("--slug", action="append", default=None,
                    help="restrict to these behaviours (repeatable); the "
                         "artifact is rebuildable one behaviour at a time")
    ap.add_argument("--provider", default="luna")
    ap.add_argument("--providers", default="providers.json")
    ap.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    ap.add_argument("--max-new", type=int, default=MAX_NEW_ATOMS,
                    help="cap on genuinely new (unmatched) atoms per behaviour")
    ap.add_argument("--max-vocab", type=int, default=DEFAULT_MAX_VOCAB,
                    help="prefilter the vocabulary to N atoms if it is larger; "
                         "the unshown fraction is a recall cap and is reported")
    ap.add_argument("--out", default=None, help="artifact path")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--log", default=None, help="failure JSONL path")
    ap.add_argument("--prompt-log", default="prompt_log")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true", default=True,
                    help="record prompts, make no network call (the default)")
    ap.add_argument("--live", action="store_true",
                    help="make real API calls; without this nothing leaves the "
                         "machine")
    ap.add_argument("--print-prompt", action="store_true",
                    help="print the first behaviour's prompt and exit")
    ap.add_argument("--notation", action="store_true",
                    help="rung-1.5 QUERY pass: act atoms carry a polarity and "
                         "an ordered principal chain, decorating a stem still "
                         "selected from the closed vocabulary. OFF by default "
                         "— nothing has measured it")
    ap.add_argument("--draws", type=int, default=1,
                    help="run N seeded draws (0..N-1) to separate artifacts; "
                         "one draw is not a result")
    ap.add_argument("--emit-stem-view", action="store_true",
                    help="also write the undecorated companion artifact, for "
                         "consumers that join on the name with no stem "
                         "fallback (relevance.py is one)")
    ap.add_argument("--spread", nargs="+", default=None, metavar="ARTIFACT",
                    help="report draw-to-draw agreement over these artifacts "
                         "and exit; makes no call")
    return ap


def _summarize(art, path):
    p = art["provenance"]
    a, c = p["alignment"], p["counts"]
    print(f"[{p['model']} / {p['run_id']}] {p['n_behaviours']} behaviours, "
          f"{p['n_calls']} call(s) — {c.get('atoms_accepted', 0)} atoms accepted, "
          f"{c.get('atoms_rejected', 0)} rejected of {c.get('atoms_seen', 0)} "
          + (f"-> {path}" if path else "-> NOT WRITTEN"))
    print(f"    alignment: {a['atoms_in_clause_vocabulary']}/{a['atoms_total']} "
          f"atoms exist in the clause vocabulary "
          f"({a['in_vocabulary_rate']:.0%}); vocabulary {a['vocabulary_total']} "
          f"atoms, {a['unshown_fraction_max']:.0%} never shown")
    print(f"    selected {c.get('atoms_selected', 0)}, coined "
          f"{c.get('atoms_new', 0)}, aliased {c.get('atoms_aliased', 0)}, "
          f"kind-snapped {c.get('kind_snapped', 0)}")
    for slug, e in art.items():
        if slug.startswith("_") or slug == "provenance":
            continue
        names = ", ".join(f"{x['name']}({x['weight']})" for x in e["atoms"][:6])
        print(f"    {slug}: {len(e['atoms'])} atoms [{e['source']}] {names}"
              + (" ..." if len(e["atoms"]) > 6 else ""))
    rej = {k: n for k, n in p["rejections"].items() if n}
    print(f"    rejections: {rej or 'none'}")
    n = p.get("notation") or {}
    if n.get("enabled"):
        print(f"    notation: {n['decorated']}/{n['atoms_total']} atoms "
              f"decorated; {n['polarised_act_fraction']:.0%} of act atoms "
              f"polarised, {n['chained_act_fraction']:.0%} chained; "
              f"polarity {n['polarity_counts']}; chains {n['chain_counts']}")
        print(f"    notation refused: "
              f"{ {k: v for k, v in n['refused'].items() if v} or 'none'}; "
              f"stem join preserved: {n['stem_join_preserved']}")
        if not n["stem_join_preserved"]:
            print("    !! STEM JOIN BROKEN — every consumer of this artifact "
                  f"loses its atom channel: {n['stem_join_broken_on']}")
    for w in art.get("_warnings", []):
        print("    !! " + w)


def _print_spread(s):
    print(f"SPREAD over {s['n_draws']} draw(s) — mean pairwise Jaccard of the "
          f"selected STEM set: {s['mean_jaccard']:.3f} "
          f"(decorated names: {s['mean_jaccard_notated']:.3f})")
    for slug, r in sorted(s["behaviours"].items()):
        print(f"    {slug:38s} J={r['mean_jaccard']:.3f}  "
              f"atoms {r['atoms_mean']:.1f} [{r['atoms_min']}-{r['atoms_max']}]  "
              f"core {r['core']} / union {r['union']}")
    print("    A single draw is not a result. Quote the spread with the mean.")


def _print_cost(est, label=""):
    if not est.get("measured"):
        print(f"    COST UNMEASURED{label}: {est.get('reason')}")
        print("    Refusing to print a chars/4 guess. Do not approve spend on "
              "this line.")
        return
    cal = est["calibration"]
    print(f"    MEASURED{label}: {est['input_tokens']} input tokens over "
          f"{est['n_calls']} call(s) "
          f"({cal['chars_per_token']:.3f} chars/token, measured on "
          f"{cal['n_calls']} of this module's own logged calls, "
          f"range {cal['chars_per_token_min']:.3f}-{cal['chars_per_token_max']:.3f})")
    print(f"    output: {est['output_tokens_likely']} likely (measured mean "
          f"{cal['completion']['mean']}/call) — {est['output_tokens_ceiling']} "
          f"at the --max-tokens cap")
    print(f"    $ LIKELY {est['usd_likely']:.4f}   $ CEILING "
          f"{est['usd_ceiling']:.4f}   [{est['model']}, via spend.cost_of]")
    print("    Approve against the CEILING. Reasoning is billed as completion "
          "and scales with the budget it is given.")


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.spread:
        _print_spread(spread(args.spread))
        return 0
    behaviours = load_behaviours(args.behaviours, slugs=set(args.slug or ()) or None)
    if not behaviours:
        print(f"no behaviours in {args.behaviours}")
        return 1
    vocab = load_vocabulary(args.annotations)
    conduct = load_conduct(args.conduct)
    print(f"{len(behaviours)} behaviour(s); clause vocabulary: {len(vocab)} atoms "
          f"from {args.annotations}; conduct for {len(conduct)} slug(s)")

    if args.print_prompt:
        b = behaviours[0]
        shown, _ = prefilter_vocabulary(
            vocab, behaviour_text(b, conduct.get(b["slug"], [])), args.max_vocab)
        system, user = render_prompt(b, shown, conduct.get(b["slug"], []),
                                     args.max_new, notation=args.notation)
        print("### SYSTEM\n" + system + "\n\n### USER\n" + user)
        return 0

    cfg = annotate.provider_config(args.provider, args.providers)
    cfg.max_tokens = args.max_tokens
    if args.notation:
        print("    NOTATION ON: act atoms carry a polarity and an ORDERED "
              f"principal chain (<= {MAX_PRINCIPALS}); the stem is still "
              "selected from the closed vocabulary and the name is constructed "
              "here, never copied from the model.")
    est = dry_run_cost(behaviours, vocab, model=cfg.model, conduct=conduct,
                       max_new=args.max_new, max_tokens=args.max_tokens,
                       notation=args.notation, draws=max(1, args.draws))
    _print_cost(est)

    client = annotate.make_annotate_client(cfg, live=args.live,
                                           log_dir=_p(args.prompt_log))
    if not args.live:
        print("DRY RUN (no network). Pass --live to make real calls.")

    kw = dict(conduct=conduct, out_dir=args.out_dir, log_path=args.log,
              model=cfg.model, provider=cfg.name, max_new=args.max_new,
              max_vocab=args.max_vocab, max_tokens=args.max_tokens,
              annotations_path=args.annotations, notation=args.notation)
    if args.draws > 1:
        paths = run_draws(client, behaviours, vocab, draws=args.draws,
                          out=args.out, **kw)
        for p in paths:
            print(f"    draw -> {p}")
        _print_spread(spread(paths))
        if args.emit_stem_view:
            for p in paths:
                _write_stem_view(p)
        return 0

    art, path = run(client, behaviours, vocab, out=args.out, seed=args.seed,
                    return_path=True, **kw)
    _summarize(art, path)
    if args.emit_stem_view and path:
        _write_stem_view(path)
    return 0


def _write_stem_view(path):
    target = path.replace(".json", "_stems.json")
    try:
        with open(target, "w", encoding="utf-8") as f:
            json.dump(stem_view(path), f, indent=1, ensure_ascii=False)
    except OSError as e:
        print(f"    could not write stem view: {e}", file=sys.stderr)
        return None
    print(f"    stem view -> {target} (undecorated; for consumers that join "
          "on the name)")
    return target


if __name__ == "__main__":
    raise SystemExit(main())
