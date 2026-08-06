# Human adjudication — protocol, schema, and contamination ledger

**Status: DESIGN, for approval. Instrument not yet generated, no items burned.**
Written 2026-08-05.

## Why this exists

Two questions need answering and neither can be answered by a model:

1. **How much of the tool-vs-panel gap is the panel being wrong?** The census field that
   nominally records this is confounded with which batch produced it, so it cannot be quoted.
   Asking a model to adjudicate whether frontier models were wrong is close to circular — the
   frontier panel *is* the benchmark.
2. **Is a behaviour-general representation possible?** (`FRONTIER_LAYER_FEASIBILITY.md`) That
   turns on what information a passage must carry to decide relevance — which is knowable only
   by someone actually deciding relevance and noticing what they used.

**These are the same act of reading.** One pass answers both. Running them separately would
require judging the same items twice, which is exactly what we cannot do.

---

## The constraint that shapes everything: attention is one-shot

Once you have read an item and formed a judgement, you can never again be a *blind* judge on
it. That makes human attention a consumable resource of the same kind as the six held-out
behaviours, and it gets the same discipline:

* **A contamination ledger** — `human_adjudication/BURNED.md` records every passage id seen,
  when, and in which pass. Anything on that list is permanently ineligible for a future blind
  human pass.
* **A reserved pool** — the sampler sets aside a disjoint set of comparable items, untouched,
  so a second question can be asked later without re-using burned ones.
* **Capture enough the first time.** The schema below is deliberately wider than question 1
  needs, because the marginal cost of recording *why* while the passage is in front of you is
  seconds, and the cost of coming back is that you can't.

---

## What you see, and what you don't

Per item, you see **only**:

* the passage text, as it appears in the document;
* the behaviour name and its definition, verbatim;
* nothing else.

You do **not** see: what the tool predicted, what the panel scored, that the two disagreed, the
census cause, or any other item's verdict. Items are **interleaved across behaviours** and
presented in a randomized order — the census's `side` field became unusable precisely because
three separate per-behaviour runs each developed their own stance, and interleaving is the
cheapest structural defence against repeating that.

**Roughly 20% of items will be cases where the tool and panel AGREED**, unlabelled and
indistinguishable from the rest. Without them we can measure your disagreement rate on hard
cases but have no baseline to compare it against, and any estimate of panel error would be
inflated by construction.

---

## The record, per item

```json
{
  "item_id": "…",
  "verdict": "relevant" | "not_relevant" | "unclear",
  "confidence": "high" | "medium" | "low",
  "deciding_span": "verbatim quote from the passage that decided it, or null",
  "deciding_information": "what did you need to know about this passage to decide?",
  "definition_sufficient": true | false,
  "definition_gap": "if false: what the behaviour definition leaves open",
  "notes": "anything else a future reader should know"
}
```

**`verdict`** — the ground truth for question 1. `unclear` is **first-class**, not a failure:
the project's standing convention is never to force a call, and a forced call here would
manufacture agreement or disagreement that isn't real.

**`deciding_span`** — the verbatim quote is what makes your judgement auditable and reusable.
It is the same license-quote discipline every annotation seat in this project already follows:
a claim that cannot cite its span does not land.

**`deciding_information`** — *the slot data, and the highest-value field here.* Not "why is it
relevant" but "what did you need to KNOW about this passage". Answers cluster into slots — who
is affected, what is implied but unsaid, what kind of obligation it is — and the rate at which
new clusters appear **is** the saturation curve. A few words is enough: *"who the harm falls
on"*, *"that this is about answer quality, not about anyone being harmed"*.

**`definition_sufficient` / `definition_gap`** — when the *behaviour definition* is what's
ambiguous rather than the passage, that is an interpretation candidate, and it belongs in the
ruling channel rather than the schema. The m0108 boundary — is a user's own employer a third
party — was found exactly this way, by two people splitting on it.

---

## Sampling

* **~40 items**, stratified across the three behaviours and the main failure causes, plus the
  ~20% agreement anchors.
* Selection is **frozen and sha-pinned before you see anything**, with the answer key held in a
  separate file the presentation cannot read. That is the sandwich rule this repo already
  applies to every golden set.
* Forty is enough for the question actually being asked. Distinguishing "the panel is wrong on
  ~14% of disagreements" from "~50%" needs far less resolution than distinguishing 14% from
  20%, and we only need the former to know whether the benchmark is materially wrong.

---

## What comes out

* **Question 1:** your verdicts against the tool's and the panel's, on the same items — a
  direct estimate of each one's error rate on disagreements, with no model in the loop for
  ground truth.
* **Question 2:** the `deciding_information` answers, clustered into a slot inventory, with the
  saturation curve plotted across behaviours in the order you saw them.
* **A third thing, free:** a small set of human-adjudicated cases with verbatim spans and
  reasoning — which is precisely the shape of a golden set, and is reusable as one.

---

## Handling of the result

* Stored under `human_adjudication/`, sha-pinned, **immutable once written**. A verdict may be
  superseded by a later recorded ruling, never silently edited.
* **`FORBIDDEN`-registered.** This is ground-truth data adjacent to the panel; it must never be
  reachable from the query path. Same fence as the panel artifacts.
* The `BURNED.md` ledger updates in the same commit as the results — never later, or the ledger
  drifts from what was actually seen.

---

## The one thing I want you to push back on before we run it

Forty items at roughly 90 seconds each is about an hour, and that hour is the entire cost. If
that is too much, the honest smaller version is **20 items** — enough to detect a large panel
error rate but not to resolve a moderate one, and enough for maybe half a saturation curve.

What I would *not* do is shrink it by dropping the agreement anchors or the
`deciding_information` field. Without the anchors the panel-error estimate is uninterpretable;
without the deciding-information field we spend your attention once and get one answer instead
of two.
