# LATENT FIX REGISTRY — plans for issues with no current instance

Purpose: a registry of **latent/speculative fixes** — concerns that are real in principle
and have a sketched response, but for which an enumeration or audit found **zero current
instances**, so implementing them now would be building for a problem we do not have.
Each entry stays here, **not implemented**, until a real instance appears, with a named
TRIGGER that would justify implementation. This keeps us from shipping speculative
machinery while not losing the plan.

Origin (2026-08-05): coordinator ruling on D3 — the proposed example-kind taint rule was a
fix for a speculative issue the enumeration showed does not exist; Matt directed that such
plans be registered here rather than implemented.

Protocol:
* An entry belongs here when the concern is genuine but a current enumeration/audit found
  no instance. If there IS a current instance, it is not latent — it belongs in
  OUTSTANDING_WORK.md instead.
* Each entry names: ISSUE, EVIDENCE OF CURRENT ABSENCE, PLAN IF IT APPEARS, TRIGGER,
  STATUS.
* Entries are re-checked when the trigger fires or at a periodic review. If an entry's
  trigger fires, promote it to OUTSTANDING_WORK.md as active work.

---

## LF-1 — example-kind distinct taint rule (from designer ruling D3)

* **ISSUE.** Example passages' modeled response is structurally addressed to the user
  (the example shows the model speaking to the user), so it was hypothesized that
  example-kind clauses might need a DISTINCT taint rule rather than the uniform
  beneficiary-attribution rule (§5.3).
* **EVIDENCE OF CURRENT ABSENCE.** `D3_EXAMPLE_CLAUSE_ENUMERATION.md` (2026-08-05): over
  all 183 example-kind clauses, uniform attribution produces 0 wrong-result cases and 0
  undefined compositions. The motivating concern (user-directed remedial acts, 197/202
  chains) is real but is exactly what §5.3 absorbs. No special rule has work to do.
* **PLAN IF IT APPEARS.** Design an example-kind taint rule. NOTE: the §3 wall
  (m0275 vs m0276 structural identity) shows any ATTRIBUTION-FREE example rule would
  resurface user-harm clauses (m0291/m0264/m0290), so such a rule must itself be
  beneficiary-aware, and needs its own design + adversarial review — it is NOT sketched
  yet.
* **TRIGGER.** A future example-kind clause where uniform attribution produces a wrong
  result (wrong suppression or wrong surfacing), or a distribution shift in example
  clauses that the enumeration's shape buckets do not cover.
* **DETECTION (fail-loud tripwire — lands with the S3b build).** So the latent case fails
  LOUDLY and points here rather than silently mispricing:
  1. POPULATION PIN: a test asserts the example-kind population equals the enumeration's
     vetted set (the 183 ids). On any change (a new/re-annotated example clause), FAIL:
     "example-clause population changed since the D3 enumeration — re-run the enumeration
     before trusting example-clause pricing (see LATENT_FIX_REGISTRY.md LF-1)." This is
     the guard that catches a FUTURE instance the enumeration never vetted.
  2. LOAD-BEARING PIN: assert the attribution-load-bearing examples (m0176/m0300/m0467)
     surface for a third-party query via the attributed PROTECTED party (not the chain
     recipient); on failure, FAIL referencing LF-1.
  3. ADJUDICATION SHAPE-FLAG: any example-kind flip matching the finding-(i) shape is
     tagged in its dossier as an LF-1 candidate requiring explicit disposition
     (confirm-uniform, or promote LF-1 to active work) — never silently absorbed.
* **STATUS.** NOT IMPLEMENTED — S3b uses UNIFORM (D3 ruled 2026-08-05). Registered so the
  idea is not lost and not re-litigated from scratch if the trigger fires.
* **REVISIT (coordinator 2026-08-05).** Keep the DETECTION check MINIMAL for now (population
  pin + the 3 load-bearing clauses + shape-flag; NOT the full 183-clause pin). We do not yet
  know whether tripwires are useful or how many latent fixes will accumulate. Revisit the
  tripwire strategy if it costs more than it is worth, or if it is not catching enough —
  widen, narrow, or drop on that evidence.

---

## LF-2 — the interpretation layer (`INTERPRETATION_LAYER_DESIGN.md`)

* **ISSUE.** Judgement calls that the analysed document does not settle — boundary rulings,
  implied bearers — are made in order to answer any relevance question, but they are recorded
  as prose in cycle directories. They are invisible in the tool's output, so a reader cannot
  see which of them an answer depended on, cannot cheaply disagree, and cannot see what a
  different reading would cost. The design proposes: interpretations as registered entries
  (endorsed reading + named alternative + grounds + approver + revocable lifecycle), carried
  as a version-key axis on the config-driven builder, cited per hit in the explain trail,
  switchable by end users as a *view* while our own measurement stays on one frozen,
  opinionated, all-on set.

* **⚠️ PROTOCOL NOTE — this entry bends the registry's rule, deliberately.** The protocol says
  an entry belongs here only when an audit finds **zero** current instances. Interpretations
  are not zero: **I-01** (m0108's representation boundary — ruled in prose,
  `cycles/patient-pricing-2026-08-04/M0108_SEAT_DEFECT_REVIEW.md`), **I-02** (foreseeable
  downstream harm — decided *silently* inside that same review's ground (e), while the
  behaviour definition says "weigh the **potential** harm"), **I-03** (D3's uniform
  example-clause rule), and the implied-effects entries beginning with **m0239** all exist
  today. What is absent is not the instances but the **machinery**: nothing currently breaks
  for lack of it, and no measurement is wrong because of it. So the MACHINERY is parked here;
  the known instances are a live backlog and belong in `OUTSTANDING_WORK.md`, not in this
  registry. Do not read this entry as "there are no interpretations yet."

* **EVIDENCE OF CURRENT ABSENCE (of the need, not the instances).** Every interpretation made
  so far has been recorded in prose with grounds, by a named seat, in a cycle directory that
  survives. The audit trail exists; it is just not machine-readable or reader-facing. No
  reported number is currently wrong for want of this layer, and no cycle has been blocked by
  it. Building it now would be building presentation and toggling machinery ahead of a
  consumer that does not yet exist (there is no shipped reader UI).

* **PLAN IF IT APPEARS.** `INTERPRETATION_LAYER_DESIGN.md`, in full: the entry schema
  (generalizing the implied-effects entry type rather than inventing one), the
  `interpretation_set` config axis on `index_builder.py` with ABSENT = no interpretations so
  every existing snapshot reconstructs unchanged, the explain-trail `interpretations` field
  (**empty = licensed by document text alone**, which is the distinction that carries the
  value), and §6's anti-fitting constraints — frozen sha-pinned set, adopted on document-side
  grounds only, one recorded vector never a swept grid, user views structurally incapable of
  producing a reported number.

* **TRIGGERS** (any one promotes LF-2 to active work):
  1. **A reader consumer ships.** The moment there is a user-facing surface
     (`site/spec-reader-test/` is the prototype), toggles have someone to serve and the
     absence becomes user-visible rather than internal.
  2. **An external reader contests a boundary.** The first time someone disagrees with a
     ruling and we cannot show them the alternative reading's flip set cheaply, the argument
     costs more than the machinery.
  3. **A second seat-defect review lands.** One (m0108) is an incident; two is a class, and a
     class wants a registry.
  4. **A flip is adjudicated on a definitional boundary rather than on document text.** That
     is an interpretation deciding a cycle outcome while unregistered — the sharpest signal
     available.
  5. **The generalization phase or the constitution battery begins.** A new document brings
     its own boundary questions; doing that at scale while recording rulings as prose repeats
     the m0108 pattern with no way to audit it.
  6. **The implied-effects layer is built.** Its entries are LF-2 entries of one kind. Ship
     it against the general schema or accept a migration later.

* **DETECTION (tripwires — to be implemented, see the note below).** Minimal, in LF-1's
  spirit:
  1. **Ambiguity-language scan.** A test scans cycle `decision.json` justifications,
     `flip_verdicts*.json` reasons, and `*_SEAT_DEFECT_REVIEW.md` files for
     definitional-ambiguity markers ("under-determines", "genuine ambiguity", "both readings",
     "boundary", "seat defect") and FAILS with a pointer here when a hit is not covered by a
     registered interpretation id. This is trigger 3 and 4 made mechanical.
  2. **Reader-surface pin.** A test fails if a user-facing reader gains a scoring path while
     no interpretation artifact exists — trigger 1, mechanical.
  3. Triggers 2, 5 and 6 are human-noticed; they are listed so they are not lost, not because
     a test can catch them.

* **STATUS.** NOT IMPLEMENTED. Design written and parked 2026-08-05.

* **⚠️ IMPLEMENTATION DEBT ACROSS THIS REGISTRY (coordinator, 2026-08-05).** LF-1's DETECTION
  tripwires are specified but also NOT IMPLEMENTED — LF-1 defers them to "the S3b build's
  test set", which has not been built. A registry of parked designs whose tripwires never
  fire is a filing cabinet, not a safety net: the entries would be found only by someone
  already reading this file, which is exactly the person who does not need the reminder.
  **Action:** implement LF-1's and LF-2's tripwires together as one small unit, independent of
  the S3b build. Both are test-only, deterministic, and cost nothing to run.

## LF-3 — census vector() flattened representations (Arc1-e adversarial review, 2026-08-21)

* **ISSUE.** `satisfiability_census.vector()` (graph_v2/behavior_pilot) flattens three
  key-wise/count-sensitive instrument structures: (a) `purpose_hit`'s per-key
  actor∧purpose conjunction (vector carries unioned actors × purposes); (b) the
  all-plumbing exclusion predicate (vector carries the plumbing-suffix set but not key
  counts, so "all keys flagged" is inexpressible when non-plumbing keys are invisible);
  (c) fail-open-on-no-keys vs keys-with-empty-values asymmetry. Any of these could make
  two same-vector nodes engage differently, biasing the census toward false UNSAT
  (hiding separability) on those classes.
* **EVIDENCE OF CURRENT ABSENCE.** Arc1-e clean-context adversarial review (2026-08-21):
  full-corpus recomputation over every same-vector class under all three live v18
  modules found ZERO instances of all three divergences. The same review's
  governs_conditional audit found it accidentally safe on current classes as well;
  governs_conditional and party_concern are NOT registered here — they have fail-loud
  guards in `census()` instead (they are declarable-but-unrepresentable, which the
  guard converts into a hard stop).
* **PLAN IF IT APPEARS.** Extend `vector()` with key-resolved structure (per-key
  actor-purpose pairs, plumbing/key counts, key-presence flags), capture a new frozen
  prefixture, re-run the monotone-refinement test suite, adversarial re-review. Follows
  the Arc1-e prereg template (CENSUS_VECTOR_FIX_PREREG.md).
* **TRIGGER.** Any same-vector class found (by pre-census audit) whose members differ on
  one of the three structures; re-audit is REQUIRED at every instrument freeze
  (round-4 certification, each generalization run) until then.
* **STATUS.** NOT IMPLEMENTED — zero instances verified 2026-08-21. Registered so the
  flattening is a KNOWN sufficiency scope, not an accident; the census docstring points
  here.

## LF-4 — terminality fence reads refinement marks fail-open (Arc1-b review, 2026-08-21)

* **ISSUE.** `verify_terminal.py::pending_vocab_nodes()` (graph_v2 behavior_pilot)
  guards the context-atoms and census files but reads act-refinement marks
  fail-open (`if os.path.exists(act_refinements_FINAL.json)`): if that file
  vanished, the fence would silently shrink to the atom-only set and some
  vocab-reachable rows would be stamped TERMINAL again.
* **EVIDENCE OF CURRENT ABSENCE.** The file is committed (Arc1-b mint, 2026-08-21),
  the fence re-ran clean against it at closure (45 re-stamps, reviewer-reproduced),
  and the identical fail-open in `satisfiability_census.load_refinements()` is
  its twin — no current instance of either absence.
* **PLAN IF IT APPEARS.** Make the file required with a fail-loud guard (the
  census M2 pin already exercises load_refinements; extend the pin or add one
  for the fence), or re-derive the marks from the seat outputs.
* **TRIGGER.** any state in which act_refinements_FINAL.json is absent while
  terminality verdicts are consumed (9b arithmetic, round-4 freeze).
* **STATUS.** NOT IMPLEMENTED — registered at lane closure per reviewer nit
  (CLEAR-WITH-NITS); latent only.
