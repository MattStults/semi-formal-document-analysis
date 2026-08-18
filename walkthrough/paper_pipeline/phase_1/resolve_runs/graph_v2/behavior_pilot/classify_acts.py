#!/usr/bin/env python3
"""Classify every bespoke corpus act functor into the canonical act ontology
(ONTOLOGY_CONTRACT_DRAFT.md, provisional list) using the cheap tier, batched.
Output: act_bridges.json {functor: {"canonical": ..., "confidence": ..., "why": ...}}.
`NEW:<name>` is an allowed answer when no canonical act fits — that is how a
genuinely novel act surfaces for the ontology instead of being forced. Every
call ledgered. Then act_bridges.lp is GENERATED (never edits the 762 modules).
"""
import json, os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "..", ".."))
import live_pilot, translate
CANON = json.load(open(os.path.join(HERE, "behavior_vocab.json")))["canonical_acts_provisional"]
BRIEF = ("You classify ACT predicates from a policy-document translation into a small canonical act ontology. "
 "Canonical acts (name: what its argument is): " + "; ".join(f"{k}: {v[1]}" for k, v in CANON.items()) + ". "
 "For each bespoke act you are given (name, arity, gloss, an example module), answer with the ONE canonical act it is a kind of. "
 "A refusal in a judgmental tone is a kind of refuse; providing crisis resources is a kind of provide; asking for confirmation is a kind of ask; "
 "sending an email or deleting a file is act_in_world; adopting or optimizing for a goal is pursue_goal; being preachy/judgmental is judge_or_moralize; "
 "hedging or adding disclaimers is express_uncertainty; overriding or ignoring an instruction is override; romantic/relationship engagement is engage_relationship; "
 "answering, producing a response, or responding in a manner is respond; complying with or following an instruction is comply. "
 "If NONE fits, answer NEW:<snake_case_name> and say why in one clause. Reply with a JSON object mapping each functor to {\"canonical\": ..., \"why\": ...}. JSON only.")

def main():
    acts = json.load(open(os.path.join(HERE, "act_functors.json")))
    out_p = os.path.join(HERE, "act_bridges.json")
    out = json.load(open(out_p)) if os.path.exists(out_p) else {}
    todo = [f for f in sorted(acts) if f not in out]
    complete = live_pilot.seat_client(max_tokens=3000); translate.set_run_tag("act_ontology_classify")
    for i in range(0, len(todo), 25):
        batch = todo[i:i+25]
        user = "\n".join(f"- {f} /{acts[f]['arity']} — gloss: {acts[f]['gloss'][:160] or '(none)'} — e.g. module {acts[f]['modules'][0]}" for f in batch) + "\n\nClassify each. JSON only."
        try:
            env = complete(BRIEF, user); txt = env.get("text","")
            m = re.search(r"\{.*\}", txt, re.S); d = json.loads(m.group(0)) if m else {}
        except Exception as ex:
            print("batch failed:", repr(ex)[:120]); d = {}
        for f in batch:
            v = d.get(f) or {}
            c = str(v.get("canonical","")).strip()
            if c and (c in CANON or c.startswith("NEW:")):
                out[f] = {"canonical": c, "why": str(v.get("why",""))[:200]}
        json.dump(out, open(out_p,"w"), indent=1)
        print(f"{min(i+25,len(todo))}/{len(todo)} classified; ${complete.client.spent_usd:.4f}", flush=True)
    news = [f for f,v in out.items() if v["canonical"].startswith("NEW:")]
    print(f"done: {len(out)} classified, {len(news)} NEW proposals: {sorted(set(v['canonical'] for f,v in out.items() if v['canonical'].startswith('NEW:')))[:20]}")
    # bridges .lp
    lines = ["% act_bridges.lp — GENERATED (classify_acts.py, 2026-08-18). Bespoke corpus acts -> canonical act ontology.",
             "% Never edits the 762 modules; loaded beside them. canonical_act(<canon>(X)) :- <bespoke>(X).",
             "% Arity: bespoke acts are arity 1 in the corpus (act(X)); higher arities bridge on their first argument."]
    for f, v in sorted(out.items()):
        c = v["canonical"]
        if c.startswith("NEW:"): continue
        ar = acts[f]["arity"]
        if ar == 0: lines.append(f"canonical_act({c}(unit)) :- {f}.")
        elif ar == 1: lines.append(f"canonical_act({c}(X)) :- {f}(X).")
        else: lines.append(f"canonical_act({c}(X)) :- {f}(X" + ",_"*(ar-1) + ").")
    open(os.path.join(HERE, "act_bridges.lp"),"w").write("\n".join(lines)+"\n")
    print("wrote act_bridges.lp:", len(lines)-3, "bridges")
if __name__ == "__main__": main()
