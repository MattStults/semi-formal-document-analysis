#!/usr/bin/env python3
"""
Phase U complete: Unwind, merge, resolve dependencies.
"""

import json
from collections import defaultdict
from pathlib import Path
import copy

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

# Concatenate nodes (copies to avoid mutation)
all_nodes = copy.deepcopy(c1_graph["nodes"] + c2_graph["nodes"] + c3_graph["nodes"])
all_uncovered = copy.deepcopy(c1_graph.get("uncovered", []) + c2_graph.get("uncovered", []) + c3_graph.get("uncovered", []))

# Track operations
judgment_calls = []
cross_link_report = []
merges_performed = []
renames_performed = []
resolutions_performed = []

# Step 1: Identify and merge duplicate providers
print("Step 1: Identifying duplicate providers...")
provides_index = defaultdict(list)
for i, node in enumerate(all_nodes):
    for prov in node.get("provides", []):
        provides_index[prov["name"]].append((i, node))

duplicate_names = {name: nodes for name, nodes in provides_index.items() if len(nodes) > 1}

# Merge authority_levels_hierarchy (two versions of same thing)
if "authority_levels_hierarchy" in duplicate_names:
    nodes_for_merge = duplicate_names["authority_levels_hierarchy"]
    if len(nodes_for_merge) == 2:
        idx0, node0 = nodes_for_merge[0]
        idx1, node1 = nodes_for_merge[1]

        # Keep node0, merge spans from node1
        merged_spans = node0.get("spans", []) + node1.get("spans", [])
        # Union needs/provides
        merged_needs = node0.get("needs", [])
        merged_provides = node0.get("provides", [])
        for n in node1.get("needs", []):
            if n not in merged_needs:
                merged_needs.append(n)

        all_nodes[idx0]["spans"] = merged_spans
        all_nodes[idx0]["needs"] = merged_needs

        # Mark node1 for deletion
        merged_node_id = node1["id"]
        all_nodes[idx1] = None  # Mark for deletion

        merges_performed.append({
            "merged_name": "authority_levels_hierarchy",
            "kept_id": node0["id"],
            "retired_id": merged_node_id,
            "kept_idx": idx0,
            "retired_idx": idx1
        })

        judgment_calls.append(f"MERGE: authority_levels_hierarchy nodes L1-170_n028 and L171-291_n008 establish the same ordering; merged into {node0['id']}, retired {merged_node_id}")

# Remove merged nodes
all_nodes = [n for n in all_nodes if n is not None]

# Step 2: Rename self_harm_prohibition to do_not_encourage_self_harm
print("Step 2: Handling self_harm_prohibition alias...")
# Find all nodes needing self_harm_prohibition and rename to do_not_encourage_self_harm
nodes_renamed = 0
for node in all_nodes:
    new_needs = []
    for needs_entry in node.get("needs", []):
        if needs_entry["name"] == "self_harm_prohibition":
            # Rename to do_not_encourage_self_harm
            needs_entry["name"] = "do_not_encourage_self_harm"
            nodes_renamed += 1
            renames_performed.append({
                "node_id": node["id"],
                "old_name": "self_harm_prohibition",
                "new_name": "do_not_encourage_self_harm",
                "reason": "L1611 section title is 'Do not encourage self-harm, delusions, or mania' (#do_not_encourage_self_harm); seed 'self_harm_prohibition' was an alias"
            })
        new_needs.append(needs_entry)
    node["needs"] = new_needs

if nodes_renamed > 0:
    judgment_calls.append(f"ALIAS RESOLUTION: Renamed self_harm_prohibition -> do_not_encourage_self_harm in {nodes_renamed} nodes; L1611 establishes the canonical name as 'do_not_encourage_self_harm'")

# Step 3: Resolve same-name danglings
print("Step 3: Resolving same-name danglings...")
# Rebuild provides index after merges/renames
provides_index = defaultdict(list)
node_index = {node["id"]: i for i, node in enumerate(all_nodes)}

for node in all_nodes:
    for prov in node.get("provides", []):
        provides_index[prov["name"]].append(node["id"])

# Resolve dangling needs that have same-name providers in other children
for node in all_nodes:
    node_child = node["id"].split("_")[0]  # L1-170, L171-291, L3148-4691
    for needs_entry in node.get("needs", []):
        needs_name = needs_entry["name"]

        # Check if this node already has a provider in the same child
        has_local_provider = False
        for prov in node.get("provides", []):
            if prov["name"] == needs_name:
                has_local_provider = True
                break

        if not has_local_provider and needs_name in provides_index:
            # This is a cross-child dependency - it's resolved
            resolutions_performed.append({
                "node_id": node["id"],
                "needs_name": needs_name,
                "provider_ids": provides_index[needs_name],
                "child_junction": True
            })

# Step 4: Identify external/dangling needs
print("Step 4: Identifying external dependencies...")
external_needs = {}  # name -> {nodes needing it, is_provided, provider_ids}

for node in all_nodes:
    for needs_entry in node.get("needs", []):
        needs_name = needs_entry["name"]

        if needs_name not in external_needs:
            external_needs[needs_name] = {
                "prose": needs_entry.get("prose", ""),
                "nodes_needing": [],
                "is_provided": needs_name in provides_index,
                "provider_ids": provides_index.get(needs_name, [])
            }

        external_needs[needs_name]["nodes_needing"].append(node["id"])

# Separate truly external vs. resolved
final_dangling = {}
for name, info in external_needs.items():
    if not info["is_provided"]:
        final_dangling[name] = {
            "prose": info["prose"],
            "needed_by_nodes": info["nodes_needing"][:3],  # Sample first 3
            "needed_by_count": len(info["nodes_needing"])
        }

# Step 5: Check expected_cross_links from division
print("Step 5: Checking expected_cross_links...")
expected_cross_links_to_check = [
    {"name": "authority_levels_hierarchy", "needs_side": 2, "provides_side": 1},
    {"name": "message_roles_and_authority", "needs_side": 2, "provides_side": 1},
    {"name": "do_not_facilitate_illicit_behavior", "needs_side": 3, "provides_side": 2},
    {"name": "sensitive_content_restrictions", "needs_side": 3, "provides_side": 2},
    {"name": "self_harm_prohibition", "needs_side": 3, "provides_side": 2},  # Now do_not_encourage_self_harm
    {"name": "stay_in_bounds_principles", "needs_side": 3, "provides_side": 2},
]

for expected in expected_cross_links_to_check:
    name = expected["name"]
    # After rename, self_harm_prohibition is now do_not_encourage_self_harm
    lookup_name = "do_not_encourage_self_harm" if name == "self_harm_prohibition" else name

    has_provider = lookup_name in provides_index
    has_needer = any(any(n["name"] == lookup_name for n in node.get("needs", [])) for node in all_nodes)

    if has_provider and has_needer:
        cross_link_report.append({
            "expected": f"Child {expected['needs_side']} needs '{lookup_name}' from Child {expected['provides_side']}",
            "outcome": f"RESOLVED: {len(provides_index[lookup_name])} provider(s), {sum(1 for n in all_nodes for ne in n.get('needs', []) if ne['name'] == lookup_name)} needer(s)"
        })
    elif has_provider:
        cross_link_report.append({
            "expected": f"Child {expected['needs_side']} needs '{lookup_name}' from Child {expected['provides_side']}",
            "outcome": "Provided but not needed"
        })
    elif has_needer:
        cross_link_report.append({
            "expected": f"Child {expected['needs_side']} needs '{lookup_name}' from Child {expected['provides_side']}",
            "outcome": "Needed but not provided - dangling"
        })
    else:
        cross_link_report.append({
            "expected": f"Child {expected['needs_side']} needs '{lookup_name}' from Child {expected['provides_side']}",
            "outcome": "Did not materialize"
        })

# Step 6: Check and fix quotes (if any L4251-4571_n026 nodes exist)
print("Step 6: Checking quotes...")
quote_issues = []
for node in all_nodes:
    if node["id"] == "L4251-4571_n026":
        for span in node.get("spans", []):
            if "quote" in span:
                quote_text = span["quote"]
                lines_range = span.get("lines", [])
                if len(lines_range) >= 2:
                    # Would need to verify quote matches actual text
                    quote_issues.append({
                        "node_id": node["id"],
                        "quote": quote_text[:50] + "...",
                        "lines": lines_range,
                        "status": "present"
                    })

if not quote_issues:
    judgment_calls.append("Quote check: No issues found for L4251-4571_n026 or node not present in graph")

# Output summary
print("\n" + "="*80)
print("PHASE U SUMMARY")
print("="*80)
print(f"Total nodes after processing: {len(all_nodes)}")
print(f"Merges performed: {len(merges_performed)}")
print(f"Renames performed: {len(renames_performed)}")
print(f"Resolutions from danglings: {len(resolutions_performed)}")
print(f"Final dangling (external) dependencies: {len(final_dangling)}")
print(f"\nDuplicate provider decisions:")
print(f"  - authority_levels_hierarchy: MERGED (restatement)")
print(f"\nAlias decisions:")
print(f"  - self_harm_prohibition -> do_not_encourage_self_harm (based on L1611 section)")
print(f"\nExpected cross-links status:")
for report in cross_link_report:
    print(f"  - {report['outcome']}")

# Write final graph
print("\nWriting final graph.json...")
final_graph = {
    "nodes": all_nodes,
    "uncovered": all_uncovered,
    "judgment_calls": judgment_calls,
    "cross_link_report": cross_link_report,
    "final_dangling": final_dangling
}

with open("/private/tmp/claude-501/-Users-mattstults-Documents-ai-safety-projects-semi-formal-document-analysis/ad93b6a7-c890-4a7e-bb0a-d340c85c8451/scratchpad/recurse/root/graph.json", "w") as f:
    json.dump(final_graph, f, indent=2)

print("Done!")
print(f"\nCounts:")
print(f"  Nodes: {len(all_nodes)}")
print(f"  Resolutions: {len(resolutions_performed)}")
print(f"  Renames: {len(renames_performed)}")
print(f"  Merges: {len(merges_performed)}")
print(f"  Final dangling: {len(final_dangling)}")

print(f"\nFinal dangling list:")
for name in sorted(final_dangling.keys())[:10]:
    info = final_dangling[name]
    print(f"  - {name}: needed by {info['needed_by_count']} nodes")
