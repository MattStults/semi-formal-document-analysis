"""Freeze a blind human-adjudication sample (HUMAN_ADJUDICATION_PROTOCOL.md).

Writes THREE artifacts, sha-pinned:
  items.json    presentation only -- passage text + behaviour definition. No verdicts.
  key.json      what the tool predicted, what the panel scored, the census cause.
  reserved.json a disjoint pool, untouched, for a later question.

The split is the point: the presenter reads items.json and never key.json.

PANEL-READING. Never importable from the query path.
"""
import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import benchmark as B  # noqa: E402

OUT = os.path.join(HERE, "human_adjudication")
SEED = 20260805          # pinned; recorded in the manifest
N_DISAGREE = 32
N_ANCHOR = 8
CENSUS = os.path.join(HERE, "audit_dossiers", "ext_v1_merged__audit_v1")
SNAPSHOT = os.path.join(HERE, "snapshots", "join-integrity-v2-2026-08-04.json")


def sha(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def main():
    rng = random.Random(SEED)
    os.makedirs(OUT, exist_ok=True)

    behaviours = B.load_true_panel()
    clauses, _ = B.load_clauses(B.CLAUSES)
    snap = json.load(open(SNAPSHOT))
    defs = {b["slug"]: b for b in
            json.load(open(os.path.join(HERE, "behaviours_query.json")))["behaviours"]}

    # ---- pool 1: census disagreements, with their passage text -----------------
    verdicts = json.load(open(os.path.join(CENSUS, "verdicts_merged.json")))
    disagree = []
    for v in verdicts:
        d = json.load(open(os.path.join(CENSUS, v["dossier_id"] + ".json")))
        p = d.get("passage") or {}
        if not p.get("quote"):
            continue
        disagree.append({
            "kind": "disagreement",
            "behaviour": d["behaviour"],
            "passage_id": p["id"],
            "quote": p["quote"],
            "_cause": v["cause"],
            "_side": v.get("side"),
            "_tool_says": "relevant" if d.get("kind") == "FP" else "not_relevant",
            "_panel_score": p.get("panel_score"),
        })

    # ---- pool 2: agreement anchors --------------------------------------------
    anchors = []
    for slug, beh in behaviours.items():
        if slug not in snap["behaviours"]:
            continue
        joins = B.clause_joins(beh, clauses)
        tool = B.lift(set(snap["behaviours"][slug]["predicted"]), joins)
        targets = B.pair_targets(beh, 1)
        golds = [set(t["gold"]) for t in targets.values()]
        by_id = {p["id"]: p for p in B.passages(beh, "openai")}
        for pid in joins:
            in_all = all(pid in g for g in golds)
            in_none = all(pid not in g for g in golds)
            if not (in_all or in_none):
                continue                       # panel itself is split -> not an anchor
            panel_rel = in_all
            tool_rel = pid in tool
            if panel_rel != tool_rel:
                continue                       # not an agreement
            p = by_id.get(pid)
            if not p or not p.get("quote"):
                continue
            anchors.append({
                "kind": "anchor",
                "behaviour": slug,
                "passage_id": pid,
                "quote": p["quote"],
                "_cause": None,
                "_side": None,
                "_tool_says": "relevant" if tool_rel else "not_relevant",
                "_panel_score": None,
            })

    # ---- stratified draw -------------------------------------------------------
    strata = {}
    for row in disagree:
        strata.setdefault((row["behaviour"], row["_cause"]), []).append(row)
    for k in strata:
        strata[k].sort(key=lambda r: r["passage_id"])
        rng.shuffle(strata[k])

    picked, keys = [], sorted(strata)
    while len(picked) < N_DISAGREE:
        progressed = False
        for k in keys:
            if strata[k] and len(picked) < N_DISAGREE:
                picked.append(strata[k].pop())
                progressed = True
        if not progressed:
            break

    anchors.sort(key=lambda r: (r["behaviour"], r["passage_id"]))
    rng.shuffle(anchors)
    by_beh = {}
    for a in anchors:
        by_beh.setdefault(a["behaviour"], []).append(a)
    picked_anchors = []
    while len(picked_anchors) < N_ANCHOR:
        progressed = False
        for slug in sorted(by_beh):
            if by_beh[slug] and len(picked_anchors) < N_ANCHOR:
                picked_anchors.append(by_beh[slug].pop())
                progressed = True
        if not progressed:
            break

    sample = picked + picked_anchors
    rng.shuffle(sample)                        # interleaved, randomized order

    items, key = [], []
    for i, row in enumerate(sample, 1):
        iid = f"H{i:03d}"
        b = defs[row["behaviour"]]
        items.append({
            "item_id": iid,
            "behaviour_name": b["name"],
            "behaviour_definition": b["definition"],
            "passage": row["quote"],
        })
        key.append({
            "item_id": iid, "kind": row["kind"], "behaviour": row["behaviour"],
            "passage_id": row["passage_id"], "tool_says": row["_tool_says"],
            "census_cause": row["_cause"], "census_side": row["_side"],
            "panel_score": row["_panel_score"],
        })

    chosen = {(r["behaviour"], r["passage_id"]) for r in sample}
    reserved = [
        {"behaviour": r["behaviour"], "passage_id": r["passage_id"],
         "kind": r["kind"]}
        for r in disagree + anchors
        if (r["behaviour"], r["passage_id"]) not in chosen]

    manifest = {
        "seed": SEED, "n_disagreement": len(picked), "n_anchor": len(picked_anchors),
        "items_sha256": sha(items), "key_sha256": sha(key),
        "reserved_pool_size": len(reserved),
        "protocol": "HUMAN_ADJUDICATION_PROTOCOL.md",
        "note": "items.json is presentation-only. The presenter must not read key.json.",
    }
    for name, obj in (("items", items), ("key", key), ("reserved", reserved),
                      ("manifest", manifest)):
        json.dump(obj, open(os.path.join(OUT, f"{name}.json"), "w"),
                  indent=1, ensure_ascii=False)

    print(json.dumps(manifest, indent=1))
    print(f"\nstratа drawn from: {len(strata)} (behaviour x cause) cells")
    print(f"anchors available: {len(anchors)}; reserved pool: {len(reserved)}")


if __name__ == "__main__":
    main()
