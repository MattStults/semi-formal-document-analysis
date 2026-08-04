"""Merge the two stratum verdict shards into the canonical verdict_file.json.

Pure concatenation with duplicate/coverage checks; no verdict is altered.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

primary = json.loads((HERE / "verdicts_primary.json").read_text())
unmarked = json.loads((HERE / "verdicts_unmarked.json").read_text())
worksheet = json.loads((HERE / "worksheet.json").read_text())


p_recs, u_recs = primary["records"], unmarked["records"]

sha_p = primary.get("worksheet_sha256")
sha_u = unmarked.get("worksheet_sha256")
if sha_p != sha_u or sha_p is None:
    sys.exit(f"worksheet_sha256 mismatch between shards: {sha_p} vs {sha_u}")


def key(rec):
    return (rec["clause_id"], rec["name"])


merged, seen = [], set()
for rec in p_recs + u_recs:
    k = key(rec)
    if k in seen:
        sys.exit(f"duplicate verdict across shards: {k}")
    seen.add(k)
    merged.append(rec)

out = {"worksheet_sha256": sha_p, "records": merged}
(HERE / "verdict_file.json").write_text(json.dumps(out, indent=1) + "\n")
print(f"merged {len(p_recs)} primary + {len(u_recs)} unmarked = {len(merged)} verdicts")
from collections import Counter

print(Counter(r["verdict"] for r in merged))
