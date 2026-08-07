# S3B Finding Reclassification (2026-08-06)

Second pass over the S3B adversarial review findings, sorting each by **one question:**

> **Was the fix stateable in the representation that existed when the finding was raised?**

Not "what is the finding about." `RELATIONAL_TURN_DECISIONS.md` V8 classified by subject matter
and got ~45% representation; that method put M-1 in the representation bucket even though the
reviewer named the fix in R1 and it recurred anyway. This pass classifies by *availability of the
fix*.

**Buckets:** `INEXPR` (concept could not be written down — needs relational encoding) ·
`EXPR-UNVER` (fix was stateable; prose could not enforce it — needs typed fields, operational
definitions, executable formulas) · `PROCESS` (vacuity, pre-registration, blindness, scope —
needs the executable envelope) · `DOC` (update anomaly — needs normalization).

Source: `S3B_ADVERSARIAL_REVIEW{,_R3,_R4,_R6,_R8}.md`, finding bodies read, not headings.

---

## Classification

| # | finding | bucket | grounds |
|---|---|---|---|
| B-1 | §5.3 not computable; "harm-bearing atom" never defined | EXPR-UNVER | a predicate over attribution records; definition simply omitted |
| B-2 | restoring m0239 requires a bearer the clause text never names; the adjudication "had to supply the bearer by inference" | **EXPR-UNVER** *(was INEXPR — reclassified, see F2 retraction)* | the reviewer states two fixes in the finding body (`S3B_ADVERSARIAL_REVIEW.md:92–101`): widen §5.1's evidence regime **or** demote m0239 from the falsifiable core. The second was taken |
| B-3 | restoration plank vacuously satisfiable | PROCESS | `gate(baseline) = FAIL` |
| M-1 | harm-bearer value space + text→principal mapping unspecified | EXPR-UNVER | reviewer names the fix *and* the existing principal set in the same finding |
| M-2 | attribution keying granularity; atom-name keying would corrupt a control | EXPR-UNVER | **reviewer gives a stateable fix: "state in §5.1 that attribution is keyed per clause instance (clause_id + span), and validator-check it"** |
| M-3 | generic flag re-prices a golden case; d carried without re-derivation | PROCESS | constant carried forward without re-running its licensing procedure |
| M-4 | §7.5 pre-registers no figure/method/denominator/trigger | PROCESS | envelope: `threshold` is a number or the record fails |
| M-5 | blindness fence not airtight; repair channel unfenced | PROCESS | anti-cheat perimeter |
| M-6 | §7.1 misstates the adjudication record, drops m0018 | DOC | decision.json says 4, §7.1 names 3 — update anomaly |
| E-1 | clause-level composition has two contradictory readings | EXPR-UNVER | pick a reading and state it; formal notation forces one, prose permits both |
| E-2 | keying STILL unspecified (prior M-2) | EXPR-UNVER | recurrence |
| E-3 | value space + mapping STILL unpinned (prior M-1) | EXPR-UNVER | recurrence |
| E-4 | D5 population predicate has no operational definition, seat, or fence | EXPR-UNVER | definition + seat both available |
| E-5 | blindness fence is a denylist; HANDOFF.md carries the answer key and is mandated reading | PROCESS | anti-cheat; unrelated to encoding |
| E-6 | build seam unstated (version bump, dispatch branch, explain schema) | DOC | design incompleteness |
| E-7 | §2.1 misattributes the re-derivation remedy (wrong document cited) | DOC | citation error |
| S-1(R3) | restoration signature contradicts §7.1 for m0018 under every horn | PROCESS | a pre-registered check contradicting a pre-registered prediction |
| S-2 | signature's iteration set admits vacuity | PROCESS | vacuity |
| S-3 | d = 0.10 carried UNCHANGED; derivation never re-argued (prior M-3) | PROCESS | recurrence |
| S-4 | §7.5 STILL no figure/procedure/denominator/trigger (prior M-4) | PROCESS | recurrence |
| S-5 | falsifiable core no longer tests the headline defect | PROCESS | what the experiment covers |
| S-6 | stratified controls never re-attached; corpus-wide rule checked on 4–5 clauses | PROCESS | envelope `denominator` must resolve to a case set |
| S-7 | m0108's pricing undefined in a foreseeable state | **PROCESS** *(was EXPR-UNVER — reclassified)* | the reviewer's own fix is "pre-register m0108's expected pricing signature as an exploratory observation"; pre-registration is this document's `PROCESS` definition |
| S-8 | branch 2 hardcodes one horn of open D4 without stating dependence | DOC | unstated dependence |
| R4-E1 | formula dimensionally inconsistent (Σ missing `/atom_norm`), ambiguous on generics | EXPR-UNVER | **prose arithmetic nobody could execute**; as code this is one failing test |
| R4-E2 | subsumption composition never re-specified | EXPR-UNVER | `patient.py` already implements subsumption matching; the design just never said how the new rule composes |
| R4-E3 | F-linearity guarantee narrowed to RESOLVED mass; under-suppression is flip-invisible | EXPR-UNVER | a formal property, statable and checkable; left unproven |
| R4-B1 | m0239 demoted from core but not from the corpus-wide bound | PROCESS | scope/bound mismatch between two parts of the design |
| R4-S1 | §7.5's floor set AFTER observing the quantity it gates | PROCESS | hash-before-measure ordering |
| R6-E-1 | REVISION 6 self-contradictory about D3 — four locations OPEN, one RULED | DOC | textbook update anomaly |
| R6-E-2 | m0290's suppression not licensable: the only "user" in the clause text is the `<user>` XML speaker tag | **EXPR-UNVER** *(was INEXPR — reclassified, see F2 retraction)* | **already FIXED in-representation.** `S3B_ADVERSARIAL_REVIEW_R8.md:72–105`: TASK DESIGN §1.4 note (v) adds a first-person speaker-turn mapping, so the verdict "now carries a byte-exact verbatim license quote… **Licensable.** ✔" |
| R6-S-1 | exclusion points at an unreviewed draft; no lapse condition pre-registered | PROCESS | dependency on an unready receiver |
| S-A | restoration signature's arms are a free disjunction as written; appositive binding doesn't bind | EXPR-UNVER | formal notation binds explicitly; prose apposition does not |
| S-B | lapse state space undefined; two restatements disagree on which bound receives re-entry | DOC | (+ totality note) |

## Tally — CORRECTED 2026-08-06 after adversarial review

> **Three corrections applied.** (a) The original tally miscounted its own table (BL-4): 12
> `EXPR-UNVER` rows and 6 `DOC` rows, not 11 and 7. (b) **Both `INEXPR` rows are reclassified to
> `EXPR-UNVER`** (BL-5) — see the retraction of F2 below. (c) **S-7 moves to `PROCESS`**: the
> reviewer's own fix text is *"pre-register m0108's expected pricing signature as an exploratory
> observation"*, and pre-registration is this document's definition of the `PROCESS` bucket.

| bucket | occurrences | share | fix |
|---|---|---|---|
| `INEXPR` | **0** | **0%** | — nothing required a representation that did not exist |
| `EXPR-UNVER` | 13 | ~38% | typed fields, operational definitions, executable formulas |
| `PROCESS` | 15 | ~44% | executable envelope |
| `DOC` | 6 | ~18% | normalized design object |

*(34 occurrences; recurrences counted separately since each cost a review round. See the corpus
disclosure below — 34 is a subset, not the full record.)*

**The clean statement, replacing the earlier "~74%" figure** (which was arithmetically wrong — it
summed `PROCESS + EXPR-UNVER`, not "envelope + normalization"): with `INEXPR` empty,
**100% of the measured churn is addressable without any representation migration.** Envelope
covers 44%, typed fields and definitions 38%, normalization 18%.

## ⚠️ Corpus disclosure (MA-1) — 34 is a subset of ~54

"Source: … finding bodies read, not headings" read as complete. It is not. Omitted:
R1 `m-1`; R4 minors `e-1…e-4, s-1, s-2` (6); R6 minors `E-3…E-9, S-2, S-3, S-4` (10); R8 minors
`E-a, E-b, S-c` (3). Meanwhile R3's minors **are** included, and first occurrences `m-2…m-5` are
dropped while their R3 recurrences are kept — the reverse of the stated counting rule.

**So inclusion tracked nothing principled**, true occurrence count ≈ 54, and the omitted set is
`DOC`/`PROCESS`-heavy, meaning every percentage above understates those two buckets. The
direction of the headline is unaffected: `INEXPR` was 0 in the counted subset and the omitted rows
are minors and recurrences, none of which is a representation-impossibility claim. **Re-running on
the full 54 is outstanding.**

---

## Findings

**F1 — The relational encoding's exclusive share is ~6%, not ~45%.** V8 was wrong, and wrong in
the direction that flattered the proposal I was writing.

**F2 — RETRACTED 2026-08-06.** It read: *"Both `INEXPR` findings are the SAME defect… the fix is a
license taxonomy for facts."* **Both premises were wrong, and the bucket is empty.**

- **R6-E-2 was already FIXED, in-representation, and the fix is recorded in this document's own
  source file.** `S3B_ADVERSARIAL_REVIEW_R8.md:72–105`: TASK DESIGN §1.4 note (v) adds a
  first-person speaker-turn mapping (`<user>` turn ⇒ `user`), so *"the {user} verdict now carries a
  byte-exact verbatim license quote… satisfying §1.2(b)'s regime. **Licensable.** ✔"* A mapping
  rule **inside** the existing quote regime — not a license taxonomy, not relational arguments.
- **B-2 fails the same test.** The reviewer states two fixes in the finding body
  (`S3B_ADVERSARIAL_REVIEW.md:92–101`): widen §5.1's evidence regime, **or** demote m0239 from the
  falsifiable core. The second was taken (R4-B1 presupposes the demotion).
- F2 also contradicted its own bucket definition: it conceded *"relational argument positions are
  not required for either"* while `INEXPR` is defined as *"needs relational encoding."*

⇒ **`INEXPR` = 0. No S3B finding in this corpus required a representation that did not exist**, and
the relational migration's churn attribution is **0%**, not ≈0%. The conclusion is strengthened,
not weakened, by the retraction.

**F3 — M-2 is not representation evidence, correcting my earlier claim.** I had cited it as the
one finding that "does not survive translation," on the grounds that the reviewer named atom-name
keying as the hazard. Reading the body, the reviewer also names a stateable fix in the same
paragraph — *key per clause instance, validator-check it*. Relational encoding makes correct
keying the **default** rather than making it **possible**. That is a real but much weaker claim.

**F4 — CORRECTED: 62% is envelope + normalization** (44% + 18%); the earlier "~74%" summed `PROCESS + EXPR-UNVER`, a different pair. With `INEXPR` empty the operative figure is that **100%**, neither of which needs any migration and
both of which apply to the existing propositional system unchanged.

**F5 — The largest single sub-class inside `EXPR-UNVER` is prose that should have been code.**
R4-E1 is a dimensionally inconsistent formula; E-1 and S-A are binding/scope ambiguities that
formal notation cannot have; R4-E3 is an unproven formal property. These do not need *relational*
encoding — they need the artifact to be **executable at all**.

## What this does and does not change

**Does not touch the other two arguments for the relational turn**, which were never about churn:
1. **Tool accuracy** — H006 needs multi-hop subsumption (`public_official ⊑ third_party`,
   `privacy_breach ⊑ harm`), currently inexpressible with `is_a` absent and closure one-step. Two
   of the four adjudicated tool misses are this shape.
2. **Hypothesis cost** — "implied impact on an unnamed party" as a mode declaration plus an
   extractor versus a bespoke code project.

**Does change the justification and the ordering weight.** The relational encoding should be
argued on capability and hypothesis economics, **not** on review-churn reduction. D9's sequencing
(process first) was right, but for a stronger reason than stated: the process work is not merely
cheaper to do first — it captures roughly three quarters of the churn *by itself*.

## Limits

- One design's reviews (S3B), 34 occurrences. Not a sample of the project's history.
- Classified by me, with a stake in the answer, having asserted-then-retracted five times this
  session. B-1, E-4, R4-E3, S-7 and S-B are boundary calls; S-B is genuinely mixed.
- "Was the fix stateable" is judged from the reviewer's own fix text where present. Where the
  reviewer proposed no fix, I inferred one — a weaker basis.
- **This classification should be re-run by a clean context before it is used to authorise or
  cancel a migration.**
