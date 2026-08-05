# ADVERSARIAL REVIEW — IMPLIED_EFFECTS_DESIGN.md

Reviewer: clean-context adversarial subagent (no prior involvement; model set explicitly
by dispatcher). Date: 2026-08-04. Artifact reviewed:
`IMPLIED_EFFECTS_DESIGN.md` (DRAFT, "awaiting adversarial review").

Read before judging, in this order: the artifact; `grammar.py`, `patient.py`,
`containment.py` (chain seam), `annotations_ext_v1_merged.json` (shape via
`cycles/patient-pricing-2026-08-04/flip_dossiers/` m0239 and m0276 dossiers),
`inventory.py` (join_version), `validate_query.py`, `briefs/backfill_author.md`,
`HANDOFF.md` (top section), `ITERATION_LOOP.md` (policy §), `REPRODUCIBILITY.md`,
`S3B_REDESIGN.md` (§3, §4A, §4B ruling (b), §5.3, §7), and
`snapshots/patient-backfill-2026-08-04.json` (config identity).

---

## OVERALL VERDICT: **REVISE**

Not do-not-build: the layer is needed (S3B ruling (b) creates it), the core principles
(§1.1–1.4, §2.2's rejection of the chain shortcut) are correct, and every blocking
finding below is fixable by specification, not by abandoning the concept. Not proceed:
the design has **four blocking findings** — two on each dimension — any one of which
would let the layer corrupt the measurement or fail to build to a single reading. The
architecture (two keyed layers, opt-in seam, provenance) is right; the rulings that make
it safe are missing.

Finding counts:

| dimension | blocking | major | minor |
|---|---|---|---|
| Engineering excellence | 2 | 3 | 2 |
| Science | 2 | 4 | 1 |

What is genuinely sound (stated so the revision does not churn it): §2.2's rejection of
encoding the implied beneficiary as an extra chain is exactly right — verified against
`grammar.py` (`describe`: "WHO: X acts, upon Y") and `briefs/backfill_author.md` rules 3
and 5 (never infer; no capacity-packing). The claims about the grammar are otherwise
accurate (agent-first chains, `PRINCIPALS` vocabulary, span-backed entries). Reusing the
opt-in/version-seam pattern is the right instinct, and §9's scope discipline
(beneficiary-only, no automation, m0239 as proposal not restoration) is proper v1
restraint. The problem is not scope creep; it is the missing rulings below.

---

# Engineering excellence

## ENG-B1 (BLOCKING) — §2.4 composition is underspecified against the actual pricing mechanism; two plausible implementations diverge, and one produces a state the pricing documents as impossible.

The design defines `relevant_patients(atom) = translation_patients(atom) ∪
implied_patients(atom)` and stops there. The mechanism it composes with
(`patient.py`, PRICING_VERSION "2.0") does not have one patient reading — it has
three interacting structures: (1) the per-atom patient set `pa` in `_priced_record`
(factor 1.0 if `pa ∩ P`, else `d`), (2) the clause-taint quantifier
(`_clause_tainted` / `_chain_patients`: ">= 1 patient-bearing chain and none
consistent"), and (3) the taint cap (argmax survivor keeps `d`, all other credited
matches zeroed). The design never says whether implied patients enter (1) only,
(2) only, or both.

The readings diverge concretely, and the dossier evidence shows it is not academic:

* m0239 (`flip_dossiers/…m0239__no_longer_predicted.json`, `explain_b.patient_pricing`)
  has TWO patient-bearing atoms: `should_deescalate_extremist_involvement` (the match,
  the design's key target, §2.3 example) and `should_contextualize_harmful_ideology`
  (not matched, gets no implied entry). Under "implied enters both (1) and (2)", the
  implied `third_party` on the de-escalation atom defeats clause taint and the match is
  restored at factor 1.0 — the intended outcome. Under "implied enters (1) only",
  `clause_tainted` stays true (translation-only quantifier) while the record reads
  `why: consistent, factor 1.0` — the exact collision `patient.py::_priced_record`
  declares impossible ("On a tainted clause every patient-bearing chain is mismatched
  by definition, so `consistent` and `clause_taint` can never collide"). An
  implementer must pick; the design gives no basis to.
* The collision is not inert. With `tainted=True` and >1 credited record, the taint-cap
  code zeroes every non-argmax record regardless of its factor — an implied-consistent
  match can be zeroed by a translation-only taint. That is a silent scoring leak no
  explain field would flag, because the zeroed record's `why` would read
  `taint_capped` with no mention of the implied patient that argued against it.
* The same under-specification is worse against the regime the layer will actually
  meet. S3B ruling (b) (`S3B_REDESIGN.md` §4B) demotes m0239 to this layer precisely
  because S3b's strict attribution cannot license it; S3b is the next pricing change
  and re-prices on **attributed `harm_bearers`** via a four-branch precedence ladder
  (§5.3: unresolved → 1.0 and excluded from taint; generic → 1.0; consistent → 1.0;
  mismatched → d), with taint re-expressed over resolved+specific harm-bearing atoms.
  §2.4 is written against the REVERTED S3 chain-reading only and never names S3b.
  Under S3b, an implied patient attached to an atom whose attribution is `unclear`
  either stays in branch 1 (1.0, taint-excluded — the implied patient is inert) or
  promotes the atom into branches 3/4 (changing both factor and the taint quantifier).
  The union formula does not say which. A layer defined on top of a pricing regime
  that will not exist when it ships is not buildable.

Also note the prose misdescribes the mechanism: "A query patient that matches an
implied patient is **credited** exactly as a text-grounded match would be" — the
patient layer adds no credit; it removes or alters a discount (m0239's atom already
matches exactly at base idf 5.695; the layer's effect is restoring the factor from
0.1 to 1.0). An implementer reading "credited" may look for an additive path that
does not exist. And the design never states the dual: implied entries can also
SUPPRESS — an implied patient added to a patient-free atom makes it mismatched
(1.0 → d) for every query whose declared patients are disjoint, and can defeat or
create taint. The composition's score-movement envelope (patient.py states its own:
I2 monotone-downward on raw scores; factors in `{0.0} ∪ [d, 1.0]`) is nowhere
pre-registered for this layer.

**Required before build:** one named ruling — where implied patients enter (per-atom
factor, taint quantifier, or both), stated twice: once against the current
`patient.py` structures and once against S3B §5.3's precedence ladder (or an explicit
sequencing contract that the implied layer is only defined after S3b lands); plus the
score-movement envelope the layer may produce, with the taint-cap interaction worked
for the consistent-record-on-tainted-clause case.

## ENG-B2 (BLOCKING) — the two-layer key space is unbound: key form unpinned, no translation-identity binding in the schema, stale-key failure mode unspecified.

The entire architecture is "keyed, not merged" (§2.1), but the key contract is one
sentence: "the validator requires the key to resolve against the translation."

* **Key form is unpinned.** The §2.3 example keys on the DECHAINED spelling
  (`should_deescalate_extremist_involvement`), but the annotation artifact carries
  CHAINED names (`should_deescalate_extremist_involvement__model_user` — the dossier's
  `clause.atoms` shows chained `name`s), and `grammar.parse_name` makes those different
  atoms. The pricing seam (containment 1.2) keys `self.chains` by dechained name and
  prices dechained names (`patient.py`: "All explain records name the DECHAINED clause
  atom"). Chained and dechained keys have different staleness behavior under the exact
  migrations this repo runs: the chain-repair cycle's five `atom_refactor` rechain
  migrations moved chains and left stems fixed — dechained keys survive them, chained
  keys break. The design must pin the form and the resolution function
  (`grammar.stem_of`), not leave it to an implementer's "obvious" choice.
* **No translation-identity binding in the schema.** The entry schema (§2.3) has no
  field naming WHICH translation (version + sha256) the entry was authored and approved
  against. The project's own pattern for binding judgement records to their exact input
  exists and is unambiguous: `briefs/backfill_author.md`'s `worksheet_sha256` ("binds
  your records to exactly the worksheet you judged"). Without the analog, "the key
  resolves" is evaluated against whatever translation happens to be on disk — a moving
  target, since annotation is versioned and re-annotation is foreseeable
  (`annotations_ext_v1_merged.json` is `v1`).
* **Stale-key semantics unspecified.** When a key stops resolving (re-annotation, atom
  rename), does the loader hard-fail or silently drop the entry? The project's stated
  bias is hard-fail ("rewriting the join key on a name we could not read is the one
  failure that would be invisible downstream" — `grammar.py::stem_of`; "a convention
  that silently half-parses is worse than none" — `parse_name`). The design says
  nothing; a loader that skips unresolvable entries deletes approved judgement calls
  with zero signal — the canonical silent-failure mode.
* Related: the entry carries no verbatim quote of the clause text the judgement was
  made against (contrast S2's validator-checked `license_quote`). If the translation is
  ever re-glossed, the rationale can silently stop matching what the approver read.

**Required before build:** key form pinned (recommendation: dechained stem via
`stem_of`, consistent with the 1.2 seam); artifact-header field binding the exact
translation sha256; load-time hard-fail on unresolvable keys, never skip; a migration
story in the `atom_refactor` pattern for when a keyed atom legitimately changes; and a
`clause_quote` field (verbatim substring) in the entry schema.

## ENG-M1 (MAJOR) — §2.3 schema is incomplete and ambiguous on several fields and states.

* `polarity` has no mechanical effect. §2.4 composition ignores it entirely; the
  validator rules for which `effect_type × polarity` combinations are legal are absent.
  `beneficiary` + `harmful` (an act whose harm falls on an unnamed party) has no
  definable pricing semantics — the pricing has no negative channel — so either v1
  restricts to `protective` and the validator refuses the rest, or the composition for
  `harmful` must be defined. As written the schema admits entries with no semantics.
* Lifecycle/revocation semantics unresolved. §4.4 says "Revocation drops a single
  entry" — does the entry REMAIN in the artifact with `status: revoked` or is it
  removed? Explain trails cite `imp-<id>` "which resolves to the full provenance"
  (§2.4); if revoked entries are removed from the next artifact version, only the
  versioned-filename discipline (`annotations_implied_vN.json`) plus sha-pinning of
  snapshots (see ENG-M3) keeps old trails resolvable — that chain is never stated.
  `superseded` has no field linking to the superseding entry. Whether `rejected` /
  `proposed` / `under_review` entries may appear in the shipped artifact at all
  (affecting loader filtering on `status == active`) is unspecified.
* Duplicate semantics: two `active` entries on the same key — union? conflict? refused?
  Unspecified.
* Closed-schema rule unstated: I-imp5 is only enforceable if the validator refuses
  unknown fields (e.g., a behaviour slug sneaking into an entry); the design never says
  the schema is closed.
* Internal inconsistency: §2.1 says effects attach "to an existing atom **(or
  clause)**", while §8-E1 says "v1 keys effects to atoms" and the schema makes
  `atom_name` look required. Pick one for v1.
* `id` stability rules (unique, never reused, format pinned) are absent.

## ENG-M2 (MAJOR) — the opt-in seam and I-imp1 test are asserted, not specified; the "present but inert" cases are the hazard and are unaddressed.

I-imp1 is stated as "absent or OFF ⇒ bit-for-bit identical", mirroring `patient.py`
I1 — but `patient.py` earns that invariant by a named discipline the design does not
adopt: `query_patients` explicit and default-None, "nothing here — or anywhere —
silently reads a `patients` field"; early-return before any pricing path when the
active set is empty. The design specifies no constructor surface for the implied
artifact, no OFF flag semantics, and — the actual risk — says nothing about the
present-but-inert cases: artifact exists but has zero `active` entries; artifact loaded
but flag OFF. A loader that parses the file, builds an index of entries, or touches
`_chain_patients` while "OFF" is exactly how bit-identity dies by a float somewhere.

The test IS specifiable, and the design should carry this sketch: build the index on
the frozen `patient-backfill-2026-08-04` baseline with the declared `query_patients`;
run all three DEV behaviours; capture `channel_scores` + full `explain` bytes for:
(a) implied artifact absent; (b) artifact present, no `active` entries; (c) artifact
present with `active` entries but layer flag OFF; (d) flag ON with a behaviour that
declares no patients (must equal (a) — the patient layer's own I1 surface,
"absent is absent"). Assert byte-equality of (b), (c), (d) to (a), plus the
two-process `PYTHONHASHSEED` variant `REPRODUCIBILITY.md` mandates for deterministic
artifacts. Until the seam is specified to this level, I-imp1 is an aspiration.

The explain contract when ON is equally unspecified: which records/fields change, how
an implied patient that DEFEATS taint (a discount removed, not a match made) is cited
by `imp-<id>`, and confirmation that explain stays absent-is-absent when no patients
are declared (`patient.py::explain` returns the bare containment payload in that case —
the implied layer must preserve that).

## ENG-M3 (MAJOR) — the version seam is half-wired: snapshot identity + sha-pin missing; the §7 "F2" citation misreads the existing pattern.

* §7 says runs record "whether the layer was ON and which artifact version". Version
  string is not enough for the claims §7 makes ("byte-frozen at the G-freeze"). The
  project's frozen-input discipline is sha-pinning: `worksheet_sha256`
  (`briefs/backfill_author.md`), the sha-pinned derivation of
  `PATIENT_MISMATCH_DISCOUNT` (`patient.py`: "a silent re-licensing is a loud test
  event"), `thresholds_frozen.json` v1. The implied artifact must be sha-pinned in
  snapshot config identity, not just version-named; otherwise two artifacts can claim
  "v1" and the byte-freeze claim is unverifiable.
* The pattern the design must mirror is `pricing_version`, not `join_version`:
  `snapshots/patient-backfill-2026-08-04.json` records `"pricing_version": "1.2"` in
  snapshot identity because pricing can flip clauses; `inventory.py` F12 explicitly
  routes `join_version` to CENSUS identity instead, on the stated ground that "the join
  is downstream of the scorer and cannot flip a clause snapshot". The implied layer
  changes scores and flips clauses, so `implied_version` (+ artifact sha, + ON/OFF)
  belongs in SNAPSHOT config identity and in `dossier.py` reconstruction dispatch
  (HANDOFF ruling 4's F9 version-key requirement — without it, snapshots taken with the
  layer ON become un-reconstructable). §7's "(F2)" citation points the wrong way.

## ENG-m1 (MINOR) — module-registration obligations unstated.

The layer needs at least one new query-side module (loader/composition). The standing
rule (`AGENTS.md`; `test_no_reference_leak.py`): new query-side module →
`QUERY_MODULES` registration; any panel-reading module → `FORBIDDEN`; new test →
`conftest._OPTIONAL`. The design should state these obligations for its modules rather
than discover them at review time.

## ENG-m2 (MINOR) — determinism hygiene unmentioned.

Canonical ordering of implied patients in explain output (patient.py sorts its lists;
the implied additions must too), and the cross-process determinism test
(`REPRODUCIBILITY.md`: "Determinism is a cross-PROCESS property") for any new artifact
builder/validator. Cheap to add now, expensive to retrofit.

---

# Science

## SCI-B1 (BLOCKING) — panel-blindness fences the APPROVAL step only; proposal/queue formation is unfenced, and that is where panel-fitting actually lives. Concrete attack included. I-imp4 as written cannot protect the layer's central risk surface — and would refuse the design's own flagship entry.

**The attack (queue-selection laundering).** The adversary need never touch an
approval. Step 1: run the tool, read the panel-visible artifacts (flip dossiers,
census, `compare_to_panel` outputs). Step 2: propose implied effects ONLY for clauses
where the tool under-predicts relative to the panel; never propose the equally
plausible implied effects on clauses where the tool already agrees. Step 3: author
each rationale in pure document language — no panel token appears anywhere. Step 4:
the approver, blind per I-imp4, approves each entry on clause text + implication.
Every invariant holds. The resulting approved set is 100% concentrated on
panel-disagreement clauses; switching the layer ON moves exactly the clauses the panel
wants moved; MCC rises; it looks like accuracy; it is panel-fitting laundered through
blind approval of a panel-selected queue. Nothing in §1.5, §3 I-imp4, or §4 detects
this, because all of them govern approval inputs only. The proposal set is a channel
with no fence.

**The design is already downstream of this attack on its first entry.** §0 names m0239
as the driver precisely because S3's flip and adjudication surfaced it; §2.3's example
`rationale` is a paraphrase of the adjudicator's words
(`S3B_REDESIGN.md` §4B quotes leg 1: "Radicalization leads to violence against third
parties…"). The proposal provenance is flip-derived by construction. This is legal
under `ITERATION_LOOP.md` policy 1 — "Candidates from anywhere, provenance recorded…
Labels are NOT trusted" — IF the judgement is re-derived against the document and the
provenance class is recorded. But I-imp4's wording ("Approval inputs exclude … flip
outcomes") applied honestly would refuse its own flagship: whoever approves m0239
using this design document as context is reading flip outcomes. The design must
distinguish, by name: (a) blind text-derived proposal (the safe default), (b)
flip-surfaced proposal (legal, but must carry that provenance class on the entry and
an explicit disclosure that the approval itself was re-derived from clause text), and
it must fence the RATIONALE — a rationale authored by someone who has seen the flip
verdict carries the flip outcome into the approval input through the back door.

**Fix direction (required before build):** make §5's count-first enumeration
panel-blind and make IT the proposal source (enumerate what the text implies before
consulting any outcome; flips may then order the work — attention, never truth);
record `proposal_source` class per entry; extend to this layer the residual-fence list
S3B's B1 fix already enumerated (`S3B_REDESIGN.md` §5.1: the approver must not see the
census/`audit_dossiers`, the S3 cycle record, `S3B_REDESIGN.md`, this design document,
or `HANDOFF.md` — all of which name m0239's outcome); and state that the standalone
brief, not the token scan, is the primary fence (see SCI-M1).

## SCI-B2 (BLOCKING) — no pre-registered negative controls: every approved entry carries taint-defeating power, which is exactly the power that would re-surface m0276; and §4.2's signature-batch path is provably unable to separate m0239 from m0276.

The representation captures m0239's implied beneficiary — verified: an entry keyed
`(m0239, should_deescalate_extremist_involvement)` with `patients: ["third_party"]`,
composed per §2.4, restores the match from factor 0.1 to 1.0 (dossier `explain_b`:
base_credit 5.695, raw 0.2646 → 0.8856-class, score back above cut 0.2365). The
question the review brief demands is whether it does so WITHOUT breaking m0276-class
suppression. The design provides no assurance, and the mechanism says why:

* m0276's suppression (dossier `explain_b`) rests ENTIRELY on clause taint: the only
  matched atom is the patient-free situation `imminent_bodily_harm`; its three
  patient-bearing siblings (`mustnot_enable_self_harm`, `should_provide_supportive_response`,
  `must_advise_immediate_help`, all `__model_user`) are uniformly mismatched against
  `third_party`, so the match is discounted to 0.1. ONE implied entry adding
  `third_party` to ANY of m0276's chained atoms defeats the taint ("ONE consistent
  chain anywhere on the clause defeats the taint" — `patient.py`), re-surfaces m0276
  for third-party queries, and resurrects the canonical census false positive. The
  composition hands this power to every active entry; the only defense in the design is
  "a human would never approve that."
* §4.2 makes "a human would never approve that" into "a sample was glanced at." Worse:
  the design's exemplary signature — "model-protective act whose harm averts onto
  unspecified others" — is a predicate over the translation, and
  `S3B_REDESIGN.md` §3/§4A has ALREADY proven that no such predicate separates the
  cases: m0275 (must surface) and m0276 (must stay suppressed) are "structurally
  identical … a matched patient-free situation plus a sibling user-directed model-act.
  … No value of `d`, and no rule over chains as currently recorded, can separate them.
  The separator is the harm-bearer in the gloss." A signature batch over the
  translation will sweep m0276-shaped clauses into the approved class unless the
  signature reads glosses and judges harm-bearers — at which point it IS S3b's
  attribution mechanism (see SCI-M2), reborn with weaker governance.
* The discipline the design must mirror exists next door and is absent here: S3B §7.2
  pre-registers "Keep the canonical removals. m0276 and m0290 remain
  `no_longer_predicted` … If either re-surfaces, REVERT regardless of all else", and
  §7.1 requires a per-clause mechanical restoration SIGNATURE (non-empty
  `harm_bearers ∩ P`, factor 1.0, `why: consistent`) checked by an independent seat —
  "'still predicted' is NOT enough". The implied design pre-registers neither: no
  must-stay-suppressed control set, no mechanical signature that m0239 was restored BY
  the implied entry (and not merely predicted for some other reason), no REVERT rule.

**Required before build:** a pre-registered control set (at minimum m0276, m0290 under
every behaviour that declares patients) asserted suppressed with the layer ON, pinned
by test and by the activation cycle's prediction; a mechanical restoration signature
for m0239 (explain trail cites the `imp-<id>`, factor 1.0, `why: consistent`); and a
ruling that no signature batch may be approved without stratified NEGATIVE exemplars
(the must-suppress clauses that match the signature's syntactic shape) and a measured
false-positive count on them.

## SCI-M1 (MAJOR) — I-imp4's enforcement claim is overstated, and the judgement seat the layer invents has no brief and no document-side validator — the sandwich rule is not met.

§3 claims I-imp4 is "enforced the same way the attribution fence is
(`test_no_reference_leak.py` FORBIDDEN scan + standalone brief)". Verified against the
referents, this elides two different fences:

* The FORBIDDEN scan binds MODULE SOURCE (`test_no_reference_leak.py` scans
  `QUERY_MODULES`' code for panel-artifact references). It can and should guard the
  implied LOADER (the code that reads `annotations_implied_vN.json` at query time must
  not read panel files). It cannot inspect what a human approver or approval seat saw.
  Saying the approval blindness is "enforced" by it is false as written.
* The attribution fence's real strength is that S2's output is mechanically checkable
  against the document: every chain carries a verbatim `license_quote`, "checked
  mechanically; a chain that cannot quote its license does not land"
  (`briefs/backfill_author.md`). Implied effects have NO such check by construction —
  rule 3 of the same brief is precisely why m0239 cannot have a license quote. So the
  one judgement step in the project that is INTRINSICALLY uncheckable against the text
  gets the WEAKEST stated validation. Honesty requires: the fence is procedural
  (blind dispatch, recorded seat inputs, standalone brief), provenance is attestation,
  and the remedy for a bad entry is revocation (§4.4) — which is exactly why SCI-B2's
  controls and E-M1's revocation semantics are load-bearing.
* `REPRODUCIBILITY.md`'s sandwich rule ("a fix or feature is in-principle done only
  when its step conforms"; "Reviews … should flag transcript-only procedure as a
  finding, same severity as a missing test"): every judgement seat in this repo has a
  written brief in `briefs/` (backfill_author, flip_adjudicator, golden_author, …).
  The implied layer defines a new seat — the approver — and names no brief, no input
  envelope record (which files/texts the approver was shown; S2 binds this via
  `worksheet_sha256`), and no validator semantics beyond key resolution. That is a
  transcript-only procedure by the project's own definition.

## SCI-M2 (MAJOR) — signature-batch approval (§4.2) is a mass-approval failure mode as specified, and its boundary against S3b's attribution backfill is undefined.

* As specified, class approval transports human judgement from a "stratified sample of
  exemplars" to an UNBOUNDED set of unreviewed matching entries, with no precision
  requirement, no mandated negative exemplars (see SCI-B2), no count of
  sampled-and-REJECTED matches (only `reviewed_examples` "that grounded it" — the audit
  cannot distinguish a signature validated at 90% from one validated at 50%), and no
  specified review process for the signature artifact itself (who reviews it, under
  what blindness?). "The signature itself is a reviewed, versioned artifact" is one
  sentence for the most dangerous mechanism in the design.
* "This rule is made to be broken when it improves data quality" inverts the project's
  discipline. In this repo, rules bend by RECORDED RULING with grounds and a rejected
  alternative named (`AGENTS.md`: "Rulings go in the repo, not the transcript"). A
  per-batch discretion clause is a standing license for case-by-case exceptions without
  rulings. Rewrite: manual is the default; signature-batch requires a named ruling per
  use.
* Boundary against S3b D1(a): a signature that separates m0239-class from m0276-class
  must read glosses and judge harm-bearers (S3B §3's wall). That judgement, with
  per-row license quotes and golden review, IS S3b's annotation-side attribution
  backfill. If the implied layer's signature batch does the same judgement with
  class-level approval instead of per-row validator-checked quotes and golden review,
  it is S3b's mechanism under weaker governance — an arbitrage path where the
  convenience of batch approval drains work from the disciplined route. The design must
  draw this border explicitly (recommendation: any effect whose discriminator is a
  harm-bearer judgement readable from text+gloss belongs to strict attribution, not to
  this layer; this layer is for what attribution cannot reach — m0239's shape — and
  those are, by S3B's own finding, exactly the cases with NO mechanical signature).
  Note the irony this creates for §4.2: for the very effect type v1 ships, the
  conditions that make an entry implied (not document-grounded) are plausibly the same
  conditions that defeat any translation-only signature. §4.2 may be unusable in v1;
  the design should say so if the count-first bears it out.

## SCI-M3 (MAJOR) — §7 omits the inner-loop obligations of turning the layer ON: it is a score-changing change and must run as a cycle.

§7 covers config identity, DEV stamping, and frozen evaluations — and says nothing
about the machinery that governs every other score-changing change in this project:
switching the implied layer ON produces flips; `ITERATION_LOOP.md` policy 2 requires
"Every delta, adjudicated … on its COMPLETE flip set — both directions, no sampling by
default — against the DOCUMENT, under the written brief", with keep/revert citing
document-side reasons only, under a pre-registered prediction with a
`max_regressions` bound (S3 precedent: 19/19 measured, bound breached, REVERT —
`HANDOFF.md`). The implied layer's activation cycle must pre-register: expected flips
(count-first gives the number), the control planks of SCI-B2, and the adjudication of
every flip the layer causes — including flips on behaviours nobody proposed entries
for (the blast radius of a clause-scoped entry is all behaviours that declare
patients; one entry on m0239 touches every patient-declaring query, since
`{user, third_party}` now intersects more declared sets). §7's silence invites an
activation that bypasses the loop. Also note: flip adjudication's standard
("would a careful auditor of this behaviour need this clause" —
`briefs/flip_adjudicator.md`) itself permits implied reasoning (the m0239 adjudicator
inferred third-party victims), so layer-ON flips adjudicate coherently — but only if
they go to adjudication at all.

## SCI-M4 (MAJOR) — "count-first" (§5) is a gesture, not a gate; and as worded it can touch the sealed TEST.

Compare what §5 claims to mirror with what it contains. S3B §7.5's expected-recovery
estimate is: pre-registered BEFORE OPEN, mechanical, blind to flip outcomes, and its
result gates the cycle ("grounds to RE-SCOPE before spending an attribution cycle, not
a fact to discover at MEASURE … the figure is pre-registered here and the MEASURE
result is checked against it"). §5 has none of those properties: no pre-registered
thresholds ("small" vs "many" is undefined), no halt rule, no artifact spec for the
enumeration itself (who enumerates, blind to what, output schema — the sandwich rule
applies to it too), and no check-against-prediction structure. A sizing step with no
consequences is a gesture. Additionally: §5 says "how many implied effects the target
TEXTS need" (plural). The constitution is sealed TEST (`ITERATION_LOOP.md` §5: "never
consulted during iteration"). Enumerating the constitution's implied-effect needs
during iteration is consulting it; scope count-first to the DEV text (Model Spec) and
defer the constitution to the frozen-pipeline phase, or say so explicitly.

## SCI-m1 (MINOR) — the approval standard and the adjudication standard are not tied together.

The layer approves "this clause implies X" by an unspecified human standard, while the
loop adjudicates flips by "would a careful auditor of this behaviour need this clause"
(`briefs/flip_adjudicator.md`). If those standards drift, the layer and the loop
disagree about what counts as a legitimate implication — entries get approved that
adjudication would reject, or vice versa, and the disagreement is invisible until it
produces a flip. The approver brief (SCI-M1) should state its standard in the
adjudicator's words or explicitly justify a different one.

Also on the review brief's question whether "deterministic because it reads judgement"
is true: narrowly, yes — given a sha-pinned artifact (ENG-M3), same input → same
output, and an explain trail citing `imp-<id>` is reproducible. The claim should not
be stretched further: determinism of OUTPUT does not certify the JUDGEMENT; that is
what the approval fence, controls, and revocation are for, and the design's rhetoric
(§1.3) occasionally leans on determinism as if it were correctness.

---

## RECOMMENDATION

**Revise.** The concept is right and needed; the draft is not buildable or safe as
written. In priority order:

1. **Rule the composition** (ENG-B1): where implied patients enter the pricing
   (per-atom factor, taint quantifier, or both), against both `patient.py` and S3B
   §5.3; state the score-movement envelope; work the taint-cap interaction.
2. **Bind the key space** (ENG-B2): dechained-stem keys pinned by ruling, translation
   sha256 in the artifact header, hard-fail on unresolvable keys, `atom_refactor`-style
   migration story, verbatim clause quote per entry.
3. **Fence the proposals, not just the approvals** (SCI-B1): panel-blind count-first
   enumeration as the proposal source; `proposal_source` provenance class; residual
   input exclusions (census, S3/S3B records, this design, HANDOFF); blind rationale
   authorship; disclosed exception handling for flip-surfaced proposals (m0239
   included).
4. **Pre-register the controls** (SCI-B2): must-stay-suppressed set (m0276, m0290)
   pinned under layer ON; mechanical restoration signature for m0239; REVERT rule;
   mandated negative exemplars and measured false-positive counts for any signature
   batch.
5. **Complete the schema and lifecycle** (ENG-M1): polarity semantics or v1
   restriction; revocation retention semantics; `superseded` links; duplicate-key
   rules; closed schema.
6. **Specify the seam and its test** (ENG-M2): constructor surface, present-but-inert
   cases, the I-imp1 test sketch above, explain contract when ON.
7. **Wire the version seam properly** (ENG-M3): snapshot config identity (the
   `pricing_version` pattern, not `join_version`), artifact sha-pinning, dossier
   reconstruction dispatch.
8. **Write the approver brief** (SCI-M1) into `briefs/`, with the input-envelope
   record; drop the "enforced by FORBIDDEN scan" overclaim.
9. **Rewrite §4.2's discretion clause** as a ruling requirement and draw the S3b
   attribution boundary (SCI-M2); accept that signature batches may be unusable for
   the beneficiary type in v1.
10. **Make count-first a gate** (SCI-M4): pre-registered thresholds, artifact spec,
    DEV-text-only scope; and add the activation-cycle obligations to §7 (SCI-M3).

Minor items (registration duties, determinism hygiene, standard-tieing) ride along.
After revision, this document needs a clean-context re-review before any build, per the
standing rule that a design's own review cycle is where its flaws are paid for, not
discovered at MEASURE.

— END OF REVIEW
