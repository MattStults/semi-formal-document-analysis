# RETRIEVAL QUALITY — measured and signed BEFORE any live call

⚠️ **Order of operations, which is the whole point of this file.** The selector
was written, run over all 17 clauses, and **frozen by sha256 in `SHAS.json`**
(`selector_sha256`, and a per-clause `system_sha256` for every prompt) *before*
`../list_in_prompt_insample/RESULT.md` — the answer key — was opened. The
recall table below is scored against that answer key **after** the freeze. No
trigger, no weight and no `k` rule was touched afterwards.

⛔ **And none will be.** Having now read the key, any edit I make to the
selector would be shaped by knowing which entry named which defect — the exact
answer-key leakage the brief forbids. **Rejected alternative, by name: writing a
"selector v2" now that patches the misses below.** It would score better and
mean nothing. v1 runs as frozen.

---

## 1. Is the selector blind? — MEASURED, `verify_blind.py`

```
[PASS] imports are stdlib-only and inert  ['argparse','hashlib','json','os','re','sys']
[PASS] every read-open targets the corpus or promptsE/entries/
[PASS] no code reference to 'turns.md' / 'lessons.md' / 'adjudication' /
       'RESULT' / 'flip_verdicts' / 'feedback' / 'list_in_prompt' / 'defect' /
       'insample' / 'ORDERING'
[PASS] renaming the clause changes no selection          (id-invariance)
[PASS] perturbing the span text changes the selection    (9/17 clauses)
[PASS] every clause gets 2-4 substantive entries
BLIND. selector uses no field derived from a historical adjudication.
```

The only history the selector sees is `PRIOR` — the `ORDERING.md`
"distinct clauses with a finding" column. Those are **20 numbers, aggregate over
17 clauses, identical for every clause**, so they cannot encode which defect any
particular clause had. Everything else is a lexical test over that clause's own
narrowed span and node header.

## 2. What it selected — MEASURED

Mean shipped list **4,300 chars vs 13,607** for the full list: a **68%
reduction**, and the assembled system block falls from 53,426c to a mean of
44,181c. Prompts are in `promptsE/<clause_id>/40_review_list.md`.

| clause | words | k | selected |
|---|---:|---:|---|
| `l1_170_n056` | 15 | 2 | E02, E09 |
| `l3147_3238_n003` | 36 | 3 | E03, E01, E04 |
| `l1707_1973_n006` | 145 | 4 | E04, E07, E01, E06 |
| `l3239_3382_n002` | 17 | 2 | E01, E03 |
| `l4252_4482_n016` | 19 | 2 | E11, E07 |
| `l171_426_n022` | 117 | 4 | E09, E07, E08, E01 |
| `l699_796_n012` | 13 | 2 | E03, E07 |
| `l1001_1107_n005` | 7 | 2 | E01, E04 |
| `l1368_1541_n019` | 48 | 4 | E03, E01, E12, E06 |
| `l1707_1973_n022` | 67 | 4 | E02, E07, E01, E12 |
| `l2126_2404_n016` | 27 | 3 | E03, E01, E12 |
| `l2474_2554_n004` | 71 | 4 | E02, E12, E06, E08 |
| `l2821_3040_n017` | 11 | 2 | E07, E01 |
| `l3239_3382_n004` | 22 | 2 | E07, E01 |
| `l3596_3876_n009` | 23 | 2 | E03, E11 |
| `l3877_3953_n014` | 6 | 2 | E01, E04 |
| `l4252_4482_n005` | 22 | 2 | E01, E05 |

Entries retrieved at least once: E01 (12×), E07 (7×), E03 (6×), E04 (4×),
E12 (4×), E02 (3×), E06 (3×), E08 (2×), E09 (2×), E11 (2×), E05 (1×).
**Never retrieved on any clause: E10, E13, E14, E15, T1, T2, T3** — 7 of 18.
E14 was *actively withheld* on 3 clauses by its polarity gate (§5).

---

## 3. ⛔ RECALL — THE NUMBER THAT DECIDES WHETHER A NULL IS INTERPRETABLE

Answer key: the "entry that names it" column of
`../list_in_prompt_insample/RESULT.md` §3, whose **bolded** entry is the one
naming that clause's *frozen* conclusion-changing defect.

| # | clause | frozen defect | entry that names it | selected | primary retrieved? |
|---|---|---|:--:|---|:--:|
| 1 | `l4252_4482_n016` | `prefer` on the acts the span says to avoid | **12** | E11, E07 | ❌ *(E12 triggered, cut)* |
| 2 | `l3147_3238_n003` | three `oblige` on one body for an "or" | **15** | E03, E01, E04 | ❌ *(E15 triggered, cut)* |
| 3 | `l2126_2404_n016` | coextensive `ontology` heads, one body | **15** mirror | E03, E01, E12 | ❌ *(E15 triggered, cut)* |
| 4 | `l3239_3382_n004` | the span's two conditions do no work | **8** | E07, E01 | ❌ *(E08 never triggered)* |
| 5 | `l1368_1541_n019` | `S` names two things | **1** | E03, **E01**, E12, E06 | ✅ |
| 6 | `l4252_4482_n005` | chain inverts into a blanket accent ban | **3** | E01, E05 | ❌ *(E03 triggered, cut)* |
| 7 | `l1_170_n056` | exception unattached to the obligation | **2** | **E02**, E09 | ✅ |
| 8 | `l3239_3382_n002` | `overstepping(A)` head in its own body | **1** | **E01**, E03 | ✅ |
| 9 | `l3596_3876_n009` | three glosses restate their own names | **1** | E03, E11 | ❌ *(E01 triggered, cut)* |
| 10 | `l3877_3953_n014` | document relation in `inputs` | **5** | E01, E04 | ❌ *(E05 triggered, cut)* |
| 11 | `l1001_1107_n005` | `rule_under_heading/2` in `inputs` | **5** | E01, E04 | ❌ *(E05 triggered, cut)* |
| 12 | `l2474_2554_n004` | `third_party_interaction` inverts the conjunction | **8** | E02, E12, E06, **E08** | ✅ |
| 13 | `l2821_3040_n017` | unconditional manner duty | **8** | E07, E01 | ❌ *(E08 never triggered)* |
| 14 | `l1707_1973_n022` | exception imported into the tenor by NAF | **14** | E02, E07, E01, E12 | ❌ **withheld by design** |
| 15 | `l171_426_n022` | `higher_level_instruction` hardcoded to root | **8** | E09, E07, **E08**, E01 | ✅ |
| 16 | `l1707_1973_n006` | three of four behaviours reach no rule | **tail P10** | E04, E07, E01, E06 | ❌ *(T3 never triggered)* |
| 17 | `l699_796_n012` | modality survives on one conjunct | **7** | E03, **E07** | ✅ |

### The three figures, all MEASURED

| | | |
|---|---:|---|
| **R1 — primary entry RETRIEVED** | **6 / 17 = 35%** | the entry naming the frozen defect was shipped |
| **R2 — primary entry ELIGIBLE** (triggered, may have been cut by `k`) | **13 / 17 = 76%** | the trigger fired; the *ranking* dropped it |
| **R3 — ANY listed entry retrieved** (primary or the secondaries the key names) | **14 / 17 = 82%** | some entry from the relevant set was shipped |

⛔ **R1 = 35% is below the 70% threshold `PREREG.md` §6 set for NULL-A.** Stated
plainly, in advance of the drafting results: **if arm E returns a null, it is a
NULL-B — "retrieval is the bottleneck", the signal-to-noise hypothesis is
UNDETERMINED, and the next instrument is a better selector.** It will not be
reported as evidence that instruction cannot reach this content.

The transfer branch is unaffected and remains live: if the defect rate falls at
R1 = 35%, that is a *strong* positive, because it would mean retrieval helped
while retrieving the naming entry only a third of the time.

### ⭐ Where the recall is lost — MEASURED, and it is not where I expected

**R2 (76%) minus R1 (35%) = 7 clauses where the right entry FIRED and was then
cut by the top-`k` ranking.** The triggers are not the weak part. The **ranking**
is: `score = trigger_bonus + prior × 2/12` lets E01's near-universal +2 prior and
E07's broad hedge trigger crowd out an entry whose trigger is narrow and exact
(E15's literal `or`, E12's literal `avoid`, E05's `inputs` shape). Five of the
seven losses are on `k = 2` clauses.

⚠️ **INFERRED, not measured, and deliberately NOT acted on:** a selector that
weighted *trigger specificity* above *aggregate prior*, or that let `k` rise when
a narrow trigger fires exactly, would plausibly recover most of those seven. That
is a **hypothesis for a pre-registered selector v2**, recorded here so it is on
the record as having been thought of *before* the drafting results — and it is
**not** being run in this arm.

Only **3 of 17** clauses are true trigger failures (#4, #13 — E08's "widens past
the qualifier" test has no lexical fingerprint in the span, since the defect is
about the *body the drafter writes*, not about the span's wording; and #16, whose
naming entry T3 fires only on a literal GOOD/BAD marker that this span does not
carry). **INFERRED: an entry whose test is over the MODULE rather than over the
SPAN is not retrievable by a span-side selector at all.** That is a structural
limit of this instrument and it caps R1 below 100% for any lexical selector.

## 4. ⚠️ WHAT THE RECALL FIGURE DOES *NOT* SAY

R1 is scored against the **frozen** defect — the one defect per clause that
arm C's pre-registration named in advance. The in-sample arm recorded **42
conclusion-changing defects over the 17 clauses**, of which **35 (83%) were named
by some entry**. R1 therefore measures retrieval against 17 of those 42, not all
42. The all-42 analogue — *the fraction of arm E's CC defects covered by a
RETRIEVED entry* — can only be computed after adjudicating arm E's own drafts,
and is reported in `RESULT.md` as the number that separates "retrieval helped"
from "retrieval missed".

## 5. Entry 5 and entry 14 — the two measured-harm entries

* **E05 was FIXED, not shipped as written** (`PREREG.md` §3). A STOP CONDITION
  and two pre-tests were **added**; nothing was deleted. It was retrieved on
  exactly **1** clause (`l4252_4482_n005`).
* **E14 was never retrieved, on any clause** — not by accident. Its trigger is
  polarity-gated to its one measured-*safe* branch (an absence-phrase inside a
  **permission**); on the 3 clauses where an absence-phrase appeared inside an
  obligation or a default, the selector **withheld it and recorded why**. Note
  the cost, honestly: clause 14's frozen defect is the one entry 14 names, so
  this deliberate withholding is one of the 11 R1 misses. **A gate that
  prevents a measured harm and loses a retrieval is still the right trade**, but
  it is a trade and it is scored as one.

---

**Signed before the first live call.** — adjudicator, 2026-08-16
