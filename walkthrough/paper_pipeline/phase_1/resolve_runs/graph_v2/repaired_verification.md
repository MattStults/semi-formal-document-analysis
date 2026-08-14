# Verification of `runs/ds7/root_graph.repaired.json`

Two-part verification of the promise-repair output. Fully offline, **$0 API spend**.
Date 2026-08-14. Nothing under `runs/` was written or modified (verified read-only:
all analysis ran out of loaded JSON in a scratch process).

Inputs: `runs/ds7/root_graph.json` (original, accepted), `runs/ds7/root_graph.repaired.json`,
`runs/ds7_repaired/{root_graph,compare_vs_golden,edge_similarity}.json`,
`runs/ds7/{compare_vs_golden,edge_similarity,promise_repair_report}.json`,
`recurse/root/graph.json` (golden), `graph_compare.py`,
`specs/openai-model-spec/model_spec.md`, `delta_investigation.md`,
`opus_recheck_report.md`, `promise_repair.py`.

**HEADLINE VERDICT: NOT FIT for production as-is.** 22 of 26 splices are sound and the
delta moves exactly as `delta_investigation.md` cause 3 predicted. **4 splices are wrong
claims** and must be reverted or re-aimed before the production stamp; one of them
(`assume_objective_pov`) asserts the *negation* of the document's principle. Details in
§1b. With those 4 removed the graph is fit; §2's remaining delta is then benign-by-protocol
+ measurement artifact plus one *named, bounded, non-blocking* residual defect class
(§2c).

---

# PART 1 — SPLICE INTEGRITY

## 1a. Exactly what changed

Mechanical whole-graph diff, original vs repaired:

| property | original | repaired | |
|---|---|---|---|
| node count | 773 | 773 | identical |
| node ids, and their **order** | — | — | **byte-identical** (list-equality on the id sequence) |
| nodes added / removed | — | — | **0 / 0** |
| nodes whose any field differs | — | **26** | exactly the 26 recorded repairs |
| fields that differ, across all 773 nodes | — | — | **`provides` only (17 nodes), `provides`+`needs` (9 nodes)** |
| `spans` differing on any node | — | — | **0** |
| `establishes` differing on any node | — | — | **0** |
| `id` differing on any node | — | — | **0** |
| provides entries **removed** | — | — | **0** (splice is purely additive) |
| top-level `uncovered` | — | — | identical |
| top-level `judgment_calls`, `unwind_log`, `dropped_merges`, `rename_seat_verdicts`, `cross_link_report`, `descend_near_misses`, `brief_sha` | — | — | identical |
| top-level `driver_autofixes` | 4 | 30 | +26, one provenance line per repair |
| top-level `promise_repairs` | absent | 26 entries | new provenance block |

`runs/ds7_repaired/root_graph.json` is **byte-equivalent** (canonical-JSON equal) to
`runs/ds7/root_graph.repaired.json` — the staged copy is faithful, so the battery run on
`ds7_repaired/` is a battery on the artifact under review.

Exported distinct provides names: **92 -> 118** (+26, one per repair; no name collisions —
see 1c). Needs entries: 9 nodes gained 1–2 needs each (14 new needs total), all
validator-accepted names.

**(a) verdict: PASS.** Only `provides` and validator-accepted `needs` were added. Spans,
establishes, ids and node count are untouched. No node added or removed. This is a clean
splice at the mechanical level.

## 1b. Adjudication of each of the 26 spliced `provides` — the load-bearing check

Method: for every spliced entry, read the receiving node's span text **in the document**
and ask whether that text establishes the concept the entry's `name` + `prose` assert.

### ACCEPTED — 18 splices, span text establishes the claim verbatim or near-verbatim

| node | name | span | basis |
|---|---|---|---|
| `L1368-1541_n024` | `unclear_cases_wait_rule` | L1475 | verbatim |
| `L1542-1706_n001` | `do_not_facilitate_illicit_behavior` | L1543 | the section heading line itself; a section-pointer name on the section's own heading node |
| `L1707-1973_n002` | `avoid_regulated_advice_rule` | L1710 | verbatim incl. the disclaimer clause |
| `L1707-1973_n008` | `support_mental_health_rule` | L1753 | verbatim |
| `L1707-1973_n024` | `privileged_information_rule` | L1807 | verbatim (both clauses present) |
| `L1707-1973_n025` | `instruction_conflict_surfacing_rule` | L1807 | verbatim |
| `L1707-1973_n030` | `tool_call_sensitive_data_rule` | L1814 | verbatim, all four assessment prongs |
| `L1707-1973_n038` | `recipient_identification_rule` | L1928 | verbatim |
| `L171-426_n029` | `letter_and_spirit_section` | L294 | the section's substantive first claim (literal wording vs underlying intent) |
| `L3239-3382_n002` | `avoid_overstepping` | L3241 | `#avoid_overstepping`'s first substantive claim, ends "without overstepping" |
| `L3239-3382_n003` | `transformation_no_unrequested_changes` | L3243 | verbatim |
| `L3239-3382_n004` | `transformation_interactive_alert` | L3243 | verbatim |
| `L3239-3382_n010` | `creativity_principle` | L3321 | verbatim |
| `L3383-3501_n001` | `interactive_vs_programmatic_setting` | L3386 | verbatim — the flagship repair |
| `L3954-4251_n008` | `no_unprompted_personal_comments_rule` | L3999 | verbatim |
| `L3954-4251_n014` | `avoid_condescension_rule` | L4052 | verbatim |
| `L3954-4251_n043` | `no_repetition_rule` | L4204 | verbatim |
| `L3954-4251_n045` | `avoid_hedging_rule` | L4251 | verbatim |
| `L461-608_n013` | `control_side_effects_section` | L529 | `#control_side_effects`'s first substantive claim |

(19 rows; `control_side_effects_section` is the 19th accepted-clean entry.)

### ACCEPTED WITH RESERVATION — 3 splices, correct site, prose over-reaches or mis-names

* **`L1-170_n017` / `red_line_principles_section`** (span L30). L28 is
  `## Red-line principles {#red_line_principles}` and is **uncovered** by any node, so L30
  ("We are committed to upholding the following high-level principles…") is the earliest
  admissible target — this is precisely the recorded "earliest-first can pick a lead-in
  paragraph" residual. The lead-in does establish that a set of red-line principles
  follows. But the entry's prose ("…including legal constraints and safety-critical
  information") describes the enumerated items at **L32–L41, which are outside the node's
  span**. Functionally fine as a section pointer; the prose asserts more than the span.
* **`L1-170_n033` / `risk_taxonomy_section`** (span L55). "We consider three broad
  categories of risk" — establishes the taxonomy. The prose's second clause ("describes
  the assistant's responsibilities in balancing empowerment and harm minimization") is not
  at L55. Same shape: over-reaching prose on a correct site.
* **`L609-698_n002` / `no_agenda_section`** (span L612). L612 does state "the assistant
  must not pursue its own agenda beyond helping the user" — this is the exact clause the
  Opus recheck (idx 113) named as the real, unexported referent, so the *content* delivered
  is right. But the **name says `_section`** and L612 sits inside `#assume_best_intentions`
  (L609), while the document's actual `#no_agenda` section opens at **L2128**, ~1,500 lines
  away (and is covered by `L2126-2404_n028`, "a topic heading establishing no rule"). A
  consumer traversing `no_agenda_section` lands on the clause, not the section. Correct
  claim, misleading name.

None of these three asserts something false about its span; I would keep all three and
tighten the prose in a follow-up, not revert them.

### REJECTED — 4 splices. Each is a claim the receiving span does not support.

**R1 — `assume_objective_pov` on `L2126-2404_n031` (span L2151). The prose is INVERTED.**
Spliced prose: *"The principle that the assistant should not assume an objective point of
view on contested topics."* The document's section is
`### Assume an objective point of view {#assume_objective_pov authority=user}` (L2137) and
its rule (L2139) is *"By default, the assistant should present information clearly,
focusing on factual accuracy and reliability."* The principle is that the assistant
**should** assume an objective point of view. The export now asserts its negation.
Second, independent defect: the receiving span **L2151 is a `!!! meta "Commentary"` block**
("This principle may be controversial…") — a commentary line *about* the principle, which
the graph's own policy excludes as an instruction site. The correct target exists and is
`L2126-2404_n004` (span L2139, establishes the rule verbatim).
The prose was inherited verbatim from the pre-existing needer `L2405-2473_n011`, so the
inversion is a pre-existing graph error — but the repair is what promoted it from a
dangling need (invisible) to an **export** (a claim the graph makes about a span). This is
the single most serious finding: a false safety-relevant claim in the production graph's
resolution vocabulary.

**R2 — `assume_best_intentions_principle` on `L3877-3953_n012` (span L3937).** The span is
*"Users may say thank you in response to the assistant. The assistant should not assume
this is the end of the conversation."* That establishes a conversational-sense rule; it
does **not** establish "the assistant should assume the user has best intentions". The real
`#assume_best_intentions` section is at **L609** (and its content node `L609-698_n004`
exports `implicit_biases`, which is why the Opus recheck **upheld**
`assume_best_intentions_section` as already-in-graph and `promise_repair` skipped it as
`skipped_not_opus_confirmed`). The under-export-class plan then re-created the concept
1,300 lines away on an unrelated rule. Also produces a **self-loop** (see below). Revert.

**R3 — `user_authority_section_rules` on `L3147-3238_n001` (span L3152).** Span:
*"The assistant should avoid making mistakes that would compromise the accuracy or utility
of its responses."* Spliced prose: *"Rules in sections marked authority=user carry
user-level instruction authority."* The span establishes the error-avoidance rule; the
authority claim comes from the **heading L3150**
(`### Avoid factual, reasoning, and formatting errors {#avoid_errors authority=user}`),
which I confirmed is **uncovered by any node in the graph**. The B2 fix correctly taught
`_select_target` to decline authority-*assignment* nodes; the unintended consequence here
is that an authority-class name landed on a substantive node instead, which is the same
assignment-vs-definition conflation the 16/16 `dropped_merge` upholds forbid, just in the
opposite direction. Additionally the prose is *generic* ("sections marked authority=user"),
contradicting the graph's mandated **per-section** authority convention (the 7 existing
`*_section_*_authority` names). Revert; the honest fix is a coverage fix at L3150, not a
splice.

**R4 — `voice_style_guidelines` on `L4252-4482_n001` (spans L4255, L4257, L4258).**
Spliced prose: *"The style guidelines in the voice_style section apply to both standard and
advanced voice modes; instructions about audio/video nuances apply only to advanced
voice."* That sentence is at **L4260** — *"The guidelines for content in this section apply
to both systems, but instructions that discuss the nuances of audio or video inputs or
outputs are only relevant to Advanced voice."* — which is **not in n001's spans**. The node
that does establish it already exists: **`L4252-4482_n003`, span L4260, whose `establishes`
is that sentence nearly verbatim** — and n003 is one of the two needers the repair counted
as "resolved". The splice is provably one node off. Re-aim to `L4252-4482_n003`; the
concept is real and belongs in the graph.

### Two systemic side-effects found while adjudicating

**Self-loops.** Self-loops (a node needing a name it provides) went **16 -> 19**; all three
new ones are repair-created:
`L3383-3501_n001` (`interactive_vs_programmatic_setting`), `L4252-4482_n001`
(`voice_style_guidelines`), `L3877-3953_n012` (`assume_best_intentions_principle`).
In each case the node was **its own dangling needer**, so the "resolution" is degenerate:
3 of the 43 resolved needers resolved onto themselves. For n001/L3383 this is harmless
(the node genuinely establishes the concept and also cites it). For R2 and R4 the self-loop
is a *symptom* of the mis-aim already rejected above.

**A dangling was introduced.** The repair spliced `privileged_information_definition` as a
new need on `L1707-1973_n024` — **nothing in the graph provides that name**. It is the one
new dangling in the diff (net 66 -> 24 is still a large win). The concept *is* exported, as
`privileged_information`; this is a one-token naming miss, cheaply fixed.

**(b) verdict: 19 clean + 3 accepted-with-reservation + 4 REJECTED.** The four rejections
are the blocker.

## 1c. Duplicate exports

Full census of names provided by >1 node in the repaired graph:

| name | providers | status |
|---|---|---|
| `guideline_authority` | 13 | pre-existing, **legitimate by protocol** |
| `root_authority` | 11 | pre-existing, legitimate by protocol |
| `user_authority` | 11 | pre-existing, legitimate by protocol |
| `system_authority` | 4 | pre-existing, legitimate by protocol |
| `developer_authority` | 3 | pre-existing, legitimate by protocol |
| `conversational_language_examples` | 3 (`L2821-3040_n019/20/21`) | **pre-existing, genuine three-way shard** of one example list; identical prose on three sibling nodes. Not a repair concern; arguably a pre-existing merge candidate |

**Not one of the 26 new names collides with an existing export or with another new name.**
The guards did their job: guard 1 (same-referent, locality-constrained) plus the B3
under-export empty-provides contract kept every duplicate out, including the two the
reviewers named — `sexual_content_involving_minors_section` (skipped against
`sexual_content_minors_prohibition`) and `authority_level_ordering` (skipped against
`authority_levels_hierarchy`).

The authority-name multiplicity is the documented convention (`authority_convention.md`,
EXPERIMENTS 08-13, Matt-approved): five level names shared document-wide and cited by
`needs`. That is exactly what inflates the comparator's edge denominator (§2a) and is
benign-by-protocol, not a duplicate defect.

One **semantic** near-duplicate is worth recording: R3's `user_authority_section_rules`
carries the same claim as the existing generic `user_authority`. It is not a name
collision, but it is a redundant coinage — a further reason to revert R3.

**(c) verdict: PASS.** 0 new duplicate exports; all 6 duplicated names are pre-existing,
5 of them protocol-mandated.

## 1d. The 43 resolved needers — spot-check of 8

Selection: the two largest cohorts, plus every case where needer and provider prose are not
lexically near-identical, plus the self-resolutions (i.e. deliberately weighted toward the
cases most likely to be a silenced dangling rather than a real link).

| # | need | needer | provider | judgment |
|---|---|---|---|---|
| 1 | `interactive_vs_programmatic_setting` (14 needers) | `L3239-3382_n004/5/6`, `L3383-3501_n002..n011` | `L3383-3501_n001` (L3386) | **REAL.** Provider span states the distinction verbatim; the 11 `L3383-3501_n*` needers are the section's own rules, each of which is conditioned on interactive-vs-programmatic. Highest-value single repair in the set — and 8 of the 36 newly matched golden edges are golden's `interactive_vs_programmatic_context`, i.e. the golden graph independently draws the same dependency. |
| 2 | `do_not_facilitate_illicit_behavior` | `L4572-4692_n015` (prose: *"The principle restricting actionable instructions for unlawful acts"*) | `L1542-1706_n001` (L1543 heading) | **REAL, and the lexically hardest case** — token sim 0.0, which is why it is the one new `<0.10` edge (§2b). The needer is an appendix rule pointing at the illicit-behaviour section; the provider *is* that section's heading. Correct link, low lexical overlap. |
| 3 | `do_not_facilitate_illicit_behavior` | `L1368-1541_n005` | `L1542-1706_n001` | **REAL.** Needer prose is verbatim the transformation-exception cross-reference; the target is the cited section. |
| 4 | `privileged_information_rule` | `L1707-1973_n036` | `L1707-1973_n024` (L1807) | **REAL.** Needer prose and provider span are the same sentence; n036 is a downstream example/elaboration node in the same section. |
| 5 | `recipient_identification_rule` | `L1707-1973_n040/n041` | `L1707-1973_n038` (L1928) | **REAL.** Provider span is the rule verbatim; the two needers are its consequent clauses. |
| 6 | `assume_objective_pov` | `L2405-2473_n011` | `L2126-2404_n031` (L2151) | **SILENCED, NOT RESOLVED.** The dangling stopped dangling only because the repair created an export with the *needer's own inverted prose* on a commentary line (R1). The need was already wrong; resolving it against a copy of itself validates nothing. Falls with R1. |
| 7 | `assume_best_intentions_principle` | `L3041-3146_n002` | `L3877-3953_n012` (L3937) | **SILENCED, NOT RESOLVED.** Needer wants the best-intentions principle (real, at L609); provider span is the "thank you" rule. Prose matches because it was copied from the need. Falls with R2. Note `assume_best_intentions` (the correctly-named need on `L1542-1706_n007`) is **still dangling** — the graph now has the concept named twice and satisfied at the wrong place. |
| 8 | `voice_style_guidelines` | `L4252-4482_n003` (+ n001 self) | `L4252-4482_n001` | **BACKWARD.** `n003` *is* the node whose span (L4260) establishes the claim; the repair made the section-lead-in node the provider and the true establishing node the consumer. The edge exists but points the wrong way. Falls with R4. |

**(d) verdict: 5 of 8 are real graph improvements; 3 are danglings silenced rather than
resolved — and all 3 are the already-rejected splices R1/R2/R4.** No *fourth*, independent
silencing was found, which is the reassuring part: the resolution failures are coextensive
with the splice failures, not a separate class. Independent corroboration that the accepted
resolutions are real: **36 golden edges that were unmatched pre-repair are matched
post-repair, and the post-repair unmatched set is a strict subset of the pre-repair one**
(no golden edge lost coverage) — the newly matched golden need-names are
`interactive_vs_programmatic_context` (8), `unprompted_personal_comments_rule` (3),
`do_not_facilitate_illicit_behavior` (3), `regulated_advice_requirement` (2),
`recipient_identification` (2), `transformation_preserve_unasked_rule` (2),
`hidden_messages_concealment` (2), `creativity_pursuit_rule` (2),
`mental_health_support_approach` (2), and 5 singletons. Golden, built independently, draws
the same dependencies the repair drew.

## 1e. The 3 declines — honest or evasive?

| name | class | verdict |
|---|---|---|
| `letter_and_spirit_principle` | under-export | **HONEST, and correct.** *"L712 is a bullet item about following clearly intended low-risk instructions, not a statement of the letter-and-spirit principle itself… The seed's provenance (L712) appears to be a misattribution from a parent's division."* I checked: this is right. The redraw refused a bad splice and named the reason precisely — exactly what the deliver-or-explain escape hatch exists for. This decline is the best evidence in the run that the enforcement is not rubber-stamping. |
| `refusal_style_section` | promise | **ARGUED, semi-honest.** Not "the span does not establish this" — the reason is doctrinal: *"providing it would duplicate the heading-metadata role already carried by the guideline_authority needs entries. If the driver requires a provides entry, it should be added to n015."* That is a defensible reading of the section-name-vs-authority-name convention, and the fact that it volunteers the target it would use is candour, not evasion. Costless in practice: **no need in the graph references `refusal_style_section`**, so the decline leaves no dangling. Acceptable, but record it as a convention question, not a document finding. |
| `support_mental_health` | promise | **NOT AN HONEST DECLINE — this one is incoherent and should not have been booked as "honestly undeliverable."** The recorded reason argues both sides and then **ends by announcing compliance**: *"…the promise repair says if the span genuinely establishes it, include a provides entry with exactly this name. The section heading itself establishes the existence of the policy section… **I will add a provides entry to n007 for 'support_mental_health' with the seed's prose to satisfy the promise repair.**"* The entry was not added. So the stage recorded, as an honest declination, an output whose own text concludes the promise **is** deliverable. Mitigating: the concept is not lost — the repair separately exported `support_mental_health_rule` on `L1707-1973_n008` (L1753), which is sound. Aggravating: `support_mental_health` **remains one of the 24 danglings**. Reclassify as a *non-delivery* (a redraw that failed to emit what it said it would), not a decline. Not a wrong claim in the graph, so not a blocker — but the report's "3 honestly undeliverable" count overstates by one. |

**(e) verdict: 1 exemplary, 1 acceptable-but-doctrinal, 1 mis-booked.** No decline is an
evasion of the "the span does not establish this" question in the sense that matters
(none conceals a defect); one is a bookkeeping error in the stage's own report.

## 1f. The 24 remaining danglings, classified

No dangling in the set is **external-by-design** (this document has no external
references). The set splits cleanly in two, plus one repair-caused regression:

### Class A — concept IS in the graph under another name (9 names / 15 needers). Not content loss; resolvable by rename/alias at $0.

| name | needers | the concept, as exported |
|---|---|---|
| `authority_level_ordering` | 5 | `authority_levels_hierarchy` (`L1-170_n042`) — prose **verbatim identical**; guard 1 correctly refused to duplicate it |
| `avoid_info_hazards` | 3 | `information_hazards_prohibition` (`L831-1000_n003`) |
| `objective_point_of_view` | 2 | the `#assume_objective_pov` region — but see R1: currently exported only under the inverted-prose entry, so treat as unresolved until R1 is fixed |
| `ask_clarifying_questions_section` | 1 | `ask_clarifying_questions_section_guideline_authority` (`L2653-2820_n001`) — the convention's own per-section name |
| `sexual_content_involving_minors_section` | 1 | `sexual_content_minors_prohibition` (`L797-830_n014`); **deliberately** skipped under the B3 empty-provides contract, with the by-name rejection of threshold-lowering recorded |
| `assume_best_intentions` | 1 | `implicit_biases` (`L609-698_n004`), per the Opus recheck |
| `support_mental_health` | 1 | `support_mental_health_rule` (`L1707-1973_n008`), added by this very repair; left dangling by the mis-booked decline (§1e) |
| `letter_and_spirit_principle` | 1 | `letter_and_spirit_section` (`L171-426_n029`), added by this repair |

### Class B — genuinely under-exported: sections with **zero** content exports (5 names / 8 needers). Still-repairable, needs a second bounded pass.

| name | needers | section | section lines | golden content exports there | ds7-repaired |
|---|---|---|---|---|---|
| `do_not_encourage_self_harm` | 3 | `#do_not_encourage_self_harm` | 97 | 2 | **0** |
| `be_warm_rule` | 2 | `#be_warm` | 42 | 1 | **0** |
| `avoid_errors_rule` | 1 | `#avoid_errors` | 89 | 6 | **0** |
| `be_thorough_but_efficient_rule` | 1 | `#be_thorough_but_efficient` | — | — | **0** |
| `respect_real_world_ties` | 1 | `#respect_real_world_ties` | 76 | 5 | **0** |

These are the honest residue of cause 3. Note the safety weight: self-harm and
real-world-ties are both root/system-authority material.

### Class C — repair-introduced (1 name / 1 needer)

`privileged_information_definition` on `L1707-1973_n024` — a need the splice itself added,
naming a provider that does not exist. `privileged_information` does. One-token fix.

**(f) verdict:** 0 external-by-design, **15 needers (9 names) name-mismatch — content
present**, **8 needers (5 names) genuine under-export — still repairable**, **1 repair
regression**. Net 66 -> 24 danglings, with 63% of the residue being vocabulary alignment
rather than missing content.

---

# PART 2 — DELTA RE-INVESTIGATION vs GOLDEN

## 2a. The three causes, re-measured on the repaired graph

Recomputed with `graph_compare.build_edges` / `match_edges` directly (same functions the
comparator uses), golden = `recurse/root/graph.json`.

### Cause 1 — authority fan-out share of edges: **essentially unchanged, still the dominant measurement artifact**

| bucket | pre-repair | post-repair |
|---|---|---|
| authority-class need names | 5,354 (92.7%) | 5,376 (**91.9%**) |
| `assistant_definition` | 224 (3.9%) | 229 (3.9%) |
| **content edges** | **196 (3.4%)** | **242 (4.1%)** |
| total | 5,774 | 5,847 |

Re-measured exactly as `delta_investigation.md` §2 did:

| filter | pre: a / b / recall / precision | post: a / b / recall / precision |
|---|---|---|
| all names | 512 / 5,774 / 0.369 / 0.050 | 512 / 5,847 / **0.439** / **0.056** |
| authority names excluded | 402 / 420 / 0.177 / 0.176 | 402 / 471 / **0.264** / **0.227** |
| + `assistant_definition` excluded | 402 / 196 / **0.177** / **0.378** | 402 / 242 / **0.264** / **0.442** |

The report's pre-repair reference pair (0.177 / 0.378) **reproduces exactly**, confirming
the method. Post-repair the honest content numbers are **recall 0.264 (+49% relative),
precision 0.442**. Strict variants move the same way (strict recall 0.162 -> 0.213, strict
precision 0.0144 -> 0.0186). The authority plumbing grew by only 22 edges (the 14 spliced
needs include a few authority citations) — the repair did **not** feed the artifact.

### Cause 2 — granularity / misalignment mass: **exactly zero change, by construction**

`alignment` is byte-identical between the two compare files: `one_to_one` 486/486,
`split_join` 16/15, misaligned 91 (golden) / 272 (ds7), and `line_mass` identical. Coverage
is likewise identical (`uncovered.only_a` 38, `only_b` 279, jaccard 0.4954). This is the
expected result and a useful control: since the splice touched only `provides`/`needs`, no
node/span/coverage metric could move — and none did. Cause 2's classification
(benign-by-protocol under the GRAPH_EQUIVALENCE split/join rule, ~4.7–7.1% line mass, 0
substantive disagreements in the 15-sample) stands unmodified.

### Cause 3 — provides under-export: **the gap is roughly half closed, and the remainder is mostly not real**

Exported names **92 -> 118**, golden 230. Decomposing golden's 230 so the residual gap is
honest:

* 28 of golden's 230 are **authority-class coinages** — the per-section names
  (`avoid_errors_section_authority`, `do_not_lie_section_authority`,
  `root_authority_extremism`, …) that `authority_convention.md` records as the convention
  ds7 was **built to replace** with 5 shared names + `needs` links. ds7-repaired has 17.
  This slice of the gap is **benign-by-protocol, not a defect** — closing it would be a
  regression.
* **58 of golden's 230 names are never needed by any golden node** — dead exports that
  cost the comparator nothing and buy a consumer nothing.
* Golden **content names that are actually load-bearing (needed at least once): 153.**

So the meaningful comparison is ds7-repaired's 101 content names vs golden's 153
load-bearing content names, and the operational measure is content-edge recall: **0.264,
i.e. ds7-repaired carries 242 of the 402 golden content edges' worth of linkage, up from
196.**

Estimating what fraction of the remaining gap is real, using the §1f classification of the
24 danglings and the per-section export census:

* **~40% is vocabulary mismatch, not missing content** — Class A, 9 names / 15 needers,
  every one traceable to an exported node (see table). Fixable at $0 by aliasing.
* **~60% is real** — Class B plus the per-section zero-export census below.

The **biggest remaining unexported concepts** (sections with ≥30 lines and **zero** content
exports in the repaired graph, ranked by size; "golden" = golden's content exports there):

| section | lines | golden | ds7-repaired |
|---|---|---|---|
| `#do_not_lie` | 97 | 9 | 0 |
| `#avoid_errors` | 89 | 6 | 0 |
| `#avoid_sycophancy` | 78 | 5 | 0 |
| `#respect_real_world_ties` | 76 | 5 | 0 |
| `#no_topic_off_limits` | 75 | 3 | 0 |
| `#uphold_fairness` | 71 | 5 | 0 |
| `#be_professional` | 60 | 4 | 0 |
| `#do_not_encourage_self_harm` | 97 | 2 | 0 |
| `#present_perspectives` | 96 | 2 | 0 |
| `#imitate_accents_in_voice_mode` | 103 | 2 | 0 |
| `#handle_interruptions_in_voice_mode` | 68 | 2 | 0 |
| `#prioritize_teen_safety` | 115 | **0** | 0 (golden exports nothing either — not a ds7 defect) |

And by residual gap vs golden (top of the list, all sections):
`#disallowed_content` (gap 10), `#do_not_lie` (9), `#letter_and_spirit` (8),
`#sensitive_content` (7), `#no_agenda` (7), `#have_conversational_sense` (7),
`#voice_style` (6), `#avoid_errors` (6).

Sections the repair visibly improved: `#protect_privileged_information` 1 -> 5,
`#letter_and_spirit` 0 -> 1, `#support_programmatic_use` 0 -> 1, `#control_side_effects`
1 -> 2, `#no_agenda` 0 -> 1, `#have_conversational_sense` 0 -> 1, `#red_line_principles`
0 -> 1, `#support_mental_health` 0 -> 1.

**Cause 3 verdict: materially reduced, not closed.** It remains ds7's one real defect
class, now smaller, bounded, and enumerable by section.

## 2b. Did anything get worse?

**The two numbers in the brief, checked:**

1. **Mismatched (edge-similarity `<0.10`) 7 -> 8: NOT a regression.** The single new
   low-sim edge is `L4572-4692_n015 --[do_not_facilitate_illicit_behavior]-->
   L1542-1706_n001`, sim **0.0**. I adjudicated it in §1d (#2): it is **semantically
   correct** — an appendix rule ("The principle restricting actionable instructions for
   unlawful acts") pointing at the `#do_not_facilitate_illicit_behavior` section heading.
   Its similarity is 0 purely because the needer paraphrases and the provider prose is a
   section pointer; there is no shared token. Before the repair this pair was an invisible
   *dangling*; the repair made it a visible edge, and the instrument reports it. The rate
   fell: **7/1,011 = 0.69% -> 8/1,064 = 0.75%** in absolute rate but the healthy bucket
   grew fastest (`>=0.25`: 679 -> **729**, `0.10–0.25`: 325 -> 327). Zero pre-existing
   low-sim edges were introduced or worsened (the pre-repair 7 are unchanged and none was
   removed).
2. **Uncovered jaccard "0.5086 -> 0.4954": the premise is a mis-attribution — nothing got
   worse.** Both `runs/ds7/compare_vs_golden.json` and
   `runs/ds7_repaired/compare_vs_golden.json` report jaccard **0.4954**, with identical
   `only_a` (38) and `only_b` (279). **0.5086 is `runs/ds5/compare_vs_golden.json`'s
   number** (grepped: it appears nowhere else in the tree). ds7 was already at 0.4954
   pre-repair; the ds5 -> ds7 movement is a run-to-run difference that
   `delta_investigation.md` §3 already explained (~98% coverage-policy difference,
   ~5 lines of real gap), and the repair cannot move coverage at all since it never touches
   `spans` or `uncovered`.

**What did get worse, that the brief did not name:**

| regression | magnitude | severity |
|---|---|---|
| **4 wrong claims spliced** (R1–R4, §1b) | 4 of 26 | **BLOCKING.** R1 asserts the negation of a document principle. |
| self-loops 16 -> 19 | +3 | Low on its own; 2 of the 3 are symptoms of R2/R4 and disappear with them. |
| new dangling `privileged_information_definition` | +1 | Trivial, one-token fix. |
| `promise_repair_report.json` books `support_mental_health` as "declined_honestly" | 1 | Bookkeeping: the count of honest declines is 2, not 3. |
| raw edge denominator 5,774 -> 5,847 | +73 | Not a regression — raw precision still **rose** 0.050 -> 0.056, and authority-excluded precision rose 0.176 -> 0.227. |

**Nothing regressed on the golden comparison.** `unmatched_a` (golden edges ds7 fails to
carry) went 323 -> 287, and the post-repair set is a **strict subset** of the pre-repair
set — no golden edge that ds7 covered before is uncovered now. Same for
`strict_unmatched_a` (429 -> 403, strict subset). Alignment, coverage, node counts and
line mass are byte-identical.

## 2c. Verdict on the remaining delta

**Not yet exclusively benign — but the residual real defect class is bounded, named, and
already the one the investigation predicted.** Breakdown of the post-repair delta:

| component | disposition |
|---|---|
| Comparator authority/name fan-out — 5,376 authority + 229 `assistant_definition` = **95.9%** of the 5,847-edge denominator | **MEASUREMENT artifact** (the F4 authority-collapse never built) over a **BENIGN-BY-PROTOCOL** convention. Unchanged by the repair. Record the authority-excluded pair **0.264 / 0.442** as the honest edge numbers for the production package. |
| Granularity / misalignment (773 vs 593 nodes; 91 / 272 misaligned at 4.7–7.1% line mass) | **BENIGN-BY-PROTOCOL** + comparator windowing. Byte-identical pre/post; 0 substantive disagreements in the recorded 15-sample. |
| Uncovered-set difference (jaccard 0.4954) | **BENIGN-BY-PROTOCOL** (~98% coverage policy: blank lines, admonition markers, headings, example markup) + ~5 lines of real gap, per `delta_investigation.md` §3. Untouched by the repair. |
| Golden-side quirks (58 never-needed exports, 28 per-section authority coinages, swallowed markup, giant spans like L69–191) | **GOLDEN defects.** Newly quantified here: **86 of golden's 230 names (37%) are either dead or superseded-by-convention**, so the raw "230 vs 118" gap materially overstates the deficit. |
| **Content-edge under-export** — 242 vs golden's 402; 5 names / 8 needers still dangling; **11 named sections ≥30 lines with zero content exports** | **REAL ds7 DEFECT, reduced not eliminated.** Mass: ~160 content edges; exemplars `#do_not_lie` (97 lines, golden 9, ds7 0), `#avoid_errors` (89 / 6 / 0), `#avoid_sycophancy` (78 / 5 / 0), `#uphold_fairness` (71 / 5 / 0), `#respect_real_world_ties` (76 / 5 / 0), `#do_not_encourage_self_harm` (97 / 2 / 0). ~40% of the *dangling* residue is name-mismatch (content present, §1f Class A) and closable at $0. |
| **4 mis-aimed splices (R1–R4)** | **NEW REAL DEFECT introduced by this repair.** Not part of the pre-repair delta. Blocking. |

So: the pre-existing delta is now **cause 1 + cause 2 + coverage policy = measurement
artifact and protocol**, plus **one real, shrinking, section-enumerable under-export class**
that is explicitly in-scope for a further bounded pass under ruling #4. What blocks the
production stamp is not the delta — it is the four unadjudicated wrong claims the repair
itself wrote.

---

# FITNESS VERDICT

**`runs/ds7/root_graph.repaired.json` is NOT fit to be the production graph in its current
state.** Against the project's three tests:

1. *Every difference from golden explained* — **YES.** §2c accounts for 100% of the
   delta: 95.9% of the edge denominator is the documented authority artifact, alignment and
   coverage are protocol differences with recorded classifications, 37% of golden's name
   advantage is golden-side dead/superseded vocabulary, and the honest residual is a named,
   section-enumerated under-export class with mass and exemplars.
2. *Every applied change evidenced* — **YES, mechanically.** All 26 splices carry a
   `promise_repairs` provenance entry, a `driver_autofixes` line, a redraw artifact under
   `runs/ds7/promise_repair/`, and a health.jsonl summary; the diff is provably additive
   and confined to `provides`/`needs`.
3. *No unadjudicated wrong claims* — **NO. FAILS.** Four splices assert things their
   receiving spans do not establish, one of them (`assume_objective_pov`) the **negation**
   of the document's principle.

**Splices I reject:** `assume_objective_pov` on `L2126-2404_n031`;
`assume_best_intentions_principle` on `L3877-3953_n012`; `user_authority_section_rules` on
`L3147-3238_n001`; `voice_style_guidelines` on `L4252-4482_n001`.

**Path to fit — all $0, all deterministic, no new model calls:**

1. **Revert R1, R2, R3** (drop the three `provides` entries and, for R2, the matching
   `needs` entry) — restores `objective_point_of_view` /
   `assume_best_intentions` / `user_authority_section_rules` to dangling, which is the
   honest state. Danglings 24 -> 27; nothing else moves.
2. **Re-aim R4**: move `voice_style_guidelines` from `L4252-4482_n001` to
   `L4252-4482_n003` (span L4260, whose `establishes` is the claim). Purely mechanical;
   also clears one self-loop and turns a backward edge into a correct one.
3. **Fix the introduced dangling**: rename the spliced need
   `privileged_information_definition` -> `privileged_information` on `L1707-1973_n024`.
4. **Correct the report**: reclassify `support_mental_health` from `declined_honestly` to a
   non-delivery; `declined_honestly` becomes 2.
5. **Tighten the three reservation proses** (`red_line_principles_section`,
   `risk_taxonomy_section`, `no_agenda_section`) so no entry claims more than its span, and
   record the `no_agenda_section` name/referent mismatch.
6. **Record, do not fix now**: the Class-B under-export residue (5 names / 8 needers; 11
   zero-export sections) as the scope of any follow-on bounded pass, and the Class-A
   name-mismatch residue (9 names / 15 needers) as an aliasing task.

With steps 1–4 applied, the graph carries 23 evidenced splices, 0 wrong claims, content
recall 0.264 / precision 0.442 against golden, danglings ~26, and a fully explained delta.
**At that point it is fit for the production stamp.**
