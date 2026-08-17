#!/usr/bin/env python3
"""THE LICENCE CONTROL — one call per clause, TURN 1 ONLY, 17 clauses.

The manipulation is ONE PARAGRAPH.  The same 17 clauses, the same 39,959-char
production system block, the same provider, model and temperature as arm A and
arm A-prime.  The only difference anywhere is a single licence question appended
to the USER block, which is where it must live: the system block is gated
byte-identical and cannot carry it.  See PREREG.md, signed before the first call.

⛔ THREE GATES, all of which must hold or nothing is sent.
  (1) The four production prompt files must still assemble to arm A's system
      block `3a66c5f5...4c34c`, 39,959 chars.  Refuse otherwise.
  (2) Every one of the 17 USER blocks must equal arm A's user block for that
      clause with EXACTLY the licence question inserted -- nothing else moved,
      added or dropped.  Both sides are rebuilt here and compared by
      reconstruction, not by eyeball.  A gate on the system block alone would
      miss a corpus row having moved, or a second variable having crept into
      the template.
  (3) The worst case of the exact set about to be sent, plus this arm's on-disk
      ledger, must be <= CAP_USD.  Priced up front because the calls run in
      parallel and a per-call gate cannot serialise against itself.

⚠️ `translate.Client._log_usage` runs BEFORE `_check_envelope`, so a call that
truncates or returns empty IS BILLED and IS logged to `usage.jsonl` while
raising and writing no arm record.  This structure copies `arm_aprime/
run_aprime.py` exactly, including that hole; it is not patched, because arms A
and A' ran with it and a control that patches it is not running their harness.
Spend is reconciled against `usage.jsonl` by `reconcile.py`, never against
`out/`.  The ledger line count is stamped into `ledger_window.json` immediately
before the send so the reconciliation window is exact even with another arm
running concurrently.

USAGE
    run_licence.py --dry     verify all three gates, price the 17, send nothing
    run_licence.py --live    send the 17 turn-1 calls in parallel
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

CONFIG = os.path.join(HERE, "config_licence.json")
ARM_A_CONFIG = os.path.join(PHASE1, "resolve_runs", "graph_v2",
                            "config_corpus_all.json")
OUT = os.path.join(HERE, "out")
LEDGER = os.path.abspath(os.path.join(
    PHASE1, "..", "..", "..", "semi-formal-experiment", "usage.jsonl"))

#: HARD CAP in measured dollars, owner-set for this arm: the brief's ceiling.
#: MEASURED comparable -- arm A' billed $0.021107 for 12 calls on the same block
#: and model ($0.00176/call); arm A's 17 turn-1 calls measured $0.02971.  This
#: arm is expected at ~$0.030 and its gated worst case is ~$0.045.
CAP_USD = 0.06

MAX_WORKERS = 5

ARM_A_SHA256 = ("3a66c5f54277fbea1c6a8f030435f0c3083d480954b2f6ee3aeef5f1"
                "f4e4c34c")
ARM_A_CHARS = 39959


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
    """GATE 1 — the block sent must be the production block, to the byte."""
    h = hashlib.sha256(system.encode()).hexdigest()
    if len(system) != ARM_A_CHARS or h != ARM_A_SHA256:
        raise SystemExit(
            f"REFUSED: system block is {len(system)}c sha256 {h}, not the "
            f"production {ARM_A_CHARS}c {ARM_A_SHA256}. A control that does not "
            f"send the production block controls nothing. Nothing sent.")
    return h


def gate_users(cfg, rows, picks):
    """GATE 2 — rebuild each user block from ARM A's OWN config and require that
    this arm's block is arm A's with EXACTLY the licence question inserted.

    The check is by RECONSTRUCTION: delete the question from this arm's block and
    require byte equality with arm A's.  An eyeball diff would pass a template
    that also, say, dropped the cross-references.  Restores `translate._BASE` for
    the caller, since `load_config` mutates it as a side effect."""
    q = cfg["_licence_question"]
    idk = cfg["corpus"]["id_key"]
    mine = {r[idk]: translate.build_user(r, rows, cfg)[0] for r in picks}
    a_cfg = translate.load_config(ARM_A_CONFIG)
    a_rows = translate.load_corpus(a_cfg)
    a_idk = a_cfg["corpus"]["id_key"]
    a_by = {r[a_idk]: r for r in a_rows}
    gate_system(translate.build_system(a_cfg))
    bad = []
    for cid, u in mine.items():
        if cid not in a_by:
            bad.append(f"{cid}: absent from arm A's corpus")
            continue
        au = translate.build_user(a_by[cid], a_rows, a_cfg)[0]
        if u.count(q) != 1:
            bad.append(f"{cid}: licence question appears {u.count(q)}x, want 1")
            continue
        stripped = u.replace("\n" + q + "\n\n", "\n", 1)
        if stripped != au:
            bad.append(f"{cid}: block minus the question is not arm A's "
                       f"({len(stripped)}c vs {len(au)}c)")
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
                if isinstance(obj, dict) and "_lc_cost_usd" in obj:
                    total += float(obj["_lc_cost_usd"] or 0.0)
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
        rec = {"clause_id": cid, "_lc_cost_usd": cost,
               "_lc_sha1_raw": hashlib.sha1(raw.encode()).hexdigest(),
               "_lc_t_start": t0, "_lc_t_end": time.time(),
               "usage": env.get("usage"), "floor": floor,
               "module": obj if floor["parsed"] else None}
        with open(os.path.join(OUT, f"{cid}.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(rec, fh, indent=1)
    return cid, cost, floor


def stamp_window():
    """The exact ledger line count immediately before the send, so the
    reconciliation window is not guessed with another arm possibly running."""
    n = sum(1 for _ in open(LEDGER, encoding="utf-8"))
    p = os.path.join(HERE, "ledger_window.json")
    rec = {"lines_before_send": n, "first_new_line": n + 1, "ts": time.time()}
    if os.path.exists(p):                    # a retry must not move the window
        prev = json.load(open(p, encoding="utf-8"))
        rec = {**prev, "retry_windows": prev.get("retry_windows", []) + [
            {"lines_before_send": n, "ts": time.time()}]}
    json.dump(rec, open(p, "w", encoding="utf-8"), indent=1)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--only", nargs="*", default=None,
                    help="re-send only these clause ids (authorised retries "
                         "for calls that RAISED; see PREREG.md §8)")
    a = ap.parse_args(argv)

    cfg, rows, prov, system = setup(CONFIG)
    picks = selected(rows, cfg)
    sha = gate_system(system)
    users = gate_users(cfg, rows, picks)

    idk = cfg["corpus"]["id_key"]
    # the cap gate prices EXACTLY the set about to be sent, not always all 17 --
    # strictly tighter, never looser.
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
    qlen = len(cfg["_licence_question"])

    print(f"provider {prov.name}  model {prov.model}  "
          f"max_tokens {prov.max_tokens}  temp "
          f"{cfg['model'].get('temperature')}  price {prov.price_per_mtok}")
    print(f"GATE 1 OK: system block {len(system)}c sha256 {sha} == production's.")
    print(f"GATE 2 OK: all {len(picks)} user blocks == arm A's + exactly the "
          f"{qlen}-char licence question, nothing else.")
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
    win = stamp_window()
    lock = threading.Lock()
    print(f"ledger window opens at line {win['first_new_line']}")
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
