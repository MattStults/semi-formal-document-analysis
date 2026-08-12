#!/usr/bin/env python3
"""
Final adjudication fix: properly clean up renamed entries and finalize dangling.
"""

import json

with open('graph.json') as f:
    graph = json.load(f)

# The renamed entries that should be removed from final_dangling
renamed_removed = [
    'letter_and_spirit',
    'transformation_exception',
    'objective_point_of_view',
    'express_uncertainty',
    'assume_best_intentions_principle',
    'assume_best_intent_principle'
]

# The ones to keep as truly external
truly_external = {
    'protect_privileged_information': 'Concept is named differently in providers; section concept not explicitly provided - EXTERNAL REFERENCE',
    'avoid_info_hazards': 'Section concept; no node provides this name - EXTERNAL REFERENCE',
    'respect_real_world_ties': 'Section concept; established via section heading not provides entry - EXTERNAL REFERENCE',
    'avoid_overstepping': 'Section concept; no node provides this name - EXTERNAL REFERENCE',
    'avoid_errors_principle': 'Principle concept; section provides avoid_errors_section_authority, not principle - EXTERNAL REFERENCE',
    'harmful_illicit_activities_guidance': 'Related concept; differs from do_not_facilitate_illicit_behavior - EXTERNAL REFERENCE',
    'red_line_principles': 'Section concept; no node provides this name - EXTERNAL REFERENCE',
    'behavioral_principles': 'Meta-concept spanning multiple sections - EXTERNAL REFERENCE',
    'conscientious_employee_metaphor': 'Metaphorical concept from letter_and_spirit section - EXTERNAL REFERENCE',
    'privacy_instruction_priority': 'Concept from privacy section; no node provides this name - EXTERNAL REFERENCE',
    'protected_groups': 'Taxonomy concept; no node provides this name - EXTERNAL REFERENCE',
    'safety_instruction_priority': 'Priority concept; no node provides this name - EXTERNAL REFERENCE',
    'usage_policies': 'EXTERNAL: openai.com/policies/usage-policies (outside Model Spec document)',
}

# Rebuild final_dangling with only truly external entries
new_final_dangling = {}
for name in sorted(truly_external.keys()):
    info = graph['final_dangling'].get(name, {})
    new_final_dangling[name] = {
        'prose': info.get('prose', ''),
        'needed_by_count': info.get('needed_by_count', 0),
        'grounds': truly_external[name]
    }

# Update graph
graph['final_dangling'] = new_final_dangling

# Write updated graph
with open('graph.json', 'w') as f:
    json.dump(graph, f, indent=2)

print("Adjudication finalized")
print(f"Removed from dangling (renamed): {len(renamed_removed)}")
print(f"Final dangling (truly external): {len(new_final_dangling)}")
print("\nFinal dangling list:")
for name in sorted(new_final_dangling.keys()):
    grounds = new_final_dangling[name]['grounds']
    count = new_final_dangling[name]['needed_by_count']
    print(f"  - {name} ({count} needers): {grounds}")
