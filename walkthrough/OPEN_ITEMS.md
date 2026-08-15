# Open items register

**This file is the canonical list of outstanding work.** `EXPERIMENTS.md` is
the chronological *record* (what happened, with grounds); it is not a worklist
and late entries there silently supersede earlier ones. If an item is not in
this table, it is not tracked. Close items by moving them to §6 with the commit
that closed them — never by deleting the row.

Status: `READY` (designed+validated, awaiting a gate) · `DESIGNED` (spec exists,
not built) · `IN FLIGHT` (someone is on it) · `NEEDS RULING` (blocked on Matt) ·
`DEFERRED` (deliberate, with the reason).

## 0 · Review status of what §1 asks you to rule on

⛔ **A ruling request that has not survived an adversarial pass is not ready.**
Audited 2026-08-15: every builder self-report that DID go to clean-context
review this campaign came back with defects the builder had missed (promise
repair 3 rounds; ds8 fix set 2; pipeline fixes 2; the frontier stage's
near-miss would have inverted 43% of a paid slice). Items below carry their
review state; do not spend attention on an UNREVIEWED row.

| item | reviewed? |
|---|---|
| M1 fixes C/D/E | ⏳ IN REVIEW (dispatched 2026-08-15, `TRANSLATION_CENSUS_REVIEW.md`) |
| M2 fix F | ⏳ same review |
| M3 factory spec | ⚠️ PARTIAL — its parent was an adversarial review; the spec itself is that reviewer's own output, unattacked |
| M4 held test | n/a — your design tension, not a review artifact |
| M5 behavior-pipeline questions | ❌ UNREVIEWED — written by the pilot's builder; the skeleton has never had a review pass |
| M6 backups | n/a — not a claim about the code |

## 1 · Blocked on Matt (nothing proceeds without a ruling)

| id | item | why it needs you | source |
|---|---|---|---|
| ~~M1~~ | ~~Guard-accept the diffs for C/D/E~~ **WITHDRAWN 2026-08-15 pending rework** — the adversarial review (`TRANSLATION_CENSUS_REVIEW.md`) found the coverage claim is **43%, not 58%**, with **47 of 49 kills unmeasured** (class subtraction by fiat, not replay). Verdicts: **C** safe minus one part; **A/B/D** need work (A's `declare-asserted-act` can bless a typo and nets +10 breach-rounds; B's diff no-ops for `cites` and would make `cites: null` illegal for 224/1386 items, pushing toward FABRICATED citations; D leaves 200 stored modules unloadable with no migration); **E/F** rejected. Nothing to accept until reworked and re-reviewed. | — | — |
| ~~M2~~ | ~~Ruling on fix F~~ **WITHDRAWN 2026-08-15 (Matt):** everything lands in the same next generation, so waiting buys no information. Build F like the others, in its own commit; if it is not ready and reviewed at launch, shelve it. The calendar decides, not a prior judgement of value. | — | — |
| ~~M3~~ | ~~Build the stage-4 client factory now?~~ **RULED 2026-08-15 (Matt, accepting the recommendation): DEFER.** Build order is F1/F2/F3 first, then the factory. Grounds: with the evidential stamp firing on ~0% of the corpus and 48% of 4c's denominator being text 4b sees verbatim, a working factory would produce authoritative-looking seat numbers nobody should trust. The two `seats.py` hardening items stay with the review agent (work order §3.2). The spec review continues (free, offline) so the spec is validated and amended for when the build happens. | — | — |
| ~~M4~~ | ~~held `test_d4b`~~ **RULED 2026-08-15 (Matt): pin the loudness rule.** Both branches now pinned; walkthrough suite green (42). Root cause was a STALE FIXTURE caused by this campaign's own `_supplement_borrow_glosses` helper — the CLI was correct throughout. | — | — |
| M5 | Behavior-pipeline design questions (6) | shape the ASP module for behaviours; no code hinges yet | `behavior_pilot/DESIGN.md` §6 |
| M6 | Backup: secrets to a password manager; second copy of the repo (R2/B2/Zenodo) | only unrecoverable asset is credentials; one GitHub account is the single copy | 2026-08-15 discussion |

## 2 · Ready to land (validated; gated only by sequencing)

| id | item | gate | source |
|---|---|---|---|
| R1 | Translation autofix (**fix A**) — written, 34 RED-first pins | wire at the START of the next corpus generation, never mid-corpus | `translate_autofix.py` |
| R2 | **Fix B** — `cites`/`clause_id` as a per-request `const` under strict json_schema | same gate as R1; "four lines, cannot regress" | `TRANSLATION_FIX_PLAN.md` §B |
| R3 | `promise_repair.py:868` — resume test reads `paused` only, so a cost-gate stop re-pays every plan | next repair run | pipeline-fix review |

## 3 · Designed, not built

**Build policy (Matt 2026-08-15):** every fix gets its OWN commit with its own
pins, so any one can be shelved at launch without disturbing the others. Build
them all now in parallel with the corpus run; readiness at launch decides what
ships. The gate is NOT the corpus run — it is the census review
(`TRANSLATION_CENSUS_REVIEW.md`, in flight): all of these rest on its numbers,
and if the class-subtraction simulation behind the 58% is overstated, the
targets change before anything is built.

| id | item | est. | source |
|---|---|---|---|
| D1 | Translation fixes **C, D, E** (ontology split; acts carry closure; requires/inputs carry name+arity+gloss) — 56% of the 58%; SEPARATE COMMITS | needs M1 + census verdict | `TRANSLATION_FIX_PLAN.md` |
| D1f | Translation fix **F** (body literals carry origin) — 32 more points; own commit, shelvable | census verdict; high risk → its own review round | `TRANSLATION_FIX_PLAN.md` §F |
| D2 | Live validation of the prompt-side fixes: 15-clause held sample, 3 arms, pre-registered falsifier | **~$0.09** | `TRANSLATION_FIX_PLAN.md` §live |
| D3 | Stage-4 evidential fixes: per-item echo stamp (F8/F1), 4c/4b independence (F2), layer-1 rendering reaching seats (F3) — **now the PREREQUISITE for the factory (M3 ruling)** | — | `STAGE4_DESIGN_REVIEW.md` |
| D3f | Stage-4 client factory — build AFTER D3, to the spec as amended by `STAGE4_FACTORY_SPEC_REVIEW.md`; NEW FILES ONLY (`seats.py` belongs to the review agent) | after D3 | `STAGE4_DESIGN_REVIEW.md` |
| D4 | Stage-4 `seats.py` hardening: defensive reply parsing in `judge`; `run_clause` records a skipped seat | delegated | `WORK_ORDER_review_agent.md` §3.2 |
| D5 | D6 stages 2-3 (dense-leaf bisect) — superseded by the dense-leaf recursion ruling; keep or formally drop | — | `EXPERIMENTS.md` 2026-08-12 |

## 4 · Delegated to the review agent (do not duplicate)

| id | item | phase |
|---|---|---|
| G1-G10 | guardrail findings: spend gauge under-reporting + stale cap, hook fails open, `--accept --all` doctrine, matcher mismatch | 1 |
| DOC | documentation-truth pass (`translate.py` banner, `node_corpus.py` usage, `READBACK_SMOKE`, `BATCH_DESIGN`, READMEs) | 1 |
| A1-A5 | stage-1/2 core findings (content guard, repair guards, RED test, `link.py`) | 2 |
| NC | `node_corpus.py --out` — prevent the corpus/fixture clobber (bitten 4×; currently detected, not prevented) | 2 |
| F4 | comparator authority-class collapse — raw edge numbers are ~93% authority fan-out and mislead every reader | 2 |
| BP | `behavior_pilot` honesty + missing-pin pass (not mutation infra) | 2 |
| C6 | consumer-check script: unresolved need is a hard reportable; modal-drift nodes carried; honest authority-excluded pair; config points at the CERTIFIED graph | 2 |

## 5 · Watch conditions (not work — things that must be re-checked later)

| id | condition | when |
|---|---|---|
| W1 | `requires-unprovided` in cleared graveyard entries is expected while the corpus is partial; if it survives a FULL corpus it becomes a real under-export finding | corpus completion |
| W2 | The 6 modal-drift nodes (2 teen-safety) must be carried forward as a known list | any consumer of the graph |
| W3 | Certification follow-ups C3 (3 reservation proses) and C5 (stale `promise_repair_report.json` counts: `declined_honestly` 3→2, `danglings_after` 24→25) | package assembly |
| W4 | Corpus generation discipline: this corpus is **gen-11**. Fixes make **gen-12**. Do not mix generations within one corpus — re-runs are whole-corpus | next run |
| W5 | Embedding spend is unledgered by construction (~$0.001/run) | any ledger audit |

## 6 · Closed

| id | item | closed by |
|---|---|---|
| — | batch checkpoint pause discarded already-paid rows (4a) | reviewed + pinned, 2026-08-15 |
| — | ds7 production graph certification | `production_certification.md`, 2026-08-14 |
| — | identical-retry seam guard; 10 routing-gap fixes | ds8 fix set, 2026-08-14 |
