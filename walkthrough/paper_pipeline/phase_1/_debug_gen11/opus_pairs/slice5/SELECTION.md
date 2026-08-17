# SELECTION — slice 5 of 5

Deterministic, no hand-picking. Reproduced by the snippet at the bottom.

## The universe

`resolve_runs/graph_v2/node_corpus_all.json`, key `clauses`, field `id`.
This is the graph node corpus of record for the `config_corpus_all.json` runs —
the same corpus `_debug_gen11/ds_opus_loop/loop.py` loads. Its `id` order as
stored is **not** sorted (`corpus order == sorted: False`), so the sort below is
applied explicitly rather than assumed.

## Exclusions (the two existing cohorts)

* **ds_opus_loop cohort** — the module ids in `_debug_gen11/ds_opus_loop/out/*.json`,
  excluding the `.transcript`/`.raw`/`.turn` sidecars. 17 ids.
* **reference_set cohort** — the filenames in `_debug_gen11/reference_set/modules/*.json`.
  25 ids. *(Filenames only were read. No file inside `reference_set/` was opened,
  here or by any subagent, per the fence.)*
* The two cohorts **overlap in 5 ids**, so the excluded union is **37**, not 42.

No other exclusion was applied. In particular `resolve_runs/graph_v2/corpus_exclusions.py`
was deliberately **not** consulted: five slices are partitioning one list and an
exclusion only one slice applies would break the partition. If a selected node
turns out to be on that list, that is a finding to report, not a reason to reselect.

## Eligible set

**736 nodes** (773 total − 37 excluded).

## The stride

Slice 5 = `eligible[4::5]` in **plain lexicographic `sorted()` order of the id
strings** (Python `sorted()`; not natural/numeric order — `l1001_…` sorts before
`l1108_…` and both before `l1_170_…`). The stride sequence has 147 members; the
first 5 are taken.

| # | index in eligible | id | kind | shape |
|---|---|---|---|---|
| 1 | 4  | `l1001_1107_n006` | conditional | prohibition, PROVIDES a name |
| 2 | 9  | `l1001_1107_n011` | meta | **span headed `**Example**`** — GOOD/BAD pair |
| 3 | 14 | `l1108_1367_n003` | conditional | prohibition + unresolved cross-ref |
| 4 | 19 | `l1108_1367_n008` | conditional | prohibition; **narrowing truncated mid-phrase** |
| 5 | 24 | `l1108_1367_n013` | conditional | **section heading only**; declares authority |

Nothing about that table entered the selection — it is recorded after the fact
so a reader can see what the deterministic rule happened to hand us.

## Spans

Rendered with the production renderer, not by hand:
`translate.build_user(row, rows, cfg)` under
`resolve_runs/graph_v2/config_corpus_all.json`, written to
`_debug_gen11/opus_pairs/slice5/spans/<id>.prompt_user.txt`. No clause in the
slice resolved any cross-reference; two carry an unresolvable one
(`assume_objective_pov`, `avoid_hateful_content`).

## Reproduce

```python
import json, glob, os
ids = [x['id'] for x in json.load(open('resolve_runs/graph_v2/node_corpus_all.json'))['clauses']]
ds  = {os.path.basename(p)[:-5] for p in glob.glob('_debug_gen11/ds_opus_loop/out/*.json')}
ds  = {i for i in ds if '.' not in i}
ref = {os.path.basename(p)[:-5] for p in glob.glob('_debug_gen11/reference_set/modules/*.json')}
elig = sorted(i for i in ids if i not in (ds | ref))
assert len(elig) == 736
picked = elig[4::5][:5]
```
