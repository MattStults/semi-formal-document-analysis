# TRANSLATION_REPAIR_CENSUS.md

**What this is.** Every translation run on disk, mined for repair rounds. A repair
round is one paid extra call: `translate.py` hands the model back its own module with
`attempt N failed these checks: …` and pays for another completion. The graph side ran
the equivalent census and drove buried failures 72 → 25 → 17 by finding the cause of
each class rather than paying for retries. This is the translation-side twin.

**Built 2026-08-14. Zero API spend — every number below is re-analysis of bytes already
on disk.** Reproduce with:

```
.venv/bin/python translation_repair_census.py            # all generations
.venv/bin/python translation_repair_census.py --list-gens
.venv/bin/python translation_repair_census.py --gen -1   # the live prompt
.venv/bin/python translation_fix_sim.py                  # replay + fix simulation
```

Nothing under `runs/` or `repair_graveyard/` was written to; a batched corpus run was
in flight throughout and its directories were read only.

---

## 0. The headline

| | |
|---|---|
| clauses translated, across all runs | **191** |
| model calls those clauses cost | **435** |
| of which repair rounds (paid EXTRA calls) | **244 — 56% of all calls** |
| share of translation spend that is repair | **60%** ($0.4825 of $0.8005) |
| under the CURRENT prompt (generation 11) | **87 rounds over 71 clauses — 1.23 per clause** |
| repair rounds killed by the fix plan (measured by replay) | **58%** |

More than half of every dollar spent translating this document is spent translating it
again. That is the systemic cost the census exists to attack.

---

## 1. Sources and method

### 1.1 What was mined

| source | what it holds |
|---|---|
| `runs/*/` (14 dirs) | flat-clause translation runs, 2026-08-07 → 08-09 |
| `resolve_runs/graph_v2/translation_sample/runs/*/` (14 dirs) | graph-node runs, 08-10 → 08-14 |
| `repair_graveyard/*/` | flat-clause graveyard entries |
| `resolve_runs/graph_v2/translation_sample/repair_graveyard/*/` (93 entries) | graph-node graveyard, including the 48 `_cleared_*` entries with their `findings.json` and written `VERDICT.md` |

Graveyard `transcript.json` files are byte copies of the run transcripts, so the miner
deduplicates on transcript content hash before counting. 285 transcript files reduce to
191 distinct clause attempts.

### 1.2 The unit of measurement

Each repair round is located in a transcript as a user turn matching

```
attempt N failed these checks:
  - [check_id] where: message
  ...
Fix every one of them. Return the corrected module, complete.
```

The assistant turn that follows it is the paid call. `entry.json` in the graveyard
independently records `attempts` and agrees with the transcript count on every entry
checked.

### 1.3 The taxonomy came from the messages, not from guesses

The 557 deduplicated finding lines were bucketed by `check_id` plus message shape,
iterating until the residual `OTHER` bucket was empty. `check_id` alone is useless here:
**518 of the 557 lines carry `check_id: schema-breach`**, one bucket for eighteen
different defects (the remainder: 22 `clingo-error`, 13 `requires-unprovided`,
2 `closure-missing`, 2 `unresolved-reference`). The message shape is the discriminator.
The taxonomy is in `translation_repair_census.py:TAXONOMY` as (family, class, regex),
first match wins.

### 1.4 The cost model, and how it was checked

Each round is priced from its own transcript:

```
cost = (prompt_chars/cpt · $0.14 + completion_chars/cpt · $0.28) / 1e6
prompt_chars = |prompt_system.txt as sent on that run| + all turns up to the repair message
cpt          = 3.74 chars/token, the MEDIAN of content_chars/completion_tokens
               over the 708 priced together-deepseek-v4-flash rows in usage.jsonl
```

`prompt_system.txt` matters: it is 34–38 kB and is resent on every repair round, so it
dominates the input side. Prices are the `[0.14, 0.28]` per-Mtok pair stamped on every
recorded row.

**Validation.** The model prices 435 calls it can see; `usage.jsonl` prices the ones
that were actually billed:

| | |
|---|---|
| modelled mean call | $0.00184 |
| recorded mean call (708 rows) | $0.00166 |
| ratio | **1.11×** pooled · **1.16×** over generation 11 alone |

The model runs 11–16% high, most likely because 71% of recorded input tokens land as
`cached_input_tokens` and the arithmetic here does not discount them. **Every dollar
figure below is therefore an upper bound within ~16%.** The bias is one-directional and
applies to every row, so cost *shares* between classes are unaffected — and the plan is
ranked on shares and on round counts, not on absolute dollars.

### 1.5 Attribution

A round is caused by every class present in it. Its cost is split evenly across the
distinct classes in that round, so the class cost column sums to total repair spend and
nothing is double counted. `rounds` counts rounds in which the class appears — those
columns legitimately sum to more than the round total.

### 1.6 Generations: runs are grouped by the prompt they were actually sent

The prompt changed eleven times across these runs, so a single pooled table would
average a live failure together with one that has been extinct for four days. Runs are
grouped by `sha256(prompt_system.txt)` — the bytes the model saw — not by git history,
because a run's system block is assembled from several files chosen by its own config.

```
gen  3 dfccbc4a  runs= 3 clauses=  3 rounds=  3  r/clause=1.00  20260807-154504 …
gen  4 8e2defe2  runs= 2 clauses= 10 rounds= 14  r/clause=1.40  20260807-171729 …
gen  5 4943e853  runs= 1 clauses=  8 rounds=  8  r/clause=1.00  20260807-174848
gen  6 0ea7852e  runs= 4 clauses= 12 rounds=  7  r/clause=0.58  20260809-114002 …
gen  7 2926e213  runs= 2 clauses= 30 rounds= 52  r/clause=1.73  20260810-203553 …
gen  8 e9a6c4a2  runs= 1 clauses= 15 rounds= 16  r/clause=1.07  20260810-212409
gen  9 88aea33e  runs= 1 clauses= 14 rounds= 16  r/clause=1.14  20260810-213043
gen 10 ab3cb944  runs= 3 clauses= 28 rounds= 41  r/clause=1.46  20260810-214234 …
gen 11 5ff9daf7  runs= 7 clauses= 71 rounds= 87  r/clause=1.23  20260810-225427 … 20260814-173322
```

**Generation 11 is the live prompt** and carries 71 of the 191 clauses.

---

## 2. The census — all generations

```
family    class                           rounds   share  findings     cost$  clauses
-------------------------------------------------------------------------------------
SAFETY    unsafe-variable                     43  17.6%        88    0.0765       31
READBACK  readback-slot-arity                 40  16.4%        65    0.0699       27
DECLARE   undeclared-body-name                47  19.3%        73    0.0683       29
SYNTAX    asp-syntax-refused                  22   9.0%        22    0.0402       16
ACTS      act-not-in-acts                     30  12.3%        39    0.0366       25
IDFORM    not-a-term                          22   9.0%        35    0.0337       19
GLOSS     borrowed-without-gloss              28  11.5%        41    0.0328       20
IDFORM    forbid-body-not-bare-name           16   6.6%        22    0.0229        9
IDFORM    concept-name-carries-arity          10   4.1%        41    0.0146        8
CLOSURE   closure-missing                     17   7.0%        17    0.0138       12
PROV      citation-not-in-corpus              11   4.5%        41    0.0136        9
SYNTAX    asp-body-unparseable                 8   3.3%        11    0.0118        8
PROV      clause-id-mismatch                  12   4.9%        12    0.0104        9
CLOSURE   closure-ungoverned                  15   6.1%        15    0.0083       10
IDFORM    inputs-entry-not-name-arity          4   1.6%         4    0.0056        4
MINOR     abstain-with-content                 3   1.2%         4    0.0052        3
MINOR     toggleable-licence-mismatch          3   1.2%         3    0.0045        3
MINOR     requires-inputs-overlap              5   2.0%         5    0.0040        3
MINOR     empty-translation                    2   0.8%         2    0.0030        2
LINK      requires-unprovided                  3   1.2%        13    0.0027        2
MINOR     empty-body-not-null                  2   0.8%         2    0.0024        2
LINK      unresolved-reference                 2   0.8%         2    0.0018        1
```

**This table is the wrong one to plan from.** Three of its top eight rows are already
extinct. It is here because the extinctions are the evidence that the method works.

---

## 3. The trend, and what it proves

Rounds per class, per generation:

```
class                         g3  g4  g5  g6  g7  g8  g9  g10 g11
undeclared-body-name          1   2   3   0   3   2   1   10  25
unsafe-variable               0   2   0   0   11  1   1   6   22
readback-slot-arity           0   5   0   4   2   2   2   7   18
borrowed-without-gloss        0   0   0   0   2   0   0   3   23   ← check ADDED 08-10
act-not-in-acts               0   0   0   1   6   0   1   5   17
closure-ungoverned            0   0   0   0   0   0   0   0   15   ← surfaces once acts are fixed
closure-missing               0   1   1   0   0   2   0   1   12
clause-id-mismatch            0   0   0   0   3   1   0   0   8
citation-not-in-corpus        0   0   0   0   5   1   0   0   5
─────────────────────────── EXTINCT UNDER THE LIVE PROMPT ───────────────────────────
not-a-term                    2   1   1   0   2   5   9   1   1
forbid-body-not-bare-name     1   0   1   0   4   1   5   4   0
concept-name-carries-arity    0   0   0   0   2   3   2   3   0
asp-syntax-refused            0   2   2   1   13  0   0   3   1
```

### 3.1 Two classes were killed outright, and by the predicted lever

`not-a-term`, `forbid-body-not-bare-name` and `concept-name-carries-arity` are one
defect: the model writes a predicate in the wrong one of its three renderings (`name`,
`name/arity`, `name(Var)`). They peaked at gen 8–10 (5, 9, 4, 3 rounds) and are at
**zero or one under gen 11**. What changed is the notation table added to
`resolve_runs/graph_v2/node_worked_example.md`:

```
| `requires` / `inputs`                  | name/arity              | best_intentions_bias/1 |
| `acts`, and `act` inside an assert     | term with its variable  | apply_default(D)       |
| `closure.act_class`, `forbid_body.head`| bare functor name       | apply_default          |
```

A table that enumerates every slot and its rendering took a 43-round family to two.
That is the strongest single piece of evidence in this census, and it is the reason the
fix plan reaches for *enumeration and enforcement* rather than more prose.

`asp-syntax-refused` fell from 13 rounds (gen 7) to 1, killed by `asp_id()` aliasing in
`node_corpus.py` — graph ids like `L527-796_n012` are not valid ASP constants.

### 3.2 On a held-constant clause set, generation 11 is improving

Three runs translate the identical 15-clause sample:

| run | rounds / clause |
|---|---|
| 20260810-225427 | 2.27 |
| 20260810-234100 | 1.86 |
| 20260812-133317 | **0.67** |

The system block is byte-identical across all three (that is what makes them one
generation), so the improvement came from the **per-request adapter** — the
ESTABLISHES / PROVIDES / NEEDS / CITATION scaffolding `node_corpus.py` writes into the
user block. Naming the predicates and the one legal citation per request moved the
number that four prompt rewrites had not.

⚠️ The other two gen-11 runs translate *different* clause sets (`20260812-090344` a
fresh 15 at 0.93; `20260814-163457` the first 12 nodes of the corpus run at 0.25) and
are **not** comparable points on this curve. `20260814-173322` was still in flight and
contributed no transcripts.

---

## 4. The census that matters — generation 11, the live prompt

71 clauses · 158 calls · **87 repair rounds (55% of all calls)** · repair spend $0.1838
of $0.3034 (**61%**).

| # | family | class | rounds | share of rounds | findings | cost $ | clauses |
|---|---|---|---|---|---|---|---|
| 1 | SAFETY | `unsafe-variable` | 22 | 25.3% | 40 | **0.0439** | 12 |
| 2 | READBACK | `readback-slot-arity` | 18 | 20.7% | 23 | **0.0341** | 10 |
| 3 | DECLARE | `undeclared-body-name` | 25 | 28.7% | 51 | **0.0278** | 14 |
| 4 | GLOSS | `borrowed-without-gloss` | 23 | 26.4% | 36 | **0.0232** | 15 |
| 5 | ACTS | `act-not-in-acts` | 17 | 19.5% | 26 | **0.0122** | 13 |
| 6 | CLOSURE | `closure-ungoverned` | 15 | 17.2% | 15 | 0.0083 | 10 |
| 7 | PROV | `citation-not-in-corpus` | 5 | 5.7% | 23 | 0.0067 | 4 |
| 8 | PROV | `clause-id-mismatch` | 8 | 9.2% | 8 | 0.0065 | 5 |
| 9 | CLOSURE | `closure-missing` | 12 | 13.8% | 12 | 0.0059 | 7 |
| 10 | MINOR | `requires-inputs-overlap` | 4 | 4.6% | 4 | 0.0017 | 2 |
| | | *everything else (8 classes)* | ≤2 each | | | 0.0135 | |

**Top classes by cost, which is the ranking asked for:**

1. **`unsafe-variable`** — $0.0439, 22 rounds (SAFETY)
2. **`readback-slot-arity`** — $0.0341, 18 rounds (READBACK)
3. **`undeclared-body-name`** — $0.0278, 25 rounds (DECLARE)
4. **`borrowed-without-gloss`** — $0.0232, 23 rounds (GLOSS)
5. **`act-not-in-acts` + `closure-*`** — $0.0264 combined, 44 round-appearances (ACTS/CLOSURE — one defect cluster, see §5.3)

Note the ranking by cost differs from the ranking by count: `undeclared-body-name`
appears in the most rounds (25) but costs less than `unsafe-variable` (22 rounds),
because unsafe-variable rounds sit later in longer transcripts and each resend more
context.

---

## 5. What each class actually is

Diagnosis, quoted instruction and proposed lever are in **`TRANSLATION_FIX_PLAN.md`**.
The one-line version:

### 5.1 `unsafe-variable` — `ontology` used as a declaration list
Every gen-11 instance is an `ontology[i].atom` carrying a variable nothing binds:
`u18_user(U)`, `teen_user(U)`, `stay_in_bounds_principle(P)`, `limits_taxonomy(T)`,
`implicit_bias_default(D)`. The model is saying *"this predicate exists"* — which is
what `concepts` is for. **74% of these atoms are already declared in `concepts` with the
same name and arity**, so the ontology entry is a duplicate that also makes clingo
refuse the whole file.

### 5.2 `readback-slot-arity` — `read_back_slots` read as "this rule's variables"
**61 of 65 findings are one shape: the sentence contains no `%` at all and the slot list
is non-empty.** The model writes a complete English sentence naming its subject in
prose, then fills the slot list with the assertion's variables:

```json
{"read_back": "for U18 users, the assistant cannot engage in immersive romantic roleplay",
 "read_back_slots": ["U"]}
```

Nothing is ambiguous here — the format rules already declare the empty list correct for
this sentence.

### 5.3 `act-not-in-acts` + `closure-missing` + `closure-ungoverned` — one defect
The module's act vocabulary does not line up across three lists that must agree:
`acts`, `asserts[].act`, and `closure[].act_class`. Fixing one surfaces the next —
which is why `closure-ungoverned` appears for the first time in gen 11, after
`act-not-in-acts` started being reported.

### 5.4 `borrowed-without-gloss` — bookkeeping in two places
Names correctly listed in `inputs`/`requires` (`assistant_or_tool_message/1`,
`quoted_or_untrusted_text/1`, `multimodal_data/1`) with no matching `concepts` entry.
The declaration and its meaning live in two different lists and the second is forgotten.

### 5.5 `undeclared-body-name` — the one that needs a decision
A body literal (`teen`, `request`, `assistant`, `first_person_roleplay`) is in none of
`ontology` / `requires` / `inputs`. Choosing the bucket is a real content decision and
the check's own text says an undeclared name "cannot be told apart from a typo".
**This class must keep costing a call until the grammar changes shape.**

---

## 6. Two systemic effects the per-class table hides

### 6.1 Masking — round 1 is told less than the truth

`schema.Module._coherent` is an `after` validator: it runs only once every sub-model has
validated. So **any notational breach in one sub-model suppresses the entire coherence
layer** — the undeclared names, the missing glosses, the missing closures. The model is
told about a mis-rendered concept name on round 1, fixes it, and only then learns about
the four coherence breaches that were behind it.

Measured over the 114 repaired clause chains: **only 61% of a chain's eventual breach
classes are visible at round 1**, and only 54% of chains have their whole breach set on
the table at the first repair. Running `translate_autofix` before validating removes the
notational breaches without a call and lets `_coherent` report on round 1, lifting those
to 65% and 61%.

### 6.2 Repair-induced regression — fixing A breaks B

Of the 124 repair rounds after the first, **65 (52%) carry a class no previous attempt
had.** The model is not converging; it is trading defects:

| introduced by a repair | count | | persists across a repair | count |
|---|---|---|---|---|
| `undeclared-body-name` | 11 | | `undeclared-body-name` | 18 |
| `act-not-in-acts` | 11 | | `readback-slot-arity` | 13 |
| `closure-missing` | 9 | | `unsafe-variable` | 12 |
| `unsafe-variable` | 9 | | `borrowed-without-gloss` | 8 |
| `borrowed-without-gloss` | 8 | | `forbid-body-not-bare-name` | 7 |

This is the mechanism behind the user's framing — *errors that are fixed still increase
costs systemically*. A repair prompt that reports a partial breach set invites a rewrite
that breaks something else, and each exchange is billed. It is also why the plan is
ranked by **rounds killed** and not by findings removed: removing four of a round's five
findings saves nothing at all.

### 6.3 Attempts, and where the tail is

```
attempts per clause (calls):  1 → 73 clauses   2 → 38   3 → 58   5 → 22
```

22 clauses burned the full five attempts. Those 22 account for 88 of the 244 repair
rounds — **36% of all repair spend sits in 12% of clauses.**

---

## 7. Replay: the taxonomy is checkable, not asserted

Every stored failing module was re-run through `schema.validate_all` as it stands today.

**For generation 11: the census classes are re-derived from the stored artifact by the
live checks in 84 of 84 schema-stage rounds — 100%.** The class names in this document
are what the current code says about those bytes, not a reading of the messages.

Three gen-11 rounds involve link-stage findings (clingo, cross-module resolution) that a
single stored module cannot reproduce; they are excluded from the replay and counted
separately.

Across *all* generations the replay reproduces the recorded classes as a **superset** in
most rounds rather than an exact match, for two documented reasons: the corpus id set has
changed (old runs used `L1-170_n026`-style ids), and checks have been added since — the
`borrowed-without-gloss` check landed 2026-08-10 and finds breaches in older modules
that were never reported at the time. Neither affects the gen-11 result.

---

## 8. What the plan removes

Measured by replaying every gen-11 round with `translate_autofix` applied for real and
the grammar fixes simulated by subtracting the classes they make unrepresentable
(`translation_fix_sim.py`):

| plan | rounds killed | $ saved |
|---|---|---|
| A — autofix alone | 2 / 84 (2%) | $0.0043 |
| A + B — cites/clause_id const | 5 / 84 (6%) | $0.0106 |
| A + B + C — requires/inputs carry their gloss | 14 / 84 (17%) | $0.0288 |
| A + B + C + D — ontology split rules/facts | 36 / 84 (43%) | $0.0747 |
| **A + B + C + D + E — acts carry their closure** | **49 / 84 (58%)** | **$0.1032** |
| A + B + C + D + E + F — body literals carry origin | 76 / 84 (90%) | $0.1624 |

**The plan through E removes 58% of repair rounds under the live prompt.** The residual
is 28 rounds of `undeclared-body-name` and eight singletons.

Projected onto the 773-node corpus at measured gen-11 rates ($0.00427/clause, of which
$0.00259 is repair): **~$3.30 total, ~$2.00 of it repair, ~$1.16 removed by the plan.**
The dollar amounts are small; the round counts are not, and rounds are what set wall
clock, rate-limit exposure and the regression rate in §6.2.

---

## 9. Standing cautions

* **Do not pin any count in this document into a test.** These are live-artifact counts
  over a corpus run that is still filling. `test_translate_autofix.py` pins frozen
  inputs and subset properties only.
* **`requires-unprovided` in the graveyard `_cleared_*` entries is not a defect** and is
  not counted as one here. At ~45 of 773 modules most providers are simply not
  translated yet. The `VERDICT.md` files say so, and flag it for recheck at corpus
  completion — if it survives a full corpus it becomes a real under-export finding.
* **The graveyard is not a failure population.** It records every non-first-attempt
  convergence, including `shrank`-guard entries kept deliberately as audit material.
* **The 11–16% cost overestimate is one-directional** and applies to every row, so it
  cannot reorder the ranking.
