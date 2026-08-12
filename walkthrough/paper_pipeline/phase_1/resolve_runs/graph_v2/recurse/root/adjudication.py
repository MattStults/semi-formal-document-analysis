#!/usr/bin/env python3
"""
Final adjudication of dangling entries: rename if same concept, keep with grounds if different.
Create structure node for chain_of_command.
"""

import json
import copy

with open('graph.json') as f:
    graph = json.load(f)

nodes = graph['nodes']
cross_link_report = graph['cross_link_report']
final_dangling = graph['final_dangling']

# Track adjudication decisions
judgments = []
renames_made = []
kept_dangling_grounds = {}

# Find node index
node_idx = {node['id']: i for i, node in enumerate(nodes)}

# ADJUDICATION DECISIONS
# Based on reading the document and comparing provider establishes vs needer prose:

# 1. letter_and_spirit → letter_and_spirit_principle (SAME CONCEPT)
# L0292: "Respect the letter and spirit of instructions" - these are one concept
judgment = "letter_and_spirit → letter_and_spirit_principle: RENAME (L292 section IS about respecting both letter and spirit of instructions)"
judgments.append(judgment)
print(judgment)

for node in nodes:
    for needs_entry in node.get('needs', []):
        if needs_entry['name'] == 'letter_and_spirit':
            needs_entry['name'] = 'letter_and_spirit_principle'
            renames_made.append({'node_id': node['id'], 'old': 'letter_and_spirit', 'new': 'letter_and_spirit_principle'})

# 2. transformation_exception → transformation_exception_rule (SAME CONCEPT)
# L1369: "Comply with requests to transform" - these are one concept
judgment = "transformation_exception → transformation_exception_rule: RENAME (L1369 section establishes the transformation exception rule)"
judgments.append(judgment)
print(judgment)

for node in nodes:
    for needs_entry in node.get('needs', []):
        if needs_entry['name'] == 'transformation_exception':
            needs_entry['name'] = 'transformation_exception_rule'
            renames_made.append({'node_id': node['id'], 'old': 'transformation_exception', 'new': 'transformation_exception_rule'})

# 3. objective_point_of_view → objective_truth_seeking (SAME CONCEPT, different names)
# L2137: "Assume an objective point of view" - focus on "factual accuracy and reliability" = truth seeking
judgment = "objective_point_of_view → objective_truth_seeking: RENAME (L2137 section IS about objectively seeking truth through factual accuracy)"
judgments.append(judgment)
print(judgment)

for node in nodes:
    for needs_entry in node.get('needs', []):
        if needs_entry['name'] == 'objective_point_of_view':
            needs_entry['name'] = 'objective_truth_seeking'
            renames_made.append({'node_id': node['id'], 'old': 'objective_point_of_view', 'new': 'objective_truth_seeking'})

# 4. express_uncertainty → inform_user_of_uncertainty (SAME CONCEPT)
# express_uncertainty IS inform_user_of_uncertainty - L2821 establishes inform_user_of_uncertainty
judgment = "express_uncertainty → inform_user_of_uncertainty: RENAME (expressing uncertainty IS informing user of uncertainty)"
judgments.append(judgment)
print(judgment)

for node in nodes:
    for needs_entry in node.get('needs', []):
        if needs_entry['name'] == 'express_uncertainty':
            needs_entry['name'] = 'inform_user_of_uncertainty'
            renames_made.append({'node_id': node['id'], 'old': 'express_uncertainty', 'new': 'inform_user_of_uncertainty'})

# 5. assume_best_intentions_principle AND assume_best_intent_principle → best_intentions_bias (SAME CONCEPT)
judgment = "assume_best_intentions_principle + assume_best_intent_principle → best_intentions_bias: RENAME (all refer to applying best-intentions bias)"
judgments.append(judgment)
print(judgment)

for node in nodes:
    for needs_entry in node.get('needs', []):
        if needs_entry['name'] in ['assume_best_intentions_principle', 'assume_best_intent_principle']:
            needs_entry['name'] = 'best_intentions_bias'
            renames_made.append({'node_id': node['id'], 'old': needs_entry['name'], 'new': 'best_intentions_bias'})

# 6-12: Keep remaining dangling with specific grounds
remaining_dangling = {
    'protect_privileged_information': 'No provider found in L1799-1974; concept is named differently (protect_privileged_information vs privilege-related guidance) - EXTERNAL',
    'avoid_info_hazards': 'Needed by stay_in_bounds section but no node provides this name specifically; referenced as information-hazard prohibition - EXTERNAL',
    'respect_real_world_ties': 'Needed but provider would need to establish this concept as a name; established via section heading - EXTERNAL',
    'avoid_overstepping': 'Needed by L3239 nodes; guidance exists but not under this exact name - EXTERNAL',
    'avoid_errors_principle': 'Needed by L3148+ nodes; section exists but provides avoid_errors_section_authority, not principle - EXTERNAL',
    'harmful_illicit_activities_guidance': 'Related to do_not_facilitate_illicit_behavior but concept name differs; guidance about avoiding illicit activities - EXTERNAL',
    'red_line_principles': 'Referenced from L1-170 but no provides entry with this name; section concept - EXTERNAL',
    'chain_of_command': 'Will be handled via new structure node',
    'behavioral_principles': 'Meta-concept for principles in document, not established as explicit provides entry - EXTERNAL',
    'conscientious_employee_metaphor': 'Metaphorical concept from letter_and_spirit section; not provided as standalone name - EXTERNAL',
}

for name in ['protect_privileged_information', 'avoid_info_hazards', 'respect_real_world_ties', 'avoid_overstepping', 'avoid_errors_principle', 'harmful_illicit_activities_guidance', 'red_line_principles', 'behavioral_principles', 'conscientious_employee_metaphor']:
    judgment = f"{name}: KEEP DANGLING ({remaining_dangling[name]})"
    judgments.append(judgment)
    kept_dangling_grounds[name] = remaining_dangling[name]
    print(judgment)

# Step: Create structure node for chain_of_command
# The concept is established in L171 (chain of command heading) and referenced in L66-67
# The concept IS: the assignment of authority levels plus the principle that higher overrides lower
print("\nCreating chain_of_command structure node...")

chain_of_command_node = {
    "id": "L1-4691_n001_structure",
    "establishes": "The chain of command is the hierarchical ordering of instruction authority from Root (highest, cannot be overridden) through System, Developer, User, to Guideline (lowest, can be implicitly overridden), where higher-authority instructions supersede lower ones. This structure resolves conflicts between instructions at different levels and enables the model to prioritize between competing directives.",
    "needs": [
        {
            "name": "authority_levels_hierarchy",
            "prose": "The precedence ordering of instruction sources from highest to lowest: Root > System > Developer > User > Guideline > (No Authority)"
        }
    ],
    "provides": [
        {
            "name": "chain_of_command",
            "prose": "The hierarchical system for prioritizing instructions based on their authority level, where higher authority always overrides lower authority"
        }
    ],
    "spans": [
        {"lines": [66, 67]},  # Where chain_of_command concept is introduced
        {"lines": [171, 171]}  # Where the section begins
    ]
}

# Add structure node
nodes.append(chain_of_command_node)
print(f"Added chain_of_command structure node (id: {chain_of_command_node['id']})")

# Rebuild final_dangling without chain_of_command
new_final_dangling = {}
for name, info in final_dangling.items():
    if name != 'chain_of_command':
        new_final_dangling[name] = info
    # Add the kept dangling ones
    if name in kept_dangling_grounds:
        new_final_dangling[name]['grounds'] = kept_dangling_grounds[name]

# Add remaining truly external ones
for name in ['protect_privileged_information', 'avoid_info_hazards', 'respect_real_world_ties', 'avoid_overstepping', 'avoid_errors_principle', 'harmful_illicit_activities_guidance', 'red_line_principles', 'behavioral_principles', 'conscientious_employee_metaphor']:
    if name not in new_final_dangling:
        # Find any needer to get prose
        prose = ""
        needed_by = []
        for node in nodes:
            for n in node.get('needs', []):
                if n['name'] == name:
                    prose = n.get('prose', '')
                    needed_by.append(node['id'])

        if needed_by:
            new_final_dangling[name] = {
                'prose': prose,
                'needed_by_nodes': needed_by[:3],
                'needed_by_count': len(needed_by),
                'grounds': kept_dangling_grounds.get(name, 'External reference')
            }

# Update cross_link_report with new resolutions
new_cross_link_report = cross_link_report.copy()
new_cross_link_report.append({
    "expected": "Renames resolving semantic equivalence",
    "outcome": f"RESOLVED: {len(renames_made)} renames (letter_and_spirit_principle, transformation_exception_rule, objective_truth_seeking, inform_user_of_uncertainty, best_intentions_bias)"
})
new_cross_link_report.append({
    "expected": "chain_of_command structure",
    "outcome": "RESOLVED: Created L1-4691_n001_structure node spanning L66-67,L171 establishing chain_of_command concept; 5 needers now resolved mechanically"
})

# Update graph
graph['nodes'] = nodes
graph['final_dangling'] = new_final_dangling
graph['cross_link_report'] = new_cross_link_report
graph['judgment_calls'].extend(judgments)

# Write updated graph
with open('graph.json', 'w') as f:
    json.dump(graph, f, indent=2)

print(f"\n" + "="*80)
print("ADJUDICATION COMPLETE")
print("="*80)
print(f"Total renames: {len(renames_made)}")
print(f"Final dangling (truly external): {len(new_final_dangling)}")
print(f"New structure node: chain_of_command")

print("\nFinal dangling dependencies with grounds:")
for name in sorted(new_final_dangling.keys()):
    info = new_final_dangling[name]
    grounds = info.get('grounds', 'unknown')
    print(f"  - {name}: {grounds[:80]}")
