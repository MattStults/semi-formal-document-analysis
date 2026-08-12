# Meltdown analysis: DeepSeek-V4-Flash on Phase L, L1542-1800 (2026-08-11)

## Findings (quantitative)

**F1 — The loop begins at node 2.** The 470K-char reply (`runs/ds2/failed/1786478653962.json`)
holds 1000 sequential ids, 999 sharing one `establishes`; the first repeat is index 1
(`n002`), ~500 chars into the reply. The model never gets past L1545, the span's FIRST
content line. Both n001 and n002 cite L1545 with fabricated quotes; the looped sentence
("should not provide information that could be used to create harmful content...") appears
nowhere in the document — it is a generic safety hedge. Reply length ≈110K tokens; only the
131072 `max_tokens` cap ends it (no frequency/presence penalty is sent; temp 0.2, json_object).

**F2 — The "fabrications" are cross-reference RESOLUTIONS, not free inventions.** Every
stable quote-verbatim failure is a line whose `[?](#anchor)` link the model expanded into
remembered target prose:
- L1547 real: "...the assistant should typically [?](#assume_best_intent)." → claimed:
  "...should typically assume best intentions and comply; it should never ask the user to
  clarify their intent..." (real prefix verbatim up to the ref, then the ref's target text).
- L1613 real: "In addition to the guidance in [?](#support_mental_health), the assistant
  should convey..." → claimed: "In addition to the guidance in the support mental health
  section, the assistant should convey..." (footnote markers [^3kvn] also stripped).
- L1545 (590 chars, 3 footnote markers, "[?](#avoid_info_hazards)") → paraphrased, with
  "explosives" vocabulary imported from the fenced example at L1556/1560.
The failing refs are LOAD-BEARING phrases (object of "outlined in", the entire verb phrase
of L1547's final sentence — unreadable unless resolved). The healthy leaf 1101-1400
(`runs/ds2/c3/c1/c2/graph.json`, 40 nodes, 25 quotes) quoted its two crossref lines
(L1316, L1373) verbatim — but there the refs are parenthetical "(such as ...)"/"(see ...)".

**F3 — The meltdown is the endpoint of a rule-conflict squeeze, not the primary defect.**
Timeline across draws (timestamps 1786467xxx → 1786480xxx): (1) 4 repair rounds, identical
n007/L1547 verbatim failure each round; (2) quote attributed to blank L1542; (3) quote-honesty
pressure → model omits ALL quotes → 100 nodes cycling 10 establishes covering 8 lines,
"coverage identity fails: 204 unaccounted", ×4 rounds; (4) empty nodes list; (5) full
999-loop; (6) span split to 1542-1707 → same n007/L1547 failure ×4. Both exits are blocked:
quote → rejected as fabrication; omit → coverage fails. The degenerate attractor is where
the model lands when no continuation is rewarded. Repair feedback shows only the claimed
quote (60 chars), never the real line text, so no round can self-correct.

**F4 — The loop attractor is not unique to this span; the blocked-exit condition is.**
Two other giant replies loop the same way: span 1-170 (472K chars, loop at node 12 on L41,
988 copies) and 561-800 (381K, loop at node 9 on L623, 969 copies). L41 (199 chars), L623
(304), L1545 (590), L1547 (549) are all long multi-clause normative sentences. Those spans
eventually completed; 1542-1800 never does because its trigger lines cannot be quoted at all
under the current rule (F2). Safety content is the loop's *flavor* (hedge sentence), not its
cause — L41/L623 are not safety lines.

**F5 — Span statistics vs successes.** 1542-1800: 259 lines, 73% inside ~~~ fences, only 24
content lines, mean prose-line length 201 chars (max 831) vs 51 in the healthy 1101-1400;
3 crossrefs all mid-sentence load-bearing; 17 footnote markers. Fence density is NOT
discriminating (1801-2100 is 76%). The discriminator is: nearly all semantic weight sits in
4 very long lines (1545/1547/1613/1615-ish) that each mix crossrefs + footnotes.

**F6 — probes/meltdown_characterization.log exists but is empty (0 bytes)**; no probe
results to incorporate.

## Ranked hypotheses, each with a cheap discriminating test

**H1 (strong — direct textual evidence, F2): mid-sentence load-bearing `[?](#anchor)` links
break verbatim quoting.** The model reads the ref as a semantic placeholder and renders its
resolution; verbatim check then rejects; the line is unquotable in principle for this model.
Test (~$0.001): one Phase L dispatch on L1542-1560 with the span text pre-rewritten
`[?](#x)` → `(see: x)`. Predict: quotes pass. Control: same dispatch unmodified fails at the
same char offset. Protocol fix: driver normalizes refs before dispatch (and un-normalizes in
stored quotes), or brief rule "a quote must END before any `[?](` or `[^` token" with a
worked example doing exactly that on a ref-bearing line.

**H2 (strong for the 999-loop specifically, F1/F3/F4): unpenalized-repetition attractor
under blocked-exit pressure.** json_object forcing + temp 0.2 + no frequency penalty + a
validator that rejects both available continuations = degenerate fixed point; 131072
max_tokens lets it run to 110K tokens. Test (~$0.01): redraw the failing dispatch once with
`frequency_penalty: 0.3` (or `max_tokens: 8192`). Predict: loop absent or cheap; the
*verbatim* failure (H1) persists — which also discriminates H1 from H2. Protocol fix:
streaming duplicate-establishes guard (3 identical → abort draw; `_health` already computes
this post-hoc) and a Phase-L-specific max_tokens (a 259-line leaf never needs 131K).

**H3 (moderate): repair rounds starve the model of the ground truth.** Feedback never
includes the real line text, so rounds 1-4 are byte-identical failures. Test ($0.003): one
repair round whose error message appends `REAL L1547: <full line>`. Predict: fixes in one
round even without H1's rewrite.

**H4 (weak, subsumed by H1): footnote markers `[^kdoq]` inside quote runs.** Stripped in
every fabricated quote. The H1 probe's rewrite should also leave footnotes in place to see
whether they independently break matching.

**H5 (refuted): token-position effect.** The 1542-1707 re-split moved the span boundary and
shortened the context; failure is byte-identical at L1547 → position not causal.

**H6 (mostly refuted): safety-content hedging as the cause.** The looped sentence is
safety-flavored, but the same loop fired on non-safety spans (L41, L623). Safety content
selects the attractor's wording and may lower the barrier (the L1545 paraphrase mixes in
"explosives" from the fenced example), but the mechanism is H1+H2. Test rides along with
H1's probe: if the ref-rewritten safety span succeeds, safety content alone was never
sufficient.

## Recommended change to solve the span unaided
(1) Pre-normalize `[?](#x)` (and optionally `[^id]`) in dispatched span text, or add the
quote-terminates-before-ref rule + example (H1). (2) Cap Phase L max_tokens and add the
streaming duplicate guard (H2). (3) Include the real line text in quote-verbatim repair
feedback (H3). Expected: (1) alone likely unblocks the leaf; (2)+(3) make any residual
failure cheap and self-correcting.

Note (post-analysis): `recurse_driver.py` now carries a `normalise()` quote-verification
helper (strips `[^id]`, rewrites `[label](url)` → `label`, straightens curly quotes,
collapses whitespace) — this handles H4 and the *cosmetic* half of H1. It does NOT rescue
the `[?](#x)` resolution case: `[?](#assume_best_intent)` normalises to `?`, while the model
writes the ref's *target prose* ("assume best intentions and comply..."), so L1547-style
quotes still mismatch. The pre-dispatch rewrite or quote-stops-before-ref rule is still
needed; H1's probe remains the discriminating test.
