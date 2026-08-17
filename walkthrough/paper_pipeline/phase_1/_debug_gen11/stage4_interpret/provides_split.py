#!/usr/bin/env python3
"""JOB 1 — the PROVIDES-aware split of seat 4c's 264 `unlicensed` verdicts.

Free. No model call. Pure re-analysis of artifacts already on disk:

  * the stored 4c replies  `_debug_gen11/stage4_baseline/out/raw/*.4c.json`
  * the judged modules     `resolve_runs/graph_v2/translation_sample/runs/<run>/*.json`
  * the decomposition graph `resolve_runs/graph_v2/runs/ds7/root_graph.production.json`

Decision rule is `PREREG.md` §JOB 1 and is not changed here.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN11 = os.path.dirname(HERE)
PHASE1 = os.path.dirname(GEN11)
sys.path.insert(0, PHASE1)

BASE = os.path.join(GEN11, "stage4_baseline", "out")
RUN = os.path.join(PHASE1, "resolve_runs", "graph_v2", "translation_sample",
                   "runs", "20260815-130831-together-deepseek-v4-flash")
GRAPH = os.path.join(PHASE1, "resolve_runs", "graph_v2", "runs", "ds7",
                     "root_graph.production.json")

FUNCTOR = re.compile(r"\b([a-z_][A-Za-z0-9_]*)\s*\(")
WORD = re.compile(r"[a-z0-9]+")


def norm_id(nid):
    return nid.replace("-", "_").lower()


def functors(text):
    return set(FUNCTOR.findall(text or ""))


def words(s):
    return set(WORD.findall((s or "").lower()))


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ---------------------------------------------------------------- graph side
graph = json.load(open(GRAPH, encoding="utf-8"))
gnodes = {norm_id(n["id"]): n for n in graph["nodes"]}
needs_of = {k: {d["name"]: d.get("prose", "") for d in n.get("needs") or []}
            for k, n in gnodes.items()}
providers_of = {}
for k, n in gnodes.items():
    for d in n.get("provides") or []:
        providers_of.setdefault(d["name"], set()).add(k)

# --------------------------------------------------------------- module side
modules = {}
for f in sorted(os.listdir(RUN)):
    if (not f.endswith(".json") or f in ("run.json", "concepts.json")
            or f.endswith((".transcript.json", ".version.json"))):
        continue
    obj = json.load(open(os.path.join(RUN, f), encoding="utf-8"))
    if obj.get("outcome") == "translated":
        modules[norm_id(obj["clause_id"])] = obj
IN_RUN = set(modules)

# ------------------------------------------------------- join soundness gate
have_needs = [k for k in modules if needs_of.get(k)]
joined = [k for k in have_needs
          if {c["name"] for c in modules[k]["concepts"]} & set(needs_of[k])]
join_rate = len(joined) / len(have_needs) if have_needs else 0.0


def item_names(mod, iid):
    """Predicate names at stake in one 4c item id, from the module JSON."""
    kind, idx = iid[:-1].split("[")
    item = mod[kind][int(idx)]
    if kind == "concepts":
        return {item["name"]}
    if kind == "ontology":
        return functors(item.get("atom", "")) | functors(item.get("body", ""))
    if kind == "asserts":
        names = functors(item.get("body", ""))
        act = (item.get("act") or "").strip()
        names |= functors(act) or ({act} if re.fullmatch(
            r"[a-z_][A-Za-z0-9_]*", act) else set())
        return names
    return set()          # defines / beats: no predicate name at stake


rows = []
parse_fail = []
SEAT_SUFFIX = (".4c.json", ".4b.json")
for f in sorted(os.listdir(os.path.join(BASE, "raw"))):
    if not f.endswith(SEAT_SUFFIX):
        continue
    seat = f[-7:-5]
    rec = json.load(open(os.path.join(BASE, "raw", f), encoding="utf-8"))
    cid = norm_id(rec["tag"].split(".")[0])
    mod = modules[cid]
    own = {c["name"] for c in mod["concepts"]}
    try:
        reply = json.loads(rec["text"])
    except Exception:                                         # noqa: BLE001
        m = re.search(r"\{.*\}", rec["text"], re.S)
        if not m:
            parse_fail.append(cid)
            continue
        reply = json.loads(m.group(0))
    for j in reply["judgements"]:
        iid = j["item"]
        try:
            names = item_names(mod, iid)
        except Exception:                                     # noqa: BLE001
            names = set()
        needs = needs_of.get(cid, {})
        # a name is BORROWED-eligible iff the graph told this node it is
        # established elsewhere (B1) and some OTHER node provides it (B2)
        borrowed = {n for n in names
                    if n in needs
                    and (providers_of.get(n, set()) - {cid})}
        unresolved = names - borrowed
        strict = all((providers_of.get(n, set()) - {cid}) & IN_RUN
                     for n in borrowed) if borrowed else False
        rows.append({
            "seat": seat,
            "clause": cid, "item": iid, "kind": iid.split("[")[0],
            "verdict": j["verdict"], "names": sorted(names),
            "borrowed_names": sorted(borrowed),
            "unresolved_names": sorted(unresolved),
            "provider_in_run": strict,
            "reason": j.get("reason", "")[:400],
        })

# ------------------------------------------------------------- classify
DEFECT = {"4c": "unlicensed", "4b": "unfaithful"}


def classify(r, mod_own):
    if r["verdict"] != DEFECT[r["seat"]]:
        return None
    if not r["borrowed_names"]:
        return "UNLICENSED-REAL"
    # mixed item: any name that is neither borrowed nor declared by this
    # node's own concept rows keeps the verdict real
    if r["kind"] in ("ontology", "asserts"):
        leftover = [n for n in r["unresolved_names"] if n not in mod_own]
        if leftover:
            return "UNLICENSED-REAL"
    return ("BORROWED-STRICT" if r["provider_in_run"]
            else "BORROWED-DANGLING")


for r in rows:
    mod_own = {c["name"] for c in modules[r["clause"]]["concepts"]}
    r["klass"] = classify(r, mod_own)

# gloss fidelity for borrowed concept rows
for r in rows:
    r["gloss_fidelity"] = None
    if r["klass"] not in ("BORROWED-STRICT", "BORROWED-DANGLING"):
        continue
    if r["kind"] != "concepts":
        r["gloss_fidelity"] = "n/a"
        continue
    name = r["names"][0]
    idx = int(r["item"][:-1].split("[")[1])
    gloss = modules[r["clause"]]["concepts"][idx]["gloss"]
    prose = needs_of[r["clause"]].get(name, "")
    a, b = words(gloss), words(prose)
    if a == b:
        r["gloss_fidelity"] = "exact"
    elif jaccard(a, b) >= 0.6:
        r["gloss_fidelity"] = "high-overlap"
    else:
        r["gloss_fidelity"] = "drifted"
    r["jaccard"] = round(jaccard(a, b), 3)

json.dump(rows, open(os.path.join(HERE, "job1_4c_rows.json"), "w",
                     encoding="utf-8"), indent=1)

# ------------------------------------------------------------------ report
import collections
rows4c = [r for r in rows if r["seat"] == "4c"]
rows4b = [r for r in rows if r["seat"] == "4b"]
tot = collections.Counter(r["verdict"] for r in rows4c)
un = [r for r in rows4c if r["verdict"] == "unlicensed"]
by = collections.Counter(r["klass"] for r in un)
fid = collections.Counter(r["gloss_fidelity"] for r in un if r["klass"] and
                          r["klass"].startswith("BORROWED"))
kinds = collections.Counter((r["kind"], r["klass"]) for r in un)

print(f"join soundness: {len(joined)}/{len(have_needs)} modules with a "
      f"non-empty graph `needs` have >=1 concept row matching a needs name "
      f"= {join_rate:.1%}  (gate: >=60%)")
print(f"parse failures: {parse_fail}")
print(f"\n4c judgements: {sum(tot.values())}  {dict(tot)}")
print(f"\nunlicensed = {len(un)}")
for k, v in by.most_common():
    print(f"  {k:22s} {v}")
print(f"\nborrowed gloss fidelity: {dict(fid)}")
print("\nby item kind:")
for (k, c), v in sorted(kinds.items()):
    print(f"  {k:10s} {str(c):22s} {v}")

drift = [r for r in un if r["gloss_fidelity"] == "drifted"]
borrowed_ok = [r for r in un if r["klass"] and r["klass"].startswith("BORROWED")
               and r["gloss_fidelity"] != "drifted"]
real = [r for r in un if r["klass"] == "UNLICENSED-REAL"]
print(f"\nCORRECTED 4c: real unlicensed = {len(real)} + drifted-borrowed "
      f"{len(drift)} = {len(real) + len(drift)}  "
      f"(exonerated {len(borrowed_ok)} of {len(un)})")

# ------------------------------------------- clause-level corrected headline
reports = {}
for p in sorted(os.listdir(os.path.join(BASE, "reports"))):
    rep = json.load(open(os.path.join(BASE, "reports", p), encoding="utf-8"))
    reports[norm_id(rep["clause_id"])] = rep

real_ids = {(r["clause"], r["item"]) for r in real + drift}
head = {}
for cid, rep in reports.items():
    seats_ = rep.get("seats", {})
    b = [j for j in seats_.get("4b", []) if j["verdict"] == "unfaithful"]
    d = [j for j in seats_.get("4d", []) if j["verdict"] == "not-conveyed"]
    c_all = [r for r in rows4c
             if r["clause"] == cid and r["verdict"] == "unlicensed"]
    c_real = [r for r in c_all if (r["clause"], r["item"]) in real_ids]
    head[cid] = {"4b": len(b), "4d": len(d),
                 "4c_raw": len(c_all), "4c_real": len(c_real)}

raw_def = sum(1 for v in head.values() if v["4b"] or v["4d"] or v["4c_raw"])
cor_def = sum(1 for v in head.values() if v["4b"] or v["4d"] or v["4c_real"])
only_c_raw = sum(1 for v in head.values()
                 if v["4c_raw"] and not (v["4b"] or v["4d"]))
only_c_real = sum(1 for v in head.values()
                  if v["4c_real"] and not (v["4b"] or v["4d"]))
n = len(head)
print(f"\nclause-level over n={n}")
print(f"  raw       : {raw_def} defective / {n - raw_def} clean")
print(f"  CORRECTED : {cor_def} defective / {n - cor_def} clean")
print(f"  clauses whose ONLY defect was 4c: raw {only_c_raw} -> "
      f"corrected {only_c_real}")
json.dump(head, open(os.path.join(HERE, "job1_clause_headline.json"), "w"),
          indent=1, sort_keys=True)

# ---------------------------------------------------- SECONDARY (post-hoc):
# the identical check applied to 4b's `unfaithful`. NOT pre-registered; the
# rule is the same deterministic one, applied to a second seat, and is
# reported separately for exactly that reason.
unf = [r for r in rows4b if r["verdict"] == "unfaithful"]
by_b = collections.Counter(r["klass"] for r in unf)
fid_b = collections.Counter(r["gloss_fidelity"] for r in unf
                            if r["klass"] and r["klass"].startswith("BORROWED"))
print(f"\n[secondary, post-hoc] 4b judgements {len(rows4b)}, "
      f"unfaithful {len(unf)}: {dict(by_b)}  fidelity {dict(fid_b)}")
b_real_ids = {(r["clause"], r["item"]) for r in unf
              if r["klass"] == "UNLICENSED-REAL"
              or r["gloss_fidelity"] == "drifted"}
both = sum(1 for cid, v in head.items()
           if v["4d"] or v["4c_real"]
           or any(k[0] == cid for k in b_real_ids))
print(f"[secondary] corrected on BOTH 4b and 4c: {both} defective / "
      f"{n - both} clean of {n}")
