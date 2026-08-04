# Adversarial-review hardening notes (seam + re-pin review, 2026-08-04)

Verdict: PASS (full re-closure simulated end-to-end in scratch; all six attack
angles refuted by execution). Non-blocking findings carried forward for a
future tooling batch — neither can fire during the patient-backfill apply
(verified: the backfill produces zero length-1 chains and never scopes b8):

- **F1 — grandfather clause is multiplicity-blind** (test_dechain.py): a NEW
  second instance exactly duplicating one of the five grandfathered length-1
  triples would escape the length>=2 rule (frozen ⊆ live checks membership,
  not live-side counts). Hardening: bound live-side multiplicity of the five
  grandfathered triples to their frozen counts.
- **F2 — "b8 frozen forever" is docstring+gate, not tool-enforced**:
  _check_surfaces accepts ["annotations_b8.json"], and an unscoped rechain
  still legally decorates b8 (required by legacy replay semantics);
  enforcement is post-hoc via test_grammar's b8 pins (which demonstrably
  work — they caused the halt). Hardening option: a deny-list for NEW
  scoped entries naming legacy surfaces.
- F3/F4 (info): over-broad refusal on identity-less replay of non-annotation
  shapes (safe direction); basename-vs-rel asymmetry between the surfaces
  check and split-assignment lookup (pre-existing, split-only).

Also carried: five pre-existing length-1 chains (m0021, m0178, m0179,
m0502 x2) are grandfathered inside the sha-pinned census fixture; whether to
repair them is an open question for a future annotation cycle.

## Change-review findings (cycle review seat, PROCEED, 2026-08-04 — low, non-blocking)

- **R1 — conftest registration outside any manifest**: conftest.py's
  _OPTIONAL entry for test_backfill_worksheet predates OPEN but is named in
  no manifest files_to_change; record it in the CLOSE notes (it rides this
  cycle's commit).
- **R2 — sign-off provenance**: amendment 2's designer sign-off is
  attestation-in-text (coordinator relay + amendment reason), not a
  standalone signed artifact; future re-closures should carry a signed
  file (decision_signer-style) alongside the amendment record.
- **R3 — scope-coherence hardening**: test_backfill_worksheet's live-scope
  check is `live ⊆ frozen`; harden to the exact identity
  `live == frozen − licensed` (derived from verdict_file.json) in the
  future tooling batch, so an over-removal (a non-licensed candidate
  vanishing) also goes RED.
