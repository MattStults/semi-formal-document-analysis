# Questions waiting on Matt

**Maintained by the autonomous run. Everything here BLOCKED work; everything else continued.**
Newest first. Each entry says what is blocked, what I did instead, and what a decision costs.

## ⛔ ONE ACTION NEEDED BEFORE ANY FURTHER COMMIT TOUCHING A WATCHED FILE

```
semi-formal-experiment/.venv/bin/python walkthrough/model/guard.py --accept paper_pipeline/phase_1/schema.py
```

`schema.py` moved twice after you accepted it, both times to **restore or complete a guard**, and
both on evidence: the anonymous-variable rejection (`b7c663e` — xclingo dies on `_` in a body, so my
earlier withdrawal was wrong) and the internal-full-stop rejection (`f8f83ed` — a body carrying a
second statement was having two thirds of itself silently dropped). Nothing was relaxed.

---

⚠️ **Nothing here was decided unilaterally.** Where a design question arose I recorded it and
worked around it. Where a design ruling already existed I followed it, even where I would have
chosen differently — that is the standing instruction.

---

## Q-21 ⛔ THE RENDERER SUBSTITUTES AN INSTANCE GLOSS FOR A VARIABLE — Invariant 1, live

Found while checking something a subagent flagged in passing. **Not a design question — a defect —
and it is being fixed. Recorded because of what it says about the check set.**

`m0014`'s rule body is `critical_high_severity_harm(H)` — a **variable**, ranging over six ontology
instances (acts of violence, WMD, terrorism, child abuse, persecution, mass surveillance).

| | |
|---|---|
| the CONCEPT's gloss | *"a harm that is critical and high severity, as enumerated in the clause"* |
| **what the seat is shown** | *"clause m0014 forbids ⟨act facilitate(H)⟩ when «**mass surveillance** is a critical high severity harm»"* |

⇒ The renderer picked **one arbitrary instance's** gloss for a universally-quantified variable. A
seat judging *"does the clause support this?"* is shown a rule about mass surveillance when the
actual rule covers all six — and it reads perfectly fluently.

⛔ **RB1 through RB5 all PASS on it.** No label survives; every body predicate has *a* gloss present
(an instance gloss is a gloss); polarity is right; the rendered set is non-empty. **Every check is
green on a sentence that says something the module does not.**

That is the failure the read-back exists to prevent, occurring inside the read-back, and undetected
by the five checks written to detect exactly this class. The lesson for the check set is worth more
than the bug: **RB2 asks whether *a* gloss is present, never whether it is the *right* gloss.**

⚠️ It would defeat 4b/4c the same way it defeats RB2 — except that here the new instrument check
helps: 4c sees the module's variable, 4b sees the instance sentence, so they disagree and the
rendering is correctly accused. The check works; the bug is upstream of it.

---

## Q-20 ✅ RULED — artifact versioning and the re-run strategy

**Matt, 2026-08-08:** *"It should probably trigger a re-run. If there's an intention flag that would
make sense for a partial re-run we could respect that."*

⛔ **This was under-tracked and that is my failure, not a design gap.** The two hash functions have
existed since the graveyard landed, but `[RAN]` they are called **only when writing a graveyard
entry** — metadata on a FAILURE record. Zero occurrences across every `run.json` and `m*.json`.
Nothing compared a stored hash to a current one; nothing selected clauses for re-translation. The
strategy did not exist, and it appeared nowhere in this file despite 19 other entries being here.

**The ruling, now being implemented:**

| hash | covers | on a change |
|---|---|---|
| `contract_hash` | clause text + schema source | the artifact **may no longer validate** ⇒ re-translate, not optional |
| `provenance_hash` | prompt + model + params | ⭐ **also re-runs**, per this ruling |

⚠️ **The two stay separate even though both now re-run**, because they answer different questions: a
module whose `provenance_hash` moved is still **valid** and still links — it simply cannot be cited
as evidence about the current prompt. Collapsing them marks the whole corpus stale on every prompt
edit, which makes iteration impossible. `graveyard.py`'s docstring already carries that argument.

**Rejected by name** (to be written into `03_pipeline.md` with the ruling): *"one hash for
everything"*, and *"a provenance change only relabels, never re-runs"* — the latter considered and
rejected by Matt today.

**The intention flag is the part to watch.** It is the mechanism by which someone makes 593 stale
modules not-stale with one word, so it is being designed to be hard to use carelessly, to leave a
record, and to be **incapable of excusing a `contract_hash` change**.

---

## Q-19 ⛔ §6's DIVERGENCE MACHINERY CAN NEVER FIRE — and the design, not the code, is why

`[RAN]` **0 divergence records over all 81 legal verdict combinations.** Every seat's verdict
vocabulary is disjoint from every other's:

| seat | verdicts |
|---|---|
| 4a | `as-meant` · `not-as-meant` · `unclear` |
| 4b | `faithful` · `unfaithful` · `unclear` |
| 4c | `licensed` · `unlicensed` · `unclear` |
| 4d | `covered` · `not-conveyed` · `unclear` |

…and **every pair in `CONTRADICTIONS` sits inside a single seat's vocabulary.** So `seat-divergence`,
the brief shas, `promote`, `Triage` and `report_line`'s NOT-ADJUDICATED branch are all unreachable,
and the five tests pinning §6 build judgements `validate_judgements` refuses.

⚠️ **The code implements the design literally.** §6 says *"when two seats reach opposite verdicts on
one item"* — and its own worked example is *"only `faithful` vs `unfaithful`"*, **both 4b's**. The
design describes a cross-seat mechanism using a within-seat pair.

**The question is what "opposite" means across seats**, and it is genuinely yours:
1. **Shared vocabulary** — seats answer the same question, so verdicts are comparable. Changes every
   seat brief.
2. **A tension table** — `4b: faithful` against `4c: unlicensed` is not literally opposite but is in
   tension. Needs the pairs enumerated and justified.
3. **§6 applies only within a seat** — two labellings of one item by one brief. Cheapest, and much
   weaker than §6 reads.

⛔ **This matters more than its size suggests.** §4.3's whole guard is that *unanimity must not read
as confirmation*, and §6 is the mechanism that makes disagreement visible. If it cannot fire, four
agreeing seats are the only possible outcome — which is the failure §4 is written to prevent.

---

## Q-18 · Stage 0's competency check has 2 unexpected failures — red, and correctly loud

`walkthrough/paper_pipeline/cq_check.py` reports **14 as declared, 2 unexpected, 2 blocked**.
CQ-6.a and CQ-6.b fail against their written-first expectations. Pre-existing, unrelated to today's
work, and outside the stage 1–4 scope I was given — recorded so it is not lost.

⚠️ **A correction worth reading, because two of us got it wrong in the same way.** A subagent
reported *"the tool exits 0 anyway, so stage 0's competency check is red and quiet"*, and I nearly
filed that as a defect. It is false: `[RAN]` `cq_check.py` exits **1**. Both measurements had been
taken through a shell pipe, where `$?` reports `tail`'s status and not the program's.

⇒ The check is red and **loud**. Nothing needs fixing in its signalling; what needs attention is the
two failures themselves, which is a stage-0 question.

⭐ The general lesson is worth more than the finding: **`cmd | tail` silently discards the exit
code**, and this repo's whole discipline is that a check must not be able to look like it passed.
Two independent agents produced the same false "exits 0" claim from that one habit.

---

## Q-16 ✅ RESOLVED — stage 4's R3 layer is built and wired

`STEP_stage4.md` §2.1 specifies **three** rendering layers. `readback.py` produces **R1 and R2
only**. R3 — *"xclingo explanation tree, every leaf replaced by its R1 rendering"* — is absent, so
**no derivation reaches any seat**, and 4a/4b's denominators are smaller than §2.1 describes.

⭐ **DONE 2026-08-08.** `readback_r3.py` (36 tests, 21 mutants / 0 survivors) composes a
`%!trace_rule` mechanically from the module's own glosses, runs xclingo once per derived verdict
atom, and replaces every leaf with its R1 rendering. Wired into 4a and 4b, which §5.1 specifies as
*"the rendered set (R1+R2+R3)"* — so the design answered the "fifth denominator?" question and no
decision was needed.

`[RAN]` **8 of 18 covering-set situations derive a verdict** across the stored modules. The other 10
are excluded **by name** as `no-derivation`, never dropped — dropping them would overstate 4a's
coverage by more than a third.

⚠️ **Two defects it found on live material, both Invariant 1 violations reaching seat-facing text:**
the ablation guard `o` surfaced as an unglossed leaf of every ontology-backed derivation, and a raw
ASP atom (`asserts(m0079,oblige,produce_response)`) reached the rendered sentence because xclingo
joins two labels with `;` and the payload was read as one quoted string.

**Still unsigned:** R3 is not gated on the probe outcome — `m0134`'s probe outcome is `failed` and
R3 renders it anyway. Arguably right, since the derivation is still real evidence, but nobody has
ruled.

⚠️ It is also the reason the anonymous-variable guard matters (see `b7c663e`): R3 is the layer that
xclingo actually drives, so a `_` anywhere in the link set would take the whole tree down.

---

## Q-17 · 4c's independence is compromised by gating, not by design

`plan_clause` refuses a clause whose read-back failed, so **4c never runs for the 7
`readback-ungloss` modules**. §4.1's anchor property is that 4c is independent of the rendering —
and it is provably independent of a *wrong* rendering (a test asserts 4c is never stamped), but not
of a *missing* one.

⇒ The seat designed to be the check on the shared artifact is switched off exactly when that
artifact fails. **Worth a ruling**, and I did not change the gating.

---

## Q-14 · The design contradicts its own grounds for disclosing an `impossible` label

The spec-drift review filed this as a leak (A2, "CODE should change"). **I checked and the reviewer
is wrong about the remedy** — but right that something is inconsistent.

`STEP_stage3.md:331` **explicitly rules**: *"`impossible` is a label the seat may return, and it is
the only label that is not a verdict… which is why it is **disclosable**"*. §8 item 16 is a TDD test
for precisely that behaviour, and `:385` lists the finding text under `probe-structural`.

⇒ **The code follows the design.** I did not change it.

⚠️ **But `:385`'s stated GROUND is false of it**: *"derived from the module and the solver alone,
with no expected verdict anywhere near them."* An `impossible` label is a **seat output**, not
solver-derived. The ruling may well be right — an `impossible` finding names a situation and no
status — but it is right for a different reason than the one written down.

**What a decision costs:** one sentence in `:385` distinguishing *"carries no expected verdict"*
(true, and the real ground) from *"was not produced by a model"* (false). ⛔ It is a design edit to
a watched file, so I left it.

---

## Q-15 · Review findings I did NOT act on, and why

Both adversarial reviews landed (`SPEC_DRIFT_REVIEW_2026-08-07.md`, `ENGINEERING_REVIEW_2026-08-07b.md`).
Two HIGH findings are **fixed** (the silent content drop, and the anonymous-variable guard I
withdrew on the wrong tool). These remain, each because acting would be a design decision:

- **RB1's act exemption** (`readback.py`) grants a second exception where `STEP_stage4.md:415`
  grants one. 19 of 19 `asserts` renderings show a bare functor. The reviewer's view is "a hole, not
  a limit"; mine is that it cannot be closed without a schema field for an act gloss — which is
  **Q-7**. Same question, two symptoms.
- **RB4 is structurally blind to layer-1 content.** Revision 2 weakened a check while stating it
  amended only §2.3. Latent today at 0/106 layer-1 items, live as soon as any module uses a
  construct with no template.
- **`readback.Finding` has no `origin`**, so `readback-structural` cannot be registered in
  `DISCLOSABLE_ORIGINS` as §5.5 requires "in the same diff". This is the leak perimeter's
  registration rule, and it is currently unsatisfiable for stage 4.
- **§8 requires stage 4 to ship a mutation run at 0 survivors**, but `mutate_schema.py` deletes
  `ast.Raise` nodes and `readback.py` has **none** by design. ⭐ The reviewer's judgement, which I
  share: **do not weaken the bar — write the right instrument.** The reviewer hand-wrote 15 mutants
  and killed 12; the 3 survivors are real gaps.

---

## Q-10 ⭐ THE LABELLED HALF FOUND A LIVE TRANSLATION DEFECT THE DETERMINISTIC HALF SCORED CLEAN

**This is the result that justifies building the `[L]` half at all, and it needs your adjudication.**

`m0150`: the deterministic half scores it **`passed`, |R| = 5, coverage 5/5** — a clean sheet. The
seat labels situations S5 and S9 `must-be-silent`. The module asserts `prefer make_tool_call` in
both, **because its rules never require a tool call to be under consideration**.

⇒ The rule fires in situations the clause does not speak to. `[D]` cannot see this **by
construction** — mutation coverage asks whether deleting a rule changes an outcome, and this rule
does change outcomes; it changes them in the wrong situations.

⛔ **`CLAUDE.md` requires every flip to be adjudicated against the document, with label values
nowhere in the room. I have not done that** — it is a judgement about what clause m0150 says, which
is yours. The seat's reason and the situations are in `RESULT_stage3_labelled_live.md`.

⚠️ One caveat that cuts the other way: the seat's errors on `m0217` all run in **one direction** —
over-reaching past the clause's trigger. If that is the seat's bias rather than the module's defect,
S5/S9 could be the same over-reach. That is exactly why this needs a human and not me.

---

## Q-11 · `render_situation` is defective at k = 1, and it cost the run its only forbid-side module

With a single fact line the seat reads the fact **as the situation id**, `adjudicate` refuses, and
`m0014` returned 6 refusals from 6 calls. The guard behaved correctly — a refusal, not a partial
pass — but the rendering is wrong, and the run therefore has **no forbid-side / `cnpa` coverage at
all**.

**Not fixed:** the fix changes what the seat is shown, which `STEP_stage3.md` §5 specifies row by
row. That is a design edit.

---

## Q-12 · The label set has no answer for `oblige` or `prefer`

Four of twelve mismatches are this artefact, not disagreement. The three-valued set
(`must-forbid` / `must-permit` / `must-be-silent`) covers the forbid/permit axis; the closed status
set is **four** values. A seat with no way to say "the clause requires this" must answer with one of
the three it has.

**What a decision costs:** either a fourth and fifth label (changing §5's brief and every stored
labelling), or an explicit ruling that `oblige`/`prefer` rules are out of scope for stage 3 and
excluded from the denominator by name.

---

## Q-13 · The seat is NOT validated, and the standing ruling names the test that would do it

`CLAUDE.md`: *"the adjudication seat is proven at small-model/frontier parity, and divergence from a
frontier model on the same brief is a seat defect, not a model failure."*

That test has **not been run**. There was no ground truth in this run, so "working" currently means
only *"did not exhibit the failure §9 named"*. The actual validation is a frontier model on the
identical brief over the identical 23 cells — **≈ $0.20**.

**I did not run it:** it is the validation the ruling requires, and Q-10's adjudication depends on
knowing whether the seat over-reaches. Say the word and it is twenty minutes.

---

## Q-6 ⛔ REFRAMED 2026-08-08 — it is a STAGE-1 CONTRACT gap, not a stage-4 threshold

**Superseded reading:** *"is `readback-ungloss` too strict?"* ⇒ **No. It is correct, and relaxing it
would have been the wrong fix.** 7 of 19 stored modules are blocked, and the cause is upstream.

**What is actually wrong.** `[RAN]` 14 distinct symbols block those modules, and **not one is
glossed by any module we have translated**. Every one is a predicate a module *uses in a body* and
declares in `requires` or `inputs`. The contract demands a gloss for `concepts` — the names a clause
**introduces** — and demands nothing for the names a clause **borrows**.

⇒ **So the accumulation the design assumes has no source.** `concepts.json` is the union of
`concepts` blocks; a borrowed symbol never appears in one.

### ⛔ And `DEFERRED.md` D-3's escape clause is half wrong

D-3 defers corpus-wide resolution on the ground that it *"resolves itself as the corpus grows."*
`[RAN]`, classifying all 14 against the document:

| | n | |
|---|---|---|
| a clause plausibly **owns** it | 6 | `disallowed`, `new_material`, `out_of_scope`, `task`, `includes_malicious_instructions`, `translation_of_user_content` |
| barely mentioned | 2 | `conflicts_with_higher_authority`, `not_read_carefully` |
| ⛔ **appears NOWHERE in the document** | **6** | `policy_class`, `pasted_text`, `interactable_entity`, `interaction_entity`, `delegated_authority_to_webpage`, `conflicts_with_later_same_authority` |

**Growth resolves 6 of 14 and can never resolve 6**, because the model coined names whose words
appear in no clause at all. ⚠️ `m0053` invented **`interactable_entity` AND `interaction_entity`**
for one idea and glossed neither — two spellings, one clause, no other clause to point at.

### Can linking find the definitions without re-reading the source?

`[RAN]` **Probably not.** None of the five blocking clauses carries a single markdown anchor, and
corpus-wide only **77 of 593 (13%)** carry any. The document's cross-reference structure is mostly
implicit, so the only information a module carries about a borrowed symbol is **name + arity** — and
name-matching is measured at **20% wrong** (46 of 228 reused names carry conflicting definitions).

### ⇒ The real question, and it is Invariant 1's open arm

Either a clause glosses every symbol it uses — which **manufactures problem #9 at source**, since
the borrower invents a meaning for a term another clause owns — or something resolves symbols across
modules. That is Invariant 1's undecided A/B/C choice, and **open question 2's "run both arms on the
same clauses" is currently unrunnable, because neither arm has a dictionary.**

⭐ **Matt's proposal, 2026-08-08:** a pre-translation pass mapping concepts to input/output names
across the whole document, statically checked, supplied per section. That is **arm A** in delivery —
but the recorded objection to A is about feeding a model *its own accumulated output*, and a
document-derived, statically-checked vocabulary is a materially different artifact. It is also the
**lookup arm C requires and lacks**, so building it makes the A/B/C comparison possible rather than
pre-empting it. A one-off experiment is being run before any design is written.

### ⛔ THE EXPERIMENTS ARE DONE, AND THEY CONSTRAIN THE ANSWER — 2026-08-08

Six experiments in `resolve_runs/ITERATION_LOG.md`. The ones that bear on the decision:

| | `[RAN]` |
|---|---|
| can a concept map **predict** the names a translator will coin? | **1 of 32**, then **0 of 32** with 268 candidates on the table |
| asked **concept-level** instead of name-level, can a model say where a borrowed concept is established? | **4 of 4** — the framing was the problem, not the model |
| do five runs **formalizing** the same concept agree on vocabulary? | agreement **0.06**; 27 of 51 borrowed names appear in exactly **one** run |
| ⭐ does **iterating to self-sufficiency** fix that? | agreement **0.00** on all 8 concepts; **0** rule shapes shared by ≥3 of 5 runs for 6 of 8 concepts |

⚠️ **The runs are individually good** — 89% of passages verbatim, clingo accepts 94%, only 1 of 40
faked closure. Five careful, document-grounded definitions that do not overlap. This is not a
capability result and cannot be fixed by a better model or a longer prompt.

⭐ **The one thing that DOES converge is the document's own `**Term**:` inventory.** Every name five
independent runs agree on is either a name we handed them or a term the document names outright.

⇒ **What is now decidable, and it is Matt's call:**

- **arm C is buildable only over the document's own named terms**, and must then *refuse* rather
  than guess for everything else. That is a much smaller lookup than the design assumes, and it
  leaves the 6 symbols that appear nowhere in the document permanently unresolvable — which is a
  true statement about those symbols, not a gap in the lookup.
- **or arm C is abandoned** and stage 1 changes its contract so a clause must gloss what it
  borrows — accepting problem #9 at source, now with a measured price: **20%** of reused names
  already carry conflicting definitions.

⛔ **Neither is chosen here.** What the experiments remove is the option of assuming the lookup can
be generated; it cannot, and that was the only unmeasured premise in arm C.

---

## Q-22 ⛔ DEFECT — an UNSATISFIED `requires` is silently false, not an error

⚠️ **CORRECTED 2026-08-09, same day, after reading the modules instead of the signature rule.** The
first version of this entry said the stage-1 contract had a hole and that borrowed predicates were
undeclared. **That was wrong and the correction matters, because it moves the fix.**

`[RAN]` **Every orphan IS declared**, in `requires`:

```
m0079  requires: ['conflicts_with_higher_authority/1', 'conflicts_with_later_same_authority/1']
m0255  requires: ['policy_class/2', 'scope/2', 'out_of_scope/2']
m0105  requires: ['pasted_text/1', 'not_read_carefully/1', 'includes_malicious_instructions/1', ...]
```

`schema.py`'s D4b check — *"body references `X` but nothing declares it"* — passed **correctly**. The
model did its job. `requires` means *"another clause must define it"*, `inputs` means *"supplied with
the case"*, and the model separated them sensibly.

⛔ **The defect is that `probe.situation_signature` reads `inputs` and ignores `requires` entirely.**
A `requires` predicate is therefore: correctly declared, not in the signature, and — at `[RAN]` **13
of 593 clauses translated** — not defined by any link either. So it is **silently false in every
enumerated situation**.

**Found 2026-08-09, while answering Matt's "are we off track?".** It is the answer.

⭐ **AND THE DESIGN DEFERRED THIS ON PURPOSE.** `schema.py` says so in the check itself: *"Only
whether the declaration finds a PROVIDER corpus-wide is link scope. Whether it also finds a
DEFINITION somewhere in the corpus is a question for link time, once enough clauses exist to answer
it."* ⇒ **The hole is a deferred check that was never implemented at link time.** An unsatisfiable
promise is currently indistinguishable from a kept one.

### What it does, on a real committed module `[RAN]`

`m0079` references `conflicts_with_higher_authority/1` in a rule body. It is head-less, absent from
`inputs`, and absent from the concept table — which declares the *differently named*
`higher_authority_conflict/1`.

```
applicable_instruction(I) :- o, instruction(I), not higher_authority_conflict(I),
                                                not later_same_authority_conflict(I).
higher_authority_conflict(I) :- o, instruction(I), conflicts_with_higher_authority(I).
```

⇒ `conflicts_with_higher_authority(I)` can never be true
⇒ `higher_authority_conflict(I)` can never be true
⇒ `not higher_authority_conflict(I)` is **always** true
⇒ ⛔ **the module collapses to "every instruction is applicable"**, and the clause's entire content
— instructions being superseded by higher authority — is **inert**.

**The probe reads green**, because the predicate is not in the signature, so no enumerated situation
ever toggles it and nothing can test the dead branch.

### Scale `[RAN]`

| | n |
|---|---|
| modules examined | 19 |
| ⛔ with a referenced, head-less predicate **missing from the signature** | **6 (32%)** |
| of those, the orphan gates a **negated** literal — always-true branch, WRONG output | 1 |
| the rest are positive-only — the rule **never fires**, MISSING output | 5 |

Both are silent. `m0255` loses `out_of_scope/2`, `policy_class/2`, `scope/2`; `m0105` loses four;
`m0134` loses `task/1`; `m0150` loses `translation_of_user_content/1`.

### ⭐ Why this reframes the whole resolution line

Satisfying a required input has **three** discharge routes, and every experiment in
`resolve_runs/` pursued only the second:

| | route | what it needs | status |
|---|---|---|---|
| 1 | **declare it as a situation input** — stage 3 toggles it true and false | nothing. Mechanical. **No document, no model** | ⛔ **THE MISSING ONE. 32% of modules fail here** |
| 2 | another module derives it | cross-module symbol identity | `[RAN]` names cannot do it (**0.00** across repeat translations); extension is the only stable key (**97%**) |
| 3 | genuinely undischargeable — `contradicts/2`, `makes_irrelevant/2` | must become an **explicit open input**, never silence | the one thing 5 of 5 iterative runs agreed on |

⇒ **A predicate does not need a meaning to be satisfied. It needs to be DECLARED.** The resolution
work was not wrong, it was **premature** — it answers route 2, which only matters once route 1 holds.

### Two candidate fixes, neither chosen

- **(i) widen the signature rule** — include every referenced head-less predicate, declared or not.
  ⚠️ `max_signature` is 10 (2^10 candidates ≈ 0.8 s); `m0105` alone would add four, so this needs a
  measured look at signature growth before it is safe.
- **(ii) widen the stage-1 contract** — require a clause to declare every symbol it borrows. This is
  Q-6's original question, and it manufactures problem #9 at source.

⛔ **Independent of which:** a referenced head-less predicate reaching neither route must be a **hard
error**, not a silent drop. That is the anti-cheat perimeter shape used everywhere else in this
repo, and its absence here is why a module can delete its own clause and pass.

---

## Q-7 · `STEP_stage4.md` §2.3's `act/1` template cannot be implemented as written

It renders `produce(M)` as *"producing the material"*. But `[RAN]` **no module in the corpus
declares a concept for its own act functor**, nothing in the schema glosses an act, and turning
`produce` into "producing" plus reading `M` as "the material" needs knowledge no artifact carries.

**What was done instead:** the act renders as itself inside `⟨act produce(M)⟩` with a
`readback-act-literal` note, and only that marked span is exempt from RB1. Without the exemption
RB1 fires whenever an act functor is also a declared input.

**What a decision costs:** doing it properly needs a **new schema field** (an act gloss). That is a
contract change, so it was not made. Cheap to add if you want it.

---

## Q-8 · Two prompt sites still teach the disproved `_` ground

`prompt/00_task.md:70-71` and `prompt/30_failure_modes.md:20` both tell the model *"the explanation
tooling cannot process `_`"*. That ground is now disproved and the schema gate is gone.

⚠️ **Consequence, stated plainly: until these are edited the model still will not write `_`, so the
schema change alone buys nothing at the prompt level.**

**Not edited, deliberately.** Both are watched transcriptions; the failure-mode list is a numbered
transcription of `03_pipeline.md` Part 1 whose count `translate.py --self-test` asserts, it is
mirrored in three `eval_arms/` copies, and `DEBUGGING_TIPS.md` §10 requires a held-out measurement
and a review for any prompt change. Removing a schema *gate* is what "no restrictions" means
mechanically; changing what we *teach* is a prompt change with its own process.

---

## Q-9 · RB1 as specified fires on ordinary English inside glosses

`[RAN]` RB1 ("no predicate label survives into the English") fired on 9 of 14 modules, 34 findings —
but **18 of the 34 are single-word predicate names like `task`, `user`, `instruction`, `assistant`
occurring as ordinary English inside a gloss**, not as a leaked label.

The renderer now distinguishes renderer-emitted from gloss-internal in each finding, because
collapsing them would point every repair at the renderer when the majority are about the gloss.
Whether gloss-internal occurrences should be a finding at all is a design question.

---

## Q-1 · Stage 5+ have no design at all

**Blocked:** anything past stage 4. `03_pipeline.md` describes stages 1–9, but only 1–4 have STEP
documents. Stages 5–9 have no plan, no failing example, and no cost model.

**What I did instead:** wrote *initial* designs for the next undesigned components as drafts marked
`DRAFT — NOT REVIEWED`, following the STEP format (a passing example, a failing example, evidence
produced, cost). They are proposals for you to review, not decisions.

**What a decision costs:** reading one STEP draft is ~15 minutes. Implementing against an
unreviewed design risks the thing this project already paid for twice — building a check that
measures the wrong thing and reports success.

---

## Q-2 · The `[L]` half of stage 3 has never been run against a real model

**Status: UNBLOCKED — you authorised the spend before going AFK ("Feel free to spend on the [L]
run"), so I am running it.** Recorded here because the RESULT may need your ruling.

`STEP_stage3.md` §9 says two measurements must exist before any coverage number is believed:
- the **`silent`-rate**. A rate near zero on a corpus where most clauses govern one act is a **seat
  defect**, to be investigated as one — not a conclusion about the translations.
- the **`k` histogram**, from which `probe.max_signature` must be re-set. It is currently 10, from a
  cost model, and nobody has measured the real distribution.

**What needs you afterwards:** if the `silent`-rate comes back near zero, §9 says that is a brief
defect. Rewriting a seat brief is a design change, so I will report and not act.

---

## Q-3 · Stage 4's four seats need spend, and the amount is not yet estimable

**Blocked:** running stage 4 end to end.

Four review seats per clause, over a corpus of 593. The renderer is being built now; until it
exists I cannot count the items each seat must read, so I cannot price it. The project cap is
$8.50 with roughly $2.5 used.

⭐ **ANSWERED 2026-08-08 — `seats.py --cost`, computed from the real rendered artifact, free:**

| | total (7 clauses) | per clause |
|---|---|---|
| **WORST, flash** | **$0.0360** | $0.0051 |
| WORST, frontier | $3.5782 | $0.5112 |
| likely, flash | $0.0063 | $0.0009 |
| likely, frontier | $0.3979 | $0.0568 |

⚠️ **WORST is the number a budget decision uses** — every reply at its 4096-token cap, which is what
dominates the frontier figure. `likely` assumes 40 output tokens per judgement and is an
**assumption**: nothing has run, so no reply length has been measured.

⇒ **On the configured flash model a full stage-4 run over everything that can reach a seat costs
about four cents.** That is inside any reasonable ceiling. On a frontier model it is $3.58, which is
42% of the entire remaining project budget.

⛔ **AT CORPUS SCALE THE FRONTIER NUMBER IS DISQUALIFYING, and the first estimate understated it.**
`STEP_stage4.md` §7 said roughly $25 for 593 clauses. Measured: **$303 worst / $33.7 likely** at the
hard-coded `(5.0, 30.0)` frontier price — and once the code reads the *real* maximum in
`providers.json` (`fable`, `10/50`), **$509 worst / $60.1 likely**. That is **60× the entire $8.50
project cap**, and even the optimistic figure is 7×.

⇒ **A frontier stage-4 pass over the corpus is not affordable and never was.** The flash figure
scales to roughly $3 for 593 clauses, which is. §7 now carries the measured table.

⛔ Only **7 of 19** stored modules reach a seat: 5 fail stage 2, 7 are blocked by `readback-ungloss`
(**Q-6**). The check was not relaxed to raise that number.

---

## Q-4 · `dryrun.txt` is stale and is the one failing self-test check

`translate.py --self-test` reports **51 passed / 1 failed** (this said 52; measured 2026-08-07).
The failure predates today.

⚠️ **It is now VISIBLE from pytest.** `test_prompt_examples.py
::test_translate_self_test_runs_to_completion` asserted only "no Traceback" and "N passed", so
`pytest walkthrough/` read green while the self-test exited 1. It now asserts `returncode == 0`
— which pins no count, so it does not re-create the anti-pinning problem its old comment
claimed — and carries `xfail(strict=True)` naming this question. **Strict matters:** the moment
this is resolved and the self-test goes green, that test XPASSes and FAILS, so the exemption
cannot outlive the ruling.

**I have deliberately NOT regenerated it.** Regenerating bakes the current prompt into the
artifact, which would turn a visible red into an invisible green while changing what the artifact
attests. That is the shape this project keeps being bitten by.

**What a decision costs:** one word. Either "regenerate it" (and it goes green, attesting today's
prompt) or "leave it" (and it stays red and honest until the prompt settles).

---

## Q-5 · `STATE.md` is a deletion candidate with live inbound citations

It duplicates `REVIEW_QUEUE.md` and the phase_1 README and has drifted from both — it claimed
stage 2 was "under review, nothing built" until I corrected it today. But `STEP_stage3.md` and
`STEP_stage4.md` both cite it, and one live finding (weakest-licence inheritance being stated in
two places and computed nowhere) has **`STATE.md` as its only record**.

**What I did instead:** left it, corrected its false claim, and marked it a deletion candidate in
the file itself.

**What a decision costs:** "delete it" means first moving that one finding somewhere live. I can do
that unprompted if you want it gone — say so and it is a ten-minute job.

---

## Q-23 · Why can't a BORROW carry a gloss? (Matt, 2026-08-09)

`requires` is `list[str]` — bare `name/arity`. `concepts` carries a gloss and a licence. The
question is why the borrow side does not.

**The recorded objection (Q-6):** a clause that glosses what it borrows *"invents a meaning for a
term another clause owns"*, manufacturing problem #9 at source.

### ⭐ The objection assumes gloss divergence, and the measurement says the opposite

| `[RAN]` across repeat translations of one clause | |
|---|---|
| borrowed **names** | **0.00** agreement (0 of 22) |
| concept **names** | 0.30 |
| ⭐ concept **glosses** | **39 of 45 identical**; all 6 differences are pure paraphrase |

⇒ **The model agrees about meaning and disagrees about labels, every time.** A gloss is the stable
channel; a name is the noise channel. Requiring a gloss on a borrow puts the join key in the medium
that reproduces.

### ⭐ And a borrow gloss is a DIFFERENT SPEECH ACT from a definition

| field | says | authority |
|---|---|---|
| `concepts[].gloss` | *"X means this"* | **authoritative** — the clause owns it |
| a gloss on `requires` | *"I need an X that means this"* | an **expectation**, owned by nobody |

Two clauses may hold different *expectations* of one symbol without contradicting each other. Where
their expectations diverge, that is **problem #9 DETECTED** — the symbol is overloaded — and today it
is undetectable because there is nothing to compare. ⇒ **Problem #9 is manufactured only if a borrow
gloss is typed as a definition. Typed as a requirement, divergence is a detector.**

### ⚠️ The independent argument: `requires` is currently an UNVERIFIABLE promise

`requires: ['policy_class/2']` asserts another clause defines it. Nothing checks the claim (Q-22),
and even once a clause *does* define something, **nothing can tell whether it is the same thing**,
because names agree at 0.00. A gloss is the only artifact that could make the link checkable. Without
one, `requires` is a promise with no way to be kept **or broken**.

### What it costs, honestly

- ⛔ `schema.py` is **WATCHED**: guard acceptance, and a `contract_hash` change re-translates the
  corpus per Q-20's ruling. ⭐ At **13 of 593 clauses** that cost is near its lifetime minimum — it
  will only ever get more expensive.
- ⚠️ A borrower may write a confident wrong gloss. That is the *point*: it becomes checkable against
  the owner's gloss. Today it fails silently instead.
- It does **not** fix Q-22 — an unsatisfied `requires` still needs to become an error. Orthogonal.

⛔ **Not decided.** The alternative worth rejecting by name if this is adopted: *"resolve borrows
from the document instead"* — six experiments, ending at **0.00** vocabulary agreement and 0 shared
rule shapes for 6 of 8 concepts (`resolve_runs/ITERATION_LOG.md`).
