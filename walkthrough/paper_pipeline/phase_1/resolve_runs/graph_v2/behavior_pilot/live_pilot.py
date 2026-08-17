#!/usr/bin/env python3
"""LIVE behavior-matching pilot — DESIGN.md §5's pre-registered validation
order, executed against the frozen pilot subset (PILOT_SUBSET.md, 2026-08-16).

Steps, cheapest falsifier first (each is a subcommand; artifacts land in
live_run1/ and are the record):

  seat    (~$0.01)  the demo's (atom x candidate) pairs through the REAL
                    small-model seat. The mocked demo expected exactly one
                    engaged node per atom; live verdicts are recorded beside
                    that expectation for adjudication. Divergence from a
                    frontier model on the same brief is a seat defect, not a
                    model failure (rename_seat parity protocol) — the frontier
                    pass is the harness's own context reading seat_report.json,
                    not a metered call.
  atoms   (~$0.01)  decompose the 5 pilot behaviors live (1 call each,
                    behavior_atoms shape: named atoms with glosses). Counts of
                    atoms matching 0 / >3 nodes downstream answer the
                    granularity question (Matt's #7).
  match   (~$0.15)  rank candidates over the pilot subset's node views
                    (live e5 embedder when TOGETHER_API_KEY is set; lexical
                    fallback is REFUSED for the record run — a stand-in ranker
                    would make recall unmeasurable), then adjudicate ALL top-k
                    through the seat (DESIGN open question 2: all-k for the
                    pilot, measure the delta vs first-hit).
  query   (~$0.02)  grounding + clingo: one call per behavior phrases
                    situation facts in the matched modules' declared
                    input/required signatures (validation question 3 — can it
                    do so without inventing predicates? counted mechanically),
                    then relevance_query over the matched nodes reports fired
                    asserts and forbid-vs-does conflicts.

  all               seat -> atoms -> match -> query.

Refinement (stage 4) is deliberately NOT here: it is user-in-the-loop by
design, and an autonomous run pretending to be the user would validate
nothing. Run it with Matt present.

Spend: seat/atom/grounding calls go through translate.Client, so every call
is billed into usage.jsonl with measured cost. Embedding calls bypass the
ledger (curl, recurse_driver._embed_texts) — their cost is recorded in
live_run1/spend.json instead, priced at together's e5 list rate.

Usage:
    TOGETHER_API_KEY=... ../../../../../../semi-formal-experiment/.venv/bin/python \
        live_pilot.py all
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GRAPH_V2 = os.path.dirname(HERE)
PHASE1 = os.path.abspath(os.path.join(GRAPH_V2, "..", ".."))
for p in (HERE, GRAPH_V2, PHASE1):
    sys.path.insert(0, p)

import behavior_match as BM        # noqa: E402
import recurse_driver              # noqa: E402
import translate                   # noqa: E402

OUT = os.path.join(HERE, "live_run1")
SUBSET = json.load(open(os.path.join(HERE, "pilot_subset.json")))
PILOT_BEHAVIORS = json.load(open(os.path.join(HERE, "pilot_behaviors.json")))
NODE_CORPUS_ALL = os.path.join(GRAPH_V2, "node_corpus_all.json")
TOP_K = 5


# ------------------------------------------------------------------ client

class _Args:
    provider = None
    model = None
    max_tokens = None


def seat_client(max_tokens=600):
    """A translate.Client wired for small JSON replies, ledger included."""
    cfg = json.load(open(os.path.join(GRAPH_V2, "config_corpus_all.json")))
    cfg["model"]["format_forcing"] = "json_object"
    cfg["model"]["max_tokens"] = max_tokens
    prov = translate.resolve_provider(cfg, _Args())
    prov.max_tokens = max_tokens
    client = translate.Client(prov, cfg)
    translate.set_run_tag("behavior_pilot/live_run1")

    def complete(system, user):
        return client.complete(system, user)

    complete.client = client
    return complete


def views_subset():
    views = BM.node_views(NODE_CORPUS_ALL)
    keep = set(SUBSET["subset"])
    return {k: v for k, v in views.items() if k in keep}


def live_embed(texts):
    key = os.environ.get("TOGETHER_API_KEY", "")
    if not key:
        cfg = json.load(open(os.path.join(GRAPH_V2, "config_corpus_all.json")))
        prov = translate.resolve_provider(cfg, _Args())
        key = translate._resolve_key(prov)
    if not key:
        raise SystemExit("no together key — the record run refuses the "
                         "lexical fallback (a stand-in, not a measured ranker)")
    vecs = recurse_driver._embed_texts(texts, key)
    if vecs is None:
        raise SystemExit("embedder returned None — refusing to fall back")
    live_embed.batches += 1
    live_embed.texts += len(texts)
    return vecs


live_embed.batches = 0
live_embed.texts = 0


def _write(name, obj):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, sort_keys=True)
    print("wrote", os.path.relpath(p, os.getcwd()))


# ------------------------------------------------------------------ step 1

def step_seat():
    """The demo's atom x candidate pairs, judged by the live seat."""
    views = BM.node_views()                     # the demo runs on the 15-node sample
    atoms = BM.DEMO_ATOMS
    ranked = BM.rank_candidates(atoms, views, embed=None, top_k=TOP_K)
    complete = seat_client()
    rows = []
    for ai, a in enumerate(atoms):
        for score, cid in ranked[ai]:
            prompt = BM.build_prompt(a, views[cid])
            v = BM.judge(complete, prompt)
            expected = BM._DEMO_SEAT_KEY.get((a["name"], cid), "not_engaged")
            rows.append({"atom": a["name"], "node": cid,
                         "lexical_score": round(score, 4),
                         "demo_key_verdict": expected,
                         "agrees_with_demo_key": v["verdict"] == expected,
                         "verdict": v["verdict"], "grounds": v["grounds"]})
            print(f"  {a['name']:28s} {cid:20s} {v['verdict']}")
    c = complete.client
    _write("seat_report.json", {
        "protocol": "live small-model seat on the demo pairs; frontier parity "
                    "pass = adjudicate this file in a fresh frontier context "
                    "against the same BRIEF; divergence is a seat defect",
        "model": c.p.model, "calls": c.calls,
        "spent_usd": round(c.spent_usd, 6), "rows": rows})


# ------------------------------------------------------------------ step 2

ATOM_BRIEF = (
    "You decompose one BEHAVIOR - a described way an AI assistant might act - "
    "into its atomic elements for matching against a policy document. Return "
    "JSON only: {\"atoms\": [{\"name\": snake_case, \"gloss\": one sentence "
    "saying what makes the element present in a situation, \"kind\": one of "
    "act|condition|consideration}]}. 3 to 8 atoms. Each atom is ONE thing a "
    "policy clause could bear on: an act the assistant performs, a condition "
    "of the situation, or a consideration at stake. Do not restate the whole "
    "behavior in every atom, and do not invent policy content - the atoms "
    "describe the BEHAVIOR only.")


def step_atoms():
    complete = seat_client(max_tokens=1500)
    out = {}
    sel = {b["slug"]: b for b in PILOT_BEHAVIORS["behaviors"]}
    for slug in PILOT_BEHAVIORS["selected"]:
        b = sel[slug]
        user = (f"BEHAVIOR: {b['name']}\n\n{b['definition']}\n\n"
                "Decompose. JSON only.")
        env = complete(ATOM_BRIEF, user)
        try:
            atoms = json.loads(env.get("text", ""))["atoms"]
            atoms = [a for a in atoms
                     if re.fullmatch(r"[a-z][a-z0-9_]+", str(a.get("name", "")))
                     and str(a.get("gloss", "")).strip()][:8]
        except Exception as ex:              # noqa: BLE001
            atoms = []
            print(f"  !! {slug}: unparseable decomposition: {ex!r}")
        out[slug] = atoms
        print(f"  {slug:38s} {len(atoms)} atoms: "
              + ", ".join(a["name"] for a in atoms))
    c = complete.client
    _write("atoms.json", {"model": c.p.model, "calls": c.calls,
                          "spent_usd": round(c.spent_usd, 6),
                          "behaviors": out})


# ------------------------------------------------------------------ step 3

def step_match():
    atoms_by_b = json.load(open(os.path.join(OUT, "atoms.json")))["behaviors"]
    views = views_subset()
    complete = seat_client()
    report = {}
    for slug, atoms in atoms_by_b.items():
        if not atoms:
            continue
        ranked = BM.rank_candidates(atoms, views, embed=live_embed, top_k=TOP_K)
        rows = []
        for ai, a in enumerate(atoms):
            verdicts = []
            for score, cid in ranked[ai]:
                v = BM.judge(complete, BM.build_prompt(a, views[cid]))
                verdicts.append({"node": cid, "score": round(score, 4),
                                 "verdict": v["verdict"],
                                 "grounds": v["grounds"]})
            engaged = [v["node"] for v in verdicts if v["verdict"] == "engaged"]
            rows.append({"atom": a["name"], "gloss": a["gloss"],
                         "verdicts": verdicts, "engaged": engaged,
                         "first_hit": engaged[0] if engaged else None})
            print(f"  {slug[:24]:24s} {a['name']:30s} "
                  f"{len(engaged)}/{len(verdicts)} engaged")
        report[slug] = rows
    c = complete.client
    # granularity + cardinality measurements, mechanical
    g = {"atoms_matching_0": 0, "atoms_matching_gt3": 0, "atoms_total": 0,
         "extra_nodes_from_all_k_vs_first_hit": 0}
    for rows in report.values():
        for r in rows:
            g["atoms_total"] += 1
            n = len(r["engaged"])
            g["atoms_matching_0"] += (n == 0)
            g["atoms_matching_gt3"] += (n > 3)
            g["extra_nodes_from_all_k_vs_first_hit"] += max(0, n - 1)
    _write("match_report.json", {
        "model": c.p.model, "seat_calls": c.calls,
        "spent_usd": round(c.spent_usd, 6),
        "embed_batches": live_embed.batches, "embed_texts": live_embed.texts,
        "granularity": g, "behaviors": report})


# ------------------------------------------------------------------ step 4

GROUND_BRIEF = (
    "You phrase the FACTS of a situation in a fixed predicate vocabulary for "
    "a logic query. Return JSON only: {\"facts\": [\"pred(arg, ...)\"...], "
    "\"does\": [\"act_term\"...]}. HARD RULES: every fact must use ONLY "
    "predicates from the provided signature list, at the exact arity shown "
    "(name/2 takes two arguments); arguments are lowercase constants you "
    "coin for this case. `does` lists the act terms the behavior performs, "
    "chosen from the act signatures. If a needed fact has no predicate in "
    "the list, OMIT it and add its would-be predicate name to "
    "{\"missing\": [...]} instead of inventing one.")


def _signatures(node_ids):
    """Declared inputs/requires/acts of the matched modules, from the newest
    artifacts (the same gather as the query)."""
    import link_nodes
    sigs, acts = set(), set()
    for lp, obj, run in link_nodes.gather().values():
        cid = obj.get("clause_id")
        if cid not in node_ids:
            continue
        for k in ("inputs", "requires"):
            for s in obj.get(k) or []:
                sigs.add(str(s))
        for a in obj.get("acts") or []:
            acts.add(str(a))
    return sorted(sigs), sorted(acts)


def step_query():
    atoms_by_b = json.load(open(os.path.join(OUT, "atoms.json")))["behaviors"]
    match = json.load(open(os.path.join(OUT, "match_report.json")))["behaviors"]
    sel = {b["slug"]: b for b in PILOT_BEHAVIORS["behaviors"]}
    complete = seat_client(max_tokens=1200)
    out = {}
    for slug, rows in match.items():
        nodes = sorted({n for r in rows for n in r["engaged"]})
        if not nodes:
            out[slug] = {"matched_nodes": [], "note": "no engaged nodes"}
            continue
        sigs, acts = _signatures(set(nodes))
        b = sel[slug]
        user = (f"THE SITUATION (a behavior under judgment):\n{b['name']} — "
                f"{b['definition']}\n\nATOMS:\n"
                + "\n".join(f"- {a['name']}: {a['gloss']}"
                            for a in atoms_by_b[slug])
                + "\n\nPREDICATE SIGNATURES (the only vocabulary):\n"
                + "\n".join(f"- {s}" for s in sigs)
                + "\n\nACT SIGNATURES:\n"
                + "\n".join(f"- {a}" for a in acts)
                + "\n\nPhrase the case. JSON only.")
        env = complete(GROUND_BRIEF, user)
        try:
            g = json.loads(env.get("text", ""))
            facts = [f for f in g.get("facts", []) if isinstance(f, str)]
            does = [d for d in g.get("does", []) if isinstance(d, str)]
            missing = g.get("missing", [])
        except Exception as ex:              # noqa: BLE001
            facts, does, missing = [], [], [f"unparseable: {ex!r}"]
        # mechanical invention count (validation question 3)
        allowed = {s.split("/")[0] for s in sigs}
        invented = sorted({m.group(1) for f in facts
                           for m in [re.match(r"([a-z_][A-Za-z0-9_]*)\(", f)]
                           if m and m.group(1) not in allowed})
        bid = "b_" + slug.replace("-", "_")
        lp = BM.render_behavior_module(
            bid, f"{b['name']}: {b['definition'][:120]}",
            [f for f in facts
             if (m := re.match(r"([a-z_][A-Za-z0-9_]*)\(", f))
             and m.group(1) in allowed],
            does)
        row = {"matched_nodes": nodes, "facts": facts, "does": does,
               "reported_missing": missing, "invented_predicates": invented}
        try:
            q = BM.relevance_query(nodes, lp)
            row["query"] = q
        except Exception as ex:              # noqa: BLE001
            row["query_error"] = repr(ex)
        out[slug] = row
        qq = row.get("query")
        fired = len(qq.get("relevant_modules") or []) \
            if isinstance(qq, dict) else "?"
        print(f"  {slug:38s} nodes={len(nodes)} facts={len(facts)} "
              f"invented={len(invented)} relevant_modules={fired}")
    c = complete.client
    _write("query_report.json", {"model": c.p.model, "calls": c.calls,
                                 "spent_usd": round(c.spent_usd, 6),
                                 "behaviors": out})


STEPS = {"seat": step_seat, "atoms": step_atoms,
         "match": step_match, "query": step_query}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=list(STEPS) + ["all"])
    args = ap.parse_args(argv)
    for name in (list(STEPS) if args.step == "all" else [args.step]):
        print(f"== {name}")
        STEPS[name]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
