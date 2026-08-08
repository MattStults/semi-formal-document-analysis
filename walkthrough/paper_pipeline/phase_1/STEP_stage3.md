# Step X — stage 3: build test cases for a translated clause, and run them

**Status: revision 2, for review. Nothing is built. This document is the plan only.**

⚠️ **Every claim below about existing code was executed**, and is marked `[RAN]` with the command
or the number it produced. Claims taken from reading a file are marked `[READ]`. Three previous
Step-X plans in this directory were found *wrong* — not under-specified — by a clean reviewer, and
the commonest error was a scope table asserting a capability nobody had exercised. Two of the
scope rows below changed after running them.

⚠️ **`03_pipeline.md` was re-read at the point of writing**, per `STATE.md` NEW-7. Stage 3 is the
`PROBE` node of the Part 3 flowchart (*"3. BUILD TEST CASES — solver enumerates situations; model
labels each must-forbid / must-permit"* → *"run them · deterministic"* → *"mismatch → FIX"*), plus
Part 4 §3 (*"Why test cases must include must-permit"*).

⛔ **A numbering contradiction in the source of truth, found by reading.** The Part 3 flowchart
numbers probe cases **3** and read-back **4**. Part 4 §*"Do we also require unit tests here?"* says
*"the probe cases at **stage 4** are the unit tests"* and *"Stage 1 emits a module. **Stage 4**
tests it, from a different seat."* Same object, two numbers. This plan uses the flowchart's
numbering (**3 = probe cases**) because the task brief and the repair-origin table
(*"**stage 3**, probe-case mismatch — carries an answer key: **Yes**"*) both do. Recorded, not
resolved: it is a defect in `03_pipeline.md`'s prose, not in this plan.

---

## 0 ⭐ REVISION 2 — the order is inverted, and the reason is measured

**Stage 3 as the design specifies it is the SECOND most valuable thing here, and the design has it
ahead of the first.** Revision 1 planned labelled verdicts as the main event. This revision puts
**discrimination coverage** first and puts labelled verdicts behind a measurement.

### The evidence

`m0255` — the design's flagship worked example — has **five hand-written probe cases**, which is
exactly what stage 3 automates. Its claim **C3** ("purpose never creates an exemption") is two
rules. Delete both:

| | |
|---|---|
| the five probe cases | **bit-identical** — every one |
| models enumerated | 144 → **144** |
| do the rules fire? | **yes** — 36 of 144 models satisfy a C3 body, so *rule coverage passes them* |
| what caught it | **mutation. The probe cases did not.** |

And the same shape from the other side, in §3 below: under `m0217`'s own declared `cepa` closure,
deleting the module's **only** rule changes **0 of 8** situations — a naive stage 3 reports 8/8 on
an empty module.

### Why this is structural, not a matter of enumerating harder

A verdict comparison asks *"does the module give the right answer in situation X?"*

⇒ **An inert rule changes no answer in any situation, by definition.** So verdict-based testing
cannot detect one — not with more situations, not with better labels, not ever.

And an inert rule is the failure actually observed here, twice: `m0255`'s C3, and `m0217`'s single
rule whose body predicates were declared only as concepts so it could never fire. Both passed every
check that existed at the time.

### What each half buys

| | catches | cost | has it caught something here? |
|---|---|---|---|
| **discrimination coverage** — mutate the module's own rules, confirm some situation changes | inert rules, claims that do nothing | **free**, deterministic, no model call | ⭐ **yes, twice** |
| **labelled verdicts** — enumerate, have a seat label, compare | a module that is live but WRONG about the clause | a model call per clause, and a seat that must hold a three-valued distinction | not yet — no module exists rich enough to try |

They are complementary and neither subsumes the other: mutation proves a rule *matters*, never that
the module is *right*. Only a label compares the module against the document.

⇒ **Build discrimination coverage first, measure what it catches on a real corpus, and let that
decide whether labelled verdicts earn their per-clause cost.** Today we would be paying for a check
whose failing case is demonstrated and whose passing case has never been observed — on a corpus
holding one assertion in total.

### ⚠️ This is a recorded departure from `03_pipeline.md`

The design orders stage 3 as *"solver enumerates situations; model labels each"*. This plan does the
solver half first and gates the model half on a measurement. The design's own Part 1 #12 concedes
coverage is *"the problem this pipeline addressed least well"* and points at **structure-based
coverage criteria** — which is what discrimination coverage is. To be folded into the design if this
revision survives review.

⇒ **Sections 2–9 below stand as written and describe the labelled-verdict half.** They are the plan
for phase two, not for what gets built first. §3's failing example and §4's impossible-state problem
apply to both halves and should be read now.

---

## 1 Scope

### What stage 3 does

Given one module that has **already passed stage 2**, plus its link scope (the transitive anchor
closure of clause modules it requires):

| | | model? |
|---|---|---|
| **3a** | **Enumerate** the coherent situations over the module's *situation signature* — every assignment to its free predicates that the module's own program admits | no |
| **3b** | **Reduce** the enumeration to a covering set under a declared coverage criterion | no |
| **3c** | **Label** each situation in the covering set: does the clause *require* this act be forbidden, *require* it be permitted, say *nothing* about it, or is the situation one that *cannot arise*? | ⭐ **yes — the only paid work in stage 3** |
| **3d** | **Run** the module against each labelled situation and compare the derived status to the label | no |
| **3e** | **Report** coverage, the label distribution, and every mismatch — routed by origin (§5) | no |

### What stage 3 does not do

- **It does not judge the wording.** Whether the module *reads* like the clause is stage 4 (read-back,
  four seats). Stage 3 only compares derived statuses to labels.
- **It does not run at corpus scope.** Link scope only, for the reason `03_pipeline.md` Part 4 §2
  gives: run on a clause alone, a good rule looks dead.
- **It does not produce a per-clause pass rate that means anything.** Part 7: correctness is not
  local. A clause can pass every situation here and be forced to change at stage 5.
- **It does not create the module's integrity constraints.** It *consumes* them (§4) and reports
  when they are missing. Authoring them is stage 1's job, reached via a stage-2-shaped finding.

### Which of Part 1's testing failure modes it addresses

| # | | stage 3 |
|---|---|---|
| **11** | test cases describing impossible situations | ⭐ **addressed structurally** — situations are answer sets of the module itself, so a situation the module's constraints reject is never generated. **Partially:** a module that declares no constraints has nothing to reject with. §4 |
| **12** | testing one branch only | ⭐ **addressed, and this is the point of 3b** — coverage becomes a computed number with a named criterion, not a judgement. ⚠️ The obvious criterion (rule coverage) is **insufficient**, measured in §6 |
| **13** | only testing that it forbids | ⭐ **addressed by construction** — the enumeration is verdict-blind, so must-permit and must-be-silent situations appear at the same rate as must-forbid ones. ⛔ **But the global CEPA/CNPA commitment is NOT reachable from any probe**, exactly as #13 says. §3 is the demonstration |
| **14** | claims no test case can demonstrate | ⛔ **cannot be addressed and must not appear to be.** `forbid_body` declarations are checked by `link.py` at stage 2 by inspecting the program. Stage 3 must *count* them and exclude them from its denominator, or a clause whose only unenforced claim is a `forbid_body` claim reports full coverage |
| **15** | "never fired" has three causes | **addressed for two of three** — link scope separates *"waiting on an unlinked clause"* from *"genuinely dead"*. The third (*"the tests do not reach it"*) is dissolved: the solver enumerates, so there is no test-author to under-reach |

⚠️ **#5 (hollow stubs) arrives here in a new form and stage 3 makes it worse if built naively.**
The situations are expressed in the translator's own coined predicate names, which echo the
document's words by construction. A labelling seat shown `political_content(x), broad_audience(x)`
grades the *names*. Mitigation in §5; it is the reason the seat is shown glosses, never signatures.

---

## 2 A specific PASSING example

**Clause `m0217`**, from `runs/20260807-154618-together-deepseek-v4-flash/` — the only new-contract
conditional module in the runs with any `asserts`. Its whole logic is one rule `[READ]`:

```
%% acts: produce(M)
%% closure: produce = cepa
asserts(m0217, permit, produce(M)) :- political_content(M), broad_audience(M),
                                      not exploits_individual(M).
```

**3a — the situation signature.** ⛔ **Not `%% inputs:`.** `[RAN]` `m0217.json` has
`inputs: []`, `requires: []`, `acts: ["produce(M)"]`. All three body predicates are declared in
`concepts.json`, and `link.py` classifies them exactly so:

```
$ .venv/bin/python link.py runs/…-154618/m0217.lp runs/…-154618/m0037.lp runs/…-154618/m0053.lp
concept table: 10 row(s) from …/concepts.json
  declared in the concept table (expected head-less): broad_audience/1,
      exploits_individual/1, political_content/1
  ✅ no unresolved references
```

⇒ **The situation signature is `inputs ∪ (head-less predicates declared in the concept table)`, at
link scope.** Building it from `inputs` alone would give the empty set and stage 3 would enumerate
one situation, find nothing, and report green. That is a scope row that changed because it was run.

**3a result** `[RAN]`: three unary predicates over one material `x` → 2³ = **8 candidate
situations, 8 coherent** (the module declares no constraints — see §4).

**3b** `[RAN]`: MC/DC-style reduction (§6) selects **4** of the 8 — the one firing situation and
its three single-flip neighbours.

**3c — the labelled case.** Situation `S₆`:

> The material is political content. It is crafted for an unspecified or broad audience. It does
> **not** exploit the unique characteristics of a particular individual or demographic for
> manipulative purposes. The act is: produce it.

(rendered from `concepts.json` glosses — see §5). Label from the clause text *"political content
that is crafted for an unspecified or broad audience is allowed, as long as it does not exploit…"*:
⇒ **MUST-PERMIT**.

**3d** `[RAN]`, all 8 situations solved against `m0217.lp`:

```
(pc, ba, ex)  derived
(0,0,0)  —      (0,0,1)  —      (0,1,0)  —      (0,1,1)  —
(1,0,0)  —      (1,0,1)  —      (1,1,0)  asserts(m0217,permit,produce(x))     (1,1,1)  —
```

**Verdict: match.** `S₆ = (1,1,0)` is the only situation deriving `permit`, and it is the only
must-permit label. Its three MC/DC neighbours `(0,1,0)`, `(1,0,0)`, `(1,1,1)` are labelled
**silent** and derive nothing. Stage 3 passes `m0217` with a coverage report of
`4/4 labelled · 1 must-permit · 0 must-forbid · 3 silent · 0 impossible`.

⚠️ **`0 must-forbid` is reported as a number, never suppressed.** `m0217` forbids nothing, so the
must-forbid half of the test set is empty *for this clause* and the reader must be able to see
that. §3 is what happens when it is not.

---

## 3 ⭐ A specific FAILING example — stage 3 reports success and is wrong

**The same clause, `m0217`, and the naive design passes it 8/8 on a module with its only rule
deleted.**

The design says the model labels each situation **must-forbid / must-permit**. Take that literally:
the labeller answers in two values, and 3d compares against the module's *resolved* verdict — the
status the corpus would return for the act, which is what a competency question actually asks
(*"list every passage that forbids this"*). Resolving requires the closure declaration, and
`m0217` declares `produce = cepa` — **silence permits**.

`[RAN]` Delete the single `asserts(...)` line from `m0217.lp` and recompute the cepa-resolved
verdict for all 8 situations:

```
situations where the CEPA-resolved verdict differs: 0 of 8
  (0,0,0) permit permit    (0,0,1) permit permit    (0,1,0) permit permit    (0,1,1) permit permit
  (1,0,0) permit permit    (1,0,1) permit permit    (1,1,0) permit permit    (1,1,1) permit permit
```

**Every situation still resolves to `permit`. The empty module scores 8 of 8.** The pipeline
reports *"stage 3: m0217 passed, 8/8"*, the translation is worthless, and nothing anywhere in
stages 1–3 says otherwise — `link.py` also returns `✅ no unresolved references` on the emptied
file, because there is nothing left to resolve.

This is Part 1 #13 with its sign flipped. The design's own sentence — *"a translation that forbids
everything passes every 'does it correctly say no' test"* — has a mirror image nobody wrote down:
**under `cepa`, a translation that says nothing at all passes every "does it correctly say yes"
test**, and `cepa` is the closure `m0217` actually declared.

### The three things that follow, and they are the load-bearing part of this plan

1. ⭐ **The comparison is on the DERIVED atom, never on the closure-resolved verdict.** Labels are
   **three-valued**: `must-forbid` · `must-permit` · `must-be-silent` (*the clause does not speak
   to this*), with `impossible` as a fourth, non-verdict answer (§4). `[RAN]` under the
   three-valued comparison the same mutation flips **1 of 8** — `(1,1,0)` goes from `permit` to
   `silent` — and stage 3 fails the emptied module.
2. ⭐ **A pass is reported as a vector, never a fraction.** `1 must-permit · 0 must-forbid ·
   3 silent` on a covering set of 4. A single-number pass rate is what let 8/8 look like evidence.
3. ⛔ **Stage 3 cannot check the closure declaration and must say so.** The whole point of the
   forced per-act closure (`STATE.md` NEW-2: *"`closure=open` is bit-identical to `closure=cepa`"*)
   is that it is a **global semantic commitment**, and #13 states flatly: *"no probe coverage
   surfaces a global semantic commitment."* Stage 3's report carries the declared closure verbatim
   and marks it `NOT TESTED HERE`. Any design that folds closure into the verdict re-creates this
   failure.

⚠️ **Residual, after all three fixes.** `m0217`'s covering set has exactly **one** discriminating
situation. The check's entire power over this clause is 1 bit. That is not a defect to fix — it is
the true information content of a one-rule clause — but it must be *reported*, because
`4/4 labelled` and `1 discriminating situation` are very different pieces of evidence and only the
second is worth anything.

---

## 4 ⭐ What it looks like when the check is measuring the wrong thing (#11)

#11: *"A test asserted material was both brand new AND a transformation of user-supplied content.
The program accepted it and produced the right answer from an impossible state."* That is the
history of `m0255_case_d.lp`, in the file's own comment `[READ]`.

**The design move: situations are not written, they are ANSWER SETS OF THE MODULE.** A candidate
assignment is ground into the module at link scope and solved. `UNSAT` ⇒ the module's own integrity
constraints reject it ⇒ it never becomes a test case. There is no separate well-formedness
language to keep in sync with the logic, which is where #11 came from.

`[RAN]`, `m0255.lp` + `clauses/m0200,m0201,m0203.lp`, signature of 7 predicates over one material:

```
total enumerated 2^7 = 128   SAT: 92   UNSAT (rejected by the module's own constraints): 36
```

36 of 128 impossible states are removed with no model call and no hand-written filter, including
every `new_material ∧ transformation_of_user_content` pair — the exact `case_d` defect — and every
state where `lifted` and `binds` would both hold.

### Three ways this still measures the wrong thing, and what each costs

| | |
|---|---|
| ⛔ **Silent suppression is the pass-looks-like-did-not-run shape.** A situation dropped for `UNSAT` is byte-identical in the output to a situation the enumerator never proposed. If a translator over-constrains — `:- political_content(M).` — the enumeration shrinks to nothing and stage 3 reports *"all 0 situations matched"* | ⇒ **the suppressed count is a first-class output**, and `suppressed / candidates` above a declared threshold, or a coherent set of size 0, is an **ERROR**, not a clean run. `STATE.md`: *"a check whose 'pass' state is indistinguishable from its 'did not run' state is broken by design"* |
| ⛔ **A module with no constraints filters nothing.** `[RAN]` `m0217.json` declares zero constraints, so all 8 of its situations are "coherent" including `political_content ∧ broad_audience ∧ exploits_individual`, which may well be document-impossible. The mechanism that protected `m0255` is simply absent | ⇒ **`impossible` is a label the seat may return**, and it is the only label that is *not* a verdict. It produces a finding of the form *"the module admits a situation the clause treats as impossible"* — naming the situation and no verdict — which is why it is **disclosable** (§5) |
| ⛔ **Coherence is not possibility.** The constraints encode what the *translator thought* was impossible. A translation that omits a constraint the document implies produces coherent nonsense that the labeller then dutifully labels | ⇒ this is why the `impossible` label exists rather than a deterministic check. It is the one place stage 3 asks the seat about the *world* rather than about the clause, and the report separates `impossible`-rate from mismatch-rate so the two are never summed |

---

## 5 Who labels, and what they are shown

⛔ **Not the translator, not its transcript, not its model instance.** `03_pipeline.md`: *"A
translator writing its own tests checks what it already thought of, and it would need the expected
verdicts, which stage 1 is explicitly denied."* A separate seat with its own brief, per the
ten-element seat contract (open question 5, RULED: adopt all ten).

| shown | denied |
|---|---|
| the clause text, verbatim | ⛔ **the module. Any of it.** Not the `.lp`, not the JSON, not the rule bodies |
| the texts of cross-referenced clauses at link scope (same closure stage 1 got) | ⛔ the module's `claims` list — it is the translator's reading, and a seat shown it grades that reading |
| the situation, rendered **from `concepts.json` glosses**, one English sentence per fact | ⛔ **the coined predicate names.** `political_content/1` is the document's own words; a seat shown it agrees with the label by echo. Invariant 1: *"the read-back renders the definition, not the label"* |
| the act, as an English phrase (`produce this material`) | ⛔ the derived status, the closure declaration, any other clause's verdict, and any behaviour |
| the four permitted answers and the instruction that **`silent` is a real answer**, with the same framing abstention gets at stage 1 | ⛔ prior stage-3 results for this clause, on repair |

**The denominator is computed from the enumeration, never supplied by the seat** — the same rule
`03_pipeline.md` gives for the citation checker. Every enumerated situation must carry exactly one
labelling, no labelling may name a situation id that was not enumerated, and every label must carry
a non-empty reason; a run failing any of these is **not adjudicated**. A seat that skips the hard
situations otherwise returns a complete-looking set, and the skipped ones are the discriminating
ones.

### ⭐ What a stage-3 mismatch discloses, and what it withholds

`checks.Finding.origin` is required and never defaulted `[READ]`, and the filter is **already
built** — `[RAN]`:

```python
>>> translate.DISCLOSABLE_ORIGINS
('schema', 'link')
>>> translate.render_error_log([('attempt 1', [stage3_finding, link_finding])])
'attempt 1 failed these checks:\n  - [unresolved-reference] m0217.lp: nothing declares …\n
   - (1 finding(s) withheld: they come from a later stage and would disclose an expected answer)\n…'
```

So the fence exists. The question this plan must answer is what stage 3 *emits*, and the honest
answer forces a **departure from the design's own arrow**.

⛔ **The `RUN --mismatch--> FIX` edge cannot be honoured for verdict mismatches without leaking the
answer.** The verdict space is three-valued, but for any one situation the module derived
*something specific*; telling the translator *"situation S is wrong"* leaves at most two
possibilities and, in the two-valued sub-case that covers most rules (derived-vs-not), **naming the
situation IS the answer key**. Withholding the label while naming the situation is not a partial
disclosure; it is the whole disclosure with a fig leaf.

⇒ **Stage 3 emits findings under two distinct origins.**

| origin | contains | disclosable | routes to |
|---|---|---|---|
| `probe-structural` | *"rule R is in no derivation over the covering set"*, *"claim C₃ is not discriminated by any situation"*, *"the module admits a situation the clause treats as impossible: ⟨situation⟩"*, *"the coherent set is empty"* | ⭐ **yes** — derived from the module and the solver alone, with **no expected verdict anywhere near them**, exactly as stage 2's are. Added to `DISCLOSABLE_ORIGINS` | the accumulating repair transcript |
| `probe-verdict` | a situation whose derived status disagrees with its label | ⛔ **no.** Withheld, leaving the visible hole `render_error_log` already emits | ⭐ **not the transcript.** §below |

⇒ ⭐ **RULING: a `probe-verdict` mismatch discards the transcript and re-runs stage 1 from a clean
prompt**, up to `max_retranslations` (default 1), then the clause is recorded
`status: "probe-mismatch"` and carried, unrepaired, to stage 4 and to a human. **Rejected by name:**
*(a)* **"append the mismatch to the transcript"** — the transcript is persistent per clause, so one
appended label lives there for the rest of that clause's life (the leak `STEP_stage2_and_repair.md`
§5 was written to stop); *(b)* **"disclose the situation but not the label"** — the paragraph above;
*(c)* **"let stage 3 findings drive repair with the labels stripped to a count"** — a count of
mismatches plus an unchanged module is a hill-climbing signal against a hidden answer key, which is
the anti-cheat perimeter the wider repo exists to defend. Re-translation carries no information
from the mismatch at all, which is the point: it costs one stage-1 call and leaks zero bits.

⚠️ **This is a departure from `03_pipeline.md`'s flowchart and is recorded as one.** If the design
wants the arrow, the design must say what crosses it.

---

## 6 The evidence produced, and telling "the translation is right" from "the test set was too weak"

Per clause, a `probe.json`:

```
candidates · coherent · suppressed · covering-set size
labels: must-forbid / must-permit / must-be-silent / impossible   (counts, and the situations)
discriminating situations: n          ← the number that matters
coverage: <criterion> = k/N covered, with the uncovered items NAMED
forbid_body claims: n  (NOT TESTABLE HERE — checked by link.py, excluded from the denominator)
closure declared: produce = cepa      (NOT TESTED HERE — #13)
mismatches: [(situation, label, derived)]        ⛔ withheld from any repair prompt
```

#12 is the design's own admission that coverage is *"the problem this pipeline addressed least
well"*, and it names the remedy: *"ASP has published structure-based coverage criteria — rule,
definition and loop coverage over the dependency graph."*

### ⛔ Rule coverage is insufficient, and this was measured, not argued

`m0255`'s claim **C3** (*"purpose never lifts a policy"*) is encoded as two rules:

```
binds(P,M) :- policy_class(P,K), K = restricted, forbids(P,M), new_material(M).
binds(P,M) :- policy_class(P,K), K = sensitive,  forbids(P,M), new_material(M).
```

`[RAN]` **Those rules fire.** Instrumented with a marker head and given
`new_material(x), forbids(restricted_content,x)`: `fired_c3 present: True`. **Rule coverage is
satisfied.**

`[RAN]` **Deleting both rules changes nothing.**

```
MUTATION: delete both C3 rules -> 0 of 128 situations change verdict
```

`[RAN]` **And all five hand-written probe cases are bit-identical against the mutant:**

```
a SAME   b SAME   c SAME   d SAME   e SAME
```

The rules are subsumed: `unlifted(P,M,not_user_supplied) :- forbids(P,M), not
transformation_of_user_content(M)` already derives `binds` in every situation the C3 rules reach,
and the coherence constraint `:- new_material(M), transformation_of_user_content(M)` excludes the
rest. `[RAN]` The same thing shows up in the MC/DC scan as an input with **no discriminating pair
at all**:

```
input transformation_of_user_content(x)   discriminating pairs:  20
input new_material(x)                     NO discriminating pair  ⛔
input material_type(x,information)        discriminating pairs:   4
… (5 more, all non-empty)
coherent situations: 92   distinct verdicts: 24   MC/DC-style covering set size: 8
```

⇒ ⭐ **The criterion is DISCRIMINATION coverage, not rule coverage.** A rule is covered iff there
exists an enumerated situation whose derived status *changes when that rule is removed*; a claim is
covered iff at least one of the rules carrying it is covered; a situation input is covered iff it
has a discriminating pair. This is stage 9's mutation technique brought forward to the clause, and
it is the only criterion tested here that separates *"the translation is right"* from *"the test
set was too weak"* — because an uncovered rule is a **named** artifact in the report (`C3:
uncovered — 2 rules, 0 discriminating situations`) rather than an absence.

⚠️ **A whole claim of the walkthrough's flagship clause is behaviourally dead, and neither
`link.py` nor the five hand probes caught it.** That is a finding about the existing worked example,
produced by running, and it belongs in the record independently of this plan.

⚠️ **Discrimination coverage is necessary and not sufficient.** It cannot see #14 claims (excluded
from the denominator by name), cannot see the closure commitment (#13), and cannot see a claim the
translator never encoded at all — that is stage 4d, over the whole case set.

---

## 7 Cost

**Solver time is free and measured, not assumed.** `[RAN]` 128 ground-and-solve cycles over
`m0255` at link scope (4 files): **0.13 s**. The `m0217` enumeration is 8 cycles.

**Model calls.** One labelling call per clause, batched — every situation in the covering set in
one request, because the denominator rule requires the seat to see the whole set anyway and
per-situation calls would multiply the clause context by the set size.

Priced from `config.json` `[READ]`: **$0.14 / $0.28 per Mtok**, input billed at the full rate (the
config declines to claim the cached rate).

| | |
|---|---|
| labelling brief (system, cacheable, identical every clause) | ~1,200 tok in |
| clause + link-scope cross-references | ~250–800 tok in (measured range for the 4 run clauses: `m0217` user block 1,173 B, `m0091` 5,341 B `[RAN]` `ls -l`) |
| situation table, glossed | ~45 tok × covering-set size |
| labels + reasons out | ~50 tok × covering-set size |
| **per clause, covering set of 8** | ≈ 2,300 in + 400 out ≈ **$0.00043** |

**A four-clause run costs ONE labelling call — about $0.0005.** `[RAN]` from
`runs/20260807-154618-…/run.json` and the four module JSONs:

| clause | `acts` | `asserts` | reaches stage 3? |
|---|---|---|---|
| `m0037` | `[]` | 0 | ⛔ no — 4 claims, 5 concepts, **zero** asserts/defines/ontology/closure. Nothing to enumerate over |
| `m0053` | `[]` | 0 (1 `defines`) | ⛔ no |
| `m0091` | — | — | ⛔ no — `status: "unrepaired"`, never passes stage 2 |
| `m0217` | `[produce(M)]` | 1 | ✅ yes — 8 candidates, 4-situation covering set |

⚠️ **That table is itself a finding, and it is the honest cost picture.** `m0037` is a module that
passes stage 2 clean `[RAN]` (`link.py`: *no unresolved references*) and contains no logic
whatsoever. Stage 3 must report it as **`no-testable-content`** — a distinct outcome — and never as
a pass. A pipeline that reports *"3 of 4 clauses passed stage 3"* over that run is reporting that
three clauses had nothing to test.

**Re-translation budget.** A `probe-verdict` mismatch costs one further stage-1 call, priced at the
measured translation rate `[RAN]` (`m0217`: 6,926 in / 413 out = **$0.001085**). Worst case for a
four-clause run: $0.0005 + $0.001 ≈ **$0.0016**. Against the $8.50 ceiling with $2.057 used
`[RAN]` (`spend.py`), stage 3 is not a budget question at four clauses. **At 593 clauses it is
~$0.26 for labelling and ~$0.64 with one re-translation each** — still not the binding constraint;
stage 1 remains the budget.

⛔ **Nothing in this plan is authorised to spend.** Build and test offline against the committed
run outputs; a `--live` labelling run is a separate decision.

---

## 8 The TDD test list

`walkthrough/paper_pipeline/phase_1/test_probe.py`. Fixtures constructed through
`schema.validate()` + `render_lp()`, as `test_link.py` and `test_checks.py` do — **not** the
committed `.raw.txt` files, which were produced under superseded contracts.

⚠️ **The bar.** `[RAN]` `mutate_schema.py` today reports `45 killed · 0 SURVIVORS · 0 errors (of 45
guards)` and `63 of 64 tests killed by a narrow mutation are killed by exactly one`. Stage 3 ships
with its own mutation run at 0 survivors, or it does not ship. Every test below therefore names the
guard it pins **and a paired negative control that must stay SILENT** — a check that fires on
everything is pinned by nothing.

| # | the check must FIRE on | the paired control must stay SILENT on | why the control is the real test |
|---|---|---|---|
| 1 | a signature built from `inputs` only, when the module's body predicates live in the concept table (`m0217`-shaped) → **empty enumeration** is an ERROR | a module whose predicates genuinely are all in `inputs` (`m0255`-shaped) → no finding | §2. The bug is invisible because an empty enumeration reports green |
| 2 | a module whose coherent set is empty (over-constrained) → ERROR | a module with 36/128 suppressed → suppression **reported**, no error | §4. Suppression must be data, not a silent filter |
| 3 | the suppressed count appears in `probe.json` even when zero | a run with zero suppression must not acquire a warning | a warning on every run becomes invisible — `link.py`'s own recorded lesson |
| 4 | ⭐ deleting `m0217`'s only `asserts` rule → **mismatch on ≥1 situation** under the three-valued comparison | the unmutated `m0217` → 0 mismatches, `1 must-permit · 0 must-forbid · 3 silent` | §3. **This is the test the whole document exists for.** `[RAN]` the naive closure-resolved comparison gives 0 of 8 and the mutant passes |
| 5 | a report that resolves silence through the closure declaration before comparing → refused at construction | a report that carries the closure verbatim under `NOT TESTED HERE` | §3. #13 is unreachable from probes and must not look reached |
| 6 | ⭐ deleting `m0255`'s two C3 rules → **`C3: uncovered`** under discrimination coverage | the same deletion under **rule** coverage → covered, i.e. the control demonstrates the criterion that does NOT work | §6. `[RAN]` fires, `[RAN]` 0/128 verdicts change, `[RAN]` all 5 hand cases SAME |
| 7 | a situation input with no discriminating pair is NAMED in the report | an input with ≥1 discriminating pair is not named | §6. `new_material` is the live instance |
| 8 | a `forbid_body` claim counted in the coverage denominator → refused | `forbid_body` claims counted and reported **outside** the denominator | #14. A clause whose only gap is a `forbid_body` claim must not report full coverage |
| 9 | ⭐ a `probe-verdict` finding reaching `render_error_log` → withheld, hole visible | a `probe-structural` finding → **rendered in full**, because it carries no expected verdict | §5. Both halves needed: a filter that withholds everything is as wrong as one that withholds nothing |
| 10 | `probe-verdict` routed into the accumulating transcript by any path → refused | `probe-verdict` routed to re-translation with a discarded transcript → allowed | §5 ruling. Assert the **absence** of the label text in every message of the next call, as `test_repair.py` does |
| 11 | a labelling response missing a situation, or naming an unenumerated situation, or with an empty reason → **not adjudicated** | a complete labelling with reasons → adjudicated | §5, the denominator rule. A judge that skips the hard ones returns a complete-looking set |
| 12 | a seat prompt containing any predicate signature (`political_content/1`) → refused at construction | a seat prompt containing only glosses → allowed | §5. #5 (hollow stub) at the test seat |
| 13 | a seat prompt containing the module, the derived status, the closure, or the `claims` list → refused | the clause text and cross-references → allowed | §5 |
| 14 | `m0037` (zero asserts, zero acts) → outcome **`no-testable-content`** | `m0217` → outcome `passed` | §7. `no-testable-content` must never aggregate into a pass rate |
| 15 | a per-clause single-number pass rate anywhere in the output → refused | the label vector + discriminating count → allowed | §3 consequence 2. `8/8` was the whole failure |
| 16 | an `impossible` label → a `probe-structural` finding naming the situation, **no verdict** | a `must-*` label → never produces a structural finding | §4. The one label that is not a verdict is the one that may be disclosed |

⚠️ **Two of these pin things that do not exist yet and must be built in the same diff, not after:**
`DISCLOSABLE_ORIGINS` gains `probe-structural` (test 9), and `checks.SEVERITIES` is *not* extended
— `probe-structural` findings are `error`/`note` like every other. Registration, not
documentation, is what fences a module.

---

## 9 What this plan is least sure of

Written here rather than left to a reviewer to find:

⚠️ **The three-valued label set may be beyond a small seat.** `must-be-silent` asks a labeller to
distinguish *"the clause permits this"* from *"the clause does not speak to this"* — the CEPA/CNPA
distinction, at the situation level, which `STATE.md` NEW-2 records as *"real, clause-local, and
flips the verdict"* and which took a hand-encoding exercise to see at all. If the seat collapses
`silent` into `permit`, §3's failure returns in full and the check goes quiet again. **The
mitigation is a measurement, not an argument:** the first live labelling run reports the
`silent`-rate, and a rate near zero on a corpus where most clauses govern one act is a **seat
defect**, investigated as one (per the standing ruling that seat divergence defaults to a brief
defect) before any conclusion is drawn about the translations.
