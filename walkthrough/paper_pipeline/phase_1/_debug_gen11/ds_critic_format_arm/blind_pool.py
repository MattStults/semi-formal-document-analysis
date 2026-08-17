#!/usr/bin/env python3
"""THE BLIND POOL — cell labels stripped before any identification is scored.

⛔ WHY.  Arm E's headline was the adjudicator's own match of a critic sentence to
a frozen item, with the criteria formed while reading the replies.  Arm F freezes
the criteria first (`key/frozen_key.json`) and strips the cell label second.

WHAT GOES IN: every critic reply from **F1, F2 and ARM E**.  Arm E is re-scored
under arm F's key, from the same pool, because otherwise F1 and F2 are not
comparable to anything.

WHAT COMES OUT:
  blind/replies/<opaque>.txt   the reply, clause id kept, CELL STRIPPED
  blind/candidates.json        the mechanical prefilter's proposals per reply
  blind/_sealed_map.json       opaque id -> (cell, clause).  NOT read until
                               `verdicts.json` is complete; `unseal.py` refuses
                               otherwise.

The clause id is NOT stripped: the key is per-clause, so scoring without it is
impossible.  What is hidden is which of the three reply-contracts produced the
reply — which is the only thing that could bias the match.

⚠️ THE BLIND IS BROKEN ON FOUR ARM-E REPLIES and this is recorded in the pool
itself, not just in prose: I read arm E's `edits.md` for `l171_426_n022`,
`l3147_3238_n003`, `l3239_3382_n002` and `l4252_4482_n005` while designing this
arm.  Those replies are recognisable to me.  `broken_blind` marks them.

⛔ The prefilter PROPOSES.  It never decides.  A candidate is a line that shares
an anchor group with an item; whether it actually names the change the item
requires is a read, and the read is what `verdicts.json` records.

READ-ONLY except `_debug_gen11/ds_critic_format_arm/blind/`.
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
G11 = os.path.dirname(HERE)
BLIND = os.path.join(HERE, "blind")
KEY = json.load(open(os.path.join(HERE, "key", "frozen_key.json"),
                     encoding="utf-8"))

SOURCES = {
    "armE": os.path.join(G11, "ds_critic_arm", "out"),
    "F1": os.path.join(HERE, "out_f1"),
    "F2": os.path.join(HERE, "out_f2"),
}
#: clauses whose arm-E reply I had already read in this session (PREREG §4.2)
BROKEN_BLIND = {("armE", "l171_426_n022"), ("armE", "l3147_3238_n003"),
                ("armE", "l3239_3382_n002"), ("armE", "l4252_4482_n005")}

#: a fixed salt, so the mapping is reproducible and not chosen after the fact
SALT = "armF-blind-2026-08-16"

FIX_RE = re.compile(r"^\s*E(\d+)\s*:\s*FIX\b[\s—\-:]*(.*)$")
VERDICT_RE = re.compile(r"^\s*E(\d+)\s*:\s*(PASS|FIX)\b", re.I)


def opaque(cell, cid):
    return "R" + hashlib.sha256(f"{SALT}|{cell}|{cid}".encode()
                                ).hexdigest()[:10]


def fix_lines(raw):
    out = []
    for ln in raw.splitlines():
        if not VERDICT_RE.match(ln):
            continue
        m = FIX_RE.match(ln)
        if m and m.group(2).strip():
            out.append({"entry": int(m.group(1)), "text": m.group(2).strip()})
    return out


def candidates(cid, fl):
    """Mechanical prefilter: item <- line if the line contains every token of
    any one anchor group."""
    out = []
    for item in KEY.get(cid, []):
        cands = []
        for i, f in enumerate(fl):
            s = f["text"].lower()
            for grp in item["anchors"]:
                if all(t in s for t in grp):
                    cands.append({"line": i, "entry": f["entry"],
                                  "anchor": grp})
                    break
        out.append({"id": item["id"], "element": item["element"],
                    "identify_if": item["identify_if"],
                    "repair_if": item["repair_if"], "candidates": cands})
    return out


def main():
    os.makedirs(os.path.join(BLIND, "replies"), exist_ok=True)
    pool, sealed, cand = [], {}, {}
    for cell, d in SOURCES.items():
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".critic.txt"):
                continue
            cid = f.split(".")[0]
            raw = open(os.path.join(d, f), encoding="utf-8").read()
            oid = opaque(cell, cid)
            sealed[oid] = {"cell": cell, "clause_id": cid,
                           "broken_blind": (cell, cid) in BROKEN_BLIND}
            fl = fix_lines(raw)
            open(os.path.join(BLIND, "replies", f"{oid}.txt"), "w",
                 encoding="utf-8").write(
                     f"reply {oid}\nclause {cid}\n"
                     f"{len(fl)} FIX lines\n\n" + raw.strip() + "\n")
            pool.append({"reply": oid, "clause_id": cid,
                         "n_fix": len(fl), "fix_lines": fl})
            cand[oid] = {"clause_id": cid, "fix_lines": fl,
                         "items": candidates(cid, fl)}
    pool.sort(key=lambda r: r["reply"])          # shuffled by hash, not by cell
    json.dump(pool, open(os.path.join(BLIND, "pool.json"), "w"), indent=1)
    json.dump(cand, open(os.path.join(BLIND, "candidates.json"), "w"), indent=1)
    json.dump(sealed, open(os.path.join(BLIND, "_sealed_map.json"), "w"),
              indent=1)
    print(f"{len(pool)} replies pooled, cell labels stripped")
    print(f"  key: 164 items / 17 clauses, sha256 "
          f"{hashlib.sha256(open(os.path.join(HERE, 'key', 'frozen_key.json'), 'rb').read()).hexdigest()[:8]}")
    n = sum(len(i['candidates']) > 0 for r in cand.values() for i in r['items'])
    print(f"  prefilter proposes {n} item/reply pairs for adjudication")
    return 0


if __name__ == "__main__":
    sys.exit(main())
