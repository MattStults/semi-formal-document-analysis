#!/usr/bin/env python3
"""
Phase U: Unwind and link children's graphs for root span.
Concatenate, resolve cross-child dependencies, identify renames/merges.
"""

import json
from collections import defaultdict
from pathlib import Path

# Load child graphs
c1_path = Path("/private/tmp/claude-501/-Users-mattstults-Documents-ai-safety-projects-semi-formal-document-analysis/ad93b6a7-c890-4a7e-bb0a-d340c85c8451/scratchpad/recurse/c1/graph.json")
c2_path = Path("/private/tmp/claude-501/-Users-mattstults-Documents-ai-safety-projects-semi-formal-document-analysis/ad93b6a7-c890-4a7e-bb0a-d340c85c8451/scratchpad/recurse/c2/graph.json")
c3_path = Path("/private/tmp/claude-501/-Users-mattstults-Documents-ai-safety-projects-semi-formal-document-analysis/ad93b6a7-c890-4a7e-bb0a-d340c85c8451/scratchpad/recurse/c3/graph.json")

with open(c1_path) as f:
    c1_graph = json.load(f)
with open(c2_path) as f:
    c2_graph = json.load(f)
with open(c3_path) as f:
    c3_graph = json.load(f)

# Concatenate nodes
all_nodes = c1_graph["nodes"] + c2_graph["nodes"] + c3_graph["nodes"]
all_uncovered = c1_graph.get("uncovered", []) + c2_graph.get("uncovered", []) + c3_graph.get("uncovered", [])

# Build provides index: name -> list of (node_id, node)
provides_index = defaultdict(list)
for node in all_nodes:
    for prov in node.get("provides", []):
        provides_index[prov["name"]].append((node["id"], node))

# Track dangling needs and resolutions
dangling_with_provider = []  # (node_id, needs_name, provider_nodes)
duplicate_providers = defaultdict(list)  # name -> list of (node_id, node)
needs_by_node = defaultdict(lambda: defaultdict(list))  # node_id -> name -> list of needs entries

# Scan for dangling and duplicates
for node in all_nodes:
    for needs_entry in node.get("needs", []):
        needs_name = needs_entry["name"]
        needs_by_node[node["id"]][needs_name].append(needs_entry)

        # Check if it has a provider in the same child
        has_provider_in_child = False
        for prov_node in all_nodes:
            if prov_node["id"].split("_")[0] == node["id"].split("_")[0]:  # same child
                for prov in prov_node.get("provides", []):
                    if prov["name"] == needs_name:
                        has_provider_in_child = True
                        break

        # If no provider in same child, look across children
        if not has_provider_in_child and needs_name in provides_index:
            dangling_with_provider.append((node["id"], needs_name, provides_index[needs_name]))

# Find duplicate providers (names provided by more than one node)
for name, providers in provides_index.items():
    if len(providers) > 1:
        duplicate_providers[name] = providers

# Report duplicates for manual decision
print("=" * 80)
print("DUPLICATE PROVIDERS (restatement merge candidates):")
print("=" * 80)
for name, providers in sorted(duplicate_providers.items()):
    print(f"\n{name}:")
    for node_id, node in providers:
        print(f"  - {node_id}: {node.get('establishes', '')[:80]}")

# Report dangling with providers
print("\n" + "=" * 80)
print("DANGLING NEEDS WITH SAME-NAME PROVIDERS:")
print("=" * 80)
for node_id, needs_name, providers in dangling_with_provider:
    print(f"\n{node_id} needs '{needs_name}'")
    for prov_id, _ in providers:
        print(f"  - provided by {prov_id}")

# Alias candidates to check
print("\n" + "=" * 80)
print("ALIAS CANDIDATES TO EXAMINE:")
print("=" * 80)
alias_candidates = [
    ("self_harm_prohibition", "do_not_encourage_self_harm"),
    ("respect_real_world_ties", "respect_real_world_ties_principle"),
    ("avoid_info_hazards", "avoid_information_hazards"),
    ("avoid_overstepping", "avoid_overstepping_principle"),
    ("conscientious_employee_metaphor", "conscientious_employee"),
    ("assume_best_intentions_principle", "assume_best_intentions"),
    ("avoid_errors_principle", "avoid_errors"),
    ("express_uncertainty", "express_uncertainty_principle"),
    ("letter_and_spirit", "respect_letter_and_spirit"),
    ("transformation_exception", "transform_user_content"),
    ("objective_point_of_view", "assume_objective_pov"),
    ("red_line_principles", "red_line_principles_list"),
    ("risk_taxonomy", "risk_taxonomy_framework"),
    ("behavioral_principles", "behavioral_principle"),
]

# Check which aliases have any presence
for alias1, alias2 in alias_candidates:
    has1 = any(any(p["name"] == alias1 for p in node.get("provides", [])) for node in all_nodes)
    has2 = any(any(p["name"] == alias2 for p in node.get("provides", [])) for node in all_nodes)
    has1_need = any(any(n["name"] == alias1 for n in node.get("needs", [])) for node in all_nodes)
    has2_need = any(any(n["name"] == alias2 for n in node.get("needs", [])) for node in all_nodes)

    if has1 or has2 or has1_need or has2_need:
        print(f"\n{alias1} vs {alias2}:")
        if has1: print(f"  - {alias1} PROVIDED: yes")
        if has2: print(f"  - {alias2} PROVIDED: yes")
        if has1_need: print(f"  - {alias1} NEEDED: yes")
        if has2_need: print(f"  - {alias2} NEEDED: yes")

print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)
print(f"Total nodes: {len(all_nodes)}")
print(f"Duplicate provider names: {len(duplicate_providers)}")
print(f"Dangling needs with providers: {len(dangling_with_provider)}")
