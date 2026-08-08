# Clean review of `model/pipeline.lp` against `resources/03_pipeline.md`

**Date:** 2026-08-07 · **Reviewer:** clean-context agent, did not write the design or the model
**Trigger:** `guard.py` ⛔ STALE — `resources/03_pipeline.md` `7339e4e118f6d5d8 -> 607c68e35024929d`
**Brief:** `model/REVIEW_BRIEF.md`
**Disposition:** ⛔ **Do not `--accept`.** The model does not yet describe the current design.
Nothing here was edited except this file.

---

## 0. Could I review it confidently?

**Yes for the model; qualified yes for the design.** The model's facts are traceable and the
document is specific enough to license or refuse most of them. Two things blocked full confidence
and are recorded as design-side findings (§4), not resolved: the stage numbering is inconsistent
in at least six places, so `check(C, Stage, _)` cannot be checked against a single authority; and
the closing ruling of open question 1 states requirements without saying which pipeline stage or
artifact owns them.

---

## 1. Invented facts

Ordered by severity. Each names the search done to license it.

### 1.1 ⛔ `catches(normalise, p9)` — pipeline.lp:64. Invented, and it is false comfort.

The model asserts the normalise seat **closes** #9 (*same name, different meanings*).

Searched: every occurrence of "9", "normalis", "same name", "meanings". The design's normalise is
line 603: *"**Normalise** is horizontal: two clauses name one concept differently; pick one entry."*
That is #8, and the model records `catches(normalise, p8)` for it correctly. Nothing anywhere says
normalising closes #9. The design's own remedy for #9 is Invariant 1 (line 71), which is
**undecided** — line 112: *"⇒ **Not decided here.** Both arms are cheap."*

Worse, the design states #9 has an irreducible floor. Line 692:

> ⇒ **Our measured 20% multi-definition rate is the ordinary rate for this task, not a defect.**
> Problem #9 has a floor set by the work itself. The target is not zero.

**Effect on the output.** `catches(normalise, p9)` makes `caught(p9)` true by closure, which
suppresses `finding(only_narrowed, p9, single_reading_only)` (rules.lp:79-80). `narrows(diverge,
p9, ...)` is then invisible. This is exactly the failure the model's own comment at pipeline.lp:40-44
says the `catches`/`narrows` split was introduced to prevent: *"an earlier version recorded
everything as `catches`… That is false comfort, which is worse than an open finding."*

The waiver at `accepted.json:110-114` (`silent_needs_determinism/p9`) reasons correctly — *"a
uniformly-wrong reading has no twin to differ from"* — and is contradicted by the `catches` fact
sitting twelve lines away.

### 1.2 `check(coverage, s2, deterministic)` — pipeline.lp:49. Stage is invented; the effect is the one the brief warned about.

The check itself is licensed as a *possible* check — line 56: *"ASP has published structure-based
coverage criteria — rule, definition and loop coverage over the dependency graph — and they are what
#12 needs. A clause with four claims and one test case fails definition coverage mechanically."*
It is accounted (`todo`, pipeline.lp:119).

The **stage** is not. Coverage is defined at line 965 as *"whether the tests exercise each rule and
each definition"* — it needs the probe set, which stage 4 (`s4`) builds. Stage 2 is the five
deterministic checks D1–D5 of the diagram (lines 178-183); coverage is not among them, and line 55
says #12 has *"**no corresponding check anywhere in the pipeline**"*.

**Effect.** `det_planned(p12)` holds via rules.lp:71, so `silent_needs_determinism` never fires for
p12 — the problem the design calls, at line 41, *"the problem this pipeline addressed least well."*
The brief's warning that one of these *"disabled the model's flagship rule on its own flagship
example"* still applies, now via the stage rather than via the fabrication.

Same objection, weaker, to `check(cycle_beats, s2, ...)` (pipeline.lp:56): a `beats` cycle spans
clauses and can only be checked at link scope (`s9`). The design does not say where; it says only
(line 38) *"Needs a mechanical cycle check on the `beats` relation."*

### 1.3 `catches(fresh, p4)` — pipeline.lp:60. Unlicensed mapping.

Seat 4b's row (line 538) reads: *"**4b clean** | clause + paraphrase, never the code | unfaithful
claims | anything imported from elsewhere"*. Its `catches` column says *unfaithful claims*. #4 is
*"Right answer, wrong stated reason"* — a **faithful verdict** with a wrong justification, and the
design attributes its cause to tooling (line 30: *"A property of the tooling used, not of ASP"*),
with the remedy in the translation instructions, not in a seat. No sentence maps 4b to #4. Plausible
by inference; not licensed.

### 1.4 `narrows(diverge, p9, single_reading_only)` — pipeline.lp:62. Unlicensed mapping.

Section 6 (lines 578-596) is about **reviewer** disagreement — line 585: *"one reviewer saying the
paraphrase is faithful and another saying it is not"*. The model reads "two readings" as two
interpretations of a name and maps it to #9. The design never connects §6 to #9. Given 1.1 also
mis-records #9, the net effect is that #9's coverage in the model is entirely inferred.

### 1.5 `catches(probe_run, p11)` — pipeline.lp:57. Inferred, not stated.

Design §3 (lines 520-528) argues only that must-permit cases detect over-permissiveness. The
supporting sentence for #11 is line 527: *"The solver enumerates candidate situations; the model
only labels them."* That licenses *"enumeration cannot produce an impossible situation"* — a
property of **stage 4's construction**, not of `probe_run` (the diagram's `RUN[run them ·
deterministic]`). The attribution is to the wrong object.

### 1.6 `check(anthem, s2, deterministic)` — pipeline.lp:54, and `todo(anthem, ...)` at :123.

The check is licensed by D5 (line 183: *"rule-shape declarations hold"*) and by the `forbid_body`
field (lines 435-437: *"rule-set claims that no test case can demonstrate"*). The **name** is not:
`grep -n anthem` over the design returns exactly one hit, line 990, in the Sources list. The design
never says anthem 2.0 implements D5. `todo(anthem, "external tool identified (anthem 2.0); not
wired")` states a design decision the design does not contain.

### 1.7 `declared_departure/1` ×3 — pipeline.lp:173-175.

`no_cycle_driver`, `no_panel_fencing`, `no_dev_test_split` are licensed by `walkthrough/README.md`
lines 41-42, **not** by `03_pipeline.md`, which is the declared source of truth. They are also dead:
nothing in `rules.lp` reads `declared_departure/1`.

### 1.8 `forbidden(probe_labeller, expected_verdicts)` — pipeline.lp:82.

The probe labeller *produces* the verdicts (line 188: *"model labels each must-forbid /
must-permit"*). The design's "denied the expected verdicts" rule is stated only for the translator
(line 385) and the repair seat (line 355). Harmless but unlicensed.

### 1.9 `todo(stub_leaf, ...)` — pipeline.lp:143.

*"a predicate standing for a referenced section with NO defining rules is a bare leaf"* is a
mechanism the design does not propose. Note `STEP_stage2_and_repair.md` §1 independently reports
D3 as *"⛔ no definition exists. 'Opaque' is not a mechanical property yet"* — i.e. a second
reviewer reached the opposite conclusion about whether this mechanism is available.

### Checked and licensed

All 17 `problem/3` facts against the Part 1 table (categories, detection values, including
`p3=loud` from *"Loud but ignorable"*, `p7=loud` from *"Loud — crashes"*, `p16=silent` from
*"Structurally silent"*). All six `seat/2` and their `sees`/`forbidden` against the table at lines
537-540 and the deny list at lines 380-385. `exposes/2` ×3. All six `claim/3` against lines 35, 36,
37, 44, 46. `invariant/3` ×3 against Part 2. `specified(coverage_rule, citation_checker)` against
lines 545-576 and open question 5. `blocked_by(coverage_rule, invariant_2_unimplemented)` against
line 566: *"⛔ **Prerequisite, currently unmet: facts do not carry licences yet.**"* The three
`implementation/2` entries against Part 6's built table (line 905-907) and its *"Three components of
roughly fifteen have running code"*.

One provenance slip: pipeline.lp:24 attributes p17 to *"(deolingo assessment)"*; the design line 38
says *"Found while assessing a superiority kernel, 2026-08-07."*

---

## 2. Omissions — ranked by what a rule could have done with them

### 2.1 ⛔ The entire CLOSED ruling of open question 1. Nothing. Not one fact.

This is the delta that made the guard fire, and the model records **none** of it. Lines 724-755:

> ⭐ **Plain clingo, plus a superiority relation, plus exactly ONE deontic axiom.**
> **Structure:** one encoding of the document (`asserts/3`), one of the behaviour (`b_asserts/3`)…
> ⛔ **The namespace separation is mandatory.** … Enforce with a type constraint.
> **The one deontic axiom: `O(¬a) ≡ F(a)` over act complements.**
> **Also required, none yet implemented:**
> - act-index both sides — without it the natural encoding derives **zero** conflicts, silently
> - `beats/2` → **`beats(Sayer, Winner, Loser)`** — `m0255` *states* an override, scores 5/6, and is
>   unreachable because nothing records who said it
> - ⭐ a **forced, per-act default-closure declaration**, enforced in `link.py`

Five requirements, three of them explicitly *"none yet implemented"*. The model has vocabulary that
fits them exactly — `specified/2` + `blocked_by/2`, with `finding(specified_not_built, …)` at
rules.lp:52 — and uses it for one thing only (`coverage_rule`), with the rule hard-wired to
`per_item/1` so it cannot generalise. See §5.1.

Two further consequences the model also misses:

- **The design now attributes an enforcement to a file the model has already characterised.**
  Line 748 says the closure declaration is *"enforced in `link.py`"*; pipeline.lp:116 says
  `implementation(link, "walkthrough/link.py — anchor closure + unresolved predicates")`. Those are
  two different descriptions of one file, and nothing compares them.
- **The evidence base of the ruling is unrecorded.** Line 754: *"⚠️ Evidence is 17 clauses of 593,
  one behaviour, hand-encoded, and the closure result rests on an inference the behaviour text does
  not license."* `claim(representation_ruling, "contradiction_probe + deontic_probe", 1)` — one
  behaviour — would fire `claim_n_is_one` (rules.lp:40) on a ruling the design calls CLOSED. That
  is the single highest-value missing fact in this review.
- Line 750: *"**Contrary-to-duty needs nothing:** zero clauses in 593 have a CTD antecedent"* — a
  measured claim with n=593, unrecorded.

### 2.2 ⛔ Invariant 2's fourth licence class, and the licence classes themselves.

Lines 133-136:

> ⛔ **The three classes do not reach the behaviour side.** All are defined relative to *the
> document*; a fact read out of a **behaviour statement** fits none of them. **A fourth class is
> required** — found 2026-08-07…

The model has no `licence_class/1` facts at all. It records `specified(licence_annotation,
translation_format)` and `todo(licence, "blocked: facts do not carry licences yet")`, and that is
the whole of Invariant 2. So:

- the three classes `textual`/`assumed`/`world` (lines 122-126) are unmodelled;
- the **required fourth class** is invisible — there is nothing for a rule to count;
- open question 5's routing table (lines 866-870) says *"the case types already exist… **they are
  Invariant 2's licence classes**"*, so a seat-routing rule keyed on licence class also has no
  facts to stand on;
- line 558's *"**The denominator is licence-dependent**"*, which is why `coverage_rule` is blocked,
  is asserted in the model as an opaque atom rather than derived.

Also unrecorded: line 138, *"⭐ **A conclusion inherits the weakest licence in its derivation.**"*

### 2.3 ⛔ Abstention. Absent entirely.

Design line 346 (*"ABSTAIN with a reason — a real answer, and the rate is a reliability signal"*),
the `Abstention` dataclass at lines 438-442, the section at 448-455 —

> A model that cannot faithfully translate a clause should **say so**, with a reason, rather than
> produce something that passes the checks. Published work… reports abstention rates from 5% to 52%
> and treats the rate as a live reliability signal.
> Without it every clause either passes or loops forever, and coverage is invisible — you cannot
> tell "we translated the document" from "we translated the easy parts of the document."

— and line 923's *"75–87% end-to-end… with 5–52% abstention"*. Zero occurrences in `pipeline.lp`.
Stage 1 has two outcomes in the design and one in the model.

### 2.4 Invariant 3 is recorded as holding when the design says it is violated.

`invariant(i3, one_clause_one_module)` (pipeline.lp:160) records the invariant. Line 154 records its
status: *"⛔ **This invariant is currently violated by the design's own handling of exceptions.** …
The mechanism that lets an exception live in its own module and defeat a rule in another is a
**superiority relation†**, standard in defeasible deontic logic and **absent from what we built**."*

The model has no `violated/1` or `remedied_by/2`. A rule of the shape "an invariant recorded as
violated needs a named remedy with an implementation-or-todo" would connect §2.4 to §2.1 — the
superiority relation *is* the remedy, and open question 1 has now adopted it.

### 2.5 The four review seats' asymmetry, and seat 4a's disqualification.

Line 537: *"**4a author** | its own translation | misunderstanding | ⚠️ **measurably biased toward
its own output** — LLM evaluators recognise and favour their own generations. **Weakest seat: a
cheap first pass, never evidence**"*.

`seat(self_check, s5)` exists at pipeline.lp:71 but no `check/3` names it and no `catches/2` is
attached, so the disqualification is invisible: the model cannot express "this problem's only
catcher is a seat that is never evidence". Similarly unmodelled: line 542, *"⚠️ **4b must never see
the logic.**"* is modelled (`forbidden(fresh_reader, logic_source)` ✅) but line 543, *"⚠️ **4d needs
the whole set.**"* is modelled only as `sees(completeness, all_paraphrases)` with no constraint that
it is an error to run it on one.

### 2.6 The three practices adopted in Part 4b — none recorded, none accounted.

Lines 666-684 adopt: (1) *"A CI job that loads the published artifact and runs the published
queries"*; (2) *"DPV's concept record, wholesale"* with *"**79% citation coverage** is the realistic
target, not 100%"*; (3) *"A named-removal changelog per revision."* Plus line 679, MIREL's
undefined-term marker. Four adopted commitments with no code. If recorded as checks, all four would
fire `unaccounted_check` or need a `todo` — which is the point of that accounting section.

### 2.7 Measured claims the design states and the model does not carry.

The design opens Part 1 with *"Every measured figure names its source and its n"* (line 22). The
model records six. Missing, at minimum: MIREL Jaccard 0.30/0.24/0.29 and 18.4% token disagreement,
n=3 annotator pairs (line 688); DPV 79% citation coverage (line 677); 234 competency questions /
106 patterns across 5 ontologies (line 320); 9 models × 10 EU provisions, ρ = +0.09 (line 651); nine
repositories surveyed, *"One is alive, one cites machine-readably, zero have a test suite"* (line
663); LKIF 48 forks / 39 with zero commits (line 712); *"Two of nine specimens examined had none"*
(line 947); F1 ≈ 0.74 and 75–87% (line 923). Several of these are n=1 or n=small and would fire
`claim_n_is_one`.

### 2.8 Part 7's four standing limits.

Lines 935-948: *"**Correctness is not local.** … Any per-clause pass rate reported before then
overstates the result"*; *"This project has **ten recorded human adjudications in total**"*;
*"**Concept minting has no cost model.**"*; *"**Clause coverage is incomplete.** … Two of nine
specimens examined had none — invisible in any aggregate score, and fatal to any coverage claim
built on the clause as the unit."* None recorded. The last one falsifies the model's unit of
analysis and nothing says so.

### 2.9 Open questions 2, 3 and 4 have no representation.

The model touches OQ3 and OQ5 only inside `todo` strings. OQ2 — Invariant 1's arms A/B/C, which
line 495 calls *"**Run both arms on the same clauses before building anything downstream that
assumes one**"* and Part 6 line 928 calls the *"Highest-value next step"* — has no fact. Neither
does `sees(translator, concept_dictionary)`, which is arm-A-conditional (line 377). There is no
`open_question/2`, so a ruling landing on one (as OQ1 just did) has nowhere to be recorded. This is
the structural cause of omission 2.1.

### 2.10 Stage-model gaps.

- No `parameterise` stage: `check(param, s7, seat)` puts it inside `normalise`, while line 602
  is titled *"Why normalising and parameterising are **different** operations"* and line 607 gives
  the reason merging them is wrong.
- The acceptance test both stages share (lines 610-626) — *"the **coarsest partition** that
  survives"*, cheap candidate proposal, order-dependence to a confirmed fixpoint — is unmodelled.
  Line 628: *"⚠️ **This is where correctness stops being local.**"*
- The diagram's `V4 -.-> GEN` feedback edge (line 202) — a missing rule-set claim becomes a
  declaration — is unmodelled.
- The interpretation registry and its anti-fitting constraints (line 600) are unmodelled.
- `exposes/2` has three facts; there is no `produces/2` or `consumes/2`, so "a stage-1 output no
  stage-2 path handles" is not expressible. See §5.3.

---

## 3. Accounting (`implementation/2` vs `todo/2`)

**Clean.** 20 checks; 3 carry `implementation`, 17 carry `todo`; `unaccounted_check` does not fire
and its self-test case proves it can (`c99`). The 3 implementations match Part 6's three built
components exactly.

⚠️ Against the brief's *"`todo/2` is scaffolding… it should shrink over time, not grow"*: it has
grown. Two are now questionable —

- `todo(coverage, ...)` and `todo(cycle_beats, ...)` were added to account for the two facts a prior
  review found invented. Accounting for a fact does not license its stage (§1.2).
- `todo(anthem, ...)` states a tool choice the design does not make (§1.6).

And one is now **stale against evidence elsewhere in the directory**:
`todo(cycle_beats, "the design says #17 needs a mechanical cycle check on beats/2; not written")` —
`paper_pipeline/phase_1/STEP_stage2_and_repair.md` §1 records `#17` as *"⭐ **done, `link.py`** — DFS
over ground `beats`"*. The model still owes a check that has been built. That is `todo/2` rotting in
the other direction, and the guard cannot see it because it does not watch `link.py`.

---

## 4. Contradictions inside the design (reported, not resolved)

1. **17 problems, called 16.** Line 171 (stage diagram input): *"instructions, worked examples,<br/>
   and the 16 error cases"*. Line 335 (stage 1 diagram): *"the 17 known failure modes"*. Part 1
   lists 17. Line 171 is stale since #17 was added.
2. **Test cases are stage 3 and stage 4.** Line 315: *"Stage 3 of this pipeline builds test cases
   for a single passage"*. Line 486: *"⇒ Stage 1 emits a module. **Stage 4** tests it, from a
   different seat."* Line 476: *"because **stage 4** already is them"*. The diagram says 3.
3. **Two different things are stage 6.** Heading at line 578: *"### 6 — Divergence, replacing the
   ambiguity exit"*. Heading at line 602: *"### 5 and 6 — Why normalising and parameterising…"* The
   diagram numbers PARAMETERISE 6 and leaves DIV unnumbered.
4. **"9 and 10" contains 9 and 11.** Heading line 632: *"### 9 and 10 — Testing the tests"*; body
   line 642: *"**11 — Translate twice, enumerate the disagreement.**"* The diagram says 10.
5. **Stage 7 is the merge, and also EXPAND.** Line 823: *"**Stage 7's merge** is exactly the shape
   this project already removed from its own process"* — the merge is diagram stage 5 (NORMALISE);
   diagram stage 7 is EXPAND.
6. **Stage 9 is where corpus-level correctness appears, and also mutation.** Line 937: *"Whether it
   is correct *in the corpus* … is visible only at **stage 9**"* — that is LINK, diagram stage 8;
   diagram stage 9 is MUTATION.

⇒ Every `check(C, Stage, _)` in the model rests on a numbering the document does not hold
consistently. The model's own scheme (`s3=repair`, `s4=test_cases`, `s5=read_back`, `s6=divergence`,
`s7=normalise`, `s8=expand`, `s9=link`) matches neither the diagram nor the prose: it promotes
REPAIR — unnumbered in the diagram — to a stage and drops PARAMETERISE. That choice is defensible
and is nowhere recorded.

7. **An unresolved review comment is embedded in the design.** Line 376 carries an inline reviewer
   query in the cell text: *"<√Are you confidence the document's own mardown anchors are sufficient
   to give every cross reference accurately? …>"*. It bears directly on `sees(translator,
   closure_texts)` — if anchors are insufficient, #2's mitigation is weaker than modelled.

---

## 5. Would this model have caught today's five conformance failures?

Verdict up front: **one was caught and not obeyed; one is one small rule away; three are out of
reach of the model as scoped.** Coverage tracks the author's imagination here, and the boundary is
real.

### 5.1 OQ1's CLOSED ruling not implemented in the stage-1 contract → **could fire; the rule is one generalisation away.**

The model has the right vocabulary and uses it once. `rules.lp:52-53`:

```
finding(specified_not_built, coverage_rule, Blocker) :-
    per_item(S), specified(coverage_rule, S), blocked_by(coverage_rule, Blocker).
```

The subject is a **constant**, and the body is gated on `per_item/1`. It cannot say anything about
anything but `coverage_rule`. Generalise it —

```
finding(specified_not_built, X, Owner) :- specified(X, Owner), not built(X).
built(X) :- implementation(X, _).
```

— and add five facts drawn verbatim from lines 744-748:

```
specified(act_indexing,        stage_1_contract).
specified(beats_sayer,         stage_1_contract).   % beats(Sayer, Winner, Loser)
specified(closure_declaration, link_py).            % "enforced in link.py"
specified(namespace_type_constraint, stage_1_contract).
specified(deontic_axiom_o_not_a, stage_1_contract).
```

Each would then fire until an `implementation/2` landed. The design even hands over the `⚠️ none yet
implemented` marker. **This one was in reach and was simply not written.** Cost: one rule rewrite,
five facts. It is the cheapest of the five by a wide margin and I would do it first.

### 5.2 #17 had no detector and was in neither list of a plan claiming to enumerate both → **the model holds the fact; it cannot reach the plan.**

`problem(p17, cross_clause, silent)` and `check(cycle_beats, s2, deterministic)` +
`catches(cycle_beats, p17)` + `todo(cycle_beats, ...)` are all present, and `check.py --self-test`
proves the rule fires when the catcher is dropped:

```
[PASS] a problem loses its only catcher
        `uncaught_problem` introduced: ['p17']
```

So the model **knew #17 existed and knew nothing was built for it**. It could not fire, because the
failure was in `STEP_stage2_and_repair.md` — a plan document the model does not represent and
`guard.py` does not watch (`WATCHED` is `03_pipeline.md`, `pipeline.lp`, `rules.lp` only).

Closing it needs `plan/1`, `plan_in_scope/2`, `plan_out_of_scope/2` and

```
finding(plan_unenumerated, Plan, P) :-
    plan_claims_exhaustive(Plan), problem(P,_,_),
    not plan_in_scope(Plan,P), not plan_out_of_scope(Plan,P).
```

⚠️ Honest reservation: those facts must be **transcribed by hand from prose**, and a transcription
that omits #17 reproduces the original failure inside the model. This is not a mechanical extension.
**A rendered checklist of all 17 problems, printed and diffed against any plan claiming exhaustive
scope, would have been strictly more reliable than the logic.** `check.py` already emits `label/2`
for all 17 and could print that checklist today.

### 5.3 Abstention absent from a stage-2 plan → **structurally out of reach.**

Nothing in the model mentions abstention (§2.3), so there is nothing to fire on. But the deeper
problem is dimensional: the failure is *"a stage-2 plan has no path for one of stage 1's two
outcomes"*, and the model has no notion of a stage's outputs or of a downstream path consuming them.
It has `exposes/2` (what a stage leaks to a seat) and nothing else.

Reaching it needs a new relation, not a new fact:

```
produces(s1, module).  produces(s1, abstention).
handles(s2, module).
finding(unhandled_output, St, O) :- produces(St, O), next(St, St2), not handles(St2, O).
```

That is a second graph over stages, and every `handles/2` fact is again a hand transcription of a
plan. **Two facts are cheap; the relation is a real extension; the transcription burden is the same
one that sinks 5.2.** I would add `produces(s1, abstention)` regardless, because §2.3 is a plain
omission from the design's own text, and let the rule wait.

### 5.4 #13's ⛔ escalation dropped from a prompt → **out of reach, and the model actively records the wrong residue.**

This is the one I would fix on its own merits even though it would not have fired.

Design line 42: *"⛔ **More than a testing gap:** plain ASP's closed-world reading of `not
forbidden(X)` silently commits the whole corpus to *"whatever is not forbidden is permitted"*
(CEPA vs CNPA). **No probe coverage surfaces a global semantic commitment.**"*

The model says, at pipeline.lp:57-58:

```
narrows(probe_run, p13, outside_the_probe_set).
%%   escapes: over-permissiveness on situations no probe covers. A test, not a proof.
```

The named residue is *"situations no probe covers"*. The design says the residue **is not about any
situation** — it is a commitment of the whole corpus, which is why no amount of probe coverage
reaches it. The model records #13 as an ordinary coverage shortfall and its waiver
(`accepted.json:78-82`) repeats that reading. The ⛔ is not merely absent; it has been paraphrased
into something weaker.

Reachable form:

```
escalated(p13, global_semantic_commitment).
finding(escalation_unrecorded, P, E) :-
    escalated(P, E), narrows(_, P, R), R != E.
```

That would have fired **today, on the current facts**, and pointed at exactly the sentence the
prompt-writer dropped. The prompt itself is still unwatched — but a model that carried the
escalation would have put it in front of whoever wrote the prompt. Cost: one fact, one rule, one
corrected `narrows`. Second priority after 5.1.

### 5.5 A prompt built from a stale read of the design, while the guard was red → **the model caught this and it did not bind.**

`guard.py` printed ⛔ STALE with the correct digests, and `hooks/pre-commit` is written to block a
commit touching a watched file:

```
COMMIT BLOCKED. The formal model is stale or reporting findings.
```

Commit `00d33f5` landed anyway. Two possibilities, and I cannot distinguish them without git, which
I am not permitted to run: the hook is not installed (it requires a manual
`ln -sf … .git/hooks/pre-commit`, per its own header), or it was bypassed with `--no-verify`, which
the hook's own text advertises. **Worth checking before anything else in this list** — a gate that
fires and is walked past is the cheapest thing here to repair.

Second, narrower gap: the guard protects the *model* from design drift; it does not protect
**derived artifacts** from design drift. `paper_pipeline/phase_1/prompt/30_failure_modes.md` is a
transcription of Part 1 and `prompt/00_task.md` transcribes Invariant 2 and the abstention rule.
Neither is in `WATCHED`, in `guard.py:46` or in `hooks/guard_hook.py:17`. A design edit can silently
invalidate them even when the model is green. Adding them to `WATCHED` is a two-line change and
turns 5.5 from "a red light was ignored" into "the light also points at the prompt". ⚠️ It also
introduces a second, cruder staleness signal — digest-level, so it fires on typos.

### The boundary, stated plainly

Of the five, the model **held the relevant facts** for two (5.2, 5.5 — and it fired on 5.5), could
hold them cheaply for two (5.1, 5.4), and would need a new relation for one (5.3). But the common
thread in 5.2, 5.3 and 5.4 is not modelling power — it is that **the failures occurred in plans and
prompts, and this model describes only `03_pipeline.md`**. The model checks the constraints its
author wrote about one document; it cannot see documents derived from that one. That is the honest
boundary, and no rule added inside `pipeline.lp` moves it.

---

## 6. Is extending the model to `paper_pipeline/phase_1/` worth doing?

**Estimate: no, not as a logic model. Yes as one two-line change plus a printed checklist.**

### What is actually there

`schema.py` (775 lines), `translate.py` (1907), `test_schema.py` (869), `test_mutate.py` (271),
`mutate_schema.py` (555), four prompt files (469), `STEP_stage2_and_repair.md` (201).

### Why a `phase_1.lp` would not earn its cost

1. **The oracle problem inverts.** `REVIEW_BRIEF.md` records that this model *"has **no oracle**"*
   and that *"A sibling model elsewhere in this repo is differentially tested against executing
   code."* `phase_1/` **is** executing code with 1,140 lines of tests over it, including
   `mutate_schema.py`, which is mutation testing of exactly the kind Part 4 §9 describes. A logic
   model of code that already has a mutation harness is the weaker instrument, and it would be a
   second hand-authored assertion set with the same author.
2. **The contract is already self-documenting against the ruling.** `schema.py:21-27` records
   `act-indexing → Assertion.act`, `beats(Sayer, Winner, Loser) → Superiority`, `per-act default
   closure → Closure, and FORCED`. The traceability the model would add is in the docstring, in
   code, where a test can hold it.
3. **The transcription tax dominates.** Every finding in §5 that needed new facts needed them
   transcribed from prose by hand, and a wrong transcription reproduces the original failure
   silently. Over five files and 5,190 lines that tax scales badly and the failure is invisible.
4. **It cannot check the thing that failed.** Failures 5.1–5.4 were all *"the design says X and the
   artifact does not"*. A model built from the artifact records what the artifact does. The gap is a
   correspondence between two documents, and a single-sided model of either one cannot hold it.

### What I would do instead, in order

| | change | cost | buys |
|---|---|---|---|
| 1 | Confirm `hooks/pre-commit` is installed; if it is, find out how `00d33f5` landed | minutes | 5.5, which is the failure that let the other four propagate |
| 2 | Add `prompt/*.md`, `schema.py`, `STEP_stage2_and_repair.md` to `guard.py:46 WATCHED` | 2 lines | a design edit flags every artifact transcribed from it |
| 3 | Generalise `finding(specified_not_built, …)` off `coverage_rule`; add the 5 OQ1 facts | ~10 lines | 5.1 fires; every future ruling has a home |
| 4 | Add `escalated/2` + its rule; correct `narrows(probe_run, p13, …)` | ~5 lines | 5.4 fires today |
| 5 | `check.py --checklist` printing all 17 `label(pN, …)` | ~10 lines | 5.2, by the reliable route rather than the clever one |
| 6 | Fix §1.1 `catches(normalise, p9)` → delete; record #9's floor from line 692 | 2 lines | removes the model's one live false-comfort claim |

Items 1–6 total well under an hour and address four of the five failures. A `phase_1.lp` is
several days and addresses none of them directly. ⚠️ Items 3, 4 and 6 change what the model
reports; under this directory's own rule they are the human's to make, not a reviewer's.

---

## 7. Run output

```
$ python3 check.py
15 findings — 0 blocking, 15 waived
  GAP: only_narrowed        p13, p14, p2                    [all waived]
  GAP: silent_needs_determinism  p1, p13, p14, p2, p6, p9   [all waived]
  GAP: specified_not_built  coverage_rule                   [waived]
  DISCLOSURE: claim_n_is_one  completeness_ok, divergence, flat_siblings,
                              reviewer_blind, witness_scope  [all waived]

$ python3 check.py --self-test
  [PASS] a problem loses its only catcher — uncaught_problem introduced: ['p17']
  [PASS] the OLD repair loop — contamination introduced: ['repair_seat','translator']
  [PASS] a check placed at a stage that does not exist — check_no_stage: ['bogus']
  [PASS] a silent problem loses its deterministic floor — unaccounted_check: ['c99']
  [PASS] GREEN: contamination absent on the real model

$ python3 guard.py --self-test
  [PASS] guard sees findings at all (15 via direct import)
  [PASS] every recorded waiver matches a live finding (15/15)

$ python3 guard.py
  ⛔ STALE — resources/03_pipeline.md  7339e4e118f6d5d8 -> 607c68e35024929d

$ python3 -m pytest test_model.py -q
  15 passed in 0.87s
```

**Everything passes. Nothing failed.** All 15 findings are waived with valid date/who/why; no waiver
is stale; no `review_by` has passed. The only failure is the intended one — STALE — and it is the
design's, not the model's.

⚠️ This is precisely the shape the brief warns about. `check.py`'s own docstring, lines 12-16:
*"WHAT THIS CANNOT DO. It cannot tell whether a `catches` claim is TRUE. If the model says the
citation checker catches invented entities and it does not, the model confirms coverage and is
wrong."* Every defect in §1 and §2 is invisible to every rule in `rules.lp`. A green run here is
evidence of internal consistency and of nothing else.

### One code defect, minor

`check.py:38-62` — the `CLASS` dict defines `"unaccounted_check"` three times and
`"specified_not_built"` twice. The first occurrence of each is a bare string, not the
`(class, clears)` tuple every consumer expects. The last assignments win so behaviour is correct
today, but `cls, _ = CLASS.get(kind, ...)` at line 158 would raise `ValueError` on a 3-character
string if the order ever changed. Also `"no_coverage_rule"` is classified but can never fire while
`specified(coverage_rule, citation_checker)` holds.

---

## 8. Disposition

⛔ **Do not run `guard.py --accept`.** The model does not describe the current design: the whole
of open question 1's CLOSED ruling and Invariant 2's required fourth licence class are absent
(§2.1, §2.2), and one live fact (§1.1) asserts coverage the design contradicts in plain words.

The accept should follow the human's decisions on §1.1, §2.1 and §2.2 — not this review.
