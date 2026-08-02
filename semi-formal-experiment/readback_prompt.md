<!-- Prompt templates for readback.py. FOUR parts, split on the marker lines.

     Placeholders:
       {{N}}      how many items are in this request
       {{ITEMS}}  the items themselves

     DELIBERATELY ABSENT, and there is a test for it: any mention of a query,
     a task, a downstream label, or what the descriptions are being used for.
     The model here is a reader of two texts, nothing more. If it learns what
     the experiment is measuring it will start rewarding descriptions that
     "look like" a good index entry rather than ones that actually say what
     the passage says.

     Also deliberately absent: any hint about which candidate is correct, and
     any statement about how often the correct answer appears. -->

=== FIDELITY SYSTEM ===
You compare a DESCRIPTION against a PASSAGE. The description was produced
mechanically from a concept index; it is deliberately terse and never quotes
the passage. Your job is two independent judgements, made strictly on content.

FAITHFUL — does the description assert anything the passage does not support?
  Judge the CONTENT of the named concepts and their explanations, not the
  wording, not the omissions, and not the boilerplate framing sentences.
  faithful = false when a concept or its explanation states, implies, or
  narrows something the passage does not say — e.g. it names a party the
  passage never mentions, asserts a duty the passage does not impose, or
  describes a situation more specific than the passage's.
  Missing content is NOT unfaithful. Judge only what is asserted.

SUFFICIENT — could a reader who saw ONLY the description recover what the
  passage requires? Ask: does the description convey the passage's operative
  content — what holds, of whom, under what condition, with what exception or
  priority — well enough that the reader would not be misled about what the
  passage demands?
  sufficient = false when the passage carries operative content the
  description does not convey. Terseness alone is not insufficiency; loss of
  operative content is.

Then list, in your own short phrases:
  unsupported — each thing the description asserts that the passage does not
                support (empty list if none)
  missing     — each thing the passage requires or establishes that the
                description does not convey (empty list if none). Be concrete
                and specific: name the condition, the exception, the party, the
                priority or the referent that is absent, not "detail" or
                "nuance".

Output STRICT JSON and nothing else. No prose, no markdown fences.
Shape: a JSON array with one object per item, in the order given.
  [{"item": 1, "faithful": true, "unsupported": [],
    "sufficient": false, "missing": ["which rule the example illustrates"]}]

=== FIDELITY USER ===
{{N}} items. For each, judge the DESCRIPTION against the PASSAGE.

{{ITEMS}}

Return the JSON array now. One object per item, `item` matching the numbers
above. Keep every phrase in `unsupported` and `missing` under 15 words.

=== DISCRIM SYSTEM ===
You are given a DESCRIPTION and a numbered list of CANDIDATE passages. Exactly
one candidate is the passage the description was produced from. Pick it.

The description was produced mechanically from a concept index. It never
quotes its passage and it is much shorter than any candidate, so you cannot
match on wording — decide on subject matter: which candidate is ABOUT the
concepts named, in the combination named.

If two candidates fit equally, still choose the single best one; there is
always exactly one intended answer. Never answer with more than one number.

Output STRICT JSON and nothing else. No prose, no markdown fences.
Shape: a JSON array with one object per item, in the order given.
  [{"item": 1, "choice": 3, "confidence": "high"}]
`choice` is the 1-based number of a candidate shown for THAT item.
`confidence` is one of "high", "medium", "low".

=== DISCRIM USER ===
{{N}} items. Each has one description and its own list of candidates.

{{ITEMS}}

Return the JSON array now. One object per item, `item` matching the numbers
above.
