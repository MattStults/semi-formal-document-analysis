# RESULTS — the document-internal semantic arm

Measured 2026-08-06. Pre-registration: `SEMANTIC_ARM_PREREGISTRATION.md`, frozen before any
number below existed. Code: `semantic_arm.py`, `semantic_arm_ci.py`. Raw:
`semantic_arm_results.json`. Spend: **$0.00119** (arm B embeddings, 59,579 tokens).

## The question

`HANDOFF.md` states the residual `+0.278 → +0.591` is not derivable from "anything the
corpus supplies". That claim rested on an enumeration containing **no distributional
semantics** — the space was excluded by contract (`relevance.py:4`), never measured. Matt's
objection: near-injectivity and the supervised ceiling prove the atoms *distinguish* the
passages and that a rule exists, but neither shows the **document cannot supply that rule**.
"There is more meaning in the document we have not mined" was untested.

## Numbers

Mean over the 9 (behaviour × pair-gold) cells; MCC at the label-free Otsu cut.

| scorer | mean MCC | Δ vs anchor | mean AUC |
|---|---:|---:|---:|
| **ANCHOR — exact IDF over atom-name overlap** | **+0.293** | — | **0.723** |
| A / lsa-25 / soft-match | +0.192 | −0.101 | 0.743 |
| A / lsa-50 / soft-match | +0.210 | −0.083 | 0.741 |
| A / lsa-100 / soft-match | +0.209 | −0.084 | 0.745 |
| A / lsa-200 / soft-match | +0.226 | −0.067 | 0.743 |
| A / lsa-200 / soft-match × idf | +0.225 | −0.068 | 0.741 |
| A / lsa-200 / passage-text cosine | +0.092 | −0.200 | 0.583 |
| A / lsa-25 / passage-text cosine | +0.000 | −0.293 | 0.503 |
| B / openai / soft-match | +0.254 | −0.039 | **0.759** |
| B / openai / soft-match × idf | +0.249 | −0.044 | 0.756 |
| B / openai / passage-text cosine | +0.166 | −0.127 | 0.672 |

Paired bootstrap over passages, 2,000 draws, seed 20260806:

| contrast | ΔAUC | 95% CI | |
|---|---:|---|---|
| A (lsa-200) soft-match vs exact anchor | +0.020 | [−0.012, +0.053] | **spans zero** |
| B (openai) soft-match vs exact anchor | +0.035 | [+0.006, +0.064] | excludes zero |
| B (openai) vs A (lsa-200) | +0.015 | [−0.006, +0.038] | **spans zero** |

## Verdict against the frozen predictions

| | prediction | outcome |
|---|---|---|
| P1 | nothing reaches +0.40 mean MCC | **held** — best is +0.254 |
| P2 | soft-match beats anchor by < 0.045 MCC | **held**, and stronger than predicted: it *loses* by 0.039–0.101 |
| P3 | passage-text cosine loses to the anchor | **held** — loses by 0.127–0.293 |
| P4 | best soft-match AUC within ±0.03 of shipped | **FAILED for arm B** (+0.035, just outside). Held for arm A (+0.020). |
| P5 | stable in sign across k | **held** — all four k agree in sign and ordering |
| P6 | B beats A on AUC | **NOT ESTABLISHED** — point estimate +0.015, CI spans zero |

Two of six did not go as written, and both are recorded as they fell.

## What this establishes

**1. Matt's hypothesis gets a clean null — and it is the pre-registered falsification test
that did not fire.** Document-internal semantics was given the functional form the previous
54 variants could not express (soft matching, where a passage atom merely *near* a query
atom contributes) and its ranking gain is **+0.020 AUC, CI spanning zero**. On the decision
metric it does not merely fail to gain, it **loses 0.067–0.101 MCC**. The falsification bar
(+0.40 MCC, or beating the anchor by the 0.045 noise floor) was not approached from any
direction. On this evidence, "the meaning was in the document, unmined" does not survive.

**2. The extra-document reading gets weak, real, and badly insufficient support.** Arm B is
the only scorer whose ranking gain excludes zero (+0.035 AUC). That is knowledge from
outside this document improving a document-grounded task — the sign the extra-document
framing predicts. But it is a *ranking* gain of 0.035 AUC against an MCC gap of 0.313, and
it does not clear the decision metric at all.

**3. The pattern that would have been decisive did not fully materialise.** The
pre-registration named A-null/B-positive as the confirming outcome. Arm A is null and arm B
is positive against the anchor — **but B vs A directly spans zero**. So the two arms are not
statistically separated from each other, only from the anchor. The confirming pattern is
present in the point estimates and *not* established at the 95% level. Anyone citing this as
proof of the extra-document claim is over-reading it.

**4. A finding neither arm was built for: semantics helps RANKING and hurts DECIDING.** Both
arms beat the anchor on AUC while losing on MCC. That is this project's oldest theme — the
scorer "RANKS far better than it DECIDES" (`threshold.py`) — reappearing in a new channel:
soft matching flattens the score distribution, and Otsu, a distribution-shape rule, cuts a
flattened distribution worse. The semantic signal is real and the calibration eats it.

## What this does NOT establish

* **Not "the document does not contain it."** The power caveat was declared in advance and
  it binds: 589 passages is thin for LSA, so arm A's null is confounded with corpus size.
  The honest statement is **"document-internal semantics at this corpus size did not close
  the gap"**.
* **Not a licence to ship anything.** Contract §5 invariant 10 forbids a dense channel as
  the product regardless of these numbers. `semantic_arm` is registered in
  `test_no_reference_leak.FORBIDDEN`; no query module may reach it.
* **Not a general result about embeddings.** One LSA family and one general-purpose
  embedding were tried. A spec-domain embedding is untested and is *not* licensed as a next
  step — see the hazard below.

## Amendment owed to `HANDOFF.md`

The sentence "the learned weighting is **not a function of anything we compute**" (R² = 0.039
over five surface statistics) should be read as it was written: a statement about surface
statistics. It now has a genuine semantic arm behind it — which came out the same way — but
that arm is **one null and one 0.035-AUC positive**, not a proof. The `⭐⭐⭐⭐` section's
restated goal is untouched by this: it does not depend on the gap being unrecoverable.

## Hazards carried forward

* **Do not iterate this.** Sweeping embedding families, k, or scorer forms until MCC rises is
  the withdrawn `rho` lead one level out — fitting to the panel through a proxy. The sweep
  reported here was fixed in advance and is reported entire, losers included.
* **Accounting gap.** The $0.00119 is logged in `usage.jsonl` but prices as $0.00 in
  `spend.py`, which has no entry for `text-embedding-3-small`. Adding one would mean putting
  an embeddings endpoint into `providers.json`, a **chat-provider** registry whose entries
  carry `cache_mode`/`max_tokens` semantics that do not apply. Left unpriced deliberately;
  the row carries the true cost in its `note`.
* **Unreviewed.** Per AGENTS.md this needs a clean-context adversarial review before any of
  it is cited as settled. It has not had one.
