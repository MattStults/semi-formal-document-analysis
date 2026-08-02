<!-- Prompt template for annotate.py.
     Two parts, split on the two marker lines below. Placeholders:
       {{KNOWN_ATOMS_BLOCK}}  vocabulary already coined earlier in this run
       {{BATCH_LINE}}         which slice of the document this request covers
       {{N_CLAUSES}}          how many clauses are listed
       {{CLAUSES}}            the clauses: id, locator, kind, candidate spans
     Nothing else is substituted. Braces elsewhere are literal JSON.

     DELIBERATELY ABSENT: anything about a particular behaviour, question, or
     query. This annotation is produced ONCE and then answers many behaviour
     queries offline. If a behaviour description ever reaches this prompt the
     tool collapses into "ask a model per query" — which is the baseline it
     exists to beat — and the fast-iteration property is gone. -->

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
         "gloss": str, "span_id": str}

Your whole reply is one JSON object:

  {"clauses": [{"clause_id": str, "atoms": [atom, ...]}, ...]}

One entry per clause you were given, in the order given. A clause that
genuinely carries no reusable concept gets "atoms": [] — that is a legitimate
answer, not a failure.

THE FOUR KINDS. This set is closed. Do not invent a fifth.

  situation — a circumstance that may or may not obtain: what is going on when
              the clause applies. "the user's request is ambiguous", "the
              operator's instruction conflicts with a platform rule", "the
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
