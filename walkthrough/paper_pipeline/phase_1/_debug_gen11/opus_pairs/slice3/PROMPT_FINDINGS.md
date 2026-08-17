# PROMPT FINDINGS — slice 3

Defects that belong to the PROMPT, not to the translator. Gap #4 of the brief:
"the previous critic rejected the borrowed-gloss fix BY NAME on the grounds that
`10_output_format.md` line 66 requires it — and it was probably right that the
PROMPT is what teaches it." When a fix is declined because the prompt licenses
the thing, that is a prompt finding, not a clean module.

---

## ⭐ PF-1 — `00_task.md` and `node_worked_example.md` give OPPOSITE rules on abstention, and they are concatenated into the same system block

**MEASURED. This is the direct cause of measured gap #1, and it means the gap is
a prompt defect, not a critic defect.**

`config_corpus_all.json` builds the system block from four files in this order:

```
prompt/00_task.md  ·  prompt/10_output_format.md
resolve_runs/graph_v2/node_worked_example.md  ·  prompt/30_failure_modes.md
```

`00_task.md`, "Abstention is a real answer":

> If you cannot translate this clause faithfully — **it is a section heading**, it
> states a goal rather than a condition, **it is an example**, or its content is
> not expressible as rules — **abstain and give the reason**.

`node_worked_example.md`, closing the four good examples:

> What decides between them is **whether the node establishes anything the
> document says — not what KIND of passage it is.**

and, in the bad-example list:

> "It states no obligation" is not on its own grounds to abstain — **the heading
> node above states none and is translated.**

The later file does not merely soften the earlier one. It **retires two of
`00_task.md`'s four triggers by name** and demonstrates the retirement twice:

* a **heading** node (`l3995_4164_n001`) — translated, `ontology` only, `asserts` empty;
* a **document worked example**, a GOOD/BAD response pair (`l4251_4571_n029`) — translated as a `prefer`.

`node_worked_example.md` also replaces the binary with a **three-way route** that
`00_task.md` never states: a norm → `asserts`; a structural fact about the
document → `ontology` with `asserts` empty; **neither** → abstain.

### Why this is the whole of measured gap #1

The brief records that a clause headed `**Example**: medical question` was
translated with **zero occurrences of "abstain" in its entire transcript**, and
reads that as a critic never auditing the frame. On this slice the frame WAS
audited — every drafter and every critic was ordered to answer in words — and
**every one of them answered "translate", each citing `node_worked_example.md`'s
discriminator.** Two of the five spans are abstention-trigger shaped on their
face (`n003` is headed `**Example**:`; `n011` IS a `####` heading with an
`{#anchor authority=root}` block) and both are translated, correctly, under the
three-way route.

So the silence in the earlier transcript was not necessarily a missing question.
A translator reading all four files in order has already been told the trigger
does not fire, and has nothing to write down. **The instrument that shows the
question was asked cannot be the word "abstain" appearing in the transcript** —
that is a null-result detector with no positive control.

### The recommendation, stated so it can be rejected by name

`00_task.md` is the corpus-independent method file; `node_worked_example.md` is
the graph-node-specific one, and only the latter is on the node path. The
tempting fix — **delete "it is a section heading" and "it is an example" from
`00_task.md`** — is REJECTED here: `00_task.md` is shared with the flat-clause
corpora, where those triggers may still be live, and this slice measured nothing
about them. The fix that fits the evidence is narrower: `00_task.md`'s abstention
section should say that a corpus-specific prompt file may narrow this list, and
`node_worked_example.md` should say **which triggers it retires**, so the reader
is not left to infer the override from file order. Until then, two translators
can split on this seam for reasons that belong to neither of them.

⚠️ **Consequence for how the loop is scored:** a translator who abstains on
`n003` or `n011` is following `00_task.md` and is not wrong on the face of the
prompt. Counting that as a translator defect scores a prompt seam against the
model.

---

## PF-2 — the abstention contract makes an "abstain, but PROVIDES is promised" node unrepresentable

`10_output_format.md`: "Set `outcome` to `"abstained"`, give `abstain_reason`,
and leave **every** list empty."

`node_worked_example.md` on the heading node: "the node's `PROVIDES` names
`guideline_authority`, so **other nodes are waiting on this module** to make that
predicate derivable, and abstaining would strand every one of them."

The two combine into a real constraint the translator cannot see from either file
alone: on any node whose `PROVIDES` is non-empty, abstention is not merely
discouraged, it **breaks the graph**, because an abstention with every list empty
cannot supply the promised predicate. `l1108_1367_n011` is exactly this shape —
`PROVIDES: root_authority`, and other nodes in this very slice (`n003`, `n006`)
`require` a `root_authority`.

**Mechanically checkable, and nothing checks it:** *is `outcome == "abstained"`
on a node whose span's `PROVIDES` block is not `(none)`?* Three lines of Python.
It would fire on a real, silent graph break. Recorded in `LESSONS.md` as L-4.

---

## PF-3 — the prompt's NAF rule is scoped by "only" and by READ-BACK honesty; it says nothing about the DIRECTION the error runs in

`l1108_1367_n001` encodes its exception as
`forbid generate(C) :- erotica(C), not generated_in_exception_context(C)`.

⚠️ **Correction to an earlier draft of this file, recorded rather than
overwritten:** I first wrote that the prompt says nothing about negation as
failure. That was wrong, and the `n001` critic found the text I missed.
`00_task.md` rule 4:

> **Give each way of failing its own positive reason.** Do not conclude something
> "because the exception does not reach this case" **using only**
> negation-as-failure — `not p` carries no account of *why*, and the read-back
> then states a wrong reason for a right verdict.

and `30_failure_modes.md` #4 names the same failure — *"Right answer, wrong stated
reason … Caused by leaning on negation-as-failure."*

So the prompt's concern is **read-back honesty**, scoped by the word "only". Every
`n001` body carries a positive ground first (`erotica(C), not …`) and every
read-back verbalises the negation epistemically ("no … context **has been
established** for it"). On the prompt's own terms the module is compliant.

**What the prompt still does not say, and what the module actually turns on:**
nothing anywhere states that `not X` under a `forbid` head and `not X` under a
`permit` head are opposite safety bets. Under a prohibition, an unestablished
exception makes the duty FIRE — conservative. Under a permission, silence
LICENSES the act — the dangerous cell. The prompt has one rule about NAF and it
is about prose quality, not about which way an unknown fact falls. A translator
choosing between `not exception(C)` in a `forbid` body and a positive
`no_exception_established(C)` predicate is unguided on the only axis that changes
what the compiled program concludes.

⛔ Recorded as a PROMPT finding rather than a module defect, per gap #4. The
`n001` choice runs in the **conservative** direction and is not scored against it.
The review-list side of this is `LESSONS.md` L-1.

---

## PF-5 — a critic adjudicated against a prompt file that is NOT in this corpus's system block

**MEASURED, this slice** (`out/l1108_1367_n001.critic_t1.md`, sha `d29fe6047928c57e…`, cited
at L4, L91, L343, L423). The `n001` critic supported its NAF verdict by citing
`20_worked_example.md` bad example 3. That file is in `config_corpus_all.json`'s
**`unused_files`** list — it is never sent on the graph-node path. The translator
has never seen it.

The verdict survives, because `00_task.md` rule 4 (which IS in the system block)
says the same thing, and the critic cited that too. But the reasoning was
partly built on material the translator could not have read, and a finding of the
form "the prompt told you X" is void when the prompt in question was not sent.

This is the exact species of gap #4 running in reverse: gap #4 is a critic
excusing a defect because the prompt licenses it; this is a critic grounding a
finding in a prompt the translator never got. Both need the same discipline —
**a critic's prompt citations must be checked against the config's
`system_files`, not against the `prompt/` directory listing.**

⭐ **MECHANICALLY CHECKABLE, and nothing checks it:** extract every
`\w+\.md` mentioned in a critic file; assert the set is a subset of
`load_config(cfg)["prompt"]["system_files"]` basenames plus the review aids the
critic was explicitly handed. A dozen lines. It would have fired here.

The trap is easy to fall into: `prompt/20_worked_example.md` sits in the same
directory as the four files that ARE sent, and only the config distinguishes them.

---

## PF-6 — the borrowed-gloss licence: `textual` + self-cite on a meaning another node owns, on 5 of 5 clauses

**MEASURED on every clause in this slice — 7 instances across all five — and
raised by only ONE of the five per-clause passes.** This is a sweep result (see
`SWEEP.md`), and it is gap #4's own example class, arrived at independently.

Every `NEEDS` name must go in `requires` and must also carry a `concepts` gloss.
The gloss's content comes from the node's `NEEDS` header, which states in terms
that these concepts *"are established by OTHER nodes of the graph"*. Yet the
gloss is stamped `"licence": "textual", "cites": "<this clause>"` — *this clause
says this* — on a meaning this clause does not state. `l1001_1107_n009`'s span
says nothing whatever about root authority or about privacy being
context-dependent, and both are glossed `textual`, self-cited.

**Why no critic called it a module defect:** `node_worked_example.md`'s "good
one" does exactly this — `authority_levels_hierarchy` is a `NEEDS` name and its
`concepts` entry is `"licence": "textual"` citing the node itself. A translator
following the single worked example it is shown produces this every time.

⛔ **This is precisely the disposition gap #4 asks for: NOT a clean module, and
NOT a translator defect. It is a prompt defect, recorded as one.** The licence
field currently cannot distinguish "this clause says it" from "the graph header
handed it to me" — the one distinction `30_failure_modes.md` says the licence
exists to carry.

**The fix, with the tempting alternative rejected by name.** The tempting fix is
to have translators stamp borrowed glosses `assumed`. REJECTED: it makes
`assumed` mean two different things (an inference the translator drew, and a
meaning the graph supplied) and it puts every node module out of step with the
one worked example. The fix that fits is either an explicit ruling in
`node_worked_example.md` that a `NEEDS` gloss is licensed by the node's own
header and `textual`/self-cite is the correct encoding of that — said out loud,
because it currently reads as a violation of rule 1 — or a distinct licence value
for graph-supplied meaning.

⭐ **MECHANICALLY CHECKABLE in three lines** (`mech.py:c_needs_gloss_licence`):
is a `concepts` entry whose name appears in the span's `NEEDS` block licensed
`textual` and citing this clause? Nothing checked it before this slice.

---

## PF-4 — the harness, not the prompt: `slice3/validate.py` misreported a clean module as "2 error(s)"

Not a prompt defect, recorded here because it is the same species — a defect in
the scaffolding that would have been booked against the translator.

The first version of `_debug_gen11/opus_pairs/slice3/validate.py` (written by the
coordinator) treated `schema.validate_all`'s `(Module, list[Breach])` **tuple** as
a flat error list, so every module printed `schema.validate_all: 2 error(s)` — the
`Module` repr as error 1, the empty breach list as error 2 — and then died with
`TypeError: 'CheckResult' object is not iterable` before printing a single note.

**All four drafters that saw it caught it, named the exact cause, refused to
edit it (it was outside their fence), and re-ran the two calls directly rather
than distorting a module to make the number go down.** That is a positive control
worth keeping: it is evidence the "nothing changed" reports on this slice are
application and not rubber-stamping, because the same agents demonstrably did not
accept a tool's word when it conflicted with the document. The harness was fixed
by the coordinator before any critic ran; the fixed version is what produced
every number in `SWEEP.md`.

**Class, mechanically checkable:** *does the validation harness report zero
findings on a module known to be clean, and at least one on a module with a known
injected defect?* A validator nobody has run a positive control through can report
anything. Every check in `slice3/mech.py` was self-tested this way before use.
