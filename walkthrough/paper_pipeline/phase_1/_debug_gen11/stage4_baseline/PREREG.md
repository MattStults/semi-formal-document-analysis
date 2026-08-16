# Stage-4 first correctness baseline — written BEFORE the run

Not a hypothesis. This is a MEASUREMENT; nothing about the outcome is
pre-registered. What is fixed in advance is the instrument, the command, the
price and what will be reported, so that none of them can be chosen after
seeing the numbers.

## Instrument

* Driver: `_debug_gen11/stage4_baseline/stage4_driver.py` (new; the missing
  piece — `seats.plan_clause`/`seats.run_clause` already existed).
* Target run: `resolve_runs/graph_v2/translation_sample/runs/20260815-130831-together-deepseek-v4-flash`
* Corpus for clause text: `resolve_runs/graph_v2/node_corpus_all.json`
  (NOT `node_corpus.json`, which is the pinned 15-node test fixture).
* Gloss table + provider spans: `link_nodes.merged_gloss` /
  `link_nodes.provider_texts`, **fenced to this one run** rather than
  `link_nodes.gather()`'s newest-run-wins across all 18 runs. A seat judging
  run A's module against run B's glosses measures neither run.
* Model: `deepseek-ai/DeepSeek-V4-Flash-0731` via together.ai, defined inline
  in `config_corpus_all.json` (`together-deepseek-v4-flash`), $0.14/$0.28 per
  Mtok. NOT frontier. The seat is documented as validated at
  small-model/frontier parity.
* Seat client departures from the stage-1 client, each deliberate:
  `format_forcing json_schema -> json_object`, `max_tokens -> 4096`,
  envelope -> text. (These are `READBACK_SMOKE.md` gap 2, still open; this
  driver owns them now.)
* `discrimination=None`: no stage-3 probe was run, so **every 4d `covered`
  will be stamped `unsupported`**. That is the honest state, not a defect of
  this run — an unavailable check must not read as a passed one.

## The population, before any call

* 88 clause ids attempted by the translation run (`run.json:results`).
* 87 modules on disk — `l1_170_n034` never produced one (unrepaired,
  `schema-breach` on an unsafe variable; it is in the graveyard).
* 82 `translated`, 5 `abstained` (`l1_170_n014`, `n061`, `n063`, `n076`,
  `n079`) — an abstention reaches no seat.
* 81 reach a seat. `l1_170_n083` is refused at `plan_clause`: *"the clause
  carries a stage-3 expected verdict"*.

**So the denominator for this baseline is 81, not 88, and the 7 that fell out
fell out before stage 4 could say anything about them.**

## Cost, printed before anything is sent

    clauses reaching a seat : 81
    seat calls              : 324  (4 per clause)
    judgements requested    : 2182
    input tokens            : 332,957
    WORST  (every reply at the 4096-token cap) : $0.4182   <- gates
    likely (40 out-tok/judgement, ASSUMPTION)  : $0.0711
    ceiling for this task                      : $0.6000

$0.4182 < $0.60, so the run proceeds. The gate reads the WORST case, never
the likely one.

## Command

    ../../../semi-formal-experiment/.venv/bin/python \
      _debug_gen11/stage4_baseline/stage4_driver.py --live --budget 0.60

(preceded by a one-clause `--ids ... --limit 1` smoke to prove the client
seam, which has never been driven at scale.)

## What will be reported, decided now

1. Per clause: each seat's verdict vector, the pooled `unclear` rate and its
   denominator, and every `unfaithful` / `unlicensed` / `not-conveyed` /
   `not-as-meant` with the seat that returned it.
2. The headline: of the clauses that reached a seat, how many drew no defect
   verdict from any seat and how many drew at least one.
3. `unclear` is reported as its own answer. It is NOT collapsed into pass or
   fail, in either direction.
4. Instrument failures — a seat refusing, an unparseable reply, a
   `NotAdjudicated` — are reported AS A RATE and as a property of the
   instrument. Nothing is retried into looking better.
5. `checks.polarity_findings` over the same modules, and the overlap with
   what stage 4 found. Free, deterministic, run in the dry pass already.
6. Whether the defect classes resemble the Opus read of 25 modules from
   `20260815-124836` (`_debug_gen11/spotcheck_semantic/verdicts.json`,
   13 defective / 25). Different clauses — this is a comparison of CLASSES,
   never a join.

## Known in advance, so it cannot be presented as a finding later

* `checks.polarity_findings` fires on exactly **1** entry in **1** clause
  (`l1_170_n053`, `asserts[0]`, `impose_restrictive_rules(D)`) across these
  81. The 9-entries-across-7-clauses figure is CORPUS-WIDE; this run is 73
  nodes from `l1_170` and 8 from `l171_426`, and most of the corpus-wide
  polarity hits live elsewhere. So the polarity overlap test here has an
  n of 1 and can only ever be suggestive.
* Mean clause echo over the 81 is 0.431; the declared echo level is what
  decides the `high-echo` stamp, and 4b/4d verdicts above it are recorded
  non-evidential by `stamp_evidential`. That stamping is expected and is not
  a driver bug.
