# RESULTS — both experiments closed UNTESTABLE at the instrument check

Written 2026-08-15, after arm A and **before any arm-B call**. Reported against
`PREREG.md` exactly as that file was written. Raw per-draw scores in `scored.json`,
raw responses in `draws/`, frozen printout in `RESULTS_armA.txt`.

**Spend: $0.0895 measured, 54 calls. Authorised $0.40. Arm B was NOT sent — protocol
rule 1 fired on both experiments.** Remaining authorisation unspent: $0.3105.

---

## Prompts (both arms assembled, sha256 of the full system block)

| | sha256 | chars | diff vs arm A |
|---|---|---|---|
| arm A (stock) | `5ff9daf7fe58845fff0819eb990d9bba2723eda545449410a4d2d02e4a1e2a58` | 36,605 | — |
| arm B, D1 | `444be5e44019decb82ec1b636695b3bcbee5cb44cd72a8508e17b859c59302d4` | 37,147 | 1 hunk, +7 / −0 |
| arm B, D2 | `9a10916219fe3e128d6828cc0c3bfb1eff1a607c42e7861cc98ee1dd85689cd7` | 37,680 | 1 hunk, +22 / −4 |

Full diffs: `system_diff_d1.txt`, `system_diff_d2.txt`. Both are a single hunk containing
only the named edit. No guard-watched file was touched; arm B reads copies under
`promptsB_d1/` and `promptsB_d2/` via `config_arm_b_d1.json` / `config_arm_b_d2.json`.

### Arm-B wording, D1 — `10_output_format.md`, inserted after the `Status` paragraph

> ⛔ **The act in a `prefer` entry is the act TO DO.** `prefer` names what the clause wants
> done, never what it warns against. `Status` has no negative pole, so `prefer` attached to
> the disfavoured act states the opposite of the clause. A clause that says *"avoid X"*, or
> that marks X as a bad example, is encoded by naming the **avoidance** as the act —
> `prefer avoid_x(R)`, `prefer minimize_x(R)`, `prefer respond_without_x(R)` — never
> `prefer x(R)`. If your read-back would have to say the act is dispreferred, you have
> named the wrong act.

### Arm-B wording, D2 — `00_task.md`, replacing the "Abstention is a real answer" section

> ## Where the clause goes: rule, fact, or neither
>
> Before you choose a status, decide what kind of claim this clause makes. There are three
> destinations and they are not interchangeable.
>
> - **A rule** — it tells some actor what they must, may, must not, or should prefer to do.
>   Give it a status in `asserts`.
> - **A fact** — it states that something IS the case, and imposes no requirement on
>   anyone's conduct. What the document covers and how it is organised, what an
>   organisation values or aims at, what a message or a field contains, what a term means.
>   It belongs in the **ontology** block, with `concepts` for the names it needs. **Never
>   give a fact a deontic status.** *"OpenAI is committed to safeguarding privacy"* and
>   *"a system message will list the available tools"* say what is so, not what anyone must
>   do; writing either as `oblige` puts a duty into the corpus that the document never
>   states, and no later check can tell it apart from a duty the document does state.
> - **Neither** — it has no propositional content that can be recorded at all. Abstain.
>
> A statement of what the document or its author *aims at* is a fact, not a rule, unless it
> also tells an actor to do something.
>
> ## Abstention is a real answer
>
> If you cannot translate this clause faithfully, **abstain and give the reason**. …

---

## EXPERIMENT 1 — D1(a) prefer polarity: **UNTESTABLE-WITH-THIS-INSTRUMENT**

Pre-registered floor: **≥ 8/21 arm-A draws must trip `checks.polarity_mismatches`.**

| measure (arm A, 21 draws over the 7 flagged clauses) | |
|---|---|
| **polarity_mismatch** | **3/21 = 14.3% [5.0, 34.6]** — floor 8/21 **MISSED** |
| draws emitting ≥1 `prefer` at all | 14/21 = 66.7% |
| inversion *conditional* on a `prefer` being emitted | 3/14 = 21.4% [7.6, 47.6] |
| abstained | 0/21 |
| unparsed / schema-invalid | 0/21 |

Per clause (arm A, 3 draws each): `l1707_1973_n006` 1/3, `l1974_2125_n019` 1/3,
`l2405_2473_n001` 1/3; `l1108_1367_n027`, `l1_170_n053`, `l3954_4251_n010`,
`l4251_4571_n029` all **0/3**. Four of the seven clauses that the detector flagged on disk
did not reproduce the defect once in three fresh draws.

**Why this is untestable and not merely a low rate.** At arm A = 3/21, even a *perfect*
arm B — 0/21, the defect eliminated outright — gives Fisher two-sided **p = 0.23**. The
design as pre-registered could not have returned a significant result no matter what arm B
did. Spending on arm B would have bought a guaranteed non-answer. This is the case the
instrument-check rule exists to catch.

## EXPERIMENT 2 — D2 fact-as-obligation: **UNTESTABLE-WITH-THIS-INSTRUMENT**

Pre-registered floor: **≥ 17/24 arm-A target draws must be `deontic_hard`.**

| measure (arm A) | target cohort, 24 draws | control cohort, 9 draws |
|---|---|---|
| **deontic_hard** | **10/24 = 41.7% [24.5, 61.2]** — floor 17/24 **MISSED** | 9/9 = 100% [70.1, 100] |
| routed_ontology | 14/24 = 58.3% [38.8, 75.5] | — |
| abstained | 0/24 | 0/9 |
| unparsed | 0/24 | 0/9 |

Per clause (arm A, 3 draws each): `l1108_1368_n004` 3/3, `l171_426_n041` 3/3,
`l1_170_n005` 2/3, `l796_1000_n034` 2/3; `l171_426_n016`, `l1_170_n022`, `l1_170_n032`,
`l1_170_n081` all **0/3**. The historical record for this cohort was **8/8 deontic at
attempt-1**; on a fresh draw with byte-identical prompt bytes it is 10/24.

The control cohort behaved exactly as designed — 9/9 deontic — which confirms the endpoint
measure itself is sound and discriminating. The instrument failure is in the target
cohort's reproducibility, not in the metric.

---

## The finding that is actually load-bearing

**Both "defects" were measured by selecting clauses on a single draw's outcome, and
neither survives re-drawing with the same prompt.**

Prompt drift is ruled out: the assembled system block has been byte-identical
(`5ff9daf7…`, 36,605 chars) across every run from `20260810-225427` onward, including all
five runs that produced the flagged polarity entries and the runs behind the routing
study. Nothing was fixed in between. The difference is per-draw stochasticity at
temperature 0.2.

What that changes:

- The **corpus-level prevalence figures stand** — 9 flagged polarity entries and ~6% of
  modules asserting unstated obligations are honest censuses of what is on disk, and the
  bad artifacts are really bad.
- The **per-clause attributions do not**. "These 7 clauses have the polarity defect" and
  "these 8 clauses route a fact to a duty" are not properties of those clauses; they are
  coin flips that happened to land that way once. A cohort built from them regresses hard.
- Consequently **any A/B test cohort selected this way is mis-powered by construction**,
  and this will bite every future prompt experiment in this project that recruits from a
  single-draw census. That is the transferable lesson here.

Secondary, free, and worth recording: on the D1 clauses arm A emitted **no `prefer` entry
at all in 7/21 draws** and emitted a hard `forbid`/`permit`/`oblige` in 8/21. So on exactly
the clauses where the design says a comparative belongs, the stock prompt reaches for
`prefer` only two-thirds of the time. The polarity inversion is a *sub-case* of a broader
instability in status selection, and fixing polarity alone would not address it.

---

## Recommendation

**File neither change on this evidence.** Neither is refuted — both are untested. The
arm-B wordings above are reasonable and cost nothing to keep on the shelf; what is missing
is a design that can measure them.

A filing-grade replication, costed at the measured $0.00166/call:

| | design | calls | cost |
|---|---|---|---|
| **D2 (do this one)** | same 8-clause target + 3-clause control, **12 draws per cell** instead of 3 | 132 | **$0.22** |
| D1 | needs ≥ 40 draws/arm against a perfect arm B; the cohort must first be **re-recruited by drawing the whole corpus twice and keeping clauses that trip the detector both times** | ≥ 80 + recruitment | ≥ $0.14 + recruitment |

Grounds for the split: at the *measured* arm-A rate of 41.7%, 24 draws per arm already
detects a drop to ≤ 3/24 (p = 0.049) — so D2 is close to testable and a modest increase in
draws makes it comfortably so. D1 at 14.3% is not close, and no amount of draws fixes a
cohort whose members mostly do not have the defect; it needs re-recruitment first.

⚠️ **The floors in `PREREG.md` were not amended after seeing these numbers, and must not
be.** The observation that D2 retains usable power at 10/24 is stated here as a reason to
*re-run under a new pre-registration*, not as grounds to continue the run that failed its
own gate.

## Confound recorded, for whoever picks this up

The D2 arm-B block bundles the one-sentence design change (*"never give a fact a deontic
status"*) with a transcription correction (deleting the four-trigger abstention list at
`00_task.md:111`, which no sentence in `03_pipeline.md` licenses). A positive result from
this block would be attributable to the block, not the sentence. Separating them costs a
third arm.
