⚠️ **HARD LIMIT: under 400 words.** No preamble, no restatement of these instructions, no closing summary, no tables. One short line per item. If you are running long, shorten the reasons, never drop an item.

# Stage 2 of 4 — THE DEONTIC LAYER ONLY.

Using only your own stage-1 answers and the span, settle the normative layer. Nothing else in
this stage: no `concepts`, no `ontology`, no `requires`, no `inputs`, no licences, no JSON.

The fixed vocabulary: `asserts(ClauseId, Status, Act)`, `beats(Sayer, Winner, Loser)`,
`defines(ClauseId, Kind, Term)`. `Status` is exactly one of `forbid` · `permit` · `oblige` ·
`prefer`.

Write a numbered line per stage-1 item, in this shape:

    status: <one of the four>
    act:    <a term with its variable, e.g. hedge_answer(R)> — an ACT, not a thing
    body:   <the conditions, as named predicates with variables — or NONE>
    read_back: <the sentence a reader sees INSTEAD of the formal item, in the clause's voice>

Then answer these four questions about what you just wrote. Answer them; do not restate them.

**Q1. Where does each condition come from?** For every variable in a `body`, say which other
atom in that same body binds it. A variable appearing exactly once in a rule binds nothing.

**Q2. If stage 1 said the items are ALTERNATIVES, look at your bodies.** Do two or more of your
lines carry the same `status` on the same `body`? If so, an agent that did one of them violates
the others. Say whether that is what the span means. If it is not, say what you are changing.

**Q3. If stage 1 question 4 applied, look at your act names.** `Status` has four values and none
of them is negative — there is no `discourage`. So `prefer X` says X is the GOOD one. Read your
line back literally: does it say the span's thing-to-avoid is preferred? If so, say which of the
two phrasings from stage-1 question 4 you are putting in `act`.

**Q4. Your `read_back` and your `status` are read by different people.** Read each pair
literally, together. Do they say the same thing?

**Q5. CLOSURE.** For every distinct functor you used in `act`, say what the document's SILENCE
about that act means for this clause: `cepa` (silence permits), `cnpa` (silence prohibits), or
`unclear` (this clause does not settle it) — with a one-sentence reason from the span. An act on
a branch the span deliberately declined to speak about is not `cepa`.

Prose and the numbered lines. No JSON yet.
