#!/usr/bin/env python3
"""Granularity smoke test, portable across models (Matt's item 1,
2026-08-11).

Replays the two dispatches that exposed the DeepSeek build's failure modes
against ANY openai-compatible model, N draws each, and scores every draw
against ABSOLUTE bands (no golden needed):

  A. leaf L561-800 (the c2/c3 child-2 dispatch): the draw that produced 969
     byte-identical duplicate nodes. Bands: duplicates ~0 after dedupe
     accounting, density 0.05-0.7 nodes/line.
  B. leaf L1-170 (the c1 dispatch): the draw that extracted ZERO needs.
     Band: needs > 0 (this span's chain-of-command region is linkage-rich).

Usage:
  python3 smoke_granularity.py --yes                       # DeepSeek (default)
  python3 smoke_granularity.py --model Qwen/Qwen3-235B-A22B-Instruct-2507-tput --yes
  python3 smoke_granularity.py --model moonshotai/Kimi-K2-Instruct --yes

Output: probes/smoke_<model-slug>/report.json + a verdict table. A model
whose draws sit in-band needs no prompt customization; out-of-band tells
you WHICH lesson its variant of the brief needs.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.abspath(os.path.join(
    HERE, "..", "..", "..", "..", "..", "semi-formal-experiment")))

import recurse_driver as R  # noqa: E402


def unwind_fixture():
    """Dispatch D: the ROOT UNWIND reconstructed from the completed ds2
    tree (Matt 2026-08-11: evaluate the heaviest dispatch per-model without
    a pipeline run). Prompt built by the SAME unwind_inputs the driver
    uses. Bands: reply under ~8K chars (the size contract), parses, zero
    apply_decisions errors, resolutions subset of provided names."""
    division = json.load(open(os.path.join(HERE, "runs", "ds2",
                                           "division.json")))
    children = [json.load(open(os.path.join(HERE, "runs", "ds2", c,
                                            "graph.json")))
                for c in ("c1", "c2", "c3")]
    _, _, provides, dangling, _, user = R.unwind_inputs(
        division, children, 1, 4692, {})
    return user, provides, dangling


def score_unwind(text, provides):
    try:
        o = R.parse_json_reply(text)
    except Exception as exc:
        return {"error": f"parse: {exc}"[:120]}
    res = o.get("resolutions", [])
    bad = [r for r in res if isinstance(r, dict)
           and (r.get("rename_to") or r.get("name")) not in provides]
    return {"reply_chars": len(text),
            "resolutions": len(res), "bad_targets": len(bad),
            "judgment_calls": len(o.get("judgment_calls", [])),
            "verdicts": {
                "size": "PASS" if len(text) < 8000 else f"FAIL ({len(text)})",
                "targets": "PASS" if not bad else f"FAIL ({len(bad)})",
                "economy": "PASS" if len(o.get("judgment_calls", [])) <= 12
                           else "FAIL"}}


def dispatches():
    d23 = json.load(open(os.path.join(HERE, "runs", "ds2", "c2", "c3",
                                      "division.json")))
    seeds_a = d23.get("seed_vocabulary", [])
    root = json.load(open(os.path.join(HERE, "runs", "ds2",
                                       "division.json")))
    seeds_b = root.get("seed_vocabulary", [])
    return [("A_dup_leaf", 561, 800, seeds_a),
            ("B_zero_needs_leaf", 1, 170, seeds_b)]


def score(g, lo, hi):
    dups = R.dedupe_nodes(g)
    n = len(g.get("nodes", []))
    span = hi - lo + 1
    density = n / span
    needs = sum(len(x.get("needs", [])) for x in g.get("nodes", []))
    verdicts = {
        "duplicates": "PASS" if dups <= 2 else f"FAIL ({dups} exact dups)",
        "density": ("PASS" if 0.05 <= density <= 0.7
                    else f"FAIL ({density:.2f}/line)"),
        "linkage": "PASS" if needs > 0 else "FAIL (zero needs)",
    }
    return {"nodes": n, "dups_removed": dups, "density": round(density, 3),
            "needs": needs, "verdicts": verdicts}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None,
                    help="together model id (default: driver_config's)")
    ap.add_argument("--n", type=int, default=2)
    ap.add_argument("--max-tokens", type=int, default=32768)
    ap.add_argument("--yes", action="store_true")
    args = ap.parse_args()

    cfg = json.load(open(os.path.join(HERE, "driver_config.json")))
    model = args.model or cfg["model"]["model"]
    slug = model.split("/")[-1][:40]
    out = os.path.join(HERE, "probes", f"smoke_{slug}")
    os.makedirs(out, exist_ok=True)
    lines = R.load_doc(os.path.join(
        HERE, "..", "..", "..", "..", "..", "specs", "openai-model-spec",
        "model_spec.md"))

    est = args.n * 2 * (40000 / 4 / 1e6 * cfg["price_per_mtok"][0]
                        + args.max_tokens / 1e6 * cfg["price_per_mtok"][1])
    print(f"smoke on {model}: {args.n} draws x 2 dispatches, "
          f"worst-case ~${est:.2f} at DeepSeek prices (other models may "
          f"price higher)")
    if not args.yes:
        print("dry run: pass --yes to spend")
        return

    prov = R.T.Provider(
        name=f"smoke-{slug}", kind="openai-compatible", model=model,
        base_url=cfg["model"]["base_url"],
        api_key_env=cfg["model"]["api_key_env"],
        temperature=cfg["model"].get("temperature", 0.2),
        max_tokens=args.max_tokens, price_per_mtok=cfg["price_per_mtok"])
    client = R.GraphClient(prov, {"model": dict(
        cfg["model"], model=model, format_forcing="json_object",
        usage_log=cfg["model"].get("usage_log", "DEFAULT"))})
    client.max_cost_usd = 0.50
    drv = R.Driver({"model": dict(cfg["model"],
                                  max_tokens=args.max_tokens)},
                   client, lines, out)

    report = {"model": model, "dispatches": {}}
    for name, lo, hi, seeds in dispatches():
        extra = ("Reply with the Phase L graph.json object "
                 "(nodes/uncovered/judgment_calls). Node ids are prefixed "
                 f"L{lo}-{hi}_.")
        user = drv.dispatch_block("L", lo, hi, seeds, extra)
        rows = []
        for i in range(args.n):
            client.reply_schema = ("leaf_graph", R.LEAF_SCHEMA)
            try:
                env = client.complete(drv.brief, user)
                g = R.parse_json_reply(env["text"])
                row = score(g, lo, hi)
                errs = R.validate_leaf(g, lo, hi, lines)
                row["validation_errors"] = len(errs)
            except Exception as exc:        # noqa: BLE001
                row = {"error": str(exc)[:160]}
            rows.append(row)
            print(f"  {name} draw {i}: {json.dumps(row)[:180]}")
        report["dispatches"][name] = rows
    # dispatch D: the root unwind
    u_user, u_provides, _ = unwind_fixture()
    rows = []
    for i in range(args.n):
        client.reply_schema = R.unwind_schema(20, 700)
        try:
            env = client.complete(drv.brief, u_user)
            row = score_unwind(env["text"], u_provides)
        except Exception as exc:            # noqa: BLE001
            row = {"error": str(exc)[:140]}
        rows.append(row)
        print(f"  D_root_unwind draw {i}: {json.dumps(row)[:170]}")
    report["dispatches"]["D_root_unwind"] = rows
    report["spent_usd"] = round(getattr(client, "spent_usd", 0.0), 4)
    R.write_json(os.path.join(out, "report.json"), report)
    print(f"spent ${report['spent_usd']:.4f} -> {out}/report.json")


if __name__ == "__main__":
    main()
