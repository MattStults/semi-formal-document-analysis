"""Find and dump tool-vs-frontier disagreements for manual debugging.

DIAGNOSTIC-ONLY, PANEL-READING — in the anti-cheat FORBIDDEN set for exactly
that reason. This module exists to pick individual disagreement cases and dump
everything a human needs to adjudicate them: the passage, the judges' verdicts,
the clause segmentation, the atoms, the deterministic rendering, and the
query's own explanation of its score. Its output is a REPORT for a person.
Nothing here may feed a prompt, a vocabulary, a threshold, a weight or a
schema (contract §5 invariant 9 bars fitting, not measuring); it imports the
scorer and the panel and must never be imported by a query module.

Passage-level decision rule mirrors `benchmark.score_tool`'s passage_level:
a passage is PREDICTED iff any of its mapped clauses is predicted. Gold is
`score >= min_score` (default 5, the working reference cutoff) on the TRUE
reconstructed universe, so score-0 passages are really "no judge saw
relevance", not "absent from the file".

Case-selection bias, stated: FN candidates are restricted to passages that
mapped to at least one clause — an unmapped passage is a segmentation-coverage
failure, already measured elsewhere, and debugging it teaches nothing about
translation or query. That restriction makes the FN pick FAVOURABLE to the
segmenter and must be said in any write-up.
"""
from __future__ import annotations

import argparse
import json

import benchmark as B
import inventory
import relevance as R


def passage_map(behaviour, clauses,
                join_version: int = inventory.JOIN_VERSION_V1,
                mixed_variants: bool = False):
    """pid -> {score, quote, verdicts, clause_ids} over the FULL universe.

    `join_version`/`mixed_variants` select the join, straight through to
    `benchmark.map_reference`: the defaults are the measured state (v1,
    uniform variants) so every historical caller reproduces its numbers,
    and the census passes both explicitly so the join it RECORDS in its
    config-identity header is the join it actually ran (PORTFOLIO_REVIEW
    F12: join identity belongs to CENSUS identity).
    """
    m = B.map_reference(behaviour, clauses, min_score=0,
                        join_version=join_version,
                        mixed_variants=mixed_variants)
    per = m["per_passage"]
    out = {}
    for p in B.passages(behaviour):
        out[p["id"]] = {
            "score": p.get("score", 0),
            "quote": p.get("quote", ""),
            "verdicts": p.get("verdicts"),
            "clause_ids": sorted(per.get(p["id"], [])),
        }
    return out


def survey(index, behaviours, panel, clauses, min_score=5,
           join_version: int = inventory.JOIN_VERSION_V1,
           mixed_variants: bool = False):
    """All disagreements, both directions, every frontier behaviour.

    `join_version`/`mixed_variants` are passed through to `passage_map`;
    a caller must give the SAME pair to both or its dossiers would describe
    a different join from the one that found the disagreements."""
    rows = []
    for slug, beh in behaviours.items():
        scores = index.raw_scores(beh)
        predicted = index.predict(beh)          # label-free Otsu cut
        pmap = passage_map(panel[slug], clauses, join_version=join_version,
                           mixed_variants=mixed_variants)
        for pid, rec in pmap.items():
            cids = rec["clause_ids"]
            pred = bool(set(cids) & predicted)
            gold = rec["score"] >= min_score
            if pred == gold:
                continue
            rows.append({
                "behaviour": slug,
                "pid": pid,
                "kind": "FN" if gold else "FP",
                "panel_score": rec["score"],
                "mapped_clauses": cids,
                "tool_max": max((scores.get(c, 0.0) for c in cids),
                                default=0.0),
                "quote_head": rec["quote"][:110],
            })
    return rows


def dump_case(index, behaviours, clauses, slug, pid, out_path):
    """Everything a human adjudicator needs for one passage, as JSON."""
    import readback as RB
    beh = behaviours[slug]
    raw_beh = B.load_true_panel()[slug]
    pmap = passage_map(raw_beh, clauses)
    rec = pmap[pid]
    ann = R.load_annotations("annotations_b8.json")
    by_clause = ann["by_clause"] if "by_clause" in ann else ann
    rows = {r["id"]: r for r in B._clause_rows(B.load_clauses()[0])} \
        if False else {}
    clause_texts = {c["id"]: c.get("quote") or c.get("text", "")
                    for c in clauses}
    case = {
        "behaviour": slug,
        "passage_id": pid,
        "panel": {"score": rec["score"], "verdicts": rec["verdicts"]},
        "passage_quote": rec["quote"],
        "query_atoms": sorted(a["name"] for a in beh.norm_atoms),
        "otsu_threshold_note": "predict() derives the cut from this query's "
                               "own score distribution; see per-clause scores",
        "clauses": [],
    }
    for cid in rec["clause_ids"]:
        atoms = by_clause.get(cid, [])
        case["clauses"].append({
            "clause_id": cid,
            "clause_text": clause_texts.get(cid, "<clause file mismatch>"),
            "atoms": atoms,
            "rendering": RB.render(atoms),
            "explain": index.explain(beh, cid),
        })
    with open(out_path, "w") as f:
        json.dump(case, f, indent=1)
    return case


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", nargs=2, metavar=("SLUG", "PID"))
    ap.add_argument("--out", default="disagreement_case.json")
    args = ap.parse_args()

    clauses, _ = B.load_clauses()
    index = R.RelevanceIndex.from_files(annotations_path="annotations_b8.json")
    panel = B.load_true_panel()
    behaviours = R.behaviours_from_panel(panel,
                                         atoms_source="behavior_atoms_b8.json")

    if args.case:
        slug, pid = args.case
        dump_case(index, behaviours, clauses, slug, pid, args.out)
        print(f"wrote {args.out}")
        return

    rows = survey(index, behaviours, panel, clauses)
    from collections import Counter
    print(Counter((r["behaviour"], r["kind"]) for r in rows))
    for kind in ("FN", "FP"):
        sub = [r for r in rows if r["kind"] == kind and r["mapped_clauses"]]
        sub.sort(key=lambda r: (-r["panel_score"], r["tool_max"])
                 if kind == "FN" else (-r["tool_max"], r["panel_score"]))
        print(f"\n=== {kind} candidates (mapped only) ===")
        for r in sub[:6]:
            print(f"{r['behaviour']:24s} {r['pid']:12s} panel={r['panel_score']:2d} "
                  f"tool_max={r['tool_max']:.3f} clauses={len(r['mapped_clauses'])} "
                  f"| {r['quote_head']}")


if __name__ == "__main__":
    main()
