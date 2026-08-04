"""Materialise the read-back loss corpus as a flat, coder-ready file.

DIAGNOSTIC ONLY. Produces no score and feeds no query. It exists so that the
hole-taxonomy pass reads a frozen artifact rather than a hand-pasted sample,
and so two independent coders provably see byte-identical input.

The corpus is ALREADY PAID FOR: these are the judge's own words from the
read-back run over 125 clauses. Nothing here calls a model.

Two channels, kept apart because they answer different questions:
  missing      — content of the clause the atoms did NOT carry.  HOLES.
  unsupported  — content the atoms asserted that the clause did NOT say.
                 FABRICATION, not a hole; a grammar feature would not fix it.
"""
from __future__ import annotations

import json
import pathlib

HERE = pathlib.Path(__file__).parent
RESULTS = HERE / "readback_results.json"
OUT = HERE / "hole_corpus.json"

#: The read-back was run per-clause under two conditions; `fidelity` is the
#: 125-clause pass over real annotations. `discrim` is a 4-clause control and
#: is EXCLUDED — mixing a control into the corpus would let its induced
#: categories look like document structure.
RUN = "fidelity"


def build():
    d = json.loads(RESULTS.read_text())
    per = d["results"][RUN]
    src = {}
    for key in ("gloss_echo", "trials", "fidelity_trials"):
        blob = d.get(key)
        if isinstance(blob, dict):
            for cid, rec in blob.items():
                if isinstance(rec, dict) and rec.get("source_text"):
                    src.setdefault(cid, rec["source_text"])
        elif isinstance(blob, list):
            for rec in blob:
                if isinstance(rec, dict) and rec.get("source_text"):
                    cid = rec.get("clause_id") or rec.get("id")
                    if cid:
                        src.setdefault(cid, rec["source_text"])

    items, fabrications = [], []
    for cid, rec in sorted(per.items()):
        if not isinstance(rec, dict):
            continue
        text = src.get(cid)
        for phrase in rec.get("missing") or []:
            items.append({"id": f"{cid}#m{len(items)}", "clause_id": cid,
                          "phrase": phrase, "clause_text": text})
        for phrase in rec.get("unsupported") or []:
            fabrications.append({"id": f"{cid}#u{len(fabrications)}",
                                 "clause_id": cid, "phrase": phrase,
                                 "clause_text": text})

    out = {
        "artifact": "hole_corpus",
        "derived_from": "readback_results.json",
        "run": RUN,
        "clauses": len(per),
        "with_source_text": sum(1 for i in items if i["clause_text"]),
        "missing": items,
        "unsupported": fabrications,
        "caveat": (
            "Every phrase is the READ-BACK JUDGE's paraphrase, not the "
            "document's wording. A taxonomy induced over these phrases "
            "describes what that judge noticed and how it chose to say so. "
            "It is evidence about the grammar's holes, not a census of them: "
            "loss the judge did not notice is absent by construction."),
    }
    OUT.write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    o = build()
    print(f"clauses      {o['clauses']}")
    print(f"missing      {len(o['missing'])}")
    print(f"unsupported  {len(o['unsupported'])}")
    print(f"source text  {o['with_source_text']}/{len(o['missing'])}")
    print(f"-> {OUT}")
