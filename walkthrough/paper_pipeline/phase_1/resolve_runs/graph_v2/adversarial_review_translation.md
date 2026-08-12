# Adversarial review — graph_v2 node translation, repair non-convergence

Clean-context review, 2026-08-10. Artifacts read: `prompt/00_task.md`,
`prompt/10_output_format.md`, `prompt/30_failure_modes.md`,
`resolve_runs/graph_v2/node_worked_example.md`, every `*.transcript.json` in
runs `20260810-214437` and `20260810-215527`, `resolve_runs/graph_v2/node_corpus.py`,
`phase_1/translate.py` (`repair_loop`, `render_error_log`), `phase_1/checks.py`,
`phase_1/schema.py`, `walkthrough/link.py`. No prior analysis was consulted.

Everything below is quoted from those artifacts. Two claims were verified by
running code (F2, F3); they are marked `[RAN]`.

---

## 0. The framing to correct first: these are not "stubborn nodes"

The two runs have **identical `user_sha` for all 15 nodes** (`run.json`), i.e.
byte-identical prompts, and they disagree about which nodes are hard:

| node | 214437 (max 3 attempts) | 215527 (max 5 attempts) |
|---|---|---|
| `l1611_1798_n006` | **unrepaired**, 3 | translated, **1** |
| `l527_796_n012`   | translated, 3 | **unrepaired**, 5 |
| `l292_526_n027`   | translated, 2 | **unrepaired**, 5 |
| `l797_809_n001`   | translated, 2 | **unrepaired**, 5 |
| totals | 12 translated | 9 translated |

The run with the *larger* repair budget passed *fewer* nodes. That is only
possible if repair rounds are, on average, close to value-neutral — each round
clears one defect and has a comparable chance of introducing another. So the
target is not "why does node X resist"; it is **why does a repair round not
monotonically reduce the defect set**. Findings F1, F2, F6 are that mechanism.

---

## A. Per-node: why repair did not converge

### A1 `l3384_3501_n007` — one finding, five rounds, never even attempted

Standing finding, identical in attempts 1–5:

```
- [schema-breach] forbid_body[0]: forbid_body `head` 'forbid(respond_with(R))' is not a bare predicate name
```

The model's `forbid_body` is **byte-identical across attempts 2, 3, 4 and 5**:

```json
{"head": "forbid(respond_with(R))",
 "banned": "programmatic_instruction(I), plain_text_response(R), overrides(I, R)"}
```

It never tried a different shape. It is not misunderstanding the finding — it
has no model of what the field wants, and nothing it was given supplies one:

* `forbid_body` appears in **no worked example** — all four good examples and all
  six bad examples carry `"forbid_body": []`.
* `00_task.md` rule 8 says only *"Put it in `forbid_body`"*, with no shape.
* The schema description the model receives is `head` = *"the derived relation,
  e.g. permit"*.
* `node_worked_example.md`'s three-notations table says the opposite:
  `forbid_body.head` is the **bare functor name of the act**, `apply_default`.

`forbid(respond_with(R))` is exactly what you get by trying to satisfy both
readings at once. Meanwhile `banned` is described as *"what may not appear in its
body"* — which invites the conjunction the model wrote — but
`ForbidBody._fb_ok` demands `^[a-z][A-Za-z0-9_]*$` for it too. Had the model ever
fixed `head`, `banned` would have failed on the next round (the validator loops
`head` then `banned` and raises on the first).

Rounds 3 and 4 also carried five *new* `concept name 'X/1' is not a predicate
name` breaches that were absent in rounds 1–2 — collateral damage from
rewriting the whole module each round (see F1, F5).

### A2 `l292_526_n027` — the feedback names a repair the model does not believe applies

Standing finding, attempts 1, 2 and 4:

```
- [schema-breach] <root>: body references `scope_of_autonomy` but nothing declares it.
  Put it in this module's `ontology`, in `requires` ..., or in `inputs` ...
```

The model **had already declared it** — as `concepts[0]`, `{"name":
"scope_of_autonomy", "arity": 1, "gloss": "…"}` — in every one of the five
attempts, and left `"requires": []`, `"inputs": []` in every one of the five
attempts. It reads its own `concepts` entry as satisfying "nothing declares it".
The rule that `concepts` is not a declaration site exists (10_output_format:
*"⚠️ Declaring a concept is not the same as defining it"*), but the finding
message does not invoke it, and the message's three-way choice reads as
information the model thinks it has already supplied.

Attempt 3 tried the only other thing it could think of — writing the rule into
`atom`:

```json
{"atom": "semi_structured_scope_record(S) :- scope_of_autonomy(S)", "body": "scope_of_autonomy(S)"}
```

which drew a *different* finding, so attempt 4 reverted to attempt 2's text, and
attempt 5 went back to the rule-in-atom. That is a two-state oscillation, not
progress.

Note also: `scope_of_autonomy` is the node's **only NEEDS name**, and the input
block already says *"every one of them belongs in this module's `requires`"*.
The finding could have said so and did not.

Third defect, never reported at all: every entry in all five attempts cites
`l292_527_n027`. The node is `l292_526_n027`. See F8.

### A3 `l797_809_n001` — same shape

```
attempt 2/3/4: body references `fully_comply` but nothing declares it.
```
Three identical rounds. Attempt 1's finding was a different one (`inputs entry
'request(R)' is not name/arity`), so the budget was spent one defect at a time.

### A4 `l4572_4691_n011` — the message argues against its own fix

Attempts 1, 3, 4 and 5 all fail with three copies of:

```
- [schema-breach] asserts[i]: read_back has 0 `%` slot(s) but 1 slot entr(ies) — the rendered
  sentence would silently be wrong. A literal percent sign cannot be written; say 'per cent'
```

The read-backs barely move across rounds:

```
attempt 1: 'for U18 users, engaging in immersive romantic roleplay is forbidden, …'  ['U']
attempt 5: 'for U18 users, engaging in immersive romantic roleplay is forbidden'      ['U']
```

Two repairs exist — insert a `%`, or empty `read_back_slots` — and the message
names **neither**. Its only actionable-looking sentence, *"A literal percent
sign cannot be written; say 'per cent'"*, is irrelevant here and reads as a
prohibition on putting `%` in the sentence, i.e. it points away from repair 1.
The model kept editing the prose (the only lever it understood) and never
touched the slot list. **Speculative** on the mechanism; the non-convergence is
fact.

Attempt 2 additionally introduced two unbound-atom breaches while the read_back
ones still stood — again, whole-module rewriting.

### A5 `l810_919_n014` — pure oscillation, plus an unreported fabricated citation

Run 215527, findings by round:

1. `ontology[0]` unbound `R` → model adds `"body": "user_request(R), requests_pathogen_amplification_steps(R)"`
2. `asserts[0]` read_back 0 `%` / 1 slot → model empties the slots **and deletes the body it just added** (`"body": null`)
3. `ontology[0]` unbound `R` **again** (identical to round 1's finding) → model restores a body and adds a `%`
4. `inputs entry 'user_request(R)' is not name/arity` → model fixes that and drops the `%` again
5. out of budget. Final `inputs` is `["requests_amplification_steps/1", "requests_amplification_steps/1"]` — a duplicated entry, and `user_request/1` is still referenced by the body and still undeclared, which would have been round 6.

Round 3's finding is round 1's finding. Nothing about the feedback is
ambiguous here — the loop simply gave the model no reason to hold a cleared fix
while making the next one, and the model regenerated the object from scratch
each time. Run 214437 shows the same node failing on a *different* pair:
`assertion names act 'refuse_biological_amplification_help(R)', which is not in
'acts'` → then `no default-closure declaration for act class(es)
['refuse_biological_amplification_help']`. Those are **two halves of one
mistake** (declare the act, declare its closure), reported on consecutive paid
rounds, and the 3-attempt budget ran out between them.

Also, unreported for five rounds: attempt 1 cites `l3995_4164_n014` — a mangle
of the worked example's node id `l3995_4164_n001` — and from attempt 2 onward
the module renames itself `"clause_id": "l810_896_n014"` (node id fused with the
`L0880-L0896` span). Neither ever produced a finding. See F8.

### A6 `l527_796_n012` — the model cannot reproduce the module it was handed

This node **is the headline worked example in the system prompt**, complete
gold module included, and it went unrepaired in run 215527. Its findings walk a
different defect each round:

```
1: body references `instruction` but nothing declares it
2: read_back has 1 `%` but 2 slot entries
3: ontology[0] 'best_intentions_bias(B)' unbound  +  read_back 0 `%` / 2 entries
4: body references `instruction_level` but nothing declares it
```

Round 1 and round 4 are the **same defect in the same body** — the model wrote
`"body": "instruction(I), instruction_level(I, L), bias_level(B, M), authority_hierarchy(L, M)"`
and the validator reported one undeclared name, then, after that was fixed, the
next one. Attempts 3 and 5 also put a NEEDS name (`best_intentions_bias`) into
`ontology` with `"body": null`, which the input text explicitly forbids
(*"never in `ontology`, never defined here"*) — an instruction no check
enforces.

That a model holding the gold answer for this exact node fails it is the
strongest available evidence that the binding constraint is the **repair
channel**, not the teaching.

---

## B. Contradictions and untaught rules

### B1 `00_task.md` rule 10 contradicts three fields — CONFIRMED, with damage

> **10. Include arity everywhere** a predicate is named: `forbids/2`, never `forbids`.

`concepts[].name`, `acts[]` and `closure.act_class` all reject `name/arity`.
`node_worked_example.md`'s three-notations table is correct; rule 10 is a
blanket instruction that overrides it. Damage, verbatim:

```
l1799_1974_n009 attempt 3:  concept name 'assistant/1' is not a predicate name
                            concept name 'underlying_prompt/1' …
                            concept name 'policy_allows_disclosure/1' …
l3384_3501_n007 attempts 3 and 4: five such breaches each
```

In `l1799` this cost a round and the node only just recovered (translated at
attempt 5, flagged `shrank` + `declaration-edit`).

### B2 `forbid_body` — taught by nobody, described inconsistently

Covered in A1. Three sources, three shapes for `head`; `banned`'s description
(*"what may not appear in its body"*) and its validator (a bare predicate name)
are flatly incompatible.

### B3 Rules the validator enforces that nothing teaches

* **`banned` must be a single predicate name.** Nowhere in prompt or examples.
* **Every head variable must be bound by the body** — the worked example says
  it (*"Every variable in every atom is bound by its body"*) and the schema does
  **not** enforce it (F3), so the teaching is correct and the enforcement is not.
* **`requires` and `ontology` may overlap.** Only `requires ∩ inputs` is
  checked. `l527_796_n012` attempt 1 put `higher_level_instruction/1` in
  `requires` *and* defined it in `ontology`; no finding.

### B4 Rules the input text states that nothing enforces

The NEEDS block promises *"every one of them belongs in this module's
`requires`"*. `l3384_3501_n007` used **neither** of its two NEEDS names in any
of five attempts (`interactive_vs_programmatic_context`,
`interactive_behaviors`) and was never told. So the strongest instruction in the
per-node input has no consequence, while the borrow-gloss rule — which the input
text never mentions — does (`l1799` attempt 1: *"`assistant/1` is borrowed but
has no gloss"*).

---

## C. Input-side (`node_corpus.py::row()`)

1. **`ESTABLISHES (the one claim this module must express)`** contradicts the
   abstention route the system prompt calls "a real answer". `l292_526_n027`'s
   own establishes text literally begins *"Commentary: …"*, and `l810`/`l3384`
   are document examples — the three worst nodes are exactly the three where
   abstention or a tiny module was the cheap correct answer, and the header word
   is "must". **Speculative** but cheap to test.

2. **The node id sits next to look-alike line spans in three places** —
   `clause id: l810_919_n014`, `location: … > L810-919_n014 > L880-896`, and
   `L0880-L0896:` in the body. Both observed citation corruptions are exactly
   this fusion: `l810_896_n014`, `l292_527_n027`.

3. **`kind` is a keyword heuristic** (`kind_of`: `"example demonstrat" in
   establishes → meta`) and is rendered into the prompt as `kind: meta`, a label
   no prompt file explains.

4. **The NEEDS block does not mention the gloss obligation** or that the arity is
   the model's to choose but must then be used consistently in every body.

---

## D. Findings ranked by expected impact on pass rate

### F1 — The validator can report only ONE root-level defect per round (CONFIRMED, highest impact)

**Defect.** `Module._coherent` is a single pydantic `model_validator` that
`raise`s on its first failure. Every cross-field rule lives inside it —
`requires`/`inputs` shape, `requires ∩ inputs`, act-declared-in-`acts`, forced
closure, undeclared body names (one `raise` inside a `for` loop over every
name), borrow-gloss, gloss-restates-name, `beats` sayer. Additionally, if **any**
sub-model field fails, pydantic never runs `_coherent` at all, so a single bad
`read_back` masks the entire root-level rule set. Net: an attempt with six
defects gets one message, and the model rewrites the whole object to answer it.

`checks.py`'s own docstring states the design intent this violates:

> A repair loop built on those directly repairs one defect per PAID MODEL CALL …
> The complete finding set is this module's whole reason to exist.

It merges `schema` with `link` findings, but `schema` itself only ever yields
one root-level finding, so the merge does not deliver what the docstring
promises.

**Evidence.** `l810` run 214437 (act-not-declared → its closure, two halves of one
mistake on consecutive rounds); `l527_796_n012` run 215527 (`instruction`
undeclared at round 1, `instruction_level` from the same body at round 4);
`l810` run 215527 (round 3's finding is round 1's finding); `l292` rounds 2↔3↔4
oscillation.

**Minimal fix.** Change `_coherent` from raise-on-first to collect-then-raise:
accumulate messages in a list and `raise ValueError("\n".join(msgs))` once —
or, better, move the cross-field rules into a collecting function in `checks.py`
that runs whenever `mod is not None`, so each becomes its own `Finding`. The
undeclared-name loop should report **all** names in one message either way.
Expected to be worth more than every other fix combined: it converts a
one-defect-per-paid-call loop into the one the design intends.

**Confidence: high.**

### F2 — The clingo error is truncated to its useless first line (CONFIRMED `[RAN]`)

**Defect.** `link.py:157` `CLINGO_ERR = re.compile(r"^.*\berror\b\s*:.*$", re.M)`
keeps only lines containing `error:`. clingo emits the actionable content on the
*following* lines. Reproduced locally on `l1611_1798_n006` attempt 1:

```
/tmp/x.lp:31:1-66: error: unsafe variables in:
  delusion_mania_response_approach(A):-[#inc_base];delusion_mania_sign(S);o.
/tmp/x.lp:31:34-35: note: 'A' is unsafe
```

The model received only line 1 — no rule, no variable name:

```
- [clingo-error] l1611_1798_n006.lp: clingo refused this program, so nothing below
  was actually analysed: …:60:1-66: error: unsafe variables in:
```

**Evidence.** `l1611_1798_n006` run 214437, attempts 1 and 2 identical, node
unrepaired — and the same node passed on attempt 1 of run 215527, so the whole
failure is this message. Also `l1975_2125_n012` run 215527 attempt 1.

**Minimal fix.** In `_compiles`, keep each `error:` line plus every following
line that is indented or contains `note:`, up to the next blank line. One regex
change.

**Confidence: high.**

### F3 — The schema accepts head variables the body does not bind (CONFIRMED `[RAN]`)

**Defect.** `OntologyFact._onto_ok` and `Assertion._assertion_ok` call
`_check_term(..., allow_vars=bool(self.body))` — *any* non-empty body licenses
*any* variable in the head. Verified: `l1611` attempt 1's
`{"atom": "delusion_mania_response_approach(A)", "body": "delusion_mania_sign(S)"}`
returns **zero breaches** from `schema.validate_all`, then dies in clingo.

This is the defect `node_worked_example.md` calls *"the single most common
failure on nodes"*, and it escapes the clear schema message that names it,
arriving instead as F2's truncated clingo line.

**Minimal fix.** After the body check, compare variable sets:
`unbound = vars(atom) - vars(body)`; if non-empty raise the existing
"carries the variable X and there are no conditions to bind it" message with
X = the unbound one. ~4 lines in `_check_term`'s callers.

**Confidence: high.**

### F4 — `forbid_body` is untaught and its descriptions contradict its validator

**Defect + evidence.** A1 and B2. One node's entire 5-round budget.

**Minimal fix.** (a) Add one populated `forbid_body` to `node_worked_example.md`
(the natural one: `{"head": "permit", "banned": "purpose"}` with a sentence
saying it means *no permit rule may rest on purpose*). (b) Change the `banned`
field description from *"what may not appear in its body"* to *"a single
predicate NAME — no arguments, no conjunction"*. (c) Make `_fb_ok` report both
slots and show the required shape in the message. (d) Reconcile the
three-notations table's `forbid_body.head` row with the schema description —
they currently teach different things.

**Confidence: high on the defect; medium on which of the three readings is
intended — the schema description ("the derived relation, e.g. permit") and the
example table (act functor) need a human ruling before either is edited.**

### F5 — `00_task.md` rule 10 tells the model to write `name/arity` everywhere

**Defect + evidence.** B1; 8 breaches across two nodes.

**Minimal fix.** Rule 10 → *"Include arity in `requires` and `inputs`:
`forbids/2`, never `forbids`. Everywhere else — `concepts.name`, `acts`,
`closure.act_class` — see the three-notations table."*

**Confidence: high.**

### F6 — Findings state the rationale but not the available repairs

**Defect.** Every message explains *why the rule exists* (correctly, and at
length) and none says *what to change*. Two messages actively mislead:

* read_back mismatch ends with *"A literal percent sign cannot be written; say
  'per cent'"* — irrelevant to the mismatch and pointing away from the
  insert-a-`%` repair (`l4572`, 4 rounds; `l810` rounds 2 and 4).
* "body references X but nothing declares it" lists three sites and omits the
  one thing the model got wrong, namely that its `concepts` entry does not count
  (`l292`, 4 rounds; `l797`, 3 rounds).

**Minimal fix.** Two message edits:
`read_back has N '%' but M slot entries — either write a '%' where each of
[slots] is substituted, or set read_back_slots to []`;
and append to the undeclared-name message: *"a `concepts` entry declares what a
name MEANS and is not a declaration site"*, plus, when the name matches one of
the node's NEEDS names, *"`X` is a NEEDS name of this node: it belongs in
`requires` as `X/n`"*.

**Confidence: high that the messages are under-specified; medium on the size of
the pass-rate gain.**

### F7 — Fabricated citations and identity drift are never reported (soundness, not just pass rate)

**Defect.** Two gaps, one mechanism:

1. `validate_all` returns early when `mod is None`, so the clause_id-identity
   check and the corpus-citation check never run while any field breach stands
   — which, on a failing node, is every round.
2. Even when they do run, the corpus-citation loop covers only
   `("asserts", "beats", "defines", "ontology")`. **`concepts[].cites` is never
   checked against the corpus at all.**

**Evidence.** `l810` cited `l3995_4164_n014` (attempt 1) and renamed itself
`l810_896_n014` (attempts 2–5) — never reported. `l292` cited `l292_527_n027`
in all five attempts, in `concepts` and `ontology` — never reported. Both are
`00_task.md`'s *"single worst failure available here"*: an invented entity
behind a passed check.

**Minimal fix.** Add `"concepts"` to the citation-check field tuple, and run the
identity + citation checks on the raw dict (they need only `clause_id` and
`cites` strings) even when `Module.model_validate` raised.

**Confidence: high.**

### F8 — Input-side: "the one claim this module must express" suppresses abstention

**Defect + evidence.** C1. All three worst nodes are `meta`/commentary.

**Minimal fix.** In `row()`, change the header to
`ESTABLISHES (the claim this module should express — or abstain, if the node
states no obligation, permission or prohibition)`, and drop the `L…-…_nNNN >
Lstart-Lend` span suffix from the `location` line (C2) so the only id-shaped
string in the prompt is the citable one.

**Confidence: medium (mechanism plausible, not directly evidenced). The
`location`-span change is high confidence — two observed citation corruptions
are exactly that fusion.**

### F9 — The NEEDS→`requires` contract is unenforced

**Defect + evidence.** B4; `l3384` dropped both NEEDS names silently.

**Minimal fix.** A `note`-severity finding is the wrong tool (notes are never
shown). Either add an error-severity check *"NEEDS name X appears in neither
`requires` nor any body"*, or stop promising it in `row()`. As written the
instruction is decorative.

**Confidence: high that it is unenforced; medium on whether enforcing it helps
pass rate — it may raise the failure count before it lowers it.**

---

## E. What I would change first

F1 + F2 + F3 are three small, independent code edits in `schema.py`,
`checks.py` and `link.py`, and together they change what a repair round *is*:
from "you get told one of your defects, in a message that may not name the
offending rule" to "you get the complete list". F5 and F6 are text edits with
no code risk. F4 needs a ruling before it can be written. F7 is a correctness
fix that does not raise pass rate and should be landed anyway.

I would **not** re-measure pass rate against the 214437/215527 pair — with
identical prompts they differ by 3 of 15, so the noise floor is ~20 points on
this sample size. Any claimed gain needs more nodes or repeated runs.
