# ADVERSARIAL REVIEW DISPOSITION — retranslation integration census (P1/P2)
(2026-08-24. Clean-context Opus reviewer returned P1 UNSUPPORTED (as
measured) / P2 UNSUPPORTED. Per standing rule, each finding was CoVe'd
against the artifacts before disposition — the decisive ones were
re-derived independently by the driver, not taken on the reviewer's
word. Verdict: THE REVIEW STANDS. The census's "INTEGRATION TEST
PASSED" headline is WITHDRAWN and superseded by this document.)

## CoVe re-derivations (driver-run, $0, deterministic)
- F1 NULL MODEL: a content-free random 4-bucket-per-family partition of
  the leaf vocabulary achieves separability 1.00 in 299/300 seeded
  trials with reuse trivially 1.00 — dominating the real mid lattice
  (1.00 sep / 0.57-0.58 reuse) on the census's own pass condition.
  CONFIRMED by re-derivation. The pass condition as registered has no
  statistical power: it is satisfiable by noise.
- F4 RELEVANCE PREDICTION: 1-NN over mid-level signatures (Jaccard)
  predicts panel relevance at 0.72 (tradeoffs, base 0.60) and 0.70
  (user-autonomy, base 0.59). CONFIRMED by re-derivation — at or near
  majority-class base rate. Separability of nodes does NOT imply the
  representation carries the relevance concept. Consistent with the
  earlier L1/TF-IDF findings (the concept lives in deep semantics).
- F8 SEAT NON-INDEPENDENCE MASKED: exact dimension-handle-set agreement
  between blind seats A and B is 23/39 (41% disagreement), invisible to
  the census metric because mids were pooled across seats. CONFIRMED
  by re-derivation (exactly 23/39).

## Dispositions of the remaining findings
- F2 (mids induced from the same 39 nodes they separate; no
  falsification condition) — ACCEPT. Circular by construction; the
  original census flagged it as a caveat but scored it as a pass anyway.
- F3 ("zero truth-distinct collisions" vacuous at leaf/mid — there are
  no collisions at sep 1.00; at top it rests on 7 single-behaviour
  pairs) — ACCEPT. The clause was decorative, not evidential.
- F5 (both scored behaviours are inside the 100-definition corpus;
  trajectory-class behaviours already recorded as out-of-space, notes
  0038) — ACCEPT on substance. One reviewer slip corrected for the
  record: "ua" is user-autonomy, not undermine-oversight; the finding
  is unchanged because user-autonomy is also in-corpus.
- F6 (corpus ~7 documents, 2021-23 single-turn-chat skew; agentic
  dimension fires 3/39; four dimensions never fire) — ACCEPT; matches
  the coordinator's own source counts.
- F7 (39-node sample stratified on known-problem nodes; more than half
  the ontology untested) — ACCEPT; that is how the sample was drawn.

## Corrected verdicts (what we can honestly claim)
- P1 (the ontology + graph inputs/outputs/atoms suffice for complete
  separation under full retranslation): NOT ESTABLISHED. The measured
  separability is real but carries no information beyond what a random
  partition of the vocabulary provides at matched granularity; and the
  representation does not predict relevance above base rate.
- P2 (extension to novel behaviours because they fall in the corpus
  space): NOT ESTABLISHED. Both test behaviours are in-corpus; the
  corpus under-covers agentic/tool-use/multi-turn; a known behaviour
  class (trajectory-shaped) is already recorded as outside the design.
- Preserved verbatim from the reviewer, and endorsed: "this is a defect
  in the *measurement*, not proof that the ontology is bad." What
  remains true: two blind seats retranslated 39/39 full spans with the
  schema and ZERO new coinages (coverage-in-form), and mid-level
  handle reuse (0.57) shows the vocabulary compresses. Those are
  necessary conditions, now honestly labeled as only that.

## BINDING METHOD RULE (adopted; applies to every future separability claim)
Every separability/representability claim ships with a MATCHED-
GRANULARITY RANDOM-PARTITION NULL (same item count, same family
structure, same bucket count, seeded), and the claim is only as strong
as its MARGIN over that null. A pass condition jointly satisfiable by
noise is void as registered. (Companion to the V5 coverage rule.)

## Licensing experiments (registered as the path to honest P1/P2, all parked)
- L1 (for P1): freeze mids induced from HALF the spec's nodes; score
  separability + reuse of the HELD-OUT half against the frozen mids;
  report margin over the random-partition null; AND relevance
  prediction over the representation must beat majority baseline.
- L2 (for P2): >=10 held-out behaviour definitions NOT drawn from the
  corpus's documents, including agentic/tool-use/multi-agent classes,
  expressed in the schema and scored for coverage without new coinage.
