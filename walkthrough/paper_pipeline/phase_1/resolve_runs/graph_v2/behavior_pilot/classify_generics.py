#!/usr/bin/env python3
"""Situation refinement r2: reachability. For each dim-less unary concept
appearing in rule bodies (dimless_blockers.json), decide:
  generic: true  — the concept holds for ANY ordinary entity of its sort
                   (gloss restates the sort: 'R is a request...'); the
                   reversal may derive it from the bare sort fact.
  dims: {...}    — the concept EXPRESSES scope-dimension values the first
                   typing pass missed.
  neither        — genuinely specific; stays unreachable (honest
                   'undetermined' in arm (b)); NOT forced."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "..", ".."))
import live_pilot, translate
DIMS = {"party": ["user","third_party","developer","minor","society"], "intent": ["benign","ambiguous","illicit"],
        "setting": ["interactive","programmatic","agentic"], "reversibility": ["reversible","irreversible"],
        "content_class": ["permitted","sensitive","restricted","prohibited"], "stakes": ["low","high"]}
BRIEF = ("For each concept (name, sort, gloss) from a policy-document ontology answer: is it GENERIC — true exactly when the concept holds for ANY "
 "ordinary entity of its sort (the gloss merely restates the sort, e.g. 'R is a request made by the user' for sort request)? A concept adding ANY "
 "qualification (explicit, applicable, cannot_be_fulfilled, quoted, good) is NOT generic. Independently: does it EXPRESS scope-dimension values? "
 "Dimensions: " + "; ".join(f"{k}: {'|'.join(v)}" for k, v in DIMS.items()) + ". "
 "JSON only: {\"<name>\": {\"generic\": true|false, \"dims\": {}}}.")
def main():
    t = json.load(open(os.path.join(HERE, "situation_types.json"))); inv = json.load(open(os.path.join(HERE, "situation_concepts.json")))
    blockers = list(json.load(open(os.path.join(HERE, "dimless_blockers.json"))))
    complete = live_pilot.seat_client(max_tokens=3000); complete.client.cfg["model"]["format_forcing"] = "json_object"; complete.client.forcing = "json_object"
    translate.set_run_tag("situation_generics")
    ng, nd = 0, 0
    for i in range(0, len(blockers), 30):
        b = [n for n in blockers[i:i+30] if n in t]
        user = "\n".join(f"- {n} (sort {t[n]['sort']}): {inv[n]['gloss'][:130]}" for n in b) + "\n\nJSON only."
        try:
            m = re.search(r"\{.*\}", complete(BRIEF, user).get("text", ""), re.S); d = json.loads(m.group(0)) if m else {}
        except Exception as ex: print("batch failed", repr(ex)[:80], flush=True); d = {}
        for n in b:
            v = d.get(n) or {}
            if v.get("generic") is True: t[n]["generic"] = True; ng += 1
            dims = {k: val for k, val in (v.get("dims") or {}).items() if k in DIMS and val in DIMS[k]}
            if dims and not t[n]["dims"]: t[n]["dims"] = dims; nd += 1
        json.dump(t, open(os.path.join(HERE, "situation_types.json"), "w"), indent=1)
    print(f"DONE: {ng} generic, {nd} gained dims, of {len(blockers)}; ${complete.client.spent_usd:.4f}", flush=True)
if __name__ == "__main__": main()
