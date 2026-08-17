# SLICE 2 — clause selection, recorded before any drafting

## The corpus of record

`resolve_runs/graph_v2/node_corpus_all.json` — the graph node corpus that
`resolve_runs/graph_v2/config_corpus_all.json` points `corpus.path` at. This is
the same corpus both existing cohorts were drawn from: **every id in
`_debug_gen11/ds_opus_loop/out/` and in `_debug_gen11/reference_set/modules/`
resolves in it, with none missing.** That check is the evidence the corpus is
the right one; it was run, not assumed.

⚠️ Not `node_corpus.json` — that file is the 15-node sample used by
`config_graph_nodes.json` and its ids (`l1_170_n028`, `l1108_1368_n004`) are a
different segmentation from the cohorts'.

## The exclusion

* `ds_opus_loop` cohort: 17 ids (basenames of `out/*.json`).
* `reference_set` cohort: 25 ids (basenames of `modules/*`).
* Union: **37** — the two cohorts overlap by 5.

⛔ The reference-set ids were obtained by **listing filenames only**. No file
under `reference_set/`, `redraw_adjudication/` or `spotcheck_semantic/` was
opened, by me or by any subagent, at any point.

## The eligible set

Total nodes in the corpus: **773**. Eligible after removing the 37: **736**,
sorted lexicographically by node id.

## The slice rule, as applied

Slice 2 = **every 5th eligible node starting at index 1**, first five taken —
i.e. eligible-sorted indices **1, 6, 11, 16, 21**. Slice *k* takes indices
*k−1, k+4, k+9, k+14, k+19*, so the five slices interleave and cannot collide.
Nothing was hand-picked.

| # | eligible index | clause id | kind | span |
|---|---|---|---|---|
| 1 | 1 | `l1001_1107_n002` | conditional | L1004 |
| 2 | 6 | `l1001_1107_n008` | conditional | L1037 |
| 3 | 11 | `l1001_1107_n013` | meta | L1087–1106 |
| 4 | 16 | `l1108_1367_n005` | conditional | L1199 |
| 5 | 21 | `l1108_1367_n010` | conditional | L1112 |

Reproduce with:

```python
allids = [c["id"] for c in json.load(open("resolve_runs/graph_v2/node_corpus_all.json"))["clauses"]]
ex = {basenames of _debug_gen11/ds_opus_loop/out/*.json} | {basenames of _debug_gen11/reference_set/modules/*}
elig = sorted(i for i in allids if i not in ex)
slice2 = elig[1::5][:5]
```

## Spans

`spans/<id>.prompt_user.txt` were generated locally with
`translate.build_user` over `config_corpus_all.json` — zero API spend.
**Verified**: regenerating `l461_608_n015` this way reproduces the existing
`_debug_gen11/translate_opus/spans/l461_608_n015.prompt_user.txt` byte-for-byte
after strip, so the spans handed to my drafters are the production prompt-user
block and not a paraphrase of it.

`system_block.txt` is `translate.build_system` over the same config — the four
production prompt files in order (`00_task.md`, `10_output_format.md`,
`node_worked_example.md`, `30_failure_modes.md`). `response_schema.json` is
`schema.json_schema()`, the object the translator is format-forced to.

## Note on the draw

The lexicographic sort concentrates the draw in `l1001_1107` and `l1108_1367`.
That is a consequence of the stated rule, not a choice; it is recorded because
it bounds how far the slice's findings generalise across the document. Two of
the five drawn nodes are **abstention-trigger shaped** by `00_task.md`'s own
list — one is headed `**Example**:` (`l1001_1107_n013`) and one *is* a section
heading (`l1108_1367_n010`). That was luck of the draw, and it makes this slice
an unusually direct test of measured gap 1.
