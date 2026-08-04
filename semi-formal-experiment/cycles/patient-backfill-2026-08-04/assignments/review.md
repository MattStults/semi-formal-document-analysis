# Change review assignment — cycle patient-backfill-2026-08-04

Seat brief: briefs/change_reviewer.md — read it first; it is the seat's
entire instruction. This is a frontier/careful seat: it exists to catch the
implementer's mistakes, so the small-model standard does not apply.

Change under review (from the manifest):

- fix_description: THE PATIENT BACKFILL (spine cycle S2; BACKFILL_DESIGN.md as amended per PORTFOLIO_REVIEW.md F10i) — a targeted chain-completion annotation pass, run under the code-cycle ceremony per the chain-repair precedent (artifact-only change). A deterministic worksheet generator (backfill_worksheet.py, the chain_audit_worksheet.py sibling) enumerates every chain-free act-kind atom instance of annotations_ext_v1_merged.json label-free: 692 instances across 462 clauses, primary stratum = the polarity-marked subset (505 instances across 347 clauses), emitted primary-first. A behaviour- and panel-blind frontier seat (briefs/backfill_author.md — SILENT on pricing, discounts and every design document per F10i) verdicts each candidate under the closed schema {chain_licensed | no_chain_licensed | unclear} with a mandatory verbatim license_quote (validator-checked substring of the clause text) for every chain_licensed verdict; the validator additionally enforces coverage-exactly-once, principal-vocabulary and parse round-trip of every corrected chain, length >= 2 (no length-1 addition, the chain-audit agent-missing lesson), stem+polarity immutability (decoration only), and the FORBIDDEN-token scan on worksheet, verdict file and all new CLI/field names. Validated chain_licensed verdicts are then applied as clause-scoped atom_refactor rechain migrations (chain-free name -> decorated name, one migration per (name, corrected_chain, licensed-clause-set), --apply --date, logged and replayable in vocabulary_migrations.json — the chain-repair discipline); behavior_atoms_audit_v1.json and every query-side artifact are untouched (the license is per-clause; the query side is NOT decorated by this cycle). Zero flips by construction under the S1 decoration-blind join (pricing_version 1.2): chains are pricing metadata invisible to every channel.
- document_side_rationale: The annotation contract's own licensing convention, verbatim and binding (golden_translations.json, quoted in briefs/golden_author.md): 'A chain is written ONLY where the clause names both an actor and a party the act falls on (or an actor other than the assistant).' The chain audit (chain-repair-2026-08-04, KEEP) adjudicated all 109 EXISTING chains against clause text; this cycle is that audit's dual — which unwritten chains does the clause text license? Every landed chain must quote its license verbatim from the clause; the central prohibition (annotate_prompt.md, verbatim in the seat brief): 'Write a party ONLY where the clause names one. Do not infer an affected party from the subject matter.' NOT a harm-inference pass and NOT a relabeling toward anything panel-derived: the seat sees clause text and annotation only — no behaviour names, no scores, no predicted sets, no census fields, no pricing. Provenance disclosed: the census's fp_promiscuous_atom figures directed ATTENTION to this population; no census number appears in the worksheet, the verdicts, or any keep decision. Document-side only.
- files_to_change: annotations_ext_v1.json, annotations_ext_v1_merged.json, annotations_ext_v1_patch.json, backfill_worksheet.py, briefs/backfill_author.md, vocabulary_migrations.json
- gate_tests: test_backfill_worksheet.py, test_dechain.py, test_atom_refactor.py, test_grammar.py, test_no_reference_leak.py

Required output: review_verdict.json in this cycle's directory:

    {"verdict": "proceed" | "blocked",
      "by": "<who reviewed — never the implementer>",
      "notes": "<what was verified, or why blocked>"}

All three keys are REQUIRED; verdict is a CLOSED set. The driver re-checks
the frozen manifest/prediction shas, the two-sided one-variable check and
the gate tests mechanically; your seat verifies what the machine cannot
(see the brief: freeze shas, declared-diff-only, tests bind — at least one
mutant — and the fence scan). A "blocked" verdict halts the cycle until
resolved and re-reviewed.

---

## Cycle-specific addendum (operator, at the IMPLEMENT review halt)

This is an ANNOTATION-artifact cycle run under the code ceremony
(chain-repair precedent). Beyond the brief's standing duties (freeze shas,
declared-diff-only, tests bind — plant at least one mutant — fence scan),
this cycle asks the seat to verify:

1. **The amendment chain (manifest_amendments.json, 4 entries).** Entries
   1 and 3 are manifest amendments (surface discovery; legacy-file
   withdrawal) chaining f9f3a5cd… → b3f0ed95… → b5706377…. Entries 2 and 4
   are RE-CLOSURE records (state.json closure_shas edits): entry 2 was
   designer-approved and adversarially reviewed (tooling seam + test_dechain
   re-pin); entry 4 (test_backfill_worksheet.py scope-pin repair,
   007994151ed3 → 861ebc042c65) was OPERATOR-EXECUTED at the gate and needs
   your explicit countersign or block — verify the repaired test weakens no
   assertion (all four scope counts now pinned against the frozen worksheet,
   sha ce26cf89…, plus a live-coherence subset check).
2. **The apply.** 139 surface-scoped rechain migrations
   (backfill/apply_rechains.py, deterministic), 1,324 rewrites over exactly
   annotations_ext_v1 / _patch / _merged; 264/264 licensed pairs decorated,
   zero licensed pairs left chain-free, 428/428 non-licensed pairs
   untouched; log 144 entries (5 legacy-unscoped + 139 scoped), gap-free.
3. **Replay + legacy freeze.** All five annotation surfaces replay
   BYTE-IDENTICAL from pre-apply copies through the mixed log; annotations.json
   / annotations_b8.json / golden_translations.json / behavior_atoms_audit_v1
   byte-untouched (shas in the operator report). Suggested mutant: strip one
   entry's `surfaces` field and watch b8 replay diverge.
4. **The zero-flip pre-proof.** The measure snapshot was pre-built with the
   driver's exact command into snapshot_build/ (the driver will reuse it at
   MEASURE): vs baseline decoration-blind-join-2026-08-04 — 0 flips,
   thresholds and predicted sets identical (95/73/146), vocabulary 624→624
   with 0 df shifts, every non-config snapshot section bit-identical, only
   config.inputs.annotations differs, pricing_version 1.2 both sides.
5. **Seat-chain integrity.** worksheet.json unchanged since the seat
   assignment (sha echoed in backfill/verdict_file.json, validator CLEAN,
   264/425/3); RULINGS.md + verdict_file_v1.json record the golden review
   and sweep; the brief passes scan_brief (F10i silence).
