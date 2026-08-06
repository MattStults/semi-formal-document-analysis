# RELEVANCE_QUALITY_READ — where the tool stands, and whether the ladder can close the gap

**Measured 2026-08-05/06 in a clean detached worktree at `5a2973f` (main's head when
measurement began; main has since advanced — see §7). Worktree removed after measurement;
main checkout never written to.**

## Headline answer, in three sentences

The tool sits at **+0.3088 mean MCC** against a **+0.5555** frontier-panel bar on the 3 DEV
cells over the true 589-passage universe — exactly the README's +0.309 — and **the six closed
cycles since 2026-08-04 have moved that number by +0.0003 in total**, an order of magnitude
below the project's own noise floor (0.0316–0.037); every gain in the record came from
swapping annotation/atom artifacts, not from a cycle. Under an **oracle** assumption that
every remaining planned cycle lands perfectly with zero collateral, the whole live ladder
closes **28–42%** of the 0.247 gap (to +0.377…+0.412), and the honest, evidence-supported
figure is nearer **15%** (+0.347) — because S5 was measured to produce **zero flips**, S6's
own Tier-1 review puts 14–15 of its 26 targets out of bounds, S3b reaches only 79/155 of its
class, and the 60-case threshold class has **no mechanical owner by design**. The ladder
cannot close this gap; the project has already produced its answer, and the answer is that
the measurement instruments and the process — not the relevance scorer — are the deliverable.

---

## 1. The current number

Config, resolved from `cycles/CYCLE_LOG.jsonl` (latest closed-KEEP =
`join-integrity-v2-2026-08-04`, not a statically named tag):

| input | value |
|---|---|
| annotations | `annotations_ext_v1_merged.json` (`1ea7fe9d…`) |
| behaviour atoms | `behavior_atoms_audit_v1.json` (`54056241…`) |
| clauses | `modelspec_clauses.json` (`c6be91a0…`) |
| overlay | `overlay_empty.json` (`3f3adca9…`) |
| queries | `behaviours_query.json` (`48dbd8fb…`) |
| thresholds | `thresholds_frozen.json` (`60d1273a…`) |
| pricing_version | `1.2` · threshold_rule `otsu` (frozen values used) |

**Verified reconstructable**: rebuilding this snapshot from the tree gives an object identical
apart from `tag`, and identical predicted sets (95 / 73 / 146 clauses). The census
`audit_dossiers/ext_v1_merged__audit_v1/` matches this configuration exactly — **0 of 294
census cases disagree with head-of-main's prediction state.**

**TRUE universe (589 passages), pair-consensus golds, mean over the three held-out-judge
targets:**

| behaviour | tool MCC | judge MCC (mean LOO) | gap | tool P / R (mean) |
|---|---:|---:|---:|---|
| helpfulness | **+0.249** | +0.571 | 0.321 | 0.35 / 0.47 |
| harm-avoidance-to-third-parties | **+0.366** | +0.615 | 0.249 | 0.65 / 0.34 |
| avoiding-over-and-under-caution | **+0.311** | +0.481 | 0.170 | 0.23 / 0.56 |
| **pooled mean** | **+0.3088** | **+0.5555** | **+0.2467** | |

Mean confusion per target: caution TP 22 / FP 73 / FN 18; harm TP 47 / FP 26 / FN 92;
helpfulness TP 50 / FP 93 / FN 57. The two failure shapes are different — caution and
helpfulness over-fire, harm under-fires badly (recall 34%).

**Reference points re-derived, not assumed:**

| README (2026-08-04) | reproduces? |
|---|---|
| frontier panel +0.555 | ✅ +0.5555 |
| tool audited selection +0.309 | ✅ +0.3088 |
| first shipped config +0.28 | ✅ +0.2778 (`baseline-2026-08-03`) |
| bag-of-words control +0.19 | ❌ **does not reproduce** |

⚠️ **README correction.** `benchmark.py --control` on the 3 DEV cells / true universe gives
**+0.096 / +0.200 / +0.027 = +0.108 mean** (published universe +0.106). The +0.19 in the
README is `HANDOFF.md`'s "lexical control +0.185", which is a **9-behaviour, 5-atom-draw**
figure sitting in a table of 3-DEV-cell numbers. The error is in the tool's favour to
correct: the real lift over bag-of-words is ~2.9×, not ~1.6×.

---

## 2. The trajectory

Every frozen snapshot, scored through `benchmark.evaluate()` — the same code path as the
headline table — on its own frozen predicted sets.

| # | snapshot (cycle) | pooled MCC | Δ prev | config family | comparable to head? |
|---|---|---:|---:|---|---|
| 1 | `baseline-2026-08-03` | +0.2778 | — | b8 ann + b8 atoms, rule-derived cut | ✗ different artifacts |
| 2 | `containment-v0` (cycle 1, 2 edges) | +0.2897 | +0.0119 | b8 + `containment.json` | ✗ **unreconstructable** (overlay bytes gone) |
| 3 | `containment-v1-pricing` (cycle 2) | +0.2810 | −0.0087 | b8 + pricing 1.0 | ✗ **replays but disagrees** |
| 4 | `containment-v1.1-kindinherit` (cycle 3) | +0.2897 | +0.0087 | b8 + pricing 1.1 | ✗ different artifacts |
| 5 | `ext-v1` | +0.2365 | −0.0532 | ext_v1 ann + **ext_v1** atoms | ✗ pre-audit atom selection |
| 6 | `baseline-2026-08-04-auditv1` | **+0.3085** | **+0.0720** | ext_v1 ann + **audit_v1** atoms | ~ (cut not yet frozen) |
| 7 | `versioned-cut-2026-08-04` (KEEP, noop) | +0.3085 | 0.0000 | + versioned cut | ✓ |
| 8 | `chain-repair-2026-08-04` (KEEP) | +0.3085 | 0.0000 | + frozen thresholds | ✓ |
| 9 | `decoration-blind-join-2026-08-04` (S1, KEEP) | +0.3088 | **+0.0003** | + join 1.2, `overlay_empty` | ✓ |
| 10 | `patient-backfill-2026-08-04` (S2, KEEP) | +0.3088 | 0.0000 | + 264 chains | ✓ |
| 11 | `patient-pricing-2026-08-04` (S3, **REVERT**) | +0.3148 | +0.0060 | pricing 2.0 | ✓ (reverted) |
| 12 | **`join-integrity-v2-2026-08-04` (head)** | **+0.3088** | −0.0060 | head config | ✓ |

**The shape of the curve.** Flat, with one step. The step is #5→#6: **+0.072 from
re-selecting the behaviour-atom artifact** (`select_audit` v2 → `behavior_atoms_audit_v1.json`)
— an *instrument* change, not a mechanism change. From #6 onward, six logged cycles produced a
**cumulative +0.0003**. The project's own re-derived noise floor is **0.0316–0.037**
(`HANDOFF.md`, two independent agents, 1000–2000 resamples). Every post-#6 movement,
including the reverted S3's +0.006, is at least 5× below that floor. **On the metric, the last
six cycles are indistinguishable from zero.**

**Comparability warnings, checked rather than assumed:**

* **`verify_reconstruction.py` does not exist on main.** It is `OUTSTANDING_WORK.md` item D2,
  still open (it exists only on the unmerged index-builder branch). A 40-line stand-in was
  written for this report.
* **7 of 12 snapshots cannot be rebuilt from head-of-main**: `ext-v1`,
  `baseline-…-auditv1`, `chain-repair`, `versioned-cut`, `decoration-blind-join`,
  `patient-pricing` record input SHAs that no longer match the tree (S2's backfill rewrote the
  annotations; S3's revert rewrote `behaviours_query.json`); `containment-v0`'s overlay bytes
  were destroyed by an in-place edit. Their *frozen predicted sets* remain valid evidence of
  what the tool said; their *configs* are not re-derivable.
* **`containment-v1-pricing` replays and disagrees, confirmed.** Replaying it yields 118
  predicted clauses on harm-avoidance where the frozen snapshot has 114 — `m0216/m0217/m0218/
  m0220` return, because the replay runs `PRICING_VERSION 1.2` and the 1.0-era code **never
  entered version control**. Read row 3 as a historical artifact only.
* Rows 1–5 use a different annotation/atom pairing than head and are not like-for-like.

---

## 3. The gap decomposition, and the upper bound

### 3.1 Method and its honest limitation

Each census dossier names a passage and a direction. "Fixing" a case = removing that passage
from the predicted set (FP) or adding it (FN), then recomputing the real headline MCC. This is
an **oracle** edit: perfect landing, zero collateral flips. Everything below is therefore an
upper bound. Where a class's reachable subset is smaller than the class, random subsets of the
stated reachable size are drawn (200–300 Monte-Carlo trials) and the mean reported — **an
estimate, labelled as one**, because no artifact enumerates *which* 79 of the 155 S3b reaches.

⚠️ **The census does not enumerate the metric's error mass.** The census's own gold is
`summed panel score ≥ 5`; the headline MCC uses pair-consensus golds. Measured: **447 passages
are a disagreement under at least one pair-gold; the 294-case census covers 256 of them —
57%.** Harm-avoidance is worst: 91 of its 153 disagreement passages are outside the census
entirely. **43% of the error the metric is scored on has never had a cause attributed to it,
and no ladder cycle owns it.** This is the single most important structural caveat in this
report.

### 3.2 Per-class arithmetic

| census class | n (%) | oracle ceiling if the WHOLE class is fixed | owner | measured/reviewed reach | reach as % of census |
|---|---:|---:|---|---|---:|
| `fp_promiscuous_atom` | 155 (52.7%) | +0.3436 (Δ **+0.0348**) | S3b | **79/155 (51%)**, measured structurally. ~30 of the residue are helpfulness-domain answer-quality atoms with **no harm and no protection in them**. D5's "+17 from D5b" is **superseded**: the act-atom ceiling measured **~2 (range 1–4)**, so best case ~81/155. | **27%** |
| `fp_threshold_drift` | 59 (20.1%) | +0.3139 (Δ **+0.0052**) | **nobody, by design** | P3 is DISCLOSURE ONLY — "nothing mechanical may consume these verdicts". Only **20 (33%)** were judged 'not-needed'; 39 are defensible. Re-cutting needs a cycle that is not on the ladder. | **0%** |
| `fp_section_prior` | 30 (10.2%) | +0.3278 (Δ **+0.0190**) | S4 | **24/30** — the design's own forecast says the 6 with atom > 0 are **not** expected to move, and that `fn_*` classes may **grow**. | **8%** |
| `fn_family_absent_from_vocabulary` | 26 (8.8%) | +0.3710 (Δ **+0.0622**) | S6 | **Contested.** Its Tier-1 review: "a mechanical recomputation puts **14 of the 26** target dossiers on the side the design says it must not touch". Realistic reach ≈ **11–12**. | **4%** |
| `fn_names_cannot_meet` | 19 (6.5%) | +0.3715 (Δ **+0.0627**) | S5 → S7 | **REFUTED BY MEASUREMENT.** S5 produces **exactly zero flips**; forcing 2.5× credit still yields 0. S7 widening is gated on S5. | **0% today** |
| `fp_join_artifact` | 2 (0.7%) | +0.3105 | P1 | 2/2 | 0.7% |
| `unexplained_escalate` | 2 (0.7%) | +0.3138 | P2 | 2/2 | 0.7% |
| `fn_threshold` | 1 (0.3%) | +0.3114 | P3 (disclosure) | 0 | 0% |

### 3.3 The composed bound

| scenario | cases | pooled MCC | Δ | gap closed |
|---|---:|---:|---:|---:|
| head-of-main | — | +0.3088 | — | — |
| A. S3b alone (79/155) | 79 | +0.3188 | +0.0100 | 4.0% |
| B. + S4 (24/30) | 103 | +0.3389 | +0.0301 | 12.2% |
| **C. + P1/P2 — everything with a MEASURED reach** | **107** | **+0.3467** | **+0.0379** | **15.4%** |
| H. C + S6 at the 12/26 its own review leaves it | 119 | +0.3771 | +0.0683 | 27.7% |
| **D. C + S6 at its full nominal 26, zero collateral** | **133** | **+0.4116** | **+0.1028** | **41.7%** |
| E. D + S5/S7 (19) — **refuted, S5 measures 0 flips** | 152 | +0.4756 | +0.1668 | 67.6% |
| F. D + a threshold re-cut nobody owns (20/60) | 153 | +0.4183 | +0.1095 | 44.4% |
| G. every one of the 294 census cases, oracle | 294 | +0.6400 | +0.3312 | 134% |

> **THE DEFENSIBLE UPPER BOUND: +0.41 (scenario D), closing ≈ 42% of the gap. It is not
> reachable by anything currently believed, and the honest central estimate is scenario C/H:
> +0.35 to +0.38, closing 15–28%.**

**What the bound rests on.** Scenario D assumes: (i) S3b lands 79 of 155 correctly, when its
reach numbers are *structural* — whether the mechanism can see the atom, not whether the
attribution will be right; (ii) S4 lands 24 of 30 with none of the FN growth its own design
forecasts; (iii) S6 recovers all 26 FNs including the 14–15 its own Tier-1 rules out of bounds,
**and adds no new false positives at all**; (iv) zero collateral anywhere. Point (iii) is where
the bound is most brittle: **65% of scenario D's gain is S6's 26 FNs.** Priced with collateral
(r new FPs per FN recovered — the expected behaviour of vocabulary widening, which can only
*add* matches):

| r | pooled | Δ | gap closed |
|---:|---:|---:|---:|
| 0 (oracle) | +0.4120 | +0.1032 | 41.8% |
| 1 | +0.3811 | +0.0723 | 29.3% |
| 2 | +0.3583 | +0.0495 | 20.1% |
| 3 | +0.3406 | +0.0318 | 12.9% |
| 5 | +0.3110 | +0.0022 | 0.9% |

At three collateral FPs per FN recovered — modest for a vocabulary widening on a corpus where
the tool already runs at 23–65% precision — S6 delivers less than the difference between B
and C.

**The empirical prior is worse than any of this.** The last six cycles delivered +0.0003
against class ceilings of comparable nominal size. The realised-to-oracle ratio of the
executed ladder so far is, to three decimals, zero.

---

## 4. The divergence question, taken literally

**The record exists.** `expert_salience.json` (2026-08-04, the first and only human-expert
relevance signal in the project; 4 anchors). The expert's verdict:

> "The panel's failure mode is SALIENCE FLATTENING: it over-flags, treating many related
> passages as equally relevant, and fails to distinguish THE core passage. *'Missing nuance
> and specificity but the tool is very useful and efficient to find relevant parts and
> compare.'* Endorsed use case: interest groups checking whether and how their topics are
> covered."

**Read carefully, because it does not say what a reader hoping for good news wants.** The
complaint is about **ranking/salience**, an axis the panel — a binary instrument — cannot
express and **which MCC does not measure**. The expert did not find the panel's binary
relevance calls wrong. So this evidence does **not** license discounting the +0.247 gap. What
it does say is that the axis the endorsed use case needs is *a different axis from the one the
ladder has been spent on*. Three of the four anchors are on the sealed constitution; the one
openai anchor is on a **generalization-set behaviour, consumable exactly once at S9**. No
anchor evaluates a DEV cell, so the salience claim is currently unmeasured.

**The mechanical proxy, per class:**

| class | n | side=`panel` (tool wrong) | side=`tool` (panel arguably wrong) | `both_defensible` |
|---|---:|---:|---:|---:|
| `fp_promiscuous_atom` | 155 | 121 (78%) | 21 (14%) | 13 |
| `fp_threshold_drift` | 59 | 45 (76%) | 0 | 14 |
| `fp_section_prior` | 30 | 26 (87%) | 4 (13%) | 0 |
| `fn_family_absent_from_vocabulary` | 26 | 14 (54%) | 12 (46%) | 0 |
| `fn_names_cannot_meet` | 19 | 15 (79%) | 4 (21%) | 0 |
| others | 5 | 5 (100%) | 0 | 0 |
| **total** | **294** | **226 (76.9%)** | **41 (13.9%)** | **27 (9.2%)** |

⚠️ **But the `side` field will not bear this weight.** Cross-tabulated by behaviour, it is
**perfectly block-segregated**:

| behaviour (seat run) | `panel` | `tool` | `both_defensible` |
|---|---:|---:|---:|
| helpfulness (129 cases) | **129** | 0 | 0 |
| avoiding-over-and-under-caution (85) | 58 | **0** | **27** |
| harm-avoidance-to-third-parties (80) | 39 | **41** | **0** |

Not one of the three seat runs used all three values, and each used a *different* two. Zero
mixing across 294 independent judgments is not what per-case judgment looks like — it is the
signature of a per-run stance, the same seat-calibration defect P3's drift pass diagnosed.
Blind validation of the census is **n=4**. **Conclusion: the census's cause attribution is
usable; its `side` field is confounded with which run produced it and must not be quoted as a
panel-quality measurement without a fresh, cross-behaviour-calibrated seat pass.**

For completeness, the (uncertain) magnitude if `side` were taken at face value:

| gold | tool | judges | gap |
|---|---:|---:|---:|
| as published | +0.3088 | +0.5555 | +0.2467 |
| corrected on the 41 `side=tool` | +0.3614 | +0.5368 | +0.1754 |
| + the 27 `both_defensible` | +0.4381 | +0.5506 | +0.1126 |

That would say **more than half the gap is panel error**. Do not act on it — the 41 are all one
behaviour and the 27 all another, so this table measures a seat's per-run stance as much as
anything about the panel. **It is the highest-value cheap follow-up on the board**: one
recalibrated cross-behaviour `side` pass would either legitimise a ~0.11–0.18 correction to
the bar or kill the hypothesis.

---

## 5. Recommendation

**The ladder cannot close this gap, and the project has already produced its answer. Stop
treating the +0.555 bar as the objective.**

Grounds, in order of weight:

1. **Six closed cycles, +0.0003.** No measurable movement, against a noise floor 100× larger.
   The only real gain (+0.072) came from re-selecting an artifact — an instrument improvement.
2. **The bound is 42% under assumptions already refuted.** S5's lever measures zero. S6's own
   Tier-1 disqualifies 14–15 of its 26 targets and is the source of 65% of the bound's gain.
   Strip those and the ladder is worth **+0.038 to +0.068** — inside, or barely outside, the
   noise floor.
3. **43% of the metric's error mass is not in the census at all.** Every planned cycle is
   aimed at the 57% that is. Harm-avoidance — 92 mean FNs — is where the census is thinnest.
4. **The threshold class (60 cases, 20%) has no mechanical owner by design**, and correctly
   so: consuming those verdicts is exactly the panel-fitting the invariants exist to prevent.
5. **The one human-expert signal points elsewhere.** The endorsed use case is ranked
   first-pass auditing, and the failure they named is the panel's, on an axis MCC cannot see.
   The project has an instrument for that axis and has never run it.

**What to do instead, concretely:**

* **Do not spend the S3b budget.** Its measured, oracle, best case is +0.010 — a third of the
  noise floor. Costed honestly it is unfalsifiable.
* **Run the zero-cost, high-information passes first:** the recalibrated cross-behaviour
  census `side` pass (§4) — the only thing that can legitimately move the bar. ⚠️ The salience
  rank-position check is **not** zero-cost in the way it first appears: its only openai anchor
  sits on a generalization-set behaviour, so running it spends part of a one-shot resource.
  That is a project-lead decision, not a free follow-up.
* **Go to S8/S9 sooner.** The generalization question — does the error-class distribution
  transfer to 6 never-consulted behaviours — is answerable on a frozen pipeline, is the
  question "whether transfer even matters" is really about, and is *not* improved by first
  spending three cycles to move MCC by 0.04.
* **Rewrite the headline claim.** "+0.31 against a +0.555 bar" invites the wrong comparison.
  The defensible claims: an offline, auditable, label-free tool at **2.9× the bag-of-words
  control** (+0.309 vs +0.108, not the +0.19 the README states), with a per-answer licensing
  span, on an endorsed first-pass-audit use case whose own quality axis has not been measured.
  That is a real result. Judge replacement is not, and the arithmetic says it will not become
  one.

**Where this might be wrong:** if the 41+27 `side` verdicts survive recalibration, the true bar
is nearer +0.44–+0.53 and scenario D's +0.41 becomes a near-miss rather than a rout. That
single check is worth running before anyone accepts this recommendation.

---

## 6. What a reviewer should independently check

1. The README's **bag-of-words control +0.19** — measured +0.108 on the DEV cells / true
   universe; +0.19 appears to be HANDOFF's 9-behaviour figure in a 3-behaviour table.
2. **Census coverage of the metric's error mass: 256 of 447 (57%)** — the most load-bearing
   new number here, computed from a purpose-written script, not repo tooling.
3. The **`side`-field block structure** (129/0/0, 58/0/27, 39/41/0). If it is an artifact of
   how the three seat runs were briefed, record it as a census defect; if genuine, §4's
   correction table becomes the most important number in this report.
4. The **oracle simulation's assumption** that removing/adding a census passage has no
   collateral effect on other passages.
5. **`verify_reconstruction.py` (D2) is unwritten on main**; the stand-in used here is not a
   reviewed instrument.
6. **The suite does not pass from a clean checkout**:
   `test_ladder.py::test_nothing_here_constructs_a_live_client` fails with `FileNotFoundError`
   because it writes into `smoke_annotate/`, which `.gitignore` excludes. After
   `mkdir smoke_annotate`: 2163 passed, 3 skipped. A real reproducibility defect.

---

## 7. Note on the moving head

Measurement ran at `5a2973f`; main advanced during the session. The only measurement-relevant
code change is `benchmark.py`'s new `mixed_variants` parameter — opt-in, defaulting to `False`,
explicitly "the measured state" — so every number holds at the newer head. Two of the newer
commits are *used* above and strengthen the report: the S5 zero-flip measurement and the S6
14-of-26 finding.

---

## Appendix — reproduction

Setup (worktree removed after use; main checkout never written):

```bash
git -C <repo> worktree add --detach <scratch>/measure-wt 5a2973f
cd <scratch>/measure-wt/semi-formal-experiment
python3 -m venv .venv && .venv/bin/pip install pytest clingo
mkdir -p smoke_annotate                       # see §6 — gitignored, required by test_ladder
.venv/bin/python -m pytest -q                 # 2163 passed, 3 skipped
```

**The current number** (`preds_head.json` = the head snapshot's `predicted` sets):

```bash
.venv/bin/python -c "import json;d=json.load(open('snapshots/join-integrity-v2-2026-08-04.json'));json.dump({k:sorted(v['predicted']) for k,v in d['behaviours'].items()},open('/tmp/preds_head.json','w'))"
.venv/bin/python benchmark.py /tmp/preds_head.json     # headline + universe-delta tables
.venv/bin/python benchmark.py --control                # bag-of-words control
```

**Trajectory** — score every snapshot's frozen predicted sets through `benchmark.evaluate()`,
the same path as the headline table, reporting the mean `mcc_full` over each behaviour's
pair-gold targets.

**Gap decomposition** — oracle edit per census case (FP → discard the passage, FN → add it)
against `B.lift(predicted, clause_joins)`, rescored with `B.mcc(tool, gold, universe)` over
`B.pair_targets(...)`; class subsets drawn 200–300 times where reach < class size; collateral
sensitivity adds `int(r · n_fn)` random currently-unpredicted passages per behaviour.
Sanity assertion printed first: `census/head prediction-state mismatches: 0 of 294`.

**Census cross-tabs:**

```bash
.venv/bin/python -c "
import json,collections,os
C='audit_dossiers/ext_v1_merged__audit_v1'
V={v['dossier_id']:v for v in json.load(open(os.path.join(C,'verdicts_merged.json')))}
c=collections.Counter((json.load(open(os.path.join(C,d+'.json')))['behaviour'],v['side']) for d,v in V.items())
print(sorted(c.items()))"
```

**Constraints honoured:** no network or API calls; `cycle.py` never run; no commit, push, or
write to the main checkout; temporary worktrees removed.
