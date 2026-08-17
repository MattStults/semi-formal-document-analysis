# RESULT — ARM E, per-clause retrieval of the review list

Read `PREREG.md` first, then `RETRIEVAL.md`. Both were signed before the calls;
`RETRIEVAL.md` was signed before the selector's output was compared to any
defect record. Nothing in either was edited afterwards.

**Spend: $0.03184 measured, cap $0.08.** 17 turn-1 calls, one retried after a
provider 503. Raw responses and floor records in `out/<id>.json`,
`out/<id>.raw.json`; prompt provenance in `SHAS.json`.

---

## 0. THE HEADLINE, IN FOUR LINES

1. **NULL on the outcome.** 0 of 17 defect-free, 17 of 17 conclusion-changing,
   43 CC defects against the paired arm's 42. Retrieval did not reduce defects.
2. **The null is MIXED and — for the first time — SPLIT PER CLAUSE.** 8 clauses
   are NULL-A (a retrieved entry named the defect and the model committed it
   anyway); ≥3 are NULL-B (the naming entry was cut by the ranking and the defect
   recurred exactly). Arms A/B/C could not tell these apart on any clause.
3. ⭐ **The most important measurement in this arm is a HARM, and it overturns
   the reading of the whole series.** Removing entry 2 flipped `closure` from
   `unclear` to `cepa` on **7 of the 14 clauses where it was not retrieved**,
   and on **0 of the 3 where it was**. Total `unclear` fell 16 → 2. **The list
   was doing real work all along; arms B/C could not see it because no entry was
   ever absent.** The null is not "instruction cannot reach this content".
4. ⛔ **All four pre-registered harms fired** (H1, H2, H3, H4).

---

## 1. THE ARM IS ATTRIBUTABLE — the assembly gate

`run_arme.py` refuses to send unless its own four shared prompt files, joined by
production code, **plus the full 13.6 KB list**, reproduce arm B/C's system-block
sha256. It does:

```
ASSEMBLY PROVEN: four-file base + FULL list reproduces arm B's sha256 04560828…
```

So arm E's per-clause block differs from the paired arm's in **the list text and
nothing else** — same four files, same order, same `\n\n---\n\n` joiner, same
strip. Every shipped entry body is a verbatim byte slice of arm B's list; the one
exception is E05 (§7). The system block falls from 53,426c to a mean of 44,181c;
the list block from 13,607c to a mean of 4,300c (**−68%**).

Per-clause system shas: `l1_170_n056` `ee8b2d1a9c26`, `l3147_3238_n003`
`ffdb661a33f8`, `l1707_1973_n006` `ef1affc89683`, `l3239_3382_n002`
`e70d457b95be`, `l4252_4482_n016` `5a6c4bb8df55`, `l171_426_n022`
`c8834ce662bf`, `l699_796_n012` `a44ee4c3d933`, `l1001_1107_n005`
`bdb8a619a4ef`, `l1368_1541_n019` `142187650e68`, `l1707_1973_n022`
`daad11dcfb78`, `l2126_2404_n016` `091ed16de799`, `l2474_2554_n004`
`81bebe90b525`, `l2821_3040_n017` `880468e3bb80`, `l3239_3382_n004`
`880468e3bb80`, `l3596_3876_n009` `6d60d55a2e82`, `l3877_3953_n014`
`bdb8a619a4ef`, `l4252_4482_n005` `0ac7867bd838`. Two pairs collide because two
clauses drew the same 2-entry selection — expected, and a check on the builder.

---

## 2. RETRIEVAL QUALITY, REPORTED FIRST (full working in `RETRIEVAL.md`)

| | | |
|---|---:|---|
| **R1 — the entry naming the frozen defect was RETRIEVED** | **6 / 17 = 35%** | ⛔ below the 70% NULL-A threshold |
| **R2 — that entry was ELIGIBLE** (triggered; cut by top-`k`) | **13 / 17 = 76%** | the triggers fire; the *ranking* drops them |
| **R3 — ANY entry the key names was retrieved** | **14 / 17 = 82%** | |

**The recall is lost in the ranking, not the triggers.** On 7 clauses the right
entry fired and lost the top-`k` cut to E01's near-universal prior or E07's broad
hedge trigger; 5 of those 7 are `k = 2` clauses. Only 3 are true trigger failures,
and all 3 are entries whose test is **over the module the drafter writes, not over
the span** (E08's "does your body widen past the qualifier", T3's GOOD/BAD
marker) — **INFERRED: those are not retrievable by any span-side selector.**

⚠️ By `PREREG.md` §6's rule, R1 = 35% makes this a **NULL-B**. §5 below shows the
per-clause evidence is richer than the rule and reports both components.

---

## 3. THE PER-CLAUSE TABLE — MEASURED, span-first, paired against the in-sample arm

`E` = arm E (retrieval). `C` = `../list_in_prompt_insample/` (all 20 entries,
same 17 clauses, same protocol). "cov" = the CC defect was named by an entry
**arm E retrieved**.

| # | clause | retrieved | E floor | C floor | E CC | cov | frozen defect | vs C |
|---|---|---|---|---|---:|---:|---|---|
| 1 | `l1_170_n056` | E02,E09 | inv 1 | clean | 2 | 0 | ✅ not reproduced | ⭐ **better** — C put `forbid` on the excepted branch; E's `oblige` is right-signed |
| 2 | `l3147_3238_n003` | E03,E01,E04 | inv 3 | inv 3 | 2 | 0 | ⛔ verbatim (3 obliges, one body) | worse (cepa×3) |
| 3 | `l1707_1973_n006` | E04,E07,E01,E06 | clean | clean | 2 | **1** | ⛔ 3 of 4 claims reach no rule | worse (C encoded the GOOD arm) |
| 4 | `l3239_3382_n002` | E01,E03 | clean | inv 6 | 3 | 0 | ✅ head-in-own-body gone | ⭐ **better** (floor) |
| 5 | `l4252_4482_n016` | E11,E07 | clean | clean | 2 | **1** | ✅ not reproduced | ⭐ **better** — C's `prefer` states the OPPOSITE of the span |
| 6 | `l171_426_n022` | E09,E07,E08,E01 | inv 2 | clean | 4 | **1** | ⛔ mechanism | worse (⛔ H2) |
| 7 | `l699_796_n012` | E03,E07 | clean | clean | 2 | **1** | ✅ fixed (both arms) | worse (invented `clarification_conversation`) |
| 8 | `l1001_1107_n005` | E01,E04 | clean | clean | 1 | 0 | ⛔ identical | **no difference at all** |
| 9 | `l1368_1541_n019` | E03,E01,E12,E06 | inv 2 | inv 4 | 4 | **1** | ⚠️ substituted | mixed |
| 10 | `l1707_1973_n022` | E02,E07,E01,E12 | inv 2 | inv 1 | 3 | **1** | ⛔ NAF import | ⭐ better (C's `p(P) :- p(P)` tautology gone) |
| 11 | `l2126_2404_n016` | E03,E01,E12 | inv 1 | inv 3 | 3 | 0 | ⛔ mechanism | ⭐⭐ **the vacuous-rule harm is gone** (§7); ⛔ but C's two `forbid`s are dropped |
| 12 | `l2474_2554_n004` | E02,E12,E06,E08 | inv 5 | inv 2 | 4 | **1** | ⛔ reproduced | worse (5 `body: None` ontology entries) |
| 13 | `l2821_3040_n017` | E07,E01 | clean | clean | 3 | **1** | ⚠️ half-fixed | mixed (`default_context` import gone; oblige now fully unconditional) |
| 14 | `l3239_3382_n004` | E07,E01 | inv 2 | clean | 2 | 0 | ✅ conditions now do work | mixed (⛔ `prefer` where C's `permit` was right) |
| 15 | `l3596_3876_n009` | E03,E11 | clean | clean | 2 | 0 | ⛔ **byte-identical** (3 glosses restate their names) | same — ⛔ **the clean NULL-B cell** |
| 16 | `l3877_3953_n014` | E01,E04 | clean | clean | 1 | 0 | ⛔ identical | no material difference |
| 17 | `l4252_4482_n005` | E01,E05 | clean | clean | 3 | 0 | ✅ no blanket ban | ⭐ **better** — C's `oblige` obliges every accent |
| | **TOTAL** | | **8 inv** | **6 inv** | **43** | **8** | **6 ✅ / 2 ⚠️ / 9 ⛔** | |

---

## 4. SCORED AGAINST THE PRE-REGISTRATION

| criterion | threshold | measured | |
|---|---|---|---|
| **T1** defect-free turn-1 drafts | ≥ 2 of 17 | **0 of 17** | ❌ |
| **T2** conclusion-changing rate | ≤ 12 of 17 | **17 of 17** | ❌ |
| **T3** CC defects named by a RETRIEVED entry | ≤ 40% | **8 of 43 = 19%** | ⚠️ **met, but the metric is degenerate — see below** |
| **H1** crowding-out | ≥ 3 | ⛔ **FIRES, 7 of 17** | §6 |
| **H2** obedience harm | ≥ 1 | ⛔ **FIRES, 1** | §6 |
| **H3** entry-driven invention | ≥ 3 | ⛔ **FIRES, 3** | §6 |
| **H4** floor regression | ≥ 3 | ⛔ **FIRES, exactly 3** | §6 |
| mix `asserts`/`ontology` | — | **no shift survives pairing** | §8 |
| mean raw output chars | — | **3,301 vs 3,803 (−13%)** | P-c |

### ⚠️ T3 IS A BAD METRIC AND I AM NOT CLAIMING IT

T3 was pre-registered as the mechanism claim: *"under the signal-to-noise
hypothesis the 83–87% figure should COLLAPSE."* It collapsed, to **19%**. It
means nothing.

**The collapse is arithmetic.** The 83% counted defects named by *any of 18*
entries the model held. The 19% counts defects named by one of a mean of *2.6*.
Shrinking the denominator by 86% drops the coverage fraction whether or not
anything improved — and the absolute defect count did **not** improve: **43 in
arm E against 42 in the paired arm.** Retrieval did not remove defects. It
removed *warnings about* the defects.

This is the same error shape as arm B's retracted mix shift, and it is recorded
here as a **pre-registration defect found in scoring**, not as a result. The
honest reading of T3: **the model committed the same volume of defects with 86%
fewer warnings in front of it, which says the warnings were not what was
preventing them — for the 15 entries other than entry 2.** Entry 2 is the
exception, and it is §6.

---

## 5. ⛔ WHICH NULL — the question prior arms could not answer

**Both, and the arm can name the clauses.**

### NULL-A — the entry was retrieved, uncrowded, and the defect happened anyway
**8 instances, MEASURED.** These are the strongest cells in the arm, because the
model was holding a 4 KB list of 2–4 entries, one of which named exactly the
mistake it then made.

* **#5 `l4252_4482_n016`** — E07 retrieved (*"does the span hedge? … an
  unconditional `oblige` is byte-identical to one whose default was dropped"*).
  Span: *"should **avoid** … and **generally** minimize redundant phrases"*,
  under a NEEDS gloss that says guideline authority is *"guidance rather than a
  strict requirement"*. The draft **quotes that gloss back** and then emits three
  unconditional `forbid`s with `cnpa` closures. *"Generally"* survives in
  `claims` and appears in none of the three read-backs.
* **#13 `l2821_3040_n017`** — E07 retrieved. Span: *"**By default**, the
  assistant should express uncertainty naturally."* Draft: `oblige
  express_uncertainty_naturally(A) :- natural_uncertainty_expression(A)`, no
  defeater, no note. The paired arm at least coined a `default_context` atom.
* **#10 `l1707_1973_n022`** — E07 retrieved. Span: prompts stay private
  *"**by default**"*. Draft's `claims` C2 says "by default"; the `forbid` and its
  read-back do not.
* **#9 `l1368_1541_n019`** — E01 retrieved, including its second half *"does any
  rule's head appear in its own body?"*. Draft:
  `dangerous_situation(S) :- prevent_imminent_harm_rule(R), dangerous_situation(S)`.
* **#3 `l1707_1973_n006`** — E06 retrieved (*"is every entry in `claims`
  actually encoded?"*). Four claims, one assert; C1–C3 reach no rule.
* **#12 `l2474_2554_n004`** — E08 retrieved (*"does each body widen past the
  span's qualifier?"*). Every assert stays gated on `third_party_interaction(A)`,
  including the two the span states generally (*"expected to be honest and
  forthright … avoiding deceptive behavior"*). The frozen defect exactly.
* **#7 `l699_796_n012`** — E03 retrieved (*"does every symbol you COINED trace to
  a substring of the narrowed text?"*). Narrowed text: *"seek clarification when
  instructions might be intended but could cause serious side effects"*. Draft
  coins `clarification_conversation(C)` and makes it the act's argument. No
  *conversation* in the span. The paired arm indexed the act to the instruction.
* **#6 `l171_426_n022`** — E07 retrieved, and its ⛔ half (*"do not invent a
  defeater"*) violated: see H2, §6.

### NULL-B — the naming entry was cut by the ranking and the defect recurred
**≥3 instances, MEASURED.**

* ⭐ **#15 `l3596_3876_n009` is the clean cell.** Frozen defect: *three glosses
  restate their own names*. E01 — the entry that names it, the top scorer in the
  whole list — **triggered at 3 and was cut by `k = 2`**. The draft returns
  `recognizes_strangeness/2 :: "A recognizes the inherent strangeness of X"`,
  `possessing_vast_knowledge_without_first_hand_experience/0 :: "the state of
  possessing vast knowledge without first-hand human experience"`, and
  `being_large_language_model/0 :: "the state of being a large language model in
  general"`. **Three names, re-spaced. The defect recurred byte-for-byte in
  mechanism, and the entry that names it was one rank below the cut.**
* **#2 `l3147_3238_n003`** — E15 (*"or"*) triggered, cut; three `oblige` on one
  identical body, verbatim.
* **#11 `l2126_2404_n016`** — E15's mirror triggered, cut; and E06 not retrieved,
  so the span's *"without resorting to false neutrality or excessive
  qualifications"* is claimed in C2 and encoded nowhere — the paired arm gave it
  two `forbid` asserts.

**Verdict on the split: the null is MIXED, roughly 8 NULL-A to 3 NULL-B on the
clauses where the question is decidable.** That is a real answer to the brief's
question, and it is the first time the series has produced one.

**What it implies, and I want to be precise about the strength:** NULL-A
dominating says that for most of these entries, **putting the naming entry in a
4 KB uncrowded list in front of the model does not stop the defect.**
Signal-to-noise is therefore *not sufficient* as an explanation of arms B/C —
MEASURED, on 8 clauses. But R1 = 35% means the arm did not test the strong form
of the hypothesis, so signal-to-noise is not **refuted** either. A selector with
higher R1 remains the next instrument, and §9 says what it should change.

---

## 6. ⭐⭐ THE HARMS — and the one that reinterprets the whole series

### H1 crowding-out: FIRES, 7 of 17, and it is the arm's most important result

`closure` values, paired, over all 17 clauses:

| | `unclear` | `cepa` | `cnpa` |
|---|---:|---:|---:|
| **C — all 20 entries** | **16** | 11 | 4 |
| **E — retrieval** | **2** | **19** | 7 |

Entry 2 is the entry that governs this field: *"reading its silence as blanket
permission (`cepa`) is a commitment the clause never made — **use `unclear`**"*,
and it names the exact circular reason to watch for.

**E02 was retrieved on 3 of 17 clauses.**

| | E02 retrieved | E02 not retrieved |
|---|---:|---:|
| clauses where arm E has **more** `cepa` than the paired arm | **0 of 3** | **7 of 14** |

The 7: `l3147_3238_n003`, `l171_426_n022`, `l699_796_n012`, `l1368_1541_n019`,
`l2126_2404_n016`, `l2821_3040_n017`, `l4252_4482_n005`. And on
`l3147_3238_n003` the reason the draft gives is the circular one entry 2 quotes:
*"the clause obliges using a tool when confidence is lacking, but is silent about
using a tool when confidence is sufficient; **silence permits that act**"* — ×3.
On the E02-retrieved clauses arm E is never worse and once better
(`l2474_2554_n004`, one `cepa` → `unclear`).

⚠️ **The strength of this, stated honestly.** MEASURED: 7 of 17 drafts regressed
on a conclusion-changing field, and every regression is on a clause where E02 was
absent. The exposed cell has **n = 3**, so the *association* is not established at
this n (Fisher exact on 0/3 vs 7/14 is p ≈ 0.25). What **is** established is the
regression itself, paired and per clause, and that it never occurred where E02
was present.

⭐ **Why this reinterprets arms A/B/C.** Those arms concluded the list does not
transfer, from a null. **They could not have seen entry 2 working, because entry
2 was never absent in any of them.** This arm removed it on 14 clauses and the
field it governs collapsed. **At least one entry of `REVIEW_LIST.md` measurably
changes the draft.** The series' null is a null about *most* entries, not about
instruction.

Two further H1 instances outside `closure`: **#11**, the two `forbid` asserts on
false neutrality / excessive qualifications, present in the paired draft and
dropped here (E06 not retrieved); and **#3**, the `good_response` /
`bad_response` ontology, present in the paired draft and dropped here.

### ⛔ H2 obedience harm: FIRES, 1 clean instance
**`l171_426_n022`.** E07 was retrieved. Its positive half says *"encode the
defeater as a body condition **if the span names one**"*; its ⛔ half says *"if it
names none, say so explicitly — **do not invent a defeater to satisfy this**"*.
The draft coins `higher_level_directs_otherwise/1`, glosses it *"a higher-level
instruction directs that the assistant may engage in the argument"*, and puts it
under NAF in both asserts. **Nothing in the 117-word span names any such
defeater.** The paired arm, holding the same entry among 20, did not do this.
Half the entry was obeyed and the half that forbids the remedy was not — the R57
shape, reproduced under retrieval.

### H3 invention: FIRES, 3
`higher_level_directs_otherwise` (#6, from E07), `clarification_conversation`
(#7, from E03's "give the act an argument" reading), `in_setting/2` +
`handles_task/2` (#14, from E07's "encode the condition"). All three are coined
machinery whose motivation is a retrieved entry rather than the span, and all
three are absent from the paired draft.

### H4 floor regression: FIRES, exactly 3
Clean → invalid on `l1_170_n056`, `l171_426_n022`, `l3239_3382_n004`.
Invalid → clean on `l3239_3382_n002`, `l2126_2404_n016`. Net **8 of 17 invalid
vs 6 of 17** paired (arm A on these clauses: 7 of 17). The worst single draft is
`l2474_2554_n004`, which emitted **five `ontology` entries with `body: null`**.

---

## 7. ENTRY 5 — the fix is UNTESTED, and I will not claim it

`PREREG.md` §3 fixed entry 5 rather than excluding it: a STOP CONDITION plus two
pre-tests were **added**, nothing deleted, forbidding a body that is a universal
type predicate.

**MEASURED: the manufactured class does not appear in any of the 17 arm-E
drafts.** The paired arm produced it plainly on `l2126_2404_n016` —
`no_moral_ambiguity(S) :- scenario(S)` **and**
`no_valid_opposing_perspective(S) :- scenario(S)`, making a clause the span
scoped to *"in scenarios where there's no moral ambiguity"* govern every
scenario. Arm E emits no `ontology` there at all and leaves `no_moral_ambiguity/1`
undefined in `inputs`, which is exactly what the fixed entry prescribes.

⛔ **But E05 was retrieved on only ONE clause, and it was not that one.** The
disappearance is attributable to **entry 5 being absent**, not to the fix
working. **The fix is untested and is reported as untested.** Testing it needs an
arm that ships fixed-E05 on clauses that trigger it.

⚠️ And a vacuous body appeared anyway where E05 was absent:
`avoid_overstepping(R) :- user_authority(R)` (#4),
`natural_uncertainty_expression(A) :- assistant_definition(A)` (#13, also in the
paired draft), and the two in #15. **The class is not gone; the specific
`:- scenario(S)` shape is.**

**Entry 14 was never retrieved on any clause**, by design — its trigger is gated
to its one measured-*safe* branch. It withheld itself on 3 clauses and recorded
why. The cost is real and is scored: on `l1707_1973_n022` entry 14 is the entry
that names the frozen defect, the defect recurred, and the gate is why it was not
in the room. **A gate that prevents a measured harm and loses a retrieval is
still the right trade — but it is a trade.**

---

## 8. THE MIX — PAIRED, and it does not shift

⚠️ Arm B claimed an `asserts`/`ontology` shift that **did not survive pairing and
was retracted.** Not repeated here: every figure is arm E minus the paired arm on
the same clause id.

* `asserts`: E **29** total, C **34**. Per clause: E lower on 4, higher on 0,
  tied on 13.
* `ontology`: E **17**, C **22**. Per clause: E lower on 5, higher on 3, tied on 9.
* Ratio: E 1.71, C 1.55 — but the per-clause sign is **not consistent** (3 of 17
  clauses move the other way on `ontology`).

**MEASURED: no mix shift survives pairing.** The aggregate difference is carried
by four long clauses on which arm E simply wrote less, which is the length effect
(§P-c), not a routing change.

---

## 9. PREDICTIONS, SCORED

| | prediction | outcome |
|---|---|---|
| **P-a** | headline NULL | ✅ **correct** |
| **P-b** | recall ≥ 70%, so the null is NULL-A | ❌ **wrong on R1** (35%); right on R2 (76%). The null is mixed, and I could not have called the split |
| **P-c** | output length falls | ✅ **correct, −13%** (3,301 vs 3,803). Defects did **not** fall with it, so the length confound §P-c warned about does not bite |
| **P-d** | H1 fires | ✅ **correct, and larger than expected** (7 of 17) |
| **P-e** | if any entry transfers it is E01 | ⚠️ **partial** — E01 CAUGHT twice (#4 head-in-own-body gone where the paired arm broke; #10 the paired arm's `p(P) :- p(P)` tautology replaced by two real rules) and MISSED twice (#9 head-in-own-body **with E01 retrieved**; #15 the gloss defect recurred **with E01 cut**). Best single entry, not a reliable one |

---

## 10. ⚠️ CONTAMINATION, AND WHICH WAY IT CUTS

* I knew these 17 clauses are the loop's clauses and that each has a historical
  defect on record **before designing the selector**. That shaped which lexical
  triggers I thought to write. Mitigation: the selector is stdlib-only, id-invariant,
  text-sensitive, and was frozen by sha (`SHAS.json`) before the answer key was
  opened — `verify_blind.py` checks all four mechanically.
* I read the answer key **after the freeze and before the calls**, in order to
  report recall first as the brief required. Having read it, I did not touch the
  selector. **Rejected alternative, by name: a "selector v2" patching the seven
  ranking misses.** It would have scored better and meant nothing.
* **My adjudication of arm E's drafts is NOT blind to these clauses' histories.**
  That cuts toward finding defects I am primed for. Every charge in §3 and §5
  quotes the span or the module text, so a reader can check each against the
  document rather than trusting me. The two figures the verdict most turns on —
  the `closure` table (§6) and the floor counts — are **mechanical counts over
  the JSON, not judgments**, and are reproducible from `out/`.
* n = 17, single-digit cells throughout. The E02-exposed cell is **n = 3**.

---

## 11. VERDICT

**NULL on the outcome; the hypothesis is NOT refuted; and the arm returned one
positive finding that is larger than the null.**

* Signal-to-noise **is not sufficient** to explain arms A/B/C. MEASURED on 8
  clauses where a retrieved, uncrowded entry named the defect the model then
  committed. Cutting the list by 68% and putting 2–4 relevant entries in front of
  the model left the defect count flat (43 vs 42) and the defect-free count at 0.
* Signal-to-noise **is not refuted** either. R1 = 35%: on 7 clauses the naming
  entry fired and lost the `k` cut, and on `l3596_3876_n009` that produced a
  byte-identical recurrence of the exact defect the cut entry names. The strong
  form of the hypothesis has not been tested.
* ⭐ **The finding that outranks both: entry 2 works.** Its removal flipped
  `closure` from `unclear` to `cepa` on 7 of the 14 clauses that lost it, and on
  none of the 3 that kept it. `unclear` fell 16 → 2 across the arm. **This is the
  first measurement in the series showing that an entry of `REVIEW_LIST.md`
  changes the draft**, and it was invisible to every prior arm for a structural
  reason: no prior arm ever removed an entry. The series' null is about *most*
  entries, not about instruction as such.

### What follows, and what does not

* ⛔ **Do not retire the list on arms B/C/E.** The retirement case in
  `ORDERING.md` was built on entries that *found nothing as a critic*. Entry 2's
  value here is as a **drafting guard**, which is a different axis, and this arm
  is the only instrument that has ever measured it. **Any entry proposed for
  retirement should first be run in an ablation of this shape.**
* **The next instrument is an ablation, not a better selector.** The highest
  information per dollar in this whole series turned out to be *removing* an
  entry and measuring what breaks. 18 leave-one-out arms at ~$0.032 each is
  ~$0.57 — and it would score every entry on the axis that matters for drafting,
  which `ORDERING.md` cannot.
* **If a selector v2 is wanted anyway, pre-register it as v2 and report both.**
  The diagnosis is in `RETRIEVAL.md` §3: weight *trigger specificity* above
  *aggregate prior*, and let `k` rise when a narrow trigger fires exactly. That
  is INFERRED, was recorded before the drafting results, and is untested.
* Three entries are **structurally unretrievable** by any span-side selector,
  because their test is over the module the drafter writes rather than over the
  span (E08, T3, and E10's converse check). They cap R1 below 100% for this class
  of instrument.

---

**Signed. Adjudicated span-first, paired, by me.** — adjudicator, 2026-08-16
