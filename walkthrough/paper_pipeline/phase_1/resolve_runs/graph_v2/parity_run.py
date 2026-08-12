#!/usr/bin/env python3
"""10-item frontier-parity sample for the rename seat (working rule:
validate a seat on a sample before live use). Runs the REAL seat prompt
+ schema live; the frontier adjudicates the same prompts separately."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import recurse_driver as R
import rename_seat as RS

cfg = json.load(open(os.path.join(HERE, "driver_config.json")))
lines = R.load_doc(os.path.join(HERE, "..", "..", "..", "..", "..",
                                "specs", "openai-model-spec", "model_spec.md"))
g = json.load(open(os.path.join(HERE, "runs", "ds5",
                                "root_graph.pre_resolution.json")))
by_id = {n["id"]: n for n in g["nodes"]}
prov_node, prov_prose = {}, {}
for n in g["nodes"]:
    for p in n.get("provides", []):
        if isinstance(p, dict):
            prov_node.setdefault(p["name"], n)
            prov_prose.setdefault(p["name"], p.get("prose", ""))

prov = R.T.Provider(name="parity", kind="openai-compatible",
                    model=cfg["model"]["model"],
                    base_url=cfg["model"]["base_url"],
                    api_key_env=cfg["model"]["api_key_env"],
                    temperature=0.0, max_tokens=1024,
                    price_per_mtok=cfg["price_per_mtok"])
client = R.GraphClient(prov, {"model": dict(cfg["model"],
                                            format_forcing="json_object",
                                            max_tokens=1024)})
client.max_cost_usd = 0.05

out = []
for it in json.load(open(os.path.join(HERE, "parity_positive_6.json"))):
    prompt = RS.build_prompt(it["prose"], by_id.get(it["needer"]),
                             prov_prose.get(it["to"], ""),
                             prov_node.get(it["to"]), lines)
    v = RS.judge(client.complete, prompt,
                 schema_slot=lambda sch: setattr(client, "reply_schema",
                                                 sch))
    out.append({**it, "seat": v["verdict"], "grounds": v["grounds"],
                "prompt": prompt})
    print(f"{it['from']} -> {it['to']}: {v['verdict']}")
json.dump(out, open(os.path.join(HERE, "parity_positive_results.json"), "w"),
          indent=1)
print(f"spent ${client.spent_usd:.4f} over {client.calls} calls")
