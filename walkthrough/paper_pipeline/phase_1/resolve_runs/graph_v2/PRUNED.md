# PRUNED.md — evidence-prune manifest (2026-08-30)

Everything below was removed from the working tree at publication prep to keep
the repo reviewable. NOTHING IS LOST: full git history is retained, and each
entry pins the exact content by git object id (tree/blob sha at the pre-prune
commit). To restore any entry: `git checkout <pre-prune-commit> -- <path>`.
Reason per entry: superseded iteration runs, repair-stage intermediates, or
regenerable caches; the certified artifacts (ds7_production, the cited
translation runs, all behavior_pilot evidence) are retained in full.

| path | git object id | files | bytes |
|---|---|---|---|
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260810-203553-together-deepseek-v4-flash | a3581523b0781c0b5407934fe5bfd78e5c1c7096 | 54 | 416,495 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260810-205513-together-deepseek-v4-flash | 911b3e30b7ee2c4818bd44950aec179789c2bb4f | 60 | 402,097 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260810-212409-together-deepseek-v4-flash | 16af00b96f2a2feb1c572b2683fad325d12c8e79 | 81 | 475,581 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260810-213043-together-deepseek-v4-flash | 305650d3c24bcbd44b33d4f9f4946e0ac38321e1 | 64 | 406,996 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260810-214234-together-deepseek-v4-flash | 8bc1ade8855affd6ada935175607824f65927084 | 1 | 35,747 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260810-214437-together-deepseek-v4-flash | 618db50e39649c6212373b052e3c8fbfdbbcbccf | 82 | 433,706 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260810-215527-together-deepseek-v4-flash | 34fa4821a3135d91ff6c2891e13ea115d2e08188 | 70 | 465,370 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260810-225427-together-deepseek-v4-flash | 120e2885c75e35bfa30887a4e8e6b5f84f1ae66d | 72 | 492,413 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260810-234100-together-deepseek-v4-flash | b91b95ffcc5e0406570d9358830e93713c5a88b8 | 73 | 476,592 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260812-090344-together-deepseek-v4-flash | bec74a14e7978a5fea2ac070c3750a6c6f09fa64 | 87 | 401,845 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260812-133011-together-deepseek-v4-flash | 5847b826f435d4205fbf6142cc17dd2d291c2b3d | 1 | 36,820 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260814-163457-together-deepseek-v4-flash | 05dddbe9df1069231b4371ccc22f141c08df04d7 | 80 | 253,033 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260814-173322-together-deepseek-v4-flash | a08d40c5a7e582b26c5d8a0bb66cdf521dc21474 | 475 | 2,029,702 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260815-070038-together-deepseek-v4-flash | e9855f02ebbfedde61206dbc45a117fdcf03fccf | 388 | 1,984,483 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260815-130831-together-deepseek-v4-flash | 93e38d86b70dd205bf799180d516f33bf14cdd33 | 528 | 2,022,333 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260816-094505-together-deepseek-v4-flash | e4025c50f0127b5fa2aa77e3e093cc605650d05a | 147 | 698,676 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260816-130000-licence-fixup | f00a8219d73692fd632a583f6379c682021bd90b | 433 | 1,478,785 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260816-221213-together-deepseek-v4-flash | cfc19fd68ec4751312f27a6ea3fb6cef6797688b | 84 | 455,847 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260816-230554-together-deepseek-v4-flash | 008666737480d8057746bed85f646bb81730279f | 532 | 2,668,512 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260817-004238-together-deepseek-v4-flash | af4e26989c912eba8bc9462df44e7302c5a39907 | 538 | 2,537,168 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260817-005052-together-deepseek-v4-flash | ddbf26e4c4f1e87e1d32ded42693afbed69ae743 | 75 | 588,034 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260817-010032-together-deepseek-v4-flash | 329768e2ef3ba6d558cb0f5d9b18b9f39c9d542e | 33 | 260,895 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260817-020000-frontier-repair | 332a905380dcc0655d7ae92355ab38a0b2717525 | 25 | 91,420 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260817-071407-together-deepseek-v4-flash | c35e4e90dd5368fa0702f503e840bf62660f4459 | 541 | 2,229,759 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260817-080454-together-deepseek-v4-flash | d06999890afcc36139be1f7ab7917553ab248a7d | 541 | 2,220,074 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260817-082018-together-deepseek-v4-flash | e8376af7fb92fbd7a3dba9c699775239ae8f8c28 | 544 | 2,277,101 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260817-085233-together-deepseek-v4-flash | 236b7bbf36b2d50695525d0d042d2c16416b5226 | 544 | 2,184,145 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260817-090000-frontier-repair-2 | 032ee7b6bf6f41b6eeea9aaffc67591133476afc | 9 | 31,302 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260817-090314-together-deepseek-v4-flash | 52e6061a8e228f9dfa0d188339355fe362c76d61 | 388 | 1,902,739 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260817-100000-frontier-repair-3 | 2d528891bc44bbdffd095620dad8c71a7c6fabb7 | 12 | 42,578 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260817-110000-frontier-repair-4 | 28e8787f923541dffcb4c28a278298f8e8d20229 | 9 | 32,491 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260817-120000-frontier-repair-5 | 5cd03e06895b5d473db88f733294b4540d82f83c | 15 | 51,594 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260817-130000-frontier-repair-6 | 6984ffffbcccfa65d3eef0bf809b656fb97b6b57 | 12 | 48,492 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260818-200000-frontier-repair-7 | 790cc40036a026f25a40e00a7ba92c556830732b | 6 | 15,164 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260818-220000-frontier-repair-8 | 0db5addeb3785fb8f608eccee789ea2115a616f5 | 102 | 277,912 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/runs/20260818-233000-frontier-repair-9 | b590863b9f9ce9164cbb1baee0df56d5a9cb4b70 | 399 | 1,044,545 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/translation_sample/repair_graveyard | 5414a5e591635ba3beb2b9cd142d27213abe4c55 | 1519 | 7,640,861 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds1 | 112cd21c022cfbb92dc712666f489c97ce64f1c0 | 30 | 2,322,338 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds2 | 74eb9adba7d466ce593a78fcf2ae2bfc7c39c0f1 | 124 | 6,845,796 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds3 | 17854a59ecd3361c2a206fd7f6b6ea755ee65004 | 80 | 6,010,526 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds4 | 66443b9661829f3c41401712ccc03c9996204410 | 154 | 8,251,610 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds5 | 2c1d0d79bbf12fc89cf606927d52fb6b92b3b53c | 104 | 11,667,960 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds6 | 5142150be3189c6201266d6b2ef7726ef4236546 | 95 | 6,974,732 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7_repaired | 5408f9c10e37c0b00faa46dbc85663fb6f45e164 | 16 | 9,364,837 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/hh_batch | b44b7b0f5b59e7603334b7117d17e5813df7f162 | 123 | 5,900,459 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/hh_concurrent | f61234a1dda2cca38fd3b7995a859364316a114d | 124 | 6,888,467 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/hh2_batch | 6479ba1eba8bf90c90495a20986fa2340f07d753 | 82 | 6,097,806 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/hh2_concurrent | ae7e8016ffbe02feb11dc0e5a49b54e47a50c56c | 81 | 6,120,659 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/c1 | 6b243e172f68401379739e0adf28bcaac678dd1e | 1 | 77,011 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/c2 | a10aecaf89fc19356d496717bf27bd231a85ae9a | 63 | 2,851,373 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/compare_repaired_vs_golden.json | dfddeff0e8875c9b4461b5efc143bae4e8a88516 | 1 | 8,304,485 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/compare_vs_golden.json | 06a2c502fa839fe11a6425c52a648f57a65059f5 | 1 | 8,303,587 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/division.json | e6e65127b5014eb1697c782b8ba9caa5aa5cbf8a | 1 | 4,151 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/edge_similarity.json | 80dd8da0048f23a7585b0d13ed70aaefc1b3644e | 1 | 778 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/failed | fd8844cc0670154215a2b44a08c6933ad72e38d7 | 12 | 1,046,733 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/fixup_queue.json | 37304dae0ad23a3993fa1d44dd2a1060bd53e037 | 1 | 38,558 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/frontier_batch_input.jsonl | 41fc8e702ca7c3955c96818adc41b7cc57c96203 | 1 | 314,618 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/frontier_verdicts.json | 7cdf0f08f7f0d890017c94df1828a1561876f35a | 1 | 210,445 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/graph.json | 138f07937ed40171776f0a005e5a55060b2269a9 | 1 | 675,232 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/health.jsonl | 5150d05c4934912e880f6faa96abb23876f357ba | 1 | 40,696 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/inflight | untracked-or-file | 0 | 0 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/postbuild_compare_vs_golden.txt | 9febc2dab72a35e1861453c3b44dab317f027223 | 1 | 300 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/postbuild_graph_check.txt | ab31c829f3dec29f93e43f3a4ed287db5a31e168 | 1 | 6,074 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/postbuild_repair_census.txt | 7ccf4f01c18fb00fac51bce2b2d1c5cd79180a5d | 1 | 477 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/postbuild_risk_queue.txt | 5db4928e092ea307444d70697bf6ef24ccf31671 | 1 | 170 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/postbuild_sweep_headings.txt | 6ace9df264ef3c3dd8b1edbd4025eb9e08b20455 | 1 | 108 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/postbuild_sweep_modals.txt | 0e9b93dea6260f28cdaf47226a8ddc64591046ba | 1 | 459 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/promise_repair | f4569a7d4127b45d4bef045e1002dff26e5d0df8 | 36 | 1,174,089 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/promise_repair_report.json | 2c3ed5d0e54026d139913d4fc776c6c8bf5cda5d | 1 | 19,103 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/repair_census.json | 013499100d35d71572942448d7c1c1f0f348c973 | 1 | 3,306 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/risk_queue.json | 691c284b7396fe7838efe29ef8ed191c0465a707 | 1 | 65,933 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/root_graph.fixed.json | 5fbaffa7ba5e9843839c9355aa11cd3463d9bdec | 1 | 864,602 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/root_graph.json | 2a0bfe5e3240bdb1dc165083ba2f6c3ef4c5e51a | 1 | 864,438 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/root_graph.pre_resolution.json | 7bf16f024b0a88033505c3b07b74d15a70d71748 | 1 | 712,012 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/root_graph.repaired.json | 2a8eba0e77e31cffc7d1b6bab4dc6f1a48a50a03 | 1 | 885,110 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/run_meta.json | 2bd1bcb0fdf39e56e1bdae66a16c69e36c7b46c0 | 1 | 140 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/sweep_headings_report.json | 1668d289115d733428da0219bfa3602a2e82befe | 1 | 445 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/runs/ds7/sweep_modals_report.json | c0cd6ba8130415a3da5e3536d166a696468b55a6 | 1 | 20,871 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/run1 | b54f3378fcc9f0a4e82daa82d066d0db7c7236c0 | 1 | 125,816 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/run3 | 67356767feb72345a95b46f0f034b4c20b4cfef1 | 4 | 72,610 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/run4 | b09d795ee759b8cb75e2d92abe78048dc9f9c1f4 | 1 | 79,711 |
| walkthrough/paper_pipeline/phase_1/resolve_runs/graph_v2/run5 | d22bce780c6f7b56f5db9f982d597501f1f78fef | 14 | 1,153,417 |
| annotate_failures.jsonl | ede77687ba467c7a6ac3ec33d8b3f2bc2ee166da | 1 | 39,564 |
| annotations_gpt-5.6-luna_s0-c24c4c05.json | 6e5b7753304203a33f2860fd26f1c5b58e247a4c | 1 | 35,489 |
| blog_drafts | f8fc18b1fa36f5b6152cf49725a3aca2ca7061d8 | 4 | 25,893 |
| semi-formal-experiment/semantic_arm_embeddings.json | f79d04496a8385148c7f247f0a5fb2135db0c90d | 1 | 29,580,595 |
| semi-formal-experiment/HARNESS_REDESIGN.md.presplice | untracked-or-file | 0 | 0 |
| **TOTAL** | | **9801** | **173,154,896** |
| **Net after the post-prune restore (below)** | | **~7,778** | — |

Retained deliberately: runs/ds7_production (certified 773-node graph),
runs/ds7/root_graph.production.json (demo-path input), runs/*.txt logs,
runs/mock, translation_sample runs 20260812-133317 / 20260815-113545 /
20260815-124836 (cited by TRANSLATION_* docs), run2 (pinned refinement-turn
result), all of behavior_pilot/. semantic_arm_embeddings.json is a
regenerable embedding cache (see weight_diag.py).

**Restored post-prune (load-bearing for tests), 2026-08-30.** The first pass
over-pruned: the entries below are read at test time, so removing them turned
the walkthrough suite red. Each was restored from the pre-prune commit at the
exact path and content the loader reads — no test was weakened, and the run
directories they live in remain pruned except for these files.

* `translation_sample/runs/*/l*.{json,lp,version.json}` — the 750 node modules
  that WIN `link_nodes.gather()`'s newest-translated-per-node dedupe but whose
  winning run was pruned (1,973 files, 5.5 MB), plus the 34
  `run.json`/`concepts.json` of the 26 run directories they sit in (3.1 MB),
  which `link_nodes.merged_concepts()` reads. Pre-prune `gather()` selected 762
  nodes; post-prune it selected 66. This corpus is the input to
  `behavior_match.relevance_query` / `run_demo`, to
  `relevance_by_act.corpus_acts()`, and hence to
  `satisfiability_census.census()` — i.e. to the whole behavior_pilot analysis,
  not just its tests. Only the dedupe WINNERS were restored; losing artifacts
  for the same node stay pruned.
* `translation_sample/repair_graveyard/{l1_170_n047-20260815-040445,
  l1_170_n087-20260815-040444, l1_170_n088-20260815-040444,
  l171_426_n024-20260815-073255}` — the four arity-defect instances
  `test_checks.py::REAL` reads by name (16 files, 180 KB). The rest of the
  graveyard stays pruned.

Restoring these also re-satisfies `test_checks.py`'s
`scanned > 100` population floor (71 stored modules post-prune, ~800 with the
corpus back), which is a path-drift guard over `translation_sample/**`.
