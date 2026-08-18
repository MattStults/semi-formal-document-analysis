#!/usr/bin/env python3
"""Mechanical validation of a BEHAVIOR module against the corpus vocabulary
contract (node_behavior_contract.md / behavior_vocab.json) — the behavior-side
twin of schema.validate_all. Matt's ruling 2026-08-18: behaviors are
translated INTO the document's vocabulary; an invented predicate is a BREACH
(BEHAVIOR_TRANSLATION_FAILURES.md B5), not a style note.

Checks (each a QUESTION a later reader can apply without judgment):
  V1  every predicate in `module.situation` is a seam name or a declared
      corpus input, at its declared arity
  V2  every head in `module.does` is a canonical act (provisional list) —
      bespoke corpus acts are reached through bridges, never named directly
  V3  every atom id in `structure` exists in `atoms`, and every atom is used
      by some branch (no orphan atoms)
  V4  conditions/guards are seam or input predicates (not coined)
  V5  the module's rules parse and ground under clingo (unsafe variables,
      syntax) — the same 'a check that cannot run must not look like a pass'
      discipline as the spec side
Tier: all hard. Output: breaches, or "0 breaches".

Usage: .../.venv/bin/python validate_behavior_module.py modules_tuned_r2.json [--slug S]
"""
import json, re, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
VOCAB = json.load(open(os.path.join(HERE, "behavior_vocab.json")))
CANON = set(VOCAB["canonical_acts_provisional"])
SEAM = {n: s["arity"] for n, s in VOCAB["seam"].items()}
INPUTS = {}
for s in VOCAB["inputs"]:
    n, _, a = s.partition("/")
    INPUTS[n] = int(a) if a.isdigit() else None
_ATOM = re.compile(r"(-?)([a-z_][A-Za-z0-9_]*)\s*\(([^()]*)\)")


def preds(expr):
    for neg, name, args in _ATOM.findall(expr or ""):
        yield name, len([a for a in args.split(",") if a.strip()])


def validate(mod):
    br = []
    ids = {a["id"] for a in mod.get("atoms", [])}
    used = set()
    for b in (mod.get("structure") or {}).get("branches", []):
        for a in b.get("atoms", []):
            used.add(a)
            if a not in ids: br.append(f"V3 structure references unknown atom `{a}`")
    for a in ids - used: br.append(f"V3 atom `{a}` used by no branch")
    for f in (mod.get("module") or {}).get("situation", []):
        for n, ar in preds(f):
            if n in SEAM:
                if SEAM[n] != ar: br.append(f"V1 `{n}` used at arity {ar}, seam pins /{SEAM[n]}")
            elif n in INPUTS:
                if INPUTS[n] not in (None, ar): br.append(f"V1 `{n}` used at arity {ar}, corpus declares /{INPUTS[n]}")
            else: br.append(f"V1 situation predicate `{n}` is neither a seam name nor a declared corpus input (B5)")
    # internal derived predicates: heads the module itself defines (branch ids, `violates`, atom ids used as
    # derived heads) are legitimate — like a spec module's own ontology heads. What must be canonical is the
    # ACT the behavior PERFORMS against the corpus: heads whose name is an atom of kind "act" or that appear
    # in `does` as performed acts. Coined = neither seam, input, canonical act, atom/branch/derived id.
    branch_ids = {b["id"] for b in (mod.get("structure") or {}).get("branches", [])}
    derived = set(branch_ids) | {"violates"}
    rules = (mod.get("module") or {}).get("does", [])
    for r in rules:
        hp = list(preds(r.split(":-")[0]))
        if hp: derived.add(hp[0][0])
    act_atoms = {a["id"] for a in mod.get("atoms", []) if a.get("kind") == "act"}
    for r in rules:
        head = r.split(":-")[0].strip()
        hp = list(preds(head))
        if not hp: br.append(f"V2 does-rule has no parsable head: `{r[:60]}`"); continue
        n, ar = hp[0]
        if n in act_atoms and n not in CANON:
            br.append(f"V2 performed act `{n}` is not a canonical act — bespoke corpus acts are reached via bridges; behaviors perform canonical acts (B5)")
        for n2, ar2 in list(preds(r))[1:]:
            if n2 not in SEAM and n2 not in INPUTS and n2 not in ids and n2 not in CANON and n2 not in derived:
                br.append(f"V4 body predicate `{n2}` in `{r[:50]}…` is coined (B5)")
    for c in mod.get("conditions", []):
        n = c["id"]
        if n not in SEAM and n not in INPUTS: br.append(f"V4 condition `{n}` is neither seam nor declared input (B5)")
    try:
        import clingo
        prog = "\n".join((x if x.rstrip().endswith(".") else x + ".") for x in (mod.get("module") or {}).get("does", []))
        prog += "\n" + "\n".join((x if x.rstrip().endswith(".") else x + ".") for x in (mod.get("module") or {}).get("situation", []))
        ctl = clingo.Control(["--warn=none"]); ctl.add("base", [], prog); ctl.ground([("base", [])])
    except Exception as ex:
        br.append(f"V5 clingo: {str(ex).splitlines()[0][:120]}")
    return br


if __name__ == "__main__":
    path = sys.argv[1]; slug = sys.argv[sys.argv.index("--slug") + 1] if "--slug" in sys.argv else None
    d = json.load(open(path)); mods = d.get("modules", {})
    rc = 0
    for s, m in mods.items():
        if slug and s != slug: continue
        if "structure" not in m: print(f"{s}: (atom list, not a module — skipped)"); continue
        b = validate(m)
        print(f"{s}: {len(b)} breaches"); rc |= bool(b)
        for x in b: print("   ", x)
    sys.exit(rc)
