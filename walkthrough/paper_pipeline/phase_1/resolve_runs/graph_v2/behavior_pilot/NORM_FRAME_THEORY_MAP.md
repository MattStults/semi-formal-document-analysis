# NORM-FRAME THEORY MAP — grounding the slot inventory in existing theory
(2026-08-24, design tier, Matt's directive: "we are almost certainly not
the first to diagram these — find the existing theory instead of finding
dimensions one by one." STATUS: DRAFT FROM MODEL KNOWLEDGE — the
citations below are standard and old, but this document requires a
literature-verification pass before anything BINDS to it; nothing here
is seat material.)

## 1. The mapping: our empirically-minted slots vs the canonical inventories

| Our slot (how we got it) | Canonical home | Theory source |
|---|---|---|
| force (permit/forbid/prefer/oblige — in the corpus from day 1) | norm CHARACTER | von Wright, Norm and Action (1963), the six norm elements |
| acts / arg_sorts (day 1) | norm CONTENT: the act | von Wright |
| proposed LOCUS ("whose space does the norm operate on" — minted from UA misses) | norm CONTENT: the act's OBJECT | von Wright — the object-place of content; we were re-deriving half a slot |
| contexts / governs_conditional (minted iter-1) | CONDITION OF APPLICATION | von Wright |
| actor (day 1) + the chain of command | AUTHORITY (norm-giver) | von Wright; the spec's instruction hierarchy is an authority ordering |
| (mostly constant: the assistant) | SUBJECT (addressee) | von Wright |
| protects / party (E1-era) | fragments of the CORRELATIVE RELATION | Hohfeld (1913): claim-right/duty, privilege/no-right, power/liability, immunity/disability. User-autonomy IS a Hohfeldian privilege sphere with a correlative duty of non-interference |
| machinery_concern (minted iter-2 from structural exclusion) | CONSTITUTIVE vs REGULATIVE rule | Searle: constitutive rules create the institution (the chain-of-command definitions), regulative rules govern conduct within it |
| ARB (minted iter-3 from tradeoffs) | DEFEASIBILITY / exception structure within a norm | defeasible deontic logic; LegalRuleML's override/exception machinery |
| plumbing / authority_plumbing (frontier-labeled) | meta-norms / promulgation | von Wright's ancillary elements |
| governs qualities (day 1) | the norm's regulated DIMENSION of conduct | closest to legal-drafting "subject-matter" classification; weakest theoretical anchor of our slots |
| purposes (8-addendum) | norm TELEOLOGY / ratio legis | purposive interpretation tradition |

## 2. What the theory predicts that no miss has forced yet (the a-priori gaps)
- G1 CORRELATIVITY, full Hohfeld: we mark who is protected, but not the
  RELATION TYPE (is this the user's claim-right against the assistant, a
  privilege the assistant must not infringe, a power the developer holds,
  an immunity?). Behaviours about autonomy, authority, and consent are
  relation-typed; protects alone conflates them.
- G2 INTER-NORM PRIORITY as a RELATION: ARB marks structure WITHIN a
  claim; the theory individuates priority as a relation BETWEEN norms
  (lex superior — the chain of command; lex specialis — exceptions).
  The spec's hierarchy is a priority graph we currently encode as node
  properties.
- G3 CONSTITUTIVE/REGULATIVE as translation-time annotation: machinery
  is currently a gate; theory says it is a first-class binary every
  assert has.
- G4 DEONTIC vs EPISTEMIC modality: several style-section FPs are norms
  about EPISTEMIC PRESENTATION (hedging, uncertainty) — modal typology
  distinguishes these from conduct norms cleanly.

## 3. The proposal
Derive the NEXT DOCUMENT's translation schema from the completed frame
(von Wright core + Hohfeld relation + constitutive flag + defeasibility
+ modality type), not from accumulated misses. TEST (the kill-criterion,
upgraded): behaviours 3-6 and the next document must be coverable with
ZERO slots outside the theory-derived frame — a stronger and better-
grounded prediction than the empirical curve alone.

## 4. Obligations before use
Literature-verification pass (the table's attributions checked against
sources, not memory); design review; and the frame is SCHEMA for
translation — the calculus's measurement discipline over it is unchanged.


## CORRECTIONS (2026-08-24, append-only — adversarial literature review, web-verified, + spot-check data)
The verification pass CHANGED the table, per the reviewer's verdict
("directionally right, not yet sound"):
- C1 HOHFELD DOCTRINAL ERROR, fixed: a privilege's correlative is a
  NO-RIGHT, not a duty; a duty of non-interference correlates with a
  CLAIM-RIGHT. If the assistant genuinely owes non-interference,
  user-autonomy is a claim-right sphere, not a privilege sphere.
- C2 STRUCK: "locus = von Wright's content object-place" — unsourced;
  the honest homes are ODRL's `target` and frame-semantic roles.
- C3 DEMOTED: ARB is NOT defeasibility (which is an ordered relation
  between norms — LegalRuleML Overrides, Governatori superiority); ARB
  is at most a flag that a clause participates in an unrepresented
  priority structure. CONFIRMED BY DATA: the defeasibility field was
  the only unstable one in the blind spot-check (0.38 vs 0.87-0.97).
- C4 von Wright corrected: EIGHT prescription components with a
  three-element norm-kernel (character, content, condition); no
  "ancillary elements" class; 'prefer' is preference logic, not a
  deontic character.
- C5 COMPARANDA REPLACED: validate against LegalRuleML + ODRL (+ Kanger-
  Lindahl normative positions, Alchourron & Bulygin completeness,
  Sartor 2006, legal-NLP deontic annotation), not 1963 monographs.
- C6 KILL-CRITERION REPLACED per the review: pre-register the CELL
  ASSIGNMENT of every anticipated dimension before behaviours 3-6
  (rhetorical accommodation into a huge union is otherwise
  unfalsifiable).
- C7 SPOT-CHECK VERDICT (CANON_SPOTCHECK_SCORED.json): the canon frame
  is cheaply blind-annotatable (7/8 fields 0.87-0.97) and belongs in
  the a-priori translation schema AS THE FORM LAYER — but NO form field
  separates behaviour-relevance; the separating dimensions are
  content-side (target/locus/topic). Form comes free from theory;
  relevance still requires the content dimensions, now to be designed
  against ODRL/FrameNet rather than minted from misses.
