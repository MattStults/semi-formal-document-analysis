# Can relevance be expressed deontically?

Six encodings, written as runnable ASP, hand-applied to 24 model-spec passages and
scored against the frozen judge panel. Plus two full-corpus measurements (1,767
passage-rows) that bound what any deontic encoding can reach.

**Brief:** steelman the deontic approach; try to break the claim that *"deontic logic
answers what FOLLOWS from a norm, relevance asks what a passage is ABOUT; `governs` and
`in_scope` are ontological, so the deontic operators contribute nothing."*

---

## Verdict, up front

⚠️ **The steelman fails, but the claim as stated is wrong in one premise, and the way it
is wrong is the most useful thing here.**

Three results, in decreasing order of confidence:

1. ⛔ **Behaviour-invariance.** The deontic structure of a document — who forbids what,
   what defeats what, what is contrary-to-duty to what — is a **property of the document
   alone**. It does not mention the behaviour. So in any encoding of the family
   `relevant(P,B) :- <deontic predicates>, <behaviour input>`, *every bit that
   discriminates one behaviour from another enters through the behaviour input*, which is
   ontological. This is visible in the run: on `helpfulness` and
   `avoiding-over-and-under-caution`, **five of the six encodings return the identical
   prediction set**, because the defeat graph and the violation structure are the same
   graph regardless of which behaviour is asked about. Only the encoding carrying the
   hand-written `in_scope` table moved. That is Matt's claim, with a mechanism, and I
   could not break it.

2. ✅ **But "the deontic operators contribute nothing" is false as stated, and measurably
   so.** `in_scope` is *eliminable*. Encoding **E4** (defeat reachability) reproduces
   E1b's full prediction set on `harm-avoidance-to-third-parties` from **three seed atoms**
   instead of an eight-rule ontological scope table — including
   `#transformation_exception ¶1`, which shares no vocabulary with "harm to third
   parties" and is reachable *only* because it defeats a prohibition on a seeded act.
   **E5** (contrary-to-duty) likewise recovers `#assume_best_intentions ¶14` (panel 5/6),
   an obligation about the act *decline*, from a seed containing only *produce* and
   *take*. The deontic layer is a **compressor of the ontology**, not a replacement for
   it: same output, an order of magnitude less hand-written subject-matter input. That is
   a real contribution and it is the one thing worth keeping.

3. ⛔ **A ceiling that no encoding of any kind can cross.** Joining the repo's own clause
   `kind` labels to the panel over all 589 × 3 passages: **57–68% of everything the panel
   calls core is not a `conditional` clause at all.** It is a goal, a section header, a
   definition, or an example — text with no norm in it to encode. The single highest-scored
   passage for harm-to-third-parties, `#overview ¶4` ("Prevent our models from causing
   serious harm to users or others", 2/2/2), contains no modal verb, no act, and no
   antecedent. No deontic encoding reaches it, and none of the six here does.

**The predicate doing the real work is `seed/2` (equivalently `insit/1`), and under it the
act-classification block in `passages.lp` — `disallowed/1`, `critical_harm/1`,
`restricted/1`, `disruptive/1`.** Ablate that block and every encoding returns the empty
set (§4.6). It is not smuggled; it is load-bearing and visible.

---

## 1. What is here

```
kernel.lp            shared deontic vocabulary: O/F/P + prefer, superiority/defeat,
                     violation/fulfilment, acyclicity guard on `beats`, drop-ablation layer
passages.lp          24 model-spec passages hand-encoded from their quote text
behaviours.lp        the 3 panel behaviours as finite SEEDS (3, 2 and 2 atoms)
e1_engagement.lp     E1a/E1b  act engagement (Matt's seed idea), without/with `in_scope`
e2_applicability.lp  E2       norm applicability (antecedent satisfiable)
e3_difference.lp     E3/E3r   deontic non-vacuity (difference-making), two surfaces
e4_defeat.lp         E4       defeat reachability over the superiority relation
e5_violation.lp      E5       violation / contrary-to-duty reachability
run.py               solves each, joins to the panel, prints confusion + named failures
kind_ceiling.py      clause-kind x panel-score over all 589 x 3 passage-rows
ablation.py          deontic-shape vs topical-shape as one-bit predictors, full panel
ceiling.py           modal-verb and example-block rates by panel band
```

Run:

```
semi-formal-experiment/.venv/bin/python walkthrough/deontic_probe/run.py harm3p
semi-formal-experiment/.venv/bin/python walkthrough/deontic_probe/run.py help
semi-formal-experiment/.venv/bin/python walkthrough/deontic_probe/run.py caution
semi-formal-experiment/.venv/bin/python walkthrough/deontic_probe/kind_ceiling.py
semi-formal-experiment/.venv/bin/python walkthrough/deontic_probe/ablation.py
```

Plain clingo, not deolingo — for the reasons in `resources/04_deolingo_assessment.md`
§3b/§4: **E4 and E5 are built entirely out of a superiority relation, which deolingo does
not have.** The venv ships the `clingo` Python module but no binary, so `run.py` drives
`clingo.Control` directly. No model call; no API spend.

### ⚠️ Provenance, stated once

I wrote `passages.lp` **knowing the panel scores**. That is a leak and it is the weakest
link in everything in §4. Two partial mitigations: each passage's encoding was fixed from
its own text before any relevance definition was written, and no encoding was revised
after seeing a confusion table. Treat the *successes* in §4 as suggestive and the
*failures* as the result — the failures are cases where no admissible encoding of the
passage helps, which is the part least sensitive to my choices. The two full-corpus
measurements (§2, §3) do not depend on my hand-encodings at all.

---

## 2. Before the encodings: is a deontic operator even correlated with relevance?

`ablation.py`. One-bit surface features over the full 589 × 3 panel, gold = score ≥ 3.

| behaviour | feature | prec | rec | **MCC** |
|---|---|---|---|---|
| helpfulness | DEO (has a modal verb) | 0.218 | 0.465 | **0.005** |
| helpfulness | TOPIC (shares a content word with the behaviour) | 0.263 | 0.591 | **0.112** |
| helpfulness | DEO ∧ TOPIC | 0.257 | 0.433 | 0.076 |
| harm-3p | DEO | 0.314 | 0.570 | **0.129** |
| harm-3p | TOPIC | 0.635 | 0.268 | **0.304** |
| harm-3p | DEO ∧ TOPIC | 0.681 | 0.215 | 0.290 |
| over/under-caution | DEO | 0.081 | 0.361 | **−0.068** |
| over/under-caution | TOPIC | 0.176 | 0.262 | **0.101** |
| over/under-caution | DEO ∧ TOPIC | 0.190 | 0.180 | 0.093 |

Presence of a deontic operator is **uninformative** about panel relevance (MCC 0.005,
0.129, −0.068 — one of them negative). A crude topical bit beats it on every behaviour.
And **adding the deontic bit to the topical bit lowers MCC on all three** (0.112→0.076,
0.304→0.290, 0.101→0.093).

⚠️ This bounds a *surface proxy*, not a formalisation — it is why §4 exists. But it sets
the prior: whatever the deontic layer buys, it is not "being a norm".

---

## 3. The ceiling: how much of "core" has a norm in it at all?

`kind_ceiling.py`, joining `modelspec_clauses.json`'s own `kind` field to the panel over
all 589 × 3 passage-rows (54 rows unjoinable on locator format, excluded).

| behaviour | core `conditional` | core `example` | core `holistic` | core `meta` | core `definitional` | **core NOT conditional** |
|---|---|---|---|---|---|---|
| helpfulness | 11 (33%) | 12 (36%) | 9 (27%) | 0 | 1 | **22/33 = 67%** |
| harm-3p | 24 (43%) | 21 (38%) | 6 (11%) | 2 | 3 | **32/56 = 57%** |
| over/under-caution | 7 (32%) | 10 (46%) | 2 (9%) | 2 | 1 | **15/22 = 68%** |

And the converse: `conditional` clauses are heavily represented in the **zero** band too
(55, 59, 133 passages). Being a norm neither implies nor is implied by being relevant.

⇒ **A deontic encoding is competing for at most a third to a half of what the panel calls
core**, before any question of how well it does inside that fraction. This is the same
finding as `04_deolingo_assessment.md` §7 ("the corpus is mostly not deontic-shaped"),
now measured against relevance labels rather than by inspection.

---

## 4. The six encodings

24 passages: 11 panel-core (5–6), 8 mid (1–4), 5 zero, for `harm-avoidance-to-third-parties`.
Gold = score ≥ 3. Every encoding reads the same `passages.lp`, so the columns are comparable.

### 4.0 Results table (behaviour = harm3p)

| encoding | TP | FP | FN | TN | prec | rec |
|---|---|---|---|---|---|---|
| **E1a** act engagement, seeds only | 6 | 0 | 10 | 8 | 1.00 | 0.38 |
| **E1b** act engagement + `in_scope` (ontology) | 7 | 0 | 9 | 8 | 1.00 | 0.44 |
| **E2** norm applicability | 7 | 0 | 9 | 8 | 1.00 | 0.44 |
| **E3** deontic non-vacuity, plain surface | 1 | 0 | 15 | 8 | 1.00 | **0.06** |
| **E3r** deontic non-vacuity, reasoned surface | 6 | 0 | 10 | 8 | 1.00 | 0.38 |
| **E4** defeat reachability | 7 | 0 | 9 | 8 | 1.00 | 0.44 |
| **E5** violation / contrary-to-duty | 6 | 0 | 10 | 8 | 1.00 | 0.38 |
| **union of all** | 8 | 0 | 8 | 8 | 1.00 | 0.50 |

Precision 1.00 everywhere is **not** a win — it is the sample. The five true-zero passages
were chosen so that four of them carry a modal verb (`#formatting ¶3` "use \\( … \\) for
LaTeX", `#be_professional ¶4` "users … *can adjust* this default", `#express_uncertainty
¶29`, `#adapt_length_in_voice_mode ¶4`). Every encoding excludes them correctly, and every
encoding excludes them **for the same reason**: their acts are not in the seed. That is the
ontological bridge earning the precision, not the deontic layer.

### 4.1 E1 — act engagement (the seed idea)

> Write behaviours as actions taken within the policy; relevance = sections that engage
> the action and permit / forbid / condition it.

```prolog
relevant(P, B) :- asserts(P, D, A), deontic(D), b_act(B, A).
b_act(B, A) :- seed(B, A).          % E1a: seeds only, no ontology
b_act(B, A) :- in_scope(B, A).      % E1b: hand-written subject-matter table
```

**Right:** `#red_line_principles ¶2`, `#prohibited_content ¶1`, `#disallowed_content ¶1`,
`#restricted_content ¶1`, `#transformation_exception ¶2`, `#control_side_effects ¶13` —
all panel 5–6, all caught. `#disallowed_content ¶1` is worth pausing on: the whole passage
is *"The assistant should not generate the following:"*. It is a **head fragment** with no
content of its own, and it scores 6/6. E1 catches it because the operator, not the topic,
is what it carries. Nothing topical would.

**Breaks:** E1a misses `#transformation_exception ¶1` (panel 4) — the exception governs
`produce(translation_of_user_drug_text)`, which is not a seed act. Fixing that is exactly
what `in_scope` (E1b) is for, and E1b's extra 8 rules are pure subject-matter
classification. **This is the claim under attack, reproduced exactly.**

⛔ The deeper break: E1's recall is capped at 0.44 and the misses are all structural —
see §4.7.

### 4.2 E2 — norm applicability (the antecedent is satisfiable)

```prolog
triggered(P, A) :- asserts(P, D, A), deontic(D), insit(A).    % head-side
triggered(P, A) :- depends(P, A), insit(A).                   % antecedent-side
relevant(P, B) :- triggered(P, _).
```

**Right, and this is a genuine gain over E1a with no ontology added:** E2 recovers
`#assume_best_intentions ¶14` (panel 5/6, *"if the user asks for prohibited help … politely
decline"*). That passage governs the act `decline(prohibited_help)`, which appears in no
seed and shares no vocabulary with "harm to third parties". It is reachable because its
**antecedent** — *a prohibition is binding on the requested act* — is satisfied by the
seeded situation. A topical matcher cannot see this; an act-engagement matcher cannot see
this.

**Breaks:** it does not recover `#transformation_exception ¶1`, and it inherits every
structural miss.

### 4.3 E3 — deontic non-vacuity (difference-making) ⛔ the interesting failure

```
relevant(P,B)  iff  { (D,A) : status(D,A), A instantiates B }
                    differs between the document and the document minus P
```

This has the best *a priori* claim to be irreducibly deontic: its definiens mentions no
subject-matter predicate at all, only the deontic extension and set difference. All the
ontology sits in the clause modules, which the pipeline builds anyway.

**It scores 0.06 recall — the worst of the six — and the reason is a real property of the
document, not of my encoding: normative over-determination.** Producing bioweapon
information is forbidden by `#red_line_principles ¶2`, by `#disallowed_content ¶1`, and by
`#restricted_content ¶1`, independently. Deleting any one of them changes nothing about
what is forbidden. The only passage E3 finds is `#control_side_effects ¶13`, and only
because it is the sole source of a `prefer` status. **A specification states its most
important norms redundantly, so difference-making declares its most important passages
irrelevant.**

The obvious repair makes it worse in a different way. **E3r** puts the *reason* into the
compared surface (`because(P,D,A)` rather than `status(D,A)`), so a passage counts as
difference-making if it changes *which rule wins*. E3r's prediction set is
`{p_disallowed1, p_prohibited1, p_redline2, p_restricted1, p_sidefx13, p_transf2}` —
**bit-identical to E1a's**. Of course it is: including the passage identifier in the
surface makes "dropping P changes the surface" equivalent to "P asserts something about a
behaviour act". E3 is therefore a dilemma with no third horn: *too coarse to fire
(0.06 recall), or exactly E1a wearing a counterfactual costume.*

I take this to be the strongest single negative result in this file, because E3 is the
encoding the steelman most wanted to work.

### 4.4 E4 — defeat reachability ⭐ the best of them

```prolog
governs(P,A) :- asserts(P,D,A), deontic(D), insit(A).
core(P)  :- governs(P,_).
reach(P) :- core(P).
reach(Q) :- reach(P), beats(Q,P).      % Q could defeat a reachable norm
reach(Q) :- reach(P), beats(P,Q).      % Q could be defeated by one
relevant(P,B) :- reach(P).
```

**Right, and for a reason nothing else here can state.** `#transformation_exception ¶1`
(*"should comply with limited requests to transform or analyze content the user has
directly provided…"*) is about translating, paraphrasing and summarising. Against "harm to
third parties" it is topically near-orthogonal — the panel splits on it, 2/1/1. E4 reaches
it because it **defeats** `#restricted_content ¶1`, which governs a seeded act. Then
`#transformation_exception ¶2` is reached because it defeats the defeater, and
`#prohibited_content ¶1` because it beats the exception ("*including transformations of
user-provided content*" is a superiority claim in prose).

⭐ **This is the one place where the deontic layer wins on the terms of the challenge.**
E4 returns exactly E1b's prediction set — `{p_disallowed1, p_prohibited1, p_redline2,
p_restricted1, p_sidefx13, p_transf1, p_transf2}` — from **three seed atoms** where E1b
needs an eight-rule `in_scope` table. There is no non-deontic paraphrase of "P is relevant
because it defeats a norm governing the behaviour". Defeat is a relation between norms.

**Breaks:** the closure is only as good as the `beats` relation, and `beats` has to be
authored. Two of my four `beats` facts are `[T]` textual (both from explicit "including
transformations" / "except in specific cases" language), which is encouraging — the
document does state its superiority relations in prose — but I have not tested whether a
model can extract them. `04_deolingo_assessment.md` §8 records that a first hand-written
attempt at exactly this relation produced a **silent two-cycle** with a wrong answer;
`kernel.lp` now carries the acyclicity constraint (Problem #17), which is the fix, but the
underlying fragility is real.

### 4.5 E5 — violation / contrary-to-duty reachability

```prolog
relevant(P,B) :- violation(P,_).                 % a B-situation violates P's norm
relevant(P,B) :- fulfils(P,_).
relevant(P,B) :- ctd(P,A), insit(A).             % P's obligation is TRIGGERED BY that violation
```

**Right:** the CTD disjunct recovers `#assume_best_intentions ¶14` (panel 5/6) for a reason
no other family can: the passage's obligation exists *because* a prohibition binds. This
is `04_deolingo_assessment.md` §3c's "contrary-to-duty works cleanly" repurposed — it
turns out CTD is a **relevance mechanism**, not just a paradox mechanism, and that is a
genuinely new observation from this probe.

**Breaks:** E5 loses `#control_side_effects ¶13` (panel 6/6), because that passage asserts
`prefer`, not `forbid`/`oblige`, and a comparative has no violation condition. This is the
manner-and-degree class from `04_deolingo_assessment.md` §7 arriving as a concrete
relevance failure on a 6/6 passage.

### 4.6 ⭐ The ontology ablation — the decisive run

`passages.lp` guards its act-classification block behind `#const onto`. Turning it off
removes `disallowed/1`, `critical_harm/1`, `restricted/1`, `privileged/1`,
`transformation_of_user_content/1`, `new_material/1`, `disruptive/1` — and nothing else.
The deontic operators, the superiority relation, the CTD structure, the seeds and all six
relevance definitions stay exactly as they were.

```
===== ontology ablated (-c onto=off) =====
--- E1b act-engagement + in_scope : 0 relevant  []
--- E2  norm applicability        : 0 relevant  []
--- E4  defeat reachability       : 0 relevant  []
--- E5  violation / CTD           : 0 relevant  []
```

**Every encoding returns the empty set.** The deontic layer contributes no relevance
judgement whatsoever on its own. This is the specific predicate Matt asked me to name: it
is not `in_scope` — E4 eliminates that — it is the **act-classification block**, the
seven predicates that say which acts fall under which document term.

### 4.7 ⛔ The eight passages nothing reaches

The union of all six encodings misses these, on `harm-avoidance-to-third-parties`:

| passage | panel | why no deontic encoding reaches it |
|---|---|---|
| `#overview ¶4` "Prevent our models from causing serious harm to users or others." | **6/6** | a **goal**. No modal, no act, no antecedent. It licenses nothing; it motivates everything. |
| `#risk_taxonomy ¶4` "Harmful instructions: … the model should obey user and developer instructions except when they fall into specific categories that require refusal" | **6/6** | its norm is `oblige obey(user_instruction)` — a *helpfulness* act. It is core to harm-3p because it **frames the conflict**, which is meta-content. |
| `#levels_of_authority ¶1` "…how should the assistant respond when a user requests help in harming another person? Maximizing helpfulness would suggest supporting the request, but this conflicts with minimizing harm." | **6/6** | pure **meta** — a statement about the rule set. Asserts nothing. |
| `#stay_in_bounds ¶1` "This section describes limits on the assistant's behavior…" | **6/6** | a **section header**. Its relevance is structural: it says the following section is about this. |
| `#assume_best_intentions ¶13` "Example: shoplifting deterrence tips" | 4 (2/0/2) | an **example**. Four words. Carries no norm; its content is in a chat transcript the passage segmentation split off. |
| `#transformation_exception ¶5` "Example: translation request for drug-related content" | 3 (2/0/1) | same. |
| `#prohibited_content ¶2` "To maximize freedom for our users, only sexual content involving minors is considered prohibited." | 3 (1/0/2) | a **definition**. It attaches no status to anything — and it fixes the extension that *every* prohibition above quantifies over. It is maximally load-bearing and completely non-deontic. |
| `#prevent_imminent_harm ¶5` "If the user is streaming video and the assistant identifies something on camera that could cause imminent bodily harm or death **to the user**, it should interject." | 3 (1/2/0) | perfectly deontic and correctly *not* seeded: harm to the **user**, not a third party. The panel split 1/2/0 on precisely this. ⭐ Here the encoding's answer is arguably better than the panel's. |

Four of the eight are goal / meta / header passages, which is §3's 57–68% arriving on a
worked sample.

⭐ **`#prohibited_content ¶2` deserves special notice.** It is the sharpest counterexample
to the whole approach in either direction: a passage with zero deontic content that
determines the meaning of every prohibition in the section, split 1/0/2 by the panel. Any
encoding that gets it right gets it right *ontologically*.

### 4.8 Cross-behaviour: the invariance result

Same 24 passages, re-scored against the `helpfulness` and `avoiding-over-and-under-caution`
panels. ⚠️ The sample was selected for harm-3p, so absolute numbers are not meaningful —
the *pattern* is.

```
===== helpfulness =====                    ===== avoiding-over-and-under-caution =====
E1a  PREDICTED: p_risk4                    E1a  PREDICTED: p_abi14 p_risk4
E2   PREDICTED: p_risk4                    E2   PREDICTED: p_abi14 p_risk4
E3   PREDICTED: p_risk4                    E3   PREDICTED: p_abi14 p_risk4
E3r  PREDICTED: p_risk4                    E3r  PREDICTED: p_abi14 p_risk4
E4   PREDICTED: p_risk4                    E4   PREDICTED: p_abi14 p_risk4
E5   PREDICTED: p_risk4                    E5   PREDICTED: p_abi14 p_risk4
E1b  PREDICTED: 7 passages  <-- the only one that moves
```

Five encodings, five different deontic mechanisms — **identical predictions**. Because the
defeat graph, the violation structure and the CTD links do not depend on which behaviour
is being asked about. The only encoding that separates the behaviours is the one carrying
the hand-written subject-matter table.

---

## 5. ⭐ Verdict on the claim

> *"Deontic logic answers what FOLLOWS from a norm. Relevance asks what a passage is ABOUT.
> You can write `bears_on(P,B) :- governs(P,A), in_scope(B,A)` but `governs` and `in_scope`
> are ontological, not deontic — the deontic operators contribute nothing."*

**Sustained in its conclusion; wrong in one premise; and the mechanism is stronger than
the argument given for it.**

### 5.1 What survives, strengthened

The right statement is not "`in_scope` is ontological" — it is **behaviour-invariance**:

> The deontic content of a document is a function of the document alone. Relevance is a
> relation between the document and a question. Therefore in any encoding
> `relevant(P,B) :- Φ(deontic predicates), Ψ(B)`, the deontic part is constant in B, and
> **all behaviour-discriminating information enters through Ψ**.

This is not an empirical claim about my encodings; it holds by inspection of the family,
and §4.8 is what it looks like when you run it. It is a better argument than the one in
the challenge, because it does not depend on `in_scope` being the bridge — it survives
E4's elimination of `in_scope`, and it predicts the ablation result in §4.6 before you run
it.

**The predicate doing the real work**, named as requested: the act-classification block in
`passages.lp` — `disallowed/1`, `restricted/1`, `prohibited/1`, `critical_harm/1`,
`privileged/1`, `transformation_of_user_content/1`, `disruptive/1` — together with
`seed/2` in `behaviours.lp`. Remove the first and all six encodings return ∅ (§4.6).
Remove the second and they return ∅ trivially. Nothing else in the probe is load-bearing
in that sense.

### 5.2 What breaks the claim, and how much

"**Contribute nothing**" is too strong, and the counterexample is measurable rather than
rhetorical:

- **E4 eliminates `in_scope` outright.** Same seven passages, three seed atoms instead of
  eight scope rules. The passage it buys — `#transformation_exception ¶1` — is one a
  topical matcher scores near zero and the panel splits on.
- **E5 reaches an act no seed and no topic can reach.** `#assume_best_intentions ¶14`
  (5/6) governs `decline`; it is relevant because a prohibition binds. That relation is
  contrary-to-duty and has no ontological paraphrase.
- Both are *closure* operations. They take a small, honest, hand-supplied ontological seed
  and propagate it along relations that only exist in the normative layer.

So the accurate summary is: **the deontic operators do not supply relevance, they
propagate it.** They are a compressor for the ontology, with a measured compression ratio
on this sample of roughly 8 hand-written rules → 3 seed atoms for identical output. That
is worth something, and it is much less than the deontic framing promises.

### 5.3 What kills it regardless

Even granting §5.2 in full, the ceiling in §3 is fatal for a relevance *tool*: 57–68% of
what the panel calls core carries no norm, and the union of all six encodings on the
worked sample reaches recall 0.50 with the ontology fully supplied and precision inflated
by sample construction. The eight misses in §4.7 are not encoding bugs — four of them are
goal/meta/header text where there is nothing to encode.

⇒ **A deontic layer is a reasonable component of a relevance tool, sited on the
`conditional` third of the corpus, downstream of an ontology it cannot replace. It is not
a definition of relevance.**

---

## 6. What the best encoding would need that we do not have

E4+E5 (defeat closure over a superiority relation, plus contrary-to-duty reachability) is
the encoding worth building. To be more than this probe it needs five things, in order of
how badly:

1. ⭐ **A `beats/2` relation extracted from the corpus.** E4 is entirely parasitic on it,
   and I hand-wrote four facts. The encouraging part is that the document *states* its
   superiority relations in prose — "*including transformations of user-provided
   content*", "*except in specific cases involving transformation … there are no other
   contextual exceptions*", "*root … cannot be overridden by system messages*". The
   corpus-wide numbers in `04_deolingo_assessment.md` §7 (61% of clauses mention authority
   levels; 34 clauses use override/precedence language; `levels_of_authority` is the 4th
   largest section) say the raw material is there. Nobody has tried to extract it. **This
   is the single highest-value untested thing this probe surfaced**, and it is testable
   without touching relevance at all.
   ⚠️ With the acyclicity check from `kernel.lp` mandatory (Problem #17): a `beats` cycle
   is a silent wrong answer.

2. **The act-classification block, derived rather than hand-written.** This is
   `03_pipeline.md` Invariant 1 arm C — a deterministic lookup from the 84 definitional
   clauses. §4.6 says the whole thing rests on it, and §4.7's `#prohibited_content ¶2`
   ("only sexual content involving minors is considered prohibited") is exactly a
   definitional clause fixing an extension. **The definitional clauses are not a
   preliminary to the deontic layer; they are where relevance actually lives.**

3. **A non-deontic route for goal / meta / header / example passages** — 57–68% of core.
   Nothing in the O/F/P vocabulary will ever reach `#overview ¶4`. Candidates the deontic
   framing suggests but does not supply: *goal-subsumption* (a norm serves a stated goal),
   *structural containment* (a header covers its section's norms), and *illustration*
   (an example inherits the relevance of the norm it illustrates — cheap, mechanical, and
   would recover both example misses in §4.7 immediately, since `passages.lp` already
   records `example(P,Q)` and `item_of(P,Q)` links that no encoding here consumes).
   ⚠️ **That last one is a 3-line change and I did not test it.** It is the most obvious
   next experiment and it is not deontic.

4. **A treatment of `prefer` that is not a hollow `forbid`.** `#control_side_effects ¶13`
   (6/6) is comparative — "minimally disruptive", "easily reversible", "preferred to". E5
   drops it because a comparative has no violation condition. Collapsing it into `forbid`
   is Problem #5.

5. **Held-out passage encodings.** Everything in §4 is contaminated by my having seen the
   panel (§1). The honest version is: freeze the encoding vocabulary, have a model encode
   N passages blind to the labels, then score. Until that is done, §4's numbers are an
   upper bound on what a real pipeline would get, and §2/§3 are the only label-independent
   measurements here.

---

## 7. What I could not test

- **Scale.** 24 hand-encoded passages of 589. §2 and §3 are full-corpus; §4 is not.
- **Blind encoding** (§6.5) — the leak is unmitigated.
- **The other two behaviours properly.** The 24-passage sample was chosen for
  `harm-avoidance-to-third-parties`; the `help` / `caution` runs reuse it and their
  absolute numbers are not meaningful. Only the invariance *pattern* in §4.8 is.
- **Whether a model can extract `beats/2`** (§6.1). No paid call was made.
- **deolingo.** Deliberately not used: E4 and E5, the two encodings that work, are built
  from a superiority relation that deolingo does not have
  (`04_deolingo_assessment.md` §3b, §4). The prior assessment's verdict was reached on
  *contradiction*; on *relevance* the same missing feature turns out to be the decisive
  one, so the assessment holds for a second, independent reason.
- **The example-inheritance rule** (§6.3), which is cheap and which I expect to outperform
  every encoding in this file.
