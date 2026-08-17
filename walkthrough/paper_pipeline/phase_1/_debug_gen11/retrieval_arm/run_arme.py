#!/usr/bin/env python3
"""ARM E — the review list RETRIEVED PER CLAUSE, in the translator's prompt.
TURN 1 ONLY.

Arms B and C shipped ALL 20 entries as static prose: 0/15 defect-free
out-of-sample, 0/17 in-sample, 83-87% of conclusion-changing defects named by an
entry the model was holding.  Those arms cannot separate "instruction cannot
reach this content" from "the 2-4 entries that mattered were buried under the 16
that did not".  THIS arm ships only what `selector.py` retrieves for the clause.

⚠️ THE SYSTEM BLOCK'S sha256 DIFFERS PER CLAUSE BY CONSTRUCTION.  That is the
arm.  What is held byte-identical instead, and PROVEN before any send:

  * the four shared prompt files are arm B's, read-only, concatenated by
    production code (`translate.build_system`) in arm B's order;
  * `assert_assembly_matches_arm_b()` rebuilds arm B's system block from those
    same four files plus the FULL 13.6 KB list and checks its sha256 against
    arm B's recorded 04560828... .  If that matches, then arm E's per-clause
    block differs from arm B's in the LIST TEXT AND NOTHING ELSE -- same files,
    same order, same '\\n\\n---\\n\\n' joiner, same strip;
  * every entry body shipped is a verbatim byte slice of arm B's list.  The one
    exception is E05, fixed per PREREG.md section 3, and it is diffed in SHAS.json.

Reuses `translate.load_config / load_corpus / resolve_provider / build_system /
build_user / Client / response_envelope` and the `providers._append_usage`
ledger, exactly as `ds_opus_loop/loop.py` and `run_insample.py` do.  Deviation
from loop.py, stated: loop.py is one-clause-per-invocation because it carries an
adjudicated multi-turn transcript.  Arm E is turn 1 with no feedback, so the
parallel single-turn shape of `run_insample.py` -- itself a descendant of
loop.py using the identical translate.* surface -- is what is reused, and it is
what makes arm E protocol-identical to the arm it is paired against.

USAGE
    run_arme.py --dry     price all 17, prove the assembly, send nothing
    run_arme.py --live    send the 17 turn-1 calls in parallel
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
sys.path.insert(0, HERE)

import translate                                              # noqa: E402
import schema                                                 # noqa: E402
import checks                                                 # noqa: E402
import selector                                               # noqa: E402

CONFIG = os.path.join(HERE, "config_arme.json")
OUT = os.path.join(HERE, "out")
FULL_LIST = os.path.join(HERE, "..", "list_in_prompt", "promptsB",
                         "40_review_list.md")

#: Arm B's / arm C's assembled system-block sha256, on record in
#: ../list_in_prompt_insample/run_insample.py.  Reproducing it from arm E's own
#: four files + the full list is the proof that only the list text differs.
ARM_B_SHA = "045608289e6e60a6c7ab327cfb10625a034bd38080af88f0043f757b59517917"

JOIN = "\n\n---\n\n"

#: HARD CAP in measured dollars, owner-set for this experiment.  The run prices
#: the WORST CASE of all 17 calls before sending any of them and refuses
#: outright if that plus the on-disk ledger would cross it.  Priced up front
#: because the calls run in parallel and a per-call gate cannot serialise
#: against itself.
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
    base = translate.build_system(cfg)          # the four shared files only
    return cfg, rows, prov, base


def assert_assembly_matches_arm_b(base):
    full = open(FULL_LIST, encoding="utf-8").read().strip()
    rebuilt = base + JOIN + full
    got = hashlib.sha256(rebuilt.encode()).hexdigest()
    if got != ARM_B_SHA:
        raise SystemExit(
            "REFUSED: arm E's four-file base + the FULL list does not "
            f"reproduce arm B's system block.\n  got      {got}\n"
            f"  expected {ARM_B_SHA}\n"
            "Something other than the list text differs between the arms, and "
            "the comparison would be unattributable. Nothing sent.")
    return got


def per_clause_system(base, cid):
    p = os.path.join(HERE, "promptsE", cid, "40_review_list.md")
    return base + JOIN + open(p, encoding="utf-8").read().strip()


def selected(rows, cfg):
    idk = cfg["corpus"]["id_key"]
    want = list(cfg["select"]["clause_ids"])
    by_id = {r[idk]: r for r in rows}
    missing = [c for c in want if c not in by_id]
    if missing:
        raise SystemExit(f"clause ids not in corpus: {missing}")
    return [by_id[c] for c in want]


def worst_case(system, user, prov, cfg):
    cpt = float(cfg["cost"]["chars_per_token"])
    in_tok = (len(system) + len(user)) / cpt
    pin, pout = prov.price_per_mtok
    return (in_tok / 1e6) * pin + (prov.max_tokens / 1e6) * pout


def ledger_spent():
    """Measured dollars this arm has already spent, from the records on disk --
    never from a counter in memory, which a crashed run would lose while the
    money stayed spent."""
    total = 0.0
    if os.path.isdir(OUT):
        for f in sorted(os.listdir(OUT)):
            if f.endswith(".json") and not f.endswith(".raw.json"):
                try:
                    obj = json.load(open(os.path.join(OUT, f),
                                         encoding="utf-8"))
                except Exception:                             # noqa: BLE001
                    continue
                if isinstance(obj, dict) and "_arm_e_cost_usd" in obj:
                    total += float(obj["_arm_e_cost_usd"] or 0.0)
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
        rec = {"clause_id": cid, "_arm_e_cost_usd": cost,
               "_arm_e_sha1_raw": hashlib.sha1(raw.encode()).hexdigest(),
               "_arm_e_system_sha256": hashlib.sha256(system.encode())
               .hexdigest(),
               "_arm_e_system_chars": len(system),
               "_arm_e_selected": [e for _, _, e, _ in selector.select(row)[3]],
               "usage": env.get("usage"), "floor": floor,
               "module": obj if floor["parsed"] else None}
        with open(os.path.join(OUT, f"{cid}.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(rec, fh, indent=1)
    return cid, cost, floor


def write_shas(base, systems, arm_b_sha):
    """Everything a reader needs to reconstruct any clause's prompt exactly."""
    def sha(p):
        return hashlib.sha256(open(p, "rb").read()).hexdigest()
    ent_dir = os.path.join(HERE, "promptsE", "entries")
    rec = {
     "_": "ARM E prompt provenance. The system block differs PER CLAUSE by "
          "construction; these shas pin every part of it.",
     "arm_b_system_sha256_reproduced": arm_b_sha,
     "arm_b_system_sha256_expected": ARM_B_SHA,
     "shared_prompt_files": {
      os.path.basename(f): sha(translate.rel(f))
      for f in translate.load_config(CONFIG)["prompt"]["system_files"]},
     "four_file_base_sha256": hashlib.sha256(base.encode()).hexdigest(),
     "four_file_base_chars": len(base),
     "full_list_sha256": sha(FULL_LIST),
     "entry_files": {f: sha(os.path.join(ent_dir, f))
                     for f in sorted(os.listdir(ent_dir))},
     "e05_note": "E05.md is the ONE entry whose bytes differ from arm B's. "
                 "PREREG.md section 3: a STOP CONDITION and two pre-tests were "
                 "ADDED (nothing deleted) because entry 5 as written was "
                 "measured to manufacture vacuous bodied rules.",
     "selector_sha256": sha(os.path.join(HERE, "selector.py")),
     "prereg_sha256": sha(os.path.join(HERE, "PREREG.md")),
     "per_clause": {
      cid: {"system_sha256": hashlib.sha256(s.encode()).hexdigest(),
            "system_chars": len(s),
            "list_chars": len(s) - len(base) - len(JOIN),
            "selected": sel}
      for cid, (s, sel) in systems.items()},
    }
    p = os.path.join(HERE, "SHAS.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1)
    return p


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args(argv)

    cfg, rows, prov, base = setup()
    arm_b_sha = assert_assembly_matches_arm_b(base)
    picks = selected(rows, cfg)
    idk = cfg["corpus"]["id_key"]

    systems, users = {}, {}
    for r in picks:
        cid = r[idk]
        s = per_clause_system(base, cid)
        systems[cid] = (s, [e for _, _, e, _ in selector.select(r)[3]])
        users[cid] = translate.build_user(r, rows, cfg)[0]

    shas_path = write_shas(base, systems, arm_b_sha)
    cfg, rows, prov, base = setup()                # restore _BASE after write

    grand = sum(worst_case(systems[c][0], users[c], prov, cfg) for c in users)
    spent = ledger_spent()
    print(f"provider {prov.name}  model {prov.model}  "
          f"max_tokens {prov.max_tokens}  price {prov.price_per_mtok} $/Mtok")
    print(f"ASSEMBLY PROVEN: four-file base + FULL list reproduces arm B's "
          f"sha256 {arm_b_sha[:8]}…  -> only the list text differs")
    print(f"four-file base: {len(base)}c")
    for c in cfg["select"]["clause_ids"]:
        s, sel = systems[c]
        print(f"  {c:20s} {len(s):6d}c  list {len(s)-len(base)-len(JOIN):5d}c  "
              f"{'+'.join(sel):20s} sha {hashlib.sha256(s.encode()).hexdigest()[:12]}")
    print(f"shas written -> {shas_path}")
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
    todo = [r for r in picks
            if not os.path.exists(os.path.join(OUT, f"{r[idk]}.json"))]
    print(f"sending {len(todo)} of {len(picks)} "
          f"({len(picks) - len(todo)} already on disk)")
    with cf.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(one, r[idk], r, rows, cfg, prov,
                          systems[r[idk]][0], lock): r[idk] for r in todo}
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
