#!/usr/bin/env python3
"""Standalone dangling-resolution pass over a COMPLETED graph (Matt's cheap
test, 2026-08-11): can the 119 stated-but-unresolved needs resolve against
the full provides index as a separate stage? Reuses unwind machinery; ~2
calls; resolved pairs are applied to a COPY, never the source graph."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.abspath(os.path.join(
    HERE, "..", "..", "..", "..", "..", "semi-formal-experiment")))
import recurse_driver as R

g = json.load(open('runs/ds3/root_graph.json'))
cfg = json.load(open('driver_config.json'))
cfg['rename_candidates'] = True     # warned attention aid, per ruling
nodes = g['nodes']
provides = {}
for n in nodes:
    for p in n.get('provides', []):
        provides.setdefault(R.nm(p), []).append(n['id'])
dangling = [{"needer": n['id'], "name": R.nm(d),
             "prose": d.get('prose', '') if isinstance(d, dict) else ''}
            for n in nodes for d in n.get('needs', [])
            if R.nm(d) not in provides]
print(f"{len(dangling)} danglings, {len(provides)} provided names")

# v2 (2026-08-11): dedicated resolution prompt -- v1 borrowed the unwind's
# anti-grind contract ("leave danglings alone") and resolved ZERO. This
# pass's ONLY job is resolution; opposite emphasis, candidates attached.
summaries = [{"id": n['id'], "establishes": n.get('establishes', ''),
              "provides": [{"name": R.nm(p), "prose": p.get('prose', '')
                            if isinstance(p, dict) else ''}
                           for p in n.get('provides', [])]}
             for n in nodes if n.get('provides')]
user = ("YOUR DISPATCH\nPhase: RESOLUTION PASS\n"
        "Your ONLY job: connect the DANGLING NEEDS below to providers that "
        "already exist in this graph. A dangling need and a provides entry "
        "describing the SAME concept in different words should be connected "
        "by renaming the need to the provider's exact name (judge on the "
        "prose MEANING, never name similarity). Be thorough: most of these "
        "danglings DO have a matching provider under a different name. Only "
        "leave a need dangling if NO provider's prose describes its "
        "concept. CANDIDATES below are lexical suggestions ONLY (the true "
        "provider is absent ~1 in 10 -- scan all providers).\n"
        f"DANGLING NEEDS:\n{json.dumps(dangling, indent=1)}\n"
        f"CANDIDATES:\n{json.dumps(R.rename_candidates(dangling, nodes), indent=1)}\n"
        f"ALL PROVIDERS:\n{json.dumps(summaries, indent=1)}\n"
        "Reply with ONE JSON object: {\"resolutions\": [{\"needer\", "
        "\"name\", \"rename_to\" (an existing provided name)}], "
        "\"merges\": [], \"structure_nodes\": [], \"judgment_calls\": "
        "[...max 10, decision classes only]}")
lines = R.load_doc('../../../../../specs/openai-model-spec/model_spec.md')
prov = R.T.Provider(name="resolve-pass", kind="openai-compatible",
    model=cfg['model']['model'], base_url=cfg['model']['base_url'],
    api_key_env=cfg['model']['api_key_env'], temperature=0.2,
    max_tokens=8192, price_per_mtok=cfg['price_per_mtok'])
client = R.GraphClient(prov, {"model": dict(cfg['model'],
    format_forcing="json_object", usage_log="DEFAULT")})
client.max_cost_usd = 0.30
drv = R.Driver(dict(cfg, max_repairs=2), client, lines, 'probes/resolve_pass')
os.makedirs('probes/resolve_pass', exist_ok=True)
test_nodes = json.loads(json.dumps(nodes))
dec = drv.call(user, lambda o: R.apply_decisions(
    json.loads(json.dumps(test_nodes)), o, provides, 1, 4692, lines)[1],
    schema=R.unwind_schema(len(dangling), len(nodes)))
log, errs = R.apply_decisions(test_nodes, dec, provides, 1, 4692, lines)
resolved = [l for l in log if l.startswith('resolved')]
after = [R.nm(d) for n in test_nodes for d in n.get('needs', [])
         if R.nm(d) not in provides]
out = {"danglings_before": len(dangling), "resolutions_applied": len(resolved),
       "danglings_after": len(set(after)), "dropped": len(log) - len(resolved),
       "spent": round(client.spent_usd, 4), "sample_resolutions": resolved[:10]}
R.write_json('probes/resolve_pass/report.json', out)
print(json.dumps(out, indent=1)[:900])
