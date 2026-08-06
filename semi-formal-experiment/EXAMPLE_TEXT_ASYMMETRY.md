# Example dialogues: the tool reads them, the panel's passage list does not

**Recorded 2026-08-05.** A narrow, measured fact plus an explicit correction of a larger claim
that was drafted and withdrawn.

## ⚠️ Correction, first — because the wrong version existed briefly

An earlier draft of this file claimed the panel judged example passages **without context**, and
therefore that disagreements on 31% of the universe were "not comparable". **That was wrong.**

The panel was given the **entire spec** and asked to score each passage against it. The harness
says so (`engine/panel/whole_doc.py:18-20`): *"You are given the ENTIRE document, split into
numbered passages in reading order; use the full document and its structure as context when
grading each passage."* A judge reading

```
[230] (§ no_erotica_or_gore) Example: discussing sex and reproductive organs in a
                             scientific or medical context
```

has the governing rule two passages earlier, the section heading, and the whole surrounding
document. That is a coherent, well-posed task, and nothing here says the panel judged blind.

The error came from generalising a defect in **my presentation to a human adjudicator** into a
defect in the benchmark. It is not one.

## The fact that does hold

The two sides have asymmetric access to the *dialogue text itself*:

| | example content | mean length |
|---|---|---|
| clause (what the **tool** scores) | title **plus** the worked dialogue — `<user>`/`<assistant>` turns, GOOD/BAD comparisons | **820 chars** |
| passage (what the **panel's list** contains) | the title line only | **53 chars** |

Verified: **0 of 589** passages contain `<user>` / `<assistant>` / `~~~xml`; **183 of 593**
clauses do; 183 passages carry `exampleBlock: True` and those are exactly the title-only ones.

**What this is worth is unmeasured, and plausibly small.** The judges had the governing rule and
the section; an example titled *"discussing sex and reproductive organs in a scientific or
medical context"*, sitting under a rule about erotica with a stated medical carve-out, may be
fully determined by its context without the dialogue. The dialogue would matter only where it
carries something the surrounding rule does not — which is an empirical question nobody has
asked.

**The measurement that would settle it:** recompute the tool-vs-panel gap over the non-example
subset alone and compare with the full-universe figure. If the gap is materially smaller off
the examples, the asymmetry is doing work; if not, it is a curiosity. Not yet run.

## What the semi-formal side does with context (asked 2026-08-05)

The annotation pipeline already handles the problem this raises, and did so deliberately.
`annotate.py:690`:

> *The nearest earlier clause in the same section that is not itself an example — or None.
> An example clause read alone ("**Example**: the assistant declines") says nothing about which
> rule it illustrates, and examples are 39% of the relevance signal, so the annotation of an
> example is only as good as the context it is given.*

So when an example clause is annotated, the annotator is shown the nearest preceding
non-example clause in the same section, labelled *"NOT to be annotated"*. Context influences the
atoms.

**Three limits, which bear directly on the frontier-layer design:**

1. **Context shapes the annotation but is not RECORDED in it.** The preceding clause influences
   which atoms get written and then disappears. Nothing in the artifact says *this example
   illustrates m0274*. The relation cannot be queried, cannot be audited for whether the
   annotator used it correctly, and a consumer cannot distinguish a context-informed atom from a
   self-evident one. **Candidate slot for the frontier layer: an explicit `illustrates` edge.**
2. **The selection is a heuristic, not a semantic choice** — nearest preceding, same section,
   non-example. If the governing rule sits two clauses back, or in a section header, or the
   example illustrates an *exception* to the preceding rule, the anchor is wrong and nothing
   detects it.
3. **It is one-directional.** The rule clause gets no signal that examples elaborate it.

A second, cruder context path exists at scoring time — the section channel credits every clause
from its section's top-3 neighbours — but that is positional smoothing, not semantics, and S4
exists to gate it precisely because it fires without atom-level evidence.

## The finding that stands on its own

The human adjudication protocol presented item 1 as passage text plus behaviour definition, and
that was **defective**: the judges had a document, the human had one line. The response —
*this is not enough to classify; in one surrounding context it is clearly relevant, in another
it is a stretch* — was a correct diagnosis of the instrument, and it needs no benchmark defect
behind it to be worth acting on.

**Protocol amendment** (`HUMAN_ADJUDICATION_PROTOCOL.md`): presentation must match the panel's
condition — passage text, its § section path, its position in reading order, and context
available on request, with the request recorded. *What context a decision required* is itself
slot evidence for the feasibility study: a decision that needs document-level context is a
constraint on any per-passage representation.

Item **H001** is burned and its answer retained as the above.

## Reproduction

```bash
cd semi-formal-experiment
.venv/bin/python -c "
import benchmark as B, json
ps = B.passages(B.load_true_panel()['helpfulness'], 'openai')
cl = json.load(open('modelspec_clauses.json'))['clauses']
print('passages with dialogue:', sum('<user>' in p['quote'] for p in ps), 'of', len(ps))
print('clauses  with dialogue:', sum('<user>' in c['quote'] for c in cl), 'of', len(cl))
print('exampleBlock passages :', sum(1 for p in ps if p.get('exampleBlock')))
"
```

Prompt construction: `engine/panel/whole_doc.py:56-60`. Annotation context:
`annotate.py:690-712`, rendered at `:723-726`.
