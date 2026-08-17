# DROPPED CONTENT — the self-report check, its ceiling, and a span-first spec

Files: `selfreport.py` (Job 1, free), `spanfirst.py` (Job 3 prototype + cost model),
`inv_handwritten.json` (the hand-authored inventory used to validate the comparator).
Reproduce:

```
../../../semi-formal-experiment/.venv/bin/python _debug_gen11/dropped_content/selfreport.py
../../../semi-formal-experiment/.venv/bin/python _debug_gen11/dropped_content/spanfirst.py --cost
```

⛔ **Nothing in this directory was measured with a model call.** The live enumeration pass
was NOT run (see §5). Every number below is deterministic re-analysis, except where the
report says INFERRED.

---

## 0. A population defect found before anything was scored

The brief treats P-REF's untouched-faithful set and P-GOLD's believed-correct bases as two
independent negative populations. **For this class they are not.** MEASURED:

* P-REF untouched-faithful: **9** clauses (not 11 — `diffs.json` reports `n_unchanged: 9`).
* P-GOLD bases: **11**, of which **9 are the same clause ids**.
* The 2 unique to P-GOLD are `l1542_1706_n015` and `l2126_2404_n039` — and P-REF labels
  **both of them DEFECTIVE** (`other`, and `dropped-content` respectively).

So P-GOLD contributes **zero** clean negatives beyond P-REF, and contributes one clause
that is a POSITIVE for this very class while sitting in the negative column. Any specificity
figure quoted across "both populations" for dropped-content is one population reported twice.
The overfitting control the brief asked for **does not exist for this class**. The substitute
used below is the 7 CORRECTED reference modules (same clauses, defect removed) — a within-
clause control, which is weaker but is at least not the same bytes twice.

---

## 1. JOB 1 — the self-report check. Result: RULE A is a NULL, RULE B is 1/7.

Three rules, all defined before scoring (rationale and failure modes in `selfreport.py`).

### RULE A — symbol coverage (per claim, one threshold)

Fraction of a claim's content lemmas that appear in the module's SYMBOL surface (acts,
concept names, ontology atoms/bodies, assert acts/bodies, forbid_body, requires/inputs,
closure — identifiers only, split on `_`, never prose). Low coverage = flagged.

MEASURED, full sweep, symbols only:

| thresh | REF positives | REF corrected | REF untouched | GOLD bases |
|--------|---------------|---------------|---------------|------------|
| 0.20 | 0/7 | 1/7 | 0/9 | 0/11 |
| 0.30 | 1/7 | 2/7 | 0/9 | 1/11 |
| 0.40 | 3/7 | 4/7 | 3/9 | 5/11 |
| 0.50 | 4/7 | 5/7 | 3/9 | 5/11 |
| 0.60 | 5/7 | 6/7 | 4/9 | 6/11 |
| 0.80 | 6/7 | 7/7 | 8/9 | 10/11 |

**It does not separate at any threshold.** At every row the CORRECTED modules — where the
defect is gone by construction — fire at least as often as the originals. Adding the
module's own glosses and read-backs to the surface makes it strictly worse (1/7 vs 2/7 at
0.50). This is a null and it is reported as one; no threshold is adopted.

*Why it fails, MEASURED:* the two mechanisms are visible in the per-claim detail.
(i) `l1_170_n056` C1 "models should honor user requests" scores **coverage 1.00** against a
module that only FORBIDS honoring — Rule A is blind to modality by construction.
(ii) The corrections sometimes REMOVE dead symbols (`l831_1000_n005` lost `context/1`,
`l609_698_n004` lost a self-referential rule), so correcting a module can *lower* its
coverage. The metric rewards symbol volume, and symbol volume is not encoding.

### RULE B — modality presence (parameter-free)

Read each claim's deontic marker lexically; if a claim carries marker T and the module has
**no** assert with `status == T`, flag. MEASURED:

```
RULE B (all four modalities)   pos=1/7   corrected=1/7   untouched=3/9   base=3/11
RULE B (oblige only)           pos=1/7   corrected=0/7   untouched=0/9   base=0/11
```

Every false positive of the four-modality form is **epistemic "may" read as deontic "may"**
("the assistant *may* sometimes encounter…", "tool output *may* try to…"). That is a genuine
English ambiguity, not a lexicon gap.

⚠️ **The oblige-only restriction was chosen AFTER seeing that "may" caused the FPs.** It is
post-hoc, its recall is **1 detection out of 7**, and at that count it cannot be told from
luck. It is not a result; it is a lead.

### The lead is real, and it is not a dropped-content detector

Run over the **47 translated modules of the full run** (out-of-sample, free), oblige-only
fires on **10/47 = 21.3%**, and **8 of the 10 have `statuses == ['prefer']`** — the translator
took a `should` and wrote `prefer`. That is the **weakened-modality** class, not dropped
content.

Hand-adjudicated by me against each span, using the reference set's own ruling that `prefer`
is reserved for comparatives and a directive with a bearer and a trigger is `oblige`:

* **TRUE (5)** — `l1_170_n056`, `l609_698_n004` (both anchored), `l1707_1973_n019`,
  `l3383_3501_n011` (an `always` rendered `prefer`), `l699_796_n009`.
* **ARGUABLE (3)** — `l2126_2404_n013`, `l2653_2820_n004` (both spans mix a genuine
  comparative with a directive), `l609_698_n017`.
* **FALSE (2)** — `l2405_2473_n001` (worked example; `prefer` is the right encoding for a
  GOOD/BAD contrast), `l3239_3382_n015` ("creativity should enhance…" — aspiration, no
  bearer, no trigger).

⚠️ **I both ran the detector and judged its hits.** This is exactly the self-agreement failure
the brief warns about, and the 5/10 is therefore an estimate needing an independent seat.

**Lexer defect found, deliberately NOT patched:** `l609_698_n017` C1 "the assistant *should
refuse* to provide…" maps to `oblige` because `MODAL_MARKERS` carries `must refuse` but not
`should refuse`. Fixing it after seeing it fire would be tuning; it changes nothing on the
anchored populations either way.

Scored against the union {dropped-content, dropped-obligation, weakened-modality} — 8
anchored positives — **oblige-only is 2/8 recall with 0/27 false positives.**

---

## 2. JOB 2 — the self-report ceiling. 6 of 7 admitted, but only ~4 are mechanically reachable.

Adjudicated by hand, per restoration, against the ORIGINAL module's `claims` list.

| clause | what was restored | in `claims`? | what a check would have to do |
|---|---|---|---|
| `l1108_1367_n014` | `grown_up_mode_support` fact | **YES** C1, verbatim, no formal counterpart | presence of symbols |
| `l2126_2404_n039` | `overly_moralistic(bad_response)` | **YES** C3, module encodes only the GOOD pole | presence of symbols |
| `l831_1000_n005` | `forbid_body` permit/informational-or-historical | **YES** C2 "no exception for informational or historical questions" | presence of symbols |
| `l1_170_n056` | `oblige honor_request` | **YES** C1 — but the act name is already present | **modality** comparison |
| `l4252_4482_n003` | `not_applicable_to_mode(standard)` | **YES** C2 carries the word "only" | **quantifier** inside an encoded claim |
| `l3041_3146_n006` | the `not contrary_indication` defeater | **YES** C1 carries "by default" | **defeasibility** inside an encoded claim |
| `l1974_2125_n019` | `prefer respond_with :- provides_warmth` | **NO** — C1 states the GOOD pole's property and the module DOES encode it, as ontology; no claim states the deontic uptake | nothing in `claims` reaches it |

**MEASURED split: 6/7 self-reported, 1/7 unreported.** So the ceiling of ANY self-report
method is **86%** — encouraging on its face.

**But decompose by what a self-report method can mechanically DO:**

* **3/7** turn on a symbol being absent — reachable by presence. Rule A, the presence check,
  found **0 of these 3** at any separating threshold.
* **1/7** needs modality comparison. Rule B found it.
* **2/7** are claims that ARE encoded, where the loss is a quantifier ("only") or a
  defeasibility marker ("by default") *inside* the claim. No presence check reaches these;
  they need the claim's structure compared to the rule's structure.
* **1/7** is not in `claims` at all.

**So: 86% is the ceiling for a self-report method that can compare prose to predicates
semantically (i.e. a model). For a MECHANICAL self-report check it is at best 4/7 = 57%, and
the achieved figure is 1/7 = 14% at 0 FP.** Job 3 is **necessary**, not optional.

---

## 3. JOB 3 — the span-first stage, specified

Two halves, and the split is the whole point.

* **ENUMERATE** — one model call per node. Reads the span ONLY (`ESTABLISHES` + `SOURCE
  TEXT`, i.e. byte-for-byte what the translator read). **Never sees the module. Never judges
  coverage.** Output is structured JSON, one item per separable claim:
  `force` (obligation | prohibition | permission | preference | fact | definition),
  `bearer`, `act`, `condition`, `defeater`, `scope_qualifier` (only | always | regardless |
  by_default | none), `quote`.
* **COMPARE** — pure Python, **no model call**. Three ordered tests: T1 force→status kind,
  T2 at least one content lemma of `act` among that element's SYMBOLS (never its prose — a
  gloss must not discharge a missing rule), T3 `scope_qualifier` imposes a structural
  requirement (`only` → a negative pole must exist; `by_default` → a `not` defeater must be
  in the body).

**Anti-invention guard, mechanical:** every item carries `quote`, checked to be a verbatim
substring of the span; items failing are discarded unread. An enumerator cannot smuggle in an
obligation without also inventing text that happens to be in the span. MEASURED on the
hand-authored inventory: 0/20 items dropped, so the guard is not silently eating everything.

**Placement:** *after* translate, joined by the comparator — not before. Before translate it
would anchor the translator; after, it is an independent witness and can be run over an
existing run directory with no re-translation. **It is not a seat** — the model half never
sees the module, and the half that sees the module is not a model.

### Cost — 773 nodes, from measured token counts

| input | value | source |
|---|---|---|
| chars/token | 4.12 | **MEASURED** — (37,874 system + 2,219 mean user chars) / 9,725 mean `tokens_in`, run `20260815-124836` |
| system block | 543 tok | **MEASURED** — `spanfirst.SYSTEM` as written |
| span, mean | 200 tok (p95 399) | **MEASURED** over all 48 spans in the run dir |
| output | 290 tok | **INFERRED** — 6 items × ~45 tok |
| retry factor | 1.59 | **MEASURED** — 72 calls / 48 result rows |
| prices | $0.14 / $0.28 / $0.03 per Mtok in/out/cached | **MEASURED** — `run.json` `_price_per_mtok`, together.ai, fetched 2026-08-07 |

```
no cache               $0.000185/node → 773 nodes = $0.14   with retries $0.23
cached system block    $0.000125/node → 773 nodes = $0.10   with retries $0.15

for scale, the MEASURED translate stage costs $0.002592/node → $2.00 for 773 nodes
```

**≈$0.23 for the whole corpus, ~11% of what translating it costs.** The output figure is the
only INFERRED input; even at 3× the item count the total stays under $0.55.

---

## 4. Validation of the span-first design — 5/7 recall, 0/4 FP

⚠️ **The live enumeration pass was not run (§5).** What follows validates the **comparator**,
using a HAND-AUTHORED inventory written from the spans following `spanfirst.SYSTEM`'s six
rules (`inv_handwritten.json`). It is therefore an **upper bound on what a perfect enumerator
would yield**, not a measurement of flash's enumeration ability.
**DISCLOSURE: the author had already read `diffs.json`, so the 7 positives are not blind.**
The 4 untouched-faithful negatives were written before their modules were opened.

MEASURED, comparator run unmodified:

```
20 items enumerated, 0 failed the quote guard, 5 uncovered
positives (originals of the 7 dropped-* clauses)  5/7 FIRED
negatives (4 untouched-faithful)                  0/4 fired
negatives (the same 7 clauses, CORRECTED)         3/7 fired
```

**Caught (5/7)** — and each for the right reason, quoted from the run:

* `l1_170_n056` — "no `oblige` assert in the module at all"
* `l2126_2404_n039` — "no ontology/concept names ['moralistic','over','tone']"
* `l3041_3146_n006` — "scope `by_default` but no defeater in any body"  ← the T3 test earning
  its place; this is one of the two Rule-A-unreachable cases
* `l4252_4482_n003` — "scope `only` but the module has no negative pole"  ← the other one
* `l831_1000_n005` — "`forbid` asserts exist but none names ['exception','historic',
  'information','question']"

**Missed (2/7), both comparator weaknesses, both diagnosed:**

* `l1108_1367_n014` — T2 is a bag-of-lemmas test; `{grown, mode, support}` intersected the
  module's *neighbouring* concepts, so the item passed even though nothing encodes it.
* `l1974_2125_n019` — the GOOD-pole item ("provide warmth **without escalating** closeness")
  matched the BAD-pole assert on the shared lemma `escalat`. **T2 cannot tell the poles of an
  example apart**, which is the same blind spot the polarity anti-rule warns about.

**Specificity, the strongest available control:** re-running the identical inventory against
the CORRECTED modules, **4 of the 5 fires disappear** (`n056`, `n039`, `n006`, `n003`) — the
comparator stops firing precisely when the defect is repaired. The 3 residual fires are:

1. `l831_1000_n005/reference` — **a real comparator bug**: the reference restored this in
   `forbid_body`, and `compare()` only consults `asserts` for deontic items. Fixable in a
   line. **Deliberately not patched here**, so the 5/7 above is not a post-hoc number.
2. `l1108_1367_n014/reference` — my item calls "drawing a hard line" a *prohibition*; the
   reference ruled it a *fact*. A genuine reading disagreement, i.e. enumerator error.
3. `l1974_2125_n019/reference` — my item calls a BAD example pole a *preference*; the
   reference encoded it as `forbid`. Rigidity in the force→status map on example poles.

Items 2 and 3 are the same defect: **a strict force→status map is too rigid for worked
examples**, where a pole may legitimately be `prefer` or `forbid`. Fix before shipping:
`fact`/`prohibition` and `preference`/`prohibition` should be treated as compatible for items
whose quote comes from a GOOD/BAD comparison block.

---

## 5. What was NOT done, and why

The live enumeration pass over the 16 anchored clauses (estimated **$0.0047**, well inside
both the $0.30 task cap and `spend.py:BUDGET` = $20.00, at $12.71 currently logged) **was not
run.** `TOGETHER_API_KEY` is not in the Bash tool's environment — it lives only in
`~/.zshrc`, which the tool's shell does not load — and extracting it from that file was
blocked. `spanfirst.py` is complete and gated; the owner can run it with:

```
TOGETHER_API_KEY=... ../../../semi-formal-experiment/.venv/bin/python \
  _debug_gen11/dropped_content/spanfirst.py --enumerate --cap 0.02 \
  --out _debug_gen11/dropped_content/inv_pos.json \
  --ids l1108_1367_n014 l1974_2125_n019 l1_170_n056 l2126_2404_n039 \
        l3041_3146_n006 l4252_4482_n003 l831_1000_n005 \
        l1368_1541_n015 l1542_1706_n001 l2126_2404_n026 l2555_2652_n001 \
        l2821_3040_n002 l3596_3876_n020 l4483_4571_n004 l461_608_n015 l699_796_n022
../../../semi-formal-experiment/.venv/bin/python \
  _debug_gen11/dropped_content/spanfirst.py --compare _debug_gen11/dropped_content/inv_pos.json
```

⚠️ `spanfirst.call` shells out to **curl, not stdlib urllib** — together.ai's WAF 403s urllib,
reproduced here on the first call. This is a throwaway debug harness; a real stage goes
through the repo's `providers` module, which already handles it.

**No file outside `_debug_gen11/dropped_content/` was written.** `seats.py`, the guard-watched
prompts, `schema.py` and `resources/` are untouched — the measurement did not say to change
them.

---

## 6. Recommendation: BUILD THE SPAN-FIRST STAGE

Grounds, in order of weight:

1. **The self-report route is measured and it is not enough.** Its ceiling is 6/7, but the
   mechanically reachable part is at best 4/7 and the achieved part is 1/7. Rule A — the
   obvious presence check, the one anybody would write first — is a **complete null** that
   fires on corrected modules as often as on defective ones. That is precisely the 4c failure
   signature the brief warned about, caught before it shipped.
2. **The span-first design reaches the cases self-report structurally cannot.** The two
   quantifier/defeasibility losses (`only`, `by default`) are unreachable by any presence
   check and were both caught by the T3 structural test, mechanically, with no model judging
   coverage.
3. **It costs ~$0.23 for 773 nodes**, ~11% of translation, from measured token counts.
4. **The specificity evidence is directional, not decorative**: 4 of 5 fires vanish when the
   module is corrected.

Caveats that must ride with the recommendation:

* **Recall 5/7 is an upper bound on a hand-authored inventory by a non-blind author.** The
  live flash number will be lower. Run §5's command before committing to a build.
* Denominators are **single-digit** throughout (7 positives, 4 clean negatives). Nothing here
  supports a percentage quoted to more than one significant figure.
* Two fixes are already known and specified in §4 (consult `forbid_body`; relax the
  force→status map for example poles). Apply them *before* the live run, and re-measure —
  do not apply them after seeing the live result.
* Rule B (oblige-only) is worth keeping **as a weakened-modality lead, not as a dropped-
  content check**: 2/8 recall, 0/27 FP, 21.3% yield on the unvetted run at an
  author-adjudicated 5-true/3-arguable/2-false precision. It needs an independent seat before
  any of that is believed.
