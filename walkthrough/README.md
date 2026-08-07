# `walkthrough/` — a prototype that is allowed to contradict the rest of this repository

**Read this before changing anything in this directory, and before citing anything in it elsewhere.**

## What this is

A **complete redesign** of the surrounding project, being validated as a prototype. The rest of the
repository builds a *lexical relevance scorer*: it ranks passages by overlap and is measured against
a judge panel. This directory attempts something different — translating each clause of a
specification into a small logic program, verifying the translation says what the clause says, and
linking the results so a derivation can chain across clauses.

The two share a corpus and nothing else. Different representation, different failure modes,
different evidence.

## The rule that makes this directory work

⭐ **`resources/03_pipeline.md` is the source of truth for everything in `walkthrough/`, above any
other document in this repository.**

Outside this directory, the repo's own rulings, module map and handoff notes govern. Inside it,
they do not automatically apply. **A contradiction between this directory and the wider repo is
expected and is not a defect to be reconciled.**

⚠️ This does *not* mean repo practice is irrelevant here. Two adversarial reviews found real
defects in the design by comparing it against repo practice, and several were adopted — the graded
`textual / assumed / world` licence, the rule that seat divergence defaults to a *brief* defect
rather than a document finding, the seat-contract format. The rule is that repo practice is
**evidence to weigh, not law to obey**. Where this directory departs, it should say so and say why.

## How to interact with it

**If you are an agent working in this directory:**

1. Read `resources/03_pipeline.md` first. It carries the current design, and — more importantly —
   an explicit list of open questions with contrary evidence. Several load-bearing choices are
   *not settled*.
2. Do not "fix" an inconsistency with the wider repo. Check whether the departure is deliberate;
   if it is not recorded, say so rather than resolving it.
3. Do not import repo ceremony because it exists. `cycle.py`, the flip budget, panel-blindness
   fencing and DEV/TEST splits all exist to protect continuous scores against a label set. This
   directory has neither.
4. **Evidence discipline is the one thing that does carry over unchanged.** Every number states its
   source and its n. Every check is shown failing for its named reason before it is trusted. A
   claim inferred from code structure is marked inferred until it is run.

**If you are citing this directory elsewhere:** don't, yet, except as a prototype. Part 6 of the
pipeline document is the honest status — three components of roughly fifteen have running code, and
the first stage has never been executed.

## What is here

| | |
|---|---|
| `resources/03_pipeline.md` | ⭐ the design. Source of truth for this directory |
| `resources/00_established_practice.md` | published practice for validating a text→logic translation, with provenance |
| `resources/01_which_checks_are_scripts.md` | which checks are deterministic, which need a model, and what context each seat may and may not see |
| `resources/02_problem_taxonomy.md` | how to enumerate the problem space so coverage is arguable rather than asserted |
| `resources/04_deolingo_assessment.md` | whether a deontic ASP extension covers our cases *(pending)* |
| `WALKTHROUGH_REPORT.md` | the hand-executed worked example that produced most of Part 1's problem list |
| `m0255.lp`, `clauses/`, `m0255_case_*.lp`, `witness.lp`, `behaviour_harm3p.lp` | that worked example — one clause, its three linked dependencies, four probe cases |
| `link.py` | the built deterministic checks: cross-reference closure, unresolved names, rule-shape |
| `paper_pipeline/` | pipeline components as they are built, hand-executed first |

## Working method

Each pipeline stage gets hand-executed before anything is automated. Before each, a **Step X**
section is written describing what will be done, with a specific passing example, a specific
failing example, what evidence the step produces, and what it costs — and that section is agreed
before the work starts.

The reason is on the record: three times in this project a check was built that measured the wrong
thing and reported success. In each case the mechanism was describable but the *failing case* was
not, and writing one down first would have caught it.
