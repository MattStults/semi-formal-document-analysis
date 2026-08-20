# declaration_proposals.json — REQUIRED SHAPE
{
 "_": "<one-line status incl. the hypothesis-only disclaimer>",
 "inventory": {"contract": "v18", "run_seed": 20260820},
 "proposals": [
  {
   "behavior": "<slug>",
   "kind": "add" | "wall",
   "slot": "governs_concern" | "governs_conditional" | "protects_concern" |
           "purpose_concern" | "party_concern" | "performs_acts" | "contexts_concern",
   "schema_extension": false | true,
   "delta": <exact JSON fragment to merge into the behavior module, e.g.
             {"governs_concern": ["+objectivity_neutrality"]} or
             {"contexts_concern": ["requester_purpose_conditioned"]}>,
   "feature": "<feature-matrix column name>",
   "stability": <0..1>,
   "median_coef": <float>,
   "predicted": {"fixes": <int>, "breaks": <int>,
                 "fixed_nodes": [...], "broken_nodes": [...]},
   "blind_justification_stub": "<1-2 sentences: what DOCUMENT-side reading would
                                justify this declaration a priori — a hypothesis
                                for the 9b design round, not a claim>"
  }
 ],
 "unmappable": [{"behavior": "...", "feature": "...", "stability": <..>,
                 "why_unmappable": "..."}]
}
Sorted: proposals by predicted.fixes - predicted.breaks descending.
