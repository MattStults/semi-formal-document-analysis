# RESULT — ARM E: a SEPARATE DeepSeek instance critiques the module as a peer

**Answer: AMBIGUOUS on the headline, and the arm splits the question in a way no
prior arm could. A peer DeepSeek critic MORE THAN DOUBLES diagnosis over
self-review — and the drafter's repair reliability COLLAPSES from 92% to 62%
while doing it. The bottleneck moved; it did not disappear.**

⭐ **THE HEADLINE, both halves.** Of 89 frozen turn-1 defect items across 13
clauses, the peer critic **identified 26 (29%)** against self-review's **13%**;
on the **6 clauses both arms completed**, the paired figures are **37% (10/27) vs
15% (4/27)**. But of the 26 items it identified, only **~16 were actually
repaired (≈62%)**, against self-review's **92%** and the Opus critic's
100+/100+. **5 of 13 modules acquired a conclusion-changing defect** (H1 fires
hard). Diagnosis improved; prescription got worse.

**Pre-registration:** `PREREG.md`, signed before the first call, with the
transfer/null/ambiguous/harm branches and seven named predictions.
**Spend of record: $0.08335** against a **$0.12** cap, reconciled against
`usage.jsonl`. **13 of 17 clauses completed**; 4 lost to reasoning truncation,
mechanism measured in §5.

---

## 1. WHAT WAS SENT, AND WHAT WAS VERIFIED BEFORE SENDING

| | value |
|---|---|
| system block | 39,959 chars, sha256 `3a66c5f5…4c34c` |
| **equal to arm A's recorded sha** | ✅ gate refuses to send otherwise |
| prompt files | byte-verified copies: `0463449d`, `92dbd355`, `a0c12943`, `7a88183e` |
| turn-1 user blocks rebuilt vs arm A's stored transcripts | **17 of 17 byte-identical** |
| turn-1 assistant drafts | **arm A's own**, resumed, not re-drawn |
| review list shown to the critic | **byte-identical** to arm D's eleven entries + three anti-rules |

⭐ **Arm A (Opus critic), arm D (self-review) and arm E (peer critic) all review
the byte-identical draft of the same clause by the same model. The only variable
is who reviews it, and from where.**

⛔ Nothing outside `_debug_gen11/ds_critic_arm/` was written. `ds_opus_loop/`,
`selfreview_arm/`, `arms_review/`, `licence_control/`, `runs/`,
`translation_sample/runs/`, `repair_graveyard/`, `prompt/`, `schema.py` and
`resolve_runs/` were read only. No git was run, no branch switched, no commit
made.

### The design, one line each (grounds in `PREREG.md` §3)

* **The critic is a fresh call with no drafting transcript** — arm A's turn-1
  user block byte-identical, then the module framed as another author's, then
  the list. Arm A's full system block, so the critic holds the same rules the
  Opus critic held.
* **Not format-forced** (`format_forcing: "none"`) — forcing is MEASURED to zero
  out reasoning, and diagnosis tracks reasoning length.
* **Same eleven entries as arm D**, so the contrast is one variable: self vs peer.
* **`max_tokens` 7,168 for the critic, uniform, no retries** — arm D lost 47% of
  its sample at 4,096 to a loss correlated with the outcome.
* **Findings enter the drafting transcript in the Opus loop's own imperative
  edit-list form**, FIX sentences extracted mechanically, `PASS` lines dropped,
  ending "Change nothing else." **The repair side of arm E and of the Opus loop
  are regime-identical; only the author of the sentences differs.**

---

## 2. THE DECISIVE TABLE

Frozen items are the numbered edits in `ds_opus_loop/out/<id>.feedback_1.md` —
the Opus critic's span-first adjudication of these exact drafts, written before
either arm existed. "Leave X alone" lines excluded. **This is arm D's
denominator, unchanged.**

| clause | frozen | FIX lines | **identified** | **repaired** | FIX lines performed | floor T1 → E |
|---|---:|---:|---:|---:|---:|---|
| `l1_170_n056` | 10 | 6 | **4** | 5 | 5/6 | invalid → invalid |
| `l1001_1107_n005` | 9 | 3 | 3 | 3 | 3/3 | translated → translated |
| `l1368_1541_n019` | 11 | 2 | 3 | 3 | 2/2 | invalid → invalid |
| `l1707_1973_n006` | 4 | 2 | 1 | **0** | 1/2 | translated → translated |
| `l1707_1973_n022` | 10 | 1 | 1 | 1 | 1/1 | translated → translated |
| `l171_426_n022` | 3 | 2 | 2 | 1 | 2/2 | invalid → invalid ⚠️H1 |
| `l2821_3040_n017` | 17 | 3 | 3 | 2 | 2/3 | translated → translated |
| `l3147_3238_n003` | 3 | 2 | **1** | **0** | 2/2 | translated → translated ⛔H1 |
| `l3239_3382_n002` | 4 | 6 | 2 | 1 | 3/6 | invalid → invalid ⚠️H1 |
| `l3596_3876_n009` | 4 | 1 | 1 | 1 | 1/1 | translated → translated |
| `l3877_3953_n014` | 5 | 3 | 2 | 1 | 3/3 | translated → translated |
| `l4252_4482_n005` | 6 | 7 | 2 | 1 | 5/7 | invalid → invalid ⚠️H1 |
| `l4252_4482_n016` | 3 | 1 | 1 | 1 | 1/1 | translated → translated |
| **TOTAL (13)** | **89** | **39** | **26 (29%)** | **20 (22%)** | **31/39 (79%)** | 8 clean → 8 clean |

### The three-way paired comparison, on the 6 clauses arms D and E both completed

| | frozen | identified | repaired |
|---|---:|---:|---:|
| **arm D — self-review** | 27 | **4 (15%)** | 4 (15%) |
| **arm E — peer critic** | 27 | **10 (37%)** | 7 (26%) |
| **arm A — Opus critic** | 27 | 27 (authored) | ~27 |

⭐ **This is the cleanest cell the series has produced: identical drafts,
identical list, identical model, one variable.** A peer vantage roughly
**doubles** identification. n = 6 clauses / 27 items; single-digit cells.

### What the peer vantage fixed, and what it did not

⭐⭐ **The two cases arm D's RESULT called out by name were both CAUGHT.**
* `l4252_4482_n016` — arm D answered `E10: PASS` while the module stated a
  preference *for* the three acts the span says to avoid. **Arm E's critic wrote
  the correct FIX with the correct remedy and the correct rationale**, and the
  drafter performed it: `prefer repeat_user_prompt(R)` → `prefer
  avoid_repeating_user_prompt(R)`, all three acts, matching the frozen edit.
* `l3596_3876_n009` — arm D answered `E1: PASS` on a clause whose four frozen
  edits are *all* E1. **Arm E's critic wrote `E1: FIX`** and named the offending
  gloss. ⚠️ It named **one of the three** identical E1 defects; the other two
  glosses restate their names untouched.

⛔ **So arm D's failure on those clauses was a VANTAGE effect, not a reading
ceiling — and that is the single most informative result here.** My P-d
predicted the opposite and was wrong. It also has a limit: the critic finds *a*
member of a defect class and stops, rather than sweeping the class.

⛔ **The critic is not internally consistent about its own entries.** It demanded
`cepa → unclear` on **six** clauses and answered `E2: PASS` on
`l4252_4482_n016`, whose frozen edit requires exactly that change, and on
`l1707_1973_n006`, same. The entry fires or does not on grounds invisible from
the output.

---

## 3. ⭐ THE ARM'S NEW FINDING: DIAGNOSIS ROSE AND PRESCRIPTION FELL

**Repair conditional on identification: ≈62% (16 of 26), against arm D's 92% (11
of 12) and the Opus critic's 100+/100+.** The *same model*, on the *same drafts*,
under the *same transcript regime*, executed worse. Two measured mechanisms.

**(a) The critic offers the drafter a CHOICE, and the Opus critic never does.**
⭐ MEASURED: **11 of 39 FIX lines (28%) contain "either … or", "or delete",
"or remove", "or mark assumed"**. Across all 17 Opus `feedback_1.md` files there
is **1** such line. Every place the harm landed, the drafter took the cheap,
deleting branch:

* ⛔⛔ **`l171_426_n022` — arm D's H1/H2 case REPRODUCED EXACTLY, by a different
  critic.** `E6: FIX — … either add a body condition referencing
  lower_level_content to both asserts, or delete C3.` The drafter added it, plus
  an invented `influences/2` input. Both prohibitions now fail to fire in any
  situation that does not affirmatively supply authority facts — the exact
  weakening E8's counter-intuitive half warns about. The Opus ruling is the
  opposite: C3 belongs to the paragraph's first sentence and should be **deleted**.
  **E6 has now produced this defect in two independent arms with two different
  critics. It is a defect-generating entry and that is a measured claim about the
  review list, not about either model.**
* **`l3239_3382_n002`** — four of six FIX lines offered "delete it or mark it
  assumed". The `forbid overstep` assert and its closure are gone, `C3` remains
  in `claims`, `avoid_overstepping/1` remains in `requires`, and `PROVIDES` names
  a predicate the module now defines nowhere. **The module no longer expresses
  its own ESTABLISHES claim** — the identical regression arm D produced here.
  Floor `errors` 2 → 1: the score improved as the content left.
* **`l4252_4482_n005`** — the biggest frozen defect **was repaired** (both
  ontology entries deleted, so accented speech is no longer forbidden for every
  accent). But the `permit` was deleted with them, and `forbid speak_in_accent(A)
  :- exaggerated_or_stereotypical(A)` now has a body predicate defined nowhere:
  the prohibition can never fire.

**(b) One sentence cannot carry a remedy specification.** ⛔⛔ The sharpest case:

* **`l3147_3238_n003`, the clause whose decisive historical defect is the lost
  disjunction.** ⭐ **The peer critic FOUND it** — `E11: FIX — replace the three
  separate oblige entries on the identical body with one act over a disjunction,
  since satisfying one disjunct (tool, hedge, or explain) satisfies the span.`
  That is a diagnosis arm D never reached. **The repair then deleted two of the
  three obligations**, leaving `oblige use_tool_to_gather_info(R) :-
  lacks_sufficient_confidence(R)` alone with a read-back that recites all three
  alternatives. The module now says *use a tool*; the sentence shown to a
  reviewer says *tool, hedge, or explain*. The Opus feedback on this same defect
  spends two paragraphs forbidding precisely this ("the three named responses
  have to stay individually visible … a single obligation on one opaque predicate
  is a hollow stub"), and requires that an inexpressible disjunction be **stated
  in `claims`**. Neither survived compression to one sentence.
  **The floor is `translated`, `repair_needed=False`, 0 breaches. Nothing
  mechanical sees it.**
* **`l1_170_n056`** — the exception was attached to the obligation's body, as
  the frozen item demands, using `not developer_instruction(I), not
  system_instruction(I), not conflicts_with(R, I)` with `I` **unbound under
  negation**. The Opus feedback rules this out in the same sentence that states
  the item: *"rather than being left to negation-as-failure with no account of
  why the exception reaches this case."* Floor `errors` 5 → 1.

⭐ **The generalisation, stated as INFERRED, not measured:** the Opus critic's
value is not only *noticing*. It is that its edit names the field, the new value,
the branch NOT to take, and the constraint the fix must preserve. **A peer
critic recovers a real share of the noticing and almost none of that.**

---

## 4. MECHANICAL MEASURES — one code path, scored against the measured noise floor

Computed by `licence_control/measure.py` over `arms_review/floor.py` and
`measures.py`, **imported, not reimplemented**. All columns restricted to the
same 13 clauses.

| set | n | floor_clean | selfcited/requires | errors | polarity | asserts | bodiless | closure mix |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **armA turn-1 (the shared draft)** | 13 | 8 | 19/20 | 14 | 0 | 24 | **0** | cepa 19, cnpa 2 |
| **armA turn-2 (OPUS, 1 round)** | 13 | **11** | 16/18 | 7 | 0 | **28** | 0 | unclear 10, cepa 11, cnpa 2 |
| **armA final (OPUS gold)** | 13 | **13** | 16/17 | 0 | 0 | 23 | 0 | **unclear 14, cepa 5, cnpa 1** |
| **armE post (DS critic)** | 13 | **8** | 19/20 | 9 | 0 | **18** | **0** | **unclear 14, cepa 5, cnpa 1** |

⛔ **B7, the MEASURED noise floor** (`arm_aprime`): a byte-identical re-draw moves
error count on **7 of 17** clauses and `floor_clean` on **3 of 17**.

* **`floor_clean` 8 → 8. No movement at all**, against Opus's 8 → 11 after one
  round. Not noise in either direction; simply flat.
* **`errors` 14 → 9.** ⚠️ A drop of 5 is **inside the 7-clause noise band and is
  reported as noise** — and §3 shows two of the drops (`l3239_3382_n002`,
  `l1_170_n056`) are content leaving the module, not defects being fixed.
* ⭐ **`closure` mix: `cepa` 19 → 5, `unclear` 0 → 14 — IDENTICAL to the Opus
  gold's final mix.** This is the one class where the peer critic reaches
  frontier-critic output, and it is the review list's E2. It is also the only
  class where the FIX line needs no remedy specification: the value is named in
  the entry itself.
* ⛔ **`asserts` 24 → 18, while the Opus critic went 24 → 28.** **The peer
  critic's loop DELETES normative content and the frontier critic's ADDS it.**
  That single row is the arm's harm signature and it points the same way as §3.
* **Self-cited borrowed glosses 19/20 → 19/20, unmoved** (P-f). The class only
  heavy interventions have moved (worked examples 3/24, decomposition 3/21) and a
  critique turn is not one.
* **Bodiless asserts: 0 throughout.** **Polarity mismatches: 0 throughout** —
  note the `prefer`-polarity defect on `l4252_4482_n016` was real and repaired,
  and `checks.polarity_mismatches` scored 0 on the broken draft, so that detector
  did not see it either.

---

## 5. COST, TRUNCATION, AND THE LEDGER HOLE

**Spend of record $0.08335**, cap $0.12, reconciled (`reconcile.json`).
⚠️ On-disk records total **$0.06723**. The **$0.01612 difference is the measured
hole**: 4 critic calls were billed and then raised on truncation, leaving no
turn record. `run_arme.py` writes a zero-cost record for each and the gate takes
`max(records, ledger)`; **the ledger figure is the one quoted.** 30 ledger rows in
the window, **all 30 attributable to arm E by prompt shape, 0 unattributed** — no
sibling arm ran concurrently this time.

| | value |
|---|---|
| critic calls (unforced, 7,168 cap) | 17 sent, **13 completed, 4 truncated** |
| repair calls (forced, 4,096) | 13 sent, **13 completed** |
| **cost per completed clause** | **$0.0064** (critic + repair) |
| Opus loop, for comparison | $0.005/clause of API spend over 2–4 turns — **plus an unbilled frontier critic** |

⭐ **The `reasoning_chars` discriminator replicates perfectly and extends the
measurement: 17/17 unforced calls emit >0 (8,464–31,723 chars); 13/13 forced
calls emit exactly 0.** Running totals are now 202/202 forced at zero and 81/81
unforced above it.

⭐⭐ **AND IT SUPPLIES THE MECHANISM FOR THE LIFT.** Arm D's completed
self-reviews reasoned **3,585–14,541** chars. Arm E's peer critiques reasoned
**8,464–31,723** — **the peer critic thinks roughly 2.5× harder about the same
module, from a colder start.** That is measured, not inferred, and it is the most
plausible account of a 15% → 37% identification lift with no other variable moved.

**The 4 truncations** hit the wall at **29,530 / 30,125 / 30,606 / 31,723**
reasoning chars — i.e. the longest reasoners again, the same selection arm D
suffered. Raising the cap 1.75× cut the loss from **8/17 to 4/17** (P-g held) but
did not remove it, because the peer condition also raised the reasoning. ⛔ **Not
retried at a higher cap**, per `PREREG.md` §3.6: the truncated set is selected by
the behaviour under test. **This biases the headline in the same direction it
biased arm D's — the lost clauses are the ones the critic worked hardest on, so
29% is plausibly an UNDER-estimate.** It is stated here, not buried.

---

## 6. SCORED AGAINST THE PRE-REGISTRATION

| branch | threshold | measured | |
|---|---|---|---|
| **T3** frozen items identified | ≥ 30% | **29%** (37% on the paired 6) | ❌ by one point |
| **T2** frozen items repaired | ≥ 40% | **22%** | ❌ |
| **T1** defect-free modules | ≥ 3 of 13 | **0** | ❌ |
| **NULL** | ident ≤20% ∧ repaired ≤20% ∧ ≤1 clean | 29% / 22% | ❌ not a null |
| ⭐ **AMBIGUOUS** | identification 20–30% | **29%** | ✅ **THIS IS THE VERDICT** |
| **H1** ≥3 modules acquire a conclusion-changing defect | ≥3 | **5 of 13** | ⛔ **FIRES HARD** |
| **H2** defect from correctly obeying an entry | ≥1 | **≥2** (E6 on `l171`, E11 on `l3147`) | ⛔ **FIRES** |
| **H3** clean floor → failing floor | ≥3 | **0 of 13** | ✅ did not fire |
| **H4** anti-rule violated in repair | ≥1 | **2** | ⛔ **FIRES** |
| **H5** ≥25% of FIX lines are false charges | ≥25% | **5%** (2 of 39) | ✅ did not fire |

**H4, itemised.** Anti-rule 3 — *"Never make `status` and `read_back` agree by
REWRITING THE READ-BACK. Fix the formal item."* — was violated twice, **by the
drafter, not charged by the critic**: on `l3147_3238_n003` the read-back was made
to carry a disjunction the formal item had just lost (the anti-rule's exact
failure mode, inverted), and on `l4252_4482_n016` all three read-backs were
rewritten where the frozen edit says *"Keep every read-back word for word — they
are already correct and must not be touched."* The formal item was also fixed
there, so that one is the marginal case.

**H5's two false charges**, both contradicting an explicit frozen ruling:
`l1001_1107_n005` `E4` charged a `licence` the Opus edit list explicitly says to
leave alone (item 4: *"Leave that ontology entry's `licence` and `cites` exactly
as they are"*), and it was performed, leaving the module with two `root_authority`
ontology entries. `l4252_4482_n005` `E2` demanded `cepa → unclear` where the
frozen edit sets the new closures to `cepa`; also performed.

### Predictions

* **P-a ✅** — identification above 13%, below 30%; AMBIGUOUS, as predicted.
* **P-b ❌ — and it is the arm's most important miss.** I predicted repair
  conditional on identification would stay ≥80% on the grounds that B3 and B5
  agree across two instruments. Measured **≈62%**. **Repair reliability is not a
  property of the model; it is a property of how completely the edit is
  specified.** That reframes B3 and B5: they were measurements of *Opus's edit
  writing* as much as of DeepSeek's execution.
* **P-c ❌** — I predicted more false charges from a critic lacking drafting
  context. Measured 2 of 39 (5%), *lower* than self-review's rate. The peer
  critic is conservative, not trigger-happy; its errors are omissions.
* **P-d ❌ — and the miss is informative.** I predicted E1 and E10 would stay
  under-called. Both were caught, on the two clauses arm D's RESULT named. **Arm
  D's failure there was vantage, not capability.**
* **P-e ½** — mean FIX lines 3.0 vs arm D's 2.6; medians both 2. Not separated.
* **P-f ✅** — self-cited glosses 19/20 → 19/20, unmoved.
* **P-g ✅** — 4 of 17 truncations, under the predicted 8.

---

## 7. VERDICT, AND WHAT IT PRICES

**A separate DeepSeek instance is a materially better diagnostician than the same
model reviewing itself — roughly double, on identical drafts — and a materially
worse prescriber than a frontier critic. The one working process does not become
cheap by swapping the critic's model, because what the frontier critic supplies
is not only the finding.**

1. **Arm D's conclusion needs amending, and this arm amends it.** Arm D
   concluded *the model does not SEE the defects*. Arm E shows it sees roughly
   twice as many from a cold, peer vantage, thinking ~2.5× longer — including
   both clauses arm D flagged as evidence for a reading ceiling. **Vantage is
   real and worth ~15 points of identification.**
2. **But the binding constraint moved rather than lifting.** 29% identified, 22%
   repaired, **0 defect-free modules**, and **5 of 13 modules regressed**.
   Shipping this loop unsupervised would delete normative content: `asserts`
   24 → 18 where the Opus loop went 24 → 28.
3. ⭐ **The actionable finding is about the FIX LINE, not the model.** 28% of the
   critic's edits offer the drafter a branch; the Opus critic's offer 1 in 17
   files. Every H1 case is a cheap branch taken. **The next instrument is a
   critic whose reply format forbids disjunctive remedies and requires the
   field, the new value, and what must be preserved** — a prompt change inside
   this arm's own design, testable for ~$0.08.
4. ⭐ **`E6` is a defect-generating entry, measured twice.** Arm D and arm E, two
   different critics, produced the identical weakening on `l171_426_n022` by
   obeying it. It should carry E8's counter-intuitive warning or be dropped, and
   that is a change to the review list with two independent measurements behind
   it.
5. **The mechanical floor cannot referee any of this.** `l3147_3238_n003` came
   back `translated`, `repair_needed=False`, 0 breaches, 0 polarity mismatches —
   with two of three obligations deleted and the read-back left asserting them.
   Arm D's recommendation to *build detectors instead of instructions* survives
   this arm, with the correction that **the detectors this loop most needs do not
   exist yet**, and `checks.polarity_mismatches` scored 0 on the very draft whose
   `prefer` polarity was inverted three times.

---

## 8. LIMITS — read these before quoting any number

* ⚠️ **n = 13 of 17 clauses, 89 items, and the paired three-way cell is 6
  clauses / 27 items.** Every count is single-digit or low-double-digit. **No
  rate here is statistically separated from noise.**
* ⛔⛔ **THE LOSS IS NOT RANDOM AND IT CUTS AGAINST MY HEADLINE.** The 4 missing
  clauses are the 4 longest reasoners (29.5k–31.7k chars) and within the 13 that
  completed, longer reasoning tracks more FIX lines. **29% is plausibly an
  under-estimate**, exactly as arm D's 13% was.
* ⚠️ **The identified/repaired classification is MY adjudication** against the
  frozen `feedback_1.md` files. Items are counted as *identified* when a FIX line
  names the field and the change the frozen item demands; partial matches are
  noted per clause in §2–§3 and I have flagged where I chose the conservative
  reading. Another adjudicator could move several single cells; the 15% → 37%
  paired gap survives several cells of movement, the 30% T3 threshold does not.
* ⚠️ **Item counting is coarse.** `l2821_3040_n017` (17 items) and
  `l1368_1541_n019` (11) dominate the denominator. Excluding both: 61 items, 20
  identified (**33%**) — the shape does not change.
* ⚠️ **The critic call is not production.** Format forcing off, `max_tokens`
  7,168 not 4,096. It produced no module; the repair call ran under production's
  exact `response_format` and `max_tokens`.
* ⚠️ **One critic→repair cycle only.** The Opus loop converged in 2–4 turns; arm
  E could not afford a second cycle, so *turns to convergence* is unmeasurable
  here and **0 of 13 converged in one cycle** against the Opus critic's **6 of
  17**. A second cycle might close some of that; this arm cannot say.
* ⚠️ **Eleven entries, not twenty** — same surface as arm D, not the same as
  arms B/C.
* ⚠️ **The review list is in-sample**, distilled from the Opus loop's findings
  over these very clauses. Arm D held the identical advantage, so the D-vs-E
  contrast is unaffected; the *absolute* 29% is flattered.
* ⚠️ **CONTAMINATION, as disclosed in `PREREG.md` §9.** I had read arm D's
  PREREG and RESULT in full and knew the E1/E10 cases by name before designing
  this arm. The structural mitigation that carries the headline: **the defect list
  is the frozen `feedback_1.md` files, authored by the Opus critic before either
  arm existed**, and the mechanical table is computed by imported code published
  for prior arms.
* ⛔ **Nothing was tuned after results were seen.** `messages/`, `promptsE/` and
  `config_arme.json` are byte-unchanged since the first live call. No second
  variant was run. Neither result is softened: the identification lift is real
  and the harm is real.

---

**Adjudicated span-first, floor first, against a defect list frozen before the
arm existed. — adjudicator, 2026-08-16**
