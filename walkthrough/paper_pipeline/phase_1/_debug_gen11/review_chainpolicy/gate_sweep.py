import sys, os, io, re, contextlib, json
HERE = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, HERE)
import translate as T

class A:
    clause = section = kinds = limit = provider = model = max_tokens = None
    live = False; show_prompt = 0; only_stale = False

cfgs = sys.argv[1:]
for p in cfgs:
    d = os.path.dirname(os.path.abspath(p))
    cwd = os.getcwd()
    buf = io.StringIO()
    real, seen = T.estimate_cost, []
    def spy(*a, **k):
        o = real(*a, **k); seen.append((o[0], k.get("max_attempts"))); return o
    T.estimate_cost = spy
    try:
        os.chdir(d)
        with contextlib.redirect_stdout(buf):
            T.run(T.load_config(os.path.basename(p)), A())
    except Exception as e:
        print(f"{p}: EXC {type(e).__name__}: {e}")
        T.estimate_cost = real; os.chdir(cwd); continue
    finally:
        T.estimate_cost = real; os.chdir(cwd)
    out = buf.getvalue()
    m = re.search(r"cost \(worst\) : \$([0-9.]+)", out)
    cfg = json.load(open(p))
    ceil = cfg.get("cost", {}).get("max_cost_usd")
    ma = (cfg.get("repair") or {}).get("max_attempts", 1)
    n = re.search(r"clauses      : (\d+)", out)
    print(f"{p}: printed={m.group(1) if m else '?'} ceiling={ceil} T={ma} clauses={n.group(1) if n else '?'} single={seen[-1][0]:.4f} shim2T=?")
