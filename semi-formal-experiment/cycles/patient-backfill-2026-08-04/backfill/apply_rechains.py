"""Batch driver for the patient-backfill rechain applications — cycle
patient-backfill-2026-08-04 (the merge_verdicts.py precedent: a cycle
artifact, not shipped tooling).

Reads backfill/verdict_file.json (validator CLEAN, golden-reviewed), groups
every chain_licensed record into ONE migration per (name, corrected_chain)
with the licensed clause set as --clause scope, and drives
atom_refactor.plan_migration / apply_changes — the exact functions behind
the CLI, so the vocabulary_migrations.json entries are byte-for-byte what
per-entry CLI invocation would have written (BACKFILL_DESIGN §5 volume
note). Deterministic: migrations sorted by (old_name, chain); date is the
manifest's, never the wall clock.

Every entry is stamped with the ext_v1-lineage surface scope (the S2 seam,
designer-ruled at the IMPLEMENT halt): the b8/legacy annotation surfaces
(annotations.json, annotations_b8.json) are frozen chain-free historical
artifacts and are never decorated by a backfill-class rechain, and replay
honors the recorded scope.

Usage (from the repo root):
    python3 cycles/patient-backfill-2026-08-04/backfill/apply_rechains.py           # dry-run plan
    python3 cycles/patient-backfill-2026-08-04/backfill/apply_rechains.py --apply   # apply + log
"""
from __future__ import annotations

import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)

import atom_refactor  # noqa: E402
import grammar        # noqa: E402

VERDICT_FILE = os.path.join(HERE, "verdict_file.json")
DATE = "2026-08-04"   # the frozen manifest's date, caller-supplied

#: The backfill's surface scope: the ext_v1 lineage ONLY. b8/legacy
#: annotation surfaces stay frozen chain-free (atom_refactor module policy).
SURFACES = ["annotations_ext_v1.json", "annotations_ext_v1_patch.json",
            "annotations_ext_v1_merged.json"]


def migrations():
    with open(VERDICT_FILE) as f:
        payload = json.load(f)
    groups = collections.defaultdict(set)
    for r in payload["records"]:
        if r["verdict"] != "chain_licensed":
            continue
        groups[(r["name"], tuple(r["corrected_chain"]))].add(r["clause_id"])
    out = []
    for (old, chain), clauses in sorted(groups.items()):
        p = grammar.parse_name(old)
        assert not p["error"] and not p["principals"], old
        new = grammar.format_name(p["stem"], p["polarity"], list(chain))
        reason = (
            f"patient backfill (worksheet seat, independently reviewed): "
            f"the clause text of {', '.join(sorted(clauses))} names "
            f"{chain[0]} acting and {', '.join(chain[1:]) or 'no patient'} "
            f"acted upon; verbatim license_quote per clause in "
            f"cycles/patient-backfill-2026-08-04/backfill/verdict_file.json")
        out.append((old, new, sorted(clauses), reason))
    return out


def main() -> int:
    apply = "--apply" in sys.argv[1:]
    per_file = collections.Counter()
    total = 0
    n_migrations = 0
    for old, new, clauses, reason in migrations():
        entry, changes = atom_refactor.plan_migration(
            REPO, "rechain", old, new, date=DATE, reason=reason,
            clauses=clauses, surfaces=SURFACES)
        if apply:
            atom_refactor.apply_changes(REPO, entry, changes)
        n_migrations += 1
        for rel, ch in changes.items():
            per_file[rel] += ch["n"]
            total += ch["n"]
        print(f"{'APPLIED' if apply else 'plan':7s} {old} -> {new} "
              f"clauses={len(clauses)} rewrites="
              f"{sum(ch['n'] for ch in changes.values())}")
    print()
    print(f"{'APPLIED' if apply else 'DRY-RUN'}: {n_migrations} migrations, "
          f"{total} rewrites")
    for rel in sorted(per_file):
        print(f"  {rel}: {per_file[rel]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
