# PATIENT BACKFILL — targeted chain-completion annotation cycle (design, 2026-08-04, for adversarial review)

One cycle under CYCLE_DESIGN.md (amended form), shape: annotation. The real
fix for the 53% class: a targeted pass over clause atoms whose clause TEXT
licenses a patient the annotation omitted, adding the principal chain the
golden convention says a careful reader should have written. DESIGN ONLY —
no code, no worksheet, no migration ships with this file.

## 0. What this is and is not

The census's `fp_promiscuous_atom` class is 155/294 (53%) of tool-vs-panel
disagreement, and CYCLE5_DESIGN §0 concedes that pricing alone moves 1 of
those 155: ~80% of the class is carried by patient-FREE atoms, and no pricing
rule can read structure that was never written. This cycle WRITES it — where,
and only where, the clause text already says it.

Population, computed 2026-08-04 over annotations_ext_v1_merged (post
chain-repair): **1,442 atom instances over 589 clauses; 109 carry a principal
chain (5 length-1, 101 length-2, 3 length-3) across 100 distinct clauses.**
The chain audit adjudicated all 109 against clause text (97 correct, 12
repaired) — the EXISTING chains are now a clean population. This cycle is the
audit's dual: not "are the written chains right?" but "which unwritten chains
does the text license?"

What it is NOT: a harm-inference pass. The licensing rule (§2) is the
annotation contract's own, verbatim, and its central prohibition — never
infer an affected party from subject matter — is the exact line separating a
chain-completion from a relabeling of the corpus toward what the census
rewarded. Every verdict must quote the clause text naming both parties; a
backfill that cannot quote its license does not land.

## 1. The seat: worksheet + judgment (the chain-audit pattern), NOT an extraction re-run

Two candidate shapes existed; the choice is the design's first commitment.

**Rejected: an extraction-style LLM pass** (annotate.py with a
chain-completion prompt, or re-annotation of candidate clauses). Reasons:
(a) re-running extraction re-rolls everything — names, reuse decisions, span
selection, atom budgets — an uncontrolled many-variable diff, where this
cycle's contract is ONE variable: chains added, nothing else moved. The
one-variable check (F5) could not even state its closure. (b) The extraction
seat is a small-model seat under reuse pressure; chain licensing is a
judgment about who a clause names acting on whom — exactly the class of
judgment the repo reserves for the golden-review tier ("it takes at least
the author's competence to catch the author's mistakes"). (c) No new
vocabulary is needed: the backfill coins NO new stems, no new glosses, no new
spans — only decorations on existing atoms. Extraction machinery buys nothing.

**Chosen: the chain audit's worksheet/verdict pattern with a frontier seat —
the house precedent.** A deterministic producer (`chain_audit_worksheet.py`'s
sibling, extended or parametrized: every candidate instance with clause_id,
full clause text, atom name, gloss, quote span, current parse) → judgment
under a closed schema → mechanical validator → mechanical application via
atom_refactor. The sandwich rule, already exercised at 109 instances in the
chain audit and validated end-to-end by the chain-repair cycle's review
(worksheet independently rebuilt byte-equal; replay byte-identical). The seat
is a frontier model or human, panel-blind and behaviour-blind: the worksheet
carries NO behaviour names, no scores, no predicted sets, no census fields —
clause text and annotation only, so nothing panel-derived can steer which
chains appear.

## 2. The brief — licensing rules, verbatim and binding

The seat's brief quotes the conventions it enforces from the artifacts that
own them; the brief may add procedure but never loosen these:

1. **The golden convention** (golden_translations.json, binding on every
   entry, quoted in briefs/golden_author.md): *"A chain is written ONLY where
   the clause names both an actor and a party the act falls on (or an actor
   other than the assistant)."*
2. **Agent-first order** (grammar.py / annotate_prompt.md): the chain lists
   *"who acts first, then who is acted upon"*; *"slot two is who the act is
   done TO"*. A backfilled chain on a model-act atom is `__model_<patient>`,
   never `__<patient>` — the exact inversion the chain audit just spent a
   cycle repairing (11 of its 12 findings were agent-missing `__user`
   chains). The validator refuses any length-1 addition outright (§4).
3. **Never infer harmed parties from subject matter** (annotate_prompt.md,
   verbatim): *"Write a party ONLY where the clause names one. Do not infer
   an affected party from the subject matter: a clause forbidding an act does
   not thereby name whoever that act would harm."* The worked example is the
   golden set's recorded m0236 correction: the clause prohibits creating
   extremist-praising content but names NO party the act falls on, so
   `__model_third_party` had to go — contrasted with m0223/m0242 where a
   party IS named and the chains stand.
4. **No bare `__model`** (annotate_prompt.md): the acting assistant is the
   default; a chain earns its place only by naming a patient or a non-model
   actor.
5. **No capacity-packing**: parties the clause mentions in other capacities
   (who selected a setting, who benefits) do not enter the chain.
6. **Decoration only.** The seat may not touch stems, polarity, kinds,
   glosses, spans, or atom membership. Anything it believes wrong outside the
   chain is recorded as a `flag` for a future cycle, never edited here.

Verdict schema (closed, chain-audit style): per candidate instance
`{clause_id, name, verdict: chain_licensed|no_chain_licensed|unclear,
corrected_chain: [...principals...]|null, license_quote: "<exact clause text
naming actor AND patient>", reason}`. `chain_licensed` REQUIRES a
`license_quote` that is a substring of the clause text; the validator checks
the substring mechanically. `unclear` is legal and lands nothing.

## 3. Scale — the candidate set, enumerated label-free

Candidates are enumerable from the annotation artifact alone (no census, no
panel, no predicted sets — the enumeration script joins the panel-blind
scanned set):

- **Universe: every chain-free atom instance of kind `act`** — chains
  decorate acts; all 109 existing chained instances are acts. Computed:
  **692 instances across 462 clauses.**
- **Primary stratum: the polarity-marked subset — 505 instances across 347
  clauses** (every polarity-marked chain-free atom in the artifact is an
  act). Deontic acts are where the golden convention's actor+patient pattern
  concentrates; an unmarked act atom ("interject", "coin_tray_jammed"-style
  topics) rarely has a clause-named patient.

Proposed scope: **the full 692**, emitted in deterministic batches with
complete-coverage validation (the check_taxonomy pattern: every candidate
receives exactly one verdict), primary stratum first. This is ~6× the chain
audit's 109 — large for one sitting but not for one cycle, and worksheet
verdicts are not flip adjudications: the 30-flip budget does not apply to
them. If the seat's throughput forces a cut, the cut is the pre-registered
stratum boundary (505 first, remainder as a declared follow-up cycle), never
a hand-picked subset.

Expected yield, honestly unknown: the convention is restrictive (the golden
set deliberately balanced six-of-twelve chained; m0236 shows how often
"obvious" patients are unlicensed). The census-era observation that only 31
of 155 promiscuous max-clauses carried any chain suggests the licensed yield
on harm-relevant clauses may be substantial — but that number directed
ATTENTION here; it licenses nothing per-instance and appears nowhere in the
worksheet.

## 4. Validation

**Mechanical (validator, all-or-nothing before any application):**
- every `corrected_chain` parses under `grammar.parse_name` when formatted
  onto its name; principals ∈ `grammar.PRINCIPALS`; length ≥ 2 OR actor ≠
  model (the golden convention's "actor other than the assistant" arm);
  never a bare `__model`;
- stem and polarity of the decorated name identical to the original
  (rechain's own precondition, checked twice: here and by the tool);
- `license_quote` a verbatim substring of the clause's text;
- coverage: every candidate instance verdicted exactly once;
- FORBIDDEN-token scan on worksheet, verdict file, and every new CLI/field
  name (the `--verdicts` lesson: the flag is `--verdict-file`);
- the golden-author self-check lesson: assert every closed vocabulary, not
  just names.

**Golden review seat (briefs/golden_review.md, frontier or human) —
two-tier:**
- a pre-registered seeded sample of all `chain_licensed` verdicts (proposed
  20%, seed recorded in the manifest), audited against clause text under the
  correction rule ("factual, never taste"); a sampled error rate above a
  pre-registered bar (proposed: any 2 errors in the sample) fails the batch
  back to the seat rather than patching individual entries;
- **100% review, REQUIRED (adopted from CYCLE5_REVIEW and CYCLE5_DESIGN
  Q2), of every backfilled chain landing on: (i) any clause in any current
  predicted set of any DEV behaviour, (ii) any ever-adjudicated-correct
  clause (m0221/m0222 class — a kept cycle-5 taint marks them ×0.25
  forever), (iii) m0248 by name** (the abuse-FN case whose mis-chaining
  `__model_user` would let the taint rule suppress a panel-unanimous
  clause). The predicted-set membership list is computed mechanically from
  the baseline snapshot — the REVIEWER may see it; the verdict seat never
  does.

## 5. Artifact mechanics — rechain expresses add-chain; NO tool extension needed

**Verified against atom_refactor.py, 2026-08-04.** `rechain` operates on
exact decorated names and requires only that both names parse and share stem
and polarity (`_require_rechain_pair`); a chain-FREE name parses with
`principals=[]`, so `rechain <name> <name>__model_user` is a legal
chain-only change — add-chain IS a rechain, no new op required. The
mechanics that matter:

- **Clause-scoped by default for this cycle.** `--clause <id>` (repeatable)
  rewrites only the licensed clauses' usages and folds vocabulary counts
  with merge semantics; clause-blind surfaces (behavior_atoms*,
  containment.json, behaviours_query.json) are untouched — exactly right:
  the license is per-clause, and the query side must NOT be decorated by
  this cycle. The whole-artifact form's guard (`NameExistsError` when the
  target exists) already forces scoping where the target name is in use.
  Whole-artifact rechain is legal only when EVERY clause carrying the name
  received a `chain_licensed` verdict with the same chain.
- **One migration per (name, corrected_chain, licensed-clause-set)**, reason
  citing the backfill verdict file, `--apply --date`, logged and replayable
  in vocabulary_migrations.json — the chain-repair cycle's exact discipline
  (its review replayed all three tracked artifacts byte-identical; the same
  replay check is this cycle's gate).
- **Volume note (non-blocking):** plausibly 50–300 migration entries. The
  replay contract handles any count; if per-entry CLI invocation is the
  bottleneck, a thin batch driver that emits the same log entries is a QoL
  tool change, declared in files_to_change — not a semantics change.
- **Golden entries:** a scoped rechain touching golden_translations.json
  re-freezes with an in-file review record (the tool already does this);
  any such landing additionally requires the golden reviewer's countersign,
  since it edits the standard itself.

## 6. THE JOIN PROBLEM — the prediction "zero flips" is FALSE today, and what makes it true

The task this cycle inherits assumed decoration is score-invariant until
pricing exists. **Computed against relevance.py, it is not:**

- The atom channel matches on EXACT `(name, kind)` (`_atom_score`:
  `nk.get(name)`), and `atom_idf`/`atom_df` are keyed by exact name. **51 of
  the 98 query atom names (behavior_atoms_audit_v1, 3 DEV behaviours) also
  occur as chain-free candidate names in the clause annotation.** Backfilling
  `should_prioritize_safety` → `should_prioritize_safety__model_user` on a
  clause BREAKS that clause's exact match against the chain-free query atom
  (score drops), and splits the name's df (idf of the surviving chain-free
  instances RISES — scores move on clauses the backfill never touched).
  Two-directional movement, before any pricing exists.
- The lex channel tokenizes atom names with underscores split, so adding
  `__model_user` injects "model"/"user" tokens into the clause's lex
  document and shifts corpus df — small, but nonzero and global.

So a prerequisite lands first: the **DECORATION-BLIND JOIN** — a versioned
matcher change under which the atom-channel match key, the atom idf/df, and
the lex atom-text all read the DECHAINED name (polarity + stem; the chain
stripped — polarity is NOT stripped: `must_` vs `mustnot_` staying distinct
is the whole point of the grammar, which is why `stem_of` is the wrong key
here). Chains become pure pricing metadata, invisible to every v1-era
channel; that is arguably what CYCLE5_DESIGN §1.6 already believed
("its chain therefore never enters stem-level matching") — this makes the
belief true. Recorded in snapshot config (fold into the pricing-version
lineage, e.g. `PRICING_VERSION "1.2"`), legacy reachable per the F9
contract, absent-key ⇒ legacy per CYCLE5_DESIGN I5.

The decoration-blind join is its own micro-cycle with its own computed pin:
on the CURRENT artifact it merges df where both variants of a name exist
(computed today: the only chained-clause-atom/chain-free-query coincidence is
`should_ask_clarifying_questions` on m0384/m0385, already exactly matched via
the chained query variant) and removes chain tokens from lex docs — expected
flips ~0, pinned exactly at its OPEN, adjudicated if nonzero.

**With the join in place, this cycle's invariance is a GATE TEST, not a
hope:** a planted add-chain mutant must leave every channel score
bit-identical (verify RED against the current exact-name join, where the
same mutant must move scores).

## 7. Fit to the cycle ceremony

- **Shape:** annotation-artifact change run under the driver's existing
  discipline, the chain-repair precedent: `files_to_change` = the annotation
  artifacts + vocabulary_migrations.json (+ the worksheet/verdict artifacts
  under `cycles/<name>/`), closure pinning behaviours_query.json,
  behavior_atoms*, containment.json, thresholds_frozen.json, and the query
  modules unchanged. (cycle.py's annotation-cycle variant remains an
  extension point; chain-repair showed the code-shape ceremony carries an
  artifact-only change fine.)
- **PREDICT (the shape of the prediction): ZERO FLIPS.** Score-invariant by
  construction under the decoration-blind join: flip_count {min: 0, max: 0},
  no directions, no regressions — the chain-repair cycle's exact prediction
  shape, measured there as 0/0/0 PASS. **Any flip falsifies the join
  contract and is a BUG in the join, not a judgment call about the
  backfill** — the cycle halts and the join micro-cycle reopens. Nothing
  here is adjudicated by flips because nothing may move; the judgment
  content of this cycle lives in the verdict file and its golden review
  (§4), which is where review effort goes.
- **Gate tests:** the §6 bit-identity mutant test (verify RED); replay
  byte-identity for every touched artifact; validator completeness; the §4
  golden-review artifacts present and passing before IMPLEMENT closes;
  `snapshot.assert_frozen_thresholds` on both snapshots (the frozen-cut
  regime stays asserted even in a zero-flip cycle).
- **Census:** `deferred_to_checkpoint`, `census_scope: dev`. This cycle's
  provenance is disclosed as census-seeded (the 53%/31-chain figures
  directed attention here); no census number appears in worksheet, verdicts,
  or the keep decision.
- **DECIDE:** keep = (validator clean) ∧ (golden review clean) ∧ (measured
  zero flips). A revert of any individual chain later (e.g. a cycle-5
  adjudication finds a backfilled chain wrong) is ONE rechain migration
  back, cited to that adjudication — the population is repairable
  chain-by-chain without reverting the cycle.

## 8. Joint sequencing with cycle 5

The ladder, superseding CYCLE5_REVIEW's ordering (which predated the §6
finding and the zero-flip construction):

1. **Decoration-blind join micro-cycle** (§6). Tiny, computed pin, expected
   ~0 flips. Without it, neither the backfill's zero-flip prediction nor
   cycle 5's "chains never enter matching" premise is true.
2. **This backfill cycle.** Zero flips by construction; all judgment in the
   verdict + golden-review artifacts.
3. **Amended cycle 5** (CYCLE5_DESIGN rev 2, §7): prices the full backfilled
   population in one adjudication — the real effect, with per-flip chain
   provenance (repair-era vs backfilled) pre-registered as the
   stratification if the flip volume exceeds the 30 budget.

Why not cycle 5 first (the review's ladder): before the backfill it is a
1/155 fix (CYCLE5_DESIGN §0), it spends the under-18 adjudication on a
rehearsal population, and its stated purpose — measuring the backfill
through an adjudicated mechanism — is empty once the backfill is
measurement-invariant: there is nothing to measure until pricing lands, and
pricing lands exactly once, last, confounded with nothing. The cost accepted:
cycle 5's first contact with reality is the large population, so its flip
volume is real; the budget path is pre-registered there, not improvised.

Tension stated for review: sequencing the backfill before any pricing means
its chains are landed by a seat that KNOWS (from this design's existence)
that user-patient chains will later discount harm-behaviour matches. The
blinding answer: the verdict seat sees no behaviours, no scores, no predicted
sets, and must quote its license from clause text; the golden review
re-checks exactly the clauses where a wrong chain would matter most (§4).
Whether behaviour-blindness plus quoted licenses is enough insulation — or
whether the backfill should also be authored before cycle 5's constant and
rule are finalized, so no one can chain toward a known discount — is a
question the joint portfolio review should attack.
