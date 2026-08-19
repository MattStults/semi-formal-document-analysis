#!/usr/bin/env python3
"""PARTY-TYPED ACT ARGUMENTS (Matt's decision 2, 2026-08-18): for each act
functor, WHO does the act's object/beneficiary/victim concern, where the
gloss expresses it: user | third_party | developer | assistant_self |
unspecified. The E1 structural fix: harm-avoidance then walls on
third_party-concerning acts; unspecified FAILS OPEN (never trade recall
silently — the arg-sort lesson)."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "..", ".."))
import live_pilot, translate
VALS = ["user", "third_party", "developer", "assistant_self", "unspecified"]
BRIEF = ("For each act predicate (name, gloss) from a spec regulating an AI assistant: whose interests does the act's object/beneficiary/victim CONCERN, "
 "when the gloss says? user = the person in the conversation (their safety, data, autonomy, wellbeing); third_party = people OUTSIDE the conversation, "
 "society, other creators, minors depicted, the world; developer = the developer/operator; assistant_self = the assistant itself; unspecified = the gloss "
 "does not fix a party (most content/formatting/answering acts). Be conservative: only assign a party the gloss actually expresses. "
 "JSON only: {\"<name>\": \"" + "|".join(VALS) + "\"}.")
def main():
    fun = json.load(open(os.path.join(HERE, "act_functors.json")))
    out_p = os.path.join(HERE, "act_party.json"); out = json.load(open(out_p)) if os.path.exists(out_p) else {}
    complete = live_pilot.seat_client(max_tokens=3000); complete.client.cfg["model"]["format_forcing"] = "json_object"; complete.client.forcing = "json_object"
    translate.set_run_tag("act_party_typing")
    todo = [f for f in sorted(fun) if f not in out]
    for i in range(0, len(todo), 30):
        b = todo[i:i+30]
        user = "\n".join(f"- {f}: {fun[f]['gloss'][:120] or '(infer from name)'}" for f in b) + "\n\nJSON only."
        try:
            m = re.search(r"\{.*\}", complete(BRIEF, user).get("text",""), re.S); d = json.loads(m.group(0)) if m else {}
        except Exception as ex: print("batch failed", repr(ex)[:80], flush=True); d = {}
        for f in b:
            v = str(d.get(f,"")).strip()
            if v in VALS: out[f] = v
        json.dump(out, open(out_p,"w"), indent=1)
    from collections import Counter
    print("DONE:", dict(Counter(out.values()).most_common()), f"${complete.client.spent_usd:.4f}", flush=True)
if __name__ == "__main__": main()
