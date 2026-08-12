# Edge divergence after the ds4 fixes: why recall barely moved

Inputs: `runs/ds4/compare_vs_golden.json` (golden=a: 512 edges, ds4=b: 970; unmatched 335 /
721), `recurse/root/graph.json` (593 nodes), `runs/ds4/root_graph.json` (780 nodes) and its
`root_graph.pre_resolution.json`. Method identical to `edge_divergence_analysis.md` (ds3):
need-name+prose token overlap >= 0.5 vs all counterpart edges; authority class = need name
matching `authority|root_instruction`. Deterministic, no API spend.

## Findings

**(a) The authority class did NOT close: 47% of divergence in ds3 -> 48% in ds4** (504/1056 vs
413/876), and it GREW in absolute edges (413 -> 504). It is 451/721 (63%) of ds4-only and
53/335 (16%) of golden-only. Two sub-mechanisms, neither touched by the convention as deployed:

1. **The convention's own canonical edges are mostly non-golden: 183 of the 451.** ds4 now
   dutifully draws heading -> shared-definition edges with canonical names (`root_authority` 74,
   `authority_level_ordering` 44, `guideline_authority` 34, ...) from ~100 heading nodes — but
   golden instantiates that class over only a partial subset of headings (ds3 report, E10), so
   systematic instantiation manufactured ~183 new unmatched edges. Dual providers (L71 *and*
   L186 both provide `root_authority`) double most of them (101 needer-need pairs -> 183 edges).
2. **Per-section coinages survived on CHILD nodes: 268 of the 451.** The convention bans
   `<section>_section_authority` only in the *heading's* needs entry; children still need the
   coinage from their heading (`letter_and_spirit_section_authority` etc., 237 distinct
   needers). Golden's children carry needs=[] — it never draws child -> heading authority
   plumbing. This intra-section fan-out is the single largest surviving block.

**(b) Class shares on the combined unmatched set (n=1056):**

| class | golden-only (335) | ds4-only (721) | combined |
|---|---|---|---|
| same prose, different attachment (overlap >= 0.5 vs counterpart edge) | 187 (56%) | 623 (86%) | 810 (**77%**) |
| genuinely absent in counterpart | 148 (44%) | 98 (14%) | 246 (23%) |
| counterpart expressed it but it dangled | 0 | 0 | 0 (ds3: 4%) |
| (cross-cut) strict granularity swallow (edge inside ONE counterpart node) | 6 (2%) | 84 (12%) | 90 (9%) |
| (cross-cut) created by the resolution pass | — | 119 (17%) | 119 (11%) |

The resolution pass eliminated the dangling class as designed (150/155) but at a bad exchange
rate: of its 140 new edges, **119 (85%) match nothing in golden** — dangling needs became wrong
or convention-noise edges (`content_definition` 38, `transformation_exception_section_authority`
16, `chain_of_command` 10, ...). Precision fell 0.297 -> 0.257. Shadowing also worsened: 336
ds4 shadowed edges vs golden's 76 (strict recall 0.164), driven by the same fan-out.

## Case walkthroughs

**C1 (ds4-only x2, `root_authority`, L292 -> L71 / L186) — convention edge golden doesn't
draw.** ds4 `L292-425_n001` (the `authority=root` "letter and spirit" heading, L292) needs
canonical `root_authority`, resolving to BOTH L1-170_n034 (L71) and L171-203_n009 (L186).
Golden `L292-526_n001` (same L292) has needs=[], providing `root_authority_rules` locally.

**C2 (ds4-only x3, `letter_and_spirit_section_authority`, L294/L296 -> L292) — surviving
child coinage.** ds4 `L292-425_n002/3/4` each need the per-section name from the heading;
golden's counterparts (`L292-526_n002/3`, L294-296) carry needs=[]. 268 edges of this shape.

**C3 (ds4-only, `content_definition`, L270 -> L126) — resolution-pass mis-resolution.**
Pre-resolution, `L204-291_n015` (L270, root/system-conflict example) dangled on
`stay_in_bounds_content_categories`. The pass renamed it to `content_definition` ->
L1-170_n059 (L126), the *message-format* field "`content`: a sequence of text ... chunks" —
semantically wrong provider; 38 such edges. Golden draws the dependency correctly:
`disallowed_content_categories` L818 -> L812-816 (golden-only, since ds4's landed at L126).

**C4 (golden-only x3, `guideline_authority`, L3999 -> L4050/L4073/L4138) — mirror of C2.**
Golden `L3995-4164_n002` (L3999) needs canonical `guideline_authority` from sibling heading
providers. ds4's node at L3999 (`L3954-4136_n009`) instead needs
`do_not_make_unprompted_personal_comments_section_authority` — the exact coinage the convention
was written to kill, intact because it sits on a non-heading node.

## Verdict and implication

Recall moved only 0.316 -> 0.346 because the fixes targeted edge *naming*, but the matcher
scores line-region overlap: the class only closes when both graphs draw edges between the SAME
REGIONS. The convention added a systematic region pattern golden only partially has (183 new
misses), left child -> heading plumbing untouched (268), and resolution minted 119 more.

**Actionable implication: stop trying to make the graphs converge on this class and neutralize
it in scoring instead** — have `graph_compare.py` collapse/exclude authority-plumbing edges
(canonical heading edges AND `*_section_authority` child edges) as one equivalence class, and
gate the resolution pass on need-vs-provider prose similarity (C3's rename had near-zero
overlap). That addresses ~59% of ds4-only divergence with no judgment content at stake; the
golden-only "genuinely absent" block (148, 44%) is the real recall work not yet started.
