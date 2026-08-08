# Transcription review — five stage-1 files against `resources/03_pipeline.md`

**Reviewer:** clean (did not write the design or any file under review). **Date:** 2026-08-07.
**Brief:** `model/REVIEW_BRIEF.md`. **Question:** does each file still say what the design says, and
does it say nothing the design does not?

Nothing was edited. `guard.py --accept` was not run.

## Run output

```
guard.py                → RED. 1 stale (resources/03_pipeline.md), 5 never reviewed. exit 1
guard.py --self-test    → all PASS, exit 0
pytest walkthrough/model                          → 22 passed
pytest paper_pipeline/phase_1/test_schema.py      → 97 passed
```

Both complete worked-example modules in `20_worked_example.md` were extracted and run through
`schema.validate_all()`: **both validate clean.** The five bad ones are deliberate fragments, as the
file presents them.

## Verdicts

| file | verdict |
|---|---|
| `prompt/00_task.md` | **faithful**, with two recorded minor drifts (I1, I2) |
| `prompt/10_output_format.md` | **drifted** — F, and the vocabulary in B is not licensed by the design |
| `prompt/20_worked_example.md` | **drifted** — D, E |
| `prompt/30_failure_modes.md` | **drifted** — C. Otherwise the most faithful of the four |
| `schema.py` | **partly cannot review** — see B. Its validators and messages trace; its central relation vocabulary does not |

⭐ **Where I decline.** I can trace every validator, every error message and every field *behaviour*
in `schema.py` back to the design. I **cannot** license its four-relation vocabulary from
`03_pipeline.md` at all — `defines/3`, the closed status set `forbid/permit/oblige/prefer`, and the
separate `ontology` / `concepts` blocks appear nowhere in the source of truth. They are recorded in
`STATE.md` NEW-5, but `README.md` says `03_pipeline.md` outranks every other document in this
directory. So for the part of the contract that five files are transcribed *from*, I am reviewing a
transcription of a document that does not contain the original.

---

## Ranked findings

### A. The design still specifies `provides`; the implementation removed it deliberately — **the design is behind**

The design states the declared interface as three parts, in three places:

> line 350 (stage-1 diagram): `O2[2 · declared interface<br/>provides / requires / inputs]`
> line 449: *"**A declared interface** — what this module *provides* to others, what it *requires*
> from them, and what counts as a fact about the case…"*
> line 476: `provides:  list[str]      # ['lifted/2', 'binds/2']  what others may use`

`schema.py` has no `provides` field; `10_output_format.md`'s field table (48–64) has no such row;
`00_task.md` rule 9 (85–93) restates the interface as **ontology / requires / inputs**.

This is not an omission by the transcription. `link.py:746-755` records the removal with grounds:
the `provides` check could not fire on any stage-1 output, and its companion warning fired on every
module, *"training the reader to ignore the tool's warnings"*; what a module provides is now taken
to be what it defines. That reasoning is sound and lives in a **code comment**.

⇒ **Fix belongs in the DESIGN** (all three sites). Highest cost if left: this is the one element a
clean reader is guaranteed to flag as a dropped requirement — I did, and only found the grounds by
grepping `link.py`. The next reader re-adds `provides` to the prompt and to `Module`.

### B. The stage-1 relation vocabulary is not licensed by the source of truth

Open question 1's CLOSED section (770–801) — which the task named as the section to check against —
licenses exactly four things, and all four are present and correct in the transcription:

> *"one encoding of the document (`asserts/3`), one of the behaviour (`b_asserts/3`)"* ✅
> *"act-index both sides — without it the natural encoding derives **zero** conflicts, silently"* ✅
> *"`beats/2` → **`beats(Sayer, Winner, Loser)`**"* ✅
> *"a **forced, per-act default-closure declaration**"* ✅
> *"⛔ The namespace separation is mandatory… Enforce with a type constraint."* ✅

It licenses **none** of the following, which the transcription treats as the settled contract:

| in the transcription | where | in the design |
|---|---|---|
| `defines(ClauseId, Kind, Term)` as one of four relations | `10_output_format.md:19`, `schema.py:15`, `Definition` | absent |
| statuses closed to `forbid/permit/oblige/prefer` | `schema.py:46`, `10_output_format.md:22` | absent. `prefer` is *motivated* by *"comparatives… which have no violation condition"* (796) but never named |
| a separate `ontology` block, non-deontic, ablatable | `10_output_format.md:20`, `OntologyFact` | absent as a relation. Invariant 1 licenses concepts-with-definitions, not this split |
| `concepts` as a distinct declaration type | `Concept`, `Concepts`, `concept_rows` | Invariant 1 licenses the *content* (see below); the type is not in the design |
| `RESERVED` name set | `schema.py:50` | absent |
| *"Measured on this corpus: the contradiction verdict FLIPS on the closure, and `open` and `cepa` are bit-identical"* | `30_failure_modes.md:41`, `Closure` docstring | absent from the design; licensed by `contradiction_probe/FINDINGS.md:133-134` and `STATE.md:76-78` |

All of it is recorded in `STATE.md` NEW-5 and NEW-2. None of it is in the design.

⇒ **Fix belongs in the DESIGN** — fold `STATE.md` NEW-5 into the CLOSED section. Cost if left: the
guard will fire again, and the next clean reviewer will hit the same wall. This is the failure the
apparatus exists to prevent, one document upstream of where it is currently looking.

The parts that *do* trace, quoted, so the accepted material is on the record:

- **Licences.** `Licensed` (150–198) and `00_task.md`'s licence table are Invariant 2 (115–140)
  almost verbatim, including *"Binary rejection has a bad escape hatch… behind a passed check"* →
  the `textual`-with-no-citation message, and *"A conclusion inherits the weakest licence"* →
  `00_task.md:34`.
- **Glosses.** `OntologyFact.gloss` / `Concept.gloss` and `10_output_format.md:36-38` reproduce
  Invariant 1 (74–77) near-verbatim: *"the read-back must render **the definition, not the label**.
  Otherwise a clause pointing at the wrong concept produces a paraphrase that reads correctly and
  nothing catches it."*
- **`requires` vs `inputs` disjointness.** Design 490–492, verbatim in the error message.
- **`forbid_body`.** Design 481–483 and problem #14 (43).
- **`Superiority` docstring** on exceptions living in their own file: Invariant 3's ⛔ note (154–159).
- **Abstention.** Design 494–501.
- **`Breach` carrying no fix and no expected value.** Design 431–439.

### C. `30_failure_modes.md:39` instructs an output the format cannot carry

> *"**11** Test cases describing impossible situations … ⇒ **this one you can prevent**: write
> integrity constraints for states the document treats as impossible."*

The design's #11 (line 40) says only that a program accepted an impossible state; it never assigns
integrity constraints to the translator. And `Module` has **no field for a constraint** — not
`asserts` (a status must attach to an act), not `ontology` (non-deontic classification), not
`forbid_body` (head + banned name only) — and `render_lp` emits none. So a model that follows this
instruction either has nowhere to put the result, or smuggles it into a body.

⇒ **Invented, and unactionable. Fix in the TRANSCRIPTION** (delete it, or add the field first).
This is the clearest single invention I found.

### D. Two of the design's five bad worked examples were replaced

The design's stage-1 diagram asks for *"worked examples: one good, five bad"* (332) and its own
table (512–518) names the five: invents an entity · **translates in isolation** · reasons from an
absence · **imports a name without its content** · turns a negative into a positive.

`20_worked_example.md` keeps three and substitutes two: **"the act is a material, not an act"**
(148) and **"the superiority has no sayer, or invents one"** (163). Both substitutes are licensed by
the CLOSED ruling — *"without it the natural encoding derives zero conflicts, silently"* and
*"unreachable because nothing records who said it"* — so this reads as a deliberate post-ruling
update, not an accident.

But the two dropped are the design's #2 and #5, and #5 is the one it singles out as
*"**Survives a paraphrase check by construction**"* — the hardest class to catch later. They survive
as table rows in `30_failure_modes.md` and as rules 2 and 5 of `00_task.md`, so they are not absent
from the prompt set, only from the worked examples — and the design's stated reason for worked
examples is that *"a reviewer told only 'is this faithful?' passed a fabricated policy. Naming the
failure is what makes it visible."*

⇒ **Fix in either, but record it.** My recommendation: update the DESIGN's five-bad table to the
post-ruling five and note that hollow stubs and isolation are covered by the rule list — or add two
more bad examples. Do not leave the two documents naming different fives with nothing saying so.

### E. No `world`-licensed fact appears anywhere in the prompt set

The design's *"What a good one looks like"* (505–508) describes the m0255 module as one that
*"marks the one fact that came from general knowledge rather than from the text"*, and Invariant 2
(119–121) names it: `protects_third_party(restricted_content)`, *"which is asserted, not read from
any clause"*.

The worked example's good module carries four `assumed` ontology facts and **zero `world` facts**;
`protects_third_party` does not appear. Neither does a `world` example appear in `10_output_format`
or `30_failure_modes`. So the one licence class with a distinct extra obligation — `toggleable:
true` — is demonstrated nowhere, while `assumed` is demonstrated four times.

⇒ **Fix in the TRANSCRIPTION.** Cost: `world` facts get marked `assumed`, and the design's stated
payoff — *"change one asserted fact and the match disappears"*, made visible by toggling — loses the
handle it depends on. Note that `Licensed` (163–167) is the only place in the whole set that
explains what toggleability buys.

### F. `concepts` is missing from `10_output_format.md`'s field table

The Fields table (48–64) lists thirteen fields and omits `concepts`, which is **required** by
`schema.py:529`, described at length immediately above the table (28–38), and used in the worked
example. A model reading the table as the field list will omit it.

⇒ **Fix in the TRANSCRIPTION.** Small, concrete, cheap.

### G. Invariant 2's required fourth licence class is unrecorded in `schema.py`

> design 133–136: *"⛔ **The three classes do not reach the behaviour side.** … **A fourth class is
> required** — found 2026-08-07."*

`Licensed` says *"Three licences"* flatly. I believe this is **correct for stage 1** — stage 1 never
sees a behaviour, and `BEHAVIOUR_NS` rejects any reach into it — but nothing anywhere says so, so
the next reader cannot tell a scoped decision from an unnoticed gap.

⇒ One line in `schema.py`, or one line in the design scoping the fourth class to the behaviour side.

### H. Design contradicts itself — reported, not resolved

The task asked specifically about repair and about stale diagrams. **The stage-1 diagram is
correct and coherent with the rewritten prose**: `REP` (355) reads *"REPAIR — one accumulating
transcript. Carries: the model's own prior modules + every check they failed, with reasons. ⛔ Only
stage-2 findings. Never a verdict."* — that matches 393–443 exactly, and no other stage-1 text still
says "fresh conversation".

**The Part 3 diagram did not get the rewrite.** Its `FIX` node (185) is labelled *"REPAIR — an
accumulating transcript, given every failing check with its reason, NEVER an expected verdict"* —
but it takes edges from `RUN -->|mismatch| FIX` (190, stage 3) and `DIV -->|empty set| FIX` (200,
stage 4), whose findings the design's own table (424–426) says **do** carry an answer key
(*"⛔ **Yes.** The cases carry their must-forbid / must-permit labels"*). The diagram shows no
ORIGIN filter, so read alone it asserts the thing 431 forbids.

⇒ **Fix in the DESIGN.** This is the highest-cost of the internal contradictions: the ORIGIN rule is
the one the design says *"must exist from the first version — retrofitting it once stages 3 and 4
attach is how the denial dissolves with nothing to notice."* (It **is** implemented, correctly, in
`checks.py:96-139` and `translate.py:1948-1978`, with `origin` required, positional and never
defaulted. The code is ahead of the top-level diagram.)

Others found, none of which the transcription inherited:

- **16 vs 17 failure modes.** Part 3 diagram `A4` (171) says *"the 16 error cases"*; the stage-1
  diagram `I3` (333) says *"the 17 known failure modes"*; the Part 1 table has 17 rows.
  `30_failure_modes.md` says 17 and reproduces all seventeen with the design's own grouping and both
  measured figures (12 of 13; 46 of 228) intact. **The prompt is right; line 171 is stale.**
- **Stage numbers.** `### 6 — Divergence` and `### 5 and 6 — Why normalising and parameterising…`
  both claim 6. `### 9 and 10 — Testing the tests` contains a subsection headed `**11 — Translate
  twice**`. Open question 3 says *"Stage 7's merge"* but stage 7 is EXPAND and the merge is stage 5.
  Open question 4 says *"seat 5c"* but the seats are 4a–4d. Part 4 stage 1 says *"the probe cases at
  stage 4 are the unit tests"* and *"Stage 4 tests it"* while the diagram makes test cases stage 3
  and stage 4 the read-back.
- **Part 6 (957): *"⭐ Stage 1 has never been run."*** `STATE.md` records three clauses run today
  (m0255 contaminated, m0091 translated, m0217 validator-rejected). Design stale.
- **Enforcement sites.** 794 says the forced closure is *"enforced in `link.py`"*; it is enforced in
  **both** `schema.py:597-615` and `link.py:501`. 783 says the namespace separation is enforced
  *"with a type constraint"*; `schema.py` enforces it by rejecting `BEHAVIOUR_NS` names at
  validation, which is not an ASP type constraint. Neither is wrong; the design names one site each.

### I. Minor drift inside the prompt set

1. **`00_task.md:38-39`** — *"**A rule is not a fact.** … Licences are for the facts your module
   asserts."* But `10_output_format.md:79` puts a licence on every `asserts` and `beats` entry, and
   those carry a `body` — i.e. they *are* rules; the worked example's `beats` entry is a rule with
   `licence: textual`. The design's sketch does separate `facts` (licensed) from `rules` (read-back
   annotated), so `00_task` is faithful to the *design* and inconsistent with its *sibling files*.
   Fix in the transcription, and note it as a consequence of A/B.
2. **`00_task.md:109-112`** — the abstention grounds (*"a section heading, it states a goal rather
   than a condition, it is an example"*) are not in the design, which gives none. Repeated in
   `schema.py:514-515`. Harmless, unlicensed.
3. **The `%` substitution marker and `%!trace_rule`** (`10_output_format.md:95-109`, `ReadBack`,
   `render_lp`) are a rendering mechanism the design does not specify. Consistent with #7 and with
   the read-back requirement; noted only so it is not mistaken for a design element.
4. **`00_task.md` never states that cross-referenced clause texts will be supplied** — the design
   makes this one of the four given items and calls it load-bearing (*"a clause that modifies rules
   defined elsewhere cannot be translated in isolation"*). Rule 2 hedges: *"If you were shown the
   cross-referenced text, you may cite it."*
5. **The concept dictionary is absent from the prompt** — correct while open question 2 is open, but
   `STATE.md` NEW-6 records that *"Invariant 1's arm B was adopted by implementation, not by
   decision"* and that the design still calls it open. That belongs in the design.

### J. Out of scope but adjacent

`paper_pipeline/phase_1/README.md:84-102` is a stage-1 conformance table and **three of its rows are
now false**: licences ⛔ *"absent"* (they are the backbone of the schema), format forcing ⛔
*"instruction-following plus a regex"* (it is strict `json_schema`), and *"the five bad are a prose
table, not five worked modules"* (they are five JSON snippets). It is not a watched file, but it is
what a reader consults to learn what conforms.

---

## What I would re-check first with ten minutes

**Open question 1's CLOSED section against `schema.py`'s vocabulary (finding B).** Five files were
transcribed from that section, and it does not contain three of the four relations they implement,
the status set, or the ontology/concepts split — all of which live only in `STATE.md`. Until that is
folded in, no reviewer can license the centre of the stage-1 contract from the source of truth, and
this whole review has to end in a partial decline again. Everything else on this list is cheaper
than the second occurrence of that.
