"""Measure what one extraction batch actually costs, per model.

Estimating output size does not work for reasoning models: reasoning is billed
as completion tokens and dominates. A smoke run on gpt-oss-20b produced 339
characters of content against 8,000 billed completion tokens — a ~24:1
overhead ratio that no a-priori estimate would have produced.

So: send one real batch to each candidate, read the usage block, and price
from measured tokens. Reports cost per usable batch, since a model that
returns nothing costs infinity regardless of its rate card.

  .venv/bin/python calibrate.py --models sol,terra,luna,kimi --live
"""
from __future__ import annotations

import argparse, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from providers import ProviderConfig, LiveClient  # noqa: E402

USAGE_LOG = os.path.join(HERE, "usage.jsonl")


def batch_prompt(batch_size=14):
    """First extraction batch, exactly as extract_section.py would send it."""
    out = subprocess.run(
        [os.path.join(HERE, ".venv/bin/python"), os.path.join(HERE, "extract_section.py"),
         "--print-prompt", "--batch-size", str(batch_size)],
        capture_output=True, text=True, cwd=HERE).stdout
    # take the first SYSTEM/USER pair; batches are printed in order
    i = out.find("USER")
    j = out.find("SYSTEM", i)          # start of batch 2, if present
    return out[:i], out[i:j if j > 0 else len(out)]


def price(cfg, usage):
    p = getattr(cfg, "price_per_mtok", None)
    if not p or usage.get("prompt_tokens") is None:
        return None
    return (usage["prompt_tokens"] / 1e6 * p[0]
            + (usage.get("completion_tokens") or 0) / 1e6 * p[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="sol,terra,luna,kimi")
    ap.add_argument("--batch-size", type=int, default=14)
    ap.add_argument("--batches", type=int, default=3,
                    help="batches per extraction run, for projection")
    ap.add_argument("--runs", type=int, default=2, help="extraction runs, for projection")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--providers", default=os.path.join(HERE, "providers.json"))
    args = ap.parse_args()

    cfgs = {c.name: c for c in ProviderConfig.load_all(args.providers)}
    system, user = batch_prompt(args.batch_size)
    print(f"batch prompt: system {len(system)} chars, user {len(user)} chars\n")
    if not args.live:
        print("dry run — pass --live to measure. No call made.")
        return

    rows = []
    for name in [m.strip() for m in args.models.split(",") if m.strip()]:
        cfg = cfgs.get(name)
        if cfg is None:
            print(f"  {name:8s} UNKNOWN provider"); continue
        if not cfg.key():
            print(f"  {name:8s} no key in ${cfg.api_key_env}"); continue
        t0 = time.time()
        try:
            env = LiveClient(cfg).complete_envelope(system, user, usage_log=USAGE_LOG)
        except Exception as e:
            print(f"  {name:8s} FAILED: {type(e).__name__}: {str(e)[:90]}")
            rows.append({"model": name, "ok": False, "error": str(e)[:200]}); continue
        dt = time.time() - t0
        u = env["usage"]
        txt, rsn = env["text"], env["reasoning"]
        parses = False
        try:
            s = txt[txt.index("{"):txt.rindex("}") + 1]; json.loads(s); parses = True
        except Exception:
            pass
        c = price(cfg, u)
        rows.append({"model": name, "ok": True, "parses": parses,
                     "truncated": env["truncated"], "finish": env["finish_reason"],
                     "prompt_tokens": u.get("prompt_tokens"),
                     "completion_tokens": u.get("completion_tokens"),
                     "content_chars": len(txt), "reasoning_chars": len(rsn),
                     "seconds": round(dt, 1), "cost_batch": c})
        print(f"  {name:8s} finish={str(env['finish_reason'])[:10]:10s} "
              f"in={u.get('prompt_tokens')} out={u.get('completion_tokens')} "
              f"content={len(txt)}c reasoning={len(rsn)}c "
              f"parses={parses} {dt:.0f}s "
              f"${c:.3f}" if c is not None else "")

    print("\n=== cost per batch, and projected full extraction run ===")
    print(f"{'model':8s} {'in':>7s} {'out':>7s} {'ratio':>6s} {'parses':>7s} "
          f"{'$/batch':>9s} {'$/run':>8s} {'$/spike':>8s}")
    for r in rows:
        if not r.get("ok"):
            print(f"{r['model']:8s}  FAILED"); continue
        ratio = ""
        if r["content_chars"]:
            ratio = f"{r['reasoning_chars']/max(1,r['content_chars']):.1f}x"
        cb = r["cost_batch"]
        run = cb * args.batches if cb is not None else None
        spike = run * args.runs if run is not None else None
        print(f"{r['model']:8s} {r['prompt_tokens'] or 0:7d} {r['completion_tokens'] or 0:7d} "
              f"{ratio:>6s} {str(r['parses']):>7s} "
              f"{('$%.3f' % cb) if cb is not None else 'price?':>9s} "
              f"{('$%.2f' % run) if run is not None else '?':>8s} "
              f"{('$%.2f' % spike) if spike is not None else '?':>8s}")
    print("\n$/spike = extraction only (batches x runs). Baseline runs are extra.")
    print("A model whose output does not parse has unbounded effective cost.")
    json.dump(rows, open(os.path.join(HERE, "calibration.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
