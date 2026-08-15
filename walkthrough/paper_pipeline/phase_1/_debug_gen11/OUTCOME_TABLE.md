# OUTCOME_TABLE.md — every clause of the gen-11 translation run

Runs `20260814-163457-together-deepseek-v4-flash` (12 clauses) and
`20260814-173322-together-deepseek-v4-flash` (88 clauses). Same `system_sha 5ff9daf7fe58845f`,
same `schema_sha 30ef9db24fb069a7`, same `provenance_params {max_tokens: 4096, format_forcing: json_schema, max_attempts: 5}`.
Prompt generation 11. **Zero API spend: every number is re-analysis of bytes on disk.**

Cost is the REAL recorded cost: all 230 assistant turns were matched 1:1 to `semi-formal-experiment/usage.jsonl`
rows on `content_chars` (0 unmatched), following the method the census review validated. The two `run.json`
`spend` blocks record 235 calls; the extra 5 are `resample_truncation` draws that never enter a transcript.

`frozen` = repair rounds that returned a module **byte-identical** to the previous attempt.
`08-15 retry` = outcome of the same clause under a **byte-identical prompt** (same `user_sha`) in
`20260815-070038`, which re-attempted 18 of the 19 unrepaired clauses.

## Totals

| | |
|---|---|
| clauses | **100** |
| paid calls (transcript turns) | **230** |
| of which repair rounds | **130 — 57% of all calls** |
| recorded spend | **$0.4051** |
| of which repair | **$0.2415 — 60%** |
| translated | **69** (36 first-pass, 33 after 1-4 repair rounds) |
| unrepaired (5 attempts, no module) | **19** |
| abstained | **11** + 1 `abstained_under_repair` |
| modules produced | **69 / 100** |
| repair rounds returning byte-identical bytes | **52 / 130 (40%) — $0.1026 bought nothing** |

Attempts: 1 → 47 clauses · 2 → 20 · 3 → 10 · 4 → 2 · 5 → 21.
The 21 five-attempt clauses (21% of clauses) burned 84 of the 130 repair rounds — **65% of repair spend**.

## Finding classes (raw, before mechanism grouping)
```
 206  undeclared-body-name
  50  borrowed-no-gloss
  12  gloss-restates-name
  10  unsafe-var
  10  unresolved-reference
  10  assumed-no-inference
   7  readback-slot-mismatch
   7  concept-declared
   7  schema-breach
   5  unsafe-var-no-body
   5  clingo-error
   5  situation-input
   4  requires-unprovided
   2  atom-not-a-term
```
`schema-breach` is the `check_id` on 309 of the 341 finding lines; the class names above come from the
message shape, exactly as `translation_repair_census.py` does it. Four of these classes
(`gloss-restates-name`, `assumed-no-inference`, `concept-declared`, `situation-input`) have **no entry in
that census taxonomy** and would land in its `OTHER:` bucket — see `PRIOR_WORK_MAP.md`.

## Mechanism key

| id | mechanism | file |
|---|---|---|
| M1 | invented descriptive predicate has no legal declaration bucket | `class_no-legal-bucket.md` |
| M2 | borrowed name declared in one list, glossed in another | `class_borrowed-gloss-split.md` |
| M3 | tautological predicate — the gloss can only restate the name | `class_tautological-gloss.md` |
| M4 | `ontology` used as a declaration list (unsafe variable) | `class_ontology-as-declaration.md` |
| M5 | cross-module identity drift and upstream loss (link stage) | `class_link-identity-drift.md` |
| M6 | `read_back_slots` read as "this rule's variables" | `class_readback-slots.md` |
| M7 | honest invention penalised (`assumed` with no named inference) | `class_honest-invention-penalised.md` |
| M8/M9 | residue: abstention-with-content, gloss punctuation, textual-licence-no-citation | SUMMARY.md §residue |

Cross-cutting: `class_repair-fixed-point.md` (the 40% byte-identical rounds) is a **multiplier on all of the above**, not a separate row.

## Per-clause table

| clause | status | att | $ | frozen | mechanisms per repair round | 08-15 retry |
|---|---|---|---|---|---|---|
| `l171_426_n005` | unrepaired | 5 | 0.0099 | 1 | a1:M4; a2:M4; a3:M1+M2+M3; a4:M3; a5:M3 | translated/4 |
| `l1_170_n006` | unrepaired | 5 | 0.0086 | 3 | a1:M4; a2:M4; a3:M4; a4:M4; a5:M4 | translated/1 |
| `l1_170_n014` | unrepaired | 5 | 0.0089 | 4 | a1:M1; a2:M1; a3:M1; a4:M1; a5:M1 | translated/2 |
| `l1_170_n015` | unrepaired | 5 | 0.0109 | 3 | a1:M1+M2; a2:M1; a3:M1; a4:M1; a5:M1 | abstained/1 |
| `l1_170_n023` | unrepaired | 5 | 0.0087 | 2 | a1:M1; a2:M1; a3:M1; a4:M1; a5:M1 | translated/2 |
| `l1_170_n028` | unrepaired | 5 | 0.0084 | 3 | a1:M3; a2:M3; a3:M3; a4:M3; a5:M3 | translated/1 |
| `l1_170_n037` | unrepaired | 5 | 0.0084 | 3 | a1:M4; a2:M4; a3:M1; a4:M1; a5:M1 | translated/1 |
| `l1_170_n043` | unrepaired | 5 | 0.0080 | 3 | a1:M5; a2:M5; a3:M5; a4:M5; a5:M5 | translated/1 |
| `l1_170_n047` | unrepaired | 5 | 0.0083 | 4 | a1:M5; a2:M5; a3:M5; a4:M5; a5:M5 | translated/1 |
| `l1_170_n052` | unrepaired | 5 | 0.0087 | 3 | a1:M1+M2; a2:M1; a3:M1; a4:M1; a5:M1 | translated/1 |
| `l1_170_n056` | unrepaired | 5 | 0.0088 | 2 | a1:M2; a2:M2; a3:M2; a4:M2; a5:M2 | unrepaired/5 |
| `l1_170_n058` | unrepaired | 5 | 0.0084 | 0 | a1:M1; a2:M1; a3:M1; a4:M1; a5:M1 | unrepaired/5 |
| `l1_170_n062` | unrepaired | 5 | 0.0119 | 4 | a1:M1; a2:M1; a3:M1; a4:M1; a5:M1 | translated/1 |
| `l1_170_n065` | unrepaired | 5 | 0.0064 | 3 | a1:M1; a2:M1; a3:M1; a4:M1; a5:M1 | translated/3 |
| `l1_170_n069` | unrepaired | 5 | 0.0077 | 3 | a1:M1+M2; a2:M1; a3:M1; a4:M1; a5:M1 | translated/1 |
| `l1_170_n078` | unrepaired | 5 | 0.0085 | 0 | a1:M1; a2:M1; a3:M4; a4:M1; a5:M1 | unrepaired/5 |
| `l1_170_n084` | unrepaired | 5 | 0.0092 | 4 | a1:M1; a2:M1; a3:M1; a4:M1; a5:M1 | unrepaired/5 |
| `l1_170_n087` | unrepaired | 5 | 0.0115 | 3 | a1:M2; a2:M5; a3:M5; a4:M5; a5:M5 | translated/2 |
| `l1_170_n088` | unrepaired | 5 | 0.0132 | 2 | a1:M7; a2:M1+M2; a3:M1; a4:M1; a5:M1 | translated/3 |
| `l171_426_n003` | abstained_under_repair | 2 | 0.0016 | 0 | a1:M8 | — |
| `l1_170_n002` | abstained | 1 | 0.0014 | 0 | — | — |
| `l1_170_n009` | abstained | 1 | 0.0014 | 0 | — | — |
| `l1_170_n011` | abstained | 1 | 0.0014 | 0 | — | — |
| `l1_170_n012` | abstained | 1 | 0.0014 | 0 | — | — |
| `l1_170_n018` | abstained | 1 | 0.0025 | 0 | — | — |
| `l1_170_n029` | abstained | 1 | 0.0014 | 0 | — | — |
| `l1_170_n038` | abstained | 1 | 0.0014 | 0 | — | — |
| `l1_170_n063` | abstained | 1 | 0.0014 | 0 | — | — |
| `l1_170_n064` | abstained | 1 | 0.0001 | 0 | — | — |
| `l1_170_n076` | abstained | 1 | 0.0014 | 0 | — | — |
| `l1_170_n079` | abstained | 1 | 0.0014 | 0 | — | — |
| `l1_170_n053` | translated | 5 | 0.0080 | 0 | a1:M1; a2:M4; a3:M1; a4:M2 | — |
| `l1_170_n057` | translated | 5 | 0.0083 | 2 | a1:M1; a2:M1; a3:M1; a4:M1 | — |
| `l1_170_n016` | translated | 4 | 0.0073 | 0 | a1:M1; a2:M4; a3:M1 | — |
| `l1_170_n031` | translated | 4 | 0.0080 | 0 | a1:M1+M2; a2:M1; a3:M2 | — |
| `l1_170_n003` | translated | 3 | 0.0048 | 0 | a1:M6; a2:M2 | — |
| `l1_170_n019` | translated | 3 | 0.0061 | 0 | a1:M1; a2:M3 | — |
| `l1_170_n039` | translated | 3 | 0.0051 | 0 | a1:M4; a2:M1 | — |
| `l1_170_n050` | translated | 3 | 0.0052 | 0 | a1:M1; a2:M3 | — |
| `l1_170_n060` | translated | 3 | 0.0052 | 0 | a1:M6; a2:M6 | — |
| `l1_170_n067` | translated | 3 | 0.0053 | 0 | a1:M1; a2:M3 | — |
| `l1_170_n068` | translated | 3 | 0.0053 | 0 | a1:M7; a2:M2 | — |
| `l1_170_n077` | translated | 3 | 0.0050 | 0 | a1:M9; a2:M1+M2 | — |
| `l1_170_n086` | translated | 3 | 0.0052 | 0 | a1:M1; a2:M1 | — |
| `l1_170_n091` | translated | 3 | 0.0053 | 0 | a1:M7; a2:M1+M2 | — |
| `l171_426_n001` | translated | 2 | 0.0032 | 0 | a1:M1 | — |
| `l171_426_n002` | translated | 2 | 0.0032 | 0 | a1:M5 | — |
| `l1_170_n007` | translated | 2 | 0.0029 | 0 | a1:M4 | — |
| `l1_170_n024` | translated | 2 | 0.0031 | 0 | a1:M6 | — |
| `l1_170_n025` | translated | 2 | 0.0034 | 0 | a1:M6 | — |
| `l1_170_n032` | translated | 2 | 0.0032 | 0 | a1:M1 | — |
| `l1_170_n036` | translated | 2 | 0.0034 | 0 | a1:M2 | — |
| `l1_170_n045` | translated | 2 | 0.0032 | 0 | a1:M1 | — |
| `l1_170_n046` | translated | 2 | 0.0061 | 0 | a1:M2 | — |
| `l1_170_n049` | translated | 2 | 0.0031 | 0 | a1:M2 | — |
| `l1_170_n051` | translated | 2 | 0.0031 | 0 | a1:M2 | — |
| `l1_170_n066` | translated | 2 | 0.0031 | 0 | a1:M1+M2 | — |
| `l1_170_n071` | translated | 2 | 0.0031 | 0 | a1:M2 | — |
| `l1_170_n072` | translated | 2 | 0.0031 | 0 | a1:M2 | — |
| `l1_170_n073` | translated | 2 | 0.0032 | 0 | a1:M1+M2 | — |
| `l1_170_n074` | translated | 2 | 0.0033 | 0 | a1:M1+M2 | — |
| `l1_170_n075` | translated | 2 | 0.0034 | 0 | a1:M2 | — |
| `l1_170_n082` | translated | 2 | 0.0034 | 0 | a1:M2 | — |
| `l1_170_n083` | translated | 2 | 0.0034 | 0 | a1:M9 | — |
| `l171_426_n004` | translated | 1 | 0.0015 | 0 | — | — |
| `l171_426_n007` | translated | 1 | 0.0095 | 0 | — | — |
| `l171_426_n008` | translated | 1 | 0.0015 | 0 | — | — |
| `l171_426_n009` | translated | 1 | 0.0015 | 0 | — | — |
| `l1_170_n001` | translated | 1 | 0.0014 | 0 | — | — |
| `l1_170_n004` | translated | 1 | 0.0015 | 0 | — | — |
| `l1_170_n005` | translated | 1 | 0.0015 | 0 | — | — |
| `l1_170_n008` | translated | 1 | 0.0015 | 0 | — | — |
| `l1_170_n010` | translated | 1 | 0.0013 | 0 | — | — |
| `l1_170_n013` | translated | 1 | 0.0015 | 0 | — | — |
| `l1_170_n017` | translated | 1 | 0.0015 | 0 | — | — |
| `l1_170_n020` | translated | 1 | 0.0014 | 0 | — | — |
| `l1_170_n021` | translated | 1 | 0.0016 | 0 | — | — |
| `l1_170_n022` | translated | 1 | 0.0015 | 0 | — | — |
| `l1_170_n026` | translated | 1 | 0.0017 | 0 | — | — |
| `l1_170_n027` | translated | 1 | 0.0019 | 0 | — | — |
| `l1_170_n030` | translated | 1 | 0.0016 | 0 | — | — |
| `l1_170_n033` | translated | 1 | 0.0016 | 0 | — | — |
| `l1_170_n034` | translated | 1 | 0.0017 | 0 | — | — |
| `l1_170_n035` | translated | 1 | 0.0017 | 0 | — | — |
| `l1_170_n040` | translated | 1 | 0.0016 | 0 | — | — |
| `l1_170_n041` | translated | 1 | 0.0015 | 0 | — | — |
| `l1_170_n042` | translated | 1 | 0.0016 | 0 | — | — |
| `l1_170_n044` | translated | 1 | 0.0017 | 0 | — | — |
| `l1_170_n048` | translated | 1 | 0.0015 | 0 | — | — |
| `l1_170_n054` | translated | 1 | 0.0015 | 0 | — | — |
| `l1_170_n055` | translated | 1 | 0.0015 | 0 | — | — |
| `l1_170_n059` | translated | 1 | 0.0015 | 0 | — | — |
| `l1_170_n061` | translated | 1 | 0.0014 | 0 | — | — |
| `l1_170_n070` | translated | 1 | 0.0015 | 0 | — | — |
| `l1_170_n080` | translated | 1 | 0.0016 | 0 | — | — |
| `l1_170_n081` | translated | 1 | 0.0015 | 0 | — | — |
| `l1_170_n085` | translated | 1 | 0.0016 | 0 | — | — |
| `l1_170_n089` | translated | 1 | 0.0037 | 0 | — | — |
| `l1_170_n090` | translated | 1 | 0.0019 | 0 | — | — |
| `l1_170_n092` | translated | 1 | 0.0016 | 0 | — | — |
