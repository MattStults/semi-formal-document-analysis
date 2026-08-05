# IMPLIED-EFFECTS LAYER — human-approved judgement calls, separately tracked (DRAFT for review)

Status: **DRAFT — design only, nothing implemented.** Author: session coordinator
(Qwen Code), 2026-08-04, from the design discussion with Matt Stults. Provenance:
this is the sibling effort `S3B_REDESIGN.md` ruling (b) hands m0239 to. It is a DESIGN
for review, not a build.

---

## 0. Why this exists

The tool's purpose is to let a practitioner understand the **coverage and contradiction**
of an arbitrarily specified behaviour against a stable text (a model spec, a
constitution). Those texts carry **implied meaning that is not explicit in the text**.
A coverage tool that reads only the literal text will under-report, and practitioners
will notice — they will give feedback that a match or a contradiction "doesn't work as
expected." This layer is where that implied meaning lives, **once a human has approved
it.**

The driver case is **m0239** (harm-avoidance-to-third-parties): the clause de-escalates
a user's radicalization; every gloss is user-focused; no span names a third party. Yet an
auditor of third-party harm reasonably expects it to be covered, because de-escalating a
potential extremist **protects future victims**. `S3B_REDESIGN.md` ruling (b) held that
strict document-grounded attribution cannot license that third party
(`briefs/backfill_author.md` rule 3 forbids inferring an affected party from subject
matter; m0236 precedent), so m0239 is not an S3b restoration — it is the **first member
of this layer**: a human-approved, provenance-logged judgement that the tool reads, never
infers at query time.

---

## 1. Design principles (the converged position)

1. **Separate, droppable, provenance-logged.** Implied effects live in their own
   artifact, never merged into the text-grounded translation. Dropping the layer returns
   the tool to its explicit-only behaviour. Every entry records who/what identified it and
   who approved it, for audit.
2. **Droppability is DEBUGGABILITY, not second-class status.** Implied effects are
   load-bearing for *accuracy* (implied meaning is part of the document's meaning, so the
   accurate representation includes it). The separate layer exists so you can (a) trace
   which conclusions came from text vs judgement, and (b) compute the **explicit-only
   counterfactual** ("what would the tool say with all judgement calls switched off?").
3. **Deterministic, because the tool READS judgement, it does not PERFORM it.** An implied
   effect is a judgement made once, offline, human-approved, and logged as a fixed fact.
   Given the artifact, same input → same output. An explanation may legitimately contain
   "beneficiary inferred by X on 2026-08-04" and remain fully reproducible. This is the
   difference from a frontier judge, which infers fresh on every call.
4. **Unified accurate output by default; differentiation is a debugging feature.** The
   tool produces its best accurate representation of the document; the text-vs-judgement
   split is available via introspection for the (audit) cases that need it. Most users
   never have to care.
5. **Approval is PANEL-BLIND.** This is the highest-risk surface in the project for
   panel-fitting, because it is judgement. The approver sees the clause text and the
   proposed implication — never panel verdicts, judge ratings, gold values, or flip
   outcomes. An implied effect justified by "the panel said this should match" is a
   laundering path, not an annotation, and is refused.
6. **Behaviour-agnostic.** An implied effect is a property of a clause/atom (m0239
   protects third parties), not of any one query. The approval may be *surfaced* by a
   behaviour's feedback, but the recorded effect is clause-scoped, preserving the
   annotation-is-behaviour-agnostic invariant.

---

## 2. The representation — how a human-approved implied annotation relates to the
##    semi-formal translations

This is the core of the design.

### 2.1 Two annotation layers, one key space

* **The semi-formal translation** (`annotations_ext_v1_merged.json` and its grammar,
  `grammar.py`) is the TEXT-GROUNDED layer: each clause → atoms; each atom has a name, a
  kind, a gloss, a verbatim quote, and (where the clause names both an actor and a party
  acted on) an agent-first principal chain `[agent, recipient]`. Every entry is backed by
  a span of the text. **This layer is immutable with respect to the implied layer: the
  implied layer never edits it.**
* **The implied-effects artifact** (`annotations_implied_vN.json`) is the
  JUDGEMENT-GROUNDED layer: a set of human-approved effects that EXTEND the translation
  with semantic content the text does not literally carry. It is a separate, versioned,
  droppable file.

The relationship is **complementary and keyed, not merged**. Each implied effect attaches
to an existing atom (or clause) of the translation by `(clause_id, atom_name)`; the
validator requires the key to resolve against the translation. The implied layer does not
create new atoms and does not alter existing ones — it annotates them further.

### 2.2 Why a separate field, not another chain

The tempting shortcut is to encode an implied beneficiary as an extra chain on the atom
(e.g. `[model, third_party]` for m0239's de-escalation act). **Rejected.** The chain
grammar means "the agent ACTS UPON the recipient"; the implied beneficiary is not a
recipient of the act (the model de-escalates the *user*, and that *protects* third
parties). Reusing the chain would (a) misrepresent the grammar's defined semantics, (b)
make the translation no longer purely text-grounded, and (c) merge judgement into the very
artifact we need to be able to drop. Implied content therefore gets its own typed field.

### 2.3 Entry schema (illustrative)

```json
{
  "id": "imp-0001",
  "key": { "clause_id": "m0239",
           "atom_name": "should_deescalate_extremist_involvement" },
  "effect_type": "beneficiary",
  "polarity": "protective",
  "patients": ["third_party"],
  "provenance": {
    "approval_mode": "manual",
    "identified_by": "<seat / practitioner-feedback id / process>",
    "approved_by": "<human approver>",
    "approved_date": "2026-08-04",
    "rationale": "De-escalating a user's radicalization prevents extremist violence;
                   the protected parties are potential victims, not the user addressed.",
    "reviewed_examples": ["m0239"]
  },
  "status": "active",
  "lifecycle": [
    { "event": "proposed", "date": "…", "actor": "…", "note": "…" },
    { "event": "approved", "date": "…", "actor": "…", "note": "manual review" }
  ]
}
```

* `effect_type` is TYPED and extensible. v1 ships `beneficiary` (an act's protective or
  harmful effect falls on a party not named — the m0239 shape). Later types may include
  `scope` (a generic noun comprehends principals) and `contradiction` (two clauses
  implicitly conflict). Type-specific validation rides with each type.
* `polarity` distinguishes protective from harmful effect (who the clause shields vs who
  it exposes).
* `patients` are members of `grammar.PRINCIPALS`, same vocabulary as declared query
  patients, so the pricing can compose them.
* `provenance` is the audit record. `approval_mode` is `manual` or
  `signature:<signature_id>` (§4). `reviewed_examples` names the clauses actually looked
  at (for a signature approval, the sampled exemplars).
* `status` + `lifecycle` give the full per-entry history, including revocation (§4.4).

### 2.4 Composition at query time

The pricing's view of "who this atom is relevant to" becomes:

```
relevant_patients(atom) = translation_patients(atom)          # chains, text-grounded
                          ∪ implied_patients(atom)             # only when the layer is ON
```

* **Layer OFF (the default):** `implied_patients = ∅`; the tool is bit-for-bit identical
  to the text-only behaviour (invariant I-imp1 below). This is the explicit-only
  counterfactual, available at any time for debugging.
* **Layer ON:** for each atom with `active` implied effects, their `patients` join the
  atom's relevant set. A query patient that matches an **implied** patient is credited
  exactly as a text-grounded match would be, BUT the explain trail records that the match
  came via `imp-<id>` (which resolves to the full provenance). This is what makes the
  judgement visible and auditable in the output.

Because the composition is a pure read of a fixed artifact, determinism is preserved:
the "beneficiary inferred by X on Y date" is data, not a runtime inference.

---

## 3. Invariants pre-registered for the layer

* **I-imp1 opt-in bit-identity.** Implied layer absent or OFF ⇒ the tool reproduces the
  text-only behaviour bit-for-bit. Pinned by test (same pattern as patient pricing I1 and
  join_version v1-default). This is what makes the layer droppable and the explicit-only
  counterfactual real.
* **I-imp2 determinism.** Given a fixed implied artifact and a fixed query, the output is
  fixed. The layer performs no inference at query time.
* **I-imp3 translation immutability.** The implied layer never writes to the translation
  artifact; it only keys into it. Validator: every `key` resolves; no entry redefines an
  atom.
* **I-imp4 panel-blind approval.** Approval inputs exclude panel verdicts, judge ratings,
  gold values, and flip outcomes; enforced the same way the attribution fence is
  (`test_no_reference_leak.py` FORBIDDEN scan + standalone brief). Violation = refused as
  contamination.
* **I-imp5 behaviour-agnostic.** An entry is clause/atom-scoped, never behaviour-scoped.

---

## 4. Review workflow — manual by default, signature-batch when justified, made to be broken

The approval gate is the integrity-critical component: once implied effects are
load-bearing for accuracy, this gate is the only thing keeping them trustworthy.

### 4.1 Default: manual review
Each proposed implied effect is reviewed individually by a human; approve or reject, with
rationale; logged with `approval_mode: manual`. This is the rule.

### 4.2 Breakable rule: signature-based batch approval
When many implied effects share a **mechanically recognizable signature** (a pattern over
the translation that reliably predicts the implication — e.g. "model-protective act whose
harm averts onto unspecified others"), reviewing each of a large number individually is
*less* meaningful than careful review of the signature plus representative examples. In
that case:
1. Define the signature precisely (the predicate over the translation).
2. Carefully review a stratified sample of exemplars against the signature.
3. Approve the CLASS; each matching entry is recorded with
   `approval_mode: signature:<signature_id>` and the `reviewed_examples` that grounded it.

The signature itself is a reviewed, versioned artifact (it is itself a judgement and must
be auditable). This rule is **made to be broken when it improves data quality** — the
choice of manual vs signature for a given batch is itself logged.

### 4.3 Automation is a later, higher-bar decision (count-first, §5)
If the count is large and signatures do not cover it, automating proposal generation may
become attractive. That is a DIFFERENT, riskier system (judgement at scale, adjacent to
panel-fitting) and is NOT part of this design. If it is ever built it needs golden-
validated accuracy, the panel-blind fence, and a high bar to switch on. Treat it as out
of scope until manual + signature are demonstrably insufficient.

### 4.4 Lifecycle and revocation
`status` transitions: `proposed → under_review → active` (approved) or `rejected`; and
`active → revoked` (later judged wrong) or `superseded`. Every transition is appended to
`lifecycle` (event, date, actor, note). **Revocation drops a single entry**, not just the
whole layer — a wrong approved effect is removable on its own, and the explain trail then
no longer cites it. Revocation changes the artifact, hence the output; that is a new
artifact version, not a violation of determinism.

---

## 5. Count-first

Before building, **enumerate** how many implied effects the target texts need (and how
they cluster):
* **Small, scattered** → manual review for all (the ideal; §4.1).
* **Many under shared signatures** → signature-batch approval (§4.2).
* **Many with no signature structure** → this is the warning that the layer may not scale
  per-entry; revisit scope before considering automation (§4.3).

The count also decides whether per-entry provenance is a manageable curation surface. This
step mirrors `S3B_REDESIGN.md` §7.5's expected-recovery estimate, and the two should be
run together: S3b sizes the strict-attribution reach, this sizes the implied remainder.

---

## 6. Reporting and debuggability

* **Default output:** the unified, as-accurate-as-possible representation (principle 4).
  The practitioner sees coverage/contradiction, not a lecture about provenance.
* **Introspection (debugging tools):** for any conclusion, the explain trail distinguishes
  text-grounded matches from implied ones and names the `imp-<id>` (→ full provenance).
  A "why did this match?" view and an **explicit-only counterfactual** toggle (I-imp1) are
  the two core debugging affordances. This is the audit path for anyone who needs to know
  whether a conclusion rests on a judgement call.

---

## 7. Interaction with the measurement/evaluation discipline

* **Version seam.** The implied layer is an opt-in artifact with a version key
  (`implied_version`), exactly like `pricing_version` / `join_version`. Any measurement
  run records whether the layer was ON and which artifact version, in its config identity.
* **DEV stamping / census.** Numbers computed with the layer ON are reported as such; the
  census and any checkpoint declare the implied artifact in their config identity (F2).
* **Frozen evaluations.** For the sealed generalization/constitution evaluations, the
  implied artifact is either EXCLUDED (frozen OFF) or byte-frozen at the G-freeze
  artifact. It must never drift under a frozen pipeline.

---

## 8. Open questions / decision points

* **E1 — clause-level vs atom-level.** v1 keys effects to atoms (m0239). Does any real
  case need clause-level effects (no atom is the carrier)? Decide from the count, not
  speculation.
* **E2 — union vs precedence in composition.** §2.4 unions implied patients with
  translation patients. Is there a case where an implied effect should OVERRIDE the text
  (e.g. correct a known-wrong chain) rather than extend it? If so that is a rechain, not
  an implied effect — keep the layers honest.
* **E3 — promotion.** Can a long-standing, well-supported implied effect ever be promoted
  into the translation (becoming text-grounded via a rechain), or is it permanently a
  judgement? Leaning: it stays an implied effect unless the text itself is amended; a
  promotion path needs its own ruling.
* **E4 — contradiction type.** `effect_type: contradiction` (two clauses implicitly
  conflict) is a different shape from `beneficiary`. Is it in scope for this layer or a
  sibling? v1 ships `beneficiary` only.

---

## 9. What this document deliberately does NOT do

* It does not implement anything; `annotations_implied_vN.json` does not exist yet.
* It does not let the tool infer at query time. All judgement is offline, human-approved,
  and logged before the tool ever reads it.
* It does not automate approval (deferred, §4.3).
* It does not modify the semi-formal translation or the annotation pipeline.
* It does not restore m0239 by itself — it provides the mechanism; m0239 is the first
  proposed entry, subject to §4 approval like any other.

— DRAFT; awaiting adversarial review.
