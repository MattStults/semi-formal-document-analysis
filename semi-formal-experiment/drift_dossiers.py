"""STRIPPED dossiers for the drift-standing adjudication pass (option (a) of
DRIFT_STANDING_DESIGN.md §3) — producer + validator.

WHAT THIS IS. The census (`audit_dossiers/ext_v1_merged__audit_v1/
verdicts_merged.json`) attributed 59 disagreements to `fp_threshold_drift`
and 1 to `fn_threshold` — the standing near-cut population of the frozen
label-free cut (`thresholds_frozen.json` v1). The design's adjudicate-and-
accept pass runs a NEW label-blind seat (`briefs/drift_standing.md`) over
those 60 cases. The EXISTING audit dossiers are panel-contaminated BY DESIGN
(they carry panel scores and per-judge verdicts) and must never reach that
seat — so this module regenerates each case as a STRIPPED dossier holding
only document-side and tool-side facts:

  behaviour name / definition / query atoms (with glosses);
  clause id, full text, section_path, locator, clause kind;
  the clause's atoms with glosses, and the deterministic read-back rendering;
  explain() under the CURRENT keep configuration (annotations_ext_v1_merged
  + behavior_atoms_audit_v1, overlay null): channels, channel shares,
  matched atoms, top lexical terms;
  the frozen cut, the clause's normalized score, and distance-to-cut.

NO panel verdicts, NO panel scores, NO cause labels, NO side attributions,
NO passage quotes. A recursive banned-key schema check enforces that at
generation AND validation time.

FENCE — DIAGNOSTIC-ONLY, LABEL-DIRECTED ATTENTION. This module reads the
census verdict file, but ONLY to extract the 60-case id list (cause in
{fp_threshold_drift, fn_threshold}); no panel value flows into any output
byte. Under ITERATION_LOOP.md §1 that id list is label-directed ATTENTION —
legitimate, disclosed in the assignment artifacts' provenance blocks, and
firewalled from anything that sets a number. `drift_dossiers` is a FORBIDDEN
token in test_no_reference_leak.py (like audit_disagreements /
diagnose_disagreement): no query module may import it, and nothing under
drift_standing/ may be read at query time. The seat's verdicts are
DISCLOSURE-ONLY case law (design §3, "What may never flow from it"): no
exclusion lists, no post-filters, no outcome pins, no threshold or weight
edit may cite them.

PINNED GENERATION CONFIG (design §3, amended per PORTFOLIO_REVIEW): the
index.jsonl header is a config_identity record carrying every input's
sha256 (annotations, behaviour atoms, queries file, clauses file, the
thresholds_frozen artifact), the threshold rule, explicit overlay null,
pricing_version null (no overlay active) and join_version null (F12
placeholder) — so the dossiers are reproducible bytes, not "the frozen
config" by reputation. `validate` refuses a headerless directory.

DETERMINISM. Sorted keys, floats rounded to 6 dp, no wall clock: same
inputs give the same bytes (checked by double-generation diff at build).

TEST DEBT, stated: targeted tests live in test_drift_dossiers.py
(registered in conftest._OPTIONAL). They cover the validator (coverage
exactly-once, closed verdict/confidence sets, non-empty reasons, headerless
refusal) and the banned-key fence with synthetic fixtures; the generation
path is exercised by inline self-checks at build time (case-list counts
59+1, |distance_to_cut| <= 0.10, sign-vs-family agreement, banned-key scan
per dossier) rather than by a hermetic unit test, because it requires the
full artifact set.

Usage:
    .venv/bin/python drift_dossiers.py dossiers
    .venv/bin/python drift_dossiers.py validate \
        --verdicts drift_standing/verdicts_leg_a.json \
        --dossier-dir drift_standing/dossiers
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))

#: The CURRENT keep configuration (thresholds_frozen.json provenance block:
#: annotations_ext_v1_merged + behavior_atoms_audit_v1, overlay null).
ANNOTATIONS = os.path.join(HERE, "annotations_ext_v1_merged.json")
BEHAVIOUR_ATOMS = os.path.join(HERE, "behavior_atoms_audit_v1.json")
QUERIES = os.path.join(HERE, "behaviours_query.json")
THRESHOLDS = os.path.join(HERE, "thresholds_frozen.json")

#: The census this pass's ATTENTION derives from (never its truth).
CENSUS_DIR = os.path.join(HERE, "audit_dossiers", "ext_v1_merged__audit_v1")
CENSUS_VERDICTS = os.path.join(CENSUS_DIR, "verdicts_merged.json")
CENSUS_INDEX = os.path.join(CENSUS_DIR, "index.jsonl")

#: The two threshold-family cause labels whose cases this pass adjudicates.
CASE_CAUSES = ("fn_threshold", "fp_threshold_drift")

#: Pinned expected census composition (design, amended per F13): 59 + 1.
EXPECTED_BY_CAUSE = {"fp_threshold_drift": 59, "fn_threshold": 1}

OUT_DIR = os.path.join(HERE, "drift_standing", "dossiers")

CONFIG_TAG = "ext_v1_merged__audit_v1__frozen_v1"

#: The seat's CLOSED verdict set (design §3 output schema).
VERDICT_VALUES = ("admit_defensible", "admit_not_needed", "unclear")
CONFIDENCE_VALUES = ("high", "medium", "low")

#: Keys that must never appear ANYWHERE in a stripped dossier. `passage`
#: (and its quote) is banned too: passage selection is panel-side.
BANNED_KEYS = frozenset({
    "panel_score", "verdicts", "verdict", "cause", "side", "judge",
    "judges", "gold", "sweep_core_evidence", "passage", "panel",
})


def _round(x: float) -> float:
    return round(float(x), 6) + 0.0


# -------------------------------------------------------------- fence check

def banned_key_hits(obj, path="") -> list:
    """Every (json-path, key) in `obj` whose key is banned or contains
    'panel'. Recursive over dicts/lists; values are never scanned (clause
    text may legitimately contain any word — the fence is on FIELDS)."""
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            where = f"{path}.{k}" if path else k
            if k in BANNED_KEYS or "panel" in k.lower():
                hits.append(where)
            hits.extend(banned_key_hits(v, where))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(banned_key_hits(v, f"{path}[{i}]"))
    return hits


# ---------------------------------------------------------------- case list

def case_list() -> list:
    """The 60 standing threshold-family cases, as
    [{dossier_id, behaviour, pid, cause}], sorted by dossier_id.

    `cause` stays IN MEMORY for generation-time self-checks only — it is
    never written into any dossier or index record. Counts are pinned to
    the design's 59 + 1; a drifted census fails loudly here rather than
    silently changing the adjudicated set.
    """
    with open(CENSUS_VERDICTS) as f:
        verdicts = json.load(f)
    causes = {v["dossier_id"]: v["cause"] for v in verdicts
              if v.get("cause") in CASE_CAUSES}
    got = Counter(causes.values())
    assert dict(got) == EXPECTED_BY_CAUSE, (
        f"census composition drifted: expected {EXPECTED_BY_CAUSE}, "
        f"got {dict(got)} — re-read DRIFT_STANDING_DESIGN.md before "
        f"regenerating this pass")
    out = []
    with open(CENSUS_INDEX) as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            did = r.get("dossier_id")
            if did in causes:
                out.append({"dossier_id": did, "behaviour": r["behaviour"],
                            "pid": r["pid"], "cause": causes[did]})
    assert len(out) == len(causes) == 60, (
        f"census index resolves {len(out)} of {len(causes)} case ids")
    return sorted(out, key=lambda r: r["dossier_id"])


# ------------------------------------------------------------ config header

def config_identity() -> dict:
    """The PINNED generation config (design §3 amendment): every input as
    {path, sha256}, explicit nulls for overlay / pricing_version (no overlay
    is active under the frozen config) and join_version (F12 placeholder),
    plus the threshold rule. Written as the FIRST line of index.jsonl."""
    import benchmark as B
    import snapshot
    import threshold as T

    def rec(p):
        return {"path": os.path.basename(p),
                "sha256": snapshot._sha256_file(p)}

    return {
        "record": "config_identity",
        "pass": "drift_standing",
        "config_tag": CONFIG_TAG,
        "inputs": {
            "annotations": rec(ANNOTATIONS),
            "behaviour_atoms": rec(BEHAVIOUR_ATOMS),
            "queries": rec(QUERIES),
            "clauses": rec(B.CLAUSES),
            "thresholds": rec(THRESHOLDS),
            "overlay": None,
        },
        "threshold_rule": T.PREFERRED,
        "pricing_version": None,
        "join_version": None,
    }


# --------------------------------------------------------------- generation

def generate(out_dir: str = OUT_DIR) -> list:
    """The 60 stripped dossiers + index.jsonl (config-identity header
    first). Returns the index records. Byte-deterministic.

    The panel is read ONLY to reproduce the deterministic quote-containment
    join (pid -> mapped clause ids -> max-scoring clause), exactly as the
    census did; nothing panel-valued is emitted.
    """
    import benchmark as B
    import diagnose_disagreement as DD
    import readback
    import relevance as R
    import snapshot

    cases = case_list()
    clauses, _ = B.load_clauses()
    rows_by_id = {r["id"]: r for r in readback.load_clauses(B.CLAUSES)}
    index = R.RelevanceIndex.from_files(annotations_path=ANNOTATIONS)
    behaviours = snapshot.load_behaviours(BEHAVIOUR_ATOMS, QUERIES)
    frozen = snapshot.load_frozen_thresholds(THRESHOLDS)
    ann = R.load_annotations(ANNOTATIONS)
    with open(QUERIES) as f:
        raw_queries = {(q.get("slug") or q.get("id") or ""): q
                       for q in json.load(f).get("behaviours", [])}
    panel = B.load_true_panel()

    _pmaps, _raws, _norms = {}, {}, {}

    def _for(slug):
        if slug not in _pmaps:
            _pmaps[slug] = DD.passage_map(panel[slug], clauses)
            _raws[slug] = index.raw_scores(behaviours[slug])
            _norms[slug] = dict(index.rank(behaviours[slug]))
        return _pmaps[slug], _raws[slug], _norms[slug]

    os.makedirs(out_dir, exist_ok=True)
    records = []
    for case in cases:
        slug, pid, did = case["behaviour"], case["pid"], case["dossier_id"]
        beh = behaviours[slug]
        pmaps, raw, norm = _for(slug)
        cids = pmaps[pid]["clause_ids"]
        assert cids, f"{did}: unmapped passage — not a threshold-family case"
        assert slug in frozen, f"{did}: no frozen cut for behaviour {slug}"
        cut = frozen[slug]

        best = sorted(cids, key=lambda c: (-norm.get(c, 0.0), c))[0]
        ex = index.explain(beh, best)
        row = rows_by_id.get(best, {})
        atoms = ann.get(best, [])
        dist = _round(norm.get(best, 0.0) - cut)

        # SELF-CHECKS (generation-side only; `cause` never leaves memory):
        # the case must actually sit inside the census's near-cut margin,
        # on the side its family names — an admitted FP above the cut, the
        # FN just below it. A violation means the join or config drifted.
        assert abs(dist) <= 0.10 + 1e-9, (
            f"{did}: |distance_to_cut| = {abs(dist)} > 0.10 — not near-cut "
            f"under the frozen configuration; config drift, refuse to ship")
        if case["cause"] == "fp_threshold_drift":
            assert dist >= 0 and norm.get(best, 0.0) > 0, (
                f"{did}: fp_threshold_drift case is not admitted at the "
                f"frozen cut (distance {dist})")
        else:
            assert dist < 0, (
                f"{did}: fn_threshold case is not below the frozen cut "
                f"(distance {dist})")

        qatoms = sorted(({"name": a["name"], "kind": a["kind"],
                          "gloss": a["gloss"]} for a in beh.norm_atoms),
                        key=lambda a: a["name"])
        catoms = sorted(({k: a.get(k, "") for k in
                          ("name", "kind", "gloss", "quote", "span_id",
                           "locator")} for a in atoms),
                        key=lambda a: (a["name"], a["kind"]))
        raw_q = raw_queries.get(slug, {})

        dossier = {
            "dossier_id": did,
            "config_tag": CONFIG_TAG,
            "behaviour": {
                "slug": slug,
                "name": raw_q.get("name", ""),
                "definition": raw_q.get("definition", ""),
                "query_atoms": qatoms,
            },
            "clause": {
                "id": best,
                "text": row.get("quote", ""),
                "section_path": list(row.get("section_path") or []),
                "locator": row.get("locator", ""),
                "kind": row.get("kind", ""),
                "atoms": catoms,
            },
            "rendering": readback.render(atoms, row.get("kind")),
            "explain": {
                "channels": {k: _round(v) for k, v in
                             sorted(ex["channels"].items())},
                "channel_share": {k: _round(v) for k, v in
                                  sorted(ex["channel_share"].items())},
                "matched_atoms": ex["matched_atoms"],
                "top_lexical_terms": [[t, _round(v)] for t, v in
                                      ex.get("top_lexical_terms", [])],
                "atom_channel_live": ex.get("atom_channel_live"),
            },
            "cut": _round(cut),
            "cut_source": "frozen_artifact",
            "score": {"raw": _round(raw.get(best, 0.0)),
                      "norm": _round(norm.get(best, 0.0))},
            "distance_to_cut": dist,
        }
        hits = banned_key_hits(dossier)
        assert not hits, f"{did}: banned field(s) in stripped dossier: {hits}"

        fname = did + ".json"
        with open(os.path.join(out_dir, fname), "w") as f:
            json.dump(dossier, f, indent=1, sort_keys=True)
            f.write("\n")
        records.append({"dossier_id": did, "behaviour": slug, "file": fname})

    records.sort(key=lambda r: r["dossier_id"])
    with open(os.path.join(out_dir, "index.jsonl"), "w") as f:
        f.write(json.dumps(config_identity(), sort_keys=True) + "\n")
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
    return records


# ---------------------------------------------------------------- validator

def _load_index(dossier_dir: str) -> tuple[dict | None, dict]:
    """(config-identity header or None, {dossier_id: record}). The header
    is the first non-blank line iff it is a config_identity record."""
    header, out, first = None, {}, True
    with open(os.path.join(dossier_dir, "index.jsonl")) as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if first and r.get("record") == "config_identity":
                header = r
                first = False
                continue
            first = False
            out[r["dossier_id"]] = r
    return header, out


def validate(verdicts, dossier_dir: str) -> dict:
    """Audit a seat verdict file against the dossier set. REFUSES loudly.

    `verdicts`: a path or a list of {dossier_id, verdict, document_reason
    [, confidence]}. Checks: config-identity header present; every dossier
    covered exactly once; no unknown ids; verdict in the CLOSED set;
    document_reason a non-empty string; confidence (when present) in the
    closed set; and every dossier file free of banned panel-side keys (the
    fence stays checked at read time, not only at write time). Returns
    {"ok", "violations", "n_verdicts", "by_verdict"}.
    """
    if isinstance(verdicts, str):
        with open(verdicts) as f:
            verdicts = json.load(f)
    header, index = _load_index(dossier_dir)
    errs = []
    if header is None:
        errs.append(f"{dossier_dir}: index.jsonl has no config-identity "
                    "header record — the dossier set cannot prove which "
                    "configuration produced it; regenerate")

    ids = [v.get("dossier_id") for v in verdicts]
    for did, n in sorted(Counter(ids).items()):
        if n > 1:
            errs.append(f"duplicate verdict for {did} ({n} records)")
    for did in sorted(set(ids) - set(index)):
        errs.append(f"unknown dossier_id {did}")
    for did in sorted(set(index) - set(ids)):
        errs.append(f"missing verdict: dossier {did} has no record")

    by_verdict = Counter()
    for v in verdicts:
        did = v.get("dossier_id")
        verdict = v.get("verdict")
        if verdict not in VERDICT_VALUES:
            errs.append(f"{did}: verdict {verdict!r} not in the closed set "
                        f"{VERDICT_VALUES}")
        else:
            by_verdict[verdict] += 1
        reason = v.get("document_reason")
        if not (isinstance(reason, str) and reason.strip()):
            errs.append(f"{did}: document_reason must be a non-empty string")
        conf = v.get("confidence")
        if conf is not None and conf not in CONFIDENCE_VALUES:
            errs.append(f"{did}: confidence {conf!r} not in "
                        f"{CONFIDENCE_VALUES}")

    for did, rec in sorted(index.items()):
        fname = rec.get("file", did + ".json")
        with open(os.path.join(dossier_dir, fname)) as f:
            hits = banned_key_hits(json.load(f))
        if hits:
            errs.append(f"{did}: dossier holds banned panel-side field(s) "
                        f"{hits} — the set is contaminated; regenerate")

    return {"ok": not errs, "violations": errs, "n_verdicts": len(verdicts),
            "by_verdict": dict(sorted(by_verdict.items()))}


# ---------------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("dossiers")
    g.add_argument("--out-dir", default=OUT_DIR)
    v = sub.add_parser("validate")
    v.add_argument("--verdicts", required=True)
    v.add_argument("--dossier-dir", default=OUT_DIR)
    args = ap.parse_args()

    if args.cmd == "dossiers":
        recs = generate(args.out_dir)
        by_beh = Counter(r["behaviour"] for r in recs)
        print(f"wrote {len(recs)} stripped dossiers -> {args.out_dir} "
              f"({dict(sorted(by_beh.items()))})")
    else:
        rep = validate(args.verdicts, args.dossier_dir)
        print(f"--- verdicts {rep['n_verdicts']}; "
              f"by_verdict {rep['by_verdict']}")
        if rep["ok"]:
            print("CLEAN")
        else:
            for e in rep["violations"]:
                print("VIOLATION:", e)
            raise SystemExit(
                f"INVALID: {len(rep['violations'])} violation(s) — the "
                "verdict file is refused; fix and re-validate.")


if __name__ == "__main__":
    main()
