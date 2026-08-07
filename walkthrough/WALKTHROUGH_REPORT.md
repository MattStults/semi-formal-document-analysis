# Manual walkthrough — spec → Clingo → English → verification

2026-08-07. Everything below was run by hand, no subagents, `$0` (no provider calls).
Artifacts: `walkthrough/*.lp`, `semi-formal-experiment/WALKTHROUGH_SPECIMENS.json`.

**Scope actually completed:** step 1 in full (all 9 specimens selected from real frontier
panel data), and steps 2–4 and 6 driven end-to-end on **one** specimen — the flagship
hard-relation case. Step 5 (repeat across the other 8) is **not done**. The method findings
below are what the exercise was for, and they generalise; the remaining 8 are queued.

---

## Step 1 — specimen selection (complete)

Source: `panel_universe.load_universe(spec_keys=('openai',))` — the frontier panel, 589
passages × 3 behaviours, judges **Kimi-K3, Claude Fable 5 / Opus, GPT-5.6 Sol**, each voting
0 (not relevant) / 1 (related) / 2 (core), summed 0–6. Tool predictions from the shipped
compliant module `combined`, paired with the canonical `annotations.json` + `behavior_atoms.json`.

Where the current tool disagrees with the frontier panel:

| behaviour | tool fired | FN (panel ≥5, tool missed) | FP (panel =0, tool fired) | contested (one judge core, another none) |
|---|---:|---:|---:|---:|
| helpfulness | 228 | 3 | 47 | 97 |
| harm-avoidance-to-third-parties | 162 | 16 | 18 | 34 |
| avoiding-over-and-under-caution | 236 | 1 | 137 | 59 |

Chosen specimens (`WALKTHROUGH_SPECIMENS.json`):

| behaviour | matching | not matching | contested |
|---|---|---|---|
| helpfulness | `m0284` sensitive-topic advice (5/6, tool missed) | `m0041` developer-latitude rationale (0/6, tool fired) | "Inapplicable instructions…" (3/6, **no clause joins to it**) |
| harm-3p | ⭐ `m0255` transformation-exception scope (5/6, tool missed) | `m0142` "Direct expenditures" fragment (0/6, tool fired) | `m0186` tool-output relevance (3/6, tool missed) |
| over/under-caution | `m0546` avoid excessive hedging (6/6 unanimous, tool missed) | `m0004` "Prevent serious harm" (0/6, tool fired) | `m0206` "However… may discuss…" (2/6, tool fired) |

⚠️ **Two selected passages have `clauses=[]`** — no clause joins to them at all, so the tool
cannot predict them regardless of representation. That is a join defect, not a relevance one,
and it is invisible in any MCC number.

---

## Step 2 — hand translation of `m0255`

The passage carries four separable claims:

| | claim |
|---|---|
| C1 | the transformation exception's scope is exactly {restricted, sensitive} |
| C2 | policies outside that scope still bind |
| C3 | purpose ("good cause", research, analysis) never lifts a policy |
| C4 | the exception covers **information** only, never **actions** |

⭐ **C1 is the hard relation**, and it is why this specimen was chosen: it is not a property
of a clause, it is a relation between one rule and a **class of other rules**. A bag of concept
names cannot state it — which is exactly the `readback` sufficiency finding (0.160) in one case.

---

## Steps 3–4 — round-trip and the three iterations

Each iteration was forced by a specific defect the read-back exposed. This is the part worth
keeping.

### Iteration 1 — lifting a policy that was never engaged
`lifted(P,M)` did not require `forbids(P,M)`, so case A reported
`lifted(sensitive_content, m1)` for a policy that never applied. Verdict unaffected;
explanation polluted with true-but-meaningless steps. **Fix:** require `forbids`.

### ⭐ Iteration 2 — negation-as-failure carries no trace
`binds(P,M) :- …, not lifted(P,M).` Case C (an **action** inside the exception's scope)
produced:

> *"restricted_content still binds: the transformation exception does not reach it"*
> — supported by `policy_class(restricted_content, restricted)`

That is **right in its verdict and wrong in its reason**: `restricted` *is* in scope; the
operative reason is that `m3` is an action. Negation-as-failure gave the explainer nothing to
show, so the rule's own prose asserted a reason that was not the one that fired.

**Fix:** every way of failing to be lifted became a positive atom
(`out_of_scope`, `is_an_action`, `not_user_supplied`). Case C now reads:

> *"the exception covers information only, and m3 is an action"* — supported by `material_type(m3, action)`

**Generalises:** any translation that reaches a verdict through `not …` will produce
explanations whose stated reason is unverifiable. For an explainability-first tool this is a
design rule, not a detail: **negative conditions must be positivised before read-back.**

### ⭐ Iteration 3 — an incoherent world state produced a confident answer
Probe case D asserted both `transformation_of_user_content(m4)` and `new_material(m4)`. The
program accepted it and derived `lifted` **and** `binds` for the same pair, then returned the
correct verdict anyway. A right answer from an impossible state is worse than a wrong one.

**Fix:** `:- lifted(P,M), binds(P,M).` and `:- new_material(M), transformation_of_user_content(M).`
Case D is now `UNSATISFIABLE` — the formalisation *rejects the malformed probe*, which is the
behaviour we want. Cases A–C unaffected.

### My own faithful / sufficient judgement (the step-3 test)

**FAITHFUL — yes, after iteration 2; no, before it.** All four read-backs now assert only what
the passage supports. Before iteration 2, case C was unfaithful.

⚠️ But every explanation leans on facts from **outside the clause** — `policy_class(deception,
other)`, `protects_third_party(restricted_content)`. The clause never says deception is a
policy or that restricted content protects third parties. Under the license taxonomy these are
`world`/`assumed`, never `textual`, and the derivation is only as good as they are.

**SUFFICIENT — not from any single case.** Coverage needed all four probes: C1 from A+B, C2
from B, C4 from C, and C3 is not demonstrable by any case at all (see below).

⭐ **This directly bears on the 0.160 sufficiency number.** `readback` judges **one** rendering
per clause. A four-branch conditional cannot be sufficient in one rendering *by construction*.
Sufficiency is a property of the **probe set**, not of a rendering — so some unknown part of
the 84% insufficiency is a measurement design artifact, not an encoder failure.

### ⭐ A claim that no case can demonstrate

C3 ("purpose never lifts") is a **meta-claim about the rule set**, not about any world state.
It is encoded as `:- lifted(P,M), lifted_by_purpose(P,M)` — an assertion that *no rule of a
certain shape may exist*. No positive case exhibits it; it is verified by inspecting the
program, not by running it.

⇒ **Two verification modes are needed, not one:** model-checking (run probe cases) for
claims about situations, and program inspection for claims about the rule set. A harness that
only does the first will silently under-verify every meta-rule in the document.

---

## Step 6 — does formal verification get the match right?

Behaviour encoded in `walkthrough/behaviour_harm3p.lp` from its definition: *"weigh the
potential harm to those outside the conversation, avoiding actions or content that harm third
parties, society, or the world."*

Derivation returned:

```
"clause m0255 bears on the behaviour: it decides whether material under policy
 restricted_content may be produced, and that policy protects someone outside
 the conversation"
  |__protects_third_party(restricted_content)
  |__policy_class(restricted_content,restricted)
```

| | verdict |
|---|---|
| frontier panel | **5/6 — matching** (kimi 2, opus 1, sol 2) |
| current tool | **missed it** (false negative) |
| formal translation | **matches, with a citable derivation** |

⚠️ The derivation rests on `protects_third_party(restricted_content)`, which is asserted, not
read from the document. Change that one fact and the match disappears. That is the honest
shape of the result: **the formalism made the reasoning inspectable and the load-bearing
assumption nameable** — it did not make it assumption-free.

---

## What this exercise cost, and what it says about scale

One specimen, three iterations, ~40 lines of Clingo, four probe cases, `$0`. Call it an hour of
careful work. At that rate the 9 specimens are a day, and 593 clauses is not reachable by hand
— which was already the assumption, but this is the first datum on the per-clause cost.

## Open, for the next session

1. Steps 2–4 on the remaining 8 specimens, starting with the two `clauses=[]` join failures.
2. The `world`/`assumed` facts each translation needs — collect them and see whether they form
   a small shared vocabulary or a long tail. This decides whether the approach scales.
3. Whether iteration 2's positivise-the-negation rule can be checked mechanically.
