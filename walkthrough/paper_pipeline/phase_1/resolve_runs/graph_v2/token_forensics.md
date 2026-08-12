# Token forensics: where DeepSeek-V4-Flash graph replies spend their budget

Method: field-level char counts (chars/4 ≈ tokens) over every complete probe reply, every
unique `runs/ds*/failed/*.json` reply, and the root_D draws. Script logic: JSON-parse the
reply, measure `len(json.dumps(value))` per top-level field. All 13 unique failed replies
parse — truncated completions were retried-and-discarded by translate.py (9 `finish_reason=length`
events in `runs/ds1/driver_log_{0110,128k}.txt`), so the runaway shape is inferred from the
one loop that finished under the cap (below).

## Findings

**1. Three distinct sinks, one per phase — no single field dominates everywhere.**
- LEAF (healthy, c1_L samples 0-2): `nodes` 81-95%, `judgment_calls` 5-7%, structure ~10%.
  The sink is node COUNT: 70/94/112 nodes vs 46 expected (1.5-2.4x over-granularity).
- LEAF (pathological, leaf_1101_diag.txt, 55,892 chars): `nodes` 44.6%, **`uncovered` 29.0%**
  (16,200 chars = 300 single-LINE entries, one per example line: `{"lines":[1102,1102],"reason":"example content"}`
  repeated for a 300-line block), `judgment_calls` 8.2%.
- UNWIND (u_diag_last_reply.txt, 28,025 chars): **`judgment_calls` = 93.8%** (26,279 chars,
  222 items). `structure_nodes` 2.0%, `resolutions` 0.4%.
- DIVISION replies are never a sink: 143-1,196 chars each (root_D and failed D replies).

**2. Yes — the judgment_calls mandate scales with instance count, not decision count.**
- Unwind: 220 of 222 items are the SAME rename narrated once per needer ("Renamed
  L527-796_n023's need 'chain_of_command' to 'authority_levels_hierarchy'…", avg 114 chars) —
  one decision, 220 narrations, ~6.3K tokens. Meanwhile the structured `resolutions` list,
  which is supposed to carry exactly this, has 1 entry.
- leaf_1101: 49 of 52 items are per-example trivia ("The example at lines 1394-1398 is a BAD
  example of sensitive content handling.") — per-line enumeration, not contested decisions.
- The trigger is the brief's line 79-80: "`judgment_calls` is mandatory everywhere… An empty
  list is a claim that nothing was debatable." The model satisfies the mandate by volume.

**3. Truncation deaths are repetition, not meta-commentary.**
runs/ds1/failed/1786446184401.json (381,782 chars ≈ 95K tokens, the largest reply on disk):
1,000 nodes, only **32 unique** `establishes` — one node ("The assistant should not avoid or
censor topics…") emitted **969 times** as full ~385-char node objects ≈ 373K chars =
**97.6% of the reply**. This one squeaked under the 128K cap; the 9 `finish_reason=length`
retries in the driver logs are the same loop pattern that didn't. leaf_1101 shows the small
form: 82 nodes, 2 unique (81 duplicates). The looped content is well-formed nodes — the
model dies generating content-shaped repetition, never prose meta-commentary.

**4. No hidden reasoning channel.** leaf_1101 usage: `completion_tokens` 15,883,
`reasoning_tokens` null, visible text 55,892 chars ≈ 13,973 tok at chars/4. The ~12% gap is
tokenizer density (JSON runs denser than 4 chars/tok), not a reasoning burn. All spend is
visible output.

## Prompt clarifications, ranked by expected savings

1. **Loop brake (saves up to ~90K tok/reply; prevents the truncations outright).** The new
   Granularity section already bans duplicates as a validity rule; add it as a GENERATION
   rule: "If you notice you have already emitted a node with this `establishes`, do not emit
   it again — close the current array and continue to the next field." Evidence:
   1786446184401.json (969x, 97.6% of reply); leaf_1101 (81x).
2. **Rewrite the judgment_calls mandate (saves ~6K tok/unwind, ~1K/leaf).** Replace
   "mandatory everywhere / an empty list is a claim that nothing was debatable" with: "one
   entry per decision CLASS, 3-8 entries total; a rename or rule applied to N nodes is ONE
   entry naming the rule and listing affected ids; never restate anything already encoded in
   `resolutions`/`merges`; per-line or per-example observations are not judgment calls."
   Evidence: u_diag 220/222 rename items = 93.8% of the reply; leaf_1101 49/52 per-example items.
3. **Uncovered as ranges (saves ~4K tok on example-heavy leaves).** State: "`uncovered`
   entries are maximal contiguous RANGES with one reason — never one entry per line."
   Evidence: leaf_1101's 300 single-line entries (16,200 chars, 29%) collapse to ~3 range
   entries (~200 chars).
4. **Node-count ceiling as a target, not just a reject.** The granularity section's
   "25-60 nodes per 200 lines" should be echoed in Phase L itself ("if you are past ~60
   nodes, stop and re-check for splits/duplicates") — healthy c1_L draws still ran 1.5-2.4x
   over the haiku reference (70/94/112 vs 46), and `nodes` is 81-95% of every leaf reply, so
   granularity is the multiplier on the dominant field.

Items 1-3 together would have kept every reply on disk under ~10K completion tokens.
