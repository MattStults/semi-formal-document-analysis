# TRANSLATION_RUNBOOK.md — running stages 1–4 with no prior context

**Audience:** a capable model-agent with **no conversation history**, told to run the
translation pipeline over graph nodes or spec clauses. You need nothing outside this file
except the files it cites by path.

**Written 2026-08-14 by an adversarial sufficiency audit.** Every command below was
executed (free/offline paths only). Where a documented command is *wrong*, this file says
so and gives the working one. Companion: `RUNBOOK_AUDIT.md` (why each item is here).

> ⛔ **Read §0 STOP CONDITIONS before running anything.** Two of them fire on the
> *documented* happy path.

---

## §0 STOP CONDITIONS — never decide these yourself

Halt and ask a human. Do not work around, do not "temporarily" relax.

| # | Condition | Why |
|---|---|---|
| S1 | **Any spend at all.** `--live` sends immediately, with no confirmation prompt. | The only automatic rail is the cost gate; there is no human-in-the-loop step in the code. Repo budget is `semi-formal-experiment/spend.py` `BUDGET = 8.50`, and *this harness's spend is invisible to it* (see §6). |
| S2 | **`CostGateError`** — estimate over `cost.max_cost_usd`. | Raising a ceiling is a spend decision. Never edit `max_cost_usd`. Reduce the selection instead (`--limit`, `--clause`), or stop. |
| S3 | **`GraveyardError: graveyard cap reached`**. | Requires per-entry human diagnosis. See §5. Never bulk-clear. |
| S4 | **Stage-4 seats (`seats.judge`) need a live client.** No blessed factory exists in the repo. | You would have to author the provider seam yourself — that is a design decision about what the seats see. STOP. See §4c. |
| S5 | A quality floor, threshold, or acceptance band would have to be **lowered** for the run to pass. | `CLAUDE.md`: "Never lower a quality floor to make a run pass." Scoring far *above* a floor is a leak signature, not a win. |
| S6 | You are about to **write into, edit, or delete anything under a `runs/` directory** (`runs/`, `translation_sample/runs/`) or a `repair_graveyard/` entry. | Raw responses of a paid run are the one thing that cannot be regenerated. Read-only, always. |
| S7 | A prompt file under `prompt/` or `node_worked_example.md` would have to change. | These are watched transcriptions (`DEBUGGING_TIPS.md` §10). A prompt change is a cycle, not a fix. |
| S8 | `git commit`, `git push`, or `--no-verify`. | Repo rule (`CLAUDE.md`): **the driver never runs git.** A human stages and commits. ⚠️ Note `walkthrough/DEFERRED.md:229` *sanctions* `--no-verify` in a narrow case; that permission is for a human, not for you. |
| S10 | `walkthrough/model/guard.py --accept` on any file, and **especially `--accept --all`**. | The staleness guard is **currently RED by design** for all five phase_1 watched files. `DEFERRED.md:236-238`: "The one thing that must not happen is `guard.py --accept --all` to clear the noise." A red guard is a known state, not your problem to clear. |
| S9 | Any run whose result you intend to *report as evidence* about the current prompt, when `version.py` says the modules are `contract-stale`. | A waiver can never excuse a contract-hash change. |

**Never** edit `config.json`, `config_graph_nodes.json` cost/repair/graveyard blocks, or
`schema.py`, to make a run proceed. The only config regeneration this runbook authorises is
§2 step 1 (`node_corpus.py`), which is deterministic and idempotent.

---

## §1 What is actually runnable, and what is not

The task is often stated as "stages 1–4: translate → mechanical validation → readback →
seats". **The repo does not number them that way**, and this mismatch will mislead you:

| This runbook | Repo's name | Code | Runnable hands-off? |
|---|---|---|---|
| Stage 1 translate | stage 1 | `translate.py` | ✅ yes, one command |
| Stage 2 mechanical validation | stage 2 | `checks.py` + `schema.py` + `../../link.py` | ✅ **automatic** — not a separate step; it is the unconditional gate inside every stage-1 attempt |
| Stage 3 corpus link / probe | repo calls **stage 3 = probe cases** (`probe.py`); `link_nodes.py` calls itself "Step 3" | `link_nodes.py`, `probe.py` | ✅ free, offline |
| Stage 4 readback R1/R2/R3 | stage 4 | `readback.py`, `readback_r3.py` | ⚠️ free, but **library only — no CLI**; needs ~20 lines of driver you write |
| Stage 4 seats 4a–4d | stage 4 | `seats.py` | ⛔ **NOT runnable** — see S4 |

`STEP_stage3.md` records a numbering contradiction in the source of truth
(`walkthrough/resources/03_pipeline.md`): its flowchart numbers probe cases **3** and
read-back **4**; its prose says the probe cases are at stage **4**. Use the table above.

**`readback.py` has no `main()` and no `__main__`.** `seats.py`'s only CLI is
`seats.py --cost` (a free survey). `probe.py`'s CLI takes `.lp` paths, not a run directory.
There is **no end-to-end driver for stages 3–4.** Plan for that.

---

## §2 Prerequisites and environment

```bash
REPO=/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis
V=$REPO/semi-formal-experiment/.venv/bin/python     # ALWAYS this interpreter
```

* **Never `source` the venv**; call the binary by path (user global instruction).
* `clingo` and `xclingo` must be importable from that venv — stage 2, `link.py`, `probe.py`
  and `readback_r3.py` all shell out to / import them. If missing, stage 2 cannot run and
  **you must stop, not proceed** (`DEBUGGING_TIPS.md` §8: a check that cannot run must not
  exit like a check that passed).
* **Working directory matters.** `translate.py` resolves config-relative paths against
  `phase_1/`. Run stage 1/2 from `phase_1/`. Run `node_corpus.py` and `link_nodes.py` from
  `resolve_runs/graph_v2/` — **every graph_v2 script assumes graph_v2 as cwd.**
* **API key:** env var `TOGETHER_API_KEY`. If unset, `translate.py:500-523` falls back to
  parsing an `export ...=` line out of `~/.zshrc`, `~/.bashrc`, `~/.bash_profile` — "keys
  live in `~/.zshrc` by project convention". This fallback is documented **nowhere in any
  .md**; it is why a run can succeed with no visible key in the environment.
* Provider calls use **stdlib `urllib`** — no vendor SDK. ⚠️ For the **batch** endpoints
  only, together.ai's WAF 403s stdlib urllib while accepting `curl`; `dispatch_core.py`
  (`CurlTransport`, ~:863) shells to curl for that reason. Chat completions are fine on
  urllib. If you see an unexplained 403 on `/v1/batches` or `files/upload`, this is why.

---

## §3 Stage 1 + 2 — the run

### 3.0 Preflight (all free, no network except where noted)

```bash
cd $REPO/walkthrough/paper_pipeline/phase_1

$V translate.py --self-test        # ~52 checks, offline
$V version.py                      # staleness census over runs/, free
$V -m pytest -q                    # ~1054 tests, ~2.5 min
```

**Expected preflight state as of 2026-08-14 — do not treat these as your failures:**

* `--self-test` → **`51 passed, 1 failed`, exit code 1.** The failure is
  `dryrun.txt matches the current config and prompts` — the checked-in artifact is stale.
  Fix is `$V translate.py --write-artifact` (free, regenerates `dryrun.txt`).
  ⚠️ Do **not** gate your run on `--self-test` exit code without first checking that the
  only failure is this one. Any *other* failure is a real stop.
  (`README.md` says "53 checks"; it is 52. `README.md` says the system prompt is
  "27,754 chars from 4 files"; it is 37,891. Both stale.)
* `pytest` → **`1 failed, 1053 passed, 1 xfailed`.** The failure is
  `resolve_runs/graph_v2/test_promise_repair.py::test_infeasible_plan_is_reported_and_never_paid`
  (`TypeError: bad_locate() got an unexpected keyword argument 'seed'` — a stale test
  double, not a pipeline defect). Pre-existing. Any *additional* failure is a real stop.

⛔ **`translate.py`'s module docstring and its end-of-run banner are STALE and say the
opposite of what the harness does** — they claim nothing is validated. Stage 2 has been the
unconditional gate for a long time. Believe `README.md` and the code, not those strings.

### 3.1 Choose the corpus, and therefore the config

| You are translating | Config | Corpus |
|---|---|---|
| **spec clauses** | `config.json` (the default; pass nothing) | `semi-formal-experiment/modelspec_clauses.json`, 593 clauses |
| **graph nodes** | `--config resolve_runs/graph_v2/config_graph_nodes.json` | `resolve_runs/graph_v2/node_corpus.json`, 15 stratified nodes (seed 42) |

They differ in more than paths — **know these before you interpret a result:**

| knob | clause config | node config |
|---|---|---|
| `cost.max_cost_usd` | **0.25** | **2.00** |
| `repair.max_attempts` | **3** | **5** |
| `model.resample_truncation` | *unset* (= raise on truncation) | **2** |
| graveyard dir | `repair_graveyard/` | `translation_sample/repair_graveyard/` |
| output dir | `runs/` | `translation_sample/runs/` |
| worked example | `prompt/20_worked_example.md` | `node_worked_example.md` |

### 3.2 ⛔ NODE PATH: the documented command fails out of the box — fix it first

`resolve_runs/graph_v2/README.md`'s "Translation sample" command currently dies:

```
⛔ ConfigError: prompt file(s) on disk but never sent: delta_investigation.md,
   k3_validity_report.md, opus_recheck_report.md.
```

This is the **orphan-prompt guard** doing its job: `config_graph_nodes.json`'s
`prompt.unused_files` must enumerate *every* `.md` sitting in a directory that contributes a
system-prompt file, and three new `.md` files were added to `graph_v2/` after the config was
generated. **Any new `.md` written into `resolve_runs/graph_v2/` breaks the node run.**

**The fix — deterministic, verified, authorised:**

```bash
cd $REPO/walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2
$V node_corpus.py                  # rewrites node_corpus.json + config_graph_nodes.json
```

Verified: `node_corpus.json` comes back **byte-identical** (seed 42 is deterministic) and
`config_graph_nodes.json` gains exactly the three missing `unused_files` entries. Nothing
else changes. This is safe and idempotent.

⚠️ **Do not run `node_corpus.py --ids ...` or `--all`** unless you intend to change the
sample: it clobbers `node_corpus.json` and breaks the pinned 15-node set that every prior
run's numbers are comparable against.

⚠️ `node_corpus.py`'s own docstring tells you to run
`$VENV ../../translate.py --config resolve_runs/graph_v2/config_graph_nodes.json --dry-run`.
**That is wrong twice**: there is no `--dry-run` flag (argparse rejects it), and the config
path is relative to `phase_1/`, not to `graph_v2/`. Use §3.3.

### 3.3 Dry run — mandatory, free, sends nothing

**A bare `translate.py` invocation IS the dry run.** There is no `--dry-run` flag.

```bash
cd $REPO/walkthrough/paper_pipeline/phase_1

# clauses
$V translate.py
# graph nodes
$V translate.py --config resolve_runs/graph_v2/config_graph_nodes.json

# see the exact bytes that would be sent, for one clause
$V translate.py --config resolve_runs/graph_v2/config_graph_nodes.json --show-prompt 1
```

Read the cost line before anything else. Current measured values:

| selection | worst-case cost | ceiling | margin |
|---|---|---|---|
| clause default (3 clauses) | $0.1745 | $0.25 | comfortable |
| **node default (15 nodes)** | **$1.9940** | **$2.00** | **$0.006** |

⛔ **THE RESTART POLICY DOUBLES BOTH NUMBERS ABOVE.** Stage 2's repair loop may discard a
frozen transcript and redraw the clause once from attempt 1, so a clause's worst case is
TWO chains of `max_attempts`, and `run()` prices it by doubling the single-chain estimate.
The worst-case CALL COUNT is likewise 2 × `max_attempts`, not `max_attempts`. Every figure
in this table already carries that doubling; the pre-policy figures were $0.0872 and
$0.9970. Expect it in the printed cost line — it is not an error.

**What to expect to actually spend:** ~0.9×–1.2× of the old policy, not 2×. The restart
truncates the frozen chain early, so the calls saved nearly pay for the redraw (measured
0.89×–1.28× whole-run; 0.79×–1.60× if you look only at chains that fired). **Do not use
that to shave the ceiling.** The gate is priced on the worst case by signed ruling, and the
125-node cap on `config_corpus_all` slices depends on it: expected spend ≈ 1.0×, required
gate headroom = 2×.

⛔ **The node run sits $0.006 under its own gate, and that is deliberate** — the raise to
$2.00 was ruled MINIMAL, not "with headroom", because a ceiling with slack has stopped
being a constraint. 16 nodes already prices $2.1267 and is refused. Any increase — one more
node, a higher `max_attempts`, a longer prompt file — trips `CostGateError` (→ S2). This is not a bug to
route around; it is the gate binding. If it fires, cut the selection with `--limit`.

Other free checks worth running:

```bash
$V translate.py --list-models     # GET /models — network, no spend; verifies the model id
$V translate.py --only-stale      # prints the staleness census ABOVE the cost line
```

`--only-stale` is **off by default on purpose**: changing what a bare run translates is a
spend change.

### 3.4 Live run — only after S1 is satisfied by a human

```bash
$V translate.py --config resolve_runs/graph_v2/config_graph_nodes.json --live
```

There is **no confirmation prompt**. `--live` spends on invocation.

Concurrent/batch execution exists (`resolve_runs/graph_v2/translate_exec.py`, requires an
explicit `execution` block in the config) but has accepted divergences from serial —
including **batch kill-recovery is unsupported: a killed batch run's submitted, paid job is
abandoned.** For a hands-off first run, use serial `translate.py`.

### 3.5 What stage 2 does automatically

Every attempt is schema-validated, compiled under clingo, link-checked, rule-shape checked
and cycle checked **before anything is written**. `error`-severity findings drive the repair
loop; `note` findings are counted and inert.

⚠️ **`requires-unprovided` fires on every well-formed single-clause module** — it is a
`note` and it is *correct*. A loop that chased notes would converge on teaching the model to
move predicates out of `requires` until nothing fires. Do not "fix" it. Ruling is in
`checks.py`'s module docstring; see also `DEBUGGING_TIPS.md` §7.

---

## §4 Stages 3 and 4

### 4a Corpus link (free, has a CLI, works today)

```bash
cd $REPO/walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2
$V link_nodes.py
```

Verified output 2026-08-14:

```
linked 28 node modules as one corpus (143 concept rows)
  concept-declared     16 [note]   concept-multi-gloss   9 [note]
  requires-unprovided  27 [note]   situation-input      13 [note]
requires: 2/37 resolved in-corpus (35 dangling); 6/22 modules fully resolved
report -> link_nodes_report.json
```

**Zero errors, all notes** = healthy. `requires` dangling at this rate is expected: most
providers are simply untranslated. It writes only `link_nodes_report.json`.

Useful library entry points it exposes: `merged_gloss()`, `provider_texts()`,
`requires_resolution()` — these are what stage 4 needs (§4b).

### 4b Readback R1/R2/R3 (free, offline, **no CLI — you must write the driver**)

Entry points, per `resolve_runs/graph_v2/STEPS34_READINESS.md` and
`READBACK_SMOKE.md` (read both — they are the only real documentation of this path):

```
readback.render_module(mod, extra_gloss=…, clause_quote=…)     # R1 + R2
readback_r3.render_r3(mod, situations, extra_gloss=…, link_texts=…)   # R3
```

* `mod` = `schema.validate(json.load(open(<run>/<id>.json)))`. Stored node modules validate
  unchanged.
* `situations` = `probe.probe_clause(...).covering` — a stage-3 artifact that
  **materialises on demand, free**. `READBACK_SMOKE.md` confirms this dissolved the feared
  "no stage-3 artifact exists for nodes" blocker.
* `extra_gloss` **must** come from the merged corpus table
  (`link_nodes.merged_gloss()` / `readback.gloss_from_rows`), or every cross-node predicate
  is a `readback-ungloss` **error**.
* `clause_quote` **must not** be the corpus row's `quote` — for nodes that is the *packed
  prompt* (scaffold + names + span). Use `readback.clause_text(row)`, which returns the
  narrowed span. This is now pinned by `test_stage4_node_plumbing.py`.
* `sys.path` order: put `semi-formal-experiment/` **last**. It contains its own
  `translate.py` which shadows phase_1's.

⚠️ **`READBACK_SMOKE.md`'s "Integration gaps" list is now partly STALE.** Its gaps 1, 3, 4
and 5 (seat item-id disclosure, node clause text, cross-node gloss, link-scope hygiene) have
since been **fixed in code** and are pinned by `test_stage4_node_plumbing.py` (21 tests, all
passing). Its **gap 2 is still open** — see §4c. Read the smoke doc for the shape of the
problems, not for their status.

A `readback-ungloss` error is usually a **real translation defect**, not an integration
failure: the module declared `inputs` that no concept row defines. Stage 2 accepts that; R3
is the first stage that refuses. Record it as a finding.

### 4c ⛔ Seats 4a–4d — STOP (S4)

`seats.judge` **raises without an explicit `client_factory`** — deliberately: "a default
that quietly reaches the network is the one mistake a revert cannot undo."

**No config-driven seat client factory exists anywhere in the repo.** Grep confirms every
`client_factory` in the tree is a test stub or `translate.run`'s own. Running the seats live
requires you to author the seam yourself: `json_schema → json_object` forcing (the config's
json_schema is the stage-1 *module* schema and would mangle a seat reply),
`max_tokens → seats.SEAT_MAX_TOKENS`, and an envelope→text adapter. That is a design
decision about what the seats are shown. **Escalate; do not improvise it.**

Free and safe: `$V seats.py --cost` surveys what a live stage-4 run would cost off the
modules already on disk.

---

## §5 The repair graveyard

`graveyard.py`. Non-converging clauses (and a sample of converging ones) are written to the
graveyard dir. **Cap is 40 open entries** in both configs.

**Current state (verified 2026-08-14):** `repair_graveyard/` 2 open; node graveyard 5 open.
Neither is near the cap.

**When the cap fires** — `GraveyardError`, and `translate.py` exits **2** with the message:

```
graveyard cap reached: N open entries at <root>. Diagnose and clear them before
translating more — continuing spends the budget reproducing a defect that is
already recorded N times
```

It fires **after the cost gate and before any dispatch**, so no money is spent.

**The disposition procedure — and it IS discoverable from the code alone:**

* An entry is cleared by `graveyard.clear(root, name)`, which **refuses** unless the entry
  directory contains a `VERDICT.md`:
  > "`{name}` has no VERDICT.md. An entry is cleared by diagnosing it, not by deleting it —
  > the diagnosis is the artifact the graveyard exists to produce"
* Clearing **renames** `<entry>` → `_cleared_<entry>`. Nothing is deleted.
* ⛔ **There is deliberately no clear-all**, stated in the docstring: "A graveyard that gets
  bulk-emptied is worse than none."

**What a VERDICT.md must contain** — specified *only* in `PROPOSAL_graveyard.md:169-177`,
which nothing in the code, config, or README links to:

1. The cause.
2. Where the fix belongs: prompt, schema, design, or "the model cannot do this".
3. The held-out result.
4. ⭐ What would have caught this earlier.

Plus four tripwires (`PROPOSAL_graveyard.md:152-164`): is the diagnosis *fitting* the
instance? does the fix touch a **watched transcription**? does it disclose an answer key? is
the cause correctly attributed among model / prompt / schema / design? And the mandate at
`:141-151`: the **first** step of clearing is to read `DEBUGGING_TIPS.md`, and clearing
*maintains* it — "a cleared entry whose diagnosis was hard and left no tip is an incomplete
clearing." Worked examples of the practised format live under
`resolve_runs/graph_v2/translation_sample/repair_graveyard/*/VERDICT.md`.

⛔ **Writing a VERDICT.md is a human diagnosis, not a formality.** Do not author 40
verdicts to unblock a run — that is exactly the failure the cap exists to prevent. Cap
reached → **S3, stop and ask.** (Precedent: a 44-entry cap fired before a prior run; all 44
were diagnosed individually with per-entry VERDICT.md, explicitly "no bulk clear".)

### §5.1 The staleness guard (`walkthrough/model/guard.py`)

Separate rail, and it **watches phase_1 directly**: `resources/03_pipeline.md`,
`paper_pipeline/phase_1/prompt/*.md`, and `paper_pipeline/phase_1/schema.py`
(`walkthrough/model/watch.json`). It is wired as a **blocking git pre-commit hook** and as
an advisory Claude Code PostToolUse hook.

**It is currently RED / NEVER REVIEWED for all five phase_1 watched files, deliberately**
(`walkthrough/DEFERRED.md:220-224`). Expect it to fire. **Do not clear it** — see S10.
`guard.py --accept` refuses to run with no arguments precisely so that accepting stays
per-file and on the record.

---

## §6 Cost, spend, and the ledger

* Cost is estimated **worst-case**: every call billed at full `max_tokens`, and **triangular
  in attempt count** (each repair turn carries the transcript forward). Overstating is
  survivable; understating is how a hard cap gets passed.
* The gate refuses **before anything is sent**. An **unpriced provider counts as over
  budget**, never as free.
* ⚠️ **This harness's spend is invisible to `spend.py`.** The provider is defined *inline*
  in the config rather than in `providers.json`, and `spend.py` prices only from the latter.
  Every run prints the residue and `run.json` records
  `"visible_to_spend_py": false` with the reason. **When you report spend, report both**:
  the repo ledger figure *and* this directory's residue.
* Repo hard budget: `semi-formal-experiment/spend.py`, `BUDGET = 8.50`.
* Caching is **unpriced** here (together.ai lists a cached-input rate; the estimate bills
  full rate — the conservative direction).

---

## §7 Failure modes: what fires, and the correct response

| Symptom | What it is | Correct response |
|---|---|---|
| `CostGateError` | estimate over `cost.max_cost_usd` | **S2.** Cut the selection. Never raise the ceiling. |
| `GraveyardError` cap | 40 open entries | **S3.** |
| `ProviderError: no key for $TOGETHER_API_KEY` | key not in env and not an `export` line in `~/.zshrc`/`~/.bashrc`/`~/.bash_profile` | Ask the human. Do not hardcode a key. |
| `ProviderError` on `finish_reason=length` | truncation | ⚠️ **Cannot fire on the configured model** — together.ai returns `finish_reason: null` for DeepSeek-V4-Flash. A cut-off completion surfaces one step later as a **JSON parse failure reported as "the provider ignored `response_format`"**. If you see that message, suspect length, not format. |
| repeated truncation | provider-side **stochastic** pathology, not determinism | `model.resample_truncation` (node config: 2) redraws. ⚠️ **It is inert on repair rounds** (`complete_messages` bypasses `Client._retrying`) and inert in concurrent mode. Do **not** raise `max_tokens` to fix it — low caps are the fail-fast mechanism, and that fix was tried and reverted. |
| empty response | `ProviderError` | Transient; the executor ladders retry it (2 attempts). Serial raises. |
| `HTTP 402` | credit exhausted — **but together.ai 402s flap for minutes after a top-up** | Rides a **short** ladder (2 retries, ~90s), deliberately not treated as terminal. If it persists past that: **S1**, ask the human about credit. |
| `HTTP 429` | rate limit | Transient mark; bounded retries. Do not tighten concurrency on your own. |
| `curl: (6) Could not resolve host` / DNS | **network outage, not a hang** | A batch sitting server-side is safe. The correct behaviour is bounded-backoff waiting, never exit. Historically this killed an unattended run. |
| batch appears hung | measured SLA is ~62s, but the queue has been observed at **>45 min for a 19-request batch** | Provider-side latency. Verify with `CurlTransport.status(batch_id)` **before** diagnosing a hang. |
| `ResponseParseError` | not a JSON object, or fails the schema | A refusal, by design. See truncation row above for the common real cause. |
| `unrepaired` status | repair loop exhausted, findings standing | Normal, expected at some rate. `surviving_findings` is written beside it. Not an error to fix in-flight. |
| `abstained_under_repair` | model refused *after being told twice it was wrong* | ⭐ **Count this separately from `abstained`.** It is not a successful translation. A model can otherwise abstain its way out of the hard clauses while the rate reads ordinary. |
| clause won't converge | | Let it land in the graveyard. That is the designed sink. Do not hand-edit a module. |
| a module renames itself (`clause_id` slip) | **known open class, 3 instances observed** | The proposed fix (enum-force `clause_id`) is **designed, not shipped**. Detect it in `run.json`; report it. Do not assume it is prevented. |
| a `.md` added under `graph_v2/` | orphan-prompt guard `ConfigError` | §3.2 — regenerate with `node_corpus.py`. |
| graph node id in ASP | **graph ids are not valid ASP constants** — `L527-796_n012` parses `L` as a variable and `-` as subtraction; clingo refuses every module with an `assert` | Already fixed in the adapter (`asp_id()` → `l527_796_n012`; graph id lives in `locator`). Named here because if you ever build a corpus by hand, this silently zeroes your success rate. |

---

## §8 Acceptance criteria — what a good run looks like

**Node sample (15 nodes), the run-history baseline** (from `translation_sample/runs/*/run.json`,
counts verified 2026-08-14):

| run | translated | other | spend |
|---|---|---|---|
| 20260810-203553 | 2 | 13 unrepaired | $0.078 |
| 20260810-205513 | 3 | 11 unrep, 1 abst-under-repair | $0.072 |
| 20260810-212409 | 10 | 4 unrep, 1 abst-under-repair | $0.052 |
| 20260810-213043 | 5 | 8 unrep, 1 err, 1 abst | $0.059 |
| 20260810-214437 | 12 | 2 unrep, 1 err | $0.046 |
| 20260810-215527 | 8 | 6 unrep, 1 err | $0.086 |
| 20260810-225427 | 6 | 7 unrep, 2 abst-under-repair | $0.093 |
| 20260810-234100 | 8 | 5 unrep, 1 err, 1 abst | $0.082 |
| **20260812-090344** | **13** | 2 unrep | $0.052 |
| **20260812-133317** | **13** | 1 unrep, 1 abst | $0.045 |

**Read this: 8–13 of 15 is the operating band. 13/15 is the best observed.** A run at 5/15
is within historical variance, not necessarily a regression.

⭐ **The acceptance rule, and it is not the pass count:**

> "per-node success is partly stochastic; single-run rate comparisons on 15 nodes carry
> **~±3 noise**. The honest instrument is the **FINDING-CLASS distribution** (which classes
> exist), not the pass count; **class extinction across runs is signal, rate wobble is
> not.** If a class persists after its lesson, next lever is `max_attempts`, not more prose."

So: **report which finding classes appeared**, and whether any previously-extinct class came
back. Do not report "we improved from 10 to 12".

Additional signals:

* Cost per run in band **$0.045–$0.095**, 25–49 calls. Well outside → investigate.
* `link_nodes.py`: **0 error-severity findings.** Notes are expected.
* Two run directories in `translation_sample/runs/` have **no `run.json`** (`…-214234`,
  `…-133011`) — aborted runs. An aborted run leaves a directory behind; that is not
  corruption. `run.json` is rewritten after **every** clause, so an interrupt never loses
  the record of clauses already paid for.
* ⛔ Scoring far **above** the band is a leak signature, not a win.

**Clause path:** `version.py` today reports `11 contract-stale, 19 unstamped (of 30 stored
modules)`. Contract-stale means the artifact **may no longer validate** and a waiver may
never excuse it.

---

## §9 Where to record results

* **Never** hand-edit `run.json` or anything under a `runs/` dir (S6). The run writes its
  own record: config/prompt shas, response_format sent, per-clause status, attempts,
  findings, licence counts, spend.
* Narrative results and rulings go in a **new** markdown file, or as a dated entry appended
  to `resolve_runs/graph_v2/EXPERIMENTS.md`.
  ⚠️ **If you add a `.md` to `resolve_runs/graph_v2/`, you break the next node run** (§3.2).
  Either write it elsewhere, or regenerate `config_graph_nodes.json` in the same change.
* **Rulings go in the repo, not the transcript** (`CLAUDE.md`). A decision that resolves an
  open design question must be written down with its grounds, and the tempting alternative
  rejected **by name**.
* You draft; a human commits (S8).

---

## §10 Required reading, in order, if something is unclear

1. `walkthrough/paper_pipeline/phase_1/README.md` — the stage 1+2 contract. Authoritative
   except the three stale numbers flagged in §3.0.
2. `walkthrough/paper_pipeline/phase_1/DEBUGGING_TIPS.md` — 19 numbered traps. §7 (notes
   don't drive repair), §8 (a check that cannot run must not exit like one that passed),
   §9 (never pin an exact count of a live artifact), §10 (prompt files are watched).
3. `resolve_runs/graph_v2/STEPS34_READINESS.md` — the stage 3/4 gap map. Short, accurate.
4. `resolve_runs/graph_v2/READBACK_SMOKE.md` — the only end-to-end account of stages 3–4 on
   nodes. **Status of its gap list is stale** (§4b).
5. `resolve_runs/graph_v2/GOLDEN_PROTOCOL.md` and `AUDIT_KEY.md` — the two genuinely
   runbook-shaped docs in graph_v2, with pre-registered thresholds under real headings.
6. `semi-formal-experiment/REPRODUCIBILITY.md` — sandwich rule, new-constant governance.
7. `CLAUDE.md` / `AGENTS.md` (repo root) — the standing rules (never lower a quality floor;
   the driver never runs git; rulings go in the repo).
   ⚠️ **It never mentions `walkthrough/` or `paper_pipeline/` at all.** It says "most work
   happens in `semi-formal-experiment/`" and routes you through five documents about a
   *different subtree*. There is no `walkthrough/AGENTS.md`. Do not conclude from
   `AGENTS.md`'s silence that this directory is ungoverned — §0 of this file is its brief.
   In particular, **`MODULE_MAP.md` §11's anti-rules are entirely
   `semi-formal-experiment/`-scoped** (containment, dossier, patient, threshold, benchmark)
   and none of them govern `translate.py`, `schema.py`, or `graveyard.py`. Read §11 for the
   *reasoning pattern* — "a change a competent agent would make in good faith that breaks a
   contract" — not for rules that apply here. The phase_1 analogues of §11 are
   `DEBUGGING_TIPS.md` and the "known unpinned edges" section of `README.md`.

**The sandwich rule** (`REPRODUCIBILITY.md:9-41`) *does* apply, and this pipeline satisfies
it: deterministic producer (`translate.py` corpus + prompt assembly) → LLM under written
instructions (`prompt/*.md`, versioned in the repo, never in a transcript) → mechanical
validator (`checks.py`/`schema.py`/`link.py`, before anything is written). If you add a
step, it ships with all four artifacts or it is not done. **A new numeric constant is a
fitting surface** (`REPRODUCIBILITY.md:105-124`) — a bare literal in a scoring path is a
review finding. **Determinism is a cross-process property**: verify by rebuilding under a
different `PYTHONHASHSEED` in a second process, never by calling the builder twice in one.

⚠️ `resolve_runs/graph_v2/README.md` says of `EXPERIMENTS.md`: "**Read this first.**"
**That instruction is a trap.** `EXPERIMENTS.md` is a 2,183-line chronological lab notebook
with no table of contents, no "current state" section, and several late entries that
silently retract earlier ones. Reading it top-down and stopping early leaves you acting on
withdrawn conclusions. Everything from it that a run needs has been hoisted into this file.
Also note `BATCH_DESIGN.md` still reads "Status: DESIGN — not yet built"; batch **was**
built.
