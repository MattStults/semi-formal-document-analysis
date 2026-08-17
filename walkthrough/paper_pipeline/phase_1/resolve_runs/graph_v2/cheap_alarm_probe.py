#!/usr/bin/env python3
"""CHEAP_ALARM probe — can a cheap model's discrepancy VOLUME route modules
to frontier semantic review? (Matt's filter question, 2026-08-16.)

Lineage: the arm-series' queued CHEAP_ALARM design (SERIES_HANDOFF §7):
score a clause by FIX volume from a cheap pass, document-tunedness NONE.
Tested here against the 20 blind-audited modules of semantic_audit.json —
the first labeled set this project has had for the purpose.

Pre-stated decision rule (before any call is made):
  * Rank the 20 modules by the cheap pass's discrepancy count.
  * USABLE as a router iff all 3 defective modules land in the top 8
    (a 40% review budget catching 3/3) — else NOT USABLE, and the per-chunk
    random sample remains the only QC instrument.
  * n=20 with 3 positives is weak power; a pass here upgrades the signal to
    "deploy with a per-chunk miss-rate sample", never to "trust outright".

The cheap calls are BLIND: prompt carries module JSON + span only; the
audit labels enter only at scoring, after all calls return.

Cost: 20 calls x ~$0.002. Run:
  ../../../../../semi-formal-experiment/.venv/bin/python cheap_alarm_probe.py
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "behavior_pilot"))

import corpus_gate      # noqa: E402
import live_pilot       # noqa: E402

LABELS = {
 "l1368_1541_n015": "faithful", "l1542_1706_n001": "faithful",
 "l1707_1973_n019": "faithful", "l171_426_n010": "faithful",
 "l171_426_n029": "faithful", "l1_170_n017": "faithful",
 "l1_170_n033": "faithful", "l1_170_n067": "faithful",
 "l1_170_n080": "faithful", "l4252_4482_n003": "defective",
 "l427_460_n007": "faithful", "l461_608_n001": "faithful",
 "l461_608_n002": "faithful",
 "l1001_1107_n002": "faithful", "l171_426_n015": "faithful",
 "l171_426_n038": "faithful", "l1_170_n046": "defective",
 "l1_170_n072": "faithful", "l2653_2820_n004": "defective",
}

BRIEF = (
 "You review one ASP translation of a specification clause. Compare the "
 "MODULE against the SPAN it translates. List every discrepancy you find "
 "as its own line starting with 'FIX:', covering: normative content the "
 "span states that the module does not encode; content the module asserts "
 "that the span does not state; a status/polarity that mis-renders the "
 "span (preference vs prohibition, conditional vs unconditional, an "
 "exclusivity or exception lost). Quote the decisive words. If the module "
 "is faithful, output exactly 'NO FINDINGS'. Do not propose remedies; "
 "findings only.")


def main():
    gathered = corpus_gate.gather()
    # UNFORCED and roomy, deliberately: reasoning_chars was a perfect
    # format-forcing discriminator in the arm series (185/185 forced = 0) —
    # forcing the critic's output shape removes the thing that diagnoses.
    complete = live_pilot.seat_client(max_tokens=3000)
    complete.client.cfg["model"]["format_forcing"] = "none"
    complete.client.forcing = "none"
    rows = []
    for cid in sorted(LABELS):
        o, span, run = gathered[cid]
        user = ("SPAN (what the module must be faithful to):\n" + span[:6000]
                + "\n\nMODULE:\n" + json.dumps(
                    {k: o.get(k) for k in ("claims", "acts", "concepts",
                                           "ontology", "asserts", "beats",
                                           "defines", "closure", "requires",
                                           "inputs", "forbid_body")},
                    indent=1)[:8000]
                + "\n\nList discrepancies.")
        try:
            env = complete(BRIEF, user)
            text = env.get("text", "") if isinstance(env, dict) else str(env)
            n_fix = len(re.findall(r"^\s*(?:[-*\d.\s]*)FIX:", text, re.M))
            truncated = False
        except Exception as ex:                    # noqa: BLE001
            # A critique that overflows the cap IS an alarm, not a crash:
            # the module provoked more discrepancy-listing than fits.
            if "TRUNCATED" not in repr(ex):
                raise
            text, n_fix, truncated = repr(ex)[:300], 99, True
        rows.append({"id": cid, "fix_count": n_fix, "truncated": truncated,
                     "label": LABELS[cid], "raw": text[:1500]})
        print(f"  {cid:20s} FIX={n_fix:2d}{' (TRUNC)' if truncated else ''}"
              f"  ({LABELS[cid]})")
    rows.sort(key=lambda r: -r["fix_count"])
    top8 = {r["id"] for r in rows[:8]}
    defect = {c for c, l in LABELS.items() if l == "defective"}
    caught = defect & top8
    usable = caught == defect
    c = complete.client
    out = {"rule": "usable iff all 3 defective in top-8 by fix_count",
           "top8": sorted(top8), "defective_caught": sorted(caught),
           "usable": usable, "spent_usd": round(c.spent_usd, 6),
           "rows": rows}
    with open(os.path.join(HERE, "cheap_alarm_probe.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(f"\ndefective in top-8: {len(caught)}/3  -> "
          f"{'USABLE (deploy with per-chunk miss-rate sample)' if usable else 'NOT USABLE (random sampling stands)'}")
    print(f"spent ${c.spent_usd:.4f}; wrote cheap_alarm_probe.json")


if __name__ == "__main__":
    main()
