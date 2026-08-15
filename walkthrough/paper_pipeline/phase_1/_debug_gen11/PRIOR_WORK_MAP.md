# PRIOR_WORK_MAP.md — reconciling this post-mortem with the earlier repair census

Three artifacts already cover this ground from a different angle:

* `TRANSLATION_REPAIR_CENSUS.md` — 191 clauses / 435 calls / 244 repair rounds, grouped by
  prompt-bytes **generation**, taxonomy by **finding shape**.
* `TRANSLATION_FIX_PLAN.md` — six candidate fixes A-F, claimed coverage 58%.
* `TRANSLATION_CENSUS_REVIEW.md` — clean-context adversarial review of both.

This post-mortem's taxonomy is by **mechanism** (`_debug_gen11/README.md`: *"a class is a
MECHANISM, not a `check_id`"*), over a **different population**: the 100 clauses of the
two 08-14 runs, of which only 12 (`20260814-163457`) were inside the census's gen-11
sample. `20260814-173322` was in flight while the census was written and *"contributed no
transcripts"* — so **88 of these 100 clauses are data the earlier work never saw.**

---

## 1. Census class → mechanism

| census class (`translation_repair_census.py:TAXONOMY`) | census gen-11 rounds | rounds in THIS run | maps to |
|---|---|---|---|
| `undeclared-body-name` | 25 | 81 rounds / 206 findings | **splits into M1 + part of M2/M4** — see §2 |
| `unsafe-variable` | 22 | 10+5 findings | **M4** (merged here with `not-a-term`) |
| `readback-slot-arity` | 18 | 7 findings | **M6**, but the *direction* reverses — see §3 |
| `borrowed-without-gloss` | 23 | 50 findings | **M2**, with a trigger the census did not have |
| `act-not-in-acts` | 17 | **0** | absent from this corpus region |
| `closure-ungoverned` | 15 | **0** | absent |
| `closure-missing` | 12 | **0** | absent |
| `citation-not-in-corpus` | 5 | **0** | absent |
| `clause-id-mismatch` | 8 | **0** | absent |
| `requires-inputs-overlap` | 4 | **0** | absent |
| `not-a-term` | 1 | 2 findings | folded into **M4** (this run shows it as the same clause thrashing) |
| `asp-syntax-refused` (clingo) | 1 | 5 findings | folded into **M5** as a cascade wrapper; the review's F-7 reading is confirmed |
| `requires-unprovided` | (noted, not counted) | 4 findings | **M5**, and largely *not a defect* per the standing ruling |
| `unresolved-reference` | — | 10 findings | **M5** |
| — no census class — | — | 12 findings | **M3** `gloss-restates-name` |
| — no census class — | — | 10 findings | **M7** `assumed-no-inference` |
| — no census class — | — | 7 findings | **M5** `concept-declared` |
| — no census class — | — | 5 findings | **M5** `situation-input` |

**Five of the census's top nine gen-11 classes fired zero times here.** The document's
overview and definitions sections govern almost no acts and cite almost nothing, so the
whole ACTS / CLOSURE / PROV block is absent. **The class ranking is corpus-region-
dependent and neither document says so.**

**Four classes here have no census entry at all** and would be `OTHER:schema-breach` under
`classify()`. The census reports *"557 lines, 0 in `OTHER`"* — true of its population, and
this run shows the taxonomy is not closed over the corpus. Two of the four (M3, and M5's
`concept-declared`) killed modules.

---

## 2. The split the census asked for: `undeclared-body-name` is at least three mechanisms

`_debug_gen11/README.md` states it as a given (*"`undeclared-body-name` was 32 findings and
at least three mechanisms"*). Measured here over 206 findings:

| mechanism | evidence | share |
|---|---|---|
| **M1 — no legal bucket exists for the invented predicate.** The name is model-invented (201/206 = **98%** name a predicate the graph never mentions), the module's `inputs` is empty, and the descriptive property is neither case data nor another node's claim. | 10 of 13 unrepaired-with-this-finding have empty `inputs`; only 3 of 17 recovered ones do. Controlled pair `n055`/`n070` (pass, non-empty `inputs`) vs `n065`/`n069` (fail, empty `inputs`), identical module shape. | dominant |
| **M4 spillover — the model bound a variable and the binder was undeclared.** | `l1_170_n039` round 1 = 3× unsafe-variable, round 2 = 3× `undeclared-body-name` on `authority_level`. `n016`, `n053`, `n078` show the same oscillation. | ~5 rounds |
| **A genuine typo / graph-name mismatch.** | 5 of 206 findings name a predicate that IS in the node's NEEDS/PROVIDES block — the case the check was written for. | 2% |

**The census merged these because it discriminated on message text only.** The review made
the same criticism of `unsafe-variable`, `not-a-term` and `closure-missing` (F-7); this is
the fourth instance and the most expensive one, because it is the class Fix F was costed
against.

Conversely, this post-mortem **merges** two census classes the census kept apart:
`not-a-term` into `unsafe-variable` (→ M4), on the evidence that `l1_170_n037` produces
both from one intention across consecutive rounds; and `asp-syntax-refused` into M5, on
the evidence that it is a wrapper with no independent cause.

---

## 3. Fix A-F → mechanism → verdict → still viable?

| fix | targets (census) | targets (mechanism) | review verdict + the specific defect | still viable? |
|---|---|---|---|---|
| **A** deterministic autofix | `readback-slot-arity`, IDFORM, `act-not-in-acts` | **M6** (partly), M4's `atom`-holds-a-rule sub-case | **NEEDS WORK.** A-1: `readback-empty-slots` decides a question the model left open — a no-`%` sentence with slots has two repairs and A1 always drops the slots, while the rule below refuses the mirror case for that exact reason; it *"silences a check without fixing the read-back"*. A-2: `declare-asserted-act` is a content decision that can bless a typo and nets **+10 breach-rounds** (`closure-missing` 22→48, `closure-ungoverned` 23→7). | **Yes, defects are to the diff.** Ship with `declare-asserted-act` off and the dropped-slot list recorded. **But this run re-scopes A's value: `act-not-in-acts` fires 0 times here, and A1 reaches at most 1 of 5 M6 rounds.** |
| **B** `cites`/`clause_id` as a per-request const | `citation-not-in-corpus`, `clause-id-mismatch` | **nothing in this run** (both classes fire 0 times) | **NEEDS WORK.** B-1: the diff is a **no-op for `cites`** — `json_schema()` pops `$defs` before the patch lands. B-2: the `anyOf` collapses to `{"enum":[…],"type":["string","null"]}`, making `cites: null` **illegal for 224/1386 licensed items (16.2%)** and pushing toward fabricated citations. B-3: `translate.py:1206` already passes the whole 773-id corpus as `known_ids`. B-4: use `enum`, not `const` (zero `const` uses in the repo). Realistic diff **60-120 lines**, not four. | **Yes, lever is right, diff is broken.** B-2 is the important one and it is the same laundering pressure M7 exhibits from the other side. **Deprioritise for this corpus region: 0 rounds to win here.** |
| **C** `requires`/`inputs` carry name+arity+gloss | `borrowed-without-gloss`, `inputs-entry-not-name-arity`, `requires-inputs-overlap` | **M2** | **SAFE TO LAND**, lowest blast radius, *"the one I would land first"* — minus `requires-inputs-overlap`, which carrying a gloss does nothing to prevent. Caveat: *"the model can satisfy it with a junk gloss… suppresses the check rather than removing the defect."* | **Yes — and it is the highest-confidence item on the list.** But **re-cost it against M3**: making a gloss required converts M2 rounds (4% kill rate) into either junk glosses or `gloss-restates-name` rounds (40% kill rate). That interaction is new and the review could not have seen it. |
| **D** split `ontology` into rules / ground facts | `unsafe-variable` | **M4** | **NEEDS WORK.** F-2: does not make the class unrepresentable (reaches only body-less ontology sites; 12/99 unsafe atoms carry a body; `OntologyGroundFact`'s no-variable rule is a docstring with no validator) — headline **58% → 43%**. D-1: no migration for 200 stored modules. D-2: uncosted forced re-translation (219 artifacts go `CONTRACT_STALE`; `apply_waivers` **raises**). D-3: `schema.py:865` builds the declaration set from `self.ontology` — if not updated, **every ontology-declared body literal becomes an M1 finding**. D-4: the cheaper conditional-`body` lever reaches 87/99 with zero blast radius and **was never rejected by name**. | **Idea yes, diff no.** D-4 is the shape to build. This run adds an argument for D-4: D-3's failure mode would inflate M1, the largest and least-fixable class here. |
| **E** acts carry their own closure | `act-not-in-acts`, `closure-*` | **nothing in this run** (0 rounds) | **REJECT as written.** E-1: deletes `_check_head_bound` on assert heads with no replacement, so ~20 assert-site unsafe variables would arrive as truncated clingo refusals instead. E-2: `schema.py:1294` would emit `asserts(cid, forbid, 0)` — *"valid ASP that means something else"*. E-3: silently no-ops three of Fix A's rules **while all 34 of A's tests still pass**. | **Not in current shape.** The review's own fallback (fold `closure` into `acts`, leave `asserts[].act` a string) is defensible. **Zero value in this corpus region.** |
| **F** body literals carry their origin | `undeclared-body-name` | **M1** | **REJECT / not ready.** *"Making the origin a required field does not make the choice; it relocates the same decision into a field the model must still fill, and converts a good message into a worse one."* Its 27 marginal kills are *"the least defensible subtraction in the document"*. | **Re-scoped by this run — see §4.** |

---

## 4. What the new evidence RE-RANKS

### 4a. Fix F targets a symptom — **the coordinating instance's reading is CONFIRMED, and the mechanism is now named**

The reading under test: *forced to translate non-normative text, the model invents
predicates, so making it declare its inventions would convert hard failures into plausible
fabrications.*

The data supports it and sharpens it. F proposes
`origin: Literal["ontology", "requires", "inputs"]` as a required field. For M1's
predicates, **none of the three is correct by the pipeline's own definitions**:

* `requires` is reserved by the adapter for graph NEEDS names, *"spelled EXACTLY as given"*;
* `inputs` is defined by the adapter as *"only for plain facts about the situation being
  judged (messages, roles, case data)"* — and
  `interacted_with_by_end_user_or_developer/1` is not one;
* `ontology` needs a body of its own, which regresses to the same problem.

**A required enum that is not total over the values the corpus needs forces a false
declaration.** So F would not merely relocate the decision (the review's finding) — it
would make the wrong answer mandatory, and the resulting module would pass. That is worse
than the current hard failure, which at least leaves a lost module rather than a laundered
one.

**Recommendation for phase B: F should be RE-SCOPED, not kept and not simply dropped.**
The part worth keeping is F's *intermediate* proposal (`body_names: [{name, arity,
origin}]` alongside a string body) **only if the origin vocabulary is first made total** —
i.e. only after the missing bucket for descriptive properties of defined terms exists.
Building F before that is building the fabrication. Keeping F "for a residue of genuinely-
normative clauses" does not rescue it either: the four genuinely-normative losses here
(`n047`, `n052`, `n056`, `l171_426_n005`) fail on `conflict/3`, `developer_instruction`,
two missing glosses, and one gloss — F reaches only `n052`, and only if `inputs` is a
legal home for `developer_instruction`, which is exactly the question F assumes away.

### 4b. Other re-rankings this run forces

| item | earlier standing | re-ranked because |
|---|---|---|
| **A + B "highest value per unit of risk"** | rank 4 and 5, recommended first | Both target classes that fire **0-1 rounds** in this corpus region. Their value is real but is concentrated in the normative sections, not here. |
| **C** | rank 3 | **Promote.** It is the only fix the review passed and the only one whose mechanism (M2) is the #2 cost here — *provided* it is re-costed against M3. |
| **D** | rank 1, *"highest value overall"* | **Demote.** M4 is #4 here, not #1, and D-3's failure mode feeds M1. Build D-4 instead. |
| **E** | rank 2 | **Park.** Zero exposure in this region and a REJECT verdict. |
| **the repair loop itself** | not on the list | **New #1 by recoverable cost.** 40% of repair rounds returned byte-identical bytes ($0.1026, 42% of repair spend); 14 of 19 losses recovered on a byte-identical retry costing 45 calls against 95 spent producing nothing. No candidate fix addresses this. |
| **span-type classification at graph stage** | not on the list | **New.** 16/19 losses and 12/12 abstentions are non-normative spans. No candidate fix addresses this. |

---

## 5. What the earlier work got RIGHT and must be preserved

Do not re-derive these; they were independently validated by the review and this
post-mortem uses them.

* **All 435 calls match `usage.jsonl` 1:1 on `content_chars`, zero unmatched.** This
  post-mortem used the same method and got 230/230 on its own population. It is the
  correct costing method and it should be the standard.
* **Real repair share is 61%** ($0.4654 of $0.7649 recorded). This run independently
  measures **60%** ($0.2415 of $0.4051). The finding is stable across populations.
* **The census cost model runs 1.05× high, and the stated cause is wrong**: not
  undiscounted cache but `translation_repair_census.py:307` (`in_cpt = out_cpt`); input is
  3.98 chars/token, completion 3.74. Any future cost model must not repeat this.
* **Defect trading is REAL** — 97 novel-class instances genuinely introduced vs only 5
  latent, under a hard masking replay. This post-mortem confirms the phenomenon and adds
  the caveat that the 57% headline is a **per-clause** rate, not a per-round rate
  (`SUMMARY.md` §4).
* **The notation-table lesson**: enumerating every slot and its rendering in
  `node_worked_example.md` took a 43-round family (`not-a-term` /
  `forbid-body-not-bare-name` / `concept-name-carries-arity`) to 0-2 rounds. Confirmed
  here — that family is 2 findings in 100 clauses. **Enumeration works; warnings do not.**
* **The refusal lines in `translate_autofix.py`** — never autofix an undeclared body name,
  never rewrite a fabricated citation, never guess prose in `forbid_body`, never fix a
  disagreeing arity suffix. This run's M1 and M7 evidence strengthens every one of them.
* **`requires-unprovided` at partial corpus is expected incompleteness, not a defect**
  (`repair_graveyard/_cleared_*/VERDICT.md`), with a recheck mandated at corpus
  completion.
* **Fix A's replay firing counts and class deltas** were reproduced exactly by the review
  and are not in question.

## 6. What the earlier work got WRONG (already corrected by the review; restated so it is not re-imported)

* **"58% of gen-11 repair rounds removed, measured by replay"** — 47 of the 49 kills are
  class subtraction by fiat; only 2 are measured. Corrected headline: **43%**, of which 2
  measured and 34 assumed.
* **§6.1's masking numbers do not reproduce** (61% / 54% / 114 chains → 59.5% pooled /
  49% / 120 chains). The qualitative claim — `Module._coherent` is an `after` validator, so
  round 1 is told less than the truth — is correct and important.
* **§3.2's causal attribution** (the improvement came from the per-request adapter) is
  perfectly confounded with `resample_truncation: 2` switching on at the same transition.
* **§5.1 "every gen-11 `unsafe-variable` is an `ontology[i].atom`"** — 37 of 40; 3 are
  `asserts[i]`.
* **§5.1 "74% already declared in `concepts`"** — unsourced; independent measurements give
  67.8-72.7% (all gens) / 84% (gen-11 ontology sites).
* **`TRANSLATION_FIX_PLAN.md:54` cumulative "+C → 43%"** is wrong; D+E+C = 45/84 = 54%.
* **"Fix A is IMPLEMENTED"** means the module exists and is pinned. It is imported only by
  `translation_fix_sim.py`; **no translation uses it.**
* Add from this run: **the census taxonomy is not closed over the corpus** (four live
  classes fall into `OTHER:`), and **the gen-11 class ranking does not transfer between
  corpus regions**.
