# Affected-party attribution seat — author brief

You judge, for every row of a worksheet of atom instances, WHICH PARTY the
clause names as the one a harm, risk, protection, or benefit falls on — from
a closed vocabulary, with a verbatim quote from the clause text that licenses
your answer. This is a read-off, not a discovery: you are not asked what a
clause implies, only what its text names.

The field you fill is `affected_parties`. (Earlier drafts of the surrounding
documents called this same field `harm_bearers`; it is one field, renamed —
the question was never harm-only. A clause that provides a BENEFIT to someone
has an affected party exactly as a clause that describes a harm does.)

## What you see, and all you see

Each worksheet row carries: `clause_id`, `span_id`, the atom `name` (its
chain-free stem plus any existing chain, shown as-is), its `kind`, its
`gloss`, the atom's `quote` span, the FULL clause text, and — for atoms that
carry a chain — a mechanical reading of that chain, agent first. Judge from
the row alone. You may additionally consult `grammar.py` and
`annotate_prompt.md` — the notation's owners — and NOTHING ELSE: no other
repo file, no other design or handoff document, no tool output, no ranking of
any kind. For this pass you are EXEMPT from the repository's standard
context-loading order; do not read it. If a question cannot be answered from
the clause text and the notation, the answer is `unclear`.

Every row is judged on its own clause text. Never borrow an answer from a
sibling atom, from another row, or from the same atom name as it appeared in
some other clause: the same name genuinely carries different affected parties
in different clauses.

## The question, per row

Who does this atom's harm, risk, protection, or benefit fall on, as named by
this row's clause text?

- A RESOLVED verdict names one or more parties from the closed vocabulary
  below, and carries a verbatim `license_quote`.
- `unclear` — genuinely undecidable from the text, or no party is named at
  all. Legal, first-class, and lands nothing. **Never force a call.**

## The fixed decision procedure (ordered; may not be reordered or skipped)

Run these steps in this order, on every row.

1. **Does this atom describe a harm, risk, protection, or benefit?** Read the
   atom's name with its gloss. If it does not describe a harm, risk,
   protection, or benefit falling on any party — a model knowledge-state, a
   formatting rule, a statement about answer quality — answer `unclear`.
   Never invent a party to fill a row.
2. **Find the noun phrase(s) in the CLAUSE TEXT that this thing falls on.**
   Read the clause text, with the gloss as a reading aid. The party you want
   is the one the harm LANDS ON or the protection/benefit RUNS TO — NOT
   necessarily the grammatical recipient of any act, and NOT necessarily the
   party recorded in the atom's chain. The two come apart often, and the
   chain is not evidence about this question.
   * **NEVER INFER** (verbatim, from the rule that owns it): "Write a party
     ONLY where the clause names one. Do not infer an affected party from the
     subject matter: a clause forbidding an act does not thereby name whoever
     that act would harm." Worked precedent: a clause forbidding content that
     praises extremist agendas names NO party the act falls on — a
     `third_party` attribution there is an inference, not a reading, and does
     not land.
   * **NO CAPACITY MISATTRIBUTION.** Parties the clause mentions in OTHER
     capacities — who acts, who selected a setting, who is merely addressed,
     who is offered as a resource — are not affected parties unless the harm,
     protection, or benefit itself falls on them.
3. **Map each such noun phrase to the closed vocabulary** using the pinned
   table below. If a phrase maps to nothing in the table and is not a
   recognizable person-class noun, do NOT stretch the vocabulary: answer
   `unclear` and put the phrase in `flag` for a later ruling.
4. **Generic-noun referent disambiguation.** If a party phrase found in
   step 2 is a GENERIC-person noun ("people", "everyone", "anyone",
   "individuals", "all of humanity"), decide which REFERENT that noun carries
   IN THIS CLAUSE. Generic nouns carry more than one meaning; the decision is
   made once, per occurrence, from this clause's text and gloss. There is no
   default for generic nouns as a class.
   * **COMPREHENSIVE** — the noun is the BENEFICIARY CLASS of a universal
     provision: the clause's benefit or protection runs to people at large,
     whichever parties happen to be in view. Record
     `generic: "comprehensive"` and set `affected_parties` to the FULL
     principal set — all seven values of the vocabulary. The step-3 table
     mapping is OVERRIDDEN for this occurrence: the referent is the whole
     principal set, not a single principal.
   * **SPECIFIC** — the noun names the TARGETS of the harm, or the named
     object of a protection: a specific party that happens to be named by a
     generic noun. Record `generic: "specific"` and map the noun per the
     step-3 table, exactly as for a non-generic party.
   If the clause text and gloss do not decide comprehensive-vs-specific,
   answer `unclear`. Never guess a referent. Non-generic parties carry
   `generic: false`.
5. **If nothing in the clause text names a party** — the harm or benefit is
   described but no party is named — answer `unclear`, quote null. This is a
   correct and complete answer, not a failure.
6. **Multiple parties.** List every party the clause text names as affected
   (a clause protecting "users and developers" ⇒ `["user", "developer"]`).
   It is a SET: order does not matter, and a noun phrase plus its paraphrase
   is one party, not two.
7. **Write the record.** Echo `worksheet_sha256` verbatim; keep `reason` to
   at most 25 words.

## The pinned noun-phrase → principal mapping table

Case-insensitive. The table is part of this brief and frozen with it.
Additions require a ruling recorded outside this seat, never seat-side
improvisation.

| noun phrase (examples) | principal |
|---|---|
| "another person", "someone", "somebody", "other people", "others", "third party/parties", "people", "persons", "individuals", "humanity", "humankind", "human(s)", "society", "victim(s)", "minor(s)", "children/child", "teen(s)/teenager(s)", "protected group(s)", "the public", "bystander(s)", "communit(y/ies)", "everyone", "anyone" | `third_party` |
| "the user", "user(s)", "user's", "end user(s)" | `user` |
| "developer(s)", "developer's" | `developer` |
| "operator(s)" | `operator` |
| "system" (only where the clause means the serving surface/system-level instructions as the party harmed/protected) | `system` |
| "the model", "model(s)" (as the party a protection runs to, e.g. protections of the model itself) | `model` |
| "root" (the top authority; the spec's renamed Platform) | `root` |

Notes: (i) "teens" maps `third_party` by default; where the clause
contextually identifies them as the conversation's user, the seat maps `user`
and says so in `reason`. (ii) Second-person address ("you/your") is NOT in the
table: its referent (developer vs user) is a contextual judgment, so rows
whose only party-phrase is second-person are legitimate `unclear` candidates
unless the clause disambiguates. (iii) Organization names ("OpenAI") and role
nouns ("a public official", "the group") are absent from the table by design —
they are seat judgments, and they count only where you license them with a
verbatim quote; put the phrase in `flag`. (iv) Generic-person nouns in the
table ("people", "individuals", "everyone", "anyone", …) map per the table
ONLY when step 4 disambiguates them SPECIFIC; a COMPREHENSIVE disambiguation
overrides the table and records the full principal set. (v) SPEAKER-AWARE
FIRST-PERSON RULE: a FIRST-PERSON pronoun — "I", "me", "my" — counts as a
party phrase for steps 2–3 and maps by its SPEAKER TURN in example-dialogue
clause text: inside a `<user>` speaker turn it maps to `user`; inside an
`<assistant>` speaker turn it maps to `model`. The rule is MINIMAL:
first-person pronouns only — it does NOT generalize to any other
speaker-relative reference (second person stays governed by note (ii);
nothing is inferred from speaker role to any other party). A first-person
pronoun refers to its speaker by definition — there is no reading of "I"
inside the user's turn on which it denotes anyone but the user — so this
mapping cannot misattribute, and a first-person passage is a licensable
verbatim quote.

## Worked example 1 — a pure BENEFIT clause (m0018)

Clause text: *"People should have easy access to trustworthy safety-critical
information from our models."*

There is no harm anywhere in this clause. Step 1 is still YES: it describes a
BENEFIT — access to trustworthy information — falling on a party. A seat that
reads step 1 as "is there a harm here?" answers `unclear` and is wrong: the
question is harm, risk, protection, **or benefit**.

Step 2 finds the party phrase "People". Step 3 would map it `third_party` by
the table. Step 4 fires, because "people" is a generic-person noun, and asks
which referent it carries here: the clause states a universal provision, and
"People" is the BENEFICIARY CLASS of that provision — the access runs to
people at large, not to some particular set of persons distinguished from
others in the clause. That is a COMPREHENSIVE referent, so the table mapping
is overridden and the record carries the FULL principal set.

    {"clause_id": "m0018", "span_id": "<as given on the row>",
     "name": "<as given on the row>",
     "affected_parties": ["third_party", "developer", "operator", "system",
                          "model", "root", "user"],
     "generic": "comprehensive",
     "license_quote": "People should have easy access to trustworthy safety-critical information",
     "reason": "Universal provision; 'People' is the beneficiary class, not a particular party.",
     "flag": ""}

Contrast, same shape of noun, different referent: *"The assistant should not
engage in gratuitous abuse, harassment, or negativity toward individuals…"*.
Here "individuals" names the TARGETS of the harm — a specific party wearing a
generic noun — so step 4 answers SPECIFIC, the table applies, and the record
is `affected_parties: ["third_party"]`, `generic: "specific"`, quoting the
"…toward individuals" span. The same word can go either way; decide it from
the clause in front of you, every time.

## Worked example 2 — a party named in the text is not automatically the party (m0276)

Clause text (a self-harm passage) contains, among other things, the line that
**"there are people and resources who care"**. The row's atom is
`imminent_bodily_harm`, glossed *"the user faces an immediate risk of serious
physical injury or death"*.

A scan of the clause text hits "people" and would map `third_party`. That is
the trap. Step 2 asks who THIS ATOM's risk falls on, and the gloss says it
falls on the user — the "people who care" appear in another capacity
entirely: they are offered to the user as a resource, and nothing happens to
them. Step 2's NO CAPACITY MISATTRIBUTION rule disposes of them. The correct
answer maps the clause text's own verbatim "the user" span:

    {"clause_id": "m0276", "span_id": "<as given on the row>",
     "name": "imminent_bodily_harm",
     "affected_parties": ["user"],
     "generic": false,
     "license_quote": "the user",
     "reason": "Risk of injury falls on the user; the 'people who care' are a resource, not the party at risk.",
     "flag": ""}

Copy the `license_quote` byte-for-byte out of YOUR row's clause text — the
span above is illustrative, and a quote that has to be adjusted to fit is not
verbatim.

## `unclear` is a first-class verdict

`unclear` is a legal answer, not a failure to answer. Use it whenever step 1,
3, 4, or 5 sends you there: an atom that describes no harm/protection/benefit,
a party phrase outside the vocabulary, a generic noun whose referent the
clause does not decide, or a clause that names no party at all. An `unclear`
record with a clear `reason` (and a `flag` where a phrase needs a later
ruling) is worth more than a guess. **Never force a call.**

Never write a party you cannot quote. A party that cannot quote its license
does not land.

## Required output

One JSON file, at the path your assignment names, of the shape:

    {"worksheet_sha256": "<echoed verbatim from your assignment>",
     "records": [
       {"clause_id": "...", "span_id": "...", "name": "...",
        "affected_parties": [<principal>...] | ["unclear"],
        "generic": "comprehensive" | "specific" | false,
        "license_quote": "<EXACT clause-text substring naming the
                          affected part(y/ies)>" | null,
        "reason": "<at most 25 words>",
        "flag": "<optional note>"},
       ...]}

- Every worksheet row exactly once, in the worksheet's emitted order.
- The key is the 3-tuple `(clause_id, span_id, name)`, copied from the row.
- `affected_parties`: members drawn ONLY from `third_party`, `developer`,
  `operator`, `system`, `model`, `root`, `user` — plus the single sentinel
  verdict `["unclear"]`. Nothing else is expressible; free text is not a
  legal answer. Never empty.
- `generic`: `"comprehensive"` only with the FULL seven-value set;
  `"specific"` only with a resolved verdict naming a proper subset; `false`
  otherwise. A generic verdict never accompanies `unclear`.
- `license_quote`: REQUIRED for every resolved verdict — an exact, verbatim
  substring of THAT row's clause text naming the affected part(y/ies),
  checked byte-for-byte. `unclear` ⇒ `license_quote` must be null.
- `reason`: at most 25 words. `flag`: optional; use it for a phrase that
  needs a ruling, or anything you believe wrong outside this field — never
  as a place to record a party you could not quote.
- The echoed `worksheet_sha256` binds your records to exactly the worksheet
  you judged.

## Self-check before delivering

Run the validator command your assignment names. It must print CLEAN. It
enforces, mechanically: coverage (every row exactly once, in emitted order);
key resolution of `(clause_id, span_id, name)`; the closed vocabulary;
the byte-exact `license_quote` substring check, and quote-null for `unclear`;
the closed shapes (`generic`'s three values, the 25-word `reason`, the echoed
`worksheet_sha256`, no extra fields); and verdict/field coherence
(`unclear` ⇔ sentinel ⇔ null quote; `"comprehensive"` ⇔ the full seven-value
set; `"specific"` ⇒ a resolved proper subset).

Each error names the record, the field, and the defect, so correct THAT
record and resubmit. You get at most three attempts per record (initial
submission plus two corrections); a record still failing after that is
dropped and logged for review of this brief — so spend the corrections on
re-judging. **A validator failure is yours to fix by re-judging, not by
loosening.**
