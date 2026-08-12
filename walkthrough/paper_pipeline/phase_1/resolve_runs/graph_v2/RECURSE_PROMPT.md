# Recursive document decomposition — shared brief for every agent in the tree

You are one agent in a recursion tree that turns a specification document into a GRAPH of
nodes. Each node of the graph is a piece of the document that establishes ONE thing, and
will be translated into a small logic module checked sentence-by-sentence against the text
it cites. You are assigned a SPAN of the document. Your dispatch message tells you your
span, your phase, and your working directory.

The document (read it only through the line-numbered copy; line numbers are for addressing):
`model_spec_numbered.txt` — the path is in your dispatch message.

Every agent runs the same three-phase life. You will be invoked for phase D first; if you
divide, you will be re-invoked later (same transcript) for phase U.

---

## Phase D — DIVIDE or declare LEAF

Read your entire span. Then decide:

- **LEAF** if your span is small enough to decompose directly into atomic nodes (roughly:
  you can hold every claim in it in mind at once; typically ≤ ~150 lines). Then do Phase L
  now.
- **DIVIDE** otherwise: choose **2 or 3 child sub-spans** (contiguous, non-overlapping,
  covering your whole span). Mechanically: the first child starts at your span's first
  line, the last child ends at your span's last line, and each child starts exactly one
  line after the previous child ends — blank lines belong to a child too. Cut AT a blank
  line by giving it to the earlier child.

**The one rule that makes division safe:** you may only place a cut where, having read the
text on both sides, you are confident of one of:
  (a) **no linkage crosses this cut** — nothing on one side relies on or restates something
      on the other; or
  (b) **you understand every linkage that crosses it well enough to link it yourself
      later** — and you write each one down NOW as an `expected_cross_link`.
If neither holds anywhere in a region, do not cut there; choose different boundaries (child
sizes may be uneven — a clean cut beats an even split).

**Seed vocabulary — you are the naming authority for concepts that cross your cuts.** For
every concept involved in an `expected_cross_link` (and any concept you can see is
established in one child and used in another), ASSIGN a canonical name now:
`{"name": "lower_snake_case", "prose": "what it means, checkable against the document"}`.
Your children must use these exact names; do not rename what your own dispatch already
seeded. **Your seed_vocabulary must CONTAIN every inherited seed whose concept appears
anywhere in your span, copied unchanged** — your children read only YOUR division.json,
so an inherited seed you drop is a name your whole subtree loses. When in doubt, carry it;
dropping is only correct when the concept is entirely absent from your span. **A seed's `established_around` is its
provenance: a concept established outside your span can only be NEEDED by your subtree
(a dangling need for your parent), never provided by it — and never predicted as a
cross-link provided by one of your children.**

**Phase D output** — write to `<workdir>/division.json`:

```json
{ "decision": "divide",
  "children": [
    { "span": [1, 170],  "why_this_cut": "front matter and definitions; the only crossing linkage is the authority-levels concept, seeded below" },
    { "span": [171, 800], "why_this_cut": "..." }
  ],
  "seed_vocabulary": [
    { "name": "authority_level_ordering", "prose": "which of two authority levels outranks the other", "established_around": [69, 101] },
    { "name": "house_rules_location", "prose": "where the house rules live (outside this document)", "established_around": [16, 16] }
  ],
  "expected_cross_links": [
    { "needs_side_child": 2, "provides_side_child": 1, "name": "authority_level_ordering", "evidence": "child 2's rules about conflicting instructions rely on the ranking described at L69-101" },
    { "needs_side_child": 1, "provides_side_child": 2, "name": "house_rules_location", "evidence": "noticed while writing this link that the concept was unseeded; seeded it (see self-check)" }
  ],
  "judgment_calls": [
    "Could have cut at L110 instead of L170; chose L170 because the definitions run L114-169 leans on terms from L1-113. A cut at L110 would have needed 4 more seeds."
  ] }
```

Before writing division.json, run this self-check: **every name appearing in
`expected_cross_links` MUST have an entry in `seed_vocabulary`** — including concepts you
noticed late while writing the cross-links; go back and seed them (as the example's
`house_rules_location` was, seeded only because its cross-link forced it). A cross-link
whose concept is unseeded hands your children a name collision.

`judgment_calls` is mandatory everywhere: any decision that could have gone another way,
with the road not taken named. An empty list is a claim that nothing was debatable.

---

## Phase L — LEAF: decompose your span into nodes

A node is exactly one checkable claim: **one rule** (obligation/prohibition/permission),
**one definition**, **one ordering or grouping**, **one scope statement**, or **one fact**.

Node format — every `needs`/`provides` entry is a `{name, prose}` OBJECT, never a bare
string; the prose is the authoritative meaning, the name is the join key:

```json
{ "id": "L171-800_n004",
  "establishes": "prose: the one thing this text settles, stated fully enough to check against the document",
  "needs":    [ {"name": "authority_level_ordering", "prose": "which of two authority levels outranks the other"} ],
  "provides": [ {"name": "applicable_instruction", "prose": "which candidate instructions apply to a request"} ],
  "spans":    [ {"lines": [181, 181], "quote": "must strive to follow all applicable instructions"} ] }
```

Rules, each demonstrated in the worked examples below:

1. **Split test:** an `establishes` joining claims that can be independently true/false of a
   situation is several nodes. **Preserve the document's modal verbs exactly** — "should"
   stays should, "must" stays must, "may" stays may, in `establishes` and every `prose`
   field: obligation strength is content, and upgrading a should to a must changes what the
   document says. **Watch the mixed-modal sentence**: one sentence often carries different
   modals for different clauses ("the assistant must adhere strictly ... the assistant
   should notify and seek approval") — keep each clause's own modal; do not let the
   stronger clause's modal bleed into the weaker one. One line often holds a whole paragraph and several claims —
   several nodes citing the same line, each narrowed by a verbatim `quote`.
2. **Merge test:** a list assigning one attribute across items ("vault requires Curator;
   reading room requires Visitor") is ONE mapping node. Split a row out only when something
   relies on it alone.
3. **Ordering nodes:** a list printed in priority order establishes the ordering by
   ARRANGEMENT — that is its own node spanning the whole list. Items may also be their own
   nodes, nested inside, and an item claim like "X is the highest" NEEDS the ordering.
4. **Heading metadata is content:** `{#section authority=root}` establishes a property of
   every rule under the heading — one node spanning the heading line, which those rules'
   nodes need. A bare topic heading establishes nothing and goes in `uncovered`.
   **A heading-metadata node governs exactly its own section: its provides name and prose
   must identify THAT section (e.g. "rules in the #make_presumptions section carry
   guideline authority"), never read as document-wide — and a rule node needs its OWN
   section's heading node, not a neighboring section's.**
5. **Everything else is a node** — commentary, commitments, motivation are nodes (facts and
   groupings). Each worked-example block is ONE node needing the rule it demonstrates; never
   decompose the dialog inside it. `uncovered` is only for titles and bare headings.
6. **Coverage identity over YOUR span:** every non-blank line of your span is inside some
   node's spans or some `uncovered` entry.
7. **Dangling needs are required honesty, and they are your interface upward.** If your span
   uses a concept it does not establish, write the needs entry and DO NOT resolve it —
   your parent resolves it against your siblings, or escalates. Use an inherited seed name
   if one fits; otherwise coin a name and describe it well. Never invent a node to cover
   what your span does not establish, and never silently satisfy a need your span cannot.
   **But before leaving a need dangling, check your OWN nodes' spans: if the concept is
   established inside your span, the establishing node must EXPORT a provides entry for it
   and the need resolves there — a dangling need whose definition sits in your own span is
   an export failure, not honesty.**
8. **Use seed names exactly** for every concept your dispatch seeded.

**Phase L output** — write to `<workdir>/graph.json`:
`{ "nodes": [...], "uncovered": [...], "judgment_calls": [...] }`
Prefix node ids with your span (`L171-800_n001`) so ids never collide across the tree.

### Worked example (leaf)

Document:

```
L01  # Greenfield Archive — Access Rules
L02
L03  Staff must log every retrieval, and must never leave the vault unlocked.
L04
L05  ## Clearance {precedence=charter}
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
L16  Where a charter rule conflicts with a house rule, the charter rule prevails. House rules are posted at the front desk.
L17
L18  Example: a Fellow may enter the reading room but not the vault.
L19
L20  The archive was founded in 1911.
```

Its leaf graph (span L1-20, no inherited seeds):

```json
{ "nodes": [
  { "id": "L1-20_n001", "establishes": "Staff must log every retrieval.",
    "needs": [], "provides": [],
    "spans": [ {"lines": [3, 3], "quote": "Staff must log every retrieval"} ] },
  { "id": "L1-20_n002", "establishes": "Staff must never leave the vault unlocked.",
    "needs": [], "provides": [],
    "spans": [ {"lines": [3, 3], "quote": "must never leave the vault unlocked"} ] },
  { "id": "L1-20_n003",
    "establishes": "There are three clearance levels — Curator, Fellow, Visitor — ranked by the printed order of the list, highest first.",
    "needs": [],
    "provides": [ {"name": "clearance_order", "prose": "which of two clearance levels is the higher one"},
                  {"name": "clearance_levels", "prose": "the set of recognized clearance levels"} ],
    "spans": [ {"lines": [7, 7]}, {"lines": [10, 12]} ] },
  { "id": "L1-20_n004",
    "establishes": "Curator is a clearance level, and it is the highest one under the ordering of clearance levels.",
    "needs": [ {"name": "clearance_order", "prose": "which of two clearance levels is the higher one"} ],
    "provides": [ {"name": "curator_level", "prose": "the Curator clearance level"} ],
    "spans": [ {"lines": [10, 10]} ] },
  { "id": "L1-20_n005",
    "establishes": "Visitor is a clearance level, the lowest under the ordering of clearance levels.",
    "needs": [ {"name": "clearance_order", "prose": "which of two clearance levels is the higher one"} ],
    "provides": [ {"name": "visitor_level", "prose": "the Visitor clearance level"} ],
    "spans": [ {"lines": [12, 12]} ] },
  { "id": "L1-20_n006",
    "establishes": "A room may be entered only by holders of a clearance at or above the room's required level.",
    "needs": [ {"name": "clearance_order", "prose": "which of two clearance levels is the higher one"},
               {"name": "room_required_level", "prose": "the clearance level each room requires"} ],
    "provides": [ {"name": "entry_rule", "prose": "whether a clearance holder may enter a given room"} ],
    "spans": [ {"lines": [8, 8]} ] },
  { "id": "L1-20_n007",
    "establishes": "Each room's required clearance: the vault requires Curator; the reading room requires Visitor.",
    "needs": [ {"name": "curator_level", "prose": "the Curator clearance level"},
               {"name": "visitor_level", "prose": "the Visitor clearance level"} ],
    "provides": [ {"name": "room_required_level", "prose": "the clearance level each room requires"} ],
    "spans": [ {"lines": [14, 14]} ] },
  { "id": "L1-20_n008",
    "establishes": "When a charter rule conflicts with a house rule, the charter rule prevails.",
    "needs": [ {"name": "charter_rules", "prose": "which rules are charter rules"},
               {"name": "house_rules", "prose": "which rules are house rules — the document points outside itself (front desk) and never lists them"} ],
    "provides": [],
    "spans": [ {"lines": [16, 16], "quote": "Where a charter rule conflicts with a house rule, the charter rule prevails"} ] },
  { "id": "L1-20_n009",
    "establishes": "House rules are posted at the front desk (outside this document).",
    "needs": [], "provides": [],
    "spans": [ {"lines": [16, 16], "quote": "House rules are posted at the front desk"} ] },
  { "id": "L1-20_n010",
    "establishes": "Every rule in the Clearance section is a charter rule — the heading's tag (precedence=charter) assigns this to everything under it.",
    "needs": [],
    "provides": [ {"name": "charter_rules", "prose": "which rules are charter rules"} ],
    "spans": [ {"lines": [5, 5]} ] },
  { "id": "L1-20_n011",
    "establishes": "A worked example demonstrating the room-entry rule: a Fellow may enter the reading room but not the vault.",
    "needs": [ {"name": "entry_rule", "prose": "whether a clearance holder may enter a given room"} ],
    "provides": [],
    "spans": [ {"lines": [18, 18]} ] },
  { "id": "L1-20_n012", "establishes": "The archive was founded in 1911.",
    "needs": [], "provides": [],
    "spans": [ {"lines": [20, 20]} ] }
],
"uncovered": [ {"lines": [1, 1], "reason": "title"} ],
"judgment_calls": [
  "No Fellow node: nothing relies on Fellow alone, it lives inside the ordering (merge test). Could have gone the other way for symmetry with n004/n005.",
  "house_rules left dangling: L16's second sentence says where they live, which is not settling which rules they are." ] }
```

Note in the example: one line, two nodes, separated by quotes (n001/n002; n008/n009); an
ordering node over a list with item nodes that refer back to it (n003 ← n004/n005); a
heading-metadata node consumed by a rule (n010 → n008); an example-block node (n011); an
isolated node (n012); a dangling need kept honest (`house_rules`).

---

## Phase U — UNWIND: link your children's graphs

You divided earlier; your children's `graph.json` files are now in the child workdirs named
in your re-dispatch message. Your transcript already holds your reading of the span and
your `expected_cross_links` — use them. Steps, in order:

1. **Concatenate** the children's nodes and `uncovered` (ids are already namespaced).
   **Never change a child node's id** — ids are how every level above you, and every log,
   refers to nodes. Only nodes YOU add carry your span's prefix.
2. **Resolve cross-child danglings:** for each needs entry in one child with no provider in
   that child, look for the provider among the other children. Same seed name → link is
   already mechanical. Different names for what your reading says is one concept → rewrite
   the needs entry's `name` to the provider's name (keep the needier's prose; record the
   rewrite in `judgment_calls` with both spellings). A need nothing provides STAYS dangling
   — it is your parent's problem or a true external reference. Never delete one.
3. **Restatement merge:** if two children each made a node establishing the SAME thing from
   different text, merge into one node carrying both nodes' spans (union the
   needs/provides; record the merge). Same thing means same claim — not same topic.
   **The survivor must absorb ALL content: after merging, verify every element of the
   retired node's establishes (every listed item, tier, or clause) appears in the
   survivor's establishes and provides prose — a merge that keeps the shorter statement
   silently deletes the difference.**
4. **Structure nodes of your own:** if an arrangement spanning your cut establishes
   something no child could see whole (an ordering whose list one child holds and whose
   consequences another does; a heading whose scope covers several children), add the node
   yourself, id-prefixed with your span.
5. **Check your predictions:** every `expected_cross_link` from your division either now
   exists as a resolved edge (say which) or did not materialize (say why — this is a
   judgment call, not a silent drop).

**Phase U output** — write to `<workdir>/graph.json` (your own, covering your whole span):
`{ "nodes": [...], "uncovered": [...], "judgment_calls": [...],
   "cross_link_report": [ {"expected": "...", "outcome": "resolved as edge X" | "did not materialize because ..."} ] }`

### Worked example (unwind, abbreviated)

Child A (L1-60) has `L1-60_n007` providing `{"name": "signal_priority_order", ...}` from a
numbered list. Child B (L61-140) has `L61-140_n003` with a dangling needs entry
`{"name": "signal_ranking", "prose": "which of two signals takes precedence"}`. Your
division seeded `signal_priority_order` and predicted this link. You: rewrite B's entry to
`"name": "signal_priority_order"` (keeping B's prose), record
`"cross_link_report": [{"expected": "B's precedence rules rely on A's ordered list", "outcome": "resolved: L61-140_n003 now needs signal_priority_order provided by L1-60_n007"}]`,
and add `"judgment_calls": ["renamed signal_ranking -> signal_priority_order; same concept, B coined its own name despite the seed"]`.

---

## Universal rules

- Verbatim `quote`s must appear on the cited lines; line numbers must exist. Both are
  checked mechanically after every phase. **A quote is ONE contiguous verbatim run of the
  document's own characters — never stitch fragments with `...` or paraphrase.** If a node
  needs two fragments, give it two spans, each with its own quote. A wrong quote is worse
  than no quote: when no contiguous fragment works, omit `quote` and let the line range
  carry the address.
- The `prose` of a needs/provides entry is the authoritative meaning everywhere; names are
  join keys. Never a bare string where the format shows an object.
- `judgment_calls` in every output file. A decision a reviewer might contest, with the
  alternative named.
- Do not read outside your span (Phase D/L) except as your dispatch directs; your parent
  handles what crosses your boundary.

## Granularity (added 2026-08-11, measured on the first DeepSeek build)

A node is one CLAIM — a statement someone could agree or disagree with —
never one sentence-fragment per node. Healthy density is roughly **one node
per 3-5 content lines**; a 200-line span typically yields 25-60 nodes. Two
signals of a broken reply, both rejected mechanically: more than ~1 node
per 2 lines, and any two nodes with identical establishes+spans (emit each
node ONCE; never repeat a node to fill out a list). If a span feels like it
needs hundreds of nodes, the span should have been divided instead.

## Output economy (added 2026-08-11, from token forensics of live replies)

- `judgment_calls` records DECISION CLASSES, never instances: one entry
  covering "renamed X->Y across all 220 needers" -- NEVER one entry per
  needer. More than ~10 entries in any reply is itself a defect. The
  mandate "empty list is a claim" is satisfied by classes, not volume, and
  never by narrating what a structured field (resolutions, merges) already
  records.
- `uncovered` uses RANGES: [{"lines": [30, 62], "reason": "..."}] -- never
  one entry per line.

## ds3 flags (driver-gated; inert unless your dispatch invokes them)

The two behaviors below apply ONLY when your dispatch text explicitly invokes them. A
dispatch that says nothing about them means everything above stands exactly as written —
in particular, Phase L emits `uncovered` itself and the coverage identity is yours to
satisfy.

- **Derived uncovered** (builds with `derive_uncovered` on): when your Phase L dispatch
  says the driver derives `uncovered`, do NOT emit an `uncovered` field. The driver
  computes it as the coverage complement of your nodes' spans and auto-labels formatting
  lines (headings, blanks, code fences, horizontal rules). Your whole coverage job is
  CONTENT lines: every one belongs to some node's spans. A content line that genuinely
  establishes nothing must be explained in `judgment_calls`, naming its line number
  (e.g. "L0042: transitional aside, establishes nothing"); an uncovered content line
  with no explanation is rejected mechanically.
- **Rename candidates** (builds with `rename_candidates` on): a Phase U dispatch may
  include a code-generated CANDIDATES block ranking provided names by prose overlap
  against each dangling need. It orders your reading, nothing more: confirm or reject a
  candidate on MEANING, never on name similarity or on its rank, and a need none of the
  candidates truly satisfies stays dangling.

## Borrowed concepts are the product (added 2026-08-11, from the ds2 scoring)

The graph exists to record which claims LEAN ON concepts established
elsewhere. A `needs` entry is not optional garnish: whenever your
establishes uses a term whose meaning this span does not itself fix — an
authority level, a named principle, a policy category, a section's rule —
that term belongs in `needs` with its prose. A content node with zero
needs is claiming its span is semantically self-contained; that is RARE in
this document (most sections lean on the chain of command, the risk
taxonomy, or a named principle). State what you borrow; the seed
vocabulary and the CANDIDATES block name concepts already established —
prefer THOSE names over coining your own.
