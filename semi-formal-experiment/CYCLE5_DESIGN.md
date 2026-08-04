# CYCLE 5 — patient/kind-aware match pricing (design, 2026-08-03, for adversarial review)

One cycle under CYCLE_DESIGN.md (amended form), shape: code/matching fix.
Target class: `fp_promiscuous_atom` — 155/294 (53%) of all tool-vs-panel
disagreement in the ext_v1_merged__audit_v1 census, the class DISAGREEMENT_
REPORT.md's m0276 case defined: patient-free / patient-wrong atoms firing on a
clause about a different party. This design prices recorded patient structure
into the atom channel. DESIGN ONLY — no code ships with this file.

## 0. Scope honesty, first

Measured over the census dossiers: of the 155 `fp_promiscuous_atom` verdicts,
only **31 max-clauses carry any principal-chained atom at all** (29 of those
chains name `user`). The other ~80% of the class is carried entirely by
patient-FREE atoms — atoms whose annotation records nothing about who is
protected. **No pricing rule can read structure that was never written.** This
cycle therefore does two things and claims only the first:

1. Makes recorded patient structure PAY: a chain naming the wrong patient
   becomes counter-evidence, which today it cannot be even in principle
   ("an unmatched atom contributes 0, never a penalty" — DISAGREEMENT_REPORT).
2. Establishes the pricing mechanism that makes a FUTURE patient-backfill
   annotation cycle worth running. The 80% patient-free mass is that cycle's
   target, not this one's. Attacking it by discounting patient-free matches
   directly is considered and REJECTED below (§2, option B) with numbers.

## 1. The pricing rule

### 1.1 Where the query's patient context comes from (label-free, document-side)

A new optional field on each entry of `behaviours_query.json`:

```json
{"slug": "harm-avoidance-to-third-parties", ..., "patients": ["third_party"]}
```

- Values drawn from `grammar.PRINCIPALS` only.
- **Document-anchored declaration**: `validate_behaviours.py` REFUSES a
  `patients` list unless each declared principal's readable form (or an
  enumerated surface synonym: "third parties"/"those outside the conversation"
  → `third_party`; "users" → `user`) appears in that behaviour's own
  `name + definition` text. The declaration is authored by us, licensed by the
  query file's own prose — never by a panel number. The panel file is never
  opened; the field lives in the query-side file whose split from the
  reference file exists precisely so this is checkable
  (test_no_reference_leak.py).
- Proposed declarations: harm-avoidance-to-third-parties → `["third_party"]`
  ("harm third parties, society, or those outside the conversation");
  helpfulness → `["user", "developer"]` ("the users and developers it works
  with"); avoiding-over-and-under-caution → `[]` (its definition names no
  protected party). **An empty or absent list disables patient pricing for
  that query entirely — bit-identical scores.**
- The behaviour atoms' own chains (audit_v1 carries 7: 4 `__model_user` on
  helpfulness, 1 `__model_third_party` on harm, 2 on caution) are used as a
  CONSISTENCY CHECK only — the validator warns if a query atom's chain patient
  is outside the declared set — not as the source. They are too sparse
  (0 chains in behavior_atoms_ext_v1) to be the source, and sourcing from
  them would make the patient context an accident of atom-drafting.

Rejected alternative: mechanical extraction from the definition text. Brittle
(pronoun/paraphrase misses), and a silent extraction failure = silently
disabled pricing — the dead-channel failure mode this repo has hit twice.
A declared field with a mechanical anchor check keeps the declaration loud
and the license checkable.

### 1.2 The patient of an atom (clause side)

`patients_of(name)`: parse via `grammar.parse_name`. No principal chain →
**patient-free** (None — absent is absent, never defaulted, same contract as
`role_of`). Chain of length 1 → that principal ("the party concerned"). Chain
length ≥ 2 → the set `chain[1:]` (grammar.describe: "WHO: X acts, upon Y").
So `must_advise_immediate_help__user` → {user};
`shouldnot_lie_by_commission__model_third_party` → {third_party};
`mustnot_disclose_reasoning__model_user` → {user}. This reading is pinned by
test; if the reviewer thinks chain[1:] is the wrong patient reading for any
shipped chain shape, that is a finding against §1.2, not a tuning knob.

### 1.3 The rule (PRICING_VERSION "2.0")

For a query with non-empty declared patients P, on each clause:

- **Per-atom factor.** Each credited atom match (exact or containment
  subsumption) through a clause atom `a`:
  - `patients_of(a) ∩ P ≠ ∅` → **consistent: factor 1.0 — priced bit-identical
    to today.** (Invariant I1, §3.)
  - `patients_of(a)` non-empty, disjoint from P → **mismatched: factor
    `patient_mismatch_discount`** (proposed 0.25 — see §1.4).
  - patient-free → factor 1.0 from this layer.
- **Clause-taint factor** (the m0276 mechanism — clause-side presence as
  counter-evidence). If the clause's annotation carries ≥ 1 chained atom and
  **every** chained atom on it is mismatched with P (none consistent), the
  clause is *uniformly mismatch-attested*: every atom credit on that clause —
  including patient-free matches — takes factor `patient_mismatch_discount`.
  Rationale, document-side: the annotation records who this clause protects
  (m0276: `must_advise_immediate_help__user`), and the patient-free stock
  atoms on the same clause (`imminent_bodily_harm`, `human_safety`-likes)
  inherit that recorded context. One consistent chain anywhere on the clause
  defeats the taint (the m0248 guard, §5).
- **Single application, no compounding**: effective factor per credited match
  = `patient_mismatch_discount` if (that atom mismatched) OR (clause tainted),
  else 1.0. Never d².
- Patient-free clauses (no chains at all — the majority) are **priced exactly
  as today**. Absence of decoration is never penalized (option B rejected,
  §2).
- The lex, kind, and section channels are untouched; section recomputes from
  the discounted local totals as it always has (section is defined over local
  scores, not frozen against them — this propagation is inside the flip
  prediction, §2).

Options for pricing patient-free atoms under a patient-specific query,
considered and rejected with document-side counts (all label-free; computed
over the current census configuration, annotations_ext_v1_merged +
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
authored claim about who the clause concerns. It will NOT be swept: any sweep
selects against the panel and violates contract §5 invariant 9. 0.0 (outright
exclusion) is rejected because chains are model-authored and unaudited at
scale — exclusion makes a single mis-chained atom able to erase a clause's
whole atom channel. If the reviewer thinks 0.25 vs 0.4 vs "reuse
kind_mismatch_discount" matters, the answer must come from document-side
reasoning or golden-set cases, not a grid.

### 1.5 Mechanism and housing (the containment house pattern)

- New opt-in subclass `PatientIndex(ContainmentIndex)` (module `patient.py`),
  constructor `..., *, edges=(), query_patients=None`. `query_patients` maps
  slug → frozenset of principals; None/empty → **bit-identical to
  ContainmentIndex** (which with edges=() is bit-identical to RelevanceIndex).
  Nothing constructs it with patients unless a caller opted in by name;
  nothing silently reads behaviours_query.json's field.
- `PRICING_VERSION = "2.0"` in patient.py; snapshot config records
  `pricing_version` and the per-slug declared patients (with the
  behaviours_query sha it already records). Old behavior reachable forever:
  construct without `query_patients`, or any snapshot recording
  pricing_version ≤ 1.1 reconstructs through the old classes — the F9
  contract, same as containment's.
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
parent; its chain therefore never enters `stem`-level matching, only this
pricing layer). Composition is multiplicative on the credit:

    credit = min(idf(subsumer), idf(clause_atom)) * kind_factor * patient_factor

with `patient_factor ∈ {1.0, patient_mismatch_discount}` per §1.3's single-
application rule. Both discounts ≤ 1, so the never-outprice invariant is
UNWEAKENED: a subsumption match still never outprices the exact match on the
same evidence — and a patient-mismatched exact match is discounted by exactly
the same factor as a patient-mismatched subsumption through the same atom, so
the overlay cannot become a discount-dodging route. Matching structure
(each query atom credited once, each clause atom once) is untouched.

## 2. PREDICT — mechanism-level, document-side, checkable with zero panel contact

This change only ever LOWERS scores (§3, I2). Under the frozen per-behaviour
cut (§4), that yields:

- **`newly_predicted` flips: exactly 0.** Any newly_predicted flip falsifies
  the monotonicity claim outright and is a bug, not a judgment call.
- **`no_longer_predicted` flips: only on clauses matching the mechanism
  signature** — "a clause whose annotation carries ≥ 1 principal chain, all
  of whose chains name patients outside the query's declared set, and whose
  atom channel carries enough of the score that the discount drops it below
  the frozen cut" — plus, second-order, section-mates of such clauses whose
  own score leaned on the section channel that the tainted clause's local
  total fed.
- Counts, from the label-free document-side census of the current
  configuration (rerun and pinned at OPEN):
  - **helpfulness: 0 flips.** Its declared patients {user, developer} cover
    every `__model_user` chain in the vocabulary; 33 predicted clauses carry
    consistent chains, 0 carry uniformly-mismatched ones. This cell is the
    no-regression control.
  - **avoiding-over-and-under-caution: 0 flips** (patients [] → pricing
    disabled; bit-identity is a gate test, not a prediction).
  - **harm-avoidance-to-third-parties:** the uniformly-mismatch-attested
    predicted set is exactly 16 clauses: m0221, m0222, m0260, m0263, m0264,
    m0276, m0579, m0580, m0581, m0584, m0585, m0588, m0589, m0590, m0591,
    m0593 (mostly `__user`/`__model_user` chains: self-harm, mental-health,
    under-18 sections). At d=0.25, first-order arithmetic (atom channel
    discounted, cut frozen) flips **m0276 out** (0.358 → ~0.20 vs cut
    ~0.237) and leaves the other 15 in (their normalized scores sit well
    above the cut or their atom share is small). Allowing section
    propagation: **expected 1–5 no_longer_predicted flips, all within the
    16-clause tainted set or its section-mates; hard bound ≤ 16 + their
    section peers.** Anything flipping outside that named set fails the
    prediction.
- Adjudication expectations (the flip-seat, briefs/flip_adjudicator.md):
  m0276's removal expected `correct` — the passage's every harm-bearing noun
  phrase is the user, per the plain reading the hand autopsy already did.
  Under-18 flips, if section propagation produces any, expected CONTESTED:
  a teen user is the user, but "prioritize teen safety" clauses arguably
  concern third parties (minors as a protected class) — a `regression`
  verdict there is a real finding against the taint rule, and reverting on
  it is the designed outcome, not a failure of process.
- Well under the F4b flip budget (30). If MEASURE counts more, the change is
  not doing what this design says and the §4 template fires.

Provenance disclosure (policy §1: candidates from anywhere, provenance
recorded): this cycle was seeded by the m0276 autopsy and the census's 53%
figure — both panel-reading instruments. The keep decision will cite only the
flip adjudications; the census check happens at the next pre-registered
checkpoint, DEV-stamped. Naming m0276 in the prediction is mechanism-level
("the one predicted clause whose taint discount crosses the frozen cut"),
permitted and required by amendment 1; whether that line holds is for the
reviewer (§5, Q1).

## 3. Invariants (each becomes a gate test; verify-RED applies)

- **I1 — no regression on correct matches.** A patient-consistent match is
  priced bit-identically to today: factor 1.0 on both layers, and a clause
  carrying any consistent chain is never tainted. Test: score equality (not
  approx) on every helpfulness clause, full config, and on every clause of
  every behaviour under `patients=[]`.
- **I2 — never-underprice-below-zero + monotone-downward.** All factors lie
  in [d, 1.0] with d ≥ 0; channel scores stay ≥ 0. For every (behaviour,
  clause): score_v2.0 ≤ score_v1.1, with equality wherever no mismatch
  evidence exists. Corollary tested directly: predicted_v2.0 ⊆ predicted_v1.1
  at a fixed cut.
- **I3 — monotone in the declared set.** Enlarging a behaviour's `patients`
  never lowers any clause's score (more chains become consistent, taints can
  only be defeated). Empty set = identity.
- **I4 — containment composition.** Never-outprice preserved (mutant: drop
  the min-idf cap or the patient factor from the subsumption path → a pinned
  test must go red); a chained atom still cannot appear in any licensed edge;
  discount applied once, never d².
- **I5 — F9 reconstruction.** PRICING_VERSION "2.0" recorded in snapshot
  config; snapshots at ≤ 1.1 reconstruct through the old pricing bit-exact;
  dossier's ReconstructionMismatch self-check extended to dispatch on the
  recorded version. `diff_snapshots` must surface `pricing_version` in
  `config.changed` — the standing cycle-3 escalation (c) becomes a blocking
  precondition here, because THIS cycle's diff is meaningless if the config
  change is invisible.
- Mutation checks under the HANDOFF bytecode-cache discipline (clear
  `__pycache__`, assert the mutant loaded).

## 4. The cycle-4 dependency (hard gate)

This is a **score-reducing change under a derived cut**. Today's cut is Otsu
over each query's own score distribution: lowering scores MOVES the cut,
so flips would mix `match_change` with `threshold_drift` — the exact drift
class (m0422, three cycles running) that put the Otsu rule under formal
suspicion, and the adjudication question would be muddled for every flip.

**Cycle 4 — the versioned/frozen cut (CYCLE_DESIGN.md "first customer":
per-behaviour thresholds chosen label-free via the cut_stability route,
pre-registered, recorded as a threshold rule version in snapshot config) —
must be CLOSED with KEEP before cycle 5 OPENs.** Cycle 5's manifest names the
frozen rule version in its baseline snapshot tag, and its baseline and
measure snapshots must record the identical threshold rule; the driver's
config-identity check makes a mismatch a refusal. The §2 predictions are
stated against the frozen cut and are NOT defined without it.

If run before cycle 4 (or if cycle 4 reverts): do not open. There is no
soft-degrade mode — re-deriving Otsu on the discounted distribution would
let the cut chase the discount, manufacture flips in BOTH directions
(newly_predicted included, breaking §2's zero), and charge them to a rule
already under suspicion. The manifest carries
`depends_on: cycle4-frozen-cut (closed, keep)` and review must verify it;
absent a driver-level dependency field this is enforced by the review gate
and the snapshot config identity, and that gap is itself listed in §6 for
the v1.1 driver queue.

## 5. Risks & open questions — for the adversarial reviewer to attack

- **Q1 — Is this cycle fitting to the panel through a 155-sample keyhole?**
  DISAGREEMENT_REPORT.md's own closing section forbids editing the matcher
  "to fix these two cases". This design's defense: the rule is motivated by a
  representational principle (recorded patient structure must be able to
  bear on price), its rationale and its flip bounds are computed document-
  side, the keep decision cites flip adjudications only, and the census
  check is deferred to the checkpoint. But the census DID direct attention
  here, the class IS 53% of disagreement, and the defining case IS predicted
  to flip. If disclosure-plus-document-side-adjudication doesn't hold that
  line, the whole amended-cycle policy fails with it — attack it here.
- **Q2 — FN re-creation at the margin.** The m0248 abuse FN
  (harm-avoidance, `#avoid_abuse ¶1`, panel 5/6-relevant, census
  `fn_names_cannot_meet`) shows the sweep already misses abuse-of-
  individuals content on this behaviour. m0248's atoms
  (`shouldnot_engage_abuse`, chain-free) are untouched by this rule TODAY —
  but a future patient backfill that mis-chains it `__model_user` ("don't
  abuse your interlocutor") would let the taint rule suppress a clause the
  panel is unanimous on. The one-consistent-chain-defeats-taint guard and
  golden review of any chain backfill are the mitigations; are they enough,
  and should the backfill cycle be REQUIRED to golden-review every chain
  whose clause the current predicted set contains?
- **Q3 — census FN growth forecast.** At the next checkpoint, each kept
  flip-out becomes, at worst, one new FN dossier classed
  `fn_kind_or_patient_discount` per mapped passage. Bounded by the ≤ 16
  clause set × their passage fan-in; expected 1–5 clauses. But the census
  also predicts the HEADLINE effect is small: ≤ 31/155 of the target class
  even carries chain evidence, so cycle 5 cannot move the 53% much — is a
  pricing cycle whose main payoff is enabling a future annotation cycle
  worth its review budget now, or should it wait and land WITH the backfill?
  (Design's position: land first, so the backfill's effect is measurable
  through an already-adjudicated pricing mechanism rather than confounded
  with it.)
- **Q4 — the under-18 boundary.** Chains on m0579–m0593 name `user`; the
  behaviour's patients are third parties. Minors-as-users sit exactly on the
  patient boundary (protected class vs conversation participant). The taint
  rule treats `__user` as counter-evidence there. Section propagation could
  flip some of these; the design accepts contested adjudications (§2) — but
  should `under_18`-sectioned clauses be exempted from taint, or is that an
  unprincipled carve-out?
- **Q5 — chain semantics.** §1.2 reads patient = chain[1:] (or the sole
  member). `('user','model')` chains exist (2 instances): under this reading
  their patient is `model`. Is that right, or is the chain convention too
  loosely attested (109 instances, one annotation batch, never audited as a
  population) to price at 0.25 strength?
- **Q6 — the discount constant is unfalsifiable by design.** 0.25 is hand-
  set and unsweepable (invariant 9). The flip set is step-function-sensitive
  to it near the cut (0.4 keeps m0276 in? — first-order arithmetic says
  0.358·(1−0.75·share)... the OPEN-phase pin must state the flip set at the
  chosen d). Is "hand-set with stated reasoning" acceptable, or does an
  unsweepable constant need a golden-case criterion (e.g. derived from the
  golden set's patient-contrast pairs) to be more than taste?

## 6. Fit to the cycle ceremony

- **Manifest (OPEN):** description "patient-aware match pricing v2.0 —
  recorded principal-chain patients discount mismatched and uniformly-
  mismatch-attested matches"; document-side rationale §1.3's; 
  `depends_on: cycle4-frozen-cut`; `census: deferred_to_checkpoint`;
  `census_scope: dev` (the 3 Model-Spec cells; constitution cells untouched);
  baseline snapshot tag = the cycle-4 keep configuration;
  `pricing_version: "2.0"`.
- **files_to_change:** `patient.py` (new), `relevance.py` (Weights field
  `patient_mismatch_discount` only), `behaviours_query.json` (the three
  `patients` declarations), `validate_behaviours.py` (anchor check),
  `snapshot.py` + `dossier.py` (config identity, version dispatch, explain
  passthrough), `test_patient.py` (new; registered in `conftest._OPTIONAL`),
  `test_snapshot.py`/`test_dossier.py` (identity + F9 pins). The two-sided
  one-variable check (F5) pins everything else, `containment.json` and all
  annotation artifacts included, unchanged.
- **Gate tests:** the §3 invariants I1–I5, each verified RED first against
  the unfixed code or a planted mutant (cache-cleared); plus the
  `diff_snapshots` pricing_version surfacing test (blocking precondition).
- **PREDICT artifact:** §2 verbatim — zero newly_predicted; no_longer_
  predicted ⊆ the named 16-clause set + section peers, expected 1–5,
  m0276 named; helpfulness and caution zero-flip. Frozen at PREDICT with the
  manifest (F5).
- **review_required: true.** This file is the review's input; §5 is its
  agenda. FORBIDDEN-token check on every new CLI/field name before
  implementation (the `--verdicts` lesson). `patient.py` joins the
  query-adjacent, panel-blind set scanned by test_no_reference_leak.py.
- **Flip handling:** expected well under the 30 budget; over-budget →
  the §4 policy template (split or pre-registered stratified sample).
- **DECIDE:** keep/revert cites flip adjudications only; a failed prediction
  obliges written justification, never auto-reverts; census consultation
  waits for the checkpoint and stamps DEV.
