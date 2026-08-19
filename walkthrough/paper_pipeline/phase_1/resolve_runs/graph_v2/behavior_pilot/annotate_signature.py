#!/usr/bin/env python3
"""NORM-SIGNATURE ANNOTATION (contract §8 retrofit): governs_aspect + authority_plumbing
per assert. ESCALATION ARCHITECTURE: this script is the CHEAP DeepSeek seat; a Haiku
subagent labels the same packets independently; agreement keeps the label, disagreement
escalates to a Fable instance. Side-layer output assert_signature.json — sealed modules
and assert_protects.json untouched.

Input construction carries the lessons of the protects campaign (calibration r1):
ESTABLISHES + verbatim SOURCE TEXT, prompt_user.txt fallback for drifted ids, empty
spans fail LOUD.

Usage: .../.venv/bin/python annotate_signature.py --check --nodes id1 ...  (calibration)
       .../.venv/bin/python annotate_signature.py --all                    (gated on signature_calibration.json)
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "..", ".."))
import live_pilot, translate, link_nodes

ASPECTS = ["substance_usefulness", "objectivity_neutrality", "accuracy_calibration", "tone_manner",
           "safety_of_manner", "formatting_style", "identity_meta", "operational_hygiene"]
BRIEF = ("For each NORM from a spec regulating an AI assistant you get: the norm as asserted (read_back), its deontic status, and the source span. "
 "Answer TWO questions. (1) governs: WHAT QUALITY of the assistant's act does this norm constrain? One (rarely two) of: "
 "substance_usefulness = whether the response substantively helps with the task; objectivity_neutrality = balance/viewpoint fairness of wording; "
 "accuracy_calibration = truthfulness, honesty, uncertainty expression; tone_manner = interpersonal tone, warmth, directness; "
 "safety_of_manner = protective handling of a vulnerable interaction (hedging, de-escalation, disclaimers); formatting_style = layout, markdown, length, structure; "
 "identity_meta = what the assistant says about itself/its provider; operational_hygiene = agentic/tooling mechanics (metadata, side effects, tool-call handling). "
 "(2) authority_plumbing: true iff the norm is ABOUT the document's own instruction machinery (instruction levels, precedence, what counts as an instruction, "
 "which policies apply) rather than an operative response norm. DIRECTING vs DEFINING: a norm that DIRECTS the assistant to follow/obey/comply with "
 "instructions is OPERATIVE (usually substance_usefulness; authority_plumbing false); authority_plumbing true is ONLY for norms that DEFINE the machinery "
 "(what counts as an instruction, which level takes precedence, whether some text carries authority). Judge from the span including its examples and rationale. "
 "JSON only: {\"governs\": [\"<aspect>\", ...], \"authority_plumbing\": true|false}.")


def span_for(cid, quotes, lp):
    q = quotes.get(cid, "")
    if not q:
        pu = os.path.join(os.path.dirname(lp), f"{cid}.prompt_user.txt")
        if os.path.exists(pu): q = open(pu).read()
    if not q:
        raise RuntimeError(f"{cid}: EMPTY SPAN — refuse to annotate blind (contract §8)")
    est = q[q.find("ESTABLISHES"):].split("PROVIDES")[0][:600] if "ESTABLISHES" in q else q[:600]
    src = q[q.find("SOURCE TEXT"):][:2400] if "SOURCE TEXT" in q else ""
    return (est + "\n\n" + src).strip()


def annotate(node_ids, check=False, out_name="assert_signature.json"):
    quotes = {c["id"]: c["quote"] for c in json.load(open(os.path.join(os.path.dirname(HERE), "node_corpus_all.json")))["clauses"]}
    sel = link_nodes.gather()
    out_p = os.path.join(HERE, out_name); out = json.load(open(out_p)) if os.path.exists(out_p) else {}
    complete = live_pilot.seat_client(max_tokens=1500); complete.client.cfg["model"]["format_forcing"] = "json_object"; complete.client.forcing = "json_object"
    translate.set_run_tag("assert_signature")
    for cid in node_ids:
        lp, o, r = sel[link_nodes.norm_id(cid)]
        asserts = o.get("asserts") or []
        if not asserts: continue
        span = span_for(cid, quotes, lp)
        for i, a in enumerate(asserts):
            key = f"{link_nodes.norm_id(cid)}|{i}"
            user = f"SOURCE SPAN:\n{span}\n\nNORM:\n[{a.get('status')}] {str(a.get('read_back'))[:200]}\n\nJSON only."
            try:
                m = re.search(r"\{.*\}", complete(BRIEF, user).get("text", ""), re.S); d = json.loads(m.group(0)) if m else {}
            except Exception as ex:
                print(key, "failed", repr(ex)[:80]); continue
            gov = [v for v in (d.get("governs") or []) if v in ASPECTS]
            rec = {"governs": gov or ["substance_usefulness"], "authority_plumbing": bool(d.get("authority_plumbing"))}
            if check:
                print(f"CHECK {key}: {rec}")
            else:
                out[key] = rec
    if not check:
        json.dump(out, open(out_p, "w"), indent=1)
    return complete.client.spent_usd


if __name__ == "__main__":
    check = "--check" in sys.argv
    argv = [a for a in sys.argv if a != "--check"]
    if "--nodes" in argv:
        ids = argv[argv.index("--nodes") + 1:]
    elif "--all" in argv:
        cal = json.load(open(os.path.join(HERE, "signature_calibration.json")))
        assert cal.get("calibration_passed") is True, "REFUSED: calibration not confirmed (signature_calibration.json)"
        ids = sorted(link_nodes.gather())
    spent = annotate(ids, check=check)
    print(f"annotated {len(ids)} node(s); ${spent:.4f}")
