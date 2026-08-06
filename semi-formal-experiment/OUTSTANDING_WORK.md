# OUTSTANDING WORK — working checklist (rewritten 2026-08-05, late)

Everything open, with its gate. **Goal driving the ordering: reach the S8 checkpoint census
(the re-measurement immediately before S9 behaviour expansion) as fast as possible — target
end of week, ideally sooner.**

Spine (serial, dispatch-ladder composition): `S3b → S4 → S5 → S6 → S6b → S7 → S8 → S9`.
Checkpoint 1 sits after S5. The *cycles* are serial; their **designs and reviews are not**,
which is where the schedule is actually won.

---

## A. BLOCKED ON MATT — nothing else moves these

- [ ] **A1. D2 — the m0108 organisation boundary.** Substance already settled by
      `cycles/patient-pricing-2026-08-04/M0108_SEAT_DEFECT_REVIEW.md`; what remains is
      recording the disposition (carry as `unclear`; the definitional clarification goes to a
      query-side cycle). **Blocks S3b's §9 OPEN conditions.**
- [ ] **A2. D5b — patient-free ACT atoms in the population.** `D5B_ACT_ATOMS.md` recommends
      NO; `D5B_COUNTS.md` measured the ceiling at ~2 (range 1–4), not the ≤17 first assumed.
- [ ] **A3. Implied-effects: four blocking findings** (ENG-B1, ENG-B2, SCI-B1, SCI-B2).
      Decision material → `IMPLIED_EFFECTS_DECISIONS.md`. **Highest-leverage decision on the
      board: S3b cannot OPEN until this layer passes review and accepts m0239.**
- [ ] **A4. Sequencing — S4 before S3b?** S4 needs E2 + one Tier-1. S3b needs a Tier-1, A1,
      A3, a seat brief that does not exist, a provider entry, and real spend. Composition
      burden is symmetric either way. **This is the single biggest schedule lever.**
- [ ] **A5. `containment-v1-pricing`** — retire as un-replayable, or keep with the
      disagreement documented. Its 1.0-era code never entered version control (verified: no
      `PRICING_VERSION = "1.0"` in any commit); the recorded numbers predate 1.1 too.
- [ ] **A6. Spend authorization for the S3b build** — the first real money in the ladder.
      Needs F4's cost estimate first.

**RULED, do not re-litigate:** D1 (annotation-side backfill) · D3 (uniform example rule;
LF-1) · D4 (translation-time generic disambiguation) · **D5 = b-trim/439** (368 and 746
rejected by name, `S3B_REDESIGN.md` §8) · `harm_bearers` → **`affected_parties`** ·
E2 vehicle = thread the parameter (option (a)) · index-builder refactor lands first.

---

## B. Autonomous — running or ready to run without a decision

- [x] **B1.** LF-1 + LF-2 tripwires — DONE, see H7.
- [ ] **B2.** `IMPLIED_EFFECTS_DECISIONS.md` — decision material for A3. *(in flight)*
- [ ] **B3.** S5 Tier-1 adversarial review. *(in flight)*
- [ ] **B4.** S6 Tier-1 adversarial review. *(in flight)*
- [ ] **B5.** Group 0c — census config headers + `--overlay`, required before S8. *(in flight)*
- [ ] **B6.** Clean-context adversarial review of the index-builder refactor (C1).
- [ ] **B7.** S4's E2 resolution against the landed builder, then its Tier-1 re-review.
- [ ] **B8.** `join_facts` bug (H1) — S8 needs it.
- [ ] **B9.** Snapshot-replayability CI (D1/D2), once the builder lands.
- [ ] **B10.** The S3b attribution seat brief (F3) — writable now; does not need A1/A3.

---

## C. Index-builder refactor (on a branch, not merged)

Branch `worktree-agent-a4a214c0140729246`, rebased onto `main`. One config-driven
`build_index` replaces the two drifted F9 ladders; registry-based, so a new version axis is
an entry, not a branch. Suite 2180 pass / 3 skip. Noop verified on all 12 snapshots.

- [ ] **C1.** Clean-context adversarial review — **mandatory before merge** (reconstruction
      path; standing rule).
- [ ] **C2.** Run as a cycle: `shape: code`, predicted flips **0**, gate = all snapshots
      reconstruct bit-identically. Pre-built ⇒ the PRE-BUILT CYCLES disclosure applies.
- [ ] **C3.** Third ladder in `audit_disagreements.py:655-665` left alone (FORBIDDEN module,
      different defaults). Decide: migrate, or document as intentionally separate.
- [ ] **C4.** `rung_for` swallows exceptions from `live_version()`; would hide an unexpected
      import error. Flagged by its author.

---

## D. Snapshot replayability (a CI gap, not a one-off)

After the `_git_bytes_matching` fix: **9 exact / 1 mismatch / 2 unreconstructable**
(was 4/1/7 — five were false negatives from the pathspec bug).

Root cause of the two real ones: **nothing enforced that a snapshot's inputs be committed at
the content it records.** `containment-v0`'s overlay and `patient-pricing-2026-08-04`'s
`behaviours_query.json` were snapshotted against working-tree states that never entered git.
They fail at the *license check*, before byte recovery is attempted, so no tooling fix reaches
them.

- [ ] **D1. Write-time refusal** — `snapshot.write_snapshot` refuses (or loudly discloses)
      when an input's recorded sha is not retrievable from git or archived in `pre_change/`.
      The durable fix: prevents new orphans.
- [ ] **D2. CI check** — `verify_reconstruction.py` over all snapshots on every change,
      failing on NEW breakage only, with known-broken ones in a documented **shrinking**
      allowlist. Never grows to silence a failure.
- [ ] **D3.** Gated on C1/C2 — both touch `verify_reconstruction.py`.

---

## E. S4 — section-prior evidence gate (nearest to OPEN)

- [x] Tier-1 review R2: REVISE, 3 majors + 9 minors (`S4_ADVERSARIAL_REVIEW_R2.md`).
- [x] E1 (the driver does not enforce revert — it is the DECIDE **signer's** obligation), S1
      (the "4 of 30" arithmetic was unsound: 24/30 intersection), and all nine minors applied.
- [ ] **E1.** Resolve E2 against the landed builder. §6 carries a loud `⚠️ PLACEHOLDER`;
      `files_to_change` freezes at OPEN, so it cannot be deferred past it.
- [ ] **E2.** Tier-1 re-review before OPEN — the document changed substantially since R2.
- [ ] **E3.** OPEN the cycle.

---

## F. S3b — beneficiary-aware pricing (largest lever, most gates)

Expected coverage **≈27% of the census**, not 53% (`D5_WORKED_EXAMPLES.md`; BUILD_OVERVIEW
corrected).

- [ ] **F1.** Tier-1 review of **REVISION 9** — R8 reviewed REVISION 8 and returned REVISE;
      REVISION 9 has only a Tier-2, and §9 still reads "awaiting adversarial re-review".
- [ ] **F2.** A1 (D2) + A3 (receiver readiness) — both are §9 OPEN conditions.
- [ ] **F3.** Write the attribution seat brief. It **does not exist**;
      `briefs/backfill_author.md` has zero occurrences of the bearer field. Must carry the
      `affected_parties` rename and a worked pure-benefit example (m0018), or a seat will
      answer `unclear` on a provision clause and fail its own control.
- [ ] **F4.** Provider entry + cost preflight. `BUILD_OVERVIEW.md` names "DeepSeek V4 Flash";
      `providers.json` has `deepseek-ai/DeepSeek-V3.2`. No estimate exists for 439 instances +
      ~80–100 parity rows × 2 models + golden review. `spend.py --would-cost` before the first
      call. Budget $8.50, ~$2.06 logged, plus a known **unlogged-spend** warning.
- [ ] **F5.** backfill → parity validation → pricing cycle.

---

## G. Rest of the spine

- [ ] **G1. S5** overlay reactivation — review in flight. **Checkpoint 1 follows S5.**
- [ ] **G2. S6** vocab additions — review in flight. **Highest fitting risk on the board**:
      the query-side atoms *are* the query.
- [ ] **G3. S6b** re-selection · **G4. S7** admission-order freeze (optional per PORTFOLIO).
- [ ] **G5. S8 checkpoint census** ← **the target.** Needs B5, P1's deferred passage-level
      re-measurement, and H1.
- [ ] **G6. S9** generalization + G-freeze artifact — DESIGN tier, run-once measurement.
- [ ] **G7. F** final battery. Constitution stays sealed until then.

---

## H. Tooling debt

- [x] `_git_bytes_matching` double-prefix — **FIXED** (`68b036d`); unlocked 5 snapshots.
- [ ] **H1. `join_facts` bug** — `evaluate()` with caller-supplied joins and `join_version=2`
      does not populate `join_facts`. **S8 needs this.**
- [ ] **H2.** Five grandfathered length-1 chains (m0021, m0178, m0179, m0502 ×2).
- [ ] **H3.** Backfill hardening F1/F2/R1–R3.
- [ ] **H4. `REVIEW_POLICY.md` amendment:** a Tier-2 pass verifying a claim *about code* must
      read the code. Its first real use credited two fixes it could not have checked — it
      scoped itself to "design-doc verification only, no code reads", and one fix was entirely
      a claim about what `cycle.py` does.
- [ ] **H5.** P2 `segmentation-variants-2026-08-04` — parked; merge at a gate window
      (Option-A restore-then-reapply + pre-built disclosure, as P1 did).
- [x] **H6.** Doc-staleness sweep (requirements.txt, pricing ladder, test count, casebank) —
      done `690fa69`; `casebank` remaining mentions are the legitimate corpus concept.
- [x] **H7. Latent-fix tripwires** — DONE (`test_latent_fix_tripwires.py`, 8 tests + 1 named
      skip, registered in `conftest._OPTIONAL`), closing the registry's own implementation
      debt. **LF-1**: example-kind population pinned as a DIGEST (per its REVISIT note, not
      183 ids inline); m0176/m0300/m0467 pinned as example-kind; adjudication shape-flag
      requiring every example-kind flip's cycle to carry an explicit LF-1 disposition.
      **LF-2**: ambiguity-language scan over `cycles/*/decision.json`, `flip_verdicts*.json`
      and `*_SEAT_DEFECT_REVIEW.md`, failing on any hit outside the hand-maintained
      `LF2_KNOWN_HITS` allowlist (9 entries: 8 are I-01, m0108's representation boundary; 1 a
      named false positive), plus a reader-surface pin on `site/spec-reader-test/`. The
      allowlist is PINNED so growth must be edited in the same diff — it is not a floor and
      does not get lowered. Deliberately not implemented: LF-1's load-bearing SURFACING
      assertion (needs S3b's attribution artifact — present as a named skip) and dossier-side
      tagging (`dossier.py` is under refactor).

---

## I. Parked by design

- **LF-1** example-kind taint rule · **LF-2** interpretation layer
  (`INTERPRETATION_LAYER_DESIGN.md`) — both in `LATENT_FIX_REGISTRY.md`, tripwires now live.
  LF-2's protocol caveat: the *machinery* is parked, but four interpretations (I-01 m0108
  representation, I-02 foreseeable downstream harm, I-03 D3 uniform, I-04.. implied effects)
  exist **today** and are a live backlog, not a latent one.
- [ ] **I1.** Retroactive audit: mine closed cycle records for implicit interpretations. I-02
      was found only by reading one review closely.

---

_Model tiering: strongest tier for orchestration/design/adversarial review; mid tier for
executing a written and reviewed plan; small validated seats for judgment work. Set the model
explicitly on every dispatch. Design work stays off the implementation tier — the S3b
redesign, the G-freeze artifact, and interpretation-layer rulings._
