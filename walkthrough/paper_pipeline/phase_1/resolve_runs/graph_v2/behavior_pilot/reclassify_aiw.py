#!/usr/bin/env python3
"""Act refinement r2b (A5-driven): re-classify the act_in_world and
express_uncertainty buckets under a SHARPENED brief. Measured failure
(blind spot-check, 50/62): internal deliberation / interpretive stances /
content-shaping steps were filed under act_in_world; misrepresentation
under express_uncertainty. The line, stated: act_in_world ONLY when the act
has an effect OUTSIDE the conversation through a tool or action (sending,
deleting, deploying, purchasing, executing); anything that merely shapes
the response is respond; supplying content/info is provide; genuine
hedging only is express_uncertainty."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "..", ".."))
import live_pilot, translate
CANON = ["respond","refuse","comply","provide","ask","act_in_world","override","express_uncertainty","pursue_goal","judge_or_moralize","engage_relationship"]
BRIEF = ("Re-classify each bespoke act into ONE canonical act: " + ", ".join(CANON) + ". "
 "STRICT RULES (each cites a measured mis-classification): act_in_world ONLY for acts with effect OUTSIDE the conversation via tools/actions "
 "(send, delete, deploy, execute, purchase, modify external systems). An internal interpretive stance, deliberation, inference, weighing, or "
 "content-formatting step is respond. Producing/supplying content, guidance, or resources IN the response is provide. express_uncertainty ONLY "
 "for genuine hedging/conveying uncertainty — misrepresentation (downplaying, sugar-coating, misleading) is respond. "
 "JSON only: {\"<name>\": \"<canonical>\"}.")
def main():
    br = json.load(open(os.path.join(HERE, "act_bridges.json")))
    fun = json.load(open(os.path.join(HERE, "act_functors.json")))
    targets = [f for f, v in br.items() if v["canonical"] in ("act_in_world", "express_uncertainty") and "spot-check correction" not in v.get("why","")]
    complete = live_pilot.seat_client(max_tokens=3000); complete.client.cfg["model"]["format_forcing"] = "json_object"; complete.client.forcing = "json_object"
    translate.set_run_tag("act_reclassify_aiw")
    changed = 0
    for i in range(0, len(targets), 25):
        b = targets[i:i+25]
        user = "\n".join(f"- {f}: {fun[f]['gloss'][:140] or '(no gloss; infer from name)'}" for f in b) + "\n\nJSON only."
        try:
            m = re.search(r"\{.*\}", complete(BRIEF, user).get("text", ""), re.S); d = json.loads(m.group(0)) if m else {}
        except Exception as ex: print("batch failed", repr(ex)[:80], flush=True); d = {}
        for f in b:
            c = str(d.get(f, "")).strip()
            if c in CANON and c != br[f]["canonical"]:
                br[f] = {"canonical": c, "why": "r2b sharpened-brief reclassification"}; changed += 1
        json.dump(br, open(os.path.join(HERE, "act_bridges.json"), "w"), indent=1)
    print(f"DONE: {len(targets)} re-examined, {changed} moved; ${complete.client.spent_usd:.4f}", flush=True)
if __name__ == "__main__": main()
