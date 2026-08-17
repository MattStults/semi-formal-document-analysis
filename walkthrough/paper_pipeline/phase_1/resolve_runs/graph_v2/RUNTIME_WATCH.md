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
  prompt edits while Matt is AFK.
* Diagnoses and outcomes append to `graveyard_watch.json` beside this file.

Budget note: redraws under this policy ride the bulk run's authorization
(BUDGET $25, D6); the gauge is consulted before any batch of redraws.
