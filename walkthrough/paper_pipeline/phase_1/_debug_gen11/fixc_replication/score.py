"""Validate experiment outputs exactly as the pipeline does.

translate.py:1381 calls repair_loop(..., corpus_ids=known_ids) and
translate.py:2557 calls checks.run_checks(obj, clause, corpus_ids,
concepts=None, attempt=n).  `concepts=None` means the module's own rows -- the
same self-contained per-clause gate the live run used at attempt 1.
"""
import json, os, re, sys, glob

HERE = "/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
sys.path.insert(0, HERE)
import checks as _checks          # noqa: E402
import schema as _schema          # noqa: E402
from translation_repair_census import classify, FINDING  # noqa: E402

CORPUS = os.path.join(HERE, "resolve_runs/graph_v2/node_corpus_all.json")
_c = json.load(open(CORPUS))
ROWS = {r["id"]: r for r in _c["clauses"]}
KNOWN = set(ROWS)


def extract_json(text):
    """The raw response; the pipeline json.loads()es it directly."""
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\s*", "", t)
        t = re.sub(r"\s*```\s*$", "", t)
    try:
        return json.loads(t), None
    except json.JSONDecodeError as exc:
        i, j = t.find("{"), t.rfind("}")
        if i >= 0 and j > i:
            try:
                return json.loads(t[i:j + 1]), "fenced/extracted"
            except json.JSONDecodeError as e2:
                return None, str(e2)
        return None, str(exc)


def score_one(clause_id, raw_text):
    obj, note = extract_json(raw_text)
    if obj is None:
        return {"ok": False, "outcome": "not-json", "findings": [],
                "classes": ["not-json"], "note": note}
    row = ROWS[clause_id]
    res = _checks.run_checks(obj, row, KNOWN, concepts=None, attempt=1)
    fs = [{"check": f.check_id, "sev": f.severity, "where": f.where,
           "msg": f.message} for f in res.findings]
    classes = sorted({classify(f["check"], f["msg"]) for f in fs
                      if f["sev"] == "error"})
    return {"ok": (res.outcome == "translated"), "outcome": res.outcome,
            "findings": fs, "classes": classes, "note": note,
            "n_ontology": len(obj.get("ontology") or []),
            "n_ontology_bodyless": len([o for o in (obj.get("ontology") or [])
                                        if isinstance(o, dict)
                                        and not o.get("body")]),
            "n_inputs": len(obj.get("inputs") or []),
            "n_requires": len(obj.get("requires") or []),
            "n_concepts": len(obj.get("concepts") or [])}


def main(expdir):
    man = json.load(open(os.path.join(expdir, "manifest.json")))
    out = []
    missing = []
    for t in man["tasks"]:
        p = os.path.join(expdir, t["task_id"], "answer.json")
        if not os.path.exists(p):
            missing.append(t["task_id"])
            continue
        raw = open(p, encoding="utf-8").read()
        r = score_one(t["clause"], raw)
        r.update(task_id=t["task_id"], arm=t["arm"], clause=t["clause"],
                 draw=t["draw"])
        out.append(r)
    json.dump(out, open(os.path.join(expdir, "scored.json"), "w"), indent=1)
    print("scored", len(out), "missing", len(missing), missing[:20])
    return out


if __name__ == "__main__":
    main(sys.argv[1])
