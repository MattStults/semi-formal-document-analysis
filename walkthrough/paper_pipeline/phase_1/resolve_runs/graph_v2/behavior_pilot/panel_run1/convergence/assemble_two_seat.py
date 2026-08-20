#!/usr/bin/env python3
"""TWO-SEAT CONSENSUS ASSEMBLY (escalation architecture, definitional lane).
Rules (fixed before results were compared):
 - a claim is ADMISSIBLE only if both seats agree on actor; disputed-actor claims
   contribute nothing and go to the escalation queue (Fable, post-reset);
 - set fields (acts/governs/contexts/protects/purpose): consensus = intersection
   (only values BOTH seats endorsed); values one seat proposed go to the queue;
 - empty consensus on a field = no information = the lane's fail-open semantics
   (sig records only when governs non-empty; protects defaults unspecified);
 - role purity: minor -> third_party (contract 9a), applied to both seats pre-compare.
Outputs: definition_*.json consensus layers + definitional_escalation_queue.json."""
import json, os, glob
HERE = os.path.dirname(os.path.abspath(__file__))
BP = os.path.abspath(os.path.join(HERE, '..', '..'))

def load(seat_globs):
    d = {}
    for g in seat_globs:
        for p in sorted(glob.glob(os.path.join(HERE, g))):
            d.update(json.load(open(p)))
    return d

def purify(vals):
    return sorted({'third_party' if v == 'minor' else v for v in (vals or [])})

# EXAMPLE-NARRATION SCOPE (channel jurisdiction, same principle as the purpose-
# channel scoping): a definitional claim that NARRATES a worked example's response
# ("the GOOD/BAD assistant ...", "the example ...") is example material — the
# calibrated channel for examples is example_acts.json (quote-gated, Opus). The
# definitional lane does not lift acts from such claims. Deterministic predicate
# on the claim text itself; no truth values in the loop. (Both seats independently
# flagged example-label claims as ambiguous during annotation.)
import re
_EX = re.compile(r"\b(?:GOOD|BAD)\s+assistant\b|\bthe example\b", re.I)

s1 = load(['def_cal_ann_*.json', 'def_rest_ann_*.json'])
s2 = load(['def_s2_ann_*.json'])
assert set(s1) == set(s2) and all(len(s1[n]) == len(s2[n]) for n in s1)

# EXAMPLE-NARRATION SCOPE (channel jurisdiction; same principle as the purpose-
# channel scoping in relevance_by_act.py): a claim that NARRATES a worked
# example's response ("the GOOD/BAD assistant ...", "the example ...") is example
# material — the calibrated channel for examples is example_acts.json (quote-
# gated). The definitional lane does not lift ACTS from such claims (other fields
# unaffected). Deterministic predicate on the claim text; no truth in the loop.
# Both seats independently flagged example-label claims as ambiguous.
import re, sys as _sys
_sys.path.insert(0, BP); _sys.path.insert(0, os.path.dirname(BP))
import link_nodes as _ln
_EX = re.compile(r"\b(?:GOOD|BAD)\s+assistant\b|\bthe example\b", re.I)
_sel = _ln.gather()
CLAIMS = {nid: (_sel[_ln.norm_id(nid)][1].get('claims') or []) for nid in s1}

acts, sig, prot, pa = {}, {}, {}, {}
queue = []
for nid in sorted(s1):
    node_acts = set()
    for i, (c1, c2) in enumerate(zip(s1[nid], s2[nid])):
        k = f"{nid}|c{i}"
        if c1.get('actor') != c2.get('actor'):
            queue.append({"key": k, "field": "actor", "seat1": c1.get('actor'), "seat2": c2.get('actor')})
            continue  # inadmissible claim
        fields = {}
        claim_text = ""  # locate this claim's text for the example-narration predicate
        example_claim = False
        try:
            import link_nodes as _ln  # claims live in the module object
        except Exception:
            _ln = None
        for f in ('acts', 'governs', 'contexts', 'purpose'):
            v1, v2 = set(c1.get(f) or []), set(c2.get(f) or [])
            fields[f] = sorted(v1 & v2)
            for v in sorted(v1 ^ v2):
                queue.append({"key": k, "field": f, "value": v, "endorsed_by": "seat1" if v in v1 else "seat2"})
        v1, v2 = set(purify(c1.get('protects'))), set(purify(c2.get('protects')))
        fields['protects'] = sorted(v1 & v2)
        for v in sorted(v1 ^ v2):
            queue.append({"key": k, "field": "protects", "value": v, "endorsed_by": "seat1" if v in v1 else "seat2"})
        if not _EX.search(CLAIMS[nid][i] if i < len(CLAIMS[nid]) else ""):
            node_acts |= set(fields['acts'])
        if fields['governs']:
            sig[k] = {"governs": fields['governs'], "contexts": fields['contexts'],
                      "authority_plumbing": c1.get('actor') == 'document'}
        prot[k] = fields['protects'] or ['unspecified']
        pa[k] = {"actor": c1.get('actor'), "purpose": fields['purpose']}
    if node_acts:
        acts[nid] = sorted(node_acts)

json.dump({"_": "two-seat consensus (assemble_two_seat.py); escalations in definitional_escalation_queue.json", "acts": acts},
          open(os.path.join(BP, 'definition_acts.json'), 'w'), indent=1)
json.dump(sig, open(os.path.join(BP, 'definition_signature.json'), 'w'), indent=1)
json.dump(prot, open(os.path.join(BP, 'definition_protects.json'), 'w'), indent=1)
json.dump(pa, open(os.path.join(BP, 'definition_purpose_actor.json'), 'w'), indent=1)
json.dump({"_": "field-level seat disagreements for Fable escalation (post-reset); consensus layers carry only two-seat-agreed values",
           "count": len(queue), "items": queue},
          open(os.path.join(HERE, 'definitional_escalation_queue.json'), 'w'), indent=1)
print(f"nodes with consensus acts: {len(acts)}; sig records: {len(sig)}; escalation items: {len(queue)}")
