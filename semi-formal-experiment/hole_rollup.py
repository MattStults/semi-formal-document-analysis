"""Roll the two induced taxonomies up against the GRAMMAR FEATURES.

DIAGNOSTIC ONLY.

⚠️ THE GROUPING BELOW IS MINE, NOT THE CODERS'. They induced categories
bottom-up and blind to the grammar; mapping those categories onto grammar
features is a second, editorial step and it reintroduces exactly the prior the
blind coding was designed to exclude. It is kept in one visible table, applied
to BOTH coders' partitions, so a reader can reject the mapping and keep the
counts. Any number in `LOSS BY FEATURE` is downstream of a judgement call;
the per-category counts are not.

⚠️ COUNTS OVERSTATE DISTINCT HOLES. Both coders independently reported that
the read-back judge splits a coordinated list into one record per conjunct, so
a single shattered enumeration is counted several times. Treat these as shares
of LOSS MASS, not as a census of ideas.
"""
from __future__ import annotations

import collections
import json
import pathlib

HERE = pathlib.Path(__file__).parent

#: feature -> the categories, per coder, I judge it would carry.
GROUPS = {
    "ALREADY BUYING: deontic force (polarity prefix)": {
        "a": ("required_action", "prohibition", "permission_latitude"),
        "b": ("conjoined_directive", "prohibition_or_avoidance",
              "permission_or_exception"),
    },
    "ALREADY BUYING: condition/exception (role field)": {
        "a": ("applicability_condition", "exception_carveout"),
        "b": ("applicability_condition",),
    },
    "ALREADY BUYING: party (principal chain)": {
        "a": ("third_party_norm",),
        "b": ("non_assistant_addressee",),
    },
    "CANDIDATE: relation between atoms": {
        "a": ("authority_precedence", "preference_ordering",
              "procedural_sequence"),
        "b": ("precedence_or_preference_ordering",
              "temporal_or_procedural_order"),
    },
    "CANDIDATE: enumeration / scope": {
        "a": ("enumerated_list_member", "coverage_scope_extension"),
        "b": ("scope_delimitation", "illustrative_instance"),
    },
    "CANDIDATE: manner / degree": {
        "a": ("manner_quality_qualifier",),
        "b": ("manner_or_quality_qualifier",),
    },
    "CANDIDATE: rationale / purpose": {
        "a": ("rationale_purpose",),
        "b": ("rationale_or_purpose",),
    },
    "CANDIDATE: default / defeasible presumption": {
        "a": ("default_presumption", "context_dependent_variation",
              "tradeoff_balancing"),
        "b": ("unresolved_tradeoff",),
    },
    "ARGUABLY OUT OF SCOPE: not a directive at all": {
        "a": ("example_case_adjudication", "descriptive_system_fact",
              "document_meta", "term_definition", "character_disposition"),
        "b": ("worked_example_particular", "descriptive_premise",
              "document_metatext", "definition_or_constitution"),
    },
}


def main():
    parts = {}
    for c in ("a", "b"):
        t = json.loads((HERE / f"hole_taxonomy_coder_{c}.json").read_text())
        parts[c] = collections.Counter(
            v.get("primary") for v in (t["assignments"] or {}).values())

    tot = {c: sum(parts[c].values()) for c in parts}
    print(f"records: A {tot['a']}, B {tot['b']}\n")
    print(f"{'':52s} {'A':>12s} {'B':>12s}")
    seen = {c: set() for c in parts}
    for label, spec in GROUPS.items():
        cells = []
        for c in ("a", "b"):
            n = sum(parts[c][k] for k in spec[c])
            seen[c] |= set(spec[c])
            cells.append(f"{n:4d} {100*n/tot[c]:5.1f}%")
        print(f"{label:52s} {cells[0]:>12s} {cells[1]:>12s}")
    print()
    for c in ("a", "b"):
        left = sorted(set(parts[c]) - seen[c])
        if left:
            print(f"coder {c} ungrouped: {[(k, parts[c][k]) for k in left]}")


if __name__ == "__main__":
    main()
