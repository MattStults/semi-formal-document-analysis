# M6 — `read_back_slots` read as "this rule's variables"

**Mechanism, one sentence.** `read_back_slots` sits beside `act` and `body`, which *are*
lists of a rule's variables, so the model fills it with the rule's variables rather than
with the arguments of the `%` markers actually present in the sentence.

**5 repair rounds, $0.0085 (4% of repair spend), 4 clauses, 0 modules lost.**

---

## How to recognise it

```
asserts[0]: read_back has 2 `%` slot(s) but 1 slot entr(ies) — the rendered sentence
  would silently be wrong. Make the counts match: add one `%` in the sentence per slot
  entry (in order), or remove the extra entries; a sentence with no substitution takes []
  and no `%`. (`%` is reserved for substitution — for a percentage, say 'per cent')
```

**Note the direction, because it is nearly the reverse of the earlier census's.**

| shape | findings here | clauses | fixable by Fix A1? |
|---|---|---|---|
| `2 % slots but 1 slot entr(ies)` — more `%` than entries | **5** | `n003`, `n024`, `n025` ×3 | **no** — pinned refusal, `test_more_percent_than_slots_is_NOT_autofixed` |
| `0 % slots but 1 slot entr(ies)` — the census's dominant shape | 2 | `n060` (both its rounds) | yes |

`TRANSLATION_REPAIR_CENSUS.md` §5.2 measured **61 of 65** findings as the second shape.
Here it is 2 of 7. **Fix A1 would have killed at most 1 of this run's 5 rounds** (`n060`
attempt 1; its attempt-2 round would still have been paid, since the finding repeated).

---

## The clauses

| clause | attempts | rounds | outcome |
|---|---|---|---|
| `l1_170_n060` | 3 | 2 | translated |
| `l1_170_n003` | 3 | 1 | translated |
| `l1_170_n024` | 2 | 1 | translated |
| `l1_170_n025` | 2 | 1 | translated |

## Verbatim excerpts

**`l1_170_n025` — 3 findings on one round.** Verbatim (L40):

> `People should have transparency into the important rules and reasons behind our models'
> behavior. We provide transparency primarily through this Model Spec, while committing to
> further transparency when we further adapt model behavior in significant ways (e.g., via
> system messages or due to local laws), especially when it could implicate people's
> fundamental human rights.`

**`l1_170_n060` — the only 2-round member.** Verbatim (L101):

> `For example, if a user asks the model to speak like a realistic pirate, this implicitly
> overrides the guideline to avoid swearing.`

**`l1_170_n024`.** Verbatim (L39):

> `People should have easy access to trustworthy safety-critical information from our
> models.`

---

## Recovery

All four recovered; three in one round. This is the least harmful class in the run: it
never killed a module and never persisted past two rounds.

## The paid cost of the class

| | |
|---|---|
| repair rounds | **5 of 130 (4%)** |
| findings | 7 |
| clauses touched | 4 |
| **attributed spend** | **$0.0085** |
| **modules lost** | **0** |

---

## FALSIFIER

*This run's direction reversal is real and not a small-sample artefact.* Wrong if, over
the full corpus, the zero-`%`-non-empty-slots shape returns to dominance. n=7 here; the
census had n=65. **The honest statement is that this class is too small in this slice to
carry any conclusion**, and the only thing worth recording is the direction, because it
determines whether the one shipped, tested fix applies at all.

---

## Candidate solutions already on record

* **Fix A1 (`readback-empty-slots`)** — implemented, 34 tests, replayed 61 firings on the
  stored corpus. Reviewed **NEEDS WORK** (`TRANSLATION_CENSUS_REVIEW.md` A-1): it *"decides
  a question the model left open"* — a no-`%` sentence with slots has two repairs (drop the
  slots, or add the `%`) and A1 always picks the first, while the rule immediately below
  refuses the mirror case for exactly that reason. Concretely, *"affirming an ungrounded
  belief that might lead to distress is forbidden"* with `slots: ["B"]` reads as a
  universal after the fix. Recommendation on record: keep the rule, record the dropped
  slot list on the `Fix` record and surface it in the run artifact; do not describe it as
  lossless.
* **Defect fatal to the diff, not the idea** — but note this run's finding: **A1 reaches
  only 2 of the 7 findings and at most 1 of the 5 rounds here.** Its credited 17-of-18
  gen-11 readback rounds come from the earlier population, whose direction distribution
  does not hold in this corpus region.
* **Fix A1′ (delete `read_back_slots`, name substitutions inline in braces)** is the
  durable version and is the only candidate that addresses *this* run's direction too,
  because it removes the count entirely. It is explicitly deferred to ride with Fix D.

---

## Graph-stage or translation-stage?

**Translation-stage, unambiguously.** A field name and its neighbours cause it; the graph
has no bearing on it whatever. It is also the cleanest example in the whole post-mortem of
the campaign's standing lesson — *"Prose cannot beat a field name"* — the rule is stated
correctly three times (in `10_output_format.md` twice and in `schema.ReadBack`'s own field
text) and still fires.

---

## Open question for the fix pass

A1′ replaces `%` with inline `{Var}` braces and touches `render`, `%!trace_rule`
interpolation and `readback.py` together. **Does anything downstream parse the `%` form
positionally** — in particular `readback_r3.py` and the seat-facing sentences in
`seats.py` — such that A1′ needs a migration for stored modules the way Fix D does? The
review costed D's migration and nobody has costed A1′'s.
