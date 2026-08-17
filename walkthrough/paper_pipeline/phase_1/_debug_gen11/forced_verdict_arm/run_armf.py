#!/usr/bin/env python3
"""ARM F — STRUCTURAL COERCION. The review list as REQUIRED OUTPUT FIELDS.

Three arms have now shipped the review list as PROSE and returned nulls: arm B
(15 new clauses, 0 defect-free, 87% of conclusion-changing defects named by an
entry the model held) and the in-sample arm (the same 17 clauses this file
draws, 0 of 17 defect-free, 83%). Neither can tell whether the model READ AND
IGNORED an entry or NEVER ENGAGED it, because nothing in the reply is about the
entries.

This arm changes the MECHANISM, not the text. The production pipeline already
guarantees the reply's shape at generation (`model.format_forcing:
json_schema`); arm F EXTENDS THAT SHAPE with a required `checks` array, one
element per entry, each demanding a quotation, a verdict and an action. A
well-formed module now cannot be produced without answering every check.

⛔ `schema.py` IS GUARD-WATCHED AND IS NOT TOUCHED. `arm_f_schema` deep-copies
`schema.response_format(strict)` and appends one property; the production
function is never patched or shadowed. The returned object has that one key
STRIPPED before the REAL `schema.validate_all` and `checks.run_checks` run on
it, and the strip is proved per clause (`arm_f_schema.strip_proof`): exactly one
top-level key removed, every surviving field identical BY `is` and byte-equal
under re-serialisation.

⚠️ ONE TURN PER CLAUSE, no feedback, issued in parallel — identical protocol to
arm B and the in-sample arm, so the three arms differ in WHERE THE ENTRIES LIVE
and nothing else. The system block here is the PRODUCTION one and a sha gate
refuses to send if it is not.

USAGE
    run_armf.py --dry     price all 17, verify both shas, send nothing
    run_armf.py --live    send the 17 turn-1 calls in parallel
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
import checks as checks_mod                                   # noqa: E402
import arm_f_schema                                           # noqa: E402

CONFIG = os.path.join(HERE, "config_arm_f.json")
OUT = os.path.join(HERE, "out")
PROD_CONFIG = os.path.join(PHASE1, "resolve_runs", "graph_v2",
                           "config_corpus_all.json")

#: HARD CAP in measured dollars, owner-set for this arm. Not a config knob: the
#: run prices the WORST CASE of all 17 calls before sending any of them and
#: refuses outright if that plus the on-disk ledger would cross it. Priced up
#: front rather than per call because the calls run in parallel and a per-call
#: gate cannot serialise against itself.
CAP_USD = 0.10

MAX_WORKERS = 5


class _Args:
    provider = None
    model = None
    max_tokens = None


class ArmFClient(translate.Client):
    """`translate.Client` with ONE method overridden.

    Everything that decides what the call costs and how it is retried, logged
    and envelope-shaped is production code: `_send`, `_log_usage`,
    `response_envelope`, `providers._append_usage`. The override replaces the
    `response_format` — and only when the config already asked for
    `json_schema`, so a config that had forcing off could not silently acquire
    a forced schema through this subclass.
    """

    def _body(self, system, user):
        body = super()._body(system, user)
        if self.forcing != "json_schema":
            raise SystemExit("arm F requires model.format_forcing=json_schema; "
                             f"config says {self.forcing!r}")
        body["response_format"] = arm_f_schema.request_json_schema(
            self.cfg["model"].get("json_schema_strict", True))
        return body


def setup(cfg_path=CONFIG):
    cfg = translate.load_config(cfg_path)
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


def worst_case(system, user, prov, cfg, wire_schema_chars):
    """One call's worst case, `translate.estimate_cost`'s arithmetic PLUS the
    wire schema, which arm F makes 50% bigger and which is billed as input."""
    cpt = float(cfg["cost"]["chars_per_token"])
    in_tok = (len(system) + len(user) + wire_schema_chars) / cpt
    pin, pout = prov.price_per_mtok
    return (in_tok / 1e6) * pin + (prov.max_tokens / 1e6) * pout


def ledger_spent():
    """Measured dollars this arm has already spent, read from the records on
    disk — never from a counter in memory, which a crashed run would lose while
    the money stayed spent. Own-turn records first; the shared
    `semi-formal-experiment/usage.jsonl` carries other arms' rows concurrently
    and is a cross-check, not the source."""
    total = 0.0
    if os.path.isdir(OUT):
        for f in sorted(os.listdir(OUT)):
            if f.endswith(".json") and not f.endswith(".raw.json"):
                try:
                    obj = json.load(open(os.path.join(OUT, f), encoding="utf-8"))
                except Exception:                             # noqa: BLE001
                    continue
                if isinstance(obj, dict) and "_arm_f_cost_usd" in obj:
                    total += float(obj["_arm_f_cost_usd"] or 0.0)
    return total


def floor_on_stripped(stripped, row, cfg, rows):
    """The MANDATORY floor, run on the STRIPPED object — the REAL
    `schema.validate_all` then the REAL `checks.run_checks`, unmodified."""
    out = {"breaches": [], "checks": [], "outcome": None}
    idk = cfg["corpus"]["id_key"]
    ids = {r[idk] for r in rows}
    _mod, breaches = schema.validate_all(stripped, row[idk], ids)
    out["breaches"] = [str(b) for b in breaches]
    try:
        res = checks_mod.run_checks(stripped, row, ids)
        out["outcome"] = res.outcome
        out["repair_needed"] = bool(res.repair_needed)
        out["checks"] = [f"[{f.severity}/{f.origin}] {f.check_id} @ {f.where}: "
                         f"{f.message}" for f in res.findings]
    except Exception as exc:                                  # noqa: BLE001
        out["checks"] = [f"run_checks raised: {exc!r}"]
    return out


def prompt_shas(cfg, system):
    """Two shas, both required to match before anything is sent.

    * arm F's own system block vs the PRODUCTION block rebuilt from
      `resolve_runs/graph_v2/config_corpus_all.json` — they must be EQUAL,
      because arm F ships no prose and any inequality means it accidentally
      does.
    * arm F's block vs arm B's (`045608289e…`) — they must DIFFER, and the
      difference must be exactly the appended review list.
    """
    f_sha = hashlib.sha256(system.encode()).hexdigest()
    prod_cfg = translate.load_config(PROD_CONFIG)
    prod_sha = hashlib.sha256(
        translate.build_system(prod_cfg).encode()).hexdigest()
    translate.load_config(CONFIG)                             # restore _BASE
    return f_sha, prod_sha


ARM_B_SHA = "045608289e6e60a6c7ab327cfb10625a034bd38080af88f0043f757b59517917"


def one(cid, row, rows, cfg, prov, system, lock):
    user, _, _ = translate.build_user(row, rows, cfg)
    client = ArmFClient(prov, cfg)
    env = client.complete_messages(system, [{"role": "user", "content": user}])
    raw = env["text"]
    cost = float(env.get("cost_usd") or 0.0)

    rec = {"clause_id": cid, "_arm_f_cost_usd": cost,
           "_arm_f_sha1_raw": hashlib.sha1(raw.encode()).hexdigest(),
           "usage": env.get("usage")}
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as exc:
        rec["parsed"] = False
        rec["floor"] = {"breaches": [f"not-json: {exc}"], "checks": [],
                        "outcome": None}
        rec["module"] = None
        rec["armf_checks"] = None
    else:
        rec["parsed"] = True
        stripped, extra = arm_f_schema.strip(obj)
        rec["strip_proof"] = arm_f_schema.strip_proof(obj, stripped)
        rec["checks_shape"] = arm_f_schema.checks_wellformed(extra)
        rec["armf_checks"] = extra
        rec["floor"] = floor_on_stripped(stripped, row, cfg, rows)
        rec["module"] = stripped
    with lock:
        with open(os.path.join(OUT, f"{cid}.raw.json"), "w",
                  encoding="utf-8") as fh:
            fh.write(raw)
        with open(os.path.join(OUT, f"{cid}.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(rec, fh, indent=1, ensure_ascii=False)
    return cid, cost, rec


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args(argv)

    cfg, rows, prov, system = setup()
    picks = selected(rows, cfg)
    f_sha, prod_sha = prompt_shas(cfg, system)
    cfg, rows, prov, system = setup()                         # rebuild

    prod_wire = json.dumps(schema.response_format(
        cfg["model"].get("json_schema_strict", True)))
    armf_wire = json.dumps(arm_f_schema.request_json_schema(
        cfg["model"].get("json_schema_strict", True)))

    print(f"provider {prov.name}  model {prov.model}  "
          f"max_tokens {prov.max_tokens}  price {prov.price_per_mtok} $/Mtok")
    print(f"system block: {len(system)}c  sha256 {f_sha}")
    print(f"PRODUCTION  : sha256 {prod_sha}")
    if f_sha != prod_sha:
        raise SystemExit(
            "REFUSED: arm F's system block is NOT the production one. Arm F "
            "ships no prose; an inequality here means it does. Nothing sent.")
    print("VERIFIED byte-identical to the production system block.")
    if f_sha == ARM_B_SHA:
        raise SystemExit("REFUSED: arm F's system block equals ARM B's — the "
                         "review list is in the prose and the arms are "
                         "confounded. Nothing sent.")
    print(f"differs from arm B's {ARM_B_SHA[:8]}… as required.")
    print(f"wire schema: production {len(prod_wire)}c -> arm F "
          f"{len(armf_wire)}c (+{len(armf_wire) - len(prod_wire)}c, the "
          f"{len(arm_f_schema.ENTRIES)} forced checks)")

    users = [translate.build_user(r, rows, cfg)[0] for r in picks]
    grand = sum(worst_case(system, u, prov, cfg, len(armf_wire)) for u in users)
    spent = ledger_spent()
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
                cid, cost, rec = f.result()
            except Exception as exc:                          # noqa: BLE001
                print(f"  !! {futs[f]}: {exc!r}")
                continue
            fl = rec.get("floor") or {}
            sh = rec.get("checks_shape") or {}
            print(f"  {cid}: ${cost:.5f} parsed={rec['parsed']} "
                  f"outcome={fl.get('outcome')} "
                  f"repair_needed={fl.get('repair_needed')} "
                  f"breaches={len(fl.get('breaches') or [])} "
                  f"findings={len(fl.get('checks') or [])} "
                  f"checks_n={sh.get('n')} ids_ok={sh.get('ids_exact')} "
                  f"strip_ok={(rec.get('strip_proof') or {}).get('removed_is_exactly_the_arm_key')}")
    print(f"TOTAL MEASURED ${ledger_spent():.5f}  cap ${CAP_USD:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
