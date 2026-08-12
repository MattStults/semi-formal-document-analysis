#!/usr/bin/env python3
"""Phase U live probe: run the driver's REAL unwind path (prompt build,
model call with UNWIND_SCHEMA forcing, apply_decisions with full
re-verification, repair loop) on the stored c21 fixtures, and compare the
result to the Haiku tree's stored c21/graph.json name-free.

This is the one phase no live probe had exercised before the full-build
go/no-go (2026-08-10). Uses Driver.unwind itself -- zero drift from the
production path; the probe directory stands in for the tree workdir.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.abspath(os.path.join(
    HERE, "..", "..", "..", "..", "..", "semi-formal-experiment")))

import recurse_driver as R  # noqa: E402

NODE = "c21"


def main():
    if "--yes" not in sys.argv:
        print("dry run: pass --yes to spend (~$0.01-0.03)")
    division = json.load(open(os.path.join(HERE, "recurse", NODE,
                                           "division.json")))
    children = [json.load(open(os.path.join(HERE, "recurse", NODE + suf,
                                            "graph.json")))
                for suf in ("1", "2", "3")]
    expected = json.load(open(os.path.join(HERE, "recurse", NODE,
                                           "graph.json")))
    lo, hi = 171, 796          # c2's child 1 span, the c21 dispatch

    cfg = json.load(open(os.path.join(HERE, "driver_config.json")))
    lines = R.load_doc(os.path.join(
        HERE, "..", "..", "..", "..", "..", "specs", "openai-model-spec",
        "model_spec.md"))
    out = os.path.join(HERE, "probes", "c21_U")
    os.makedirs(out, exist_ok=True)
    if os.path.exists(os.path.join(out, "graph.json")):
        os.remove(os.path.join(out, "graph.json"))

    prov = R.T.Provider(
        name="graph-probe", kind="openai-compatible",
        model=cfg["model"]["model"], base_url=cfg["model"]["base_url"],
        api_key_env=cfg["model"]["api_key_env"],
        temperature=cfg["model"].get("temperature", 0.0),
        max_tokens=cfg["model"].get("max_tokens", 16384),
        price_per_mtok=cfg["price_per_mtok"])
    client = R.GraphClient(prov, {"model": dict(
        cfg["model"], format_forcing="json_object",
        usage_log=cfg["model"].get("usage_log", "DEFAULT"))})
    client.max_cost_usd = 0.25
    if "--yes" not in sys.argv:
        return

    drv = R.Driver(cfg, client, lines, out)
    g = drv.unwind(division, children, lo, hi, out)

    def stats(graph):
        provs = {R.nm(p) for n in graph["nodes"] for p in n.get("provides", [])}
        needs = [R.nm(d) for n in graph["nodes"] for d in n.get("needs", [])]
        return {"nodes": len(graph["nodes"]),
                "needs": len(needs),
                "dangling": len([x for x in needs if x not in provs])}

    got, want = stats(g), stats(expected)
    print("DeepSeek unwind:", got)
    print("Haiku stored   :", want)
    print(f"spent ${client.spent_usd:.4f} over {client.calls} calls")
    R.write_json(os.path.join(out, "report.json"),
                 {"got": got, "expected": want,
                  "spent_usd": round(client.spent_usd, 4)})


if __name__ == "__main__":
    main()
