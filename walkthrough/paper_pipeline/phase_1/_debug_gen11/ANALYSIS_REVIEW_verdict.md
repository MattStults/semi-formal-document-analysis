# ANALYSIS_REVIEW — verdict summary (full text in the session record)

Adversarial review of `_debug_gen11/`, 2026-08-15. Offline, zero spend.

**Headline: the arithmetic is excellent and the central mechanism claim is
wrong.** Everything computable from bytes reproduced (several exactly). The
two conclusions about to drive a prompt/spec change do NOT survive contact
with the specification or with the run's own successes.

## DECISION-CHANGING (do not act on the analysis as written)

* **DC-1 `ontology` IS a legal declaration bucket** (HIGH). schema.py:865-867
  declares any ontology head by NAME ALONE, body or not; `OntologyFact.body`
  is Optional and a body-less ground atom is legal; prompt/10_output_format.md
  says so in bold ("You DO invent names in the **ontology** block"); and the
  model already does it — 33 of 173 ontology entries across 127 translated
  modules are body-less ground atoms on exactly the spans M1 says have no
  home, ALL first-pass. The failing pair members recover via existing routes
  under a byte-identical prompt. **M1 collapses.** The planned adapter-prompt
  widening of `inputs` is aimed at a gap that is not there — and would be the
  same false-declaration failure the analysis condemns in Fix F. The real
  residual is DISCOVERABILITY (the model reaches for `concepts` and only
  sometimes finds the ontology route), whose remedy is a worked example, not
  a schema change.
* **DC-2 the "controlled pair" is not controlled** (HIGH): both the bucket
  choice and the outcome are free model choices on the same call, over four
  clauses with different text and different graph blocks. Reduced to content
  it says "a declared name passes, an undeclared one fails" — the checker's
  definition. Do not carry it into EXPERIMENTS.md as proof.
* **DC-3 "losses compound" is not in the data** (HIGH): n047 and n087 died on
  their OWN invented predicates, not on a missing upstream export.
* **DC-5 NEW MECHANISM the analysis missed** (HIGH): the declaration check is
  **arity-blind** (schema.py D4b matches by name only), so `inputs:
  ['conflict/2']` legalises `conflict(P1,P2,C)` and the mismatch only
  surfaces at link stage reading like a missing upstream module. Exactly four
  instances corpus-wide, **all four on unrepaired clauses** — 16% of the 19
  losses, more than M3+M4+M6+M7 combined. Remedy is a ONE-LINE checker change
  (compare arity: "declared at /2 but used at /3"). No prompt change, no
  graph change, no contract bump.
* **DC-6 Fix F's `origin` enum DOES have a correct member** (HIGH): the
  proposed Literal is exactly schema.py's declaration set, so it is total by
  construction. F's disposition (don't build it this cycle) stands on the
  ORIGINAL objection; the "no correct member" justification is withdrawn.
* **DC-7 span-type routing has ~no discriminative power here**
  (MEDIUM-HIGH): ~32 of the 36 first-pass SUCCESSES are also non-normative.
  Base rate ~88/100; P(fail | non-normative) ~32% vs P(fail | normative)
  ~25%. A router diverting non-normative spans would divert nearly
  everything, including the cheapest successes. The corpus `kind` field reads
  `conditional` for 94 of 100. **Graph-stage span-type classification is
  unsupported in this region.**
* **DC-8 the defect-trading "unit correction" is numerology** (HIGH): 57%
  reproduces EXACTLY as a per-round rate on the census's own population; the
  census was right. The real finding is a POPULATION effect — trading is
  ~2.7x weaker in this corpus region.

## SAFE TO ACT ON AS WRITTEN

* `class_repair-fixed-point.md` **in full** — every number reproduced exactly
  (52/130 frozen rounds, 50/76 on unrepaired chains, same 4 frozen chains);
  correct #1 by recoverable cost.
* The fresh-draw counterfactual's DIRECTION, with corrected numbers: all 19
  were re-attempted (not 18), **13 of 18** non-abstaining recovered, and the
  money comparison is **08-14 $0.1780 / 95 calls / 0 modules** vs **08-15
  $0.0780 / 45 calls / 14 modules**. Like-for-like confirmed (identical
  system_sha, schema_sha, provenance_hash, per-clause user_sha).
* M2's mechanism and its graph-stage verdict; M2's harmlessness (1/24).
* The census taxonomy is not closed (25 of 284 findings land in OTHER).
* The ranking is corpus-region-dependent: five census classes fire ZERO
  times here, so Fixes A, B, E have no exposure in this region.
* Kill-rate CIs: M1 40% [25,58], M5 75% [30,95], M3 40% [12,77], M2 4%
  [1,20]. M1≠M2 and M5≠M2 survive (Fisher p=0.005); "M5 second worst" and
  "M3 lethal" do NOT — report those as direction only.
