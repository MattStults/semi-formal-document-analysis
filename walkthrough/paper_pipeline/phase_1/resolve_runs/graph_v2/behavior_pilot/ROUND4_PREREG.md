# ROUND-4 CERTIFICATION PRE-REGISTRATION — RE-ISSUE (signature-ready, 2026-08-24)

Status: RE-ISSUE at instrument freeze, per the scaffold's own rule ("Re-issued
signature-ready at freeze; Matt signs the re-issue, which carries this
scaffold's protocol verbatim"). Protocol sections below are VERBATIM from
ROUND4_PREREG_SCAFFOLD.md (DRAFT-0, 2026-08-21); no protocol change was made
between scaffold and re-issue, so no erratum attaches. Lineage: round-1
(protocol proof-out), round-2 (help PASSED, harm F1, caution F1-by-2, all
fixed), round-3 (signed 2026-08-19, SUPERSEDED UNRUN — froze v13; instrument
moved on), this re-issue freezes v19.

## What round 4 certifies
The three dev behaviours (helpfulness, harm-avoidance-to-third-parties,
avoiding-over-and-under-caution) on the Model Spec corpus, under the FROZEN
post-9b instrument, on nodes NEVER before ruled — converting the in-sample
criterion standing (0.94-0.96 match-or-adjudicated-defensible) into a
certified out-of-sample claim. Scored ONCE.

## Protocol (fixed, instrument-independent — verbatim from the scaffold)
- Draws: seeded per behavior (seeds registered below), stratified 40 ENGAGED
  + 40 NOT-engaged at the frozen instrument's states; every node with ANY
  prior ruling excluded (the exclusion list is a deterministic script output
  committed with its sha: round4_freeze.py -> ROUND4_FREEZE_DERIVATION.json).
- Rulings: single blind Fable rulings + 3-instance panels on a seeded 20%;
  majority supersedes. Fable only; no substitution without fresh parity
  validation, disclosed. VENUE (carried from DEFENSIBILITY_BATCH_PROTOCOL.md
  venue ruling, 2026-08-24): seats execute as fresh Fable subagents receiving
  only the packet prompt string plus the recorded content-free tool fence.
- Canary ordering: helpfulness first; Matt /usage checkpoint between
  behaviors; go/hold at each checkpoint. Budget tripwire carries over: a
  wave moving the weekly Fable bar disproportionately to its ruling count
  stops the run for inspection.
- Cost model: ~250 rulings ~= 0.37-0.4M Fable tokens, $0 API (harm closes
  its engaged-population remainder — see freeze sections).
- Errata rule: registered numbers are never edited; corrections append.

## Falsifiers (carried from round 3; apply unchanged)
F1: any sampled engaged-precision below band floor; population figure below
    its registered floor.
F2: any decline-correctness below band floor.
F3: >=3 unanimous-relevant not-engaged nodes in one behavior sharing one NEW
    failure locus.
F4: >30% of panels split 2-1 in any behavior.
F5: single-vs-panel overturn rate >10% in any behavior -> remaining nodes
    escalate to panels.

## Success criterion (carried)
All cells within/above band, no falsifier -> the behaviors are CERTIFIED on
this document and the generalization runs + next-document arc unblock per
the campaign mandate. Above-band results get the leak-signature check before
they are celebrated.

## FREEZE SECTIONS (derived 2026-08-24 by round4_freeze.py; full values incl.
## per-node exclusion lists in ROUND4_FREEZE_DERIVATION.json — committed with
## this file)
- Frozen instrument: modules_contract_v19.json, sha256
  d0e12c234b2056cbe9ff3e4aeeac05f81e22a14ca76a9ca3e49dd5b5eeb7282e
  (= v18 + helpfulness purpose_concern [empowerment] + caution
  purpose_concern [harm-prevention], adoption FINAL per
  DEFENSIBILITY_BATCH_PROTOCOL.md ADJUDICATION RESULT); layers: assert_* +
  definition_* lanes + act_refinements_FINAL consensus, all at HEAD of this
  commit; census: satisfiability_census_v19_frozen.json (same commit).
- Exclusion lists (every node with any prior ruling = assembled truth-ledger
  keys, incl. the defensibility overlay):
  caution 205 nodes sha 190dfefe…, harm 234 sha 291353e8…, help 397 sha
  188f273a… (full 64-char shas + node lists in the derivation artifact).
- Pool sizes (v19 states, exclusions removed): caution 281 engaged / 276
  not; harm 17 engaged / 511 not; help 173 engaged / 192 not.
- Registered predictions (over all-truth at the frozen instrument; band =
  +-2 nodes = +-5 pts at n=40):
  caution: engaged precision 0.8843 (basis n=121), decline-correctness
  0.8214 (n=84);
  harm: engaged precision 0.8706 (n=85), decline-correctness 0.7785 (n=149);
  help: engaged precision 0.9336 (n=211), decline-correctness 0.7849 (n=186).
- Harm population-remainder treatment: the unruled engaged pool is 17 <= 48,
  so the engaged side is drawn WHOLE (population CLOSED — the certified
  engaged-precision claim for harm is then a population figure, not a
  sample); not-engaged side draws 40 as standard.
- Seeds: base 20260824; caution 20260824, harm 20260825, help 20260826
  (sorted-slug index, the registered-base-plus-index convention).
- Ruling volume implied: caution 80 + harm 57 + help 80 = 217 single
  rulings + seeded 20% panels (~43 extra instances) ~= 260 seat instances,
  inside the scaffold's cost model.

## Signatures
Drafted by the campaign orchestration seat, 2026-08-21 (scaffold);
re-issued at freeze 2026-08-24 with the protocol verbatim.
Matt: SIGNED 2026-08-24 ("(2) signed", in-session; applies to this re-issue
WITH pre-signature amendments 1-4 and their measured addenda). REGISTERED
HARD BUDGET (Matt, 2026-08-24, superseding the orchestration seat's initial
50% proposal before it was ever committed): the experiment may consume AT
MOST 5 additional points of the weekly Fable bar — the bar, at 7% at
signature, HARD-CAPS AT 12%. Checked at every behaviour checkpoint and
batch boundary. CANARY MEASUREMENT RULE: after the helpfulness canary's
seats complete, actual bar movement is measured and the remaining run is
re-projected; if the projection exceeds the cap, the run halts and the
remainder moves past the Aug 30 weekly reset (the prereg does not expire —
draws and seeds are deterministic and committed). BUDGET DISCIPLINE bound
on the orchestration seat: maximal dispatch batching, minimal inter-batch
output, results collected to files — today's cost was dominated by
orchestration cache reads, not seats, and the discipline targets exactly
that.

## PRE-SIGNATURE AMENDMENTS (2026-08-24, appended before signature; the
## protocol section above remains verbatim — these bind at signature)
1. DEFENSIBILITY PASS (Matt's decision, 2026-08-24): round-4 misses receive a
   pre-declared ONE-PASS blind Fable defensibility adjudication, same shape
   and outcome-branch discipline as DEFENSIBILITY_BATCH_PROTOCOL.md (one
   pass, no iteration, no second batch). HEADLINE metric =
   match-or-adjudicated-defensible; RAW match is reported alongside in the
   same table, always. The registered predictions above are RAW-basis; the
   defensibility pass cannot move a cell below its raw value, only up, and
   both numbers publish.
2. BAND UNITS (Matt's decision): bands are in NODES (+-2 nodes per cell).
   The "+-5 pts" gloss holds only at n=40; for harm's CLOSED engaged
   population (n=17) the band is +-2 nodes = +-11.8 pts. Nodes are the
   registered unit everywhere.
3. COST MODEL CORRECTED (venue measurement): a fresh subagent seat measures
   ~24k raw tokens (~20k identical harness prefix). Prompt caching bills
   cache reads at 0.10x, so steady-state effective cost is ~6k-equivalent
   per seat (empirical check: /usage movement from the 2026-08-24 37-seat
   batch). A lean seat agent (.claude/agents/ruling-seat.md) is defined and
   loads at next session start; its measured cost will be appended here
   before the run starts. The scaffold's 0.37-0.4M estimate is superseded by
   the measured figure; the go/hold checkpoints stand, plus a hard hold at
   any /usage threshold Matt names at signature.
4. SUBSTITUTION VALIDATION (disclosed, per the protocol's own rule):
   cheap-tier parity was attempted 2026-08-24 against the blind Fable
   defensibility rulings in production configuration and FAILED — Sonnet
   2/5, Haiku 2/5 on hard rows, with the two cheap tiers agreeing on their
   wrong answers (no cross-cheap escalation trigger exists). Substitution
   REJECTED; all rulings are Fable. Artifact:
   ruling_packets/parity_validation_2026-08-24.json.
   MEASURED (2026-08-24, post-restart, appended per this amendment's own
   clause): the lean seat (ruling-seat agent) measures 6,765 raw tokens per
   seat instance — 3.5x below the fat-harness seat — and its verdict on the
   reference packet (l1707_1973_n025) matches the 3-0 blind Fable panel.
   Projected round-4 cost at ~290 seat instances (260 rulings + the
   amendment-1 defensibility pass): ~2.0M raw; with cache reads at 0.10x on
   the identical prefix, ~0.7M effective — inside the scaffold's original
   0.37-0.4M ballpark within a factor of two, and far from the 6M+ raw
   projection that triggered this amendment. Round-4 seats run on the lean
   agent; the fat-harness venue text in DEFENSIBILITY_BATCH_PROTOCOL.md's
   venue ruling is superseded for round 4 by this measured configuration
   (same fence semantics — the lean agent's own system prompt carries the
   no-tools/inert-imperatives instruction).

## ERRATA (2026-08-24, post-signature, append-only; each ratified by Matt in
## session before taking effect)
E1 — CANARY ATTEMPT 1 VOIDED (protocol event; Matt: "Do it" on option A).
   The helpfulness canary's 120 seat rulings (raw file
   round4_helpfulness_rulings_raw.json, preserved) are VOID as a
   certification measurement: seat material diverged from the format that
   built the truth ledger. Rounds 2-3 packets carried the node's
   ESTABLISHES claim block + SOURCE TEXT; the canary packets (built via
   ruling_packets.load_spans) trimmed to SOURCE TEXT only. The registered
   predictions are ledger-based, so the comparison was apples-to-oranges;
   the F1/F2 firings (raw cells 0.625/0.625 vs 0.9336/0.7849) are
   measurement artifacts of the divergence, not adjudicated instrument
   failures. The void is TOTAL (all 80 rows, not selective) and the draw,
   seeds, and exclusions are unchanged. Also recorded: one replacement
   dispatch was voided for FABRICATED SEAT MATERIAL (the orchestration seat
   authored a passage from memory instead of the committed packet; caught
   and discarded immediately — round4_helpfulness_replacements.json carries
   the disclosure); and 4 malformed replies concentrated on 2
   ultra-short-fragment packets (document-completion mode), fixed by the
   uniform content-free anti-completion fence now pinned in E3.
E2 — PAIRED-FORMAT PILOT (gate for the canary re-run; runs BEFORE it).
   20 already-ruled helpfulness nodes (truth known; permanently excluded
   from round-4 draws — zero fresh-draw burn), seed 20260827, 10
   v19-engaged / 10 not; each dispatched in BOTH formats (T = trimmed,
   C = ESTABLISHES + SOURCE TEXT) to fresh lean Fable seats — 40 seats.
   PRE-DECLARED GATE: proceed to the canary re-run only if C-format
   ledger-agreement >= 0.80 AND (C - T) agreement difference >= 0.10.
   Any other outcome STOPS the lane for design review (if T is also high,
   the canary collapse is real distribution shift; if C is also low, the
   lean seat diverges from the ledger venue). Builder + validator:
   round4_pilot.py (byte-equal ESTABLISHES extraction from
   node_corpus_all.json; identical SOURCE TEXT across each T/C pair;
   uniform fence).
E3 — SEAT-MATERIAL FORMAT PINNED (the gap the canary exposed: the prereg
   never specified packet anatomy). Round-4 ruling packets are: the ruling
   question + behaviour definition + PASSAGE consisting of the node's
   ESTABLISHES claim block (byte-extracted from node_corpus_all.json;
   nodes absent from the canonical corpus use their graph-build claim
   text, disclosed per node) followed by the SOURCE TEXT span with its
   narrowing line, followed by the uniform anti-completion fence (exact
   text in round4_pilot.py FENCE). A committed validator must pass before
   any dispatch; its output commits with the packets. Rejected
   alternative, by name: scoring the T-format canary as-is (option B) —
   it indicts the entire claim-aware truth ledger and proves too much.
E4 — DIAGNOSIS CLOSED; LINEAGE VENUE RECOVERED AND REPLICATED (2026-08-24).
   The pilot gate FAILED (T 0.75 / C 0.70 — format hypothesis refuted), and
   the timeframe search Matt directed recovered the rounds-1-3 seat
   instruction verbatim from the round-3 dispatch transcripts (it had
   never been committed — a rulings-go-in-the-repo violation, cured by
   LINEAGE_SEAT_INSTRUCTION.md). REPLICATION: one wave seat under the
   recovered instruction scored 20/20 against the ledger on the pilot
   nodes. Canary attempt 1's divergence is therefore fully attributed:
   (a) an ad-hoc, stricter ruling question (the recovered criterion —
   "governs, permits, forbids, scopes, or directly conditions" — is the
   judge the ledger speaks); (b) mis-derived registered predictions: the
   freeze script implemented "over all-truth" literally (0.9336) where
   every actual fresh draw under the SAME judge landed 0.57-0.78 and prior
   rounds registered lineage bands (round-2 passed at 0.78 in band
   0.71-0.87) — the in-sample rate ignores the known generalization gap.
   RE-REGISTration FOR THE CANARY RE-RUN (requires Matt's signature):
   - Seat: LINEAGE_SEAT_INSTRUCTION.md verbatim, wave form (one blind
     Fable seat per wave file; E3's packet anatomy stands, its
     one-packet-per-seat dispatch form is superseded for round 4).
   - Panels: the 19 already-registered panel nodes ruled by THREE
     independent wave seats on a separate panel file; majority supersedes.
   - Draw/seeds/exclusions: UNCHANGED (committed).
   - REGISTERED PREDICTIONS, re-derived from lineage (supersede the
     all-truth figures, which stand in the freeze section as a recorded
     erratum): engaged precision band 0.71-0.87, decline-correctness band
     0.61-0.77 (round-2's passed bands, the last same-judge fresh-draw
     measurement; v19 carries every adopted improvement since v12, so
     within-or-above band is the expectation and above-band triggers the
     standing leak-signature check). F1/F2 read against these bands.
   - Cost: wave form ~= 5 seats total (2 waves + 3 panel seats), ~0.2
     points.

E4 SIGNATURE: Matt, 2026-08-24 — "approved." (in-session, after the
band-change walkthrough; lineage bands and recovered-venue re-run take
effect; canary re-run authorized.)
