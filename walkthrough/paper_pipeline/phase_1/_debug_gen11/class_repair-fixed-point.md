# X — the repair fixed point: 40% of repair rounds bought byte-identical bytes

**Mechanism, one sentence.** When the model has no move it believes in, it re-emits the
**byte-identical module** in response to the repair prompt, and the loop pays for it up to
four more times.

**This is not a defect class — it is a multiplier on every other class in this
post-mortem, and it is the single largest recoverable cost in the run.**

---

> ⚠️ **Standing caveat on the 08-15 comparison.** `20260815-070038-together-deepseek-v4-flash`
> was **still in flight** while this analysis was written (its `run.json`, `health.jsonl`
> and `inflight/` are live, and graveyard entries were still appearing). Its outcomes are a
> **snapshot**, they will change, and **no count from it may be pinned into a test** — per
> `TRANSLATION_REPAIR_CENSUS.md` §9 and `AGENTS.md`. Nothing under `runs/` or
> `repair_graveyard/` was written to by this analysis. Its 08-14 numbers, by contrast, are
> from two completed runs and are stable.

## The measurement

Every assistant turn in both runs was hashed and compared with its predecessor.

| | |
|---|---|
| repair rounds | 130 |
| of which returned a module **byte-identical to the previous attempt** | **52 (40%)** |
| spend on those rounds (matched to `usage.jsonl`) | **$0.1026 of $0.2415 repair spend — 42%** |
| repair rounds on **unrepaired** clauses that were frozen | **50 of 76 (66%)** |
| repair rounds on **translated** clauses that were frozen | 2 of 53 (4%) |
| clauses with at least one frozen round | 18 |
| clauses where **every** attempt was byte-identical | 4 |

The four fully-frozen chains — `l1_170_n014`, `l1_170_n047`, `l1_170_n062`,
`l1_170_n084` — each paid five calls to receive the same JSON five times.

**The signal separates the two outcomes almost perfectly.** A frozen round predicts
"this chain will not converge": 96% of frozen rounds sit on chains that ended
`unrepaired`. It is computable for free at the moment the response arrives — one hash
comparison — and nothing in the pipeline looks at it.

---

## Verbatim: what the loop was paying for

`l1_170_n062`, attempts 1-5, verbatim repair message (identical each time):

```
attempt N failed these checks:
  - [schema-breach] <root>: body references `default_instruction` but nothing declares it. …
  - [schema-breach] <root>: body references `overridable_guideline` but nothing declares it. …
  - [schema-breach] <root>: body references `default_instruction` but nothing declares it. …
  - [schema-breach] <root>: body references `overridable_guideline` but nothing declares it. …
  - [schema-breach] <root>: body references `default_instruction` but nothing declares it. …
  - [schema-breach] <root>: body references `overridable_guideline` but nothing declares it. …
  - [schema-breach] <root>: body references `default_instruction` but nothing declares it. …
  - [schema-breach] <root>: body references `overridable_guideline` but nothing declares it. …
  - [schema-breach] <root>: body references `derived_on_the_fly` but nothing declares it. …
Fix every one of them. Return the corrected module, complete.
```

Note the duplication: the same two names are reported four times each because they appear
at four body sites. Nine lines, two distinct problems. `l1_170_n015` reports
`rest_of_document_section` four times and `document_order` twice, every round, for five
rounds.

`l1_170_n052`, all five attempts, module unchanged down to the field:

```
inputs:   ['overridden_by_root_or_system/1']
requires: ['developer_authority/1', 'authority_levels_hierarchy/2']
ontology: []
```

## The counterfactual, measured

Run `20260815-070038` re-attempted 18 of the 19 unrepaired clauses under **byte-identical
prompts** (same `user_sha` per clause, same `system_sha 5ff9daf7fe58845f`, same
`schema_sha`, same `max_tokens: 4096 / max_attempts: 5`).

| | 08-14 repair loop | 08-15 fresh sample |
|---|---|---|
| calls spent on those 19 clauses | **95** | **45** |
| modules produced | **0** | **14** |

A fresh first attempt costs the same as a repair round and, on this evidence, is
dramatically more likely to succeed than the fourth repair of a frozen chain. **Half the
run's repair budget was spent asking a model that had already stopped moving to move.**

---

## FALSIFIER

*Byte-identity predicts non-convergence.* Wrong if a meaningful number of chains recover
**after** a frozen round. On this run 2 of 53 translated-chain repair rounds were frozen —
so recovery after freezing happens, but rarely. The stronger and cheaper test is over the
whole disk: replay every stored transcript in `runs/` and
`resolve_runs/graph_v2/translation_sample/runs/`, hash consecutive assistant turns, and
report the recovery rate conditional on a frozen round. If it is materially above ~5%, an
early stop on byte-identity would be discarding real convergences and this file's
framing is wrong.

*The 08-15 comparison is clean.* Wrong if anything differed between the runs. Checked:
`system_sha`, `schema_sha`, `provenance_params` and the per-clause `user_sha` are all
identical. What is **not** identical is the link scope — more modules existed by 08-15 —
so the three link-stage recoveries (`n043`, `n047`, `n087`) are explained by corpus fill,
not by resampling. Excluding those, the comparison is **11 of 16 schema-stage clauses
recovered on a fresh sample**. That is the number to quote.

---

## Candidate solutions already on record

* **No candidate on record targets this.** Fixes A-F are all about making individual
  defects unrepresentable; none of them changes the loop. `TRANSLATION_REPAIR_CENSUS.md`
  §6.2 measures the loop's *other* pathology (defect trading) and §6.3 notes that *"22
  clauses burned the full five attempts… 36% of all repair spend sits in 12% of clauses"*
  — the same tail, seen from the outside — but proposes nothing for it.
* The review confirmed defect trading at **57% of post-first rounds (71/124)**, with a
  masking test showing **97 genuinely new vs 5 latent**. This file is the complementary
  half: the rounds that are *not* trading defects are largely doing nothing at all.
  Together they account for the loop's behaviour: a post-first round either introduces a
  new class or repeats the old bytes.

---

## Graph-stage or translation-stage?

**Neither — this is loop-design, and it is the cheapest thing in this post-mortem to act
on.** It needs no schema change, no prompt change, no `contract_hash` bump, no migration,
and no model call to validate. It is orthogonal to every other class, so it can land
alongside any of them.

Stated as a caution rather than a fix (this is the analysis pass): whatever phase B does
about M1 and M2, **the 42% of repair spend that this file identifies is recoverable
independently of all of it**, and the 08-15 run has already demonstrated, with real money
already spent, that the alternative works.

---

## Open question for the fix pass

`translate.py` wraps the first attempt in `_retrying` for truncation (`resample_truncation:
2`) but not the repair rounds. **Is there a principled reason the loop resamples a
truncated first attempt but not a stalled repair** — and does the graveyard's `shrank`
guard have anything to say about a module that is byte-identical rather than smaller?
Both mechanisms already exist; neither is pointed at this.
