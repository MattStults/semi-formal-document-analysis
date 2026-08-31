# CONTAINMENT_WIDENING_DESIGN — an admission procedure for overlay families (design, 2026-08-04, for review)

[REVISION 2026-08-05 per `S5_ADVERSARIAL_REVIEW.md` (verdict REVISE; 4
blocking, 8 major, 5 minor): the mechanical findings are resolved inline,
each marked at the change site with `[per S5_ADVERSARIAL_REVIEW <id>]`. Every
number restated below was recomputed from the tree at revision time, not
transcribed from the review. **The review's headline finding — SCI-B1, that
S5 produces zero flips and so cannot be falsified as designed — is NOT
resolved here.** It is a strategic question reserved for the project lead and
is recorded, unresolved, in the block at the head of §0.5. The parts the
review verified correct (the frozen order, the dead-53 handling, the min-idf
cap, §2.3's floor check, §5.2's pricing claims) are not re-opened.]

## 0. Scope, and what this is NOT

This designs the PROCEDURE by which containment families are admitted to
`containment.json` — the order, the review gate, the budget rule, the pricing
interactions, the expected-effect statement, and the stopping rule. It does
NOT nominate specific edges: under this contract no edge is even considered
until the procedure reaches it, and the procedure's order is frozen before
the first admission.

Evidence base (label-directed attention, disclosed): the census assigns **19
FN dossiers** the cause `fn_names_cannot_meet` — atom channel zero, empty
exact-name intersection, NONEMPTY stem-family adjacency. The clause and query
already carry same-family names; only the matcher cannot connect them. By
shared head, the 19 break down: **information 9** (avoid_extremist_content_5,
avoid_info_hazards_3, do_not_facilitate_illicit_behavior_2, protect_privacy
1/2/3/5, support_programmatic_use_13, do_not_lie_11), **request 3**,
**context 3**, and one each for content, topic, task, instruction (goal as a
secondary adjacency). Per the standing policy these counts locate the
opportunity; they never justify an edge.

Current state: budget `{max_edges: 4, max_families: 2}`, 2 edges, 1 family
(manipulation), **PRICING_VERSION 1.2** (`containment.PRICING_VERSION`), and
`cycles/CYCLE_LOG.jsonl` holds **6 closed cycles — 5 keep, 1 revert**
(`patient-pricing-2026-08-04`) [corrected per S5_ADVERSARIAL_REVIEW ENG-B4;
both recomputed from disk 2026-08-05: the log's six lines, and
`containment.py:125`. The earlier "PRICING_VERSION 1.1, three KEEP cycles
logged" was stale on both counts, and the pricing number is load-bearing —
S5's snapshot records 1.2, so the edges it turns on are priced by the
decoration-blind join, not by v1.1].

## 0.5 Hard dependency: the overlay-reactivation cycle S5 (F2)

> ### ⛔ OPEN STRATEGIC QUESTION — S5 PRODUCES ZERO FLIPS. NOT DECIDED HERE.
> **[recorded per S5_ADVERSARIAL_REVIEW SCI-B1 and review item 6; a
> project-lead decision, deliberately left unresolved by this revision.]**
>
> **Measured, re-verified from disk 2026-08-05:** building S5's snapshot
> (`annotations_ext_v1_merged.json` + `behavior_atoms_audit_v1.json`,
> `--overlay containment.json`, `--thresholds thresholds_frozen.json`) and
> diffing it against `join-integrity-v2-2026-08-04` yields **no flips on any
> DEV behaviour** — `avoiding-over-and-under-caution` 95 → 95,
> `harm-avoidance-to-third-parties` 73 → 73, `helpfulness` 146 → 146, all
> three cuts frozen and unmoved. All 8 clauses that gain subsumption credit
> were already inside the predicted set. The nearest non-predicted clause,
> m0357, moves 0.1831 → 0.1937 against a cut of 0.2365 — a 0.0428 gap it
> does not close.
>
> §0.5 as written says "keep/revert cites the flip adjudications only".
> **There are none to cite.** A cycle that closes KEEP on a clean validator
> and zero adjudications is a rubber stamp, and it is the gate every widening
> cycle in this document waits on. The review's three live options — run S5
> as a deliberate, disclosed no-op; fix the design so it can be falsified
> (the review's item 6: a flip-capability screen in §2, and the §2.2
> kind-inheritance statement applied to S5 itself, which would surface
> pre-registered that inheritance is currently **blocked**); or skip S5 — are
> **not chosen here**.
>
> **Pending decision.** See `S5_ADVERSARIAL_REVIEW.md` (SCI-B1, SCI-M3, and
> item 6 of SHORTEST PATH TO READY-FOR-OPEN) and `SCOPE_DECISIONS.md`
> **Decision 1**. Everything below §0.5 that describes S5 is written to be
> *accurate and openable* under whichever way Decision 1 is ruled; the
> pre-registration in §0.5.2 is explicitly **conditional** on that ruling.

> ### ⚠️ MANDATORY DISCLOSURE — S5 WAS MEASURED BEFORE OPEN
> **[per S5_ADVERSARIAL_REVIEW's opening disclosure and `CYCLE_DESIGN.md`
> § PRE-BUILT CYCLES.]** The adversarial review built S5's snapshot and
> diffed it before any cycle opened, and this revision re-verified the same
> numbers. S5's **temporal guarantee is therefore already spent**.
> `CYCLE_DESIGN.md` is explicit about what follows: *"this is already gone
> and no procedure restores it. Do not construct a ritual that appears to
> restore it."* What survives is the mechanical gate coverage (declared files
> changed, gate tests green, closure unchanged, review verdict present), and
> that is worth keeping. **This disclosure must ride into the cycle record —
> stated plainly in S5's `prediction.json` notes AND repeated in its decision
> justification.** Without it, an honest zero-flip pre-registration reads to a
> later reader as a blind prediction that came true.

[Amended per PORTFOLIO_REVIEW F2 — the finding this design silently sat
on.] The overlay lineage has a seam: containment's two edges are DORMANT in
the spine's baseline configuration, and no design owned turning them back
on. Widening dormant edges would grow a machine nobody is running.
Precisely, and corrected [per S5_ADVERSARIAL_REVIEW ENG-B4 — recomputed
across `snapshots/*.json` 2026-08-05]: the **frozen cuts** are genuinely
overlay-null (`thresholds_frozen.json` was derived from
`baseline-2026-08-04-auditv1`, whose recorded `inputs.overlay` is `null`),
while **4 of the 6 driver-era cycles** record `inputs.overlay:
overlay_empty.json` — an explicitly empty overlay, not a missing one. Both
routes leave the edges dormant, but they are different records and the
earlier blanket claim ("the entire keep lineage … measured overlay-OFF")
overstated it. The dependency stands either way: **no admission cycle opens
until S5 closes.** That dependency is DESCRIPTIVE PROSE, not a manifest key
[corrected per S5_ADVERSARIAL_REVIEW ENG-m1: `cycle.py` has no `depends_on`
field in `manifest_template` (`:227-244`) or `REQUIRED_MANIFEST_KEYS`
(`:247-250`), and nothing validates one — an extra key is tolerated noise
that no gate would ever check. The identical error was corrected in
`SECTION_PRIOR_DESIGN`]. The operator verifies the dependency by reading
`cycles/CYCLE_LOG.jsonl` for S5's closing line before OPEN, as a §7.0 step.

**S5's shape, defined here** (a short, standard cycle — its own cycle, not
a rider): turn the existing containment edges ON — **under PRICING_VERSION
1.2, not v1.1** [corrected per S5_ADVERSARIAL_REVIEW ENG-B4: the built
snapshot records `pricing_version: "1.2"`, verified] — under the audit_v1
configuration with the frozen cuts (`thresholds_frozen.json` asserted on
both snapshots); snapshot → diff against the baseline resolved from the
cycle log; the complete flip set dossiered and **adjudicated** like any
other cycle's; keep/revert cites the flip adjudications only (**but see the
zero-flip block above — as measured there are none**); census deferred to
checkpoint, which is also the driver's own default for `shape: code`
(`cycle.py:672-673`). Its expected-effect statement is §4's machinery, **in
the two-part form §4 now specifies**, run over the two existing manipulation
edges. Only after S5 closes KEEP does the overlay-ON configuration become
the baseline this design's admission cycles measure against.

**The configuration, named by sha** [per S5_ADVERSARIAL_REVIEW ENG-m4 — "the
audit_v1 configuration" named only the atoms artifact; both sides are
load-bearing. Shas read from `snapshots/join-integrity-v2-2026-08-04.json`'s
config identity, 2026-08-05]:

| role | artifact | sha256 |
|---|---|---|
| clause annotations | `annotations_ext_v1_merged.json` | `1ea7fe9d684e0954b58c4f0ff3bd21849733d10572e19eb534946aace3357e70` |
| query-side atoms | `behavior_atoms_audit_v1.json` | `540562415cdb95e15eb99f06e2d06fb2f5f2347daac42e3b7a998dcc8d3a7531` |
| overlay (ON) | `containment.json` | `fa994943bb82321efc27d0988be966e72424a502b4051c6125d7671167935f60` |
| frozen cuts | `thresholds_frozen.json` | `60d1273a4e0ac3a4de0eb2a44481b763531491c8c0884387529014dcb724251a` |

### 0.5.1 S5's manifest — what makes it expressible as a cycle at all

[Added per S5_ADVERSARIAL_REVIEW ENG-B1. The refusals below were re-verified
directly against `cycle.py` 2026-08-05, not taken from the review.] As
originally written S5 changes **no file**: it is a change to the manifest's
own `config.overlay` value, from `overlay_empty.json` to `containment.json`.
The driver has no shape for that, and would halt an operator at OPEN three
separate ways:

* `PHASES_BY_SHAPE` (`cycle.py:97-103`) offers only `code` and `checkpoint`.
  S5 is not a checkpoint (census deferred).
* For `shape: code`, OPEN refuses an empty `files_to_change` — *"a code fix
  cycle changes something"* — and refuses a missing
  `compatibility.version_key` / `compatibility.statement` under amendment F9.
  (Verified in `_open`'s validation block; both refusals append to
  `problems`, which raises `CycleError`.)
* `config.overlay` is added to the OPEN **closure pin**: `closure =
  gate_tests ∪ {annotations, atoms} ∪ {overlay, thresholds} ∪
  CLOSURE_DEFAULTS`, minus `files_to_change` (`cycle.py:661-668`). So
  `containment.json` must NOT change. And declaring it in `files_to_change`
  to satisfy the non-empty rule only moves the halt: the IMPLEMENT gate then
  refuses it as byte-identical to its OPEN sha — *"the fix has not been
  implemented"* (`_implement`, `cycle.py:828-834`).

**The manifest S5 opens with**, therefore:

* `shape: "code"`.
* `files_to_change: ["test_containment.py"]` — the change is to add the pin
  that `containment.json` loads cleanly under the **CURRENT** vocabulary
  (`containment.load_edges(path, vocabulary=<current clause vocabulary>)`,
  which is the only call path that runs `_check_family_support` —
  `containment.py:328-329`; `snapshot.py:184/190` and `dossier.py:354/361`
  all call `load_edges` **without** a vocabulary). This is a real file
  change, so the IMPLEMENT gate is genuinely exercised; it is a *stronger*
  pin than the existing `_b8_vocabulary()` one at `test_containment.py:777-793`,
  which pins the superseded corpus; and it closes ENG-M3 (the ≥2-children
  license is never enforced on the configuration S5 actually scores).
  Verified by hand that the current corpus passes, so this pin lands green:
  latent `manipulation` df **8**, and both children are present.
* `gate_tests: ["test_containment.py", "test_snapshot.py",
  "test_no_reference_leak.py"]` — the design previously declared none.
  (`test_containment.py` appears in both lists; per `cycle.py:668` the
  closure subtracts `files_to_change`, so it is pinned as a declared change
  and not double-pinned. This is the ordinary `CYCLE_DESIGN.md` § GATE PINS
  VS DECLARED CHANGES case, decided in advance rather than discovered as a
  mid-cycle re-closure.)
* `compatibility: {version_key: "overlay", statement: "the old behaviour
  remains reachable by pointing config.overlay at overlay_empty.json; no
  scoring code changes, so every pre-S5 snapshot reconstructs unchanged"}` —
  `overlay` is already the natural F9 version key, and it is already
  recorded in every snapshot's config identity.
* `baseline_snapshot_tag`: **resolved at OPEN from
  `cycles/CYCLE_LOG.jsonl`** — the last line with `"decision": "keep"` — and
  **never a statically named tag in this document** (`HANDOFF.md` ruling 2)
  [per S5_ADVERSARIAL_REVIEW ENG-M1]. At revision time that read resolves to
  `join-integrity-v2-2026-08-04`; that value is stated here as a
  *diagnostic*, not as the manifest's source of truth. Residual the operator
  must settle at OPEN and record: the last closed KEEP is P1's
  `join-integrity-v2`, which is not a *spine* snapshot. Mitigating and
  verified: `patient-backfill-2026-08-04` and `join-integrity-v2-2026-08-04`
  are score-identical, so the numbers do not move either way.

Ordering caveat [per S5_ADVERSARIAL_REVIEW ENG-M4]: `CYCLE_LOG.jsonl` has no
S4 line, and S4 changes the **section channel** — the channel carrying 16 of
S5's 24 score deltas (§4). **S5 as specified here assumes it runs BEFORE
S4.** If that order changes, the §0.5.2 expected effect must be re-derived
before it is frozen.

### 0.5.2 S5's pre-registration — CONDITIONAL on the Decision-1 ruling

[Added per S5_ADVERSARIAL_REVIEW SCI-B2: the design specified no prediction
targets at all, including `max_regressions`, which `prediction.json`
REQUIRES as a non-negative int (`cycle.py:794-796`) and which is checked at
ADJUDICATE (`_check_predictions_adjudicate`, `cycle.py:1046`). Without this
block an operator would have to invent the targets at the halt — the
transcript-only procedure `REPRODUCIBILITY.md` classes as a review finding.]

**This block is conditional.** It is the pre-registration for S5 *run as
specified above*. If Decision 1 rules that S5 is redesigned to be
falsifiable, or skipped, this block is void and must be rewritten or
deleted — it must not be lifted into a cycle whose shape has changed.

Flip-level targets (all zero, honestly):

* `expected_flip_count: {min: 0, max: 0}`
* `expected_directions: []` — the driver licenses an empty list **only**
  when `expected_flip_count.max == 0`, which is exactly this case
  (`cycle.py:777-786`, verified: *"the honest zero-flip prediction, where no
  direction can occur"*).
* `max_regressions: 0`

Mechanism-level targets — the part of S5 that *can* fail. **Every number
below was recomputed from the tree on 2026-08-05, not transcribed:**

* **8** subsumption records, on exactly
  `{m0216, m0217, m0218, m0220, m0221, m0222, m0322, m0355}`, all on
  `harm-avoidance-to-third-parties` (the other two DEV behaviours carry
  zero records).
* Each priced **1.6812**, at `kind_factor` **0.4** — the mismatch discount,
  on every record without exception.
* Latent parent `manipulation` at **df 8**, **idf 4.2030**.
* **24** clauses change score, of which **16** change through the **section
  channel only** (`m0219, m0321, m0323, m0354, m0356–m0367`) and 8 carry an
  atom-channel delta (`+0.1771`) alongside their section delta.

Note, recorded rather than resolved [per S5_ADVERSARIAL_REVIEW SCI-M1 and
item 6]: the uniform `kind_factor 0.4` is *why* every match is discounted —
`parent_kinds['manipulation']` computes to `frozenset()` on this corpus, so
kind inheritance is **blocked**. `_unanimous_child_kind`
(`containment.py:426-449`) requires every licensed child to be attested
under exactly one agreeing non-empty kind; on `annotations_ext_v1_merged.json`
`targeted_political_manipulation` is filed as a **situation** where
`psychological_manipulation` is an **act**, so the children disagree and the
latent parent inherits nothing. Whether that child is a situation or an act
is a genuine document-side question on which the overlay's pricing turns.
Making it a §2.2-style kind statement that S5 itself must answer is part of
review item 6 and belongs to Decision 1; it is **not** decided here.

**Prediction notes must carry the §0.5 pre-built disclosure verbatim**: the
flip count was known before the prediction was frozen.

## 1. The candidate universe and its pre-registered order

### 1.1 Enumeration (label-free, mechanical)

The enumerator is `head_induction_probe.py`'s convention hardened to
containment's own license: over `annotations_ext_v1_merged.json` (clause
side) ∪ the behaviour-atom artifacts (query side), a candidate family is a
last-token head `H` together with every name `n` such that the edge `n → H`
passes `containment._license_edge` (right-headed, no polarity, no principal,
no negation, parses clean), restricted to families with **≥ 2 licensed
children present in the clause vocabulary** (`_check_family_support`).

Count discrepancy — RESOLVED [amended per PORTFOLIO_REVIEW F3]: the
briefing figure of **53 fireable families is DEAD** — the review could not
reproduce it from any (artifact, license, roster) triple; it is dropped,
not "to be reconciled". The reproducible numbers: the license **as coded**
over literal last-token heads gives **38 families**; the head-induction
probe's **singularized** head convention gives **27** — and the gap between
them is not free: **singular parents cannot license plural children under
the license as coded** (a `restriction → restrictions`-shaped edge fails
`_license_edge`), so the singularized convention over-promises what the
overlay can actually connect. That plural/singular limitation is recorded
here as a limitation of the license, not papered over by picking the
flattering count. Resolution: **the enumerator ships as a COMMITTED script**
(named in files_to_change, sha-pinned in the freeze artifact) and **its
output is frozen** as the §1.3 order file; the count is whatever the
committed script yields on the pinned inputs (38 under the literal-head
convention, which is the license's own). **Nothing admits until the script
is committed and its output frozen.**

### 1.2 The order, and why it is what it is

**The F1 lesson, restated as a rule**: any ordering that consults panel
outcomes — "admit the family that moves MCC most" — is label fitting no
matter how each individual edge is licensed, because the SEQUENCE becomes
the fitted parameter. Therefore the order is a pure function of document-side
and query-side artifacts, computable by anyone from the pinned inputs, frozen
before cycle 1 of widening:

1. **Primary: fireability, descending** — the number of distinct
   (query_atom, clause) pairs the family would newly connect, computed
   mechanically per §4 (this is the expected-effect statement's own number).
   Justification: it is the size of the family's testable claim — the
   families adjudication can learn most from come first — and it is
   label-free: it reads query atoms and clause annotations, never a panel.
2. **Secondary: licensed children present in the clause vocabulary,
   descending** — a df-like document statistic; larger attested families give
   the latent parent a better-grounded union df.
3. **Tertiary: parent head, ascending alphabetical** — arbitrary, therefore
   unbiased, therefore last.

What the order is NOT: it is not a quality ranking. The enumeration's biggest
heads (request 11 clause-present children, content 6, information 4+) are
semantically the WEAKEST — "information" as a latent parent asserts that
`dual_use_information` and `privileged_information` attest one concept, which
is exactly the promiscuity the census's 155 `fp_promiscuous_atom` verdicts
warn about. Quality is the review gate's job (§2); the order only fixes the
SEQUENCE so that no one cherry-picks a flattering family, and a family the
gate rejects is recorded and skipped, not reordered around.

### 1.3 The freeze

`containment_admission_order.json` (new artifact): the enumerator inputs by
sha (annotations artifact, each behaviour-atom artifact, grammar.py,
containment.py LICENSE, **and the committed enumerator script itself**),
**plus the `pricing_version` and `join_version` the order was computed
under [amended per PORTFOLIO_REVIEW F7]** — fireability counts read
(query_atom, clause) connectivity, which both the pricing lineage
(1.2/2.0) and the join version (v1/v2) change, so an order file that does
not name them is not reproducible — the full ordered candidate list with
per-family
fireability and child rosters, and the census-provenance disclosure. Frozen
(own sha) before the first widening cycle. Re-enumeration is permitted ONLY
at declared checkpoints (vocabulary changed — e.g. after VOCAB_GAPS additions
— or a pricing version change), and produces a NEW versioned order file; the
old one is never edited.

## 2. Per-family review gate (before any admission)

For the family at the head of the order:

1. **Golden gloss review, blinded** (`briefs/golden_review.md` pattern): for
   EVERY licensed child, the seat answers "is <child> a genuine
   specialization of <parent> **in each clause where it appears**, on the
   gloss and the clause text?" — the same question cycle 1's flip
   adjudication asked, moved before admission. One invalid child removes that
   child's edges; if fewer than 2 clause-present children survive, the FAMILY
   is rejected (the one-child alias rule, applied at review time rather than
   load time).
2. **Kind-inheritance statement** (mechanical, pre-admission): compute
   `_unanimous_child_kind` over the surviving children. Record whether the
   latent parent inherits a kind or every subsumption match will pay the
   mismatch discount. A family that cannot inherit is still admissible — the
   discount is the designed conservatism — but the expectation is stated
   before the flips exist, so a "family did nothing" outcome is a prediction
   confirmed, not a surprise.
3. **Floor check** (mechanical): compute the latent parent's union df and
   idf. A parent whose idf floors to 0 (union df above the stopword cutoff)
   can never contribute credit; admitting it wastes budget on a no-op. Such a
   family is marked `floored` and skipped without consuming a cycle.
4. **Chain-reachability statement** (mechanical, honesty about limits):
   principal-chained and polarity-prefixed names can NEVER be containment
   children by license. **⚠️ The worked example below is STALE on its
   chain-based half and must be re-derived before it is relied on** [flagged
   per S5_ADVERSARIAL_REVIEW SCI-m1; same root cause as ENG-B3, and the
   correct contract is now stated in §5.3: under pricing 1.2 the clause side
   is dechained BEFORE matching, so a *chained clause atom* is reachable
   through the overlay and the `mustnot_/should_decline_` cases below are not
   excluded for the reason given. Polarity is NOT stripped, so the
   polarity-prefixed half of the argument still stands and the "~4 of 9"
   conclusion may survive on those grounds — but the reasoning as written
   does not. Re-deriving it is a redesign question, not a mechanical fix, and
   is deliberately left open here.] For the FN dossiers adjacent to this
   family, list
   which clause atoms are reachable and which are not. Worked example from
   the information family: `privileged_information` (m0364, m0467) and
   `provide_public_contact_information` (m0228) are licensable children;
   `mustnot_provide_private_information__model_user` (m0226, m0230),
   `should_decline_private_information__model_user` (m0227),
   `may_provide_general_drug_information` (m0211) are not. So even a fully
   admitted information family addresses at most ~4 of its 9 census cases;
   the rest belong to cycle-5 patient pricing or query-side selection, and
   the gate says so BEFORE admission so the checkpoint cannot mistake a
   designed non-effect for a failed one.

## 3. Budget escalation rules

The budget is the overlay's self-declared ceiling; raising it is the visible
act of growth. Contract:

1. **One family per cycle.** Each admission is its own config change:
   budget+edges edited together in `containment.json`, then snapshot → diff
   → dossier → adjudicate → decision.json, per the standing loop. No batch
   admissions. **The former grounds — "the cycle-1 experience (7 flips for a
   2-edge family)" — are STRUCK as refuted** [per S5_ADVERSARIAL_REVIEW
   SCI-M2; re-verified 2026-08-05: cycle 1's 7 flips were measured on the
   **b8** corpus, and the same 2 edges on the current corpus
   (`annotations_ext_v1_merged.json` + `behavior_atoms_audit_v1.json`, frozen
   cuts) produce **0** flips — see §0.5's zero-flip block]. The rule is kept,
   re-grounded on what still holds: a family's flip count is not knowable
   before the cycle runs (0 and 7 are both attested for the *same* two
   edges), the ~30-flip adjudication guideline is a hard budget
   (`CYCLE_DESIGN.md` amendment F4b), and one family per cycle is the only
   admission unit under which a keep/revert can be attributed to a
   *particular* family at all. A refuted number is not carried into the
   freeze.
2. **Exact-fit raises.** On admitting a family with k surviving edges:
   `max_families += 1`, `max_edges += k`. The budget is always EXACTLY the
   admitted content — never raised ahead of an admission decision, so a
   nonzero slack between budget and content is by construction a validation
   failure waiting to be noticed, and `_check_budget` keeps meaning "this
   file is the size it declared".
3. **Reverts shrink.** A reverted family removes its edges AND lowers the
   budget by the same amounts, in the same cycle's decision.
4. **A hard review ceiling.** When cumulative admissions would exceed
   **8 families / 32 edges**, widening halts for a joint review regardless of
   per-cycle outcomes — a ratchet check on the procedure itself, matching the
   review's "growth must read as growth" finding.

## 4. Expected-effect statement per admission (pre-registered, label-free)

Before the candidate family's snapshot is taken, compute and freeze
`cycles/<tag>/expected_effect.json`. The statement is **TWO-PART**, because
the scorer moves credit through two channels and an atom-channel-only
prediction can never cover the second [restructured per
S5_ADVERSARIAL_REVIEW ENG-B2 — the previous one-part form was incomplete *by
construction*, not by oversight]:

**Part A — the atom channel (the subsumption diff).** For every behaviour
with atoms, every (query_atom, clause_id, clause_atom, subsumer, priced
credit) record the new edges add — obtained by running `ContainmentIndex`
with and without the candidate edges on current inputs and diffing
`subsumption_matches`. This is mechanism-level and computable label-free
pre-admission (it is exactly the machinery `explain()` already exposes).

**Part B — the induced section-channel delta.** Every clause that gains atom
credit lifts **every co-sectional clause**, whether or not that clause
carries any subsumption record. The mechanism is `relevance.py:703-711`:
after the per-clause local score is formed, `section = w.section × mean(top-k
local scores in the clause's section)`, at the shipped defaults `w.section =
0.45` and `section_top_k = 3` (`relevance.py:491-492`) — so a gain that
enters any section's top-3 propagates to all of that section's members.
Part B therefore enumerates, for each section touched by Part A, that
section's full membership and each member's predicted section-channel delta.

S5's own numbers show the split is not marginal [re-verified 2026-08-05]:
**24** clauses change score, but only **8** carry a subsumption record; the
other **16** are pure section-channel spillover, moving `{section:
+0.0266/+0.0797}` and nothing else, while the 8 move `{section:
+0.0797/+0.0266, atom: +0.1771}`. On S5 this is inert (nothing flips). On a
widening cycle, where flips are the point, a Part-A-only statement would book
two-thirds of the legitimate second-order effects as "unexplained flips" and
block a KEEP.

Falsifiable use: the adjudicated flip set of the cycle must be EXPLAINED by
this statement — every newly-predicted clause must carry at least one
predicted **Part A** record, **or carry the tag `section_spillover` [added
per S5_ADVERSARIAL_REVIEW ENG-B2]: a clause with no subsumption record of its
own that crosses its cut on the Part B section delta induced by a
co-sectional clause's atom gain. This is the ORDINARY second-order effect of
any admission — permitted, and adjudicated on the document like any other
flip (the seat is asked whether the clause belongs, not whether the channel
was expected) — never booked as an unexplained flip. It is admissible only
when the clause appears in Part B's enumeration; a section-channel move on a
clause Part B did not name is still a bug investigation.** Or be a tagged
threshold-drift flip (adjudicated as a cut question per policy §3, the m0422
pattern), **or carry the tag
`section_gate_reactivation` [amended per PORTFOLIO_REVIEW F7]: once the
section evidence gate (SECTION_PRIOR_DESIGN A1, landed at S4) is in force,
an admission that gives a previously atom-zero clause its FIRST atom credit
also un-gates that clause's section credit — a legitimate second-order
effect of the admission, adjudicated as such, never booked as an
unexplained flip.** An unexplained flip is a bug
investigation that blocks the KEEP decision. The statement also feeds §1.2's
fireability number, so the order and the prediction can never disagree.

## 5. Pricing interactions (stated now, so later cycles inherit contracts)

1. **Kind inheritance (v1.1)**: latent parents inherit a kind only under
   child unanimity. Prediction per §2.2 is recorded pre-admission. Mixed-kind
   families (request: situations + acts; context likewise) will NOT inherit
   and pay the mismatch discount on every match — expected and priced, not a
   defect.
2. **Min-idf cap**: subsumption credit is
   `min(idf(subsumer), idf(clause_atom)) * kind_factor`; the never-outprice
   invariant is a review requirement for ANY widening and no admission may
   weaken it. Big-family union dfs push subsumer idf down; combined with the
   cap this means the weakest-headed families are also the cheapest per
   match — the pricing already leans against promiscuity, and §2.3 floors the
   worst outright.
3. **Patient-taint composition — REWRITTEN, and now CONDITIONAL** [per
   S5_ADVERSARIAL_REVIEW ENG-B3 (the old contract was false) and ENG-B4
   (its premise was counterfactual)].

   *What was here, and why it was false.* The old text read: *"licensed
   children are chain-free by construction, so every subsumption match is
   patient-FREE on the clause-atom side … a chained clause atom remains
   unreachable via the overlay."* That was true at **v1.1**. It is **false
   under pricing 1.2**: `ContainmentIndex.__init__` dechains **every clause
   atom before the base index is built** (`containment.py:350-378` — the
   decoration-blind join), so the match key, the df/idf and the lexical
   documents all read the dechained name, and a chained clause atom whose
   dechained form is a licensed child matches through the overlay normally.
   **Verified directly on one of S5's own 8 records, 2026-08-05:** clause
   **m0355** carries the clause atom `psychological_manipulation__developer_user`;
   `idx.chains['m0355'] == {'psychological_manipulation': [['developer',
   'user']]}` — i.e. it *is* principal-chained — and the overlay nonetheless
   produces the record `query_atom targeted_political_manipulation →
   clause_atom psychological_manipulation, subsumer manipulation, credit
   1.6812`. The chained atom is reached. The old sentence would have frozen a
   false premise into exactly the redesign the program's only revert was
   called on.

   *The real contract.* On the **query** side, licensed children remain
   chain-free by license (`_license_edge` refuses principals). On the
   **clause** side the license constrains nothing, because matching happens
   after dechaining: **a subsumption match may land on a clause atom that
   carries a principal chain, and the chain is invisible to the match.** The
   chain is not destroyed — it is preserved as pricing metadata in
   `idx.chains` and surfaced by `explain()` — so a patient-pricing layer
   *can* see it. That makes the composition requirement a real obligation
   rather than a vacuous one: **the patient factor must be applied to
   subsumption credit using the clause atom's OWN preserved chain, the same
   chain its exact match would have been priced under.** Applying the
   patient-free price to a subsumption match on a chained clause atom would
   let the overlay LAUNDER patient structure — cheaper credit through the
   parent than through the atom itself. That is the invariant a patient
   redesign must not break, and S5 is the cycle that makes the path live.

   *Conditionality.* The old text was premised on "once cycle 5 lands".
   **Cycle 5 (`patient-pricing-2026-08-04`) REVERTED** [re-verified from
   `cycles/CYCLE_LOG.jsonl` 2026-08-05: its line reads `"decision":
   "revert"`], so there is no landed patient pricing for this contract to
   compose with and the premise as written is counterfactual. This clause is
   therefore **conditional on S3b** (the patient/beneficiary redesign the
   revert sent back): if and when S3b lands, it re-prices overlay matches too
   and MUST bump PRICING_VERSION; the first admission cycle after it lands
   re-runs its expected-effect statement (both parts, §4) under the new
   pricing before adjudication, and `diff_snapshots` surfacing
   `pricing_version` becomes a prerequisite rather than a nice-to-have.
   Nothing in this document waits on S3b; only this contract does.

## 6. Stopping rule (checkpoints only, stated before the first cycle)

Widening STOPS when the first of these holds:

1. **Diminishing fireability**: two consecutive candidates in the frozen
   order have expected-effect statements connecting < 2 new (query, clause)
   pairs each — the order is fireability-sorted, so everything below them is
   smaller still. Label-free, checkable every cycle.
2. **Gate attrition**: three consecutive families rejected at the §2 gloss
   gate — the enumeration has run out of semantically real families even
   where names still share heads.
3. **FN-class exhaustion, measured at declared checkpoints ONLY**: at a
   census checkpoint on DEV cells, the `fn_names_cannot_meet` class has no
   remaining member whose adjacency head is an unadmitted, unrejected family.
   This is a labelled read; it happens at checkpoints, never per-cycle, and
   it can only STOP widening, never order or justify an admission.
4. **The §3.4 hard ceiling.**

Whichever fires, the terminal state is recorded in the order artifact
(admitted / rejected / floored / unreached per family) so the next
vocabulary change starts from a legible history, not a fresh argument.

## 7. Order of operations, per cycle

0. Verify the S5 dependency — a `"decision": "keep"` line for the
   overlay-reactivation cycle in `cycles/CYCLE_LOG.jsonl` — as an OPERATOR
   STEP read from the log (§0.5; amended per PORTFOLIO_REVIEW F2).
   **Not a manifest key** [corrected per S5_ADVERSARIAL_REVIEW ENG-m1:
   `depends_on` is in neither `cycle.py`'s `manifest_template` (`:227-244`)
   nor `REQUIRED_MANIFEST_KEYS` (`:247-250`), and nothing validates it — a
   dependency written there would be checked by no gate. See §0.5.]
1. Commit the enumerator script and freeze its output as
   `containment_admission_order` (§1.1/§1.3 as amended per F3 — the 53 is
   dead; the committed script's count on the pinned inputs governs).
2. Take the head-of-order family → §2 gate (gloss review, kind statement,
   floor check, reachability statement). 3. Freeze expected_effect.json.
4. Edit containment.json (edges + exact-fit budget). 5. Snapshot, diff,
   dossier, adjudicate the complete flip set; verify flips ⊆ expected-effect
   ∪ tagged cut-drift. 6. Decision.json; on revert, shrink budget. 7. Check
   stopping rules 1–2 and 4. 8. Census checkpoint reads rule 3 when declared.

Cut-stability remains a standing gate: the Otsu cut is under suspicion
(m0422, three cycles), so every widening cycle runs the cut-stability
diagnostic before adjudication, and drift flips are charged to the cut rule,
not the family.
