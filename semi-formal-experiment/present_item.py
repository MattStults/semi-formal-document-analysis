"""Present one blind adjudication item, matching the panel's condition.

Reads human_adjudication/items.json ONLY. Never key.json -- the presenter must not
know what the tool or the panel said (HUMAN_ADJUDICATION_PROTOCOL.md).

Amended 2026-08-05: the panel was given the whole document and told to use its
structure as context, so an item carries its section path and reading position, and
`--context N` shows neighbouring passages on request. What context a decision required
is recorded as data, not treated as a deviation.

Usage:  present_item.py H002 [--context 3]
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import benchmark as B  # noqa: E402

SAFE = ("id", "locator", "quote", "exampleBlock")   # never role/score/verdicts


def universe():
    beh = B.load_true_panel()["helpfulness"]        # same 589-passage universe
    return [{k: p.get(k) for k in SAFE} for p in B.passages(beh, "openai")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("item_id")
    ap.add_argument("--context", type=int, default=0,
                    help="show N passages either side (recorded when used)")
    a = ap.parse_args()

    items = json.load(open(os.path.join(HERE, "human_adjudication", "items.json")))
    item = next(i for i in items if i["item_id"] == a.item_id)
    ps = universe()
    idx = next(k for k, p in enumerate(ps) if p["quote"] == item["passage"])
    me = ps[idx]

    print(f"ITEM {item['item_id']}  ({items.index(item) + 1} of {len(items)})")
    print()
    print(f"BEHAVIOUR: {item['behaviour_name']}")
    print(f"DEFINITION: {item['behaviour_definition']}")
    print()
    print(f"SECTION: {me['locator']}")
    print(f"POSITION: passage {idx + 1} of {len(ps)} in reading order")
    print()
    print("PASSAGE:")
    print(item["passage"])

    if a.context:
        print()
        print(f"--- CONTEXT (requested: {a.context} either side) ---")
        for j in range(max(0, idx - a.context), min(len(ps), idx + a.context + 1)):
            tag = ">>" if j == idx else "  "
            sec = ps[j]["locator"].split(">")[-2:] if ">" in ps[j]["locator"] else [""]
            print(f"{tag} [{j+1}] (§{'>'.join(s.strip() for s in sec)})")
            print(f"     {ps[j]['quote'][:700]}")
            print()


if __name__ == "__main__":
    main()
