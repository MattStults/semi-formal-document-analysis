# PROMPT FINDINGS — slice 4

Defects that belong to the **prompt**, not the translator. Kept separate on
purpose: the previous critic declined the borrowed-gloss fix BY NAME on the
grounds that `10_output_format.md` line 66 requires it and *"the worked example
does exactly this"* — and it was probably right that the PROMPT is what teaches
it. A prompt defect recorded as "clean module" is a defect that never gets
fixed, and a prompt defect recorded as a translator defect gets the wrong fix.

---

## ⭐ PF-1 — The abstention trigger "it is an example" is CONTRADICTED by the graph-node worked example, in the same system block

**This is the direct cause of the measured gap-1 finding**, and it means that
finding is largely a PROMPT defect, not a translator defect.

### The contradiction, both halves quoted

`prompt/00_task.md`, § *Abstention is a real answer*:

> If you cannot translate this clause faithfully — it is a section heading, it
> states a goal rather than a condition, **it is an example**, or its content is
> not expressible as rules — **abstain and give the reason**.

That is a test **on the kind of passage**. Now
`resolve_runs/graph_v2/node_worked_example.md`:

* **§ "A worked-example node — translate the lesson, not the dialog"** (line 213)
  — *"Node `l4251_4571_n029` is a document example (a good/bad response pair).
  Its lesson is a preference, so `prefer` is the status"* — and it then ships a
  full worked module with `"outcome": "translated"` for that example node.
* Line ~292, in the summing-up: *"Many graph nodes are commentary, headings, or
  document examples. … **What decides between them is whether the node
  establishes anything the document says — not what KIND of passage it is.**"*

The second sentence **denies the test the first file states**, in bold, by name.
`00_task.md` says *kind of passage decides*; `node_worked_example.md` says
*kind of passage does not decide*.

### Why the demonstration wins

`resolve_runs/graph_v2/config_graph_nodes.json` → `prompt.system_files` sends,
in order:

    ../../prompt/00_task.md
    ../../prompt/10_output_format.md
    node_worked_example.md          ← the contradiction, and it is LATER
    ../../prompt/30_failure_modes.md

The contradicting instruction arrives **after** the trigger list, is stated in
bold, and is backed by a complete worked module doing the thing. A translator
following the prompt faithfully translates example nodes. That is not a
capability failure and no amount of critic pressure on the translator fixes it.

### The measurement

`sweep.py:C_ABSTAIN_FRAME` over the **previous 17-clause cohort**
(`_debug_gen11/ds_opus_loop/out/`): an abstention trigger from `00_task.md` is
textually present in three of those modules' spans, and **every one of the three
is `outcome: "translated"`** — two on *"it is a section heading"*, one on
*"it is an example"*. On slice 4 the same check fires on two more spans, both
`**Example**:`-headed. The trigger is not a rare edge; the prompt has simply
overridden it.

### ⭐ This is DEBUGGING_TIPS §19 again, on a different contract

Tip 19 records exactly this shape: *"`requires` vs `inputs` — the WORKED EXAMPLE
teaches the opposite of the prose"*, with the ruling *"⇒ **Check the
DEMONSTRATION before concluding the task is impossible.** A contradictory example
looks identical to an unknowable distinction from the outside — both produce a
stable-looking coin flip — and they have wildly different fixes."*

**Second measured instance of the class, on a different pair of files and a
different contract.** That promotes "prose vs demonstration disagreement" from an
anecdote about one file to a recurring structural defect of this prompt, and it
suggests a mechanical check nobody has written: *for each rule stated in the
prose, does any shipped worked module violate it?*

### What is NOT being claimed

⛔ I am not claiming example nodes should abstain. `node_worked_example.md`'s
criterion — *does the node establish anything the document says?* — is very
plausibly the **better** criterion, and it is the one a coordinator would
probably ratify. The finding is that **two files in one system block state
incompatible tests**, so the answer is decided by which file the model weights
more, which is a coin flip nobody registered. Either file can be the one that
changes; that is the owner's call, not mine.

### Blast radius of the fix (per tip 19's table)

Prompt-only change ⇒ moves `provenance_hash`, not `contract_hash`. Modules stay
valid and still link; they merely stop being citable as evidence about the
current prompt. Cheap. The expensive alternative — treating it as a translator
defect and adding a review-list entry — would push the contradiction onto every
future translator instead of removing it.

---

## PF-2 — `oblige`/`prefer` on an example node has no way to record that its force is EXEMPLARY

Raised on `l1001_1107_n004`, and it generalises to every `**Example**:` node.

An example node licenses *"in this case, this response was good"*. The schema's
`asserts` has exactly four statuses and none of them carries "as illustrated".
So an `oblige` derived from a single worked exemplar is **byte-identical** to an
`oblige` derived from a stated universal duty — the same shape P7 names for
dropped defeasibility (*"an unconditional `oblige` is byte-identical to one whose
default was dropped"*), one level up.

`node_worked_example.md`'s own example-node module reaches for `prefer`, which
softens the force but is not the same distinction: `prefer` is for
**comparatives** (`00_task.md` 5b), and using it to mean "merely exemplary"
overloads a status that already has a job. There is currently nowhere else to put
it, so the only honest move available to a translator is prose in `claims`, which
nothing reads mechanically.

Recorded as a prompt/schema finding, not a translator finding: no translator
choice available on this corpus makes the distinction visible.

---

## PF-3 — the borrowed-`concepts` entry is forced to a licence the contract does not fit

Observed on every slice-4 module that carries a `NEEDS` name, and it is the same
family the previous critic already declined a fix on.

`10_output_format.md`: *"**every `requires` entry must also have a `concepts`
entry saying what you need it to MEAN**"*, and *"⚠️ **You are not defining the
term.** You are recording what this clause has to assume about it."* But the
licence table in `00_task.md` offers only `textual` (⇒ must cite), `assumed`
(⇒ must give an inference) and `world` (⇒ `toggleable: true`). A gloss for a
borrowed name is none of the three: it is neither something the cited clause
says, nor an inference this module drew, nor outside knowledge.

The node prompt then forces the choice: *"every ontology/asserts entry that cites
a source must cite EXACTLY '<this node id>'"*, and `node_worked_example.md`'s
modules stamp borrowed `concepts` entries `licence: "textual", cites: "<own
id>"`. So the translator writes a **self-citation for a concept another node
establishes** — which is defensible (the NEEDS line does appear in this node's
own text) and is also exactly the shape `00_task.md` calls the worst failure
available: *"Do not manufacture a citation to make a fact look textual."*

⛔ **Do not "fix" this on the translator.** It is prompt-directed and the
demonstration is unambiguous. Recorded so the class is visible; see the existing
`_debug_gen11/class_borrowed-gloss-split.md`.

---

## PF-4 — `licence: "textual"` on a rule whose body rests on `assumed` facts is what the demonstration teaches

Full analysis in `SWEEP.md` (class LICINH). Stated here because the sweep found
it in **every slice-4 module that has a body**, which is not a translator
pattern — it is the demonstration's pattern.

`00_task.md` states the lattice in bold: *"**Note: A conclusion inherits the
weakest licence in its derivation.** If a rule depends on one `world` fact,
everything it concludes rests on that fact."* Immediately after, the same file
says *"**A rule is not a fact.** Rules encode what the clause says and are traced
by their read-back annotation. Licences are for the facts your module asserts."*

Those two paragraphs give opposite answers for an `asserts` entry, which carries
BOTH a `licence` field and a body. The worked modules resolve it by stamping
`textual` and ignoring the lattice. The previous cohort's own review named the
class, called it *"mechanically checkable; nothing checks it"* — and left it in
12 of 17 modules. Slice 4 reproduces that rate exactly (see `SWEEP.md`).

**The four-line check exists now** (`sweep.py:C_LICINH`) and independently
recomputes the previous cohort's figure: **31 instances across 12 of 17
modules**, against the 32/12-of-17 on record. That agreement is what makes this a
prompt finding rather than a guess — the class is real, mechanical, and
unaddressed.

---

# PART II — what the five independent critics returned

Written after all five critic passes closed. Every claim below cites the file it
rests on; hashes are frozen in `CRITIC_LEDGER.json` and re-verifiable with
`critic_ledger.py verify`.

## ⭐ PF-1 CONFIRMED — three independent critics, three different clauses, same contradiction, same line numbers

PF-1 above was written by the coordinator from the prompt files, before any
critic reported. It then arrived **independently, three times**, from agents that
had not seen it and could not see each other:

| critic report | what it said |
|---|---|
| `l1001_1107_n004.critic_1.md` | *"'it is an example' — **FIRES**, literally and on every reading… If `00_task.md` were the whole contract, the only defensible answer here would be **abstain**, and the module would be CONCLUSION-CHANGINGly wrong."* Cites `00_task.md` 111–113 against `node_worked_example.md` 213–266 and 296–297. |
| `l1_170_n011.critic_1.md` | *"`00_task.md` lines 110–114 give a kind-of-passage discriminator while `node_worked_example.md` line 296 says 'not what KIND of passage it is'."* Recommends bounding line 296 to exclude statements of purpose or intent. |
| `l831_1000_n014.critic_1.md` | Same two passages, and adds the reconciling observation the others missed: **the prompt's worked example node is shown WITHOUT a `[node narrows this span to: …]` line**, so it is not a precedent for reading past a narrowing. Recommends stating that "it is an example" fires **on the narrowed text**, and adding the missing narrowing line to the worked example. |

⭐ Independent convergence of three readers on the same two files is much stronger
evidence than any one of them, and the third reader's reconciliation is a
concrete, cheap repair the coordinator's own reading did not reach. Note also
that both critics who found the trigger firing **still translated** — the
demonstration wins even when the contradiction is consciously in view.

`SCHEMA.json` line 7 was flagged twice as a **third** copy of the kind-based
trigger (*"A clause that cannot be translated faithfully — a heading, a goal with
no trigger, an example — should be declined"*), so a repair to `00_task.md` alone
leaves the contradiction standing in the schema.

## ⭐⭐ PF-5 — THE NARROWING STEP DELETES THE DOCUMENT'S WORKED EXAMPLES FROM THE CORPUS

**Escalated as the single most consequential finding of this slice.** Raised by
`l831_1000_n014.critic_1.md` as its own PF-4, which called it *"the real defect
this clause exposes"* and *"a graph-narrowing defect that silently removes the
document's four political-persuasion worked examples from the corpus"*.

The critic verified four sibling nodes (`l831_1000_n013/n014/n015/n016`) each
narrowed to a bare `**Example**: …` label while their `ESTABLISHES` summarises
the dialog printed beneath and outside the narrowing.

**Measured corpus-wide by the coordinator** (recompute; do not pin — command in
`SWEEP.md` §4): **roughly one node in eleven of the graph corpus is narrowed to
nothing but an `**Example**:` caption**, spread across at least eight different
line-blocks — so this is a systematic property of the narrowing step, not a local
accident. Nodes carrying an `**Example**:` heading anywhere are roughly a quarter
of the corpus.

Under the standing ruling that the narrowing governs, **every one of those nodes
must abstain**, and the Model Spec's worked examples — a substantial part of how
the document actually communicates its norms — enter the corpus through no module
at all.

⛔ **This is not a translator defect and no review-list entry can reach it.** It
is upstream of translation entirely. It is also invisible from inside any single
clause, which is precisely why the end-of-run sweep was mandated.

## PF-6 — an abstention CANNOT carry its `NEEDS` names, so graph links vanish

Raised independently by the `l831_1000_n014` **drafter** and by its **critic**
(as its PF-2). A direct collision between two prompt files:

* `10_output_format.md`, *When abstaining*: *"Set `outcome` to `"abstained"` …
  and leave every list empty. An abstention with content in it is neither an
  abstention nor a translation, and is rejected."*
* `node_worked_example.md`, contract 2: **every `NEEDS` name goes in `requires`**
  even when unused — and it calls dropping one *"the one outcome that cannot be
  inspected"*.

Every abstaining node with a non-empty `NEEDS` block must breach one of the two.
`l831_1000_n014` obeyed the machine-checked one and thereby dropped two declared
graph links (`targeted_political_manipulation_prohibition`,
`authority_level_ordering`) with nothing recording the drop. The drafter itemised
them in its notes; nothing mechanical would have.

**Recommendation from the critic, adopted here:** carve `requires` and its
matching `concepts` glosses out of the empty-lists rule for abstentions, or state
explicitly that abstention is licensed to drop inbound links. Either is fine; the
current silence is not.

## PF-7 — `PROVIDES`/`ESTABLISHES` hand over a genus word the narrowed span lacks

Raised by the `l2821_3040_n010` drafter. `PROVIDES` supplies *"uncertainty"*,
which is **absent from the narrowed span**. Contract 2 says carry the handed-down
meaning; `REVIEW_LIST` N10 says every coined symbol must trace to a substring of
the narrowed text. The drafter resolved it by keeping the genus in the `concepts`
gloss and never letting it become a symbol — but a translator could as reasonably
coin `uncertainty/1` and put it in every body, which would be unanchored **and**
would gate both rules on a fact no node visibly provides (the BORROWED-GATE
shape). `PROVISIONAL.md` decides the *conflict* case; this is an *addition* that
is a category word rather than a claim, and it is undecided.

## PF-8 — `kind:` is asserted on the span and is frequently wrong

Raised by the `l1_170_n011` drafter. The node header says `kind: conditional`
while the span contains **no** condition of any kind and its matrix verb is an
aim. A translator treating `kind:` as authoritative is pushed toward
manufacturing a conditional that is not there — a direct path to the
invented-obligation failure.

**Measured corpus-wide by the coordinator, and it is systematic:** `conditional`
is by far the modal `kind` in the node corpus, carried by well over two-thirds of
nodes, and it is stamped on nodes that carry no condition — including, on this
slice's own selection, a pure taxonomy item and a purpose statement. Of the
corpus's `**Example**:`-headed nodes, most are `meta` but a substantial minority
are `conditional`.

The drafter also observed that `ESTABLISHES`'s framing as *"the one claim this
module **must** express"* is standing pressure against abstention **even where
`ESTABLISHES` is itself accurate** — which is the same force PF-1 identifies,
arriving through a second channel.

## PF-9 — `Status` has four values and the document has a guideline tier

Raised by the `l3954_4251_n030` critic (its PF-2). *"should"* is rendered
`oblige` because `10_output_format.md` fixes the enum to
forbid/permit/oblige/prefer with no guideline tier, while the document itself
ranks *guideline* below *user* in its own authority hierarchy and this very node
carries `guideline_authority` in `NEEDS`. `prefer` is not the escape — it is
reserved for comparatives (`00_task.md` 5b), and overloading it would collide
with P1. So a guideline-level *should* and a root-level *must* compile to the
identical atom. Same family as PF-2 above (exemplary force) and as `REVIEW_LIST`
P7 (defeasibility): **the schema has one slot for deontic force and the document
uses at least three dimensions of it.**

## PF-10 — the read-back check is weakest exactly where the content is typographic

Raised by the `l3954_4251_n030` drafter. `_BAD_IN_TEXT` rejects backslashes in
every `read_back` and `gloss`, but this clause's entire content **is** backslash
delimiters, so the read-backs must transliterate (*"backslash-open-parenthesis"*).
**A module naming the wrong delimiter would still read fluently.** The redundancy
between `status` and `read_back` that the third anti-rule calls *"the only place
a wrong status is visible"* is degraded here by the output format rather than by
the translation.

---

# Summary for the coordinator

| finding | owner | cheap to fix? | evidence |
|---|---|---|---|
| **PF-5** narrowing deletes worked examples from the corpus | the graph's narrowing step | needs a decision, then a re-narrow | ⭐⭐ measured corpus-wide + 4 verified siblings |
| **PF-1** "it is an example" vs "not what KIND of passage it is" | `00_task.md` + `node_worked_example.md` + `SCHEMA.json` | ✅ prompt-only; moves `provenance_hash`, not `contract_hash` | ⭐ 3 independent critics, same lines; 2nd instance of DEBUGGING_TIPS §19's class |
| **PF-4** licence inheritance vs "a rule is not a fact" | `00_task.md` | ✅ prompt-only | ⭐ checker reproduces the prior cohort's 12-of-17 |
| **PF-6** abstention drops its `NEEDS` links | `10_output_format.md` | ✅ one carve-out | drafter + critic, independently |
| **PF-8** `kind:` is frequently wrong | the segmenter | needs investigation | measured corpus-wide |
| PF-3 borrowed-gloss self-citation | prompt convention | already a known class | 3 critics declined a fix on these grounds |
| PF-2 / PF-9 / PF-10 | schema / output format | needs design | 1 each |

⛔ **Nothing in this file was fixed by a translator, and nothing should have
been.** Under the previous arm, PF-1, PF-3 and PF-4 would each have been recorded
as "clean module" — which is the specific accounting error gap 4 was instrumented
to catch.

---

# PART III — from the turn-2 critic (`l2821_3040_n010.critic_2.md`)

Frozen at sha256 `c0c99959997a21d1…`. A fresh reader, fenced from the drafter's
notes, the span enumeration, **and turn 1's critique**.

## ⭐ PF-3 STRENGTHENED — the prompt contradicts itself IN WORDS on the borrowed gloss

PF-3 above recorded that a borrowed `NEEDS` name's `concepts` entry is forced to
a licence the contract does not fit. This critic reached the same class
independently, gave the exact lines, and found the piece I had missed: **the
prompt states both sides of the contradiction in prose, in one file.**

* `10_output_format.md:66-67` and `node_worked_example.md:44-49` require the
  borrowed name's `concepts` entry to be `licence: "textual"` **citing the
  borrowing node** — so `assistant_definition` and `guideline_authority` here
  cite a clause that says neither thing.
* `00_task.md:26-29` calls exactly that *"the single worst failure available
  here"*: *"Do not manufacture a citation to make a fact look textual… it creates
  an invented entity behind a passed check."*
* ⭐ And `10_output_format.md:76-78` — the **same file** as the requirement —
  says the entry is *"recording what this clause has to **assume** about it."*

So the requirement and its own rationale disagree about the licence, and the
demonstration settles it toward the reading `00_task.md` names as the worst
failure. **Declined at the translator level and logged here**, which is the
correct disposition and the third slice-4 clause on which a critic declined a fix
for prompt reasons.

## ⭐⭐ PF-11 — `REVIEW_LIST` P3 fires on every correct zero-assert module

Not strictly a prompt defect — a defect in the **review list**, and it is the
same shape as the P9 correction, so it belongs beside these.

P3 says *"check every entry in `claims` against the asserts."* A module that
correctly takes the ontology route has **no asserts**, so P3 fires on all of
them, and its literal remedy is to **invent a deontic entry the span does not
support**. Two of slice 4's five modules have zero asserts by design.

⛔ **P9's correction records that its original form "fires on every CORRECT node
module" and that this is "how seat 4c reached 48/86 on known-good modules". P3
has the same shape and has not been corrected.** It also compounds the known E6
trap: on a zero-assert module the entry fires unconditionally, so the
add-a-condition-or-delete-the-claim branch is armed on every ontology-route
clause in the corpus.

**Repair, one branch:** narrow P3 to *"check every entry in `claims` against the
asserts **and the ontology**"*. Full write-up and the mechanical evidence —
`sweep.py:C_CLAIMS_UNENCODED` already searches both and correctly does **not**
fire — are in `LESSONS.md` L8.

## PF-3b — the abstention triggers live in two files with two discriminators

A third independent restatement of PF-1, from a fourth critic. Recorded for the
convergence count, not as a new finding.
