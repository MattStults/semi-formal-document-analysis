# SLICE 4 — result

Zero API spend. Every model call is a local subagent; nothing touched a provider.
`REVIEW_LIST.md`, `PROCEDURE.md`, `checks.py`, `EXPERIMENTS.md` and `usage.jsonl`
were not edited. No git, no commits, no branch change.

## Files

| file | what it is |
|---|---|
| `SELECTION.md` | the deterministic selection rule, the eligible-set size, and the one interpretation I had to make (recorded, with the rejected alternative named) |
| `SWEEP.md` | ⭐ the cross-clause sweep, its calibration, and the delta |
| `LESSONS.md` | candidate review-list entries — mechanical questions, tagged MEASURED/INFERRED and MECHANICALLY CHECKABLE |
| `PROMPT_FINDINGS.md` | ⭐ defects that belong to the prompt, not the translator |
| `out/<id>.json` · `.notes.md` · `.span_enumeration.md` · `.critic_N.md` | per clause |
| `sweep.py` · `validate.py` · `critic_ledger.py` · `build_spans.py` | the tooling, all runnable |
| `DRAFTER_BRIEF.md` · `CRITIC_BRIEF.md` · `SCHEMA.json` · `spans/` | the inputs the agents got |

## The five clauses

| clause | outcome | asserts | critic turn 1 | stage 2 |
|---|---|---|---|---|
| `l1001_1107_n004` | translated | 2 | NOTHING CONCLUSION-CHANGING (1 craft fix applied) | clean |
| `l1_170_n011` | **abstained** | 0 | NOTHING CONCLUSION-CHANGING | clean |
| `l2821_3040_n010` | translated | 0 (content in `ontology`) | ⚠️ **CONCLUSION-CHANGING** — repaired, then **turn 2: NOTHING CONCLUSION-CHANGING** | clean |
| `l3954_4251_n030` | translated | 3 | NOTHING CONCLUSION-CHANGING | clean |
| `l831_1000_n014` | **abstained** | 0 | NOTHING CONCLUSION-CHANGING | clean |

Every module re-derived by the coordinator through `schema.validate_all` +
`checks.run_checks`: **0 breaches, 0 error-severity findings, 5 of 5**. All
remaining findings are `note` severity and are the known-benign
`requires-unprovided` / `concept-declared` / `situation-input` families, two of
which are named anti-rules.

## ⛔ What did not settle — reported unsoftened

* ⛔ **A REPORTING ERROR OF MINE, corrected here rather than quietly fixed.** I
  closed this slice reporting that `l2821_3040_n010`'s turn-2 critic *"never
  returned"* and that a second reader was *"still owed"*. **It did return**, ~1.6
  hours after dispatch, and I had stopped polling before it landed. **I called an
  outstanding result missing while it was still running** — the mirror of the
  failure mode this campaign instruments everywhere else, and worth recording as
  a process datum: a long-tail agent under pool contention is indistinguishable
  from a dead one unless you wait on the completion signal rather than on a
  poll loop. Nothing downstream was built on the wrong claim; the correction is
  below and the item is now **settled**.
* **`l2821_3040_n010` turn 2: NOTHING CONCLUSION-CHANGING, zero fixes proposed.**
  See `SWEEP.md` §7c. The deletion audit came back clean and independent.
* **The pair ran one turn on four clauses and two on one.** The stopping rule was
  the critic's verdict, and four verdicts were NOTHING CONCLUSION-CHANGING at
  turn 1. No pair exhausted its five turns. Whether a second turn on the four
  clean clauses would have found more is untested.
* **Both abstentions rest on an owner-unratified ruling** (`PROVISIONAL.md`: the
  narrowing governs). If the owner rules the other way, `l831_1000_n014` becomes
  a roughly-two-assert module. The abstention rate measures the ruling as much as
  the translator.
* **`n = 5`.** Nothing here distinguishes "the no-disjunction rule prevented the
  E6 harm" from "these five clauses did not invite it".
* **The critic-artifact hash freeze began mid-run**, because the coordinator's
  ruling arrived mid-run. For the two earliest artifacts I can prove no change
  *since freezing*, not *since writing*. No overwrite was detected anywhere.

## The four instrumented gaps

1. **The frame is never audited** → answered in words, by the critic, on 5 of 5.
   Two abstentions. Both critics who translated an `**Example**:` node wrote down
   that the trigger fires and named what overrides it. ⭐ Forcing the question is
   what surfaced `PROMPT_FINDINGS.md` PF-1, which three independent critics then
   reached separately with the same file and line citations.
2. **Classes found late never reach clauses done early** → `sweep.py`, calibrated
   against the previous cohort before use. **Delta: LICINH fires on 2 of the 3
   translated modules and no per-clause pass raised it** — because it is on no
   list, and a class on no list is checked by nobody. A second class
   (BORROWED-GATE) was raised by clause 4 and swept back across all five.
3. **Content deletion is invisible** → assert ledger on every clause, every turn.
   ⭐ **The instrument as specified is not sufficient**, and this slice measured
   why: the one repair that removed content is `asserts` 0 → 0 while `concepts`
   and `inputs` both fell. On a definitional module the content is not in
   `asserts` at all. `LESSONS.md` L4.
4. **Prompt defects masquerade as translator defects** → prompt findings returned
   on 5 of 5 clauses, including on the module with no craft findings at all.
   Under the previous arm at least three would have been banked as "clean".

## The three findings worth the coordinator's time

1. **PF-5** — roughly one node in eleven of the graph corpus is narrowed to
   nothing but an `**Example**:` caption, so under the standing ruling the
   document's worked examples enter the corpus through no module at all. A defect
   in the **narrowing** step, invisible from inside any clause, checkable in four
   lines of regex nobody had written.
2. **PF-1** — `00_task.md`'s "it is an example" abstention trigger versus
   `node_worked_example.md`'s *"not what KIND of passage it is"*, in the same
   system block, with the contradiction arriving later and backed by a shipped
   worked module. Second measured instance of `DEBUGGING_TIPS` §19's
   prose-vs-demonstration class. Prompt-only fix; cheap.
3. **`REVIEW_LIST` P3 fires on every correct zero-assert module**, and its
   literal remedy is to invent a deontic entry the span does not support — the
   P9 failure, on a second entry, uncorrected, and it arms the known E6 branch on
   every ontology-route clause in the corpus. One-line repair. `LESSONS.md` L8 /
   `PROMPT_FINDINGS.md` PF-11.
4. **The E6 amendment** — the one conclusion-changing fix of the slice REMOVED a
   body condition, and its critic applied the trap question in the removal
   direction. **The trap question is symmetric and the E6 record only ever states
   it one way.** `LESSONS.md`, E6 section.
