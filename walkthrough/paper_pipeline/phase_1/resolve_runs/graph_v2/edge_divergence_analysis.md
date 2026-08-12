# Edge divergence: mechanism analysis

Inputs: `runs/ds3/compare_vs_golden.json` (golden=a: 512 edges, ds3=b: 748; unmatched 350 / 526),
graphs `recurse/root/graph.json` (593 nodes) and `runs/ds3/root_graph.json` (804 nodes),
`adjudication/edge_sample.json` + verdicts A/B. All analysis deterministic, no API spend.
Matcher context: `graph_compare.py:245` matches by line-region overlap only (any Y-edge whose
needer AND provider lines overlap), so prose/name divergence (d) *cannot by itself* unmatch an
edge, and node splits are matched generously — every unmatched edge means the counterpart draws
NO edge between those two document regions.

## Findings (full-set, mechanical)

Proxy: need-name+prose token overlap >= 0.5 (overlap coefficient) against every counterpart edge.

| class | golden-only (n=350) | ds3-only (n=526) | combined (876) |
|---|---|---|---|
| same dependency, counterpart attaches it to a DIFFERENT node pair (b, granularity-assisted a) | 55 (16%) | 407 (77%) | 462 (**53%**) |
| counterpart expressed the same need but it DANGLED (provider never named) | 37 (11%) | 0 | 37 (4%) |
| genuinely absent in counterpart (c / unshared judgment) | 258 (74%) | 119 (23%) | 377 (43%) |

Cross-cutting: **the authority-label edge class alone is 47% of all divergence** — need names
matching `authority|root_instruction` are 355/526 (67%) of ds3-only and 58/350 (17%) of
golden-only. Both graphs draw "this section's `authority=X` label leans on the authority-level
definitions (L67–101/L183)" edges, but each instantiates the class over a different partial
subset of sections and routes it differently: ds3 makes a per-section `X_section_authority`
hub plus long edges to L67 (fan-out from finer nodes: 113 vs 46 in L1-170 alone); golden uses
shared `guideline_authority`/`authority_levels_hierarchy` providers from fewer sections. Of
ds3-only `prose_elsewhere` cases, 218/233 are this class — golden has the same-prose edge, from
other sections. Pure granularity swallowing (edge internal to ONE counterpart node, mechanism a
strict) is small: 55/526 ds3-only (10%), 12/350 golden-only (3%). Secondary asymmetry: ds3 has
**119 dangling need instances vs golden's 3** — ds3 states the dependency but its provider
naming fails to resolve, so the edge never forms (a within-graph (d) failure, not a matcher one).

## Case walkthroughs (all SUPPORTED by at least one seat)

**E00 (ds3_only, `conversation_definition`, L169 -> L118) — class (b/c).** ds3 nodes n112/n113
(L169) need `conversation_definition`, resolved to n076 (L118). Golden has a node at the *same
granularity* (`L1-170_n046`, L169) with needs=[] provides=[] — no split, no naming issue; golden
simply did not judge truncation to lean on the conversation definition. Genuinely absent.

**E08 (ds3_only, `authority_level_ordering`, L2137 -> L67/L183) — class (b), authority class.**
ds3 `L2125-2302_n004` (L2137, "Assume an objective point of view" heading) draws 3 long edges to
the authority-ordering providers. Golden's L2137 node (`L2126-2303_n003`) instead encodes the
label locally as provides=`user_authority_metadata`, needs=[] — same reading, opposite routing.

**E10 (golden_only, `authority_levels_hierarchy`, L2050 -> L69-101) — mirror of E08.** Golden
`L1975-2125_n010` (L2050, "Respect real-world ties" heading) -> `L1-170_n028` (L69-191). ds3's
counterpart `L1974-2124_n011` (L2050) has needs=[] and only *provides*
`respect_real_world_ties_section_root_authority` for local consumers. Each graph draws the
heading->definitions edge for a partially disjoint subset of ~40 headings; the symmetric
difference of two partial instantiations of one edge class is what the matcher counts.

**E28 (ds3_only, `be_clear_section_authority`, L3778 -> L3756) — class (b), identical node
boundaries.** Both graphs carve L3762-76 / L3778 / L3780 identically. ds3 links each example to
the section header (authority chain); golden links the same needers to
`direct_answer_requirement` (L3760, the rule content) and `avoid_errors_principle` (L3150). Two
defensible answers to "what does this example lean on"; zero granularity involvement.

**E07 (golden_only, `extremism_prohibition`, L1199 -> L1157) — dangling counterpart (d-within-
graph).** Golden n010/n011 -> n008 (L1157). ds3's `L1107-1235_n008` (L1199) needs
`radicalization_deescalation` and n012 (L1172-97) needs `extremist_violence_prohibition` — ds3
saw dependencies here, but *neither name is provided anywhere in ds3*, so both dangled and no
edge exists. The judgment was made; the naming step lost it.

**E15 (golden_only, `restricted_content_rule`, L856-858 -> L854) — dangling + boundary shift.**
Golden `L810-919_n009` (L856-858) -> n008 (L854). ds3 nodes n022/n023 (L858 only) need
`information_hazard_prohibition` — also unprovided in ds3, so dangling; and ds3's node omits
L856, so even a resolved edge would attach one line off.

## Verdict

**Dominant mechanism: (b) — both models see the same dependencies but attach them to different
node pairs / route them through different intermediates, concentrated in one edge class
(section-authority plumbing), with granularity (a) as an amplifier, not a cause.** Estimate:
~53% of unmatched edges have a same-prose counterpart edge at a different attachment (and ~47%
of ALL divergence is the authority-label class alone); strict granularity-swallowing is ~8%;
~43% are genuinely absent, which is real judgment variance (c/b) plus ds3's 119 dangling needs.
Blind seats certify both sides because both attachments are document-supported readings of the
same underlying dependency — the graphs disagree far less than the edge recall of 0.32 implies.

**Actionable implication:** canonicalize the authority-label edge class before comparison —
mandate one attachment convention (every `authority=X` heading links once to the L67-101
definitions, prompt-side), or collapse/exclude the class in `graph_compare.py` scoring — and
make the driver resolve or reject dangling needs (ds3: 119). Together these address roughly
half of the measured edge divergence without touching any genuine judgment content.
