# Behavior-translation failure classes — the behavior-side twin of 30_failure_modes.md

Every entry: MECHANISM (not a check id), EVIDENCE (round, behavior, quoted
artifact), FALSIFIER, FIX LOCUS (checklist / translator brief / seat brief /
retrieval / act-seam / spec). Promote a class into BEHAVIOR_CHECKLIST.md or
the translator brief once it has fired twice. Started 2026-08-18 after Matt
asked whether errors were being recorded generally; before this file they
lived in commit messages only (transcript-only procedure — a review finding).

| # | class | evidence | falsifier | fix locus |
|---|---|---|---|---|
| B1 | **Party-scope conflation** — a harm/duty atom without the party qualifier engages user-harm, third-party-harm and confidentiality clauses alike | cold-start harm-avoidance engagement defensibility 0.56; every precision error a scope conflation (REGISTERED_RESULT.md) | tuned atoms with party named show no scope-conflation errors (r1: 9/9 held-out engagements defensible) | checklist rule 1 + seat brief party test — DONE |
| B2 | **Abstract consideration atoms** ("foreseeable societal harm", "protecting user interests") reach no clause and ground no fact | cold-start: 6/28 atoms engaged 0 nodes; harmlessness grounding invented 4 predicates (live_run1) | concrete act atoms engage and ground without invention | checklist rules 3–4 — DONE |
| B3 | **Vocabulary mismatch with the document's framing** — behavior phrased about REQUESTS where the document speaks of TOPICS/AGENDA | caution: 17/17 panel-hot declines were real misses; the whole l2126_2404 cluster (report) | atoms in topic/agenda phrasing reach the cluster (caution r1 module engaged them) | checklist rules 2, 5 — DONE |
| B4 | **Retrieval reach** — good atoms whose glosses share too few content words with clause text never surface | harm r1: only 9/46 held-out engaged, probe engaged 16/35 unretrieved | wider beam / clause-vocabulary glosses raise raw held-out engagement (caution r1 at K=24: 15/33) | TOP_K_TUNED — DONE; gloss rewrite in r2 |
| B5 | **Invented predicates in the module block** — the translator coins `request_would_harm_third_party(b)`, `clarification_sought(b)`, `does` heads not declared by any corpus module | harm r2 module `does`; helpfulness r1 `-atom(b)` classical negation the corpus never uses; S4 needed hand-grounding | a translator given the corpus vocabulary contract emits only declared predicates and validates 0 breaches like a spec module | **translator brief + act seam contract — OPEN (Matt ruling)** |
| B6 | **Structure flattened** — a conjunction-of-disjunctions behavior represented as a flat bag, so per-branch coverage is unreportable | pre-spec atom lists for all 3 behaviors; Matt's caution example | module with explicit branches reports per-branch coverage (caution r1: over 38 / under 33) | BEHAVIOR_MODULE_SPEC — DONE |
| B7 | **Over-fit to tuning nodes** (risk, not yet observed) — atoms phrased to hit specific tuning verdicts, failing on held-out | held-out scoring by fresh adjudicators exists to detect it; harm r1 held-out precision 1.00 says not yet | held-out precision drop vs tuning-half precision | tuner brief anti-overfit clause — DONE, monitored |
| B8 | **Act-name non-canonicality in the CORPUS blocks behavior firing** — 60 caution-relevant modules, ~90 act names for ~10 concepts (refuse_to_help/refuse_help/refuse_request…) | vocabulary inventory 2026-08-18; S4 grounded by hand | an act seam contract + gate check collapses the act space; behavior modules fire corpus-wide | **act seam contract — OPEN (Matt ruling); spec side** |
