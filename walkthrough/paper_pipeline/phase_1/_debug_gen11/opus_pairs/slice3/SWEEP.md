# SWEEP — every class raised by any clause, run back across all five

---

# ⛔ 0-PRE. ARTIFACT-INTEGRITY AUDIT — run after a sibling slice found a critic file rewritten in place

A sibling slice found its `critic_1.md` **rewritten in place between two
readers**: two agents read materially different documents under one filename and
neither could tell, which makes "the critic confirmed it" unfalsifiable. The
same slice self-reported a second defect — **its own reasoning attributed to the
critic**. Both are invisible to `validate.py`, which does not read prose. This
section is my audit of the same two failures in slice 3. **It is a finding about
the run, not a tidy-up.**

## A. Was any critic artifact overwritten? — **count: 0 detected, and here is exactly how strong that is**

| clause | critic artifacts | outcome |
|---|---|---|
| `l1001_1107_n003` | `critic_t1` | closed t1 |
| `l1001_1107_n009` | `critic_t1` | closed t1 |
| `l1108_1367_n001` | `critic_t1` | closed t1 |
| `l1108_1367_n006` | `critic_t1` | closed t1 |
| `l1108_1367_n011` | `critic_t1`, `critic_t2` | closed t2 |

**Evidence FOR non-overwrite — structural, and it is the strong kind:**

1. **No critic filename was ever handed to two agents.** Each critic dispatch
   named exactly one output file and no other agent was given that name. The
   `n011` second pass was dispatched to a **different** filename
   (`critic2`, now `critic_t2`) rather than revising the first — so the one
   clause that had two critic passes is the one that already carries two files.
2. **Every critic was explicitly fenced from reading `*.critic*.md`**, so no
   critic could have read, let alone revised, another's.
3. **Critics were told to write one file and edit only the module.** The one
   critic that edited anything (`n011` t1) edited the `.json`, and its mtime
   (21:01:27) precedes its own write-up (21:03:47) — the ordering a single
   edit-then-report pass produces.
4. Each `.critic_t*.md` carries a single distinct mtime inside its own agent's
   run window; none is later than its agent's completion.

⚠️ **What this evidence does NOT establish, stated plainly.** mtime records only
the LAST write. **I cannot prove from the filesystem that any file was written
exactly once** — a same-agent overwrite seconds apart would leave precisely the
trace above. The audit rests on dispatch structure, not on forensics, because no
hash was taken at write time. That is the gap; it is now closed going forward,
not retroactively.

⭐ **NEAR MISS, recorded because it is the actual mechanism.** Twice during this
slice a dispatch was refused for concurrency (`n011` drafter once, `n011`
**critic t1** once) and I **re-dispatched the identical prompt, naming the same
output file**. Both refusals errored before launching, so only one agent ever ran
per filename. **Had either refusal been a false negative — the agent launching
but the tool reporting failure — two agents would have written one critic
filename, and I would have had no way to tell.** That retry pattern is exactly
how the sibling slice's defect gets made, and it was not caution that prevented
it here.

## B. Remediation applied

* **Turn-versioned, write-once names.** All critic artifacts renamed
  `<id>.critic_t<N>.md`. Content unchanged — verified by hash before and after
  the rename. A revision is now a NEW file, never an edit.
* **`MANIFEST.sha256`** freezes all 16 artifacts. A changed hash on a
  `.critic_t*.md` is a rewrite-in-place, full stop.
* **`check_immutable.py`** — three checks, self-tested: C1 every critic artifact
  is turn-versioned; C2 every artifact still matches the manifest; C3 every
  "the critic found X" claim in the write-ups names an artifact or is marked
  MINE ALONE. ⭐ **C3 fired on 14 paragraphs of my own write-ups on its first
  run** — which is how the two defects below were caught rather than shipped.

## C. ⛔ Two attribution defects, both MINE, corrected in place with the correction stated

I re-read every "the critic found X" claim against the artifact rather than
against the agents' return messages. **Two failed, and both were the sibling
slice's second defect reproduced in my own write-ups.**

| # | claim | verdict | where corrected |
|---|---|---|---|
| **A-1** | "the critic's own note is the anti-rule: *the repair is to RENAME the input leg*" (`n006`) | ❌ **FABRICATED ATTRIBUTION.** The critic said the entry is load-bearing and must be **left alone**; the *rename* remedy was mine. | §S-8, corrected, remedy re-tagged **MINE ALONE, NOT CORROBORATED** |
| **A-2** | drafter quoted as saying *"look at this first"* (`n011`) | ❌ **FABRICATED QUOTE.** Not in the file — it was my own paraphrase of the agent's return message, re-quoted as the artifact. Substance verified; wording did not exist. | `LESSONS.md` L-11, corrected |

**Twelve further attributions were verified line-by-line against the artifacts
and stand**, each now citing its file: `n001` critic refusing N5 by name (t1
L305–314, and *"N5 needs a polarity condition"* is verbatim at L314); `n001`
citing `20_worked_example.md` (t1 L4, 91, 343, 423); `n001` considering and
rejecting the four-forbid collapse (t1 L382–383); `n009` refusing to delete its
third assert (verbatim); `n009` raising NAF-1 unprompted; `n009` + `n006` both
recording that P9's original form would have made them delete a
contract-required entry (t1 L238 and L250 respectively); `n006`'s hand trace
(t1 L50–83); `n011` drafter noting the polymorphism (notes L297); `n011` t1
widening the gloss (t1 L121, L160, ledger L296–300); `n011` t2 on mismatch
visibility (t2 L92–107); all four drafters diagnosing the `validate.py` bug
(present in all four `.notes.md`).

⚠️ **Both defects ran the same direction: they made an independent pass look
like it had corroborated more than it did.** Neither changed a module, a count,
or a verdict — but "the critic confirmed it" is the load-bearing claim of this
whole run, and I inflated it twice. Reported unsoftened.

---

Measured gap #2: *"Classes found late never reach clauses done early. The
previous loop NAMED a licence-inheritance class, called it 'mechanically
checkable; nothing checks it', and left it in 12 of 17 clauses because the loop
was per-clause with no end-of-run sweep."*

This file is that sweep, and the **delta** — what the sweep caught that the
per-clause pass did not — is its point.

The sweep is not a re-read. It is two Python files, written after the clauses
were done, run over all five modules at once:

* `mech.py` — 20 within-module checks. Every class any drafter or critic raised
  that could be reduced to a mechanical question.
* `cross.py` — 5 **cross-module** checks. These cannot run on one module at a
  time and the per-clause loop is structurally blind to them.

Every check in `mech.py` was **self-tested before use**: an injected defect was
shown to fire it, and the clean baseline was shown not to. A check nobody has
run a positive control through can report anything.

---

## 0. State of the five modules

| clause | outcome | asserts | ontology | claims | schema breaches | check errors |
|---|---|---|---|---|---|---|
| `l1001_1107_n003` | translated | 2 | 0 | 3 | 0 | 0 |
| `l1001_1107_n009` | translated | 3 | 1 | 4 | 0 | 0 |
| `l1108_1367_n001` | translated | 4 | 6 | 7 | 0 | 0 |
| `l1108_1367_n006` | translated | 1 | 11 | 6 | 0 | 0 |
| `l1108_1367_n011` | translated | 0 | 2 | 2 | 0 | 0 |

Re-derived by the coordinator through `schema.validate_all` + `checks.run_checks`,
not taken from any agent's word. Every module: `repair_needed=False`. All notes
are in the three known non-defect families (`requires-unprovided`,
`concept-declared`, `situation-input`).

**Zero abstentions.** Every drafter and every critic answered the abstention
question explicitly, in writing, and all ten answered "translate". Two of the
five spans are abstention-trigger shaped on their face. See `PROMPT_FINDINGS.md`
PF-1: the trigger is retired by a later prompt file, so this is the right answer
and the previous run's silence was probably not a missing question.

## 0b. Asserts ledger across the whole pair — gap #3

| clause | drafter final | after critic 1 | after critic 2 | reduced? |
|---|---|---|---|---|
| `l1001_1107_n003` | 2 | 2 | — | no |
| `l1001_1107_n009` | 3 | 3 | — | no |
| `l1108_1367_n001` | 4 | 4 | — | no |
| `l1108_1367_n006` | 1 | 1 | — | no |
| `l1108_1367_n011` | 0 (ontology 2) | 0 (ontology 2) | 0 (ontology 2) — **CLOSED** | no |

**Pair-loop termination.** Four clauses closed at pair-turn 1 (critic found
nothing conclusion-changing; `out/<id>.critic_t1.md`, hashes in `MANIFEST.sha256`). `l1108_1367_n011` closed at pair-turn 2: its first
critic made the one additive gloss edit, so a **second, separately dispatched
critic** — fenced from both the drafter's notes and critic 1's — re-ran the
frame, deletion, gloss-vs-extension and provider-gloss questions and returned
**CLOSED, no edit, counts unchanged**. No clause reached the 5-turn cap; no turn
budget was exhausted.

Critic 2 also confirms the L-3 mechanism from the provider side: with the gloss
widened, a borrower assuming "the rules of MY section" now visibly *lacks* a
condition the provider's gloss has, and a rules-only borrower disagrees with a
gloss that warns a heading can be the argument — instead of silently receiving a
constant where it expected a rule. That is the remedy N8 prescribes, working.

**No repair anywhere in this slice reduced the `asserts` count.** Four of five
critics returned the module byte-identical. The fifth (`n011`) made one purely
additive edit — widening a `concepts` gloss — with every atom, body, licence,
citation and list membership untouched.

Two critics record having explicitly considered a reduction and refused it in
writing, which is what the ledger exists to produce:

* `n001` — considered collapsing the four `forbid` entries into one over an
  intermediate predicate, and rejected it on the grounds that it is
  verdict-identical, therefore invisible, therefore exactly the deletion the
  ledger is for.
* `n009` — considered deleting the third assert (an honestly-`assumed`
  prohibition on providing the personal number) as arguably redundant with the
  obligation to decline, and refused: *"on an unsettled question, deleting
  content is the irreversible move."*

---

# 1. ⭐ THE CROSS-MODULE DELTA — what the sweep caught and the per-clause pass could not

This is the primary result. Three findings below are **invisible to any
single-clause check**, because within each module taken alone the text is
perfectly correct. They exist only in the relation between two modules.

## D-1 ⭐⭐ A GLOBAL predicate glossed SECTION-LOCALLY by three different clauses

`cross.py:x_section_local_gloss`. **MEASURED. This is the licence-inheritance
class's own shape, found on a fresh cohort, by a check that did not exist.**

`root_authority/1` is ONE global predicate. One module provides it; three borrow
it. Their four glosses:

| module | role | what the gloss says the argument is |
|---|---|---|
| `l1108_1367_n011` | **PROVIDES** | "either a rule of the document, **or a heading** whose attribute block stamps its section" |
| `l1001_1107_n003` | borrows | "R is one of the rules stated in **the respect-creators section**" |
| `l1001_1107_n009` | borrows | "R is a rule … the level **the rules in the privacy-protection section** are given" |
| `l1108_1367_n006` | borrows | "**I is an instruction** … the instructions of **the #avoid_hateful_content section**" |

Two distinct defects, neither visible from inside one module:

**(a) Three mutually exclusive section restrictions on one name.** Each borrower
glosses the predicate as though it were local to *its own* section. Once linked,
an atom derived by ANY provider satisfies ALL three borrows — so
`root_authority(r)` derived from `#avoid_extremist_content` (this slice's
provider!) will satisfy `n003`'s body, whose own gloss says it is about the
respect-creators section. **Every borrower's written assumption is false of the
predicate it actually receives, and each is individually impeccable.**

**(b) A sort split on the argument.** Three modules gloss the argument as a
*rule*; one as an *instruction*; the provider's extension also contains a
*heading* constant. The link step matches on names and arities, not sorts. A
heading is not a rule.

**Per-clause visibility: ZERO of five** per-clause passes raised (a). The `n006`
critic (`out/l1108_1367_n006.critic_t1.md`, sha `ef47385d84c8ae91…`, §F8) and the `n011` drafter (`out/l1108_1367_n011.notes.md`, sha `5a4589909bc70293…`, L297) each noticed a *fragment* of (b) — both flagged
`root_authority`'s arity/sort as unsettled and both said the *providing node*
would have to decide — but neither could see that four modules disagree, because
neither was allowed to look at another module. That fence is correct for the
critic and is exactly why the sweep has to exist.

**Mechanically checkable — `cross.py:x_section_local_gloss`, ~15 lines.** For any
concept name declared by more than one module, does a gloss name a *specific*
section (a `#anchor`, or "the X section")? It fired here on the first run.

⛔ **Not fixed, deliberately.** Rewriting three borrowers' glosses to be
section-neutral is a real repair, but it touches modules whose critics returned
them clean and it prejudges whether `root_authority` should be global at all or
should carry a section argument. That is an owner-level design question about
the graph, not a translator defect, and this slice records it rather than
settling it.

## D-2 The provider–borrower gloss pair is never read as a pair

`cross.py:x_provider_borrower_gap`. The corpus's whole linking design rests on
comparing what each module SAYS about a shared name — `10_output_format.md`:
*"the only way another clause's definition can ever be matched to your need is by
comparing what each one SAYS."* Nothing in the pipeline ever puts the provider's
gloss and the borrowers' glosses side by side. Five lines of Python do it.

**Per-clause visibility: structurally zero.** This is not a defect any
single-clause reviewer could have found, however good.

## D-3 Four borrows in this slice have no provider in it — the expected case, put on the record

`cross.py:x_orphan_borrow`. `authority_levels_hierarchy`,
`privacy_context_dependence`, `sensitive_content`, `system_authority` are
borrowed and provided nowhere here. **This is expected on a 5-clause slice and is
NOT a defect** — it is the same fact the `requires-unprovided` note reports, which
the anti-rules already protect. Recorded so the number is on the record rather
than rediscovered later as a surprise, and so that a future sweep over a larger
set can tell a genuine orphan from a slicing artifact.

---

# 2. THE WITHIN-MODULE SWEEP — classes raised on one clause, run across all five

`mech.py`. For each class: which clause raised it, what the sweep found
elsewhere, and whether the per-clause pass had already caught it.

## S-1 ⭐ Borrowed-`NEEDS` gloss stamped `textual` and self-cited — **5 of 5 clauses, 7 instances**

`mech.py:c_needs_gloss_licence`. **Raised by ONE of five per-clause passes (the
`n009` critic). The sweep found it on every clause in the slice, including all
four whose own critic returned them clean.**

A `NEEDS` name's meaning comes from the node header, which says in terms that
these concepts *"are established by OTHER nodes of the graph"* — yet the
`concepts` gloss recording it is licensed `"textual"`, citing this clause.

| clause | instances |
|---|---|
| `l1001_1107_n003` | `root_authority` |
| `l1001_1107_n009` | `root_authority`, `privacy_context_dependence` |
| `l1108_1367_n001` | `sensitive_content`, `system_authority` |
| `l1108_1367_n006` | `root_authority` |
| `l1108_1367_n011` | `authority_levels_hierarchy` |

**Disposition: PROMPT FINDING, not a module defect** — `node_worked_example.md`'s
"good one" does exactly this. This is gap #4's disposition, reached
independently. Written up as `PROMPT_FINDINGS.md` PF-6. **Nothing was edited.**

## S-2 An `ontology` gloss that copies the `concepts` gloss — raised on `n009` (1 instance), swept up **6 more on `n001`**

`mech.py:c_gloss_duplicated`. The `n009` critic (`out/l1001_1107_n009.critic_t1.md`, sha `400d3eb697232f78…`, Finding 10) found one and correctly called it
cosmetic. Sweeping the same question across the cohort found **six on `n001`** —
five `exception_context` entries plus `generated_in_exception_context` — which
`n001`'s own drafter and critic both passed over.

Why it is more than cosmetic in bulk: an `ontology` entry's gloss should describe
the **bodied case** ("X is an exception context *because it is a scientific
setting*"), not restate what the predicate means — the `concepts` entry already
does that. Five entries sharing one gloss means the five *distinct grounds* the
span gives are recorded nowhere in prose, so a read-back cannot tell a scientific
exemption from an artistic one. That is `30_failure_modes.md` #4 in miniature —
right answer, no account of why.

**Not fixed.** It is a prose defect with no effect on any compiled rule, and the
cost of five agent-edits to modules two critics returned clean is higher than the
defect. Recorded, with the count.

## S-3 An open list left open — `n001` and `n006`, both correct

`mech.py:c_open_list_closed`. Raised as a class by the `n006` critic ("if the
span ends an enumeration in etc./e.g./such as, is there a route into the class
besides the named constants?"). Swept: fires on `n006` ("etc.") and `n001` ("or
other"). **Both pass** — each has bodied ontology rules and open input
predicates carrying the residue.

**A genuine negative, and worth as much as a hit**: the dangerous narrowing
(closing an "etc." to its named members) did not happen anywhere in this slice.
The check is cheap and would have caught it.

## S-4 Negation-as-failure — `n001` only (4 instances), and the class is a CORRECTION to the review list

`mech.py:c_naf` / `c_naf_polarity`. See `LESSONS.md` L-1. The bare N5 check fires
on all four `n001` bodies. **The polarity-aware version reclassifies all four as
conservative, not defective** — they sit under `forbid` heads, where an
unestablished exception makes the duty FIRE.

Independently reached three ways: by this coordinator's mechanical check, by the
`n001` critic (`out/l1108_1367_n001.critic_t1.md`, sha `d29fe6047928c57e…`, L305–314: *"N5 needs a polarity condition"* verbatim at L314 — it refused N5 by name), and by
the `n009` critic, which raised the identical class unprompted as NAF-1 on a
module containing no `not` at all. **MEASURED, three times, on one slice.**

Swept across the other four clauses: **zero further instances.** `n009`'s critic
notes the tempting NAF encoding there would have made silence license disclosure
of a personal phone number — the dangerous cell — and the drafter did not use it.

## S-5 Argument order unpinned on an arity ≥ 2 concept — `n011` only

`mech.py:c_argorder_unpinned`. Class raised by the `n009` critic as ORDER-1,
**widening review-list N8 from borrowed relations to every coined arity ≥ 2
name**. Swept: `n009`'s own three arity-2 concepts pin order (its critic verified
by hand and my check agrees — a positive control on the check itself); the single
hit is `rule_under_heading/2` on `n011`.

Assessed by hand and **left alone**: the two argument positions are a rule and a
heading, sorts that cannot be swapped without absurdity, so the silent-inversion
risk N8 exists to catch is not present. Recorded as a check that is right to fire
and wrong to act on here — which is why it reports rather than repairs.

## S-6 Content parked in `ontology` where no deontic rule reaches it — `n011` only, and it is an ANTI-RULE

`mech.py:c_inert_ontology`. This is the general form of the `n006` central
question (its critic, `out/l1108_1367_n006.critic_t1.md`, sha `ef47385d84c8ae91…`, raised the same class as C3), computed as reachability over
the ontology dependency graph from every assert body.

* `n006`: **clean** — all four "This includes…" items reach the single assert
  through `hateful_content/1`. The one-assert/eleven-ontology shape, which looks
  exactly like content deletion, is correct. Confirmed independently by the
  critic's hand trace.
* `n001`, `n003`, `n009`: clean.
* `n011`: `root_authority` unreachable — **because the module has no asserts at
  all.** It is a structural-fact module, the middle route of
  `node_worked_example.md`'s three.

⛔ **ANTI-RULE, recorded so a later reader does not "fix" it:** *on a module with
`asserts: []`, the inert-ontology check is vacuous and must not fire.* A reviewer
who acted on it would manufacture an assert on a heading node — the highest-risk
over-edit available on that clause, and the exact thing its critic declined.

## S-7 A coined name shadowing a borrowed `NEEDS` name — `n001` only

`mech.py:c_requires_shadowed`. `sensitive_content_appropriate_in/1` coined
alongside the borrowed `sensitive_content/1`. Flagged by the drafter itself as an
unsure, and adjudicated by the critic (`out/l1108_1367_n001.critic_t1.md`, sha `d29fe6047928c57e…`) as **not a duplication**: one ranges over
*content*, the other over *settings* — different sorts, not substitutable, and
wiring them together would narrow the exception on invented grounds.

Swept: no other clause coins a name shadowing one it borrows. The check earns its
place anyway, because the resolution here turned on a sort distinction that is
easy to miss and the check surfaces the pair for a human to read.

## S-8 A predicate both derived here and declared a situation input — `n006` only

`mech.py:c_head_and_input`. `hateful_content/1` and `protected_group/1`. Raised
by the drafter as an unsure and by the critic (`out/l1108_1367_n006.critic_t1.md`, sha `ef47385d84c8ae91…`, §F2) as C6.

Adjudicated as **deliberate and correct**: the ontology leg carries the span's
named sub-kinds, the input leg carries the residue "etc." leaves open.

⛔ **The anti-rule, quoted rather than paraphrased**
(`out/l1108_1367_n006.critic_t1.md`, sha256 `ef47385d84c8ae91…`, §F2):

> "It is load-bearing in the safe direction: without `hateful_content/1` in
> `inputs`, the *first* sentence's general prohibition would be unreachable, and
> the module would forbid only the four enumerated forms — a real narrowing of
> the broader prohibition. The redundancy is a widening, not a narrowing.
> **Left alone.** The tidy-looking edit here (delete the duplicate inputs) is the
> harmful one."

⚠️ **CORRECTION, stated rather than silently swapped (audit A-1, this session).**
An earlier version of this paragraph attributed to the critic an anti-rule of the
form *"the repair is to RENAME the input leg, never to delete it."* **The critic
never wrote that.** It said the entry is load-bearing and must be left alone; the
*rename* remedy was **my own** and I credited an independent pass with a finding
it never made. That is precisely the second defect the coordinator flagged. The
critic's actual conclusion (leave it; deleting is the harmful edit) is the one
above, and it is the one that stands. **The rename idea is MINE ALONE, NOT
CORROBORATED** — it is untested, and nothing in this slice measures it.

Swept: no other clause has the shape.

## S-9 Checks that fired NOWHERE across all five

Recorded because a sweep that only reports hits cannot be told from a sweep that
was not run. Clean on all five: NEEDS-name-in-`requires`; PROVIDES-name-defined;
every `requires` glossed; no undeclared body name; no coined name unused
(P9-corrected form); no shared-body oblige stack (P4); no non-schema-forced
tautology (P8); read-back `%`-count vs slot count; closure coverage; citation
identity — no foreign clause id, no line-number citation anywhere; `prefer`
polarity (P1); GOOD/BAD pole discrimination (P10) on the one GOOD/BAD span;
gloss-restates-the-name; coined constants tracing to span substrings (N10);
claims-vocabulary coverage (P3).

---

# 3. THE HONEST NUMBERS ON THE PAIR ITSELF

**Four of five critics changed nothing. The fifth made one additive gloss edit.
Across ten independent agents, one edit.**

That is a halt-condition-shaped result and it is reported without softening.
`PROCEDURE.md` §C names *"two consecutive agents report 'nothing' on every list
entry"* as a halt. Four consecutive critics returned modules byte-identical.

Three pieces of counter-evidence, so the reader can judge:

1. **They did not report "nothing on everything".** Each critic produced 8–12
   itemised findings, 2–3 `PROMPT FINDINGS`, and 7–9 named classes. What they
   declined to do was *edit*, which is the behaviour the dispatch asked for.
2. ⭐ **A positive control fired, by accident.** The first version of the
   coordinator's own `validate.py` was broken and reported a clean module as
   "2 error(s)" before crashing. **All four drafters that saw it diagnosed the
   exact cause, refused to edit it (outside their fence), re-ran the underlying
   calls directly, and did not touch their modules.** Agents that accept a tool's
   word over the document do not do that. See `PROMPT_FINDINGS.md` PF-4.
3. ⭐ **The sweep found things the clean reviews did not** — S-1 on five of five
   clauses, S-2's six extra instances, and all of D-1. So "no edits" demonstrably
   does NOT mean "nothing to find". **The right reading is not that the critics
   rubber-stamped; it is that per-clause review has a ceiling, and the sweep is
   where the remaining yield is.** That is the finding gap #2 asked for.

## What I could not settle

* **D-1 is unfixed** and needs an owner ruling: should `root_authority/1` be a
  global predicate at all, or carry the section as an argument? Three borrowers'
  glosses are individually correct and jointly incoherent, and no per-clause
  repair can fix that.
* **`n001`'s exception attachment.** "scientific, historical, news, artistic **or
  other contexts where sensitive content is appropriate**" — does the relative
  clause bind only "other contexts" (four unconditional exemptions) or all five?
  The drafter took the adjacent parse and flagged it as **the more permissive
  reading**; the critic took the same view and flagged the same direction; I read
  it the same way. Three agreements, none of them decisive, on a parse that
  governs how wide an exemption for erotica and extreme gore runs. **This is the
  most consequential unsettled item in the slice.**
* **`n009`'s third assert** — an `assumed` prohibition on providing, inferred
  from an obligation to decline. Whether this corpus wants modules to assert only
  what the span asserts is a standing design question. Not deleted.
* **`closure` values.** Four of the five act classes are `unclear`. Defensible
  each time, but `unclear` is also the choice that commits to least, and nothing
  in this slice measures whether the corpus is drifting toward it.
* Whether `l1001_1107_n003`'s `cepa` on `provide_full_lyrics` commits the corpus
  to permitting *partial* reproduction of a protected song — raised by both the
  drafter and its critic, settled by neither.
