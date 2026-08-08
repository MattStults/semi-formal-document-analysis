# Debugging tips — read this BEFORE proposing a prompt change

**Audience: any agent clearing a graveyard entry, or diagnosing why a translation failed.**
Read it first. Every entry below cost someone hours, and most of them cost the same hours twice.

> ## ⭐ THE STANDING RULE THAT MAINTAINS THIS FILE
>
> **Any time you work something out after struggling, add it here.** Not the conclusion alone —
> the *false path you took first*, because the next agent will take it too. A tip that only
> records the right answer saves nobody: the expensive part was ruling out the wrong one.
>
> If you churned on a prompt fix, that churn is the finding. Write it down before you write
> the fix.

---

## 1 ⭐ Before anything else: is the rule DEMONSTRATED, or only stated?

**Check whether a correct worked example exists for the exact shape that failed.** Not whether
the prompt *says* the rule. Whether it *shows* it.

**How this presented.** The dominant stage-2 failure was a whole rule written into `atom`, a
slot holding one term — 59 occurrences in 36 first attempts. The prompt already forbade it, in
prose, quoting the exact rejected form. A model asked why it did it quoted that prohibition
back and said *"The instructions were clear… I simply misapplied that guidance."*

⛔ **Everything about that says "model capability problem". It was not.** Counting every
`ontology` entry demonstrated anywhere in the four prompt files:

| ground facts (`body: null`) | 5 |
|---|---|
| **conditional (with a body)** | **1** — and it was in the format doc, not the worked example |

The worked example contained **no derived predicate at all**. Every failing clause needed one.

**What fixed it.** One worked example (clause `m0088`) showing a derived predicate and
alternatives-by-repeated-atom. Measured, arms A/B, first attempt only:

| | diagnosis set | held-out |
|---|---|---|
| rule-in-atom-slot | 18 → **0** | 10 → **0** |
| error findings | 22 → 3 | 35 → 13 |

⇒ **An example is an instruction with a picture attached, and it outranks the prose.** A model
shown four ground facts and told "conditionals are allowed" has been taught, in the more
credible channel, that `ontology` holds ground facts.

⭐ **AND CHECK WHETHER THE FAILURE IS CLAUSE-CONCENTRATED BEFORE THEORISING ABOUT THE PROMPT.**
The 59 came from **2 of 6 clauses**, which produced it on *every* attempt in *both* arms; the other
four produced it never. Both were `definitional`. A defect that tracks the clause TYPE rather than
appearing diffusely is telling you the prompt fails totally on a kind of input, not that the model
is sloppy — and that is a different fix. Aggregate rates hide this completely; group by clause first.

**The check to run:** extract every shape the prompt demonstrates and count them by category. If
the failing shape has zero good examples, stop — you have found it. `test_prompt_examples.py`
does this mechanically and the pre-commit hook runs it.

**⛔ The trap:** the fix that suggests itself is to state the prohibition more emphatically. If
the model can already quote the prohibition, more emphasis is not the fix and will cost you a
run to learn.

## 2 A metric can read 0.0000 when it measured NOTHING

`licence_modules_scored` came back at 1.33 of 6 clauses, so every licence rate was computed over
one or two modules and every one read `within noise`. That is **"not measured"**, and it is
indistinguishable from "no difference" unless the population size is reported next to the rate.

⇒ **Every rate needs its denominator printed beside it.** If you cannot see how many things a
metric was computed over, you cannot read the metric.

## 3 ⛔ Never measure a fix on the clauses that motivated it

The `read_back` fix went 6 → 0 on the eight clauses it was diagnosed from, and read as
eliminated. On six held-out clauses it recurred **18 times**.

⇒ Fitting shows up as *total success on the diagnosis set*. Draw a fresh set — the salted-rank
selectors in `eval_arms/*.provenance.json` do this deterministically — and report both, with the
diagnosis-set number labelled as fitting by construction.

**Exclude from any held-out draw:** every clause ever sent to the model, every previous eval
set, and **every clause id named in `prompt/*.md`** — those carry a worked answer. The last one
was missed on the first attempt and `m0204` was drawn while sitting in the prompt as an example.

## 4 ⛔ Pooling across attempts fabricates patterns that are not in any attempt

Pooled over 36 attempts, 90% of distinct rules-in-atom-slots belonged to a repeated head — which
read as strong evidence that the model was reaching for alternative sufficient conditions.

**Within single attempts it collapsed:** only 4 of 12 affected attempts repeated a head, and all
four were one clause. The other clause wrote four rules with four *different* heads.

⇒ A hypothesis about what a model was *trying to do* must be checked **inside one attempt**. A
count pooled across repeats measures the clause set, not the reasoning. This nearly shipped as
the diagnosis.

## 5 Cluster failure messages by NORMALISED text, never by `check_id`

Every schema failure carries `check_id == "schema-breach"`, so a ranking keyed on the id has one
bucket holding every distinct defect.

⚠️ **And normalising backticks is not enough.** `schema.py` interpolates with `{term!r}` —
**single quotes**. A backtick-only normaliser left the dominant cause fragmented
one-cluster-per-clause, invisible in a rank, and produced a report saying the prompt fixes had
changed nothing. Erase backticks, both quote styles, digit runs, and absolute paths (`clingo`
embeds a fresh tempdir every run). `eval.normalise_message` is the reference.

## 6 The model's account of its own failure is a PROPOSER, never a diagnosis

Two recorded cases of a false self-report: one annotated *"the anonymous variable is avoided by
using a named variable"* while writing one; another stated a rule that could not have produced
its own examples.

⚠️ But do not discard it either. In §1 the self-report was **right about the wrong thing** — the
model correctly said the instructions were clear, which is what ruled out the emphasis fix and
pointed at the demonstration gap. Treat it as evidence about what the model *saw*, not about
what caused the failure.

**Running it:** continue the existing transcript with `format_forcing: "none"` and **keep the
stage-1 system block**. It is a request-body flag, not a property of the transcript — the first
attempt left forcing on and got eight JSON modules back instead of eight diagnoses. Keeping the
system block is necessary, not incidental: the question asks which instruction misled the model.

## 7 Notes are not failures, and a repair loop that chases them will not converge

`requires-unprovided` fires on **every well-formed single-clause module** — a `%% requires:`
predicate is head-less by design. One clause was handed eight of them under *"Fix every one of
them"* and never converged.

⇒ Only `error` severity drives repair. When reading a graveyard entry, filter to errors before
counting anything, or the ranking is dominated by findings that are true of correct modules.

## 8 A check that cannot run must not exit like a check that passed

The staleness guard was red for two hours and nobody looked, because the hook had never been
installed. A test written to catch tests leaking into the production graveyard **passed
vacuously** because pytest runs files alphabetically and it ran first.

⇒ Verify RED before you trust GREEN: break the thing on purpose and confirm the check fails. A
missing venv, a regex that matches nothing, an empty artifact — all must **block**, never skip.

## 9 Do not pin an exact value of a live artifact in a test

Fixtures and assertions that hard-code prompt text break when someone legitimately edits the
prompt, and report an ordinary edit as a defect.

- A test asserted a named sentence appeared in `00_task.md` exactly once. The sentence was
  deliberately deleted; the test failed and blamed the edit.
- An eval fixture built arm B by *deleting that same sentence*. Once it was gone the edit became
  a no-op, both arms went byte-identical, and three tests failed. The harness's own
  identical-arms guard was right; the fixture was wrong.

⇒ Pin **behaviour**, not content. Make fixture edits content-independent (append a sentinel).
This has now bitten three times and is in the repo brief.

## 10 Prompt files are watched transcriptions

Editing one without review is the failure that has cost the most here. `walkthrough/model/guard.py`
blocks a commit touching a watched file that is not at its review point, and the pre-commit hook
also runs `test_prompt_examples.py` so an example our own checks reject cannot be committed.

⇒ A graveyard fix that edits a prompt is not done when it works. It is done when it has a
held-out measurement, a pre-registered prediction, and a review.
