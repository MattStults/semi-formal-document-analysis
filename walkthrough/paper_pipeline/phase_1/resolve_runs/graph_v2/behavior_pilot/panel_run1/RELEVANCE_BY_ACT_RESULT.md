# RELEVANCE BY ASP — first result, 2026-08-18

The project owner's framing: without symbolic relevance, most of the pipeline was irrelevant. This
is the first measurement where the translated corpus is on the critical path
for relevance. Method: 720 bespoke act functors classified into 11 canonical
acts (act_bridges.lp, 718 bridges, generated beside the corpus); the three
behavior modules rewritten INTO the corpus vocabulary (modules_contract_v1,
0 validator breaches, 11 gaps recorded not invented); relevance = a module
asserts a deontic status on a canonical act the behavior performs. Static
read of assert heads through the bridges. **$0, deterministic, a stated
reason per hit.** Scored on the SAME held-out halves against the SAME Fable
truth as the seat.

| behavior | seat cold | seat tuned (best) | ASP relevance-by-act | recall / precision (ASP) |
|---|---|---|---|---|
| helpfulness | 0.67 | 0.65 | **0.73** | 0.75 / 0.94 |
| avoiding-over-and-under-caution | 0.64 | 0.67 | **0.67** | 0.73 / 0.76 |
| harm-avoidance-to-third-parties | 0.31 | 0.78 | 0.61 | 0.63 / 0.73 |

Findings:
* A first-pass generated ontology (with an admitted `respond` catch-all,
  195 functors) matches or beats the LLM seat on 2 of 3 behaviors, and beats
  BOTH seat columns on helpfulness. The corpus does the job.
* Harm-avoidance lags because its performed acts are the coarsest buckets
  (refuse/provide/act_in_world -> 282 modules engaged); ontology COARSENESS
  is now the measured lever. Splitting provide/respond (disclose,
  provide_hazard vs provide_information) is a classifier review, not new
  machinery.
* The two instruments are complementary by construction: symbolic gets the
  ACT and cannot see SCOPE (party, condition); the seat gets scope and
  cannot say why. Next number: the COMBINATION — symbolic first, seat only
  on the residue.
* Corpus vocabulary gaps surfaced by the rewrite (no declared name for
  'plausible benign reading', 'untrusted recipient', 'no good-cause
  exception', programmatic-output-as-case-fact …) are input-ontology
  findings — the situation-concept twin of the act problem.
