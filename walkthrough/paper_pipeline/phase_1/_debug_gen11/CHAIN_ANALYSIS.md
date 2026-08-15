# CHAIN_ANALYSIS.md — repair-chain dynamics: what separates a chain that recovers from one that freezes

Scope: the CHAIN as the unit. The mechanism cut is `class_*.md`, the cost cut is
`SUMMARY.md`, the fixed-point measurement is `class_repair-fixed-point.md`; this file does
not redo any of them and cites them where it builds on them. **Zero project API spend.**
Every number below is recomputed from the stored `*.transcript.json` files and re-validated
offline through `checks.run_checks` / `schema.validate`. Nothing under `runs/`,
`translation_sample/runs/`, `repair_graveyard/` or any pipeline module was written to.

Populations:
* **08-14 pair** — `20260814-163457` (12 clauses) + `20260814-173322` (88) = 100 clauses,
  230 calls, 53 chains with at least one repair round. Completed runs, stable.
* **08-15** — `20260815-070038`, 69 clauses, 157 calls, 43 repair chains. **The standing
  caveat in `class_repair-fixed-point.md` said this run was in flight. It is now
  complete** (`inflight/` empty, `run.json` and `health.jsonl` last written 07:32, results
  present for all 69). Its counts are used here as a *replication*, and — per
  `TRANSLATION_REPAIR_CENSUS.md` §9 — **no count from it is proposed for a test pin**.

---

## 0. Headline

The thing that separates a chain that recovers from one that freezes is not the defect, not
the number of findings, not the clause, and not the quality of the repair message. It is
**whether the model is still producing answers it has not already produced.**

| chain, after round 1 | n | ended `translated` |
|---|---|---|
| every reply distinct from every earlier reply | **64** | **63 (98%)** |
| some reply repeats an earlier reply in the same chain | **32** | **3 (9%)** |

(all three runs pooled, 96 repair chains. 08-14 pair alone: 31/32 vs 2/21. 08-15 alone:
32/32 vs 1/11. The split replicates across runs held out from each other.)

**Every one of the 19 lost chains in the 08-14 pair repeats an earlier reply. None of the
31 clean recoveries does.** Sensitivity 19/19, specificity 31/33.

This is a strictly better predictor than the byte-identical-to-*previous* signal that
`class_repair-fixed-point.md` measured: adjacent-freeze catches 17 of the 19 lost chains,
repeat-of-any catches 19 of 19. The two it adds are the *oscillating* chains —
`l1_170_n058` and `l1_170_n078` — which never emit the same bytes twice in a row but do
return to an earlier answer (`n078` replies A,B,C,**A**,D; `n056` replies A,B,**A**,**A**,**A**).
The model is not stuck on one answer; it is stuck in a **cycle over a small answer set**.
Median distinct replies in a 5-call lost chain: **2**.

---

## 1. Q1 — what distinguishes a chain that recovers from one that freezes

Measured per chain over the 08-14 pair: 33 recovered (translated after ≥1 repair round),
19 lost (`unrepaired`), 1 `abstained_under_repair` (`l171_426_n003`).

| feature | RECOVERED (33) | LOST (19) | discriminates? |
|---|---|---|---|
| round-1 findings, mean / median | 2.15 / 1 | 2.47 / 1 | **no** |
| round-1 *distinct* findings (dedup'd) | 1.97 | 1.95 | **no** |
| round-1 `check_id` | schema-breach 32, unresolved-reference 1 | schema-breach 17, clingo-error 1, unresolved-reference 1 | **no** |
| round-1 finding *class* (message shape) | 14 undeclared-body-name, 12 borrowed-no-gloss, +6 others | 10 undeclared-body-name, 5 borrowed-no-gloss, +4 others | **no** |
| output length, round 1 (chars) | 2465 | 2756 | no |
| output length, last round | 2838 | 3091 | no |
| Δ length over the chain | +372 | +335 | **no** |
| round-1 findings still present at the end | 1.03 of 1.97 (52%) | 1.32 of 1.95 (68%) | weak |
| chains where the finding set ever GREW (a defect was traded in) | 11 (33%) | 6 (32%) | **no** |
| **chains with ≥1 round whose finding set is unchanged** | **3 (9%)** | **19 (100%)** | **yes** |
| **chains with ≥1 byte-identical-to-previous reply** | **1 (3%)** | **17 (89%)** | **yes** |
| **chains that repeat ANY earlier reply** | **2 (6%)** | **19 (100%)** | **yes** |

Read the top half of that table carefully: **nothing about the difficulty of the clause,
the number of defects, the class of defect, or how much the model wrote separates the two
outcomes.** Lost chains do not start with more findings, harder findings, different
findings, or longer output. Defect trading (`SUMMARY.md` §4) happens at the same rate in
both — 33% vs 32% of chains — so it is *not* the loss mechanism either; it is what a
chain does while it is still moving.

Three sub-answers to the specific questions asked:

* **Were the round-1 findings later ADDED to rather than fixed?** Both groups add. Lost
  chains add *less* (mean +0.26 new findings vs +0.64 for recovered) because a frozen chain
  cannot add anything — it is not editing. The chains that grow their finding set are
  disproportionately the ones that *recover*: motion, even wrong motion, correlates with
  convergence.
* **Did the model change anything at all between rounds?** This is the whole answer. In
  the 19 lost chains, 50 of 76 repair rounds returned bytes identical to the immediately
  preceding reply, and every chain returned to an earlier answer at least once. Four
  (`n014`, `n047`, `n062`, `n084`) emitted exactly one distinct reply across five calls.
* **Did the repair message name a defect it could act on?** Yes, in every lost chain. Not
  one lost chain received a "(no error-severity findings — nothing here is yours to fix)"
  log, and not one received only notes. Every message named a concrete predicate and
  offered three concrete homes for it. §2 shows the instruction was not merely
  *nameable* but **actually actionable**: a different model performed the named repair in
  one turn from the identical message.

### The one counterexample worth naming

`l1_170_n057` froze at rounds 1 and 2 (three identical replies), then moved at round 4 and
translated at round 5. `l1_170_n016` cycled (reply 3 = reply 1) and translated at round 4.
`l171_426_n005` (08-15) froze at round 1 and translated at round 4. Three chains in 96 —
**~9–12% of repeat-chains do eventually recover**, which is what makes "stop and abandon"
the wrong policy and "stop and redraw" the right one (§4).

---

## 2. Q2 — why a chain freezes: four hypotheses, three killed by evidence

### H-D: provider-side determinism — **REFUTED**

If the byte-identity came from the provider (caching, temperature-0 behaviour, a
deterministic backend), the same prompt bytes would produce the same reply across runs.
They do not.

> For all **19** clauses that the 08-14 loop lost, the 08-15 run issued a first call with
> **byte-identical `prompt_user.txt`, byte-identical `prompt_system.txt`
> (`aa5c59bf8128f8dbae65563946d8c5aae69d9d01`), identical `system_sha`, `schema_sha`,
> `provenance_hash`, model, and `max_tokens`/`format_forcing`/`max_attempts`.**
> **0 of 19 attempt-1 replies were identical across the two runs.** Reply lengths differ
> by up to 3.5× on the same prompt (`n043`: 1193 vs 4222 chars; `n015`: 3854 vs 574).

The config sets `temperature: 0.2`. Sampling is live. **A model that produces a different
answer every time it is asked cold, and the same answer five times in a row inside a
transcript, is being frozen by the transcript, not by the provider.**

### H-A: the repair prompt is uninformative or self-contradictory — **REFUTED for the frozen chains**

Experiment (Q5), zero project spend. Four frozen 08-14 chains — `l1_170_n062` (5 identical
replies, 9 findings), `l1_170_n014` (5 identical), `l1_170_n084` (5 identical),
`l1_170_n056` (cycle A,B,A,A,A) — were replayed through local **Haiku** stand-in
translators in two conditions:

* **accum** — the verbatim stored transcript up to and including the last repair message,
  with the stored `prompt_system.txt` as the system instruction. This is the exact input
  DeepSeek froze on.
* **fresh** — the first user turn only, same system instruction.

Every output was validated offline with `schema.validate` and `checks.run_checks(concepts=None,
attempt=1)` — the identical call the loop makes.

| clause | accum → | fresh → | what the accum reply did |
|---|---|---|---|
| `l1_170_n062` | **validate OK, checks `translated`, 0 errors** | validate OK, `translated` | moved `default_instruction/1`, `overridable_guideline/1`, `derived_on_the_fly/1` into `inputs` |
| `l1_170_n014` | **validate OK, `translated`, 0 errors** | validate OK, `abstained` | moved `sets_out_guidance/1`, `primarily_for_humans/1`, `useful_context_for_model/1` into `inputs` |
| `l1_170_n084` | **validate OK, `translated`, 0 errors** | validate OK, `translated` | moved `hidden_chain_of_thought_message/1`, `guides_model_behavior/1`, `not_exposed_except_summarized/1` into `inputs` |
| `l1_170_n056` | **validate OK, `translated`, 0 errors** | validate OK, `translated` | added the two missing `concepts` glosses for `user_authority/1`, `authority_levels_hierarchy/2` |

**8 of 8 passed `schema.validate`; 7 of 8 reached `translated`; the eighth abstained, which
is a legal answer.** In the `accum` condition — the condition where DeepSeek re-emitted the
same bytes four times — **4 of 4 performed the exact edit the repair message asked for, in
one turn.** For `n062` the resulting module is 99% textually identical to the frozen one:
the difference is three strings appended to an empty `inputs` list.

Two consequences:
* The repair message **contains sufficient information to repair the module.** It is not
  uninformative and it is not self-contradictory. The class doc's reading of the M1
  parenthetical as a trilemma (`class_no-legal-bucket.md`: "`ontology` regresses,
  `requires` is reserved, `inputs` is restricted") is a fair reading of the *prompt's*
  ambiguity, but `inputs` was in fact legal and accepted for all four.
* **Caveat, recorded as the README requires.** Haiku is a different model, and the stand-in
  harness is not the translation harness: the agents ran with tool access and free-form
  reasoning, without `json_schema` format forcing, without `max_tokens: 4096`, and each
  produced one turn rather than a live continuation. These results are **evidence about the
  LOOP** — that the information needed to converge is present in the transcript the loop
  hands back — and are **not** a prediction that DeepSeek-V4-Flash would do the same.

### H-C: a defect the model genuinely cannot fix — **REFUTED for 14 of 19, SURVIVES for 4**

The whole-population version of the same test. Re-validated today, offline, with the exact
in-loop arguments (`corpus_ids` = all 773 `node_corpus_all.json` ids, `concepts=None`,
`attempt=1`):

| | 08-14 final module | 08-15 final module |
|---|---|---|
| 14 clauses (`l171_426_n005`, `n006`, `n014`, `n023`, `n028`, `n037`, `n043`, `n047`, `n052`, `n062`, `n065`, `n069`, `n087`, `n088`) | `invalid`, repair_needed | **`translated`, 0 errors** |
| `n015` | `invalid`, 6 errors | `abstained` (legal) |
| `n056`, `n058`, `n078`, `n084` | `invalid` | `invalid`, same error counts |

**A defect that a fresh draw of the same model on the same prompt does not commit is not a
defect the model cannot fix.** 14 of 19 are loop losses, not clause losses.

The 4 that fail twice split further:
* `n078`, `n084` — fail on the **same invented predicate names in both runs**
  (`tailored_for_under_18_conversation`, `hidden_chain_of_thought_message`, …). These are
  genuine M1 (`class_no-legal-bucket.md`): the span is about the document / a policy
  commitment, and the model reaches for the same illegal declaration every time.
* `n056`, `n058` — fail on **different names in each run** (`user_authority/1` vs
  `user_request/1`; `guideline_instruction` vs `implicitly_overridable_instruction`).
  Not one unfixable defect but a high per-draw defect rate: each fresh draw invents fresh
  undeclared names. A cap-and-redraw policy helps these only probabilistically.

### H-B: the model anchors on its own prior wrong answer — **the surviving explanation**

By elimination and by direct evidence: sampling is live cold (H-D), the message is
sufficient (H-A), the defect is repairable by the same model on a fresh draw (H-C). What
is left is the accumulating transcript. The mechanism is visible in the shape of the
failure: the model is not producing *worse* answers under repair pressure, it is producing
*the same* answer — the strongest continuation of a context in which it has already
committed to that answer once, and (by round 3) three times. `repair_loop`'s docstring
notes with satisfaction that "the transcript's PREFIX never changes, so every call after
the first is a cache hit." That property is exactly what makes the frozen state cheap to
re-enter and the loop cheap to waste money in.

The 9 lost chains whose first repeat is at **round 1** — the very first repair round — are
the clearest case: one prior wrong answer in context is already enough.

---

## 3. Q3 — the fresh-draw alternative, verified like-for-like

`class_repair-fixed-point.md` and `SUMMARY.md` §6.4 report "14 of 19 (or 18) unrepaired
clauses translated in 45 calls against 95". Verified, corrected in three places:

**What checks out.**
* All **19** (not 18) 08-14-unrepaired clauses were re-attempted in 08-15.
* `system_sha 5ff9daf7fe58845f`, `schema_sha 30ef9db24fb069a7`, `provenance_hash
  71e808c1fe729ae8`, provider, model, `max_tokens: 4096`, `format_forcing: json_schema`,
  `max_attempts: 5`, `temperature: 0.2`, `resample_truncation: 2`, corpus file
  (`node_corpus_all.json`, 773 rows selected in both): **identical**.
* Per-clause `user_sha`: **identical for all 19**; `prompt_user.txt` and
  `prompt_system.txt` byte-compared for a sample: identical.
* Calls: **95 → 0 modules** (08-14) vs **45 → 14 modules** (08-15).

**Correction 1 — the outcome breakdown.** 14 translated, **1 abstained** (`n015`),
4 unrepaired. The abstention is a legal outcome but it is not a module; the honest module
count is 14 of 19.

**Correction 2 — the "3 link-stage recoveries are corpus fill" caveat is wrong, and the
"11 of 16" number should not be quoted.** `class_repair-fixed-point.md` excludes `n043`,
`n047`, `n087` on the grounds that more modules existed by 08-15, so a bigger link scope
explains them. It does not: **`translate.py` line 1381 calls `repair_loop` without
`concepts=`**, so `concepts` is `None`, and `run_checks` documents that `None` means "the
module's OWN rows", not a corpus table. The in-loop checks never see `concepts.json`, and
the growth from 282 to 351 concepts cannot have loosened them. Confirmed empirically: all
14 recovered modules were re-validated **today**, offline, with `concepts=None` and the
identical 773-id `corpus_ids`, and **all 14 return `outcome=translated`, `repair_needed=False`,
0 errors** — while all 19 of the 08-14 finals return `invalid` under the same call.
**The recoveries passed the same gate the failures were judged by. The number to quote is
14 of 19, not 11 of 16.**

**Correction 3 — `config_sha` and `inputs_sha` do differ** between the runs
(`6617b34e`/`8c828597` vs `be66747e`/`c3dbccbf`), from the `only_stale` selection and the
concept table. Neither feeds the prompt (`user_sha` is unchanged) nor the in-loop checks
(`concepts=None`). Recorded so nobody re-derives the alarm.

### Honest expected value

Not "one fresh draw beats four repairs" — the 45 calls were *whole restarted 5-attempt
loops*, of which **9 of 19 succeeded on the very first call**. The right comparison is
between two loop *policies* on the same 19 clauses:

| policy | calls | modules |
|---|---|---|
| current: 5 accumulating attempts | **95** | **0** |
| stop at the first repeated reply, then restart the loop once from a clean transcript | **54 + 45 = 99** | **14** |

Roughly the same money, fourteen modules instead of zero. Projected over the whole 08-14
population of 100 clauses:

| policy | calls | modules of 100 |
|---|---|---|
| current | 230 | 69 |
| stop at first repeat, abandon | 185 (−20%) | 67 (loses `n016`, `n057`) |
| **stop at first repeat, restart once** | **~230** | **~81–83** |

The recomputed stop-point is not a guess: the 45 calls that a stop-at-first-repeat would
have avoided are *exactly* the 45 calls the fresh restart cost. The trade is call-for-call.

**The predictor and the saving replicate on 08-15 held out from the tuning:** 26 of its 157
calls sit after a first repeat, against 1 module (`l171_426_n005`) that recovered after one.

---

## 4. Q4 — the repair policy that follows (design only; not implemented)

### The policy

1. **Detect.** After every repair round, hash the assistant text and compare it against
   **every earlier assistant turn in this chain**, not only the previous one. Free, one
   `sha1` per turn, no model call. (Use repeat-of-any, not adjacent-identical: it catches
   `n058`/`n078` and costs nothing extra.)
2. **On the first repeat: discard the transcript and restart the clause from attempt 1**,
   once. Do not continue the accumulating chain. Re-base the attempt counter and the
   per-clause spend exactly as `dispatch_core.ClauseState` already does.
3. **Cap the total.** `max_attempts: 5` stays as the per-transcript cap; the restart gets
   its own budget of at most `max_attempts` and the restart flag is set once per clause,
   so worst case is 10 calls and a runaway is impossible.
4. **On a repeat inside the restarted chain: abandon and record.** Write the graveyard
   entry with a new flag, `frozen`/`refroze`, alongside the existing `shrank` and
   `declaration-edit` flags from `_diff_flags`. `graveyard.should_keep` already keeps
   every `unrepaired` clause, so no sampling change is needed — only the flag, so that
   "froze twice" is separable from "ran out of attempts" in later census work.
5. **Do not vary the prompt.** Explicitly rejected by name: paraphrasing the repair
   message, raising temperature on repair, or re-rendering the whole finding history into
   each turn. §2 shows the message is sufficient; the defect is the context it arrives in.
   Varying the prompt changes a measured artifact (`system_sha`) to fix an unmeasured one.
6. **Deduplicate the repair message.** Not the fix, but free and separately justified:
   `n062` was shown 9 lines carrying 3 distinct problems (the same name at four body
   sites), `n015` 7 lines carrying 3. `render_error_log` should collapse identical
   `(check_id, where, message)` triples with a count. This is a cosmetic-tier change and
   must **not** be bundled into the same commit as the loop change, or neither can be
   attributed.

### What it costs

Call-neutral at the run level (~230 → ~230 on the 08-14 population), or a 20% saving if
step 2 is dropped and stopped chains are simply abandoned. The implementation cost is one
hash set per `ClauseState` and one branch in `repair_loop`; `translate_exec.ClauseState`
gains a real `can_restart()` in place of its current hard `False`.

### What it risks

* **~9–12% of repeat-chains recover on their own** (3 of 32 pooled: `n016`, `n057`,
  `l171_426_n005`). Stop-and-abandon discards those. Stop-and-**restart** does not — it
  gives each of them a fresh 5-attempt loop, which on the measured population is a *better*
  bet than continuing. This is why the abandon variant is not recommended even though it is
  the cheapest line in the table.
* **A restart is not free of the failure it escapes.** 4 of the 19 refroze on the fresh
  draw. Expect a residual tail; that tail is M1 (`class_no-legal-bucket.md`) and is not a
  loop problem.
* **Reproducibility.** A restart adds a second sampled draw to a clause's history. The
  transcript must record both segments (a `restarted: true` marker between them), or the
  stored transcript stops being a record of the exchange — the exact failure
  `repair_loop`'s docstring warns about for synthesised first prompts.
* **The 08-15 evidence is a single run.** The 14-of-19 yield is one sample of a stochastic
  process; the *predictor* replicates across three runs, the *yield* does not yet.

### The pin that would prove it works — and the falsifier

**Pin (frozen input, no live count — `AGENTS.md`):** a unit test over a **frozen fixture
transcript** checked into `fixtures.py`, containing a synthetic 5-turn chain whose reply 3
equals reply 1. Assert: (a) the loop stops at reply 3 rather than reaching attempt 5;
(b) `can_restart()` is true exactly once; (c) the restarted segment begins from a
one-element transcript; (d) the outcome record carries the `frozen` flag. No count of any
live artifact appears in it.

**Falsifier, and it is cheap.** *A repeated reply predicts non-convergence.* The
measurement is over stored transcripts only: replay every chain in `runs/` and
`translation_sample/runs/`, hash all assistant turns, and report the translate rate
conditional on a repeat. Current whole-disk figure for the adjacent-freeze variant: **49
chains with a frozen round, 3 ended translated — 6.1%**; for repeat-of-any over the three
gen-11 runs: **3 of 32 — 9%**. **If a future corpus region puts that materially above ~20%,
the policy is discarding real convergences and this file is wrong.** The second falsifier
is the yield: if a repeated re-run of the 08-15 restart on the same 19 clauses yields
substantially fewer than 14 modules per ~45 calls, the expected-value table is an artifact
of one lucky sample.

---

## 5. Q4 (cont.) — should translation adopt the graph driver's remedy, and why did the
## original decision differ?

**The remedy already exists, twice, in this repository.**

`recurse_driver.Driver.call` (lines ~1460-1467):

```python
# byte-identical to the reply it was asked to correct: the
# transcript adds no information (ds5 2026-08-12, mirrored in
# dispatch_core.feed); fresh restart, once
if (env["text"] == transcript[-2]["content"] and not _restarted):
    print("    (repair reply byte-identical to the previous; "
          "restarting dispatch fresh)")
    return self.call(user, validate, schema, _restarted=True)
```

`dispatch_core.ClauseState.feed` mirrors it, resetting `transcript`, `repair_round`,
`errs` and `spent`, with `can_restart()` gating it to "laden repair transcript, once".
Its docstring states the theory outright: *"the transcript inflates the reasoning burn; a
fresh draw completes where the laden one cannot."*

`translate_exec.ClauseState.can_restart` returns a hard `False`, with the comment
*"translate.py has no fresh-restart path; a truncation failure goes to the clause body as
data instead."*

**Should translation adopt it? Yes — and the evidence is stronger than what justified it in
the graph driver.** The graph driver's restart was written from one incident (`ds5
2026-08-12`: `unwind c3_c1` repeated one 3,127-byte reply r1..r3). Translation now has 96
chains, three runs, a 98%-vs-9% outcome split, a refutation of provider determinism on 19
byte-identical prompt pairs, and a 14-of-19 measured recovery.

**Why the original decision differed — and it was not wrong on its own evidence.**
`translate_exec.can_restart` was written for **truncation**, not for freezing. In the graph
driver a truncation is a transport-level catastrophe that has to be handled inside the
dispatch layer; in `translate.py` the equivalent is already handled one level up and
differently, twice over: `_retrying` resamples a truncated **first** attempt
(`resample_truncation: 2`), and a repair-round failure is delivered *into the clause body as
data* so the per-clause handler can record it. Given only truncation to worry about,
"translation has no fresh-restart path" is a correct and deliberate design, not an
oversight. **The freezing case simply had not been measured when that line was written.**
`class_repair-fixed-point.md`'s open question — *"is there a principled reason the loop
resamples a truncated first attempt but not a stalled repair"* — now has an answer: **no.
The distinction is historical. Truncation was the only failure the restart path was ever
asked about.**

Two things translation should **not** copy from the graph driver:
* `dispatch_core` sets `self.spent = 0.0` on restart. Translation's cost gate is a run-level
  budget with a per-clause estimate; zeroing per-clause spend there would make the printed
  worst case a lie. Translation should re-base the *attempt counter* and leave spend
  cumulative.
* The graph driver keys on adjacent byte-identity only. Translation should key on
  repeat-of-any-earlier-reply: it is the same cost and it catches the two oscillating
  chains (`n058`, `n078`) that adjacent identity misses.

---

## 6. What this file adds, and what it does not claim

Adds:
1. The recover/freeze separator is **motion, not difficulty** — no round-1 feature of the
   defect predicts the outcome; 98% vs 9% on whether the model is still producing new
   answers.
2. **Repeat-of-any beats adjacent-identity** as the stop signal (19/19 vs 17/19), and the
   failure shape is a small-cycle attractor, not a single fixed point.
3. **Provider determinism is refuted** — 0 of 19 attempt-1 replies match across runs on
   byte-identical prompts, at `temperature: 0.2`.
4. **The repair message is sufficient** — four frozen transcripts were repaired in one turn
   each by a Haiku stand-in, validated through the real `checks.run_checks`.
5. **The 14-of-19 comparison is clean and the corpus-fill caveat was mistaken** — the
   in-loop checks run with `concepts=None`, and all 14 recoveries re-validate today under
   the failures' own gate. Quote 14 of 19; retire "11 of 16".
6. The restart remedy already exists in `recurse_driver`/`dispatch_core`; translation's
   refusal of it was scoped to truncation and does not survive this evidence.

Does not claim:
* That DeepSeek-V4-Flash would behave like Haiku. §2's experiment is about the loop.
* That the restart fixes M1. Four clauses refroze; that tail belongs to
  `class_no-legal-bucket.md`.
* Any pinnable count from `20260815-070038`. It is used as replication and as an
  expected-value estimate, per `TRANSLATION_REPAIR_CENSUS.md` §9.
