# Independent certification of `runs/ds7/root_graph.production.json`

Second, independent pass over the corrected artifact. Fully offline, **$0 API spend**.
Date 2026-08-14. **Nothing under `runs/` was written or modified** — every check ran out of
loaded JSON in a scratch process; the one tool invocation (`graph_check.py`) was run on the
production file and its output read from stdout only (`graph_check` does not write).

Posture: this pass treats the corrections as **unverified**, because they were applied by the
coordinating instance rather than by an independent party, and because no script that applies
them exists in the repo (see C4).

Inputs: `runs/ds7/root_graph.json` (original accepted), `runs/ds7/root_graph.repaired.json`,
`runs/ds7/root_graph.production.json` (the candidate), `runs/ds7_production/*` (full battery),
`runs/ds7/promise_repair_report.json`, `recurse/root/graph.json` (golden),
`specs/openai-model-spec/model_spec.md`, `graph_compare.py`, `graph_check.py`,
`promise_repair.py`, `repaired_verification.md`, `delta_investigation.md`,
`opus_recheck_report.md`, `EXPERIMENTS.md`.

---

## HEADLINE VERDICT: **CERTIFIED-WITH-CONDITIONS**

The **resolution vocabulary is clean**. All 23 surviving `provides` exports were
re-adjudicated (12 in depth, 11 by span-text read) against the document and **I reject none
of them** — including the four the previous pass reserved or re-aimed. The three reverts were
each genuinely warranted; the re-aim is genuinely correct; the rename is genuinely the same
concept. Mechanical integrity is intact: 773 nodes, byte-identical id sequence, **0** spans /
establishes / quotes changed, 0 new duplicate providers, 0 provides or needs removed relative
to the original, coverage and `uncovered` byte-identical.

What blocks an unconditional stamp is **not** a false export. It is that the corrections were
**incomplete in two mechanical respects the prior verification itself named**, and both leave
a repair-fabricated `needs` claim in the graph:

* **C1 (must fix) — the R2 revert is half-done.** `L3877-3953_n012` still carries the
  splice-introduced need `assume_best_intentions_principle`.
* **C2 (must fix) — the R4 re-aim created a *new* self-loop** on `L4252-4482_n003`, in direct
  violation of `promise_repair.py`'s own FIX 3 contract.

Both are one-line, deterministic, $0 edits. With C1 and C2 applied the artifact is
unconditionally fit. C3–C6 are record-only.

---

# 1. THE CORRECTIONS

## 1a. Mechanical diff `repaired -> production`: exactly the intended 5 changes, nothing else

Whole-graph diff, canonical-JSON equality per node and per top-level key.

| property | result |
|---|---|
| node count | 773 -> 773 |
| node id sequence | **list-identical** |
| nodes differing | **6** (the 5 changes touch 6 nodes: the R4 pair is a move) |
| fields differing across all 773 | **`provides` (5 nodes), `needs` (1 node)** — nothing else |
| `spans` / `establishes` / `id` differing | **0 / 0 / 0** |
| top-level `uncovered`, `judgment_calls`, `dropped_merges`, `unwind_log`, `cross_link_report`, `rename_seat_verdicts`, `descend_near_misses`, `brief_sha`, `promise_repairs` | **all byte-identical to `repaired`** |
| top-level `driver_autofixes` | 30 -> 36 (+6, one provenance line per correction) |
| top-level `verification_corrections` | new, 6 entries |

`runs/ds7_production/root_graph.json` is **canonical-JSON identical** to
`runs/ds7/root_graph.production.json`, so the battery under `ds7_production/` is a battery on
the artifact under review.

The six differing nodes and the change on each:

| node | change |
|---|---|
| `L2126-2404_n031` | `provides` `[assume_objective_pov]` -> `[]` (revert) |
| `L3147-3238_n001` | `provides` `[user_authority_section_rules]` -> `[]` (revert) |
| `L3877-3953_n012` | `provides` `[assume_best_intentions_principle]` -> `[]` (revert) |
| `L4252-4482_n001` | `provides` loses `voice_style_guidelines`; keeps `standard_voice_mode`, `advanced_voice_mode` (its two original exports) |
| `L4252-4482_n003` | `provides` `[]` -> `[voice_style_guidelines]` (re-aim) |
| `L1707-1973_n024` | `needs` entry `privileged_information_definition` -> `privileged_information` (prose unchanged) |

**No sixth change, no collateral edit, no silent field touch.** Relative to the *original*
accepted graph, production differs on 25 nodes (`provides` 23, `needs` 9) and removes nothing.

## 1b. Were the three reverts genuinely wrong claims? — YES, all three

Read against `specs/openai-model-spec/model_spec.md`.

**R1 `assume_objective_pov` @ `L2126-2404_n031` (span L2151) — revert CORRECT, and it was the
worst of the four.**
* The document's heading is `### Assume an objective point of view {#assume_objective_pov authority=user}`
  (L2137) and its rule (L2139) is *"By default, the assistant should present information
  clearly, focusing on factual accuracy and reliability"*. The spliced prose asserted *"the
  assistant should **not** assume an objective point of view on contested topics"* — the
  **negation**.
* Independently: L2150 opens `!!! meta "Commentary"` and L2151 is inside that block; the
  node's own `establishes` begins *"The commentary states that…"*. A commentary line is not an
  instruction site under the graph's own policy.
* Post-revert the node's `provides` is `[]`, matching the original graph exactly.

**R2 `assume_best_intentions_principle` @ `L3877-3953_n012` (span L3937) — revert CORRECT.**
L3937 reads *"Users may say thank you in response to the assistant. The assistant should not
assume this is the end of the conversation."* The `#assume_best_intentions` section is at
**L610**, 3,300 lines away. The span establishes a conversational-sense rule and nothing about
best intentions. **But the revert is incomplete — see C1.**

**R3 `user_authority_section_rules` @ `L3147-3238_n001` (span L3152) — revert CORRECT.**
L3152 is *"The assistant should avoid making mistakes that would compromise the accuracy or
utility of its responses or any downstream actions."* The authority claim belongs to the
heading **L3150** (`## Avoid factual, reasoning, and formatting errors {#avoid_errors authority=user}`),
which no node covers. The spliced prose was also *generic* ("sections marked authority=user"),
against the graph's mandated per-section convention. Reverting is right; the honest fix is a
coverage fix at L3150, which this artifact does not attempt. Confirmed no residue: this node's
`needs` are identical to the original.

## 1c. Does `L4252-4482_n003` genuinely establish the voice-style claim? — YES

| | |
|---|---|
| node | `L4252-4482_n003`, span `[4260, 4260]` |
| span quote (verified verbatim substring of L4260) | *"The guidelines for content in this section apply to both systems, but instructions that discuss the nuances of audio or video inputs or outputs are only relevant to Advanced voice."* |
| node `establishes` | the same sentence, verbatim |
| spliced prose | *"The style guidelines in the voice_style section apply to both standard and advanced voice modes; instructions about audio/video nuances apply only to advanced voice."* |

The claim is inside the span, verbatim. `L4252-4482_n001`'s spans are L4255/L4257/L4258 and
contain no such sentence, so the original aim was provably one node off. **The re-aim is
correct**, and it converts a backward edge into a correct one: `n001` needs
`voice_style_guidelines` and is now resolved by `n003`. (The re-aim also introduces a defect
of its own — C2.)

## 1d. Is the renamed need's target genuinely provided, and genuinely the same concept? — YES

`L1707-1973_n024`'s need `privileged_information` resolves to `L1707-1973_n018`:

| | prose |
|---|---|
| the need (unchanged text) | *"What counts as privileged information: non-public OpenAI policies, system messages, hidden chain-of-thought messages, and private content provided by developer or user"* |
| `L1707-1973_n018` provides `privileged_information` | *"Information that is private or privileged, including non-public policies, system messages, hidden chain-of-thought, and private user/developer content."* |

Same enumeration, same referent, same section. Provider is unique (no duplicate). The name
`privileged_information_definition` no longer appears anywhere in the graph. **Rename correct
and complete.**

## 1e. What the corrections MISSED

The brief asked specifically about three items the verification named. All three were missed,
in whole or in part.

### (i) The 3 new self-loops — **2 of 3 still present; one of them was created by the correction itself**

Self-loop census (distinct `(node, name)` pairs where a node needs a name it provides):

| graph | distinct self-loops | repair-caused |
|---|---|---|
| original | 16 | — |
| repaired | 19 | 3 (`L3383-3501_n001`, `L3877-3953_n012`, `L4252-4482_n001`) |
| **production** | **18** | **2** (`L3383-3501_n001`, **`L4252-4482_n003`**) |

Only `L3877-3953_n012`'s loop was cleared, and only as a side effect of dropping its
`provides`. `L3383-3501_n001`'s survives (the prior pass called it harmless — I concur that
the *claim* is sound, but it is still a degenerate need). And the R4 re-aim did not remove the
self-loop; it **moved** it from `n001` to `n003`, because `n003` already needed
`voice_style_guidelines` and now also provides it.

This is not a matter of taste: `promise_repair.py` FIX 3 (docstring, and code at the splice
site) states *"a node cannot depend on itself. The name it now PROVIDES is dropped from its
own needs"*, and records `dropped_self_needs` per repair. **The correction bypassed the
module's own contract.** See C2.

Practical consequence: `voice_style_guidelines` has two needers, `n001` and `n003`; one is
the provider itself. Only **one** genuine dangling is resolved by this splice, not two.

### (ii) The 3 accept-with-reservation splices — **prose NOT tightened; all three unchanged**

Verification path step 5 ("tighten the three reservation proses so no entry claims more than
its span, and record the `no_agenda_section` name/referent mismatch") was not applied. Verbatim
in the production artifact:

| entry | span | the overreach, re-verified |
|---|---|---|
| `red_line_principles_section` @ `L1-170_n017` | L30 | prose says *"…including legal constraints and safety-critical information"*. Those referents are real but live at **L38** (safety-critical information) and **L40** (legal compliance) — **outside** the node's L30 span. The heading L28 is uncovered by any node, so L30 is the earliest admissible site. |
| `risk_taxonomy_section` @ `L1-170_n033` | L55 | prose's second clause *"describes the assistant's responsibilities in balancing empowerment and harm minimization"* corresponds to **L61** (*"a direct conflict between empowering the user and preventing harm"*) — outside the L55 span. |
| `no_agenda_section` @ `L609-698_n002` | L612 | L612 does state *"the assistant must not pursue its own agenda beyond helping the user"*, so the **content is right**. But `#no_agenda` is at **L2128** (confirmed by anchor grep), 1,516 lines away; L612 sits inside `#assume_best_intentions` (L610). A consumer resolving `no_agenda_section` lands on the clause, not the section. |

**Adjudication:** none of the three asserts anything the document contradicts, so none is a
*false* claim, and I do not reject them. Two are span-scope overreach in the prose; one is a
misleading name over a correct claim. They are recorded as C3 (record-and-tighten), not as a
blocker — consistent with the prior pass's disposition, which I independently reach.

### (iii) The mis-booked decline — **NOT corrected**

`runs/ds7/promise_repair_report.json` still reads `declined_honestly = 3` and
`danglings_after = 24`. Both are stale against the production artifact:

* `support_mental_health` was booked as an honest decline although the redraw's own reason
  ends *"I will add a provides entry to n007 for 'support_mental_health'"* and then did not —
  a **non-delivery**, per `promise_repair.py`'s own later `narration_mismatch` rule.
* the artifact's actual dangling count is **26**, not 24.

Graph-side this changes nothing (no wrong claim), but the production *package*'s own
provenance report misstates its two headline counts. See C5.

---

# 2. RE-ADJUDICATION OF THE SURVIVING SPLICES

The artifact carries **23** new `provides` entries relative to the original (26 spliced, 3
reverted; the re-aimed one counts once). I re-derived that set mechanically rather than
trusting the report. Below: a stratified sample of **12** re-adjudicated in depth against the
document — the 3 reserved, the 1 re-aimed, and 8 drawn to maximise failure probability (the
section-pointer names, the heading-node splice, the shared-line splices, the multi-clause
proses, the flagship). The remaining 11 were checked by reading their span line against their
prose; all are verbatim or near-verbatim restatements and are listed after the table.

Method, per entry: read the receiving node's span **line(s) in the document** and ask whether
that text establishes what the entry's `name` + `prose` assert. Name is judged separately from
claim.

| # | name | node / span | document text at the span | verdict |
|---|---|---|---|---|
| 1 | `red_line_principles_section` | `L1-170_n017` / L30 | *"Human safety and human rights are paramount to OpenAI's mission. We are committed to upholding the following high-level principles…"* | **ACCEPT (prose overreach).** Span establishes that a set of red-line principles follows. Prose's "legal constraints and safety-critical information" is true of the section (L38/L40) but outside the span. Not false; tighten. |
| 2 | `risk_taxonomy_section` | `L1-170_n033` / L55 | *"We consider three broad categories of risk, each with its own set of potential mitigations:"* | **ACCEPT (prose overreach).** Taxonomy established verbatim. Empowerment/harm clause is at L61, outside the span. Not false; tighten. |
| 3 | `no_agenda_section` | `L609-698_n002` / L612 | *"While the assistant must not pursue its own agenda beyond helping the user, or make strong assumptions about user goals…"* | **ACCEPT (name mismatch).** The claim is exact. The name promises a section that is actually at L2128. Not false; rename or re-point. |
| 4 | `voice_style_guidelines` | `L4252-4482_n003` / L4260 | *"The guidelines for content in this section apply to both systems, but instructions that discuss the nuances of audio or video inputs or outputs are only relevant to Advanced voice."* | **ACCEPT — the re-aim is right.** Claim verbatim in span. (Self-loop: C2.) |
| 5 | `do_not_facilitate_illicit_behavior` | `L1542-1706_n001` / L1543 | `### Do not facilitate or encourage illicit behavior {#do_not_facilitate_illicit_behavior authority=root}` | **ACCEPT.** A section-pointer name on the section's own heading node — the one shape where a `_section`-style name and its site coincide exactly. Its 0.0-similarity edge from `L4572-4692_n015` is a lexical artifact, not an error. |
| 6 | `interactive_vs_programmatic_setting` | `L3383-3501_n001` / L3386 | *"The assistant's behavior should vary depending on whether it's interacting with a human in real time or whether its output will be consumed programmatically…"* | **ACCEPT.** Verbatim. 14 needers, 13 of them genuine (one is the self-need — C2/C6). Highest-value splice in the set. |
| 7 | `avoid_overstepping` | `L3239-3382_n002` / L3241 | *"The assistant should help the developer and user by following explicit instructions and reasonably addressing implied intent (see …) without overstepping."* | **ACCEPT.** Line ends "without overstepping"; heading `#avoid_overstepping` is two lines above at L3239. The prose's word "section" is loose but the consumer lands inside the section. |
| 8 | `privileged_information_rule` | `L1707-1973_n024` / L1807 | L1807 contains *"The assistant must not disclose privileged content without permission…"* **and** *"It should also avoid confirming or denying the existence of confidential instructions…"* | **ACCEPT.** Both clauses of the prose are in the span. Node `establishes` covers only the second clause, but the span is the whole line and does establish both. |
| 9 | `instruction_conflict_surfacing_rule` | `L1707-1973_n025` / L1807 | same line, clause *"when higher-level instructions materially change how the assistant should respond… must not quietly apply those instructions in a way that would mislead the user…"* | **ACCEPT.** Two distinct exports off one dense line, each matched to a distinct clause; not a duplicate (different names, different referents, verified against the line). |
| 10 | `tool_call_sensitive_data_rule` | `L1707-1973_n030` / L1814 | *"For each tool call involving sensitive data, the assistant should assess: (i) the sensitivity and classification…; (ii) whether the recipient is trustworthy…; (iii) the tool's side effects; and (iv) whether sharing this information is within the agreed scope of autonomy or user intent"* | **ACCEPT.** All four prongs of the prose present verbatim. |
| 11 | `avoid_regulated_advice_rule` | `L1707-1973_n002` / L1710 | *"…the assistant should equip the user with information without providing definitive advice that would be best given by a licensed professional. A concise disclaimer should also be included…"* | **ACCEPT.** The prose's disclaimer clause — which the node's own `establishes` omits — **is** in the span at L1710. Correct. |
| 12 | `letter_and_spirit_section` | `L171-426_n029` / L294 | *"The assistant should consider not just the literal wording of instructions, but also the underlying intent and context…"* | **ACCEPT.** The section's (L292 `#letter_and_spirit`) first substantive claim; the letter/spirit distinction is stated verbatim. |

**Checked by span read, all ACCEPT (verbatim or near-verbatim):**
`unclear_cases_wait_rule` (L1475), `support_mental_health_rule` (L1753),
`recipient_identification_rule` (L1928), `transformation_no_unrequested_changes` (L3243),
`transformation_interactive_alert` (L3243), `creativity_principle` (L3321),
`no_unprompted_personal_comments_rule` (L3999), `avoid_condescension_rule` (L4052),
`no_repetition_rule` (L4204), `avoid_hedging_rule` (L4251),
`control_side_effects_section` (L529).

**Splices I reject: NONE.** 23/23 exports are claims their receiving spans support. The two
splices sharing L1807 and the two sharing L3243 were checked specifically for double-claiming
and are each matched to a distinct clause of a multi-clause line.

Note on `transformation_*`: both are aimed at L3243, which contains both the
no-unrequested-changes rule and the interactive-alert rule verbatim, and the two names are
matched to the two clauses correctly. No conflation.

---

# 3. WHOLE-ARTIFACT INTEGRITY (recomputed from scratch, not inherited)

| check | result |
|---|---|
| node count vs original | 773 -> 773 |
| node ids **and order** vs original | list-identical |
| nodes added / removed | 0 / 0 |
| `spans` differing on any node vs original | **0** |
| `establishes` differing on any node vs original | **0** |
| span `quote` strings | unchanged (contained in `spans`; 0 differences) |
| `graph_check` (re-run on the production file) | **0 bad line ranges / 846 spans; 0 bad quotes / 602**; 0 nodes covering 0 lines; 0 nodes >100 lines |
| `provides` entries **removed** vs original | **0** — purely additive/reverting |
| `needs` entries **removed** vs original | **0** |
| duplicate provider names | **6**, all pre-existing: `guideline_authority` 13, `root_authority` 11, `user_authority` 11, `system_authority` 4, `developer_authority` 3 (all protocol-mandated), `conversational_language_examples` 3 (pre-existing three-way shard). **0 new** |
| duplicate `provides` entries within a node | **0** |
| duplicate `needs` entries within a node | 1, `L1-170_n042` needs `authority_levels_hierarchy` twice — **pre-existing in the original**, untouched by repair or correction |
| self-loops | **18 distinct** (17 before, 16 in the original by distinct-pair count once `n042`'s duplicate is collapsed); **2 repair/correction-caused**: `L3383-3501_n001`, `L4252-4482_n003`. **This fails a strict "no self-loops" test.** See C2/C6. |
| danglings | **26 needers / 15 names**, all enumerated by `graph_check` and reproduced independently. 66 -> 26 vs the original. |
| every need resolves or is an enumerated dangling | **YES** — 1088 need entries; 1062 resolve to a provider, 26 are the enumerated danglings; no unaccounted need |
| `uncovered` set | **byte-identical** to original and to repaired (733 entries; 92 declared uncovered lines; 3638/3722 non-blank lines covered; unaccounted 0) |
| exported distinct names | 92 (orig) -> 118 (repaired) -> **115** (production) |
| nodes with empty `provides` | 644 -> **622** |
| staged copy `ds7_production/root_graph.json` | canonical-JSON identical to the candidate |

**Modal adjudication — the 6 drifted nodes, present and accounted.**
`runs/ds7_production/modal_adjudication.json`: 45 rows, 39 `preserved`, **6 `drifted`**. All 6
ids exist in the production graph; all 6 have **empty `provides`**; **none** was touched by the
repair or the corrections (byte-identical to the original graph). So modal drift is fully
orthogonal to the splice work — it is inherited ds7 state, not a repair regression.

| drifted node | span | drift |
|---|---|---|
| `L2555-2652_n001` | 2556, 2558–2574 | strengthened: `establishes` adds "must not lie" where the span only labels a white lie "over the line" |
| `L2555-2652_n002` | 2578 | strengthened: span describes sycophancy as a concern; `establishes` says "must not be sycophantic" |
| `L2821-3040_n026` | 2945, 2947–2965 | flattened: span "you may want to double check" -> `establishes` "should flag" |
| `L2821-3040_n035` | 3018, 3020–3039 | weakened/flattened: span "might"/"suggesting" -> `establishes` "should" |
| `L4572-4692_n008` | 4584 | strengthened: teen-safety "don't condescend" -> "must not" (×3 strong modals) |
| `L4572-4692_n009` | 4585 | strengthened: teen-safety "Be transparent" -> "must" |

Two of the six (`L4572-4692_n008/n009`) are **teen-safety** obligations whose strength was
raised by the graph. That is a translation-relevant finding — see §5 and C6.

---

# 4. THE DELTA vs GOLDEN

Recomputed directly with `graph_compare.build_edges` / `match_edges` against
`recurse/root/graph.json`, not read off the report.

## 4a. Headline

| filter | original | repaired | **production** |
|---|---|---|---|
| all names — a / b / recall / precision | 512 / 5774 / 0.3691 / 0.0504 | 512 / 5847 / 0.4395 / 0.0558 | 512 / **5845** / **0.4395** / **0.0558** |
| authority names excluded | 402 / 420 / 0.1766 / 0.1762 | 402 / 471 / 0.2637 / 0.2272 | 402 / **469** / **0.2637** / **0.2281** |
| + `assistant_definition` excluded (content only) | 402 / 196 / 0.1766 / 0.3776 | 402 / 242 / 0.2637 / 0.4421 | 402 / **240** / **0.2637** / **0.4458** |

`runs/ds7_production/postbuild_compare_vs_golden.txt` reports recall 0.4395 / precision 0.0558
/ uncovered jaccard 0.4954 / 1:1 486 / misaligned 91-272 — **all reproduce exactly**.

The corrections cost **2 content edges** (240 vs 242): one each from `assume_objective_pov` and
`assume_best_intentions_principle`. `user_authority_section_rules` had **zero** needers, so
reverting it cost nothing — worth recording, because it means R3's splice was a pure coinage
that resolved no dangling at all.

**No golden coverage was lost by the corrections.** Unmatched golden edges (all names): 323
(original) -> 287 (repaired) -> **287 (production)**; the production unmatched set is
**identical to repaired's** and a **strict subset of the original's**. Nothing regressed.

Edge denominator composition (production): authority 5,376 (92.0%), `assistant_definition` 229
(3.9%), **content 240 (4.1%)**. Golden: content 402, authority 110. So **95.9% of the raw
precision denominator is the documented authority/name fan-out artifact**, unchanged by both
the repair and the corrections.

## 4b. Is every remaining difference explained by the recorded causes? — YES

| component | disposition | evidence this pass |
|---|---|---|
| authority + `assistant_definition` fan-out, 95.9% of the denominator | **MEASUREMENT artifact** over a **BENIGN-BY-PROTOCOL** convention (`authority_convention.md`; the F4 authority-collapse was never built) | recomputed bucket census; authority edges moved 5,354 -> 5,376 across the whole repair, i.e. the repair did not feed the artifact |
| granularity / misalignment (773 vs 593 nodes, 91/272 misaligned) | **BENIGN-BY-PROTOCOL** + comparator 2–3-node windowing | `alignment` and `line_mass` byte-identical original/repaired/production — the splice cannot move a node metric, and did not |
| uncovered jaccard 0.4954 | **BENIGN-BY-PROTOCOL** (~98% coverage policy: blank lines, admonition markers, headings, example markup) + ~5 real lines | `uncovered` byte-identical across all three graphs; `only_a` 38 / `only_b` 279 unchanged |
| golden-side quirks (58 never-needed exports, 28 per-section authority coinages) | **GOLDEN defects** | consistent with the prior pass; honest comparison is ~101 vs ~153 load-bearing content names |
| **content-edge under-export** | **REAL ds7 DEFECT, reduced not eliminated** | 240 vs golden's 402; **296 of golden's 402 content edges unmatched** |

**Nothing NEW appeared.** Every production-side number is either identical to the repaired
graph's or moves by the exact amount the three reverts predict. The `edge_similarity` low-sim
set is 8/1062 (0.75%), the same 8 as the repaired graph, and the one new member
(`L4572-4692_n015 --[do_not_facilitate_illicit_behavior]--> L1542-1706_n001`, sim 0.0) I
independently adjudicate as **semantically correct** (appendix rule -> the section heading it
paraphrases); its similarity is 0 because there is no shared token.

## 4c. Is the under-export residue enumerable? — YES. The biggest gaps, by name

Unmatched golden **content** edges: **296 of 402**. Top residues by golden need-name:

| golden need-name | unmatched edges |
|---|---|
| `objective_truth_seeking` | 19 |
| `disallowed_content_categories` | 8 |
| `do_not_facilitate_illicit_behavior` | 8 |
| `do_not_encourage_self_harm` | 8 |
| `best_intentions_bias` | 7 |
| `stay_in_bounds_principles` | 7 |
| `real_world_ties_principle` | 6 |
| `user_perspective_spectrum_permission` | 6 |
| `risk_vs_asking_balance` | 6 |
| `trivial_vs_wrong_assumption_tradeoff` | 6 |
| `voice_turn_taking_rule` | 6 |
| `extremism_prohibition`, `hateful_content_prohibition`, `prevent_imminent_real_world_harm`, `privileged_information_categories`, `love_humanity_principle`, `conversational_sense_principle` | 5 each |

Caveat worth recording: `do_not_facilitate_illicit_behavior` appears here with 8 unmatched
edges **even though production now exports it** — the comparator matches on line *regions*, and
golden attaches the concept to different regions. Part of this residue is therefore the same
granularity artifact, not pure under-export.

The 15 dangling names (26 needers) split as the prior pass predicted:
**content present under another name (resolvable at $0 by aliasing)** —
`authority_level_ordering` (5, = `authority_levels_hierarchy`), `avoid_info_hazards` (3, =
`information_hazards_prohibition`), `objective_point_of_view` (2), `ask_clarifying_questions_section` (1),
`sexual_content_involving_minors_section` (1, deliberately skipped under the B3 contract),
`assume_best_intentions` (1), `support_mental_health` (1), `letter_and_spirit_principle` (1),
`assume_objective_pov` (1, restored by the R1 revert — the honest state);
**genuinely under-exported sections** — `do_not_encourage_self_harm` (3), `be_warm_rule` (2),
`avoid_errors_rule` (1), `be_thorough_but_efficient_rule` (1), `respect_real_world_ties` (1);
**repair residue** — `assume_best_intentions_principle` (2, one of which is bogus: C1).

Sections ≥30 lines with **zero** content exports remain the enumerable scope of any follow-on
pass: `#do_not_lie`, `#avoid_errors`, `#avoid_sycophancy`, `#respect_real_world_ties`,
`#no_topic_off_limits`, `#uphold_fairness`, `#be_professional`, `#do_not_encourage_self_harm`,
`#present_perspectives`, `#imitate_accents_in_voice_mode`, `#handle_interruptions_in_voice_mode`.

---

# 5. FITNESS FOR PURPOSE (translation + behavior matching)

**Wrong provides feeding wrong ASP predicates.** This was the acute risk and it is **closed**.
The graph's resolution vocabulary is 115 names over 23 audited additions with **0 rejected**.
The single most dangerous item — an export asserting the *negation* of `#assume_objective_pov`
on a commentary line — is gone, and the concept is back to an honest dangling
(`L2405-2473_n011 needs assume_objective_pov`), which fails loudly rather than translating a
false rule. No predicate in the production vocabulary is derived from a span that does not
support it.

**Danglings silently dropping edges.** 26 danglings, every one enumerated by `graph_check` and
reproduced independently here. They are *enumerated*, not silent — provided the translation
driver treats an unresolved need as a hard reportable rather than a no-op. **That property must
be asserted by the consumer** (C6). Two of the 26 are safety-weighted:
`do_not_encourage_self_harm` (3 needers) and `respect_real_world_ties` (1) reference sections
where ds7 exports nothing; the claims exist as nodes, so nothing is lost from the document, but
the cross-link will not form.

**The one bogus dependency.** C1's leftover need makes `L3877-3953_n012` (the "thank you" rule)
declare a dependency on `assume_best_intentions_principle`. It currently dangles, so it emits
no edge — but if the follow-on aliasing pass resolves `assume_best_intentions_principle` to the
real principle at L610, this fabricated dependency **silently becomes a real edge** and a false
premise in behavior matching. This is precisely why it must be dropped now rather than recorded.

**Self-loops.** 2 repair/correction-caused self-loops. A node that needs what it provides
produces a self-referential ASP edge; depending on the encoder that is either a no-op or a
trivial cycle. Neither is a *content* error, but both violate the repo's own stated contract
and should be cleared for the same reason the contract exists.

**Modal drift in nodes likely to be translated.** 6 nodes carry adjudicated obligation-strength
drift (~0.8% of nodes, the same rate as ds6). Four of the six are worked-example nodes; **two
are teen-safety rules** (`L4572-4692_n008/n009`) where the graph reads `must`/`must not` for
document text that says `don't` / `Be transparent`. Behavior matching against those two nodes
will over-trigger on obligation strength. They are flagged, in the risk queue (`modal_drift`
6), and none carries a `provides` entry — so they cannot propagate through the resolution
vocabulary, only through their own `establishes`. Acceptable **if carried forward as a known
list** (C6).

**Battery status (production run):** `graph_check` OK (0 bad spans, 0 bad quotes),
`sweep_headings` 1 flag (`modal_in_heading`, pre-existing), `sweep_modals` 45 flags -> 6
adjudicated drift, `risk_queue` 168 items, `edge_similarity` 8/1062 <0.10 (0.75%),
`repair_census` 0 buried failures.

**Fitness call: FIT for translation and behavior matching once C1 and C2 are applied.** No
defect in the artifact corrupts a translation output today; C1 is a latent corruption that
activates on the *next* repair pass, and C2 is a contract violation with a benign present
effect.

---

# CONDITIONS

## Must fix before the production stamp (both $0, deterministic, one line each)

**C1 — complete the R2 revert.** Drop the repair-introduced need
`assume_best_intentions_principle` from `L3877-3953_n012`. It was added by the splice (the
original node did not have it), it asserts a dependency the span does not support, and it is
one of the two needers keeping that name dangling. After: danglings 26 -> 25;
`assume_best_intentions_principle` keeps its one legitimate needer `L3041-3146_n002`.
*(For contrast, R1's other residue — the `user_authority` need added to `L2126-2404_n031` — is
CORRECT and should stay: L2151 sits under `#assume_objective_pov authority=user`. R3 left no
residue at all.)*

**C2 — clear the self-loop the re-aim created.** Drop `voice_style_guidelines` from
`L4252-4482_n003`'s own `needs`, per `promise_repair.py` FIX 3. After: self-loops 18 -> 17,
repair-caused 2 -> 1; `voice_style_guidelines` retains its one genuine needer `L4252-4482_n001`.
Consider clearing `L3383-3501_n001`'s self-need on `interactive_vs_programmatic_setting` in the
same edit (13 genuine needers remain); it is harmless but is the last repair-caused loop.

## Record, do not fix now

**C3 — the three reservation proses were not tightened.** `red_line_principles_section` and
`risk_taxonomy_section` claim more than their spans; `no_agenda_section` is a correct claim
under a name pointing 1,516 lines away from `#no_agenda` (L2128). None is false. Record the
name/referent mismatch explicitly so a downstream consumer does not read `no_agenda_section` as
a section pointer.

**C4 — the corrections have no reproducible artifact.** No script in the repo applies them;
`verification_corrections` and the six `driver_autofixes` lines are the entire record, and
`grep` finds the strings only in the artifact and `EXPERIMENTS.md`. Per `REPRODUCIBILITY.md`
this is a process gap: the artifact cannot be regenerated from the repaired graph by a
committed, re-runnable step. I verified the *outcome* is exactly right; I could not verify the
*process*. Commit the corrections script (or fold C1/C2 and the reverts into a single recorded
`apply_verification_corrections.py`) before the stamp.

**C5 — `promise_repair_report.json` is stale.** It still reads `declined_honestly = 3` (should
be 2 — `support_mental_health` is a non-delivery, by the module's own later
`narration_mismatch` rule) and `danglings_after = 24` (the artifact has 26). Graph-side this
changes nothing; package-side it misstates two headline counts.

**C6 — consumer-side assertions for the translation run.** (a) an unresolved need must be a
hard reportable, not a no-op, so the 26 enumerated danglings cannot silently drop edges;
(b) carry the 6 `modal_drift` nodes forward as a known list, with `L4572-4692_n008/n009`
(teen-safety, `don't`/`Be transparent` read as `must`) called out; (c) the honest edge numbers
for the package are the authority-excluded pair **recall 0.264 / precision 0.446**, not the
raw 0.4395 / 0.0558.

---

# VERDICT

**CERTIFIED-WITH-CONDITIONS.**

* The five corrections are **exactly** the five intended, on six nodes, with **zero**
  collateral change. Each is independently verified **correct** against the document: the three
  reverts removed genuine false or unsupported claims, the re-aim lands on the node whose span
  contains the claim verbatim, and the rename targets a genuinely provided, genuinely identical
  concept.
* **I reject none of the 23 surviving splices.** Re-adjudicated 12 in depth and 11 by span
  read; every export is supported by its receiving span.
* Whole-artifact integrity holds independently of the prior pass: 773 nodes, identical ids,
  0 span/establishes/quote changes, 0 new duplicate providers, 0 removals, identical
  `uncovered`, every need resolved or enumerated, `graph_check` clean.
* The delta vs golden is fully explained by the three recorded causes, contains **nothing new**,
  and the under-export residue is enumerable by name and by section.
* **What the corrections missed:** all three items the verification named — 2 of 3 self-loops
  (one of which the correction itself created), the 3 reservation proses (untouched), and the
  mis-booked decline (untouched). Two of these leave repair-fabricated `needs` claims in the
  graph and are the conditions C1/C2.

**Apply C1 and C2 (and, per C4, commit the script that applies them) and this artifact is fit
to be the production graph.** As it stands today it would not corrupt a translation run — but
C1 is a latent corruption that activates the moment a follow-on aliasing pass resolves
`assume_best_intentions_principle`, and the repo's own standard is that a repair does not leave
claims it cannot defend.

---

# CLOSURE ADDENDUM — conditions applied, verdict converted

Re-verified after `graph_corrections.py` (new, committed at `5a95279`) was written and the
artifact regenerated. Same posture: independent, offline, $0, nothing under `runs/` written
(all trial runs wrote to scratch; `runs/ds7/root_graph.production.json` and
`runs/ds7_production/root_graph.json` mtimes unchanged at 16:13/16:14).

## (1) The diff is exactly the corrections plus C1/C2 — confirmed

`repaired -> production` now touches **6 nodes / 9 field changes**, and every one is a named
correction:

| node.field | change | correction |
|---|---|---|
| `L2126-2404_n031.provides` | `[assume_objective_pov]` -> `[]` | R1 revert |
| `L3147-3238_n001.provides` | `[user_authority_section_rules]` -> `[]` | R3 revert |
| `L3877-3953_n012.provides` | `[assume_best_intentions_principle]` -> `[]` | R2 revert |
| `L3877-3953_n012.needs` | drops `assume_best_intentions_principle` | **C1** |
| `L4252-4482_n001.provides` | drops `voice_style_guidelines` | R4 (from) |
| `L4252-4482_n003.provides` | `[]` -> `[voice_style_guidelines]` | R4 (to) |
| `L4252-4482_n003.needs` | drops `voice_style_guidelines` | **C2** |
| `L3383-3501_n001.needs` | drops `interactive_vs_programmatic_setting` | **C2** (second repair-introduced loop) |
| `L1707-1973_n024.needs` | `privileged_information_definition` -> `privileged_information` | rename |

Nothing else. Every other top-level key is byte-identical to `repaired`
(`uncovered`, `judgment_calls`, `dropped_merges`, `promise_repairs`, `unwind_log`,
`cross_link_report`, `rename_seat_verdicts`, `descend_near_misses`, `brief_sha`);
`driver_autofixes` 30 -> 38 (+8, one line per correction) and `verification_corrections`
carries the same 8 with grounds. Against the **original**: `spans` 0 changed, `establishes` 0
changed, `id` 0 changed, node ids list-identical, 773 nodes, **0 provides entries removed**,
and the only `needs` names removed are the two repair-introduced self-needs.

## (2) C1 and C2 correctly and completely applied — confirmed, no third leftover

* **C1.** `L3877-3953_n012.needs` = `[assistant_definition, user_authority]` — the fabricated
  dependency is gone, and the two remaining needs are original. `assume_best_intentions_principle`
  now has exactly **one** needer, the legitimate `L3041-3146_n002`.
* **C2.** `L4252-4482_n003` provides `voice_style_guidelines` and no longer needs it; its one
  genuine needer `L4252-4482_n001` still resolves. `L3383-3501_n001` likewise: 13 genuine
  needers remain (14 -> 13, the dropped one being itself).
* **No third leftover of the same class.** I re-derived every `needs` entry added by the repair
  and checked each against its receiving node. Of the 14, the 3 problematic ones are now all
  disposed (C1 + the two self-needs); the remaining 11 are `assistant_definition` (×5),
  `conversation_definition` (×2), `root_authority`, `privileged_information` (renamed), and
  `user_authority` on `L2126-2404_n031` — which is **correct** and should stay, since L2151 sits
  under `#assume_objective_pov authority=user`.

## (3) The self-loop scoping is right and complete — confirmed, and the near-miss catch was correct

| graph | self-loop entries | distinct pairs |
|---|---|---|
| original (baseline) | 17 | **16** |
| repaired | 20 | 19 |
| **production** | **17** | **16** |

* production's self-loop set is **set-equal to the original's** (`set(prod) == set(orig)` -> True);
* **repair-introduced remaining: 0**;
* **pre-existing wrongly removed: 0**;
* the sorted **entry list** is identical too, so `L1-170_n042`'s pre-existing *duplicate*
  `authority_levels_hierarchy` need entry (17 entries vs 16 distinct pairs) survives intact —
  the sweep did not silently deduplicate accepted content either.

The near-miss was real and the catch was right: a general sweep would have deleted 16
never-adjudicated needs from the accepted graph, which is exactly the class of unadjudicated
edit the repo's rules forbid. The baseline-scoped implementation in `apply(g, baseline=...)`
is the correct fix, and `main()` loads the baseline from `HERE/runs/ds7/root_graph.json`
unconditionally — the scoping cannot be lost by forgetting an argument.

## (4) The preconditions genuinely refuse — verified by execution, four ways

All runs directed at scratch outputs; no `runs/` write.

| trial | result |
|---|---|
| run against the **original** `root_graph.json` | `precondition failed: assume_objective_pov not on L2126-2404_n031`, **exit 1**, no output written |
| run against the **already-corrected** production graph (double-apply) | same refusal, **exit 1** — the script is not silently idempotent, it refuses |
| mutated input: `L4252-4482_n003` span moved off L4260 | `precondition failed: L4252-4482_n003 does not cover L4260`, **exit 1** |
| mutated input: `privileged_information` removed from `L1707-1973_n018` | `precondition failed: privileged_information is not provided`, **exit 1** |

Each guard is a hard `SystemExit` before any write, and the revert/drop guards check
*cardinality* (`before - 1`, `len != before`) rather than merely filtering, so a name that is
absent cannot pass as a no-op. **C4 is closed**: rerunning the script on
`root_graph.repaired.json` reproduces `root_graph.production.json` **byte-for-byte** (verified
by byte comparison, not just canonical-JSON equality).

## (5) Post-correction state re-measured

| | value |
|---|---|
| nodes / exported names / needs | 773 / **115** / **1085** |
| danglings | **25 needers / 15 names** (was 26/15; C1 removed one) — all enumerated by `graph_check` |
| self-loops | **16 distinct**, all pre-existing |
| `graph_check` | 0 bad line ranges / 846 spans; **0 bad quotes / 602**; 0 zero-line nodes |
| duplicate providers | the same 6 pre-existing names; **0 new**; 0 duplicate entries within a node |
| `uncovered` | byte-identical to the original |
| recall vs golden (all names / content-only) | **0.4395 / 0.2637 — unchanged**; precision 0.0558 / **0.4496** (up from 0.4458) |
| content edges | 238 (was 240; the 2 dropped are the two degenerate self-edges) |
| battery | `edge_similarity` 8/1060 <0.10 (0.75%); `risk_queue` 168; `modal_adjudication` 45 rows / 6 drifted; `repair_census` 0 buried failures; staged copy canonical-JSON identical to the candidate |

**Recall is identical to four decimal places on both the raw and content-only measures**, which
is the load-bearing check: dropping the two self-edges removed no golden coverage. Precision
rose. Nothing else moved.

## Converted verdict

**CERTIFIED.** `runs/ds7/root_graph.production.json` is fit to be the production graph for a
full-corpus translation run and downstream behavior matching. C1, C2 and C4 are closed; the
self-loop scoping is verified correct and complete.

Nothing further must change before the translation run. Three items remain open as **recorded
follow-ups, not gates**:

* **C3** — the three reservation proses (`red_line_principles_section`, `risk_taxonomy_section`
  span-scope overreach; `no_agenda_section` name pointing 1,516 lines from `#no_agenda` at
  L2128). None is a false claim; tighten in the next bounded pass.
* **C5** — `promise_repair_report.json` is stale (`declined_honestly = 3` should be 2;
  `danglings_after = 24` should be 25). Package bookkeeping only; the graph is unaffected.
* **C6** — consumer-side assertions for the run: an unresolved need must be a hard reportable
  so the 25 enumerated danglings cannot silently drop edges; carry the 6 `modal_drift` nodes
  forward as a known list, with the two teen-safety nodes `L4572-4692_n008/n009` called out;
  and report the authority-excluded pair **recall 0.264 / precision 0.450** as the honest edge
  numbers rather than the plumbing-dominated raw pair.
