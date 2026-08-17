# PREREG — ARM F: the cheap critic's REPLY CONTRACT, two cells

⚠️ **Written and saved BEFORE any live call.** Nothing below may be edited after
the first response arrives; corrections go in `RESULT.md`, marked as such.
Arm E's design is this arm's design (`ds_critic_arm/PREREG.md` §§2–4, §8), and
every section here states only what DIFFERS from it.

---

## 1. THE FINDING UNDER TEST

Arm E measured a split no prior arm could see. A separate DeepSeek instance
critiquing the module as a peer:

| | arm D (self-review) | **arm E (peer critic)** | arm A (Opus critic) |
|---|---:|---:|---:|
| frozen items identified (paired 6 clauses) | 15% | **37%** | authored |
| repair **conditional on identification** | 92% | **≈62%** | 100+/100+ |
| `asserts`, turn-1 → post (13 clauses) | — | **24 → 18** | **24 → 28** |
| modules acquiring a conclusion-changing defect | — | **5 of 13** | — |

⭐ **Diagnosis roughly doubled and prescription collapsed. The loop DELETED
normative content where the frontier loop ADDED it.**

⭐⭐ **The measured mechanism.** **11 of 39 DeepSeek FIX lines (28%) offer the
drafter a branch** — *"either add a body condition … or delete C3"*, *"delete it
or mark it assumed"*. **Across all 17 Opus `feedback_1.md` files there is
exactly 1 such line.** Every arm E harm case is a cheap branch taken.

Arm E's own inferred generalisation: the Opus critic's edit names **the field,
the new value, the branch NOT to take, and the constraint the fix must
preserve.** A peer critic recovers a real share of the noticing and almost none
of that.

## 2. THE TWO CELLS

Both cells are arm E with **one thing changed: what the critic is allowed to
write.** The eleven entries, the three anti-rules, the 17 clauses, arm A's
stored turn-1 drafts, the unforced critic call, the mechanical FIX extraction
and the imperative edit-list form are all held.

### Cell F1 — BAN. *The mechanism test.*

One bullet is added to the critic's reply rules:

> ⛔ **COMMIT TO ONE EDIT. No alternatives.** A FIX line must name exactly one
> change. Never write "either … or", "or delete", "or remove", "or mark
> assumed", "or fix", or any other choice. If two remedies are both available,
> decide which one is right for THIS span and write only that one. A line that
> hands the author a choice is a failed line, and the author will take the
> cheapest branch.

F1 isolates arm E's measured mechanism and tests its prediction directly.

### Cell F2 — BAN + PRESERVE. *The engineering arm.*

F1's ban, plus the reply form gains a field and one more rule:

> `E2: FIX — <one sentence: the exact field, and the exact change to make> PRESERVE: <what this edit must not destroy>`
>
> * **Every FIX line ends with `PRESERVE: <clause>`.** Name the thing your edit
>   must NOT destroy — the obligation, the distinction, the content, or the
>   qualifier that must still be present in the module after the edit is made.
>   Be concrete: name the predicate, the claim, or the words. If an edit deletes
>   something, say what has to survive the deletion.

The PRESERVE clause rides into the drafter's edit list on the same line, because
the whole FIX sentence is extracted mechanically. **That is the intervention:
the drafter now receives the constraint as well as the change.**

⚠️ **Cost of that, disclosed:** F2's edit lines are longer than arm E's and F1's,
so F2's repair side is *not* regime-identical to the Opus loop's in the way arm
E's was. F1's is.

⛔ **REPORTED SEPARATELY, NEVER BLENDED.** F1 is the mechanism test. F2 is the
engineering arm. There is no "arm F number".

### Byte-identity gate on the list

`verify_prompts()` refuses to send unless both cells' review lists are
**byte-identical to arm E's** from `**E1. Does a gloss…` to the end of the
anti-rules. Reference tail sha256 `39fcb552…0ac4b8d`.

⛔ **Entry E6 STAYS, and this is deliberate.** E6 is a MEASURED defect generator:
arm D and arm E, two different critics, produced the identical weakening on
`l171_426_n022` by obeying it. Pulling it is tempting and would add a second
variable and destroy the comparison. **E6 firings are COUNTED per cell and
reported instead.** A list-repair arm is a separate experiment.

## 3. ⛔ THE TRAP, INSTRUMENTED — NOT ASSUMED AWAY

**Banning the disjunction may simply move the coin flip inside the critic.** A
critic forced to commit could pick the deleting branch just as often. Branch
count would then read as a clean success while the modules got worse.

⛔ **Branch count is a MANIPULATION CHECK. It tells us the instruction took
effect and nothing more. It is never quoted as a result.**

### THE HEADLINE, in the order it will be reported

⭐ **TIER 1 — ADJUDICATION-FREE.** Computed by `arms_review/floor.py`,
`arms_review/measures.py` and `licence_control/measure.py`, imported not
reimplemented. No judgment of mine enters any of these.

1. ⭐ **`asserts` delta.** Arm E 24 → 18; Opus 24 → 28. **The sign is the
   result.**
2. **`floor_clean`, `errors`, `polarity`, `bodiless_asserts`, self-cited
   borrowed glosses, closure mix** — the published cross-arm columns.
3. **Class B (licence inheritance) and Class C (dead `requires`)** from
   `independent_review/scan.py`, four lines of Python, computable on any module.
   ⚠️ **ARTIFACT MISMATCH, stated wherever used:** the independent review read
   the CONVERGED modules, not the turn-1 drafts arm F starts from. Its *counts*
   are not arm F's baseline; only its *checks* are borrowed.

**TIER 2 — ADJUDICATED, and labelled as such on every line.**

4. **Conclusion-changing defects acquired** (arm E: 5 of 13).
5. **Identified and repaired, as TWO separate numbers, never multiplied** — and
   **repair conditional on identification** (arm D 92%, arm E ≈62%).

## 4. ⭐ THE ANSWER KEY IS FROZEN, AND THE MATCHING IS BLIND

⛔ **This is the amendment that most distinguishes arm F from arm E.** Arm E's
headline was the adjudicator's own match of a critic sentence to a frozen item,
with the criteria formed while reading the replies. Arm E conceded its 37% cell
"would not survive a few cells of re-adjudication". Arm F removes that.

### 4.1 The key, committed before the first call

`key/build_key.py` → `key/frozen_key.json`, sha256 `16965c45…af45aa6`,
**164 items over all 17 clauses**. Every item is one required change in
`ds_opus_loop/out/<id>.feedback_1.md` — the Opus critic's adjudication of these
exact drafts, authored before arms D, E and F existed. **I enumerate; I do not
author.**

Each item carries, written in advance: `element` (the field + predicate a critic
must NAME), `identify_if` (the criterion in prose), `anchors` (token groups for
a mechanical prefilter), `repair_if` (what the post module must show).

**Inclusion rule, frozen:** one item per distinct required change; excluded are
"leave/keep X as it is" lines, "do not use word W" prohibitions, `[note/keep]`
blocks, and any block requiring no edit; included are `[note/unused]` and
`[note/claims]` blocks naming a defect.

**Matching rules, frozen:** an item matches at most once per reply; one critic
line may satisfy more than one item if it names each change; a line naming the
right field but the WRONG change is not a match and is recorded as a false
charge.

⚠️ **My denominators are arm E's on 12 of the 13 clauses arm E completed.** They
differ on `l3147_3238_n003` (4 here, 3 in arm E — I include the `[note/unused]`
`response/1` finding). This is disclosed and the affected numbers are shown both
ways.

### 4.2 The matching is blind, and arm E is RE-SCORED

⛔ **REQUIRED, not optional.** All critic replies from **F1, F2 and arm E** go
into one pool, cell labels stripped, filenames replaced by opaque seeded ids
(`blind_pool.py`). I score from the pool. Only after every verdict is written is
the mapping unsealed.

⭐ **Arm E's blind re-score is reported beside its original 37%. If they differ
materially, that difference is a finding about the MEASUREMENT and is reported
as prominently as the F cells.**

⚠️ **Blinding limits, stated honestly and not softened.** I have read arm E's
`RESULT.md` in full and four of its `edits.md` files in this session. **Arm E's
replies on `l171_426_n022`, `l3147_3238_n003`, `l3239_3382_n002` and
`l4252_4482_n005` are recognisable to me and the blind is broken on those four.**
They are flagged in the verdict record. The blind is intact on the rest, and on
every F reply.

## 5. WHAT DIFFERS MECHANICALLY FROM ARM E

| | arm E | **arm F (both cells)** |
|---|---|---|
| critic `max_tokens` | 7,168 | **8,192, UNIFORM across both cells** |
| critic `format_forcing` | none | none (unchanged) |
| repair call | production `response_format`, 4,096 | unchanged |
| retries | none | none |
| cap | $0.12 (one cell) | **$0.25 across BOTH cells** |

⚠️ **THE 8,192 DEPARTURE, disclosed.** Arm E lost 4 of 17 clauses to truncation
at 7,168, and the loss was **correlated with the outcome** — the four longest
reasoners. 8,192 is 1.14× that. **This makes arm F's truncation rate not
like-for-like with arm E's**, and if arm F completes more clauses than arm E did,
the extra clauses are the hard ones and the two arms' rates are computed over
different samples. Every cross-arm rate is therefore also reported restricted to
the clauses **all three** cells completed.

⛔ **No clause is retried at a different cap.** A retry set selected by the
behaviour under test makes the sample heterogeneous in a way correlated with the
outcome.

## 6. SPEND

Hard cap **$0.25 across both cells**, owner-set, enforced in
`run_armf.py:CAP_USD`, against the project ceiling `spend.py:BUDGET`. The gate
counts **both cells** since one recorded ledger start line, so F2 is gated
against F1's spend. Each phase is priced at worst case IN FULL before any of its
calls is sent. ⛔ Over the cap, nothing is sent.

Arm E cost **$0.08335** for one cell at 7,168. Two cells at 8,192, with F2's
longer replies, should land near **$0.19**. If the worst-case gate refuses F2
after F1 has run, **F2 is not run and that is reported as a truncated
experiment** — the cap is not raised.

⚠️ **THE MEASURED LEDGER HOLE.** `translate.Client._log_usage` runs BEFORE
`_check_envelope`, so **a truncated completion is billed and then raises, leaving
no turn record.** It hid $0.01612 of arm E's $0.08335 (4 calls) and 36% of arm
D's. `run_armf.py` writes a zero-cost record for each raise and the gate takes
`max(records, ledger)`. `reconcile.py` re-attributes the whole window by prompt
shape before any spend figure is quoted: **on-disk vs of-record vs the
difference, every row attributed.**

⛔ **`loop.py` IS NOT TOUCHED.** Fixing the hole would change the instrument
mid-series. If that changes, `RESULT.md` says so explicitly.

## 7. THE BRANCHES, fixed now

Scored **per cell**, over the clauses that cell completed, and again over the
all-cells-completed intersection.

### ⛔ WHAT WOULD MAKE ME SAY THE DISJUNCTION BAN DOES **NOT** WORK

Any ONE of these, in **F1**, is a NULL on the ban and will be reported as one:

* **N1 (⭐ the decisive one).** `asserts` **stays flat or falls** relative to
  turn 1 — i.e. the ban removed the branches and the deletion continued. Arm E:
  24 → 18. **A cell that bans the branch and still deletes normative content has
  shown the coin flip moved inside the critic.**
* **N2.** **≥3 of the completed modules acquire a conclusion-changing defect**
  (arm E: 5 of 13, on 13). This is the H1 threshold, unchanged.
* **N3.** **Repair conditional on identification stays ≤ 70%** — the collapse
  (arm E ≈62%) survives the ban.

⭐ **N1 firing while the branch count goes to ~0 is the single most informative
outcome available in this arm, and it is the one I have most reason to fear.**
It would mean the branch was a SYMPTOM and the cheap critic's remedy selection
is the disease — which prices frontier-tier prescription as load-bearing and
makes a reply-format fix a dead end.

### TRANSFER — the ban works. All THREE required, in F1:

* **T1.** `asserts` **rises** relative to turn 1 (turn-1 baseline over the same
  clauses), i.e. the sign matches the Opus critic's, not arm E's.
* **T2.** **≤2 modules acquire a conclusion-changing defect.**
* **T3.** **Repair conditional on identification ≥ 80%** — back to the arm
  D / B3 / B5 band.

### PARTIAL
Anything between: reported as a partial effect with the cell counts, and
explicitly **not** claimed as transfer.

### F2 IS SCORED ON THE SAME THREE, SEPARATELY
plus one of its own:
* **T4 (F2 only).** F2 beats F1 on `asserts` delta **and** on
  conclusion-changing defects. ⚠️ At n=13–17 with single-digit cells, an F2-over-F1
  difference of one or two modules is **not separated from noise** and will be
  said to be.

### MANIPULATION CHECK — reported as such, never as a result
* **M1.** Branch-bearing FIX lines fall from arm E's **28% (11/39)** to **≤5%**
  in both cells. If M1 fails, the instruction did not take and the cells are
  uninterpretable as a test of the ban.
* **M2 (F2 only).** **≥90% of F2 FIX lines carry a `PRESERVE:` clause.** If not,
  F2 is a partial dose and is reported as one.

### HARM, scored separately and reported even if everything improves
* **H1.** ≥3 modules acquire a conclusion-changing defect. (= N2.)
* **H2.** ≥1 defect that is the direct product of correctly obeying an entry
  (the E6 / R57 shape).
* **H3.** ≥3 modules whose turn-1 floor was clean fail after. ⚠️ This sits ON
  the measured 3-of-17 noise band (B7) and a bare firing is
  **indistinguishable from noise**.
* **H4.** ≥1 "repair" of an anti-rule-protected item.
* **H5.** ≥25% of FIX lines are false charges.
* ⭐ **H6 (new, F2-specific).** ≥3 FIX lines whose `PRESERVE:` clause is
  **violated by the repair the same line asked for.** A constraint the drafter
  is told and then breaks is worse than no constraint, because it looks like
  supervision.

### ⛔ THE NAMED CASE, worth more than a rate
**`l3147_3238_n003`.** Arm E's critic FOUND the lost-disjunction defect that
self-review never reached; the repair then **deleted two of the three
obligations** while the read-back still recited all three, and the floor came
back `translated`, `repair_needed=False`, 0 breaches — **nothing mechanical saw
it.** Per cell, reported explicitly: did the critic find it, and **do all three
named responses (use a tool, hedge, explain) survive in the post module?**
Key item `l3147_3238_n003#01`'s `repair_if` says so in advance: *deleting any of
the three is NOT a repair — it is the harm this arm is testing for.*

## 8. PREDICTIONS, on the record

* **P-1.** ⭐ **M1 passes and N1 also fires in F1** — branch lines go to near
  zero and `asserts` still does not rise. Confidence: **moderate-to-high, and
  this is my headline prediction.** Grounds: arm E's deletions were not only on
  branch lines (`l1_170_n056`'s unbound-negation repair was a single committed
  instruction), and a critic told to commit has no more information about which
  branch is right than one told to offer both.
* **P-2.** **F2 beats F1 on `asserts` delta**, but by ≤3 asserts — inside the
  noise. Confidence: low-moderate. Grounds: PRESERVE supplies the one thing arm
  E named as missing, but one sentence carrying both a remedy and a constraint
  is the same compression failure arm E measured.
* **P-3.** **Identification does NOT fall** in either cell relative to arm E's
  blind re-score. The ban constrains the remedy, not the noticing. Confidence:
  moderate.
* **P-4.** ⭐ **`l3147_3238_n003` loses obligations again in at least one cell.**
  Confidence: moderate-high. If F2 preserves all three, that is the single
  strongest evidence in the arm for the PRESERVE field.
* **P-5.** **E6 fires and produces the same weakening on `l171_426_n022` in at
  least one cell**, now without a branch to hide behind. Confidence: moderate.
  A third independent reproduction would make E6's defect-generation a
  three-instrument measurement.
* **P-6.** **My blind re-score of arm E lands within 5 points of its published
  37% paired figure.** Confidence: **low.** Arm E's own limits section says
  several cells could move. If I am wrong here it is a finding about arm E's
  measurement and it will lead the report.
* **P-7.** **Truncation ≤3 of 17 per cell** at 8,192 (arm E: 4 of 17 at 7,168).
  Confidence: moderate.

## 9. PROTOCOL COMMITMENTS

1. ⛔ **No tuning after seeing results.** `messages/`, `promptsF/`,
   `config_armf.json` and `key/` are frozen at the first live call. A third cell
   would have to be pre-registered as such and reported.
2. **The floor runs first** on every module — `schema.validate_all` then
   `checks.run_checks` — and adjudication is on top of it, never instead.
3. **Span-first adjudication.**
4. ⛔ **READ-ONLY outside `_debug_gen11/ds_critic_format_arm/`.** **No git, no
   commit, no branch change, and never `--no-verify`.** If `git status` shows
   modified files I did not touch, that is other work in this session and is
   reported, not acted on.
5. **n = 13–17 per cell, every cell single-digit.** No rate here is
   statistically separated from noise, and B7 (a byte-identical re-draw moves
   error count on 7 of 17 and `floor_clean` on 3 of 17) is quoted beside every
   mechanical comparison.
6. **A null is a real result and is reported undiluted.** Neither direction is
   softened.
7. **Limits are reported without softening**, including: one critic→repair cycle
   only, so **turns-to-convergence cannot be compared against the Opus critic's
   6 of 17**; the review list is in-sample; and the 8,192 departure.

## 10. CONTAMINATION, DISCLOSED

I have read `ds_critic_arm/PREREG.md` and `RESULT.md` in full, arm E's
`run_arme.py`, `measure.py` and `reconcile.py`, `arms_review/floor.py` and
`measures.py`, `licence_control/measure.py`, `independent_review/02_classes.md`,
all 17 `feedback_1.md` files, and four of arm E's `edits.md` files. **I designed
arm F knowing arm E's per-clause outcomes and its named cases. I cannot
adjudicate blind on those four clauses' arm-E replies and I do not claim to.**

Structural mitigations, not promises:

* The answer key is **frozen and hashed before the first call**, and derives
  from files authored by the Opus critic before any of these arms existed.
* The matching criteria are **written before any reply exists**.
* Cell labels are **stripped before scoring**; the mapping is sealed until every
  verdict is written.
* The Tier-1 measures are computed by **imported code published for prior arms**
  and involve no judgment of mine at all — which is why they lead the report.
* Every contested classification quotes the span text in `RESULT.md`.

---

**Signed before the first call.** — adjudicator, 2026-08-16
