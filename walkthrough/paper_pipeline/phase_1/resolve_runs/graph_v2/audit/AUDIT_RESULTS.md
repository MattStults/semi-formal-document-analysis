# Fable audit results — 2026-08-10, scored against AUDIT_KEY.md (pre-registered)

| Stratum | Result | Threshold verdict |
|---|---|---|
| A node fidelity (n=30) | FAITHFUL 24 (80%), OVERREACH 4, INCOMPLETE 2, WRONG 0; split-defects 4 | at the 80% boundary → usable WITH the repair pass |
| B edge validity (n=30) | VALID 28 (93%), MISMATCH 1, PARTIAL 1, MENTION-ONLY 0 | join-grade (≥90%) |
| C blind re-adjudication | renames 9/9 CONFIRMED; merge CONFIRMED; structure node CONFIRMED; usage_policies truly-external CONFIRMED; danglings: 9/10 recorded escalations WRONG (resolvable in-graph) | adjudicated decisions sound; ESCALATION was the over-conservative habit |
| D coverage honesty (n=17) | 17/17 correctly-uncovered, 0 silently-dropped | clean |

## Systematic defect classes (each with enumerated instances in report_*.json)
1. MODAL STRENGTHENING — establishes upgrades document "should" to "must" (≥2 sampled
   instances). Deontic strength is load-bearing for ASP; needs a targeted sweep.
2. HEADING/SECTION CONCEPT SEMANTICS — section-local authority markers with global-sounding
   provides prose (guideline_authority); heading-only providers for rich concepts
   (do_not_encourage_self_harm bare heading); section-lead nodes lacking a provides entry
   for the section concept (3 cases). The graph's one systematic weak spot.
3. PROVIDES UNDER-EXPORT → FALSE DANGLINGS — 9/10 final danglings resolvable: providers
   exist (split onto avoid_info_hazards+do_not_facilitate for harmful_illicit...), or the
   concept is established in-span but never exported (protected_groups CIRCULAR — defined
   inside its own needer's span; L3384-3501_n009 empty provides; conscientious-employee
   metaphor at L372 dropped by L292-526_n009).
4. MERGE CONTENT LOSS — the n028 merge kept the 5-tier establishes and dropped tier 6
   ("No Authority", L191), which the retired node carried. The id/content diff missed it
   because absorbed-content preservation was never checked. Instrument lesson recorded.

## Instrument notes
- graph_check.py off-by-one: believes the file has 4692 lines (splitlines artifact).
- Merge verification must diff ABSORBED content (retired node's establishes/tiers) into
  the surviving node, not only check survivors unchanged.
