# Step X — stage 2's deterministic checks, and the repair loop

**Status: revision 3, for review. `checks.py` and the repair loop are NOT built.**

⚠️ **Why revision 3.** A clean-context compliance review found four **wrong-plan** items, not four
under-specified ones. Implementing revision 2 would have produced green tests over checks that
cannot fire — the failure this directory exists to prevent.

⚠️ **And much of revision 2's scope has since been BUILT**, by other hands than planned: `link.py`
was repaired, and `schema.py` gained the checks that belong at generation. The plan is
correspondingly smaller. What is left is genuinely stage 2.

---

## 1 What stage 2 specifies, and what of it now exists

`03_pipeline.md` gives five deterministic checks — *no model, no cost*.

| | check | status |
|---|---|---|
| **D1a** | compiles | ⭐ **done, `link.py`.** Note the trap: `python -m clingo` exits **0** on a parse error, on unsafe variables and on success alike, so the return code carries no signal. The error TEXT is read |
| **D1b** | no unresolved names | ⭐ **done, `link.py`** — arity-aware and `requires`-aware. ⚠️ Reports `requires-unprovided` as a **note**, not the spec's three-way `linkage` / `not-yet-translated` / `dead` diagnosis: that needs a corpus-wide provider index which does not exist |
| **D1c** | no anonymous placeholders | done in `schema.py`, at generation, in every term slot and every body |
| **D2** | a witness for every rule, at link scope | ⛔ **not built.** `witness.lp` is a hand demo for one clause |
| **D3** | no opaque stubs | ⛔ **no definition exists.** "Opaque" is not a mechanical property yet |
| **D4a** | every fact cites a real clause | done, `schema.validate(known_clause_ids=…)` |
| **D4b-1** | every referenced concept is declared | done, `schema.py` |
| **D4b-2** | every concept has a written definition | done — `Concept.gloss`, required |
| **D4b-3** | …and it finds a provider corpus-wide | ⛔ link scope — `DEFERRED.md` D-3 |
| **D5** | rule-shape declarations hold | ⭐ **done, `link.py`** |
| **#17** | cyclic `beats` is silently wrong | ⭐ **done, `link.py`** — DFS over ground `beats`. ⚠️ A *quantified* `beats` rule is a lower bound; its edges depend on what grounds |

⛔ **Correction to revision 2, which understated the defect.** It said `link.py` "cannot serve D1b or
D5". The truth was worse: its rule regex returned **nothing at all** on a new-contract file —
`[^)]*` stops at the first `)` inside a compound act term, and the trailing licence comment defeats
the `\.\s*$` anchor. Every head-shaped check was **inert**, not mis-scoped.

### On D4b-3 — the arm-B argument is withdrawn

⛔ Revision 2 argued the concept dictionary is emergent from ontology blocks, that this is Invariant
1's **arm B**, and that D4b therefore becomes link-scoped rather than blocked. Three objections, any
one sufficient:

- Arm B is *"concepts fixed in a separate step that maps names → concepts"*, and its recorded cost is
  *"needs a merge procedure with its own failure modes"*. Revision 2 claimed the arm and declined the
  obligation. A union of coined names **is** the un-normalised state arm B exists to normalise.
- Invariant 1: *"Not decided here… Do not build the merge machinery before knowing which arm we are
  in."* Open question 2: *"run both arms on the same clauses."* Part 6 names that as the single
  highest-value next action. Committing by implementation and recording it afterwards is not that.
- **Nothing in stage 2 needs an arm.** D4b-3 excludes on the flat ground that *no corpus-wide
  provider index exists under either arm today.*

⇒ Excluded on the flat ground. `DEFERRED.md` D-3 keeps the arm-B note only as a record that a
commitment was made by implementation — a thing to undo, not to justify.

---

## 2 The piece — `checks.py`, and it is now thin

`link.py` already exposes `collect(paths) -> list[Finding]`, with `Finding(check_id, severity,
where, message)` — a frozen dataclass carrying **no `fix` and no `expected` field**, asserted by a
test. `report()` is the only presentation. So `checks.py` wraps and reimplements nothing.

What is actually left:

1. ⭐ **Return the COMPLETE finding set for one attempt.** `schema.validate` raises on the first
   breach; `link.collect` returns many. A repair loop needs every finding from an attempt, or repair
   is serialised at one defect per paid call. This is `checks.py`'s real job.
2. **An abstention branch** — §3, omitted entirely from revision 2.
3. **A disclosability marker on `Finding`** — §5.

⚠️ **Cost, re-reckoned.** Revision 2 said the `link.py` split was "$0, covered by test 15". Wrong by
an order of magnitude, and now moot: the work took a full agent session and produced 22 tests. What
remains is genuinely small.

---

## 3 ⭐ Abstention, which revision 2 never mentioned

Stage 1: *"A model that cannot faithfully translate a clause should **say so**, with a reason,
**rather than produce something that passes the checks**… Without it every clause either passes or
loops forever, and coverage is invisible — you cannot tell 'we translated the document' from 'we
translated the easy parts.'"*

An abstention is forced empty on every content field, so it **passes every deterministic check
trivially**. Both defaults are harmful:

- pass it through → it enters stage 3 as a passing module, and the abstention rate is never computed
- fire a check on it → the loop re-prompts a model that has already said it cannot translate
  faithfully, **producing exactly what abstention exists to prevent**, with an accumulating error log
  behind it

⇒ **`run_checks` returns `outcome="abstained"` as a first-class result, never a findings list**, and
the loop terminates on it. An abstention is a final answer, not a failure. The run report carries the
rate and the reasons, because the rate is the reliability signal.

⚠️ Abstaining on attempt 2 is the **maximal shrink** — revision 2's "no shrinking" guard would have
flagged the correct answer as suspicious. See §4.

---

## 4 ⛔ The gaming analysis was one-sided; the guard is replaced

Revision 2 guarded against a repair that **shrinks** the module. The cheap attacks **grow** it.

| | the repair | why it goes green, and why it is wrong |
|---|---|---|
| **A** | move a predicate from `requires` to `inputs` | Satisfies disjointness (it left one list); `link.py` then reads it as a declared situation input. **Destroys the distinction the spec calls load-bearing**: *"Without it, 'a name nothing defines' cannot be told apart from 'a name supplied at query time,' and every translation looks broken or every one looks fine."* The loop would teach the model to make every translation look fine |
| **B** | `closure: "unclear"` on every act class | Legal enum, module grows. **Re-creates the silent CEPA default behind a declaration claiming a commitment was made** — measured: `open` and `cepa` are bit-identical, which is why the declaration is forced at all |
| **C** | broaden the act term and retarget the assertion | Grows. Green |

⇒ **Guard 1 becomes a TYPED comparison, not a size comparison.** Between attempts, a change to
`requires` / `inputs` / `acts` / `closure` / `forbid_body` is a **declaration edit**; a change to
`asserts` / `beats` / `defines` / `ontology` bodies is a **translation edit**. A repair that is
mostly declaration edits is flagged beside the green result, **in either direction**. Same cost.

⚠️ **Attack B needs a RATE, not a flag.** Report the `unclear` closure rate per run: a model
answering `unclear` everywhere is making no commitments, and no per-attempt diff reveals that.

Guards 2 and 3 stand — green-after-repair is never reported as green (`attempts: N`, with the
distribution in any aggregate), and the per-attempt diff is written to disk.

⚠️ Part 7 applies to that aggregate and should print beside it: *"Any per-clause pass rate reported
before [stage 9] overstates the result."*

**The attack shape is already observed, at attempt 1, before any repair pressure:** in the first live
run the model wrote `political_topic(C, _)` and annotated it *"The anonymous variable is avoided by
using a named variable in a helper rule."* It self-reported compliance while violating.

---

## 5 The repair loop, and the leak revision 2 was not defending

Stage 1's constraints, one to one:

- **fresh conversation** = a new `messages` list per attempt, no assistant turns carried. The system
  block is byte-identical, so the cache prefix holds.
- **the accumulating error log** = prior attempts and their findings, rendered into the *user* block.
- **bounded** = `max_attempts`, default 3. Exhaustion is `status: "unrepaired"` — recorded, never an
  exception, never a silent pass.
- **convergence is measured, not assumed.** The spec flags the split as untested. Findings-per-attempt
  per clause goes in the run report, so non-convergence is data rather than a hang.

⛔ **`Finding` having no `fix` field is sufficient for stage 2 and defends the wrong leak.** Stage 2's
findings derive from the module itself; no expected verdict is near them. But the spec routes **two**
answer-key-bearing edges into the same repair node:

```
RUN --|mismatch|--> FIX          stage 3 probe cases, WITH their must-forbid/must-permit labels
OK  --|fail|--> DIV --> FIX      the four review seats
```

The error log is **accumulating and persistent per clause**. The first stage-3 mismatch appended to it
carries an expected verdict into every later attempt, permanently, through a structure designed for
stage-2 findings only.

⇒ ⭐ **`Finding` gets an `origin` / disclosability marker NOW**, while there is only one origin, plus a
hard rule that the rendered log admits only stage-2-origin findings. Retrofitting after stages 3–4
attach is how the denial dissolves silently.

---

## 6 The TDD list

`walkthrough/paper_pipeline/phase_1/test_checks.py`. ⓘ Verified: pytest from `semi-formal-experiment/`
collects 2,262 tests and does not reach `walkthrough/`.

⛔ **Fixtures are CONSTRUCTED, not the live run outputs.** Revision 2 proposed committing the
`.raw.txt` files. They were produced under two superseded contracts — the 14:15 run predates the
`concepts` field entirely — so they no longer validate, and committing them would freeze green tests
over an input class stage 1 can never emit again. Build fixtures through `schema.validate()` +
`render_lp()`, as `test_link.py` does.

| # | test | why it is not vacuous |
|---|---|---|
| 1 | a clean module returns zero error-severity findings | a check that fires on everything is useless |
| 2 | the **complete** finding set is returned, not the first | one defect per paid call is the cost model failing |
| 3 | an abstention returns `outcome="abstained"` and no findings | §3 |
| 4 | the loop **terminates** on an abstention rather than re-prompting | §3 — the harmful default |
| 5 | `max_attempts` exhaustion → `status: "unrepaired"`, not an exception, not a pass | §5 |
| 6 | attempt count recorded; green-on-3 distinguishable from green-on-1 | §4 guard 2 |
| 7 | a repair moving a predicate `requires`→`inputs` is flagged `declaration-edit` **even though it returns zero findings** | §4 attack A — **the gaming case** |
| 8 | a repair adding `closure: unclear` is flagged, and the unclear RATE is reported | §4 attack B |
| 9 | `Finding` has no field that could carry an answer — assert the **field set** | ⚠️ revision 2 asked for "no suggested replacement", a natural-language property no implementation can check honestly |
| 10 | a stage-3-origin finding is **excluded** from a rendered repair log | §5 — the leak that matters |
| 11 | findings-per-attempt is in the run report for every clause | convergence is the measured thing |

⛔ **Dropped from revision 2, with reasons:** tests 1/2/8/9/15 tested `link.py`, which now has its own
22-test suite; test 3 pinned an old-contract raw file the current schema rejects on an unknown field,
so it would have gone green for the wrong reason; tests 5/6 moved into `schema.py` and are covered
there; test 11 was ill-defined — there is no "reference module" for a real clause.

---

## 7 What this explicitly does not do

- **D2 (witness), D3 (opaque stubs), D4b-3** — excluded, each for a reason stated in §1.
- **It does not judge the translation.** Whether m0091 says what clause m0091 says is stage 4 and
  needs a model. Passing stage 2 must never be reported as "correct".
- **It does not make the checks sufficient.** Part 7: correctness is not local, and any per-clause
  pass rate reported before stage 9 overstates the result.
