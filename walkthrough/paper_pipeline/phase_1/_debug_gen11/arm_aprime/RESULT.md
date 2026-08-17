# ARM A′ — RESULT: the noise floor this series never had

**One replicate, n = 17, MEASURED spend $0.029952** (ledger of record:
`semi-formal-experiment/usage.jsonl` lines 5048–5064, 17 rows, 0 unrecorded,
0 truncated). Cap $0.05, not approached. Pre-registration and both amendments:
`PREREG.md`. Nothing here was adjudicated span-first; every number comes from
`../arms_review/floor.py` and `measures.py`, reused unmodified via `measure.py`.

**Gates that held before the send:** system block 39,959c sha256
`3a66c5f5…4c34c` == arm A's; all 17 user blocks byte-identical to the blocks
arm A built from its own config; worst case priced and under cap.

**Validity note.** `checks.py` was modified by a concurrent session during this
work. Both sides of every comparison below were re-measured under the *same*
current `checks.py` in one process, and the re-derived arm A turn-1 aggregates
(floor_clean 10, self-cited 25/26 across 15 clauses, closure cepa 25 / cnpa 4)
reproduce the frozen `../arms_review/measures.json` exactly — so the drift does
not touch these measures.

---

## THE FLOOR (MEASURED)

Clauses of 17 that changed under the **empty manipulation**:

| measure | F | 95% CI (Wilson) |
|---|---|---|
| polarity_mismatches count | **0 / 17** | 0–18% |
| arity_mismatches count | **0 / 17** | 0–18% |
| self-cited borrowed-gloss count | **1 / 17** | 1–27% |
| floor outcome | 3 / 17 | 6–41% |
| floor_clean (outcome + breaches + errors) | 3 / 17 | 6–41% |
| asserts count | 4 / 17 | 10–47% |
| **MECHANICAL FLOOR (outcome + error count)** | **7 / 17 (41%)** | 22–64% |
| error-severity count | 7 / 17 | 22–64% |
| ontology count | 7 / 17 | 22–64% |
| closure verdict list | **8 / 17 (47%)** | 26–69% |
| concepts count | 8 / 17 | 26–69% |
| structural signature identity | **15 / 17** | 66–97% |
| exact module identity | **17 / 17** | 82–100% |

**The floor is not one number.** It is near zero on some measures and near
chance on others, and the series' claims are distributed across both.

---

## EVERY HEADLINE EFFECT, AGAINST ITS OWN FLOOR

Turn-1 vs turn-1 throughout (`vs_arms.py`). Arm A′ is a turn-1 draw, so arm A's
turn-1 draft is the only like-for-like comparator.

| arm | n | mech-floor diff from arm A | vs floor |
|---|---|---|---|
| **arm A′ (NULL)** | 17 | **7 (41.2%)** | — |
| list_in_prompt_insample (B) | 17 | 9 (52.9%) | Fisher **p = 0.73** |
| examples_arm (C) | 17 | 9 (52.9%) | Fisher **p = 0.73** |
| retrieval_arm (E) | 17 | 9 (52.9%) | Fisher **p = 0.73** |
| forced_verdict_arm (F) | 17 | 9 (52.9%) | Fisher **p = 0.73** |
| decompose_arm (G) | 13 | 11 (84.6%) | Fisher **p = 0.026** — exceeds |
| selfreview_arm | 9 | 3 (33.3%) | below the floor |
| bucketed_arm | 9 | 1 (11.1%) | below the floor |

### 1. "6 of 17 fixed", "9 of 17 reproduced their own frozen defect" — DEAD

Pre-registered kill condition: F(mechanical floor) ≥ 6/17. **F = 7/17.**

Four separate arms move the mechanical floor at 9 of 17 clauses. Doing
*nothing* moves it at 7 of 17. Fisher p = 0.73. **On the mechanical floor, arms
B, C, E and F are statistically indistinguishable from re-running arm A's own
prompt unchanged.** Any count of the form "k of 17 fixed / reproduced" is a
report of draw-to-draw noise unless k is far outside 7 ± its interval, and none
of them is. The adversarial review's arm-F finding (6 of 17) is confirmed and
generalised: it was not an arm-F quirk, it is the floor.

Only `decompose_arm` clears the floor (p = 0.026), and it clears it in the
*worse* direction — it breaks the floor at 11 of 13 clauses.

### 2. "5 modules structurally identical to arm A" — UNINTERPRETABLE

Pre-registered condition for this verdict: F ≥ 3. It is 15 (signature) and 17
(exact). **A byte-identical re-draw of arm A reproduces arm A's module exactly
0 times out of 17, and by signature 2 times out of 17.** No n=17 arm reaches 5
on either mechanical definition (B 2, C 2, E 1, F 3, G 0). The claim's own
identity predicate is nowhere in the review code, so it cannot be checked — and
that unstated predicate is precisely the series' central weakness. The claim is
not reportable as written.

*(Direction matters: because the null cannot manage even one exact match,
identity to arm A is a strong signal where it does occur — `bucketed_arm` 6/9
exact, `selfreview_arm` 3/9 — not noise. Those two arms barely changed anything;
that is a real finding, not an artefact.)*

### 3. Arm C's borrowed-gloss collapse (24→3) — **SURVIVES, decisively**

Pre-registered survival condition: arm A′ self-citing at ≥ 12 / 17 clauses.

| | clauses with a self-cited borrowed gloss |
|---|---|
| arm A turn 1 | 15 / 17 |
| **arm A′ (NULL)** | **15 / 17** |
| examples_arm (C) | 3 / 17 |

* Arm A vs arm A′, McNemar: **0 discordant pairs, p = 1.0.** Zero noise.
* Per-clause self-cited *count* floor: **F = 1 / 17.**
* **Arm A′ vs arm C, McNemar: 12 discordant pairs, all one way, p = 4.9e-4.**

This is the one headline effect the null makes *stronger*, by supplying the
paired comparator the original p ≈ 1e-6 assumed rather than measured. (The
correct figure is p = 4.9e-4 at clause level against a measured null, not
1e-6 at gloss level against an assumed-fixed 24/24.) `decompose_arm` reproduces
the same collapse independently (3/13).

### 4. Arm B's closure shift (unclear 0→16) — **SURVIVES on `unclear`; the rest is noise**

Pre-registered survival condition: arm A′ producing ≤ 2 `unclear`. **It produced 0.**

| | closure entries |
|---|---|
| arm A turn 1 | cepa 25, cnpa 4, **unclear 0** |
| **arm A′ (NULL)** | cepa 16, cnpa 8, **unclear 0** |
| list_in_prompt_insample (B) | cepa 11, cnpa 4, **unclear 16** |

**Split the claim in two, because the two halves have opposite floors:**

* The **`unclear` verdict has a floor of 0 / 17.** An unmanipulated draw never
  emits one. Arm B's 16 is real and attributable to the manipulation.
* The **cepa↔cnpa composition has a floor of 8 / 17 clauses (47%), with 14 of
  32 closure entries moving under the null** — cepa 25→16, cnpa 4→8 with no
  manipulation whatsoever. **Any part of the closure result that rests on
  cepa-vs-cnpa movement is at the noise floor and is not supported.**

The reported McNemar p = 0.031 ("6 of 11 toward the critic's gold") cannot be
recomputed from the code in `arms_review/`, so which half it rests on is not
determinable here. **If its discordant pairs include cepa↔cnpa flips, it is
void**; if it counted only the appearance of `unclear`, it stands. That must be
resolved before the number is published. **INFERRED, not measured.**

---

## LIMITS — stated, not softened

* **One replicate.** F is a point estimate; the intervals above are wide
  (the mechanical floor is 41%, 95% CI 22–64%). A second replicate was refused
  *before* the run, on arithmetic — it would have crossed the $0.05 cap — not
  after seeing results. **The floor is bounded loosely, and "7 of 17" should be
  read as "roughly two in five", never as a constant.**
* **Where the floor is high, this arm proves the claims are unsupported; it
  does not prove they are false.** A properly powered design (≥5 replicates, or
  paired re-draws per arm) could still separate a real effect at 9/17 from a
  floor at 7/17. Nothing here licenses the opposite claim either.
* **Where the floor is 0 (polarity, arity, self-cited glosses, `unclear`),
  n = 17 with zero events gives a 95% upper bound of ~18%** — low, not zero.
* Arms with n = 9 or 13 are compared to a floor measured at n = 17; the Fisher
  tests account for this, the raw percentages do not.
* 5 of the first 17 calls raised HTTP 503 and were re-sent byte-identically;
  the 503s billed nothing (they raise before `_log_usage`) and generated
  nothing, so no draft was selected on. Disclosed in PREREG.md AMENDMENT 1.

## Bottom line

**The series' floor-based counts do not survive; its two mechanism claims do.**
Four arms' mechanical-floor differences from arm A are noise (p = 0.73 against
an empty manipulation). Arm C's borrowed-gloss collapse and arm B's `unclear`
verdicts sit on measures where the null moves nothing at all, and both hold.
The closure result must be split: `unclear` is real, cepa/cnpa is noise.
