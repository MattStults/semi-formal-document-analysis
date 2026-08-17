# PROMPT FINDINGS — slice 2

Defects that belong to the **prompt**, not to the translator. Filed separately because
"the critic declined the fix, so the module is clean" and "the critic declined the fix
because the prompt requires the thing" are different results, and the previous cohort lost
the second one for want of a place to put it. (Measured gap 4.)

⛔ **Nothing here has been applied.** No prompt file was edited by me or by any agent of
this slice. These are findings for the prompt owner.

## ⭐ Every line reference below was verified by the coordinator against the source file,
not taken from an agent's report.

---

# PF-A ⭐⭐ — `00_task.md` and `node_worked_example.md` give OPPOSITE answers on whether an example span is translated

**This is the root cause of measured gap 1, and it is a prompt defect, not a translator
defect.** A fix aimed only at the translator or the critic will not close it.

`prompt/00_task.md` **lines 110–113**:

> If you cannot translate this clause faithfully — it is a section heading, it states a
> goal rather than a condition, **it is an example**, or its content is not expressible as
> rules — **abstain and give the reason**.

Read straight, membership in that list is sufficient to abstain.

`resolve_runs/graph_v2/node_worked_example.md` **line 213**:

> `## A worked-example node — translate the lesson, not the dialog`

— which then translates a document GOOD/BAD response pair into a `prefer` assert and
presents it as the model answer. And **lines 296–297** of the same file state the opposite
rule outright:

> What decides between them is whether the node establishes anything the document says —
> **not what KIND of passage it is.**

The two files are concatenated into one system block **with no precedence rule between
them**, and they disagree on the single decision that determines whether a module exists at
all. A translator weighting `00_task.md` abstains; a translator weighting the worked
example never asks the question. Both are following the prompt.

**Why this predicts the measured gap.** `node_worked_example.md` is long, concrete,
structurally identical to the input, and *demonstrates* translating an example;
`00_task.md`'s trigger is three words inside a list. Demonstration beats enumeration. The
previous cohort's `**Example:**`-headed clause translated with **zero occurrences of
"abstain" in its whole transcript** is exactly what this contradiction produces.

**Consequence for the abstention rate.** `00_task.md` calls the abstention rate "a signal
we want". A signal produced by which of two contradictory instructions a sampler happened
to attend to carries no information.

*Raised on `l1001_1107_n013` (span headed `**Example**: asking for Acme employee
information`, `kind: meta`). Independently live on `l1108_1367_n010`, whose span IS a
section heading — the FIRST trigger in the same list — and which was also translated.*

**Suggested repair (not applied).** Make the two files state one rule. The line-296 test is
the better one and is already written: *abstain when the node establishes nothing the
document says.* One file states it; the other must not restate it — two descriptions of one
rule drift, which `10_output_format.md` says about field descriptions in its own §Fields.

---

# PF-B ⭐⭐ — the worked example teaches a manufactured citation on every borrowed `NEEDS` gloss

**Filed independently by FOUR of this slice's five drafters and by at least one critic that
never saw any drafter's reasoning.** That is the strongest convergence in the run.

The mechanism is structural, and it starts with a rule that is itself sound:

* `prompt/10_output_format.md` **line 66** — *"And every `requires` entry must also have a
  `concepts` entry saying what you need it to MEAN."* Compulsory, with good reasons given.
* A `requires` entry is, by the node contract, **another node's content**. So every node
  with a non-empty `NEEDS` block is forced to write a gloss for content its own span does
  not state.
* The only worked examples of doing that mark it `textual`, citing the node's own id:
  * `node_worked_example.md` **lines 47–49** — `authority_levels_hierarchy`,
    `"licence": "textual", "cites": "l527_796_n012"`.
  * `node_worked_example.md` **lines 230–232** — `voice_turn_taking_rule`,
    `"licence": "textual", "cites": "l4251_4571_n029"`.
* And **lines 268–269 of the same file** say, of that second example, in the prompt's own
  words:

  > **Nothing in this birthday example turns on voice turn-taking**; the graph linked the
  > node to that concept anyway.

**The prompt therefore states that the span has nothing to do with the concept, and in the
same example cites that span as the textual source of the concept's meaning.**

Against `prompt/00_task.md`, which defines `textual` as *"the cited clause says this"* and
calls a citation for something the clause does not say **"the single worst failure
available here"**, because it creates an invented entity behind a passed check.

**Nothing in the pipeline catches it.** `schema.validate_all` and `checks.run_checks` do not
compare a `licence` against span text; both the `textual` and the `assumed` form pass with
zero breaches and `repair_needed: False`. Measured on this slice: modules that took opposite
answers on the identical question were byte-indistinguishable in every instrument the
pipeline runs.

**Direction of harm.** The borrowed gloss is the ONLY place a provider/consumer mismatch on
a shared concept can surface (`REVIEW_LIST` N8). Marking it `textual` asserts that this node
is the authority for a meaning it borrowed — so a disagreement between two nodes reads as
two textual claims about one document rather than as one node's assumption, which is the
form in which it could be inspected.

*Raised independently on `l1001_1107_n002`, `l1001_1107_n008`, `l1108_1367_n005`,
`l1108_1367_n010`, and by the independent critic of `l1001_1107_n008`.*

**Suggested repair (not applied).** Change the `NEEDS`-concept entries in the worked
examples to `assumed`, `cites: null`, with an inference of the form *"the node's NEEDS block
hands this name and meaning to the module; the span does not state it"* — **unless** the
span genuinely uses the concept's words, in which case `textual` is right and the example
should say why. `PROVISIONAL.md` ground 2 already reasons exactly this way for the
neighbouring `ESTABLISHES` case: *"anything `ESTABLISHES` adds is still expressible: as
`assumed`, with the inference naming `ESTABLISHES` as its source. Nothing is lost, only
marked."*

---

# PF-C ⭐ — the worked HEADING node violates the prompt's own licence-inheritance rule

`prompt/00_task.md`:

> **Note: A conclusion inherits the weakest licence in its derivation.**

`resolve_runs/graph_v2/node_worked_example.md` **lines 184–201**, the model heading node
`l3995_4164_n001`, does this:

```json
"concepts": [
  { "name": "rule_under_heading", "arity": 2,
    "licence": "assumed", "cites": null,
    "inference": "the node speaks of the rules under a heading, so a relation between a
                  rule and a heading must exist" }, ...
],
"ontology": [
  { "atom": "guideline_authority(R)",
    "body":  "rule_under_heading(R, unprompted_personal_comments_heading)",
    "licence": "textual", "cites": "l3995_4164_n001" }
]
```

**The conclusion is marked `textual` and its only body fact is `assumed`.** Verified by the
coordinator against the file, not reported second-hand.

This is the **licence-inheritance class the previous loop NAMED, called "mechanically
checkable; nothing checks it", and left in 12 of 17 clauses**. This slice's finding is
stronger than "nothing checks it": ⭐ **it is TAUGHT**, in the model answer, on the corpus's
largest node class — `authority_convention.md` measures the section-authority edge class at
~47% of all golden-vs-ds3 edge divergence.

*Raised on `l1108_1367_n010`, whose span is a heading of exactly this shape. That drafter
followed the RULE and not the EXAMPLE: it split the genuinely textual label fact
(`heading_authority_label(no_erotica_or_gore_heading, system)`, `textual` — the document
does print that attribute) from the propagation to the section's rules
(`system_authority(R) :- rule_under_heading(R, …)`, `assumed`, inference naming the
markup convention). Nothing was lost; the derivation is now inspectable.*

**Suggested repair (not applied).** One word and one field in the worked example: mark that
`ontology` entry `assumed` with an inference naming the heading-attribute convention. Or,
if the intended teaching is that a heading's scope IS textual, say so — but then the
`rule_under_heading` concept above it should not be `assumed`, and the example currently has
it both ways.

---

# PF-D — `ESTABLISHES` arrives pre-formalised, making the deontic call upstream of the translator

Lower confidence than A–C; recorded because two clauses hit it.

The node's `ESTABLISHES` field is a derived summary, and on several nodes it arrives already
in deontic form — `l1001_1107_n013`'s reads *"the assistant **must not** share … but **may**
offer a privacy-safe alternative path"*, and calls the span *"a worked example"* in the
translating sense. The prompt asks the translator to decide force (`forbid`/`permit`/
`oblige`/`prefer`) from the document; `ESTABLISHES` has often decided it already, one
generation step from the text and outside the citation contract.

`PROVISIONAL.md` governs the *content* conflict (the narrowing governs) but says nothing
about the *force* being pre-decided, which is a different question and is currently
unruled.

*Raised on `l1001_1107_n013`; visible on `l1108_1367_n010`, where `ESTABLISHES` supplies the
scope rider ("applying to all rules in that section") that the heading line does not state.*

---

# PF-E (minor) — a contract-forced double note reads as a defect

Every correctly declared `inputs` predicate draws BOTH a `concept-declared` and a
`situation-input` note, and every correctly recorded `NEEDS` name draws
`requires-unprovided`. On this slice that is 3–18 note-severity findings per module, all of
them contract-required and all of them left standing per `REVIEW_LIST`'s anti-rules. It is
not a false positive in the checker's terms, but it is the noise floor that makes a real
note hard to see, and it is the shape that got `REVIEW_LIST` P9 written wrongly the first
time (an entry that fired on every correct module).

*Raised on `l1001_1107_n013` (18 notes, zero of them actionable).*
