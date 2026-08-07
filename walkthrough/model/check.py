"""Run the formal model of the pipeline, and prove its rules actually fire.

    python3 check.py              # report findings
    python3 check.py --self-test  # prove each rule rejects a deliberately broken model

WHAT THIS IS. `pipeline.lp` is a hand-authored model of the design in
`resources/03_pipeline.md`: its problems, stages, checks, seats, and which check
claims to catch which problem. `rules.lp` turns the design's own claims about
itself into constraints. A finding means the design contradicts itself or has a
hole nobody noticed.

WHAT IT CANNOT DO. It cannot tell whether a `catches` claim is TRUE. If the model
says the citation checker catches invented entities and it does not, the model
confirms coverage and is wrong. Mutation testing is the complement, not a
redundancy — one checks that the design is consistent, the other that the checks
actually work.
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WALK = os.path.dirname(HERE)
PY = os.path.join(WALK, "..", "semi-formal-experiment", ".venv", "bin", "python")
PY = PY if os.path.exists(PY) else sys.executable
FACTS = os.path.join(HERE, "pipeline.lp")
RULES = os.path.join(HERE, "rules.lp")

FINDING = re.compile(r"finding\(([a-z_]+),([^,)]+)[,)]")
LABEL = re.compile(r'label\(([a-z0-9_]+),"([^"]*)"\)')

#: Findings sort into three kinds, and they want different reactions.
#: GAP      — something is missing; fix it or waive it with a reason.
#: DISCLOSURE — true and known; it clears with more evidence, not with work.
#: CONTRADICTION — the design says two incompatible things; must be resolved.
CLASS = {
    "uncaught_problem":         ("GAP",           "add a check, or accept the problem is unhandled"),
    "contamination":            ("CONTRADICTION", "a seat can reach forbidden material — break the path"),
    "check_no_stage":           ("CONTRADICTION", "the check refers to a stage that does not exist"),
    "claim_n_is_one":           ("DISCLOSURE",    "clears when a second observation exists"),
    "unaccounted_check":
        "a check is asserted with neither an implementation nor a TODO — it was "
        "invented",
    "specified_not_built":
        "the design RULED this exists, and it does not — the named blocker is "
        "what has to land first",
    "no_coverage_rule":         ("GAP",           "declare a coverage rule for this seat"),
    "unaccounted_check":
        "a check is asserted with neither an implementation nor a TODO — it was "
        "invented",
    "specified_not_built":      ("GAP",           "build it, or record why the blocker stands"),
    "unaccounted_check":        ("CONTRADICTION", "implement it, add a TODO, or delete the claim"),
    "silent_needs_determinism": ("GAP",           "write a deterministic check, or record that none is possible"),
    # ⛔ `only_narrowed` was DISCLOSURE, i.e. non-blocking. That gave it waiver
    # semantics without a waiver's cost — no date, no who, no why — and made
    # check.py report 10 blocking where guard.py reported 14 on identical facts.
    # Ruled 2026-08-07: everything blocks; a waiver is the ONLY route to
    # non-blocking, because it is the only one that records who accepted it.
    "only_narrowed":            ("GAP",           "close it, or waive it with a reason"),
}

#: What each finding kind means, in one line, for someone who did not write it.
MEANING = {
    "uncaught_problem":
        "a problem in the design's own list has NO check claiming to catch it",
    "contamination":
        "a seat can reach material it is forbidden from seeing — transitively, "
        "through a continued conversation",
    "check_no_stage":
        "a check is placed at a stage that does not exist",
    "claim_n_is_one":
        "a measured claim rests on a single observation",
    "unaccounted_check":
        "a check is asserted with neither an implementation nor a TODO — it was "
        "invented",
    "specified_not_built":
        "the design RULED this exists, and it does not — the named blocker is "
        "what has to land first",
    "no_coverage_rule":
        "a seat judges one item at a time and nothing establishes that every "
        "item was judged — the skipped ones are the hard ones",
    "only_narrowed":
        "a check REDUCES this problem but does not close it, and no other check "
        "closes it either — the named residue is a standing disclosure",
    "silent_needs_determinism":
        "a SILENT problem is caught only by a model judgement, so it has no "
        "deterministic floor under it",
}


def solve(extra_facts: str = "") -> set:
    """Return the set of (kind, subject) findings."""
    files = [FACTS, RULES]
    tmp = None
    if extra_facts:
        tmp = os.path.join(HERE, "_scratch.lp")
        open(tmp, "w").write(extra_facts)
        files.append(tmp)
    try:
        r = subprocess.run([PY, "-m", "clingo"] + files + ["--outf=0"],
                           capture_output=True, text=True, cwd=HERE)
        out = r.stdout
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)
    findings = {(m.group(1), m.group(2).strip()) for m in FINDING.finditer(out)}
    labels = dict(LABEL.findall(out))
    # ⛔ PARSE CANARY. The model always emits labels. Zero labels means the
    # parser stopped matching, not that the model is clean — and a parser that
    # silently returns nothing is indistinguishable from a passing check. This
    # exact failure once made guard.py report green on ten open gaps.
    if not labels:
        raise RuntimeError(
            "parsed 0 labels from the solver output — the parser is broken, "
            "or the model failed to solve. Refusing to report a result.\n"
            f"first 400 chars of output:\n{out[:400]}")
    return findings, labels


def solve_modified(drop: str = None, add: str = "") -> set:
    """Solve with one fact line removed from pipeline.lp and/or facts added."""
    src = open(FACTS).read()
    if drop:
        src = src.replace(drop, "")
    tmp = os.path.join(HERE, "_broken.lp")
    open(tmp, "w").write(src + "\n" + add)
    try:
        r = subprocess.run([PY, "-m", "clingo", tmp, RULES, "--outf=0"],
                           capture_output=True, text=True, cwd=HERE)
        return {(m.group(1), m.group(2).strip())
                for m in FINDING.finditer(r.stdout)}
    finally:
        os.remove(tmp)


def waived_set():
    """(kind, subject) pairs carrying a valid waiver in accepted.json."""
    path = os.path.join(HERE, "accepted.json")
    if not os.path.exists(path):
        return set()
    import json
    req = ("finding", "subject", "date", "who", "why")
    return {(w["finding"], w["subject"])
            for w in json.load(open(path)).get("waivers", [])
            if all(str(w.get(f, "")).strip() for f in req)}


def report(found, labels) -> int:
    if not found:
        print("no findings — the model is internally consistent")
        return 0

    waived = waived_set()
    buckets = {"CONTRADICTION": [], "GAP": [], "DISCLOSURE": []}
    for kind, subj in sorted(found):
        cls, _ = CLASS.get(kind, ("GAP", ""))
        buckets[cls].append((kind, subj))

    # Every finding blocks unless waived. The three buckets order the display;
    # they no longer decide anything.
    n_block = sum(1 for c in buckets for k, s_ in buckets[c]
                  if (k, s_) not in waived)
    print(f"{len(found)} findings — {n_block} blocking, "
          f"{len(found) - n_block} waived\n")

    for cls in ("CONTRADICTION", "GAP", "DISCLOSURE"):
        items = buckets[cls]
        if not items:
            continue
        header = {"CONTRADICTION": "⛔ CONTRADICTION — the design says two incompatible things",
                  "GAP": "◻ GAP — something is missing",
                  "DISCLOSURE": "· DISCLOSURE — true and known; not work to be done"}[cls]
        print(header)
        by_kind = {}
        for kind, subj in items:
            by_kind.setdefault(kind, []).append(subj)
        for kind, subjects in by_kind.items():
            meaning = MEANING.get(kind, "?")
            _, clears = CLASS.get(kind, ("", ""))
            print(f"\n  {kind}")
            print(f"    what it means : {meaning}")
            print(f"    what clears it: {clears}")
            for sub in subjects:
                mark = "  [waived]" if (kind, sub) in waived else ""
                name = labels.get(sub)
                print(f"      - {sub}{f' — {name}' if name else ''}{mark}")
        print()
    return 1 if n_block else 0


def self_test() -> int:
    """RED: each rule must fire on a model broken in its own specific way."""
    cases = [
        # p17 has exactly one catcher; p12 has two, so dropping one of p12's
        # leaves it caught — the first version of this case tested nothing.
        ("a problem loses its only catcher",
         dict(drop="catches(cycle_beats, p17)."),
         "uncaught_problem"),

        # The repair loop as originally designed: repair CONTINUED the
        # translator's conversation. Stage 4 exposes the expected verdicts, so
        # after one round-trip the translator has seen them — which one of this
        # project's own documents forbids. The revised design makes repair a
        # fresh conversation; this case proves the rule would have caught the
        # old one.
        ("the OLD repair loop — same conversation as the translator",
         dict(add="continues(repair_seat, translator).\n"
                  "sees(translator, expected_verdicts)."),
         "contamination"),

        ("a check placed at a stage that does not exist",
         dict(add="check(bogus, s99, deterministic). catches(bogus, p1)."),
         "check_no_stage"),

        # ⛔ The previous version of this case dropped `check(link, deterministic)`
        # and re-added it as a seat — but `link` only NARROWS p2, so it was never
        # a floor, and the finding was already firing for nine other problems.
        # The delta comparison now catches that; this replacement introduces a
        # silent problem WITH a working floor, then removes the floor.
        ("a silent problem loses its deterministic floor",
         dict(add="problem(p99, testing, silent).\n"
                  "check(c99, s2, deterministic). catches(c99, p99).\n"
                  "label(p99, \"synthetic test problem\")."),
         "unaccounted_check"),
    ]

    print("RED — each case must INTRODUCE its finding, not merely coexist with it:\n")
    baseline, _ = solve()
    ok = True
    for name, kw, expect in cases:
        # ⛔ An earlier version tested `expect in kinds`. Two cases passed
        # because the finding was ALREADY firing for other reasons — the
        # mutation changed nothing and the test proved nothing. Compare deltas.
        if kw.get("drop"):
            src = open(FACTS).read()
            if kw["drop"] not in src:
                print(f"  [FAIL] {name}")
                print(f"          drop string not found in pipeline.lp — "
                      f"the mutation silently did nothing")
                ok = False
                continue
        found = solve_modified(**kw)
        added = found - baseline
        hit = expect in {k for k, _ in added}
        print(f"  [{'PASS' if hit else 'FAIL'}] {name}")
        if hit:
            print(f"          `{expect}` introduced: "
                  f"{sorted(s for k, s in added if k == expect)}")
        else:
            already = expect in {k for k, _ in baseline}
            print(f"          `{expect}` NOT introduced"
                  + (" — it was already firing, so this case tests nothing"
                     if already else ""))
        ok &= hit

    print("\nGREEN — the real model must NOT report contamination "
          "(repair is a fresh conversation):")
    live = {k for k, _ in solve()[0]}
    clean = "contamination" not in live
    print(f"  [{'PASS' if clean else 'FAIL'}] contamination absent")
    print(f"\nlive findings on the real model: {sorted(live)}")
    return 0 if (ok and clean) else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(self_test())
    f, labels = solve()
    raise SystemExit(report(f, labels))
