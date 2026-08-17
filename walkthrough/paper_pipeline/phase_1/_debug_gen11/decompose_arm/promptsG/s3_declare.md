⚠️ **HARD LIMIT: under 400 words.** No preamble, no restatement of these instructions, no closing summary, no tables. One short line per item. If you are running long, shorten the reasons, never drop an item.

# Stage 3 of 4 — THE ONTOLOGY AND DECLARATION LAYER ONLY.

Every predicate name you used in stage 2 now needs a home. Three fields, three different
meanings:

- **`ontology`** — a non-deontic classification *this clause itself establishes*. Either a
  ground atom, or an `atom` plus a `body` that binds its variables.
- **`requires`** — a predicate *another clause* must define. You use it; you do not define it.
- **`inputs`** — a predicate describing *the case being judged* — messages, roles, case data —
  supplied at query time.

`requires` and `inputs` are disjoint. Every name in either carries `/arity`.
Separately, **`concepts`** declares what a name MEANS — name, arity, gloss — for every predicate
you introduce and for every `requires` name. `concepts` asserts nothing.

Go through every name from stage 2 and place it. Then answer these. Answer them; do not restate
them.

**Q1. THE EXCLUSION TEST, for every `ontology` entry you give a `body`.** Name a thing of the
head variable's kind that your body EXCLUDES — a case where the body is false. If you cannot
name one, the body derives the head of every case, and the class you meant to define does not
exist in your module. When that happens you have two honest routes and you must pick one by
name: leave the name in `concepts` only, with no `ontology` entry, or put it in `inputs` as a
fact about the case. Say which you picked and why.

**Q2. TWO HEADS, ONE BODY.** If any two `ontology` entries share the same body, they have the
same extension — the distinction you drew is not in the module. Say whether you meant that.

**Q3. THE NEEDS NAMES, AND THE LICENCE ON A GLOSS YOU DID NOT WRITE.** Each `concepts` entry
carries a `licence`: `textual` (the cited clause says this — and requires `cites`), `assumed`
(an inference the document licenses but does not state — and requires `inference`, one
sentence), or `world` (outside the document — and requires `toggleable: true`).

For each NEEDS name, you said in stage 1 whether this node's narrowing establishes it. Now:
   (a) which licence are you putting on its `concepts` entry?
   (b) if `textual`, write out the clause id you are citing, and then write out the sentence in
       the narrowing that says it. The node's CITATION instruction permits exactly one id.
   (c) if you cannot complete (b), say so, and say which licence you are using instead.

**Q4. GLOSSES.** Read each gloss beside its name. A gloss that re-spaces the name — `pasted_text/1`
glossed "pasted text" — tells a reader nothing. For each, say what makes it true.

**Q5. EVERY BODY NAME HAS A SOURCE.** List every predicate appearing in any `body` from stage 2
or this stage, and beside it write `ontology`, `requires` or `inputs`. A name on none of the
three can never fire.

Prose and lists. No JSON yet.
