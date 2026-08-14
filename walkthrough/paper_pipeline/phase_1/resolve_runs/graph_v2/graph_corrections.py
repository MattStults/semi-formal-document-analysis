#!/usr/bin/env python3
"""Deterministic, reproducible corrections from repaired -> production.

⭐ EVERY correction here was ADJUDICATED against the document by an
independent pass (repaired_verification.md, production_certification.md)
and is applied MECHANICALLY: this file makes no content judgment, it
executes recorded verdicts and refuses if a precondition fails.

⛔ Written because the first application was an ad-hoc command
(production_certification C4: "outcome verified; process not
reproducible") -- REPRODUCIBILITY.md requires the procedure, not just
the artifact. Rerunning this on the repaired graph reproduces the
production graph byte-for-byte.

Usage: graph_corrections.py [in.json] [out.json]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import recurse_driver as R  # noqa: E402

#: (node_id, name, grounds) -- provides entries the verification pass
#: adjudicated as FALSE CLAIMS against the document.
REVERT_PROVIDES = [
    ("L2126-2404_n031", "assume_objective_pov",
     "span L2151 is inside a !!! meta Commentary block and its prose "
     "NEGATES the L2139 rule (repaired_verification R1)"),
    ("L3877-3953_n012", "assume_best_intentions_principle",
     "span L3937 is the thank-you rule; the section is at L610 (R2)"),
    ("L3147-3238_n001", "user_authority_section_rules",
     "span L3152 is the error-avoidance rule; the authority claim sits "
     "on heading L3150, which no node covers (R3)"),
]

#: (from_node, to_node, name, must_cover_line, grounds)
REAIM_PROVIDES = [
    ("L4252-4482_n001", "L4252-4482_n003", "voice_style_guidelines", 4260,
     "the claim is the both-modes sentence at L4260, which n003's span "
     "covers verbatim and n001's does not (R4)"),
]

#: needs the repair fabricated or misnamed (certification C1 / the rename)
DROP_NEEDS = [
    ("L3877-3953_n012", "assume_best_intentions_principle",
     "left behind by the R2 revert: a fabricated dependency on a name "
     "this node no longer provides -- latent false premise once an "
     "aliasing pass resolves it (certification C1)"),
]
RENAME_NEEDS = [
    ("privileged_information_definition", "privileged_information",
     "the repair introduced a need under a name nothing provides; the "
     "same enumeration is provided by L1707-1973_n018"),
]


def apply(g, baseline=None):
    """`baseline` = the pre-repair accepted graph. Self-loops present in
    it are NOT touched: they are accepted content, never adjudicated, and
    out of scope for these corrections (near-miss caught 2026-08-14 -- a
    general sweep removed 19, of which 16 pre-dated the repair)."""
    log = []
    by_id = {n["id"]: n for n in g["nodes"]}

    for nid, name, why in REVERT_PROVIDES:
        n = by_id[nid]
        before = len(n.get("provides", []))
        n["provides"] = [p for p in n["provides"] if R.nm(p) != name]
        if len(n["provides"]) != before - 1:
            raise SystemExit(f"precondition failed: {name} not on {nid}")
        log.append(f"REVERTED provides {name} from {nid}: {why}")

    for src, dst, name, must_cover, why in REAIM_PROVIDES:
        s, d = by_id[src], by_id[dst]
        if not any(sp["lines"][0] <= must_cover <= sp["lines"][1]
                   for sp in d.get("spans", [])):
            raise SystemExit(f"precondition failed: {dst} does not cover "
                             f"L{must_cover}")
        entry = next(p for p in s["provides"] if R.nm(p) == name)
        s["provides"] = [p for p in s["provides"] if R.nm(p) != name]
        d.setdefault("provides", []).append(entry)
        log.append(f"RE-AIMED provides {name} {src} -> {dst}: {why}")

    for nid, name, why in DROP_NEEDS:
        n = by_id[nid]
        before = len(n.get("needs", []))
        n["needs"] = [d for d in n.get("needs", [])
                      if not (isinstance(d, dict) and d.get("name") == name)]
        if len(n["needs"]) == before:
            raise SystemExit(f"precondition failed: need {name} not on {nid}")
        log.append(f"DROPPED need {name} from {nid}: {why}")

    provided = {R.nm(p) for n in g["nodes"] for p in n.get("provides", [])}
    for old, new, why in RENAME_NEEDS:
        if new not in provided:
            raise SystemExit(f"precondition failed: {new} is not provided")
        k = 0
        for n in g["nodes"]:
            for d in n.get("needs", []):
                if isinstance(d, dict) and d.get("name") == old:
                    d["name"] = new
                    k += 1
        if k:
            log.append(f"RENAMED need {old} -> {new} ({k}): {why}")

    # SELF-LOOP SWEEP (certification C2), SCOPED TO REPAIR-INTRODUCED
    # loops only. The R4 re-aim MOVED a self-loop rather than removing
    # it; that one and any other the repair created are dropped. Loops
    # already present in the accepted baseline are LEFT ALONE -- they are
    # accepted content and removing them would be an unadjudicated edit.
    pre = set()
    if baseline:
        for n in baseline["nodes"]:
            prov = {R.nm(p) for p in n.get("provides", [])}
            for d in n.get("needs", []):
                if R.nm(d) in prov:
                    pre.add((n["id"], R.nm(d)))
    for n in g["nodes"]:
        prov = {R.nm(p) for p in n.get("provides", [])}
        keep, dropped = [], []
        for d in n.get("needs", []):
            loop = isinstance(d, dict) and d.get("name") in prov
            (dropped if loop and (n["id"], R.nm(d)) not in pre
             else keep).append(d)
        if dropped:
            n["needs"] = keep
            for d in dropped:
                log.append(f"DROPPED repair-introduced self-need "
                           f"{d.get('name')} from {n['id']}")

    g["verification_corrections"] = log
    g.setdefault("driver_autofixes", []).extend(log)
    return g, log


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "runs/ds7/root_graph.repaired.json"
    dst = sys.argv[2] if len(sys.argv) > 2 else "runs/ds7/root_graph.production.json"
    base = json.load(open(os.path.join(HERE, "runs/ds7/root_graph.json")))
    g, log = apply(json.load(open(src)), baseline=base)
    json.dump(g, open(dst, "w"), indent=1)
    names = {R.nm(p) for n in g["nodes"] for p in n.get("provides", [])}
    needs = [(n["id"], d) for n in g["nodes"] for d in n.get("needs", [])
             if isinstance(d, dict)]
    dang = [x for x in needs if x[1]["name"] not in names]
    loops = [(n["id"], R.nm(d)) for n in g["nodes"] for d in n.get("needs", [])
             if R.nm(d) in {R.nm(p) for p in n.get("provides", [])}]
    print("\n".join("  " + l for l in log))
    print(f"\n{dst}: {len(g['nodes'])} nodes | {len(names)} exported names | "
          f"{len(needs)} needs | {len(dang)} dangling | {len(loops)} self-loops")


if __name__ == "__main__":
    main()
