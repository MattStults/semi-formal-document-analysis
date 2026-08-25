# L1/L2 LICENSING EXPERIMENTS — CLEAN-CONTEXT ADVERSARIAL REVIEW

## Provenance

- **Reviewer:** clean-context adversarial reviewer, Opus tier, no stake in the project's
  success. No prior context on this repo beyond what is recorded below.
- **Session date:** 2026-08-24 (the artifacts under review are dated 2026-08-24/25;
  notes 0042 and commit `bf0d4978` carry 2026-08-25).
- **Asked to determine:** whether the two registered licensing experiments — L1 (for P1)
  and L2 (for P2), as registered verbatim in `RETRANS_REVIEW_DISPOSITION.md` — would, if
  passed exactly as written, answer the user's two questions:
  - **Q-A:** Would using this ontology in a COMPLETE retranslation of the OpenAI spec
    allow complete representability of all dimensions necessary for SEPARATION
    (distinguishing which clauses bear on which behaviours)?
  - **Q-B:** Is this likely to EXTEND TO NOVEL BEHAVIOURS, on the theory that novel
    behaviours fall within the space spanned by the 100-definition corpus?
  Specifically: every way the experiments could PASS while the claims stay FALSE, every
  way they could FAIL for reasons unrelated to the claims, whether L1+L2 are jointly
  sufficient for a funding decision on a full retranslation campaign, and what single
  experiment to run instead or in addition.
- **Standing context taken as ground truth (not re-litigated):** the prior integration
  census was demolished by adversarial review and the demolition was accepted in full —
  random-partition null dominates the pass condition 299/300; 1-NN relevance prediction
  at 0.72/0.70 vs bases 0.60/0.59; mids induced circularly; 39-node sample stratified on
  known-problem nodes; both scored behaviours in-corpus; seat agreement 23/39 masked by
  pooling.
- **Operative standard applied:** the project's own — the system either MATCHES the
  frontier panel or gives a FRONTIER-JUSTIFIABLE answer.

### Repo artifacts inspected

All under
`/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/`.

Primary (read directly by the reviewer):
- `walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/behavior_pilot/RETRANS_REVIEW_DISPOSITION.md`
- `.../behavior_pilot/ITERATION_NOTES.md` (notes 0031, 0032, 0033, 0036, 0042)
- `.../behavior_pilot/HANDOFF_CURRENT.md`
- `.../behavior_pilot/qc_separability_census.py`
- `.../behavior_pilot/RETRANS_INTEGRATION_CENSUS.json`
- `.../behavior_pilot/qc_canonical_values.json`
- `.../behavior_pilot/qc_emergent_schema.json`
- `.../behavior_pilot/qc_emergent_ann_A.json`, `qc_emergent_ann_B.json`
- `.../behavior_pilot/query_class_corpus.json`
- `semi-formal-experiment/spend.py` (+ its live report over `usage.jsonl`)
- `git log` at `bf0d4978` and predecessors

Secondary (inventoried by a delegated exploration pass, results folded into the
addendum):
- `data/behaviours.json`, `data/panel-coverage.json`, `data/panel-v5/` (`runlog-v5.jsonl`,
  `behaviour-definitions-v5.json`, `rubric-v5.txt`, `PROVENANCE.md`)
- `.../behavior_pilot/satisfiability_census.py`, `arm_ab.py`,
  `satisfiability_census_v19_frozen.json`, `ROUND4_FREEZE_DERIVATION.json`,
  `atoms_frontier_frozen.json`, `PREREG_panel_equivalence.{md,sha256}`
- `.../behavior_pilot/panel_run1/` (adjudication + fresh_draw / fresh_draw2 /
  fresh_draw3 / fresh_draw4 result blocks, `agreed_negative_rulings.json`,
  `panel_rerulings.json`, `REGISTERED_RESULT.json`, `spotcheck_matt_result.json`)
- `.../behavior_pilot/ua_truth_visible.json`, `ua_truth_sealed.json`,
  `ITER1_TRADEOFFS_REPAIR_TRUTH.json`, `ITER2_TRADEOFFS_REPAIR_TRUTH.json`,
  `GEN_BLOCK1_SCORED.json`, `ITER*_SCORED.json`, `round4_*_scored*.json`,
  `ROUND4_DEV_TABLE.json`, `ruling_packets/`, `coverage_translated.json`
- `graph_v2/node_corpus_all.json`, `graph_v2/GRAPH_OVERVIEW.md`
- prereg drafts: `FRESH_DRAW_PREREG_DRAFT.md`, `FRESH_DRAW_ROUND2_PREREG_DRAFT.md`,
  `FRESH_DRAW_ROUND3_PREREG_DRAFT.md`, `ROUND4_PREREG.md`,
  `GENERALIZATION_PREREG_DRAFT.md`, `DEFENSIBILITY_BATCH_PROTOCOL.md`,
  `CONVERGENCE_CAMPAIGN.md`

### Structure of this document

The **main review** (findings F1–F27, Parts 1–4, amendments A1–A12) is reproduced first,
verbatim as delivered. The **addendum** (corrections C1–C2, findings F28–F36, revised
recommendation and verdict, amendments A13–A20), written after a panel-truth inventory
returned, follows verbatim. Nothing has been revised, reconciled, or softened between the
two parts; where the addendum corrects the main review it says so explicitly.

---
---

# PART ONE — MAIN REVIEW (verbatim)

---

# ADVERSARIAL REVIEW — licensing experiments L1 / L2

Ground-truth artifacts consulted:
`/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/behavior_pilot/` — `RETRANS_REVIEW_DISPOSITION.md`, `ITERATION_NOTES.md` (0031, 0036, 0042), `qc_canonical_values.json`, `qc_emergent_schema.json`, `qc_emergent_ann_{A,B}.json`, `query_class_corpus.json`, `qc_separability_census.py`, `RETRANS_INTEGRATION_CENSUS.json`; and `/Users/mattstults/.../semi-formal-experiment/spend.py`.

---

## PART 1 — If L1 passes exactly as written, is Q-A answered YES?

**NO.** L1 as registered is (a) already satisfied by evidence the project has itself ruled inadequate, (b) measuring the wrong quantity, and (c) unspecified on every parameter that determines whether it can fail.

### F1. L1's relevance clause is ALREADY PASSED by the exact numbers that demolished 0041. Fatal.
**Defect.** L1 requires "relevance prediction over the representation must beat majority baseline." The demolition's own CoVe re-derivation reports 1-NN at **0.72 vs base 0.60** (tradeoffs, n≈150) and **0.70 vs 0.59** (user-autonomy, n≈122). Those *beat* the majority baseline, and beat it significantly: one-sided binomial vs p₀ = 0.60 gives **p = 0.0015** (108/150) and **p = 0.0097** (85/122). So the clause is not a hurdle — it is a restatement of the result the review called "at or near majority-class base rate."
Worse, the project has already ruled on this exact effect size in the opposite direction: `ITERATION_NOTES.md` 0031 records "**NO canon form field carves behaviour relevance (best 0.70 vs 0.59 base)**" as a *failure*. The same numbers cannot be a failure in 0031 and a pass in L1.
**Why it matters for Q-A.** L1 could be "run" today, at $0, and would return PASS on its relevance clause, licensing a 600-node campaign on the strength of a base-rate predictor. This is erratum #21 recurring for the fourth time: a pass condition that cannot fail.
**Fix (registered condition).** Delete "beats majority baseline." Replace with the project's own operative standard: *the representation must reach ≥ (panel-internal agreement − δ) on positive-class F1 or MCC, δ pre-registered at ≤ 0.05, AND must beat a raw-clause-text baseline (TF-IDF and/or a frontier judge reading the clause string) by a pre-registered margin.* Report AUC/MCC, never accuracy, and report panel-internal agreement as the ceiling. Notes 0036 already records that "L1 over full symbolic space and TF-IDF both at base rate" — so the text baseline is the comparator that actually decides whether translation buys anything.

### F2. "Separability" as implemented is signature UNIQUENESS, which is not the Q-A quantity and is arguably anti-correlated with it.
**Defect.** `qc_separability_census.py` defines `separability = len(distinct_signatures) / n`. That is a fingerprinting metric. Q-A asks whether the representation distinguishes *which clauses bear on which behaviours* — i.e. whether nodes relevant to behaviour X are systematically separated in signature space from nodes not relevant to X. Uniqueness is neither necessary nor sufficient: two clauses that bear on exactly the same behaviours in exactly the same way *should* collide, and a representation optimized for uniqueness degenerates into text fingerprinting — which the project already measured and named (`b2adc1f6`: value-layer separability "is mostly fingerprinting", 0% node reuse). Pushing sep→1.00 is the failure mode, not the goal.
**Why it matters for Q-A.** L1 can score sep 1.00 with a large null margin and still carry zero relevance information — precisely the 0041 outcome.
**Fix.** Retire uniqueness as a pass condition. Register **truth-aligned separability**: for each behaviour with panel truth, compute (i) AUC of a signature-space classifier for relevant-vs-not, (ii) the ratio of mean within-class to between-class signature distance, (iii) the collision rate *between truth-discordant pairs only* (nodes that differ in relevance to at least one scored behaviour). Uniqueness may be reported descriptively; it may not be a pass condition.

### F3. L1 does not test annotation reliability at all, and the reliability ceiling caps everything downstream.
**Defect.** Two blind seats agreed on the exact dimension set for **23/39** nodes (41% disagreement), masked by pooling. L1 says nothing about seats, blinding, or agreement, and its "score separability of the held-out half" is silent on whether scoring is per-seat or pooled — pooling is exactly the move that hid F8.
**Why it matters for Q-A.** A 600-node campaign whose per-node dimension assignment is reproducible only 59% of the time cannot support "complete representability." Predictive validity is bounded above by reliability; measuring validity without reliability makes a failure uninterpretable and a pass unbelievable.
**Fix.** Register: two independent blind seats annotate every L1 node; **all metrics are computed per seat and reported per seat — pooling across seats is prohibited**; report exact-dimension-set agreement, Jaccard agreement, and Krippendorff α over the 24-dimension indicator matrix; **pre-register a reliability floor (α ≥ 0.67) as a gate that runs BEFORE any separability or relevance metric is computed**, and a hard rule that a run failing the floor is void, not renegotiated.

### F4. Held-out-half induction fixes only the *mid-lattice* circularity. The vocabulary leak — and the document leak — survive.
**Defect.** The 24 dimensions × 105 canonical values were open-coded from `query_class_corpus.json`, whose source distribution is **29/100 entries drawn from the OpenAI Model Spec itself** (plus 12 Anthropic, 10 Anthropic Usage Policy, 11 the project's own behaviour set, 9 HHH, 24 one-line Sparrow rules, 6 Llama Guard). L1 holds out half the spec's *nodes* from mid induction, but every held-out node is scored against a vocabulary that was induced with that same document in view. Separately, mid induction over a fixed 105-value vocabulary shared by both halves is near-trivially transferable: the held-out half tests whether new nodes need new *values* (coverage), not whether the buckets are non-arbitrary — and the null already showed arbitrary buckets do as well.
**Why it matters for Q-A.** A pass reads as "the ontology transfers within the OpenAI spec," which is a weaker claim than Q-A, and it is contaminated even for that.
**Fix.** Register: (a) an explicit contamination audit — for every held-out node, record whether its section concept appears among the 29 spec-derived corpus entries, report metrics **separately for contaminated and clean held-out nodes**, and treat the clean subset as the headline; (b) a second, harder arm — induce mids from a corpus with the 29 spec-derived entries removed, and report the delta; (c) state up front that L1 bounds *within-document* transfer only, and that Q-A's "complete representability" claim is licensed only on the clean subset.

### F5. Every operational parameter of L1 is unspecified, so it cannot be pre-registered as written.
**Defect.** "HALF the spec's nodes" does not say: half of the ~600, or half of the 39-node problem-stratified sample; how the split is drawn; who annotates; blind to what; which representation layers enter the signature (dimensions only, or + inputs/outputs/atoms); which readout model. If the split is over the existing 39, each half is n≈19 — no power for anything.
**Why it matters for Q-A.** Q-A is about a *complete* retranslation. Testing a half of a sample that was deliberately stratified on known-problem nodes generalizes to nothing.
**Fix.** Register verbatim before any run: fresh **uniform random draw from the full ~600-node graph**, sample size and seed stated; the 39-node problem-stratified sample **excluded** (or scored separately as a stress arm, never pooled); split drawn and hashed before annotation; seats blind to the panel truth, to the split membership, to the census, and to this design document (per the standing "a cycle's design document is never seat material" rule); the exact feature set entering the signature; the readout family.

### F6. "Report margin over the null" is a reporting instruction, not a pass condition — and the null is under-specified.
**Defect.** L1 says report the margin. It does not say what margin passes, what null distribution, how many seeds, or what happens at margin ≈ 0. The BINDING rule adopted in the same document says a claim "is only as strong as its margin over the null" — which without a threshold is unfalsifiable, the same defect the rule was written to kill. Also unspecified: matched on *what*. The 0041 null matched bucket count per family; a properly matched null must also match per-node handle counts and the empirical family-usage distribution (which is highly skewed — `operational_uplift` 12/100, `agentic_action_footprint` **1/100**).
**Fix.** Register: ≥1000 seeded null draws, matched on item count, family structure, bucket count per family, per-item handle count, and empirical family-usage frequency; the observed statistic must exceed the **99th percentile** of the null; report the effect as a z-score or percentile, not a difference of ratios; and state explicitly that a margin below threshold is a FAIL that stops the campaign, not a caveat.

### F7. Splitting the graph in half destroys the power of the only clause that matters.
**Defect.** Panel truth exists for ~150 and ~122 nodes. A random half-split leaves ~75 and ~61 truth-bearing nodes in the held-out half. Power to detect a true 0.72 accuracy against a 0.60 base at α = 0.05 is **0.66 at n = 75 and 0.56 at n = 61** — a coin flip. (At the full n = 150/122 it is 0.91/0.86.)
**Why it matters for Q-A.** L1 is structured so that its one substantive clause is measured on the underpowered half. Both a pass and a fail would be uninformative.
**Fix.** Decouple the two clauses: induce mids on a *node* half-split, but score relevance on **all** truth-bearing nodes not used in induction, and if that is fewer than a pre-registered n, use k-fold induction (5-fold, mids re-induced per fold) so every truth-bearing node is scored out-of-fold. Register the minimum detectable effect at the achieved n before running.

### F8. Two behaviours cannot answer a question about "which clauses bear on which behaviours."
**Defect.** Q-A is a statement about a behaviour × clause matrix. L1 scores two behaviours, both in-corpus, previously measured near-orthogonal (φ 0.04–0.29, notes 0036). With k = 2 there is no between-behaviour variance estimate; a pass is a single anecdote reported twice.
**Fix.** Register a minimum of **5 behaviours with adjudicated truth** for the relevance clause, spanning at least two of the project's own behaviour classes, with per-behaviour results reported individually and the **worst** behaviour, not the mean, as the headline. Existing partial truth (round4 helpfulness / harm-avoidance-to-third-parties / avoiding-over-and-under-caution rulings, `ITER*_TRADEOFFS_REPAIR_TRUTH.json`, `ua_truth_sealed.json`) should be inventoried first — some of this may already be on disk at $0.

### F9. L1 does not measure whether the ontology is *alive* on the held-out half.
**Defect.** Four dimensions never fire on the 39-node sample; on the 100-definition corpus, `agentic_action_footprint` fires **1/100** and `integrity_of_human_oversight` **1/100**, and each has exactly **one** canonical value. Two dimensions (`no_operational_handle`, `bare_value_word_left_undefined`) are explicit catch-alls, one of whose values is literally named `undefined_harmfulness_catch_all`. A held-out half can score "full coverage" while a large share of its signature mass lands in catch-alls or singleton dimensions.
**Fix.** Register as a reported gate: per-dimension and per-value firing rates on the held-out half; the fraction of nodes whose signature is **entirely** catch-all or singleton-valued (pre-registered ceiling, e.g. ≤ 10%); and a rule that any dimension firing on 0 held-out nodes is declared dead and removed from the effective-ontology size used in all null matching (an ontology with 4 dead dimensions is a 20-dimension ontology, and the null must be matched to the live one).

**Verdict on Part 1:** L1 as written, passed, licenses nothing. It re-runs a uniqueness metric that is the wrong construct, against a relevance bar that its own demolished data already clears, on an underpowered half of an unspecified sample, without measuring reliability, and against a null with no threshold.

---

## PART 2 — If L2 passes exactly as written, is Q-B answered YES?

**NO.** L2 is the vacuousness trap in a new costume, and it violates the binding rule adopted three paragraphs above it in the same document.

### F10. "Coverage without new coinage" is satisfiable by construction — the schema contains named coverage sinks.
**Defect.** `bare_value_word_left_undefined` has the value `undefined_harmfulness_catch_all`; `no_operational_handle` has `names_a_tension_without_a_deciding_property`. Any novel behaviour definition can be assigned to one of these with zero coinage and zero information. Separately, `agentic_action_footprint` has exactly one value (`irreversible_side_effects_and_proportionality`) and `integrity_of_human_oversight` exactly one (`evasion_and_evidence_tampering`) — so *every* agentic/tool-use/multi-agent held-out definition is guaranteed "covered" by a single pre-existing value. L2's pass condition is met before the experiment starts, for exactly the classes L2 was designed to stress.
**Why it matters for Q-B.** Q-B asks whether novel behaviours fall in the *span* of the corpus. Landing every novel agentic behaviour on one value is evidence that they do **not** — the ontology is collapsing them, not spanning them — yet L2 scores that as a pass.
**Fix.** Register coverage as **discriminative coverage**: an assignment counts only if (a) no component is a catch-all dimension, (b) no component is the sole value of its dimension, (c) the resulting signature is distinct from every other held-out behaviour's signature, and (d) the signature is distinct from that of the most-similar in-corpus definition (nearest neighbour reported explicitly). Report catch-all rate and singleton rate as first-class results, not footnotes.

### F11. L2 ships with no null — in direct violation of the binding rule adopted in the same document.
**Defect.** The BINDING METHOD RULE says every representability claim ships with a matched-granularity random-partition null, and a pass condition satisfiable by noise is void as registered. L2 makes a representability claim and has no null. A random assignment of existing (dimension, value) pairs achieves "coverage without new coinage" at **100%** by construction.
**Fix.** Register the null explicitly for L2: random assignment of 1–3 existing (dimension, value) pairs per held-out definition, matched to the empirical handle-count distribution, ≥1000 seeds; the real annotation must beat it on *discriminative* coverage and on agreement with a blind second seat at the 99th percentile. If it cannot, L2 is void as registered — by the project's own rule.

### F12. Expressing a definition in the schema does not show the representation can SEPARATE or MATCH it against the spec.
**Defect.** L2 tests a property of the *definition side only*. Q-B's operative content is: given a novel behaviour, does the representation of the spec's clauses suffice to determine which clauses bear on it, matching the frontier panel. L2 never touches spec nodes, never touches panel truth, and never produces a relevance judgment. It measures the schema's descriptive elasticity — which the project has already twice measured and twice found to be the wrong signal (the fingerprinting finding, the null finding).
**Fix.** L2 must be an end-to-end relevance test, not a coverage test. Register: for **≥3** held-out out-of-corpus behaviours, obtain panel relevance truth over a stratified node sample, then score the representation's relevance determination against it under the same metrics as F1. Coverage-without-coinage may remain as a cheap necessary-condition pre-gate, explicitly labelled as such and explicitly non-licensing.

### F13. n ≥ 10 is arithmetically incapable of supporting the claim.
**Defect.** With 10/10 successes, the exact one-sided 95% lower bound on the true coverage rate is **0.741**. L2 passing perfectly is consistent with the ontology missing **1 in 4** novel behaviours. And if the true miss rate were 20%, L2 would return a clean 10/10 sweep **10.7%** of the time. At n = 30 the lower bound is 0.905 and the 20%-miss sweep probability drops to 0.1%.
**Why it matters for Q-B.** A funding decision on a 600-node campaign cannot rest on "coverage is somewhere above 74%."
**Fix.** Register **n ≥ 30** held-out definitions with a **minimum of 5 per named out-of-space class** (agentic/tool-use, multi-agent, trajectory-shaped, multi-turn/longitudinal, oversight/control), a pre-registered pass threshold stated as a lower confidence bound (e.g. "95% LCB on discriminative coverage ≥ 0.85"), and a pre-registered fail action (which dimensions would have to be added, and what that does to campaign cost).

### F14. Nobody is named as the author of the held-out definitions, so they will be written to fit.
**Defect.** L2 says "≥10 held-out behaviour definitions NOT drawn from the corpus's documents." Left to the pipeline, these get written by an agent that has the 24-dimension schema in context. This is the fourth recurrence of designer-vocabulary smuggling (errata: designer vocabulary, grandfathered places, noise-satisfiable census).
**Fix.** Register: definitions are **lifted verbatim** from documents published outside the corpus, never authored; the source documents are named, hashed, and committed **before** any seat sees them; source selection is done by a seat **blind to the 24-dimension schema**, briefed only on "behaviour/trait/rule definition, these classes"; the frozen definition set is committed with its hash pre-annotation. Also register a *no-quarantine* rule: the Anthropic constitution and Anthropic Usage Policy are **already partly in the corpus** (22/100 entries) and are therefore not valid held-out sources.

### F15. "No new coinage" conflates dimension-level closure with value-level coinage, and penalizes a healthy ontology.
**Defect.** The claim worth testing is that the **24 dimensions** are closed — that novel behaviours need no new *axis*. Needing a new *value* within an existing dimension is exactly what a healthy ontology does when it meets a new domain. L2 scores both as failure.
**Fix.** Register two separate numbers with separate thresholds: **dimension-level closure** (pass = zero new dimensions required; this is the P2 claim) and **value coinage rate** (reported, permitted up to a pre-registered rate, e.g. ≤ 30% of assignments, with each coinage reviewed for whether it is a genuine new value or a disguised new dimension).

**Verdict on Part 2:** L2 passed licenses nothing about Q-B. It is a test of schema elasticity with named catch-alls in the schema, no null, no separation, no panel truth, and an n whose best possible result is consistent with a 26% miss rate.

---

## PART 3 — Are L1 + L2 jointly sufficient for the funding decision?

**NO**, for a reason neither addresses: **neither experiment compares the representation to the cheap alternative it must beat.**

### F16. The funding decision is a comparison, and no registered experiment makes it.
**Defect.** The campaign's proposition is that translating ~600 clauses into a symbolic representation makes relevance determinable. The default that must be beaten is: hand a frontier model the raw clause text and the behaviour. Notes 0036 already records that the symbolic space and TF-IDF are **both at base rate**, while frontier panels are the truth standard — i.e. raw text plus a frontier model is currently *strictly better* than the representation. Neither L1 nor L2 measures this gap. Both could pass while the campaign has negative expected value.
**Fix.** Register the comparison as the gate: no campaign is funded unless the representation-only arm reaches within a pre-registered δ of the raw-text arm on the same nodes, same behaviours, same judge.

### F17. THE SINGLE STRONGEST EXPERIMENT — the blind-readout information-equivalence ablation (run this instead).
This is what Q-A actually asks, it uses truth already on disk, and it fits the remaining budget.

**Design (register verbatim before running).**
- **Items:** all nodes with existing adjudicated panel truth for the two scored behaviours (~150 and ~122), plus any additional behaviours whose partial truth is already on disk, scored per behaviour.
- **Arms, same frontier judge, same prompt skeleton, same output schema, order-randomized, run blind to each other:**
  - **Arm T (ceiling):** the raw clause text + the behaviour definition → relevant / not.
  - **Arm R (the claim):** *only* the symbolic representation of that clause — dimensions + values + inputs/outputs/atoms handles, **no natural-language span, no section title, no node id** → relevant / not.
  - **Arm N (null):** the same symbolic representation with values permuted within dimension under a seeded random map, ≥100 seeds on a subsample.
- **Pre-registered pass condition:** `MCC(R) ≥ MCC(T) − 0.05`, **and** `MCC(R)` above the 99th percentile of Arm N, **and** both reported per behaviour with the worst behaviour as the headline, **and** `MCC(T)` itself reported against panel-internal agreement so the ceiling is visible.
- **Pre-registered fail action:** a leakage audit on Arm R (can the judge reconstruct the clause from the signature? if yes, Arm R is contaminated and void), then a per-node error triage naming which dimensions were missing.
- **Why this is decisive:** it is a direct test of *sufficiency of the representation* — the literal Q-A claim — under the user's own operative standard (match the panel, or be frontier-justifiable). It cannot be passed by uniqueness, by fingerprinting, by catch-alls, or by noise. A pass licenses the campaign outright; a fail says exactly which dimensions to add before spending.
- **Cost:** ~272 nodes × 2 arms ≈ 550 short frontier calls, plus a seeded-null arm on a subsample. `spend.py` reports **$17.179 of the $25.00 BUDGET (69%)**, leaving ~$7.8 headroom, and the reported total is flagged as an overstatement (4,645 uncached-rate rows, plus unidentifiable batch-billed rows). This fits, but register a stratified 120-node-per-behaviour subsample as the fallback if a cost pre-flight exceeds a pre-registered ceiling, and route the null arm through the cheap tier with a frontier parity check on a subsample (the project's established pattern).

### F18. The cheap companion that caps everything — run it first, at near-zero cost.
Two blind seats annotate a **fresh uniform random 60-node draw** from the full graph (not the problem-stratified 39). Report exact-dimension-set agreement, Jaccard, and α. This is the reliability ceiling on every number the campaign will ever produce; at 23/39 today it may kill the campaign for under $1 before any panel spend. Register it as a **gate that runs before F17**, with α ≥ 0.67 as the pre-registered floor.

### F19. What is missing from the funding decision even if F17 passes.
No registered experiment estimates the campaign's **cost curve or its degradation at scale**: 600 nodes × 2 blind seats × a merge seat, with a reliability figure measured on 39 problem-stratified nodes. Register a scaling pre-flight: annotate a random 60-node draw end-to-end through the full pipeline (translate → merge → lattice), record wall-clock, $, seat disagreement rate, and merge-arbitration rate, and extrapolate to 600 with the measured per-node figures. Fund on `F18 pass AND F17 pass AND a scaling estimate inside budget` — not on any two of three.

---

## PART 4 — Ways L1 / L2 could FAIL SPURIOUSLY (false negatives that also mis-spend the budget)

### F20. 1-NN over sparse binary Jaccard is a weak, high-variance readout.
With ~1.2 handles per item and 105 values, most pairs have Jaccard 0; ties are broken arbitrarily. An adequate representation could score at base rate purely from readout weakness.
**Fix.** Register a readout family — 1-NN, L2-regularized logistic regression on dimension+value indicators, and a frontier judge on signature-only (Arm R above) — with the **frontier-judge arm decisive** and the others reported. "The representation does not carry the concept" may only be concluded if the *best* readout fails.

### F21. Accuracy under 60/40 imbalance is a broken metric in both directions.
A representation that recovers the 40% minority well can score below a majority-class predictor on accuracy.
**Fix.** Register MCC and positive-class F1 as primary; accuracy reported only alongside base rate; class-balanced resampling reported as a secondary.

### F22. Panel truth is itself noisy, so the achievable ceiling is below 1.0 and is currently unmeasured.
If panel-internal agreement is, say, 0.85, a representation at 0.83 is functionally perfect but reads as a fail against any absolute bar.
**Fix.** Register: panel-internal agreement (or the adjudication seat's own test-retest) is measured and published as the ceiling; the representation is scored as **% of ceiling attained**, with the pass threshold expressed in those terms.

### F23. The spec's halves are not exchangeable — either split is wrong in a different direction.
A random node split leaks (adjacent clauses in one section share vocabulary); a section-blocked split makes the held-out half out-of-distribution for topical reasons unrelated to ontology adequacy. Either can produce a spurious fail (section-blocked) or a spurious pass (random).
**Fix.** Register **both** splits, report both, and pre-declare section-blocked as the honest estimate and random-node as the leakage upper bound. A gap between them is itself a reportable result.

### F24. A held-out definition may be inexpressible because it is badly written, not because the ontology is inadequate.
The corpus itself contains items with `no_operational_handle` — definitions that supply nothing decidable. Out-of-corpus sources will contain more.
**Fix.** Register a blind pre-screen seat that rules each candidate definition behaviour-shaped **before** annotation, with exclusions logged and counted; and register that if the exclusion rate exceeds a pre-registered ceiling, the source-selection procedure — not the ontology — is what failed.

### F25. "No new coinage" can fail on a healthy ontology.
See F15. As written, a correct and useful ontology that mints one new value for a genuinely new domain scores as a failure.
**Fix.** Split the metric per F15.

### F26. Seat model tier could produce a fail unrelated to the ontology.
Small-model seats may under-annotate where the ontology is fine — and the project's standing rule is that seat/frontier divergence is a *seat defect*.
**Fix.** Register a frontier-parity check on a ≥20-item subsample for every seat used in L1/L2, run **before** the main results are read, with divergence voiding the run.

### F27. Both experiments lack a stated stopping/void rule, so a spurious fail invites re-running until it passes.
**Fix.** Register: one run per registered design; a fail is published with its number; any re-run requires a new registration naming the change and the reason, and both results appear in the record. (This is the project's existing "no post-hoc granularity shopping" rule — bind it explicitly to L1/L2.)

---

## OVERALL VERDICT

**DOES-NOT-LICENSE.**

Passing L1 and L2 exactly as written would **not** answer Q-A or Q-B. The decisive reasons, in order of severity:

1. **L1's relevance clause is pre-satisfied.** 0.72 vs 0.60 (p = 0.0015) and 0.70 vs 0.59 (p = 0.0097) already "beat the majority baseline." The project's own notes 0031 call the identical effect size "NO field carves behaviour relevance." L1 could be marked PASS today, at $0, on the data that demolished 0041. That is a pass condition that cannot fail — erratum #21, fourth recurrence.
2. **L2 has no null**, in explicit violation of the binding rule adopted in the same document, and its pass condition is met by construction: the schema contains a value literally named `undefined_harmfulness_catch_all`, and the two dimensions L2 exists to stress (`agentic_action_footprint`, `integrity_of_human_oversight`) each hold exactly **one** value fired by exactly **1/100** corpus definitions.
3. **Neither experiment measures the Q-A construct.** Separability-as-implemented is signature uniqueness — a fingerprinting metric the project has already caught fingerprinting. Coverage-without-coinage is schema elasticity. Neither is "which clauses bear on which behaviours."
4. **Neither compares against the alternative the campaign must beat** — a frontier model reading the raw clause. On existing evidence that alternative wins, which makes the campaign negative-value regardless of L1/L2.

These are defects in the *measurements*, not proof the ontology is inadequate — the same distinction the 0041 disposition drew, and it still holds. But on the funding question the burden runs the other way: the designs as registered cannot discharge it.

**Amendments that would convert this to LICENSES-WITH-AMENDMENTS**, in dependency order:

- **A1 (gate, ~$0, run first).** F18: fresh random 60-node draw, two blind seats, α ≥ 0.67 pre-registered floor, all downstream metrics per-seat, pooling prohibited (F3).
- **A2 (the experiment).** Replace L1 with F17's blind-readout ablation — Arm T / Arm R / seeded Arm N, MCC(R) ≥ MCC(T) − 0.05 and above the 99th null percentile, per behaviour, worst-behaviour headline, panel-internal agreement published as the ceiling (F1, F2, F16, F20–F22).
- **A3.** Extend the relevance clause to ≥5 behaviours using truth already on disk; inventory partial truth before spending (F8).
- **A4.** Replace L1's half-split with 5-fold out-of-fold induction so every truth-bearing node is scored, plus both random-node and section-blocked splits reported (F7, F23).
- **A5.** Contamination audit: 29/100 corpus entries are OpenAI Model Spec; report clean vs contaminated held-out nodes separately, clean subset as headline; state that L1 bounds within-document transfer only (F4).
- **A6.** Pre-register every L1 parameter — sample frame, seed, seats, blinding, feature set, readout — and exclude the problem-stratified 39 from the headline (F5).
- **A7.** Null threshold: ≥1000 seeds, matched on family-usage frequency and per-item handle count, 99th percentile, fail = stop (F6). Dead-dimension audit and catch-all/singleton ceiling reported (F9).
- **A8.** Rebuild L2 as: n ≥ 30, ≥5 per out-of-space class, verbatim-lifted definitions from sources chosen by a schema-blind seat and hashed pre-annotation, Anthropic constitution and Usage Policy disqualified as already in-corpus (F13, F14).
- **A9.** L2 scored on **discriminative** coverage (no catch-alls, no singletons, distinct from all other held-out and from the nearest in-corpus definition), against a seeded random-assignment null, with dimension-closure and value-coinage as separate pre-registered numbers (F10, F11, F15).
- **A10.** L2's licensing clause becomes end-to-end: ≥3 out-of-corpus behaviours get panel truth over a stratified node sample and are scored by A2's protocol. Coverage-without-coinage survives only as an explicitly non-licensing pre-gate (F12).
- **A11.** Behaviour-shaped pre-screen with logged exclusions; frontier-parity check on every seat before results are read; one-run-per-registration rule (F24, F26, F27).
- **A12.** Fund only on `A1 pass AND A2 pass AND a 60-node end-to-end scaling pre-flight whose extrapolation to 600 fits budget` (F19). Note the budget context: `spend.py` reports **$17.179 of $25.00 (69%)**, ~$7.8 headroom, with the total flagged as an overstatement.

Without A1, A2, A9, and A10 at minimum, a PASS on L1+L2 is a repeat of 0041 with a larger n.

---
---

# PART TWO — ADDENDUM (verbatim)

*Written after a delegated panel-truth inventory returned. It corrects two premises in the
main review and adds nine findings — all of which strengthen the negative verdict except
one, which removes an objection.*

---

# ADDENDUM — corrections and nine further findings

## Corrections to the main review

**C1 — Cost premise (affects F17, A12).** Panel adjudication is **$0 API**. The $17.179/$25.00 in `spend.py` is corpus translation and matching spend (DeepSeek-V4-Flash bulk translation alone is $13.73); `usage.jsonl` has essentially no rows during the periods when the round-3/4, generalization, UA, and tradeoffs panels ran. Panel truth is produced by **Fable/Opus subagent seats**, and the real budget is Matt's Fable envelope (notes 0032: 5%/week cap), pre-registered at **~0.13–0.17M Fable tokens per 80-node panel round**, ~0.08–0.10M per 40-node generalization behaviour. My F17 experiment is therefore **not** dollar-constrained — but it must be registered against the **Fable** budget, and that is a real constraint the L1/L2 registrations also omit entirely.
**Fix.** Every registered experiment states its Fable-token cost estimate alongside its $ cost, per the existing prereg pattern.

**C2 — Scale (affects F5, F7).** The graph is **773 nodes** (`graph_v2/node_corpus_all.json`; 593 at root unwind per `GRAPH_OVERVIEW.md`), not ~600. More importantly: `behavior_pilot/coverage_translated.json` records **`translated_nodes: 183`**. See F32.

---

## New findings

### F28. There are TWO incompatible "relevance" truths on disk, and L1 names neither. This is truth-shopping waiting to happen.
**Defect.**
- Graph-node ledger (`satisfiability_census.truth_all()`, `.../behavior_pilot/satisfiability_census.py:180-199`): helpfulness 477 nodes at **0.560** positive, harm-avoidance 291 at **0.443**, caution 285 at **0.540**.
- panel-v5 (`data/panel-v5/runlog-v5.jsonl`, 31,293 rows, pinned to `ai-character-index@ef08e676`): same behaviours over **589 model-spec passages**, majority-verdict≥2 positive rates of **0.012 (helpfulness), 0.044 (third-party-harm), 0.007 (over-under-caution)** — one to two orders of magnitude apart from the node ledger.
- The original frontier panel (`data/behaviours.json`, rubric v3w) gives a third set: 377/333/153 passages at 0.536/0.550/0.614.

Three artifacts, three constructs, all called "relevance." L1 says "relevance prediction over the representation must beat majority baseline" without naming the ledger, the unit (node vs passage), or the threshold (any-judge≥2 vs majority≥2 vs score≥2).
**Why it matters.** "Beats majority baseline" means something wildly different at base rate 0.56 than at 0.007 — at the latter, a constant-negative predictor scores 0.993 and *nothing* beats it on accuracy. And with three ledgers available, a failing run can be re-scored against another until one passes. This is the granularity-shopping the project already banned once (`dd8abd55`).
**Fix (registered condition).** Name the ledger, the unit, and the threshold **in the registration, before running**. Register the graph-node ledger at node granularity as primary (it is the only one at the unit the campaign produces), panel-v5 as a pre-registered secondary replication, and prohibit re-scoring against a second ledger without a new registration naming the change. Separately: publish the **cross-ledger agreement rate** on the nodes/passages that join. If two frontier-panel constructs of "relevance" disagree this much, the construct validity of the target itself is unestablished, and that is a prior question to Q-A.

### F29. Q-B is circular by construction: every behaviour with panel truth is IN the 100-definition corpus, because 11 corpus entries ARE the project's own behaviour set.
**Defect.** `query_class_corpus.json`'s 100 ids break down as `ms:` 29, `sparrow:` 24, `anthropic-constitution:` 12, `anthropic-aup:` 10, **`adria:` 11**, `hhh:` 9, `llamaguard:` 6. Every behaviour with adjudicated node truth maps into the `adria:` block: helpfulness, third-party-harm, over-under-caution, tradeoffs, user-autonomy, harmlessness-to-user, objectivity, general-welfare, proportionate-risk. panel-v5's two additional defined behaviours (`no-sycophancy`, `undermine-oversight`) are *also* in the corpus and have **zero rulings** in the runlog. The one behaviour outside the 100 — `animal-welfare-impacts` — has citation coverage only (`data/panel-coverage.json`) and **zero** adjudicated relevant/not_relevant rulings anywhere.
**Why it matters for Q-B.** The 24×105 ontology was open-coded from a corpus that includes the definitions of the very behaviours it is scored against. There is **no out-of-corpus panel truth in this repo at all**. L2 as written does not fix this, because L2 never produces a relevance judgment (F12) — so if L2 passes, Q-B remains untested by construction, not merely under-tested.
**Fix.** Register explicitly: **Q-B cannot be answered by any experiment that does not create new out-of-corpus panel truth.** Minimum: 3 out-of-corpus behaviours × a uniformly drawn, fully ruled node block (the fresh-draw pattern, ~80 nodes each ⇒ ~0.4–0.5M Fable, $0 API), with the behaviour definitions selected per F14 and frozen pre-annotation. `no-sycophancy` and `undermine-oversight` are **not** eligible (in-corpus). This is the single largest gap in the licensing plan and it is affordable.

### F30. `panel-v5` is a large, pinned, externally-authored truth set that neither L1 nor L2 uses.
**Defect.** 9 behaviours × 589 model-spec passages, 3 judges each (5 for proportionate-risk), rubric committed, provenance byte-identical to an external repo — i.e. truth the project did not author, already frozen, at $0. It is unexploited.
**Why it matters.** External-provenance truth is the strongest defence against the designer-smuggling erratum series. It also gives 9 behaviours where L1 gives 2 (F8).
**Fix.** Register panel-v5 as the pre-registered replication tier for the relevance clause — but only after a committed **join audit**: passages→nodes is not an identity map, and the join must be built, hashed, and its coverage/ambiguity rate published before any metric is computed. Score with class-aware metrics only (F21); at majority≥2 positive rates of 0.005–0.061, accuracy is meaningless and 1-NN will collapse to all-negative.

### F31. The assembled truth ledger is composition-biased: positives and negatives were selected by different processes.
**Defect.** `truth_all()` assembles helpfulness's 477 nodes from: the base `arm_ab.truth_for()` block (157), `panel_run1/adjudication_run2_help.json` (82), **`panel_run1/agreed_negative_rulings.json` (15/behaviour, seed 20260816)**, `arm3_negative_rulings.json`, `arm2_*_fresh_rulings.json`, fresh-draw blocks, `panel_rerulings.json` precedence overlays, and a `defensibility_rulings.json` `truth_ledger_updates` entry. Negative-class nodes enter partly through dedicated "agreed negative" draws; positive-class nodes partly through escalation panels.
**Why it matters for Q-A.** Any classifier scored on this ledger can learn the *assembly process* rather than the relevance concept — and a 0.72-vs-0.60 result is exactly the size of effect that assembly artefacts produce. It also means the 0.560/0.443/0.540 base rates are properties of the assembly, not of the document.
**Fix.** Score the relevance clause on **single-process, uniformly drawn, fully ruled partitions only**. These already exist: `panel_run1/fresh_draw/HELP_RESULT.json` (80), `fresh_draw2/{HELP_R2,HARM_R2,CAUTION_R2}_RESULT.json` (80 each), `fresh_draw3/HELP_R3_RESULT.json` (80), `fresh_draw4/{HELP_R4 80, HARM_R4 57, CAUTION_R4 80}` — ~537 rulings across clean uniform draws, with sane positive rates (0.375–0.538). Register these as the evaluation set; report the assembled ledger, if at all, as a separate stratum with its composition disclosed.

### F32. L1 presupposes the campaign it is supposed to license — only 183 nodes have ever been translated.
**Defect.** `coverage_translated.json` records `translated_nodes: 183` of 773. L1 says "freeze mids induced from HALF the spec's nodes; score … the HELD-OUT half." Half of 773 is ~386 nodes that do not exist in translated form. Producing them **is** the retranslation campaign — the ~$/Fable expenditure the experiment is meant to justify. Read literally, L1 cannot be run before the decision it informs.
**Why it matters.** Either L1 silently means "half of the 39-node problem-stratified sample" (n≈19, no power, wrong frame — F5, F7), or it means a several-hundred-node translation commitment made before the licensing question is settled.
**Fix.** Register L1 explicitly as a **staged pre-flight**: a uniform random draw of N nodes (N set by a power calculation against the F31 clean partitions, and stated), translated end-to-end through the real pipeline, with wall-clock / Fable-token / seat-disagreement / merge-arbitration rates recorded — so the pre-flight simultaneously yields the licensing measurement (F17) and the scaling estimate (F19). State the pre-flight's cost as a fraction of full-campaign cost in the registration.

### F33. Existing gates have already FAILED, and L1/L2 are structured to bypass rather than reconcile with them.
**Defect.** On disk right now: `GEN_BLOCK1_SCORED.json` — how-to-approach-tradeoffs engaged-precision **0.40**, "F2 fires, block-1 **STOP RULE**"; `panel_run1/REGISTERED_RESULT.json` — **`metric0: FAIL`** on all three behaviours (helpfulness decline 3/24, panel-citation 21/24); `ITER2_ATTEMPT3_SCORED.json` prec 0.40 / decl 0.50; the OPERATIVE_TARGET mint held at TP-side coverage 0.67 vs a ≥0.70 gate. L1/L2 make no reference to any of these and would, if passed, sit alongside an un-cleared STOP RULE.
**Why it matters for the funding decision.** A licensing experiment that can pass while a prior stop rule remains fired is not a gate; it is a second opinion sought after an unfavourable first one.
**Fix.** Register a precondition: **L1/L2 results are void unless the block-1 STOP RULE and the `metric0: FAIL` findings are either cleared with a measurement or explicitly superseded by a signed ruling naming them.** The campaign decision memo must list every currently-red gate and its disposition.

### F34. **Objection withdrawn / good news:** the power problem in F7 is fixable at zero cost.
The graph-node ledger holds 477 / 291 / 285 truth-bearing nodes (union 644 across three behaviours), plus UA 175 and tradeoffs 75 — far more than the ~150/~122 I assumed. Restricting to the clean uniform draws of F31 still leaves ~537 single-process rulings. **F7's underpowered-half concern therefore disappears entirely if L1 is scored out-of-fold on the full clean partition set instead of on a single held-out half** — at n = 477 the power to detect 0.72 vs 0.60 is ≈0.999, and n = 80 per fresh-draw block supports per-block replication. This is the one place where the registrations are more conservative than they need to be, and the fix (A4: k-fold out-of-fold induction) costs nothing.

### F35. `ua_truth_sealed.json` is the repo's only genuinely held-out truth partition, is single-use, and is at risk of being spent on the wrong question.
**Defect.** 38 nodes (11 relevant / 27 not, 0.289), marked **"SEALED — single-use at the registered confirmation; must not enter visible truth."** It is the closest thing the project has to an uncontaminated confirmation set. Neither L1 nor L2 mentions it, which means an unregistered run could burn it.
**Fix.** Register: the UA seal is **not** available to L1 or L2. It is reserved for the single registered confirmation it was created for, and any proposal to redirect it requires a signed ruling naming what it is being spent on and what is given up. Add a repo-level guard: a test asserting that no L1/L2 scoring path reads `ua_truth_sealed.json` (the project's existing `FORBIDDEN` / `QUERY_MODULES` registration pattern).

### F36. UA's own ledger shows the base-rate problem is behaviour-dependent, which breaks any single pass threshold.
**Defect.** Positive rates across the truth on disk span **0.005 to 0.614** — user-autonomy visible 0.255, tradeoffs iter-1 0.350 / iter-2 0.467, fresh draws 0.375–0.538, panel-v5 majority 0.005–0.061, original panel 0.536–0.614. L1's single "beats majority baseline" bar is not comparable across behaviours and is trivially satisfiable at the extremes.
**Fix.** Per-behaviour thresholds expressed in ceiling-relative, class-aware terms (F21, F22): MCC and positive-class F1 against panel-internal agreement, with the **worst** behaviour as the headline (A3), never a pooled mean.

---

## Updated Part 3 recommendation

F17 stands as the single strongest experiment, with these revisions from the inventory:

- **Items:** the F31 clean uniform fresh-draw partitions (~537 rulings across helpfulness / harm-avoidance / caution), **not** the assembled `truth_all()` ledger; panel-v5 (589 passages × 9 behaviours) as a pre-registered replication tier after a committed join audit.
- **Cost:** $0 API. Register the **Fable-token** estimate instead (~0.13–0.17M per 80-node ruled block is the project's own measured unit; the two readout arms are judge calls over already-ruled nodes, so the marginal cost is arm-count × block size).
- **Behaviour count:** 9 behaviours have some truth, so A3's "≥5 behaviours" is achievable today at $0.
- **Added, non-optional (F29):** ≥3 **out-of-corpus** behaviours with new fresh-draw panel truth. Without this, Q-B is untestable by construction, and it is the cheapest high-value spend available (~0.4–0.5M Fable, $0 API).

---

## REVISED OVERALL VERDICT

**DOES-NOT-LICENSE** — unchanged, and now on firmer ground.

The inventory removes one of my objections (F34: power) and adds a worse one in its place: **there is no out-of-corpus panel truth anywhere in the repo, and all nine truth-bearing behaviours are inside the 100-definition corpus via its own `adria:` block.** Q-B is therefore not merely under-tested by L2 — it is untestable by any experiment currently registered, because L2 never produces a relevance judgment and no held-out behaviour has truth to judge against.

Meanwhile L1's relevance clause is (a) already passed by the demolished numbers, (b) unspecified as to which of **three mutually inconsistent relevance ledgers** it means, with base rates spanning 0.005–0.614, and (c) written against a node population 76% of which has never been translated.

**Amendments A1–A12 stand, with these additions:**

- **A13 (F28).** Name the ledger, unit, and threshold in the registration; publish cross-ledger agreement; prohibit re-scoring against a second ledger without a new registration.
- **A14 (F29).** Q-B requires new out-of-corpus panel truth: ≥3 behaviours × ~80-node uniform fully-ruled draws, definitions frozen per F14, `no-sycophancy` and `undermine-oversight` ineligible as in-corpus. **No amendment substitutes for this one.**
- **A15 (F30).** Register panel-v5 as the replication tier, gated on a committed passage→node join audit, scored class-aware only.
- **A16 (F31).** Score on single-process uniform fresh-draw partitions; disclose composition for any assembled stratum.
- **A17 (F32).** Restructure L1 as a staged translation pre-flight that yields the licensing measurement and the scaling estimate together, with its cost stated as a fraction of the full campaign.
- **A18 (F33).** Void L1/L2 unless the block-1 STOP RULE and the `metric0: FAIL` results are cleared or superseded by signed ruling; the decision memo enumerates every red gate.
- **A19 (F35).** The UA seal is off-limits to L1/L2, enforced by a registered test.
- **A20 (C1).** Every registration states its Fable-token cost, not only its $ cost.

**A14 is the load-bearing one.** Without it, L1 and L2 can both pass and Q-B will be exactly as open as it is today.
