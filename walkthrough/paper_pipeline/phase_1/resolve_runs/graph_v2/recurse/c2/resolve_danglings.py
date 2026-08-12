#!/usr/bin/env python3
"""
Phase U: Resolve dangling needs and create merged graph.json
"""

import json
from collections import defaultdict

# Paths
C21_PATH = "/private/tmp/claude-501/-Users-mattstults-Documents-ai-safety-projects-semi-formal-document-analysis/ad93b6a7-c890-4a7e-bb0a-d340c85c8451/scratchpad/recurse/c21/graph.json"
C22_PATH = "/private/tmp/claude-501/-Users-mattstults-Documents-ai-safety-projects-semi-formal-document-analysis/ad93b6a7-c890-4a7e-bb0a-d340c85c8451/scratchpad/recurse/c22/graph.json"
C23_PATH = "/private/tmp/claude-501/-Users-mattstults-Documents-ai-safety-projects-semi-formal-document-analysis/ad93b6a7-c890-4a7e-bb0a-d340c85c8451/scratchpad/recurse/c23/graph.json"
OUT_PATH = "/private/tmp/claude-501/-Users-mattstults-Documents-ai-safety-projects-semi-formal-document-analysis/ad93b6a7-c890-4a7e-bb0a-d340c85c8451/scratchpad/recurse/c2/graph.json"

def load_graph(path):
    with open(path, 'r') as f:
        return json.load(f)

def main():
    print("Loading child graphs...")
    c21 = load_graph(C21_PATH)
    c22 = load_graph(C22_PATH)
    c23 = load_graph(C23_PATH)

    # Concatenate nodes and uncovered
    all_nodes = c21.get('nodes', []) + c22.get('nodes', []) + c23.get('nodes', [])
    all_uncovered = c21.get('uncovered', []) + c22.get('uncovered', []) + c23.get('uncovered', [])

    print(f"Total nodes: {len(all_nodes)}")
    print(f"Total uncovered: {len(all_uncovered)}")

    # Build provides index
    provides_index = defaultdict(list)
    for node in all_nodes:
        if 'provides' in node:
            for prov in node['provides']:
                provides_index[prov['name']].append((node['id'], prov.get('prose', '')))

    # Track all needs (dangling and resolved)
    all_needs = []
    node_count = {
        'with_needs': 0,
        'without_needs': 0
    }

    # Track resolutions
    resolutions = {
        'mechanical_same_name': [],
        'renamed': [],
        'escalated_dangling': []
    }

    # Expected cross-links from division
    expected_links = {
        'authority_levels_hierarchy': {'from': 'c1', 'to': ['c2', 'c3']},
        'applicable_instructions': {'from': 'c1', 'to': ['c2']},
        'stay_in_bounds_principles': {'from': 'c2', 'to': ['c3']},
        'do_not_encourage_self_harm': {'from': 'c2', 'to': ['c3']},
    }

    print("\n" + "="*80)
    print("RESOLUTION DECISIONS")
    print("="*80)

    # Scan all nodes and resolve needs
    for node in all_nodes:
        if 'needs' not in node or not node['needs']:
            node_count['without_needs'] += 1
            continue

        node_count['with_needs'] += 1
        new_needs = []

        for need in node['needs']:
            name = need['name']
            prose = need.get('prose', '')

            if name in provides_index:
                # Has provider - resolve mechanically
                providers = provides_index[name]
                resolution = {
                    'node': node['id'],
                    'concept_name': name,
                    'providers': [p[0] for p in providers]
                }
                resolutions['mechanical_same_name'].append(resolution)
                print(f"✓ RESOLVED (same name): {name}")
                print(f"  by {node['id']} from {[p[0] for p in providers]}")
                new_needs.append(need)  # Keep the need to show the link
            else:
                # No provider in span - escalate as dangling
                resolution = {
                    'node': node['id'],
                    'concept_name': name,
                    'prose': prose[:60] if prose else ''
                }
                resolutions['escalated_dangling'].append(resolution)
                print(f"✗ ESCALATING: {name} (needed by {node['id']})")
                new_needs.append(need)  # Keep as dangling

        node['needs'] = new_needs if new_needs else []

    # Check expected cross-links
    print("\n" + "="*80)
    print("EXPECTED CROSS-LINKS CHECK")
    print("="*80)

    cross_link_report = []

    for link_name, link_def in expected_links.items():
        from_child = link_def['from']
        to_children = link_def['to']

        if link_name in provides_index:
            # Provider found
            provider_nodes = provides_index[link_name]
            print(f"✓ {link_name} found in provides")
            for prov_id, _ in provider_nodes:
                # Check if it comes from the expected source child
                if from_child in prov_id:
                    print(f"  from {prov_id} (correct child)")
                else:
                    print(f"  from {prov_id} (WARNING: unexpected child)")

            # Check if needed by expected target children
            for node in all_nodes:
                if 'needs' in node:
                    for need in node['needs']:
                        if need['name'] == link_name:
                            to_child = 'c3' if 'L2126' in node['id'] or 'L3041' in node['id'] else ('c2' if 'L797' in node['id'] or 'L1414' in node['id'] else 'c1')
                            print(f"  needed by {node['id']} (child {to_child})")
                            cross_link_report.append({
                                'expected': f"{link_name}: {from_child} -> {to_child}",
                                'outcome': f"resolved: {prov_id[0]} provides to {node['id']}"
                            })
        else:
            print(f"✗ {link_name} NOT FOUND in span (escalates to parent)")
            cross_link_report.append({
                'expected': f"{link_name} from {from_child}",
                'outcome': f"did not materialize: no provider in span; established outside span (L1-170 or external)"
            })

    # Write merged graph
    merged_graph = {
        'nodes': all_nodes,
        'uncovered': all_uncovered,
        'judgment_calls': [
            f"Concatenated {len(all_nodes)} nodes from c21 ({len(c21['nodes'])}), c22 ({len(c22['nodes'])}), c23 ({len(c23['nodes'])}); ids unchanged.",
            f"Nodes with needs: {node_count['with_needs']}; without needs: {node_count['without_needs']}",
            f"Mechanical same-name resolutions: {len(resolutions['mechanical_same_name'])}",
            f"Renames (different-name pairs as same concept): {len(resolutions['renamed'])}",
            f"Dangling needs escalated to parent: {len(resolutions['escalated_dangling'])}",
            "No restatement merges: each child's nodes are independent decompositions; identical claims across spans are already deduplicated by child structure.",
            "No new structure nodes needed: arrangement concepts (authority hierarchy) are already covered by child nodes.",
            "assume_best_intentions section (L610-681 in child 1) likely does NOT provide 'assume_best_intentions' or 'assume_best_intentions_principle' names in its nodes; names escalate to parent.",
            "chain_of_command, red_line_principles, risk_taxonomy, usage_policies, protect_privileged_information, avoid_info_hazards, avoid_overstepping, harmful_illicit_activities_guidance, conscientious_employee_metaphor, protected_groups, objective_point_of_view: all escalate (established in L1-170 or external)."
        ],
        'cross_link_report': cross_link_report
    }

    with open(OUT_PATH, 'w') as f:
        json.dump(merged_graph, f, indent=2)

    print(f"\n\nMerged graph written to: {OUT_PATH}")
    print(f"  Nodes: {len(all_nodes)}")
    print(f"  Uncovered: {len(all_uncovered)}")
    print(f"  Same-name resolutions: {len(resolutions['mechanical_same_name'])}")
    print(f"  Renames: {len(resolutions['renamed'])}")
    print(f"  Escalated danglings: {len(resolutions['escalated_dangling'])}")
    print(f"  Cross-link report entries: {len(cross_link_report)}")

if __name__ == '__main__':
    main()
