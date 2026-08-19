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

# v2 — refined with the blind audit's failure lessons (13/56 disagreements, panel_run1/protects_audit_result.json).
# v1 text kept above unchanged for the record; calibration for v2 is protects_calibration_v2.json.
BRIEF_V2 = BRIEF + (
 " AUDIT-DERIVED RULES (each fixed a real error class): "
 "(1) CO-PROTECTION: when the span's examples or rationale name harms to DIFFERENT parties (e.g. wrong dosage hurts the user AND defamatory claims hurt an outside person), list EVERY named party — the most-missed error is listing only one. "
 "(2) PROHIBITION BENEFICIARIES: a norm forbidding or declining assistance with prohibited/restricted/harmful activity protects the would-be VICTIMS of that activity (third_party/society, per what the spec says the prohibition exists for), not the requesting user alone. "
 "(3) unspecified is ONLY for norms whose protection genuinely is not fixed by the text (formatting, style, epistemic-quality). If the span names who is at risk (e.g. 'a user showing signs of mania'), use that party — never unspecified. "
 "(4) NO OVER-INFERENCE: do not add society/developer/etc. without concrete span support; developer only when an operator's business/confidentiality/product interest is concretely at stake in the span. "
 "(5) THIS SPEC'S DEFINITIONS BIND: this spec defines 'prohibited content' as ONLY sexual content involving minors — norms about prohibited content protect minor. "
 "(6) generic 'instructions' in this spec come from BOTH users and developers — a norm about following instructions serves both parties unless the span restricts it.")

# v3 — v2 rules + forced two-step elicitation (v2 calibration failed the co-protection classes:
# the seat skipped the span scan and listed one party; forcing an explicit at_risk enumeration
# first gives the JSON-forced model the intermediate step). Output schema differs — parsed below.
BRIEF_V3 = BRIEF_V2 + (
 " OUTPUT FORMAT (two steps, both required): for each numbered norm, FIRST scan the whole span — including its examples, rationale sentences, and "
 "what the spec elsewhere says a prohibition exists for — and enumerate under 'at_risk' EVERY party whose interest the span shows to be at stake; "
 "THEN give 'protects' as the subset the norm is actually FOR (usually all of at_risk). "
 "JSON only: {\"<n>\": {\"at_risk\": [\"<party>\", ...], \"protects\": [\"<party>\", ...]}}.")


def annotate(node_ids, brief=BRIEF, check=False):
    quotes = {c["id"]: c["quote"] for c in json.load(open(os.path.join(os.path.dirname(HERE), "node_corpus_all.json")))["clauses"]}
    sel = link_nodes.gather()
    lock_p = os.path.join(HERE, "protects_locked.json")
    locked = json.load(open(lock_p))["keys"] if os.path.exists(lock_p) else {}
    out_p = os.path.join(HERE, "assert_protects.json"); out = json.load(open(out_p)) if os.path.exists(out_p) else {}
    complete = live_pilot.seat_client(max_tokens=2500); complete.client.cfg["model"]["format_forcing"] = "json_object"; complete.client.forcing = "json_object"
    translate.set_run_tag("assert_protects")
    for cid in node_ids:
        lp, o, r = sel[link_nodes.norm_id(cid)]
        asserts = o.get("asserts") or []
        if not asserts: continue
        q = quotes.get(cid, "")
        if not q:
            # 15 nodes carry run-local ids absent from node_corpus_all.json (range drift);
            # their span lives in the run's own prompt_user.txt (calibration r1 finding #2)
            pu = os.path.join(os.path.dirname(lp), f"{cid}.prompt_user.txt")
            if os.path.exists(pu): q = open(pu).read()
        if brief is BRIEF:  # v1 input construction, kept verbatim for the record
            span = q[q.find("ESTABLISHES"):][:500] if "ESTABLISHES" in q else q[:500]
        else:
            # v3+ INPUT FIX (calibration r1 finding): the 500-char cut carried only the
            # ESTABLISHES paraphrase + scaffolding — the verbatim SOURCE TEXT with the
            # examples the protects judgment needs was never shown to the seat.
            est = q[q.find("ESTABLISHES"):].split("PROVIDES")[0][:600] if "ESTABLISHES" in q else q[:600]
            src = q[q.find("SOURCE TEXT"):][:2400] if "SOURCE TEXT" in q else ""
            span = (est + "\n\n" + src).strip()
        items = "\n".join(f"{i}. [{a.get('status')}] {str(a.get('read_back'))[:160]}" for i, a in enumerate(asserts))
        user = f"SOURCE SPAN:\n{span}\n\nNORMS:\n{items}\n\nJSON only."
        try:
            m = re.search(r"\{.*\}", complete(brief, user).get("text",""), re.S); d = json.loads(m.group(0)) if m else {}
        except Exception as ex:
            print(cid, "failed", repr(ex)[:80]); continue
        for i in range(len(asserts)):
            raw = d.get(str(i)) or []
            if isinstance(raw, dict): raw = raw.get("protects") or []  # v3 two-step schema
            vs = [v for v in raw if v in VALS]
            key = f"{link_nodes.norm_id(cid)}|{i}"
            if check:
                print(f"CHECK {key}: model={sorted(vs) or ['unspecified']} current={sorted(out.get(key, []))} locked={sorted(locked[key]['values']) if key in locked else '-'}")
                continue
            if key in locked:  # audit-verified ground truth is never overwritten
                continue
            out[key] = vs or ["unspecified"]
    if not check:
        json.dump(out, open(out_p, "w"), indent=1)
    return complete.client.spent_usd


if __name__ == "__main__":
    brief = BRIEF_V3 if "--v3" in sys.argv else BRIEF_V2 if "--v2" in sys.argv else BRIEF
    check = "--check" in sys.argv  # print comparison, write nothing
    argv = [a for a in sys.argv if a not in ("--v2", "--v3", "--check")]
    if "--nodes" in argv:
        ids = argv[argv.index("--nodes") + 1:]
    elif "--all" in argv:
        cal_name = "protects_calibration.json" if brief is BRIEF else "protects_calibration_v2.json"
        cal = json.load(open(os.path.join(HERE, cal_name)))
        assert cal.get("calibration_passed") is True, f"REFUSED: calibration not confirmed ({cal_name})"
        ids = sorted(link_nodes.gather())
    spent = annotate(ids, brief=brief, check=check)
    print(f"annotated {len(ids)} node(s); ${spent:.4f}")
