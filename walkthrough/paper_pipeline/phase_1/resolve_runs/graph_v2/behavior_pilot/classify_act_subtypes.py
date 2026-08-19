#!/usr/bin/env python3
"""Act ontology refinement r1: split the two catch-all buckets into SUBTYPES.
Two-level ontology — every subtype IMPLIES its parent via a bridge rule
(canonical_act(provide(X)) :- canonical_act(provide_hazardous(X))), so
nothing coarsens: behaviors may perform either level. Subtypes chosen for
the scope discriminations the measured precision gaps need (harm-avoidance
0.73 through provide; helpfulness respond 27% catch-all).

provide  -> provide_information | provide_content | provide_resources |
            disclose_data | provide_hazardous | provide (generic)
respond  -> answer_directly | respond_in_manner | acknowledge |
            express_stance | respond (generic)
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "..", ".."))
import live_pilot, translate
SUB = {"provide": ["provide_information", "provide_content", "provide_resources", "disclose_data", "provide_hazardous", "provide"],
       "respond": ["answer_directly", "respond_in_manner", "acknowledge", "express_stance", "respond"]}
GLOSS = {"provide_information": "give neutral factual information or explanation",
         "provide_content": "produce requested content/artifacts (creative text, code, documents)",
         "provide_resources": "offer resources, referrals, alternatives, or support options",
         "disclose_data": "reveal private, confidential, internal, or privileged data",
         "provide_hazardous": "supply hazardous, illicit-enabling, or actionable-harm material",
         "provide": "generic provision not fitting a subtype",
         "answer_directly": "answer the question substantively and directly",
         "respond_in_manner": "shape the tone, style, format, or manner of a response",
         "acknowledge": "acknowledge, admit, or note something in the response",
         "express_stance": "state an opinion, stance, assessment, or position",
         "respond": "generic responding not fitting a subtype"}


def main():
    br = json.load(open(os.path.join(HERE, "act_bridges.json")))
    fun = json.load(open(os.path.join(HERE, "act_functors.json")))
    out_p = os.path.join(HERE, "act_subtypes.json"); out = json.load(open(out_p)) if os.path.exists(out_p) else {}
    complete = live_pilot.seat_client(max_tokens=3000); complete.client.cfg["model"]["format_forcing"] = "json_object"; complete.client.forcing = "json_object"
    translate.set_run_tag("act_subtype_classify")
    for parent, subs in SUB.items():
        members = [f for f, v in br.items() if v["canonical"] == parent and f not in out]
        brief = (f"Classify each bespoke act (name, gloss) into ONE subtype of '{parent}': "
                 + "; ".join(f"{s}: {GLOSS[s]}" for s in subs)
                 + f". Use '{parent}' only when no subtype fits. JSON only: {{\"<name>\": \"<subtype>\"}}.")
        for i in range(0, len(members), 25):
            b = members[i:i+25]
            user = "\n".join(f"- {f}: {fun[f]['gloss'][:140] or '(no gloss; infer from name)'}" for f in b) + "\n\nJSON only."
            try:
                m = re.search(r"\{.*\}", complete(brief, user).get("text", ""), re.S); d = json.loads(m.group(0)) if m else {}
            except Exception as ex: print("batch failed", repr(ex)[:80], flush=True); d = {}
            for f in b:
                v = str(d.get(f, "")).strip()
                if v in subs: out[f] = v
            json.dump(out, open(out_p, "w"), indent=1)
        print(f"{parent}: {len([f for f in out if br.get(f,{}).get('canonical')==parent])} classified; ${complete.client.spent_usd:.4f}", flush=True)
    # regenerate act_bridges.lp WITH subtypes + parent-implication rules
    lines = ["% act_bridges.lp — GENERATED (classify_acts.py + classify_act_subtypes.py r1). Two-level act ontology.",
             "% Bespoke -> finest canonical; subtype implies parent, so coarse behaviors lose nothing."]
    for s in sorted(set(out.values())):
        if s not in ("provide", "respond"):
            parent = "provide" if s.startswith(("provide", "disclose")) else "respond"
            lines.append(f"canonical_act({parent}(X)) :- canonical_act({s}(X)).")
    for f, v in sorted(br.items()):
        c = out.get(f, v["canonical"])
        if str(c).startswith("NEW:"): continue
        ar = fun[f]["arity"]
        if ar == 0: lines.append(f"canonical_act({c}(unit)) :- {f}.")
        elif ar == 1: lines.append(f"canonical_act({c}(X)) :- {f}(X).")
        else: lines.append(f"canonical_act({c}(X)) :- {f}(X" + ",_"*(ar-1) + ").")
    open(os.path.join(HERE, "act_bridges.lp"), "w").write("\n".join(lines) + "\n")
    from collections import Counter
    print("DONE:", dict(Counter(out.values())), flush=True)


if __name__ == "__main__": main()
