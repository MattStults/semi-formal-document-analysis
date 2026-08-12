#!/usr/bin/env python3
"""Step 3 for graph-node modules: link the translated node corpus AS A CORPUS.

Gathers every node module that reached `translated` across the sample runs
under translation_sample/runs/, dedupes to ONE artifact per node (the newest
run wins -- run dirs are timestamp-named), merges the concept rows those runs'
concepts.json declare for the selected modules, and runs `link.collect` ONCE
over the whole set. Per-module linking is what checks.py already does at
stage 2; the point here is the cross-module scope: a `requires` that dangles
per-module may be provided by a sibling node, and only corpus scope can say so.

Writes link_nodes_report.json beside this script:
  - findings by check class (and severity), with every message kept
  - requires-resolution: per module, which `%% requires:` signatures find a
    provider among the OTHER selected modules and which dangle

No model call, no spend -- pure re-analysis of artifacts already on disk.

Usage:
  python3 link_nodes.py            # uses the venv's clingo via link.py's PY
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
WALK = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
for _p in (PHASE1, WALK):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import link  # noqa: E402  (walkthrough/link.py)

RUNS = os.path.join(HERE, "translation_sample", "runs")
REPORT = os.path.join(HERE, "link_nodes_report.json")
#: run-dir names start with a sortable timestamp (YYYYMMDD-HHMMSS-...)
RUN_DIR = re.compile(r"^\d{8}-\d{6}-")


def norm_id(node_id):
    """Same normalisation as node_corpus.asp_id: early runs named artifacts
    with the raw graph id (L3995-4164_n001), later ones with the ASP-safe
    alias (l3995_4164_n001). One node, one key."""
    return node_id.replace("-", "_").lower()


def gather():
    """One (lp_path, json_obj, run_dir) per node -- newest translated wins."""
    selected = {}
    for run in sorted(d for d in os.listdir(RUNS) if RUN_DIR.match(d)):
        rdir = os.path.join(RUNS, run)
        for f in sorted(os.listdir(rdir)):
            if not f.endswith(".json") or f in (
                    "run.json", "concepts.json") or f.endswith(
                    (".transcript.json", ".version.json")):
                continue
            obj = json.load(open(os.path.join(rdir, f), encoding="utf-8"))
            if obj.get("outcome") != "translated":
                continue
            lp = os.path.join(rdir, f[:-len(".json")] + ".lp")
            if not os.path.isfile(lp):
                continue
            selected[norm_id(obj["clause_id"])] = (lp, obj, rdir)
    return selected


def merged_concepts(selected):
    """The selected modules' rows from their OWN runs' concepts.json.

    A run's table covers every module of that run; taking only the selected
    module's rows keeps one declaration per node and no rows from artifacts
    that lost the dedupe.
    """
    rows = []
    for nid, (_lp, obj, rdir) in sorted(selected.items()):
        table = os.path.join(rdir, link.CONCEPT_TABLE)
        if not os.path.isfile(table):
            continue
        for r in link.load_concept_table(table):
            if norm_id(str(r.get("clause_id") or "")) == nid:
                rows.append(r)
    return rows


def requires_resolution(selected):
    """Which `%% requires:` signatures find a provider module in this corpus?"""
    headers = {nid: link.header(lp)
               for nid, (lp, _o, _r) in selected.items()}
    provided_by = {}
    for nid, (lp, _o, _r) in selected.items():
        for sig in link.defined_predicates(
                open(lp, encoding="utf-8").read()):
            provided_by.setdefault(sig, []).append(nid)
    per_module, n_res, n_dangle = {}, 0, 0
    for nid in sorted(headers):
        res, dangle = {}, []
        for sig in sorted(headers[nid]["requires"]):
            providers = [p for p in provided_by.get(sig, []) if p != nid]
            if providers:
                res[sig] = sorted(providers)
            else:
                dangle.append(sig)
        n_res += len(res)
        n_dangle += len(dangle)
        per_module[nid] = {"resolved": res, "dangling": dangle}
    total = n_res + n_dangle
    return {
        "per_module": per_module,
        "requires_total": total,
        "requires_resolved": n_res,
        "requires_dangling": n_dangle,
        "resolution_rate": round(n_res / total, 4) if total else None,
        "modules_fully_resolved": sum(
            1 for v in per_module.values() if not v["dangling"]),
        "modules_with_requires": sum(
            1 for v in per_module.values()
            if v["resolved"] or v["dangling"]),
    }


# --------------------------------------------------------------------------
#  ⭐ The blessed step-4 plumbing (READBACK_SMOKE.md gaps 2 and 4). The smoke
#  hand-built both of these; a driver must not. Everything here is pure
#  re-analysis of artifacts already on disk — no model call, no spend.
# --------------------------------------------------------------------------

def merged_gloss(selected=None):
    """The merged node-corpus concept table as the ONE extra_gloss dict the
    render/seat path takes: `readback.render_module(mod, extra_gloss=...)`,
    `readback_r3.render_r3(mod, cov, extra_gloss=...)`. This is where a
    borrowed (`requires`) name gets its written meaning — the provider node's
    own gloss — so a derivation leaf that crosses a node boundary renders as
    a definition instead of blocking on `readback-ungloss`.

    (`probe.probe_clause(..., concepts=merged_concepts(selected))` takes the
    ROWS, not this dict; the row shape is what probe reads.)

    ⛔ PROVIDER-FIRST (consolidated_fix_review.md F3, 2026-08-12): when the
    same bare name is glossed by several nodes, the winner must be a node
    whose ASP actually DEFINES the predicate (the provider index,
    `link.defined_predicates`) — before this fix the alphabetically-first
    node won, so a borrower's gloss could shadow the provider's
    (`stay_in_bounds_principles` live). Ties among genuine providers keep
    the sorted-id order; a name no module defines falls back to the old
    first-row-wins.
    """
    import readback
    selected = gather() if selected is None else selected
    rows = merged_concepts(selected)
    defined = {}
    for nid, (lp, _o, _r) in selected.items():
        for sig in link.defined_predicates(
                open(lp, encoding="utf-8").read()):
            defined.setdefault(sig.split("/")[0], set()).add(nid)
    provider_rows = [
        r for r in rows
        if norm_id(str(r.get("clause_id") or ""))
        in defined.get(str(r["concept"]).split("/")[0], ())]
    return readback.gloss_from_rows(provider_rows + rows)


def node_clause_texts(corpus_path=None):
    """`{asp_id: judgeable clause text}` off node_corpus.json, through
    `readback.clause_text` — the narrowed span text, NEVER the packed
    translator prompt. This is the `clause_text`/`corpus_texts` source for
    RB4 and every seat prompt over node modules."""
    import readback
    path = corpus_path or os.path.join(HERE, "node_corpus.json")
    corpus = json.load(open(path, encoding="utf-8"))
    return readback.clause_texts(corpus["clauses"])


def provider_texts(node_id, selected=None, texts=None, resolution=None):
    """The provider nodes' span texts for `node_id`'s in-corpus-resolved
    `requires` — the `cross_reference_texts` a seat prompt takes.

    ⭐ THE LIVE EVIDENCE (READBACK_SMOKE.md gap 4): shown only its own node
    span, the first live 4b seat returned `unclear` on every borrowed concept
    gloss — rightly, since the narrowed span does not define them. The
    defining spans must ride along. A `requires` that dangles in-corpus has no
    provider and contributes nothing here; the Q-22 path already surfaces it
    as `requires-unsatisfied` at stage 3.
    """
    selected = gather() if selected is None else selected
    texts = node_clause_texts() if texts is None else texts
    resolution = (requires_resolution(selected) if resolution is None
                  else resolution)
    per = resolution["per_module"].get(norm_id(node_id), {})
    providers = sorted({p for ps in per.get("resolved", {}).values()
                        for p in ps})
    return tuple(texts[p] for p in providers if texts.get(p))


def main():
    selected = gather()
    if not selected:
        raise SystemExit(f"no translated node modules found under {RUNS}")
    concepts = merged_concepts(selected)
    paths = [lp for _nid, (lp, _o, _r) in sorted(selected.items())]

    # ⭐ The `#const onto = on.` collision first measured HERE (2026-08-11,
    # STEPS34_READINESS.md gap 1) is now handled where corpus assembly
    # happens: `link.collect` dedupes exactly `link.SHARED_PREAMBLE` at
    # multi-file scope, and any OTHER `#const` redefinition still errors.
    # This script's local strip is gone.
    findings = link.collect(paths, concepts=concepts)
    dedup = {"handled_by": "link.collect / link.dedupe_shared_preamble",
             "shared_preamble": list(link.SHARED_PREAMBLE)}

    by_class = {}
    for f in findings:
        by_class.setdefault(f.check_id, []).append(
            {"severity": f.severity, "where": f.where, "message": f.message})
    resolution = requires_resolution(selected)

    report = {
        "scope": "cross-module link over translated graph-node modules",
        "runs_dir": os.path.relpath(RUNS, HERE),
        "modules": {nid: os.path.relpath(lp, HERE)
                    for nid, (lp, _o, _r) in sorted(selected.items())},
        "n_modules": len(selected),
        "n_concept_rows": len(concepts),
        "findings_by_class": {
            k: by_class[k] for k in sorted(by_class)},
        "finding_counts": {k: len(v) for k, v in sorted(by_class.items())},
        "n_errors": sum(1 for f in findings if f.severity == "error"),
        "n_notes": sum(1 for f in findings if f.severity == "note"),
        "preamble_dedup": dedup,
        "requires_resolution": resolution,
    }
    json.dump(report, open(REPORT, "w", encoding="utf-8"), indent=1)

    print(f"linked {len(selected)} node modules as one corpus "
          f"({len(concepts)} concept rows)")
    for k, v in sorted(report["finding_counts"].items()):
        sev = {f["severity"] for f in by_class[k]}
        print(f"  {k:<24} {v:>3}  [{'/'.join(sorted(sev))}]")
    r = resolution
    print(f"requires: {r['requires_resolved']}/{r['requires_total']} resolved "
          f"in-corpus ({r['requires_dangling']} dangling); "
          f"{r['modules_fully_resolved']}/{r['modules_with_requires']} "
          f"modules fully resolved")
    print(f"report -> {os.path.relpath(REPORT, os.getcwd())}")


if __name__ == "__main__":
    main()
