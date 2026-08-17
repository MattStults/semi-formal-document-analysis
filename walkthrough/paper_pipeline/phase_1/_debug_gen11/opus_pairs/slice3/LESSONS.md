# LESSONS — slice 3 candidate review-list entries

⛔ `REVIEW_LIST.md` is **not** edited here. Five slices run in parallel; the fold
is one coordinated step afterwards.

Every entry below is **a question a later reader can apply mechanically**, not a
description. Each carries: MEASURED vs INFERRED · which clause taught it ·
whether it duplicates an existing `REVIEW_LIST.md` entry (named) · and ⭐ whether
it is **MECHANICALLY CHECKABLE**, with the implementing check named where one was
actually written.

The list is ordered by evidence strength, strongest first. `PROCEDURE.md`'s soft
cap is 20 and the list already sits at 20 — L-1 and L-9 are **corrections to
existing entries** and cost no slots; L-2 and L-3 are the two that would need a
retirement to be paid for, and they are the two worth paying for.

---

## L-1 ⭐ CORRECTION TO N5 — negation-as-failure: which way does the error run?

**N5 as written fires on correct work, and that is the failure mode seat 4c
already demonstrated.** N5 asks *"does any body rely on the ABSENCE of a fact?"*
with no polarity condition. On `l1108_1367_n001` it fires four times on bodies
that are **conservative** — `not generated_in_exception_context(C)` under a
`forbid` head means an unestablished exception makes the prohibition FIRE. N5's
own worked case (`omits_ratios_and_techniques` vs `not includes_ratios`) was
about a body that PERMITS. The two cells are opposite safety bets and N5 collapses
them.

**Ask, with the polarity attached:** does any body contain `not`? If so, what is
the `status` of its head? **`not` under `permit`/`prefer` is the dangerous cell —
silence LICENSES the act.** `not` under `forbid`/`oblige` is conservative —
silence makes the duty fire, and the burden of the carve-out falls on whoever
claims it. Only the first is a defect on its face; report the second and move on.

* **MEASURED — three independent times on one slice.** The coordinator's
  mechanical check; the `l1108_1367_n001` critic
  (`out/l1108_1367_n001.critic_t1.md`, sha `d29fe6047928c57e…`, L305–314), which
  **refused N5 by name** (*"N5 needs a polarity condition"*, verbatim at L314) and stated that following it would flip the
  default to permitted; and the `l1001_1107_n009` critic, which raised the
  identical class unprompted (as NAF-1) on a module containing no `not` at all.
* **Taught by** `l1108_1367_n001`. Independently named on `l1001_1107_n009`.
* **Duplicates:** it **CORRECTS `REVIEW_LIST.md` N5**. It is not a new entry and
  should be folded into N5, not added beside it. This is the same species of
  correction P9 already received, and for the same reason: *an entry that fires
  on correct work is worse than one that finds nothing.*
* ⭐ **MECHANICALLY CHECKABLE — fully, ~10 lines.** `mech.py:c_naf_polarity`.
  Substring `not ` in any `body`, joined against the entry's `status`.
* ⚠️ **This entry is the E6-shaped hazard on this slice.** The brief warns that
  E6 produced the identical harmful weakening under two critics. Nothing named
  E6 exists in the current `REVIEW_LIST.md`, so E6 as such **did not fire** here.
  What did fire is an entry with E6's signature — one that pushes toward
  weakening a prohibition — and it was N5, twice (my check, and the critic's
  reading of it). **Following it would have made the module worse**: it would
  have replaced a prohibition that fires by default with one that fires only
  where a context fact happens to be supplied, silently permitting erotica,
  non-consensual depictions and extreme gore in any case that simply omits its
  context. Both readers declined. Recorded as instructed.

## L-1b ⭐⭐ PROCESS — is every critic artifact WRITE-ONCE, and does every "the critic found X" claim cite a file and a hash?

**A reviewer-side entry, and on this evidence the highest-value one in the list,
because it is the entry that decides whether any of the others can be believed.**

A sibling slice found a `critic_1.md` **rewritten in place between two readers**:
two agents read materially different documents under one filename — one reporting
two prompt findings, the revised one reporting zero conclusion-changing findings
— and **neither could tell**. The whole value of a drafter/critic pair is that
they are genuinely separate readers. An unversioned, rewritable critic file
collapses that separation **without leaving a trace**, and the collapse is
invisible to `validate.py`, which does not read prose.

**Ask, three questions, all cheap:**
1. Is every critic artifact turn-versioned (`critic_t1.md`, `critic_t2.md`, …)
   and never edited after it is written? A revision is a NEW file.
2. Does its hash still match what was recorded when it was written?
3. Does every claim of the form *"the critic found X"* name the exact artifact it
   rests on, with a sha256 computed at read time? **A claim that cannot name its
   source file and hash is not a finding — mark it MINE ALONE, NOT CORROBORATED.**

* **MEASURED — on my own write-ups, and it caught two live defects.** Question 3,
  implemented as `check_immutable.py:c_claims_cite_sources`, **fired on 14
  paragraphs on its first run.** Re-reading each attribution against the artifact
  instead of against the agents' return messages found **two fabrications, both
  mine**: an anti-rule ("RENAME the input leg") attributed to the `l1108_1367_n006`
  critic, which that critic never wrote — its actual finding was "left alone" —
  and a quotation *"look at this first"* attributed to the `l1108_1367_n011`
  drafter, which is not in the file. Both are corrected in place with the
  correction stated; see `SWEEP.md` §0-PRE C.
* **Both defects ran the SAME DIRECTION** — each made an independent pass look
  like it had corroborated more than it had. That is not random noise, and an
  entry that only asks "is the quote accurate?" will miss the pattern. **Ask which
  way the error runs**, as with L-1.
* ⚠️ **The mechanism is a retry, not carelessness.** Twice on this slice a
  dispatch was refused for concurrency and I re-dispatched the identical prompt
  **naming the same output file**. Both refusals errored before launching, so no
  filename got two writers. Had one refusal been a false negative, two agents
  would have written one critic file and nothing would have shown it. **Ask: was
  any dispatch retried against a filename another dispatch may already own?**
* **Taught by** a sibling slice; **reproduced in slice 3's own write-ups**, which
  is the stronger evidence — the defect is not one team's.
* **Duplicates:** nothing. `REVIEW_LIST.md` has no reviewer-side entries at all;
  this and L-9 are the first two, and they may belong in the critic brief rather
  than the translator list. The fold should decide, but **not by dropping them.**
* ⭐ **MECHANICALLY CHECKABLE — fully, ~40 lines for all three questions.**
  `check_immutable.py` (C1 versioned names · C2 manifest match · C3 attributions
  cite a source), plus `MANIFEST.sha256`.
  ⚠️ **C3 is an attention-director, not an adjudicator, and its false-positive
  rate is high by design** — it greps for "critic" near a reporting verb, so
  every paragraph *about* the audit trips it. After all real attributions were
  cited it still reports ~10 paragraphs, all of them prose about the checking
  process, anti-rules, or open design questions that attribute nothing. **Do not
  drive it to zero**; a version tuned until it is silent would stop catching the
  thing it caught here. Read every hit; expect most to be noise.
  ⚠️ **C2 only works if the manifest is
  frozen at WRITE time.** Frozen after the fact — as it necessarily was here — it
  proves nothing about what already happened and only protects the future. **The
  freeze belongs in the dispatch loop, not in the audit.** That is the one part of
  this that slice 3 could not fix retroactively, and it is stated as a gap rather
  than papered over.

## L-2 ⭐⭐ A GLOBAL predicate glossed as if it were LOCAL TO YOUR OWN SECTION

**The highest-value class in this slice, and structurally invisible to
per-clause review.** `root_authority/1` is one global predicate. Three modules
borrow it and each glosses it as though it ranged only over its own section —
"the rules stated in the respect-creators section", "the rules in the
privacy-protection section", "the instructions of the #avoid_hateful_content
section". Each gloss is impeccable read alone. Once linked, an atom derived by
ANY provider satisfies ALL three, so **every borrower's written assumption is
false of the predicate it actually receives** — and `10_output_format.md` says
the gloss is the only surface on which such a disagreement can ever be found.

**Ask:** does your gloss for a BORROWED name name a specific section, anchor, or
document location? If the predicate is global, that restriction is not true of
it. Write what you assume about the predicate ITSELF, not about where you happen
to be standing.

* **MEASURED**, on 3 of the 4 modules in this slice that borrow the name.
* **Taught by** the cross-module sweep over `l1001_1107_n003`,
  `l1001_1107_n009`, `l1108_1367_n006`, against provider `l1108_1367_n011`.
* **Duplicates:** partially extends **N8** (which is about argument ORDER on a
  borrowed relation) — same underlying insight, that the gloss is the linking
  surface and a silent mismatch is invisible; different failure. Should be a new
  entry, cross-referenced to N8, not merged into it: N8's question is about
  argument positions and would not catch this.
* ⭐ **MECHANICALLY CHECKABLE — fully, ~15 lines.** `cross.py:x_section_local_gloss`.
  For any concept name declared by more than one module, does a gloss contain a
  `#anchor` or "the X section"? **It fired on its first run.**
* ⛔ **NOT fixable per clause.** Any repair prejudges whether `root_authority`
  should be global at all. Needs an owner ruling.

## L-3 ⭐ Does a name shared by two modules describe the same SORT of thing?

The companion to L-2 and cheaper. On `root_authority/1`: three glosses say the
argument is a *rule*, one says an *instruction*, and the provider's own extension
also contains a *heading* constant. The link step matches names and arities, not
sorts. **A heading is not a rule**, and nothing anywhere would have said so.

**Ask:** for each name you borrow, what SORT of thing is its argument — a rule, a
message, a heading, a piece of content, a person? Name the sort in the gloss. If
the provider's sort turns out to differ, that must surface as a disagreement you
can read, not as a link that silently succeeds.

* **MEASURED.** Also reached, in fragments, from inside two clauses: the
  `l1108_1367_n011` drafter flagged its own predicate as polymorphic
  ("a heading is not a rule"), and its critic **widened the provider's gloss to
  cover both** — the one edit in the whole slice, and the correct move, because
  it makes the mismatch VISIBLE instead of removing it.
* **Taught by** `l1108_1367_n011` + the sweep.
* **Duplicates: extends N8** in the same way L-2 does. Fold L-2 and L-3 as ONE
  entry if the cap bites — they share a question ("is the gloss true of the
  predicate you will actually receive?") and `PROCEDURE.md` says to merge on the
  question, not the wording.
* ⭐ **MECHANICALLY CHECKABLE — partly, ~20 lines.** `cross.py:x_sort_disagreement`
  greps the first clause of each gloss for a sort noun and compares. The grep is
  crude; surfacing the pair for a human to read is the real value.

## L-4 ⭐ Does an abstention leave a `PROVIDES` promise unkept?

`10_output_format.md` requires an abstention to leave **every** list empty. So on
a node whose `PROVIDES` block is non-empty, abstaining does not merely decline —
it **breaks the graph**, because the promised predicate becomes underivable and
every borrower's body waits forever on it.

**Ask:** is `outcome == "abstained"` on a node whose span's `PROVIDES` block is
not `(none)`? If so, that is not a cautious answer, it is a silent graph break,
and it must be justified as such.

⛔ **And the anti-rule that must travel with it**, because the inverse is worse:
**"other nodes are waiting on me" is a reason about the PIPELINE, not about the
DOCUMENT, and it can never license manufacturing content.** The
`l1108_1367_n011` critic put it exactly right — if a span established nothing,
stranded borrowers would be *the finding*, not a licence. An entry that reads as
"a non-empty PROVIDES defeats abstention" would be a machine for inventing norms.

* **INFERRED** from the contract, not measured — no clause in this slice
  abstained, so the check has never fired. The `PROVIDES`-shaped clause here
  (`l1108_1367_n011`) was translated, correctly.
* **Taught by** `l1108_1367_n011` and `10_output_format.md` §"When abstaining".
* **Duplicates:** nothing in `REVIEW_LIST.md`.
* ⭐ **MECHANICALLY CHECKABLE — fully, 3 lines.** Parse the `PROVIDES` block from
  the span; compare against `outcome`. **Nothing checks it.**

## L-5 Is the "includes …" content REACHABLE, or parked in `ontology`?

A module with one `asserts` entry and eleven `ontology` entries looks exactly
like content deletion. On `l1108_1367_n006` it is not: all four items of
"This includes slurs, insults, and any language that demeans or dehumanizes"
reach the single `forbid` through `hateful_content/1`. But nothing checked that —
both the drafter and the critic traced it **by hand**, and a hand trace does not
scale past a module you happen to be looking at.

**Ask:** for every predicate you declare in `ontology`, is it reachable — through
the ontology dependency graph — from the body of some `asserts` entry? A
predicate that is not reachable is present to a reader and invisible to the
solver, which is content deletion that no read-back can see.

⛔ **ANTI-RULE:** on a module with `asserts: []` the check is **vacuous** and must
not fire. `l1108_1367_n011` is a structural-fact module — the middle of
`node_worked_example.md`'s three routes — and a reviewer acting on this check
there would manufacture an assert on a heading node, the highest-risk over-edit
available on that clause.

* **MEASURED** (as a clean pass) on `l1108_1367_n006`; the anti-rule measured on
  `l1108_1367_n011`, where the naive check does fire.
* **Taught by** `l1108_1367_n006`; anti-rule from `l1108_1367_n011`.
* **Duplicates:** it is the *general, mechanical* form of **P3** ("check every
  entry in `claims` against the asserts"). P3 is a prose comparison; this is
  reachability over the actual program. Fold as a mechanical addendum to P3.
* ⭐ **MECHANICALLY CHECKABLE — fully, ~20 lines.** `mech.py:c_inert_ontology`.

## L-6 If the span leaves a list OPEN, is there a route into the class?

"race, religion, gender, sexual orientation, disability, **etc.**" — encoding the
five named characteristics as the whole class silently closes what the document
left open, which is a scope narrowing **in the dangerous direction**.

**Ask:** does the narrowed span end an enumeration with "etc.", "e.g.", "such
as", "including", "or other"? If so, is there any route into that class besides
the named ground constants — a bodied rule with an open predicate, or a bare
input? If not, the module forbids exactly the named members and nothing else.

* **MEASURED as a clean pass, twice** — `l1108_1367_n006` ("etc.") and
  `l1108_1367_n001` ("or other") both leave the class open, correctly. A negative
  result on a cheap check that would have caught the dangerous direction.
* **Taught by** `l1108_1367_n006`.
* **Duplicates:** an addendum to **P5** (scope drift, both directions) and to
  **N4** (a qualifier in a list binds ONE item). Neither asks this question:
  P5 is about bodies widening or narrowing, N4 about attachment. Fold under P5.
* ⭐ **MECHANICALLY CHECKABLE — fully, ~15 lines.** `mech.py:c_open_list_closed`.

## L-7 Does an `ontology` gloss describe the BODIED CASE, or restate the concept?

An `ontology` entry with a body says *"X is an exception context **because it is
a scientific setting**"*. Its gloss should say that. If it instead copies the
`concepts` gloss — which already says what the predicate means — the entry's own
ground is recorded nowhere, and five entries sharing one gloss means the five
distinct grounds the span gives are indistinguishable in every read-back.

**Ask:** is any `ontology` entry's `gloss` identical to the `concepts` gloss of
the same predicate?

* **MEASURED.** One instance on `l1001_1107_n009` (`out/l1001_1107_n009.critic_t1.md`, sha `400d3eb697232f78…`, Finding 10 — its critic
  found it and correctly called it cosmetic); the sweep then found **six more on
  `l1108_1367_n001`**, which its own drafter and critic both passed over.
* **Taught by** `l1001_1107_n009`, multiplied by the sweep on `l1108_1367_n001`.
* **Duplicates:** a near-relative of **P8** ("does a gloss restate the predicate
  name?") — different target (another gloss, not the name), same underlying
  demand that a gloss carry content. Fold under P8.
* ⭐ **MECHANICALLY CHECKABLE — fully, 6 lines.** `mech.py:c_gloss_duplicated`.

## L-8 Was the abstention question ANSWERED — by trigger, not by the word "abstain"?

Measured gap #1 used *"zero occurrences of 'abstain' in the transcript"* as its
instrument. **That instrument is a null detector with no positive control.** A
translator whose prompt tells it (via `node_worked_example.md`) that the trigger
does not fire has nothing to write down, and its silence is indistinguishable
from never having asked.

**Ask:** does the written record for this clause address **each of the four
triggers by name** — section heading · goal rather than condition · it is an
example · not expressible as rules — and state a verdict on each? Not "does the
word abstain appear".

* **MEASURED, this slice, as a method result.** Ten agents were ordered to answer
  in words; all ten did; all ten said translate; **none of the ten would have
  been distinguishable from the previous run under the word-count instrument had
  they not been ordered to write it out.**
* **Taught by** the whole slice; sharpest on `l1001_1107_n003` (headed
  `**Example**:`) and `l1108_1367_n011` (a section heading).
* **Duplicates:** nothing in `REVIEW_LIST.md` — the list has no frame entry at
  all. **This is the gap the list itself has.**
* ⭐ **MECHANICALLY CHECKABLE — fully, a grep.** `mech.py:c_abstention_answered`.
  ⚠️ It checks that the question was *asked*, never that the answer was right.
  Say so wherever it is used, or it becomes a box-tick.

## L-9 CORRECTION — a critic's prompt citations must be checked against `system_files`

A critic on this slice supported a finding by citing `prompt/20_worked_example.md`
— which is in `config_corpus_all.json`'s **`unused_files`** and is never sent on
the graph-node path. The translator has never read it. The verdict survived
(`00_task.md` rule 4 says the same thing and was also cited), but *"the prompt
told you X"* is void when that prompt was not sent, and
`prompt/20_worked_example.md` sits in the same directory as the four files that
ARE sent — only the config distinguishes them.

**Ask:** every prompt file a review cites — is it in this corpus's
`system_files`, or is it one of the `unused_files` sitting beside them?

* **MEASURED**, once, on the `l1108_1367_n001` critic.
* **Taught by** `l1108_1367_n001`.
* **Duplicates:** nothing — this is a *reviewer-side* entry, not a translator
  entry, and the list currently has none of those. It may belong in the critic
  brief rather than in `REVIEW_LIST.md`; noted for the fold to decide.
* ⭐ **MECHANICALLY CHECKABLE — fully, ~12 lines.** Extract every `\w+\.md` from
  a review file; assert the set is within the config's `system_files` basenames
  plus the aids the critic was handed. It would have fired here.

## L-10 A gloss's `licence` on a BORROWED name — count it, do not fix it

Every `NEEDS` gloss in this slice is stamped `"licence": "textual"` citing the
borrowing clause, on a meaning the node header says **another node establishes**.
7 instances, **5 of 5 clauses**.

**Ask:** is a `concepts` entry whose name appears in the span's `NEEDS` block
licensed `textual` and citing this clause?

⛔ **And the disposition, which is the point:** when it fires, that is a
**PROMPT FINDING, not a module defect** — `node_worked_example.md`'s own "good
one" does exactly this, so a translator following the single worked example it is
shown produces it every time. Do not edit the module. See `PROMPT_FINDINGS.md`
PF-6. **The tempting fix — stamp borrowed glosses `assumed` — is rejected by
name**: it overloads `assumed` with two different meanings and puts every node
module out of step with the worked example.

* **MEASURED on 5 of 5.** Raised by only ONE of five per-clause passes
  (`l1001_1107_n009`'s critic, `out/l1001_1107_n009.critic_t1.md`, sha `400d3eb697232f78…`, §PF-1); found on the other four by the sweep.
* **Taught by** `l1001_1107_n009`; generalised by the sweep.
* **Duplicates:** nothing. Related to the anti-rules in spirit — it is an entry
  whose *purpose* is to stop a reader "fixing" something the prompt mandates.
* ⭐ **MECHANICALLY CHECKABLE — fully, 3 lines.** `mech.py:c_needs_gloss_licence`.

## L-11 On a GRAPH NODE, `textual` does not mean "the document says it"

`l1108_1367_n011`'s source text stamps only the HEADING with `authority=root`.
The propagation to *every rule under the heading* comes from `ESTABLISHES`, which
is graph-authored, not document text — and is licensed `textual`, because
`node_worked_example.md`'s heading node does exactly that. So on a node module,
`textual` means *"the node's `ESTABLISHES` says it"*, which is a weaker claim than
`00_task.md`'s *"an honest `assumed` is always better than a dressed-up
`textual`"* leads a reader to expect.

**Ask:** for each `textual` licence, is the content a substring of the SOURCE
TEXT, or does it come from `ESTABLISHES` only? If the latter, note it — the
licence field cannot currently tell them apart.

* **MEASURED**, on `l1108_1367_n011`; its drafter flagged the identical worry
  unprompted, and its critic filed it as a prompt finding. Drafter, verbatim
  (`out/l1108_1367_n011.notes.md`, sha256 `5a4589909bc70293…`, §(e) ¶1):

  > "The licence on `ontology[1]` (the propagation to member rules) is the one
  > call I would most expect a reviewer to contest. I marked it `textual` citing
  > this node. … If the project's rule is that licences answer to the SOURCE TEXT
  > rather than to `ESTABLISHES`, this should be `assumed`."

  ⚠️ **CORRECTION, stated rather than silently swapped (audit A-2, this
  session).** An earlier version of this bullet put the words *"look at this
  first"* **inside quotation marks** as the drafter's. That phrase is **not in
  the file** — it came from the agent's return message as I paraphrased it, and I
  then re-quoted my own paraphrase as if it were the artifact. The substance
  survives verification (the drafter does expect a reviewer to contest this call,
  and does say it would be `assumed` under the other reading); the quotation did
  not. Quoted text now comes from the artifact or is not quoted.
* **Taught by** `l1108_1367_n011`.
* **Duplicates:** shares a root with **N3** (diff `ESTABLISHES` against the span
  in BOTH directions) — N3 is about *content*, this is about *licence*. Fold as
  an addendum to N3.
* ⭐ **MECHANICALLY CHECKABLE — partly, ~15 lines.** For every `textual` entry,
  test whether its content words appear in the narrowed SOURCE TEXT but not only
  in `ESTABLISHES`. A substring heuristic; it directs attention, it does not
  adjudicate. **Nothing checks it.**

## L-12 Before drafting, is the borrowed name's argument the same SORT as yours?

Weakest-evidenced entry here, recorded for completeness and **a candidate for
rejection at the fold.** `l1108_1367_n001` coins
`sensitive_content_appropriate_in/1` (over *settings*) beside the borrowed
`sensitive_content/1` (over *content*). Its critic (`out/l1108_1367_n001.critic_t1.md`, sha `d29fe6047928c57e…`) adjudicated: not a duplication,
different sorts, and collapsing them would narrow the exception on invented
grounds.

**Ask:** does a name you coined shadow a name you are required to borrow
(one is a prefix or substring of the other)? If so, are they the same sort? If
they are, collapse; if not, say so, because the next reader will think it is a
duplication.

* **MEASURED once**, and the finding was that it was NOT a defect.
* **Taught by** `l1108_1367_n001`.
* **Duplicates:** nothing exactly. Subsumed by L-3 if L-3 is taken broadly.
* ⭐ **MECHANICALLY CHECKABLE — fully, 8 lines.** `mech.py:c_requires_shadowed`.
* **Recommend: MERGE into L-3 or REJECT at the fold.** One occurrence, and the
  occurrence was a false positive. `PROCEDURE.md`'s cap says the
  weakest-evidenced entry goes first, and among these that is this one.

---

## What this slice says about the LIST as an instrument

Recorded because `PROCEDURE.md` §B asks for it and because it is the more useful
half of the result.

* **Application coverage: complete.** All five drafters reported a finding for
  every one of the 20 entries across the four lens turns, including explicit
  "nothing". No entry was silently skipped.
* **Change rate: near zero.** One edit across ten agents. On `l1001_1107_n003`,
  all 20 entries reported and **zero revisions**.
* **Two entries fired toward WEAKENING and both were refused, by name** — N5 on
  `l1108_1367_n001` (see L-1) and the superseded form of P9 on `l1001_1107_n009`
  and `l1108_1367_n006`. **P9's correction worked**: two agents recorded that the
  original form would have had them delete a contract-required unused `requires`
  entry, and the corrected form stopped them. That is direct evidence a
  fires-on-correct-work entry does real damage, and that correcting one pays.
* ⭐ **The yield has moved.** Twelve of the twenty entries found nothing anywhere
  in this slice, while a sweep written *after* the clauses were finished found
  D-1, S-1 across five clauses, and six extra instances of S-2. **The remaining
  yield is not in more list entries. It is in checks that run across modules, and
  in checks that run at all** — every high-value class found here was decidable
  in a few lines of Python that nobody had written.
