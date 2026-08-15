# GROUP ADVERSARIAL REVIEW — commit `3a354b5`

Two independently-built, independently-green changes reviewed **together** for the
first time: the restart-on-repeat chain policy (`translate.py`,
`resolve_runs/graph_v2/translate_exec.py`, `test_repair.py`) and the arity-aware
declaration check (`checks.py`, `test_checks.py`), plus the `render_error_log`
dedupe.

Clean context. Offline only — **zero API calls, zero spend**. No non-test file was
modified; nothing under `runs/`, `translation_sample/runs/` or `repair_graveyard/`
was written. All disabling experiments were run through throwaway pytest plugins in
a scratchpad, never by editing the tree.

**Combined suite as committed: `1204 passed, 1 xfailed` (3m49s).** Green together.
Green is not the finding.

---

## VERDICT

**NOT SAFE TO RUN TOGETHER ON A PAID CORPUS AS COMMITTED — one blocker, and it is
the one the brief predicted.** The blocker is not a correctness bug in either
mechanism; both mechanisms are sound and their interaction on the *findings* stream
is clean. The blocker is that the chain policy's cost arithmetic **over-charges by
enough to close the gate on every live config**, including the default one, so a
gen-12 validation run would be refused before a single call is made. Two further
decision-changing findings corrupt the artifact the gen-12 run exists to produce
(the graveyard).

**No coverage regression was found.** The arity check's author's central safety
claim is independently confirmed (details in §2).

Fix D1, D2, D3 before the validation run. D1 is a one-line change plus a deliberate
ceiling decision; D2 and D3 are small and local.

---

## DECISION-CHANGING

### D1. The doubled cost estimate now REFUSES all three live configs. `translate.py:1248`, `translate_exec.py:672-674`. Confidence: **certain** (executed).

The chain author is right that the restart doubles the worst case and that pricing
one chain would have printed **50% low** on the output term. But the shim chosen —
feed `estimate_cost` **one chain of `2T`** instead of **two chains of `T`** — is not
a small conservative rounding. `estimate_cost`'s dominant term is
`max_tokens · len(users) · T(T-1)/2` (resent completions), which is *quadratic*:
going `T=5 → T=10` multiplies it by **4.5×** while the true worst case only doubles.

Measured, by driving `translate.load_config` / `build_system` / `build_user` /
`estimate_cost` offline on the real configs:

| config | n | T | ceiling | old (1 chain) | **exact 2 chains** | **shipped `2T`** |
|---|---|---|---|---|---|---|
| `config.json` | 3 | 3 | $0.25 | $0.0872 ok | **$0.1745 ok** | **$0.2744 ⛔ REFUSED** |
| `resolve_runs/graph_v2/config_graph_nodes.json` | 15 | 5 | $1.00 | $0.9970 ok | $1.9940 ⛔ | **$3.3690 ⛔ REFUSED** |
| `resolve_runs/graph_v2/config_corpus_all.json` | 773 | 5 | $8.00 | $24.65 ⛔ | $49.31 ⛔ | $86.70 ⛔ |

Two consequences, both silent blockers:

* **The default config is refused by its own ceiling** — and would *not* be, if the
  restart were priced exactly. $0.1745 < $0.25 < $0.2744. The over-charge is
  precisely the difference between a runnable default config and a dead one. "An
  estimate is allowed to be high" is true in general and false here: this estimate
  is wired to a hard `CostGateError`.
* **`config_corpus_all.json` slice sizing collapses.** That config never passes the
  gate whole (it did not before either, $24.65 > $8.00 — it is run in `--only-stale`
  slices). The largest slice that passes the $8.00 gate drops from **250 nodes to 71
  nodes** (computed by bisecting `estimate_cost` over the real 773-node corpus:
  T=5 → 250 nodes at $7.9701; T=10 → 71 nodes at $7.9252). Any gen-12 slice sized on
  the old arithmetic — the README/runbook cadence is well above 71 — is now refused
  with no explanation beyond "estimated $X exceeds the ceiling".

`config_graph_nodes.json` deserves separate alarm independent of this change: at
**$0.9970 against a $1.00 ceiling** it was already at 99.7% of cap. It has no
headroom for *any* future estimate increase.

**Action this changes:** the gen-12 prior-success/prior-failure validation run, and
every subsequent corpus slice, would be refused at `--live`. Recommended fix, in
order of preference:

1. Price the restart **exactly**: `est = 2 × estimate_cost(..., max_attempts=T)`
   when `T > 1` (the true worst case is two independent chains of `T`, each of which
   `estimate_cost` already over-charges on its `sys+user` term). This preserves the
   never-under-charge rule, keeps `config.json` runnable, and keeps serial and batch
   identical. It must go in **both** call sites in one diff.
2. Then raise `cost.max_cost_usd` on `config_graph_nodes.json` deliberately and with
   the measurement recorded (it needs ≥ $2.00 under the exact price), and re-derive
   the corpus slice size from the exact price (≈125 nodes, not 250 and not 71).

The two call sites are byte-identical today and must stay so — that part is right,
and `translate_exec.py:667-671` says why. Verified: no drift between them.

### D2. A restarted-and-recovered clause is bucketed `first_try` in the graveyard and sampled at 5% instead of 25%; and `write_entry` has no field that records the restart. `graveyard.py:126`, `graveyard.py:149-160`, `translate.py:2487-2491`. Confidence: **certain** (executed).

`attempts` is re-based by the restart. The author justified this by pointing at
`should_keep`'s `attempts >= max_attempts` branch — which is indeed unharmed. But
`should_keep` has a *second* consumer of `attempts` three lines later:

```python
bucket = "repaired" if attempts > 1 else "first_try"
```

Executed against the real function:

```
RESTART+RECOVER: status=translated attempts=1 restarted=True flags=[]
   rates {'first_try':0.0,'repaired':1.0} -> (False, '')      # dropped
   rates {'first_try':1.0,'repaired':0.0} -> (True, 'sampled: every first_try case')
NO RESTART (4 calls): attempts=4 -> (True, 'sampled: every repaired case')
```

All three live configs ship `rates: {"repaired": 0.25, "first_try": 0.05}`. So a
clause that consumed four model calls, froze, was discarded and redrawn, and then
recovered — the single most diagnostically valuable outcome this whole change
produces — is now sampled into the graveyard at **5% instead of 25%**, a 5×
under-representation. This is the graveyard-population distortion the author's
"`restarted` is not a `flag`" reasoning was designed to avoid, arriving through the
other door.

Compounding it: `graveyard.write_entry`'s `entry.json` (`graveyard.py:149-160`)
records `attempts`, `per_attempt`, `flags`, and nothing else numeric. Neither
`restarted` nor `pre_restart_per_attempt` is in `meta` and neither is passed as
`extra`. A graveyard entry for a restarted chain therefore asserts
`"attempts": 3, "per_attempt": [1,1,1]` while its `transcript.json` holds twelve
turns and a restart marker. The run record was correctly taught the new fields
(`translate.py:1425-1431`, `translate_exec.py:568-573`); the graveyard was not.

**Action this changes:** the gen-12 diagnostic corpus. Add `restarted` /
`pre_restart_per_attempt` to `write_entry`'s `meta` (or pass via `extra=` at the
call site), and bucket a restarted chain as `"repaired"` — `attempts > 1 or
getattr(out, "restarted", False)`.

### D3. Flags earned inside the DISCARDED segment survive the restart and attach to a module that segment did not produce. `translate.py:2732`, `2820-2825`. Confidence: **certain** (executed).

`per_attempt` is swapped out at the restart (`pre_restart, per_attempt = per_attempt,
[]`) and `prev_shape` is re-based to the redraw. `flags` is **not** reset. Executed:

```
model replies: [shape-shrunk BROKEN2, BROKEN(repeat → restart), clean module]
result: status=translated  restarted=True  flags=['shrank']  pre_restart_per_attempt=[1,1,1]
```

The kept module never shrank. Three things go wrong at once:

* `run()` prints `↻ m0001: translated on attempt 1 after a fresh restart ⚠️ shrank`
  against a module that is not shrunk.
* `should_keep` returns `True` on `if flags:` — so this clause is force-kept in the
  graveyard on the strength of a discarded draft. That is exactly the pollution the
  `RepairOutcome.restarted` docstring (`translate.py:2477-2484`) says the design is
  protecting against; the protection is one field wide and leaks through `flags`.
* `run.json`'s `flags` for the clause becomes a claim about bytes that were thrown
  away, which is a provenance defect in an artifact the paper reads.

**Action this changes:** what the graveyard contains and what `flags` means on a
translated module. Fix: at the restart, do the same thing to `flags` that is already
done to `per_attempt` — move them aside (`pre_restart_flags`) or clear them.

---

## PRECISION

### P1. The chain author's vacuity claim is wrong: **9 of 14**, not 14 of 14 — and one new pin is genuinely vacuous. `test_repair.py:893-911`. Confidence: **certain** (executed).

Disabling the detector (monkeypatching `translate._reply_hash` to return a unique
value per call — the exact mechanism the pins name) gives `9 failed, 35 passed`.
Correctly-green: `test_a_chain_that_KEEPS_MOVING_is_never_restarted` (declared
negative control), `test_the_run_level_estimate_PRICES_the_restart` (source pin, no
detector involvement), and the two `render_error_log` dedupe pins (a different
mechanism; separately verified — disabling the dedupe reddens
`test_an_IDENTICAL_finding_is_shown_ONCE_with_a_count`, and
`test_findings_that_DIFFER_ANYWHERE_are_never_collapsed` is a declared control).

That leaves one **truly vacuous** pin:
`test_the_loop_does_not_PARAPHRASE_or_RE_RENDER_to_break_a_freeze`. With the
detector fully off, no restart happens, `model.calls[2]` is an ordinary repair round,
and `calls[2][1][0] == calls[0][1][0]` is trivially true — the transcript prefix
never changes. It passes green while measuring nothing about the redraw it names.
Add `assert out.restarted` (the loop's return value is currently discarded).

The arity author's claim is **exactly right**: disabling `checks.arity_mismatches`
gives `8 failed, 26 passed` on `test_checks.py`, 8 of 13 as stated; the other five
are unit pins on `body_uses`/`declared_arities` and silence/negative controls that
correctly stay green.

### P2. `render_error_log`'s dedupe rationale does not describe the arity findings it will actually meet. `translate.py:2503-2506`. Confidence: high.

The docstring's premise — "`where` is `<root>` for the declaration checks, so the
lines are not merely similar, they are byte-identical" — is true of `schema.py`'s
D4b breaches and **false of the new arity findings**, which carry
`where="asserts[0]"`, `"ontology[3]"`, etc. Measured on
`repair_graveyard/l1_170_n087-.../module.json`: two arity findings at
`ontology[3]` and `ontology[4]`, **not** collapsed.

This is the *safe* direction — the dedupe never merges genuinely different sites —
so it is precision, not a defect. But it means the new check emits one
**uncollapsible ~403-character line per body site** into a log whose budget
(`REPAIR_LOG_CHAR_BUDGET = 8_000`, `translate.py:933`) is *asserted* by
`_check_repair_log_budget` and never *measured*. **18 sites** of one wrong-arity name
would breach it and silently under-price the run — the one direction that file says
is forbidden. Maximum observed in the corpus is 2, so this is a note, not a blocker.
Correct the docstring so a later reader does not "fix" the dedupe to key on
`message` alone.

### P3. The stored transcript now contains two consecutive `user` turns. `translate.py:2614-2620`, `self_diagnose.py:71`. Confidence: high.

`record.extend(transcript)` (ending in an `assistant` turn) → `RESTART_MARKER`
(`user`) → `transcript = [first_turn()]` (`user`). The author's core judgement is
**correct**: an invented `"restart"` role or an extra `"restarted": true` key would
be a provider-rejected request, because `self_diagnose.py` re-sends stored
transcripts verbatim through `Client._body_messages`. The current provider is
OpenAI-compatible (Together), which accepts consecutive same-role turns, so the
"one cosmetic cost" framing holds *today*.

The gap: the wire-legality pin (`test_repair.py:875-879`) checks keys and role
values but **not alternation**, so nothing in the suite would catch the day this
project points at an endpoint that enforces strict alternation (Anthropic's does).
Either pin the assumption ("the provider tolerates consecutive user turns") or make
the marker a suffix on the redraw's first user turn rather than its own turn.

### P4. `config_graph_nodes.json` sits at 99.7% of its own ceiling *before* this change. Confidence: certain. Not caused by either fix, but surfaced by pricing them; it deserves a deliberate ceiling decision in the same diff as D1.

### P5. Nothing in the suite prices a shipped config against its own gate. Confidence: high.

`test_the_run_level_estimate_PRICES_the_restart` pins the ratio and a source string;
no test asserts that `config.json` / `config_graph_nodes.json` / a corpus slice
*passes* `cost_gate`. D1 is exactly the failure such a pin would have caught — and it
is the failure mode the brief describes: a change that is green in its own suite and
dead in the real configuration. Adding one is cheap and offline.

---

## NITPICK

* `render_error_log`'s `shown` counter now increments per *finding*, not per emitted
  *line*, so `shown` no longer equals the number of `  - ` lines. Only used for the
  `if not shown` branch, which is still correct. `translate.py:2528`.
* `test_the_run_level_estimate_PRICES_the_restart` pins the literal source string
  `"max_attempts=_max_attempts * 2 if _max_attempts > 1 else 1"`. Fixing D1 will
  redden it — which is arguably the point, but the test's name promises a behavioural
  claim and delivers a textual one; only the serial site is pinned, not
  `translate_exec.py`'s.

---

## §1 — INTERACTION: the arity finding through the chain policy

The attack was the right one and the result is **clean**. Everything below was
executed, not read.

* **`origin="schema"` really is disclosed.** `DISCLOSABLE_ORIGINS = ("schema",
  "link", "probe-structural")` at `translate.py:2456`; the arity finding is
  constructed with `"schema"` at `checks.py:277`. It reaches the repair prompt.
  Verified end-to-end: `render_error_log` over the findings of
  `run_checks(l1_170_n047)` emits the arity line.
* **No other new-origin finding is silently withheld.** `checks.py` constructs
  `Finding` in exactly two places (`checks.py:273` arity, `checks.py:427` schema
  breaches) and inherits `link` findings through `Finding.from_link`
  (`checks.py:339`). The only origin strings in the file are `"schema"` and
  `"link"`, both disclosable. Nothing new is invisible to repair.
* **The arity finding does not mask or short-circuit anything.** It is inserted
  *after* the abstention return and *before* the link stage (`checks.py:436`), and
  `run_checks` has no early exit on `findings` being non-empty — the `lp`/`link`
  pass still runs. Verified on `l1_170_n047`, whose combined log is:

  ```
  [schema/error] asserts[0]: `conflict` is declared at `conflict/2` but a body uses it at `conflict/3` ...
  [link/note]  `root_authority/1` is declared in `%% requires:` and no module ...
  [link/error] `conflict/3` is used in a body, defined nowhere in this link scope ...
  ```

  The clarifying arity line arrives **before** the misleading "missing upstream"
  link line. That is the intended ordering and it works.
* **An extra finding cannot trigger or suppress a restart.** The freeze detector keys
  on `_reply_hash(raw)` — the assistant reply's exact bytes — and never on the
  finding set (`translate.py:2799-2801`). Changing the findings changes what the
  model is *told*, and therefore may change what it *replies*, but there is no path
  from a finding to the detector's state.
* **A restart cannot loop on the arity finding.** The restart is hard-capped by
  `if restarted:` → `return close("unrepaired", ...)` with the `frozen` flag
  (`translate.py:2803-2818`). At most one `break` re-enters the `while True`. Worst
  case is exactly `2 × max_attempts` calls. Pinned and independently reasoned; the
  `while True` is not a runaway risk.
* **The dedupe does not collapse arity findings at different sites** (P2). Different
  `where` → different key → separate lines.
* **`feed_failure` cannot masquerade as a frozen reply.** `translate_exec.py:249-253`
  delivers a transport failure as a `ProviderError` raised *inside the clause body*,
  not as text assigned to `raw`. It never enters `seen`. The author's §7 judgement
  holds.

The two fixes' only real coupling is **cost**: the arity check can only ever *add*
failures (73% unrepaired on the tier analysis), so it raises the number of chains
entering repair, which raises the number of restarts, which the chain policy prices.
That coupling is real and it is D1.

## §2 — COVERAGE REGRESSION: none found (independently verified)

Method: walked every directory under `phase_1/` containing a `run.json`, built a
`(dir, clause_id) → status` index from every `results` list, then ran
`checks.arity_mismatches` over **every module-shaped JSON on disk** (any dict
carrying `ontology`/`asserts`/`beats`) — not only the ones named in a run record.

* **346 module-shaped JSON files scanned**, across 32 run directories plus the
  graveyards. 257 of them are tied to a `run.json` result:
  **237 `translated`, 15 `abstained`, 5 `abstained_under_repair`**.
* **Zero arity hits on any module that translated.** Zero on abstentions.
* **Exactly 3 hits**, all in
  `resolve_runs/graph_v2/translation_sample/repair_graveyard/`:
  `l1_170_n047` (`conflict` 2→3, `asserts[0]`), `l1_170_n087`
  (`output_consumed_by` 2→1, `ontology[3]` and `[4]`), `l171_426_n024`
  (`user_request` 1→2, `asserts[0]` and `[1]`). All three are graveyard entries,
  i.e. clauses that already failed.

**The arity check converts no past success into a failure.** The author's claim is
confirmed independently and over a wider population than they scanned. The fourth
named instance (`l1_170_n088`) has no stored `module.json` under any run directory —
consistent with the author's note that it no longer constructs; its pin is a fixture,
not a stored artifact.

## §3 — the six rewritten pre-existing tests

The diagnosis is correct and important: under the new detector, a script feeding the
same reply twice exercises the **restart** branch, not the accumulating chain. Six
tests were rewritten with `broken(tag)` (`test_repair.py:83-98`). `broken(tag)` keeps
`read_back_slots=["M"]` against a 0-slot read-back, so it is the **same breach with
distinct bytes** — the property the rewrite needs.

Checked one by one; **no coverage lost**:

| test | claim | still measures it? |
|---|---|---|
| `test_the_transcript_alternates_user_and_assistant` (:112) | roles alternate over a 3-round chain | yes — `BROKEN2, BROKEN3` keeps the chain accumulating to attempt 3 |
| `test_the_transcript_PREFIX_is_byte_identical_as_it_grows` (:125) | prefix stability ⇒ cache hits | yes — compares `calls[0]` vs `calls[1]` of a real accumulating chain |
| `test_the_clause_is_in_the_transcript_exactly_once` (:137) | clause not restated | yes |
| `test_the_error_log_ACCUMULATES_across_attempts` (:152) | `"attempt 1"` appears exactly once in the final transcript | yes — and this one would have been *actively wrong* under the old fixture, since a restart discards the transcript |
| `test_exhausting_max_attempts_is_RECORDED...` (:253) | 3 distinct failures ⇒ `unrepaired` | yes — and this is the one the freeze detector would have silently converted into a restart test |
| `test_findings_per_attempt_is_recorded...` (:276) | `len(per_attempt) == 3` | yes — under the old fixture `per_attempt` would have been re-based and this would have measured the restart |

Three further sites (`:189`, `:198`, `:460`) and `:265` were switched for the same
reason; `test_the_log_carries_the_MODULE_as_well_as_the_finding` still asserts the
substring `"producing this is forbidden"`, which `BROKEN` (the attempt-1 argument,
unchanged) still supplies. Swept the rest of `test_repair.py` and every other
`repair_loop` caller in the tree (`test_latent_paths_steps14.py:283`, single-reply):
**no remaining script feeds a duplicate reply except the four that mean to**.

## §4 — chain-policy semantics

* `frozen` as a flag on an unchanged `unrepaired` status: **correct**. `unrepaired`
  is already unconditionally kept by `should_keep` (`graveyard.py:120-121`), so the
  flag adds separability without changing sampling. Verified.
* `restarted` as a field, not a flag: **the reasoning is right and the
  implementation leaks** — see D3. Flags earned pre-restart route the clause into the
  graveyard anyway.
* Re-based `attempts`/`per_attempt`: safe for `attempts >= max_attempts`, **unsafe
  for the `repaired`/`first_try` bucket** — see D2.
* Refreeze accounting: `attempts = n + 1` where `n < max_attempts` always holds (the
  `n == max_attempts` branch returns first), so the refreeze return can report
  `attempts < max_attempts`; the `frozen` flag keeps it anyway. Consistent.
* `max_attempts == 1`: the `for` returns at `n == 1` before any repeat check can run,
  so no restart is possible — which matches the `if _max_attempts > 1 else 1` guard
  on the estimate. Consistent.
* `resample_truncation` / `_retrying`: untouched, one level above the loop. No
  interaction.
* Abstention: `"abstained" if n == 1 and not restarted else "abstained_under_repair"`
  is right and pinned; a post-restart abstention is correctly *not* a first answer.
* Per-clause spend deliberately not zeroed: **correct**, and correctly the reason the
  run-level estimate must carry the restart — which is why D1 must be fixed by
  pricing it *exactly*, not by dropping the doubling.

## §5 — what must change before the validation run

1. **D1** — price the restart as two chains of `T`, in both call sites, one diff;
   then set `config_graph_nodes.json`'s ceiling deliberately and re-derive the corpus
   slice size. *Blocker.*
2. **D2** — carry `restarted` / `pre_restart_per_attempt` into `graveyard.write_entry`
   and bucket a restarted chain as `repaired`. *Blocker for the artifact, not for the
   run.*
3. **D3** — move or clear `flags` at the restart. *Blocker for the artifact.*
4. **P1** — add `assert out.restarted` to
   `test_the_loop_does_not_PARAPHRASE_or_RE_RENDER_to_break_a_freeze`.
5. **P5** — add one offline pin that a shipped config passes its own `cost_gate`.
6. **P2/P3** — correct the `render_error_log` docstring; decide whether to pin the
   consecutive-`user`-turn assumption.

Nothing here argues for reverting either mechanism. Both are well-evidenced and, on
the findings stream, they compose correctly. The failure is that neither author
priced the other's effect on the gate they share.
