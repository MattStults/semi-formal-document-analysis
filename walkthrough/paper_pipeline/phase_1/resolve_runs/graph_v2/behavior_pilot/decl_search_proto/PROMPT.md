# DECLARATION-SEARCH PROTOTYPE — durable Opus execution prompt
(Design tier: Fable, 2026-08-20. Execution tier: Opus. Re-runnable; each run
overwrites outputs in THIS directory only.)

## GOAL (repeat this verbatim in your final message and self-check against it)
Prove out L1-based declaration search on the OpenAI-spec instrument: build the
feature matrix from the existing annotation layers, fit per-behavior sparse
logistic models against panel truth, run stability selection, and emit
declaration proposals in the exact contract vocabulary — as HYPOTHESES with
predicted charter arithmetic, never as adopted changes.

## EXIT CRITERIA (all machine-checked by validate_output.py — run it; a run that
## fails validation is NOT complete and you must say so)
1. feature_matrix.json written: one row per (behavior, node) truth point, the
   exact feature dictionary of §DATA below, with row/feature counts reported.
2. fit_report.json written: per behavior — CV log-loss of the fitted model vs
   the trivial baseline AND vs the current instrument's decisions; L1 path
   summary; stability-selection frequencies (>=100 bootstrap resamples,
   fixed seed 20260820) for every feature with nonzero median coefficient.
3. declaration_proposals.json written, conforming to OUTPUT_SCHEMA.md: only
   proposals whose feature passed stability >= 0.7; each carries predicted
   fixes/breaks counted by applying the proposed discrete rule (not the soft
   model) to the truth table.
4. validate_output.py exits 0.

## DATA (read-only; never modify any file outside decl_search_proto/)
Work from /Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/behavior_pilot
(cd there; imports need it). Truth: `import satisfiability_census as sc;
sc.truth_all(slug)` for the three behavior slugs in modules_contract_v18.json.
Feature construction per node — reuse the instrument's own readers, do not
re-derive: `import relevance_by_act as RBA`; br=RBA.bridges();
corpus=RBA.corpus_acts(); pm=RBA.parent_map(); layers assert_signature.json,
assert_protects.json, assert_purpose_actor.json, definition_*.json (adopted),
panel_run1/convergence/context_atoms_consensus.json (credits).
Features per (behavior,node) row (binary): for each canonical act A and status
class s in {oblige,forbid,permit,prefer,example,described}: carries(A,s) where
A is the bridged canonical act OR any hierarchy ancestor/descendant relation to
a behavior-performed act (encode three separate features: exact, module-specific
-behavior-genus, module-genus-behavior-species); each governs value; each
contexts value INCLUDING the four context atoms; each protects value; actor
has-assistant; each purpose value. Label: truth == 'relevant'.
MASK (exclude from fitting, keep in matrix flagged masked=true): every
(behavior,node) with an adjudicated-defensible verdict — read
panel_run1/convergence/flip_adjudication_verdicts.json plus any file matching
panel_run1/convergence/*verdicts*.json where verdict contains 'defensible'
(case-insensitive), and treat bucket-2 entries in LEDGER files the same way if
present as JSON.

## METHOD (fixed; do not redesign)
sklearn LogisticRegression(penalty='l1', solver='liblinear', C swept over a log
grid, class_weight='balanced'); model selection by 5-fold CV log-loss;
stability selection = refit at the chosen C on >=100 bootstrap resamples (seed
20260820), frequency = fraction of resamples with |coef| > 1e-6. Per behavior
independently. numpy/sklearn are in system python3 (1.6.1/2.2.5).

## INTERPRETATION RULES (fixed)
A stable positive feature that the behavior's current declarations DO NOT
consume -> proposal kind 'add' (e.g. a governs value not in governs_concern, a
context atom with no declaration, an act relation outside current performs
set). A stable negative feature the current config treats as engaging ->
proposal kind 'wall'. Map every proposal into the contract slots ONLY:
governs_concern | governs_conditional | protects_concern | purpose_concern |
party_concern | performs-act set | context-declaration (new slot; name it
contexts_concern and mark schema_extension=true). If a stable feature maps to
no slot, report it under 'unmappable' — do not invent slots silently.

## ANTI-GOALS (violating any of these is a failed run even if validation passes)
- No file outside decl_search_proto/ is created or modified.
- No proposal is described as adopted, validated, or an improvement — they are
  truth-fitted HYPOTHESES pending blind justification (9b) and fresh-pool
  certification (9e); say so in fit_report.json's '_' field verbatim.
- No claim of completion without validate_output.py exiting 0.

## FINAL MESSAGE FORMAT
(1) restate GOAL and each EXIT CRITERION with met/not-met; (2) per behavior:
baseline vs fitted CV log-loss, count of stable features, count of proposals,
top-3 proposals one line each; (3) anything ambiguous or smelling of leakage.

## RUN-2 AMENDMENTS (design tier, 2026-08-20 — supersede conflicting run-1 text)
A. INTERACTION FEATURES: add pairwise product columns between feature families
   (act-relational x protects, act-relational x purpose, governs x contexts,
   governs x protects, act-relational x contexts). Screen before fitting: keep a
   product column only if it has support >= 3 positive rows and differs from
   both parents on >= 2 rows. Report the post-screen column count. A stable
   interaction maps to governs_conditional when it is governs x contexts;
   otherwise to a NEW proposal kind "subtype" (schema_extension=true) naming
   both parent atoms.
B. FAIR INSTRUMENT COMPARISON: report accuracy/log-loss on ALL rows with
   defensible rows scored correct-for-both; keep the masked fit as-is.
C. ACT ENCODINGS: the run-1 seat's resolution is now canonical — 'exact' =
   behavior-blind carries(A,s); the two relational encodings are separate.
D. RESIDUAL TARGET LIST: fit as before, but additionally report, for each of
   the current unresolved mismatches (recompute: disagreement AND not
   adjudicated-defensible), which post-screen columns separate it from its
   census colliders (zero, or the list). This is the run-3 carving queue.
