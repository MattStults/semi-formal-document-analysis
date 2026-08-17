# Live pilot run 1 — 2026-08-16

DESIGN.md §5's pre-registered order, executed by `live_pilot.py` against the
frozen subset (PILOT_SUBSET.md). Model: DeepSeek-V4-Flash (the production
cheap tier) behind `translate.Client`; every call in usage.jsonl. **Total
metered spend $0.0166 over 165 calls** (seat $0.0016/15 · atoms $0.0005/5 ·
match $0.0137/140 · grounding $0.0007/5) plus ~5k unledgered embedding texts
(e5-large, sub-cent, recorded here per live_pilot.py's spend note). Estimate
was ~$0.18–0.25; actual came in ~10x under.

## 1. Seat sanity (seat_report.json)

15 demo (atom × candidate) pairs, live seat. **10/15 agree with the canned
demo key; all 5 divergences are live `engaged` where the key said
`not_engaged`, each with grounds that read as defensible engagement** (the key
marked exactly one node per atom by construction, so over-engagement against
it is expected, not refuted). Frontier parity pass still owed: adjudicate
seat_report.json against the BRIEF in a fresh frontier context.

## 2. Granularity (atoms.json + match_report.json)

28 atoms across the 5 behaviors (5–6 each). Against the 107-node subset at
top-5: **6/28 atoms engaged 0 nodes, 4/28 engaged >3, and all-k acceptance
added 30 node-slots over first-hit** — the cardinality delta DESIGN open
question 2 asked for, and it is large: first-hit would have discarded half
the engagement evidence.

## 3. Grounding (query_report.json)

4 of 5 behaviors grounded with **zero invented predicates** — the hard rule
("omit and report `missing` instead of inventing") held. The exception is
instructive: harmlessness-to-the-user's grounding used its own ATOM NAMES as
predicates (`protecting_user_interests(assistant)`, 4 invented) — when the
matched modules' input vocabulary has no purchase on an abstract behavior,
the model reaches for the atom vocabulary. Mechanically counted, not
adjudicated.

## 4. Relevance query — and the pilot's central finding

clingo ran end-to-end on all 5 behaviors (one solve each, no QueryError).
**2 of 5 behaviors fired a module** (tradeoffs: `prefer
detect_conflict_or_ambiguity`; animal-welfare: `oblige consider_context`);
**0 conflicts anywhere; most matched modules stayed silent.**

The silence is largely CORRECT, and that is the finding: the corpus's
modules encode **conditional norms** (`oblige control_side_effects(S) :-
situation(S), misaligned_instruction(S)`), while the pilot behaviors are
**value abstractions, not cases** — "harmlessness to the user" states no
misaligned instruction, no user mistake, no unclear provenance, so no
conditional norm should fire on it. The demo's concrete case (U18 romantic
roleplay: specific user, specific act) fired 4 asserts and exactly one
conflict on the same machinery. **Matching finds the right neighborhoods for
abstract behaviors; firing and contradiction detection need concrete
behavior INSTANCES — a situation plus acts — as input.** The validation Matt
wants (relevance + contradiction on real cases) should therefore feed
concrete scenario descriptions, not value definitions; the machinery is
demonstrated ready for exactly that shape.

Secondary bound, known at freeze: engaged modules whose rule bodies run
through `requires` names with no translated provider (the seam) cannot fire
even on a concrete case — the seam identity contract remains the next
corpus-side step.

## Not run, deliberately

Stage-4 refinement is user-in-the-loop by design; an autonomous run
impersonating the user validates nothing. Run it with Matt present on one
concrete behavior instance.
