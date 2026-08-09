#!/usr/bin/env python3
"""Score the ITERATIVE definition runs — does closing a definition terminate?

THE QUESTION. The single-shot formalization run (`asp_run1..5.json`) showed
structure converging (rule counts sd 0.8) and vocabulary NOT converging
(borrowed-predicate agreement 0.06). It also showed that formalizing a concept
INTRODUCES two or three new undefined predicates. That left the question this
script exists to answer: **if you keep going — gather passages for the new
borrows, extend the definition, repeat — does it close, or does the borrow set
grow without bound?**

⭐ WHY CLOSURE IS COMPUTED HERE AND NOT READ OFF THE MODEL'S `closed` FIELD.
The prompt asks the model to declare whether its definition is self-sufficient,
and the cheapest way to satisfy that instruction is to relabel an undefined
predicate as a "primitive". `DEBUGGING_TIPS` §6: self-report is a proposer,
never a verdict. So this script derives the open set MECHANICALLY — parse every
final rule with `clingo.ast`, take the body predicates, subtract the ones that
appear as a head somewhere in the same definition — and reports the model's
claim and the computed answer side by side. A run whose `closed: true` disagrees
with the computed open set is the finding, not an error to be smoothed over.

⚠️ PRIMITIVES ARE NOT COUNTED AS CLOSED, they are counted separately. Whether
`end_user/1` is genuinely a primitive is a judgment about the document, and this
script has no standing to make it. It reports how many body predicates each run
resolved by DEFINING them versus by DECLARING them primitive, because a run that
closes mostly by declaration has answered a different question from one that
closes mostly by definition.

⛔ NO PINNED COUNTS. Every number below is measured from the run files. The
0.06 baseline is quoted from `asp_run*` in the log, not asserted here.
"""

import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PANEL = os.path.join(HERE, "resolve_runs", "panel")


# --------------------------------------------------------------------------
# verbatim checking
# --------------------------------------------------------------------------
def normalise(s):
    """⚠️ The normaliser is itself a measuring instrument and it was WRONG once.

    An earlier version reported 80% verbatim where the true rate was 100%,
    because the document carries `[^footnote]` markers and curly quotes that no
    model reproduces. Every transform here exists because it changed a measured
    number, and none of them is cosmetic.
    """
    s = re.sub(r"\[\^[^\]]*\]", "", s)            # footnote markers
    s = s.replace("**", "")                       # markdown emphasis

    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("—", "--").replace("–", "-")
    s = s.replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip().lower()


def load_document(path):
    """Return {section_id: normalised_text} plus the whole normalised document."""
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    parts = re.split(r"=====\s*SECTION:\s*(\S+)\s*=====", raw)
    secs = {}
    for i in range(1, len(parts) - 1, 2):
        secs[parts[i]] = normalise(parts[i + 1])
    return secs, normalise(raw)


# --------------------------------------------------------------------------
# ASP structure
# --------------------------------------------------------------------------
def rule_signature(asp):
    """(head, frozenset(body)) as name/arity pairs, or None if clingo refuses.

    Uses `clingo.ast` rather than a regex because the thing being counted is
    *which predicates a rule depends on*, and a regex cannot tell a predicate
    from a function term inside one.
    """
    try:
        import clingo.ast as A
    except ImportError:
        return "NO_CLINGO"
    head, body, bad = [None], set(), []

    def sig(sym):
        return f"{sym.symbol.name}/{len(sym.symbol.arguments)}"

    def walk_head(node):
        if node.ast_type == A.ASTType.Literal and \
                node.atom.ast_type == A.ASTType.SymbolicAtom:
            try:
                head[0] = sig(node.atom)
            except AttributeError:
                pass

    def walk_body(node):
        if node.ast_type == A.ASTType.Literal and \
                node.atom.ast_type == A.ASTType.SymbolicAtom:
            try:
                body.add(sig(node.atom))
            except AttributeError:
                pass

    def on(node):
        if node.ast_type == A.ASTType.Rule:
            walk_head(node.head)
            for lit in node.body:
                walk_body(lit)

    try:
        A.parse_string(asp, on, logger=lambda c, m: bad.append(m))
    except Exception as exc:                                    # noqa: BLE001
        return {"ok": False, "error": str(exc)}
    if bad:
        return {"ok": False, "error": bad[0]}
    return {"ok": True, "head": head[0], "body": body}


def closure(rules):
    """Compute the OPEN set: body predicates with no head in the definition.

    This is the check the model's own `closed` field is scored against.
    """
    parsed = [rule_signature(r.get("asp", "")) for r in rules]
    if "NO_CLINGO" in parsed:
        return None
    heads = {p["head"] for p in parsed if p.get("ok") and p.get("head")}
    bodies = set()
    for p in parsed:
        if p.get("ok"):
            bodies |= p["body"]
    return {"heads": heads, "open": bodies - heads,
            "parse_ok": sum(1 for p in parsed if p.get("ok")),
            "parse_n": len(parsed),
            "errors": [p.get("error") for p in parsed if not p.get("ok")]}


# --------------------------------------------------------------------------
def jaccard_all(sets):
    """Fraction of the union present in EVERY set. 1.0 = full agreement."""
    sets = [s for s in sets if s is not None]
    if not sets:
        return None, 0, 0
    union = set().union(*sets)
    if not union:
        return None, 0, 0
    inter = set.intersection(*sets)
    return len(inter) / len(union), len(inter), len(union)


def score(run_paths, doc_path):
    secs, whole = load_document(doc_path)
    runs = []
    for p in sorted(run_paths):
        with open(p, encoding="utf-8") as fh:
            runs.append((os.path.basename(p), json.load(fh)))

    print(f"\n{'='*74}\nITERATIVE DEFINITION — {len(runs)} runs, "
          f"document {len(secs)} sections\n{'='*74}")

    # ---- A. termination ---------------------------------------------------
    print("\nA · DID IT TERMINATE?  (model's own claim)")
    print(f"  {'run':12} {'concepts':>8} {'closed':>8} {'rounds: mean':>13} {'max':>4}")
    per_concept_rounds = {}
    for name, data in runs:
        cs = data.get("concepts", [])
        rounds = [c.get("rounds_taken") or len(c.get("rounds", [])) for c in cs]
        rounds = [r for r in rounds if r]
        closed = sum(1 for c in cs if c.get("closed"))
        mean = sum(rounds) / len(rounds) if rounds else 0
        print(f"  {name:12} {len(cs):>8} {closed:>8} {mean:>13.2f} "
              f"{max(rounds) if rounds else 0:>4}")
        for c in cs:
            per_concept_rounds.setdefault(c.get("predicate"), []).append(
                c.get("rounds_taken") or len(c.get("rounds", [])))

    print("\n  rounds needed, per concept, across runs:")
    for pred, rs in sorted(per_concept_rounds.items(),
                           key=lambda kv: -sum(kv[1]) / max(1, len(kv[1]))):
        print(f"     {pred:42} {rs}")

    # ---- B. does the borrow set GROW? ------------------------------------
    print("\nB · ⭐ DID THE BORROW SET GROW BETWEEN ROUNDS?")
    print("     (the whole question: gathering more to close a definition may")
    print("      open more than it closes)")
    grew = shrank = flat = 0
    growth_cases = []
    for name, data in runs:
        for c in data.get("concepts", []):
            seq = [len(r.get("still_undefined", []) or [])
                   for r in c.get("rounds", [])]
            if len(seq) < 2:
                continue
            for i in range(len(seq) - 1):
                if seq[i + 1] > seq[i]:
                    grew += 1
                elif seq[i + 1] < seq[i]:
                    shrank += 1
                else:
                    flat += 1
            if seq[-1] > seq[0]:
                growth_cases.append((name, c.get("predicate"), seq))
        seq_by_run = {}
        for c in data.get("concepts", []):
            s = [len(r.get("still_undefined", []) or [])
                 for r in c.get("rounds", [])]
            if len(s) > 1:
                seq_by_run[c.get("predicate")] = s
        g = sum(1 for s in seq_by_run.values()
                for i in range(len(s) - 1) if s[i + 1] > s[i])
        k = sum(1 for s in seq_by_run.values()
                for i in range(len(s) - 1) if s[i + 1] < s[i])
        print(f"     {name:16} grew {g:>2} · shrank {k:>2}  "
              f"(over {len(seq_by_run)} multi-round concepts)")
    tot = grew + shrank + flat
    if tot:
        print(f"  round-to-round transitions: n={tot}  "
              f"grew {grew} · shrank {shrank} · flat {flat}")
    else:
        print("  ⚠️  no concept ran more than one round — nothing to compare")
    if growth_cases:
        print(f"  ⛔ {len(growth_cases)} concept-runs ended with MORE open than "
              f"they started:")
        for n, p, s in growth_cases:
            print(f"     {n:12} {p:38} {s}")
    else:
        print("  no concept-run ended with more open than it started")

    # ---- C. verbatim ------------------------------------------------------
    print("\nC · ARE THE PASSAGES REAL?  (verbatim, after normalising)")
    ok = bad = wrong_sec = 0
    for name, data in runs:
        for c in data.get("concepts", []):
            for r in c.get("rounds", []):
                for ex in r.get("passages", []) or []:
                    t = normalise(ex.get("excerpt", ""))
                    if not t:
                        continue
                    sid = ex.get("section_id")
                    if sid in secs and t in secs[sid]:
                        ok += 1
                    elif t in whole:
                        wrong_sec += 1
                    else:
                        bad += 1
    n = ok + bad + wrong_sec
    if n:
        print(f"  n={n}   in the section named: {ok} ({ok/n:.0%})   "
              f"elsewhere in document: {wrong_sec}   not found: {bad}")

    # ---- D. does the ASP parse, and does it actually close? --------------
    print("\nD · ⭐ MODEL'S `closed` CLAIM vs COMPUTED CLOSURE")
    print("     computed = body predicates with no head in the same definition")
    print(f"  {'run':12} {'concept':38} {'says':>6} {'parse':>7} {'open(computed)':>15}")
    agree = disagree = 0
    per_concept_open = {}
    all_parse_ok = all_parse_n = 0
    for name, data in runs:
        for c in data.get("concepts", []):
            rules = c.get("final_definition") or []
            cl = closure(rules)
            if cl is None:
                print("  ⚠️  clingo unavailable — D and G cannot run")
                return 2
            all_parse_ok += cl["parse_ok"]
            all_parse_n += cl["parse_n"]
            declared = {p.get("predicate") for p in c.get("primitives", []) or []}
            unexplained = {o for o in cl["open"]
                           if o.split("/")[0] not in
                           {d.split("/")[0] for d in declared if d}}
            says = "closed" if c.get("closed") else "OPEN"
            mark = ""
            if c.get("closed") and unexplained:
                disagree += 1
                mark = "  ⛔ claims closed"
            else:
                agree += 1
            print(f"  {name:12} {str(c.get('predicate')):38} {says:>6} "
                  f"{cl['parse_ok']}/{cl['parse_n']:<5} "
                  f"{len(cl['open']):>3} ({len(unexplained)} undeclared){mark}")
            per_concept_open.setdefault(c.get("predicate"), []).append(cl["open"])
    if all_parse_n:
        print(f"\n  clingo accepts {all_parse_ok}/{all_parse_n} "
              f"({all_parse_ok/all_parse_n:.0%}) of final rules")
    print(f"  claim matches computed closure: {agree}   "
          f"claims closed but is not: {disagree}")

    # ---- E. vocabulary agreement -----------------------------------------
    print("\nE · ⭐ DOES ITERATING MAKE THE VOCABULARY CONVERGE?")
    print("     single-shot baseline was 0.06 (asp_run1..5, borrowed predicates)")
    # ⚠️ `empty` IS LOAD-BEARING AND ITS ABSENCE MADE THIS TABLE LIE. Jaccard
    # over open-sets scores a concept 0.00 when four runs closed it cleanly
    # (open set empty) and one did not — intersection empty, union 1. That
    # reads as total disagreement and is very nearly the opposite. The count of
    # runs with NOTHING open has to sit beside the agreement figure, or the
    # figure cannot be read. `DEBUGGING_TIPS` §2: print the denominator.
    print(f"  {'concept':38} {'agreement':>10} {'in all':>7} {'union':>6} "
          f"{'runs w/ 0 open':>14}")
    for pred, opens in sorted(per_concept_open.items()):
        a, i, u = jaccard_all(opens)
        empty = sum(1 for o in opens if not o)
        print(f"  {str(pred):38} "
              f"{('n/a' if a is None else f'{a:.2f}'):>10} {i:>7} {u:>6} "
              f"{empty:>9}/{len(opens)}")
    heads_per_run = []
    for name, data in runs:
        h = set()
        for c in data.get("concepts", []):
            cl = closure(c.get("final_definition") or [])
            if cl:
                h |= cl["heads"]
        heads_per_run.append(h)
    a, i, u = jaccard_all(heads_per_run)
    print(f"\n  ⭐ DEFINED (head) vocabulary across whole runs: "
          f"agreement {('n/a' if a is None else f'{a:.2f}')}  "
          f"in all 5: {i}  union: {u}")
    if u:
        inall = set.intersection(*[h for h in heads_per_run if h])
        print(f"     shared by every run: {sorted(inall)}")

    # ---- F. section attribution ------------------------------------------
    print("\nF · DO THE RUNS AGREE ON WHICH SECTIONS CONTRIBUTE?")
    print(f"  {'concept':38} {'agreement':>10} {'in all':>7} {'union':>6}")
    by_concept = {}
    for name, data in runs:
        for c in data.get("concepts", []):
            s = {r.get("from_section") for r in c.get("final_definition") or []}
            s |= {p.get("section_id") for rd in c.get("rounds", [])
                  for p in rd.get("passages", []) or []}
            by_concept.setdefault(c.get("predicate"), []).append(s - {None})
    for pred, sets in sorted(by_concept.items()):
        a, i, u = jaccard_all(sets)
        print(f"  {str(pred):38} "
              f"{('n/a' if a is None else f'{a:.2f}'):>10} {i:>7} {u:>6}")

    # ---- G. consolidation -------------------------------------------------
    print("\nG · CONSOLIDATION — which rules do the runs actually share?")
    print("     matched on (head, body-predicate set), NOT on text")
    for pred in sorted(by_concept):
        counts = {}
        for name, data in runs:
            seen = set()
            for c in data.get("concepts", []):
                if c.get("predicate") != pred:
                    continue
                for r in c.get("final_definition") or []:
                    sg = rule_signature(r.get("asp", ""))
                    if isinstance(sg, dict) and sg.get("ok") and sg.get("head"):
                        seen.add((sg["head"], frozenset(sg["body"])))
            for k in seen:
                counts[k] = counts.get(k, 0) + 1
        shared = {k: v for k, v in counts.items() if v >= 3}
        print(f"\n  {pred}   {len(counts)} distinct rule shapes, "
              f"{len(shared)} in >=3 of {len(runs)} runs")
        for (h, b), v in sorted(shared.items(), key=lambda kv: -kv[1]):
            print(f"     [{v}/{len(runs)}] {h} :- {', '.join(sorted(b)) or 'true'}")
    print()
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    # ⚠️ `iter_run*.json` is TOO BROAD — the run agents write intermediate
    # scratch files beside their output (`iter_run2_base.json`,
    # `iter_run4_temp.json` were both picked up and scored as if they were
    # runs). Match only the five final files.
    p.add_argument("--runs", default=os.path.join(PANEL, "iter_run[1-5].json"))
    p.add_argument("--document", default=os.path.join(PANEL, "DOCUMENT.txt"))
    a = p.parse_args(argv)
    paths = sorted(glob.glob(a.runs))
    if not paths:
        # ⛔ DEBUGGING_TIPS §8: a check that cannot run must not exit like one
        # that passed. Two agents have already reported "exits 0" from a
        # harness that never ran.
        print(f"⛔ no run files matched {a.runs} — nothing measured", file=sys.stderr)
        return 2
    return score(paths, a.document)


if __name__ == "__main__":
    raise SystemExit(main())
