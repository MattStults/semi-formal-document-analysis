#!/usr/bin/env python3
"""Authority-edge canonicalization smoke test (prepared 2026-08-11; see
authority_convention.md and edge_divergence_analysis.md).

The section-authority edge class is ~47% of all golden-vs-ds3 edge
divergence: both graphs judge "this heading's authority=X label leans on
the L67-101 authority-level definitions" but attach it differently (ds3:
per-section `<section>_section_authority` coinages; golden: shared
canonical names like `guideline_authority`). This smoke replays two
heading-dense leaf dispatches with ONE MANDATED CONVENTION appended to
the standard leaf extra, and scores each draw mechanically.

Scorer: fraction of heading-authority nodes (nodes whose spans cover an
`authority=` line) carrying a CANONICAL authority concept — an entry
whose name tokens are drawn entirely from the authority vocabulary
(level words + generic authority terms) and include 'authority'.
Token-based, not exact-string: `user_authority_metadata` and
`authority_levels_hierarchy` count; `refusal_style_section_authority`
does not. Band: PASS at frac >= 0.8. (`canon_needs` is also reported:
the convention's strict needs-based form.)

Usage:
  python3 smoke_authority.py             # DRY RUN (default, free):
                                         #   prints both dispatch texts +
                                         #   scorer self-test: golden PASS,
                                         #   ds3 FAIL — validates the scorer
  python3 smoke_authority.py --yes       # live draws (SPENDS; not part of prep)

Span selection: densest authority=-label spans SUBJECT TO the self-test
asymmetry holding (golden must PASS, ds3 must FAIL, else the scorer
validates nothing). L3502-3755 (5 labels) is excluded: golden itself
skips the class there (0/5). Chosen: A=L3995-4164 (5 labels, golden
4/5), B=L1975-2125 (3 labels, golden 3/3).
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.abspath(os.path.join(
    HERE, "..", "..", "..", "..", "..", "semi-formal-experiment")))

import recurse_driver as R  # noqa: E402

SPEC = os.path.join(HERE, "..", "..", "..", "..", "..", "specs",
                    "openai-model-spec", "model_spec.md")

# The mandated convention — verbatim in authority_convention.md. Appended
# to the SAME single-source leaf extra the pipeline uses (R.leaf_extra).
CONVENTION = (
    "AUTHORITY-LABEL CONVENTION (mandatory). Headings in this document "
    "carry inline `authority=X` labels (X in root/system/developer/user/"
    "guideline). When you emit a node for such a heading, record the "
    "label's dependence on the document's authority-level definitions as "
    "a `needs` entry naming the SHARED, document-wide concept for that "
    "level -- exactly one canonical name per level: `root_authority`, "
    "`system_authority`, `developer_authority`, `user_authority`, "
    "`guideline_authority` (prose: \"the X authority level as defined in "
    "Instructions and levels of authority\"), or "
    "`authority_levels_hierarchy` when the ordering between levels is "
    "itself at stake. Never coin a per-section name for this dependency "
    "(patterns like `<section>_section_authority` or "
    "`<section>_section_root_authority` are forbidden): the concept "
    "belongs to the whole document, and a section-local coinage prevents "
    "the edge from resolving to the shared definition.")

# A: golden-canonical guideline region; B: the E08/E10 root/user region.
SPANS = [("A_L3995-4164", 3995, 4164), ("B_L1975-2125", 1975, 2125)]

LEVELS = {"platform", "developer", "user", "guideline", "none",
          "root", "system"}
GENERIC = {"authority", "authorities", "level", "levels", "hierarchy",
           "ordering", "instruction", "instructions", "metadata",
           "label", "chain", "command"}


# ---------------------------------------------------------------- scorer
def authority_lines():
    """1-based doc lines carrying an inline authority= label."""
    with open(SPEC) as f:
        return {i + 1 for i, l in enumerate(f) if "authority=" in l}


def canon_entry(e):
    """Canonical = name tokens all from the authority vocabulary, and
    'authority' among them. NOT a prose match: ds3's coinages describe
    their level in prose too (51/55 prose-match), so prose alone cannot
    discriminate; the shared NAME is what makes the class matchable."""
    name = (e.get("name") or "") if isinstance(e, dict) else str(e)
    toks = set(re.split(r"[^a-z]+", name.lower())) - {""}
    return "authority" in toks and not (toks - LEVELS - GENERIC)


def score(g, lo, hi, auth):
    """Fraction of heading-authority nodes in [lo,hi] carrying a
    canonical concept. Primary metric counts needs OR provides (the
    shared name is what canonicalizes the edge class for comparison);
    canon_needs is the convention's strict form, reported alongside."""
    tot = needs_ok = any_ok = 0
    misses = []
    for n in g.get("nodes", []):
        lines = {ln for s in n.get("spans", [])
                 for ln in range(s["lines"][0], s["lines"][1] + 1)}
        hit = {x for x in lines & auth if lo <= x <= hi}
        if not hit:
            continue
        tot += 1
        nk = any(canon_entry(x) for x in n.get("needs", []))
        ak = nk or any(canon_entry(x) for x in n.get("provides", []))
        needs_ok += nk
        any_ok += ak
        if not ak:
            misses.append((n.get("id"), sorted(hit)))
    frac = any_ok / tot if tot else 0.0
    return {"heading_auth_nodes": tot, "canon_needs": needs_ok,
            "canon_any": any_ok, "frac": round(frac, 3),
            "verdict": "PASS" if tot and frac >= 0.8 else "FAIL",
            "misses": misses}


# ------------------------------------------------------------- dispatches
def seeds_for(lo, hi):
    """Deepest runs/ds3 division whose span covers [lo,hi] — same
    reconstruction idea as smoke_granularity.py, generalized because
    these spans cross ds3 leaf boundaries."""
    d, seeds = os.path.join(HERE, "runs", "ds3"), []
    while True:
        j = json.load(open(os.path.join(d, "division.json")))
        seeds = j.get("seed_vocabulary", seeds)
        for i, ch in enumerate(j.get("children", []), 1):
            clo, chi = ch["span"]
            sub = os.path.join(d, f"c{i}")
            if (clo <= lo and hi <= chi and os.path.isdir(sub)
                    and os.path.exists(os.path.join(sub, "division.json"))):
                d = sub
                break
        else:
            return d, seeds


def build_dispatch(drv, lo, hi):
    _, seeds = seeds_for(lo, hi)
    extra = R.leaf_extra(lo, hi) + "\n" + CONVENTION
    return drv.dispatch_block("L", lo, hi, seeds, extra)


# --------------------------------------------------------------- self-test
def self_test(auth):
    """Free scorer validation: the golden's own nodes must PASS and
    ds3's must FAIL on both spans — asymmetry proves the scorer
    discriminates shared-canonical from per-section coinage BEFORE any
    spend."""
    graphs = [("GOLDEN", os.path.join(HERE, "recurse", "root",
                                      "graph.json")),
              ("DS3", os.path.join(HERE, "runs", "ds3",
                                   "root_graph.json"))]
    print("== scorer self-test (deterministic, no spend) ==")
    ok = True
    results = {}
    for name, lo, hi in SPANS:
        for tag, path in graphs:
            r = score(json.load(open(path)), lo, hi, auth)
            results[f"{name}/{tag}"] = r
            want = "PASS" if tag == "GOLDEN" else "FAIL"
            mark = "ok" if r["verdict"] == want else "UNEXPECTED"
            ok &= r["verdict"] == want
            print(f"  {name} {tag}: {r['canon_any']}/"
                  f"{r['heading_auth_nodes']} = {r['frac']:.2f} "
                  f"-> {r['verdict']} (needs-only {r['canon_needs']}) "
                  f"[{mark}]")
            for mid, at in r["misses"]:
                print(f"      miss: {mid} @ {at}")
    print(f"  self-test {'VALID' if ok else 'INVALID -- do not run live'}:"
          f" golden PASS / ds3 FAIL asymmetry"
          f" {'holds' if ok else 'BROKEN'}")
    return ok, results


# -------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None,
                    help="together model id (default: driver_config's)")
    ap.add_argument("--n", type=int, default=2)
    ap.add_argument("--max-tokens", type=int, default=32768)
    ap.add_argument("--yes", action="store_true",
                    help="actually spend; default is the free dry run")
    args = ap.parse_args()

    cfg = json.load(open(os.path.join(HERE, "driver_config.json")))
    model = args.model or cfg["model"]["model"]
    slug = model.split("/")[-1][:40]
    out = os.path.join(HERE, "probes", f"smoke_authority_{slug}")
    lines = R.load_doc(SPEC)
    auth = authority_lines()

    # Prompt-building needs a Driver but no client (dry run never calls).
    drv = R.Driver({"model": dict(cfg["model"],
                                  max_tokens=args.max_tokens)},
                   None, lines, out)

    valid, _ = self_test(auth)

    if not args.yes:
        print("\n== DRY RUN (default) -- dispatches that WOULD be sent ==")
        for name, lo, hi in SPANS:
            user = build_dispatch(drv, lo, hi)
            ddir, seeds = seeds_for(lo, hi)
            print(f"\n---- {name}: span L{lo}-{hi}, {len(seeds)} seeds "
                  f"from {os.path.relpath(ddir, HERE)}, "
                  f"schema=R.leaf_schema({lo},{hi}), "
                  f"dispatch {len(user)} chars ----")
            print(user[:1400])
            print(f"    [... {max(0, len(user) - 1400)} more chars: "
                  f"numbered span L{lo}-{hi} ...]")
        print("\ndry run only: pass --yes to spend (check spend.py "
              "ceiling first)")
        return

    if not valid:
        print("refusing live run: scorer self-test asymmetry is broken")
        sys.exit(1)

    os.makedirs(out, exist_ok=True)
    est = args.n * len(SPANS) * (
        40000 / 4 / 1e6 * cfg["price_per_mtok"][0]
        + args.max_tokens / 1e6 * cfg["price_per_mtok"][1])
    print(f"\nsmoke on {model}: {args.n} draws x {len(SPANS)} dispatches,"
          f" worst-case ~${est:.2f} at config prices")

    prov = R.T.Provider(
        name=f"smoke-auth-{slug}", kind="openai-compatible", model=model,
        base_url=cfg["model"]["base_url"],
        api_key_env=cfg["model"]["api_key_env"],
        temperature=cfg["model"].get("temperature", 0.2),
        max_tokens=args.max_tokens, price_per_mtok=cfg["price_per_mtok"])
    client = R.GraphClient(prov, {"model": dict(
        cfg["model"], model=model, format_forcing="json_object",
        usage_log=cfg["model"].get("usage_log", "DEFAULT"))})
    client.max_cost_usd = 0.50
    drv.client = client

    report = {"model": model, "convention_chars": len(CONVENTION),
              "dispatches": {}}
    for name, lo, hi in SPANS:
        user = build_dispatch(drv, lo, hi)
        rows = []
        for i in range(args.n):
            client.reply_schema = R.leaf_schema(lo, hi)
            try:
                env = client.complete(drv.brief, user)
                g = R.parse_json_reply(env["text"])
                row = score(g, lo, hi, auth)
                row["nodes"] = len(g.get("nodes", []))
                row["validation_errors"] = len(
                    R.validate_leaf(g, lo, hi, lines))
            except Exception as exc:        # noqa: BLE001
                row = {"error": str(exc)[:160]}
            rows.append(row)
            print(f"  {name} draw {i}: {json.dumps(row)[:200]}")
        report["dispatches"][name] = rows
    report["spent_usd"] = round(getattr(client, "spent_usd", 0.0), 4)
    R.write_json(os.path.join(out, "report.json"), report)
    print(f"spent ${report['spent_usd']:.4f} -> {out}/report.json")


if __name__ == "__main__":
    main()
