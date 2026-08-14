# K3 frontier-verdict validity report (ds7)

Investigation date: 2026-08-14. All offline — verdicts, queue, graph, and document read
from disk; zero API spend. Inputs: `runs/ds7/frontier_verdicts.json` (150 verdicts),
`runs/ds7/risk_queue.json`, `runs/ds7/root_graph.json`, `frontier_review.py`,
`rename_seat.py` (BRIEF), `specs/openai-model-spec/model_spec.md`.

## VERDICT: MIXED — trustworthy where the prompt carried evidence; rubber-stamp-by-construction where it did not

The 97% agreement is real and NOT explained by a lazy judge. It IS explained by two
things Matt's suspicion correctly smelled: (1) the near-miss queue is stuffed with
embedding noise, so "uphold the non-rename" is trivially correct 62 times; and (2) two
whole kinds (`dropped_merge`, largely `broken_promise`) were judged on prompts that
contain **no evidence at all**, so those verdicts are the brief's uncertainty-default
applied 61 times, not judgments.

Per-kind trust:

| kind | n | outcome | evidence in prompt | trust |
|---|---|---|---|---|
| dangling_near_miss | 64 | 62 uphold / 1 reject / 1 no_verdict | need name + candidate names + sims (NO node prose, NO quotes) | TRUSTWORTHY as judged; but the question it answers is nearly rhetorical (see §3) |
| seat_accepted_rename | 18 | 15 uphold / 2 reject | names + seat's grounds + where | TRUSTWORTHY — substantive, discriminating |
| low_sim_edge | 7 | 3 uphold / 2 reject / 2 no_verdict | need name + establishing prose | TRUSTWORTHY — the only kind with real per-item prose, and it split 3/2 |
| broken_promise | 45 | 40 reject / 1 uphold / 4 no_verdict | promised NAME + unwind path only | LOW-INFORMATION — name-shape heuristic + reject-default; safe direction (routes to humans) |
| dropped_merge | 16 | 16 uphold | node-id pair ONLY | RUBBER-STAMP-BY-CONSTRUCTION — zero information added |

## 1. Are the grounds substantive?

Sampled 21 verdicts stratified across kinds and decisions (idx 0, 1, 2, 3, 6, 7, 8, 18,
24, 25, 26, 27, 52, 59, 90, 96, 106, 113, 134, 135, 136, 137).

**Rename kinds: yes, substantive and evidence-specific.** The judge draws real semantic
distinctions, e.g. idx 18 (reject of seat rename `authority_level_ordering` ->
`information_hazards_prohibition`): "a precedence ordering among instructions ... whereas
... a substantive content rule barring detailed actionable guidance" — exactly right.
Idx 96 (reject `privileged_information_rule` -> `privileged_information`): rule-vs-object
distinction, defensible under the brief's "definition-vs-rule = two" ruling (mildly
over-strict under the facet doctrine; the safe direction — it reverts to an honest
dangling). Idx 6/7/8 upholds cite the facet doctrine correctly for
`transformation_exception` -> `transformation_exception_rule`. Idx 90 is the standout:
the ONE near-miss whose top candidate is genuinely the same concept
(`avoid_info_hazards` vs `information_hazards_prohibition`, the document's
`#avoid_info_hazards` section) — and the judge caught it and rejected (= proposed the
rename). One true positive in the haystack, found. That is discrimination, not stamping.

**dropped_merge: honest but empty.** All 16 grounds say, in varied words, "no node text
was supplied ... uncertainty defaults to upholding" (idx 134, 135, 136, 137 quoted in
full during review). The judge is transparently reporting it has nothing to judge with.
The 16/16 uphold row in the finale summary should be read as "16 defaults", not "16
confirmations". Same mechanism, opposite direction, for broken_promise: the prompt is a
bare name plus a path, and 40/45 grounds are variants of "substantively named concept +
no recorded evidence of delivery -> default reject" (38 distinct phrasings, but one
template thought). The one broken_promise uphold (idx 113, `no_agenda_section`) reasons
correctly from the name alone — but the name is genuinely all it had.

**Structural defect found:** `rename_seat.BRIEF` instructs the judge to "weigh the
passages' quoted text above the description phrasing" — and `frontier_review.item_prompt`
never sends any quoted text for near-misses (the risk_queue detail is names+sims only).
The brief promises evidence the prompt doesn't carry. Grounds are also stored truncated
at 400 chars (median 383).

## 2. Do any upheld near-misses look like true renames? My adjudication (5 items, against the document)

| idx | need vs top candidate | frontier | my call vs model_spec.md | agree? |
|---|---|---|---|---|
| 81 | `avoid_hedging_rule` vs `avoid_quantifying_uncertainty` | uphold | Doc L4251 (hedging/disclaimers, style section) and L~2830 (don't give percentage confidences) are different rules in different sections. different_concept | YES |
| 34 | `privileged_information_rule` vs `privacy_protection_rule` | uphold | Privacy = private info about people (L1001-1107); privileged = confidential system/dev content (#protect_privileged_information, L1799). different_concept | YES |
| 62 | `do_not_encourage_self_harm` vs `sexual_content_minors_prohibition` | uphold | Doc has a real `#do_not_encourage_self_harm` section (L1611); the candidate is obviously a different rule. different_concept | YES |
| 28 | `voice_style_guidelines` vs `advanced_voice_mode` | uphold | Scope-of-guidelines claim vs definition of a mode; related, not the same referent. different_concept | YES |
| 85 | `transformation_interactive_alert` vs `transformation_exception_rule` | uphold | The alert clause (doc L3243) is a distinct behavior from the restricted-content transformation exception (#transformation_exception). different_concept | YES |

Plus the near-miss reject idx 90: I agree (same referent, `#avoid_info_hazards`).
**Agreement: 6/6.** On the items the frontier saw, its answers match a document-grounded
adjudication.

## 3. Why 62/64 upheld: the candidate lists are embedding noise

Measured over all 64 near-miss items (`root_graph.json` provides vocabulary, name-token
Jaccard after stripping _rule/_principle/_section):

* Top-candidate similarity range is **saturated**: 0.848–0.952 across ALL 320 candidate
  slots (median top-1 = 0.895). The embedding space compresses everything to ~0.9.
* **0/64** items have ANY top-5 candidate sharing >= 0.3 name-token Jaccard with the
  need name. 48/64 top candidates share **zero** content tokens (e.g.
  `authority_level_ordering` -> `targeted_political_manipulation_prohibition` at 0.952,
  idx 27).
* Plausibly-true top candidate: **1/64** (idx 90 — the one the judge rejected).
  Clearly-wrong top candidate: ~60/64. Borderline: idx 59 (no_verdict), idx 81, 85.

So 62 upholds is the EXPECTED outcome of a discriminating judge on this queue: the
candidates really are wrong. The 97% is a property of the queue, not proof of a stamp —
but it also means the near-miss review bought little: it confirmed noise is noise.

## 4. The finding the K3 pass structurally cannot make (the real story behind the 64 danglings)

The near-miss review asks only "is the top-5 candidate the same concept?" It can never
notice that the dangling need has a TRUE resolution the retrieval missed:

* **~50/64 near-miss danglings name real document content.** The need names map to real
  spec anchors (`#do_not_encourage_self_harm`, `#avoid_info_hazards`,
  `#support_mental_health`, `#be_warm`, `#letter_and_spirit`, `#assume_objective_pov`,
  `#avoid_regulated_advice`, ... ) or real clauses (the 14 —
  fourteen — `interactive_vs_programmatic_setting` items all reference
  `#support_programmatic_use`, L3384). The establishing CONTENT exists as ds7 nodes
  (e.g. `L1542-1706_n013` "The assistant must not encourage or enable self-harm.";
  `L3383-3501_n001..n004` for interactive-vs-programmatic) — but those nodes export **no
  `provides` entry**, so the concept is absent from the resolution vocabulary. ds7 has
  only **92 distinct provides names for 773 nodes** (golden: 230 for 593). The danglings
  are honest per-item; in aggregate they are the shadow of a systematic **under-export
  defect**.
* **6/64 had an in-vocabulary true target that embedding top-5 missed** (retrieval
  recall failure, invisible to the judge): `privileged_information_rule` ->
  `privileged_information` (idx 34; when the seat separately proposed exactly this
  rename at idx 96 the frontier rejected it on rule-vs-object grounds),
  `ask_clarifying_questions_section` -> `ask_clarifying_questions_section_guideline_authority`
  (idx 39), and the 4 `authority_level_ordering` items whose true target
  `authority_levels_hierarchy` (provided by `L1-170_n042`) never appeared in any of
  their top-5 lists.

## 5. Parity 0%

10/10 decided pairs, band 0.4. Consistent with the seat-parity doctrine and with §3:
most sampled items have an obvious answer given (only) the evidence sent, so
frontier/flash agreement is cheap. It validates the seat on THIS evidence diet; it says
nothing about what richer evidence would change.

## Bottom line

* The frontier judge itself: **not a rubber stamp** — 6/6 agreement with my
  document-grounded adjudication, and it found the one real same-concept pair.
* The stage as designed: **MIXED** — `dropped_merge` (16 verdicts) and largely
  `broken_promise` (45) were judged evidence-free and should be treated as defaults,
  not confirmations; the near-miss slice mostly re-verified embedding noise.
* Actionable: (a) `item_prompt` should ship node prose/quotes for near-miss, dropped_merge
  and broken_promise kinds — the brief already assumes it; (b) the 64 "honest danglings"
  are mostly resolvable — ~50 need provides-exports on existing nodes, 6 need better
  retrieval — and that work belongs on the fixup queue, not another review round.
