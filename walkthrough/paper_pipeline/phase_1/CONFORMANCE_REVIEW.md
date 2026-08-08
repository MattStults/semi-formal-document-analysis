# Adversarial conformance review — stage 1, stage 2, the repair loop

**Date:** 2026-08-07. **Spec:** `walkthrough/resources/03_pipeline.md` (source of truth for
`walkthrough/`, above every other document here). **Read:** open question 1's **CLOSED** section,
not the superseded one below it.

**Artifacts as reviewed** (other agents are writing in this tree; `translate.py` changed underneath
this review once, so the versions are pinned):

    translate.py  md5 1e4879e142626fde1bbec3cab68cea03
    schema.py     md5 35ca9510cc7ca70b506150735aa9ee4e
    checks.py     md5 f1c30df421b8a8e4bdd909840ba95b20
    link.py, prompt/*.md, config.json, runs/20260807-154618-together-deepseek-v4-flash/

Everything below was **run**, not inferred, except where marked *inferred*. Nothing was sent;
`--live` was not used; no spend. `pytest` in `phase_1/`: 153 passed.

---

## Summary of where each side stands

**The design is ahead of the implementation** on: the accumulating transcript's *content* (F1), the
gate that stage 2 is supposed to be (F2), D2 witness and D3 opaque-stubs (F6), Invariant 1's
"render the definition, not the label" (F7), Invariant 2's toggleability and weakest-licence
inheritance (F8), and open question 1's namespace **type constraint** (F9).

**The implementation is ahead of the design** on: the error/note severity split, the
`declaration-edit` / `unclear`-rate guards, `Concepts` carrying a licence, `outcome` +
`abstain_reason` folded into `Module`, `OntologyFact.gloss` being required, `RESERVED`, the `%%`
header format and the `#const onto = on` ontology guard. None of these is in `03_pipeline.md`. Most
are improvements; two of them (F3, F4) are where the design's own guarantees leak out.

**Stale, and contradicting both:** `STEP_stage2_and_repair.md` §5 still says repair is a *"fresh
conversation … no assistant turns carried"*. That is the wording the design records as **wrong** and
the implementation no longer does. `STEP` §1 also withdraws the arm-B commitment that `DEFERRED.md`
D-3 still asserts.

---

## F1 ⛔ The repair transcript's first user turn is not the prompt that produced attempt 1

**Spec** (Part 4 §1, *How repair works, corrected 2026-08-07*):

> ```
> system   : the fixed instructions, format, worked examples, failure modes
> user     : the clause and its cross-references
> assistant: the module it produced
> ```
> … the message **prefix is byte-identical as the transcript grows**, so every turn after the first
> is a cache hit

**Implementation** (`translate.py:repair_loop`): the transcript is seeded with

```python
transcript = [{"role": "user",
               "content": f"CLAUSE {clause.get('id')}\n{clause.get('quote','')}"}]
```

not with `build_user(...)`, which is what was actually sent. Measured on the live run: `m0091`'s
real user block is **5,341 bytes** and includes the `CROSS-REFERENCED CLAUSES` section for eight
clauses (`m0293 m0295 m0296 m0298 m0304 m0523 m0524 m0525`); the transcript's first user turn is
**491 bytes** and contains none of it — no locator, no kind, no cross-references, no instruction.

**Consequences, both load-bearing:**

1. **The repair attempt is denied something stage 1 says it must be given.** Part 4 §1's GIVEN list:
   *"the text of every clause this one cross-references — ⭐ a clause that modifies rules defined
   elsewhere cannot be translated in isolation."* Attempt 2 of `m0091` was asked to repair a module
   about refusal style and privileged information with the text of both dependencies removed. That
   is failure mode #2 reintroduced by the repair loop itself.
2. **The stated cache benefit does not exist between attempt 1 and attempt 2** — the prefix changes
   completely. It holds only from attempt 2 onward. The design gives this as one of the three
   reasons repair is a conversation at all.

`test_repair.py::test_the_transcript_PREFIX_is_byte_identical_as_it_grows` is green because it only
compares `repair_loop`'s own calls to each other; nothing compares turn 1 to what `run()` sent.

**Accidental.** Nothing records it. **Whose fix: the harness** (pass the built user block in).

## F2 ⛔ Stage 2's link checks never run on a clause that validates first time

**Spec** (Part 3 flowchart): stage 1 → `2. DETERMINISTIC CHECKS` → D1…D5 → `pass?` → yes → stage 3;
no → repair.

**Implementation** (`translate.py:run()`): the only call path is

```python
obj = parse_module(env["text"], ...)          # schema.validate ONLY
except ResponseParseError:                     # -> repair_loop -> checks.run_checks
```

`run_checks` — and therefore `link.collect`, i.e. **clingo compilation, unresolved references,
rule-shape, closure conflict, beats-cycle, the concept-table checks** — is reachable *only* from
inside `repair_loop`, and `repair_loop` is entered *only* when the schema validator already raised.
Verified by grep: `run_checks` appears in `translate.py` exactly once, at line 2103, inside
`repair_loop`.

**Consequence:** in the run on disk, `m0217` and `m0053` were written as `status: "translated"`
having never been compiled or link-checked. (I ran `link.py` over the run directory afterwards: they
happen to pass. That is luck, not a check.) Half of the five deterministic checks the design draws
as the gate are, in a real run, applied only to modules that already failed the other half.

**Accidental.** **Whose fix: the harness.**

## F3 ⛔ An unrepaired module with a standing error is written out as `translated`

**Spec:** the repair edge exists because a failing module must not proceed.

**Implementation:** `checks.run_checks` returns `CheckResult(outcome="invalid", module=<the built
module>, …)` whenever the object *constructed* but breached a corpus/identity rule or a link check —
`module` is `None` only when pydantic refused to build it. `repair_loop` then returns
`status="unrepaired"` **with a non-`None` module**, and `run()` tests only

```python
if out.module is None:   # -> failure
...
obj = out.module         # -> written as .json/.lp, status=obj.outcome == "translated"
```

**Run, not inferred.** A scripted two-attempt repair on a module citing `m9999`:

```
status: unrepaired | module is None: False | outcome on module: translated
findings: [('schema-breach','error',"cites 'm9999', which is not a clause in this corpus...")]
```

`run()` would print `↻ repaired on attempt 2`, write `m0001.json` / `m0001.lp`, record
`status: "translated"`, and count it in the "N translated" summary line.

**Consequence:** a fabricated citation — the design's *"single worst failure available here"*, the
one that creates an invented entity behind a passed check — survives repair and is reported green.
Every link-origin error has the same exit. `m0091` only failed loudly because its breach was at the
pydantic layer.

**Accidental, and it is the one finding here I would treat as blocking.** **Whose fix: the harness.**

## F4 ⛔ `concepts` is a third declaration site the design never granted, and it makes a dead rule pass

**Spec** (Part 4 §1): *"⚠️ `requires` versus `inputs` is the distinction that makes the link check
possible. Without it, 'a name nothing defines' cannot be told apart from 'a name supplied at query
time,' and every translation looks broken or every one looks fine."* The prompt transcribes this
correctly — `10_output_format.md`: *"Anything appearing in a body must be in your `ontology`, in
`requires` …, or in `inputs`."* Three sites.

**Implementation** (`schema.py:_coherent`, line 623-625) admits a fourth:

```python
declared = ({f.atom.split("(")[0] for f in self.ontology}
            | {c.name for c in self.concepts})
known = declared | {p.split("/")[0] for p in self.requires + self.inputs}
```

A bare `Concepts` entry — name, arity, gloss, licence, and **no logical content whatsoever** —
satisfies the body-reference check. `link.py` then classifies the name `concept-declared`, which
`checks.py`'s severity ruling makes a **note**, i.e. inert.

**Measured on the live run.** `m0217.lp`:

```
asserts(m0217, permit, produce(M)) :- political_content(M), broad_audience(M),
                                      not exploits_individual(M).
```

All three body predicates are declared *only* as `concepts`. `requires` and `inputs` are both empty.
Nothing anywhere can ever derive `political_content/1`, so this rule can never fire — failure mode
#3 — and the module passed every check with three notes and zero errors.

**Consequence:** the exact degenerate `checks.py` documents for attack A (`requires`→`inputs`) is
available one field over and costs nothing: route every undefined name through `concepts` and every
translation looks fine. This is not in `STEP_stage2_and_repair.md` §4's attack table.

**Accidental.** **Whose fix: the schema** (the prompt is already right).

## F5 ⛔ `acts` is *not* a declaration site, and that is what defeated the only repair in the run

Same block: `known` omits `self.acts`. So an act term the module declared in `acts` and then used in
a rule body is reported as undeclared, and the message names three remedies, none of which is
correct for an act:

> `m0091`: *"body references `be_explicit_about_inability` but nothing declares it. Put it in this
> module's `ontology`, in `requires` … or in `inputs`."*

`m0091` declared `be_explicit_about_inability(I)` in `acts`. The clause was sent back once, failed
identically (`per_attempt: [1, 1]`), and is the run's one `unrepaired`.

**Consequence:** for act-typed predicates, the finding is false and the guidance is wrong; the loop
cannot converge. Note this compounds with F1 — the repair attempt was also missing eight
cross-referenced clause texts.

**Accidental.** **Whose fix: the schema.** (Not the model: it followed the contract as written.)

## F6 ⚠️ Two of the five deterministic checks do not exist; one is half-built

**Spec** (Part 3): D1 compiles · no unresolved names · no anonymous placeholders; D2 a witness for
every rule, at link scope; D3 no opaque stubs; D4 every fact cites a real clause **and a real
concept**; D5 rule-shape declarations hold.

| | status | where |
|---|---|---|
| D1a compiles | ✅ | `link._check_clingo` |
| D1b unresolved names | ✅ arity-aware | `link.collect` |
| D1c anonymous placeholders | ✅ at generation | `schema._check_term` / `_check_body` |
| **D2 witness at link scope** | ⛔ **absent** | nothing. `witness.lp` is a hand demo |
| **D3 no opaque stubs** | ⛔ **absent** | no mechanical definition exists |
| D4a cites a real clause | ✅ | `validate(known_clause_ids=…)` |
| D4b concept declared / glossed | ✅ | `_coherent`, `Concept.gloss` |
| **D4b-3 finds a provider corpus-wide** | ⛔ deferred, grounds in `DEFERRED.md` D-3 | link scope |
| D5 rule-shape | ✅ | `link._check_rule_shape` |
| #17 beats-cycle | ✅ (extra, ground facts only) | `link._check_beats_cycle` |

D2's and D3's absence is **stated honestly** in `STEP_stage2_and_repair.md` §1 and §7 — deliberate
and recorded, and I verified the claim rather than accepting it. But D2's absence has a concrete
cost in this very run: it is precisely the check that would have caught F4's dead rule, and the
design measures it (*5 witnesses with the dependency linked, 0 without*). D3's absence means failure
mode #5, the hollow stub, has **no check anywhere** in a pipeline whose stage-1 prompt names it.

## F7 ⚠️ Invariant 1 — the ingredient exists, the remedy does not

**Spec:** *"symbols must resolve to concepts with written definitions, and the read-back must render
**the definition, not the label**."*

- Written definitions: ✅ `Concept.gloss` and `OntologyFact.gloss` are both required and non-empty
  (`DEFERRED.md` D-3 level 2 records that the second was added to close this; verified).
- Rendering the definition into the read-back: ⛔ **absent.** `read_back` is free prose written by
  the model; `render_lp` interpolates it verbatim into `%!trace_rule` and never substitutes a gloss.
  `m0217`'s read-back says *"political content crafted for a broad audience"* — labels, echoing the
  clause, which is the failure the invariant exists to prevent.
- Arm A vs arm B: the dictionary is **not** supplied to the model (arm B by construction). Recorded
  in `DEFERRED.md` D-3 as a design amendment — honest — but note the design's instruction
  (*"Run both arms on the same clauses before building anything downstream that assumes one"*) is
  unexecuted, and stage 2 is downstream. `STEP` §1 withdraws the arm-B label; `DEFERRED.md` D-3
  still asserts it. **Those two implementation-side documents contradict each other.**

**Verdict: partial.**

## F8 ⚠️ Invariant 2 — the graded version is correctly encoded; two of its clauses are not

The **earlier binary version is nowhere.** Checked both sides:

- `schema.Licensed` implements the three classes with per-class obligations (`cites` required for
  `textual`, `inference` for `assumed`, `toggleable` for `world`) and rejects nothing on grounds of
  class. Its docstring carries the design's own reasoning verbatim (*"Rejecting non-textual facts
  outright pushes an author to cite a plausible-looking clause"*).
- `prompt/00_task.md` states the table and adds *"An honest `assumed` is always better than a
  dressed-up `textual`."*

Two clauses of the invariant are not implemented:

1. **Toggleability is a claim the rendering does not deliver.** `render_lp` emits a `world` fact as
   `atom :- o.` with the comment `% [W] toggleable` and nothing else. The **ontology block** is
   genuinely switchable (`#const onto = on.`); an individual `world` fact is not. The design requires
   it to be *"marked and toggleable — a result resting on world knowledge is a different claim"*, and
   Part 4 §4 makes "marked and toggleable" the deterministic check that stands in for the `world`
   row of the citation checker's denominator. Half of it cannot be checked because half of it is not
   there.
2. **Weakest-licence inheritance** (⭐ in the design) is told to the model in `00_task.md` as a note
   and computed nowhere. No propagation exists in `schema`, `link` or `checks`.

The fourth class for the behaviour side is absent, correctly — it is out of stage 1's scope.

**Verdict: partial.** Grading itself: ✅ implemented, prompt and validators agree.

## F9 ⚠️ Open question 1 CLOSED — four of five present; the namespace guard is not a type constraint

| requirement | status |
|---|---|
| act-index both sides | ✅ `Assertion.act` is an act term, `acts` declared, `_check_term` rejects a rule in the slot; `asserts` must name a declared act |
| `beats(Sayer, Winner, Loser)` | ✅ `Superiority.sayer`, plus the rule that a module may only record superiority its own clause states, plus corpus membership for all three slots |
| forced per-act default closure, **enforced in `link.py`** | ✅ enforced twice — `schema._coherent` at generation and `link._check_closure` on the `%% acts:` header, with `closure-conflict` across a link set |
| namespace type constraint | ⚠️ **partial, and not a type constraint** — see below |
| the one deontic axiom `O(¬a) ≡ F(a)` | ⛔ deferred, `DEFERRED.md` D-2. **Claim verified:** no field of `Module` mentions act complements, so the axiom can be added over an existing `asserts/3` corpus without re-translating. Honest deferral |

The namespace separation is implemented as a **three-name lexical blacklist**
(`BEHAVIOUR_NS = {"b_asserts", "b_beats", "seed"}`) applied to rule bodies and ontology atom names.
The spec says *"Enforce with a type constraint."* A blacklist over three literal names is not a type
constraint: any behaviour-side predicate not spelled `b_*` passes, and `link.py` — where the
constraint would live if it were one — has no namespace check at all. The `beats` corpus-membership
rule does cover the specific attack the spec names (`beats(clause, behaviour)`), which is why this is
partial rather than absent. **Accidental / unrecorded.**

## F10 ⚠️ `acts: []` escapes the forced closure entirely, and a contentless module counts as translated

`schema._coherent` derives `governed` from `self.acts`; a module with no acts owes no closure. And
the "did you actually translate anything" guard is

```python
if not (self.asserts or self.defines or self.ontology or self.beats or self.concepts):
```

— **`concepts` alone satisfies it.**

**Measured.** `m0037` (definitional, *"System: Rules set by OpenAI…"*). Attempt 1 wrote an ontology
entry whose `atom` was a whole rule; the finding was correct. Attempt 2 **deleted it** rather than
moving the conditions into `body`. The result: `n_asserts 0, n_beats 0, n_defines 0, n_ontology 0`,
five concept declarations, four claims, zero acts, zero closure — and `status: "translated"`,
counted in the run's success line. `m0037.lp` contains no logic at all, only comments.

The `shrank` flag *did* fire and is recorded in `run.json`. It is inert: it changes no outcome and
no exit code. So the design's *"a model that cannot faithfully translate a clause should say so
rather than produce something that passes the checks"* was defeated in the opposite direction — the
model produced nothing and it passed.

This is a fifth entry for `STEP` §4's attack table: **delete the content, keep the declarations**.
**Whose fix: the schema.** (The model's deletion is a model choice; the schema is what called it a
translation.)

## F11 ✅ / ⚠️ The repair loop's *denial* machinery is correct — verified item by item

The newest work is, on this axis, conformant. Checked each of the design's four requirements:

| spec | implementation |
|---|---|
| accumulating transcript, nothing dropped once fixed | ✅ `repair_loop` appends two turns per attempt; `render_error_log` renders **one** attempt's findings per turn and the history stays in the conversation. Correct — re-rendering the whole history each turn would duplicate and re-pay |
| only stage-2-origin findings admitted, filtered by ORIGIN | ✅ `Finding.origin` is required, positional, `__post_init__`-guarded against empty, has no default; `DISCLOSABLE_ORIGINS = ("schema", "link")`; `link.Finding` is adapted at the boundary via `asdict` so a new field raises rather than being dropped |
| an excluded finding leaves a **visible hole** | ✅ `render_error_log` emits `(N finding(s) withheld: they come from a later stage and would disclose an expected answer)` |
| abstention is a real answer; the rate is a signal | ✅ terminal, never re-prompted; `abstained` vs `abstained_under_repair` distinguished; `CheckResult.first_attempt` is tri-state; read off the validated module, never the raw dict |
| convergence measured because the split is untested | ✅ `per_attempt` per clause in `run.json`; `unclear_closure_rate`; exhaustion is `unrepaired`, never an exception |

Two caveats that are not conformance defects but limit the measurement:

- `per_attempt` counts **all** findings, notes included, so a clause whose only findings are inert
  notes reads as non-converging. `m0091`'s `[1, 1]` happens to be two errors.
- The **abstention rate** the design calls the reliability signal is printed (`N abstained`) but not
  written to `run.json` as a rate, and `run_checks`'s abstention branch is unreachable from `run()`
  for a first-attempt abstention (F2's path again: `parse_module` accepts it and it is recorded from
  `obj.outcome` instead). The two paths agree today; they are two copies of one rule.

## F12 ▫️ `Module` field-by-field against the design's dataclass

| design | implementation | note |
|---|---|---|
| `clause_id`, `claims`, `acts`, `ontology`, `asserts`, `beats`, `defines`, `closure`, `requires`, `inputs`, `forbid_body` | present, same names, same meanings | ✅ |
| `concepts: list[Concept]` | `list[Concepts]` where `Concepts(Licensed, Concept)` | **added**: a concept declaration now carries `licence`/`cites`/`inference`/`toggleable`. Not in the design. Worse, `prompt/10_output_format.md`'s licence section lists *"On `asserts`, `beats`, `defines` and every `ontology` entry"* — **`concepts` is not named**, so the model is required by the wire schema to supply a field the prompt never explains. In the run it guessed reasonably (`m0091` used `assumed` with named inferences), but this is unguided |
| `Abstention` as a separate dataclass | folded into `Module` as `outcome` + `abstain_reason`, with every content field forced empty | departure, explained in `schema.py`'s docstring, harmless — arguably better, since it makes "abstained but carries claims" expressible-and-rejected |
| `Fact.atom` | split across `OntologyFact.atom`, `Assertion.act`, `Definition.kind/term` | equivalent |
| `forbid_body: list[tuple[str,str]]` | `ForbidBody(head, banned)` | equivalent |
| `provides` **REMOVED** | absent from `Module`, from `render_lp`, and from `link.py` (with a self-test pinning that no `provides` output survives) | ✅ correctly removed on both sides |

The relation vocabulary written into the design today is transcribed **exactly**: four relations,
`Status` exactly `forbid`/`permit`/`oblige`/`prefer`, `prefer` explained as a comparative in both
`schema.py` and `00_task.md` rule 5b, `concepts` vs `ontology` distinguished with the design's own
reasoning, concept glosses kept out of the `.lp` and emitted as `concepts.json`. The GIVEN list
(clause text, cross-referenced texts, instructions + worked examples + failure modes) and the DENIED
list (no behaviour, no label or gold answer, no test cases) are both honoured; `30_failure_modes.md`
carries all 17. Cache ordering (fixed block first, varying last) is implemented and enforced by
config.

## F13 ▫️ Things the implementation asserts that the spec does not say

- **The error/note severity split, and "only `error` drives a repair."** Not in `03_pipeline.md` at
  all — the flowchart has one undifferentiated `pass?`. The reasoning in `checks.py`'s docstring is
  sound (a `requires-unprovided` note is true of a *correct* module, so a note-driven loop would
  teach the model to destroy the `requires`/`inputs` distinction). But this is a design decision
  taken in an implementation file, and F4 is its unbudgeted consequence: `concept-declared` was made
  a note by the same ruling, and that is what lets a dead rule pass.
- **`declaration-edit` flagging and the `unclear`-closure rate.** From `STEP` §4, not from the
  design. Good additions; both currently inert (they set no outcome).
- **`STEP_stage2_and_repair.md` §5 is stale and wrong**: *"fresh conversation = a new `messages`
  list per attempt, no assistant turns carried"*. This is the formulation the design explicitly
  corrected today (*"Read as written that produced the wrong implementation"*). The implementation
  is ahead of this document; the document should not be used as a plan.
- **`DEFERRED.md` D-3 vs `STEP` §1** disagree on whether arm B was committed to. Design says the
  choice is open and both arms should be run.

---

## Load-bearing spec items the implementation ignores

1. *"Run both arms on the same clauses before building anything downstream that assumes one"*
   (Invariant 1 / open question 2 / Part 6's *highest-value next step*). Only arm B exists, and
   stage 2 assumes it.
2. *"A conclusion inherits the weakest licence in its derivation"* (F8).
3. D2 witness and D3 opaque stubs (F6) — recorded as excluded, but D3 leaves failure mode #5 with no
   check anywhere.
4. *"toggleable"* as an operative property rather than a comment (F8).

## Ranked fix order, and who owns each

| | finding | owner |
|---|---|---|
| 1 | F3 — unrepaired module written as `translated` | harness |
| 2 | F2 — link checks skipped on first-time-valid clauses | harness |
| 3 | F4 — `concepts` as a free declaration site (dead rule passes) | schema |
| 4 | F1 — repair transcript drops the real prompt and the cross-references | harness |
| 5 | F5 — `acts` missing from the declaration set (blocks convergence) | schema |
| 6 | F10 — contentless module counts as translated; `acts: []` escapes closure | schema |
| 7 | F9 — namespace blacklist is not a type constraint | schema / link |
| 8 | F7, F8 — Invariant 1 read-back rendering; Invariant 2 toggleability + inheritance | design work, then schema |

**Not model defects.** Of the four modules in the run, exactly one problem is the model's own
(`m0217`'s `not exploits_individual(M)`, which `00_task.md` rule 4 forbids; and `m0053`'s coined
`interactable_entity`, which nothing checks because `Definition` validates shape only and carries no
read-back). Everything else traces to the schema or the harness.
