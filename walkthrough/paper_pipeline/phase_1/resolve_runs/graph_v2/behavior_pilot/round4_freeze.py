#!/usr/bin/env python3
"""Round-4 freeze derivation — deterministic, read-only, zero-spend.

Emits ROUND4_FREEZE_DERIVATION.json with every FREEZE-section value the
scaffold (ROUND4_PREREG_SCAFFOLD.md) says is "derived mechanically at
instrument freeze":

- frozen instrument identity (v19 contract sha; census artifact),
- per-behaviour EXCLUSION list (every node with ANY prior ruling = the keys
  of the assembled truth ledger satisfiability_census.truth_all(), which
  already folds in adjudication_run2, all fresh-draw results, and the
  2026-08-24 defensibility overlay) + its sha,
- pool sizes (v19-engaged / not-engaged among corpus nodes, minus excluded),
- registered predictions per behaviour computed over ALL-TRUTH at the frozen
  instrument: engaged precision = P(truth=relevant | engaged, ruled) and
  decline-correctness = P(truth=not_relevant | not engaged, ruled),
- population-remainder treatment: any side whose unruled pool is <= 48 is
  drawn WHOLE (population closed for that side), per the round-3 design the
  scaffold carries for harm,
- registered draw seeds: base 20260824, per-behaviour index by sorted slug
  (the campaign's registered-base-plus-index convention).

Determinism: no randomness, no time; draws themselves happen at run time
with the seeds registered here.
"""

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import relevance_by_act as RBA           # noqa: E402
import satisfiability_census as SC       # noqa: E402

CONTRACT = "modules_contract_v19.json"
BASE_SEED = 20260824
SLUGS = ["avoiding-over-and-under-caution", "harm-avoidance-to-third-parties",
         "helpfulness"]                  # sorted; index = seed offset
CLOSE_POOL_AT = 48                       # side drawn whole at/below this


def sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def main():
    contract_raw = open(os.path.join(HERE, CONTRACT)).read()
    mods = json.loads(contract_raw)["modules"]
    br = RBA.bridges()
    corpus = RBA.corpus_acts()
    all_nodes = set(corpus)

    out = {"_": "ROUND-4 freeze derivation (2026-08-24) — see module docstring",
           "contract": CONTRACT,
           "contract_sha256": hashlib.sha256(contract_raw.encode()).hexdigest(),
           "census_artifact": "satisfiability_census_v19_frozen.json",
           "base_seed": BASE_SEED,
           "behaviours": {}}

    for i, slug in enumerate(SLUGS):
        truth = SC.truth_all(slug)
        excluded = sorted(truth)                     # any prior ruling
        _, rel = RBA.relevance(mods[slug], br, corpus)
        eng = set(rel)
        pool_eng = sorted((all_nodes - set(excluded)) & eng)
        pool_not = sorted((all_nodes - set(excluded)) - eng)
        ruled_eng = [n for n in truth if n in eng]
        ruled_not = [n for n in truth if n not in eng]
        prec = (sum(1 for n in ruled_eng if truth[n] == "relevant")
                / len(ruled_eng)) if ruled_eng else None
        decl = (sum(1 for n in ruled_not if truth[n] == "not_relevant")
                / len(ruled_not)) if ruled_not else None
        out["behaviours"][slug] = {
            "seed": BASE_SEED + i,
            "excluded_n": len(excluded),
            "exclusion_sha256": sha(excluded),
            "pool_engaged_n": len(pool_eng),
            "pool_not_engaged_n": len(pool_not),
            "remainder_treatment": {
                "engaged": "POPULATION CLOSED (draw whole side)"
                           if len(pool_eng) <= CLOSE_POOL_AT else "draw 40",
                "not_engaged": "POPULATION CLOSED (draw whole side)"
                               if len(pool_not) <= CLOSE_POOL_AT else "draw 40"},
            "registered_prediction": {
                "engaged_precision": round(prec, 4) if prec is not None else None,
                "decline_correctness": round(decl, 4) if decl is not None else None,
                "band": "+-2 nodes = +-5 pts at n=40",
                "basis_ruled_engaged_n": len(ruled_eng),
                "basis_ruled_not_engaged_n": len(ruled_not)},
            "excluded_nodes": excluded,
        }
    path = os.path.join(HERE, "ROUND4_FREEZE_DERIVATION.json")
    open(path, "w").write(json.dumps(out, indent=1))
    slim = {s: {k: v for k, v in b.items() if k != "excluded_nodes"}
            for s, b in out["behaviours"].items()}
    print(json.dumps({"contract_sha256": out["contract_sha256"],
                      "behaviours": slim}, indent=1))


if __name__ == "__main__":
    main()
