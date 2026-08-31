# Runtime watch protocol for the bulk run (2026-08-16, per Matt's D1/D7)

Written into the repo because transcript-only procedure is a review finding.
Two watchers run for the life of the bulk completion run. The judgment work
is done by CLEAN-CONTEXT subagents (that blindness is what makes the audits
valid); the session orchestrator is the loop that applies the rules to
their outputs. Known bound, stated: the watchers live in the interactive
session. If the session dies, the bulk run itself continues unwatched and
the END-of-run corpus gate still fires; restart the session and re-arm from
this file.

## Watcher 1 — per-chunk stage-4 semantic audit (the "step 4" automation)

Trigger: each `chunk rc=` line in `bulk_run.log`.
1. Sample ~6 modules from the chunk's run directory (deterministic: first 6
   by sorted id with ≥1 assert; pad with assert-less if short).
2. Dispatch a blind Fable auditor (protocol of `SEMANTIC_AUDIT.md`: module
   vs span, DROPPED/INVENTED/WRONG-POLARITY/HOLLOW, decisive words quoted,
   no gate results shown).
3. Apply the countersigned floor: **≥85% faithful → continue.** Breach →
   `pkill -f bulk_run.sh`, then the D1 loop: diagnose the failing sample,
   draft a fix, **verify it by redrawing the failing modules and blind-
   re-auditing them**; verified → restart remaining chunks; unverifiable →
   stays stopped for the owner.
4. Append the verdict to `semantic_audit.json`.

## Watcher 2 — graveyard diagnosis

Baseline at arm time: 191 entries. Trigger: same per-chunk event; diff the
graveyard directory against baseline.
For each NEW entry, dispatch a diagnosis subagent (reads `entry.json`, the
standing findings, the attempt transcript; classifies the MECHANISM, not
the check_id — the gen-11 rule).

Fix policy, decided here so the watcher never improvises:
* **Redraw is allowed only when the diagnosis names a cause that has since
  been fixed** (e.g. a pre-seam-contract signature guess, a pre-ruling
  licence tangle) **or a concrete non-prompt fix verified on the case.**
  One redraw per clause; the harness's identical-retry seam guard stands.
* **Never a blind re-roll.** The production loop already spent 3 attempts
  plus a restart; a 4th identical draw is spend without information.
* **Prompt-class diagnoses** (the failure implicates instruction text)
  are QUEUED for the owner — prompt files are guard-watched and D7 excludes
  prompt edits while unattended.
* Diagnoses and outcomes append to `graveyard_watch.json` beside this file.

Budget note: redraws under this policy ride the bulk run's authorization
(BUDGET $25, D6); the gauge is consulted before any batch of redraws.

---

## AMENDED 2026-08-16 (owner directive, unattended block): step 4 is machine-driven

Watcher 1's audit DISPATCH is no longer session-bound. Three layers:

1. **`semantic_gate.py` + `semantic_gate_loop.sh` (nohup, fully automated,
   cheap tier):** two independent UNFORCED DeepSeek critique passes per
   translated module; alarm signal = max FIX-line volume across passes,
   with truncation-as-alarm (no logprobs exist for this model — volume +
   disagreement + truncation are the confidence proxies). Score >=
   THRESHOLD (calibrated on the 20 blind-audited modules by
   cheap_alarm_probe.py) -> write-once entry in `semantic_queue/` — the
   graveyard-shaped audit queue. Resumable; survives this session.
2. **Fable queue drain (frontier, asynchronous):** auditors read
   `semantic_queue/*.json` entries with `frontier_verdict: null`, apply the
   SEMANTIC_AUDIT.md protocol, append their verdict INTO the entry
   (write-once otherwise). Runs whenever a session is alive; the queue
   waits patiently when none is.
3. **The random-sample floor (unchanged, and still the authority):** the
   per-chunk blind Fable sample measures the CHEAP GATE'S MISS RATE — the
   arm series measured single-pass cheap-critic identification at ~21%, so
   the router is never trusted with the 85% floor. A defect the sample
   finds that the gate did not queue is the gate's own failure metric,
   recorded in semantic_audit.json.

### Layer 1 verdict (2026-08-17): NOT DEPLOYED

cheap_alarm_probe.py ran the pre-stated rule and volume routing FAILED
(1/3 defective in the top 8; the top two scores were faithful modules whose
critiques overflowed the cap — the cheap critic says more about good
modules than broken ones; ranking in cheap_alarm_probe.json, $0.03).
semantic_gate.py stays refusing (THRESHOLD None) with the verdict in its
header. The per-chunk random Fable sample (layer 3) is the ONLY stage-4
instrument for this bulk run, and its accumulating labels (~60 by run end)
are the recalibration set if routing is ever attempted again.
