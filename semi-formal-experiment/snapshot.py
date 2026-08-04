"""Freeze, diff, flip list — Unit 1 of the iteration loop (ITERATION_LOOP.md).

WHY THIS EXISTS. The inner loop is "change → rerun → see what newly succeeds
or fails → debug each flip → keep or revert". That is only cheap and only
honest if "see what changed" is a mechanical comparison of two frozen tool
outputs — yesterday's snapshot vs today's — rather than a rerun eyeballed
against memory. A snapshot records, for every behaviour with query atoms,
exactly what the scorer said and under exactly which configuration it said
it; a diff turns two snapshots into flip lists (which clauses became
predicted, which stopped) with the score movement and the channel that moved
most, so each flip can be adjudicated one at a time against the DOCUMENT.

WHAT THIS MODULE MUST NEVER DO. It is query-adjacent and PANEL-BLIND, under
the same fence as the query modules (test_no_reference_leak.py scans it
forever). Its diff object is tool-vs-tool — a fact about the tool, never
about any gold. It may read only the declared query-side inputs: the clause
file, the clause annotations, the behaviour-atom artifact, and the query-side
behaviour file (slug/name/definition — the file that exists precisely so
queries never open the reference). No score, threshold, or flip in a snapshot
may be derived from, compared against, or selected on the evaluation
reference; keep/revert decisions cite document-side evidence only.

DETERMINISM CONTRACT. Same inputs → byte-identical snapshot file. No
wall-clock timestamps, no randomness, dict keys sorted on dump, sets
serialized as sorted lists. The tag is caller-supplied and is the only thing
distinguishing two snapshots of the same configuration — which the diff then
reports explicitly as a no-op rather than as silently empty flip lists.

Usage:
    .venv/bin/python snapshot.py snapshot --tag baseline
    .venv/bin/python snapshot.py diff --a baseline --b containment-v0 [--json out.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import relevance
import threshold as threshold_rules

HERE = os.path.dirname(os.path.abspath(__file__))

#: Default inputs — the b8 pairing, the current PREFERRED artifacts.
ANNOTATIONS = os.path.join(HERE, "annotations_b8.json")
BEHAVIOUR_ATOMS = os.path.join(HERE, "behavior_atoms_b8.json")
CLAUSES = os.path.join(HERE, "modelspec_clauses.json")
#: The QUERY-SIDE behaviour file: slug, name, definition only. This is the
#: file relevance.main reads for the same reason — the reference lives
#: elsewhere and this module must never open it.
QUERIES = os.path.join(HERE, "behaviours_query.json")

SNAPSHOT_DIR = os.path.join(HERE, "snapshots")

#: Exposed so the repo's anti-cheat spy (test_no_reference_leak.py) can drive
#: this module's query surface — the same accommodation readback.py ships.
#: snapshot has no scorer of its own; its query surface IS the scorer's.
Index = relevance.RelevanceIndex


# ---------------------------------------------------------------- hashing

def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_obj(obj) -> str:
    """Content hash of a JSON-serializable object, key-order independent."""
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True).encode()).hexdigest()


#: Decimal places every recorded score is rounded to. This is a DETERMINISM
#: measure, not cosmetics: the scorer's atom channel sums IDF terms in the
#: iteration order of a set of strings, which varies with the per-process
#: hash seed — so the same inputs produce sums differing in the last ulp
#: (~1e-16 relative, ≲1e-14 absolute here) from one process to the next, and
#: "byte-identical snapshot" fails across processes. 1e-10 is far above that
#: noise and far below any movement worth a flip dossier (real flips move
#: ≥1e-3). Threshold and predicted set are derived FROM the rounded scores so
#: the snapshot stays internally consistent.
PRECISION = 10


def _r(x: float) -> float:
    # `+ 0.0` normalizes -0.0 → 0.0 so the serialized text is stable too.
    return round(float(x), PRECISION) + 0.0


# --------------------------------------------------------------- building

def load_behaviours(atoms_path: str = BEHAVIOUR_ATOMS,
                    queries_path: str = QUERIES) -> dict:
    """`{slug: Behaviour}` for every query-side behaviour WITH query atoms.

    Names and definitions come from the query-side behaviour file; atoms from
    the behaviour-atom artifact. A behaviour without atoms is excluded rather
    than snapshotted as a lexical baseline: a flip list over a degraded
    scorer would be adjudicated as if it were the tool's.
    """
    with open(queries_path) as f:
        queries = json.load(f)
    atoms = relevance.load_behaviour_atoms(atoms_path)
    out = {}
    for raw in queries.get("behaviours", []):
        slug = raw.get("slug") or raw.get("id") or ""
        if slug and atoms.get(slug):
            out[slug] = relevance.behaviour_from_panel(raw, atoms)
    return out


def load_frozen_thresholds(path: str) -> dict:
    """`{slug: cut}` from a frozen-thresholds artifact — per-behaviour cut
    VALUES frozen from a named baseline snapshot's own label-free derivation,
    so future score-changing cycles cannot move them (the m0422
    threshold_drift escalation). The artifact carries its own provenance;
    this loader reads only the `thresholds` map."""
    with open(path) as f:
        raw = json.load(f)
    return {slug: float(v)
            for slug, v in (raw.get("thresholds") or {}).items()}


def build_snapshot(tag: str, *,
                   annotations_path: str = ANNOTATIONS,
                   atoms_path: str = BEHAVIOUR_ATOMS,
                   clauses_path: str = CLAUSES,
                   queries_path: str = QUERIES,
                   overlay_path: str | None = None,
                   thresholds_path: str | None = None) -> dict:
    """One frozen record of what the scorer says under this configuration.

    Per behaviour: normalized per-clause scores (the numbers the threshold
    cuts), unnormalized raw scores, the per-clause channel decomposition, the
    label-free derived threshold, and the predicted set AT that threshold.
    Plus vocabulary stats and the sha identity of every input, so a diff can
    name what changed instead of guessing.

    `overlay_path` is the OPT-IN containment overlay (ITERATION_LOOP.md
    Unit 4): when given, scoring runs through ContainmentIndex with that
    file's validated edges, and the file's sha joins the config identity
    under the key "overlay" — recorded as an explicit null when absent, so
    overlay-on and overlay-off snapshots diff cleanly instead of differing
    by a missing key. There is no default overlay; None means none.

    `thresholds_path` is the OPT-IN frozen-thresholds artifact (the
    versioned-cut fix answering the m0422 threshold_drift escalation): when
    given, a behaviour named in the artifact takes its cut FROM the artifact
    instead of re-deriving it, a behaviour absent from it falls back to the
    rule, and each behaviour records which happened under
    `threshold_source` ("frozen_artifact" | "rule_fallback"). The artifact's
    sha joins the config identity under "thresholds" — an explicit null when
    absent, exactly the overlay pattern — so the OLD behavior stays reachable
    by omitting the flag and reconstructs from the recorded config
    (amendment F9's version dispatch). The predicted set uses predict()'s
    decision rule (strictly positive AND at-or-above the cut) either way.
    """
    frozen_cuts = (load_frozen_thresholds(thresholds_path)
                   if thresholds_path else None)
    if overlay_path:
        import containment
        idx = containment.ContainmentIndex.from_files(
            clauses_path=clauses_path, annotations_path=annotations_path,
            edges=containment.load_edges(overlay_path))
    else:
        idx = relevance.RelevanceIndex.from_files(
            clauses_path=clauses_path, annotations_path=annotations_path)
    behaviours = load_behaviours(atoms_path, queries_path)

    per_behaviour = {}
    for slug in sorted(behaviours):
        beh = behaviours[slug]
        channels = idx.channel_scores(beh)
        true_raw = {cid: sum(c.values()) for cid, c in channels.items()}
        top = max(true_raw.values(), default=0.0)
        # normalized exactly as rank() normalizes — these are the numbers the
        # threshold is applied to, so these are the numbers recorded (rounded
        # per the PRECISION note: determinism, not cosmetics)
        scores = {cid: _r(v / top if top > 0 else 0.0)
                  for cid, v in true_raw.items()}

        # the operating point. Default path: the label-free preferred rule,
        # derived exactly as predict(None) derives it — over this query's
        # positive RECORDED (rounded) scores, so recorded threshold and
        # recorded scores can never disagree at the last ulp. Frozen path:
        # the artifact's cut for this behaviour, with the rule as recorded
        # fallback for behaviours the artifact does not name.
        source = None
        if frozen_cuts is not None and slug in frozen_cuts:
            cut = _r(frozen_cuts[slug])
            source = "frozen_artifact"
        else:
            positives = [s for s in scores.values() if s > 0]
            cut = _r(threshold_rules.apply_rule(threshold_rules.PREFERRED,
                                                positives)
                     if positives else 0.0)
            if frozen_cuts is not None:
                source = "rule_fallback"
        # honored on the recorded numbers, with predict()'s exact decision
        # rule (strictly positive AND at-or-above the cut)
        predicted = {cid for cid, s in scores.items() if s > 0 and s >= cut}

        per_behaviour[slug] = {
            "threshold": cut,
            "predicted": sorted(predicted),
            "scores": scores,
            "raw": {cid: _r(v) for cid, v in true_raw.items()},
            "channels": {cid: {ch: _r(v) for ch, v in channels[cid].items()}
                         for cid in channels},
        }
        if source is not None:
            per_behaviour[slug]["threshold_source"] = source

    weights = {k: getattr(idx.weights, k)
               for k in sorted(vars(idx.weights))}
    df = {name: int(n) for name, n in idx.atom_df.items()}
    config = {
        "inputs": {
            "annotations": {"path": os.path.basename(annotations_path),
                            "sha256": _sha256_file(annotations_path)},
            "behaviour_atoms": {"path": os.path.basename(atoms_path),
                                "sha256": _sha256_file(atoms_path)},
            "clauses": {"path": os.path.basename(clauses_path),
                        "sha256": _sha256_file(clauses_path)},
            "queries": {"path": os.path.basename(queries_path),
                        "sha256": _sha256_file(queries_path)},
            "overlay": ({"path": os.path.basename(overlay_path),
                         "sha256": _sha256_file(overlay_path)}
                        if overlay_path else None),
            "thresholds": ({"path": os.path.basename(thresholds_path),
                            "sha256": _sha256_file(thresholds_path)}
                           if thresholds_path else None),
        },
        "weights": weights,
        "threshold_rule": threshold_rules.PREFERRED,
    }
    if overlay_path:
        # An active overlay means containment.py's pricing rules scored this
        # snapshot: record their version in the config identity, so a
        # scoring-rule change under identical inputs produces a diff that can
        # name its own cause. Absent when no overlay is — the base scorer's
        # rules are not containment's to version (same pattern as the
        # overlay key itself).
        config["pricing_version"] = containment.PRICING_VERSION
    return {
        "tag": tag,
        "config": config,
        "vocabulary": {
            "atom_count": len(df),
            "df": df,
            "df_sha256": _sha256_obj(df),
            "stopword_count": len(idx.atom_stopwords),
        },
        "behaviours": per_behaviour,
    }


# ------------------------------------------------------------ persistence

def snapshot_bytes(snap: dict) -> bytes:
    """THE canonical serialization — sorted keys, fixed separators, trailing
    newline. Every write goes through here so byte-identity is a property of
    the content, never of the writer."""
    return (json.dumps(snap, sort_keys=True, indent=1,
                       ensure_ascii=False) + "\n").encode("utf-8")


def write_snapshot(snap: dict, out_dir: str = SNAPSHOT_DIR, *,
                   force: bool = False) -> str:
    """Write snapshots/<tag>.json — NO-CLOBBER by default (TOOLING item 2).

    Snapshot tags are immutable baselines (amendment F3): overwriting one
    with different bytes destroys the artifact another cycle's dossiers
    resolve against. The driver refuses tag reuse, but a bare CLI call used
    to clobber silently — so the refusal lives HERE, in the writer itself:

      * target absent            → write;
      * target byte-identical    → silent no-op success (rewrite changes
        nothing, so nothing is written);
      * target differs, no force → SystemExit naming the tag and BOTH shas;
      * target differs, force    → overwrite, both shas printed to stdout
        (the driver never passes force; a forced clobber is always said).
    """
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{snap['tag']}.json")
    new = snapshot_bytes(snap)
    if os.path.exists(path):
        with open(path, "rb") as f:
            old = f.read()
        if old == new:
            return path
        old_sha = hashlib.sha256(old).hexdigest()
        new_sha = hashlib.sha256(new).hexdigest()
        if not force:
            raise SystemExit(
                f"REFUSING to overwrite snapshot tag {snap['tag']!r} at "
                f"{path}: the file on disk has sha256 {old_sha} but this "
                f"build serializes to sha256 {new_sha}. Snapshot tags are "
                f"immutable baselines (amendment F3) — pick a fresh tag, or "
                f"pass --force to overwrite ON THE RECORD.")
        print(f"FORCED OVERWRITE of snapshot tag {snap['tag']!r}: "
              f"sha256 {old_sha} -> {new_sha}")
    with open(path, "wb") as f:
        f.write(new)
    return path


def load_snapshot(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def assert_frozen_thresholds(snapshot_path: str) -> None:
    """Gate-style guard (CYCLE5_REVIEW.md MUST item 6): every behaviour in
    the snapshot at `snapshot_path` must record
    `threshold_source == "frozen_artifact"` — its cut came FROM the frozen-
    thresholds artifact, not from the per-snapshot derivation rule. A
    behaviour on `rule_fallback` (the artifact did not name it) or with no
    `threshold_source` key at all (built without --thresholds) silently
    re-derives its cut — exactly the m0422 threshold_drift class the
    versioned-cut fix froze out. Raises AssertionError naming the offending
    behaviours and what each recorded; returns None when fully frozen.

    Housed here (not in cycle.py) because this module owns the
    `threshold_source` key and is panel-blind, so gate tests anywhere —
    including query-side ones — can import it without touching the fenced
    driver."""
    snap = load_snapshot(snapshot_path)
    offending = {
        slug: beh.get("threshold_source", "absent (rule-derived, old shape)")
        for slug, beh in sorted((snap.get("behaviours") or {}).items())
        if beh.get("threshold_source") != "frozen_artifact"}
    if offending:
        raise AssertionError(
            f"snapshot {snap.get('tag')!r} ({snapshot_path}) is NOT fully "
            f"frozen — threshold_source != 'frozen_artifact' for: "
            + "; ".join(f"{slug}: {src}" for slug, src in offending.items())
            + ". These behaviours re-derived their cut from the rule "
            "(m0422 threshold_drift; CYCLE5_REVIEW.md item 6).")


# ----------------------------------------------------------------- diffing

def _flip_record(cid, ba, bb):
    """One flipped clause: scores and thresholds on both sides, plus the
    channel whose contribution moved the most (by absolute delta) — the first
    question an adjudicator asks is "what pushed it" — plus the flip's
    `cause`, compared at PRECISION:

      * "match_change"    — the clause's own score moved (cut did not);
      * "threshold_drift" — the score is identical, only the cut moved. The
        adjudication question for these is about the THRESHOLD, not the
        clause (ITERATION_LOOP.md policy §3);
      * "both"            — score and cut both moved.

    A flip with neither moved is impossible for snapshots the builder wrote
    (identical scores + identical cut ⇒ identical predicted set), so the
    else-branch below can only mean the cut moved.
    """
    ch_a = (ba.get("channels") or {}).get(cid) or {}
    ch_b = (bb.get("channels") or {}).get(cid) or {}
    deltas = {ch: ch_b.get(ch, 0.0) - ch_a.get(ch, 0.0)
              for ch in sorted(set(ch_a) | set(ch_b))}
    top = (max(sorted(deltas), key=lambda ch: abs(deltas[ch]))
           if deltas else "")
    score_a = (ba.get("scores") or {}).get(cid, 0.0)
    score_b = (bb.get("scores") or {}).get(cid, 0.0)
    threshold_a = ba.get("threshold", 0.0)
    threshold_b = bb.get("threshold", 0.0)
    score_moved = _r(score_a) != _r(score_b)
    cut_moved = _r(threshold_a) != _r(threshold_b)
    if score_moved and cut_moved:
        cause = "both"
    elif score_moved:
        cause = "match_change"
    else:
        cause = "threshold_drift"
    return {
        "clause_id": cid,
        "score_a": score_a,
        "score_b": score_b,
        "threshold_a": threshold_a,
        "threshold_b": threshold_b,
        "top_channel": top,
        "channel_delta": deltas.get(top, 0.0),
        "cause": cause,
    }


def diff_snapshots(a: dict, b: dict) -> dict:
    """Everything that changed between two snapshots, mechanically.

    Per behaviour: the two flip lists. Plus which input shas changed, which
    weights changed, and the vocabulary delta (atoms added/removed, df
    shifts). `noop` is True only when the config identity AND every score are
    identical — reported explicitly so an unchanged rerun never reads as
    "the diff found nothing" by accident.
    """
    ins_a = a["config"]["inputs"]
    ins_b = b["config"]["inputs"]
    changed = sorted(k for k in set(ins_a) | set(ins_b)
                     if (ins_a.get(k) or {}).get("sha256")
                     != (ins_b.get(k) or {}).get("sha256"))
    weights_changed = {
        k: [a["config"]["weights"].get(k), b["config"]["weights"].get(k)]
        for k in sorted(set(a["config"]["weights"])
                        | set(b["config"]["weights"]))
        if a["config"]["weights"].get(k) != b["config"]["weights"].get(k)}
    rule_changed = (a["config"]["threshold_rule"]
                    != b["config"]["threshold_rule"])

    df_a = a["vocabulary"]["df"]
    df_b = b["vocabulary"]["df"]
    vocab = {
        "atom_count_a": a["vocabulary"]["atom_count"],
        "atom_count_b": b["vocabulary"]["atom_count"],
        "atoms_added": sorted(set(df_b) - set(df_a)),
        "atoms_removed": sorted(set(df_a) - set(df_b)),
        "df_shifted": {n: [df_a[n], df_b[n]]
                       for n in sorted(set(df_a) & set(df_b))
                       if df_a[n] != df_b[n]},
        "df_sha_changed": (a["vocabulary"]["df_sha256"]
                           != b["vocabulary"]["df_sha256"]),
    }

    behaviours = {}
    scores_identical = True
    # A no-op also requires identical CUTS and PREDICTIONS. Scores alone are
    # not enough: a code-level threshold change under identical scores flips
    # clauses (34 of them, measured live on the real baseline) — reporting
    # that as "no-op change" would hide exactly the threshold_drift class the
    # cause tag exists to make adjudicable.
    cuts_identical = True
    for slug in sorted(set(a["behaviours"]) | set(b["behaviours"])):
        ba = a["behaviours"].get(slug) or {}
        bb = b["behaviours"].get(slug) or {}
        if ba.get("scores") != bb.get("scores"):
            scores_identical = False
        if (ba.get("threshold") != bb.get("threshold")
                or (ba.get("predicted") or []) != (bb.get("predicted") or [])):
            cuts_identical = False
        pa, pb = set(ba.get("predicted") or []), set(bb.get("predicted") or [])
        behaviours[slug] = {
            "newly_predicted": [_flip_record(c, ba, bb)
                                for c in sorted(pb - pa)],
            "no_longer_predicted": [_flip_record(c, ba, bb)
                                    for c in sorted(pa - pb)],
            "threshold_a": ba.get("threshold"),
            "threshold_b": bb.get("threshold"),
            "predicted_count_a": len(pa),
            "predicted_count_b": len(pb),
        }

    noop = (not changed and not weights_changed and not rule_changed
            and scores_identical and cuts_identical)
    return {
        "tag_a": a["tag"],
        "tag_b": b["tag"],
        "noop": noop,
        "config": {"changed": changed,
                   "weights_changed": weights_changed,
                   "threshold_rule_changed": rule_changed},
        "vocabulary": vocab,
        "behaviours": behaviours,
    }


def format_diff(d: dict) -> str:
    """The human-readable report the inner loop reads before adjudicating."""
    lines = [f"# diff {d['tag_a']} -> {d['tag_b']}"]
    if d["noop"]:
        # "allowing absent==null keys": a config key newer snapshots record
        # as an explicit null (overlay, thresholds) may be entirely absent
        # from an older snapshot — null-equal, not byte-identical, and still
        # the same configuration (versioned-cut-2026-08-04 first-customer
        # finding).
        lines.append(
            "no-op change: identical configuration (allowing absent==null "
            "keys) and identical scores — the two snapshots differ only in "
            "tag.")
        return "\n".join(lines) + "\n"

    cfg = d["config"]
    if cfg["changed"]:
        lines.append(f"inputs changed: {', '.join(cfg['changed'])}")
    if cfg["weights_changed"]:
        for k, (va, vb) in sorted(cfg["weights_changed"].items()):
            lines.append(f"weight {k}: {va} -> {vb}")
    if cfg["threshold_rule_changed"]:
        lines.append("threshold rule changed")
    if not (cfg["changed"] or cfg["weights_changed"]
            or cfg["threshold_rule_changed"]):
        lines.append("config identity unchanged (a code-level change moved "
                     "the scores)")

    v = d["vocabulary"]
    lines.append(f"vocabulary: {v['atom_count_a']} -> {v['atom_count_b']} "
                 f"atoms; +{len(v['atoms_added'])} "
                 f"-{len(v['atoms_removed'])}; "
                 f"{len(v['df_shifted'])} df shifts")
    for name in v["atoms_added"]:
        lines.append(f"  + {name}")
    for name in v["atoms_removed"]:
        lines.append(f"  - {name}")

    for slug, beh in sorted(d["behaviours"].items()):
        lines.append(f"\n## {slug}  (threshold {beh['threshold_a']} -> "
                     f"{beh['threshold_b']}; predicted "
                     f"{beh['predicted_count_a']} -> "
                     f"{beh['predicted_count_b']})")
        if not beh["newly_predicted"] and not beh["no_longer_predicted"]:
            lines.append("  no flips")
        for label, flips in (("NEWLY PREDICTED", beh["newly_predicted"]),
                             ("NO LONGER PREDICTED",
                              beh["no_longer_predicted"])):
            for f in flips:
                lines.append(
                    f"  {label}: {f['clause_id']}  "
                    f"score {f['score_a']:.4f} -> {f['score_b']:.4f}  "
                    f"(cut {f['threshold_a']:.4f} -> "
                    f"{f['threshold_b']:.4f}; moved most: "
                    f"{f['top_channel']} {f['channel_delta']:+.4f}; "
                    f"cause: {f['cause']})")
    return "\n".join(lines) + "\n"


# -------------------------------------------------------------------- CLI

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="snapshot.py",
        description="freeze the scorer's outputs; diff two freezes into "
                    "flip lists (ITERATION_LOOP.md Unit 1)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_inputs(p):
        p.add_argument("--annotations", default=ANNOTATIONS)
        p.add_argument("--atoms", default=BEHAVIOUR_ATOMS)
        p.add_argument("--clauses", default=CLAUSES)
        p.add_argument("--queries", default=QUERIES)
        p.add_argument("--dir", default=SNAPSHOT_DIR,
                       help="snapshot directory")

    ps = sub.add_parser("snapshot", help="write snapshots/<tag>.json")
    ps.add_argument("--tag", required=True)
    ps.add_argument("--overlay", default=None,
                    help="opt-in containment overlay (licensed edges); "
                         "absent means none, recorded as null")
    ps.add_argument("--thresholds", default=None,
                    help="opt-in frozen-thresholds artifact (per-behaviour "
                         "cut values, label-free provenance); absent means "
                         "rule-derived cuts, recorded as null")
    ps.add_argument("--force", action="store_true",
                    help="overwrite an existing snapshots/<tag>.json whose "
                         "bytes differ (refused by default — amendment F3; "
                         "both shas are printed when forced)")
    add_inputs(ps)

    pd = sub.add_parser("diff", help="flip lists between two tags")
    pd.add_argument("--a", required=True)
    pd.add_argument("--b", required=True)
    pd.add_argument("--dir", default=SNAPSHOT_DIR)
    pd.add_argument("--json", default=None,
                    help="also write the machine-readable diff here")

    args = parser.parse_args(argv)

    if args.cmd == "snapshot":
        snap = build_snapshot(args.tag,
                              annotations_path=args.annotations,
                              atoms_path=args.atoms,
                              clauses_path=args.clauses,
                              queries_path=args.queries,
                              overlay_path=args.overlay,
                              thresholds_path=args.thresholds)
        path = write_snapshot(snap, out_dir=args.dir, force=args.force)
        for slug in sorted(snap["behaviours"]):
            beh = snap["behaviours"][slug]
            print(f"{slug}: {len(beh['predicted'])} clauses predicted "
                  f"at threshold {beh['threshold']:.4f}")
        print(f"wrote {path}")
        return 0

    a = load_snapshot(os.path.join(args.dir, f"{args.a}.json"))
    b = load_snapshot(os.path.join(args.dir, f"{args.b}.json"))
    d = diff_snapshots(a, b)
    sys.stdout.write(format_diff(d))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(d, f, sort_keys=True, indent=1)
            f.write("\n")
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
