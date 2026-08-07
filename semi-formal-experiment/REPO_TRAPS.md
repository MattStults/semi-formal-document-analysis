# Repo traps — things a careful reader gets wrong

Verified 2026-08-06. Every entry is a place where the **repo itself** points at a wrong answer:
a stale docstring, a half-quoted constant, a field whose name suggests the opposite of what it
means. Each was reached by honest inference from the code and each was wrong.

This file exists so the next reader does not re-derive them. It is not a changelog and not an
apology; if an entry ever stops being a trap — the stale text is fixed at source — delete it.

**How to use:** before asserting anything on this list, check the named file and line.

---

## 1. `source: "definition"` describes the QUERY side, not the document side

`behavior_atoms.json` has `source: "definition"` on all 65 atoms. This looks like the document
annotation is derived from behaviours, i.e. that the corpus is not behaviour-agnostic.

**It is not.** That field describes the *behaviour* artifact. The document side is annotated once,
independently: `annotate.py` — *"**Behaviour-agnostic** clause annotation: 593 clauses → a reusable
atom index… The spec is annotated ONCE; behaviour queries are then answered offline and instantly."*

⇒ The corpus/query split (north star C1) is **already satisfied**.

## 2. The noise floor is `0.0316–0.037` — and `combined.py` quotes only half of it

`combined.py:305` quotes the 2000-resample half (`0.035–0.037`). The live constant is the full
range: `breadth_filter.py:190` is literally `NOISE_FLOOR = (0.0316, 0.037)`, and
`test_breadth_filter.py:354` asserts **both** endpoints appear in the report.

Source, `HANDOFF.md:1046-1051`: two agents derived 0.0316 at 1000 resamples / 9 cells and
0.0350–0.0357 at 2000.

⇒ Quoting `0.035–0.037` makes results look weaker than the record supports. `V1@any − B = +0.0317`
**straddles the band** — it clears 0.0316 by 0.0001 and misses 0.037. Do not call it "clears."

## 3. `section.py`'s −0.143 is retracted, but still asserted live in two other places

`predict()`'s docstring: *"[RETRACTED: said 'THIS LOSES, measured −0.143'. That was measured under
the inherited `act_match`. At the no-choice `any_atom` this module is the **best single compliant
predictor** measured]"*.

Two other sites in the same file still state −0.143 as live. **The repo is self-contradictory
here.** Do not propagate one side silently.

**Split the claim — it holds for ranking, not for decision:**
- **Ranking:** section is the best single compliant *ranker* (AUC 0.7427 vs structural 0.6475).
- **Decision:** at `any_atom`, section election still **loses** to the per-clause operator
  (+0.258 vs +0.293); `Q` (section alone) is the lowest compliant variant at 0.1984.
- The retracted −0.143 concerned elect-and-distribute under `act_match` and **has never been
  re-measured at `any_atom` as a decision rule.**

## 4. The section partition is INERT — the gain is the election RANKING

The intuitive reading is that grouping clauses into sections is what earns the section channel's
gain, and that the ranking is incidental. **Both halves are backwards.**

`HANDOFF.md:1141-1145`: the size-matched control reproduces exactly (+0.2431) but **cannot come out
any other way** — sd across 200 randomisations is 0.0021. The decisive control was never run until
later: random **whole sections**, size-matched, score **+0.2406** — no better than random clauses.

⇒ **The partition is inert. The gain is the election ranking**, computed from typed atoms already
in the core. Any claim of the form "the gain is the partition" is retracted at source.

## 5. `readback.py`'s three measures are LLM-judged

`readback.py:45` — *"Step 2, three measures, judged by **a cheap model** against the SOURCE
CLAUSE."* The phrase "no model" in that module scopes to `render()` only.

⇒ `faithful` / `sufficient` / `discriminable` are **all model-judged** (`_call`,
`client.complete_envelope`, `--provider`). The harness's core quality signal is model judgment
checked against model judgment, so **A-6 is load-bearing**, not minor.

## 6. No inter-judge kappa exists in this repo

**No `.py` computes one** (verified). Any figure of the form "the panel's inter-judge kappa is
0.39–0.50" is unsourced — it conflates an n=5 qualitative aside in `HUMAN_VS_MODEL_JUDGES.md` with
κ = 0.42 from an external paper (Zhang et al., arXiv:2510.07686) quoted in `litreview.md`.

⇒ Measure it or drop it. An agreement claim without a kappa is not a result.

## 7. Dropping the query norm is NOT order-equivalent for this scorer

Tempting: *"for a fixed query `|q|` is constant, so ranking by `dot(q,c)/|c|` is order-equivalent
to cosine — no `sqrt` needed."* **False here.**

The score is an **additive mix of four channels** (`raw = 1.0·lex + 0.6·atom + 0.45·section`,
`relevance.py:714-717`). Dropping `1/|q|` scales the **lex channel only**:
`raw' = |q|·lex + 0.6·atom + 0.45·section ≠ |q|·raw`. Ordering is not preserved, and Otsu then cuts
a different distribution.

⇒ Order-equivalence holds only for a *pure* cosine ranking. The query norm must be carried as a
fixed-point constant in any re-encoding.

## 8. Otsu cuts the SCORE distribution, not the rank distribution

`relevance.py:806-808`: `vals = [s for _, s in scored if s > 0]`. Positives only.

⇒ Writing `otsu(rank distribution)` sends a porter to histogram the wrong population. The
zero-mass exclusion matters: a large zero mass would move the cut entirely.

## 9. The gap attribution has SIX terms, two of them negative

Full line, +0.278 → +0.583:
calibration **+0.118** · per-atom re-weighting **+0.141** (label-free reachable: +0.009) ·
section block **+0.118** · lex+section drop **−0.039** · supervised's own calibration cost **−0.034**.

⇒ Dropping the negatives sums to 0.655 and overstates available headroom by ~0.07.
Any "~+0.537" figure uses only the first three terms; the two are not interchangeable and neither
is authoritative.

## 10. `+0.537` vs `+0.404` is not an open conflict — they agree

The gap components are **in-cell** (they include the judge-specific share); the cross-judge arm is
what survives **disjoint label sources**. The measured deflator is 68–69%:

**0.69 × 0.583 = 0.402 ≈ +0.404.** They reconcile exactly.

⇒ Recording this as unresolved makes the elicitation route look ~0.13 MCC more promising than the
evidence supports.

## 11. The oracle-cut spread is n=3, not "closed by proof"

Score distributions near-identical (mean 0.16–0.19, sd 0.14–0.18) while optimal cuts differ by
**0.40**. The mechanism argument is general; **the 0.40 spread is three points** — in a repo whose
§2.1 documents an n=3 reading inverting at n=9.

⇒ State as *closed on the evidence available, at n=3*. The n=9 re-derivation is free.

## 12. A `✅` header licenses only the claims it names

Section-level ✅ marks created a silent third state: unmarked numeric claims inside a ✅ section
were indistinguishable from checked ones. Adversarial review found errors **clustered in ✅
sections**, precisely because the mark was doing work no one had done per-claim.

⇒ **Any unmarked numeric claim is ⚠️ by default, whatever the header says.**

---

## Standing lesson

Every entry above was produced by inferring a fact from code structure and asserting it without
running the cheap check that would have falsified it. Claims marked ⚠️ *inferred* held up; claims
marked ✅ *verified* were where the errors were.

**Before asserting a repo fact: run the check, or mark it inferred.**
