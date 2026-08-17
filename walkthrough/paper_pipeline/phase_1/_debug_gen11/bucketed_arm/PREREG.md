# PREREG — ARM G: lens-grouped BUCKETS of checks, phrased as PROCEDURES, each turn returning a MODULE

**Signed before the first live call.** Nothing below was edited after any result
was seen; `RESULT.md` records the diff of this file as empty.

---

## 1. THE MECHANISM ARGUMENT THIS ARM TESTS

Two prior arms measured *why* six arms have failed:

* **Arm D** (`selfreview_arm/RESULT.md`): identification **13%**, repair **92%
  conditional on identification**; exactly one of 91 frozen items was identified
  and not repaired. **The bottleneck is diagnosis, not execution.** But D put
  **eleven entries in one message** and asked for eleven verdict lines. This
  project's own procedure doctrine says that above ~10 items at once none are
  applied properly, so D may have measured its own overload.
* **Arm F** (`forced_verdict_arm/RESULT.md`): asked for a verdict per check, it
  returned `applies_and_handled` **102 of 102**, including 17 clauses where the
  polarity check was stamped "handled" on modules containing **zero** `prefer`
  asserts. **Asking this model to judge a check produces a rubber stamp.**

**The design that follows from both: exploit the 92%, avoid the judgement.**
Convert every check from a question into a PROCEDURE that ENUMERATES something
in the module, deliver 2–3 procedures per turn grouped by lens, and make the
deliverable of every turn the MODULE — with **no verdict field anywhere**, so
there is nothing to rubber-stamp and nothing scoreable except the artefact.

## 2. WHAT IS HELD FIXED, AND THE ONE COST-FORCED DEPARTURE

| | arm D | **arm G** |
|---|---|---|
| turn-1 draft | arm A's stored draft, resumed | **identical — arm A's stored draft, resumed** |
| system block | sha256 `3a66c5f5…`, gated | **identical, same gate, refuses otherwise** |
| entries delivered | E1–E11 + 3 anti-rules | **the same E1–E11 + the same 3 anti-rules, verbatim content** |
| delivery | 11 entries, ONE turn | **2–3 entries per turn, FOUR turns, grouped by lens** |
| phrasing | *"Does a gloss restate its name?"* | **"For every entry in `concepts`, write the name with underscores as spaces, then write the gloss; if (2) is (1) with variables inserted…"** |
| deliverable per turn | verdict lines, then a module | **a module, always; no verdict field exists** |
| calls per clause | 2 | **4** |

⛔ **THE ONE DEPARTURE: 9 clauses, not 17.** 17 clauses × 4 buckets prices at
**$0.27 worst case** against a **$0.12** hard cap; it cannot be run. The 9
selected are **exactly the 9 arm D COMPLETED** (`l699_796_n012`,
`l1001_1107_n005`, `l2474_2554_n004`, `l3239_3382_n002`, `l3239_3382_n004`,
`l171_426_n022`, `l1707_1973_n006`, `l3596_3876_n009`, `l4252_4482_n016`),
because the headline comparison is against arm D and a paired comparison needs
D's own sample. ⚠️ **That sample is itself biased**: D's other 8 were lost to a
truncation correlated with reasoning length, i.e. with the clauses whose review
reasoned hardest. Arm G therefore inherits D's selection bias exactly, which is
the right property for the paired contrast and the wrong property for any claim
about the corpus. **Stated here, not discovered later.**

Rejected by name: *"run all 17 with 2 buckets"* — it would confound bucketing
with entry coverage, and there would be no arm-D row to compare against on 8 of
them. *"Run 17 at 4 buckets and stop when the cap bites"* — a sample truncated
by cost is a sample selected by transcript length, which is D's exact bias
compounded.

## 3. ENTRY 5 IS FIXED, NOT EXCLUDED — with the reason

Entry 5 is measured to manufacture vacuous-bodied rules. Arm F rewrote it; the
rewrite fixed F's own quoted cases and **did not generalise** (three new vacuous
bodies appeared elsewhere). Arm D **amended** it with an explicit falsifiability
gate, and the amendment **held at n = 2**: both firings deleted a vacuous rule,
neither created one, and no vacuous body appeared anywhere in D's output.

**Ruling: keep arm D's amendment verbatim, and convert it into a procedural
gate** — `bucket2.md` step 3 requires the model to *write down one concrete case
the proposed new body is FALSE of* before changing any atom, and to leave the
atom alone if it cannot. This is exactly the manipulation the arm is testing
applied to the entry most in need of it.

Rejected by name: **"exclude entry 5"** — it fired twice in D and both firings
were correct, so excluding it would drop a working entry and make the bucket set
non-comparable to D's eleven. **"Adopt arm F's rewrite"** — measured not to
generalise.

## 4. THE BUCKETS

| bucket | lens | entries | anti-rule carried |
|---|---|---|---|
| 1 | is the right CONTENT here | E6 claims-vs-asserts, E3 coined-symbol tracing, E4 outside-the-narrowing | `requires` false alarm |
| 2 | is the LOGICAL FORM right | E11 disjunction, E8 scope, E5 vacuous body / unification | `forbid X(R) :- X(R)` is schema-forced |
| 3 | is the FORCE right | E10 polarity, E7 defeasibility, E2 unless-arms and `closure` | never fix by rewriting the read-back |
| 4 | HYGIENE + the anti-rules | E1 gloss-restates-name, E9 argument order, head-in-own-body | **all three, plus an explicit UNDO sweep over the whole conversation** |

All 11 entries are delivered; none is dropped. The anti-rule most likely to be
tripped by a bucket sits *in* that bucket, and all three are restated in bucket
4 with an instruction to undo earlier violations.

**⚠️ The over-editing guard is in the preamble of EVERY bucket, not just the
first**, because this design's specific risk is churn: *"A turn that changes
nothing is an EXPECTED AND CORRECT outcome… Returning the module byte-identical
to the one you just wrote is a legitimate answer."*

### Which checks could NOT be converted into procedures — pre-declared

Converted cleanly (the enumeration is mechanical and its output is an edit):
**E6, E3, E1, E9, E10, E5**, head-in-own-body.
Converted only PARTLY (the enumeration is mechanical, the decision on each
enumerated item is still a judgement): **E11** (enumerate every "or", then judge
the De Morgan test), **E2** (enumerate every "unless" and every `closure`, then
judge whether the span decides it), **E7** (enumerate hedge words, then judge
whether the span names a defeater).
**NOT CONVERTED: E4 and E8.** "Is every asserted predicate supported by the
narrowed text" and "does each body widen past the span's qualifier" have no
mechanical enumeration whose output is an edit — the two-column comparison in
bucket 1 step 3 and the body-vs-substring table in bucket 2 step 2 are the
closest approximations and both leave the whole decision to judgement. **This
list is itself a finding and is reported as one.**

## 5. MEASUREMENT — the module, never the model's words

⛔ **F's lesson is binding: no number here comes from anything the model says
about a check.** The model returns only modules. Every figure is read off the
returned JSON by me, span-first.

**Denominator: arm D's own frozen per-clause item counts**, taken from D's
RESULT table, which counts the numbered edits in
`ds_opus_loop/out/<id>.feedback_1.md` — written by the Opus critic against these
exact drafts before either arm existed. I did not author them and do not
re-count them: 5, 9, 29, 4, 30, 3, 4, 4, 3 = **91**.

Per clause and per bucket I report: defects present before the bucket, after it,
and **fixed / missed / newly introduced**.

⭐ **What is directly measurable here, and what is inferred.** Arm G has no
identify step, so **repair-rate is MEASURED and identification is INFERRED.**
Arm D measured repair-conditional-on-identification at 92%; if that conditional
holds, `identification ≈ fixed / 0.92`, and since it cannot exceed 1.0 the
fixed-rate is a **lower bound** on identification. The comparison to D's 13%
identification / 12% repair is therefore made on the **repair (fixed) rate**,
where D's number is **12% (11 of 91)** and no inference is needed on either
side.

## 6. PRE-REGISTERED BRANCHES

| branch | fires when |
|---|---|
| **TRANSFER** | ≥ **27 of 91** items fixed (≥30%, ≥2.5× arm D) AND ≤ 2 of 9 modules acquire a conclusion-changing new defect |
| **NULL** | ≤ **18 of 91** fixed (<20%) — bucketing did not move diagnosis, and the argument moves to detectors |
| **PARTIAL** | 19–26 fixed; reported as partial, with the bucket that carried it named |
| **MANUFACTURED HARM (H1)** | ≥ 3 of 9 modules acquire a conclusion-changing defect absent from the turn-1 draft |
| **H2 obey-and-break** | ≥ 1 defect created by correctly obeying a procedure step |
| **OVER-EDITING (H5, new to this design)** | (a) ≥ 3 of 9 modules show a substantive edit in a bucket whose lens the frozen list names no defect for, **or** (b) newly-introduced defects ≥ defects fixed, summed over the four buckets |
| **STASIS-NULL (H6, new)** | ≥ 6 of 9 modules byte-identical across all four buckets — the procedural framing produced no action at all, a different null from D's |
| **H4 anti-rule breach** | ≥ 1 "repair" of an anti-rule-protected item |

## 7. SIGNED PREDICTIONS

* **P1** — fixed-rate rises above arm D's 12%, into **20–35%**. Grounds: D's
  identify step held 11 entries at once and this project's procedure doctrine
  says >10 at once are not applied.
* **P2** — **bucket 3 carries the largest single gain**, because E10 polarity is
  the most mechanical entry and the one where D's most flagrant miss sits
  (`l4252_4482_n016`, three `prefer` asserts stating the opposite of the span,
  answered `E10: PASS`).
* **P3** — **over-editing branch (a) FIRES**: ≥ 3 modules edited on a lens the
  frozen list names no defect for.
* **P4** — **the borrowed-gloss class does NOT move.** A gloss borrowed from
  another node and stamped `licence: textual, cites: <this node>` was 15/15 in
  the prose arms and fell to 3/15 only under arm C's demonstrations. No bucket
  names it; I predict 0 corrections.
* **P5** — the amended E5 (bucket 2 step 3) creates **no** vacuous-bodied rule.
* **P6** — ≥ 1 clause returns a byte-identical module for ≥ 3 of the 4 buckets.
* **P7** — ≤ 1 truncation. Grounds: D measured **0 reasoning chars** on every
  forced call and 3,585–19,384 on every unforced one; arm G's calls are all
  forced.

## 8. SPEND

Cap **$0.12**, enforced in `run_armg.py` at worst case against the on-disk
ledger before each bucket. Worst case for all four buckets is **$0.14442**,
which is OVER the cap — so **the run is gated bucket by bucket against MEASURED
spend**, and bucket 4 may be refused. If it is, the arm reports three buckets
and says so. ⚠️ `loop.py`'s ledger hole (a raising call spends and writes no
record) means `ledger_spent()` is a lower bound; `RESULT.md` reconciles against
`semi-formal-experiment/usage.jsonl`, ⚠️ **which sibling arms append to
concurrently** — the window must be split by prompt shape, not row count.

**Cost per defect fixed is reported**, against the 1-call baseline: a 4-bucket
design must beat one call per dollar as well as per defect.

## 9. CONTAMINATION — disclosed

I have read arm D's `RESULT.md` in full and arm F's headline before designing
this arm, and I know several of these clauses' histories, including which entry
D's worst miss belongs to (that knowledge is *in* P2). **I cannot adjudicate
blind and do not claim to.** The structural mitigation that carries the
headline: the denominator is arm D's frozen item counts over the Opus critic's
`feedback_1.md`, authored before either arm existed, and the numerator is read
off returned JSON against the span.

⛔ Nothing outside `_debug_gen11/bucketed_arm/` is written. No git is run, no
branch switched, no commit made. `decompose_arm/` is not touched.

— pre-registered 2026-08-16, before the first live call.
