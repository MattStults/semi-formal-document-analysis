# Questions waiting on Matt

**Maintained by the autonomous run. Everything here BLOCKED work; everything else continued.**
Newest first. Each entry says what is blocked, what I did instead, and what a decision costs.

⚠️ **Nothing here was decided unilaterally.** Where a design question arose I recorded it and
worked around it. Where a design ruling already existed I followed it, even where I would have
chosen differently — that is the standing instruction.

---

## Q-1 · Stage 5+ have no design at all

**Blocked:** anything past stage 4. `03_pipeline.md` describes stages 1–9, but only 1–4 have STEP
documents. Stages 5–9 have no plan, no failing example, and no cost model.

**What I did instead:** wrote *initial* designs for the next undesigned components as drafts marked
`DRAFT — NOT REVIEWED`, following the STEP format (a passing example, a failing example, evidence
produced, cost). They are proposals for you to review, not decisions.

**What a decision costs:** reading one STEP draft is ~15 minutes. Implementing against an
unreviewed design risks the thing this project already paid for twice — building a check that
measures the wrong thing and reports success.

---

## Q-2 · The `[L]` half of stage 3 has never been run against a real model

**Status: UNBLOCKED — you authorised the spend before going AFK ("Feel free to spend on the [L]
run"), so I am running it.** Recorded here because the RESULT may need your ruling.

`STEP_stage3.md` §9 says two measurements must exist before any coverage number is believed:
- the **`silent`-rate**. A rate near zero on a corpus where most clauses govern one act is a **seat
  defect**, to be investigated as one — not a conclusion about the translations.
- the **`k` histogram**, from which `probe.max_signature` must be re-set. It is currently 10, from a
  cost model, and nobody has measured the real distribution.

**What needs you afterwards:** if the `silent`-rate comes back near zero, §9 says that is a brief
defect. Rewriting a seat brief is a design change, so I will report and not act.

---

## Q-3 · Stage 4's four seats need spend, and the amount is not yet estimable

**Blocked:** running stage 4 end to end.

Four review seats per clause, over a corpus of 593. The renderer is being built now; until it
exists I cannot count the items each seat must read, so I cannot price it. The project cap is
$8.50 with roughly $2.5 used.

**What I did instead:** everything up to the seats — renderer, the five deterministic RB checks,
and the seat prompts exercised against stubs.

**What a decision costs:** an authorisation and a ceiling. I will produce a measured estimate from
the renderer's real output before asking, so the number will be evidence rather than a guess.

---

## Q-4 · `dryrun.txt` is stale and is the one failing self-test check

`translate.py --self-test` reports 52 passed / 1 failed. The failure predates today.

**I have deliberately NOT regenerated it.** Regenerating bakes the current prompt into the
artifact, which would turn a visible red into an invisible green while changing what the artifact
attests. That is the shape this project keeps being bitten by.

**What a decision costs:** one word. Either "regenerate it" (and it goes green, attesting today's
prompt) or "leave it" (and it stays red and honest until the prompt settles).

---

## Q-5 · `STATE.md` is a deletion candidate with live inbound citations

It duplicates `REVIEW_QUEUE.md` and the phase_1 README and has drifted from both — it claimed
stage 2 was "under review, nothing built" until I corrected it today. But `STEP_stage3.md` and
`STEP_stage4.md` both cite it, and one live finding (weakest-licence inheritance being stated in
two places and computed nowhere) has **`STATE.md` as its only record**.

**What I did instead:** left it, corrected its false claim, and marked it a deletion candidate in
the file itself.

**What a decision costs:** "delete it" means first moving that one finding somewhere live. I can do
that unprompted if you want it gone — say so and it is a ten-minute job.
