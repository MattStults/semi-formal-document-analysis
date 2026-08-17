#!/usr/bin/env python3
"""Frontier-panel agreement check over the translated node corpus.

Matt's question (2026-08-16): run the behaviors the FRONTIER PANEL judged
(`data/behaviours.json`: helpfulness, harm-avoidance-to-third-parties,
avoiding-over-and-under-caution — judges sol/kimi/fable/opus/kimi-k2) through
the node-matching pipeline over the currently translated corpus, and use
agreement/disagreement with the panel's clause citations as a QUALITY CHECK.

⛔ LABELS DIRECT ATTENTION, NEVER TRUTH (standing rule). The panel is a
measuring instrument, not an answer key for the pipeline: agreement numbers
are an ATTENTION surface, and every disagreement is a queue entry to be
adjudicated against the document, not a scored error. The check is
structurally leak-fenced, mirroring semi-formal-experiment's split:

  * `match` (phase A, QUERY-SIDE): reads ONLY `behaviours_query.json`
    (definitions; built exactly so the panel labels are unreachable from the
    query path), decomposes live, embeds + seat-judges top-K per atom over
    ALL translated nodes with geometry. Never imports benchmark or touches
    data/behaviours.json. Its artifacts are written before any label loads.
  * `compare` (phase B, EVALUATION-SIDE): loads the panel, maps reference
    passages -> clauses (benchmark.clause_joins, join v1) -> clause lines ->
    translated node spans, and crosses that with phase A's verdicts. Reports
    the 3-way pipeline state per node (engaged / judged_not_engaged /
    never_retrieved) so retrieval misses are not conflated with seat misses.
  * `probe` (phase C, EVALUATION-SIDE spend): seat-judges the panel-relevant
    nodes phase A never retrieved. Label-SELECTED (labels directing
    attention), but each verdict is made blind: the prompt carries only the
    atom gloss and the node's prose, exactly as in phase A.

Usage (run from behavior_pilot/):
    .../.venv/bin/python panel_agreement.py match     (~$0.02)
    .../.venv/bin/python panel_agreement.py compare   ($0)
    .../.venv/bin/python panel_agreement.py probe     (~$0.03)
    .../.venv/bin/python panel_agreement.py compare   (re-run: folds probe in)
"""
import argparse, json, os, re, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
GRAPH_V2 = os.path.dirname(HERE)
PHASE1 = os.path.abspath(os.path.join(GRAPH_V2, "..", ".."))
REPO = os.path.abspath(os.path.join(PHASE1, "..", "..", ".."))
EXP = os.path.join(REPO, "semi-formal-experiment")
for p in (HERE, GRAPH_V2, PHASE1):
    sys.path.insert(0, p)

import behavior_match as BM        # noqa: E402
import corpus_gate                 # noqa: E402
import live_pilot                  # noqa: E402  (seat_client, live_embed)

OUT = os.path.join(HERE, "panel_run1")
NODE_CORPUS_ALL = os.path.join(GRAPH_V2, "node_corpus_all.json")
QUERY_DEFS = os.path.join(EXP, "behaviours_query.json")
SLUGS = ["helpfulness", "harm-avoidance-to-third-parties",
         "avoiding-over-and-under-caution"]
TOP_K = 8


def _write(name, obj):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, sort_keys=True)
    print("wrote panel_run1/" + name)


def translated_views():
    """Views for every translated, non-abstained node in the CURRENT corpus."""
    views = BM.node_views(NODE_CORPUS_ALL)
    out = {}
    for cid, (o, _s, _r) in corpus_gate.gather().items():
        if o.get("outcome") == "translated" and cid in views:
            out[cid] = views[cid]
    return out


def node_geometry():
    geo = {}
    for c in json.load(open(NODE_CORPUS_ALL))["clauses"]:
        loc = c["locator"].split(">")[-1]
        geo[c["id"]] = [(int(m.group(1)), int(m.group(2)))
                        for m in re.finditer(r"L(\d+)-(\d+)", loc)]
    return geo


# ------------------------------------------------------------------ phase A

def step_match():
    defs = {b["slug"]: b for b in json.load(open(QUERY_DEFS))["behaviours"]}
    views = translated_views()
    print(f"universe: {len(views)} translated nodes")
    complete = live_pilot.seat_client(max_tokens=1500)
    report = {"universe": sorted(views), "behaviors": {}}
    for slug in SLUGS:
        b = defs[slug]
        env = complete(live_pilot.ATOM_BRIEF,
                       f"BEHAVIOR: {b['name']}\n\n{b['definition']}\n\n"
                       "Decompose. JSON only.")
        try:
            atoms = [a for a in json.loads(env.get("text", ""))["atoms"]
                     if re.fullmatch(r"[a-z][a-z0-9_]+", str(a.get("name", "")))
                     and str(a.get("gloss", "")).strip()][:8]
        except Exception as ex:              # noqa: BLE001
            print(f"  !! {slug}: unparseable decomposition {ex!r}")
            atoms = []
        ranked = BM.rank_candidates(atoms, views, embed=live_pilot.live_embed,
                                    top_k=TOP_K)
        rows = []
        for ai, a in enumerate(atoms):
            verdicts = []
            for score, cid in ranked[ai]:
                v = BM.judge(complete, BM.build_prompt(a, views[cid]))
                verdicts.append({"node": cid, "score": round(score, 4),
                                 "verdict": v["verdict"],
                                 "grounds": v["grounds"]})
            rows.append({"atom": a["name"], "gloss": a["gloss"],
                         "verdicts": verdicts})
            print(f"  {slug[:28]:28s} {a['name']:32s} "
                  f"{sum(1 for v in verdicts if v['verdict']=='engaged')}"
                  f"/{len(verdicts)} engaged")
        report["behaviors"][slug] = {"definition": b["definition"],
                                     "atoms": rows}
    c = complete.client
    report["model"] = c.p.model
    report["calls"] = c.calls
    report["spent_usd"] = round(c.spent_usd, 6)
    _write("match.json", report)


# ------------------------------------------------------------------ phase B

def _panel_reference_nodes():
    """{slug: {tier: set(node ids)}} — panel reference passages joined to
    clauses, clause lines intersected with translated node spans. Also
    returns per-slug coverage facts (reference clauses outside every span)."""
    sys.path.insert(0, EXP)
    _cwd = os.getcwd()
    os.chdir(EXP)              # benchmark resolves data paths relative to EXP
    try:
        import benchmark
        clauses, _src = benchmark.load_clauses()
        line_of = {c["id"]: c["line"] for c in clauses if "line" in c}
        panel = benchmark.load_true_panel()
        geo = node_geometry()
        translated = set(json.load(open(
            os.path.join(OUT, "match.json")))["universe"])

        def nodes_at(ln):
            return {n for n in translated
                    for a, b in geo.get(n, []) if a <= ln <= b}

        out, facts = {}, {}
        for slug in SLUGS:
            b = panel[slug]
            joins = benchmark.clause_joins(b, clauses)
            tiers = {}
            cov = {}
            for tier, min_s in (("consensus_ge5", 5), ("any_ge2", 2)):
                pids = benchmark.reference_ids(b, min_score=min_s)
                cids = {c for p in pids for c in joins.get(p, [])}
                nodes, uncovered = set(), set()
                for c in cids:
                    ns = nodes_at(line_of[c]) if c in line_of else set()
                    nodes |= ns
                    if not ns:
                        uncovered.add(c)
                tiers[tier] = nodes
                cov[tier] = {"reference_passages": len(pids),
                             "joined_clauses": len(cids),
                             "clauses_outside_translated_spans": len(uncovered)}
            out[slug] = tiers
            facts[slug] = cov
        return out, facts
    finally:
        os.chdir(_cwd)


def _pipeline_states(match, probe):
    """{slug: {node: engaged | judged_not_engaged}} + retrieval universe."""
    states = defaultdict(dict)
    for slug, b in match["behaviors"].items():
        for row in b["atoms"]:
            for v in row["verdicts"]:
                cur = states[slug].get(v["node"])
                if v["verdict"] == "engaged":
                    states[slug][v["node"]] = "engaged"
                elif cur is None:
                    states[slug][v["node"]] = "judged_not_engaged"
    for slug, rows in (probe or {}).items():
        for v in rows:
            cur = states[slug].get(v["node"])
            if v["verdict"] == "engaged":
                states[slug][v["node"]] = "engaged"
            elif cur is None:
                states[slug][v["node"]] = "judged_not_engaged"
    return states


def step_compare():
    match = json.load(open(os.path.join(OUT, "match.json")))
    probe_p = os.path.join(OUT, "probe.json")
    probe = json.load(open(probe_p))["behaviors"] if os.path.exists(probe_p) \
        else None
    ref_nodes, cov = _panel_reference_nodes()
    states = _pipeline_states(match, probe)
    universe = set(match["universe"])

    report = {"probe_included": probe is not None, "coverage": cov,
              "behaviors": {}}
    lines = ["# Frontier-panel agreement — attention surface, not truth",
             "",
             "Every number below is agreement with a PANEL, adjudicate-"
             "against-the-document before treating any cell as an error."
             f" Probe folded in: {probe is not None}.", ""]
    for slug in SLUGS:
        st = states.get(slug, {})
        engaged = {n for n, s in st.items() if s == "engaged"}
        judged_not = {n for n, s in st.items() if s == "judged_not_engaged"}
        row = {}
        for tier, ref in ref_nodes[slug].items():
            agree_rel = sorted(engaged & ref)
            seat_only = sorted(engaged - ref)
            panel_only_judged = sorted(ref & judged_not)
            panel_only_unseen = sorted((ref - engaged - judged_not) & universe)
            row[tier] = {
                "panel_relevant_translated_nodes": len(ref),
                "agree_relevant": agree_rel,
                "seat_engaged_panel_cold": seat_only,
                "panel_hot_seat_declined": panel_only_judged,
                "panel_hot_never_retrieved": panel_only_unseen,
            }
        row["engaged_total"] = len(engaged)
        row["judged_total"] = len(st)
        report["behaviors"][slug] = row
        t = row["consensus_ge5"]
        lines += [f"## {slug}", "",
                  f"* panel-relevant translated nodes (consensus>=5): "
                  f"{t['panel_relevant_translated_nodes']}"
                  f" — reference clauses with no translated span: "
                  f"{cov[slug]['consensus_ge5']['clauses_outside_translated_spans']}"
                  f" (structural ceiling, not a miss)",
                  f"* agree relevant: {len(t['agree_relevant'])}",
                  f"* seat engaged / panel cold: "
                  f"{len(t['seat_engaged_panel_cold'])}  <- adjudication queue A",
                  f"* panel hot / seat declined: "
                  f"{len(t['panel_hot_seat_declined'])}  <- adjudication queue B",
                  f"* panel hot / never retrieved: "
                  f"{len(t['panel_hot_never_retrieved'])}"
                  + ("  <- run `probe`" if probe is None else
                     " (after probe)"), ""]
    _write("agreement.json", report)
    with open(os.path.join(OUT, "AGREEMENT.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


# ------------------------------------------------------------------ phase C

def step_probe():
    """Judge the panel-relevant nodes phase A never retrieved. Each node is
    judged against its 2 lexically-closest atoms; blind per-pair prompts."""
    match = json.load(open(os.path.join(OUT, "match.json")))
    ref_nodes, _ = _panel_reference_nodes()
    states = _pipeline_states(match, None)
    views = translated_views()
    complete = live_pilot.seat_client()
    out = {}
    for slug in SLUGS:
        atoms = [{"name": r["atom"], "gloss": r["gloss"]}
                 for r in match["behaviors"][slug]["atoms"]]
        targets = sorted(ref_nodes[slug]["any_ge2"]
                         - set(states.get(slug, {})))
        rows = []
        for cid in targets:
            scored = sorted(
                ((BM.lexical_similarity(BM.atom_query_text(a),
                                        BM.node_candidate_text(views[cid])), a)
                 for a in atoms), key=lambda t: -t[0])[:2]
            verdict = "not_engaged"
            grounds = ""
            for _s, a in scored:
                v = BM.judge(complete, BM.build_prompt(a, views[cid]))
                rows.append({"node": cid, "atom": a["name"],
                             "verdict": v["verdict"], "grounds": v["grounds"]})
                if v["verdict"] == "engaged":
                    verdict, grounds = "engaged", v["grounds"]
                    break
        n_eng = sum(1 for r in rows if r["verdict"] == "engaged")
        print(f"  {slug:34s} probed {len(targets)} nodes, "
              f"{n_eng} engagements")
        out[slug] = rows
    c = complete.client
    _write("probe.json", {"model": c.p.model, "calls": c.calls,
                          "spent_usd": round(c.spent_usd, 6),
                          "behaviors": out})


STEPS = {"match": step_match, "compare": step_compare, "probe": step_probe}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=list(STEPS))
    args = ap.parse_args(argv)
    STEPS[args.step]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
