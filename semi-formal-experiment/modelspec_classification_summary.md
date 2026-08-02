# OpenAI Model Spec focus-area classification summary

Source: `external/model_spec/model_spec.md` (model_spec repo checkout, 4691 lines). Inventory: `modelspec_focus_areas.json`. Criteria identical to the constitution pass (`segmentation_summary.md`, 616 clauses).

**Total focus areas: 259** (all 259 unique `[^xxxx]` markers in the file)

## Marker structure

The `[^xxxx]` tokens are **inline anchors, not footnotes**. The file contains **zero** footnote-definition lines (`[^id]:`) — a scan of all 4691 lines finds none. Each marker sits immediately after the span of prose it labels (the rendered site turns each into a per-focus-area permalink), so the governing statement for a marker is the sentence it terminates or sits inside. All 259 markers occur in normative prose; **0** fall inside the `~~~`-fenced example conversation blocks.

## By kind

| kind | count | % |
|---|---|---|
| conditional | 174 | 67.2% |
| holistic | 68 | 26.3% |
| definitional | 15 | 5.8% |
| meta | 2 | 0.8% |

**Formalizable fraction (conditional): 67.2%** (71.9% conditional among the trigger-bearing vs weighing normative pool)

## By top-level section

| section | total | conditional | holistic | definitional | meta | % conditional |
|---|---|---|---|---|---|---|
| The chain of command | 62 | 42 | 13 | 6 | 1 | 67.7% |
| Stay in bounds | 76 | 61 | 11 | 4 | 0 | 80.3% |
| Seek the truth together | 40 | 27 | 8 | 4 | 1 | 67.5% |
| Do the best work | 30 | 22 | 7 | 1 | 0 | 73.3% |
| Use appropriate style | 51 | 22 | 29 | 0 | 0 | 43.1% |

## Modality distribution

Counted over the governing statement plus its bullet lead-in, so a focus area can carry more than one modality verb.

| modality verb | focus areas | % of 259 |
|---|---|---|
| should | 138 | 53.3% |
| (none) | 52 | 20.1% |
| may | 30 | 11.6% |
| should not | 26 | 10.0% |
| must | 15 | 5.8% |
| must not | 11 | 4.2% |
| may not | 4 | 1.5% |

Exact combinations:

| combination | count |
|---|---|
| should | 126 |
| (none) | 52 |
| may | 22 |
| should not | 19 |
| must | 15 |
| must not | 9 |
| should not+should | 6 |
| may not+may | 3 |
| should+may | 3 |
| must not+should | 2 |
| may not+should+may | 1 |
| should not+may | 1 |

## Defeasibility

**46 of 259 focus areas (17.8%) carry an explicit defeasibility marker** (`unless`, `by default`, `overrid`* covering override/overridden/overriding, `except`).

| marker | occurrences |
|---|---|
| unless | 18 |
| by default | 15 |
| except | 8 |
| overrid | 7 |

Authority level declared on the containing section heading (`{#id authority=...}`), inherited down the heading chain:

| authority | focus areas | % |
|---|---|---|
| root | 118 | 45.6% |
| guideline | 72 | 27.8% |
| user | 54 | 20.8% |
| system | 9 | 3.5% |
| developer | 5 | 1.9% |
| (none stated) | 1 | 0.4% |

## Side-by-side: Model Spec vs Anthropic constitution

| kind | Model Spec (n=259) | % | Constitution (n=616) | % | delta (pp) |
|---|---|---|---|---|---|
| conditional | 174 | 67.2% | 195 | 31.7% | +35.5 |
| holistic | 68 | 26.3% | 204 | 33.1% | -6.9 |
| definitional | 15 | 5.8% | 168 | 27.3% | -21.5 |
| meta | 2 | 0.8% | 49 | 8.0% | -7.2 |

Conditional (formalizable) share: **Model Spec 67.2%** vs **constitution 31.7%** — a +35.5 pp difference.

## Robustness: de-duplicated to distinct governing sentences

69 of the 259 markers are sub-sentence enumeration anchors sharing one governing sentence with siblings (23 sentences carry 2+ markers), e.g. `chemical[^91oh], biological[^bz0o], radiological[^li9q]`. Collapsing to the 213 distinct governing sentences:

| kind | count | % |
|---|---|---|
| conditional | 134 | 62.9% |
| holistic | 63 | 29.6% |
| definitional | 14 | 6.6% |
| meta | 2 | 0.9% |

Conditional share on this stricter unit: **62.9%** (vs 67.2% per-marker). The comparison to the constitution's 31.7% holds in either accounting.

## Verbatim verification

Every `text` field was checked as an exact substring of `model_spec.md`: **259/259 = 100.0% pass**. `marked_span` fields: 259/259 = 100.0%. Run `python classify_modelspec.py` to reproduce.

## Caveats

- Units are not comparable one-for-one: constitution units are segmented *clauses*; Model Spec units are the authors' own *focus areas*. 69 of the 259 markers are sub-sentence enumeration anchors that share one governing sentence with siblings, which inflates the conditional count wherever a crisp rule enumerates many items; see the de-duplicated table above.
- 0 focus areas were unclassifiable; every marker associated cleanly with a governing sentence.
- Four whole top-level sections carry no focus markers at all: Overview (lines 1-108), Definitions (109-170), the voice-mode subsections (`#voice_style` and children), and the Under-18 Principles (`#chatgpt_u18`). The last marker is at line 4251 of 4691.
