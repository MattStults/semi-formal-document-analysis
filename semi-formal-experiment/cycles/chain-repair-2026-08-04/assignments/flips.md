# Flip adjudication assignment — cycle chain-repair-2026-08-04

Seat brief: briefs/flip_adjudicator.md — read it first; it is the seat's
entire instruction. Judge each flip AGAINST THE DOCUMENT, from the dossier
alone.

Dossiers: flip_dossiers/ under this cycle's directory. Enumerate the work via
flip_dossiers/index.jsonl — one JSON dossier file per flip.

Dossier set sha256: 508c8aa1606246d5b009babdd64fc0add9032b8c244f3bd2a56a35b7a35c2abc

Required output: flip_verdicts.json in this cycle's directory:

    {"dossier_set_sha": "508c8aa1606246d5b009babdd64fc0add9032b8c244f3bd2a56a35b7a35c2abc",
      "records": [
        {"flip_id": "<copied verbatim from the dossier>",
          "verdict": "correct" | "regression" | "unclear",
          "document_reason": "<document-side reason, citing the clause>",
          "confidence": "high" | "medium" | "low"},
        ...]}

The dossier_set_sha above MUST be echoed verbatim — it binds your verdicts
to exactly this dossier set. flip_id, verdict, document_reason are REQUIRED
per record; confidence optional. Every flip in index.jsonl exactly once.
Reusing a previous adjudication is legal ONLY when the dossier bytes are
identical (same set sha) and declared via a "reused_from" key naming the
source file — never presented as fresh adjudication. The file is checked by
`dossier.py validate` before the cycle advances.
