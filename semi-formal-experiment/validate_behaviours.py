"""Validate the prototype against the LLM-panel behaviour->passage relevance data.

Three checks per behaviour from behaviours.json:
  1. Expressibility: can the behaviour be defined over the current vocabulary?
     (deterministic: every required concept must map to an existing atom)
  2. Relevance: which norms does the deterministic check flag (atom overlap +
     one-step conflict closure), and which constitution section families?
  3. Panel join: within the formalized section families, do the panel's
     high-consensus passages (score >= 5, all 3 judges) land in families our
     relevance check flags?

NOTE: NORMS below mirrors rules.lp by hand (reification debt — the full
version should generate this from the .lp file).
"""
import json
import os
from collections import Counter

PANEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "behaviours.json")
HIGH_CONSENSUS = 5  # score >= 5 of 6 = all three judges, at least two "core"

# ---- vocabulary (mirrors rules.lp) ----
CTX = {
    "user_prefers_p", "bel_true", "bel_false", "bel_uncertain", "user_wants_info",
    "op_restricts_info", "op_restricts_limit_info", "business_reason",
    "compliance_creates_false_impression", "deception_real_harm",
    "decision_own_purview", "harms_flourishing", "user_wants_reliance",
    "reliance_endorsed", "caution_not_needed", "risk_to_life",
}
ACTS = {
    "assert_p", "hedge_p", "disclose_i", "comply_restrict", "tell_limits",
    "refer_emergency", "respect_decision", "intervene_wellbeing", "foster_reliance",
}

# ---- reified norms (mirrors rules.lp) ----
NORMS = {
    "h1_truthful":     dict(ctx={"bel_false"}, act="assert_p", family="Being honest"),
    "h2_calibrated":   dict(ctx={"bel_uncertain", "user_prefers_p"}, act="hedge_p", family="Being honest"),
    "h4_forthright":   dict(ctx={"user_wants_info", "op_restricts_info"}, act="disclose_i", family="Being honest"),
    "h5_nondeceptive": dict(ctx={"compliance_creates_false_impression"}, act="comply_restrict", family="Being honest"),
    "h7_antireliance": dict(ctx={"user_wants_reliance", "reliance_endorsed"}, act="foster_reliance", family="Being honest"),
    "g1_immediate":    dict(ctx={"user_prefers_p"}, act="assert_p", family="Genuine helpfulness"),
    "g1_reliance":     dict(ctx={"user_wants_reliance"}, act="foster_reliance", family="Genuine helpfulness"),
    "g3_wellbeing":    dict(ctx={"harms_flourishing"}, act="intervene_wellbeing", family="Genuine helpfulness"),
    "g5_nowishywashy": dict(ctx={"caution_not_needed", "user_prefers_p"}, act="hedge_p", family="Genuine helpfulness"),
    "g6_autonomy":     dict(ctx={"decision_own_purview"}, act="respect_decision", family="Genuine helpfulness"),
    "p1_opcomply":     dict(ctx={"op_restricts_info", "business_reason"}, act="comply_restrict", family="Principal hierarchy"),
    "p1b_oplimits":    dict(ctx={"op_restricts_limit_info", "business_reason"}, act="tell_limits", family="Principal hierarchy"),
    "p2_telllimits":   dict(ctx={"op_restricts_limit_info"}, act="tell_limits", family="Principal hierarchy"),
    "p3_noharmdeceive": dict(ctx={"compliance_creates_false_impression", "deception_real_harm"}, act="comply_restrict", family="Principal hierarchy"),
    "p4_emergency":    dict(ctx={"risk_to_life"}, act="refer_emergency", family="Principal hierarchy"),
    "p4b_opsilence":   dict(ctx={"risk_to_life", "op_restricts_info", "business_reason"}, act="refer_emergency", family="Principal hierarchy"),
}

# conflict pairs as enumerated by run_conflicts.py (one-step relevance closure)
CONFLICT_PAIRS = [
    ("g1_immediate", "h1_truthful"), ("g1_immediate", "h2_calibrated"),
    ("g1_reliance", "h7_antireliance"), ("h2_calibrated", "g5_nowishywashy"),
    ("h4_forthright", "p1_opcomply"), ("p1_opcomply", "h5_nondeceptive"),
    ("g3_wellbeing", "g6_autonomy"), ("p1_opcomply", "p3_noharmdeceive"),
]

# ---- behaviour definitions: concept -> vocabulary atom (or None = unmappable) ----
BEHAVIOURS = {
    "helpfulness": {
        "satisfy user's immediate request": "user_prefers_p",
        "proactively useful information": "user_wants_info",
        "engagement/reliance user seeks": "user_wants_reliance",
        "respect user's own decisions": "decision_own_purview",
        "serve long-term wellbeing": "harms_flourishing",
        "unhelpfulness is a cost (no needless caution)": "caution_not_needed",
        "act: fulfil the request": "assert_p",
        "act: share information": "disclose_i",
    },
    "avoiding-over-and-under-caution": {
        "excessive hedging/caveats": "hedge_p",
        "caution not actually needed": "caution_not_needed",
        "unnecessary refusal of reasonable requests": None,   # no refuse/comply-with-task act in vocab
        "watered-down help without telling the user": None,   # not encoded
        "under-caution / harmful compliance": None,           # only user-directed deception harm exists
        "disclosing task limits": "tell_limits",
    },
    "harm-avoidance-to-third-parties": {
        "third party outside the conversation": None,
        "harm to society/world": None,
        "weighing costs to non-principals": None,
        # nearest atoms (deception_real_harm, risk_to_life) are user-directed, not third-party
    },
}

# panel section-path (first two levels) -> our formalized family, if any
FAMILY_MAP = {
    "Being broadly ethical > Being honest": "Being honest",
    "Being helpful > What constitutes genuine helpfulness": "Genuine helpfulness",
    "Being helpful > Why helpfulness is one of Claude’s most important traits": "Genuine helpfulness",
    "Being helpful > Navigating helpfulness across principals": "Principal hierarchy",
}


def relevance(atom_map):
    atoms = {a for a in atom_map.values() if a}
    base = {n for n, d in NORMS.items() if d["act"] in atoms or d["ctx"] & atoms}
    closure = set(base)
    for a, b in CONFLICT_PAIRS:
        if a in base:
            closure.add(b)
        if b in base:
            closure.add(a)
    return base, closure


def main():
    panel = json.load(open(PANEL))["behaviours"]
    for beh in panel:
        slug = beh["slug"]
        atom_map = BEHAVIOURS[slug]
        missing = [c for c, a in atom_map.items() if a is None]
        mapped = {c: a for c, a in atom_map.items() if a}
        n_req = len(atom_map)
        status = ("EXPRESSIBLE" if not missing else
                  "INEXPRESSIBLE" if not mapped else "PARTIAL")

        print("=" * 70)
        print(f"{slug}:  {status}  ({len(mapped)}/{n_req} concepts map to vocabulary)")
        if missing:
            print("  unmappable concepts (deterministic signal):")
            for c in missing:
                print(f"    - {c}")
        if status == "INEXPRESSIBLE":
            # boundary check: where do this behaviour's high-consensus passages live?
            passages = beh["coverage"]["anthropic"]["passages"]
            hc = [p for p in passages if p["score"] >= HIGH_CONSENSUS]
            in_scope = sum(1 for p in hc
                           if " > ".join(p["locator"].split(" > ")[1:3]) in FAMILY_MAP)
            print(f"  boundary check: {len(hc)} high-consensus panel passages, "
                  f"{in_scope} inside formalized families, {len(hc) - in_scope} outside")
            continue

        base, closure = relevance(atom_map)
        fams = sorted({NORMS[n]["family"] for n in closure})
        print(f"  relevant norms (atom overlap): {len(base)}; with conflict closure: {len(closure)}")
        print(f"    {sorted(closure)}")
        print(f"  relevant families: {fams}")

        # panel join within formalized families
        passages = beh["coverage"]["anthropic"]["passages"]
        rows = []
        for p in passages:
            fam_key = " > ".join(p["locator"].split(" > ")[1:3])
            fam = FAMILY_MAP.get(fam_key)
            rows.append((p, fam))
        in_scope_hc = [(p, f) for p, f in rows if f and p["score"] >= HIGH_CONSENSUS]
        agree = [(p, f) for p, f in in_scope_hc if f in fams]
        out_of_scope_hc = [p for p, f in rows if not f and p["score"] >= HIGH_CONSENSUS]
        print(f"  panel join (formalized families only):")
        print(f"    high-consensus passages in scope: {len(in_scope_hc)}; "
              f"in families we flag relevant: {len(agree)}")
        misses = [(p, f) for p, f in in_scope_hc if f not in fams]
        for p, f in misses:
            print(f"    MISS: [{f}] {p['locator'].split(' > ', 1)[1]}")
        fam_dist = Counter(" > ".join(p["locator"].split(" > ")[1:3]) for p in out_of_scope_hc)
        print(f"    high-consensus passages OUTSIDE formalized scope: {len(out_of_scope_hc)} "
              f"(top: {fam_dist.most_common(3)})")
    print("=" * 70)


if __name__ == "__main__":
    main()
