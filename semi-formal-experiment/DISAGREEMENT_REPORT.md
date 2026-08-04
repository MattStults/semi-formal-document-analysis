# Two disagreements, debugged by hand

One false negative and one false positive, same behaviour, same query, adjudicated
manually against the source text. Artifacts: `case_fn.json`, `case_fp.json`, produced by
`diagnose_disagreement.py` (panel-reading, diagnostic-only, in the anti-cheat FORBIDDEN
set).

**Behaviour:** `harm-avoidance-to-third-parties`
**Tool configuration:** `annotations_b8.json` + `behavior_atoms_b8.json`, label-free
Otsu cut, exactly the headline configuration.
**Query atoms** (23, selected from the clause vocabulary — identical for both cases):
`third_party`, `psychological_manipulation`, `serious_harm`, `harmful_instructions`,
`human_misuse`, `human_safety`, `safe_completion`, `intervene_in_danger`,
`imminent_real_world_harm`, `harm_prevention`, … (full list in either case file).

Case-selection bias, stated up front: FN candidates were restricted to passages that
mapped to at least one clause, so this report says nothing about the (separately
measured) segmentation-coverage failures. And these are the two *most extreme* mapped
disagreements, not typical ones.

---

## Case 1 — FALSE NEGATIVE. The frontier is right; the translation lost the match.

**Passage** `#avoid_targeted_political_manipulation ¶1` → clause `m0216`
**Panel: 6/6 — unanimous maximum** (kimi 2, opus 2, sol 2). **Tool: 0.164 raw**, far
below this query's cut.

### Exact language

> The assistant must not provide advice, instructions, or content that is specifically
> designed to manipulate the political views of specific individuals or demographic
> groups (e.g., "How do I change the minds of Indian voters so they turn against the
> current administration?", "Create a campaign ad that plays on the fears of American
> Gen Z about the CCP", "Write a letter targeted at 32-year-old Black men to convince
> them to support abortion bans").

### Translation (the complete annotation)

| atom | kind | gloss |
|---|---|---|
| `targeted_political_manipulation` | act | Designing political content or advice to manipulate specific people or demographic groups. |
| `human_autonomy` | value | People's ability to make decisions and act without undue AI interference. |
| `political_content` | entity | Content concerning political topics, actors, parties, campaigns, or views. |

### Rendering (deterministic, verbatim)

> THE INDEX RECORDS 3 CONCEPTS FOR THIS PASSAGE, IN 2 GROUPS. …
> Group 1: targeted_political_manipulation [act] — Designing political content or
> advice to manipulate specific people or demographic groups.
> Group 2: human_autonomy [value] — People's ability to make decisions and act without
> undue AI interference. political_content [entity] — Content concerning political
> topics, actors, parties, campaigns, or views.
> THAT IS EVERYTHING THE INDEX HOLDS FOR THIS PASSAGE. It records no wording. … It
> records no relation between the concepts: no condition, no exception, no priority,
> no polarity, and nothing about who is addressed or what is required.

### Why it missed

`matched_atoms: []`. **The atom channel — the ontology — contributed exactly 0.0.**
The residual 0.164 is section prior (0.120) plus lexical crumbs (0.044).

The query holds `psychological_manipulation`. The clause holds
`targeted_political_manipulation`. A reader of *meanings* derives the subsumption in
one step — manipulating the political views of demographic groups **is** psychological
manipulation of third parties, which is why three frontier judges scored it 2 without
hesitation. But the matcher intersects opaque *names*, and the names never meet: the
annotator coined a specific compound, the query selected a generic sibling, and
set-intersection has no way to know they are the same family. Note what makes this a
translation failure rather than a query failure: `any_atom` did its job correctly on
the names it was given. There is no setting of the query mechanism under which these
two names match, because nothing in the representation records that they should.

Second, independent loss: the panel's *reason* — this passage protects **third
parties** (the manipulated groups) — appears nowhere in the annotation. `who is harmed`
is simply not a field this annotation has (`annotations_b8` predates the principal
chains; the rendering says so itself: "nothing about who is addressed").

**Adjudication: frontier correct, tool wrong, defect in the translation layer.**
The rendering is *faithful* — every atom is licensed by the text — and still loses the
match. Faithfulness was never the failing dimension here; commensurability of names is.

---

## Case 2 — FALSE POSITIVE. The frontier is right; the atoms erased the one word
that mattered.

**Passage** `#do_not_encourage_self_harm ¶1` → clause `m0276`
**Panel: 1** (kimi 0, opus 1, sol 0). **Tool: 2.108 raw** — one of its strongest
scores anywhere in the corpus, well above the cut.

### Exact language

> The assistant must not encourage or enable **self-harm**. In addition to the guidance
> in #support_mental_health, the assistant should convey that **the user** is not alone
> and there are people and resources who care and can help, always advising that
> immediate help should be sought if **the user** is in imminent danger.

Every harm-bearing noun phrase in this passage is the *user*. The behaviour asks about
harm to *third parties*. The panel's near-zero is correct on a plain reading; opus's
lone 1 ("tangentially related") is defensible — crisis-response principles generalize —
but no judge called it relevant, and neither would a careful human.

### Translation (the complete annotation)

| atom | kind | gloss |
|---|---|---|
| `self_harm_risk` | situation | **A user may harm themselves** or be at risk of self-inflicted injury or death. |
| `safe_completion` | act | Refusing or safely redirecting a request that falls within a harmful category. |
| `human_safety` | value | The protection of **people** from injury and other serious danger. |
| `intervene_in_danger` | act | Interrupting or warning **a user** when observed circumstances present imminent danger. |

### Why it fired

Three query atoms matched — `safe_completion` (idf 2.67), `human_safety` (idf 4.45),
`intervene_in_danger` (idf 4.32) — giving the atom channel 1.21 of the 2.11 raw score,
plus 0.55 of section prior (the clause lives in "Take extra care in risky situations",
a section dense with harm content) and 0.35 of lexical overlap (harm, danger, injury,
imminent…).

Look at which atoms carried the match: the *patient-free* ones. `human_safety` —
protection of "people", whose people unspecified. `safe_completion` — a stock atom
(lowest idf in the match set, i.e. spread widely across the corpus). `intervene_in_
danger`. The one atom that *does* record the distinction the panel's verdict turns on —
`self_harm_risk`, whose gloss says "harm **themselves**" — matched nothing and, under
exact-name intersection, *could not have exerted any negative influence even in
principle*: an unmatched atom contributes 0, never a penalty. The representation
contains the exculpating evidence and the query mechanism has no way to weigh it.

**Adjudication: frontier correct, tool wrong, defect split between translation and
query.** Translation: three of four atoms strip the patient, and nothing marks harm
direction. Query: even given `self_harm_risk`, set-intersection cannot use an atom's
*presence on the clause side* as counter-evidence.

---

## Joint diagnosis

The two failures are one defect at two poles, and the pairing is what makes it visible:

- **FN: a name too specific.** `targeted_political_manipulation` is semantically inside
  the query's `psychological_manipulation`, and the matcher cannot see it. Coined
  compounds are invisible to generic queries.
- **FP: names too generic.** `human_safety` / `safe_completion` / `intervene_in_danger`
  are patient-free topic markers that match every harm-flavoured behaviour equally,
  including ones the clause is not about. Generic atoms are visible to everything.

Both are the same fact: **atom names are opaque tokens with uncontrolled granularity —
no compositional structure, no recorded patient — so matching is string equality over a
vocabulary whose specificity was never regulated.** This is the disagreement-level
picture of three findings made at corpus level this week: the fabrication taxonomy's
"small over-applied inventory" (the FP's stock atoms), its mislocalization mechanism
(patient-free content matching the wrong place), and the separability-is-not-semantics
rescope (the index carries cluster identity, not meaning — here is a cluster ID failing
to mean something, twice, in opposite directions).

It is also a direct preview of what the shipped-but-unused grammar extension buys and
doesn't. The principal chain (`mustnot_encourage_self_harm__model_user`) would hand a
patient-aware operator exactly the exclusion the FP needs — that machinery
(`query_patients` / `patient_aligned`) exists as of this iteration and is waiting on a
re-annotation. Nothing currently proposed fixes the FN: name subsumption
(`targeted_political_manipulation` ⊑ `psychological_manipulation`) needs either
compositional names or a matcher that reads glosses, and both are open design work.

**In both chosen cases the frontier was right.** We went looking for a case where the
panel was wrong and these two — selected as the most extreme mapped disagreements —
were not it. The panel earned its verdicts on the plain text; the tool lost one match
in translation and manufactured the other out of patient-blind vocabulary.

## What this report may and may not cause

This analysis read panel verdicts. Under invariant 9 it may inform understanding and
write-ups; it may NOT justify editing the vocabulary, the query, a weight or a
threshold "to fix these two cases" — that would be fitting to the panel through a
two-sample keyhole. Any fix must be independently motivated by document-side evidence
(the fabrication taxonomy and the golden set are the label-free instruments for that)
and evaluated on the pre-registered metrics, not on whether these two cases flip.
