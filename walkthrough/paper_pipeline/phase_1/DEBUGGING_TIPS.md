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

⛔ **A live instance, found 2026-08-07 and now fixed: the run summary counted `abstained_under_repair`
as TRANSLATED.** `run()` computed `n_ab` by matching `status == "abstained"` **exactly**, then printed
`len(results) - failures - n_ab` as the translated count. `abstained_under_repair` matches neither the
abstained test nor the failure branch — it is admitted on the success branch — so it landed in
"translated". A clause the model declined after two failed attempts was reported as a success, in the
one line a human reads.

⇒ **When a status set grows, every place that partitions on it has to grow with it.** The record was
fixed months before the arithmetic was: `run.json` carries the distinction and `test_repair.py
::test_abstained_UNDER_REPAIR_survives_into_the_record` pins it — but that test reads the **stored
field**, and the defect was in a number **derived** from it one line below. `README.md`'s status list
was missing the value too, which is how it stayed invisible.

⭐ **The generalisable form: a fix and its test must meet at the number a human actually reads.**
Grep every consumer of a status before adding one, pin the **derived counts** and not just the stored
field, and make the residual loud — `run()` now counts `translated` by name and prints a warning
naming any status its partition does not cover, so the next status added cannot be silently absorbed
into the most flattering bucket. Pinned by `test_cost_and_summary.py
::test_the_PRINTED_SUMMARY_does_not_count_an_abstention_as_a_translation`, which asserts on the
printed line via `capsys`.

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

⚠️ **`per_attempt` in `run.json` is not an error count.** `repair_loop` records `len(found)` over the
**complete** findings list, notes included (`translate.py`, `per_attempt.append(len(found))` at the
top of the attempt loop). A clause whose only surviving findings are `requires-unprovided` notes —
true of every correct single-clause module — reads as `per_attempt: [1, 1]`, **byte-identical** to a
clause with one real error on both attempts, which is what `m0091` was. Any convergence rate computed
off this field is measuring note volume. Filter by severity before counting, or read
`surviving_findings`, which is only written on the failure path. The rule above tells a *reader* to
filter; the recorded field itself still mixes the two, and `per_attempt` is what a convergence
measurement would group on.

## 8 A check that cannot run must not exit like a check that passed

The staleness guard was red for two hours and nobody looked, because the hook had never been
installed. A test written to catch tests leaking into the production graveyard **passed
vacuously** because pytest runs files alphabetically and it ran first.

⇒ Verify RED before you trust GREEN: break the thing on purpose and confirm the check fails. A
missing venv, a regex that matches nothing, an empty artifact — all must **block**, never skip.

⛔ **A live instance of exactly this, found 2026-08-07 inside the function written to prevent it.**
`link._check_clingo`'s guard is `if errs or r.returncode not in CLINGO_OK_RC:` — two **deliberately
redundant** detectors, and only the first was tested. Mutating the line to `if errs:` **survived all
352 tests and `link.py --self-test` 19/19**. The redundancy is not decorative: with `clingo` missing
from the interpreter the output is *"No module named clingo"*, `CLINGO_ERR` matches **zero** of it,
and the finding is raised by the return code **alone**. Under the mutant, a link check over a program
that was never compiled reports **clean** — the "pass indistinguishable from did-not-run" shape this
project names as its recurring failure, sitting unpinned inside its own guard.

⇒ **When a guard is deliberately redundant, each arm needs its own RED test.** A test that only
exercises the arm that fires most often converts the redundancy into decoration — and the arm left
behind is the one covering the **environment** failure, which is precisely the one you cannot reach
by writing a bad program. Both arms are now pinned (`test_link.py
::test_d4_clingo_that_NEVER_RAN_is_a_failure_even_with_no_error_text`, with
`::test_d4_every_documented_clingo_exit_code_stays_silent` as the `if True:` guard).

⚠️ **And do not write that test as "run a python that happens to lack clingo".** That makes the test
a claim about the machine it runs on: install clingo system-wide and it silently stops testing
anything — this same failure mode, one level up. Script the two observables the check reads (a fake
interpreter that ignores its arguments, prints what you choose and exits the code you choose), and
**assert the premise inside the test**: `CLINGO_ERR.findall(blob) == []`, so the day the regex grows
to match the missing-module message the test says so instead of quietly passing on the other arm.

### 8a ⭐ SWEEP FOR THE SHAPE, DO NOT FIX THE INSTANCE — and the shape has a grep

**2026-08-07.** §8's instance was found again the same day in `test_schema.py`, in the commit
that fixed it in `link.py`. Fixing the named test would have been the wrong-sized repair. The
**generalised shape** is:

> anything that shells out and decides pass/fail **purely from stdout matching**.

⚠️ **The false path I took first: grepping for `clingo`.** That finds the instances someone
already thought about. The shape is not about clingo — it is about `subprocess.run` whose result
is read only through its text. `grep -rn subprocess --include=*.py` over the tree, then look at
each site and ask **"what does this assert if stdout is empty?"** A negative assertion
(`assert not errs`, `assert not leaked`, `expect: {"absent": [...]}`) is satisfied by a dead
process; a positive one (`assert "concept table" in first`) is not. **Sort the sites by that
question, not by which tool they call.**

⛔ **What the sweep found that two adversarial reviews did not.** `paper_pipeline/cq_check.py` —
stage 0's competency-question runner, and the *only* mechanical check on the design's written-first
answers. Both its runners parse stdout and read no return code, so with a clingo-less interpreter
**CQ-4.a, CQ-5.a, CQ-5.b and CQ-6.c all reported `pass`** with nothing executed. Their
expectations are written as **absences** (`absent`, `unresolved: []`), and an absence is exactly
what a dead process produces. Two reviews read this tree that day and neither looked outside
`phase_1/`.

⚠️ **And the return code is not always enough.** `link.py` exits **1** for both *"found
error-severity findings"* (a real outcome) and *"the interpreter died"*. CQ-6.c survived the
return-code arm alone for that reason. The second observable is that `link.py` **always prints**:
a silent stdout is a dead process. ⇒ **When a tool's exit codes are ambiguous, find a second
observable rather than widening the accept set.**

Also swept and found SOUND, recorded so the coverage is auditable: `mutate_schema.py` (checks the
baseline return code *and* that each mutant collected the same number of tests — a mutant whose
suite did not run comparably is reported `error`, never `survivor`); `model/test_model.py`'s hook
tests (assert on return codes); `test_link.py`'s CLI tests except the live-run acceptance case,
which had the shape and now asserts `returncode == 0` first.

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

## 11 ⛔ A metric that reads only VALID modules cannot measure a habit that co-occurs with invalidity

`empty_gloss_rate` reads `outcome.module`, which is `None` whenever the response failed a schema
check — 44% of first attempts in the run in question. An A/B of bad worked example #6 was written
up as invalid because the control arm scored **0.000 on all three repeats**, read as *"the eval set
does not exhibit the failure at all"*, and the recorded next step was to go draw a different clause
set.

**Re-counting that same arm's raw responses, already on disk, cost nothing and said otherwise:**

| arm A | empty glosses | concepts | rate |
|---|---|---|---|
| as the metric measured it | 0 | 42 | 0.000 |
| off the raws in `*_raw/A/r*/` | **8** | 84 | **0.095** |

All eight sat inside modules that failed the schema. The zero was **censoring, not absence** — and
the censoring was not neutral between arms, because they differed in `unbuildable_rate` (0.444 vs
0.333) as well as in glosses. The metric compared two differently-sized populations and reported
the difference as an effect.

⇒ **When a metric conditions on a validity check, ask whether the condition is independent of the
thing being measured.** A sloppy module is more likely to be *both* schema-breaching and
content-free, so it is exactly the wrong thing to drop. `eval.glosses_raw` is the reference: the
same count off `outcome.raw`, conditioned on nothing but "it parsed", with `raw_responses_parsed`
printed beside it.

**⛔ The trap, and it is a specific one:** the wrong diagnosis was *"draw a better eval set"*, which
sounds like rigour and would have spent another $0.05 to reproduce the same blindness on new
clauses. The eval set was fine. **Before concluding an eval set has zero incidence, count the
incidence in the raws yourself** — the raws exist for this, and it is free.

## 12 A selection rule for an eval set is a hypothesis, and it can be wrong

Choosing clauses "that plausibly introduce named categories" is the right instinct, but the first
mechanical rule for it — an enumeration marker word (`such as`, `e.g.`, `including`) — scored
**4.9%** empty glosses on rule-positive clauses against **6.4%** on rule-negative. It selected
nothing; the marker word is everywhere and the two worst offenders enumerate without one.

⇒ **Score a proposed selection rule against the responses already on disk before you spend on it.**
Six candidates took ten minutes and no money, and the kept rule (a run of ≥3 short comma-separated
items, or a bolded term) separates 9.7% from 3.0%. The one that scored *highest* was not kept —
it rested on four clauses, and a rule whose expected incidence comes from one or two clauses will
hand you an eval set that either exhibits the failure enormously or not at all.

⚠️ And say in the pre-registration that the rule was **fitted to prior data**, list the candidates
that lost, and exclude every clause used to derive it from the draw. A selection rule predicts
*where* a failure occurs, not *what fixes it*, so it cannot manufacture a difference between arms
— but it can make the eval set atypical, and that is a real limitation to write down rather than a
loophole.

## 13 ⛔ `acts` is not in the body-declaration set, and the message it produces is wrong

**Still live, reproduced 2026-08-07.** `schema.py`'s D4b-level-1 check builds `known` from
`ontology ∪ requires ∪ inputs`. `acts` is **not** in it. So a module that declares
`be_explicit_about_inability(I)` in `acts` — correctly — and then references it in a rule body is
told:

```
body references `be_explicit_about_inability` but nothing declares it. Put it in this module's
`ontology`, in `requires` (another clause defines it), or in `inputs` (a fact about the case).
An undeclared name cannot be told apart from a typo
```

All three remedies are **wrong for an act**, and following any of them corrupts the module.

**The cost is not a bad message, it is non-convergence.** The finding is `error` severity, so it
drives repair; the model can only clear it by doing something wrong; the loop exhausts. `m0091` was
the one `unrepaired` clause of the first live run for exactly this reason, and it burned a paid
attempt to learn nothing.

⛔ **The trap:** the neighbouring block was tightened **deliberately** — `concepts` was REMOVED from
`known` because a rule resting only on concept declarations can never fire, and `fixtures.py:14-19`
records a wrong test fixture (`political()`) corrected in that same change. Do not undo that while
fixing this. **The distinction to preserve: an act is a declaration site because the module governs
it and owes a closure over it; a concept is not, because saying what a name means never says that
anything derives it.**

⚠️ Getting to the reproduction takes four rounds with the validator, and every intermediate failure
is a *different, correct* error — act-entry-is-not-a-term, act-not-declared, closure-not-declared,
closure-field-name. Do not read those as "the schema already catches it". The reproduction is: both
acts declared, a closure row for each, and the act referenced in another assertion's `body`.

## 14 ⛔ The cost estimate was on the wrong side of its own stated rule

**Found and fixed 2026-08-07.** `estimate_cost` grew the *input* term triangularly in
`max_attempts` — but only over `len(system) + len(user)`. Each repair turn also resends **every prior
completion**, worth up to `max_tokens` (16,384 — about 12× the user block), and that term was
**absent**. At the shipped `max_attempts: 3` the printed worst case was **12.7 % below** the true
worst case; at 5, **21.4 %** below.

| `max_attempts` | printed "cost (worst)" | true worst case | under by |
|---|---|---|---|
| 2 | $0.013265 | $0.014196 | 7.0 % |
| **3 (shipped)** | **$0.021943** | **$0.024734** | **12.7 %** |
| 4 | $0.031984 | $0.037566 | 17.5 % |
| 5 | $0.043389 | $0.052692 | 21.4 % |

⛔ **The trap is that two documents told you this could not happen.** `config.json`'s comment says
*"Overstating an estimate is survivable; understating is how a hard cap gets passed"*, and
`README.md` explained the triangular growth as *"because each repair turn resends the transcript"* —
**which is the exact term that was missing**. The estimate was described by its own rationale as
conservative while being anti-conservative, on the project with a hard $8.50 ledger. A reader
checking the estimate against the README was told the error could not exist.

⚠️ **Two errors point in opposite directions and partly mask each other.** The estimate
**over**-charges the full user block on every repair turn, while the loop actually re-sends only an
error log. **Do not net them off.** The over-charge is deliberately kept; high is survivable, low is
not.

**The check to run:** price a repair sequence **by hand, attempt by attempt** — attempt 1 is
`system + user`; attempt *k* is `system + user + (k−1) × max_tokens` of prior completions — and diff
it against the printed number. Write it out as a loop, not as a closed form: re-deriving the same
algebra the code uses lets one slip pass both.

⛔ **A test asserting `three > one * 2.5` cannot see this**, and one existed. With `max_tokens=1000`
and the strings `"sys"` / `"user"`, the **output** term alone gives exactly 3×, so the assertion
passes with the input term contributing nothing measurable. ⇒ **A cost test written on toy strings
measures the output term and nothing else.** Use realistic sizes (the real 33,614-char system block
and a real user block), and add an isolation test: hold everything fixed, raise **only**
`max_tokens`, and require the **input** token count to move. `test_cost_and_summary.py` does both,
with `::test_one_attempt_bills_no_carried_completion` as the guard that stops "just inflate the
estimate" from passing.

## 15 ⛔ A MUTATION SWEEP is a check, and it can pass without running either

**Found 2026-08-08 by adversarial review, and it is §8 applied to the instrument
that certifies §8's fixes.** `mutate_seats.py` reported **`83 mutants applied, 0
survivor(s)`, exit 0, against a suite with an always-failing test appended.** The whole kill
rule was:

```python
killed = r.returncode != 0
```

⇒ **a red suite kills every mutant, so every guard reads as pinned.** Two more of the same
shape sat behind it: a mutant that broke the import gave pytest **`rc=2`** — a *collection
error*, i.e. the suite did not run — and was reported KILLED; and nothing recorded *which*
test died, so a mutant killed by an unrelated flake was indistinguishable from one killed by
its named guard.

⛔ **The trap is that the documented trap was fixed.** The file carried a careful, correct
note about `.pyc` invalidation `(mtime seconds, size)` making a second mutant silently not
take effect — a real instance of "a pass indistinguishable from did-not-run", found inside
the tool built to detect it, and genuinely closed with `rmtree(__pycache__)` +
`PYTHONDONTWRITEBYTECODE=1`. **Fixing the instance is what §8a warns about.** The general
shape — *this tool decides pass/fail from one weak signal* — was left standing one line below
the note about it.

⇒ **A mutation harness needs four things, and `mutate_schema.py` had all four in the same
directory the whole time:**

1. a **green baseline through the SAME isolation path**, before any mutation;
2. **return-code triage** — `rc in (2,3,4,5)` is *the suite did not run*, never a kill;
3. a **collected-count comparison** against the baseline — a mutant whose run collected a
   different number of tests proves nothing;
4. an **`error` status at all**. Without a third status every failure folds into `killed`,
   which is the flattering direction.

⚠️ **And "killed" must mean A NAMED TEST DIED**, read off pytest's `-rfE` summary — not "the
process exited non-zero". That is also what makes the entanglement table possible, which is
how you see a test that dies under many unrelated mutants and is therefore failing for a
reason other than the one it names.

### 15a ⚠️ The mirror's LOCATION is load-bearing, and I got this wrong first

The obvious rewrite is *"stop editing the source in place; copy the tree to `/tmp` and mutate
the copy"*. `[RAN]` that makes **every** mutant die, for a reason that has nothing to do with
its guard:

```
FileNotFoundError: …/scratchpad/repro/semi-formal-experiment/modelspec_clauses.json
```

`seats.py` computes `WALKTHROUGH = dirname(dirname(HERE))` and `link.py` resolves the clause
corpus relative to the repo root **above that**, so a mirror under `/tmp` breaks `survey()`
and the sweep reports a clean 100 % kill built entirely out of import errors — *the same
defect it was rewritten to fix, wearing the opposite sign*. The mirror is therefore created
**inside `paper_pipeline/`**, dot-prefixed so pytest never collects it, and removed in a
`finally`. Directories are symlinked (`runs/`, `probe_runs/` are the bulk); files are copied,
so pytest's import machinery never has to resolve a symlink to decide a module's identity.

⇒ **When you isolate a tree, check what the code under test computes from `__file__`.** The
baseline guard (1) is what catches this — it fires before a single mutant runs — which is the
second reason to have it.

### 15b `21/21 killed` with no committed harness is a claim, not a measurement

`readback_r3.py` shipped with *"mutation sweep 21/21 killed, 0 survivors"* in a commit message
and **no mutation harness in the repo**. Nobody but the author could re-run it, and CI never
could. `mutate_readback_r3.py` now exists and runs on the same engine — 33 mutants, 0
survivors. ⇒ **A number that cannot be re-run does not meet a bar; it describes one.**

## 16 ⛔ A restriction justified by a TOOL is a bug report about the tool, not a rule about the input

**2026-08-08. The false path was mine and I took it twice in one day, in the same function.**

### The rule

Before adding a guard to `schema.py`, ask what its ground is. Three grounds are legitimate:

| ground | example | what to do |
|---|---|---|
| the **SOLVER** | `p(_) :- q(X).` — clingo: *unsafe variables in `p(#Anon0)`* | reject |
| the **CONTRACT** | `act` holds one term, and a rule is not a term | reject |
| the **LEAK FENCE** | `b_asserts` may not appear in a clause translation | reject |

A fourth is not: **"a tool of ours cannot cope"**. That is a bug report about the tool, and it must
first be tested for a **meaning-preserving transform** applied on the way to the tool.

⭐ **THE SAFETY CRITERION, and it is the only one that licenses any transform:**

> **A transform is safe iff it preserves the ANSWER SETS of the program that actually runs.**

Not "it looks equivalent", not "the renderer copes" — run both programs and compare the witness
sets. `test_readback_r3.py::test_the_transform_PRESERVES_THE_ANSWER_SETS` is the reference: it
compares `clingo --outf=2` witnesses, and asserts `Result == SATISFIABLE` first, because two
programs that both failed to ground compare **equal** and would pass having proved nothing.

### Worked case that QUALIFIES — `_` in a rule body

`_check_body` rejected an anonymous variable. The stated ground was true and was `[RAN]`: xclingo
2.0b24 dies on `p(X) :- q(X,_).` with `unsafe variables in: _xclingo_sup(...#Anon0)`, exits 0, and
takes the **whole link set's** explanation down.

⛔ **What nobody tried was renaming it.** An anonymous variable in a positive literal *is* a fresh
variable used once, so the substitution is alpha-renaming:

```
p(X) :- q(X,_).      -> p(a), p(b)
p(X) :- q(X,_V1).    -> p(a), p(b)      identical, and it RENDERS: |__"p holds of a"
```

The guard is gone; `readback_r3.deanonymise` does the substitution on the text handed to xclingo,
and the module and its `.lp` keep the author's `_`. **The cost of the guard had been paid for a
year in expressiveness the design explicitly wants**, to work around one tool's grounding order.

⚠️ **Two things the transform is NOT, both found by running it and neither predicted:**

* **A `not` literal must be left alone.** gringo does not rename `_` there, it **projects** the
  literal — so `not r(X,_)` solves and `not r(X,_V2)` is **unsafe**. Renaming would turn a working
  program into a refused one, which is the opposite of meaning-preserving. ⇒ *"An anonymous
  variable is a fresh variable used once"* is true of positive literals and **false under `not`**.
* **And that case never needed a guard at all.** `[RAN]` xclingo renders `not r(X,_)` unaided,
  because it only lifts POSITIVE body literals into `_xclingo_sup`. **The restriction had been
  wider than its own ground the entire time** — which is the second reason to run the tool on each
  shape rather than reason from one failure to a class.

### Worked case that does NOT qualify — an internal full stop

`derived(P) :- adult(P). N > 5, N != 9.` is two statements. All three readings, `[RAN]`:

| reading | outcome |
|---|---|
| what runs today | `derived(a)`, comparisons **severed and silently gone** |
| the OR reading (two rules) | **REFUSED** — `N` and `P` unsafe |
| the AND reading (one comma) | **REFUSED** — `N` unsafe |

⇒ There is nothing to transform *into*: the OR program **does not exist**, so rendering English for
it would describe a rule that can never fire. And a `.` is a **terminator, not an operator**, so
picking any reading resolves an ambiguity the read-back exists to surface. This stays a refusal.

### ⭐ But the guard was still wrong, and this is the second half of the lesson

**Test the DEFECT, not the character.** The guard was `re.search(r"(?<!\.)\.(?!\.)", _strip_strings(body))`
— it matched a `.`, which merely *correlates* with the failure. It therefore needed a hand-written
exception for `..`, a string-blanking pass for `kind(P,"a.b")`, and it still banned nothing a
motivated author could not reintroduce another way.

The actual defect is **one declared entry producing more than one statement**, and clingo's own
parser reports that directly:

```python
parse_string(f"x :- {body}.", seen.append)      # count ASTType.Rule
adult(P). N > 5, N != 9   -> 2      <- the defect
adult(P), N > 5, N != 9   -> 1
p(X), X = 1..3            -> 1      no special case needed
p(X), 2 = #count{Y:q(Y)}  -> 1      no special case needed
kind(P,"a.b")             -> 1      no special case needed
```

Same rejection, **no false positives, no special-casing, every ASP construct permitted**, and it
generalises to any future cause of a split. `_strip_strings` was deleted with it — it existed only
to prop up the two character-matching guards, and both are gone.

⛔ **The trap, and it caught the test as well as the code:** the old test asserted the message
contained the words `"full stop"`. That assertion passes against **either** implementation, so it
could not tell a guard that catches the defect from a guard that catches a character. A test that
names the symptom in the guard's own vocabulary cannot audit the guard's ground. It now asserts on
`"produced 2 statements"`, and `test_ordinary_ASP_is_NOT_mistaken_for_a_SECOND_STATEMENT` carries
the five-row control set of legal ASP the character version banned or needed exceptions for.

### The check to run

Grep every `raise` in a validator and put each one in the four-column table above. Anything landing
in the fourth column — **and every guard whose message names one of our own tools** — is a
candidate. For each: write the transform, run both programs, compare answer sets. If the transform
exists, the guard goes and the transform lives in the render path. If it does not, say *why* in the
guard, with the failed candidate readings **named**, so the next reader does not re-derive it.

---

## 17 ⛔ The VERBATIM CHECKER has now been the broken instrument three times

Every experiment in `resolve_runs/` asks the same mechanical question — *did the model
quote the document, or paraphrase it?* — and the check is a substring test after
normalisation. **Three times the first reported number was wrong, and every time it was
the NORMALISER, not the model.**

| reported | true | what the normaliser was missing |
|---|---|---|
| 80% | 100% | `[^footnote]` markers, curly quotes |
| 76% | — | (carried forward, believed settled) |
| 76% | **88%** | `**markdown emphasis**` — one model stripped it, another kept it |

⭐ **The tell is a SPLIT within one run.** In `iter_run1` the same model emitted
`Assistant: the entity…` (stars stripped) and `**Root**: Fundamental root rules…`
(stars kept), and only the first failed. A model is not that inconsistent about how it
quotes; a *checker* is exactly that inconsistent about what it tolerates. **A failure
mode that splits within a single run is nearly always the instrument.**

⚠️ **What is and is not a legitimate normalisation.** Strip things that are *formatting
carried by the file* — footnote markers, emphasis markers, quote-glyph variants,
whitespace runs. Do NOT strip content words, punctuation that changes meaning, or
bracketed text like `[restricted]` that the document uses as a term of art. The test for a
proposed transform: *if the document were rendered to plain prose, would this disappear?*
Stars and footnote markers would; `[restricted]` would not.

⛔ **Do not trust a verbatim rate until you have looked at the failures.** Run the
per-excerpt probe and read the first half-dozen. In all three cases above, six excerpts
were enough to see the pattern, and in all three cases the number had already been
reported to Matt before anyone looked.

**The check to run** (`iter_score.py` has it as `normalise`): for each miss, test the raw
fragment against (a) the named section, (b) the whole document, (c) the section under each
candidate extra transform. A fragment that passes (b) but not (a) is a *model* error —
right words, wrong section. A fragment that only passes under a new transform is a
*checker* error, and the transform belongs in `normalise` with a comment saying which
measured number it changed.

---

## 18 ⛔ The CORPUS FILE handed to a blind run had the answer key printed in it

An experiment was designed to remove one confound: a resolver that is told which clause borrowed a
predicate cites that clause's home passage, so "same extension" silently means "same clause". The fix
was to hand the model the document and a shuffled list of names with **no clause information at
all**. Three runs were dispatched. All three were void before they started.

⛔ **`DOCUMENT.txt` is not the document.** It is the document with a `needs_block` injected under
every section marker — **78 of them** — each reading *"[BORROWED PREDICATES — the rules written from
this section test these...]"* followed by the predicate names. The file being handed out as the
blind corpus was a **complete name → section answer key**, printed above the text it was supposed to
hide.

⚠️ **How it was caught, and it was luck.** Not by a check — by a subagent's prose report saying it
had found a name *"listed in the BORROWED PREDICATES section of `follow_all_applicable_instructions`"*.
Nothing in the JSON output would have shown it. The results would have looked like a **strong
positive**: near-perfect grounding, high agreement, exactly the answer the experiment wanted.

⭐ **THE GENERALISABLE FORM: an artifact built for one experiment carries that experiment's framing,
and the framing is often the next experiment's answer.** `DOCUMENT.txt` was correct and well-designed
for `resolve_probe.py`, whose entire question was *"given that this section borrows these names,
where are they established?"* The annotation was the point. Reusing the file for a question that must
not know the borrower inverted its meaning without changing a byte.

**The check to run — mechanical, and it must run BEFORE dispatch, not after:**

```
grep -icF "$MARKER"  corpus.txt          # the annotation's own header
grep -cE '^\s*[-*]\s*[a-z_]+/[0-9]'      # bullet lists of predicate/arity
for each name in the task:  grep -qF "$name" corpus.txt  &&  fail
```

⛔ **The last line is the one that matters and is the easiest to skip.** If the corpus contains any
string the model is being asked to locate, the task is a lookup and not a search. A **clean-corpus
assertion belongs in the dispatch path**, not in a reviewer's memory — `⚠️ still to be built as a
guard; today it is a documented manual step`, which is exactly the transcript-only procedure
`REPRODUCIBILITY.md` calls a review finding.

⚠️ **Also: the leaked runs must be DELETED, not kept and labelled.** Both leaked and clean runs write
`blind_run<N>.json`, and a stale leaked file that a later scorer globs up is indistinguishable from a
real result. Delete, then confirm every leaked agent has finished before relaunching, or the old
agent's write can land on top of the new one's.
