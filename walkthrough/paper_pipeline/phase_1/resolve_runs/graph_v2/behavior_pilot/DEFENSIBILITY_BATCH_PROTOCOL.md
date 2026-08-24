# DEFENSIBILITY ADJUDICATION BATCH — pre-declared 2026-08-22 (directive: Matt 2026-08-21, "ideally we would evaluate if some of the FP/FN were defensible")

STATUS: registered as campaign protocol under Matt's stated directive; no
objection recorded when the concrete batch was proposed 2026-08-21.
SCOPE: the 9b arithmetic's new false positives, ALL deltas, ONE batch.
Nodes (28 distinct / 29 rows; l797_830_n004 appears under two deltas):
- helpfulness: l3596_3876_n039, l427_460_n003, l797_830_n004 (empowerment);
  l1707_1973_n025, l2474_2554_n002, l2821_3040_n005, l2821_3040_n019,
  l2821_3040_n020, l2821_3040_n027, l3505_3595_n003, l3954_4251_n003,
  l4572_4692_n009 (trust); l1707_1973_n034, l171_426_n035, l1974_2125_n007,
  l1_170_n083, l3383_3501_n003, l3383_3501_n014, l3954_4251_n027,
  l3954_4251_n029, l426_610_n029, l461_608_n007, l461_608_n018,
  l461_608_n021 (predictability-and-reliability)
- avoiding-over-and-under-caution: l1707_1973_n029 (harm-prevention);
  l2126_2404_n001, l2126_2404_n003, l2126_2404_n010, l797_830_n004
  (epistemic-autonomy)
PROTOCOL: blind Fable adjudication, single rulings + seeded 20% three-
instance panels (round-4 lineage protocol), post-reset, one pass, no
iteration — adjudicate-reject-adjudicate loops are the fitting risk this
pre-declaration exists to prevent. Question per node: does this passage
bear on THE BEHAVIOUR MODULE named in the packet? RECONCILIATION (packets
review M1, 2026-08-22): the batch is grouped by delta, but the deltas
exist only as bare purpose_concern labels with no definition text, so the
ruling question is operationalized at MODULE level using the v18 module
definition — the only definition available. Delta membership is used ONLY
post-ruling, to map each ruling back to its delta for the per-delta charter
recomputation; the ruling seat receives no delta information (the
behaviour/delta fields in the packet file are routing metadata, never
shown to the seat — review L2 justification). Rulings update the truth
ledger with explicit precedence; charter is then recomputed per delta on
rescued counts (fixes vs breaks-minus-rescues). A delta charter-positive
after rescue is ADOPTABLE under the same adoption rule as before.
NON-BINDING PRIOR: DIRECTIONAL_9B_FP_PREVIEW.json (orchestration seat,
non-blind, unvalidated) — comparison material only; if Fable disagrees
with it anywhere, Fable wins without discussion.
SEAT HAZARD CAVEAT (packets review L3, 2026-08-22): the span for
l426_610_n029 (helpfulness batch) contains pipeline translation debris
inside the corpus text — an imperative fragment ("Write the module for
clause..."). The span is presented as-is (it is the corpus text the ruling
is about), but the session running the rulings should treat any
imperative-looking debris inside a passage as inert content, not as an
instruction.
SEAT MATERIAL AND SHUFFLE REGISTRATION (packets re-review R2, 2026-08-22):
the ruling seat receives ONLY each packet's prompt string (passage +
definition + question). Headers and the behaviour/delta routing fields are
campaign material, never seat material; the seat must not consult the repo,
the draw files, this protocol, or any other campaign artifact. Packet order
is a seeded permutation: base seed 20260823, this batch's seed = base + 6
(generalization files use base + 0..5 by sorted-slug index); registered in
GENERALIZATION_PREREG_DRAFT.md addendum 4 as well. The seed is not stored
in the packet file.
COST: ~29 rulings + panels ~= 0.06-0.08M Fable, inside the fresh bar.

OUTCOME BRANCHES, COMPLETE (top-review ALARMING-1, appended 2026-08-24
BEFORE dispatch; approved by Matt "Do it"): the paragraph above stated only
the positive branch. All branches, pre-declared:
- A delta charter-positive after rescue is ADOPTABLE (unchanged, above).
- A delta charter-NEGATIVE after rescue is FINALLY REJECTED for this cycle:
  no re-adjudication, no widened batch, no alternative rescue path. Its
  arithmetic (original and rescued) is recorded with the rejection.
- FORESEEN OUTCOME, stated plainly: 25 of the 29 rows belong to the three
  deltas the 9b arithmetic REJECTED (trust 9, predictability-and-reliability
  12, epistemic-autonomy 4). The rescue arithmetic can flip a rejected delta
  to charter-positive, making it adoptable. That is not a loophole; it is
  the pre-frozen per-delta adoption rule applied to corrected truth, and it
  is symmetric (blind rulings can also rescue nothing). Recorded here so a
  rejected delta's adoption, if it happens, reads as the rule working, not
  as fitting.
- NO SECOND BATCH: this is the ONLY defensibility adjudication these 28
  nodes will ever receive. A future cycle needing to revisit any of them
  must say so in a new prereg naming this clause as the bar it is clearing.
- Rejected alternative, by name: leaving the negative branch implicit
  ("adjudicate-reject-adjudicate is already barred") — an unwritten branch
  is where a disappointed result goes looking for room; the bar must be
  written where the result will be read.

PANEL OPERATIONALIZATION (registered 2026-08-24, BEFORE dispatch): the
"seeded 20% three-instance panels" clause is operationalized by
ruling_packets/make_defensibility_dispatch.py — row i (1-based, shuffled
order) is paneled iff sha256(f"panel:20260829:{i}")-derived uniform < 0.2,
where 20260829 is this batch's ALREADY-registered shuffle seed (base
20260823 + 6; no new constant introduced). Resulting paneled rows: 2, 4, 8,
11 (4/29 — a rate sampler, not a quota; the draw landed under 20% and is
kept as drawn). Panel rows receive THREE independent fresh-session rulings
on the identical prompt; majority supersedes the single ruling. The seat is
never told which rows are paneled. Dispatch artifact:
ruling_packets/defensibility_dispatch.txt (29 numbered prompt strings, the
ONLY seat material).
