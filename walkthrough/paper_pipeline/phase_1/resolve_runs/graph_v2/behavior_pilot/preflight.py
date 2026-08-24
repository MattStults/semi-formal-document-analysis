#!/usr/bin/env python3
"""PREFLIGHT — validates the calculus's explicit preconditions (A14) before
any iteration starts. The machine is a REPAIR calculus, not a construction
calculus: P1-P4 are constructive prerequisites (built by the bootstrap
pipeline); P5's truth can cold-start (the one self-buildable component);
P6-P7 are harness/governance. Every check is mechanical. Exit 0 = cleared;
named failures otherwise. Run from behavior_pilot/."""
import json, os, sys, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OK, FAIL = [], []
def check(name, fn):
    try:
        msg = fn()
        OK.append((name, msg or "ok"))
    except Exception as e:
        FAIL.append((name, f"{type(e).__name__}: {e}"))

def p1_decomposition():
    nc = json.load(open(os.path.join(HERE, "..", "node_corpus_all.json")))
    cl = nc["clauses"]
    assert nc.get("source_sha256"), "no source sha recorded"
    assert all("id" in c and "quote" in c for c in cl)
    return f"{len(cl)} nodes, source sha pinned"

def p2_translation():
    import relevance_by_act as RBA
    corpus = RBA.corpus_acts(); br = RBA.bridges()
    mods = json.load(open(os.path.join(HERE, "modules_contract_v19.json")))["modules"]
    empty = []
    for slug, m in mods.items():
        _, rel = RBA.relevance(m, br, corpus)
        if not rel: empty.append(slug)   # the F1 silent-empty-lane class
    assert not empty, f"modules engaging NOTHING (F1 class): {empty}"
    bridged = sum(1 for rows in corpus.values() for f, _ in rows if br.get(f))
    assert bridged > 0, "no bespoke act bridges to any canonical act"
    return f"{len(corpus)} nodes carry acts; every module engages >0"

def p3_keying():
    import satisfiability_census as SC
    sig, ap, pa, ctx = SC.load_layers()
    import relevance_by_act as RBA
    acts_corpus = set(RBA.corpus_acts())
    canon = {c["id"] for c in json.load(open(os.path.join(
        HERE, "..", "node_corpus_all.json")))["clauses"]}
    orphan = {k.split("|")[0] for k in sig} - acts_corpus
    drift = set()
    for slug in ("helpfulness", "harm-avoidance-to-third-parties",
                 "avoiding-over-and-under-caution"):
        drift |= set(SC.truth_all(slug)) - (acts_corpus | canon)
    # canonical-corpus drift: ruled nodes the CLAUSE corpus does not know
    # (the F-r1 class). Known instances are NAMED, never silently passed:
    canon_drift = set()
    for slug in ("helpfulness", "harm-avoidance-to-third-parties",
                 "avoiding-over-and-under-caution"):
        canon_drift |= set(SC.truth_all(slug)) - canon
    KNOWN_F_R1 = set(json.load(open(os.path.join(
        HERE, "F_R1_KNOWN_DRIFT.json")))["nodes"]) & canon_drift
    new_drift = canon_drift - KNOWN_F_R1
    msg = (f"layer-orphans {len(orphan)}, hard drift {len(drift)}, "
           f"canonical drift {len(canon_drift)} "
           f"(KNOWN F-r1 superseded-chunking: {len(KNOWN_F_R1)}, repair queued; NEW: {len(new_drift)})")
    assert not orphan and not drift and not new_drift, msg
    return "WARN " + msg if canon_drift else msg

def p4_modules():
    import relevance_by_act as RBA
    mods = json.load(open(os.path.join(HERE, "modules_contract_v19.json")))["modules"]
    fields = set(RBA.DECLARABLE_MOVES)
    for slug, m in mods.items():
        assert m.get("definition"), f"{slug}: no definition text"
        unknown = {k for k in m if k in
                   ("protects_concern","governs_concern","purpose_concern",
                    "arg_sorts","party_concern","governs_conditional")} - fields
        assert not unknown, f"{slug}: declares outside the registry {unknown}"
    return f"{len(mods)} modules, declarations within DECLARABLE_MOVES"

def p5_truth_and_brief():
    t = open(os.path.join(HERE, "LINEAGE_SEAT_INSTRUCTION.md")).read()
    assert "20/20" in t, "brief carries no measured stability record"
    import satisfiability_census as SC
    n = len(SC.truth_all("helpfulness"))
    return f"pinned brief with replication record; truth ledger {n} nodes (cold-startable if 0)"

def p6_harness():
    for m in ("satisfiability_census", "probe", "verify_terminal",
              "trace_check", "route"):
        importlib.import_module(m)
    import verify_terminal as VT, relevance_by_act as RBA
    assert set(VT.ENUMERATED) | set(VT.KNOWN_UNENUMERATED) == set(RBA.DECLARABLE_MOVES)
    return "census/probe/verify_terminal/trace/route importable; registry handshake holds"

def p7_governance():
    for f in ("HYPOTHESIS_LEDGER.jsonl", "ITERATION_NOTES.md",
              "CALCULUS_RUNBOOK.md", "ERROR_CALCULUS.md"):
        assert os.path.exists(os.path.join(HERE, f)), f"{f} missing"
    rb = open(os.path.join(HERE, "CALCULUS_RUNBOOK.md")).read()
    assert "STOP CONDITIONS" in rb
    return "ledgers, runbook, spec, stop conditions present"

for name, fn in (("P1 decomposition", p1_decomposition),
                 ("P2 translation-liveness", p2_translation),
                 ("P3 keying-consistency", p3_keying),
                 ("P4 modules-in-registry", p4_modules),
                 ("P5 truth+pinned-brief", p5_truth_and_brief),
                 ("P6 harness", p6_harness),
                 ("P7 governance", p7_governance)):
    check(name, fn)
for n, m in OK:   print(f"  PASS {n}: {m}")
for n, m in FAIL: print(f"  FAIL {n}: {m}")
print(f"preflight: {len(OK)} pass, {len(FAIL)} fail")
sys.exit(1 if FAIL else 0)
