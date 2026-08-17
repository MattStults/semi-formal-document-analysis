# CRITERIA — how the 25 reference modules were judged, written to be transplanted

Companion to `PASS1.md` (blind span reads), `modules/` (the reference corpus) and `diffs.json`
(26 edits with class, before, after, grounds). This file is about the **instrument**, not the
result: the sequence actually used, the discriminating question per defect class, the places the
judgment nearly went wrong, and what a seat would have to be shown to reproduce it.

⚠️ **DISCLOSURES, both of which limit how far this transfers.**
1. **I was not blind to the anchor's verdicts.** The brief gave me
   `spotcheck_semantic/verdicts.json` as a control, and I read the id/verdict/mode table before
   Pass 1. I did not read any module before Pass 1, and I did not read the stage-4 verdicts or the
   golden mutants at all. But "13 of these 25 are defective" was in my context throughout, and a
   seat will not have that.
2. **`l1_170_n056.json` was opened once before Pass 1**, to learn the file format. Its Pass 1 entry
   is not strictly blind.

---

## 1. The decision procedure actually used, in order

### Stage 0 — learn the target language before reading anything to be judged (~15 min, once)

Read `schema.py` (`Licensed`, `Assertion`, `OntologyFact`, `Concept`, `Closure`, `ForbidBody`,
`Module._coherent`), `checks.py` (`run_checks`, `polarity_mismatches`) and
`prompt/10_output_format.md`. This was not preparation, it was **load-bearing**: four of my
findings and three of my *non*-findings turn on schema facts I could not have guessed.
`toggleable` is reserved for `world` facts, so "By default" cannot be marked toggleable. A
variable act with a null body is rejected, so `forbid X(R) :- X(R)` is the only legal shape and is
not a defect. Several ontology rules with one head **is** a disjunction, so
disjunction-as-conjunction is a defect and not an expressibility limit. A judge that does not know
these will report forced constructions as errors and miss the real ones.

### Stage 1 — BLIND. All 26 spans, no modules. (`PASS1.md`)

I extracted the 26 `prompt_user.txt` files into one file and read them in a single pass, with no
module open. Per clause, in this order:

1. **Find the narrowing first.** `[node narrows this span to: ...]` — mark everything in the
   printed `L####` block that is *outside* it. Doing this first, before reading for meaning, is
   what made `l2405_2473_n001` and `l1108_1367_n027` obvious: their spans are a title line, and
   everything else on the page is context. Reading for meaning first makes the XML block feel like
   the clause.
2. **Find the main verb and its modal.** `must not` / `should` / `should avoid` / `may` /
   `is/are` / `we're exploring`. Write it down verbatim. This single token decides `forbid` /
   `oblige` / negative-with-E-1 / `permit` / no-assert / no-assert.
3. **Name bearer, act, trigger** as three separate things. If the bearer is not the model or the
   assistant, there is probably no norm here (`l1108_1367_n014`: every verb belongs to OpenAI;
   `l3954_4251_n023`: every verb describes what models *do*).
4. **Descend into the noun phrases and list every qualifier.** This is where scope lives, and it
   is the step most easily skipped because the sentence already "makes sense" without it.
   *"a **precise** recipe ... **that includes precise quantities, temperatures, or durations**"*;
   *"its chemical components **(without specific ratios or integration techniques)**"*;
   *"**only** relevant to Advanced voice"*; *"ambiguous statements **paired with** concerning
   details"*.
5. **Mark every AND and every OR, including inside the qualifiers.** *"quantities, temperatures,
   or durations"* is disjunctive; *"following explicit instructions and reasonably addressing
   implied intent"* is conjunctive; *"use a tool, hedge, or explain"* is disjunctive and is the
   whole content of `l3147_3238_n003`.
6. **Write the boundary — what a neighbouring sentence carries that this span does not.** For
   `l2821_3040_n002` that is "should express uncertainty"; for `l3147_3238_n003` it is three
   further norms in the same paragraph; for `l3239_3382_n002` it is "without overstepping".
7. **Predict the shape**: `asserts` entries with statuses, `ontology` entries, or abstention.

Then **save the file**. Everything after this is measured against it.

### Stage 2 — CORRECT. Module open, checks run in this fixed order

Per clause, and I did not vary this:

1. **`claims` vs `asserts`/`ontology` coverage.** Read the module's own `claims` list and, for
   each entry, point at the formal item that carries it. This is the cheapest defect detector in
   the whole exercise and it is already in every module: `l1_170_n056` lists *"C1 models should
   honor user requests"* and has no `oblige` anywhere.
2. **`asserts[*].status` against the modal I wrote down in Pass 1 step 2** — reading the `status`
   field and the `act` functor **only**, with the read-back covered up. See §3.1: this ordering is
   the single most important mechanical detail in this document.
3. **`asserts[*].body` against the trigger from Pass 1 step 3.** Wider, narrower, or absent?
4. **`ontology[*].body` against the qualifiers from Pass 1 step 4.** Every qualifier must appear
   in some body or the class is wider than the document's.
5. **Reverse direction: for every formal item, point at the span words that license it.** This is
   where invented obligations and out-of-span sourcing surface.
6. **Structure check:** disjunction encoded as several rules with one head, or as several
   co-triggered asserts (defect)?
7. **Hygiene:** a body that is its own head, a head that appears in its own body, a `requires`
   name used as an act.
8. **Run `schema.validate_all` + `checks.run_checks`.** Last, never first — it is a syntax gate,
   and all 25 originals except four passed it while carrying 26 semantic edits' worth of error.

### Stage 3 — decide what NOT to change

Minimal edits. Three explicit brakes, each of which stopped at least one edit: (a) is the existing
form *forced by the schema* (E-5, E-2)? (b) is there a **corpus convention** that makes it
acceptable — worked examples may be ontology-only, and the anchor rates two such modules FAITHFUL?
(c) is my objection about *taste* (predicate naming, structure) rather than about what the document
says? If (c), stop.

---

## 2. Per defect class — the discriminating question, as a procedure

Each is phrased so a weaker model can execute it without my context. The rule throughout: **make
it an enumeration or a comparison, never "does this look right".**

| class | the procedure |
|---|---|
| **dropped-obligation** | *Before seeing the module:* list every sentence in the span whose main verb carries `must` / `should` / `is required to`, and for each write `<bearer> is obliged to <act> when <trigger>`. *Then:* for each line, name the `asserts` entry with status `oblige` (or `forbid` for a prohibition) that carries it. Any line with no entry is a dropped obligation. **Also, for free: read the module's `claims` list and do the same mapping** — a translator that dropped an obligation usually still *listed* it. |
| **inverted-modality** | For each `asserts` entry, read **only** `status` and the act functor. Ask: *"does the document want more of this act, or less?"* `prefer`/`permit`/`oblige` mean more; `forbid` means less. Then check the act functor's name against the span. **Do not read `read_back` while doing this** — in all five real cases the read-back was correct and only the status was wrong. Additional rule for worked examples: the GOOD-marked and BAD-marked responses must not carry the same status on the same act. |
| **fact-as-deontic** | For every `asserts` entry, find the span sentence it came from and identify **the subject of its main verb**. If the subject is not the model/assistant — if it is OpenAI, users, developers, a website, a section, or a model *generation* — there is no norm here and the entry should be an ontology fact. Test phrase: can you rewrite the sentence as "X is required/permitted to Y" without adding words the span does not have? |
| **invented-obligation** | For each `asserts` entry, quote the span words that grant that status. If the quote needs the word "let", "exploring", "considering", "may sometimes encounter", or a hedge, it is not a grant. *"We're exploring how to let users generate X"* does not permit generating X. *"The assistant may sometimes encounter Q"* is not a permission — "may" here is possibility, not licence. |
| **weakened-modality** | For each `asserts` entry with status `prefer`, find the span's modal. `prefer` is legitimate **only** for a comparative — "minimize", "favour", "generally reduce", or a GOOD/BAD contrast. A bare "should" + bearer + trigger is `oblige`. Warning sign: the module's own `claims` list argues for the demotion ("C3 ... a preference, not a strict requirement") — that is the translator rationalising, not the document. |
| **scope-drift-widen** | Two sub-procedures, both needed. **(i) Qualifier check:** list every adjective, parenthetical and relative clause inside the span's noun phrases; for each, name the body literal that carries it. `precise_recipe(R) :- recipe_for_methamphetamine(R)` fails because "precise", "quantities", "temperatures", "durations" appear nowhere. **(ii) Span-membership check:** for every predicate name and every act, find the words in the **narrowed** span it comes from. If it comes from the printed context block outside the narrowing, it does not belong. |
| **scope-drift-narrow** | For each `asserts` body, ask whether adding that literal makes the rule fire in **fewer** cases than the span. Sub-case that reads as a strengthening and is not: a body added to encode "applies regardless of context" (`..., context(C)`) makes the rule *conditional* on a context fact and so weakens it. Rule: "regardless of X" is encoded by the **absence** of an X condition, never by adding one. |
| **disjunction-as-conjunction** | Find every "or" in the span. For each, check how the module encoded it. Correct: several `ontology` rules with **one shared head**, or several `asserts` with the **same act** and different bodies. Defect: several `asserts` with **different acts** and the **same body** — that says all of them are required at once. Test: construct a case satisfying exactly one disjunct and ask whether the module convicts it. |
| **prefer-polarity** | Mechanical, and `checks.polarity_mismatches` already does it — but its `_DISFAVOURED` regex misses "is to be avoided" and "is to be minimized" (it has "should be avoided"). Procedure for a judge: for each `prefer` assert, does the read-back sentence describe the act as something to do more of, or less of? If less, the status is wrong. |
| **dropped-content (general)** | Numbered-list discipline. From the span alone, number every distinct claim — including facts, inclusion cases, and both poles of a GOOD/BAD contrast. Then map each number to a formal item. Unmapped numbers are the finding. A concept that is **declared and never used in any body or declaration site** is the module's own fingerprint of a dropped item (`explicit_suicidal_or_self_injurious_intent`, `grown_up_mode_support`, `bad_response`). |
| **other / hygiene** | Three regex-cheap checks: (a) an `ontology` body whose first literal is the head's own functor — a rule that derives nothing; (b) a head functor appearing anywhere in its own body; (c) a name listed in `requires` or in the node's `NEEDS`/`PROVIDES` block being used as an **act term** in `acts`. ⚠️ Exception to (a): `asserts` with a variable act **must** have a body that binds the variable, so `forbid X(R) :- X(R)` is forced by the schema and is not a defect. |

---

## 3. Where I nearly went wrong — and what stopped me

These are the highest-value items in this file: each is a place where the *natural* reading passes
a defective module, so a cheap judge will go wrong here by default.

### 3.1 The read-back is where the correct meaning hides. `l4252_4482_n016`

I read `"read_back": "repeating the user's prompt in % is to be avoided"` and my first pass
registered it as correct — because it *is* correct. The error is one field away, in
`"status": "prefer"` on act `repeat_user_prompt(R)`. **The compiled program states a preference
FOR repeating the user's prompt.**

What stopped me: forcing myself to read `status` + `act` with the read-back covered. Having done
that, I found the second and third asserts are inverted the same way — `prefer
include_redundant_phrase(R)`, `prefer include_redundant_idea(R)` — which the anchor did not name
and which `checks.polarity_mismatches` does not catch (its regex has "should be avoided", these
say "is to be minimized").

> **Transplant:** any seat shown the *rendering* is structurally blind to this class, because the
> rendering is right. It is not a matter of the seat trying harder. This is the single clearest
> case in the set where the fix is what the seat is SHOWN, not how it is asked.

### 3.2 An extra rule that looks like a strengthening and is a weakening. `l831_1000_n005`

The module has a second `forbid` on the same act with body `precise_recipe(R), context(C)`,
plainly written to carry *"This prohibition applies regardless of context."* I nearly filed it as
harmless duplication. It is not: adding `context(C)` makes the prohibition fire only where some
context fact exists. What stopped me was reading every body as a **firing condition** rather than
as a comment — asking "in which cases does this rule NOT fire?" rather than "what does this rule
say?".

### 3.3 A verb that belongs to OpenAI. `l1108_1367_n014`, `l3954_4251_n023`

*"drawing a hard line against potentially harmful uses"* and *"models starting with GPT-5 prefer
Safe Completions"* both read as norms at speed. Neither is: the first is a subordinate clause
bounding OpenAI's exploration inside a `!!! meta Commentary` block; the second is a report about
what was built, in which "prefer" is an ordinary English verb that happens to collide with the
schema's status name. What stopped me: asking **who is the subject of the main verb** before
asking what the sentence requires. `l3954_4251_n023` is a lexical trap — the word "prefer" is
present, the status `prefer` is not licensed.

### 3.4 Over-correcting a module that is thin but not wrong. `l2126_2404_n039`

I had drafted a rule that every GOOD/BAD example must produce paired asserts, which would have
rewritten a module the anchor calls FAITHFUL. What stopped me: `l699_796_n022` is also a worked
example, is also ontology-only, and is also rated FAITHFUL. **Ontology-only rendering of an
example is a corpus convention, not a defect.** I withdrew the rule and made the minimal edit —
adding the BAD pole's discriminating property as an ontology fact. The general principle: before
promoting a preference into a rule, check whether the corpus already treats the alternative as
acceptable.

### 3.5 Two "defects" that are forced by the schema

* `l2555_2652_n001`: `forbid lie_to_reduce_anxiety(R) :- lie_to_reduce_anxiety(R)` looks like a
  textbook tautology. `_check_term(allow_vars=bool(body))` rejects a variable act with a null
  body, so this is the **only legal encoding** of an unconditional prohibition over a variable act.
* `l3041_3146_n006`: the anchor suspected `toggleable: false` on a "By default" rule.
  `Licensed._licence_obligations` raises *"toggleable is for `world` facts only"* — the translator
  had no choice. The real defect is elsewhere (the body carries no defeating condition).

> **Transplant:** a judge without the schema in front of it will file both as defects. Any seat
> asked about rule shape needs the relevant schema constraints, or an explicit "these forms are
> forced" list.

### 3.6 Reading order is not a preference

I nearly did the obvious thing — open module and span side by side. Had I done so, `l1_170_n056`
would have passed. `forbid honor_request(R)` on conflict with a higher-level instruction is
coherent, well-glossed, correctly cited, and passes every mechanical check. Nothing about it
prompts the question *"where is the obligation?"* That question only arises if the obligation was
written down **first**, from the span, with no module in view.

---

## 4. What I needed to see that the seats are not shown

Written against the golden-set measurements supplied by the coordinator. Each claim below is meant
to be re-scorable against the same 42 anchored items.

### 4c — 48/86 flags on FAITHFUL modules, 14/14 borrowed-name controls. Structural, and fixable.

4c asks *"does the CITED CLAUSE license this item?"* and is shown the item and its cited clause.
**In a decomposed graph that question is malformed**, and the seat is answering it correctly.
Every node's `prompt_user.txt` has a `NEEDS` block that says, in the graph's own words:

> *"these concepts are established by OTHER nodes of the graph, so every one of them belongs in
> this module's `requires`, spelled EXACTLY as given"*

So a borrowed name is licensed **by the node's construction**, not by the cited text, and the
cited text will never contain it. 14/14 is the expected score for a correct answer to the wrong
question.

**Two changes, and I would test them separately:**

1. **Show 4c the `PROVIDES` and `NEEDS` blocks, and split the question.**
   *(i)* Is this predicate name listed in `NEEDS` or `PROVIDES`? If yes → **licensed, clean, stop**
   (do not look at the source text; that is what those blocks mean). *(ii)* Otherwise → is it
   grounded in the narrowed span? **Prediction: this alone removes the 14/14 borrowed-name false
   positives and most of the 48/86**, because those blocks are exactly what I used to decide the
   same question and I never once needed to consult the cited clause for a borrowed name.
2. **Show 4c the NARROWED span, not the whole cited clause.** If it is currently shown the printed
   `L####` block, it cannot possibly catch the class it should be catching — out-of-span sourcing.
   Three clauses in my 25 (`l2405_2473_n001`, `l1108_1367_n027`, `l3239_3382_n002`) are defective
   *precisely* because the module encodes text that is inside the printed block and outside the
   narrowing. A seat shown the whole block will pass all three, and this is a "does the cited
   source license this?" question — 4c's own job. **Prediction: the fix converts 4c from a base-rate
   flagger into the only seat that catches out-of-span sourcing.**
3. A worked example of a correct-but-borrowed item would help, but I rank it **third**. The
   borrowed-name false positive is not a calibration problem the seat can be talked out of; it is
   the seat lacking the one artefact that licenses the item. Give it the artefact first, then add
   the example if residual FPs remain.

### 4b — precise but `unclear` on inverted-modality, fact-as-deontic, invented-obligation; 0/3 on scope-drift-widen

4b sees the rendered sentences. §3.1 explains why that makes it blind by construction on
inverted-modality: **in all five real inversions in my 25, the read-back sentence is correct.**
There is no wording 4b could be shown that would reveal a defect living in a field it is not shown.
`unclear` is the honest answer to an impossible question, not a calibration failure.

Two specific asks, in priority order:

1. **Give 4b the `status` and the `act` term beside the sentence** — not the whole module, which
   would cost its precision. One line per assert:
   `status=prefer | act=repeat_user_prompt(R) | reads: "repeating the user's prompt in R is to be avoided"`
   and one question: *"does the status agree with the sentence — more of this act, or less?"* That
   is a three-token comparison, not a judgement, and it is exactly the check I ran in §3.1.
   **Prediction: inverted-modality goes from `unclear` to detected, with no precision cost**, since
   the comparison cannot fire on an item where status and sentence agree.
2. **Scope-drift-widen 0/3 is a different miss and needs a different fix.** That defect lives in an
   `ontology` **body**, and a rendering of `asserts` never shows one. 4b would need the ontology
   rules rendered too, each paired with the span phrase it claims to encode, and the qualifier
   procedure from §2 (*"list every adjective and parenthetical in the span's noun phrases; name the
   body literal carrying each"*). This is a bigger change and I would do it after (1).

### 4d — 1/33 FP, the only seat catching dropped-obligation. The cheapest available upgrade.

4d is the Pass-1-shaped seat and its numbers say so. Two additions, both nearly free:

1. **Show it the module's own `claims` list and require a coverage mapping** — for each `claims`
   entry, name the formal item carrying it. `l1_170_n056` self-reports its dropped obligation in
   `claims` C1. This costs no new artefact and no new turn: the list is already in the module.
2. **Make it two-turn**, if the budget allows one extra call: turn 1 shows only the narrowed span
   and asks for the numbered enumeration (§1 Stage 1, steps 2–6); turn 2 shows the module and asks
   for the mapping. §3.6 is the evidence that the order — not the wording — is what does the work.
   If only one seat gets a second turn, it should be this one.

### On the pooled measure (+0.091 discrimination)

Pooling a near-base-rate flagger (4c, 48/86 on clean modules) with a precise-but-insensitive one
(4b) yields a near-constant function; that is arithmetic, not a surprise. **Do not tune the pool
until 4c's question is fixed.** After the 4c change, re-score per-seat before re-pooling, and
consider weighting by measured per-class recall rather than pooling uniformly — the classes are
not interchangeable and the seats are not redundant: 4d is the only seat with any purchase on
dropped-obligation, and no current seat can see inverted-modality at all.

### The one thing no seat currently has

**A stated correct answer.** Every seat is asked to detect *wrongness*, which is why the classes
that read as coherent — dropped-obligation, dropped-content, disjunction-as-conjunction — are the
ones they miss. `modules/` plus `diffs.json` now provide 26 anchored edits with classes and 9
untouched modules as a false-positive control, on clauses none of the seat briefs were tuned
against. That is a per-class recall/precision measurement for any brief change proposed above, and
it is deterministic re-analysis of data already on disk.
