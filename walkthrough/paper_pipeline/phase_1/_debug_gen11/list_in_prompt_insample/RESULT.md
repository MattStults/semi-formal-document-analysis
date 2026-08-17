# RESULT — does the review list work IN-SAMPLE, on the clauses it was measured on?

**Answer: NO. It fails at the ceiling.**

Seventeen clauses, each re-drawn under the **byte-identical arm-B prompt** that
carries a list entry naming that clause's own historical defect — in eight cases
quoting an artifact of that clause's own draft **verbatim**.

* **0 of 17** turn-1 drafts defect-free (arm A: 0 of 17; arm B: 0 of 15).
* **9 of 17** reproduced their own frozen historical defect; **16 of 17** either
  reproduced it or replaced it with an equally conclusion-changing one.
* **35 of 42 conclusion-changing defects (83%)** correspond to an entry the
  translator was holding — arm B out-of-sample measured **87%**. The two numbers
  are indistinguishable.
* **Five modules are structurally identical to their unaided arm-A drafts**, two
  of them **byte-identical in the field that carries the defect.**

⚠️ **MEASURED at n = 17, single-digit cells throughout.** No rate below is
statistically separated from noise. The claims that need no rate are the ones
that carry the verdict: a defect the prompt quotes *word for word* is evidence
about that defect whether it happened once or nine times.

**Pre-registration:** `PREREG.md`, signed before the first call, including the
frozen per-clause defect table §4 that recurrence is scored against.
**Spend: $0.03826** measured, 17 live calls, cap $0.06. Prompt sha256
`045608289e6e60a6c7ab327cfb10625a034bd38080af88f0043f757b59517917`, verified
equal to arm B's by a gate that refuses to send otherwise.

---

## 1. THE PROMPT — not rebuilt, and the gate proves it

`config_insample.json` points `system_files` at `../list_in_prompt/promptsB/`,
the exact five files arm B sent, read-only. `run_insample.py:prompt_shas`
recomputes the assembled system block and **raises `SystemExit` unless the
sha256 still equals arm B's**. It printed the match before sending:

```
system block: 53426c  sha256 04560828…917
VERIFIED byte-identical to arm B (04560828…917).
17 clauses, worst case $0.0526; measured so far $0.0000; cap $0.06
```

⛔ Nothing under `prompt/`, `schema.py`, `resources/`, `resolve_runs/graph_v2/`,
`runs/`, `repair_graveyard/`, or `_debug_gen11/list_in_prompt/` was written. No
git was run. Every byte this arm produced is under
`_debug_gen11/list_in_prompt_insample/`.

**All 17 clauses, not 15,** as `PREREG.md` §2 records: `ORDERING.md` defines the
list's evidence population as 17, and the two proof clauses carry the sharpest
in-sample relation available (entry 15's worked example *is*
`l3147_3238_n003`'s span; entry 2's *is* `l1_170_n056`'s). The alternative —
the 15 loop clauses only — was rejected by name in the pre-registration.

---

## 2. ⚠️ THE IN-SAMPLE PREMISE, CORRECTED BEFORE THE RUN

The brief said these clauses "are the ones every entry was written from."
`PREREG.md` §3 recorded before any call that this is **not exactly true**: ten
of the twenty entries name an earlier five-clause wave as provenance
(`l831_1000_n005`, `l461_608_n015`, `l1108_1367_n014`, `l2405_2473_n001`,
`l1974_2125_n019`), none of which is in this draw.

**The relation that is true, and that this arm tests:** these 17 are the clauses
the list was **measured, ranked and corrected on**. Every cell of `ORDERING.md`
counts over them; all four corrections folded into the arm-B text (R33, R57,
R58, R65) came from them; and the adjudicator ran every entry against every one.

The pre-registration split that into two grades, frozen before the run:

* **GRADE A (8 clauses)** — the prompt quotes, verbatim, an artifact of that
  clause's own draft or span.
* **GRADE B (9 clauses)** — an entry produced a recorded finding on that clause.

⚠️ **One grading error, in my own disfavour, found after the run and reported
rather than fixed.** Row 16 (`l1707_1973_n006`) was frozen as grade B. It is
grade A: the tail entry *"A GOOD/BAD example pair must have DISJOINT arms"*
quotes `good_response(R)` and `bad_response(R)` — this clause's own atoms — and
`REVIEW_LIST.md` records that P10 was written from this very clause. **Scoring
below uses the frozen grade**, which understates the result. The correction is
noted where it bears.

---

## 3. THE PER-CLAUSE TABLE — scored against the FROZEN §4 predictions

`✅` = the frozen defect did not recur. `⛔` = it recurred (verbatim or in
mechanism). `⚠️` = it did not recur but an equally conclusion-changing defect
took its place.

| # | clause | grade | entry that names it | frozen defect | outcome | CC defects | floor A→B |
|---|---|:--:|---|---|:--:|---:|---|
| 1 | `l4252_4482_n016` | **A** | **12** | `prefer` on the acts the span says to avoid | ⛔ **verbatim, 3 of 3** | 2 | clean→clean |
| 2 | `l3147_3238_n003` | **A** | **15** | three `oblige` on one identical body for an *"or"* | ⛔ **verbatim** | 2 | clean→**3 breaches** |
| 3 | `l2126_2404_n016` | **A** | **15** mirror, 1, 5 | coextensive `ontology` heads on one identical body | ⛔ **mechanism** | 1 | clean→**3 breaches** |
| 4 | `l3239_3382_n004` | **A** | 1, **8**, 5 | the span's two conditions do no work | ⛔ **mechanism** | 3 | 2 br→clean |
| 5 | `l1368_1541_n019` | **A** | **1**, 9, 2 | `S` names two things; middle `oblige` cannot fire | ⚠️ | 2 | 1 br→**4 breaches** |
| 6 | `l4252_4482_n005` | **A** | **3**, 1, 6 | chain inverts the clause into a blanket accent ban | ⚠️ | 3 | 2 br→clean |
| 7 | `l1_170_n056` | **A** | **2**, 3, 9 | exception unattached to the obligation | ⚠️ | 2 | 5 br→clean |
| 8 | `l3239_3382_n002` | **A** | **1** | `overstepping(A)` head in its own body | ✅ **fixed** | 3 | 2 br→**6 breaches** |
| 9 | `l3596_3876_n009` | B | **1** | three glosses restate their own names | ⛔ **byte-identical** | 2 | clean→clean |
| 10 | `l3877_3953_n014` | B | **5**, 4 | document relation in `inputs`; the node provides nothing | ⛔ **isomorphic** | 2 | clean→clean |
| 11 | `l1001_1107_n005` | B | **5**, 4, 3 | `rule_under_heading/2` in `inputs`; rule cannot fire | ⛔ **byte-identical** | 3 | clean→clean |
| 12 | `l2474_2554_n004` | B | **8**, 14, 1 | `third_party_interaction` inverts the conjunction | ⚠️ | 4 | 2 br→**2 breaches** |
| 13 | `l2821_3040_n017` | B | **8**, 4, 1, 3 | unconditional manner duty; `default_context` from an **excluded** sentence | ⛔ **assert byte-identical** | 4 | clean→clean |
| 14 | `l1707_1973_n022` | B | **14**, 4, 1 | vehicle's exception imported into the tenor by NAF | ⛔ **isomorphic** | 3 | clean→**1 breach** |
| 15 | `l171_426_n022` | B | **8**, 3, 4, 6 | `higher_level_instruction` hardcoded to root | ⚠️ | 3 | 4 br→clean |
| 16 | `l1707_1973_n006` | B*(A) | 6, 11, 10, **tail P10** | three of four behaviours reach no rule | ⚠️ | 2 | clean→clean |
| 17 | `l699_796_n012` | B | **7**, 3, 2 | modality survives on only one conjunct | ✅ **fixed** | 1 | clean→clean |
| | **TOTAL** | | | | **9 ⛔ / 6 ⚠️ / 2 ✅** | **42** | **7→6 invalid** |

Full drafts and floor records in `out/<id>.json` and `out/<id>.raw.json`.

---

## 4. SCORED AGAINST THE PRE-REGISTRATION

| criterion | "works" threshold | measured | |
|---|---|---|---|
| **M1** defect-free turn-1 drafts | ≥ 5 of 17 | **0 of 17** | ❌ |
| **M3** frozen defect recurs | ≤ 5 of 17 **and** no equal substitute | **9 of 17 recur; 6 of the 8 remaining substitute** | ❌ |
| **M5** grade-A clauses reproducing | ≤ 2 of 8 | **4 of 8** | ⚠️ **AMBIGUOUS as written** |
| **M2** conclusion-changing rate | — | **16 of 17** | (arm B: 14 of 15) |
| **M4** defects an entry names | ≤ 25% | **83%** (35 of 42) | ❌ (arm B: 87%) |
| **M6** floor failures | — | **6 of 17 (35%)** | NULL vs arm A's 7 of 17 |
| **M7** `asserts`/`ontology` mix | — | **no shift under pairing** | ⭐ see §6 |
| **H1** crowding-out / floor | fires at ≥ 11 of 17 | 6 of 17 | ✅ did not fire |
| **H2** obedience harm | fires at ≥ 1 | ⛔ **FIRES, on ≥ 4 clauses** | see §7 |
| **H3** entry-driven invention | fires at ≥ 3 | ⛔ **FIRES, 4 clauses** | see §7 |

⚠️ **M5 must be reported as the pre-registration wrote it, and it is ambiguous.**
4 of 8 grade-A clauses reproduced their frozen defect — between the "works"
band (≤ 2) and the "fails" band (≥ 5). The four that did not reproduce **all
substituted an equally conclusion-changing defect**, which makes 8 of 8 grade-A
clauses defective on a conclusion-changing point; but that combined measure was
**not** what M5 pre-registered, and it is not scored as though it were. **M5 is
the one headline metric this arm did not resolve cleanly.**

### Against the paired arm-A baseline

| | arm A turn-1 (same 17) | arm B (15 new) | **in-sample (17)** |
|---|---|---|---|
| defect-free turn-1 drafts | 0 of 17 | 0 of 15 | **0 of 17** |
| `outcome != translated` | 7 of 17 (41%) | 8 of 15 (53%) | **6 of 17 (35%)** |
| conclusion-changing defect | ~16 of 17 | 14 of 15 | **16 of 17** |
| CC defects an entry names | — | **87%** | **83%** |
| mean raw output chars | 3,645 | 3,854 (+6%) | **3,803 (+4%)** |

---

## 5. THE DECISIVE READOUT — the four cells where the prompt quotes the clause

No rate is needed to read these.

### ⛔⛔⛔ `l4252_4482_n016` — the sharpest cell in the experiment, and Q-c landed

Entry 12 is in the prompt. It names the failure (*"`status` has no negative
pole"*), names the mechanism (*"the natural move is `prefer X` with a read-back
that negates it — so the compiled rule states the OPPOSITE of the document"*),
gives the remedy **in this clause's own words** (*"`prefer
minimize_redundant_phrases`"*), and closes *"Never leave `status` and
`read_back` disagreeing."*

The module emitted, for a span reading *"should **avoid** repeating the user's
prompt, and generally **minimize** redundant phrases and ideas"*:

```
prefer repeat_user_prompt(R)        read_back: "…is to be avoided"
prefer include_redundant_phrases(R) read_back: "…is to be minimized"
prefer include_redundant_ideas(R)   read_back: "…is to be minimized"
```

**Three of three, statuses identical to the unaided arm-A draft.** The stage-4
`prefer-polarity` detector fired on all three — at `note` severity, which cannot
reach the repair loop. **In production this module ships.**

⛔ **And it got worse in a second way.** Arm A's bodies were linked
(`response(R), user_prompt(P), repeats_prompt(R, P)`). This draft moved them
into three new `ontology` entries **sharing one identical body**:

```
repeats_user_prompt(R)        :- response(R).
contains_redundant_phrases(R) :- response(R).
contains_redundant_ideas(R)   :- response(R).
```

so **every response now repeats the prompt and contains redundant phrases and
ideas**. That is entry 15's mirror (*"several `ontology` heads sharing ONE
identical body are coextensive"*), violated in the block the list pushed the
content into.

### ⛔⛔ `l1368_1541_n019` — the gloss the prompt quotes by name, minus two letters

Entry 1 — the file's #1-ranked, highest-yield entry — opens:

> `safety_precaution_suggestion/1` glossed *"S is a suggestion that the user
> take safety precautions"* is **the name, re-spaced**.

Arm A's gloss: `'S is a suggestion that the user take safety precautions'`.
This draft's gloss: `'a suggestion that the user take safety precautions'`.

**The only edit is deleting the two-character variable prefix that the entry's
own sentence quotes.** The predicate name is quoted in the prompt. The gloss is
quoted in the prompt. The verdict on it is in the prompt, in bold, at the top.

### ⛔⛔ `l3147_3238_n003` — the list made the module *articulate* the error, not fix it

Entry 15 quotes this clause's span verbatim: *"use a tool …, hedge …, **or**
explain"* became three obliges on one body, *"so an assistant that hedged
violated two."*

The module emitted three `oblige` on the identical body
`assistant_definition(A), lacks_sufficient_confidence(A, R)` — **unchanged from
arm A**. What did change is `claims`, which now carries a fourth entry the
unaided draft never had:

> *"C4: The three options in C1-C3 are alternatives: satisfying any one of them
> satisfies the clause's requirement."*

⭐ **The list moved the correct reading into the prose and left the logic
stating the opposite.** That is not "the model ignored the prompt". The module
now **states the disjunction and encodes the conjunction**, manufacturing entry
6's fingerprint (a claim encoded nowhere) that arm A's draft did not have.

### ⛔⛔ `l1707_1973_n006` — P10's own calibration clause reproduces P10's defect

The prompt's tail entry says a GOOD/BAD pair must have disjoint arms, and quotes
`good_response(R)` / `bad_response(R)` — this clause's own atoms. The module
emitted **the same `prefer` on the same act `respond_with(R)`** for both:

```
prefer respond_with(R) :- good_response(R), …
prefer respond_with(R) :- bad_response(R), …
```

with read-backs that say "preferred" and "disfavored". **The compiled program
cannot tell the poles apart — the one thing the example exists to say.**

---

## 6. ⭐ ARM B's ONE MEASURED "BEHAVIOUR CHANGE" DOES NOT SURVIVE PAIRING

Arm B's headline mechanism claim was: *"The list demonstrably changed drafting
behaviour: content moved OUT of `asserts` and INTO `ontology`"* — `asserts`
−35%, `ontology` +50%. That was measured against a **historical control of
different clauses**.

Measured **paired**, on the same 17 clauses, same model, one variable:

| field, mean entries per module | arm A t1 | in-sample | arm B (unpaired) |
|---|---:|---:|---:|
| `asserts` | 2.0 | **2.0** | 1.3 |
| `ontology` | 1.2 | **1.3** | 1.8 |
| `acts` | 1.5 | 1.8 | 1.0 |
| `concepts` | 5.5 | 5.8 | 5.9 |
| `inputs` | 2.9 | 2.9 | 3.2 |
| `claims` | 2.7 | 3.0 | 2.6 |

⭐ **The shift is gone.** `asserts` did not move at all; `ontology` moved by
0.1 entries per module. **Q-e is REFUTED**, and arm B's mix result is best read
as clause-set difference rather than a list effect — which is exactly the
weakness arm B named in its own limitations and could not test.

⚠️ **This does NOT mean the list changed nothing.** The per-clause movements are
large and in *both* directions (`l4252_4482_n016`: `ontology` 0→3, `inputs` 7→1;
`l171_426_n022`: `inputs` 7→2, `concepts` 7→4; `l4252_4482_n005`: `ontology`
2→0). **The list changes drafting; it does not change it in a consistent
direction, and it does not change the defect rate.**

---

## 7. ⛔ HARM: H2 FIRES, AND IT IS THE MOST ACTIONABLE RESULT HERE

Arm B pre-registered H2 (a defect that is the **direct product of correctly
obeying an entry**, the R57 shape) and it did **not** fire. **In-sample it
fires, and it fires on the entry ranked #5.**

Entry 5 (N1) says: *"if the span names a KIND of thing, prefer the bodied rule
over a coined constant, and give it the argument the act's variable can bind."*
That is the entry the loop measured as reversing an adjudicator's own call.
Obeyed, it produced **vacuous bodied rules** — bodies that are type
declarations, true of every case:

| clause | arm A | in-sample, after obeying entry 5 |
|---|---|---|
| `l4252_4482_n016` | no `ontology`; linked bodies in `asserts` | `repeats_user_prompt(R) :- response(R)` ×3 |
| `l2126_2404_n016` | `no_moral_ambiguity/0`, an inert arity-0 constant | `no_moral_ambiguity(S) :- scenario(S)` — **the clause's guard is now true of every scenario** |
| `l2821_3040_n017` | `natural_uncertainty_expression(A) :- assistant_definition(A), default_context` | `… :- assistant_definition(A)` — **the default condition deleted** |
| `l2474_2554_n004` | — | `honest_and_forthright(A) :- assistant_conduct(A)` |

⭐ **The mechanism, stated so it is checkable.** An inert ground constant is
*harmless*: nothing unifies with it, so the rule derives nothing and the module
concludes less than the span. A vacuous bodied rule is *actively wrong*: it
derives the span's discriminating condition **of every case**, so the module
concludes more than the span, in the dangerous direction. **Entry 5 moves
modules from the first failure to the second and its text contains nothing that
would stop it.** `l2126_2404_n016` is the cleanest instance — arity-0 →
arity-1-with-a-variable is precisely what entry 5 asks for, and the result is
that a clause scoped to *"scenarios where there's no moral ambiguity"* now
governs all scenarios.

⚠️ **Entry 5 also points the wrong way on two clauses outright.** On
`l1001_1107_n005` and `l3877_3953_n014` the correct answer is a **ground atom
about the document** — entry 5's own last sentence — and both modules wrote a
bodied rule over a situation input instead. The exception is one sentence at the
end of an entry whose headline is the opposite instruction.

**H3 also fires** (4 clauses coin `ontology` machinery an entry motivates and
the span does not), though it is the same four modules, so H2 and H3 should be
read as one finding, not two.

---

## 8. WHAT THE LIST *DID* DO — recorded so the null is not overstated

* ⭐ **`l3239_3382_n002` — entry 1 worked.** The circular
  `overstepping(A) :- …, overstepping(A)` that made arm A's only prohibition
  undischargeable is **gone**. This is the arm's one unambiguous structural fix
  attributable to an entry. ⚠️ The same module then failed the floor with **6
  breaches** — the worst in the arm — and pulled *"without overstepping"* in
  from outside the narrowing, which entry 4 forbids.
* ⭐ **`l3239_3382_n004` — entry 1 worked on the glosses it quotes.** Arm A's
  *"T is a transformation task"* and *"S is an interactive setting"* are gone,
  replaced by glosses that genuinely define. ⚠️ **The content defect moved into
  the body**: the single new `ontology` entry carries `transformation_task(T)`
  and `changes_warranted(C)` as **unlinked singleton variables**, so the span's
  two conditions still do no work. **The defect relocated; it did not go away.**
* ⭐ **`l2474_2554_n004` — entry 8 worked at the point of failure.** Arm A's
  `third_party_interaction(A) :- on_behalf_of_user(A)` inverted the span's
  conjunction; this draft writes both conjuncts. ⚠️ The *consequence* returned
  by another route: the `permit lie_by_omission` assert drops the third-party
  guard entirely, so **lying by omission to the user is permitted** — the same
  dangerous conclusion the loop charged arm A with.
* ⭐ **`l699_796_n012` — the one clean row.** The frozen defect (modality on
  only one conjunct) is fixed: `serious_side_effects` is now glossed *"an
  instruction whose execution **could** cause serious side effects"*. It is also
  the arm's least severe frozen defect. ⚠️ The clause's *other* historical
  defect recurred verbatim in class — the borrowed `root_authority` gloss
  rewritten with invented content (*"outranks other rules in the document"*) and
  stamped `licence: textual, cites: <this node>`.
* ⭐⭐ **Entry 2 is the arm's clearest transfer, and it is MEASURED
  mechanically.** `closure` is conclusion-bearing (`cepa` says silence permits),
  and entry 2's whole second half is *"use `unclear`"*:

  | | arm A t1 | in-sample |
  |---|---:|---:|
  | clauses with ≥ 1 `cepa` closure | **14 of 17** | **6 of 17** |
  | clauses with ≥ 1 `unclear` closure | **0 of 17** | **8 of 17** |

  Arm A never wrote `unclear` on any of these 17 clauses. **This is the one
  entry that demonstrably changed a conclusion-bearing field across the arm, in
  the direction the entry asks for.** ⚠️ It is also the entry the loop scored
  #2 by evidence and applied *beyond* its measured case twice, so some of these
  eight may be over-application; each was judged individually here and none was
  charged as wrong, but that judgement is mine and is contaminated. **Recorded
  as the strongest positive in the arm, and it did not move M1, M2 or M4.**
* **Entry 9** was applied on `l1_170_n056`: `authority_levels_hierarchy` carried
  an explicit argument order in its gloss. One clause, no conclusion changed.

⛔ **And the class no entry names did not move at all.** A borrowed `NEEDS` gloss
rewritten and stamped `licence: textual, cites: <this node>` — arm B's largest
fresh class — appears on **16 of the 16 clauses that have NEEDS names, in both
arms**. Identical. `00_task.md` calls a manufactured citation *"the single worst
failure available here"*, and the list, at 13.5 KB across 20 entries and three
anti-rules, contains no sentence that asks what licence a borrowed gloss carries.

**Five of seventeen modules are structurally identical to their unaided arm-A
drafts.** Two are byte-identical in the field that carries the defect:

```
l1001_1107_n005  ontology:  root_authority(R) :- rule_under_heading(R, protect_privacy_heading)   [A == B]
l3596_3876_n009  ontology:  recognizes_strangeness(A, …) :- assistant_definition(A)  ×2           [A == B]
l2821_3040_n017  asserts:   oblige express_uncertainty_naturally(A) :- assistant_definition(A), default_context  [A == B]
```

---

## 9. PREDICTIONS, SCORED

| | prediction | outcome |
|---|---|---|
| **Q-a** | M1 = 0 or 1 of 17 | ✅ **0 of 17** |
| **Q-b** | recurrence 8–13 of 17 | ✅ **9 of 17** |
| **Q-c** | `l4252_4482_n016` reproduces its polarity inversion | ✅ **3 of 3 asserts** |
| **Q-d** | entry 1 violated on ≥ 3 of the 4 clauses whose gloss is quoted | ✅ **3 of 4** (rows 3, 5, 9; row 4 fixed) |
| **Q-e** | the `asserts`/`ontology` shift repeats | ❌ **REFUTED under pairing** — and it retro-weakens arm B's claim |
| **Q-f** | ≥ 2 clauses produce a defect fresh to both arms | ✅ arm B's largest fresh class — a borrowed gloss rewritten and stamped `licence: textual, cites: <this node>` — appears on **16 of the 16 clauses with NEEDS names, in BOTH arms, unchanged**; nothing in the 20 entries asks what licence a borrowed gloss carries |
| **Q-g** | H2 does not fire | ❌ **it fires**, on ≥ 4 clauses, via entry 5 |

---

## 10. ⚠️ CONTAMINATION, AND WHICH WAY IT CUTS

`PREREG.md` §7 disclosed this in advance and it is restated, not softened.
**I did not adjudicate blind and I do not claim to.** I read all 17 historical
adjudications before writing the frozen table, and I wrote the frozen table.

* **What is protected:** recurrence was scored against §4's **written, frozen**
  predictions, not against whatever I noticed afterwards. The floor ran first on
  every draft. Span-first order was preserved.
* ⭐ **The direction of the bias favours the finding I reached, and that must be
  carried.** Knowing a clause's historical defect biases me **toward** finding it
  again. So the **9 of 17 recurrence rate is the number to distrust**, and it is
  the number I lean on least. The claims that do not depend on it are the ones
  the verdict rests on: three byte-identical fields, one gloss reproduced minus
  two characters, and 3-of-3 status inversions against an entry that prints the
  remedy in the clause's own words. **Those are checkable from the bytes on
  disk without trusting my reading at all.**
* **What cannot be fixed:** one adjudicator, no second reader, no answer key.
  **Novel** defects got less attention than predicted ones by construction, so
  any claim that a clause's defect count *fell* is weaker than a claim that it
  did not. The `asserts`/`ontology` and floor numbers in §4 and §6 are
  **mechanical** and carry none of this.
* **Where contamination most plausibly bit:** rows 5, 6, 7, 15, 16 — the ⚠️
  rows, where I judged a *substitute* defect "equally conclusion-changing".
  That judgement is mine, it is the softest in the table, and a reader who
  disagrees with it should read M3 as **9 recurrences out of 17** and stop
  there. The verdict does not depend on the ⚠️ column.

---

## 11. VERDICT

**The review list does not work in-sample. The format is insufficient, and the
argument moves to the schema and the graph.**

`PREREG.md` §1 named the two possible readings in advance. This is the first:

1. **0 of 17 defect-free**, against a paired baseline of 0 of 17. The number the
   experiment exists to move did not move on its own clauses.
2. **83% of conclusion-changing defects were explicitly warned against** —
   against 87% out-of-sample. **The list's coverage is not the problem, and
   in-sample specificity buys nothing.** Four percentage points at n = 17 is
   noise; the finding is that the two numbers are the same.
3. **Defects the prompt quotes verbatim reproduced**: a gloss minus two
   characters, three status inversions whose remedy is printed in the clause's
   own words, a disjunction the prompt quotes as its worked example, and a
   GOOD/BAD collision on the clause the entry was written from.
4. ⛔ **The list manufactures a defect class.** Entry 5, obeyed correctly, turned
   harmless inert constants into **vacuous bodied rules** that assert the
   clause's discriminating condition of every case. Arm B could not see this;
   pairing makes it visible.
5. ⭐ **Arm B's one positive mechanism claim does not survive pairing.** The
   `asserts`→`ontology` movement is a clause-set artifact.

⭐ **What follows.** The defects that dominate this arm are the same structural
five arm B named, and pairing shows they are **not clause-specific and not
knowledge-shaped**:

* **a vacuous or unlinked rule body** — `X(R) :- response(R)`,
  `no_moral_ambiguity(S) :- scenario(S)`, unlinked singleton variables (**6 of 17**);
* **a `status` field with no negative pole** — `prefer` on the act to avoid
  (**2 of 17**, one of them new);
* **negation-as-failure where the schema offers nothing else** (**2 of 17**);
* **a document-side relation with nowhere legal to live** — forced into `inputs`,
  where no situation will ever supply it (**3 of 17**);
* **a borrowed gloss with no licence rule** — rewritten and self-cited
  `textual` (**16 of 16**, identical in both arms, and named by no entry).

Each is a place where the model wrote the only thing the format allowed, or
wrote a thing the format does not check. **A prompt cannot reach them — not at
any level of specificity, including specificity that quotes the clause's own
bytes.** That is what this arm adds to arm B, and it is the strongest available
evidence for a schema change.

⚠️ **What this does NOT show.** It does not show the list is worthless — its
value as a **critic's** instrument is measured in `ORDERING.md` and stands
untouched. **One entry did transfer**: entry 2 moved `cepa` from 14 of 17
clauses to 6, and put `unclear` on 8 clauses where arm A wrote it on none (§8).
That is a real, mechanically measured change in a conclusion-bearing field, and
it is the shape a transferable entry has — a single named value, decidable
without re-reading the span. **It is one entry in twenty, and it did not move
M1, M2, M3 or M4.** It does not establish a rate for anything: n = 17, cells of 1–4, one
contaminated adjudicator. It does not show that *no* prompt could help; it shows
that this prompt, at 13.5 KB, does not, on the clauses most favourable to it.
And **M5 — the pre-registration's sharpest metric — landed in the ambiguous
band and is reported as ambiguous.**

⛔ **Nothing in `promptsB/` was tuned, before or after. No second variant was
run.** A second variant would have to be pre-registered as such, and both
reported.

---

**Signed.** — adjudicator, 2026-08-16. Spend **$0.03826** of a $0.06 cap, 17
live calls. **Reconciled two ways**: the per-clause records in `out/*.json` sum
to $0.03826, and the last 17 rows of `semi-formal-experiment/usage.jsonl` sum to
$0.03825 — agreement to the rounding.

⛔ **Write audit.** The only file this arm touched outside
`_debug_gen11/list_in_prompt_insample/` is `usage.jsonl`, appended by
`providers._append_usage` as every paid call in this repo does. `checks.py`
(12:09) and `resolve_runs/graph_v2/EXPERIMENTS.md` (09:49) were already modified
before this run (16:35) and were not touched by it; nothing under `runs/`,
`translation_sample/runs/`, or `repair_graveyard/` was written; no git was run.
