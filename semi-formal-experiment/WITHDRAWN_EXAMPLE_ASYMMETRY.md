# WITHDRAWN — "the panel and the tool were not looking at the same document"

**Withdrawn 2026-08-06. The claim was wrong. This file exists so the claim is not
re-derived, and so anyone who saw either earlier version can find out what happened.**

## What was claimed, in two successively weaker versions

**v1 (2026-08-05):** the panel judged example passages *without context*, so disagreement
on 31% of the universe was "not comparable". **Withdrawn same day** — the panel was given
the entire spec and instructed to use its structure as context.

**v2 (2026-08-05):** a narrower survivor — the tool's clause carried the worked dialogue
(820 chars mean) while the panel's passage list carried only the title (53 chars), so the
two sides had asymmetric access to the example *text*. **Withdrawn 2026-08-06. Also wrong.**

## Why v2 was wrong

I measured `benchmark.passages()`, which reads the stored evaluation artifact
`data/panel-coverage.json`. The prompt actually sent to the judges is built by
`engine/panel/whole_doc.py` from **`harness.passages()`**, a different function that
re-segments the spec source.

Run them side by side on the same locator (`model-spec@2025-12-18 > #definitions > ¶8`):

| | text | length |
|---|---|---:|
| sent to judges (`harness.passages`) | ``**Example**: … rendered as follows: ~~~xml <assistant recipient="python"…> import this </assistant> ~~~`` | **153** |
| stored in the artifact (`benchmark.passages`) | `Example: in the Model Spec, messages will be rendered as follows:` | **65** |

`harness.passages('model-spec')` returns 589 passages of which **183 contain dialogue
markers**. The judges saw the dialogues. There is no asymmetry.

**The error:** I mistook a property of the archive for a property of the experiment, and
did it twice in the same area after being corrected once. The second time I still had not
checked which `passages()` the prompt builder called.

## The residue, which is real and is a different question

**The evaluation artifact does not store what the judges were shown.** The stored quote is
truncated at the code block.

This does not affect the panel's judgments — those were made on the full text. It does mean
anything reading `panel-coverage.json` downstream is working with truncated passage text,
including the passage→clause join the tool's scoring runs through
(`inventory.match_passage*` matches on the stored quote). Whether truncation changes any
join is **unmeasured**, and is a narrow, checkable question:

```
for each passage: does the truncated quote join to the same clause set as the full text?
```

That is worth running. It is not evidence about the panel.

## Standing instruction

Before claiming anything about "what the judges saw", read
`engine/panel/whole_doc.py:56-60` and follow `h.passages` into
`engine/panel/harness.py:152`. The stored coverage artifact is a downstream archive, not
the experiment's input.
