# PREREG — a TRIAGE instrument: can cheap pre-critic signals predict frontier-critic yield?

Signed before any predictor was joined to any outcome column.
Zero API spend. Every number below is recomputed from data already on disk.
No git was run, no branch switched, no commit made.

---

## 0. DECLARED BLINDNESS BREACH — read this first

I am **not** fully blind to the outcome column, and pretending otherwise would be the
first way to corrupt this result. Before writing this file I had already read, in the
course of finding out what data exists:

* `independent_review/01_verdicts.md` — the per-clause CONTENT/LICENCE verdicts **and**
  the revised standing (10 correct / 3 defective / 4 unsure), including the named clauses
  in each bucket.
* `independent_review/02_classes.md` — the four mechanical classes and their counts.
* `ds_critic_arm/RESULT.md` §2 — arm E's per-clause frozen / identified / repaired table.
* `selfreview_arm/RESULT.md` §2 — arm D's per-clause table.

I have **not** opened, and will not open until this file is signed:

* `reference_set/diffs.json` and `reference_set/CRITERIA.md` — the 25-clause transfer
  cohort. **This cohort is therefore genuinely out-of-sample for me**, and it is the only
  part of this analysis that carries an honest blindness claim.
* any per-clause join of a predictor to an outcome, on either cohort.

**What this costs.** Predictor selection on the 17 cannot be claimed as blind. A reader
should treat every in-sample number on the 17 as an upper bound that has had a human
prior applied to it, and should weight the reference-set transfer check accordingly —
which is the correct weighting anyway, and is why the transfer check is the deliverable
that matters.

**What I have done to limit it.** Every predictor below is justified from a **stated
mechanism, written here, before any join was computed**, and each mechanism is traceable
to a rule in the prompt (`00_task.md`), to a `REVIEW_LIST.md` entry, or to the structure
of the decomposition graph — not to a correlation I noticed. Two of the six (BORROWED,
FLOORDIRTY) I would have written down from the mechanism alone with no outcome exposure
at all. The one I care most about (DISAGREE) is defined by a mechanism the task brief
handed me, not by anything I read.

---

## 1. THE QUESTION

A frontier (Opus) critic on 100% of clauses sets the price of the pipeline. A cheap
(DeepSeek) peer critic diagnoses roughly a third of what the frontier critic does and its
repairs sometimes delete normative content.

**Can we predict, from signals available BEFORE the frontier critic runs and at
effectively zero marginal cost, which clauses most need near-frontier feedback?**

A working instrument converts "frontier critic everywhere" into "cheap critic everywhere,
frontier critic on the top k%".

The instrument only has to be **monotone in yield**, not accurate. It is a ranker, not a
classifier. It is useful if the top-k by score contains materially more frontier-critic
yield than a random k.

---

## 2. OUTCOME COLUMNS, PRE-REGISTERED AND RANKED BY OBJECTIVITY

Per the coordinator's amendment: the outcome column is pre-registered too, and every
result below states which tier it stands on. A predictor that works on Tier 1 is worth
more than one that works on Tier 3 **independent of effect size**.

### Tier 1 — adjudication-free, recomputed here, not copied

| id | column | definition | why it is Tier 1 |
|---|---|---|---|
| **O1** | `FROZEN` | count of numbered edit lines in `ds_opus_loop/out/<id>.feedback_1.md`, matching `^\s*\d+\.\s`, **excluding** lines whose text begins "Leave " | counting numbered lines in a file. The *content* is frontier-authored — that is the thing being predicted — but no one re-adjudicates the count. Labelled **Tier 1-M**: mechanically counted, frontier-authored. |
| **O2** | `TURNS` | number of `feedback_*.md` files on disk for the clause | a file count. This is *literally the frontier-critic bill* for that clause: one feedback file is one frontier round. **This is the primary outcome.** |
| **O3** | `LICINH` | licence-inheritance instances, **recomputed by me**, not copied from the review: count of `ontology`/`asserts` entries stamped `licence:"textual"` whose `body` references a predicate the same module declares with `licence` in {`assumed`,`world`} | four lines of Python over the module JSON |
| **O4** | `SELFCITE` | borrowed `requires` names whose `concepts` entry is `licence:"textual", cites:<this node>`; via `measures.selfcited`, unmodified | existing shared measure |
| **O5** | `FLOORDIRTY_CONV` | `floor.py` on the CONVERGED module: not (`outcome=="translated"` and no breaches and no errors) | existing shared measure |

O3 and O4 are recomputed on **both** the turn-1 draft and the converged module. The
turn-1 value is a *predictor* (see §3); the converged value is an *outcome*. They must
never be crossed, and the code keeps them in separately named columns.

### ⚠️ AMENDMENT A1 — signed after the first join attempt, before any statistic was read

**Grounds.** `O1 (FROZEN)` as specified above assumed every `feedback_1.md` is a numbered
edit list. It is not. The frontier critic writes in **three formats**:

1. a numbered edit list (`Make these edits… 1. 2. 3.`),
2. prose ordinals (`Three edits. First: … Second: … Third: …`),
3. a check report (`attempt 1 failed these checks: [error/schema] … [error/faithfulness] …`).

The pre-registered regex sees only format 1, and silently returned `FROZEN = 0` for four
clauses (`l171_426_n022`, `l1_170_n056`, `l3147_3238_n003`, `l4252_4482_n016`) whose
feedback files are long and substantive. A zero there is not a measurement of low yield,
it is a parse failure, and using it would have inverted the outcome on exactly the clauses
the frontier critic worked hardest on.

**This amendment is a bug fix, not a re-specification after an unwelcome answer.** No
correlation, ranking or top-k number had been computed when it was written; the only thing
read was the four-zeros pattern and the raw text of the four files. Recorded here rather
than in the transcript so the record shows what changed and why.

**Retired.** `O1 (FROZEN)` is retired as a headline outcome. It is retained only as
`FROZEN_FMT1`, reported on the subset of clauses whose feedback is in format 1, and
explicitly marked format-restricted.

**Added, both Tier 1 and both format-independent** — they are file measurements that make
no assumption about how the critic chose to write:

| id | column | definition | why |
|---|---|---|---|
| **O1a** | `FB1_CHARS` | `len()` of `feedback_1.md` | how much the frontier critic had to say about the unaided draft |
| **O1b** | `FB_CHARS` | Σ `len()` over all `feedback_*.md` for the clause | **the frontier critic's total output volume on this clause — i.e. literally the bill.** This is the economically correct target and it replaces O1 as co-primary alongside O2. |

**Direction is unchanged for every predictor**: all six were pre-registered as pointing the
same way for "more frontier yield", and `FB_CHARS`/`TURNS` are more-yield-is-larger just as
`FROZEN` was. No predictor's predicted sign moves as a result of this amendment.

### Tier 2 — adjudicated, but blind and independent

| id | column | definition |
|---|---|---|
| **O6** | `IREV_NOTCORRECT` | 1 if the independent review's **revised** CONTENT verdict is DEFECTIVE or UNSURE, 0 if CORRECT |

One reader. It retracted three of its own findings after opening the critic's turns and
left four clauses UNSURE. Usable, and I will use it, but it is one person's judgement and
the UNSURE bucket (4 of 17) is larger than the DEFECTIVE bucket (3 of 17), which means the
binary is dominated by *the reader's uncertainty*, not by defect. **Any result on O6 is
reported as Tier 2 and is not allowed to carry the headline.**

### Tier 3 — adjudicated by an interested party

| id | column | definition |
|---|---|---|
| **O7** | `E_IDENT_RATE` | arm E's `identified / frozen` per clause |

Arm E adjudicated its own arm and conceded in its own RESULT that some cells would not
survive re-adjudication. **A predictor whose evidence rests only on O7 is a hypothesis,
and is labelled as one in RESULT.md.**

### Transfer cohort (semi-independent, different provenance)

| id | column | definition |
|---|---|---|
| **T1** | `REF_EDITED` | 1 if the clause carries ≥1 classified edit in `reference_set/diffs.json` |

25 clauses, 26 classified edits, 16 of 25 carry ≥1. Not opened before signing.

---

## 3. THE SIX CANDIDATE PREDICTORS

Cap of six, held. Each is stated with its **mechanism**, its **predicted direction**, its
**input tier**, and its **document-tunedness** — how much of it would survive swapping the
Model Spec for a different document.

Document-tunedness scale, stated before use:
* **NONE** — no document-specific term anywhere; would run unchanged on any document.
* **LOW** — English-general lexicon or graph-interface structure; the *values* shift on a
  new document but the *mechanism* does not.
* **MEDIUM** — depends on a lexicon or convention that is English-general but whose
  calibration is likely document-specific.
* **HIGH** — keyed to Model Spec phrasing. Worth much less at equal in-sample accuracy.

---

### ⭐ P1 — `DISAGREE`: two cheap critics disagree on the same draft

**Definition.** Arms D (self-review) and E (peer critic) each emit a PASS/FIX verdict on
each of the eleven review-list entries `E1..E11` for the same byte-identical turn-1 draft.
`DISAGREE` = the number of entries where exactly one of them says FIX.
Also recorded: `DISAGREE_FRAC` = `DISAGREE / 11`.

**Mechanism.** Two independent cheap reads of the same object. Where they agree, the
cheap model has a stable read and a frontier read is likely to be redundant. Where they
diverge, the draft sits at a decision boundary the cheap model cannot resolve from its own
resources — which is exactly where an additional, better read carries information. Arm E's
own finding supports the mechanism from the other side: arm D's misses on
`l4252_4482_n016` and `l3596_3876_n009` were **vantage effects, not reading-ceiling
effects** — a second cheap vantage recovered them. If a second cheap vantage recovers
*some* of the frontier's yield, then *where the two vantages fight* should mark the rest.

**Predicted direction.** More disagreement → more frontier-critic yield (higher O1, O2).

**Input tier: 1.** It is a diff between two files already on disk. No adjudication.

**Document-tunedness: NONE.** Contains no document term, no span feature, no lexicon and
no schema knowledge. It would transfer to a second document *for free* — and if it works,
the entire triage instrument is "run the cheap critic twice, escalate where they differ."
This is the highest-value candidate in the set and it is ranked first for that reason,
before any number was computed.

**Known limit, stated in advance:** arms D and E both completed only **6** of the 17
clauses. n=6 is not a test. It is a look. I am pre-committing to reporting it as a look.

---

### P2 — `BORROWED`: how many names the node header borrows

**Definition.** `|NEEDS|` — the number of names listed under NEEDS in the node header
(`corpus row['quote']`), i.e. concepts this module must take on trust from other nodes.
Parsed from the header, **not** from the module, so it is available before any draft
exists.

**Mechanism.** Every borrowed name is one opportunity for the manufactured-citation class:
the drafter must gloss a name it cannot see the definition of, and the CITATION
instruction permits only this node's own id, so the honest move (`assumed` + inference) is
one step further away than the dishonest one (`textual` + cites-self). A node with zero
borrowed names has **nothing to manufacture**. This is a structural pressure created by
the node interface, not by any particular wording.

**Predicted direction.** More borrowed names → more frontier yield, more SELFCITE, more
LICINH, more likely NOT-CORRECT.

**Input tier: 1.** Header parse.

**Document-tunedness: LOW.** The NEEDS block is an artifact of the decomposition graph,
which exists for any decomposed document. The count distribution would shift on a new
document (the decomposer is measured 82% document-tuned) but the mechanism — borrowed name
creates citation pressure — is a property of the interface, not of the Model Spec.

---

### P3 — `FLOORDIRTY_T1`: the unaided draft already fails the free mechanical checks

**Definition.** `floor.py` on `ds_opus_loop/out/<id>.turn1.raw.json`: 1 if NOT
(`outcome == "translated"` and zero schema breaches and zero error-severity findings).
Sub-columns kept: `T1_ERRORS`, `T1_BREACHES`.

**Mechanism.** The mechanical validator is free and runs today. If a drafter could not
satisfy the *easy, checkable* constraints on a clause, that is evidence the clause was hard
for it, and hardness should be correlated across the easy and the hard axis. This is the
cheapest possible signal — it costs one function call on an artifact we already have.

**Predicted direction.** Floor-dirty at turn 1 → more frontier yield.

**Input tier: 1.**

**Document-tunedness: NONE.** `checks.py` / `schema.py` are document-general by
construction; the project's own generalization census places the verifier on the
document-general side of the split.

⚠️ **Pre-registered caveat:** arm A′ measured the mechanical floor at **7/17 (41%)** under
an empty manipulation. `FLOORDIRTY_T1` is therefore a **noisy** predictor by measurement,
and any effect smaller than that floor is not an effect. I am writing this down before
seeing the number so I cannot forget it afterwards.

---

### P4 — `PROPLOAD`: propositional load of the narrowed span (REVIEW_LIST N9)

**Definition.** Over the **narrowed** span only (the `[node narrows this span to: ...]`
text if present, else the SOURCE TEXT): count of deontic-modal occurrences
(`should`, `should not`, `must`, `may`, `can`, `is expected to`, `is required to`,
`needs to`, `ought to`) plus the count of coordinating conjunctions joining verb phrases
(`, and `, `, or `, ` and then `). One integer.

**Mechanism.** REVIEW_LIST **N9** — "Count the FINITE VERBS before drafting" — and its
associated finding that repair-loop exhaustion on a *short* span is a SCOPE CONFLICT: the
span demands more propositions than the drafter allocated structure for, so obligations get
collapsed into one act (the `l1368_1541_n019` three-obligations case) or conditions get
merged. Propositional load is the pressure N9 names.

**Predicted direction.** Higher load → more frontier yield.

**Input tier: 1.** Span parse.

**Document-tunedness: MEDIUM.** The modal lexicon is English-general, but the Model Spec's
register is unusually modal-dense and the calibration would not transfer without
re-fitting. Ranked below P1–P3 for that reason.

---

### P5 — `DISJ`: a disjunction marker in the narrowed span (REVIEW_LIST P4)

**Definition.** 1 if the narrowed span contains ` or `, `either `, or `, or ` outside a
parenthetical citation. Regex, case-insensitive.

**Mechanism.** REVIEW_LIST **P4** — "Disjunction encoded as conjunction" — is a named
failure with a named remedy (one act with alternative bodies and a single `oblige`). A
disjunctive span forces a choice the schema does not make obvious; the wrong choice
changes the claim from "do any one" to "do all three".

**Predicted direction.** Disjunction present → more frontier yield.

**Input tier: 1.**

**Document-tunedness: LOW.** ` or ` is English, not Model Spec.

---

### P6 — `HEDGE`: a defeasibility marker in the narrowed span (REVIEW_LIST P7)

**Definition.** 1 if the narrowed span contains any of: `by default`, `generally`,
`typically`, `usually`, `unless`, `may want to`, `should be willing`, `in general`,
`normally`, `tends to`. Regex, case-insensitive.

**Mechanism.** REVIEW_LIST **P7** — "Defeasibility is unencodable and must be RECORDED" —
and independent-review class E: four asserts where the hedge survives *only in the
read-back* while the formal item is an unqualified `forbid`/`oblige`. The schema has no
value for defeasible force, so a hedged span systematically pushes the drafter into
overclaiming. `l1707_1973_n022` ("by default", "unless policy explicitly allows it") is the
worst instance in the set and it is exactly this shape.

**Predicted direction.** Hedge present → more frontier yield.

**Input tier: 1.**

**Document-tunedness: LOW-MEDIUM.** English-general lexicon; the specific hedges are
common across normative documents, but the list was assembled with the Model Spec in view.

---

### Considered and REJECTED, with reason (not fitted, not scored)

* **`ABSTAIN_TRIGGER`** — span is a section heading, a worked example, or purely
  descriptive (`00_task`'s three named abstention triggers). Mechanism is excellent and
  the single clearest DEFECTIVE module in the set (`l1707_1973_n006`) is an example clause.
  **Rejected because its positive cell would be n≈4 of 17.** A predictor with a cell of 4
  cannot be tested at this n; fitting it would be the exact overfit this pre-registration
  exists to prevent. Recorded here so that a future run at larger n knows to test it, and
  so that it cannot be smuggled in after the fact.
* **`reasoning_chars`** — a PERFECT format-forcing discriminator (185/185 forced = 0,
  64/64 unforced > 0), so it is only interpretable within the unforced cells. The Opus loop
  turn 1 is a single regime, so within-regime variance is all that is left and it is
  confounded with span length. Excluded to hold the cap at six.
* **`GOOD/BAD` example structure (P10)** — subsumed by `ABSTAIN_TRIGGER`, same n problem.
* **assert count / concept count on the turn-1 draft** — excluded as *outcome-adjacent*:
  they are counts of the same object the frontier critic is editing, so a correlation with
  edit count is partly definitional (more entries = more editable surface). If used at all
  they are reported as a **length control**, never as a predictor.

---

## 4. ANALYSIS PLAN, FIXED BEFORE THE JOIN

1. Compute all six predictors on all 17 clauses. Compute all outcomes. Join.
2. **Primary:** Spearman rank correlation of each predictor against **O2 (`TURNS`)** and
   **O1 (`FROZEN`)**, both Tier 1-M. Report ρ and the n behind it.
3. **Ranker evaluation, not classifier evaluation.** For each predictor, report the
   fraction of total frontier yield (Σ`FROZEN`) captured by the top-⌈17/3⌉ = 6 clauses by
   that predictor, against the 6/17 = 35.3% a random selection captures. This is the
   number that answers the economic question and it is the number I will lead with.
4. Secondary: O3–O6.
5. **Transfer:** recompute P2, P4, P5, P6 on the 25-clause reference cohort (P1 is
   unavailable there — no cheap critics ran on it; P3 requires a turn-1 draft in the same
   regime and is checked for availability) and test against **T1**. Report whether the
   direction pre-registered in §3 holds. **A predictor that reverses sign on transfer is
   reported as dead, whatever its in-sample ρ.**
6. Report every cell size. Any cell below 5 is reported as a look, not a finding.

## 5. FALSIFIERS, FIXED BEFORE THE JOIN

* **P1 is falsified** if `DISAGREE` has |ρ| < 0.3 against `TURNS` on the 6 available
  clauses, or if it points the wrong way.
* **Any predictor is falsified** if its top-6 capture of Σ`FROZEN` does not exceed the
  35.3% random baseline by more than the arm A′ mechanical noise floor allows.
* **The whole instrument is falsified**, and I will say so in those words, if no predictor
  both (a) beats the random baseline in-sample and (b) holds its pre-registered sign on the
  reference cohort. **A negative result here is a real finding and will be reported as
  the headline if that is what the data says.** I am not permitted to reach for a rule.

## 6. WHAT n=17 CANNOT SETTLE, WRITTEN IN ADVANCE

With 17 points and 6 predictors, a multivariate fit is meaningless and will not be run.
Only univariate rank statistics and top-k capture are reported. No thresholds are tuned.
No predictor is combined with another. Any 2×2 with a cell below 5 is a look.
