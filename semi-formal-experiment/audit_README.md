# Atom justification audit — experimenter README

**Do not give this file, or `audit_key.json`, to the rater.** The rater gets exactly two
things: `audit_instructions.md` and `audit_sheet.json` (plus `constitution_clauses.json` as
the source of truth). Everything else in this directory is off limits to them — the
instructions say so explicitly, and it is the experimenter's job to enforce it. If a rater
has already read `vocabulary_pilot.json`, `adversarial_review_1.md`, or this README, their
ratings are not usable.

## What this measures

We have an instrument — "show an auditor an atom's gloss and its supporting quote spans and
ask whether the document justifies it" — whose sensitivity has never been measured. We have
reason to think it may be blind: the project's own known-coined atom carries verbatim,
locator-matched spans and passes every mechanical check. This sheet plants known-defective
items among clean ones to find out whether an auditor catches them.

## Files

| file | audience | contents |
|---|---|---|
| `audit_sheet.json` | rater | 20 items, opaque ids `a01`–`a20`, randomized order, rater-visible fields only |
| `audit_instructions.md` | rater | protocol, Q1/Q2 definitions, worked example (uses an atom not on the sheet) |
| `audit_key.json` | experimenter only | per-item class + defect note |
| `audit_README.md` | experimenter only | this file |

Composition: 15 clean atoms, 5 planted items (2 known-defective atoms carried over from the
project's adversarial review, 3 newly constructed decoys). All 35 quote spans across all 20
items — decoys included — are exact substrings of the clause their locator points to. The
decoys are built to pass mechanical verification; that is the point.

## How to score

**Report the planted-item detection rate first.** Every write-up, table, and summary of this
experiment leads with performance on the 5 planted items. Statistics about the 15 clean
atoms — false-positive rate, agreement, anything — come after, and are never presented as
the headline. The reason: the instrument's value is entirely in whether it catches bad
atoms. A high score on clean items is compatible with total blindness.

### Primary: detection on the 5 planted items, reported separately for Q1 and Q2

Let *P* be the 5 planted items (their ids are in `audit_key.json`).

- **Q1 detection rate** = |{i in P : q1(i) == `model_invention`}| / 5.
- **Q2 detection rate** = |{i in P : q2(i) in {`gloss_asserts_more`, `no_span_licenses_gloss`}}| / 5.

Report both as *k*/5 with the individual item outcomes listed, not just the ratio — with
n = 5 the per-item pattern carries most of the information.

Report per class as well, since the two defect shapes may not be equally detectable:

- `known_coined` + `decoy_nonlicensing_span` (3 items) — the "coined atom" shape.
- `known_overshoot` + `decoy_widened_gloss` (3 items) — the "overshot gloss" shape.

(These overlap the totals above by design; there are 5 planted items in 2 shape families,
with the known/constructed split cutting across.)

Note also the *asymmetry of interest*: for a widened-gloss decoy, `q1 = document_draws_it`
is a **correct** Q1 answer — the document does draw the distinction; only the gloss
overreaches. So a widened-gloss decoy is "detected" by Q2, and Q1 alone should not be
expected to catch it. This is the central comparison the experiment exists to make:

> Does the directed Q2 catch defects that the global Q1 misses?

Compute and report **Q2-only detections** (items where Q2 flagged and Q1 did not) and
**Q1-only detections**. If Q2-only is substantially larger, the proposed fix is doing work.

### Confound to declare in any write-up

Item class `known_overshoot` (`intervene_wellbeing`) is presented unmodified as it stands in
`vocabulary_pilot.json` today, per the build spec. Its gloss already carries a corrective
parenthetical noting what c318 does and does not license. That parenthetical is a strong
cue that the other 19 items do not have. **Report this item's outcome separately and
discount it**, or report the primary rate both with and without it (i.e. *k*/5 and *k*/4).
Do not let it inflate the headline number silently.

### Secondary: the 15 clean atoms

Only after the above. False-positive rate = fraction of clean items flagged by Q1 as
`model_invention`, and by Q2 as `gloss_asserts_more` / `no_span_licenses_gloss`. A rater who
flags everything scores 5/5 on detection and is worthless; the clean-item rate is what
distinguishes sensitivity from indiscriminate suspicion. Report detection and
false-positive rates as a pair, never detection alone.

### Other things worth recording

- `cannot_tell` rate, and whether it concentrates on planted items.
- Confidence calibration: mean confidence on hits vs. misses vs. false positives.
- For Q2, whether the rater's named `licensing_span` matches the one the key says is (or
  is not) doing the work.

## Reproducing / regenerating

The sheet and key were generated together with a fixed shuffle seed and a mechanical
substring + locator check over all spans, which must pass with zero failures before the
files are written. If you regenerate, re-run that check; a decoy whose quote is not an exact
substring of its clause would be detectable by machine and would invalidate the design.
