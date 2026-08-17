#!/usr/bin/env python3
"""JOB 2 — re-judge the stored seat prompts with a DIFFERENT model.

⭐ THE POINT IS THE INSTRUMENT, NOT THE ANSWER. The baseline's judge is
`deepseek-ai/DeepSeek-V4-Flash-0731`, the same model that wrote the
translations it graded. This re-runs a sample of the **byte-identical stored
prompts** through `seats.judge` — same brief, same validation, same reply
parsing — with only the model changed.

⛔ THE PROMPTS ARE NOT REBUILT. `out/raw/<clause>.<seat>.json:prompt` is the
user message exactly as the baseline sent it, and `seats.BRIEFS[seat]` is the
system message off the same `seats.py`. Rebuilding a prompt would measure a
different instrument and the comparison would be worthless.

Spend: printed first, gated hard. Provider call is stdlib `urllib` — this repo
takes no vendor SDK (`AGENTS.md` §Environment), and the `anthropic` package is
not installed in its venv.

Usage:
  python3 crossjudge.py            # estimate only, no call
  python3 crossjudge.py --live     # estimate, gate, then call
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
GEN11 = os.path.dirname(HERE)
PHASE1 = os.path.dirname(GEN11)
sys.path.insert(0, PHASE1)

import seats  # noqa: E402

RAW = os.path.join(GEN11, "stage4_baseline", "out", "raw")
OUT = os.path.join(HERE, "crossjudge_raw")

MODEL = "claude-sonnet-4-5"
#: $ per million tokens, (input, output) — Sonnet-tier list price.
PRICE = (3.0, 15.0)
CAP_USD = 0.25
SEATS = ("4b", "4c")
N_CLAUSES = 10                     # PREREG amendment; see PREREG.md
CHARS_PER_TOKEN = 3.5              # conservative (over-counts input)
OUT_HEADROOM = 1.3                 # vs the DeepSeek reply's measured length


def sample(n=N_CLAUSES):
    """Deterministic, spread across the sorted id space. NOT hand-picked."""
    cl = sorted({f.split(".")[0] for f in os.listdir(RAW)})
    step = len(cl) / n
    return [cl[int(i * step)] for i in range(n)]


def stored(clause, seat):
    return json.load(open(os.path.join(RAW, f"{clause}.{seat}.json"),
                          encoding="utf-8"))


def estimate(clauses):
    tin = tout = 0.0
    for c in clauses:
        for s in SEATS:
            r = stored(c, s)
            tin += (len(seats.BRIEFS[s]) + len(r["prompt"])) / CHARS_PER_TOKEN
            tout += r["out"] * OUT_HEADROOM
    usd = tin * PRICE[0] / 1e6 + tout * PRICE[1] / 1e6
    return {"calls": len(clauses) * len(SEATS), "in_tokens": round(tin),
            "out_tokens": round(tout), "usd": round(usd, 4)}


class Client:
    """`seats.judge`'s client seam, one model, measured spend."""

    def __init__(self, model=MODEL):
        self.model = model
        self.key = os.environ.get("ANTHROPIC_API_KEY")
        self.spent = 0.0
        self.calls = 0
        self.tag = "?"
        os.makedirs(OUT, exist_ok=True)

    def complete_messages(self, system, messages):
        body = {"model": self.model, "max_tokens": 4096, "system": system,
                "messages": messages}
        req = lambda: urllib.request.Request(                 # noqa: E731
            "https://api.anthropic.com/v1/messages",
            json.dumps(body).encode(),
            headers={"x-api-key": self.key,
                     "anthropic-version": "2023-06-01",
                     "Content-Type": "application/json"})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req(), timeout=600) as resp:
                    data = json.load(resp)
                break
            except urllib.error.HTTPError as e:
                detail = e.read().decode()[:400]
                if e.code in (429, 500, 502, 503, 529) and attempt < 3:
                    time.sleep(5 * (attempt + 1))
                    continue
                raise RuntimeError(f"HTTP {e.code}: {detail}") from e
        u = data.get("usage") or {}
        n_in = (u.get("input_tokens") or 0) + \
               (u.get("cache_creation_input_tokens") or 0) + \
               (u.get("cache_read_input_tokens") or 0)
        n_out = u.get("output_tokens") or 0
        cost = n_in * PRICE[0] / 1e6 + n_out * PRICE[1] / 1e6
        self.spent += cost
        self.calls += 1
        text = "".join(b.get("text", "") for b in data.get("content", [])
                       if b.get("type") == "text")
        json.dump({"tag": self.tag, "model": self.model, "in": n_in,
                   "out": n_out, "cost_usd": cost,
                   "stop_reason": data.get("stop_reason"), "text": text},
                  open(os.path.join(OUT, f"{self.tag}.json"), "w",
                       encoding="utf-8"), indent=1, ensure_ascii=False)
        return text


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--n", type=int, default=N_CLAUSES)
    args = ap.parse_args(argv)

    clauses = sample(args.n)
    est = estimate(clauses)
    print(f"model      : {MODEL}   ${PRICE[0]}/${PRICE[1]} per Mtok")
    print(f"sample     : {args.n} clauses x {len(SEATS)} seats = "
          f"{est['calls']} calls")
    print(f"             {clauses}")
    print(f"ESTIMATE   : {est['in_tokens']} in + {est['out_tokens']} out "
          f"= ${est['usd']:.4f}   (cap ${CAP_USD})")
    if est["usd"] > CAP_USD:
        raise SystemExit(f"REFUSED: estimate ${est['usd']:.4f} exceeds the "
                         f"${CAP_USD} cap. Lower --n.")
    if not args.live:
        print("dry run — pass --live to spend")
        return
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("no ANTHROPIC_API_KEY in the environment")

    client = Client()
    rows, failures = [], {}
    for c in clauses:
        for s in SEATS:
            rec = stored(c, s)
            client.tag = f"{c}.{s}"
            try:
                js = seats.judge(s, rec["prompt"],
                                 _ids(c, s), client_factory=lambda: client)
            except Exception as exc:                          # noqa: BLE001
                failures[client.tag] = f"{type(exc).__name__}: {exc}"[:300]
                print(f"  {client.tag}: REFUSED {failures[client.tag][:90]}")
                continue
            for j in js:
                rows.append({"clause": c, "seat": s, "item": j.item,
                             "verdict": j.verdict, "reason": j.reason[:400]})
            print(f"  {client.tag}: {len(js)} judgements  "
                  f"(${client.spent:.4f} so far)")
            if client.spent > CAP_USD:
                print("⛔ CAP REACHED mid-run — stopping")
                break
        else:
            continue
        break
    json.dump({"model": MODEL, "clauses": clauses, "seats": list(SEATS),
               "spent_usd": client.spent, "calls": client.calls,
               "estimate": est, "seat_failures": failures, "rows": rows},
              open(os.path.join(HERE, "crossjudge.json"), "w",
                   encoding="utf-8"), indent=1)
    print(f"\nMEASURED SPEND: ${client.spent:.6f} over {client.calls} calls")
    print(f"judgements: {len(rows)}   seat failures: {len(failures)}")


def _ids(clause, seat):
    """The denominator ids the baseline used for this seat — recovered from
    the stored per-clause report, never rebuilt."""
    rep = json.load(open(os.path.join(GEN11, "stage4_baseline", "out",
                                      "reports", f"{clause}.json"),
                         encoding="utf-8"))
    return tuple(j["item"] for j in rep["seats"][seat])


if __name__ == "__main__":
    main()
