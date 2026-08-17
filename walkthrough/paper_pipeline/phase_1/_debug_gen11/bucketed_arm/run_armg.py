#!/usr/bin/env python3
"""ARM G — CHECKS DELIVERED IN LENS-GROUPED BUCKETS, PHRASED AS PROCEDURES.

Design, grounds and pre-registered branches: `PREREG.md`. Read it first.

⚠️ WHAT IS REUSED. `ds_opus_loop/loop.py` owns the turn boundary and the
mandatory floor, and `selfreview_arm/run_armd.py` owns the paired-resume gate.
Both are IMPORTED or copied verbatim, not reinvented: `loop.adjudicate_floor`,
`loop.worst_case`, `loop.clause_row`, `loop._Args`.

WHAT IS DIFFERENT FROM ARM D, and it is the only thing under test:
  * a round is ONE call, not two.  There is no IDENTIFY step and no verdict
    field anywhere.  Arm F measured that asking this model for a per-check
    verdict returns `applies_and_handled` 102/102, so a verdict field is a
    rubber stamp and is deliberately absent.  The deliverable of every turn is
    the MODULE, under production's own `response_format`.
  * the eleven entries are split across FOUR turns of 2-3 entries, grouped by
    lens, and each is phrased as a PROCEDURE that enumerates something in the
    module rather than as a question about it.

⛔ `ds_opus_loop/out/` and `selfreview_arm/` are READ ONLY here. Turn 1 is arm
A's stored draft, resumed byte-identically; every byte this arm writes lands
under `_debug_gen11/bucketed_arm/`.

USAGE
    run_armg.py --dry                    price every planned bucket, send nothing
    run_armg.py --live --bucket 1        run bucket 1 on all 9 clauses
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
sys.path.insert(0, os.path.join(PHASE1, "_debug_gen11", "ds_opus_loop"))

import translate                                              # noqa: E402
import loop                                                   # noqa: E402

CONFIG = os.path.join(HERE, "config_armg.json")
OUT = os.path.join(HERE, "out")
MSG = os.path.join(HERE, "messages")
ARM_A_OUT = os.path.join(PHASE1, "_debug_gen11", "ds_opus_loop", "out")

#: HARD CAP in measured dollars, owner-set for this experiment. Not a config
#: knob. A BUCKET is priced at its worst case in full, against the on-disk
#: ledger, before any of its calls is sent.
CAP_USD = 0.12

#: arm A's recorded system-block sha256. The run REFUSES to send if it moved.
ARM_A_SHA256 = ("3a66c5f54277fbea1c6a8f030435f0c3083d480954b2f6ee3aee"
                "f5f1f4e4c34c")

N_BUCKETS = 4
MAX_WORKERS = 5


def setup():
    cfg = translate.load_config(CONFIG)
    rows = translate.load_corpus(cfg)
    prov = translate.resolve_provider(cfg, loop._Args())
    system = translate.build_system(cfg)
    sha = hashlib.sha256(system.encode()).hexdigest()
    if sha != ARM_A_SHA256:
        raise SystemExit(
            f"REFUSED: system block sha256 {sha} != arm A's {ARM_A_SHA256}. "
            f"The prompt is not the one that produced the turn-1 drafts this "
            f"arm resumes. Nothing sent.")
    return cfg, rows, prov, system


PREAMBLE = None


def msg(n):
    """Bucket n's user message: the shared preamble plus bucket n's steps.
    The preamble is repeated every turn on purpose — it carries the
    'a turn that changes nothing is expected' instruction, which is the
    over-editing guard this design needs at every turn, not only the first."""
    global PREAMBLE
    if PREAMBLE is None:
        PREAMBLE = open(os.path.join(MSG, "_preamble.md"),
                        encoding="utf-8").read().strip()
    body = open(os.path.join(MSG, f"bucket{n}.md"), encoding="utf-8").read()
    return PREAMBLE + "\n\n---\n\n" + body.strip()


def arm_a_turn1(cid):
    p = os.path.join(ARM_A_OUT, f"{cid}.transcript.json")
    st = json.load(open(p, encoding="utf-8"))
    return st["transcript"][0]["content"], st["turns"][0]["raw"]


def state_path(cid):
    return os.path.join(OUT, f"{cid}.armg.json")


def load_state(cid):
    p = state_path(cid)
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return {"clause_id": cid, "calls": []}


def ledger_spent(clauses):
    """Measured dollars from the call records on disk. ⚠️ `loop.py` has a
    MEASURED ledger hole — a raising call (truncation) spends and writes no
    record — so this figure is a LOWER BOUND and RESULT.md reconciles it
    against `semi-formal-experiment/usage.jsonl` as well."""
    return sum(float(c.get("cost_usd") or 0.0)
               for cid in clauses for c in load_state(cid)["calls"])


def transcript_for(cid, cfg, rows, bucket):
    """The exact message list for this clause at this bucket. Every earlier
    bucket's module is in it verbatim: this is one growing conversation, which
    is what 'across turns' means here."""
    user1, draft1 = arm_a_turn1(cid)
    row = loop.clause_row(rows, cfg, cid)
    rebuilt, _, _ = translate.build_user(row, rows, cfg)
    if rebuilt != user1:
        raise SystemExit(f"REFUSED: rebuilt turn-1 user block for {cid} is not "
                         f"byte-identical to arm A's. Nothing sent.")
    t = [{"role": "user", "content": user1},
         {"role": "assistant", "content": draft1}]
    by = {c["phase"]: c for c in load_state(cid)["calls"]}
    for b in range(1, bucket):
        t.append({"role": "user", "content": msg(b)})
        if f"bucket{b}" not in by:
            raise SystemExit(f"{cid}: bucket {bucket} needs bucket {b} on disk.")
        t.append({"role": "assistant", "content": by[f"bucket{b}"]["raw"]})
    t.append({"role": "user", "content": msg(bucket)})
    return t


def price_bucket(cfg, rows, prov, system, clauses, bucket, only_todo=True):
    total = 0.0
    for cid in clauses:
        if only_todo and f"bucket{bucket}" in {
                c["phase"] for c in load_state(cid)["calls"]}:
            continue
        t = transcript_for(cid, cfg, rows, bucket)
        head = "".join(m["content"] for m in t)
        total += loop.worst_case(system, head, prov, cfg, 0)
    return total


def record(cid, phase, env, floor, transcript_len):
    st = load_state(cid)
    st["calls"] = [c for c in st["calls"] if c["phase"] != phase]
    raw = env["text"]
    st["calls"].append({
        "phase": phase, "raw": raw,
        "sha1": hashlib.sha1(raw.encode()).hexdigest(),
        "cost_usd": float(env.get("cost_usd") or 0.0),
        "usage": env.get("usage"), "messages_sent": transcript_len,
        "floor": floor,
    })
    st["calls"].sort(key=lambda c: c["phase"])
    with open(state_path(cid), "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=1)


def one_clause(cid, cfg, rows, prov, system, bucket, lock):
    row = loop.clause_row(rows, cfg, cid)
    t = transcript_for(cid, cfg, rows, bucket)
    phase = f"bucket{bucket}"
    env = translate.Client(prov, cfg).complete_messages(system, t)
    floor, _ = loop.adjudicate_floor(env["text"], row, cfg, rows)
    with lock:
        record(cid, phase, env, floor, len(t))
        if floor["parsed"]:
            with open(os.path.join(OUT, f"{cid}.{phase}.module.json"), "w",
                      encoding="utf-8") as fh:
                json.dump(json.loads(env["text"]), fh, indent=1)
    return cid, float(env.get("cost_usd") or 0.0), floor


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--bucket", type=int, default=1)
    a = ap.parse_args(argv)

    cfg, rows, prov, system = setup()
    clauses = list(cfg["select"]["clause_ids"])
    spent = ledger_spent(clauses)
    print(f"provider {prov.name}  model {prov.model}  "
          f"max_tokens {prov.max_tokens}  price {prov.price_per_mtok} $/Mtok")
    print(f"system block {len(system)}c  sha256 VERIFIED == arm A "
          f"({ARM_A_SHA256[:8]}…)")
    print(f"measured so far ${spent:.5f}; cap ${CAP_USD:.2f}")

    if a.dry:
        # Price ALL FOUR buckets, using each bucket's module slot filled with
        # the largest arm-A draft as a stand-in for the not-yet-existing
        # completions. That is what `n_prior_completions` in `loop.worst_case`
        # is for: an unmaterialised completion is priced at a full max_tokens.
        run = 0.0
        for b in range(1, N_BUCKETS + 1):
            tot = 0.0
            for cid in clauses:
                user1, draft1 = arm_a_turn1(cid)
                head = user1 + draft1 + "".join(msg(x) for x in range(1, b + 1))
                tot += loop.worst_case(system, head, prov, cfg, b - 1)
            run += tot
            print(f"  bucket {b}: {len(clauses)} clauses worst case ${tot:.5f}"
                  f"   cumulative ${run:.5f}")
        print(f"WORST CASE ALL FOUR BUCKETS ${run:.5f} vs cap ${CAP_USD:.2f}"
              f"  -> {'WITHIN' if spent + run <= CAP_USD else 'OVER'}")
        return 0

    grand = price_bucket(cfg, rows, prov, system, clauses, a.bucket)
    print(f"bucket {a.bucket}: worst case ${grand:.5f}")
    if spent + grand > CAP_USD:
        raise SystemExit(f"REFUSED: ${spent:.5f} + ${grand:.5f} worst case "
                         f"would cross the ${CAP_USD:.2f} cap. Nothing sent.")
    if not a.live:
        print("WITHIN cap. nothing sent (no --live).")
        return 0

    os.makedirs(OUT, exist_ok=True)
    todo = [c for c in clauses
            if f"bucket{a.bucket}" not in {x["phase"]
                                           for x in load_state(c)["calls"]}]
    print(f"sending {len(todo)} of {len(clauses)} clauses")
    lock = threading.Lock()
    with cf.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(one_clause, c, cfg, rows, prov, system, a.bucket,
                          lock): c for c in todo}
        for f in cf.as_completed(futs):
            try:
                cid, cost, floor = f.result()
            except Exception as exc:                          # noqa: BLE001
                print(f"  !! {futs[f]}: {exc!r}")
                continue
            print(f"  {cid} bucket{a.bucket}: ${cost:.5f} "
                  f"parsed={floor['parsed']} outcome={floor['outcome']} "
                  f"repair_needed={floor.get('repair_needed')} "
                  f"breaches={len(floor['breaches'])} "
                  f"findings={len(floor['checks'])}")
    print(f"TOTAL MEASURED ${ledger_spent(clauses):.5f}  cap ${CAP_USD:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
