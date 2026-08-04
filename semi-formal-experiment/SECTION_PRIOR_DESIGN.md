# SECTION_PRIOR_DESIGN — evidence-gated section credit (design, 2026-08-04)

Status: DESIGN ONLY — no code ships with this file. One cycle under
CYCLE_DESIGN.md (amended), shape: code/matching fix, IF the recommendation
survives review. Target class: `fp_section_prior` — 30/294 verdicts in
`audit_dossiers/ext_v1_merged__audit_v1/verdicts_merged.json` (18
avoiding-over-and-under-caution, 12 harm-avoidance-to-third-parties, 0
helpfulness; side: 26 `panel`, 4 `tool`).

## 0. Fitting risk, stated first

**This is one of the two highest-fitting-risk items on the board** (the other
is DRIFT_STANDING_DESIGN.md), and the section channel carries its own relapse
scar tissue in HANDOFF.md:

- A section titled "the section signal is unexploited" was DELETED from
  HANDOFF.md because it functioned as "an instruction to go fit it — exactly
  the drift invariants 9 and 10 exist to prevent", and a reviewer found the
  next funded experiment had been designed to execute it.
- The channel's value is formally UNKNOWN: paired bootstrap for dropping it
  is +0.0217, 95% CI [−0.0118, +0.0557] — spans zero — and `−section` beats
  `full` on helpfulness (HANDOFF.md, "the section channel's value is
  UNKNOWN — do not delete it, and do not claim it helps").
- Lead 2 closed: the section signal is NOT recoverable label-free, and ~40%
  of the supervised section signal "encodes which sections THOSE JUDGES
  treated as relevant... a property of the judges, not of the document".
- The weight 0.45 itself predates every corrected measurement and has no
  standing label-free justification on record.

And the class was named by the census, a panel-reading instrument. Policy
(ITERATION_LOOP.md §1): that directs attention, never truth — recorded here
as this cycle's provenance. The discipline this file follows: **every
candidate rule is stated in §2 below, with mechanism-level predictions in
§3, before any further census or panel consultation**; the keep decision
cites flip adjudications only; census contact waits for the pre-registered
checkpoint and stamps DEV.

## 1. The mechanism, verified against the code

`relevance.py`, class `Weights` (lines 491–492):

```
section: float = 0.45
section_top_k: int = 3
```

`RelevanceIndex.channel_scores` (lines 694–712): each clause first gets its
LOCAL channels — `lex + atom + kind` (kind weight is 0.0). Then, lines
703–711:

- `local[cid]` = sum of the clause's own channels (line 704);
- per section path, `sec[path]` = the mean of the top-`section_top_k` (=3)
  local totals among that section's members (lines 706–709; membership map
  built at lines 568–574 from `section_path`);
- **every member** of the section receives
  `channels[cid]["section"] = 0.45 * sec[path]` (lines 710–711).

So the section channel is pure propagation: a clause with zero evidence of
its own inherits 0.45 × (mean of its 3 strongest section-mates' local
scores), unconditionally. Its own local score participates in the top-k but
is not required to be nonzero, and the credit is identical for every clause
in the section regardless of its own content.

The 30 FPs are exactly this shape. Measured over the 30 dossiers: **24/30
have `atom_channel_zero: true`**; section channel-share runs 0.43–0.96,
median 0.89. Worked example (dossier `...prioritize_teen_safety..._11`,
max clause m0587): atom 0.0, lex 0.082, section 0.580 — share 0.876; no
matched atoms at all; the score is its neighbours'.

## 2. Candidate rules — all stated here, before any consultation

Principle under test: **"the section prior may amplify evidence, never
substitute for it."**

### Is that defensible document-side? The argument, made honestly

For: the adjudication standard this whole loop runs on
(briefs/flip_adjudicator.md) is "would a careful auditor of this behaviour
NEED this clause" — a property of the clause's own text. Section membership
is a fact about the document, and it is legitimate *supporting* evidence: a
borderline match inside `Prioritize safety for teens` is more credibly about
safety than the same match inside a style appendix. But a clause NONE of
whose own content matches the query is being predicted on its neighbours'
words — and "its neighbours concern the behaviour" can never, on a plain
reading, establish that an auditor must include THIS clause. Pure-proximity
admission is indefensible under the loop's own question. HANDOFF Lead 2
supplies the mechanistic version: the only behaviour-specific label-free
signal is the atom index, and section aggregation of it "adds no
information — it re-uses the same clause matches"; when the clause's own
atom evidence is zero, the section channel is not aggregating its evidence,
it is *reassigning other clauses'*.

Against (stated, because it is real): a clause can genuinely concern the
behaviour while its atom coverage is missing — an annotation gap, not an
irrelevance (4 of the 30 FPs were sided `tool`: the census's own autopsy
thought the auditor-need reading supported the tool). m0587 itself
(body-image / disordered-eating boundary for U18) is arguably a
harm-avoidance clause whose atoms (`shouldnot_enable_body_image_harms`)
simply never met the query's names — an `fn_names_cannot_meet` wearing an
`fp_section_prior` costume. Gating section credit on the atom channel makes
the section prior inherit every atom-vocabulary gap. That cost is accepted
and DISCLOSED rather than denied: the fix for missing atom evidence is
vocabulary/annotation work (the backfill route), not score laundering
through neighbours. The flip adjudications will price this: a `regression`
verdict on such a clause is the designed detector, and reverting on a
pattern of them is the designed outcome.

### The candidates

- **Rule A1 — evidence gate (RECOMMENDED).** If a clause's own atom channel
  is exactly 0.0, its section credit is 0.0. Otherwise unchanged
  (`section = 0.45 * sec[path]` as today). "Atom channel" means the credited
  atom total explain() reports — after containment subsumption pricing and
  (if cycle 5 lands) patient pricing — not exact-name-only: a subsumption
  match is the clause's own evidence.
- **Rule A2 — self-cap.** `section = min(0.45 * sec[path], local[cid])`:
  section credit may at most double a clause's own evidence, never exceed
  it. Strictly stronger than A1 (A2 ⇒ A1 since local ≥ atom ≥ 0 and a
  zero-local clause caps at 0)... it is not adopted because it also throttles
  the amplify case A1 deliberately preserves, on no stated document-side
  principle for why the cap is *own-total* rather than 2× or ½× own-total —
  it smuggles a shape choice.
- **Rule B — fractional cap when atom == 0** (`section *= c`, c ∈ (0,1)).
  REJECTED: no label-free principle selects c; any value would be chosen by
  how the census classes move, i.e. swept against the panel — invariant-9
  violation in slow motion. This is the fitting trap named; see §4.
- **Rule C — lower `section` weight globally** (0.45 → something). REJECTED:
  same unselectable-constant problem as B, PLUS it re-litigates a weight
  whose ablation CI spans zero (§0) — there is no label-free evidence the
  channel is net-harmful overall, only that its *substitution mode* is
  indefensible. Touch the mode, not the weight.
- **Rule D — require lex > 0 as the gate instead of atom > 0.** REJECTED:
  lex is near-universally nonzero (smoothed idf, line 563-565 keeps every
  term positive) — the gate would fire almost never; and lexical overlap
  without shared concept is itself the `fp_lexical_only` failure class, not
  evidence worth amplifying.

A1 is recommended precisely because it is **parameter-free**: it introduces
no constant anyone could have tuned. The principle (substitution banned,
amplification untouched) fully determines the rule.

## 3. PREDICT — mechanism-level, checkable with zero panel contact

A key structural fact: A1 changes only the section-assignment step. The
`local` pool (lines 704–709) is computed from lex+atom+kind, which A1 does
not touch — so `sec[path]` is unchanged and **there is no second-order
propagation**: unlike cycle 5's discount (which lowers local totals and
thereby section-mates' credit), A1's effect on each clause is independent
and exactly computable offline. The complete flip set is enumerable at OPEN,
label-free: {clauses with atom == 0 whose total minus section credit falls
below the frozen cut}.

- **Scores only decrease; predicted_new ⊆ predicted_old at the frozen cut.
  `newly_predicted` flips: exactly 0.** Any such flip falsifies the design
  outright.
- **`no_longer_predicted` flips only on clauses with atom channel exactly
  0.0** whose section share carried them over the cut. Anything flipping
  with atom > 0 falsifies the design.
- **helpfulness is NOT a control cell** [amended per PORTFOLIO_REVIEW F5:
  the original control-cell claim here was FALSE]. Zero census FPs of this
  class does not mean zero computed flips: the review's mechanical
  enumeration of the A1 flip set finds **4 helpfulness flips — m0379, m0381,
  m0382, m0389** — despite its highest frozen cut (0.3131). The complete
  computed flip set is **30 = 13 avoiding-over-and-under-caution + 13
  harm-avoidance-to-third-parties + 4 helpfulness**, exactly AT the F4b
  30-flip line. **The per-behaviour split (13/13/4) is pre-registered here
  against that line**: the OPEN enumeration must reproduce it (or re-pin
  with a written delta), and since the total sits at the budget boundary,
  any growth triggers the F4b template rather than a judgment call.
- Dossier-class forecast (checked only at the pre-registered checkpoint,
  DEV-stamped): `fp_section_prior` should shrink substantially — its 24
  atom-zero members are the exact mechanism signature; the 6 with atom > 0
  are NOT expected to move (their section share dominated but the gate
  doesn't fire — a disclosed limit of A1, not a surprise). `fn_*` classes
  may GROW by the §2 "against" mechanism (atom-gap clauses losing their
  proxy) — forecast disclosed now so it cannot be quietly re-narrated later.
- **Hard precondition — the frozen cut.** This is a score-reducing change:
  under a re-derived Otsu the cut would chase the removed mass and
  manufacture drift flips in both directions (the exact m0422 class). The
  cycle's baseline and measure snapshots must both record
  `thresholds_frozen.json` (cycle-4 config, `snapshot.py --thresholds`);
  without it the predictions above are not defined. Same hard gate as
  CYCLE5_DESIGN.md §4.
- **Flip budget (F4b).** The exact flip count must be computed label-free
  and pinned in the OPEN manifest. [Amended per PORTFOLIO_REVIEW F5:] the
  review's computed count is **exactly 30 (13/13/4 per behaviour, above)** —
  at the line, not under it. If the OPEN recomputation lands > 30, the F4b
  template fires: split
  (e.g. per-behaviour sub-cycles) or pre-registered stratified sampling —
  never label-selected sampling.
- Adjudication expectations: most flip-outs expected `correct` under the
  auditor-need question (the clause's own text carries no match); a cluster
  of `regression` verdicts concentrated on atom-gap clauses (the m0587
  pattern) is the designed failure signal and grounds revert or a
  vocabulary-cycle referral — that outcome is a finding, not a process
  failure. [Amended per PORTFOLIO_REVIEW F13: the referral target is NAMED,
  not generic — an m0587 regression refers to **the F13 vocab follow-up
  batch** (the named m0587 vocabulary follow-up that F13 assigns an owner),
  so the referral cannot dissolve into "some future vocabulary work".]

## 4. The value-selection problem — the fitting trap, and the label-free exit

Any rule in the B/C family needs a constant, and there is **no label-free
chooser for it**: a structural argument does not produce a real number in
(0,1); the golden/readback artifacts attest annotation fidelity
(span-support, glosses), not score magnitudes, so they cannot rank c = 0.3
against c = 0.5; and a sweep is a sweep no matter what it claims to
optimize — on this board, every constant that was ever swept was swept
against the panel in effect (HANDOFF's threshold and F1 lessons). The
available label-free choices are therefore exactly:

1. **a principled zero** (A1 — substitution contributes nothing), or
2. **a structurally forced identity** (leave the channel exactly as is), or
3. **defer, stated** — if review rejects A1's document-side argument and no
   parameter-free alternative survives, the correct action is NO CHANGE plus
   a standing-cost disclosure for this class (the DRIFT_STANDING_DESIGN.md
   §2(a) pattern: adjudicate-and-accept the 30, seat pass and error-mass
   line, no tool change). Deferral is a legitimate terminal state of this
   design, and is its fallback recommendation.

Hand-set constants with stated reasoning (the CYCLE5 §1.4 precedent, 0.25)
are tolerated there because *some* discount is structurally required and
zero was rejected on stated grounds. Here zero is not merely available but
is the principle itself — so a fractional constant would be strictly less
defensible than in cycle 5, and is refused.

## 5. Interactions and combined-change ordering

**With patient-taint (CYCLE5_DESIGN.md).** Cycle 5's discount multiplies
credited atom matches by 0.25 — it lowers the atom channel but never zeroes
it (d > 0, and taint applies to matches that exist). Therefore A1's gate
(atom == 0.0 exactly) is **decision-invariant to cycle 5**: the set of gated
clauses is identical before and after patient pricing. Magnitudes are not:
cycle 5 lowers local totals, hence `sec[path]`, hence surviving clauses'
section credit — so the *flip set* of this cycle differs depending on which
baseline it is measured against. **Scope of that invariance claim [amended
per PORTFOLIO_REVIEW F6]: the gated set is invariant to PRICING changes
only (cycle 5's discounts never zero an atom channel). It is NOT invariant
to the decoration-blind join (S1 changes which exact-name matches exist,
hence which atom channels are zero) and NOT invariant to vocabulary
additions (S6 atoms can give a gated clause its first nonzero atom credit).
The 30-flip enumeration in §3 is therefore valid ONLY against the named
post-S3 baseline (cycle 5's keep config, sitting on S1+S2); it does not
survive any later join or vocab change and must be re-enumerated if the
cycle runs after one.** Consequence: the OPEN-pinned flip
enumeration is valid only against a named baseline config — specifically
the post-S3 baseline named in the manifest.

**With containment credits.** Containment prices subsumption matches INTO
the atom channel (`ContainmentIndex`, min-idf × kind_factor). A1 must read
the post-containment atom total: a clause whose only evidence is a licensed
subsumption match has atom > 0 and keeps its section credit. This is
correct — the subsumption credit is the clause's own evidence, and gating on
exact names only would silently punish the overlay's adjudicated wins
(cycles 1–3). Gate test: a clause scored solely via a containment edge must
be un-gated (verify-RED against a mutant reading exact matches only).

**Ordering.** One variable per cycle (F5 two-sided closure), so never
combined with cycle 5 in a single cycle. Recommended order:

1. Cycle 5 first — it is designed, adversarially reviewed, and its §2
   predictions are already pinned against the cycle-4 keep config;
   re-pinning it against a section-gated baseline would waste that review.
2. This cycle second, baseline = cycle 5's keep config (or the cycle-4
   config if cycle 5 reverts — the flip enumeration recomputed and
   re-pinned against whichever, named in the manifest). Its predictions are
   robust to the ordering in *class* terms (the gated set is invariant to
   pricing — and ONLY to pricing, per the F6 scoping above; a join or vocab
   change voids the enumeration outright) but not in *count* terms, which is
   exactly what the manifest pin is for.
3. The checkpoint census runs after both, measuring the combined
   census-class deltas once, DEV-stamped — not per-cycle (F1).

Both cycles are score-reducing under the same frozen cut; neither may
re-derive it (DRIFT_STANDING_DESIGN.md §2(b) governs any cut change).

## 6. Fit to the cycle ceremony

Manifest: description "evidence-gated section credit — section prior may
amplify evidence, never substitute for it (atom-channel gate, parameter-
free)"; document-side rationale §2; `depends_on: cycle4-frozen-cut (closed,
keep)` + named baseline (post-cycle-5 or cycle-4); `census:
deferred_to_checkpoint`; `census_scope: dev`. files_to_change: `relevance.py`
(channel_scores section step only — or a versioned subclass if review
prefers the containment house pattern; either way old behavior reachable,
F9, version recorded in snapshot config), tests. Gate tests, all verify-RED:
zero-atom ⇒ zero-section; atom > 0 ⇒ bit-identical section credit;
containment-credited clause un-gated; monotone-decrease + subset-at-fixed-
cut; F9 reconstruction of pre-gate snapshots. PREDICT: §3 verbatim with the
enumerated flip list frozen at OPEN. review_required: true; §2's
document-side argument and §4's deferral option are the review's agenda.
FORBIDDEN-token check on any new names.
