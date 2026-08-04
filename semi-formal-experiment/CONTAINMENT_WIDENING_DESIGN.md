# CONTAINMENT_WIDENING_DESIGN — an admission procedure for overlay families (design, 2026-08-04, for review)

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
(manipulation), PRICING_VERSION 1.1, three KEEP cycles logged.

## 0.5 Hard dependency: the overlay-reactivation cycle S5 (F2)

[Amended per PORTFOLIO_REVIEW F2 — the finding this design silently sat
on.] The overlay lineage has a seam: the entire keep lineage and the frozen
cuts were measured **overlay-OFF** — containment v1.1's two edges are
DORMANT in the spine's baseline configuration, and no design owned turning
them back on. Widening dormant edges would grow a machine nobody is
running. Therefore this design's manifest carries
`depends_on: overlay-reactivation cycle S5 (closed, keep)`, verified
against CYCLE_LOG.jsonl, and **no admission cycle opens until S5 closes**.

**S5's shape, defined here** (a short, standard cycle — its own cycle, not
a rider): turn the existing v1.1 edges ON under the audit_v1 configuration
with the frozen cuts (`thresholds_frozen.json` asserted on both snapshots);
snapshot → diff against the overlay-OFF baseline; the complete flip set
dossiered and **adjudicated** like any other cycle's; keep/revert cites the
flip adjudications only; census deferred to checkpoint. Its
expected-effect statement is exactly §4's machinery run over the two
existing manipulation edges. Only after S5 closes KEEP does the overlay-ON
configuration become the baseline this design's admission cycles measure
against.

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
   children by license. For the FN dossiers adjacent to this family, list
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
   admissions: the cycle-1 experience (7 flips for a 2-edge family) prices a
   multi-family batch straight past the ~30-flip adjudication guideline.
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
`cycles/<tag>/expected_effect.json`: for every behaviour with atoms, every
(query_atom, clause_id, clause_atom, subsumer, priced credit) record the new
edges add — obtained by running `ContainmentIndex` with and without the
candidate edges on current inputs and diffing `subsumption_matches`. This is
mechanism-level and computable label-free pre-admission (it is exactly the
machinery `explain()` already exposes).

Falsifiable use: the adjudicated flip set of the cycle must be EXPLAINED by
this statement — every newly-predicted clause must carry at least one
predicted record, or be a tagged threshold-drift flip (adjudicated as a cut
question per policy §3, the m0422 pattern), **or carry the tag
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
3. **Patient-taint composition (once cycle 5 lands)**: licensed children are
   chain-free by construction, so every subsumption match is patient-FREE on
   the clause-atom side. Contract for composition: the cycle-5 patient factor
   applies to subsumption credit exactly as to a patient-free exact match —
   subsumption edges never LAUNDER patient structure (a chained clause atom
   remains unreachable via the overlay; its patient pricing happens only on
   its own exact matches). Landing cycle 5 therefore re-prices overlay
   matches too and MUST bump PRICING_VERSION; the first admission cycle after
   cycle 5 lands re-runs its expected-effect statement under the new pricing
   before adjudication, and `diff_snapshots` surfacing `pricing_version` (the
   logged v1.2 follow-up) becomes a prerequisite rather than a nice-to-have.

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

0. Verify `depends_on: overlay-reactivation cycle S5 (closed, keep)`
   against CYCLE_LOG.jsonl (§0.5; amended per PORTFOLIO_REVIEW F2).
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
