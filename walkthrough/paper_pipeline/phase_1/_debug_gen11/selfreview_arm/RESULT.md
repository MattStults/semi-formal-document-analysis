# RESULT — ARM D: the model applies the review list to its OWN draft, across turns

**Answer: NULL on transfer — but the arm answers the question it was built for, and
the answer is the opposite of what I predicted.**

⭐ **THE HEADLINE.** Of 91 frozen turn-1 defect items, the model **identified 12
(13%)** and **repaired 11 (12%)**. Only **one** item was identified and then not
repaired. **Conditional on identifying a defect, the model repaired it 11 of 12
times (92%) — at the Opus critic's own performance level.** The bottleneck is
**diagnosis, not execution**, and no prior arm could see that.

**Pre-registration:** `PREREG.md`, signed before the first call, including the
transfer / null / manufactured-harm branches and six named predictions.
**Spend: $0.07026** measured against a **$0.12** cap. **9 of 17 clauses
completed** — the other 8 were lost to a reasoning-budget truncation, mechanism
measured below, and **that loss is the biggest threat to the headline; it is
stated in §7, not buried.**

---

## 1. WHAT WAS SENT, AND WHAT WAS VERIFIED BEFORE SENDING

| | value |
|---|---|
| system block | 39,959 chars, sha256 `3a66c5f5…4c34c` |
| **equal to arm A's recorded sha** | ✅ verified by a gate that refuses to send otherwise |
| prompt files | byte-verified copies: `0463449d`, `92dbd355`, `a0c12943`, `7a88183e` |
| turn-1 user blocks rebuilt vs arm A's stored transcripts | **17 of 17 byte-identical** |
| turn-1 assistant drafts | **arm A's own**, resumed, not re-drawn |

⭐ **The comparison is therefore PAIRED, not historical.** Arms B and C are
historical controls on different draws. Arm D and the Opus loop reviewed the
*byte-identical draft of the same clause by the same model*. The only variable is
**who reviews it.**

⛔ Nothing outside `_debug_gen11/selfreview_arm/` was written. No git was run, no
branch switched, no commit made. `ds_opus_loop/`, `runs/`,
`translation_sample/runs/`, `repair_graveyard/`, `prompt/`, `schema.py` and
`resolve_runs/` were read only.

### The design, in one line each (grounds in `PREREG.md` §3)

* **A round is two calls: IDENTIFY then REPAIR.** Production forces the output to
  the module schema with `additionalProperties: false, strict: true`, so a
  per-entry verdict has no field to live in. The IDENTIFY call is the *only*
  departure from production (`format_forcing: "none"`) and it produces no module;
  the REPAIR call runs under production's exact `response_format`. Splitting them
  is what makes identified-vs-repaired observable at all.
* **Eleven entries, not twenty** — arm-B entries 1–9 (the nine highest-yield on
  these very clauses per `ORDERING.md`) plus entry 12 and entry 15. Dropped: 10,
  11, 13, 14 and the low-yield tail, each with a measured reason. **All three
  anti-rules carried in full.**
* **Entry 5 AMENDED, not excluded** — the vacuous-bodied-rule guard is quoted in
  `messages/review_d.md`: *"is there a case this body is FALSE of? If there is
  not, leave the atom exactly as it is."* Scored under H2 below.
* **Imperative, fixed-format reply**: eleven `E<n>: PASS|FIX — <one sentence>`
  lines, no "N/A", each FIX naming the field and the new value; the repair message
  is four lines. This follows the loop's own style result (100+/100+ and 29/29 for
  per-item mechanical imperatives, 0/3 for prose critiques).
* **The span is not re-pasted** — it is already in the transcript; the message
  says *"Re-read the SOURCE TEXT in my first message."*

---

## 2. THE DECISIVE TABLE — the measurement no prior arm could make

Frozen turn-1 defect items are the numbered edits in
`ds_opus_loop/out/<id>.feedback_1.md`, written by the Opus critic against these
exact drafts **before this arm existed**. I score against them; I did not author
them. "Leave X alone" lines are excluded.

| clause | frozen items | FIX lines | **identified** | **repaired** | **identified, NOT repaired** | **never identified** | floor T1 → D |
|---|---:|---:|---:|---:|---:|---:|---|
| `l699_796_n012` | 5 | 5 | **3** | **3** | 0 | 2 | translated → translated |
| `l1001_1107_n005` | 9 | 2 | 2 | 2 | 0 | 7 | translated → translated |
| `l2474_2554_n004` | 29 | 4 | 3 | 3 | 0 | 26 | invalid 2b → invalid 3b |
| `l3239_3382_n002` | 4 | 6 | 1 | 1 | 0 | 3 | **invalid 2b → translated** |
| `l3239_3382_n004` | 30 | 2 | 2 | 1 | **1** | 28 | **invalid 2b → translated** |
| `l171_426_n022` | 3 | 4 | 1 | 1 | 0 | 2 | invalid 4b → invalid 4b |
| `l1707_1973_n006` | 4 | **0** | 0 | 0 | 0 | 4 | translated → translated |
| `l3596_3876_n009` | 4 | **0** | 0 | 0 | 0 | 4 | translated → translated |
| `l4252_4482_n016` | 3 | **0** | 0 | 0 | 0 | 3 | translated → translated |
| **TOTAL (9 clauses)** | **91** | 23 | **12 (13%)** | **11 (12%)** | **1** | **79 (87%)** | 2 improved, 0 regressed |

⚠️ Two clauses carry 29 and 30 items and dominate the denominator. Excluding
them: 32 items, 7 identified (22%), 7 repaired (22%), 25 never identified (78%).
**The shape does not change.**

### What this says, and it is the arm's product

* **87% of the defect mass was never named.** The model held an entry covering the
  defect and answered `PASS`.
* **Of what it did name, it fixed 92%.** Execution is not the problem. This
  matches the Opus loop's edit-performance record (100+/100+, 29/29, 101/101 with
  one miss) — the *same model*, when the diagnosis arrives from outside.
* ⭐ **That is exactly why the positive control converged 15/15.** The critic
  supplied diagnosis; DeepSeek supplied execution. Arm D removes the critic and
  the diagnosis disappears while the execution stays intact.
* **3 of 9 clauses produced zero FIX lines** and returned a module identical to
  the draft — perfect compliance with "change nothing you marked PASS", on modules
  the critic wrote 4, 4 and 3 edits for.

### The three cases that need no rate

⛔⛔ **`l4252_4482_n016` — entry E10 quotes this clause's own remedy verbatim and
the model answered PASS.** The span is *"The assistant should **avoid** repeating
the user's prompt, and generally **minimize** redundant phrases and ideas."* The
module asserts `prefer repeat_user_prompt(R)`, `prefer include_redundant_phrase(R)`,
`prefer include_redundant_idea(R)` — a stated preference **for** the three acts the
span says to avoid. E10, in the model's context, reads: *"`status` has no negative
pole … the natural move is `prefer X` with a read-back that negates it — so the
compiled rule states the OPPOSITE of the document. **Name the avoidance as the act**
(`prefer minimize_redundant_phrases`)."* That parenthesis is this clause's own act
name. **The model answered `E10: PASS`, and production's own `prefer-polarity`
detector fires three times on the module it returned.** A deterministic checker in
the same pipeline sees what the self-review does not.

⛔⛔ **`l3596_3876_n009` — every frozen edit is an E1 edit, and E1 is the list's
#1 entry.** The critic's four edits are: three glosses that restate their own names
(`recognizes_strangeness/2` glossed *"A recognizes the inherent strangeness of X"*),
plus a claim. E1 is titled *"Does a `gloss` restate its predicate's name instead of
defining it?"*, is labelled *"the highest-yield entry in this file, and the cheapest
to run"*, and its worked examples are the same construction. **`E1: PASS`.**

⭐ **`l699_796_n012` — the one clause where it worked.** Five FIX lines, three
naming real defects, all three performed: `tool_instruction` deleted from the
assert body, `concepts` and `inputs` (the narrowed span says *"instructions"*, not
*"tool instructions"* — E3/E4 applied correctly), and the `cepa` closure changed to
`unclear` with a non-circular reason (E2 applied correctly). Two items missed. It
is the clearest evidence that the mechanism can work; it is one clause of nine.

---

## 3. SCORED AGAINST THE PRE-REGISTRATION

| branch | threshold | measured | |
|---|---|---|---|
| **T1** defect-free modules | ≥ 3 of 17 (ceiling 6/17) | **0 of 9** | ❌ |
| **T2** frozen items repaired | ≥ 50% | **12%** | ❌ |
| **T3** frozen items identified | ≥ 50% | **13%** | ❌ |
| **NULL** | ≤1 defect-free ∧ repaired <30% ∧ identified <30% | all three hold | ✅ **NULL** |
| **H1** ≥3 modules acquire a conclusion-changing defect | ≥ 3 | **3 of 9** | ⚠️ **FIRED** (one marginal, named below) |
| **H2** defect from correctly obeying an entry | ≥ 1 | **1** | ⚠️ **FIRED — and it is E6, not E5** |
| **H3** clean floor → failing floor | ≥ 3 | **0 of 9** (2 went invalid → translated) | ✅ did not fire |
| **H4** "repair" of an anti-rule-protected item | ≥ 1 | **0 of 9** | ✅ did not fire |

**Predictions.** **P-a ✅** (null on T1). **P-b ❌ — and it is the arm's most
important miss.** I predicted identification would exceed repair by ≥15 points on
the grounds that arms B/C measured 83–87% of defects *named* by a held entry.
Measured: **13% identified vs 12% repaired — one point apart.** The arm-B/C figure
was mine, computed by me over a finished corpus; it was never evidence that *the
model* could name them. **P-c ✅** (median FIX 2 per clause vs median 4 frozen
items). **P-d ✅** — the amended E5 fired FIX twice and both times caused the
**deletion** of a vacuous rule, never the creation of one; no vacuous bodied rule
appears anywhere. n=2 firings, so this is weak support, not a validation.
**P-e ½** — at least one false charge ✅, zero anti-rule violations ❌.
**P-f unscored** — see §5.

### H1 and H2, itemised

* **`l171_426_n022` — H1 and H2 together, the R57 shape with a different entry.**
  `E6: FIX — In asserts, add lower_level_content(A) to the body of both asserts.`
  It was performed. `lower_level_content/1` is an ontology-derived predicate whose
  own body needs `content_authority`, `authority_hierarchy` and `root_authority`
  facts, so **both prohibitions now fail to fire in any situation that does not
  affirmatively supply an authority level** — the exact weakening E8's
  counter-intuitive half warns about, produced by obeying E6. The critic's reading
  is the opposite: claim C3 belongs to the paragraph's *first* sentence, not this
  node, and should be deleted. **The model encoded it instead.** This is a defect
  created by correctly obeying an entry, and it is not entry 5 or entry 14 — it is
  entry 6, which carried no warning.
* **`l2474_2554_n004` (the marginal one).** `uncertainty_needed(A)` was added to
  the `oblige clarify_uncertainty` body without the `concepts` gloss the schema
  requires, adding a **new** breach (2 → 3) and narrowing an obligation. The
  narrowing is arguably span-supported (*"whenever needed"*); the missing gloss is
  not arguable. Counted as H1; flagged as the case a reader may score differently.
* **`l3239_3382_n002`.** Six FIX lines all say "delete the overstepping
  machinery", and it was done: claim C3, the `overstep` act, its assert and its
  closure are gone. Defensible under E3/E4 — the node's own narrowing stops before
  *"without overstepping"*. But `ESTABLISHES` states that claim, and `PROVIDES`
  names `avoid_overstepping` as a predicate **this module must define**; the module
  now defines nothing while still listing `avoid_overstepping/1` in `requires`.
  **The module no longer expresses its own ESTABLISHES claim.** The floor went
  `invalid` → `translated` on this clause: the score improved as the content left.

⭐ **The E5 amendment held and is worth keeping.** Both E5 firings
(`l3239_3382_n002`, `l3239_3382_n004`) removed rules that were vacuous or
self-referential — including two `ontology` entries with `body: null` over a free
variable, which asserted that *everything* is a transformation task and *every*
setting is interactive. The pre-amendment failure mode (an inert constant converted
into `x(S) :- scenario(S)`) did not occur. **At n = 2 this is a signal, not a
result**, and the amendment is offered as a review-list fix on that basis.

---

## 4. THE MEASURED COST OF SELF-REVIEW, AND WHY 8 CLAUSES ARE MISSING

| call | reasoning chars | content chars |
|---|---|---|
| IDENTIFY (unforced, 9 completed) | **3,585 – 14,541** | 100 – 714 |
| IDENTIFY (8 truncated) | **16,604 – 19,384** | **0** |
| REPAIR (forced, 9) | **0** | 2,123 – 6,669 |

⭐ **The self-review turn triggers thousands of characters of hidden reasoning; the
repair turn triggers none.** On 8 of 17 clauses (47%) that reasoning ran past the
4,096-token `max_tokens` wall **before a single verdict line was emitted**, and the
harness raised rather than keep a half-answer. Those 8 clauses cost $0.02514 and
produced nothing.

The instruction itself was obeyed exactly where it completed: **9 of 9 replies were
exactly eleven `E<n>:` lines and no JSON**, three of them 100 characters total. The
failure is a capacity limit on the reasoning the review turn provokes, not a format
failure.

⛔ **I did not re-run the 8.** Recovering them needs a raised `max_tokens`; at
worst-case pricing that is $0.069 against $0.0497 of remaining cap, so the gate
refuses. Independently: the 8 are selected **by the behaviour under test**, so
re-running them under a different token cap would make the sample heterogeneous in
a way correlated with the outcome. Both reasons point the same way. **See §7 for
which direction this biases the headline — it is the direction that hurts it.**

---

## 5. ROUND 2 WAS NOT RUN, AND THE REASON IS A RESULT

`PREREG.md` §3.6 gated a second repair round on budget. It is not run, and the
budget is the lesser reason: **round 2 targets the identified-but-unrepaired
population, and that population has exactly one member.** Spending ~$0.03 to
re-push a single item would measure nothing. **P-f is unscored, and the reason it
is unscored — that the failure mode it was designed to attack barely exists — is
worth more than the measurement would have been.**

---

## 6. VERDICT, AND WHAT FOLLOWS

**The review list does not transfer to the drafter reviewing itself, and the
mechanism of the failure is now known: the model does not SEE the defects. When it
sees one, it fixes it as reliably as a frontier critic's edit list gets fixed.**

Against the three prior nulls this is a different result, not a fourth repetition:

1. Arms B and C established that a static list in the prompt does not prevent the
   defects, and that 83–87% of defects correspond to a held entry — **a fact about
   the list's coverage, established by me reading finished modules.**
2. Arm D establishes that the same model, holding the same entries, asked directly
   and one at a time about its own finished module, **names 13% of them.** The
   83–87% coverage figure and the 13% detection figure are about different readers
   and were never the same claim.
3. The Opus loop remains the ceiling and is now explained. It was never evidence
   that the list's content is transferable — it was evidence that **DeepSeek's
   repair execution is excellent and its self-diagnosis is not.**

⭐ **What this redirects.** A null on delivery would have argued for better
instructions. A null on *identification with 92% repair* argues for the opposite:
**stop writing instructions and build detectors.** The one deterministic detector
that exists in this pipeline (`prefer-polarity`) caught, on `l4252_4482_n016`, the
precise defect the self-review passed — three times, for free, with no model call.
Several list entries are mechanically checkable in the same way (E1 gloss-restates-
name is *already* a schema check; E5's discriminating-body test, E9's argument-order-
in-gloss test, E2's `cepa`-on-an-excepted-branch test). **The measured evidence now
favours converting review-list entries into checks over rewriting them as prose.**

⛔ **This does not show the list is worthless** — its value to a critic is measured
elsewhere and stands. It does not show a self-review can never work: `l699_796_n012`
shows it working. It shows that at this model tier the diagnosis step is where the
loss is.

---

## 7. LIMITS — read these before quoting any number

* ⚠️ **n = 9 of the intended 17.** Every cell is single-digit. No rate here is
  statistically separated from noise.
* ⛔⛔ **THE LOSS IS NOT RANDOM AND IT CUTS AGAINST MY HEADLINE.** The 8 missing
  clauses are exactly the ones whose self-review reasoned longest. Within the 9
  that completed, longer reasoning goes with more FIX lines (the two longest,
  `l171_426_n022` at 14,541 chars and `l2474_2554_n004` at 13,256, produced 4 FIX
  lines each; the shortest, 3,585 chars, produced 0). **The lost 8 may well have
  identified more, so 13% is plausibly an UNDER-estimate of the identification
  rate.** The 92% repair-conditional-on-identification figure is less exposed to
  this, since it is a ratio within observed items, but it too rests on 12 items.
* ⚠️ **The IDENTIFY call is not production.** Format forcing was off for it. It
  produced no module and the REPAIR call ran under production's exact
  `response_format`, but the drafting regime for that one message is not the one
  arms A/B/C used.
* ⚠️ **Eleven entries, not twenty.** Arm D does not test the same list surface as
  arms B and C. No defect in this arm was covered *only* by a dropped entry, so
  nothing was scored under that exemption — but the arms are not surface-identical.
* ⚠️ **Item counting is coarse** on the two clauses carrying 29 and 30 critic
  edits, several of which are one conceptual defect split across fields. §2 reports
  the figures with those two clauses excluded; the shape is unchanged.
* ⚠️ **CONTAMINATION, as disclosed in `PREREG.md` §9.** I had read
  `ds_opus_loop/FINDINGS.md` in full and both prior arms' results before designing
  this arm, and I know several of these clauses' histories. I could not adjudicate
  blind and did not claim to. The mitigation that carries the headline is
  structural: **the turn-1 defect list is the frozen `feedback_1.md` files, authored
  by the Opus critic before this arm existed.** The identified/repaired counts are
  scored against those, not against a list I wrote after seeing the output.
* ⛔ **Nothing was tuned after results were seen.** `messages/`, `promptsD/` and
  `config_armd.json` are byte-unchanged since the first live call. No second
  variant was run.

## 8. SPEND, RECONCILED

**$0.07026 measured**, cap **$0.12**, gate enforced worst-case against the on-disk
ledger before every send (it refused once, at a $0.1356 first estimate, and the
pricing double-count that caused it was corrected before anything was sent).

* 18 recorded calls (9 clauses × 2): **$0.04512**, in `out/<id>.armd.json`.
* 8 truncated IDENTIFY calls: **$0.02514**, billed and unrecorded by the harness
  because it raised before writing a turn record. Recovered from
  `semi-formal-experiment/usage.jsonl` and added here. ⚠️ **This is a real ledger
  hole in `loop.py`'s design and it is worth fixing: a raising call spends money
  and leaves no turn record**, so `ledger_spent()` under-reports after any
  truncation.
* ⚠️ **43 rows appear in `usage.jsonl` in this arm's time window; only 26 are
  arm D's** (prompt 13.5k–15.0k tokens, matching the transcript shapes above). The
  other 17 have ~11.2k–12.0k prompt tokens, one call each, module-shaped output —
  the shape of a plain 17-clause turn-1 run, **not this arm's**, and their $0.03184
  is not counted here. `_debug_gen11/decompose_arm/`, `forced_verdict_arm/` and
  `retrieval_arm/` appeared on disk **during** this run, so sibling arms were
  executing concurrently and one of them is the likely owner. `priced_by` is the
  same literal string on every row and cannot separate them, so **whoever
  reconciles `spend.py` must split this window by prompt shape, not by row count.**

---

**Adjudicated span-first, floor first, against a defect list frozen before the arm
existed. A null is reported as a null. — adjudicator, 2026-08-16**
