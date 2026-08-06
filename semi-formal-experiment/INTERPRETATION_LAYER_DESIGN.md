# INTERPRETATION LAYER — making judgement calls visible, citable, and switchable

**Status:** DESIGN, for review. Nothing implemented, no ruling made. Written 2026-08-05.

**The problem in one line:** the tool's claim is that every hit traces to a licensing span
of source text — but interpretations don't trace. They live as prose in cycle records, and
a reader has no way to see which of them a given answer depended on.

---

## 1. What an interpretation is

A question the document under analysis does not settle, which someone had to settle anyway
in order to answer "does this passage bear on behaviour X?".

The canonical instance is **m0108**. The spec's example: a user asks the assistant to follow
instructions on their company wiki, the wiki has been compromised, and the bad path disables
2FA and grants admin access on "our team accounts". Is that harm to *"those outside the
conversation"*?

Two independent, competent adjudicators split on it. The seat-defect review
(`cycles/patient-pricing-2026-08-04/M0108_SEAT_DEFECT_REVIEW.md`) found the definition
genuinely under-determines the case — and settled it, in prose, in a cycle directory. Today
that ruling is invisible to anyone reading the tool's output. A user who would have read the
boundary differently has no way to know a boundary was drawn, let alone where.

**Interpretations are not defects.** Every serious reading of a normative document makes
them. The failure is leaving them implicit.

---

## 2. Two consumers, two different rules

This is the design's central distinction, and it resolves the tension that otherwise sinks
the idea.

### The reader path — users, who legitimately fit to their own needs

Someone auditing a model against this spec has a purpose: a compliance question, an incident,
a policy review. They should be able to see the interpretations in play and **switch them**,
because the right boundary genuinely depends on what they are looking for. A safety team
asking "what does the spec say that bears on data-breach harm to customers?" may well want
the foreseeable-downstream reading that our default excludes.

That is fitting-to-purpose, and it is **fine**. It is what a search tool is for.

### The measurement path — us, where fitting is forbidden

Every number this project reports — MCC against the panel, flip sets, census classes — is
produced under **one opinionated configuration**, frozen, changed only through a cycle. We
do not choose interpretations to improve a metric. That prohibition is the whole reason the
project's constants are sha-pinned and its thresholds frozen.

**The rule that keeps these apart:** a user-toggled view is **not a measured configuration**
and is never a source of a reported number. Our shipped recommendation is a single named
interpretation set; a reader's toggling produces a view, labelled as such.

### Current position

**All interpretations ON**, as the single opinionated recommendation. A future set could be
a mix — an entry we register but do not endorse by default — but nothing today needs that,
and building the machinery for a mix before we have a case is how speculative complexity
gets in (see `LATENT_FIX_REGISTRY.md` for the pattern of registering an idea rather than
building it early).

---

## 3. What an entry looks like

Each interpretation names a question, an **endorsed reading**, and at least one **named
alternative** — because "off" must mean something specific, not merely "don't do that".

```json
{
  "id": "I-01",
  "question": "Is the user's own organisation 'outside the conversation'?",
  "endorsed": {
    "reading": "representation",
    "statement": "Parties whose interests are represented in the conversation by the
                  user or developer are NOT third parties. Where the user acts AGAINST
                  their organisation's interests, the organisation IS a third party,
                  because its interests are not represented by a user acting against
                  them.",
    "mechanics": "<how the tool applies it — a predicate, an atom set, a mapping rule>"
  },
  "alternatives": [
    {"reading": "literal_participant",
     "statement": "The conversation is the model-user exchange; every other party,
                   including the user's own organisation, is outside it.",
     "mechanics": "..."}
  ],
  "grounds": "cycles/patient-pricing-2026-08-04/M0108_SEAT_DEFECT_REVIEW.md §2-§3",
  "approved_by": "<name>",
  "approved_date": "2026-08-05",
  "status": "active",
  "lifecycle": [{"event": "approved", "date": "...", "actor": "...", "note": "..."}],
  "affects": ["behaviours_query.json:harm-avoidance-to-third-parties"]
}
```

Three of those fields are not new. The implied-effects layer already carries
`approved_by`, `approved_date`, `approval_mode`, `status` and a revocable `lifecycle`, and
already cites `imp-<id>` in the explain trail. **This design generalizes that entry type
rather than inventing one** — implied effects become one *kind* of interpretation
(a bearer the text implies but never names), alongside boundary rulings like I-01.

---

## 4. How it plugs in

### Recording — the version-key convention, unchanged

The repo already mandates that any behaviour change be reachable via a version recorded in
snapshot config (amendment F9; `cycle.py` refuses to open a code cycle without
`compatibility.version_key`). Interpretations become one more registered axis on the
config-driven builder:

* `config_key`: `interpretation_set`
* **absent means**: no interpretations applied — the pre-interpretation legacy behaviour, so
  every existing snapshot reconstructs unchanged.
* present: the sha of a frozen interpretation-set artifact, so a snapshot *is* a statement
  of which readings were in force when it was taken.

This is the same shape as `pricing_version` and the thresholds artifact, and it is why the
`index_builder.py` refactor is the right foundation: adding this axis should be a registry
entry, not a new branch.

### Surfacing — the explain trail

Every hit already reports the atoms that matched and the spans licensing them. It gains an
`interpretations` list: the ids the hit depended on, or empty.

**Empty is the important case.** A hit that cites no interpretation is licensed by document
text alone. That distinction — "the spec says this" versus "the spec says this *under our
reading of an ambiguity*" — is exactly what an auditor needs and cannot currently get.

### Switching — a read-time view

A reader selects a non-default reading; the tool rescores and marks the result as a view,
naming the deviation from the recommendation. Views are not snapshots and are not
measurement inputs.

---

## 5. What this buys

1. **Auditability reaches the last un-traced input.** Spans, atoms, and thresholds are all
   already inspectable. Interpretations are the remaining silent one.
2. **Disagreement becomes cheap and specific.** Instead of "I think you drew that boundary
   wrong", a reader gets the alternative reading and the exact set of passages that move.
3. **The cost of a reading becomes measurable.** "What does I-01 buy?" is a snapshot diff —
   the flip machinery that already exists. Today the answer is an argument.
4. **It matches how the project already reasons.** The strongest work here has come from
   naming a judgement and measuring its consequences (the S3 revert, the 746 band, the D5b
   ceiling). This makes that a standing capability rather than a per-question effort.

---

## 6. Anti-fitting constraints — non-negotiable

Every toggle is a knob, and this repo has been burned by knobs: two `Weights` constants were
selected by reading results off the panel that scores the tool, a violation disclosed in that
class's own docstring. The same must not happen here.

* **The measurement set is frozen and sha-pinned.** Changing it is a cycle: pre-registered
  predictions, complete flip set adjudicated against the document, signed decision.
* **Never chosen to improve a metric.** An interpretation is adopted on document-side grounds
  or not at all. Adopting one because it raises MCC is the same violation as fitting a
  threshold, and should be a review finding by name.
* **One recorded vector, never a grid.** The enabled set is a single artifact with a sha.
  Sweeping combinations to find a good configuration is forbidden; if `N` entries ever make
  `2^N` tempting, that is the signal to stop, not to automate.
* **User views never feed reported numbers.** Structurally, not by convention: a view carries
  no snapshot tag and cannot be written as one.
* **Panel-blind adoption.** Same fence the implied-effects layer specifies: the approver sees
  clause text and the definition, never panel verdicts, judge ratings, or the census. Note
  that layer's review found the *proposal queue* unfenced even where approval was fenced —
  this design inherits that finding and must fence proposal too.

---

## 7. Worked examples

### I-01 — the organisation boundary (from m0108)
Endorsed: **representation**. Alternative: **literal participant**. Approximate blast radius:
every clause where a named party is the user's own organisation. Concrete consequence: under
the endorsed reading m0108 is not third-party harm; under the alternative it is.

### I-02 — foreseeable downstream harm
The m0108 review excluded downstream effects: *"that a compromised corporate account might
later be leveraged against outsiders is a counterfactual chain absent from the text."* But
the behaviour definition says the model should weigh the **potential** harm to those outside
the conversation, and compromising an organisation's systems has a predictable path to that
organisation's customers.

So the review resolved one axis (representation) while silently deciding a second one it
never named. That is precisely the failure this layer exists to prevent, and it is a good
first test of the design: **I-02 should exist as an entry even though we endorse the narrow
reading**, because the narrow reading is a choice.

Endorsed: **textually-named bearers only**. Alternative: **foreseeable downstream bearers
count**. Expect a large blast radius — most security, privacy and integrity clauses have a
path to someone outside — which is itself worth measuring rather than assuming.

### I-03 — uniform example-clause treatment (from D3)
Already ruled: example clauses get no distinct rule
(`LATENT_FIX_REGISTRY.md` LF-1, grounded in a 183-clause enumeration finding zero instances
of the problem). A ruled-and-measured interpretation, included to show entries need not be
contested — they need to be *visible*.

### I-04.. — implied effects
Each approved implied effect (m0239 first) is an entry of kind `implied_effect`, inheriting
the layer's existing approval, provenance and revocation machinery.

---

## 8. What v1 does not do

* No mixed default set. All entries ON; the schema permits a mix, nothing builds the case
  for one yet.
* No user interface. This defines the artifact, the config axis, and the explain-trail
  field; presentation is downstream.
* No automatic detection of interpretations. Entries are created when a human notices a
  judgement call, which is how I-01 and I-02 arose. Automating discovery is a research
  question, not v1.
* No retroactive audit. Existing cycle records are not mined for implicit interpretations.
  That backlog is real — I-02 was found by reading one review closely — and is registered
  as follow-up work rather than done here.

---

## 9. Open questions for review

1. **Granularity.** Is I-01 one entry, or one per behaviour it affects? One entry with an
   `affects` list is simpler; per-behaviour is more precise if a boundary should differ
   across behaviours.
2. **Does an interpretation change need a full cycle?** It is score-affecting, so the
   default answer is yes. But adding an entry that merely *documents* an already-applied
   reading is a noop by construction, and noop cycles have a cheaper path.
3. **Where does the artifact live**, and does its sha join snapshot config identity directly
   or ride the existing inputs block? The thresholds artifact is the precedent to copy.
4. **Interaction with the sealed TEST set.** Interpretations adopted while looking at
   dev-cell behaviour could leak into the generalization phase. The DEV/TEST discipline
   needs restating for this artifact specifically.
5. **Retroactive audit scope.** How far back do we mine cycle records for interpretations
   that are currently implicit?
