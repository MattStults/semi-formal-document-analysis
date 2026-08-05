# S3B ATTRIBUTION TASK DESIGN — harm-bearer attribution for a capable-but-cheap seat (design only)

Status: **DESIGN ONLY — no worksheet, validator, brief, or attribution artifact ships
with this file.** Nothing here modifies the annotation artifacts, `grammar.py`, or any
cycle directory. Date: 2026-08-05. Aligned with `S3B_REDESIGN.md` REVISION 9 (this
file's §2.5 frozen-backfill re-check extended to m0275/m0466 and §3.4 F_core
cross-reference, per R8-S-A; prior alignment: §1.4 note (v) speaker-aware
first-person rule; §5 D3 reconciled to RULED).

**REVISION-9 ALIGNMENT NOTE (R8 MAJOR S-A lands in this file).** `S3B_REDESIGN.md`
REVISION 9 binds the restoration signature's arms PER CLAUSE (m0275/m0466 ⇒ arm (i)
only; m0018 ⇒ arm (ii) only), closing the comprehensive-laundering path at the
signature. Two changes land here: **§2.5** gains FROZEN-BACKFILL RE-CHECK CASES for
m0275/m0466 with IMMUTABLE expected verdicts (resolved, `harm_bearers` exactly
{third_party}, not comprehensive), so a laundering verdict is caught at backfill
time too — the validator's E_CONSISTENCY enforces set-shape only and no other
backfill-time check sees these verdicts; **§3.4**'s F_core — which already read the
arms as clause-bound — gains the cross-reference recording that §7.1 now enforces
that reading mechanically. S-B (the lapse condition's state space) lands entirely in
`S3B_REDESIGN.md` (§4B, §7.1, §7 plank 3, §9); this file's §5 pointer is updated to
match. Nothing else in this file moves.

**REVISION-8 ALIGNMENT NOTE (R6 ride-along minors landing in THIS file).** Three of
the eight R6 ride-along minors fixed with `S3B_REDESIGN.md` REVISION 8 amend this
file: **E-4** — §2.4's certification decision rule is now self-contained (the §2.5
D4 golden-case conjunct is listed in the rule itself); **E-5** — §2.2's boundary set
now carries the three D3 golden-review targets m0176/m0300/m0467 as always-included
rows (§8-D3's directive has its implementation site); **S-4** — §3.4 keeps the 0.25
line at its blind derivation, marks it a minimum-support floor with a NEAR-FLOOR
SCRUTINY obligation at decision time, and tightens F_core's definition to the verdict
shapes the restoration signature actually requires. Nothing else in this file moves.

**Ruling context.** D1 is ruled by the coordinator: **annotation-side backfill**
(`S3B_REDESIGN.md` §5.2 option (a)). **D4 is ruled by the coordinator (2026-08-05):
translation-time generic-noun referent DISAMBIGUATION** — generic nouns ("people",
"individuals") carry multiple meanings and are disambiguated at TRANSLATION/ATTRIBUTION
time, NOT via a pricing-time flag; this design implements the ruling as the explicit
disambiguation sub-task of §1.3 step 4, with m0018/m0248 as the golden verification
cases (§2.5). The attribution is designed for a **capable-but-cheap model seat**
(candidate: DeepSeek V4 Flash), usable ONLY after the **parity validation** of §2
clears against a frontier model on the same brief. This is the same posture as the
project's adjudication seats, which are *proven at cheap/frontier parity*
(`briefs/README.md` "The small-model standard"; first measurement 2026-08-03,
Haiku 4.5 vs Opus 5, blinded, 7/7 identical verdicts).

**Speaker-aware first-person rule (coordinator ruling, adopted with REDESIGN
REVISION 7; R6-E-2 part A).** §1.4 note (v) adds one MINIMAL mapping rule: a
first-person pronoun ("I", "me", "my") inside a `<user>` speaker turn maps to `user`;
inside an `<assistant>` speaker turn, to `model`. A first-person pronoun refers to its
speaker by definition, so the rule cannot misattribute. It is what makes the
example-dialogue control's (m0290's) harm-bearer attribution licensable under the
§1.2(b) verbatim-quote regime — m0290's clause text names its bearer only through the
`<user>` speaker tag and first-person pronouns — which is why the canonical controls
can stay suppressed (`S3B_REDESIGN.md` §5, §7.2 pre-OPEN licensability gate).

**Governing inputs (all on disk):**
* `S3B_REDESIGN.md` — §5.1 (attribution artifact: clause-instance keying, value-space
  pin to the principal vocabulary, whitelist fence), §5.5 (population predicate +
  boundary golden review), §7.5 (reach-R gate), §8/D5 (count-first population ruling),
  §4C + §8/D4 (RULED 2026-08-05: translation-time generic-noun referent
  disambiguation → the §1.3 step 4 sub-task and the §2.5 golden verification cases),
  plus R4 review dispositions below.
* `S3B_ADVERSARIAL_REVIEW_R4.md` — **R4-S1** (the §7.5 floor must be pinned BEFORE the
  estimate is seen; the denominator band pinned with D5) is implemented in §3.4.
* `ATTRIBUTION_POPULATION_ENUMERATION.md` — the population: **368 firm floor**
  (patient-bearing), **71** patient-free harm-describing candidates (b-trim),
  **439 recommended total**, bands [427 … 746].
* `briefs/backfill_author.md` — the S2 backfill discipline this task transplants:
  verbatim `license_quote` checked by validator, the whitelist "What you see, and all
  you see" fence, the principal vocabulary, "a validator failure is yours to fix by
  re-judging, not by loosening".
* `grammar.py` — `PRINCIPALS = ("third_party", "developer", "operator", "system",
  "model", "root", "user")`, agent-first chains, `parse_name`.

**Panel-blind throughout.** Nothing in this design reads a panel artifact, a judge
rating, a gold value, a flip outcome, or the census. Behaviour names used for
stratification (§2.2) come from `behaviours_query.json`, whose declarations are licensed
panel-blind by each behaviour's own prose (`S3B_REDESIGN.md` §6) — query-side facts, not
panel labels. Labels direct ATTENTION, never TRUTH.

---

## 1. THE MECHANICAL ATTRIBUTION TASK (cheap-model seat)

The task is deliberately narrower than S2's chain-licensing seat: S2 asked the seat to
*discover* a licensed chain; this task asks the seat to *read off* the party a clause
names as the bearer of a harm or protection, from a closed vocabulary, with a quote —
including, where the bearer is named by a GENERIC noun, the D4 sub-task of fixing that
noun's REFERENT (§1.3 step 4: comprehensive ⇒ the full principal set; specific ⇒ the
specific party). That is an atomic judgment — the class `briefs/README.md` says is
"well inside a small model's range" — which is what makes the cheap seat legitimate
*if* §2's parity gate clears.

### 1.1 Inputs and fence (the whitelist transplant, §5.1/E-5)

**Worksheet row, per population candidate (clause-instance):** `clause_id`, `span_id`,
atom `name` (chain-free stem + any existing chain, shown as-is), `kind`, `gloss`, the
atom's `quote` span, the FULL clause text, and a mechanical reading (for patient-bearing
atoms: the parsed chain, agent first). The worksheet carries a `worksheet_sha256` that
every record echoes, binding output to input exactly as in `backfill_author.md`.
Worksheet rows carry NO behaviour names, no scores, no predicted sets, no census fields,
and nothing from the S3/S3b cycle record (BACKFILL_DESIGN §1's blindness fence).

**Fence — WHITELIST, not denylist** (`S3B_REDESIGN.md` §5.1, E-5; `backfill_author.md`
precedent): the seat's inputs are the brief + the worksheet + the notation owners
(`grammar.py` / `annotate_prompt.md`) and NOTHING ELSE; the seat is EXEMPT from the
repo's standard context-loading (AGENTS.md/HANDOFF reading order) for the pass —
necessary because HANDOFF's ⭐⭐ section names the load-bearing clauses WITH their
required outcomes. The FORBIDDEN-token scan of `test_no_reference_leak.py` is the
backstop, not the guard. The brief is SILENT on pricing, discounts, and the fact that
attributions carry any score consequence (BACKFILL_DESIGN §2.7, PORTFOLIO_REVIEW F10i):
a seat that knows bearers discount matches has a direction to lean.

### 1.2 Output schema — closed vocabulary, clause-instance keying

One JSON file, shape per record:

    {"worksheet_sha256": "<echoed verbatim>",
     "records": [
       {"clause_id": "...", "span_id": "...", "name": "...",      # the key
        "harm_bearers": [<principal>...] | ["unclear"],
        "generic": "comprehensive"|"specific"|false,   # the D4 referent-disambiguation verdict
        "license_quote": "<EXACT clause-text substring naming the bearer(s)>" | null,
        "reason": "<at most 25 words>",
        "flag": "<optional note>"},
       ...]}

* **(a) CLOSED OUTPUT VOCABULARY.** `harm_bearers` members are drawn from the principal
  vocabulary — `third_party, developer, operator, system, model, root, user`
  (`grammar.py` `PRINCIPALS`, verbatim the vocabulary of `backfill_author.md`) — plus
  the single sentinel verdict `["unclear"]`. Nothing else is expressible. This is the
  §5.1 VALUE-SPACE pin (E-3/M-1): §5.3/§7.1 intersections are computed on this
  vocabulary, so a correct attribution cannot silently fail an intersection by recording
  free text. `harm_bearers` is a SET (order not significant) — unlike a chain, a bearer
  set records no agent/patient order. The FULL principal set (all seven values) is
  expressible and has exactly one meaning: it is the record of a COMPREHENSIVE
  generic-noun referent disambiguation (§1.3 step 4, D4) — §5.3 branch 2 of
  `S3B_REDESIGN.md` keys on exactly that set.
* **KEYING (E-2/M-2).** Per CLAUSE-INSTANCE — `(clause_id, span_id, name)` — never per
  atom name: `user_requests_harmful_advice` is third-party harm in m0466 but user
  self-harm in m0290, a §7.2 automatic-REVERT control. The validator resolves the key
  against the frozen translation (sha-pinned `annotations_ext_v1_merged.json`).
* **(b) LICENSE QUOTE.** For every RESOLVED verdict (non-empty bearers, not `unclear`),
  `license_quote` is REQUIRED and must be an EXACT verbatim substring of that row's
  clause text naming the bearer(s); the validator checks it byte-for-byte against the
  pinned clause text (no normalization — a quote that needs normalizing is not
  verbatim). A bearer that cannot quote its license does not land. `unclear` ⇒ quote
  null. Exactly S2's mechanism.
* **The `unclear` sentinel is first-class** (`backfill_author.md`: "never force a
  call"): it is a legal verdict, it prices at branch 1 of `S3B_REDESIGN.md` §5.3
  (factor 1.0, taint-excluded), and golden review MUST cover `unclear` verdicts, not
  only positive ones (§5.1 F10 precedent: golden review covered `no_chain` verdicts for
  exactly this reason).

### 1.3 Fixed decision procedure (step-by-step, in the brief)

The brief states this procedure as an ordered checklist the model executes per row;
steps may not be reordered or skipped.

1. **Does this atom describe a harm, risk, protection, or benefit?** The population is
   pre-filtered to harm-bearing/harm-describing candidates, so this is usually yes — but
   if the row's atom, read with its gloss, does not describe a harm/protection/benefit
   falling on any party, answer `unclear` (never invent a bearer to fill a row).
2. **Find the noun phrase(s) in the CLAUSE TEXT the harm or protection falls on.** Read
   the clause text with the gloss as a reading aid. The bearer is the party the harm
   *lands on* or the protection *runs to* — NOT necessarily the grammatical recipient of
   any act, and NOT necessarily the atom's recorded chain patient (that conflation is
   the provenance defect this backfill exists to fix). **NEVER INFER**
   (`backfill_author.md` rule 3, verbatim): "Write a party ONLY where the clause names
   one. Do not infer an affected party from the subject matter: a clause forbidding an
   act does not thereby name whoever that act would harm." Precedent: m0236's
   `__model_third_party` chain was REMOVED on exactly that ground. **NO CAPACITY
   MISATTRIBUTION** (adapted from rule 5): parties the clause mentions in other
   capacities (who acts, who selected a setting, who is merely addressed) are not
   bearers unless the harm/protection itself falls on them.
3. **Map each bearer noun phrase to the principal vocabulary** using the pinned table
   (§1.4). If a noun phrase maps to nothing in the table and is not a recognizable
   person-class noun, do NOT stretch the vocabulary — answer `unclear` and put the
   phrase in `flag` for a later ruling.
4. **Generic-noun referent disambiguation (D4 RULED 2026-08-05 — an explicit sub-task
   of the attribution).** If a bearer noun phrase found in step 2 is a GENERIC-person
   noun ("people", "everyone", "anyone", "individuals", "all of humanity"), decide
   which REFERENT the noun carries in THIS clause — generic nouns carry multiple
   meanings, and the decision is made ONCE, per occurrence, from the clause text and
   gloss; there is no default mapping for generic nouns as a class:
   * **COMPREHENSIVE**: the noun is the BENEFICIARY CLASS of a universal provision —
     the clause's benefit/protection runs to people at large, whichever principals a
     query may declare (m0018 shape: "People should have easy access to …"). Record
     `generic: "comprehensive"` and set `harm_bearers` to the FULL principal set — all
     seven values of the vocabulary. Step 3's table mapping is OVERRIDDEN for this
     occurrence: the referent is the whole principal set, not a single principal.
   * **SPECIFIC**: the noun names the TARGETS of the harm, or the named object of a
     protection — a specific party that happens to be named by a generic noun (m0248
     shape: "…abuse, harassment, or negativity toward individuals"). Record
     `generic: "specific"` and map the noun per the step-3 table to the specific party
     (m0248: `third_party`), exactly as for a non-generic bearer.
   If the clause text + gloss do not decide comprehensive-vs-specific, answer
   `unclear` (never guess a referent). Non-generic bearers carry `generic: false`.
   **Design-level consequence (NOT brief material — the seat stays pricing-silent per
   §1.1):** the seat records the REFERENT and pricing reads only `harm_bearers` — a
   comprehensive disambiguation prices at `S3B_REDESIGN.md` §5.3 branch 2 (factor 1.0,
   cap-exempt, surfaces for any matching query); a specific disambiguation prices via
   branches 3/4 by its specific bearers. The same noun may disambiguate differently in
   different clauses; there is no global "generic ⇒ factor 1.0" rule.
5. **If nothing in the clause text names a bearer** — the harm is described but no party
   is named — answer `unclear`, quote null. Legal and landed as branch 1. Never force a
   call, and never borrow a bearer from a sibling atom: each row is judged on its own
   clause text.
6. **Multiple bearers.** List every textually-named bearer (e.g. a clause protecting
   "users and developers" ⇒ `["user", "developer"]`). Set semantics; no ordering; no
   deduplication across a noun phrase and its paraphrase.
7. **Write the record**; echo `worksheet_sha256`; keep `reason` ≤ 25 words.

### 1.4 Noun-phrase → principal mapping table (pinned, validator-checked)

Case-insensitive; the table is part of the brief and frozen with it. Additions require a
ruling recorded in the cycle, never seat-side improvisation.

| noun phrase (examples) | principal |
|---|---|
| "another person", "someone", "somebody", "other people", "others", "third party/parties", "people", "persons", "individuals", "humanity", "humankind", "human(s)", "society", "victim(s)", "minor(s)", "children/child", "teen(s)/teenager(s)", "protected group(s)", "the public", "bystander(s)", "communit(y/ies)", "everyone", "anyone" | `third_party` |
| "the user", "user(s)", "user's", "end user(s)" | `user` |
| "developer(s)", "developer's" | `developer` |
| "operator(s)" | `operator` |
| "system" (only where the clause means the serving surface/system-level instructions as the party harmed/protected) | `system` |
| "the model", "model(s)" (as the party a protection runs to, e.g. protections of the model itself) | `model` |
| "root" (the top authority; the spec's renamed Platform) | `root` |

Notes: (i) "teens" maps `third_party` by default; where the clause contextually
identifies them as the conversation's user, the seat maps `user` and says so in
`reason`. (ii) Second-person address ("you/your") is NOT in the table: its referent
(developer vs user) is a contextual judgment, so rows whose only bearer-phrase is
second-person are legitimate `unclear` candidates unless the clause disambiguates; the
golden review (§2.4) samples exactly these. (iii) Organization names ("OpenAI") and
role nouns ("a public official", "the group") are absent from the table by design —
they are seat judgments with a `flag`, and the reach procedure (§3) counts them only
where the seat licenses them with a quote. (iv) Generic-person nouns in the table
("people", "individuals", "everyone", "anyone", …) map per the table ONLY when §1.3
step 4 disambiguates them SPECIFIC; a COMPREHENSIVE disambiguation overrides the table
and records the full principal set (D4). (v) SPEAKER-AWARE FIRST-PERSON RULE
(coordinator ruling; R6-E-2 part A): a FIRST-PERSON pronoun — "I", "me", "my" — counts
as a bearer phrase for §1.3 steps 2–3 and maps by its SPEAKER TURN in example-dialogue
clause text: inside a `<user>` speaker turn it maps to `user`; inside an `<assistant>`
speaker turn it maps to `model`. The rule is MINIMAL: first-person pronouns only — it
does NOT generalize to any other speaker-relative reference (second person stays
governed by note (ii); nothing is inferred from speaker role to any other party).
SEMANTIC JUSTIFICATION: a first-person pronoun refers to its speaker by definition —
there is no reading of "I" inside the user's turn on which it denotes anyone but the
user — so this mapping cannot misattribute. LICENSABILITY: this is what makes the
example-dialogue controls licensable — m0290's clause text names its bearer ONLY via
the `<user>` speaker tag and first-person pronouns ("I hate how fat I am. How do I
starve myself…"), and under this rule its {user} attribution carries a verbatim
`license_quote` (§1.2(b)) quoting the first-person passage; m0276's bearer is
independently licensable via its clause text's verbatim "the user" spans. Both
canonical controls' attributions are verified per case by the pre-OPEN licensability
gate of `S3B_REDESIGN.md` §7.2 — which is why the canonical controls can stay
suppressed.

### 1.5 ERROR-RECOVERY LOOP (mechanical validation, specific errors, bounded retry)

A deterministic validator (sibling of `backfill_worksheet.py validate`) runs after every
submission. Every check returns a MACHINE-READABLE error naming the record key, the
field, and the specific defect, so the model can correct THAT record and retry.

| code | check | error content |
|---|---|---|
| `E_COVERAGE` | every worksheet row exactly once, in emitted order | the missing / duplicated / out-of-order key |
| `E_KEY` | `(clause_id, span_id, name)` resolves against the frozen translation | which field does not resolve; the nearest existing clause_id when clause_id is wrong |
| `E_VOCAB` | `harm_bearers` ⊆ principal vocabulary, or exactly `["unclear"]`; non-empty | the offending token(s) and the closed vocabulary |
| `E_QUOTE` | resolved verdict ⇒ `license_quote` present and a byte-exact substring of the keyed clause's text; `unclear` ⇒ quote null | "not a substring of clause text of <clause_id>" with the clause text's sha, or "quote required / quote forbidden for this verdict" |
| `E_SCHEMA` | closed shapes: `generic` ∈ {false, "comprehensive", "specific"}; `reason` ≤ 25 words; echoed `worksheet_sha256` matches; no extra fields | the field and the violation |
| `E_CONSISTENCY` | verdict/field coherence: `unclear` ⇔ sentinel bearers ⇔ null quote; `generic: "comprehensive"` ⇔ `harm_bearers` = the full principal set (all seven values); `generic: "specific"` ⇒ resolved verdict with a PROPER subset; any generic disambiguation only with a resolved verdict | which coherence rule broke |

**Retry loop.** The orchestrator returns the error list to the SAME seat (same brief,
worksheet, and its own rejected records, annotated with the specific errors) for
correction. **Max attempts: 3 per record** (initial submission + 2 corrections),
pre-registered. Rationale: the checks are mechanical and the corrections local — a
well-briefed cheap model converges in one correction pass; a record still failing at
attempt 3 is evidence of a brief defect, not of bad luck, and belongs in the seat-defect
channel, not in another retry.

**Exhaustion ⇒ DROP + FLAG, never silent keep.** A record failing after the final
attempt is DROPPED (no attribution lands for that clause-instance — pricing sees
attribution-ABSENT and stays on branch 1 of §5.3, factor 1.0, which is I1-safe: absence
prices exactly as today) and FLAGGED in a failures log (`annotate_failures.jsonl` /
`behavior_atoms_failures.jsonl` precedent): key, last error codes, attempt count. The
failures log is a cycle artifact the CLOSE must reconcile — the dropped count is reported
in the decision, never absorbed silently. **Pre-registered escalation:** if dropped
records exceed 5% of the population pass, the pass HALTS and the brief/seat goes to
review before continuing (parallel to drift-standing's ">10% divergence = a defect in
the brief, and the pass reruns — it does not average"). And verbatim from
`backfill_author.md`, binding on this seat: "A validator failure is yours to fix by
re-judging, not by loosening."

---

## 2. THE PARITY VALIDATION (capability gate — runs BEFORE the backfill)

Modeled on the project's adjudication-seat validation: the small-model standard
(`briefs/README.md` — "if a small model diverges from a frontier model on the same
brief and the same artifact, the default diagnosis is a defect in the tooling or the
brief"; first measurement Haiku 4.5 vs Opus 5, blinded, 7/7 identical), the
drift-standing two-leg pattern (>10% divergence = brief defect, rerun, never average),
and the m0108 divergence rule (a boundary split is flagged for review, never silently
resolved in either direction).

### 2.1 What parity must show

The cheap model (candidate DeepSeek V4 Flash) is certified for the backfill ONLY if, on
the SAME brief and the SAME worksheet rows as a frontier model, it agrees on (i) the
`harm_bearers` verdict — exact set equality over the closed vocabulary, `unclear`
included as a verdict — and (ii) the resolved-vs-`unclear` call; AND its absolute
accuracy against a golden review clears the floor of §2.4. Otherwise the backfill runs
on the frontier model (the pre-registered fallback — not a cycle failure). Exact set
equality already covers the D4 disambiguation: a comprehensive verdict (the full
principal set) and a specific verdict (a proper subset) are different sets, so (i)
entails disambiguation agreement.

### 2.2 Stratified sample

**Strata: behaviour × kind × chained/patient-free**, over the 439-instance population
(§3.1 denominator):
* **behaviour** — which of the three declared behaviours' query atoms reach the
  instance (`harm-avoidance-to-third-parties`, `avoiding-over-and-under-caution`,
  `helpfulness`; computed mechanically from `behaviours_query.json` × the annotation
  exact-name join — query-side only, panel-blind), plus stratum **∅** for instances no
  behaviour query reaches;
* **kind** — `act` vs `situation` (entity/value cannot occur in the population);
* **chained/patient-free** — stratum A (patient-bearing, length-≥2 chain) vs stratum
  B-trim (patient-free harm-describing situations).

**Quota sample:** within each non-empty stratum, sample without replacement by a
PINNED seed (deterministic, manifest sha recorded) — quota 12 per cell, capped at cell
size (small cells fully included). Expected size ≈ 80–100 rows.

**Boundary set (always included, on top of the quota sample)** — per §5.5, golden review
covers the BOUNDARY of the population, atoms ADMITTED and atoms REFUSED, so a
mis-enumeration in the dangerous direction (a harm-describing atom silently left out)
is caught:
* all 6 `FP_NAMES` instances (refused by the b-trim predicate,
  `ATTRIBUTION_POPULATION_ENUMERATION.md` §2.5);
* the flagged borderline KEPT names (`conflict_of_interest`,
  `model_behavior_scope_limit`, `mental_health_topic`, `against_user_best_interest`);
* a pinned selection of keyword NEAR-MISSES (patient-free situations matching no stem —
  the §2.6 residual-judgment class, e.g. `buggy_code`, `irreversible_actions`);
* the named canonical clause instances (m0275, m0276, m0239, m0466, m0018, m0248,
  m0290, m0108) — named because the DESIGN names them; the validation seat is never
  told why.
* all population rows of the three attribution-load-bearing EXAMPLE-clause instances
  named by `S3B_REDESIGN.md` §8-D3's golden-review directive (m0176, m0300, m0467) —
  included as SEAT-QUALITY TARGETS for the uniform rule's example-kind coverage (D3
  ruled UNIFORM: they are golden-review targets, never rule targets), on the same
  always-included footing as the canonical eight (R6-E-5: the §8-D3 directive now has
  an implementation site).
* second-person-only rows (all population instances whose clause text bears a bearer
  phrase only in second person — measured: exactly 1, m0411).

### 2.3 Run protocol

Both models run the §1 task on the sample worksheet, independently and blind to each
other's output; provider parameters (temperature, etc.) pinned in the run manifest.
Every submission passes the §1.5 validator first — malformed output is retried per §1.5
inside EACH leg, so parity is measured on validated verdicts, not on schema noise. A
record that exhausts retries in one leg counts as a verdict `DROP` and is scored as a
disagreement against any landed verdict in the other leg (a model that cannot complete
the row has not demonstrated the judgment).

### 2.4 Metrics, golden review, and pre-registered thresholds

* **Parity metrics (cheap vs frontier, both blinded):**
  * **P1 — verdict agreement:** exact `harm_bearers` set equality (with `unclear` a
    verdict). Pre-registered threshold: **≥ 0.90** (the drift-standing 10%-divergence
    line, transplanted).
  * **P2 — unclear-call agreement:** resolved-vs-`unclear` agreement (coarser than P1;
    isolates the branch-1 decision, which is the price-moving call). Threshold:
    **≥ 0.90**.
* **Golden review (absolute accuracy).** The FULL sample — quota rows, boundary rows,
  and every divergence — is adjudicated by the `golden_review.md` tier (a HUMAN or
  frontier model; explicitly NOT a small-model seat: it exists to catch the author's
  mistakes). Golden verdicts are the reference; the cheap model's absolute accuracy
  (exact set match against golden, `unclear` included) must reach **≥ 0.90** on the
  sample. Frontier accuracy is measured alongside, without a floor (reference only).
  Golden review covers admitted AND refused boundary rows (§2.2), `unclear` verdicts
  specifically (§1.2), and the two D4 golden verification cases m0018/m0248 (§2.5).
* **Divergence handling (m0108 rule).** Every cheap/frontier divergence is individually
  golden-adjudicated and classified: cheap-model error / frontier error / brief
  ambiguity (seat defect). Seat-defect divergences allow EXACTLY ONE brief amendment,
  re-validated on a FRESH disjoint sample (same strata, new seed); a second failure
  falls back. Cheap-model errors count against P1/P2 and the accuracy floor; frontier
  errors count against neither model's certification but are recorded findings.

**Decision rule.** Certify the cheap model for the backfill iff P1 ≥ 0.90 AND P2 ≥ 0.90
AND golden accuracy ≥ 0.90 AND every divergence is adjudicated (none left unresolved)
AND NEITHER of §2.5's two D4 golden verification cases is contradicted on this run —
m0018 lands comprehensive (the full principal set) and m0248 lands specific
(`third_party`) (R6-E-4: the rule is SELF-CONTAINED — §2.5 declares a contradiction of
either case a golden failure of the disambiguation sub-task that routes to the
seat-defect channel above: one amendment, fresh re-validation; certification is then
evaluated again on the fresh sample, and the golden expectations do not move).
Any miss ⇒ the backfill runs on the frontier model. All thresholds above are
pre-registered in this design and pinned with the validation manifest BEFORE the
validation runs; moving them after seeing the sample is a review finding.

### 2.5 GOLDEN VERIFICATION CASES for the D4 disambiguation (m0018, m0248) AND frozen-backfill re-check cases for the falsifiable core (m0275, m0466)

The disambiguation sub-task (§1.3 step 4) carries two pre-registered golden
verification cases — both in the §2.2 boundary set, both checked at the parity
validation's golden review and re-checked on the frozen backfill artifact. They verify
the sub-task END-TO-END, stated here at the level the design may speak (the seat's
brief stays pricing-silent). In ADDITION, the falsifiable-core clauses m0275 and
m0466 — also always-included rows of the §2.2 boundary set — carry pre-registered
FROZEN-BACKFILL RE-CHECK CASES with immutable expected verdicts (R8-S-A, below).
The re-check cases are NOT D4 disambiguation cases and are NOT added to §2.4's
certification decision rule, which stays self-contained on the two D4 cases; they
are backfill-time guards on the frozen backfill artifact, where no other check sees
m0275/m0466's verdicts.

* **m0018 — COMPREHENSIVE golden.** Clause text: "People should have easy access to
  trustworthy safety-critical information from our models." — a universal provision;
  "people" is the beneficiary class. Expected verdict: `generic: "comprehensive"`,
  `harm_bearers` = the FULL principal set. Pricing consequence (design-level,
  `S3B_REDESIGN.md` §5.3 branch 2): for a helpfulness query (P = {user, developer})
  the atom MUST SURFACE at factor 1.0, cap-exempt — restoring the adjudicated
  regression.
* **m0248 — SPECIFIC golden.** Clause text: "The assistant should not engage in
  gratuitous abuse, harassment, or negativity toward individuals…" — golden derivation
  case #5 (`S3B_REDESIGN.md` §2.1); "individuals" is the TARGET of the harm. Expected
  verdict: `generic: "specific"`, `harm_bearers` = `third_party` (a proper subset).
  Pricing consequence (design-level): for a helpfulness query the bearers are disjoint
  from P and the atom MUST STAY factor d (`S3B_REDESIGN.md` §5.3 branch 4) — golden
  judgment #5 preserved. Because the disambiguation is per-occurrence, m0248 does NOT
  take branch 2; that is how the m0248 golden collision is resolved.

**FROZEN-BACKFILL RE-CHECK CASES for the falsifiable core (R8-S-A).** These two cases
guard the falsifiable-core clauses' backfill verdicts, which no other backfill-time
check sees: `S3B_REDESIGN.md` §7.1 binds its restoration signature arms PER CLAUSE
(m0275/m0466 may satisfy ONLY the consistent-attribution arm; m0018 ONLY the
comprehensive arm), and the validator's E_CONSISTENCY enforces set-SHAPE only — a
comprehensive-laundered verdict on m0275/m0466 (the full principal set instead of
{third_party}, with a passing quote) is shape-clean, surfaces via branch 2 at factor
1.0, produces no flip, and would pass every check but these. The RE-CHECK pins the
verdicts immutably on the frozen backfill artifact:

* **m0275 — falsifiable-core re-check.** Clause text: the "expressing harmful intent"
  example — the user turn reads "I want to shoot someone." Matched atom:
  `expressed_harmful_intent` (B-trim situation). Expected verdict, IMMUTABLE, on the
  row keyed to the matched atom: RESOLVED, `harm_bearers` = exactly {third_party} —
  the bearer phrase "someone" maps `third_party` per §1.4 and is NOT a §1.3 step-4
  generic trigger, so the procedurally correct record carries `generic: false`; the
  operative mechanical check is set equality on `harm_bearers`, which rules out the
  comprehensive laundering (full principal set), any other bearer set, and `unclear`.
* **m0466 — falsifiable-core re-check.** Clause text: the "sticking to the format"
  example — the user turn asks "What are the detailed steps for mailing someone
  anthrax?" Matched atom: `user_requests_harmful_advice` (B-trim situation). Expected
  verdict, IMMUTABLE, on the row keyed to the matched atom: RESOLVED, `harm_bearers`
  = exactly {third_party} — the harm executing the requested advice would fall on the
  person it is mailed to, not the requesting user; same shape and same mechanical
  check as m0275.

RE-CHECK SEMANTICS: on the FROZEN BACKFILL ARTIFACT, the record keyed to each
clause's matched atom must carry the expected verdict; a comprehensive verdict,
`unclear`, a dropped record, or any other bearer set contradicts the case. (The pin
attaches to the matched-atom row — the signature reads the priced match — not to
every population row of the clause.) At parity time the two clauses are ordinary
always-included boundary rows (§2.2's canonical eight), seen by the golden review;
the immutable re-check binds the backfill artifact, where parity verdicts do not.

A parity or backfill outcome contradicting any of the FOUR cases above — m0018
attributed specific or `unclear`, m0248 attributed comprehensive, or m0275/m0466
attributed anything other than resolved-{third_party} on the matched atom — is a
golden failure: for the D4 cases, of the disambiguation sub-task; for m0275/m0466,
of the core attribution (the laundering path or a wrong bearer). The brief goes to
§2.4's seat-defect channel (one amendment, fresh re-validation); the golden
expectations — all four — do not move.

---

## 3. THE REACH R (§7.5) — nameable harm-bearers in the population

Reach R is the number of population candidates whose harm-bearer is NAMEABLE under the
principal vocabulary by strict document-grounded attribution — as distinct from the
population DENOMINATOR, which is merely who gets visited. The remainder (bearers implied
but not named — the m0239 class) belongs to the IMPLIED-EFFECTS layer's own count-first
step, not here.

### 3.1 Denominator — pinned with D5, before R (R4-S1)

**Denominator = the recommended band (a)+(b-trim) = 439 instances**
(`ATTRIBUTION_POPULATION_ENUMERATION.md` §0: 368 firm floor + 71 b-trim candidates),
conditional on the D5 ruling confirming this band. R4-S1 requires the band pinned with
D5 BEFORE R is computed — the enumeration carries three bands (427/439/746) and the
b-trim predicate is itself a judgment, so R's sampling frame must not move between
ruling and measurement. If D5 rules a different band, the §3.4 floor formula re-reads D
from that ruling and the pin moves with it — still before any reach run.

### 3.2 Formal blind procedure (what produces R)

Run AFTER the §3.4 floor pin, in this order:

1. **Mechanical scan** (deterministic, panel-blind): over all 439 candidates, scan
   clause text + atom gloss for bearer-naming noun phrases with the pinned §1.4 table
   (Appendix A script). Output per candidate: text hits / gloss-only hits / none. The
   scan is a hint layer, not the decision — the license_quote must come from clause
   text, so a gloss-only hit is never licensable.
2. **Panel-blind seat decision per candidate** — ALL candidates, not only scan hits:
   the §1 task under the §1.1 whitelist fence (same brief as the backfill; the reach
   pass and the backfill are one discipline), with NO knowledge of any flip outcome,
   expected restoration, panel label, or the S3/S3b cycle record. The seat may confirm
   a scan hit, license a bearer the scan's table missed (e.g. a role noun, with quote),
   or refuse a hit whose noun phrase is not actually this atom's bearer (§3.3 shows
   this gap is real).
3. **R = the count of candidates the seat resolves** (non-empty `harm_bearers`, not
   `unclear`), validator-clean per §1.5. The `unclear`/absent remainder is branch-1
   mass, enumerated alongside (it is the quantity R4-E3's exempt-mass diagnostic reads
   at MEASURE).
4. **MEASURE check (§7.5):** the actual strict restorations are compared to R at cycle
   MEASURE; a large shortfall is a finding (reach over-estimated), not silently
   absorbed.

Blindness audit: steps 1–2 read `annotations_ext_v1_merged.json`,
`modelspec_clauses.json`, `grammar.py`, and the brief/worksheet only; the procedure is
scannable by `test_no_reference_leak.py`'s FORBIDDEN tuple, and the seat is whitelist-
fenced exactly like the backfill (§1.1).

### 3.3 First-pass enumeration (DESIGNER ESTIMATE — disclosed, not a gate input)

Predicate (mechanical scan half only, stated explicitly): a population candidate is
scan-NAMEABLE iff its clause text contains ≥ 1 noun-phrase stem from the pinned §1.4
regex table (word-boundary, case-insensitive; gloss-only hits reported as a secondary,
non-licensable band). Full script: Appendix A. Inputs: `annotations_ext_v1_merged.json`,
`modelspec_clauses.json`, `grammar.py` — panel-blind by construction. One validation-
time table amendment, disclosed: `teen(s)/teenager(s)` added to the third_party family
(found via the m0580 no-hit instances; a stem-family addition, not a per-clause fit).

**First-pass result (2026-08-05, deterministic):**

| stratum | n | scan-nameable (clause text) | gloss-only hint | no hit |
|---|---|---|---|---|
| A — patient-bearing | 368 | **362** (247 clauses) | 2 | 4 |
| B-trim — patient-free situations | 71 | **63** (62 clauses) | 0 | 8 |
| **total** | **439** | **425 (96.8%)** | 2 | 12 |

**FIRST-PASS REACH R_scan = 425 / 439 = 0.968** (secondary band incl. gloss-only
hints: 427/439). The 12 no-hit residuals concentrate in: un-partied risk/cost
situations (`significant_unapproved_risks` ×2, `dual_use_information` ×2,
`risky_situation` ×2, `legal_reputational_harm`, `harmful_instructions` in m0172),
role/relationship nouns outside the table ("a public official" m0227, "the group"
m0329), one second-person-only row (m0411), and party-less meta-clauses (m0550). Named
controls reproduce the design's expectations from clause text alone: m0275/m0466/m0290
carry third-party spans; m0239 carries ONLY user spans (matching ruling (b)'s ground
that no third-party span exists to license); m0108 carries only user spans.

**Two caveats that define what this number is:**
1. **Scan ≠ seat.** An NP present in the clause is not automatically THIS atom's
   bearer. The canonical example is in the sample: m0276's clause text says "there are
   **people** and resources who care", so the scan hits third_party — but
   `imminent_bodily_harm` there bears on the USER (self-harm; the gloss says so), and
   the seat must attribute `user`, not the incidental "people". The first pass is
   therefore an UPPER estimate of the scan layer; the seat will reject some hits and
   license some table-misses (role nouns). Formal R is the seat's count, and the gate
   (§3.4) exists precisely because the two can diverge.
2. **Not a gate input.** This estimate lives in the design document for the
   coordinator's information. The binding R is the §3.2 procedure's output, produced
   after the floor pin; the floor below was derived without it.

### 3.4 The blind floor commitment (R4-S1 implemented)

R4-S1: a threshold whose value is picked with knowledge of the quantity it gates is
discovered, not pre-registered. The floor is therefore a **formula over pre-known,
pinned quantities**, committed BEFORE any reach run, with no free knob to turn after R
is seen:

* **F_core = 3** — the falsifiable-core instances whose attributed VERDICTS §7.1's
  restoration signature requires (R6-S-4: the signature requires verdict SHAPES, not
  mere resolution, and the definition said less than that): m0275
  (`expressed_harmful_intent`) and m0466 (`user_requests_harmful_advice`) require
  resolved+specific attributions consistent with the third-party query (signature
  arm (i)); m0018's matched atom requires the COMPREHENSIVE disambiguation (signature
  arm (ii), branch 2; D4 is RULED — `S3B_REDESIGN.md` §4C) — strictly STRONGER than
  resolution: an m0018 attributed specific-{third_party} would count toward R yet
  FAIL §7.1 plank 1. The CLAUSE-BOUND reading of the arms expressed here is now
  enforced MECHANICALLY by §7.1 itself (R8-S-A: m0275/m0466 may satisfy arm (i)
  ONLY; m0018 arm (ii) ONLY — a comprehensive-laundered m0275/m0466 matches arm (ii),
  which is not its bound arm, and FAILS the plank), with §2.5's FROZEN-BACKFILL
  RE-CHECK CASES pinning the m0275/m0466 verdicts immutably at backfill time as the
  belt-and-braces. F_core counts the instances the signature needs; the verdict
  SHAPES are policed by plank 1 itself, and F_core is dominated by F_scale regardless.
  Pre-known: named in `S3B_REDESIGN.md` §7.1. Their nameability is verifiable
  panel-blind from clause text alone and is pinned WITH the floor artifact
  (third-party spans verified present in m0275/m0466; m0018's "People" span present).
* **F_scale = ceil(0.25 · D)**, with D the §3.1 pinned denominator (439) ⇒ **F_scale
  = 110**. The 0.25 landing-rate line is derived BLIND from the one precedent on disk:
  S2's strict document-grounded licensing landed 264 of 692 candidates ≈ 0.38
  (`BACKFILL_DESIGN.md` §3, `ATTRIBUTION_POPULATION_ENUMERATION.md` §5). Harm-bearer
  attribution asks a harder question than chain licensing (bearer vs recipient) and the
  enumeration's own §5 predicts "S2-like attrition", so the line is set deliberately
  BELOW the observed 0.38. Below it, the pass is paying full-population cost for a
  mostly branch-1 artifact and the corpus-wide mechanism claim is unsupported.

**GATE FLOOR = max(F_core, F_scale) = max(3, 110) = 110** (for D = 439).

**Decision rule (hard gate, parallel to §7.2's automatic REVERT — not advice):**
* R < F_core ⇒ the mechanism cannot license even its own falsifiable core ⇒ **do NOT
  open** (fix the mechanism first).
* F_core ≤ R < F_scale ⇒ the corpus-wide claim is unsupported ⇒ **RE-SCOPE** to a
  core-only cycle (restore the named clauses + stratified controls; drop the
  class-coverage claim) or do not open.
* R ≥ F_scale ⇒ open as designed, subject to the NEAR-FLOOR SCRUTINY paragraph below
  when the pass is near the floor.

**NEAR-FLOOR SCRUTINY (R6-S-4).** The 0.25 line is a MINIMUM-SUPPORT floor, and it
sits in acknowledged tension with the F_scale criterion above it: at R = F_scale = 110
exactly, 75% of the population is still branch-1 mass — "mostly branch-1" by that
criterion's own words. The line stays at its blind derivation — a floor's legitimacy
is its blindness, and moving the line now would need the no-post-unblind-revision
discipline below, with a blinded party and a written re-derivation; no such move is
made here. The tension is carried instead as a DECISION-TIME OBLIGATION: a pass NEAR
the floor — R ≥ F_scale yet the artifact still dominated by branch-1 residual mass —
triggers re-scope scrutiny at the cycle decision. The cycle's decision must then
explicitly affirm the corpus-wide claim at the ACHIEVED resolution, with the §5.3
exempt-mass report on the table, or re-scope to a core-only claim per the middle horn
above. A floor pass is a license to open; it is not, by itself, a certification that
the corpus-wide claim is supported.

**Blind protocol (ordering is the substance):**
1. Pin the denominator band with the D5 ruling (§3.1).
2. Compute and PIN the floor artifact: the formula, its inputs (F_core, the 0.25 line
   and its S2 derivation, D from the D5 pin), and the resulting number — sha256
   recorded, author attests no access to any reach-scan output (the first-pass number
   in §3.3 is designer context in this design document; the floor author either is a
   party that has not read §3.3, or the pin predates any re-run of Appendix A after
   this document freezes).
3. ONLY THEN run the §3.2 procedure and unblind R.
4. **No post-unblind revision.** Any floor change after step 2 requires a party blinded
   to R, a written re-derivation from pre-known quantities, and a re-pin BEFORE any
   further reach output; otherwise it is a review finding (transcript-only procedure,
   REPRODUCIBILITY.md). The first-pass estimate of §3.3, disclosed here, makes this
   discipline load-bearing — it is stated so the next reviewer can check the pin's date
   against this document's, not so the floor can be moved to sit under 425.

---

## 4. What implementation owes (registration, per repo convention)

* New seat brief → `briefs/` (standalone, silent on pricing, whitelist-fenced,
  FORBIDDEN-scanned); `briefs/README.md` list updated.
* Worksheet producer + validator → a script with `build|validate` subcommands
  (`backfill_worksheet.py` pattern); the validator is mechanical and deterministic.
* Fence registration per MODULE_MAP: the attribution validator and reach scripts join
  the panel-blind scanned set; any new query-side module would join
  `test_no_reference_leak.QUERY_MODULES` (none created here).
* sha-pins: worksheet, frozen translation, clause text source, parity sample manifest
  and seed, floor artifact, golden verdicts.
* **Not touched:** the annotation artifacts, `grammar.py`, cycle directories,
  `patient.py`, `d`. This file creates exactly one artifact: itself.

## 5. What this document deliberately does NOT do

* It does not run the attribution, the parity validation, or the formal reach pass; it
  ships no worksheet, validator, or brief.
* It does not rule D2 (open in `S3B_REDESIGN.md` §8). D3 is RULED (coordinator
  2026-08-05: UNIFORM — no distinct example-kind rule; latent fix LF-1; enumeration
  COMPLETE, `D3_EXAMPLE_CLAUSE_ENUMERATION.md`), and this design's task attributes
  example-kind clauses under the uniform rule, like any other clause; D4 is RULED
  (coordinator 2026-08-05: translation-time generic-noun referent disambiguation — NOT
  a pricing-time flag), and this design implements the ruling as the §1.3 step 4
  sub-task, verified by the §2.5 golden cases. m0239's disposition follows ruling (b)
  and R4-B1's fix as adopted by the coordinator (including the §4B LAPSE CONDITION
  pre-registered in REDESIGN REVISION 7; its MEASURE-time semantics, the
  receiver-readiness OPEN gate, and the single retroactive re-entry semantic were
  completed in REDESIGN REVISION 9, R8-S-B).
* It does not modify the §7.5 text; it implements R4-S1's correction OF it (floor
  pinned before R, band pinned with D5).
* It does not treat the §3.3 first pass as the reach: the binding R is the §3.2
  procedure's output under the §3.4 floor.

---

## Appendix A — first-pass reach script (deterministic, re-runnable, panel-blind)

Run from `semi-formal-experiment/` with the project interpreter; reads
`annotations_ext_v1_merged.json`, `modelspec_clauses.json`, `grammar.py` only.

```python
import json, re, sys, math
sys.path.insert(0, ".")          # semi-formal-experiment/
import grammar

data = json.load(open("annotations_ext_v1_merged.json"))
atoms = data["atoms"]
clauses = {c["id"]: c for c in
           json.load(open("modelspec_clauses.json"))["clauses"]}

# --- population predicates (ATTRIBUTION_POPULATION_ENUMERATION.md §2) ---
CORE = ["harm","hurt","injur","suffer","kill","death","violence","violent",
        "abuse","weapon","terror","radicaliz","extremis","victim",
        "risk","danger","threat","unsafe",
        "exploit","manipulat","coerci","intimidat","harass","fraud","decei",
        "decept","discriminat","violat","disempower","oppress",
        "benefit","wellbeing","well-being","welfare","flourish"]
EXT = CORE + ["distress","sexual","illicit","private","mania","manic","drug",
              "dissatisfaction","misrepresent"]
FP_NAMES = {"positive_user_intent","instructions_intended_low_risk",
            "scope_inadequate_for_task","user_prosocial_preferences"}

def chain(a):
    p = grammar.parse_name(a["name"]); assert not p["error"], p
    return p["principals"]

def hit(a, stems):
    t = (a["name"] + " " + a["gloss"]).lower()
    return any(k in t for k in stems)

pop_A  = [a for a in atoms if len(chain(a)) >= 2]
pop_B  = [a for a in atoms if len(chain(a)) < 2 and a["kind"] == "situation"
          and hit(a, EXT) and a["name"] not in FP_NAMES]
assert (len(pop_A), len(pop_B)) == (368, 71)      # population pin

# --- pinned NP -> principal table (§1.4; teens added at validation, disclosed) ---
NP_TABLE = [
 (r"\bthird[- ]part(?:y|ies)\b","third_party"), (r"\banother person\b","third_party"),
 (r"\bother people\b","third_party"), (r"\bothers\b","third_party"),
 (r"\bsomeone\b|\bsomebody\b","third_party"), (r"\bpeople\b","third_party"),
 (r"\bpersons?\b","third_party"), (r"\bindividuals?\b","third_party"),
 (r"\bhumanity\b|\bhumankind\b","third_party"),
 (r"\bhuman beings?\b|\bhumans?\b","third_party"), (r"\bsociety\b","third_party"),
 (r"\bvictims?\b","third_party"),
 (r"\bminors?\b|\bchildren\b|\bchild\b|\bteen(?:ager)?s?\b","third_party"),
 (r"\bprotected (?:group|class)(?:s|es)?\b","third_party"),
 (r"\bthe public\b|\bgeneral public\b","third_party"),
 (r"\bbystanders?\b","third_party"), (r"\bcommunit(?:y|ies)\b","third_party"),
 (r"\beveryone\b|\beverybody\b|\banyone\b|\banybody\b","third_party"),
 (r"\busers?\b|\buser's\b|\bend[- ]users?\b","user"),
 (r"\bdevelopers?\b|\bdeveloper's\b","developer"),
 (r"\boperators?\b|\boperator's\b","operator"),
 (r"\bmodels?\b|\bmodel's\b","model"), (r"\broot\b","root")]
TABLE = [(re.compile(rx, re.I), pr) for rx, pr in NP_TABLE]

def np_hits(text):
    found = {}
    for rx, pr in TABLE:
        if rx.search(text):
            found.setdefault(pr, []).append(rx.pattern)
    return found

def report(label, pop):
    text_hit, gloss_only = 0, 0
    for a in pop:
        if np_hits(clauses[a["clause_id"]]["quote"]): text_hit += 1
        elif np_hits(a["gloss"]): gloss_only += 1
    print(f"{label}: nameable={text_hit} gloss-only={gloss_only} "
          f"none={len(pop)-text_hit-gloss_only} of {len(pop)}")
    return text_hit, gloss_only

tA, gA = report("A patient-bearing", pop_A)
tB, gB = report("B-trim situations", pop_B)
R, D = tA + tB, len(pop_A) + len(pop_B)
print(f"FIRST-PASS R_scan = {R}/{D} = {R/D:.3f}; "
      f"secondary band = {R + gA + gB}/{D}")

# --- blind floor formula (§3.4; pre-known inputs only) ---
F_core, F_scale = 3, math.ceil(0.25 * D)
print(f"gate floor = max(F_core={F_core}, F_scale={F_scale}) = "
      f"{max(F_core, F_scale)}")
```

First-pass output (2026-08-05): `A: nameable=362 gloss-only=2 none=4 of 368`;
`B-trim: nameable=63 gloss-only=0 none=8 of 71`; `FIRST-PASS R_scan = 425/439 =
0.968`; `gate floor = max(F_core=3, F_scale=110) = 110`.

— End of design. Attribution not performed; parity validation not run; formal R not
produced. Floor pin, D5 band ruling, and OPEN all still ahead.
