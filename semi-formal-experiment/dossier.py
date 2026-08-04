"""One flip → one self-contained case file — Unit 2 of the iteration loop.

WHY THIS EXISTS. Unit 1 turns two frozen snapshots into flip lists; this
module turns each flip into a dossier an adjudicator can decide WITHOUT
repo access — the Haiku-operability contract is "dossier in → verdict out,
no exploration required". So a dossier carries everything the document-side
question needs: the behaviour's definition and query atom names on both
sides, the full clause text with its section path, the clause's atoms, the
deterministic read-back rendering, explain() under BOTH configurations,
score and threshold before and after, the channel that moved most, and the
config-sha diff naming what changed. The companion `validate` subcommand
checks an adjudication file against the dossier set with check_taxonomy.py
discipline — full coverage, no dupes, no unknown ids, a closed verdict set,
a non-empty document_reason — so the loop's output is mechanical too.

WHAT THIS MODULE MUST NEVER DO. It is query-adjacent and PANEL-BLIND, under
the same fence as snapshot.py (test_no_reference_leak.py scans it forever).
A dossier holds NO panel fields: no gold, no judge labels, no panel score —
the adjudication it supports asks only "does this clause concern this
behaviour's subject matter, on a plain reading of the DOCUMENT". Its inputs
are exactly the artifacts the two snapshots recorded, resolved by sha: if a
recorded input has drifted on disk, building FAILS LOUDLY rather than pair
frozen scores with the wrong artifacts.

DETERMINISM CONTRACT. Same two snapshots → byte-identical dossier files and
index. Serialization goes through snapshot.snapshot_bytes; every float is
rounded to snapshot.PRECISION; no wall-clock, no randomness; flip_ids are
pure functions of (tag_a, tag_b, slug, clause_id, direction).

Usage:
    .venv/bin/python dossier.py dossiers --a baseline --b containment-v0
    .venv/bin/python dossier.py validate --dir dossiers/baseline__containment-v0 \
        --verdict-file adjudications.json
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys

import containment
import readback
import relevance
import snapshot

HERE = os.path.dirname(os.path.abspath(__file__))

#: Default root for written dossier sets: dossiers/<tagA>__<tagB>/.
DOSSIER_ROOT = os.path.join(HERE, "dossiers")

#: The closed verdict set (ITERATION_LOOP.md Unit 2). Anything else is a
#: schema violation, not a fourth opinion.
VERDICT_VALUES = ("correct", "regression", "unclear")

DIRECTIONS = ("newly_predicted", "no_longer_predicted")

#: Exposed so the repo's anti-cheat spy (test_no_reference_leak.py) can drive
#: this module's query surface — the same accommodation snapshot.py ships.
#: dossier has no scorer of its own; its query surface IS the scorer's.
Index = relevance.RelevanceIndex


class StaleConfigError(RuntimeError):
    """A snapshot's recorded input no longer matches the file on disk.

    Raised instead of building, because a dossier generated over drifted
    artifacts would pair one side's frozen scores with the OTHER
    configuration's clause text and atoms — the wrong case file, delivered
    confidently. Re-snapshot, or restore the recorded file.
    """


class ReconstructionMismatch(RuntimeError):
    """A rebuilt side's explain score contradicts the snapshot's frozen score.

    Every dossier is checked at build time: the side's index is rebuilt from
    the RECORDED configuration (including any recorded containment overlay),
    and the reconstructed explain score, rounded at snapshot.PRECISION, must
    equal the frozen score for that clause. A mismatch means the dossier
    would self-contradict — the 2026-08-03 review produced exactly that by
    rebuilding an overlay snapshot through a plain index — or the snapshot
    was hand-edited. Either way: raise loudly, never ship the case file.
    """


# ------------------------------------------------------------ reconstruction

def _resolve_inputs(snap: dict, inputs_dir: str) -> dict:
    """The snapshot's recorded inputs as verified on-disk paths.

    Every path is resolved (basenames against `inputs_dir`) and its sha256
    re-computed; any mismatch raises StaleConfigError naming the file and
    both hashes. No partial result: either every input is exactly the one
    the snapshot saw, or nothing is built.
    """
    out = {}
    for key in sorted(snap["config"]["inputs"]):
        rec = snap["config"]["inputs"][key]
        if rec is None:
            # an explicitly-null input (e.g. "overlay" when no containment
            # overlay was passed — Unit 4 records the absence so overlay-on
            # and overlay-off snapshots diff cleanly). Nothing to resolve.
            continue
        p = rec["path"]
        full = p if os.path.isabs(p) else os.path.join(inputs_dir, p)
        if not os.path.exists(full):
            raise StaleConfigError(
                f"snapshot {snap['tag']!r} records {key} = {p!r} but "
                f"{full} does not exist — cannot rebuild this side's index")
        actual = snapshot._sha256_file(full)
        if actual != rec["sha256"]:
            raise StaleConfigError(
                f"snapshot {snap['tag']!r} recorded {key} = {p!r} with "
                f"sha256 {rec['sha256'][:12]}… but the file on disk hashes "
                f"to {actual[:12]}… — the input CHANGED since the snapshot "
                f"was taken. Refusing to dossier against the wrong "
                f"artifacts; re-snapshot or restore the file.")
        out[key] = full
    return out


def _side(snap: dict, inputs_dir: str) -> dict:
    """One snapshot's configuration, rebuilt exactly: the scorer index, the
    behaviours with that side's query atoms, the clause rows, and the clause
    annotations (for the read-back rendering).

    When the snapshot RECORDS a containment overlay, the rebuild goes through
    ContainmentIndex with that overlay's validated edges — the overlay file is
    resolved and sha-verified by _resolve_inputs like every other input. A
    plain-index rebuild of an overlay snapshot produced explain numbers that
    silently contradicted the frozen scores (2026-08-03 review)."""
    paths = _resolve_inputs(snap, inputs_dir)
    rows = readback.load_clauses(paths["clauses"])
    if "overlay" in paths:
        index = containment.ContainmentIndex.from_files(
            clauses_path=paths["clauses"],
            annotations_path=paths["annotations"],
            edges=containment.load_edges(paths["overlay"]))
    else:
        index = relevance.RelevanceIndex.from_files(
            clauses_path=paths["clauses"],
            annotations_path=paths["annotations"])
    return {
        "paths": paths,
        "index": index,
        "behaviours": snapshot.load_behaviours(
            paths["behaviour_atoms"], paths["queries"]),
        "rows_by_id": {r["id"]: r for r in rows},
        "annotations": relevance.load_annotations(paths["annotations"]),
    }


def _rounded(x):
    """snapshot.PRECISION applied recursively — the same determinism measure
    Unit 1 takes, so explain() numbers cannot differ in the last ulp between
    two processes and break byte-identity."""
    if isinstance(x, float):
        return snapshot._r(x)
    if isinstance(x, (list, tuple)):
        return [_rounded(v) for v in x]
    if isinstance(x, dict):
        return {k: _rounded(v) for k, v in x.items()}
    return x


# ---------------------------------------------------------------- building

def flip_identifier(tag_a: str, tag_b: str, slug: str, clause_id: str,
                    direction: str) -> str:
    """Stable and deterministic: a pure function of the flip's coordinates,
    so re-generation never renumbers the casework."""
    return f"{tag_a}__{tag_b}__{slug}__{clause_id}__{direction}"


def _explain(side: dict, slug: str, clause_id: str) -> dict:
    beh = side["behaviours"].get(slug)
    if beh is None:
        return {}
    return _rounded(side["index"].explain(beh, clause_id))


def _query_atom_names(side: dict, slug: str) -> list:
    beh = side["behaviours"].get(slug)
    return sorted(beh.atom_names) if beh is not None else []


def _one_dossier(flip: dict, *, direction: str, slug: str,
                 snap_a: dict, snap_b: dict, side_a: dict, side_b: dict,
                 query_raw: dict, what_changed: dict) -> dict:
    cid = flip["clause_id"]
    # Clause text, atoms and rendering come from the AFTER side (the
    # configuration under decision); if the clause id only exists on the
    # before side (a clause-file change removed it), fall back so the
    # dossier still shows the text the flip is about.
    src = side_b if cid in side_b["rows_by_id"] else side_a
    row = src["rows_by_id"].get(cid, {})
    atoms = src["annotations"].get(cid, [])
    explains = {"a": _explain(side_a, slug, cid),
                "b": _explain(side_b, slug, cid)}
    # BUILD-TIME SELF-CHECK: the reconstructed side must reproduce the frozen
    # score at snapshot.PRECISION, or the dossier would self-contradict (the
    # failure mode the 2026-08-03 review demonstrated on overlay snapshots).
    for side_name, frozen in (("a", flip["score_a"]), ("b", flip["score_b"])):
        ex = explains[side_name]
        if not ex:
            continue
        if snapshot._r(ex["score"]) != snapshot._r(frozen):
            raise ReconstructionMismatch(
                f"clause {cid!r}, side {side_name} "
                f"(behaviour {slug!r}): reconstructed explain score "
                f"{ex['score']!r} != frozen score {frozen!r} at "
                f"PRECISION={snapshot.PRECISION}. The snapshot's recorded "
                f"configuration does not reproduce its own frozen numbers — "
                f"a hand-edited snapshot or a reconstruction bug. Refusing "
                f"to write a self-contradictory dossier.")
    return {
        "flip_id": flip_identifier(snap_a["tag"], snap_b["tag"], slug, cid,
                                   direction),
        "direction": direction,
        "tag_a": snap_a["tag"],
        "tag_b": snap_b["tag"],
        "behaviour": {
            "slug": slug,
            "name": query_raw.get("name", ""),
            "definition": query_raw.get("definition", ""),
            "query_atoms_a": _query_atom_names(side_a, slug),
            "query_atoms_b": _query_atom_names(side_b, slug),
        },
        "clause": {
            "id": cid,
            "text": row.get("quote", ""),
            "section_path": list(row.get("section_path") or []),
            "locator": row.get("locator", ""),
            "kind": row.get("kind", ""),
            "atoms": [{k: a.get(k, "") for k in
                       ("name", "kind", "gloss", "quote", "span_id",
                        "locator")} for a in atoms],
        },
        "rendering": readback.render(atoms, row.get("kind")),
        "explain_a": explains["a"],
        "explain_b": explains["b"],
        "score_a": flip["score_a"],
        "score_b": flip["score_b"],
        "threshold_a": flip["threshold_a"],
        "threshold_b": flip["threshold_b"],
        "top_channel": flip["top_channel"],
        "channel_delta": flip["channel_delta"],
        "cause": flip["cause"],
        "what_changed": what_changed,
    }


def build_dossiers(tag_a: str, tag_b: str, *, snap_dir: str | None = None,
                   inputs_dir: str | None = None,
                   behaviour: str | None = None) -> list:
    """Every flip in diff(tag_a, tag_b), each as one self-contained dossier.

    Both sides' indexes are reconstructed from the configuration each
    snapshot RECORDED (sha-verified — see StaleConfigError), never from
    whatever happens to be current, so explain_a/explain_b are the numbers
    those snapshots actually froze.
    """
    snap_dir = snap_dir or snapshot.SNAPSHOT_DIR
    inputs_dir = inputs_dir or HERE
    snap_a = snapshot.load_snapshot(os.path.join(snap_dir, f"{tag_a}.json"))
    snap_b = snapshot.load_snapshot(os.path.join(snap_dir, f"{tag_b}.json"))
    d = snapshot.diff_snapshots(snap_a, snap_b)

    side_a = _side(snap_a, inputs_dir)
    side_b = _side(snap_b, inputs_dir)

    # behaviour name/definition, from the query-side file of the AFTER
    # configuration (slug/name/definition only — the file that exists so
    # queries never open the evaluation artifacts)
    with open(side_b["paths"]["queries"]) as f:
        raw_queries = {(q.get("slug") or q.get("id") or ""): q
                       for q in json.load(f).get("behaviours", [])}

    what_changed = {
        "inputs_changed": d["config"]["changed"],
        "weights_changed": d["config"]["weights_changed"],
        "threshold_rule_changed": d["config"]["threshold_rule_changed"],
        "atoms_added": d["vocabulary"]["atoms_added"],
        "atoms_removed": d["vocabulary"]["atoms_removed"],
    }

    out = []
    for slug in sorted(d["behaviours"]):
        if behaviour and slug != behaviour:
            continue
        for direction in DIRECTIONS:
            for flip in d["behaviours"][slug][direction]:
                out.append(_one_dossier(
                    flip, direction=direction, slug=slug,
                    snap_a=snap_a, snap_b=snap_b,
                    side_a=side_a, side_b=side_b,
                    query_raw=raw_queries.get(slug, {}),
                    what_changed=what_changed))
    out.sort(key=lambda x: x["flip_id"])
    return out


# ------------------------------------------------------------- persistence

INDEX_NAME = "index.jsonl"


def write_dossiers(dossiers: list, out_dir: str) -> list:
    """One JSON file per dossier plus index.jsonl (one line per dossier:
    flip_id, behaviour, clause id, direction) so an operator can enumerate
    the work. Bytes go through snapshot.snapshot_bytes — byte-identity is a
    property of the content, never of the writer."""
    os.makedirs(out_dir, exist_ok=True)
    dossiers = sorted(dossiers, key=lambda x: x["flip_id"])
    paths = []
    for d in dossiers:
        path = os.path.join(out_dir, f"{d['flip_id']}.json")
        with open(path, "wb") as f:
            f.write(snapshot.snapshot_bytes(d))
        paths.append(path)
    lines = [json.dumps({"flip_id": d["flip_id"],
                         "behaviour": d["behaviour"]["slug"],
                         "clause_id": d["clause"]["id"],
                         "direction": d["direction"]}, sort_keys=True)
             for d in dossiers]
    with open(os.path.join(out_dir, INDEX_NAME), "w") as f:
        for line in lines:
            f.write(line + "\n")
    return paths


# --------------------------------------------------------------- validate

def _load_verdict_records(path: str) -> list:
    """The adjudication file: a JSON list of records, or a dict holding one
    list under any key (tolerant, like the repo's other loaders)."""
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in sorted(data):
            if isinstance(data[key], list):
                return data[key]
    return []


def validate(dossier_dir: str, verdict_path: str):
    """Check an adjudication file against a dossier set, mechanically.

    check_taxonomy.py discipline: coverage re-derived from the dossier index
    rather than believed, dupes and unknown ids surfaced, every count
    printed, and a one-word VERDICT line at the end. Hard requirements per
    record: flip_id known, verdict in the closed set, document_reason
    non-empty. Returns (ok, summary).
    """
    idx_path = os.path.join(dossier_dir, INDEX_NAME)
    with open(idx_path) as f:
        expected = [json.loads(line)["flip_id"]
                    for line in f if line.strip()]
    records = _load_verdict_records(verdict_path)

    seen = []
    malformed = 0
    bad_value = []
    empty_reason = []
    for rec in records:
        if not isinstance(rec, dict) or not rec.get("flip_id"):
            malformed += 1
            continue
        fid = rec["flip_id"]
        seen.append(fid)
        if rec.get("verdict") not in VERDICT_VALUES:
            bad_value.append(fid)
        reason = rec.get("document_reason")
        if not (isinstance(reason, str) and reason.strip()):
            empty_reason.append(fid)

    counts = collections.Counter(seen)
    dupes = sorted(k for k, v in counts.items() if v > 1)
    never = [fid for fid in expected if fid not in counts]
    unknown = sorted(set(seen) - set(expected))

    summary = {
        "expected": len(expected),
        "adjudicated": len(seen),
        "malformed": malformed,
        "never_adjudicated": never,
        "duplicated": dupes,
        "unknown": unknown,
        "bad_verdict": sorted(bad_value),
        "empty_reason": sorted(empty_reason),
    }
    ok = not (malformed or never or dupes or unknown
              or bad_value or empty_reason)

    print(f"--- {os.path.basename(verdict_path)} "
          f"vs {os.path.basename(os.path.abspath(dossier_dir))}")
    print(f"dossiers            {len(expected)}")
    print(f"adjudicated         {len(seen)}")
    print(f"malformed records   {malformed}")
    print(f"never adjudicated   {len(never)} {never[:5]}")
    print(f"duplicated ids      {len(dupes)} {dupes[:5]}")
    print(f"unknown ids         {len(unknown)} {unknown[:5]}")
    print(f"bad verdict value   {len(bad_value)} {sorted(bad_value)[:5]}")
    print(f"empty reason        {len(empty_reason)} "
          f"{sorted(empty_reason)[:5]}")
    print(f"VERDICT             {'clean' if ok else 'DISCREPANCIES ABOVE'}")
    return ok, summary


# -------------------------------------------------------------------- CLI

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="dossier.py",
        description="one flip → one self-contained case file; validate an "
                    "adjudication file against a dossier set "
                    "(ITERATION_LOOP.md Unit 2)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pd = sub.add_parser("dossiers", help="write one dossier per flip in "
                                         "diff(a, b), plus index.jsonl")
    pd.add_argument("--a", required=True)
    pd.add_argument("--b", required=True)
    pd.add_argument("--behaviour", default=None,
                    help="restrict to this behaviour slug")
    pd.add_argument("--snap-dir", default=snapshot.SNAPSHOT_DIR)
    pd.add_argument("--inputs-dir", default=HERE,
                    help="directory the snapshots' recorded input paths "
                         "resolve against")
    pd.add_argument("--out-dir", default=None,
                    help="default: dossiers/<a>__<b>/")

    pv = sub.add_parser("validate", help="check an adjudication file "
                                         "against a dossier directory")
    pv.add_argument("--dir", required=True)
    pv.add_argument("--verdict-file", required=True)

    args = parser.parse_args(argv)

    if args.cmd == "dossiers":
        out_dir = args.out_dir or os.path.join(
            DOSSIER_ROOT, f"{args.a}__{args.b}")
        try:
            ds = build_dossiers(args.a, args.b, snap_dir=args.snap_dir,
                                inputs_dir=args.inputs_dir,
                                behaviour=args.behaviour)
        except StaleConfigError as e:
            print(f"STALE CONFIGURATION: {e}", file=sys.stderr)
            return 2
        write_dossiers(ds, out_dir)
        if not ds:
            print(f"no flips between {args.a!r} and {args.b!r} — nothing "
                  f"to adjudicate (empty {INDEX_NAME} written)")
        else:
            for d in ds:
                print(f"{d['flip_id']}  ({d['top_channel']} "
                      f"{d['channel_delta']:+.4f})")
            print(f"wrote {len(ds)} dossiers to {out_dir}")
        return 0

    ok, _ = validate(args.dir, args.verdict_file)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
