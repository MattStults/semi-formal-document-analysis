#!/usr/bin/env python3
"""
Phase U: Merge children graphs and report dangling needs.
Reads three child graph.json files, concatenates nodes/uncovered,
builds provides index, and reports all dangling needs.
"""

import json
import sys
from collections import defaultdict

# Paths
C21_PATH = "/private/tmp/claude-501/-Users-mattstults-Documents-ai-safety-projects-semi-formal-document-analysis/ad93b6a7-c890-4a7e-bb0a-d340c85c8451/scratchpad/recurse/c21/graph.json"
C22_PATH = "/private/tmp/claude-501/-Users-mattstults-Documents-ai-safety-projects-semi-formal-document-analysis/ad93b6a7-c890-4a7e-bb0a-d340c85c8451/scratchpad/recurse/c22/graph.json"
C23_PATH = "/private/tmp/claude-501/-Users-mattstults-Documents-ai-safety-projects-semi-formal-document-analysis/ad93b6a7-c890-4a7e-bb0a-d340c85c8451/scratchpad/recurse/c23/graph.json"

def load_graph(path):
    """Load a graph.json file."""
    with open(path, 'r') as f:
        return json.load(f)

def build_provides_index(nodes):
    """
    Build an index: name -> [(node_id, prose), ...]
    Maps each provided concept name to the nodes that provide it.
    """
    index = defaultdict(list)
    for node in nodes:
        if 'provides' in node:
            for provide in node['provides']:
                name = provide['name']
                prose = provide.get('prose', '')
                index[name].append((node['id'], prose))
    return index

def find_dangling_needs(nodes, provides_index):
    """
    Find all needs entries that have no provider in the provides_index.
    Returns: list of (node_id, need_name, need_prose)
    """
    dangling = []
    for node in nodes:
        if 'needs' in node:
            for need in node['needs']:
                name = need['name']
                if name not in provides_index:
                    prose = need.get('prose', '')
                    dangling.append((node['id'], name, prose))
    return dangling

def main():
    print("=" * 80)
    print("PHASE U: MERGE GRAPHS AND REPORT DANGLING NEEDS")
    print("=" * 80)

    # Load children graphs
    print("\nLoading child graphs...")
    c21 = load_graph(C21_PATH)
    c22 = load_graph(C22_PATH)
    c23 = load_graph(C23_PATH)

    c21_nodes = c21.get('nodes', [])
    c22_nodes = c22.get('nodes', [])
    c23_nodes = c23.get('nodes', [])

    all_nodes = c21_nodes + c22_nodes + c23_nodes

    print(f"Child 1 (L171-796): {len(c21_nodes)} nodes")
    print(f"Child 2 (L797-2125): {len(c22_nodes)} nodes")
    print(f"Child 3 (L2126-3147): {len(c23_nodes)} nodes")
    print(f"Total: {len(all_nodes)} nodes")

    # Build provides index
    print("\nBuilding provides index...")
    provides_index = build_provides_index(all_nodes)
    print(f"Total unique provided names: {len(provides_index)}")

    # Find all dangling needs
    print("\nFinding dangling needs...")
    danglings = find_dangling_needs(all_nodes, provides_index)

    # Group by name for reporting
    dangling_by_name = defaultdict(list)
    for node_id, name, prose in danglings:
        dangling_by_name[name].append((node_id, prose))

    print(f"\nTotal dangling needs entries: {len(danglings)}")
    print(f"Unique dangling concept names: {len(dangling_by_name)}")

    # Report each dangling
    print("\n" + "=" * 80)
    print("DANGLING NEEDS REPORT")
    print("=" * 80)

    for name in sorted(dangling_by_name.keys()):
        entries = dangling_by_name[name]
        print(f"\n{name}:")
        for node_id, prose in entries:
            print(f"  needed by: {node_id}")
            print(f"    prose: {prose[:100]}")

        if name in provides_index:
            print(f"  PROVIDER FOUND:")
            for prov_id, prov_prose in provides_index[name]:
                print(f"    {prov_id}")
                print(f"      prose: {prov_prose[:100]}")
        else:
            print(f"  NO PROVIDER IN THIS SPAN")

    # Save detailed report to file
    report_path = "/private/tmp/claude-501/-Users-mattstults-Documents-ai-safety-projects-semi-formal-document-analysis/ad93b6a7-c890-4a7e-bb0a-d340c85c8451/scratchpad/recurse/c2/dangling_report.json"
    report_data = {
        "total_nodes": len(all_nodes),
        "total_dangling_needs": len(danglings),
        "unique_dangling_names": len(dangling_by_name),
        "provides_index_size": len(provides_index),
        "dangling_by_name": {
            name: {
                "needing_nodes": [node_id for node_id, _ in entries],
                "providers": provides_index.get(name, []) if name in provides_index else None
            }
            for name, entries in dangling_by_name.items()
        },
        "all_nodes": all_nodes
    }

    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)

    print(f"\n\nDetailed report saved to: {report_path}")
    print("\nScript complete. Proceed with manual resolution decisions.")

if __name__ == '__main__':
    main()
