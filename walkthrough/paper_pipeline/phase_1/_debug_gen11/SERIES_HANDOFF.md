# SERIES HANDOFF — the critic-loop arm series (2026-08-15 → 2026-08-16)

> ⭐ **SERIES PARKED — 2026-08-16 (owner call).** Its question is answered well
> enough to act on (§1), and none of the remaining arms produce a validated
> corpus. The artifact directories this file cites were **deleted from the
> working tree** after being committed in full at snapshot commit **`06e2050`**
> — retrieve any of them with `git show 06e2050:<path>` or check out that
> commit. What survived, and where it went:
> * slice3's `mech.py` + `cross.py` → **`resolve_runs/graph_v2/corpus_gate.py`**
>   (the single operational defect definition, run corpus-wide).
> * the licence question (§7) → **RULED**: `textual` = "the source text says
>   this" — `phase_1/DECISION_licence_textual.md`, prompt conformed at commit
>   `713f8ae`, corpus mechanically salvaged (`licence_fixup.py`, 38→178/203
>   hard-clean with redraws).
> * the abstention contradiction (§7) → RULED in the same commit
>   (establishes-test replaces the kind-of-passage triggers in 00_task.md).
> * the spend gauge (§6) → RESTORED (`providers.json` priced the embedding
>   row; TOTAL $13.69/$20).
> * the fast path onward → `resolve_runs/graph_v2/behavior_pilot/`
>   (`PILOT_SUBSET.md`, `live_pilot.py`, `live_run1/`), and the campaign log
>   entry "THE PIVOT BACK TO THE DELIVERABLE" in `graph_v2/EXPERIMENTS.md`.
> * NOT resurrected, still open: the seam identity contract (arity/sort/gloss
>   per shared name), the review-list fold, CHEAP_ALARM, F2-PRESERVE
>   replication, the `unclear`-vs-`cepa`/`cnpa` code question (§8).

**Read this before touching anything that WAS under `_debug_gen11/`.** It is
the state of the whole arm series as of the last coordinator turn, written into
the repo because transcript-only procedure is a review finding
(`REPRODUCIBILITY.md`).

Companion records (all at `06e2050`, none superseded by this file):
`arms_review/` (shared measures) · `independent_review/` · `ds_critic_arm/` (E) ·
`ds_critic_format_arm/` (F) · `triage/` · `triage/prospective/` ·
`translate_opus/REVIEW_LIST.md` + `PROCEDURE.md` · `opus_pairs/slice{1..5}/`.

---

## 0. ⛔ NUMBERS I PUBLISHED THAT ARE WRONG — fix these before quoting anything

A later model will find these figures in the transcript and in earlier writeups.
They are corrected here and the correction is the authority.

| stated | correct | why |
|---|---|---|
| arm E identified **29%** / repair-given-ID **~62%** | **21.1% / 57.9%** | blind re-score against the frozen key (`ds_critic_format_arm/`). Direction is DOWN, 3 clauses drive it. Arm E's qualitative finding survives; **quote it as a range, never a point.** |
| "the critic MISSED the borrowed-gloss class (20/23)" | it **ruled on it and deferred to the prompt** | it rejected the fix BY NAME twice, citing `10_output_format.md:66` and "the worked example does exactly this". This is a PROMPT defect, not a critic oversight. |
| "the frontier critic costs ~$0.005/clause plus an unbilled critic" | the frontier critic is **not a metered call at all** | it is a model in the harness's own context. `usage.jsonl` has NO frontier rows. Its cost is **agent attention**: 33 adjudicated turns, 50,541 chars of critique for 17 clauses. |
| "15/15 converged" / "the loop converged" | **not supportable** | the blind independent review scored the converged set 10 correct / 3 defective / 4 unsure — and see §3, that verdict column is itself confounded. |
| "~$0.45 / ~$0.53 series spend of $20" | **unknown; the gauge refuses** | see §6. Those were arm-local reconciliations, not the ceiling gauge. |

Previously withdrawn and still withdrawn — do not resurrect: the 32%
over-translation figure (κ 0.248) · the 29.5% shape-flip figure (contradictions
are 6.2%) · the node-conflict triage · "0 of 66 defect-free" · "the review list
is a critic's instrument" · "bucketing is not the answer" · "a prompt cannot
reach these at any level of specificity" (withdrawn: three variants of ONE
mechanism is not a survey of instruments).

---

## 1. The question the series was actually answering

Can a cheap executor (DeepSeek-V4-Flash-0731 on together.ai) produce reliable
ASP translations if a critic reviews its drafts — and does the critic have to be
a frontier model?

**Answer as it stands: yes to the critic, and the frontier critic is currently
load-bearing.** Every attempt to substitute a cheap critic moved the bottleneck
rather than lifting it.

| arm | condition | identified | repaired | `asserts` turn-1 → post |
|---|---|---|---|---|
| Opus critic, 1 round | frontier critic, fresh context | — | — | 24 → **28** (n=13) |
| D — self-review | same instance, in its own transcript | 15% | 15% | — |
| E — peer critic | separate DeepSeek, no drafting context | 21.1%* | 57.9%* (repair\|ID) | 24 → **18** (n=13) |
| F1 — ban only | E + disjunctive remedies forbidden | — | — | 11 → **9** (n=5) |
| F2 — ban + preserve | F1 + must state what the fix must preserve | — | — | 17 → **15** (n=6) |

\* blind re-score, §0.

**The sign of the `asserts` delta is the headline.** The frontier critic ADDS
normative content; every cheap-critic loop DELETES it.

---

## 2. Mechanisms that are MEASURED, not inferred

1. **Branching remedies cause the deletion.** 11 of 39 DeepSeek FIX lines (28%)
   offer the drafter a branch ("either add X or delete Y"); across all 17 Opus
   feedback files there is **1**. Every harm case is a cheap branch taken.
2. **Banning the branch does not fix it — the coin flip moves inside the critic.**
   Arm F drove branch lines 28% → 0% in both cells (verified by manual read of
   every FIX line containing "or") and `asserts` still fell in both. This was
   pre-registered as the null and named as the feared outcome.
3. ⭐ **Forbidding the hedge makes the critic go QUIET, not decide.** FIX lines
   per clause 3.0 → 1.4; identification fell on both instruments in both cells.
4. **Self-review's failure was VANTAGE, not a reading ceiling.** Both cases arm
   D's writeup named were caught by the peer critic, which reasons 8,464–31,723
   chars against arm D's 3,585–14,541 — ~2.5× harder on the same module from a
   colder start.
5. **Classes found late never reach clauses done early.** The Opus critic NAMED
   licence inheritance, called it "LICENCE LAUNDERING" and "mechanically
   checkable; nothing checks it" — then fixed 2 clauses and left 12, and its own
   remedy RECREATED the class two edits after naming it. Cause: the loop is
   per-clause with **no end-of-run sweep**. The check is four lines of Python.
6. **The frame is never audited.** The critic asks "is this a good translation?"
   and never "should this clause have been translated at all?" One clause whose
   span is headed "**Example**: medical question" was translated with **zero
   occurrences of "abstain" in its entire transcript**, though `00_task.md` lists
   "it is an example" as an abstention trigger.
7. **Deletion is invisible to every mechanical check we have.** `l3147_3238_n003`:
   repair deleted 2 of 3 obligations while the read-back still recited all three
   — `translated`, `repair_needed=False`, 0 breaches. Under F1 the ban DESTROYED
   the diagnosis (committed to `oblige respond_appropriately_when_uncertain(R)`,
   the hollow stub the Opus feedback forbids by name).
8. ⭐ **F2's `PRESERVE` converted silent semantic damage into a LOUD schema
   error** — the alternation survived, written with `;`, so the module came out
   `invalid` with 3 breaches. **The only cell whose failure the floor can see.
   n=1. Replicate before believing.** This is the most promising thread in the
   series.
9. **`reasoning_chars` is a perfect format-forcing discriminator**: 185/185
   forced = 0, 64/64 unforced > 0. Forcing the critic's output shape plausibly
   removes the thing that does the diagnosing. Critics run unforced for this
   reason.
10. **Recomputed independently and CONFIRMED**: licence inheritance 32 instances
    across 12 of 17; self-citation 20 across 12 of 17. Two separate code paths.

---

## 3. ⛔ CONFOUNDS AND INSTRUMENT DEFECTS — check before using these columns

* **The Opus verdict column cannot referee anything.** The independent review's
  correct/defective/unsure split correlates with **module size at ρ −0.60** —
  bigger modules judged more correct — and its four UNSURE are all short
  heading/descriptive spans. **It measures span type, not defect.** Any rule
  validated against it is a heading detector in disguise.
* **`polarity = 0` throughout arm F is NOT independent.** `checks.py` was patched
  on 2026-08-16 on exactly the `l4252_4482_n016` construction.
* **Arm F's blinding protocol FAILED** — the operator read each cell's outputs
  while running it. Replacement: an anchor prefilter hashed before the first call
  (armE 32.2% / F1 14.6% / F2 22.1%). Reported at full strength as a method
  finding; do not quote arm F rates as blind.
* **Arm F is badly underpowered and NOT at random.** 10/17 and 11/17 calls
  truncated, delivering 5 and 6 modules. **The three clauses where arm E's
  branch-taking did its worst damage truncated in BOTH cells** — the most
  informative cells are the missing ones.
* **`E6` in `translate_opus/REVIEW_LIST.md` is a measured DEFECT GENERATOR** —
  two different critics produced the identical harmful weakening on
  `l171_426_n022`. It is retained deliberately so arms D/E/F stay comparable.
  **Repairing the list is its own arm.** Its third measurement could not be
  attempted: `l171_426_n022` truncated in both F cells.
* **`arm E/reconcile.py` has a start line but no end line.** Re-run today it
  sweeps up arm F's 21 truncations and reports 25 arm-E cuts instead of 4. Its
  `reconcile.json` was correct only because no later arm existed when it ran.
  **Both `reconcile.json` files are measurements of record — do not re-run them.**
* **The `opus_pairs` cohort is CLUSTERED — coordinator briefing error.** Region
  counts: `l1001_1107`=11 · `l1108_1367`=10 · `l1_170`=1 · `l831_1000`=1 ·
  `l2821_3040`=1 · `l3954_4251`=1. "Every 5th eligible node by sorted node-id"
  interleaves WITHIN a region because the id list is grouped by line range; it
  does not spread across the document. Slice 4 alone read it as five equal blocks
  of the 736 eligible nodes and has corpus-wide spread. **These 25 are a sample
  of two document regions plus four scattered clauses.** Recurrence findings are
  evidence about those regions until shown otherwise. The fix is a SECOND spread
  cohort, not discarding this one.

---

## 4. Triage — a negative result, with one weak survivor

`triage/RESULT.md`. Six pre-registered predictors; outcome columns tiered by
objectivity.

* ⛔ **The starred hypothesis FAILED and points the WRONG way.** Cheap-critic
  *disagreement* (D vs E on identical drafts): ρ = **−0.167** and **−0.154**,
  falsified on both limbs. The clause where the two cheap critics agreed
  *perfectly* drew the most frontier turns — **they agreed because both flagged
  6 of 11 entries. The signal is SHARED ALARM, not disagreement.** n=6.
* **Only `HEDGE` survives** — a defeasibility regex on the span. ρ +0.34
  in-sample, **stronger on transfer** (+0.42 on 25, +0.38 on the 20
  non-overlapping); 6/6 hedged clauses edited vs a 64% base rate, hypergeometric
  p = 0.045. **One cell of six. DOCUMENT-TUNED (lexical).**
* **Two deaths, one instructive.** `FLOORDIRTY_T1` (ρ +0.46) is **untestable on
  transfer — 0/25 variance vs 7/17**: it measured the PIPELINE GENERATION, not
  the clause. A rule keyed to it would have silently become a constant. This is
  the 22-instruments failure mode caught in advance. `BORROWED` won in-sample
  (ρ +0.494, p=0.043) and **collapsed to +0.13** — that shrinkage is what
  selection on 17 points looks like.
* **The headroom is small regardless.** A perfect oracle picking the top 6 of 17
  captures **63.4%** of frontier output vs a **35.3%** random baseline. Nothing
  on this cohort beats ~1.8×.
* ⭐ **The limit triage cannot see, stated by the triage run itself:** a perfect
  triage instrument would still ship the cheap critic's content-deleting repairs
  on the un-escalated remainder. **Fixing deletion is worth more than triage.**

**Prospective test, pre-registered and hashed BEFORE outcomes existed:**
`triage/prospective/PREDICTION.md`, sha256 `9233def5a18777d8ba259759bb2f0df29d42117c4c88ea645a98621ef94bb01b`
(`prediction.json` `150e1dee…`). `HEDGE` fires on **2 of 25** — recorded as
**UNDERPOWERED BEFORE SCORING**, along with the clustering. Score it against the
adjudication-free tier only. Do not rescue it post hoc.

---

## 5. Harness state — CHANGED, uncommitted, in the production path

⚠️ **`translate.py` is modified and is production code, not an arm artifact.**

* A call that raises AFTER the response was parsed now hands the billed envelope
  out (`exc.billed`, `Client.last_billed`); `translate.billed_record()` writes a
  complete record BEFORE the raise propagates. **`billed=False` ⇒ `cost_usd is
  None`** — unknown spend is never reported as zero.
* Run tags: `set_run_tag()` / `run_tag_of(row)`; rows carry
  `…/config.json#run=armF/f2`. **Unset ⇒ byte-identical to the 5,012 pre-existing
  rows.**
* `ds_opus_loop/loop.py`: `record_billed_failure()` writes to
  `st["billed_failures"]`, **never `st["turns"]`**, so turn numbering and
  re-sending turn N after a truncation are unchanged. `ledger_spent()` now sums
  turns **and** billed failures — reading `turns` alone **was the hole**, and it
  fed the `CAP_USD` gate.
* Truncation is a first-class visible outcome. **Nothing retries. No cap moved.**

**Reconciliation, exact to 1e-9:** arm E $0.06723 + $0.01612 = $0.08335 (n=4 cut
at 7168) · arm F $0.06933 + $0.09066 = $0.15999 (n=21 cut at 8192). **57% of arm
F's spend bought nothing.** Every recovered record is `billed and truncated` with
`completion_tokens_at_cut == requested_max_tokens`.

**Test:** `phase_1/test_ledger_hole.py`, 17 tests, offline, no key, no spend
(`usage_log` forced falsy so it cannot append to the real ledger). **No
registration needed** — phase_1's `conftest.py` is 34 lines with only the
graveyard fixture; `_OPTIONAL`/`QUERY_MODULES`/`FORBIDDEN` belong to
`semi-formal-experiment/`, which this diff does not touch.

**Suite as of the fix:** phase_1 **1254 passed, 1 xfailed, 1 failed**. The
failure is `resolve_runs/graph_v2/test_corpus_exclusions.py::
test_the_erotica_gore_permission_is_out_of_the_corpus` — **pre-existing and
unrelated**, it turns on which run directories are on disk.
`translate.py --self-test`: 51 passed, 1 failed — `dryrun.txt` inputs-sha, stale
because `prompt/*.md` was edited by other work. **Neither is from this diff.**

**Deliberately NOT changed, with grounds:** no `max_tokens` anywhere (arm E 7168,
arm F 8192, prod 4096) — a pre-registered variable; changing it invalidates the
E-vs-F comparison. **Arm F's 47% cut rate at 8192, against reasoning traces of
12,257–38,452 chars, means the cap is the BINDING CONSTRAINT on the critic, not a
tail event — a re-run at a higher cap is a NEW ARM with its own PREREG, not a
repair of F.** No retry/resample. `_check_envelope`'s raise-on-truncation is a
contract, not a defect.

---

## 6. ⛔ Spend — the gauge REFUSES to report a total

`semi-formal-experiment/spend.py` currently **refuses**: 1 of 5,156 logged rows
has no price entry (`text-embedding-3-small`). Per its own G1 ruling
(2026-08-13), a partial sum printed as a total is how $9.20 read as 24% of cap.

**So there is no current authoritative series total.** Arm-local reconciliations
are trustworthy and small (E $0.08335, F $0.15999). The ceiling is
`spend.py:BUDGET` = **$20.00** — quote the constant, never a second number.

Two standing caveats printed by the gauge: 2,336 calls had cached input but no
cached rate (billed at full input rate ⇒ **overstatement**), and batch-billed
rows are **not identifiable** in `usage.jsonl`, so list-price totals may
**overstate** actual cost.

**To restore the gauge:** add the missing price to `providers.json`. Do not paper
over it with a partial sum.

---

## 7. What is running / queued

### `opus_pairs` — slice 3 COMPLETE, slice 4 running, slices 1/2/5 KILLED

✅ **SLICE 4 COMPLETED** — including the cross-clause sweep and the critic
artifact audit. 5/5 modules clean through `schema.validate_all` +
`checks.run_checks` (0 breaches, 0 errors); **all six critic artifacts frozen and
verified byte-identical, no overwrites.** It is the only slice with corpus-wide
spread (§3), so it is the series' generalization check and it held.

**Its own self-correction, recorded rather than quietly fixed:** it had reported a
turn-2 critic as never returning; the critic completed **~1.6 hours after
dispatch**, after the coordinator stopped polling. Nothing downstream was built on
the wrong claim. Folded in as `LESSONS.md` L9: **under parallel slices, "did not
return within my patience" and "did not return" are different claims and must be
written differently.** Guard is a dispatch ledger — the same four lines as the
critic ledger. This is the same family as the corroboration-inflation finding
below: reporting a convenient state as a settled one.

⛔ **Slices 1, 2 and 5 were STOPPED MID-RUN for cost (owner's call, 2026-08-16).
Their directories hold PARTIAL artifacts. Do NOT read them as completed slices,
and do NOT compute any rate over them.** Individual per-clause records in them
are usable if cited individually. Slice 4 was kept because it is the ONLY slice
with corpus-wide spread (§3, clustering); slices 1/2/5 drew from the same two
regions as slice 3, so their marginal value was confirmatory.

⛔ **No slice edits `REVIEW_LIST.md`.** The fold remains an uncompleted step.

**⭐ SLICE 3 IS THE STRONGEST RESULT OF THE SERIES. The end-of-run sweep works.**
5 clauses, 10 agents (5 drafters, 6 critics, all fresh separate dispatches), all
5 modules 0 breaches / 0 errors / `repair_needed=False`, re-derived by the
coordinator rather than taken from an agent. 4 closed at pair-turn 1.

The sweep delta — what the per-clause pass structurally could not reach:
* ⭐ **`root_authority/1` is ONE global predicate glossed section-locally by
  THREE different borrowers** ("respect-creators", "privacy-protection",
  "#avoid_hateful_content"), plus a sort split (rule / instruction / heading).
  Each gloss impeccable alone; jointly incoherent. **Zero of five per-clause
  passes raised it, and it was structurally impossible for them to.** This is the
  licence-inheritance class's own shape on a fresh cohort. **UNFIXED — needs an
  owner ruling.**
* Borrowed-`NEEDS` gloss stamped `textual` + self-cite: **1 of 5** per-clause,
  **5 of 5** by sweep.
* Duplicated ontology glosses: 1 per-clause, **6 more** by sweep.

**Reading: per-clause review has a CEILING.** Four of five critics changed
nothing and one made a single additive gloss edit — halt-condition-shaped on its
face — but each produced 8–12 itemised findings and 7–9 named classes, and the
sweep proves "no edits" ≠ "nothing to find". **A positive control fired by
accident**: the coordinator's `validate.py` was briefly broken and reported a
clean module as "2 error(s)"; all four drafters diagnosed it, refused to edit
outside their fence, and did not distort their modules.

**#3 asserts accounting: no repair anywhere reduced `asserts`.** Two critics
considered a reduction and refused it in writing.

**`E6` did not fire — no such entry exists in the current list.** What fired with
E6's signature was **N5**, twice, pushing toward weakening a prohibition; both
readers declined. Following it would have permitted erotica/gore in any case that
merely omits its context. **N5 needs a polarity correction.**

### ⛔ Two findings that RETIRE coordinator framings

1. **"Zero occurrences of 'abstain'" is a NULL DETECTOR with no positive
   control.** A translator told the trigger does not fire has nothing to write.
   Slice 3 replaced it with a check of all four triggers by name (`mech.py`).
   **The abstention gap in §2(6) must be re-measured with that instrument before
   it is quoted again.**
2. ⭐ **The abstention "gap" is a PROMPT CONTRADICTION, found independently by
   slices 2 and 3.** `00_task.md` lists "it is a section heading" and "it is an
   example" as unqualified abstention triggers; **`node_worked_example.md`,
   concatenated AFTER it in the same system block, retires both by name and
   demonstrates the retirement twice** — "what decides is whether the node
   establishes anything the document says, **not what KIND of passage it is**".
   Slice 3's two trigger-shaped spans were both correctly translated. **This is
   an owner decision on `00_task.md`, not a translator defect.**

**⭐ Slice 2 PROMPT FINDING (independent corroboration of §0's borrowed-gloss
correction): THE PROMPT'S OWN GOOD WORKED EXAMPLE MANUFACTURES CITATIONS.**
`authority_levels_hierarchy` and `best_intentions_bias` — both `NEEDS` names —
are marked `textual` citing a node whose quoted source states no ranking; three
derived ontology heads are `textual` while their bodies run through `assumed`
concepts, **breaking `00_task.md`'s own licence-inheritance rule.** A reviewer
pattern-matching to the example scores an honest module's correct `assumed`
markings as defects. This is the mechanism behind the whole borrowed-gloss thread.

### ⛔⛔ THE PROMPT'S WORKED EXAMPLE TEACHES THE DEFECTS THE REVIEW LIST CATCHES

Three independent critics, on three different clauses, traced a module finding
back to the prompt's own **GOOD** demonstration. This reframes the whole
review-list programme: **several list entries are fighting the prompt.**

* **Manufactured citations** — `node_worked_example.md` L329–331 licenses a
  borrowed `NEEDS` concept as `textual` against a source stating no such thing;
  three derived ontology heads are `textual` while their bodies run through
  `assumed` concepts, **breaking `00_task.md`'s own licence-inheritance rule.**
  Found independently twice. A reviewer pattern-matching to the example **scores
  an honest module's correct `assumed` markings as defects** — which is precisely
  what §0 records the Opus critic doing.
* ⭐ **P10's exact defect is DEMONSTRATED** — L532–538 encodes a good/bad pair as
  **one `prefer` with the BAD arm dropped**. The translator is taught the failure
  that review-list entry P10 exists to catch.
* **The abstention triggers** — `00_task.md` L109–114 (and the schema root
  description) versus `node_worked_example.md` L495–548 / L574–579, which says the
  category is explicitly NOT the test and translates a good/bad example node.
  Found independently three times.

⭐ **The open question, stated crisply by a slice-5 critic — this is the decision
to make, and everything above is downstream of it:**

> Does `licence: "textual"` mean **"the source text says this"** or **"this
> node's contract says this"**?

`00_task.md`'s licence table implies the first. Contract 2 plus the worked
example (`node_worked_example.md` lines 46, 48–49, 231) demonstrate the second.
**Both readings are currently taught in one system block.** Answer this and the
borrowed-gloss class, the manufactured-citation findings, and the `assumed`-vs-
`textual` disagreement in §0 all resolve together.

⭐⭐ **Slice 4 located the contradiction INSIDE A SINGLE FILE, with lines — this
is close to decisive.** `10_output_format.md:66-67` **forces** `licence:
"textual"` citing the borrowing node, while **`10_output_format.md:76-78`** says
the same entry records what the clause "has to **assume**" — and
**`00_task.md:26-29` calls the forced reading "the single worst failure available
here."** One file instructs both ways, and the task file names the instructed
behaviour as the worst available failure. **The evidence points to `assumed`
being right and `10_output_format.md:66-67` being the defect** — which would also
vindicate the two arms whose "fix" the Opus critic rejected by name (§0).
Owner decision; the file is guard-watched.

**⭐ NEW SCHEMA GAP (PF3), independent of the two already logged in §8:** the
schema gives a translator **no in-band field to record that a narrowing cut an
exception off a prohibition.** `PROVISIONAL.md` sends it to `notes.md` — OUTSIDE
the artifact a corpus reader sees. Two slices independently hit this: the
resulting over-broad prohibition is invisible in the JSON, and the only
machine-readable trace either drafter could leave was `closure: "unclear"`, which
is a different assertion. **Third schema change the evidence supports.**

* **A FOURTH contradiction, schema vs demonstration (slice 4):** the schema's
  `ontology.gloss` description — *"what the PREDICATE means, not what this
  particular instance asserts"* — read literally requires **identical glosses on
  two entries sharing a head**; the worked example distinguishes them. The
  drafter followed the demonstration (it is what production sends for graph
  nodes) and flagged the tension rather than hiding it. **A future reader going
  by the schema text will call this drift.**

**Consequence: fix the PROMPT before growing the list.** A list entry that
contradicts a demonstration loses — the demonstration is what the model imitates.
This is an owner decision; `node_worked_example.md` and `00_task.md` are
guard-watched.

### ⛔⛔ `P3` FIRES ON EVERY CORRECT ZERO-ASSERT MODULE — fix before any reuse

**Slice 4, MEASURED.** P3 says *"check every entry in `claims` against the
asserts."* A module correctly taking the **ontology route** has no asserts, so
**P3 fires unconditionally, and its literal remedy is to invent a deontic entry
the span does not support.** Two of slice 4's five modules have zero asserts by
design.

**This is the P9 failure exactly, on a second entry, uncorrected.** P9's own
correction records that its original form "fires on every CORRECT node module"
and that this is **"how seat 4c reached 48/86 on known-good modules."**

⭐ **And it COMPOUNDS the E6 trap**: on a zero-assert module the
add-a-condition-or-delete-the-claim branch is armed on **every ontology-route
clause in the corpus**, not on the occasional real gap.

**Repair is one line — "against the asserts AND the ontology."** The evidence that
the CHECKER is already right while the PROSE is wrong:
`sweep.py:C_CLAIMS_UNENCODED` searches both and correctly does not fire. Recorded
as a correction to P3, not as a new row.

⚠️ **Generalise the pattern before trusting any remaining entry:** three list
entries (P9, E6/N5, P3) have now been measured to fire on correct work or to push
toward a harmful edit. **Audit every entry against a known-good zero-assert
module and a known-good ontology-route module before the list is reused.**

### `N6` — declined with grounds TWICE, by different readers

N6 ("regardless of X has a destination and it is `forbid_body`") is over-applied.
Two independent refusals, each with a concrete harm: a `forbid_body` entry would
**ban the document's own live carve-out** (slice 5); and pushing `publicly_leaked`
into an assert body would **permit sharing an un-leaked SSN** (slice 2).
**N6 needs a precondition, not deletion.**

### ⛔ PROCESS DEFECT — critic artifacts were REWRITABLE IN PLACE

A slice-4 drafter found `critic_1.md` **changed on disk between two readers**.
One version reported two prompt findings; the revised one reported "zero
conclusion-changing findings" and one. **Neither reader could tell.** The same
drafter then self-reported having **attributed its own reasoning to the critic**,
and corrected it in place with the correction stated rather than swapping the
text quietly — the right handling.

**Consequence: "the critic confirmed it" is unfalsifiable wherever a critic file
was unversioned.** Invisible to `validate.py`, which does not read prose. All
live slices were instructed mid-run to write critic passes to immutable
turn-versioned filenames, to cite file + sha256 for every "the critic found X",
and to audit what they already had. **Slices stopped for cost may not have
completed that audit — treat their critic artifacts as unverified.**

**Standing rule going forward: a critic artifact is write-once, or it is not a
citable record.** Mechanically checkable in a few lines.

### ⛔⛔ CORROBORATION INFLATION — the run's most important process finding

**Two independent agents, in two different slices, fabricated attributions to an
independent pass. Both errors ran the SAME DIRECTION: they made an independent
reader look like it had corroborated more than it had.** Neither changed a
module, a count, or a verdict. But **"the critic confirmed it" is this run's
load-bearing claim**, and it was inflated in both places.

* Slice 4 drafter: credited the critic with findings it never made, having read
  an earlier version of a rewritable file. **Self-reported.**
* Slice 3 coordinator, on audit: **A-1** credited a critic with an anti-rule
  (*"rename the input leg, never delete it"*) — the critic's actual finding was
  that the entry is load-bearing and must be **left alone**; the remedy was the
  coordinator's own. **A-2** placed *"look at this first"* in quotation marks as a
  drafter's words — a paraphrase of a return message re-quoted as the artifact.
  Twelve further attributions verified line-by-line and stand.

**This is a systematic bias, not noise. Treat every relayed "X confirmed Y" — at
any level, including the coordinator's reports to the owner — as unverified until
it cites file + hash + line.** Both agents corrected **in place with the
correction stated**, never by swapping text; that is the required handling.

⭐ **The mechanism that ALMOST made it worse, and its cause is the coordinator's:**
twice a slice-3 dispatch was refused for **concurrency** (the 20-agent cap the
coordinator's own fan-out saturated) and the slice **re-dispatched the identical
prompt naming the same output file.** Both refusals errored before launching. Had
either been a false negative — agent launches, tool reports failure — **two
agents would have written one critic file with no way to tell.** Retry-on-refusal
into a fixed filename is how the sibling defect gets made. It was not caution
that prevented it.

**Instrument:** `check_immutable.py` (C1 versioned names, C2 manifest match, C3
attributions cite a source) + `MANIFEST.sha256`. ⭐ **C3 fired on 14 paragraphs of
the coordinator's own write-ups on its first run — that is how A-1 and A-2 were
caught instead of shipped.** Recorded as `LESSONS.md` L-1b, placed second because
it decides whether the other entries can be believed.

Two caveats recorded honestly rather than smoothed:
* **C2 is worthless frozen after the fact.** The freeze belongs in the dispatch
  loop — the one thing slice 3 could not fix retroactively.
* **C3 has a high false-positive rate BY DESIGN** (~10 remaining hits, all prose
  about the audit). **Tuning it silent would stop it catching what it caught.**

**Audit strength, stated plainly and not overclaimed:** 0 overwrites detected, but
**mtime records only the last write and no hash was taken at write time.** The
audit rests on dispatch structure — no critic filename was ever handed to two
agents — **not on forensics.** The gap is closed going forward, not retroactively.

### ⭐ `root_authority` — THREE independent slices, three different failure modes

The single most corroborated finding of the run. All three are the SAME borrowed
`NEEDS` name, and none of the three readers saw the others' work.

* **Slice 3, by cross-module sweep:** one global predicate glossed
  section-locally by three different borrowers, plus a sort split
  (rule / instruction / heading). Jointly incoherent. **No per-clause pass could
  reach it.**
* **Slice 4, by grammar:** a drafter had inverted subject and locative — reading
  the argument as a SECTION where a provider node emits a RULE. Corrected against
  `node_worked_example.md` 185–201, where the authority predicate takes a rule and
  the heading appears only as the second argument of a SEPARATE relation. **The
  drafter's own earlier "N8 fix" was the defect: the entry fired correctly and it
  resolved it the wrong way.**
* **Slice 5, by arity:** the drafter chose `/1` and states plainly it is **an
  invention**. If a provider emits `/0` the link silently never fires, and
  **`requires-unprovided` reads IDENTICALLY to "provider not linked yet".**

* **Slice 2, by citation audit (4th mode):** `root_authority`'s entire gloss —
  authority level, non-overridability, section attachment — has **zero support in
  the lines it cites**. A manufactured `textual` citation. Remedy: `assumed` plus
  an inference naming the NEEDS block, costing nothing since it appears in no body.

* ⛔ **Slice 5 critic, by list audit (5th mode): `REVIEW_LIST.md`'s OWN
  illustration is wrong for this predicate.** N1 illustrates a document-fact
  ground atom as `root_authority(section_x)` — a SECTION argument. Slice 4's
  grammar analysis and this module both make the argument a RULE. **The list
  entry teaches the wrong argument sort for the single most-contested name in the
  corpus.** The module did the N8-correct thing (wrote its reading into the
  gloss), so it must NOT be edited; the disagreement should surface at link time.

**Reading: the borrowing seam has no identity contract.** Gloss, argument sort,
and arity are each independently guessable, every guess passes every check we
have, and a mismatch is indistinguishable from an unlinked provider. This is
review-list N8 generalised beyond argument ORDER to argument IDENTITY.
**Mechanically checkable at corpus level; nothing checks it. UNFIXED.**

### Two review-list corrections earned by slice 5 (per-clause record, coordinator killed)

* ⛔ **N6's remedy INVERTS on an exception that lives outside the narrowing.** N6
  says "regardless of X" has a destination and it is `forbid_body`. Here a
  `forbid_body` entry **would ban the document's own live carve-out.** The
  drafter left `forbid_body` deliberately empty and recorded why.
* **A principled asymmetry worth promoting to a standing rule:** importing an
  excluded exception puts a PERMISSION into the artifact marked `textual`, citing
  a node for text the narrowing removed — **indistinguishable in output from a
  real permission.** Omitting it leaves an over-restriction, which stays
  **visible and citable**. *This pipeline prefers the omission.* Recorded in
  machine-readable form (`closure` = `unclear`, not `cepa`), not only in prose.
* Its unsoftened cost, stated by the same drafter: **the `unclear` closure does
  NOT repair the over-reach** — closure governs silence and this is a firing
  rule. Only linking the excepting node repairs it.

**Caveat on all of it:** Opus grading Opus with NO answer key. "Converged" means
little; the recoverable part is the classes that recompute in code — and those
did recompute.
* **QUEUED, not started: `CHEAP_ALARM`** — score a clause by FIX *volume* across
  two cheap passes rather than by their disagreement. **Document-tunedness NONE**
  (no span features, no lexicon), so it transfers for free. Complete arms D and E
  to all 17 (8 + 4 calls), **≈$0.05**, outcome columns already on disk.
  Falsifier pre-registered at ρ < +0.30 or failure to beat 35.3% top-6 capture.
  The n=6 disagreement value is explicitly **not** carried forward as evidence.
  Held only to avoid concurrent `usage.jsonl` writes during other arms.

## 8. Open decisions and unfinished work

* **The `unclear`-vs-`cepa`/`cnpa` question blocks publication.** Does the
  closure McNemar p=0.031 rest on the `unclear` half (floor 0/17 — real) or on
  `cepa`↔`cnpa` (floor 8/17 — unsupported)? Code question.
* **Fix an operational definition of "defect" and re-score every arm through one
  code path.** Arms currently use overlapping predicates.
* **The `asserts`-must-carry-a-body schema constraint** — the only schema change
  the evidence supports.
* **`schema_design/PROPOSAL_defeasibility.md`** — touches 4 guard-watched files,
  needs the owner's attestation. **Its own recommendation is CHANGE NOTHING.**
* **The borrowed-gloss PROMPT defect** (§0) — `10_output_format.md:66` and the
  worked example teach the thing two arms "fixed". Owner decision; the prompt is
  guard-watched.
* **PRs #5, #6, #7** open and stacked on branch `d3-worked-example` (current
  branch). Uncommitted: `translate.py`, `checks.py`, `usage.jsonl`,
  `EXPERIMENTS.md`, and all of `_debug_gen11/`.

## 9. Standing process rules this series confirmed the hard way

* **The driver never runs git.** No agent in this series was permitted to commit,
  branch, or use `--no-verify` (an agent bypassed the guard earlier in the
  campaign; briefs now forbid it explicitly).
* **Freeze the answer key AND the match criteria before any output exists**, then
  score from a shuffled, label-stripped pool. Arm E's headline moved 8 points
  when this was done properly.
* **Lead with the adjudication-free tier.** `arms_review/floor.py` and
  `measures.py` need no judgment call; adjudicated rates come second, labelled.
* **Parse and re-serialise structured files. Never regex them.** A regex edit to
  a JSON config swallowed the `repair` block and would have priced a 1-attempt
  worst case while looking like it worked.
* **Never pin an exact count of a live artifact** in a test.
* **Labels direct ATTENTION, never TRUTH.**
