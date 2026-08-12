# Decomposition-step experiment plan — v2, written while run 1 executes

## Decisions taken (with grounds), open to challenge

**D1 — names are ASSIGNED in this pass.** The measured failures (1/32, 0/32 name overlap;
0.00 borrowed-name agreement in ITERATION_LOG §8) are all *prediction* or *independent
coining*. A single global pass that assigns one name and reuses it on both sides has neither
problem, and it makes dangling-needs mechanically countable. Prose stays the authoritative,
cross-run-comparable content. Risk: naming could degrade the prose or tempt name-similarity
sloppiness → E1 tests it.

**D2 — the forcing rule is functional, not numeric.** v1's "tens not hundreds" produced 19
section summaries. Replacement: one node = one checkable claim (rule / definition / ordering /
scope / fact); split when the establishes joins independently-violable claims; merge test for
attribute-mappings so it doesn't shatter into 593 clauses again. Coverage obligation +
`uncovered` list pushes against summaries from the other side.

**D3 — worked example carries the load** (DEBUGGING_TIPS §1). v1 had NO example. The toy
document demonstrates: compound-sentence split (same-line overlap via quotes), ordering node
over a list (multi-span), item nodes nested inside it and needed individually, the merge
test, a dangling need, an isolated node, name reuse.
  ⚠️ Matt's spec of required property (c) was truncated mid-sentence ("at least o…"). I
  inferred: within the list subgraph, at least one item node nested inside the ordering
  node's span and relied on individually elsewhere. CONFIRM WITH MATT.

**D4 — addressing:** raw-file line ranges + optional verbatim quote to narrow within a line.
Both machine-checked (`graph_check.py`, normaliser per §17).

**D5 — process:** chunked read → incremental node file → one global reconciliation pass →
JSON to disk; self-report collected separately, treated as proposer (§6).

## Head-to-head experiments (want Matt in the loop before running the expensive/decisive ones)

- **E1 names vs no-names** (v2A vs v2B): n=3 each on Haiku. Compare: node count/size dist,
  overlap use, dangling rate, and — the real question — whether prose quality or graph shape
  differs. If no harm, names win by default (linking becomes mechanical).
- **E2 process shape**: single global pass (v2A) vs claim-enumeration-then-grouping (v2C):
  first list every atomic claim with its span, then group/link. Targets the section-summary
  attractor from a different side.
- **E3 stability**: n=3–5 repeats of the winner. Extension identity was 97% stable in prior
  work; the graph's spans should reproduce; node boundaries and names are the open question.
  This is the go/no-go: an unstable graph can't anchor translation.
- **E4 audit turn**: "which node establishes THIS sentence?" over unaccounted normative
  lines, state pinned (62%-replacement finding). Run only after single-pass shape is stable.
- **E5 model tier**: same winning prompt on Sonnet — does disagreement shrink or change
  character? (GRAPH_KEY's own step 2.)

## Mechanical checks per run (graph_check.py, calibrated against v1's known failures)

span resolution, quote verbatim-rate, size distribution, overlap/nesting counts (K5),
name-link resolution + dangling list, K1 (L183–191 ordering node), coverage accounting.
Reading-based checks: does establishes state content or summarize; needs/provides prose
sanity; the K2/K3/K4 checks from GRAPH_KEY.

## Iteration budget

Up to 5 Haiku runs, then check in with Matt (or earlier on a serious issue / drift).

## Run log

**Run 1 (v2A, single-pass).** 246 nodes, spans all resolve, 43 names, 2 dangling, 29
overlap pairs. Failures: K1 list (183–191) unaccounted (ordering grounded only at L69–99);
0/59 authority-tagged headings captured; 204/246 nodes zero-needs; coverage accounting
abandoned after L113; 0 quotes. Self-report falsely claimed its ordering node spanned
L186–190 (actually 69–99). DISCOVERY: heading `authority=` tags are the highest-value
formatting-carried content and no run had been asked to catch them; also the GRAPH_KEY claim
"the ranking is stated nowhere in sentences" is overstated for the raw doc — L69–99 states
relative ranks in prose. The 183–191 numbered list is still the crispest total order.

**Run 2 (v2B: + heading rule, restatement rule, needs sweep, coverage identity, quote rule).**
158 nodes, 48 names, 6 dangling, K1 substantively PASSES (n034 `authority_ordering`,
span 185–190 off-by-one, misses L191), headings 34/59, zero-needs 93/158, coverage identity
holds (1 unaccounted). REGRESSION: coarsening — mechanical obligations were paid for by
merging claims (5 mitigations → one node; per-level item nodes gone; 292 substantive prose
lines node-less vs 123 in run 1). Quotes still 0. Diagnosis: constraint competition — the
model satisfies the most mechanical constraint and relaxes the fuzziest one (the split
test). Self-report wrongly said the worked example lacked heading-metadata nodes (n010 is
one) — proposer, not verdict, again.

**Run 3 (v2C: split-test self-check + "never trade granularity for bookkeeping" + staged
process: Phase A extraction region-by-region, Phase B global passes with accounting last).**
WORST RUN: 95 nodes covering 44 lines, 0 names/needs/provides (Phase B never ran), lines
795–4691 declared uncovered wholesale, 0/59 headings. Confirms the capacity-bound reading:
told not to coarsen, Haiku truncated SCOPE instead. Three runs, three different casualties,
same ~100–150k token budget.

## Matt's rulings (check-in after run 3, 2026-08-10)

1. **Fan-out approved but deferred** until the failure is characterized: he doubts 400-line
   regions can carry document-level dependencies (attempt-2 history: section-scoped
   extraction lost the ordered-list rule). Sonnet worth trying only if the failure is
   capacity, not comprehension. Slice-scoped iteration fine if the slice is complex enough.
2. **Worked-example requirement (c), verbatim:** "within (b), at least one item node that
   refers back to the ordering node, so a hierarchy is demonstrated rather than described."
   → v2D: n004/n005 now NEED `clearance_order` (item → ordering edges).
3. **Everything is a node** — front matter, commentary, commitments all become nodes;
   `uncovered` only for text establishing nothing (titles, bare headings). v2D: example
   blocks become ONE node each, needing the rule they demonstrate.

**Run 4 (v2D, Haiku, slice L1–800 only):** 156 nodes at claim granularity (87k tokens —
envelope NOT exhausted), K1 exact-span pass, 7/7 headings, perfect accounting, quotes used
(80% verbatim; 13 real paraphrases). Defects: 129/129 needs/provides as bare strings
(format regression), ordering unconsumed, 70% zero-needs. ⇒ extraction is slice-solvable
on Haiku; linking stays weak even with effort to spare.

**Run 5 (v2D, Sonnet, full doc):** 580 nodes, 347k tokens. n031 restatement-merge
(L69+L186–191) with 13 consumers incl. the L181 chain; 59/59 headings; 636 needs / 16%
zero-needs; 906/906 {name,prose} objects; 31/31 quotes verbatim; coverage holds.
Self-admitted back-half coarsening (~150–300 nodes light); zero dangling (self-flagged).
First fully-accurate self-report.

**Matt's rulings after runs 4/5:** target executor is DeepSeek (unknown tier mapping) ⇒
design for small-model-completable steps + verification, per the repo's seat doctrine.
My "linking is a tier effect" was an overreach — bundled-linking data says nothing about
decomposed linking. Golden: cheap generation × N + Fable adjudication of disagreements +
audit sample, judgment calls logged — NOT Fable doing the mapping.

## Recursion probe (Matt's design: same transcript divides and later links; one branch
deep, close inspection per level; shared prompt RECURSE_PROMPT.md)

**Level 0 (root, L1–4691, Haiku):** division mechanically sound — cuts at 170/171 and
3147/3148 both verified real boundaries; 7 seeds incl. authority_levels_hierarchy
est_around [69,191] (correctly spanning both statements of the ordering). Defects: all 4
long-range 2→3 cross-links (Under-18 family) unseeded — repair turn added all 4 correctly
(anchors verified). Sampling instead of full reading, admitted in its own uncertainty flag
→ read-everything made explicit in child dispatches. Division-level repairability: works.

**Level 1 (c2, L171–3147):** cuts verified on `#` boundaries (797, 2126); seed inheritance
works (4 passed down, one anchor legitimately narrowed, 3 sensible new). Same unseeded-
cross-link defect recurred → promoted to prompt per §8a (self-check + example showing a
seed forced by its cross-link). Repair turn fixed it.

**Level 2 (c21, L171–796):** cuts on `##` headings (292, 527); ALL cross-links seeded
(prompt fix held); coined letter_and_spirit_principle seed with the exact self-check
reasoning. Defect: two one-line blank gaps between children — repaired.

**Level 3 (c212, L292–526):** clean 2-way cut on heading L426; rule-(a) claim "no linkage
crosses" recorded as falsifiable prediction; empty cross-links legal. Unwind will test it.

**PRE-REGISTERED: the c21 unwind key (written before c213/c21-U ran).**
A correct c21 unwind must: (1) resolve c211's dangling `letter_and_spirit_principle`
against c212's provider `L292-425_n002` — the one known real cross-child link, mechanical
because both used the seed name; (2) resolve c212's `authority_levels_hierarchy` ×2 and
`applicable_instructions` ×1 against c211's providers; (3) `chain_of_command` ×3: either
escalate dangling (no child provides it) OR add a structure node spanning the whole span
providing it (the `# The chain of command` heading is L171, untagged; the section as an
arrangement establishes the concept) — both defensible, record which; (4) address all 6
predicted cross-links in cross_link_report; (5) change no child node ids and lose no
child establishes; (6) coverage identity over 171–796. Failure modes to watch:
self-satisfying chain_of_command by pointing at a node that merely mentions it;
deleting danglings; renumbering ids (now prompt-forbidden).

**c21 UNWIND: PASSED the pre-registered key 6/6.** letter_and_spirit link resolved against
a true provider; 14→3 danglings, all mechanical via seed names (incl. n032 the self-report
omitted); chain_of_command ×3 escalated, not self-satisfied; all 6 predictions addressed
incl. 2 honest non-materializations; 0 ids changed, 0 claims lost; identity holds.
Merged: 81 nodes, 64 edges, 7/7 headings.

**⚠️ Flagged judgment call (mine):** the c1 dispatch tells the leaf that a prose run of
level descriptions in stated order IS the ordering and must provide the seed name. This is
the seed protocol, but it pre-answers the leaf's judgment — the root restatement-merge
test therefore tests the MECHANISM, not spontaneous recognition. If we ever want the
spontaneous-recognition number, rerun c1 with the bare seed list.

**⚠️ Test deviation (mine): the c22 self-satisfaction test was NOT run blind.** The
dispatch told the unwinder its authority-provenance prediction was wrong and instructed
escalation. Chosen deliberately: the merged graph is a keepable artifact, and letting a
known-bad link land to preserve test purity trades a real asset for a measurement. The
blind version remains runnable later as a rerun of the c22 unwind from its transcript
state without the warning. What c22's unwind DOES still test blind: whether it invents
merges/structure nodes at 165-node scale, and whether the two seeded resolutions are
performed mechanically.

**Full-tree build-out summary (levels below c2, all Haiku):** 16 leaves + 11 unwinds
completed, 0 unwind failures, all quotes verbatim after repairs, all coverage identities
hold, 2 successful cross-child renames (express_uncertainty→inform_user_of_uncertainty;
transformation_exception→transformation_exception_rule), external danglings surviving
correctly (usage_policies ×3 sites). Recurring defect classes promoted to prompt: seed
self-check, gap arithmetic, seed provenance, contiguous quotes, id stability.

**PRE-REGISTERED: the ROOT unwind key (written before the root unwind ran).**
R1 ⭐ RESTATEMENT MERGE: c1's `L1-170_n028` (prose ordering, spans [69,101]) and c2's
`L171-291_n008` (list ordering, spans [183]+[186,191]) BOTH provide
`authority_levels_hierarchy`. The root must merge them into ONE node whose spans cover
both statements — the design's original motivating structure. Failure: keeping two
providers of one name, or dropping either grounding.
R2: c33's four seeded Under-18 danglings resolve to c2's providers: stay_in_bounds_principles
→ L797-809_n001; sensitive_content_restrictions → c22a2c's provider;
do_not_facilitate_illicit_behavior → c22b1a's provider; self_harm_prohibition → ALIAS of
do_not_encourage_self_harm (c22b1b's provider) — a rename with the alias recorded.
R3: rename candidates needing document-grounded judgment: respect_real_world_ties (c33) vs
c22b2b's real-world-ties provider; avoid_info_hazards (c33, c23) vs c22a2a's info-hazards
provider; conscientious_employee_metaphor (c23) vs c21's letter-and-spirit providers.
R4: chain_of_command danglings (≥4 sites) resolve to c1's provider.
R5 ⭐ the FINAL dangling list is nonempty and every survivor is genuinely external or
underspecified (usage_policies at minimum). A zero-dangling root = over-resolution.
R6: zero child ids changed or deleted; zero establishes lost; coverage identity over
L1-4691.

**Level 3 LEAF c211 (L171–291) — THE K1 RESULT:** n008 = ordering node, spans [183]+[186–191],
full six-level order in establishes, provided under the INHERITED seed name as {name,prose},
10 consumers incl. the L181 rule (K1+K3 by construction). One dangling need =
letter_and_spirit_principle, exactly the link c21 predicted. 18/18 object format, 92/92
coverage, 1/9 quote paraphrase. The motivating case falls out of the architecture.

## ROOT UNWIND — scored against the pre-registered key

R1 ⭐ PASS: authority ordering merged into ONE node, L1-170_n028, spans
[69-101]+[183]+[186-191], 31 consumers. The motivating structure, achieved.
R2 PASS: all 4 Under-18 links resolved incl. the alias (self_harm_prohibition →
do_not_encourage_self_harm, adjudicated from L1611/L4589 with grounds).
R3 PARTIAL: root under-renamed; adjudication bounce resolved 5 more
(letter_and_spirit, transformation_exception, objective_point_of_view,
express_uncertainty, assume_best_intentions ×2); 7 kept dangling on name-level grounds —
contestable; this residue is the golden protocol's adjudication surface.
R4 PASS (after bounce): chain_of_command had NO provider anywhere — real gap; root added
structure node L1-4691_n001_structure spanning [66-67]+[171]; 5 needers resolved.
R5 PASS: final_dangling = 13, nonempty, usage_policies the true external.
R6 PASS: only the R1-merged node retired (recorded); 0 other ids/claims lost;
2/3722 lines unaccounted; 1/302 quotes non-verbatim.

FINDING (systematic): most surviving danglings are SECTION-ANCHOR names — the document
cross-references sections ([?](#anchor)); providers carry concept names. An anchor→concept
mapping table (mechanical, from headings) would close most of the residue and belongs in
the next prompt/pipeline revision.

FINAL: 593 nodes (== the original clause-corpus count), 224 names, 482 edges,
0 bad spans, 18 unwinds with 1 deletion violation (caught by the id-diff, repaired).

## POST-AUDIT STATE (final for this build)
All 16 audit repairs verified applied (one required a re-repair after a false completion
report — caught by string-check, the pattern's Nth confirmation). Final graph: 593 nodes,
482 needs, 3 dangling entries over 2 names (behavioral_principles: structural
self-reference; usage_policies: external URL) — both legitimate. Audit rates: A 80%
faithful (pre-repair), B 93% valid, C adjudications 100% confirmed blind, D 0 dropped.
Defect classes and prompt fixes for the next build recorded in audit/AUDIT_RESULTS.md.

## FIX-VALIDATION SPOT-CHECKS (diagnosis-set per S3 — held-out test = stability rerun)

Five fresh Haiku re-runs of the failing leaves, amended prompt, dispatches free of any
failure hints. Targets scored against the document:
- modal (c23b2, L2580): PASS — "should not" preserved.
- modal (c212b, L483 MIXED-MODAL line): FAIL — "should notify" again became "must notify";
  the rule missed the one-sentence-two-modals case. Prompt sharpened with an explicit
  mixed-modal example; needs re-validation in the stability rerun.
- heading scoping (c32a3): PASS — four section-scoped heading nodes, each rule wired to
  its OWN section's authority node. (Also independently reproduced in c22a2c.)
- false danglings (c22a2c protected_groups; c31c priority names): PASS by dissolution —
  no circular need, zero coined danglings; export mechanism itself not directly exercised.
- REPAIR CORRUPTION FOUND: the earlier n026 modal repair garbled the sentence
  ("...seek approval the user and seek approval") — fix dispatched with verbatim-verify.

## INSTRUMENT FIXES (S8: RED before GREEN)
- merge_check.py built; RED on the historical n028/n008 tier loss (catches "No Authority"),
  and on the post-repair state flags a real residual ("Model Spec" per-tier sourcing) —
  reviewed: covered by c1 per-level nodes, accepted with note.
- LINE-COUNT GROUND TRUTH: the raw file has 4692 lines (final "~~~" without trailing
  newline; wc -l undercounts). graph_check was RIGHT; blind audit D's "L4692 does not
  exist" was WRONG — auditors need verification too. Root division built on 1-4691;
  uncovered entry for L4692 dispatched.

## TRANSLATION SAMPLE RUN (DeepSeek live, 2026-08-10, $0.078 / 42 calls)
15 stratified nodes through unmodified phase_1 translate.py via node_corpus.py
adapter. Result: 2 translated (both near-empty heading/meta modules), 13
unrepaired. CLASSIFICATION (the coupling question): ZERO link-level failures;
all local, and all in the ADAPTER/prompt-shape class: (1) citation contract —
models cite line-ranges from the adapter's SOURCE TEXT instead of the node id
(~14 findings); (2) Sec.19 requires/inputs confusion — the NEEDS preamble names
the names but not the field, and the clause-shaped worked example demonstrates
the wrong mapping for node input (n028's sole standing finding); (3) real
clingo/format errors on rich nodes. No node failed on requires-unprovided
alone (Sec.7 note-trap did not fire). ⇒ The graph's provides-index makes
requires-resolution locally checkable at translation time — the genuinely
link-time residue is only head-shape agreement, mechanical under enforced
canonical names. Next: adapter fixes (cite-the-node-id instruction; NEEDS →
requires-vs-inputs guidance per Sec.19's local criterion), then rerun; a
node-shaped worked example is the watched-prompt change to make only with
this evidence in hand.

## GOLDEN STATUS OF THE GRAPH (answering Matt directly)
Applied & verified: all enumerated audit findings (16 repairs, 9 dangling
resolutions, renames, tier-6, sentence fix, L4692). NOT yet done: sweeping
systematic classes beyond the audit samples (30/593 nodes, 30/~480 edges) —
expected ~6 unsampled modal-class instances. Mechanically sweepable: modal-
diff (establishes vs span text) and heading-prose scope check; then one more
audit round on the post-sweep graph.

## GOLDEN SWEEPS (2026-08-10, post-audit graph -> golden candidate)

Matt's ruling: "we should make it a golden." The two systematic classes the
Fable audit found in-sample were swept over ALL 593 nodes.

Instruments (both RED-verified via --self-test before first use, S8):
- sweep_modals.py  -- modal profile of establishes vs span text
  (strengthened / weakened / flattened). 70 candidates.
- sweep_headings.py -- heading-only nodes asserting section content.
  6 candidates.

Adjudication: 76 candidates + span text -> 4 parallel seats (frontier tier,
blind to sweep provenance beyond the flag kind; imperative-mood carve-out
stated in the brief). Verdicts in adjudication/verdicts_0..3.json:
**40 repair / 36 false_positive.**

Verification before applying (garbled-repair lesson):
- Mechanical: every proposed_establishes re-swept + merge_loss vs the
  original (content-drop check). 38/40 clean; the 2 re-flags
  (L1-170_n026, L527-796_n027) were inspected by hand and are INSTRUMENT
  ARTIFACTS ("prohibited categories" as a category name matches the STRONG
  lexicon; "recommend...should" trips the tier-count heuristic) -- proposals
  faithful, accepted. Recorded in adjudication/DISPOSITION.json.

Applied: all 40 repairs; backup at recurse/root/graph.pre_sweep_2026-08-10.json.
Closed loop: re-sweep of the repaired graph flags EXACTLY the 36 accepted
false positives + the 2 artifacts (38 residual, 0 unexpected, 0 lost).

Two pre-existing mechanical defects also closed while at it:
- L4251-4571_n026 quote made verbatim (was a mid-sentence fragment).
- L424 (closing ~~~ fence of the L410-423 example) added to its owning
  node's span; unaccounted lines now 0.

graph_check on the result: 0 bad ranges, 0 bad quotes, 0 unaccounted,
danglings unchanged (usage_policies external x2, behavioral_principles
structural). **This is the golden candidate.** Remaining known limits:
the 36 adjudicated-keep flags are recorded (not defects); one more
independent audit round on this exact artifact is the optional cap-stone.

## TRANSLATION SAMPLE RERUN (2026-08-10, run 20260810-205513, $0.0723/40 calls)

Control: same 15 nodes, same prompts/model/gates as run 20260810-203553;
ONLY the adapter text changed (cite-the-node-id; NEEDS->requires with the
Sec.19 local criterion and the never-in-both rule). Corpus generated from
the PRE-sweEP graph deliberately, so the diff isolates the adapter.

Result: 3 translated + 1 principled abstention + 11 failed
        (was: 2 translated + 13 failed).

The two targeted classes are GONE:
- citation-wrong-id ("cites 'LN-LN', not a clause in this corpus"):
  ~14 findings -> 0.
- requires/inputs both-fields (n028's standing finding): 1 -> 0. n028 --
  the merged six-tier ordering node, the hardest in the sample -- now
  TRANSLATES (15 ontology entries, attempt 2).

Residual failure surface is entirely GENERIC ASP-craft, nothing
graph-adapter-shaped:
- unsafe variables in ontology atoms (no binding conditions) x~8
- undeclared acts referenced by assertions x2
- rule syntax written into an ontology atom x1
- abstain-with-content / translate-with-nothing confusions x3
- raw clingo syntax errors x3

Reading: the graph->corpus adapter is no longer the bottleneck; the
remaining failures are the same craft errors ordinary clauses can hit,
concentrated because node texts are ~3x clause size and DeepSeek-V4-Flash
is at the small end. Raising the rate from here is prompt-side (the
node-shaped worked example -- a WATCHED-prompt change requiring ceremony,
now with evidence) and/or more repair attempts; not adapter-side.

## NODE-SHAPED WORKED EXAMPLE + TWO STRUCTURAL DISCOVERIES (2026-08-10)

Matt's ruling: replace the clause-shaped worked example entirely for the
graph pipeline. Done WITHOUT touching watched phase_1 prompts:
node_worked_example.md lives in graph_v2 and node_corpus.py swaps it in for
20_worked_example.md in the generated config only. Gate:
test_node_worked_example.py mirrors phase_1/test_prompt_examples.py -- every
good example must pass the REAL stage-2 checks against node_corpus.json
(4 good: the conditional flagship l527_796_n012 with requires+inputs both
populated + repeated-atom alternatives; a heading-authority hollow module; a
document-example prefer module; a clean abstention. 5 bad: this week's
actual failures -- unbound variable, rule-in-atom, undeclared act,
abstain-with-content, citing line markers).

Discovery 1 (via the example gate, would have poisoned the full run):
**graph node ids are not valid ASP constants.** `asserts(L527-796_n012,...)`
parses L as a variable and the hyphen as subtraction -> clingo refuses every
module that has an assert. This is why run 2's only successes were hollow
modules and abstentions. Fix in the adapter: corpus ids are now asp_id()
(l527_796_n012); the graph id stays in `locator`. The graph itself is
unchanged -- but a FUTURE graph build could emit ASP-safe ids directly
(candidate change for the DeepSeek build).

Discovery 2 (from reading run 2's "successes"): l4251_4571_n029's accepted
module contained `"body": "brief_overview(R) ; overloaded_response(R)"` --
the ;-means-AND trap; it validates and can never fire. The worked example's
version fixes it and the trap is taught by the flagship's notes.

Also: recurse_driver.py now sends per-phase json_schema response_format
(DIVISION/LEAF/UNWIND schemas; non-strict; auto-downgrade to json_object if
the endpoint rejects it) -- Matt's format-forcing request for the graph
build. 27/27 driver tests green, incl. new pins: every phase call carries
its schema; downgrade path; span typed [int,int].

Run 3 launched: node example + asp ids, same 15 nodes.

## RUNS 3-5: THE WORKED-EXAMPLE ITERATION LOOP (2026-08-10)

Run 3 (20260810-212409, $0.052): node example + asp ids ->
**10 translated + 1 principled abstention + 4 failed** (from 3+1+11).
Modules now substantive: 1-4 asserts each with declared closures; n028 and
the Under-18 n011 both pass. Residual: 3x acts written in slash notation
(name/arity leaking from requires/inputs into `acts`), 1x undeclared body
predicate.

Fix A (example edit): "slash notation never leaves requires/inputs" note +
bad example 0. Re-gated 10/10.

Run 4 (20260810-213043, $0.059): **5+1+9 -- a REGRESSION, and the failing
set is nearly disjoint from run 3's.** Reading the findings: the lesson
BACKFIRED SIDEWAYS -- acts stopped slashifying, but closure.act_class
started (`apply_default/1`, 5 nodes) and forbid_body.head got full terms.
The schema has THREE notations (name/arity; term; bare functor) and the
lesson taught a binary contrast. Also: n026 truncated (reasoning model,
hidden reasoning bills against max_tokens) and n011 flipped to a
requires-AND-inputs both-fields breach -- evidence of real run-to-run
sampling variance at temperature 0.2, not only prompt effects.

Fix B (example edit): the binary note replaced by a three-notations TABLE
(field -> notation -> the same act spelled all three ways), bad example 0
extended to show the closure.act_class case. Re-gated 10/10.
(A max_tokens "raise" to 4096 was drafted and REVERTED -- phase_1's cap is
already 16384; 4096 would have lowered it.)

Run 5: launched with Fix B.

Standing observation for the harness design: per-node success is partly
stochastic; single-run rate comparisons on 15 nodes carry ~±3 noise. The
honest instrument is the FINDING-CLASS distribution (which classes exist),
not the pass count; class extinction across runs is signal, rate wobble is
not. If a class persists after its lesson, next lever is max_attempts (each
attempt ~$0.001-0.004), not more prose.

Run 5 (20260810-214437, $?): **12 translated + 0 abstained + 3 failed** --
best yet; ZERO notation findings (Fix B held with no new side effects).
Residuals are single-instance craft slips, not classes: one unsafe variable
at solver level (n006), one missing closure declaration (n014), one
reasoning-burn truncation (n007). Graveyard note: the 44-entry cap fired
before this run; all 44 diagnosed with per-entry VERDICT.md files mapped to
the documented classes (no bulk clear -- the mechanism's point was honored).

Wobble worth recording: l1799_1974_n009 (the definitional-analogy node) has
now flipped translate/abstain/translate across runs 2-5, and BOTH outcomes
pass validation. Whether that node should translate is a judgment call the
harness cannot see; candidate for the equivalence protocol's claim-agreement
seat when comparing runs.

Run 6: repair budget raised 3->5 (config-level, adapter-generated; watched
config untouched) on the run-5 evidence that residuals are craft slips
repairable in-band.

Run 6 (20260810-215527, max_attempts 3->5, ceiling ->$1.00): **8+0+7 --
5 attempts did NOT beat run 5's 12/15 at 3 attempts.** The unrepaired nodes
sit at ONE standing finding for 5 rounds: the model re-commits the same slip
instead of applying the feedback. Conclusion: repair budget is not the
lever either; the translation loop is at its single-model plateau
(~8-12/15 per draw, extinct classes stay extinct). The next real levers are
(a) best-of-N sampling per node with the validator as judge, or (b) the
full-cycle gate: accept per-node stochastic failure and re-run failures in
a fresh transcript (the run-to-run disjointness of failures means two
independent runs cover ~15/15 between them). Left max_attempts=5 in the
adapter (harmless; single-run comparison is not evidence either way).

## ADVERSARIAL REVIEW OF TRANSLATION FAILURES (2026-08-10, Matt's request)

Clean-context reviewer, artifacts only (transcripts of runs 5-6 failures +
prompt files + adapter; my analyses withheld). Report:
adversarial_review_translation.md. Five findings; per the validate-first
rule each was verified against code/behavior before anything was applied:

- F1 CONFIRMED (measured: 6 planted defects -> 2 findings/round). Repair is
  drip-fed because pydantic surfaces one failure per validator chain and
  Module._coherent only runs once sub-models validate. PARTIALLY DEFERRED:
  validate_all's docstring records this scope as deliberate (fabricated
  findings on half-validated values were considered and REJECTED), so the
  full collect-then-raise refactor is a design decision for Matt, not an
  autonomous fix.
- F2 CONFIRMED + FIXED (walkthrough/link.py CLINGO_ERR): clingo `note:`
  lines (the actual diagnosis, e.g. "'A' is unsafe") are now captured into
  the finding alongside the error line.
- F3 CONFIRMED + FIXED (schema.py _check_head_bound): a head variable the
  body never mentions now gets the GOOD unsafe-variable message at schema
  level instead of dying later as a truncated clingo error. Scoped to
  plain-literal bodies -- on aggregates/intervals/assignments/strings the
  module level must not play solver (test_no_construct_is_refused_at_
  module_level is a named contract and stays green).
- F5a CONFIRMED + FIXED: the two misleading messages rewritten (read_back
  slot mismatch now states the fix; undeclared-name now says a `concepts`
  entry does not count as declaration).
- F5b CONFIRMED + FIXED: `concepts[].cites` is now corpus-checked (the
  "L-72" fabrication class), and clause_id identity is checked on the RAW
  dict so it fires even when field breaches stand (the l810_896_n014
  self-rename ran 5 rounds unchallenged before).
- F4 DEFERRED TO MATT (watched prompts): 00_task.md rule 10's
  "include arity everywhere" induces `assistant/1` as a concept NAME
  (8 breaches over two nodes), and forbid_body is demonstrated nowhere
  while its field descriptions contradict the validator. Both are
  phase_1/prompt edits = ceremony.

phase_1 suite after fixes: 737 passed, 1 xfailed (two false-positive rounds
during development were caught by the suite's own pins -- the empty-body
precedence and the no-construct-refusal contract -- and the fix was scoped
accordingly).

## DISPATCH PROBES: DEEPSEEK VS THE HAIKU TREE (2026-08-10, Matt's design)

probe_node.py replays a stored dispatch (input reconstructed from the tree
exactly as Driver.build threads it; expected = the stored artifact) against
DeepSeek N times, single-shot, name-free comparison. $0.042 total.

**c1 Phase L (span 1-170, 11 seeds, n=3):**
- Boundary agreement with Haiku is STRIKING: 42-45 of 46 expected node
  starts appear within +-1 line in every sample. The models see the same
  seams.
- Granularity differs 1.5-2.4x: 70/94/112 nodes vs Haiku's 46. The
  equivalence protocol's split/join tolerance exists for exactly this.
- 1/3 samples fully valid; the other two failed ONLY on quote-not-verbatim
  (the class the driver's repair loop historically clears: c1 Haiku went
  25/40 -> 0 under repair).
- Reasoning burn at leaf scale: negligible (calls fast and cheap).

**root Phase D (span 1-4692, n=2): the protocol does NOT transfer at
root scale on first attempt.**
- Sample 0: 47 children, some spans FABRICATED past the document end.
- Sample 1: 191 micro-children that stop at line 406 (gave up mid-list).
- Both caught by validate_division ("need 2-3 children..."), so the driver
  would bounce them into repair -- but 0/2 first-attempt compliance vs
  Haiku's stable 3-child behavior is a real distribution difference, found
  for four cents before any full-tree run.
- FIX APPLIED: DIVISION_SCHEMA children now carries minItems 2 / maxItems 3
  -- the cardinality the prose failed to convey is now in the grammar the
  format forcing sends (pin: test_division_schema_states_the_child_
  cardinality). 28/28 driver tests green.
- Also learned: root-scale dispatches engage heavy hidden reasoning (~20K+
  CoT tokens billed as output; format forcing exempts the reasoning
  channel), so the full build needs max_tokens >= 32K and ~10-min patience
  for the top few dispatches; leaf-scale calls show no such burn.

Haiku reference distribution (3 subagent replays of the same root
dispatch): IN FLIGHT.

## ROOT PROBE ROUND 2 + HAIKU REFERENCE DISTRIBUTION (2026-08-10)

Haiku reference (3 subagent replays of the identical root dispatch), with
the original build as a 4th draw: **3 children in 4/4**; cuts wobble
(170/177/2125 for the first, 806/2125/3147 for the rest; 3147 recurs 3/4).
Haiku varies WHERE, never HOW MANY.

DeepSeek re-probe after the two fixes (children minItems2/maxItems3 in the
DIVISION_SCHEMA grammar + the 2-3 rule restated in the dispatch text):
- cardinality violations GONE (was 47 and 191 children; now 3 and 3).
- sample 1: first cut 170 -- EXACTLY the original build's. Second cut 340
  differs, but Haiku's own second cut ranges over 806-3147, so DeepSeek now
  sits at the edge of the reference wobble, not outside the protocol.
  Residual errors mechanical (0-indexed span; coverage stopped at 510) --
  repair-round territory.
- sample 0 found a DRIVER HOLE instead: declared the whole 4692-line span
  "leaf" and validated CLEAN. Fixed: validate_division now rejects a leaf
  declaration on any span over 2x leaf_max (pin:
  test_whole_document_leaf_dodge_is_RED). 29/29 driver tests green.

Reading (Matt's hypothesis confirmed): the root-scale deviation was PROMPT
TRANSFER, not capability -- moving the rule from the long brief into the
grammar + dispatch line eliminated it in one step. Remaining DeepSeek root
behavior (cut placement, mechanical span slips) is inside or near Haiku's
own run-to-run distribution and inside the repair loop's reach.

Also: Matt's watched-prompt authorization executed -- 00_task.md rule 10
now scopes /arity notation to references (concepts name / acts / closure /
forbid_body slots excluded, the `assistant/1` class); forbid_body field
descriptions state the bare-name contract; node_worked_example.md flagship
now demonstrates forbid_body populated ({permit, best_intentions_bias})
with a when-to-use note. Example gate 10/10; phase_1 suite 737 passed.

## GO DECISION + FULL DEEPSEEK BUILD LAUNCH (2026-08-10, Matt AFK)

Matt's checklist before launch, and how each was met:
1. Spot-check sufficiency: all THREE phases now live-probed.
   - Phase D root: cardinality fixed by grammar+dispatch (3/3 children;
     one cut == the Haiku original's 170).
   - Phase L (c1): 42-45/46 boundary agreement, quote errors repairable.
   - Phase U (c21, the previously-untested surface): DeepSeek produced
     82 nodes vs Haiku's 81, needs 64=64, IDENTICAL dangling set, and made
     the same cross-child rename (chain_of_command ->
     authority_levels_hierarchy). Live cache measurement: 87% prompt-token
     hit rate (13,952/16,098) -- the byte-identical-brief design works.
2. Auto-fix built in: (a) in-loop -- multi-round ACCUMULATING repair
   (cfg max_repairs, default 2) replacing the single retry; every phase
   reply schema-forced; (b) post-build -- graph_check + both sweeps run
   automatically on the finished graph, reports into the run dir
   (post_build_checks; sweeps parametrized by --graph/--report).
3. New pins this session: caching (byte-identical system prompt across all
   phases + tally reads real cached counts), 2-3 child cardinality in the
   schema, whole-document leaf-dodge rejection. Driver suite: 31 passed.
4. Ops fixes found by dry-fire: driver key resolution (sys.path to
   providers.py's rc parser), max_tokens 32768 (U/root reasoning burn;
   truncation is stochastic and absorbed by repair+resume).

Launched: recurse_driver.py --yes --out runs/ds1
  plan: 4692 lines, leaf_max 300, ~64 calls; expected ~$0.19,
  worst-case ~$1.12, measured-spend ceiling $2.00. Resumable at every
  tree node; on abort, rerunning the same command continues.

In parallel: translation run 7 (20260810-225427) is measuring the
collect-then-raise multi-finding feedback (Matt's test) -- scored when it
lands. Note Matt's standing prereq: node translation error-free before the
graph pipeline is USED downstream; the build tonight produces the graph +
auto-check reports either way.

Run 7 (20260810-234100, collect-then-raise live): **8+1+6.** The
what-would-change-our-minds test comes back NEUTRAL-TO-POSITIVE: several
nodes fixed multi-item finding lists in one round (attempt-2 successes),
convergence did not collapse -> the refactor stays. One thrash case
(n011, 14 findings standing all 5 rounds) noted as the failure shape to
watch. One truncation (l527_796_n022): translate.py has NO
resample-on-truncation (the graph driver now does); candidate port.
Plateau holds at 8-12/15 per draw -- per-node stochasticity, not classes.
The graph BUILD (runs/ds1) proceeds independently; Matt's prereq gates
downstream USE of the graph, not its construction.

## THE DEGENERATE-LEAF POSTMORTEM + GOLDEN-FREE DETECTION (2026-08-11)

Root cause of the overnight stall and the "13x c2": ONE leaf reply carried
**969 byte-identical copies of a single node** under distinct ids -- a
decoding loop, not fragmentation -- and every id-based validator passed it.
Its bulk then flowed up two unwinds (c2/c3, c2). Second real defect: the
banked c1 leaf extracted ZERO needs (linkage did not transfer on that
draw). Runaway 128K draws on later leaves were the same loop hitting the
token cap instead of finishing.

Fixes (all pinned, 35/35 driver tests):
- dedupe_nodes: exact-duplicate removal as a SAFE autofix inside
  validate_leaf (identical content cannot lose information).
- LEAF_DENSITY_MAX band (0.7 nodes/line, ~2x healthy top) for
  non-identical spam.
- RECURSE_PROMPT.md granularity section (one claim per node, 1 per 3-5
  content lines, never repeat a node) -- prompt-side so any model gets it.
- Driver health telemetry (Matt's Q3): per-artifact rows in
  <out>/health.jsonl {density, needs, autofixes} with immediate warnings on
  zero-needs-in-large-span and density-over-band. ALL of tonight's damage
  was detectable without a golden: 5.3 nodes/line, 969 dups, needs=0 are
  absolute signals. For new documents these bands are the early-warning.
- smoke_granularity.py: replays the two failure dispatches against ANY
  openai-compatible model with absolute-band verdicts -- the portability
  smoke test for prompt-customization decisions.
- BATCH_DESIGN.md: BFS-layered batch execution design for build +
  translation (Matt's item 2).

Salvage instead of rebuild: banked ds1 tree migrated to runs/ds2 with
duplicates removed (c2: 1098 -> 130 nodes vs golden 83 -- split/join band)
and an explicit run_meta migration note; build resumed on ds2.
Aggregate spend to date logged at $1.57 pre-salvage; $3.00 tripwire armed.

## TOKEN FORENSICS (2026-08-11, Matt's request) + CORRECTION

token_forensics.md (subagent, quantitative). Headline: **no hidden
reasoning channel** -- billed completion ~= visible text, reasoning_tokens
null. My earlier "hidden CoT burn" reading of the long draws was WRONG;
the burn is all visible content, in three sinks:
- duplicate-node repetition: 97.6% of the 381K-char failed reply (the 969x
  loop) -- already fixed (dedupe + granularity rule, verified by smoke A);
- judgment_calls narration: 93.8% of the unwind reply -- 222 entries, 220
  narrating the SAME rename once per needer, duplicating `resolutions`.
  The brief's "mandatory everywhere" mandate implicated;
- uncovered as per-line entries: 29% of the pathological leaf.

Fixes applied: RECURSE_PROMPT.md "Output economy" section (judgment_calls
records decision CLASSES, ~10 max; uncovered uses ranges); ds2 restamped
(migration2), build bounced to pick it up BEFORE the remaining unwinds
(root unwind with 500+ summaries was the at-risk dispatch). Also new:
per_dispatch_usd budget ($0.30) in the driver, pinned.

Smoke verification on DeepSeek (probes/smoke_DeepSeek-V4-Flash-0731):
dispatch A (the 969-dup leaf): FIXED -- 2/2 draws, 0 dups, density 0.21,
needs 41-52, all bands PASS. Dispatch B (c1): still truncates at the 32K
smoke cap -> c1 is a prompt-shape problem (front-matter density), being
re-drawn in the build at 128K; leaf-splitting DEMOTED from "natural
escalation" (Matt's challenge upheld by the evidence).

## RULINGS + DETERMINIZATION WAVE (2026-08-11)

Matt's rulings: (a) uncovered-derivation QUEUED to ds3 (ds2 stays a
two-migration artifact; third migration rejected to preserve
interpretability); (b) batch design approved as: shared core
(DispatchState + scheduler + in-flight manifest) + concurrent executor +
$0.05 SLA probe FIRST; batch executor contingent on the probe. Execution
mode is config-selected (service/model dependent). (c) Golden protocol:
deterministic dominant, LLM as fallback catch surface.

Determinizations shipped:
- modal_repair.py: sweep -> auto-clear (imperative carve-out) -> TEMPLATED
  directional repairs (span's own modal substituted, mechanically gated) ->
  seats only for flattened/fallthrough. RED self-test 3/3. Note: runs on
  PRE-adjudication reports only; adjudication outranks the template.
- Queued for ds3: uncovered derived in code (kills the gap-arithmetic
  class); rename pre-matching in unwind prompts (prose-token overlap
  ranking, model confirms).

Reviews in flight (completed-and-stable work): instruments
(graph_compare + modal_repair) and driver autofix layer + GOLDEN_PROTOCOL
accuracy. graph_compare landed earlier: self-compare 593/593 1:1, edge
recall/precision 1.0, planted-mutation RED test sensitive (blinding a
matcher fails it).

Batch API mechanics captured (docs): files/upload (purpose=batch-api) ->
POST /v1/batches -> poll status enum -> output file JSONL by custom_id;
50K req/100MB caps; "small batches typically finish in minutes"; 50%
discount on SELECTED models (eligibility of ours = probe question).
sla_probe.py launched.

## BATCH SLA PROBE RESULT (2026-08-11)

One-request batch on deepseek-ai/DeepSeek-V4-Flash-0731 via the real Batch
API (files/upload -> /v1/batches -> poll): **62 seconds submit-to-complete**
(VALIDATING+IN_PROGRESS ~60s, then COMPLETED with output file). Model is
batch-ELIGIBLE. Implementation note: together's WAF 403s stdlib-urllib on
the batch endpoints while accepting curl -- the batch executor must set a
browser-ish UA or shell to curl.
Verdict for the executor decision: turnaround is minutes-scale even for
tiny jobs, so batched repair ROUNDS are viable, and the batch executor
clears its gate. Build order stays: shared core -> concurrent executor ->
batch executor.

## REVIEW WAVE CLOSED (2026-08-11)

Both stability reviews were POSITIVE and both are now resolved:
- instruments_review.md: modal_repair fixed by hand (MR-1 polarity
  inversion via negation-blind regexes -- both directions; MR-2 mixed-span
  auto-clear narrowed to pure-imperative; MR-3 quoted-example spans routed
  to seats; 6/6 pins incl. the three review regressions). graph_compare
  fixed by agent per review-as-spec: similarity-scored tie-breaking (GC-1),
  Matt's class2 ruling (identical-normalized establishes auto-agree, all
  else queued, modal prefilter orders not gates -- alternative rejected by
  name) (GC-2), strict+permissive edge metrics with shadowed-edge
  disclosure (GC-3), subset-search grouping (GC-4), augmenting-path maximum
  matching (GC-5), class-4 queueing (GC-6), de-circularized RED test
  (GC-8). 7 tests; golden self-compare perfect incl. strict metrics.
- driver_layer_review.md: F1 self-merge, F2 lowercase-claim floor in
  merge_loss, F3a out-of-span coined seeds, F4 duplicate structure nodes,
  F5 self-satisfying resolutions, F6 unwind health rows, F7 cross-link
  index range, F8 large-gap marker -- all guarded, 37/37 driver pins.
  (Lesson re-learned mid-wave: a patch script that dies after printing
  its intent but before writing leaves pins testing nothing -- the write
  now precedes the celebration.)
- GOLDEN_PROTOCOL.md corrected per G1-G4 (provenance honesty, the
  pre-registered unwind keys restored to the procedure, the closed-loop
  pass rule fixed to include instrument artifacts, the unpackaged-script
  caveat).

Build: c1 redraw SUCCEEDED (42 nodes, 16 needs vs the discarded zero-needs
draw); tree at 17 artifacts, deep in c3; healths in-band.

## SHARED EXECUTION CORE LANDED (2026-08-11)

dispatch_core.py + test_dispatch_core.py + minimal --exec-mode integration
(default serial path byte-untouched). Verified myself: 53 tests green
(37 driver + 16 core). Equivalence: serial-through-core build is
byte-identical to Driver.build on the mock e2e, INCLUDING the exact
prompt-byte sequence; concurrent and batch e2e byte-match the serial
reference. F1-F5 addressed as specified (state machine, sweep-don't-
resubmit manifest, split-to-fit submit gate, per-request bodies, data-
shaped taxonomy with requeue-live). Known honest caveat recorded by the
implementer: batch-mode truncated rows requeue as fresh draws rather than
transcript-restarts (matches the serial ladder's observable behavior).
Adversarial review of the core dispatched (required before it spends live
money); head-to-head (concurrent vs batch on real dispatches) gated on
that review.

Build: the L1542-1800 leaf has now failed quote-verbatim twice (4 rounds
each); relaunched once more -- on a third failure the play is DIAGNOSIS of
the exact quote mismatch (likely markdown-normalisation in that span),
not more draws. Aggregate spend $2.09 (tripwire $3.00).

## DISPATCH CORE: REVIEW CYCLE CLOSED (2026-08-11)

dispatch_core_review.md was positive ("do not spend yet"): four money-path
defects (R1 budget blind to billed failed draws; R2/R3 manifest kill
windows; R4 submit-gate overcommit across in-flight jobs; R5 collected
results discarded on mid-loop raise) -- every one living exactly where the
equivalence tests substituted fakes. All fixed per findings-as-spec, plus
R6-R10 lower-severity items; 11 new pins from the review's own suggested
list (kill sims, bills-then-raises clients, two-flush overcommit).
Suite: 64 tests green, byte-equivalence pins unchanged. The core is now
CLEARED for live spend.

Head-to-head (concurrent vs batch) deliberately HELD until the ds2 build
completes: shares the wire and the spend aggregate ($2.09 of the $3.00
tripwire), and a clean comparison wants an idle provider path. Plan: fixed
dispatch slice, both modes, fresh stated budget, scored on wall-clock /
error rate / cost incl. cache delta.

## DS3 FEATURES LANDED + PROMPT-DRIFT LESSON (2026-08-11)

Both determinizations are in behind default-off flags with flag-off
byte-identity pins (43 driver tests): derive_uncovered (coverage complement
computed in code, formatting runs auto-labeled, content-line residue gets a
cover-or-explain error -- the coverage-identity failure class cannot fire
when on) and rename_candidates (top-3 prose-overlap candidates per
dangling, code-ranked, model confirms on MEANING). ds2 restamped
(migration3, flag-gated brief addition, inert).

Drift lesson: the quote-honesty sentence I added to Driver.leaf while the
core agent worked left dispatch_core's copied prompt literal stale -- the
core's own prompt-byte pin caught it (exactly what it exists for). My
regex "sync" then overwrote the WRONG literal (Phase D's) -- caught by the
same pin again. Hand-restored both; 70/70 green. Standing note: the
prompt literals exist in TWO files; any Driver extra edit must touch both,
and the byte pin is the enforcement.

Early ds2 quality signal (free, banked subtrees): 6 modal flags / 172
nodes (3.5%) and 0 heading flags -- vs the Haiku golden's PRE-repair
70/593 (11.8%). The upgraded brief generates more modally-faithful
establishes on DeepSeek than the original did on Haiku.


Mid-ds2 config flip: derive_uncovered=true (see driver_config note) -- the
L1542-1800 leaf's post-quote-rule failure mode (under-reported uncovered)
is impossible under derivation. Config-level, brief untouched, no restamp
needed. ds2 is now heterogeneous in uncovered PROVENANCE (model-emitted
early, derived late) with identical artifact shape.

## TRANSLATE_EXEC LANDED (2026-08-11)

translate_exec.py + 8 tests: opt-in concurrent/batch translation through
dispatch_core. Design note worth keeping: ClauseState runs translate.py's
OWN repair_loop on a private thread against a shim model that parks each
request for the executor -- repair semantics exist in exactly one place in
all three modes. Equivalence: concurrent and batch byte-identical to
serial on every deterministic artifact incl. ledger call counts and spend,
on 5-clause fakes with a repair case. Mixed-round batch pin passes (one
job carrying clause-A attempt-1 + clause-B round-2). Verified: 95 tests
green across graph_v2 + phase_1 suite 737 unbroken.
Pending before translate_exec spends live money: its own adversarial pass
(the shim/threading surface is new; the core beneath is already reviewed),
scheduled with the head-to-head.


HUMAN INTERVENTION on ds2/c3/c1/c3: the [1542,1800] span split at the
L1708 heading via artifact edit (999-dup + fabricated-quote meltdown on
6+ draws; buying more draws rejected). Backup kept; logged in the
artifact's judgment_calls. Precedent: the c32 deletion restoration in the
original build.


MELTDOWN ROOT CAUSE (probe, 4 conditions, $0.019): MY quote-honesty rule
was the trigger on the link-dense span -- WITH rule: truncation loop;
WITHOUT: healthy 37-node reply; quotes-forbidden: loop-free but degraded;
temp0: empty. The threat phrasing ('fabrication and is rejected') loops
the model on spans where exact copying is hard. Rule SOFTENED to a plain
conditional (permission without threat) in both prompt literals. Full
analyst report pending (meltdown_analysis.md).

## MELTDOWN ROOT CAUSE, COMPLETE (2026-08-11)

Two composing mechanisms, both from Matt-requested analyses:
1. FABRICATION (analyst, meltdown_analysis.md, primary): mid-sentence
   LOAD-BEARING [?](#anchor) cross-refs -- the model quotes verbatim up to
   the ref then substitutes the ref's remembered target prose. The healthy
   1101-1400 leaf's refs were parenthetical; this span's are grammatical.
2. LOOP (probe + analyst): an unpenalized-repetition attractor that
   persists only while BOTH exits are validator-blocked (quote ->
   "fabrication rejected" threat; omit -> coverage failure), amplified by
   my threat-phrased quote rule (probe: WITH rule = truncation loop,
   WITHOUT = healthy 37 nodes) and 131K max_tokens headroom. Same loop
   shape fired on non-safety spans; safety content flavors, not causes.

Fixes shipped (all dispatch/validator-side, both prompt literals):
- threat rule -> plain conditional (permission without threat);
- quotes may never span a [?](#...) ref (fragment-or-omit);
- repair feedback now SHOWS THE ACTUAL LINE TEXT (the model cannot copy
  what it cannot see -- analyst's sharpest observation);
- both loop exits already open (softened rule + derive_uncovered).
The hand-split of [1542,1800] stays for ds2 (geometry only); with these
fixes a future build should clear such spans unaided -- the ds3 stability
run is the held-out test.

Budget: Matt raised the aggregate tripwire to $6.00 ("additional $3 for
the remaining work"); monitors updated.

## DS2 BUILD COMPLETE + GOLDEN COMPARISON (2026-08-11)

**The DeepSeek build finished end-to-end**: 745 nodes, root unwind done,
72% cache hit rate on the final resume leg. Post-build checks (automatic):
0 bad ranges, 0 bad quotes (405 quotes!), modal sweep 36/745 = 4.8%
flagged (golden pre-repair: 11.8%), heading sweep 1 flag. The final
blockers each became permanent guards (example-dialogue hint; F5
self-satisfy -> autofix-drop after the model proposed it 4 straight
rounds).

graph_compare vs golden (pre-registered protocol, descriptive):
- Alignment: 478 1:1 + 21 split/join = 84% of golden mass aligned;
  ds2's extra granularity leaves 238 of its 745 misaligned.
- EDGES (the load-bearing dimension): permissive recall 0.32 /
  precision 0.41; strict 0.20/0.25. Danglings 19 (golden: 2).
  The skeleton matches; the LINKAGE is substantially thinner --
  the c1 zero-needs incident writ large: DeepSeek under-extracts
  needs/provides and the unwinds resolve fewer cross-references.
- Queues for the verdict path: 1258 adjudication, 469 class2, 200 modal
  (verdict = judgment-backed zero; sampling required, not bulk seats).

Reading: NOT equivalent under the protocol as-is; divergence is
CONCENTRATED in linkage extraction, not in boundaries (which are
excellent) or modality (which is better than golden pre-repair). The
targeted lever for ds3 is needs/provides emphasis in the brief + the
rename_candidates flag (built, off) for unwind resolution.

## MATT'S ARCHITECTURE RESTORED + DS3 LAUNCHED (2026-08-11)

Accountability answer, recorded: the driver's single-completion phases were
MY design substitution when porting from the subagent build -- I judged
"division fed back as data" informationally equivalent to "the divider
instance performs the unwind" and optimized for prefix-cache cost without
flagging the substitution against Matt's stated architecture ("the same
transcript that does the splitting also does the linking"). The ds2
linkage gap (edge recall 0.32) is evidence the substitution was NOT
behaviorally equivalent. Restored: transcript_continuity flag -- the
unwind reconstructs [D-user, D-reply, U-user] deterministically; the
prefix cache already holds brief+D-user from the divide call, so Matt's
"identical starting prompts for cost reasons" holds too. Pinned.

rename_candidates: validated against the golden's 479 known edges -- the
lexical top-3 contains the true provider 89% (median rank 1) but MISSES
~1 in 10 (worst rank 223), and post-resolution prose makes 89% an
overestimate. Matt's ruling: ds3 runs continuity ALONE (candidates OFF)
to isolate effects; candidates re-enter later only as a warned attention
aid, never a filter.

Translation continuity: translate.py's repair loop genuinely accumulates
one transcript per clause (verified in run artifacts' transcript.json --
real multi-turn, not pretense).

ds3 LAUNCHED: fresh full build, transcript_continuity=true,
rename_candidates=false, linkage brief section active, all guards +
autofixes + grammar caps from the ds2 campaign. Scored via graph_compare
vs golden on completion; the key metric is EDGE RECALL vs ds2's 0.32.

## DS3 COMPLETE + VERDICT (2026-08-11)

Build: 804 nodes, mechanically immaculate (0 bad ranges, 0/475 bad quotes,
modal 4.1%, 1 heading flag). Fresh full build under: transcript
continuity, linkage brief, candidates OFF, derive_uncovered, all guards.

vs golden (pre-registered comparator):
- Alignment: 499 1:1 + 19 s/j = 87% of golden mass (ds2: 84%);
  misaligned 94 -> 75.
- EXTRACTION: FIXED. 754 needs, 0.94/node (ds2 0.61; golden 0.81);
  748 edges asserted (ds2 420; golden 512).
- Edge recall vs golden: 0.3164 -- IDENTICAL to ds2 (likely the seeded
  easy-subset both recover); precision 0.30 (down, from asserting more);
  danglings 37; ds3 shadowed edges 245 (granularity-driven measurement
  artifacts inflate apparent divergence).

READING: the campaign fixed extraction volume and density, and the final
unwinds now complete (the wrong-name abort class stopped). But agreement
with the GOLDEN's edge set did not move: the divergence changed shape from
"too few edges" to "DIFFERENT edges". Whether different means WRONG is
precisely what the protocol reserves for seats: sample the 1654-item
adjudication queue (~30 items, blind, golden-vs-ds3 edge pairs against
the document) before any further prompt iteration. If sampled ds3 edges
adjudicate as legitimate alternative factoring, the equivalence question
becomes a naming/granularity normalization problem, not a quality one.

## EDGE ADJUDICATION VERDICT (2026-08-11, two blind frontier seats)

30 stratified blind items, inter-seat agreement 24/30.
- ds3-only edges: 9/13 supported by consensus, 1 unsupported, 3 split.
  DeepSeek's "different" edges are overwhelmingly REAL dependencies --
  legitimate alternative factoring, NOT fabrication.
- golden-only edges: 10/13 supported. ds3's recall gap is also real --
  it genuinely misses real linkage the golden captured.
- Calibration greens: only 2/4 clean-supported -- the calibration
  construction (name-matched provider fallback) was weak, not
  necessarily the seats; noted as a caveat on absolute rates, though the
  ds3-vs-golden CONTRAST stands (both strata judged by the same seats).

CONCLUSION: the two graphs factor the document's dependency structure
DIFFERENTLY and both factorings are largely document-supported. Identical-
edge-set equivalence is the wrong frame (the protocol's own caution);
the open decision is Matt's: accept ds3 as the DeepSeek production graph
(running ITS OWN golden-protocol pass on its 33 modal flags + seat queue),
or reconcile toward a union graph. Either unblocks the steps-1-4 sequence.
Campaign spend: $3.26 of $6.00.

## DIVERGENCE MECHANISM IDENTIFIED (2026-08-11, analyst on adjudicated cases)

edge_divergence_analysis.md. Matt's question answered: the divergence is
(b) DIVERGENT-BUT-DEFENSIBLE ATTACHMENT JUDGMENTS on the same
dependencies, not missing knowledge. Numbers: ~53% of the 876 unmatched
edges have a same-prose counterpart attached to a different node pair
(77% for ds3-only); ONE edge class -- section-authority plumbing -- is
~47% of ALL divergence (both graphs draw "heading authority=X leans on
the L67-101 definitions" but instantiate over different heading subsets
with different routing: ds3 per-section hubs vs golden shared providers).
Granularity swallowing only ~8%. ds3's 119 danglings are STATED
dependencies whose names never resolved (E07 radicalization->extremism:
edge written, name unresolved, edge vanished) -- the resolution half
remains real. True disagreement is far smaller than recall 0.32 implied.

Actionables: (1) canonicalize the authority-edge attachment convention
(prompt-side) or collapse the class in comparator scoring; (2) force
dangling-need resolution (the 119 are written-but-unresolved -- exactly
where candidates-as-attention-aid or a dedicated resolution pass
re-enters). Together ~half the measured divergence.

## HEAD-TO-HEAD COMPLETE (2026-08-11, identical fixtures, current code)

Both modes finished the identical replay (c3/c2 subtree + dependent
unwinds incl. root) with ZERO failures -- the size contract + per-phase
caps held; no decision-failure retries needed in either mode.

| mode                    | wall  | calls | measured cost | cache hit |
|-------------------------|-------|-------|---------------|-----------|
| concurrent (n=4)        | 322s  | 10    | $0.0711       | 43%       |
| batch (min_pending=3)   | 459s  | 11    | $0.0945       | 57%       |

Concurrent: 1.4x faster wall-clock, 25% cheaper AT LIST RATES. Caveat
that decides the real ranking: our ledger prices batch rows at LIST; if
together's 50% batch discount applies to this model (their docs say
"selected models"), batch's true cost is ~$0.047 -- cheaper than
concurrent. That is verifiable only on the together billing dashboard
(Matt's side), not from our ledger.

Recommendation: concurrent as the default for interactive/small runs
(faster, simpler); batch for large unattended volume IF the dashboard
confirms the discount -- exactly the service/model-dependent config
choice Matt's ruling anticipated. Both modes are now proven reliable
end-to-end under the full guard stack.

## BOTH DIVERGENCE FIXES VERIFIED (2026-08-11, $0.018 total)

1. RESOLUTION PASS v2: **115 of 119 danglings resolved** ($0.007). v1's
   null confirmed as the contract conflict (the unwind's anti-grind text
   suppressed resolution); the dedicated pass -- "your ONLY job is
   resolving these", candidates attached, rename-on-meaning -- resolved
   115/119 with 4 correctly dropped (self-satisfy class). Systematic
   renames surfaced (default_instruction -> guideline_instruction xN).
   Resolution-as-dedicated-post-build-pass is VALIDATED; the resolved
   pairs should get a blind-seat sample before golden-grade acceptance.
2. AUTHORITY CONVENTION: **4/4 draws PASS at fraction 1.0** on both
   heading-dense spans ($0.011) -- with the convention paragraph in the
   dispatch, every heading-authority node carried canonical
   authority-level needs. Scorer self-test asymmetry (golden PASS / ds3
   FAIL) held before any spend.

Together these address the two mechanisms that explained ~half the
golden-vs-ds3 divergence, verified without any full rerun. Next build
(or a ds3 post-pass) inherits both: convention paragraph -> leaf_extra;
resolution pass -> post-build stage after graph completion.

Commit status: full campaign staged; commit BLOCKED by the design-review
guard on 4 watched files pending Matt's document review (his call).


Batch is now the DEFAULT execution mode (Matt confirmed the 50% DeepSeek
discount on together): true cost ~$0.047 vs concurrent's $0.071 on the
identical fixture; concurrent remains one flag away for hurried runs.
Both verified fixes are permanently integrated: the authority convention
in the shared leaf extra and the resolution pass as an automatic
post-build stage (78 tests green, both pinned).

## MATT'S RULINGS (2026-08-11, six-item decision list)

1. Watched-file review: TBD (traveling). Commit remains staged/blocked.
2. D5 RULING: continuity replays the POST-AUTOFIX division as the
   assistant's prior turn. Ground: the autofixed division is what the tree
   USED; replaying the raw reply would give the instance a memory the
   artifacts contradict. REJECTED BY NAME: store-and-replay raw replies
   (higher verbal fidelity, memory-vs-artifact divergence). Matt's caveat
   recorded verbatim in spirit: not clearly the best approach; not worth
   exhaustive testing now.
3. D6 APPROVED WITH VALIDATION DEMANDED, and Matt's question exposes a
   REAL WEDGE: cap-overflow-means-divide-further has two dead ends --
   (a) spans <= leaf_max NEVER divide (build sends them straight to
   Phase L; no divide option exists), so a dense 300-line span needing
   >24K output is unbuildable; (b) DEPTH_MAX=8 stops division regardless.
   PLANNED MECHANISM (after the in-flight core fix lands, to avoid file
   collision): on truncation-at-cap with otherwise-clean draws, the driver
   mechanically BISECTS the span at the best formatting boundary and
   treats it as a planted 2-child division (mechanical concatenation
   unwind) -- leaf-splitting returns, now with the diagnosis-gated trigger
   Matt originally required. Pin required before use.
4. pipeline.md link-tolerance paragraph INSERTED (marked pending Matt's
   full-doc review).
5+6. Production-graph choice and translation acceptance policy: DEFERRED
   (no downstream consumer needs either today; ds4 and run 8 will inform
   both). Reason-not-to-defer check: none found.

## DS4 COMPLETE -- THE INTEGRATED BUILD (2026-08-12)

The enforced-grammar shakeout (8 attempts, each failure one pinned class:
lawful field omission, null-finish_reason truncation masking, admonition
markers, example-markup tags, F17 carriage, tiny-residue containment)
ended in a build that is operationally the best of the campaign:
- 780 nodes in 302s / $0.148, batch mode, 28% cache.
- RESOLUTION PASS FIRED AUTOMATICALLY: 150/155 danglings resolved ->
  **5 final danglings** (golden: 2-3; ds3 had 119 pre-pass, 37 post-hoc).
- needs 1.10/node (golden 0.81); mechanically immaculate (0 bad ranges,
  0/394 bad quotes); modal 5.3%, heading 1.
vs golden: alignment best yet (506 1:1, misaligned 68); edge recall 0.346
(ds2/ds3: 0.316), precision 0.257 with 970 edges asserted, shadowed_b 336.

READING: the authority convention + resolution pass made ds4 the
strongest PRODUCTION graph (dense, connected, self-repaired, cheap) but
golden-edge-set recall barely moved -- consistent with the adjudicated
conclusion that the two graphs are legitimately different factorings and
edge-set identity is the wrong convergence target. Equivalence judgment
belongs to the protocol's seat path + class-collapsed scoring, not raw
recall. Recommendation: accept ds4 as the DeepSeek production graph and
proceed to run 8 / steps 1-4 small corpus against its nodes.
Campaign spend: ~$4.6 of $6.00.

## PRE-RUN REVIEW: GO WITH CONDITIONS (2026-08-12) + READBACK SMOKE

prerun_review.md verdict GO. Applied: F1 (attribute-carrying markup tags
-- the LAST dialect per the reviewer's document enumeration -- pinned);
F3 aggregate unclaimed-content telemetry (per-leaf cap stands; ds4 actual
total was 2; abuse ceiling noted; round-gating queued post-run).
RECORDED EXPECTATIONS, not to be reread as regressions:
- F2: the 0.25 similarity gate is effectively a DISABLE of the resolution
  pass -- the reviewer's replay on ds4's own 150 renames shows NO
  threshold separates good from bad (near-chance ROC; the motivating
  wrong-rename class sits <= 0.143 but golden-good renames score low
  too). ds5 will finish with ~140 danglings, by design. The long-term
  disposition of rename verification is a SEAT question, not a threshold.
  DO NOT retune mid-run.
- F4: ds5 raw recall/precision stays plumbing-dominated (the comparator
  authority-collapse was never implemented); judge via the seat path.
Also: all 33 ds4 leaf artifacts revalidate 0-fail under current code.

READBACK_SMOKE.md (Matt's artificial-context suggestion): probe works
FREE with zero synthesis (stage-3 gap dissolves); r3 renders and caught a
REAL defect (inputs glosses missing -- stage-2's gloss rule covers
requires only, gap noted); the 4b seat ran live for $0.0004 and exposed a
genuine seats.py bug (prompt item ids vs validator ids -- mocks masked
it). Step 4 verdict: a-few-fixes-away.

## 2026-08-12: ds5 zero-intervention attempt -- two blockers, both fixed in code

The reviewed rerun (goal: complete untouched at ~$0.15) stopped twice.

**Blocker 1 (crash): duplicate seed names.** The model legitimately seeded
`chain_of_command` at two establishment sites ([1799,1799] and [2488,2488]).
`autofix_division` built its seed lookup dict LAST-wins while
`validate_division` resolves seeds FIRST-match -- the autofix judged child 3
fine on the [2488] entry, the validator failed it on the [1799] entry: an
unfixable 4-round loop by construction. Fix: `setdefault` (first-wins) so
autofix and validator read the same entry; pinned
(`test_duplicate_seed_names_autofix_validator_coherence`).

**Blocker 2 (crash): oversize first draw misdiagnosed as truncation.**
Leaf c3_c2_c3_c2_c1 (span 2126-2302, 177 lines) drew a COMPLETE 103,611-char
JSON reply: 123 nodes, 108 of them repeating one establishes string -- the
969-dup-loop class, at a deep leaf. The first-draw oversize short-circuit
(len > cap*3) hard-failed the whole build with the message "reply looks
truncated at max_tokens" -- factually wrong (the JSON parsed; its errors were
semantic coverage errors). This was `classify_cap_overflow`'s first live
firing and it returned "malfunction", correctly. **Fix: D6 stage 1 is now
wired live** in both `Driver.call` and `dispatch_core.feed`: an oversize
first draw classified MALFUNCTION gets ONE fresh resample (sharing the
existing once-only restart flag; budget re-bases as feed_failure does);
only a DENSE verdict fails, with an honest message. Pinned both ways
(`test_dispatch_state_oversize_malfunction_resamples_once`,
`test_dispatch_state_oversize_dense_fails_immediately`).

**Near-blocker (would have exhausted repairs): byte-identical repair
replies.** Unwind c3_c1 returned one identical 3,127-byte reply across
repair rounds r1..r3 ("merge ... loses content" each time) -- the growing
repair transcript added no information. New rule, both paths: a repair
reply byte-identical to the reply it was asked to correct triggers the
existing once-only fresh restart instead of burning rounds. Pinned
(`test_dispatch_state_identical_repair_reply_restarts_fresh`); the
exhaustion pin's fixture evolved to distinct reply texts (its intent --
loud failure + burial -- unchanged).

**Rejected alternative, by name:** mechanically dropping validator-rejected
unwind merges after non-convergence (merges are an optional dedupe, so the
un-merged graph is valid). Rejected for now: it edges into code making a
content call, and the restart remedy is content-free. Reconsider only if
the restart proves insufficient on a real build.

**Certificate note:** every fix above landed MID-CAMPAIGN between ds5
attempts. ds5's completion (if it completes) validates the fixes but is NOT
a strict zero-intervention certificate; that requires a fresh ds6 under
frozen code. 92 driver+core tests green at this entry.

## 2026-08-12: consolidated fix review -- NEGATIVE verdict, findings validated and closed

`consolidated_fix_review.md` (clean-context agent) returned NEGATIVE: two
fixes required before seats adjudicate real material. Per the standing rule
every finding was REPRODUCED before any fix was applied; all reproduced.

* **F0 (gate) FIXED**: `node_corpus.json` had been clobbered by the run-8
  `--ids` sample, failing 6 pins in `test_node_worked_example.py`. Restored
  by regenerating the default stratified 15 (deterministic, `Random(42)`).
  Residual hazard recorded: ad-hoc `--ids`/`--all` runs write over the
  pinned corpus file; a `--out` split is the durable fix (not done today).
* **F1 (seat validity) FIXED**: `_reply_item`'s digit-index fallback now
  fires ONLY for 4a/4b, whose pre-fix prompts taught `0.`, `1.`; 4d numbers
  its SENTENCES (denominator = claims -- positional mapping silently
  re-attributed verdicts), 4c never numbers anything. Digits for 4c/4d are
  refused by name. Pinned both ways.
* **F2 FIXED**: `readback.clause_text` narrows per-SPAN now; a partially
  narrowed multi-span node keeps its un-narrowed spans' source text
  (5 such nodes live; RB4/seats under `--all` were the exposure). Pinned.
* **F3 FIXED**: `link_nodes.merged_gloss` is provider-first: a gloss wins
  only from a node whose ASP defines the predicate (`defined_predicates`);
  alphabetical-first had let a borrower shadow the provider
  (`stay_in_bounds_principles` verified flipped live). Pinned.
* **F4 FIXED (both halves)**: edge-whitespace claims now round-trip via
  stripped-to-stripped matching in `_reply_item`, guarded to fire only
  while stripping keeps the denominator unambiguous; `_NODE_SPAN_HEAD`
  widened to `L\d{4,}` (5-digit line numbers). Pinned.
* **Held test_link failure**: untouched, deliberately -- it is Matt's
  design-tension item; the review's rebuild-don't-delete recommendation is
  parked with it.

Suites after the fixes: phase_1 765 passed + 1 xfailed (the 6 F0 failures
gone); seats/readback/plumbing 359 passed; full graph_v2 suite running.

## 2026-08-12: latent-guard-branch audit (Matt's question after the ds5 blockers)

Branch coverage was run over the guard stack (`pytest-cov`, driver+core
suites). Headline finding: **the Driver.call serial-path twins of today's
three fixes were themselves latent** -- only the dispatch_core versions were
pinned, which is the exact defect class that bit ds5. Added and green:
`test_call_oversize_malfunction_resamples_once_serial`,
`test_call_oversize_dense_fails_serial`,
`test_call_identical_repair_reply_restarts_fresh_serial` (max_repairs=1
makes it discriminating), plus two batch failure-path pins:
`test_batch_job_level_failure_reruns_live` (FAILED/EXPIRED/CANCELLED job ->
rerun live, worst-case rollback, manifest clear) and
`test_feed_recovered_invalid_reply_requeues_for_repair`. 97 driver+core
tests green; branch coverage 84% (was 82%).

Remaining latent regions, triaged and left by name:
* concurrent-executor billing lock + body build (dc 602-655): concurrent
  mode only; equivalence pins cover its outputs, the lock internals need a
  threaded fake worth building only if concurrent becomes the default again.
* manifest adoption corners (dc ~1214-1228): partially covered; the happy
  recovery path ran live twice in ds5 today.
* live transport ladders (GraphClient retries, `_send` truncation resample)
  and `main()`/`post_build_checks`: fire only against a real provider/CLI;
  the retry taxonomy is pinned at the marker-string level.

## 2026-08-12: ds5 complete -- validation results (all offline, no spend)

Build: 817 nodes, 1853s final segment, post-build checks OK (0 bad spans,
0 bad quotes), modal sweep 36 flagged (23 flattened / 11 strengthened /
9 weakened), heading sweep 1 flag. Health: 50 records, all unclaimed-content
containments (aggregate cost of the F3 round-0 containment -- telemetry,
not failures). Cost across ds5's three segments: $0.916 ($0.224 + $0.219 +
$0.473) vs the $0.15 target -- the two crashes each paid for partially
recovered work. CAMPAIGN LEDGER NOW $6.101, $0.10 OVER the $6.00
authorization; no further model spend without Matt.

graph_compare vs golden (GRAPH_EQUIVALENCE.md): 1:1 aligned 498 (ds4: 506),
split/join 33, misaligned a/b 76/286; permissive edge recall 0.393 /
precision 0.112 (raw numbers remain authority-plumbing-dominated -- F4
comparator collapse still unbuilt, recorded expectation); adjudication
queue 3403 (needs seats = spend; parked).

**Substantive divergence found (deterministic, no seat needed):
`chain_of_command` DANGLES in ds5** -- 24 needers, zero providers -- and the
pre-registered boundary rule says it must NOT dangle. Root cause chain:
the section that establishes it (L1798-1973) provides only privacy-related
names; in ds4 the resolution pass (150 renames) would have wired the
needers to a provider, but ds5 ran under the 0.25 similarity gate that
effectively disables the pass (recorded F2 expectation). So the dangling
is BY DESIGN of the gate -- but this measures the gate's cost against the
golden boundary rule for the first time. ds5 name-level danglings: 37
(ds4: 5; golden: 2). The rename disposition remains the parked SEAT
question, now with a concrete stake.

**Proposal recorded (not implemented): enforce division promises.** The
c3/c2 division PROMISED `chain_of_command` via expected_cross_links
(provides_side child 2 after the coherence autofix), and no leaf of that
child ever provided it. Nothing checks promise-vs-delivery today. A
deterministic post-unwind check (code-only: compare expected_cross_links
names against the children's actual provides; record breaks in health)
would have named this at build time. Rejected alternative, by name:
having the driver ADD the missing provides -- code must not make content
decisions.

## 2026-08-12: promise-vs-delivery check IMPLEMENTED (Matt-approved)

`broken_promises(division, children)` in recurse_driver.py, called at both
unwind sites (Driver.unwind and dispatch_core._want_unwind -- same function,
equivalence by construction). Undelivered expected_cross_links names land in
the unwind's health.jsonl row (`broken_promises`) and print a warning at
build time. Observation only; the add-the-missing-provides alternative
stays rejected by name. Pinned
(test_broken_promises_names_undelivered_cross_links); 98 driver+core green.
Budget note: Matt extended the campaign authorization to $10.00 (2026-08-12).

## 2026-08-12: steps-1-4 latent-path audit -- 2 bugs, both validated and fixed

Clean-context agent ran branch coverage over translate/schema/checks/
readback/readback_r3/seats (+35 offline tests, test_latent_paths_steps14.py
adopted into the tree). Both findings REPRODUCED before fixing:

* **BUG 1 FIXED: the two truncation validators disagreed.**
  `response_envelope` flags finish_reason "max_output_tokens" as truncated;
  `_check_envelope` raised only on "length"/"max_tokens" -- the same reply
  was truncated to the batch collector and complete to the serial guard,
  failing later as a parse error blaming response_format. The guard now
  trusts the envelope's own `truncated` flag (authority when present;
  finish-reason list kept as fallback for envelopes built without it).
* **BUG 2 FIXED: HTTP 402 rode the full transient ladder** (6 retries,
  630s of sleep) on terminal credit exhaustion, and hung the two F2 pins
  in test_translate_exec ~10.5 min each (the 22-minute graph_v2 suite was
  ~21 min of these two hangs). Ruling: 402 stays retryable -- rejected
  alternative, by name: terminal 402 -- because together.ai 402s flapped
  for ~minutes after mid-campaign credit top-ups (measured); it now rides
  a SHORT ladder (2 retries, ~90s) in BOTH paths (dispatch_core._ladder +
  Driver._complete). The F2 pins patch sleep and run in seconds.

Also adopted from the audit, recorded not fixed: `complete_messages`
bypasses `_retrying`, so repair-round truncations are never resampled even
with resample_truncation set (pinned as documented behavior); the
merged_gloss provider-first fix depends on gloss_from_rows staying
first-wins (`setdefault`) -- a refactor to plain assignment would silently
invert F3. Suites: 98 driver+core, 800+1 phase_1, 12 translate_exec (3.6s,
was 21 min), 35 audit tests -- all green.

## 2026-08-12: Matt's rulings -- repair process, dense-leaf recursion, gate, enum plan

**Process ruling (budget): graph construction gets the translation
pipeline's error discipline.** `repair_census.py` (new, offline) mines a
run's failed/ + health into a category taxonomy with a named fix lever per
category, and compares runs side by side. Baseline measured: ds4 buried 72
failures, ds5 buried 25; ds5's residue is quote-not-verbatim 9,
merge-loses-content 4, cross-link-provider 4 (the coherence bug, now
fixed), uncovered-content 2. STANDING RULE: before the next paid run,
every category with a repeat offender gets an underlying-cause fix
(prompt / example / format forcing) tested against the stored failing
transcript, and the census must show the per-category count falling
run-over-run. The estimator lesson from ds5 stands beside it: repair
rounds near the root cost ~$0.03/draw (221k-token prompts), so lowering
error counts IS the cost model.

**Dense-leaf ruling (risk #1): the normal recursion absorbs it.** Matt:
"why can't the existing process just continue to break it down?" -- it
now does. Serial: build() catches the dense failure and falls through to
the ordinary Phase D on the same span. Core: the leaf state MORPHS in
place into the division dispatch (`_division_state` + `DispatchState._morph`,
executor holds the same object). A dense-morphed division answering
decision="leaf" fails loudly (no loop). Pinned both paths e2e
(byte-identical artifacts). REJECTED BY NAME: D6 stages 2-3 mechanical
boundary bisect -- a second splitting mechanism to test and trust, when
the one we already trust suffices. D6 stage 1 (the classifier) stays: it
routes malfunction->resample vs dense->divide.

**0.25 gate ruling: option (c) approved by Matt** -- resolution renames
are proposed mechanically and adjudicated by a seat on prose-vs-prose
meaning; the similarity gate survives as prefilter only. Seat calls are
independent ONE-SHOTS (no transcript continuity: the seat has no prior
transcript -- continuity is a build-model concern; each judgment must
stand alone and order-blind, like every stage-4 seat). To design next:
brief + 10-item frontier-parity validation sample before any live use.

**Naming/reference plan (Matt, to test before the F4 comparator
collapse):** measured on ds5, needs draw from small pools -- inherited
seed vocabularies median 34.5 names (max 77), 123 distinct provided names
graph-wide, 374/1100 need-instances name a seed. Plan: format-force the
unwind's decision fields to per-dispatch ENUMS of valid options
(resolutions[].rename_to from the actually-provided names,
needer/survivor/retired from actual node ids) -- grammar-level "only
valid options", per-node and cheap at these pool sizes. To be tested
against stored unwind transcripts first. F4 comparator-side collapse
remains the fallback if enum-forcing underperforms.

## 2026-08-12 (late): rename seat built + validated; enum forcing in; graveyard dispositioned; small-set rerun

**Rename seat (`rename_seat.py`, wired into run_resolution_pass behind
`rename_seat: true`):** one-shot, order-blind, BLIND ON NAMES by
construction (prose + span text only -- name similarity is the documented
failure mode and never enters the prompt); fail-closed to
different_concept. Validation, 22 live judgments, $0.002 total:
- 10 ds4 ungated renames (incl. the content_definition known-bad): seat
  rejected all 10; frontier (this driver, same evidence) rejected all 10.
- 6 ds5 gate-ACCEPTED renames: seat rejected all -- and frontier review
  agrees these were wrong (chain_of_command -> one rule inside it;
  avoid_sycophancy -> forthrightness). The 0.25 gate's accepts were
  themselves plumbing-grade, consistent with its near-chance ROC.
- 6 constructed true positives (same mechanically-resolved name,
  independently-written prose): accepted the clear paraphrase pair,
  rejected 5 borderline facet-mixes (instruction-class vs authority-level
  prose under one name). RECORDED BIAS: the seat is stricter than the
  frontier on facet-mixing pairs; per the pre-registered principle
  (absence > wrong) this errs honest. Revisit if ds6 danglings stay high.

**Enum forcing** (`enum_decisions: true`): unwind + resolution grammars
now enumerate rename_to from provided names, needer/survivor/retired from
node ids, name from actual danglings. Flag-off byte parity pinned.

**Graveyard dispositioned:** all 41 open entries got per-entry VERDICT.md
diagnoses (craft-slip class -> run-5..8 prompt fixes; translated-with-
notes -> benign; abstentions -> honest; one clause-identity slip -> new
candidate lever: enum-force clause_id). 0 open.

**Small-set rerun (steps 1-3), $0.045:** 13 translated / 1 abstained
(l1799_1974_n009) / 1 unrepaired (l797_809_n001) -- run-8 parity under
the full fix stack; link scope gathers 28 modules, requires-resolution 7,
merged gloss 132 names, no errors. Steps-4 live seats not run this pass.

**ds6 PRECONDITIONS:** clean-context adversarial review of all post-PR-#1
work (Matt's order), then launch with enum_decisions + rename_seat +
promise check + dense-recursion in driver_config. Budget $10.00, ~$6.20
spent.
