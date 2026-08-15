# Adversarial review — phase-1 guardrails + documentation truth (`guardrails-fixes`), 2026-08-15

**VERDICT: PASS — the branch is correct, RED-first-pinned, and within scope. Zero FIX-REQUIRED findings. Two SHOULD findings, both PRE-EXISTING holes one layer away from the adjudicated fix (neither introduced nor worsened by this diff, both outside its strict scope — follow-ups, not blockers).**

Subject: `git diff walkthrough-prototype...guardrails-fixes` — 6 commits `3748da0..73580e8`, merge-base `12891dc` (verified: `git merge-base` = `12891dc6d8…`, matches the claimed base), 13 files, 650 insertions / 113 deletions. Reviewer ran everything offline against scratch copies and the worktree; no API calls; the real `usage.jsonl` and `reviewed.json` were only ever READ (hash-verified untouched); the main tree was never modified (scratch worktree added/removed via git only).

Method note: `walkthrough-prototype` moved during the review (other console; `b3803e5` → `6d3bf31` → `66cfba8` → …). Verified by `git diff --name-only 12891dc <tip> -- <the 13 reviewed files>` = EMPTY at each tip, so the scratch base checkout (detached at the then-tip) is byte-identical to the merge-base for every file under review. The post-branch commits (work-order amendments, graveyard census, repair census, open-items register, run artifacts) have ZERO file overlap with the branch's 13 files (`comm -12` empty) — no merge collision in the reviewed set.

---

## §A — RED→GREEN re-adjudication

Method: scratch checkout of pre-fix code (`git worktree add --detach /tmp/rev-p1-base walkthrough-prototype`, venv symlinked), branch TEST files copied in via `git show guardrails-fixes:<path>`, run there (expect RED), then run in the branch worktree (expect GREEN).

**Base run: 15 failed, 49 passed** — exactly the 15 claimed pins fail and all 49 pre-existing tests pass (scratch tree healthy). **Branch run: 64 passed.**

| pin | RED against base (evidence) | GREEN on branch |
|---|---|---|
| G1 loud-total pin (`test_a_usage_row_with_no_price_entry_makes_the_total_loud_not_quiet`) | `AttributeError: module 'spend' has no attribute 'report_lines'` — mechanism absent; BEHAVIOURAL base repro in scratch dir: ledger {1 priced row, 1 unpriced 5M+5M-token row} printed `TOTAL … $0.001 of $8.50 (0%)` with only a `!!` line — partial sum as the total | PASS |
| G1 `--check` fail-closed pin (`test_check_fails_closed_when_any_row_is_unpriced`) | `AttributeError: no attribute 'run_cli'`; BEHAVIOURAL base repro: `spend.py --check 1000000` on the same ledger → **exit 0** (gate certified a sum it could not finish) | PASS |
| G1 campaign-priced pin (`test_the_campaign_inline_provider_is_now_priced`) | `AssertionError: the ledger's dominant model has no price` — `deepseek-ai/DeepSeek-V4-Flash-0731` absent from base `prices()` | PASS |
| G1 cached-at-full-rate pin, fully-priced control, `--check`-passes control, BUDGET pin, 2 batch-caveat pins | all RED (`KeyError`/`AttributeError`/`BUDGET == 8.50`/no caveat machinery) | all PASS |
| G2 missing-interpreter pin (`test_pre_commit_BLOCKS_when_the_interpreter_is_missing`) | the review's exact repro re-run against the BASE hook: `env PATH=/tmp/empty GUARD_STAGED_FILES="walkthrough/paper_pipeline/phase_1/schema.py" /bin/sh …/pre-commit` → `python3: command not found` → **exit 0** (fail-OPEN reproduced) | PASS (blocks, "COMMIT BLOCKED") |
| G2 crashing-python3 pin (`test_pre_commit_BLOCKS_when_the_guard_crashes`) | fake `python3` exiting 1 → base `|| exit 0` → exit 0 | PASS |
| G2 sentinel-code pin (`test_watches_cli_names_a_reserved_skip_code`) | base `--watches walkthrough/README.md` exits 1 (= Python's crash code), not 3 | PASS (3 skip / 0 fire) |
| G6 pin (`test_accept_all_is_refused_not_a_bulk_attestation`) | base `guard.accept(["--all"])` returned **0** (`assert 0 != 0` — bulk attestation recorded) | PASS (rc 2, no stamp written) |
| G10 matcher pin (`test_watches_agrees_with_resolve_star_does_not_cross_slash`) | base fnmatch crossed `/` — staged `prompt/sub/x.md` matched the `prompt/*.md` entry | PASS |
| G10 quoting pin (`test_a_staged_path_with_a_space_reaches_the_gate_as_one_path`) | base hook word-split `my file.md` into two bogus paths → exit 0, gate skipped (failure text captured in the RED run) | PASS |
| paired control (`test_two_unwatched_paths_are_still_silent…`) | passed on base too (correct for a control) | PASS |

RED adjudication: **all 15 claims hold.** The RED failures are not environmental (venv symlink present; 49 pre-existing tests green on the same scratch tree).

---

## §B — new findings in the changed code, ranked

### FIX-REQUIRED: none.

### SHOULD-1 — the gauge can still be silenced by a MALFORMED ledger row (pre-existing hole the new refusal does not cover; docstring now overstates)
`spend.py:rows()` (branch `semi-formal-experiment/spend.py:79-86`) does `except json.JSONDecodeError: pass` — a truncated/corrupt row is dropped BEFORE pricing, so it never counts as "unpriced" and never triggers TOTAL REFUSED / CHECK REFUSED. Repro (scratch copy of branch spend.py + providers.json, scratch usage.jsonl — real ledger untouched):
```
printf '%s\n' '{"model":"gpt-5.6-luna","prompt_tokens":999000000,"completion_tokens":999000000' > usage.jsonl
spend.py            # prints TOTAL $0.000 of $20.00 (0%), "usage.jsonl rows: 0"
spend.py --check 0.0001   # exit 0 — certifies $0 against any bar
```
A killed-mid-append write is a realistic shape for this live-appended file. This is the SAME class as G1 ("a partial sum printed as the total"), and the new docstring (`spend.py:9-11`, "Rows the price table cannot price are louder still: the report REFUSES its total and `--check` fails closed") is not true of rows that cannot be PARSED. Missing `usage.jsonl` has the same shape (exit 0, `$0.000`). Ranked SHOULD, not FIX-REQUIRED, because it is pre-existing (base `rows()` is byte-identical), the adjudicated finding was "a row with no price entry", and doctrine fences scope — but it is the natural follow-up ruling (loud-count of unparsable rows, or refuse on `unparsed > 0`). Confidence: high (ran it).

### SHOULD-2 — the refusal lives in the CLI only: `ladder.preflight()` and `annotate.py` still gate on the silent partial sum (pre-existing consumers, unchanged)
`semi-formal-experiment/ladder.py:2275-2277`: `spent = spend.total()["total"]; budget = spend.BUDGET …; ok = (spent + proj) <= budget` — `total()` still returns the partial sum with the unpriced count merely carried in the dict, and `preflight` ignores it. Same at `ladder.py:2373,2422` (in-run spend tracking) and `annotate.py:1395` (`"spent_so_far": spend.total()["total"]`). With today's ledger (1 unpriced embedding row, ~$0.001) the undercount is small; the mechanism is exactly the G1 shape one API layer down, and `spend.py`'s new docstring speaks of the gauge where these consumers read the number. Pre-existing, outside the adjudicated finding's scope (G1 pinned the gauge/`--check`), hence SHOULD-follow-up (e.g. `total(refuse=True)` or preflight checking `unpriced`), not a branch blocker. (`ladder.py:2271` docstring also still says "The session budget is $7.50" — same follow-up.) Confidence: high (read; the ledger state was run-verified).

### NITs (none blocking; each verified)
1. **`PRICED SUBTOTAL (PARTIAL)` line prints the ALL-rows count in its `calls` column** (`spend.py` `report_lines()`, `f"{'PRICED SUBTOTAL (PARTIAL)':34s} {t['calls']:5d}"`) while its cost column is priced-only; the REFUSED block below clarifies, but the column itself mislabels. Observed: subtotal row showed calls=3 with one row unpriced.
2. **`phase_1/README.md` dates the base commit wrongly**: "(12891dc, 2026-08-15)" — `git show -s 12891dc` = **2026-08-14** 18:58. The measurement happened 08-15; the parenthetical reads as the commit's date.
3. **`phase_1/README.md` scope ambiguity**: "2,121 calls, embedded sum $7.7967" is CAMPAIGN-scoped (verified EXACTLY: 2,121 campaign rows, 2,118 with `cost_usd`, sum $7.7967; recompute-equality holds on all 2,118 — 0 mismatches) but sits beside "whole-ledger priced subtotal $11.249" (also exact; whole ledger = 2,748 rows at the base commit). Both figures true; a careless read takes 2,121 as the whole ledger.
4. **`config.json` is now self-contradictory** (file untouched by the branch, outside its edit allowance): `:50` `_inline_why` says the model "is not a row in providers.json" — it now is; `:58` still says "hard $8.50 ledger cap". Follow-up doc pass.
5. **Residual stale-spend claims outside the sanctioned doc list**: `walkthrough/STATE.md:175` ("Spend from this harness is currently invisible to spend.py … Being fixed") and `TRANSLATION_RUNBOOK.md:22` (S1: "BUDGET = 8.50, and this harness's spend is invisible to it") + `:379` (§6). Both now false. The sanctioned G8 list did not include these files, so this is scope-respecting residue, flagged for the same documentation-truth discipline the branch applied elsewhere. (`phase_1/README.md`'s own disclosure of the two hardcoded stale mechanisms inside translate.py — the invisibility warning and `visible_to_spend_py: false` — is honest and accurate.)
6. **3 `openai/gpt-oss-20b` rows carry embedded `cost_usd` ≈1.49× spend.py's recomputation** (e.g. recalc $0.007014 vs embedded $0.010464) — a pre-existing price-table/call-time divergence outside the campaign; whole-ledger priced total $11.249 is ~$0.008 under those rows' own arithmetic. Informational; the README's equality claim is scoped to the campaign's 2,118 rows and holds exactly there.
7. **Report mode exits 0 while refusing the total** (refusal is loud text; only `--check` exits non-zero). Deliberate and coordinator-acknowledged; a script reading only the report exit code would miss the refusal. Noted, not contested.
8. **git-quoted paths**: a staged path git renders in quoted form (tab/quote/unicode → `"escaped"`) would reach the matcher literally, match nothing, and skip silently on rc 3. No watched file can have such a name today; theoretical. (`set -f` + newline-IFS handles spaces and glob chars — run-verified below.)

### Direct answers to the ranked hunt questions
* **B1 refusal semantics** — all-priced scratch ledger: TOTAL prints `$1.820 of $20.00 (9%)` (arithmetic verified incl. cached-at-full: 2M prompt w/ 1M cached + 0.5M out = $0.42); `--check 5.00` exit 0, `--check 0.001` exit 1 OVER BUDGET; unpriced row → PRICED SUBTOTAL + TOTAL REFUSED naming the model, `--check 999999` exit 1 CHECK REFUSED; `--would-cost` prints a labelled PARTIAL warning. Refusal triggers on unpriced rows ONLY — see SHOULD-1 for the other silencing state.
* **B2 exit-code space** — exit 3 is producible ONLY by the `--watches` CLI mapping (`guard.py:415-426`); `check()`→0/1/2, `accept()`→0/2, `self_test()`→0/1; a crash anywhere exits 1 → the hook BLOCKs. Broken watch list: `watches()` returns 0 (hook RUNS the gates) and `check()` then loud-ERRORs rc 2 — fail-closed chain intact. Zero-watched-files commits: silent exit 0 (run: `GUARD_STAGED_FILES="walkthrough/README.md"` → exit 0, no output; also with empty lines interleaved).
* **B3 quoting/glob** — hook end-to-end with `GUARD_STAGED_FILES="walkthrough/paper_pipeline/phase_1/prompt/[z].md"`: `set -f` prevented expansion, gate FIRED, ran the real gates (pytest examples 15 passed/1 xfailed, guard GREEN) → exit 0. Deeper-level path → silent skip 3. Space-path covered by the pin + GREEN.
* **B4 guard** — per-file accept verified end-to-end on scratch state (fresh NEVER-REVIEWED rc 1 → accept one file rc 0 → partial → edit → STALE rc 1 → `--accept --all` rc 2 with the stamp BYTE-IDENTICAL → no-args rc 2 → unwatched rc 2 → both files by name rc 0 → GREEN rc 0); the worktree's real `reviewed.json` sha256 unchanged before/after.
* **B5 providers.json row** — `[0.14, 0.28]`, base_url, key-env all match `config.json:52-58`'s recorded sources (together.ai page fetched 2026-08-07); the row prices through `cost_of` (scratch-run verified); real frozen ledger: exactly 1 unpriced row remains (`text-embedding-3-small`, the by-construction-unledgered embedding path, routing-gap finding 6 — correctly NAMED by the refusal).
* **B6 doc-truth** — (a) `translate.py --self-test` RUN: **51 passed, 1 failed (the known Q-4), exit 1** = the README's "52 checks" exactly; the assembly check itself prints **37,891 chars from 4 files**, matching the README figure. (b) "stage 2 is the gate": unconditional `repair_loop(...)` call at `translate.py:1384-1389` under the "⭐ STAGE 2 IS THE GATE, ALWAYS" comment (:1377-1383 — the builder's cite is right), and `repair_loop` runs `look(initial_raw, 1)` → `_checks.run_checks(..., attempt=1)` at :2565/:2579 — checks run on the FIRST attempt. (c) graph_v2 corrections: `BATCH_DESIGN.md`'s status block matches `config_corpus_all.json` exactly (`execution.mode: batch`, `batch_min_pending: 8`, Matt's 2026-08-14 note verbatim, `checkpoint_pause: false`); `graph_v2/README.md`'s "last six entries from 'ds7 PRODUCTION GRAPH -- CERTIFIED'" verified (EXPERIMENTS.md 2,901 lines, entry at :2675, exactly 6 `##` headers from there to EOF, all 2026-08-14; 2 "CORRECTION to this log" retraction markers); the named reports exist; READBACK_SMOKE's cited pin file exists (21 tests, "LIVE-SHAPED pin (READBACK_SMOKE gap 1)" marker present); the batch-billing note's grounds verified in `dispatch_core.py:1233` (`T.response_envelope(self.prov, body)` — batch rows ledger through the same envelope, no billing-path marker). BUDGET authorization history verified against EXPERIMENTS.md **:1291** ($10.00, exact line) and **:2712** ($20.00 "Matt +$5", exact line).

---

## §C — spec-drift verdict: **NO DRIFT.**

* `translate.py` diff is **EXACTLY the two sanctioned strings** — hunk audit of the full diff: only `@@ -4,14 +4,20 @@` (module docstring) and `@@ -1512,7 +1518,9 @@` (end-of-run banner). Nothing else in the file.
* Never-modify grep over the diff (`dispatch_core|promise_repair|translate_exec|risk_queue|recurse_driver|frontier_review|fixup|splice_seat|run_checkpoint|graph_corrections|node_corpus_all|config_corpus_all|config_graph_nodes`): 6 hits, ALL prose inside sanctioned edits (the providers.json `batch_billing_note`, the BATCH_DESIGN.md status block, the node_corpus.py usage example naming `config_graph_nodes.json` as a --config ARGUMENT). `git diff --raw` confirms zero such files MODIFIED.
* `usage.jsonl` and everything under real `runs/` directories: untouched (diff-stat and `--raw` verified; the only `resolve_runs/` edits are the four §2-G8-sanctioned graph_v2 docs).
* No new API/spend path: grep of added lines for `urllib|requests|curl|http.client|socket` = empty; the providers.json change is a DATA row; all new code is reporting/matching.
* No stray files: all 13 entries are `M` on existing 100644/100755 paths — no new files, no symlinks (no 120000 mode), no scratch outputs; worktree `git status` clean apart from the pre-existing `.venv` symlink.
* Scope discipline otherwise exact: G3/G5 deferred (not touched), G4 cross-referenced not re-derived (the embedding row is named by the refusal, consistent with its admitted unledgered-by-construction status), G7/test_d4b untouched (still failing at HEAD — see §A suite numbers), no cap raised without the recorded Matt authorizations (BUDGET comment cites both, line-verified above).

## §D — doctrine verdict: **COMPLIANT.**

* **Every fix has a pin** — 15 new pins, each re-verified RED against base then GREEN (§A). Doc-truth items carry run-verification instead (appropriate; they are prose).
* **Rulings recorded with rejected alternatives** — all five claimed rulings found: G6 (`guard.py` DESIGN NOTE "RULING 2026-08-15", rejected: "keep `--all` as an escape hatch"); cached rate (providers.json `cached_price_note`, rejected: `cached_input_per_mtok: 0.03`); batch discount (`batch_billing_note`, rejected: half-list pricing and ledger batch-markers, each with its reason); fail-closed mechanism (hook + `guard.py:416-425` comments — skip moved OFF exit 1 because 1 is Python's crash exit; the rejected alternative is named by its failure mode rather than a "Rejected alternative:" phrase — format looser, substance present); matcher direction (`_glob_match` docstring + pin docstring — "Over-blocking is the safe direction, but 'what is watched' must have ONE answer").
* **No lowered floor** — every behavioural change is strictly stricter (open→closed scoping gate, silent undercount→refusal, bulk attestation→refusal, ambiguous matcher→single-answer matcher). The one removed capability (`--accept --all`) is the recorded G6 ruling, not a quiet deletion.
* **No deleted/weakened pins** — zero `-def test_` lines in the diff; the one pre-existing test edited (`test_pre_commit_is_silent_when_nothing_watched_is_staged`) was adapted to the new newline-joined helper signature with its assertion intent intact (still passed on BASE in my RED run, so not gamed).
* **Registration fence** — all new tests live in pre-existing registered files; no new module needed `conftest._OPTIONAL`.

## §E — what I did not check

* G3 (arm drift), G5 (N-of-M deletion) — deferred findings, out of phase-1 scope; untouched, verified absent from the diff.
* READBACK_SMOKE gap-fixes verified at citation-level (pin file + §1 marker exist, counts match), not by re-running/re-deriving each gap's fix semantics.
* The 4 skipped semi-formal-experiment tests and any optional-dependency behaviour they fence.
* Hook behaviour under filenames git must C-quote (see §B NIT-8) and under the literal PR-time merge of the later `walkthrough-prototype` commits (file-overlap verified empty, but the merge itself is the coordinator's act).
* Whether the live campaign (other console) is affected by hook strictness in its own commits — not observable from here, and the hook's BLOCK messages are actionable by design.
* The held-RED `test_d4b_no_table_and_no_concepts_declared_is_silent` (deliberately failing; the walkthrough suite's ONLY failure: **1 failed, 1211 passed, 1 xfailed**; semi-formal-experiment suite from its own cwd: **2267 passed, 4 skipped**).
