"""Link-check a clause translation: is it MISSING A REFERENCE?

The question this answers, with no reasoning capability at all:

    "This clause's translation uses a predicate. Does anything define it?
     If not, which clause should have?"

TWO LAYERS, both mechanical.

  L1  ANCHOR GRAPH (free, high precision, incomplete). The spec's own text
      carries its cross-references as markdown anchors -- `[restricted](#restricted_content)`
      -- and `section_id` values match those anchors. 45 of 46 distinct targets
      in the corpus resolve. So the referenced sections are readable straight
      off the source with a regex. Only ~13% of clauses carry anchors, so this
      is a LOWER BOUND on dependencies, never the whole set.

  L2  UNRESOLVED PREDICATES (mechanical, complete for what the code uses).
      clingo already emits `info: atom does not occur in any rule head: p/n`.
      That IS the missing-reference detector. It needs one thing to become
      useful: a way to tell a genuine SITUATION INPUT (`forbids`, `produced` --
      facts about the case being judged) from an unresolved reference to
      another clause. Each file declares its inputs in a `%% inputs:` header;
      anything head-less and not declared is an unresolved reference.

      ⭐ This is the check that was already firing and being ignored.
      `lifted_by_purpose/2` sat in a constraint body with no provider, making
      that constraint dead, and clingo said so on every single run.

Usage:
    python3 link.py <clause.lp> [more.lp ...]        # link-check
    python3 link.py --suggest m0255                  # what does the anchor graph say?
"""

import os
import re
import subprocess
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
EXP = os.path.join(REPO, "semi-formal-experiment")
PY = os.path.join(EXP, ".venv", "bin", "python")
CLAUSES_JSON = os.path.join(EXP, "modelspec_clauses.json")

ANCHOR = re.compile(r"\]\(#([a-zA-Z0-9_\-]+)\)")
FORBID = re.compile(r"^%%\s*forbid-body\s*:\s*(\w+)\s*<-\s*(\w+)\s*$", re.M)
RULE = re.compile(r"^\s*([a-z_]\w*)\s*\([^)]*\)\s*:-(.*?)\.\s*$", re.M | re.S)
NO_HEAD = re.compile(r"atom does not occur in any rule head:\s*\n?\s*([a-z_][A-Za-z0-9_]*)")
HDR = re.compile(r"^%%\s*(provides|inputs|clause|section)\s*:\s*(.*)$", re.M)


def load_clauses():
    d = json.load(open(CLAUSES_JSON, encoding="utf-8"))
    rows = d if isinstance(d, list) else d["clauses"]
    return {r["id"]: r for r in rows}


def header(path):
    """`%% provides: p/2, q/1` -> {'provides': {'p','q'}, ...}"""
    txt = open(path, encoding="utf-8").read()
    out = {}
    for key, val in HDR.findall(txt):
        if key in ("provides", "inputs"):
            out[key] = {t.split("/")[0].strip()
                        for t in val.split(",") if t.strip()}
        else:
            out[key] = val.strip()
    return out


def suggest(clause_id):
    """L1: which sections does this clause's own TEXT point at?"""
    rows = load_clauses()
    r = rows.get(clause_id)
    if not r:
        print(f"no such clause: {clause_id}")
        return 1
    targets = sorted(set(ANCHOR.findall(r["quote"])))
    secs = {}
    for c in rows.values():
        secs.setdefault(c["section_id"], []).append(c["id"])
    print(f"{clause_id}  [section: {r['section_id']}]")
    print(f"  text: {r['quote'][:150]}...")
    if not targets:
        print("  L1: no anchor references in the text "
              "(does NOT mean no dependencies -- see L2)")
        return 0
    print(f"  L1: {len(targets)} anchor reference(s):")
    for t in targets:
        ids = secs.get(t)
        print(f"    #{t:28} -> " +
              (f"section exists, {len(ids)} clauses: {', '.join(ids[:8])}"
               if ids else "⛔ UNRESOLVED: no section with this id"))
    return 0


def link(paths):
    declared_inputs, provided = set(), set()
    for p in paths:
        h = header(p)
        declared_inputs |= h.get("inputs", set())
        provided |= h.get("provides", set())
        if "provides" not in h:
            print(f"⚠️  {os.path.basename(p)}: no `%% provides:` header — "
                  f"cannot tell its interface from its internals")

    # L3: static rule-shape checks. Some document claims are about the RULE
    # SET ("purpose never lifts"), not about any world state. No probe case can
    # exhibit them; they are verified by inspecting the program.
    shape_fails = []
    for p in paths:
        txt = open(p, encoding="utf-8").read()
        for head, banned in FORBID.findall(txt):
            for h, body in RULE.findall(txt):
                if h == head and re.search(r"\b%s\b" % banned, body):
                    shape_fails.append(
                        f"{os.path.basename(p)}: rule deriving `{head}` mentions "
                        f"`{banned}` in its body, which %% forbid-body bans")

    r = subprocess.run([PY, "-m", "clingo"] + paths + ["--outf=3"],
                       capture_output=True, text=True, cwd=EXP)
    blob = r.stdout + r.stderr
    headless = set(NO_HEAD.findall(blob))
    unresolved = sorted(headless - declared_inputs)
    inputs_seen = sorted(headless & declared_inputs)

    print(f"linked {len(paths)} file(s): "
          f"{', '.join(os.path.basename(p) for p in paths)}")
    if inputs_seen:
        print(f"  situation inputs (expected head-less): {', '.join(inputs_seen)}")
    if shape_fails:
        print(f"  ⛔ {len(shape_fails)} RULE-SHAPE violation(s):")
        for f in shape_fails:
            print(f"      {f}")
    if not unresolved:
        print("  ✅ no unresolved references")
        return 1 if shape_fails else 0
    print(f"  ⛔ {len(unresolved)} UNRESOLVED REFERENCE(S) — "
          f"used in a body, defined nowhere, and not declared as an input:")
    for u in unresolved:
        print(f"      {u}")
    print("\n  Each one is either (a) a missing `%% inputs:` declaration, or")
    print("  (b) a clause this translation depends on and does not include.")
    print("  A constraint whose body holds an unresolved atom is DEAD: it can never fire.")
    return 1


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        raise SystemExit(2)
    if a[0] == "--suggest":
        raise SystemExit(suggest(a[1]))
    raise SystemExit(link([os.path.abspath(x) for x in a]))
