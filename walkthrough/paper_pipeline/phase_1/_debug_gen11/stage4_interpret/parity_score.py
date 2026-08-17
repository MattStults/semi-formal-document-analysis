#!/usr/bin/env python3
"""JOB 2, part 2 — score the cross-model judgements against the baseline's.

Free: re-reads `crossjudge_raw/*.json` (already paid for) and the baseline's
stored replies. No model call.

⚠️ ONE POST-HOC REPAIR, DECLARED. Every Claude reply came back wrapped in a
```json ... ``` markdown fence, so `json.loads` on the raw text refused all 20
seats — the same class of instrument failure as the baseline's 4d refusal
(§4 of BASELINE.md), and on a different model. The fence is stripped here and
**the identical strip is applied to the DeepSeek replies too**, where it is a
no-op (they are already bare JSON). Both sides then go through
`seats.validate_judgements` — the same validation the live run used. Nothing
about a verdict is repaired; only the envelope.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN11 = os.path.dirname(HERE)
PHASE1 = os.path.dirname(GEN11)
sys.path.insert(0, PHASE1)

import seats  # noqa: E402

BASE_RAW = os.path.join(GEN11, "stage4_baseline", "out", "raw")
REPORTS = os.path.join(GEN11, "stage4_baseline", "out", "reports")
NEW_RAW = os.path.join(HERE, "crossjudge_raw")
FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$")


def unfence(text):
    """Strip a markdown code fence if present. A no-op on bare JSON."""
    return FENCE.sub("", FENCE.sub("", text.strip()))


def judged(text, seat, ids):
    data = json.loads(unfence(text))
    js = tuple(seats.Judgement(seat,
                               seats._reply_item(r["item"], tuple(ids), seat),
                               str(r["verdict"]), str(r.get("reason", "")))
               for r in data["judgements"])
    return seats.validate_judgements(seat, tuple(ids), js)


def ids_of(clause, seat):
    rep = json.load(open(os.path.join(REPORTS, f"{clause}.json"),
                         encoding="utf-8"))
    return tuple(j["item"] for j in rep["seats"][seat])


def kappa(pairs, labels):
    n = len(pairs)
    if not n:
        return None
    agree = sum(1 for a, b in pairs if a == b) / n
    pa = {l: sum(1 for a, _ in pairs if a == l) / n for l in labels}
    pb = {l: sum(1 for _, b in pairs if b == l) / n for l in labels}
    exp = sum(pa[l] * pb[l] for l in labels)
    return agree, exp, (agree - exp) / (1 - exp) if exp < 1 else None


DEFECT = {"4b": "unfaithful", "4c": "unlicensed"}
LABELS = {"4b": ("faithful", "unfaithful", "unclear"),
          "4c": ("licensed", "unlicensed", "unclear")}

pairs_by_seat = {"4b": [], "4c": []}
rows, drops = [], []
clauses = sorted({f.split(".")[0] for f in os.listdir(NEW_RAW)})
for c in clauses:
    for s in ("4b", "4c"):
        ids = ids_of(c, s)
        new_raw = json.load(open(os.path.join(NEW_RAW, f"{c}.{s}.json"),
                                 encoding="utf-8"))
        old_raw = json.load(open(os.path.join(BASE_RAW, f"{c}.{s}.json"),
                                encoding="utf-8"))
        try:
            new = {j.item: j.verdict for j in judged(new_raw["text"], s, ids)}
        except Exception as exc:                              # noqa: BLE001
            drops.append((c, s, f"claude: {type(exc).__name__}: {exc}"[:160]))
            continue
        old = {j.item: j.verdict for j in judged(old_raw["text"], s, ids)}
        for iid in ids:
            if iid not in new or iid not in old:
                drops.append((c, s, f"{iid} missing from one side"))
                continue
            pairs_by_seat[s].append((old[iid], new[iid]))
            rows.append({"clause": c, "seat": s, "item": iid,
                         "deepseek": old[iid], "claude": new[iid]})

json.dump(rows, open(os.path.join(HERE, "parity_rows.json"), "w"), indent=1)

print(f"clauses {len(clauses)}   items scored {len(rows)}   drops {len(drops)}")
for d in drops:
    print("   DROP", d)
print()
pooled = []
for s in ("4b", "4c"):
    p = pairs_by_seat[s]
    pooled += p
    a, e, k = kappa(p, LABELS[s])
    d_old = sum(1 for x, _ in p if x == DEFECT[s])
    d_new = sum(1 for _, y in p if y == DEFECT[s])
    u_old = sum(1 for x, _ in p if x == "unclear")
    u_new = sum(1 for _, y in p if y == "unclear")
    print(f"seat {s}: n={len(p)}  agreement {a:.3f}  expected {e:.3f}  "
          f"kappa {k:.3f}")
    print(f"         defect verdicts: DeepSeek {d_old}  Claude {d_new}   "
          f"(direction {d_new - d_old:+d})")
    print(f"         unclear:         DeepSeek {u_old}  Claude {u_new}")
    import collections
    cm = collections.Counter(p)
    for (x, y), n in sorted(cm.items(), key=lambda kv: -kv[1]):
        if x != y:
            print(f"         DISAGREE  DeepSeek {x:11s} -> Claude {y:11s} {n}")
    print()

# pooled kappa over a common 3-way alphabet: pass / defect / unclear
def collapse(v):
    if v in ("faithful", "licensed"):
        return "pass"
    if v in ("unfaithful", "unlicensed"):
        return "defect"
    return "unclear"


cp = [(collapse(a), collapse(b)) for a, b in pooled]
a, e, k = kappa(cp, ("pass", "defect", "unclear"))
print(f"POOLED (pass/defect/unclear): n={len(cp)}  agreement {a:.3f}  "
      f"kappa {k:.3f}")
d_old = sum(1 for x, _ in cp if x == "defect")
d_new = sum(1 for _, y in cp if y == "defect")
print(f"  defect rate: DeepSeek {d_old}/{len(cp)} = {d_old/len(cp):.3f}   "
      f"Claude {d_new}/{len(cp)} = {d_new/len(cp):.3f}")

# binary collapse: defect vs not-defect (the headline's own question)
bp = [(("defect" if x == "defect" else "not"),
       ("defect" if y == "defect" else "not")) for x, y in cp]
a, e, k = kappa(bp, ("defect", "not"))
print(f"BINARY (defect vs not):        n={len(bp)}  agreement {a:.3f}  "
      f"kappa {k:.3f}")

# clause-level: would the headline change?
import collections
per = collections.defaultdict(lambda: {"deepseek": 0, "claude": 0})
for r in rows:
    if r["deepseek"] in DEFECT.values():
        per[r["clause"]]["deepseek"] += 1
    if r["claude"] in DEFECT.values():
        per[r["clause"]]["claude"] += 1
d_cl = sum(1 for v in per.values() if v["deepseek"])
c_cl = sum(1 for v in per.values() if v["claude"])
print(f"\nclause-level over the {len(per)} sampled clauses (4b+4c only): "
      f"DeepSeek calls {d_cl} defective, Claude calls {c_cl}")
