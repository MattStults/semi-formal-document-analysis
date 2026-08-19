#!/usr/bin/env python3
"""H5 fix: ACTOR-tag every act functor (assistant | developer | user |
system | other) from its gloss. Bridges then carry only assistant-actor
acts into behavior matching — a developer's act engaging an
assistant-behavior was census class H5 (2 FPs). Cheap tier, ledgered."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "..", ".."))
import live_pilot, translate
BRIEF = ("For each act predicate (name, gloss) from a policy-document translation, who PERFORMS the act? "
 "assistant (the AI model/assistant acting or responding), developer (the developer configuring or instructing), user (the human user), "
 "system (the platform/OpenAI), other. If the gloss is unclear, infer from the name; default assistant only when the act is plausibly the model's. "
 "JSON only: {\"<name>\": \"assistant|developer|user|system|other\"}.")
def main():
    fun = json.load(open(os.path.join(HERE, "act_functors.json")))
    out_p = os.path.join(HERE, "act_actors.json"); out = json.load(open(out_p)) if os.path.exists(out_p) else {}
    complete = live_pilot.seat_client(max_tokens=3000); complete.client.cfg["model"]["format_forcing"] = "json_object"; complete.client.forcing = "json_object"
    translate.set_run_tag("act_actor_tagging")
    todo = [f for f in sorted(fun) if f not in out]
    for i in range(0, len(todo), 30):
        b = todo[i:i+30]
        user = "\n".join(f"- {f}: {fun[f]['gloss'][:120] or '(infer from name)'}" for f in b) + "\n\nJSON only."
        try:
            m = re.search(r"\{.*\}", complete(BRIEF, user).get("text",""), re.S); d = json.loads(m.group(0)) if m else {}
        except Exception as ex: print("batch failed", repr(ex)[:80], flush=True); d = {}
        for f in b:
            v = str(d.get(f,"")).strip()
            if v in ("assistant","developer","user","system","other"): out[f] = v
        json.dump(out, open(out_p,"w"), indent=1)
    from collections import Counter
    print("DONE:", dict(Counter(out.values())), f"${complete.client.spent_usd:.4f}", flush=True)
if __name__ == "__main__": main()
