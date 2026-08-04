# The reproducibility principle

Goal (Matt, 2026-08-03): the whole pipeline — ontology building, spec
extraction, behaviour extraction, evaluation, iteration — must be runnable
again on NEW documents and NEW behaviours without archaeology. Every step is
either mechanical, or an LLM step with a written interface. Almost always
both: deterministic tooling with a well-defined seam where the LLM plugs in.

## The sandwich rule

Every pipeline step ships as FOUR artifacts, or it is not done:

1. **A deterministic core** — typed artifacts in, typed artifacts out,
   byte-reproducible (same inputs → same bytes; no wall clock, no hash-seed
   dependence — the snapshot harness found and now guards that class).

   Corollary (2026-08-03, learned the hard way): artifacts consumed by
   snapshots get VERSIONED FILENAMES, never in-place edits. The containment
   overlay was edited in place (adding the budget field for v1), so the bytes
   snapshot `containment-v0` recorded no longer exist on disk and that
   snapshot is permanently un-dossierable — `dossier.py`'s stale-sha guard
   fired, correctly; the artifact practice was the bug, not the guard. A
   config change is a NEW file (`containment_v1.json`, not an edited
   `containment.json`); the old bytes stay put so every snapshot that pinned
   them stays reconstructable.
2. **A closed interface for judgment** — where an LLM (or a person) must
   exercise judgment, the interface is a schema, not a conversation:
   dossier in → verdict out; batch of clauses in → atoms out. Small closed
   vocabularies, required fields, stable ids.
3. **A mechanical validator** — the LLM's output is checked by code before it
   is used: coverage (every id exactly once), schema, sha-pins, budget.
   `check_taxonomy.py`, `dossier.py validate`, annotate's rejection machinery
   are the pattern.
4. **An instruction file IN THE REPO** — the prompt/brief the LLM runs under
   is a versioned artifact (like `annotate_prompt.md`), never something that
   lives only in a conversation transcript.

The LLM is always sandwiched: deterministic producer → LLM under written
instructions → deterministic validator. A step where the model's output flows
onward unvalidated, or whose instructions exist only in a session log, is a
reproducibility bug even if it worked once.

## Document-agnostic vs document-specific

Instruction files must separate PROCEDURE (how to annotate, any document)
from DOCUMENT FACTS (this document's authority levels, its principals). The
2026-08-03 audit found `annotate_prompt.md` teaching Model-Spec-specific
facts ("root vs system", "there is no platform") inside the general
procedure — harmless on the Model Spec, false teaching on the constitution.
Rule: document facts live in a per-document block/file the harness splices
in; the procedure file never names a specific document's ontology.
RESOLVED for annotation 2026-08-03: `annotate_prompt.md` carries
`{{DOCFACTS:...}}` markers, filled by `annotate.load_template` from
`--docfacts` (default `docfacts_model_spec.md`; `docfacts_constitution.md`
written, untested live). The default composition is pinned byte-identical
to the pre-split prompt, and the prompt guards in `test_annotate.py` bind
on the composed prompt for both docfacts files.

## Status audit (2026-08-03)

Already compliant:
- **Annotation**: `annotate.py` + `annotate_prompt.md` + rejection/validation
  + spend guards + sha-pinned frozen demos. The reference example.
- **Behaviour atoms**: `behavior_atoms.py` + `behavior_atoms_prompt.md`
  (+ selection-from-vocabulary validation).
- **Query / threshold / benchmark / renderer**: fully mechanical.
- **Read-back**: deterministic renderer + `readback_prompt.md` + harness.
- **Iteration loop** (compliant as of 2026-08-03): snapshot/diff/dossier
  deterministic; verdicts schema-validated; built Haiku-operable by design.
  The 2026-08-03 adversarial review caught this entry listed compliant while
  the adjudicator's brief (leg 4) was still missing — the loop's code legs
  existed but its judgment seat ran on transcript-only instructions, which
  is exactly the violation class below. Resolved the same day:
  `briefs/flip_adjudicator.md` + `briefs/README.md` now exist, and the
  verdict schema is enforced by `dossier.py validate`.
- **Segmentation**: one-off scripts kept with provenance (MODULE_MAP §6).

Violations / debt (each is a session-transcript-only procedure today):
1. ~~**The blind-coder method**~~ RESOLVED 2026-08-03: `briefs/blind_coder.md`
   now carries the two-coder protocol as actually run twice (corpus-in shape,
   bottom-up induction, kinds-not-topics, the blindness list with reasons,
   coverage self-check, output schema, and the verification chain —
   `check_taxonomy.py`, transcript blindness grep, `taxonomy_agreement.py`,
   cross-coder-stability reporting rule). Listed in `briefs/README.md`.
2. ~~**Golden-set authoring and review**~~ RESOLVED 2026-08-03:
   `briefs/golden_author.md` (selection criteria, principal-chain convention,
   seeded split, sha-freeze, the report-what-the-grammar-cannot-express duty)
   and `briefs/golden_review.md` (parse_name chain audit,
   factual-correction-not-taste, auditable review entries + re-freeze,
   independent coverage re-derivation; explicitly a human/frontier-model
   seat). Listed in `briefs/README.md`.
3. ~~**Flip adjudication**~~ RESOLVED 2026-08-03: `briefs/flip_adjudicator.md`
   now carries the adjudicator instructions (verdict semantics, the tight
   symmetric auditor-need question, the edge-validity and threshold-drift
   variants, the no-label-values rule), with `briefs/README.md` describing
   leg 4 itself. Moved to "Already compliant" above.
4. **New-document runbook**: WRITTEN 2026-08-03 (`NEW_DOCUMENT_RUNBOOK.md`)
   but **UNTESTED** — steps 2–7 have never executed on a second document, and
   the runbook says so per step. It stays in this debt list until the
   constitution run has executed FROM it and amended it in place; only then
   does it move to "Already compliant".

## The rule for new work

A fix or feature is in-principle done only when its step conforms to the
sandwich rule. Reviews (including the standing adversarial reviews) should
flag transcript-only procedure as a finding, same severity as a missing test.
