# RULING 02 — how much of the blind survived, and what replaces it

**Written after F1 completed and before any identification was scored.**
Recorded in the repo, not the transcript.

## What happened

`PREREG.md` §4.2 committed to scoring identification from a pool with cell
labels stripped, and disclosed in advance that the blind was already broken on
**four arm-E replies** I had read while designing the arm.

⛔ **It is now broken on more than that.** While the F2 critic phase was running
I read **all five of cell F1's `edits.md` files** — which are nothing but F1's
extracted FIX lines — in order to see whether the disjunction ban had taken
effect. It had, and the reading was informative, but it means **I can recognise
F1's five repaired replies in the pool.**

Nothing was reordered, deleted or re-run to hide this.

## The tally, stated exactly

| replies in the pool | blind | **NOT blind** |
|---|---|---|
| arm E (13) | 9 | **4** (`l171_426_n022`, `l3147_3238_n003`, `l3239_3382_n002`, `l4252_4482_n005`) |
| F1 (7) | 2 | **5** (every clause that produced FIX lines) |
| F2 (n) | **0** | **all of them** |

⛔ **AMENDED, same session, before scoring: the blind did not survive at all.**
While F2's critic phase was running I read its FIX lines too, to check that the
`PRESERVE:` field had taken (M2). **So the honest statement is not "the blind is
damaged" — it is: THE BLINDING PROTOCOL FAILED. Every cell's replies were read
with their cell known before any identification was scored.** The pool, the
opaque ids and the seal were built and are on disk, and they did their
mechanical job; what they could not survive was my reading the outputs while
operating the run. That is a defect in the PROTOCOL — a single agent cannot both
drive a live experiment and be blind to its outputs — and it is reported as a
finding about the method, not buried in a limits list.

⛔ **So the F1-vs-armE identification contrast — the one the blind was there to
protect — is the contrast whose blind is most damaged.** That is the honest
statement and it is not softened.

## The decision

⛔ **The pool is scored anyway, the broken-blind replies are marked in
`_sealed_map.json` and counted in `RESULT.md`, and a SECOND, fully
adjudication-free identification number is reported beside the adjudicated
one.**

### The replacement instrument: the frozen-anchor prefilter

`key/frozen_key.json` carries, per item, `anchors` — token groups written
**before any reply existed** and hashed (`16965c45…af45aa6`). A line is a
prefilter match for an item if it contains every token of any one group.

⭐ **The prefilter rate involves no judgment of mine at any point.** It is
computed by `blind_pool.py` from a file frozen before the first API call, on
replies it cannot distinguish. It is coarse — it will over-count (a line naming
the right field with the wrong change matches) and under-count (a correct
finding phrased around the anchors does not) — **but it cannot be bent toward a
cell, and I cannot bend it now without changing a hashed file.**

**Both numbers are reported for all three cells. Where they disagree, the
disagreement is the finding**, and the prefilter number is the one quoted in any
cross-cell comparison the broken blind touches.

## Rejected by name

* ***Re-run F1 so a fresh set of replies can be scored blind.*** It costs money
  for no new information, and the second draw would differ from the one whose
  repairs are already on disk, so the identification and repair numbers would no
  longer describe the same objects.
* ***Drop the identification measure and report only Tier 1.*** Tier 1 is the
  headline (`PREREG.md` §3) and it is unaffected — but identified-vs-repaired is
  what distinguishes this arm's question from a floor comparison, and discarding
  it because I damaged one instrument would hide the damage rather than report
  it.
* ***Score F1 first from memory and call it blind.*** Not a real option; named
  here because it is the shape the temptation takes.

## What is unaffected

⭐ **Every Tier-1 measure — `asserts` delta, `floor_clean`, `errors`, polarity,
bodiless asserts, self-cited glosses, closure mix, class B, class C — is
computed by imported code on the modules themselves and involves no judgment of
mine.** `PREREG.md` §3 already put those first, before this happened, and they
carry the arm's headline. The named `l3147_3238_n003` case is likewise decided
by counting `asserts` and reading the module, not by matching a sentence.

— adjudicator, 2026-08-16, mid-run
