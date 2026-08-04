# The attribution ladder — plan of record

> # ⚠️ READ THIS BOX BEFORE ANYTHING ELSE — THE LADDER IS NOT THE PLAN
>
> This file is named after an experiment that has since been **demoted**, and
> most of what follows is a record of how that happened rather than a live
> instruction. As of end of 2026-08-02:
>
> | | status |
> |---|---|
> | **Grammar extension** (polarity, deontic force, ordered principals, condition/consequent) | **⬅ THE LIVE WORK.** Matt-approved, ~$0.55, gated on a clean-context review before any paid call |
> | The six-rung ladder | ⛔ demoted. Its one goal-connecting step is ~30x under-powered |
> | Step 5 — Sol / frontier annotation | ⛔ dead. $41.72 even fully cached; output is 86% of the bill |
> | Query-side tuning (DF/breadth) | ⛔ closed. Measured negative, see the next section |
> | Over-assertion as an intervention | ⛔ closed. Null against a matched control |
> | Read-back | ✅ ran at full scale; the result that redirected everything |
>
> **The one-line state of the project:** the atoms are an adequate *index* and
> a poor *representation*; representation was never the relevance ceiling
> (capacity bound +0.972 vs a +0.555 bar); and the binding constraint on every
> remaining question is **n=9 behaviours**, which no amount of ontology or
> query work moves.
>
> Salvaged from the ladder and still in use: the rung-1.5 **notation** (now
> `grammar.py`), the four polarity/role **operators** in `structural.py`, the
> **rate-cap** machinery, and the **preflight** spend guard.

**Original status: AGREED 2026-08-02, then AMENDED the same day after an
adversarial drift review returned SEVERITY-1 findings.**
Written so a reviewer can hold the work to it. If the work diverges from this
document, the document is wrong or the work is — say which.

Spend at time of writing: **$1.520 of $7.50** (`spend.py`), plus 6 unlogged
`gpt-oss-20b` artifacts, so treat $1.52 as a floor.

---

## ⛔ THE QUERY-SIDE LINE IS CLOSED (2026-08-02) — DF/breadth measured, negative

`breadth_filter.py`. Pre-declared Otsu cutoff on the DF distribution (zero free
parameters, declared before any score; `cutoff()` proven by spy test to open no
file and call neither `universe()` nor `score()`). Controls matched on
**occurrences**, not names — 43 broad names carry 674 occurrences where 43
random names carry ~190, so a name-matched control would have been the
"couldn't come out otherwise" trap for the third time.

| arm (`combined` V1@any, 589 universe, 9 cells) | ΔMCC | 95% CI |
|---|---|---|
| filter broad atoms | **−0.1248** | [−0.2104, −0.0351] |
| random control, 40 draws | −0.0616 | SD 0.0421 |
| contrast: filter *lowest*-DF | −0.0089 | [−0.0232, +0.0059] |

**Three independent things agree it is dead:**
1. Filtering broad atoms **hurts**, CI excluding zero.
2. **The contrast fails.** Breadth predicts high-DF and low-DF move in
   OPPOSITE directions. Under both compliant modules they move in the SAME
   direction at a matched occurrence budget. The arms track how much was
   deleted, not from which end.
3. The DF sweep is **monotone-negative**; its best row is "no filtering at
   all". Even the forbidden move — promoting the sweep's argmax — selects
   *don't do this*.

**Where the +0.0601 that motivated it went: it was an ERROR-RATE number.**
On MCC the same arm is −0.125, trading 916 false positives for 383 false
negatives. `unsupported_ablation` had already flagged exactly this trade at
−0.0074 in its own treatment arm; this is the same artifact seven times larger.
With 86% of errors being false positives, deleting anything improves error
rate for free. **An intervention that only moves error rate is not an
improvement, and I recommended this one on an error-rate number without
checking that it survived the balanced statistic.**

`HANDOFF.md:453-462` had already measured the same thing from the other side:
the supervised weighting is **anti**-correlated with IDF (positively-weighted
atoms have HIGHER document frequency), and 54 label-free re-weighting variants
bought at most +0.016. The broad atoms carry signal, not noise.

**Interpretability cost, had it worked:** 76 of 587 clauses emptied of all
atoms — unretrievable *and* unexplainable; citable query atoms per gold passage
0.82 → 0.27 (−67%). It would have bought MCC by deleting the explanations,
against a project whose stated value is auditability.

⇒ Query-side tuning is closed. The binding constraint remains **n=9
behaviours**, and nothing on the query side moves it.

## ⛔ SECOND REVIEW (science + drift, 2026-08-02, later): PROCEED WITH CHANGES — and the ladder is NOT the next spend

Every number it was asked to check reproduced exactly. The findings are about
**inference and allocation**, not fabrication. Awaiting Matt's decision on the
reallocation; the $0 items are running.

**S1. Step 1's gate-clearing claim is module-dependent — the robust half points
the other way.** Re-run under the compliant modules:

| within-kind PRIMARY | relevance (bag) | structural@any | combined V1@any |
|---|---|---|---|
| faithful | −0.157 | −0.155 | −0.147 |
| ≥1 unsupported | +0.157 | +0.155 | +0.147 |
| **sufficient** | **−0.096 [−0.182,−0.014]** | −0.102 | **−0.077 [−0.176, +0.019]** |

Under `combined V1@any` — the best compliant config — **the `sufficient` CI
spans zero**. This plan cleared Step 1 on "sufficiency weakly predicts
retrieval error", which is the fragile half. The over-assertion finding is
robust across all three modules and is the real result. Restate the gate as:
**over-assertion predicts retrieval error; sufficiency does not survive the
module swap.** Being re-run now.

Also: **atom count is an uncontrolled common cause.** ρ(unsupported, error)
+0.185 vs ρ(atom count, error) +0.170; under `combined` both exclude zero.
Stratifying on atom-count tertiles attenuates `faithful` from −0.157 to −0.100
(~36%). Since 86% of errors are false positives, *any* property correlated with
firing more predicts "error" — "over-assertion causes FPs" and "broader atoms
cause FPs" are not separated by this design.

**S2. Step 3b — the ONLY step connecting the ladder to the goal — is ~30×
under-powered, by this repo's own numbers.** `ladder.py:1709` says it: 125 of
587 clauses re-annotated, so any delta is diluted ~5×. Against a noise floor of
0.0316–0.037 and a best prior estimate of a real annotation upgrade of **+0.005
n.s.**, that is ~+0.001 against ~0.035. It can only return a null, and the null
will be uninformative. **This is reason #2 that killed
`ONTOLOGY_REFINEMENT.md`, reappearing in the design that replaced it.**

**S3. Rung 1.5's load-bearing justification conflates two different
"negative"s.** The whole ladder rests on `HANDOFF.md:449` (3–11 query atoms earn
a negative weight "which our query cannot express"). The next two bullets of
that same section say those weights are anti-correlated with IDF in 8/9 cells
and regress on every available corpus statistic at **R² = 0.039 — "it encodes
atom identity."** A document-derived polarity prefix is a document feature; the
thing it must express is measured as *not a function of anything derivable from
the document*. And that fact is a **supervised, panel-fitted diagnostic** —
promoting it to the ladder's justification is panel analysis steering ontology
design, which is what the `weight_diag` fence exists to prevent.

**S4. Drift: yes.** The chain "better atoms → higher MCC" is measured shut at
every link — capacity bounds at +0.972 vs a +0.555 bar; text-only (+0.398)
scores *below* the atom index (+0.435); a real vocabulary upgrade moved +0.005
n.s. `HANDOFF.md:726`: **"n=9 is the binding constraint on every remaining
question. More passages buy nothing; more behaviours buy everything."** The
ladder adds no behaviours.

**S5. Sol is definitively dead.** Prompt caching now exists and was measured:
full ladder on Sol **$41.72** cached (from $69.51); rung 3 alone $7.78, floor
$2.69. Caching cannot rescue it — **output is 86% of the bill** (223,626 tokens
× $30/Mtok = $6.71 for rung 3 alone) and caching is input-side only. Step 5 is
closed, not pending.

**Ranked reallocation of the remaining $5.98:**
1. **$0** — the over-assertion ablation: delete judge-flagged unsupported
   atoms, re-score under `combined`/`structural` against a random-deletion
   control. Tests the one robust finding. *(running)*
2. **$0** — re-run Step 1 under the compliant modules, restate the gate.
   *(running)*
3. **~$0.15** — annotate the Anthropic constitution. The only independent
   replication available, and the explicitly-stated second half of the goal
   ("the spec can eventually be swapped out"). The ontology has **never** run
   against a second document.
4. **The bulk** — more frontier-judged behaviours. The frontier panel has
   **3**; `behaviours.json` holds **11**. This is the one purchase that
   relieves the constraint named as binding on every remaining question,
   including any future ladder result.
5. **The ladder, reduced and only if money remains** — rungs 0, 1, 1.5, null +
   controls; drop 2/3/4, which grant the freedom that produces the failure mode
   Step 1 actually identified.

**Also flagged: `semi-formal-experiment/` is NOT under version control.**
`.git` is at `ai_character_index/`; this directory is untracked. No
pre-registration claim in this project is independently verifiable, and there
is no recovery point. Fix before any further pre-registered step.

## Amendments (drift review, 2026-08-02)

The review reproduced **every** headline number in this document exactly, and
every Step 0 item checked out. The findings are structural. In severity order:

**A1. The ladder never measured relevance — BLOCKING, now fixed below.** Rungs
0-4 produce only fidelity/sufficiency/discriminability. No step scored a rung's
atoms against the panel with the shipped query, so even rung 3 lifting
sufficiency 0.16 -> 0.45 could not have shown the tool got better. That is the
entire goal. **Step 3b added.**

The review also found the mechanism runs the wrong way: sufficiency is
overwhelmingly a property of GLOSSES, but the compliant modules match on atom
NAMES and TYPES — only `relevance.py`, the invariant-10-violating bag scorer,
consumes glosses lexically. So naive "raise sufficiency" work improves the
module the contract is trying to RETIRE. And expressiveness has already been
measured as non-binding: `HANDOFF.md:236-239`, the atom index partitions 589
passages into 534 classes, bounding any function of the atom set at **+0.972**
against a bar of +0.555.

**The one mechanism that survives** — and it is now the load-bearing
justification for the whole ladder, replacing the representation-quality
argument: `HANDOFF.md:449` records that 3-11 of every 19-28 query atoms earn a
**negative** weight *"which our query cannot express"*. Rung 1.5's parseable
polarity prefix is a label-free, document-derived way to make that expressible
in a **structural** operator. Rung 1.5 is the point of the ladder; rungs 2-4
are ceiling probes around it.

**A2. Sol was under-costed by ~10x — STEP 5 BLOCKED.** This document says Sol
is "25x luna" and "same code path, same rate cap", which makes it **$10-15**,
not $1.00-1.50, against $5.98 remaining. Rung 1's "no eviction" ships the full
361-atom vocabulary every call: **39,022 chars ~= 9,755 input tokens per
call**, with no prompt caching anywhere in the repo. This is the SAME costing
error that killed `ONTOLOGY_REFINEMENT.md` (it priced the open-vocabulary pass
while eviction was what made that pass cheap). No Sol approval until a
`--dry-run` emits measured token counts, and Sol is then scoped to **rung 3
only** (+ rung 4 if rung 3 moves), not a five-rung replication.

**A3. Step 1 was under-powered and confounded.** 20 positives of 125 gives a
two-proportion MDE of **0.33 absolute**; a null is near-guaranteed regardless
of truth. Clause kind is a common cause of both variables, and the kind-level
confound alone is r=0.172 — essentially the n=125 significance threshold. Now
stratified by kind, MDE pre-registered, and **the null is a hard stop**, not a
"re-justification": continuing as conflict work requires Matt's explicit
sign-off as new scope.

**A4. "Each has a stop condition" was false** — only steps 0 and 1 had one.
Promoted to a prospective gate: **rung 3 ~= rung 0 on luna BLOCKS Step 5**,
emitted by the harness as an explicit PROCEED/STOP line.

**A5. The judge is unvalidated.** All six of read-back's pre-registered
predictions were wrong, several inverted, and nobody has checked that luna's
`faithful`/`sufficient` labels mean what the labels say. Positive control (feed
the clause's own text as the rendering -> must be sufficient) and negative
control (a different clause's rendering -> must not) now ship with the harness.

**A6. The synthetic-demo mitigation was syntactic, the leak is semantic.** A
substring test never fires on hand-written prose. The real channel is
SELECTION — which features get demonstrated, on what content, by an author who
has by then read panel-conditioned analysis. Demonstrations are now **written
and frozen with a sha256 BEFORE Step 1's output exists**.

Not yet actioned, carried as debt: the extraction surface (`annotate.py`) is
not covered by `test_no_reference_leak.py` at all, and no rung isolates
renderer artifacts from ontology artifacts (`render()` is fixed across rungs
while faithful=0.46 may be partly template-induced).

## The question

Read-back (n=125, pre-registered, 125/125 answered, $0.19) returned:

| | predicted | measured |
|---|---|---:|
| discriminable, hardest condition | 0.45 | **0.89** |
| faithful | 0.90+ | **0.46** |
| sufficient | ~0.35 | **0.16** |

and the cross-tab that matters: **91 of 125 clauses can be picked out of nine
same-section neighbours from their atoms alone, while a reader of those atoms
would not know what the clause requires.** Identification and representation
have come apart. The atoms are an adequate *index* and a poor *representation*.

The question this plan answers is **where that loss happens**, so that effort
goes to the component actually responsible:

1. **Segmentation** — the content is not in this clause; it is in a neighbour.
2. **Assignment** — content is in the clause, an atom could carry it, none does.
3. **Vocabulary** — content is in the clause, no suitable atom exists.
4. **Grammar** — content is in the clause and there is nowhere to put it.

## What we already know, free

Both role and polarity are *expressible* in the current grammar as name
conventions, and were barely used:

| | measured over `annotations_b8.json` |
|---|---|
| names encoding a role relation (≥2 principals) | **3 of 361** |
| `act` atoms naming any principal | **128 of 820 (16%)** |
| names carrying polarity lexically | 53 of 361 (15%), ad-hoc, **not machine-readable** |

So "the grammar cannot represent role/polarity" is **not established**. Some of
it is the prompt never asking. The ladder measures the ratio before any schema
change.

---

## Steps, in order. Each has a stop condition.

### Step 0 — close the drift gate *(✅ DONE 2026-08-02, $0)*

Suite **1153 passed, 3 skipped**. Both operator defaults flipped to `any_atom`
and mutation-verified; floors re-derived on the shipped path; the collection
guard rebuilt to name its guard files (the count alone let all three anti-cheat
files be deleted green); `readback` added to the anti-cheat scan; the withdrawn
premise deleted from `readback.py`; `MODULE_MAP.md`, `HANDOFF.md` and the blog
corrected. Original scope below.

Blocking. No spend until done. Remaining: re-derive the three quality floors
moved by the operator flip; `MODULE_MAP.md` rewrite; `HANDOFF.md:547` forward
pointer; delete `relevance.py:109-120`'s "report +0.187"; reconcile
`weight_diag.NOISE`; re-run `benchmark.py --compare-modules` so shipped
defaults and the recorded headline agree.

Done when: full suite green and no shipped default contradicts `HANDOFF.md`.

### Step 1 — does any of this buy *relevance*? *($0, offline)*

Correlate per-clause `sufficient` / `faithful` (125 clauses) with per-clause
retrieval error against the panel.

- Reads the panel ⇒ **fenced diagnostic-only**, like `weight_diag`. Its output
  may never inform the ontology, the vocabulary, or a threshold.
- **Stop condition:** if sufficiency does not predict retrieval error, then the
  grammar's blind spots are orthogonal to relevance. Steps 2–5 are then
  *conflict* work, not relevance work, and must be re-justified against the
  standing "focus on relevance" instruction before proceeding.

### Step 1 RESULT *(✅ DONE 2026-08-02, $0)* — the gate does NOT fire, and the mechanism is inverted

Sufficiency weakly predicts retrieval error, so the ladder is not orthogonal to
relevance and Steps 2-5 remain relevance work. **But my stated prior was wrong
in both halves**, and the correction matters more than the verdict:

| within-kind, 20k-resample clause bootstrap | effect [95% CI] |
|---|---|
| faithful | **−0.157 [−0.251, −0.062]** |
| ≥1 unsupported phrase | **+0.157 [+0.062, +0.250]** |
| sufficient | −0.096 [−0.182, −0.014] |
| ρ(count of unsupported phrases, error) | +0.185 [+0.011, +0.352] |
| missing **party** / missing **deontic** | not distinguishable from zero |

I predicted party-loss would predict relevance error and deontic-loss would
not. **Neither is distinguishable** — this design cannot separate them. What
does predict error is **over-assertion**: 86% of retrieval errors are false
positives (312 FP / 49 FN), and unsupported atoms give the query extra surface
to match on. The loss that costs relevance is content the atoms **add**, not
content they **drop**.

⚠️ **Consequence for the rate cap, now required of the harness**: rungs 2-4
grant exactly the freedom that produces unsupported assertions, and the cap as
specified prices atoms and gloss characters but not over-assertion. A rung
could win by asserting more, and the table would read that as expressiveness.
The unsupported-phrase rate is now a first-class column and bounds the gate.

⚠️ **Power caveat, not to be dropped**: observed effects sit at or below the
MDE (sufficient 0.184 means / 0.314 two-proportion). ~20 splits tested, 5 CIs
exclude zero, ~1 expected by chance. Noisy estimates of large effects, not
precise estimates of small ones. Directions are worth designing around;
magnitudes are not worth quoting.

Also: the phrase categoriser's exact-set match is **0.600 [0.474, 0.714]** on a
held-out sample — so the "party 23% / deontic 15%" split that motivated the
P0/P0.5 framing is itself ~40% wrong per phrase, single-annotator, with
inter-annotator agreement unmeasured. Do not build a schema change on it.

### Step 2 RESULT *(✅ DONE 2026-08-02, $0)* — segmentation is not the constraint

**~2.6% of the sufficiency loss** (Wilson 0.8–10.2%); >90% of missing content
is in the clause's own text. The conditional hypothesis is **refuted as
stated**: "must not X" / "unless Y" split across clauses happens once in 25.
The defeaters are in the clause and the atoms drop them — an assignment/grammar
failure, in scope for rungs 1–3.

New confound found, and it attacks the rung-3 gate directly: **16 of 125
clauses are structurally orphaned** (list items severed from their lead-in,
bare antecedents). No rung can make those sufficient. Left in the denominator,
rung 3 ≈ rung 0 on that subset reads as "the grammar was never the constraint"
when the truth is "the clause was never whole". The gate is computed on the
excluded set, with both numbers printed.

### Step 2 — segmentation attribution *($0–0.02, mostly offline)*

For each of the 268 missing phrases, is its content present in an adjacent
clause in the same section? If yes, that is a segmentation loss and no atom
change fixes it. Prior: small overall, non-trivial for `conditional`
(currently 1/25 sufficient).

### Step 3 RESULT *(✅ BUILT 2026-08-02, $0)* — and the cost is the headline

`ladder.py` (~1700 loc), `ladder_prompt.md`, `test_ladder.py` (112 tests).
Suite 1314 passed. Zero API calls. 17 planted mutants, all caught — five
escaped the first pass and each exposed a genuinely weak test (a row-grep that
matched the wrong column; an orphan-gate fixture where both arms cleared).

**MEASURED COST, from real token counts — the plan's estimates were both wrong:**

| | plan said | measured (worst / best) |
|---|---|---|
| luna, full ladder | $0.40–0.60 | **$2.78 / $0.64** |
| sol, full ladder | $1.00–1.50 | **$69.5 / $16.1** |
| sol, meta-only n=25 | — | $13.3 / $2.66 |

**Sol is infeasible at any point in the planned range** against $5.98
remaining — off by 10–45×, not by a rounding error. The driver is that the
361-atom vocabulary block is re-sent on every call (~9,755 input tokens) and
**nothing in the repo requests prompt caching**, though the constant prefix is
~95% of each request. That lever is being built now; until it lands, Step 5
stays blocked and the honest answer to "can we buy a ceiling?" is no.

Note this is the *third* time this project has mis-priced the same operation:
`ONTOLOGY_REFINEMENT.md` priced the open-vocabulary pass while eviction was
what made it cheap, this plan repeated it, and both times the error pointed
the same way — toward spending.

**Design objections the builder raised against its own work**, kept because
they bound the result:
* Rung 1.5 as specified was self-contradictory ("existing vocabulary, no
  coining" + "ordered principals on every act" — almost no shipped name
  carries a principal). Resolved by decorating a closed stem
  (`[polarity_]stem__principals`); that is a judgement call and the single
  most consequential one made.
* **The rungs are not rendered identically.** Rungs 1.5+ need a different
  closing paragraph because read-back's ("records no polarity, nothing about
  who is addressed") becomes a false assertion. A real confound, printed in
  the artifact rather than hidden.
* **The relevance hook is structurally under-powered**: 125 of 587 clauses are
  re-annotated (~5× dilution) and the compliant modules match names and types,
  so any rung whose gain is in glosses is invisible to it by construction. A
  null there must not be read as "the rungs didn't help".
* Rung 0 is exempt from the rate cap because it *defines* the budget, so rungs
  1+ face a per-clause ceiling of 5 that rung 0's one 8-atom clause never did.

### Step 3 — build the ladder harness *($0)*

One command, fixed seed, deterministic table. Model is a parameter so
`--model luna` and `--model sol` are the same code path.

| rung | relaxes | isolates |
|---|---|---|
| 0 | — | baseline (F 0.46, S 0.16) |
| 1 | one clause at a time, existing 361-atom vocabulary, no eviction | **assignment error** |
| 1.5 | + prompt requires ordered principals on every `act`, polarity as a reserved parseable prefix | **prompt vs grammar** |
| 2 | + may coin atoms; per-occurrence glosses | **vocabulary inadequacy** |
| 3 | + unlimited freedom within the schema | **the grammar ceiling** |
| 4 | + may invent structure (relations, polarity, deontic) | **value of extending the grammar** |

Rung 4's output is the *design document* for any schema change — the structure
a strong annotator reaches for in this document, rather than my guess.

**Rate cap, non-negotiable.** Every rung is held at the shipped encoding budget:
≤2.78 atoms/clause, ≤211 characters of gloss, with the atom reuse profile (df
distribution, hapax share) reported in the same table. A rung that reaches
sufficiency by making every atom a hapax has demonstrated memorisation, not
expressiveness. The withdrawn refinement design died of exactly this hole — its
objective priced atom names but not glosses — and the ladder must not reopen it.

**Coverage gate.** The harness refuses to emit a table below 100% coverage.
The read-back run lost 52 of 125 calls to rate limits and reported
`unanswered: 0` while a condition sat at 90/125, with losses concentrated in
whole clause-kind strata. That defect moves a number further than the effect
being measured.

**Null-ontology arm.** `render([], kind)` still emits a kind label and fixed
boilerplate. Fidelity is run on empty renders for the same clauses, so no rung
can claim credit for a target-independent constant.

### Step 3b — connect the ladder to the goal *($0)* — ADDED BY AMENDMENT A1

Score each rung's atoms with `benchmark.py` under the **shipped compliant
query**, on the true 589-passage universe. **Measured once, reported, never fed
back** — the phrasing `ONTOLOGY_REFINEMENT.md:118-120` got right. Invariant 9
bars *fitting*, not *measuring*, and the fence stated in the first draft of
this plan was broad enough to forbid the one measurement that connects the
ladder to the tool.

Without this step no rung result can support a claim about tool quality, and
the plan would have produced a representation-quality paper for a
relevance-quality project.

### Step 4 — ⛔ BLOCKED by engineering review. Run on luna *(ceiling $5.4, not $2.78)*

A clean-context engineering review returned **NOT SAFE TO RUN LIVE**, four
SEV-1 defects. Fixes in flight. The review confirmed the gates fire, the sha
freeze holds, the notation is collision-free over all 361 names and the cost
arithmetic re-derives — these are what it broke:

1. **`run_ladder` never writes `clause_kinds`**, so the per-kind table silently
   vanishes and `sufficient_headline` equals `sufficient_standalone` while the
   prose says it excludes `example`. **The tests passed only because they
   hand-inject the key.** A fixture that supplies what the code forgot is not
   a test — this is the same shape as the `section_path` bug that left the
   section channel dead through 631 green tests.
2. **The rate cap does not bind on rung 4.** Nested strings are priced but not
   collected, so the binary search converges to ceiling 0 — deleting every
   legitimate top-level gloss while the nested prose survives into the render.
   Rung 4 could win by asserting more, the exact hole this cap exists to close.
3. **The atom-drop trim is strata-correlated** (lexicographic tie-break, clause
   ids contiguous within kind): 28 drops land 9 on `example`, 1 on
   `definitional`. Same defect class as the read-back loss, and `by_kind` is
   read straight off it.
4. **The judge controls have no coverage gate** — 2 surviving control calls
   print PROCEED on the instrument gate that certifies every rung above it.

⚠️ **The luna ceiling is $5.4, not $2.78.** "$ worst" assumed reasoning at the
batch-8 mean, but that distribution already brushes `--max-tokens 4096` (p90
3202 / max 4060). At batch 1 running to the cap it is **$5.39 against $5.98
remaining** — i.e. the ladder could consume the entire remaining budget. Rungs
must run as separate invocations with a pre-flight `spend.py --check`.

### Step 4 — run the ladder on luna and validate *(~$0.40–0.60, re-cost via `--dry-run` first)*

Then the three reviews (engineering / science / drift) on the results before
anything is concluded from them.

### Step 5 — ⛔ BLOCKED. Sol, scoped to rung 3 *(cost UNKNOWN until `--dry-run`)*

Sol is `gpt-5.6-sol`, $5/$30 per Mtok — 25× luna. **An oracle run by a weak
model is not a ceiling**, which is the whole argument for spending here. Same
code path, same seed, same rate cap, so the delta is clean.

**Three gates, all of which must clear first:**

1. `--dry-run` produces a MEASURED token count and therefore a real price. The
   $1.00–1.50 in the first draft of this plan was arithmetic on a stale figure
   and is withdrawn; on this plan's own "25×" it is $10–15, which does not fit
   the budget. **Nothing is approved until the measured number exists.**
2. Rung 3 must move on luna. If rung 3 ≈ rung 0, the grammar was never the
   constraint and there is no ceiling worth buying.
3. Matt's explicit approval of the measured price.

**Scope: rung 3 only** (plus rung 4 if rung 3 moves). The oracle argument
justifies a *ceiling probe*, not a five-rung replication — using it for the
latter is how a sound argument becomes a rationalisation for a frontier run.

⚠️ **Withdrawn over-claim.** This was billed as "the long-open *do better
models produce better atoms?* experiment". It is not. `HANDOFF.md:241-252`
closed that question on two objections: unattributable (21% vocabulary overlap
between runs) and under-powered (MDE 0.032–0.045 against a best estimate of
+0.005). Fixing the vocabulary answers the first and is a real improvement. It
does **not** answer the second. What Sol actually measures here is whether Sol
produces more *reconstructive* atoms — a different question, worth asking,
which should be named as itself.

---

## Matt's point about examples — and the hazard in it

Correct and adopted: rungs 1.5+ require the extractor to be *shown* the grammar
features, not merely told. Format demonstrations are not labelled examples in
the sense invariant 9 forbids — that bars examples of the panel's
behaviour→passage judgements, not demonstrations of annotation format.

**But there is a real leak path and it must be closed in the design, not
policed after.** If the demonstration clauses are drawn from the Model Spec,
the extractor sees hand-curated annotations of evaluation-set clauses, and any
care taken in choosing them is a channel from a human who has seen the panel.

Rule: **demonstration clauses are synthetic, written to exercise the grammar,
and are not passages of either spec.** They ship in the prompt file, are
diffable, and `test_no_reference_leak.py` gets a check that no demonstration
string is a substring of either spec. A reviewer should treat any demonstration
sourced from the spec as a blocking finding.

---

## What I will *not* do

- Not extend the schema before the ladder says the grammar is the constraint.
- Not restart the withdrawn refinement loop (`ONTOLOGY_REFINEMENT.md`, ⛔).
- Not spend on Sol without explicit approval.
- Not report a rung table at <100% coverage.
- Not let step 1's panel-reading diagnostic inform anything ontology-side.

## How to tell if this went wrong

- A rung's sufficiency gain is accompanied by a rise in hapax share ⇒ the rate
  cap failed and the number is memorisation.
- Rung 3 ≈ rung 0 ⇒ the grammar was never the constraint; steps 4–5 should have
  stopped early.
- Any number in a summary that I cannot regenerate from a committed script.
  `combined.MEASURED` and `section.MEASURED` are already hand-transcribed
  constants with no in-repo generator; the ladder must not add a third.
