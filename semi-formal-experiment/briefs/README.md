# briefs/ — the instruction files the sandwich rule requires

REPRODUCIBILITY.md's sandwich rule, leg 4: every place an LLM (or a person)
exercises judgment inside the pipeline, the instructions it runs under are a
VERSIONED ARTIFACT IN THE REPO — never something that lives only in a
conversation transcript. A step whose brief exists only in a session log is a
reproducibility bug even if it worked once, because the next operator (or the
same operator on a new document) cannot re-run the judgment under the same
rules, and no reviewer can audit what the rules were.

Each brief in this directory is the complete written interface for one
judgment seat: what comes in (a typed artifact), what must come out (a
schema-validated record), the question to be answered and the standard it is
answered against, and what the judge may never see. The deterministic
producer before the seat and the mechanical validator after it live in code;
the brief is the middle of the sandwich.

Current briefs:

- `flip_adjudicator.md` — the dossier→verdict seat of the iteration loop
  (ITERATION_LOOP.md Unit 2; validator: `dossier.py validate`).
- `blind_coder.md` — the two-coder open-coding seat over a frozen loss corpus
  (`hole_corpus.json` in; validators: `check_taxonomy.py`, the transcript
  blindness grep, `taxonomy_agreement.py`; run twice — hole and fabrication
  taxonomies).
- `golden_author.md` — the panel-blind hand-author of
  `golden_translations.json` (validators: `golden.load`'s sha-freeze,
  `test_golden.py`, the reviewer seat).
- `select_audit.md` — the SELECT-step seats: budgeted vocabulary sweep +
  query read-back (validator: `select_audit.py validate`).
- `disagreement_autopsy.md` — the cause-attribution seat over per-
  disagreement audit dossiers (producer: `audit_disagreements.py dossiers`;
  validator: `audit_disagreements.py validate`). ⚠️ The one seat that SEES
  panel verdicts by design — its fence is disclosure, not blindness; nothing
  from it may edit vocabulary/queries/thresholds directly.
- `golden_review.md` — the golden-set audit seat (chain/force/role audit via
  `grammar.parse_name`, factual-correction-not-taste, auditable review
  entries + re-freeze). ⚠️ The one seat that is explicitly for a HUMAN or
  frontier model — it exists to catch the author's mistakes, so the
  small-model standard below does not apply to it.
- `change_reviewer.md` — the cycle driver's IMPLEMENT-gate review seat
  (assignment: `assignments/review.md`, written by `cycle.py`; output:
  `review_verdict.json`): freeze shas, declared-diff-only, tests bind
  (incl. at least one mutant), fence scan. ⚠️ Frontier/careful seat, like
  `golden_review.md` — it exists to catch the implementer's mistakes, so
  the small-model standard does not apply.
- `decision_signer.md` — the cycle driver's DECIDE seat (input:
  `decision.draft.json` with computed fields; output: signed
  `decision.json`): the keep/revert standard (document-side adjudications
  decide; census numbers inform, never decide) and when justification is
  mandatory. ⚠️ Careful seat — a human, or a frontier model under recorded
  authorization; it holds the loop's keep/revert authority.

None of the audit's owed briefs remain outstanding (REPRODUCIBILITY.md,
status audit items 1–3: all resolved).

## The small-model standard (Matt, 2026-08-03)

Every judgment seat is designed to be operable by a Haiku-class model. This
is a CLAIM ABOUT THE SEAT, not about the model: the decisions are atomic and
well inside a small model's range, so **if a small model diverges from a
frontier model on the same brief and the same artifact, the default diagnosis
is a defect in the tooling or the brief** — an ambiguous question, an
under-informative dossier — and the work is to find and fix that defect, not
to upgrade the model. Escalate to "the model can't do this" only after the
brief and artifact have been ruled out.

Operating policy: run seats with a small model by default (cheap, and every
run doubles as a test of the seat's design); periodically replicate a batch
with a frontier model, blinded, and treat any disagreement as a finding about
the seat. First measurement (2026-08-03, containment-v0, 7 flips): Haiku 4.5
vs Opus 5, blinded, **7/7 identical verdicts** — evidence the seat is
well-designed, with the honest caveat that 6 of the 7 flips shared one edge
and the batch had no genuinely borderline call; the discriminating test is a
batch of hard cases (generic-family edges), not yet run.
