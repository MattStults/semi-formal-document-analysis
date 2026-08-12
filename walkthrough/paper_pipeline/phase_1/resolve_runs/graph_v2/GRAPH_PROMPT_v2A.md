# Build a graph of what this document establishes

You are given a specification document twice: the **raw file** (ground truth) and a copy with
every line numbered `L0186  ...` (for addressing only — the numbers are not part of the text).

Break the document into a **graph of nodes**. A node is a piece of the document that
establishes ONE thing.

## What the nodes are FOR — this decides their size

Each node will be handed, alone, to a translator that turns it into a small logic module
(a handful of formal rules), and that module is then checked sentence-by-sentence against the
text the node cites. So a node must be exactly one checkable claim:

- **one rule** (an obligation, prohibition, or permission that a situation can satisfy or violate),
- **one definition** (what a term means),
- **one ordering or grouping** (a ranking, a hierarchy, a set of categories),
- **one scope statement** (when a set of rules does or does not apply), or
- **one plain fact**.

**The split test:** if the `establishes` prose joins two claims that could be independently
true or false of a situation — "be honest and don't have an agenda" — that is two nodes.

**The merge test:** a list or table that assigns the same attribute across several items
("the vault requires Curator; the reading room requires Visitor") is ONE node — one mapping —
not one node per row. Split a row out only when some other node relies on that row by itself.

A node is never a summary. "This section covers how conflicts are resolved" is not an
`establishes`. If you cannot restate your `establishes` as a single claim a checker could
verify against a situation, split it.

## Node format

```json
{ "id": "n017",
  "establishes": "prose: the one thing this part of the document settles, stated fully enough to check against the text",
  "needs":    [ {"name": "clearance_order", "prose": "which of two clearance levels is the higher one"} ],
  "provides": [ {"name": "clearance_order", "prose": "which of two clearance levels is the higher one"} ],
  "spans":    [ {"lines": [183, 191]},
                {"lines": [45, 45], "quote": "never leave the vault unlocked"} ] }
```

- `needs` — what this node relies on but does not itself settle.
- `provides` — what this node settles that other parts of the document rely on. If nothing
  else relies on it, `provides` is empty; the node still exists.
- `spans` — where in the document this node lives. A span is a line range in the RAW file.
  Add `quote` (verbatim text from within those lines) only to narrow a span to part of a line.
  Every line number must exist; every quote must appear verbatim on the cited lines. Both are
  checked mechanically.

## Names: you are the naming authority

Because you see the whole document at once, you ASSIGN each concept its canonical name —
lower_snake_case — and reuse that exact string everywhere the concept appears, in `needs` and
`provides` alike. Later stages link modules by these names, so:

- one concept, one name, spelled identically at every use;
- the `prose` is the authoritative meaning — write it so it can be checked against the
  document; the name is just the handle;
- a `needs` entry whose name matches no `provides` anywhere is a real and useful answer when
  the document genuinely never settles it. Keep it, with honest prose. Never invent a node to
  cover something the document does not establish.

## Structure rules

1. **Spans may overlap, nest, and skip.** A node may cover lines another node also covers; a
   node may sit entirely inside another; a node may be several disjoint spans when the
   document establishes one thing in two places. Section headings do not constrain nodes.
2. **Formatting can be the content.** If a list is printed in priority order, the ordering is
   established by the ARRANGEMENT — no single item states it. That ordering is its own node
   spanning the whole list. Items may additionally be their own nodes, nested inside, when
   something relies on them individually.
3. **Coverage:** every sentence that asserts, defines, orders, groups, or scopes something
   must be inside some node's spans. Text that only motivates, illustrates, or gives worked
   examples (e.g. sample conversations) may be left out — list what you deliberately left out,
   as line ranges with a short reason, in `uncovered`.
4. **Do not multiply nodes beyond what the text asserts.** One assertion, one node. When in
   doubt between two mergeable nodes and one, prefer one — unless the split test above forces
   two.

## Worked example — a toy document and its full graph

The document (numbered copy shown; the raw file is the same without the `L` column):

```
L01  # Greenfield Archive — Access Rules
L02
L03  Staff must log every retrieval, and must never leave the vault unlocked.
L04
L05  ## Clearance
L06
L07  The following clearance levels are listed from highest to lowest.
L08  A room may be entered only by holders of a clearance at or above the room's required level.
L09
L10  1. **Curator**
L11  2. **Fellow**
L12  3. **Visitor**
L13
L14  The vault requires Curator clearance. The reading room requires Visitor clearance.
L15
L16  Where two rules conflict, the rule tied to the higher clearance level prevails.
L17
L18  The archive was founded in 1911.
```

Its graph:

```json
{ "nodes": [
  { "id": "n001",
    "establishes": "Staff must log every retrieval.",
    "needs": [], "provides": [],
    "spans": [ {"lines": [3, 3], "quote": "Staff must log every retrieval"} ] },

  { "id": "n002",
    "establishes": "Staff must never leave the vault unlocked.",
    "needs": [], "provides": [],
    "spans": [ {"lines": [3, 3], "quote": "must never leave the vault unlocked"} ] },

  { "id": "n003",
    "establishes": "There are three clearance levels — Curator, Fellow, Visitor — ranked Curator highest, then Fellow, then Visitor. The ranking is carried by the printed order of the list, highest first.",
    "needs": [],
    "provides": [ {"name": "clearance_order", "prose": "which of two clearance levels is the higher one"},
                  {"name": "clearance_levels", "prose": "the set of recognized clearance levels"} ],
    "spans": [ {"lines": [7, 7]}, {"lines": [10, 12]} ] },

  { "id": "n004",
    "establishes": "Curator is a clearance level (the highest).",
    "needs": [],
    "provides": [ {"name": "curator_level", "prose": "the Curator clearance level"} ],
    "spans": [ {"lines": [10, 10]} ] },

  { "id": "n005",
    "establishes": "Visitor is a clearance level (the lowest).",
    "needs": [],
    "provides": [ {"name": "visitor_level", "prose": "the Visitor clearance level"} ],
    "spans": [ {"lines": [12, 12]} ] },

  { "id": "n006",
    "establishes": "A room may be entered only by holders of a clearance at or above the room's required level.",
    "needs": [ {"name": "clearance_order", "prose": "which of two clearance levels is the higher one"},
               {"name": "room_required_level", "prose": "the clearance level each room requires"} ],
    "provides": [],
    "spans": [ {"lines": [8, 8]} ] },

  { "id": "n007",
    "establishes": "Each room's required clearance: the vault requires Curator; the reading room requires Visitor.",
    "needs": [ {"name": "curator_level", "prose": "the Curator clearance level"},
               {"name": "visitor_level", "prose": "the Visitor clearance level"} ],
    "provides": [ {"name": "room_required_level", "prose": "the clearance level each room requires"} ],
    "spans": [ {"lines": [14, 14]} ] },

  { "id": "n008",
    "establishes": "When two rules conflict, the rule tied to the higher clearance level prevails.",
    "needs": [ {"name": "clearance_order", "prose": "which of two clearance levels is the higher one"},
               {"name": "rule_clearance_tie", "prose": "which clearance level a given rule is tied to — the document never says how rules acquire a clearance level"} ],
    "provides": [],
    "spans": [ {"lines": [16, 16]} ] },

  { "id": "n009",
    "establishes": "The archive was founded in 1911.",
    "needs": [], "provides": [],
    "spans": [ {"lines": [18, 18]} ] }
],
"uncovered": [ {"lines": [1, 1], "reason": "title"},
               {"lines": [5, 5], "reason": "heading"} ] }
```

Why this graph is right — each point is a rule from above in action:

- **L03 is one line, two nodes** (n001, n002): two obligations a situation can violate
  independently. Their spans overlap on the line; the quotes separate them.
- **The ordering is its own node** (n003) spanning the list AND the sentence announcing the
  order — a multi-span node. No single list item states the ranking; the arrangement does.
- **n004 and n005 nest inside n003's span.** They exist because n007 relies on Curator and
  Visitor individually. There is no Fellow node: nothing relies on Fellow by itself, so it
  lives only inside the ordering. This is rule 4 and the merge test working together.
- **n007 is ONE node for a two-row mapping** — the merge test. It does not split because
  nothing relies on "the vault requires Curator" separately from the mapping.
- **n008 carries a dangling need** (`rule_clearance_tie`): the document never settles how a
  rule gets a clearance level. The need is kept, honestly described, and no node is invented.
- **n009 is isolated** — no needs, no provides. Plain facts are allowed to be alone.
- **`clearance_order` is one name, spelled identically at all four uses** across n003, n006,
  n008 — that is the naming-authority rule.

## What you return

```json
{ "nodes": [...], "uncovered": [...] }
```
