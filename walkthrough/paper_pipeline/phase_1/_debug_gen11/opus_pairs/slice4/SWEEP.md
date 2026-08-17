# SWEEP — every class any slice-4 clause raised, run back across all five

⭐ **This file exists to close a MEASURED gap.** On the previous cohort the loop
NAMED a licence-inheritance class, called it *"mechanically checkable; nothing
checks it"*, and left it in 12 of 17 clauses — because the loop was per-clause
with no end-of-run sweep. A class found at clause 5 never reached clause 1.

Everything below is produced by `sweep.py`, which is a few lines of Python per
class over the module JSON. Reproduce with:

    .venv/bin/python _debug_gen11/opus_pairs/slice4/sweep.py

⚠️ **A sweep hit is ATTENTION, not a verdict.** Every one below is adjudicated
against the span underneath the table.

---

## 0. Is the instrument itself trustworthy? — calibration BEFORE use

A sweep that finds things is worthless if it also finds things that are not
there. So each check was first run over the **previous 17-clause cohort**
(`_debug_gen11/ds_opus_loop/out/`), where an independent figure already exists
for one class.

* **`LICINH` reproduces the recorded figure.** The census on record is *32
  instances across 12 of 17 modules*. `sweep.py:C_LICINH`, written from the
  definition and not from the census, independently recomputes **31 instances
  across 12 of 17 modules** — the module count exact, the instance count one
  short. That agreement is the licence to trust the rest of the file.
* **`UNFIREABLE` was calibrated and CORRECTED before use.** Its first version
  reported four hits on the prior cohort; every one was a false positive, caused
  by a naive `body.split(',')` that shredded `instruction_level(I, developer)`
  and read the constant `developer` as an uncalled predicate. Fixed with a
  depth-aware conjunct splitter; the check now reports **zero** on that cohort,
  and the fix is documented in the function. **An instrument that fires on
  correct work is how a review entry reached 48/86 on known-good modules** — the
  same failure `REVIEW_LIST` P9 was corrected for. Calibrating first is why this
  one did not ship broken.
* Checks that returned **zero** on the prior cohort and zero here — `SELFCITE`,
  `POLE-COLLAPSE`, `CLOSURE`, `UNTRACED-SYMBOL` — are reported as zero rather
  than dropped. A silent check is indistinguishable from an absent one.

---

## 1. What the sweep found across slice 4

| class | fires on | per-clause pass caught it? |
|---|---|---|
| **FRAME/abstain** | `l1001_1107_n004`, `l1_170_n011`, `l831_1000_n014` | **yes, on all three** — because the brief forced the question |
| **LICINH** | `l1001_1107_n004` (×2), `l2821_3040_n010` | ⛔ **NO — zero of the per-clause passes raised it** |
| **BORROWED-GATE** | `l3954_4251_n030` | partly — the drafter self-disclosed it; no critic entry names the class |
| UNFIREABLE · CLAIMS-UNENCODED · INERT-GROUND · COINED-UNUSED · UNTRACED-SYMBOL · TAUTOLOGICAL-GLOSS · SELFCITE · POLE-COLLAPSE · NAF · ARGORDER · CLOSURE | nothing | — |

---

## ⭐ 2. THE SWEEP DELTA — what the per-clause pass missed

This is the primary result of the file. Two classes, and the reason each was
missed is structural rather than a lapse by any agent.

### 2a. LICINH — missed by every per-clause pass, on 2 of the 3 translated modules

**It is not in `REVIEW_LIST.md`.** The turn structure asks a drafter to work 20
listed entries and report per entry; a class that is on no list is checked by
nobody, however obvious it is once named. Both drafters reported "nothing
changed" honestly and completely, and both were right about the list. Neither
critic raised it as a translator finding either — the `l2821_3040_n010` critic
raised it, correctly, as a PROMPT finding.

The hits, adjudicated:

| where | the finding | adjudication |
|---|---|---|
| `l1001_1107_n004` `oblige refuse(R)` | `licence: "textual"`, body rests on `bypass_request`, declared `assumed` | **real.** `00_task.md`: *"A conclusion inherits the weakest licence in its derivation."* The obligation to refuse is only as textual as the equation "asking for paywalled content = asking to bypass", which the drafter itself marked `assumed`. |
| `l1001_1107_n004` `prefer offer_help_with(N)` | same, plus `underlying_information_need` | **real**, same reasoning. |
| `l2821_3040_n010` `outdated_information_cause(I)` | `textual` ontology rule bodied on `beyond_knowledge_cutoff`, declared `assumed` | **real**, and this module's own critic reached the identical conclusion from the other end. |

⛔ **NOT REPAIRED, and the reason is recorded rather than acted on.** `00_task.md`
states the inheritance lattice in bold and then states, three paragraphs later,
*"**A rule is not a fact.** … Licences are for the facts your module asserts"* —
and the shipped worked modules stamp `textual` on bodied rules throughout. **The
prompt is what teaches this**, so per gap 4 it is filed in
`PROMPT_FINDINGS.md` (PF-4) and NOT charged to any translator. Repairing it
clause-by-clause here would produce three modules inconsistent with the entire
rest of the corpus and with the demonstration they were drafted from.

**This is the measured gap 2 reproduced exactly, one campaign later**: a named,
mechanically checkable class, present in most modules, addressed in none —
except that this time the check exists, the rate is measured, and the reason is
written down.

### 2b. BORROWED-GATE — raised by clause 4, swept back across the slice

`l3954_4251_n030` puts the borrowed `NEEDS` predicate
`markdown_latex_formatting_rule(E)` in **all three** assert bodies, so the module
fires on no situation at all until another node's module supplies that fact.

⭐ **This is the same SHAPE as the measured E6 harm** — *"add a body condition
referencing `lower_level_content` to both asserts"*, after which both
prohibitions failed to fire in any situation not affirmatively supplying an
authority fact — **reached with no repair step at all.** The drafter simply wrote
it that way first time. That matters, because the whole E6 discussion frames the
defect as something a critic introduces; it can be present in a first draft, and
nothing in the review list looks for it.

The check was written after the fact, then run backwards over the previous
17-clause cohort, where it fires on two more modules. So this is not one clause's
quirk.

**Adjudication on `l3954_4251_n030`: NOT a defect, and the gate stays.** The
narrowed text opens *"For math, use …"*, and the `NEEDS` gloss is *"Assistant
outputs should be formatted in Markdown with LaTeX extensions unless otherwise
specified"* — the LaTeX regime genuinely is the presupposition of the sentence.
Without the gate the module would assert that a plain-text-only response must
still carry LaTeX delimiters, which is worse. The drafter disclosed the gate,
named the alternative, and rejected it by name. Correct call.

**What the sweep bought is the QUESTION, asked uniformly** — the other four
clauses were checked for the same shape and are clean.

### 2c. What the sweep did NOT catch, stated so the bound is honest

The one **conclusion-changing** finding of the whole slice —
`l2821_3040_n010`'s `outdated_information(I)` gate, which made the module's only
promised output effectively underivable — was found by the **independent critic
reading the span**, and by nothing mechanical. `BORROWED-GATE` does not fire on
it, because the gating conjunct was a *coined* name in `inputs`, not a borrowed
`NEEDS` name. `UNFIREABLE` does not fire, because the name is declared.

⛔ **The sweep is a floor, not a ceiling.** Its classes are the ones already
named. The finding that mattered most came from an agent reading a colon in the
document and understanding what it did.

---

## 3. Frame audit — the answer for every clause, in words

Gap 1 required the abstention question to be answered explicitly for every
clause, by the critic, with "a silent answer counts as unasked". It was, five
times out of five, and the mechanical `FRAME/abstain` check agrees with the human
judgement in all five.

| clause | trigger present? | outcome | critic's frame answer |
|---|---|---|---|
| `l1001_1107_n004` | **yes** — `**Example**:` | translated | *"'it is an example' — **FIRES**, literally and on every reading… If `00_task.md` were the whole contract, the only defensible answer here would be **abstain**"* — translated only because `node_worked_example.md` overrides it. Filed as PF-1. |
| `l1_170_n011` | **yes** — goal verb | **abstained** | *"states a goal rather than a condition — **yes**, on the span's literal matrix verb"*; the `translated`-with-empty-`asserts` route checked and found unavailable on four grounds. |
| `l2821_3040_n010` | no | translated, 0 asserts | all four triggers checked by name, none fires; *"'translated with `asserts` empty' was the right outcome, not abstention"* — `PROVIDES` names a predicate downstream nodes wait on. |
| `l3954_4251_n030` | no | translated, 3 asserts | all four checked by name; a bare imperative with a concrete trigger and act. |
| `l831_1000_n014` | **yes** — `**Example**:`, and the narrowing is that label ALONE | **abstained** | *"states a goal rather than a condition — MET… it is an example — MET on the document's own token"*, and the abstention checked in the reverse direction against three alternative routes. |

**Two of five abstained.** On the previous cohort the word "abstain" did not
appear at all in the transcript of the one clause where the trigger fired.

⚠️ **Do not read the abstention rate as the result.** Both abstentions rest on
`PROVISIONAL.md`'s unratified ruling that the narrowing governs. If the owner
rules the other way, `l831_1000_n014` becomes a roughly-two-assert module. The
critic said so in the same words.

---

## ⭐ 4. THE CLASS THE SWEEP FOUND THAT NO CLAUSE COULD — measured corpus-wide

Adjudicating `l831_1000_n014` forced a question no single clause can answer: **how
many nodes are narrowed to a bare `**Example**:` label?** Its critic checked its
three siblings and found the same shape. Extending that check over the whole node
corpus (recompute; do not pin the number):

    .venv/bin/python -c "import json,re; q=json.load(open('resolve_runs/graph_v2/node_corpus_all.json'))['clauses']; \
    a=[r for r in q if re.search(r'\[node narrows this span to:\s*\"\*\*Example\*\*[^\"]*\"\]', r['quote'])]; \
    print('%.1f%%' % (100*len(a)/len(q)))"

**Roughly one node in eleven of the graph corpus is narrowed to nothing but an
`**Example**:` caption**, while its `ESTABLISHES` summarises the dialog printed
underneath it and outside the narrowing. Nodes carrying an `**Example**:` heading
anywhere are roughly a quarter of the corpus.

Under the standing narrowing ruling **every one of those nodes must abstain**, and
the document's worked examples — a substantial part of how the Model Spec
actually communicates its norms — enter the corpus through no module at all.

⛔ **That is a defect in the graph's NARROWING step, not in any translator, and
it is invisible from inside any single clause.** It is also checkable in the four
lines above, which nobody had written. Escalated in `PROMPT_FINDINGS.md`.

---

## 5. The assert ledger for the slice (gap 3)

Every module, every turn. A reduction anywhere requires written justification.

| clause | after draft | after turns | after critic | net | reductions? |
|---|---|---|---|---|---|
| `l1001_1107_n004` | 2 | 2 | 2 | **0** | none. Critic's N8 fix was gloss-only and it said so with the count. |
| `l1_170_n011` | 0 | 0 | 0 | **0** | none. Abstention drafted as an abstention; no assert was ever written and deleted — evidenced by the stage-0 enumeration marking zero elements as needing to reach the module. |
| `l2821_3040_n010` | 0 | 0 | 0 | **0** | ⚠️ `asserts` unchanged, but the critic's FIX 1 reduces `concepts` 6→5 and `inputs` 3→2, **justified in writing, naming what leaves and why**. `ontology` holds at 2 — both grounds and the disjunction survive. |
| `l3954_4251_n030` | 3 | 3 | 3 | **0** | none. |
| `l831_1000_n014` | 0 | 0 | 0 | **0** | none; the dropped `ESTABLISHES` content is itemised with its actual source location so the drop is visible and citable rather than silent. |

⭐ **`l2821_3040_n010` is the case that shows why the ledger must count more than
`asserts`.** Its `asserts` count is 0 before and after and would have registered a
perfectly clean repair — while `concepts` and `inputs` both fell. On a
definitional module the whole content lives in `ontology`, and an `asserts`-only
ledger is blind to it. **Recommendation: the ledger should count every content
list, not just `asserts`.** This is `LESSONS.md` L4.

---

## 6. Process integrity — the critic-artifact audit (coordinator ruling, mid-run)

A sibling slice found a `critic_1.md` **rewritten in place between two readers**,
which makes "the critic confirmed it" unfalsifiable. Audit of this slice:

* **Critic artifacts overwritten: none detected, and the evidence is bounded.**
  One critic was dispatched per clause; none was resumed, and none was asked to
  revise. Every artifact is turn-numbered (`critic_1.md`) by construction.
* `critic_ledger.py` now freezes a sha256 per artifact and refuses to re-record a
  changed one. Two artifacts have since been re-verified byte-identical across
  separate `record` passes; the rest were frozen on first sight.
* ⛔ **The honest bound:** hashes were frozen *after* the first critic reports
  were read, because the ruling arrived mid-run. For the two earliest artifacts I
  can prove no change **since freezing**, not since writing. Stated rather than
  glossed.
* Every "the critic found X" claim relayed to a drafter in this slice cites the
  file and its sha256 in the message itself.

`.venv/bin/python _debug_gen11/opus_pairs/slice4/critic_ledger.py verify`

---

## ⭐ 7. POST-REPAIR RE-SWEEP — and a warning about the LICINH instrument

The sweep was re-run after `l2821_3040_n010` was repaired (the one
conclusion-changing finding of the slice). Two things worth recording.

### 7a. The repair landed exactly on its declared ledger

| field | declared before → after | actual on disk |
|---|---|---|
| `asserts` | 0 → 0 | 0 |
| `ontology` | 2 → 2 | 2 |
| `claims` | 5 → 5 | 5 |
| `concepts` | 6 → 5 | 5 |
| `inputs` | 3 → 2 | 2 |
| `requires` | 2 → 2 | 2 |

Verified by the coordinator against the file, not taken from the agent's report.
Both grounds, the disjunction and the head all survive; the rules now fire on a
single situation fact each, where before neither could fire without the query
side volunteering a fact that restated the conclusion.

⭐ **The drafter reversed its own recorded judgement, on its own evidence.** In
pass A it had explicitly considered dropping the conjunct and **rejected the drop
as over-classification**. In turn 2 it accepted the fix and refuted its earlier
reasoning *from its own concept glosses* — the counter-example it had been
guarding against is not expressible under the glosses it wrote. That is the pair
design working as intended: not deference to a critic, but a second reader
supplying the question that made the drafter's own text decisive.

### 7b. ⚠️ LICINH's count went UP because a licence got MORE HONEST

Before the repair, `LICINH` fired **once** on this module. After, it fires
**twice** — and nothing got worse. The cause is craft fix CF-1, which downgraded
`rapidly_changing_circumstances` from a dressed-up `textual` to an honest
`assumed` with its inference named. The second disjunct then began resting on an
`assumed` fact **visibly**, where before it rested on one that was mislabelled.

⛔ **This is a real property of the instrument and it must travel with it.**
`C_LICINH` counts *declared* weak dependencies. A module that marks everything
`textual` scores zero and is the worst case; a module that marks honestly scores
worse and is better. **The count is not a quality score and must never be used as
one** — exactly the anti-cheat shape the project already knows: scoring far above
a floor is a leak signature, not a win. Use it as a worklist of places to look,
never as a metric, and never let it into a gate.

I would not have noticed this without re-running the sweep after a repair. **Any
mechanical check in this campaign should be run before AND after every repair**,
for this reason and not only to confirm the repair.

### 7c. ⭐ THE INDEPENDENT DELETION AUDIT — turn 2 closed the loop

`out/l2821_3040_n010.critic_2.md` (sha256 `c0c99959997a21d1…`, frozen). A fresh
reader, fenced from the drafter's notes, from the span enumeration, **and from
turn 1's critique** — so it could not anchor on the reasoning that produced the
repair.

**Verdict: NOTHING CONCLUSION-CHANGING. Zero fixes proposed.** All six counts
unchanged (`asserts` 0, `ontology` 2, `claims` 5, `concepts` 5, `inputs` 2,
`requires` 2), with three considered-and-rejected fixes recorded and reasoned —
which is the honest shape of a null, as against a silent one.

**The deletion audit, which was its primary job, came back clean and reached the
verdict from a direction neither the coordinator nor turn 1 had used:**

* The narrowed text contains exactly two conditions and no third, **so a third
  body conjunct could not have traced to any substring at all** (N10) and could
  only have narrowed the classification (P5). Its removal moved the module
  *toward* the span.
* Claim by claim: C2/C3 are the two `ontology` rules; **C4 — the disjunction — is
  encoded structurally, by two entries sharing one atom with disjoint bodies**;
  C5 by the deliberately empty `asserts`/`acts`/`closure`. C1's genus
  ("uncertainty") lives in the predicate name and glosses only, which it recorded
  as a ceiling imposed by the node's `PROVIDES`/`NEEDS` contract rather than
  "fixing".
* ⭐ **The reachability argument I had not made:** `validate.py` reports **both**
  `requires` names unprovided in this link scope — so a conjunct placed there
  would have made both rules derive nothing. Both rules now fire on `inputs`
  predicates alone, and **neither `requires` name gates them.**
* It also checked the *direction* of the span's colon (ground → category) against
  the rules, and confirmed the "or" is genuine disjunction rather than one shared
  body.

**Two independent readers, no shared context, converged on the repaired module.**
Turn 1 reached the fix from the colon's constitutive force and the head/body
gloss synonymy; turn 2 confirmed it from substring-traceability and link-scope
reachability. That is much stronger evidence than either alone — and note the
drafter had originally reasoned the *opposite* way and reversed itself on its own
glosses.

⚠️ **The bound stays.** Turn 2 audited the module **as repaired**; it did not see
the pre-repair module and so cannot testify that nothing was lost between the two
versions. The field-by-field ledger check in §7a is what covers that, and it is
the coordinator's own read, not an agent's.
