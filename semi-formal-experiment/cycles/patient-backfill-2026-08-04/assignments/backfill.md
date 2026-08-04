# Patient-chain worksheet seat assignment — cycle patient-backfill-2026-08-04

Seat brief: briefs/backfill_author.md — read it first; it is the seat's
entire instruction. Judge every worksheet row from its clause text alone,
under the licensing rules the worksheet header quotes verbatim. You may
additionally consult grammar.py and annotate_prompt.md, and nothing else.

Worksheet: backfill/worksheet.json under this cycle's directory —
692 candidate instances over 462 clauses. Work it in its emitted order:
the polarity-marked stratum (505 instances, 347 clauses) comes first, then
the unmarked stratum (187 instances, 148 clauses). Every instance receives
exactly one record; `unclear` is legal and lands nothing.

Worksheet sha256:
ce26cf89b37cb05c7d8adab12c3f3dae12388befe9d34a9f76aa0cf39209c6c7

Required output: backfill/verdict_file.json in this cycle's directory:

    {"worksheet_sha256":
       "ce26cf89b37cb05c7d8adab12c3f3dae12388befe9d34a9f76aa0cf39209c6c7",
     "records": [
       {"clause_id": "...", "name": "...",
        "verdict": "chain_licensed" | "no_chain_licensed" | "unclear",
        "corrected_chain": [...] | null,
        "license_quote": "<exact clause-text substring>" | null,
        "reason": "<at most 25 words>",
        "flag": "<optional>"},
       ...]}

The worksheet_sha256 above MUST be echoed verbatim — it binds your records
to exactly this worksheet. Every `chain_licensed` record must quote its
license verbatim from the clause text (mechanically checked as a
substring); a chain that cannot quote its license does not land.

Self-check before delivering (must print CLEAN):

    python3 backfill_worksheet.py validate \
        --dir cycles/patient-backfill-2026-08-04/backfill

Your records are then independently reviewed — both directions, licensed
and unlicensed — before anything is applied. Nothing is applied by you.
