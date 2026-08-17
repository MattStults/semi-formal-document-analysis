#!/usr/bin/env python3
"""ARM A-PRIME — the NULL-MANIPULATION REPLICATE.  TURN 1 ONLY.

The manipulation is the EMPTY manipulation: the same 17 clauses, the same
39,959-char arm A system block, the same user blocks, the same provider, model
and temperature.  Every difference from arm A is draw-to-draw noise and nothing
else.  See PREREG.md, signed before the first call.

⛔ THREE GATES, all of which must hold or nothing is sent.
  (1) The four production prompt files must still assemble to arm A's system
      block `3a66c5f5...4c34c`, 39,959 chars.  Refuse otherwise.
  (2) Every one of the 17 USER blocks must be BYTE-IDENTICAL to the block arm A
      built from its own config.  Both are rebuilt here and compared.  A prompt
      gate on the system block alone would miss a corpus row having moved.
  (3) The worst case of all 17 calls, plus this arm's on-disk ledger, must be
      <= CAP_USD.  Priced up front because the calls run in parallel and a
      per-call gate cannot serialise against itself.

⚠️ `translate.Client._log_usage` runs BEFORE `_check_envelope`, so a call that
truncates or returns empty IS BILLED and IS logged to `usage.jsonl` while
raising and writing no arm record.  This structure copies `examples_arm/
run_armc.py` exactly, including that hole; it is not patched, because arm A ran
with it and the null must run with it too.  Spend is reconciled against
`usage.jsonl` afterwards by `reconcile.py`, never against `out/`.

USAGE
    run_aprime.py --dry     verify all three gates, price the 17, send nothing
    run_aprime.py --live    send the 17 turn-1 calls in parallel
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)

import translate                                              # noqa: E402
import schema                                                 # noqa: E402
import checks                                                 # noqa: E402

CONFIG = os.path.join(HERE, "config_aprime.json")
ARM_A_CONFIG = os.path.join(PHASE1, "resolve_runs", "graph_v2",
                            "config_corpus_all.json")
OUT = os.path.join(HERE, "out")

#: HARD CAP in measured dollars, owner-set for this arm.  Not a config knob.
#: Arm A's turn-1 spend on these same 17 clauses is MEASURED at $0.02971, so
#: one replicate is expected to land there and a SECOND replicate would cross
#: this cap — which is why PREREG.md refuses the second one on arithmetic.
CAP_USD = 0.05

MAX_WORKERS = 5

ARM_A_SHA256 = ("3a66c5f54277fbea1c6a8f030435f0c3083d480954b2f6ee3aeef5f1"
                "f4e4c34c")
ARM_A_CHARS = 39959
JOIN = "\n\n---\n\n"


class _Args:
    provider = None
    model = None
    max_tokens = None


def setup(config):
    cfg = translate.load_config(config)
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


def gate_system(system):
    """GATE 1 — the block sent must be arm A's, to the byte."""
    h = hashlib.sha256(system.encode()).hexdigest()
    if len(system) != ARM_A_CHARS or h != ARM_A_SHA256:
        raise SystemExit(
            f"REFUSED: system block is {len(system)}c sha256 {h}, not arm A's "
            f"{ARM_A_CHARS}c {ARM_A_SHA256}. A null replicate of a prompt that "
            f"is not arm A's is not a null replicate. Nothing sent.")
    return h


def gate_users(cfg, rows, picks):
    """GATE 2 — rebuild each user block from ARM A's OWN config and require
    byte equality.  Restores `translate._BASE` for the caller, since
    `load_config` mutates it as a side effect."""
    idk = cfg["corpus"]["id_key"]
    mine = {r[idk]: translate.build_user(r, rows, cfg)[0] for r in picks}
    a_cfg = translate.load_config(ARM_A_CONFIG)
    a_rows = translate.load_corpus(a_cfg)
    a_idk = a_cfg["corpus"]["id_key"]
    a_by = {r[a_idk]: r for r in a_rows}
    a_sys = translate.build_system(a_cfg)
    gate_system(a_sys)
    bad = []
    for cid, u in mine.items():
        if cid not in a_by:
            bad.append(f"{cid}: absent from arm A's corpus")
            continue
        au = translate.build_user(a_by[cid], a_rows, a_cfg)[0]
        if au != u:
            bad.append(f"{cid}: user block differs from arm A's ({len(au)}c "
                       f"vs {len(u)}c)")
    translate.load_config(CONFIG)          # restore _BASE for the live run
    if bad:
        raise SystemExit("REFUSED: " + "; ".join(bad) + ". Nothing sent.")
    return mine


def worst_case(system, user, prov, cfg):
    """One turn's worst case, same arithmetic as `translate.estimate_cost`."""
    cpt = float(cfg["cost"]["chars_per_token"])
    in_tok = (len(system) + len(user)) / cpt
    pin, pout = prov.price_per_mtok
    return (in_tok / 1e6) * pin + (prov.max_tokens / 1e6) * pout


def ledger_spent():
    """Measured dollars this arm has already spent, from the records on disk —
    never a counter in memory, which a crashed run would lose while the money
    stayed spent.  Under-counts by exactly the `_log_usage`-before-
    `_check_envelope` hole; `reconcile.py` closes that against usage.jsonl."""
    total = 0.0
    if os.path.isdir(OUT):
        for f in sorted(os.listdir(OUT)):
            if f.endswith(".json") and not f.endswith(".raw.json"):
                try:
                    obj = json.load(open(os.path.join(OUT, f),
                                         encoding="utf-8"))
                except Exception:                             # noqa: BLE001
                    continue
                if isinstance(obj, dict) and "_aprime_cost_usd" in obj:
                    total += float(obj["_aprime_cost_usd"] or 0.0)
    return total


def adjudicate_floor(raw, row, cfg, rows):
    """The MANDATORY mechanical floor on every draft. NOTHING in this arm is
    read span-first; this and `measure.py` are the only readers."""
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


def one(cid, row, rows, cfg, prov, system, user, lock):
    t0 = time.time()
    client = translate.Client(prov, cfg)
    env = client.complete_messages(system, [{"role": "user", "content": user}])
    raw = env["text"]
    cost = float(env.get("cost_usd") or 0.0)
    floor, obj = adjudicate_floor(raw, row, cfg, rows)
    with lock:
        with open(os.path.join(OUT, f"{cid}.raw.json"), "w",
                  encoding="utf-8") as fh:
            fh.write(raw)
        rec = {"clause_id": cid, "_aprime_cost_usd": cost,
               "_aprime_sha1_raw": hashlib.sha1(raw.encode()).hexdigest(),
               "_aprime_t_start": t0, "_aprime_t_end": time.time(),
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
    ap.add_argument("--only", nargs="*", default=None,
                    help="re-send only these clause ids (authorised retries "
                         "for calls that RAISED; see PREREG.md)")
    a = ap.parse_args(argv)

    cfg, rows, prov, system = setup(CONFIG)
    picks = selected(rows, cfg)
    sha = gate_system(system)
    users = gate_users(cfg, rows, picks)

    idk = cfg["corpus"]["id_key"]
    # AMENDMENT 2 (PREREG.md): the cap gate prices EXACTLY the set about to be
    # sent, not always all 17. Strictly tighter, never looser -- the figure
    # gated on is the real worst case of the real send.
    todo = [r for r in picks
            if not os.path.exists(os.path.join(OUT, f"{r[idk]}.json"))]
    if a.only is not None:
        want = set(a.only)
        unknown = want - {r[idk] for r in picks}
        if unknown:
            raise SystemExit(f"--only names non-arm clauses: {sorted(unknown)}")
        todo = [r for r in picks if r[idk] in want]

    grand = sum(worst_case(system, users[r[idk]], prov, cfg) for r in picks)
    send = sum(worst_case(system, users[r[idk]], prov, cfg) for r in todo)
    spent = ledger_spent()

    print(f"provider {prov.name}  model {prov.model}  "
          f"max_tokens {prov.max_tokens}  temp "
          f"{cfg['model'].get('temperature')}  price {prov.price_per_mtok}")
    print(f"GATE 1 OK: system block {len(system)}c sha256 {sha} == arm A's.")
    print(f"GATE 2 OK: all {len(picks)} user blocks byte-identical to arm A's.")
    print(f"all {len(picks)} clauses worst case ${grand:.4f}; "
          f"THIS SEND {len(todo)} clauses worst case ${send:.4f}; "
          f"recorded so far ${spent:.4f}; cap ${CAP_USD:.2f}")
    if spent + send > CAP_USD:
        raise SystemExit(f"REFUSED: ${spent:.4f} + ${send:.4f} worst case "
                         f"would cross the ${CAP_USD:.2f} cap. Nothing sent.")
    print("GATE 3 OK.")
    if not a.live:
        print("WITHIN cap. nothing sent (--dry).")
        return 0

    os.makedirs(OUT, exist_ok=True)
    lock = threading.Lock()
    print(f"sending {len(todo)} of {len(picks)} "
          f"({len(picks) - len(todo)} already on disk)")
    fails = []
    with cf.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(one, r[idk], r, rows, cfg, prov, system,
                          users[r[idk]], lock): r[idk] for r in todo}
        for f in cf.as_completed(futs):
            try:
                cid, cost, floor = f.result()
            except Exception as exc:                          # noqa: BLE001
                fails.append((futs[f], repr(exc)))
                print(f"  !! {futs[f]}: {exc!r}  ⚠️ MAY HAVE BEEN BILLED — "
                      f"reconcile against usage.jsonl")
                continue
            print(f"  {cid}: ${cost:.5f} parsed={floor['parsed']} "
                  f"outcome={floor['outcome']} "
                  f"repair_needed={floor.get('repair_needed')} "
                  f"breaches={len(floor['breaches'])} "
                  f"findings={len(floor['checks'])}")
    print(f"TOTAL RECORDED ${ledger_spent():.5f}  cap ${CAP_USD:.2f}  "
          f"raised={len(fails)}")
    for cid, e in fails:
        print("  RAISED", cid, e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
