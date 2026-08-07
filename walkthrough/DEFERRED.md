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

**Revisit when:** a behaviour query returns a set, and licences exist.
