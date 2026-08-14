# Opus recheck of the 61 quarantined ds7 verdicts (evidence prompts)

Date: 2026-08-14. **Zero API spend** — the prompts were rendered by the committed
`frontier_review.item_prompt` with a real `Evidence` context and judged by an Opus
subagent in its own context. Per-item output: `opus_recheck.json` (runs-adjacent, not
under `runs/`).

Inputs
* `runs/ds7/frontier_verdicts.json` — the 61 quarantined rows (45 `broken_promise`,
  16 `dropped_merge`), all judged in the first slice on **name-only** prompts.
* `frontier_review.load_evidence('runs/ds7', lines)` over `runs/ds7/root_graph.json`
  and `specs/openai-model-spec/model_spec.md`.
* **0 items `evidence_unconstructable`** — every one of the 61 rendered a real
  evidence prompt under the corrected `item_prompt` (no `run_review` prep exclusions).

## 1. Agreement vs the quarantined K3 verdicts

| kind | n | K3 decided | agree | disagree | K3 no_verdict | agreement (decided) |
|---|---|---|---|---|---|---|
| broken_promise | 45 | 41 (40 reject, 1 uphold) | 12 | 29 | 4 | **29%** |
| dropped_merge | 16 | 16 (16 uphold) | 16 | 0 | 0 | **100%** |
| **total** | **61** | **57** | **28** | **29** | **4** | **49%** |

Cell-level:

| | K3 reject | K3 uphold | K3 no_verdict |
|---|---|---|---|
| **Opus reject** | 12 | 1 | 1 |
| **Opus uphold** | 28 | 16 | 3 |

Opus totals: **47 uphold / 14 reject** (broken_promise 31/14, dropped_merge 16/0).

### dropped_merge: same answer, real grounds

All 16 are one shape — node A is a **section heading assigning an authority level**
(`#respect_creators authority=root`, `#avoid_abuse authority=user`, …) or a
**level-assignment list item** (`1. **Root**: Model Spec "root" sections`); node B is
the **definition of that level** (`Root: Fundamental root rules that cannot be
overridden…`). Assignment vs definition: distinct scope and obligation, so dropping the
merge was correct, 16/16. The K3 row was 16 uncertainty-defaults; with evidence the same
answer is now *earned*. This is the clean case where evidence **confirms** rather than
changes.

## 2. Where evidence CHANGED the verdict (29 items — these matter most)

The K3 round was reject-default, so almost all movement is reject → uphold. The changes
fall into four evidence classes.

### (a) The name is already provided elsewhere in the root graph — 9 items
`promise_repair`'s own prep independently marks these `skipped_already_provided`
(re-review finding 1a), so this is not an Opus idiosyncrasy.

| idx | name | provider | K3 → Opus |
|---|---|---|---|
| 0,1,2,3,4,5 | `chain_of_command_principle` | `L1-170_n040` (seed prose verbatim) | reject → **uphold** |
| 12,13 | `scope_of_autonomy` | `L461-608_n002` | reject → **uphold** |
| 63 | `stay_in_bounds_section` | `L427-1107_n001` | reject → **uphold** |

### (b) The concept is in the graph under a different name — 15 items
The promised prose matches an exported name's referent. A cross-link resolves onto the
right passage; the defect (where any) is a rename/retrieval mismatch, not a vanished
concept — and a `promise_repair` redraw would create a **duplicate export**.

| idx | promised name | already exported as | K3 → Opus |
|---|---|---|---|
| 97–105 (9) | `authority_level_ordering` | `authority_levels_hierarchy` (`L1-170_n042`) — **prose is verbatim identical** | reject/no_verdict → **uphold** |
| 107, 131 | `avoid_info_hazards`, `information_hazards_section` | `information_hazards_prohibition` (`L831-1000_n003`) — the same pair the frontier itself found at near-miss idx 90 | reject → **uphold** |
| 122, 130 | `transformation_exception`(`_section`) | `transformation_exception_rule` (`L1368-1541_n002`) + `covered_transformation_tasks`, `transformation_output_scope` | reject → **uphold** |
| 133 | `restricted_content` | `restricted_content_definition` (`L797-830_n009`), `restricted_content_rule` | reject → **uphold** |
| 114 | `sexual_content_involving_minors_section` | `sexual_content_minors_prohibition` (`L797-830_n014`) | reject → **uphold** |
| 132 | `protect_privacy_section` | `privacy_protection_rule` (`L1001-1107_n006`) | reject → **uphold** |
| 118, 128 | `assume_best_intentions`(`_section`) | `implicit_biases` (`L609-698_n004`) | no_verdict/reject → **uphold** |

Note on doctrine: this does **not** reopen the repo's `definition-vs-rule = two` ruling.
That ruling governs whether a node's export may be *renamed*; the question here is only
whether the promised content is **missing from the graph**, and it is not.

### (c) The graph's own convention already names the section — 4 items

| idx | promised name | the convention's own entry | K3 → Opus |
|---|---|---|---|
| 112 | `ask_clarifying_questions_section` | `ask_clarifying_questions_section_guideline_authority` (`L2653-2820_n001`) — the k3 report's own idx-39 retrieval miss | reject → **uphold** |
| 123 | `highlight_misalignments_section` | `highlight_misalignments_section_guideline_authority` (`L3041-3146_n001`) | reject → **uphold** |
| 119, 120 | `section_authority_level` (ea 3506 = `#love_humanity`) | `love_humanity_section_user_authority` (`L3505-3595_n001`); the graph exports **per-section** authority names (7 of them), never a generic one | reject/no_verdict → **uphold** |

### (d) The one change in the *unsafe* direction — 1 item

| idx | name | K3 | Opus | why |
|---|---|---|---|---|
| **113** | `no_agenda_section` | **uphold** | **reject** | The seed prose ("should not pursue its own agenda beyond helping the user") is the clause at doc **L611** inside `#assume_best_intentions`; `L609-698_n004` exports only `implicit_biases` (the three biases), not the no-agenda principle, and nothing in the 92-name vocabulary covers `#no_agenda` (doc L2128) either. |

This is the only quarantined item K3 upheld, and it reasoned from the name alone
("no_agenda_section sounds like a section that exists"). Evidence reverses it — the
fail-closed direction was wrong here, which is exactly why the quarantine was right.

Also newly decided from K3 `no_verdict`: **111** `objective_point_of_view` → **reject**
(the referent is `#assume_objective_pov`, doc L2137, and the graph exports **no name at
all** from the whole L2126–2475 region).

## 3. Bottom line: how many of the 45 broken-promise rejects are real defects?

**14 of the 45 items survive as evidence-confirmed defects** — 12 of K3's 40 rejects,
plus idx 111 (K3 no_verdict) and idx 113 (K3 uphold). **31 are not defects.**

Those 14 items are **13 distinct names**:

| idx | name | doc referent | why it is a real defect |
|---|---|---|---|
| 14 | `interactive_vs_programmatic_setting` | `#support_programmatic_use` L3384 | covering nodes state the distinction verbatim; **no provides name at all** from L3383–3501 (the flagship case, 14 danglings) |
| 108 | `do_not_facilitate_illicit_behavior` | L1543 | the section's own heading node `L1542-1706_n001` has an empty `provides` |
| 110 | `voice_style_guidelines` | `#voice_style` L4253 | the both-modes scoping claim is a node claim; only `standard_voice_mode`/`advanced_voice_mode` are exported |
| 111 | `objective_point_of_view` | `#assume_objective_pov` L2137 | zero exports across L2126–2475 |
| 113 | `no_agenda_section` | doc L611 / `#no_agenda` L2128 | only `implicit_biases` is exported from that span |
| 115, 116 | `support_mental_health` | L1751 | only `privileged_information` is exported from all of L1707–1973 |
| 117 | `avoid_overstepping` | L3239 | no covering name; the seed's ea 1422 is a *citation* site |
| 121 | `user_authority_section_rules` | `#avoid_errors authority=user` L3150 | no `*_authority` name for that section, unlike the 7 that exist (low severity) |
| 124 | `letter_and_spirit_section` | L292 | taxonomy exported, the section/distinction itself is not (borderline) |
| 125 | `control_side_effects_section` | L527 | only `side_effect_examples`; the section's obligation is unexported |
| 126 | `risk_taxonomy_section` | `#risk_taxonomy` L53 | nothing exported from that Overview region |
| 127 | `red_line_principles_section` | `#red_line_principles` L28 | nothing exported |
| 129 | `refusal_style_section` | `#refusal_style` L4073 | nothing refusal-style in L3954–4251's exports |

Every one is an instance of the **provides under-export defect** the delta investigation
named as the one real ds7 defect (92 exported names vs golden's 230) — reaching the
broken-promise queue by a second route. **None** of the 14 is a case of content actually
lost from the document.

## 4. Does the promise-repair plan set match the evidence-confirmed defects?

`promise_repair.py runs/ds7` prep (run deterministically, **no `--yes`, $0**, artifacts
reverted): 29 plans = **9 promise-class** + 20 under-export-class; 3 promise names
skipped as already-provided; 14 promise names failed to locate a leaf.

### The 9 promise-class plans vs this recheck

| plan | ea | redraw leaf | Opus verdict | alignment |
|---|---|---|---|---|
| `interactive_vs_programmatic_setting` | 3384–3386 | [3383, 3501] | **defect** | ✅ correct target |
| `do_not_facilitate_illicit_behavior` | 1543 | [1542, 1706] | **defect** | ✅ correct target |
| `voice_style_guidelines` | 4255–4260 | [4252, 4482] | **defect** | ✅ correct target |
| `user_authority_section_rules` | 3150 | [3147, 3238] | **defect** | ✅ correct target |
| `avoid_overstepping` | 1422 | [1368, 1541] | **defect** | ⚠️ **displaced** — the section is at L3239; ea 1422 is the imminent-harm rule *citing* `(#avoid_overstepping)`. The redraw would attach the concept to the wrong passage. |
| `avoid_info_hazards` | 1373 | [1368, 1541] | not a defect | ❌ duplicate of `information_hazards_prohibition`, **and** displaced (section is L856) |
| `transformation_exception` | 814–815 | [797, 830] | not a defect | ❌ duplicate of `transformation_exception_rule`, **and** displaced (section is L1369) |
| `restricted_content` | 1371 | [1368, 1541] | not a defect | ❌ duplicate of `restricted_content_definition`, **and** displaced (section is L852) |
| `section_authority_level` | 3506 | [3505, 3595] | not a defect | ❌ the target node already provides `love_humanity_section_user_authority` |

**4/9 cleanly aligned; 5/9 misaligned.** The recorded `_select_target` fix (EXPERIMENTS
2026-08-14, "final 1c displacement CLOSED") makes the *splice* pick an exact-cover node,
but it cannot correct a seed whose `established_around` points at a **citation site
rather than an establishing site** — that is the residual displacement in
`avoid_overstepping`, `avoid_info_hazards`, `transformation_exception`,
`restricted_content`. Recommend a prep-time guard: **skip (or re-aim) a promise plan
whose ea line lies inside a `[?](#anchor)` cross-reference to a section whose own heading
lives elsewhere**, and extend the already-provided filter to **same-referent** names, not
just exact-name matches (`avoid_info_hazards` → `information_hazards_prohibition`,
`authority_level_ordering` → `authority_levels_hierarchy`).

### Under-export-class overlap (of the 20 plans)

* ✅ `support_mental_health` (ea 1751), `assume_objective_pov` (ea 2151 = idx 111),
  `no_agenda_section` (ea 612 = exactly the L611 clause) — all three land on confirmed
  defects with correct targets.
* ❌ `sexual_content_involving_minors_section` (ea 4576, leaf [4572, 4692]) — I upheld
  this item; the prohibition is already exported by `L797-830_n014`, and 4576 is the
  **U18 section's cross-reference** to it. This plan would splice the minors-prohibition
  concept onto a U18 node, ~3750 lines from the establishing text.
* The remaining 16 under-export plans concern names outside this quarantined set and were
  not adjudicated here.

### Confirmed defects with NO plan

`control_side_effects_section`, `risk_taxonomy_section`, `red_line_principles_section`,
`refusal_style_section` — and `letter_and_spirit_section` only obliquely (the
`letter_and_spirit_principle` plan sits at L712 inside `#ignore_untrusted_data`, not at
L292). All five failed prep with *"seed has no usable established_around"*: the
`*_section` seeds carry no `established_around`, so `locate_leaf` cannot find a span.
These are real, unrepaired gaps in Overview/style regions.

### Net

Of 13 distinct evidence-confirmed defect names: **7 correctly planned**, **1 planned but
displaced** (`avoid_overstepping`), **5 unplanned**. Of the 29 plans, **5 would export a
concept the graph already carries** (4 promise-class + 1 under-export-class).

**The plan set is roughly half-aligned with the evidence.** It is not wrong in direction
— every plan it lands correctly repairs a real under-export — but it inherits the ds7
reject-default's over-breadth: it plans repairs for four concepts that are already in the
vocabulary under adjacent names, and misses five sections that genuinely have no export
because their seeds lack an `established_around`.

## 5. Standing conclusion

* The **quarantine was correct and should stand**: 29 of 57 K3-decided verdicts move
  once evidence is attached, including one flip in the unsafe direction (idx 113).
* The corrected `item_prompt` **works**: 61/61 items rendered constructable evidence, and
  the evidence was decisive (not merely decorative) on 29 of them.
* The finale entry's "40 broken promises = real defects" should read **14**, and every one
  of those 14 is the provides under-export defect, not lost content.
* `dropped_merge` 16/16 uphold stands, now on grounds rather than on a default.
