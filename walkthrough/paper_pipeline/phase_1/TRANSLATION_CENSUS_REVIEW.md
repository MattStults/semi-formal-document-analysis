# TRANSLATION_CENSUS_REVIEW.md

**Clean-context adversarial review of `TRANSLATION_REPAIR_CENSUS.md`,
`TRANSLATION_FIX_PLAN.md`, `translation_repair_census.py`, `translate_autofix.py`,
`test_translate_autofix.py`, `translation_fix_sim.py`.**

Written 2026-08-14 by a reviewer with no part in producing the material under review.
**Zero API spend.** Every number below is re-derived from bytes already on disk, by code
written for this review, not by re-running the author's scripts. Nothing under `runs/`,
`resolve_runs/.../runs/`, `repair_graveyard/` or any owned module was written to; the
in-flight corpus run was read only.

---

## 0. Bottom line

**The measurement is sound and better than its own documentation claims.** I independently
re-derived 191 / 435 / 244 / 56% / 60%, the per-class table and the gen-11 table from the
raw transcripts, and matched **all 435 calls one-to-one against `usage.jsonl`** — something
the census did not do and did not need to. Real recorded spend is $0.7649, repair $0.4654
(**61%**), against the modelled $0.8005 / $0.4825 / 60%. The cost model is 5% high, not
11–16%, and its per-class ranking is stable under every cache-discount regime I tried.

**The fix plan is where the trouble is.** Three things, in order of severity:

1. The headline "**58% of gen-11 repair rounds removed … measured by replaying every
   stored failing module**" is 96% assumption. **47 of the 49 kills come from subtracting
   a class by fiat; only 2 are actually measured.** The word "measured" is doing work the
   evidence does not support.
2. Fix D — the lever that carries 24 of those 49 kills — **does not make
   `unsafe-variable` unrepresentable**. Rebuilding the simulation so Fix D removes the
   class only where Fix D's own mechanism reaches it (body-less ontology sites) drops the
   headline from **58% to 43%**.
3. §6.1 and §6.2, the two systemic claims, **are computed by no committed script**.
   §6.2 survives a hard independent test and is if anything understated; §6.1's numbers
   do not reproduce.

Fix-by-fix: **A NEEDS WORK** (one rule crosses the line the file draws for itself),
**B NEEDS WORK** (the written diff is a no-op for the half that matters, and would make
`cites: null` illegal), **C SAFE TO LAND with one class removed from its credit**,
**D NEEDS WORK**, **E REJECT as written**, **F REJECT / not ready**.

---

# PART I — THE MEASUREMENT

## 1. Headline counts — **CONFIRMED**

Re-derived from the 285 transcript files without using `translation_repair_census.py`'s
grouping:

| claim | my number | verdict |
|---|---|---|
| 285 transcript files → 191 distinct clause attempts | 285 → 191, 94 dropped | **CONFIRMED** |
| 191 clauses | 191 | **CONFIRMED** |
| 435 model calls | 433 assistant turns + 2 unanswered rounds | **CONFIRMED (see F-1)** |
| 244 repair rounds, 56% of calls | 244 / 435 = 56% | **CONFIRMED** |
| 60% of spend is repair ($0.4825 of $0.8005) | **61% ($0.4654 of $0.7649)** recorded | **CONFIRMED, corrected** |
| gen-11: 71 clauses, 87 rounds, 1.23/clause | 71 / 87 / 1.23 | **CONFIRMED** |
| gen-11: 61% of spend is repair ($0.1838 of $0.3034) | **61% ($0.1735 of $0.2866)** recorded | **CONFIRMED, corrected** |
| attempts per clause 1→73, 2→38, 3→58, 5→22 | identical | **CONFIRMED** |
| 22 clauses × 5 attempts = 88 rounds, "36% of repair spend" | 88 rounds; **38%** of recorded repair spend | **CONFIRMED, mildly understated** |
| every finding line classified, `OTHER` empty | 557 lines, 0 in `OTHER`, 0 lines dropped by the parser | **CONFIRMED** |
| `entry.json` `attempts` agrees with the transcript | 94/94 entries, 0 mismatches | **CONFIRMED** |

Dedup is clean. All 94 graveyard transcripts are **byte-identical** copies of run
transcripts, so the graveyard contributes zero unique clause attempts. That is worth
saying plainly: `§1.1`'s framing of the graveyard as a distinct source (including "the 48
`_cleared_*` entries with their `findings.json` and written `VERDICT.md`") is decorative —
none of it enters any number in the document. (Also: **92** graph-side graveyard entries,
not the 93 stated at `TRANSLATION_REPAIR_CENSUS.md:49`.)

---

## 2. Findings, ranked by severity

### F-1 · **HIGH** — "measured by replay" is 96% assumption

`TRANSLATION_REPAIR_CENSUS.md:33` (headline table) and `:387` describe the 58% as
"**measured by replaying every stored failing module with the autofix applied for real**
and the grammar fixes simulated by class subtraction". `TRANSLATION_FIX_PLAN.md:52-58`
reports the ladder in a column headed "kills alone / cumulative" with no assumption
marker at all.

Re-running the ladder with everything *actually applied* and nothing subtracted:

```
autofix applied for real, no class subtraction   :  2 / 84  ( 2%)
published A+B+C+D+E                              : 49 / 84  (58%)
```

**47 of the 49 kills rest entirely on class subtraction.** The subtraction assumes the
model, under a different grammar, would emit the *same module minus that defect* — which
census §6.2 itself measures to be false 57% of the time when the model rewrites a module.
The plan is arguing from the premise its own census refutes.

`translation_fix_sim.py:20-24` states the assumption honestly. The two documents that will
be read by the owner do not. **Verdict on the headline: OVERSTATED.** Honest phrasing:
*"2 rounds removed by measurement; 47 more projected on the assumption that a grammar
change removes a class without perturbing the rest of the module."*

### F-2 · **HIGH** — Fix D's class subtraction over-credits it; 58% → 43%

`translation_fix_sim.py:62-63` models Fix D as subtracting the **entire**
`unsafe-variable` class. Fix D's mechanism (`TRANSLATION_FIX_PLAN.md:517-524`) is a split
into `OntologyRule` (body required) and `OntologyGroundFact`. It therefore reaches only
**body-less ontology sites**. Three independent gaps:

* **Other emission sites.** The message has five emission sites in `schema.py`
  (`:446-447` assertion, `:538-540` ontology, `:655-656` closure, `:506-507` defines,
  `:819-820` acts). Fix D touches one. Measured: of 40 gen-11 `unsafe-variable` findings,
  **37 are `ontology[i]`, 3 are `asserts[i]`** — so §5.1's "**Every** gen-11 instance is
  an `ontology[i].atom`" (`TRANSLATION_REPAIR_CENSUS.md:280-281`) is **WRONG as written**,
  though only 1 round turns on it.
* **Bodied entries survive verbatim.** Across all stored attempts, **12 of 99 unsafe
  ontology atoms already carry a non-empty `body`**. They migrate into `OntologyRule`,
  satisfy the required-`body` field, and reproduce the identical breach.
* **`OntologyGroundFact`'s no-variable rule is a docstring.** The proposed diff at
  `TRANSLATION_FIX_PLAN.md:517-524` gives it a `Field(description=…)` and **no validator
  and no `pattern`**. `{"atom": "u18_user(U)"}` is a well-formed `OntologyGroundFact`.
  The plan's own lever ordering (`:10-24`) says not to trust that configuration; here it
  is lever (d) wearing lever (a)'s label.

Corrected simulation, Fix D subtracting `unsafe-variable` only where its mechanism reaches:

```
published (whole class subtracted)          : 49 / 84  (58%)
ontology sites only                         : 48 / 84  (57%)
body-less ontology sites only  <-- correct  : 36 / 84  (43%)
```

**Verdict on "58% of gen-11 repair rounds removed": OVERSTATED. Corrected: 43%**, and of
that 43%, 2 rounds are measured and 34 are assumed.

### F-3 · **HIGH** — §6.1 and §6.2 are computed by no committed script

Neither `translation_repair_census.py` nor `translation_fix_sim.py` contains any code for
masking or for repair-induced regression. Grep for `masking|round 1|visible|novel|
regression|persists|introduced` across both returns nothing. Both are the argumentative
core of the case that repair rounds are *systemically* costly, and neither is reproducible
from the shipped artifacts.

**§6.2 — repair-induced regression: CONFIRMED, and understated.**
`TRANSLATION_REPAIR_CENSUS.md:337` claims 65 of 124 post-first rounds (52%) carry a novel
class. I get **71 of 124 (57%)**. The introduced/persisted tables at `:341-346` reproduce
*exactly*, so the discrepancy is in the headline, not the detail.

I then ran the masking test the brief asked for — for every novel class, replay **every
earlier failing module in the same chain** through the live checks and ask whether the
class was already latent:

```
novel-class instances already latent in an earlier module (MASKED) :  5
genuinely introduced by the repair                                 : 97
```

Excluding the 7 link-stage `asp-syntax-refused` cases a stored module cannot reproduce:
**90 genuinely new vs 5 masked**. The regression claim is not a masking artifact. This is
the strongest thing in the census and it is the one thing with no script behind it.

**§6.1 — masking: NUMBERS DO NOT REPRODUCE.** `:331-332` claims "only 61% of a chain's
eventual breach classes are visible at round 1" and "only 54% of chains have their whole
breach set on the table at the first repair", over "**114** repaired clause chains".

```
chains with >=1 repair round                     : 120   (not 114 — 114 matches nothing)
fraction visible at round 1, macro (mean of ratios): 72.6%
fraction visible at round 1, micro (pooled)      : 59.5%
chains with the whole set at round 1             : 49%   (not 54%)
```

Neither 61% nor 54% nor 114 reproduces. The **qualitative** claim (round 1 is told less
than the truth, because `Module._coherent` is an `after` validator — `schema.py`) is
correct and important; the numbers attached to it are not defensible as stated.
**Verdict: OVERSTATED / UNREPRODUCIBLE. Corrected: 59.5% pooled (72.6% per-chain mean),
49% whole-set, over 120 chains.** The follow-on claim that running the autofix first
lifts these "to 65% and 61%" has the same problem and I could not reproduce it either.

### F-4 · **MEDIUM** — the cost-model "validation" compares populations that do not match

`TRANSLATION_REPAIR_CENSUS.md:95-108` validates the model by comparing a modelled mean
over 435 calls to a recorded mean over **708 `usage.jsonl` rows**. Those 708 rows are all
`together-deepseek-v4-flash` rows in the project — the eval arms, probes, readback and
seat calls included. Only 435 of them are translation calls. The 1.11× is a ratio of two
different populations.

The right check is available and easy: **every one of the 435 calls matches a usage row
uniquely on `content_chars`**, with zero unmatched. On the matched calls:

```
modelled $0.8000   vs   recorded $0.7649    ratio 1.05x   (not 1.11x)
```

And the **stated cause is wrong**. §1.4 attributes the gap to 71% cached input going
undiscounted. But `cost_usd` in `usage.jsonl` prices the whole `prompt_tokens` at
$0.14/Mtok (recorded cost ÷ whole-prompt price = **1.0000** median), so cache cannot
explain a gap against it. The actual cause is `translation_repair_census.py:307`
(`in_cpt = out_cpt`): the census calibrates chars-per-token on the **completion** side
(3.74) and reuses it for input. Measured on the matched calls, **input is 3.98 chars/token
(median)**, so the model over-counts input tokens by ~6%.

**Verdict on "validated against usage.jsonl at 1.11×": OVERSTATED as a validation.
Corrected: 1.05× on a proper call-level match, and the cache explanation is wrong.**

*One caveat the census should have raised and did not:* `cost_usd` is computed by this
project's own pricer (`priced_by: walkthrough/paper_pipeline/phase_1/config.json`), not by
the provider. "Together bills cached input whole" (`translation_repair_census.py:298-300`)
is inferred from the repo's own pricing convention, which is circular.

### F-5 · **MEDIUM** — cache-discount sensitivity: the *claim* is right, the *reason* is not

§1.4 asserts the bias "cannot reorder the ranking". I tested it properly, re-costing every
class from the real recorded rows under three regimes:

| gen-11 rank | no discount | cache @25% | cache free |
|---|---|---|---|
| 1 | `unsafe-variable` | `unsafe-variable` | `unsafe-variable` |
| 2 | `readback-slot-arity` | `readback-slot-arity` | `readback-slot-arity` |
| 3 | `undeclared-body-name` | `undeclared-body-name` | `undeclared-body-name` |
| 4 | `borrowed-without-gloss` | `borrowed-without-gloss` | `borrowed-without-gloss` |
| 5 | `act-not-in-acts` | `act-not-in-acts` | `act-not-in-acts` |

**CONFIRMED for gen-11** — no flip at any discount. (On the pooled all-generations table
ranks 2 and 3 do swap under discount, but that table is correctly labelled "the wrong one
to plan from".) The stated *ground* — "the bias is one-directional and applies to every
row" — is not why it holds; it holds because the gap between adjacent classes is larger
than the discount's differential effect. Right answer, wrong reasoning.

### F-6 · **MEDIUM** — "generations" are not comparable within gen 11

`sha256(prompt_system.txt)` groups by what the model was told, which is the right *idea*
and better than git history. But it is **invariant to every model parameter**, and those
changed inside gen 11:

| gen-11 run | rounds/clause | `max_tokens` | `resample_truncation` | mean 1st-completion chars |
|---|---|---|---|---|
| 20260810-225427 | 2.27 | 16384 | — | 3149 |
| 20260810-234100 | 1.86 | 16384 | — | 3415 |
| 20260812-090344 | 0.93 | 16384 | 2 | 2856 |
| 20260812-133317 | **0.67** | 16384 | 2 | 3726 |
| 20260814-163457 | **0.25** | **4096** | 2 | **1568** |

Two consequences.

* §3.2 claims the 2.27 → 1.86 → 0.67 improvement "came from the **per-request adapter**"
  because "the system block is byte-identical across all three". It is byte-identical —
  and so is nothing else. `resample_truncation: 2` switches on **exactly** at the
  transition to the improved runs, a perfect confound. A resampled draw is a paid call
  that never enters the transcript (`translate.py:605-618` — `_retrying`, which wraps the
  first attempt only), so it is invisible to the census by construction. **The causal
  attribution in §3.2 is not supported by the evidence offered.** (Mitigating: I found
  only 4 truncated unmatched usage rows overall, so the effect is probably small — but
  "probably small" is not what §3.2 says.)
* The 0.25 run wrote modules **half the size** of every other gen-11 run, under a 4× lower
  `max_tokens`. Fewer ontology entries and asserts is fewer breach opportunities. §3.2
  does flag this run as not comparable — correctly — but the census header row
  "gen 11 · 71 clauses · 87 rounds · 1.23/clause" **pools it in anyway**, and that pooled
  figure is what the projection in §8 rests on.

Minor: §3.2 says "three runs translate the **identical** 15-clause sample"; 20260810-234100
has **14** (missing `l527_796_n022`). The comparison survives on the common 14.

### F-7 · **MEDIUM** — the taxonomy merges sites that the fix plan then treats as one

`classify()` (`translation_repair_census.py:124-128`) discriminates on **message text
only** and ignores `check_id`. Because several checks emit the same sentence from
different sites, three classes silently merge distinct defects:

* **`unsafe-variable`** — 83 ontology + 3 assertion-forbid + 2 closure sites. This is the
  merge that lets Fix D over-claim (F-2).
* **`not-a-term`** — 18 ontology + 13 closure `act_class` + 4 `acts` entries.
* **`closure-missing`** — 15 "no default-closure declaration for act class(es)" plus 2
  from a different check (`governs act class(es) … with no `%% closure:` declaration`).

And one class is not a defect class at all: **`asp-syntax-refused` is a cascade wrapper.**
Its message is *"clingo refused this program, so nothing below was actually analysed"* —
and **18 of its 22 rounds carry no other class**, so for those rounds the census records a
class whose actual cause is unknown. It is nonetheless ranked #4 by cost in the pooled
table (`:148`) and credited in §3.1 as a class that was "killed outright". It is 1 round
in gen 11, so nothing downstream turns on it.

Also: `TAXONOMY`'s last entry, `("SYNTAX", "body-prose-connective", r"ontology '[^']+':
'[^']*'")` (`translation_repair_census.py:117-118`), matches **zero** lines — dead code,
and a suspiciously broad mop for a taxonomy whose claim to soundness is "iterated until
the residual `OTHER` bucket was empty".

### F-8 · **LOW** — two paid rounds have no assistant turn

Two transcripts (`runs/20260807-154618-.../m0037.transcript.json` and `…/m0091…`) end with
a repair message and no reply (`u-a-u`). The census counts them as calls (hence 435 rather
than 433 assistant turns) and prices them with `completion_chars = 0`. Defensible either
way; worth one sentence in §1.2.

### F-9 · **LOW** — the §8 projection is a straight-line extrapolation from a 15-node sample

`$0.00427/clause × 773 ≈ $3.30` checks out arithmetically ($3.30; on recorded cost,
$0.004036 → $3.12). But the per-call input cost is dominated by a 34–38 kB system block
plus a per-request adapter whose ESTABLISHES/PROVIDES/NEEDS scaffolding is a function of
corpus size, and `requires-unprovided` is explicitly expected to behave differently at
full corpus (§ standing cautions). The projection is presented without an error bar and
is used at `TRANSLATION_FIX_PLAN.md` to size a paid arm.

---

# PART II — THE FIX PLAN

## 3. Fix A — the deterministic autofix · **NEEDS WORK**

The code is genuinely good. `autofix` is pure, non-mutating, idempotent, individually
addressable, and every rule carries the instruction it enforces. The 34 pins are
**RED-first on real disk artifacts** — each asserts the real breach fires before and that
the exact corrected field value is present after (`test_translate_autofix.py:128-136`,
`:170-177`, `:238-250`). They prove considerably more than "the code runs". I reproduced
the plan's corpus-replay firing counts exactly (116 `declare-asserted-act`, 61
`readback-empty-slots`, 41 `concept-name-arity`, 38 `forbid-body-bare`, 15
`act-class-functor`, 9 `ontology-rule-split`, 8 `reference-name-arity`, 1
`readback-trailing-slots`) and the class deltas (`readback-slot-arity` 40→3,
`act-not-in-acts` 30→0, `concept-name-carries-arity` 10→0,
`inputs-entry-not-name-arity` 4→0). All of `TRANSLATION_FIX_PLAN.md:228-234` is accurate.

But the pins prove **conformance to the checks**, not **preservation of meaning**, and two
rules cross the line the file draws at `translate_autofix.py:16-22`.

### A-1 · `_fix_readback_empty_slots` decides a question the model left open

`translate_autofix.py:84-108`. A `read_back` with no `%` and a non-empty
`read_back_slots` has **two** repairs: drop the slots, or add the `%`. The autofix always
picks the first. The rule immediately below it (`:111-134`) refuses the mirror case for
exactly this reason — *"choosing which variable fills the extra `%` is a content
decision"*. The asymmetry is unargued.

What is actually lost: `read_back` is emitted as `%!trace_rule {"sentence", args}`
(`schema.py:1291-1301`) — the human-audit surface for why a rule fired. Dropping the slot
makes the explanation stop naming *which* user or material it fired for.

I inspected all 22 gen-11 instances. The verdict is **mostly favourable to the fix but not
uniformly**: sentences like *"an instruction at level L1 outranks an instruction at level
L2 when L1 is higher than L2"* with `slots: ["L1","L2"]` already name their variables in
prose and the slot list is genuinely spurious. But *"affirming an ungrounded belief that
might lead to distress is forbidden"* with `slots: ["B"]` reads as a universal after the
fix, where the model signalled it was about a particular belief `B`.

This is the **largest single class the autofix touches** (17 of 18 gen-11 readback rounds).
It does not corrupt the rendered sentence — the slot was unreachable — but it **silences a
check whose purpose is to catch a bad read-back, without fixing the read-back**.

*Recommendation:* keep the rule, but record the dropped slot list on the `Fix` record and
surface it in the run artifact, so a reader can tell a spurious slot from a lost
parameterisation. Do not describe it as "nothing a reader could have meant is lost".

### A-2 · `_fix_declare_asserted_acts` is a content decision, and it makes things worse

`translate_autofix.py:286-315`. When `asserts[i].act` names an act absent from `acts`, the
rule appends the assertion's act term to `acts` — i.e. it decides that **the assertion is
authoritative and the declaration list is wrong**. Constructed counter-example:

```python
{"acts": ["produce(M)"], "asserts":[{"act":"produce_material(M)","status":"forbid"}]}
  -> acts == ["produce(M)", "produce_material(M)"]
```

If `produce_material(M)` was the typo, the autofix has just blessed it and manufactured a
second governed act class. `acts` is not "a declaration list, not content"
(`translate_autofix.py:296-298`) — closure obligations attach to it (`schema.py`), which
is why the plan's own §A4 records the side effect.

The plan is honest about the cost (`TRANSLATION_FIX_PLAN.md:213-219`: *"does not save the
call"*). My replay says it is worse than "does not save": over all 244 rounds,
`closure-missing` **22 → 48** and `closure-ungoverned` 23 → 7, a **net +10 breach-rounds**.
The pipeline is being asked to do deliberately what census §6.2 identifies as the systemic
cost — trade one defect for another and pay for the round anyway.

*Recommendation:* ship the autofix with `declare-asserted-act` **off by default**
(`rules=` already supports a subset), and turn it on with Fix E if Fix E ever lands in a
shape that makes the pair one structural requirement.

### A-3 · Constructed wrong-but-passing inputs (LOW, but they exist)

| input | produced | correct |
|---|---|---|
| `inputs: ['holds("a,b")']` | `holds/2` | `holds/1` — `_arity_of` (`:53-66`) tracks `()` and `[]` depth but **not quotes**; `{a,b}` pools miscount too |
| `ontology[0].atom = "p(X) :- q(X). r(Y) :- s(Y)."` | `atom="p(X)"`, `body="q(X). r(Y) :- s(Y)"` | the head `r(Y)` is silently absorbed into a body string |
| `forbid_body[0].head = "forbid(permit(f(X)))"` | `f` | two deontic layers stripped by the `while` loop at `:242-244` |

The second fails loudly downstream (unparseable body); the first does not — it produces a
schema-legal reference with the wrong arity. Guarded correctly: `':-'` inside a quoted
string is skipped, prose in `forbid_body` is left alone, disagreeing arity suffixes are
left alone, `Produce(M)` (an ASP variable) is left alone.

### A-4 · Fix A is not wired in

`translate_autofix` is imported only by `translation_fix_sim.py`. "IMPLEMENTED"
(`TRANSLATION_FIX_PLAN.md:71`) means the module exists and is pinned, not that any
translation uses it. The plan says so at `:236`; the census headline does not.

**Fix A verdict: NEEDS WORK** — land it with `declare-asserted-act` disabled and the
dropped-slot record added; the other six rules are safe.

## 4. Fix B — `cites` / `clause_id` as a per-request const · **NEEDS WORK**

The lever is empirically justified: across 177 stored modules, **0 cite more than one
distinct clause**, the only 3 foreign-id citations are the fabrications themselves, and all
16 abstentions carry a `clause_id`. And schema forcing demonstrably works on this provider
— 204 stored completions validated against the exact schema their own `run.json` recorded,
**zero violations** of `required`, `additionalProperties`, or any of the 8 shipped `enum`s.

"**Four lines and cannot regress**" (`TRANSLATION_FIX_PLAN.md:64`) is false on four counts.

* **B-1 (HIGH) — the written diff is a no-op for `cites`.** The plan patches `raw` and
  returns it; `schema.json_schema()` pops `$defs` into a local at `schema.py:983` and
  returns `inline(raw)`. After the pop, the number of defs in `raw` carrying a `cites`
  property is **0**. All seven item types live in the popped `$defs`. The `clause_id` half
  would land; the citation half — which the plan calls "the single worst failure available
  here" — would silently do nothing.
* **B-2 (HIGH) — it would make `cites: null` illegal.** The proposed
  `{"anyOf":[{"enum":[…]},{"type":"null"}]}` is collapsed by the module's own flattener to
  `{"enum":["l1_170_n003"], "type":["string","null"]}`; `enum` and `type` are conjunctive,
  so `null` is excluded. **224 of 1386 licensed items (16.2%)** across stored modules are
  `licence: "assumed"` with null/absent `cites`. Making those unemittable pushes the model
  toward exactly the outcome `schema.py:337-341` warns is *"strictly worse than an honest
  `assumed`"* — a fabricated citation behind a green check. Correct form:
  `{"type":["string","null"], "enum": sorted(ids) + [None]}`, applied **after** `inline()`.
* **B-3 (MEDIUM) — the legal-set premise is false.** The plan asserts the legal set for a
  graph node is `{node_id}`. `translate.py:1206` computes `known_ids` as the **whole loaded
  corpus** (773 ids) and passes it to `repair_loop` at `:1381`. Fix B would make the grammar
  773× stricter than the check it enforces. The plan's own guard rail — *"if the two sets
  can drift, pass nothing rather than a wrong set"* — fires on the current code, unnoticed.
* **B-4 (MEDIUM) — `const` is evidenced by nothing; `enum` by 204 completions.** There are
  **zero uses of `const`** anywhere in the repo. `TRANSLATION_RUNBOOK.md:408` and
  `RUNBOOK_AUDIT.md:270` both record enum-forcing `clause_id` as "designed, not shipped".
  Use a single-element `enum`.
* **B-5 (MEDIUM) — it fails silently.** If the pin no-ops or the provider ignores it, the
  run is observationally identical to today. Nothing asserts the pin was honoured.
* **B-6 (LOW) — collateral.** `translate.py:1084/1185` would record an *unpinned* schema in
  `run.json` while the wire carried a pinned one, falsifying `run_record`'s own docstring
  at `:1174`. `version.schema_source()` (`version.py:298`) hashes the text of `schema.py`,
  so editing it re-stamps every stored artifact stale. Realistic diff: **60–120 lines
  across 3–4 files**, plus threading a clause id through `_body` / `_body_messages` /
  `complete` / `complete_messages`, which six other modules also call.

**Verdict: NEEDS WORK.** Right lever, broken diff. Fix B-1 and B-2 before it goes near a
run; use `enum`; add a run-level assertion that the pin was honoured; re-derive the legal
set from the same source the checker uses.

## 5. Fix C — `requires`/`inputs` carry name+arity+gloss · **SAFE TO LAND, with one class removed from its credit**

Of the three classes `translation_fix_sim.py:59-61` subtracts for C:

* `inputs-entry-not-name-arity` — **genuinely unrepresentable** once the entry is a
  structured `{name, arity}` object. Sound.
* `borrowed-without-gloss` — the field becomes required, so the *check* becomes
  unfailable. But the model can satisfy it with a junk gloss. This suppresses the check
  rather than removing the defect; the round is genuinely killed, which is what the
  simulation measures, so the credit stands — but the plan should not describe the defect
  as eliminated.
* **`requires-inputs-overlap` — should not be credited.** Carrying a gloss does nothing to
  stop a name appearing in *both* lists. Nothing in Fix C makes this class unrepresentable.
  It costs 4 gen-11 rounds and does not change the ladder, but it is an unearned
  subtraction sitting in a decision table.

Lowest blast radius of the three grammar fixes and the one I would land first.

## 6. Fix D — ontology split into rules / ground facts · **NEEDS WORK**

Beyond F-2 (it does not make the class unrepresentable, and the honest number is 43% not
58%):

* **D-1 (HIGH) — no migration for 200 stored modules.** 200 stored module objects, **159
  with a non-empty `ontology`**, 389 ontology entries. Renaming `ontology` →
  `ontology_rules` + `ontology_facts` makes **every one unloadable** by
  `Module.model_validate`. The plan proposes no shim and no alias. *Encouragingly*, of the
  141 stored body-less entries **0 carry a variable**, so the content migration is
  mechanical (body ⇒ rule, no body ⇒ fact) — which makes the missing shim gratuitous
  rather than unavoidable.
* **D-2 (HIGH) — the contract-hash cost is uncosted, and it is not waivable.**
  `graveyard.contract_hash` (`graveyard.py:76-82`) hashes `schema_source`, and
  `version.schema_source()` (`version.py:298-301`) returns the **entire text of
  `schema.py`** — any byte, including a docstring. **219 stored artifacts carry a
  `contract_hash`; 110 `*.version.json` stamps exist.** All go `CONTRACT_STALE`
  (`version.py:205-208`), and `version.apply_waivers` (`:445-455`) **raises** on a
  contract-stale clause: *"A contract change is never waivable … Re-translate."* Landing D
  obliges a full paid re-translation that appears nowhere in the plan's cost table.
* **D-3 (HIGH) — seven `schema.py` sites unnamed, one of them dangerous.**
  `schema.py:865` builds the declaration set as `{f.atom.split("(")[0] for f in
  self.ontology}` — the *declaration site* for `undeclared-body-name`. If it is not updated
  to union both new lists, **every ontology-declared body literal becomes an
  `undeclared-body-name` finding**, inflating the exact class Fix F exists to kill.
  Also `:778`, `:789`, `:867`, `:1058`, `:1188`, `:1272-1281`. `:1058` and `:1188` raise
  `AttributeError` rather than degrade.
* **D-4 (HIGH) — the cheapest lever is not considered by name.** The plan goes straight
  from *"`body` is optional, so 'unbound head with no body' is a well-formed value"*
  (`:485-488`) to the two-class split. **Conditionally requiring `body` when the atom
  carries a variable** — one `model_validator`, or a JSON-Schema `if`/`then` — buys the
  same enforcement on **87 of the 99** measured cases with **zero** blast radius: no key
  rename, no 200-artifact migration, no ~58 test edits, no contract re-stamp. It leaves
  the 12 bodied cases and the assert sites — but so does Fix D. Under repo doctrine
  ("rulings go in the repo, and the tempting alternative is rejected **by name**"), this
  omission alone is disqualifying for the current draft.
* **D-5 (MEDIUM) — the named rejection answers a different proposal.**
  `TRANSLATION_FIX_PLAN.md:559-565` rejects an autofix that would **delete** a redundant
  ontology entry, on the ground that deletion is a content edit. The alternative actually
  on the table is a **move** — demote the atom to a `concepts` declaration — which is not a
  deletion and is not addressed. Precedent for an ontology-touching autofix already exists
  in the file the plan just landed (`translate_autofix.py:254-283`).
* **D-6 (MEDIUM) — the 74% figure is unsourced and does not reproduce.**
  `TRANSLATION_REPAIR_CENSUS.md:286-287` and `TRANSLATION_FIX_PLAN.md:557-558` say it is
  "reproducible from `translation_repair_census.py`". No code in that file compares
  `concepts` to `ontology`. Independent measurements: **69.7%** (69/99 over all stored
  unsafe atoms, name+arity), **67.8%** restricted to the body-less ones the plan describes,
  **84%** (31/37) over gen-11 post-autofix ontology sites. All support the *argument*; none
  is 74%.
* **D-7 (MEDIUM) — ~58 test functions break**, routed through 7 module builders in
  `fixtures.py` (`:110`, `:205`, `:228`, `:265`, `:286`, `:317`): `test_schema.py` 26,
  `test_readback.py` 12, `test_seats.py` 6, `test_translate_autofix.py` 6,
  `test_prompt_examples.py` 3, `test_readback_r3.py` 3, `test_eval.py` 1, `test_checks.py` 1.

## 7. Fix E — acts carry their own closure · **REJECT as written**

* **E-1 (HIGH) — it deletes a live safety check with no replacement.** `schema.py:447`
  runs `_check_head_bound(self.act, self.body, where)` — the guard against an unsafe
  variable in the `asserts` head. Under Fix E, `Assertion.act` becomes an `int` index
  (`TRANSLATION_FIX_PLAN.md:625-629`) and the term moves to `GovernedAct.term`. The check
  cannot run where it is; the plan neither relocates it nor mentions it. The ~20 measured
  assert-site unsafe variables would stop being reported at schema stage and arrive instead
  as raw clingo whole-file refusals — which `schema.py:155-158` records as reaching the
  repair loop **truncated**. A bookkeeping fix must not degrade a solver-safety guard.
* **E-2 (HIGH) — silent renderer corruption.** `schema.py:1294` would emit
  `asserts(l796…, forbid, 0).` — **valid ASP that means something else**. `schema.py:1242`
  (`', '.join(mod.acts)`) raises. Unaddressed, as are `readback.py:691/697`,
  `readback_r3.py:187`, `seats.py:689` (a seat-facing sentence that would read *"forbids
  the act 0"*) and `translate.py:1466/1471`.
* **E-3 (HIGH) — it silently no-ops three of Fix A's eight rules.**
  `_fix_act_class_to_functor`, `_fix_ontology_rule_into_body` and
  `_fix_declare_asserted_acts` all reach for the removed/retyped keys via `dict.get`, so
  under D+E they return `None` and the loop simply does not run — **no error**. The 116 + 15
  + 9 corpus firings the plan credits to A drop to zero, and **all 34 tests keep passing**
  because their fixtures are old-shape dicts. That is a silent regression behind a green
  suite. The plan's ordering (`:815-823`) lands A at step 1 and D+E at step 4 without
  noting the collision.
* **E-4 (MEDIUM) — knowingly the more brittle option.** The plan's own footnote
  (`:648-654`) concedes the integer index is "more brittle to a partial regeneration" and
  names a string+`enum` fallback that is not available for free-form clauses.
* **E-5** — for **10%** of rounds killed, this is the largest coupling change in the plan
  and the only one that can corrupt rendered ASP without erroring. ~56 test functions.

*A defensible shape exists:* fold `closure` into `acts: list[GovernedAct]` — that half
cleanly kills `closure-missing` and `closure-ungoverned`, which are pure cross-list
agreement defects — and **leave `asserts[].act` a string**, keeping `_check_head_bound`
where it is. `act-not-in-acts` is already 30 → 0 under Fix A.

## 8. Fix F — body literals carry their origin · **REJECT / not ready**

Not in the recommended ladder, and correctly so, but its 27 marginal kills (58% → 90%) are
the least defensible subtraction in the document. Census §5.5 says it itself:
*"Choosing the bucket is a real content decision… This class must keep costing a call."*
Making the origin a required field does not make the choice; it relocates the same decision
into a field the model must still fill, and converts a good message (*"nothing declares
it"*) into a worse one (*"origin says ontology but it is not there"*). Do not quote the
90% figure to the owner as a plan outcome.

---

## 9. The two "honest negatives" — both **CONFIRMED**, one understated

* **"Autofix alone kills 2 rounds."** Reproduced exactly: 2/84. Honest, and the plan does
  not hide behind it. But see F-1: this is the *only* measured number in the ladder, which
  makes it far more load-bearing than its presentation suggests.
* **"`declare-asserted-act` saves no call."** Reproduced, and it is **worse than stated**.
  Over all 244 rounds the rule moves `closure-missing` 22 → 48 and `closure-ungoverned`
  23 → 7 — **net +10 breach-rounds**, not a neutral trade. See A-2.

**A bigger negative is not reported anywhere:** the ladder's cumulative column is 96%
assumption (F-1), and the single largest lever's assumption is measurably wrong (F-2).

---

## 10. Arithmetic and transcription

* `TRANSLATION_FIX_PLAN.md:54`, cumulative column, row C: **"+C → 43%" is wrong.**
  Verified by simulation: D 24 (29%) ✓, E 8 (10%) ✓, D+E 30 (36%) ✓, **D+E+C = 45/84 =
  54%**, D+E+C+B = 49/84 = 58% ✓. The 43% is the census §8 value for the *different*
  combination A+B+C+D (36/84). The error understates the plan's own case, but it sits in a
  decision table.
* Census §8 ladder reproduces exactly: 2/5/14/36/49/76 of 84.
* "Kills alone" B 5, C 11, D 24, E 8, F 11 all reproduce. Note they are all measured
  *on top of the autofix*, so they are not additive and the marginals (3/9/22/6) sum to 42,
  not the cumulative 49 — the extra 7 come from multi-class rounds needing several fixes.
  Neither document explains this; a reader summing the column will get the wrong answer.
* §6.3 "36% of all repair spend" is the *round* share; the recorded *spend* share is 38%.

---

## 11. Verdict table

### Headline claims

| claim | verdict | corrected |
|---|---|---|
| 191 clauses / 435 calls / 244 rounds / 56% | **CONFIRMED** | — |
| 60% of translation spend is repair | **CONFIRMED** | 61% recorded ($0.4654 / $0.7649) |
| gen 11: 71 clauses / 87 rounds / 1.23 per clause | **CONFIRMED** | pools non-comparable runs (F-6) |
| gen-11 per-class cost table & ranking | **CONFIRMED** | rank-stable under any cache discount |
| taxonomy has no residual `OTHER`, no dropped lines | **CONFIRMED** | merges 3 site-distinct classes (F-7) |
| cost model validated at 1.11× against usage.jsonl | **OVERSTATED** | 1.05× on a proper call-level match; cache is not the cause |
| cache share cannot reorder the ranking | **CONFIRMED** | right answer, wrong stated reason |
| runs grouped by prompt generation are comparable | **OVERSTATED** | `max_tokens` 16384→4096 and `resample_truncation` change *inside* gen 11 |
| §3.2 improvement came from the per-request adapter | **NOT SUPPORTED** | perfectly confounded with `resample_truncation: 2` |
| §5.1 "every gen-11 `unsafe-variable` is an `ontology[i].atom`" | **WRONG** | 37 of 40; 3 are `asserts[i]` |
| §5.1 "74% already declared in `concepts`" | **UNSOURCED** | 67.8–72.7% (all gens) / 84% (gen-11 ontology) |
| §6.1 "only 61% visible at round 1", "54% whole set", "114 chains" | **OVERSTATED / UNREPRODUCIBLE** | 59.5% pooled, 72.6% per-chain mean, 49% whole set, 120 chains |
| §6.2 "52% of post-first rounds carry a novel class" | **CONFIRMED, understated** | **57% (71/124)**; masking test: 97 genuinely new vs 5 latent |
| §6.3 "36% of repair spend in 12% of clauses" | **CONFIRMED** | 38% of recorded spend |
| §7 faithfulness 84/84 | **CONFIRMED** | it is a *superset* test, which is the conservative direction |
| **"58% of gen-11 repair rounds removed, measured by replay"** | **OVERSTATED** | **43%** with Fix D restricted to its own mechanism; and **47 of 49 kills are assumed, 2 measured** |

### Fixes

| fix | verdict | one-line ground |
|---|---|---|
| **A** autofix | **NEEDS WORK** | six rules are safe and well pinned; `declare-asserted-act` is a content decision that nets +10 breach-rounds, and `readback-empty-slots` silences a check without fixing the read-back |
| **B** cites/clause_id pin | **NEEDS WORK** | right lever, empirically justified; the written diff no-ops for `cites` and would make `cites: null` illegal for 16% of licensed items |
| **C** requires/inputs + gloss | **SAFE TO LAND** | lowest blast radius; drop `requires-inputs-overlap` from its credited classes |
| **D** ontology split | **NEEDS WORK** | does not make the class unrepresentable (43%, not 58%); no migration for 200 artifacts; forces an uncosted paid re-translation; the cheaper conditional-`body` lever is not rejected by name |
| **E** acts carry closure | **REJECT as written** | deletes `_check_head_bound` on assert heads with no replacement, renders `asserts(cid, forbid, 0)` silently, and silently no-ops three of Fix A's rules behind a green suite |
| **F** body-literal origin | **REJECT / not ready** | relocates a content decision rather than removing it; the census says so itself |

---

## 12. What I would ask for before any of this reaches the owner

1. Re-title the 58%. Publish the measured number (2) and the projected number separately,
   and rebuild the ladder with each fix subtracting only what its own mechanism reaches.
2. Commit the §6.1 / §6.2 computation as code, in `translation_repair_census.py`, and
   correct §6.1's three numbers. §6.2 deserves better than an uncommitted claim — it is
   the strongest finding in the document and it survived a hard test.
3. Replace §1.4's validation with the call-level match (all 435 match on `content_chars`),
   fix `in_cpt = out_cpt` at `translation_repair_census.py:307`, and withdraw the cache
   explanation.
4. Add the run's model parameters to the generation key, or state plainly that a
   generation groups only the system block. Withdraw §3.2's causal attribution or control
   for `resample_truncation`.
5. Land **C** first, then **A** with `declare-asserted-act` off, then **B** after B-1 and
   B-2 are fixed. Send **D** back for the conditional-`body` comparison and a migration
   plan with the contract-hash cost in it. Do not land **E** in its current shape.
6. Publish the 74% derivation, or drop the number.

*(Per the standing caution at `TRANSLATION_REPAIR_CENSUS.md:412`: no count in this review
should be pinned into a test either. They are live-artifact counts over a corpus run that
is still filling.)*
