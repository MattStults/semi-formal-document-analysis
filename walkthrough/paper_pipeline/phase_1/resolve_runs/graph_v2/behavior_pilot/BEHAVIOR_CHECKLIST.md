# Behavior-authoring checklist — general fixes that help every future behavior

Each item was licensed by a MEASURED failure (source cited). Apply when
writing or iterating a behavior's atoms; the seat brief enforces the same
rules from the other side.

1. **Name the party in every atom that involves harm, duty, or protection.**
   "harm" alone engages user-harm, third-party-harm and confidentiality
   clauses alike. Write `harm_to_third_party_outside_conversation`, not
   `harm`. (Registered result 2026-08-18: harm-avoidance engagement
   defensibility 0.56 — every precision error was a party-scope conflation.)
2. **Cover both directions of a calibration behavior with atoms phrased in
   the DOCUMENT's own framing.** The over/under-caution atoms were written
   about *requests* ("refuses a benign request"); the spec's anti-over-refusal
   clauses are written about *topics* and *agenda* ("never avoid a topic
   because it is sensitive", "refusing is itself an agenda"). Add atoms in
   the document's vocabulary or the seat never sees the clause. (17/17 caution
   declines were real misses; the whole `l2126_2404` cluster.)
3. **Include the paradigm cases as concrete atoms.** Harm-avoidance missed
   CSAM, bio-threat, illicit-behavior and extremist-content clauses — the
   textbook cases — because its atoms were abstract ("foreseeable societal
   harm"). One atom per paradigm case reaches them. (35/43 harm-avoidance
   declines were real misses.)
4. **Prefer acts and conditions over considerations.** Consideration atoms
   ("stake that…") engage little and ground nothing; act atoms fire. Keep at
   most one consideration per behavior.
5. **State the atom's vocabulary reach test:** would a policy clause about
   this element share at least one content word with the gloss? If not,
   retrieval never surfaces it (embed-rank is lexical-then-judged).

Provenance: THREEWAY_REPORT.md action column; REGISTERED_RESULT.md; the
2026-08-17/18 blind adjudication rounds. Layer: behavior translation
(checklist) + seat brief; retrieval width is a separate infrastructure item.
