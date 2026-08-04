# Patient-chain worksheet seat — author brief

You judge, for every row of a worksheet of atom instances, whether the
CLAUSE TEXT licenses a principal chain that the annotation left off — and
which chain. This is a frontier/careful seat: chain licensing is a judgment
about who a clause names acting on whom, and it takes at least the
annotation author's competence to catch the annotation author's omissions.

## What you see, and all you see

Each worksheet row carries: the clause id, the full clause text, the atom
name (chain-free), its gloss, its quote span, its polarity and stem, and a
mechanical reading. Judge from the row alone. You may additionally consult
`grammar.py` and `annotate_prompt.md` — the notation's owners — and nothing
else: no other repo file, no tool output, no ranking of any kind. If a
question cannot be answered from the clause text and the notation, the
answer is `unclear`.

## The question, per row

Does the clause text name both an actor and a party this act falls on (or
an actor other than the assistant)? Three answers:

- `chain_licensed` — the text names the parties; you write the chain it
  licenses.
- `no_chain_licensed` — the text names no such party; the atom correctly
  stays chain-free.
- `unclear` — genuinely undecidable from the text. Legal, and lands
  nothing; never force a call.

## The rules (verbatim from the artifacts that own them; procedure may be
## added around these, never loosening them)

1. THE CONVENTION (the golden-translation standard, binding on every
   entry): "A chain is written ONLY where the clause names both an actor
   and a party the act falls on (or an actor other than the assistant)."
2. ORDER IS MEANING (`annotate_prompt.md`): the parties come after a double
   underscore, IN ORDER: "who acts first, then who is acted upon, then any
   further party." `__model_user` and `__user_model` are different atoms
   and must not be swapped. A chain you add to an assistant-act atom is
   `__model_<patient>`, never `__<patient>` alone — a sole-member chain
   reads as "this party is the party concerned" and cannot state who acts
   on whom. The validator refuses every length-1 addition outright.
3. NEVER INFER (`annotate_prompt.md`, verbatim): "Write a party ONLY where
   the clause names one. Do not infer an affected party from the subject
   matter: a clause forbidding an act does not thereby name whoever that
   act would harm." Worked example, from the reference standard's recorded
   correction on m0236: the clause forbids creating content that praises
   extremist agendas, but names NO party the act falls on — so a
   `__model_third_party` chain had to be REMOVED. Contrast m0223 ("helpful
   to users" — the user is named) and m0242 ("targeting protected groups"
   — the target is named), where chains stand.
4. NO BARE ASSISTANT CHAIN (`annotate_prompt.md`): "Do NOT write a chain
   whose only party is the assistant itself." "A chain earns its place only
   when it names a PATIENT the act falls upon or an actor other than the
   assistant."
5. NO CAPACITY-PACKING (`annotate_prompt.md`): "do not pack a chain with
   parties the clause mentions in other capacities (who selected a setting,
   who benefits): slot two is who the act is done TO."
6. DECORATION ONLY. You may not touch stems, polarity, kinds, glosses,
   spans, or which atoms a clause carries. Anything you believe wrong
   OUTSIDE the chain goes in the record's optional `flag` field as a note
   for a later pass — never an edit here.

## Required output

One JSON file, at the path your assignment names, of the shape:

    {"worksheet_sha256": "<echoed verbatim from your assignment>",
     "records": [
       {"clause_id": "...", "name": "...",
        "verdict": "chain_licensed" | "no_chain_licensed" | "unclear",
        "corrected_chain": ["model", "user"] | null,
        "license_quote": "<EXACT clause-text substring naming actor AND
                          the party acted on>" | null,
        "reason": "<at most 25 words>",
        "flag": "<optional note on anything outside the chain>"},
       ...]}

- Every worksheet row exactly once; work the worksheet in its emitted
  order (polarity-marked rows come first).
- `corrected_chain`: only for `chain_licensed`; the FULL agent-first list,
  length at least two, members drawn from: third_party, developer,
  operator, system, model, root, user. Null otherwise.
- `license_quote`: only for `chain_licensed`; an exact, verbatim substring
  of that row's clause text naming both parties. It is checked
  mechanically; a chain that cannot quote its license does not land. Null
  otherwise.
- The echoed `worksheet_sha256` binds your records to exactly the
  worksheet you judged.

## Self-check before delivering

Run the validator command your assignment names. It must print CLEAN. It
enforces: coverage exactly once, the closed verdict vocabulary, the
length-2 floor, principal membership and parse round-trip of every
corrected chain (your chain is always re-attached to the ORIGINAL stem and
polarity — nothing else can move), the license-quote substring check, and
the reason length. A validator failure is yours to fix by re-judging, not
by loosening.
