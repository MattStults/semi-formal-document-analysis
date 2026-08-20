#!/usr/bin/env python3
"""Machine check for the declaration-search prototype (design tier: Fable).
Exit 0 = outputs structurally complete. Does NOT bless the content."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
def die(m): print("FAIL:", m); sys.exit(1)
for f in ("feature_matrix.json", "fit_report.json", "declaration_proposals.json"):
    if not os.path.exists(os.path.join(HERE, f)): die(f"{f} missing")
fm = json.load(open(os.path.join(HERE, "feature_matrix.json")))
rows = fm.get("rows") or []
if len(rows) < 800: die(f"feature matrix has {len(rows)} rows; expected ~836")
if not any(r.get("masked") for r in rows): die("no masked (defensible) rows — mask step skipped")
feats = fm.get("feature_names") or []
need_prefixes = ("governs=", "protects=", "purpose=", "context=", "actor")
for p in need_prefixes:
    if not any(p in f for f in feats): die(f"no feature named with '{p}'")
if not any("requester_purpose_conditioned" in f for f in feats): die("context atoms absent from features")
fr = json.load(open(os.path.join(HERE, "fit_report.json")))
if "hypothes" not in json.dumps(fr).lower(): die("fit_report missing hypothesis-only disclaimer")
slugs = {"helpfulness", "harm-avoidance-to-third-parties", "avoiding-over-and-under-caution"}
if not slugs <= set(fr.get("behaviors", {})): die("fit_report missing a behavior")
for s, d in fr["behaviors"].items():
    for k in ("baseline_logloss", "fitted_logloss", "stability"):
        if k not in d: die(f"fit_report[{s}] missing {k}")
    if not isinstance(d["stability"], dict) or not d["stability"]: die(f"fit_report[{s}] stability empty")
dp = json.load(open(os.path.join(HERE, "declaration_proposals.json")))
VALID_SLOTS = {"governs_concern","governs_conditional","protects_concern","purpose_concern",
               "party_concern","performs_acts","contexts_concern"}
for p in dp.get("proposals", []):
    for k in ("behavior","kind","slot","delta","feature","stability","predicted","blind_justification_stub"):
        if k not in p: die(f"proposal missing {k}: {json.dumps(p)[:120]}")
    if p["slot"] not in VALID_SLOTS: die(f"invalid slot {p['slot']}")
    if p["stability"] < 0.7: die(f"proposal below stability bar: {p['feature']}")
    for k in ("fixes","breaks","fixed_nodes","broken_nodes"):
        if k not in p["predicted"]: die(f"proposal.predicted missing {k}")
print("OK: outputs structurally complete "
      f"({len(rows)} rows, {len(feats)} features, {len(dp.get('proposals', []))} proposals)")
