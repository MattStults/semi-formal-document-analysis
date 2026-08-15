# M4 — `ontology` used as a declaration list (the unsafe variable)

**Mechanism, one sentence.** The model wants to say *"this predicate exists"* about a
property the span merely names, writes it as an `ontology` atom carrying a variable, and
supplies no body that binds the variable — a state the grammar permits and only a
validator rejects, and one that makes clingo refuse the whole file.

**14 repair rounds, $0.0221 (9% of repair spend), 8 clauses, 1 module lost.**

---

## How to recognise it

Three message shapes, one defect:

```
ontology[0]: ontology atom: 'adheres_to_chain_of_command(S)' carries the variable 'S'
  but the body never mentions it, so nothing binds it. The solver refuses the WHOLE FILE
  for an unsafe variable — bind it in the body, or drop it from the head

ontology[0]: ontology atom: 'model_training_alignment(M)' carries the variable 'M' and
  there are no conditions to bind it. The solver refuses the WHOLE FILE for an unsafe
  variable, so this would take every linked clause down with it — give it a body, or
  write a term with no variables

ontology[1]: ontology atom: 'not dictates_action(G,S)' is not a term. It must be a
  functor like produce(M) or say_cannot_answer — not a rule, not a sentence
```

and, when it reaches the solver instead of the schema checker, the wrapper:

```
l1_170_n043.lp: clingo refused this program, so nothing below was actually analysed:
  …/l1_170_n043.lp:46:1-72: error: unsafe variables in: | …:46:16-17: note: 'R' is unsafe
```

The `atom-not-a-term` variant belongs here rather than in a separate IDFORM class: on
`l1_170_n037` it is the same clause thrashing between representations across rounds 1-2
before landing on M1 at round 3.

---

## The clauses, with attempt counts

| clause | attempts | rounds in class | outcome |
|---|---|---|---|
| `l1_170_n006` | 5 | 5 | **unrepaired — module lost** |
| `l171_426_n005` | 5 | 2 | unrepaired (lost to M3) |
| `l1_170_n037` | 5 | 2 | unrepaired (lost to M1) |
| `l1_170_n016` | 4 | 1 | translated |
| `l1_170_n053` | 5 | 1 | translated |
| `l1_170_n078` | 5 | 1 | unrepaired (lost to M1) |
| `l1_170_n039` | 3 | 1 | translated |
| `l1_170_n007` | 2 | 1 | translated |

---

## Verbatim excerpts

**`l1_170_n006` — 5 attempts, the same finding every round, module lost.** Verbatim (L11):

> `These goals can sometimes conflict, and the Model Spec helps navigate these trade-offs
> by instructing the model to adhere to a clearly defined [chain of
> command](#chain_of_command).`

The offending atom is `adheres_to_chain_of_command(S)` — the model minted a
situation-indexed predicate for a sentence that describes what the Model Spec *does*, and
then had no situation to bind `S` to, because the sentence is not about a situation.

**`l1_170_n007` — 2 attempts, recovered.** Verbatim (L13):

> `We are training our models to align to the principles in the Model Spec.`

Atom `model_training_alignment(M)`, no body. Same shape, same cause: a descriptive
sentence about OpenAI, turned into a predicate about a variable that the sentence never
quantifies over.

**`l1_170_n039` — 3 attempts.** Verbatim (L67):

> `We assign each instruction in this document, as well as those from users and
> developers, a *level of authority*.`

Three unsafe-variable findings on round 1; round 2 they become three
`undeclared-body-name` findings on `authority_level`. **The repair traded M4 for M1** —
the model bound the variables by adding a body, and the body's predicate was then
undeclared. This is defect trading with a visible mechanism, not noise.

---

## The overlap that Fix D's simulation does not model

**Seven of the eight clauses in this class are non-normative spans** (`n006` about-doc,
`n007` descriptive, `n016` about-doc — *"commentary that is not directly instructing the
model will be placed in blocks like this one"* — `n037` about-doc, `n053` rationale,
`n078` notation convention, `n039` descriptive). Only `l171_426_n005` is an obligation.

That matters because the unsafe atom is the *same act* as M1's undeclared body name: both
are the model trying to declare that a descriptive predicate exists. It picks `ontology`
with no body, or `ontology` with a body of undeclared names, and the checker names the
two attempts differently. **`n039` shows the model moving between them within one chain,
and `n053` and `n078` and `n016` do the same** (`n016`: M1 → M4 → M1 across three rounds;
`n053`: M1 → M4 → M1 → M2 across four).

Consequence for the fix pass, stated plainly: a grammar change that makes the unsafe form
unwritable does not make the *intention* go away. On this run's evidence it would push
those attempts into M1, which is the class with no candidate fix.

---

## Recovery — what changed when it did

Four of eight recovered. The recovery move is either "add a body" (which promptly draws
an M1 finding, `n039`, `n016`, `n053`) or "drop the variable and write a ground term".
`l1_170_n006` never moved: five byte-identical modules, then unrepaired. On the 08-15
retry under a byte-identical prompt it translated on **attempt 1**.

---

## The paid cost of the class

| | |
|---|---|
| repair rounds in which it appears | **14 of 130 (11%)** |
| findings | 17 (10 `unsafe-var`, 5 `unsafe-var-no-body`, 2 `atom-not-a-term`) |
| clauses touched | 8 |
| **attributed spend** | **$0.0221** (9%) |
| **modules lost** | **1** (`l1_170_n006`) |

Note the collapse against the earlier census. `unsafe-variable` was the **#1 class by
cost** in `TRANSLATION_REPAIR_CENSUS.md` §4 (22 rounds, $0.0439, 25% of gen-11 rounds).
On this 100-clause slice it is #4 at 11%. The earlier census's gen-11 population was
dominated by clause sets with acts and rules; this slice is the document's overview and
definitions sections, where there is far less to bind. **Do not carry the census's
ranking into this corpus region without re-measuring.**

---

## FALSIFIER

*M4 and M1 are the same intention wearing two checkers.* Wrong if, over a larger sample,
chains that draw an unsafe-variable finding do **not** show an elevated rate of
subsequently drawing `undeclared-body-name`. On this run 5 of the 8 clauses show the
transition, which is suggestive on n=8 and nothing more. The clean test is available with
zero spend: replay every stored failing module through `schema.validate_all` with the
unsafe-variable check disabled and count how many then report `undeclared-body-name`. If
the count is near zero, the two are independent and Fix D's class subtraction is sound
after all.

---

## Candidate solutions already on record

* **Fix D — split `ontology` into `OntologyRule` (body required) and `OntologyGroundFact`
  (no variables).** Reviewed **NEEDS WORK**, with four independent defects
  (`TRANSLATION_CENSUS_REVIEW.md` §6, F-2):
  * **F-2**: D does not make the class unrepresentable — it reaches only body-less
    ontology sites; 12 of 99 unsafe atoms already carry a body and migrate unchanged;
    `OntologyGroundFact`'s no-variable rule is *"a `Field(description=…)` and no validator
    and no `pattern`"* — lever (d) wearing lever (a)'s label. Headline drops 58% → **43%**.
  * **D-1**: no migration for 200 stored modules, 159 with a non-empty `ontology`.
  * **D-2**: uncosted forced re-translation — `contract_hash` goes stale on 219 artifacts
    and `version.apply_waivers` **raises** on a contract-stale clause.
  * **D-3**: `schema.py:865` builds the `undeclared-body-name` declaration set from
    `self.ontology`; if not updated for both new lists, **every ontology-declared body
    literal becomes an M1 finding**.
  * **D-4**: the cheaper lever — *conditionally requiring `body` when the atom carries a
    variable* — reaches 87 of 99 cases with zero blast radius and **was never rejected by
    name**, which under repo doctrine is disqualifying for the draft.
* **Fatal to the diff, not to the idea.** D-4 is the review's own answer and it is
  untouched by anything in this run. This run adds one new argument *against* the full
  split and *for* D-4: the split's own D-3 failure mode would inflate M1, the most
  expensive and least-fixable class here.
* **Fix A3 (`ontology-rule-split`)** already clears the sub-case where the whole rule was
  stuffed into `atom` (`"atom": "system_rule(R) :- set_by_openai(R)"`); it fired 9× on the
  stored corpus and is safe. It does not appear in this slice.

---

## Graph-stage or translation-stage?

**Translation-stage, with a graph-stage contributor.**

The illegal state is a property of `schema.OntologyFact` — `body: Optional[str]` makes
"unbound head, no body" well-formed. No graph decision changes that, and the fix is
lever (a) or (b) inside the schema. That is the translation-stage half and it is real.

The graph-stage contributor is the same one as M1: **seven of the eight clauses are
non-normative spans**, and the model reaches for a situation variable because it has been
told to write a rule about a sentence that quantifies over nothing. `adheres_to_chain_of_command(S)`
has no `S` because *"the Model Spec helps navigate these trade-offs"* has no situation in
it. A graph-stage span-type decision would remove most of this class's volume without
touching the schema — but not the one obligation clause in it (`l171_426_n005`), and not
the class in corpus regions that are genuinely normative, where the earlier census
measured it as the most expensive class of all.

**Verdict: fix it at translation stage (D-4 shape), because the graph-stage route does not
generalise past this corpus region.**

---

## Open question for the fix pass

The whole-file refusal wrapper is the worst message in the pipeline: rounds 1-4 of
`l1_170_n043` told the model only *"clingo refused this program"* plus a temp-file path,
and the model returned byte-identical bytes four times. **Does the unsafe-variable check
run before link stage on every path, or are there routes (like `n043`'s) where it reaches
the model only as a clingo cascade?** If the latter, part of M4's cost is a
message-plumbing defect and not a grammar problem at all.
