# RUNBOOK_AUDIT.md — adversarial sufficiency audit of the translation pipeline

**Question:** can a capable frontier model with **no prior conversation context** run stages
1–4 of the translation pipeline over graph nodes and/or spec clauses, correctly and safely,
largely hands-off, using only what is written in this repository?

**Method:** walk the documented path from the entry points a newcomer would actually find,
following *only* what is written; execute every free/offline step; probe the safety rails
and the failure-mode coverage; record the first point at which a fresh agent must guess.
No live API calls, no spend, nothing under any `runs/` directory modified.

**Date:** 2026-08-14. **Deliverable pair:** `TRANSLATION_RUNBOOK.md` (the instruction set)
and this file (why each item in it exists).

---

## VERDICT

# SUFFICIENT-WITH-RUNBOOK — for stages 1–3 only. INSUFFICIENT for stage 4 seats.

Split verdict, because the pipeline splits:

| Scope | Verdict | Evidence |
|---|---|---|
| **Stage 1 + 2** (translate + mechanical validation), **clause** corpus | **SUFFICIENT-WITH-RUNBOOK** | Ran clean from documentation. `README.md` is unusually good. Gaps are stale numbers and one broken preflight gate. |
| **Stage 1 + 2**, **graph-node** corpus | **SUFFICIENT-WITH-RUNBOOK**, but the documented command is **currently broken** (G1) and the cost gate has $0.003 of headroom (G2). Without the runbook a fresh agent stalls at the first command. |
| **Stage 3** (corpus link / probe) | **SUFFICIENT-WITH-RUNBOOK**. `link_nodes.py` ran clean; `STEPS34_READINESS.md` is accurate. But nothing in the top-level docs tells you this stage exists. |
| **Stage 4 R1/R2/R3** (readback) | **SUFFICIENT-WITH-RUNBOOK, with code to write.** No CLI exists. The agent must author a driver from library entry points documented only in two graph_v2 files. |
| **Stage 4 seats 4a–4d** | **INSUFFICIENT.** `seats.judge` refuses without a `client_factory`; **no config-driven factory exists anywhere in the repo**. Running the seats requires the agent to invent the provider seam — a design decision. Not a documentation gap that a runbook can close. |

The pipeline is not unsafe. Every rail I probed **fires correctly and refuses before
spending**. The deficiency is navigational and stage-4-structural, not protective.

---

## Part 1 — Ranked gaps I had to fill by inference

Each of these is a real sufficiency defect: a fresh agent following only what is written
would stall, guess, or act wrongly.

### G1 — ⛔ The documented graph-node command fails out of the box (BLOCKER)

`resolve_runs/graph_v2/README.md` §"Translation sample" gives the node command. Running it
verbatim:

```
⛔ ConfigError: prompt file(s) on disk but never sent: delta_investigation.md,
   k3_validity_report.md, opus_recheck_report.md.
```

The orphan-prompt guard is working correctly — `config_graph_nodes.json`'s
`prompt.unused_files` must enumerate every `.md` in any directory contributing a
system-prompt file, and three `.md` files were added to `graph_v2/` after the config was
generated. **Any new `.md` written into `resolve_runs/graph_v2/` breaks the node pipeline.**

The fix (`node_corpus.py` regeneration) is nowhere stated as the remedy for this error. I
verified it: `node_corpus.json` returns **byte-identical** (seed 42), and
`config_graph_nodes.json` gains exactly the three entries. But a fresh agent facing a
`ConfigError` naming three unrelated analysis documents has no reason to run a *corpus
generator*, and the plausible wrong moves — hand-editing `unused_files`, or deleting the
three `.md` files — are both worse.

**Severity: blocks the entire node path at command one.** This is also a self-inflicted
trap for anyone (including this audit) who writes a report into `graph_v2/`.

### G2 — The node cost gate has $0.003 of headroom

Measured worst-case for the default 15-node selection: **$0.9970** against a ceiling of
**$1.00**. Nothing anywhere states this. A fresh agent adding one node, raising
`max_attempts`, or lengthening a prompt file gets `CostGateError` and — without the runbook
— the single most tempting fix is to raise `max_cost_usd`, which is a spend decision
disguised as a config typo. The gate's own error message invites exactly this: *"Narrow the
selection or raise `cost.max_cost_usd` deliberately."*

### G3 — The mandatory-looking preflight gate fails on a clean checkout

`README.md` puts `translate.py --self-test` first. It exits **1**:
`51 passed, 1 failed` — `dryrun.txt is missing or STALE`. Pre-existing; the artifact simply
was not regenerated. `pytest` likewise: `1 failed, 1053 passed`
(`test_promise_repair.py::test_infeasible_plan_is_reported_and_never_paid`, a stale test
double — `TypeError: bad_locate() got an unexpected keyword argument 'seed'`).

A hands-off agent that (correctly) gates on preflight exit codes stops before it starts. One
that ignores exit codes has just disabled its only offline check. Neither failure is
documented as expected. **A known-failure baseline is the thing that was missing.**

### G4 — Stage numbering is contradictory across the source of truth

The task, the code, and the docs use three numberings. `STEP_stage3.md` records the
contradiction honestly:

> "The Part 3 flowchart numbers probe cases **3** and read-back **4**. Part 4 says *'the
> probe cases at **stage 4** are the unit tests'*. Same object, two numbers. Recorded, not
> resolved: it is a defect in `03_pipeline.md`'s prose."

Meanwhile `link_nodes.py` calls itself "Step 3", `readback.py` and `seats.py` both call
themselves "Stage 4", and `STEPS34_READINESS.md` uses "Step 4a / Step 4b" for readback R1/R2
and R3. An agent told "run stages 1–4" cannot map that onto files without guessing. The
runbook's §1 table is entirely inference.

### G5 — Stages 3 and 4 have no runnable entry point

| module | `main()` | `__main__` | CLI usefulness |
|---|---|---|---|
| `translate.py` | ✅ | ✅ | full |
| `link_nodes.py` | — | ✅ | full |
| `probe.py` | ✅ | ✅ | takes `.lp` paths only — not a run directory |
| `readback.py` | ❌ | ❌ | **none — library only** |
| `readback_r3.py` | ✅ | ✅ | present but not a pipeline driver |
| `seats.py` | ✅ | ✅ | **only `--cost`, a survey** |

There is no script that takes a run directory and produces a readback or a seat report. The
agent must compose `schema.validate` → `probe.probe_clause` → `link_nodes.merged_gloss` →
`readback.render_module` / `readback_r3.render_r3` itself. The recipe exists — in
`STEPS34_READINESS.md` and `READBACK_SMOKE.md` — but as prose in two files that nothing
upstream links to.

### G6 — ⛔ Stage-4 seats are structurally unrunnable (INSUFFICIENT)

`seats.judge` raises without an explicit `client_factory`, by design: *"a default that
quietly reaches the network is the one mistake a revert cannot undo."* Correct. But a grep of
the whole tree shows **every `client_factory` in existence is a test stub or
`translate.run`'s own**. No blessed, config-driven seat factory was ever written.

`READBACK_SMOKE.md` names this as open gap #2 and specifies what the seam needs:
`json_schema → json_object` forcing (the config's json_schema is the stage-1 *module* schema
and would mangle a seat reply), `max_tokens → seats.SEAT_MAX_TOKENS`, and an envelope→text
adapter. A capable agent could write those fifteen lines. **It should not.** Deciding what
the seats are shown is precisely the design decision `seats.py` is architected around (seat
4c's anchor property is enforced by *the absence of a parameter*). This is a stop-and-ask,
and nothing in the repo says so.

### G7 — No stop-and-ask conditions are written anywhere

Grep for `STOP condition` / `stop-and-ask` across `.py` and `.md` in phase_1 returns three
hits, all about a parity threshold in `frontier_review.py`. There is no list, anywhere, of
what an autonomous agent must escalate rather than decide. §0 of the runbook is entirely
synthesised from scattered practice — status prose in `walkthrough/STATE.md`, comments like
`--live # needs authorisation`, and the hedged paragraph in `AGENTS.md`.

### G8 — "Never spend without explicit human authorization" is not a rule anywhere

The strongest statement in the auto-loaded brief is hedged: *"If you find yourself about to
spend, check that the question genuinely needs a new model call."* "Check that" is not "get
authorization." `--live` has **no confirmation prompt** — one flag spends immediately. The
actual protection is default-off plus the cost gate, both of which are good; the *norm* is
not written as a rule an agent could follow.

Compounding this: **phase_1's spend is invisible to `spend.py`**. The provider is defined
inline in the config rather than in `providers.json`, and `spend.py` prices only from the
latter, so the repo's `BUDGET = 8.50` does **not** bind this harness by any mechanism —
only by manual reconciliation. To the repo's credit this is documented loudly and `run.json`
records `visible_to_spend_py: false`. But an agent reporting "we are within budget" using
`spend.py` would be wrong.

### G9 — The auto-loaded agent brief never mentions this subtree

`AGENTS.md` / `CLAUDE.md` is the only brief that loads automatically. It says *"Most work
happens in `semi-formal-experiment/`"* and routes the reader through five
`semi-formal-experiment/` documents. **It never mentions `walkthrough/` or
`paper_pipeline/` at all,** and there is no `walkthrough/AGENTS.md`.

Consequence: an agent that dutifully follows the documented reading order arrives at
`MODULE_MAP.md` §11's anti-rules — which are **entirely `semi-formal-experiment/`-scoped**
(containment, dossier, patient, threshold, benchmark; not one of them touches `translate.py`,
`schema.py`, or `graveyard.py`) — and learns nothing about the graveyard cap, the cost gate,
`--live`, or the staleness guard. The governance it is handed is for a different subtree.

### G10 — `EXPERIMENTS.md`'s "Read this first" is a trap

`resolve_runs/graph_v2/README.md:9` says of `EXPERIMENTS.md`: **"Read this first."** It is
**2,183 lines**, chronological, with no table of contents, no "current state" section, and
no operational reference. Roughly 60% of the operational facts a hands-off run needs exist
as **single sentences past the 30% mark under headings that do not name them.** Worse,
several late entries silently retract earlier ones — the final entry (99.9% through)
corrects "40 real defects" to **14**, and an entry at 81% reverts a token-cap change made at
80%. An agent that reads the first 500 lines and stops acts on withdrawn conclusions.

### G11 — The VERDICT.md *contents* spec is unlinked

The graveyard's *prohibition* is excellent and discoverable from code alone (see Part 3).
But **what a VERDICT.md must contain** — cause, where the fix belongs, held-out result, what
would have caught it earlier, plus four tripwires — exists only in
`PROPOSAL_graveyard.md:169-177`, a file framed as a *proposal*, that nothing in the code,
config, or `README.md` links to. `phase_1/README.md` does not mention the graveyard at all
(grep: zero hits). The two open entries in `repair_graveyard/` contain no README pointing
anywhere.

### G12 — Node-vs-clause config differences are undocumented as a set

The two configs differ in five load-bearing ways beyond paths — `max_cost_usd` 0.25 vs 1.00,
`max_attempts` 3 vs 5, `resample_truncation` unset vs 2, and different graveyard and worked-
example files. No document compares them. An agent that reads `config.json`'s excellent
inline comments and then switches to `--config config_graph_nodes.json` will carry the wrong
numbers in its head. I built the comparison by diffing the JSON.

---

## Part 2 — Things that are actively WRONG in current docs

Stale instructions are worse than missing ones. Ranked by how badly they mislead.

| # | Location | What it says | Truth |
|---|---|---|---|
| W1 | `node_corpus.py` docstring, "Then:" block | `$VENV ../../translate.py --config resolve_runs/graph_v2/config_graph_nodes.json --dry-run` | **Wrong twice.** There is no `--dry-run` flag (argparse: `unrecognized arguments: --dry-run`); a bare invocation *is* the dry run. And the config path is relative to `phase_1/`, not `graph_v2/`, so the command fails from the directory it tells you to run it in. |
| W2 | `translate.py` module docstring (`:7`, `:10-14`) and end-of-run banner (`:1225`) | *"Stage 1 has never been run"*; *"⛔ IT VALIDATES NOTHING ABOUT THE TRANSLATION"*; every run prints *"⛔ NOTHING here has been validated. No compile, no link, no read-back."* | The exact opposite. Stage 2 has been the unconditional gate for a long time — every attempt is compiled, link-checked, shape-checked and cycle-checked before anything is written. **A fresh agent reading the code's own docstring would conclude its clean run means nothing.** `README.md` flags this, and notes `translate.py` is not a watched file so nothing will catch it. Still present. |
| W3 | `READBACK_SMOKE.md` "Integration gaps before full step-4 on nodes, ranked" | Gaps 1, 3, 4, 5 (seat item-id disclosure, node clause text, cross-node gloss, link-scope hygiene) block stage 4. | **Gaps 1, 3, 4 and 5 are fixed in code** and pinned by `test_stage4_node_plumbing.py` (21 tests, passing): `build_4b_prompt` now takes `ids`, `readback.clause_text` returns the narrowed span not the packed prompt, `link.dedupe_shared_preamble` exists, `%!show_trace` stripping is tested. **Gap 2 alone is still open.** The doc's status is 2 days stale and would make an agent abandon a working path. |
| W4 | `phase_1/README.md` | "53 checks"; "Currently 27,754 chars from 4 files" | 52 checks; **37,891** chars (clause config) / 36,605 (node config). The prompt has grown ~37% since that line was written. |
| W5 | `graph_v2/README.md:9` | Of `EXPERIMENTS.md`: "**Read this first.**" | Actively harmful — see G10. It is a lab notebook, not a reference, and reading it partially yields retracted facts. |
| W6 | `graph_v2/BATCH_DESIGN.md:3` | "Status: DESIGN — not yet built", with the 50%-discount question listed as open | Batch **was** built (`dispatch_core.py`, `translate_exec.py`), is the driver default (`driver_config.json: "mode": "batch"`), and the discount was confirmed. An agent reads this and concludes batch mode does not exist. |
| W7 | `phase_1/README.md` "Known unpinned edges" | Lists the repair-default three-way disagreement, the misdiagnosing `CorpusError`, the `sys.path` hazard | These are honestly recorded — but the `sys.path` one is no longer hypothetical: `READBACK_SMOKE.md` records it biting for real ("`semi-formal-experiment/` must go LAST: its `translate.py` shadows phase_1's — bit once, loudly"). The README still calls it "one filename away from a very confusing bug." It already happened. |
| W8 | `graveyard.py` error message; `translate.py` cost-gate message | "Diagnose and clear them before translating more"; "Narrow the selection or **raise `cost.max_cost_usd` deliberately**" | Not wrong, but both messages address a *human*. Handed to an autonomous agent they read as instructions to clear the graveyard and raise the ceiling — the two things it must never do. The messages need an "if you are an agent, stop" clause, or the runbook must supply it (it does: S2, S3). |

---

## Part 3 — Safety rails: what I probed, and how each behaved

Good news first: **every rail I tested fires correctly, and all of them fire before money
moves.** The repo's protective engineering is genuinely strong.

| Rail | Enforced in code? | Fires before spend? | Discoverable unbriefed? |
|---|---|---|---|
| Graveyard cap (40 open) | ✅ `graveyard.py:211-223`, called at `translate.py:1301-1303` | ✅ after the cost gate, before any dispatch state exists | ✅ **in the error message itself** |
| No bulk clear; VERDICT.md required | ✅ `graveyard.py:188-203`, tested (`test_graveyard.py:105-115`) | n/a | ✅ **in the docstring and refusal message** — "⛔ There is deliberately no clear-all" |
| VERDICT.md *contents* | ❌ | n/a | ❌ **G11** — only in an unlinked proposal doc |
| Cost ceiling | ✅ three layers: `--live` default-off, pre-send `cost_gate()`, measured post-billing `max_cost_usd` | ✅ | ✅ `config.json` + README |
| Unpriced provider = over budget | ✅ `translate.py:986-988` | ✅ | ✅ |
| Never write into an existing run dir | ✅ **structurally** — `os.makedirs(outdir)` with no `exist_ok`, timestamped names | n/a | ✅ `README.md:205-206` |
| Refuse on typo'd clause/section id | ✅ `CorpusError` | ✅ | ✅ |
| Refuse "translate everything" by accident | ✅ `CorpusError` on empty selection | ✅ | ✅ |
| Orphan prompt file | ✅ `ConfigError` | ✅ | ✅ (and see G1) |
| Truncation / empty response | ✅ `ProviderError` | n/a | ⚠️ partly — see below |
| `seats.judge` refuses a default client | ✅ | ✅ | ✅ in the module docstring |
| Staleness guard (`walkthrough/model/guard.py`) | ✅ blocking pre-commit + advisory hook; watches `prompt/*.md` and `schema.py` | n/a | ⚠️ **currently RED by design for all five phase_1 watched files** — an agent will hit it and must not clear it |
| "Never bypass guard.py" | n/a | n/a | ❌ **not written.** Only `--accept --all` is prohibited (`DEFERRED.md:236-238`); `--no-verify` is *explicitly sanctioned* at `DEFERRED.md:229` |
| "Never lower a quality floor" | ✅ tested in `semi-formal-experiment/` | n/a | ✅ `AGENTS.md` — but the enforcement (`test_quality_floor.py`, the `CEILING_BAND` leak signature) is `semi-formal-experiment/`-scoped; phase_1 has no analogue |
| "Never spend without authorization" | ❌ | n/a | ❌ **G8** |

**The one rail that is misleading rather than missing:** the truncation guard. `README.md`
is admirably honest that it **cannot fire on the configured model** — together.ai returns
`finish_reason: null` for DeepSeek-V4-Flash, so a cut-off completion surfaces one step later
as a JSON parse failure *reported as "the provider ignored `response_format`"*. An agent
debugging that message will chase format forcing when the real cause is length. The correct
diagnosis is documented, but in a README paragraph an agent reads before the failure, not
after.

---

## Part 4 — Tribal-knowledge inventory

Facts a fresh agent cannot get from the repo, or can get only by reading a 2,183-line
notebook past the 60% mark. All are now in the runbook. Discoverability column: where it
*actually* lives.

| Fact | Lives at | Discoverability |
|---|---|---|
| **together.ai's WAF 403s stdlib urllib on the batch endpoints while accepting `curl`** | `EXPERIMENTS.md` L715-717 (33%), inside a section titled "BATCH SLA PROBE RESULT"; `dispatch_core.py:863` | ⛔ The word "curl" appears **once** in 2,183 lines. Chat completions are fine on urllib, so this only bites in batch mode — as a mystery 403. |
| **API key falls back to parsing `export` lines out of `~/.zshrc` / `~/.bashrc` / `~/.bash_profile`** | `translate.py:500-523` only | ⛔ **In no `.md` in the repo.** Explains why a run can succeed with no key in the environment — and why it fails on a machine where the key is elsewhere. |
| **Batch latency variance: measured SLA 62s, observed >45 min for a 19-request batch** | 62s at L711 (33%); the >45-min caveat at L1671-1673 (76%) | ⛔ Split across the file, optimistic number first. Highest-risk omission for an unattended run: the agent diagnoses a hang that isn't one. |
| **`curl: (6) Could not resolve host` is a network outage, not a terminal error** — the batch is safe server-side; the poll must back off, never exit | L1708-1726 (78%) | ⛔ Buried, though under a findable heading. This killed a real unattended run. |
| **HTTP 402 flaps for minutes after a credit top-up**, so it rides a short 2-retry ladder rather than being terminal | L1306-1313 (60%); `dispatch_core.py:659-670` | ⛔ Counter-intuitive (402 reads as terminal). The code comment is clearer than the log. |
| **`resample_truncation` is inert on repair rounds** (`complete_messages` bypasses `Client._retrying`) and inert in concurrent mode | L1319-1321 (60%), one sentence in a bullet | ⛔ An agent sets it and wrongly believes repair rounds are covered. |
| **Truncation is a provider-side *stochastic* pathology; raising `max_tokens` was tried and REVERTED** — "low caps are the fail-fast mechanism" | L1772-1795 (81%) | ⛔ The obvious fix is the wrong one, and the reversal is later in the file than the change. |
| **Graph node ids are not valid ASP constants** — `L527-796_n012` parses `L` as a variable and `-` as subtraction; clingo refuses every module containing an `assert` | L373-380 (17%), under the vague heading "TWO STRUCTURAL DISCOVERIES" | ⛔ Already fixed in the adapter, but this silently zeroed an entire run's success rate once. Anyone hand-building a corpus repeats it. |
| **What a good run looks like: 8–13 of 15; run-8 and the 08-12 rerun both 13/15; $0.045–$0.095, 25–49 calls** | Scattered across ~10 run-log entries, no table | ⛔ Greppable by "/15" if you know to. I built the table from the `run.json` files. |
| ⭐ **The acceptance rule is the finding-class distribution, not the pass count** — "±3 noise on 15 nodes; class extinction is signal, rate wobble is not" | L425-430 (19%), under no descriptive heading | ⛔ The single most important interpretive line in the repo, and it is unheaded. Without it an agent reports "we improved 10→12" as a result. |
| **`node_corpus.py --ids` / `--all` clobbers `node_corpus.json` and breaks 6 pins** | L1190-1194 (54%) | ⛔ Silent corruption of run comparability. |
| **Every `graph_v2` script assumes `graph_v2` as cwd**; two probe scripts were once written to the repo root by cwd drift | L1674-1676 (76%) | ⛔ In the "HANDOFF SNAPSHOT" — the entry written *for* a context-free successor, filed chronologically like everything else. |
| **`semi-formal-experiment/` must go LAST on `sys.path`** — its `translate.py` shadows phase_1's | `READBACK_SMOKE.md`, "bit once, loudly" | ⚠️ Findable, but only in a smoke-test doc. |
| **Clause-identity slip is a 3-instance open class; the fix (enum-force `clause_id`) is designed, not shipped** | L1396-1397, L1417-1419 (65%) | ⛔ Its *status* is the easy thing to misread — "lever tracked" reads as done. |
| **Batch kill-recovery is unsupported**: a killed batch run's submitted, paid job is abandoned | `translate_exec.py` docstring, "Divergences accepted by name" | ⚠️ Well written, but in a module docstring an agent reaches only after choosing batch mode. |
| **Prompt-cache ordering**: brief verbatim first, dispatch block last, document via tool results after — the 2026-08-10 build did the reverse and got zero cross-agent cache sharing | `graph_v2/README.md` L54-62 | ✅ Actually well placed. |
| **Repo budget `spend.py BUDGET = 8.50` does not bind this harness** | `phase_1/README.md:193-198` | ✅ Documented loudly, to the repo's credit. |

**Structural observation:** the three genuinely runbook-shaped documents in `graph_v2/` are
`GOLDEN_PROTOCOL.md`, `AUDIT_KEY.md` (pre-registered thresholds under a real heading), and
`README.md`'s "Translation sample" section. Everything else operational is chronology.

---

## Part 5 — What remains genuinely underspecified

Items a runbook *cannot* fix, because the repo has not decided them:

1. **The stage-4 seat client seam (G6).** Requires a design decision, not documentation.
   Until it exists, "run stages 1–4" is not a thing that can be done hands-off. This is the
   single item that makes the verdict INSUFFICIENT for stage 4.
2. **Cross-node concept reconciliation.** `link_nodes.py` reports 9 `concept-multi-gloss`
   notes and a closure conflict across 28 modules — the same predicate with different
   written meanings. `STEPS34_READINESS.md` gap 2 says a corpus-level merge/rename policy is
   needed "before requires-resolution numbers mean anything." No policy exists. An agent
   reporting requires-resolution as a metric today is reporting a number whose meaning is
   undefined.
3. **What to do with an `unrepaired` clause.** The graveyard catches it; nothing says
   whether a run with N unrepaired is acceptable, at what N, or who decides. The ±3-noise
   rule covers the pass count but not the disposition.
4. **Whether node rows should carry real `section_id`s.** Today they are placeholders
   (`graph_node`), which makes `link.py`'s L1 anchor layer **inert** on node corpora — L2
   carries everything. `STEPS34_READINESS.md` gap 5 flags this as undecided. An agent
   comparing node-corpus link results to clause-corpus link results is comparing different
   instruments.
5. **The stage numbering (G4)**, which `STEP_stage3.md` explicitly declines to resolve.
6. **Reconciling phase_1 spend with the repo ledger.** Manual, by convention, with no
   procedure written.

---

## Part 6 — What worked from documentation alone

In fairness, and it is a lot:

* `phase_1/README.md` is one of the best module documents I have read. The "What it refuses
  to do" table, the licence contract, the cost-estimate correction (including the admission
  that the printed worst case was **12.7% below** the true worst case, in the one direction
  the config's own comment says must never be wrong), and the "Known unpinned edges" section
  are model-grade. Its three stale numbers are trivial beside that.
* `translate.py --self-test` (52 offline checks), `--show-prompt`, the bare dry run,
  `version.py`, and `link_nodes.py` all ran correctly with no inference beyond the flag
  names — which are self-documenting via `--help`.
* `node_corpus.py` regeneration is deterministic and idempotent, exactly as claimed.
* `STEPS34_READINESS.md` is accurate, short, and ranked. `READBACK_SMOKE.md` is an
  excellent account of what actually happens end-to-end — its only fault is that its status
  is now stale.
* The graveyard's refusal-to-bulk-clear is the best-engineered rail in the repo: the
  prohibition, the reason, and the required artifact are all in the code, and the error
  message teaches the procedure at the moment of failure.
* Nothing I ran spent money, and nothing could have without `--live`.

---

## Part 7 — Recommended fixes, ranked by cost-to-benefit

1. **Regenerate `config_graph_nodes.json`** (one command) — unblocks the node path. Add a
   note to `graph_v2/README.md` that adding any `.md` to that directory requires it. *(G1)*
2. **Delete or correct `translate.py`'s docstring and end-of-run banner.** It tells every
   reader that the harness validates nothing. *(W2)*
3. **Fix `node_corpus.py`'s "Then:" docstring** — remove `--dry-run`, correct the cwd. *(W1)*
4. **Add a status line to `READBACK_SMOKE.md`** saying gaps 1/3/4/5 are closed and pinned by
   `test_stage4_node_plumbing.py`. *(W3)*
5. **Add a `walkthrough/AGENTS.md`** (or a `walkthrough/` section to the root brief) so the
   auto-loaded brief acknowledges this subtree exists. *(G9)*
6. **Hoist an "Operational reference" section to the top of `EXPERIMENTS.md`**, and change
   `graph_v2/README.md:9` from "Read this first" to "chronological log; read the operational
   reference at the top, then this runbook." *(G10, W5)*
7. **Link `PROPOSAL_graveyard.md` from `graveyard.py`'s `clear()` docstring** and from the
   cap error message. Four required fields, one line of pointer. *(G11)*
8. **Regenerate `dryrun.txt`** (`--write-artifact`) and fix `test_promise_repair.py` so
   preflight is green and can be used as a gate. *(G3)*
9. **Mark `BATCH_DESIGN.md` as built.** *(W6)*
10. **Write the seat client factory, or write down that it must not be improvised.** *(G6)*

---

*Audit executed against commit state of branch `walkthrough-prototype`, 2026-08-14. All
commands run with `semi-formal-experiment/.venv/bin/python`. No live API calls; no `runs/`
directory read from was modified; `config_graph_nodes.json` and `node_corpus.json` were
regenerated to verify the G1 fix and then restored to their committed bytes.*
