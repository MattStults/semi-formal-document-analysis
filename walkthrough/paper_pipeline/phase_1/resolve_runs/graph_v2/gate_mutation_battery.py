#!/usr/bin/env python3
"""Does the mechanical instrumentation actually catch the semantic damage the
critic-loop series documented? A MEASUREMENT, not an assertion (Matt's
question, 2026-08-16).

Method: take hard-clean modules off the corpus (the gate's own report), seed
one documented defect class at a time, and ask whether schema.validate_all or
a hard-tier corpus_gate check fires. Every mutation mirrors a failure the
series measured on real traffic:

  drop_obligation           delete one deontic assert, KEEP its claim
                            (SERIES_HANDOFF §2.7's l3147_3238_n003 shape)
  drop_obligation_and_claim same, and delete the matching claim too — the
                            fully-consistent deletion. EXPECTED UNCAUGHT:
                            this is the class the series called invisible,
                            and the battery exists to say so with a number.
  hollow_stub               replace a specific assert with the generic
                            oblige respond_appropriately(S) :- situation(S)
                            (the stub the Opus feedback forbade by name),
                            with all bookkeeping (acts/closure/concepts/
                            inputs) kept consistent so only hollowness is
                            being tested.
  manufactured_citation     borrowed NEEDS gloss assumed -> textual citing
                            self (the class of DECISION_licence_textual.md)
  alternation_collapse      two same-atom ontology entries merged into one
                            with `;` (arm F2's PRESERVE case — the damage
                            that became a LOUD schema error)
  inert_ontology            an ontology head no assert can reach
  drop_closure              closure list deleted
  slot_mismatch             a read_back gains a `%` with no slot
  prefer_to_forbid          a comparative collapsed into a prohibition
                            (00_task rule 5b). EXPECTED PARTIALLY UNCAUGHT.
  drop_needs_require        a NEEDS name removed from requires

Deterministic: subjects are the first N eligible hard-clean modules by
sorted id; every mutation targets the first applicable entry. Zero spend.

Run: ../../../../../semi-formal-experiment/.venv/bin/python gate_mutation_battery.py
"""
import copy, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)
sys.path.insert(0, HERE)

import schema          # noqa: E402
import corpus_gate     # noqa: E402

N_SUBJECTS = 8


def gate_hits(cid, o, span, tier):
    hits = []
    for name, fn, default in corpus_gate.PER_MODULE:
        try:
            for h in fn(cid, o, span):
                if corpus_gate.tier_of(name, h, default) == tier:
                    hits.append(f"{name}: {h}")
        except Exception as ex:                       # noqa: BLE001
            hits.append(f"{name}: CHECK ERROR {ex!r}")
    return hits


def schema_breaches(cid, o, known):
    mod, breaches = schema.validate_all(o, clause_id=cid,
                                        known_clause_ids=known)
    return [str(b) for b in breaches]


def stage2_errors(cid, o, row, known):
    """Production stage 2: checks.run_checks (schema contract + deterministic
    link checks INCLUDING the clingo compile). error severity only."""
    import checks
    clause = {"id": cid, "section_id": row.get("section_id"),
              "kind": row.get("kind"), "quote": row.get("quote")}
    try:
        res = checks.run_checks(o, clause, known)
        return [str(e) for e in res.errors]
    except Exception as ex:                           # noqa: BLE001
        return [f"RUN_CHECKS RAISED {ex!r}"]


# ------------------------------------------------------------- mutations
# each: (module, span) -> mutated module | None if not applicable

def m_drop_obligation(o, span):
    for i, a in enumerate(o.get("asserts") or []):
        if a.get("status") in ("oblige", "forbid"):
            m = copy.deepcopy(o)
            del m["asserts"][i]
            return m
    return None


def _claim_tokens(c):
    return {t for t in re.split(r"[^a-z]+", str(c).lower()) if len(t) > 4}


def m_drop_obligation_and_claim(o, span):
    for i, a in enumerate(o.get("asserts") or []):
        if a.get("status") not in ("oblige", "forbid"):
            continue
        blob = " ".join(str(a.get(k, "")) for k in ("act", "body", "read_back")).lower()
        best, bj = -1, None
        for j, c in enumerate(o.get("claims") or []):
            n = sum(1 for t in _claim_tokens(c) if t[:5] in blob)
            if n > best:
                best, bj = n, j
        if bj is None:
            return None
        m = copy.deepcopy(o)
        del m["asserts"][i]
        del m["claims"][bj]
        return m
    return None


def m_hollow_stub(o, span):
    for i, a in enumerate(o.get("asserts") or []):
        if a.get("status") in ("oblige", "forbid"):
            m = copy.deepcopy(o)
            st = m["asserts"][i]
            st["act"] = "respond_appropriately(S)"
            st["body"] = "situation(S)"
            st["read_back"] = "the assistant should respond appropriately here"
            st["read_back_slots"] = []
            m.setdefault("acts", []).append("respond_appropriately(S)")
            m.setdefault("inputs", []).append("situation/1")
            m.setdefault("concepts", []).append(
                {"name": "respond_appropriately", "arity": 1,
                 "gloss": "the assistant handles the situation in a fitting way",
                 "licence": "assumed", "cites": None,
                 "inference": "the clause concerns appropriate handling",
                 "toggleable": False})
            m["concepts"].append(
                {"name": "situation", "arity": 1,
                 "gloss": "a situation the assistant is in",
                 "licence": "assumed", "cites": None,
                 "inference": "the clause applies to situations",
                 "toggleable": False})
            m.setdefault("closure", []).append(
                {"act_class": "respond_appropriately", "closure": "cepa",
                 "reason": "silence permits"})
            return m
    return None


def m_manufactured_citation(o, span):
    needs = set(corpus_gate.needs_names(span))
    cid = o.get("clause_id")
    for e in o.get("concepts") or []:
        if str(e.get("name", "")).split("/")[0] in needs \
                and e.get("licence") == "assumed":
            m = copy.deepcopy(o)
            for e2 in m["concepts"]:
                if e2.get("name") == e.get("name"):
                    e2["licence"] = "textual"
                    e2["cites"] = cid
                    e2["inference"] = None
                    break
            return m
    return None


def m_alternation_collapse(o, span):
    heads = {}
    for i, e in enumerate(o.get("ontology") or []):
        h = str(e.get("atom", ""))
        if e.get("body"):
            heads.setdefault(h, []).append(i)
    for h, idxs in heads.items():
        if len(idxs) >= 2:
            m = copy.deepcopy(o)
            a, b = idxs[0], idxs[1]
            m["ontology"][a]["body"] = (m["ontology"][a]["body"] + "; "
                                        + m["ontology"][b]["body"])
            del m["ontology"][b]
            return m
    return None


def m_inert_ontology(o, span):
    if not isinstance(o.get("ontology"), list):
        return None
    m = copy.deepcopy(o)
    m["ontology"].append(
        {"atom": "orphaned_classification(X)", "body": "situation_x(X)",
         "gloss": "a classification nothing ever uses",
         "licence": "assumed", "cites": None,
         "inference": "seeded by the mutation battery", "toggleable": False})
    m.setdefault("concepts", []).append(
        {"name": "orphaned_classification", "arity": 1,
         "gloss": "a class of thing the document distinguishes",
         "licence": "assumed", "cites": None,
         "inference": "seeded", "toggleable": False})
    m["concepts"].append(
        {"name": "situation_x", "arity": 1,
         "gloss": "an input state of the case",
         "licence": "assumed", "cites": None,
         "inference": "seeded", "toggleable": False})
    m.setdefault("inputs", []).append("situation_x/1")
    return m


def m_drop_closure(o, span):
    if not o.get("closure"):
        return None
    m = copy.deepcopy(o)
    m["closure"] = []
    return m


def m_slot_mismatch(o, span):
    for i, a in enumerate(o.get("asserts") or []):
        if "read_back" in a:
            m = copy.deepcopy(o)
            m["asserts"][i]["read_back"] = str(a["read_back"]) + " (see %)"
            return m
    return None


def m_prefer_to_forbid(o, span):
    for i, a in enumerate(o.get("asserts") or []):
        if a.get("status") == "prefer":
            m = copy.deepcopy(o)
            m["asserts"][i]["status"] = "forbid"
            return m
    return None


def m_drop_needs_require(o, span):
    needs = corpus_gate.needs_names(span)
    reqs = o.get("requires") or []
    for n in needs:
        for i, r in enumerate(reqs):
            if str(r).split("/")[0] == n:
                m = copy.deepcopy(o)
                del m["requires"][i]
                return m
    return None


MUTATIONS = [
    ("drop_obligation", m_drop_obligation),
    ("drop_obligation_and_claim", m_drop_obligation_and_claim),
    ("hollow_stub", m_hollow_stub),
    ("manufactured_citation", m_manufactured_citation),
    ("alternation_collapse", m_alternation_collapse),
    ("inert_ontology", m_inert_ontology),
    ("drop_closure", m_drop_closure),
    ("slot_mismatch", m_slot_mismatch),
    ("prefer_to_forbid", m_prefer_to_forbid),
    ("drop_needs_require", m_drop_needs_require),
]

#: What the instrumentation is EXPECTED to miss, stated before the run so a
#: surprise in either direction is visible (pre-registration in miniature).
EXPECTED_UNCAUGHT = {"drop_obligation_and_claim", "prefer_to_forbid"}


def main():
    report = json.load(open(os.path.join(HERE, "corpus_gate_report.json")))
    rows = {c["id"]: c for c in json.load(
        open(os.path.join(HERE, "node_corpus_all.json")))["clauses"]}
    known = set(rows)
    gathered = corpus_gate.gather()
    subjects = []
    for cid in sorted(report["modules"]):
        r = report["modules"][cid]
        if r["hits"]["hard"] or cid not in rows or cid not in gathered:
            continue
        o, span, _run = gathered[cid]
        if len(o.get("asserts") or []) >= 1:
            subjects.append((cid, o, span))
        if len(subjects) >= N_SUBJECTS:
            break
    print(f"subjects: {len(subjects)} hard-clean modules "
          f"({', '.join(c for c, _, _ in subjects)})")

    matrix = {}
    for mname, fn in MUTATIONS:
        applied = blocked = flagged = 0
        fired = {}
        for cid, o, span in subjects:
            base = {
                "schema": set(schema_breaches(cid, o, known)),
                "stage2": set(stage2_errors(cid, o, rows[cid], known)),
                "gate-hard": set(gate_hits(cid, o, span, "hard")),
                "gate-review": set(gate_hits(cid, o, span, "review")),
            }
            m = fn(o, span)
            if m is None:
                continue
            applied += 1
            new = {
                "schema": [b for b in schema_breaches(cid, m, known)
                           if b not in base["schema"]],
                "stage2": [e for e in stage2_errors(cid, m, rows[cid], known)
                           if e not in base["stage2"]],
                "gate-hard": [h for h in gate_hits(cid, m, span, "hard")
                              if h not in base["gate-hard"]],
                "gate-review": [h for h in gate_hits(cid, m, span, "review")
                                if h not in base["gate-review"]],
            }
            if new["schema"] or new["stage2"] or new["gate-hard"]:
                blocked += 1        # production refuses or the gate hard-fails
            elif new["gate-review"]:
                flagged += 1        # attention-tier only: visible, not blocking
            for layer, hs in new.items():
                for h in hs:
                    key = f"{layer}:{h.split(':')[0]}" if layer.startswith(
                        "gate") else layer
                    fired[key] = fired.get(key, 0) + 1
        exp = "EXPECTED-UNCAUGHT" if mname in EXPECTED_UNCAUGHT else ""
        verdict = ("BLOCKED" if applied and blocked == applied else
                   "FLAGGED" if blocked + flagged == applied and applied else
                   "PARTIAL" if blocked + flagged else
                   "UNCAUGHT")
        matrix[mname] = {"applied": applied, "blocked": blocked,
                         "flagged_only": flagged, "fired": fired,
                         "verdict": verdict,
                         "expected_uncaught": mname in EXPECTED_UNCAUGHT}
        print(f"  {mname:28s} blocked {blocked}/{applied}  flagged {flagged}"
              f"  {verdict:9s} {exp:18s} {', '.join(sorted(fired)) or '-'}")
    with open(os.path.join(HERE, "gate_mutation_report.json"), "w") as f:
        json.dump({"subjects": [c for c, _, _ in subjects],
                   "matrix": matrix}, f, indent=1, sort_keys=True)
    print("wrote gate_mutation_report.json")


if __name__ == "__main__":
    main()
