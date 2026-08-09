# Q-22 fix + worked-example fix — what actually happened

**Steps 1–4 of the critical-path plan. `[RAN]` throughout. Total spend $0.0318.**

⚠️ **THIS LANDED IN TWO PIECES, and the split is deliberate.** The pre-commit hook is scoped to
STAGED files, so the machinery below is committed. Two files are held back together —
`prompt/20_worked_example.md` (watched) and the three placement tests in
`test_prompt_examples.py`, **which fail against the old prompt and would make a clean checkout
red if they shipped without it.** They land when Matt reads the prompt diff and runs

```
python3 walkthrough/model/guard.py --accept paper_pipeline/phase_1/prompt/20_worked_example.md
```

⚠️ I did not run it. The guard's own text: *"Accepting a file you did not read is the failure this
guard exists to prevent, performed by hand."*

---

## 1 · Q-22 — the signature fix

`situation_signature` gained two terms: **unsatisfied `requires`**, and **linked modules' `inputs`**.
The second was the same defect one level down — `[RAN]` linking a provider in moved the required
predicate out of the signature (correctly, it is derived) while the provider's own inputs never
entered, so the defining rule could not fire and **linking made a module more inert, not less**.

⭐ **Not "add `requires` to the signature".** A *satisfied* `requires` is derived; putting a derived
predicate in the signature lets a situation assert it independently of the rule that produces it.
Pinned by `test_q22_control_a_requires_THE_LINK_DEFINES_stays_out`.

| clause · run | signature before | after |
|---|---|---|
| `m0255` 1339 | 5 | **8** |
| `m0079` 1719 | 1 | **3** |
| `m0079` 1748 | 1 | **5** |
| `m0105` 1748 | 1 | **5** |
| `m0134` 1748 | 5 | **6** |
| `m0150` 1748 | 1 | **2** |
| corpus total | 40 | **55** |

**The worst case, proven end to end.** `m0079` 1719 previously enumerated **2** situations over
`instruction/1` alone, so `not higher_authority_conflict(I)` was permanently true and the module
meant *"every instruction is applicable"*. Now: **8 situations**, `higher_authority_conflict(x)` and
`later_same_authority_conflict(x)` both derived in some of them, `applicable_instruction`
discriminating instead of constant, and a `requires-unsatisfied` note naming the unkept promises.

⚠️ **`note`, not `error`** — only `error` drives the stage-2 repair loop, and no rewrite of this
module can conjure the clause that was supposed to define the predicate (`DEBUGGING_TIPS` §7).

### The consequence, surfaced rather than suppressed

With borrows enumerated, `render_situation` refuses them for want of a gloss (Q-6), which **blocked
two shipped specs**. ⛔ The gloss fence is the anti-hollow-stub check and **was not relaxed**.
`probe_live` gained `UnglossedSignature` and `blocking_gaps` so a blocked module is a **named,
reported state**; two new tests prove every block is genuine (the predicate really is in `requires`,
really is unglossed) and that the error names the predicate. **No count is pinned** — Q-23 landing
will legitimately empty that set.

⇒ **Q-23 is no longer an optimisation. It is a prerequisite for stage 4 on any module with an
unsatisfied borrow.**

## 2 · The worked-example fix, and whether it worked

`m0088` demonstrated `"requires": []` with all six body predicates in `inputs`. Three are
document-side by the prompt's own rule 9. Moved to `requires`, and the *"all six appear in `inputs`"*
line replaced with a predicate-by-predicate table drawing the distinction.

**Re-translated twice** — the diagnosis set (`m0105`, `m0150`, `m0079`) and a **deterministically
drawn held-out set** never translated before (`m0092`, `m0177`, `m0158`), from borrow-heavy sections.

| | wholesale field flips | borrowed-NAME agreement | placement agreement |
|---|---|---|---|
| **before** (1719 vs 1748) | **2 of 2** clause-pairs | `[RAN]` **0.00** (0 of 22) | unmeasurable — no shared names |
| diagnosis set | **0** | 0.50 (8/16) | 0.75 (6/8) |
| ⭐ **held-out** | **0** | **0.69** (9/13) | **0.56** (5/9) |

⭐ **The severe failure is fixed, on held-out clauses.** The wholesale flip — one run putting
everything in `inputs`, the other everything in `requires`, giving an 8× difference in test-space
size — **did not recur once**.

⚠️ **The fine-grained placement decision is still unstable, and worse held-out (0.56) than on the
diagnosis set (0.75).** All four held-out flips are `m0092`'s coined *classification* predicates —
`imperative_argument/1`, `logical_argument/1`, `moral_argument/1`, `persona_confusion_attempt/1` —
where run A called all eight `requires` and run B split 4/4. *"Is this a logical argument?"* is a
fact about the case, so run B is the better answer and the residual error is the model reaching for
`requires` on coined categories. **The fix did not address that and does not claim to.**

⚠️ **Name agreement rising 0.00 → 0.50/0.69 was NOT predicted.** It is an observation at small n,
not a confirmed hypothesis, and it should be re-measured before anything is built on it.

⛔ **n is small and one clause was lost.** 2 held-out clause-pairs, 9 shared symbols; `m0177` failed
in run A and is excluded. A failure that shrinks the held-out set is exactly the kind of thing that
makes a small result look cleaner than it is.

## 3 · Corpus-wide state, and a number that will look like a regression

`probe_live.py --histogram`: signatures on the previously-orphaned modules moved from k=0–1 to
**k=2–8**.

⚠️ **Some modules now `failed` that previously `passed`** — `m0079` among them. **That is the fix
working.** They passed before because they had nothing to test; now they have testable content and
some of it does not hold. **Anyone reading only the pass count will read this as a regression.**

## 4 · Spend and suite

| | |
|---|---|
| translation, 4 live runs | **$0.0318** (ledger $2.057 of $8.50 before) |
| suite | **733 passed, 1 xfailed** |

⚠️ **My earlier "~$0.07" estimate was from recorded actual spend (~$0.005/module); the harness gate
quotes worst case at full `max_tokens`, which for 5 clauses is $0.14.** Both numbers are right about
different things and I quoted the friendlier one without saying which.
