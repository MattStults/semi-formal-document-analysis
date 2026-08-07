# The ontology-fit test

`ontology_fit.py` — run this during **ontology setup**: whenever a specification is added, a
specification changes, the ontology changes, or the model changes.

| | |
|---|---|
| `ontology_fit.py` | the tool. `--help` states what it measures and what it cannot |
| `ontology_fit_config.json` | ⭐ every knob, at its default, with the reason next to it |
| `ontology_fit_dryrun.txt` | ⭐ **the worksheet** — the `--dry-run` output for the default config, reviewable and fillable without spending |
| `ontology_fit_worksheet.json` | the same 20 concepts as a fillable JSON stub, for `--expected` |
| `ontology_fit_selftest.txt` | the `--self-test` output: 39 checks, each shown going RED for its own named reason |
| `ontology_cache/lkif-core/*.ttl` | vendored LKIF-Core (CC BY 4.0) — see "the imports are dead" below |

```bash
python3 ontology_fit.py --self-test        # no network, no API, no cost
python3 ontology_fit.py --dry-run --worksheet-json ws.json   # the worksheet. No call.
python3 ontology_fit.py --list-classes     # what parsed, at what depth, in which module
python3 ontology_fit.py --live             # ~$0.03. Needs authorisation.
python3 ontology_fit.py --live --expected ws.json   # ...also scored against your worksheet
```

---

## The one question it answers

> **Can this model place concepts from this text into this ontology's upper classes,
> consistently enough to be usable?**

⛔ **Consistently. Not correctly.** See the scope section — it is the most important thing on
this page.

### Why the answer is a SET, not one label

Naming is unbounded: *"what should this concept be called?"* has no wrong answer that announces
itself, and inter-run agreement on a free-text name is not a quantity. That is problem #8, and it
is why some closed-vocabulary task has to replace naming.

But the first version of this tool over-corrected into **single-label classification**, on the
premise — taken from `SCRATCH_concept_phase.md` — that a closed set "has fifteen answers, a
definite right one". **That premise is false.** `developer` is an `Agent` **and** a `Role`, and
instantiated, a `Person`. LKIF is itself a multiple-inheritance ontology: `Person` is a subclass of
`Agent` *and* of `Natural_Object`. Forcing one label does two bad things:

1. it discards the multiple-inheritance structure that is the reason to use an ontology at all; and
2. ⭐ **it manufactures disagreement.** Two runs answering `Agent` and `Role` are *both correct*.
   Under a forced single choice they score 0. A low agreement number would then be an artifact of
   the question, not a property of the model.

So the task is: **return the most specific classes in the closed vocabulary that subsume this
concept — one or more.** The answer is a set; the vocabulary is still closed, which is what keeps
it measurable. The self-test contains this exact case as a named check.

---

## ⛔ Scope: self-consistency only

**No ground truth is used in this run and none is claimed.**

A model that places every concept under the same **wrong** classes, every time, scores a
**perfect 1.0**. Consistency is necessary and never sufficient. The verdict line says so, the
JSON report carries a `measures` field saying so, and `what_would_change_it` ends by saying that
nothing in the report would move a verdict about correctness.

**Correctness is judged by a person, through the worksheet** (below), as a pre-registration.

It also does not answer: whether LKIF is the right ontology (the `NONE_OF_THESE` rate is a coverage
hint, nothing more); whether a human would agree; steps 2 (PARENT) and 3 (MINT) of the concept
phase; or whether the prompt is any good.

---

## ⭐ The worksheet is the primary deliverable

`--dry-run` does not print a summary. It prints a document a person reads top to bottom and writes
into, and it costs nothing. Per sampled concept it gives:

* the **concept name** and its **gloss**
* the **source sentence** it was extracted from, and the clause id
* the existing **hand-rolled `kind`** (`situation` / `act` / `entity` / `value`), for comparison
* a blank **`expected_placement`** line
* the **exact prompt** that will be sent

and, once at the top, the **full closed set with every class's own gloss**, so a reader can see
what the options mean before choosing among them.

```
--- 01/20 ------------------------------------------------------------
  concept          : automated_monitoring
  gloss            : Using automated systems to monitor model use or outputs
                     for potential violations.
  source sentence  : we do use automated monitoring to detect potential usage
                     policy violations and
  from             : m0120
  hand-rolled kind : act        <- the existing 4-category label, for comparison

  expected_placement: ______________________________________________
```

Write the expectations **first**, then run. That turns the correctness check into a
pre-registration rather than a rationalisation: `--worksheet-json` emits the same rows as a
fillable JSON stub, and `--live --expected <that file>` reports mean Jaccard of the model's
placements against yours. Sampling is deterministic given `(corpus, n_items, seed)`, so a
worksheet filled today scores against a run made next week.

⚠️ **The hand-rolled `kind` is on the worksheet and deliberately NOT in the prompt.** Feeding the
model the four-category label would anchor the placement on the very scheme the ontology is meant
to replace, and the comparison between them would be circular. Adding `kind` to
`corpus.prompt_context_keys` raises `ConfigError` — there is a self-test that proves it.

---

## How to read the live output

```
mean pairwise Jaccard    : 0.8000   95% CI [0.7333, 0.8667]  (bootstrap over concepts)
trained-human-pair band  : 0.30 / 0.24 / 0.29  (MIREL, annotated ECHR)
identical placements     : 8/20 concepts had every run return the same set
classes per answer       : mean 1.42, distribution {1: 35, 2: 25}
NULL                     : each run returns a set of the SAME SIZE the model actually
                           returned, but drawn uniformly at random from the 22-class
                           closed vocabulary
p vs that null           : 4.9998e-05
NONE_OF_THESE rate       : 0.150
```

### The statistic: Jaccard, not a kappa

The answers are **sets**, so a chance-corrected single-label statistic cannot represent them.
Fleiss' or Cohen's kappa would have to score `{Agent}` against `{Role}` as total disagreement when
both are right — the exact artifact this design exists to avoid — and neither has a defined
meaning when one rater returns two categories. Mean pairwise Jaccard between runs, averaged over
concepts, is the natural measure over set-valued answers; the CI is a percentile bootstrap over
concepts, which is the unit that was sampled.

### ⭐ The reference line is 0.27-ish, not chance

The MIREL project's annotated ECHR data gives concept-vocabulary Jaccard of **0.30 / 0.24 / 0.29**
between **pairs of trained human annotators** on legal text (measured, not published). So the
question is *"is this within reach of two trained people"*, not *"is this better than guessing"*.

⚠️ **Two caveats, printed on every report, not just here.** It is a different corpus and a
different ontology, so it is a rough reference and not a strict baseline. And it measures agreement
between **two different annotators**, whereas this measures **one model against itself on an
identical prompt** — a strictly easier task. Treat the band as a **low floor**, not a pass mark.
A model that merely ties two humans disagreeing with each other has not shown much.

### The p-value

The null is stated in the output, not left implied: *each run returns a set of the **same size**
the model actually returned, but drawn uniformly at random from the closed vocabulary.* Sizes are
held fixed on purpose — a null that also randomised set size could be beaten by nothing more than
the model's consistent verbosity, and "the model reliably answers with two classes" is not evidence
that it places concepts consistently. Fixing sizes asks the sharper question: **given how many
classes it returns, does it return the same ones?**

### ⭐ Per class: two different instabilities, counted separately

```
  class                     uses  items  stable  unstab  solo  swapped for
  Agent                        6      4       0       4     8
  Process                     10      6       1       5    10  Action(3)
```

* **swapped for** — one run said `A` exactly where another said `B`. Points at two classes whose
  glosses do not separate.
* **solo** — a class came and went with nothing offered in its place. Points at disagreement about
  **how many** classes apply, not which.

These need different fixes, so they are not merged. (An earlier version counted every co-present
class as a "swap" and reported `Agent swapped_with Role` when `Role` was stable in every run and
only `Agent` came and went. That was wrong and is now a documented distinction.)

A good aggregate number can hide one bad pair — read this table before the verdict.

---

## The verdict, and what would change it

Read on the **CI lower bound**, never the point estimate, so a small `--n-items` cannot buy a good
verdict:

| verdict | condition |
|---|---|
| **usable** | Jaccard CI lower bound ≥ **0.30** — the top of the human band |
| **marginal** | lower bound ≥ **0.24** — inside the human band |
| **unusable** | below the band, **or** p > 0.01 whatever the Jaccard |

The boundaries are read directly from `reference.human_pair_jaccard` in the config — there is no
second copy of those numbers, so changing the band changes the verdict. Every run prints the exact
lower bound needed, the current margin, the CI half-width (which shrinks as 1/√n), and a final line
reminding the reader that **none of it bears on correctness**.

**What a failing verdict means**, in order of likelihood: the closed set contains classes whose
glosses do not separate (read the *swapped for* column); the model disagrees with itself about how
many classes to name (read *solo*, and consider constraining the answer size in the prompt); or the
placement step is genuinely not stable enough to build on — in which case the concept phase fails
at step 1 and nothing downstream is worth building.

---

## Fail-closed

This project has repeatedly shipped checks whose "pass" was indistinguishable from "did not run".
That is the primary failure mode designed against here. **Every one of these raises and reports
nothing:**

| condition | error |
|---|---|
| ontology parsed to zero classes | `OntologyParseError` (the parse canary) |
| ontology module absent and downloads disabled | `OntologyParseError` |
| a name in `include_classes` is not in the loaded modules | `ClosedSetError` — a typo must not silently shrink the vocabulary the null is computed over |
| closed set has fewer than 2 members | `ClosedSetError` |
| corpus missing, or zero concepts after filtering | `CorpusError` |
| `--n-items` larger than the corpus | `CorpusError` |
| the API errors, or a client returns `None` | `ProviderError` |
| a response was truncated (`finish_reason=length`) | `ProviderError` — a cut-off completion can contain a partial set |
| a response is empty, or contains any token outside the closed set | `ResponseParseError` — one invented class rejects the whole answer |
| a response combines `NONE_OF_THESE` with real classes | `ResponseParseError` — incoherent |
| zero responses collected | `ProviderError` |
| `--runs-per-item` < 2 | `DegenerateAgreementError` |
| `expected_placement` names a class the model was never offered | `ClosedSetError` |
| the `--expected` worksheet has no filled rows | `CorpusError` — an unfilled pre-registration is not a score of zero |
| `prompt_context_keys` includes the hand-rolled prior label | `ConfigError` — that comparison would be circular |
| estimated cost over the ceiling, or unpriced provider | `CostGateError`, before anything is sent |

`--self-test` exercises all of them and prints, for each, the error class raised and the reason it
was supposed to raise for. **A check that has never gone red is not a check**, so the self-test is
RED-first by construction. Its greens include Jaccard against hand computation, the
Agent/Role manufactured-disagreement case, and a check that the parser really does recover
multiple inheritance from LKIF (the fact the whole design rests on).

---

## ⚠️ Every `owl:imports` in LKIF-Core is dead

`estrellaproject.org` 301s and then 404s. **Any loader that resolves imports cannot load this
ontology at all** — which is why this tool vendors the module files and parses them directly with a
stdlib Turtle/RDF-XML parser rather than using `rdflib` or an OWL API. A future reader will assume
the standard tooling works; it does not.

Related, so that nobody over-trusts the source: the **ontology content is unchanged since 2008**.
The February 2026 commit was a **licence change only**, and 39 of its 48 forks have no commits of
their own. It is a stable, well-cited artifact — **not an actively maintained one**, and this
document does not describe it as such.

One more parser trap, found the hard way: LKIF **re-declares foreign classes in importing modules**
with only their local axioms — `role.ttl` declares `action:Action` with no `rdfs:subClassOf` at
all. A first-declaration-wins merge silently orphans `Action` from `Process` and every depth below
it is then wrong. The loader unions parents across modules instead.

---

## Configuration

Everything is in `ontology_fit_config.json`; CLI flags override individual keys; `--config` points
somewhere else entirely. Nothing about LKIF, the Model Spec or any provider is hardcoded in the
tool.

* **text** — any JSON file that is or contains a list of records: `path`, `records_key`, `id_key`,
  `text_key`, `dedupe_by`, `prompt_context_keys`, `worksheet_fields`, and
  `include_where` / `exclude_where` / `min_text_chars` filters. The default is the naive-extraction
  atom set (`annotations.json`, 1,423 atoms → 330 distinct concepts after dedupe), because the
  worksheet needs a concept, a gloss, a source sentence and the prior label, and that file is the
  only one carrying all four. To place raw clause text instead, point `corpus` at
  `modelspec_clauses.json` with `records_key: "clauses"`, `id_key: "id"`, `text_key: "quote"`.
* **ontology** — a directory of module files or a URL template, Turtle or RDF/XML. `tiers` chooses
  which modules load; `vocabulary_only_modules` marks modules whose **class names are taken and
  whose axioms are not** — the standing resolution on `norm`, whose deontic commitments
  (`Prohibition ⊑ Permission`, `Prohibition ≡ Obligation`) we ruled against. Naming `Prohibition`
  says a concept *is* a prohibition; it does not license inferring what follows from one.
* **model** — reuses `semi-formal-experiment/providers.json` + `providers.py` `LiveClient` when
  both are present (so live runs append to `usage.jsonl` and stay visible to `spend.py`), and falls
  back to a stdlib client configured inline. Neither file is required.
* **sampling** — `n_items` (20), `runs_per_item` (3), `seed` (0), `temperature` (1.0).
  ⚠️ Temperature must be > 0. At `--temperature 0` this measures the *API's* determinism, not the
  model's stability, and a perfect score would mean nothing.

## Cost

The estimate is printed **before** any call and gated at `cost.max_cost_usd` (default $0.50); over
it, nothing is sent. An **unpriced provider counts as over budget**, never as free. The estimate
assumes the worst case — every call emitting the full `max_tokens` — because on a reasoning model
the hidden reasoning is billed as output and dominates, and overstating is survivable while
understating is how a hard cap gets passed.

Default configuration: **60 calls, ~$0.03** against a ledger at $2.06 of $8.50.

---

## Where this departs from `SCRATCH_concept_phase.md`

1. ⭐ **"a definite right one" is false, and the scratch has been corrected.** See the top of this
   page. This is the substantive change: single-label classification manufactures disagreement on a
   multiple-inheritance ontology.
2. **"a CLOSED set of ~15" is underspecified, and no structural cut yields it.** Measured on the
   loaded modules: `Agent` d0, `Person` d1, `Process` d1, `Action` d2, `Role` d2, `Norm` d3,
   `Permission` d4, `Prohibition` d5. A depth ≤ 1 cut gives mereology's `Atom`/`Part`/`Whole` and
   **drops `Action` entirely**. The closed set is therefore a **declared, reviewable list** in
   config (21 classes + `NONE_OF_THESE` = 22), not a by-product of hierarchy shape.
3. **There is no `spacetime` module.** The abstract tier is `lkif-top`, `relative-places`,
   `mereology`, `time`.
4. **`norm` is in the legal tier**, so "abstract+basic tiers, norm vocabulary-only" is an *addition
   with a flag*, not a subtraction from a tier.
5. **V1 ("classification agreement, κ over a CLOSED set") is superseded** by V1′: Jaccard over
   set-valued placement against a human-pair reference band. The scratch's reasoning for why V1 is
   *possible* survives intact; only the statistic and the answer shape change.
