# PREREG — ARM E: a SEPARATE DeepSeek instance critiques the module as a peer

⚠️ **Written and saved BEFORE any live call.** Nothing below may be edited after
the first response arrives; corrections go in `RESULT.md`, marked as such.

---

## 1. THE UNTESTED CELL

One process in this series has an end-to-end success record: DeepSeek drafts →
an **Opus** critic adjudicates into DeepSeek's own transcript → DeepSeek
revises. **15/15 converged in 2–4 turns.** The critic was a local frontier
agent and was never billed, so the process is not priceable as it stands.

Two cheaper conditions have been tested and both failed.

| condition | arm | result |
|---|---|---|
| review list as **static text in the drafting prompt** | six variants (B, C, …) | all null; 0 defect-free drafts |
| **self-review, same instance, same transcript** | `selfreview_arm` (D) | **13%** of frozen defects identified, **92%** of what it identified repaired |

Arm D's product is the split: **the bottleneck is diagnosis, not execution.**

⭐ **Never tested: a SEPARATE DeepSeek instance, with no memory of drafting the
module, critiquing it as a peer.** That is materially different from self-review
in two ways — no anchoring on its own drafting reasoning, and the critic's whole
context is *the span and the module*, not a 40k-char transcript it authored.

**The question:** does a peer DeepSeek critic recover a useful share of the Opus
critic's diagnosis? If yes, the one working process becomes cheap and
API-scalable. If no, **frontier-tier diagnosis is load-bearing and that sets the
price of the whole pipeline** — a valuable null.

## 2. THE MATERIAL — PAIRED, and turn 1 is NOT re-drawn

The same 17 clauses. Turn 1 is arm A's stored draft, resumed byte-identically,
exactly as arm D did. **VERIFIED before this file was written, not assumed:**

| | value |
|---|---|
| system block | 39,959 chars, sha256 `3a66c5f54277…f1f4e4c34c` |
| **equal to arm A's recorded sha** | ✅ (a gate in `run_arme.py` refuses to send otherwise) |
| the four prompt files | byte-verified copies: `0463449d`, `92dbd355`, `a0c12943`, `7a88183e` |
| turn-1 user blocks rebuilt vs arm A's stored transcripts | **17 of 17 byte-identical** |

⭐ **So arm E, arm D and the Opus loop all review the byte-identical draft of the
same clause by the same model. The only variable is who reviews it, and from
where.** This is the cleanest three-way contrast the series has had.

⚠️ **Cost of reuse, stated:** arm E has no independent turn-1 sample and cannot
speak to turn-1 variance.

## 3. THE DESIGN, AND WHY EACH CHOICE WAS MADE

### 3.1 The critic is a fresh call with NO drafting transcript

One user message, in a new context:

1. **arm A's turn-1 user block, byte-identical** — the span, the narrowing, the
   node header, the cross-references. Nothing about the span is re-worded.
   ⚠️ That block ends *"Write the module for clause X."*; the critic message
   opens by explicitly cancelling that line. **Disclosed, not hidden:** it is a
   one-line override, and the alternative — editing the block — would have
   destroyed the byte-identity that makes this arm paired.
2. **the module under review**, verbatim, framed as *another author's*.
3. **the review list**, §3.3.

The **system block is arm A's, in full**. Rejected by name: *a lean critic system
prompt*. A critic that does not hold the twelve rules, the schema and the worked
example cannot tell a schema-forced construction from a defect, and would
manufacture false charges the Opus critic never made. It also keeps the
cacheable prefix identical across every call in the series.

### 3.2 The critic call is NOT format-forced

⚠️ **MEASURED and decisive:** `reasoning_chars` is a perfect discriminator —
185/185 format-forced calls emit **0** reasoning characters, 64/64 unforced emit
**>0** — and arm D's diagnosis quality tracked reasoning length (its two longest
reasoners produced 4 FIX lines each; its shortest produced 0). **Forcing the
critic's output shape would destroy the very faculty under test.**
`format_forcing: "none"` for the critic call, exactly as arm D's IDENTIFY call.
The critic call produces **no module**. The repair call runs under production's
exact `response_format`.

### 3.3 The critic sees the SAME eleven-entry review list arm D saw

The entries and all three anti-rules are **byte-identical** to
`selfreview_arm/messages/review_d.md`; only the framing header and the
reply-format bullets are rewritten from second to third person, plus one clause
pointing "my first message" at the system block.

Grounds: it makes the contrast against arm D **one variable — self vs peer.**
Rejected by name: *an unaided critic with no list*. It tests a weaker and
different condition, and arms B/C already establish that the model does not
spontaneously apply these classes; a null there would be uninterpretable
("maybe it just did not know what to look for").

⚠️ **Contamination, disclosed:** the list was distilled from the Opus loop's
findings **over these very 17 clauses**, so it is in-sample. That is a defect of
the list, not of this arm — arm D held exactly the same advantage and scored
13%, so the comparison is unaffected.

### 3.4 The findings enter the drafting transcript in the MEASURED-EFFECTIVE form

⚠️ MEASURED across 100+ edits: short, imperative, **one sentence per edit**,
ending *"Change nothing else"* was performed 100+/100+ and 29/29; ~3,900-char
prose critiques scored **0/3**.

The critic already replies in eleven `E<n>: PASS|FIX — <one sentence>` lines. The
**FIX sentences are extracted mechanically** (no rewriting by me, no model call)
and rendered in the Opus loop's own feedback shape, verbatim template:

```
{n} edits. Make each one exactly.

1. <sentence>
2. <sentence>
…

Change nothing else.
```

⭐ This means the **repair side of arm E and the repair side of the Opus loop are
regime-identical**: same draft, same transcript position, same feedback form.
Only the author of the sentences differs. `PASS` lines are dropped: the Opus
critic never sent ratifications either.

**Zero FIX lines ⇒ no repair call is sent** for that clause, and its post-module
is the turn-1 draft, byte-identical. Sending "change nothing" would measure
nothing and cost money. It is recorded as *critic found nothing*, which is
itself a diagnosis result.

### 3.5 ONE critic→repair cycle, and that is the right comparison anyway

$0.12 does not buy a second cycle (34 more calls). It does not need to: the
paired comparator is **the Opus loop's `feedback_1` → `turn2`**, one round of
feedback on the identical draft, whose one-round convergence is **6 of 17**.
Turns-to-convergence is reported against that, and the arm's inability to run a
second cycle is a stated limit, not a hidden one.

### 3.6 The critic's `max_tokens` is raised to 7,168; production's 4,096 stays for repair

⛔ Arm D lost **8 of 17 clauses (47%)** to reasoning that ran past a 4,096-token
wall before a single verdict line was emitted, and **the loss was correlated with
the outcome** (the longest reasoners were the ones lost). Its own RESULT names
that as the biggest threat to its headline. Repeating that flaw would repeat it.
The critic cap is therefore **7,168 for all 17 clauses, uniformly, fixed in
advance**. Arm D's truncated calls hit the wall at 16.6k–19.4k reasoning chars;
7,168 tokens is roughly 33k chars, ~1.7× that.

⛔ **No clause is retried at a different cap.** A retry set selected *by the
behaviour under test* would make the sample heterogeneous in a way correlated
with the outcome — arm D's own stated reason for declining. Uniform up front,
no retries after. Any truncation is reported as a loss and its billed cost is
recovered from `usage.jsonl`.

⚠️ **Departure disclosed.** For calls that *complete*, the regime is identical to
arm D's IDENTIFY call; only the truncation rate differs.

### 3.7 Spend

Hard cap **$0.12**, owner-set, enforced in `run_arme.py:CAP_USD`, worst-case
priced against the on-disk ledger before every phase.

| phase | calls | in (chars) | worst-case each | worst-case total |
|---|---:|---|---:|---:|
| **critic** | 17 | 39,959 sys + ~2,223 user + ~3,645 module + 10,830 list ≈ 56.7kc ≈ 14.2k tok | $0.00399 | **$0.0678** |
| **repair** | ≤17 | 39,959 + ~2,223 + ~3,645 + ~600 edits ≈ 46.4kc ≈ 11.6k tok, out 4,096 | $0.00277 | **$0.0471** |
| | | | **total** | **$0.1149** |

Measured rates (~$0.0027/call) predict **≈ $0.09**. Fits at worst case with
$0.005 of margin. ⛔ Over the cap, nothing is sent.

⚠️ **THE LEDGER HOLE, and how it is handled.** `translate.Client._log_usage`
runs BEFORE `_check_envelope`, so **a truncated or empty completion is billed
and then raises, leaving no turn record** — it hid 36% of arm D's spend. The
gate here therefore uses `max(on-disk records, usage.jsonl attribution)` and
`reconcile.py` re-attributes the whole window by prompt shape before the spend
of record is quoted. The starting `usage.jsonl` line number is recorded before
the first call.

## 4. THE FROZEN DEFECT INVENTORY — authored before this arm existed

Scoring uses `ds_opus_loop/out/<id>.feedback_1.md` — the Opus critic's
span-first adjudication of **these exact drafts**, frozen on disk, written before
arm D and arm E existed. Each numbered edit that changes something is one item;
"leave X alone" lines are excluded. **This is arm D's denominator, unchanged**,
so arms D and E are scored by one predicate over one list.

⛔ **No ninth defect predicate is invented.** The mechanical module measures come
from `arms_review/floor.py`, `arms_review/measures.py` and
`licence_control/measure.py` — **imported, not reimplemented**, so arm E lands in
the same table as every arm before it.

## 5. THE BASELINES, stated before looking

| B# | baseline | value | source |
|---|---|---|---|
| **B1** | turn-1 drafts defect-free | 0 of 17 | arm A |
| **B2** | ⭐ clauses converged after ONE round of **Opus** feedback | **6 of 17** | Opus loop |
| **B3** | Opus-critic edits performed by DeepSeek | 100+/100+, 29/29, 101/101 with 1 miss | R56/R61/R62 |
| **B4** | ⭐ **self-review identification** | **13%** (12 of 91 items, n=9 clauses) | arm D |
| **B5** | ⭐ **repair conditional on identification** | **92%** (11 of 12) | arm D |
| **B6** | self-cited borrowed glosses | baseline 25/26, null 24/29, worked examples 3/24, decomposition 3/21 | cross-arm |
| **B7** | ⛔ **NOISE FLOOR, MEASURED** | a byte-identical re-draw changes **7 of 17** clauses on error count, **3 of 17** on `floor_clean`, and reproduces the module **0/17** exactly | `arm_aprime` |

⛔ **B7 governs every mechanical module comparison in this arm.** A change of ≤3
on `floor_clean` or ≤7 on error count is **noise and will be reported as noise**,
however it points. It does **not** govern the identification/repair counts: those
are scored per item against a frozen list, on byte-identical input drafts.

## 6. THE BRANCHES

### TRANSFER — any one of:
* **T3 (⭐ THE HEADLINE — diagnosis).** ≥ **30%** of frozen turn-1 items correctly
  named by a critic FIX line. Grounds for 30%: it is >2× arm D's 13% and is the
  point at which "a peer critic recovers a useful share of the Opus critic's
  diagnosis" is arguable at n=17.
* **T2 (repair).** ≥ **40%** of frozen turn-1 items repaired in the post module.
  (Arm D: 12%.)
* **T1 (the strong one).** ≥ **3 of 17** post-repair modules carry no defect I
  would have sent an edit for. Baseline 0; one-round Opus ceiling 6 of 17.

### NULL
* identification ≤ **20%** **and** repaired ≤ **20%** **and** ≤1 defect-free
  module.
* ⚠️ A null here is **not** a repeat of arm D. Arm D says *the drafter cannot
  diagnose its own module*. Arm E would say *this model cannot diagnose this
  class of module at all, from any vantage point* — which prices the pipeline:
  **frontier-tier diagnosis is load-bearing and cannot be substituted at
  $0.0002/call.**

### AMBIGUOUS
* Anything between: identification in 20–30%. Reported as a partial lift with
  the cell counts, and explicitly **not** claimed as transfer.

### MANUFACTURED HARM — scored separately and reported even if everything improves
* **H1 regression.** ≥3 post modules acquire a conclusion-changing defect the
  turn-1 draft did not have.
* **H2 obedience harm** (the R57 / E6 shape). ≥1 defect that is the direct
  product of correctly obeying an entry.
* **H3 floor regression.** ≥3 modules whose turn-1 floor was clean fail after.
  ⚠️ This threshold sits exactly ON the measured 3-of-17 noise band (B7) and a
  bare firing will be reported as **indistinguishable from noise**.
* **H4 false repair from an anti-rule.** ≥1 "repair" of an anti-rule-protected
  item (schema-forced tautological binder, contract-required `NEEDS` name in
  `requires`, rewritten read-back).
* **H5 (peer-specific, new).** ≥ **25%** of the critic's FIX lines are **false
  charges**. A critic with no memory of the drafting rationale has more room to
  mis-charge than a self-reviewer does. If H5 fires alongside a T3 lift, the
  lift is **not** bankable without a filter, and that will be said.

### THE DECISIVE READOUT
Per clause, every frozen item in one of four states: **IDENTIFIED+REPAIRED ·
IDENTIFIED+UNREPAIRED · NOT-IDENTIFIED · N/A**; and every FIX line as **real ·
false charge · anti-rule violation**. Identical to arm D's table, so the two sit
side by side. ⭐ **Diagnosis and repair are reported as two separate numbers**,
never multiplied into one.

## 7. PREDICTIONS, on the record

* **P-a.** Identification **lifts above arm D's 13% but lands below 30%** —
  headline **NULL or AMBIGUOUS on T3**. Confidence: moderate. Grounds: arm D's
  two sharpest cases (E1 passed on a clause whose four frozen edits are *all* E1;
  E10 passed where production's own deterministic detector fires three times) look
  like *reading capability*, not self-anchoring, and a peer vantage does not fix
  reading capability.
* **P-b.** **Repair conditional on identification stays ≥ 80%.** Confidence:
  high. Grounds: B3 and B5 agree across two independent instruments.
* **P-c.** The **false-charge rate is HIGHER than arm D's**, because the critic
  lacks the drafting context that made some constructions defensible.
  Confidence: moderate. This is what H5 is for.
* **P-d.** ⭐ **E1 and E10 remain systematically under-called.** This is the
  sharpest single diagnostic in the arm and needs no rate: if the peer critic
  catches the clauses arm D passed on, anchoring was the mechanism; if it PASSes
  them again, arm D's capability explanation is confirmed from a second vantage.
  Predict: still under-called.
* **P-e.** **More FIX lines per clause than arm D's median of 2**, because the
  critic has no ownership of the module. Confidence: moderate. ⚠️ P-e rising
  while T3 stays flat would mean the critic is *charging more and finding no
  better* — that is H5 territory, not transfer.
* **P-f.** **Self-cited borrowed glosses stay in the 24–29 band.** Confidence:
  high — only heavy interventions (worked examples, decomposition) have moved
  that class, and a critique turn is not one.
* **P-g.** **Fewer than 8 of 17 critic calls truncate** at the raised 7,168 cap
  (arm D: 8 of 17 at 4,096).

## 8. PROTOCOL COMMITMENTS

1. ⛔ **No tuning after seeing results.** `messages/`, `promptsE/` and
   `config_arme.json` are frozen at the first live call. A second variant would
   have to be pre-registered as such and **both** reported.
2. **The floor runs first** on every module — `schema.validate_all` then
   `checks.run_checks` — and my adjudication is on top of it, never instead.
3. **Span-first adjudication**, as the loop and arms B/C/D did.
4. ⛔ **READ-ONLY outside `_debug_gen11/ds_critic_arm/`.** Nothing under
   `runs/`, `translation_sample/runs/`, `repair_graveyard/`, `prompt/`,
   `schema.py`, `resolve_runs/`, `arms_review/`, `ds_opus_loop/`,
   `selfreview_arm/` or any other arm directory is written. No git is run, no
   branch switched, no commit made, and never `git commit --no-verify`.
5. **n = 17, single-digit cells throughout.** No rate reported here is
   statistically separated from noise, and B7 is quoted beside every mechanical
   comparison.
6. **A null is a real result and is reported as one**, undiluted. Neither
   direction is softened.

## 9. CONTAMINATION, DISCLOSED

I have read `selfreview_arm/PREREG.md` and `RESULT.md` in full, `measures.py`,
`floor.py`, `licence_control/measure.py`, `arm_aprime/RESULT.md` in part, and
`review_d.md` in full. I therefore know arm D's per-clause outcomes, the E1/E10
cases by name, and the frozen item counts for 9 of the 17 clauses. **I cannot
adjudicate these clauses blind and I do not claim to.** Mitigations, structural
rather than promises:

* The defect list is the **frozen `feedback_1.md` files**, authored by the Opus
  critic before either arm existed. I score against them; I do not write them.
* The mechanical measures are computed by **imported code published for prior
  arms**, on a scorer I did not write.
* The critic's list is **byte-identical to arm D's**, so entry selection carries
  no choice of mine.
* Every contested FIX-line classification quotes the span text in `RESULT.md`.

---

**Signed before the first call.** — adjudicator, 2026-08-16
