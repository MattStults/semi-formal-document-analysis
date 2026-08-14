# Engineering review — the meta-instruments, 2026-08-13

Scope: the guardrails, ledgers and evaluation harnesses — the instruments that certify
everything else. Staleness guard (`model/guard.py` + hook), spend accounting
(`semi-formal-experiment/spend.py` + `usage.jsonl`), the eval harness
(`phase_1/eval.py`, `eval_arms/make_arm.py`), and status-attestation hygiene in the
walkthrough's current docs. **REVIEW ONLY — nothing was modified.** Scratch repros ran in
`mktemp -d` directories; no API calls, no spend, `guard.py --accept` never run against the
real repo (the sandbox also enforced this).

The meta-question over everything: **could any of these instruments report "all good"
while broken?** Three verified yeses below (G1, G2, G3).

---

## Baselines (exact commands, run 2026-08-13 from repo root)

Interpreter: `semi-formal-experiment/.venv/bin/python`, run from
`/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis`.
HEAD: `8614f44` (walkthrough-prototype, 2026-08-13 13:40).

| command | result |
|---|---|
| `…/.venv/bin/python walkthrough/model/guard.py` | **GREEN, exit 0** — "every watched file is at its recorded review point (6 file(s))". ⚠️ The task brief (and REVIEW_QUEUE §1, dated 2026-08-07) expected RED with five unreviewed files; all six were accepted 2026-08-07/2026-08-12 (`model/reviewed.json`; last commit touching watched files + stamps is `3d856a8`, 2026-08-12). Nothing to clear; state reported as found |
| `…/.venv/bin/python walkthrough/model/guard.py --self-test` | **7/7 PASS, exit 0** (loud-ERROR cases for empty/unreadable watch list, no-match pattern, staleness fire/no-fire, `why` presence) |
| `pytest walkthrough/model/test_model.py walkthrough/paper_pipeline/phase_1/test_eval.py walkthrough/paper_pipeline/phase_1/eval_arms/test_make_arm.py -q` | **72 passed** in 6.24s |
| `pytest walkthrough/ -q` | ⛔ **1 failed, 1003 passed, 1 xfailed** in 158s — the failure is G7 |
| `…/.venv/bin/python walkthrough/paper_pipeline/phase_1/translate.py --self-test` | **51 passed, 1 failed, exit 1** — the one red is the disclosed Q-4 `dryrun.txt` staleness (tracked as xfail(strict) in `test_prompt_examples.py`) |
| `…/.venv/bin/python walkthrough/link.py --self-test` | **21/21 passed, exit 0** |
| `semi-formal-experiment/.venv/bin/python semi-formal-experiment/spend.py` | TOTAL **$2.072 of $8.50 (24%)** over 2,092 rows — `!! 1626 logged calls had no price entry`; audit: no unlogged-model artifacts |
| `… spend.py --check 8.50` | **exit 0** (under budget) — see G1 for why this is misleading |
| `mutate_schema.py` | **NOT RUN** — blocked by the session sandbox on both attempts. Last independently re-run figure: 44 guards / 0 survivors (`ENGINEERING_REVIEW_2026-08-07b`); REVIEW_QUEUE §6 says 46 |
| hook end-to-end: `GUARD_STAGED_FILES="walkthrough/paper_pipeline/phase_1/schema.py" /bin/sh walkthrough/model/hooks/pre-commit` (cwd = repo root) | **exit 0**: pytest `test_prompt_examples.py` → 15 passed, 1 xfailed; then guard GREEN |

Hook installation state: `.git/hooks/pre-commit` is a **symlink →
`../../walkthrough/model/hooks/pre-commit`**, so the byte comparison is trivially exact
(same file); target is `rwxr-xr-x`; the symlink resolves (the hook ran). ⚠️ Installation
is per-clone and unverified by anything — a fresh clone has no hook and nothing notices
(STATE.md's process note says to check by hand; see G2/I-2). `guard_hook.py` (Claude Code
PostToolUse, advisory) is installed via `.claude/settings.json`, invoked through bare
`python3`, which on this machine resolves to **another project's venv**
(`introspection_leakage/.venv/bin/python3`, 3.10.6) — it works (stdlib only) but is
environment-dependent.

---

## CONFIRMED findings, ranked

### G1 · HIGH — the budget gauge reads 24% while the project's own arithmetic says the $8.50 cap has been passed; the one budget gate exits 0

`spend.py` reports **$2.072 of $8.50 (24%)**. But **1,626 of 2,092 ledger rows carry no
price entry** — every call of the walkthrough's workhorse model
`deepseek-ai/DeepSeek-V4-Flash-0731` (864 `graph-build`, 694 `together-deepseek-v4-flash`,
22 `parity`, 15 `spot2`, 13 `graph-probe`, …). Those rows are not information-free: each
carries a top-level `cost_usd` computed at call time by the harness's own conservative
arithmetic (cached input billed at the FULL input rate; `priced_by:
walkthrough/paper_pipeline/phase_1/config.json`).

Measured off `usage.jsonl` (scratch script, offline):

* 1,622 V4-Flash rows carry `cost_usd`; **sum = $6.836**. The 3 rows without it ≈ $0.003.
* Priced rows: $2.072. **Adjusted total ≈ $8.91 of a $8.50 hard cap** — over.
* Even billing cached tokens at together's discounted rate (~0.1×), the same rows cost
  ≈ $5.07 → true total ≈ $7.14, **84% of cap** — still not "24%".

The mechanism, verified in code: `spend.py:prices()` builds its price table from
`providers.json` only; `cost_of()` returns `None` for the inline provider and `total()`
skips the row — it never consults the row's own `cost_usd`. Consequences:

* `spend.py --check 8.50` → **exit 0**. The machine gate cannot see 78% of the calls.
* AGENTS.md tells new agents "hard budget ceiling … currently $8.50, ~$2.15 used" —
  understated ~4× on the conservative reading (G9).
* STATE.md's 2026-08-07 "Being fixed" note on this gap: **still unfixed**, and the gap
  grew from "311 unpriced calls" (ENGINEERING_REVIEW_2026-08-07b F12) to 1,626.

The warning machinery is real — every run prints `spend_invisibility_warning()` and
`run.json` records `visible_to_spend_py: false` — but the *instrument of record* still
publishes a number that excludes the dominant spend path. A budget gauge that reads 24%
when the conservative ledger says "over cap" is the pass-looks-like-did-not-run shape at
the level of money.

Confidence: high (ran it).

### G2 · HIGH — the pre-commit hook fails OPEN when the guard cannot run: no `python3` on PATH ⇒ silent commit pass (ran it)

`walkthrough/model/hooks/pre-commit:20`:

```sh
python3 walkthrough/model/guard.py --watches $staged || exit 0
```

Any non-zero exit from this line — interpreter missing (127), `guard.py` crashing,
`guard.py` absent — is indistinguishable from "no watched file staged", and the hook
exits 0 with the commit proceeding. Reproduced in a scratch repo (guard deliberately left
RED/unreviewed there):

```
$ env PATH=/tmp/empty_path_dir GUARD_STAGED_FILES="walkthrough/prompt/00_task.md" \
      /bin/sh walkthrough/model/hooks/pre-commit
walkthrough/model/hooks/pre-commit: line 20: python3: command not found
→ exit 0          # watched file staged, guard unreviewed, commit would proceed
```

The design considered exactly this class: `guard.watches()` returns 0 on a broken watch
list ("a broken watch list must make the hook RUN, not skip") — but a missing/crashed
*interpreter or guard* is not covered. Two aggravators, both verified:

* the hook calls **bare `python3`**, which on this machine resolves to another project's
  venv; a GUI git client or a clean-PATH shell may have no `python3` at all;
* the guard-crash variant of the same line is mechanically identical (`|| exit 0` on any
  non-zero rc) — not run (sandbox declined corrupting even the scratch guard.py), but no
  code path separates it from the missing-interpreter case above.

Contrast: the hook's other gates fail closed — missing venv BLOCKS (`pre-commit:32-38`),
pytest failure BLOCKS, guard-RED BLOCKS (`|| { … exit 1; }`). Only the scoping gate fails
open. Being right and unseen cost two hours on 2026-08-07; this is the same failure with
the seeing part removed whenever the environment shifts.

Confidence: high (ran the missing-interpreter case).

### G3 · HIGH — eval arms have measurably DRIFTED from the live prompt; the diff attestation is write-only; three of four arm dirs carry no attestation at all

`make_arm.py`'s contract — "an arm is generated as a VERIFIED one-line diff of the live
prompt, never a copy" — is enforced **only at generation time**. Nothing ever re-checks it:

* grep for readers of the provenance sidecar: only writers (`make_arm.py:96`,
  `select_category_clauses.py:193`) and a test that it was written. `eval.py` compares
  arms to EACH OTHER (`assert_arms_differ`), never to their claimed parent.
* Measured drift, offline:
  * live `prompt/00_task.md` sha256 `0463449d…`; arm copy
    `eval_arms/prompt_head/00_task.md` sha256 `27779899…` — **differ**. The arm carries
    the OLD rule 10 ("Include arity everywhere a predicate is named"); the live file's
    rule 10 was expanded (value-slot carve-outs, `assistant/1` rejection). Five lines
    apart, meaningfully different instructions.
  * `eval_arms/prompt_b/00_task_no_emphasis.md.provenance.json` records
    `source_sha256: 043265ab…` ≠ live `0463449d…` — the one generated arm's attestation
    is stale; the note says "Regenerate after any edit to the source", and nothing
    enforces or even checks it.
  * `prompt_head/`, `prompt_head_plus6/`, `prompt_a_pre_example/` contain plain copies
    with **no provenance sidecar at all** — not even auditable after the fact.
* `config_arm_b.json` mixes a frozen generated file with LIVE
  `prompt/10_output_format.md` etc., so the arm's composition itself moves when the live
  prompt moves, while its "one-line diff" half stays frozen.

Past RESULT runs are not invalidated (they ran before the drift), but the arms directory
now holds drifted copies that any future run would use while the §6 claim reads
"never a copy". This is the exact failure `make_arm.py`'s docstring says it exists to
prevent — "the original gets edited, the copy does not, and the run then measures every
drift between them while reporting the name of the one line you meant to test" — relocated
from generation-time to storage-time.

Confidence: high (hashes measured).

### G4 · MEDIUM-HIGH — embedding spend is unledgered by construction (mechanism confirmed), and no command reconciles total spend against any cap

* `recurse_driver.py:1698-1727` (`_embed_texts`): embeddings go out via a raw `curl`
  subprocess to `api.together.xyz/v1/embeddings` with **no ledger write anywhere on the
  path**. Pre-ds7 review finding 6 stands and is admitted in EXPERIMENTS.md
  ("~$0.001/run") — small in dollars, but it is the only spend path with *no* record, and
  ds7's `greedy_rename_descend` puts an embedding call into every build. RUN-not-possible
  (would spend); mechanism verified by reading.
* "Is there ONE command that reconciles total spend vs the $8.50 budget?" — the candidate
  is `spend.py [--check N]`. Verified inadequate on three axes: it skips unpriced rows
  (G1); `--check` prints nothing about them and exits 0; and `audit()` globs only
  `semi-formal-experiment/` artifacts, so walkthrough run artifacts are outside its
  reconciliation entirely. The graph_v2 campaign tracks spend by its own conventions
  (per-dispatch budgets, per-run ceilings, a manually-armed "tripwire" in EXPERIMENTS.md
  prose) — none of which reads `spend.BUDGET`.

Confidence: high on the mechanism (read); the no-reconciliation claim verified by running
`spend.py` / `spend.py --check 8.50`.

### G5 · MEDIUM — one watched file among many can be DELETED through the guard with a warning, not a block

`guard.resolve()` raises (loud ERROR) only when a watch **entry** matches zero files. If
one of the four `prompt/*.md` files is deleted, the entry still matches the others; the
deleted file drops out of `current()`, its review point becomes an **orphan**, and
`check()` prints `⚠️ 1 recorded review point(s) for files no longer watched` and then
falls through to `✅ every watched file is at its recorded review point` — **exit 0**.
The hook would therefore pass a commit deleting a watched transcription (the staged
deletion path matches `--watches`, the gate runs, the guard is "green").

The single-file entry case is loud (rename/delete the only file of an entry → ERROR —
verified by `test_a_pattern_matching_no_file_is_an_error` and the self-test, both run).
The N-of-M case is a ⚠️ line above a green exit. Deletion of a transcription is arguably
the strongest possible claim that it no longer matches the design, and it is the one
movement the guard reports as a warning. (Partly a design call — but the guard's own
standard is that "pass == did not run" shapes are errors; a watched file that silently
stops being watched is that shape at one-file granularity.)

Confidence: high on the code path (INFERRED — sandbox blocked the accept step needed to
set up the run; the orphan branch `guard.py:163-167` + `check()`'s fall-through are
unambiguous).

### G6 · MEDIUM — REVIEW_QUEUE §1's "There is deliberately no accept-all" is contradicted by the code: `guard.py --accept --all` exists and is documented

`guard.py` docstring line 4: `python3 guard.py --accept --all  # record every watched
file (say why)`; `accept()`: `if paths == ["--all"]: paths = sorted(now)`.
REVIEW_QUEUE.md:27 states the opposite as a design fact, and no test pins either state
(`test_accept_is_per_file` pins per-file semantics; nothing refuses `--all`). The
instrument's own API is misdescribed by the document that tells reviewers how to use it.
(For the record: `--accept` with no args IS refused, and ambiguous/non-watched paths are
refused — those parts of the claim hold. Not run against any real state: the sandbox
blocks `--accept` execution; the accept tests in `test_model.py` ran and passed in the
suite.)

Confidence: high (code reading; RUN of accept blocked by sandbox policy).

### G7 · MEDIUM — the walkthrough suite is RED at HEAD: `test_link.py::test_d4b_no_table_and_no_concepts_declared_is_silent` fails on committed state

`pytest walkthrough/` → **1 failed, 1003 passed, 1 xfailed**. Reproduced standalone. The
test renders the m0255-style fixture ("declares no concepts at all") and asserts no
`concept-table-absent` finding — but since the 2026-08-12 every-borrow-needs-a-gloss
ruling (committed in `3d856a8`, the last commit to touch either file) the renderer emits
a `%% concepts:` header derived from `inputs`, so the note fires:

```
concept-table-absent | note | plain.lp | 1 module(s) in this link declare concepts in a
`%% concepts:` header and no concept table (`concepts.json`) was supplied …
```

The fixture no longer means what the test's docstring claims it means; the test's own
warning — "A warning that fires on every run is how the old `no %% provides:` message
became invisible" — is materialising. Filed here (not as an application bug — link.py's
logic is agent A's) because a red test at HEAD is an instrument-state fact, and the §6
section is titled "WHAT IS BUILT AND GREEN".

Confidence: high (ran it twice).

### G8 · MEDIUM — phase_1/README.md carries three undated, stale live values, one of them a 300× understatement of invisible spend

Measured vs claimed (all RUN-verified measurements):

| claim (phase_1/README.md) | measured now |
|---|---|
| "Currently 27,754 chars from 4 files" (Design notes) | **37,891 chars** (self-test's assembly check, run today) |
| `$V translate.py --self-test  # 53 checks` | **52 checks** (51 passed + 1 failed) |
| "Repo ledger: $2.06 of $8.50; this directory has spent a further **$0.021 across 17 calls** that the ledger does not see" | priced ledger $2.072; invisible-to-`spend.py` rows: **1,625 calls, $6.84 embedded cost** (G1) |

None carries a date. The first two are cosmetic drift (the F3 class); the third is
material — the number a reader uses to gauge how much unledgered money is in play is
stale by ~325×. (The README's disclosed staleness note about `translate.py`'s docstring
is accurate — verified still present at `translate.py:7,10-14` — and translate.py is
indeed unwatched, as the README warns.)

Confidence: high.

### G9 · MEDIUM — two contradictory budget ceilings are in force, and neither is what the machine reads

* AGENTS.md (repo-wide, undated): "hard budget ceiling recorded in `spend.py` (currently
  $8.50, ~$2.15 used)".
* EXPERIMENTS.md 2026-08-13 handoff: "Budget: **$10.00 authorization**, ~$7.40 used at
  snapshot" (Matt's extension, 2026-08-12, per EXPERIMENTS.md:1291).
* `spend.py:BUDGET = 8.50`, with a comment that raising it "is a decision, never a
  workaround" — the $10 decision never propagated into the machine that enforces it; and
  `spend.py`'s own docstring still says "$7.50 total".

A new agent obeying AGENTS.md sees "$2.15 of $8.50"; the campaign record says "$7.40 of
$10.00"; the conservative ledger says "$8.91" (G1). All three are "the budget". Same
class as G8 but at the level of the cap itself.

Confidence: high (all three texts and BUDGET read; spend measured).

### G10 · LOW-MEDIUM — the hook's `--watches` matcher uses fnmatch while the guard uses glob; unquoted `$staged` word-splits

`guard.watches()` matches staged paths with `fnmatch.fnmatch(rel, pattern)`, where `*`
crosses `/`; `resolve()` uses `glob.glob`, where it does not. A staged
`prompt/sub/x.md` would make the hook *fire* (over-blocking — the safe direction; it
cannot make the hook skip a genuinely watched file), and the divergence is another copy of
"what is watched" in behaviour if not in data. Separately, `--watches $staged` is
unquoted: a staged path with spaces word-splits into bogus arguments (again failing
toward over-blocking here, since any match fires the gate; a path that splits into
zero matches would skip — not reachable for the current watch set).

Confidence: high (code reading; INFERRED).

### G11 · LOW — the guard's self-test is not run by the hook; it merely exists at commit time

Answering the posed question directly: `pre-commit` runs (a) pytest
`test_prompt_examples.py` and (b) `guard.py` check. It does **not** run
`guard.py --self-test`; that runs only when someone runs pytest (`test_model.py::
test_pre_commit_self_test_passes`). Not a defect in isolation — the hook's two steps are
substantive checks — but the self-test that proves the guard's loud-ERROR cases is one
layer removed from the gate it protects.

Confidence: high (hook read; hook run).

### G12 · LOW — accept is attestation-only, by design, and `--accept --all` makes the scripted path one command

`accept()` records `{digest, at, by=$USER}` and verifies nothing about whether anyone
read anything — the docstring says exactly this ("Accepting a file you did not read is
the failure this guard exists to prevent, performed by hand"). Nothing mechanical can
close that; noted only because the review brief asked whether a stale file can be
accepted without re-reading: mechanically, yes, and the barrier is prose. Combined with
G6, the whole-list variant is one undocumented-in-the-queue command away.

Confidence: high (code reading).

---

## Minor notes

| # | note |
|---|---|
| N1 | `spend.py` docstring still says "$7.50 total" two years of edits below `BUDGET = 8.50` (same file contradicts itself) |
| N2 | REVIEW_QUEUE §6 "spend ~$0.19 of $8.50 (Measured 2026-08-07)" contradicts the same-day $2.057 in ENGINEERING_REVIEW_2026-08-07b F12 and STEP_stage3.md — presumably phase_1-only, but unlabeled in a list of repo-wide numbers |
| N3 | STATE.md "guard.py + watch.json + hooks/, 23 tests" — still exactly right (`test_model.py` = 23 tests); a dated claim that survives contact |
| N4 | `link.py --self-test` is now 21/21 (the §6 claim "19/19" is dated 08-07 and moved legitimately) |
| N5 | mutate_schema guard count: §6 says 46, the 08-07 review measured 44 the same day; could not re-run this session (sandbox) — unresolved, not a verified mismatch |
| N6 | `test_prompt_examples.py`'s xfail marker cites `OPEN_QUESTIONS.md` Q-4 — resolves to `walkthrough/OPEN_QUESTIONS.md`; Q-4's text was corrected to "51 passed / 1 failed". Chain intact |
| N7 | `guard_hook.py` (PostToolUse) is advisory-only by design, installed in `.claude/settings.json`, launched via environment-dependent bare `python3` — if it dies, nothing notices, but the blocking gate is the pre-commit hook, so this is disclosure-level |
| N8 | `reviewed.json` entries are committed data: an edit + accept + commit of both files in one shot passes the hook by construction. Inherent to an attestation ledger; the hook even says so ("Bypass … records nothing, and nobody will know") |
| N9 | eval.py noise measurement is deliberately not seeded — it measures live run-to-run spread at T=0.2; a single repeat reports `sd: None` and prints "UNMEASURED, not zero" (`test_a_single_repeat_reports_UNKNOWN_spread_not_zero` passes). Loud, correct |
| N10 | second-attempt leakage into eval scoring: closed as claimed — `_one_clause` makes exactly one `client.complete` per clause; `StubClient.complete_messages` raises on any repair turn and `test_the_harness_never_repairs` pins calls == clauses × repeats (ran, passed) |

---

## Status-attestation audit (claim → location → measured now → verdict)

| claim | file:line | measured now | verdict |
|---|---|---|---|
| "500 passed + 1 xfail" | REVIEW_QUEUE.md:175 (§6) | 1 failed, **1003 passed**, 1 xfailed | OK-as-of-date (2026-08-07) — but note the suite is RED at HEAD (G7) |
| "translate.py --self-test 51 passed / 1 FAILED" | REVIEW_QUEUE.md:175 | 51 passed / 1 failed, exit 1 | ✅ exact |
| "link.py --self-test 19/19" | REVIEW_QUEUE.md:175 | 21/21, exit 0 | OK-as-of-date; count moved legitimately |
| "mutate_schema.py 46 guards, 0 survivors" | REVIEW_QUEUE.md:176 | NOT RUN (sandbox blocked); last independent run said 44 (08-07) | UNVERIFIED |
| "spend ~$0.19 of $8.50" | REVIEW_QUEUE.md:176 | priced $2.072 + $6.84 unpriced; same-day docs say $2.057 | ⚠️ contradicts same-day figures; unlabeled scope (N2) |
| "Six watched files. One accepted, five never reviewed" / guard RED | REVIEW_QUEUE.md:16-25 | guard GREEN; 6/6 accepted (08-07 ×1, 08-12 ×5) | STALE — dated doc, but the review brief itself carried this state; actual state recorded above |
| "Accepting is per file … There is deliberately no accept-all" | REVIEW_QUEUE.md:27 | `--accept --all` exists and is documented in guard.py | ⛔ FALSE (G6) |
| "eval.py … measures its own noise first and scores the FIRST attempt only" | REVIEW_QUEUE.md:191-192 | both properties test-verified (72-suite run) | ✅ |
| "make_arm.py — an arm generated as a verified one-line diff of the live prompt, never a copy" | REVIEW_QUEUE.md:192-193 | generator verified; **arms on disk are drifted copies, attestation write-only** (G3) | ⛔ FALSE as a statement about current arms |
| "Since: … eval.py … make_arm.py … stage 3 plan revision 3" | REVIEW_QUEUE.md:190-193 | present and tested | ✅ |
| "Currently 27,754 chars from 4 files" | phase_1/README.md (Design notes) | 37,891 chars | ⛔ STALE, undated (G8) |
| "$V translate.py --self-test # 53 checks" | phase_1/README.md (top) | 52 checks (51+1) | ⛔ STALE, undated (G8) |
| "Repo ledger $2.06 of $8.50; … further $0.021 across 17 calls" | phase_1/README.md (Design notes) | $2.072 priced; 1,625 invisible calls / $6.84 | ⛔ STALE, undated, material (G8) |
| "hard budget … currently $8.50, ~$2.15 used" | AGENTS.md:85-86 | priced $2.072; conservative true ≈ $8.91; campaign says $10.00 cap | ⛔ STALE and understated ~4× (G1/G9) |
| "spend.py: $2.06 of $8.50" | STATE.md:225 (Cost) | priced $2.072 | OK-as-of-date (2026-08-07 header) |
| "guard … 23 tests" | STATE.md:104 | 23 | ✅ |
| "Budget: $10.00 authorization, ~$7.40 used at snapshot" | EXPERIMENTS.md:1704 (2026-08-13) | embedded-cost total now ≈ $8.91 (post-ds7 growth consistent) | OK-as-of-date; contradicts AGENTS.md cap (G9) |
| "embedding spend remains UNLEDGERED by construction (~$0.001/run)" | EXPERIMENTS.md:1620 | mechanism confirmed (curl path, no ledger write) | ✅ honest disclosure |
| "122 tests green" (graph_v2, pre-ds7) | EXPERIMENTS.md:1632 | not re-run (out of scope + sandbox) | UNVERIFIED |
| translate.py module docstring "Stage 1 has never been run" etc. | translate.py:7,10-14 | still present; disclosed as stale by README; translate.py unwatched | DISCLOSED (README note verified) |

**Headline: of 19 audited claims, 6 are stale/false without date-protection (G6, G8 ×3,
G9, and the §6 arm claim), 2 are unverified (sandbox), 1 is stale-but-dated (guard
state), the rest hold.**

---

## Improvement opportunities

1. **`make attest` — one command that re-derives every status number from live runs.**
   Test counts, both self-tests, guard state + hook-installation check (present,
   executable, resolves, fires), priced + embedded-cost spend totals against BOTH budget
   regimes, and arm provenance re-verification. Emits JSON + human lines; docs cite it or
   link it instead of hardcoding moving numbers. This converts the entire G8/G9/N2 class
   from recurring rot into one script, and it is the direct answer to F3's lesson.
2. **Fail-closed scoping gate + pinned interpreter in the hook.** Capture the rc of the
   `--watches` call: `1` = nothing watched (skip), anything else = "the guard could not
   run" → BLOCK with a named reason. Run `guard.py` with the repo venv's python (same
   missing-blocks style as the pytest step), not bare `python3`. One line of sh each.
3. **Close the ledger gap at the source.** Add the `providers.json` row that
   `spend_invisibility_warning()` already prints verbatim — or teach `cost_of()` to honour
   a row's embedded `cost_usd` (it is computed with the project's own conservative
   arithmetic and carries its `priced_by`). Additionally make `spend.py --check` fail
   when unpriced rows exist unless explicitly waived. G1 is a one-row-or-one-function
   fix; the warning machinery did its job for weeks and nothing consumed it.
4. **Enforce arm attestation at load time.** `eval.py:load_arm` (or a `make_arm
   --verify`) should re-hash each arm's recorded parent and REFUSE a stale arm without a
   dated waiver; generate `prompt_head`-style arms through `make_arm.py` so every arm
   carries a sidecar. The sidecar note "Regenerate after any edit" is advice; make it a
   gate.
5. **Make deletion of a watched file blocking** (or require the watch entry's removal in
   the same commit): orphans are currently ⚠️ under a green exit (G5).
6. **Ledger the embedding path** — one row per `_embed_texts` batch, even at price 0, so
   no spend path exists with zero record (G4).
7. **One budget SSOT.** A version-controlled `budget.json` (cap + authorization history)
   that `spend.py`, AGENTS.md and the campaign docs all quote; a cap change updates one
   file and the machine reads it (G9).
8. **`guard.py --doctor`**: hook installed? executable? interpreter resolvable? watch
   list loads? self-test green? — the 2026-08-07 lesson ("being right was never the hard
   part") as a command, not a process note.

---

## What I did not check

* `mutate_schema.py` re-run — blocked by the session sandbox on two attempts; guard
  count 46 vs 44 left unresolved (N5).
* Scratch execution of the accept workflow (`--accept` in any form was blocked even
  against the scratch copy) — covered instead by `test_model.py`'s accept tests, which
  ran and passed inside the suite; G5/G6 are code-verified accordingly.
* Whitespace-only-change repro end-to-end (needs a prior accept state); inferred from
  `digest()` being a sha256 over raw bytes — whitespace changes the hash by construction.
* The guard-crash variant of the hook's scoping gate (sandbox declined corrupting even
  the scratch `guard.py`); inferred from the ran missing-interpreter case — same line,
  same `|| exit 0`.
* graph_v2 campaign logic and its non-spend claims in EXPERIMENTS.md (agent C's scope),
  including the "122 tests green" figure; seats/readback/mutate application behaviour
  (agent B); link.py's logic beyond its red-test status (agent A).
* ds7 per-run artifacts (run.json/health.jsonl) integrity — agent C.
* Whether the 2026-08-12 accepts corresponded to actual re-reads — human acts, outside
  mechanical reach by the guard's own self-description.
* `semi-formal-experiment/`'s own test suite and `ladder.preflight` behaviour — that
  area is read-only and self-governing; I only audited what walkthrough claims about it.

---

## Verdict

**NOT CLEAN.** Three HIGH findings, all of the one shape this directory exists to
prevent: an instrument reporting "all good" while broken. The pre-commit hook passes
commits silently when its interpreter is missing (ran it). The budget gauge reads 24%
while the project's own conservative arithmetic says the cap has passed, and the machine
gate exits 0 (ran it). The eval arms carry a "verified one-line diff" attestation that
nobody verifies, and the hashes prove drift (measured it). The staleness guard's CORE is
the strongest instrument in the set — its loud-ERROR discipline, per-file accepts and
exact-sha policy all survive scrutiny — and the eval harness's first-attempt and
noise-first properties are genuinely pinned by tests. The rot is at the edges: wiring
(hook ↔ environment), money (ledger ↔ prices), and time (attestations that were true
when written and are checked never again).
