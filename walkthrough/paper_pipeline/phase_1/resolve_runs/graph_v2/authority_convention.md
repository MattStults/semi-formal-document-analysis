# Authority-edge canonicalization: the mandated convention (prepared, NOT yet run live)

Motivation: `edge_divergence_analysis.md` — the section-authority edge class alone is ~47%
of all golden-vs-ds3 edge divergence. Both graphs judge "this heading's `authority=X` label
leans on the Levels-of-authority definitions (L67-101)"; they diverge only in HOW they
attach it. The fix candidate is one mandated convention in the dispatch text, smoke-tested
by `smoke_authority.py` before any pipeline change. All analysis below is deterministic,
no API spend.

## The convention paragraph (verbatim text appended to the leaf dispatch extra)

> AUTHORITY-LABEL CONVENTION (mandatory). Headings in this document carry inline
> `authority=X` labels (X in root/system/developer/user/guideline). When you emit a node
> for such a heading, record the label's dependence on the document's authority-level
> definitions as a `needs` entry naming the SHARED, document-wide concept for that level
> — exactly one canonical name per level: `root_authority`, `system_authority`,
> `developer_authority`, `user_authority`, `guideline_authority` (prose: "the X authority
> level as defined in Instructions and levels of authority"), or
> `authority_levels_hierarchy` when the ordering between levels is itself at stake.
> **Never coin a per-section name for this dependency** (patterns like
> `<section>_section_authority` or `<section>_section_root_authority` are forbidden):
> the concept belongs to the whole document, and a section-local coinage prevents the
> edge from resolving to the shared definition.

Key sentence: **every heading node with an `authority=X` label carries a `needs` entry
naming the shared canonical authority-level concept (one canonical name per level, e.g.
`guideline_authority`), never a per-section coinage.**

## The two conventions it must disambiguate

**Golden (`recurse/root/graph.json`, L3995-4164 region)** — shared canonical names.
Heading nodes at L3997/L4050/L4073/L4138 each carry `guideline_authority` (heading nodes
provide it locally for their section's consumers; elsewhere, e.g. `L1975-2125_n010` at
L2050, the heading *needs* the shared `authority_levels_hierarchy` from `L1-170_n028`).
Either way the NAME is the document-wide concept, so at unwind the class resolves to one
shared provider and edges become comparable.

**ds3 (`runs/ds3/root_graph.json`, same region)** — per-section coinages. The same
headings become `do_not_make_unprompted_personal_comments_section_authority` (L3997),
`avoid_being_condescending_section_authority` (L4050), `refusal_style_section_authority`
(L4073), `formatting_section_authority` (L4138), `be_thorough_section_authority` (L4163):
one freshly minted hub name per section, plus separate long edges to L67. Same judgment,
uncomparable plumbing.

The convention resolves the class to a third, uniform shape (needs-based, shared name);
both historical shapes above are what it forbids drifting back into.

## Mechanical scorer (see `smoke_authority.py`)

Per graph, per span: heading-authority nodes = nodes whose spans cover a document line
containing `authority=`. A needs/provides entry is *canonical* when its name tokens are
drawn entirely from the authority vocabulary (level words + generic authority terms) and
include `authority` — token-based, not exact-string, so `user_authority_metadata` and
`authority_levels_hierarchy` count, while `refusal_style_section_authority` does not.
Primary metric: fraction of heading-authority nodes carrying a canonical concept
(needs OR provides — the shared NAME is what makes the edge class matchable in
`graph_compare.py`); `canon_needs` is reported separately as the convention's strict
form. Band: PASS at >= 0.8.

Note: ds3's inherited seed vocabulary already fixes `authority_level_ordering`
(established L69-103); its tokens are all authority-vocabulary, so a live draw that
routes the heading dependency through the seed name instead of the convention's
`authority_levels_hierarchy` still scores canonical — the scorer measures
shared-vs-coined, not which shared name won.

Why not the naive "prose mentions authority + level word" match: it does not
discriminate — ds3's coinages describe their level in prose too (55 heading-authority
nodes, 51 prose-match "canonical"). Name-token canonicality does discriminate (below).

## Span selection and scorer self-test (dry run, free)

Spans chosen by authority-label density *subject to the self-test asymmetry holding*
(the scorer must PASS the golden's own nodes and FAIL ds3's, or it validates nothing).
The densest raw span, L3502-3755 (5 labels), is unusable: the golden itself skips the
class there (0/5), consistent with the analysis's "partially disjoint subset of ~40
headings". Chosen dispatches:

| span | authority labels | GOLDEN self-test | ds3 self-test |
|---|---|---|---|
| A: L3995-4164 | 5 (3997, 4050, 4073, 4138, 4163) | 4/5 = 0.80 **PASS** (needs-only 0) | 0/5 = 0.00 **FAIL** |
| B: L1975-2125 | 3 (1975, 1979, 2050) | 3/3 = 1.00 **PASS** (needs-only 3) | 0/3 = 0.00 **FAIL** |

Golden's A-span misses only `L3995-4164_n025` (the bare L4163 heading, no concept at
all); its A-span heading nodes carry the canonical name in `provides`
(`guideline_authority`), while its B-span nodes carry it in `needs` — the two golden
sub-shapes the primary either-side metric deliberately unifies.

That free asymmetry validates the scorer before any spend. Seeds are reconstructed from
`runs/ds3`'s tree (deepest division whose span covers the dispatch): A →
`runs/ds3/c3/c3/c3/c2/division.json` (50 seeds), B → `runs/ds3/c3/c3/c1/division.json`
(48 seeds). Dispatch = `Driver.dispatch_block("L", lo, hi, seeds,
R.leaf_extra(lo,hi) + CONVENTION)` with `R.leaf_schema(lo,hi)` — same single-source
extra and grammar the pipeline uses.

## Status

Prepared only. `python3 smoke_authority.py` (dry-run default) reprints the self-test and
the full dispatch texts. Live run (`--yes`, ~2 draws x 2 dispatches, cost-capped like
`smoke_granularity.py`) is NOT authorized by this prep; check the spend question against
`spend.py`'s ceiling first.
