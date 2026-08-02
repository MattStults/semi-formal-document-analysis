"""End-to-end interface smoke test: hand-encoded extraction -> ASP -> conflicts
-> delta -> worksheet. NOT a real extraction; it exercises the seams between
Agent A/B/C modules with real Model Spec rows."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inventory, emit_asp, delta, adjudicate

rows = {r["id"]: r for r in inventory.load_section()}
cond = [r for r in inventory.conditional(inventory.load_section())]
print(f"inventory: {len(rows)} rows, {len(cond)} conditional")

# pick two provisions that plausibly tension: follow-instructions vs a limit
a, b = cond[0], cond[1]
def span(row, n=60):
    return row["quote"][:n]

ext = {
 "section": "chain_of_command", "model": "hand", "run_id": "smoke",
 "atoms": [
   {"name":"instruction_given","kind":"context","dimension":"principal",
    "gloss":"an applicable instruction has been issued by a principal",
    "quote_spans":[{"locator":a["locator"],"focus_id":a["id"],"quote":span(a)}],
    "status":"draft"},
   {"name":"instruction_conflicts_higher","kind":"context","dimension":"principal",
    "gloss":"that instruction conflicts with a higher-authority instruction",
    "quote_spans":[{"locator":b["locator"],"focus_id":b["id"],"quote":span(b)}],
    "status":"draft"},
   {"name":"follow_instruction","kind":"act","dimension":"act",
    "gloss":"carry out the instruction as given",
    "quote_spans":[{"locator":a["locator"],"focus_id":a["id"],"quote":span(a)}],
    "status":"draft"},
   {"name":"decline_instruction","kind":"act","dimension":"act",
    "gloss":"decline to carry out the instruction",
    "quote_spans":[{"locator":b["locator"],"focus_id":b["id"],"quote":span(b)}],
    "status":"draft"},
 ],
 "rules": [
   {"id":a["id"],"modality":"oblige","act":"follow_instruction",
    "conditions":["instruction_given"],"defeaters":[],"tier":1,
    "locator":a["locator"],"quote":a["quote"],"status":"draft"},
   {"id":b["id"],"modality":"oblige","act":"decline_instruction",
    "conditions":["instruction_given","instruction_conflicts_higher"],
    "defeaters":[],"tier":1,"locator":b["locator"],"quote":b["quote"],"status":"draft"},
 ],
 "incompat": [{"acts":["follow_instruction","decline_instruction"],
               "license":"logical","source":"an instruction cannot be both carried out and declined"}],
 "exclusions": [],
 "unencoded": [{"focus_id": r["id"], "reason":"not encoded in smoke fixture"} for r in cond[2:]],
}
json.dump(ext, open("smoke_extraction.json","w"), indent=1)
print(f"extraction: {len(ext['atoms'])} atoms, {len(ext['rules'])} rules, {len(ext['unencoded'])} unencoded")

emit_asp.run(ext, "smoke.lp", "smoke_conflicts_tool.json")
tool = json.load(open("smoke_conflicts_tool.json"))
print(f"emit_asp -> {len(tool['conflicts'])} conflicts; source={tool['source']}")
for c in tool["conflicts"]:
    print(f"   {c['pair']}  ctx={c['witness']['ctx']}")

# synthetic baseline: one shared pair + one baseline-only
base = {"source":"baseline","model":"hand","run_id":"smoke-b",
        "conflicts":[dict(c, witness={"ctx":[]}) for c in tool["conflicts"]] +
                    [{"pair":sorted([cond[2]["id"], cond[3]["id"]]),"witness":{"ctx":[]},
                      "witness_prose":"a baseline-only tension","note":"synthetic"}]}
json.dump(base, open("smoke_conflicts_base.json","w"), indent=1)

m = delta.compute([tool], [base], extraction=ext)
print("delta buckets:", {k: len(v) for k, v in m["buckets"].items()} if "buckets" in m else list(m))
open("smoke_metrics.json","w").write(json.dumps(m, indent=1, default=str))
md = adjudicate.render_worksheet(m, rows, [tool], [base])
if md:
    open("smoke_worksheet.md","w").write(md)
    print(f"worksheet: {len(md)} chars, {md.count('ITEM')} items")
