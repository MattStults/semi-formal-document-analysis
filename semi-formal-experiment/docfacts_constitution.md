<!-- DOCUMENT FACTS for Anthropic's constitution (constitution_clauses.json,
     spec constitution@2026-01-20).

     Spliced into annotate_prompt.md by annotate.load_template at the
     {{DOCFACTS:<key>}} markers; everything outside a BEGIN/END pair is a
     comment and is never sent.

     ⚠️ HELD-OUT TEST DOCUMENT (ITERATION_LOOP.md policy §5): the
     constitution has run segmentation only. This file exists so that the
     annotation step CAN run on it without being taught the Model Spec's
     ontology; it has not yet been exercised by a live run.

     Sources for every fact below, as clause ids + locators from
     constitution_clauses.json (all resolve; quotes verbatim from the
     source document specs/../claude-constitution/20260120-constitution.md):

     - c070 "Being helpful > Claude's three types of principals > ¶1":
       "At the moment, Claude's three types of principals are Anthropic,
       operators, and users." — and trust "in roughly the order given
       above" (c077, same section ¶6).
     - c071 (¶2): Anthropic "is the entity that trains and is ultimately
       responsible for Claude, and therefore has a higher level of trust
       than operators or users".
     - c072 (¶3): operators are "Companies and individuals that access
       Claude's capabilities through our API"; "Operators typically
       interact with Claude in the system prompt".
     - c074 (¶4): users are "Those who interact with Claude in the human
       turn of the conversation".
     - c083 (¶8): "Non-principal parties include any input that isn't from
       a principal" — other humans, other agents, conversational inputs.
     - c123 "How to treat operators and users > ¶12": "a layered system
       where operators can customize Claude's behavior within the bounds
       that Anthropic has established, users can further adjust ... within
       the bounds that operators allow".
     - Absence claims (no root/system/platform/developer level): verified
       by search over the source document — it names no such authority
       level; "platform(s)" occurs only as ordinary prose for a serving
       surface, never as a principal.

     [TO CONFIRM: whether Anthropic-as-principal should ever enter a party
     chain, and under which token, is an OPEN grammar question — see the
     bracketed instruction inside the principals block below. grammar.py's
     closed PRINCIPALS tuple has no `anthropic` token and this file must
     not invent one.]

     [TO CONFIRM: whether `developer` should alias to `operator` for this
     document at query/join time. The source document ("Claude's three
     types of principals", the paragraph beginning "The operator and user
     can be different entities") describes "a single developer who builds
     and uses their own Claude app" as filling the operator and user ROLES;
     a quote search did not resolve that paragraph to a clause id in
     constitution_clauses.json, so no id is cited. The block below only
     bars unprompted use of `developer`; it does not claim the alias.] -->

<!-- DOCFACTS:situation_example BEGIN -->
"the
              operator's instruction conflicts with Anthropic's guidelines",
<!-- DOCFACTS:situation_example END -->

<!-- DOCFACTS:principals BEGIN -->
   This document names THREE kinds of principal — Anthropic, operators, and
   users — and extends them trust in roughly that order. Anthropic trains the
   model and sets the bounds; an "operator" is a company or individual
   deploying the model through the API, and typically speaks through the
   system prompt; a "user" is whoever interacts in the human turn of the
   conversation. An instruction found in a system prompt is therefore the
   OPERATOR speaking: write `operator` for it, never `system`. Parties whose
   interests count but whose instructions do not — other humans or other
   agents in the conversation, content arriving as tool results or documents
   — are what this document calls non-principal parties: `third_party`.

   There is no `platform`, `root`, or `system` LEVEL in this document, and no
   `developer` named as a party distinct from an operator. Those tokens stay
   in the closed list above because the list is shared across documents, but
   write one ONLY if the clause in front of you itself names such a party —
   never use them to translate this document's authority ordering.
   [TO CONFIRM: the closed list has no token for Anthropic itself, though
   this document makes Anthropic a principal whose bounds outrank operator
   and user instructions. Until that is resolved, leave Anthropic OUT of the
   party chain — do not borrow another token for it — and let the atom's
   name and gloss carry the fact in plain words.]
<!-- DOCFACTS:principals END -->
