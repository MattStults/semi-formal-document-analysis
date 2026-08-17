#!/usr/bin/env python3
"""ARM C — the SAME content as arm B's top-evidence entries, rendered as BEFORE/
AFTER WORKED EXAMPLES instead of prose rules.  TURN 1 ONLY.

Two arms have failed.  Arm B put the evidence-ordered review list in the
TRANSLATOR's prompt out-of-sample (0/15 defect-free, 87% of conclusion-changing
defects named by an entry the translator held); the in-sample arm ran the
byte-identical prompt on the 17 clauses the list was measured on (0/17, 83%).
The owner's hypothesis is that the failing variable is FORM: the list is twenty
prose rules and zero demonstrations, and `../routing_criterion/` measured that
in this very prompt a model disregards prose while following a concrete
demonstration.

⛔ THE FIRST FOUR PROMPT FILES ARE COPIES, VERIFIED.  `promptsC/` holds
byte-identical copies of the four production files; `prompt_shas` refuses to
send unless (i) those four still assemble to arm A's 39,959-char block
`3a66c5f5...`, and (ii) the whole five-file block equals arm C's frozen
`b5af1129...`.  Either check failing means the prompt is not the one PREREG.md
was signed against, and nothing is sent.

⚠️ SAME 17 CLAUSES as the in-sample arm, so arm C is paired against BOTH
baselines on identical material: arm A's unaided turn-1 drafts and the prose
arm's.  One turn per clause, no feedback, issued in parallel.

USAGE
    run_armc.py --dry     price all 17, verify both shas, send nothing
    run_armc.py --live    send the 17 turn-1 calls in parallel
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

CONFIG = os.path.join(HERE, "config_armc.json")
OUT = os.path.join(HERE, "out")

#: HARD CAP in measured dollars, owner-set for this experiment.  Not a config
#: knob: the run prices the WORST CASE of all 15 calls before sending any of
#: them, and refuses outright if that plus the on-disk ledger would cross it.
#: Priced up front rather than per turn because the calls run in parallel and a
#: per-call gate cannot serialise against itself.
CAP_USD = 0.08

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
                if isinstance(obj, dict) and "_armc_cost_usd" in obj:
                    total += float(obj["_armc_cost_usd"] or 0.0)
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


ARM_A_SHA256 = ("3a66c5f54277fbea1c6a8f030435f0c3083d480954b2f6ee3aeef5f1"
                "f4e4c34c")
ARM_C_SHA256 = ("b5af1129958a631347c506bfad4fe03f74b0c0cc177fd1b24277727886"
                "f68af5")
JOIN = "\n\n---\n\n"


def prompt_shas(cfg, system):
    """TWO GATES, both of which must hold or nothing is sent.

    (1) The first FOUR prompt files must still assemble to arm A's production
        system block.  Arm C's whole claim is that it is arm A plus one
        appended demonstration block; if a production file has moved by a byte
        the arm is no longer paired with anything.
    (2) The whole five-file block must equal the sha256 recorded in `PREREG.md`
        BEFORE the pre-registration was signed.  Editing the examples after
        seeing a result is the one thing that would make this arm worthless,
        and this is the check that makes it impossible to do by accident.
    """
    files = list(cfg["prompt"]["system_files"])
    if len(files) != 5:
        raise SystemExit(f"REFUSED: expected 5 system files, got {len(files)}")
    parts = [open(translate.rel(f), encoding="utf-8").read().strip()
             for f in files]
    a = hashlib.sha256(JOIN.join(parts[:4]).encode()).hexdigest()
    if a != ARM_A_SHA256:
        raise SystemExit(f"REFUSED: the four production files assemble to {a}, "
                         f"not arm A's {ARM_A_SHA256}. Nothing sent.")
    c = hashlib.sha256(system.encode()).hexdigest()
    if c != ARM_C_SHA256:
        raise SystemExit(f"REFUSED: system block sha256 {c} != the frozen arm "
                         f"C block {ARM_C_SHA256} recorded in PREREG.md before "
                         f"signing. Nothing sent.")
    if system != JOIN.join(parts[:4]) + JOIN + parts[4]:
        raise SystemExit("REFUSED: the block is not armA + JOIN + examples.")
    return a, c


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
        rec = {"clause_id": cid, "_armc_cost_usd": cost,
               "_armc_sha1_raw": hashlib.sha1(raw.encode()).hexdigest(),
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
    sha_a, sha_c = prompt_shas(cfg, system)

    users = [translate.build_user(r, rows, cfg)[0] for r in picks]
    grand = sum(worst_case(system, u, prov, cfg) for u in users)
    spent = ledger_spent()

    print(f"provider {prov.name}  model {prov.model}  "
          f"max_tokens {prov.max_tokens}  price {prov.price_per_mtok} $/Mtok")
    print(f"system block: {len(system)}c  sha256 {sha_c}")
    print(f"VERIFIED: first four files == arm A ({sha_a}); whole block == the "
          f"frozen arm C sha in PREREG.md.")
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
