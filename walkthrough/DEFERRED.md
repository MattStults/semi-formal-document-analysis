# Deferred features

Things this design will need and is deliberately not building yet. Each entry records **why it is
safe to defer** — specifically, what it does *not* block — because that is the claim that can turn
out to be wrong.

⚠️ A deferral is only honest if deferring it changes nothing about what we build in the meantime.
Where that check was actually run, it is recorded.

---

## D-1 — Ordering (the lexicographic grade)

**Deferred 2026-08-07.** Phase-0 work is hand-executing stage 1; ordering is a query-side product
feature and the query side barely exists.

**What it is.** A set of relevant clauses returned in a defensible order rather than unordered.
Described in `semi-formal-experiment/HARNESS_REDESIGN.md` as lexicographic over discrete features,
never a fitted score — a score invites weights and weights invite fitting. Four tiers, precedence a
user control, document order as the final tie-break:

1. **match completeness** — how much of the behaviour's definition is derivable
2. **derivation directness** — own facts > one hop > many > closure only
3. **licence strength** — proof uses only `textual` > requires `assumed` > requires `world`
4. **salience** — the clause's speech act: rule-stating > illustrating > commentary

**⭐ Why deferring is safe, checked rather than assumed.** Ordering's only blocker is that facts do
not carry licences. But licences are required by three things that are *not* ordering — the
citation checker's coverage denominator, CQ-1's weakest-licence output, and Invariant 2 itself. So
the licence work proceeds regardless, and **nothing stage 1 emits changes**: a fact declares
`textual`/`assumed`/`world` whether or not anything later sorts on it.

**What it blocks:** nothing currently being built. CQ-1's `answer_shape` was amended to return an
unordered set and to name this entry.

### Open questions to answer when it returns

- ⭐ **What produces the set?** Ordering needs a set to order, and nothing produces one — the
  behaviour encoding is a single hand-written file with hardcoded clause ids (stage-0 finding F3).
  This gates every tier and is the first thing to resolve.
- ⭐ **Is tier 3 one value or a family of minimal supports?** Stage-0 finding **F4** showed the
  simple version is already wrong: *"change that one fact and the match disappears"* was false — the
  match survived through a second independent world fact. Toggleability needs minimal supports,
  plural, which may change what "licence strength" means.
- **Tier 1 is a placeholder.** "How much of the behaviour's definition is derivable" is a
  reasonable starting measure and explicitly TBD; the wider repo's rung ladder was built for a
  lexical scorer and may not transfer.
- **Tier 2: derivation steps, or clauses traversed?** These differ, and for a document-analysis
  tool the second is probably the meaningful one — *"I had to pull in five other clauses"* is a
  different claim from *"the proof was five steps deep inside one clause."*
- **Tier 4: does the measured null transfer?** Salience returned null in the wider repo — but on an
  instrument that **discards ranking order entirely** (`benchmark.passage_scores` calls `dict(...)`).
  The null may be a property of the instrument, not of speech-act salience.
- **Configuration:** who chooses precedence, and must the chosen order be recorded with the result?
  The wider repo says yes — a sort control adjacent to a metric is a fitting channel.
- **Guard:** sorting must never change the set. Membership is the derivation's job.
- **Tie-break:** document order is total over clauses — but two of nine specimens examined had **no
  clause at all**, so they are unsortable and also unretrievable. That is a coverage problem wearing
  a sorting costume.
- ⭐ **Weakest-licence inheritance is stated and unbuilt, and tier 3 is the thing that needs it.**
  `resources/03_pipeline.md` Invariant 2: *"A conclusion inherits the weakest licence in its
  derivation."* `prompt/00_task.md:31` tells the model so, as a note. **Nothing computes it** —
  verified 2026-08-07: not `schema.py`, not `link.py`, not `checks.py`; the only occurrences of the
  word are those two statements of intent. Tier 3 (*"licence strength: proof uses only `textual` >
  requires `assumed` > requires `world`"*) is a statement **about a derivation**, so it cannot be
  read off the per-fact licences the contract collects; it has to be **propagated**. Note this is
  the same propagation the citation checker's licence-dependent denominator needs, and the same one
  D-4 below needs to make toggling mean anything — one piece of work serving three consumers, not
  an ordering feature.

**Revisit when:** a behaviour query returns a set, and licences exist.

---

## D-2 — The one deontic axiom, `O(¬a) ≡ F(a)`

**Deferred 2026-08-07,** when open question 1's CLOSED ruling was implemented in the stage-1
contract. Everything else the ruling requires was implemented in the same change; this one was not.

**What it is.** The corpus states the same prohibition in two polarities — `m0208` *"must not
generate restricted content"* → `F(produce(m))`, and `m0270` *"should refuse to help"* →
`O(refuse(m))`. Plain predicates see two unrelated ground terms, so the conflict **vanishes**
(`contradiction_probe/FINDINGS.md`, T1). The axiom relates an obligation on an act's complement to a
prohibition on the act, and is the one genuinely deontic thing the ruling adopts.

**⭐ Why deferring is safe, and the check that was actually run.** It is a **corpus-level reasoning
axiom, not a per-clause output.** Nothing a module emits changes: a module writes
`asserts(m0270, oblige, refuse(R))` whether or not anything later relates `refuse` to `produce`. So
the axiom can be added over an existing `asserts/3` corpus **without re-translating a single
clause** — verified by inspecting the contract: no field of `Module` mentions complements.

Contrast with the three parts of the same ruling that were NOT deferred, because each *does* change
what a module emits: act-indexing (`Assertion.act` is an act term), `beats(Sayer, Winner, Loser)`
(`Superiority.sayer`), and the forced per-act default closure (`Closure`, required for every act
class governed).

**Why it is not being built now.** It needs act **complementation** to be computable, and no naming
convention exists that makes it so: `refuse(X)` is not syntactically the complement of `produce(X)`.
⚠️ The probe's hand-written substitute is on the record as **O(n²) and wrong on its first attempt,
producing a false positive between a clause and a behaviour that agree.** Guessing a convention now
would bake it into 593 modules; deriving one later costs nothing already spent.

**What it blocks.** Cross-polarity contradiction detection, and only that. Same-polarity
contradiction, relevance, defeat and the closure question all work without it.

### Open questions to answer when it returns

- **What makes complements computable?** A declared `complement/2` per act pair, a naming
  convention (`refuse(X)` ↔ `produce(X)`), or an explicit act-complement declaration in the module.
  Only the third changes the stage-1 contract, which is the reason to decide before adopting it.
- **Is it needed for the document side alone,** or only where the document meets a behaviour? The
  probe found the break at the document↔behaviour join.

---

## D-3 — D4b-GLOBAL only: does a declared concept find a provider corpus-wide

⚠️ **Corrected 2026-08-07, same day.** A first draft of this entry deferred all of D4b. That was
wrong: it conflated three levels, and only the third is genuinely deferred.

| | scope | status |
|---|---|---|
| **1** every referenced concept is **declared** — in `ontology`, `requires` or `inputs` | per-module | ⭐ **implemented**, in `Module._coherent`. It is D1b applied to the ontology namespace |
| **2** every ontology predicate carries a **written definition** | per-module | ⭐ **implemented** — `OntologyFact.gloss` is required. Adding it closed an Invariant 1 violation that the first contract shipped with |
| **3** the declaration finds a real **provider** corpus-wide, and providers agree | link scope | **deferred — this entry** |

⭐ **Level 2 is why probing this was worth it.** The first contract let an ontology entry declare a
concept *by use* with no statement of what the predicate means. Invariant 1 requires that a symbol
resolve to a concept **with a written definition**, because *"the read-back must render the
definition, not the label"* — otherwise a clause pointing at the wrong concept produces a paraphrase
that reads correctly and nothing catches it. One required field fixed it.

**Deferred 2026-08-07.** `03_pipeline.md` stage 2's D4 is *"every fact cites a real clause **and a
real concept**"*. The clause half is implemented (`schema.validate(known_clause_ids=...)`); the
concept half is not.

**⭐ Why level 3 is not blocked on building an ontology.** The concept dictionary is **not a prior
artifact**. Every module carries its own **ontology block** — non-deontic classification facts, each
now with a gloss — so the dictionary is the *union of those blocks*, emergent as clauses are
translated. That is Invariant 1's **arm B**.

⚠️ **Recorded as a design amendment, because the commitment was made by implementation rather than
by decision.** Invariant 1 says the choice between arms is empirical and undecided; today's contract
picks arm B by construction. Anyone re-opening it should know it was decided this way and when.

⛔ **WITHDRAWN BY NAME: "stage 2 has picked arm B, so level 3 is link-scoped rather than blocked."**
*(Folded in from `phase_1/STEP_stage2_and_repair.md` §1 when that plan was retired, 2026-08-07.)*
That argument was made and is withdrawn on three grounds, any one sufficient:

- Arm B is *"concepts fixed in a separate step that maps names → concepts"*, and its recorded cost
  is *"needs a merge procedure with its own failure modes."* The argument claimed the arm and
  declined the obligation — a union of coined names **is** the un-normalised state arm B exists to
  normalise.
- Invariant 1 says *"not decided here… do not build the merge machinery before knowing which arm we
  are in"*, and open question 2 says *"run both arms on the same clauses."* Committing by
  implementation and recording it afterwards is not that.
- **Nothing in stage 2 needs an arm at all.** Level 3 excludes on the flat ground that *no
  corpus-wide provider index exists under either arm today.*

⇒ The exclusion stands on the flat ground. The arm-B note above is a record that a commitment was
made by implementation — **a thing to undo, not a thing to justify.**

**What deferring level 3 changes:** nothing stage 1 emits, and nothing stage 2 can check on one
module. It is a **link-scope** check exactly like D2 (witness) — blocked on having translated enough
clauses, not on a missing phase, and it resolves itself as the corpus grows.

**Consequence to carry:** problem #9 (same name, different meanings) now lives **inside the ontology
blocks**. Two clauses writing `disallowed/1` with different extensions link cleanly and are wrong.
That is a **stage 5 (normalise)** problem — see `SCRATCH_concept_phase.md` §5, where the merge veto
is the proposed instrument.

⚠️ **Sharper than "incomplete": the live wiring makes `concept-multi-gloss` STRUCTURALLY INCAPABLE
of firing.** `run()` accumulates `_concepts` across the whole run — exactly the data the check wants
— and then calls `repair_loop` **without** `concepts=`, so `run_checks` falls back to the module's
own rows and every link sees a one-module table. A check that reports over a population of one is
the "0.0000 means it measured nothing" shape (`phase_1/DEBUGGING_TIPS.md` §2), not merely a partial
check. Verified still true 2026-08-07.

---

## D-4 — `world` facts are marked toggleable but are not actually switchable

**Deferred 2026-08-07.** Invariant 2 requires a `world` fact to be *"marked and toggleable — a
result resting on world knowledge is a different claim"*, and `schema.Licensed` enforces the **mark**:
`licence: "world"` without `toggleable: true` is rejected (`schema.py:197`), and `toggleable` on a
non-`world` fact is rejected (`:202`). **The switch does not exist.** `render_lp` emits the fact
unconditionally and `_line` appends a trailing `% [W] toggleable` **comment** (`schema.py:910`); the
only thing in a rendered module that is actually switchable is the **whole ontology block**, via
`#const onto = on.` (`:972-973`).

**What this blocks, precisely.** `03_pipeline.md`'s citation-checker table gives the `world` row as
*"is it marked as world knowledge, and is it toggleable?"* — a deterministic check standing in for a
human seat. Today it can only check the first half, so half of that check cannot run. And D-1's
tier 3 ("licence strength") rests on the same mechanism, with stage-0 finding **F4** already showing
the naive version wrong: *"change that one fact and the match disappears"* was false, because the
match survived through a second independent world fact. **Toggleability needs minimal supports,
plural** — which is an argument for building the switch once, properly, rather than per-fact.

**Why deferring is safe.** Nothing stage 1 emits changes: a fact declares `world` and carries
`toggleable: true` whether or not the renderer later gives it its own `#const`. The switch is a
**rendering decision over an existing contract**, so no stored module is invalidated by building it
later.

⛔ **What must not happen** is `STEP_stage4.md:452`'s claim being read as closing this. It says the
deterministic marked-and-toggleable check *"already exists in `schema.Licensed`"*. `Licensed`
enforces the **flag**, which is the marking, not the switchability. Deleting this entry on the
strength of that line would retire a check that was never built — and it would look like progress.

---

## Re-reviewing the five newly watched transcriptions — deferred 2026-08-07

**What is deferred.** `guard.py`'s watch list was widened to `paper_pipeline/phase_1/prompt/*.md`
and `paper_pipeline/phase_1/schema.py` (the files transcribed from the design). None of the five has
a review point, so the guard is ⛔ RED and says NEVER REVIEWED. Establishing the baseline means
actually reading each against `resources/03_pipeline.md` with `model/REVIEW_BRIEF.md` — a real
review, not a rubber stamp.

**Why deferring it blocks nothing.** The guard is *supposed* to be red here: five files transcribed
from a design nobody re-checked is the true state, and recording it as green would be the exact
failure the guard exists to prevent. Red costs a `--no-verify` on an unrelated commit; a fabricated
baseline costs the next two-hour stale-design run.

⚠️ **The one thing that must not happen** is `guard.py --accept --all` to clear the noise. That is
why `--accept` refuses to run with no arguments and prints the files one per line: accepting is
per-file, and the record names who did it and when.

**What clears it.** A clean reviewer per file (they are small: 49–175 lines for the prompts, 874 for
`schema.py`), then `--accept <path>` for each one they actually read. `30_failure_modes.md` first —
it is the shortest and the one whose drift is most likely to have already caused a stage-1 defect.
