"""Safety tests for the paragraph-level provenance back-fill.

Run: .venv/bin/python -m pytest test_locators.py -q

Invariants:
  1. every locator/4 fact is verified: the norm's source sentence (PROBES) is an
     EXACT substring of the cited clause's quote, and the locator/clause-kind
     match that clause's own metadata;
  2. locator/4 is OUTPUT METADATA ONLY -- it appears in no rule body or head;
  3. deleting all locator facts leaves the derived conflict/5 set unchanged;
  4. the rulebase still yields exactly 7 distinct norm-pair conflicts.
"""
import json
import os
import re

import clingo

import backfill_locators as bl

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "rules.lp")


def rules_text():
    return open(RULES).read()


def locator_facts():
    return re.findall(r'^locator\((\w+),\s*"([^"]*)",\s*"(\w+)",\s*"(\w+)"\)\.\s*$',
                      rules_text(), re.M)


def clauses():
    return {c["id"]: c for c in json.load(open(bl.CLAUSES))["clauses"]}


def test_every_locator_is_verified_against_its_clause():
    cl = clauses()
    facts = locator_facts()
    assert facts, "no locator/4 facts found"
    for nid, loc, cid, kind in facts:
        assert cid in cl, f"{nid}: unknown clause {cid}"
        c = cl[cid]
        assert bl.PROBES[nid] in c["quote"], f"{nid}: probe not a substring of {cid}"
        assert c["locator"] == loc, f"{nid}: locator string mismatch"
        assert c["kind"] == kind, f"{nid}: kind mismatch"


def test_locator_is_inert_syntactically():
    """locator/4 must never appear in a rule body or a derived head."""
    for line in rules_text().splitlines():
        s = line.strip()
        if s.startswith("%") or "locator" not in s:
            continue
        assert s.startswith("locator(") or s == "#show locator/4.", \
            f"locator used non-inertly: {s}"
        assert ":-" not in s, f"locator appears in a rule: {s}"


def _conflicts(text):
    ctl = clingo.Control(["--enum-mode=brave"])
    ctl.add("base", [], text)
    ctl.ground([("base", [])])
    got = []

    def on_model(m):
        got.clear()
        got.extend(str(s) for s in m.symbols(shown=True) if s.name == "conflict")

    ctl.solve(on_model=on_model)
    return sorted(got)


def test_locators_do_not_change_derivation():
    full = rules_text()
    stripped = "\n".join(l for l in full.splitlines()
                         if not l.strip().startswith("locator(")
                         and l.strip() != "#show locator/4.")
    assert _conflicts(full) == _conflicts(stripped)


def test_exactly_seven_distinct_norm_pair_conflicts():
    pairs = set()
    for c in _conflicts(rules_text()):
        n1, n2 = c[len("conflict("):-1].split(",")[:2]
        pairs.add(frozenset((n1.strip(), n2.strip())))
    assert len(pairs) == 7, sorted(map(sorted, pairs))
