# Change review assignment — cycle decoration-blind-join-2026-08-04

Seat brief: briefs/change_reviewer.md — read it first; it is the seat's
entire instruction. This is a frontier/careful seat: it exists to catch the
implementer's mistakes, so the small-model standard does not apply.

Change under review (from the manifest):

- fix_description: The DECORATION-BLIND JOIN, pricing v1.2 (spine cycle S1; BACKFILL_DESIGN.md §6 as amended per PORTFOLIO_REVIEW.md F1 — promoted from micro-cycle to a full standard cycle). containment.py's ContainmentIndex becomes the versioned v1.2 pricing path: the atom-channel match key, the atom df/idf, and the lexical atom-text all read the DECHAINED atom name — polarity + stem with the principal chain stripped (polarity is NOT stripped; grammar.stem_of is the wrong key). The dechain key applies at every entry point (_atom_score and _subsumption_matches dechain their query-atom names; channel_scores/explain dechain the behaviour, which also strips chain principal tokens from the lexical query text). Chained and chain-free instances of one dechained name share one df entry (clause sets unioned); stripped chains are preserved on the index as pricing metadata (self.chains) for the future 2.0 patient-pricing layer and reported by explain() under a `dechained` key (absent on chain-free evidence). PRICING_VERSION bumps "1.1" -> "1.2". The opt-in vehicle is the existing overlay seam: config.overlay = overlay_empty.json (ZERO edges, budget 0/0), which routes snapshot scoring through ContainmentIndex and records pricing_version "1.2" in the snapshot config identity — containment.json's licensed edges stay dormant (reactivation is cycle S5's, PORTFOLIO_REVIEW F2), so the only behavioural delta vs the baseline is the join itself. PROCESS NOTE, disclosed: a first OPEN/PREDICT of this same cycle name earlier today (manifest sha cf6e2496f048..., prediction sha 5b05b018d48d...) was DISCARDED before IMPLEMENT and before any snapshot was built or published: post-freeze RED->GREEN work exposed two defects in the then-frozen gate-test file test_dechain.py (a fixture gloss that embedded the chained name — glosses are authored prose, not decoration — and a missing pin that the dechain key applies at _atom_score's own entry point), and that file sat sha-pinned in the OPEN closure, so per the driver's own remedy the cycle was reopened with the corrected file finalized pre-OPEN. The prediction content is numerically identical to the discarded freeze; no measurement had run.
- document_side_rationale: The join was already BELIEVED decoration-blind by the containment design (CYCLE5_DESIGN §1.6: a chain 'therefore never enters stem-level matching') — this cycle makes the belief true. A principal chain is the annotation contract's decoration recording WHO acts on WHOM; it is not a different concept, and the chain audit (chain-repair-2026-08-04, KEEP: 109/109 instances adjudicated against clause text, 97 correct / 12 repaired) has ensured the chains are semantically sound first. Under the exact-name join, decoration splits a concept's document frequency and breaks matches between a chained and a chain-free spelling of the same (polarity+stem, kind) atom — computed live: helpfulness's chained query atom should_ask_clarifying_questions__model_user is severed from 13 chain-free clause instances of the same concept, and 50 chained clause-side names hold df entries split off their dechained keys. Without this join, neither the S2 patient backfill's zero-flip construction nor cycle 5's 'chains never enter matching' premise is true (PORTFOLIO_REVIEW F1: two-sided coincidence, a REAL retrieval change). Document-side only: no panel value informs the rule; the dechain key is defined entirely by grammar.py's notation.
- files_to_change: containment.py, test_containment.py
- gate_tests: test_dechain.py, test_containment.py, test_no_reference_leak.py

Required output: review_verdict.json in this cycle's directory:

    {"verdict": "proceed" | "blocked",
      "by": "<who reviewed — never the implementer>",
      "notes": "<what was verified, or why blocked>"}

All three keys are REQUIRED; verdict is a CLOSED set. The driver re-checks
the frozen manifest/prediction shas, the two-sided one-variable check and
the gate tests mechanically; your seat verifies what the machine cannot
(see the brief: freeze shas, declared-diff-only, tests bind — at least one
mutant — and the fence scan). A "blocked" verdict halts the cycle until
resolved and re-reviewed.
