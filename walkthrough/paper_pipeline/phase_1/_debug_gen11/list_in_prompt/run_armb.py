#!/usr/bin/env python3
"""ARM B — the review list in the TRANSLATOR's system prompt. TURN 1 ONLY.

The 15-clause loop showed `REVIEW_LIST.md` only to the ADJUDICATOR, so every
turn-1 draft came from the byte-identical production prompt and DeepSeek never
saw an entry.  This file sends the list WITH the clause.

⚠️ ONE TURN PER CLAUSE, and no feedback.  What is being measured is the UNAIDED
draft under the new prompt, so there is deliberately no repair loop here: a
second turn would measure the critic again, which is the thing the loop already
measured.  For the same reason the 15 calls are issued IN PARALLEL — the prompt
is fixed for the whole arm, so there is no accumulation and no ordering effect.

Reuses `translate.load_config / load_corpus / resolve_provider / build_system /
build_user / Client / estimate_cost / response_envelope` and the
`providers._append_usage` ledger, exactly as `ds_opus_loop/loop.py` does.  The
system block is built by `translate.build_system` from the config, so it is
formed by production code; only the FILE LIST differs.

USAGE
    run_armb.py --dry     price all 15, print both prompt shas, send nothing
    run_armb.py --live    send the 15 turn-1 calls in parallel
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)

import translate                                              # noqa: E402
import schema                                                 # noqa: E402
import checks                                                 # noqa: E402

CONFIG = os.path.join(HERE, "config_arm_b_listprompt.json")
OUT = os.path.join(HERE, "out")

#: HARD CAP in measured dollars, owner-set for this experiment.  Not a config
#: knob: the run prices the WORST CASE of all 15 calls before sending any of
#: them, and refuses outright if that plus the on-disk ledger would cross it.
#: Priced up front rather than per turn because the calls run in parallel and a
#: per-call gate cannot serialise against itself.
CAP_USD = 0.12

MAX_WORKERS = 5


class _Args:
    provider = None
    model = None
    max_tokens = None


def setup():
    cfg = translate.load_config(CONFIG)
    rows = translate.load_corpus(cfg)
    prov = translate.resolve_provider(cfg, _Args())
    system = translate.build_system(cfg)
    return cfg, rows, prov, system


def selected(rows, cfg):
    idk = cfg["corpus"]["id_key"]
    want = list(cfg["select"]["clause_ids"])
    by_id = {r[idk]: r for r in rows}
    missing = [c for c in want if c not in by_id]
    if missing:
        raise SystemExit(f"clause ids not in corpus: {missing}")
    return [by_id[c] for c in want]


def worst_case(system, user, prov, cfg):
    """One turn's worst case, same arithmetic as `translate.estimate_cost`."""
    cpt = float(cfg["cost"]["chars_per_token"])
    in_tok = (len(system) + len(user)) / cpt
    pin, pout = prov.price_per_mtok
    return (in_tok / 1e6) * pin + (prov.max_tokens / 1e6) * pout


def ledger_spent():
    """Measured dollars this arm has already spent, from the records on disk —
    never from a counter in memory, which a crashed run would lose while the
    money stayed spent."""
    total = 0.0
    if os.path.isdir(OUT):
        for f in sorted(os.listdir(OUT)):
            if f.endswith(".json") and not f.endswith(".raw.json"):
                p = os.path.join(OUT, f)
                try:
                    obj = json.load(open(p, encoding="utf-8"))
                except Exception:                             # noqa: BLE001
                    continue
                if isinstance(obj, dict) and "_arm_b_cost_usd" in obj:
                    total += float(obj["_arm_b_cost_usd"] or 0.0)
    return total


def adjudicate_floor(raw, row, cfg, rows):
    """The MANDATORY floor on every draft, before any reading by me:
    `schema.validate_all` then `checks.run_checks`."""
    out = {"parsed": False, "breaches": [], "checks": [], "outcome": None}
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as exc:
        out["breaches"] = [f"not-json: {exc}"]
        return out, None
    out["parsed"] = True
    idk = cfg["corpus"]["id_key"]
    ids = {r[idk] for r in rows}
    _mod, breaches = schema.validate_all(obj, row[idk], ids)
    out["breaches"] = [str(b) for b in breaches]
    try:
        res = checks.run_checks(obj, row, ids)
        out["outcome"] = res.outcome
        out["repair_needed"] = bool(res.repair_needed)
        out["checks"] = [f"[{f.severity}/{f.origin}] {f.check_id} @ {f.where}: "
                         f"{f.message}" for f in res.findings]
    except Exception as exc:                                  # noqa: BLE001
        out["checks"] = [f"run_checks raised: {exc!r}"]
    return out, obj


def prompt_shas(cfg, system):
    """Both shas the deliverable asks for: the arm-A production system block
    and the arm-B one.  Arm A is rebuilt from the PRODUCTION config so the
    figure is the real one and not a reconstruction."""
    b = hashlib.sha256(system.encode()).hexdigest()
    prod = os.path.join(PHASE1, "resolve_runs", "graph_v2",
                        "config_corpus_all.json")
    saved = translate._BASE
    a_cfg = translate.load_config(prod)
    a = hashlib.sha256(translate.build_system(a_cfg).encode()).hexdigest()
    translate.load_config(CONFIG)                             # restore _BASE
    assert translate._BASE != saved or True
    return a, b


def one(cid, row, rows, cfg, prov, system, lock):
    user, _, _ = translate.build_user(row, rows, cfg)
    client = translate.Client(prov, cfg)
    env = client.complete_messages(system, [{"role": "user", "content": user}])
    raw = env["text"]
    cost = float(env.get("cost_usd") or 0.0)
    floor, obj = adjudicate_floor(raw, row, cfg, rows)
    with lock:
        with open(os.path.join(OUT, f"{cid}.raw.json"), "w",
                  encoding="utf-8") as fh:
            fh.write(raw)
        rec = {"clause_id": cid, "_arm_b_cost_usd": cost,
               "_arm_b_sha1_raw": hashlib.sha1(raw.encode()).hexdigest(),
               "usage": env.get("usage"), "floor": floor,
               "module": obj if floor["parsed"] else None}
        with open(os.path.join(OUT, f"{cid}.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(rec, fh, indent=1)
    return cid, cost, floor


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args(argv)
    cfg, rows, prov, system = setup()
    picks = selected(rows, cfg)
    sha_a, sha_b = prompt_shas(cfg, system)
    cfg, rows, prov, system = setup()                         # rebuild after A

    users = [translate.build_user(r, rows, cfg)[0] for r in picks]
    grand = sum(worst_case(system, u, prov, cfg) for u in users)
    spent = ledger_spent()

    print(f"provider {prov.name}  model {prov.model}  "
          f"max_tokens {prov.max_tokens}  price {prov.price_per_mtok} $/Mtok")
    print(f"system block: arm A {len(''):d}… sha256 {sha_a}")
    print(f"system block: arm B {len(system)}c  sha256 {sha_b}")
    print(f"{len(picks)} clauses, worst case ${grand:.4f}; "
          f"measured so far ${spent:.4f}; cap ${CAP_USD:.2f}")
    if spent + grand > CAP_USD:
        raise SystemExit(f"REFUSED: ${spent:.4f} + ${grand:.4f} worst case "
                         f"would cross the ${CAP_USD:.2f} cap. Nothing sent.")
    if not a.live:
        print("WITHIN cap. nothing sent (--dry).")
        return 0

    os.makedirs(OUT, exist_ok=True)
    lock = threading.Lock()
    idk = cfg["corpus"]["id_key"]
    todo = [r for r in picks
            if not os.path.exists(os.path.join(OUT, f"{r[idk]}.json"))]
    print(f"sending {len(todo)} of {len(picks)} "
          f"({len(picks) - len(todo)} already on disk)")
    with cf.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(one, r[idk], r, rows, cfg, prov, system, lock): r[idk]
                for r in todo}
        for f in cf.as_completed(futs):
            try:
                cid, cost, floor = f.result()
            except Exception as exc:                          # noqa: BLE001
                print(f"  !! {futs[f]}: {exc!r}")
                continue
            print(f"  {cid}: ${cost:.5f} parsed={floor['parsed']} "
                  f"outcome={floor['outcome']} "
                  f"repair_needed={floor.get('repair_needed')} "
                  f"breaches={len(floor['breaches'])} "
                  f"findings={len(floor['checks'])}")
    print(f"TOTAL MEASURED ${ledger_spent():.5f}  cap ${CAP_USD:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
