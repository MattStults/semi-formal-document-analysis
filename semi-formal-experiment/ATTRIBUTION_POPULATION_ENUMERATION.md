# ATTRIBUTION POPULATION ENUMERATION — S3b harm-bearer attribution (D5 count-first step)

Status: **READ-ONLY enumeration, no attribution performed, nothing implemented.**
Prepared for the D1 build-vs-backfill ruling (`S3B_REDESIGN.md` §5.2, §8/D5): the size of
the harm-bearer attribution population is an input to annotation-side-backfill (a) vs
index-side-seat (b), and must be enumerated BEFORE that ruling. This document is the
count-first step §8/D5 mandates. Date: 2026-08-04. Enumeration script:
`/tmp/enum_attribution_population.py` (ephemeral; complete predicates and the full script
are reproduced below — the enumeration is deterministic re-analysis of data already on
disk, zero API spend).

---

## 0. Headline counts

| # | quantity | instances | distinct names | distinct clauses |
|---|---|---|---|---|
| **(a)** | **patient-bearing atoms — FIRM FLOOR** (chain length ≥ 2) | **368** | 183 | 253 |
| (b-trim) | patient-free harm-describing CANDIDATES (recommended predicate, §2.3) | 71 | 34 | 70 |
| (b-core) | same, core keyword list only (lower band) | 59 | 30 | 58 |
| (b-wide) | same, all patient-free situation atoms (upper band, no keyword filter) | 378 | 186 | 321 |
| **(c)** | **total candidate population** = (a)+(b-trim) — recommended | **439** | 217 | 275 |
| (c) | total, lower band = (a)+(b-core) | 427 | — | — |
| (c) | total, upper band = (a)+(b-wide) | 746 | — | 408 |

**Reading (§5): LARGE.** The firm floor alone (368) already exceeds the number of chains
S2's full-cycle backfill actually landed (264), and the recommended population (439) is
~63% of S2's candidate count (692) — which was a full-cycle, four-seat effort. This is
not a small manual backfill.

---

## 1. Inputs and unit of enumeration

* **Artifact:** `annotations_ext_v1_merged.json` (gpt-5.6-luna, run `s0-c24c4c05`,
  2026-08-03). Cross-checked: `atoms` list = 1,442 instances = Σ `by_clause` sizes, over
  exactly 589 clauses; **0 duplicate (name, clause_id) pairs**; 688 distinct names.
  Provenance caveat (carried from the artifact's own `warnings`): 2 of 102 extraction
  batches hit the model output cap and contributed zero atoms — counts are over what
  merged.
* **Unit:** the atom INSTANCE (an element of `atoms`, i.e. a (name, clause_id) pair with
  its own gloss and quote). Attribution is per instance, not per name, because the same
  stem can bear different harm-bearers in different clauses (e.g. `harmful_instructions`
  occurs in 6 clauses, `risky_situation` in 8).
* **Grammar:** `grammar.py` `parse_name`. Chains are agent-first; patients = `chain[1:]`
  for length ≥ 2; a length-1 chain records only the agent and carries NO patient.
  All 1,442 names parse with **0 errors**. Chain-length distribution over the artifact:
  no chain 1,069 · length 1: 5 · length 2: 362 · length 3: 5 · length 4: 1.

## 2. Exact predicates

### 2.1 Predicate A (firm floor) — patient-bearing

`A(atom) := len(parse_name(name).principals) >= 2`

**Result: 368 instances, 183 names, 253 clauses.** Structural facts:

* **ALL 368 are kind `act`.** Chains in this artifact were written only on act atoms —
  which is precisely why the patient-free harm-describing class (§2.2) is concentrated in
  the situation atoms.
* chain lengths: 2 → 362, 3 → 5, 4 → 1.
* recorded patients (`chain[1:]` joined): **user 337** · third_party 18 · model 6 ·
  user_developer 3 · user_third_party 2 · system_developer_user 1 · developer 1.
  (91.6% of recorded recipients are `user` — the provenance defect of S3 is structural
  here: the population whose recorded recipient would be refined into a harm-bearer is
  overwhelmingly user-recipient.)
* agents (`chain[0]`): model 358 · user 5 · developer 3 · root 1 · system 1.

### 2.2 Predicate B (candidate band) — patient-free harm-describing

Patient-free means `len(principals) < 2` (includes the 5 agent-only length-1 chains).
The patient-free remainder is 1,074 instances: act 433 · **situation 378** · entity 202 ·
value 61.

"Harm-describing" is partly judgmental, so B is reported as a BAND under explicit,
stated predicates:

* **B-wide (upper band, judgment-free):** `patient_free AND kind == "situation"`.
  → **378 instances, 186 names, 321 clauses.** Rationale: §3/§4A of the design locate the
  patient-free harm-describing class in the situation atoms (`expressed_harmful_intent`,
  `imminent_bodily_harm`, `harmful_instructions` are all patient-free situation atoms).
  Patient-free entity atoms (party names) and value atoms do not describe harms and are
  excluded; patient-free act atoms are outside §5.1's target (sensitivity check §3.3).
* **B-core (lower band):** B-wide AND (name+gloss matches a CORE keyword stem, §2.4).
  → **59 instances, 30 names, 58 clauses.**
* **B-ext:** B-wide AND (name+gloss matches CORE+EXT keyword stems, §2.4).
  → 77 instances, 38 names, 76 clauses.
* **B-trim (recommended headline):** B-ext minus four audited false-positive names
  (§2.5) → **71 instances, 34 names, 70 clauses.**

### 2.3 Recommended candidate predicate (headline b)

`B-trim(atom) := len(principals) < 2 AND kind == "situation"
                AND keyword_match(name + gloss, CORE+EXT)
                AND name NOT IN FP_NAMES`

### 2.4 Keyword stems (case-insensitive substring on name + " " + gloss)

* **HARM:** harm, hurt, injur, suffer, kill, death, violence, violent, abuse, weapon,
  terror, radicaliz, extremis, victim
* **RISK:** risk, danger, threat, unsafe
* **VICTIMIZATION:** exploit, manipulat, coerci, intimidat, harass, fraud, decei,
  decept, discriminat, violat, disempower, oppress
* **BENEFIT:** benefit, wellbeing, well-being, welfare, flourish
* **EXT additions** (added after a gloss-level audit of the B-wide misses found clear
  harm-describing situations the CORE stems did not reach): distress, sexual, illicit,
  private, mania, manic, drug, dissatisfaction, misrepresent. Each EXT stem captured
  exactly its intended target(s): emotional_distress ×5, sexual_content_involving_minors
  ×4, user_requests_private_information ×2, body_dissatisfaction ×2, mania_signs ×1,
  developer_lie_instruction ×1, drug_use_question ×1, user_indicates_illicit_intent ×1,
  plus one further instance of user_requests_illicit_help (m0270).

### 2.5 Audited false positives (FP_NAMES, removed in B-trim)

Matched a keyword but whose gloss does NOT describe a harm/risk/benefit-to-a-party
situation: `positive_user_intent` (×3; gloss "constructive rather than harmful purpose"
— the keyword hit is a negation), `instructions_intended_low_risk` (×1; "pose little
risk"), `scope_inadequate_for_task` (×1; "would benefit from a broader scope" — task
scope, not a party's benefit), `user_prosocial_preferences` (×1; the user's values, not a
harm situation). Removed: 6 instances. Borderline cases KEPT and flagged for the eventual
attribution seat: `conflict_of_interest`, `model_behavior_scope_limit` (its gloss names a
"harmful-use issue"), `mental_health_topic`, `against_user_best_interest`.

### 2.6 Residual judgment (the wide/narrow gap)

The 148 B-wide names NOT matched by any keyword are mostly non-harm situations
(instruction conflicts, uncertainty states, formatting requests, conversation mechanics).
The gloss audit found the clear harm-describing misses and EXT captured them (§2.4);
residual borderline cases remain (e.g. `bad_surprises`, `significant_real_world_consequences`,
`irreversible_actions`, `legal_insider_trading`, `buggy_code`) — cost/risk-adjacent
situations a future attribution seat may or may not license. This residual judgment is
why (b) is a candidate band [59 … 378], not a point claim; the recommended point inside
it is 71.

## 3. Breakdown (requirement d)

### 3.1 By kind — full artifact vs population

| kind | all instances | (a) patient-bearing | patient-free | (b-trim) candidates |
|---|---|---|---|---|
| act | 801 | **368** | 433 | 0 (by predicate; see §3.3) |
| situation | 378 | 0 | 378 | **71** |
| entity | 202 | 0 | 202 | 0 |
| value | 61 | 0 | 61 | 0 |
| **total** | **1,442** | **368** | **1,074** | **71** |

### 3.2 Chained vs patient-free

* Chained with patient (length ≥ 2): **368** instances — all in population (a).
* Chained agent-only (length 1): 5 instances — patient-free, none is a `situation`, so 0
  in (b).
* Unchained: 1,069 instances, of which 378 are situations → the (b) pool.

### 3.3 Distinct clause counts and overlap

* Clauses with ≥ 1 patient-bearing atom: **253** of 589 (43.0%).
* Clauses with ≥ 1 (b-trim) candidate: **70** (11.9%).
* Clauses in the recommended population (a ∪ b-trim): **275** (46.7%).
  Overlap — clauses containing BOTH a patient-bearing atom and a candidate situation
  atom: **48**. (These are exactly the clause shape §4A taint-inheritance fires on:
  a harm-describing situation atom beside a user-directed remedial act — e.g. m0275,
  m0276, m0239; verified below.)
* Upper band: a ∪ b-wide covers 408 clauses (69.3%).
* Sensitivity — patient-free ACT atoms matching the keyword predicate: 41 instances,
  26 names, 38 clauses (e.g. `prevent_serious_harm`, `shouldnot_facilitate_critical_harms`,
  `should_prevent_imminent_harm`). These are OUTSIDE §5.1's stated target; if the
  designer ever extends attribution to patient-free acts, add ~41.

### 3.4 Cross-check against the design's canonical cases

The enumeration reproduces the §3/§4A clause shapes from atom data alone:

| clause | patient-free situation | patient-bearing sibling(s) | design role |
|---|---|---|---|
| m0275 | `expressed_harmful_intent` (b-trim ✓) | `should_provide_supportive_response__model_user` | RESTORE, in core |
| m0276 | `imminent_bodily_harm` (b-trim ✓) | `mustnot_enable_self_harm__model_user` + 2 more, all `__model_user` | canonical removal, must stay suppressed |
| m0108 | `harmful_instructions` (b-trim ✓) | (contested case) | contested, not counted |
| m0239 | `user_vulnerability_to_radicalization` (b-trim ✓) | `should_deescalate_extremist_involvement__model_user` | demoted to IMPLIED-EFFECTS by ruling (b) |

Note: m0239's atoms are IN the enumerated population even though ruling (b) demoted the
case from the falsifiable core — the population is defined structurally, not by flip
outcomes (labels direct attention, never truth).

## 4. Assumptions

1. Instances, not names, are the attribution unit (§1); the artifact has no duplicate
   (name, clause_id) pairs, so instance = distinct (atom, clause) attribution target.
2. "Patient-free" includes agent-only length-1 chains (grammar: they record no patient).
3. All patient-bearing atoms in this artifact are `act`s (measured, not assumed); the
   design's "patient-free harm-describing" class therefore lives in situation atoms, and
   B is restricted to kind `situation` with patient-free acts reported only as
   sensitivity (§3.3).
4. Keyword matching is a mechanical CANDIDATE screen, not an adjudication: the band
   [59 … 378] brackets the judgment, the recommended point is 71, and the eventual
   attribution seat licenses each item with a verbatim quote (§5.1) — `unclear`/empty is
   a legal verdict and would simply leave an atom on pricing branch 1.
5. No harm-bearer has been attributed anywhere in this document. Enumeration only.

## 5. Small-vs-large reading (input to D1)

**Scale reference (S3B_REDESIGN.md §8/D5):** S2's backfill was a full-cycle, four-seat
effort — 692 candidates, 264 chains landed.

**Measured comparison:**

| | instances | vs S2 |
|---|---|---|
| firm floor (a) | 368 | 53% of S2's 692 candidates; **140% of S2's 264 landed chains** |
| recommended (a)+(b-trim) | 439 | 63% of S2's candidates |
| upper band (a)+(b-wide) | 746 | 108% of S2's candidates |

**Reading: LARGE — the harm-bearer attribution is a full-cycle-scale effort, not a small
manual backfill.** Three points:

1. Even the mechanical floor (368) is already larger than what S2's four-seat cycle
   actually landed, and every item in the population needs the same discipline S2's did —
   panel-blind, document-grounded, verbatim `license_quote`, golden review (§5.1, §8/D5) —
   so per-item cost is non-trivial. The wide band (746) would exceed S2 outright.
2. Manual per-item review is FEASIBLE only as a properly-staffed annotation cycle
   (D1 option (a)), not as a quick backfill; and the (b) component is judgment-heavy —
   the keyword screen needed an audit pass that found both false positives and false
   negatives, and a residual borderline set remains (§2.6). If the attribution were done
   manually, expect S2-like attrition between candidates and licensed attributions.
3. This materially narrows the cost advantage of D1 option (a) annotation-side backfill:
   its main selling point was "proven S2 machinery," but the machinery's cost is now
   measured at S2 scale. D1 option (b), the index-side seat, becomes comparatively more
   attractive — its per-item judgment cost is the same, without the full annotation-cycle
   overhead — at the price §5.2(b) names (a judgment seat in the index path, needing its
   own brief and parity check). The ruling belongs to the designer; this enumeration only
   supplies the size.

One structural mitigation worth recording (not a recommendation): 337 of the 368
patient-bearing instances have recorded recipient `user`, and the design's own
discipline (§5.1, m0236 precedent) forbids inferring harm-bearers from subject matter —
so a future scoping ruling could shrink the population by mechanical default rules (e.g.
attribute only where the clause text names a party), at the cost of leaving more atoms on
pricing branch 1. Any such scoping is a design decision, not an enumeration one.

---

## Appendix A — (b-trim) candidate atom names (34)

instances × name (keyword hit):

* 8 × `risky_situation` (danger, harm, risk)
* 6 × `harmful_instructions` (harm)
* 6 × `targeted_political_manipulation` (exploit, manipulat)
* 5 × `emotional_distress` (distress)
* 4 × `critical_high_severity_harms` (abuse, danger, harm, terror, violence, weapon)
* 4 × `sexual_content_involving_minors` (sexual)
* 3 × `imminent_bodily_harm` (death, harm, injur, risk)
* 3 × `user_requests_harmful_advice` (harm)
* 2 × `body_dissatisfaction` (dissatisfaction) · 2 × `dual_use_information` (harm) ·
  2 × `significant_unapproved_risks` (risk) · 2 × `user_requests_extremist_propaganda`
  (extremis) · 2 × `user_requests_illicit_help` (illicit) · 2 ×
  `user_requests_private_information` (private)
* 1 each: `against_user_best_interest`, `conflict_of_interest`, `dangerous_challenge`,
  `developer_lie_instruction`, `drug_use_question`, `explicit_abuse_instruction`,
  `expressed_harmful_intent`, `human_misuse`, `human_rights_violation`,
  `legal_reputational_harm`, `mania_signs`, `mental_health_topic`,
  `model_behavior_scope_limit`, `non_actionable_harmful_mention`, `serious_safety_concerns`,
  `suicide_ideation`, `suspected_gas_leak`, `user_indicates_illicit_intent`,
  `user_interest_in_extremist_cause`, `user_vulnerability_to_radicalization`

## Appendix B — enumeration script (deterministic, re-runnable)

Run from `semi-formal-experiment/` with the project interpreter; reads
`annotations_ext_v1_merged.json` and `grammar.py` only.

```python
import json, sys
from collections import Counter
sys.path.insert(0, ".")          # semi-formal-experiment/
import grammar

data = json.load(open("annotations_ext_v1_merged.json"))
atoms = data["atoms"]

CORE = ["harm","hurt","injur","suffer","kill","death","violence","violent","abuse",
        "weapon","terror","radicaliz","extremis","victim",                # HARM
        "risk","danger","threat","unsafe",                                # RISK
        "exploit","manipulat","coerci","intimidat","harass","fraud",
        "decei","decept","discriminat","violat","disempower","oppress",   # VICTIMIZATION
        "benefit","wellbeing","well-being","welfare","flourish"]          # BENEFIT
EXT = CORE + ["distress","sexual","illicit","private","mania","manic",
              "drug","dissatisfaction","misrepresent"]
FP_NAMES = {"positive_user_intent","instructions_intended_low_risk",
            "scope_inadequate_for_task","user_prosocial_preferences"}

def chain(a):
    p = grammar.parse_name(a["name"]); assert not p["error"], p
    return p["principals"]

def hit(a, stems):
    t = (a["name"] + " " + a["gloss"]).lower()
    return any(k in t for k in stems)

pb = [a for a in atoms if len(chain(a)) >= 2]              # (a) firm floor
pf = [a for a in atoms if len(chain(a)) < 2]
pf_sit    = [a for a in pf if a["kind"] == "situation"]     # (b) wide
b_ext     = [a for a in pf_sit if hit(a, EXT)]
b_trim    = [a for a in b_ext if a["name"] not in FP_NAMES] # (b) recommended
b_core    = [a for a in pf_sit if hit(a, CORE)]

for label, xs in [("a patient-bearing", pb), ("b wide", pf_sit),
                  ("b core", b_core), ("b ext", b_ext), ("b trim", b_trim)]:
    print(f"{label:20s} instances={len(xs):4d} names={len({a['name'] for a in xs}):3d}"
          f" clauses={len({a['clause_id'] for a in xs}):3d}")
print("total recommended (a)+(b-trim):", len(pb) + len(b_trim))
print("total upper     (a)+(b-wide):", len(pb) + len(pf_sit))
```

— End of enumeration. No attribution performed; D1 ruling still open.
