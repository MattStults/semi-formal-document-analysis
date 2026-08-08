# What needs your review before this commits

Written 2026-08-07. Ordered by what blocks what.

---

## 1 ⛔ MECHANICALLY BLOCKING THE COMMIT

The pre-commit hook is installed and `walkthrough/model/guard.py` is red. It blocks any commit
touching a watched file while **any** watched file is unreviewed.

    semi-formal-experiment/.venv/bin/python walkthrough/model/guard.py

**Six watched files. One accepted, five never reviewed.**

| file | state |
|---|---|
| `resources/03_pipeline.md` | ⚠️ **stale again** — you accepted it, then I and an agent both edited it |
| `phase_1/prompt/00_task.md` | never reviewed |
| `phase_1/prompt/10_output_format.md` | never reviewed |
| `phase_1/prompt/20_worked_example.md` | never reviewed |
| `phase_1/prompt/30_failure_modes.md` | never reviewed |
| `phase_1/schema.py` | never reviewed |

Accepting is per file: `guard.py --accept <path>`. There is deliberately no accept-all.

⚠️ **A clean review of the five already ran** (`model/TRANSCRIPTION_REVIEW.md`). It found six items.
Four are fixed. **Two are open and one needs your ruling — see §2.1.** Accepting the five now would
certify files a review just found drifted.

---

## 2 DECISIONS ONLY YOU CAN MAKE

### 2.1 ⭐ Does stage 1 demonstrate a `world`-licensed fact? *(blocks §1)*

The design's *"what a good one looks like"* holds up `m0255`'s `protects_third_party` as the
exemplary `world` fact. Two problems, both measured:

- ⛔ It lives in `behaviour_harm3p.lp` — **behaviour-side material**, which stage 1 is denied. And
  Invariant 2 says the three licence classes *"do not reach the behaviour side… a fourth class is
  required."*
- Across **18 hand-encoded document clauses** (`doc.lp` + `m0255.lp` + `clauses/`): **zero**
  document-side `world` facts. 31 textual, 8 assumed, 0 world.

⇒ Either (a) find a genuine document-side `world` example for the prompt, (b) record that `world`
may have no document-side instances and stop demonstrating it, or (c) rule that the design's example
is simply wrong and remove it there. **I did not choose — this is a design call.**

### 2.2 The other open transcription item

Two of the design's five bad worked examples were swapped out for act-indexing and missing-sayer
cases. Dropped: *"translates in isolation"* and the hollow stub the design calls *"survives a
paraphrase check by construction."* Restore, or record the swap as deliberate.

---

## 3 PROPOSALS AWAITING YOUR REVIEW

| | file | state |
|---|---|---|
| **the graveyard** | `phase_1/PROPOSAL_graveyard.md` | you have read it; you asked for re-review then implement. **Not yet re-reviewed** |
| **stage 3** | `phase_1/STEP_stage3.md` | ⛔ **revision 2's §0 is REFUTED** and not yet reverted — see §4 |
| **stage 4** | `phase_1/STEP_stage4.md` | written by an agent, **not reviewed by me or you** |

---

## 4 ⛔ THINGS I GOT WRONG THAT ARE NOT YET FIXED

**`STEP_stage3.md` §0 is wrong and still in the file.** I argued discrimination coverage should be
built first and labelled verdicts deferred. A clean review refuted it on three independent grounds:

- the cost argument was false — labelling is **~$0.26 for all 593 clauses**, against $6.4 remaining
- one of its two data points was wrong — m0217's rule **does** fire, in 1 of 8 situations
- the concession was far too generous — discrimination coverage reports **byte-identically** for a
  correct module and for one whose meaning is inverted (`permit`→`forbid`)

Revision 3 must revert §0, partition §§1–9 by half, fix a test whose fire condition cannot fire on
the bug it names, and add an enumeration cap and a zero-rule refusal. **Not done.**

⚠️ One review finding I could **not reproduce** (F1: whether a probe case detects the dead C3 claim
at explanation granularity). Recorded as unresolved, not accepted.

---

## 5 FINDINGS ABOUT COMMITTED ARTIFACTS — worth knowing before you sign anything

- ⭐ **`m0255.lp`'s claim C3 is behaviourally inert.** Deleting both its rules changes nothing:
  144→144 models, all five probe cases bit-identical. **Cause found**: a later edit to the same file
  (iteration 3's coherence constraint) subsumes it. Remove that constraint and the counts diverge
  180 vs 192. Recorded in `phase_1/FINDINGS_m0255.md`. **The rules were not deleted.**
- ⭐ **The "5 witnesses" figure cited three times in the design does not reproduce.** The honest
  number is **72**; six projections were tried and none gives 5. The load-bearing half — *zero*
  without the dependency — reproduces exactly. Corrected in all three places.
- **5 of 8 stored modules no longer validate** under the current contract, from two contract changes
  made today. That is the empirical case for artifact versioning (§6).

---

## 6 WHAT IS BUILT AND GREEN

217 tests · `translate.py --self-test` 53/53 · `link.py --self-test` 19/19 ·
`mutate_schema.py` **45 guards, 0 survivors** · spend ~$0.05 of $8.50.

Stage 1 and stage 2 run end to end: schema contract, clingo compile, unresolved names, rule shape,
closure, `beats` acyclicity, concept table — then an accumulating repair transcript with typed
gaming guards. The formal model was retired to its staleness guard, which now watches the
transcriptions.

---

## 7 MY RECOMMENDED ORDER WHEN YOU RETURN

1. Rule on §2.1 (`world` facts) — it unblocks the transcription review and therefore the commit.
2. Re-review + implement the graveyard (you have already called this).
3. `STEP_stage3.md` revision 3, re-reviewed, then implement both halves.
4. Retire `STEP_stage2_and_repair.md` into the design — it is **already** stale, still describing
   repair as a "fresh conversation", the formulation the design corrected today.
