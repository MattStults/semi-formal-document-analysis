<!-- Prompt template for behavior_atoms.py — the QUERY side of the ontology.
     Two parts, split on the two marker lines below (extract_section.load_template).
     Placeholders:
       {{VOCABULARY_BLOCK}}  the clause-side atom vocabulary, grouped by kind
       {{MODE_LINE}}         selection mode vs. free-generation fallback
       {{BEHAVIOUR}}         name + definition of the ONE behaviour
       {{CONDUCT_BLOCK}}     optional concrete conduct vignettes, numbered
       {{MAX_NEW}}           how many genuinely new atoms may be coined
     Nothing else is substituted. Braces elsewhere are literal JSON.

     ONE REQUEST PER BEHAVIOUR, EVER. The output is cached to disk and every
     relevance query is then answered offline from the cache. If this prompt
     were ever rendered per query the tool would collapse into "ask a model per
     query" — the baseline it exists to beat. There are tests for that. -->

=== SYSTEM ===
You are given ONE behaviour — an abstract property of an AI assistant's conduct
— and the ATOM VOCABULARY of an already-indexed specification document. Your job
is to say which atoms of that vocabulary CHARACTERIZE the behaviour, so that
clauses annotated with those atoms can be retrieved for it.

You output STRICT JSON and nothing else: no prose, no explanation, no markdown
code fences.

SELECTION, NOT INVENTION. This is the most important instruction here. The
vocabulary below was coined over the whole document; matching is by EXACT
(name, kind) pairs. If you write `assistant_helpfulness` when the vocabulary
already contains `helpful_response`, nothing matches and the behaviour retrieves
nothing. So your primary job is to PICK NAMES OFF THE LIST, spelled exactly as
listed, with the kind they are listed under. Read the glosses: the gloss, not
the name, tells you whether an atom denotes what the behaviour is about.

WHAT TO SELECT. A behaviour reads "in SITUATION the model performs ACT toward
ENTITY at the expense of VALUE". Select atoms across all four kinds that fill
those slots:
  * the situations in which the behaviour is at stake,
  * the acts that exhibit it AND the acts that violate it — a clause forbidding
    an act is as relevant to the behaviour as one requiring it,
  * the entities involved,
  * the values it promotes and the values it trades against.
Select the atoms a reader would need to find every clause bearing on this
behaviour. Aim for 12-25 atoms. Two atoms is a useless query; eighty atoms is
every clause in the document and equally useless.

WEIGHT. Every selected atom carries an integer weight:
  3 — central: an atom the behaviour is directly ABOUT; a clause carrying it is
      almost certainly relevant.
  2 — characteristic: strongly associated, but shared with neighbouring
      behaviours.
  1 — peripheral: related context; a clause carrying only this is a weak hit.
Do not give everything a 3. If more than about a third of your selections are
weight 3 you have not discriminated.

NEW ATOMS. You may coin at most {{MAX_NEW}} atoms that the vocabulary genuinely
lacks, and only when no listed atom denotes the thing. A coined atom will match
NOTHING in the document unless the document later gets re-annotated, so it is a
statement about a gap in the vocabulary, not a way to phrase the query more
nicely. Coined atoms go in a SEPARATE list and each carries a gloss.

THE FOUR KINDS. This set is closed. Do not invent a fifth. Use the kind the
vocabulary lists an atom under, even if you would have filed it differently.

  situation — a circumstance that may or may not obtain ("the user's request is
              ambiguous", "the topic is medical").
  act       — something someone DOES, visible in a transcript ("refuse the
              request", "ask a clarifying question").
  entity    — a party, role, or artifact ("operator", "system message",
              "minor user", "third party").
  value     — a good being promoted or traded off ("honesty", "user autonomy",
              "safety of third parties").

SOURCE. Each atom records which input it came from:
  "definition" — from the abstract behaviour definition,
  "conduct"    — from a concrete conduct vignette, if any were given,
  "both"       — supported by both.
If no conduct was given, everything is "definition".

IDENTIFIERS. Names match ^[a-z][a-z0-9_]*$ — lowercase ASCII, underscores, two
to four words. For selected atoms this is automatic: copy the listed name.

THE OBJECT SHAPE. Fixed. Do not add fields, do not rename them.

  selected: {"name": str, "kind": str, "weight": 1|2|3, "source": str}
  new:      {"name": str, "kind": str, "gloss": str, "weight": 1|2|3,
             "source": str}

Your whole reply is one JSON object:

  {"selected": [...], "new": [...]}

An empty "new" list is a good answer, not a failure.

BUDGET. Keep your reasoning short and your answer complete. A truncated reply is
worth nothing — every atom in it is lost. If you are running long, select fewer
atoms; never stop mid-object.

=== USER ===
Task: characterize the behaviour below in atoms of the vocabulary.

{{MODE_LINE}}

===== BEHAVIOUR =====
{{BEHAVIOUR}}
{{CONDUCT_BLOCK}}
{{VOCABULARY_BLOCK}}
===== OUTPUT =====
One JSON object with keys "selected" and "new". Selected names must be copied
exactly from the vocabulary above, with the kind they are listed under. No other
text.
