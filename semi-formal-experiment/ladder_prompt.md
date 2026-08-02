<!-- Rung blocks for ladder.py. One block per rung, split on the marker lines.

     Each block is APPENDED to the system prompt of annotate_prompt.md. It
     never replaces it: rung 1 must differ from the shipped annotation pass
     only by (a) one passage per request and (b) the whole vocabulary carried
     with no eviction, so everything else has to stay byte-identical.

     DEMONSTRATIONS. Rungs 1.5 and above SHOW the grammar rather than only
     describing it. Every demonstration passage is written for this file, is
     about a fictional community garden, and is NOT a passage of the Model
     Spec or of the constitution. That is a hard rule, not a preference: a
     demonstration lifted from either spec would be a hand-curated annotation
     of an evaluation-set passage chosen by someone who has seen the panel,
     which is a leak channel. Every demonstration passage is marked with a
     leading `DEMO> ` so `ladder.demonstration_passages` can extract it and
     `ladder.assert_demonstrations_synthetic` can refuse to build a prompt if
     any of them turns up inside either spec.

     The demonstrations deliberately use INVENTED atom stems. They teach the
     grammar, not a vocabulary; at rungs 1 and 1.5 the stem must still come
     from the closed list of atoms already defined.

     THE FREEZE. The substring check is a backstop against the syntactic
     case. The leak that actually matters is SELECTION — which grammar
     features get demonstrated, on what content, by an author who has read
     panel-conditioned analysis — and no test can detect that after the fact.
     The mitigation is a pre-commitment: the three demonstration passages
     below were written and frozen before any of the ladder's results
     existed, and their sha256 is recorded here. `ladder.py` refuses to build
     a prompt if the two disagree, so a demonstration cannot be quietly
     re-chosen once results start arriving. Changing them is allowed and is
     meant to be loud: update the hash in the same commit, and say why.

     The hash is taken over the DEMO> lines only, whitespace-collapsed and
     lower-cased, joined with newlines:
         .venv/bin/python -c "import ladder; print(ladder.demonstrations_sha256())"

DEMONSTRATIONS-SHA256: 84206edee5728c715222edcc4e24d53317167bb12d43258e2b5dc71034b18b60
-->

=== RUNG 1 ===

THIS REQUEST COVERS EXACTLY ONE PASSAGE. Give it your whole attention. There
is no competition for room with other passages and no reason to be brief for
brevity's sake.

THE VOCABULARY IS CLOSED. Every name you emit must be one of the atoms listed
under "ATOMS ALREADY DEFINED", spelled exactly as it appears there. You may
NOT coin a new name in this request. The list is the complete vocabulary of the
index; nothing has been evicted from it. If no listed atom fits some part of
the passage, leave that part unrecorded and emit fewer atoms — that omission is
information we want, and inventing a name to cover it destroys it.

You do not need to write a gloss: the index already holds one for every listed
atom and yours would be discarded. Emit the `gloss` field as an empty string.

RATE CAP. Three atoms is the budget for a passage. Five is the hard ceiling and
anything past it is dropped before anyone reads your answer. The budget is an
AVERAGE over the whole run: a fourth atom here is paid for by a passage that
needs only two, so spend a fourth only where it earns its place.

=== RUNG 1.5 ===

THIS REQUEST COVERS EXACTLY ONE PASSAGE. Give it your whole attention.

THE VOCABULARY IS CLOSED, exactly as in the previous instruction: every atom
STEM must be one of the atoms listed under "ATOMS ALREADY DEFINED", spelled
exactly. You may not coin a stem. Emit `gloss` as an empty string.

TWO THINGS THE NAME MUST NOW CARRY. The index has no fields for them, so they
are carried by a naming convention that is read back mechanically. Get the
convention exactly right or the atom is rejected.

  1. PRINCIPALS, ORDERED. Every atom of kind `act` names the principals the act
     runs between, appended to the stem after a DOUBLE UNDERSCORE, in order:
     the one who acts first, then the one acted upon, then any third party.

         <stem>__<actor>[_<patient>[_<third>]]

     Order is the content. `__model_user` and `__user_model` are different
     acts and must never be swapped. Use only these principal words:

         user  operator  developer  model  system  platform  third_party

     If the passage names only who acts, give only that one principal. An
     `act` atom with no `__` section is rejected.

  2. POLARITY, AS A RESERVED PREFIX. If the passage puts deontic force on the
     act, say which, with one of these prefixes on the FRONT of the name:

         must_       the passage requires it
         mustnot_    the passage forbids it
         should_     the passage says to prefer it, without requiring it
         shouldnot_  the passage says to avoid it, without forbidding it
         may_        the passage permits it

     These five prefixes are RESERVED. Use them for nothing else. If the
     passage states no deontic force, use no prefix — that is a real answer,
     not a missing one, and a guessed `must_` is worse than none.

  A full name is therefore:  [prefix_]stem__principals

DEMONSTRATIONS. Three passages, with the annotation each should get. They are
about a community garden and have nothing to do with the document you are
indexing; they are here to show the convention. Their stems are invented — in
your own answer the stem must come from the closed list.

DEMO> If a plot holder cannot tend their plot for more than three weeks, the plot holder must tell the garden steward before the third week ends.

  {"clauses": [{"clause_id": "demo1", "atoms": [
    {"name": "must_announce_absence__user_operator", "kind": "act",
     "gloss": "", "span_id": "s1"},
    {"name": "plot_left_untended", "kind": "situation",
     "gloss": "", "span_id": "s2"}]}]}

  The act is required, so `must_`. The one who acts is the plot holder and the
  one acted upon is the steward, in that order. The circumstance is a
  situation and carries no polarity and no principals.

DEMO> The garden steward never reassigns a plot to settle a dispute between two plot holders.

  {"clauses": [{"clause_id": "demo2", "atoms": [
    {"name": "mustnot_reassign_plot__operator_user_third_party", "kind": "act",
     "gloss": "", "span_id": "s1"},
    {"name": "dispute_between_holders", "kind": "situation",
     "gloss": "", "span_id": "s1"}]}]}

  Forbidden, so `mustnot_`. Three principals: the steward acts, the plot
  holder is acted upon, and the other holder is the third party.

DEMO> Watering cans left by the gate are shared, and anyone may take one for the afternoon.

  {"clauses": [{"clause_id": "demo3", "atoms": [
    {"name": "may_borrow_shared_tool__user", "kind": "act",
     "gloss": "", "span_id": "s2"},
    {"name": "shared_tool", "kind": "entity", "gloss": "", "span_id": "s1"}]}]}

  Permitted, so `may_`. Only the actor is named, so only one principal. The
  tool is an entity: no prefix, no principals.

RATE CAP. Three atoms is the budget for a passage, five is the hard ceiling,
and the budget is an average over the whole run. Anything past the ceiling is
dropped before anyone reads your answer.

=== RUNG 2 ===

THIS REQUEST COVERS EXACTLY ONE PASSAGE. Give it your whole attention.

Keep everything from the previous instruction: ordered principals after a
double underscore on every `act`, and the five reserved polarity prefixes
`must_ mustnot_ should_ shouldnot_ may_` on the front of a name when the
passage puts deontic force on the act.

TWO THINGS ARE NOW RELAXED.

  1. YOU MAY COIN. The listed atoms are still the right first choice and reuse
     is still what makes the index work — read the list before you write a
     name. But where no listed atom denotes what this passage is about, coin a
     new stem rather than forcing a near-fit. A forced fit and an honest new
     name are both visible to us and we would rather see the new name.

  2. THE GLOSS IS PER-OCCURRENCE. Write what the atom means IN THIS PASSAGE,
     not a definition that has to serve every other passage as well. Say the
     thing the name cannot: which party, which condition, which exception.

RATE CAP. Three atoms and 211 characters of gloss is the budget for a passage.
Five atoms is the hard ceiling and anything past it is dropped. Both budgets
are AVERAGES over the whole run, enforced before anyone reads your answer: a
run that comes in over budget has its longest glosses truncated. Spend the
characters on what the names cannot carry.

DEMO> If a plot holder cannot tend their plot for more than three weeks, the plot holder must tell the garden steward before the third week ends.

  {"clauses": [{"clause_id": "demo1", "atoms": [
    {"name": "must_announce_absence__user_operator", "kind": "act",
     "gloss": "notice is owed before the third week, not after",
     "span_id": "s1"},
    {"name": "plot_left_untended", "kind": "situation",
     "gloss": "untended for more than three weeks; shorter gaps are fine",
     "span_id": "s2"}]}]}

  Both glosses carry the threshold and the deadline, which no name could.

=== RUNG 3 ===

THIS REQUEST COVERS EXACTLY ONE PASSAGE. Give it your whole attention.

NO CONVENTIONS ARE IMPOSED. Coin freely or reuse; name however you think best;
write whatever glosses you think best. Only two things are fixed:

  - the object shape, exactly as specified above: an atom is
    {"name", "kind", "gloss", "span_id"} and nothing else. Do not add fields.
  - the four kinds: situation, act, entity, value.

Within that, write the best representation of this passage you can. Assume your
reader sees the atoms and their glosses and NOTHING ELSE — not the passage, not
its title, not its neighbours — and has to know what the passage requires.

If you want to put structure into a NAME, two spellings are read back
mechanically and will be decoded for that reader rather than shown as raw
text: a leading `must_`, `mustnot_`, `should_`, `shouldnot_` or `may_` is read
as that deontic force, and a trailing double underscore followed by parties
(`__model_user`) is read as those parties in that order — who acts first, then
who is acted upon. Neither is required and neither is expected; they are
offered so that a name you would have written anyway is not read as an opaque
string. Any other scheme you invent will be shown to your reader verbatim.

RATE CAP. Three atoms and 211 characters of gloss is the budget for a passage;
five atoms is the hard ceiling; both budgets are averages over the whole run
and are enforced before anyone reads your answer. The cap is the point of the
exercise: we are asking what you can do at the budget the index actually runs
at, not what you could do with more room.

=== RUNG 4 ===

THIS REQUEST COVERS EXACTLY ONE PASSAGE. Give it your whole attention.

YOU MAY INVENT STRUCTURE. The object shape is no longer fixed. Beyond the four
required fields — "name", "kind", "gloss", "span_id" — you may add any fields
you like to an atom, and you may use them to record what the four-field shape
cannot: a relation between two atoms, a polarity, a deontic force, a condition,
an exception, a priority, an addressee. Invent the fields you need. Name them
whatever you like. The four kinds are still situation, act, entity, value, and
"span_id" must still be one of the span labels offered under this passage.

We are asking what you reach for, so reach. If the right representation of this
passage is one atom with a rich structure hanging off it, emit that. If it is
three flat atoms, emit that.

DEMO> If a plot holder cannot tend their plot for more than three weeks, the plot holder must tell the garden steward before the third week ends.

  {"clauses": [{"clause_id": "demo1", "atoms": [
    {"name": "announce_absence", "kind": "act", "span_id": "s1",
     "gloss": "telling the steward you will be away",
     "deontic": "required",
     "actor": "plot_holder", "addressee": "garden_steward",
     "condition": "plot_left_untended",
     "deadline": "before the end of the third week"},
    {"name": "plot_left_untended", "kind": "situation", "span_id": "s2",
     "gloss": "away more than three weeks",
     "triggers": "announce_absence"}]}]}

  That is ONE possible shape and not a template. The fields above were chosen
  for this passage; choose your own for yours.

RATE CAP, AND HOW IT COUNTS INVENTED FIELDS. Three atoms and 211 characters of
FREE TEXT is the budget for a passage; five atoms is the hard ceiling; both
budgets are averages over the whole run and are enforced before anyone reads
your answer. Free text means the gloss plus every string you write in a field
you invented — a relation recorded as prose is prose, and it is priced the same
as a gloss. Field NAMES are free; their string values are not. Structure is
what we are paying for here, not room.
