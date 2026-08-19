#!/usr/bin/env python3
"""PER-ASSERT `protects` ANNOTATION — the E1 fix, run INCREMENTALLY
(Matt's protocol 2026-08-18: calibration nodes with PRE-REGISTERED expected
outcomes first; broaden only on confirmation).

For each assert in a module: whose interest does THIS norm protect, judged
from the read_back + source span. Values: user | third_party | minor |
society | developer | unspecified. Side-layer output (assert_protects.json
keyed module|index) — sealed modules untouched, fully reversible.

Usage: .../.venv/bin/python annotate_protects.py --nodes id1 id2 ...   (calibration)
       .../.venv/bin/python annotate_protects.py --all                 (only after calibration passes)
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "..", ".."))
import live_pilot, translate, link_nodes
VALS = ["user", "third_party", "minor", "society", "developer", "unspecified"]
BRIEF = ("For each numbered NORM from a spec regulating an AI assistant you get: the norm as asserted (read_back), its deontic status, and the source "
 "span it translates. Whose INTEREST does the norm protect — who is the norm FOR? "
 "user = the person in the conversation (their safety, data, autonomy, time, wellbeing); third_party = specific people outside the conversation "
 "(the person a user wants to harm, people whose private data would be shared, other creators); minor = minors specifically; society = the public, "
 "institutions, the world at large (electoral integrity, public health, infohazards); developer = the developer/operator's interests (confidentiality "
 "of instructions, business); unspecified = the norm's protection is not fixed by the text (formatting, style, epistemic quality norms). "
 "A norm can protect MORE THAN ONE party when the text supports it — list all that the SPAN supports, never infer beyond it. "
 "JSON only: {\"<n>\": [\"<party>\", ...]}.")


def annotate(node_ids):
    quotes = {c["id"]: c["quote"] for c in json.load(open(os.path.join(os.path.dirname(HERE), "node_corpus_all.json")))["clauses"]}
    sel = link_nodes.gather()
    out_p = os.path.join(HERE, "assert_protects.json"); out = json.load(open(out_p)) if os.path.exists(out_p) else {}
    complete = live_pilot.seat_client(max_tokens=2500); complete.client.cfg["model"]["format_forcing"] = "json_object"; complete.client.forcing = "json_object"
    translate.set_run_tag("assert_protects")
    for cid in node_ids:
        lp, o, r = sel[link_nodes.norm_id(cid)]
        asserts = o.get("asserts") or []
        if not asserts: continue
        q = quotes.get(cid, ""); span = q[q.find("ESTABLISHES"):][:500] if "ESTABLISHES" in q else q[:500]
        items = "\n".join(f"{i}. [{a.get('status')}] {str(a.get('read_back'))[:160]}" for i, a in enumerate(asserts))
        user = f"SOURCE SPAN:\n{span}\n\nNORMS:\n{items}\n\nJSON only."
        try:
            m = re.search(r"\{.*\}", complete(BRIEF, user).get("text",""), re.S); d = json.loads(m.group(0)) if m else {}
        except Exception as ex:
            print(cid, "failed", repr(ex)[:80]); continue
        for i in range(len(asserts)):
            vs = [v for v in (d.get(str(i)) or []) if v in VALS]
            out[f"{link_nodes.norm_id(cid)}|{i}"] = vs or ["unspecified"]
    json.dump(out, open(out_p, "w"), indent=1)
    return complete.client.spent_usd


if __name__ == "__main__":
    if "--nodes" in sys.argv:
        ids = sys.argv[sys.argv.index("--nodes") + 1:]
    elif "--all" in sys.argv:
        cal = json.load(open(os.path.join(HERE, "protects_calibration.json")))
        assert cal.get("calibration_passed") is True, "REFUSED: calibration not confirmed (protects_calibration.json)"
        ids = sorted(link_nodes.gather())
    spent = annotate(ids)
    print(f"annotated {len(ids)} node(s); ${spent:.4f}")
