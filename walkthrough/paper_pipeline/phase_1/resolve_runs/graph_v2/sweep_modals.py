#!/usr/bin/env python3
"""Modal-diff sweep (golden sweep #1): for every node, compare the modal
profile of `establishes` against the modal profile of its span text.

The Fable audit (strata A-D, 30/30 samples) caught modal strengthening
("should" in the document rendered as "must" in establishes) and mixed-modal
flattening (a span containing both "must adhere strictly" and "should notify"
summarised under one modal). Those were repaired where SAMPLED; this sweep
runs the same comparison over all 593 nodes so the class is closed, not
spot-fixed.

This is a CANDIDATE GENERATOR, not an auto-fixer: a flag means "a human/agent
must adjudicate against the document", because establishes legitimately
paraphrases (e.g. span says "must" inside a quoted example the node is not
about). Output: sweep_modals_report.json + a readable summary on stdout.

RED check (S8): --self-test feeds the known n026 defect shape (span has
should, establishes says must) and MUST flag it, and a clean pair MUST pass.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GRAPH = os.path.join(HERE, "recurse", "root", "graph.json")
DOC = os.path.join(HERE, "..", "..", "..", "..", "..", "specs",
                   "openai-model-spec", "model_spec.md")

# ordered by strength; 'never'/'always' treated as must-strength prohibitions
STRONG = re.compile(r"\b(must(?:\s+not)?|never|always|required|prohibited|"
                    r"forbidden)\b", re.I)
MEDIUM = re.compile(r"\b(should(?:\s+not)?|shouldn't|expected\s+to|"
                    r"encouraged\s+to)\b", re.I)
WEAK = re.compile(r"\b(may|might|can|could|optional|allowed\s+to|"
                  r"permitted)\b", re.I)


def profile(text):
    return {"strong": len(STRONG.findall(text)),
            "medium": len(MEDIUM.findall(text)),
            "weak": len(WEAK.findall(text))}


def span_text(lines, node):
    segs = []
    for sp in node.get("spans", []):
        a, b = sp["lines"]
        segs.append(sp.get("quote") or "\n".join(lines[a - 1:b]))
    return "\n".join(segs)


def check(node, lines):
    """Return a list of flags for one node (empty = clean)."""
    est, src = node["establishes"], span_text(lines, node)
    pe, ps = profile(est), profile(src)
    flags = []
    # strengthening: establishes asserts strong modality the span never uses
    if pe["strong"] and not ps["strong"]:
        flags.append({"kind": "strengthened",
                      "detail": f"establishes has {pe['strong']} strong "
                                f"modal(s); span has none "
                                f"(span: {ps['medium']} medium, "
                                f"{ps['weak']} weak)"})
    # weakening: span demands, establishes only suggests/permits
    if ps["strong"] and not pe["strong"] and (pe["medium"] or pe["weak"]):
        flags.append({"kind": "weakened",
                      "detail": f"span has {ps['strong']} strong modal(s); "
                                f"establishes has none"})
    # flattening: span mixes strengths, establishes keeps only one
    tiers_src = sum(1 for k in ps if ps[k])
    tiers_est = sum(1 for k in pe if pe[k])
    if tiers_src >= 2 and tiers_est == 1 and len(src) < 2500:
        flags.append({"kind": "flattened",
                      "detail": f"span mixes {tiers_src} modal tiers "
                                f"({ps}); establishes keeps one ({pe})"})
    return flags


def self_test():
    lines = ["The assistant should notify the user before acting.",
             "It must adhere strictly to the platform policy."]
    # RED 1 -- strengthening: span says should, establishes says must
    bad = {"id": "t1", "establishes":
           "The assistant must notify the user before acting.",
           "spans": [{"lines": [1, 1]}]}
    assert any(f["kind"] == "strengthened" for f in check(bad, lines)), \
        "self-test FAILED: strengthening not flagged"
    # RED 2 -- flattening: span mixes must+should, establishes keeps must only
    mixed = {"id": "t2", "establishes":
             "The assistant must adhere strictly to the platform policy.",
             "spans": [{"lines": [1, 2]}]}
    assert any(f["kind"] == "flattened" for f in check(mixed, lines)), \
        "self-test FAILED: mixed-modal flattening not flagged"
    # GREEN -- faithful summary passes
    ok = {"id": "t3", "establishes":
          "The assistant should notify the user, and must adhere strictly "
          "to the platform policy.",
          "spans": [{"lines": [1, 2]}]}
    assert check(ok, lines) == [], "self-test FAILED: clean pair flagged"
    print("self-test: all 3 cases behave (2 RED flagged, 1 GREEN clean)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--graph", default=GRAPH,
                    help="graph.json to sweep (default: the Haiku golden)")
    ap.add_argument("--report", default=None,
                    help="report path (default: beside this script)")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    g = json.load(open(args.graph))
    lines = open(DOC).read().splitlines()
    report = []
    for n in g["nodes"]:
        flags = check(n, lines)
        if flags:
            report.append({"id": n["id"], "establishes": n["establishes"],
                           "flags": flags})
    out = args.report or os.path.join(HERE, "sweep_modals_report.json")
    json.dump({"total_nodes": len(g["nodes"]), "flagged": len(report),
               "findings": report}, open(out, "w"), indent=1)
    by_kind = {}
    for r in report:
        for f in r["flags"]:
            by_kind[f["kind"]] = by_kind.get(f["kind"], 0) + 1
    print(f"{len(g['nodes'])} nodes swept; {len(report)} flagged "
          f"({by_kind}) -> sweep_modals_report.json")
    for r in report[:10]:
        print(f"  {r['id']}: {[f['kind'] for f in r['flags']]}")


if __name__ == "__main__":
    main()
