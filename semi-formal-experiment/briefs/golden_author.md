# Golden-translation author brief

You hand-author the reference translations in `golden_translations.json`: a
small set of clauses from the document, each paired with the atom set a
careful reader SHOULD produce under the notation in `grammar.py`. The file is
a STANDARD, not a sample — when a later run says "the extractor translated
this clause correctly", correctness means agreement with your file (scored by
`golden.py`, graded matching anchored on `grammar.stem_of`).

## Why this seat exists

Every automated score of the extractor is circular unless something in the
repo says what the RIGHT answer is, written by a hand that was not looking at
what the extractor produced or at what the panel rewards. This is that hand.
It is also the seat that discovers, clause by clause, what the grammar CANNOT
say — which is not a side effect but a primary deliverable (see the gap-report
duty below).

NO MODEL IS CALLED to produce any atom, gloss or split in this file. A model
asked to author the reference would be grading its own homework
(`golden.py`'s standing rule). The Model Spec run's provenance line is the
template: "hand, panel-blind; no model was called to produce any atom, gloss
or split in this file".

## What this seat may never see

- **Every panel / gold / ranking artifact** — `behaviours.json`,
  `../data/panel-coverage.json`, `panel_universe.py`, `panel_v2.py`,
  `benchmark.py` outputs, coverage numbers, behaviour artifacts. Why: the
  golden set is used to evaluate the same pipeline the panel evaluates; an
  author who knows which clauses the panel scores high, or which clauses the
  tool currently gets wrong, will select and translate toward that knowledge,
  and no later audit can measure how much got through.
- **The extractor's own annotations** (`annotations*.json`,
  `behavior_atoms*.json`) and any per-clause tool output. Why: the reference
  must encode what the CLAUSE says, not a cleaned-up version of what the
  extractor said.

The Model Spec run's recorded allowlist — the ONLY files opened: the clause
corpus (`modelspec_clauses.json`), `grammar.py`, `annotate_prompt.md`,
`annotate.py`'s loader/schema, and `extract_section.candidate_spans`. A new
document's author opens the analogous five and nothing else, and records the
list in the artifact's `selection_criteria`.

## Selecting the clauses

The recorded criteria (`golden_translations.json`, `selection_criteria`) are
the standard; reproduce their logic, not necessarily their ids:

1. **From the clause TEXT alone.** Grep the corpus for the surface markers of
   each structure the grammar exists to encode, then read the hits. No
   ranking, coverage, panel or behaviour artifact is opened.
2. **One cell per structure, selected as pairs.** Plain obligation,
   prohibition, permission, "must not X unless Y", a default stated
   exception-first, "X. However, Z", rules naming who acts on whom (both a
   two-link and a three-link chain). Structural PAIRS, because the split
   (below) sends one member of each pair to each half — so a failure mode
   cannot hide behind a structure one half happens to lack.
3. **Controls with none of the structure** — a bare definition and a topical
   statement whose correct translation carries no prefix, no chain, no role.
   They are the only way to measure OVER-marking; without them an extractor
   that decorates everything scores well on the rest. One control per half.
4. **Spread across the document's sections** (six sections in the Model Spec
   run), so the set is not a portrait of one drafting style.
5. **Spread across the segmentation's `kind` labels**, since the extractor
   sees that label and may behave differently under each.
6. **Short enough to translate exactly** (~340-character cap in the Model
   Spec run): a reference translation of a long clause is a summary, and
   disagreement with it would measure summarisation rather than encoding.

## The principal-chain convention

Verbatim, from the artifact, and binding on every entry:

> A chain is written ONLY where the clause names both an actor and a party
> the act falls on (or an actor other than the assistant).

A bare `__model` is never written: every clause in a model spec is about the
model, so the lone chain carries no information while costing the reader a
claim the clause did not make. Deliberately balance the set — in the Model
Spec run, six of the twelve carry a chain and six do not. The same discipline
applies to force prefixes and roles: mark ONLY what the clause states
(`annotate_prompt.md`'s rule: marking structure the clause does not state is a
worse error than leaving it off).

## Entry shape and split

Each entry: `clause_id`, `locator`, `section_id`, `kind`, `quote` (the exact
clause text), `structure` (which structural cells it covers), `split`, `atoms`
(each with `name`, `kind`, `gloss`, `span_id`, optional `role`, and the exact
`quote` span), `recoverable`, `not_recoverable` (see below), and an initially
empty `review` history for the reviewer seat.

**Dev / held-out split, seeded and stratified.** The split is computed by
`golden.seeded_split` from a recorded seed over the structural pairs: one
member of each pair to dev, the other to held-out, so both halves cover every
structure (including one control each). A hand-picked split can be picked to
flatter; the recorded seed is the proof it was not. Precedent worth keeping:
the Model Spec run tried an unstratified shuffle first, it put both controls
in dev, and the METHOD was changed, not the seed. Dev may be iterated
against; held-out may be scored once, as a final evaluation, ever —
`golden.py` enforces this with `HeldOutAccessError` and the
`final_evaluation=True` flag whose only purpose is to make the decision
appear in the caller's diff.

**The sha-freeze.** The finished artifact carries `sha256` over its own
canonical-JSON content (`golden.compute_sha256`), and `golden.load` refuses a
file whose content and hash disagree. Without that, the cheapest way to raise
a score is to edit the reference, and the edit leaves no trace. Any later
change re-freezes in the same commit and says why the old translation was
wrong (the reviewer brief covers the procedure).

## The gap-report duty — report what the grammar cannot express

For every entry you MUST fill two fields:

- `recoverable`: what a reader of the atoms alone would correctly learn.
- `not_recoverable`: what the clause says that the atom set CANNOT carry,
  stated concretely enough that a grammar designer could act on it.

This is not an apology footer; it is the seat's most valuable output. In the
Model Spec run the author's consolidated report of the grammar's expressive
gaps — degree modifiers ("strive to" decoding as strict requirement),
value-bounding trade-offs ("while striving to be helpful"), inter-atom
elaboration/scope-extension, alternative-vs-joint exceptions, enumerations
surviving only inside glosses, implied-but-unnamed parties, orderings needing
relations between atoms — fed directly into the notation and relation-layer
planning, and mattered more than the twelve translations themselves.
[TO CONFIRM: the consolidated 8-gap report exists only in the authoring
session's transcript; the per-clause raw material survives in the artifact's
`recoverable`/`not_recoverable` fields. When this brief is next exercised, the
consolidated report is written to a repo file, not a transcript.]

## What validates the output

- `golden.load()` — the freeze check, plus schema via `test_golden.py`
  (span resolution, budget, split integrity: run `pytest test_golden.py -q`).
- ⚠️ YOUR OWN SELF-CHECK MUST COVER EVERY CLOSED VOCABULARY, not just names.
  Before delivering, programmatically assert: every `kind` is one of
  situation / act / entity / value; every `role`, where present, is one of
  condition / exception / consequent / topic; every name parses under
  `grammar.parse_name` with no error. A calibration author once delivered 14
  atoms whose names all parsed while every `kind` was an invented word
  ("behavior", "concept") — the name check alone proves nothing about the
  fields around it.
- The seeded split is recomputable: `golden.seeded_split(ids, seed)` must
  reproduce the recorded `dev`/`held_out` lists.
- The reviewer seat (`briefs/golden_review.md`) audits every chain, prefix
  and role against the clause text, and independently re-checks the coverage
  claims made in `selection_criteria` — nothing in this file is done until
  that review has run.
