#!/usr/bin/env python3
"""Round-4 draw + packet builder (per signed ROUND4_PREREG.md).

Deterministic: draw = random.Random(seed).sample over the SORTED pools from
ROUND4_FREEZE_DERIVATION.json (40/side, or the whole side when the prereg
closed the population). Packets reuse ruling_packets.RULING_PROMPT + spans.
Shuffle seed = the behaviour's registered draw seed. Panels: the registered
sha sampler, sha256(f"panel:{seed}:{i}") uniform < 0.2 on the shuffled
1-based row index. Usage: round4_run.py <slug>."""
import hashlib, json, random, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import relevance_by_act as RBA
import ruling_packets as RP

slug = sys.argv[1]
fz = json.load(open("ROUND4_FREEZE_DERIVATION.json"))["behaviours"][slug]
seed = fz["seed"]
b = json.load(open("ROUND4_FREEZE_DERIVATION.json"))
mods = json.load(open("modules_contract_v19.json"))["modules"]
corpus = RBA.corpus_acts(); br = RBA.bridges()
_, rel = RBA.relevance(mods[slug], br, corpus); eng = set(rel)
excl = set(fz["excluded_nodes"])
pool_e = sorted((set(corpus) - excl) & eng)
pool_n = sorted((set(corpus) - excl) - eng)
assert len(pool_e) == fz["pool_engaged_n"] and len(pool_n) == fz["pool_not_engaged_n"], "pool drift vs freeze"
rnd = random.Random(seed)
draw_e = pool_e if len(pool_e) <= 48 else sorted(rnd.sample(pool_e, 40))
draw_n = pool_n if len(pool_n) <= 48 else sorted(rnd.sample(pool_n, 40))
spans = RP.load_spans()
dfn = mods[slug].get("definition", "")
packets = [{"node": n, "side": "E" if n in eng else "N",
            "prompt": RP.RULING_PROMPT.format(label=slug, query=dfn,
                boundary="(see definition)", node=n, span=spans.get(n, "SPAN MISSING"))}
           for n in draw_e + draw_n]
missing = [p["node"] for p in packets if "SPAN MISSING" in p["prompt"]]
random.Random(seed).shuffle(packets)
panels = [i for i in range(1, len(packets)+1)
          if int(hashlib.sha256(f"panel:{seed}:{i}".encode()).hexdigest()[:8],16)/0xFFFFFFFF < 0.2]
json.dump({"_": f"ROUND-4 {slug}: seeded draw + BLIND packets. side is POST-RULING routing metadata, never seat material. Shuffle seed = draw seed (registered in ROUND4_PREREG.md); panel rows via the registered sha sampler.",
           "slug": slug, "seed": seed, "n": len(packets),
           "draw_engaged": draw_e, "draw_not_engaged": draw_n,
           "panel_rows": panels, "packets": packets},
          open(f"round4_{slug}_packets.json", "w"), indent=1)
print(json.dumps({"slug": slug, "n": len(packets), "engaged": len(draw_e),
                  "not_engaged": len(draw_n), "panel_rows": panels,
                  "missing_spans": missing}))
