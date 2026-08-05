# OUTSTANDING WORK — working checklist (refreshed 2026-08-05)

Living checklist of everything open. Sequencing: **finish S3b REVISION 6 + re-review →
implied-effects REVISION 2 (against the settled S3b rule) → builds → spine.** Each item
names its gate/dependency.

**Rulings now settled** (do not re-litigate without new evidence): **D1** = annotation-side
backfill with a mechanical cheap-model attribution seat gated on parity validation;
**R4-B1** = class rule excluding implied-layer-demoted clauses from S3b's regression bound;
**D4** = generic nouns disambiguated at translation/attribution time (not a pricing-time
flag); **D2/m0108** = resolved by the seat-defect review (user's-own-org, not third-party).

> Note (2026-08-05): a reviewer audited this file against the tree; its corrections are
> folded in below (F5/F6 checked off, F4 reduced to casebank/, D1 baseline no longer named
> statically, mixed_variants item added, uncommitted working-set noted). Subagent quota was
> exhausted mid-session; the in-flight items are being completed in the coordinator session.

---

## A. Design revisions (in the review loop) — DO FIRST

- [ ] **A1. S3b REVISION 6** (`S3B_REDESIGN.md`). REVISION 5 applied the R4-B1 class rule,
      the D1 ruling, and the four R3 majors. REVISION 6 folds the **D4 ruling**
      (translation-time generic-noun disambiguation: comprehensive "people" →
      harm_bearers = full principal set; specific "individuals" → specific party; branch 2
      re-grounded as the comprehensive-generic case; m0018/m0248 golden cases). Then
      **clean-context adversarial re-review** of REVISION 6.
- [ ] **A2. Implied-effects REVISION 2** (`IMPLIED_EFFECTS_DESIGN.md`). Per
      `IMPLIED_EFFECTS_ADVERSARIAL_REVIEW.md` (REVISE). **Sequence AFTER S3b REVISION 6
      re-review is non-blocking** (ENG-B1 must spec against the settled S3b §5.3).
  - [ ] Fix **ENG-B1**: one named ruling on where implied patients enter (per-atom factor /
        taint quantifier / both), stated against BOTH `patient.py` and S3b §5.3; work the
        taint-cap interaction; pre-register the score-movement envelope; fix the
        "credited"→"discount-removed" prose.
  - [ ] Fix **ENG-B2**: pin key form (dechained stem via `grammar.stem_of`); translation-sha
        binding; hard-fail (never skip) unresolvable keys; `atom_refactor` migration story;
        `clause_quote` field.
  - [ ] Fix **SCI-B1**: fence the PROPOSAL/queue, not just approval; count-first enumeration
        panel-blind and the proposal source; `proposal_source` class per entry; extend S3b's
        residual-fence list; distinguish blind-text vs flip-surfaced proposals (m0239 is
        flip-derived — handle honestly).
  - [ ] Fix **SCI-B2**: pre-register must-stay-suppressed controls (m0276, m0290 under every
        patient-declaring behaviour) with layer ON; restoration signature for m0239
        (explain cites `imp-<id>`, factor 1.0, `why: consistent`); REVERT rule; no
        signature-batch without stratified NEGATIVE exemplars + measured FP count.
  - [ ] Carry the sealed-TEST major (**SCI-M4**) from the review as well.
  - [ ] Re-dispatch clean-context adversarial review.

## B. S3b build path (after A1 re-review non-blocking)

- [x] **B1.** ~~Rule D1~~ — **RULED (a)**: annotation-side backfill; mechanical task for a
      capable-but-cheap seat (candidate DeepSeek V4 Flash), gated on pre-registered parity
      validation; error-recovery loop for malformed entries. Spec:
      `S3B_ATTRIBUTION_TASK_DESIGN.md`.
- [x] **B2.** ~~Count-first enumeration~~ — done: `ATTRIBUTION_POPULATION_ENUMERATION.md`
      (368 floor / ~439 recommended), `S3B_ATTRIBUTION_TASK_DESIGN.md` §3 (reach-R scan
      425/439; blind floor 110).
- [ ] **B3.** Designer rulings: **D3** RULED **UNIFORM** (coordinator 2026-08-05) — no
      distinct example-kind rule; enumeration found 0 instances of the problem
      (`D3_EXAMPLE_CLAUSE_ENUMERATION.md`, 183/183 handled); the distinct-rule idea is
      registered as latent fix **LF-1** (`LATENT_FIX_REGISTRY.md`), not implemented;
      golden-review m0176/m0300/m0467 as seat-quality targets. **D2** resolved (see G1).
      **D4** RULED (translation-time disambiguation — folded in REVISION 6).
- [ ] **B4.** Run the S3b attribution backfill cycle + the S3b pricing cycle with the
      restoration signature and m0276/m0290 controls. DESIGN TIER (frontier).

## C. Implied-effects build path (after A2 re-review + S3b settled)

- [ ] **C1.** Count-first enumeration: how many implied effects; do they cluster by signature?
- [ ] **C2.** Decide manual vs signature-batch per the count (signature-batch only with
      negative exemplars, per SCI-B2).
- [ ] **C3.** Build: `annotations_implied_vN.json`, `implied_version` seam, composition per
      ENG-B1, explain-trail provenance, explicit-only counterfactual toggle, controls.
- [ ] **C4.** First entry m0239: propose → review → approve, with the control set asserted.

## D. The spine (fix ladder)

- [ ] **D1. S4 — section-prior evidence gate.** Baseline: read the latest closed-KEEP
      snapshot from `cycles/CYCLE_LOG.jsonl` (never named statically here — HANDOFF ruling;
      currently join-integrity-v2). Needs its own F9 version key
      (`section_gate_version`); A1 flip enumeration intact (30 = 13/13/4) — keep it.
- [ ] **D2. S5 — overlay reactivation** (dormant containment-v1.1 edges; owns the seam).
- [ ] **D3. S6 — vocab additions (per family) + S6b re-selection.**
- [ ] **D4. S7 — admission-order freeze + widening cycles.**
- [ ] **D5. S8 — checkpoint census.** Carries P1's deferred passage-level re-measurement.
      GATED on the mixed_variants lever (E2): the census must explicitly pin the join
      variant it uses. Also fold the P1 reviewer's note: `evaluate()` with caller-supplied
      joins + `join_version=2` does not populate `join_facts`.
- [ ] **D6. S9 — generalization phase + the G-freeze artifact.** DESIGN work (frontier tier;
      run-once measurement it defines).
- [ ] **D7. F — final battery** (constitution + anchors).

## E. Parked / uncommitted / latent

- [ ] **E1. P2 `segmentation-variants-2026-08-04`** — parked, uncommitted. Merge at a gate
      window the same way P1 was (Option-A restore-then-reapply + disclosure if pre-built).
- [x] **E2. mixed_variants lever-bleed — FIXED (uncommitted).** `match_passage_v2` default
      flipped `mixed_variants=True → False` (measured/pinned state; the unmeasured variant
      set is now opt-in). New test `test_match_passage_v2_default_is_mixed_variants_false`
      pins the default (behavioral + signature); the one test relying on the old default
      now passes `mixed_variants=True` explicitly; 28 tests green. REMAINING: the D5/S8
      census must still explicitly pin the join variant it uses (see D5).
- [ ] **E3. Uncommitted working set.** The checklist's own docs + design revisions are
      uncommitted (OUTSTANDING_WORK.md, the S3b/implied-effects reviews + designs, modified
      S3B_REDESIGN.md, LATENT_FIX_REGISTRY.md, D3 enumeration, attribution spec, and the
      dossier.py/inventory.py fixes). Commit at a coordinator CLOSE. (`.qwen/` gitignore
      line ADDED 2026-08-05.)

## F. Tooling debt & doc corrections

- [x] **F1.** ~~`_git_bytes_matching` double-prefix~~ — FIXED (dossier.py + regression test;
      targeted tests green).
- [ ] **F2.** Backfill hardening F1/F2/R1–R3
      (`patient-backfill-2026-08-04/backfill/REVIEW_HARDENING_NOTES.md`).
- [ ] **F3.** Five grandfathered length-1 chains (m0021, m0178, m0179, m0502 ×2) — repair is
      an open annotation-cycle question.
- [x] **F4.** ~~Stale-doc residue~~ — RESOLVED: the `casebank/` directory-misconception was
      already corrected in `ITERATION_LOOP.md` §"The case bank" ("the case bank is a
      corpus, not a directory — there is no `casebank/` on disk", 2026-08-04). The
      remaining "casebank" mentions (DRIFT_STANDING_DESIGN, MODULE_MAP, PORTFOLIO_REVIEW,
      briefs/drift_standing) use it as the legitimate drift_standing dossier-corpus
      CONCEPT, not a literal path — no cleanup needed. requirements.txt, the pricing
      ladder, and the test count (2,156 passing) were corrected in `690fa69`.
- [x] **F5.** ~~Anti-rules section~~ — DONE (`MODULE_MAP.md §11`, commit `690fa69`).
- [x] **F6.** ~~Cycle-ceremony mechanics~~ — DONE (`CYCLE_DESIGN.md` amendment channel /
      re-closure / PRE-BUILT CYCLES, commit `690fa69`).

## G. Resolved / deferred

- [x] **G1.** ~~m0108 seat-defect review~~ — RESOLVED
      (`cycles/patient-pricing-2026-08-04/M0108_SEAT_DEFECT_REVIEW.md`): m0108's harm is the
      user's own organisation, NOT "those outside the conversation"; genuine definition
      ambiguity flagged. FOLLOW-UP (future cycle): clarify the definition's boundary as
      representation — "parties whose interests are not represented in the conversation by
      the user or developer."

---
_Model tiering (Matt's rule): **Fable/K3/Qwen** for orchestration/design/adversarial review;
**Opus** for executing a written+reviewed plan; **Haiku** for validated seats. S3b redesign
and the G-freeze artifact are DESIGN work — keep them off the implementation tier._
