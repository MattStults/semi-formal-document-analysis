# RESULT — ARM F: banning the disjunction does NOT fix the cheap critic

**Answer: the pre-registered NULL fires in both cells. The ban took effect
completely — every remedy-branch disappeared — and `asserts` still FELL in both
cells, exactly as `PREREG.md` §7/P-1 said would constitute a null. ⭐ The coin
flip moved inside the critic. Adding `PRESERVE` changed the KIND of failure
rather than removing it, and that change is the arm's one positive finding: F2
preserved the content and produced a module the mechanical floor could SEE was
broken, where arm E and F1 both produced silent semantic damage that every check
passed.**

⛔ **Read the limits first, not last.** The disjunction ban made the critic reason
~1.3× longer and **10 of 17 F1 calls and 11 of 17 F2 calls were lost to
truncation.** F1 delivered **5** modules, F2 **6**, against arm E's 13, and the
three-way paired intersection is **3 clauses / 18 items.** Every cell here is
single digit. **No rate in this document is statistically separated from
anything.** The two findings that survive that are (i) the `asserts` sign, which
is the same in both cells and driven by a case examined in full, and (ii) the
`l3147_3238_n003` case series, which needs no rate.

**Pre-registration:** `PREREG.md`, signed before the first call.
**Rulings:** `RULING_01_no_retry.md` (the cap is not raised),
`RULING_02_blind_broken.md` (the blinding protocol FAILED; here is what replaced
it). **Spend of record: $0.15999** against a **$0.25** cap, both cells,
reconciled against `usage.jsonl`.

---

## 0. WHAT WAS SENT, AND WHAT WAS VERIFIED BEFORE SENDING

| gate | value |
|---|---|
| system block | 39,959 chars, sha256 `3a66c5f5…4c34c` |
| **equal to arm A's recorded sha** | ✅ `run_armf.py` refuses to send otherwise |
| the four prompt files | byte-identical copies of arm E's: `0463449d`, `92dbd355`, `a0c12943`, `7a88183e` |
| turn-1 user blocks rebuilt vs arm A's stored transcripts | **17 of 17 byte-identical**, gated per clause |
| turn-1 assistant drafts | **arm A's own**, resumed, not re-drawn |
| ⭐ review list (11 entries + 3 anti-rules), **both cells** | **byte-identical to arm E's**, tail sha256 `39fcb552…0ac4b8d`, gated |
| **E6 present and unmodified in both cells** | ✅ held fixed on purpose; firings counted, §6 |

⛔ Nothing outside `_debug_gen11/ds_critic_format_arm/` was written. No git was
run, no commit made, no branch switched. `loop.py` was **not** touched — the
ledger hole is measured, not fixed (`PREREG.md` §6).

⚠️ **Two files in the tree were modified by other work in this session and I did
not act on them:** `walkthrough/paper_pipeline/phase_1/checks.py` (mtime 12:09,
hours before this arm ran) and `resolve_runs/graph_v2/EXPERIMENTS.md`. **The
`checks.py` change matters and is disclosed:** it adds an `_AVOIDANCE_ACT`
exemption to `polarity_mismatches`, on exactly the `l4252_4482_n016` construction
this arm reports. Every polarity figure below — arm E's included, since arm E
also ran after 12:09 — is computed with that patch in place, so the cells are
consistent with each other but **`polarity = 0` throughout is partly the
patch, not only the modules.**

### The one thing that differs between the cells

Both cells are arm E with the reply contract changed and nothing else.

* **F1 (ban)** adds one bullet: *"COMMIT TO ONE EDIT. No alternatives … A line
  that hands the author a choice is a failed line, and the author will take the
  cheapest branch."*
* **F2 (ban + preserve)** adds that bullet **and** requires every FIX line to end
  `PRESERVE: <what this edit must not destroy>`.

⚠️ **Departure from arm E, disclosed:** critic `max_tokens` **8,192**, uniform
across both cells, against arm E's 7,168. F-vs-E truncation rates are therefore
not like-for-like; the reasoning-length distributions are.

---

# ⭐ TIER 1 — THE ADJUDICATION-FREE MEASURES

**No judgment of mine enters anything in this section.** Computed by
`arms_review/floor.py`, `arms_review/measures.py` and
`licence_control/measure.py` — imported, not reimplemented — plus the two
mechanically checkable classes the blind independent review enumerated.
`PREREG.md` §3 put this section first before any result existed, and
`RULING_02` is the reason it now carries the whole headline.

## 1.1 ⭐⭐ THE `asserts` SIGN — the pre-registered headline

Each cell against **its own clauses' turn-1 drafts**, so every row is a
before/after on the same modules.

| loop | n | turn-1 `asserts` | post `asserts` | **Δ** |
|---|---:|---:|---:|---|
| **arm A — OPUS critic, ONE round** | 13 | 24 | **28** | **+4** ⭐ |
| **arm E — cheap critic, no ban** | 13 | 24 | **18** | **−6** |
| **F1 — cheap critic, BAN** | 5 | 11 | **9** | **−2** |
| **F2 — cheap critic, BAN + PRESERVE** | 6 | 17 | **15** | **−2** |

⛔ **N1 FIRES IN BOTH CELLS. `PREREG.md` §7 defined the null as `asserts` staying
flat or falling under the ban, and it fell in both.** The frontier critic's loop
adds normative content; every cheap-critic loop tested, banned or not, removes
it. **The sign did not move.**

⭐ **AND THE LOSS IS ONE CLAUSE, IN BOTH CELLS.** Every deleted assert in F1 and
in F2 comes from `l3147_3238_n003` (3 → 1 in each). Remove that clause and
neither cell deletes anything. Arm E deleted on **three** of its 13
(`l3147` 3→1, `l1_170_n056` 4→1, `l3239_3382_n002` 3→2). ⚠️ **Arm E's other two
deletion clauses truncated in BOTH F cells, so arm F cannot say whether the ban
would have saved them.** Per-clause deletion rates — armE 3/13, F1 1/5, F2 1/6 —
are not separated from each other at these counts and are not claimed to be.

## 1.2 The full mechanical table

Each cell restricted to its own clauses, turn-1 → post.

| set | n | `floor_clean` | `errors` | `asserts` | selfcited/requires | polarity | bodiless | class B | class C |
|---|---:|---|---|---|---|---:|---:|---:|---:|
| **F1** turn-1 → post | 5 | 5 → **5** | 0 → **0** | 11 → **9** | 7/7 → 7/7 | 0 → 0 | 0 → 0 | 7 → **7** | 7 → **7** |
| **F2** turn-1 → post | 6 | 3 → **2** | 8 → **6** | 17 → **15** | 9/9 → 8/9 | 0 → 0 | 0 → 0 | — → **4** | — → **7** |
| **arm E** turn-1 → post | 13 | 8 → **8** | 14 → **9** | 24 → **18** | 19/20 → 19/20 | 0 → 0 | 0 → 0 | — → **17** | — → **13** |
| arm A turn-2 (OPUS, 1 rd) | 17 | 10 → **15** | 18 → **7** | 34 → **38** | 25/26 → 20/24 | 0 | 0→1 | 22 | 18 |
| arm A final (OPUS gold) | 17 | 10 → **17** | 18 → **0** | 34 → **33** | 25/26 → 20/23 | 0 | 1 | 32 | 18 |

⛔ **B7, the MEASURED noise floor** (`arm_aprime`): a byte-identical re-draw moves
error count on **7 of 17** clauses and `floor_clean` on **3 of 17**. **Every
mechanical movement in the F rows is inside that band and is reported as noise**,
however it points. At n=5 and n=6 that is not a caveat, it is the whole reading.

* **`floor_clean`: F1 5→5, F2 3→2, arm E 8→8**, against the Opus critic's 10→15
  over 17. **No cheap-critic cell moved the floor.** F2's single loss is
  `l3147_3238_n003` and is discussed in §3 — it is the *good* kind of failure.
* **Self-cited borrowed glosses unmoved everywhere.** P-f-equivalent holds: only
  heavy interventions (worked examples 3/24, decomposition 3/21) have moved that
  class and a critique turn is not one.
* **Class B / class C (the independent review's mechanical classes) are flat**
  in F1 (7→7, 7→7). ⚠️ **ARTIFACT MISMATCH, as `PREREG.md` §3 required me to
  state wherever these are used:** the independent review computed its counts
  (32 class-B instances, 18 class-C, over 12–14 of 17 modules) on the
  **CONVERGED** modules, not the turn-1 drafts arm F starts from. **Its counts
  are not a baseline for arm F.** Only its two checks are borrowed, recomputed
  here on every set in the table so the comparison is internal to this file.
  Read that way, the finding is: **no cheap-critic loop, banned or not, touches
  the licence-inheritance class at all** — and neither does the Opus gold, whose
  class-B count is the highest in the table (32).

## 1.3 ⭐ THE MANIPULATION CHECK — the instruction took, completely

⛔ **Stated as `PREREG.md` §3 requires: this is a manipulation check. It tells us
the instruction took effect and NOTHING MORE. It is not a result.**

| cell | clauses | FIX lines | **branch lines (regex)** | **branch lines (manual read of every line)** | `PRESERVE:` |
|---|---:|---:|---|---|---|
| **arm E** | 13 | 39 | 9 narrow / **11 wide** | **11 (28%)** | 0 |
| **F1** | 7 | 10 | **0** | **0** | 0 |
| **F2** | 6 | 12 | 0 / 1 | **0** | **12 (100%)** |
| Opus `feedback_1`, all 17 files | 17 | 346 prose lines | 1 | **0** (the single regex hit is *"either `interactive` or `programmatic`"* — an argument's value, not a remedy choice) | — |

* ⭐ **M1 PASSES, and passes under manual review, not only regex.** I read every
  FIX line in the pool containing the word "or". **Every remedy-branch in the
  entire pool is arm E's; F1 and F2 contain none.** The three F-cell "or" hits
  are the word inside a gloss being defined.
* **The regex under-counts and I am reporting that**: `remove the entry or give
  it a meaningful body` (arm E, `l1707_1973_n022`) is a genuine branch that both
  the narrow and wide predicates missed. The manual count is the one to quote.
* ⭐ **The manual count reproduces arm E's published 11 of 39 exactly.**
* **M2 PASSES at 100%** — every F2 FIX line carries a `PRESERVE:` clause. F2 is a
  full dose, not a partial one.

⭐ **So the trap `PREREG.md` §3 was built to catch is exactly what happened: the
branches went to zero and `asserts` still fell. Branch count reads as a clean
success while §1.1 says the loop still deletes. That is why it is not the
headline.**

## 1.4 ⛔ THE BAN'S UNPRICED COST: it eats the sample

| | arm E (7,168, no ban) | **F1 (8,192, ban)** | **F2 (8,192, ban+preserve)** |
|---|---|---|---|
| reasoning chars, completed calls | 8,464 – 31,723 | \| **12,257 – 38,452 across both F cells** \| |
| **calls truncated** | **4 of 17 (24%)** | **10 of 17 (59%)** | **11 of 17 (65%)** |
| modules delivered | **13** | **5** | **6** |
| `reasoning_chars` discriminator | 17/17 unforced > 0 | **34/34 unforced > 0; 11/11 forced exactly 0** |

⭐ **A critic told to commit to one remedy has strictly more work to do than one
allowed to write "either X or delete Y". The disjunction was not only a defect in
the output — it was a SHORTCUT IN THE REASONING**, and removing it costs enough
thinking to lose most of the sample at a cap that was already 1.14× arm E's.

⛔ **The cap was NOT raised and no clause was retried** (`RULING_01`, with
*retry the truncated clauses at 12,288* and *re-run all 17 uniformly* rejected by
name). **The lost clauses are the ones the critic worked hardest on, so both F
cells' identification figures are under-estimates, and the bias points the same
way it did in arms D and E.**

⚠️ **This alone probably disqualifies the ban as written.** Cost per delivered
module: **arm E $0.0064, F1 ≈ $0.0159, F2 ≈ $0.0134** — 2.1–2.5×, for a loop
whose `asserts` sign did not change.

---

# ⚠️ TIER 2 — THE ADJUDICATED MEASURES

**Every number below rests on a judgment of mine.** `PREREG.md` §4 froze the key
and the criteria before the first call; `RULING_02` records that the blinding
half of that protocol failed.

## 2.1 ⛔ THE BLINDING PROTOCOL FAILED — reported here, not buried

`PREREG.md` §4.2 committed to scoring identification from a pool with cell labels
stripped, and disclosed in advance that four arm-E replies were already known to
me. **In the event I read F1's five extracted FIX lists while F2 was running, and
F2's while its repair phase was pending.** The pool, the seeded opaque ids and
the sealed map were all built and are on disk and did their mechanical job.
**What they could not survive is that a single agent drove the live run and read
its outputs. Blind scoring and run operation cannot be the same seat.** That is a
finding about the METHOD and it is stated at full strength.

⭐ **What replaced it.** `key/frozen_key.json` — **164 items across all 17
clauses, sha256 `16965c45…af45aa6`, written and hashed before the first API
call** — carries per-item `anchors`: token groups that define a purely mechanical
match. **The prefilter rate involves no judgment of mine at any point and cannot
be bent toward a cell without editing a hashed file.** It is coarse in both
directions (it counts a line naming the right field with the wrong change; it
misses a correct finding phrased around the anchors — one measured instance,
arm E on `l1707_1973_n006`). **Both numbers are reported for all three cells.**

## 2.2 ⭐ THE ARM-E RE-SCORE — required by the amendment, and it moves

| | arm E's own published figure | **my re-score, arm F's frozen key** |
|---|---|---|
| identification, arm E's own 13 clauses | **29%** (26 of 89) | **21.1%** (19 of 90) |
| repair \| identification | **≈62%** | **57.9%** (11 of 19) |
| adjudication-free prefilter, same clauses | — | **32.2%** (29 of 90) |

⭐⭐ **P-6 IS WRONG AND THIS IS A FINDING ABOUT THE MEASUREMENT, NOT ABOUT ARM E'S
CELLS.** I predicted my re-score would land within 5 points of arm E's paired
37%. Against its own-sample 29% I am **8 points lower**, and against the key's
strictest reading the gap is entirely in *what counts as naming the change*.

The three clauses that move it, quoted so the disagreement is checkable:

* **`l2821_3040_n017`** — arm E scored 3 identified; my key scores **1**. Its
  critic wrote *"Remove 'rather than quantified measures' from the gloss"*, which
  is half of frozen edit 9; the frozen edit's other half — *rewrite the gloss so
  it describes a RESPONSE and not an assistant* — is the whole point of that
  module's structural defect, and the critic never reaches it.
* **`l1001_1107_n005`** — arm E scored 3; my key scores **2**. Naming
  `protect_privacy_heading` inside a proposed atom is not the same as saying the
  `protect_privacy_heading` **concepts entry must be deleted**.
* **`l3596_3876_n009`** — arm E scored 1; my key scores **0**, and the reason is
  worth more than the cell: the critic wrote *"replace"* where entry E1 of its
  own review list says in bold **"Do not *replace* a gloss to satisfy this —
  **add** to it. A gloss rewritten to state argument order and nothing else is
  worse than the one it replaced."** ⛔ **arm E's critic AND F2's critic both
  prescribed the replacement their own list forbids, and both repairs performed
  it, destroying the original sentence.** That is two independent violations of
  an explicit instruction, in the direction the instruction warns about.

⛔ **The honest conclusion: arm E's 29%/37% is soft by roughly 8 points under a
key whose criteria were fixed in advance, and arm E said so itself
("another adjudicator could move several single cells"). The direction of the
correction is DOWN.** It does not overturn arm E's qualitative finding — a peer
critic still identifies more than self-review's 13% — but the headline number
should be quoted as **~21–29% depending on strictness**, never as 37% alone.

## 2.3 THE CELLS, side by side with arm D and arm E

⚠️ **Every column is adjudicated except the prefilter column. All four cells are
different clause samples — see §2.4 for the only paired reading.**

| | arm D self-review | **arm E peer, no ban** | **F1 ban** | **F2 ban + preserve** | arm A Opus |
|---|---|---|---|---|---|
| clauses delivered | 9 | 13 | **5** | **6** | 17 |
| frozen items | 91 | 90 | **48** | **68** | — |
| **identified (adjudicated)** | 13% | **21.1%** (19) | **8.3%** (4) | **8.8%** (6) | authored |
| ⭐ **identified (PREFILTER, adjudication-free)** | — | **32.2%** (29) | **14.6%** (7) | **22.1%** (15) | — |
| **repaired** | 12% | **12.2%** (11) | **8.3%** (4) | **5.9%** (4) | ~100% |
| ⭐ **repair \| identification** | **92%** | **57.9%** | **100%** (4/4) | **66.7%** (4/6) | 100+/100+ |
| false charges | — | 2 | **1** | **2** | — |
| FIX lines per clause | 2.6 | 3.0 | **1.4** | **2.0** | — |

⛔ **N3 does not fire in F1 and DOES fire in F2.** F1's repair-conditional-on-
identification is 4 of 4; F2's is 4 of 6. ⚠️ **Four for four is not evidence of
anything at n=4** and is not claimed as such; T3 is scored as *not assessable*
rather than passed.

⛔ **THE COST OF THE BAN THAT NOBODY PRE-REGISTERED: the critic stops charging.**
FIX lines per clause fall from arm E's 3.0 to **1.4 in F1**, and **2 of F1's 7
completed critics returned eleven PASSes and nothing else.** Identification falls
on both instruments in both cells. **P-3 — "identification does NOT fall" — is
WRONG.** A critic forbidden to hedge appears to resolve its uncertainty by
staying silent, and that is a worse trade than the branch it was forbidden.

## 2.4 The only strictly paired reading: 3 clauses, 18 items

`l1707_1973_n022`, `l3147_3238_n003`, `l3596_3876_n009` — the clauses all three
cells completed.

| | identified (adjudicated) | identified (prefilter) | repaired |
|---|---|---|---|
| **arm E** | 2 / 18 | **4 / 18** | 1 |
| **F1** | 1 / 18 | **2 / 18** | 1 |
| **F2** | 2 / 18 | **4 / 18** | 2 |

⛔ **Three clauses cannot support a rate and I am not reporting one.** This is a
case series and §3 is the only thing in it worth quoting.

---

## 3. ⛔ THE NAMED CASE — `l3147_3238_n003`, and it decides the arm

The clause: *"If the assistant lacks sufficient confidence … it should use a tool
to gather more information, hedge its answer appropriately, **or** explain that
it can't give a confident answer."* The Opus critic's frozen feedback requires
**one obligation discharged by any of the three, with the three named responses
individually visible**, and forbids the two obvious wrong answers by name: three
obliges on one body, and *"a single obligation on one opaque
'respond-adequately' predicate with the three specific responses named nowhere —
that is a hollow stub."*

| | did the critic FIND it? | what the repair produced | do all three survive? | floor |
|---|---|---|---|---|
| **turn-1 draft** | — | 3 × `oblige` on one body | yes, but conjoined | `translated`, clean |
| **arm E** | ✅ *"one act over a disjunction, since satisfying one disjunct … satisfies the span"* | kept `use_tool` only; read-back still recites all three | ⛔ **NO — 2 of 3 deleted** | `translated`, **0 breaches** |
| **F1 (ban)** | ⛔ **NO** — *"replace the three `oblige` entries with a single `oblige` on `respond_appropriately_when_uncertain(R)`"*: no disjunction, no alternation, no preservation | one opaque act, **`ontology` empty**, `acts` reduced to that one name, read-back collapsed to *"it should respond appropriately when uncertain"* | ⛔ **NO — all 3 deleted** | `translated`, **0 breaches** |
| **F2 (ban+preserve)** | ✅ *"…add an ontology rule defining that act as the disjunction of the three acts. **PRESERVE: the obligation that at least one of the three actions be taken**"* | one act `handle_low_confidence(R)`, **`ontology` body `use_tool_to_gather_info(R); hedge_answer(R); explain_cannot_answer_confidently(R)`** | ⭐ **YES — all three named and visible** | ⛔ **`invalid`, 3 breaches** |
| Opus gold, for reference | — | one act `respond_to_low_confidence(R)`, **three `ontology` entries, same head, different bodies**, three concepts | ✅ | `translated`, clean |

⭐⭐ **THIS IS THE ARM'S RESULT.**

1. ⛔ **The ban DESTROYED the diagnosis here.** Arm E's critic wrote the correct
   finding with the correct rationale. F1's, forbidden to offer an alternative,
   committed to the single remedy the Opus feedback names as the wrong one — and
   never mentioned that the three are alternatives at all. **The prefilter, which
   is adjudication-free, scores it 0 as well: the two instruments agree.**
   P-1 and P-4 both hold, and this is the sharpest evidence for them.
2. ⛔ **F1's output is WORSE than arm E's.** Arm E kept one real, named
   obligation. F1 kept none: `use_tool_to_gather_info`, `hedge_answer` and
   `explain_cannot_answer_confidently` are gone from `acts`, from `asserts`, from
   `ontology` and from `concepts`. The module now says *"respond appropriately"*
   — a tautology — and **the floor returns `translated`, `repair_needed=False`,
   0 breaches, 0 polarity mismatches. Nothing mechanical sees it.**
3. ⭐ **`PRESERVE` WORKED, and produced a LOUD failure instead of a silent one.**
   F2's constraint carried the alternation into the edit list; the drafter kept
   all three named responses; and it then wrote them with `;` between literals —
   the construction the Opus feedback forbids in the same paragraph — leaving
   three predicates undeclared. **The module is `invalid` with 3 breaches and the
   mechanical floor catches it.** F2 is the only cell of the three whose
   `l3147` failure is visible to a check.

⭐ **The generalisation, stated as INFERRED, not measured (n=1 per cell):** the
`PRESERVE` field does not make the cheap critic prescribe correctly. What it does
is **stop the repair from silently discarding content, so the remaining error
becomes a SCHEMA error rather than a semantic one — and schema errors are the
kind this pipeline can already detect.** For a loop whose measured failure mode
is invisible deletion, converting silent damage into a loud breach is worth more
than it looks. **It is one clause. It should be replicated before anyone builds
on it.**

---

## 4. SCORED AGAINST THE PRE-REGISTRATION

| branch | threshold | **F1** | **F2** |
|---|---|---|---|
| ⛔ **N1** `asserts` flat or falling | the null | **FIRES** (11→9) | **FIRES** (17→15) |
| **N2** ≥3 modules acquire a conclusion-changing defect | ≥3 of the sample | 1 of 5 — **does not fire** ⚠️ n=5 | 2 of 6 — **does not fire** ⚠️ n=6 |
| **N3** repair \| ID ≤70% | the null | 100% (4/4) — **does not fire**, n=4 | 67% — **FIRES** |
| **T1** `asserts` RISES | transfer | ❌ | ❌ |
| **T2** ≤2 conclusion-changing defects | transfer | ✅ (1) | ✅ (2) |
| **T3** repair \| ID ≥80% | transfer | **not assessable** (n=4) | ❌ |
| **T4** F2 beats F1 on `asserts` Δ and defects | F2 only | — | ❌ (Δ tied at −2; defects 2 vs 1) |
| **M1** branch lines ≤5% | manipulation check | ✅ **0%** | ✅ **0%** |
| **M2** ≥90% of F2 lines carry PRESERVE | manipulation check | — | ✅ **100%** |
| **H1** ≥3 acquire a conclusion-changing defect | harm | ❌ (1 of 5) | ❌ (2 of 6) |
| **H2** defect from correctly obeying an entry | harm | **FIRES** (E11 on `l3147`) | **FIRES** (E1 on `l3596`, E8 on `l2474`) |
| **H3** ≥3 clean floors fail after | harm | ❌ (0) | ❌ (1 — `l3147`) |
| **H4** anti-rule violated in repair | harm | ❌ **0** ⭐ | **FIRES** (1 — `l3596` gloss replaced) |
| **H5** ≥25% false charges | harm | ❌ (1 of 10) | ❌ (2 of 12) |
| **H6** PRESERVE clause violated by its own repair | F2 only | — | ❌ **0 of 12** |

### ⛔ VERDICT ON THE PRE-REGISTERED QUESTION

**N1 fires in both cells. `PREREG.md` §7 named it "the decisive one" and
"the single most informative outcome available in this arm, and the one I have
most reason to fear". It happened. The disjunction ban does not work.**

### Harm findings that need saying plainly

* ⭐ **H4 did NOT fire in F1, and that is F1's one clean win.** On
  `l4252_4482_n016` — the polarity clause — F1 renamed all three acts to the
  avoidance, kept `prefer`, kept every body, and **left all three read-backs
  word for word**, which is exactly what the frozen edit demands
  (*"Keep every read-back word for word — they are already correct and must not
  be touched"*). **Arm E rewrote all three read-backs on the same clause and that
  was its anti-rule violation.** A one-edit committed instruction did the job a
  branching one botched.
* ⛔ **H6 did not fire, but F2 found a failure mode H6 was not written for.** On
  `l2474_2554_n004` the FIX line read: *"add a body condition to the `forbid` for
  `deceive(A)` to exclude cases where `lie_by_omission(A)` and
  `aligns_with_social_norms(A)` hold … **PRESERVE: the permit rule for aligned
  lies of omission**"*. The `PRESERVE` clause was honoured exactly — and the edit
  **narrowed a prohibition**, which is entry E8's explicitly dangerous direction.
  ⭐ **The constraint protected the right thing and the wrong thing was destroyed
  anyway, because the critic named a PERMISSION to preserve while its edit
  weakened a PROHIBITION.** A `PRESERVE` field is only as good as the critic's
  choice of what to name, and that choice is the same faculty the ban was
  supposed to fix.

### Predictions

* **P-1 ✅ — the headline prediction, and it held.** M1 passed at 0% and `asserts`
  fell anyway, in both cells. The coin flip moved inside the critic.
* **P-2 ❌** — F2 did not beat F1 on `asserts` Δ; both are −2, both from the same
  clause.
* **P-3 ❌ — and it is the miss that matters most for anyone tempted to try this
  again.** I predicted identification would not fall. It fell on **both**
  instruments in **both** cells (prefilter 32% → 15% / 22%). **Forbidding the
  hedge does not make the critic decide; it makes it go quiet.**
* **P-4 ✅** — `l3147_3238_n003` lost its obligations again, in F1, worse than in
  arm E. F2 preserved all three, which `PREREG.md` named in advance as *"the
  single strongest evidence in the arm for the PRESERVE field"* — and it is,
  with the caveat that the module it produced does not validate.
* **P-5 — UNTESTABLE.** `l171_426_n022` truncated in **both** F cells. **E6's
  defect generation could not be retested and this arm adds no third
  measurement.**
* **P-6 ❌ — the most consequential miss.** See §2.2. My re-score is 8 points
  below arm E's own figure.
* **P-7 ❌, badly.** I predicted ≤3 truncations of 17 per cell at 8,192. Measured
  **10 and 11**. See `RULING_01`.

## 5. E6 — held fixed on purpose, and what it did

⛔ `PREREG.md` §2 kept entry **E6** byte-identical despite it being a measured
defect generator, because pulling it would have added a second variable.
Firings, as promised:

| cell | E6 FIX lines | on `l171_426_n022` (the measured harm clause) |
|---|---:|---|
| arm E | **7** of 39 | ✅ fired, produced the weakening again |
| **F1** | **1** of 10 | ⛔ **clause truncated — not testable** |
| **F2** | **0** of 12 | ⛔ **clause truncated — not testable** |

⭐ **E6's firing rate collapses under the ban (18% → 10% → 0%), which is
consistent with §2.3's general finding that the banned critic charges less — not
with E6 being fixed.** ⛔ **The `l171_426_n022` reproduction could not be
attempted in either cell. E6 still stands on two independent measurements
(arms D and E), not three. A list-repair arm remains the right experiment and
arm F does not substitute for it.**

## 6. SPEND, TRUNCATION, AND THE LEDGER HOLE

**Spend of record $0.15999**, cap **$0.25 across both cells**, reconciled
(`reconcile.json`). ⛔ **`loop.py` was NOT modified.**

| | value |
|---|---|
| **on disk (`out_f1/`, `out_f2/` records)** | **$0.06933** |
| ⭐ **of record (`usage.jsonl`)** | **$0.15999** |
| ⛔ **the difference — THE MEASURED HOLE** | **$0.09066** |
| rows in the window | **45**, **all 45 attributed to arm F by prompt shape, 0 unattributed** |
| rows raised after billing | **21** (10 F1-critic + 11 F2-critic truncations), **$0.09066** — the hole exactly |

Every row attributed:

| phase | calls | raised | recorded on disk |
|---|---:|---:|---:|
| `out_f1/critic` | 17 | **10** | $0.026756 |
| `out_f1/repair` | 5 | 0 | $0.009495 |
| `out_f2/critic` | 17 | **11** | $0.021137 |
| `out_f2/repair` | 6 | 0 | $0.011941 |
| | **45** | **21** | **$0.069329** |

⛔⛔ **57% of this arm's spend bought nothing.** `translate.Client._log_usage`
runs before `_check_envelope`, so a truncated completion is billed and then
raises with no turn record. It hid 36% of arm D's spend and 19% of arm E's;
**here it hid 57%.** The proportion scales with the truncation rate, which the
intervention itself raised. **Any arm that makes the model think harder must
reconcile against `usage.jsonl` or it will under-report its cost by more than
half.**

⭐ The `reasoning_chars` discriminator replicates again: **34/34 unforced calls
emit > 0 (12,257–38,452); 11/11 forced calls emit exactly 0.** Running totals
are now **213/213 forced at zero, 115/115 unforced above it.**

## 7. VERDICT

⛔ **A non-disjunctive cheap critic is NOT usable, and arm F is a clean null on
the intervention it was built to test.**

1. ⭐ **The mechanism arm E identified was real, and fixing it fixed nothing.**
   The branch lines went from 28% to 0% under manual review, in both cells, and
   `asserts` fell in both anyway. **The disjunction was a symptom. The disease is
   the cheap critic's remedy selection, and forcing it to commit does not improve
   it — on the arm's one fully examined case it made it commit to the wrong
   remedy the frontier critic forbids by name.**
2. ⛔ **The ban has an unpriced cost that is larger than any effect it had.** It
   raises reasoning ~1.3×, cost **59–65% of both samples** to truncation, cut FIX
   lines per clause from 3.0 to 1.4, and roughly **doubled the cost per delivered
   module**. A critic forbidden to hedge goes quiet rather than deciding.
3. ⭐ **`PRESERVE` is the one thing here worth another experiment, and not for the
   reason it was proposed.** It did not make the critic prescribe correctly. On
   `l3147_3238_n003` it stopped the repair from discarding content, and the
   defect that remained was a **schema breach the existing floor caught** —
   converting the pipeline's worst failure mode (silent semantic deletion behind
   a clean floor) into its most tractable one. **n = 1. Replicate before
   believing.**
4. ⛔ **Arm E's headline number needs correcting downward.** Under a key fixed
   before the first call, arm E's identification is **21%**, not 29%, and
   `repair | ID` is **58%**, not 62%. Arm E's qualitative conclusion survives;
   its number should be quoted as a range.
5. ⛔ **The blinding protocol failed and the fix is structural, not a promise.**
   One agent cannot both operate a live run and be blind to its outputs.
   **The instruments that survived — the hashed anchor prefilter and the imported
   Tier-1 code — are the ones that require no seat discipline at all.** Any future
   arm making an adjudicated claim should either hand scoring to a separate seat
   or restrict itself to what those two can measure.
6. **The mechanical floor still cannot referee this.** F1's `l3147` came back
   `translated`, `repair_needed=False`, 0 breaches, 0 polarity mismatches, with
   **all three** named obligations replaced by a tautology. Arm D's and arm E's
   recommendation — build detectors, not instructions — survives arm F intact.

## 8. LIMITS — read these before quoting any number

* ⛔⛔ **n = 5 (F1) and 6 (F2) delivered modules; the three-way paired set is 3
  clauses / 18 items.** Every cell is single digit. **Nothing here is
  statistically separated from anything.** The `asserts` sign and the
  `l3147_3238_n003` case series are the only findings that do not depend on a
  rate, and they are what the verdict rests on.
* ⛔ **THE LOSS IS NOT RANDOM AND IT CUTS AGAINST BOTH CELLS.** 10 and 11 of 17
  calls truncated, and the truncated calls are the longest reasoners — the
  clauses the ban made the critic work hardest on. **Both cells' identification
  figures are under-estimates.** `RULING_01` records why no clause was retried
  and names the rejected alternatives.
* ⛔ **The two arm-E harm clauses that would have tested the ban hardest
  (`l171_426_n022`, `l3239_3382_n002`, plus `l4252_4482_n005`) truncated in BOTH
  cells.** The ban is untested on the three clauses where arm E's branch-taking
  did its worst damage. This is the single biggest gap in the arm.
* ⛔ **The blinding protocol failed** (`RULING_02`). Adjudicated identification
  figures were produced by a scorer who knew each reply's cell. The prefilter
  column does not have this defect and is the one to quote in any cross-cell
  comparison.
* ⚠️ **8,192 ≠ arm E's 7,168.** F-vs-E truncation is not like-for-like.
* ⚠️ **My frozen key's denominators differ from arm E's** on
  `l3147_3238_n003` (4 vs 3) and, through a stricter inclusion rule, on the
  interpretation of several multi-part edits (§2.2). All three cells are scored
  by ONE key, so the cross-cell comparison is internally consistent; the
  comparison to arm E's *published* figures is not, and both are given.
* ⚠️ **`checks.py` was modified by other work at 12:09 today**, in a way that
  directly affects `polarity_mismatches` on `l4252_4482_n016`. All cells here and
  arm E ran after it, so they are mutually consistent, but `polarity = 0` is not
  independent of that patch.
* ⚠️ **One critic→repair cycle only.** Turns-to-convergence **cannot** be compared
  against the Opus critic's 6 of 17, and **0 of 5 / 0 of 6 converged in one
  cycle.** A second cycle might close some of it; this arm cannot say.
* ⚠️ **The review list is in-sample**, distilled from the Opus loop's findings
  over these very clauses. All cells hold the identical advantage, so the
  cross-cell contrast is unaffected; the absolute rates are flattered.
* ⚠️ **F2's repair side is not regime-identical to the Opus loop's** — its edit
  lines carry the `PRESERVE` clause and are longer. F1's is.
* ⛔ **Nothing was tuned after results were seen.** `messages/`, `promptsF/`,
  `config_armf.json` and `key/` are byte-unchanged since the first live call. No
  third cell was run. Both cells are reported separately and neither result is
  softened: the ban failed, and the one thing that looked promising rests on a
  single clause.

---

**Adjudicated span-first, floor first, against a key frozen and hashed before the
first API call. Tier 1 leads because Tier 2's protocol broke.
— adjudicator, 2026-08-16**
