# SECTION_PRIOR_DESIGN — evidence-gated section credit (design, 2026-08-04)

Status: DESIGN ONLY — no code ships with this file. One cycle under
CYCLE_DESIGN.md (amended), shape: code/matching fix, IF the recommendation
survives review. [REVISION 2026-08-05 per S4_ADVERSARIAL_REVIEW.md (verdict
REVISE): the blocking finding and all four majors are resolved inline, each
marked at the change site; minors fixed or explicitly deferred with a named
owner. The items the review verified correct (baseline log-read, A1 flip
enumeration, `section_gate_version` key spec in its verified respects) are
NOT re-opened.] [REVISION 2 2026-08-05 per S4_ADVERSARIAL_REVIEW_R2
(verdict REVISE: 0 blocking, 3 majors, 9 minors): majors E1 and S1 and all
nine minors are resolved inline, each marked at the change site with
`[per S4_ADVERSARIAL_REVIEW_R2 <id>]`. Rule A1, the pinned
`max_regressions: 0`, and the 13/13/4 flip enumeration are UNCHANGED — the
review was explicit that A1 itself needs no change. Major **E2** (the
gate-OFF construction parameter's reachability) is ACCEPTED but DEFERRED
pending the in-flight config-driven index-builder refactor; §6 carries a
marked placeholder and it must be resolved before OPEN.] Target class: `fp_section_prior` — 30/294 verdicts in
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
as this cycle's provenance. **Fuller provenance, stated out loud [added per
S4_ADVERSARIAL_REVIEW_R2 S4]: the gate PREDICATE is also the census's own
discriminator** — `atom_channel_zero` is computed at
`audit_disagreements.py:248`, in a module whose docstring reads
"PANEL-READING, DIAGNOSTIC-ONLY — in the anti-cheat FORBIDDEN set". This is
a disclosure, not a violation, and the direction of the choice matters: the
census's `fp_section_prior` SIGNATURE is "section is the dominant channel
share" (`audit_disagreements.py:131–137`), and A1 deliberately does NOT use
that predicate — using it would have required a share threshold, i.e.
exactly the swept constant §4 refuses. Choosing atom-zero over the class's
own signature is the more principled selection; saying so is a stronger
disclosure than silence. The discipline this file follows: **every
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

Principle under test: **"the section prior may amplify a clause's own ATOM
evidence, never substitute for it."** [Wording narrowed per
S4_ADVERSARIAL_REVIEW SCI-m1: evidence is operationalized as the atom
channel only, not evidence-in-any-sense, and the narrowing is load-bearing
— on the baseline, 506/510 (caution), 530/533 (harm), 442/451
(helpfulness) of the gated (atom == 0) clauses carry positive lexical
self-evidence, so the original wording read as if lexical self-evidence is
not evidence, a larger claim than the argument makes. The grounds for
atom-only operationalization are HANDOFF Lead 2 — the atom index is the
only behaviour-specific label-free signal — and Rule D below: lexical
overlap without shared concept is itself the `fp_lexical_only` failure
class, not evidence worth amplifying.]

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
  section credit may at most double a clause's own local total, never
  exceed it. NOT strictly stronger than A1 — [corrected per
  S4_ADVERSARIAL_REVIEW ENG-M2: the original "A2 ⇒ A1" lemma was FALSE;
  the two rules are INCOMPARABLE. A2 zeroes section credit only where
  LOCAL (= lex + atom + kind, kind weight 0.0) is zero; an atom-zero
  clause with positive lex keeps positive section credit under A2 — the
  design's own worked example decides it: m0587 (atom 0.0, lex 0.0819,
  ungated section 0.5803) gets section 0.0 under A1 and min(0.5803,
  0.0819) = 0.0819 under A2. Conversely A1 does not imply A2 either: A2
  throttles the amplify case A1 deliberately preserves (an atom-positive
  clause whose section credit exceeds its local total is capped under A2,
  untouched under A1).] A2 is rejected on the independent ground that
  follows, which stands without the lemma: it throttles that amplify case
  on no stated document-side principle for why the cap is *own-total*
  rather than 2× or ½× own-total — the cap constant smuggles a shape
  choice. (The recommendation is unaffected: the correction removes a
  false lemma, not a reason.)
- **Rule B — fractional cap when atom == 0** (`section *= c`, c ∈ (0,1)).
  REJECTED: no label-free principle selects c; any value would be chosen by
  how the census classes move, i.e. swept against the panel — invariant-9
  violation in slow motion. This is the fitting trap named; see §4.
- **Rule C — lower `section` weight globally** (0.45 → something). REJECTED:
  same unselectable-constant problem as B, PLUS it re-litigates a weight
  whose ablation CI spans zero (§0) — there is no label-free evidence the
  channel is net-harmful overall, only that its *substitution mode* is
  indefensible. Touch the mode, not the weight. **Scale disclosure [added
  per S4_ADVERSARIAL_REVIEW_R2 S3]: "the mode" is most of the channel.**
  Measured on the log-resolved baseline, A1 removes 71.9% (caution) /
  75.3% (harm) / 64.8% (helpfulness) of ALL section-channel mass in the
  corpus — 22.8% / 27.2% / 4.4% of the section mass on the predicted set —
  gating 510 / 533 / 451 of 593 clauses per behaviour. The Rule-C
  rejection stands (A1 is content-conditioned where a weight change is
  not, and it leaves the amplify case bit-identical), but a reader is owed
  the magnitude, especially given §0's admission that the channel's
  aggregate value is UNKNOWN.
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
label-free — and it is defined on the NORMALIZED surface predictions are
decided on, not the raw surface [`rank()` divides every raw score by the
corpus raw max, relevance.py:780–783; the snapshot records exactly those
normalized scores against the frozen cut]: {clauses with atom == 0 whose
normalized total minus their section credit's normalized contribution
falls below the frozen cut}. The raw-space shorthand "total minus section
credit" coincides with this exactly because the normalization denominator
is unchanged — see the corpus-max condition pinned below [reworded per
S4_ADVERSARIAL_REVIEW SCI-M1].

- **Corpus-max condition — pinned check at OPEN [added per
  S4_ADVERSARIAL_REVIEW SCI-M1].** A1 monotonically decreases RAW scores;
  normalized scores decrease too ONLY IF the corpus-max clause is not
  gated — if it were (atom == 0), the normalization denominator drops and
  every surviving clause's normalized score RISES, producing
  `newly_predicted` flips with the mechanism working exactly as designed.
  The subset and zero-new-flip predictions below are therefore CONDITIONAL
  on the corpus-max clause of every behaviour having atom > 0. That is an
  empirical envelope fact, not a mechanism necessity: verified on all
  extant baselines — the CONDITION (atom > 0) holds in every case, and the
  OPEN enumeration must assert it **per behaviour, against whichever
  clause is corpus-max on the baseline actually resolved, never against
  pinned clause ids** [corrected per S4_ADVERSARIAL_REVIEW_R2 E8: the
  prior text pinned "m0527 / m0592 / m0438", but helpfulness's corpus-max
  is `m0384` on `chain-repair-2026-08-04` and `versioned-cut-2026-08-04`
  and `m0438` only on the 1.2 lineage; the ids are not stable across
  baselines even where the condition is]. The assertion must pass before
  the flip list is pinned. A future baseline that violates the condition
  (post-vocab, per the §5 F6 scoping) voids this section's predictions the
  same way a join or vocab change does — re-enumerate on the normalized
  surface and re-pin with a written delta; that event is a scoping
  trigger, not a falsification.
- **Scores only decrease — conditional on the corpus-max check above;
  predicted_new ⊆ predicted_old at the frozen cut. `newly_predicted`
  flips: exactly 0.** Any such flip, WITH the corpus-max check passing,
  falsifies the design outright (with it failing, the re-pin path above
  applies instead).
- **`no_longer_predicted` flips only on clauses with atom channel exactly
  0.0** whose section share carried them over the cut. Anything flipping
  with atom > 0 falsifies the design.
- **Sharper, label-free characterization of the flip set — additionally
  pre-registered [added per S4_ADVERSARIAL_REVIEW_R2 S2].** On the
  log-resolved baseline the number of PREDICTED clauses with `atom == 0.0`
  is **13 / 13 / 4** (caution / harm / helpfulness) — identical to the
  flip counts, per behaviour. Every predicted atom-zero clause flips out;
  none survives. So at the frozen cut A1 is exactly equivalent to *"do not
  predict any clause with zero atom evidence"*, which is strictly stronger
  than the bullet above (that one permits atom-zero survivors) and is
  mechanically checkable label-free. Pre-registered as such: the OPEN
  enumeration must reproduce `predicted ∧ atom == 0` = the flip set
  exactly, or re-pin with a written delta. It also sharpens the disclosed
  cost honestly — the `fn_names_cannot_meet` exposure named in §2 is
  co-extensive with the flip set, not a subset of it, and A1 is therefore
  a large scorer change ("require atom evidence to predict"), not a narrow
  one.
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
  [Noted per HANDOFF.md S4 ruling 3 (2026-08-04): this split was
  independently recomputed against the log's then-latest closed-KEEP
  snapshot (the post-S2 keep) and found IDENTICAL — same 30 flips, same
  four helpfulness clause ids (m0379/m0381/m0382/m0389), 0
  newly_predicted — and identical against the join, chain-repair and
  versioned-cut baselines too; F6's worry that the S1 join would void the
  pre-registration did NOT materialize, and the pre-registration stands,
  not to be discarded as stale. The OPEN recomputation runs against the
  baseline resolved by the §5 log-read rule below.]
- Dossier-class forecast (checked only at the pre-registered checkpoint,
  DEV-stamped): `fp_section_prior` should shrink substantially — its 24
  atom-zero members are the exact mechanism signature; the 6 with atom > 0
  are NOT expected to move (their section share dominated but the gate
  doesn't fire — a disclosed limit of A1, not a surprise). `fn_*` classes
  may GROW by the §2 "against" mechanism (atom-gap clauses losing their
  proxy) — forecast disclosed now so it cannot be quietly re-narrated later.
  [Extended per S4_ADVERSARIAL_REVIEW_R2 S4: the flip set reaches beyond
  `fp_section_prior` (see the S1 note above), so the forecast must also
  name **`fp_threshold_drift` shrinking by up to 4** (helpfulness m0379 /
  m0381 / m0382 / m0389 flip out and are classified there) and **2
  tool-panel AGREEMENTS converting to FNs** (caution m0176, harm m0586 —
  cells the census recorded no disagreement on at all). Without these, S8
  would show class movement this design did not predict, and the
  re-narration risk this bullet exists to prevent reappears at the
  checkpoint.]
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
- **Adjudication bound — pre-registered and decision-critical [replaces the
  qualitative expectation per S4_ADVERSARIAL_REVIEW SCI-B1]. prediction.json
  carries `max_regressions: 0`.** [Mechanism claim corrected per
  S4_ADVERSARIAL_REVIEW_R2 E1 — the bound and the decision rule below are
  UNCHANGED; what was wrong is only the claim about what enforces them.]
  What the driver actually does: it REQUIRES this field as a non-negative
  integer (cycle.py:794–796), computes the tally of `regression` verdicts
  against it and RECORDS a `{"kind": "max_regressions", …, "result":
  "PASS"|"FAIL"}` check into `prediction_check.json`
  (`_check_predictions_adjudicate`, cycle.py:1046–1056 — it records and
  returns; it raises nothing), and at DECIDE it REFUSES a decision that
  carries a FAILing check without a written justification (cycle.py:1383–
  1392). It does NOT gate keep-vs-revert: CYCLE_DESIGN.md, "The decision
  rule (policy-critical)", is explicit that "a FAILED prediction or an
  override obliges a written justification; it never auto-decides", and
  that is deliberate policy, not an omission. So the integer that decides
  the cycle is pinned HERE, on document-side grounds, not chosen by the
  operator at PREDICT time — and **the revert on any `regression` verdict
  is the DECIDE signer's PRE-REGISTERED OBLIGATION under this design**,
  exactly as it was for S3. The bound binds by pre-registration, with the
  driver's tally as its tripwire; the signer must know the pull is theirs.
  Named decision rule:
  * any flip adjudicated `regression` — the seat judged, document-side,
    that a careful auditor NEEDS the clause — fails the frozen check; the
    cycle REVERTS. The original "revert OR vocabulary-cycle referral"
    disjunction is DELETED as an unpinned judgment call: revert is the
    signer's pre-registered obligation under this design [per
    S4_ADVERSARIAL_REVIEW_R2 E1], and the referral is its sequel, not an
    alternative.
  * flip-outs adjudicated `unclear` whose dossier shows the m0587 atom-gap
    pattern (auditor-need plausible, atom coverage absent) are referred in
    the cycle record to **the F13 vocab follow-up batch** (the named m0587
    vocabulary follow-up that F13 assigns an owner, PORTFOLIO_REVIEW F13)
    — a named target, not "some future vocabulary work".
  Grounds — from §2's principle alone, stated before any verdicts exist
  [census-arithmetic step RESTATED per S4_ADVERSARIAL_REVIEW_R2 S1: the
  prior text derived the bound from the census's tool-sided count, "4 of
  30", as if the census set and the flip set were the same 30 cells. They
  are not — verified on the log-resolved baseline: 30 A1 flips, 30 census
  `fp_section_prior` cells, intersection **24**; the 6 flips outside the
  class are `helpfulness/m0379, m0381, m0382, m0389` (census FPs but
  classified `fp_threshold_drift`, panel-sided) and `caution/m0176`,
  `harm/m0586` (not census disagreements at all — tool and panel agreed
  and A1 removes the clause anyway). A tool-sided count within one census
  class does not bound the atom-gap population inside the flip set, so
  "any bound ≥ 5 is ungrounded" did NOT follow from that arithmetic. The
  bound is unchanged; only its stated derivation is]: **0 follows from
  the principle.** The principle says substitution-banned flips are
  correct removals, so the ONLY clauses on which a regression could even
  be licensed are atom-GAP clauses — auditor-need present, atom evidence
  absent — and the design licenses no substitution-mode regression at all.
  Any bound ≥ 1 would pre-license substitution on exactly the clause class
  the principle bans, converting the F13 remedy (vocabulary work) into
  shipped score. The census's 4 tool-sided autopsies are named as the
  CLASS where a regression is most likely to surface — not as a bound on
  the flip set, which contains 6 cells the census never classified as
  `fp_section_prior`. That refusal is not rhetorical: §2
  accepts the atom-gap cost as DISCLOSED, names the regression verdict as
  its designed detector, and names revert + the F13 referral as the
  designed outcome — that outcome, when it occurs, is a finding, not a
  process failure. So the tripwire is 0: pre-registered from the principle
  [per S4_ADVERSARIAL_REVIEW_R2 S1 — "+ the census arithmetic" is struck;
  0 is also the driver template's default], not fitted to the mechanism.
  The older
  qualitative form survives only as orientation — most flip-outs are
  expected `correct` under the auditor-need question (the clause's own
  text carries no match), and a concentration of regressions on atom-gap
  clauses is the m0587 failure signature — but the decision reads the
  bound, not the expectation.

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
The 30-flip enumeration in §3 is therefore valid ONLY against the baseline
the cycle actually opens on; it does not survive any later join or vocab
change and must be re-enumerated if the cycle runs after one.]**

**The unlock cliff, named for the cycles that inherit it [added per
S4_ADVERSARIAL_REVIEW SCI-m2].** A1 keys the full 0.45 propagation on
EXACTLY-zero atom evidence: any nonzero atom credit, however weak, unlocks
the entire section prior. The cheapest gaming route is blocked by
construction — stopword atoms are floored to idf 0.0 (relevance.py:552–
555), so they contribute exactly 0.0 and cannot unlock (verified) — but a
rare atom with small positive idf can. The unlock side generates NO flips
in this cycle (unchanged scores are never adjudicated), so nothing in this
cycle's measurement can see it; the F6 scoping above discloses the non-
invariance ("S6 atoms can give a gated clause its first nonzero atom
credit"), and the INCENTIVE it creates is named here for S6/S7 to inherit:
vocabulary additions can buy section credit for a clause one ε-match at a
time. The checkpoint census (S8) is the first instrument that can observe
the unlock side at all; an `fp_section_prior` shrink accompanied by
clauses unlocking on single weak atoms is the pattern to read against this
disclosure.

**The baseline is read from the cycle log, never named here [amended per
HANDOFF.md S4 ruling 2 (2026-08-04)].** Standing rule (HANDOFF.md):
baseline = latest closed-KEEP spine snapshot, always read from the cycle
log, never named statically in a design doc. Mechanism, specified so OPEN
can execute it mechanically: read `cycles/CYCLE_LOG.jsonl` (one JSON
record per closed cycle, appended at CLOSE) and take the LAST line whose
`decision` is `"keep"`; **the mechanization drops the "spine" qualifier,
knowingly [noted per S4_ADVERSARIAL_REVIEW_R2 E9]** — the log's fields are
`{census_consulted, census_deltas, cycle, date, decision, exploratory,
noop, overrides, prediction_pass_rate, shape}` and NONE distinguishes a
spine keep from any other keep, so a future off-spine keep (different
annotations/atoms/overlay) would be selected silently. Today it resolves
correctly, and the mitigation is already in place: OPEN re-enumerates
against whatever the rule yields and must reproduce §3's split or re-pin
with a written delta, and the config pins in §6 make a differing lineage
surface in `config.changed` rather than pass unnoticed. A spine marker in
the log is the durable fix and belongs to the driver, not to this cycle.
Continuing the mechanism: the baseline snapshot is `snapshots/<cycle>.json`
for that line's `cycle` value — closed cycles publish their snapshot under
their own cycle name as tag, and the driver resolves
`baseline_snapshot_tag` to `snapshots/<tag>.json` at MEASURE. Whatever tag
the log yields at OPEN — not anything written in this file — is the
manifest's `baseline_snapshot_tag`. Consequences: if a new KEEP closes
between this design and OPEN, the baseline moves with the log
automatically, no amendment needed; and a revert needs no named fallback
branch — a reverted cycle puts no keep line in the log, so there is
nothing for the rule to resolve to it. The text this replaces named a
"post-S3 baseline (cycle 5's keep config)" statically and offered "the
cycle-4 config if cycle 5 reverts" as fallback; both are DELETED — the
parenthetical was ruled STALE and wrong (cycle-4 predates S1 and S2, so
its recorded config shas no longer match the tree), and the static naming
itself is what the ruling forbids. The OPEN recomputation of the flip
enumeration against the log-resolved baseline is authoritative: it must
reproduce §3's 13/13/4 or re-pin with a written delta (the empirical
envelope — enumeration verified identical across the existing keep lineage
and the join/chain-repair/versioned-cut baselines — is recorded in §3's
ruling-3 note).

**With containment credits.** Containment prices subsumption matches INTO
the atom channel (`ContainmentIndex`, min-idf × kind_factor). A1 must read
the post-containment atom total: a clause whose only evidence is a licensed
subsumption match has atom > 0 and keeps its section credit. This is
correct — the subsumption credit is the clause's own evidence, and gating on
exact names only would silently punish the overlay's adjudicated wins
(cycles 1–3). Gate test: a clause scored solely via a containment edge must
be un-gated (verify-RED against a mutant reading exact matches only).
**Written against a SYNTHETIC edge fixture, and the interaction is
currently VACUOUS [added per S4_ADVERSARIAL_REVIEW_R2 E7].** The shipped
overlay is `overlay_empty.json` — `edges: []`, `max_edges: 0`, whose own
provenance statement says it exists only as the vehicle that routes scoring
through `ContainmentIndex` so `pricing_version` is recorded, with
"containment.json's licensed edges … dormant (overlay reactivation is cycle
S5's job)". No clause in any current baseline carries subsumption credit, so
a builder hunting the live corpus for such a clause will find none: the gate
test constructs its own edge fixture. The requirement is forward-looking —
the interaction goes LIVE at S5 — and the sentence above about punishing
"the overlay's adjudicated wins" therefore states the stakes for the
reactivated overlay, not for today's scored corpus.

**With the standing quality floors (test_quality_floor.py) [pre-registered
per S4_ADVERSARIAL_REVIEW ENG-M3].** The floors are a `conftest.REQUIRED`
guard and they measure `relevance.RelevanceIndex.predict` MCC per behaviour
against the true panel on the b8 pairing — that is, they measure the very
scorer A1 modifies, under a re-derived Otsu cut (the §3 frozen-cut
precondition governs the snapshot/flip surface, not this standing
measurement path). Under the unconditional gate (§6) they measure the GATED
scorer. Pre-computed on the exact test path (the ungated side reproduces
the floor file's own docstring values exactly):

| behaviour | MCC ungated | MCC gated | floor | margin if floors untouched |
|---|---:|---:|---:|---:|
| avoiding-over-and-under-caution | +0.2826 | +0.2474 | 0.23 | **0.017** |
| harm-avoidance-to-third-parties | +0.3502 | +0.3782 | 0.30 | 0.078 |
| helpfulness | +0.2007 | +0.2626 | 0.15 | 0.113 |

All three floors stay green, so this does not block the build — but leaving
them untouched both tightens caution ~4× to a hair-trigger and lets
harm/helpfulness drift far below the measured value (a slack guard is the
floor file's own founding pathology). Pre-registered treatment, the floor
file's own rule for a changed measured quantity (its label-free re-
derivation precedent): **re-derive all three floors AND the mean floor in
the SAME COMMIT as the gate, and correct the floor file's PROSE
measurements in the same diff [added per S4_ADVERSARIAL_REVIEW_R2 E6 — a
floor file's honesty about its own numbers is load-bearing here, and these
become false under the gate]**: the module-level `FLOORS` comment
("Measured label-free: helpfulness +0.2007, harm-avoidance +0.3502,
over/under +0.2826") becomes **+0.2626 / +0.3782 / +0.2474**; and
`test_mispaired_artifacts_do_not_clear_the_floors`'s docstring
("helpfulness +0.0019, over/under +0.2516, harm-avoidance +0.3421", mean
+0.1985) becomes **helpfulness +0.0053, over/under +0.1484, harm-avoidance
+0.3369, mean +0.1636** — all four recomputed on the exact test path under
the gate. Note the guard CHANGES CHARACTER and the docstring's "honest
limit" note must say so rather than stay wrong in the tool's favour: under
the gate over/under (+0.1484) trips the proposed 0.20 floor too, where the
current text says it clears, so the mis-pairing is caught by two
per-behaviour floors plus the mean, not by the mean alone. New floors,
~0.05 below the gated measurements —
caution ≈ 0.20, harm ≈ 0.33, helpfulness ≈ 0.21, mean ≈ 0.25 — with the
gated measurements and the exact new floors pinned in the cycle record,
and the mandatory ⚠️ rationale comment in the file: the quantity changed
(substitution-banned credit removed from the scorer), and the caution
floor's numerical DROP (0.23 → ≈ 0.20) is calibration to the honest
measurement, NOT a relaxation — the run passed at 0.23 with margin 0.017,
so nothing is lowered to make a run pass. Disclosure: the Otsu cuts on
this path move substantially under the gate (helpfulness 0.2318 → 0.0569)
— the m0422 drift dynamic §3 warns about is live on every path that re-
derives its cut; on this one it is the defined measurement semantics, and
the frozen-cut precondition does not apply. `test_quality_floor.py` is in
files_to_change (§6) accordingly.

**Ordering.** One variable per cycle (F5 two-sided closure), so never
combined with cycle 5 in a single cycle. Recommended order:

1. Cycle 5 first — it is designed, adversarially reviewed, and its §2
   predictions are already pinned against the cycle-4 keep config;
   re-pinning it against a section-gated baseline would waste that review.
   [Status note (2026-08-05): cycle 5's first landing REVERTED (cycle log)
   and the pricing redesign (S3b) is in flight; per HANDOFF.md S4 ruling 1
   the spine order S3 → S4 was a sequence, not a dependency — A1's gated
   set is computed from the atom channel, which pricing never zeroes, so
   this cycle does not wait for S3b.]
2. This cycle second, baseline = whatever the log-read rule above resolves
   at OPEN (last `"decision": "keep"` line of `cycles/CYCLE_LOG.jsonl` →
   `snapshots/<cycle>.json`) — NOT any snapshot named in this design.
   [Amended per HANDOFF.md S4 ruling 2: the original parenthetical "(or
   the cycle-4 config if cycle 5 reverts)" is DELETED as STALE and wrong —
   cycle-4 predates S1 and S2, so its recorded config shas no longer match
   the tree — and revert handling is automatic under the log-read rule: a
   reverted cycle puts no keep line in the log, so no fallback branch is
   named or needed.] The flip enumeration is recomputed at OPEN against the
   resolved baseline and re-pinned with a written delta if it does not
   reproduce §3. Its predictions are robust to the ordering in *class*
   terms (the gated set is invariant to pricing — and ONLY to pricing, per
   the F6 scoping above; a join or vocab change voids the enumeration
   outright) but not in *count* terms, which is exactly what the manifest
   pin is for.
3. The checkpoint census runs after both, measuring the combined
   census-class deltas once, DEV-stamped — not per-cycle (F1).

Both cycles are score-reducing under the same frozen cut; neither may
re-derive it (DRIFT_STANDING_DESIGN.md §2(b) governs any cut change).

## 6. Fit to the cycle ceremony

Manifest: description "evidence-gated section credit — the section prior
may amplify a clause's own atom evidence, never substitute for it (atom-
channel gate, parameter-free)"; document-side rationale §2. `depends_on:
cycle4-frozen-cut (closed, keep)` is DESCRIPTIVE PROSE, not a manifest key
[corrected per S4_ADVERSARIAL_REVIEW ENG-m1: the manifest schema has no
`depends_on` field (cycle.py `manifest_template` /
`REQUIRED_MANIFEST_KEYS`); an extra key is tolerated noise] — the frozen-
cut dependency is really carried by `config.thresholds`, and it is the
frozen cut (`thresholds_frozen.json`), not a baseline snapshot; baseline:
`baseline_snapshot_tag` is set AT OPEN by the §5 log-read rule (last
`"decision": "keep"` line of `cycles/CYCLE_LOG.jsonl` →
`snapshots/<cycle>.json`) and deliberately NOT named in this design
(HANDOFF.md S4 ruling 2); `census_scope: dev`. `census:
deferred_to_checkpoint` is likewise DESCRIPTIVE PROSE, not a manifest key
[corrected per S4_ADVERSARIAL_REVIEW_R2 E4 — the identical
not-a-schema-key error one clause later: `census` is in neither
`manifest_template` (cycle.py:227–244) nor `REQUIRED_MANIFEST_KEYS`
(cycle.py:247–250), no manifest on disk carries it, and the DRIVER sets it
itself for a code-shape cycle (cycle.py:672–673, `if shape == "code":
state["census"] = "deferred_to_checkpoint"`)] — this cycle runs no census
of its own, and the driver records that state. Config pins — the measure
snapshot must score on the same inputs and overlay as the keep lineage or the diff confounds: **`config.overlay =
overlay_empty.json` pinned explicitly** [added per S4_ADVERSARIAL_REVIEW
ENG-m1: the entire keep lineage is overlay-ON, pricing_version 1.2, and
S1's manifest carries both `overlay` and `thresholds` in config; omitting
`overlay` from the measure snapshot would surface "overlay" in
`config.changed` and confound the single-variable diff with a scorer swap
(ContainmentIndex → legacy) — loud, not silent, but pinned anyway] — next
to `config.thresholds = thresholds_frozen.json` (the §3 hard
precondition). files_to_change: `relevance.py` (channel_scores section
step only: the gate and the one construction parameter for the dispatch
rung below — or a versioned subclass beside the legacy class if the
builder prefers the containment house pattern; the dispatch rung (c) is
the F9 contract, the encoding is the builder's choice), `snapshot.py` +
`dossier.py` (the version-key plumbing below),
`test_quality_floor.py` (the same-commit floor re-derivation pre-
registered in §5), tests. **Where the gate tests land, and why
`conftest.py` is NOT declared [resolved per S4_ADVERSARIAL_REVIEW_R2 E5]:
the gate tests go in `test_relevance.py`, which is EXISTING and is not in
`conftest._OPTIONAL` (it is collected unconditionally), so no
`conftest.py` change is required and declaring it would HALT the cycle —
IMPLEMENT refuses when any declared file is byte-identical to its OPEN sha
(cycle.py:830–836). The prior revision's `conftest.py` entry is therefore
WITHDRAWN. The registration fence still binds if the builder instead adds
a NEW test module: then the file must be created (at least as a stub)
BEFORE OPEN — `_open` refuses any `files_to_change`/`gate_tests` path that
does not exist (cycle.py:638–640) — and `conftest.py` declared in the same
diff that registers it in `conftest._OPTIONAL` (ITERATION_LOOP.md
anti-cheat perimeter, AGENTS.md "same diff, every time"). One route or the
other, chosen at OPEN, never both.**

**F9 version key — `section_gate_version` [per HANDOFF.md S4 ruling 4;
vehicle specified and pattern claim corrected per S4_ADVERSARIAL_REVIEW
ENG-M1]: A1 is not a pricing change, so it gets its OWN key, on the
`pricing_version` pattern in the respects named below — and with one
NAMED departure.**

**Enable/disable vehicle (stated first, because the original draft left it
unspecified): the gate is UNCONDITIONAL once merged.**
`RelevanceIndex.channel_scores` scores gated by default; there is no CLI
flag, no manifest config key, and `cycle.py::_measure` threads no new
seam — it passes exactly `annotations`, `atoms`, `overlay`, `thresholds`
from the manifest config into snapshot.py today (the snap_cmd
construction, cycle.py:927–942; `build_snapshot`'s signature has
`overlay_path`/`thresholds_path` and nothing else scoring-relevant), and
that is unchanged; `cycle.py` is therefore NOT in files_to_change. The measure snapshot is gated
automatically — no opt-in to forget (the opt-in reading would measure a
NO-OP: the measure snapshot would score ungated) and no opt-out to drift
on. Pre-gate scoring is reachable ONLY through the reconstruction
dispatch in (c).

> ⚠️ **PLACEHOLDER — E2 IS PENDING, DELIBERATELY NOT APPLIED HERE.**
> `S4_ADVERSARIAL_REVIEW_R2` E2 (MAJOR) finds that the gate-OFF
> **construction parameter** specified in (a)/(c) below cannot reach the
> shipped scorer: the dispatch ladder builds `ContainmentIndex` /
> `PatientIndex` on the paths that matter, and neither `from_files`
> forwards unknown kwargs to `relevance.RelevanceIndex.__init__`
> (`containment.py:452–458`/`:350`, `patient.py:189,229`) — so the
> absent-key branch would silently fall through to the merged default,
> the exact failure (c) names, and `containment.py` is in neither
> `files_to_change` nor the driver's undeclared-input closure, so the
> edit would not halt. **The finding is ACCEPTED and its resolution is
> DEFERRED**: a config-driven index-builder refactor is being written in
> parallel and will change which of E2's options (declare
> `containment.py`+`patient.py`; post-construction assignment in
> `dossier.py`; or a `relevance.Weights` field) is right. The gate-off
> vehicle text below stands AS-IS pending that refactor and **must be
> re-decided and rewritten before OPEN** — `files_to_change` freezes at
> OPEN, so this cannot be carried past it.

(a) module constant `SECTION_GATE_VERSION = "1.0"` beside the gate in
`relevance.py`; the index carries one explicit construction parameter
(gate on/off) whose DEFAULT is on — the parameter exists for the dispatch
rung in (c), not as a user-facing seam; [E2 PENDING — see the placeholder
above]
(b) snapshot.py records `section_gate_version` in the snapshot's config
identity UNCONDITIONALLY (every index it builds post-merge is gated) —
pre-gate snapshots carry NO such key, exactly as pre-overlay snapshots
carry no `pricing_version` (absent is a defined identity value), and
`diff_snapshots`'s scoring-rule identity loop compares the key alongside
`pricing_version`, so under identical inputs the gate itself surfaces in
`config.changed` as the diff's cause (the cycle-3 escalation (c) blocking
precondition);
(c) dossier.py's reconstruction dispatch ladder gains the rung: ABSENT
`section_gate_version` ⇒ the ungated (pre-A1) section assignment,
rebuilt by passing the gate-OFF parameter EXPLICITLY [E2 PENDING — the
vehicle for "explicitly" is unresolved; see the placeholder above] (the
in-tree scorer gates by default, so the absent-key branch must not fall
through to the merged default), present ⇒ the gated scorer — absent is a DEFINED
dispatch value, never a KeyError, never silently treated as current,
mirroring `_index_for`'s pricing_version handling. The pre-gate baseline
snapshot built under the sandwich rule therefore reconstructs ungated by
dispatch — that is the F9 guarantee that the baseline side reproduces.
**Two-axis composition [added per S4_ADVERSARIAL_REVIEW ENG-m3; made
concrete per S4_ADVERSARIAL_REVIEW_R2 E3]: this ladder (`_index_for`) is
keyed on `pricing_version` first, and it already has THREE live rungs
today — `"2.0"` ⇒ `PatientIndex`, overlay present ⇒ `ContainmentIndex`,
absent ⇒ legacy `RelevanceIndex` (dossier.py:346–364), with snapshots
existing on all three. **S4 extends all three existing pricing rungs with
the gate branch** (each rung gains: absent `section_gate_version` ⇒ the
ungated variant of THAT rung's scorer), unconditionally — not only if it
lands second. And per HANDOFF.md ⭐⭐⭐ ("run the S3b build …, then S4 —
SEQUENCED (dispatch-ladder composition), not parallel") S4 DOES land after
S3b, so it also extends S3b's new rung. Without that, a snapshot carrying
both keys is dispatch-ambiguous.**
(d) manifest `compatibility`: `{"version_key": "section_gate_version",
"statement": ...}` — both fields non-empty, as `_open` requires of every
shape:code manifest; the statement names the reachability mode:
DISPATCH-ONLY (below).

**Reachability — where the pattern holds and where it does not.** The
original draft claimed this key was "specified exactly on the
`pricing_version` pattern"; that is corrected here. The pattern HOLDS:
own config-identity key; absent-is-a-defined-value; reconstruction
dispatch rung; `diff_snapshots` surfacing. It does NOT hold at the
builder: `pricing_version`'s old behavior stayed reachable AT THE BUILDER
by omitting `--overlay` (and `--thresholds`), but once the gate is
merged, bare `snapshot.py` can never again rebuild a pre-gate snapshot
byte-for-byte — pre-gate scoring is reachable only via the dispatch rung
in (c). That satisfies F9's letter ("the old behavior remains reachable
via a version recorded in snapshot config ... so the baseline side
reconstructs"): the sandwich-rule baseline was built BEFORE the merge,
and dossier reconstruction — the adjudication's only consumer of the old
scorer — reaches it by dispatch. The departure is disclosed here rather
than papered over by the word "exactly".

**Census config identity — named S8/0c obligation, not this cycle's diff
[per S4_ADVERSARIAL_REVIEW ENG-m2].** Items (a)–(d) plumb
`section_gate_version` through snapshot identity, `diff_snapshots`
surfacing, dossier dispatch, and the manifest — but NOT through the
census identity (`audit_disagreements.config_identity`, which records
`pricing_version` when the overlay scored). This cycle runs no census of
its own (`census: deferred_to_checkpoint`), so the plumbing would be
unexercised in this cycle's gate; the obligation is named and specced
here for its owner instead: the checkpoint census is S8
(PORTFOLIO_REVIEW F13), with the census-header work tracked as Group 0c
("census --overlay/headers", before S8) — S8's F2 full-config-identity
obligation carries recording `section_gate_version` in the census header
whenever the scorer that scored had the gate enabled (post-merge:
always), so the S8 header that checks this cycle's own DEV-stamped class
forecast names every scoring rule that moved its numbers.
Gate tests, all verify-RED:
zero-atom ⇒ zero-section; atom > 0 ⇒ bit-identical section credit;
containment-credited clause un-gated; monotone-decrease + subset-at-fixed-
cut, WITH the §3 corpus-max precondition (each behaviour's corpus-max
clause has atom > 0) asserted as part of the OPEN enumeration [added per
S4_ADVERSARIAL_REVIEW SCI-M1]; F9 reconstruction of pre-gate snapshots
(absent `section_gate_version` ⇒ ungated path via the explicit gate-off
vehicle [E2 PENDING — vehicle unresolved, see §6's placeholder],
bit-exact); and the §3 hard precondition on the
CYCLE5_DESIGN.md §4 instrument:
`snapshot.assert_frozen_thresholds` passes on BOTH the log-resolved
baseline and this cycle's measure snapshot. PREDICT: §3 verbatim, with
the enumerated flip list frozen at OPEN and prediction.json's
`max_regressions: 0` pinned per §3's adjudication bound [per
S4_ADVERSARIAL_REVIEW SCI-B1]. review_required: true; §2's document-side
argument and §4's deferral option are the review's agenda. FORBIDDEN-
token check on any new names.
