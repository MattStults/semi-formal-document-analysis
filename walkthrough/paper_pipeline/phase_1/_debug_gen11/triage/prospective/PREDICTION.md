# PROSPECTIVE PREDICTION — `HEDGE` on the 25 `opus_pairs` clauses

Written BEFORE any slice reported an outcome. Prediction only; no outcome column
was read. Scoring is a separate later step.

## Provenance of the predictor

`HEDGE` is imported from `_debug_gen11/triage/build.py` (`has_hedge`), unmodified.
Lexicon: by default · generally · typically · usually · unless · may want to ·
should be willing · in general · normally · tends to. Applied to the NARROWED
span via `build.span_parts`, exactly as in the originating run.

It was the only survivor of six candidates: in-sample rho +0.34, transfer +0.42
on 25 and +0.38 on the 20 non-overlapping, 6/6 hedged clauses edited against a
64% base rate, hypergeometric p = 0.045. One cell of six.

Two siblings died on transfer and bound the expectation here: `BORROWED` won
in-sample (rho +0.494, p = 0.043) and collapsed to +0.13; `FLOORDIRTY_T1` looked
strong at +0.46 and had ZERO variance on transfer because it measured the
pipeline generation rather than the clause.

## The prediction

n = 25. **`HEDGE` fires on 2.**

Predicted high-need subset: `l1001_1107_n008`, `l1108_1367_n008`.
Predicted low-need: the other 23.

Per-clause values and span lengths: `prediction.json`.

## Falsifier, carried over unchanged

rho < +0.30 against the primary outcome column, or failure to beat the random
top-k capture baseline.

## Outcome column, fixed in advance

Adjudication-free tier ONLY: measures computed by `_debug_gen11/arms_review/
measures.py` and `floor.py`, plus the licence-inheritance and self-citation
classes, which are recomputable in a few lines rather than taken on trust.

⛔ NOT the Opus verdict column. The independent review's correct/defective/unsure
split correlates with module size at rho -0.60 and is effectively a heading
detector; it cannot referee this.

## ⛔ THIS TEST IS UNDERPOWERED AND THAT IS KNOWN BEFORE SCORING

**Only 2 of 25 clauses are hedged.** A two-item positive cell cannot move a
correlation meaningfully and cannot beat a capture baseline with any margin.
Whatever this returns, it is not a replication. It is recorded because a
pre-registered miss is still informative and because scoring it later without
this file would be post-hoc.

## ⛔ THE COHORT IS CLUSTERED — a briefing error, recorded

Region counts: l1001_1107 = 11 · l1108_1367 = 10 · l1_170 = 1 · l831_1000 = 1 ·
l2821_3040 = 1 · l3954_4251 = 1.

**21 of 25 clauses come from two adjacent line ranges.** The coordinator's
instruction ("every 5th eligible node by sorted node-id") interleaves WITHIN a
region because the sorted id list is grouped by line range; it does not spread
across the document. Slice 4 read the instruction as five equal blocks of the
736 eligible nodes (`stride_indices` 0/36/73/110/146) and is the only slice with
corpus-wide spread.

Consequence: these 25 are a sample of TWO DOCUMENT REGIONS plus four scattered
clauses, not a sample of the corpus. Any recurrence finding from this run is
evidence about those regions until shown otherwise, and a low hedge rate may be
a property of the regions rather than of the document.

## What n supports

Nothing on its own. `HEDGE` is a lexical regex over English hedging phrases and
is DOCUMENT-TUNED; it would need a second document before it could be relied on
even if this cell were large.
