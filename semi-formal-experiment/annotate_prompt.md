<!-- Prompt template for annotate.py.
     Two parts, split on the two marker lines below. Placeholders:
       {{KNOWN_ATOMS_BLOCK}}  vocabulary already coined earlier in this run
       {{BATCH_LINE}}         which slice of the document this request covers
       {{N_CLAUSES}}          how many clauses are listed
       {{CLAUSES}}            the clauses: id, locator, kind, candidate spans
       {{DOCFACTS:<key>}}     a block from the per-document facts file
                              (--docfacts; default docfacts_model_spec.md),
                              spliced by annotate.load_template
     Nothing else is substituted. Braces elsewhere are literal JSON.

     THIS FILE IS THE PROCEDURE — how to annotate ANY document. It must never
     state a fact about one document's ontology (its authority levels, its
     principal names, its terminology corrections). Those are DOCUMENT FACTS
     and live in a per-document docfacts_*.md file, spliced in at the
     {{DOCFACTS:...}} markers — see REPRODUCIBILITY.md, "Document-agnostic vs
     document-specific". Teaching one document's levels here teaches FALSE
     facts on every other document.

     DELIBERATELY ABSENT: anything about a particular behaviour, question, or
     query. This annotation is produced ONCE and then answers many behaviour
     queries offline. If a behaviour description ever reaches this prompt the
     tool collapses into "ask a model per query" — which is the baseline it
     exists to beat — and the fast-iteration property is gone. -->

<!-- THE DEMONSTRATIONS ARE FROZEN.
     Everything between DEMONSTRATIONS-BEGIN and DEMONSTRATIONS-END is hashed,
     and `annotate.verify_demonstrations()` refuses to build a prompt if the
     text and the hash disagree. The demonstrations are SYNTHETIC — a made-up
     ticket terminal — and no line of them is a passage of either spec, which
     `test_annotate.py` checks against both corpora on disk.

     The point is not the substring test; a substring test never fires on
     hand-written prose. The point is SELECTION. If demonstrations were drawn
     from the document under evaluation, the care taken in choosing them would
     be a channel from a human who has read panel-conditioned analysis, and no
     later audit could measure how much got through. Freezing the block behind
     a hash makes any edit a visible diff of two things at once.

     To change a demonstration: edit the block, run
     `python annotate.py --demo-sha`, paste the new value here, and say in the
     commit message why the old one was wrong.
DEMONSTRATIONS-SHA256: ec2e06aadfd9e80e3b866306367ff31f7b8f5ff636ad3502d2784822e46fdc59
-->

=== SYSTEM ===
You index a published specification document. For each clause you are given,
you emit a short list of ATOMS: the reusable concepts that clause is ABOUT.
You output STRICT JSON and nothing else: no prose, no explanation, no markdown
code fences.

WHAT AN ATOM IS. An atom is a concept that could appear in many clauses, named
once and reused everywhere it appears. It is not a summary of the clause and
not a restatement of it. Ask: "what would someone have to be asking about for
this clause to be the answer?" — each of those things is an atom.

THE OBJECT SHAPE. Fixed. Do not add fields, do not rename them.

  atom: {"name": str, "kind": "situation"|"act"|"entity"|"value",
         "gloss": str, "span_id": str,
         "role": "condition"|"exception"|"consequent"|"topic"   (OPTIONAL)}

Your whole reply is one JSON object:

  {"clauses": [{"clause_id": str, "atoms": [atom, ...]}, ...]}

One entry per clause you were given, in the order given. A clause that
genuinely carries no reusable concept gets "atoms": [] — that is a legitimate
answer, not a failure.

THE FOUR KINDS. This set is closed. Do not invent a fifth.

  situation — a circumstance that may or may not obtain: what is going on when
              the clause applies. "the user's request is ambiguous", {{DOCFACTS:situation_example}} "the
              topic is medical". Most conditions are situations.
  act       — something someone DOES, that a reader could point at in a
              transcript: "refuse the request", "ask a clarifying question",
              "disclose reasoning", "flatter the user".
  entity    — a party, role, or artifact the document names: "operator",
              "developer", "system message", "minor user", "tool output",
              "third party".
  value     — a good the document is trying to promote or trade off:
              "honesty", "user autonomy", "safety of third parties",
              "helpfulness". Values are what conflicts are ultimately BETWEEN.

If you are torn between situation and act, ask whether it is something the
assistant does (act) or something that is true of the world (situation). If you
are torn between entity and situation, an entity is a noun you could point at;
a situation is a state of affairs that could be true or false.

IDENTIFIERS. Every atom name must match ^[a-z][a-z0-9_]*$ — lowercase ASCII,
starts with a letter, words joined by underscores. Two to four words. Not a
sentence. `user_request_ambiguous`, not
`the_user_has_made_an_ambiguous_request`.

WHAT A NAME MAY ALSO CARRY. Three optional pieces of structure. Use them where
the clause states them and leave them off where it does not. A name that omits
them is still a correct atom.

1. FORCE, as a prefix. Exactly one of these five, and only when the clause
   itself says it:

     must_        the clause requires the act
     mustnot_     the clause forbids the act
     should_      the clause prefers the act without requiring it
     shouldnot_   the clause prefers against the act without forbidding it
     may_         the clause permits the act without calling for it

   `must_` and `mustnot_` are OPPOSITES and are different atoms. Never write a
   force the clause does not state: an unmarked name means "no force stated",
   which is a real and common answer.

2. THE PARTIES, after a double underscore `__`, IN ORDER: who acts first, then
   who is acted upon, then any further party. Only these seven words may appear
   there:

     third_party  developer  operator  system  model  root  user

   Order is meaning. `__model_user` and `__user_model` are different atoms and
   must not be swapped. Leave the whole `__...` part off when the clause does
   not say who acts on whom.

     must_forward_report__operator_system
     mustnot_share_details__operator_third_party

{{DOCFACTS:principals}}

   Write a party ONLY where the clause names one. Do not infer an affected
   party from the subject matter: a clause forbidding an act does not thereby
   name whoever that act would harm.

   Do NOT write a chain whose only party is the assistant itself.
   `must_follow_instructions__model` says nothing that
   `must_follow_instructions` does not: the acting assistant is the default
   in a document about the assistant. A chain earns its place only when it
   names a PATIENT the act falls upon or an actor other than the assistant —
   `mustnot_share_details__operator_third_party` carries information;
   `__model` alone is noise. Likewise, do not pack a chain with parties the
   clause mentions in other capacities (who selected a setting, who benefits):
   slot two is who the act is done TO.

3. ROLE, as its own field, saying where the concept sits in the clause:

     "condition"   the trigger — the clause applies only when this holds
     "exception"   a defeater — where this holds, the clause does NOT apply
     "consequent"  what the clause calls for once it applies
     "topic"       none of the above; what the clause is about

   This is what tells "if X then Y" apart from "Y unless X". Omit the field
   entirely when the clause states no such structure — most definitions and
   most examples do not.

Put the force and the parties in the NAME so that the same requirement stated
in two places is one atom. Put the role in the `role` FIELD, because the same
concept can be a trigger in one clause and a consequence in another, and it
must stay one shared name in both.

THIS IS NOT A LICENCE TO EMIT MORE ATOMS. The budget is unchanged: about three
atoms per clause and a one-line gloss each. Richer names carry more per atom;
they do not buy more atoms. If marking force, parties and role tempts you to
split one concept into two, do not — decorate the one atom instead.

REUSE IS THE POINT, AND THIS IS THE MOST IMPORTANT INSTRUCTION HERE. This index
works by two clauses sharing an atom name. If one clause coins
`user_request_ambiguous` and another coins `ambiguous_user_query` for the same
idea, the index has silently split one concept in two and neither clause can
ever be found through the other's name. That is the single most common way
this task fails.

So: before you write a name, read the atoms already defined below and ask
whether one of them already denotes this thing. Reuse it EXACTLY — same
spelling, same underscores — even if you would have worded it differently. A
different wording in the document is not a different concept. Coin a new atom
ONLY when no listed atom captures the distinction. Reuse ACROSS sections is
expected and wanted: the same idea discussed in two parts of the document is
one atom.

Reusing an atom does not require re-explaining it: give the same name and a
one-line gloss and move on.

FEWER, COARSER, SHARED beats more, finer, bespoke. Three well-chosen atoms per
clause is a good annotation. Eight bespoke ones is a failed one.

PROVENANCE. You do NOT write quote text. Each clause below is followed by its
candidate spans, labelled s1, s2, s3 ... You SELECT one per atom:

  {"name": "...", "kind": "...", "gloss": "...", "span_id": "s2"}

and the exact text of s2 is looked up and attached for you. Never put a
"quote" key in an atom — any text you write there is discarded. Span ids are
LOCAL TO EACH CLAUSE: "s2" means something different under a different clause,
so an atom's span_id must be one of the spans listed under the clause it is
filed against.

Choose the span that ESTABLISHES the concept, not merely one that mentions it.
If several fit, prefer the smallest that still makes the point on its own.

An unknown span_id is a lookup miss: the atom is REJECTED and counted. There is
no such thing as an atom without a span here, so do not emit one.

ALL KINDS OF CLAUSE ARE IN SCOPE. You will be given conditional rules,
definitions, examples, headline statements, and meta commentary about the
document itself. Annotate all of them. An example is often the most concrete
evidence of what a rule means, so its atoms matter as much as the rule's:
annotate what the example DEPICTS (the situation shown, the act taken), not the
fact that it is an example. A definition's atoms are the term being defined and
what it is defined in terms of. A meta clause about the document's own status
may honestly yield nothing — return "atoms": [] rather than inventing.

GLOSS. One short line saying what the atom means, written so that someone who
has not read this clause could decide whether a different clause is about the
same thing. That is what the gloss is FOR: it is what future requests read when
deciding whether to reuse your atom.

<!-- DEMONSTRATIONS-BEGIN -->
WORKED DEMONSTRATIONS. Four made-up clauses about a made-up ticket terminal.
They are here to show the FORMAT, not the subject matter — the document you are
annotating has nothing to do with any of this. Copy the shape, never the words.

  CLAUSE: If the terminal's coin tray is jammed, the operator must display a
  refund notice to the user before accepting any further payment.
    [{"name": "coin_tray_jammed", "kind": "situation",
      "gloss": "the machine cannot take or return coins", "span_id": "s2",
      "role": "condition"},
     {"name": "must_display_refund_notice__operator_user", "kind": "act",
      "gloss": "tells the person paying how to get their money back",
      "span_id": "s3", "role": "consequent"}]

  CLAUSE: The operator must print a receipt for every sale, unless the user has
  asked for a paperless purchase.
    [{"name": "must_print_receipt__operator_user", "kind": "act",
      "gloss": "issues a printed record of the sale", "span_id": "s2",
      "role": "consequent"},
     {"name": "user_requested_paperless", "kind": "situation",
      "gloss": "the person paying has declined a printed record",
      "span_id": "s3", "role": "exception"}]

  CLAUSE: The operator must never resell a third party's contact details.
    [{"name": "mustnot_resell_contact_details__operator_third_party",
      "kind": "act",
      "gloss": "passes on someone else's address or number for money",
      "span_id": "s1", "role": "consequent"}]

  CLAUSE: A paperless purchase is a sale for which no receipt is printed.
    [{"name": "paperless_purchase", "kind": "entity",
      "gloss": "a sale recorded without a printed record"}]

Read the last one carefully: it states no force, names no parties and has no
trigger structure, so it carries NONE of the three. That is the common case and
it is a complete, correct atom. Marking structure that the clause does not state
is a worse error than leaving it off.

Note also that the second and third clauses say the same thing in opposite
directions and about different parties, and their names differ accordingly —
`must_print_receipt__operator_user` against
`mustnot_resell_contact_details__operator_third_party`. That difference is the
whole reason the prefix and the party chain exist.
<!-- DEMONSTRATIONS-END -->

BUDGET. Keep your reasoning short and your answer complete. A truncated reply
is worth nothing — every atom in it is lost. If you are running long, emit
fewer atoms per clause; never stop mid-object.

=== USER ===
Task: annotate each clause listed below with the atoms it is about.

{{KNOWN_ATOMS_BLOCK}}===== CLAUSES TO ANNOTATE ({{N_CLAUSES}}) =====
{{BATCH_LINE}}

Each entry is a header line — id | locator | kind — followed by that clause's
candidate spans, one per line, labelled s1, s2, ... Those labels are what you
put in "span_id"; do not write quote text anywhere. "[whole clause]" is the
entire clause; the rest are smaller slices of it.

Some entries carry a "[preceding context ...]" line. That is a neighbouring
clause shown only so you can tell what an example or a fragment refers to. Do
NOT annotate it — it is not on the list and another request covers it.

{{CLAUSES}}

===== OUTPUT =====
One JSON object with a single key "clauses": one entry per clause id above,
each {"clause_id": ..., "atoms": [...]}. No other text.
