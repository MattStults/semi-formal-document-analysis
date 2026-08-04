# Golden-translation reviewer brief

You review `golden_translations.json` after the author seat
(`briefs/golden_author.md`) has produced it: audit every atom against its
clause text, correct factual errors, and re-freeze. **This seat is for a HUMAN
or a frontier model, explicitly** — it is the exception to the repo's
small-model standard (`briefs/README.md`). The reference is the standard every
later score is measured against; an error that survives review teaches the
scorer to punish correct extractors, and the whole point of the seat is to
catch the author's mistakes, which takes at least the author's competence. A
small model may not hold this seat.

The reviewer MAY be panel-exposed (the recorded Model Spec review entry is
signed "lead (panel-exposed)"), because the correction rule below confines the
review to facts checkable against the clause text alone. What a panel-exposed
reviewer may never do is use that exposure: no edit is licensed by how the
panel scores a clause or by what the tool currently predicts.

## The audit

For every entry, against the entry's own `quote` (the exact clause text):

1. **Chain audit.** Parse every atom name with **`grammar.parse_name` — never
   a hand-rolled split.** The principals tuple is matched longest-first
   precisely because `third_party` contains the separator character and a
   left-to-right split on `_` tears it in half (`grammar.py`'s own comment); a
   hand-rolled split did exactly that in an earlier review pass and produced
   two false findings before being caught. Then check each parsed chain
   against the convention stated in the artifact: a chain is written ONLY
   where the clause names both an actor and a party the act falls on. A chain
   whose patient the clause never names is an error even when the harm it
   implies is real (the recorded m0236 correction is the worked example: the
   clause prohibits creating extremist-praising content but names NO party the
   act falls on, so `__model_third_party` had to go).
2. **Force audit.** Each polarity prefix must be stated by the clause; an
   unmarked name means "no force stated" and must stay unmarked. `must_` vs
   `mustnot_` inversions are the highest-severity error class.
3. **Role audit.** `condition` / `exception` / `consequent` / `topic` against
   the clause's actual trigger structure; absent where the clause states none
   (definitions, controls).
4. **Controls.** The control entries must carry no prefix, no chain, no role —
   that absence is their content.
5. **Coverage claims, independently.** Re-derive the author's own claims
   rather than believing them: the chain balance ("six of twelve carry a
   chain"), the structural cells each half covers, one control per half, the
   split matching `golden.seeded_split(ids, seed)`, every `span_id` resolving,
   every atom name parsing clean. Script it; do not eyeball it.

## The correction rule: factual, never taste

You correct an entry ONLY where it is factually wrong against the clause text
or violates the artifact's own stated conventions. You do not re-word glosses
you would have phrased differently, swap in atoms you find more elegant, or
re-litigate the author's judgement calls where the text supports them. The
recorded review entry states its own scope — "factual correction only, not a
taste edit" — and that phrase is the standard. A reviewer with taste edits and
panel exposure is a channel; a reviewer with factual corrections and cited
clause text is an audit.

## The review entry and the re-freeze

Every change is an auditable record appended to the entry's `review` list —
the change is never silent:

```json
{"by": "<who, with their exposure declared, e.g. 'lead (panel-exposed) — factual correction only, not a taste edit'>",
 "change": "<what was changed, concretely>",
 "why": "<the clause-text evidence, citing the artifact's own convention it violated>",
 "not_recoverable_addendum": "<optional: anything real the correction removed that the grammar cannot mark>"}
```

The `why` must argue from the clause text and the artifact's conventions,
optionally contrasting entries where the same construct is correct and kept
(m0236's entry contrasts m0223 and m0242, where a party IS named and the
chains stand). If the correction removes something true-but-inexpressible,
record it in `not_recoverable_addendum` rather than losing it — that feeds the
same gap report the author owes.

Then RE-FREEZE: recompute `sha256` with `golden.compute_sha256` over the
edited payload, write it into the file, and land edit + hash in the same
commit with the reason in the commit message — `golden.load`'s error text is
the procedure ("if it genuinely needed to change, rebuild the hash in the same
commit and say why the old translation was wrong"). An artifact whose hash was
rebuilt without a review entry explaining why is a freeze that got switched
off.

## What validates the output

- `golden.load()` passes on the re-frozen file; `pytest test_golden.py -q`
  clean.
- Every edit made in the review is paired with a `review` entry (diff the
  artifact against its pre-review version and check one-to-one).
- The independent coverage re-derivation (audit step 5) is reported with the
  review, so the author's `selection_criteria` claims are checked, not
  inherited.
