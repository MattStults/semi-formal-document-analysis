# DEFINITIONAL-NODE LANE — pre-registration (2026-08-20, before any annotation ran)

## Problem (census-derived, deterministic)
25 unique mismatch nodes across the three behaviors are norm-free (asserts=[]) and
provably UNSAT at current granularity: their feature vectors are EMPTY, colliding with
every other norm-free node, 125 of which are correctly not_relevant. All 25 need
verdict=relevant (they are FNs). All 179 norm-free nodes carry `claims` (396 total).

## Negative results recorded first (deterministic link rules, $0, receipts in
## definitional_link_receipts.json)
Matt's hypothesis: definitions should feed consumers indirectly. Tested two blind rules:
1. FORMAL CHANNEL: cross-module concept reuse — DEAD. 2,351 minted concepts, only 8
   consumed by a non-minting node. Per-clause translation mints clause-local namespaces.
2. LEXICAL any-shared-token propagation (norm-free node engaged iff an engaged
   assert-bearing node shares a concept-name token): FIX 6/6/16 but BREAK 26/26/68 —
   inadmissible at every rarity threshold K∈{3,4,6,8,12}.
3. HEAD-TERM→operative-text (definition's genus term appears in an engaged node's
   assert read_backs): FIX 5/5/13, BREAK 19/21/52 — inadmissible.
Diagnosis: break lists are dominated by l1_170_* structural/meta nodes (document layout,
term scaffolding). Separating "substantive elaboration" from "structural description"
requires reading claim content = an annotation judgment, not string matching.

## Design (uses only existing, validated machinery)
Annotate CLAIMS of norm-free nodes with the SAME schema the assert lanes use
(Opus annotation lane: parity PASSED — actor 0.96, purpose 0.94–0.96):
per claim: described canonical acts (empty allowed), actor, governs, protects, purpose.
Keys `nid|c{i}` flow through existing walls unchanged (startswith(cid+"|") matching).
Acts lifted with status "described" (sibling of example-act lifting, contract mechanism).
Expected discriminators, all pre-existing: actor=document excludes structural nodes
(actor_ok); governs_concern/purpose_concern walls give per-behavior discrimination.
NO new engagement rule is added.

## Pre-registered expectations (frozen before annotation)
- SET A (25 census FN nodes): after lifting, >=80% (20/25) become engaged for the
  behavior(s) whose truth says relevant.
- SET B (13 negative controls, deterministically sampled correctly-declined norm-free
  nodes, incl. l1_170 structural nodes): <=2 become engaged for the sampled behavior.
- CROSS-BEHAVIOR: l1368_1541_n003 / l3954_4251_n046 are FNs for helpfulness AND
  negative controls for harm — the SAME annotation must engage help and not harm
  (walls, not annotation, provide behavior-specificity). Both directions count above.
- FULL-LAYER GATE (if calibration passes and the lane broadens to all 179): charter
  arithmetic on all truth — adopt only if fixes > breaks and every new FP is either
  truth-known or held for adjudication; otherwise revert and record.
Annotation is behavior-blind: packets carry claims + span + vocabularies only — no
behavior names, no truth, no expectations.

## CALIBRATION RESULT (2026-08-20, same day, evaluated against frozen expectations)
- SET B: 0/15 wrongly engaged — PASSES (bar <=2). Cross-behavior control confirmed:
  l1368_1541_n003's single annotation engaged helpfulness and declined harm.
- SET A: 10/27 engaged — FAILS the >=80% bar.
- Full all-truth regression (layers active vs off): caution TP 102->104 FP 12->12;
  harm TP 73->75 FP 11->12; help TP 178->184 FP 12->12. Net +10 TP, +1 FP
  (harm::l1_170_n031 via purpose channel — actor-ambiguity claim, seat flagged it
  unprompted; HELD for Fable adjudication).
- Three mechanical fixes found by calibration and applied to assembly (each recorded
  in assemble_definition_layers.py): (1) empty-governs = no-information -> fail-open,
  matching assert-lane unannotated semantics; (2) contexts-only records likewise;
  (3) role-purity mapping minor->third_party (brief drift vs contract 9a).
- Residual miss classes (annotation judgments, NOT tuned toward truth):
  (i) actor=document/organization on section-scaffolding and org-commitment nodes the
      panels ruled relevant (8 nodes) — wall semantics vs panel reading;
  (ii) acts=[] conservatism on disposition/characterization claims + real vocabulary
      gaps (no act for lying, empowering) (4 nodes);
  (iii) sibling-act geometry (respond_in_manner vs answer_directly etc.) (4-5 nodes).
- DISPOSITION per prereg: bar failed -> layers PARKED at
  candidate_definition_layers/ (instrument unchanged; mechanism in relevance_by_act.py
  is inert without the files). Adoption, seat-2 escalation on the judgment classes,
  and broadening to all 179 norm-free nodes are MATT'S RULING. Note the lane is
  strictly non-negative on measured truth except the one held FP.

## FP ANALYSIS + CHANNEL SCOPE RULING (2026-08-20, Matt directed "look into the FP")
harm::l1_170_n031 mechanics: claims C1/C3 ("AI systems carry potential risks",
"not all risks can be mitigated through model behavior alone") were annotated
actor=assistant + purpose=harm-prevention; seat-1 itself flagged the actor call as
ambiguous ("about AI systems in the abstract... organization framing arguable").
harm declares purpose_concern harm-prevention -> act-independent purpose channel
fired; protects_ok passed via an 'unspecified' value. Harm truth: not_relevant
(meta-commentary on the safety landscape, not conduct guidance).
Measured decomposition: ALL 10 lane fixes engage via the ACT channel; the purpose
channel's ONLY definitional firing is this FP.
RULING (structural, not per-node): channels apply where they were calibrated. The
purpose OR-channel was verdict-gated on the assert lane and never validated for
definitional claims -> definitional keys (nid|c{i}) do not feed purpose_hit
(relevance_by_act.py). Removes the FP at zero fix cost; the lane is now
act-channel-only, matching everything its calibration validated. The tempting
alternative — flipping this one node's actor to organization — is rejected BY NAME
as label-directed annotation editing; seat-2 may reach that actor independently.
