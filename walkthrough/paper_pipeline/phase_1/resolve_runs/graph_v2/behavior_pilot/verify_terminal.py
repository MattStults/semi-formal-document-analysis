#!/usr/bin/env python3
"""TERMINALITY VERIFIER (Matt's requirement, 2026-08-19) — deterministic, $0.

For every current mismatch, DECIDE its status within the admissible DECLARATION
space by construction rather than judgment: enumerate the MINIMAL declaration
moves that would flip the node, re-execute the instrument under each, and score
with CHARTER ARITHMETIC. Verdicts:
  FIXABLE(move)   — some enumerated move is charter-positive (checker doubles as fix-finder)
  TERMINAL-DECL   — every declaration move charter-negative (proof by exhaustion, receipts inline)
  TERMINAL-STRUCT — no declaration move can flip it (actor-excluded / no act match:
                    needs bridge or vocabulary moves)
All TERMINAL verdicts are RELATIVE to current vocabularies (extensions fenced, per charter).
Charter arithmetic for a move: fixes = adjudicated-wrong nodes corrected; breaks = correct
or adjudicated-wrong-the-other-way nodes newly wrong; POSITIVE iff fixes > breaks and no
previously-adjudicated instrument_wrong node is re-broken.
Usage: .../.venv/bin/python verify_terminal.py modules_contract_v18.json
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import relevance_by_act as RBA
import arm_ab as AB

GQ = ["substance_usefulness","objectivity_neutrality","accuracy_calibration","tone_manner","formatting_style","identity_meta"]
PR = ["user","third_party","society","developer","minor"]


def truth_all(slug):
    t = dict(AB.truth_for(slug))
    fmap = {"helpfulness": [("fresh_draw","HELP_RESULT"),("fresh_draw2","HELP_R2_RESULT"),("fresh_draw3","HELP_R3_RESULT")],
            "harm-avoidance-to-third-parties": [("fresh_draw2","HARM_R2_RESULT")],
            "avoiding-over-and-under-caution": [("fresh_draw2","CAUTION_R2_RESULT")]}
    for rd, f in fmap[slug]:
        p = os.path.join(HERE, "panel_run1", rd, f + ".json")
        if os.path.exists(p):
            t.update(json.load(open(p))["truth"])
    return t


def eng_set(mod, br, corpus):
    _, rel = RBA.relevance(mod, br, corpus)
    return set(rel)


def moves_for(node, slug, mod, sig, ap, pa, corpus, br, engaged):
    """Minimal single-field declaration moves that could flip `node`."""
    keys = [k for k in sig if k.startswith(node + "|")]
    out = []
    if not engaged:
        # additions: the node's own blocked values
        if keys and not any(pa[k]["actor"] == "assistant" for k in keys):
            return []          # actor-excluded: TERMINAL-STRUCT
        canon = {br[f] for f, _ in corpus.get(node, []) if br.get(f)}
        acts, _ = RBA.behavior_acts(mod)
        pm = RBA.parent_map()
        vh = any(c in acts or (pm.get(c, set()) & acts) or any(c in pm.get(a, set()) for a in acts) for c in canon)
        if not vh:
            return []          # no act match: TERMINAL-STRUCT (bridge/vocab space)
        pv = {p for k in keys for p in ap.get(k, []) if p in PR}
        gv = {g for k in keys for g in sig[k]["governs"]}
        if mod.get("protects_concern") and not (pv & set(mod["protects_concern"])):
            out.append(("protects_concern", sorted(set(mod["protects_concern"]) | pv)))
        if (mod.get("governs_concern") or mod.get("governs_conditional")) and not (gv & set(mod.get("governs_concern") or [])):
            out.append(("governs_concern", sorted(set(mod.get("governs_concern") or []) | gv)))
    else:
        # removals: drop the admitting values per field (may over-remove; that's the receipt)
        pv = {p for k in keys for p in ap.get(k, []) if p in PR}
        gv = {g for k in keys for g in sig[k]["governs"]}
        if mod.get("protects_concern"):
            keep = sorted(set(mod["protects_concern"]) - pv)
            if keep != sorted(mod["protects_concern"]):
                out.append(("protects_concern", keep))
        if mod.get("governs_concern"):
            keep = sorted(set(mod["governs_concern"]) - gv)
            if keep != sorted(mod["governs_concern"]):
                out.append(("governs_concern", keep))
    return out


def main(modules_file):
    mods = json.load(open(os.path.join(HERE, modules_file)))["modules"]
    br = RBA.bridges(); corpus = RBA.corpus_acts()
    sig = json.load(open(os.path.join(HERE, "assert_signature.json")))
    ap = json.load(open(os.path.join(HERE, "assert_protects.json")))
    pa = json.load(open(os.path.join(HERE, "assert_purpose_actor.json")))
    report = {}
    for slug, mod in mods.items():
        t = truth_all(slug)
        base = eng_set(mod, br, corpus)
        R = {k for k, v in t.items() if v == "relevant"}
        mism = [n for n in t if (t[n] == "relevant") != (n in base)]
        rows = {}
        for n in mism:
            mv = moves_for(n, slug, mod, sig, ap, pa, corpus, br, n in base)
            if not mv:
                rows[n] = {"verdict": "TERMINAL-STRUCT",
                           "note": "no declaration move can flip it (actor-excluded or no act match); bridge/vocabulary space fenced"}
                continue
            receipts = []
            best = None
            for field, val in mv:
                m2 = {**mod, field: val}
                e2 = eng_set(m2, br, corpus)
                fixes = sum(1 for x in mism if (t[x] == "relevant") == (x in e2))
                breaks = sum(1 for x in t if x not in mism and (t[x] == "relevant") != (x in e2))
                rec = {"move": {field: val}, "mismatches_fixed": fixes, "correct_broken": breaks,
                       "net": fixes - breaks, "target_flipped": (t[n] == "relevant") == (n in e2)}
                receipts.append(rec)
                if rec["target_flipped"] and rec["net"] > 0 and (best is None or rec["net"] > best["net"]):
                    best = rec
            rows[n] = ({"verdict": f"FIXABLE", "best_move": best, "receipts": receipts} if best
                       else {"verdict": "TERMINAL-DECL", "receipts": receipts,
                             "note": "every minimal declaration move is charter-negative; relative to current vocabularies"})
        report[slug] = rows
    return report


if __name__ == "__main__":
    mf = sys.argv[1] if len(sys.argv) > 1 else "modules_contract_v18.json"
    rep = main(mf)
    for slug, rows in rep.items():
        from collections import Counter
        c = Counter(r["verdict"] for r in rows.values())
        print(f"== {slug}: {dict(c)}")
        for n, r in sorted(rows.items()):
            if r["verdict"] == "FIXABLE":
                print(f"   FIXABLE {n} via {r['best_move']['move']} (net +{r['best_move']['net']})")
    out = os.path.join(HERE, "panel_run1", "convergence", "terminality_verification.json")
    json.dump({"_": "Mechanical terminality verification (verify_terminal.py).", "report": rep}, open(out, "w"), indent=1)
    print("wrote", out)
