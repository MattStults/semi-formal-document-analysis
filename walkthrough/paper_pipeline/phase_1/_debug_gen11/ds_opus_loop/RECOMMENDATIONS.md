# RECOMMENDATIONS — from the DeepSeek-drafts / Opus-adjudicates loop

Every entry below was produced by a specific turn on a specific clause in
`out/`. Each is marked **(a) prompt fix**, **(b) schema gap**, or **(c) graph
defect**, and is phrased as a mechanical question or a concrete prompt edit.

⚠️ **Scope of the evidence.** Two clauses, eight live calls, $0.0190. Every
number here is MEASURED on that population unless marked INFERRED. Two clauses
is enough to establish that a thing *happens*; it is not enough to establish a
rate.

---

## R1 — (a) prompt fix · the repair message must be SHORT, NUMBERED, MECHANICAL

**MEASURED, `l1_170_n056`, turns 1–4.** A 3,900-character critique carrying 11
findings produced a **byte-identical** reply. Twice. The second send prefixed the
findings with an explicit "attempt 2 is byte-identical to attempt 1, do not
reproduce it" — still byte-identical. A **62-word** message listing three
numbered mechanical edits and saying "change nothing else" broke the freeze on
the next turn and performed all three edits exactly.

This bears directly on `translate.repair_loop`'s docstring, which records that
the repair *message* was refuted as the cause of freezing (four frozen
transcripts replayed to stand-in translators, 4/4 repaired in one turn) and
concludes the defect is "the CONTEXT IT ARRIVES IN". That experiment varied the
*reader*. This one held the reader fixed and varied the message **length and
form**, and the freeze moved. Both can be true — but "the message is sufficient"
is now known not to imply "the message is not a lever".

⛔ This is **not** a proposal to paraphrase the repair message, which
`repair_loop` rejects by name. `render_error_log` already emits one
`check_id`/`where`/`message` line per finding; the proposal is about **volume
and imperativeness**, not wording.

**The mechanical questions to answer before changing anything:**
1. What is the distribution of `len(render_error_log(...))` across the stored
   gen-11 repair turns, and do the frozen chains sit in the long tail? This is
   answerable from `resolve_runs/graph_v2/translation_sample/runs/*` at zero
   cost and would turn one anecdote into a rate.
2. Does capping the repair log at the N most severe findings per turn change the
   freeze rate? A/B on the frozen population only.
3. Do the findings in a long log get fixed in list order, or not at all? Turn 4
   fixed 3 of 3 items from a 3-item list; turns 1–3 fixed 0 of 11 from an
   11-item list.

## R2 — (a) prompt fix · teach the DISJUNCTIVE OBLIGATION idiom, with an example

**MEASURED, `l3147_3238_n003`, turns 1–3.** Three turns and an explicit
statement of the required structure were needed to get from three obliges on one
body to one oblige over an ontology-derived act. The final shape is:

```json
"acts":    ["respond_to_low_confidence(R)"],
"ontology":[{"atom":"respond_to_low_confidence(R)","body":"uses_tool_to_gather_info(R)"},
            {"atom":"respond_to_low_confidence(R)","body":"hedges_answer(R)"},
            {"atom":"respond_to_low_confidence(R)","body":"explains_cannot_answer_confidently(R)"}],
"asserts": [{"status":"oblige","act":"respond_to_low_confidence(R)",
             "body":"lacks_sufficient_confidence(R)"}]
```

The prompt already teaches "alternatives are written by repeating the atom" —
but **only for a classification** (`higher_level_instruction(I)`, explicit or
implicit). It never shows the same device used to make an *obliged act*
disjunctive, and nothing tells the translator that a normative "or" has to be
pushed down into `ontology` because `asserts` cannot hold one.

**Concrete edit:** add a fourth good worked example to
`resolve_runs/graph_v2/node_worked_example.md` — a disjunctive-obligation node,
with the shape above and one line of prose: *"`asserts` attaches one status to
one act. A span that offers a CHOICE of acts is one obligation over an act the
`ontology` derives three ways — never three obligations, which condemns every
compliant response but one."*

⚠️ **Two failure directions, and the example must block both**, because the
feedback that worked named both: three obliges on one body is wrong, and so is
one oblige over a single opaque "respond adequately" predicate with the three
alternatives named nowhere — that is failure mode #5, the hollow stub.

## R3 — (a) prompt fix · a rewritten READ-BACK is the model's escape hatch

**MEASURED, `l3147_3238_n003`, turn 2.** Told that three obliges on one body
condemn the compliant response, the model left all three `asserts` byte-identical
and rewrote **all three read_backs** to the same, correct, disjunctive sentence.
The result is strictly worse than the input: the reviewer reads the correct claim
three times and the defect becomes invisible. It also manufactured, in its own
`claims`, exactly the P3 fingerprint ("C2: the three actions are alternatives" —
stated, encoded nowhere).

The review list's third anti-rule states this rule for the *reviewer*. The
production prompt does not state it for the *translator*.

**Concrete edit:** in the `### Read-backs` section of `prompt/10_output_format.md`,
after "Write it as the clause's own claim, not as a description of the code",
add: *"⛔ **When a finding says an item states the wrong thing, change the item.**
A read-back rewritten to match a finding, over an item that did not change, makes
the defect invisible to every later reader — the read-back is what they are shown
INSTEAD of the item. Measured: a repair turn did exactly this to all three
asserts of one module."*

## R4 — (a) prompt fix · "unless" has ONE destination, and the prompt gives it none

**MEASURED, `l1_170_n056`, turns 1–5.** The first draft encoded the exception as
three `permit refuse_request(R)` asserts and left `oblige honor_request(R) :-
user_request(R)` **unconditional** — so on a conflicting request the module
simultaneously obliged honoring and permitted refusing, with no relation between
them. It took an explicit six-item mechanical instruction to move the exception
into the obligation's body.

Note this is a *third* distinct way to get this clause wrong, alongside the two
already on record: production's "obligation dropped, exception kept" (list P3) and
N7's "a `forbid` invented on the excepted branch". All three come from the prompt
never saying where an exception goes.

**Concrete edit** to `prompt/00_task.md`, as a numbered rule beside rule 4:
*"**An exception belongs in the obligation's body.** 'A unless B' is one
assertion of A whose body excludes B — not a second assertion about B. Derive B
positively in `ontology`, one entry per ground the span names, and put `not B` in
the obligation's body: that is what gives the withdrawal a reason (rule 4) while
asserting no norm on the excepted branch (which the span does not state)."*

## R5 — (a) prompt fix · a NEEDS name is the ONLY thing that may be in `requires`

**MEASURED, `l1_170_n056`, turn 1.** `instruction_level/2` — not a NEEDS name —
was placed in `requires`, so all three `ontology` entries waited on a definition
no node of the graph supplies and the exception was dead on arrival (failure
mode #15). The prompt states the rule twice, and both statements are *permissive
in form*: contract 2 says every NEEDS name goes in `requires`, and the heading
node says `requires` "is for the names in the `NEEDS` block". Neither says
`requires` may contain **nothing else**.

**Concrete edit** to contract 2 in the node worked-example file: *"`requires`
contains the NEEDS names and nothing else. A predicate you identified yourself is
case-side and goes in `inputs`, however much it looks like something another node
ought to own — put it in `requires` and its rule waits forever on a definition no
node supplies, deriving nothing while looking like it enforces something."*

⚠️ This is the *converse* of the review list's second anti-rule, and the two must
be stated together or they will be read as contradictory. The anti-rule forbids
moving a **NEEDS** name into `inputs` to silence `requires-unprovided` notes.
This forbids putting a **non-NEEDS** name into `requires` at all. The
discriminator in both directions is the NEEDS block, never the note.

## R6 — (a) prompt fix · the borrowed gloss must be the node's meaning, not a paraphrase of the name

**MEASURED, `l1_170_n056`, turns 1–5 — this one survived to the final module.**
The node hands `user_authority` as *"The user level of instruction authority:
instructions from end users."* Every draft glossed it as *"R is a request from an
end user…"* — a property of a **request**, not an authority level — and then
coined `user_request/1` glossed *"R is a request made by an end user"* and gave
the coined name all the work. One idea, two names, inside one module, with the
borrowed one silently redefined.

This is failure mode #9 (same name, different meanings) manufactured inside a
single module, and it is the exact thing the concept gloss exists to prevent:
the gloss is what links this module to the providing node, so a silently
redefined gloss links to the wrong thing while reading correctly.

**Concrete edit:** the node prompt already says "Give it a `concepts` entry
carrying the meaning the node text hands you." Make it mechanical: *"Copy the
NEEDS meaning into the gloss. If you find yourself rewording it to fit your
bodies, stop — you are describing a different predicate, and it needs a different
name."*

**And a free mechanical check, no model call:** for every module, string-compare
each borrowed `concepts` gloss against the NEEDS text in that node's
`prompt_user.txt`. A gloss sharing few content words with the text it was handed
is a candidate. INFERRED that this generalises — measured on one clause.

## R7 — (a) prompt fix (review list) · P9 contradicts prompt contract 2

**MEASURED on both clauses.** Review-list **P9** asks "does every name in
`ontology`/`requires`/`inputs` appear in some body? An unused declaration is
usually the fingerprint of content that was dropped." The production prompt's
contract 2 says the opposite for one case, in bold, with a worked example: *"The
NEEDS name went to `requires` even though the module never uses it… Contract 2 is
not conditional on your judgment of relevance."*

Applied literally, P9 fires on `user_authority/1` and `assistant_definition/1` in
every correct node module in the corpus. On `l3147_3238_n003` I had to tell the
model explicitly not to touch them.

**Concrete edit to `REVIEW_LIST.md` P9:** *"⚠️ Exempt NEEDS names: contract 2
requires them in `requires` whether or not a body uses them. P9 is about names
you COINED — an unused coined name is the fingerprint. (Measured: `response/1`,
`l3147_3238_n003`, coined, declared, used in no body, three turns running.)"*

## R8 — (b) schema gap, RECORDED not proposed · `asserts` cannot hold a disjunctive act

`asserts(ClauseId, Status, Act)` binds one status to one act. A span offering a
choice of acts has no direct home, and the working encoding (R2) routes the
disjunction through `ontology`. That encoding is adequate: it is expressible,
the alternatives stay individually visible, and the read-back reads correctly.

**Recorded, with no change proposed**, and the grounds matter: adding a
disjunctive act form to the schema would change `schema_sha`, the `.lp`
rendering, and every downstream reader, to buy expressiveness the ontology route
already provides. The cost of the gap is that the translator does not *find* the
route unaided — which is R2, a prompt fix. **Reach for the schema only if R2's
worked example is added and the defect persists.**

## R9 — (c) graph defect · `user_authority` is bound to two different meanings

**MEASURED across the two clauses' `prompt_user.txt` blocks.** The same NEEDS
name arrives with two different definitions:

* `l1_170_n056`: *"The user level of instruction authority: instructions from end
  users."*
* `l3147_3238_n003`: *"Rules in sections marked authority=user carry user-level
  instruction authority."*

The first is about **instructions from a source**; the second is about **rules in
a document section**. Both nodes are told to put `user_authority` in `requires`,
so both will link to whichever node PROVIDES it — and at most one of them can be
getting the predicate it was told to assume. This is failure mode #9 arriving
through the graph rather than through the translator, and no per-clause check can
see it: each module is individually correct.

Also worth noting: `user_authority` is a NEEDS name on `l3147_3238_n003`, a
confidence/uncertainty node where it does no work at all. The model correctly
kept it (contract 2) and correctly left it unused.

**The mechanical question, answerable at zero cost:** group every node's NEEDS
block by name across `resolve_runs/graph_v2/.../\*.prompt_user.txt`, and for each
name used by more than one node, diff the definitions handed out. Any name with
two materially different definitions is either a graph defect or a name that
needs splitting, and the translator can never see it.

## R10 — (a) prompt fix · the stage-2 floor certified a module with an invented act

**MEASURED, `l1_170_n056`, turn 4.** After the three schema edits, the module
scored `outcome=translated`, `repair_needed=False`, 0 breaches — while still
carrying `permit refuse_request(R)` (an act the span never names) and an
obligation the exception never reached. Likewise `l3147_3238_n003` turns 1 and 2
both passed the floor with the disjunction defect intact.

No new check is proposed: both defects are semantic, and a checker that could see
them is the translator. What this argues for is a **recorded expectation** — a
clean stage-2 result is a well-formedness result and is not evidence of
faithfulness, and any downstream document that treats `repair_needed=False` as a
quality signal should say so explicitly. **INFERRED** that this generalises; what
is MEASURED is 3 of 8 drafts here passing the floor with a defect that changes
what the module concludes.

---
# WAVE 2 — `l1707_1973_n006` (calibration clause), converged turn 3 of 5, $0.005930

## R11 — (a) prompt fix, and a MEASURED blind spot in `checks` · a wholly unused `inputs` name raises no note

**MEASURED, `l1707_1973_n006`, turn 1.** `informative_response/1` was coined,
declared in `concepts`, declared in `inputs`, and used in **no body**. It was the
entire GOOD arm of a GOOD/BAD example. `checks.run_checks` emitted a
`situation-input` note for each of the other three inputs (`medical_question/1`,
`definitive_diagnosis/1`, `answers_question/2`) and **none for
`informative_response/1`** — so the one input that was doing nothing was the one
input the floor did not mention. The draft scored `translated`,
`repair_needed=False`, 0 breaches.

**The mechanical question, answerable at zero cost and worth answering before any
code change:** does `situation-input` fire off *use in a body* rather than off
*declaration in `inputs`*? If so the note set is silently anti-correlated with
the defect it looks like it would catch, and P9's fingerprint — a coined name
with no use — has **no** mechanical detector today.

**Prompt fix proposed, not a checker.** `10_output_format.md` line 59 already
says a declared concept "must ALSO be in your `ontology`, your `requires`, or
your `inputs`". Add the converse in the same place: *"and a name in `inputs` or
`ontology` that appears in no body is content you dropped — either use it or
delete it. A `requires` entry that is a NEEDS name is the one exception and must
be left alone."* (The exception clause is not optional; without it this fires on
every correct node module, which is the defect P9 already had once.)

## R12 — (a) protocol fix, URGENT · `REVIEW_LIST.md` P10 discloses this clause's calibration answer

**MEASURED.** The brief for this clause says the calibration defect must not be
looked up, and names three directories to avoid. **Step 3 of the same protocol
requires opening `_debug_gen11/translate_opus/REVIEW_LIST.md`, and P10 reads:**
*"Measured: `l1707_1973_n006` emits `prefer respond_to_medical_question(R)` for
**both** `good_response(R)` and `bad_response(R)`."* That is the independently
adjudicated defect, clause id and all.

The blind pass here was written and saved before the list was opened, so this
run's split survives — but it survives by luck of ordering, not by design, and
**any agent that opens the list first has no blind pass left.**

**Concrete fix, two options, both cheap:** (a) strip clause ids from the
`Measured:` lines of every list entry that names a clause in the calibration set,
keeping the pattern and dropping the identifier; or (b) hand calibration agents a
list variant with those entries removed and record which variant they got.
Option (a) is preferable — the ids are attribution, and attribution belongs in
the entry's footer where the calibration set can be filtered.

## R13 — (a) prompt fix · the prompt never says whether to GATE a rule on its NEEDS name

**MEASURED, `l1707_1973_n006`, all three turns.** The node's one NEEDS name is
`avoid_regulated_advice_rule`, glossed *"The rule that the assistant should equip
users with information without providing definitive regulated advice and include
a disclaimer."* The module's `forbid` is the enforcement of exactly that rule,
and its own claim C2 says so — *"which the avoid-regulated-advice rule
prohibits"* — yet no body mentions the name. Contract 2 makes the unused
`requires` entry correct. So the module is simultaneously right (the name is
recorded) and disconnected (nothing links the prohibition to the rule it
enforces), and **no check can tell which was intended.**

This is the same shape as the proof run's *"the prompt never says WHERE AN
EXCEPTION GOES"*, one level up: **the prompt never says whether a NEEDS name is a
name to RECORD or a name to USE.**

Gating was considered here and **rejected by name**, and the grounds are
reusable: adding `avoid_regulated_advice_rule(R)` as a body conjunct is P5's ⚠️
exactly — it *weakens* the prohibition, making it fire only where another module
derives that atom, and of a `R`-shaped argument this module only guessed at.

**Prompt fix proposed:** one sentence in contract 2. *"A NEEDS name belongs in
`requires` whether or not you use it. Put it in a BODY only when the span makes
the rule's application conditional on it; a rule the span states outright does
not become conditional because a NEEDS name describes it."*

## R14 — (b) NOT a schema gap; a prompt fix · a borrowed name arrives with no ARITY

**MEASURED.** The NEEDS block gives `avoid_regulated_advice_rule` with a gloss
and **no arity**, and `10_output_format.md` rule 10 requires arity everywhere a
predicate is referenced. The translator guessed `/1` over responses and rewrote
the graph's gloss from *"**The rule that** the assistant should…"* into *"**R is
subject to** the rule that…"* — a rule silently re-typed as a property of
responses. It took an explicit edit to restore the graph's wording.

This is N8 (argument order) generalised to argument **count**, and it is worse:
N8's inversion at least has a fixed arity to disagree about.

**Recorded as a prompt fix, not a schema change, deliberately.** The graph could
emit arities, but the NEEDS gloss is prose written for a human and the arity is a
modelling decision the *consuming* node makes. The cheap fix is in the prompt:
*"A NEEDS name arrives without an arity. Choose one, and make the `concepts`
gloss say what each argument IS — 'the rule that … ; the argument is the response
the rule is applied to' — so a provider mismatch surfaces as a description
disagreement rather than a silent arity error."*

## R15 — (a) prompt fix · a GOOD/BAD example needs its arms DISJOINT, not merely different

**MEASURED, `l1707_1973_n006`, turn 2.** After the GOOD arm was given a rule, the
two asserts *differed* in status — `forbid` vs `permit` — and P10 as written is
satisfied. **They still overlapped:** a response that explains causes, suggests a
precaution, advises a doctor **and** states a definitive diagnosis matched both
bodies and was permitted and forbidden at once. The guard existed only in a
gloss (*"without giving a definitive diagnosis"*) and never reached a body.

**Proposed as an amendment to P10 on the review list**, not to the production
prompt: *"…do the two arms differ in `status` or in act — **and can one
situation satisfy both bodies?** A GOOD/BAD pair whose arms overlap is a
contradiction generator. Close it with a POSITIVE predicate (N5), never with
`not`."*

## R16 — (a) prompt fix · a gloss written for a DECLARATION is not revisited when the name gets a DEFINITION

**MEASURED, `l1707_1973_n006`, turn 2, and it is a mechanism worth naming.** At
turn 1 `informative_response/1` was a bare `inputs` name, and its `concepts`
gloss was a free-text description. At turn 2 it acquired an `ontology` body. The
gloss was **not** touched, and it then described a different predicate from the
one the solver computes — omitting one conjunct and adding a condition the body
does not contain. Nothing in the schema couples them; `10_output_format.md` line
57 says declaring is not defining, but says nothing about what happens when the
same name gets both.

**Prompt fix:** add to line 57's paragraph — *"When a name has BOTH a `concepts`
gloss and an `ontology` body, the gloss must name exactly the body's conditions.
A gloss that says less is a dropped conjunct; one that says more is a condition
the solver will not enforce."*

## R17 — no new evidence, one CONFIRMING data point · the short-numbered-imperative repair message

The proof run measured a 3-turn freeze broken by a **62-word** numbered
imperative after two **3,900-character** critiques failed. This clause used the
short numbered imperative from turn 2 onward — **173 words / 4 edits, then 150
words / 3 edits** — and got **4 of 4 and 3 of 3 performed exactly, with nothing
else changed**, on turns that were **not** frozen.

**MEASURED: 2 of 2 for the style, on two clauses, in both the frozen and the
unfrozen regime. 0 of 2 for the long style.** **INFERRED, and flagged as
inferred:** that length is the operative variable rather than numbering or the
"change nothing else" terminator, which this run did not separate.

⚠️ **Still `n=2`, and still no rate.** No production change is proposed. The
cheap next measurement is the one this run could not make: a single clause given
the SAME findings at both lengths, on independent draws.

---
# WAVE 3 — `l3239_3382_n002`, decisive convergence turn 3 of 5, $0.008873

## R18 — (a) prompt fix · the PROVIDES block has no placement rule, and NO CHECK READS IT

**Clause/turn:** `l3239_3382_n002`, turn 1.

The node text says *"**PROVIDES** (use EXACTLY these names as the predicates
**this module defines**): - avoid_overstepping"* and the turn-1 draft put
`avoid_overstepping/1` in **`requires`** — declaring that some other node
supplies the one name this node exists to supply. The graph edge is reversed and
the downstream consumer (*"referenced by the imminent harm rule"*) is satisfied
by nobody.

**Why it survives everything.** The NEEDS block spells out its placement rule in
full — *"every one of them belongs in this module's `requires`, spelled EXACTLY
as given; never in `ontology`, never defined here"* — and the PROVIDES block
states **no placement rule at all**. And it is machine-invisible:
`grep -l provides checks.py link.py fixtures.py` returns nothing. The only note
raised is `requires-unprovided`, which the anti-rules record as firing on every
correct single-clause module, so the inversion is indistinguishable from the
benign case.

**Concrete edit — to the corpus renderer's PROVIDES block, mirroring the NEEDS
sentence it already ships:**
> PROVIDES (use EXACTLY these names as the predicates this module defines):
> every one of them must be DEFINED here — as an `ontology` head, ground or
> bodied — and **must never appear in `requires`**, which is only for names
> other nodes establish. A PROVIDES name in `requires` reverses the graph edge
> and no check can see it.

**Second, testable part:** most nodes render `PROVIDES … (none)`. A check that
fires when a rendered PROVIDES name appears in `requires`, or appears in no
head, is cheap and has no false-positive class. Registration if added: it is a
node-side check, so `test_no_reference_leak.QUERY_MODULES` does not apply; a new
test needs `conftest._OPTIONAL`.

## R19 — (a) prompt fix, and an amendment to PROVISIONAL.md · when PROVIDES demands a name the NARROWING excises

**Clause/turn:** `l3239_3382_n002`, turn 1 → turn 2.

`ESTABLISHES` says *"… without overstepping"*; the node's narrowing stops at
*"implied intent"*; and `PROVIDES` commissions a predicate named
`avoid_overstepping`. `PROVISIONAL.md` rules that the narrowed span governs and
that `ESTABLISHES` may not add content — **but it does not contemplate a
PROVIDES name whose whole subject matter is the excised material.** Read
literally, the narrowing rule deletes the very predicate the node was
commissioned to supply.

**Ruled for this clause, with the alternative rejected by name** (full text in
`out/l3239_3382_n002.turns.md`): *the narrowing governs the CONTENT; PROVIDES
governs the NAME.* The predicate is defined here, and every entry carrying its
content is licensed `assumed` with an `inference` naming `ESTABLISHES` — the
route PROVISIONAL's own Ground 2 designates. **Rejected: "delete the material,
because the narrowing excises it"** — deletion leaves the graph edge dangling
with no marker anywhere that a consumer was promised a predicate and did not get
one.

**Concrete edit:** add this as a second numbered case under PROVISIONAL's
"Clauses this file decides", so no later clause re-decides it in a transcript.
⚠️ It is a ruling on an **owner-unratified** file and inherits that status.

## R20 — (a) prompt fix · a body conjunct added for faithfulness is UNDONE by an unrevised `cepa`

**Clause/turn:** `l3239_3382_n002`, turn 2. **Decisive; measured.**

Feedback 1 added `reasonable_to_address(I)` to the body of
`oblige address_implied_intent(I)`, encoding the span's *"**reasonably**
addressing implied intent"*. The draft performed the edit exactly **and left the
closure at `cepa`**, which `00_task.md` line 103 defines as *"silence about that
act **permits** it"*. Net effect: obliged in the reasonable case, **permitted in
the unreasonable one**. The qualifier bought nothing, and every artifact — the
body, the read-back, the claim — looks correct in isolation.

**Why it is new.** P5's ⚠️ warns that a body added for faithfulness *weakens*
the rule. This is the adjacent failure: the body change is right, and a
**different field that was not part of the edit** silently restores what it
removed. `repair`-style editing is exactly where it breeds, because a numbered
edit names one field.

**Concrete edit — `10_output_format.md`, at the forced-`closure` paragraph
(line ~149):**
> ⚠️ **A closure is re-read every time an act's body changes.** If you narrow an
> obliged act with a new body condition, `cepa` on that act class **permits the
> cases you just excluded** and the narrowing has no effect. Ask: what does this
> act class's closure say about the instances my body now excludes?

## R21 — (b) schema gap, PROPOSED not merely recorded · `closure` entries carry no `licence`

**Clause/turn:** `l3239_3382_n002`, turn 2.

`concepts`, `ontology`, `asserts`, `beats` and `defines` all carry
`licence`/`cites`/`inference` (`10_output_format.md` line 107). **`closure` does
not.** On this clause the overstepping material is `assumed` — sourced from
`ESTABLISHES`, absent from the narrowed span — and every entry expressing it
could be marked so **except the closure**, which was `cnpa`: *silence prohibits*,
the strongest global commitment in the module, on content the cited text does
not support, with nowhere to say so.

This is not the `asserts`-cannot-hold-a-disjunction case (R8), where an existing
route served the need. There is **no** route: the reason string is prose and is
not read by the licence machinery.

**Proposal:** give `Closure` the `Licensed` base the other five blocks have. The
migration is additive — existing entries default to `textual` citing the clause
id, which is what they mean today. **This is a schema change and must not be
made on an implementation tier** (`AGENTS.md`, model-tier rule); it is raised
here for design, not for action.

**Interim, at no schema cost:** the prompt can require the closure `reason` to
state when the closure rests on content outside the narrowed span. Turn 3 did
exactly this unprompted-in-form once told the substance — *"the narrowed span
never mentions overstepping, and closure entries carry no licence field, so a
cnpa there is a commitment that cannot be marked as assumed"* — so the reason
string can carry it.

## R22 — (a) prompt fix · NUMBERING is not the load-bearing variable; LENGTH is

**Clause/turn:** `l3239_3382_n002`, turn 4. **A deliberate probe on a
non-decisive turn, reported as such.**

R1 and R17 record the short-numbered-imperative message at 10/10 edits against
0/3 for ~3,900-character critiques, with the note that `n` does not separate
*length* from *numbering*. This turn separated them: feedback 3 held length
(**81 words**), imperative mood and the closing *"Change nothing else."*
constant and varied **only** the numbering — flowing prose, no numerals.
**2 of 2 edits performed exactly, nothing else changed.**

| style | edits performed | turns |
|---|---|---|
| short, numbered, imperative | **12 / 12** | 5 |
| short, **unnumbered**, imperative | **2 / 2** | 1 |
| ~3,900-character critique | **0 / 3** | 3 |

**Consequence for R1:** the recommendation should be stated as *short and
mechanical*, and must **not** be stated as *numbered*, which the evidence does
not support as the active ingredient. `n=1` on the unnumbered condition — this
narrows R1's claim, it does not establish a rate, and the two edits it carried
were cosmetic, which is a weaker test than a decisive one.

## R23 — (a) prompt fix · a LIMIT on an obligation has no legal destination either

**Clause/turn:** `l3239_3382_n002`, final module. **Left open on purpose.**

FINDINGS.md records *"the prompt never says WHERE AN EXCEPTION GOES"* for
*"unless"* arms (R4). This clause is the same hole for a **limit**: *"help …
**without overstepping**"*. The module obliges the helping means and separately
forbids overstepping **on a different act term**, so the solver sees two
unrelated acts and nothing stops the obligation firing where the limit bites.

**Every attachment available is separately banned**, which is why this is a
prompt gap and not a translator defect:
* `not oversteps(...)` in the body — **N5**, under NAF silence licenses the act;
* a positive guard `within_bounds(I)` — **N10**, no substring of the narrowed
  text anchors the name;
* either one — pushes `assumed` content into the body of a `textual` assert,
  against **PROVISIONAL** Ground 2.

**Concrete edit:** `00_task.md` should state the destination for a limit
attached to an obligation, and state what to do when the limiting term is
`assumed`-licensed while the obligation is `textual`. Until it does, the honest
output is an unattached limit **plus an explicit note**, and the prompt gives no
notes field to put it in — the note lives in `claims` only by convention.

## R24 — (c) graph defect · this node supplies a normative predicate with no criterion, forcing it into `inputs`

**Clause/turn:** `l3239_3382_n002`, final module. **No edit fixes it.**

`overstepping/1` ended in `inputs`. The node text defines `inputs` as *"only for
plain facts about the situation being judged (messages, roles, case data)"*.
Whether an action **oversteps** is a normative judgement, and the module's own
gloss says it is *"as defined by the avoid_overstepping policy section"* — i.e.
by **this very module**, which `PROVIDES` `avoid_overstepping`. So the node is
commissioned to define the section and is given a span that states **no
criterion** for it. That circularity is precisely what the turn-1 draft wrote
down literally (`overstepping(A) :- …, overstepping(A)`), and it is not a
translator error so much as the node's shape showing through.

**Why it is a graph defect, not a schema gap.** The node narrows its span to
text that excludes the concept its PROVIDES name is about. Either the narrowing
should extend to *"without overstepping"*, or `avoid_overstepping` should be
provided by whichever node covers the section body. **No per-clause check can
see this** — same class as R9, and it is the second instance, which is the
argument for a graph-level audit of PROVIDES names against their nodes'
narrowed spans rather than two one-off fixes.

---
# ADDED BY CLAUSE 3 — `l4252_4482_n016`

## R25 — PROTOCOL defect (the R12 class), not (a)/(b)/(c) · a calibration answer is stored in PRODUCTION CODE, where the blind adjudicator must read it

**Clause/turn:** `l4252_4482_n016`, turn 1, before any finding was written.

`checks.py` lines 293–301 name this clause **by id** and state its defect —
*"the worst instance in the corpus: ALL THREE of its asserts are inverted"* —
in a comment dated the day of this run. I read it while looking up what
`prefer` means, which is a lookup the protocol REQUIRES for this clause.

**Why this is worse than R12.** R12 was `REVIEW_LIST.md`'s P10 entry naming a
calibration clause, and it was fixed by withholding the id — the list is an
experiment artifact and can be redacted. **This is production source code**, and
the comment is doing real work: it justifies a regex widening and records the
measurement behind it. Redacting it would degrade the code. So the two
requirements — *keep the reason for a check in the code* and *keep the
adjudicator blind* — are in genuine conflict, and there is no free fix.

**Proposal, not a rewrite:** the coordinator should record, per clause, which
production files a blind adjudicator must read to do the job, and check those
against the calibration set BEFORE dispatch. The seat cannot police this
itself; by the time it finds the leak it has already read it.

**Second-order, and independently material.** The `_DISFAVOURED` regex was
**widened on the day of this run because of this clause**. On the regex in
place when the reference set was built, this turn-1 draft raises **zero**
stage-4 notes. **Any comparison of this run's floor result against an earlier
run of the same clause is comparing two different instruments.**

## R26 — (a) prompt fix · rule 5b's own worked examples are exactly the case it gives no encoding for

**Clause/turn:** `l4252_4482_n016`, turn 1. **DECISIVE — every assert in the
module was inverted.**

`status` has **no negative pole**: *"exactly one of `forbid` · `permit` ·
`oblige` · `prefer`"*. Rule 5b closes the obvious escape — *"A comparative is
`prefer`, not `forbid`. 'Minimize side effects', 'avoid excessive hedging',
'favour approaches that are reversible' attach a preference, not a
prohibition."*

⭐ **Two of rule 5b's three illustrations are avoid/minimize comparatives, and
the rule never says what the ACT should be.** So a translator that follows 5b
correctly — as this one did; T2 in the turns record confirms the modality
choice was right — has no guidance at all on the one remaining decision, and
`prefer <the act to avoid>` is the reading the surface grammar hands it.
Measured here as a total inversion of a three-assert module that then passed
`translated / repair_needed=False / 0 breaches`.

**Concrete prompt edit**, to `00_task.md` rule 5b, after the existing text:

> ⭐ **And name the AVOIDANCE as the act.** *"Avoid X"* becomes
> `prefer avoid_x(R)`, never `prefer x(R)` — the latter compiles to a
> preference FOR the thing the document tells you to avoid. `status` has no
> negative pole, so the polarity has to live in the act name. Keep the
> read-back as the clause's own claim (*"X is to be avoided"*); do not rewrite
> it to match.

**(b) schema gap, RECORDED and NOT proposed.** The real fix is a `disprefer`
pole, which `checks.py:polarity_findings` already names as the precondition for
promoting its detector, and `schema.py` is guard-watched. The prompt edit above
is a mitigation, not the fix, and should be labelled as one.

## R27 — (a) prompt fix + a CHECK defect · the review list's remedy and the production check contradict each other, and the corrected module still fires

**Clause/turn:** `l4252_4482_n016`, turn 2. **MEASURED, not inferred.**

Turn 2 applied `REVIEW_LIST.md` P1's own remedy verbatim — *"name the avoidance
as the act (`prefer minimize_redundant_phrases`)"*. The module became correct.
**The `prefer-polarity` detector fired three times on the corrected module,
with text identical to turn 1's except for the act names:**

> `avoid_repeating_prompt(R)` is asserted with status `prefer` but its own
> read-back calls it 'is to be avoided' … the two cannot both be what the
> clause says

They now **can** both be what the clause says. `polarity_mismatches` tests
`status == "prefer"` and matches `_DISFAVOURED` against the read-back, and
**never inspects the act**. So:

* a reader of the notes **cannot distinguish the backwards module from the
  corrected one** — the check's output is bit-identical across the fix it
  exists to provoke;
* and the correct module can only be made to score clean by rewriting its
  read-backs, which is forbidden by name in the anti-rules and is precisely the
  defect-trade `polarity_findings`'s non-disclosable origin was created to
  prevent.

⛔ **And the two artifacts disagree on the facts.** `checks.py` states *"there
is **no correct single-act encoding**"* and makes *"a negative pole in
`status`"* the precondition for promoting the check. `REVIEW_LIST.md` P1 states
a correct single-act encoding and this clause demonstrates it. **One of them is
wrong and an owner must say which.** N5 is the precedent and it favours P1: the
list already endorses encoding a *"without X"* positively as a named predicate
(`omits_ratios_and_techniques(C)`, never `not includes_ratios(C)`), and naming
the avoidance as an act is that same move one level up.

**If P1 is upheld,** the detector needs a second condition — do not fire where
the act functor is itself the avoidance — and its docstring's *"no correct
encoding exists"* claim must go, in the same commit. **Until then the check
reports a false positive on every correctly-repaired instance of the defect it
was built for**, which is the shape that makes a detector's measured recall
meaningless.

## R28 — (c) graph defect · SECOND INSTANCE of R24: a normative judgement with no criterion, forced into `inputs`

**Clause/turn:** `l4252_4482_n016`, turn 1, final module. **No edit fixes it,
and none was asked for.**

`redundant_phrase/1`, `redundant_idea/1` and `repeats_prompt/2` are declared as
`inputs`, which the node text restricts to *"only for plain facts about the
situation being judged (messages, roles, case data)"*. Whether a phrase is
**redundant** is a judgement, not case data — and the narrowed span states no
criterion for it, so the module cannot derive it and `inputs` is the only
available slot.

**This is R24 (`overstepping/1` on `l3239_3382_n002`) on a different clause, a
different node and a different graph author, so it is `n=2` and no longer a
one-off.** The two share an exact shape: the node hands a rule whose operative
term is a normative judgement, narrows the span to text stating no test for it,
and provides no upstream node that defines it. The schema then offers three
slots — `ontology` (cannot derive it), `requires` (nobody provides it),
`inputs` (mislabels it as case data) — and the third is the only one that
compiles.

**This is now the argument for a graph-level audit** of every node's operative
terms against its narrowed span, rather than two one-off fixes. Same
undetectability as R9: **no per-clause check can see it**, because the module
that results is internally consistent and scores clean.

## R29 — no new evidence on style, one MECHANICAL result on GRANULARITY · a conjoined sub-item inside one imperative sentence gets dropped

**Clause/turn:** `l4252_4482_n016`, turns 2 and 3. **Second instance.**

Feedback 1's third edit read *"rewrite the gloss in the graph's own words **and**
say what its one argument is."* The first conjunct was performed exactly; the
second was silently dropped. Feedback 2 re-issued **the dropped conjunct alone**,
69 words, and it was performed exactly on the next turn — **so the drop was
granularity, not content or difficulty.**

⭐ **This is the second instance, and the first was NUMBERED.** Clause 2's
feedback 1 lost a sub-item to a deictic *"that entry"* inside a numbered edit.
**One numbered, one unnumbered ⇒ this is a property of compound edits, not of
the numbering**, and it is the only imperfection in six unnumbered edits and
twelve numbered ones.

**Recommendation for the adjudicator seat, not the prompt:** one imperative
sentence carries one edit. A second demand joined by *"and"* — or referred to
deictically — is the failure mode, and it is cheap to avoid and cheap to
recover from (one 69-word turn here).

**Style tally after clause 3:**

| style | edits performed | turns |
|---|---|---|
| short (62–173 w), numbered, imperative | **12 / 12** | 5 |
| short (69–143 w), **unnumbered**, imperative | **6 / 6** | 3 |
| ~3,900-character critique | **0 / 3** | 3 |

⭐ **R22's open caveat is discharged.** The unnumbered condition was `n=1` and
**cosmetic only**; it now has three turns across two clauses, one of them a
three-part **decisive** rewrite of every assert in a module. **Length and
mechanical imperativeness separate the styles; numbering does not.**

---

# ADDED BY CLAUSE 4 — `l171_426_n022` (the first clause with NO answer key)

## R30 — (b) schema gap / a CHECK ordering defect · a module that fails validation is repaired BLIND on everything except the breach
*(`l171_426_n022`, turn 1)*

**MEASURED by reading the code, not inferred.** `checks.run_checks`
(`checks.py:555–562`):

```python
mod, breaches = schema.validate_all(...)
findings = [Finding(SCHEMA_CHECK_ID, "error", ...) for b in breaches]
if mod is None:
    return CheckResult("invalid", None, findings, attempt, None)
```

`arity_findings`, `polarity_findings` and `_link_findings` are **all downstream
of that return.**

**The measurement.** This clause's turn-1 draft returned `invalid` with 4
breaches and **0 notes**. Turn 2 — the same module with the four breach causes
removed and nothing else added — returned **8 notes**. Clause 3's turn 1
returned 18. **So the zero was an artifact of the short-circuit, not a property
of the draft.** The draft carried three defects that change what the module
concludes (a root/relative conflation, an out-of-scope claim, a miswired
argument order) and the repair loop's first round could see none of them.

**Why this is not the abstention case.** The two returns above it are
deliberate and documented (an abstention has no bodies to check, and adding
findings before that return could only turn a terminal outcome into a repair
round). `mod is None` is different: it is a *malformed* module, not a terminal
answer, and it is **going back round the loop**. The loop then spends an
attempt optimising for the only signal it was shown.

**Concrete proposal, stated as a question because it is not free.** Several
findings genuinely cannot be computed without a validated `mod`. But
`_link_findings` runs on a **rendered `.lp`**, and a module that fails only on
a *missing gloss* is structurally renderable. Is a partial pass available —
render what validates, report the breaches **plus** whatever link findings the
partial render yields, and mark them as computed against an invalid module? If
not, the honest alternative is cheap: **when `outcome == "invalid"`, say so in
the repair message** — *"this module was not checked past validation; expect
further findings once it parses"* — so neither a model nor a reader reads an
empty findings list as a clean bill.

---

## R31 — (c) graph defect · a THIRD case of the `inputs`-normativity shape, DECLINED as an instance, and the decline is the recommendation
*(`l171_426_n022`, turns 1–3)*

`argument_about_application/2` and `direction_about_application/2` sit in
`inputs`. They are the classification the span is *about*: the module asks the
situation to hand it *"this is an argument about how higher-level instructions
should be applied to your current behaviour"* and then attaches `forbid`.

**Same shape as R24 (`overstepping/1`) and R28 (`redundant_phrase/1`). NOT
counted as the third instance.** Two grounds, and recording them is worth more
than the increment:

1. **Evaluative vs topical.** R24 and R28 pushed away *judgements* — whether
   conduct is *overstepping*, whether a phrase is *redundant*. This one pushes
   away a *topic* classification. They are not the same defect and a rule that
   catches both will catch every input predicate.
2. ⭐ **The cause is different, and it is the graph's, not the author's.**
   `PROVIDES` is **(none)** on this node — *"use EXACTLY these names as the
   predicates this module defines"*, and the list is empty. The module is
   **contractually forbidden to define any predicate**, so `inputs` is the only
   slot remaining. R24/R28 were placement choices; this was forced.

**What to do with it.** Do NOT collapse the three into one count. **Split the
population**: the R24/R28 pair asks whether a node hands down a normative
predicate with no criterion; this asks whether **`PROVIDES: (none)` is
compatible with a node whose `ESTABLISHES` turns on a classification nothing
else in the graph supplies.** If the answer is no, the fix is in the
decomposition — a node that establishes a norm over a class should either
`PROVIDE` that class or `NEED` it — and **no per-clause check can see it**,
which is what makes it a graph defect rather than a translation one.

---

## R32 — (b) schema gap, PROPOSED · nothing compares a `closure`'s REASON to its VALUE
*(`l171_426_n022`, turn 2 → turn 3. Neighbour to R21.)*

Turn 2 performed *"set both `closure` values to `unclear`"* exactly — and left
both reasons verbatim from turn 1:

> `"closure": "unclear"`, `"reason": "… silence about other arguments **permits**
> them"`

`schema.py:650` requires *"one sentence, from the clause, for **this
reading**"*, and `render_lp` prints the pair on one line:

```
%% closure: engage_in_argument = unclear   % … silence about other arguments permits them
```

**Why this is not cosmetic.** Failure mode #13 records that the contradiction
verdict FLIPS on the closure, and that *"`open` and `cepa` are bit-identical —
nothing records that a commitment was made."* **The `reason` IS the record.** A
`unclear` whose reason states `cepa`'s reading leaves the commitment recorded
backwards, which is strictly worse than the unreasoned closure the validator
already rejects. The module passed `translated / repair_needed=False / 0
breaches` in that state.

**Proposal, deliberately weak because the strong version is unavailable.** A
general reason-vs-value check needs to read English and is not on offer. But the
three readings have **three narrow lexical fingerprints** — `cepa`'s reason says
silence *permits* / *allows*, `cnpa`'s says silence *prohibits* / *forbids*,
`unclear`'s says the clause does not *settle* / *leaves open*. A `note`-severity
check firing when a reason contains the fingerprint of a **different** value
than the one declared would have caught this exactly, costs one regex per
reading, and — like `polarity_findings` — should carry a **non-disclosable
origin** so it can never turn a terminal outcome into a repair round.

⚠️ **Register the adjudicator's share of this.** The edit sent said *"set both
`closure` values to `unclear`"*, and the value is precisely what changed. The
draft did what it was told. Recovery cost one 110-word turn.

---

## R29 REFINED — the unit that survives a compound edit is the SENTENCE, not the numbered item
*(`l171_426_n022`, feedback 1 → turn 2. Counter-instance.)*

R29 concluded from two drops that *"one imperative sentence carries one edit"*
and that compound edits are the failure mode. **This clause supplies a
counter-instance that sharpens it rather than overturning it.**

Feedback 1 was a **three-part compound edit**, and its first part alone ordered
**five deletions plus one move** (both `ontology` entries, one claim, two
concepts, and `higher_level_instruction/1` relocated into `inputs`). **All of it
was performed exactly, nothing dropped, nothing else changed.**

**The difference from the two recorded drops is structural, and it is not
size.** Both drops were **conjoined sub-items inside a single sentence** — *"…in
the graph's own words **and** say what its one argument is"* (clause 3), and a
deictic *"that entry"* (clause 2). Here every demand had **its own sentence or
its own explicit enumeration** (*"`inputs` then holds exactly A, B, C"*).

**Refined statement:** a compound edit is safe to the extent that each demand
occupies its own sentence and names its own target explicitly. What gets dropped
is a demand **hitchhiking on another demand's sentence**, or one referring to its
target deictically. Tally now: **16/16 numbered, 6/6 unnumbered, 0/3 long**, two
drops, both of the hitchhiking shape.

---

## R33 — (a) prompt fix + a REVIEW-LIST fix · the anti-rule that saved this clause is written about `status` and its mechanism is about ANY independently-written pair
*(`l699_796_n012`, turn 1 → feedback 1. MEASURED: it inverted an edit I had already drafted.)*

**The anti-rule, as written:** *"Never make `status` and `read_back` agree by
rewriting the read-back. The two are written independently and that redundancy
is the only place a wrong status is visible. Fix the status."*

**What happened.** Turn 1's body had three conjuncts
(`tool_instruction(I), instruction_might_be_intended(I), serious_side_effects(I)`);
its `read_back` named two, and so did claims C1 and C2. Adjudicating blind I
raised this as F3 and drafted the remedy *"name the tool conjunct in the
read-back"*. **The read-back, C1 and C2 were the draft's own three independent
votes that the conjunct did not belong** — `tool` is in `ESTABLISHES` and not in
the narrowed span — and the edit would have deleted that evidence while leaving
the defect in place. The correct edit was to delete the conjunct, which
discharged the finding and a reversed clean call at once.

**The gap.** The anti-rule's *mechanism* — two artifacts written independently,
so their disagreement is the only visible signal — governs **body vs read-back**
and **claims vs read-back** exactly as much as **status vs read-back**. As
written it names only `status`, and a translator (or an adjudicator) reading it
literally is unprotected on the other two.

**Proposed wording, for `REVIEW_LIST.md`'s anti-rules block:**

> **Never resolve a disagreement between an assertion and its prose by editing
> the prose.** `status`, `body`, `read_back` and the `claims` entry are written
> independently, and their disagreement is the only place a wrong one is
> visible. Decide which side is defective and fix that side. This covers a
> `status` the read-back negates, a body conjunct the read-back does not name,
> and a claim no assert encodes.

**(a) prompt fix, secondary.** `00_task.md` rule 11 says the read-back is *"the
sentence a reader sees instead of the formal item"*. It does not say that the
two are written independently **on purpose**, so nothing in the production
prompt tells a translator that making them agree is the cheap wrong move. One
sentence would.

---

## R34 — (c) graph defect · a FOURTH case of the `inputs`-normativity shape, DECLINED for the second time, and the two declines now have a shared criterion
*(`l699_796_n012`. n=2 still stands. Read alongside R24, R28, R31.)*

`could_cause_serious_side_effects/1` sits in `inputs` and the span supplies **no
criterion whatever** for what makes a side effect *serious*. Same **shape** as
`overstepping/1` and `redundant_phrase/1`.

**DECLINED as an instance, for the second time in two clauses, and the reason is
now stateable as a test rather than as a judgement call.** R24/R28's class is *a
determination the SPAN should have made and the module pushed away*. The two
declines share a property the two confirmed instances do not:

| | judgement | who could have made it |
|---|---|---|
| `overstepping/1` (R24) | evaluative | the span states the norm it violates |
| `redundant_phrase/1` (R28) | evaluative | the span states the norm it violates |
| `argument_about_application/2` (R31) | **topical** | forced: `PROVIDES: (none)` |
| `could_cause_serious_side_effects/1` (here) | **evaluative** | forced: the span supplies no criterion at all, and its whole content is the *uncertainty* |

**The proposed test, for whoever adjudicates the class:** an `inputs` entry is an
instance of R24 only if **the span itself contains the material to decide it**.
Where the span's own content is the *absence* of a criterion — a modal
(*"might"*, *"could"*) or an unglossed evaluative (*"serious"*) — pushing it to
`inputs` is the **only honest placement**, and counting it inflates the class
with cases no graph change could fix.

⚠️ **The recommendation is the decline, not a fix.** Four clauses have now
produced this shape and two were forced by the span. **Do not act on R24/R28
until a case appears where the span supplies the criterion and the module pushes
it away anyway.**

---

## R35 — (c) graph defect, small and cheap to fix · `ESTABLISHES` silently restores a subject the narrowed span elides, and `PROVISIONAL.md` then forces the module to state something broader than the document
*(`l699_796_n012`. MEASURED: this clause's only reversed call, and its only remaining open item.)*

**The mechanism, which is new and is a defect in the NARROWING, not in
`ESTABLISHES`.** The node's SOURCE TEXT block is a **grammatical fragment** — a
single list bullet, *"- seek clarification when instructions might be intended
but could cause serious side effects"* — and the sentence that supplies its
subject, *"The assistant should use context, common sense, and careful judgment
to decide how to treat **tool instructions**:"*, is **one line above it in the
document and is not printed in the node at all**. `ESTABLISHES` restores *tool*;
the narrowed span cannot.

**Why this is not just another `ESTABLISHES`-vs-span disagreement.**
`PROVISIONAL.md`'s ground 1 is *"the narrowed SOURCE TEXT is quoted verbatim
from the document … where a derived artifact and its source disagree, the source
is the record."* That argument assumes the span is a **self-contained
proposition**. Here it is not: read alone it is not even a sentence, and
following the ruling makes the module assert an obligation over **all**
instructions, which is broader than the document's own sentence. **The ruling
was applied (turn 2 deletes `tool_instruction`) because it is the standing
ruling and a transcript is not the place to overturn one** — but this clause is a
sharper test of it than `l831_1000_n005`, where the span was a full sentence and
the divergence was a parenthetical.

**Three routes, in increasing cost:**

1. ⭐ **Cheapest, and it fixes the cause:** when a node's narrowed span is a list
   item, the narrowing should include **the stem that governs the list**. The
   graph already knows the bullet is a bullet — it printed the leading `- `.
2. Add this clause to `PROVISIONAL.md`'s *"Clauses this file decides"* list with
   the fragment case called out, so the owner ratifies or overturns on the
   sharper example rather than the parenthetical one.
3. Leave it, and accept that every bullet-list node in the corpus translates
   without its stem's subject. ⚠️ The `ignore_untrusted_data` section alone has
   **four** sibling bullets under one stem, so this is not a one-clause problem —
   the other three nodes will each hit it.

**No per-clause check can see it**, exactly as with R9: each module is
individually well-formed and cites correctly.

---

## R36 — (c) graph defect · a node lists ONE name in **both** `PROVIDES` and `NEEDS`, and the two halves of the prompt contradict each other on it

*Clause 6, `l1001_1107_n005`, turn 1. Pre-registered in the span enumeration
before the draft existed.*

The node hands the translator this:

```
PROVIDES (use EXACTLY these names as the predicates this module defines):
  - root_authority: rules in the #protect_privacy section carry root authority
NEEDS -- ... every one of them belongs in this module's `requires`, spelled
EXACTLY as given; never in `ontology`, never defined here:
  - root_authority: the authority level of rules in the #protect_privacy section
```

**"the predicates this module defines" and "never in `ontology`, never defined
here" cannot both be obeyed for one name.** The translator must disobey one half
of its instructions, and nothing in the output records that it was forced to.

**MEASURED, and it is systematic, not a one-off.** Across the thirteen nodes of
`L1001-1107`, **all thirteen** list `root_authority` under NEEDS — including the
two **heading** nodes (`n001` for `#respect_creators`, `n005` for
`#protect_privacy`) that also list it under PROVIDES. A per-node NEEDS list would
not list a node's own output; this one is a section-wide blanket applied
uniformly.

**What turn 1 actually did: BOTH.** It put `root_authority/1` in `requires` *and*
made it the head of its only `ontology` rule. That satisfies both texts and is a
**false statement of provenance** — `requires` means *"another clause must define
it"* (rule 9), and failure mode #15 exists to keep that honest.

⚠️ **`schema.py` cannot see it.** There is a `requires` ∩ `inputs` check
(`schema.py:807`); there is **no** `requires` ∩ `ontology` check. Both horns, and
the both-horns answer, pass the floor with zero breaches.

⚠️ **And the two glosses are not the same proposition.** PROVIDES glosses a
**claim** (*"rules … carry root authority"*); NEEDS glosses a **value** (*"the
**authority level** of rules …"*). A claim over rules is arity 1; an authority
*level* is a value or an arity-2 relation. **This is R9's shape appearing inside a
single node**, where for once it is visible without cross-clause comparison.

⭐ **The choice is not free — the schema forces it.** `schema.py:789` rejects a
`translated` module that emits no assertion, definition, superiority or ontology
fact. So the NEEDS horn (name in `requires`, defined nowhere) **cannot produce a
translated module at all**; it can only produce an abstention. Only the PROVIDES
horn yields a module.

**Two routes:**

1. ⭐ **Cheapest and correct:** when the graph builds a node's NEEDS list, subtract
   that node's own PROVIDES names. One set difference at graph-build time, and it
   fixes every heading node in the corpus at once.
2. Add a `requires` ∩ `ontology` breach to `schema.py` so the both-horns answer is
   loud instead of silent. ⚠️ This is a **second-best**: it catches the symptom in
   the translator's output, after the node has already made the contradiction
   unavoidable, and it would fire on a translator that had no better option.

⛔ **Rejected by name: "let the translator pick and say so in `claims`."** It
converts a graph defect into a per-clause judgement call, made 15 times
independently, in the one field nothing checks.

---

## R37 — (c) graph defect · `ESTABLISHES` and `PROVIDES` want a predicate over RULES; the span can only support one over the SECTION, and eight siblings borrow it

*Clause 6, `l1001_1107_n005`, turn 2. This is the run's most contestable
judgement and it is filed as a question, not as a fix.*

The node's narrowed span, entire:

> `#### Protect people's privacy {#protect_privacy authority=root}`

`ESTABLISHES` demands *"every rule under it is a **root-level rule**"*; PROVIDES
glosses `root_authority` as *"**rules** in the #protect_privacy section carry root
authority"*. **Both range over rules. The span names no rule and contains no word
for "rule".**

Turn 1 bridged the gap by coining `rule_under_heading/2` and putting it in
`inputs`. **That makes the module's only rule incapable of ever firing** — no
situation being judged ever supplies "rule X sits under heading Y" — which is
failure mode #3 arriving **behind a clean floor** (`translated`,
`repair_needed=False`, 0 breaches, 2 informational link notes).

Under `REVIEW_LIST.md` **N1** (*"reserve ground atoms for facts about the DOCUMENT
(`root_authority(section_x)`)"*), **N10** (no substring of the narrowed span
anchors `rule_under_heading`), **P6** and **`PROVISIONAL.md`** (*"`ESTABLISHES` …
may not add content the narrowed span does not state"*), turn 2 encodes the ground
fact `root_authority(protect_privacy)` and records the divergence in `claims`.

⛔ **THE COST, STATED PLAINLY.** Measured: eight sibling nodes (`n006`–`n013`)
borrow `root_authority` with a NEEDS gloss about **rules**. This module is their
**sole provider** and now offers a fact about a **section**. If they write
`root_authority(some_rule)` they link by name and mismatch on the domain —
**failure mode #9, at link time, invisible to every per-clause check.**

⚠️ **I did not pre-empt it, deliberately.** `30_failure_modes.md` group ② says in
terms: *"Do not invent shared vocabulary to pre-empt them — that is a separate
stage's job, and guessing at it from one clause makes it worse."* So the
recommendation is not "translate it differently"; it is that **the graph is asking
one node to be the section's authority provider from a span that contains no
rules.**

**Three routes:**

1. ⭐ **Widen the heading node's narrowing to the section it heads**, or give the
   node a PROVIDES gloss the span can actually support (*"the #protect_privacy
   section carries root authority"* — i.e. drop *"rules in"*). The second is a
   one-line graph edit and makes PROVIDES, the span and the module agree.
2. Have the graph state the scoping convention **once**, as its own node, so
   "a rule under a root-authority heading is a root-level rule" is a claim some
   module owns and cites, instead of an unwritten step every heading node must
   smuggle.
3. Leave it, and accept a section-level provider against rule-level borrowers.
   ⚠️ `n001` (`#respect_creators`) has the identical shape, so this is at minimum a
   **two-node** problem, and every `authority=root` heading in the document is a
   candidate.

**No per-clause check can see it**, exactly as with R9 and R35: each module is
individually well-formed and cites correctly.

---

## R35 — THIRD INSTANCE, and the extreme one · a narrowed span with **zero finite verbs**

*Clause 6, `l1001_1107_n005`. Not a new recommendation — evidence for the standing
one, recorded here so R35's population is countable.*

R35 was raised on a bullet whose governing stem sat one line above and was never
printed. **This clause is worse:** the narrowed span is
`#### Protect people's privacy {#protect_privacy authority=root}` — a markdown
title plus a machine attribute.

Run the list's own two counting tests on it:

* **N9** — *"how many finite verbs does the narrowed text contain, and how many
  propositions does `ESTABLISHES` demand?"* → **zero verbs, two propositions.**
  N9 records that this ratio is *"why two clauses burned every repair attempt and
  emitted nothing"*.
* **N2** — *"what is the main verb and who is its subject?"* → **there is no
  answer to return.**

⭐ **The brief's test applies literally: "if your narrowed text has no finite verb
or no subject, say so explicitly." It has neither.** This is the third instance
and it is the one that most cleanly justifies a graph-level fix rather than
per-clause translation around it: **a node whose span parses as no proposition at
all cannot be checked against its `ESTABLISHES` by any means available to the
translator.**

⚠️ **And `00_task.md` names this exact case as an ABSTENTION ground** — *"it is a
section heading"*, its **first** example. So the graph is issuing nodes whose spans
the production prompt tells the translator to decline, while `ESTABLISHES` tells it
to translate. **That conflict is worth an owner ruling on its own**, separately
from R35's narrowing fix: either heading nodes stop being emitted, or the prompt's
abstention list stops naming section headings.

---

## R38 — (b) schema gap + a CHECK defect · nothing detects a VARIABLE used with two incompatible meanings inside one rule, and P3's fingerprint has a second form

*Clause 7, `l1368_1541_n019`, turn 1. MEASURED, including a counterfactual floor
run.*

The unaided draft emitted this:

```json
{ "status": "oblige",
  "act":  "suggest_precautions(S)",
  "body": "dangerous_situation(S), responding_to(R, S), safety_precaution_suggestion(S), part_of_response(S, R)" }
```

`S` is one variable. The module's **own glosses** give it two incompatible
meanings — `dangerous_situation`: *"**S is a situation** in which there is a risk
of imminent real-world harm"*; `safety_precaution_suggestion`: *"**S is a
suggestion** that the user take safety precautions"*. The rule fires only where a
dangerous situation **is** a safety-precautions suggestion **and** is part of the
response to itself. **No coherent case satisfies it**, so the span's entire middle
conjunct is inert.

**MEASURED, and this is the recommendation's whole force.** I patched the object
locally, adding **only** the one `concepts` entry the schema breach named and
changing nothing else, then re-ran `schema.validate_all` + `checks.run_checks`:

```
breaches: []   outcome: translated   repair_needed: False
13 [note/link] — 1 requires-unprovided, 6 concept-declared, 6 situation-input
```

**Zero errors, zero warnings.** Arities are consistent, polarity is consistent,
every name is declared — the defect lives entirely in the *identity* of a
variable across two predicates, and nothing in the floor looks at that. Turn 2's
real floor output later reproduced those 13 notes exactly, confirming the
counterfactual was faithful.

⭐ **This is failure mode #3 reached through the VARIABLE rather than through a
predicate**, and it is a distinct shape from every prior instance in this run,
which were all *"a coined name waiting on a fact no situation supplies"*.

⭐⭐ **And it extends P3.** P3 reads: *"a claim present in `claims` and encoded
nowhere is the fingerprint."* Here C2 is present in `claims`, present in `acts`,
present in `closure` **and present in `asserts`** — and still encoded nowhere,
because its encoding cannot fire. **A `claims`-to-`asserts` cross-check, which is
what P3 currently asks for, passes this module.**

**Two routes, and they are independent:**

1. ⭐ **(b) A cheap deterministic check, and it is genuinely cheap.** For each
   `asserts`/`ontology` body, group the predicates by shared variable and compare
   their `concepts` glosses' **subject phrases** (*"S is a situation …"*, *"S is a
   suggestion …"*). Two glosses that open by declaring the same variable to be
   different kinds of thing is a strong, low-false-positive signal, and every
   ingredient is already in the object. Even the crudest version — **flag any
   variable that appears in ≥2 body predicates whose glosses' leading noun phrases
   differ** — would have caught this.
2. **(a) A prompt line, in `10_output_format.md` beside the body/atom split.**
   *"A variable is one thing throughout a rule. Before you finish a body, read each
   variable's occurrences together and check every concept gloss is talking about
   the same object."* ⚠️ Note the near-miss that generated it: the collision arose
   because the conjunct's noun (*"**s**uggestion"*) shares an initial with
   *"**s**ituation"*, and the two sibling asserts in the same module used distinct
   letters correctly. **A single-letter convention is doing load-bearing work with
   nothing enforcing it.**

⚠️ **Amend P3 in `REVIEW_LIST.md` as well:** its "Ask" should become *"check every
entry in `claims` against the asserts — and for each one you find, check that its
rule can fire."*

---

## R39 — (b) schema gap, RECORDED and PROPOSED · an obligation to PRODUCE something cannot be stated, and the prompt's own worked example teaches the shape that voids it

*Clause 7, `l1368_1541_n019`, both turns. This survives into the final artifact
and is the clause's most contestable judgement.*

The span: *"It should instead **provide a disclaimer** …, **suggest** that the user
take safety precautions, and **provide generic advice** …"*. Three duties to
produce something that is not there yet.

Every one of the three asserts in the shipped module carries `part_of_response(X,
R)` in its body:

```
oblige provide_disclaimer(D) :- dangerous_situation(S), responding_to(R, S),
                                disclaimer_acknowledging_lack(D), part_of_response(D, R).
```

**So the duty fires only where the response already contains D.** An assistant
that responds to a dangerous situation with **none** of the three things violates
nothing in this module — there is no `D` to bind, so the rule is silent. **The
obligation can be discharged only by an assistant that has already discharged it.**

**The vocabulary offers no alternative.** `asserts(ClauseId, Status, Act)` takes an
**indexed** act term, and `10_output_format.md` requires the indexing in bold
(*"Writing a material where an act belongs means the query side joins nothing"*).
There is no way to say *"obliged: **there exists** a D in R such that …"*. Dropping
`part_of_response(X, R)` does not fix it — it only unties the item from the
response, leaving a duty about a free-floating disclaimer.

⚠️ **And the prompt teaches the shape.** `20_worked_example.md`'s
`l4251_4571_n029` writes `prefer respond_with(R)` with body `brief_overview(R),
open_question(Q), answers_question(R, Q)` — the same structure, and benign there
**only because `prefer` ranks candidate responses that already exist**. Carried
over to `oblige`, the identical structure produces a duty that cannot be violated.
**The worked example is correct for its own status and misleading for the one the
translator most often needs.**

⛔ **Rejected by name: scoring this as a translator defect.** It is not one. The
draft used the only construction the schema and the worked example offer, and no
edit available in this vocabulary improves it. **The span does not decide between
keeping and deleting the conjunct, so the module was left alone and the gap is
recorded here instead.**

**Proposed, smallest first:**

1. **(a) A prompt paragraph distinguishing an obligation to ACT from a status on a
   CANDIDATE act**, with a worked `oblige` example — the current one is `prefer`
   only. State plainly which reading `oblige` carries in this corpus, because a
   reader cannot tell from the example given.
2. **(b) A schema route for a duty whose act is existentially quantified** — even a
   flag on the `asserts` entry (`existential: true`) would let the query side tell
   *"this response's disclaimer is obliged"* from *"a disclaimer is obliged and
   this response has none"*. These are different verdicts and are currently
   identical in the output.

⚠️ **Scope.** Any node whose span says *provide / include / offer / suggest / add*
is affected, and the direction of the error is **permissive** — the corpus concludes
"no violation" where the document says a duty was breached. That is the direction
`PROVISIONAL.md` ground 3 calls indistinguishable in the output from a real rule.

---

## R40 — (a) prompt fix · `should` and `must` are the document's own strength contrast, and the four-value `Status` cannot hold it

*Clause 7, `l1368_1541_n019`. Small, cheap, and it is a MEASURED gap rather than a
defect found in a module.*

The full source span is two sentences and the contrast is inside it:

> *"The assistant **must** avoid overstepping … It **should** instead provide a
> disclaimer …"*

The narrowing keeps only the *"should"* sentence. `Status` is exactly
`forbid`/`permit`/`oblige`/`prefer`, so *"should"* and *"must"* both compile to
`oblige` and **the compiled module is byte-identical either way**. P7 records the
same mechanism for defeasibility (*"an unconditional `oblige` is byte-identical to
one whose default was dropped"*); this is its **strength** analogue and the review
list does not name it.

**The draft handled it as well as the prompt allows**, which is why this is not
scored against it: all three `read_back`s and all three `claims` say *"should"*,
so the softness survives in the English a reviewer reads even though it is absent
from the formal item. **Checked and recorded as clean; the gap is upstream.**

⛔ **Rejected by name: routing *"should"* to `prefer`.** Rule 5b reserves `prefer`
for comparatives (*"minimize"*, *"favour"*), and *"should provide a disclaimer"* is
not one. Using `prefer` as a soft-obligation slot would collide with P1's measured
polarity failure and would make the two unreadable apart.

**Proposed:** one paragraph in `00_task.md` beside rule 5b — *"`oblige` covers both
'must' and 'should'. The document's strength distinction is not expressible in
`Status`; carry the document's own modal word into the `read_back` and into
`claims` so it survives where a reader can see it."* That is what a careful
translator already did here, unprompted, and writing it down makes it checkable
rather than lucky.

⚠️ **Do not "fix" this by adding a fifth `Status`** without a separate decision:
every downstream query, the closure semantics and `beats` all assume the current
four, and R21/R32 show how much rides on the deontic vocabulary staying small.

---

# FROM CLAUSE 8 — `l1707_1973_n022` (converged turn 2 of 5, $0.00344)

## R41 — (b) CHECK DEFECT · a rule that derives NOTHING counts as a definition, so a dead rule BUYS SILENCE from the link checker

**MEASURED, in both directions, on one name with everything else held fixed.**

Turn 1's `ontology` held one entry:

```json
{ "atom": "underlying_prompts(P)", "body": "underlying_prompts(P)" }
```

which renders `underlying_prompts(P) :- underlying_prompts(P).` — failure mode #3
in its purest form. `underlying_prompts/1` was **also** in `inputs`.

| | notes raised on `underlying_prompts/1` |
|---|---|
| turn 1, self-loop present | **0** |
| turn 2, self-loop deleted, nothing else about the name changed | **2** (`concept-declared`, `situation-input`) |

The other two `inputs` names raised two notes each in turn 1. **The dead rule was
the only difference.**

**The mechanism, and it is in the source.** `walkthrough/link.py:894`:

```python
headless = {_atom_id(name, parens) for name, parens in NO_HEAD.findall(blob)}
```

`headless` is read out of **clingo's own no-head warnings**. A self-loop gives the
atom a head, so the name is not headless, so neither `concept-declared` nor
`situation-input` can fire on it. And clingo — which **did** run on this module,
since the notes come from `_check_clingo`'s output — said nothing about the
self-loop, because an unfounded atom is not a warning.

⚠️ **Why this is worse than a missed detection: the check is anti-monotone in
module quality.** Deleting a rule that enforced nothing made the checker *louder*.
A translator or a repair loop optimising toward a quiet notes list is being paid
to keep dead rules in `ontology`, and the cheapest way to silence a
`situation-input` note is to add one.

⚠️ **This also interacts with the standing warning about the `situation-input`
note** (*"fires on `headless & declared_inputs`, so a declared-and-unused name
raises no note"*, six confirmations). That warning says the note carries no
information about **use**. R41 adds: **it carries no information about
DEFINEDNESS either** — a name with a vacuous head is indistinguishable from a
name with a real one.

**Proposed, and deliberately the cheap version:** a check that is **not** about
headlessness — for every `ontology` entry, is the entry's `atom` functor
**identical** to a functor in its own `body`? That is P8's ask, which no code
currently runs. It is a string comparison over the emitted object, needs no
solver, and would have fired on this module. ⛔ **It must be written to
distinguish the anti-rule case** (`forbid X(R) :- X(R)`, an **assert** whose body
binds a variable act — schema-forced) from an **`ontology`** entry deriving
itself. Field-scoped, the two do not collide.

⚠️ **Do not "fix" this inside `link.py` by changing how `headless` is computed.**
The no-head reading is correct for what it is for; the gap is that nothing else
looks at self-derivation.

---

## R42 — (a) PROMPT FIX + REVIEW-LIST FIX · N10 anchors a coined name to a SUBSTRING and is blind to WHICH SENTENCE the substring came from — which is exactly how an analogy leaks

**MEASURED here, on the clause's decisive defect.** Turn 1 coined
`policy_explicitly_allows/1` and put `not policy_explicitly_allows(P)` in the
body of a prohibition about **the assistant's system and developer prompts**.

Run **N10** on it — *"for each name you coin, which substring of the NARROWED span
does it come from?"* — and it **passes**: the substring *"unless policy explicitly
allows it"* is right there in the narrowed span. **N10 cannot see that the
substring belongs to a different sentence, about a different subject.**

The span's shape is **vehicle → `Similarly` → tenor**:

> S2 *"…**the manual itself** --- its text, structure, and even its existence ---
> should not be disclosed **unless policy explicitly allows it**."*
> S3 *"Similarly, **the assistant** can share its identity and capabilities, while
> keeping the underlying system or developer prompts **private by default**."*

The exception is attached to a **training manual belonging to a customer-service
agent** — an entity the document does not regulate and that no situation the
corpus is asked about will ever contain. The tenor's defeasibility marker is
*"by default"*, which names **no** defeater at all. Importing S2's named, closed
exception into S3 **narrows the document**: it asserts that explicit policy
permission is the *only* thing that can defeat privacy.

⛔ **Rejected by name: re-licence the conjunct as `assumed`, with the inference
*"`Similarly` licenses carrying the manual's exception across to the prompts."***
Rejected on the span, not on the schema: **the tenor supplies its own, different
defeasibility marker**, and the author had S2's phrasing in hand one sentence
earlier and wrote *"by default"* instead. What `Similarly` licenses is the
transfer the sentence itself performs. **N5 condemns the conjunct independently**
— it is negation-as-failure licensing an act by the absence of a fact — and two
independent grounds converging is the reason this call is signed without an
answer key.

**Proposed — N10 gains a second half:**

> *"…and **which sentence** of the narrowed span is that substring in, and is
> that sentence about the assistant? A span may set up an analogy and then apply
> it. Only the applying sentence governs; the illustration's own norms, subjects
> and exceptions are not the module's, however normative they sound."*

**Proposed — one sentence in `00_task.md`, beside rule 1:**

> *"Where a span states an analogy and then applies it (`similarly`, `just as`,
> `in the same way`), translate only the application. The illustration is context
> for a reader, not a source of predicates, acts or exceptions."*

⚠️ **This is not P6/`PROVISIONAL.md`.** That pair governs `ESTABLISHES`-vs-span
disagreement, and here the two **agree** — `ESTABLISHES` compresses the whole
analogy into one semicoloned sentence, vehicle included. The leak is **inside**
the span, between its own sentences, where no existing entry looks.

---

## R43 — (a) PROMPT FIX · the abstention ground *"it is an example"* has no PARTIAL form, and this span is two-thirds illustration

`00_task.md` lists *"it is an example"* among the grounds for abstaining, and
S1 says in so many words *"A useful analogy is…"*. But the paragraph does not stop
at the analogy: S3 states a permission and a default about the assistant in the
document's own voice, and `ESTABLISHES` names that as the claim the module must
express.

**The prompt offers only two moves — abstain on the whole span, or translate the
whole span — and neither is right here.** The correct move is *translate S3,
record S1–S2 in `claims` as provenance, and put nothing from them in `acts`,
`asserts`, `ontology` or `closure`.* The draft found it unaided (H1, my primary
pre-registered defect, **did not fire**), which is evidence the shape is
learnable — but nothing in the prompt says it.

**Proposed:** extend the abstention paragraph — *"Abstention is whole-span. If
part of a span is illustration and part states a norm, do not abstain: translate
the norm and record the illustration in `claims`."*

⚠️ **Low priority, and the reason is a real measurement:** the unaided draft got
this right, and got the `cnpa` closure right, against my pre-registration on both.
This is a gap in the instructions, **not** a demonstrated failure. Recorded so it
is countable if a later clause does leak an illustration into `asserts`.

---

## R44 — (a) REVIEW-LIST FIX, small · N1's illustrative ground atom is `root_authority(section_x)`, and `root_authority` is a NEEDS name on this node

**N1** — the list's own highest-value entry — closes with:

> *"Reserve ground atoms for facts about the DOCUMENT (**`root_authority(section_x)`**), where there is no situation to match."*

This node's `NEEDS` block reads:

> *"- **root_authority**: Rules in the protect_privileged_information section carry root authority."*

with the standing instruction that NEEDS names belong *"in this module's
`requires`, spelled EXACTLY as given; **never in `ontology`, never defined
here**."*

**A translator handed both would read N1 as an instruction to write
`root_authority(protect_privileged_information)` into `ontology` — which the node
header forbids outright.** The draft did not fall for it, and D1 (leave the name
unused in `requires`) was ratified twice over by P9's correction and by anti-rule
2. But the collision is live, it is exact, and it costs nothing to remove.

**Proposed:** change N1's parenthetical to a name that is **not** in any node's
`NEEDS` block — e.g. `heading_of(section_x, privacy)` — and add one clause:
*"…unless the name is a `NEEDS` name, which belongs in `requires` and is never
defined here, however document-shaped it looks."*

---

# FROM CLAUSE 9 — `l2126_2404_n016` (converged turn 3 of 5, $0.00597)

*New clause: no reference verdict, no known defect, no answer key. `ESTABLISHES`
and the narrowed span are **byte-identical**, so nothing here comes from a
narrowing defect.*

## R45 — (a) PROMPT FIX + (b) CHECK GAP · several `ontology` heads sharing ONE body are COEXTENSIVE, so a module can oblige and forbid the same act — and `P4`, the nearest review-list entry, PASSES it

**MEASURED on the turn-1 draft, which scored `translated / repair_needed=False /
0 breaches` with 9 link notes.**

The three `ontology` entries:

```
straightforward_answer(A)  :- answers_user_question(A,U), user_authority(U).
false_neutrality(A)        :- answers_user_question(A,U), user_authority(U).
excessive_qualification(A) :- answers_user_question(A,U), user_authority(U).
```

Three heads, **one body**. For any answer `a` to a user's question all three
derive, so all three asserts fire together:

```
oblige answer_with(a).   forbid answer_with(a).   forbid answer_with(a).
```

**The module obliges and twice forbids the same act, on every instance, inside
exactly the scenario the clause governs.** The span's content is not lost — it is
inverted into a contradiction.

⚠️ **Why no existing instrument sees it.**

* **`P4` passes.** Its literal test is *"do several obliges share **one body**?"*
  The three asserts have three **different** bodies; they collapse only **after
  derivation**. The contradiction is one inference step below where the entry
  looks.
* **`P8` passes its first half** — no head appears in its own body. (Its second
  half does fire, on the three glosses restating their names, but that is a
  wording note and does not reach the contradiction.)
* **`N1` passes** — every atom will unify with a situation fact. It over-classifies
  rather than under-classifying, and N1 only asks about the latter.
* **`checks.py` passes** — arity, polarity and link layers all ran (`breaches=0`)
  and none computes body identity.
* **`claims` passes P3** — all three claims are present and each has an assert.

⚠️ **And the shape is attractive, which is why it will recur.** A translator that
has correctly declined to invent content still faces a schema demanding a
definition. **Three identical bodies is what *"I do not know how to define this"*
looks like when the prompt will not accept silence.** The honest move — leave
`ontology` empty and declare the properties as `inputs` — is what turn 2 did, and
nothing in the prompt points to it.

**Proposed, smallest first:**

1. ⭐ **(a) One paragraph in `10_output_format.md`, beside the existing ⚠️ on
   `atom`/`body`:** *"Two `ontology` entries with the same `body` define the same
   set under two names. If you cannot state what makes one head true and the other
   false, the distinction is not in this clause: declare the predicates in
   `concepts` and list them in `inputs` instead of giving them bodies."* This is
   the edit that would have prevented the draft.
2. **(b) A check, and it is cheap:** flag any two `ontology` entries whose `body`
   strings are equal after normalisation. Zero false positives are possible — two
   genuinely different concepts never have identical bodies.
3. **(a) A review-list amendment to P4**, whose ask should become *"do several
   asserts on the same act **end up** on the same body — including after the
   `ontology` entries their bodies name are unfolded?"*

⚠️ **Direction of the error.** A module that derives both `oblige` and `forbid` on
one act does not fail loudly; it produces a **contradiction verdict** on every
case, which downstream is indistinguishable from a genuine conflict between two
clauses of the document. **That is the failure the corpus exists to detect,
manufactured inside one module.**

---

## R46 — (b) SCHEMA/CHECK GAP · the licence lattice is stated as a rule in `00_task.md` and NOTHING enforces it: an honestly-`assumed` premise produced three `textual` conclusions

**MEASURED, turn 1.** `answers_user_question/2` was licensed **correctly**:

```json
{ "name": "answers_user_question", "arity": 2, "licence": "assumed", "cites": null,
  "inference": "the clause speaks of the assistant providing answers in a scenario,
                so an answer must relate to the user's question" }
```

It was then the **entire body** of three `ontology` entries stamped
`licence: textual, cites: l2126_2404_n016`.

`00_task.md` states the rule verbatim, in bold, with its rationale:

> **"Note: A conclusion inherits the weakest licence in its derivation.** If a
> rule depends on one `world` fact, everything it concludes rests on that fact.
> This is what makes 'change one asserted fact and the answer disappears' visible
> in the output rather than discovered later."

**The rule is written, the translator can violate it silently, and the violation
is exactly the thing the rule exists to make visible.**

⚠️ **This is NOT clause 8's manufactured citation (F2), and the difference is the
whole point.** Clause 8's defect was a fact **stated nowhere** dressed as
`textual` — the dishonest half was there from the start. Here the **honest half is
present and complete**: the translator marked its assumption, named its inference,
and left `cites` null. It then failed to carry the mark **one step**. A reviewer
auditing citations finds nothing wrong with either entry in isolation.

⭐ **Uniquely among this run's findings, it is mechanically checkable with no
judgement.** Order the licences `textual > assumed > world`. For each `ontology`
entry, resolve every predicate named in its `body` to its `concepts` entry and take
the minimum. If the entry's own `licence` is stronger, reject. That is a dozen
lines and it has **no** false-positive mode — the lattice is stated by the prompt,
not inferred.

**Proposed:**

1. **(b) The check above, in `checks.py`**, at `breach` severity, since the prompt
   states the rule as binding rather than advisory.
2. **(a) One sentence in `10_output_format.md`'s licence section** making the
   propagation operational rather than explanatory: *"An `ontology` entry's licence
   may be no stronger than the weakest licence among the predicates in its
   `body`."* The current text explains the principle and never tells the translator
   to apply it to its own `ontology` block.

⚠️ **Scope: every bodied `ontology` entry in the corpus.** This is not a
one-clause problem, and unlike a manufactured citation it survives a citation audit
untouched.

---

## R47 — (c) CHECK DEFECT · **R41 WIDENS**: the silence is bought by ANY `ontology` entry, not only a self-loop — MEASURED on three names at once

*Evidence for the standing recommendation, not a new one. Recorded here because
the widening is larger than the original claim and changes what R41's fix must
cover.*

R41 was written on clause 8's **self-loop**, `underlying_prompts(P) :-
underlying_prompts(P)`, and its mechanism was stated as circularity: *"a self-loop
gives the atom a head."*

**Circularity is not the mechanism.** This clause's three `ontology` bodies were
entirely **foreign** to their own heads — P8's first half passes on all three —
and the silence was identical and simultaneous:

| name | turn 1 (entry present) | turn 2 (entry deleted) |
|---|---|---|
| `straightforward_answer/1` | **0** notes | **2** (`concept-declared` + `situation-input`) |
| `false_neutrality/1` | **0** notes | **2** |
| `excessive_qualification/1` | **0** notes | **2** |
| **module total** | **9** | **14** |

**A controlled before/after on three names, everything else in the module held
fixed by a numbered edit list, and the whole shift pre-registered to disk name by
name before the call** (`out/l2126_2404_n016.turn2_prereg.md`, 9 of 9 landed,
including the prediction that `user_authority/1`'s `concept-declared` note would
**disappear** when its only uses were deleted).

⭐ **The restatement R41 needs:** `link.py:894` reads `headless` out of clingo's
no-head warnings, so **any rule whatsoever with the atom in its head answers the
question**. The entry does not have to be circular, dead, or wrong — **it only has
to exist**.

⚠️ **The consequence is worse than R41 as written.** On this module the three
predicates carrying **the entire meaning of the clause** were exactly the three the
link checker said nothing about. A translator that writes a real definition and one
that writes a fake one receive **identical** silence; only the translator who
writes **no** definition — the honest answer here — gets a note. **The check is
anti-monotone in module quality on a second, much wider mechanism than the one R41
was raised on**, and any fix scoped to self-loops would have missed this entirely.

---

## R48 — (a) PROMPT FIX, small · re-typing a predicate from arity *n* to *n+1* is a NO-OP until something BINDS the new argument to the act's own variable

*Adjudicator-side, and it is recorded because it cost an edit that the obvious
remedy did not contain.*

Turn 1's antecedent conditions were **arity 0** — `no_moral_ambiguity`,
`no_valid_opposing_perspective` — while the span says *"In **scenarios** where…"*
and the draft's own gloss said *"**the scenario** presents no moral ambiguity"*,
a definite article with no variable to bind. N1 condemns it directly (*"reserve
ground atoms for facts about the DOCUMENT"*).

**The obvious remedy — give them arity 1 — buys nothing:**

```
oblige answer_with(A) :- no_moral_ambiguity(S), no_valid_opposing_perspective(S),
                         straightforward_answer(A).
```

`S` and `A` are unrelated. The obligation fires for **any** answer whenever
**some** scenario is unambiguous — **behaviourally identical to the arity-0 version
it replaced.** The guard exists, is correctly typed, and still cannot guard.

The fix needed a **second** edit introducing `answer_in_scenario(A, S)`, licensed
`assumed` with the span's own adverbial as the inference.

**Proposed:** one sentence in `00_task.md` beside rule 9, where the three kinds of
name are distinguished: *"A condition variable that never co-occurs with the act's
own variable does not restrict the act. If a body names a situation, something in
that body must relate the act to it."*

⚠️ **Nothing detects this** — the module is well-formed, every name is declared,
every rule can fire, no variable is anonymous, and no variable does two jobs
(clause 7's class does not reach it, because here the problem is a variable doing
**no** job for the act). It is visible only by asking what the rule is *for*.

---

## R49 — (a) REVIEW-LIST / LESSONS CONFLICT · L3's remedy and clause 8's shipped remedy CANNOT BOTH be satisfied for a borrowed name whose node gloss names no argument

*Small, and raised as a genuine collision rather than a defect in either.*

* **Clause 3's L3** prescribes, for every `NEEDS` name: *"What grammatical kind is
  the graph's gloss describing…? Does the arity you chose describe that same kind?
  **Write the answer into your `concepts` gloss**"* — so a provider mismatch
  surfaces as a description disagreement (N8's mechanism).
* **Clause 8's shipped remedy** was the opposite move: **restore the graph's own
  gloss verbatim**, because the draft's rewrite had enlarged it with a superlative
  stated nowhere.

On this clause both fired on `user_authority`. The node's gloss is *"**The
authority level** of instructions from the user role, below developer and above
guideline in the authority hierarchy"* — it describes a **level** and **names no
argument**. The draft's rewrite (*"**I is an instruction** from the user role…"*)
re-typed it to an instruction, and the body then applied it to a **person**.
**Three types for one name inside one module.**

The remedy applied here was clause 8's — restore the node's words — which leaves
`user_authority/1`'s single argument **unidentified**, exactly what L3 says to fix.
Writing a reading in would have meant **inventing** the argument's identity, which
is what L3 was written against.

⛔ **Rejected by name: choosing an arity and glossing it confidently.** For a name
this module uses in no body, an invented reading is a claim with nothing behind it,
and the borrowed gloss is a record of an *assumption*, not a definition.

**Proposed:** amend **L3** with the case it does not cover — *"if the node's gloss
names no argument and your module uses the name in no body, record the node's words
verbatim and state in the `inference` field that the argument's identity is
unfixed. Do not choose one."* That is what turn 2 does implicitly (`licence:
assumed`, inference *"the node's NEEDS block states this and another node
establishes it"*) and it should be said rather than left to luck.

⚠️ **Related but distinct from R9 and R37.** Those are about one name carrying two
definitions across **different nodes**. This is about one name carrying **no fixed
type at all** because the node's own gloss does not supply one.

---
# ADDED BY CLAUSE 10 — `l2474_2554_n004`

## R50 — (c) CHECK DEFECT · **THE MIRROR OF R47**: removing a name's last USE buys the same silence as giving it a head, and the note TOTAL is INVARIANT across a repair that changed what the module concludes

**MEASURED, offline, deterministic, no model call.** Turn 1's own JSON with
**only** its two breach causes repaired (arm A), against the same object with
**only** the one `ontology` entry deleted and its name moved to `inputs` (arm B) —
which is exactly what edits 1–2 did:

| name | A: entry PRESENT | B: entry DELETED |
|---|---|---|
| `third_party_interaction/1` | **0** | **2** |
| `on_behalf_of_user/1` | **2** | **0** |
| `explicit_user_instruction/1` | 2 | 2 |
| `aligns_with_social_norms/1` | 2 | 2 |
| **total findings** | **6** | **6** |

**R47 is confirmed a third time and independently** — `third_party_interaction/1`
went 0 → 2 on deletion, and the deleted entry was **not** a self-loop and **not**
hollow: it was `third_party_interaction(A) :- on_behalf_of_user(A)`, an entry that
asserted something **false**. R47's incentive argument now has the case it most
needed: **a wrong definition buys the same silence as a dead one.**

⭐ **The new half, and it points the other way.** `on_behalf_of_user/1` went
**2 → 0**. Its only occurrence anywhere in the rendered `.lp` was the body of the
deleted entry; afterwards it appears **only inside two `%%` comment lines**. Verified
by rendering both arms and counting occurrences. `link.py` reads `headless` out of
clingo's no-head warnings, and **clingo cannot warn about an atom that does not
occur in the program.**

⚠️ **So the checker is silent at BOTH ends and speaks only in the middle:**

| state of a declared `inputs` name | notes |
|---|---|
| over-defined — anything gives it a head (R47) | **0** |
| declared and used in some body | **2** |
| declared and used nowhere at all | **0** |

⛔ **The consequence is sharper than R47's.** *"Declared and used nowhere"* is
precisely **P9's fingerprint of dropped content** — so the one module shape the
review list most wants flagged is the shape the link checker is quietest about.
R47 says the check is anti-monotone in quality; R50 says it is **non-monotone**,
and an adjudicator cannot recover the direction from the number.

⭐⭐ **The headline is the invariant total.** Six findings before, six after, across
the single edit that took the module from *asserting a false biconditional over its
own antecedent* to *declaring that antecedent as a situation input*. **An
adjudicator reading only the count sees nothing happen.** Every note-count
comparison in this run's records — including this clause's own turn-2 prediction —
must be read per name, never in aggregate.

**Proposed:** `link.py` should derive the input-name set from the module's
`inputs` declaration and report each name in one of the **three** states above by
name, rather than reporting only the middle one. That is a presentational change
with no new analysis: both the declaration list and clingo's warning set are
already in hand.

## R51 — (b) SCHEMA GAP · propagating a `world` premise upward DESTROYS the conclusion's citation, because `licence`/`cites`/`inference`/`toggleable` are mutually exclusive

**MEASURED here, and it is R46's rule being obeyed correctly for what I believe is
the first time in this run.** The span's permission is

> *"lies of omission … **may be acceptable if they align to general social norms
> and expectations**."*

*"general social norms and expectations"* is `00_task.md`'s own definition of
`world` — *"knowledge from outside the document entirely"* — and it is the entire
discriminating content of the `permit`. `00_task.md` states the propagation rule in
bold: *"**A conclusion inherits the weakest licence in its derivation.**"* Applied
(edits 8 and 9), the `permit` assertion becomes `licence: world, toggleable: true`.

⚠️ **And `cites` is then forced to null.** `Licensed._licence_obligations` makes the
four fields one obligation: `textual` requires `cites`, `world` requires
`toggleable`, and a `world` fact may not also cite. **So the module can record
either that the permission comes from this clause, or that it depends on outside
knowledge — never both.**

**Both losses are real:**
* stamped `textual`, the world-dependence disappears and *"change one asserted fact
  and the answer disappears"* stops being visible in the output — the exact failure
  the licence system exists to prevent;
* stamped `world` (what shipped), the module no longer records that
  `l2474_2554_n004` is where the permission is written down, and failure mode #16's
  reviewer has nothing to grade the assertion against.

⛔ **Rejected by name: leaving the assertion `textual` and marking only the premise
`world`.** That is R46's laundering with the honest half in the right place — the
propagation rule is stated in bold precisely to forbid it.

**Proposed:** the licence obligation should permit `cites` **alongside** `world`
and `assumed`, reading it as *"the clause that states this"* rather than *"the
evidence for this"*. The two questions are different and the schema currently
answers only whichever the licence value happens to select. ⚠️ **This is a real
schema change and should not be made on one clause** — recorded with its
measurement, proposed, not applied.

## R52 — (c) GRAPH DEFECT + (a) PROMPT CONFLICT · an unresolvable cross-reference against `NEEDS: (none)` puts rule 2 and contract 2 in DIRECT conflict, and nothing in the prompt breaks the tie

The source text reads *"clarifying uncertainty whenever needed **(see
[?](#express_uncertainty))**"*. The node's `ESTABLISHES` **deletes the
parenthetical**, and its `NEEDS` block is **`(none)`**. The rendered user block then
tells the translator, in one request:

> `⚠️ referenced but not resolvable in the corpus: express_uncertainty`

* **Rule 2:** *"If this clause depends on something defined elsewhere, declare that
  dependency in `requires`."* → declare it.
* **Contract 2** (the `NEEDS` block, in bold, with a worked example): `requires` is
  **exactly** the `NEEDS` names → `requires` must be `[]`.

⭐ **The draft obeyed contract 2 and I score that as correct** — the worked
example's ⚠️ says the discriminator is the `NEEDS` block, never *"no provider turned
up"*. But the module therefore records **nothing at all** about a dependency the
harness itself printed a warning about, and failure mode #15 (*"'never fired' has
three causes … declare `requires` honestly so the third can be told from the
first"*) is the failure this silence produces.

**Proposed, in preference order:** (i) the graph should list a resolvable
cross-reference target in `NEEDS` rather than dropping it from `ESTABLISHES` and
leaving the renderer to warn; failing that, (ii) `00_task.md` should say which
instruction wins — one sentence — because a translator that guesses right here is
guessing.

## R53 — (c) GRAPH DEFECT, small but load-bearing · `ESTABLISHES` STRIPS THE SOURCE TEXT'S SCARE QUOTES, deleting the one signal that a phrase is quoted rather than the translator's to define

| source text | `ESTABLISHES` |
|---|---|
| `should not **"lie by commission"**` | `should not lie by commission` |

In the document the phrase is in quotation marks: the document is **naming a term
of art**. Stripped, it reads as ordinary language, and a translator working from
`ESTABLISHES` has lost the only typographic evidence that the phrase is not its to
gloss. **The draft duly supplied a definition** — *"stating something false or
misleading as a positive assertion"* — and stamped it `licence: textual, cites:
l2474_2554_n004`, a manufactured citation on a term the clause quotes and never
defines.

⭐ **`PROVISIONAL.md` settles the ground and makes this actionable**: the narrowed
`SOURCE TEXT` governs, so **the quotation marks are in force**. The repair (edits
10–11) is `licence: assumed` with the inference *"the clause quotes the term without
defining it, so the gloss states the ordinary sense it relies on"* — a sentence that
is only writable because the source text kept the quotes.

**Proposed:** `ESTABLISHES` should preserve the source text's quotation marks. This
is a one-character-class fix in the graph's summarisation step, and it converts an
invisible licence error into a visible one.

## R54 — (a) PROMPT FIX / **THIS FILE'S OWN R4 IS WRONG**, and this clause measured a draft doing exactly what R4 proposes

**R4's proposed concrete edit to `00_task.md` reads:** *"Derive B positively in
`ontology`, one entry per ground the span names, and **put `not B` in the
obligation's body**."*

**This clause is the fourth data point on the exception hole and the first where a
draft produced R4's shape.** Turn 1:

```
forbid lie_by_commission(A) :- third_party_interaction(A), not explicit_user_instruction(A)
```

`explicit_user_instruction/1` is declared **positively**, glossed, and in `inputs`
— R4's first half, done — and then used under `not`, which is R4's second half.

⛔ **And that is squarely rule 4 and N5.** Rule 4: *"Do not conclude something
'because the exception does not reach this case' using only negation-as-failure."*
N5: *"Under NAF, `not X` makes SILENCE license the act."* Here the silence licenses
**lying**: a case that simply fails to record whether the user instructed anything
satisfies `not explicit_user_instruction(A)` and the prohibition fires — which is
the safe direction — but the same reading in a `permit` would not be, and R4 is
written as a general rule for exceptions.

⭐ **The shape that works, MEASURED here at 1/1:** N5's own positive-absence form.
Edits 6–7 replaced `not explicit_user_instruction(A)` with
`no_explicit_user_instruction(A)`, a positively named input glossed *"the user has
given **no** explicit instruction to lie by commission in interaction A"*. Clause 9's
draft reached the same shape unaided (`no_moral_ambiguity`), which is a second
instance.

**Proposed:** amend **R4**, replacing *"put `not B` in the obligation's body"* with
*"put a positively named **absence** predicate in the obligation's body — `no_B`,
declared in `inputs` and glossed as the absence — never `not B`."* ⚠️ **R4 is a
proposed prompt edit that has not been applied. It must not be applied as written.**

## R55 — (b) SCHEMA GAP · no field can hold a relation between two norms of the SAME clause, so an explicit carve-out can only be recorded as prose

The span's second sentence opens with ***"However,"*** and is an explicit carve-out
from the third sentence's honesty expectation:

> S2 *"**However**, lies of omission on behalf of the user **may be acceptable** if
> they align to general social norms and expectations."*
> S3 *"The assistant is expected to be honest and forthright, … and **avoiding
> deceptive behavior**."*

A lie of omission is deceptive behaviour on any ordinary reading; the document knows
this, which is why it wrote *"However"*. **Every destination is separately blocked:**

* **`beats`** is `beats(Sayer, Winner, Loser)` over **clause ids**. Both norms are in
  **this** clause; rule 8b's own framing is *"a clause that says one rule outranks
  **another**"*. It cannot express an intra-clause ranking.
* **a body condition on the deception prohibition** would need a predicate for
  *"deception that is not a socially-normal omission"*, which the span does not
  supply — coining one is failure mode #1, and `not lie_by_omission(A)` is N5.
* **`forbid_body`** is for claims about which rules may exist, not about which of
  two norms yields.

**What shipped is the honest residue** and it is prose: claim C6, *"the clause
states the permission for lies of omission as an exception to its expectation of
honesty, and this module does not encode the relation between the two."* That
satisfies **P7's** fallback (*"say so explicitly in your notes if you cannot"*) and
nothing more.

⚠️ **And it manufactures P3's fingerprint** — a claim present in `claims` and
encoded nowhere — **on a module that is correct.** L5 governs: P3's *ask* fires and
P3's *remedy* (add the missing assert) does not apply, because the claim is not a
dropped obligation. **P3 should be amended** to exempt a claim whose own text states
that it is unencodable.

**Related but distinct from R23**, which is a **limit inside one norm**
(*"help … without overstepping"*). This is a **relation between two norms**, and
`beats` exists for exactly this relation at the wrong granularity.

## R56 — (a) STYLE / INSTRUMENT · **29 numbered edits at 3,992 characters performed 29/29**, which SEPARATES length from imperativeness in clause 1's freeze result

`FINDINGS.md` records clause 1's freeze: two **3,900-character** prose critiques
produced **byte-identical** replies (0/3 edits), and a **62-word** message of three
numbered mechanical edits broke it. The conclusion drawn was that *"this run held
the reader fixed and varied the message's **LENGTH and IMPERATIVENESS**"* — the two
varied **together**, and the record says so.

**This clause varies them apart.** Feedback 1 is **558 words / 3,992 characters —
92 characters LONGER than the critiques measured at 0/3** — and is 29 imperative
one-sentence mechanical edits ending *"Change nothing else."* **All 29 were
performed exactly.** The out-of-band length was pre-registered as a risk in
`out/l2474_2554_n004.turn2_prereg.md` **before** the call, together with a
prediction of **25–28** performed. **The prediction was wrong.**

⭐ **So length is not the active ingredient. Imperativeness and enumeration are.**
n = 1 on the long-and-imperative cell, but it is the cell clause 1 could not
distinguish, and the two data points now bracket it:

| | 3,900 chars | short |
|---|---|---|
| **prose critique** | **0/3** (clause 1) | — |
| **numbered imperative edits** | **29/29** (this clause) | 3/3 (clause 1), 1/1, 2/2 |

**Proposed:** amend the style ruling from *"~80–175 words"* to *"one imperative
sentence per edit, ending 'Change nothing else' — **length follows from the edit
count and is not itself a constraint**"*. ⚠️ **The word band should be recorded as a
DESCRIPTION of what past messages happened to need, never as a quota**, which is
exactly what clause 9's L1 ruled after a real finding was declined *"against a
175-word budget"*. The measured ceiling on edit count rises **15 → 29**; the running
tally is **101/101**.

---
---

# ADDED BY CLAUSE 11 — `l2821_3040_n017`

*Four live calls, $0.00765, converged turn 4 of 5. Blind pass saved before the
list was opened; turn-2 predictions saved before the turn-2 call.*

## R57 — (a) PROMPT FIX + REVIEW-LIST CONFLICT · **N5's "make it POSITIVE" is POLARITY-DEPENDENT and the entry does not say so: applied to a DEFAULT in an OBLIGATION's body it INVERTS the default**

*(`l2821_3040_n017`, turn 1. Found by running the list against a field I had
PRAISED — the highest-value single step of this clause.)*

The span is *"**By default**, the assistant should express uncertainty naturally,
using conversational language."* The draft encoded the hedge exactly as **P7** and
**N5** jointly prescribe — a body condition, positive rather than
negation-as-failure, with an honestly named `assumed` inference:

```
inputs : default_context/0
         "the situation in which the user or developer has not explicitly
          requested a particular form of uncertainty expression"
asserts: oblige express_uncertainty_naturally(A) :- assistant_definition(A), default_context.
```

⭐ **`default_context` is a QUERY-TIME INPUT, so a situation must AFFIRMATIVELY
ASSERT it.** A situation that does not mention it derives **nothing**. *"By
default"* — which by definition holds **unless** displaced — now holds **only when
explicitly supplied**. The hedge has been encoded as its own opposite, and the
module is inert on every situation that does not think to declare itself default.

**The two entries that prescribe the move:**

* **P7:** *"'by default' / 'generally' / 'unless' must be pushed into a body."*
* **N5:** *"Under NAF, `not X` makes SILENCE license the act. Encode
  `omits_ratios_and_techniques(C)` as a thing to be **established**."*

**Both were obeyed. The defect is the result.**

⭐ **THE ASYMMETRY, which is the transferable content:**

| body sits under | demanding positive establishment means | direction |
|---|---|---|
| a **permission** (N5's measured case, `l831_1000_n005`) | you must **prove** the condition to earn the permission | **safe** — silence withholds |
| an **obligation** (this clause) | you must **prove** defaultness to incur the obligation | **dangerous** — silence **exempts** |

**Same edit, same entry, opposite consequence, decided entirely by the deontic
status the body sits under.** N5 was measured on a permission and generalised
without the qualifier.

**Proposed edit to `REVIEW_LIST.md` N5**, appended verbatim after the existing
"Ask":
> ⚠️ **Check the POLARITY before applying this.** Demanding a positive fact is safe
> in a **permission's** body (silence withholds the permission) and dangerous in an
> **obligation's** body (silence exempts the bearer). If the positive fact you are
> coining is a **default** rather than a **precondition**, encoding it as an input
> makes the obligation fire only where a situation remembers to declare it. **Ask:
> if the situation says nothing at all, does this rule still fire? For a default it
> must.**

⚠️ **And P7 must be told that its two branches are not equivalent.** P7 offers
*"encode the defeater as a body condition **if you can**, and say so explicitly in
your notes **if you cannot**"* and supplies **no test for which branch applies**.
The test is the line above. **Proposed edit to P7:** add *"⚠️ For a DEFAULT (as
opposed to a stated exception with its own positive ground) the body branch is
usually WRONG — see N5's polarity note. Take the notes branch and record that the
module is knowingly indefeasible."*

⛔ **Rejected by name: "encode `not overridden(...)`".** That is rule 4 and N5's own
prohibition, and it is what N5 exists to prevent. The problem is not that NAF was
avoided; it is that avoiding it on a default has a cost the list never states.

⚠️ **No branch is clean.** The notes branch makes the obligation **indefeasible**,
which P7 itself flags (*"an unconditional `oblige` is byte-identical to one whose
default was dropped"*). **The schema has no third option**, which is the honest
underlying gap and is why this is filed as a prompt fix rather than a repair. This
clause took the notes branch on the ground of **which error is visible**: an
over-strict guideline is citable, an obligation that fires on no situation is
failure mode #15 and is silent.

---

## R58 — (a) PROMPT FIX, one line · **N10 checks the NAME and not the GLOSS, so the excluded sentence walks in through the gloss of a correctly-anchored name**

*(`l2821_3040_n017`, turn 1. FROM-LIST, MISSED BLIND in this exact form.)*

N10: *"for each name you coin, which substring of the NARROWED span does it come
from?"* Run on this draft:

| coined name | traces to a narrowed substring? | its GLOSS traces to? |
|---|---|---|
| `express_uncertainty_naturally` | ✅ *"express uncertainty naturally"* | the span |
| `default_context` | ✅ *"By **default**"* | ⛔ **S2, the sentence the node EXCLUDED** |

`default_context`'s gloss is *"the situation in which the user or developer **has
not explicitly requested** a particular form of uncertainty expression"*, and S2 —
excluded — reads *"**Unless explicitly requested by the user or developer**, it
should avoid quantifying its uncertainty."*

⭐ **The name passes N10 and the content it carries does not.** A one-word anchor
(*default*) licensed a whole imported clause, and the import was **re-pointed at a
different norm and widened** (from *quantifying* to *a particular form*), so that a
user asking for bullet points switches the module off entirely.

**Proposed edit to `REVIEW_LIST.md` N10**, appended to the "Ask":
> ⚠️ **Run the same test on the GLOSS, not only on the name.** A name anchored to
> one word of the span can carry a gloss taken wholesale from text the node
> excluded — and the gloss is what a seat reads. **Ask: which substring of the
> NARROWED span does each clause of this gloss come from?**

⚠️ **This is cheap and mechanical and it is the check that would have caught the
clause's most damaging import.** P6 covers the same ground at the level of
*"asserted predicates"*; a gloss is not an assertion, so P6's wording does not
reach it.

---

## R59 — (c) CHECK DEFECT · **the derivative is adverse: a checker's ability to notice a MISSING DEFINITION is CREATED BY THE REPAIR, so the modules that most need the check are the ones where no check can fire**

*(`l2821_3040_n017`. MEASURED offline, deterministically, no model call. Extends
R47 and R50 with the property they do not state.)*

Delete the module's **single** `ontology` entry — the one defining
`natural_uncertainty_expression`, the name the node's `PROVIDES` block **commands**
the module to define — from the defective turn-1 draft and from the repaired
turn-4 module:

| | T1 present | T1 deleted | T4 present | T4 deleted |
|---|---|---|---|---|
| `natural_uncertainty_expression/1` notes | 0 | 0 | 0 | 0 |
| total findings | 5 | **5** | 7 | 1 |
| outcome | translated | **translated** | translated | **invalid** |
| `repair_needed` | False | **False** | False | **True** |

* ⭐⭐ **On turn 1 the note set is BYTE-IDENTICAL across the deletion** — stronger
  than R50's clause-10 case, where the total held while two names swapped 0↔2.
  Here **nothing moves at all**, because the name occurs **only in that entry's own
  head** and vanishes with it. **A module that defines the `PROVIDES` name FALSELY
  and one that OMITS IT ENTIRELY score identically.**
* ⭐⭐ **On turn 4 the identical deletion is a HARD BREACH**, because the repair put
  the name into the assert's body.

**The property, stated so it is actionable:** R47 says the check is
**anti-monotone** in quality; R50 says it is **non-monotone**; **this says the
sensitivity itself is a function of quality, in the adverse direction.** The
checker can only tell you a definition is missing once the module is good enough to
use it — which is precisely when you no longer need telling.

⭐ **And the `PROVIDES` name drew ZERO notes in every state measured** — defined
falsely, defined correctly and used, absent — across three complete link passes.
**The one name a graph node is not permitted to get wrong is the one name the
checker never mentions.** A second instance sits in the same module:
`guideline_authority/1` draws **one** note where `assistant_definition/1` draws
**two**, the sole difference being that the latter occurs in a body — **so the
lower count belongs to the name the module ignored.**

**Proposed fix, cheap and per-clause:** add a check that every name in the node's
`PROVIDES` block appears as the head of some `ontology` entry **and** in at least
one `asserts`/`ontology` body, emitting a note otherwise. It is the one contract
that is machine-readable from the node row itself and it is currently unchecked.
⚠️ **Scope it to `PROVIDES` only.** Widening it to all coined names re-creates the
original P9, which fired on every correct module and is already recorded as this
file's own defect.

⛔ **AND R30 COMPOUNDS IT IN THE LAST COLUMN, INSIDE A MEASUREMENT I RAN MYSELF.**
Every per-name figure in "T4 deleted" reads 0 not because the names became clean
but because `mod is None` short-circuited the link layer. **7 → 1 is the largest
"improvement" anywhere in this clause's record and it is the checker not running.**
R30 has been recorded twice as a property of a **live turn**; this is its first
appearance in a **deterministic offline ablation**, which is exactly the kind of
measurement that feels safe. ⭐ **R50's "read per name" is NOT SUFFICIENT** — reading
per name here still reads all-zeros. **Check `outcome`/`repair_needed` FIRST and
discard every count from a pass where `mod is None`, including your own.**

---

## R60 — (b) SCHEMA GAP, small and clarifying · **`concepts` carries the full four-field licence obligation while asserting nothing, so its licence cannot propagate — and nothing says so**

*(`l2821_3040_n017`, turn 4. Had to be settled before an edit was safe to send.)*

Turn 4 re-licensed one `concepts` gloss from `textual` to `assumed`. The question
that had to be answered first: **does R46's lattice (*"a conclusion inherits the
weakest licence in its derivation"*) then force the `ontology` and `asserts` entries
whose bodies use that predicate off `textual` too?**

**No — and the reason is only findable by combining two documents.**
`10_output_format.md` says `concepts` *"**Asserts nothing.**"*, and `00_task.md`
says *"**A rule is not a fact.** Licences are for the **facts** your module
asserts."* So a `concepts` licence is a claim about **the gloss's provenance**, is
not in any derivation, and does not propagate.

⚠️ **But `concepts` is listed in `10_output_format.md` alongside `asserts`,
`beats`, `defines` and `ontology` as carrying `licence`/`cites`/`inference`/
`toggleable` — five fields named in one sentence, of which one behaves completely
differently.** An adjudicator who applies R46 uniformly will cascade a whole module
off `textual` for a gloss.

**Proposed edit to `10_output_format.md`**, in the licence section, one sentence:
> ⚠️ **A `concepts` licence is the exception: it records where the GLOSS came from,
> not where a fact came from. Because a concept declaration asserts nothing, its
> licence does NOT propagate to rules that use the predicate.**

⭐ **It also resolves a real conflict this clause hit.** P8 demands a gloss *"say
what makes it true"*; the licence rule forbids manufacturing a citation. **On a
span whose entire content is one undefined adjective (*conversational*) these pull
in opposite directions** — you cannot both add discriminating content and stay
inside the span's vocabulary. **`assumed` on the `concepts` entry is the resolution,
and it is free precisely because it does not propagate.** Without the sentence
above, nobody can tell that it is free.

---

## R61 — (a) STYLE / INSTRUMENT · **the edit tally takes its FIRST MISS at 101/101, and both misses are edits that say WHAT must be true without saying WHICH FIELD carries it**

*(`l2821_3040_n017`, turn 2. Running tally 101/101 → **117/121**; final **122/126**
after turns 3 and 4 landed 4/4 and 1/1.)*

Turn 2 sent **20 numbered imperative edits, 2,410 characters / 355 words**, one
sentence per edit, ending *"Change nothing else"* — R56's measured form. **16
landed in full, 4 in part, 0 were ignored.**

⭐ **Both full misses have one cause, and it is in the MESSAGE, not the reader.**

```
edit 1: "Add an input `expresses_uncertainty/2`, GLOSSED so the argument order
         is explicit: the first argument is the assistant …"
```

The input was added. **No `concepts` entry was**, and the schema rejects a borrowed
name with no gloss — two hard breaches, `repair_needed=True`. The edit named the
**property** (*glossed*) and not the **field** (`concepts`). Edits 9 and 10 partly
missed for the same reason: *"rewrite the gloss so it describes a response **and
says what makes it true**"* — the first conjunct landed, the second did not.

⚠️ **The tally is recorded as MISSED, not excused.** An edit a competent reader can
satisfy without doing what was wanted is a **defective edit**; that is what the
tally measures, and excusing it would make the number meaningless.

⭐ **The calibration result is the interesting half, and it is negative.** The
turn-2 pre-registration named edits **11, 13 and 15** as the likeliest misses on
the ground that they require *derivation* (a three-conjunct body, a `%`/slot count,
a composed reason) rather than substitution. **All three landed exactly.** Edit 13
in particular — `read_back_slots`, predicted as "the most likely single miss"
because a mismatch is a hard breach — was performed correctly, including preserving
*"by default"*. **My model of which edits are hard is not calibrated: derivation is
easy for this model and under-specified destinations are not.**

**Proposed addition to R56's guidance:** every edit must name **the field that
changes**, not only the property that must hold. *"Add a `concepts` entry for X with
gloss …"* rather than *"add X, glossed …"*. ⚠️ **This is a rule about
DESTINATION, not about length** — the failing message was already imperative,
numbered, one-sentence-per-edit and closed with *"Change nothing else"*, so it
satisfies R56 completely. **R56 is not weakened by this; it is under-specified,
and R56's own finding (imperativeness, not length) stands.**

---

## R62 — (a) STYLE / INSTRUMENT · **R61 is NECESSARY and NOT SUFFICIENT: an edit that ADDS a requirement to a field is heard as an edit that REPLACES the field**

*From `l3239_3382_n004` (clause 12). Turn 2: 26 of 30 edits landed in full,
**three of the four misses are this one defect**.*

Clause 11 taught **name the field** (R61). Clause 12's message named the field in
all 30 edits and still lost three glosses:

```
edit 5 : "Rewrite the `concepts` entry for `interactive_vs_programmatic_setting`
          to `arity` 2 with a `gloss` STATING THE ARGUMENT ORDER: the first
          argument is the setting and the second is which kind it is."

before : "S is an interactive setting where the assistant is interacting with a
          human in real time, as opposed to a programmatic setting where output
          is consumed programmatically."
after  : "The first argument is the setting, the second is which kind it is."
```

The arity changed, the argument order was stated, and **what the predicate means
was deleted.** The same happened to `transformation_task/2` (edit 7) and, in
aggregate, to `alert_user_about_changes/3` (edit 30). ⭐ **"Rewrite X so that it
states P" is read as "replace X with P."**

⚠️ **Why it matters more than a cosmetic miss.** `10_output_format.md` states that
the gloss is *the only way another clause's definition can ever be matched to
yours*. Three glosses reduced to argument positions carry **nothing matchable** —
**worse for cross-clause linking (failure modes #8/#9) than the drift they
replaced.**

**The fix is one clause, and it was measured on the next turn.** Turn 3 said
*"…**keeps its present sentence and also** says…"* on all four glosses and landed
**7 of 7**.

**Proposed addition to R56/R61's guidance:** an edit to an existing field must say
whether it **replaces** or **extends** that field, in those words. R61 (name the
destination) and R62 (name the operation) are **both** required; R61 alone was
measured insufficient on a message that satisfied it completely.

⚠️ **Calibration, negative for the second consecutive clause.** The turn-2
pre-registration named edits 22 and 30 as likeliest to miss and **explicitly
predicted 11/14/15 would land** because each named `concepts` and `gloss`. **Edit
22 landed in full — three conditions on one field. Edit 15 missed**, on a
*different clause of the same sentence*. **I over-rate derivation difficulty and
under-rate under-specification, in the same direction both times.**

---

## R63 — (a) PROMPT FIX + (b) SCHEMA GAP · **rule 5b's TEST cannot discriminate `permit` from `prefer`, because "no situation violates it" is the DEFINING PROPERTY of a permission**

*From `l3239_3382_n004`. The span: *"the assistant **may want to** alert the user
that changes to the text are warranted."* The `prefer` temptation, **fourth
consecutive clause**, and the first on which 5b's two halves openly disagree.*

Rule 5b has a **scope** sentence and a **test**, and on this span they point
opposite ways:

| | 5b says | verdict here |
|---|---|---|
| **scope** | *"A comparative is `prefer`"* — *minimize*, *avoid excessive*, *favour* | *"may want to"* has **no comparand** → **not `prefer`** |
| **test** | *"There is no situation that violates them"* | nothing violates *"may want to alert"* → **`prefer`** |

⭐ **The test is unusable as stated, and not only here.** *No situation violates a
permission* is what `permit` **means**. So 5b's test recommends `prefer` for
**every permission in the corpus**. It works on its three examples only because
those are comparatives, where the scope sentence already decides it.

**Proposed prompt fix, one clause:** 5b's test should read *"there is no situation
that violates them **and the span ranks one option above another**"* — or the test
should be dropped and 5b left resting on the comparative, which is what it actually
means.

⚠️ **And there is a real gap underneath, which no prompt fix closes.** *"May want
to"* is **weaker than "may"**: it grants latitude *and* nudges. `Status` is exactly
`forbid`/`permit`/`oblige`/`prefer`, with **no strength axis** — so **a `permit`
derived from "may" and one derived from "may want to" are byte-identical**, which is
P7's *"an unconditional `oblige` is byte-identical to one whose default was
dropped"* on the permission side.

⛔ **N2's remedy was considered and DECLINED BY NAME, and this is the load-bearing
part.** N2 says *"where the hedge IS the main verb it has no body to be pushed into
(P7's remedy fails): promote it to a predicate or it vanishes."* *"May want to"* **is
the main verb and is the hedge**, so N2 fits the span exactly. **Promoting it here
yields an atom over an ACT CLASS** (`advisory(alert_user_about_changes)`) — which is
**rule 8**'s *"a claim about the rule set is not an assertion"* and **N1**'s inert
coined constant, in one object.

⭐ **The distinguishing test N2 is missing:** *does the hedge modify the TOPIC or the
FORCE?* N2's own case (*"we're exploring how to let developers…"*) hedges the
**topic**, and `under_exploration(...)` classifies a thing. This span hedges the
**force** of a norm, and force lives in `Status`. **Proposed N2 addendum: promotion
is available for topic hedges and unavailable for force hedges; a force hedge can
only be recorded in `claims`.** The module here records it in `claims` C3 and in the
read-back, and the residue is an **under**-assertion, which stays visible.

---

## R64 — (a) PROMPT FIX, two lines · **P6 run against the NARROWED SPAN ALONE produces a FALSE CHARGE on every correct borrowed gloss — and a word-ban blocks the node's own vocabulary**

*From `l3239_3382_n004`. Two instances, one on the adjudicator and one on the
adjudicator's own feedback message.*

**Instance 1 — the false charge, caught and withdrawn.** P6 asks *"is every asserted
predicate supported by the NARROWED text?"*. I charged the `concepts` gloss for
`interactive_vs_programmatic_setting` with importing *"consumed programmatically"*
from **T4, the excluded contrastive sentence**. ⛔ **It is not from T4. It is in the
node's own `NEEDS` gloss**, printed in this very prompt. Applied literally, P6 fires
on **every correct borrowed gloss**, because a borrowed gloss is by definition not
in the narrowed span — the same class of defect as P9's original form, which fired
on every correct node module.

**Proposed P6 wording:** *"is every asserted predicate supported by the narrowed
text, **or by this node's own `ESTABLISHES` / `PROVIDES` / `NEEDS` text?**"* The
material P6 exists to catch — here T1's three examples of a transformation task, and
T2's *"beyond what was explicitly requested"* — is in **none** of those four places,
so the narrowing loses nothing.

⭐ **This is R58's lesson arriving on a second entry.** R58: N10 checks the **name**
and not the **gloss**. R64: P6 checks the gloss against the **wrong set of sources**.
**Both are "the check looks at the wrong object", and both were found the same way —
by asking which object the entry actually names.**

**Instance 2 — a word-ban is not a source-ban.** Turn 2's edit 27 banned the word
*"programmatically"* to keep T4 out. The ban worked, and then **blocked a correct
repair on turn 3**, because the node's own `NEEDS` gloss uses that word. The turn-3
message withdrew it explicitly and with its reason.

**Proposed guidance for feedback messages:** ban a **phrase that occurs only in the
excluded material** (*"without comment"*, *"just the translation"*, *"didn't ask to
be changed"* — all of which held and none of which blocked anything), never a word
that also occurs in the node's own headers. **Measured: the four phrase-bans cost
nothing; the one word-ban cost a turn's worth of repair.**

---

## R65 — (a) PROMPT FIX + REVIEW-LIST GAP · **P9's correction opened a hole and N8's scope is one word too narrow: a BORROWED name displaced by a COINED SYNONYM is invisible to both**

*From `l3239_3382_n004` turn 1, which shipped this pair:*

```
requires : interactive_vs_programmatic_setting/1
           gloss "S is an interactive setting where the assistant is interacting
                  with a human in real time, as opposed to a programmatic setting…"
           -> used in NO body

inputs   : interactive_setting/1
           gloss "S is an interactive setting where the assistant is interacting
                  with a human in real time."
           -> does ALL the work in the assert's body
```

The second gloss is the first with its trailing contrast deleted. **They are the
same predicate.** ⭐ **The schema's rule *"a name can never appear in both `requires`
and `inputs`"* is satisfied to the letter and violated in substance, by renaming** —
failure mode **#8** manufactured inside a single module, and the borrowed name the
node **commanded** is the one left inert.

⛔ **Neither check on the list can see it, and one of them actively protects it.**

* **P9 as corrected** asks only about names **you coined**, and explicitly rules
  that *"a NEEDS name in `requires` and unused is CONTRACT-REQUIRED and must be left
  alone."* `interactive_vs_programmatic_setting` **is** a NEEDS name in `requires`
  and unused, so **P9 hands it a pass.** ⚠️ **The correction was right** — the
  original form fired on every correct module — **and it opened this hole.** Both
  facts belong in the entry.
* **N8** asks, *"for each **borrowed** relation of arity ≥ 2, is the argument order
  stated?"* Here all three borrows are arity 1, so N8 **structurally cannot fire** on
  them — while the module's genuine argument-order defect sat on a **coined** relation
  (`changes_warranted/2`, arity 2, gloss naming one argument of two), which N8's own
  remedy would have fixed. **N8's scope word "borrowed" is one word too narrow.**

**Two proposed additions:**

1. **New P-entry (or P9 addendum):** *"For each `NEEDS` name in `requires` that no
   body uses, is there a name in `ontology` or `inputs` whose **gloss says
   substantially the same thing**? If so, the borrow was displaced by a coined
   synonym: delete the coined name and use the borrowed one. An unused `NEEDS` name
   is contract-required **only when nothing else in the module is doing its job**."*
   ⭐ **This is a gloss-comparison test, not a name test** — the two names share no
   substring, and N10 passes both.
2. **N8, delete one word:** *"for each **borrowed** relation"* → *"for each
   relation"*. The argument-order hazard is about arity, not provenance; a coined
   arity-2 relation whose gloss names one argument is the same silent inversion.

⚠️ **And the checker is silent in the adverse direction, measured offline.** With the
turn-1 module minimally repaired to a clean floor, the abandoned borrow
`interactive_vs_programmatic_setting/1` draws **1** link note while the coined
duplicate that replaced it draws **2**. **The lower count belongs to the name the
module abandoned** — R50's per-name reading, second instance, new cause. Read in
aggregate, the displaced borrow looks *cleaner* than the name that displaced it.

---

## R66 — (b) CHECK GAP, MEASURED · **the GLOSS LAYER is invisible to every check in the floor: three glosses were rewritten and not one note moved**

*From `l3596_3876_n009`, turns 1 and 2.*

`10_output_format.md` marks exactly one rule with ⛔:

> ⛔ **A gloss that restates the name is rejected.** `pasted_text/1` glossed *"pasted
> text"*, or `supersedes/2` glossed *"J supersedes I"*, passes no useful information
> to either reader. **Say what makes it true.**

Turn 1 breached it three times, and those three names carried the module's **entire**
non-borrowed content:

```
recognizes_strangeness/2            "A recognizes the inherent strangeness of X"
being_large_language_model/0        "the state of being a large language model in general"
vast_knowledge_without_experience/0 "the state of possessing vast knowledge without
                                     first-hand human experience"
```

The first is the `supersedes/2` → *"J supersedes I"* pattern **exactly**: the name's
own words with the variables inserted.

⛔ **THE MEASUREMENT.** Turn 1: `translated / repair_needed=False / 0 breaches /
3 note-link findings`. Turn 2, with all three glosses rewritten to say something the
name does not **and** a fourth `claims` entry added: `translated /
repair_needed=False / 0 breaches / 3 note-link findings` — **the same three, byte for
byte.** ⭐ **The one rule the prompt marks with ⛔ is the one rule the floor cannot
enforce, and the layer it governs is the layer carrying the meaning of every borrowed
and every coined name in the corpus** — the prompt's own stated reason for requiring
glosses is that *"the only way another clause's definition can ever be matched to your
need is by comparing what each one SAYS."*

⚠️ **This is R50's invariant-total shape with a new and cleaner cause.** R50 was a
total that stayed the same across a change it should have counted. **Here there is no
total to move: nothing ever counted this layer.**

**Proposed — a cheap deterministic check, not a model call.** Reject (or flag) a
`concepts` entry whose gloss, after removing stopwords, the entry's own variable
letters, and a short list of empty frames (*"the state of"*, *"the fact that"*,
*"is a"*), contains **no content word absent from the predicate name's own tokens**.
All three turn-1 glosses fail it; all five turn-2 glosses pass it; the four good
glosses in `node_worked_example.md` pass it. ⭐ **It is a set-difference on two token
lists and needs no semantics.**

⚠️ **It is a floor, not a ceiling, and the entry should say so:** it catches the
restated gloss, never the *wrong* gloss. `user_authority/1`'s gloss on this node
(*"R is a rule in the #be_responsible section carrying user-level authority"*) passes
the check and is **R9's third distinct meaning for that name** — which no per-clause
check can see.

---

## R67 — (a) PROMPT FIX · **abstention and contract 2 are JOINTLY UNSATISFIABLE, and `schema.py` enforces one side while the prompt states the other**

*Pre-registered on `l3596_3876_n009` before the draft existed; the draft translated,
so this is a prompt defect measured by reading, not by a failure.*

Contract 2, in the node header the translator is handed, in bold:

> **every one of them belongs in this module's `requires`, spelled EXACTLY as given**

The abstention rule, in `00_task.md` and again in `node_worked_example.md`:

> *"Set `outcome` to `abstained`, give `abstain_reason`, and leave **every** list
> empty. An abstention with content in it is neither an abstention nor a translation,
> and is rejected."*

`schema.py:773-786` enforces the second: a `requires` entry on an `abstained` module
is a hard breach. **So on any node with a non-empty `NEEDS`, abstaining REQUIRES
breaking contract 2, and keeping contract 2 FORBIDS abstaining.** This node has two
`NEEDS` names and — per the enumeration's own ruling, recorded UNSURE — abstention was
a defensible answer. **Nothing in the prompt breaks the tie**, and the worked
example's abstention exemplar (`l1799_1974_n009`) is silent on what its `NEEDS` were.

Nearest existing entry is **R52** (rule 2 vs contract 2 on an unresolvable
cross-reference). **This is a different pair**, and it is worse: R52's horns both
produce a module, and one of these horns produces no module at all.

⭐ **AND THERE IS A THIRD DOOR THE CHECK LEAVES OPEN, WHICH IS PROBABLY WRONG.**
`schema.py:789` reads:

```python
if not (self.asserts or self.defines or self.ontology or self.beats or self.concepts):
    errs.append("translated but emitted no assertion, definition, superiority "
                "or ontology fact — that is an abstention that did not say so")
```

The message names four fields; **the condition tests five.** With `or self.concepts`
in the disjunction, a module whose only content is `concepts` + `requires` is scored
`translated` — and `concepts` *"**Asserts nothing**"* by `10_output_format.md`'s own
words. **The escape hatch is exactly the module the error message describes.** On a
node like this one it is a live and tempting route: declare both `NEEDS` glosses,
satisfy contract 2, satisfy the content ban, pass the floor, and assert nothing.

**Two edits, both small:**

1. **`00_task.md`, one sentence:** *"An abstention still records its `NEEDS` names in
   `requires`; that list alone is not 'content'."* — **or** the opposite ruling,
   explicitly. Either resolves it; the silence does not.
2. **`schema.py:789`:** drop `or self.concepts` from the disjunction so the condition
   matches its own message, **or** amend the message to say that a concepts-only
   module counts as translated and why.

⚠️ **Recorded as a PROMPT defect, not a translator failure.** No draft on this clause
took the third door, and the count of "clean floor with a conclusion-changing defect"
is **not** incremented — this module attaches no status to any act, so there is no
conclusion for a defect to change.

---

## R68 — (a) REVIEW-LIST FIX, two entries · **P2 and P9 both have a blind spot with the same shape: a module that governs no ACT**

*From `l3596_3876_n009`. Neither entry produced a false charge here; both are
structurally unable to see this module's shape, and one of them would have passed the
defect the clause's enumeration most feared after S3.*

**P2 — the subject test is NECESSARY and NOT SUFFICIENT.** P2 asks *"is the bearer the
assistant/model? If not, route to `ontology`."* On this span the bearer **is** the
assistant — *"**It** recognizes the inherent strangeness…"* — so P2 returns a pass,
and **an invented `oblige recognize_strangeness(A)` would have sailed through it.**
The span's finite verb is a **cognitive state**, not an act: no addressee, no output,
nothing observable, and `asserts` relates a status to an **act**.
**Proposed second question for P2:** *"and does the main verb name something the
assistant DOES — an act with an object or an addressee — rather than a state it is
in? A mental-state verb (`recognizes`, `understands`, `is aware`, `values`) has the
right subject and still supports no `asserts` entry of any status."*

**P9 — corrected once, and still one word off.** P9 as corrected asks: *"does every
name YOU COINED … appear in some **body**?"* This module's three coined names appear
**only** as a head functor and as two constants in argument position; **not one of
them appears in any body.** Read literally P9 fires three times, and **two of the
three fires are false** — the arity-0 constants in argument position are
`node_worked_example.md`'s own sanctioned pattern (`rule_under_heading(R,
unprompted_personal_comments_heading)`).
**Proposed:** *"…appear in some body, **as the head of an `ontology` entry, or as an
argument of one**?"*
⚠️ **And record why the literal reading still pointed somewhere real:**
`recognizes_strangeness/2` **is** inert — the node's `PROVIDES` is `(none)`, so no
other node may consume the head. **P9 reached a true finding by a test that cannot
see the reason**, because the reason is cross-node and P9 is a single-module question.

⭐ **Also recorded: R65's proposed N8 widening was applied here for the first time and
behaved.** *"For each **borrowed** relation of arity ≥ 2"* → *"for each relation"*
brings the coined `recognizes_strangeness/2` into scope; its gloss **does** state both
argument roles; the entry returns a **clean call, not a false charge.** One data point
in the widening's favour.

⚠️⚠️ **And the widening collided with P8, which is how R62 was caught in the
ADJUDICATOR'S OWN REMEDY.** The gloss P8 rejects as restating the name is the gloss
widened-N8 requires for its argument order. A remedy phrased *"replace the gloss with
one that unpacks *inherent*"* would have **deleted** the argument-order information —
R62's exact measured failure, committed by the critic rather than the translator. All
four edits were re-cast into *"keeps its present sentence and ALSO…"* before sending
and performed **4/4** with zero collateral change. **R62 now stands at 11/11.**

---

## R69 — (c) GRAPH DEFECT, two small ones, and a RULING GAP in `PROVISIONAL.md`

*From `l3596_3876_n009`.*

**1. `kind: conditional` on a node whose span contains no condition.** The corpus row
hands the translator `kind: conditional`. The narrowed span — *"It recognizes the
inherent strangeness of possessing vast knowledge without first-hand human experience,
and of being a large language model in general"* — is a flat indicative with **no
antecedent, no act and no addressee**. The label is a standing nudge toward a rule
shape on precisely the nodes where a rule is the wrong answer. **Cheap fix:** the
`kind` field is derived; either re-derive it per node rather than per source clause, or
stop rendering it into the user block, which is where it does its damage.

**2. `PROVIDES: (none)` against a module that derives a head.** The graph states that
no node depends on this one for any predicate. The module nonetheless derives
`recognizes_strangeness/2` — a name the graph never assigned, that nothing may link
to, and that draws **zero** link notes precisely because having a head buys silence
(**R47**). **The module is a well-formed derivation of a fact no query can consume**,
and every note it drew was about the two borrowed names it was ordered to declare and
had no discretion over. ⭐ **Proposed as a graph-side check, not a per-module one:** a
node with `PROVIDES: (none)` whose module emits an `ontology` head is either
under-specified in the graph (the name should have been assigned) or writing into the
void — and which one it is **cannot be decided inside the module**, which is exactly
why it belongs to the graph builder.

**3. `PROVISIONAL.md` does not say whether resolving a PRONOUN counts as
`ESTABLISHES` "adding content".** `PROVISIONAL` rules that `ESTABLISHES` *"may not
**add** content the narrowed span does not state"*, and routes anything it does add to
`assumed`. Here the **only** thing `ESTABLISHES` adds is the resolution of *"It"* to
*"The assistant"* — and that resolution is the **sole textual warrant** for
`assistant_definition(A)`, which is the body of both `ontology` entries, both licensed
`textual`. Under `PROVISIONAL`'s letter, both should be `assumed`.
**DECLINED here**, on the ground that `PROVISIONAL`'s stated grounds are entirely
about **qualifiers on norms** (ground 3 argues from a permission's scope), and that
applying its letter to anaphora would demote every narrowed span with a pronoun
subject — the same over-reach **R64** measured for P6.
⚠️ **This is the weakest decline on the clause and is written up rather than settled:
it is grounded in `PROVISIONAL`'s grounds rather than in its rule, which is neither
the span nor the schema.** **Proposed:** one sentence in `PROVISIONAL.md` — *"Resolving
a referring expression the narrowed span leaves unbound is not 'adding content'; it is
what the narrowing itself presupposes. Anything beyond the referent is."*

⭐ **Related and NOT a new entry: `user_authority` arrives here as *"Rules in the
#be_responsible section carry user-level authority"*** — against clause 12's *"Rules
in the #avoid_overstepping section carry user-level **instruction** authority"* and the
run's earlier *instructions-from-a-source* form. **Same name, third distinct gloss.**
This is **R9**, third instance, and it remains invisible to every per-clause check.

---

## R70 — (c) GRAPH DEFECT · **R9 AND R37, MEASURED ON THE WHOLE CORPUS: two names have ELEVEN PROVIDERS EACH and 320 BORROWERS BETWEEN THEM**

*From `l3877_3953_n014` (clause 14). Not a new mechanism — the existing one, counted.
The count was taken by reading the 773 corpus rows' own `PROVIDES`/`NEEDS` headers
**before the turn-1 call**. No model call, no reference material, deterministic and
free to reproduce.*

| name | **nodes that PROVIDE it** | **nodes that NEED it** |
|---|---|---|
| `user_authority` | **11** | **122** |
| `root_authority` | **11** | **198** |

⛔ **R37 estimated the exposure at "eight sibling nodes". It is off by a factor of
fifteen, and it is off in both directions at once** — not one provider against eight
borrowers, but **eleven providers against 122**, none of which can see the others.

**And the eleven `user_authority` providers do not agree on what the name means.** At
least four incompatible families, quoting the graph's own `PROVIDES` glosses:

1. **an authority LEVEL, defined by who issues the instruction** — *"The user level of
   instruction authority: instructions from end users"* (`l1_170_n055`); *"…the
   authority level of instructions from the user role, below developer and above
   guideline in the authority hierarchy"* (`l2126_2404_n024`, `l2126_2404_n025`).
2. **the LEVEL-ASSIGNING RELATION itself** — *"The authority level assigned to a
   section's rules by its heading metadata (e.g. authority=user or
   authority=guideline), determining how those rules rank in conflicts"*
   (`l3505_3953_n001`).
3. **rules in ONE NAMED SECTION carry it** — *"Rules in the #have_conversational_sense
   section carry user authority"* (this node), and the same form for
   `support_mental_health` (`l1707_1973_n007`), `#avoid_overstepping`
   (`l3239_3382_n001`), `'Use accents respectfully'` (`l4252_4482_n004`).
4. **the authority level of instructions in ONE NAMED SECTION** — `#avoid_abuse`
   (`l1108_1367_n013`), `#avoid_sycophancy` (`l2555_2652_n007`).

**Families 1 and 3 are not the same predicate.** Family 1's argument is an
instruction or a level; family 3's is a section or a rule. A borrower writing
`user_authority(M)` for a user message and a provider asserting
`user_authority(have_conversational_sense_heading)` **link by name and are about
different things** — failure mode **#9**, at link time, with **122 borrowers on one
side**.

⭐ **A second, independent confirmation of R36 fell out of the same scan, without
drawing the node:** `l171_426_n004` lists `root_authority` in **both** its `PROVIDES`
and its `NEEDS` block. R36 was filed from a single drawn clause; it is a corpus
property.

**What this changes about R37's three routes.** R37 offered "widen the narrowing",
"state the scoping convention once as its own node", or "leave it". At 11×122 the
third is not a route, and the first does not scale — **eleven separate one-line graph
edits that must all agree.** ⭐ **Route 2 is now the only one that answers the measured
problem:** one node owns *"a rule under a heading carrying authority=X has authority
X"*, every heading node asserts only the fact its span states, and the borrowers
depend on the convention node rather than on eleven independent guesses.

⚠️ **Still invisible to every per-clause check**, and now demonstrably so: every one of
the fourteen modules this run has produced was individually well-formed and cited
correctly.

---

## R71 — (a) STYLE / INSTRUMENT · **R61 AND R62 TOGETHER PRODUCE A KEEP-LIST, AND A FIELD IN NEITHER LIST IS KEPT STALE — MEASURED, AND IT COST A TURN**

*From `l3877_3953_n014`, turn 2. **This is an adjudicator defect, committed by me,
caught only by reading the returned object field by field.***

The edit sent, verbatim:

> *"In `ontology`, the single entry keeps its `licence`, `cites`, `inference` and
> `toggleable` exactly as they are, and ONLY its `atom` becomes
> `user_authority(have_conversational_sense_heading)` and its `body` becomes null.
> Change nothing else."*

It was performed **exactly**. And the entry's **`gloss`** — named in neither the
keep-list nor the change-list — was kept **verbatim**:

> *"**R is a rule** in the #have_conversational_sense section and therefore carries
> user authority"*

**describing a bodied rule and a variable `R` that the same edit had just deleted**,
and re-asserting over *rules* precisely the content the same turn's new `claims` entry
recorded as **not encoded**. `translated`, `repair_needed=False`, **0 breaches, 0
findings.** A whole turn was spent repairing it.

⭐ **The mechanism, stated so it is not read as carelessness.** R61 taught *name the
field*. R62 taught *say "keeps its present sentence and ALSO"*, because "rewrite X so
that it states P" is heard as "REPLACE X with P". Obeying both yields an edit of the
form **keep{A,B,C,D} / change{E,F}** — and the model, correctly, does exactly what was
said and nothing that was not. **An enumerated keep-list is not a closure over the
entry.** R61 and R62 are each necessary, each correct, and **jointly they create a
hole neither one has.**

**The fix, one clause, and it costs nothing:**

> *"…and **every other field of that entry, including its `gloss`, keeps its present
> value**…"*

⭐ **THE THIRD MEMBER OF A FAMILY, NAMED.** R61, R62 and R71 are the same shape: an
instruction that is **correct and under-specified in the same direction**. R61 — names
a property, not a field. R62 — names an addition, heard as a replacement. R71 — names
a keep-list, heard as exhaustive. **All three are fixed by saying more, never by
saying it more forcefully**, which is the standing separation of *imperativeness* from
*length* (R22, R56).

⚠️ **And it was invisible to the floor**, which is **R66**: the stale gloss changed
nothing the checks count, in either direction. Turn 2 and turn 3 both returned **0
findings** — before and after the repair.

**Tally:** the *"keeps its present … and ALSO/ONLY"* form performed **6 of 6** on this
clause with zero collateral changes, **17 of 17** across clauses 12–14. **R71 is not a
miss of that form; it is a gap in what the form covers**, and the tally is left
uninflated rather than being credited with a save it did not make.

---

## R72 — (a) REVIEW-LIST FIX, one entry · **P3's test is PRESENCE, not REACHABILITY, so a claim encoded by a DEAD RULE passes it**

*From `l3877_3953_n014`, turn 1.*

P3 as written:

> *"**Ask:** check every entry in `claims` against the asserts. A claim present there
> and encoded nowhere is the fingerprint."*

Turn 1's C1 — *"the heading metadata assigns user authority to every rule in the
#have_conversational_sense section"* — **was** encoded: `user_authority(R) :-
rule_in_have_conversational_sense(R)`. **P3 passes.** And the rule can never fire: its
only body literal sits in `inputs`, and no situation being judged can ever report
which rules occupy a section of the document. The claim is encoded by a rule that
derives nothing, ever.

**This is P3's blind spot in the same place R41/R47 found the checker's:** *having an
encoding* and *having a live encoding* are different properties, and only the first is
cheap to test.

**Proposed second half for P3:** *"…and for each claim you find encoded, can the body
of its encoding ever be satisfied? A body literal that lives in `inputs` must name
something a case can actually supply — a message, a role, a case datum. If it names a
fact about the DOCUMENT, nothing will ever supply it and the claim is encoded in name
only."*

⚠️ **Note the relation to the anti-rules, so this is not read as licence to move
things.** The remedy is **never** to move the literal into `inputs` or out of
`requires` to satisfy a note — that is the standing anti-rule. The remedy is that a
document-side fact should not have been a body literal at all.

---

## R73 — (b) SCHEMA GAP, RECORDED and PROPOSED · **rule 9's three buckets have NO HOME for a fact about the DOCUMENT'S OWN LAYOUT, and every heading node in the corpus needs one**

*From `l3877_3953_n014`. The `class_no-legal-bucket` shape, in a new place.*

Rule 9 offers exactly three destinations for a name: the `ontology` block (*"non-deontic
classification this clause itself establishes"*), `requires` (*"another clause must
define it"*), `inputs` (*"predicates describing the case being judged"*).

`rule_in_have_conversational_sense/1` — **which rules sit under this heading** — fits
none of them:

* **not `inputs`.** It is not about the case being judged. Nothing in a conversation
  can supply it. Putting it there is the ⛔-marked error in `20_worked_example.md`, and
  it is what turn 1 did.
* **not `requires`.** No clause of the document defines which rules sit in a section;
  the section membership is a fact about the *file*, not about any clause's content.
  This was **my own drafted remedy, and it was wrong** — see the turn record.
* **not `ontology`.** The node would have to enumerate the section's rules, and it was
  shown none of them. Enumerating them is failure mode #1.

**The resolution actually taken** — `PROVISIONAL.md`'s: encode the section-level fact
the span *does* state, and record the divergence in `claims` — **is correct and is a
workaround.** It ships a module whose `claims` string carries content **no solver
reads**, and the graph asked for that content by name.

**Two candidate fixes, and the first is much cheaper:**

1. ⭐ **A convention node** (R70's route 2): one module owns *"a rule under a heading
   carrying `authority=X` has authority X"* and declares `rule_in_section/2` in its own
   `requires`, once, where the question of where that fact comes from can be answered
   deliberately instead of eleven times by accident.
2. **A fourth destination** — a `document_facts` list, for predicates whose extension
   is fixed by the document's structure rather than by any clause's text or by the
   case. ⚠️ **Proposed only as the alternative, and I do not recommend it:** a new
   field is a schema change touching `schema.py`, `checks.py` and the prompt, to hold
   what one ordinary node could hold.

---

## R74 — (a) PROCESS FIX, one line, and it applies retroactively to R37 · **"nothing breaks the tie" must name the ruling documents that were read**

*From `l3877_3953_n014`. This is a correction to an earlier entry in this file, filed
as its own entry so the correction is countable.*

**R37 filed itself as *"the run's most contestable judgement … a question, not a
fix"***, and framed its three routes as though nothing decided between them. On this
clause — the same node shape, a fresh draw — **`PROVISIONAL.md` decides it outright,
and this is its paradigm case rather than a boundary one:** *"`ESTABLISHES` … may not
**add** content the narrowed span does not state"*, with the addition routed to the
notes. `PROVISIONAL.md` existed when R37 was written. **R37 does not cite it.**

⛔ **And the cost was real, not hypothetical.** Because R37 was on record as
contestable, this clause's blind pass **deliberately steered away** from the
ground-fact remedy and drafted a different one — moving the predicate to `requires` —
which N1, N10 and `PROVISIONAL.md` then all refuted. **A recommendation's own
statement of its uncertainty propagated into a wrong remedy on a later clause.**

**The fix:** any entry in this file that claims a question is open, that nothing
breaks a tie, or that a judgement is contestable **must name which ruling documents
were checked** — at minimum `PROVISIONAL.md`, `REVIEW_LIST.md`'s anti-rules, and the
production prompt's own rules. An unsourced claim of ambiguity is unfalsifiable, and it
is **read as licence by the next clause**.

**R37 is hereby amended:** route 1 is not contestable on the encoding question —
`PROVISIONAL.md` settles what the module may assert. What remains genuinely open in
R37 is the **graph-side** question of who should provide the rules-level fact, and that
is R70 and R73.

---

## EVIDENCE FOR STANDING RECOMMENDATIONS — `l3877_3953_n014`

*Not new entries. Recorded so each population stays countable.*

* ⭐⭐ **R46, SECOND MEASURED INSTANCE.** *"A conclusion inherits the weakest licence in
  its derivation"* (`00_task.md`) — turn 1's `ontology` entry was licensed `textual`
  citing this node, while the **sole literal in its body** was licensed `assumed` by
  the same module, with the inference honestly named. **Nothing enforced the lattice:
  0 breaches, 0 relevant findings.** Different clause, different node shape, different
  draw from R46's original.
* ⭐⭐ **R47 / R50, THE CLEANEST FORM YET — and it moved the WRONG WAY.** The floor's
  findings went **2 → 0** across the repair that closed four defects. Both turn-1 notes
  named the predicate the repair deleted; the surviving name acquired a head, and a
  head buys silence. **Pre-registered in `out/l3877_3953_n014.turn2_prereg.md` before
  the call and confirmed.** R50 recorded an *invariant* total across a
  conclusion-changing edit; this is a **monotonically decreasing** total across an
  entirely corrective one.
* **R66, THIRD INSTANCE.** The gloss layer is invisible to every check: turn 2 left a
  stale `ontology` gloss and turn 3 repaired it, and the floor reported **0 findings
  both times**.
* **R68's proposed P9 widening — a SECOND supporting data point.** P9 read literally
  fires on `have_conversational_sense_heading/0`, which appears in no body — and the
  fire is **false**: the name is the argument of the module's one ground atom, which is
  the sanctioned pattern. R68's *"…as the head of an `ontology` entry, **or as an
  argument of one**"* is confirmed on an independent clause.
* **R64, THIRD APPLICATION and FIRST NEGATIVE.** R64 exists to stop P6 producing a
  false charge on a gloss using the node's own header vocabulary. Run here against
  turn 1's `user_authority` gloss: *platform*, *set by*, *ranks*, *below* occur
  **nowhere** in the node — not in the span, `ESTABLISHES` or `PROVIDES`. **R64 does
  not save the draft, and the P6 charge stands**, which is exactly the discrimination
  R64 was written to make possible.
* **R35, FOURTH INSTANCE — POSITIVE, ending seven consecutive negatives.** Zero finite
  verbs in the span; `ESTABLISHES` supplies subject, verb, object **and** a universal
  quantification over rules. Second of the zero-finite-verb kind (clause 6 was first).
* **R36, SECOND INSTANCE — found by MEASUREMENT, not by drawing the node.**
  `l171_426_n004` lists `root_authority` in both `PROVIDES` and `NEEDS`. On
  `l3877_3953_n014` itself R36 is **NEGATIVE** (`NEEDS: (none)`), and that is what made
  the clause a clean replication of R37 — see R70.
* **R67's conflict is structurally ABSENT here, for the first time.** With `NEEDS:
  (none)` an abstention could have set `outcome: abstained`, left every list empty and
  breached nothing. **The route was ruled UNSURE before the draft existed and was not
  charged either way**, and the binding survived P2 appearing to endorse translating —
  P2 distinguishes `ontology` from `asserts`, never translation from abstention.
* **R57 polarity: N/A**, second consecutive — no default, no defeater, no negation.
* **R65's N8 widening: OUT OF SCOPE** — every relation on this clause is arity 1.
  Reported so the widening's evidence base is not overstated.
* **The "clean floor / conclusion-changing defect" count is NOT incremented.** Turn 1
  passed `translated / repair_needed=False / 0 breaches` carrying three defects, and it
  does not join the population: the module attaches no status to any act, so there is
  no conclusion for a defect to change. **11 of 22**, unchanged for the fourth clause
  running.
* ⚠️ **DECLINED, with grounds on the record:** the `rule_in_section/2` parameterisation
  (failure-mode group ②'s *"do not invent shared vocabulary to pre-empt them"* — it
  became R70/R73 rather than an edit); and the heading-vs-section mismatch between the
  atom's argument gloss and its predicate's gloss (both pick out the same anchor;
  sending it would have been a manufactured finding).

---

# ADDED BY CLAUSE 15 — `l4252_4482_n005`

*"The assistant should be willing to speak in all types of accents, while being
culturally sensitive and avoiding exaggerated portrayals or stereotypes."*
**NEW clause, no reference verdict, no known defect.** Converged turn 2 of 5,
$0.00361998, 2 live calls, cap $0.03 never binding. Turn 1 was the unaided output.
**Ruling documents read** (R74): `prompt/00_task.md`, `prompt/10_output_format.md`,
`prompt/30_failure_modes.md`, `FINDINGS.md`, `REVIEW_LIST.md`, `PROVISIONAL.md`,
`out/l3877_3953_n014.turns.md`, `out/l4252_4482_n016.{span_enumeration,lessons}.md`,
`out/l171_426_n022.lessons.md`, and R35/R36/R47/R50/R57/R59/R65/R66/R70/R71/R72 here.

## R75 — (b) CHECK GAP, MEASURED · **`outcome=invalid` BUYS SILENCE ACROSS THE ENTIRE NOTE LAYER, so a repair from invalid to valid RAISES the finding count by construction — and the run has now measured the count moving in BOTH directions across genuine repairs, on adjacent clauses**

*From `l4252_4482_n005`, turns 1 and 2. Extends R47, R50, R59 and `l171_426_n022`'s L4.*

| | turn 1 | turn 2 |
|---|---|---|
| outcome | **invalid** | translated |
| breaches | 2 (one message, emitted twice) | **0** |
| findings | **2** | **7** |
| defects closed | — | **six** |

**All seven of turn 2's notes are anti-rule-protected non-findings:** one
`requires-unprovided` (which `REVIEW_LIST.md` says *"fire on every CORRECT
single-clause module"*) and six head-less notes on three `inputs` names that are
head-less **by design**.

⭐ **The mechanism is structural, not incidental.** `checks.py:562` returns at
`if mod is None:` before `arity_findings`, `polarity_findings` and `_link_findings`
run. So an invalid module cannot score more than its breach count, a valid one always
pays for its whole note surface, and **every repair that crosses the validity boundary
looks like a regression** — on precisely the repairs that matter most.

⛔ **Set beside clause 14, this closes the argument.** There, a repair closing **four**
defects drove the count **2 → 0**. Here, a repair closing **six** drives it **2 → 7**.
**Two adjacent clauses, two genuine repairs, the count moving in opposite directions,
neither of them the quality signal.** With R47 (a wrong definition buys the same
silence as a dead one), R50 (the total invariant across a conclusion-changing edit),
R59 (the ability to notice is created by the repair) and R65: **never read note counts
as a quality signal, in either direction. This is the fifth independent measurement.**

**Proposed:** report `outcome` and the breach/note split separately in any summary a
human reads, and **never** a bare finding count across attempts of differing validity.

## R76 — (a) REVIEW-LIST GAP, one entry · **N10's substring test is satisfied by a COMPOSITE name assembled from three separate substrings, and passes the fused-disjunction hollow stub**

*From `l4252_4482_n005` turn 1.*

The draft coined **`exaggerated_or_stereotypical/1`** for *"exaggerated portrayals or
stereotypes"*. Run N10 literally — *"for each name you coin, which substring of the
NARROWED span does it come from?"* — and every piece answers: *exaggerated* ✅,
*or* ✅, *stereotyp-* ✅. **The name passes, and it is failure mode #5 verbatim**
(*"a single ontology predicate named after a phrase in the clause reads correctly in
every explanation while containing nothing"*) **and #10** (a flat name where structure
was wanted): a response that stereotypes without exaggerating is indistinguishable
from one that exaggerates without stereotyping.

⚠️ N10 was written to catch an **unanchored** name (`tiananmen_example`). Its inverse —
a name **over**-anchored, transcribing a whole phrase including its connective — is the
one it cannot see, and it is the more common failure on a coordinated span.

**Proposed addendum to N10:** *"…and does the name transcribe a CONNECTIVE (`_or_`,
`_and_`) from the span? A coined name spanning a coordinator fuses two things the
document distinguished — split it into one name per conjunct, and note that under a
NEGATIVE operator the split is required (L6), not optional."*

⚠️ **Fence checked before proposing:** failure mode #10 sits in group ②, *"you cannot
see these, so do not try to fix them … do not invent shared vocabulary to pre-empt
them."* Clause 14 **declined** the `rule_in_section/2` parameterisation on exactly this
fence. **The fence does not reach here, and the distinction is the point:** clause 14's
split was a *cross-node* vocabulary decision made from inside one module; this split is
between two things **this clause's own single sentence names separately**. Sent.

## R77 — (a) REVIEW-LIST GAP, one entry · **no entry asks whether the chosen `status` has the right STRENGTH, and that was this clause's decisive defect**

*From `l4252_4482_n005` turn 1, found blind and found on NO list entry.*

The span says *"the assistant **should be willing to** speak in all types of accents"*.
The draft wrote `permit speak_in_accent(A) :- accent(A)`.

**A permission concludes that speaking is allowed. It does not conclude that refusing
is a failure.** *Should be willing to* is an obligation on the assistant's
**disposition** — the one sentence in the span that makes a blanket refusal a
violation. Under turn 1, **an assistant that declined every accent request violated
nothing**, and the module's read-back said so fluently.

**The list's coverage of `status`, enumerated:** **P1** is polarity *within* `prefer`
(does the `prefer` name the act to avoid?). **P2** is deontic-force-on-a-non-norm
(is the bearer the assistant? if not, route to `ontology`) — and run here it
**endorses** the deontic rendering, because the bearer *is* the assistant. **P4** is
the shape of several obliges on one body. **Nothing asks whether `permit` should have
been `oblige`.** The two entries that touch `status` both assume the strength is right
and interrogate the polarity or the bearer.

⚠️ **And the error is asymmetric in the dangerous direction.** An over-strong
`oblige` (which my own pre-registration predicted, and which did **not** occur) states
a rule the reader can see and dispute. An under-strong `permit` states a *true*
proposition — speaking in accents *is* permitted — and simply drops the requirement,
leaving nothing to dispute. **It is a hollow stub at the deontic layer.**

**Proposed new entry, P11:** *"**Modal strength.** For each `asserts` entry, would an
assistant that NEVER performs this act violate the span? If yes, the status must be
`oblige`; a `permit` says only that the act is available. Watch for spans whose verb
governs a DISPOSITION — *should be willing to*, *should be prepared to*, *should not
hesitate to* — where the act named in the span is the thing permitted and the thing
OBLIGED is the readiness to do it."*

## R78 — (a) REVIEW-LIST FIX, one entry + one anti-rule · **P8's head-in-own-body test is written for ONE rule, and a two-step `ontology` chain reaches the same shape; the anti-rule that protects the direct form does NOT cover the derived one**

*From `l4252_4482_n005` turn 1. This clause's decisive defect (L11) rode through it.*

```
exaggerated_or_stereotypical(A) :- speak_in_accent(A).
forbid speak_in_accent(A)       :- exaggerated_or_stereotypical(A).
```

Unfolded: **`forbid speak_in_accent(A) :- speak_in_accent(A)`** — a blanket prohibition
on every accent the assistant ever speaks in, derived from a span about *willingness*.
**P8 passes both rules individually**; neither head appears in its own body.

⛔ **And the anti-rules offer an exculpation, which must be refused explicitly:**
*"`forbid X(R) :- X(R)` is **SCHEMA-FORCED**, not a defect."* **Held against, on the
anti-rule's own stated reason** — *"an unconditional prohibition over a variable act
**requires** the tautological binder"* — which **presupposes that the document states
an unconditional prohibition**. This span states none. The anti-rule licenses the FORM
where the document supplies the CONTENT; here the form is identical and the warrant is
absent. (L10, third application: clause 13 held, clause 14 reversed, this one held.)

⚠️ **The second half, and it is the more dangerous:** the floor's **only** objection to
this module was that `speak_in_accent` was undeclared, and **the compliant one-line
remedy — add `speak_in_accent/1` to `inputs` — clears both breaches, turns `outcome`
to `translated`, and cements the inversion into a module the floor then passes.**
Clause 5's **L4** in its worse direction. ⭐ `REVIEW_LIST.md`'s own anti-rule
(*"moving the predicate into `inputs` to clear them destroys the distinction the design
calls load-bearing"*) independently protects the correct route, which was the one taken.

**Proposed, two lines.** To **P8**: *"…and UNFOLD first: substitute each `ontology`
rule into any body that uses its head, then re-ask. A two-step chain reaches the same
shape and neither rule shows it."* To the **anti-rule**: *"…**provided the document
states an unconditional prohibition on that act.** If it does not, the same shape is a
defect, and it is usually reached by unfolding rather than written directly."*

## R79 — (b) SCHEMA GAP, RECORDED and PROPOSED · **`closure` is forced once per act FUNCTOR, and on an act the clause OBLIGES all three values are vacuous**

*From `l4252_4482_n005` turn 2.*

`10_output_format.md`: *"For **every act class you govern** — every distinct functor
appearing in `acts` — add one `closure` entry."* The repaired module governs three
functors, two of which appear **only** under `oblige`:

```
be_willing_to_speak_in_accent -> cepa  "the clause obliges willingness …, so silence
                                        about any particular accent permits that willingness"
culturally_sensitive          -> cepa  "the clause obliges cultural sensitivity …, so
                                        silence … permits that sensitivity"
```

Both reasons are drawn from the clause, both are honest, and **both are near-empty**.
`closure` answers *"does the document's silence about this act permit it or prohibit
it?"* — a question built for the **forbid/permit** axis, where failure mode #13's
measured verdict flip lives. For an act the clause **requires**, the reading that
silence *permits* it is trivially true and decides nothing downstream; `cnpa` would be
incoherent; `unclear` would contradict the `oblige` the same module states.

⚠️ **The cost is not a wrong answer, it is a diluted signal.** The closure declaration
is forced precisely so that a real global commitment is never made silently. Requiring
one where no commitment is available trains the translator to write closure entries as
boilerplate, and the boilerplate is indistinguishable from the entries that matter.

**Proposed, minimal:** exempt an act functor appearing **only** under `oblige` from the
forced closure entry, or add a fourth value `n/a — this clause requires the act` with
the same forcing. **Recorded, not urged:** the change touches a required field's
contract, and one clause is thin evidence. ⚠️ Not incremented into any count.

## R80 — (b) SCHEMA GAP, RECORDED not proposed · **there is no licence value for *"the graph handed me this gloss"*, and on a `concepts` entry — which asserts nothing — `textual` has no target**

*From `l4252_4482_n005`, both turns. Filed rather than charged; the draft is not at
fault.*

The draft's `user_authority` concept is the NEEDS gloss **verbatim**, carrying
`licence: textual, cites: l4252_4482_n005` — a citation to **this** node for a name
**another** node defines. Run against **P6** (*"is every asserted predicate supported
by the NARROWED text?"*) it fires: the content is in the NEEDS header, not the span.
**HELD CLEAN on the prompt's own text** — `10_output_format.md` says a `concepts`
entry *"**Asserts nothing.**"*, so P6's *asserted* does not reach it.

⭐ **And that is exactly what makes the licence field incoherent here.** `textual`
means *"the cited clause says this"*; on an entry that asserts nothing there is no
proposition for the citation to support. `assumed` would demand an `inference` naming a
step the translator never took — the gloss was **handed over**, not derived. `world`
is plainly wrong. **All three values misdescribe the provenance of every borrowed
name's gloss, on every node in the corpus with a `NEEDS` block.**

⚠️ **Distinguished from clause 14's B3, and the distinction is the finding.** There the
gloss was **invented** under a `textual` licence (*"set by the user"*, *"ranks below
platform-level rules"* — words occurring nowhere in the node) and was charged as the
worst defect on the clause. Here the gloss is **accurate and verbatim**, and only its
licence is unavailable. **The charge does not transfer and was not made.**

**Recorded, no change proposed:** a fourth licence value is a large change to a
four-field obligation the schema checks together, and R73 already proposes one new
bucket. Both should be decided together, by the owner, not clause by clause.

## R81 — (c) GRAPH · **R70's family question, checked against a NAMED provider for the first time — and the borrow came out RIGHT, unprompted**

*From `l4252_4482_n005` turn 1. A negative result, reported so R70's evidence base is
not one-sided.*

R70 measured `user_authority` at **11 providers / 122 borrowers** across four
incompatible gloss families, all invisible to per-clause checks. Its family 3 —
*"the authority level of instructions in ONE NAMED SECTION"* — **names this node's
provider by id:** `'Use accents respectfully'` (**`l4252_4482_n004`**).

This node is `l4252_4482_n005`: **the sibling borrower, inside the same span id.** So
for the first time in fifteen clauses the borrower and its provider are **both
identified**, and the family match can be **checked rather than asserted**.

⭐ **It matched.** The draft's gloss is the NEEDS gloss verbatim — *"the user authority
level assigned to rules in the 'Use accents respectfully' section"* — squarely family
3, with no re-typing of the name as a property of the user, the assistant, a request
or a response. **L3 predicted this failure on the strength of two prior instances and
it did not occur.**

⚠️ **What this is and is not evidence for.** It is **one matched pair out of 122
borrowers**, and the match was **free**: the node's own NEEDS block spelled the gloss
out, and the draft copied it. It says nothing about the 121 borrowers whose providers
sit in other sections and other families, and **nothing at all about whether family 1
and family 3 borrowers can be linked** — which is R70's actual finding and remains
untouched. **R70's route 2 (one convention node) is unaffected.** Recorded because a
graph finding built only from its confirmations is not a measurement.
