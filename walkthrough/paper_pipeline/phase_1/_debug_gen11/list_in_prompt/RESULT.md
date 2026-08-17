# RESULT — does `REVIEW_LIST.md` transfer to the TRANSLATOR?

**Answer: NO. It is a critic's instrument.**

The list, put in the drafting prompt, **measurably changed the drafts and did not
improve them.** 0 of 15 turn-1 drafts were defect-free (baseline 0 of 15); 14 of
15 carried a conclusion-changing defect; and **20 of the 23 conclusion-changing
defects correspond to an entry the translator was explicitly given** — including
two independent reproductions of a failure the prompt describes in full, with its
mechanism and its remedy, one paragraph away.

⚠️ **MEASURED at n = 15, single-digit cells throughout.** Every rate below is a
count out of 15 (or out of 17 for arm A) and none of the differences reported is
statistically separated from noise at this n. The strongest claims here are the
ones that need no rate: a defect the prompt names in its own words is evidence
about that defect whether it happened once or ten times.

**Pre-registration:** `PREREG.md`, written and saved before the first call.
Nothing in `promptsB/` was edited after it. **Spend: $0.03396** measured, 15 live
calls, cap $0.12.

---

## 1. THE PROMPTS

| | system block | sha256 |
|---|---|---|
| **arm A** (production) | 39,959 chars | `3a66c5f54277fbea1c6a8f030435f0c3083d480954b2f6ee3aeef5f1f4e4c34c` |
| **arm B** (this arm) | 53,426 chars | `045608289e6e60a6c7ab327cfb10625a034bd38080af88f0043f757b59517917` |

**Verified byte-exactly: `armB == armA + "\\n\\n---\\n\\n" + 40_review_list.md`.**
The four production files were copied into `promptsB/` and each copy's sha256 was
checked against its original before the config was written:

```
0463449d…  00_task.md            92dbd355…  10_output_format.md
7a88183e…  30_failure_modes.md   a0c12943…  node_worked_example.md
327b1240…  promptsB/40_review_list.md   (the only new byte)
```

⛔ Nothing under `prompt/`, `schema.py`, `resources/` or
`resolve_runs/graph_v2/node_*.md` was modified.

### The three judgment calls, and why

1. **Placement: appended LAST**, after `30_failure_modes.md`. Grounds: everything
   before it stays byte-identical to production, so the entire difference between
   the two arms is one appended block; and recency puts it last before the clause.

2. **All 20 entries kept, reordered by evidence, rewritten in DRAFTER voice, with
   the five zero-yield entries compressed into a labelled tail.** The list as
   written is retrospective (*"Measured: `l1974_2125_n019` compiles to…"*) and
   addressed to someone holding a finished module. Entries were re-stated as
   pre-emission checks and clause ids stripped (they are provenance, and one of
   them — P10's — had already leaked a calibration answer). Each entry carries its
   measured hit-count so the reader can weight it. **This is a confound and it is
   stated: arm B tests "the list, adapted for a drafter", not a raw paste.** A raw
   paste is strictly the weaker version and was not worth the one shot.

3. ⛔ **The `RECOMMENDATIONS.md` (a)-marked prompt fixes were NOT folded in.**
   There are ~30 of them; folding them in makes any result uninterpretable, since
   a gain could not be attributed to the list. `RECOMMENDATIONS.md` also
   contradicts itself (R4 prescribes the `not B` shape N5 forbids), so it would
   have added a second contradictory layer to a list that already contains one
   measured-harmful entry. **The natural follow-up is a pre-registered arm C
   (list + (a) fixes); it was not run and its result is not predicted here.**
   Two corrections *to the list itself* WERE folded in, because shipping a
   known-harmful instruction into a drafting prompt is the one thing that would
   manufacture harm by design: **R57** (N5's asymmetry is polarity-dependent) and
   **R58** (N10 checks the name, not the gloss), plus **R33**'s widening of
   anti-rule 3 and **R65**'s widening of N8. Each is marked in place.

---

## 2. JOB 1 — THE EVIDENCE ORDERING (full table in `ORDERING.md`)

Raw mention counts run 15–17 out of 17 files for all twenty entries: **the metric
has no variance and cannot order anything**, because the protocol required a
report on every entry on every clause. Ordered instead by **distinct clauses on
which the entry produced an actual FINDING**:

| rank | entry | caught | ratified | total | rank | entry | caught | ratified | total |
|---:|---|---:|---:|---:|---:|---|---:|---:|---:|
| 1 | **P8** gloss restates its name | 7 | 5 | **12** | 11 | N3 diff ESTABLISHES | 1 | 3 | 4 |
| 2 | **N7** excepted branch / `cepa` | 3 | 7 | **10** | 12 | N9 count finite verbs | 1 | 2 | 3 |
| 3 | **N10** coined name traces | 4 | 6 | **10** | 13 | P1 `prefer` polarity | 1 | 2 | 3 |
| 4 | **P6** outside the narrowing | 3 | 5 | **8** | 14 | N5 "without X" positive | 0 | 2 | **2** ⛔ |
| 5 | **N1** bodied rule vs constant | 3 | 5 | **8** | 15 | N2 strip the matrix verb | 1 | 1 | 2 |
| 6 | **P3** claim encoded nowhere | 4 | 3 | **7** | 16 | N4 qualifier bounds one item | 0 | 1 | 1 ⛔ |
| 7 | **P7** defeasibility recorded | 4 | 3 | **7** | 17 | P4 disjunction | 0 | 1 | 1 ⛔ |
| 8 | **P5** scope drift | 1 | 6 | **7** | 18 | P10 GOOD/BAD arms | 0 | 1 | 1 ⛔ |
| 9 | **N8** argument order | 2 | 2 | 4 | 19 | **P2** deontic on a non-norm | 0 | 0 | **0** ⛔ |
| 10 | **P9** (corrected) unused coined name | 0 | 4 | 4 | 20 | **N6** "regardless of X" | 0 | 0 | **0** ⛔ |

**Results in their own right:**
* **Five entries carry the mass** — P8, N7, N10, P6, N1 are 48 of 82 findings and
  20 of 27 "caught".
* **Five are retirement candidates.** N6 and P2 found nothing in 17 clauses, and
  P2 is worse than idle (it *endorsed* the decisive defect on
  `l4252_4482_n005`). P10 and P4 scored only on the clause each was written from.
  N4 has 1 finding against 2 recorded mis-directions.
* **N5 is measured to cause harm** (R57: obeyed correctly, it created a clause's
  decisive defect). It survives into arm B only with its polarity condition.
* **The anti-rules score on a different axis.** Anti-rule 2 (`requires-unprovided`
  is correct) prevented false charges on ~8 clauses — the highest-value line in
  the file. Anti-rule 3 inverted a drafted remedy twice.

---

## 3. THE PER-CLAUSE TABLE

15 clauses drawn by fixed stride from the **634** corpus nodes never named by any
`_debug_gen11` artifact (the brief's figure of 581 uses a narrower exclusion
basis; the larger exclusion was used, which is the conservative direction). One
node per line-block, spread across the document. Full adjudications in
`out/<id>.adjudication.md`.

| # | clause | floor | defects | **conclusion-changing** | **CC that the prompt WARNED against** | fresh |
|---|---|---|---:|---:|---|---:|
| 1 | `l1_170_n001` | `translated` 0b | 3 | **0** | — | 2 |
| 2 | `l171_426_n036` | `translated` 0b | 4 | **1** | entry 8 | 1 |
| 3 | `l609_698_n002` | `translated` 0b | 4 | **2** | entries **2**, **10** | 1 |
| 4 | `l797_830_n003` | `translated` 0b | 6 | **3** | entries **13**, **15**, **5**, 10, 6 | 1 |
| 5 | `l1108_1367_n004` | `invalid` 1b | 3 | **1** | entry **5** | 1 |
| 6 | `l1368_1541_n025` | `invalid` 8b | 3 | **2** | entry 8 | 1 |
| 7 | `l1707_1973_n023` | `invalid` **clingo refused** | 4 | **2** | entries **14**, **1** | 1 |
| 8 | `l2126_2404_n010` | `invalid` 2b | 5 | **1** | entry 8 (+14 non-CC) | 1 |
| 9 | `l2405_2473_n007` | `translated` 0b | 3 | **2** | entries **15**, **1** | 1 |
| 10 | `l2821_3040_n001` | `translated` 0b | 2 | **1** | — (graph-forced) | 1 |
| 11 | `l3041_3146_n013` | `invalid` 2b | 6 | **2** | entries **12**, 2, 8 (+14) | 1 |
| 12 | `l3383_3501_n013` | `invalid` 1b | 4 | **1** | entry **1** | 1 |
| 13 | `l3596_3876_n029` | `invalid` 4b | 5 | **1** | entry **12** (+1, 2) | 0 |
| 14 | `l3954_4251_n015` | `translated` 0b | 5 | **3** | entries 1, **8**, 7 | 1 |
| 15 | `l4252_4482_n015` | `invalid` 1b | 4 | **1** | entries **6**, **10** | 0 |
| | **TOTAL** | 8 invalid / 15 | **61** | **23** | **20 of 23 (87%)** | **14** |

---

## 4. THE COMPARISON, SCORED AGAINST THE PRE-REGISTRATION

| criterion | threshold | measured | |
|---|---|---|---|
| **I1** defect-free turn-1 drafts | ≥ 2 of 15 | **0 of 15** | ❌ FAILS |
| **I2** conclusion-changing rate | ≤ 4 of 15 | **14 of 15** | ❌ FAILS |
| **I3** defects NOT covered by a given entry | ≥ 75% | **13%** (3 of 23) | ❌ FAILS badly |
| **H1** crowding-out / floor failures | ≥ 3 | see below | ⚠️ **premise was wrong** |
| **H2** defect caused by OBEYING an entry | ≥ 1 | **0 measured**, 1 adjacent | ✅ did not fire |
| **H3** invention driven by an entry | ≥ 3 | **0** | ✅ did not fire |

**Against the loop's recorded baselines:**

| | arm A (loop) | arm B |
|---|---|---|
| turn-1 drafts that were defect-free | **0 of 15** | **0 of 15** |
| turn-1 `outcome != translated` | 7 of 17 (41%) | 8 of 15 (53%) |
| turn-1 with ≥ 1 schema breach | 7 of 17 (41%) | 7 of 15 (47%) |
| clean floor **while carrying a conclusion-changing defect** | 11 of 22 drafts (all turns) | **5 of 15 turn-1 drafts (33%)** |

⚠️ **H1's premise was WRONG as pre-registered**, and I record it against myself: I
wrote that "the loop's turn-1 breach rate was low". Measured from the loop's own
stored turn records it is **41%**. Arm B's 47% is not separable from that at
n=15. **The floor-failure rate is a NULL, not a harm.**

⚠️ **The floor-blindness figure is not comparable across the two rows** — arm A's
11/22 counts drafts at every turn, arm B's 5/15 counts turn-1 drafts only. It is
reported to show the class is still live, not as a movement.

### The one dimension where a movement is visible — and it is not an improvement

| field, mean entries per module | arm A t1 | arm B |
|---|---:|---:|
| `asserts` | 2.0 | **1.3** |
| `ontology` | 1.2 | **1.8** |
| `acts` | 1.5 | **1.0** |
| `claims` / `concepts` / `requires` / `inputs` | 2.7 / 5.5 / 1.5 / 2.9 | 2.6 / 5.9 / 1.5 / 3.2 |

⭐ **The list demonstrably changed drafting behaviour: content moved OUT of
`asserts` and INTO `ontology`.** That is what entries 5 and 15 ask for. **It did
not reduce defects — it relocated them.** Three of the arm's conclusion-changing
defects (`l797_830_n003` F2, `l2405_2473_n007` F1, `l2126_2404_n010` F1) are
*in the ontology block the list pushed content into.*

⚠️ **P-e was WRONG.** Mean raw output moved 3,645 → 3,854 chars (+6%); the median
**fell** (4,087 → 3,470). A 34% longer prompt did not produce longer output.

**Predictions scored:** P-a ✅ (no effect on I1/I2 — in fact worse than "no
effect" on I2 is unmeasurable, since the baseline was already 0/15). P-b ✅ and
more strongly than predicted (87%, not "a majority"). **P-c ❌ and it is the most
interesting miss: P8 — the entry ranked #1, predicted as the most likely to
transfer because its test is local and syntactic — is the entry the arm violated
most often** (name-restating glosses on clauses 7, 9, 13; head-in-own-body on 12;
and four ungossed borrowed names on 13). **P-d ✅** in the safe direction: H2 did
not fire. P-e ❌.

---

## 5. THE DECISIVE READOUT — defects the prompt named

**20 of 23 conclusion-changing defects (87%) correspond to an entry the
translator was given.** The three that do not are: the PROVIDES/NEEDS collision on
`l2821_3040_n001` (a graph defect, not reachable by instruction), and the two
example-to-norm conversions on `l1368_1541_n025` / `l3041_3146_n013`.

Two of these are worth stating on their own, because they do not depend on any
rate:

* ⛔⛔ **`l797_830_n003`.** The span is *"**We** aim to serve all of humanity and
  will thus operate within applicable legal constraints…"* The prompt's entry 13
  gives, as its worked example, *"**We** are committed to safeguarding privacy" →
  `oblige safeguard_privacy(I)`*. Same pronoun, same sentence shape, entry present
  in the prompt. **The module emitted `oblige operate_within_legal_constraints(A)`
  on the assistant.**

* ⛔⛔ **`l3041_3146_n013` and `l3596_3876_n029`, independently.** Both emitted
  `status: "prefer"` on the act the document says to avoid, with a `read_back`
  that negates it — the compiled rule stating the opposite of the document. The
  prompt's entry 12 names the failure (*"`status` has no negative pole"*), names
  the mechanism (*"the natural move is `prefer X` with a read-back that negates
  it"*), and gives the remedy (*"name the avoidance as the act"*). **Two of
  fifteen clauses reproduced it verbatim.**

* ⛔ **`l1707_1973_n023`.** `not permission_to_disclose(C, R)` — negation-as-failure
  on a *"without X"* condition, forbidden by **production rule 4** and by **list
  entry 14** in the same prompt, with an unsafe variable that made **clingo refuse
  the entire program**. NAF appeared on three of fifteen clauses.

### The one clear positive
⭐ **`l3383_3501_n013` — entry 9 worked.** The borrowed `authority_levels_hierarchy/2`
arrived from the graph with **no argument order stated**, and the module wrote one
into its gloss (*"the first argument is a level that outranks the second"*) and
then used it correctly. The loop measured that a total inversion here *"passes
every deterministic check we have"*. **This is the single unambiguous case in 15
clauses of a list entry improving a draft.** It is one clause, on the entry ranked
9th, and it is n = 1.

Two smaller positives: entry 15's disjunction test was answered correctly on
`l1108_1367_n004` (three permits on three bodies, not three obliges on one), and
entry 5's document-fact exception was applied correctly on `l2821_3040_n001`.

### The largest FRESH class the arm found
⭐ **A borrowed `NEEDS` gloss stamped `licence: textual, cites: <this node>` — on
10 of 15 clauses.** The node hands over a gloss that *another* node establishes,
and the module cites *itself* for it. `00_task.md` calls a manufactured citation
*"the single worst failure available here"*. **Nothing in the 20 entries asks what
licence a borrowed gloss carries.** This is not a translator failure so much as a
prompt gap, and it is the clearest new item this arm produced.

---

## 6. VERDICT

**The review list does not transfer to the translator. It is useful to a critic
and not to a drafter.**

The evidence, in order of strength:

1. **87% of conclusion-changing defects were explicitly warned against.** A list
   whose entries are being violated at that rate is not failing to *cover* the
   defect space — it covers it well. It is failing to *act*.
2. **Two independent clauses reproduced entry 12's measured failure verbatim**,
   and one reproduced entry 13's worked example almost sentence-for-sentence. No
   rate is needed to read those.
3. **The list did change drafting behaviour** — `asserts` down 35%, `ontology` up
   50% — **and the defects moved with it.** So this is not "the model ignored the
   prompt"; it is "the model followed the prompt and the defects were not
   reachable that way."
4. **0 of 15 defect-free, against a baseline of 0 of 15.** No movement on the one
   number the experiment exists to move.

⚠️ **What this does NOT show.** It does not show the list is worthless — its value
as a critic's instrument is measured elsewhere and stands. It does not show a
better-adapted list would fail; only that this adaptation of it, at 13.5 KB, did.
And it does not establish a rate for anything: n = 15, cells of 1–3, historical
control on different clauses.

⭐ **What follows from a null of this shape.** The defects that dominate this arm
are structural, not knowledge-shaped: **an unlinked body variable** (3 clauses),
**a `status` field with no negative pole** (2 clauses), **negation-as-failure
where the schema offers nothing else** (3 clauses), **coextensive `ontology`
heads** (2 clauses), and **a licence with no rule for borrowed glosses** (10
clauses). Each of these is a place where the model wrote the only thing the
format allowed, or wrote a thing the format does not check. **A prompt cannot
reach them. The argument moves to the schema and to the graph findings** —
exactly the disposition `PREREG.md` recorded in advance for a null.

⛔ **Nothing in `promptsB/` was tuned after these results and no second variant
was run.** A second variant would have to be pre-registered as such and both
reported.
