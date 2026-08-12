#!/usr/bin/env python3
"""Heading-scope sweep (golden sweep #2): find heading/section-metadata nodes
whose `establishes` claims semantic content beyond what a heading carries, or
whose section-scoping is missing/wrong.

Audit finding class B/C: a node whose span is only a heading line (or heading
+ blank) sometimes 'establishes' the CONTENT of the section rather than the
existence/scope of the section -- semantics smuggled in from lines the node
does not own. The RECURSE_PROMPT rule is: heading-metadata nodes are
section-scoped ("Section X titled Y governs lines A-B") and never assert the
section's rules themselves.

Detection: a node is heading-only if every span line is a markdown heading,
blank, or horizontal rule. Flag it if establishes (a) never mentions
section/heading/title/govern/cover/scope vocabulary, or (b) contains modal
claims (must/should/may) -- a heading can't oblige anyone.

CANDIDATE GENERATOR: flags require adjudication against the document.
RED check: --self-test feeds a heading node asserting a rule (must flag) and
a correct section-scoped one (must pass).
"""
import argparse
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
GRAPH = os.path.join(HERE, "recurse", "root", "graph.json")
DOC = os.path.join(HERE, "..", "..", "..", "..", "..", "specs",
                   "openai-model-spec", "model_spec.md")

HEADINGISH = re.compile(r"^\s*(#{1,6}\s|\s*$|[-=~]{3,}\s*$|\*\*[^*]+\*\*\s*$)")
SCOPE_VOCAB = re.compile(r"\b(section|heading|title[ds]?|govern|cover|scope|"
                         r"introduc|organiz|group|contains|delimits?)\b", re.I)
MODAL = re.compile(r"\b(must|should|may not|shall|never|always|required)\b",
                   re.I)


def heading_only(lines, node):
    body = []
    for sp in node.get("spans", []):
        a, b = sp["lines"]
        body.extend(lines[a - 1:b])
    return bool(body) and all(HEADINGISH.match(l) for l in body)


def check(node, lines):
    if not heading_only(lines, node):
        return []
    est = node["establishes"]
    flags = []
    if not SCOPE_VOCAB.search(est):
        flags.append({"kind": "no_scope_vocab",
                      "detail": "heading-only span but establishes never "
                                "frames itself as section metadata"})
    if MODAL.search(est):
        flags.append({"kind": "modal_in_heading",
                      "detail": "heading-only span but establishes asserts "
                                "an obligation -- content smuggled in"})
    return flags


def self_test():
    lines = ["## Stay in bounds", "", "The assistant must follow policy."]
    bad = {"id": "t1", "establishes":
           "The assistant must always stay in bounds and follow policy.",
           "spans": [{"lines": [1, 2]}]}
    assert any(f["kind"] == "modal_in_heading" for f in check(bad, lines)), \
        "self-test FAILED: rule-asserting heading node not flagged"
    ok = {"id": "t2", "establishes":
          "Section heading 'Stay in bounds' titles and governs the "
          "stay-in-bounds subsection.",
          "spans": [{"lines": [1, 2]}]}
    assert check(ok, lines) == [], "self-test FAILED: correct scoped node " \
                                   "flagged"
    content = {"id": "t3", "establishes": "The assistant must follow policy.",
               "spans": [{"lines": [3, 3]}]}
    assert check(content, lines) == [], "self-test FAILED: non-heading node " \
                                        "swept"
    print("self-test: all 3 cases behave (1 RED flagged, 2 GREEN clean)")


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
    report, heading_nodes = [], 0
    for n in g["nodes"]:
        if heading_only(lines, n):
            heading_nodes += 1
        flags = check(n, lines)
        if flags:
            report.append({"id": n["id"], "establishes": n["establishes"],
                           "flags": flags})
    out = args.report or os.path.join(HERE, "sweep_headings_report.json")
    json.dump({"total_nodes": len(g["nodes"]),
               "heading_only_nodes": heading_nodes,
               "flagged": len(report), "findings": report},
              open(out, "w"), indent=1)
    print(f"{len(g['nodes'])} nodes; {heading_nodes} heading-only; "
          f"{len(report)} flagged -> sweep_headings_report.json")
    for r in report[:12]:
        print(f"  {r['id']}: {[f['kind'] for f in r['flags']]}")


if __name__ == "__main__":
    main()
