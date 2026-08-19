#!/usr/bin/env python3
"""ACT-ARGUMENT SCOPING (H1 structural fix; Matt authorized pre-prereg
2026-08-18): type each act functor's ARGUMENT — what sort of thing the act
acts ON. Engagement then requires verb match AND argument-sort
compatibility; unknown arguments FAIL OPEN (engage) so recall is never
silently traded. The H1 exemplars: refuse_to_discuss(T) acts on a TOPIC,
a harm behavior refuses a REQUEST -> no engagement."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "..", ".."))
import live_pilot, translate
ARG_SORTS = ["request", "instruction", "topic", "content", "information", "data", "question", "response", "action", "goal", "user", "party", "tool", "message", "none", "other"]
BRIEF = ("For each act predicate (name, gloss) from a policy-document translation about an AI assistant, what SORT of thing is the act's FIRST argument — "
 "the thing acted ON? One of: " + ", ".join(ARG_SORTS) + ". "
 "Examples: refuse_request -> request; refuse_to_discuss -> topic; provide_instructions -> information; ask_clarifying_questions -> question; "
 "delete_file / send_email -> action; override_instruction -> instruction; judge_user -> user; respond_in_kind -> response; arity 0 -> none. JSON only: {\"<name>\": \"<sort>\"}.")
def main():
    fun = json.load(open(os.path.join(HERE, "act_functors.json")))
    out_p = os.path.join(HERE, "act_arg_sorts.json"); out = json.load(open(out_p)) if os.path.exists(out_p) else {}
    complete = live_pilot.seat_client(max_tokens=3000); complete.client.cfg["model"]["format_forcing"] = "json_object"; complete.client.forcing = "json_object"
    translate.set_run_tag("act_arg_sorts")
    todo = [f for f in sorted(fun) if f not in out]
    for i in range(0, len(todo), 30):
        b = todo[i:i+30]
        user = "\n".join(f"- {f} /{fun[f]['arity']}: {fun[f]['gloss'][:110] or '(infer from name)'}" for f in b) + "\n\nJSON only."
        try:
            m = re.search(r"\{.*\}", complete(BRIEF, user).get("text",""), re.S); d = json.loads(m.group(0)) if m else {}
        except Exception as ex: print("batch failed", repr(ex)[:80], flush=True); d = {}
        for f in b:
            v = str(d.get(f,"")).strip()
            if v in ARG_SORTS: out[f] = v
        json.dump(out, open(out_p,"w"), indent=1)
    from collections import Counter
    print("DONE:", dict(Counter(out.values()).most_common()), f"${complete.client.spent_usd:.4f}", flush=True)
if __name__ == "__main__": main()
