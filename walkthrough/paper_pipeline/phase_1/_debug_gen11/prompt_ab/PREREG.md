# PRE-REGISTRATION — two prompt A/B tests, written BEFORE any draw

Date: 2026-08-15. Branch `stage4-sees-the-corpus`. Nothing here may be revised after the
first live call; an amendment must be appended below with its own timestamp and reason.

Instrument: `deepseek-ai/DeepSeek-V4-Flash-0731` via together.ai, configured inline in
`resolve_runs/graph_v2/config_corpus_all.json` — the production translator, temperature
0.2, `format_forcing: json_schema`, `max_tokens: 4096`. Calls go through
`translate.Client.complete`, one call per draw, no batching, no repair loop, no shared
context between draws. Arm A is the stock assembled system prompt, byte-for-byte.

**Spend ceiling for this whole file: $0.40 (authorised). Project ledger `spend.py:BUDGET`
= $20.00.**

---

## 0. What is NOT touched

No file under `prompt/`, no `schema.py`, no `resources/03_pipeline.md`, no
`resolve_runs/graph_v2/node_*.md`. Arm B prompts are **copies** under
`_debug_gen11/prompt_ab/promptsB_d1/` and `promptsB_d2/`, reached by arm-B configs in this
directory. Nothing is written to `runs/`, `translation_sample/runs/`, or
`repair_graveyard/`; all output lands in `_debug_gen11/prompt_ab/`. The stage-4 baseline
directory is not read or written.

## 1. Design common to both experiments

- 3 independent draws per (clause × arm) cell. Draws are isolated single calls.
- User prompts are the **exact `*.prompt_user.txt` bytes already on disk** for that
  clause (most recent copy), so the clause side is identical across arms by construction.
- Arm A and arm B system prompts are diffed and both sha256s recorded. Arm B must differ
  from arm A only in the named added/replaced block.
- Task order is shuffled under seed 20260815 so arm is not confounded with call order.
- Analysis unit is the **draw**. Fisher exact, two-sided, α = 0.05. Wilson 95% intervals
  on every reported rate. Per-clause rates reported alongside, because 3 draws on 7–8
  clauses is a small design and a result driven by one clause must be visible as such.

## 2. Protocol rule 1 — instrument check first

Arm A is drawn and scored **before any arm-B call is made**. If arm A does not reproduce
the defect at or above the floor named below, the experiment closes as
**UNTESTABLE-WITH-THIS-INSTRUMENT** and no arm-B money is spent.

---

## EXPERIMENT 1 — D1(a): `prefer` polarity inversion

### Cohort (fixed now, 7 clauses)

The complete set flagged by `checks.polarity_mismatches` over every module copy on disk
(342 translated module files, 80 `prefer` entries, 10 flagged entries in 7 clauses):

`l1108_1367_n027`, `l1707_1973_n006`, `l1974_2125_n019`, `l1_170_n053`,
`l2405_2473_n001`, `l3954_4251_n010`, `l4251_4571_n029`

7 clauses × 2 arms × 3 draws = **42 calls**.

⚠️ Recorded now as a known weakness: this cohort was **selected on the outcome**, so the
arm-A re-draw rate is expected to regress downward from the 100% that selection implies.
That regression is exactly what the instrument check measures, and it is why the floor is
set well below 100%.

### Arm B edit — `prompt/10_output_format.md`, inserted after line 24

Placed there, and not in `00_task.md`, because line 22–24 is the sentence that *defines*
`prefer`; `00_task.md` rule 5b is about the different confusion (comparative collapsed
into `forbid`) and putting a polarity rule there separates the statement from the status
vocabulary it corrects.

### Endpoint (mechanical, no seat)

`defect_1(draw)` = the drawn module trips `checks.polarity_mismatches` (≥1 `prefer`
assert whose own `read_back` matches `checks._DISFAVOURED`). Unparseable draws are
scored `defect_1 = False` and counted separately as `unparsed`.

### Instrument floor

**≥ 8 of 21 arm-A draws (38%) must trip the detector.** Grounds: at 8/21 vs a
hypothesised 0/21 in arm B, Fisher exact gives p ≈ 0.002; at 5/21 vs 0/21 it gives
p ≈ 0.046 and the design has no margin. Below 8/21 → UNTESTABLE, stop.

### Verdicts

- **VALIDATED** — arm-B rate below arm-A rate, Fisher p < 0.05, and no defect-trading
  trigger below fires.
- **NULL** — Fisher p ≥ 0.05.
- **NULL-with-harm** — arm-B rate is significantly lower but a defect-trading trigger
  fires.

### Defect-trading triggers (pre-registered, all mechanical)

Fires if, comparing arm B to arm A, any of these rises by ≥ 15 percentage points:

1. `abstained` rate — the model buys the number by declining to translate.
2. schema-invalid / unparseable rate.
3. **`prefer`-erasure**: draws that emit zero `prefer` asserts. Deleting the entry deletes
   the specification's guidance, which is the failure mode `checks.polarity_findings`
   explicitly refuses to risk.
4. **comparative-collapse**: draws that emit a `forbid`/`oblige` on an act that arm A
   preferred — i.e. the model resolves the polarity by inventing a violation condition,
   the failure `00_task.md` rule 5b and `03_pipeline.md:617` both warn against.

---

## EXPERIMENT 2 — D2: routing a fact away from a deontic status

### Cohorts (fixed now)

**Target cohort, 8 clauses** — the routing study's "either tier DESCRIPTION" set
(`routing_criterion/agreement.json`, kappa 0.725), every one of which routed `deontic`
at attempt-1 (`discoverability.py`: 0/8 to ontology):

`l1108_1368_n004`, `l171_426_n016`, `l171_426_n041`, `l1_170_n005`, `l1_170_n022`,
`l1_170_n032`, `l1_170_n081`, `l796_1000_n034`

**Control cohort, 3 clauses** — drawn `random.Random(20260815).sample()` from the 32
sample items both tiers judged NORM and which are `deontic_hard`. These SHOULD keep their
deontic status; they exist to catch the routing rule over-firing:

`l1611_1798_n006`, `l171_426_n020`, `l427_460_n010`

(8 + 3) × 2 arms × 3 draws = **66 calls**.

### Arm B edit — `prompt/00_task.md`, replacing the "Abstention is a real answer" section

The replacement is stated in full in `promptsB_d2/00_task.md` and diffed in
`system_diff_d2.txt`. Two components, and they are **confounded in this test** — that is
recorded now, not discovered later:

1. **The design change, one sentence:** *"Never give a fact a deontic status."* plus the
   rule/fact/neither routing triage that makes it actionable.
2. **A transcription correction:** the four-trigger abstention list at `00_task.md:111`
   ("a section heading… states a goal rather than a condition… an example… not
   expressible as rules") is licensed by **no sentence** in `03_pipeline.md`, whose
   abstention section says only that a model which cannot faithfully translate should say
   so with a reason. Two of those four triggers actively push descriptive content toward
   abstention rather than toward `ontology`.

Because arm B carries both, a positive result is attributable to **the block**, not to the
one sentence. A follow-up that separates them is out of scope and out of budget here.

### Endpoint (mechanical, no seat)

For a target-cohort draw:
- `deontic_hard(draw)` = ≥1 `asserts` entry with status in {`forbid`,`permit`,`oblige`}.
- `routed_ontology(draw)` = not `deontic_hard` **and** ≥1 `ontology` entry.
- `abstained(draw)` = `outcome == "abstained"`.

Primary endpoint: `deontic_hard` rate, arm B vs arm A, on the 8 target clauses.

### Instrument floor

**≥ 17 of 24 arm-A target draws (70%) must be `deontic_hard`.** Historical attempt-1 rate
on this cohort is 8/8 = 100%; 70% leaves room for temperature noise while still giving
Fisher power against a hypothesised arm-B rate near 25%. Below 17/24 → UNTESTABLE, stop.

### Verdicts

- **VALIDATED** — target `deontic_hard` rate falls, Fisher p < 0.05, **and** the shift is
  absorbed by `ontology` rather than by abstention (below), **and** the control cohort
  does not lose its deontic status (below).
- **NULL** — Fisher p ≥ 0.05 on the target cohort.
- **NULL-with-harm** — the target rate falls significantly but a trigger below fires.

### Defect-trading triggers (pre-registered, all mechanical)

1. **Abstention capture**: of the target draws that stopped being `deontic_hard`, fewer
   than half are `routed_ontology` — i.e. the rule buys the number by refusing to
   translate rather than by routing.
2. **Control over-fire**: control-cohort `deontic_hard` rate drops by ≥ 15 percentage
   points, or Fisher p < 0.05 on the control. A rule that also strips duties from
   genuinely normative clauses is strictly worse than the defect it removes.
3. Schema-invalid / unparseable rate rises by ≥ 15 percentage points.

---

## 3. Budget arithmetic, stated before spending

Assembled system prompt: 36,605 chars. Mean (system + user) ≈ 9,699 tokens; the forced
JSON schema adds 3,608 tokens → ≈ 13,307 input tokens per call. Prices from the config:
$0.14/Mtok in, $0.28/Mtok out; cached input **not** claimed.

- input: 13,307 / 1e6 × $0.14 = **$0.00186** per call
- output, worst case at the full `max_tokens` 4096: 4096 / 1e6 × $0.28 = **$0.00115**
- worst case per call **$0.00301**; realistic (measured 858–1319 out-tokens) ≈ $0.0022

Total 42 + 66 = **108 calls** → worst case **$0.325**, realistic **≈ $0.24**. Both under
the authorised $0.40. Arm A alone (54 calls) is at most $0.163.

The driver refuses to start if the printed worst-case estimate exceeds $0.40, and aborts
mid-run if measured spend exceeds $0.38.

## 4. Things this study will NOT do

- Not report a point estimate without its Wilson interval and its per-clause breakdown.
- Not treat "arm B removed the defect" as a win when a defect-trading trigger fired.
- Not re-cut a cohort, a floor, or a trigger after seeing a result. Any change is an
  appended, timestamped amendment that says what was already known when it was written.
- Not file either change on the strength of 3 draws per cell alone; the recommendation
  will say what a filing-grade replication would need.

---

## CLOSING NOTE — appended 2026-08-15 after arm A, before any arm-B call

Arm A drawn: 54 calls, $0.0895 measured. **Both instrument floors missed.**

- EXP1: 3/21 vs floor 8/21 → **UNTESTABLE-WITH-THIS-INSTRUMENT**.
- EXP2: 10/24 vs floor 17/24 → **UNTESTABLE-WITH-THIS-INSTRUMENT**.

Per §2, arm B was **not sent** and no further money was spent. $0.3105 of the $0.40
authorisation is unspent. Results in `RESULTS.md`.

No floor, cohort or trigger in this file was revised. The post-hoc observation that EXP2
retains usable power at its observed arm-A rate is recorded in `RESULTS.md` as grounds for
a NEW pre-registration, not as an amendment to this one.
