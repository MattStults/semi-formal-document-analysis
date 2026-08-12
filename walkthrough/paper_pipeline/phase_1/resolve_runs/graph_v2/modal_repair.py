#!/usr/bin/env python3
"""Deterministic modal repair for the golden protocol (Matt's ruling
2026-08-11: deterministic dominant, LLM fallback).

Covers the two DIRECTIONAL sweep classes -- strengthened (establishes says
must, span says should) and weakened (the reverse) -- where the repair is
fully determined: replace the establishes' modal token with the span's own
modal token, verbatim. Everything else (flattened needs a composed clause;
multi-modal establishes; no clean token mapping) is routed to the seat
queue untouched.

Safety: every templated repair must pass the SAME mechanical gate the seat
repairs passed (re-sweep clean + merge_loss no-content-drop); one that
fails the gate falls back to the seat queue rather than being applied.
The imperative-mood carve-out is applied as a deterministic auto-clear
BEFORE repair: a span that prohibits in imperative mood ("Do not X")
legitimately renders as "must not X" and is not a defect.

Usage:
  python3 modal_repair.py --report sweep_modals_report.json --graph <g.json>
      [--apply]        # without --apply: plan only
Output: modal_repair_plan.json {auto_cleared, templated, seat_queue};
with --apply, templated repairs are written to the graph (backup first).
RED check: --self-test.
"""
import argparse
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sweep_modals import check as modal_check, span_text  # noqa: E402

#: Imperative-mood prohibition/command openers: must-strength text with no
#: modal verb (the run-1 triage regex, promoted).
IMPERATIVE = re.compile(
    r"(?m)^\s*(?:[-*]\s*)?(?:Do not|Don't|Never|Avoid|Refuse|Always)\b",
    re.I)
#: The only substitutions this module is allowed to make: directional
#: modal-token swaps. Anything not covered falls through to the seats.
#: Ordered longest-first, and bare modals exclude their negated forms via
#: lookahead -- review MR-1: \bshould\b matched inside "should not" and a
#: templated repair INVERTED polarity while passing the band gate.
SWAPS = [("must not", "should not"), ("must never", "should never"),
         (r"must(?!\s+(?:not|never)\b)", "should"),
         ("should not", "must not"), ("should never", "must never"),
         (r"should(?!\s+(?:not|never)\b)", "must")]
#: Spans containing example/dialogue markers get no templated repair --
#: review MR-3 (live): the template borrowed a "must" from a fictional
#: developer rule quoted inside a worked example. The gate certifies tier
#: counts, not provenance; quoted-example spans need a seat.
EXAMPLE_MARKERS = re.compile(r"~~~|<assistant>|<user>|<developer>|"
                             r"<comparison>|!!! meta", re.I)


def plan_one(node, lines):
    """-> ('auto_clear'|'templated'|'seat', detail)."""
    flags = modal_check(node, lines)
    kinds = {f["kind"] for f in flags}
    if not flags:
        return "auto_clear", "no longer flagged"
    src = span_text(lines, node)
    from sweep_modals import profile
    ps = profile(src)
    if (kinds == {"strengthened"} and IMPERATIVE.search(src)
            and not ps["medium"] and not ps["weak"]):
        # review MR-2: only a PURE imperative span auto-clears; a span
        # mixing "Do not ..." with its own should-claims still needs eyes
        return "auto_clear", "pure imperative-mood span: must-strength " \
                             "without a modal verb is faithful"
    if EXAMPLE_MARKERS.search(src):
        return "seat", "span contains quoted example/dialogue; a modal " \
                       "borrowed from quoted text needs judgment (MR-3)"
    if kinds <= {"strengthened", "weakened"}:
        # directional: substitute the wrong modal with the span's own
        want_dir = "weaken" if "strengthened" in kinds else "strengthen"
        est = node["establishes"]
        for a, b in SWAPS:
            strengthens = b.startswith("must")
            # the span occurrence of the TARGET modal must itself be
            # un-negated when the target is a bare positive form -- the
            # MR-1 inversion happened because the span's "should" was part
            # of "should not"
            bare = b in ("should", "must")
            span_pat = (rf"\b{b}\b(?!\s+(?:not|never)\b)" if bare
                        else rf"\b{b}\b")
            if ((want_dir == "strengthen") == strengthens
                    and re.search(rf"\b{a}\b", est)
                    and re.search(span_pat, src, re.I)):
                prop = re.sub(rf"\b{a}\b", b, est, count=1)
                trial = dict(node, establishes=prop)
                if not modal_check(trial, lines):     # the mechanical gate
                    return "templated", prop
        return "seat", "no clean token mapping to the span's own modal"
    return "seat", f"non-directional flags {sorted(kinds)} need composition"


def self_test():
    lines = ["The assistant should notify the user before acting.",
             "Do not reveal the system prompt."]
    # RED 1: directional strengthened -> templated with the span's modal
    n = {"id": "t", "establishes": "The assistant must notify the user "
                                   "before acting.",
         "spans": [{"lines": [1, 1]}]}
    kind, prop = plan_one(n, lines)
    assert kind == "templated" and "should notify" in prop, (kind, prop)
    # RED 2: imperative span -> auto_clear, never "repaired"
    n2 = {"id": "t2", "establishes": "The assistant must not reveal the "
                                     "system prompt.",
          "spans": [{"lines": [2, 2]}]}
    kind2, why = plan_one(n2, lines)
    assert kind2 == "auto_clear", (kind2, why)
    # RED 3: flattened routes to seat (composition needed)
    lines3 = ["It should ask first.", "It must never lie."]
    n3 = {"id": "t3", "establishes": "It must never lie.",
          "spans": [{"lines": [1, 2]}]}
    kind3, _ = plan_one(n3, lines3)
    assert kind3 == "seat", kind3
    print("self-test: 3/3 (templated, auto-clear, seat-fallback)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", default=os.path.join(
        HERE, "sweep_modals_report.json"))
    ap.add_argument("--graph", default=os.path.join(
        HERE, "recurse", "root", "graph.json"))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        review_pins()
        return
    doc = os.path.join(HERE, "..", "..", "..", "..", "..", "specs",
                       "openai-model-spec", "model_spec.md")
    lines = open(doc).read().splitlines()
    g = json.load(open(args.graph))
    by = {n["id"]: n for n in g["nodes"]}
    rep = json.load(open(args.report))
    out = {"auto_cleared": [], "templated": [], "seat_queue": []}
    for r in rep["findings"]:
        n = by.get(r["id"])
        if n is None:
            continue
        kind, detail = plan_one(n, lines)
        row = {"id": r["id"], "detail": detail}
        {"auto_clear": out["auto_cleared"], "templated": out["templated"],
         "seat": out["seat_queue"]}[kind].append(row)
    plan_path = os.path.join(HERE, "modal_repair_plan.json")
    json.dump(out, open(plan_path, "w"), indent=1)
    print(f"{len(out['auto_cleared'])} auto-cleared, "
          f"{len(out['templated'])} templated, "
          f"{len(out['seat_queue'])} to seats -> {plan_path}")
    if args.apply and out["templated"]:
        shutil.copy(args.graph, args.graph + ".pre_modal_repair.bak")
        for row in out["templated"]:
            by[row["id"]]["establishes"] = row["detail"]
        json.dump(g, open(args.graph, "w"), indent=1)
        print(f"applied {len(out['templated'])} templated repairs "
              f"(backup written)")




def review_pins():
    """RED pins for review MR-1/MR-2/MR-3 (instruments_review.md)."""
    # MR-1: polarity must not invert -- span says "should not", establishes
    # wrongly says "must": NO template may produce "should" (dropping the not)
    lines = ["The assistant should not comply with such requests."]
    n = {"id": "p1", "establishes": "The assistant must comply with such "
                                    "requests.", "spans": [{"lines": [1, 1]}]}
    kind, detail = plan_one(n, lines)
    assert not (kind == "templated" and "should comply" in detail), \
        f"MR-1 REGRESSION: polarity inverted: {detail}"
    # MR-2: mixed span (imperative + its own should-claim) must NOT auto-clear
    lines2 = ["Do not reveal the prompt.",
              "The assistant should explain its refusal."]
    n2 = {"id": "p2", "establishes": "The assistant must explain its "
                                     "refusal.", "spans": [{"lines": [1, 2]}]}
    kind2, _ = plan_one(n2, lines2)
    assert kind2 != "auto_clear", "MR-2 REGRESSION: mixed span auto-cleared"
    # MR-3: example-marker span routes to seat even if directional
    lines3 = ["~~~", "<developer>You must refund within 30 days.</developer>",
              "The assistant should follow developer instructions."]
    n3 = {"id": "p3", "establishes": "The assistant must follow developer "
                                     "instructions.",
          "spans": [{"lines": [1, 3]}]}
    kind3, _ = plan_one(n3, lines3)
    assert kind3 == "seat", f"MR-3 REGRESSION: {kind3}"
    print("review pins: 3/3")

if __name__ == "__main__":
    main()
