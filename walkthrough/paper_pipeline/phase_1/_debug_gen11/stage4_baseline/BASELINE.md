# Stage 4, first correctness baseline over the graph corpus

Run: `resolve_runs/graph_v2/translation_sample/runs/20260815-130831-together-deepseek-v4-flash`
Judge: `deepseek-ai/DeepSeek-V4-Flash-0731` (together.ai), the same flash
provider that produced the translations. Not frontier.
Date: 2026-08-15. Pre-registration: `PREREG.md`, written before the first
paid call and not edited since.

**MEASURED SPEND: $0.083144 over 324 calls.** Ceiling for the task was $0.60;
the printed worst case was $0.4182 and the printed likely case was $0.0711.
The likely-case model was accurate to 17%; the worst case over-charged by 5×,
which is the direction a hard ledger cap wants.

Everything below is MEASURED unless a line says INFERRED.

---

## 1. The population, and where the 88 went

| | n | |
|---|---|---|
| clause ids the translation run attempted | 88 | `run.json:results` |
| modules on disk | 87 | `l1_170_n034` never produced one — unrepaired `schema-breach`, an unsafe ASP variable; it is in the graveyard |
| `outcome: translated` | 82 | 5 `abstained`: `l1_170_n014`, `n061`, `n063`, `n076`, `n079` |
| reached a seat | **81** | `l1_170_n083` refused at `plan_clause`: *"the clause carries a stage-3 expected verdict"* |

**The denominator for every number below is 81, not 88.** The 7 that fell out
fell out before stage 4 could say anything about them, and reporting them as
passes or failures would be inventing a measurement.

## 2. THE HEADLINE

**Of the 81 clauses that reached a seat: 15 clean, 66 with at least one defect
verdict.**

*Clean* means: no `unfaithful` (4b), no `unlicensed` (4c) and no
`not-conveyed` (4d) on any item. `unclear` is **not** counted as clean and
**not** counted as defective — it is its own answer. 4a is advisory (the
author grading itself) and this line does not read it, exactly as
`build_report` does not.

The 15 clean: `l1_170_n018 n019 n020 n021 n022 n023 n025 n027 n035 n036 n039
n059 n064 n084 n086`.

The 66 defective are tabulated most-severe-first in **`DEFECT_TABLE.md`**,
with the seat that caught each one and the item text.

⚠️ **Read this headline with §5 and §6.** 4c alone accounts for the
difference: excluding 4c, 55 of 81 are clean; excluding 4b, 17 are. And 4d
refused on 57 of 81 clauses, so its column is nearly empty. This is a
baseline of an instrument that is only partly working, and I would not treat
15/81 as an estimate of translation quality.

## 3. Every verdict, per seat

| seat | judgements | pass verdict | defect verdict | `unclear` | `unclear` rate |
|---|---|---|---|---|---|
| 4a *(advisory)* | 651 | 644 `as-meant` | 7 `not-as-meant` | 0 | 0.000 |
| 4b | 651 | 452 `faithful` | 70 `unfaithful` | 129 | **0.198** |
| 4c | 651 | 347 `licensed` | 264 `unlicensed` | 40 | 0.061 |
| 4d | 72 | 71 `covered` | 1 `not-conveyed` | 0 | 0.000 |

Pooled `unclear` (4b+4c+4d, the seats `build_report` pools): **169 / 1374 =
0.123**.

⛔ Every one of 4d's 71 `covered` verdicts is stamped `unsupported`, because
stage 3 was not run for this measurement (`discrimination=None`). An
unavailable check is not a passed one. A 4d `covered` here means *a seat says
the claim is conveyed*, and nothing confirms it from outside the seat system.

**167 4b-vs-4c instrument defects** — items where 4b and 4c returned opposite
polarities. 4b reads only the rendering, 4c reads only the module, so the
rendering is the only thing between them; `seats.py` routes these to a human
and never to the translator. 167 over 651 shared items is 26%, which is a
large number and is itself an instrument finding (§6).

## 4. ⛔ THE INSTRUMENT FINDING: 4d refused on 57 of 81 clauses (70.4%)

Single cause, 57 out of 57 — **the model drops the claim label.** 4d's
denominator ids are the module's claim sentences *with their `C1`/`C2`
prefix*; the prompt displays them exactly as `C1 the assistant must adhere to
the Model Spec above all else`; the reply comes back as `the assistant must
adhere to the Model Spec above all else`. `seats._reply_item` matches exactly
(stripped-to-stripped), no prefix tolerance, and `validate_judgements` refuses
the whole seat. The replies are otherwise competent: right count, right
order, real reasons.

Three consequences the owner should hold onto:

1. **4d's 24 adjudicated clauses are not a random 24.** They are the clauses
   where the model happened to echo the label. Anything computed from 4d here
   is conditioned on reply format, so `1 not-conveyed / 72` is not an estimate
   of the dropped-content rate; it is an estimate over a format-selected
   subsample.
2. **This was invisible to every existing test**, for the same reason
   `READBACK_SMOKE.md` gap 1 was: the mock replies in `test_seats.py` and
   `test_stage4_node_plumbing.py` echo the denominator ids exactly. The
   live-shaped pin proves that echoing exactly what the prompt shows
   *validates*; it cannot prove that a real model *will* echo it exactly.
3. **I did not fix it.** A one-line change to `seats._reply_item` (accept a
   `C<n> ` prefix drop, the same family as the already-landed
   stripped-to-stripped fix) would very likely take the refusal rate to
   ~0 — but changing the instrument in the middle of the measurement it is
   being measured by is exactly the tuning this repo has a rule against. It
   belongs in its own cycle, with its own review, and the baseline should
   then be re-run. The 57 refused replies are all on disk under
   `out/raw/*.4d.json`, so that cycle can be validated against them for free.

No 4a, 4b or 4c call refused, and no reply was unparseable. **Instrument
failure rate: 57/324 calls = 17.6%, all of them 4d.**

## 5. What the defects actually are, and how they compare to the Opus read

The comparison target: `_debug_gen11/spotcheck_semantic/verdicts.json` — Opus
reading 25 modules of `20260815-124836` directly, finding 13 defective. Its
modes were: *2 inverted modality* (5), *3 scope drift* (4-5), *5 dropped
content* (2), *1 invented obligation*, *2 weakened modality*, *6 shape
mismatch*.

**Answer: yes, the classes resemble each other, with one dominant class and
one clear miss.**

* **Scope drift / content sourced from outside the narrowed span — MASSIVE
  overlap and stage 4's dominant class.** 179 of 264 `unlicensed` and 37 of 70
  `unfaithful` are on `concepts`, and the seats' reasons are relentlessly the
  same sentence: *"the clause does not mention a ranking of instruction
  authority levels"*, *"the clause only defines Developer as instructions
  given by developers using our API; it does not state that such instructions
  carry the developer level of authority"*. This is Opus's mode 3, and Opus
  wrote the same thing about `l2405_2473_n001` (*"all content sourced from
  outside the narrowed span"*). **See the caveat in §6 — a large part of this
  is the node decomposition, not the translation.**
* **Inverted modality — stage 4 catches the `permit`/`forbid` kind.**
  `l1_170_n088` `asserts[3]` and `asserts[4]`: the module `permits`
  `be_aware_of_system_message` and `receive_hidden_chain_of_thought` where the
  clause says developers **may not** be aware of / receive them. 4b named both
  and named them correctly. `l1_170_n052` `asserts[0..1]`: `forbids
  obey_instruction` where the clause says the instruction is *overridden*, not
  forbidden. That is Opus's mode 2, found independently by the mechanical run.
* **Invented obligation** — `l1_170_n075` `asserts[0]` permits
  `indicate_metadata` where the clause only says metadata may exist. Opus's
  mode 1.
* **Dropped content (Opus mode 5)** is the class stage 4 is *structurally
  worst placed* to see here, and the 4d refusal (§4) removes the only seat
  that looks for it. 1 `not-conveyed` over a format-selected 72 judgements is
  not evidence that dropped content is rare.

### The one shared clause

`l1_170_n056` is the only node id present in both the Opus spotcheck and this
run — but it is a **different translation of it** (Opus read run `124836`,
this is run `130831`), so this is suggestive, not a join. Opus called
`124836`'s version DEFECTIVE, *"5 dropped content / 2: 'Models should honor
user requests' obligation absent; only the exception is encoded"*. Stage 4 on
`130831`'s version: 4b 9/9 `faithful`, 4c 6 `unlicensed` / 3 `licensed`, 4d
REFUSED. So the seat that would have looked for the missing obligation — 4d —
is precisely the one that did not run, and 4b passed everything the module
*did* say. **This is the miss class in miniature: stage 4 grades what is
present and, with 4d down, nothing grades what is absent.**

## 6. ⚠️ WHAT TO DISTRUST IN THIS INSTRUMENT

1. **4d refused 70% of the time (§4).** Biggest single caveat.
2. **4c's `unlicensed` count is inflated by the node decomposition, and I
   cannot tell you by how much.** A graph node is translated with *assigned
   predicate names shared across nodes*; `link_nodes.merged_gloss`
   deliberately supplies a borrowed name's meaning from the node that
   *defines* it. So the rendering legitimately contains a gloss the judged
   node's own span does not license, and 4c — which is shown the item and its
   *cited* text — correctly calls it unlicensed. `provider_texts` only carries
   cross-reference spans for `requires` that resolve **in this run** (56 of 71;
   15 dangle), so many borrowed concepts reach the seat with no supporting
   text at all. INFERRED, not measured: a meaningful share of the 179
   concept-level `unlicensed` verdicts are this, not a translation defect.
   Separating them needs a per-item check of whether the name came from
   `PROVIDES` — that is a free, deterministic check and it does not exist yet.
3. **26% of shared items are 4b/4c instrument defects.** By `seats.py`'s own
   design that is an accusation against the *rendering*, routed to a human. At
   this volume it says the rendering layer over node modules is not yet good
   enough for the two seats to be reading the same thing.
4. **The judge is the same model that wrote the translations**
   (DeepSeek-V4-Flash-0731, same provider, same run config). Self-grading is
   not neutral. The seat is documented as validated at small-model/frontier
   parity, but that validation was not done on node modules, and it was not a
   same-model-as-author test. A frontier cross-check on a 10-clause slice
   would cost roughly $3 and would be the cheapest thing to do next.
5. **The gloss table is fenced to this one run**, not `link_nodes.gather()`'s
   newest-run-wins across all 18. That is deliberate (a seat judging run A's
   module against run B's glosses measures neither), but it means a `requires`
   whose provider was only ever translated elsewhere dangles here and would
   not in a corpus-wide run.
6. **The clean/defective headline is a shape `seats.py` deliberately refuses
   to write inside a report** (`refuse_aggregate` blocks `n_passed`, `4/4
   agreed` and every pass-rate key). It is written *here*, outside the report
   artifacts, because the owner asked for the count. The per-clause reports in
   `out/reports/` are unaggregated and each one passed `validate_report`.

## 7. The `prefer`-polarity question — THE PREDICTION HOLDS

`checks.polarity_findings` (committed `10911de`) over these same 81 modules:
**1 finding, in 1 clause.**

```
l1_170_n053  asserts[0]  `impose_restrictive_rules(D)` is asserted with status
`prefer` but its own read-back calls it 'dispreferred'
```

What the three seats that ran said about **that exact item**:

| seat | verdict | the seat's own reason |
|---|---|---|
| 4b | **faithful** | *"the clause prefers the act of imposing restrictive rules when the conditions hold, which aligns with the clause's implication that imposing overly restrictive rules leads to…"* |
| 4c | **licensed** | *"The clause expresses a preference **against** imposing overly restrictive rules … which supports the asserted preference."* |
| 4a | **as-meant** | *"The assertion correctly captures the clause's preference **against** imposing overly restrictive rules"* |

**Stage 4 caught 0 of 1. Overlap with the polarity detector: zero.**

And it is worse than "structurally invisible". The prediction was that all
four seats judge the English rendering, which is correct while only `status`
is wrong. That is not what happened here: `readback` renders the *status*
field, so the sentence the seats were shown was
`clause l1_170_n053 prefers ⟨act impose_restrictive_rules(D)⟩ when …` — the
inverted claim, in plain English, on the page. **Two of the three seats wrote
a reason that states the correct, opposite meaning ("a preference *against*
imposing overly restrictive rules") and then marked the inverted item as
passing.** The seats read the polarity, restated it correctly, and did not
notice it disagreed with the item in front of them.

So: **the mechanical detector is justified, and by a stronger argument than
the one that motivated it.** It is not merely covering a blind spot in the
seats' field of view; it is covering a case the seats look straight at and
rationalize.

⚠️ **n = 1. Do not over-read it.** The corpus-wide figure is 9 entries across
7 clauses, and this run is 73 nodes from `l1_170` plus 8 from `l171_426` —
6 of the 7 polarity clauses live in other line ranges. This is one clean
observation consistent with the prediction, not a rate. Running stage 4 over
the ~6 other polarity clauses would cost about $0.006 and would settle it;
that is the second cheapest thing to do next.

## 8. Artifacts

| path | what |
|---|---|
| `stage4_driver.py` | the driver (§9) |
| `baseline_report.py` | assembles `out/baseline.json` from the stored reports. Free, re-runnable |
| `PREREG.md` | written before the first paid call |
| `DEFECT_TABLE.md` | the 66 defective clauses, most severe first, every defect verdict with its item text |
| `out/plan.json` | the plan, the cost estimate, the 6 that never reached a seat, the polarity findings |
| `out/reports/<id>.json` | 81 per-clause stage-4 reports, each through `seats.validate_report` |
| `out/raw/<id>.<seat>.json` | all 324 prompts and replies, **including the 57 that failed adjudication** |
| `out/baseline.json` | every count in this document |
| `out/spend.json` | measured spend against the estimate |

## 9. The driver

`_debug_gen11/stage4_baseline/stage4_driver.py`

```bash
PY=../../../semi-formal-experiment/.venv/bin/python

# free — plan all 81, price the run, run the free polarity detector
$PY _debug_gen11/stage4_baseline/stage4_driver.py --dry

# spends — prints the estimate first and REFUSES over --budget
$PY _debug_gen11/stage4_baseline/stage4_driver.py --live --budget 0.60

# free — rebuild the baseline from the stored reports
$PY _debug_gen11/stage4_baseline/stage4_driver.py --report
$PY _debug_gen11/stage4_baseline/baseline_report.py
```

Flags: `--run`, `--corpus`, `--config`, `--out`, `--ids`, `--limit`,
`--force`, `--budget`.

* Without `--live` there is **no client factory at all**, so `seats.judge`
  raises by construction rather than by a flag check.
* The estimate prints on every path; `--live` compares the **worst** case
  (every reply at the 4096-token cap) against `--budget` and refuses over it.
  A second, measured ceiling is enforced inside the client between calls.
* Re-runnable: a clause whose report is on disk is skipped unless `--force`,
  so an interrupted run resumes without re-paying.
* It owns the seat client seam `READBACK_SMOKE.md` gap 2 says nobody owned:
  `format_forcing json_schema → json_object`, `max_tokens → 4096`, envelope →
  text. That seam should move into `seats.py` or a blessed module; it is
  synthesized here for the second time.
* It drives the seats **one at a time** rather than calling
  `seats.run_clause`, because `run_clause` is all-or-nothing and one 4d
  refusal would have discarded three paid, adjudicated seats. Everything after
  the seat loop is `run_clause`'s own sequence, called in the same order with
  the same arguments.

### Two defects the driver found in itself, recorded rather than quietly fixed

1. **It reported $0.000000 over four real billed calls** on the first smoke.
   `translate._check_envelope` reduces the envelope to `{text, in, out,
   cost_usd}` — `usage` does not survive it, so `env["usage"]["cost_usd"]` was
   always absent. Now reads `Client.spent_usd`, the accumulator the client
   bills against. Any other harness reading `usage.cost_usd` off a
   `complete_messages` return is under-reporting to zero.
2. **`run_clause` is all-or-nothing** (above). Measured on the first live
   clause, `l171_426_n001`: 4a/4b/4c adjudicated, 4d refused, and the
   exception discarded all four.
