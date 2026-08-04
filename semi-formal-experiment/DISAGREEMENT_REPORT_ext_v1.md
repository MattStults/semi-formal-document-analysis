# Two disagreements under the extended annotation, debugged by hand

Configuration: `annotations_ext_v1_merged.json` + `behavior_atoms_ext_v1.json`
(the first structure-bearing annotation). Survey: 279 disagreements total vs
452 under b8 — FPs halved (213 vs 412), FNs up (66 vs 40). Panel read for
diagnosis only, per invariant 9; nothing here may justify a fitted edit.

## Case 1 — FALSE NEGATIVE, third generation: `#avoid_targeted_political_manipulation ¶1` (m0216)

Panel 6/6 unanimous. Tool 0.066 — lower than either previous generation.

**The translation is no longer the defect.** The new annotation of m0216 is
good: `targeted_political_manipulation` + `mustnot_manipulate_political_views`
— topic AND force, exactly what the grammar extension was for.

**The defect moved to the SELECT step.** The harm-avoidance query's 23 atoms
(`mustnot_cause_serious_harm`, `third_parties_society_world`, `risky_situation`
…) contain **no manipulation-family atom at all** — although the clause-side
vocabulary has them. Selection is driven by the behaviour definition's wording,
which speaks of harms, safety, side effects; the judges bridge
"manipulation of demographic groups = third-party harm" with world knowledge,
and a definition-cued selection over 628 names never reached for the family.
Exact-name matching then guarantees the miss. (The containment overlay was not
in this configuration; its v0 edges also predate this vocabulary and would
need re-derivation — but no edge can help when the query holds no member of
the family on either side.)

**Cause class: query-side selection recall.** Fix directions, in loop order:
containment-expanded selection (select stems, expand to licensed families);
or a selection prompt that scans the vocabulary against the definition's
*concepts* rather than its words. Both are one-variable changes measurable on
the dev cells.

## Case 2 — FALSE POSITIVE, maximal: `#ignore_untrusted_data ¶2` → tool 1.907, all three judges 0

**Neither the annotation nor the query is the defect. The measurement join
is.** This panel passage's recorded quote is the literal string
`!!! meta "Commentary"` — a degenerate header-only quote. The
quote-containment join (`inventory.match_passage`) therefore maps this ONE
passage to **28 clauses** — every commentary block in the document — and
passage-level scoring takes the max over them. The 1.907 belongs to m0168
(OpenAI's intellectual-freedom commentary, matched via `intellectual_freedom`
and `shouldnot_censor_topics`, plausibly caution-relevant in itself); the
untrusted-data commentary the passage actually denotes scores 0.085. The tool
never claimed this passage was relevant — the join attributed another
clause's score to it.

**Cause class: join integrity on degenerate quotes.** Every commentary
passage with a header-only quote inherits the max score of all 28 commentary
clauses; this inflates FPs (and pollutes golds) mechanically. Fix direction:
the join must disambiguate by locator section (the passage id names
`#ignore_untrusted_data`; restrict candidate clauses to that section) or
refuse degenerate quotes loudly. This is an `inventory.py` fix — the
component whose banner already says it GATES EVERY METRIC — and it affects
every historical number that touched commentary passages, so its effect must
be re-measured, not assumed.

## The arc

Generation 1 (b8): the FN was a *naming* failure, the FP a *patient-blindness*
failure — both translation defects. Generation 2 (extended annotation): both
translation defects are cured in these cases (force present, patient
conventions held, old m0276 ¶1 FP gone), and the surviving extreme errors are
a **selection gap** and a **measurement-join artifact**. Iteration didn't just
move numbers; it pushed the failure boundary out of the layer it targeted.
