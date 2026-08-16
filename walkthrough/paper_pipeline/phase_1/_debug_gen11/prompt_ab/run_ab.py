"""Execute the pre-registered draws. ONE ISOLATED CALL PER DRAW.

Usage:  run_ab.py --arm A [--estimate-only]
Prints the worst-case estimate and REFUSES if it exceeds SESSION_CEILING.
Aborts mid-run if measured spend exceeds ABORT_AT.
Writes only into _debug_gen11/prompt_ab/draws/.
"""
import os, sys, json, time, argparse, hashlib

P1 = "/Users/mattstults/Documents/ai_safety_projects/semi-formal-document-analysis/walkthrough/paper_pipeline/phase_1"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, P1)
os.chdir(P1)
import translate

SESSION_CEILING = 0.40      # authorised, both experiments combined
ABORT_AT = 0.38
DRAWS_DIR = os.path.join(HERE, "draws")
LEDGER = os.path.join(HERE, "spend_ledger.json")

ap = argparse.ArgumentParser()
ap.add_argument("--arm", required=True, choices=["A", "B"])
ap.add_argument("--estimate-only", action="store_true")
args = ap.parse_args()

man = json.load(open(os.path.join(HERE, "manifest.json")))
systems = {k: open(os.path.join(HERE, f"system_{k}.txt"), encoding="utf-8").read()
           for k in ("A", "B_d1", "B_d2")}
for k, v in systems.items():
    tag = "sha_A" if k == "A" else "sha_B"
    exp = man["systems"]["d1" if k in ("A", "B_d1") else "d2"][tag]
    got = hashlib.sha256(v.encode()).hexdigest()
    assert got == exp, f"system {k} sha drift: {got} != {exp}"

tasks = [t for t in man["tasks"] if t["arm"] == args.arm]
os.makedirs(DRAWS_DIR, exist_ok=True)
todo = [t for t in tasks if not os.path.exists(os.path.join(DRAWS_DIR, t["task_id"] + ".json"))]

cfg = translate.load_config(os.path.join(P1, "resolve_runs/graph_v2/config_corpus_all.json"))
class _A: provider = None; model = None; max_tokens = None
prov = translate.resolve_provider(cfg, _A())
pin, pout = prov.price_per_mtok
sch_tok = len(json.dumps(translate.schema.response_format(True))) / 4.0

est = 0.0
for t in todo:
    u = open(t["user_path"], encoding="utf-8").read()
    s = systems[t["sys_key"]]
    itok = (len(s) + len(u)) / 4.0 + sch_tok
    est += itok / 1e6 * pin + prov.max_tokens / 1e6 * pout

prior = json.load(open(LEDGER))["measured_usd"] if os.path.exists(LEDGER) else 0.0
print(f"ARM {args.arm}: {len(todo)} calls to send ({len(tasks)-len(todo)} already on disk)")
print(f"  model            : {prov.model} @ {prov.base_url}")
print(f"  price            : ${pin}/Mtok in, ${pout}/Mtok out (cached NOT claimed)")
print(f"  WORST-CASE EST   : ${est:.4f}   (output billed at the full max_tokens {prov.max_tokens})")
print(f"  already measured : ${prior:.4f}")
print(f"  worst-case total : ${prior + est:.4f}  vs session ceiling ${SESSION_CEILING:.2f}")
if prior + est > SESSION_CEILING:
    raise SystemExit(f"REFUSED: worst-case ${prior+est:.4f} exceeds the authorised "
                     f"${SESSION_CEILING:.2f}. Nothing sent.")
if args.estimate_only:
    raise SystemExit(0)

client = translate.Client(prov, cfg)
spent = prior
t0 = time.time()
for i, t in enumerate(todo):
    u = open(t["user_path"], encoding="utf-8").read()
    s = systems[t["sys_key"]]
    rec = dict(t)
    try:
        env = client.complete(s, u)
        rec["ok"] = True
        rec["text"] = env.get("text")
        rec["usage"] = env.get("usage")
        rec["finish_reason"] = env.get("finish_reason")
    except Exception as exc:
        rec["ok"] = False
        rec["error"] = f"{type(exc).__name__}: {exc}"
    rec["system_sha"] = hashlib.sha256(s.encode()).hexdigest()
    json.dump(rec, open(os.path.join(DRAWS_DIR, t["task_id"] + ".json"), "w"), indent=1)
    spent = prior + client.spent_usd
    json.dump({"measured_usd": spent, "calls": client.calls}, open(LEDGER, "w"), indent=1)
    print(f"  [{i+1}/{len(todo)}] {t['task_id']} {t['exp']}/{t['cohort']} {t['clause']} "
          f"arm={t['arm']} draw={t['draw']} ok={rec['ok']} spent=${spent:.4f}")
    if spent > ABORT_AT:
        raise SystemExit(f"ABORT: measured ${spent:.4f} > ${ABORT_AT:.2f}")
print(f"\nDONE arm {args.arm}: {client.calls} calls, measured ${spent:.4f}, "
      f"{time.time()-t0:.0f}s")
