#!/usr/bin/env python3
"""Produce the full panel dataset: every rollout behaviour x both specs x the frontier panel.

DRY-RUN BY DEFAULT: prints the exact call plan, what resume will skip, and a cost
estimate. Nothing is sent to any API unless --go is passed.

  python3 run_rollout.py [--go] [--runlog=path] [--behaviours=key,key] [--panel=name]

Judging is whole-document mode (whole_doc.py), resume-safe: rerunning after a crash
or provider failure only executes missing cells. Known provider quirks and their
fallbacks (from the first three behaviours):
  - Fable content-filtered on one harm-dense cell -> substitute tag `opus`
    (builder prefers fable when both exist).
  - K3 can exhaust its output budget reasoning (finish_reason: length) -> substitute
    tag `kimi-k2` (builder prefers kimi when both exist).
Run a failing cell's substitute with:  python3 whole_doc.py <behaviour> <spec> <sub-tag>
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / "panel-config.json").read_text())

# Every behaviours.json key except the two calibration behaviours (no-sycophancy,
# undermine-oversight), which were the rubric-development vehicles, not index rows.
ROLLOUT = ["helpfulness", "harmlessness-to-user", "third-party-harm", "proportionate-risk",
           "tradeoffs", "over-under-caution", "objectivity", "user-autonomy", "general-welfare"]
PANEL = CONFIG["panels"]["frontier_primary"]   # primaries only; substitutes run manually (Skill 4); --panel= overrides
# Cost is derived from config, not a hardcoded table: input is deterministic
# (spec token count times price_per_mtok); output is a range, bare verdict lines
# up to the model's max_output ceiling (models differ this much: 3k to 48k).
OUT_TOKENS_PER_PASSAGE = 8   # floor: "N: v" verdict lines only


def build_plan(behaviours, specs, panel, done, first_loc):
    """Pure: which cells to run vs which the runlog already covers."""
    plan, skipped = [], []
    for beh in behaviours:
        for spec in specs:
            for tag in panel:
                cell = (beh, spec, tag)
                if (beh, spec, tag, first_loc[spec]) in done:
                    skipped.append(cell)
                else:
                    plan.append(cell)
    return plan, skipped


def estimate(plan, spec_tokens, n_passages, models):
    """Pure: (low, high) dollar range for a plan, derived from config prices.

    low = input + verdict-lines-only output; high = input + the model's
    max_output ceiling. Both ends come from per-model config; nothing is guessed."""
    low = high = 0.0
    for _, spec, tag in plan:
        m = models[tag]
        p_in, p_out = m["price_per_mtok"]
        cin = spec_tokens[spec] / 1e6 * p_in
        low += cin + n_passages[spec] * OUT_TOKENS_PER_PASSAGE / 1e6 * p_out
        high += cin + m.get("max_output", 32768) / 1e6 * p_out
    return low, high


def main():
    panel_name = "frontier"
    go = "--go" in sys.argv
    runlog = HERE / "runlog-v3.jsonl"   # the SAME file whole_doc.py appends to
    behaviours = ROLLOUT
    for a in sys.argv[1:]:
        if a.startswith("--runlog="):
            runlog = Path(a.split("=", 1)[1])
        elif a.startswith("--behaviours="):
            behaviours = a.split("=", 1)[1].split(",")
        elif a.startswith("--panel="):
            panel_name = a.split("=", 1)[1]
            if (panel_name.startswith("_") or panel_name not in CONFIG["panels"]
                    or not isinstance(CONFIG["panels"][panel_name], list)):
                sys.exit(f"unknown panel {panel_name!r} -- panels: {[k for k in CONFIG['panels'] if not k.startswith('_')]}")
            globals()["PANEL"] = CONFIG["panels"][panel_name]
        elif a != "--go":
            sys.exit(f"unknown argument {a!r} -- valid: --go --runlog= --behaviours= --panel=")
    known = {k for k, v in json.loads((HERE / "behaviours.json").read_text()).items()
             if isinstance(v, dict)}
    bad = [b for b in behaviours if b not in known]
    if bad:
        sys.exit(f"unknown behaviours {bad} -- keys in behaviours.json: {sorted(known)}")
    sp = importlib.util.spec_from_file_location("h", HERE / "harness.py")
    h = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(h)
    h.RUNLOG = runlog
    done = h.done_keys(CONFIG["rubric"])
    all_ps = {s: h.passages(s) for s in CONFIG["specs"]}
    first_loc = {s: ps[0][0] for s, ps in all_ps.items()}
    spec_tokens = {s: sum(len(t) for _, _, t in ps) // 4 for s, ps in all_ps.items()}
    n_passages = {s: len(ps) for s, ps in all_ps.items()}

    plan, skipped = build_plan(behaviours, CONFIG["specs"], PANEL, done, first_loc)
    low, high = estimate(plan, spec_tokens, n_passages, CONFIG["models"])
    print(f"plan: {len(plan)} calls ({len(skipped)} cells resumed), estimated "
          f"${low:.0f}-{high:.0f} (config-derived: exact input cost; output floor vs ceiling)")
    for beh, spec, tag in plan:
        print(f"  whole_doc.py {beh} {spec} {tag}")
    if not go:
        print("\nDRY RUN -- nothing was sent. Re-run with --go to execute.")
        return
    fails = 0
    for beh, spec, tag in plan:
        r = subprocess.run([sys.executable, str(HERE / "whole_doc.py"), beh, spec, tag,
                            f"--runlog={runlog}"], cwd=HERE)
        if r.returncode != 0:
            fails += 1
            print(f"FAILED (continuing): {beh} {spec} {tag}")
            if fails >= 5:
                sys.exit("5 consecutive-run failures -- check keys/network before spending further")
        else:
            fails = 0
    # completeness check against the REAL runlog: catches parse failures (which exit 0),
    # crashes, and interrupts uniformly, and names the fix for each missing cell
    done = h.done_keys(CONFIG["rubric"])
    missing = [(b, sp, t) for b, sp, t in
               ((b, sp, t) for b in behaviours for sp in CONFIG["specs"] for t in PANEL)
               if (b, sp, t, first_loc[sp]) not in done]
    if missing:
        print(f"\nINCOMPLETE -- {len(missing)} cells still missing:")
        sub = {"fable": "opus", "kimi": "kimi-k2"}
        for b, sp, t in missing:
            alt = f"  (or substitute: whole_doc.py {b} {sp} {sub[t]})" if t in sub else ""
            print(f"  retry: whole_doc.py {b} {sp} {t} --runlog={runlog}{alt}")
    else:
        print(f"\nCOMPLETE -- every cell banked. Next: python3 build_site_data.py "
              f"--runlog={runlog} --rubric={CONFIG['rubric']} --panel={panel_name}")


if __name__ == "__main__":
    main()
