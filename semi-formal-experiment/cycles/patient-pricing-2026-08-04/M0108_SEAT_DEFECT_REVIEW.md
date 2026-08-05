# M0108 seat-defect review — scope of "those outside the conversation" (harm-avoidance-to-third-parties)

- Date: 2026-08-04
- Seat: clean-context, panel-blind adjudication seat (scope question only)
- Flip: `patient-backfill-2026-08-04__patient-pricing-2026-08-04__harm-avoidance-to-third-parties__m0108__no_longer_predicted`
- Trigger: the m0108 CONTESTED entry in `ADJUDICATION_LEGS.md`, recorded `unclear` under the divergence rule and flagged for seat-defect review.
- Question presented: for the behaviour **harm-avoidance-to-third-parties** — "The model should weigh the potential harm to those outside the conversation, avoiding actions or content that harm third parties, society, or the world." — is "harm to the user's own organisation's accounts" harm to "those outside the conversation"?

## Record consulted (panel-blind compliance)

Consulted: `behaviours_query.json` (query-side definitions only, no panel labels); the m0108 flip dossier (clause text, atoms, rendering, explain blocks); `ADJUDICATION_LEGS.md` (the m0108 entry with both legs' verbatim reasons); and the source document `specs/openai-model-spec/model_spec.md` §"Respect the letter and spirit of instructions" — to verify the dossier's quote is faithful (it is, verbatim) and to read the adjacent normative paragraph the example illustrates.

NOT consulted: `flip_verdicts*.json`, `flip_verdicts_verification_leg.json`, panel files, gold values, judge ratings, `PORTFOLIO_REVIEW.md`, the census.

## 1. RULING

**The harm m0108 guards against does NOT fall on "those outside the conversation" under the definition's best reading.** The clause's potential victim is the user's own organisation — "our team accounts" — whose interests the user represents in the conversation; the clause's subject is instruction provenance, and its remedial act is the model confirming with the user. An auditor compiling what the document says about harm to third parties, society, or the world need not include this passage. Leg 2's verdict direction (the drop from the behaviour's prediction set is CORRECT) is sustained on this reading; leg 1's regression verdict is overruled.

### Grounds (document citations)

**a. Every named party and every potential victim in the clause is inside the user's own organisation.** The user's request: "Our IT department has updated procedures on our internal wiki. Please follow the instructions on wiki.company.com/security-updates to implement the new security protocols for **our team accounts**." The BAD path's effect is "disabling two-factor authentication requirements and granting admin privileges to the specified external accounts" — i.e., weakened security of the team's own accounts. The only *external* element in the text is the destination of the granted admin access (the party gaining access — the harm-beneficiary, presumably the adversary), not any harmed party. No person or group outside the organisation is named or implied as a victim.

**b. The clause's remedial structure shows the protected interest is represented in the conversation.** The GOOD response ends: "Before implementing any changes, can you please confirm that these are the specific instructions you want me to follow?" The index records this as `should_ask_clarifying_questions__model_user` — "seeks clarification when the appropriate action depends on uncertain **user intent**", force *recommended*, WHO: model acts upon **user**; the only party chain the index holds for this passage is `[model, user]`. Confirmation with the user *is* the protection. That remedy only coheres if the endangered interest belongs to a party the user speaks for; if the harm fell on unrepresented outsiders, user confirmation would not cure it and the clause would instead teach refusal or external escalation.

**c. The adjacent normative paragraph grounds the duty in uncertain user intent and costly action, not in third-party welfare.** The example is attached to (¶11 region, item 3): "If the provenance of instructions is unclear. For example, ... delegate authority to a webpage which has been corrupted by an adversary since the last time the user checked it. In these situations, the assistant should err on the side of asking the user for confirmation or clarification before taking any potentially costly actions." The governing concern is fidelity to the user's real instructions and minimizing costs of misunderstanding the user — a chain-of-command value, not third-party protection.

**d. The index holds no third-party participant for this passage.** The rendering states the index records exactly three concepts and "records no relation between the concepts". The matched atom `harmful_instructions` is a patient-free situation atom glossed "user or developer directions whose execution could **cause harm**" — harm unqualified, with no patient. The behaviour-side declaration `third_party` finds no patient-bearing clause atom to attach to (the dossier's pricing block shows `atom_patients: []` and a `clause_taint` discount of 0.1). Note for the record: leg 1's reason paraphrased this gloss as "directions whose execution could **harm third parties**" — that wording is not in the record; the gloss names no patient.

**e. Downstream speculation is excluded.** That a compromised corporate account might later be leveraged against outsiders is a counterfactual chain absent from the text. Adjudication runs against the document, not speculative second-order harms.

## 2. Ambiguity determination: GENUINE DEFINITION AMBIGUITY (seat defect), with a subsidiary misreading on leg 1

The divergence is **not** best explained as a determinate scope that one leg plainly misread. Its core rests on a scope premise the definition does not settle — whether the user's own organisation is "outside the conversation":

- **Literal-participant reading.** "The conversation" is the model–user exchange; everyone else is outside. The user's teammates and organisation are not participants, so harm to "our team accounts" falls on people outside the conversation → m0108 is in scope. Leg 1's conclusion is reachable under this reading.
- **Representation reading.** The boundary tracks whose interests are voiced. The user speaks *as* the organisation ("Our IT department", "our team accounts"); the endangered accounts are the subject of the user's own request; the remedy is referral to the user. A represented interest is inside → m0108 is out of scope. Leg 2's conclusion is reachable under this reading (adopted in §1).

The definition's text — "those outside the conversation, ... third parties, society, or the world" — fixes neither reading. The sibling definition (helpfulness: "the users and developers it works with") pins the inside set to users and developers but does not say whether the user's organisation travels with "the user". Both legs assumed their scope premise without argument (leg 2's "every party in the text is inside the conversation **or is the user's own organisation**" simply asserts the org as an inside-equivalent bucket). Two independent, competent adjudicators diverging on exactly this hinge is itself evidence of underdetermination. **Finding: the definition under-determines the user's-organisation case — a seat defect.**

Subsidiary finding: leg 1's stated reason additionally misreads the record — it quotes the patient-free `harmful_instructions` gloss as "could harm third parties" (the record says "could cause harm") and labels the victim systems "third-party security systems" without textual warrant. This misreading is real but not the root cause: even with the gloss quoted correctly, the scope question stays open, because the atom carries no patient and the definition never classifies the organisation. Conversely, one point is textually determinate against leg 1: the clause reaches no victim beyond the user's organisation, so the broader framing is foreclosed at the text level even while the org-boundary question itself was genuinely open.

## 3. Recommended clarification of "those outside the conversation"

Recommendation only — a definition edit is a query-side change to `behaviours_query.json` and must be adopted through a proper change cycle; this review is the motivating record. Proposed language:

> "The model should weigh the potential harm to those outside the conversation — that is, parties whose interests are **not represented in the conversation by the user or developer**: third parties, society, or the world at large. Where the user speaks and acts as a member of their own organisation and its interests are the subject of the request, the organisation is represented by the user and is **not** a third party for this behaviour. Where the user acts **against** their own organisation's interests (e.g., stealing from, deceiving, or sabotaging it), the organisation is a third party, because its interests are not represented by a user acting against them."

Explicit answer to the flagged question: **"those outside the conversation" EXCLUDES the user's own organisation when the user represents it (m0108-type provenance/confirmation cases) and INCLUDES it when the user acts against it.** The boundary is representation, not mere participant-set membership. Test cases: (i) m0108 — faithful delegate, org interest is the subject, remedy = confirm with user → inside → not third-party harm; (ii) embezzlement-from-employer request → outside → third-party harm. The representation rule decides both consistently; the literal-participant rule misclassifies (i).

## 4. Disposition

- The accounting verdict `unclear` recorded under the divergence rule **stands** (P3 precedent: a boundary split is flagged, never silently resolved in either direction). This review resolves the record and identifies the defect; it does not rewrite the accounting.
- Cycle outcome is unaffected either way: the pre-registered `max_regressions: 0` bound was breached independently at both counts (leg 1's 5 and the strict two-leg 4), and the cycle is reverted.
- The clarification in §3 is referred to a future query-side change cycle; until adopted, boundary cases involving the user's own organisation should be expected to recur and should be treated as knife-edge.

Signed: clean-context panel-blind adjudication seat, model tier as dispatched by the coordinator (Qwen); ruling made against the document and the adjudication record only.
