#!/usr/bin/env python3
"""
Fix Phase U graph.json:
1. Rename assume_best_intentions need to best_intentions_bias in L797-809_n001
2. Fix non-verbatim quote in L171-291_n014
3. Add rename to cross_link_report
4. Update judgment_calls
"""

import json

GRAPH_PATH = "/private/tmp/claude-501/-Users-mattstults-Documents-ai-safety-projects-semi-formal-document-analysis/ad93b6a7-c890-4a7e-bb0a-d340c85c8451/scratchpad/recurse/c2/graph.json"

def main():
    # Load graph
    with open(GRAPH_PATH, 'r') as f:
        graph = json.load(f)

    # Task 1: Rename assume_best_intentions to best_intentions_bias in L797-809_n001
    print("=" * 80)
    print("TASK 1: Rename need in L797-809_n001")
    print("=" * 80)

    found_node = False
    for node in graph['nodes']:
        if node['id'] == 'L797-809_n001':
            found_node = True
            print(f"Found node: {node['id']}")
            print(f"  Current needs: {node.get('needs', [])}")

            # Find and rename the need
            if 'needs' in node:
                for need in node['needs']:
                    if need['name'] == 'assume_best_intentions':
                        old_name = need['name']
                        new_name = 'best_intentions_bias'
                        need['name'] = new_name
                        print(f"  RENAMED: {old_name} -> {new_name}")
                        print(f"  (kept prose: {need.get('prose', '')[:60]}...)")

                        # Record in cross_link_report
                        rename_entry = {
                            'expected': 'assume_best_intentions (renamed to best_intentions_bias)',
                            'outcome': 'resolved via rename: L797-809_n001 needs best_intentions_bias (same concept, both in Assume-best-intentions section L610-697) provided by L527-796_n011'
                        }
                        graph['cross_link_report'].append(rename_entry)
                        print(f"  Added to cross_link_report")
                        break

    if not found_node:
        print("ERROR: L797-809_n001 not found!")
        return False

    # Task 2: Fix quote in L171-291_n014
    print("\n" + "=" * 80)
    print("TASK 2: Fix non-verbatim quote in L171-291_n014")
    print("=" * 80)

    found_node = False
    for node in graph['nodes']:
        if node['id'] == 'L171-291_n014':
            found_node = True
            print(f"Found node: {node['id']}")

            if 'spans' in node:
                for span in node['spans']:
                    if span.get('lines') == [203, 203]:
                        old_quote = span.get('quote', '')
                        print(f"  Old quote: {old_quote}")

                        # Replace with verbatim text from L203
                        new_quote = "The assistant should not allow lower-level content (including its own previous messages) to influence its interpretation of higher-level principles"
                        span['quote'] = new_quote
                        print(f"  New quote: {new_quote[:80]}...")
                        print(f"  FIXED: quote now verbatim from L203")
                        break

    if not found_node:
        print("ERROR: L171-291_n014 not found!")
        return False

    # Task 3: Add to judgment_calls
    print("\n" + "=" * 80)
    print("TASK 3: Update judgment_calls")
    print("=" * 80)

    judgment = "Resolved assume_best_intentions escalation via rename to best_intentions_bias: both refer to same concept (three implicit biases for interpreting ambiguous instructions) from L610-697 'Assume best intentions' section; L799 cross-references this section for 'relevant details about handling ambiguous requests'; child 1 node L527-796_n011 provides the concrete bias framework, child 2 node L797-809_n001 needs the principle. Fixed non-verbatim quote in L171-291_n014 to verbatim L203 text."

    graph['judgment_calls'].append(judgment)
    print(f"Added judgment_call: {judgment[:100]}...")

    # Write back
    print("\n" + "=" * 80)
    print("Writing updated graph.json...")
    print("=" * 80)

    with open(GRAPH_PATH, 'w') as f:
        json.dump(graph, f, indent=2)

    print(f"✓ Graph updated: {GRAPH_PATH}")
    print(f"\nSummary:")
    print(f"  - Renamed L797-809_n001 need: assume_best_intentions -> best_intentions_bias")
    print(f"  - Fixed L171-291_n014 quote to verbatim L203 text")
    print(f"  - Added cross_link_report entry for rename")
    print(f"  - Added judgment_call explaining resolution")

if __name__ == '__main__':
    main()
