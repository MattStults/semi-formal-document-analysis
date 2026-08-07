"""Execute the competency questions in `competency_questions.json`.

WHY THIS EXISTS. Stage 0's output is worthless as prose. The design's rule is that a
competency question is not ready until its expected answer is written down; the natural
consequence is that the written-down answer must be *runnable*, or nobody will ever find
out that it was wrong. Two of the seven questions here had an expected answer that the
solver contradicted, and neither would have been caught by reading.

TWO MODES.

  (default)     run every instance and compare against its written-first answer.
                Exit 0 iff every instance's observed result matches its declared
                expectation, INCLUDING the instances whose declared expectation is
                "this fails" (`"note"` beginning "Expected to FAIL").

  --collapse A=B
                the stage-7 EXPAND stopping rule, mechanically. Identify the two
                symbols throughout the module set, re-run every instance, and report
                which instances break. An instance that breaks NAMES the question that
                licenses the distinction. If no instance breaks, the distinction is not
                licensed by any competency question and stage 7 must stop.

Usage:
    python3 cq_check.py
    python3 cq_check.py --collapse action=information
    python3 cq_check.py --collapse sensitive_content=restricted_content
"""

import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
WALK = os.path.dirname(HERE)                       # walkthrough/
REPO = os.path.dirname(WALK)
PY = os.path.join(REPO, "semi-formal-experiment", ".venv", "bin", "python")
SPEC = os.path.join(HERE, "competency_questions.json")
LINK = os.path.join(WALK, "link.py")

ATOM = re.compile(r"[a-z_][A-Za-z0-9_]*\([^()]*\)")


# --------------------------------------------------------------------------- prep

def resolve(mod):
    """Module paths in the spec are relative to walkthrough/, except cq_support/."""
    p = os.path.join(WALK, mod)
    return p if os.path.exists(p) else os.path.join(HERE, mod)


def materialise(modules, omit_facts, collapse, tmp):
    """Copy modules into tmp, applying fact omission and symbol collapse.

    omit_facts   drops any line whose stripped form starts with the given prefix.
                 That is what makes CQ-5 (assumption toggling) a real operation on
                 the program rather than a promise in a design document.
    collapse     token-level rename, used only by --collapse.
    """
    out = []
    for m in modules:
        src = resolve(m)
        txt = open(src, encoding="utf-8").read()
        if omit_facts:
            keep = []
            for line in txt.splitlines():
                if any(line.strip().startswith(o) for o in omit_facts):
                    continue
                keep.append(line)
            txt = "\n".join(keep) + "\n"
        if collapse:
            a, b = collapse
            txt = re.sub(r"\b%s\b" % re.escape(a), b, txt)
        dst = os.path.join(tmp, os.path.basename(src))
        i = 1
        while os.path.exists(dst):                 # basename collisions
            dst = os.path.join(tmp, "%d_%s" % (i, os.path.basename(src)))
            i += 1
        open(dst, "w", encoding="utf-8").write(txt)
        out.append(dst)
    return out


# ------------------------------------------------------------------------- runners

def run_clingo(run, collapse, tmp):
    mods = materialise(run["modules"], run.get("omit_facts"), collapse, tmp)
    cmd = [PY, "-m", "clingo"] + mods + [str(run.get("enumerate", 1)), "--outf=0"]
    if run.get("project"):
        cmd.append("--project")
    r = subprocess.run(cmd, capture_output=True, text=True)
    blob = r.stdout + r.stderr
    models = []
    for line in blob.splitlines():
        if line.startswith("Answer:"):
            models.append(None)                    # placeholder; atoms are next line
        elif models and models[-1] is None:
            models[-1] = set(ATOM.findall(line))
    models = [m for m in models if m]
    return {"unsat": "UNSATISFIABLE" in blob, "models": models,
            "union": set().union(*models) if models else set()}


def run_link(run, collapse, tmp):
    mods = materialise(run["modules"], run.get("omit_facts"), collapse, tmp)
    r = subprocess.run([PY, LINK] + mods, capture_output=True, text=True)
    blob = r.stdout + r.stderr
    unresolved, grabbing = [], False
    for line in blob.splitlines():
        if "UNRESOLVED REFERENCE" in line:
            grabbing = True
            continue
        if grabbing:
            s = line.strip()
            if not s or s.startswith("Each one"):
                break
            unresolved.append(s)
    return {"unresolved": sorted(unresolved)}


# ------------------------------------------------------------------------- verdicts

def judge(run, res, collapse=None):
    """Compare observed to the instance's written-first expectation.

    Under --collapse the expectation is restated in the collapsed vocabulary too:
    the probe asks whether the DISTINCTION does any work, not whether a symbol got
    renamed. Renaming both sides is what keeps the probe from reporting a spurious
    break on every instance that happens to mention the symbol.
    """
    exp, fails = run["expect"], []
    if collapse:
        a, b = collapse
        exp = json.loads(re.sub(r"\b%s\b" % re.escape(a), b, json.dumps(exp)))
    if run["kind"] == "link":
        if res["unresolved"] != sorted(exp["unresolved"]):
            fails.append("unresolved %s, expected %s"
                         % (res["unresolved"], sorted(exp["unresolved"])))
        return fails
    if exp.get("unsat"):
        if not res["unsat"]:
            fails.append("expected UNSATISFIABLE, got %d model(s)" % len(res["models"]))
        return fails
    if res["unsat"]:
        return ["UNSATISFIABLE — no answer at all"]
    for a in exp.get("holds", []):
        if a not in res["union"]:
            fails.append("missing %s" % a)
    for a in exp.get("absent", []):
        if a in res["union"]:
            fails.append("present but should be absent: %s" % a)
    if "model_count" in exp and len(res["models"]) != exp["model_count"]:
        fails.append("%d model(s), expected %d" % (len(res["models"]), exp["model_count"]))
    for a in exp.get("all_models_contain", []):
        bad = sum(1 for m in res["models"] if a not in m)
        if bad:
            fails.append("%d/%d model(s) lack %s" % (bad, len(res["models"]), a))
    if "union_over_models_equals" in exp:
        spec = exp["union_over_models_equals"]
        got = sorted(a for a in res["union"] if a.startswith(spec["pattern"] + "("))
        if got != sorted(spec["atoms"]):
            fails.append("%s/* == %s, expected %s" % (spec["pattern"], got,
                                                     sorted(spec["atoms"])))
    return fails


# ----------------------------------------------------------------------------- main

def main(collapse=None):
    doc = json.load(open(SPEC, encoding="utf-8"))
    rows, npass, nfail, nskip = [], 0, 0, 0
    for q in doc["questions"]:
        for inst in q["instances"]:
            run = inst["run"]
            expects_failure = inst.get("note", "").startswith("Expected to FAIL")
            if run["kind"] == "not_runnable":
                rows.append((inst["id"], "BLOCKED", run["reason"]))
                nskip += 1
                continue
            with tempfile.TemporaryDirectory() as tmp:
                res = (run_link if run["kind"] == "link" else run_clingo)(run, collapse, tmp)
            fails = judge(run, res, collapse)
            if collapse:
                # Baseline-relative, or the probe reports every already-failing
                # instance (CQ-1.c, CQ-5.a, CQ-7.a) as broken by every collapse.
                if expects_failure:
                    rows.append((inst["id"], "n/a", "already failing at baseline"))
                    continue
                rows.append((inst["id"], "BROKEN" if fails else "unaffected",
                             "; ".join(fails) or "answer unchanged under collapse"))
                continue
            if fails and expects_failure:
                rows.append((inst["id"], "FAILS-AS-DECLARED", "; ".join(fails)))
                npass += 1
            elif fails:
                rows.append((inst["id"], "FAIL", "; ".join(fails)))
                nfail += 1
            elif expects_failure:
                rows.append((inst["id"], "FAIL", "declared as expected-to-fail, but PASSED "
                                                 "— update the declaration"))
                nfail += 1
            else:
                rows.append((inst["id"], "pass", ""))
                npass += 1

    width = max(len(r[1]) for r in rows)
    if collapse:
        print("STOPPING-RULE PROBE — collapsing `%s` into `%s`\n" % collapse)
    for i, s, d in rows:
        print("  %-8s %-*s %s" % (i, width, s, d))
    if collapse:
        broke = [r[0] for r in rows if r[1] == "BROKEN"]
        print("\n  %d instance(s) broken by the collapse: %s"
              % (len(broke), ", ".join(broke) or "none"))
        print("  ⇒ " + ("the distinction is REQUIRED, and these instances are what "
                        "license it" if broke else
                        "NO competency question distinguishes these symbols. Stage 7 "
                        "must not expand here."))
        return 0
    print("\n  %d as declared, %d unexpected, %d blocked" % (npass, nfail, nskip))
    return 1 if nfail else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    col = None
    if args and args[0] == "--collapse":
        a, _, b = args[1].partition("=")
        col = (a, b)
    raise SystemExit(main(col))
