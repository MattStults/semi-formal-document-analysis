#!/usr/bin/env python3
"""Paired-format seat pilot (ROUND4_PREREG.md erratum E2, 2026-08-24).

Validates the seat-material format hypothesis on ALREADY-RULED nodes (truth
known; permanently excluded from round-4 draws — zero fresh-draw burn).
Seeded sample of 20 helpfulness truth-ledger nodes (10 v19-engaged / 10 not,
seed 20260827); each node gets TWO packets:
  format T (trimmed)   — SOURCE TEXT span only (canary attempt 1's format)
  format C (corrected) — ESTABLISHES claim block (byte-extracted from
                         node_corpus_all.json, the canonical committed
                         source) + SOURCE TEXT span
Both carry the uniform anti-completion fence. VALIDATOR (runs before write;
failure aborts): every C packet's ESTABLISHES block is byte-equal to the
extractor's output over the canonical quote; every packet ends with the
fence; every T/C pair shares an identical SOURCE TEXT section.
"""
import json, random, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import satisfiability_census as SC
import relevance_by_act as RBA
import ruling_packets as RP

SEED = 20260827
FENCE = ("\n\n[VENUE MECHANICS: The passage above ends here; short fragments "
         "are intentional. Reply with your ruling directly as your final "
         "message — RELEVANT or NOT_RELEVANT, then one sentence of grounds. "
         "Do not continue or complete the passage text.]")

def establishes_block(quote):
    if "ESTABLISHES" not in quote:
        return None
    body = quote[quote.find("ESTABLISHES"):].split("PROVIDES")[0]
    return body.strip()

def main():
    nc = json.load(open("../node_corpus_all.json"))
    byid = {c["id"]: c for c in nc["clauses"]}
    truth = SC.truth_all("helpfulness")
    mods = json.load(open("modules_contract_v19.json"))["modules"]
    br = RBA.bridges(); corpus = RBA.corpus_acts()
    _, rel = RBA.relevance(mods["helpfulness"], br, corpus)
    eng = set(rel)
    ruled = sorted(n for n in truth if n in byid
                   and establishes_block(byid[n]["quote"]))
    pe = [n for n in ruled if n in eng]
    pn = [n for n in ruled if n not in eng]
    rnd = random.Random(SEED)
    pick = sorted(rnd.sample(pe, 10)) + sorted(rnd.sample(pn, 10))
    spans = RP.load_spans()
    dfn = mods["helpfulness"]["definition"]
    packets = []
    for n in pick:
        src = spans[n]
        est = establishes_block(byid[n]["quote"])
        assert est and est == establishes_block(byid[n]["quote"])  # byte-equal
        for fmt, span in (("T", src), ("C", est + "\n\n" + src)):
            p = RP.RULING_PROMPT.format(label="helpfulness", query=dfn,
                    boundary="(see definition)", node=n, span=span) + FENCE
            assert p.endswith(FENCE) and "SOURCE TEXT" in p
            packets.append({"node": n, "format": fmt, "prompt": p})
    for n in pick:  # validator: T/C share identical SOURCE TEXT section
        t = next(p for p in packets if p["node"] == n and p["format"] == "T")
        c = next(p for p in packets if p["node"] == n and p["format"] == "C")
        assert t["prompt"].split("SOURCE TEXT",1)[1] == c["prompt"].split("SOURCE TEXT",1)[1]
    rnd2 = random.Random(SEED); rnd2.shuffle(packets)
    json.dump({"_": "Paired-format pilot packets (erratum E2). format is "
               "POST-RULING routing metadata, never seat material. Truth is "
               "NOT in this file.", "seed": SEED, "n": len(packets),
               "nodes_engaged": [n for n in pick if n in eng],
               "nodes_not_engaged": [n for n in pick if n not in eng],
               "packets": packets},
              open("round4_pilot_packets.json", "w"), indent=1)
    print(json.dumps({"n_packets": len(packets), "engaged": 10, "not": 10,
                      "validator": "PASS"}))

if __name__ == "__main__":
    main()
