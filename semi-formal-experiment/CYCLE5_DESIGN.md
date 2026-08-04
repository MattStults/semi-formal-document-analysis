# CYCLE 5 — patient/kind-aware match pricing (design, 2026-08-03; REVISION 2, 2026-08-04, integrating all six CYCLE5_REVIEW.md MUST-fixes)

One cycle under CYCLE_DESIGN.md (amended form), shape: code/matching fix.
Target class: `fp_promiscuous_atom` — 155/294 (53%) of all tool-vs-panel
disagreement in the ext_v1_merged__audit_v1 census, the class DISAGREEMENT_
REPORT.md's m0276 case defined: patient-free / patient-wrong atoms firing on a
clause about a different party. This design prices recorded patient structure
into the atom channel. DESIGN ONLY — no code ships with this file.

Revision 2 status: CYCLE5_REVIEW.md returned DO NOT BUILD AS WRITTEN with six
MUST-fixes; every one is applied below as an integrated change, not a footnote.
Two events have landed since revision 1 and are reflected throughout:
**cycle 4 (versioned-cut-2026-08-04) is CLOSED with KEEP**, and the
**chain-repair cycle (chain-repair-2026-08-04) is CLOSED with KEEP** — the 12
chain-audit corrections are applied, so every principal chain in
annotations_ext_v1_merged now parses agent-first (`chain_audit/verdicts.json`:
97 correct, 11 agent_missing repaired, 1 unlicensed folded). Numbers computed
by the reviewer BEFORE the repair are pinned below but flagged for
recomputation at OPEN (§2).

## 0. Scope honesty, first

Measured over the census dossiers: of the 155 `fp_promiscuous_atom` verdicts,
only **31 max-clauses carry any principal-chained atom at all** (census-era
figures; 29 of those chains named `user`). The other ~80% of the class is
carried entirely by patient-FREE atoms — atoms whose annotation records
nothing about who is protected. **No pricing rule can read structure that was
never written.**

And the reviewer's simulation sharpened this further (F2): at d=0.25 under the
frozen cuts, **this cycle moves exactly 1 of the 155 clauses in its nominal
target class** (m0276); the other 11 computed flips belong to
`fp_section_prior` (the under-18 section). Stated plainly: as a fix for the
53% class, cycle 5 on the CURRENT annotation is a 1/155 fix. This cycle
therefore does two things and claims only the first:

1. Makes recorded patient structure PAY: a chain naming the wrong patient
   becomes counter-evidence, which today it cannot be even in principle
   ("an unmatched atom contributes 0, never a penalty" — DISAGREEMENT_REPORT).
2. Establishes the pricing mechanism that makes the patient-backfill
   annotation cycle (BACKFILL_DESIGN.md) worth running. The 80% patient-free
   mass is that cycle's target, not this one's. Attacking it by discounting
   patient-free matches directly is considered and REJECTED below (§2,
   option B) with numbers.

Whether cycle 5 runs before or after the backfill is no longer left implicit:
§7 states the dependency and recommends AFTER.

## 1. The pricing rule

### 1.1 Where the query's patient context comes from (label-free, document-side)

A new optional field on each entry of `behaviours_query.json`:

```json
{"slug": "harm-avoidance-to-third-parties", ..., "patients": ["third_party"]}
```

- Values drawn from `grammar.PRINCIPALS` only.
- **Document-anchored declaration, housed panel-blind (F4).** The anchor
  check REFUSES a `patients` list unless each declared principal's readable
  form (or an enumerated surface synonym: "third parties"/"those outside the
  conversation" → `third_party`; "users" → `user`) appears in that
  behaviour's own `name + definition` text. Revision 1 assigned this check to
  `validate_behaviours.py`; that module opens `data/behaviours.json` — a
  FORBIDDEN, panel-side file — and may not host a check that licenses a
  query-side scoring input. The check now lives in **`patient.py` itself**
  (`patient.validate_query_patients(behaviours_query_path)`, plus a CLI
  entry), which reads ONLY `behaviours_query.json` and `grammar.PRINCIPALS`,
  and joins the query-adjacent set scanned by `test_no_reference_leak.py`.
  `validate_behaviours.py` is not touched by this cycle. The declaration is
  authored by us, licensed by the query file's own prose — never by a panel
  number. The panel file is never opened; the field lives in the query-side
  file whose split from the reference file exists precisely so this is
  checkable.
- Proposed declarations: harm-avoidance-to-third-parties → `["third_party"]`
  ("harm third parties, society, or those outside the conversation");
  helpfulness → `["user", "developer"]` ("the users and developers it works
  with"); avoiding-over-and-under-caution → `[]` (its definition names no
  protected party). **An empty or absent list disables patient pricing for
  that query entirely — bit-identical scores.**
- **Definition-freeze gate (F5).** The anchor check makes the definition text
  a scoring input, which makes editing a definition inside this cycle's own
  declared diff a way to license any declaration. Gate test, verified RED
  against a planted definition edit: every behaviour's `name` and
  `definition` in `behaviours_query.json` must be byte-equal to their values
  at cycle-4 closure (the file's sha is pinned in the closed cycles'
  `closure_checked` lists — cycles/chain-repair-2026-08-04/decision.json
  pins `behaviours_query.json` in its closure set); the `patients` key is the
  ONLY permitted delta on each entry. A definition change is a different
  cycle, never a rider on this one.
- The behaviour atoms' own chains (audit_v1 carries 7, e.g. 4 `__model_user`
  on helpfulness) are used as a CONSISTENCY CHECK only — the anchor check
  warns if a query atom's chain patient is outside the declared set — not as
  the source. They are too sparse to be the source, and sourcing from them
  would make the patient context an accident of atom-drafting.

Rejected alternative: mechanical extraction from the definition text. Brittle
(pronoun/paraphrase misses), and a silent extraction failure = silently
disabled pricing — the dead-channel failure mode this repo has hit twice.
A declared field with a mechanical anchor check keeps the declaration loud
and the license checkable.

### 1.2 The patient of an atom (clause side) — length-≥2 chains ONLY (F1)

Revision 1 read a sole chain member as the patient. That inverted the
grammar: chains are AGENT-FIRST (`grammar.py`: "after a double underscore,
agent first"; `describe`: a length-1 chain renders "WHO: X is the party
concerned", a length-≥2 chain "WHO: X acts, upon Y"), and `structural.py`'s
shipped, test-pinned reading is patients = `chain[1:]`. Under the old
misreading the defining case only worked because the annotation itself had
misused the convention (`must_advise_immediate_help__user` = "the USER
advises"). The chain-repair cycle has since fixed that: m0276 now carries
`must_advise_immediate_help__model_user` artifact-wide, so the case arrives
through the CORRECT reading, not through the bug — the review's expectation
that m0276 would have to wait for the backfill is superseded by the repair.

`patients_of(name)`: parse via `grammar.parse_name`.

- No principal chain → **patient-free** (None — absent is absent, never
  defaulted, same contract as `role_of`).
- Chain of length 1 → **patient-free.** A sole member is an AGENT
  (`should_follow_principles__developer` = the developer acts); it records
  who acts, not who is acted upon. Length-1 chains participate in NOTHING
  below: they cannot be consistent, cannot be mismatched, cannot create
  taint, cannot defeat taint. (Post-repair the artifact carries exactly 5 of
  them, all verdict-correct agent-only chains.)
- Chain length ≥ 2 → the patient set is `chain[1:]`.
  `shouldnot_lie_by_commission__model_third_party` → {third_party};
  `must_advise_immediate_help__model_user` → {user}.

This reading is pinned by test AND now attested by adjudication: the chain
audit reviewed all 109 chain instances against clause text under exactly this
convention. If the reviewer thinks `chain[1:]` is the wrong patient reading
for any shipped chain shape, that is a finding against §1.2, not a tuning
knob.

### 1.3 The rule (PRICING_VERSION "2.0")

For a query with non-empty declared patients P, on each clause. "Chained"
below always means "carrying a length-≥2 chain" per §1.2.

- **Per-atom factor.** Each credited atom match (exact or containment
  subsumption) through a clause atom `a`:
  - `patients_of(a) ∩ P ≠ ∅` → **consistent: factor 1.0 — priced bit-identical
    to today.** (Invariant I1, §3.)
  - `patients_of(a)` non-empty, disjoint from P → **mismatched: factor
    `patient_mismatch_discount`** (proposed 0.25 — see §1.4).
  - patient-free (no chain, or length-1 chain) → factor 1.0 from this layer.
- **Clause-taint factor** (the m0276 mechanism — clause-side presence as
  counter-evidence). If the clause's annotation carries ≥ 1 patient-bearing
  (length-≥2) chained atom and **every** such atom on it is mismatched with P
  (none consistent), the clause is *uniformly mismatch-attested*: every atom
  credit on that clause — including patient-free matches — takes factor
  `patient_mismatch_discount`. Rationale, document-side: the annotation
  records who this clause protects (m0276:
  `must_advise_immediate_help__model_user`), and the patient-free stock atoms
  on the same clause (`imminent_bodily_harm`, `human_safety`-likes) inherit
  that recorded context. One consistent chain anywhere on the clause defeats
  the taint (the m0248 guard, §5). A length-1 chain neither creates nor
  defeats taint.
- **Single application, no compounding**: effective factor per credited match
  = `patient_mismatch_discount` if (that atom mismatched) OR (clause tainted),
  else 1.0. Never d².
- Patient-free clauses (no length-≥2 chains at all — the majority) are
  **priced exactly as today**. Absence of decoration is never penalized
  (option B rejected, §2).
- The lex, kind, and section channels are untouched; section recomputes from
  the discounted local totals as it always has (section is defined over local
  scores, not frozen against them — this propagation is inside the flip
  prediction, §2, as is the normalizer movement it causes, §3 I2).

Options for pricing patient-free atoms under a patient-specific query,
considered and rejected with document-side counts (all label-free; computed
over the census-era configuration, annotations_ext_v1_merged +
behavior_atoms_audit_v1, Otsu):

- **Option B — flat discount on patient-free matches when P ≠ ∅.** Predicted
  clauses matched ONLY by patient-free atoms: helpfulness 126/145, harm 59/73,
  caution 78/95. Any nonzero flat discount puts essentially the whole
  predicted set in motion → the §4 flip budget (30) is exceeded several times
  over, and the mechanism is indistinguishable from "shrink the predicted set
  because the census said FPs dominate" — coordinate descent on panel counts
  wearing a pricing rule's clothes. REJECTED.
- **Option C — require ≥ 1 patient-consistent atom for full credit.** On harm,
  exactly **1** of 73 predicted clauses has a consistent chain. This discounts
  ~72/73 of the predicted set — option B with a harder edge. Re-creates the
  FN problem at full scale in one step. REJECTED.
- **Kind-aware analogue — discount patient-free `value`-kind atoms (the
  `human_safety` stock-topic class) under patient-specific queries.** Same
  objection at smaller radius, plus: kind is the channel this artifact has
  repeatedly shown to be uninformative at match level (Weights docstring:
  kind=0.0, indistinguishable from 0.3 within noise), and no unanimity
  license (the v1.1 pattern) exists for "value-kind means patient-free-and-
  promiscuous". DEFERRED to a future design if patient backfill fails; not
  in cycle 5.

### 1.4 The constant

`patient_mismatch_discount = 0.25`, a new `Weights` field. HAND-SET, with the
reasoning stated so it can be attacked: a recorded wrong patient is stronger
counter-evidence than an unstable kind (kind_mismatch_discount 0.4) — kind
drift is an annotation-batch artifact, a principal chain is a deliberate
authored claim about who the clause concerns, and since the chain audit that
claim is an ADJUDICATED population (109/109 instances reviewed against clause
text), not an unaudited one. It will NOT be swept: any sweep selects against
the panel and violates contract §5 invariant 9. 0.0 (outright exclusion) is
rejected because exclusion makes a single mis-chained atom able to erase a
clause's whole atom channel. The reviewer's simulation found the flip set
IDENTICAL for d ∈ {0.1, 0.25, 0.4} on the pre-repair artifact — a plateau,
so the constant is defensible without a sweep; **the OPEN-phase pin (§2) must
re-verify and record the plateau on the current baseline**, and if the
recomputed flip set is NOT flat across that range, the constant's placement
is a real degree of freedom and must be re-argued from golden-set
patient-contrast cases before build.

### 1.5 Mechanism and housing (the containment house pattern)

- New opt-in subclass `PatientIndex(ContainmentIndex)` (module `patient.py`),
  constructor `..., *, edges=(), query_patients=None`. `query_patients` maps
  slug → frozenset of principals; None/empty → **bit-identical to
  ContainmentIndex** (which with edges=() is bit-identical to RelevanceIndex).
  Nothing constructs it with patients unless a caller opted in by name;
  nothing silently reads behaviours_query.json's field.
- `patient.py` also hosts the §1.1 anchor check (the panel-blind housing,
  F4) and joins the set scanned by `test_no_reference_leak.py`.
- `PRICING_VERSION = "2.0"` in patient.py; snapshot config records
  `pricing_version` and the per-slug declared patients (with the
  behaviours_query sha it already records). Old behavior reachable forever:
  construct without `query_patients`, or any snapshot recording
  pricing_version ≤ 1.1 reconstructs through the old classes — the F9
  contract, same as containment's. **Explicit legacy rule (F6): a snapshot
  carrying NO `pricing_version` key at all reconstructs through the legacy
  path** — the cycle-4 baseline predates the overlay versioning and has no
  such key, so "absent" must be a defined dispatch value (= legacy), never a
  KeyError and never silently treated as current. Pinned by test against the
  actual cycle-4 keep snapshot.
- `explain()` gains `patient_pricing`: per credited match
  `{clause_atom, atom_patients, factor, why: consistent|mismatched|
  clause_taint|patient_free}` plus the clause-level taint verdict and the
  chained atoms that produced it — the records ARE the objects the scorer
  summed, so dossiers can name the discount behind a flip and can never drift
  from what scored (the Unit 4.1 contract).

### 1.6 Composition with containment subsumption pricing

A subsumption match is credited *through* a clause atom (`_best_subsumption`
returns `clause_atom`). The patient factor reads THAT clause atom's chain —
the evidence actually paid for — never the subsumer's name (subsumers are
chain-free by construction: `_license_edge` rejects principal chains on
either end of an edge, so a chained atom can never be a licensed child or
parent; its chain therefore never enters edge licensing, only this pricing
layer). Composition is multiplicative on the credit:

    credit = min(idf(subsumer), idf(clause_atom)) * kind_factor * patient_factor

with `patient_factor ∈ {1.0, patient_mismatch_discount}` per §1.3's single-
application rule. Both discounts ≤ 1, so the never-outprice invariant is
UNWEAKENED: a subsumption match still never outprices the exact match on the
same evidence — and a patient-mismatched exact match is discounted by exactly
the same factor as a patient-mismatched subsumption through the same atom, so
the overlay cannot become a discount-dodging route. Matching structure
(each query atom credited once, each clause atom once) is untouched.

## 2. PREDICT — the computed pin (F2), recomputed at OPEN

Revision 1's §2 predicted 1–5 flips by first-order arithmetic. The reviewer
implemented the rule and ran it: **the prediction was wrong by more than 2×
and mis-classed.** This section is now a COMPUTED pin, not an estimate, and
carries its own staleness flag.

**The reviewer's computed result (2026-08-04, PRE-chain-repair artifact,
d=0.25, frozen cuts):**

- **newly_predicted flips on RAW scores: 0** — a computed fact of the
  simulation, pinned as such. It is NOT restated as an a-priori monotonicity
  guarantee about the reported numbers, because the corpus-max normalizer
  moves (§3 I2): normalized flips in the newly_predicted direction are
  possible as normalizer artifacts and are tagged `normalizer_drift`, never
  `match_change`.
- **no_longer_predicted: 12 flips**, composition: **1 × fp_promiscuous_atom
  (m0276 — the defining case, and the ONLY member of the 155-clause nominal
  target class that moves)** and **11 × fp_section_prior (under-18 section
  clauses)**. The cycle's measured effect on its nominal class is 1/155 (§0).
- **Normalizer movement, disclosed:** on harm-avoidance, tainting the argmax
  section's clauses moves the corpus-max normalizer, so every UNTOUCHED
  clause's normalized score rises ~5%. This is a real reported-number change
  with zero match-level cause; dossiers must carry the `normalizer_drift`
  annotation (§3 I2) so these are never adjudicated as match changes.
- **helpfulness: 0 flips.** Its declared patients {user, developer} cover
  every `__model_user` chain in the vocabulary. Pinned per the review as
  **current-artifact luck, not structural coverage** — a future chain naming
  a non-user, non-developer patient on a helpfulness clause would taint; the
  zero is an observation about today's vocabulary, not an invariant.
- **avoiding-over-and-under-caution: 0 flips** (patients [] → pricing
  disabled; bit-identity is a gate test, not a prediction).
- **d-plateau:** flip set identical for d ∈ {0.1, 0.25, 0.4} (§1.4).

**Staleness flag — what must be RECOMPUTED at OPEN.** The pin above was
computed before the chain-repair cycle landed, and this cycle now baselines
on a post-repair (and, per §7, post-backfill) snapshot. At OPEN, rerun the
simulation on the actual baseline and re-pin, before PREDICT freezes:

- MUST re-pin: the flip count and identity, the class composition, the
  d-plateau, the normalizer deltas. The repair rewrote 5 names artifact-wide
  and the backfill (if sequenced first, §7) adds chains at population scale —
  the 12-flip figure is a pre-repair fact and may not survive either.
- Verified still true post-repair (recomputed 2026-08-04): the 16-clause
  uniformly-mismatch-attested predicted set on harm (m0221, m0222, m0260,
  m0263, m0264, m0276, m0579, m0580, m0581, m0584, m0585, m0588, m0589,
  m0590, m0591, m0593) stands under the length-≥2 reading — every one of the
  16 now carries a length-2 `model→user` chain, so the repair did not
  dissolve the taint set; it moved it onto the correct grammar.
- Stands as census-era description (no re-pin needed, marked DEV): the
  155/294 class size, the 31 chain-attested max-clauses, option B/C counts.

**The hard bound and the failure condition:** no_longer_predicted flips ⊆ the
uniformly-mismatch-attested predicted set plus its section-mates, as
recomputed at OPEN. Anything flipping outside that named set fails the
prediction. Well under the F4b flip budget (30) on the pre-repair artifact;
if the OPEN recomputation lands over 30, the §4 policy template fires BEFORE
PREDICT freezes (split, or pre-registered stratified sample).

**Adjudication expectations — the under-18 boundary IS the cycle
(pre-registered, per the review).** 11 of the 12 computed flips ride one
question: a teen user is the user, but "prioritize teen safety" clauses
arguably concern third parties (minors as a protected class). That
adjudication is this cycle's real output, and it is pre-registered as such:
m0276's removal expected `correct` (the passage's every harm-bearing noun
phrase is the user, per the hand autopsy); the under-18 flips expected
CONTESTED; a `regression` verdict on the under-18 set is a real finding
against the taint rule, and reverting on it — which loses m0276 too — is the
designed outcome, not a failure of process.

Provenance disclosure (policy §1: candidates from anywhere, provenance
recorded): this cycle was seeded by the m0276 autopsy and the census's 53%
figure — both panel-reading instruments — and the flip-composition correction
came from the reviewer's simulation. The keep decision will cite only the
flip adjudications; the census check happens at the next pre-registered
checkpoint, DEV-stamped. Naming clauses in the prediction is mechanism-level,
permitted and required by amendment 1; whether that line holds is for the
reviewer (§5, Q1).

## 3. Invariants (each becomes a gate test; verify-RED applies)

- **I1 — no regression on correct matches.** A patient-consistent match is
  priced bit-identically to today: factor 1.0 on both layers, and a clause
  carrying any consistent chain is never tainted. Test: score equality (not
  approx) on every helpfulness clause, full config, and on every clause of
  every behaviour under `patients=[]`. (Per §2: the helpfulness equality is
  luck of the current vocabulary; the test pins the fact, not a law.)
- **I2 — monotone-downward ON RAW SCORES (F3).** All factors lie in [d, 1.0]
  with d ≥ 0; channel scores stay ≥ 0; for every (behaviour, clause):
  **raw** score_v2.0 ≤ **raw** score_v1.1, with equality wherever no mismatch
  evidence exists; corollary tested directly on raw scores at a fixed cut:
  predicted_v2.0 ⊆ predicted_v1.1. **This claim is NOT made for normalized
  scores**: the corpus-max normalizer is itself a score, and when the argmax
  clause is tainted the normalizer falls and every bystander's normalized
  score RISES. Reported/normalized movement is therefore two-sided by
  construction. Any flip whose raw score is unchanged (or moved downward)
  while its normalized score crossed the cut is tagged `normalizer_drift` in
  its dossier — a queued dossier.py annotation, gate-tested — and adjudicated
  as a threshold-class question, never as `match_change`.
- **I3 — monotone in the declared set.** Enlarging a behaviour's `patients`
  never lowers any clause's raw score (more chains become consistent, taints
  can only be defeated). Empty set = identity.
- **I4 — containment composition.** Never-outprice preserved (mutant: drop
  the min-idf cap or the patient factor from the subsumption path → a pinned
  test must go red); a chained atom still cannot appear in any licensed edge;
  discount applied once, never d².
- **I5 — F9 reconstruction.** PRICING_VERSION "2.0" recorded in snapshot
  config; snapshots at ≤ 1.1 reconstruct through the old pricing bit-exact;
  **snapshots with NO pricing_version key reconstruct through legacy — the
  explicit absent⇒legacy rule (F6), pinned against the real cycle-4 keep
  snapshot**; dossier's ReconstructionMismatch self-check extended to
  dispatch on the recorded version (absent included). `diff_snapshots` must
  surface `pricing_version` in `config.changed` — the standing cycle-3
  escalation (c) becomes a blocking precondition here, because THIS cycle's
  diff is meaningless if the config change is invisible.
- **I6 — definition freeze (F5).** `behaviours_query.json` name+definition
  byte-equal to the cycle-4-closure values; `patients` the only permitted
  delta (§1.1). Verified RED against a planted definition edit.
- Mutation checks under the HANDOFF bytecode-cache discipline (clear
  `__pycache__`, assert the mutant loaded).

## 4. The cycle-4 dependency — SATISFIED, and gate-asserted (F6)

This is a **score-reducing change under a derived cut**; without a frozen cut,
lowering scores moves the cut and flips would mix `match_change` with
`threshold_drift` (the m0422 class, three cycles running).

**The gate is satisfied**: cycle 4 — versioned-cut-2026-08-04, the
per-behaviour frozen-cut artifact (`thresholds_frozen.json`, snapshot
`--thresholds` route) — is **CLOSED with KEEP**, recorded in
`cycles/CYCLE_LOG.jsonl` (`{"cycle": "versioned-cut-2026-08-04",
"decision": "keep", "date": "2026-08-04"}`) with its decision in
`cycles/versioned-cut-2026-08-04/decision.json`.

Closure alone is not enough, because the fallback path silently re-derives
(F6): a snapshot built WITHOUT `--thresholds` records no `threshold_source`
key and Otsu quietly returns. The instrument for the assertion **already
exists**: `snapshot.assert_frozen_thresholds(snapshot_path)` (snapshot.py)
raises unless EVERY behaviour in the snapshot records
`threshold_source == "frozen_artifact"`, and reports the offending slugs and
what they recorded instead. **Gate test: assert_frozen_thresholds passes on
BOTH the baseline and the measure snapshot**, verified RED against a snapshot
built without the flag. Cycle 5's manifest names the frozen rule version in
its baseline snapshot tag; baseline and measure must record the identical
threshold artifact sha; the driver's config-identity check makes a mismatch a
refusal. The §2 predictions are stated against the frozen cut and are NOT
defined without it.

If cycle 4 ever reverts: do not open. There is no soft-degrade mode —
re-deriving Otsu on the discounted distribution would let the cut chase the
discount, manufacture flips in BOTH directions, and charge them to a rule
already under suspicion. The manifest carries
`depends_on: cycle4-frozen-cut (closed, keep — CYCLE_LOG.jsonl 2026-08-04)`
and review must verify it against the log line, not this file.

## 5. Risks & open questions — for the adversarial reviewer to attack

- **Q1 — Is this cycle fitting to the panel through a 155-sample keyhole?**
  DISAGREEMENT_REPORT.md's own closing section forbids editing the matcher
  "to fix these two cases". This design's defense: the rule is motivated by a
  representational principle (recorded patient structure must be able to
  bear on price), its rationale and its flip bounds are computed document-
  side, the keep decision cites flip adjudications only, and the census
  check is deferred to the checkpoint. But the census DID direct attention
  here, the class IS 53% of disagreement, the defining case IS predicted
  to flip — and §0 now concedes the cycle moves 1/155 of the class it is
  named for. If disclosure-plus-document-side-adjudication doesn't hold that
  line, the whole amended-cycle policy fails with it — attack it here.
- **Q2 — FN re-creation at the margin — now a BINDING requirement on the
  backfill.** The m0248 abuse FN (harm-avoidance, `#avoid_abuse ¶1`, panel
  5/6-relevant, census `fn_names_cannot_meet`) shows the sweep already misses
  abuse-of-individuals content on this behaviour. m0248's atoms
  (`shouldnot_engage_abuse`, chain-free) are untouched by this rule TODAY —
  but a backfill that mis-chains it `__model_user` ("don't abuse your
  interlocutor") would let the taint rule suppress a clause the panel is
  unanimous on. Adopted from the review as a requirement, carried in
  BACKFILL_DESIGN.md §4: golden review is REQUIRED for every backfilled
  chain landing on (i) any clause in any current predicted set, (ii) any
  ever-adjudicated-correct clause (m0221/m0222: a kept taint marks them
  ×0.25 forever), (iii) m0248 by name.
- **Q3 — is the review budget spent at the right time?** Superseded in part
  by §7: the recommendation is now to run cycle 5 AFTER the backfill, so the
  one adjudication prices the real population. The residual question for
  review: does pricing-after-backfill blur attribution (which flips are the
  mechanism's, which are the new chains'), and is the dossier-level
  provenance split in §7 sufficient?
- **Q4 — the under-18 boundary.** Now pre-registered as the cycle's central
  adjudication (§2). The standing sub-question: should `under_18`-sectioned
  clauses be exempted from taint, or is that an unprincipled carve-out? The
  design's position: no carve-out; adjudicate and accept the verdict,
  including revert.
- **Q5 — chain semantics.** RESOLVED by F1 + the chain audit: patients =
  `chain[1:]`, length-1 = patient-free (§1.2), and the convention is no
  longer "loosely attested" — all 109 instances were adjudicated against
  clause text (97 correct, 12 repaired) in the chain-repair cycle. The
  residual: `('user','model')`-shaped chains read patient = model; any case
  where that reading misprices is a §1.2 finding.
- **Q6 — the discount constant.** 0.25 is hand-set and unsweepable
  (invariant 9), but no longer unfalsifiable-by-design: the d-plateau
  ({0.1, 0.25, 0.4} → identical flip set) is pinned at OPEN (§1.4, §2). If
  the recomputed plateau does not hold, the constant must be re-derived from
  golden-set patient-contrast cases before build — "hand-set with stated
  reasoning" is accepted only on a plateau.

## 6. Fit to the cycle ceremony

- **Manifest (OPEN):** description "patient-aware match pricing v2.0 —
  recorded principal-chain patients discount mismatched and uniformly-
  mismatch-attested matches"; document-side rationale §1.3's;
  `depends_on: cycle4-frozen-cut (closed, keep)` + the §7 sequencing
  declaration; `census: deferred_to_checkpoint`; `census_scope: dev` (the 3
  Model-Spec cells; constitution cells untouched); baseline snapshot tag =
  the latest closed KEEP configuration per §7;
  `pricing_version: "2.0"`.
- **files_to_change:** `patient.py` (new: PatientIndex, PRICING_VERSION,
  anchor check per F4), `relevance.py` (Weights field
  `patient_mismatch_discount` only), `behaviours_query.json` (the three
  `patients` declarations ONLY — I6), `snapshot.py` + `dossier.py` (config
  identity, version dispatch incl. absent⇒legacy, normalizer_drift tagging,
  explain passthrough), `test_patient.py` (new; registered in
  `conftest._OPTIONAL`), `test_snapshot.py`/`test_dossier.py` (identity + F9
  pins). `validate_behaviours.py` is NOT in the diff (F4). The two-sided
  one-variable check (F5) pins everything else, `containment.json` and all
  annotation artifacts included, unchanged.
- **Gate tests:** the §3 invariants I1–I6, each verified RED first against
  the unfixed code or a planted mutant (cache-cleared); the
  `diff_snapshots` pricing_version surfacing test (blocking precondition);
  `snapshot.assert_frozen_thresholds` on baseline and measure snapshots
  (§4).
- **PREDICT artifact:** §2's OPEN-phase recomputed pin, verbatim — computed
  flip identity and composition, raw-score zero-newly-predicted as computed
  fact, normalizer deltas disclosed, d-plateau, helpfulness/caution
  zero-flip. Frozen at PREDICT with the manifest (F5).
- **review_required: true.** This file is the review's input; §5 is its
  agenda. FORBIDDEN-token check on every new CLI/field name before
  implementation (the `--verdicts` lesson). `patient.py` joins the
  query-adjacent, panel-blind set scanned by test_no_reference_leak.py.
- **Flip handling:** the OPEN recomputation states the count before PREDICT
  freezes; over-budget → the §4 policy template (split or pre-registered
  stratified sample by behaviour × section × chain-provenance).
- **DECIDE:** keep/revert cites flip adjudications only; a failed prediction
  obliges written justification, never auto-reverts; census consultation
  waits for the checkpoint and stamps DEV.

## 7. Depends on the backfill? — YES in sequence: cycle 5 runs AFTER it

The question revision 1 left implicit, answered explicitly. Two orderings:

- **Cycle 5 first** (CYCLE5_REVIEW's ladder as written: chain-audit →
  cycle 5 → backfill "measured through the adjudicated pricing mechanism").
  What it prices: the 31 census-era chain-attested max-clauses — the
  reviewer's computed result says that is 12 flips, exactly 1 of them in the
  nominal target class. Its virtue: a small, clean first adjudication of the
  mechanism, and the backfill's later effect is then measured through an
  already-kept rule.
- **Cycle 5 after the backfill** — **RECOMMENDED**, for three reasons:
  1. **Effect size.** Before the backfill, this cycle is a 1/155 fix wearing
     a 53% class's name (§0). After it, the pricing rule reads patient
     structure across the whole population the backfill decorates
     (BACKFILL_DESIGN.md §3: ~500-instance candidate pool) — the cycle's
     flips are then the REAL answer to whether patient pricing helps, and
     the review budget buys one adjudication of the real question instead of
     two adjudications (a 12-flip rehearsal, then the actual event) of the
     same under-18 boundary.
  2. **The old reason for cycle-5-first has dissolved.** "Measure the
     backfill through an adjudicated mechanism" presumed the backfill would
     move scores. BACKFILL_DESIGN.md is designed measurement-invariant
     (decoration-blind join + zero-flip gate, its §6): a kept backfill
     changes NOTHING measurable until pricing exists, so there is nothing
     for a pre-existing pricing rule to measure. The only pricing-visible
     event in either ordering is cycle 5 itself; running it once, last,
     confounds nothing.
  3. **Attribution stays clean at dossier level, not cycle level.** Every
     flip dossier's `patient_pricing` records name the chain behind the
     discount, and every chain carries provenance (repair-era vs backfilled,
     via vocabulary_migrations.json reasons). The manifest pre-registers the
     flip-set stratification by chain provenance, so "the mechanism was
     wrong" and "a backfilled chain was wrong" stay separable — the latter
     reverts one migration, not the cycle.
  Cost, stated: the post-backfill flip volume is real and may exceed the
  30-flip budget — the §4 template (stratified sample by behaviour × section
  × chain-provenance) is the pre-registered path, and the OPEN recomputation
  (§2) decides before PREDICT freezes. A 12-flip rehearsal would have been
  comfortable; the real question is not.

Binding consequence: cycle 5's baseline snapshot tag = the backfill cycle's
keep snapshot (which itself sits on the chain-repair keep); its manifest adds
`depends_on: patient-backfill (closed, keep)` alongside the cycle-4
dependency, verified against CYCLE_LOG.jsonl. If the backfill cycle reverts
or stalls, cycle 5 MAY open against the chain-repair baseline instead — but
then §0's 1/155 scope statement is the design's own argument that it
probably should not.
