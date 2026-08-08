# Step X — stage 4: the read-back, and the four review seats

**Status: revision 1, for review. Nothing is built. This document is the plan only.**

⚠️ **Every claim below about existing code was executed**, and is marked `[RAN]` with the command
or the number it produced. Claims taken from reading a file are marked `[READ]`. Four Step-X plans
have now been written in this directory and **three were found wrong by a clean reviewer** — not
under-specified, wrong — and the commonest error was a scope claim nobody had executed. Five of the
statements below changed after running them, and each is flagged where it sits.

⚠️ **`03_pipeline.md` was re-read at the point of writing**, per `STATE.md` NEW-7. Stage 4 is the
`RB` node of the Part 3 flowchart (*"4. READ BACK — render each derivation as English, expanding
concept DEFINITIONS"*) and its four children `V1`–`V4`, plus Part 4 §4 (*"Why four reviews rather
than one"*), §*"The citation checker's coverage rule"*, §6 (*"Divergence, replacing the ambiguity
exit"*), Invariants 1 and 2, and Part 5 open questions 4 and 5 (**RULED**: adopt all ten seat
contract elements).

⛔ **The numbering contradiction recorded in `STEP_stage3.md` still stands** and is not resolved
here: the flowchart numbers probe cases 3 and read-back 4; Part 4's prose *"the probe cases at
stage 4 are the unit tests"* numbers them the other way. This plan uses the flowchart, as
`STEP_stage3.md` does.

---

## 0 ⛔ Five measured facts that change what this plan can claim

These were produced by running the current code against the committed run artifacts. Each one
invalidates something in the existing record, so they come before the design rather than after it.

**(1) `[RAN]` The only conditional module in the runs no longer passes stage 2.**

```
$ .venv/bin/python -c "import schema, json; \
    print(schema.validate_all(json.load(open('runs/…-154618/m0217.json')), clause_id='m0217')[0])"
None
  <root>: body references `political_content` but nothing declares it.
```

`CONFORMANCE_REVIEW.md` F4 found that `concepts` was wrongly admitted as a body-declaration site;
`schema.py` was fixed afterwards (`schema.py` 16:37, the run 15:48). The fix is right. The
consequence is that **`runs/…-154618/run.json`'s `status: "translated"` for `m0217` is stale**, the
`.lp` on disk was rendered under a superseded contract, and — this is the part that matters here —
**`STEP_stage3.md` §2's PASSING example is a module that no longer validates** (`STEP_stage3.md`
16:05, the fix 16:37). Nothing is wrong with `STEP_stage3.md`'s reasoning; its fixture has expired.

⇒ This plan uses `m0217` **patched** — the three body predicates moved from `concepts` into
`inputs` — and says so at every use. `[RAN]` the patched object validates with 0 breaches and
renders. It is a fixture, not a run result.

**(2) `[RAN]` The F4 repair IS pinned — and I had this backwards until I ran it.** Reading alone,
`grep "nothing declares it"` returns six sites that all look like the *general* undeclared-name
guard, and I wrote down that the fix would survive its own deletion. It does not. Restoring the
wrong line

```python
declared = ({f.atom.split("(")[0] for f in self.ontology}
            | {c.name for c in self.concepts})        # the F4 defect, put back
```

and running `pytest -q test_schema.py test_checks.py test_repair.py` gives **2 failed, 145 passed**:
`test_a_concept_does_NOT_declare_the_predicate_for_the_undeclared_check` and
`test_a_CONCEPT_declaration_alone_does_not_satisfy_a_body_reference`. `schema.py` was restored
byte-identically and verified. ⚠️ **Recorded because it is the exact error class this document is
warned about** — a scope claim taken from a grep. It cost one command to check.

**(3) `[RAN]` The read-back does not expand definitions anywhere, and the leaves are raw ASP.**
Two halves, both run:

```
$ .venv/bin/python -m xclingo --auto-tracing=facts m0255.lp clauses/m020{0,1,3}.lp m0255_case_c.lp
  |__"producing m3 would violate restricted_content"
  |  |__"restricted_content still binds"
  |  |  |__"the exception covers information only, and m3 is an action"
  |  |  |  |__forbids(restricted_content,m3)
  |  |  |  |__material_type(m3,action)
```

The rule sentences render (xclingo 2.0b24 `[RAN]`, `%!trace_rule` dialect works). But
`restricted_content` is a **label** in every one of them, and the derivation's leaves are
un-glossed ASP terms. `CONFORMANCE_REVIEW.md` F7 said the remedy was absent; **verified, and it is
absent in two places, not one** — the rule sentences and the fact leaves.

Second half, on schema-produced modules `[RAN]`: rendering `m0037`, `m0053` and patched `m0217`
and searching each `.lp` for its own concept glosses gives **0/5, 1/2, 1/3**. Both hits are inside
the `% SOURCE:` comment block, not in any logic line — the gloss matched because the gloss is a
verbatim fragment of the clause, which is finding (5).

**(4) `[RAN]` The read-back covers two of five content types, and a four-clause run yields one
sentence.** `read_back` is a field of `ReadBack`, and only `Assertion` and `Superiority` inherit
it `[RAN]`:

```
Assertion   [act, body, cites, inference, licence, read_back, read_back_slots, status, toggleable]
Superiority [body, cites, inference, licence, loser, read_back, read_back_slots, sayer, ...]
Definition  [cites, inference, kind, licence, term, toggleable]          <- no read_back, no gloss
OntologyFact[atom, body, cites, gloss, inference, licence, toggleable]   <- gloss, no read_back
Concepts    [arity, cites, gloss, inference, licence, name, toggleable]  <- gloss, no read_back
```

Over the whole last run `[RAN]`:

| clause | claims | licensed items | items carrying a read-back sentence |
|---|---:|---|---:|
| `m0037` | 4 | 5 concepts | **0** |
| `m0053` | 3 | 2 concepts + 1 `defines` | **0** |
| `m0217` (patched) | 3 | 3 concepts + 1 `asserts` | **1** |
| `m0091` | — | `status: "unrepaired"` — never reached stage 2 | — |

**One English sentence, over four clauses.** Any stage-4 design that assumes an authored read-back
per item has no artifact to run on. §2 is written to that fact.

`[RAN]` Related, and it is an Invariant-1 hole rather than a stage-4 one: `m0053`'s single content
item is `defines(m0053, assistant, interactable_entity).`, and `grep -rn interactable_entity` over
the run directory finds the term **only** in that fact. It has no gloss, is in no concept table,
and is defined by no clause. `Definition` has no `gloss` field, so there is nowhere to put one.

**(5) `[RAN]` Glosses today are 71–100 % verbatim clause vocabulary.** For patched `m0217`,
fraction of gloss words occurring in the clause quote: `political_content` 0.71,
`broad_audience` **1.00**, `exploits_individual` 0.93 — and `broad_audience`'s gloss is a literal
substring of the clause. So expanding definitions into the read-back, *with the glosses the
translator currently writes*, reproduces the clause almost word for word. That is seat 4d's
documented blind spot ("wording that echoes the clause") applied to seats 4b and 4d at once, and it
is measured, not hypothesised. §4 is built on it.

---

## 1 Scope

### What stage 4 does

Given one module that passes **stage 2 as it stands today**, its concept table, its clause text at
link scope, and its stage-3 output:

| | | model? |
|---|---|---|
| **4r** | **Render the read-back** — a deterministic English rendering of every content item and of each stage-3 derivation, with concept **definitions substituted for labels** (Invariant 1) | no |
| **4a** | **Author check** — the translating model, shown its own module and the rendering: *is this what you meant?* | yes |
| **4b** | **Clean check** — a fresh seat, shown clause + rendering and **never the code**: *does the rendering assert anything the clause does not support?* | yes |
| **4c** | **Source check** — per licensed item, shown that item and the text of the clause it cites: *does this clause license this?* Routed by licence class | yes |
| **4d** | **Completeness** — shown the clause and **all** renderings across the stage-3 covering set: *which of the clause's claims does no rendering convey?* | yes |
| **4v** | **Validate and route** — coverage, `unclear` rate, divergence triage, origin-filtered findings | no |

### What stage 4 does not do

- **It does not decide whether the document is ambiguous.** Seat disagreement is a brief defect
  until triaged otherwise (§6), and stage 4's output schema has no field in which a document-side
  finding can be written.
- **It does not judge behaviour or relevance.** No behaviour text enters any seat, per the
  namespace ruling (`STATE.md` NEW-2) that `schema.BEHAVIOUR_NS` already enforces at generation
  `[READ]`.
- **It does not certify the clause correct.** Part 7: correctness is not local. A per-clause stage-4
  pass rate reported before stage 9 overstates the result, and this stage adds nothing to that.
- **It does not repair.** It emits findings; §5 says which of them may be shown to a translator and
  which may not.
- **It cannot detect a claim that is encoded but inert.** §3's failing example. It borrows a
  deterministic number from stage 3 to compensate, and reports when that number is unavailable.

### Which of Part 1's failure modes it addresses

| | | stage 4 |
|---|---|---|
| **#1 invented entity** | ⭐ **addressed by 4c, not 4b.** 4b's structural blind spot is imports: the clause does not enumerate what exists, so a fabricated sibling policy reads as fine. This is the design's recorded n=1 (a clean reviewer passed a fabricated *"deception policy"* on a clause reading *"policies other than restricted or sensitive"*) |
| **#6 miscited fact** | ⭐ **addressed by 4c**, the per-item seat, and only there |
| **#8/#9 concept identity** | ⭐ **the whole point of 4r.** Rendering the definition rather than the label is what moves a cross-clause problem into a single-clause check. ⚠️ **Only as far as the glosses are meaningful — finding (5) says today they are not** |
| **#5 hollow stub** | ⛔ **not addressed and must not appear to be.** The rendering echoes the clause's own words, so it reads faithful and sufficient while carrying none of the referenced section's content. `01_which_checks_are_scripts.md` §E is explicit that no judge comparing against the clause can help; the answer is deterministic opaque-stub detection, which `CONFORMANCE_REVIEW.md` records as **absent** |
| **#12 one branch only** | **partly.** 4d is shown the whole covering set, which is what makes it possible. But 4d checks that a claim is *conveyed*, not that it is *load-bearing* — §3 |
| **#14 claims no case can demonstrate** | **counted, not judged.** `forbid_body` declarations have no derivation and no read-back; they are excluded from 4a/4b/4d denominators by name and reported separately, or a clause whose only gap is a `forbid_body` claim reports full coverage |

---

## 2 ⭐ The read-back itself, before any seat

All four seats judge one artifact. If it is wrong they are wrong together, and four agreeing seats
read as confirmation. So the rendering is specified first and checked deterministically first.

### 2.1 What is rendered

Three layers, each a distinct artifact with its own denominator:

| layer | one per | source |
|---|---|---|
| **R1 item rendering** | every licensed item (`concepts`, `ontology`, `defines`, `asserts`, `beats`) | composed by the renderer |
| **R2 rule rendering** | every `asserts` / `beats` | composed by the renderer **and** the model's authored `read_back` — two independent renderings, diffed |
| **R3 derivation rendering** | every stage-3 covering-set situation with a non-empty derivation | xclingo explanation tree, every leaf replaced by its R1 rendering |

### 2.2 ⭐ RULING: the rendering is composed by the renderer, not asked of a model

The model's `read_back` is kept and **demoted to a second opinion**. Grounds:

1. Finding (4): 11 of 12 licensed items in the last run have no authored `read_back` at all. A
   design that asks the model for one requires a schema change, a re-run, and a new spend — and it
   puts the artifact all four seats depend on into the hands of the seat the design calls the
   weakest.
2. Polarity is the recorded killer. `m0217`'s rule body is `not exploits_individual(M)` and its
   authored sentence says *"and does not exploit…"* — correct here, and unverifiable in general.
   `WALKTHROUGH_REPORT.md` iteration 2 is exactly this failure with the sign wrong: a right verdict
   with a reason the program could not support. A renderer that walks the rule's own structure gets
   polarity **by construction**; a prose author gets it by luck.
3. Two renderings of one rule cost nothing extra and disagree usefully. The mechanical rendering is
   what the seats see; the authored one is diffed against it, and a divergence is a **stage-4
   structural finding about the module**, disclosable to a repair loop (§5) because it names no
   expected verdict.

**Rejected by name:** *(a)* **"ask the model to write the expanded read-back"** — it re-creates
finding (4)'s dependency, costs a call per item, and the artifact is authored by the seat that is
measurably biased toward its own output; *(b)* **"render only the rules, skip the facts"** — that
gives `m0037` and `m0053` an empty read-back set and a vacuous pass, which is §3's second failing
example; *(c)* **"drop the authored `read_back` field"** — it is the only independent signal about
whether the mechanical rendering matches the author's intent, and removing it makes 4a's job
unfalsifiable.

### 2.3 The composition rules

Templates, one per item type. Every predicate name is replaced by its gloss; **no bare predicate
name may survive into the English.**

```
concept   c/n, gloss g          -> "«g»"                              (the definition IS the item)
ontology  a(x) :- b, gloss g    -> "«x» is «g»" / "… when «gloss(b)»"
defines   defines(C,K,T)        -> "clause C brings «gloss(T)» under «gloss(K)»"
asserts   asserts(C,S,A) :- B   -> "clause C «status(S)» «act(A)» when «B rendered»"
beats     beats(S,W,L) :- B     -> "clause S says clause W outranks clause L when «B rendered»"
body      p(X), q(X), not r(X)  -> "«gloss(p)» and «gloss(q)» and it is NOT the case that «gloss(r)»"
```

`status/1` is a fixed four-entry table (`forbid` → *forbids*, …); `act/1` renders the act term from
the module's `acts` declaration. The negation marker is emitted from the rule's own `not`, never
from prose.

⛔ **Two templates cannot be written today**, and that is a finding rather than a blocker:
`defines` has no gloss for its `term` (finding 4: `interactable_entity`), and `Definition` has no
field to hold one. The renderer therefore emits a **`readback-ungloss` ERROR** naming the symbol,
and the clause does not proceed to any seat. It fires on `m0053` today, which is the point — a
symbol with no written definition cannot have its definition rendered, and the current behaviour is
to render its label and say nothing.

### 2.4 ⭐ How a bad read-back is detected, before any model call

Five deterministic checks. Each is cheap and each has a failure it is named for.

| | check | the failure it catches | on the current corpus `[RAN]` |
|---|---|---|---|
| **RB1** | **no label survives.** No predicate name, functor, `/arity` signature or clause id from the module may appear in a rendered sentence except as the explicit clause reference | Invariant 1's whole subject. `restricted_content still binds` is today's live instance | would fire on all four `m0255` trace sentences |
| **RB2** | **every gloss is present.** Every predicate occurring in a rule's body has its gloss substring in that rule's rendering | a renderer that drops a condition — silent under-rendering, and 4b would pass the weaker sentence | — |
| **RB3** | **polarity count.** #negation markers in the rendering == #`not` in the body | iteration 2, mechanised | — |
| **RB4** | **⭐ echo score.** Token overlap of each rendering against the clause quote, reported per item and per clause | finding (5). At overlap ≈ 1.0, 4b and 4d cannot discriminate at all: they are comparing the clause to itself | `broad_audience` **1.00**, `exploits_individual` 0.93, `political_content` 0.71 |
| **RB5** | **non-empty denominator.** A module whose rendered set is empty is `no-readable-content`, an outcome, never a pass | finding (4)/§3b. `m0037` renders zero rules | fires on `m0037` |

⭐ **RB4 is reported, never used to fail a clause.** A threshold on an echo score is a scoring
instrument, and this repo's standing rule is that a search whose objective is a model judgement is
unsafe (open question 3). What it does instead: **above a declared echo level, this clause's 4b and
4d verdicts are stamped `non-evidential` in the report.** They still run, they are still recorded,
and they may not be counted as evidence that the translation is faithful. That is the honest use of
a number that says *the two texts I am comparing are the same text*.

---

## 3 A specific PASSING example, and a specific FAILING one

### 3a PASSING — patched `m0217`, seat 4b

`[RAN]` The rendering the renderer composes for the module's single rule, from the module and
`concepts.json`:

> Clause m0217 **permits** producing the material when it is content that concerns political topics
> or subjects such as a politician, party or campaign, **and** it is content crafted for an
> unspecified or broad audience, **and it is NOT the case that** it exploits the unique
> characteristics of a particular individual or demographic for manipulative purposes.

Deterministic gates: RB1 passes (no `political_content/1` in the text), RB2 passes (3 of 3 glosses
present), RB3 passes (1 negation marker, 1 `not`), RB5 passes (1 rendering), RB4 reports **0.88
mean echo — high, verdict stamped `non-evidential`**.

Seat 4b sees the clause quote and that sentence, never the module. Correct verdict: **faithful**.
The clause says exactly this. 4c sees the one `asserts` item and `m0217`'s text under the `textual`
question — **licensed**. 4d sees the clause and the covering set's renderings, and correctly reports
`C3` (*"applies regardless of the political topic"*) as **not conveyed**: nothing in the rendering
distinguishes one political topic from another, because the module encodes no such distinction.

⚠️ That 4d finding is a **true positive that should not drive a repair**: `C3` is a scope
restatement, not a separable condition. It is a `readback-incomplete` note routed to a human, which
is why §5 separates structural findings from repair-driving ones. And the whole example is stamped
`non-evidential` by RB4, so what it demonstrates is that the machinery runs — not that `m0217` is
faithful.

### 3b ⭐ FAILING — a seat reports faithful and is wrong

**Primary instance, measured in this repo: `m0255` claim C3, and seat 4d passes it.**

`FINDINGS_m0255.md` `[READ, and its commands re-run]`: the two rules encoding C3
(*"purpose never creates an exemption"*) can be deleted and every answer set is identical — 144 of
144, and **UNSAT** for any situation where a C3 body holds and `binds` is not already derived, over
a widened generator of 331,776 models. Both rules **fire**, with 36 witnesses each, so every
rule-coverage criterion passes them. They carry `%!trace_rule` annotations naming C3.

Now run stage 4 on it. 4d is shown the clause and all the renderings; two renderings say, in
English, that purpose does not create an exemption. **4d reports C3 covered. 4d is right about the
artifact and wrong about the module.** 4a, shown its own module, agrees — the rules are there. 4b,
shown clause and rendering, agrees — the sentence matches the clause. 4c, shown the two items and
their citations, agrees — `m0255` does say it. **All four seats pass, unanimously, and the claim is
carried entirely by a different rule.** The unanimity is the confirmation illusion §4 exists for.

> `FINDINGS_m0255.md`'s own sentence, which is the whole failure in one line: *"A redundant encoding
> of a claim reads as an encoding of the claim."*

**What follows, and it is load-bearing:**

⭐ **4d's `covered` verdict on a claim is not accepted unless stage 3 reports at least one
situation that discriminates that claim.** `STEP_stage3.md` §6 already computes exactly this — its
test 6 is *"deleting `m0255`'s two C3 rules → `C3: uncovered` under discrimination coverage"*,
`[RAN]` there and re-run here. So the cross-check costs nothing new; it is a join between two
outputs that already exist. Where the numbers disagree — 4d says covered, stage 3 says not
discriminated — the item is recorded **`covered-but-inert`**, which is a finding about the module
and is disclosable.

⛔ **And where stage 3 did not run, 4d's `covered` is stamped `unsupported`, never `pass`.** A
clause carried to stage 4 as `probe-mismatch` or `no-testable-content` has no discrimination
number, so the cross-check is unavailable — and an unavailable check must not read as a passed one.

**Second instance, and it is the design's own n=1: seat 4b passes a fabricated policy.** The clause
reads *"policies other than restricted or sensitive"* and never enumerates which policies exist.
A translation inventing `policy_class(deception, other)` renders as a fluent English sentence that
the clause fully supports, because the clause's own words license "other policies" in the abstract.
4b's context contains nothing that could reveal the invention — this is its structural blind spot,
not a lapse. Only 4c catches it, by asking which clause licenses `deception` being a policy, and
`m0255` does not. ⚠️ **`m0255` also rests on `protects_third_party(restricted_content)`, which is
`world`/`assumed` and asserted, not read** — and §5's denominator routes exactly that item away
from the `textual` question that would wrongly reject it.

**Third instance, cheapest of the three: `m0037` passes everything by being empty.** `[RAN]`
`m0037` has 4 claims, 5 concepts, zero asserts/defines/ontology/beats, renders zero rules, and
passes stage 2 with **0 findings**. Without RB5 its 4a/4b denominators are 0, its 4c denominator is
5 gloss items that each restate one clause fragment, and its 4d question is *"do these zero
renderings convey the clause's four claims?"* — the one question in stage 4 that would actually
fire, if 4d is not accidentally handed the `claims` list as though it were the rendering. RB5 makes
it `no-readable-content` before any seat is paid.

---

## 4 ⭐ What it looks like when the check is measuring the wrong thing

The named risk is four seats agreeing for one shared wrong reason. There are three shared reasons
available, and each gets a structural answer rather than an instruction.

### 4.1 Shared reason A — they all read the same rendering

**Answer: one seat is not downstream of it.** 4c is shown **the licensed item and the cited clause
text**, and no rendering at all. If 4r is systematically wrong — a mis-substituted gloss, a dropped
condition, a flipped polarity — 4a, 4b and 4d can all be wrong together and **4c is unaffected**.
That makes 4c the anchor, and it is why 4c is also the seat scarce human calibration is spent on
(Part 7, and open question 4's warning that human reliability on link vetting must be measured
*first*).

⇒ **Enforced, not stated:** the seat-4c prompt builder takes the module and the corpus text and has
no parameter through which a rendering could be passed. Test 12.

### 4.2 Shared reason B — the rendering echoes the clause

Finding (5), measured: glosses are 71–100 % verbatim clause vocabulary. When the rendering is the
clause, 4b's question (*does the rendering assert anything the clause does not support?*) and 4d's
question (*does the rendering convey the clause's claims?*) both answer themselves. This is 4d's
documented blind spot, and the measurement shows it reaches 4b too.

⇒ **Answer: RB4, and the `non-evidential` stamp (§2.4).** Not a threshold that fails the clause —
a label on the verdict that forbids counting it as evidence. A run in which most clauses are
`non-evidential` is a finding about the **glosses**, routed to Invariant 1 / open question 2, which
is where it belongs.

### 4.3 Shared reason C — unanimity is read as confirmation

§3b is the worked case: four seats, four correct-about-the-artifact verdicts, one worthless module.

⇒ **Answer, in three parts, all mechanical:**

1. ⭐ **No aggregate.** The report carries four per-seat verdicts and **no consensus field, no
   score, no `n_passed`**. There is nowhere to write "4/4 agreed". Test 15.
2. ⭐ **4a is never evidence.** The design says so; the report enforces it by placing 4a's verdict
   in a separate `advisory` block that the pass/fail line does not read. A cheap first pass whose
   output feeds nothing but a human's attention.
3. ⭐ **The one cross-check that is not a model judgement** — 4d `covered` against stage 3's
   discrimination count (§3b) — is the only place a seat verdict is confirmed by something outside
   the seat system. Where it is unavailable, the verdict says so.

⚠️ **What remains uncovered, stated rather than left for a reviewer.** All three answers protect
against seats agreeing *wrongly*. None of them detects seats agreeing *correctly about a rendering
that is faithful to a module that is faithful to a clause the pipeline has misunderstood at the
document level*. That is stage 5 and stage 9 work, and stage 4 must not be reported as reaching it.

---

## 5 The coverage rule and the denominators

⭐ **The denominator is computed from the translation, never supplied by the judge**
(`03_pipeline.md`). The design records the prerequisite as **unmet** — *"facts do not carry
licences yet"*. `[RAN]` **it is now met**: `schema.Licensed` is inherited by `Concepts`,
`OntologyFact`, `Assertion`, `Superiority` and `Definition`, and validation enforces
`textual`→`cites`, `assumed`→`inference`, `world`→`toggleable`. The coverage rule can therefore
exist for the first time, and this section is what it computes.

### 5.1 The four denominators

| seat | denominator | on the last run `[RAN]` |
|---|---|---|
| **4a** | the rendered set (R1+R2+R3) | 5 / 3 / 4 items for `m0037` / `m0053` / patched `m0217`; 0 / 0 / 1 **rules** |
| **4b** | the rendered set, minus items whose licence is `world` | same, no `world` items exist yet |
| **4c** | **every licensed item**, partitioned by licence class | **12 items over 3 modules — all `textual`, 0 `assumed`, 0 `world`** |
| **4d** | the module's **`claims`** list | **10 claims over 3 modules** |

⭐ **RULING: `Concepts` are in 4c's denominator.** A concept row carries `licence: textual,
cites: m0037` — that is an assertion that the clause says the term means this, and it is judgeable
under exactly the `textual` question. **Rejected by name:** *"concepts assert nothing, so exclude
them"* — true of the logic and false of the licence. `[RAN]` excluding them makes `m0037`'s 4c
denominator **0** and `m0053`'s **1**, i.e. the two modules whose entire content is vocabulary
would pass the provenance seat vacuously. The whole run's 4c denominator drops from 12 to 1.

### 5.2 Routing by licence class (seat-contract element 7)

| licence | the question 4c asks | count today |
|---|---|---:|
| `textual` | does the cited clause **contain** this? | **12** |
| `assumed` | does the clause **license** this inference, and is the inference named? | **0** |
| `world` | ⛔ **not judged by 4c.** A deterministic check that it is marked and toggleable — `schema.Licensed` already enforces both `[RAN]` | **0** |

⚠️ **Two of the three branches have no live case, and the slot is built anyway** — open question 5's
ruling is explicit that retrofitting routing into a brief that has already produced results
invalidates those results. The branches will arrive: `m0255`'s working derivation rests on
`protects_third_party(restricted_content)`, which is `world`/`assumed` and which no
schema-produced module has yet reproduced.

### 5.3 The validator, one for every per-item seat

Parameterised by how its denominator is computed, exactly as the design says.

| check | catches |
|---|---|
| every item in the denominator has exactly one judgement | silent skipping — and the skipped ones are the hard ones |
| no judgement names an id not in the denominator | a hallucinated item, or a mispaired artifact |
| every judgement carries a non-empty reason | an `unclear` with no reason is a skip in disguise |
| the denominator is non-empty | RB5. A vacuous 100 % is the failure this whole document is about |
| a run failing any of these is **not adjudicated** | hand-fixing, which is where results quietly change |

### 5.4 What an `unclear` rate is for

`unclear` is a closed verdict in every seat's response schema (element 3, ≈ free at generation).
Its rate is **not** evidence about the document. Under the divergence rule it is evidence about the
**brief or the artifact**, and it is read that way:

- a high `unclear` rate on **one seat** ⇒ that seat's brief is under-informative;
- a high rate on **one clause across seats** ⇒ the rendering is bad — check RB1–RB4 for that clause;
- a high rate **everywhere** ⇒ the rendering design is bad, and no verdict from the run counts.

⚠️ **Coverage is necessary and not sufficient**, in the design's own words: a judge can comply fully
and answer `unclear` on every hard item. Coverage passes; nothing was learned. The rate is what
makes that visible, so it is a required field, printed even when zero.

### 5.5 ⭐ What a stage-4 finding discloses, and what it withholds

`checks.Finding.origin` is required, positional and never defaulted `[READ]`; the filter is built —
`[RAN]` `translate.DISCLOSABLE_ORIGINS == ('schema', 'link')`, and `render_error_log` emits
`(N finding(s) withheld: they come from a later stage and would disclose an expected answer)`.
Stage 4 must say which side of that fence each of its findings sits on.

| origin | contains | disclosable | routes to |
|---|---|---|---|
| `readback-structural` | RB1–RB5 failures, `readback-ungloss`, the R2 mechanical-vs-authored diff | ⭐ **yes.** Derived from the module and the concept table alone; no seat has spoken; no expected verdict exists anywhere near them. Added to `DISCLOSABLE_ORIGINS` | the accumulating repair transcript |
| `seat-4a` | the author's own verdict on its own module | ⛔ **no** — and not because it leaks. It is the seat the design calls *"never evidence"*, and feeding it back is the model grading itself into a loop | the `advisory` block, and a human |
| `seat-4b` / `seat-4d` | *"the rendering asserts X, which the clause does not support"* / *"claim C₂ is conveyed by no rendering"* | ⛔ **no.** Both name what the right answer would have been. *"C₂ is not conveyed"* handed to a translator is an instruction to encode C₂ | not the transcript — §5.6 |
| `seat-4c` | *"item i's citation does not license it"* | ⛔ **no.** Same shape: it names the item and the direction of the error | not the transcript — §5.6 |
| `covered-but-inert` | 4d says covered, stage 3 says not discriminated | ⛔ **no.** It is a 4d verdict wearing a structural coat | §5.6 |

### 5.6 ⭐ RULING: a seat finding discards the transcript and re-translates from a clean prompt

Up to `max_retranslations` (default 1), then the clause is recorded `status: "readback-<seat>"` and
carried, unrepaired, to a human. This is the same ruling `STEP_stage3.md` §5 made for
`probe-verdict`, for the same reason and with the same three alternatives rejected by name:

- ⛔ **"append the seat finding to the transcript"** — the transcript is persistent per clause, so
  one appended finding lives there for the rest of that clause's life;
- ⛔ **"disclose the item but not the verdict"** — for a binary-shaped item, naming it *is* the
  verdict;
- ⛔ **"pass a count of seat findings back"** — a count plus an unchanged module is a hill-climbing
  signal against a hidden answer key, which is the anti-cheat perimeter the wider repo defends.

Re-translation carries no information from the finding at all. That is the point: one stage-1 call,
zero bits.

---

## 6 Divergence — enforced, not stated

*"Diverge" means opposite verdicts, not different words* (`03_pipeline.md` §6). Two seats phrasing
the same judgement differently is expected and uninteresting.

⭐ **The enforcement is structural: there is no route by which stage 4 can emit a document-side
finding.** The output schema's finding types are the six in §5.5, plus `seat-divergence`. There is
no `ambiguity`, no `interpretation`, no `document-finding` field. A divergence therefore cannot
become a claim about the document by being written down, because there is nowhere to write it.

When two seats reach opposite verdicts on one item:

1. the item's verdict is recorded **`unclear`**, never resolved by fiat and never by a third seat
   acting as tie-breaker;
2. a `seat-divergence` record is emitted carrying the item id, both verdicts, both reasons, and the
   **sha of each seat's brief and of the rendering** — so the two diagnoses the design names first
   (ambiguous question, under-informative dossier) are checkable against the artifacts that
   produced them;
3. the record is `not adjudicated` until a human has triaged it as brief-defect or not, and the
   triage is written into the run record with its grounds;
4. **only then**, and only by a separate human-signed step, may an alternative reading enter the
   project's interpretation registry — which carries the anti-fitting constraints this design lacks
   (sha-pinned frozen set, adoption on document-side grounds only, one recorded vector never a
   grid, blind adoption including the proposal queue).

⚠️ **The design's preferred mechanism does not apply here and this plan says so.** §6's *"hold both
readings and enumerate the situations where they decide differently; empty set ⇒ immaterial"* is
native to ASP and is exactly right for **two translations** (stage 10). Two *seats* disagreeing
about a paraphrase produce no second program to enumerate against. Borrowing the sentence without
the mechanism would be self-report dressed as a deterministic check. Where a divergence can be
reduced to two candidate modules, stage 10's machinery is used and the enumeration is run; where it
cannot, step 3 above is the whole procedure and is recorded as a weaker one.

⚠️ **Also recorded: `unclear`-vs-`faithful` is not a divergence.** Only `faithful` vs `unfaithful`
is a contradiction in content. Firing seat-defect review on a seat that abstained would punish the
honesty the closed-verdict set exists to permit, and would make `unclear` the expensive answer.

---

## 7 Cost

**Model tier.** ⛔ **These seats are not validated.** The project rule is a small model for
*validated* judgement seats, and divergence from a frontier model on the same brief is a seat
defect. Stage 4 has n=1 evidence on one seat and none on three. ⇒ **The first run uses a frontier
tier on 4b, 4c and 4d, and the translator's own model on 4a** (4a must be the author, that is what
the seat is). A small-model parity run against the same briefs and the same rendering is the
evidence that would license dropping the tier; until it exists, the tier is not dropped. At four
clauses the difference is cents either way, so there is no reason to economise on the one axis that
would invalidate the result.

**Unit prices** `[READ]` `config.json`: DeepSeek-V4-Flash **$0.14 / $0.28 per Mtok**, input billed
at the full rate (the config declines to claim the cached rate). Frontier-tier seats are priced
from `providers.json` at run time; the estimate below is given at both.

**Per clause**, using the measured artifact sizes `[RAN]` (`m0217` user block 1,173 B, `m0037`
331 B, `m0053` 348 B, `m0091` 5,341 B; `.lp` files 976–1,875 B; clause quotes 143–646 chars):

| seat | calls | input | output |
|---|---:|---|---|
| 4a author | 1 | brief ~700 + module ~600 + rendering ~300 | ~150 |
| 4b clean | 1 | brief ~700 + clause ~200 + rendering ~300 | ~200 |
| 4c source | 1 **batched** | brief ~900 + Σ(item + cited clause text) ~1,400 for 4 items | ~80 × items |
| 4d completeness | 1 | brief ~800 + clause ~200 + all renderings ~600 + claims list | ~250 |
| | **4** | **≈ 6,700 tok in** | **≈ 950 tok out** |

⭐ **4c is batched per clause, not per item** — the coverage rule requires the seat to see the whole
denominator anyway, and per-item calls would multiply the clause context by the item count.

**Per clause: ≈ $0.0012** at flash rates. **A four-clause run: ≈ $0.005**, plus at most one
re-translation per clause at the measured translation cost `[RAN]` ($0.001085 for `m0217`) — call
it **under $0.01 all in.** At frontier rates, roughly 20–40×: **$0.10–$0.20** for the four-clause
run. Against `[RAN]` `spend.py`: **$2.057 of $8.50 used (24 %)**. Stage 4 at four clauses is not a
budget question at any tier.

⚠️ **At 593 clauses it becomes one:** ~$0.7 at flash rates, ~$25 at frontier — **over the ceiling**.
So the tier decision above is explicitly a *first-run* decision, and corpus-scale stage 4 is blocked
on the small-model parity measurement, not on a preference.

⚠️ **The honest four-clause picture, from the same table as §0(4):** of the last run's four clauses,
`m0091` never reached stage 2, `m0037` is `no-readable-content` (RB5), `m0053` halts at
`readback-ungloss` (§2.3), and `m0217` needs a fixture patch to validate. **Stage 4 as designed
would today pay for exactly one clause**, and a pipeline reporting *"3 of 4 passed stage 4"* over
that run would be reporting that three clauses had nothing to read back.

⛔ **Nothing in this plan is authorised to spend.** Build and test offline against the committed run
outputs and hand-built fixtures; a `--live` seat run is a separate decision.

---

## 8 The TDD test list

`walkthrough/paper_pipeline/phase_1/test_readback.py`. Fixtures built through `schema.validate()` +
`render_lp()`, as `test_link.py`, `test_checks.py` and `STEP_stage3.md` require — **not** the
committed `.raw.txt` or `.lp` files, which §0(1) shows were produced under a superseded contract.

⚠️ **The bar.** `[RAN]` `mutate_schema.py` mutates **45 guards** in `schema.py` and exits 0 —
*"every guard is pinned by at least one test"*, with *"65 of 66 tests killed by a narrow mutation
killed by exactly one (a clean 1:1 pin)"*. A mutation run today found 21 of 46 guards in a sibling
module surviving deletion with every test passing; that is now 0. Stage 4 ships with its own
mutation run at 0 survivors or it does not ship. **Every row below names a paired negative control that must stay SILENT**; a check that fires
on everything is pinned by nothing.

| # | must FIRE on | the paired control must stay SILENT on | why the control is the real test |
|---|---|---|---|
| 1 | RB1: a rendering containing `political_content` or `political_content/1` | a rendering containing only glosses | §2.4. The label surviving into the English **is** Invariant 1's failure |
| 2 | RB2: a rendering that omits one body predicate's gloss | a rendering carrying all three | a dropped condition renders as a *weaker, true* sentence, which 4b passes |
| 3 | RB3: a body with one `not` rendered with zero negation markers | one `not`, one marker | iteration 2. `[RAN]` `m0217` is the live 1-and-1 case |
| 4 | RB4: the echo score is **present in the report even when low** | a low-echo clause must not acquire a warning | a warning on every run becomes invisible — `link.py`'s own recorded lesson |
| 5 | ⭐ RB4 ≥ threshold ⇒ 4b/4d verdicts stamped `non-evidential` **and still recorded** | below threshold ⇒ no stamp, same verdicts recorded | §4.2. A design that *drops* the verdicts hides the measurement that produced the stamp |
| 6 | ⭐ RB5: `m0037` (0 rules, 5 concepts) ⇒ `no-readable-content` | patched `m0217` ⇒ proceeds | §3b third instance. `[RAN]` `m0037` passes stage 2 with **0** findings |
| 7 | `readback-ungloss`: `defines(m0053, assistant, interactable_entity)` ⇒ ERROR naming the term | a `defines` whose `term` has a concept row ⇒ renders | §2.3. `[RAN]` the term exists nowhere else in the run |
| 8 | ⭐ 4d `covered` on a claim with **0** discriminating stage-3 situations ⇒ `covered-but-inert` | 4d `covered` with ≥1 discriminating situation ⇒ plain `covered` | §3b, the `m0255` C3 case. `[RAN]` 144/144 answer sets identical, subsumption UNSAT over 331,776 models |
| 9 | ⭐ 4d `covered` when **no stage-3 output exists** ⇒ stamped `unsupported` | stage-3 output present ⇒ cross-checked | an unavailable check must never read as a passed one |
| 10 | a 4c prompt built with a rendering in it ⇒ refused at construction | a 4c prompt of item + cited clause text ⇒ allowed | §4.1. 4c is the anchor **because** it is not downstream of the rendering |
| 11 | a 4b prompt containing the module, the `.lp`, the JSON, or a rule body ⇒ refused | clause + rendering ⇒ allowed | *"4b must never see the logic"* — a reviewer shown the code grades the code |
| 12 | a 4d prompt containing the module's `claims` list **as the rendering** ⇒ refused | `claims` as the denominator, renderings as the material ⇒ allowed | §3b third instance: handing 4d the claims list makes every claim self-evidently conveyed |
| 13 | any seat prompt containing a behaviour, a panel label, or a stage-3 expected verdict ⇒ refused | clause + cross-references ⇒ allowed | `BEHAVIOUR_NS` at generation has no counterpart at review |
| 14 | ⭐ a `seat-4b`/`4c`/`4d`/`covered-but-inert` finding reaching `render_error_log` ⇒ withheld, hole visible | a `readback-structural` finding ⇒ **rendered in full** | §5.5. Both halves: a filter that withholds everything is as wrong as one that withholds nothing |
| 15 | ⭐ any consensus field, `n_passed`, or per-clause pass fraction in the output ⇒ refused at construction | four per-seat verdicts + 4a in `advisory` ⇒ allowed | §4.3. Unanimity read as confirmation is §3b's entire failure |
| 16 | a 4c denominator excluding `Concepts` ⇒ refused | denominator = concepts + ontology + asserts + beats + defines ⇒ allowed | §5.1. `[RAN]` excluding them takes the run's denominator from **12 to 1** |
| 17 | a judgement naming an id not in the denominator, a missing id, or an empty reason ⇒ **not adjudicated** | a complete judgement set with reasons ⇒ adjudicated | §5.3, the coverage rule |
| 18 | a `world`-licensed item appearing in 4c's judgeable set ⇒ refused | a `world` item checked deterministically for marked+toggleable ⇒ allowed | §5.2. `[RAN]` the deterministic half already exists in `schema.Licensed` |
| 19 | `faithful` vs `unfaithful` on one item ⇒ `unclear` + `seat-divergence` with both brief shas | `faithful` vs `unclear` ⇒ no divergence record | §6. Firing on abstention punishes the honesty `unclear` exists to permit |
| 20 | a `seat-divergence` promoted to a document-side finding without a recorded human triage ⇒ refused | promoted **with** triage grounds recorded ⇒ allowed | §6. The route must not exist, not merely be discouraged |
| 21 | the `unclear` rate absent from the report ⇒ refused | rate present and **zero** ⇒ allowed | §5.4. A field printed only when non-zero cannot be read as "we measured it" |
| 22 | the renderer handed a module whose body predicate is declared only as a `Concepts` entry ⇒ never reached, because stage 2 rejects it `[RAN]` | the patched `m0217` fixture ⇒ renders | §0(1)/(2). Stage 4's fixtures depend on that stage-2 guard; it **is** pinned (two tests), so this row asserts the dependency, not the guard |

⚠️ **Three of these pin things that must be built in the same diff, not after:**
`DISCLOSABLE_ORIGINS` gains `readback-structural` (test 14); the new module registers in
`test_no_reference_leak.QUERY_MODULES`-equivalent fencing and `conftest._OPTIONAL` for its tests;
and `checks.SEVERITIES` is **not** extended — read-back findings are `error`/`note` like every
other. Registration, not documentation, fences a module.

---

## 9 What this plan is least sure of

⚠️ **That a mechanically composed read-back is readable enough to judge.** §2.2 takes the rendering
out of the model's hands, on evidence (polarity, finding (4)). The cost is that gluing glosses
together with *"and"* and *"it is NOT the case that"* produces prose that is correct and ugly, and
a seat given a four-condition rule may return `unclear` because the sentence is hard to parse —
which §5.4 would then read as a brief defect when it is a **renderer** defect. The two are not
distinguishable from the `unclear` rate alone.

The mitigation is a measurement, not an argument: the first run reports the `unclear` rate **split
by rendered-sentence length and condition count**, and a rate that rises with length is a renderer
finding, investigated as one before any conclusion is drawn about a brief or a translation. If it
does rise, the fallback is the *pair*: the model's authored `read_back` shown alongside the
mechanical one, with the diff already computed — but that gives the seats two texts to reconcile
and re-opens §4's shared-reason problem from a different direction, so it is not the default.

⚠️ **Second, smaller.** §3b's cross-check makes 4d's most valuable verdict depend on stage 3, which
is itself only a plan. If stage 3 ships without the discrimination number, test 9 fires on every
clause and 4d degrades to `unsupported` everywhere — correct behaviour, and a stage-4 whose best
check never runs.
