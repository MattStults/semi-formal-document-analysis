#!/usr/bin/env python3
"""ARM D — the model applies the review list TO ITS OWN DRAFT, across turns.

Design, grounds and pre-registered branches: `PREREG.md`. Read it first.

⚠️ WHAT IS REUSED, AND WHAT IS NOT.  `ds_opus_loop/loop.py` already owns the
turn boundary this arm needs, and it is IMPORTED, not reimplemented:
`loop.adjudicate_floor` (the mandatory `schema.validate_all` +
`checks.run_checks` floor), `loop.worst_case` (the per-turn cost arithmetic),
`loop.clause_row` and `loop._Args`.  What this file adds is the only thing
`loop.py` does not have: a round is TWO messages, an unforced IDENTIFY call
that returns eleven verdict lines and no JSON, then a forced REPAIR call that
returns the module under production's own `response_format`.  The reason that
split exists at all is in `PREREG.md` §3.1 — with `additionalProperties: false`
and `strict: true` there is no field a per-entry verdict could live in, and the
verdict is the measurement.

⛔ `ds_opus_loop/out/` is READ ONLY here.  Turn 1 is arm A's stored draft,
resumed byte-identically; every byte this arm writes lands under
`_debug_gen11/selfreview_arm/out/`.

USAGE
    run_armd.py --dry                price every planned call, send nothing
    run_armd.py --live --round 1     IDENTIFY then REPAIR, 17 clauses
    run_armd.py --live --round 2     the conditional second repair round
"""
import argparse
import concurrent.futures as cf
import copy
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

CONFIG = os.path.join(HERE, "config_armd.json")
OUT = os.path.join(HERE, "out")
MSG = os.path.join(HERE, "messages")
ARM_A_OUT = os.path.join(PHASE1, "_debug_gen11", "ds_opus_loop", "out")

#: HARD CAP in measured dollars, owner-set for this experiment.  Not a config
#: knob.  A ROUND is priced at its worst case in full, against the on-disk
#: ledger, before any of its calls is sent — the calls run in parallel and a
#: per-call gate cannot serialise against itself.
CAP_USD = 0.12

#: arm A's recorded system-block sha256 (`ds_opus_loop`, and the arm-A row of
#: `list_in_prompt/RESULT.md`).  The run REFUSES to send if it has moved.
ARM_A_SHA256 = ("3a66c5f54277fbea1c6a8f030435f0c3083d480954b2f6ee3aee"
                "f5f1f4e4c34c")

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


def free_client(prov, cfg):
    """The IDENTIFY call only: format forcing OFF.  `PREREG.md` §3.1 — the
    verdict cannot be returned under a strict schema with no field for it, and
    the alternatives were rejected by name.  The REPAIR call is built from the
    UNMODIFIED cfg and keeps production's `response_format`."""
    c = copy.deepcopy(cfg)
    c["model"]["format_forcing"] = "none"
    return translate.Client(prov, c)


def msg(name):
    return open(os.path.join(MSG, name), encoding="utf-8").read().strip()


def arm_a_turn1(cid):
    """Arm A's stored turn-1 draft, read-only.  Its user block is rebuilt from
    the config and checked against arm A's own transcript, so a resumed
    transcript that differed by one byte refuses instead of measuring a
    different prompt."""
    p = os.path.join(ARM_A_OUT, f"{cid}.transcript.json")
    st = json.load(open(p, encoding="utf-8"))
    return st["transcript"][0]["content"], st["turns"][0]["raw"]


def state_path(cid):
    return os.path.join(OUT, f"{cid}.armd.json")


def load_state(cid):
    p = state_path(cid)
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return {"clause_id": cid, "calls": []}


def ledger_spent(clauses):
    """Measured dollars, from the call records on disk — never from a counter
    in memory, which a crashed invocation would lose while the money stayed
    spent."""
    return sum(float(c.get("cost_usd") or 0.0)
               for cid in clauses for c in load_state(cid)["calls"])


def transcript_for(cid, cfg, rows, rnd):
    """The exact message list for this clause at this round, and the number of
    prior completions in it (what `loop.worst_case` prices)."""
    user1, draft1 = arm_a_turn1(cid)
    row = loop.clause_row(rows, cfg, cid)
    rebuilt, _, _ = translate.build_user(row, rows, cfg)
    if rebuilt != user1:
        raise SystemExit(f"REFUSED: rebuilt turn-1 user block for {cid} is not "
                         f"byte-identical to arm A's. Nothing sent.")
    t = [{"role": "user", "content": user1},
         {"role": "assistant", "content": draft1},
         {"role": "user", "content": msg("review_d.md")}]
    if rnd == 1:
        return t, 1
    st = load_state(cid)
    by = {c["phase"]: c for c in st["calls"]}
    for phase in ("identify", "repair"):
        if phase not in by:
            raise SystemExit(f"{cid}: round 2 needs the round-1 {phase} call.")
    t.append({"role": "assistant", "content": by["identify"]["raw"]})
    t.append({"role": "user", "content": msg("repair_d.md")})
    t.append({"role": "assistant", "content": by["repair"]["raw"]})
    t.append({"role": "user", "content": msg("round2_d.md")})
    return t, 3


def price_round(cfg, rows, prov, system, clauses, rnd):
    """Worst case for every call this round would send, priced in full before
    any of them goes out."""
    total = 0.0
    for cid in clauses:
        t, prior = transcript_for(cid, cfg, rows, rnd)
        head = "".join(m["content"] for m in t)
        # `head` already holds every prior completion verbatim, so the
        # `n_prior_completions` argument is 0 here and is NOT `prior` — passing
        # both would bill each stored draft twice.  It is 1 only for the REPAIR
        # call, whose IDENTIFY completion does not exist yet and is therefore
        # priced at a full `max_tokens`.
        del prior
        if rnd == 1:
            total += loop.worst_case(system, head, prov, cfg, 0)          # id
            total += loop.worst_case(system, head + msg("repair_d.md"),
                                     prov, cfg, 1)                        # rep
        else:
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
    with open(state_path(cid), "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=1)


def one_clause(cid, cfg, rows, prov, system, rnd, lock):
    row = loop.clause_row(rows, cfg, cid)
    t, _ = transcript_for(cid, cfg, rows, rnd)
    out = []

    if rnd == 1:
        env = free_client(prov, cfg).complete_messages(system, t)
        with lock:
            record(cid, "identify", env, None, len(t))
        out.append(("identify", float(env.get("cost_usd") or 0.0), None))
        t = t + [{"role": "assistant", "content": env["text"]},
                 {"role": "user", "content": msg("repair_d.md")}]
        phase = "repair"
    else:
        phase = "round2"

    env = translate.Client(prov, cfg).complete_messages(system, t)
    floor, _ = loop.adjudicate_floor(env["text"], row, cfg, rows)
    with lock:
        record(cid, phase, env, floor, len(t))
        if floor["parsed"]:
            with open(os.path.join(OUT, f"{cid}.{phase}.module.json"), "w",
                      encoding="utf-8") as fh:
                json.dump(json.loads(env["text"]), fh, indent=1)
    out.append((phase, float(env.get("cost_usd") or 0.0), floor))
    return cid, out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--round", type=int, default=1)
    a = ap.parse_args(argv)

    cfg, rows, prov, system = setup()
    clauses = list(cfg["select"]["clause_ids"])
    spent = ledger_spent(clauses)
    grand = price_round(cfg, rows, prov, system, clauses, a.round)

    print(f"provider {prov.name}  model {prov.model}  "
          f"max_tokens {prov.max_tokens}  price {prov.price_per_mtok} $/Mtok")
    print(f"system block {len(system)}c  sha256 VERIFIED == arm A "
          f"({ARM_A_SHA256[:8]}…)")
    print(f"round {a.round}: {len(clauses)} clauses, worst case ${grand:.4f}; "
          f"measured so far ${spent:.4f}; cap ${CAP_USD:.2f}")
    if spent + grand > CAP_USD:
        raise SystemExit(f"REFUSED: ${spent:.4f} + ${grand:.4f} worst case "
                         f"would cross the ${CAP_USD:.2f} cap. Nothing sent.")
    if not a.live:
        print("WITHIN cap. nothing sent (--dry).")
        return 0

    os.makedirs(OUT, exist_ok=True)
    done_phase = "repair" if a.round == 1 else "round2"
    todo = [c for c in clauses
            if done_phase not in {x["phase"] for x in load_state(c)["calls"]}]
    print(f"sending {len(todo)} of {len(clauses)} clauses "
          f"({len(clauses) - len(todo)} already on disk)")

    lock = threading.Lock()
    with cf.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(one_clause, c, cfg, rows, prov, system, a.round,
                          lock): c for c in todo}
        for f in cf.as_completed(futs):
            try:
                cid, res = f.result()
            except Exception as exc:                          # noqa: BLE001
                print(f"  !! {futs[f]}: {exc!r}")
                continue
            for phase, cost, floor in res:
                if floor is None:
                    print(f"  {cid} {phase}: ${cost:.5f}")
                else:
                    print(f"  {cid} {phase}: ${cost:.5f} "
                          f"parsed={floor['parsed']} "
                          f"outcome={floor['outcome']} "
                          f"repair_needed={floor.get('repair_needed')} "
                          f"breaches={len(floor['breaches'])} "
                          f"findings={len(floor['checks'])}")
    print(f"TOTAL MEASURED ${ledger_spent(clauses):.5f}  cap ${CAP_USD:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
