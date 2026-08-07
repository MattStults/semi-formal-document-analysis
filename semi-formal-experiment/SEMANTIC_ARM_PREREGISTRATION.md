# PRE-REGISTRATION — the document-internal semantic arm

**Written 2026-08-06, BEFORE any number in this arm was computed.** Nothing below was
revised after measurement; the results file is separate
(`SEMANTIC_ARM_RESULTS.md`) and cites this one.

## The question this answers

`HANDOFF.md` closes both label-free leads and states that the residual
`+0.278 → +0.591` gap is not derivable from "anything the corpus supplies". That claim
rests on an **enumeration** — 54 re-weighting variants, eight passage priors, a regression
of the learned per-atom coefficient on five surface statistics (R² = 0.039) — and that
enumeration contains **no distributional semantics whatsoever**. `relevance.py:4` forbids
loading an embedding model by contract ("a query-time model call would just BE the
baseline we are trying to beat"), so the space was excluded by design, never measured.

Matt's objection, stated precisely: the near-injectivity of the atom index (534 classes
over 589 passages) shows the atoms *distinguish* the passages, and the supervised ceiling
shows a rule over them exists — but neither shows the **document cannot supply the rule**.
"There is more meaning in the document we have not mined" is compatible with every number
on record.

This arm tests exactly that, and only that.

## The two arms, and why this one runs first

| arm | semantic space built from | answers |
|---|---|---|
| **A — document-internal** (THIS ONE) | the spec's own text only; no external corpus | *Is the meaning in the document, unmined?* |
| B — pretrained | an off-the-shelf embedding carrying an outside corpus | *Did the knowledge come from outside?* |

Arm A is Matt's hypothesis and is therefore first. **Arm B now also runs** (amended
2026-08-06, still before any measurement): an `OPENAI_API_KEY` is present in `~/.zshrc`,
so B uses `text-embedding-3-small` rather than the ~1GB torch install first contemplated.
Estimated spend **≈ $0.003** at $0.02/1M tokens; logged to `spend.py`. The corpus sent is
OpenAI's own **public** Model Spec, so the send discloses nothing.

Running both arms is what makes the test discriminating: **A alone cannot license the
extra-document conclusion**, because a null in A is confounded with corpus size (see the
power caveat below). Only the A-null/B-positive *pattern* separates "the knowledge came
from outside" from "we lacked the data to learn it".

## Method

Semantic space: truncated SVD (LSA) over a TF-IDF term–document matrix built **only** from
this spec's own text. Atom vectors are the centroid of the text of the clauses each atom
appears on, plus the atom's gloss. Behaviour vectors are the behaviour name + definition
text. Dimensions swept k ∈ {25, 50, 100, 200}; no k is chosen on the panel — every k is
reported.

Four scorers, all label-free, all cut by Otsu (`threshold.PREFERRED`, zero free
parameters):

1. **exact (anchor)** — the shipped IDF-weighted exact atom-name match. Reproduces the
   published anchor; if it does not, the harness is wrong and nothing else is readable.
2. **soft-match** — `Σ_q max_{a ∈ passage} cos(q, a)`. Lets a passage atom that is *near*
   a query atom contribute, which exact matching cannot express. This is the specific
   thing an embedding buys that a re-weighting cannot.
3. **soft-match × IDF** — same, with the shipped IDF weight retained on the query atom.
4. **passage-text cosine** — `cos(behaviour text, passage text)` in LSA space, atoms not
   involved at all. The end-to-end "is there unmined meaning in the raw text" test.

Reported per scorer: mean MCC over the 9 (behaviour × pair-gold) cells at the Otsu cut,
**and** mean passage AUC. AUC is reported because it is threshold-free: a scorer can carry
real ranking signal and still lose on MCC purely to calibration, and conflating those is
the error this project already made once.

## Anchors on record (from `HANDOFF.md` / `weight_diag.py`)

| | MCC |
|---|---:|
| shipped label-free tool | +0.278 |
| best of 54 label-free re-weighting variants | ≈ +0.28 … +0.32 |
| tool at an ORACLE (unreachable) threshold | +0.396 |
| supervised readout of identical features | +0.591 |
| judges, mean / best-per-behaviour | +0.555 / +0.654 |

The gap under test is +0.278 → +0.591. The declared noise floor elsewhere in this project
is **0.045 MCC**.

## PREDICTIONS — frozen

1. **P1.** No document-internal scorer reaches +0.40 mean MCC. *(i.e. the arm does not
   close a meaningful share of the gap.)*
2. **P2.** The best soft-match scorer beats the exact anchor by **less than the 0.045 noise
   floor** on mean MCC.
3. **P3.** Passage-text cosine (scorer 4) **loses** to the exact anchor. Rationale: LSA over
   589 passages recovers topic structure, and topic structure is close to section identity,
   which was already shown to add nothing over the atom index.
4. **P4.** Mean AUC for the best soft-match variant lands within ±0.03 of the shipped
   ranking AUC (0.561 / 0.695 / 0.840 per behaviour, re-measured figures).
5. **P5.** Results are stable in sign across k ∈ {25, 50, 100, 200} — i.e. the conclusion is
   not a dimensionality artifact.

6. **P6 (Arm B).** The pretrained arm beats the document-internal arm on mean AUC — the
   external corpus buys a real notion of similarity that 589 passages cannot. But it still
   does **not** reach +0.40 mean MCC, because the residual is dominated by calibration and
   by the judge-specific share, neither of which an embedding addresses.

**What would falsify the extra-document reading:** any **document-internal** scorer clearing
**+0.40 mean MCC**, or beating the exact anchor by more than the 0.045 noise floor. That
would mean the meaning was in the document and merely unmined, and the `HANDOFF.md`
framing needs amending.

**What would confirm it:** Arm A flat against the exact anchor while Arm B clears the noise
floor. That localises the missing knowledge outside the document — and, per invariant 10,
still does not license shipping it.

**The outcome that settles nothing:** both arms flat. That is consistent with "no semantic
signal exists" *and* with "LSA and a general-purpose embedding are both too blunt", and must
be reported as inconclusive rather than as support for either reading.

## Standing hazards this arm must not trip

* **This is a one-shot diagnostic, not a progress metric.** The project has already
  withdrawn one lead ("raise annotation rank fidelity, use rho against the learned
  coefficients as a cheap offline progress signal") because iterating a design until it
  correlates with panel-fitted coefficients *is* fitting to the panel, one level of
  indirection out. Iterating k, the scorer family, or the vectorizer until MCC rises would
  be the same error. The sweep above is fixed here and reported in full, losers included.
* **Nothing in this arm may ship.** Contract invariant 10 permits statistical instruments
  as ceilings, never as the product. Even a positive result is a finding about
  *derivability*, not a licence for a dense channel in `relevance.py`.
* **Power caveat, stated up front.** 589 passages is thin for learning distributional
  structure. A null in Arm A is therefore **partly a power result**, and must be reported
  as "document-internal semantics at this corpus size did not close the gap" — never as
  "the document does not contain it".
