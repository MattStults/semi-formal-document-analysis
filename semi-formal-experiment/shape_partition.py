"""SHAPE PARTITION — the mechanical Shape-A / Shape-B enumerator.

WHAT THIS IS. `VOCAB_GAPS_DESIGN.md` §2 draws the gate that is supposed to
stop a panel-derived census from being laundered into the vocabulary:

  Shape A — the concept is atomized NOWHERE. Fix = add clause-side atoms.
  Shape B — the concept exists clause-side but no behaviour's query can
            reach it. Fix = RE-SELECTION; adding duplicate atoms is
            forbidden.

`S6_ADVERSARIAL_REVIEW.md` finding B1 established that nothing enforces
that gate: the judgement seat is blinded to behaviour vocabularies by §3.1
and so cannot apply it, and the worksheet validator has no input from which
to compute it — the only thing applying it is prose in §1, which does not
survive recomputation. B1's fix, which is this module: compute the
partition mechanically, as a committed script whose output is frozen before
anything is admitted.

  python3 shape_partition.py build    [--out vocab_gap/shape_partition.json]
  python3 shape_partition.py validate  --path PATH

THE JOIN KEY IS `containment.dechain_name`, NOT `grammar.stem_of`.
`dechain_name` strips the principal chain and PRESERVES polarity;
`stem_of` strips polarity too and would merge `must_x` with `mustnot_x` —
the hazard `containment.py:141` documents in as many words, and the error a
sibling design's decision material actually made. It is not hypothetical
here: on the live artifacts the two keys give DIFFERENT answers for exactly
two of the 26 target clauses (m0242, m0253), and in both cases `stem_of`
would have called a Shape-A clause Shape-B. Those two are recorded in their
own state (see below) rather than folded silently into Shape A, so the
artifact carries the evidence of where the wrong key would have inverted
the result.

THE THIRD STATE, decided FROM the data. Three candidate third states were
computed against the live artifacts before one was adopted:
  * a target clause carrying NO atoms at all — occurs 0 times, so the data
    does not demand it (a clause with no atoms would classify `shape_a`
    with an explicit reason, which is correct);
  * a clause whose atom sits in its OWN dossier behaviour's query — would
    contradict the census's `atom_channel_zero` discriminator; occurs 0
    times;
  * a clause reachable only through the licensed containment overlay
    (`containment.json`) rather than by identity — occurs 0 times (v0's
    only family is `manipulation`, and the one target clause carrying a
    member already meets a query by identity);
  * `shape_a_polarity_variant` — no atom in any query under the correct
    key, but an atom whose POLARITY-STRIPPED stem is in some query. Occurs
    twice, and is the only state whose membership depends on the join-key
    choice. Adopted. It is a SUBSET of Shape A (the query genuinely cannot
    meet the atom: `mustnot_generate_disallowed_content` and
    `shouldnot_generate_disallowed_content` are different atoms and the
    grammar's whole point is that they stay different) — but it is the
    highest duplicate-risk corner of Shape A, because the concept exists in
    a query under another modality, so a seat adding an atom here is one
    prefix away from minting the duplicate §2 forbids.

PANEL-BLINDNESS, precisely. The SELECTION of the 26 clauses comes from the
census (`audit_dossiers/ext_v1_merged__audit_v1/verdicts_merged.json`,
cause == `fn_family_absent_from_vocabulary`) — panel-derived, legitimate
label-directed ATTENTION under ITERATION_LOOP.md §1, disclosed verbatim in
the artifact's `selection` block. Nothing else flows from the census: the
only bytes read out of it are dossier ids, and the only bytes read out of a
dossier are `mapped_clauses[*].clause_id`. The CLASSIFICATION is a pure
function of (clause-side atoms, behaviour query vocabularies) — `classify`
takes an atom list and a query index and has no argument a panel value
could arrive through, and the classification payload is banned-key scanned
at build AND validate time.

FENCE — FORBIDDEN, not QUERY_MODULES. This module reads a panel-derived
census verdict file to extract an id list. That is exactly the shape of
`drift_dossiers` (and of `audit_disagreements` / `diagnose_disagreement`
before it): a module on the *disclosure* side of the fence, whose fence is
that no query module may import it or read its output. Registering it in
`QUERY_MODULES` instead would be strictly wrong on both counts — the static
scan would fail immediately on the FORBIDDEN token `verdicts` in the census
path, and "passing" that scan by routing the census read through an
indirection would convert a disclosed reader into a laundering path. So
`shape_partition` is a FORBIDDEN token in `test_no_reference_leak.py`, and
its output artifact is a design-time record: nothing at query time may read
it, and no threshold, weight or score may cite it.

DETERMINISM. Sorted keys, sorted rows, no wall clock, no run-varying
content: same inputs give the same bytes, so the artifact is sha-pinnable
and can be frozen at cycle OPEN.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import containment
import grammar

HERE = os.path.dirname(os.path.abspath(__file__))
CENSUS_DIR = os.path.join(HERE, "audit_dossiers", "ext_v1_merged__audit_v1")
ANNOTATIONS = os.path.join(HERE, "annotations_ext_v1_merged.json")
BEHAVIOUR_ATOMS = os.path.join(HERE, "behavior_atoms_audit_v1.json")
CLAUSES = os.path.join(HERE, "modelspec_clauses.json")
DEFAULT_OUT = os.path.join(HERE, "vocab_gap", "shape_partition.json")

#: The census cause whose dossiers this partition covers.
CENSUS_CAUSE = "fn_family_absent_from_vocabulary"
CENSUS_FILE = "verdicts_merged.json"

#: Closed vocabularies (assert every one — the golden-author lesson).
SHAPES = ("shape_a", "shape_a_polarity_variant", "shape_b")
ATOM_FIELDS = ("name", "kind", "join_key", "stem_key", "in_queries",
               "polarity_variants")
CLAUSE_FIELDS = ("clause_id", "shape", "reason", "n_atoms", "atoms",
                 "divergent_under_stem_of", "shape_under_stem_key")
SELECTION_FIELDS = ("cause", "census_dir", "census_file", "n_dossiers",
                    "clause_ids", "label_hygiene")
CLI_MODES = ("build", "validate")

#: Keys that only appear when a panel/census value is being carried. Scanned
#: RECURSIVELY over the classification payload — never over the `selection`
#: block, which names the cause deliberately, as the disclosure.
BANNED_KEYS = (
    "panel_score", "panel", "verdicts", "verdict", "judge", "judges",
    "side", "cause", "note", "cut", "norm", "raw", "distance_to_cut",
    "channels", "channel_shares", "discriminators", "passage",
    "mapped_clauses", "max_clause", "dossier_id", "score", "scores",
)

#: Repeated verbatim into the artifact, per VOCAB_GAPS_DESIGN.md §0's own
#: standing requirement that every artifact carry it.
LABEL_HYGIENE = (
    "This worklist was DISCOVERED by a census over panel-labelled FN "
    "dossiers. Labels directed ATTENTION here and nothing else: the only "
    "bytes taken from the census are dossier ids, and the only bytes taken "
    "from a dossier are mapped_clauses[*].clause_id. The classification "
    "below is computed from clause-side annotations and behaviour query "
    "vocabularies alone; no panel value, score or verdict is an input to it."
)


class PartitionError(RuntimeError):
    """A refusal: invalid input artifact or invalid partition state."""


# ---------------------------------------------------------------- plumbing

def rel(path: str) -> str:
    """Repo-relative form, so the frozen artifact is the same bytes in every
    checkout. An absolute path would make the sha machine-specific."""
    return os.path.relpath(os.path.abspath(path), HERE)


def abspath(path: str) -> str:
    """The inverse of `rel`: resolve an artifact-recorded path."""
    return path if os.path.isabs(path) else os.path.join(HERE, path)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def join_key(name: str) -> str:
    """THE join key: `containment.dechain_name` — principal chain stripped,
    POLARITY KEPT. This is the key the live matcher runs on under pricing
    v1.2; see the module docstring for why `grammar.stem_of` is wrong."""
    return containment.dechain_name(name)


def stem_key(name: str) -> str:
    """The WRONG key, computed only so the artifact can record where it
    would have disagreed. Never used to classify."""
    return grammar.stem_of(name)


# ------------------------------------------------------- the query side

def query_index_from_mapping(queries) -> dict:
    """Behaviour -> query vocabulary, indexed both ways.

    `queries` maps behaviour name -> iterable of atom names. Returns
    {"behaviours": [...], "by_join_key": {key: [behaviours]},
     "by_stem_key": {stem: [(behaviour, atom_name)]}}.
    """
    behaviours = sorted(queries)
    by_join_key: dict = {}
    by_stem_key: dict = {}
    for beh in behaviours:
        for name in sorted(set(queries[beh])):
            by_join_key.setdefault(join_key(name), set()).add(beh)
            by_stem_key.setdefault(stem_key(name), set()).add((beh, name))
    return {
        "behaviours": behaviours,
        "by_join_key": {k: sorted(v) for k, v in sorted(by_join_key.items())},
        "by_stem_key": {k: sorted(v) for k, v in sorted(by_stem_key.items())},
    }


def query_index(path: str = BEHAVIOUR_ATOMS) -> dict:
    """The declared behaviours' query vocabularies, from the behaviour-atom
    artifact. `provenance` is metadata, not a behaviour."""
    with open(path) as f:
        payload = json.load(f)
    queries = {}
    for beh, block in payload.items():
        if beh == "provenance":
            continue
        if not isinstance(block, dict) or "atoms" not in block:
            raise PartitionError(
                f"behaviour {beh!r} in {os.path.basename(path)} has no "
                "atoms list")
        queries[beh] = [a["name"] for a in block["atoms"]]
    if not queries:
        raise PartitionError(f"no declared behaviours in {path}")
    return query_index_from_mapping(queries)


# ----------------------------------------------------- the classification

def classify(clause_id: str, atoms, index: dict) -> dict:
    """THE classification. A pure function of the clause's atoms and the
    query index — no census record, no dossier, no behaviour of origin, and
    therefore no argument a panel value could arrive through."""
    by_key = index["by_join_key"]
    by_stem = index["by_stem_key"]
    rows = []
    for atom in atoms:
        name = atom.get("name")
        k, s = join_key(name), stem_key(name)
        in_queries = list(by_key.get(k, []))
        variants = [{"behaviour": beh, "query_atom": qname}
                    for beh, qname in by_stem.get(s, [])
                    if beh not in in_queries]
        rows.append({
            "name": name,
            "kind": atom.get("kind"),
            "join_key": k,
            "stem_key": s,
            "in_queries": in_queries,
            "polarity_variants": sorted(
                variants, key=lambda v: (v["behaviour"], v["query_atom"])),
        })
    rows.sort(key=lambda r: (r["name"], r["join_key"]))

    met = [r for r in rows if r["in_queries"]]
    variant = [r for r in rows if r["polarity_variants"]]
    if met:
        shape = "shape_b"
        reason = (
            "existing atom(s) " + ", ".join(
                f"{r['name']} -> {r['join_key']} in "
                + "+".join(r["in_queries"]) for r in met)
            + " — the concept is already coined AND already query-worthy "
              "somewhere, so re-selection can reach this clause with zero "
              "annotation edits; adding an atom here is the duplicate "
              "VOCAB_GAPS_DESIGN.md §2 forbids")
    elif variant:
        shape = "shape_a_polarity_variant"
        reason = (
            "no existing atom's join key is in any declared query; "
            + "; ".join(
                f"{r['name']} shares stem {r['stem_key']!r} with "
                + "+".join(f"{v['behaviour']}:{v['query_atom']}"
                           for v in r["polarity_variants"])
                + " but differs in polarity/modality" for r in variant)
            + " — Shape A under the live join key, which grammar.stem_of "
              "would have inverted to shape_b")
    else:
        shape = "shape_a"
        reason = (
            "no existing atom's join key is in any declared behaviour's "
            "query vocabulary" if rows else
            "the clause carries no atoms at all")

    # the same call under the WRONG key, recorded for the divergence census
    stem_hit = any(by_stem.get(r["stem_key"]) for r in rows)
    under_stem = "shape_b" if stem_hit else "shape_a"
    return {
        "clause_id": clause_id,
        "shape": shape,
        "reason": reason,
        "n_atoms": len(rows),
        "atoms": rows,
        "shape_under_stem_key": under_stem,
        "divergent_under_stem_of": (shape == "shape_b") != (
            under_stem == "shape_b"),
    }


# ------------------------------------------------------------- the payload

def _banned_hits(node, path="") -> list:
    hits = []
    if isinstance(node, dict):
        for key, val in node.items():
            here = f"{path}.{key}" if path else key
            if key in BANNED_KEYS:
                hits.append(f"banned panel/census key {key!r} at {here} in "
                            "the classification payload")
            hits.extend(_banned_hits(val, here))
    elif isinstance(node, list):
        for i, val in enumerate(node):
            hits.extend(_banned_hits(val, f"{path}[{i}]"))
    return hits


def check_payload(rows) -> list:
    """Schema + closed-vocabulary + banned-key checks over the clause rows."""
    errors = []
    seen = {}
    for i, row in enumerate(rows):
        tag = f"clauses[{i}] {row.get('clause_id')!r}"
        unknown = sorted(set(row) - set(CLAUSE_FIELDS))
        missing = sorted(set(CLAUSE_FIELDS) - set(row))
        if unknown:
            errors.append(f"{tag}: unknown fields {unknown}")
        if missing:
            errors.append(f"{tag}: missing fields {missing}")
        if row.get("shape") not in SHAPES:
            errors.append(f"{tag}: shape {row.get('shape')!r} outside the "
                          f"closed set {SHAPES}")
        if row.get("shape_under_stem_key") not in ("shape_a", "shape_b"):
            errors.append(f"{tag}: shape_under_stem_key "
                          f"{row.get('shape_under_stem_key')!r} outside "
                          "('shape_a', 'shape_b')")
        if not str(row.get("reason", "")).strip():
            errors.append(f"{tag}: empty reason")
        for j, atom in enumerate(row.get("atoms") or []):
            au = sorted(set(atom) - set(ATOM_FIELDS))
            am = sorted(set(ATOM_FIELDS) - set(atom))
            if au:
                errors.append(f"{tag} atoms[{j}]: unknown fields {au}")
            if am:
                errors.append(f"{tag} atoms[{j}]: missing fields {am}")
        if row.get("n_atoms") != len(row.get("atoms") or []):
            errors.append(f"{tag}: n_atoms disagrees with the atom list")
        cid = row.get("clause_id")
        seen[cid] = seen.get(cid, 0) + 1
    for cid, n in sorted(seen.items()):
        if n > 1:
            errors.append(f"clause {cid!r} classified {n} times")
    ids = [r.get("clause_id") for r in rows]
    if ids != sorted(ids):
        errors.append("clause rows are not in sorted clause_id order "
                      "(the artifact must be deterministic)")
    errors.extend(_banned_hits(rows, "clauses"))
    return sorted(set(errors))


# ------------------------------------------------------------- the inputs

def target_clauses(census_dir: str = CENSUS_DIR) -> tuple:
    """The SELECTION step, and the only place the census is read.

    Returns (sorted clause ids, n_dossiers). Only dossier ids come out of
    the verdict file and only `mapped_clauses[*].clause_id` comes out of a
    dossier — no cause, side, note, score or verdict value is carried
    forward. This is label-directed ATTENTION, disclosed in the artifact.
    """
    vpath = os.path.join(census_dir, CENSUS_FILE)
    with open(vpath) as f:
        records = json.load(f)
    if isinstance(records, dict):
        lists = [v for v in records.values() if isinstance(v, list)]
        if len(lists) != 1:
            raise PartitionError(f"cannot read a record list from {vpath}")
        records = lists[0]
    ids = sorted({r["dossier_id"] for r in records
                  if r.get("cause") == CENSUS_CAUSE})
    if not ids:
        raise PartitionError(
            f"no dossiers with cause {CENSUS_CAUSE!r} in {vpath}")
    clause_ids = set()
    for did in ids:
        dpath = os.path.join(census_dir, did + ".json")
        if not os.path.exists(dpath):
            raise PartitionError(f"census names {did!r} but {dpath} is absent")
        with open(dpath) as f:
            dossier = json.load(f)
        mapped = [m["clause_id"] for m in dossier.get("mapped_clauses") or []]
        if not mapped:
            raise PartitionError(f"dossier {did!r} maps to no clause")
        clause_ids.update(mapped)
    return sorted(clause_ids), len(ids)


def clause_atoms(annotations_path: str = ANNOTATIONS) -> dict:
    with open(annotations_path) as f:
        payload = json.load(f)
    by_clause: dict = {}
    for atom in payload.get("atoms", []):
        by_clause.setdefault(atom["clause_id"], []).append(atom)
    return by_clause


def known_clause_ids(clauses_path: str = CLAUSES) -> set:
    with open(clauses_path) as f:
        return {c["id"] for c in json.load(f)["clauses"]}


# --------------------------------------------------------------- the build

def compute(census_dir: str = CENSUS_DIR,
            annotations_path: str = ANNOTATIONS,
            behaviour_atoms_path: str = BEHAVIOUR_ATOMS,
            clauses_path: str = CLAUSES) -> dict:
    """The whole artifact, as a dict. Deterministic; no wall clock."""
    clause_ids, n_dossiers = target_clauses(census_dir)
    atoms_by_clause = clause_atoms(annotations_path)
    index = query_index(behaviour_atoms_path)
    known = known_clause_ids(clauses_path)
    unknown = sorted(set(clause_ids) - known)
    if unknown:
        raise PartitionError(
            f"census names clauses absent from the document: {unknown}")

    rows = [classify(cid, atoms_by_clause.get(cid, []), index)
            for cid in clause_ids]
    errors = check_payload(rows)
    if errors:
        raise PartitionError("computed payload failed its own checks: "
                             + "; ".join(errors))

    by_shape: dict = {s: [] for s in SHAPES}
    for row in rows:
        by_shape[row["shape"]].append(row["clause_id"])
    inputs = [
        {"role": "census (SELECTION ONLY — ids out, nothing else)",
         "path": rel(os.path.join(census_dir, CENSUS_FILE)),
         "sha256": sha256_file(os.path.join(census_dir, CENSUS_FILE))},
        {"role": "clause-side annotations (document side)",
         "path": rel(annotations_path),
         "sha256": sha256_file(annotations_path)},
        {"role": "behaviour query vocabularies (query side)",
         "path": rel(behaviour_atoms_path),
         "sha256": sha256_file(behaviour_atoms_path)},
        {"role": "clause corpus (existence check)",
         "path": rel(clauses_path), "sha256": sha256_file(clauses_path)},
    ]
    return {
        "artifact": "shape_partition",
        "version": "v1",
        "spec": "S6_ADVERSARIAL_REVIEW.md finding B1",
        "join_key": {
            "function": "containment.dechain_name",
            "pricing_version": containment.PRICING_VERSION,
            "rejected": "grammar.stem_of",
            "why_rejected": (
                "stem_of strips polarity as well as the chain and would "
                "merge must_x with mustnot_x (containment.py:141). On these "
                "inputs the two keys disagree on the clauses listed in "
                "summary.divergent_under_stem_of, and stem_of would call "
                "every one of them shape_b."),
        },
        "shapes": {
            "shape_b": ("at least one existing clause-side atom's join key "
                        "is in some declared behaviour's query vocabulary "
                        "— re-selection, NOT new atoms"),
            "shape_a": ("no existing atom's join key is in any declared "
                        "query — the genuine addition case"),
            "shape_a_polarity_variant": (
                "a subset of shape_a: no atom in any query under the live "
                "join key, but an atom whose polarity-stripped stem is in "
                "some query. The only state whose membership depends on the "
                "join-key choice, and the highest duplicate risk in "
                "shape_a"),
        },
        "selection": {
            "cause": CENSUS_CAUSE,
            "census_dir": rel(census_dir),
            "census_file": CENSUS_FILE,
            "n_dossiers": n_dossiers,
            "clause_ids": clause_ids,
            "label_hygiene": LABEL_HYGIENE,
        },
        "inputs": inputs,
        "summary": {
            "n_clauses": len(rows),
            "by_shape": {s: sorted(by_shape[s]) for s in SHAPES},
            "n_by_shape": {s: len(by_shape[s]) for s in SHAPES},
            "divergent_under_stem_of": sorted(
                r["clause_id"] for r in rows if r["divergent_under_stem_of"]),
            "behaviours": index["behaviours"],
        },
        "clauses": rows,
    }


def build(out_path: str = DEFAULT_OUT, **kw) -> str:
    art = compute(**kw)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(art, f, indent=1, sort_keys=True)
        f.write("\n")
    return out_path


# ------------------------------------------------------------ the validator

def validate(path: str) -> list:
    """Return the sorted error list (empty == clean).

    The artifact is re-derived from its OWN recorded input paths and
    compared row for row, so a hand edit anywhere in the partition is a
    refusal. Input shas are checked against the files on disk: a drifted
    input is a refusal too, because a partition frozen at OPEN is only
    worth anything if the bytes it was computed from are still the bytes on
    disk.
    """
    with open(path) as f:
        art = json.load(f)
    errors = []
    if art.get("artifact") != "shape_partition":
        return [f"{os.path.basename(path)} is not a shape_partition artifact"]

    roles = {}
    for rec in art.get("inputs") or []:
        roles[rec.get("role", "")] = abspath(rec.get("path") or "")
        p = abspath(rec.get("path") or "")
        if not rec.get("path") or not os.path.exists(p):
            errors.append(f"declared input {p!r} is absent")
            continue
        live = sha256_file(p)
        if rec.get("sha256") != live:
            errors.append(
                f"input sha256 mismatch for {p}: artifact records "
                f"{rec.get('sha256')} but the file on disk is {live}")

    if art.get("join_key", {}).get("function") != "containment.dechain_name":
        errors.append("join_key.function is not containment.dechain_name — "
                      "the polarity-preserving key is the contract")

    errors.extend(check_payload(art.get("clauses") or []))
    sel = art.get("selection") or {}
    unknown_sel = sorted(set(sel) - set(SELECTION_FIELDS))
    if unknown_sel:
        errors.append(f"selection carries unknown fields {unknown_sel} — "
                      "the census contributes ids only")

    if errors:
        return sorted(set(errors))

    census_dir = abspath(sel.get("census_dir", CENSUS_DIR))
    paths = {}
    for role, p in roles.items():
        if role.startswith("clause-side"):
            paths["annotations_path"] = p
        elif role.startswith("behaviour"):
            paths["behaviour_atoms_path"] = p
        elif role.startswith("clause corpus"):
            paths["clauses_path"] = p
    try:
        fresh = compute(census_dir=census_dir, **paths)
    except PartitionError as exc:
        return [f"recomputation refused: {exc}"]
    for key in ("clauses", "summary", "selection"):
        if art.get(key) != fresh[key]:
            errors.append(
                f"artifact {key} does not match the recomputed partition — "
                "this artifact was hand-edited or its inputs moved")
    return sorted(set(errors))


# --------------------------------------------------------------------- CLI

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="shape_partition.py")
    sub = parser.add_subparsers(dest="mode", required=True)
    pb = sub.add_parser("build")
    pb.add_argument("--out", default=DEFAULT_OUT)
    pb.add_argument("--census-dir", default=CENSUS_DIR)
    pb.add_argument("--annotations", default=ANNOTATIONS)
    pb.add_argument("--behaviour-atoms", default=BEHAVIOUR_ATOMS)
    pb.add_argument("--clauses", default=CLAUSES)
    pv = sub.add_parser("validate")
    pv.add_argument("--path", default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    if args.mode == "build":
        out = build(out_path=args.out,
                    census_dir=args.census_dir,
                    annotations_path=args.annotations,
                    behaviour_atoms_path=args.behaviour_atoms,
                    clauses_path=args.clauses)
        with open(out) as f:
            art = json.load(f)
        print(json.dumps(art["summary"], indent=1, sort_keys=True))
        print(f"wrote {art['summary']['n_clauses']} clauses -> {out}")
        return 0

    errors = validate(args.path)
    if errors:
        for e in errors:
            print("FAIL:", e)
        print(f"validate: {len(errors)} error(s)")
        return 1
    with open(args.path) as f:
        art = json.load(f)
    print("validate: CLEAN —", json.dumps(art["summary"]["n_by_shape"],
                                          sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
