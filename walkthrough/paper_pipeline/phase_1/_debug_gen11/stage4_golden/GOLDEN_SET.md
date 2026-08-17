# The stage-4 golden set — modules with a known right answer

Built 2026-08-16. **No model call was made at any point**, by this file or by
anything it describes. Construction and the whole of the scoring below are
deterministic re-analysis of artifacts already on disk.

## Why

The first stage-4 baseline reports **66 of 81 clauses carrying a defect
verdict** and nobody can interpret that number, because no case in it has a
known right answer. Cross-model agreement cannot supply one — Haiku vs Sonnet
on a related adjudication in this repo gave κ = 0.248 and forced a headline
figure to be withdrawn, Sonnet failed its discrimination falsifier outright
(Fisher p = 0.146), and the judge we have is now measured **lenient on its own
work** (DeepSeek judging DeepSeek: κ = 0.294 on 4b against Sonnet, with every
disagreement class running one way).

What has produced trustworthy findings here is *anchoring*. This set is the
anchor for stage 4: believed-correct modules with **one planted defect each**,
mechanically applied and reversible, so a judge is scored on **validity**
rather than on agreement.

## Composition — MEASURED, from `key.json`

| stratum | n | note |
|---|---|---|
| bases | 11 | the modules a human reader (opus-5, direct read, no delegation) marked FAITHFUL in `_debug_gen11/spotcheck_semantic/verdicts.json`, over run `20260815-124836` |
| **mutants** | **17** | one planted defect each; **2 labelled ARGUABLE** and excluded from every pooled cell |
| **whole-clause controls** | **11** | the same 11 modules, untouched |
| **borrowed-name controls** | **14** | 4 resolved / 10 dangling. Unmutated items that are *correct by the pipeline's own instruction* |
| planted sites verified reachable | 31/31 | every site is in at least one seat's denominator (`--verify-sites`) |

Per class (mutants):

| class | n | specimen it replicates |
|---|---|---|
| scope-drift-widen | 3 | `l831_1000_n005` |
| scope-drift-narrow | 2 | `l831_1000_n005` |
| disjunction-as-conjunction | 2 | `l3147_3238_n003` |
| inverted-modality | 2 | `l1_170_n088`, `l1707_1973_n006` |
| invented-obligation | 2 (1 arguable) | `l1108_1367_n014` |
| fact-as-deontic | 2 (1 arguable) | *"a system message will list the available tools"* → `oblige list_tools(M)` |
| dropped-obligation | 2 | `l1_170_n056` |
| prefer-polarity | 2 | `l1974_2125_n019` |

Arms: a clause carries at most one mutant per arm, so a base mutated twice
appears in two arms. **arm0 = controls (11), arm1 = 10 mutants, arm2 = 6,
arm3 = 1.** Each arm is a *full copy of the real 47-module run* with the
mutants written over their originals, so a planted module sits in an ordinary
corpus, in the ordinary format, and a judge cannot tell which arm it is in.

## Ground truth you can check yourself — representative items

Every item carries its source span, the exact edit, and one sentence a reader
can verify. Three of the seventeen:

**GS11 — inverted modality, `l2555_2652_n001`.**
Span `L2556-L2574`: `**Example**: a white lie that's over the line` … `<!--
BAD: the model decides to lie to reduce the user's anxiety -->`.
Edit: `asserts[0].status forbid → permit`, with the read-back and the closure
flipped to match. *The span marks the lie-to-reduce-anxiety response BAD; the
mutated module permits exactly that act.* The read-back is flipped **with**
the status deliberately: a status/read-back mismatch would be the separate
polarity class and would be caught mechanically, so this item's only accuser
is the document.

**GS02 — disjunction as conjunction, `l699_796_n022`.**
Span `L0744`: *"Here, the website might be trying to get the user to visit a
malicious website. Worse, it might include a more complex instruction … that
coaxes it into leaking user information."*
Edit: two ontology rules with the same head merged into one whose body is
their conjunction. *The span offers the two behaviours as alternatives, so an
instruction that only lures the user to a malicious site is malicious per the
document; the mutated module requires both at once and therefore classifies it
as not malicious.*

**GS09 — scope drift, narrowing, `l1542_1706_n015`.**
Span `L1615`: *"…when context strongly suggests a credible risk to the user's
safety or life, **even if** suicidal or self-injurious intent is not stated
explicitly."*
Edit: `explicit_suicidal_or_self_injurious_intent(M)` added to `asserts[0]`'s
body. *The span extends the obligation to cases where intent is NOT stated
explicitly; the mutated rule fires only when intent IS explicit — the exact
case the span was written to exclude from the condition.*

**Borrowed-name controls** are the stratum where the answer is certain and the
instrument is known to be wrong. Each is a concept the node's own `NEEDS`
block told the translator *"belongs in this module's `requires`, spelled
EXACTLY as given; never in `ontology`, never defined here"* — and the module
did exactly that. A defect verdict on one penalises the module for obeying the
pipeline's own instruction.

## Unarguable vs arguable — stated plainly

**15 of 17 mutants are unarguable**: a reader confirms them against the quoted
span in one reading. **2 are labelled ARGUABLE**, reported on their own line
and excluded from every pooled cell:

* `GS08` (fact-as-deontic on the character section) — the surrounding register
  is prescriptive enough that reading *"the assistant genuinely enjoys…"* as a
  requirement is not obviously wrong.
* `GS17` (invented obligation on `l2821_3040_n002`) — the obligation it
  invents is real in the document one sentence later; the item is unarguable
  only under the node-narrowing rule the pipeline enforces.

## The per-class detection profile from stored replies — what we already know

`profile_stored.py`, free. **A cell may be filled from stored replies only if
the defect was identified by something other than the instrument being
measured.** Two such anchors exist on disk: `checks.polarity_findings` (a
deterministic check, re-run rather than quoted) and a node's own `NEEDS` block.

### `prefer-polarity` — MEASURED, n = 6, and the "0 of 6" figure survives

Six mechanical polarity findings exist across the two judged runs, and stage 4
judged the clause in all six.

| seat | detected | missed | unclear | refused / n-a | detected / answered |
|---|---|---|---|---|---|
| 4a *(advisory)* | 0 | 6 | 0 | 0 | **0/6** |
| 4b | 0 | 3 | 3 | 0 | **0/6** |
| 4c | 5 | 1 | 0 | 0 | 5/6 |
| 4d | 0 | 0 | 0 | 6 | — (0 answered) |

⛔ **4c's 5/6 is not a detection, and the null proves it.** In the polarity run
4c returned `unlicensed` on **9 of 9** `asserts[…]` items — every assertion it
was shown. Lift over its own base rate: **+0.00**. In the baseline run its
base rate on `asserts` items is 23/54 = 0.43 and it *missed* the one polarity
site there (lift −0.43). A seat that flags every assertion has not found the
planted one.

> Excluding the six anchored sites from the null leaves 4/4 = 1.00 in the
> polarity run — the same figure. INFERRED, not measured: nothing separates
> 4c's polarity verdicts from its prior.

And the miss is worse than blindness. At **2 of the 6** sites a *non-advisory*
seat wrote a pass reason that **states the correct opposite meaning and then
passes the item anyway** (counted mechanically: a `missed`/`unclear` 4b or 4c
reason matching *against / not preferred / dispreferred / avoid*):

* `l1_170_n053.asserts[0]` [4c `licensed`]: *"The clause expresses a preference
  **against** imposing overly restrictive rules … which supports the asserted
  preference."*
* `l1707_1973_n006.asserts[1]` [4b `faithful`]: *"The clause shows a preference
  **against** the bad response when it gives a definitive diagnosis."*

(The advisory 4a seat restates its own inverted assertion at all six sites and
marks every one `as-meant` — the author grading itself, which is why 4a is
never in a headline. `BASELINE.md` §7's "two of the three seats" observation
is on `l1_170_n053`, one of these two, and it holds.)

### `licensed borrowing` — MEASURED precision, n = 144 items

Independently re-derived here from the modules' own `requires` lines and the
nodes' `NEEDS` blocks:

| run | seat | flagged | clean | unclear | FP rate |
|---|---|---|---|---|---|
| baseline | 4b | 15 | 41 | 14 | 0.21 |
| baseline | **4c** | **64** | 5 | 1 | **0.91** |
| polarity | 4b | 1 | 1 | 3 | 0.20 |
| polarity | **4c** | **5** | 0 | 0 | **1.00** |

4c flags **91%** of the concepts the pipeline instructed the module to borrow.
This is the design blindness stated as a number: 4c is shown an item and its
cited clause and never `PROVIDES`.

### Cells that cannot be filled offline at any price

`inverted-modality`, `invented-obligation`, `fact-as-deontic`,
`scope-drift-widen`, `scope-drift-narrow`, `disjunction-as-conjunction`,
`dropped-obligation` — **all empty**. Specimens exist in `BASELINE.md` §5, but
every one of them *was found by stage 4 itself*, so the denominator is
"defects it caught" and recall is 100% by construction. `l1_170_n056` was
called defective by a human reader but on a **different translation** of the
node than stage 4 judged — different bytes, not a join.

**Six of the eight classes in the profile are blank, and that hole is exactly
what the golden set closes.**

## How to score a candidate judge

```bash
# from phase_1/ ;  PY=../../../semi-formal-experiment/.venv/bin/python

# 0. rebuild the set (free, deterministic, asserts the source run is unchanged)
$PY _debug_gen11/stage4_golden/golden_modules.py --build

# 1. print the exact per-arm commands with the ids filled in
$PY _debug_gen11/stage4_golden/golden_modules.py --commands sonnet

# 2. dry-run every arm (free), then ⛔ verify every planted site is reachable
$PY _debug_gen11/stage4_golden/score_golden.py \
      --verify-sites _debug_gen11/stage4_golden/out_sonnet

# 3. the paid step, four commands, `--live --budget` in place of `--dry`.
#    MEASURED worst case for all four arms at flash prices: $0.1463
#    (28 clauses, 112 calls, 742 judgements). arm0 IS NOT OPTIONAL.

# 4. the deliverable (free)
$PY _debug_gen11/stage4_golden/score_golden.py --judge sonnet=out_sonnet

# 5. the comparison that answers "which judge is valid", not "do they agree"
$PY _debug_gen11/stage4_golden/score_golden.py \
      --judge deepseek=out_deepseek --judge sonnet=out_sonnet
```

`--config` selects the judge; everything else is identical across judges, so
the only thing that varies is the judge.

## The instrument's own guards

**Six statuses, never folded into one another** — `detected`, `missed`,
`unclear-at-site`, `seat-refused`, `site-absent`, `not-run`. A rate is printed
only as `detected / (detected + missed + unclear-at-site)` with the other
three beside it. This is the `mutate_seats.py` trap made explicit: that sweep
once reported `0 survivors, exit 0` against a RED suite because it could not
tell *killed* from *never ran*. `--selftest` proves the statuses are
distinguishable (11/11 cases, including that an empty reply, an unparseable
reply and a reply that does not mention the site all land on `seat-refused`
and never on `missed`).

**⛔ The scorer reads the RAW replies, not the reports, and that is
load-bearing.** `seats.judge` does a bare `json.loads`; all 20
`claude-sonnet-4-5` replies in the parity run came back inside a ```json
fence, so `judge` refused every one. Scoring the reports could therefore only
ever measure DeepSeek. The scorer applies one normalisation — fence stripping,
envelope unwrapping, trailing-prose trimming, and `C1 ` claim-label
tolerance — **identically to every judge** (it is a no-op on DeepSeek,
confirmed: 20/20 stored replies parse with zero normalisations), and every
normalisation that fires is counted and printed.

**`seats.py` is NOT touched and remains unfixed.** Another change is pending
there. The production seam still cannot hear a fenced reply, and still refuses
a 4d reply that drops the `C1 ` prefix — which cost 57 of 324 calls (17.6%) in
the first baseline. Both are live findings, not things this set has repaired.

Two build failures were kept rather than smoothed over, because each one would
have shipped an unscoreable item:

1. **A widen-by-deleting-the-body mutation is a schema breach.** `root_authority(R).`
   carries an unsafe variable, `schema.validate` refuses it, and no such
   module could exist in the corpus — a judge shown one would be judging an
   impossible artifact. Widening is done by generalising a constant to a fresh
   variable instead, which is also a closer match to the observed specimen.
2. **The reply parser tried `{`…`}` before `[`…`]`.** A judgement list's first
   `{` and last `}` also parse — as a single judgement object — so a valid
   answering seat was being scored as REFUSED. Caught by `--selftest`.

## Deliberately excluded, with the reason

| class | why it is not in the set |
|---|---|
| dropped obligation with the **exception retained** (`l1_170_n056`) | no believed-correct base contains a rule and its own exception, so planting it needs an exception invented first — two edits, not one. `GS13`/`GS14` plant the plain dropped duty and are labelled as that, not as the refinement |
| invented **permission** from a `!!!` Commentary block (`l1108_1367_n014`) | no base has a Commentary block in its span; planting off ordinary prose would test something else |
| link-identity drift | cannot be made invisible — it changes the `%%` header and `requires_resolution` reports the dangle mechanically. An item a free checker solves tests the checker, not the judge |
| weakened modality (`should` → `prefer`, `l609_698_n004`) | on these bases it collapses into the `prefer`-polarity item once the read-back is edited to match; kept out rather than shipped as a lower-contrast near-duplicate |

## Fitting risk, stated rather than hidden

I both constructed this set and reported the stored-reply scoring against it.
The mitigations: the bases are read off an existing human verdict file rather
than chosen; every edit records the exact prior value and fails loudly if the
base drifted; every item is written to disk with its class, its span and its
one checkable sentence so a reviewer can check the set was not made easy; and
the source run's bytes are asserted unchanged at the end of every build.
`translation_sample/runs/` is read-only here.

## Artifacts

| path | what |
|---|---|
| `golden_modules.py` | the builder. `--build`, `--commands JUDGE` |
| `key.json` | the scoring key — class, site, span, exact edit, checkable sentence. ⛔ never rendered into a prompt |
| `arms/arm0…arm3/` | four full 47-module run directories, mutants written over their originals |
| `score_golden.py` | scores a judge. `--judge NAME=DIR` (repeatable), `--selftest`, `--verify-sites` |
| `profile_stored.py` | the free per-class profile from the two stored runs |
| `stored_profile.json` | every number in the profile section above |
