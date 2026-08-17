#!/usr/bin/env python3
"""FREE. Is F2's bearer test a MECHANISM or a WORD LIST?

_BEARER (detectors.py:227) is `(the )?(assistant|model|models|chatgpt|it)`.
If the mechanism generalises, swapping in the second document's own actor name
should restore the recognition rate. If it does not, the collapse is deeper
than vocabulary.
"""
import os, re, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
P1 = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO = os.path.abspath(os.path.join(P1, "..", "..", ".."))
sys.path.insert(0, P1)
spec = importlib.util.spec_from_file_location(
    "detectors", os.path.join(P1, "_debug_gen11", "fix_matrix", "detectors.py"))
det = importlib.util.module_from_spec(spec); spec.loader.exec_module(det)

DOC = os.path.join(REPO, "specs/claude-constitution/20260120-constitution.md")
MS = os.path.join(REPO, "specs/openai-model-spec/model_spec.md")
sent = lambda t: [s.strip() for s in re.split(r"(?<=[.;!?])\s+|\n+", t) if s.strip()]

orig = det._BEARER
VARIANTS = {
  "as shipped (assistant|model|models|chatgpt|it)": orig,
  "+ claude": re.compile(r"\b(the )?(assistant|model|models|chatgpt|it|claude)\b", re.I),
  "+ claude, anthropic, operator(s), principal(s)":
      re.compile(r"\b(the )?(assistant|model|models|chatgpt|it|claude|anthropic|"
                 r"operators?|principals?)\b", re.I),
  "ANY subject (mechanism-only: bearer test disabled)": re.compile(r"."),
}
for name, path in (("model_spec", MS), ("claude_constitution", DOC)):
    ss = sent(open(path, encoding="utf-8").read())
    deo = [s for s in ss if det._DEONTIC.search(s) or det._PERMISSION.search(s)]
    print(f"\n{name}: {len(ss)} sentences, {len(deo)} carry a deontic/permission")
    for label, rx in VARIANTS.items():
        det._BEARER = rx
        nb = sum(1 for s in ss if det._norm_bearing(s))
        cov = sum(1 for s in deo if det._norm_bearing(s))
        print(f"  {label:52s} norm-bearing={nb:5d}  "
              f"of deontic sentences kept {cov}/{len(deo)} = {cov/len(deo)*100:5.1f}%")
    det._BEARER = orig
