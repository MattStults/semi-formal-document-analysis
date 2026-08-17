# PROMPT FINDINGS — slice 5

Defects that belong to the **prompt**, not to the translator.

Gap 4 of the brief: *"Prompt defects masquerade as translator defects."* The previous
critic rejected the borrowed-gloss fix BY NAME on the grounds that `10_output_format.md`
line 66 requires it and "the worked example does exactly this" — and it was probably right
that the PROMPT is what teaches it. Anything below is a case where the module does the
thing **because a production prompt file told it to**, so recording the module as "clean"
would lose the finding entirely.

Every entry names the file and the line. All four files here are in the production system
block for `config_graph_nodes.json` / `config_corpus_all.json`, concatenated in this order:
`00_task.md` → `10_output_format.md` → `node_worked_example.md` → `30_failure_modes.md`.

---

## ⭐ PF-1 — TWO PRODUCTION PROMPT FILES GIVE CONTRADICTORY ABSTENTION TESTS, AND THE LATER ONE SILENTLY OVERRIDES THE EARLIER

**This is the finding of the slice, and it re-explains a result that was previously
scored as a critic defect.**

The brief records, as measured on the previous cohort: one clause whose span was headed
`**Example**` *"was translated anyway, with zero occurrences of 'abstain' in its entire
transcript, though `00_task.md` lists 'it is an example' as an abstention trigger."*
That was read as the critic never asking the question. **The prompt had already answered
it.**

### The two texts

`prompt/00_task.md`, § *"Abstention is a real answer"* (line 112) — a test on the KIND of
passage:

> If you cannot translate this clause faithfully — **it is a section heading**, it states a
> goal rather than a condition, **it is an example**, or its content is not expressible as
> rules — **abstain and give the reason**.

`resolve_runs/graph_v2/node_worked_example.md` line 296 — a test that explicitly rejects
the KIND of passage as the criterion:

> Many graph nodes are commentary, **headings, or document examples**. The two honest
> answers are a small module that records only what the node actually establishes … and a
> clean abstention … What decides between them is whether the node establishes anything the
> document says — **not what KIND of passage it is**.

and again at line 342:

> *"It states no obligation" is not on its own grounds to abstain — the heading node above
> states none and is translated.*

`node_worked_example.md` also ships two worked exemplars that **translate** exactly the two
kinds `00_task.md` names as triggers: a heading node (`l3995_4164_n001`, § *"…the rules
under a heading carry guideline authority"*, line ~150) and a document-example node
(`l4251_4571_n029`, § *"A worked-example node — translate the lesson, not the dialog"*,
line 213).

### Why it bites, and why it is a PROMPT defect and not a translator defect

The two files are **both in the system block**, and `node_worked_example.md` comes **third,
after** `00_task.md`. A translator reading in order meets the trigger list, then meets a
specific, worked, node-shaped counter-instruction that names the same two kinds and
translates them. The later, more specific, more concrete instruction wins — which is the
correct thing for a reader to do, and it means **the `00_task.md` trigger list is
effectively dead for headings and examples on this corpus.**

Nothing anywhere states that the trigger list has been narrowed. So:

* a translator that abstains on an Example can be told it ignored the worked example;
* a translator that translates one can be told it ignored `00_task.md`;
* and **a transcript containing zero occurrences of "abstain" on an Example-headed span is
  the expected output of this prompt**, not evidence of a lazy reader.

### Measured on this slice, on both kinds, independently

The deterministic selection handed slice 5 one of each, and both drafters resolved the
tension the same way and cited the same lines:

| clause | kind | outcome | what it cited |
|---|---|---|---|
| `l1001_1107_n011` | span headed `**Example**`, node kind `meta` | `translated` | `node_worked_example.md` line 296 and the worked-example node at line 213 |
| `l1108_1367_n013` | span is a bare `####` markdown heading | `translated` | the heading-node exemplar at line ~150 |

Two independent agents, no communication, opposite ends of the corpus, same reading. That
is strong evidence the prompt teaches this, rather than that either agent rationalised.

### ⚠️ What this does NOT settle

**It does not settle whether translating them is RIGHT.** The frame question is still open
and still worth asking per clause — `l1001_1107_n011` in particular asserts an `oblige`, a
`forbid` and a `prefer` derived from a two-turn *illustration* of a rule another node
already states. It settles only **whose defect it is**: an instruction-file conflict, fixable
in one edit, and not a translator or critic failing.

### The one-line fix this suggests (owner's call, not mine)

Reconcile the two files in one direction and say which. Either narrow `00_task.md`'s trigger
list to the test `node_worked_example.md` actually applies (*does the node establish anything
the document says?*), or state in `node_worked_example.md` that its heading/example exemplars
are exceptions to the trigger list and why. **Leaving both is the condition that produced the
measured result.**

---

## PF-2 — THE BORROWED GLOSS IS LICENSED `textual` BY THE WORKED EXAMPLE, AND CITES A NODE THAT DOES NOT DEFINE IT

Named in the brief as the class the previous critic rejected BY NAME. It is real, it is the
prompt's doing, and **it fires on this slice too** — the sweep counts the hits.

**The contract that forces the entry to exist**, `prompt/10_output_format.md` line 66:

> ⭐ **And every `requires` entry must also have a `concepts` entry saying what you need it
> to MEAN.**

**The exemplar that teaches the licence**, `resolve_runs/graph_v2/node_worked_example.md`,
the good conditional node `l527_796_n012` — `authority_levels_hierarchy` is a **NEEDS** name,
owned by another node, and the worked example glosses it:

```json
{ "name": "authority_levels_hierarchy", "arity": 2,
  "gloss": "which of two levels of the chain of command is the higher one",
  "licence": "textual", "cites": "l527_796_n012", ... }
```

`prompt/00_task.md` defines `textual` as *"the cited clause says this"*, and warns in the
strongest terms available in the file:

> **Do not manufacture a citation to make a fact look textual.** … it creates an invented
> entity *behind a passed check*.

`l527_796_n012` does not define the authority hierarchy. Another node does. The worked
example therefore demonstrates the exact shape the task file forbids, and every module that
copies it inherits a citation the cited node cannot support.

**Verdict: PROMPT defect.** A translator following the only worked example it is given
cannot avoid this, and marking it against the translator would be scoring the prompt's
choice as the model's error.

**Candidate fix (owner's call):** the borrowed gloss is precisely an `assumed` fact — *"what
this module has to assume the borrowed name means"* — which is what `10_output_format.md`
already says it is two lines later (*"You are not defining the term. You are recording what
this clause has to assume about it."*). The file's own prose and its own exemplar disagree.

---

## PF-3 — ABSTENTION IS ALL-OR-NOTHING, WHICH PENALISES ABSTAINING ON ANY NODE THAT `PROVIDES` A NAME

`prompt/10_output_format.md`, § *"When abstaining"*:

> Set `outcome` to `"abstained"`, give `abstain_reason`, and **leave every list empty**. An
> abstention with content in it is neither an abstention nor a translation, and is rejected.

`node_worked_example.md` (heading node, line ~161) states the consequence plainly:

> the node's `PROVIDES` names `guideline_authority`, so other nodes are waiting on this
> module to make that predicate derivable, and **abstaining would strand every one of them**.

So on any node with a non-empty `PROVIDES`, abstention is not a neutral answer — it breaks
the graph. The schema offers no "abstain from the norm, record the structural fact" middle,
even though that is exactly what the heading exemplar does under the name `translated`.

**Why this is a finding and not a complaint:** the abstention RATE is described in
`00_task.md` as *"a signal we want, not a failure we penalise"* — but the output contract
penalises it structurally on precisely the nodes where the frame question is most live
(headings and examples both tend to carry `PROVIDES`). The signal is biased by construction,
and nothing records that.

Both slice-5 drafters were told about this shape explicitly and asked whether it moved their
answer; both said it did not change the outcome, and `l1001_1107_n011`'s notes record that it
"only raised the cost of being wrong". **INFERRED, not measured** — one turn on two clauses
cannot separate "did not move the answer" from "moved it below the reporting threshold." A
clean measurement would need an arm where a partial abstention is representable.

---

*(Further entries are appended as the critics return. A critic that declines a fix because the
prompt licenses the thing lands here, not in the module's clean column.)*
