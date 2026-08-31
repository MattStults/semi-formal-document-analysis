# Behavior-matching pilot — offline skeleton design

Spec: EXPERIMENTS.md 2026-08-13, "BEHAVIOR-PIPELINE PILOT PLAN (owner-approved
direction)". This directory is the OFFLINE skeleton: every model call sits
behind an injectable `complete(system, user)` seam (rename_seat.judge's
contract), the embedder is injected with a lexical fallback, and the one
paid-shaped loop runs end-to-end against real translated modules with a
mocked seat. Zero spend. Built 2026-08-14; model tier: frontier
(orchestration/design per the working rule — this file includes design
decisions, not just execution).

## 1. Pilot behaviors (selection, not truth)

`select_pilot_behaviors.py` -> `pilot_behaviors.json`. Frontier evidence
(gpt-5.6-luna `behavior_atoms_v2_draw0..4` + `annotations_b8` vocabulary +
`modelspec_clauses` lines, all sharing the graph doc's source_sha256) is used
ONLY to pick which behaviors are worth piloting where the 15 translated nodes
live. Labels direct attention, never truth: `behavior_match.py` reads none of
these files, and evaluation-time disagreements get adjudicated against the
document.

Method: an atom is *stable* when >= 3 of 5 independent draws select it; a
behavior's frontier clause set is the union of its stable atoms' annotated
clauses; concentration is measured against the nodes' **narrowed spans**
(what the modules actually encode; baseline share 6.2% of 593 clauses) and
reported as lift. Selection floor: max span lift >= 0.9 across the
weight>=2 / weight>=3 cuts.

Selected (5): how-to-approach-tradeoffs (lift 2.86 — dominated by the
chain-of-command node l1_170_n028), proportionate-risk-mitigation (1.91),
animal-welfare-impacts (1.56), harmlessness-to-the-user (1.23),
harm-avoidance-to-third-parties (0.93 — also one of the three
panel-validated behaviours, kept for eval continuity).

**Honest finding:** only ONE behavior concentrates >2x in the translated
spans. Whole-spec behaviors spread across the whole spec; a 15-node sample
covers 37/593 clauses. The pilot can still answer its three questions
(brief adequacy, granularity fit, loop cost), but *retrieval recall against
frontier clause sets* will be bounded by span coverage, not by the matcher —
score that per-region, or the number will look like a matcher failure.

## 2. Behavior-module ASP shape (stage 2)

A behavior module **extends the clause-module shape** (`%%` header
discipline, citation-tagged lines, loadable through the same link path) with
one deliberate inversion: **clause modules state norms; a behavior module
states a case.** It contributes:

```
%% behavior: <asp_id>   section: behavior_module   kind: situation
%% inputs: <signatures of the facts it asserts>
behavior(<id>).
<situation facts>.        % [B] <id>      -- grounds clause-module inputs/requires
does(<id>, <act term>).   % [B] <id>      -- the acts the behavior performs
```

Deviations from the clause shape, each justified:

* **No `asserts/3`, no `%% closure`, no ontology guard.** `asserts` is the
  document's voice; a behavior asserting deontics would let the query answer
  itself. Closure lines exist to record a clause's permission default —
  a case has no default to record. The `#const onto` guard exists for the
  deontic-ablation experiment over clause corpora; behavior facts must fire
  under both settings, so they are unguarded.
* **`%% inputs` instead of `%% concepts`/`%% requires`.** The behavior's
  facts are exactly the "plain facts about the situation being judged" that
  clause-module `inputs` declare. Grounding = phrasing the behavior's atoms
  in the matched modules' declared input/required signatures. A `requires`
  block may return later if behavior modules borrow defined concepts
  (e.g. `stay_in_bounds_principles/1` when a provider module defines it) —
  today the demo supplies such tokens as plain facts, which is the skeleton's
  loosest joint (open question 3).
* **`does/2` is new vocabulary.** The clause corpus has no notion of "the
  act was performed"; conflict detection needs one. Kept minimal:
  `conflict(S, A) :- does(B, A), asserts(S, forbid, A), behavior(B).`
  Obligation gaps (an obliged act the behavior *omits*) need negation over
  `does` and a frame assumption; deferred to the live pilot (open question 4).
* **`% [B]` provenance tag** (vs `[T]`/`[A]`): behavior-derived, neither
  document-traceable nor annotator assumption. The readback layer can render
  these as "the case under judgment states…".
* Behavior ids obey `node_corpus.asp_id`'s lesson (rendered constants must
  parse); `render_behavior_module` refuses non-ASP ids loudly.

Translation of a behavior into this shape reuses stage-1 machinery
(schema checks, repair loop, graveyard) with a narrowed target grammar:
facts and `does` only, no rules. That is a *restriction* of the existing
validator surface, not new machinery.

## 3. Matching (stage 3) — retrieval + seat + clingo

* **Retrieval** (`rank_candidates`): injected `embed(texts) -> vectors|None`
  (live: `recurse_driver._embed_texts`, raw enriched prose, 82%@10
  measured; the canonical-card variant measured worse and stays declined).
  Query text = atom gloss `||` behavior text; candidate text = node
  establishes `||` span text. Offline fallback: token-count cosine —
  a stand-in, not a measured ranker.
* **Seat** (`BRIEF`/`build_prompt`/`judge`): rename_seat's discipline moved
  from identity to engagement. Blind on names by construction (prompts carry
  glosses + document text; `node_views` strips the PROVIDES/NEEDS name
  blocks; tested). Fail-closed to `not_engaged` with the asymmetry argued in
  the brief itself: a missed link is a recoverable recall gap, a wrong link
  corrupts the formal query. One-shot, order-blind, memoised per
  (gloss, node), hard call cap as a mechanism (recurse_driver finding 1),
  CostGateError propagates.
* **Acceptance**: first `engaged` in embedding order wins
  (greedy_rename_descend's shape). An atom may legitimately engage several
  nodes; whether to keep walking after the first hit is a live-pilot
  measurement (open question 2).
* **clingo query** (`relevance_query`): modules come from
  `link_nodes.gather()` (newest translated artifact per node) with
  `link.dedupe_shared_preamble` — the same corpus-assembly path as
  link_nodes.main, not a hand rebuild. One solve; `!= 1` answer sets is a
  loud `QueryError` (readback_r3 doctrine: a check that cannot run must not
  exit like a check that passed). Output: which modules' `asserts` fire
  (relevant), which stay silent, and forbid-vs-does conflicts.

Demo (real modules on disk, mocked seat) — the U18 romantic-roleplay
example here is a hand-written smoke fixture, NOT a corpus behavior:
U18 romantic-roleplay behavior ->
3 atoms -> lexical retrieval puts the right node first for all 3 -> mocked
seat accepts 3 pairs -> clingo over `l797_809_n001` + `l4572_4691_n011`
(the requires-resolved pair: `stay_in_bounds_principles/1` provided) fires
4 asserts across both modules and reports exactly one conflict:
`engage_in_immersive_romantic_roleplay(a1,u1)` is performed and forbidden.

## 4. Interactive refinement (design only — stage 4)

Feedback refines the QUERY, never the corpus. The loop state is the
behavior's artifact triple (free text, atom list, behavior module .lp);
graph and clause modules are read-only.

1. **Present**: matched nodes with seat grounds; fired asserts rendered
   through the readback layer (trace_rule strings + merged gloss); conflicts
   and silent-but-matched modules called out; capped/near-miss candidates
   listed exactly as the descend records them.
2. **Feedback in prose**: "it wasn't a minor", "you missed the privacy
   angle", "that clause isn't about this".
3. **Revise under validators**: an LLM turn (same injectable seam) maps
   feedback to edits of the atom list and/or situation facts — never edits
   node modules, never edits the graph. The revised behavior module re-runs
   the SAME stage-2 validator surface (schema, link, graveyard on repeated
   failures). Matching re-runs only for changed atoms (verdict memo makes
   unchanged pairs free).
4. **Convergence & audit**: each iteration appends (feedback, diff,
   re-match delta) to the behavior's transcript record; stop when the user
   accepts or when an iteration changes nothing (report that honestly).
   A feedback item that contradicts a seat verdict is recorded as a
   disagreement to adjudicate against the document — user feedback is also
   attention, not truth, for evaluation purposes.

No UI is built here; the loop is `(present -> feedback -> revise -> rerun)`
over the functions in behavior_match.py plus one revision prompt to be
drafted for the live pilot.

## 5. What needs LIVE validation next (costs at $0.14 in / $0.28 out per Mtok)

Token shapes measured from this skeleton's prompts (seat prompt ~1.1–1.6k
tok incl. brief; verdict ~80 tok out):

| step | calls (5 behaviors) | tok in/out | est. cost |
|---|---|---|---|
| atom decomposition (1 call/behavior, behavior_atoms prompt shape) | 5 | ~4k / 1.5k | ~$0.005 |
| behavior->module translation + repair (stage-1 loop, facts-only grammar) | 5–10 | ~8k / 2k ea | ~$0.015 |
| matching seat: ~20 atoms x <=5 candidates, memoised | <=500 | ~1.3k / 0.1k ea | ~$0.10 |
| embeddings (together e5-large) | 5 batches | — | <$0.01 |
| refinement: 2 iterations x (1 revision call + ~30% seat re-runs) | ~2x60 | mixed | ~$0.05 |
| **full 5-behavior pilot, 2 refinement rounds** | | | **~$0.18–0.25** |

Order of validation (cheapest falsifier first):

1. **Seat brief live sanity** (~$0.01): run the demo's 15 (atom x candidate)
   pairs through a real small model; divergence from a frontier model on the
   same brief is a seat defect, not a model failure — same parity protocol
   as rename_seat's sweep.
2. **Atom-vs-node granularity** (the project owner's #7 core): decompose the 5 pilot
   behaviors live, run matching, count atoms that match 0 nodes vs >3 nodes.
   Frontier clause sets are the pre-registered evaluation reference;
   disagreements adjudicated against the document.
3. **Grounding step**: can a model phrase situation facts in the matched
   modules' input signatures without inventing predicates? (This is the step
   the skeleton hand-writes in DEMO_FACTS.)
4. **Full loop with refinement** on one behavior, transcript kept.

Budget note: entire pilot fits in ~$0.25 of the ~$6.35 remaining ceiling.

## 6. Open questions for the project owner

1. **Selection floor**: only how-to-approach-tradeoffs concentrates >2x at
   span level. Accept the 5 at floor 0.9, or narrow the pilot to the top 3
   and add a 6th nearby node region to the translated sample instead?
2. **Match cardinality**: stop at first `engaged` per atom (cheap,
   greedy-descend shape) or adjudicate all top-k and keep every `engaged`
   (better module recall, ~3x seat calls)? Proposal: all-k for the pilot,
   measure the delta, then decide.
3. **Borrowed concepts in behavior modules**: should behavior facts be
   allowed to instantiate `requires`-style borrowed names (demo:
   `stay_in_bounds_principles(stay_in_bounds)`), or must those always be
   derived by provider modules with the behavior supplying only raw case
   facts? The latter is cleaner but needs the providers' own inputs
   grounded too (deeper grounding step).
4. **Obligation gaps**: conflict currently = performed-and-forbidden. Add
   obliged-and-not-performed (needs a closed-world `does` assumption per
   behavior)? Proposal: yes, but as a separate report field, flagged as
   frame-assumption-dependent.
5. **Registration/fencing**: this directory lives outside
   semi-formal-experiment's test tree, so QUERY_MODULES/FORBIDDEN fencing
   does not see it. select_pilot_behaviors.py legitimately reads frontier
   labels (evaluation side); behavior_match.py must never. Where should the
   fence live once the pilot goes live — a graph_v2-side leak test
   mirroring test_no_reference_leak's static arm?
6. **Seat prompt evidence**: node views currently show up to 1.5k chars of
   span text. rename_seat caps at 12 lines per span. Align, or measure?
