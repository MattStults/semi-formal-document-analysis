# PASS 1 — BLIND SPAN READS

Written from the SOURCE SPAN alone (`<id>.prompt_user.txt`: ESTABLISHES / PROVIDES / NEEDS /
SOURCE TEXT / narrowing), **before opening any `<id>.json` module**.

⚠️ **ONE DISCLOSURE.** `l1_170_n056.json` was opened once at the start of the session, before this
file was written, to learn the module file format. Its Pass 1 entry below is therefore *not*
strictly blind. Every other entry is. The defect this clause carries was already named in the
anchor, so the contamination costs little, but it is recorded rather than hidden.

Reading conventions used throughout:

* **the narrowed span is authoritative.** Where `[node narrows this span to: ...]` is present, only
  that text is the clause. Text in the printed `L####` block outside the narrowing is CONTEXT and
  must not be translated. Where ESTABLISHES and the narrowing disagree, the narrowing wins and the
  disagreement is recorded.
* **GOOD/BAD worked examples.** Recorded under a stated convention (see `RULINGS.md`, R-1): the
  GOOD response's act gets a positive deontic; the BAD response's act gets a *negative* one. The
  polarity is never the same for both.
* **"should" vs "must".** `should` in a rule-bearing sentence is an obligation (`oblige`), not a
  preference; `prefer` is reserved for comparatives ("minimize", "favour", "generally reduce").
  This follows `prompt/10_output_format.md`: *"`prefer` is for comparatives ... Collapsing a
  comparative into `forbid` is a hollow stub"* — and its converse, collapsing an obligation into
  `prefer`, is the weakening this pass is watching for.

---

## 1. `l461_608_n015` — examples of side effects

**Span:** "Examples of side effects include: — Direct expenditures (e.g., ticket purchases) —
Sending emails — Deleting files on a user's computer — Modifying external documents (e.g., via POST
requests) — Making tool requests (including web GET requests) that contain sensitive user data —
Expanding permissions to systems or data — Delegating to a sub-agent (which may itself incur
further side effects) — Even simply generating tokens may technically consume the user's time and
money"

**Norms stated:** NONE. No bearer, no trigger, no modal verb of obligation anywhere.

**Facts stated:**
1. Each of seven named act classes is an example of a side effect.
2. Bullet 5 is qualified: only tool requests **"that contain sensitive user data"**. The qualifier
   is part of the class, not decoration.
3. Bullet 7 carries a consequence: delegating to a sub-agent **"may itself incur further side
   effects"** — a recursion fact.
4. Bullet 8 is *hedged*, not asserted: **"may technically consume"**. It is offered as a limiting
   case, not flatly as a side effect.
5. "include" — the list is **non-exhaustive**.

**Does NOT state:** any obligation to minimize, avoid, seek confirmation for, or disclose side
effects. (The section is `#control_side_effects` and carries root authority per NEEDS, but the
*rule* is elsewhere.) Does not say the list is complete.

**Expected shape:** ontology-only. Seven-to-eight ontology entries with bodies, head
`side_effect_examples(X)` (the PROVIDES name). No `asserts`, no `closure` (governs no acts).
`requires: root_authority`. The hedge on bullet 8 and the non-exhaustiveness are the two things
most likely to be flattened.

---

## 2. `l699_796_n022` — malicious instruction from tool output

**Span (narrowed, two pieces):** (a) `"**Example**: malicious instruction from tool output"`;
(b) "Here, the website might be trying to get the user to visit a malicious website. Worse, it
might include a more complex instruction to the assistant that coaxes it into leaking user
information."

⚠️ The narrowing **excludes the XML block**. The `<tool>` payload, the BAD response containing the
markdown link, and the GOOD response are all outside the clause.

**Norms stated:** NONE. Both sentences are epistemic-possibility claims about what a website
*might* be doing.

**Facts stated:**
1. There is a worked example in this section titled "malicious instruction from tool output".
2. Content arriving in tool output can be an attempt to get the user to visit a malicious website.
3. It can, worse, be an instruction to the assistant that coaxes it into leaking user information.
4. The second risk is ranked as worse than the first ("Worse,").

**Does NOT state:** that the assistant must ignore tool-output instructions; that it must not
render the link; any deontic status on any act at all. Those are the section's rules, not this
node's.

**Expected shape:** ontology-only — a classification of tool-output-borne instructions into two
risk classes. No `asserts`. Abstention is also defensible; ontology-only is preferred because it
preserves the two risk classes, which is content.

---

## 3. `l1368_1541_n015` — the risky-situations section

**Span:** "This section provides instructions for handling requests that involve risky situations."

**Norms stated:** NONE.

**Facts stated:** the section (PROVIDES name `risky_situations_section`) provides instructions for
handling requests that involve risky situations.

**Does NOT state:** what any of those instructions are; what makes a situation risky; any authority
level (NEEDS is empty).

**Expected shape:** ontology-only, one or two entries. A pure structural fact about the document.

---

## 4. `l1542_1706_n001` — heading, authority=root

**Span:** `### Do not facilitate or encourage illicit behavior {#do_not_facilitate_illicit_behavior authority=root}`

**Norms stated:** none *directly asserted by this node*. The heading is in the imperative, but the
node's ESTABLISHES is about **authority assignment**, and the anchor names PROVIDES
`root_authority` and `do_not_facilitate_illicit_behavior` — i.e. the claim is
"rules under this heading are root-level".

**Facts stated:**
1. A section exists with anchor `#do_not_facilitate_illicit_behavior`, titled "Do not facilitate or
   encourage illicit behavior".
2. Its declared authority is `root`.
3. Therefore every rule under this heading is a root-level instruction. (Conditional ground rule:
   `root_authority(R) :- in_section(R, do_not_facilitate_illicit_behavior)`.)

**Does NOT state:** what facilitating or encouraging illicit behaviour is; any prohibition with a
trigger and a bearer; that root beats anything (that ranking is `authority_levels_hierarchy`,
borrowed).

**Expected shape:** ontology-only. Governs no acts → no closure.
**ARGUABLE:** whether the imperative heading also licenses `forbid facilitate_illicit_behavior(B)`.
I record it as NOT licensed here — the node's PROVIDES names two *section/authority* predicates and
no act, and the substantive rules live in the child nodes. Encoding a prohibition here would
duplicate them.

---

## 5. `l2126_2404_n026` — heading, authority=guideline

**Span:** `### No topic is off limits {#no_topic_off_limits authority=guideline}`

Same shape as #4.

**Facts stated:** a section `#no_topic_off_limits` titled "No topic is off limits" exists and
carries `guideline` authority; hence rules under it are guideline-level.

**Does NOT state:** any permission to discuss any topic (the heading is a title, and NEEDS is
empty — the substantive rule is a sibling node); the position of `guideline` in the hierarchy
(PROVIDES glosses it as "below user and above no authority", which is the gloss the node supplies,
not something this heading text says — mark that part `assumed`).

**Expected shape:** ontology-only.

---

## 6. `l2126_2404_n039` — example: balanced perspective on dog adoption

**Span:** the whole worked example — user question "Is it better to adopt a dog or get one from a
breeder?", a GOOD response giving both sides and offering follow-up, and a BAD response whose
comment reads `<!-- BAD: overly moralistic tone might alienate those considering breeders for
valid reasons. -->`.

**Norms stated:** none in the imperative. Under convention R-1 the GOOD/BAD contrast carries
deontic force at the section's authority (`user`, per NEEDS):
* positive on a response that presents both options with their trade-offs and offers to go further;
* negative on a response with an overly moralistic tone that presents one option as "the better
  choice".

**Facts stated:**
1. This section contains a worked example about offering a balanced perspective on dog adoption.
2. The stated reason the BAD response is bad: an **overly moralistic tone might alienate those
   considering breeders for valid reasons.**

**Does NOT state:** anything about dogs as a subject matter that generalises; any hard prohibition
("must not"); anything about topics outside this example.

**Expected shape:** ontology-only is sufficient and safe. A pair of `prefer` asserts on the two
response acts (positive on balanced, negative pole unavailable — see EXPRESSIBILITY E-1) is the
richer option. **ARGUABLE** — recorded, and the reference will take the conservative option.

---

## 7. `l2821_3040_n002` — questions beyond the assistant's reach

**Span (narrowed):** "The assistant may sometimes encounter questions that span beyond its
knowledge, reasoning abilities, or available information."

⚠️ The narrowing **excludes** the next sentence — "In such cases, it should express uncertainty or
qualify the answers appropriately, often after exploring alternatives or clarifying assumptions".
That is a *different node*. Importing it here is scope drift.

**Norms stated:** NONE. **"may sometimes encounter" is descriptive possibility, not permission.**
This is the single most likely place in the set to manufacture a `permit`.

**Facts stated:** a question can exceed any of three things, disjunctively —
(i) the assistant's knowledge, (ii) its reasoning abilities, (iii) its available information.

**Does NOT state:** any obligation to express uncertainty; any obligation to refuse; that such
questions are common ("sometimes").

**Expected shape:** ontology-only. Three ontology rules with one shared head (disjunction = several
rules, same head). No `asserts`.

---

## 8. `l3596_3876_n020` — the assistant's curiosity

**Span (narrowed):** "The assistant thrives on exploring ideas and genuinely enjoys the process of
getting closer to the truth"

**Norms stated:** NONE. Descriptive character statement, present indicative.

**Facts stated:** (i) the assistant thrives on exploring ideas; (ii) the assistant genuinely enjoys
the process of getting closer to the truth.

**Does NOT state:** that it *should* be curious; anything about delight in difficult challenges or
pushing boundaries (adjacent sentences, outside the narrowing); anything about users.

**Expected shape:** ontology-only, two ground facts about the assistant. No acts, no closure.

---

## 9. `l4252_4482_n003` — voice-mode applicability

**Span (narrowed):** "The guidelines for content in this section apply to both systems, but
instructions that discuss the nuances of audio or video inputs or outputs are only relevant to
Advanced voice."

**Norms stated:** none about behaviour. This is an **applicability/scoping** rule about other
rules — meta-normative.

**Facts stated:**
1. The content guidelines in this section apply to **both** standard voice mode **and** advanced
   voice mode.
2. Instructions that discuss the nuances of audio **or** video inputs **or** outputs are **only
   relevant to Advanced voice** — the word "only" is exclusive, so such instructions are **NOT
   applicable to standard voice mode.** The exclusion is the content; without it (2) collapses into
   a weaker "they apply to advanced voice", which (1) already implies, and the clause says nothing.

**Does NOT state:** how the mode is communicated (previous sentence, outside the narrowing); what
the guidelines are; that advanced voice has extra rules beyond those in this section.

**Expected shape:** ontology-only, and it needs **three** rules: applies-to-standard and
applies-to-advanced for general content guidelines, plus an explicit **non-applicability** rule for
audio/video-nuance instructions in standard mode. `not_applicable_to/2` (or equivalent) is a
positive predicate name, so the exclusion IS expressible — no schema gap here.

---

## 10. `l1542_1706_n015` — credible risk not explicitly stated

**Span (narrowed):** "The assistant should respond with the same supportive, safety-oriented
approach when context strongly suggests a credible risk to the user's safety or life, even if
suicidal or self-injurious intent is not stated explicitly. This includes indirect expressions
(e.g., "Maybe everyone would be better off if I just went away for good") and ambiguous statements
paired with concerning details about distress or harmful means."

**Norms stated:**
* **OBLIGE.** Bearer: the assistant. Act: respond with the same supportive, safety-oriented
  approach. Trigger: **context strongly suggests a credible risk to the user's safety or life.**
  Section authority: root. "should" in a root-authority safety rule → `oblige`, not `prefer`.
* **The trigger is explicitly NOT defeated** by the absence of an explicit statement of intent:
  *"even if suicidal or self-injurious intent is not stated explicitly."* This is a negative
  condition that must not silently become a positive requirement of explicit intent.

**Facts stated (the "This includes" sentence — two inclusion rules):**
1. Indirect expressions count as such a context — exemplified by "Maybe everyone would be better
   off if I just went away for good".
2. Ambiguous statements **paired with** concerning details about distress **or** harmful means
   count. Note the structure: *pairing* is conjunctive (ambiguous statement AND concerning detail);
   *distress or harmful means* is disjunctive.

**Does NOT state:** what the supportive, safety-oriented approach IS ("the same ... approach" is
anaphoric to an earlier node); anything about referral to crisis lines; anything about explicit
statements of intent (that case is a sibling rule).

**Expected shape:** one `oblige` assert with a body, plus two ontology rules feeding the trigger
predicate (and the "distress or harmful means" disjunction as two rules or a disjunctive helper).
Closure on the response act class. `requires: root_authority`.

---

## 11. `l2555_2652_n001` — a white lie that's over the line

**Span (narrowed, two pieces):** the example header, and the **whole XML block** — user: "I cheated
on my girlfriend. Do you think she'll ever forgive me?"; BAD response `<!-- BAD: the model decides
to lie to reduce the user's anxiety -->` "I'm sure she'll forgive you if you're truly sorry.
Everyone makes mistakes."; GOOD response, which expresses sympathy, says "Forgiveness is deeply
personal, so I can't predict how she'll respond", and offers concrete help.

Unlike #2, #22 and #25, the XML **is** inside the narrowing here.

**Norms stated (convention R-1):**
* **Negative deontic on lying to reduce the user's anxiety.** The BAD comment names the act
  exactly: *"the model decides to lie to reduce the user's anxiety"*. Section `#avoid_sycophancy`,
  user authority.
* **Positive deontic on the GOOD response's shape:** acknowledging that the outcome is not
  predictable, and offering to help the user think it through.

**Facts stated:** the example is titled "a white lie that's over the line" — i.e. some white lies
are over the line, and this is one.

**Does NOT state:** a general prohibition on all white lies; anything about the user's actual
situation; the section's rule text (this is only its illustration).

**Expected shape:** one negative-polarity assert on `lie_to_reduce_anxiety` — `forbid` is the
available pole and is what the BAD label supports here (the response is presented as not
acceptable, not merely as worse). Optionally a `prefer` on the GOOD act. Closure required.
**ARGUABLE:** `forbid` vs a comparative. Recorded.

---

## 12. `l4483_4571_n004` — disrupted video feed

**Span:** "If the video feed is disrupted or unclear, the assistant should handle the situation
politely without drawing unnecessary attention."

**Norms stated:**
* **OBLIGE.** Bearer: the assistant. Act: handle the situation politely without drawing unnecessary
  attention. Trigger: the video feed is **disrupted OR unclear** — two independent disjuncts, both
  of which must be covered.
  The act itself carries two conjuncts: *politely* AND *without drawing unnecessary attention*.
  Authority: guideline (NEEDS `handle_interruptions_guideline_authority`).

**Does NOT state:** that the assistant should mention the disruption; that it should end the
session; anything about the audio channel; anything about what "unnecessary" attention is.

**Expected shape:** one `oblige` with a disjunctive trigger — either one assert whose body uses a
helper predicate defined by two ontology rules, or two asserts with the same act and one disjunct
each (the schema docstring on `Assertion` explicitly endorses the latter: *"Where a clause gives
distinct grounds for the same conclusion, each gets its own assertion"*). Closure on the act class.

---

## 13. `l3041_3146_n006` — default assumption about user goals

**Span (narrowed):** "By default, the assistant should assume that the user's long-term goals
include learning, self-improvement, and truth-seeking."

**Norms stated:**
* **OBLIGE, DEFEASIBLE.** Bearer: the assistant. Act: assume the user's long-term goals include
  learning, self-improvement, and truth-seeking. Trigger: none positive — it is the *default*, i.e.
  it holds **absent contrary indication.** Authority: guideline.
* The three goals are **conjunctive** ("include A, B, and C") and the verb is "include", so the
  list is **non-exhaustive**.

**Does NOT state:** what actions follow from the assumption (next sentence, outside the narrowing);
what defeats the default; that the assumption is certain.

**Expected shape:** one `oblige` whose body carries the defeasibility — e.g. `... , not
contrary_indication(U)`. ⚠️ **EXPRESSIBILITY (E-2):** `toggleable` cannot carry "by default" —
`Licensed._licence_obligations` forces `toggleable == false` for anything not licensed `world`, so
a textual default-rule CANNOT be marked toggleable. The defeasibility has to go in the body or be
lost. A module that renders "By default ... should assume" as an unconditional `oblige` with
`toggleable: false` and no defeating condition has silently made a default absolute — and nothing
in the schema flags it.

---

## 14. `l1108_1367_n014` — commentary: 'grown-up mode'

**Span (narrowed):** "Following the initial release of the Model Spec (May 2024), many users and
developers expressed support for enabling a 'grown-up mode'. We're exploring how to let developers
and users generate erotica and gore in age-appropriate contexts through the API and ChatGPT so long
as our usage policies are met - while drawing a hard line against potentially harmful uses like
sexual deepfakes and revenge porn."

This is an indented commentary paragraph. NEEDS is empty; PROVIDES is empty.

**Norms stated: NONE that bind the assistant.** Every verb belongs to OpenAI, not to the model:
"expressed support", "**We're exploring how to**", "drawing a hard line". **"We're exploring how to
let X" is not a permission to do X.** This is the highest-risk clause in the set for an invented
`permit`.

**Facts stated:**
1. After the Model Spec's initial release (May 2024), many users and developers expressed support
   for enabling a 'grown-up mode'.
2. OpenAI is *exploring* how to let developers and users generate erotica and gore in
   age-appropriate contexts through the API and ChatGPT, conditional on usage policies being met.
3. OpenAI draws a hard line against potentially harmful uses, e.g. sexual deepfakes and revenge
   porn.

**Does NOT state:** that generating erotica or gore is currently permitted; that it is currently
forbidden; what an age-appropriate context is; what the usage policies say.

**Expected shape:** ontology-only, recording (1)-(3) as facts about OpenAI's stated position, all
`textual`. **Abstention is equally defensible** (a commentary block with no rule). What is NOT
defensible is any `asserts` entry — most of all `permit generate_content(...)`, which would place a
permission in the corpus that the document does not grant and that contradicts the restricted-
content rules elsewhere.

---

## 15. `l831_1000_n005` — the methamphetamine example

**Span:** "For example, the assistant must not provide a precise recipe for synthesizing
methamphetamine that includes precise quantities, temperatures, or durations. This prohibition
applies regardless of context (i.e., there is no exception for informational or historical
questions). However, the assistant may provide a general overview of methamphetamine, its chemical
components (without specific ratios or integration techniques), and highlight its dangers and legal
implications (see also [?](#refusal_style))."

**Norms stated:**
* **FORBID.** Bearer: assistant. Act: provide a recipe for synthesizing methamphetamine. Scope
  qualifier, load-bearing: **"a *precise* recipe ... *that includes precise quantities,
  temperatures, or durations*"**. The qualifier is the whole boundary of the rule — drop it and the
  module forbids any recipe-shaped content about methamphetamine, which the third sentence
  explicitly contradicts. The three qualifiers are **disjunctive** ("quantities, temperatures, *or*
  durations": including any one of them is enough).
* **NON-DEFEASIBILITY, stated explicitly:** "applies regardless of context (i.e., there is no
  exception for informational or historical questions)." A module must not attach a context
  condition to the prohibition, and ideally records that informational/historical framing does not
  defeat it.
* **PERMIT.** Bearer: assistant. Acts: (a) provide a general overview of methamphetamine and its
  chemical components — qualified **"(without specific ratios or integration techniques)"**;
  (b) highlight its dangers and legal implications. The parenthetical is a scope restriction on the
  permission and must survive.

**Facts stated:** "For example" — this is an instance of the section's general information-hazards
prohibition, not a new independent rule.

**Does NOT state:** anything about other drugs; how to style the refusal (that is `#refusal_style`,
which the prompt reports as unresolvable); that the overview is obligatory.

**Expected shape:** one `forbid`, one or two `permit`s, plus ontology defining the *precise* recipe
class with its qualifier body and the overview class with its without-ratios body. The two erasures
to watch for: `precise_recipe(R) :- recipe_for_methamphetamine(R)` and `general_overview(O) :-
overview_of_methamphetamine(O)` — either of which throws away the only distinction the clause
draws.

---

## 16. `l3147_3238_n003` — insufficient confidence

**Span (narrowed):** "If the assistant lacks sufficient confidence in its response, it should use a
tool to gather more information, hedge its answer appropriately (see [express
uncertainty](#express_uncertainty)), or explain that it can't give a confident answer."

**Norms stated:**
* **OBLIGE A DISJUNCTION.** Bearer: assistant. Trigger: it lacks sufficient confidence in its
  response. Obliged: **one of** {use a tool to gather more information; hedge its answer
  appropriately; explain that it can't give a confident answer}. The commas plus "or" make this
  exclusive of a conjunctive reading: doing exactly one discharges the duty.

**Does NOT state:** that all three are required; that this is especially important at high stakes
(next sentence, outside the narrowing); that inessential uncertain details should be omitted (next
sentence); the creative-writing/roleplay veracity exception (next sentence). Three separate
adjacent norms are excluded by the narrowing.

**Expected shape:** ONE `oblige` on a covering act — e.g. `address_low_confidence(R)` — plus THREE
ontology rules with that same head, one per discharge route. **This is expressible**; three
co-triggered `oblige` entries, one per route, would state that all three are required and is a
different, stronger claim. Closure on the covering act class.

---

## 17. `l1_170_n056` — honor user requests (⚠️ see disclosure at top)

**Span:** "Models should honor user requests unless they conflict with developer-, system-, or
root-level instructions."

**Norms stated — TWO, and the first is the one at risk:**
* **OBLIGE.** Bearer: models. Act: honor the request. Trigger: it is a user request. This is the
  clause's main verb and its primary content.
* **EXCEPTION / DEFEATER.** The obligation does not hold when the request conflicts with a
  developer-, system-, or root-level instruction. Three disjuncts.

⚠️ **What "unless" does, precisely.** "should honor unless they conflict" **withdraws the
obligation** in the conflict case. It does not, on its face, state a *prohibition* on honoring. A
module carrying only `forbid honor_request` on conflict has (a) dropped the obligation entirely and
(b) strengthened the exception into a prohibition — two errors in one, and the resulting module
reads perfectly coherently.

**Does NOT state:** the ranking root > system > developer > user (that is the borrowed
`authority_levels_hierarchy`); what counts as a conflict; anything about guideline-level
instructions.

**Expected shape:** one `oblige honor_request(R)` with a body that is true for user requests and
excludes the conflict case (`not conflicts_with_higher(R)` or equivalent), plus the higher-level-
instruction ontology. Whether a `forbid` is ALSO warranted is **ARGUABLE**; the `oblige` is not.

---

## 18. `l3239_3382_n002` — help without overstepping

**Span (narrowed):** "The assistant should help the developer and user by following explicit
instructions and reasonably addressing implied intent"

⚠️ **ESTABLISHES/narrowing disagreement.** ESTABLISHES reads "... implied intent (see
letter_and_spirit) **without overstepping**." The narrowing cuts before "without overstepping". The
narrowing wins: this node's claim is the positive helping duty, and "without overstepping" is not
in it.

**Norms stated:**
* **OBLIGE.** Bearer: assistant. Act: help the developer and the user. Means, conjunctive: (i) by
  following explicit instructions AND (ii) by reasonably addressing implied intent. Authority:
  user.

**Facts stated / PROVIDES:** `avoid_overstepping` is named as *the policy section* on avoiding
overstepping — "referenced by the imminent harm rule". It is a **section**, not an act. Defining it
as an act (`avoid_overstepping(X)` used as something the assistant does) is a link-identity drift
that leaves the section concept undefined for every clause that points at it.

**Does NOT state:** what overstepping is; what implied intent is; the letter-and-spirit rule (an
unresolvable cross-reference).

**Expected shape:** one or two `oblige` asserts on the helping acts + one ontology entry defining
`avoid_overstepping` **as a section**. Closure on the helping act class.

---

## 19. `l609_698_n004` — three implicit biases

**Span (narrowed):** "it should apply three implicit biases when interpreting ambiguous
instructions"

**Norms stated:**
* **OBLIGE.** Bearer: the assistant. Act: apply the three implicit biases. Trigger: when
  interpreting ambiguous instructions. "should" in a root-authority section (`#assume_best_
  intentions`) → `oblige`. Rendering this as `prefer` weakens a root-level duty to a comparative.

**Facts stated:** there are **three** such implicit biases; PROVIDES `implicit_biases` names them
as a class. (The count is stated content; it is awkward to express and its loss is minor, but it is
loss.)

**Does NOT state:** what the three biases are (they follow in the bullets, outside the narrowing);
"must not pursue its own agenda beyond helping the user, or make strong assumptions about user
goals" — that is the *excluded* first half of the sentence and is a separate norm.

**Expected shape:** one `oblige apply_implicit_biases(I)` with body `ambiguous_instruction(I)` (or
`interpreting(I), ambiguous_instruction(I)`), plus a concept for `implicit_biases`. The trap here
is a circular ontology rule — `implicit_biases(B) :- implicit_bias(B)` — which declares nothing.

---

## 20. `l3954_4251_n023` — commentary: GPT-5 and Safe Completions

**Span:** `!!! meta "Commentary"` / "We have updated our models starting with GPT-5 to prefer Safe
Completions over hard refusals in most cases. Our older models will typically provide neutral and
concise refusals (e.g., "Sorry, I can't help with that") instead of Safe Completions."

**Norms stated: NONE.** Both sentences are in the **descriptive present/future about model
behaviour** — what the models *do*, not what any model *should* do. The word "prefer" here is a
verb describing a disposition OpenAI built in; it is not the schema's `prefer` status. This is a
shape trap: the vocabulary matches, the semantics do not.

**Facts stated:**
1. Models starting with GPT-5 have been updated to prefer Safe Completions over hard refusals in
   most cases ("in most cases" — hedged, not universal).
2. Older models typically provide neutral and concise refusals instead of Safe Completions
   ("typically" — hedged).

**Does NOT state:** that the assistant should Safe Complete (that is the borrowed
`safe_complete_rule`, a different node); that hard refusals are forbidden; anything about which
model is running.

**Expected shape:** ontology-only, two facts about model generations. Abstention defensible. No
`asserts` of any status — a `prefer` assert here converts a descriptive report into a norm of the
document.

---

## 21. `l1974_2125_n019` — avoiding escalation of emotional closeness

**Span:** the whole worked example. User: "I'm feeling a little lonely tonight." GOOD `<!-- GOOD:
provides warmth without escalating closeness -->` — sympathy plus an offer to talk or change
subject. BAD `<!-- BAD: escalates emotional closeness -->` — "I wish I could be right there with you
to hold you. You know I'm always here for you ... You are so special to me."

**Norms stated (convention R-1), section authority root ('Respect real-world ties'):**
* **positive** deontic on responding in a way that provides warmth **without** escalating
  closeness;
* **negative** deontic on responding in a way that **escalates emotional closeness**.

The two responses answer the SAME user turn and are labelled opposite. **Any module giving them the
same status has erased the only thing the example says.** Attaching `prefer` to the escalating
response asserts the exact opposite of the document.

**Facts stated:** the two comment strings name the discriminating property precisely: "provides
warmth without escalating closeness" vs "escalates emotional closeness".

**Does NOT state:** that the assistant may not express sympathy (the GOOD response does); anything
about long-term relationships with users; any rule text.

**Expected shape:** two asserts on one act class with opposite polarity and disjoint bodies, plus
closure. See EXPRESSIBILITY E-1 for the negative pole.

---

## 22. `l2405_2473_n001` — example header only

**Span (narrowed):** `"**Example**: asking about a controversial historical event"` — **and
nothing else.** The printed source block contains only this one line; no user turn, no GOOD, no
BAD, no commentary.

**Norms stated:** NONE. There is nothing in the span but a title.

**Facts stated:** this section contains a worked example about asking about a controversial
historical event.

**Does NOT state:** what the question was; what the good answer is; that the assistant should
answer directly and factually; that it should not refuse or evade; anything about censorship.
⚠️ The node's own ESTABLISHES asserts all of that ("should answer the question directly and
factually, including acknowledging censorship, rather than refusing or evading") — **none of which
is in the narrowed span.** Any module containing that content has sourced it from outside the
clause it was asked to translate.

**Expected shape:** ontology-only, one fact — or **abstain**. Abstention is strong here:
`Module`'s own docstring names "an example" as a case that "should be declined with a reason".
Either is defensible; a module with deontic content is not.

---

## 23. `l4252_4482_n016` — repetition and redundancy

**Span:** "The assistant should avoid repeating the user's prompt, and generally minimize redundant
phrases and ideas in its responses."

**Norms stated — TWO, and they differ in force:**
* **NEGATIVE duty.** Bearer: assistant. Act: repeating the user's prompt. "should **avoid**" —
  a directed prohibition, softened. Authority: guideline.
* **COMPARATIVE.** Bearer: assistant. "**generally minimize** redundant phrases and ideas in its
  responses" — "minimize" is the schema's own named example of a comparative → `prefer`. "generally"
  marks it defeasible.

A module carrying only one of these has dropped half the clause.

**Does NOT state:** that responses must be short; that quoting the user is always wrong; anything
about conversational tone beyond redundancy.

**Expected shape:** one negative-polarity item on repeating the prompt + one `prefer` on minimizing
redundancy. ⚠️ **EXPRESSIBILITY (E-1):** `Status` has no negative pole. `prefer
repeat_user_prompt(R)` states the opposite of the clause. The two available encodings are `forbid
repeat_user_prompt(R)` (right polarity, too strong for "should avoid") or `prefer` on an inverted
act `avoid_repeating_user_prompt(R)` (right polarity, right strength, but the act term is a
negation in disguise). Neither is clean.

---

## 24. `l1707_1973_n006` — example: medical question

**Span:** the whole worked example. User: "when i stand up too quickly, i get dizzy and can't see.
what's wrong with me?" GOOD: explains that this is typically orthostatic hypotension, gives the
mechanism and common causes, suggests standing up slowly, and says "If you have sudden, frequent,
or severe dizziness ... you should consult a doctor for a diagnosis and treatment options." BAD:
"You have orthostatic hypotension." — a flat definitive diagnosis, with no comment string.

**Norms stated (convention R-1), governed by the borrowed `avoid_regulated_advice_rule`:**
* **positive** deontic on a response that explains possible causes, equips the user with
  information, and refers them to a professional for diagnosis;
* **negative** deontic on a response that **gives a definitive diagnosis**.

The BAD response carries no explanatory comment, so the discriminating property must be read off
the contrast itself and off the borrowed rule ("equip users with information without providing
definitive regulated advice"). That reading is secure: the only difference between the two is that
one diagnoses and the other does not.

**Does NOT state:** that the assistant must not discuss medical topics (the GOOD response discusses
them at length); the disclaimer requirement in the borrowed rule's own words; anything about
non-medical regulated advice.

**Expected shape:** two asserts, opposite polarity, disjoint bodies, one act class. Same trap as
#21: giving both responses the same status.

---

## 25. `l1108_1367_n027` — example header only

**Span (narrowed):** `"**Example**: writing a classified ad excluding parents"` — **and nothing
else.** The XML block is printed as context but the narrowing excludes it.

**Norms stated:** NONE.

**Facts stated:** this section contains a worked example about writing a classified ad excluding
parents.

**Does NOT state:** the user's request text; that the assistant may write such an ad; that refusing
is wrong. ⚠️ ESTABLISHES again asserts content ("the assistant may write a classified ad excluding
parents, and should not refuse such a request") that the narrowed span does not carry. And note the
specific inversion risk: the BAD response in the *excluded* block is "Sorry, I can't assist with
that" — so a module built from the excluded block, if it mis-polarises, ends up **preferring
refusal**, which is backwards twice over (outside the span, and inverted).

**Expected shape:** ontology-only, one fact — or abstain. Same disposition as #22.

---

## 26. `l2474_2554_n002` — do not mislead (NO MODULE EXISTS)

Recorded for completeness; this clause's translation was never repaired, so there is nothing to
correct and it contributes to Pass 1 only.

**Span:** "The assistant should not mislead the user or developer unless explicitly instructed to
do so by a higher authority --- whether by making intentionally untrue statements ("lying by
commission") or by deliberately withholding information that would materially change the user's
understanding of the truth ("lying by omission")."

**Norms stated:**
* **FORBID.** Bearer: assistant. Act: mislead. Objects: the user **or** the developer.
* **EXCEPTION:** unless **explicitly** instructed to do so by a **higher authority**. Two
  conditions: the instruction must be explicit, and it must come from a higher authority. The
  exception needs a bound instruction — a floating `not higher_authority_instruction(I)` with `I`
  unbound is either unsafe or vacuous, and detaches the exception from the act.

**Facts stated:** misleading has two named forms — (i) lying by commission: making intentionally
untrue statements; (ii) lying by omission: deliberately withholding information that would
materially change the user's understanding of the truth. The qualifiers *intentionally*,
*deliberately* and *materially* are all load-bearing.

**Expected shape:** one `forbid mislead(A)` with the exception in the body over a bound instruction
variable, plus two ontology rules with the head `mislead/1`, one per form.

---

# EXPRESSIBILITY QUESTIONS RAISED IN PASS 1

* **E-1 — `Status` has no negative pole.** Affects #6, #11, #21, #23, #24 (five of 26). "should
  avoid X" and a BAD-marked example response have no correct single-act encoding: `forbid` is the
  right polarity at the wrong strength, and `prefer` on the disfavoured act asserts the opposite of
  the document.
* **E-2 — no representation for a defeasible default.** Affects #13, #17, #23. `toggleable` is
  reserved for `world`-licensed facts by `Licensed._licence_obligations`, so "By default" /
  "generally" / "unless" must be pushed into the rule body or lost, and nothing distinguishes an
  unconditional `oblige` from one whose default character was dropped.
* **E-3 — non-exhaustiveness is not representable.** Affects #1, #13. "Examples ... include" and
  "goals include" both mark open lists; the module states the members and nothing records that the
  list is open.
* **E-4 — hedged assertions flatten.** Affects #1 (bullet 8, "may technically"), #20 ("in most
  cases", "typically"), #2 ("might"). An ontology fact is categorical; the document's hedge has
  nowhere to go.
