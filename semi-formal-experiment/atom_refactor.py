"""Rename / merge / split for the atom vocabulary, with a migration log.

WHY THIS MODULE EXISTS (ITERATION_LOOP.md Unit 3)
-------------------------------------------------
A vocabulary change today is a hand-edit across nine-plus JSON artifacts —
annotations, per-behaviour query configs, the golden reference, the
containment overlay — and any usage the editor misses breaks silently at the
next join. This is the "find references / rename symbol" of this codebase:

  usages <atom>      every reference, file + location, across every surface.
                     Stem-aware: a usage of `mustnot_X__model_user` IS a
                     usage of stem X (`grammar.stem_of` is the join key).
  rename / merge     mechanical rewrite of all usages. The stem moves, the
                     polarity prefix and principal chain stay. DRY-RUN by
                     default; `--apply` writes and appends one entry to
                     `vocabulary_migrations.json` (op, old, new, caller-
                     supplied date, reason, per-artifact sha before/after).
  rechain            the dual of rename: an EXACT decorated-name rewrite in
                     which the stem and the polarity must be identical and
                     only the principal chain moves. Whole-artifact by
                     default (then the target name must not exist anywhere);
                     `--clause <id>` (repeatable) scopes the rewrite to that
                     clause's usages — the case where one clause licenses a
                     shorter chain while another keeps the long one — and
                     folds vocabulary usage counts into an existing target
                     key with merge's semantics (the destination's meaning
                     survives; the source key is dropped only when no usage
                     remains). Clause-blind surfaces (behavior_atoms,
                     containment, behaviours_query) are untouched by a
                     scoped rechain: their usages carry no clause identity.
                     Same dry-run / --apply / --date / --reason discipline,
                     same log, same replay contract.
  split              NOT mechanical — whether a given usage of `X` means `a`
                     or `b` is a judgment about the document, so `split`
                     emits a per-usage worklist (clause text + gloss + quote,
                     stable ids, closed assignment vocabulary) and
                     `split-apply` applies only a complete, validated one.
                     Sandwich rule: deterministic producer → judgment under a
                     schema → mechanical validator.
  replay <artifact>  applies the migration log in order to an OLD copy of an
                     artifact and reproduces the CURRENT bytes. That is the
                     backwards-compatibility contract as a testable property:
                     no artifact is ever silently orphaned by a rename.

WHAT THIS MODULE MUST NEVER DO
------------------------------
  * A migration must never be JUSTIFIED BY PANEL OUTCOMES. The `reason`
    field records a document-side reason ("two concepts under one stem",
    "the spec's own word is X"); "it moved MCC" is not a reason a rename may
    carry, because fitting the vocabulary to the panel is fitting to labels
    (ITERATION_LOOP.md policy: labels direct attention, never truth).
  * It never reads the panel, its loaders, or anything on the FORBIDDEN
    list. It is a maintenance tool, not a query module — it is deliberately
    NOT in QUERY_MODULES — but `test_atom_refactor.py` holds its source to
    the same static scan and spies its file opens anyway.
  * It never writes on the default path. Every mutating subcommand is a
    dry-run unless `--apply` is passed; a refused precondition (target name
    exists, destination missing, non-canonical bytes, an edge collapsing to
    a self-loop) raises a NAMED error and writes nothing.
  * It never touches the wall clock. The migration date is caller-supplied
    (`--date`), so the same migration is byte-deterministic — replay and
    the sha pins in the log depend on that.
  * It never rewrites a name it cannot parse, and never rewrites a name
    whose stem is not the one being migrated: `rewrite_name` is the
    identity on every unrelated name, pinned stem_of-style over the real
    b8 vocabulary.

Artifacts are round-tripped through the repo's canonical serialization
(json.dumps indent=1; the trailing newline AND the ascii-escaping are each
a per-file STYLE, detected from the file's own bytes and preserved —
`annotations_ext_v1_merged.json` ships ensure_ascii=True while its siblings
ship ensure_ascii=False, and rewriting either in the other's style would
touch every non-ascii line). A file this tool cannot reproduce
byte-identically BEFORE editing is refused (NonCanonicalArtifactError)
rather than reformatted wholesale — "unrelated names byte-untouched" is a
contract, not a hope.

A migration touching `golden_translations.json` re-freezes its sha256 (via
`golden.compute_sha256`, same canonicalization) and appends a review record
to each touched entry, following the artifact's own in-file convention
(`entries[i].review: [{by, change, why, ...}]`) — the reference stays frozen
and the edit stays on the record.
"""
from __future__ import annotations

import argparse
import collections
import copy
import glob
import hashlib
import json
import os
import re
import sys

import golden
import grammar

HERE = os.path.dirname(os.path.abspath(__file__))

MIGRATIONS_NAME = "vocabulary_migrations.json"

#: The usage surfaces, in scan order. behavior_atoms* is a glob: every draw
#: is an artifact someone may replay, so every draw is rewritten.
FIXED_SURFACES_HEAD = ("annotations.json", "annotations_b8.json",
                       "annotations_ext_v1.json",
                       "annotations_ext_v1_patch.json",
                       "annotations_ext_v1_merged.json")
BEHAVIOR_ATOMS_GLOB = "behavior_atoms*.json"
FIXED_SURFACES_TAIL = ("golden_translations.json", "containment.json",
                       "behaviours_query.json")

#: Clause corpora consulted (read-only) to put full clause text on split
#: worklists. Never rewritten — they hold no atom names.
CLAUSE_CORPORA = ("modelspec_clauses.json", "constitution_clauses.json")

_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}$")


# ----------------------------------------------------------------- errors

class RefactorError(RuntimeError):
    """Base for every refusal this module raises."""


class UnknownAtomError(RefactorError):
    """The named atom has zero usages on any surface."""


class NameExistsError(RefactorError):
    """The rename/split target already names something."""


class NotAStemError(RefactorError):
    """rename/merge/split operate on bare stems; a decorated or unparseable
    argument was passed."""


class NotAnExactNameError(RefactorError):
    """rechain operates on exact decorated names; an argument did not parse
    under the grammar."""


class StemChangedError(RefactorError):
    """rechain may move only the principal chain, but the two names' stems
    differ — a stem move is a rename/merge, which is adjudicated
    differently."""


class PolarityChangedError(RefactorError):
    """rechain may move only the principal chain, but the two names'
    polarity prefixes differ — a force change is never a chain repair."""


class NonCanonicalArtifactError(RefactorError):
    """The artifact's bytes are not reproduced by the canonical
    serialization, so a mechanical rewrite could not leave unrelated names
    byte-untouched."""


class EdgeConflictError(RefactorError):
    """The rewrite would leave a containment self-loop or duplicate edge."""


class WorklistError(RefactorError):
    """A split worklist failed validation."""


# ------------------------------------------------------------ file plumbing

def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _dumps(data, trailing_nl: bool, ensure_ascii: bool = False) -> bytes:
    blob = json.dumps(data, indent=1, ensure_ascii=ensure_ascii)
    if trailing_nl:
        blob += "\n"
    return blob.encode("utf-8")


def _load(path):
    """(data, raw_bytes, style). Parse only — no canonicality demand;
    `usages` must work on any readable artifact.

    `style` records the file's OWN serialization style so a rewrite can
    reproduce it: the trailing newline, and ascii-escaping (a file whose
    bytes are pure ascii is reproduced with ensure_ascii=True, which is the
    identity when the content is ascii anyway and the only correct choice
    when non-ascii content was escaped on write)."""
    with open(path, "rb") as f:
        raw = f.read()
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise RefactorError(f"{path} is not a JSON artifact: {e}") from e
    style = {"trailing_nl": raw.endswith(b"\n"),
             "ensure_ascii": raw.isascii()}
    return data, raw, style


def _require_canonical(path, data, raw, style):
    if _dumps(data, style["trailing_nl"], style["ensure_ascii"]) != raw:
        raise NonCanonicalArtifactError(
            f"{path} is not in the repo's canonical serialization "
            "(json.dumps indent=1; ascii-escaping and trailing newline are "
            "per-file styles, detected and preserved). Rewriting it would "
            "reformat every line, so unrelated names could not stay "
            "byte-untouched. Re-serialize it canonically first, on its own, "
            "in a diff that changes nothing else.")


def surface_paths(root=HERE):
    """The usage surfaces present under `root`, in fixed scan order."""
    names = list(FIXED_SURFACES_HEAD)
    names += sorted(os.path.basename(p) for p in
                    glob.glob(os.path.join(root, BEHAVIOR_ATOMS_GLOB)))
    names += list(FIXED_SURFACES_TAIL)
    return [n for n in names if os.path.exists(os.path.join(root, n))]


def detect_shape(data):
    """Which rewrite rules apply, decided by CONTENT so an old copy under
    any filename replays correctly."""
    if not isinstance(data, dict):
        return None
    if data.get("artifact") == "golden_translations":
        return "golden"
    if isinstance(data.get("edges"), list):
        return "containment"
    if "by_clause" in data and "vocabulary" in data:
        return "annotations"
    if isinstance(data.get("behaviours"), list):
        return "behaviours_query"
    if any(isinstance(v, dict) and "atoms" in v for k, v in data.items()
           if k not in ("provenance",) and not k.startswith("_")):
        return "behavior_atoms"
    return None


# ---------------------------------------------------------- usage scanning

def _iter_usages(data, shape):
    """Yield (location, name, context) for every atom-name reference in one
    parsed artifact. Locations are stable strings; contexts carry what a
    split worklist needs (clause_id, span_id, gloss, quote, ...)."""
    if shape == "annotations":
        for i, a in enumerate(data.get("atoms") or []):
            yield (f"atoms[{i}]", a.get("name"),
                   {"clause_id": a.get("clause_id"),
                    "span_id": a.get("span_id"),
                    "gloss": a.get("gloss"), "quote": a.get("quote")})
        for cid, atoms in (data.get("by_clause") or {}).items():
            for j, a in enumerate(atoms or []):
                yield (f"by_clause.{cid}[{j}]", a.get("name"),
                       {"clause_id": cid, "span_id": a.get("span_id"),
                        "gloss": a.get("gloss"), "quote": a.get("quote")})
        for key, v in (data.get("vocabulary") or {}).items():
            yield (f"vocabulary.{key}", key,
                   {"gloss": (v or {}).get("gloss"), "derived": True})
    elif shape == "behavior_atoms":
        for slug, v in data.items():
            if slug == "provenance" or slug.startswith("_"):
                continue
            if not (isinstance(v, dict) and isinstance(v.get("atoms"), list)):
                continue
            for i, a in enumerate(v["atoms"]):
                yield (f"{slug}.atoms[{i}]", a.get("name"),
                       {"behaviour": slug, "gloss": a.get("gloss")})
    elif shape == "golden":
        for i, e in enumerate(data.get("entries") or []):
            for j, a in enumerate(e.get("atoms") or []):
                yield (f"entries[{i}].atoms[{j}]", a.get("name"),
                       {"clause_id": e.get("clause_id"),
                        "clause_text": e.get("quote"),
                        "span_id": a.get("span_id"),
                        "gloss": a.get("gloss"), "quote": a.get("quote")})
    elif shape == "containment":
        for i, e in enumerate(data.get("edges") or []):
            yield (f"edges[{i}].child", e.get("child"),
                   {"edge_parent": e.get("parent"), "note": e.get("note")})
            yield (f"edges[{i}].parent", e.get("parent"),
                   {"edge_child": e.get("child"), "note": e.get("note")})
    elif shape == "behaviours_query":
        for i, b in enumerate(data.get("behaviours") or []):
            for j, a in enumerate(b.get("atoms") or []):
                name = a.get("name") if isinstance(a, dict) else a
                gloss = a.get("gloss") if isinstance(a, dict) else None
                yield (f"behaviours[{i}].atoms[{j}]", name,
                       {"behaviour": b.get("slug"), "gloss": gloss})


def find_usages(atom, root=HERE):
    """Every reference to `atom`'s STEM across every surface.

    `match` is "exact" when the reference is the very name asked about, and
    "stem" when it is a decorated form of the same stem — both are usages,
    because `stem_of` is the key every join runs on.
    """
    target_stem = grammar.stem_of(atom)
    out = []
    for rel in surface_paths(root):
        data, _, _ = _load(os.path.join(root, rel))
        shape = detect_shape(data)
        if shape is None:
            continue
        for location, name, context in _iter_usages(data, shape):
            if name is None or grammar.stem_of(name) != target_stem:
                continue
            out.append({"file": rel, "location": location, "name": name,
                        "stem": target_stem,
                        "match": "exact" if name == atom else "stem",
                        "context": context})
    return out


# ----------------------------------------------------------------- rewrite

def rewrite_name(name, old, new):
    """Move the STEM `old` to `new`, keeping polarity and principals.

    The identity on every other name: an unparseable name is returned
    untouched (rewriting a join key we could not read would be invisible
    downstream), and so is any name whose stem is not `old`.
    """
    p = grammar.parse_name(name)
    if p["error"] or p["stem"] != old:
        return name
    return grammar.format_name(new, polarity=p["polarity"],
                               principals=p["principals"])


def _require_stem(arg, what):
    p = grammar.parse_name(arg)
    if p["error"] or p["polarity"] or p["principals"]:
        raise NotAStemError(
            f"{what} {arg!r} is not a bare stem. rename/merge/split operate "
            "on the stem — the join key — and rewrite every decorated form "
            "of it; pass the stem itself.")
    return arg


def _require_rechain_pair(old, new):
    """rechain's precondition: two EXACT names, identical stem, identical
    polarity — only the principal chain may differ."""
    po = grammar.parse_name(old)
    if po["error"]:
        raise NotAnExactNameError(
            f"rechain source {old!r} does not parse: {po['error']}. rechain "
            "operates on exact decorated names.")
    pn = grammar.parse_name(new)
    if pn["error"]:
        raise NotAnExactNameError(
            f"rechain target {new!r} does not parse: {pn['error']}. rechain "
            "operates on exact decorated names.")
    if po["stem"] != pn["stem"]:
        raise StemChangedError(
            f"rechain may move only the principal chain, but the stems "
            f"differ ({po['stem']!r} vs {pn['stem']!r}) — a stem move is a "
            "rename or a merge; say which.")
    if po["polarity"] != pn["polarity"]:
        raise PolarityChangedError(
            f"rechain may move only the principal chain, but the polarity "
            f"differs ({po['polarity']!r} vs {pn['polarity']!r}) — a force "
            "change is not a chain repair.")
    if old == new:
        raise RefactorError(f"rechain of {old!r} onto itself is a no-op")


def _all_names(root):
    """Every EXACT atom name in use on any surface (rechain's key space,
    the way `_all_stems` is rename/merge's)."""
    names = set()
    for rel in surface_paths(root):
        data, _, _ = _load(os.path.join(root, rel))
        shape = detect_shape(data)
        if shape is None:
            continue
        for _, name, _ in _iter_usages(data, shape):
            if name is not None:
                names.add(name)
    return names


def _guard_edges(edges):
    seen = set()
    for i, e in enumerate(edges):
        child, parent = e.get("child"), e.get("parent")
        if child == parent:
            raise EdgeConflictError(
                f"the rewrite would leave containment edge [{i}] as a "
                f"self-loop ({child!r} ⊑ {parent!r}). A subsumption of "
                "a name into itself is not a mechanical consequence of a "
                "vocabulary migration — retire or re-author the edge first.")
        key = (child, parent)
        if key in seen:
            raise EdgeConflictError(
                f"the rewrite would leave two identical containment edges "
                f"({child!r} ⊑ {parent!r}). Deduplicating provenanced "
                "edges is an authoring decision, not a mechanical one — "
                "retire one edge first.")
        seen.add(key)


def _rewrite_vocabulary(vocab, name_fn):
    """Rewrite the vocabulary's KEYS, merging entries whose keys collide.

    On a collision (merge op) the entry whose ORIGINAL key equals the final
    key keeps its kind/gloss and the clause lists are unioned — the
    destination's meaning survives, the source's coverage joins it.
    """
    merged = {}
    own_meta = {}
    for key, val in vocab.items():
        nk = name_fn(f"vocabulary.{key}", key)
        if nk not in merged:
            merged[nk] = copy.deepcopy(val)
            own_meta[nk] = (key == nk)
        else:
            a = merged[nk]
            clauses = sorted(set(a.get("clauses") or [])
                             | set(val.get("clauses") or []))
            base = a
            if key == nk and not own_meta[nk]:
                base = copy.deepcopy(val)
                own_meta[nk] = True
            base["clauses"] = clauses
            base["n_clauses"] = len(clauses)
            merged[nk] = base
    return merged


def _rechain_vocabulary(vocab, old, new, moved):
    """Rebuild the two vocabulary keys a CLAUSE-SCOPED rechain touches.

    `moved` is the set of clause ids whose usages were rewritten. Mirrors
    merge's semantics key-for-key: when the target key already exists, its
    kind/gloss survive and the moved clauses join its clause list; the
    source key keeps its remaining clauses and is dropped only when no
    usage remains. Every other key passes through untouched, in order.
    """
    out = {}
    for key, val in vocab.items():
        if key == old:
            remaining = [c for c in (val.get("clauses") or [])
                         if c not in moved]
            if remaining:
                entry = copy.deepcopy(val)
                entry["clauses"] = remaining
                entry["n_clauses"] = len(remaining)
                out[old] = entry
            if moved and new not in vocab:
                entry = copy.deepcopy(val)
                clauses = sorted(moved)
                entry["clauses"] = clauses
                entry["n_clauses"] = len(clauses)
                out[new] = entry
        elif key == new and moved:
            entry = copy.deepcopy(val)
            clauses = sorted(set(entry.get("clauses") or []) | moved)
            entry["clauses"] = clauses
            entry["n_clauses"] = len(clauses)
            out[new] = entry
        else:
            out[key] = val
    return out


def _split_vocabulary(vocab, by_clause, old, into):
    """Rebuild the vocabulary keys whose stem is `old` after a split.

    The key is derived data (name -> clause list), so it is not adjudicated:
    each decorated form of `old` is replaced, in place, by the decorated
    forms of the targets that actually appear in the rewritten by_clause,
    with clause lists recomputed and kind/gloss inherited.
    """
    present = collections.defaultdict(set)
    for cid, atoms in (by_clause or {}).items():
        for a in atoms or []:
            present[a.get("name")].add(cid)
    out = {}
    for key, val in vocab.items():
        p = grammar.parse_name(key)
        if p["error"] or p["stem"] != old:
            out[key] = val
            continue
        for target in into:
            nk = grammar.format_name(target, polarity=p["polarity"],
                                     principals=p["principals"])
            if nk not in present:
                continue
            entry = copy.deepcopy(val)
            clauses = sorted(present[nk])
            entry["clauses"] = clauses
            entry["n_clauses"] = len(clauses)
            out[nk] = entry
    return out


def _golden_review_record(op, old, new, date, reason, n):
    """The record appended to a touched golden entry — a pure function of
    the migration, so replay reproduces it byte-for-byte."""
    new_txt = ",".join(new) if isinstance(new, (list, tuple)) else new
    return {
        "by": "atom_refactor.py (mechanical vocabulary migration, "
              "not a taste edit)",
        "change": f"{op}: {old} -> {new_txt}; {n} atom name(s) rewritten "
                  "in this entry",
        "why": reason,
        "date": date,
    }


def transform_document(data, shape, entry, rel=None):
    """Apply ONE migration-log entry to one parsed artifact.

    Returns (new_data, n_rewritten, touched_locations). Pure and
    deterministic — the same function serves planning and replay. For
    `split`, `rel` selects the entry's per-artifact assignment map.
    """
    op, old, new = entry["op"], entry["old"], entry["new"]
    scope = None
    if op in ("rename", "merge"):
        def name_fn(location, name):
            return rewrite_name(name, old, new)
    elif op == "rechain":
        scope = set(entry["clauses"]) if entry.get("clauses") else None

        def name_fn(location, name):
            return new if name == old else name
    elif op == "split":
        assign = (entry.get("assignments") or {}).get(rel or "", {})

        def name_fn(location, name):
            target = assign.get(location)
            if target is None:
                return name
            return rewrite_name(name, old, target)
    else:
        raise RefactorError(f"unknown migration op {op!r}")

    if scope is not None and shape in ("behavior_atoms", "containment",
                                       "behaviours_query"):
        # A clause-scoped rechain rewrites the usages OF A CLAUSE; these
        # surfaces carry no clause identity, so the scope leaves them alone.
        return data, 0, []

    data = copy.deepcopy(data)
    n = 0
    touched = []

    def visit(container, key, location):
        nonlocal n
        name = container[key]
        nk = name_fn(location, name)
        if nk != name:
            container[key] = nk
            n += 1
            touched.append(location)

    if shape == "annotations":
        moved = set()
        for i, a in enumerate(data.get("atoms") or []):
            if scope is not None and a.get("clause_id") not in scope:
                continue
            before = n
            visit(a, "name", f"atoms[{i}]")
            if op == "rechain" and n > before:
                moved.add(a.get("clause_id"))
        for cid, atoms in (data.get("by_clause") or {}).items():
            if scope is not None and cid not in scope:
                continue
            for j, a in enumerate(atoms or []):
                before = n
                visit(a, "name", f"by_clause.{cid}[{j}]")
                if op == "rechain" and n > before:
                    moved.add(cid)
        vocab = data.get("vocabulary") or {}
        if op == "split":
            nv = _split_vocabulary(vocab, data.get("by_clause"), old, new)
        elif op == "rechain" and scope is not None:
            moved.discard(None)
            nv = _rechain_vocabulary(vocab, old, new, moved)
        else:
            nv = _rewrite_vocabulary(vocab, name_fn)
        if nv != vocab:
            n += 1
            touched.append("vocabulary")
        data["vocabulary"] = nv
    elif shape == "behavior_atoms":
        for slug, v in data.items():
            if slug == "provenance" or slug.startswith("_"):
                continue
            if not (isinstance(v, dict) and isinstance(v.get("atoms"), list)):
                continue
            for i, a in enumerate(v["atoms"]):
                visit(a, "name", f"{slug}.atoms[{i}]")
    elif shape == "golden":
        touched_entries = {}
        for i, e in enumerate(data.get("entries") or []):
            if scope is not None and e.get("clause_id") not in scope:
                continue
            for j, a in enumerate(e.get("atoms") or []):
                before = n
                visit(a, "name", f"entries[{i}].atoms[{j}]")
                if n > before:
                    touched_entries[i] = touched_entries.get(i, 0) + 1
        if touched_entries:
            for i, count in sorted(touched_entries.items()):
                rec = _golden_review_record(op, old, new, entry["date"],
                                            entry["reason"], count)
                data["entries"][i].setdefault("review", []).append(rec)
            data["sha256"] = golden.compute_sha256(data)
    elif shape == "containment":
        for i, e in enumerate(data.get("edges") or []):
            visit(e, "child", f"edges[{i}].child")
            visit(e, "parent", f"edges[{i}].parent")
        if n:
            _guard_edges(data["edges"])
    elif shape == "behaviours_query":
        for i, b in enumerate(data.get("behaviours") or []):
            for j, a in enumerate(b.get("atoms") or []):
                if isinstance(a, dict):
                    visit(a, "name", f"behaviours[{i}].atoms[{j}]")
                else:
                    visit(b["atoms"], j, f"behaviours[{i}].atoms[{j}]")
    return data, n, touched


# --------------------------------------------------------------- planning

def _all_stems(root):
    stems = set()
    for rel in surface_paths(root):
        data, _, _ = _load(os.path.join(root, rel))
        shape = detect_shape(data)
        if shape is None:
            continue
        for _, name, _ in _iter_usages(data, shape):
            if name is not None:
                stems.add(grammar.stem_of(name))
    return stems


def _check_date(date):
    if not (isinstance(date, str) and _DATE_RE.match(date)):
        raise RefactorError(
            f"--date must be a literal YYYY-MM-DD (got {date!r}). The date "
            "is caller-supplied, never the wall clock, so the migration is "
            "byte-deterministic.")


def _check_reason(reason):
    if not (isinstance(reason, str) and reason.strip()):
        raise RefactorError("--reason is required and must be non-empty. "
                            "It must state a DOCUMENT-side reason; a panel "
                            "outcome is not a reason a migration may carry.")


def plan_migration(root, op, old, new, date=None, reason=None,
                   assignments=None, clauses=None):
    """Compute a migration without writing anything.

    Returns (entry, changes): the log entry to append, and
    {relpath: {"before": bytes, "after": bytes, "n": int,
    "locations": [...]}} for every artifact the migration touches.
    Every refusal happens here, before any byte moves.
    """
    _check_date(date)
    _check_reason(reason)
    if op in ("rename", "merge"):
        _require_stem(old, "source")
        _require_stem(new, "target")
        if old == new:
            raise RefactorError(f"{op} of {old!r} onto itself is a no-op")
        stems = _all_stems(root)
        if old not in stems:
            raise UnknownAtomError(
                f"{old!r} has zero usages on any surface under {root} — "
                "nothing to migrate.")
        if op == "rename" and new in stems:
            raise NameExistsError(
                f"rename target {new!r} already names something. If the two "
                "are genuinely the same concept, that is a MERGE — say so.")
        if op == "merge" and new not in stems:
            raise UnknownAtomError(
                f"merge destination {new!r} has zero usages — a merge folds "
                "into an EXISTING atom. If the destination is new, that is "
                "a RENAME.")
    elif op == "rechain":
        _require_rechain_pair(old, new)
        if not clauses:
            clauses = None
        names = _all_names(root)
        if old not in names:
            raise UnknownAtomError(
                f"{old!r} has zero usages on any surface under {root} — "
                "nothing to migrate.")
        if clauses is None and new in names:
            raise NameExistsError(
                f"rechain target {new!r} already names something, so a "
                "whole-artifact rechain would fold every usage of "
                f"{old!r} into it unreviewed. Scope the fold with "
                "--clause <id> (repeatable) so exactly the adjudicated "
                "clauses move.")
    elif op == "split":
        if assignments is None:
            raise RefactorError("a split plan requires assignments — build "
                                "them through split-apply's worklist, never "
                                "by hand")
    else:
        raise RefactorError(f"unknown migration op {op!r}")

    entry = {"op": op, "old": old, "new": new, "date": date,
             "reason": reason}
    if op == "split":
        entry["assignments"] = assignments
    if op == "rechain" and clauses:
        entry["clauses"] = sorted(clauses)

    changes = {}
    artifacts = {}
    for rel in surface_paths(root):
        path = os.path.join(root, rel)
        data, raw, style = _load(path)
        shape = detect_shape(data)
        if shape is None:
            continue
        new_data, n, touched = transform_document(data, shape, entry, rel)
        if n == 0:
            continue
        _require_canonical(path, data, raw, style)
        after = _dumps(new_data, style["trailing_nl"], style["ensure_ascii"])
        changes[rel] = {"before": raw, "after": after, "n": n,
                        "locations": touched}
        artifacts[rel] = {"sha_before": sha256_bytes(raw),
                          "sha_after": sha256_bytes(after),
                          "n_rewritten": n}
    if not changes:
        raise UnknownAtomError(
            f"{op} of {old!r} touches zero artifacts under {root}")
    entry["artifacts"] = artifacts
    return entry, changes


def load_log(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"artifact": "vocabulary_migrations", "version": 1,
            "migrations": []}


def apply_changes(root, entry, changes, log_path=None):
    """Write the planned bytes and append the log entry. The only function
    in this module that mutates the repo."""
    log_path = log_path or os.path.join(root, MIGRATIONS_NAME)
    for rel, ch in changes.items():
        with open(os.path.join(root, rel), "wb") as f:
            f.write(ch["after"])
    log = load_log(log_path)
    log["migrations"].append(entry)
    with open(log_path, "wb") as f:
        f.write(_dumps(log, trailing_nl=False))
    return log_path


# ------------------------------------------------------------------ split

def build_worklist(root, atom, into):
    """The judgment interface for a split: one record per ADJUDICABLE usage
    (vocabulary keys are derived data and rebuilt mechanically), each with
    clause text, gloss and quote, a stable id, and an empty `assign` slot
    whose only legal values are the two targets."""
    _require_stem(atom, "atom")
    if not (isinstance(into, (list, tuple)) and len(into) == 2):
        raise RefactorError("split takes exactly two targets: <a,b>")
    a, b = into
    _require_stem(a, "target")
    _require_stem(b, "target")
    if a == b:
        raise RefactorError("split targets must differ")
    stems = _all_stems(root)
    if atom not in stems:
        raise UnknownAtomError(f"{atom!r} has zero usages under {root}")
    for t in (a, b):
        if t != atom and t in stems:
            raise NameExistsError(
                f"split target {t!r} already names something — splitting "
                "into an existing atom is a split THEN a merge; do them "
                "separately so each is adjudicated.")

    clause_text = {}
    for corpus in CLAUSE_CORPORA:
        path = os.path.join(root, corpus)
        if not os.path.exists(path):
            continue
        data, _, _ = _load(path)
        for c in data.get("clauses") or []:
            if c.get("id"):
                clause_text[c["id"]] = c.get("quote")

    usages = []
    for u in find_usages(atom, root=root):
        ctx = u["context"]
        if ctx.get("derived"):
            continue
        cid = ctx.get("clause_id")
        rec = {
            "usage_id": f"{u['file']}#{u['location']}",
            "file": u["file"],
            "location": u["location"],
            "name": u["name"],
            "clause_id": cid,
            "span_id": ctx.get("span_id"),
            "clause_text": ctx.get("clause_text") or clause_text.get(cid),
            "gloss": ctx.get("gloss"),
            "quote": ctx.get("quote"),
            "assign": None,
        }
        for k in ("behaviour", "edge_parent", "edge_child", "note"):
            if ctx.get(k) is not None:
                rec[k] = ctx[k]
        usages.append(rec)
    return {
        "artifact": "split_worklist",
        "atom": atom,
        "into": [a, b],
        "assignment_schema": {
            "assign": f"exactly one of {a!r} or {b!r} per usage; a record "
                      "left null blocks the whole apply"},
        "usages": usages,
    }


def validate_worklist(root, worklist):
    """dossier.py-validate discipline: coverage re-derived live from the
    current artifacts (a stale worklist FAILS), dupes / unknown ids / open
    or out-of-vocabulary assignments surfaced, mirror records (same file,
    clause, span, name) required to agree, every count printed, one-word
    VERDICT line. Returns (ok, summary)."""
    atom = worklist.get("atom")
    into = worklist.get("into") or []
    fresh = build_worklist(root, atom, into) if atom else {"usages": []}
    expected = [u["usage_id"] for u in fresh["usages"]]

    records = worklist.get("usages") or []
    seen = []
    bad_target = []
    unassigned = []
    groups = collections.defaultdict(set)
    for rec in records:
        uid = rec.get("usage_id")
        if not uid:
            continue
        seen.append(uid)
        assign = rec.get("assign")
        if assign is None:
            unassigned.append(uid)
        elif assign not in into:
            bad_target.append(uid)
        else:
            groups[(rec.get("file"), rec.get("clause_id"),
                    rec.get("span_id"), rec.get("name"))].add(assign)

    counts = collections.Counter(seen)
    dupes = sorted(k for k, v in counts.items() if v > 1)
    never = [uid for uid in expected if uid not in counts]
    unknown = sorted(set(seen) - set(expected))
    inconsistent = sorted(
        f"{f}:{cid}:{sid}:{name}" for (f, cid, sid, name), a in
        groups.items() if len(a) > 1 and sid is not None)

    summary = {
        "expected": len(expected),
        "assigned": len(seen),
        "never_assigned": sorted(set(never) | set(unassigned)),
        "duplicated": dupes,
        "unknown": unknown,
        "bad_target": sorted(bad_target),
        "inconsistent": inconsistent,
    }
    ok = not (summary["never_assigned"] or dupes or unknown
              or bad_target or inconsistent)

    print(f"--- split worklist for {atom!r} -> {into}")
    print(f"usages expected     {len(expected)}")
    print(f"records supplied    {len(seen)}")
    print(f"never assigned      {len(summary['never_assigned'])} "
          f"{summary['never_assigned'][:5]}")
    print(f"duplicated ids      {len(dupes)} {dupes[:5]}")
    print(f"unknown ids         {len(unknown)} {unknown[:5]}")
    print(f"bad target          {len(summary['bad_target'])} "
          f"{summary['bad_target'][:5]}")
    print(f"inconsistent mirror {len(inconsistent)} {inconsistent[:5]}")
    print(f"VERDICT             {'clean' if ok else 'DISCREPANCIES ABOVE'}")
    return ok, summary


def worklist_assignments(worklist):
    """{relpath: {location: target}} from a VALIDATED worklist."""
    out = collections.defaultdict(dict)
    for rec in worklist.get("usages") or []:
        out[rec["file"]][rec["location"]] = rec["assign"]
    return dict(out)


# ----------------------------------------------------------------- replay

def replay_artifact(path, log_path, as_rel=None):
    """Apply the migration log, in order, to an OLD copy of an artifact.

    Returns the migrated bytes. This is the backwards-compatibility
    contract: an artifact from before a rename, replayed, must equal the
    current one. `as_rel` names which surface the copy is a copy OF —
    required only for split migrations of multi-file shapes (annotations /
    behavior_atoms), whose assignments are per-file.
    """
    data, _, style = _load(path)
    shape = detect_shape(data)
    if shape is None:
        raise RefactorError(f"{path} matches no known artifact shape")
    if as_rel is None and shape in ("golden", "containment",
                                    "behaviours_query"):
        as_rel = {"golden": "golden_translations.json",
                  "containment": "containment.json",
                  "behaviours_query": "behaviours_query.json"}[shape]
    log = load_log(log_path)
    for entry in log.get("migrations") or []:
        if entry["op"] == "split" and as_rel is None:
            raise RefactorError(
                "replaying a split over an annotations/behavior_atoms copy "
                "needs --as <relpath>: the split's assignments are "
                "per-file and the copy's filename does not say which file "
                "it was.")
        data, _, _ = transform_document(data, shape, entry, as_rel)
    return _dumps(data, style["trailing_nl"], style["ensure_ascii"])


# -------------------------------------------------------------------- CLI

def _print_plan(entry, changes, applied):
    scope = (f" [clauses: {', '.join(entry['clauses'])}]"
             if entry.get("clauses") else "")
    print(f"--- {entry['op']}: {entry['old']} -> {entry['new']}{scope} "
          f"({entry['date']}; {entry['reason']})")
    for rel in sorted(changes):
        ch = changes[rel]
        print(f"{rel:32s} {ch['n']:3d} rewritten  "
              f"{entry['artifacts'][rel]['sha_before'][:12]} -> "
              f"{entry['artifacts'][rel]['sha_after'][:12]}")
        for loc in ch["locations"][:6]:
            print(f"    {loc}")
        if len(ch["locations"]) > 6:
            print(f"    ... {len(ch['locations']) - 6} more")
    if applied:
        print(f"APPLIED — {len(changes)} artifact(s) written, migration "
              f"logged to {MIGRATIONS_NAME}")
    else:
        print("DRY RUN — nothing written. Pass --apply to write the "
              "artifacts and append the migration log.")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="atom_refactor.py",
        description="find-references / rename / merge / split for the atom "
                    "vocabulary, with a replayable migration log "
                    "(ITERATION_LOOP.md Unit 3)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_root(p):
        p.add_argument("--root", default=HERE,
                       help="repo directory holding the artifacts")

    pu = sub.add_parser("usages", help="every reference to an atom's stem, "
                                       "file + location, across all surfaces")
    pu.add_argument("atom")
    pu.add_argument("--json", action="store_true",
                    help="machine-readable output")
    add_root(pu)

    def add_migration_args(p):
        p.add_argument("--date", required=True,
                       help="YYYY-MM-DD, caller-supplied — never wall clock")
        p.add_argument("--reason", required=True,
                       help="DOCUMENT-side reason; panel outcomes are not "
                            "a reason")
        p.add_argument("--apply", action="store_true",
                       help="write artifacts + migration log (default: "
                            "dry-run)")
        add_root(p)

    pr = sub.add_parser("rename", help="mechanically rewrite one stem "
                                       "everywhere (target must be new)")
    pr.add_argument("old")
    pr.add_argument("new")
    add_migration_args(pr)

    pm = sub.add_parser("merge", help="fold one stem into an EXISTING one")
    pm.add_argument("src")
    pm.add_argument("dst")
    add_migration_args(pm)

    pc = sub.add_parser("rechain", help="exact-name rewrite moving ONLY the "
                                        "principal chain — stem and polarity "
                                        "must be identical")
    pc.add_argument("old")
    pc.add_argument("new")
    pc.add_argument("--clause", action="append", dest="clauses",
                    metavar="ID", default=None,
                    help="rewrite only this clause's usages (repeatable); "
                         "required when the target name already exists")
    add_migration_args(pc)

    ps = sub.add_parser("split", help="emit the per-usage worklist for a "
                                      "split (judgment, not mechanics)")
    ps.add_argument("atom")
    ps.add_argument("into", help="the two new stems, comma-separated: a,b")
    ps.add_argument("--out", required=True, help="worklist path to write")
    add_root(ps)

    pa = sub.add_parser("split-apply", help="validate a completed worklist "
                                            "and apply it")
    pa.add_argument("--worklist", required=True)
    add_migration_args(pa)

    pp = sub.add_parser("replay", help="apply the migration log in order "
                                       "to an old artifact copy")
    pp.add_argument("artifact")
    pp.add_argument("--as", dest="as_rel", default=None,
                    help="which surface this is a copy of (needed to "
                         "replay splits over annotations/behavior_atoms)")
    pp.add_argument("--log", default=None,
                    help=f"migration log (default: <root>/{MIGRATIONS_NAME})")
    pp.add_argument("--out", default=None,
                    help="write migrated bytes here (default: stdout)")
    add_root(pp)

    args = parser.parse_args(argv)

    try:
        if args.cmd == "usages":
            got = find_usages(args.atom, root=args.root)
            if args.json:
                print(json.dumps(got, indent=1, ensure_ascii=False))
            else:
                stem = grammar.stem_of(args.atom)
                print(f"--- usages of stem {stem!r} "
                      f"(asked as {args.atom!r})")
                for u in got:
                    print(f"{u['file']:32s} {u['location']:34s} "
                          f"{u['match']:5s} {u['name']}")
                exact = sum(1 for u in got if u["match"] == "exact")
                print(f"TOTAL {len(got)} ({exact} exact, "
                      f"{len(got) - exact} stem-decorated)")
            return 0

        if args.cmd in ("rename", "merge"):
            old, new = ((args.old, args.new) if args.cmd == "rename"
                        else (args.src, args.dst))
            entry, changes = plan_migration(args.root, args.cmd, old, new,
                                            date=args.date,
                                            reason=args.reason)
            if args.apply:
                apply_changes(args.root, entry, changes)
            _print_plan(entry, changes, args.apply)
            return 0

        if args.cmd == "rechain":
            entry, changes = plan_migration(args.root, "rechain", args.old,
                                            args.new, date=args.date,
                                            reason=args.reason,
                                            clauses=args.clauses)
            if args.apply:
                apply_changes(args.root, entry, changes)
            _print_plan(entry, changes, args.apply)
            return 0

        if args.cmd == "split":
            into = [s.strip() for s in args.into.split(",") if s.strip()]
            wl = build_worklist(args.root, args.atom, into)
            with open(args.out, "wb") as f:
                f.write(_dumps(wl, trailing_nl=False))
            print(f"worklist with {len(wl['usages'])} usage(s) written to "
                  f"{args.out}. Assign each to one of {wl['into']}, then "
                  "run split-apply --worklist.")
            return 0

        if args.cmd == "split-apply":
            with open(args.worklist, encoding="utf-8") as f:
                wl = json.load(f)
            ok, _ = validate_worklist(args.root, wl)
            if not ok:
                print("REFUSED: the worklist is not complete and "
                      "consistent — nothing written.", file=sys.stderr)
                return 2
            entry, changes = plan_migration(
                args.root, "split", wl["atom"], wl["into"],
                date=args.date, reason=args.reason,
                assignments=worklist_assignments(wl))
            if args.apply:
                apply_changes(args.root, entry, changes)
            _print_plan(entry, changes, args.apply)
            return 0

        if args.cmd == "replay":
            log_path = args.log or os.path.join(args.root, MIGRATIONS_NAME)
            blob = replay_artifact(args.artifact, log_path,
                                   as_rel=args.as_rel)
            if args.out:
                with open(args.out, "wb") as f:
                    f.write(blob)
                print(f"migrated copy written to {args.out} "
                      f"(sha256 {sha256_bytes(blob)[:12]})")
            else:
                sys.stdout.write(blob.decode("utf-8"))
            return 0
    except RefactorError as e:
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
