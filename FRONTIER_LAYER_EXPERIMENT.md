# The frontier-adjudicated layer — staged experiment design

**Status: DESIGN, for approval. Nothing built, nothing spent.** Written 2026-08-05 from Matt's
staged proposal, with the measurement discipline made explicit.

**The thesis under test** (`PROJECT_ASSESSMENT.md` Option D): pay frontier prices **once per
document** to produce a rich, explained, human-correctable map of it; then answer unlimited
behaviour questions against that map cheaply. High one-time cost per document, near-zero cost
per behaviour and per iteration.

**The one thing that is genuinely unknown:** does a map built *without* knowing the behaviours
answer behaviours nobody had in mind? Everything else is engineering.

---

## The three stages

| stage | resource spent | fixes allowed? | what it measures |
|---|---|---|---|
| **1. Build** | one behaviour, burned as pure dev | yes, freely | Can a frontier layer answer *at all*? What dimensions does the schema need? |
| **2. Learn** | the other two dev behaviours | **yes, but counted and classified** | **What does extending to a new behaviour cost?** |
| **3. Test** | the held-out behaviours, frozen | **no** | Does it hold with zero adaptation? |

Stage 2 is the load-bearing one and it is easy to get wrong: if fixes are made freely and not
counted, stage 2 becomes a second dev set and measures nothing. **The number and kind of fixes
stage 2 needs is the primary result — not the score.**

---

## Which behaviour to burn — the data

Failure classes per behaviour, from the 294-case census:

| cause | caution | harm-avoidance | helpfulness |
|---|---:|---:|---:|
| `fp_promiscuous_atom` | 33 | 36 | **86** |
| `fp_threshold_drift` | 27 | **0** | 32 |
| `fp_section_prior` | 18 | 12 | **0** |
| `fn_family_absent_from_vocabulary` | 1 | **22** | 3 |
| `fn_names_cannot_meet` | 5 | 9 | 5 |
| rare classes (`fn_threshold`, `fp_join_artifact`, `unexplained_escalate`) | 1 | 1 | 3 |
| **total / distinct classes** | **85 / 6** | **80 / 5** | **129 / 7** |

**Recommendation: burn `helpfulness` as the stage-1 dev behaviour.** It carries 44% of all
catalogued failures, the most distinct classes (7 of 8), and — decisively — it contains the ~30
cases that *no current mechanism addresses at all*: passages about **answer quality**, where
relevance is not a question about parties or harms. Designing a schema against helpfulness
forces it to invent the dimension we know is missing, rather than re-deriving the party
dimensions we have already designed.

**The caveat that shapes stage 2: helpfulness has zero `fp_section_prior` cases.** A schema
designed on it alone will never have been tested against that class. Symmetrically,
harm-avoidance has zero `fp_threshold_drift`. **No single behaviour exercises everything**, and
that is not a flaw in the plan — it is the reason stage 2 exists. It just has to be
pre-registered, or stage 2's fixes will be misread.

---

## The measurement discipline for stage 2

Before stage 2 begins, **pre-register the classes stage 1 could not have exercised** (on the
recommendation above: `fp_section_prior`, and whichever rare classes helpfulness lacks). Then
classify every fix stage 2 requires into exactly one of three buckets:

| bucket | what it means | how to read it |
|---|---|---|
| **EXPECTED** | a new schema dimension for a failure class stage 1 never saw | Fine. Predicted. Says the dimension count is finite and we're enumerating it. |
| **ALARMING** | a fix in a class stage 1 *did* exercise — the schema handled it there but not here | The dimension is behaviour-sensitive. Predicts stage 3 needs more of the same. |
| **FATAL** | a per-behaviour special case — anything that names a behaviour, or only helps one | The tail is unbounded. Stop; Option D is disconfirmed. |

**The prediction to freeze before stage 2, and the thing that actually answers Matt's
question:** if the dimension count is small and behaviour-independent, stage 2 needs a handful
of EXPECTED fixes, zero ALARMING, zero FATAL — and stage 3 then needs approximately none. If
stage 2 needs ALARMING fixes, expect stage 3 to need them per behaviour forever, which *is*
"it's just going to be like that for every behaviour."

The delta between stage 2's fix count and stage 3's is the whole experiment.

---

## Freeze mechanics for stage 3

Stage 3 is one-shot. Before any held-out behaviour is looked at, freeze and sha-pin: the
annotation schema, the annotation prompt, the model and its settings, the full pipeline config,
the query-construction procedure, and the scoring code. The repo already has the pattern (the
G-freeze artifact and the cycle ceremony's config identity); this is that, applied to the layer.

**Two one-shot resources exist, and they answer different questions. Do not spend both at
once:**

* the six held-out **behaviours** — "does it generalize across behaviours on the same document?"
* the sealed **second document** (the constitution) — "does it generalize across documents?"

Stage 3 spends the first. **Reserve the second entirely.** If stage 3 succeeds, the document
transfer is the follow-up that makes the result interesting to anyone outside this project; if
stage 3 fails, spending the document too would have told us nothing extra.

Worth considering: **split the six** — three for stage 3, three reserved. Six is more statistical
power than the question needs (a per-behaviour adaptation cost shows up in three), and it keeps
a confirmation set for whatever stage 3 teaches. My recommendation is 3 + 3.

---

## Cost, honestly

* One annotation pass: ~589 passages × one frontier call ≈ **$20–60**.
* Stage 1 will re-run the pass on every schema revision. Budget **5–10 passes → $100–600**.
* Stages 2 and 3 need one pass each *if* the schema is frozen; stage 2's fixes mean 1–3 more.
* The cheap-model-plus-parity-validation variant — where the real economics live — is worth
  building only **after** stage 2, once the schema has stopped moving. Building it earlier means
  re-validating it on every revision.

**This exceeds the project's current $8.50 ceiling by one to two orders of magnitude.** It is
still small in absolute terms, and it is the first spend in this project whose result would
change what we believe rather than move a metric by less than its noise floor. It needs an
explicit budget decision, not an incremental approval.

---

## What stage 1 actually builds

Per passage, one frontier call producing a structured record — the four dimensions we found by
failing, plus an open slot:

1. **Who is affected** — who a harm falls on or a protection runs to, distinct from who is
   addressed. (The wall: two structurally identical passages, one about threatening another
   person, one about self-harm.)
2. **What is implied but not said** — parties the passage protects without naming.
3. **Scope decisions with reasoning** — where the document is genuinely ambiguous, the call and
   its grounds, so a human can overturn it later.
4. **What kind of obligation this is** — a party-protection rule, an answer-quality standard, a
   procedural constraint. (The ~30 cases nothing currently touches.)
5. **Open slot: "what else is salient here"** — free text, and the thing to mine for dimension
   #6 when stage 2 or 3 fails.

**Every field carries the model's written explanation and a verbatim quote from the passage.**
That is what makes it auditable and correctable: a human reads the reasoning, disagrees, and
overrides — and the override is logged with who made it and when, and is revocable. That
machinery is already designed (`semi-formal-experiment/INTERPRETATION_LAYER_DESIGN.md`); it does
not need reinventing.

**The schema must be written without looking at any held-out behaviour.** If the open slot is
later filled by reading a held-out failure, stage 3 is spent.

---

## What would make me stop

Stated in advance, so it is not rationalized later:

* Any **FATAL** fix in stage 2 — a per-behaviour special case.
* Stage 2 needing more schema dimensions than stage 1 did. That is a diverging series, not a
  converging one.
* Stage 1 failing to beat the current +0.309 on its own dev behaviour. If a frontier layer with
  free fixes cannot beat the rule engine on the behaviour it was built for, the thesis is wrong
  and nothing downstream will save it.
