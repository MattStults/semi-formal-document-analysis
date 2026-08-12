# The document graph, in two pictures

## 1. How it was built — the recursion tree

Each box is one Haiku transcript. Dividers chose their own cut points, seeded shared
vocabulary downward, and later linked their children's graphs; leaves produced the nodes.
Numbers are final node counts after each unwind.

```mermaid
flowchart TD
    ROOT["root L1-4691<br/>593 nodes · 13 final danglings"]
    C1["c1 leaf L1-170<br/>46 nodes<br/>overview+definitions"]
    C2["c2 L171-3147<br/>354 nodes"]
    C3["c3 L3148-4691<br/>193 nodes"]
    ROOT --> C1
    ROOT --> C2
    ROOT --> C3
    C21["c21 L171-796<br/>81 · chain of command"]
    C22["c22 L797-2125<br/>165 · stay in bounds"]
    C23["c23 L2126-3147<br/>108 · seek the truth"]
    C2 --> C21
    C2 --> C22
    C2 --> C23
    C211["c211 leaf L171-291<br/>19 · THE K1 LEAF"]
    C212["c212 L292-526<br/>30"]
    C213["c213 leaf L527-796<br/>32"]
    C21 --> C211
    C21 --> C212
    C21 --> C213
    C22A["c22a L797-1413<br/>78 · content rules"]
    C22B["c22b L1414-2125<br/>87 · risky situations"]
    C22 --> C22A
    C22 --> C22B
    C31["c31 L3148-3501<br/>42 · do best work"]
    C32["c32 L3502-4571<br/>131 · style+voice"]
    C33["c33 leaf L4572-4691<br/>20 · UNDER-18"]
    C3 --> C31
    C3 --> C32
    C3 --> C33
    style ROOT fill:#e8f0fe,stroke:#4285f4,color:#111
    style C211 fill:#e6f4ea,stroke:#34a853,color:#111
    style C33 fill:#fce8e6,stroke:#ea4335,color:#111
```

(c212, c22a, c22b, c23, c31, c32 each have 2-3 further leaf children, omitted for
legibility — the full tree is 18 dividers + 16 leaves, in `recurse/`.)

## 2. What it contains — the motivating region of the concept graph

Boxes are graph NODES (with their document grounding); arrows read "needs".
This is the sub-graph the whole design existed to produce.

```mermaid
flowchart LR
    subgraph ordering["THE RESTATEMENT MERGE (root unwind)"]
        AUTH["authority_levels_hierarchy<br/>ONE node, spans L69-101 + L183 + L186-191<br/>(prose statement AND numbered list)<br/>32 consumers"]
    end
    COC["chain_of_command<br/>root-added structure node<br/>spans L66-67 + L171"]
    FOLLOW["follow all applicable<br/>instructions rule (L181)"]
    MISALIGN["misaligned-instruction<br/>definition (L197)"]
    LIE["do-not-lie authority<br/>clarifications (L2481+)"]
    COC -->|needs| AUTH
    FOLLOW -->|needs| AUTH
    MISALIGN -->|needs| AUTH
    LIE -->|needs| AUTH
    subgraph u18["UNDER-18 DELTAS (L4572-4691) — resolved across ~3000 lines"]
        U18R["romantic-roleplay delta L4590"]
        U18S["self-harm delta L4589"]
        U18D["dangerous-activities delta L4592"]
    end
    SIB["stay_in_bounds_principles<br/>L797-809"]
    DNESH["do_not_encourage_self_harm<br/>L1611-1690<br/>(alias-resolved from<br/>self_harm_prohibition)"]
    DNFIB["do_not_facilitate_illicit_behavior<br/>L1543-1548"]
    U18R -->|needs| SIB
    U18S -->|needs| DNESH
    U18D -->|needs| DNFIB
    EXT["usage_policies<br/>FINAL DANGLING —<br/>external URL, correctly unresolved"]
    style AUTH fill:#e6f4ea,stroke:#34a853,color:#111
    style EXT fill:#fce8e6,stroke:#ea4335,color:#111
    style COC fill:#fef7e0,stroke:#f9ab00,color:#111
```

## 3. An example leaf node (what translation will consume)

The best-connected node in the graph — note it does NOT contain ASP; it is the
translation *input*: prose to check, names to join on, lines to verify against.

```json
{
  "id": "L1-170_n028",
  "establishes": "The authority hierarchy ranked from highest to lowest: Root > System > Developer > User > Guideline. Instructions at higher levels override those at lower levels in case of conflict.",
  "needs": [],
  "provides": [
    { "name": "authority_levels_hierarchy",
      "prose": "The precedence ordering of instruction sources from highest to lowest: Root > System > Developer > User > Guideline. Established in L0069-L0191, particularly the ordered list at L0186-L0191." }
  ],
  "spans": [ {"lines": [69, 101]}, {"lines": [183, 183]}, {"lines": [186, 191]} ]
}
```

And a typical delta node (Under-18, showing a long-range edge):

```json
{
  "id": "L4572-4691_n011",
  "establishes": "For U18 users, the assistant cannot engage in immersive romantic roleplay, first-person intimacy, or romantic pairing with the teen, even if a similar scene would be allowed between consenting adults. This extends the rule that prohibits role-play undermining real-world ties.",
  "needs": [
    { "name": "stay_in_bounds_principles", "prose": "The collection of limits on assistant behavior ... Section introduced at L0797-L0799." },
    { "name": "respect_real_world_ties", "prose": "Prohibition on role-play that could undermine real-world ties and relationships" }
  ],
  "provides": [],
  "spans": [ {"lines": [4590, 4590], "quote": "**Romantic or erotic roleplay:** ..."} ]
}
```

Top consumed concepts (edge counts): authority_levels_hierarchy 32,
objective_truth_seeking 19, scope_of_autonomy 13, disallowed_content_categories 12,
prevent_imminent_real_world_harm 11, stay_in_bounds_principles 10,
do_not_facilitate_illicit_behavior 10, interactive_vs_programmatic_context 10.
