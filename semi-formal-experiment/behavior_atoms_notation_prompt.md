<!-- The rung-1.5 QUERY notation, appended to `behavior_atoms_prompt.md` when
     `--notation` is passed. Kept in its own file so the unnotated prompt stays
     byte-identical and so this block is diffable on its own.

     Split on the two marker lines, like every other template here.
     Placeholders:
       {{POLARITIES}}       the reserved polarity values, from grammar.py
       {{PRINCIPALS}}       the closed principal list, from grammar.py
       {{MAX_PRINCIPALS}}   the declared chain-length ceiling

     ⚠️ EVERY DEMONSTRATION BELOW IS SYNTHETIC. Invariant 9 bars examples of the
     panel's behaviour->passage judgements; it does not bar showing the model
     the FORMAT. But a demonstration lifted from either specification would be a
     channel from someone who has read the panel, so demonstrations here are
     written to exercise the notation and are asserted not to be substrings of
     the spec (`test_behavior_atoms_notation.py`). A demonstration sourced from
     the spec is a blocking review finding. -->

=== SYSTEM ===

===== DEONTIC FORCE AND THE PARTIES (two extra fields on `act` atoms) =====
The vocabulary above is UNPOLARISED: it names acts, not who owes them to whom.
Your selection is still a selection — you still copy the name off the list —
but for each `act` atom you also choose, from two CLOSED lists, what force the
behaviour attaches to that act and which parties it holds between. You never
write the decorated name yourself; it is assembled from your choices and
rejected if it does not assemble.

POLARITY. One of: {{POLARITIES}}, or null. Choose it from the BEHAVIOUR'S OWN
definition, not from the document:
  * must / mustnot — the behaviour requires the act, or requires its absence
  * should / shouldnot — the behaviour prefers it, or prefers against it
  * may — the behaviour merely permits it; the model is not committed either way
  * null — the behaviour takes no deontic stance on this act; it is context
Use `mustnot`, not `must`, for the acts the behaviour exists to prevent. An act
the behaviour forbids is as much a part of the query as one it requires — but
they are not the same atom, and writing them as the same atom is the defect
this field removes.

PRINCIPALS. An ORDERED list, up to {{MAX_PRINCIPALS}} long, drawn only from:
  {{PRINCIPALS}}
ORDER IS THE MEANING. The first entry is WHO ACTS; the rest are who is ACTED
UPON, in order. `["model", "third_party"]` is the model doing something to a
third party. `["third_party", "model"]` is a third party doing something to the
model. These are different atoms and a behaviour about harm to third parties
wants the FIRST one. Do not sort the list, do not put the party you care about
first out of emphasis, and do not repeat a party.
Leave the list empty when the act genuinely holds between no particular
parties. An empty list constrains nothing, which is the honest answer; a guessed
chain silently excludes clauses.

WHERE THE FIELDS APPLY. `act` atoms only. Situations, entities and values take
neither field: a value has no deontic force and no parties, and marking one is
a category error that will be discarded and counted.

THE OBJECT SHAPE, EXTENDED. Two optional fields, nothing else changes:

  selected: {"name": str, "kind": str, "weight": 1|2|3, "source": str,
             "polarity": str|null, "principals": [str, ...]}

FORMAT DEMONSTRATIONS. These are shape, not content — the atoms are invented
and none of them is in the vocabulary above:

  {"name": "wibble_the_frobnitz", "kind": "act", "weight": 3,
   "source": "definition", "polarity": "mustnot",
   "principals": ["model", "third_party"]}
      the model must not wibble the frobnitz of a third party

  {"name": "quux_a_widget", "kind": "act", "weight": 2,
   "source": "definition", "polarity": "may", "principals": ["operator"]}
      the operator is permitted to quux a widget

  {"name": "zorble_state", "kind": "situation", "weight": 1,
   "source": "definition"}
      a situation atom: no polarity, no principals, unchanged from before

=== USER ===

===== POLARITY AND PRINCIPALS =====
For every `act` you select, add "polarity" (one of {{POLARITIES}}, or null) and
"principals" (an ORDERED list of at most {{MAX_PRINCIPALS}} of:
{{PRINCIPALS}}), first entry = who acts. Copy the `name` from the vocabulary
exactly as before and do NOT write the prefix or the chain into it yourself.
Non-`act` atoms take neither field.
