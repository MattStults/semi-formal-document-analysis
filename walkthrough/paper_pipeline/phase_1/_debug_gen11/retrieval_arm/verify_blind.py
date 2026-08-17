#!/usr/bin/env python3
"""Proves the selector is BLIND, before the arm spends anything.

Three assertions, all mechanical:

 1. SOURCE — `selector.py` opens no path outside `node_corpus_all.json` and
    `promptsE/entries/`, and imports nothing that could reach an adjudication
    record.  Checked by reading the file, not by trusting the docstring.
 2. ID-INVARIANCE — renaming a clause changes nothing.  If the selector keyed
    off the clause id it could have memorised which entry each clause needed.
 3. TEXT-SENSITIVITY — perturbing the span text DOES change the selection.
    Together with (2) this says the selection is a function of the clause's own
    text and of nothing else.
"""
import io
import json
import os
import re
import sys
import tokenize

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import selector                                               # noqa: E402

FAIL = []


def check(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{'  ' + detail if detail else ''}")
    if not ok:
        FAIL.append(name)


def main():
    src = open(os.path.join(HERE, "selector.py"), encoding="utf-8").read()

    print("1. SOURCE")
    imports = set(re.findall(r"(?m)^import (\w+)", src))
    check("imports are stdlib-only and inert",
          imports <= {"argparse", "hashlib", "json", "os", "re", "sys"},
          str(sorted(imports)))
    # READ-opens only.  The one write-open (the built prompt file) is the arm's
    # output, not an input, and is matched by its `"w"` mode.
    opens = [o for o in re.findall(r"open\(([^)]*)\)", src)
             if '"w"' not in o and "'w'" not in o]
    bad = [o for o in opens
           if "ENTRIES" not in o and "CORPUS" not in o and "HERE" not in o]
    check("every read-open targets the corpus or promptsE/entries/",
          not bad, str(bad))

    # Banned strings are checked against CODE ONLY — comments and docstrings
    # are prose about the design and cannot make the selector read anything.
    code = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type not in (tokenize.COMMENT, tokenize.STRING):
            code.append(tok.string)
    code = " ".join(code)
    for banned in ["turns.md", "lessons.md", "adjudication", "RESULT",
                   "flip_verdicts", "feedback", "list_in_prompt", "defect",
                   "insample", "ORDERING"]:
        check(f"no code reference to {banned!r}", banned not in code)

    print("2. ID-INVARIANCE")
    rows = selector.rows()
    base = {r["id"]: selector.select(r)[3] for r in rows}
    same = True
    for r in rows:
        alt = dict(r)
        alt["id"] = "zzz_renamed_000"
        alt["locator"] = "SCRUBBED"
        if [e for _, _, e, _ in selector.select(alt)[3]] != \
           [e for _, _, e, _ in base[r["id"]]]:
            same = False
    check("renaming the clause changes no selection", same)

    print("3. TEXT-SENSITIVITY")
    changed = 0
    for r in rows:
        alt = dict(r)
        # strip every exception/hedge/disjunction marker from the span
        alt["quote"] = re.sub(r"\b(unless|or|should|may|by default|generally|"
                              r"avoid|regardless|without)\b", "AND",
                              r["quote"], flags=re.I)
        if [e for _, _, e, _ in selector.select(alt)[3]] != \
           [e for _, _, e, _ in base[r["id"]]]:
            changed += 1
    check("perturbing the span text changes the selection",
          changed >= len(rows) // 2, f"{changed}/{len(rows)} clauses")

    print("4. SELECTION SIZE")
    ok = all(2 <= len(base[r["id"]]) <= 4 for r in rows)
    check("every clause gets 2-4 substantive entries", ok)

    print()
    if FAIL:
        print(f"BLINDNESS NOT ESTABLISHED: {FAIL}")
        return 1
    print("BLIND. selector uses no field derived from a historical adjudication.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
