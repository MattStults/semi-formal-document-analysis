# Step X — stage 3: build test cases for a translated clause, and run them

**Status: revision 3, for review. Nothing is built. This document is the plan only.**

⚠️ **Revision 2's §0 was refuted by a clean adversarial review and is withdrawn.** The new §0 says
so and states the corrected conclusion. Sections 1–9 are revision 2's, corrected: each subsection is
now marked with which half of stage 3 it belongs to, §6 gains `|R|` and the zero-rule refusal, §7
gains an enumeration cap, and §8 test 1's fire condition was wrong and is fixed.

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

## 0 ⭐ REVISION 3 — revision 2's ordering argument is WITHDRAWN

Revision 2 opened by arguing that the deterministic half of stage 3 (mutation-based discrimination
coverage) should be built **first** and the labelled-verdict half deferred behind a measurement.
**A clean adversarial review refuted that argument by running it. The refutation is accepted and the
argument is withdrawn.** Three independent grounds, each sufficient on its own:

| | revision 2 said | measured |
|---|---|---|
| **cost** | labelled verdicts must "earn their per-clause cost" | §7 of this same document measures the cost: **one labelling call for the whole four-clause run, ≈ $0.0005**, and **≈ $0.26 for all 593 clauses**. `[RAN]` `spend.py`: **$2.057 of $8.50 used, $6.44 remaining.** There is no cost to earn. §0 argued against a price §7 had already shown to be negligible |
| **a wrong data point** | `m0217`'s rule "could never fire" | It fires. §2 of this same document reports it firing in **1 of 8** situations `[RAN]`. §0 confused *"cannot fire given the providers that exist in a four-clause corpus"* with *"inert under mutation"*. So §0's "caught something twice" is **once at most** — `m0255`'s C3 |
| **the concession was far too weak** | "mutation proves a rule *matters*, never that the module is *right*" | `[RAN]` on `m0217`: deleting the rule changes **1 of 8** situations; **inverting its meaning (`permit` → `forbid`) also changes 1 of 8**. The discrimination report for the correct module and for a module that says **the opposite of the clause** is **byte-identical**:<br>`\|R\| = 1` / `rule 1: covered — 1 discriminating situation(s)` |

⇒ ⭐ **The corrected conclusion: build BOTH halves.** They fail in orthogonal directions and neither
ordering is a saving. The `m0255` C3 case argues for **stage 4d** — a claim can be encoded and
behaviourally dead, and once discrimination coverage *names* it, something has to adjudicate the
name against the clause. The `m0217` case argues for **§3's three-valued labels** — a module that is
live and wrong is invisible to mutation by construction, because the mutant of a wrong module
discriminates exactly as well as the mutant of a right one. **Neither case argues for deferral.**

### The one sentence that was not merely mis-weighted but false

Revision 2 §0 said: *"an inert rule changes no answer in any situation, by definition… verdict-based
testing cannot detect one — not ever."*

⛔ **"Not ever" is wrong. Inertness is relative to the PROJECTION.** §3 of this same document proves
the projection is a design variable, not a fact about the module: the *same* mutation of `m0217`
changes **0 of 8** situations projected to the closure-resolved verdict and **1 of 8** projected to
the derived atom `[RAN]`. Moving the projection moved the result.

⇒ The correct form, which is narrower and still enough to justify building the deterministic half:
**stage 3 projects each situation to its derived atoms, and at that granularity it cannot see a rule
that is inert. A finer projection may.**

⚠️ **One finer-projection instance, run — and it resolves a disagreement in the review.** The review
claimed `m0255` probe case D detects the dead C3 claim at *explanation* granularity via `xclingo`
(`orig 2 explanations vs mutant 1`); the reviewer's reader could not reproduce it and got identical
output. **Both are right, and the difference is one flag.** `[RAN]`, from `walkthrough/`:

```
$ .venv/bin/xclingo m0255.lp clauses/m0200.lp clauses/m0201.lp clauses/m0203.lp m0255_case_d.lp
##Total Explanations: 1        # and 1 for the C3-deleted mutant — IDENTICAL

$ .venv/bin/xclingo --output ascii-trees -n 0 0 m0255.lp clauses/m020{0,1,3}.lp m0255_case_d.lp
##Total Explanations: 2        # vs 1 for the C3-deleted mutant — DETECTED
```

xclingo's default prints **one** explanation per model, so the second explanation — *"purpose gives
no exemption: m4 is new disallowed material"*, the one the C3 rules carry — is simply not printed.
`-n 0 0` (all models, all explanations) prints it, and the mutant loses it. `[RAN]` At **derived-atom**
granularity the two are identical (1 model each, same atoms), which is why §6's mutation scan reports
`0 of 128`. ⚠️ **Two caveats before anyone builds on this:** it works only because those two rules
carry a `%!trace_rule` annotation `[READ]` (`m0255.lp:80`) — an unannotated rule is invisible to the
projection — and explanation *count* is a fragile signal, not a coverage criterion. **Recorded as an
observation, not adopted.**

### Which half each section below belongs to

Revision 2 said in one blanket sentence that *"sections 2–9 describe the labelled-verdict half"*.
⛔ **That was wrong and load-bearing**: §6 defines discrimination coverage and its report format, §7
defines the `no-testable-content` outcome, and 7 of §8's tests are deterministic-half tests. Under
revision 2's sentence the artifact to be built first had no report format, no outcome taxonomy and no
test list. Each subsection below is now marked:

| mark | half |
|---|---|
| **[D]** | **deterministic half** — enumerate, mutate, report. No model call, no labels anywhere near it |
| **[L]** | **labelled-verdict half** — a seat labels the covering set; one model call per clause |
| **[D+L]** | shared: applies to both, or defines the container both write into |

| | | |
|---|---|---|
| §1 | scope, per row: **3a**, **3b** | **[D]** |
| | **3c**, **3d** | **[L]** |
| | **3e** report | **[D+L]** |
| | failure modes **#11** (enumeration is the mechanism), **#12**, **#14** (counting and excluding), **#15** | **[D]** |
| | failure mode **#13**, and the **#5** hollow-stub note | **[L]** |
| §2 | the passing example: **3a/3b** steps | **[D]** |
| | its **3c/3d** steps | **[L]** |
| §3 | the failing example and its measurement | **[D]** — the mutation is deterministic |
| | consequence 1 (three-valued labels) | **[L]** |
| | consequences 2 (vector, not fraction) and 3 (closure `NOT TESTED HERE`), and the residual | **[D+L]** |
| §4 | enumeration, suppression, the suppressed-count ERROR | **[D]** |
| | the `impossible` label | **[L]** |
| §5 | the whole section — seat, disclosure, the re-translation ruling | **[L]**, except the `probe-structural` origin row, which is **[D]** |
| §6 | the report format, discrimination coverage, `\|R\|`, the zero-rule refusal | **[D]** |
| | the `labels:` line of `probe.json` | **[L]** |
| §7 | solver time, the enumeration cap, `no-testable-content` | **[D]** |
| | model-call pricing and the re-translation budget | **[L]** |
| §8 | tests **1, 2, 3, 6, 7, 14, 15, 17, 18, 19** | **[D]** |
| | tests **4, 5, 9, 10, 11, 12, 13, 16** | **[L]** |
| §9 | what this plan is least sure of | **[L]** |

**Build order within "both".** The deterministic half has no external dependency and its tests run
offline, so it lands first *as scheduling*, not as a gate — nothing about the labelled half waits on
a measurement from it, and revision 3 makes no claim that it should.

### ⚠️ Two departures from `03_pipeline.md`, both recorded in `STATE.md`

Recorded there rather than conditionally here, because a departure written only in the plan that
departs is not a record. See `STATE.md` → *"⭐ NEW — stage 3 plan (revision 3): two departures from
the design"*.

1. **Ordering.** Revision 3 lands on the design's own ordering (*"solver enumerates situations; model
   labels each"*, both halves), so on ordering there is now **no departure** — revision 2's proposed
   one is withdrawn. Recorded because the withdrawal is itself the fact worth carrying.
2. **§6 substitutes mutation for the design's named remedy.** Part 1 #12 names *"rule, definition and
   loop coverage over the dependency graph"*. §6 measures rule coverage **failing** on `m0255`'s C3
   (the rules fire, so rule coverage passes them; deleting them changes 0 of 128 `[RAN]`) and
   substitutes **discrimination coverage**. That is a departure with a measurement behind it, and it
   is recorded as a departure rather than described as conformance.

---

## 1 Scope — **[D+L]**, marked per row

### What stage 3 does

Given one module that has **already passed stage 2**, plus its link scope (the transitive anchor
closure of clause modules it requires):

| | | model? | half |
|---|---|---|---|
| **3a** | **Enumerate** the coherent situations over the module's *situation signature* — every assignment to its free predicates that the module's own program admits, subject to the cap (§7) | no | **[D]** |
| **3b** | **Reduce** the enumeration to a covering set under a declared coverage criterion, and **mutate** each rule to compute discrimination coverage (§6) | no | **[D]** |
| **3c** | **Label** each situation in the covering set: does the clause *require* this act be forbidden, *require* it be permitted, say *nothing* about it, or is the situation one that *cannot arise*? | ⭐ **yes — the only paid work in stage 3** | **[L]** |
| **3d** | **Run** the module against each labelled situation and compare the derived status to the label | no | **[L]** |
| **3e** | **Report** coverage, `\|R\|`, the label distribution, and every mismatch — routed by origin (§5) | no | **[D+L]** |

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

| # | | stage 3 | half |
|---|---|---|---|
| **11** | test cases describing impossible situations | ⭐ **addressed structurally** — situations are answer sets of the module itself, so a situation the module's constraints reject is never generated. **Partially:** a module that declares no constraints has nothing to reject with. §4 | **[D]** |
| **12** | testing one branch only | ⭐ **addressed, and this is the point of 3b** — coverage becomes a computed number with a named criterion, not a judgement. ⚠️ The obvious criterion (rule coverage) is **insufficient**, measured in §6 | **[D]** |
| **13** | only testing that it forbids | ⭐ **addressed by construction** — the enumeration is verdict-blind, so must-permit and must-be-silent situations appear at the same rate as must-forbid ones. ⛔ **But the global CEPA/CNPA commitment is NOT reachable from any probe**, exactly as #13 says. §3 is the demonstration | **[L]** |
| **14** | claims no test case can demonstrate | ⛔ **cannot be addressed and must not appear to be.** `forbid_body` declarations are checked by `link.py` at stage 2 by inspecting the program. Stage 3 must *count* them and exclude them from its denominator, or a clause whose only unenforced claim is a `forbid_body` claim reports full coverage | **[D]** |
| **15** | "never fired" has three causes | **addressed for two of three** — link scope separates *"waiting on an unlinked clause"* from *"genuinely dead"*. The third (*"the tests do not reach it"*) is dissolved: the solver enumerates, so there is no test-author to under-reach. ⚠️ **Dissolved only below the cap** — over `probe.max_signature` the clause is *not* enumerated at all and returns `signature-too-large` (§7), which is a refusal to answer, never an under-reach reported as a pass | **[D]** |

⚠️ **#5 (hollow stubs) arrives here in a new form and stage 3 makes it worse if built naively.** **[L]**
The situations are expressed in the translator's own coined predicate names, which echo the
document's words by construction. A labelling seat shown `political_content(x), broad_audience(x)`
grades the *names*. Mitigation in §5; it is the reason the seat is shown glosses, never signatures.

---

## 2 A specific PASSING example — **[D]** for 3a/3b, **[L]** for 3c/3d

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

## 3 ⭐ A specific FAILING example — stage 3 reports success and is wrong — **[D]** measurement, **[L]** consequence 1, **[D+L]** consequences 2–3

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

## 4 ⭐ What it looks like when the check is measuring the wrong thing (#11) — **[D]**, except the `impossible` label (**[L]**)

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

## 5 Who labels, and what they are shown — **[L]**, except the `probe-structural` origin row (**[D]**)

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

| origin | half | contains | disclosable | routes to |
|---|---|---|---|---|
| `probe-structural` | **[D]** | *"rule R is in no derivation over the covering set"*, *"claim C₃ is not discriminated by any situation"*, *"the module admits a situation the clause treats as impossible: ⟨situation⟩"*, *"the coherent set is empty"* | ⭐ **yes** — derived from the module and the solver alone, with **no expected verdict anywhere near them**, exactly as stage 2's are. Added to `DISCLOSABLE_ORIGINS` | the accumulating repair transcript |
| `probe-verdict` | **[L]** | a situation whose derived status disagrees with its label | ⛔ **no.** Withheld, leaving the visible hole `render_error_log` already emits | ⭐ **not the transcript.** §below |

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

## 6 The evidence produced, and telling "the translation is right" from "the test set was too weak" — **[D]**, except the `labels:` report line (**[L]**)

Per clause, a `probe.json`:

```
signature: k predicates · 2^k candidates · cap 2^CAP · WITHIN CAP        ← §7
|R| = n rules mutated                 ← the denominator of discrimination coverage. n = 0 is REFUSED
candidates · coherent · suppressed · covering-set size
labels: must-forbid / must-permit / must-be-silent / impossible   (counts, and the situations)   [L]
discriminating situations: n          ← the number that matters
coverage: <criterion> = k/N covered, with the uncovered items NAMED
forbid_body claims: n  (NOT TESTABLE HERE — checked by link.py, excluded from the denominator)
closure declared: produce = cepa      (NOT TESTED HERE — #13)
mismatches: [(situation, label, derived)]        ⛔ withheld from any repair prompt
```

### ⛔ `|R|` is not decoration: discrimination coverage over zero rules is a vacuous pass

`[RAN]` `m0037.lp` — from the same four-clause run this plan costs in §7 — contains **no rules at
all**: comments, a `%% concepts:` header and two `%!show_trace` directives. `link.py` passes it clean:

```
$ .venv/bin/python link.py runs/…-154618/m0037.lp
linked 1 file(s): m0037.lp
  ✅ no unresolved references          (exit 0)
```

Discrimination coverage over that module mutates nothing, finds **zero uncovered rules**, and — on
the natural formulation *"a module passes when no rule is uncovered"* — **passes**. That is
**1 of the 4 clauses** in the run this plan cites. It is the shape `STATE.md` names: *"a check whose
'pass' state is indistinguishable from its 'did not run' state is broken by design."*

⇒ ⭐ **Two requirements, and they are separate.**

1. **The report prints `|R|`, the number of rules actually mutated**, on every run, at the top, next
   to the coverage line. `0/0 covered` and `11/11 covered` must never render the same way.
2. **`|R| = 0` is REFUSED, not passed.** The outcome is `no-testable-content` (§7) — the same
   non-verdict outcome `m0037` gets for having no acts — and it never aggregates into a pass rate.
   The refusal is on `|R| = 0` **specifically**, not on the acts/asserts count, because a future
   module could carry acts and still contribute no mutable rule.

Tests 17 and 18 in §8 pin both, with controls.

⚠️ **This is the second instance in this document of the same bug.** §3's naive closure-resolved
comparison scores an emptied `m0217` at 8/8; zero-rule discrimination coverage scores `m0037` at
0-uncovered. Both halves of stage 3 have a vacuous-pass hole, and neither half's hole is patched by
the other half. That is a third argument against §0's original either/or framing.

#12 is the design's own admission that coverage is *"the problem this pipeline addressed least
well"*, and it names the remedy: *"ASP has published structure-based coverage criteria — rule,
definition and loop coverage over the dependency graph."* ⚠️ **This plan does not adopt that remedy.
It substitutes discrimination coverage, and the substitution is measured below and recorded as a
departure in `STATE.md`** — not described as conformance.

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

⛔ **And it cannot see a rule that is live and WRONG — measured, not argued.** `[RAN]` on `m0217`:
deleting the rule changes 1 of 8 situations; **inverting it (`permit` → `forbid`) also changes 1 of
8**, and this section's report renders **byte-identically** for both:

```
|R| = 1
rule 1: covered — 1 discriminating situation(s)
```

A module asserting the exact opposite of its clause scores full discrimination coverage. That is not
a gap to be closed inside §6 — it is the reason the **[L]** half exists, and it is why §0 withdraws
revision 2's proposal to defer it.

---

## 7 Cost — **[D]** solver time and the cap, **[L]** model calls

### ⛔ Solver time is NOT free, and the enumeration needs a cap

Revision 2's §0 called the deterministic half **"free"**. It is free at four clauses and it is not
free at 593. Re-measured `[RAN]` (`m0255` at link scope, 4 files, per-candidate ground+solve):

```
2^7 = 128 ground+solve cycles: 0.100 s   (0.779 ms/solve)
  2^7  =     128 solves ->     0.10 s
  2^10 =   1,024 solves ->     0.80 s
  2^14 =  16,384 solves ->    12.77 s
  2^20 = 1,048,576 solves ->  817 s   (0.23 h)
```

⚠️ **What that measures is the per-solve cost** — 128 ground-and-solve cycles over a 7-predicate
signature at `m0255`'s link scope. It is *not* a re-measurement of §4's `92 SAT / 36 UNSAT`, which is
over the module's own declared signature; a different 7 predicates gives a different SAT split and
the same ms/solve. The scaling number is **0.779 ms**.

And the enumeration is re-run **once per mutated rule**. `[RAN]` extrapolated at the measured
0.779 ms/solve: **593 clauses × ~11 rules × a 14-predicate signature ≈ 23.1 hours.** The signature is
`inputs ∪ head-less concept-table predicates` (§2), which is not bounded by anything the translator
is told to keep small.

⇒ ⭐ **A declared cap, `probe.max_signature = 10` (2^10 = 1,024 candidates)** — set so that a
worst-case clause costs 0.8 s per mutation pass and the whole 593-clause corpus stays inside
~1.5 hours `[RAN]` (593 × 11 × 1,024 × 0.779 ms ≈ 5,200 s). It is a config constant, printed in every
report, not a magic number in code.

| | |
|---|---|
| **report line** | `signature: k predicates · 2^k candidates · cap 2^10 · WITHIN CAP` — printed **always**, including when well under the cap, so the cap's absence from a report is never ambiguous |
| **outcome when over** | `signature-too-large` — a **distinct outcome**, alongside `no-testable-content`. ⛔ Not a pass, not a fail, and it **never aggregates into a pass rate**. It carries `k` and the signature itself, and routes to a human. A clause silently truncated to a sampled sub-enumeration would report coverage over a set nobody chose |
| **what it is not** | not a sampling fallback. Sampling would let `coverage: 11/11 covered` be printed over an arbitrary 1,024 of 16,384 situations, which is the "test set was too weak" failure this whole section exists to separate out |

⚠️ **The cap is a consequence of the implementation this plan describes, and `witness.lp` already
shows a better one.** The plan's 3a is a per-candidate **ground-and-solve loop**: 2^k solver
invocations. `walkthrough/witness.lp` `[READ]` expresses the same enumeration as **choice rules**, so
the solver produces every situation in **one** solve. `[RAN]`, same four files plus `witness.lp`:

```
witness.lp choice-rule enumeration: 144 models in ONE solve, 0.006 s
```

versus **0.100 s** for the 128-candidate loop — and the gap is multiplicative in 2^k, not constant.
⇒ **3a should be built in the `witness.lp` form**, which reduces the corpus cost to roughly one solve
per mutant (593 × 12 × 6 ms ≈ 43 s `[RAN]` extrapolated). The cap is still required even then,
because the covering set, the report and — if the clause reaches **[L]** — the seat prompt all scale
with the *number of situations*, not with solver time. **Choosing the implementation is not
optional-detail:** the loop form and the choice-rule form differ by ~17× on this example and the
difference decides whether the deterministic half runs in a minute or overnight.

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

⚠️ **And `m0037` is exactly the `|R| = 0` case §6 refuses.** Its `acts` list being empty is what
keeps it out of the **[L]** half; its **rule count being zero** is what would otherwise let it
*pass* the **[D]** half with `0 uncovered rules`. The two exclusions are independent and both are
required — a module could carry acts and still have no mutable rule. §6, tests 17–18.

⇒ **Stage 3's outcome set is four values, three of which are not verdicts:** `passed` · `failed` ·
`no-testable-content` (no acts, or `|R| = 0`) · `signature-too-large` (over the cap). Only the first
two may enter any aggregate.

**Re-translation budget.** A `probe-verdict` mismatch costs one further stage-1 call, priced at the
measured translation rate `[RAN]` (`m0217`: 6,926 in / 413 out = **$0.001085**). Worst case for a
four-clause run: $0.0005 + $0.001 ≈ **$0.0016**. Against the $8.50 ceiling with $2.057 used
`[RAN]` (`spend.py`), stage 3 is not a budget question at four clauses. **At 593 clauses it is
~$0.26 for labelling and ~$0.64 with one re-translation each** — still not the binding constraint;
stage 1 remains the budget.

⛔ **Nothing in this plan is authorised to spend.** Build and test offline against the committed
run outputs; a `--live` labelling run is a separate decision.

---

## 8 The TDD test list — **[D]** and **[L]**, marked per test

`walkthrough/paper_pipeline/phase_1/test_probe.py`. Fixtures constructed through
`schema.validate()` + `render_lp()`, as `test_link.py` and `test_checks.py` do — **not** the
committed `.raw.txt` files, which were produced under superseded contracts.

⚠️ **The bar.** `[RAN]` `mutate_schema.py` today reports `45 killed · 0 SURVIVORS · 0 errors (of 45
guards)` and `63 of 64 tests killed by a narrow mutation are killed by exactly one`. Stage 3 ships
with its own mutation run at 0 survivors, or it does not ship. Every test below therefore names the
guard it pins **and a paired negative control that must stay SILENT** — a check that fires on
everything is pinned by nothing.

| # | half | the check must FIRE on | the paired control must stay SILENT on | why the control is the real test |
|---|---|---|---|---|
| 1 | **[D]** | ⛔ **fire condition CORRECTED in revision 3.** A signature built from `inputs` only, when the module's body predicates live in the concept table (`m0217`-shaped) → the guard fires on **`signature == ∅`** (equivalently `\|coherent\| ≤ 1`), an ERROR | a module whose predicates genuinely are all in `inputs` (`m0255`-shaped) → no finding | §2. ⚠️ Revision 2 wrote the condition as `\|enumeration\| == 0`. **That guard never fires on the bug it names:** an empty signature yields `2^0 = 1` situation `[RAN]`, not zero, so the `inputs`-only build of `m0217` sails past it reporting one all-false situation and *green*. The bug is invisible precisely because the empty enumeration is not empty |
| 2 | **[D]** | a module whose coherent set is empty (over-constrained) → ERROR | a module with 36/128 suppressed → suppression **reported**, no error | §4. Suppression must be data, not a silent filter |
| 3 | **[D]** | the suppressed count appears in `probe.json` even when zero | a run with zero suppression must not acquire a warning | a warning on every run becomes invisible — `link.py`'s own recorded lesson |
| 4 | **[L]** | ⭐ deleting `m0217`'s only `asserts` rule → **mismatch on ≥1 situation** under the three-valued comparison | the unmutated `m0217` → 0 mismatches, `1 must-permit · 0 must-forbid · 3 silent` | §3. **This is the test the whole document exists for.** `[RAN]` the naive closure-resolved comparison gives 0 of 8 and the mutant passes |
| 5 | **[L]** | a report that resolves silence through the closure declaration before comparing → refused at construction | a report that carries the closure verbatim under `NOT TESTED HERE` | §3. #13 is unreachable from probes and must not look reached |
| 6 | **[D]** | ⭐ deleting `m0255`'s two C3 rules → **`C3: uncovered`** under discrimination coverage | the same deletion under **rule** coverage → covered, i.e. the control demonstrates the criterion that does NOT work | §6. `[RAN]` fires, `[RAN]` 0/128 verdicts change, `[RAN]` all 5 hand cases SAME |
| 7 | **[D]** | a situation input with no discriminating pair is NAMED in the report | an input with ≥1 discriminating pair is not named | §6. `new_material` is the live instance |
| 8 | **[L]** | a `forbid_body` claim counted in the coverage denominator → refused | `forbid_body` claims counted and reported **outside** the denominator | #14. A clause whose only gap is a `forbid_body` claim must not report full coverage |
| 9 | **[L]** | ⭐ a `probe-verdict` finding reaching `render_error_log` → withheld, hole visible | a `probe-structural` finding → **rendered in full**, because it carries no expected verdict | §5. Both halves needed: a filter that withholds everything is as wrong as one that withholds nothing |
| 10 | **[L]** | `probe-verdict` routed into the accumulating transcript by any path → refused | `probe-verdict` routed to re-translation with a discarded transcript → allowed | §5 ruling. Assert the **absence** of the label text in every message of the next call, as `test_repair.py` does |
| 11 | **[L]** | a labelling response missing a situation, or naming an unenumerated situation, or with an empty reason → **not adjudicated** | a complete labelling with reasons → adjudicated | §5, the denominator rule. A judge that skips the hard ones returns a complete-looking set |
| 12 | **[L]** | a seat prompt containing any predicate signature (`political_content/1`) → refused at construction | a seat prompt containing only glosses → allowed | §5. #5 (hollow stub) at the test seat |
| 13 | **[L]** | a seat prompt containing the module, the derived status, the closure, or the `claims` list → refused | the clause text and cross-references → allowed | §5 |
| 14 | **[D]** | `m0037` (zero asserts, zero acts) → outcome **`no-testable-content`** | `m0217` → outcome `passed` | §7. `no-testable-content` must never aggregate into a pass rate |
| 15 | **[D]** | a per-clause single-number pass rate anywhere in the output → refused | the label vector + discriminating count → allowed | §3 consequence 2. `8/8` was the whole failure |
| 16 | **[L]** | an `impossible` label → a `probe-structural` finding naming the situation, **no verdict** | a `must-*` label → never produces a structural finding | §4. The one label that is not a verdict is the one that may be disclosed |
| 17 | **[D]** | ⭐ `m0037` (**`\|R\| = 0`**, no rules to mutate) reaching discrimination coverage → outcome **`no-testable-content`**, REFUSED | `m0217` (`\|R\| = 1`) → coverage computed, outcome `passed` | §6. `[RAN]` `m0037.lp` has zero rules and `link.py` passes it clean; `0 uncovered of 0` is a vacuous pass on **1 of the 4** clauses in the cited run. Refusal must key on `\|R\|`, **not** on the empty `acts` list — test 14 already covers that path and they must not collapse |
| 18 | **[D]** | a coverage report rendered without `\|R\|` → refused at construction | a report carrying `\|R\| = n` next to the coverage line → allowed | §6. The control is the real test: `0/0 covered` and `11/11 covered` must not render the same, and only `\|R\|` separates them |
| 19 | **[D]** | a signature of `k > probe.max_signature` → outcome **`signature-too-large`**, carrying `k`; and **no** truncated or sampled enumeration is produced | a signature at exactly `k = probe.max_signature` → enumerated normally, `WITHIN CAP` printed | §7. `[RAN]` 0.779 ms/solve → 2^14 is 12.8 s per pass and ~23 h over the corpus. The control pins that the cap prints on **every** report, not only when exceeded — a cap visible only on failure is indistinguishable from no cap |

⚠️ **Three of these pin things that do not exist yet and must be built in the same diff, not after:**
`DISCLOSABLE_ORIGINS` gains `probe-structural` (test 9), and `checks.SEVERITIES` is *not* extended
— `probe-structural` findings are `error`/`note` like every other; and the outcome enum gains
**`signature-too-large`** alongside `no-testable-content` (tests 17, 19), with both registered as
non-aggregating at the point the pass rate is computed. Registration, not documentation, is what
fences a module.

⚠️ **Tests 1, 17, 18 and 19 are all revision-3 additions or corrections, and three of the four are
the same failure shape:** a guard whose passing state is indistinguishable from its not-having-run
state. Revision 2 contained one such guard (test 1) and two such holes (`|R| = 0`, no cap).

---

## 9 What this plan is least sure of — **[L]** for the first item, **[D]** for the second

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

⚠️ **[D] `probe.max_signature = 10` is set from a cost model, not from the corpus.** The signature is
`inputs ∪ head-less concept-table predicates` (§2) and **nobody has measured its distribution over
593 clauses** — only 4 clauses have been translated, one of which reaches stage 3 with `k = 3`
`[RAN]`. If real signatures cluster at 12–16, the cap turns into a `signature-too-large` outcome on a
large fraction of the corpus and the criterion silently stops covering the document. ⇒ **The first
corpus-scale run reports the `k` histogram before anything is concluded from a coverage number**, and
the cap is re-set from that histogram rather than defended. The failure this guards against is a
coverage report that is honest per clause and unrepresentative in aggregate.

⚠️ **What revision 3 is no longer unsure of:** revision 2 listed the build ordering as an open
question and answered it with an argument. §0 replaces the argument with three measurements and the
answer is *both halves*. That is settled, not deferred.
