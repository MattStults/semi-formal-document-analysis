# Work order — review-findings agent (issued 2026-08-15)

You wrote `REVIEW_2026-08-13_{stage12_core,stage34_seats,graph_v2,guardrails}.md`.
This order asks you to **land** the parts of them that are safe to land, in two
phases, without colliding with work running in another console.

The coordinating instance verified a sample of your findings before writing
this: **G1 is real and reproduced** (`spend.py` reports `$3.449 of $8.50 (41%)`
while `usage.jsonl` totals `$9.20` and the live authorization is `$20`;
`2122 logged calls had no price entry`). Your seats **F8** (`ECHO_LEVEL = 0.90`)
was independently rediscovered by a separate stage-4 design review — treat it as
confirmed. Two corrections to your reports are in §5.

---

## 1. Hard rules (collision safety — a paid run is in flight)

* **A live batched translation run is executing** against
  `walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/`. Do not stop it,
  do not touch its inputs or outputs.
* **NEVER modify** (owned by the other console):
  `promise_repair.py`, `dispatch_core.py`, `translate_exec.py`, `splice_seat.py`,
  `run_checkpoint.py`, `recurse_driver.py`, `frontier_review.py`, `fixup.py`,
  `graph_corrections.py`, `risk_queue.py`, `config_corpus_all.json`,
  `node_corpus_all.json`, `node_corpus.json`, `config_graph_nodes.json`,
  and **anything under any `runs/` or `translation_sample/runs/` directory**.
* **Never `git checkout`/`switch` in the main working tree.** Phase 2 runs in a
  **separate git worktree** (§3) so the main console's checkout is untouched.
* **Zero API spend.** Everything here is offline. If a task seems to need a live
  call, stop and report instead.
* Repo doctrine applies (root `CLAUDE.md`): never lower a quality floor to make
  something pass; a fix's scope is the adjudicated finding, not the class it
  belongs to; rulings go in the repo with the rejected alternative named;
  registration fences a module (new test → `conftest._OPTIONAL`, etc.).
* **Verification standard for every item:** the pin must fail RED against the
  pre-fix code (state which, and how you verified), then pass. Run the affected
  suites plus `phase_1` excluding `resolve_runs`, and report numbers.

---

## 2. PHASE 1 — now, on a branch off current `HEAD`, then a PR

Branch: `guardrails-fixes`. Base it on current `walkthrough-prototype` HEAD.
These files do **not** intersect the running work.

1. **G1 (HIGH) — the budget gauge is wrong in both directions.** Add the
   campaign's inline provider to `semi-formal-experiment/providers.json`
   (`together-deepseek-v4-flash` / `deepseek-ai/DeepSeek-V4-Flash-0731`,
   `price_per_mtok [0.14, 0.28]`, base_url `https://api.together.xyz/v1`,
   key env `TOGETHER_API_KEY`) so the 2,122 unpriced rows price; reconcile the
   cap constant with the live authorization (**$20.00**, raised 08-14 — see
   `resolve_runs/graph_v2/EXPERIMENTS.md`); and make the gauge **refuse to
   report a total when any row is unpriced** rather than silently understating.
   Also handle the batch-discount question honestly: rows billed at 50% must not
   be priced at list, or say in the output that they are.
   Pin: a usage row with no price entry makes the total loud, not quiet.
2. **G2 (HIGH) — the pre-commit hook fails OPEN** when `python3` is absent.
   Make it fail closed (block the commit with an actionable message).
   Pin it by simulating a missing interpreter.
3. **G6, G9, G10 (MED)** — the `--accept --all` contradiction with
   `REVIEW_QUEUE §1`, the two contradictory ceilings, the `fnmatch` vs `glob`
   mismatch and unquoted `$staged`. For G6, decide **by name** whether the code
   or the doctrine is wrong and record the ruling; do not silently delete either.
4. **G8 + the documentation-truth pass (MED — high value, low risk).** Several
   docs actively lie, which is worse than silence:
   * `paper_pipeline/phase_1/translate.py`'s module docstring and end-of-run
     banner still say *"⛔ IT VALIDATES NOTHING … no compile, no link, no
     read-back"* — the opposite of current behaviour. (Editing only these two
     strings in `translate.py` is permitted; nothing else in that file.)
   * `resolve_runs/graph_v2/node_corpus.py`'s "Then:" docstring is wrong twice
     (`--dry-run` is not a flag; the config path is relative to `phase_1/`).
   * `READBACK_SMOKE.md` gap list is stale (gaps 1/3/4/5 are fixed and pinned by
     `test_stage4_node_plumbing.py`; only gap 2 remains).
   * `BATCH_DESIGN.md` says batch is "not yet built" — it is built and default.
   * `phase_1/README.md` stale figures (checks count, char count, the invisible-
     spend figure that is a ~300× understatement).
   * `graph_v2/README.md` points newcomers at `EXPERIMENTS.md` (2,000+ lines,
     chronological, late entries retract earlier ones) — add a "read the last N
     entries + these named reports" pointer instead.
   Rule for this item: **change only what you can verify against the code**, and
   cite the file:line evidence for each correction in the PR body.

**Phase 1 deliverable:** one PR titled `guardrails + documentation truth`,
base `walkthrough-prototype`. Body: a table of finding → disposition
(FIXED / RULED / DEFERRED-with-reason), the RED evidence per pin, suite numbers,
and anything you chose **not** to fix and why.

---

## 3. PHASE 2 — in an isolated worktree, then a PR for hand-off

Create the isolated checkout so the other console's working tree is never
disturbed:

```bash
cd /Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis
git worktree add ../sfda-review-worktree -b review-followups
cd ../sfda-review-worktree     # do ALL phase-2 work here
```

Work items, in priority order:

1. **Stage-1/2 core findings** (§A1 content guard, §A2 repair guards, §A3 the RED
   test, §A4/A5 `link.py`) — your `stage12_core` report says all are still live
   and the scope files were untouched by the ds8 work. Land them with pins.
2. **Stage-3/4 seat hardening — build to the spec, do not redesign.** Read
   `paper_pipeline/phase_1/STAGE4_DESIGN_REVIEW.md` first; it is the governing
   design document and it was written after your report. Land exactly two things
   it names as belonging in `seats.py` rather than in any factory:
   * **defensive reply parsing in `judge`** (fence-stripping, verdict
     normalisation to the *unchanged* closed set, `SeatError` on anything else) —
     5 of 7 realistic live reply shapes currently raise uncaught exceptions while
     every mock returns clean JSON;
   * **`run_clause` recording a skipped seat** instead of `continue`.
   Then your **F8** (`ECHO_LEVEL = 0.90`, `readback.py:70`) and the review's F1:
   the evidential stamp is keyed on the **clause mean**, so it fires on ~0% of the
   corpus while 6.6% of items sit at per-item echo ≥ 0.90. Move the stamp to
   per-item grain. ⛔ **Do not build the seat client factory** — that is a
   separate, specified project and the natural implementation destroys 4c's
   anchor property.
3. **`node_corpus.py --out`** — the corpus/fixture clobber is currently
   *detected, not prevented* (it has bitten four times). Add `--out` and make the
   full-corpus path write beside, not over, the pinned sample. Do not touch the
   two corpus JSONs themselves.
4. **F4 — comparator authority-class collapse** (measurement hygiene, never
   built). `graph_compare.py` should be able to report edge recall/precision with
   authority-class names collapsed, because the raw numbers are ~93% authority
   fan-out and mislead every reader. Add it as an **option that does not change
   the default output**, plus the pin.
5. **Coverage pass on the new-but-now-stable code**: `behavior_pilot/`. (Leave
   `frontier_review.py` and `fixup.py` alone — still moving in the other console.)
6. **Certification follow-ups C3/C5/C6** — see `production_certification.md`.
   C5 (stale counts in `promise_repair_report.json`) is **report-only**: correct
   the numbers in a **new** file or a documented amendment; do not rewrite an
   artifact under `runs/`.

**Phase 2 deliverable:** a PR from `review-followups`, base
`walkthrough-prototype`, titled `review follow-ups (stage 1-2, seats, tooling)`.
It will be **handed to the coordinating instance to fold in**, so the body must
carry: per-item disposition, RED evidence, suite numbers, every ruling with its
rejected alternative, and an explicit list of files touched.

---

## 4. What NOT to do

* Do not fix `frontier_review.py`, `fixup.py`, or anything in §1's never-modify
  list — they are mid-change elsewhere.
* Do not build the stage-4 client factory (§3.2).
* Do not "fix" `test_d4b_no_table_and_no_concepts_declared_is_silent` (§5).
* Do not touch `usage.jsonl` or any run artifact; the ledger is evidence.
* Do not raise a budget cap, relax a threshold, or delete a failing pin to make a
  suite green. If something cannot be fixed without that, report it instead.

## 5. Two corrections to your reports

* **G7 is not a defect.** `test_link.py::test_d4b_no_table_and_no_concepts_declared_is_silent`
  is **deliberately held** — a design-tension item the owner is aware of and has
  chosen not to resolve. Re-label it as held; leave it failing. (Its guard is
  currently unexercised; if you want to add value, rebuild the fixture so the
  guard is exercised — do **not** delete the test.)
* **G4 is confirmed, and already recorded** on the other console as routing-gap
  finding 6 (embedding spend unledgered by construction, ~$0.001/run). Cross-
  reference rather than re-deriving it.
