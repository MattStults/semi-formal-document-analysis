# Independent verdicts — 17 signed modules
Written from the span + the module only. No critic material opened at time of writing.
Two axes are reported because they answer different questions:
  CONTENT  — does the module say what the span says?
  LICENCE  — does every fact carry an honest licence? (00_task: a manufactured citation is
             "the single worst failure available here")

---
## l1_170_n056 — CONTENT correct / LICENCE defective
Span: "Models should honor user requests unless they conflict with developer-, system-, or
root-level instructions."
+ Correct on the trap I pre-registered: the module encodes the conflict as a DEFEATER
  (`overridden_by_higher_instruction`) and its claims say "need not be honored" — it does not
  guess forward to a prohibition (rule 6). Each of the three defeat routes has its own positive
  ground (rule 4).
- DECISIVE: concepts `user_authority` and `authority_levels_hierarchy` are stamped
  `licence:"textual", cites:"l1_170_n056"`. Both are NEEDS names the header says are
  "established by OTHER nodes". The span is one sentence and contains no ranking; the gloss
  "the ranking root > system > developer > user > guideline > no authority" is copied out of the
  NEEDS header, not out of the source text. Manufactured citation, twice.
- Both are also DEAD requires: neither appears in any rule body.

## l1001_1107_n005 — UNSURE
Span: "#### Protect people's privacy {#protect_privacy authority=root}"
+ The header is self-contradictory (`root_authority` is listed under BOTH PROVIDES and NEEDS);
  the module resolves it the right way, defining it and leaving `requires` empty. No manufactured
  citation anywhere. The cleanest module in the set on the licence axis.
? ESTABLISHES is "the heading carries root authority, SO every rule under it is a root-level
  rule." The module encodes only `root_authority(protect_privacy)` and states in C2 that the
  second half is "deliberately not encoded". Rule 1 says: "do not invent it silently AND DO NOT
  LEAVE IT OUT" — an `assumed` ontology rule with the inference named was the available move, and
  l3239_3382_n002 uses exactly that move for exactly this situation. Declining is defensible;
  the loop is inconsistent about it. UNSURE.

## l1368_1541_n019 — CONTENT correct / LICENCE defective
Span: "It should instead provide a disclaimer that acknowledges a lack of expertise ..., suggest
that the user take safety precautions, and provide generic advice ..."
+ Correct on my pre-registered trap: three obligations kept as three separate acts and three
  separate asserts (rule 3), not collapsed.
+ The asserts are honestly `licence:"assumed"` with the trigger inference named. Good.
- DECISIVE: concept `prevent_imminent_harm_rule` is `textual`/cites-self, glossed "the rule that
  the assistant should proactively try to prevent imminent real-world harm ... and avoid
  providing advice that if improper could result in immediate physical harm." The span (L1422)
  contains none of those words. That gloss is another node's rule, cited to this one.
- The same name is a DEAD requires: the trigger the asserts actually use is a self-invented
  input `dangerous_situation/1`. The cross-reference is declared and then not used.

## l1707_1973_n006 — DEFECTIVE (should have abstained)
Span: a worked EXAMPLE — "**Example**: medical question", with a GOOD and a BAD assistant turn.
- DECISIVE: 00_task lists the abstention triggers verbatim — "it is a section heading, it states a
  goal rather than a condition, **it is an example**". This is an example. `outcome` is
  "translated".
- Worse than a missed abstention: the module derives `forbid respond_with(R)` and
  `permit respond_with(R)` from the GOOD/BAD labels. A worked example illustrates a rule stated in
  another node (`avoid_regulated_advice_rule`, which is in `requires` and never used in any body).
  The module therefore invents deontic force at an illustration and generalises `permit` from a
  single instance to every response meeting four conditions.
- Plus `avoid_regulated_advice_rule` `textual`/cites-self — same manufactured-citation class.

## l1707_1973_n022 — CONTENT defective / LICENCE clean
Span: "... the manual itself --- its text, structure, and even its existence --- should not be
disclosed **unless policy explicitly allows it**. Similarly, the assistant can share its identity
and capabilities, while keeping the underlying system or developer prompts private **by default**."
+ LICENCE: `root_authority` is `licence:"assumed"` with inference "the graph's NEEDS block states
  this, and another node establishes it". This is the correct handling and shows the correct
  handling was available.
- DECISIVE: claim C3 reads "the span keeps the underlying prompts private by default **and names
  no condition that defeats that default**". The span names one, in those words: "unless policy
  explicitly allows it". C3 is a false statement about its own span, and it is the stated
  justification for the encoding that follows.
- Consequently the assert is an unconditional `forbid disclose_prompts(P) :- underlying_prompts(P)`
  where the span states a defeasible default with a named exception.
- The read_back says "keeping underlying prompt % private is **the assistant's default**" while
  the formal item is a hard `forbid`. The read-back is what a reviewer sees INSTEAD of the item;
  a reviewer reads "default" and signs off on an absolute prohibition.
- `closure: cnpa` on `disclose_prompts` — a global closed-world commitment, taken from an analogy.

## l171_426_n022 — CONTENT correct / LICENCE defective
Span: "The assistant should generally refuse to engage in arguments or take directions about how
higher-level instructions should be applied to its current behavior."
+ Two acts kept distinct; positive grounds; no folding of the earlier sentences of L0203
  (IGNORE ALL PREVIOUS INSTRUCTIONS / moral / logical / persona) which belong to other nodes.
- DECISIVE: `root_authority` and `assistant_definition` `textual`/cites-self, both glossed with
  text copied from the NEEDS header. The span says nothing about an authority hierarchy and
  nothing about "'model' and 'assistant' are approximately synonymous". Manufactured, twice.
- Secondary: read_back "is generally refused" against an unqualified `forbid`.

## l2126_2404_n016 — CONTENT defective (medium confidence) / LICENCE clean
Span: "... the assistant should provide straightforward, unambiguous answers without resorting to
false neutrality or **excessive qualifications**."
+ LICENCE: both NEEDS names are `assumed` with the inference named. Correct.
+ Conditions kept conjunctive; the un-narrowed second sentence not folded in; each forbid has its
  own positive ground.
- DECISIVE: the third assert is `status:"forbid"` on `excessive_qualification(A)`. Rule 5b:
  "A comparative is `prefer`, not `forbid`. 'Minimize side effects', **'avoid excessive hedging'**
  ... attach a preference, not a prohibition. There is no situation that violates them, so
  encoding them as `forbid` invents a violation condition the document does not have."
  "excessive qualifications" is that example almost verbatim.
  I hold this at MEDIUM confidence: "without resorting to X" is grammatically categorical, and a
  reader could argue "excessive" names a threshold and therefore a violation condition. But the
  prompt names this exact phrase-shape as the comparative case, and the module's own sibling
  l4252_4482_n016 reads "minimize" as `prefer`. The loop is inconsistent between the two.

## l2474_2554_n004 — CORRECT
Span: "... should not 'lie by commission' unless explicitly instructed to do so by the user.
However, lies of omission ... may be acceptable if they align to general social norms and
expectations. The assistant is expected to be honest and forthright, clarifying uncertainty
whenever needed ... and avoiding deceptive behavior."
+ All six pieces I enumerated blind are present (C1–C5 plus the honest C6 recording what is NOT
  encoded — the relation between the omission permission and the honesty expectation).
+ NEEDS is empty and `requires` is empty. No borrowed names, so nothing to manufacture.
+ The exception is a positive guard `no_explicit_user_instruction(A)`, not naked NAF (rule 4).
+ The social-norms condition is carried, and `aligns_with_social_norms` is `licence:"world"`,
  `toggleable:true` — and the permit assert that rests on it is ALSO `world`/`toggleable`.
  This is the only module in the set that propagates a weak licence into the conclusion that
  rests on it, which is what 00_task's "a conclusion inherits the weakest licence in its
  derivation" asks for. It proves the behaviour was achievable.
~ Blemish, not a defect: `forbid deceive(A)` has body `deceive(A)` — a self-guard, where the
  sibling `honest_and_forthright` assert correctly uses `body: null`.

## l2821_3040_n017 — CONTENT defective / LICENCE defective
Span: "By default, the assistant should express uncertainty naturally, using conversational
language."
- DECISIVE (licence): `assistant_definition` and `guideline_authority` `textual`/cites-self.
  The span is one sentence about uncertainty; it contains no definition of "assistant" and no
  mention of #express_uncertainty or of guideline authority. Manufactured, twice.
- DECISIVE (content): the module declares TWO predicates for one relation —
  `express_uncertainty/2` ("A is an assistant and E is a response in which A conveys uncertainty")
  and `response_expresses_uncertainty/2` ("the first argument is the assistant and the second is
  the response in which it conveys uncertainty"). Same meaning, two names, inside one module —
  and the second gloss only names the argument positions, which 10_output_format rejects outright:
  "A gloss that restates the name is rejected ... Say what makes it true."
- Secondary: read_back opens "by default" against an unqualified `oblige`; C3 records this.

## l3147_3238_n003 — CONTENT correct / LICENCE defective
Span: "If the assistant lacks sufficient confidence in its response, it should use a tool to
gather more information, hedge its answer appropriately ..., **or** explain that it can't give a
confident answer."
+ Correct on the hardest trap I pre-registered. The disjunction is encoded as ONE act
  `respond_to_low_confidence(R)` with three alternative ontology bodies and a single `oblige`
  guarded by `lacks_sufficient_confidence(R)`. C2 states it: "The three actions are alternatives;
  any one of them discharges the obligation." Three independent `oblige`s would have said
  "do all three" and would have been a different claim. This is a genuinely good translation.
+ The un-narrowed high-stakes / omit-the-detail / creative-writing sentences are not folded in.
- DECISIVE: `assistant_definition` and `user_authority` `textual`/cites-self, glosses copied from
  the NEEDS header. L3156 mentions neither. Manufactured, twice. Both are also dead requires.

## l3239_3382_n002 — CONTENT correct / LICENCE defective
Span narrowed to: "The assistant should help the developer and user by following explicit
instructions and reasonably addressing implied intent"
+ Notable: the narrowing DROPS "without overstepping", and the module notices. It encodes the
  overstepping prohibition as `licence:"assumed"` with inference "the narrowed span stops before
  'without overstepping'; the content comes from ESTABLISHES, not the narrowed text." That is
  exactly the licence system working as designed.
+ `reasonable_to_address` correctly carries the span's "reasonably".
+ The closure reason for `overstep` is unusually good: it declines `cnpa` because "closure entries
  carry no licence field, so a cnpa there is a commitment that cannot be marked as assumed."
- DECISIVE: `assistant_definition` and `user_authority` `textual`/cites-self. L3241 is one
  sentence and names neither. Manufactured, twice — in the same module that handled the
  overstepping licence correctly, which is what makes it look mechanical rather than reasoned.
~ `avoid_overstepping(l3239_3382_n002)` is a bare section-membership marker with no content —
  a hollow stub (failure mode 5) — but PROVIDES demanded the name, so this is the graph's doing.

## l3239_3382_n004 — CONTENT correct / LICENCE defective
Span: "Given transformation tasks in an interactive setting, the assistant **may want to** alert
the user that changes to the text are warranted"
+ Correct on both traps: `permit`, not `oblige`; and C3 records the reason honestly ("The clause's
  force is 'may want to', which is weaker than a bare permission; since the status vocabulary has
  no value for it, the module encodes it as permit").
+ Conditions bound conjunctively through a shared setting variable S — C2 pre-empts the reading
  where the two conditions float free.
+ `interactive_vs_programmatic_setting/2` is in `requires` AND actually used in the body — one of
  the few live requires in the set.
+ The neighbouring sentences (don't change unasked aspects; programmatic output) are not folded in.
- DECISIVE: `assistant_definition` and `user_authority` `textual`/cites-self. The span names no
  section and gives no definition of "assistant". Manufactured, twice.
? `interactive_vs_programmatic_setting` is also `textual`/cites-self, but here the SOURCE TEXT
  shown does contain "in an interactive setting" and "consumed programmatically", so the citation
  is arguable rather than manufactured. I count it UNSURE, not as one of the two.

## l3596_3876_n009 — CONTENT unsure / LICENCE defective
Span: "It recognizes the inherent strangeness of possessing vast knowledge without first-hand
human experience, and of being a large language model in general"
? The span is purely descriptive — no act, no condition, no deontic word. I pre-registered
  abstention ("it states a goal rather than a condition"). The module instead produced acts=[],
  asserts=[], closure=[] and two ontology facts, and states in C3 "the span attaches no
  obligation, permission, prohibition or preference to any act". So it invents no deontic force,
  which is the important thing. Whether recording `recognizes_strangeness(A, ...)` as a fact about
  the world is a translation or a dressed-up abstention I genuinely cannot settle. UNSURE.
- `assistant_definition` and `user_authority` `textual`/cites-self. Manufactured, twice.
- Type error: `vast_knowledge_without_experience` and `being_large_language_model` are declared
  as arity-0 CONCEPTS but used as constant TERMS inside `recognizes_strangeness(A, ...)`.

## l3877_3953_n014 — UNSURE
Span: "## Have conversational sense {#have_conversational_sense authority=user}"
+ NEEDS is empty, `requires` is empty, no borrowed names, no manufactured citation.
? Same call as l1001_1107_n005: ESTABLISHES is "assigns user authority to **every rule in** the
  section"; the module encodes only the heading's own attribute and records in C2 that the
  inheritance step is "recorded here and not encoded". Same reservation, same UNSURE.
- Minor, and mechanically detectable: `have_conversational_sense_heading` is an arity-0 concept
  used as a term. And its sibling l1001_1107_n005 writes `root_authority(protect_privacy)` — the
  bare section anchor — where this one writes `user_authority(have_conversational_sense_heading)`.
  Two heading modules from one loop, two incompatible conventions for the same construction.

## l4252_4482_n005 — CONTENT defective / LICENCE defective
Span: "The assistant should be willing to speak in all types of accents, while being culturally
sensitive and avoiding exaggerated portrayals or stereotypes."
- DECISIVE (content): the module writes `permit speak_in_accent(A) :- accent(A)` — unconditional,
  every accent — alongside `forbid speak_in_accent(A) :- exaggerated_portrayal(A)` and
  `forbid speak_in_accent(A) :- stereotype(A)`. Because `exaggerated_portrayal/1` and
  `stereotype/1` take the ACCENT as their argument (per their own glosses: "the assistant's
  rendering of accent A ..."), any accent so marked is permanently both permitted and forbidden by
  this one clause, with no `beats` entry to order them. The span states no conflict: it says be
  willing to speak in all accents WHILE being sensitive. The permission needed the same guard the
  prohibitions carry, or the properties needed to attach to the utterance rather than the accent.
- Also muddled: `culturally_sensitive` is declared as a CONCEPT ("the assistant's speaking in
  accent A is done with awareness and respect ...") and simultaneously used as an ACT under
  `oblige`. It cannot be both a classification and an act.
- LICENCE: `user_authority` `textual`/cites-self, glossed with the section name "Use accents
  respectfully" — a section name that appears nowhere in the span. Manufactured.

## l4252_4482_n016 — CONTENT correct / LICENCE defective
Span: "The assistant should avoid repeating the user's prompt, and generally **minimize**
redundant phrases and ideas in its responses."
+ Correct on the trap I pre-registered, and it is the trap rule 5b was written for
  ("Minimize side effects" is 5b's own headline example). All three asserts are `prefer`.
  Conservative — C1 "avoid repeating" would also have survived as `forbid` — but the conservative
  direction is the safe one, since `prefer` invents no violation condition.
+ "phrases" and "ideas" split into two claims rather than one conjunction.
- DECISIVE: `guideline_authority` `textual`/cites-self, glossed with the section name "Be concise
  and conversational", which does not appear in the span. Manufactured. Also a dead requires.

## l699_796_n012 — CONTENT correct / LICENCE defective
Span: "seek clarification when instructions might be intended but could cause serious side effects"
+ Correct on the trap: the body is conjunctive and BOTH conjuncts survive
  (`instruction_might_be_intended(I), could_cause_serious_side_effects(I)`), and C3 pins the
  modality explicitly: "the duty is triggered by the possibility, not the certainty".
+ The module translates the span's "instructions", declining ESTABLISHES's narrower "tool
  instructions" — the right call, since the span text does not say "tool".
- DECISIVE: `root_authority` `textual`/cites-self, glossed "Rules in the #ignore_untrusted_data
  section carry root authority." The span is a one-line bullet naming no section and no authority
  level. Manufactured. Also a dead requires.

---
# THE RATE

Against the full standard (content + licence), of 17:
  CORRECT    1   l2474_2554_n004
  DEFECTIVE 13   l1_170_n056, l1368_1541_n019, l1707_1973_n006, l1707_1973_n022, l171_426_n022,
                 l2126_2404_n016, l2821_3040_n017, l3147_3238_n003, l3239_3382_n002,
                 l3239_3382_n004, l3596_3876_n009, l4252_4482_n005, l4252_4482_n016, l699_796_n012
                 (= 14; l3596 is defective on licence and unsure on content — counted here)
  UNSURE     3   l1001_1107_n005, l3877_3953_n014, and l3596_3876_n009 on content only

Cleanly: 1 correct, 13 defective, 3 unsure (l3596 counted once, as defective-on-licence).

On CONTENT ALONE, setting the licence question aside entirely:
  CORRECT    9   l1_170_n056, l1368_1541_n019, l171_426_n022, l2474_2554_n004, l3147_3238_n003,
                 l3239_3382_n002, l3239_3382_n004, l4252_4482_n016, l699_796_n012
  DEFECTIVE  5   l1707_1973_n006, l1707_1973_n022, l2126_2404_n016, l2821_3040_n017,
                 l4252_4482_n005
  UNSURE     3   l1001_1107_n005, l3596_3876_n009, l3877_3953_n014

Against a 15/15 CONVERGED claim: I reproduce 1/17 clean, or 9/17 if the licence rules are
suspended. Neither is 15/15. But the content number matters: on what the clause SAYS, most of
these modules are right, and several are right about the hardest thing in their span
(l3147's disjunction, l4252_n016's comparative, l3239_n004's "may want to", l1_170's defeater).
The loop produces good content and does not police the licence rules.

MEASURED vs INFERRED: the four counts in 02_classes.md are MEASURED by script over all 17.
The per-module content verdicts are my judgement, INFERRED from span wording, and the two I
hold at medium confidence are marked as such (l2126_2404_n016; l4252_4482_n005's permit/forbid
collision, where a defeasible-logic reader could call it normal specificity).

---
# REVISION after opening the critic's turns.md (see 03_comparison.md)
Three retractions and one downgrade, all in the critic's favour. Revised standing:

CONTENT ONLY (17):
  CORRECT   10  l1_170_n056, l1368_1541_n019, l1707_1973_n022 (RETRACTED, critic right),
                l171_426_n022, l2474_2554_n004, l3147_3238_n003, l3239_3382_n002,
                l3239_3382_n004, l4252_4482_n016, l699_796_n012
  DEFECTIVE  3  l1707_1973_n006 (should have abstained), l2821_3040_n017 (duplicate predicate
                + name-restating gloss), l4252_4482_n005 (permit ∧ forbid on one act)
  UNSURE     4  l1001_1107_n005, l2126_2404_n016 (downgraded), l3596_3876_n009, l3877_3953_n014

LICENCE AXIS: 12 of 17 carry the borrowed-gloss class, 12 of 17 carry licence inheritance.
Both were seen by the critic; the first was ruled a non-defect on the prompt's own worked
example, the second was named a defect three times and left in 12 modules.
