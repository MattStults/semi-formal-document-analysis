# IMPLIED-EFFECTS — the four blocking findings, made rulable

**The question:** `IMPLIED_EFFECTS_ADVERSARIAL_REVIEW.md` returned REVISE with four
blocking findings (ENG-B1, ENG-B2, SCI-B1, SCI-B2). Each needs a decision only the project
lead can make. This document makes each one rulable in one sitting.

**Status:** analysis for four rulings. **Nothing ruled, nothing implemented, no file edited.**
Written 2026-08-05. Every number below is a deterministic re-measurement of artifacts on
disk; no API spend.

⛔ **Not seat material.** This reads S3's flip outcomes and the census. Never hand it to the
attribution seat, the flip-adjudication seat, or the implied-effects approver.

**Why it is on the critical path:** S3b cannot OPEN until this layer has passed review AND
accepted m0239 as a tracked entry (`S3B_REDESIGN.md` §4B LAPSE CONDITION, §9 RECEIVER
READINESS). Four decisions are the whole bottleneck.

---

## 1. The thirty-second version

| finding | recommendation | one-line ground |
|---|---|---|
| **ENG-B1** — where implied patients enter the pricing | **(B1-2) per-atom factor only, plus an explicit taint-quantifier exclusion and a cap exemption** | measured: it restores m0239 to the *identical* score as the alternative, and it is the only reading that does **not** hand every entry the power to resurface m0276 from a *sibling* atom |
| **ENG-B2** — the key space is unbound | **(B2-1) key = `containment.dechain_name`, translation sha in the artifact header, hard-fail on unresolvable keys** | the review's own recommendation (`grammar.stem_of`) is **wrong** — it strips polarity and merges `must_x` with `mustnot_x`; `containment.py:141` says so in its docstring |
| **SCI-B1** — the proposal queue is unfenced | **(S1-2) blind enumeration is the only proposal source, with a named, disclosed one-instance exception for m0239** | m0239 *is* flip-surfaced; pretending otherwise is a lie, and banning it outright kills the layer's own driver case |
| **SCI-B2** — no negative controls | **(S2-1) m0276 + m0290 pinned suppressed by test, mechanical restoration signature for m0239, automatic REVERT — and v1 ships with §4.2 signature-batch DISABLED** | verified: the design's exemplary signature matches **72 clauses including m0276 and m0290**; approving that class resurfaces both (measured, §6.2) |

**The entry count (§2), because it decides SCI-B2's shape:** the layer plausibly needs
**single digits at OPEN and at most ~41 entries ever for the Model Spec** — of which only
**10 clauses** can move a prediction under the patient sets currently declared, and they are
named below. **Manual approval is affordable. The signature-batch path is not forced, and
should be switched off in v1.**

**Three things I found that contradict a document you are being asked to trust** — details in
§3.4, §4.1, §7:
1. The review's ENG-B2 fix recommends `grammar.stem_of`. It is the wrong function.
2. The review says the two ENG-B1 readings "diverge concretely" on m0239. **They don't** —
   m0239 scores 0.4520 either way. They diverge on *m0276*, in the opposite direction from
   the one the review's framing suggests.
3. Nobody has noticed that an implied entry on **m0275 or m0466** would let S3b's §7.1
   restoration plank **pass without the attribution mechanism doing anything** — the
   signature reads `why: consistent` + factor 1.0, which an implied entry manufactures.

---

## 2. Count-first — how many entries does this layer need?

The design mandates a count (§5) and never does one. Here it is, three frames deep, because
the frame turns out to matter more than the number.

### 2.1 The frame the brief handed me is the wrong one — and D5 says so

The brief points at `D5_WORKED_EXAMPLES.md` §6's "**~30** census cases whose clauses name no
party at all" as "the natural candidate pool." Read D5's own table again:

| sub-cause | feature that addresses it | cases |
|---|---|---|
| Bearer named, isn't the query's patient | S3b attribution | 79 |
| Bearer nameable, atom is an act | population extension (D5b) | ≤17 |
| **Bearer implied, never named in the text** | **implied-effects layer** | part of the remaining 59 |
| No party at all — the clause is about answer quality | **not an attribution problem**; query-atom curation (S6/S6b) | ~30 |

The ~30 are D5's **fourth** row, explicitly routed *away* from this layer. The implied layer
is the **third** row. The two are different sets, and the difference is exactly m0239:
m0239's clause *does* name a party ("If a **user** shows signs of vulnerability to
radicalization…") — it names the **wrong** party. **A clause that names nobody is a
helpfulness/answer-quality clause with no harm in it; a clause that names the near party
while protecting a far one is the implied-effect shape.** Sizing the layer off the
no-party row would have sized the wrong thing.

I enumerated the row anyway, since the brief asked. Reproducing D5's pipeline (155
`fp_promiscuous_atom` cases → reachability by the 439 population → text classification) I
get **75 unreachable**, split **19 / 46 / 10** rather than D5's 76 and 17/29/30. The
difference is entirely the party-noun word list, which D5 does not publish; my list counts
"you/your/the assistant" as near-party mentions and D5's evidently does not. **Treat both
splits as soft.** My 10 no-party cases sit on 9 clauses, and reading them settles the
question of what row they belong to:

> m0376 `ask_clarifying_questions`, m0451 `deep_understanding`, m0407
> `should_fill_information_gaps`, m0378 `minimize_unintended_consequences`, m0322
> `psychological_manipulation`, m0243 `may_provide_critical_factual_discussion`, m0046
> `may_override_guidelines`, m0051 `prioritize_competing_goals`, m0126 `tradeoff_handling`.

Seven of the nine are answer-quality or instruction-hierarchy clauses ("**Guideline**:
Instructions that can be implicitly overridden"). There is no implied beneficiary to approve
because there is no harm and no protection. **The no-party row yields ≈0 implied-effect
entries, not ~30.**

### 2.2 The right frame — the m0239 shape, counted mechanically and panel-blind

The m0239 signature stated as a predicate over the translation only (no census, no panel, no
flip outcome):

```
clause has >= 1 chained atom, and EVERY recorded patient on the clause is in
    {user, developer, operator}                      # the act is aimed at a near party
AND clause text + glosses carry harm/risk/victimization vocabulary
```

**72 clauses match.** Splitting them by whether the clause text also names a third-party-class
noun (which would make the bearer *nameable*, i.e. S3b's job rather than this layer's):

* **41 clauses** name no third-party-class noun — the candidate pool proper. m0239 is in it.
* 31 clauses do name one — S3b territory (and, awkwardly, m0276 and m0290 land here; §6.2).

**41 is the ceiling on plausible entries for the entire Model Spec**, and it is an ungenerous
ceiling: it is "clauses where a human *might* find an implied far-party effect", not "clauses
where one exists". A sample, so you are not deciding from a count:

| clause | text (opening) | plausible implied effect? |
|---|---|---|
| m0239 | *"If a user shows signs of vulnerability to radicalization…"* | **yes** — the flagship |
| m0273 | *"Example: volume of a bomb with intent to build"* | **yes**, and obvious |
| m0298 | *"Agentic systems risk security vulnerabilities analogous to buffer overflow…"* | **yes** — the harm lands on whoever's systems |
| m0221 | *"Write a letter that plays on my neighbor John's insecurities…"* | **yes** — John |
| m0263 | *"If the user is streaming video and the assistant identifies something on camera that could cause imminent bodily harm…"* | **no** — the bearer is the user, and it's named |
| m0287 | *"Example: medical question… when i stand up too quickly, i get dizzy"* | **no** — user only |
| m0110 | *"Example: user/developer conflict: off-topic request"* | **no** — no third party in sight |

Roughly half the pool falls away on reading, which is the point of manual review.

### 2.3 The number that actually decides affordability

An entry changes nothing unless a query with declared patients credits a match on that
clause. Measured over the frozen `join-integrity-v2-2026-08-04` baseline with the declared
sets `harm-avoidance → {third_party}`, `helpfulness → {user, developer}`:

* clauses with ≥1 credited match: **60** (harm-avoidance) + **142** (helpfulness)
* clauses **tainted** (where an entry could move a score): **21** + **2** = **23**
* of the 23, clauses where an implied `third_party` entry on the matched atom would **cross
  the cut**: **10** — m0108, m0111, m0194, m0239, m0275, m0276, m0290, m0355, m0466, m0575.

Ten. Named. That is the layer's live blast radius today, and four of those ten are clauses
with strong prior rulings attached (m0275/m0466 are S3b's restorations; m0276/m0290 are the
must-stay-suppressed controls).

### 2.4 The answer

**Plausibly needed entries: ~5–15 approved entries for the Model Spec, out of a mechanical
candidate pool of 41, with 1 (m0239) needed for S3b's receiver-readiness gate.**

At that size, per-entry manual review is trivially affordable — an afternoon, comparable to a
single golden-review sample. **The §4.2 signature-batch path is not forced by the count, and
§6 shows it is dangerous. It should be switched off in v1 by ruling**, which collapses most
of SCI-B2's surface (a class approval you cannot perform cannot sweep m0276 in).

Sensitivity: this is the Model Spec only. `ITERATION_LOOP.md` §5 seals the constitution as
TEST, so counting its implied-effect needs during iteration is consulting it (SCI-M4's
second point, which I think is correct). The constitution's count is not knowable now and
should not be attempted now.

---

## 3. ENG-B1 — where do implied patients enter the pricing?

### 3.1 What you need to know to judge this (no section references)

A query declares which parties it cares about. For each clause the scorer does three
separate things with patient information:

1. **Per-atom factor.** A matched atom whose recorded parties overlap the query's gets full
   credit; one whose parties are disjoint gets 10% credit.
2. **Clause taint.** If a clause carries party information *anywhere* and *none* of it
   overlaps the query, the whole clause is treated as evidence against — even its
   party-free matches get 10%. **One overlapping atom anywhere on the clause switches this
   off.**
3. **The taint cap.** On a tainted clause with more than one credited match, only the
   biggest match keeps its 10%; the rest are zeroed.

An implied-effect entry adds a party to an atom. The design's formula (`∪`) does not say
whether the added party is visible to (1), to (2), or to both. **(2) is the powerful one**:
it is a clause-wide switch, and it is the mechanism that keeps m0276 suppressed.

### 3.2 The measurement the review did not do

I built the implied layer both ways over the frozen baseline and scored it.

| entry | reading | m0239 | m0276 |
|---|---|---|---|
| `third_party` on m0239's matched atom `should_deescalate_extremist_involvement` | factor+taint | 0.1351 → **0.4520**, predicted | — |
| same | **factor only** | 0.1351 → **0.4520**, predicted | — |
| `third_party` on m0276's **sibling** `mustnot_enable_self_harm` | factor+taint | — | 0.1781 → **0.4567, RESURFACES** |
| same | **factor only** | — | 0.1781 → 0.1781, **stays suppressed** |
| `third_party` on m0276's **matched** atom `imminent_bodily_harm` | either | — | 0.1781 → **0.4567, RESURFACES** |

(cut = 0.2365; m0290 behaves identically to m0276.)

**Two facts the review's framing gets backwards.** First, the readings do **not** diverge on
m0239 — same score, same flip, to the last digit, because m0239 has exactly one credited
match so the cap never fires. Second, where they *do* diverge, **the factor-only reading is
the safer one**: it denies an entry the power to defeat taint from a sibling atom, which is
precisely the m0276 attack SCI-B2 is about. Factor-only narrows the attack surface from "any
atom on the clause" to "the atom the query actually matched" — it does not close it (row 5),
which is why the controls in §6 stay load-bearing either way.

### 3.3 The impossible state, and where it actually bites

`patient.py::_priced_record` documents that `why: consistent` and `clause_taint` "can never
collide". Factor-only makes them collide: taint is computed from translation chains, the
record is consistent by an implied patient. The review is right that this is a real defect —
and I can tell you exactly how big it is.

**The taint cap fires on exactly one clause in the corpus: m0220** (harm-avoidance; two
credited records; `shouldnot_manipulate_political_views` at base 5.695 and
`targeted_political_manipulation` at 4.451). Nowhere else, for either behaviour that declares
patients.

Simulating an approved entry on m0220's non-argmax atom:

* factor+taint: taint defeated, score 0.3954 → **0.6423**.
* factor-only: taint survives, the implied-consistent record is **zeroed with
  `why: taint_capped`**, score 0.3954 → **0.3954**. The approved judgement does nothing, and
  the explain trail never mentions it.

That is the review's silent leak, with a name and a number. It is one clause today, but it is
the exact shape ("a guarantee that looked mechanical but lived outside the code") this repo
keeps getting burned by, so a chosen reading must dispose of it explicitly rather than rely
on the population being small.

### 3.4 Against S3b §5.3's four branches

The design is written against a pricing regime that will not exist when it ships. Under S3b,
pricing reads attributed `affected_parties`, in a four-branch ladder: (1) unresolved/`unclear`
→ 1.0, **excluded from the taint quantifier and cap-exempt**; (2) comprehensive generic →
1.0, exempt; (3) resolved+consistent → 1.0; (4) resolved+disjoint → d. Taint quantifies over
**resolved+specific** atoms only.

m0239 under S3b: strict attribution can only license `{user}` on its matched atom (that is
ruling (b)'s whole ground), so the atom is **resolved+specific**, branch 4, tainted,
re-suppressed. So the implied layer must state which of these it does:

* **(i) implied patients join `affected_parties`** before the ladder runs → m0239's set
  becomes `{user, third_party}`, branch 3, factor 1.0, taint defeated. Simple, and it is the
  factor+taint reading in S3b clothing — with the same m0276 sibling exposure.
* **(ii) implied patients are consulted only when the ladder has already selected a branch**,
  as a factor override on branch 4 → the factor-only reading; taint unchanged; the branch-1
  cap-exemption machinery already exists, so the m0220 zeroing defect is **fixable by
  routing implied-consistent records into S3b's EXEMPT set** rather than the capped set.

That is the real prize: **S3b's §5.3 already has an exemption channel that patient.py 2.0
does not.** Factor-only is defective under 2.0 (m0220) and clean under S3b.

### 3.5 The options

**(B1-1) Implied patients enter both the factor and the taint quantifier** (the design's
apparent intent).
*Does:* union at the source; one code path; matches §2.4 as literally written.
*Costs:* nothing extra to build.
*Risks:* hands every approved entry a clause-wide taint switch. One entry on any sibling atom
of m0276 resurfaces it (measured, 0.4567). Under S3b this means implied patients are written
into `affected_parties`, blurring the line between the judgement layer and the
document-grounded attribution the whole architecture exists to keep separate.
*Score envelope:* raw scores may move **up**, unboundedly relative to a discounted baseline
(0.1 → 1.0 on the matched record, plus every party-free sibling credit released from taint).
Monotone-downward (I2) is **violated in the up direction** — which is fine, but it must be
pre-registered, because it is the first mechanism in this project that can raise a raw score.

**(B1-2) Implied patients enter the per-atom factor only, with two explicit repairs** —
*recommended*.
Repair (a): an atom carrying an active implied entry is **excluded from the taint
quantifier** (it neither creates nor defeats taint). Repair (b): an implied-consistent
record is **exempt from the taint cap**, never zeroed — the S3b branch-1 exemption pattern,
back-ported.
*Does:* restores m0239 at 0.4520 (measured, identical to B1-1); leaves m0276/m0290
suppression untouched from sibling atoms; disposes of the m0220 collision by ruling instead
of by hoping.
*Costs:* two extra rules and two extra tests; `why` values need a new member
(`consistent_implied`) so the explain trail cannot lie.
*Risks:* an entry on a **matched party-free** atom still resurfaces m0276 (row 5 of the
table) — controls still required. The `tainted=True` flag remains observable alongside a
non-discounted record, so the explain payload must state that this is now a legal state.
*Score envelope:* raw score movement bounded by the matched records' own credit: each
implied-consistent record moves from `d·base` (or `0.0` if it was capped) to `1.0·base`; no
other record on the clause moves. Every other clause is untouched. This is a **strictly
smaller** envelope than B1-1 and is stateable in one line for pre-registration.

**(B1-3) Sequence the layer after S3b: define implied effects only over `affected_parties`,
and do not build against pricing 2.0 at all.**
*Does:* removes the double specification the review demands (state it once, against §5.3),
and inherits S3b's exemption channel free.
*Costs:* the layer cannot exist before S3b lands — but **S3b cannot OPEN until this layer
has passed review and accepted m0239**. That is a deadlock unless "accepted as a tracked
entry" is read as a *tracker* state, not a *shipped code* state. §4B's wording ("its tracker
has ACCEPTED m0239 as a tracked entry") supports the weaker reading, but this option should
not be taken without ruling that question explicitly.
*Risks:* deadlock if the readings differ; a reviewed-but-unbuilt receiver may not satisfy a
later reader of the lapse condition.

**Recommendation: B1-2, stated twice as the review demands** — once against `patient.py` 2.0
(with repairs (a) and (b) explicit, m0220 named as the single live instance) and once against
S3b §5.3 (as a factor override on branch 4, with implied-consistent records joining the
EXEMPT set). Ground: it produces the *same* restoration of m0239 as B1-1 while denying every
entry the sibling-taint power that is the layer's single largest hazard, and it keeps
`affected_parties` free of judgement content.

**What would change my mind:** a case where the *right* answer is that an implied effect
should redeem a clause whose match ran through a *different* atom — i.e. genuine clause-level
implied effect. §8-E1 asks this question and the count in §2 does not answer it. If such a
case is named, B1-1 becomes the honest reading and the controls have to carry more weight.

---

## 4. ENG-B2 — binding the key space

### 4.1 First: the review's own recommendation is wrong

The review says to pin the key as "dechained stem via `grammar.stem_of`". `stem_of` strips
the **polarity prefix too**:

```
grammar.stem_of("should_deescalate_extremist_involvement__model_user")
    -> "deescalate_extremist_involvement"          # NOT a key anything prices
grammar.stem_of("must_x") == grammar.stem_of("mustnot_x") == "x"
```

`containment.py:141` names this hazard in its own docstring — *"NOT `grammar.stem_of`, which
strips polarity too and would merge `must_x` with `mustnot_x`."* The correct function is
**`containment.dechain_name`**, which yields `should_deescalate_extremist_involvement` — the
exact string in the design's §2.3 example, and the exact string the pricing keys and the
explain trail print. The review's direction was right; its named function was not. Anyone
implementing the review verbatim would build a layer whose every key silently fails to
resolve, or (worse) resolves a `mustnot_` entry onto a `must_` atom.

**The v1.2 join warning in the brief is confirmed by measurement:** the translation carries
**373 chained atom instances of 1442** (368 with chains of length ≥ 2), spelled
`..__model_user`; the pricing side holds dechained names only. An analysis or a key that
skips dechaining reports zero on the entire chained population.

### 4.2 The three sub-decisions

**Key form.**
* **(B2-a) `containment.dechain_name` (polarity + stem, chain stripped)** — the pricing join
  key; survives the five `atom_refactor` rechain migrations (they move chains, stems and
  polarity stay); one entry covers all spellings of the atom on that clause.
* (B2-b) The full chained instance name — maximally precise, breaks on every rechain
  migration, and does not match what the explain trail prints (so the `imp-<id>` citation
  would name a string the user never sees).
* (B2-c) The 3-tuple `(clause_id, span_id, name)`, matching S3b's attribution key —
  strictly more precise, and the only form that can distinguish two occurrences of one atom
  name in one clause. Costs a span-id join the implied artifact does not otherwise need.

**Translation identity.**
* **(B2-d) sha256 of the translation in the artifact header, plus a verbatim `clause_quote`
  per entry**, mirroring `briefs/backfill_author.md`'s `worksheet_sha256` and S2's
  `license_quote`. Note the annotation artifact carries **no self-identifying version or sha
  field** — its `provenance` block records model/run_id/created only — so the header sha must
  be computed over the file, exactly as `snapshot.py` does.
* (B2-e) Version string only (the design's current position). Two artifacts can both claim
  "v1"; §7's "byte-frozen at G-freeze" claim becomes unverifiable. Reject on the record.

**Stale keys.**
* **(B2-f) Hard-fail at load.** Matches the project's stated bias twice over
  (`grammar.stem_of`: "rewriting the join key on a name we could not read is the one failure
  that would be invisible downstream"; `parse_name`: "a convention that silently half-parses
  is worse than none").
* (B2-g) Skip with a warning — deletes approved human judgement with no signal. This is the
  canonical silent-failure mode the repo has been bitten by twice.
* (B2-h) Hard-fail, with a declared migration escape: a keyed atom that legitimately changes
  gets an `atom_refactor`-style migration entry recorded in the artifact's lifecycle, so the
  break is repaired visibly rather than tolerated.

**Recommendation: B2-a + B2-d + B2-h.** Ground: `dechain_name` is the only form that is
simultaneously the pricing key, the explain-trail spelling, and migration-stable; the sha
binding is the project's existing pattern for exactly this problem; hard-fail-with-migration
converts an invisible deletion into a loud, repairable event. **Reject `grammar.stem_of` on
the record**, with the polarity-merge reason stated, so the review's recommendation is not
re-adopted by a later reader.

**What would change my mind:** if the count in §2 grew past ~50 entries, or if any clause
turned out to carry two occurrences of one dechained atom name with different implied
effects, B2-c (the S3b 3-tuple) becomes worth its join cost — and using S3b's key shape
would also make the two layers diffable.

---

## 5. SCI-B1 — fencing the proposal queue

### 5.1 The mechanism in plain terms

The design fences the *approver*: they see clause text and a proposed implication, never
panel verdicts or flip outcomes. That is a real fence and it does nothing about the
following: someone runs the tool, looks at where it disagrees with the panel, and proposes
implied effects **only on those clauses**, writing each rationale in pure document language.
Every entry is honestly approved. The approved set is 100% concentrated on
panel-disagreement clauses. MCC rises. That is panel-fitting, laundered through a blind
approval of a panel-selected queue.

### 5.2 The part that has to be said out loud

**m0239 was found this way.** Not by an adversary — by the process. It surfaced in S3's flip
adjudication; `S3B_REDESIGN.md` §4B quotes the adjudicator; the design's §2.3 example
rationale is a paraphrase of those words. Anyone who approves m0239 *while reading this
design document* has read a flip outcome. I-imp4 as written would refuse its own flagship
entry.

Two honest things follow, and they pull in opposite directions:

* `ITERATION_LOOP.md` policy 1 already permits this: *"Candidates from anywhere, provenance
  recorded… Labels are NOT trusted."* Flip-surfacing is legal **as attention**, provided the
  judgement is re-derived against the document and the provenance class is recorded.
* But the layer is judgement all the way down. There is no `license_quote` to check the
  re-derivation against — by construction (`briefs/backfill_author.md` rule 3 is *why*
  m0239 is here). So "re-derived against the document" is an attestation, not a check.

### 5.3 The options

**(S1-1) Blind enumeration only; no flip-surfaced proposals ever.**
*Does:* the strongest possible fence; the proposal set is a mechanical panel-blind
enumeration (§2.2's 41-clause predicate is exactly such an artifact), reviewed in a fixed
order, flips never consulted.
*Costs:* m0239 cannot be proposed — the layer's driver case and S3b's receiver-readiness
condition die with it. Unless m0239 is re-derived by a seat that has never seen the flip,
which is achievable only by dispatching a fresh seat over the blind enumeration and hoping it
lands on m0239 independently.
*Risks:* the whole S3b sequencing stalls on a coin flip.

**(S1-2) Blind enumeration is the proposal source; flip-surfaced proposals are legal, carry
a `proposal_source` class on the entry, and are disclosed** — *recommended*.
*Does:* two provenance classes on every entry, `blind_enumeration` and `flip_surfaced`; the
approval for a flip-surfaced entry is dispatched to a seat with the residual exclusion list
(census, `audit_dossiers`, S3/S3b cycle records, `IMPLIED_EFFECTS_DESIGN.md`, this document,
`HANDOFF.md`, prior `flip_verdicts*.json`), and the **rationale is authored by that blind
seat, not carried over** — a rationale written by someone who saw the verdict imports the
verdict.
*Costs:* two dispatch paths and a written approver brief; m0239 must be re-approved from
clause text by a seat that has not read §4B, with the existing rationale discarded rather
than reused.
*Risks:* `proposal_source` is an attestation; nothing mechanically proves an entry labelled
`blind_enumeration` wasn't queue-selected. The honest mitigation is the ratio: if the
approved set is overwhelmingly `flip_surfaced`, that is a visible, reportable fitting
signature — which S1-3 turns into a rule.

**(S1-3) S1-2 plus a pre-registered concentration check.**
*Does:* adds one number to the activation cycle: the share of approved entries that are
`flip_surfaced`, and the share of the blind enumeration's 41 candidates that were actually
reviewed. A layer whose entries are 100% flip-surfaced and whose blind pool was never worked
is queue-selection laundering, visibly.
*Costs:* obliges someone to actually work the blind enumeration rather than only the flagged
cases — which, at 41 candidates (§2), is affordable.
*Risks:* none I can see beyond the work.

**Recommendation: S1-3 (i.e. S1-2 with the concentration check).** Ground: S1-1 is the
cleanest fence and it kills the layer's purpose; S1-2 alone relies entirely on attestation;
the concentration check is the only part of this that a reader can *verify*. And explicitly:
**m0239 ships as a disclosed one-instance exception with `proposal_source: flip_surfaced`, a
re-derived blind rationale, and the disclosure stated in the entry itself** — not smoothed
over.

**What would change my mind:** if a blind seat dispatched over the §2.2 enumeration proposes
m0239 independently, S1-1 becomes available at no cost and should be taken. That experiment
is cheap and could be run before ruling.

---

## 6. SCI-B2 — negative controls

### 6.1 Verifying the review's central claim myself

The review asserts §4.2's signature path is *"provably unable to separate m0239 from
m0276"*. I did not take that on trust. The design's own exemplary signature — "model-protective
act whose harm averts onto unspecified others" — written as a predicate over the translation
is the one in §2.2. Measured:

* **72 clauses match**, and both **m0276 and m0290 are among them**.
* Approving that class (an implied `third_party` on the matched atom of each) resurfaces
  **m0276 at 0.4567** and **m0290 at 0.3694**, against a cut of 0.2365. Both are the
  canonical must-stay-suppressed cases whose re-surfacing is `S3B_REDESIGN.md` §7.2's
  automatic REVERT.

**Claim verified.** With one correction worth having: adding a "clause text names no
third-party-class noun" conjunct *does* exclude m0276 and m0290 — but for the wrong reason.
m0276 is excluded because its text happens to say *"there are **people** and resources who
care"*, which is D5's standing lesson verbatim: a party appearing in the text is not the
party bearing this atom's harm. A signature that separates the cases by accident of
vocabulary is not a separator; it will fail the first time a genuine third-party clause omits
the word. And m0275 — which S3b must restore *through attribution* — sits in the same bucket
as m0239, so the signature cannot mark the boundary between this layer and S3b either
(SCI-M2's arbitrage, measured).

### 6.2 The blast radius, named rather than described

Every implied `third_party` entry on the matched atom of each of the 21 clauses that are
tainted for harm-avoidance, and what it would do:

| crosses the cut (10) | already predicted, score rises (11) |
|---|---|
| **m0108, m0111, m0194, m0239, m0275, m0276, m0290, m0355, m0466, m0575** | m0175, m0176, m0214, m0220, m0221, m0222, m0260, m0263, m0264, m0578, m0588 |

Four of those ten already carry rulings: m0275/m0466 are S3b's restorations (an implied entry
there is the SCI-M2 arbitrage), m0276/m0290 are the controls. The layer's power and its
hazard are the same power, on the same ten clauses.

### 6.3 A finding neither document contains

S3b's §7.1 restoration signature checks each named clause for `factor 1.0` **and**
`why: consistent` **and** `predicted`. An implied entry produces exactly that triple.
**If the implied layer is ON when the S3b restoration plank is evaluated, an implied entry on
m0275 or m0466 makes the plank PASS with the attribution mechanism having done nothing** —
the precise failure mode ("restored BY the mechanism" vs "never touched") that §7.1 was
rewritten to close. The fix is small and belongs in whatever ruling comes out of §3: the
explain trail must carry a distinct `why` value for an implied-consistent record
(`consistent_implied`), and §7.1's arm (i) must require `why == consistent` **and** an
attributed non-empty `affected_parties ∩ P` from the frozen attribution artifact, not from
the implied layer. Flag this to whoever owns S3b — it is a cross-document defect, not this
layer's alone.

### 6.4 The options

**(S2-1) Full control pre-registration + signature-batch disabled in v1** — *recommended*.
1. **Control set:** m0276 and m0290 asserted `no_longer_predicted` for every behaviour that
   declares patients, with the layer ON, **pinned by test** and pre-registered in the
   activation cycle's prediction. **If either re-surfaces, REVERT regardless of all else** —
   §7.2's words, adopted verbatim so the two documents cannot drift.
2. **Restoration signature for m0239:** `predicted` AND the explain trail cites the
   `imp-<id>` AND `factor 1.0` AND `why: consistent_implied` on
   `should_deescalate_extremist_involvement`. "Still predicted" is not enough — the same
   lesson §7.1 learned.
3. **§4.2 signature-batch approval is DISABLED for v1** by ruling, with §6.1's measurement as
   the ground and the count in §2 as the affordability argument. It can be re-opened by a
   named ruling if a later count makes manual review genuinely infeasible.
4. **Revert rule:** the activation cycle reverts on control re-surfacing, on a missing
   restoration signature, or on any flip the layer causes that adjudicates as a regression
   (`max_regressions: 0`, the S3 precedent).
*Costs:* four tests and a pre-registration; loses batch approval, which §2 says is not
needed.
*Risks:* the control set is two clauses. Nothing guarantees a third m0276-shaped clause
isn't out there — mitigated but not solved by the §6.2 table, which at least names every
clause the layer can move today.

**(S2-2) Controls only, keep §4.2 alive with mandatory negative exemplars.**
*Does:* signature batches remain legal but require stratified **negative** exemplars (the
must-suppress clauses matching the signature's syntactic shape) and a **measured
false-positive count** on them, plus a named ruling per use.
*Costs:* someone must construct a negative stratum for each signature.
*Risks:* §6.1 says the beneficiary type has no separating signature. A negative-exemplar
requirement on a signature that provably cannot separate produces a measured FP rate and then
a judgement call about whether it is "low enough" — which is how a 50%-valid signature ships.

**(S2-3) Controls + a corpus-wide suppression assertion.**
*Does:* S2-1, plus assert that **no clause currently suppressed by taint for a
patient-declaring behaviour becomes predicted** except those with an approved entry naming it
— i.e. the §6.2 left column is the exhaustive allowed change set, pinned.
*Costs:* one broader test; must be re-derived when the baseline moves (and must **not** pin
an exact count — `AGENTS.md`'s rule).
*Risks:* couples the layer's test surface to the baseline snapshot; a legitimate baseline
change breaks it noisily. That may be the point.

**Recommendation: S2-1, with S2-3's assertion if you want the belt.** Ground: the controls
are cheap and the review is right that they are missing; disabling §4.2 in v1 is licensed by
a measurement (72 clauses, both controls swept in) rather than by caution, and by a count
that says nobody needs it.

**What would change my mind:** a count-first result an order of magnitude larger than §2 —
say a second document needing hundreds of entries. Then §4.2 has to be made safe rather than
switched off, and S2-2's negative exemplars become the minimum bar rather than a half
measure.

---

## 7. What contradicts the review or the design

1. **`grammar.stem_of` is the wrong key function** (§4.1). The review recommends it by name;
   `containment.py:141` documents why it must not be used. Use `containment.dechain_name`.
2. **The ENG-B1 readings do not diverge on m0239** (§3.2) — 0.4520 either way, because m0239
   carries one credited match and the cap never fires. The review's "one produces a state the
   pricing documents as impossible" is true; its implication that the intended outcome
   requires the taint-quantifier reading is not.
3. **The safety ordering is the reverse of the review's framing** (§3.2). Factor-only denies
   the sibling-taint attack that resurfaces m0276; factor+taint grants it.
4. **The taint cap fires on exactly one clause corpus-wide (m0220)** (§3.3). The review
   describes the silent-zeroing leak as a class; it is currently a single named instance —
   which makes it cheap to rule on and equally cheap to forget.
5. **D5 §6's ~30 no-party cases are not this layer's candidate pool** (§2.1) — D5 routes them
   to query-atom curation, and reading the nine clauses confirms it (`ask_clarifying_questions`,
   `tradeoff_handling`, "Guideline: instructions that can be implicitly overridden"). The
   brief's framing of them as "the natural candidate pool" would have sized the wrong set. My
   reproduction of D5's split also differs (75 unreachable, 19/46/10 vs D5's 76 and 17/29/30);
   the party-noun word list is unpublished and the split is sensitive to it.
6. **An implied entry can make S3b's §7.1 restoration plank pass with no attribution
   involved** (§6.3). Neither document notices. Cross-document, needs a `why` value that
   distinguishes the two sources.
7. **The design says implied entries only extend; the mechanism says they can also suppress.**
   An implied patient on a currently party-free atom makes it *mismatched* for every disjoint
   query and can *create* taint. Nothing in §2.4 or §3's invariants acknowledges a downward
   path, and I-imp1's "absent or OFF ⇒ bit-identical" says nothing about it.
8. **The layer is the first mechanism in this project that can raise a raw score.** `patient.py`
   I2 is "monotone downward on raw scores"; the implied layer removes discounts. Whatever is
   ruled in §3 must pre-register this, or the first person to check I2 against the layer will
   read it as a defect.

---

## 8. What I can't tell you

* **Whether any of the 41 candidates other than m0239 should actually be approved.** Deciding
  that is the approver's job under a brief that does not exist yet (SCI-M1), and doing it here
  — in a document that has read the flip outcomes — would be the exact laundering §5 is about.
  My §2.2 sample is a readability check on the pool, not a proposal.
* **Whether the ~5–15 estimate holds for the constitution.** It is sealed TEST. I did not look,
  and I don't think anyone should before the frozen-pipeline phase.
* **Whether the control set is sufficient.** m0276 and m0290 are the two known cases. §6.2
  names every clause the layer can move under *currently declared* patient sets; a future
  behaviour declaring a different set re-opens the question, because entries are
  clause-scoped and behaviour-agnostic by design.
* **Whether the S3b deadlock in B1-3 is real.** It turns on reading "receiver readiness" as a
  tracker state vs a shipped-code state. §4B's wording favours the tracker reading, but that
  is a coordinator ruling I am not making.
* **The exact size of D5's 30.** My classifier disagrees with D5's and neither word list is
  authoritative. What I can say is what the clauses *are*, which is why §2.1 lists them by
  name.
* **Anything about correctness of the judgements themselves.** Determinism of output does not
  certify judgement (SCI-m1 is right about this); the controls, the brief, and revocation are
  the only things that do.

---

## Appendix — reproduction

Deterministic, read-only, no API spend, no `cycle.py`, no network.

**Baseline:** `join-integrity-v2-2026-08-04` config —
`modelspec_clauses.json`, `annotations_ext_v1_merged.json`, `overlay_empty.json`,
`behavior_atoms_audit_v1.json`, `behaviours_query.json`, `thresholds_frozen.json`
(harm-avoidance cut 0.2365055873; helpfulness cut 0.3131186309).
Declared patients as recorded in `snapshots/patient-pricing-2026-08-04.json`:
`harm-avoidance-to-third-parties → [third_party]`, `helpfulness → [developer, user]`.

**Simulation:** `patient.PatientIndex` subclassed with an `implied` map
`{clause_id: {dechained_atom: frozenset(patients)}}` and a `mode` switch:
`A` merges implied patients into both the per-atom patient set and the taint quantifier;
`B` merges them into the per-atom set only. Scores normalized exactly as `snapshot.py`
does (raw/max, `round(…, 10)`), predicted = `s > 0 and s >= cut`.

**Population predicates** re-implemented from `ATTRIBUTION_POPULATION_ENUMERATION.md`
§2.3–2.5 (verified: 368 chained + 71 b-trim = **439**, matching the enumeration).

⚠️ **The v1.2 join matches on DECHAINED names.** All keys above go through
`containment.dechain_name`, never `grammar.stem_of` (§4.1). The translation carries 373
chained atom instances; a lookup that skips dechaining reports zero on all of them.

**Sources:** flip evidence from `cycles/patient-pricing-2026-08-04/flip_dossiers/` (m0239,
m0276, m0290 `explain_b.patient_pricing`); census rows from
`audit_dossiers/ext_v1_merged__audit_v1/verdicts_merged.json` (155 `fp_promiscuous_atom` of
294) joined to clauses via each dossier's `mapped_clauses` and
`discriminators.exact_name_intersection` — **census-derived numbers are attention only and
appear in §2.1 solely to answer the brief's question about D5's 30.**
