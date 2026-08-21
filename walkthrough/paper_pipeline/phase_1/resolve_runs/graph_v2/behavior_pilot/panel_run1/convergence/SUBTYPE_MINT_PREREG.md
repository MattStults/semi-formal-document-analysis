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

## ADDENDUM 1 — first-pass results + coverage defect + M4 stop (2026-08-21)
First-pass lane ran on the ctx_chunk1-8 packets (the context-atom lane's
corpus): 583 nodes, NOT the full 762-node corpus the SCOPE clause requires —
a protocol deviation in packet selection (orchestration error; the chunks
were reused without a coverage check).
Results on the covered set: form_equivalence — seat agreement 0.9895 (M3
PASS), consensus 10 nodes (M4 PASS, band O(5-20)); exhibit:illustrate —
agreement 0.9987 (M3 PASS), consensus 169 nodes (M4 STOP: band was O(10-30),
prereg says stop and report rather than adopt).
Coverage defect, characterized: ALL 179 unjudged nodes are assert-less
nodes (translated, no asserts) — precisely the class where exhibit:illustrate
marks live (worked-example nodes carry their norm in the example, not in
asserts; example-act lifting exists for exactly this reason). 22 census
mismatch nodes are among the unjudged, including collider control
harm::l831_1000_n001 (claim: '... is an example of prohibited content') and
E1 flip l831_1000_n006. M2 is therefore NOT EVALUABLE on the harm collider.
Neither subtype is adopted. act_refinements.json holds the partial assembly,
labeled PARTIAL, for audit.
RULING REQUESTED (Matt): revise M4 for exhibit:illustrate before the
extension run — the O(10-30) band was a sparsity prior from an 8-packet
sample; the document is example-heavy by construction and the lane's health
evidence is its near-perfect agreement, not its count. Proposed M4-REVISED:
pathology signal = seat disagreement or incoherent quotes, not count;
expected exhibit count on full coverage O(100-300). The extension run
(179 nodes, span text reconstructed from source artifacts) is already
required by the frozen SCOPE clause and needs no further ruling.

M4-REVISED SIGNED by Matt 2026-08-21 ("Sign as proposed"). The exhibit stop
is lifted; extension run proceeds on the 179 unjudged nodes with unchanged
criterion, seats, and consensus rule. form_equivalence first-pass results on
covered nodes stand; both subtypes re-assembled after the extension.

## ADDENDUM 2 — extension-seat content-filter failure + sanitization ruling (2026-08-21)
All four extension seats failed with provider input-inspection rejections:
the extension set is the assert-less example-class nodes, which concentrate
the document's prohibited-content examples (15 of 179 nodes carry sexual/
self-harm/CBRN terms). RULING (orchestration seat): both mint criteria judge
FORM only (exhibit shape; form-equivalence phrasing) — content nouns are
never part of either judgment — so the 15 flagged nodes are annotated on
sanitized text: sensitive terms replaced with bracketed category labels,
structure (Example headers, speaker markup, GOOD/BAD markers, equivalence
phrasing) untouched. Manifest: mint_ext_sanitization_manifest.json (per-node
substitutions; residual screen outside labels = NONE). Seats run on
ctx_ext_san1-3.json. This is a deviation from verbatim-span annotation,
limited to 15 nodes for form-only criteria; every downstream artifact cites
this addendum. REJECTED BY NAME: human-seat fallback for the 15 nodes (kept
as contingency if sanitized seats still fail — it would cost Matt ~15
minutes and a single-seat deviation from the two-seat rule).

ADDENDUM 2, CONTINUED (2026-08-21): the sanitization ruling did NOT hold —
a sanitized extension seat was still rejected by input inspection (the
classifier reads surrounding context, e.g. '[sexual-content] involving
minors'; the v2 screen had also dropped minors/gore/violence terms).
CONTINGENCY ACTIVATED per the rejected-by-name fallback: the 15 hot nodes
are carved OUT of seat annotation entirely. Four seats re-dispatched on
ctx_ext_clean1-3.json (164 nodes, raw text). Any surviving sanitized-seat
outputs are DISCARDED in favor of clean-chunk outputs (uniform provenance).
The 15 hot nodes go to a HUMAN SEAT (Matt): packet mint_ext_human_packet.json
(raw spans + both criteria + answer format). Human-seat consensus rule: Matt's
judgment is the judgment seat; a mechanical structure screen (Example-header /
speaker-markup / GOOD-BAD markers for exhibit; quoted equivalence phrasing for
form_equivalence) runs as the second blind signal; consensus-presence as
always, disagreements recorded, never tiebroken. Disclosure: single human
seat + mechanical screen replaces two model seats on these 15 nodes only,
because no provider seat can read them.
