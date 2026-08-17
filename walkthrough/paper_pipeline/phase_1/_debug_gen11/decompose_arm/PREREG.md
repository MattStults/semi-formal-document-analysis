# PREREG — ARM G, task decomposition

**Signed before the first live call.** Nothing under `promptsG/`, `run_armg.py` or
`layers.py` was edited after this file was written; `layers.py` was written and
calibrated first, on data already on disk, at $0.

---

## 1. THE HYPOTHESIS AND WHAT WOULD REFUTE IT

Three arms shipped the 20-entry review list as static prose in ONE call and returned
nulls (`list_in_prompt/RESULT.md`, `list_in_prompt_insample/RESULT.md`). The cause none
of them could test: **the task is too large for one pass.** A module must settle the
deontic layer, the ontology layer, the declaration layer and citation discipline
simultaneously, and the measured defects cluster by layer.

Arm G splits the work into four calls over one transcript. If decomposition is the
active ingredient, defects should fall **unevenly by layer**, and the layer that does
not move is the one arguing for a schema change rather than a process change.

## 2. THE SPLIT, AND WHY THIS ONE

| stage | system block | what it settles |
|---|---|---|
| 1 ENUMERATE | `s1_enumerate.md`, 2,103c | the span, in prose. **No formalism at all.** |
| 2 DEONTIC | `s2_deontic.md`, 2,234c | statuses, acts, bodies, read-backs, closure |
| 3 DECLARE | `s3_declare.md`, 2,832c | ontology vs requires vs inputs, arity, glosses, licences |
| 4 ASSEMBLE | **the production system block, byte-identical** (39,959c, sha256 `3a66c5f5…4c34c`) | the JSON object |

User turn 1 is `translate.build_user`'s production user block, unmodified — the same
span bytes, the same NEEDS/PROVIDES/CITATION instructions. Stages 2–4 append their
stage prompt as a further user turn on the same transcript.

**Grounds for this split.** (a) The natural fault line is the one the defect data
already shows: the four defect clusters are the four layers. (b) Stage 1 must carry no
formalism, because the enumeration failure — a span asserting four things reaching one
rule — is upstream of every formal choice; asking for predicates in the same breath is
what fuses them. (c) The 40 KB production block is 84% of the arm's input cost and is
needed only at emission, so putting it on stage 4 alone makes decomposition **cheaper
than 4× a baseline call**, which is the only way it can win per dollar.

**Rejected alternatives, by name.** *One call with the same four questions inlined* —
that is arm B's design and it is the thing already refuted three times. *A separate
transcript per stage* — the model would have to be re-fed its own prior answers as
prose, which is a summarisation step and a second variable. *Deontic and ontology in
one stage* — cheaper by one call, but it re-fuses the two layers whose defect classes
are most distinct, which is the measurement.

## 3. THE STAGE PROMPTS ARE QUESTIONS, NOT REVIEW-LIST ENTRIES

Deliberate, and it is the arm's fairness condition. Every added item is posed as a
question the model must ANSWER about its own draft-in-progress (*"name a case the body
excludes"*), never as a rule it must obey (*"prefer the bodied rule"*). Shipping rules
is what arms B/C/D did. Total added prose is 7.2 KB across four stages against arm B's
13.5 KB in one, and **no stage prompt contains any clause id, any span text, or any
example drawn from these 17 clauses.**

⛔ **Entry 5 is EXCLUDED, and here is the replacement.** Entry 5 is MEASURED to
manufacture a defect class: obeyed, it turns a harmless inert constant into a vacuous
bodied rule (`no_moral_ambiguity(S) :- scenario(S)`), which asserts the clause's
discriminating condition of every case. Its text contains nothing that would stop this.
Arm G ships **no** instruction to prefer bodied rules. In its place, stage 3 Q1 asks the
**exclusion test**: *name a thing of the head variable's kind that your body excludes;
if you cannot, you have not defined the class* — and then offers the two honest routes
(leave it in `concepts` only, or put it in `inputs`) and requires the model to pick one
by name. A test that fires on the vacuous case cannot manufacture it. The same test is
asked once in stage 1 (q5) against the span's conditions in plain English, before any
predicate exists.

## 4. THE MEASUREMENT — MECHANICAL, BY LAYER

`layers.py`. Every detector reads only the emitted JSON and the node's own user block.
No adjudicator judgement enters any cell of the layer table. This is deliberate:
`list_in_prompt_insample/RESULT.md` §10 records that the single adjudicator on these 17
clauses is contaminated **toward** finding the historical defect, so a per-layer
comparison across three arms cannot rest on that reading.

**Calibration, run before this file was signed, on data already on disk:** the
detectors reproduce arm A's published floor rate (7/17 `outcome != translated`), arm B's
(6/17), and all four rows of arm B's published entry-5 harm table
(`no_moral_ambiguity(S) :- scenario(S)`, `repeats_user_prompt(R) :- response(R)` ×3,
`natural_uncertainty_expression(A) :- assistant_definition(A)`,
`honest_and_forthright(A) :- assistant_conduct(A)`).

| layer | detector | arm A | arm B |
|---|---|---:|---:|
| ONT | ONT-1 type-only body | 5/17 | 9/17 |
| ONT | ONT-2 unlinked singleton | 0/17 | 1/17 |
| ONT | ONT-3 coextensive heads | 3/17 | 3/17 |
| DEO | DEO-1 prefer polarity | 1/17 | 2/17 |
| DEO | DEO-2 shared-body `oblige` | 2/17 | 1/17 |
| DECL | **DECL-1 borrowed-gloss licence** | **15/15** clauses, **24/24** names | **15/15, 24/24** |
| DECL | DECL-2 NEEDS misfiled | 1/17 | 1/17 |
| DECL | DECL-4 undeclared body name | 1/17 | 2/17 |
| CITE | CITE-1 foreign citation | 0/17 | 0/17 |
| — | floor `!= translated` | 7/17 | 6/17 |

⚠️ **ONT-1 is an OVER-INCLUSIVE proxy** and is named as one: it flags any bodied
ontology rule all of whose body atoms are unary over head variables, which catches a
genuine three-condition definition
(`good_response(R) :- explains_possible_causes(R), …`) as well as the real defect.
It is applied identically to all three arms, so the COMPARISON is sound and the
LEVEL is inflated. Every hit is listed in `layer_scores.json` and is recheckable.

⚠️ **DECL-1's denominator is 15 clauses / 24 NEEDS names**, mechanically counted from
the user blocks. The published figure is "16 of 16" on a different basis; the substance
is identical and stronger than published — **every borrowed gloss in both prior arms,
without exception, is stamped `licence: textual`, which under this node's CITATION
instruction can only cite this node, for a concept another node established.**

⭐ **The schema DOES have a legal slot for this** (`schema.py:366` — `assumed` +
`inference`). So DECL-1 is not prima facie a schema gap; it is reachable. That makes it
the sharpest single test in the arm.

## 5. PREDICTIONS — frozen

| | prediction | scored on |
|---|---|---|
| **G-1** | **TRANSFER.** ≥ 1 layer moves by ≥ 5 clauses of 17 vs arm A | layer table |
| **G-2** | **DECL-1 falls to ≤ 5 of 15 clauses.** This is the arm's headline. It is the class no instruction has moved (15/15 in both arms) and stage 3 Q3 asks the question directly and mechanically. If it does not move, the finding is strong. | layer table |
| **G-3** | **DEO-2 goes to 0 of 17.** Stage 1 q3 forces an explicit alternatives/all-required call in prose before any predicate exists, and stage 2 Q2 makes the model read its own bodies back. This is the cleanest decomposition-only signal in the arm — stage 1 q3 adds no rule, only an enumeration. | layer table |
| **G-4** | **ONT stays flat or worsens slightly** (ONT-1 within ±3 of arm A's 5/17). The exclusion test is a question, not the bodied-rule rule; I expect it to prevent the entry-5 manufacture, not to fix ontology generally. | layer table |
| **G-5** | **NULL is live and likely on the floor.** Floor `!= translated` lands 5–9 of 17, i.e. indistinguishable from both prior arms. Decomposition is not predicted to fix schema conformance. | floor |
| **G-6** | **≥ 2 of 17 clauses show a stage-4 object that CONTRADICTS its own stage-2 or stage-3 answer.** The assembly step is the arm's weakest joint and I expect the contradiction to be visible. | hand read |
| **G-7** | **PER DOLLAR: arm G costs 1.5×–2.5× arm A per clause, not 4×** — because the 40 KB block is sent once. Below 1.5× or above 2.5× refutes the cost model. | measured |

### Manufactured harm — pre-registered, and what would make me say so

* **H-G1 fires** if ≥ 1 clause carries a conclusion-changing defect that is the direct
  product of correctly answering a stage question. The candidate I name in advance:
  stage 3 Q1's "put it in `inputs`" route, applied to a **document-side** relation,
  where no situation will ever supply it — the `l1001_1107_n005` / `l3877_3953_n014`
  failure. **If H-G1 fires here I have rebuilt entry 5's harm in a new place** and it
  will be reported as the arm's headline, ahead of any defect reduction.
* **H-G2 fires** if the four-stage transcript raises the floor-failure rate above 11 of
  17 — decomposition crowding out the format.
* **H-G3 fires** if ≥ 3 clauses invent ontology machinery the span does not support in
  order to answer stage 3 Q1's exclusion test.

### The per-dollar criterion, stated before the run

The standing comparison is the Opus-critic loop, which converged in 2–4 turns **and
required a frontier critic reading each draft against the span** — a cost this arm's
ledger would not even see. Arm G is scored as a win **only if** defects per dollar
improve, not defects alone. Concretely: arm A is 1 call at ~$0.00225/clause. Arm G is 4
calls; if it costs 2× and removes fewer than half the defects in a layer, that layer is
reported as **a loss per dollar**, and the sentence will say so before it says anything
about the raw count.

## 6. CONTAMINATION, DISCLOSED

I have read all 17 historical adjudications, both prior arms' RESULT files, and the
review list. I am not blind and do not claim to be. The layer table is **entirely
mechanical** and carries none of this. The hand-read items — G-6, and any per-clause
narrative — carry all of it, and are marked INFERRED wherever they appear.

## 7. SPEND

Cap `run_armg.py:CAP_USD = $0.115`, against the brief's $0.12. Dry run, priced before
anything was sent: **68 calls, worst case $0.1060**, every input char billed at full
rate and every output billed at the full `max_tokens`. The gate refuses at the stage
that would cross. Reconciliation from this arm's own stage records first;
`usage.jsonl` is a cross-check that contains other arms' rows.

## 8. WRITE PERIMETER

Everything this arm produces is under `_debug_gen11/decompose_arm/`. Nothing under
`runs/`, `translation_sample/runs/`, `repair_graveyard/`, `prompt/`, `schema.py`,
`resolve_runs/graph_v2/`, or any other agent's `_debug_gen11/*_arm/` directory is
written. No git is run. `usage.jsonl` is appended by `providers._append_usage`, as every
paid call in this repo does.
