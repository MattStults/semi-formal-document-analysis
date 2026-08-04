# New-document runbook

The end-to-end order for pointing the pipeline at a document it has never
seen. Written 2026-08-03 to discharge REPRODUCIBILITY.md debt item 4, BEFORE
any second document has run the full chain.

**⚠️ HONESTY BANNER — UNTESTED RUNBOOK.** Only the OpenAI Model Spec has ever
run steps 2–7. The Anthropic constitution has run step 1 only
(`constitution_clauses.json`, 616 clauses, loads today, never used for
anything — it is HELD-OUT TEST under ITERATION_LOOP.md policy §5). Every step
below marked UNTESTED is transcribed from how the Model Spec run worked, not
from a second execution. The constitution run is intended to debug this
document and amend it in place; treat a divergence between this file and
reality as a bug in this file, fix it here, and note the amendment.

Standing guards for every step: `--dry-run` is the default on every live
script (going live is `--live`, an explicit decision); every live call logs to
`usage.jsonl`; `spend.py` holds the hard budget cap and audits for unlogged
spend. Pre-flight any paid step with
`.venv/bin/python spend.py --would-cost <provider> --batches <n>` and check
headroom with `spend.py --check`.

---

## Step 0 — source freeze

- **Command:** record the document file and its sha256 in the clause artifact
  (`spec` + source sha fields, as `modelspec_clauses.json` and
  `golden_translations.json` both do).
- **Artifact:** the source document, pinned.
- **Validator:** the sha, re-checked by whatever consumes it.
- **Budget:** $0.

## Step 1 — segment into addressable clauses

- **Command:** the structural parser in `segment_modelspec.py` (its docstring:
  "The same parser runs on Anthropic's constitution, which carries no markers
  at all"). Unit model: paragraph / list item / example block / commentary
  paragraph, `¶` numbering restarting per heading. [TO CONFIRM: the exact CLI
  invocation for a non-Model-Spec source — `segment_modelspec.py main()` takes
  no arguments and writes `modelspec_clauses.json`; the constitution
  segmentation shipped as `constitution_clauses.json` with the same schema,
  but the command that produced it is not recorded as a repeatable CLI. A
  third document will need a documented entry point; write it when the
  constitution run touches this step.]
- **Artifact:** `<doc>_clauses.json` — `{"spec": ..., "clauses": [{id,
  locator, section_path, quote, kind, ...}]}`. VERSIONED FILENAME per
  document; never overwrite another document's clause file.
- **Validator:** character-coverage report (Model Spec: 97.35%); every clause
  loads under the shared schema (`measure_join.clause_rows` /
  `panel_universe` joins for documents that have a panel; for a new document,
  schema-load plus coverage is the check).
- **Judgment seat:** none at run time — mechanical. The unit-model choices are
  editorial and documented in `segment_modelspec.py`'s docstring and
  `segmentation_summary.md`.
- **Budget:** $0 (no model calls).
- **Status: executed on both documents.** The only step that has run twice.

## Step 2 — classify clause kinds

- **Command:** hand assignment per clause into the closed set {conditional,
  holistic, definitional, meta, example}, criteria as in
  `modelspec_kinds.py`'s docstring and `segmentation_summary.md`
  ("Assignments were made by reading each clause, not by pattern-matching").
  For the Model Spec this is `modelspec_kinds.py` (the RAW block is the
  record); the constitution's kinds shipped inside `constitution_clauses.json`
  with its segmentation.
- **Artifact:** `kind` on every clause row.
- **Validator:** every clause carries exactly one kind from the closed set;
  `example` assigned mechanically to fenced example blocks where the format
  has them.
- **Judgment seat:** the kind assigner. ⚠️ NO BRIEF EXISTS for this seat yet —
  the criteria live in `modelspec_kinds.py`'s docstring, which is
  seat-adequate but not in `briefs/`. If the constitution kinds need
  revisiting, write `briefs/kind_classifier.md` first.
- **Budget:** $0 as run so far (human seat).
- **Status: UNTESTED as a repeatable procedure** — both existing kind sets
  were produced ad hoc; neither run followed a written protocol.

## Step 3 — annotate: clause → atoms

- **Command:**
  `.venv/bin/python annotate.py --clauses <doc>_clauses.json
  --docfacts docfacts_<doc>.md --provider luna
  --out annotations_<doc>_<version>.json --live` (dry-run first, without
  `--live`, and read the cost print).
- **⚠️ THE DOCUMENT-FACTS BLOCK, before anything else.** REPRODUCIBILITY.md's
  rule: instruction files separate PROCEDURE (how to annotate, any document)
  from DOCUMENT FACTS (this document's authority levels, its principals), and
  the procedure file never names a specific document's ontology.
  **DONE 2026-08-03**: `annotate_prompt.md` is now document-agnostic, with
  `{{DOCFACTS:...}}` markers that `annotate.load_template` fills from a
  per-document facts file — `--docfacts` on the CLI, default
  `docfacts_model_spec.md` (the default composition is pinned byte-identical
  to the pre-split prompt in `test_annotate.py`, so no shipped behaviour
  changed). `docfacts_constitution.md` exists (with `[TO CONFIRM]` items on
  encoding Anthropic-as-principal and the `developer`→`operator` alias) but
  is UNTESTED by a live run. For a third document: write
  `docfacts_<doc>.md` supplying every block the markers name (its authority
  levels, its principal names, its terminology corrections) and pass it via
  `--docfacts`; the prompt tests in `test_annotate.py` (ENUMERATES,
  retired-principal, invariant 8) bind on the composed prompt.
- **Artifact:** `annotations_<doc>_<version>.json` (+ failure JSONL +
  `prompt_log/`). Versioned filename, never an in-place edit — see
  REPRODUCIBILITY.md's determinism bullet for why (the un-dossierable
  containment-v0 incident).
- **Validator:** annotate's own rejection machinery (schema, span-id lookup,
  rate cap ≤2.78 atoms/clause and gloss budget via `apply_rate_cap`, coverage
  report), plus `annotate.verify_demonstrations()` (frozen synthetic demos,
  sha-pinned).
- **Brief (judgment seat):** `annotate_prompt.md` — the LLM extractor's
  instructions, versioned in-repo.
- **Budget guard:** dry-run default; measured-cost pre-flight
  (`calibrate.py`, `spend.py --would-cost`); hard cap `spend.BUDGET`.
- **Status: UNTESTED on a second document** (and blocked on the
  document-facts split above).

## Step 4 — behaviour atoms: behaviour → query, selected from the vocabulary

- **Command:**
  `.venv/bin/python behavior_atoms.py --behaviours <behaviours_for_doc>.json
  --annotations annotations_<doc>_<version>.json --out
  behavior_atoms_<doc>_<version>.json --live` (dry-run first; `--notation` /
  `--draws` as the run design requires).
- **Artifact:** `behavior_atoms_<doc>_<version>.json`.
- **Validator:** selection-from-vocabulary — every selected atom must exist in
  the annotation vocabulary (the Model Spec b8 run: 100% in-vocabulary);
  coined-atom cap (`--max-new`); failure log.
- **Brief (judgment seat):** `behavior_atoms_prompt.md` (+
  `behavior_atoms_notation_prompt.md` for the notation-aware variant).
- **Budget guard:** dry-run default; `spend.py` as above.
- **Status: UNTESTED on a second document.**

## Step 5 — snapshot the baseline

- **Command:**
  `.venv/bin/python snapshot.py snapshot --tag <doc>-baseline-<date>
  --clauses <doc>_clauses.json --annotations annotations_<doc>_<version>.json
  --atoms behavior_atoms_<doc>_<version>.json --queries <queries file>`.
- **Artifact:** `snapshots/<doc>-baseline-<date>.json` — per-clause scores,
  channel decomposition, predicted sets, config shas, input basenames.
- **Validator:** determinism (same inputs → byte-identical snapshot,
  `test_snapshot.py`); the recorded input shas make any later drift
  self-exposing (`dossier.py` fails loudly on sha mismatch). Consequence:
  every artifact a snapshot consumes gets a VERSIONED FILENAME from here on —
  an in-place edit of a consumed artifact permanently orphans every snapshot
  that recorded the old sha.
- **Judgment seat:** none — mechanical and panel-blind (HARD FENCE,
  ITERATION_LOOP.md Unit 1; scanned by `test_no_reference_leak.py`).
- **Budget:** $0.
- **Status: UNTESTED on a second document** (the machinery itself is
  exercised — three Model Spec snapshots exist).

## Step 6 — read-back: does the representation describe the document?

- **Command:** `.venv/bin/python readback.py --live --out
  readback_results_<doc>_<version>.json` (dry-run first; deterministic
  renderer + faithful/sufficient/discriminable harness).
- **Artifact:** `readback_results_<doc>_<version>.json`; then
  `prep_hole_corpus.py` (pointed at that artifact — [TO CONFIRM: its RESULTS
  path is currently hardcoded to `readback_results.json`; parameterise or
  copy-in when running a second document]) → a frozen `hole_corpus` for the
  new document.
- **Validator:** the harness's own metrics + the anti-cheat scan (readback is
  in `QUERY_MODULES`); then the two-coder protocol — `check_taxonomy.py`,
  transcript blindness grep, `taxonomy_agreement.py`, cross-coder-stability
  reporting rule.
- **Briefs (judgment seats):** `readback_prompt.md` for the read-back judge;
  `briefs/blind_coder.md` for the two loss-taxonomy coders.
- **Budget guard:** dry-run default; `spend.py`.
- **Status: UNTESTED on a second document.**

## Step 7 — golden set for the new document

- **Command:** no script — two seated judgment passes under written briefs:
  author (`briefs/golden_author.md`: text-only selection, structural pairs,
  controls, principal-chain convention, seeded stratified dev/held-out split,
  gap report), then reviewer (`briefs/golden_review.md`: `grammar.parse_name`
  chain audit, factual-correction-not-taste, auditable review entries,
  re-freeze). Human or frontier-model seats; the reviewer seat is explicitly
  never a small model.
- **Artifact:** `golden_translations_<doc>.json` — new file, new seed, new
  sha; never widen the Model Spec artifact.
- **Validator:** `golden.load` (sha-freeze), `test_golden.py`, recomputable
  `seeded_split`, the reviewer's independent coverage re-derivation.
- **Budget:** $0 API (hand-authored by design).
- **Status: UNTESTED on a second document.**

---

## After the runbook

Iteration on the new document only begins once steps 1–7 are green: the
iteration loop (ITERATION_LOOP.md) diffs against the step-5 baseline, and
its adjudication seat runs under `briefs/flip_adjudicator.md`. Remember the
DEV/TEST split: if the new document was reserved as held-out test (the
constitution is), running this pipeline on it is itself a pre-registered
event, not a casual experiment.
