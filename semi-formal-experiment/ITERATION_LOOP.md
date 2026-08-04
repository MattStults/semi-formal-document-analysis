# The iteration loop — spec

Goal (Matt, 2026-08-03): make ontology changes cheap, safe and adjudicable —
"change → rerun → see what newly succeeds or fails → debug each flip → keep or
revert" — with tooling mechanical enough that a Haiku-sized model can operate
it, and with vocabulary changes made refactor-safe (find usages, migrate
artifacts, never silently break old ones). Built iteratively, starting from
debugged examples like `DISAGREEMENT_REPORT.md`.

## The design in one picture

```
           ┌────────────── INNER LOOP (label-free, run at will, $0) ─────────────┐
 change →  snapshot → diff vs baseline → flip list → dossier per flip →          │
           adjudicate each flip AGAINST THE DOCUMENT (schema-constrained) →      │
           keep/revert citing document-side evidence ────────────────────────────┘
                                    │ (rate-limited, pre-registered)
           ┌────────────── OUTER LOOP (measurement) ────────────────────────────┐
           │ panel MCC / ranking AUC, reported with CIs, never steered on       │
           └────────────────────────────────────────────────────────────────────┘
```

The inner loop never touches the panel. Its diff object is **tool-vs-tool**
(yesterday's outputs vs today's), which is fully label-free: "which
query→clause matches appeared or disappeared" is a fact about the tool, not
about any gold. Flip adjudication asks the *document* question — "does this
clause actually concern this behaviour's subject matter, on a plain reading?" —
not the panel question.

## ⚠️ The policy (Matt, 2026-08-03): labels direct ATTENTION, never TRUTH

Supersedes the earlier (a)/(b) fork, and resolves the 2026-08-03 adversarial
review's finding 1 (candidate provenance) by design rather than by fence:

1. **Candidates from anywhere, provenance recorded.** A change may be
   motivated by debugging a panel disagreement (labels making the audit
   efficient). Every change records where it came from. Labels are NOT
   trusted: adjudication may find the panel wrong.
2. **Every delta, adjudicated.** A change is evaluated on its COMPLETE flip
   set — both directions, no sampling by default — against the DOCUMENT,
   under the written brief. Keep/revert cites only document-side reasons.
   Label values never appear in a dossier or a keep decision.
3. **The tight, symmetric question.** The adjudication standard is "would a
   careful auditor of this behaviour need this clause", plus edge validity
   for containment flips ("is the subsumption valid in THIS clause's use"),
   applied with equal force to additions and removals. Cut-drift flips (score
   unchanged, threshold moved) are tagged and adjudicated as such — their
   question is about the threshold, not the clause. This is the guard against
   the volume ratchet: a loose question, not label-peeking, was the real
   convergence mechanism the review identified.
4. **A big delta is a finding.** If a change produces more flips than can be
   exhaustively adjudicated (guideline: ~30), the change is too coarse —
   split it. Pre-registered stratified sampling (by behaviour × direction ×
   flip-cause) is the fallback, never label-selected sampling.
5. **DEV / TEST split, effective now.** The 3 frontier Model-Spec cells are
   DEV: they may prioritize debugging and track iteration, and their numbers
   are dev numbers — inflated by selection, never quotable as results. The
   constitution cells (and any future behaviours) are HELD-OUT TEST: never
   consulted during iteration, evaluated only at pre-registered checkpoints.
   The constitution cells are clean today because they have never been used
   for anything; keeping them clean is the point.

   **Amendment (Matt, 2026-08-04): behaviour generalization outranks
   document transfer.** New behaviours are the common case (the user's input
   surface — users specify the behaviour they study); new specs are the rare
   case (producer-side, iterated before others depend on them), and every
   hard failure so far has been behaviour-shaped. So after the current fix
   ladder closes on the 3 DEV behaviours, the next evaluation phase is the
   6 never-consulted small-panel Model-Spec behaviours, run as a FROZEN-
   PIPELINE generalization test: pipeline config frozen first; each new
   behaviour processed fully label-free (definition into behaviours_query →
   SELECT → sweep/readback audit → mechanical re-selection → snapshot);
   their small-panel cells consulted EXACTLY ONCE at a declared evaluation,
   labelled by roster (gpt-mini/haiku/qwen-small — a weaker panel, never
   "the bar") on the panel_universe-reconstructed universe with the
   score-1-irrecoverable caveat stated. The census seats then measure
   whether error-class distributions transfer. These 6 cells are neither
   DEV nor sealed TEST: they are the GENERALIZATION SET, burned once.
   The constitution stays parked as sealed TEST (plus the two expert
   salience anchors), unlocked only at a final pre-registered battery.
6. **Fallback, explicit.** If exhaustive delta adjudication proves too
   expensive in practice, the fallback is Matt's to invoke — demote further
   toward dev-set iteration knowingly, never by drift.

## Components, in build order

### Unit 1 — `snapshot.py`: freeze, diff, flip list  (label-free core)
- `snapshot <tag>`: run the tool offline over every behaviour with atoms;
  record per-clause raw scores, channel decomposition, predicted sets,
  vocabulary stats, config hashes (annotations sha, weights, threshold rule,
  overlay shas). Write `snapshots/<tag>.json`. Deterministic: same inputs,
  byte-identical snapshot.
- `diff <tag_a> <tag_b>`: per behaviour, the flip lists (newly-predicted,
  no-longer-predicted), each with score before/after and the channel that
  moved. Plus vocabulary-level diff (atoms added/removed/renamed, df shifts).
- HARD FENCE: imports relevance/benchmark loaders for clauses only — never
  panel verdicts. Static-scan clean against FORBIDDEN; it is a query-adjacent
  module and must stay panel-blind.

### Unit 2 — `dossier.py`: one flip → one self-contained case file
Generalizes `case_fn.json` shape, minus panel fields: clause text, atoms,
rendering, explain() before/after, what changed. A dossier must contain
EVERYTHING an adjudicator needs — the Haiku-operability contract is:
  dossier in → verdict out, no repo exploration required.
Verdict schema (closed): `{flip_id, verdict: correct|regression|unclear,
document_reason, confidence}` — validated mechanically, coverage-checked
(`check_taxonomy.py` pattern: every flip adjudicated exactly once).

Amendments from the Unit 2 build (2026-08-03):
- The verdict-file CLI flag is `--verdict-file`, never `--verdicts` — the
  plural is a FORBIDDEN token (it names per-judge panel labels) and the fence
  is stricter than the spelling. Future units: check FORBIDDEN before naming
  any CLI surface.
- `confidence` is accepted but OPTIONAL; only flip_id/verdict/document_reason
  are required.
- A dossier's clause text / atoms / rendering come from the AFTER (b) side,
  falling back to a if the clause vanished; both sides' matched atoms remain
  visible via explain_a/explain_b.
- Snapshots record input basenames, so dossier resolves them against
  `--inputs-dir` (default: the repo dir) and FAILS LOUDLY on a sha mismatch
  rather than dossiering against drifted artifacts. A hand-edited snapshot is
  therefore self-exposing: its reconstructed explain_b will not match its
  frozen score_b.

### Unit 3 — `atom_refactor.py`: rename / merge / split with migrations
- `usages <atom>`: every reference across annotations*, behavior_atoms*,
  golden_translations, containment overlay, query configs — the "find
  references" of this codebase.
- `rename <old> <new>` / `merge <a> <b> → <b>`: mechanical rewrite of all
  usages + an entry in `vocabulary_migrations.json` (old, new, date, reason,
  artifact shas before/after). Migrations REPLAY: an old artifact is migrated
  forward by applying the log in order — that is the backwards-compatibility
  contract. `stem_of`-style identity checks pin that unmigrated names are
  untouched.
- `split <atom> <a,b>`: cannot be mechanical — emits a per-usage worklist
  (clause text + gloss + quote per usage) for adjudication, same schema
  discipline as dossiers. Applies only a complete, validated worklist.
- Golden set entries are sha-frozen: a refactor touching golden re-freezes
  with the migration recorded in the artifact's own history block.

### Unit 4 — overlays: change the MATCHER without re-annotation
First worked example: containment (`containment.json`: licensed ⊑ edges +
provenance per edge). The matcher consults the overlay behind a flag; scoring
at most-specific-common-subsumer priced by the SUBSUMER's idf. Runs against
the EXISTING b8 annotations — zero model calls — so Unit 1 diffs measure its
effect exactly. Edge licensing (amended per the Unit 4 build): a parsed
polarity prefix or principal chain ANYWHERE on child or parent rejects the
edge outright — not merely residual-modifier checking, which as first written
would have licensed `mustnot_X ⊑ X` after stripping; residual modifier tokens
are additionally checked against polarity stems, principals, and negations.
Sample of edges golden-reviewed against glosses before first use.

Amendment (2026-08-03, the v1 pricing fixes — adversarial-review
requirements for any widening of the edge set, shipped and kept in cycle 2):
- **Credit is a matching, not a product**: each query atom is credited at
  most once (its best match) and each clause atom likewise — killing the
  query-sibling multiplication where one clause atom was priced once per
  family sibling in the query.
- **Kind factor with the min-idf cap**: subsumption credit is
  `min(idf(subsumer), idf(clause_atom)) * kind_factor`, with kind agreement
  checked where kinds are recorded and discounted where a latent parent
  makes it uncheckable — so a subsumption match can never outprice the exact
  match on the same evidence (the never-outprice invariant).
- **Required budget**: the overlay file must declare `budget`
  {max_edges, max_families} and stay within it; a file without (or over) its
  budget is rejected, so edge-set growth is always a visible diff of the
  budget, never silent accretion.
- **One-child-family rejection**: a family with a single attested child gives
  the latent parent the child's own df — an alias, not a generalization —
  and is rejected outright.

Known blockers before live-iteration step 4 (from the Unit 4 build report) —
both RESOLVED 2026-08-03 in the review-fix round:
- ~~`dossier._side` verifies an overlay snapshot's sha but rebuilds a PLAIN
  index~~ FIXED: `_side` rebuilds through ContainmentIndex with the recorded
  (sha-verified) overlay edges, and every dossier now carries a build-time
  self-check — the reconstructed side's explain score must equal the frozen
  score at snapshot.PRECISION or building raises ReconstructionMismatch
  naming clause, side, and both numbers.
- ~~`relevance.explain()` names only exact-name matches~~ FIXED:
  `ContainmentIndex.explain()` adds `subsumption_matches` — one
  {query_atom, clause_atom, subsumer, subsumer_idf} record per priced
  subsumption match — so dossiers name the licensing edge behind a flip.

## The case bank

Every adjudicated dossier is retained under `casebank/`. Regression pins
derived from it must be MECHANISM pins (document-side facts: "the containment
closure connects psychological_manipulation to targeted_political_manipulation
via the manipulation family"), NEVER outcome pins ("m0216 must be predicted
relevant") — an outcome pin is a relevance label, and fitting to it is fitting
to labels no matter who authored them.

## Order of first live iteration (after Units 1+2 exist)

1. `snapshot baseline` on today's configuration.
2. Containment overlay v0: the `manipulation` family edge only.
3. `snapshot containment-v0`; `diff baseline containment-v0`.
4. Dossier + adjudicate every flip (expected: very few; the family has two
   members). Keep or revert on the adjudications.
5. Only then: widen the edge set family-by-family, same loop each time.

Standing rules apply unchanged: TDD with verify-RED, new test files registered
in `conftest._OPTIONAL`, adversarial review before anything paid, and this
whole apparatus is $0 until a re-annotation is proposed.

## Cycle log

- **Cycle 1 (2026-08-03): `baseline-2026-08-03` → `containment-v0`** — the
  two manipulation-family edges. 7 flips, all `newly_predicted` on
  harm-avoidance-to-third-parties. Two adjudicators, blinded to each other
  and to all labels (Opus 5 and Haiku 4.5), **7/7 identical verdicts**: 6/6
  substantive flips correct (edge valid in each clause's use), 1
  threshold-drift regression (m0422) kept knowingly as a standing cost class
  charged to the Otsu cut, not the edges. **KEEP.** Decision:
  `dossiers/baseline-2026-08-03__containment-v0/decision.json`. Status:
  SUPERSEDED by cycle 2 — and v0's overlay bytes no longer exist on disk (the
  in-place-edit lesson now recorded in REPRODUCIBILITY.md's determinism
  bullet), so v0 is not reconstructable.
- **Cycle 2 (2026-08-03): `baseline-2026-08-03` → `containment-v1-pricing`**
  — same edges plus the pricing fixes (Unit 4 amendment above). 3 flips vs
  baseline, blinded Haiku adjudication, validator clean 3/3: m0221 and m0222
  correct, m0422 regression (threshold drift again — 2nd occurrence, watch
  the cut rule). **KEEP**: strictly better than baseline, and the pricing
  guards are review requirements for any future widening. Known cost: 4
  clauses lost vs v0 (m0216, m0217, m0218, m0220 — dropped by the latent-kind
  discount)
  whose cycle-1 adjudications stand as document-side evidence auditors need
  them; **v1.1 queued** — unanimous-child kind inheritance, to be built,
  snapshot, diffed and adjudicated like any change. Decision:
  `dossiers/baseline-2026-08-03__containment-v1-pricing/decision.json`.
- **Cycle 3 (2026-08-03): `baseline-2026-08-03` →
  `containment-v1.1-kindinherit`** — v1.1 built (PRICING_VERSION 1.1,
  unanimous-child kind inheritance; guard tests verified against an
  over-broad mutant; never-outprice invariant unweakened). The v1→v1.1 diff
  is exactly the 4 lost clauses returning at an unchanged cut. Adjudicated vs
  baseline: 7 flips, a FRESH Haiku blinded to all prior verdict files —
  **identical to cycle 1's verdicts** (6 correct, m0422 regression), so the
  seat has now replicated across three independent blinded runs. **KEEP —
  the shippable configuration.** Decision:
  `dossiers/baseline-2026-08-03__containment-v1.1-kindinherit/decision.json`.
  Standing escalations recorded there: (a) m0422 drift-admitted in ALL THREE
  cycles → the Otsu cut rule is formally under suspicion; a cut-stability
  diagnostic gates any overlay widening; (b) historical snapshots made under
  older pricing code DIFF fine but cannot be DOSSIERED (the reconstruction
  guard fires, correctly, twice now) — dossier only current-code snapshots;
  (c) `diff_snapshots` does not yet surface `pricing_version` in
  `config.changed` (v1.2 follow-up).
