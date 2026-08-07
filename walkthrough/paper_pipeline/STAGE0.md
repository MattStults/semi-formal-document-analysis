# Stage 0 — competency questions, executed

2026-08-07. Hand-executed, `$0`, no provider calls. Artifacts in this directory:

| | |
|---|---|
| `competency_questions.json` | ⭐ the seven questions, their instances with expected answers written first, and the six discarded candidates |
| `cq_check.py` | runs every instance; `--collapse A=B` runs the stage-7 stopping rule |
| `cq_support/domain_totality.lp` | a totality constraint the divergence check turned out to need |
| `cq_support/reading_m0200_unqualified.lp` | a rival reading, for the CQ-3 divergence enumeration |
| `cq_support/reading_m0203_vs_m0255.lp` | the CQ-3 negative control |

Current state: **16 instances as declared, 0 unexpected, 2 blocked.** Three of the sixteen
are declared *expected to fail* and do fail — they are unmet acceptance criteria, not bugs.

```
$ python3 cq_check.py
  CQ-1.a   pass
  CQ-1.b   BLOCKED           m0142 has no module. Stage 1 has never been run on it.
  CQ-1.c   FAILS-AS-DECLARED missing bears_on(m0203,harm_3p)
  ...
  CQ-5.a   FAILS-AS-DECLARED present but should be absent: bears_on(m0255,harm_3p)
  CQ-7.a   FAILS-AS-DECLARED missing beats(m0203,m0200)
  16 as declared, 0 unexpected, 2 blocked
```

---

## The seven questions

Each is sourced from a stated purpose — `HANDOFF.md`'s 2026-08-06 goal restatement, or
`HARNESS_REDESIGN.md` §0's north star, or `03_pipeline.md` Part 4's own general-question
list. No purpose here was invented; the `purpose_source` field on each question names it.

| id | question | consumed by | status |
|---|---|---|---|
| **CQ-1** | Given a behaviour-like statement, which passages bear on it, and what is the derivation? | scoping · stage 7 · acceptance | 1 pass, 1 blocked, 1 unmet |
| **CQ-2** | Under what conditions does a named exception apply, and when does it stop applying? | stage 3 · stage 7 · acceptance | 4 pass |
| **CQ-3** | Do two passages, or two readings, decide any situation differently — and which? | stage 6 · stage 11 · acceptance | 2 pass |
| **CQ-4** | If this passage were amended or removed, which conclusions change? | stage 8 · acceptance | 2 pass, 1 defect found |
| **CQ-5** | Which non-textual facts is this conclusion resting on, and does it survive switching them off? | stage 4c · acceptance | 1 unmet, 1 pass |
| **CQ-6** | When the tool cannot decide, what exactly is missing? | stage 2 · stage 8 · acceptance | 3 pass |
| **CQ-7** | When two passages pull opposite ways, does the document state which governs? | stage 1 · stage 8 · acceptance | 1 unmet, 1 blocked |

Seven, inside the design's five-to-ten. CQ-7 is deliberately unmet: a list on which
everything already passes is describing the solution.

### What was thrown out, and why

The design's step 4 — *"throw out any question whose expected answer you cannot state"* —
removed three, and two more went for other reasons. Full text in `competency_questions.json`
under `discarded`.

| discarded | rule | why |
|---|---|---|
| *Is this action permitted by the specification, overall?* | step 4 | Ruled out of scope by Part 5 open question 1 (aggregation). Independently unstatable: under plain ASP the answer is an artifact of the closed-world reading (problem #13), not a fact about the document. |
| *Which passages are ambiguous?* | step 4 | No definite answer. The design's own stage-6 revision already retired this output and replaced it with an enumeration — that replacement is CQ-3. |
| *How strongly does this passage bear on this behaviour?* | step 4 | `HANDOFF` item 7 says grading is lexicographic over discrete features, but the rung ladder is not written down. I could not state an expected grade for m0255 × harm-3p without inventing it. **Revisit once the ladder exists** — this one is not-ready, not wrong. |
| *Is this translation faithful to its clause?* | step 1 | A question about the pipeline (stage 4b), not about the finished body of knowledge. |
| *Does clause A depend on clause B?* | CQ ≠ test case | This is `link.py`. It survives only inside CQ-6, where the dependency is a *diagnosis attached to a user-visible verdict* rather than an internal check. |
| *Does the document address a topic at all?* | step 5 | Merged, not rejected: it is the negative branch of CQ-1's answer shape. |

⚠️ One thing the design's step 4 does **not** say and should. Applied alone, it selects for
questions the system already answers — every unmet question is one whose expected answer you
can state and whose *observed* answer you cannot. The rule that actually worked was: *throw
out a question whose **expected** answer you cannot state; keep one whose expected answer you
can state and whose observed answer is wrong.* CQ-7 exists only because of the second half.

---

## ⭐ Unknown 1 — what format does a competency question take?

**Not prose. A record with an executable instance list.** The fields below are the ones that
earned their place by being needed; nothing here is speculative except where marked.

### Question level

| field | why it is needed |
|---|---|
| `id` | downstream stages cite it. `granularity_demand` and the stopping-rule report are both *lists of ids*. |
| `question` | the general form. One sentence, definite answer. |
| `purpose_source` | ⭐ **the field that stops invention.** Every question names the document and line that says someone wants this. Writing this field is what killed *"how strongly does it bear"* — I could not find a source that specified the grade. |
| `answer_shape` | what a well-formed answer *is*, independent of any instance. This is the field a downstream consumer actually reads (see Unknown 2). It is where CQ-4's "two sets, reported separately" and CQ-6's "one of {linkage, untranslated, dead}, naming the symbol" live. |
| `consumed_by` | which stages read this question. Without it, "competency questions scope the work" stays a slogan. |
| `instances` | 2–4, per the design. |

### Instance level

| field | why it is needed |
|---|---|
| `given` | the situation in English. |
| `expected_written_first` | ⭐ the design's rule. Kept in English, deliberately — see below. |
| `checked_against_passages` | real clause ids from `modelspec_clauses.json`. Enforces the design's step 3 ("use real passages, not invented ones") by making the omission visible. |
| `run` | **the executable half.** `{kind, modules, omit_facts, enumerate, project, expect}`. Without this the record is aspirational. |
| `expect` | the expected answer restated as atoms: `holds`, `absent`, `unsat`, `model_count`, `all_models_contain`, `union_over_models_equals`, `unresolved`. |
| `granularity_demand` | ⭐ **the field stage 7 consumes.** Which concept distinctions this instance forces. See Unknown 2. |
| `note` | carries the declaration *"Expected to FAIL"*, which the runner treats as a first-class outcome. |

**Why `expected_written_first` and `expect` are two fields and not one.** They say the same
thing in two languages and the gap between them is where the errors were. Twice the English
was right and the atoms were wrong, or the reverse (findings F1, F4). Collapsing them to a
single machine-readable field would have silently discarded both findings; collapsing them to
a single English field would have made the record unrunnable, which is the failure mode the
design warns about in its ⛔ column.

**Why not YAML/prose/a table.** JSON because `cq_check.py` is the validator and there is no
schema file: an instance is well-formed iff the runner can execute it and reach a verdict.
That is the same discipline the rest of this directory uses — the check, not the document, is
the contract. *(Judgement call, not derived from the design.)*

### ⚠️ What the format cannot do yet

`expect` is a set-containment language over ground atoms. It cannot express *"the stated
reason must be X"* except by naming the reason atom (CQ-2.b does this: `unlifted(...,
is_an_action)`), and it cannot express the rule-set claims at all — CQ-2.c's real content
("no rule may derive `lifted` from `purpose`") is checked by `link.py --forbid-body`, which
this format has no slot for. **That is a hole. Two verification modes are needed** — the same
conclusion `WALKTHROUGH_REPORT.md` reached from the other direction — and the CQ record
currently supports only one of them cleanly.

---

## ⭐ Unknown 2 — how does a downstream stage read one and act on it?

The design names three consumers. They are genuinely three different mechanisms, and doing
the work made only two of them concrete.

### (b) Stage 7 EXPAND — the stopping rule. **This one is mechanical, and it runs.**

The design says: *expand a concept only as far as some question requires.* Stated forward
("how far does this question require?") it is unanswerable — there is no way to read a
granularity off a question. Stated backward it is a solver call:

> **A concept distinction is licensed iff collapsing it breaks some competency-question
> instance. Collapse it, re-run every instance, and see. If nothing breaks, the distinction
> is not licensed and stage 7 stops.**

That is `cq_check.py --collapse A=B`, and it discriminates:

```
$ python3 cq_check.py --collapse action=information
  7 broken: CQ-1.a, CQ-2.a, CQ-2.b, CQ-2.d, CQ-3.a, CQ-4.a, CQ-4.b
  ⇒ the distinction is REQUIRED, and these instances are what license it

$ python3 cq_check.py --collapse sensitive=restricted
  0 broken
  ⇒ NO competency question distinguishes these symbols. Stage 7 must not expand here.

$ python3 cq_check.py --collapse new_material=transformation_of_user_content
  8 broken: CQ-1.a, CQ-2.a, CQ-2.b, CQ-2.c, CQ-2.d, CQ-3.a, CQ-4.a, CQ-4.b
  ⇒ REQUIRED
```

Three things this made concrete that the prose did not:

1. **The output is a citation, not a boolean.** "Splitting `material_type` into information
   and action is licensed **by CQ-2.b and CQ-3.a**" is an auditable answer; "yes, expand" is
   not. `granularity_demand` on the instance is the human-written form; the probe is the
   machine-checked form. **They did not agree, and the probe was right in the direction that
   matters:** I declared the information/action distinction on CQ-2.b and CQ-3.a; the probe
   shows it is also load-bearing for CQ-1.a, CQ-2.a, CQ-2.d, CQ-4.a and CQ-4.b. Every
   hand-written demand was confirmed (a fourth probe, `--collapse prohibited=restricted`,
   breaks 5 instances including CQ-1.a, which declared it) — but hand-writing them
   **under-reports by roughly half**. ⇒ Treat `granularity_demand` as documentation of intent
   and the probe as the authority.
2. **The probe must be baseline-relative.** The first version reported every
   already-failing instance as broken by every collapse. Fixed; noted here because it is the
   obvious way to build this wrong.
3. **The rule is a lower bound on granularity, and it collides with Invariant 3.**
   `restricted` vs `sensitive` is licensed by *no* question — yet the two live in separate
   modules because they come from separate clauses (m0200, m0201), which isomorphism
   requires. **Precedence must be stated and is not:** the stopping rule licenses
   *expansion*; it never mandates *contraction*, and it cannot override one-clause-one-module.
   Contraction is stages 5 and 6's job, under their own acceptance test.

### (c) Acceptance — the success criterion. **Concrete: it is the runner's exit code.**

A stage 0 whose product is a list nobody can run is the failure the design's own ⛔ column
describes. Here the criterion is: `cq_check.py` exits 0 iff every instance matches its
declaration, *including the instances declared to fail*. An instance that starts passing
unannounced is reported as a failure ("declared as expected-to-fail, but PASSED — update the
declaration"), because a silently-fixed acceptance criterion is a lost finding.

### (a) Scoping — **the design is wrong about this, or at least undrawable as drawn.**

The pipeline diagram has `CQ -.scopes.-> IN`, i.e. the questions decide which clause texts and
concepts enter stage 1. **That arrow cannot be followed at stage 0.** CQ-1.a names exactly one
clause, m0255. The scope it actually needs is `{m0255, m0200, m0201, m0203}` — and I did not
know that from the question. `link.py` computed it at stage 2, by reporting `policy_class`,
`scope` and `out_of_scope` as unresolved.

So the real relation is a fixpoint, not an arrow: **a competency question names *seed*
clauses; the link closure computes the working set; a question whose closure does not
terminate inside the translated corpus is the definition of a blocked instance** (CQ-1.b,
CQ-7.b). The scoping consumer is therefore not stage 1 — it is stage 8 (LINK), which is the
only place that knows the closure. The diagram should show the CQ node with a return edge
from LINK, not a one-way dotted arrow into the input block.

---

## Findings from doing it

**F1 — the divergence check (stages 6 and 11) is unsound as specified.** CQ-3.a's expected
answer, written first, was *"the readings differ exactly on actions."* The run returned **24
models**, most of which differed only because `witness.lp` lets `material_type` be unset, so
"material of no stated type" appeared as a substantive divergence. With a totality constraint
(`cq_support/domain_totality.lp`) and `--project`: **3 models, all `material_type(x,action)`**
— the written-first answer. ⇒ **The design's "enumerate the situations in which they decide
differently" needs two conditions it does not state: totality constraints on every choice
domain, and projection.** Without them the output is a combinatorial haystack containing
spurious findings, and it is wired to a stopping rule.

**F2 — amendment produces a silent verdict.** CQ-4.a deletes m0203 and re-asks case B.
`violation(prohibited_content, m2)` disappears, as expected — but so does everything else:
no `lifted`, no `binds`, no `unlifted`, no diagnostic. The solver reports a satisfiable model
in which the question simply has no answer. This violates `HANDOFF` item 6 (*no silent
verdicts*), and nothing in the solver catches it — only `link.py` does (CQ-6.b, which reports
`out_of_scope` unresolved). ⇒ **Amendment impact is not answerable by re-running the solver.
Every amendment query must carry its link-check, and CQ-4's `answer_shape` now says so.**

**F3 — the query side hardcodes clause ids.** CQ-1.c asks whether m0203 bears on
harm-avoidance-to-third-parties. It should: m0203 governs prohibited content, and
`behaviour_harm3p.lp` already asserts `protects_third_party(prohibited_content)`. It does not,
because that file contains `governs_production(m0255, P) :- policy(P).` — the *behaviour*
module names the clause. ⇒ The north star requires the query side to be cheap and
document-agnostic; today it is neither. Relevance as demonstrated in `WALKTHROUGH_REPORT.md`
step 6 does not generalise past the one clause it was written for. This is n=1 and may be an
artifact of hand-writing the behaviour file, but it is exactly what stage 1 must not produce.

**F4 — `WALKTHROUGH_REPORT.md`'s load-bearing-fact claim is false as stated.** It says of
`bears_on(m0255, harm_3p)`: *"Change that one fact and the match disappears."* Switching off
`protects_third_party(restricted_content)` leaves the match standing — it survives through
`protects_third_party(prohibited_content)`. Both must go (CQ-5.b). ⇒ **Invariant 2's
toggleability needs *minimal supports*, plural, not "the load-bearing fact".** A report that
names one fact when two independent ones exist understates how robust the conclusion is, and
the error is invisible without running the toggle. This is the single clearest argument for
making the expected answers executable.

**F5 — the one existing translation contains unlicensed expansion.** `m0255.lp` lines 81–82
are two rules identical except for `K = restricted` / `K = sensitive`. The stopping-rule probe
finds **no competency question distinguishes them** (`--collapse sensitive=restricted`, 0
broken). Under stages 5/6 they are one rule with `scope(transformation, K)` in the body. Not
fixed here — this directory's rule is that a stage is hand-executed before it is automated,
and the collapse is stage 6's call, not stage 0's. Recorded as a candidate.

---

## What should change in `03_pipeline.md` Part 4, stage 0

1. **Say the concrete instances must be executable, with the expected answer in two forms.**
   The section says "write the answer you expect" and stops. Two of my seven written-first
   answers were wrong (F1, F4) and neither was detectable by reading. This is the single
   biggest gap in the section.
2. **Fix the scoping arrow** (`CQ -.scopes.-> IN`). It is a fixpoint with stage 8, not a
   one-way dependency. See Unknown 2(a).
3. **State the stopping rule in its backward form**, with the collapse probe as its
   mechanism, and state its precedence against Invariant 3 and stages 5/6.
4. **Add the companion to step 4:** keep a question whose expected answer you can state and
   whose observed answer is wrong. Step 4 alone selects for what already works.
5. **Give stage 0 a slot for rule-set claims.** CQ-2.c's actual content is checkable only by
   program inspection, and the record has nowhere to put `%% forbid-body: lifted <- purpose`.
6. **Name Invariant 2's consumer.** Toggleability appears in the invariants and in `HANDOFF`
   item 5 and has no stage in the diagram that reads it. CQ-5 is that consumer; without a
   competency question demanding it, nothing in the pipeline ever switches an assumption off.
7. ⚠️ **The stage numbering is inconsistent three ways and should be fixed before anyone
   builds against it.** The diagram has 7=EXPAND, 8=LINK, 9=MUTATION, 10=TRANSLATE-TWICE.
   Part 4's headings include "6 — Divergence" (the diagram puts divergence inside the stage-4
   review loop) and "9 and 10 — Testing the tests" whose body then discusses "11 — Translate
   twice". The task that commissioned this work called expand "stage 8". I have used the
   **diagram's** numbering throughout — expand is **7**, link is **8** — and flag it rather
   than resolving it, per this directory's rule about unrecorded departures.

## Where I am guessing

- That JSON with the runner as its own validator is the right format, rather than a schema
  file. Justified above but not derived from anything.
- That seven is the right number. The design says five to ten; I have no evidence about where
  in that range this corpus sits.
- CQ-7's expected answer assumes a superiority relation over *clause ids* (`beats(m0203,
  m0200)`). Part 5's ruling adopts a superiority relation but does not say what it ranges
  over. Clause ids is the choice Invariant 3 implies; it is not stated anywhere.
- F3 is n=1 on a hand-written behaviour module and may not survive a real stage-1 run.
