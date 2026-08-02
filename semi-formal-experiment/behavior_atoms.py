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

    .venv/bin/python behavior_atoms.py --print-prompt
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


def render_prompt(behaviour, vocab, conduct=(), max_new=MAX_NEW_ATOMS):
    """`(system, user)` for ONE behaviour.

    Note what this takes and what it does not: exactly one behaviour, and no
    clause text. Rendering it per query is what the cache invariant forbids;
    rendering several behaviours at once would make one truncation cost all of
    them and would stop the artifact being rebuildable a behaviour at a time.
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


def verify_selection(obj, vocab, fail, max_new=MAX_NEW_ATOMS, has_conduct=False):
    """`(atoms, stats)` from one parsed response. Never raises.

    Selected atoms are checked against the vocabulary by name; the KIND and the
    GLOSS are then taken from the vocabulary, not from the model, because those
    are what the clause side will be matched on and the model is not the
    authority on them. A near-duplicate name is resolved through
    annotate.vocab_key before being called new.
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
            if name in seen:
                reject("duplicate", {"name": name})
                continue
            seen.add(name)

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
            out.append({"name": name, "kind": kind_out, "gloss": gloss,
                        "weight": _weight(raw.get("weight")), "source": src,
                        "new": genuinely_new})
    return out, stats


def atoms_for_behaviour(response, behaviour, vocab, fail, conduct=(),
                        max_new=MAX_NEW_ATOMS):
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
                                    has_conduct=bool(conduct))
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
    for k, v in more.items():
        if isinstance(v, dict):
            sub = into.setdefault(k, {})
            for kk, vv in v.items():
                sub[kk] = sub.get(kk, 0) + vv
        elif isinstance(v, (int, float)):
            into[k] = into.get(k, 0) + v
    return into


def run(client, behaviours, vocab, conduct=None, out=None, out_dir=".",
        log_path=None, model="", provider=None, seed=0,
        max_new=MAX_NEW_ATOMS, max_vocab=DEFAULT_MAX_VOCAB,
        max_tokens=DEFAULT_MAX_TOKENS, annotations_path=ANNOTATIONS_PATH,
        return_path=False):
    """One pass over the behaviours: ONE call each, then write the cache."""
    behaviours = [b for b in behaviours if isinstance(b, dict)]
    conduct = dict(conduct or {})
    vocab = list(vocab or [])
    vocab_names = {a["name"] for a in vocab if isinstance(a, dict) and a.get("name")}

    warns = []
    if not vocab:
        msg = FREE_GENERATION_WARNING.format(path=annotations_path)
        warns.append(msg)
        warnings.warn(msg, RuntimeWarning, stacklevel=2)
        print(f"WARNING: {msg}", file=sys.stderr)

    first = behaviours[0] if behaviours else {"slug": ""}
    _, first_user = render_prompt(first, vocab,
                                  conduct.get(first.get("slug"), []), max_new)
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
        system, user = render_prompt(b, shown, cond, max_new)
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
                                   max_new=max_new)
        atoms = part["atoms"]
        in_vocab = sum(1 for a in atoms if a["name"] in vocab_names)
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
    for w in art.get("_warnings", []):
        print("    !! " + w)


def main(argv=None):
    args = build_parser().parse_args(argv)
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
                                     args.max_new)
        print("### SYSTEM\n" + system + "\n\n### USER\n" + user)
        return 0

    cfg = annotate.provider_config(args.provider, args.providers)
    cfg.max_tokens = args.max_tokens
    est = estimate_cost(behaviours, vocab, cfg.price_per_mtok, args.max_tokens)
    print(f"    estimated {est['input_tokens']} in / {est['output_tokens']} out "
          f"tokens" + (f" ≈ ${est['usd']:.4f}" if est["usd"] is not None else ""))

    client = annotate.make_annotate_client(cfg, live=args.live,
                                           log_dir=_p(args.prompt_log))
    if not args.live:
        print("DRY RUN (no network). Pass --live to make real calls.")
    art, path = run(client, behaviours, vocab, conduct=conduct,
                    out=args.out, out_dir=args.out_dir, log_path=args.log,
                    model=cfg.model, provider=cfg.name, seed=args.seed,
                    max_new=args.max_new, max_vocab=args.max_vocab,
                    max_tokens=args.max_tokens,
                    annotations_path=args.annotations, return_path=True)
    _summarize(art, path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
