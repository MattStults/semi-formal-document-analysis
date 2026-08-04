# Capacity pilot — pre-registered

**Status: ⛔ WITHDRAWN 2026-08-02, before any spend.** The adversarial review returned
three blockers against exactly this plan: (1) it reopens the representation-capacity
hypothesis HANDOFF.md marks refuted twice under a ⛔ banner, and the richer-emission arm
already ran free twice (`annotations.json`→`b8`, +14% atoms, +0.0054, t(9)=0.49, n.s.);
(2) both proposed guards are structurally blind to the failure mode — `unsupported`
judges only what is asserted, so faithful-but-peripheral atoms raise `sufficient`
without firing it, while adding cross-passage FP surface, and MCC is both too dilute
(MDE 0.032–0.045 vs ~0.005 effects) and forbidden to steer generation on (Invariant 9);
(3) premise (e) below mis-states the cap's provenance — `annotate.py:72-79` is a second,
deliberate, generation-time justification, not an inherited category error.
Kept for the record; do not run. The reversion rule at the bottom fired at step 0.

Written before the run so the predictions below are falsifiable rather than
retrofitted. Spend to date: $1.520 of $8.50.

---

## What this pilot is for

The hole taxonomy (`hole_taxonomy_coder_{a,b}.json`, agreement ARI +0.608 /
NMI 0.749) says roughly a quarter of measured representation loss is
**capacity-shaped** — a conjunct or a list member that was never emitted —
rather than **grammar-shaped** — content with no slot to go in.

If that is right, the cheapest available intervention is to stop suppressing
emission. This pilot tests exactly that, and nothing else.

## The finding that dictates the design

`annotations.json` provenance: `atoms_per_clause = 2.4` (1423 atoms / 593
clauses), against a cap of `2.78`. **The ceiling is not what limits emission** —
a trim enforcing a mean of 2.78 cannot yield a mean of 2.4.

Strictly, whether the trim ever fired on this artifact is NOT determinable from
it: `rate_cap` provenance is `null`, which means the field did not exist when
this artifact was written, not that the cap was skipped (`run(rate_cap=False)`
records `{"applied": False}`, a different value). `_extract_raw.json` is clause
segmentation, not pre-cap atom output, so there is no stored pre-trim
annotation to diff against. The point survives regardless: at 2.4 the trim
cannot be the binding constraint.

What actually binds is `annotate_prompt.md`:

> THIS IS NOT A LICENCE TO EMIT MORE ATOMS. The budget is unchanged: about three
> atoms per clause and a one-line gloss each.

So `--no-rate-cap` alone changes NOTHING — it disables a trim that is not
firing. An arm built on that flag would return a null result caused by the
experiment not having been performed. **Any arm that claims to raise capacity
must change the prompt text, and the diff must be shown in the writeup.**

Separately: 3 of 47 batches reported `truncated: true`, i.e. hit the token
limit mid-reply. That is a second capacity loss with a different cause and a
different fix (`--batch-size`), and it must not be confounded with the first.
Hold `--batch-size 6` fixed across all arms; the pre-spend review already
selected it.

## Design

**Paired, same clauses in every arm.** The comparison is within-clause, so the
statistic is McNemar on the read-back verdicts rather than a difference of two
independent proportions. This is the whole reason a small pilot can say
anything: clause difficulty is the dominant variance term and pairing removes
it.

**Sample.** n = 40, stratified random over the 593 clauses, seed recorded.
Stratify on `kind` so the conditional stratum (the 1/25 sufficiency floor) is
represented. `grammar_candidates.py` is the post-hoc stratifier — label-free by
construction, so slicing results with it cannot be fitted to anything.

**Arms** (each differs from the control in exactly one thing):

| arm | change |
|---|---|
| A control | current prompt, current cap. Reproduces the shipped condition on this sample. |
| B capacity | prompt budget language removed/raised; trim disabled. Rate recorded, not constrained. |

Arm C (enumeration support) is deliberately NOT in this pilot. It requires a
notation design and a re-authored golden set, and bundling it here would
confound the one question this pilot exists to answer.

## Metrics

Primary — read-back on the same 40 clauses, both arms:

- `sufficient` (paired, McNemar) — the thing capacity should move.
- `unsupported` — the guard. More atoms mechanically create more opportunity to
  assert what the clause does not say.
- `faithful`.

Covariate, reported in every table without exception:

- realised `atoms_per_clause`, per arm.
- realised gloss chars/clause.
- truncated-batch count.

**A gain in `sufficient` that is not accompanied by its atom rate is not
reportable.** The cap existed to stop volume buying wins; removing it as a
constraint means the rate becomes something we must *show*, not something we
may omit.

### What this pilot CANNOT measure

**MCC.** Relevance MCC is defined over 589 passages × 9 behaviours. A 40-clause
subset cannot produce it. This pilot measures representation quality only.
Whether capacity helps *relevance* is a separate question answerable only after
a full-corpus run, and the capacity bound (+0.972 ceiling vs +0.555 bar) says
in advance that it probably will not move much. That is expected and is not a
failure of this pilot; conflating the two would repeat the project's signature
error in the other direction.

## Pre-registered predictions

Recorded before the run. Written to be wrong if they are wrong.

1. Arm B realised rate lands **3.5–5.0** atoms/clause. If it lands under 3.0 the
   prompt change did not take and the run is void — check the prompt diff, do
   not analyse.
2. `sufficient` improves in arm B, **0.16 → 0.25–0.40**. Below 0.22 counts as
   the capacity hypothesis failing.
3. `unsupported` gets **worse** in arm B — this is a cost, not a surprise, and
   the question is the exchange rate. Prediction: the gain in `sufficient`
   exceeds the loss in `faithful` by at least 2×. If it doesn't, capacity is a
   wash and the cap goes back.
4. The gain concentrates in the **conjoined-directive and enumeration** strata
   and NOT in `party`. If `party` loss moves materially, the taxonomy's feature
   attribution is wrong and everything built on it needs re-examining.
5. Discrimination (0.89) does **not** improve — it is already at its
   information-theoretic ceiling. Any apparent gain there is a bug.

## Cost

Annotation is the small half; read-back is billed per clause per arm.
Estimate via `preflight()` / `--dry-run` before any live call, and **do not
launch if the estimate exceeds $0.35 total.** `print_cost(est, live=True)`
raises `SystemExit` over budget; that guard is load-bearing here.

Order of operations, contiguous:

1. Adversarial review returns; fix anything positive.
2. Fence the new diagnostics in the anti-cheat `FORBIDDEN` set
   (`prep_hole_corpus.py`, `check_taxonomy.py`, `taxonomy_agreement.py`,
   `hole_rollup.py`) and confirm the suite still passes.
3. `--dry-run` both arms; record estimates.
4. Live arm A, then arm B.
5. Read-back both, paired.
6. Report with rates. Keep or revert per prediction 3.

## Reversion rule, stated in advance

If prediction 2 fails, the prompt budget language goes back verbatim and the
result is recorded as a negative in HANDOFF.md alongside the others. Raising
the budget is a hypothesis under test, not a decision already taken.
