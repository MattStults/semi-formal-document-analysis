# PRE-REGISTRATION — routing criterion sizing

Written BEFORE any module content was read. What had been read at the time of writing:
- `walkthrough/resources/03_pipeline.md` (the design) — for question 1 only.
- `prompt/00_task.md:105-113`, grep of `abstain` across `prompt/`.
- The *structure* of a run directory, one prompt file (`l1_170_n006.prompt_user.txt`),
  and one **abstained** module (`l1_170_n015.json`).
- Outcome counts per run (`translated` / `abstained` tallies only — no bodies).

Nothing in the `asserts` / `ontology` body of any `translated` module had been read.

---

## 1. Population

Every JSON module on disk under
`resolve_runs/graph_v2/translation_sample/runs/*/` with `outcome == "translated"`,
deduplicated by `clause_id`, keeping the **most recent** run's copy.

Measured before pre-registration: 179 unique clause ids, 165 with at least one
`translated` outcome, 18 with at least one `abstained`, 4 with both.

The two most recent run directories (`20260815-113545`, `20260815-124836`) are
suspected to be the **live in-flight run**. They are excluded from the "most recent
copy" selection so that a run still being written cannot change the answer.

## 2. The judgement is split so the judge never sees the module

The harm the reframe names is **"a fact rendered as a deontic rule"**. That is a
conjunction of two things, one of which is a property of the *source text* and one of
which is a property of the *emitted module*. They are measured separately:

- **Judged (by blind local subagents, text only):** is the node's claim NORMATIVE or
  DESCRIPTIVE?
- **Measured (deterministically, from disk):** does the module emit a deontic
  assertion?

The judge is shown the node's ESTABLISHES line and its verbatim SOURCE TEXT and
**nothing else** — not the clause id, not the module, not the run, not this document.
This is deliberate: the previous attempt at a related quantity was withdrawn at
kappa 0.248 because judges were asked a compound question. Splitting it removes the
module from the judge's view entirely.

## 3. Judge question, fixed wording (single question, three answers)

> Below is one claim extracted from a policy document, with the verbatim sentence(s)
> it came from. Decide which ONE of these three the claim is.
>
> **NORM** — the claim states a requirement, prohibition, permission, priority, or
> preference governing what some actor should or may do. Words like must, should,
> may, never, always, is required to, takes precedence over, prefer.
>
> **DESCRIPTION** — the claim states that something IS the case, and imposes no
> requirement on anyone's conduct. This includes facts about the document itself
> (what a section covers, how it is organised, what it is for), facts about an
> organisation, definitions, and statements of purpose or goal that do not tell any
> actor what to do.
>
> **NEITHER** — the claim has no propositional content that could be recorded at all:
> a bare section heading, a fragment, or text whose meaning cannot be fixed without
> inventing entities the passage does not mention.
>
> A statement of what a document *aims at* is DESCRIPTION, not NORM, unless it also
> tells an actor to do something.
>
> Answer with exactly one word on the last line: NORM, DESCRIPTION, or NEITHER.

## 4. Deterministic side, fixed definitions

For each module, from its JSON:

- `deontic_hard` = it has ≥1 entry in `asserts` whose status is `forbid`, `permit`,
  or `oblige`.
- `deontic_soft` = it has ≥1 `asserts` entry with status `prefer` **and no**
  `forbid`/`permit`/`oblige`. Reported separately and **not** counted as harm:
  `03_pipeline.md:617-620` licenses `prefer` for goal-like comparatives and states
  that no situation violates a preference, so a goal rendered as `prefer` asserts no
  rule the document lacks.
- `ontology_only` = it has ≥1 `ontology` entry and no `asserts` at all.
- `bodyless_ontology` = an `ontology` fact whose `atom` contains no `:-`.

## 5. The three buckets (assigned by rule, not by a second judgement)

| bucket | rule |
|---|---|
| **(a) genuinely normative — stays as-is** | judged NORM |
| **(b) FACT RENDERED AS A DEONTIC RULE — the headline** | judged DESCRIPTION **and** `deontic_hard` |
| **(b-null) fact, already routed correctly** | judged DESCRIPTION and not `deontic_hard` |
| **(c) genuinely untranslatable** | judged NEITHER |

Bucket (b) is the population the reframe says the pipeline is getting wrong. It is
reported as a fraction of all translated modules, with a Wilson 95% interval.

## 6. Agreement protocol — reported BEFORE any point estimate

- Two different local model tiers judge every sampled item independently:
  **tier H (haiku)** and **tier S (sonnet)**.
- Each subagent sees **exactly one** item. No batching, no shared context.
- Cohen's kappa over the 3-way label is computed and reported **first**.
- **Stopping rule, fixed now:** if kappa < 0.60 on the 3-way label, no point estimate
  for bucket (b) is reported. Instead a **bracket** is reported —
  [items both tiers call DESCRIPTION ∧ deontic_hard, items either tier calls
  DESCRIPTION ∧ deontic_hard] — and the finding is stated as "the data cannot
  separate these buckets at the available judge quality."
- If kappa ≥ 0.60, the point estimate is the **both-tiers-agree** count, with the
  either-tier count reported as the upper edge.

## 7. Sample

Deterministic quantities (`deontic_hard`, ontology usage, route counts) are computed
over the **whole** 165-module population — they cost nothing.

The judged quantity is computed on a **random sample of n = 40**, seed `20260815`,
drawn from the 165 with `random.Random(20260815).sample(...)`. The sample is drawn
and written to `sample.json` before any judging. n = 40 gives a Wilson half-width of
roughly ±13pp at p ≈ 0.3, which is enough to tell "a handful" from "a third" —
the decision-relevant distinction — and is not enough to support a precise rate,
which will be said plainly.

## 8. Discoverability (question 3) — fixed definition

Over **attempt-1** drafts only (the first entry in each `*.transcript.json`, before
any repair), for the items judged DESCRIPTION:

- **route-ontology** = the attempt-1 draft put content in `ontology` and emitted no
  `forbid`/`permit`/`oblige`.
- **route-deontic** = the attempt-1 draft emitted ≥1 `forbid`/`permit`/`oblige`.
- **route-abstain** = the attempt-1 draft abstained.

Discoverability = route-ontology / (all three). This distinguishes "the route is
missing" (schema change) from "the route is undiscoverable" (prompt change).

## 9. Things this study will NOT do

- Not edit `prompt/*.md`, `schema.py`, `resources/03_pipeline.md`, or
  `resolve_runs/graph_v2/node_*.md`. The proposal is delivered as reviewable diff text.
- Not write anything under `runs/`, `translation_sample/runs/`, `repair_graveyard/`.
- Not make any provider call. Zero spend.
- Not propose lowering any quality floor.
- Not report a point estimate ahead of the agreement statistic.

---

## AMENDMENT 1 — written after the deterministic census, BEFORE any judging

**Measured first, with no judgement involved:** of 152 translated modules, **73** emit
at least one `forbid`/`permit`/`oblige`; 12 are `prefer`-only; 67 emit no `asserts` at
all (64 of those are ontology-only).

By the §5 rule, **a module that emits no hard deontic assertion cannot be in bucket
(b)**. So 79 of the 152 are excluded from the headline by construction, and the
pre-registered random-40-from-152 sample spends roughly half its judgements on items
that cannot move the number.

**Ruling:** the judged sample is redrawn as **40 of the 73 `deontic_hard` modules**,
`random.Random(20260815).sample(...)`, written to `sample.json` before judging. The
headline becomes

    bucket (b) = P(DESCRIPTION | deontic_hard) x 73

with the Wilson interval taken on the conditional and scaled. The rejected
alternative is **"judge all 73"** — 73 items x 2 tiers x isolated dispatch is not
affordable in this session, and 40/73 already gives a Wilson half-width near +/-15pp on
the conditional, which is enough to separate "a handful" from "a third".

The cost of the amendment is stated plainly: **bucket (c) is now measured only within
the deontic_hard stratum**, so the NEITHER rate reported is conditional and is NOT a
whole-population untranslatability rate. It will be labelled as such.
