#!/usr/bin/env python3
"""FREE, deterministic, zero-API. Run the pipeline's TUNED patterns over the
Model Spec and over a second document that shares NONE of its conventions, and
report what each one does there.

⛔ This measures PATTERN FIRING ONLY. It is not a measurement of detection
quality -- there are no labels on the second document. What it establishes is
the narrower, decisive fact: which instruments go SILENT and which ones stay
alive when the conventions vanish.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
P1 = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO = os.path.abspath(os.path.join(P1, "..", "..", ".."))
for p in (P1, os.path.join(P1, "resolve_runs", "graph_v2")):
    sys.path.insert(0, p)

import checks                                              # noqa: E402
sys.path.insert(0, os.path.join(P1, "_debug_gen11", "fix_matrix"))
import importlib.util                                      # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except Exception as exc:                                # pragma: no cover
        print(f"  (could not import {name}: {exc})")
        return None
    return m


DOCS = {
    "model_spec": os.path.join(REPO, "specs/openai-model-spec/model_spec.md"),
    "claude_constitution": os.path.join(
        REPO, "specs/claude-constitution/20260120-constitution.md"),
}

# ---- the tuned patterns, copied BY VALUE from their live sites so this
# ---- script cannot perturb them. Each carries its file:line.
PATTERNS = {
    "checks._DISFAVOURED  (checks.py:305)": checks._DISFAVOURED,
    "graph_check authority heading  (graph_check.py:128)":
        re.compile(r"^#+ .*authority=", re.M),
    "promise_repair.HEADING_RE  (promise_repair.py:150)":
        re.compile(r"^\s{0,3}#{1,6}\s+.*\{#([A-Za-z0-9_-]+)[ }]", re.M),
    "modal_repair formatting  (modal_repair.py:56)":
        re.compile(r"<comparison>|!!! meta", re.I),
    "fix_matrix._WORKED_EXAMPLE  (detectors.py:280)":
        re.compile(r"<!--\s*(GOOD|BAD)\b|\bGOOD:|\bBAD:", re.I),
    "recurse_driver admonition marker  (recurse_driver.py:367)":
        re.compile(r'!!! meta "Commentary"'),
    "flip_classify narrowing title  (classify.py:337)":
        re.compile(r"\*\*Example\*\*"),
}


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.;!?])\s+|\n+", text) if s.strip()]


def main():
    texts = {k: open(v, encoding="utf-8").read() for k, v in DOCS.items()}

    print("=" * 78)
    print("A. TUNED PATTERN FIRING COUNTS  (whole document)")
    print("=" * 78)
    print(f"{'pattern':58s} " + " ".join(f"{k[:14]:>14s}" for k in DOCS))
    for name, rx in PATTERNS.items():
        row = [len(rx.findall(t)) for t in texts.values()]
        print(f"{name:58s} " + " ".join(f"{n:>14d}" for n in row))

    print()
    print("=" * 78)
    print("B. THE OVER-ASSERTION TEST (F2) -- detectors._norm_bearing")
    print("   fraction of document sentences the test rates NORM-BEARING")
    print("=" * 78)
    det = _load("detectors", os.path.join(P1, "_debug_gen11", "fix_matrix",
                                          "detectors.py"))
    if det is not None:
        for k, t in texts.items():
            ss = sentences(t)
            nb = [s for s in ss if det._norm_bearing(s)]
            bear = [s for s in ss if det._BEARER.search(s)]
            deo = [s for s in ss if det._DEONTIC.search(s)]
            print(f"  {k:24s} sentences={len(ss):5d}  "
                  f"deontic={len(deo):5d} ({len(deo)/len(ss)*100:5.1f}%)  "
                  f"bearer-word={len(bear):5d} ({len(bear)/len(ss)*100:5.1f}%)  "
                  f"NORM-BEARING={len(nb):5d} ({len(nb)/len(ss)*100:5.1f}%)")
        print()
        print("  ⚠️ F2 fires 'over-assertion' when NO sentence in a span is "
              "norm-bearing.\n     A collapse in this column is F2 becoming a "
              "FALSE-POSITIVE GENERATOR, not going quiet.")

    print()
    print("=" * 78)
    print("C. NORMATIVE DENSITY  (is the second document comparable at all?)")
    print("=" * 78)
    MOD = re.compile(r"\b(must not|must|should not|should|shall not|shall|may)\b", re.I)
    for k, t in texts.items():
        ss = sentences(t)
        print(f"  {k:24s} words={len(t.split()):6d}  sentences={len(ss):5d}  "
              f"modal tokens={len(MOD.findall(t)):5d}  "
              f"modals/1k words={len(MOD.findall(t))/len(t.split())*1000:5.1f}")


if __name__ == "__main__":
    main()
