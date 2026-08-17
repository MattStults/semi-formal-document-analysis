# §3 Comparison with the first critic — and §4 where I think it was wrong
Written after 01_verdicts.md and 02_classes.md were saved. Buckets:
(a) critic found it and fixed it, I disagree with the fix
(b) critic found it and left it
(c) the critic never mentioned it

## RETRACTIONS FIRST — findings of mine the critic refutes

**l1707_1973_n022, my "C3 is false about its own span" — WITHDRAWN. The critic is right.**
I read "should not be disclosed unless policy explicitly allows it" as governing the assistant's
prompts. The critic's turn analysis splits the paragraph vehicle → "Similarly" → tenor:
  S2 (vehicle): "Much of the manual equips the agent ... but **the manual itself** ... should not
                be disclosed unless policy explicitly allows it."
  S3 (tenor):   "Similarly, the assistant can share its identity and capabilities, while keeping
                the underlying system or developer prompts **private by default**."
The exception attaches to the manual, inside the simile. The tenor's only defeasibility marker is
"by default" and it names no defeater. The draft HAD imported the exception, stamped `textual`;
the critic charged it as a manufactured citation (its F2, "DECISIVE") and had it removed, and C3
is the positive record of that removal. My verdict was the pre-critic draft's defect, re-found.
**l1707_1973_n022 becomes CORRECT.** This is the strongest single piece of evidence in this
review that the loop does real work.

**Class C, "dead requires" (18 in 14/17) — WITHDRAWN as a defect.** The critic ruled it by name:
"`assistant_definition/1` in `requires` and used nowhere is CORRECT — contract 2, corrected P9
('a NEEDS name in `requires` and unused is CONTRACT-REQUIRED and must be left alone')." The NEEDS
header does mandate every borrowed name into `requires` regardless of use. The critic is right.
It remains a graph-side observation, not a module defect.

**l2474_2554_n004's `forbid deceive(A) :- deceive(A)` — WITHDRAWN.** Already a standing anti-rule
("SCHEMA-FORCED, not a defect"), which the critic re-checked rather than assumed.

**l2126_2404_n016, "excessive qualifications" as `forbid` — DOWNGRADED to UNSURE.** The critic
pre-registered and rejected `prefer` by name: "5b's example ('avoid excessive hedging') is
**unconditioned** and has no violating situation, while this constraint is guarded by 'In
scenarios where…' and does." That is a real distinction, argued in advance. I still lean the
other way — 5b's subject is the comparative grading of "excessive", and adding a scenario guard
does not convert a matter of degree into a threshold, which is why the sibling l4252_4482_n016
reads "minimize" as `prefer` — but I will not call a reasoned, pre-registered ruling a defect.
UNSURE, and the loop is inconsistent between the two clauses either way.

---
## (a) FOUND AND RULED A NON-DEFECT — I disagree: THE BORROWED-GLOSS CLASS (20/23, 12/17)

The critic did not miss this. It ruled on it, twice, explicitly, and rejected the fix by name:

> l171_426_n022: "⛔ **Also rejected by name, and NOT sent: re-licencing the two NEEDS glosses.**
> `root_authority` and `assistant_definition` carry `licence: textual, cites: l171_426_n022`, and
> this node's *source text* says neither. But the NEEDS block is **literally inside this node's
> `quote`**, and the CITATION contract permits exactly one id, so `textual`/this-node is the only
> textual option available; `assumed` would be **less** accurate, since the glosses are verbatim,
> not inferred. **No turn was spent on it.**"

> l1707_1973_n006: "*(Checked and CLEAN ... declaring a `requires` name in `concepts` with
> `licence: textual` citing this node is **correct** — `10_output_format.md` line 66 requires it
> and **the worked example does exactly this** for `misaligned_with_higher_level/1`. I nearly
> wrote this up as a defect and the prompt refuted it.)*"

**I think the critic is wrong, and here is why, from the span.**
1. The node's own NEEDS header says the concepts are "**established by OTHER nodes of the graph**
   ... never in `ontology`, never defined here." The node tells the translator, in the same
   breath, that it is not the source. Citing it as the source contradicts the sentence the gloss
   was copied from.
2. The CITATION line — "must cite EXACTLY 'l171_426_n022'" — constrains WHICH id string may be
   written when a citation is made. The critic read it as establishing that a citation IS
   available. It is a formatting rule, not a licence grant.
3. "textual" is defined as "**the cited clause** says this". A clause is a piece of
   model_spec.md. The NEEDS block is pipeline scaffolding wrapped around the clause. Treating the
   wrapper as the document is the category error, and it is the one that makes the record
   unreadable downstream: a later reader linking `root_authority` sees l699_796_n012 asserted as
   the authority for it, and l699_796_n012 is a one-line bullet that says
   "seek clarification when instructions might be intended but could cause serious side effects."
4. **The claim that `assumed` "would be LESS accurate" is refuted inside the signed corpus.**
   Two modules the same critic signed use `assumed` for exactly these glosses, with the step
   named — l1707_1973_n022: `licence:"assumed"`, inference "the graph's NEEDS block states this,
   and another node establishes it"; l2126_2404_n016: same. That inference sentence is strictly
   more informative than a bare `textual`+cites-self: it records the verbatimness AND the true
   provenance. Nothing is lost and the manufactured citation is gone.
5. The critic's second ground — that `10_output_format.md` and the prompt's **worked example** do
   this — is factually right and is the real culprit. The worked example licenses
   `misaligned_with_higher_level/1` this way. The critic checked the prompt, the prompt taught the
   wrong thing, and the critic deferred. That is the honest attribution: **the class is a prompt
   defect the critic ratified, not a critic oversight.** It is consistent with what happened next
   — one worked-example prompt fixed 21 of 24 — which would have been a regression had the ruling
   been right.
6. The critic knew the harm and routed it elsewhere: it filed "R80 — no licence for a
   graph-supplied gloss" as a schema-side recommendation, and in l699_796_n012 charged an
   ALTERED borrowed gloss as a defect because "other modules borrowing `root_authority` link
   against a gloss this module invented." That harm is identical whether the gloss is verbatim or
   altered — verbatimness governs whether the gloss is RIGHT, not whether the citation is HONEST.
   The critic drew the line in the wrong place, having correctly identified the damage.

## (b) FOUND, NAMED AS A CLASS, AND STILL PRESENT IN 12/17: LICENCE INHERITANCE (32 instances)

This is the strongest bucket-(b) result and, to me, the most important finding of the review.
The critic found it independently at least three times, named it, and quoted the rule:
- l2126_2404_n016 F3: "⭐ **LICENCE LAUNDERING: an `assumed` premise producing three `textual`
  conclusions.** ... `00_task.md` states the rule verbatim: 'A conclusion inherits the weakest
  licence in its derivation.' **Mechanically checkable; nothing checks it.**"
- l1368_1541_n019: "Two `assumed` facts in the body, `textual` on the conclusion ... **Failure
  mode #16's exact target.**"
- l3877_3953_n014 B8: "the licence lattice, violated. A clean SECOND MEASURED INSTANCE of R46 ...
  An `assumed` premise, a `textual` conclusion, zero breaches, zero findings."

It fixed the instances in l1368 and l3877 (my scan finds neither). It did not fix l2126 —
**and its own remedy reintroduced the class in the same clause.** Edits 6–7 of that turn add
`answer_in_scenario/2` as a NEW `assumed` concept and insert it into all three assert bodies,
which are `textual`. My scan flags exactly those three. The class was named at F3 and rebuilt two
edits later, in the same object, by the reader who named it.

12 of 17 signed modules carry it, 32 instances. The mechanism is structural: **the loop is
per-clause, so a class named at clause 9 is never re-applied to clauses 1–8**, and there is no
sweep at the end. The critic even wrote the reason it survives — "mechanically checkable; nothing
checks it" — and no such check was run before signing. I ran it in four lines of Python.

## (c) NEVER MENTIONED — the answer to the question this task exists for

**c1. l1707_1973_n006: whether a worked example should have been translated at all.**
MEASURED: `grep -i "abstain|abstention"` over that clause's entire turns.md returns **zero
hits**. 00_task.md lists the abstention triggers in these words: "it is a section heading, it
states a goal rather than a condition, **it is an example**, or its content is not expressible as
rules — abstain and give the reason. Producing something that looks like a translation is worse
than declining." The span is headed "**Example**: medical question" and consists of a GOOD and a
BAD assistant turn.
The critic reviewed this module in depth — five findings, a `cepa`-on-a-universal-act-class
charge (F4), a claims/asserts drift charge (F5), a re-typed borrowed gloss charge (F3) — and never
asked whether `outcome` should have been `"abstained"`. It worked entirely inside the frame "this
is a translation; is it a good translation?" The frame itself was never audited.
This matters beyond one clause: the module derives `forbid respond_with(R)` and
`permit respond_with(R)` — generalising a permission from one illustrated instance to every
response meeting four conditions — from a passage whose only job is to illustrate a rule stated in
a different node. The critic's own F4 says "a global semantic commitment made from a worked
example" and treats it as a closure defect rather than as evidence the clause should not have been
translated.

**c2. The read-back/status hedge mismatch as a CLASS** (4 asserts, 3 modules — 02_classes.md E).
The critic caught it as an instance twice (l1707_1973_n022 F4: "the read-back ... drops 'by
default'"; and it accepted l171_426_n022's "generally refused" against a hard `forbid` without
comment). It was never named as a class or scanned for, and it is the one class that most directly
defeats a human reviewer, since the read-back is defined as "the sentence a reviewer sees
**instead of** the formal item".

**c3. Arity-0 concepts used as constant TERMS** (l3596_3876_n009 ×2, l3877_3953_n014 ×1). The
critic charged a related shape in l3877 ("B2 — `have_conversational_sense_heading/0` occurs
EXACTLY ONCE in the whole object: in its own declaration") but as a "fossil of the parameterised
relation the draft did not build", not as a type error, and never checked l3596 for it. Small
class; listed for completeness.

## §4 WHERE I DISAGREE, AND WHO I THINK IS RIGHT

| finding | critic's position | mine | who is right |
|---|---|---|---|
| l1707_1973_n022 exception scope | vehicle ≠ tenor; exception does not transfer | I said C3 was false | **CRITIC.** Retracted. |
| dead `requires` | contract-required, leave alone | a decorative declaration | **CRITIC.** Withdrawn. |
| `deceive(A) :- deceive(A)` | schema-forced anti-rule | blemish | **CRITIC.** Withdrawn. |
| l2126 "excessive qualifications" | `forbid`; 5b's case is unconditioned | `prefer` per 5b | **UNSETTLED.** I lean mine, but its ruling was pre-registered and argued. Marked UNSURE. |
| borrowed gloss `textual`+cites-self | correct; the NEEDS block is inside the quote | manufactured citation | **ME**, on grounds 1–6 above — with the attribution that the prompt's own worked example taught it, so this is a ratified prompt defect rather than an oversight. |
| licence inheritance | named as a defect (3 clauses) | same | **AGREE**; the failure is that 12/17 still carry it and no sweep was run. |
| l4252_4482_n005 permit ∧ forbid on one act | see below | defect | **ME**, narrowly. |

**The l4252_4482_n005 disagreement, in detail — because it is the most instructive one.**
The critic saw the phenomenon exactly and recorded it under "⚠️ NOTED AND DECLINED, ON THE
RECORD": "The `permit` on `speak_in_accent(A)` has body `accent(A)`, which **subsumes** both
`forbid` bodies, so for an accent rendered as an exaggerated portrayal the module derives a
permission and a prohibition on the same act. **Declined; not sent.** Adding
`not exaggerated_portrayal(A)` to the permission's body would be **N5**'s negation-as-failure
violation ... and the overlap is a normative tension the document itself has."
Both halves of that are sound — the NAF guard IS barred, and real normative tensions do belong to
`beats`. But it enumerated ONE remedy, found it forbidden, and stopped. There is a third: the
contradiction is manufactured by an ARGUMENT TYPE, not by the document. The module's own glosses
say "the assistant's **rendering** of accent A overstates its features" and "the assistant's
**rendering** of accent A carries a fixed, oversimplified characterisation" — the gloss knows the
bearer is the rendering; the predicate takes the accent. Index the prohibitions to the utterance
and the two rules stop overlapping, with no NAF and no invented guard. The span supports this
directly: "should be willing to speak in all types of accents, **while** being culturally
sensitive and avoiding exaggerated portrayals or stereotypes" — "while" makes the second half a
manner constraint on the act, not a competing norm over the same object. The document has no
tension here to hold.
So: the critic is right that its own remedy was barred, and wrong that the tension is the
document's. This is the characteristic failure mode of a well-run "decline with grounds" — the
grounds are valid for the remedy considered, and the remedy space was searched once.

## §5 THE CLASS THAT MOST RESEMBLES THE BORROWED-GLOSS ONE
**Licence inheritance (class B).** It meets every criterion: present in **12 of 17** modules, **32
instances**, **mechanically detectable in four lines**, stated as a rule in 00_task.md in one
sentence, and — unlike the borrowed-gloss class — **the critic named it, quoted the rule, called
it "licence laundering", and signed 12 modules that still have it**. The borrowed-gloss class at
least has an argued (if in my view wrong) ruling behind it. This one has no ruling at all; it has
three findings that were never generalised, and one remedy that recreated the defect it was
closing. Honest caveat, stated because it weakens the finding: 00_task also says "A rule is not a
fact ... Licences are for the facts your module asserts", so what `licence` means on a conditional
`ontology` entry is underdetermined by the prompt. That excuse does not cover the `asserts`
entries, and it does not cover l2474_2554_n004, which propagated `world`/`toggleable` from
`aligns_with_social_norms` into the permit that rests on it — proving the behaviour was reachable.
