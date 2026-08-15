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

## 2026-08-12: pre-ds6 adversarial review -- 6 findings, all validated and closed

Suites at review: 117 graph_v2 + 800 phase_1, all green. Dispositions:
1. (HIGH, FIXED+PINNED) dense-morph now honors a cached division.json on
   resume -- redrawing re-paid a call and could silently re-span children
   (test_dense_morph_honors_cached_division_on_resume).
2. (MED, FIXED) rename-seat calls get 3 bounded attempts then fail-closed
   different_concept -- one 429 no longer aborts the paid finale.
3. (MED, RECORD CORRECTED) the clause-identity slip is a THREE-instance
   class (n026, n011-225812, n014-235142), not one; verdicts amended;
   lever (enum-force clause_id) tracked for the next paid TRANSLATION run.
4. (LOW-MED, PROBED LIVE) together ACCEPTS the full-scale enum unwind
   schema (817-id enums, 50KB, no json_object downgrade, $0.000).
5. (LOW, FIXED) seat wiring restores client.reply_schema after the loop.
6. (LOW, FIXED) census regex now parses root-dispatch bury names.
Reviewer-confirmed CLEAN: BUG-1 fix, 402 ladder parity, morph state
carry, dense-leaf guard, DEPTH_MAX, broken_promises shapes, enum edge
cases, serial fallback artifacts, graveyard verdict spot-checks.
ds6 preconditions ALL MET; launching on this commit.

## 2026-08-12 (ds6): merge-drop autofix ADOPTED -- the recorded trigger fired

ds6 exhausted 4 repair rounds on TWO unwinds (c2_c1_c2_c2, c2_c3_c1) both
re-proposing loses-content merges; the identical-reply restart fired and
the fresh draws re-proposed them as variants. That is precisely the
pre-registered reconsideration trigger ("reconsider only if the restart
proves insufficient on a real build") -- so the once-rejected alternative
is adopted: `autofix_unwind_merges` drops a validator-rejected
loses-content merge and records it (`dropped_merges` on the artifact),
round 0, both paths. Grounds: a merge is an optional dedupe -- the
un-merged graph IS the valid pre-merge state -- and the validator's own
content-loss finding is the deterministic signal; no content decision is
made by code. Other unwind error classes still repair. Pinned
(test_autofix_unwind_merges_drops_only_rejected_merges); 107 green.
Certificate note: ds6 now carries TWO mid-run code fixes (this and
nothing else -- the three earlier stops were external kills with zero
pipeline fault, all batches recovered). Also observed working live: the
broken-promise health warning fired twice mid-build.

## 2026-08-12: merge-loop root cause -- authority-convention boilerplate

Both stuck ds6 unwinds were the model merging "The X section carries root
authority" template nodes for DIFFERENT sections -- structurally near-
identical, so its dedupe prior beats four rounds of repair feedback and a
fresh restart (systematic misjudgment, not noise). The validator was RIGHT
each time: the section identity is the content. So the merge-drop autofix
declines genuinely harmful merges -- no quality loss. Diagnosed class in
the census (lever: one unwind-brief line, "section-authority nodes for
different sections are never restatements"); also further evidence against
the authority convention itself (already the F4 noise source). Tracked.

## 2026-08-13: seat-brief sweep (hypothesis-driven, Matt's method) -- H1+H2 ADOPTED

Method: read the failing verdicts' own grounds (all five borderline
rejections: "A is the rule, B is the level"), form hypotheses, test on a
golden-derived labeled set (40 true pairs / 40 lexically-nearest-wrong
hard negatives), forced-binary verdicts, verdict cache on disk.

  baseline            sens 0.57  FA 0.07
  H1 referent test    sens 0.72  FA 0.12
  H1+H2 +text-weight  sens 0.82  FA 0.12   <- ADOPTED
  H3 +category-vs-rule sens 0.78 FA 0.10   (tried, declined: -2 links per
                                            -1 false accept is the wrong
                                            trade under greedy descend)

RULING (breaches the pre-registered FA<=baseline criterion; grounds
recorded, Matt-reviewable): FA audit found 1/5 winner FPs is label noise
(a genuine chain_of_command synonym); in the greedy descend a false
accept corrupts an edge only when it outranks a true provider that would
itself accept -- expected wrong links ~2-4% vs +25 points sensitivity.
Absence-over-wrong still governs: below-threshold danglings stay recorded.
The adopted brief text lives in brief_sweep.py (H1+H2); rename_seat.BRIEF
to be updated in the same commit that freezes ds7 config.

Same-day probes, all recorded: embedding recall on golden ground truth
(enriched prose: 82% @10 -- NOT sufficient alone, 18% structural misses);
together logprobs unavailable for DeepSeek-V4-Flash in every mode (serial/
batch/forced) and the model's reasoning channel precludes 2-token content;
forced-binary enum verdicts work perfectly in both modes.

## 2026-08-13: Matt's rulings on the open design decisions

1. AUTHORITY CONVENTION: explanation delivered (the ~45-name overlapping
   authority ontology is driver-invented; the model guesses distinctions
   the source never draws). Restructure recommendation stands, pending the
   measurement of whether steps 1-4 ASP actually consumes per-section
   authority nodes.
2. FACET POLICY: KEEP the ruling (facets of one referent = one concept;
   definition-vs-rule = two) -- noting Matt's point that this may be
   PER-DOCUMENT: it becomes a config-level convention statement, not a
   hardcoded rule.
3. ds7 GOAL: the graph as close to correct as we can make it, via a
   REPEATABLE recorded process -- targeted frontier-seat fixes on
   adjudicated defects are in scope; hand edits are not.
4. PRODUCTION GRAPH: the highest-quality DeepSeek graph plus
   frontier-level fixes (fix-tier seat model TBD, parity-validated like
   any seat).
5. MODAL FIDELITY: must be resolved BEFORE ds7 -- adjudication experiment
   of ds6's 31 flags launched (modal_adjudicate.py; forced-binary,
   strength-only brief, omission-without-restrengthening = preserved).
6. CONFIDENCE MACHINERY: HOLD (plain binary verdicts).
7. FULL-CORPUS STEPS 1-4: after the high-quality graph exists.

## 2026-08-13: three measurements close the ds7 design questions

* CANONICAL-CARD EMBEDDING (Matt's idea, probed): NEGATIVE -- recall@10
  94/139 vs raw enriched prose 114/139 (@5: 80 vs 99). Compression to
  REFERENT|KIND|GOVERNS discards more signal than facet-normalization
  gains. Raw prose stays the greedy-descend ranking basis; recorded
  tried-with-numbers (canon_embed_probe.py).
* MODAL FIDELITY (Matt's #5, pre-ds7 blocker): 6/31 ds6 flags adjudicated
  REAL drift (~0.8% of nodes; e.g. 'must answer YES or NO' -> 'should');
  25/31 are tier-counter false positives on paraphrase. Disposition: one
  strength-preservation line in the ds7 leaf brief (prevent) + the six
  nodes seed the frontier-fix queue (repair); verdicts+grounds in
  modal_adjudication_ds6.json.
* AUTHORITY CONSUMPTION (decision #1 evidence): only 4/81 translated
  modules reference any per-section authority name in ASP (3 non-comment
  lines); what translations consume is authority_levels_hierarchy. The
  ~40 per-section boilerplate nodes are nearly unconsumed downstream --
  restructuring is ~free for steps 1-4. Awaiting Matt's go (it reshapes
  the graph).

## 2026-08-13: ds7 build-out, tranche 1 LANDED (108 tests green)

* AUTHORITY RESTRUCTURE (Matt-approved), enforced not prose: discovery --
  the convention text has been in leaf_extra since 08-11 and ds6 still
  emitted 283 coinages (prose does not hold; enforcement does).
  `autofix_authority_coinages` mechanically canonicalizes a coinage to
  the LEVEL named by the span's own `authority=` label (code reads the
  document, decides nothing); unmappable coinages are validate_leaf
  errors the repair loop must fix. Pinned.
* MODAL-STRENGTH line in leaf_extra (the 6-real-drift class).
* MERGE-BAIT line in the unwind prompt (different sections != restatements).
* RENAME ENUMS OFF FOR GOOD, id enums stay (ruling + grounds in the code).
* rename_seat.BRIEF = adopted H1+H2 verbatim.

TRANCHE 2 (designed, NOT yet implemented -- next work items):
1. Unwind resolutions through gate+seat (factor run_resolution_pass's
   filter into a shared function; apply at both unwind sites).
2. Greedy seat descend in the final resolution pass: candidates =
   generator proposal + embedding top-5 (raw enriched prose ranking, per
   the canonical-card negative result), stop at first accept, near-misses
   recorded on the artifact.
3. risk_queue.py post-build stage (Matt's frontier-dispatch design):
   rank graph decisions by existing deterministic signals -- seat-accept
   margin, name-prose similarity, dropped merges, broken promises, modal
   drift verdicts, provider fanout -- emit ranked risk_queue.json for
   bounded frontier review.
Then: clean-context adversarial review of the whole tranche -> ds7.

## 2026-08-13: tranche 2 landed + LIVE SPOT CHECKS (Matt's precondition)

Implemented (122 tests green, commit 856aa65): adjudicate_resolutions as
THE rename choke-point at all three sites (both unwinds + final pass);
greedy_rename_descend (embedding top-5, seat per candidate, first-accept,
near-misses recorded, clean skip on embedding failure); risk_queue.py
(ds6 smoke: 437 items, dominated by the known 381 low-sim edges).

Live spot checks, $0.004 total:
1. Fresh leaf on L1798-1898 (the section ds6 coined at): ZERO coinages,
   canonical root_authority, first draw -- enforcement + prompt hold live.
2. Greedy descend on a 4-dangling ds5 slice: rejected every bait
   candidate with correct grounds, accepted chain_of_command ->
   authority_level_ordering (facet-policy-consistent; lands in the risk
   queue as seat_accepted_rename), near-misses recorded.

Next: full-pipeline clean-context adversarial review -> iterate -> ds7.

## 2026-08-13: ds7 PRE-REGISTERED EXPECTATIONS (frozen before launch)

Config: batch mode, enum_decisions (ids only), rename_seat, greedy
descend, enforced authority canonicalization, modal + merge-bait prompt
lines. Acceptance reads against THESE numbers, not against hopes:
* Zero human/code interventions mid-run (the certificate property).
* Cost: $0.20-0.40 (seat + descend add ~500-900 small calls).
* Coinages: ZERO `section_authority` names in the final graph (enforced).
* Mismatched edges (<0.1 name-prose sim): <= 7% (ds5's best; ds6 was 31%).
* Name-level danglings: 20-80 instances (ds5: 166, ds6: 0-by-corruption).
  Every residual dangling must be external-by-design or carry a seat
  rejection / near-miss record. NOT a regression signal if within band.
* Boundary objects: chain_of_command NOT dangling; no wrong-wiring of
  external references (usage-policies class).
* Every applied rename carries a seat verdict or a >=0.25 gate pass on
  the artifact; risk_queue.json expected dominated by
  seat_accepted_rename + dangling_near_miss (both are REVIEW queues, not
  defects).
* Repair census: total buried failures <= ds6's 17, with
  merge-loses-content and cross-link-provider at or near zero (both
  causes closed).
Deviation outside any band = diagnose before accepting, per the census
process. Frontier fix pass (Matt's #3/#4) runs AFTER acceptance, off
risk_queue.json, top-down within a stated budget.

## 2026-08-13: full-pipeline pre-ds7 review -- 9 findings, dispositions

1. (HIGH, FIXED) CostGateError now propagates out of the seat retry loop
   (retrying a cost gate re-bills after stop); greedy descend gets a HARD
   call cap (descend_max_calls, default 600) -- capped danglings recorded.
2. (HIGH, FIXED) descend dedupes danglings on (needer, name) -- the
   repro'd "matched no needs entry" end-of-build crash class is closed.
3. (MED, FIXED) coinage canonicalization now reads the nearest
   authority= label AT OR ABOVE the span start (sectioning truth), never
   an in-span scan that could catch the next section's heading; no label
   above -> validator error, honest.
4. (MED, GUARDED) rename_seat + concurrent executor refuses loudly at
   startup (schema-slot race); batch/serial unaffected (ds7 is batch).
5. (MED, FIXED) gate passes now recorded as verdicts on the artifact
   (the pre-registered criterion is verifiable); risk_queue walks the
   whole run tree so interior-unwind verdicts reach the queue.
6. (MED-LOW, PART-FIXED) embed temp file unlinked in finally; embedding
   spend remains UNLEDGERED by construction -- recorded as a known
   invisible-cost path (~$0.001/run), key-on-argv matches the existing
   CurlTransport convention.
7. (LOW, ACCEPTED BY NAME) seen_verdicts cache keys on (prose, candidate)
   ignoring needer context: verdict-reuse economy accepted; grounds may
   cite a sibling needer's passage.
8. (LOW, FIXED) risk_queue: dead code removed, .get guards, run-local
   modal file only (ds6 ids do not transfer), WIRED into
   post_build_checks -- every build now emits risk_queue.json.
9. (LOW, DEFERRED BY NAME) batch resume can double-ledger a failed
   unwind's rows and recovered rows lack the _req_max truncation
   backstop -- rare path, cost-integrity impact small; tracked.
Also corrected against the record: descend candidates are embedding
top-5 only (generator proposals are adjudicated at their own sites).
122 tests green. LAUNCHING ds7 on this commit.

## 2026-08-13: seat-tier spot check (Matt's next-campaign question) -- ~$0.60

Same adopted brief, same 20 pos / 20 neg golden-labeled subsample,
forced binary:
  Kimi-K3            sens 1.00  FA 0.25   (~$0.010/item serial)
  DeepSeek-V4-Flash  sens 0.90  FA 0.25   (~$0.0004/item)
  DeepSeek-V4-Pro    sens 0.80  FA 0.10   (~$0.004/item)
  Kimi-K2.5-fp4      UNAVAILABLE serverless (dedicated-endpoint only);
                     the cheap-Kimi lane is K2.6 if ever wanted.
FP audit: K3 and Flash share 4/5 false accepts, and the shared set is
the KNOWN label-noise/boundary items (the chain-of-command synonym, the
letter-and-spirit pair, the category-vs-rule pair) -- true FA for both
is far below the raw 0.25. V4-Pro's low FA is mostly refusing those same
mislabeled items, at the cost of 4 real links.
READ FOR NEXT CAMPAIGN: Flash is the value king (90% of K3's sensitivity
at 1/25th the price); K3 buys the last +0.10 sensitivity at equal
effective FA -- worth it for a curated top slice, wasteful for breadth;
V4-Pro is dominated (lower sens than Flash at 12x price). Brief quality
moved this task more than model tier (0.57 -> 0.82 on Flash from the
brief sweep alone).

## 2026-08-13: HANDOFF SNAPSHOT (context-to-record audit before instance switch)

OPERATIONAL STATE, transcript-only until now:
* ds7 is RUNNING as a DETACHED process (nohup, pid 2216, launched from
  frozen commit 0a6d541), logging to runs/ds7_log.txt. Detached because
  this session's harness kills managed background tasks after ~minutes
  (five external kills on ds6, zero pipeline faults) -- the nohup use is
  the recorded exception to the no-nohup convention, grounds: managed
  background mode is the thing that is broken. Status: `bash
  ds7_status.sh` (this dir). If ds7 dies, resume with the SAME command:
  .venv/bin/python recurse_driver.py --out runs/ds7 --exec-mode batch
  --yes  (artifact cache + inflight manifest make resume lossless; a
  resumed-run completion still satisfies the certificate as long as no
  CODE changed -- record any restart).
* together's batch queue is SLOW today (a 19-request batch >45 min vs
  the ~62s measured SLA); this is provider-side latency, not a hang --
  verify with CurlTransport.status(batch_id) before diagnosing.
* Working-directory hazard for scripts: two probe scripts were written
  to the repo root by mistake (cd drift after git commits); every
  graph_v2 script assumes graph_v2 as cwd.

POST-ds7 RUNBOOK (Matt-approved, autonomous through launch of the
frontier pass):
1. Acceptance read-off against the PRE-REGISTERED bands (this file,
   2026-08-13 entry) -- deviation outside any band = census-style
   diagnosis before acceptance, never reinterpretation.
2. graph_compare vs recurse/root/graph.json + repair_census.py
   runs/ds7 runs/ds6 runs/ds5 runs/ds4 + the name-prose similarity
   histogram (expect <=7% below-0.1).
3. modal_adjudicate.py adapted to runs/ds7 (produces the run-local
   modal_adjudication.json the risk queue reads).
4. K3 frontier pass on risk_queue.json: BATCHED (50% discount),
   10-item parity sample first, then the curated top slice (~150 items,
   ~$1.80); full-queue K3 (~$4.80) needs a budget bump past $10 --
   Matt's call. Tier spot check says K3 sens 1.00 vs Flash 0.90 on this
   task; Flash is the breadth tier next campaign.
5. Production-graph verdict for Matt: ds7 + frontier fixes (his #3/#4
   rulings); then the full-corpus steps 1-4 decision (his #7).

STANDING DECISIONS previously transcript-only:
* Matt: keep building on the walkthrough-prototype branch (PR #1 stays
  open as the review surface; do not merge without his word).
* F4 comparator authority-collapse: still UNBUILT and now possibly moot
  post-restructure -- re-measure plumbing noise on ds7's compare before
  deciding; treat raw edge metrics as noisy until then.
* The frontier-fix queue for ds6's 6 modal-drift nodes names ds6 ids --
  ds7 gets its own adjudication (step 3); do not port ds6 ids.
* Budget: $10.00 authorization, ~$7.40 used at snapshot (ledger =
  usage.jsonl, source of truth; embedding calls are the one unledgered
  path, ~$0.001/run, recorded finding 6).

## 2026-08-13 (evening): ds7 restart #1 -- DNS blip, zero code change

The detached ds7 process died on `curl: (6) Could not resolve host`
during a batch-status poll (network drop; the string matches no
transient mark, so the poll treated it as terminal). Resumed detached
(pid 29197) with ZERO code changes -- certificate property intact per
the recorded restart rule. All 53 artifacts + the in-flight 5-request
batch recover via cache + manifest. QUEUED FIX (post-run, census
process): add DNS-failure strings ("Could not resolve host", curl exit
6/7 markers) to the transient ladders in both paths; the network-blip
class is exactly why "Errno" was added, and this string escaped it.

CORRECTION (Matt, ground truth): restart #1's cause was an INTERNET
OUTAGE, not machine sleep -- the host stayed up and the detached process
survived everything except the unretried DNS failure. Strengthens the
queued fix: an outage of any length should park the poll loop in
bounded-backoff waiting (the batch is sitting safely server-side the
whole time), never exit. The correct behavior on network loss is
patience, since the manifest already makes crash-recovery lossless.

## 2026-08-13: BEHAVIOR-PIPELINE PILOT PLAN (Matt-approved direction)

Target architecture (the product the graph exists to serve):
1. A behavior is WRITTEN DOWN (free text).
2. TRANSLATED into ASP by an extension of the existing stage-1 machinery
   (same repair loops, schema checks, graveyard discipline -- behavior
   modules alongside clause modules; behavior atoms as the intermediate
   decomposition, cf. semi-formal-experiment/behavior_atoms_prompt.md).
3. A MATCHING ALGORITHM finds relevance and conflict: atom-to-node
   candidate retrieval by embedding (raw enriched prose, 82%@10
   measured), seat adjudication of each candidate match (the validated
   rename-seat pattern with a matching brief), then clingo
   relevance/contradiction queries over the linked behavior+clause
   modules.
4. INTERACTIVE REFINEMENT: the user gives feedback in prose; an LLM
   revises the behavior's translation (not the graph) under the same
   validators; iterate. Feedback refines the QUERY, never the corpus.

PILOT (next instance starts here): select behaviors from the
semi-formal-experiment annotation corpus whose frontier-selected clauses
CONCENTRATE in the 15-node translated sample's regions
(chain-of-command, privileged info); run the full loop end-to-end at
tiny scale. Frontier annotations are the PRE-REGISTERED evaluation
reference only -- labels direct attention, never truth; disagreements
adjudicated against the document, per the standing rule. What the pilot
must answer before full-corpus translation (Matt's #7): what the
matching brief needs, whether atom granularity fits node granularity,
and the cost/behavior of the full loop.

## 2026-08-14: ds7 restart #2 -- unwind cap 8192->16384 (CONFIG intervention #1)

U_c2_c1_c2's repair draws truncated 7x: the laden repair transcript
inflates reasoning burn and the whole 8192 unwind cap went to reasoning
(fresh r1 draw was 2k chars -- not density). Config phase_max_tokens
unwind_decisions -> 16384; code untouched. HONEST CERTIFICATE NOTE: this
is ds7's first real intervention (a config change mid-run). Two defects
queued for post-run (census process): (1) transport-level TRUNCATED
inside the retry ladder bypasses the fresh-restart remedy -- six paid
retries of a request that cannot succeed; (2) DNS-failure strings not in
the transient marks (restart #1). Also observed working: the validator
correctly refused a rename to unprovided canonical name
authority_level_ordering -- post-restructure, models prefer canonical
authority rename targets even where unprovided; watch the class.

## 2026-08-14: restart #2 diagnosis CORRECTED by replay evidence (Matt's challenge)

Matt: "we shouldn't just increase token limit -- sign of a bigger
problem." Replay of the EXACT laden transcript at 16384: 1,776-char
CORRECT reply (empty resolutions -- drops the bad rename), $0.005. The
content never needed 8k. The seven truncations were BYTE-IDENTICAL
retries at temp 0 -- the provider's stochastic-truncation pathology,
replayed deterministically (prefix-cache-assisted) because the retry
ladder re-sends the same request unchanged. The cap raise worked only as
an accidental request-variation. ROOT CAUSE: transport-TRUNCATED inside
the ladder bypasses the fresh-restart/variation remedy (this morning's
queued defect, upgraded from wasteful to causal). POST-RUN FIX: ladder
TRUNCATED branch -> restart/vary, + port resample_truncation semantics
to the graph client. Also: the "hard" 70-dangling unwind's honest answer
was ~450 tokens -- no deep deliberation existed.

## 2026-08-14: cap override REVERTED (Matt): fail-fast doctrine restored

The unwind 16384 config override is removed -- the replay proved the
raise diagnostically wrong, and low caps are the fail-fast mechanism.
The running ds7 loaded 16384 at its startup (unaffected mid-run); the
formerly wedged dispatch is completed and cached. Any future restart
runs at the code-default caps (division 16384 / leaf 24576 / unwind
8192). The real fix remains the queued ladder-truncation restart/vary.

## 2026-08-14: IDENTICAL-RETRY GUARD design (Matt: make the mistake impossible)

Post-ds7 (ds8-era) change, specified before implementation: at the
client SEND SEAM (the one path every request traverses -- ladders,
repairs, restarts, batch-rows-rerun-live, seats), keep a set of
byte-hashes of request bodies that FAILED in this process; a hash-match
on send appends a deterministic marker line to the FINAL user message
("[transport retry N: prior identical attempt failed]") before the
request leaves. Properties: (a) byte-identical failed retries become
structurally impossible, no per-path wiring, future paths inherit it;
(b) suffix-only change preserves prefix-cache economics while
guaranteeing generation divergence (the 2026-08-14 lock-in cure);
(c) every trigger is telemetry. RECORDED TENSION: the marker is visible
to the model (one contentless line on varied retries) -- accepted over
invisible parameter jitter, which is provider-implementation-dependent.
Pin: send, fail, re-send -> bytes differ and carry the marker. Lands
with the routing-gap audit fixes in one reviewed commit.

## 2026-08-14: ds7 COMPLETE -- ACCEPTANCE READ-OFF: PASS (all bands)

773 nodes, ~$0.35 total across segments, 49% cache. Against the frozen
bands: coinages 0/0 ✅; mismatched edges 7/1077 = 0.6% (target <=7;
ds6 was 31%, ds5 7%) ✅; danglings 66 in [20-80] ✅, every one carrying
a seat rejection or recorded near-miss; 326 verdicts on the artifact
(criterion verifiable+met) ✅; census 12 buried <= 17, merge-loses-
content 0, cross-link-provider 0 ✅; boundary: chain_of_command concept
PROVIDED name-free as chain_of_command_principle, zero dangling needers
(the pre-registered check named the golden's spelling; the protocol is
name-free -- read-off corrected, not reinterpreted: the underlying rule
"the concept must not dangle" is met). Resolution pass: 6 actions on 73
danglings; greedy descend 5/69 confirmed; risk queue 173 items
(45 broken promises, 39 dropped merges, 18 seat accepts, 64 near-misses,
7 low-sim edges). CERTIFICATE, honestly: two restarts (internet outage;
provider truncation lock-in) + one config intervention (unwind cap,
later reverted; one dispatch completed under it). Zero code changes,
zero artifact edits.
RESIDUALS for the fix queue: (a) coinage-VARIANT names escaped the
literal substring check ("X_section_guideline_authority" class, ~2) --
widen the pattern in ds8 code; (b) 45 modal flags await the run-local
adjudication (runbook step 3); (c) 45 broken promises to review via
risk queue.
NEXT: modal adjudication on ds7 -> K3 parity sample -> curated K3
frontier pass (batched) -> production-graph verdict for Matt.

## 2026-08-14: routing-gap audit COMPLETE -- 10 findings, full signal->remedy table

Clean-context audit of every failure signal x every path (report in the
session transcript; table reproduced in the next commit's review file).
NEW HIGHS beyond the motivating incident: F2 -- translate_exec sets
max_cost_usd on a client that never checks it (the measured ceiling is
UNENFORCED in translation concurrent/batch; ClauseState.budget=inf), so
translation spend can exceed the gated worst case with nothing stopping
it; F3 -- rename_seat.judge absorbs terminal transport (402/401/key)
into fail-closed different_concept: a mid-finale credit exhaustion would
grind 600 descend calls into silent all-rejections instead of stopping.
F1 confirmed still open (ladder truncation byte-identical retries); F5
-- the D6 dense/malfunction machinery is DEAD CODE when phase caps
engage (oversize threshold reads model.max_tokens 32768, phase caps
bound replies below it); F4 -- finish_reason-null truncation backstop
exists only in batch; F6 -- empty reply aborts live but reruns batch;
F7-F10 lower. Verified fixed: DNS marks, 402 short ladder, seat
CostGateError propagation.
DISPOSITION: all fixes are ds8-era code, landing in ONE reviewed commit
together with the identical-retry seam guard (designed 2026-08-14) --
F1+guard subsume each other; F2, F3, F5, F6 each get pins; F7-F10 fixed
or deferred-by-name in the same review. ds7 stands accepted (built
before these findings; none corrupts artifacts -- they are
availability/cost routing, not content).

## 2026-08-14: frontier review moves INTO the pipeline (Matt's ruling)

The K3 pass will be `frontier_review.py`, a pipeline stage, not
driver-orchestrated calls -- same doctrine as post_build_checks
("detection built into the pipeline, no separate step"). Shape:
* Input: <run>/risk_queue.json (already emitted by every build).
* Config block `frontier_review` in driver_config.json: model
  (moonshotai/Kimi-K3), batch: true, slice (top-N by risk, default 150),
  max_cost_usd (hard gate at submit, batch worst-case arithmetic like
  the existing batch gate), parity_n (default 10).
* Stage order: (1) parity sample -- N items judged by BOTH the frontier
  model and the flash seat; divergence rate recorded; a divergence above
  a configured band STOPS the stage loudly (seat-defect doctrine);
  (2) the curated slice, batched via the existing CurlTransport +
  manifest (lossless recovery); (3) verdicts land on
  <run>/frontier_verdicts.json + a disposition summary appended to the
  run's health; items the frontier REJECTS become the fix queue.
* NOT auto-run inside post_build_checks: it spends real money, so it
  requires its own explicit invocation/flag (--frontier --yes), per the
  repo rule that consequential spends prompt. Everything else about it
  is push-button.
* The behavior-pipeline reuses the same stage shape later (frontier
  grading of relevance selections).
Implementation lands with the ds8 fix commit (it shares the batch/gate
plumbing the audit findings touch).

## 2026-08-14: behavior-matching pilot skeleton COMPLETE (offline, $0)

behavior_pilot/ landed: deterministic pilot-behavior miner (5 selected,
overlap stats recorded, labels-direct-attention guard in the artifact),
behavior_match.py (engagement seat blind-on-names/fail-closed,
injectable retrieval with lexical fallback, behavior-module ASP shape,
clingo relevance query), 22 offline tests green, DESIGN.md with the
refinement-loop design + 6 Matt questions. FIRST END-TO-END RESULT:
U18 romantic-roleplay behavior -> 3 atoms -> correct node ranked first
for all three -> matched module pair -> clingo fired 4 asserts and
reported EXACTLY the right conflict (the performed romantic-roleplay
act is forbidden). Honest bound recorded: 15-node coverage (37/593
clauses) makes frontier-recall span-bounded, not matcher-bounded.
Live pilot estimate: ~$0.18-0.25. Matt's 6 open questions in
behavior_pilot/DESIGN.md §6.

## 2026-08-14: budget -> $15.00; fixup + auto-quality-check directives (Matt)

Budget authorization extended to $15.00 total. Directives, wired into
the in-flight ds8 commit as items 14-15: (14) `--golden PATH` / config
`golden_graph`: when set, post_build_checks automatically runs
graph_compare + repair_census + the edge-similarity histogram against
the named golden -- deterministic quality deltas emitted per build;
(15) fixup.py: applies frontier verdicts MECHANICALLY where
deterministic (rejected renames revert to honest danglings; never
in-place -- writes root_graph.fixed.json), and emits fixup_queue.json
for non-mechanical dispositions -- code never makes content decisions.
SEQUENCE once reviews converge to accept: commit -> K3 frontier_review
on ds7 -> fixup round -> auto quality checks vs golden -> DELTA
INVESTIGATION (every delta gets a why, census-style) -> production
package.

## 2026-08-14: ds8 fix set LANDED -- seam guard + F1-F10 + frontier stage + fixup + golden flag

One reviewed change set, all offline-pinned (new pins: test_routing_fixes
25, test_frontier_review 24, test_fixup 11 = 60; every guard fed the
defect it catches). Item -> file:
 1. IDENTICAL-RETRY SEAM GUARD -- translate.py Client._send /
    _vary_identical_retry: sha256 failed-body set; hash-match appends
    "[transport retry N]" to the FINAL user message and re-hashes
    (suffix-only, prefix cache holds); telemetry `retry_variations`.
    Covers guard-raised (TRUNCATED/empty) sends too. GraphClient inherits.
 2. F1 -- dispatch_core._ladder + recurse_driver Driver._complete:
    TRUNCATED joins the 402-style SHORT ladder (2 tries + seam-guard
    variation, then restart paths/raise).
 3. F2 -- translate.py Client._log_usage enforces max_cost_usd after
    billing (CostGateError), as GraphClient does; translate_exec
    _TolerantRunOne propagates CostGateError by name (no per-clause grind).
 4. F3 -- rename_seat.judge raises on terminal transport (402/401/403,
    key resolution) after bounded retries instead of fail-closing.
 5. F4 -- translate.py _send stamps requested_max_tokens; _check_envelope
    raises TRUNCATED on finish_reason-null completions at the cap.
 6. F5 -- oversize threshold reads the ENGAGED per-phase cap:
    DispatchState.out_cap property + Driver.call; the D6 dense/malfunction
    machinery is reachable again (3 fixture cfgs updated to force phase
    caps, not model.max_tokens).
 7. F6 -- "empty response" is transient in both ladders, same 2-retry cap.
 8. F8 -- statusless batch polls ({"error": ...}) become a ProviderError
    after 3 consecutive polls (dispatch_core _poll_and_collect + _sweep).
 9. F9 -- _ladder re-raises CostGateError over the per-dispatch budget
    diagnosis; F10 -- GraveyardError caught BY NAME in translate.main and
    translate_exec.main (cannot subclass Phase1Error: import direction,
    recorded in graveyard.py docstring).
10. F7 (deterministic half) -- per-request max_tokens persisted in the
    flush manifest entry; _sweep rebuilds _req_max for _classify. The
    double-ledger half stays DEFERRED, recorded in a _sweep comment.
11. frontier_review.py -- the K3 stage per the ruling: risk_queue in,
    parity sample (divergence > band = loud ParityStopError), batched
    slice via CurlTransport + frontier_inflight.json record, worst-case
    gate at submit, frontier_verdicts.json + health line out; --yes
    required. Config block `frontier_review` in driver_config.json.
12. Item 13 -- coinage VARIANT pattern widened (ds7 RESIDUALS (a)):
    recurse_driver is_authority_coinage / _AUTH_COINAGE, ONE constant
    consulted by validate_leaf AND autofix_authority_coinages.
13. Item 14 -- golden-flag quality checks: config `golden_graph` /
    --golden runs graph_compare -> compare_vs_golden.json, repair_census,
    and edge_similarity_report (token-Jaccard buckets <0.1/0.1-0.25/
    >=0.25 -> edge_similarity.json) inside post_build_checks. Offline.
14. Item 15 -- fixup.py: mechanical dispositions from frontier_verdicts
    (rejected rename -> revert; upholds -> confirmed; dropped_merge
    confirmation -> no-op) into root_graph.fixed.json (never in place);
    non-mechanical -> fixup_queue.json with reasons + health line.
Also: behavior_pilot/DESIGN.md now labels the U18 romantic-roleplay
example as a hand-written smoke fixture, NOT a corpus behavior.

## 2026-08-14: adversarial review of the ds8 fix set -- 9 findings FIXED

Clean-context review before commit (fired again; right again). Fixed in
the same set, each with a pin:
 1. gate math (HIGH): frontier price default DELETED -- price_per_mtok is
    REQUIRED config (refuse over guess); max_cost_usd 2.50 -> 3.00 (the
    150-slice worst case at the corrected $3/$15 is ~$2.57); the WHOLE
    worst case (parity + slice) now gates BEFORE the parity stage spends
    (run_review, item 1c) -- the old order spent parity money then
    refused at submit.
 2. near-miss semantics INVERTED (HIGH): for dangling_near_miss the
    recorded decision is the NON-rename, so vocab_for maps
    different_concept -> uphold and same_concept -> reject; a rejected
    near-miss is a PROPOSED NEW RENAME on the fix queue (through the
    resolution pass's gate, never auto-applied). fixup dispositions now
    persist as ROWS on frontier_verdicts.json (confirmed + reverted).
 3. double-pay windows: create-kill-window adopt via list_batches
    (dispatch_core doctrine; unlistable -> refuse to resubmit); the
    inflight record is cleared only AFTER frontier_verdicts.json is on
    disk; a passed parity report persists in the record so a resume
    never re-pays parity.
 4. F2 x batch collection: CostGateError from _log_usage is DEFERRED at
    dispatch_core._collect (rows fed/completed first, live reruns never
    start) and _sweep (raise only after _persist_recovered + clear -- no
    dropped rows, no double-ledger on resume).
 5. frontier batch spend LEDGERED: every returned row goes through
    client._log_usage with measured cost at the configured price; a
    ledger gate raise defers until the verdicts persist; no client ->
    loud invisibility warning.
 8. seam-guard marker restricted to the last USER message; a userless
    body is re-sent unchanged (system/assistant turns never mutated).
 9. ParityStopError carries .report (the parity rows).
 INFO (latent): fixup revert refuses when >1 needs share the rename
    target (a genuine need is byte-indistinguishable from the renamed
    one) -- ambiguity queues, code never renames a real edge.
Re-review CONVERGED; two polish items closed in the same set:
 N1: parity no longer fails OPEN on zero decided pairs -- decided <
    min(len(sample), max(3, parity_n//2)) raises ParityStopError with
    the no_verdict evidence in .report (a judge pair that cannot decide
    is as defective as one that diverges); parse_verdict now uses the
    driver's fence-tolerant parse_json_reply, so a markdown-fenced
    frontier reply still decides.
 N2: `ledgered: true` persists into the inflight record BEFORE the
    ledger loop; a resume killed between ledgering and the verdict write
    re-parses for free and makes zero _log_usage calls (double-ledger
    would corrupt usage.jsonl's measurement, the one direction the
    overstate-is-survivable doctrine does not cover).

## 2026-08-14: ds7 FINALE COMPLETE -- frontier review + fixup + quality battery

Committed 51098a0; the chained stage ran end to end, zero interventions.
* PARITY: 0% divergence over 10 decided K3-vs-Flash pairs (band 40%) --
  the flash seat matched the frontier on every sampled judgment, again.
* K3 SLICE (150 items, $1.38, fully ledgered): near-misses 62/64 UPHELD
  (the honest danglings are honest -- absence-over-wrong vindicated at
  frontier tier); seat renames 15/18 upheld, 2 rejected; dropped merges
  16/16 upheld; broken promises 40/45 REJECTED = real defects -> queue.
* FIXUP: 97 confirmed, 1 rename reverted -> root_graph.fixed.json;
  52 non-mechanical items -> fixup_queue.json (dominated by the 40
  broken-promise defects; content-shaped, never auto-applied).
* QUALITY vs GOLDEN (deterministic, auto): 1:1 486; edge similarity
  <0.1 = 7/1011 (0.7%); full compare/census/histogram in runs/ds7.
* Campaign spend: $8.95 of $15.00.
NEXT (the standing directive): DELTA INVESTIGATION -- every golden delta
gets a why; the 52-item fixup queue (esp. the 40 frontier-confirmed
broken promises) is the concrete defect list for the production graph.

## 2026-08-14: delta investigation + K3 validity -- CORRECTION and the one real defect

Reports: delta_investigation.md, k3_validity_report.md. Three headlines:
1. CORRECTION to this log's finale entry: the 40 broken-promise
   "frontier confirmations" carried NO evidence -- frontier_review's
   item_prompt sent name-only for that kind (and no node text for
   dropped_merge), so those verdicts were the reject-default on name
   shape. The underlying defect is real but its evidence is
   investigation B, not the K3 verdicts. Evidence fixes queued (item C).
2. K3 judge verdict: MIXED -- trustworthy where evidenced (frontier
   re-adjudication agreed 6/6 incl. finding the single true pair among
   64 near-misses); the 62/64-uphold pattern is queue saturation
   (embedding candidates uniformly wrong), not rubber-stamping.
3. THE one real ds7 defect: PROVIDES UNDER-EXPORT -- 92 exported names
   vs golden's 230; ~50/64 danglings name content that EXISTS as ds7
   nodes with empty provides. Everything else is measurement artifact
   (raw edge precision 0.050 is 92.7% authority fan-out; excluded:
   precision 0.378) or benign-by-protocol granularity. Delta verdict:
   NOTHING blocks ds7+fixups as production graph once under-export is
   repaired (promise_repair scope extended to both classes) and the
   authority-excluded numbers are the recorded comparison basis.

## 2026-08-14: promise items + evidence fixes LANDED (items A-extended, B, C)

Driven by k3_validity_report.md + delta_investigation.md (both in this
dir). All offline-pinned; suites green; no commit (coordinator stages).
 A. promise_repair.py (new stage, --yes gated, budget
    promise_repair.max_cost_usd default 0.25): targeted leaf redraws for
    TWO classes -- (a) division-promise breaks from fixup_queue
    broken_promise rejects (the class stands on the division's own
    recorded promise; the ds7 K3 "confirmations" of this kind were
    evidence-free defaults and carry no weight), and (b) the
    UNDER-EXPORT scan (delta cause 3, the one real ds7 defect: 92
    provides names vs golden 230): a dangling need whose establishing
    content exists as a node (establishes-overlap >= 0.25, or spans
    containing the seeded established_around) gets the same
    must-provide-or-explain redraw aimed at that node. Mechanical splice
    into root_graph.repaired.json (NEVER in place; provenance rows +
    health line); honest declines recorded in
    promise_repair_report.json; danglings recount with resolved-needer
    counts PER CLASS.
 B. enforce_promise_delivery (validate_leaf, default false for
    byte-parity; true in driver_config for future builds): an inherited
    seed established INSIDE the leaf's span must be provided under
    exactly its name or declined in judgment_calls naming the seed --
    cover-or-explain, wired through BOTH Driver.leaf and the core
    _want_leaf (the D1 one-path lesson). ds8 prevention of the
    45-broken-promise class.
 C. frontier_review evidence fixes (k3_validity_report): item_prompt now
    ships REAL per-kind evidence from an Evidence context
    (root_graph.json + document lines) -- rename kinds get the seat's own
    build_prompt with span text (the BRIEF promised it; the prompt never
    carried it), dropped_merge both nodes' claims+text, broken_promise
    the seed prose + covering-node texts, low_sim_edge both sides;
    unconstructable evidence RAISES instead of defaulting; grounds cap
    400 -> 1200; the module docstring records that ds7 first-slice
    dropped_merge/broken_promise verdicts carry no evidentiary weight.
New pins: test_promise_repair 13 (items A+B), test_frontier_review 30
(+6 evidence pins), totals: routing 25 + frontier 30 + fixup 11 +
promise 13 = 79.

## 2026-08-14: promise_repair re-review -- 6 findings FIXED before commit

Re-review verdict: items B + evidence-content sound; promise_repair prep
was not. Fixed, each pinned:
 1a. GLOBAL already-provided filter at prep (ds7: scope_of_autonomy et
     al, 3/26 queue names stale) -- skipped_already_provided report rows,
     zero spend.
 1b. Target/ea coherence (4/23 ds7 candidates incoherent): an
     overlap-picked target derives the redraw location FROM ITS OWN SPAN
     and the stale seed ea is dropped -- never redraw an ea leaf to
     splice a distant node.
 1c. Prep-time splice feasibility (redraw-leaf and target-side span
     checks BEFORE spending; infeasible -> report rows, $0) with +-2
     containment tolerance (flagship: interactive_vs_programmatic, ea
     [3384,3386] vs nodes starting 3386).
 1d. Per-name dedupe in the promise class (chain_of_command_principle x6
     -> one plan).
 2n. Decline matching is word-boundary (recurse_driver.name_mentioned,
     used by validate_leaf AND the splice decline lookup):
     support_mental_health_rule no longer declines support_mental_health.
 4.  _no_evidence aligned on both paths: judge_item builds the prompt
     OUTSIDE the transport loop and returns a no_verdict row "evidence
     unconstructable: <why>" (never a transport label); the batch slice
     excludes such items AT PREP with report rows (excluded_no_evidence
     on the artifact) -- the stage never aborts on one.
 5.  promise_repair.max_cost_usd 0.25 -> 0.40 (~$0.0084/plan x ~31 +
     headroom); repair rounds deliberately NOT multiplied into the gate:
     the measured ceiling (client.max_cost_usd = the stage budget,
     enforced at _log_usage per routing-gap F2) backstops overruns
     mid-flight -- rationale recorded at the gate.
 3n. RULING recorded in validate_leaf: boundary-straddling seeds (ea
     crossing a leaf boundary) are owed by NO leaf -- accepted gap; the
     division-level broken_promises check catches them post-unwind.
Pin totals: routing 25 + frontier 32 + fixup 11 + promise 20 = 88.

## 2026-08-14: final 1c displacement CLOSED (last blocker for the paid run)

promise_repair splice-target selection factored into ONE function
(`_select_target`) used by BOTH the prep feasibility check and splice's
promise-class branch: EXACT-cover nodes first (no tolerance), +-2
fallback only when none exist; ties by maximum line-overlap with
[ea0, ea1], then narrowest span -- NEVER graph order (the ds7 flagship:
ea [3384,3386] with adjacent L3239-3382_n017 present now selects
L3383-3501_n001; do_not_facilitate ea 1543 selects exact L1542-1706_n001
over the adjacent [1523,1541]). DEFAULT_BUDGET fallback 0.25 -> 0.40 to
match config. Pins: promise 24 (4 new); totals routing 25 + frontier 32
+ fixup 11 + promise 24 = 92.

## 2026-08-14: promise-repair set CONVERGED (3 review rounds) -- committed

Final round closed the 1c displacement (exact-first _select_target, both
call sites, pinned with the reviewer's own ds7 reproduction cases).
92 pins across the fix-set files; graph_v2 232, phase_1 800 green.
NEXT (in order, the standing runbook): (1) Opus-subagent recheck of the
61 quarantined evidence-free verdicts using the corrected item_prompt
(zero project spend); (2) promise_repair.py runs/ds7 --yes (simulated:
29 plans, $0.244 worst case vs $0.40 gate); (3) danglings recount +
quality battery on root_graph.repaired.json; (4) production-graph
package. Budget $8.95 of $15.00 at this entry.

## 2026-08-14: OPUS RECHECK of the 61 quarantined verdicts ($0) -- ledger rewritten

opus_recheck.json + opus_recheck_report.md. With real evidence: 29 of 57
K3 name-only verdicts FLIP (broken_promise agreement 29%; dropped_merge
16/16 stands on assignment-vs-definition grounds). REAL broken-promise
defects: **14 of 45** (13 names, all instances of provides under-export;
no document content missing). One flip in the unsafe direction (K3's
lone uphold was wrong) -- the quarantine is fully vindicated. The finale
entry's "40 real defects" is corrected to 14.
PLAN ALIGNMENT: 4/9 promise plans clean; 5 misaligned (would duplicate
same-referent exports or splice onto [?](#anchor) CITATION SITES -- a
displacement class _select_target cannot catch); 1 under-export plan
(minors ea 4576 vs establishment L826) same class; 5 confirmed defects
have NO plan (section-name seeds without established_around).
RULING: promise_repair does NOT run until prep gains (1) same-referent
already-provided matching, (2) the citation-site guard (skip/re-aim
plans whose ea sits inside a cross-reference), (3) plans for the 5
unplanned confirmed defects (target by section heading line). The
evidence-confirmed 14 + Opus verdicts are the repair scope, not the 45.

## 2026-08-14: promise_repair PREP GUARDS 1-3 LANDED (the OPUS RECHECK ruling)

The three guards the recheck ruling made a precondition for spending are
in `promise_repair.py`, each pinned RED-first against the defect it
catches (fixture document; the real `model_spec.md` was read-only
evidence only).

1. **Same-referent already-provided** (`skipped_same_referent`) --
   `same_referent_provider()` extends the exact-name filter to the
   REFERENT: an existing provides entry whose prose overlaps the seed's
   by >= 0.5 tokens (`risk_queue.sim`, imported not copied) or contains
   it verbatim (case/whitespace-normalised) already exports the concept.
   ds7: 4 promise plans dropped, incl. the flagship
   `authority_level_ordering` -> `authority_levels_hierarchy`
   (L1-170_n042, verbatim, sim 1.0), plus `section_authority_level` and
   `user_authority_section_rules` -> `user_authority`, and
   `assume_best_intentions_section` -> `implicit_biases` (sim 0.6).
2. **Citation-site re-aim** -- an `established_around` line whose
   markdown cross-reference names the seed's OWN anchor
   (`see [?](#avoid_overstepping)`, `[restricted](#restricted_content)`)
   is not an establishment site; the plan is re-derived from that
   anchor's own section heading, or dropped as
   `skipped_citation_site_unresolved` when the document has no such
   heading. ds7 re-aims: `avoid_overstepping` 1422 -> **3239**,
   `avoid_info_hazards` 1373 -> 856, `restricted_content` 1371 -> 852,
   `transformation_exception` 814 -> 1369, and (under-export class, the
   same one resolver) `sexual_content_involving_minors_section`
   4576 -> **826**.
3. **Section-heading fallback** -- a seed with no usable
   `established_around` derives one by slugging its own name (stripping a
   trailing `_section`) and locating that section's heading. GENERAL, no
   name hardcoded. This plans all five confirmed defects the recheck
   found unplanned: `control_side_effects_section` L527,
   `risk_taxonomy_section` L53, `red_line_principles_section` L28,
   `refusal_style_section` L4073, `letter_and_spirit_section` L292.

**RULING (found on the dry run, recorded here rather than in the
transcript):** a RE-DERIVED establishment is descended from the **run
root**, not from the unwind that promised the name. The alternative --
"keep descending the promising unwind" -- is rejected BY NAME: the
document establishes `avoid_overstepping` at L3239 while the promising
unwind spans [1368, 1541], so that route fails with "no child span
covers line 3239" and the guard buys nothing. A seed's OWN ea keeps the
pre-guard route (its unwind promised it there).

Second ruling: `is_citation_site` is deliberately NARROW -- the
cross-reference must name the seed's own slug. A line citing some other
anchor still counts as an establishment site. Rejected by name: "re-aim
at whichever anchor the line cites", which would have this file make a
content decision about what a passage is really about.

Optional config `promise_repair.opus_verdicts` (a path; **absent in
`driver_config.json`, so committed behaviour is unchanged**) intersects
the broken_promise rows with an `opus_recheck.json`-shaped file's
`opus_decision == "reject"` names -- the evidence-confirmed scope the
ruling asks for. Setting it is a spend decision left to the human.

DETERMINISTIC PREP on runs/ds7 ($0, no `--yes`, shadow run dir; nothing
under `runs/` written):

| | plans | promise | under-export | gate worst case vs $0.40 |
|---|---|---|---|---|
| guards, `opus_verdicts` absent | **36** | 18 | 18 | **$0.30** ✅ |
| guards + `opus_verdicts` | **29** | 10 | 19 | **$0.25** ✅ |
| (pre-guard, for reference) | 29 | 9 | 20 | $0.244 |

Skips, `opus_verdicts` absent: 3 `skipped_already_provided`, 4
`skipped_same_referent`, 0 `skipped_citation_site_unresolved`, and 1
promise name still unlocatable -- `information_hazards_section`, whose
slug names no heading (the document's anchor is `#avoid_info_hazards`);
the fallback correctly declines to guess. 4 `reaimed_citation_site` + 11
`section_heading_fallback` re-derived. With `opus_verdicts`: 15
`skipped_not_opus_confirmed`, 1 `skipped_same_referent`, 1 + 6
re-derived (promise) and 1 re-derived (under-export).

Pins: promise 24 -> **37** (13 new); graph_v2 suite 232 -> **245**.

## 2026-08-14: standing directive -- translation is DRIVER-RUN, after graph validation

Matt: the translation pipeline is to be driven by the coordinating
instance (not handed to an external agent) once the graph is FULLY
VALIDATED. TRANSLATION_RUNBOOK.md therefore serves as the checklist the
driver follows, not as a hand-off package. Ordering is binding: no
corpus translation until the ds7 repair + verification cycle closes and
the production-graph package is signed. Two known blockers to clear
first, both recorded: (a) stage-4 seats have NO config-driven
client_factory anywhere in the repo -- writing that seam is a DESIGN
decision (4c's anchor property is enforced by the absence of a
rendering parameter), Matt's to rule on; (b) the documentation-truth
pass (RUNBOOK_AUDIT.md: translate.py's banner still claims it validates
nothing; node_corpus.py's usage lines are wrong; READBACK_SMOKE/
BATCH_DESIGN stale). Corpus-scale translation spend (~$1.5-3) needs its
own authorization at the time.

## 2026-08-14: prep-guard convergence review -- NO-GO (2 blockers), fix round out

Guard 2 (citation re-aim) and the run-root ruling CLOSED with strong
evidence: all 5 ds7 re-aims verified line-by-line to genuine
establishing headings; 80/80 document anchors unique; 12/15 re-derived
plans fail under the promising-unwind route while the 3 that succeed
return the identical leaf -- the ruling fixes avoid_overstepping and
breaks nothing. opus_verdicts intersection CLOSED: all 13 confirmed
names planned or accounted; duplicate-export plans drop 8 -> 1 with the
key set (RECOMMENDED configuration).
BLOCKERS: (B1) guard 1 false-skips the confirmed defect
`user_authority_section_rules` -- the document's per-section authority
TEMPLATE scores 0.545 Jaccard between ANY two such claims, so the 0.5
threshold has no discriminating power and the guard has no locality
constraint; a false skip silently keeps a defect. (B2, corrupting) both
re-aim guards emit a single-line heading ea, so _select_target
systematically picks the authority-ASSIGNMENT node (heading-line span)
over the substantive empty-provides node that IS the under-export --
5/8 (key set) or 11/15 (absent) re-derived splices land wrong,
including two on off-by-two commentary nodes chosen by graph order.
That would merge assignment with definition, contradicting the standing
ruling the 16/16 dropped_merge upholds rest on, AND spend money doing
it. Fixes dispatched: locality-constrained referent matching (also
extended to the under-export class), section-BODY establishment ranges,
and an authority-class decline in target selection. Re-run $0 prep +
re-adjudicate targets, then GO with opus_verdicts set.

## 2026-08-14: convergence review NO-GO -- B1 + B2 FIXED, prep re-adjudicated

The adversarial convergence review returned NO-GO with two blocking
findings. Guard 2's re-aim logic and the run-root ruling were confirmed
CLOSED (5/5 re-aims verified line-by-line, 80/80 anchors unique, 12/15
plans fail under the unwind route). Both blockers are fixed, each pinned
RED first on the reviewer's own reproduction cases.

**B1 -- guard 1 produced a FALSE SKIP of an evidence-confirmed defect.**
`same_referent_provider` now requires LOCALITY: the providing NODE must
cover the seed's establishment lines (`_node_covers`, the shared +-2
tolerance). Mechanism confirmed: the document states per-section
authority in a fixed TEMPLATE, so `risk_queue.sim` scores **0.545 for
any two such claims regardless of section** -- the 0.5 threshold has no
discriminating power on that shape. `user_authority_section_rules`
(ea 3150, the `#avoid_errors` heading) was being skipped against
`user_authority` on `L3239-3382_n001`, a different section 89 lines
away. Both correct skips already satisfy locality and still fire
(`L1-170_n042` covers ea 69; `L3505-3953_n001` covers ea 3506). Guard 1
now runs AFTER guards 2+3, since locality needs the RESOLVED
establishment. Without a usable ea the guard declines to fire: it must
never skip a real defect on prose resemblance alone.

**B2 -- the corrupting one: re-derived splices landed on authority
ASSIGNMENT nodes.** Both halves fixed.
* (a) `resolve_establishment` now returns the section BODY --
  `section_span()`: heading through the line before the next heading of
  the same-or-higher level, capped at `SECTION_MAX_LINES = 120`, then
  clipped to the redraw leaf by `_clip_ea` (a seed whose ea straddles the
  leaf boundary is owed by NO leaf, so the redraw would never be told
  what it owes).
* (b) `_select_target` gains ONE documented mode switch, `section=True`,
  passed identically by the prep feasibility check and by `splice`. It
  admits only nodes whose span STARTS inside the body (no tolerance, so
  the commentary two lines ABOVE the heading is out), DECLINES an
  authority-assignment node (`_is_authority_assignment`, riding
  recurse_driver's own `AUTHORITY_CANONICAL` + `is_authority_coinage` --
  one source), and ranks EARLIEST-then-narrowest. No admissible
  candidate reports rather than splicing.

This restores the repo's standing assignment-vs-definition ruling (the
16/16 `dropped_merge` upholds) inside the repair stage: a section's
substance may not be spliced onto its authority label.

**RULING (review B3, second arm).** The under-export class is DEFINED --
module docstring, delta_investigation cause 3 -- as a dangling whose
content exists as a node with EMPTY provides. A plan whose elected target
already exports SUBSTANCE (a non-authority name) is therefore a duplicate
by the class's own contract and is skipped. This was needed because the
prose filter cannot see the residual the reviewer named:
`sexual_content_involving_minors_section` vs
`sexual_content_minors_prohibition` scores **0.364** against the 0.5
threshold. REJECTED BY NAME: lowering the prose threshold to ~0.36 to
catch it -- tuning a floor until one case passes is exactly what produced
B1's false skip. The arm is scoped to the under-export class: promise
plans stand on a recorded division promise and legitimately aim at nodes
exporting adjacent names.

DETERMINISTIC PREP on runs/ds7 ($0, no `--yes`, shadow run dir; nothing
under `runs/` written):

| | plans | promise | under-export | skips | worst case vs $0.40 |
|---|---|---|---|---|---|
| `opus_verdicts` absent | **37** | 19 | 18 | 3 already-provided, 3 same-referent, 1 failed | **$0.31** ✅ |
| `opus_verdicts` set | **29** | 11 | 18 | 15 not-opus-confirmed, 1 same-referent | **$0.25** ✅ |

Every re-derived target re-adjudicated against the document; all seven in
the `opus_verdicts` scope land on the first substantive claim under their
heading: `avoid_overstepping` -> `L3239-3382_n002` (L3241),
`red_line_principles_section` -> `L1-170_n017` (L30),
`risk_taxonomy_section` -> `L1-170_n033` (L55),
`control_side_effects_section` -> `L461-608_n013` (L529),
`letter_and_spirit_section` -> `L171-426_n029` (L294),
`support_mental_health` -> `L1707-1973_n008` (L1753),
`refusal_style_section` -> `L3954-4251_n018` (L4075). The magnet node
`L171-426_n004` and both off-by-two commentary nodes are gone.

RESIDUAL, recorded not fixed: `refusal_style_section`'s target already
exports `safe_complete_rule`. It is the correct first claim of
`#refusal_style` and Opus confirms nothing refusal-style is exported, so
the plan stands -- and the redraw's own deliver-or-explain escape hatch
is the check, not more prep heuristics. `opus_verdicts` ABSENT still
plans 4 same-referent duplicates Opus upheld (`avoid_info_hazards`,
`restricted_content`, `transformation_exception(_section)`,
`protect_privacy_section`); that is the reject-default over-breadth the
intersection exists to remove, and it is why the paid run should set
`opus_verdicts`. The key remains ABSENT in `driver_config.json`: setting
it is a spend decision for the human.

Pins: promise 37 -> **49** (12 new); graph_v2 suite 245 -> **257**.

## 2026-08-14: prep guards CONVERGED -- GO with opus_verdicts SET

Independent verification closed B1 (locality constraint, not a threshold
tweak -- user_authority_section_rules recovered, targeting L3147-3238_n001
@L3152 empty-provides; the correct verbatim skips still fire), B2 (section
BODY establishment + section-mode selector declining authority-assignment
nodes by name; 7/7 re-derived targets independently adjudicated to the
document's first substantive claim, 6/7 empty-provides; _clip_ea proven
unable to empty a range; the authority-decline proven unable to reject an
authority+substance node), and B3 (the under-export class's own
empty-provides contract instead of lowering a threshold to 0.36 -- the
by-name rejection endorsed). 13/13 confirmed defects planned in both
configs. 257 graph_v2 / 800 phase_1 green; runs/ byte-identical (1110
files shasum'd).
RULING: run with promise_repair.opus_verdicts SET. Key absent = 37 plans
of which 8 write DUPLICATE exports into the accepted graph (equivalent
referents already exported: avoid_info_hazards, restricted_content,
transformation_exception(_section), protect_privacy_section, minors) and
pays for them. Key set = 29 plans, $0.25 vs the $0.40 gate, 0 upheld
names planned. Residuals recorded not blocking: earliest-first can pick a
lead-in paragraph (2 instances, both outside the set scope); same-span
ties fall to graph order (n017/n018 at L30, same sentence); slug
first-wins is document-specific (80/80 anchors unique here).

## 2026-08-14: ds7 REPAIRED + verification battery

promise_repair (opus_verdicts scope) ran clean: 26 repaired, 3 honestly
undeliverable, 0 failed; ~$0.22. Before -> after: exported names 92 ->
118, danglings 66 -> 24 (43 needers resolved: 20 promise-class, 23
under-export), need-edges 1077 -> 1088, nodes unchanged 773, mismatched
(<0.1) 7 -> 8. Edge recall vs golden 0.369 -> 0.440. The identical-retry
guard and truncation short-ladder both FIRED LIVE during the run and it
completed instead of wedging -- first real outing for both.
Battery on runs/ds7_repaired (staged copy): graph_check OK (0 bad spans,
0 bad quotes), sweeps OK, risk_queue 162 items, edge_similarity 8/1064
below 0.1. (repair_census errors on the staged dir by design -- no
failed/ history there.)
MODAL ADJUDICATION (the last outstanding ds7 check, run-local per the
risk-queue contract): 6 of 45 flags are REAL obligation-strength drift
(~0.8% of nodes, same rate as ds6's 6/31) -> modal_adjudication.json,
now feeding the risk queue.
Verification of splice integrity + delta re-investigation vs golden
dispatched (repaired_verification.md).

## 2026-08-14: repaired-graph verification -- NOT FIT, corrected -> PRODUCTION CANDIDATE

repaired_verification.md (independent, $0) returned NOT FIT: 19 of 26
splices clean, 3 accept-with-reservation, **4 REJECT** -- most seriously
`assume_objective_pov` spliced onto a node whose prose asserts the
NEGATION of the document's #assume_objective_pov (a FALSE CLAIM in the
graph), plus two wrong-section splices and one whose claim lay outside
the receiving node's spans. Also: 3 new self-loops, 1 need introduced by
the repair, and the decline count mis-booked (2 honest, not 3 --
support_mental_health's reason says "I will add a provides entry" and
then didn't). Mechanically the splice was clean: 773 nodes both sides,
ids byte-identical, ONLY provides/needs touched, 0 new duplicate names,
36 golden edges newly matched with the unmatched set a strict subset.
CORRECTIONS APPLIED deterministically -> runs/ds7/root_graph.production.json
(never in place; every correction verified before applying and recorded
on the artifact as verification_corrections): 3 wrong-claim splices
REVERTED; voice_style_guidelines RE-AIMED n001 -> n003 after verifying
n003's spans actually cover L4260; the introduced need renamed to the
provided name. Result: 115 exported names, 26 danglings, 773 nodes.
Battery on runs/ds7_production: graph_check OK (0 bad spans/quotes),
sweeps OK, risk_queue 168, edge_similarity 8/1062 below 0.1, recall vs
golden 0.4395 (authority-excluded pre-repair 0.177/0.378 -> post
0.264/0.442; content edges 196 -> 242).
DELTA STATUS: the remaining real class is the SAME predicted one --
content-edge under-export, now enumerable (~160 edges; exemplars
#do_not_lie, #avoid_errors, #avoid_sycophancy, #uphold_fairness,
#respect_real_world_ties, #do_not_encourage_self_harm -- sections where
golden exports 2-9 names and ds7 exports 0). Verifier's other finding
worth keeping: 86 of golden's 230 names are dead (58 never needed) or
superseded-by-convention (28 coinages), so the honest comparison is
101 vs 153 LOAD-BEARING content names.
NOT YET RE-VERIFIED: the corrected artifact needs one more independent
pass before it is signed as production.

## 2026-08-14: pipeline-fix thread -- validation + review required before close

The four fixes from repaired_verification (splice adjudication seat,
narration-mismatch check, self-loop check, run checkpoints) do NOT close
on the builder's report: validate-then-adversarially-review applies, as
to every substantive change. DEPENDENCY SPLIT recorded because it
governs sequencing:
* FIX 4 (checkpoints, translate_exec.py) is ON the translation critical
  path -- the corpus run uses that loop. It must be validated AND
  reviewed before the translation run starts.
* FIXES 1-3 (splice seat, narration mismatch, self-loops, all in
  promise_repair.py) gate any FUTURE repair run, not translation and not
  the current certification: the production candidate's 26 splices were
  adjudicated item-by-item by an independent frontier pass, which is a
  stronger check than the seat gate would have been. The thread stays
  OPEN until reviewed; it simply does not block the corpus run.

## 2026-08-14: the four repaired_verification fixes LANDED (unreviewed)

Built and pinned RED-first; the thread stays OPEN per the entry above
(validation + adversarial review still owed). Nothing under `runs/` was
written -- the ds7 prep re-check ran on a scratchpad copy.

**FIX 1 -- splice adjudication seat (`splice_seat.py`, new).** The root
cause: every promise_repair guard answers WHERE to aim a splice (span
coverage, citation sites, authority-assignment nodes, same-referent
duplication); NOTHING asked whether the receiving node's CONTENT
establishes the concept, and 4 of ds7's 26 splices were wrong claims
with every mechanical guard satisfied. The seat is `rename_seat.py`'s
discipline applied to establishment: BLIND ON NAMES (concept prose +
the receiving node's `establishes` and span text, never the predicate
name), forced-binary `{"verdict": "establishes"|"does_not_establish",
"grounds"}`, fail-closed to does_not_establish on any unparseable or
uncertain reply, with rename_seat's CostGateError and terminal-transport
(402/401/403, key resolution) carve-outs verbatim. The brief's
load-bearing sentence: a passage that NEGATES, contradicts, or merely
MENTIONS/comments on the concept does not establish it -- only one that
defines, asserts or introduces it does (R1 was a negation on a
`!!! meta "Commentary"` line; R2/R4 were real concepts established one
node or 1,300 lines away). Wired into `promise_repair.splice` as the
LAST gate before the graph is touched: `rejected_by_splice_seat` rows
carry the grounds and change nothing. Config
`promise_repair.splice_seat` DEFAULTS TRUE -- a correctness gate, not a
flag; the calls ride the stage's existing client and budget.

**FIX 2 -- narration mismatch.** `support_mental_health`'s decline
ended "I will add a provides entry to n007 ..." and added none; the
stage booked it as one of "3 honestly undeliverable". `asserts_delivery`
matches future/past delivery phrasing sentence-by-sentence, requires the
sentence to be about the entry, and excludes negated forms, so an honest
decline that says what it declines to do stays one. A reason that
asserts delivery with no entry is `narration_mismatch`, counted as a
FAILED repair and never as a decline.

**FIX 3 -- self-loops.** The receiving node's need for the name it now
provides is dropped (a node cannot depend on itself; ds7 made 3, and
each counted as a "resolved" needer), redraw needs naming the concept
are not spliced, and the report carries a graph-level
`self_loops_before/after` census plus `self_needs_dropped`.

**FIX 4 -- run checkpoints (`run_checkpoint.py`, new; Matt's
directive).** `checkpoint_every` (default 25, 0 disables) and
`checkpoint_pause` (default FALSE -- a non-interactive run must not
wedge), read from a stage section before the config root. Every N items
the run prints and appends to the run's `health.jsonl`: done/remaining,
spend vs ceiling, failures BY CATEGORY, graveyard open entries. Honoured
in `translate_exec` (ticked inside `RunContext.finish`, AFTER the
artifact and run.json flush; pause returns exit 3) and in
`promise_repair` (after the report row is booked and the splice is in
the graph copy). ⛔ The invariant is "never loses work": both pause pins
assert the finished items' artifacts are on disk and the unstarted ones
were never paid for, and the translate pin re-runs the remainder and
byte-compares the union against one unpaused run.

Pins: +30 `test_splice_seat.py`, +9 `test_run_checkpoint.py`; 25 of the
30 and 4 of the 9 verified RED against the pre-fix files (the rest pin
the new modules themselves). `test_promise_repair.py`'s 49 pins now run
under the production default via a seat-satisfying client whose seat
calls are counted separately, so every existing spend assertion keeps
its meaning. graph_v2 279 -> **318**; phase_1 (excl. resolve_runs) 800,
1 xfail.

$0 PREP RE-CHECK on a scratchpad copy of runs/ds7 (redraw replaced by a
raiser; no model call): plans and gate are IDENTICAL pre-fix and
post-fix -- `opus_verdicts` SET **29 plans (11 promise / 18
under-export), worst case $0.25**; ABSENT 37 (19/18), $0.31; seat calls
0 in both, because the seat gates the SPLICE, not the PLAN. (Both sides
differ from the 2026-08-14 prep table -- 29 as 10/19, 36 plans absent --
by one promise plan that the table recorded as `skipped_same_referent`;
the drift is in the run dir's inputs since that table was written, is
present identically with the pre-fix file, and is NOT caused by these
fixes.)

## 2026-08-14: production certification CERTIFIED-WITH-CONDITIONS -> conditions applied

production_certification.md: the 5 corrections were "exactly right, and
exactly incomplete". Confirmed correct (all 5 verified against the
document, 0 collateral change, 0 splices rejected out of 12 deeply
re-adjudicated, delta reproduces, no golden coverage lost). MISSED:
(C1) the R2 revert left the repair-fabricated NEED behind -- a latent
false premise the moment an aliasing pass resolves it; (C2) the R4
re-aim MOVED a self-loop rather than removing it; (C4) the corrections
were an ad-hoc command, not a script -- outcome verified, process not
reproducible (a REPRODUCIBILITY.md violation); (C5) stale report counts.
CLOSED: graph_corrections.py (new, committed) applies every adjudicated
correction deterministically with per-correction PRECONDITIONS that
refuse rather than guess; rerunning it reproduces the production graph.
C1 and C2 applied. NEAR-MISS CAUGHT IN-FLIGHT AND RECORDED: the first
self-loop sweep was general and removed 19 loops -- 16 of which PRE-DATE
the repair and are accepted, never-adjudicated content. Scoped to
repair-introduced loops only (verified: original 16, production 16,
introduced remaining 0). The lesson is the campaign's oldest: a fix's
scope must be the adjudicated finding, not the class it belongs to.
PRODUCTION CANDIDATE now: 773 nodes, 115 exported names, 1085 needs,
25 danglings, 0 repair-introduced self-loops; battery green (0 bad
spans/quotes, risk_queue 168, edge_similarity 8/1060 <0.1, recall
0.4395). C5 (stale report counts: says 24 danglings / 3 honest declines,
actual 25 / 2) and C3/C6 remain RECORD-ONLY.

## 2026-08-14: STAGE-4 ADVERSARIAL DESIGN REVIEW -- skeleton sound, accounting not

STAGE4_DESIGN_REVIEW.md (13 findings, all RUN not argued). Verdict: the
four-blinding skeleton is SOUND and should be kept; the evidential
accounting built on it is not. Build the factory (nothing in the seat
design blocks it); do NOT run corpus-scale.
* F1 (CRITICAL): the evidential output collapses to ONE seat. RB4's
  non-evidential stamp is keyed on the CLAUSE MEAN, so it fires on 0% of
  the corpus while 6.6% of items sit at per-item echo >=0.90 (the seats
  comparing the clause to itself); 3/12 modules carry
  readback-check-failed, voiding all 4b/4d verdicts; 4d's stage-3
  cross-check is UNWIREABLE (4d keys on claim sentences, ClaimCoverage on
  claim IDs). Only 4c is countable.
* F2 (CRITICAL): §6.2's independence premise is FALSE for 48% of 4c's
  denominator -- _item_text shows 4c a concept as "the term X means:
  <gloss>" while 4b's rendering IS that gloss verbatim. The anchor does
  not survive a WRONG gloss: the repo's own measured failure mode #4
  (7.5%) passes all four seats.
* F3 (HIGH): a layer-1 rendering cannot reach 4b/4d -- _MODULE_PATTERNS
  inherits ":-" from probe._DISCLOSURE, so an admitted layer-1 rule is
  refused as a disclosure attack and kills the whole clause. Latent
  today (0/121), live the moment layer-1 constructs are used.
* F4: judge has NO reply hardening -- 5 of 7 realistic live shapes raise
  uncaught exceptions; every mock returns clean json.dumps (the
  mock-vs-live gap that the single live 4b call already demonstrated).
* F5: the coverage rule lives only in judge -- a zero-seat run returns
  routing "none", byte-identical to a clean pass.
* THE STRUCTURAL GAP none of the four catches: UNDER-READING the clause.
  4d is denominated on mod.claims -- the TRANSLATOR'S OWN reading -- so a
  translator that reads 3 of 5 claims and encodes all 3 passes
  unanimously. No seat is denominated on the DOCUMENT.
* COST: §7 mandates frontier until parity is measured; frontier at 750
  modules = $651 worst / $87 likely vs $6.44 ledger remaining. Stage 4
  at corpus scale is NOT AFFORDABLE as specified.
FACTORY SPEC delivered (signature takes ONLY seat name + config; the
absent rendering parameter IS the mechanism -- passing plan/readback for
sizing or logging puts the rendering in lexical scope at 4c's call site,
and _refuse runs at prompt construction only). Two changes belong in
seats.py not the factory: defensive reply parsing in judge, and
run_clause recording a skipped seat instead of `continue`.
NEXT STEP RULED: a <=10-clause FLASH pilot (~$0.05) whose deliverable is
reply-shape measurements and the unclear rate -- NOT a faithfulness
result. Stage 4 is its own project after the corpus translation.

## 2026-08-14: pipeline-fix review -- CORRECTION to this log + 4 defects

RECORD CORRECTION (my parenthetical above, on the 11/18-vs-10/19 prep
split, was WRONG on two counts and is superseded): it said "one promise
plan" (it is TWO, which cancel -- hence the unchanged total 29) and
blamed "the run dir's inputs" (git-verified byte-identical; the
concurrent commits touched no prep input). The reviewer REFUTED my
guard-reordering hypothesis too, by ablation: reverting the ordering
alone changes nothing. TRUE CAUSE: commit 3d549e7's two changes -- the
B1 locality constraint and the B3 exports-substance arm --
moving user_authority_section_rules INTO the promise class and
sexual_content_involving_minors_section OUT of under-export. Totals and
gate unaffected ($0.2452 either way). The earlier 10/19 table needs no
correction: it was accurate for the code of its time.
REVIEW RESULT: FIX 3 fully CLOSED; FIX 1's gate placement + fail-closed
CLOSED (every reply shape enumerated); FIX 4's record-only path traced
correct end to end; the 49 promise pins verified to still mean redraws.
DEFECTS, fix round dispatched:
* 4a BLOCKING (and it blocks exactly what Matt asked for): a pause in
  BATCH mode discards already-paid collected rows -- sched.complete sits
  INSIDE _collect's loop before the gate/poison deferrals, so a
  CheckpointPause aborts routing; ~725 paid rows would be lost and
  re-paid on a 750-item run at every=25, and the fresh-outdir-per-run
  design puts them beyond orphan recovery. CheckpointPause needs the
  same collect-then-raise deferral CostGateError already has.
* 2: asserts_delivery FALSE-POSITIVES on honest declines that quote the
  instruction ("I was asked to add a provides entry but the span does
  not establish it") -- the negation search is confined to a <=3-word
  window and the splitter ignores commas/dashes. It now overstates
  failures on the same honesty metric it was built to protect.
* 1b: seat calls sit OUTSIDE the up-front cost gate, and a late
  CostGateError discards every splice already made.
* 4b: the resume hint is false (prep reads the ORIGINAL graph, so a
  resumed run re-pays every plan) and pause exits 0 under set -e.
BINDING CONDITION until 4a lands: checkpoint_pause must stay FALSE for
any batch run. Record-only checkpoints are safe today.

## 2026-08-14: ds7 PRODUCTION GRAPH -- CERTIFIED

production_certification.md addendum: CERTIFIED-WITH-CONDITIONS converts
to **CERTIFIED**. Independent closure check verified all four:
(1) the diff repaired->production is EXACTLY the adjudicated corrections
plus C1/C2 -- 6 nodes / 9 field changes, every one attributable, 0
spans/establishes/ids touched, 773 nodes, ids list-identical;
(2) C1/C2 complete with no third leftover -- all 14 repair-introduced
needs re-derived and checked, the 11 survivors legitimate (incl. one the
certifier ruled should STAY: user_authority on L2126-2404_n031, since
L2151 sits under #assume_objective_pov authority=user);
(3) THE NEAR-MISS WAS REAL and the scoping fix is right: original 16
distinct self-loops, production 16, set-equal, repair-introduced
remaining 0, pre-existing wrongly removed 0 -- a general sweep would
have deleted 16 never-adjudicated needs, the exact unadjudicated-edit
class the repo forbids;
(4) graph_corrections.py's preconditions REFUSE by execution, four ways
(original input, double-apply, moved span, unprovided rename target) --
hard SystemExit before any write, cardinality-checked so an absent name
cannot pass as a no-op; rerunning reproduces the artifact BYTE-FOR-BYTE
(C4 closed).
FINAL: 773 nodes | 115 exported names | 1085 needs | 25 enumerated
danglings | 16 pre-existing self-loops | graph_check 0 bad spans, 0 bad
quotes | 0 new duplicate providers | uncovered byte-identical | recall
vs golden unchanged to 4dp (0.4395 raw / 0.2637 content) with content
precision UP 0.4458 -> 0.4496 -- the two dropped self-edges removed no
golden coverage.
OPEN AS FOLLOW-UPS, NOT GATES: C3 three reservation proses (overreach /
name mismatch, none false); C5 stale promise_repair_report counts
(declined_honestly 3->2, danglings_after 24->25); C6 consumer-side
assertions (unresolved need = hard reportable; carry the 6 modal_drift
nodes with the two teen-safety ones called out; report the honest
authority-excluded pair 0.264 / 0.450).
THE PRODUCTION GRAPH IS runs/ds7/root_graph.production.json.

## 2026-08-14: FULL-CORPUS TRANSLATION -- setup (Matt's directives)

Budget raised to $20.00 (Matt +$5). Certification complete, so the run
is gated only by setup. Config (config_graph_nodes.json, regenerated
against runs/ds7/root_graph.production.json):
* corpus 15 -> 773 rows (the whole certified graph); the regeneration
  also closes RUNBOOK_AUDIT gap 1 (the orphan-prompt guard now knows all
  37 non-prompt .md files -- the documented command failed out of the box
  before this).
* cost ceiling 1.0 -> 8.0 with an honest note: MEASURED rate is
  ~$0.004/node (run 8) -> ~$3.1 expected; the unbounded worst case
  (~$40 at 5 attempts x the out-cap) is deliberately NOT the ceiling
  because the MEASURED gate in Client._log_usage (routing-gap F2)
  backstops it mid-flight.
* graveyard cap 40 -> 10 (Matt: "stop every 10 and fix them"). Five
  entries left open by the 08-12 rerun were diagnosed and cleared first
  so the run starts with a full budget of 10: four converged-after-repair
  (note-severity residue), one genuine DIAGNOSED-UNCONVERGED
  (l797_809_n001: an ontology atom carries an unbound variable, 5
  attempts) -- that class becomes a tracked census category with a prompt
  lever if it recurs.
* checkpoint_every 10, checkpoint_pause TRUE.
* EXECUTION MODE: LIVE (not batch). Grounds: Matt sees no reason to batch
  further, AND review defect 4a makes a pause in BATCH mode discard
  already-paid collected rows -- live is the reviewed-clean pause path,
  so we get stopping checkpoints now with zero exposure to 4a. Cost of
  the choice: no 50% batch discount (~$3 live vs ~$1.5 batched),
  affordable within the raised ceiling and squarely inside Matt's
  "don't block on 4a unless it wastes money".

## 2026-08-14: corpus translation STOPPED after 12 modules -- waiting for batching

Matt: "we should probably wait for batching given the cost." Live
concurrent slice 1 stopped at 12 translated modules, $0.026 spent (they
are on disk and --only-stale will skip them, so the work is banked, not
lost). Campaign $9.20 of $20.
Grounds: live forgoes together's 50% batch discount -- ~$3 live vs ~$1.5
batched for the corpus. Config switched to execution.mode=batch,
batch_min_pending=8.
⛔ BINDING CONSEQUENCE, recorded at the config: checkpoint_pause is now
FALSE. In batch mode a pause aborts _collect's routing loop and discards
already-paid collected rows (review defect 4a, reproduced) -- exactly the
"wasted money" case Matt's ruling carved out. So the corpus run waits on
the 4a fix (already dispatched), and until it lands the ONLY safe batch
configuration is record-only checkpoints. The graveyard cap (10) still
stops the run for diagnosis regardless of mode -- that mechanism is
independent of checkpoints and unaffected by 4a.
SEQUENCE: 4a fix lands -> reviewed -> checkpoint_pause back to true ->
resume the corpus in batch with --only-stale.

## 2026-08-14: pipeline-fix review round -- 4 defects FIXED (4a unblocks batch pausing)

All four adversarial-review defects fixed, each pinned RED against the
pre-review files (b57a007): **18 pins red there, all green now**.

**4a (BLOCKING) -- a pause in BATCH mode discarded already-paid rows.**
`dispatch_core._collect` routes a submitted job's rows one at a time,
and `sched.complete(state)` sits INSIDE that loop. A `CheckpointPause`
raised from it (translate_exec's `RunContext.finish`) aborted the loop,
so every remaining row of an ALREADY-PAID batch was never fed, never
written, never ledgered -- ~725 rows re-bought at `checkpoint_every=25`
on 750 items. The module's own R5a doctrine already deferred
`CostGateError` and poison for exactly this reason and simply did not
know about the pause. Now `pause_exc` is deferred the same way
(dispatch_core.py:1256/1288-1296/1324): every collected row is
fed/ledgered/routed, THEN the pause raises -- before the live reruns, so
it still buys nothing more. Pinned: 5-clause batch, pause at clause 2 --
all five rows ledgered, the four completable clauses written, and
m0003's repair round (a fresh paid draw) correctly left for the resume.
⛔ CONSEQUENCE for the sequence recorded above: `checkpoint_pause` is
safe in batch mode again once this is reviewed.

**2 -- `asserts_delivery` false-positived on honest declines that quote
the instruction** (the opposite direction of the same honesty metric).
Two causes: `_NEGATION` was searched only inside the <=3-word
pronoun-verb window, so a negation later in the sentence was invisible;
and the splitter did not break on commas or dashes, so the contrastive
clause stayed in-sentence. Fixed at promise_repair.py:641-663/691-701 --
negation over the WHOLE clause, `,`/`--`/`—` added to the splitter,
`was/were` added to the passive alternation (simple past was
under-detected), plus two guards the review's families demanded:
`_NON_ASSERTIVE` (reported instruction / counterfactual: "I was asked to
add ...", "I would add ... if ...") and `_CONDITIONAL` ("... only where
the span establishes it"). ⛔ `should be added` is deliberately still not
passive-delivery: ds7's `refusal_style_section` decline recommends what
someone else should do. 13 new detector pins + a stage pin that a
reported-instruction decline stays `declined`.

**1b -- the seat was outside the up-front cost gate.** The gate priced
`len(plans)` redraws while the seat added one unpriced call per
delivered redraw, so the stage's "whole worst case gated up front"
doctrine was false and the overrun could only be caught by the MEASURED
ceiling mid-run -- the expensive place. Now priced (promise_repair.py:
1101-1140): one seat call per plan at `SEAT_MAX_TOKENS` (1024, reused
from frontier_review rather than re-chosen), and the cap is REAL --
the seat call sets `max_tokens_override` and restores the driver's leaf
cap, so the gate's arithmetic is the arithmetic that runs. Second arm:
a ceiling trip mid-stage used to discard every splice already made AND
the money that bought it, because the repaired graph is written at the
end. It now breaks, writes `root_graph.repaired.json` + the report
(with `stopped_by_cost_gate`), and re-raises -- the ceiling still stops
the run loudly, but the paid work survives.

**4b -- the pause's resume hint was FALSE.** prep read the ORIGINAL
`root_graph.json`, so names already spliced into
`root_graph.repaired.json` were invisible to `skipped_already_provided`:
a resumed run re-drew and RE-PAID every plan and overwrote the partial
graph. Fixed at promise_repair.py:855-874 -- when the previous report
RECORDS A PAUSE, the repaired graph is the baseline and the report says
`resumed_from`. ⛔ Gated on the recorded pause by design: a COMPLETED
run's output must never become the silent base of a second repair
(pinned both ways). And `main()` now returns **3** on a pause, so
`ds7_repair.sh` (`set -e`) can no longer sail past a half-finished
repair into the quality battery.

Minor review items also done: the checkpoint's O(n) status scans now run
only when one is `due()` (translate_exec.py:459-463, promise_repair.py:
1211-1218), and a paused translate run with failed clauses says so
explicitly (exit 3 subsumed exit 1).

Pins: test_splice_seat 30 -> **46**, test_run_checkpoint 9 -> **13**;
graph_v2 318 -> **338 collected**; phase_1 (excl. resolve_runs) 800, 1
xfail. The four fix files' own suites (test_splice_seat,
test_run_checkpoint, test_promise_repair, test_translate_exec) are
**120/120 green**.
⚠️ NOT MINE, recorded so the next runner does not chase it: 9 graph_v2
tests fail on HEAD independently of this thread -- 6 in
test_node_worked_example, 3 in behavior_pilot/test_behavior_match, all
of the shape `assert 773 == 15`. The full-corpus translation setup
(dec53ad) regenerated `node_corpus.json` from the 15-node SAMPLE to the
whole 773-node corpus, and those pins pin the sample. That is the
"never pin an exact count of a live artifact" hazard from AGENTS.md
firing for the third time; the fix belongs to the stage-4/corpus
thread, not here.

## 2026-08-14: 4a + 3 defects FIXED; corpus/fixture split (my defect, root-fixed)

Builder closed all four with 18 pins RED at b57a007: 4a defers
CheckpointPause exactly as gate_exc (route every collected row, ledger
it, then raise before any live rerun) with a 5-clause batch pin; the
narration matcher now reads negation over the whole clause, splits on
commas/dashes, and knows was/were (with "should be added" excluded BY
NAME -- ds7's refusal_style decline recommends what someone ELSE should
do); seat calls are priced into the up-front gate at SEAT_MAX_TOKENS
with the repaired graph written BEFORE a late CostGateError re-raises;
the resume baseline is the repaired graph only when the prior report
recorded a pause, and main exits 3.
MY DEFECT, root-fixed: regenerating node_corpus.json to 773 rows broke 9
pins asserting the 15-node sample -- the repo's own "never pin an exact
count of a live artifact" hazard, third occurrence, and the recorded
durable remedy (split the file) had never been applied. Now applied:
the full-corpus run reads node_corpus_all.json via config_corpus_all.json;
node_corpus.json is restored to the pinned 15-node sample. 33 previously
failing tests green. A live artifact and a test fixture must not be the
same file.
Review of the fix round dispatched; it gates re-enabling
checkpoint_pause for the batched corpus run.

## 2026-08-14: fix-round verified GO; corpus artifacts pinned; cadence corrected

Review verdict: GO on 4a -- CLOSED, verified by re-running the
reviewer's ORIGINAL failing probe (now: 4 of 4 rows routed, all
ledgered) plus an attack pass over every other mid-collection abort
path (second pause kept-first, precedence gate>poison>pause all AFTER
the loop, propagation to exit 3 intact). Residual recorded: a pause from
job 1 would abandon jobs 2..n -- UNREACHABLE here (translation flushes
one job; FlatScheduler makes all clauses ready at once). Defects 2 and
1b CLOSED (reviewer's own 16-decline/10-delivery corpus: 0 false
positives, 0 false negatives; priced cap proven to be the cap that runs,
restore exception-safe).
NEW DEFECT recorded, promise_repair only, does NOT gate this run:
:868's resume test reads `paused` alone, so a run stopped by the MID-RUN
COST GATE (which writes paused=None + stopped_by_cost_gate) re-draws and
re-pays every plan -- contradicting its own "the paid work survives"
comment. One-line fix queued for the repair thread.
CADENCE CORRECTED (my misreading): Matt's "stop every 10 and fix them"
was about the GRAVEYARD CAP, not checkpoints. checkpoint_pause -> FALSE
(record-only every 10: done/remaining, spend vs ceiling, failures by
category, graveyard depth). Pausing every 10 clauses would have meant
~77 manual restarts. The STOPS come from the graveyard cap of 10,
checked in prepare -- so the run is SLICED and each slice re-checks it.
CORPUS ARTIFACTS PINNED (the reviewer's sharpest catch: "the single
artifact the paid run consumes is the one artifact with no pin") --
test_corpus_artifacts.py asserts node_corpus_all.json's 773 ids match
the config's selection exactly, that every row is a node of the
CERTIFIED production graph and covers all of it, and that the sample
fixture and the live corpus stay different files. 3 pins green.
Also recorded, not blocking: node_corpus.py still has no --out (so the
documented --all command would clobber the fixture a fourth time --
detected by test_full_corpus_mode..., not prevented), and
node_worked_example.md cites sample-corpus node ids that do not exist in
the 773 -- harmless as pedagogy, but its pin now means less than it says.

## 2026-08-15: proactive graveyard check -- both entries BENIGN, but the cap
## will fire on convergence noise, not defects

Checked the first 2 entries from the corpus run rather than waiting for the
cap. Both `translated` (3 and 2 attempts), ZERO error-severity findings;
the only notes are `requires-unprovided`, which at ~45/773 modules is
EXPECTED BY CONSTRUCTION -- most providers are not translated yet, so a
cross-module `requires` has nothing to resolve against. Cleared with
verdicts that carry a RECHECK-AT-COMPLETION condition: if those names are
still unprovided once all 773 exist, it becomes a real under-export
finding.
PROJECTION worth ruling on: the graveyard records every NON-FIRST-ATTEMPT
CONVERGENCE, not only failures. Observed rate on the live slice is ~2
entries / 12 modules (~17%); the campaign's recorded repair rate is ~25%.
Over 773 modules that is ~130-190 entries, i.e. ~13-19 stops at cap 10 --
almost all of them benign convergences like these two. The cap's stated
purpose ("a hundred uninspected non-convergences is not a corpus") is
aimed at the FAILURE case, which these are not.
OPTIONS for Matt: (a) keep cap 10 and accept ~15 diagnosis stops (his
stated preference for frequent stops, and each stop is cheap when the
entries are clean); (b) raise the cap to ~30 -- still bounded, ~5 stops;
(c) leave the cap and let the census distinguish -- an UNREPAIRED entry is
the signal, a converged-after-repair entry is recorded evidence. NOT
recommended: making the graveyard stop recording convergences, which would
delete the evidence trail the census reads.

## 2026-08-15: census ADVERSARIAL REVIEW -- the 58% is really 43%, and 2 of 49

Matt asked whether the ruling requests had been adversarially reviewed. They
had not. One was dispatched; TRANSLATION_CENSUS_REVIEW.md is the result and
it materially changes the ask.
SURVIVED, independently re-derived from raw transcripts (not by re-running
the author's script): 191 clauses / 435 calls / 244 repair rounds (56%), the
per-class table, gen-11 71/87, the 84/84 faithfulness replay, every Fix-A
firing count. BETTER than claimed: all 435 calls matched 1:1 to usage.jsonl
rows (the census never attempted this) -- real repair share 61%, cost model
1.05x high not 1.11x, and the stated cause (undiscounted cache) is WRONG;
the real cause is in_cpt = out_cpt at census:307. Ranking is robust: the
gen-11 top five never reorder at 0/25/100% cache discount.
§6.2 SURVIVED A HARD ATTACK and got worse: replaying every earlier failing
module through the live checks, 97 novel-class instances were genuinely
introduced vs only 5 already latent -- real defect-TRADING, not masking, at
57% (not 52%).
THE MISLEADING CLAIM: "58% removed, MEASURED by replaying every stored
failing module." Only 2 of the 49 kills are measured; 47 are class
subtraction by fiat. Fix D's mechanism (required `body`) reaches only
body-less ontology sites, but the sim subtracts the whole class including 3
assert-site and 12 already-bodied findings. Corrected: 58% -> 43%. The sim
states the assumption honestly; the two documents Matt would read say
"measured". Also: §6.1/§6.2 are computed by no committed script, and §3.2's
attribution of the 2.27->0.67 improvement to the per-request adapter is
PERFECTLY CONFOUNDED (resample_truncation switches on at the same
transition, and max_tokens drops 16384->4096 inside "generation 11", which a
prompt-hash key cannot see).
FIX VERDICTS: A NEEDS WORK (declare-asserted-act decides which of two
disagreeing lists is authoritative -- a constructed case blesses a typo --
and nets +10 breach-rounds; readback-empty-slots silences a check without
fixing the read-back). B NEEDS WORK (the diff NO-OPS for `cites`, and would
make `cites: null` illegal for 224/1386 licensed items, pushing the model
toward FABRICATED citations; ~60-120 lines, not four). C SAFE minus
requires-inputs-overlap. D NEEDS WORK (200 stored modules unloadable with no
migration; apply_waivers RAISES on contract-stale, forcing an uncosted paid
re-translation; the cheaper lever -- conditionally requiring `body` -- is not
rejected by name). E REJECT as written (deletes _check_head_bound with no
replacement; silently no-ops three of Fix A's eight rules while all 34 tests
still pass on old-shape fixtures). F REJECT / not ready.
CONSEQUENCE FOR M1: the guard-accept request is WITHDRAWN pending rework --
only C is close to landable, and the coverage claim it rests on is 43%, not
58%, with 47 of 49 kills unmeasured.

## 2026-08-15: stage-4 FACTORY SPEC review -- the central remedy does not work

STAGE4_FACTORY_SPEC_REVIEW.md. Verdict SOUND WITH AMENDMENTS, but one
amendment REVERSES the spec's central architectural move.
* MECHANISM TRUE: _refuse has exactly 9 call sites, all inside the four
  prompt builders; judge hands a list literal to a caller-supplied object
  and never reads it again. A transport appending a turn to 4c's messages
  delivered it, nothing raised.
* JUSTIFICATION OVERSTATED: "the absent parameter IS the mechanism" is
  false today -- plan_clause already holds the readback in scope four
  lines above the 4c builder. What actually keeps renderings out is a
  CONTENT scan (_RENDERING_PATTERNS) plus _item_text sourcing from the
  module. The test the spec leans on is a substring scan of PARAMETER
  NAMES whose own docstring wrongly claims it is structural.
* REMEDY DEMONSTRATED NOT TO WORK: a factory taking EXACTLY the spec's
  arguments, violating no MUST or MUST-NOT, globs run_dir, re-runs
  render_module, and appends the full read-back to 4c's messages past
  every fence. run_dir is a CAPABILITY, not a scalar. A signature fence
  cannot close a hole located on the wire -- the fix is a WIRE fence (A1).
* Property-breaking gaps: MUST 5 (rendering_sha(rb)) contradicts MUST-NOT
  1 (no rb) -- unimplementable as written, and an implementer resolves it
  by passing rb, causing the very failure the spec prevents; MUST 7 names
  run_checkpoint.py, which is a progress reporter with no key/store, so
  literal obedience gives ZERO idempotency and re-pays every resume; MUST
  2's transport violates MUST 1/6 because OUR OWN identical-retry seam
  guard appends a marker on any repeat of a failed body (arguably a §5.6
  "zero bits" breach too); truncation is mis-routed as ProviderError so it
  is retried and re-paid; the budget fence is blind because the flash
  provider is defined INLINE (stage-4 flash spend invisible to the gate
  forever); §7's frontier tier is UNREACHABLE through the mandated client
  (fable is kind=anthropic, Client refuses it).
* Ledger correction: $3.449/$8.50 -> $5.05 left by spend.py's own view
  (the review's $6.44 was wrong) -- and this is the same G1 gauge defect
  the guardrails review found, biting a second consumer.
* §C4's split VERIFIED CORRECT (run_clause's skip cannot live in the
  factory; reply parsing in judge does NOT create a second adjudicator).
  Two amendments + a THIRD seats.py change the spec missed entirely: the
  <=12-item 4c batch split belongs in plan_clause.
* BUILD ORDER (refines Matt's M3 ruling): build the factory NOW, offline,
  independently of F1/F2/F3 -- but let it make NO CALL until A1, F4, F7,
  F5 land. F1/F2/F3 gate any run that says the word "faithful", not the
  seam itself.
* PILOT REALITY: only 6 distinct clause ids render today, so the
  "<=10-clause pilot" is not available from the stored corpus. Its
  deliverable is reply shapes, unclear rate, A1 sha-mismatch count,
  normalisation rate and measured $/seat -- NEVER a faithfulness result.
  A flash pilot also needs a written ruling exempting a reply-shape pilot
  from §7's frontier mandate.

## 2026-08-15: COVERAGE is the real failure -- 19% unrepaired, one class

Live gen-11 data (100 modules attempted): **69 translated, 19 UNREPAIRED,
12 abstained** -> ~146 of 773 would fail entirely. Of 40 error findings on
unrepaired modules, **32 are `undeclared-body-name`** ("body references X
but nothing declares it"); the tail is 2 self-restating glosses, 2
borrowed-without-gloss, 1 unsafe variable, 1 clingo refusal.
THAT CLASS IS FIX F -- ranked SIXTH by the census, rated high risk, and
REJECTED by review as not ready, with the census saying it "must keep
costing a call". The inversion is a metric artifact: the fix plan ranked by
REPAIR ROUNDS SAVED (a cost metric, and cost was never the problem at ~$4
a corpus). Ranked by MODULES THAT NEVER TRANSLATE, F is first and A-E save
none of the 19. Coverage, not spend, is what a graph corpus cannot lose --
a missing module takes its concepts and edges with it.
MATT'S RULINGS 2026-08-15:
1. Let the RUNNING slice finish (more data), then STOP -- no further slices
   until a fix exists. Recorded: this is a sample, not a full corpus.
2. Reproduce the class on a SECOND MODEL and iterate there to find a
   solution, then test the solution on DeepSeek -- distinguishing an
   instruction/schema defect (reproduces) from a model-capability limit
   (does not).
3. At the end, RE-RUN EVERYTHING (not only the failures) so hashes match
   and we can prove no pre-existing success was broken by the fix.
4. Incorporate ALL fixes this round (A-F), not a filtered subset --
   provided each is adversarially reviewed and validated INDEPENDENTLY, and
   then again AS A GROUP before the run. (The group check matters: review
   already found E silently no-oping three of A's rules while all 34 of A's
   tests still passed.)
BLOCKER SURFACED, NOT WORKED AROUND: Haiku is not reachable from the
translation harness. `translate.Client` speaks **openai-compatible only**
(translate.py:553-555 refuses any other kind), and providers.json carries
no Haiku entry -- the only anthropic row is `fable`. Options are recorded
in the conversation; this needs Matt's pick before the cross-model
iteration starts.

## 2026-08-15: HAIKU CROSS-MODEL TEST -- the failures are MISSING ABSTENTION,
## not a schema defect. Fix F is aimed at a SYMPTOM.

Method (Matt's idea, zero project spend): local Haiku subagents given the
BYTE-IDENTICAL system prompt (36,820 bytes) and user message DeepSeek
received on failing clauses, with no hint of the failure. Their modules were
then run through the SAME schema.validate.
RESULT, 3 of 3: Haiku **ABSTAINED** on every clause DeepSeek left
`unrepaired`, each module passing schema cleanly, with converging reasons --
"describes the organizational structure and content of the document rather
than imposing normative requirements on model behaviour".
The document text confirms Haiku is RIGHT. All three are meta-statements:
L0011 "These goals can sometimes conflict, and the Model Spec helps navigate
these trade-offs..."; L0021 "This overview sets out the goals, trade-offs and
governance approach... primarily intended for human readers"; L0023 "The rest
of the document consists of direct instructions to the model, beginning with
some foundational definitions...". None imposes an obligation on the
assistant. They are ABOUT the document.
THE MECHANISM, and it re-ranks the whole fix plan a SECOND time:
`undeclared-body-name` is a SYMPTOM, not a cause. Forced to translate
non-normative prose, the model invents predicates for it --
`sets_out_guidance`, `rest_of_document_section`, `overarching_goal`,
`additional_principle` -- and an invented name has nothing to declare it, so
the body-reference check fires. FIX F (body literals carry their origin, a
schema-shape change the census ranked 6th and TWO reviews rejected) would
make the model DECLARE its invented predicates rather than stop inventing
them: it treats the symptom and would convert hard failures into plausible
fabrications, which is strictly worse for a corpus that feeds behaviour
matching.
THE REAL FIX is abstention guidance -- prompt-level, cheap, low-risk, and
already a first-class outcome (12 of 100 modules abstained today, so the
path works; the model just does not take it on meta-clauses). DeepSeek
abstains when the clause is obviously non-normative and forces a translation
when the clause SOUNDS normative ("helps navigate", "sets out", "consists of
direct instructions").
NOT YET ESTABLISHED (do not overclaim): 3 samples, all from L1-170. Whether
this explains all 19 unrepaired -- and how many of the 32
`undeclared-body-name` findings sit on genuinely normative clauses -- needs
the rest of the sample. That is the next measurement, and it is free.

## 2026-08-15: CHAIN ANALYSIS -- freezing is MOTION, not difficulty (98% vs 9%)

_debug_gen11/CHAIN_ANALYSIS.md. Over 96 repair chains in three runs:
  every reply distinct from every earlier reply -> 63 of 64 TRANSLATED (98%)
  some reply repeats an earlier reply           ->  3 of 32 translated (9%)
NOTHING about the defect predicts the outcome: recovered vs lost chains have
the same round-1 finding counts (2.15 vs 2.47, medians both 1), the same
check_ids, the same message shapes, the same output-length growth, and the
same defect-trading rate (33% vs 32%). All 19 lost chains repeat an earlier
reply; none of the 31 clean recoveries does. Repeat-of-ANY-earlier-reply
beats adjacent byte-identity (19/19 vs 17/19) -- the attractor is a small
CYCLE, not a point (n078 replies A,B,C,A,D; n056 replies A,B,A,A,A). Median
distinct replies in a 5-call lost chain: 2.
THREE HYPOTHESES KILLED WITH EVIDENCE:
* provider determinism REFUTED -- 08-15 re-issued attempt 1 for all 19 with
  byte-identical prompts and identical system/schema/provenance hashes;
  0 of 19 replies matched. Sampling is live cold and frozen only inside a
  transcript.
* uninformative repair prompt REFUTED -- Haiku stand-ins replayed four
  frozen transcripts in the ACCUMULATED condition (the exact input DeepSeek
  froze on) and 4 of 4 performed the named repair in ONE turn, passing the
  real schema.validate + checks.run_checks.
* unfixable defect REFUTED for 14 of 19.
What remains is ANCHORING ON ITS OWN PRIOR ANSWER -- and 9 of the 19 first
repeat at ROUND 1, so one prior wrong answer in context is enough.
CORRECTION TO THE RECORD: the class doc's "3 link-stage recoveries are
corpus fill, quote 11 of 16" is WRONG -- translate.py:1381 calls repair_loop
without concepts=, so in-loop checks never see concepts.json and its growth
cannot have loosened anything. All 19 finals re-validated offline under
identical gates: 14 recoveries pass, all 19 08-14 finals fail. **The number
is 14 of 19.**
EV, and it answers Matt's question directly (coverage, not just waste):
current 95 calls -> 0 modules; stop-at-first-repeat (54 calls) + one clean
restart (45 calls) = 99 calls -> 14 MODULES. The 45 calls a stop avoids are
exactly the 45 the restart costs -- a call-for-call trade. Whole 100-clause
population: ~230 calls / 69 modules today vs ~230 calls / ~81-83 modules.
POLICY (designed, not implemented): hash every assistant turn against ALL
earlier turns; on first repeat discard the transcript and restart the clause
from attempt 1 ONCE (max_attempts unchanged, worst case 10 calls); on a
repeat inside the restart, abandon and record with a new `frozen` graveyard
flag. REJECTED BY NAME: paraphrasing the repair message, raising repair
temperature, re-rendering full finding history -- the message is sufficient,
the CONTEXT IT ARRIVES IN is the defect.
Translation should adopt the graph driver's existing remedy
(recurse_driver.py:1460-1467, dispatch_core.feed). translate_exec.can_restart
returns hard False, but that decision was scoped to TRUNCATION only; freezing
had never been measured. Two things not to copy: do not zero per-clause spend
(the budget gate would lie), and key on repeat-of-any, not adjacent identity.
FALSIFIER: "a repeated reply predicts non-convergence" -- whole-disk replay
gives 3/49 (6.1%) adjacent and 3/32 (9%) repeat-of-any; above ~20% in a
future corpus region the policy would be discarding real convergences.

## 2026-08-15: TIER ANALYSIS -- first-try is defect KIND, not clause difficulty

_debug_gen11/TIER_ANALYSIS.md. 319 clause-observations, 5 prompt generations.
Methodological catch worth keeping: sha256(prompt_system.txt) is NOT a
complete generation label -- inside "gen 11" the schema_sha changes and
max_tokens drops 16384->4096, so the CHECKER moved. Claims are reported on
both the gen-11 pool (n=228) and the single-schema 08-14 pair (n=100).
Distribution is TRIMODAL, not a decay: 43% land immediately, 24% after one
round, 20% die.
SEPARATORS (Fisher): a1 draft with a body-bearing ontology entry AND zero
inputs -> 15% vs 49% (p<0.0001; 10% vs 58% on the 08-14 pair); requires >=2
borrowed names -> 22% vs 51% (p<0.0001); **graph needs >=2 -> 24% vs 45%
(p=0.005) -- the only EXOGENOUS separator, knowable BEFORE spending**; arity
mismatch (DC-5) -> 0/11 first-try, 73% unrepaired (p=0.004).
NULL: span length, line count, narrowing, output length, predicate count,
provides. Also null: DEFECT COUNT -- 1 finding resolves in one round 41% of
the time, 4 findings 43%. Tier is governed by defect KIND, not volume. The
predicate-count gradient on FINAL modules is survivorship and dissolves on
attempt-1 drafts.
DC-7 ADJUDICATED with a genuinely outcome-blind classification (shuffled,
opaque keys, joined to outcomes afterwards): NORMATIVE 31% [13-58] n=13 vs
NON-NORMATIVE 49% [39-60] n=87, p=0.25 -- not significant AND THE WRONG
SIGN. Span-type routing would divert ABOUT-THE-DOCUMENT, the EASIEST bucket
at 58%. The reviewer's DC-7 is confirmed and strengthened; graph-stage
span-type classification is dead in this region.
DC-1 INDEPENDENTLY CORROBORATED: drafts using the body-less ontology route
land first-try at 60% (n=15) vs 38% overall -- but only 7% of drafts use it.
Discoverability, exactly as the review argued.
COUNTERFACTUAL LADDER: +Fix C (borrowed-name gloss as a local counted
obligation; 57% of the 2-attempt tier's single repair round, 26% of ALL
repair rounds) -> 55%; + undeclared-body-name via DC-1's worked example ->
75% [81% on the 08-14 pair]; + unsafe-var -> 82%. Two classes reach ~75-81%;
three pass 80%.
HAIKU EXPERIMENT, with its confound recorded: byte-identical stored prompts,
10 clauses whose sole a1 defect was borrowed-no-gloss. Arm A (stock) 5/10;
Arm B (stock + one counted gloss paragraph) 10/10, p=0.033, with the effect
entirely on five clauses where Haiku reproduced DeepSeek's exact findings.
BUT the A/B split coincided with the subagent batch split, so agent variance
is not separable from clause difficulty -- randomised replication is the
rank-1 falsifier before this touches a prompt.
THE REFRAME: tier is largely NOT a stable property of the clause. Median
within-cell attempt spread is 3; of 20 twice-drawn cells, 10 are discordant
on first-try; and 9 of the 19 clauses that burned all 5 attempts for nothing
passed on ATTEMPT 1 of a byte-identical re-draw. No static feature can
explain most of the 43->80 gap -- which is why the chain policy (restart on
repeat) and the fresh-draw finding rank where they do.
