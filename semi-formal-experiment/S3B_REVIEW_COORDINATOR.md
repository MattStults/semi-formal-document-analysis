# S3B_REDESIGN.md — coordinator review (2026-08-04)

Not the clean-context adversarial review the design still requires (§0, §9) — this is
the coordinator's read before that review is commissioned. Verdict: **the design is
sound in its diagnosis and should proceed to adversarial review, with two BLOCKING
findings fixed first.** Both are internal contradictions, not disagreements about
direction.

## B1 (blocking) — the design document is a contamination vector for the seat it specifies

§5.1 fences the attribution seat to "clause text + gloss + the golden chain convention
only… never a panel artifact, a judge rating, or a gold value". That fence omits the
**S3 cycle record and this design document**, both of which name the answer key:
§7.1 pre-registers that m0275, m0239 and m0466 must return to `predicted`, and §1/§4
walk through the correct attribution for each. An attributor who reads S3B_REDESIGN.md
(or `flip_verdicts.json`, or the dossiers) is being handed the outcomes it is supposed
to derive independently — which collides head-on with §6's own invariant, "the
attribution MUST NOT be fit to flip outcomes".

**Fix:** add to the blindness fence, explicitly: `S3B_REDESIGN.md`, the S3 cycle
directory (`flip_verdicts*.json`, `flip_dossiers/`, `decision.json`,
`ADJUDICATION_LEGS.md`), and the census. The attribution brief must be written
standalone (S2's `briefs/backfill_author.md` precedent: it never mentioned pricing),
FORBIDDEN-token scanned, and the §7.1 restore-check must be run by a party the
attributor never talks to, **after** attribution is frozen.

## B2 (blocking) — §5.4 as written can resurface m0276, which §7.2 makes an automatic revert

§5.4 offers the structural guard as belt-and-braces that "does not depend on D1", i.e.
shippable before attribution: *a matched patient-free situation atom is never discounted
solely because a sibling model-act atom is user-directed.*

m0276 (self-harm — the canonical census false positive, and the single clearest thing
S3 got right) was suppressed for a third-party query through exactly that path: its
match runs through **patient-free** atoms (`human_safety`, `intervene_in_danger`) and its
suppression came from sibling user-bearing atoms. Under §5.4 alone, that suppression is
withdrawn and m0276 plausibly returns — which §7.2 defines as REVERT "regardless of all
else". §5's own preservation claim ("their harm-bearing atoms attribute the USER as
harm-bearer") is true only **once attribution exists**, so it cannot justify §5.4 in the
pre-attribution window.

**Fix:** either drop §5.4 as an independent step and make the whole mechanism
attribution-gated, or state (and test) that §5.4 ships only with m0276/m0290 pinned as
controls and is reverted if either re-surfaces. Do not present it as independently
justified.

## Non-blocking findings

- **N1 — the design fixes the fix, but never re-checks the original target.** S3b is
  scoped to `fp_promiscuous_atom` (155 cases) but every piece of evidence in it is one of
  the 4–5 S3 regressions. S3 itself only converted ~2 canonical cases (m0276, m0290).
  Before OPEN, estimate how much of the 155 beneficiary attribution actually reaches —
  otherwise S3b may be an expensive correction to a mechanism whose *upside* was never
  large. This belongs in §7 as a pre-registered expected-recovery figure, not discovered
  at MEASURE.
- **N2 — D5 (attribution population) is unbounded.** S2's backfill was 692 candidates and
  consumed a full cycle with four seats. Harm-bearer attribution over patient-bearing
  *and* patient-free harm-describing atoms could be larger. Enumerate before D1 is ruled:
  the population size is an input to the (a)-vs-(b) delivery choice, not a detail after it.
- **N3 — §4A-A-structural's only controls are m0276 and m0290.** Two clauses is thin for a
  rule with corpus-wide reach; pair it with the S2 golden-review pattern (stratified
  sample of affected clauses) rather than two pinned cases.
- **N4 — good, keep:** §3's statement of the wall (the separator lives in the atom's gloss
  text, not in chain metadata) is the design's best paragraph and the reason the S3
  post-mortem is trustworthy; §2's explicit carry-forward list, §7.2's
  automatic-revert-on-resurface, and §8's refusal to let D1 default are all correct
  discipline.

## Recommendation

Fix B1 and B2 in the draft, then commission the clean-context adversarial review. D1 is
genuinely load-bearing and should be ruled by the designer *with* N2's population count in
hand — leaning (a), annotation-side, matches the project's discipline and stays
rechain-repairable, but that lean should survive knowing what it costs.
