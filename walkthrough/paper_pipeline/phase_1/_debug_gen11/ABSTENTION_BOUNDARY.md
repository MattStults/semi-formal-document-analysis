# ABSTENTION_BOUNDARY.md — is the abstention criterion underspecified, and how big is the defect?

**Headline.** The criterion is **self-contradicting, not merely vague**: `prompt/00_task.md`
names *section heading* and *example* as abstention triggers, and the assembled system prompt
then shows two worked examples that **translate** a heading node and a document-example node.
One of them, `l3995_4164_n001`, is a clause **DeepSeek itself abstained on in the real corpus
run** — the model was shown that clause as a translate-exemplar and, on a different draw,
declined it as non-normative.

**Blind adjudication of the 29 disputed clauses (175 isolated Haiku draws, key opened only after
every judgement was on disk):**

| bucket | n / 29 | Wilson 95% |
|---|---|---|
| **ABSTAINER RIGHT** (span is non-normative; a model translated it anyway) | **19** | 66% [47%, 80%] |
| TRANSLATOR RIGHT (span is normative; Haiku abstained) | 2 | 7% [2%, 22%] |
| **GENUINELY AMBIGUOUS** | **2** | **7% [2%, 22%]** |
| normative, no abstainer to vindicate (control) | 6 | 21% [10%, 38%] |

**The consequential number.** Blind adjudication of DeepSeek's *successful* modules estimates
**≈22 of the 69 translated modules (32%, 95% CI [20%, 49%]) are modules for spans that should
not have them** — 43% if the ambiguous ones are counted as questionable. Every one of these
passed schema, link and readback.

**ZERO API spend.** 175 local Haiku subagent draws, one isolated agent per (item, draw). All of
`runs/`, `translation_sample/runs/`, `repair_graveyard/` read-only. No guard-watched file edited.
No git commit.

---

## 1. What the prompt actually says

The exact bytes sent are `resolve_runs/graph_v2/translation_sample/runs/20260814-173322-together-deepseek-v4-flash/prompt_system.txt`,
36,820 chars, `sha256[:16] = 5ff9daf7fe58845f` (the same artefact `DC1_EXPERIMENT.md` pins).

### 1.1 The governing prose — `prompt/00_task.md` (system prompt line 109)

> ## Abstention is a real answer
>
> If you cannot translate this clause faithfully — it is a section heading, it states a goal rather
> than a condition, it is an example, or its content is not expressible as rules — **abstain and give
> the reason**. Producing something that looks like a translation is worse than declining. The
> abstention rate is a signal we want, not a failure we penalise.

That is the **entire** criterion. It is a four-item disjunctive list of *triggers*, not a test:

1. section heading
2. states a goal rather than a condition
3. an example
4. content not expressible as rules

### 1.2 The mechanics — `prompt/10_output_format.md` (system prompt line 276)

> ### When abstaining
>
> Set `outcome` to `"abstained"`, give `abstain_reason`, and leave every list empty. An abstention
> with content in it is neither an abstention nor a translation, and is rejected.

Purely procedural. Adds no criterion.

### 1.3 `schema.py` — the `Module` contract

Docstring (`schema.py:700-713`):

> ⚠️ `abstained` is a real answer, not a failure. A clause that cannot be
> translated faithfully — a heading, a goal with no trigger, an example —
> should be declined with a reason rather than turned into something that
> passes the checks. The rate at which that happens is a signal worth reading:
> without it, "we translated the document" cannot be told apart from "we
> translated the easy parts of it".

Fields (`schema.py:715-721`):

> `outcome`: "`translated` if you wrote a module for this clause; `abstained` if you declined to"
> `abstain_reason`: "one sentence when abstaining; null when translating"

The validator (`schema.py:772-786`) enforces only *form*: an abstention needs a reason and needs
every list empty. It never asks whether abstention was *warranted*.

### 1.4 Where it is silent — three named gaps

**GAP-1 — no test, only a trigger list, and the list omits the dominant real case.**
The four triggers name *headings, goals, examples, inexpressible content*. They do **not** name the
category that in fact accounts for almost every disputed clause: **a true descriptive statement
about the system or about the document**. Of the 19 ABSTAINER-RIGHT clauses, none is a heading,
few are goals, two are examples — the rest are ordinary declarative facts:

* `l1_170_n009` — "OpenAI is training its models to align to the principles in the Model Spec."
* `l1_170_n092` — conversations may be truncated, "the user may not be aware of this truncation".
* `l1_170_n044` — "Root-level instructions are mostly prohibitive…"
* `l1_170_n061` — "The levels of authority are further explored… in a later section."
* `l171_426_n004` — "The heading 'Follow all applicable instructions' carries root authority…"

Every one is *true*, *expressible as a fact*, and *not a heading, goal, or example*. Nothing in the
prompt tells the model these are out of scope. They fail no stated trigger.

**GAP-2 — the schema supplies a legal, attractive landing spot for exactly these spans.**
`ontology` is described as "the clause's non-deontic classification facts — what something IS,
never what may be done about it", and the coherence check (`schema.py:800`) accepts a module whose
only content is `ontology`:

```python
if not (self.asserts or self.defines or self.ontology or self.beats
        or self.concepts):
    errs.append("translated but emitted no assertion, definition, superiority "
                "or ontology fact — that is an abstention that did not say so")
```

A descriptive span maps onto `ontology` perfectly. The schema therefore does not just *permit*
translating a non-normative span, it offers the natural slot for it — and the resulting module is
indistinguishable from a good one to every downstream check.

**GAP-3 — the worked examples teach the opposite of the prose, on two of the four triggers.**
This is the sharpest finding and it is not a matter of interpretation.

*System prompt line 426, `## A heading-authority node — small is correct`:*

> Node `l3995_4164_n001` establishes only that the rules under a heading carry
> guideline authority. The module is tiny, and that is right — a node that establishes
> section metadata yields a classification, not obligations. Do not inflate it.

…followed by a full `"outcome": "translated"` module. **`00_task.md` says a section heading is an
abstention trigger; the worked example translates a section-heading node and calls it correct.**

And `l3995_4164_n001` is *also* on the abstained list in
`runs/20260810-225427-together-deepseek-v4-flash/l3995_4164_n001.json`:

> "The clause is a heading that assigns guideline authority to the rules beneath it. It does not
> itself impose an obligation, permission, or prohibition…"

The same model, the same clause, both answers — because the prompt gives both answers.

*System prompt line 469, `## A worked-example node — translate the lesson, not the dialog`:*

> Node `l4251_4571_n029` is a document example (a good/bad response pair). Its lesson is a
> preference, so `prefer` is the status — collapsing it into `forbid` would be a hollow stub.

…again `"outcome": "translated"`. **`00_task.md` says "it is an example" → abstain.**

Then, at line 537, the prompt states the rule that reconciles nothing:

> Many graph nodes are commentary, headings, or document examples. A hollow-but-honest
> module (like the heading node above) or a clean abstention (like this one) are both
> better than an invented obligation.

**"Both" is the criterion.** On a heading or an example the prompt explicitly authorises either
answer and gives no rule for choosing. This is the same class of defect as `DEBUGGING_TIPS` 19
(the worked example teaching the opposite of the prose on `requires`/`inputs`) — second occurrence.

---

## 2. Method — the blind adjudication

Pre-registration: `abstention_boundary/PREREG_abstention.txt`, written and on disk **before the
first draw was dispatched** and before the id→model-choice key was opened. It fixes the materials,
the question, the escalation rule, the three buckets, the primary endpoint with its reading, and
four falsifiers.

| | |
|---|---|
| items | **53**, opaque ids `X000`–`X052`, order shuffled under seed 777 |
| blinding | each item shows only the node's `ESTABLISHES` claim and the verbatim `SOURCE TEXT` block (incl. the `[node narrows this span to: …]` line). No model output, no outcome, no model name, no stratum. Key sealed in `KEY_do_not_open_until_judged.json`, opened only after all 175 judgements were on disk |
| strata (blind to adjudicator) | `cohort17` (17) the `undeclared-body-name` cohort; `ds_abstain` (12) DeepSeek's 12 abstentions in the 08-14 100-clause pair; `ds_success` (24) random sample (seed 20260815) of the 69 `translated` modules, disjoint from the dispute set — judged in the *same* shuffled pool so stratum cannot be inferred |
| adjudicator | one isolated local Haiku subagent per (item, draw); sees one file, answers once, reads nothing else. **Never batched** |
| draws | 3 per item; the 8 items that split 2-1 escalated to 5 per the pre-registered rule. **175 draws total** |
| decision rule | 3/3 → that verdict; 5-0 or 4-1 → majority; 3-2 → AMBIGUOUS |

**Provenance.** The 08-14 pair (`…163457` + `…173322`) reproduces the headline exactly:
81 final modules = **69 translated + 12 abstained**, plus 19 unrepaired. Dispute set = the 17
cohort clauses + those 12 abstentions = 29 distinct clauses.

### 2.1 Falsifiers — all checked, none fired

* **F1 (instrument does not discriminate).** **PASSED, decisively.** `ds_abstain` scores 11/12 = 92%
  NON-NORMATIVE; `ds_success` scores 7/24 = 29%. **Fisher p = 0.00094.** The adjudicator separates
  the classes it is being asked to separate. This is the single most important control here: it is
  what licenses reading the 29% as signal rather than noise.
* **F2 (degenerate answering).** PASSED. Over all 175 draws: 84 NORMATIVE / 91 NON-NORMATIVE. Not a
  constant.
* **F3 (option-order artifact).** Not triggered — the NORMATIVE rate is 48%, far below the 90%
  threshold that would have required a reversed-order re-run.
* **F4 (Haiku is not DeepSeek).** Standing. Every number here is evidence about **the instruction**,
  read by one model. See §6.

---

## 3. The three-way split

**Dispute set, n = 29.**

| bucket | n | % | Wilson 95% |
|---|---|---|---|
| **ABSTAINER RIGHT** — span is non-normative, a model produced a module | **19** | 66% | [47%, 80%] |
| **TRANSLATOR RIGHT** — span is normative, Haiku abstained | 2 | 7% | [2%, 22%] |
| **GENUINELY AMBIGUOUS** | **2** | **7%** | **[2%, 22%]** |
| (control) normative, both models translated | 6 | 21% | [10%, 38%] |

**The ambiguous bucket is small: 2 of 29, 7%, CI [2%, 22%].**
* `l1_170_n084` — hidden chain-of-thought: describes a capability *and* states it is not exposed
  (2 NORMATIVE / 3 NON-NORMATIVE).
* `l1_170_n018` — "OpenAI is committed to upholding high-level principles…" — a commitment that is
  also a preamble (3 / 2).

**By stratum:**

| stratum | NON-NORMATIVE | Wilson 95% |
|---|---|---|
| `ds_abstain` — DeepSeek's 12 abstentions | **11 / 12 = 92%** | [65%, 99%] |
| `cohort17` — the udbn cohort | 8 / 17 = 47% | [26%, 69%] |
| `ds_success` — sample of the 69 successes | 7 / 24 = 29% | [15%, 49%] |

**Not one of DeepSeek's 12 abstentions was adjudicated NORMATIVE.** Eleven are clean
non-normative, one ambiguous. The abstentions were not a coverage failure; they were correct.

**Haiku's abstentions are also mostly right, with two exceptions.** On the cohort17 clauses where
Haiku abstained and the verdict is NORMATIVE — `l1_170_n086` (2/3 abstained) and `l1_170_n023`
(1/3) — Haiku under-translated. That is the whole TRANSLATOR-RIGHT bucket: 2 clauses.

**Corpus composition is a property of the model, and the direction is now known.** Of the 17-clause
cohort where DeepSeek produced a module every time, blind adjudication says 8 should not have had
one. Haiku abstained on 5 of those 8. The portability concern is real, and the *permissive* model
is the one that is wrong.

---

## 4. Did DeepSeek over-translate elsewhere? Yes.

ABSTAINER-RIGHT is non-empty, so the secondary endpoint is live. Stratified estimate over the 69
`translated` modules of the 08-14 pair:

| stratum | | NON-NORMATIVE |
|---|---|---|
| A — census: cohort17 clauses that ended `translated` | 10 | **5 / 10** |
| B — random sample of the remaining 59 | 24 | **7 / 24 = 29%** [15%, 49%] |

**Point estimate: 5 + 59 × 0.29 = 22.2 of 69 = 32%.**
**95% CI (from stratum B): [13.8, 34.0] modules = [20%, 49%].**
Counting the 3 AMBIGUOUS sampled modules as questionable raises it to 29.6 / 69 = **43%**.

The seven non-normative modules in the sample, verbatim:

| clause | the span that got a module |
|---|---|
| `l1_170_n001` | "The Model Spec outlines the intended behavior for the models that power OpenAI's products…" |
| `l1_170_n007` | "OpenAI is training its models to align to the principles in the Model Spec." |
| `l1_170_n044` | "Root-level instructions are mostly prohibitive, requiring models to avoid behaviors that…" |
| `l1_170_n061` | "The levels of authority are further explored from the model's perspective in a later section." |
| `l1_170_n075` | "…for example, the system may indicate to the model that it should follow the Under-18 Principles…" |
| `l1_170_n092` | "…the conversation will be truncated… the user may not be aware of this truncation…" |
| `l171_426_n004` | "The heading 'Follow all applicable instructions' carries root authority, so every rule in this section is a root-level instruction." |

**This is the silent quality defect, and it is worse than the coverage one.** `l1_170_n007` is a
statement about OpenAI's training programme; as a module it enters behaviour matching as if the
document had *told the assistant* something. `l171_426_n004` is a claim about where a heading sits
in the document; as a module it asserts root authority over a whole section from a span that only
*describes* the layout. None of schema, link or readback can see this — a faithful encoding of a
true descriptive sentence is a *correct* encoding of the *wrong kind of sentence*.

Note the contrast with the coverage story the work order started from: the 12 abstentions cost
~12 modules and were right; the 69 successes contain ~22 modules that should not exist. **The
pipeline's quality problem is roughly twice the size of its coverage problem, and points the
other way.**

---

## 5. Verdict, honestly reported against the pre-registration

The pre-registered reading has two branches, and the result lands on the **second**:

> * AMBIGUOUS ≥ 20% with Wilson lower bound ≥ 10% → the criterion is UNDERSPECIFIED…
> * AMBIGUOUS < 20% AND one model's choice is the minority verdict on a clear majority of the
>   dispute set → NULL on underspecification; report "one model is simply wrong" and drop the
>   prompt change.

AMBIGUOUS is 7% [2%, 22%] — below 20%. DeepSeek's choice (translate) is the minority verdict on
19 of 29 = 66% of the dispute set — a clear majority. **The pre-registered branch therefore reads:
NULL on the ambiguity form of underspecification; the permissive model is systematically wrong.**

**I report that verdict as pre-registered. I also record that the pre-registered dichotomy was
mis-specified, and say so rather than quietly re-reading it.** "One model is simply wrong" and "the
instruction fails to cover the case the model gets wrong" are not exclusive, and this result is
both. The evidence for the criterion gap is **not** the ambiguity count — it is §1.4:

* the four named triggers do not name the category that produces 19 of the 19 errors;
* the schema's `ontology` slot legally absorbs exactly that category;
* and the worked examples **translate** a heading node and an example node, contradicting two of
  the four triggers in the same prompt, on a clause the production model abstained on elsewhere.

That is a documentary finding about the prompt bytes. It does not depend on the adjudication at
all, and no ambiguity threshold can refute it.

**So: the criterion is underspecified — but the diagnosis is contradiction and omission, not
vagueness, and the deciding evidence is the prompt text, not the disagreement rate.** The
adjudication's job was to establish which side of the line is wrong, and it did: the permissive
side, by 19 to 2.

---

## 6. Which findings need a DeepSeek A/B before production trust

| finding | transfers? |
|---|---|
| §1 the prompt's contradiction (heading/example triggers vs worked examples) | **model-independent.** A fact about bytes on disk |
| §3 the 66/7/7 split, §4 the 32% over-translation rate | **the judgements are Haiku's.** The *clauses judged* and the *model choices joined to them* are DeepSeek's real production data, so the split is about DeepSeek's behaviour — but the ground truth is one model's reading. A frontier or human adjudicator on the same 53 blind items would settle it, and costs nothing but a different local model |
| F1's discrimination (p = 0.00094) | Haiku-only, but it is the control that makes the rest readable, and it passed by three orders of magnitude |
| the proposed diff's *effect* (§7) | **entirely unmeasured on DeepSeek.** No prompt change should land without the A/B in §7.3 |

**Cheapest next step, still zero spend:** re-adjudicate the same 53 blind items with a different
local model. If ABSTAINER-RIGHT stays above 50%, the finding is not an artifact of Haiku's
conservatism — which is the one alternative explanation this document cannot rule out from inside.

---

## 7. PROPOSED diff — not applied

`prompt/00_task.md`, `prompt/10_output_format.md`, `prompt/20_worked_example.md` and `schema.py`
are guard-watched. **Nothing below has been written to any file.** `git status` on those four paths
is unchanged.

### 7.1 The change — `prompt/00_task.md`, replacing the `## Abstention is a real answer` section

```diff
 ## Abstention is a real answer

-If you cannot translate this clause faithfully — it is a section heading, it states a goal rather
-than a condition, it is an example, or its content is not expressible as rules — **abstain and give
-the reason**. Producing something that looks like a translation is worse than declining. The
-abstention rate is a signal we want, not a failure we penalise.
+Before you translate, apply this test, in this order:
+
+**Does this span tell someone what to DO — or does it tell a reader what IS?**
+
+A span earns a module only if it states an obligation, a permission, a prohibition, a priority
+between them, or a definition that such a rule would use. If instead it *describes* — the system,
+the document, the organisation, or the world — it gets an abstention, however true and however
+precisely stated it is.
+
+**Abstain** when the span is:
+
+* a section heading, or a statement about where something sits in the document;
+* a statement about the document itself — its purpose, scope, structure, maintenance, or what a
+  later section will cover;
+* a statement about what the organisation is doing, intends, aims at, or is committed to;
+* a description of how the system behaves as a matter of fact (what it can do, what happens to a
+  conversation, what a model is trained on) with no obligation attached;
+* an example, or a label introducing one;
+* content not expressible as rules.
+
+**A true sentence is not thereby a translatable one.** "The Model Spec outlines the intended
+behavior for the models", "OpenAI is training its models to align to the principles", "the
+conversation will be truncated" are all true and all describe rather than govern. A module built
+from one of these passes every check we run and then enters behaviour matching as if the document
+had *told the assistant* something. That is the worst outcome available here — worse than a
+missing module, because a missing module is visible and a wrong one is not.
+
+**Do not use `ontology` as a way to translate a descriptive span.** `ontology` is for the
+classification facts a *rule in this module* needs. If the module's `asserts`, `defines` and
+`beats` are all empty and the `ontology` entries merely restate what the span says, that is an
+abstention wearing a module's clothes. Abstain instead.
+
+Producing something that looks like a translation is worse than declining. The abstention rate is
+a signal we want, not a failure we penalise.
```

### 7.2 The two consequential edits — the worked examples must stop contradicting this

The prose above is worthless while the same prompt shows a heading node and an example node being
translated. `node_worked_example.md` is **not** guard-watched, so these are applicable — but the
work order's standing rule is that nothing lands there without a measured result, and §7.3 is that
measurement. Both are recorded here as proposals only.

1. **`## A heading-authority node — small is correct`** (`l3995_4164_n001`). Either convert this
   exemplar to an **abstention** — which is what DeepSeek itself did on this clause in
   `runs/20260810-225427-…` — or keep it and **delete "a section heading" from the trigger list**,
   replacing it with an explicit carve-out: *a heading that assigns authority to the rules beneath
   it does yield a classification; a heading that only names a topic does not.* The current prompt
   asserts both and chooses neither. **Choosing is the fix; which way is chosen matters less than
   that the prompt stop saying both.**
2. **`## A worked-example node — translate the lesson, not the dialog`** (`l4251_4571_n029`). Same
   defect on the "example" trigger. Either drop "it is an example" from the list, or replace this
   exemplar with an abstention.
3. Delete the line **"A hollow-but-honest module … or a clean abstention … are both better than an
   invented obligation."** It is the sentence that licenses the coin flip.

### 7.3 The measurement that would justify landing any of it

A randomised DeepSeek A/B on the abstention decision, arms interleaved, one call per task, clause
order shuffled, ≥5 draws per clause per arm — never batched.

* **Cohort:** the 29 dispute clauses plus the 24 sampled successes = 53 clauses, already built and
  blind-adjudicated here, so the ground truth exists before the spend.
* **Endpoint (pre-register before spending):** agreement between the model's translate/abstain
  choice and the frozen blind verdict. Arm A (stock) baseline from this data: DeepSeek translated
  19 spans that should have been abstained and abstained 0 that should have been translated.
* **Sizing** (`DeepSeek-V4-Flash-0731`, $0.14/$0.28 per Mtok; arm-A system 36,820 chars, arm-B
  ~+1,400, user mean 2,123, answer mean 2,424): 5 draws × 53 clauses × 2 arms = 530 calls ≈ **$0.95**.
  A 3-draw screen is 318 calls ≈ **$0.57**.
* **Against the ceiling** ($8.50, ~$2.15 used) this is affordable. **It is not authorised and I have
  not spent it.**

### 7.4 Which direction this moves the line, and what it costs

**It moves the line toward MORE abstention.** Stated plainly:

* **Coverage cost:** ~22 of the 69 current successes (32%, CI [20%, 49%]) would become abstentions.
  Corpus-wide, if the 08-14 pair is representative of the 773 nodes, that is on the order of
  **150–170 modules that today exist and would stop existing.**
* **What is actually lost:** close to nothing that a query can use. These modules encode true
  descriptive sentences; they contribute concepts and edges, but the obligations they appear to
  license are not in the document.
* **What is gained:** the abstention rate becomes a measurement of the document rather than of the
  model, which is the property the method's portability claim rests on — and behaviour matching
  stops consuming ~22 modules that assert things the spec never said.
* **The honest risk:** a tighter criterion will also suppress genuine borderline normative spans.
  The TRANSLATOR-RIGHT bucket (2/29) and the AMBIGUOUS bucket (2/29) are the population at risk,
  ~14% of disputed clauses. The A/B in §7.3 measures exactly this, because it scores *both*
  directions of error against a verdict frozen before the spend.

**Do not read the coverage drop as a regression.** Per `ITERATION_LOOP.md`'s anti-cheat perimeter,
the current 69 is inflated by ~22 modules that pass the checks without being true of the document;
the number to compare against after the change is not 69 but ~47.

---

## 8. Reproduction

In `_debug_gen11/abstention_boundary/`:

* `PREREG_abstention.txt` — pre-registration, written before the first draw
* `items/X000.txt … X052.txt` — the 53 blind items as the adjudicators saw them
* `judgements/X0nn_dk.txt` — all 175 raw verdicts, one file per isolated draw
* `KEY_do_not_open_until_judged.json` — the sealed id → clause / stratum / model-choice key
* `tally3.json` — per-item vote counts at the 3-draw stage (identifies the 8 escalated items)
* `joined.json` — the post-key join: item, clause, stratum, DeepSeek outcome, Haiku draw counts,
  final verdict, votes
* `ds_pair.json` — the 81 final modules of the 08-14 pair (69 translated / 12 abstained)

Cohort recomputed from `fixc_replication/cohorts.json` (`sole_udbn`, n=17); Haiku per-clause draw
counts from `fixc_replication/instr/scored.json` (51 stock draws).
