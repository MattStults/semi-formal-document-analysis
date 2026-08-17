# RESULT — ARM F, structural coercion: the review list as REQUIRED OUTPUT FIELDS

**Answer: the field was filled 102 times out of 102 and reviewed nothing.**

⭐ **THE HEADLINE, and it is the number `PREREG.md` §7 R-c predicted before the
run: every single one of the 102 forced verdicts is `applies_and_handled`.**
Zero `does_not_apply`. Zero `applies_and_not_handled`. **21 of those 102 cells
are a written "handled" over a live defect of that check's own class** — a false
clean the model put in writing, which no prior arm could see.

* **0 of 17** turn-1 drafts defect-free (arm A: 0 of 17; arm B: 0 of 15;
  in-sample: 0 of 17). **1 of 17** carries no *conclusion-changing* defect.
* **15 of 17** carry a conclusion-changing defect (arm A ≈ 16, in-sample 16).
* ⭐ **6 of 17 frozen historical defects were FIXED** — against the in-sample
  arm's 2 of 17 — while **7 recurred and 4 were replaced by an equally
  conclusion-changing substitute.**
* ⛔ **The `checks` array was not answered as the six checks at all.** On 13 of
  17 clauses the six cells are a *decomposition of the span* — six successive
  quotations from the source text with a one-word note on how each was encoded.
  The entries themselves, 7,532 characters of them in the wire schema, are not
  engaged anywhere in 102 cells.
* **2 of 17 broke the shape contract** (`C1,C2,C3,C1,C2,C3` — `minItems`/
  `maxItems`/`enum` honoured, "exactly once each" not), so on those two clauses
  **C4, C5 and C6 were never ruled on at all.**

⚠️ **MEASURED at n = 17, single-digit cells throughout.** No rate below is
separated from noise. The claims carrying the verdict need no rate: 102/102 is
not a rate, and a module that rules `applies_and_handled` under C6's label with
the evidence *"No anonymous variables"* is evidence about that cell whether it
happened once or a hundred times.

**Pre-registration:** `PREREG.md`, signed before the first call, including the
verdict thresholds, the four harm shapes and the eight predictions.
**Spend: $0.03160 measured**, 17 live calls, cap $0.10, worst case priced
$0.0577 before signing.

---

## 1. WHAT WAS BUILT, AND THE THREE GATES THAT PROVE IT

`arm_f_schema.request_json_schema()` **deep-copies** `schema.response_format()`
and appends one property, `checks`, mirroring `json_schema()`'s own
`required == list(properties)` rule. `run_armf.py:ArmFClient` overrides
`translate.Client._body` and nothing else, so the send path, the retry path, the
usage ledger and the cost envelope are all production code.

⛔ **`schema.py` was not edited, not patched, not shadowed and not written.**
Verified by the module's self-test before any call:

```
production top-level properties: [outcome … forbid_body]              (14)
arm F      top-level properties: [outcome … forbid_body, checks]      (15)
arm F required == properties: True
every PRODUCTION property untouched in the arm-F copy: True
production object still intact after deriving: True
wire schema: 14,432c -> 21,964c
```

**Gate 1 — the prompt is production.** `run_armf.py` rebuilds the system block
from `resolve_runs/graph_v2/config_corpus_all.json` and refuses to send unless
the sha256s are equal. Printed before sending: both
`3a66c5f54277fbea1c6a8f030435f0c3083d480954b2f6ee3aeef5f1f4e4c34c`, 39,959c.
**Gate 2** refuses if that block ever equals arm B's `04560828…`.
**Gate 3 — the orphan guard.** `40_review_list.md` is declared in
`prompt.unused_files`, so `translate.check_no_orphan_prompts` makes *"arm F
ships no list prose"* a checked fact rather than an omission that looks like a
bug. (It fired on the first attempt, before the declaration existed.)

So: **arm A → arm B** is *the entries as prose in the system block*;
**arm A → arm F** is *the entries as required fields of the reply*. One variable
each way, same 17 clauses, same model, same temperature, turn 1, no feedback.

### THE STRIP, and the proof it is safe

`schema.Module` is `extra="forbid"`, so the returned object cannot reach
`validate_all` with `checks` on it. `strip()` deletes **exactly one top-level
key** and rebinds every other value **by identity** — no copy, no
re-serialisation, no normalisation. `strip_proof()` records four facts per
clause, and **all four hold on all 17**:

| fact | 17/17 |
|---|---|
| `keys_removed == ["checks"]` and `keys_added == []` | ✅ |
| every surviving field identical **by `is`** to the parsed original | ✅ |
| every surviving field byte-equal under `json.dumps(sort_keys=True)` | ✅ |
| 15 fields before → 14 after | ✅ |

Identity is the strong claim; byte-equality is the one a sceptic can re-run from
`out/<id>.raw.json` without trusting this process's object graph. The **real**
`schema.validate_all` and the **real** `checks.run_checks` then ran on the
stripped object and on nothing else.

---

## 2. ⭐ THE MEASUREMENT ONLY THIS ARM COULD MAKE

### 2a. The distribution, which is one cell wide

| verdict | count | share |
|---|---:|---:|
| `applies_and_handled` | **102** | **100%** |
| `applies_and_not_handled` | **0** | 0% |
| `does_not_apply` | **0** | 0% |

`applies_and_not_handled` was described in the schema as *"say so; a declared
defect is worth more than a hidden one"*. It was available on every one of 102
occasions and used **zero** times.

### 2b. FALSE CLEANS — a written "handled" over a live defect of that check's class

**21 of 102 cells (MEASURED, adjudicated span-first before the verdicts were
opened).** Per clause:

| clause | false-clean cells | the defect the cell ruled handled |
|---|---|---|
| `l4252_4482_n016` | **C6**, C2 | `prefer respond_with(R) :- repeats_user_prompt(R)` ×3 — the response that repeats the prompt is **preferred**; `read_back` says "dispreferred" |
| `l3239_3382_n002` | C1, C3, **C5** | `assistant(A) :- assistant_definition(A)` — a bare type declaration; `overstepping` coined and unused |
| `l3239_3382_n004` | C1, C3, **C5** | `… :- assistant_definition(A), interactive_setting(S), transformation_task(T), changes_warranted(T)` — **S and T are unlinked**, so the guard fires on any assistant whenever *some* interactive setting exists anywhere |
| `l2474_2554_n004` | C4, C5 | `third_party_interaction(A) :- on_behalf_of_user(A)` — the third-party qualifier **dropped**, so `permit lie_by_omission` licenses lying **to the user** |
| `l2821_3040_n017` | C1, C5 | `natural_uncertainty_expression(E) :- …, express_uncertainty_naturally(E)` restates its own name; `default_context/0` inert |
| `l1707_1973_n022` | C4, C5 | the customer-service **analogy's** exception imported into the assistant's own prompts; `identity_capabilities_shareable(A) :- assistant(A)` |
| `l2126_2404_n016` | C2 | `cepa` justified *"does not forbid other answers, so silence permits them"* — the circular reason C2 names |
| `l1_170_n056` | **C2** | ⛔ `forbid honor_request(R) :- …, conflicts_with(R,I)` — **an "unless" arm turned into a prohibition**, which is C2's headline sentence |
| `l3596_3876_n009` | **C1** | 3 of 5 glosses restate their own names (`being_large_language_model` → *"being a large language model in general"*) |
| `l1001_1107_n005` | **C5** | `rule_under_heading/2` in `inputs`; the module's only rule cannot fire; `root_authority/1` is in `requires` **and** defined in `ontology` |
| `l1368_1541_n019` | C4 | the `dangerous_situation` trigger imported from the sentence the node **excludes** |
| `l3877_3953_n014` | C5 | a document relation carried as a situation `input` |
| `l699_796_n012` | C1 | `instruction/1` glossed *"I is an instruction that…"* |

⭐ **The sharpest three cells, which need no rate at all:**

1. **`l1_170_n056` / C2.** C2's first sentence is *"'should honor … **unless** it
   conflicts' WITHDRAWS a requirement on the excepted branch. It does not create
   a prohibition there. Adding `forbid` on that branch asserts something the
   span never says."* The module emits `forbid honor_request(R)` on exactly that
   branch and rules C2 `applies_and_handled`, with the action *"the forbid rule
   covers it."* **The model wrote the prohibition and then cited the
   prohibition as its evidence that the check was satisfied.**
2. **`l4252_4482_n016` / C6.** The clause the check was bought for. It reproduced
   the polarity inversion — in a *new* form (the act moved to `respond_with(R)`
   and the avoided property into the body, so the compiled rule now says a
   response is **preferred** *because* it repeats the user's prompt) — and ruled
   C6 `applies_and_handled` with the evidence **"No anonymous variables"** and
   the action **"all variables bound in bodies"**. It did not rule wrongly on
   C6. **It answered a different question under C6's label.**
3. **`l1001_1107_n005` / C5.** C5's own last clause names
   `root_authority(section_x)` as the correct pattern — *this clause's answer*.
   The module put `rule_under_heading/2` in `inputs` again, exactly as arm A and
   the in-sample arm did, and ruled C5 `applies_and_handled` with evidence that
   is the clause's heading and action **"none"**.

### 2c. ⛔ WHY THIS IS NOT "IT READ THE ENTRY AND IGNORED IT" EITHER

The false-clean count was the pre-registered headline. The **larger** finding is
what the 102 cells actually contain.

On **13 of 17 clauses the six cells are a decomposition of the SPAN, not a
review of the MODULE.** `l2126_2404_n016`'s six evidences are six successive
fragments of L2252, each with an action like *"asserted as forbid"*.
`l3147_3238_n003`'s C4/C5/C6 quote three sentences **outside** the node's
narrowing. On **4 clauses every one of the six cells carries the identical
evidence string** — `l1001_1107_n005` and `l3877_3953_n014` repeat the section
heading six times with action `"none"`; `l1_170_n056` repeats the span six times
and pastes the same 20-word action into five of them.

The `evidence` field was specified as *"quote the exact text from the module you
just wrote ABOVE"*, and it was ordered **before** `verdict` precisely to force
that look. **On 15 of 17 clauses it quotes the source document instead.** The
one ordering decision made to defeat rubber-stamping was answered by quoting the
wrong artifact.

⭐ **So the arm's own distinguishing question resolves to a third answer.** The
prose arms could not tell *"read and ignored"* from *"never engaged"*. Arm F
shows the model **engaged the FIELD and not the ENTRY**: it produced a
well-formed, plausible, entirely non-referential filling of a required
structure. Coercion bought **compliance with the shape** — 102/102 populated,
15/17 perfectly shaped — and **no engagement with the content**.

---

## 3. SCORED AGAINST THE PRE-REGISTRATION

| criterion | threshold | measured | |
|---|---|---|---|
| **F1** defect-free drafts | ≥ 5 of 17 | **0 of 17** | ❌ |
| **F2** coerced-class defect on the B7 clauses | ≤ 3 of 14 | **9 of 14** | ❌ |
| **F3** false-clean ≤ 20% **and** F1 or F2 | — | 20.6%, and neither F1 nor F2 | ❌ |
| **NULL** ≤1 defect-free **and** ≥6 of 14 **and** ≥70% ratifying | all three | 0; 9 of 14; **100%** | ⛔ **NULL, on all three limbs** |
| **H-F1** vacuity | ≥ 1 draft | **3 drafts** | ⛔ FIRES |
| **H-F2** crowd-out | ≥10 floor fails / truncation / −20% module size | 5 fails, 0 truncations, **−8.9%** | ✅ did not fire |
| **H-F3** coerced invention | ≥ 3 drafts | **0** | ✅ did not fire |
| **H-F4** verdict-serving damage | ≥ 1 draft | **0 identified** | ✅ did not fire |
| **shape** | — | **15 of 17 exact; 2 emitted C1,C2,C3,C1,C2,C3** | ⚠️ |

⚠️ **F2's denominator, corrected in my own disfavour and reported rather than
fixed.** `PREREG.md` §4 froze **B7 = 14** as *"the row lists any of entries 1,
2, 3, 4, 5, 12"*. That is looser than it should have been: on three of those
rows the coerced entry is not the one naming the **decisive** defect
(`l2474_2554_n004`'s inversion is entry 8's, `l2821_3040_n017`'s is entry 8's,
`l171_426_n022`'s is entry 8's). Scoring uses **the frozen denominator**, which
is the one signed before the run. On the tighter denominator the count is 7 of
11 — the same verdict, and it is stated so a reader can use either.

### Per-clause, scored against the frozen `list_in_prompt_insample/PREREG.md` §4

`⛔` the frozen defect recurred · `⚠️` it did not, but an equally
conclusion-changing defect replaced it · `✅` fixed.

| # | clause | frozen defect | arm F | in-sample | floor |
|---|---|---|:--:|:--:|---|
| 1 | `l4252_4482_n016` | `prefer` on the acts to avoid | ⛔ **new form, same inversion** | ⛔ | clean |
| 2 | `l3147_3238_n003` | 3 `oblige` on one body for an *"or"* | ⛔ **verbatim** | ⛔ | clean |
| 3 | `l2126_2404_n016` | coextensive `ontology` heads | ✅ **fixed** | ⛔ | clean |
| 4 | `l3239_3382_n004` | the span's conditions do no work | ⛔ **mechanism (now unlinked vars)** | ⛔ | clean |
| 5 | `l1368_1541_n019` | `S` names two things | ⚠️ (obligations self-satisfying) | ⚠️ | clean |
| 6 | `l4252_4482_n005` | blanket accent ban | ✅ **fixed** | ⚠️ | clean |
| 7 | `l1_170_n056` | exception unattached | ⚠️ (`forbid` on the hole) | ⚠️ | **1 breach** |
| 8 | `l3239_3382_n002` | head in its own body | ⚠️ (unsafe var refuses the file) | ✅ | **1 breach** |
| 9 | `l3596_3876_n009` | glosses restate their names | ⛔ **3 of 5** | ⛔ | clean |
| 10 | `l3877_3953_n014` | the node's one output derived never | ✅ **fixed** | ⛔ | clean |
| 11 | `l1001_1107_n005` | `rule_under_heading/2` in `inputs` | ⛔ | ⛔ | clean |
| 12 | `l2474_2554_n004` | conjunction inverted | ⛔ **verbatim** | ⚠️ | **4 breaches** |
| 13 | `l2821_3040_n017` | manner duty unconditional; `default_context` dropped | ⚠️ (**`default_context` KEPT**) | ⛔ | **1 breach** |
| 14 | `l1707_1973_n022` | vehicle's exception in the tenor | ⛔ **isomorphic** | ⛔ | **3 breaches** |
| 15 | `l171_426_n022` | `higher_level_instruction` hardcoded to root | ✅ **fixed** | ⚠️ | clean |
| 16 | `l1707_1973_n006` | GOOD/BAD poles indistinguishable | ⛔ | ⚠️ | clean |
| 17 | `l699_796_n012` | modality on one conjunct only | ✅ **fixed** | ✅ | clean |
| | **TOTAL** | | **7 ⛔ / 4 ⚠️ / 6 ✅** | 9 ⛔ / 6 ⚠️ / 2 ✅ | **5 of 17 invalid** |

### Against the paired baselines

| | arm A t1 (same 17) | in-sample (same 17) | **arm F (same 17)** |
|---|---|---|---|
| defect-free drafts | 0 of 17 | 0 of 17 | **0 of 17** |
| carries a conclusion-changing defect | ≈16 of 17 | 16 of 17 | **15 of 17** |
| floor failure | 7 of 17 | 6 of 17 | **5 of 17** |
| frozen defect fixed | — | 2 of 17 | **6 of 17** |
| mean raw output chars | 3,645 | 3,803 | **4,952** (+36%) |
| mean **module-only** chars | 3,645 | 3,803 | **3,321** (−8.9%) |

⚠️ **A conclusion-changing DEFECT COUNT is deliberately not compared.** The
in-sample arm counted 42 over 17 (≈2.5/clause); I counted ≈17 (≈1.1/clause). The
granularity differs and the numbers are **not comparable**. Only *"carries a CC
defect"*, which is per-clause and binary, is reported across arms.

---

## 4. ⭐ WHAT THE COERCION DID BUY — recorded so the null is not overstated,
## and bounded so it is not oversold

**6 of 17 frozen defects fixed, against the in-sample arm's 2.** At n = 17 with
single-digit cells that is 6 vs 2 and nothing more, but four of the six are
structural and specific:

* `l2126_2404_n016` — the coextensive heads are gone. One `ontology` entry,
  `clear_cut_scenario(S) :- no_moral_ambiguity(S), no_valid_opposing_perspective(S)`,
  with both conditions as arity-1 `inputs`. **The clause's guard survives.**
* `l3877_3953_n014` — `user_authority(R)`, the one thing the node exists to
  provide, is now **derived** rather than being an unfirable input.
* `l171_426_n022` — `higher_level_instruction` is now glossed **relatively**
  (*"from a higher level than the level at which the current behavior
  operates"*) instead of hardcoded to root.
* `l4252_4482_n005` — the accent inversion is gone; `exaggerated_or_stereotyped`
  is an input, not derived from `speak_in_accent`.

⛔ **But the attribution is weak and must be stated as such.** The verdicts show
the entries were not engaged, so *the checks cannot be what fixed these.* What
plausibly did the work is the **7,532 extra characters of schema description** —
a second, worked, defect-focused pass over the same material sitting in the
request, which the model can condition on without ever "running" it. **That is a
prompt-content effect wearing a structural costume, and this arm cannot separate
the two.** Separating them needs an arm that ships the identical 7,532
characters as prose with no required field, which is not run here and is not
claimed.

⚠️ **And the field mix moved in the OPPOSITE direction to arm B's claim.**
Paired, per module: `ontology` **1.2 → 0.9**, `inputs` **2.9 → 3.3**, `asserts`
2.0 → 1.9, `concepts` 5.5 → 5.3. Content moved *out* of `ontology` and *into*
`inputs` — consistent with C5's rewritten headline, single-digit, **INFERRED**.

---

## 5. ⛔ HARM: H-F1 FIRES, AND THE C5 REWRITE SPLIT THE DIFFERENCE

`PREREG.md` §3 rewrote shipped entry 5 (N1) — the one entry MEASURED to
manufacture defects — in two ways: the headline was inverted to lead with the
asymmetry of harm, and `excluded_case` was added as a required field so a
vacuous body could not be written and truthfully certified at once.

**What the rewrite achieved (MEASURED): all four of the in-sample arm's §7 harm
instances are gone.**

| clause | in-sample, after obeying shipped entry 5 | **arm F, under C5** |
|---|---|---|
| `l2126_2404_n016` | `no_moral_ambiguity(S) :- scenario(S)` — the guard true of every scenario | **gone** — arity-1 `input`, guard intact |
| `l4252_4482_n016` | `repeats_user_prompt(R) :- response(R)` ×3 | **gone** — the three are `inputs` |
| `l2821_3040_n017` | `… :- assistant_definition(A)`, the default condition **deleted** | **`default_context` KEPT** in the assert's body |
| `l2474_2554_n004` | `honest_and_forthright(A) :- assistant_conduct(A)` | **gone** |

⛔ **And what it did not achieve: three NEW vacuous bodied rules appeared
elsewhere.** `assistant(A) :- assistant_definition(A)` (`l3239_3382_n002`, a
pure renaming); `identity_capabilities_shareable(A) :- assistant(A)`
(`l1707_1973_n022`); `natural_uncertainty_expression(E) :- assistant_definition(A),
express_uncertainty_naturally(E)` (`l2821_3040_n017`, which also restates its own
name). **H-F1 fires on 3 drafts.**

**The honest reading: the rewrite fixed its own named cases and did not
generalise to the class.** C5's text quotes `no_moral_ambiguity(S) :-
scenario(S)` and `repeats_user_prompt(R) :- response(R)` verbatim; those are the
maximally favourable cells and they are exactly the ones that improved. This is
the same in-sample/out-of-sample gap the prose arms measured, reproduced inside
one arm.

### ⭐ `excluded_case` — the structural half of the fix, and how it failed

`excluded_case` was mandatory on C5 and null elsewhere. Measured:

* **12 of 17 clauses left it null on every cell**, including
  `l3239_3382_n002`, which carries the clearest vacuous rule in the set.
* On the 5 that filled it, **it was answered as "what is this rule's
  exception"**, not as "what case does the body exclude":
  `"programmatic setting"`, `"policy explicitly allows it"`,
  `"explicit_user_instruction"`.
* ⛔ **`l1707_1973_n022` fills C5's `excluded_case` with `"policy explicitly
  allows it"` beside `identity_capabilities_shareable(A) :- assistant(A)` — a
  body that excludes nothing.** That is a **fabricated** excluded case, which is
  exactly what `PREREG.md` R-f named as the failure to watch for.

**The lesson is specific and transferable: a required field constrains the
SHAPE of an answer and cannot constrain its REFERENT.** `excluded_case` was
built on the assumption that a false answer would be hard to produce. It was not
— the model simply answered a nearby, easier question in the same slot, which is
what it did in all six checks.

---

## 6. THE SHAPE CONTRACT — `strict` honouring, MEASURED

`json_schema_strict: true` was UNVERIFIED for this model under an extended
schema. Measured over 17:

* `minItems`/`maxItems` = 6: **17 of 17** honoured.
* `verdict` enum: **17 of 17**, all values legal.
* `entry_id` enum: **17 of 17** legal values, but **2 of 17 emitted
  `C1,C2,C3,C1,C2,C3`** — `l1707_1973_n006` and `l171_426_n022`. `enum` cannot
  express "exactly once each", so those two clauses **never ruled on C4, C5 or
  C6 at all**. `l1707_1973_n006` is one of the clauses whose defect is C6's
  class (GOOD and BAD arms carrying the same `prefer` on the same act with
  contradicting read-backs). **R-h confirmed at 2 of 17.**
* Parse: **17 of 17**. Truncation: **0**. Strip proof: **17 of 17** on all four
  facts.

---

## 7. PREDICTIONS, SCORED

| | prediction | outcome |
|---|---|---|
| **R-a** | F1 = 0 or 1 of 17 | ✅ **0 of 17** |
| **R-b** | ≥80% of cells clean, ≤10 `applies_and_not_handled` | ✅ **100% / 0** — held at the extreme |
| **R-c** ⭐ | ≥15 false cleans | ✅ **21** |
| **R-d** ⭐ | `l4252_4482_n016` reproduces **and** rules C6 clean | ✅ — and in a stronger form: it answered a different question under C6's label |
| **R-e** | C1 transfers, ≥2 glosses materially better | ❌ **REFUTED** — `l3596_3876_n009` still restates 3 of 5 |
| **R-f** | H-F1 fires 0–1; if it fires, an `excluded_case` is fabricated | ❌ on the count (**fires on 3**); ✅ on the mechanism |
| **R-g** | mean raw output ≥ +25% | ✅ **+36%** (4,952 vs 3,645) |
| **R-h** | ≥1 shape break | ✅ **2 of 17** |

Seven of eight predictions held, one refuted. ⚠️ That is a **weak** validation:
R-a/R-b/R-c/R-d are four framings of one underlying event, and they were
predicted from two prior nulls on the same 17 clauses by an adjudicator who had
read them. It is reported because pre-registration is the rule, not because the
hit rate is evidence.

---

## 8. ⚠️ CONTAMINATION — as disclosed in §6 of the pre-registration

I had read all 17 historical adjudications, `ORDERING.md` and the in-sample
`RESULT.md` in full before writing a line of this arm. Four things were done:

1. **The historical defect and its named entry were frozen** in the in-sample
   `PREREG.md` §4 before this arm existed, so recurrence is scored against a
   written prediction. Where my own frozen B7 denominator was too loose, §3
   above corrects it **in my own disfavour** and reports both figures.
2. ⭐ **The verdict-blindness protocol was kept.** For every clause I read the
   narrowed SOURCE TEXT, then the **stripped module**, and wrote that clause's
   defect list — and only then opened `armf_checks`. The run record stores
   `module` and `armf_checks` as separate keys so this is mechanically
   possible, and the transcript order shows the module dump preceding the
   verdict dump. **The 21 false cleans were scored against a defect list already
   written.**
3. **The floor ran first** on every draft.
4. **Direction of the bias, stated: it favours the null.** Knowing each clause's
   history biases me *toward* finding its defect again, which **inflates** the
   recurrence column. So *"7 recurred"* is the weaker reading and *"6 fixed"* is
   the stronger one — which is why §4 exists and is not buried.

**What cannot be fixed:** one adjudicator, no second reader, no answer key.
Novel defects get less attention than predicted ones by construction, so *"6
were fixed"* is a weaker claim than *"7 recurred"*, and the false-clean count
of 21 is a **lower bound** — it counts only defects I found.

---

## 9. WHAT THIS ARM SETTLES, AND WHAT IT DOES NOT

**SETTLED (MEASURED).**

1. ⭐ **Structural coercion does not succeed where instruction failed.** 0 of 17
   defect-free, 15 of 17 conclusion-changing, 9 of 14 coerced-class defects
   still present. The NULL fires on all three of its pre-registered limbs.
2. ⭐ **A required field buys shape compliance, not engagement.** 102/102 cells
   populated, 15/17 perfectly shaped, and on 13 of 17 clauses the cells are a
   decomposition of the span rather than a review of the module. The one field
   ordered specifically to force a look at the finished object — `evidence`
   before `verdict` — was answered by quoting the source document instead.
3. ⭐ **The prose arms' open question now has an answer, and it is a third
   option.** Not *"read and ignored"*, not *"never engaged"*, but **engaged the
   field and not the entry**.
4. **A model that must produce a verdict will produce a clean one.** 102 of 102,
   with `applies_and_not_handled` available and described as the better answer.
   **⛔ This is the finding with the clearest downstream consequence: a
   self-attested check is not evidence, and a pipeline that reads one as a
   quality signal is reading a field that is 100% clean by construction.**
5. **`strict` does not constrain multiplicity.** `enum` + `minItems`/`maxItems`
   cannot express "exactly once each", and 2 of 17 exploited the gap in a way
   that silently dropped half the checks.

**NOT SETTLED.**

* **Whether the 6 fixes are the checks or the 7.5 KB of extra description.**
  This arm cannot separate a structural effect from a prompt-content effect,
  and does not claim to. The separating arm — the identical text as prose with
  no required field — is not run here.
* **Whether the entries would be engaged at a placement other than last.**
  `PREREG.md` §3 argued last placement is the only one that makes the
  measurement falsifiable and named rubber-stamping as its accepted cost. That
  cost was paid in full. A first-placement variant measures something else and
  would need its own pre-registration.
* **Whether a stronger model engages the field.** One model, one temperature.

---

## 10. SPEND AND FOOTPRINT

**$0.03160 measured**, 17 live calls, reconciled from this arm's own turn
records (`out/<id>.json:_arm_f_cost_usd`) as `PREREG.md` §9 required. Cap $0.10,
worst case priced at $0.0577 before signing. Cross-check: the tail of the shared
`semi-formal-experiment/usage.jsonl` carries 60 rows totalling $0.1175 across
**all** concurrent arms — consistent with, and not the source of, the figure
above.

⛔ Nothing under `runs/`, `translation_sample/runs/`, `repair_graveyard/`,
`prompt/`, `schema.py`, `resolve_runs/`, `_debug_gen11/list_in_prompt*`,
`_debug_gen11/ds_opus_loop/`, `_debug_gen11/examples_arm/`,
`_debug_gen11/selfreview_arm/` or `_debug_gen11/retrieval_arm/` was written.
Every byte this arm produced is under `_debug_gen11/forced_verdict_arm/`. **No
git was run; the branch is `d3-worked-example` and was not switched.**
