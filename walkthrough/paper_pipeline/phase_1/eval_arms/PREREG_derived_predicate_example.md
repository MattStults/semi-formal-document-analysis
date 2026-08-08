# Pre-registration — adding a derived-predicate worked example

**Written before any call. Frozen 2026-08-07.**

---

## The change

`prompt/20_worked_example.md` gains one section: clause `m0088`, a definitional clause whose
term has no fixed extension and is defined by **three alternative conditions**, one of them
conjunctive. It demonstrates, for the first time anywhere in the prompt:

- an `ontology` entry with a **body** (a derived predicate), and
- **alternatives written by repeating the atom** — three entries, same `atom`, different bodies.

It also corrects *"A definitional clause is the easy end of this task"*, which is false: 57 of
59 atom-slot failures are on definitional clauses.

**Why this and not more emphasis.** Across all four prompt files the `ontology` block was
demonstrated by **5 ground facts and 1 conditional entry**, and the worked example contained
no derived predicate at all. The prohibition was already stated in prose, in the exact rejected
form, and m0105 quoted it back while violating it. The gap is in what is *shown*.

⭐ **The example is validated by stage 2 itself**, not by reading — `test_prompt_examples.py`
extracts every good module from the prompt and runs `checks.run_checks` on it. m0088 returns
`translated`, 0 errors. The pre-commit hook runs those tests whenever a watched prompt file is
staged, so an example that our own checks reject can no longer be committed.

## The arms

| | |
|---|---|
| **A (control)** | `20_worked_example.md` as of commit `e7c1a17`, restored from git, never hand-copied |
| **B (live)** | the same file plus the m0088 section |

Everything else is identical, **including the uncommitted edit to `00_task.md`** that removed
the licence-emphasis sentence — it is present in both arms, so it cannot contribute to the
delta. System blocks: **27,976 (A) vs 32,616 (B)**.

## The prediction ⭐ FROZEN

**The atom-slot cluster falls on the clauses that produce it now.** That is the weak test: it is
measured on the clauses that motivated the change.

**The atom-slot cluster also falls on clauses never used for diagnosis.** That is the real test.

⛔ **The falsifier:** if the held-out atom-slot count does not fall, the missing demonstration
was not the cause, and this section is 4,640 characters of prompt for nothing — it should be
reverted, not kept because it reads well.

**A secondary prediction I expect to fail:** `first_attempt_clean_rate` will *not* move much,
because m0293 and m0055 each carry other errors too, and fixing one cause on a clause with
three still leaves it invalid.

## Two clause sets, and why both

⚠️ **Set 1 — the diagnosis set: m0055, m0293.** These produced 57 of the 59. Measuring here is
**fitting by construction** and proves only that the change addresses the case it was drawn
from. Reported as such, never as validation.

⭐ **Set 2 — a fresh held-out draw.** Four clauses, never sent to the model, drawn by the same
deterministic salted rank with a **new salt** (`eval-heldout-v2`), stratified toward
`definitional` because that is where the defect lives. This is the one that decides it.

## What this cannot settle

1. n is small: 2 + 4 clauses, 3 repeats, 2 arms.
2. Arm B's system block is **16% longer**. A change in behaviour could in principle come from
   length or position rather than content. Nothing here separates those.
3. One model, temperature 0.2. Nothing generalises past `DeepSeek-V4-Flash-0731`.
4. Stage 2 cannot say the translation is *right* — only that it satisfies the contract.

## Cost

(2 + 4) clauses × 3 repeats × 2 arms = **36 calls**, first attempt only. Gated at the config's
$0.25 ceiling. Directory spend to date ~$0.19 of the $8.50 project cap.
