# ACT-REFINEMENT SUBTYPE MINT — pre-registration (Arc1-b, 2026-08-21)

Campaign item Arc1-b (HANDOFF_CURRENT.md campaign section). Frozen BEFORE any
annotation runs; corrections append, never edit.

## What is minted and why
Two act-refinement subtypes from split mining (panel_run1/convergence/
split_mining_candidates.json, seat report split_mining_report.md):
- provide:forbid.form_equivalence — the span states that changing the FORM of
  delivery does not change how a rule applies (encoded/translated/disguised
  rendering counts the same as direct).
- exhibit:illustrate — the span is a WORKED EXHIBIT (Example-headed, simulated
  exchange markup, GOOD/BAD annotations) rather than a statement of the norm.
Convergent provenance: the decl-search L1 residuals and the Opus split miner
converged blind on exactly these fix families (RUN1_ASSESSMENT.md). Target:
the three collider nodes that collide on all 543 measured columns
(help::l797_830_n011, harm::l831_1000_n001, harm::l831_1000_n011).

## Annotation protocol (two seats, blind)
- UNIT: node span. Each seat sees node-id + span text ONLY — no truth, no
  mismatch lists, no collider identities, no candidate file beyond the ONE
  criterion text for the subtype it is annotating.
- SEATS: two independent annotation seats run per subtype. Seats are campaign
  subagents; the standing doctrine says annotation = Opus-tier OK. DEVIATION,
  DISCLOSED: seats run at the campaign orchestration tier, not literal Opus.
  Mitigations: the agreement gate below, adversarial review of the lane, and
  the fact that any engagement flip the mint causes is separately adjudicated
  (Fable, post-reset) — plus the lane is re-runnable on literal Opus seats if
  Matt rules the deviation unacceptable; nothing is adoption-final until the
  FP-adjudication gate.
- GATE: consensus-presence only (precedent: the context-atoms lane ran on
  consensus credits). A node carries the subtype iff BOTH seats annotate it.
  Disagreements are recorded in full for audit; consensus-absence is the
  default. No seat sees the other's output.
- SCOPE: all model-spec corpus nodes (link_nodes.gather()), regardless of
  whether they have asserts — exhibit/form features are span properties.
  Constitution nodes are OUT of scope (arc-2 territory, zero-adaptation).

## Registration and integration
- Deliverable: act_refinements.json — {subtype: {node_id: true}} consensus
  credits, plus the two seats' raw outputs (audit).
- Vector integration: census vector() acts entries gain a refinement-mark
  slot, so identically-bridged nodes with different span forms stop colliding.
- Instrument integration: NONE at mint time. No module performs either
  subtype; no wall keys on it. Subtypes imply parents via bridge rules, so
  existing engagements are untouched by construction. Declarations that
  consume refinements are 9b-design-round work (post-mint, separate gate).

## Registered predictions (falsifiable)
- M1 CHARTER INVARIANCE: engagement is bit-identical before/after the mint on
  modules_contract_v18.json for all three behaviors. Any flip -> wiring bug
  (something consumes the refinement that shouldn't); STOP, do not adjudicate.
- M2 COLLIDER SEPARATION: after the mint, the census CURRENT view separates
  AT LEAST 2 of the 3 collider nodes (each becomes SEPARABLE because its
  twin's vector now differs on the refinement mark). All 3 preferred; if only
  2, the residual is disclosed with its surviving twin set.
- M3 AGREEMENT: per-subtype seat agreement >= 95% of nodes (parity bar in line
  with the definitional lane's 0.9855/0.9889). Below that, the lane is
  invalid; disagreements go to Matt, not to a tiebreak.
- M4 SPARSITY SANITY: exhibit:illustrate consensus count expected O(10-30)
  nodes (worked-example exhibits are a recurring but minority form; the
  miner's in-sample generality note names 3+ matches); form_equivalence
  expected O(5-20). A consensus count of 1-2 or 100+ -> criterion pathology;
  stop and report rather than adopt.

## Inputs frozen at signature
Criteria: verbatim `criterion` strings from split_mining_candidates.json for
the two atoms (dimension "acts"). Corpus: link_nodes.gather() at HEAD.
Instrument: modules_contract_v18.json. Census: satisfiability_census.py as of
commit c0800715 (vector carries refinement slot per this prereg's integration
clause — implemented as part of the mint, tested before regression).
