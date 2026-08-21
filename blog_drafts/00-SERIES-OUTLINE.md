# BLOG SERIES OUTLINE — "Reading a model spec like an instrument" (DRAFT, campaign 2026-08)

Working title set. Every post carries the scope-honesty rule: what each
piece establishes and what it does NOT, stated where a reader would
otherwise over-read. Numbers appear only with an artifact pointer; claims
about the current arc are marked provisional until the weekend certification
runs land (post 3 is written LAST).

## Post 1 — What I'm trying to do, and why the goal changed
- The question: "which passages of this model spec bear on behaviour X?" —
  answered today by eyeballing or by asking a frontier model: slow,
  expensive, unauditable, and different every time you run it.
- The product: read the document once into a semi-formal layer; answer the
  question instantly, offline, with a citable span per answer and a stated
  reason for every hit. Label-free: the tool does not know the panel's
  verdicts and never reads them at query time.
- The goal restatement (the honest pivot): the target is NOT "match the
  panel". It is a logically consistent, auditable reading of the document —
  explicit toggleable assumptions, disagreement surfaced as output. Panel
  agreement is a calibration instrument, not the objective. Why: a tool that
  scores well by fitting judges inherits the judges' blind spots; a tool
  that reads the document can be wrong in ways you can find and fix.
- What the project became: the measurement instruments and the process
  around the tool outgrew the tool — pre-registered flips, blind
  adjudication, anti-cheat scans that caught real leaks, certified
  small-model judgment seats.
- Establishes: the problem, the product goal, the restatement. Does NOT
  establish: that the tool beats panels (it does not, on the old bar), or
  that the current arc has certified anything yet.

## Post 2 — The technical design: a spec as a logical object
- The pipeline: document -> graph decomposition into nodes -> typed
  translation (acts with deontic status, governed qualities, protected
  parties, actors, purposes, contexts) -> an instrument that matches
  behaviour modules against the translated corpus -> a census that says
  which remaining disagreements are fixable-in-principle and which are
  terminal.
- The contract: translation is governed by a written contract (currently
  v18) — what a module may say, what it must cite, which lanes exist
  (assert-level frontier annotation; definition-level; example-act and
  definition-act lifting; context atoms), and who may declare what.
- The measurement discipline as architecture: the separability census
  (CURRENT = the frozen instrument per behaviour; REACHABLE = the design
  space), the dead-slot probes, the fail-loud guards on channels the census
  cannot represent. These are not decorations; each exists because a real
  defect class was found.
- Establishes: the design and why each piece exists. Does NOT establish:
  that the design is minimal or final — it is where the defects have pushed
  it.

## Post 3 — How it's working (written AFTER the weekend runs)
- Certification of the Model Spec for three behaviours: the fresh-draw
  protocol, what a certified number means (and what it costs).
- Generalization: six never-consulted behaviours run zero-adaptation; the
  fix ledger as the primary result (does a new behaviour cost a fixed
  procedure, or another campaign?).
- The collaborator frontier panel (v5 bench) as comparison layer only —
  truth stays adjudicated.
- The failures worth their weight: the reverted "improvement" that deleted
  the spec's de-escalation guidance while the metric said ship it; the
  false-separable classes in the census; the annotation lanes that no
  provider seat could read.
- Establishes: whatever the runs establish, scoped exactly that far.

## Living summary (updated last, kept current)
- 5-minute read: problem, product, current state, direction. State +
  direction only, never changelog. Points to the three posts and the
  artifact trail.
