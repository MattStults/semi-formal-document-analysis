#!/usr/bin/env python3
"""Adapter: graph nodes -> a translate.py corpus, for the translation sample.

Emits (a) node_corpus.json in the exact shape modelspec_clauses.json has
(spec / source_sha256 / clauses[{id, locator, quote, kind}]), and (b)
config_graph_nodes.json -- phase_1/config.json with only the corpus block,
output dirs, and run label repointed. No watched prompt file is touched: the
node's structure (establishes, canonical provides/needs names with prose,
verbatim span text) is packed into the row's text field, so the translator
receives the ASSIGNED names -- the whole point of decomposition-first.

Sample: deterministic (seed 42), stratified to cover the shapes translation
must handle -- the merged ordering node, an Under-18 delta (long-range needs),
a heading-authority node, definition/rule/fact nodes, and one node with a
dangling need. Override with --ids.

Usage:
  python3 node_corpus.py                  # write corpus + config for 15 nodes
  python3 node_corpus.py --ids L1-170_n028 L4572-4691_n011
  python3 node_corpus.py --all                # every node of --graph
                                              # (default recurse/root/graph.json)
Then (run from phase_1/ — the --config path is relative to it; a bare run is
a DRY RUN that sends nothing, --live spends; there is no --dry-run flag):
  cd ../..                                     # phase_1
  VENV=../../../semi-formal-experiment/.venv/bin/python
  $VENV translate.py --config resolve_runs/graph_v2/config_graph_nodes.json
"""
import argparse
import hashlib
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO = os.path.abspath(os.path.join(PHASE1, "..", ".."))
GRAPH = os.path.join(HERE, "recurse", "root", "graph.json")
DOC = os.path.join(REPO, "..", "specs", "openai-model-spec", "model_spec.md")

MUST_HAVE = [           # the shapes the sample exists to exercise
    "L1-170_n028",      # the merged authority-ordering node (multi-span)
    "L4572-4691_n011",  # Under-18 delta: long-range needs incl. renamed edge
    "L3995-4164_n001",  # section-scoped heading-authority node
    "L797-809_n001",    # section-lead provider (stay_in_bounds_principles)
    "L1108-1368_n004",  # a needer of the external dangling usage_policies
]


def nm(x):
    return x if isinstance(x, str) else x["name"]


def asp_id(node_id):
    """Graph ids (L527-796_n012) are NOT valid ASP constants -- uppercase L
    parses as a variable and the hyphen as subtraction, so any module that
    renders its clause id into the logic (every `asserts`) is refused by
    clingo. Discovered via the worked-example gate, 2026-08-10. The corpus
    therefore carries an ASP-safe alias; the original id stays in `locator`.
    """
    return node_id.replace("-", "_").lower()


def span_text(lines, node):
    out = []
    for sp in node.get("spans", []):
        a, b = sp["lines"]
        seg = "\n".join(lines[a - 1:b])
        if sp.get("quote"):
            seg += f'\n[node narrows this span to: "{sp["quote"]}"]'
        out.append(f"L{a:04d}-L{b:04d}:\n{seg}")
    return "\n---\n".join(out)


def kind_of(node):
    e = node["establishes"].lower()
    if "rank" in e or "order" in e or "hierarch" in e:
        return "ordering"
    if node.get("provides") and not node.get("needs"):
        return "definitional"
    if "example demonstrat" in e or "worked example" in e:
        return "meta"
    return "conditional"


def row(node, lines):
    fmt = lambda xs: "\n".join(          # noqa: E731
        f"  - {nm(x)}: {x.get('prose', '') if isinstance(x, dict) else ''}"
        for x in xs) or "  (none)"
    text = (
        "GRAPH NODE (from the document-decomposition graph; translate the "
        "node's claim, grounded in its source text)\n\n"
        f"ESTABLISHES (the one claim this module must express):\n"
        f"{node['establishes']}\n\n"
        f"PROVIDES (use EXACTLY these names as the predicates this module "
        f"defines):\n{fmt(node.get('provides', []))}\n\n"
        f"NEEDS -- these concepts are established by OTHER nodes of the "
        f"graph, so every one of them belongs in this module's `requires`, "
        f"spelled EXACTLY as given; never in `ontology`, never defined "
        f"here. `inputs` is only for plain facts about the situation being "
        f"judged (messages, roles, case data) that YOU identify -- a name "
        f"can never appear in both requires and inputs:\n"
        f"{fmt(node.get('needs', []))}\n\n"
        f"CITATION: every ontology/asserts entry that cites a source must "
        f"cite EXACTLY '{asp_id(node['id'])}' -- the id of this node. Never "
        f"cite line numbers, line ranges, or any other id.\n\n"
        f"SOURCE TEXT (verbatim from the document; the L-numbers locate "
        f"text, they are not citable ids):\n{span_text(lines, node)}")
    spans = ",".join(f"L{s['lines'][0]}-{s['lines'][1]}"
                     for s in node.get("spans", []))
    return {"id": asp_id(node["id"]),
            "locator": f"graph_v2@2026-08-10 > {node['id']} > {spans}",
            "section_path": [], "section_id": "graph_node",
            "quote": text, "kind": kind_of(node)}


def select_ids(g, n=15, ids=None, all_nodes=False):
    """Which nodes go in the corpus. Default: the stratified 15-sample,
    byte-identical to what this script has always emitted. `--ids` overrides;
    `--all` emits EVERY node of the graph in graph order (full-corpus mode)."""
    if all_nodes:
        return [node["id"] for node in g["nodes"]]
    if ids:
        return list(ids)
    rng = random.Random(42)
    pool = [node["id"] for node in g["nodes"] if node["id"] not in MUST_HAVE]
    return MUST_HAVE + rng.sample(pool, max(0, n - len(MUST_HAVE)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=15)
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--all", action="store_true",
                    help="emit every node of --graph (full-corpus mode)")
    ap.add_argument("--graph", default=GRAPH,
                    help="graph.json to read (default: recurse/root/graph.json)")
    args = ap.parse_args()
    g = json.load(open(args.graph))
    by_id = {n["id"]: n for n in g["nodes"]}
    doc = open(DOC).read()
    lines = doc.splitlines()

    ids = select_ids(g, n=args.n, ids=args.ids, all_nodes=args.all)
    missing = [i for i in ids if i not in by_id]
    assert not missing, f"unknown node ids: {missing}"

    corpus = {"spec": "graph_v2 node sample (post-audit graph, 2026-08-10)",
              "source_sha256": hashlib.sha256(doc.encode()).hexdigest(),
              "clauses": [row(by_id[i], lines) for i in ids]}
    cpath = os.path.join(HERE, "node_corpus.json")
    json.dump(corpus, open(cpath, "w"), indent=1)

    cfg = json.load(open(os.path.join(PHASE1, "config.json")))
    cfg["corpus"] = dict(
        cfg["corpus"],
        path="node_corpus.json",
        description=("a document-decomposition graph node: a single claim "
                     "from the OpenAI Model Spec with assigned predicate "
                     "names and its verbatim source text"))
    # every other relative path resolves against THIS config's directory
    # (translate.rel), so point them back at phase_1's real files
    # the clause-shaped worked example teaches the wrong citation and field
    # habits for node input (measured 2026-08-10); swap in the node-shaped one
    cfg["prompt"]["system_files"] = [
        "node_worked_example.md" if "worked_example" in p else "../../" + p
        for p in cfg["prompt"]["system_files"]]
    unused = ["../../" + p for p in cfg["prompt"].get("unused_files", [])]
    # the displaced clause-shaped example, deliberately not sent
    unused.append("../../prompt/20_worked_example.md")
    # graph_v2's own docs/logs live beside this config; none are prompt text
    unused += sorted(
        f for f in os.listdir(HERE)
        if f.endswith(".md") and f != "node_worked_example.md")
    cfg["prompt"]["unused_files"] = unused
    pj = cfg["model"].get("providers_json")
    if pj and not os.path.isabs(pj):
        cfg["model"]["providers_json"] = "../../" + pj
    cfg["output"]["dir"] = "translation_sample/runs"
    cfg["graveyard"]["dir"] = "translation_sample/repair_graveyard"
    # select OUR sample, not phase_1's eval section
    cfg["select"] = dict(cfg["select"], clause_ids=[asp_id(i) for i in ids],
                         section_id=None, kinds=[])
    # node texts are ~3x clause size, so the worst-case estimate (full
    # max_tokens out per node, repair growth) exceeds phase_1's $0.25 gate.
    # Raised DELIBERATELY for this sample; realistic spend is ~10-20% of it.
    # ⛔ THIS VALUE CARRIES A HUMAN RULING AND THE GENERATOR MUST NOT ERASE IT
    # (review finding F-A, 2026-08-15). This file GENERATES
    # config_graph_nodes.json, so a routine `python3 node_corpus.py` refresh
    # rewrites the whole `cost` block from phase_1/config.json. Until this
    # line was fixed it wrote 1.00 back and DELETED the `_ceiling_note` that
    # records why the ceiling moved — silently reverting the ruling. The note
    # is therefore emitted HERE, by the generator, not patched into the JSON
    # by hand; a hand-patch is exactly what the next refresh would lose.
    #
    # The old comment here said "5-attempt worst case prices at ~$0.99
    # (triangular growth)". That was true and is now FALSE: stage 2's repair
    # loop may discard a frozen transcript and redraw the clause once, so a
    # clause's worst case is TWO chains of max_attempts and run() prices it by
    # doubling the single-chain estimate. Measured: $0.9970 single-chain,
    # $1.9940 doubled. Realistic spend remains ~10-20% of the worst case
    # (0.89x-1.28x of the old policy, since the truncated chain nearly pays
    # for the redraw) — but a gate is priced on the worst case, not the mean.
    _CEILING_NOTE = (
        "RAISED 1.00 -> 2.00 by the human, 2026-08-15, and the raise is "
        "MINIMAL BY RULING. Stage 2's repair loop may DISCARD a frozen "
        "transcript and redraw the clause once from attempt 1, so a clause's "
        "worst case is TWO chains of max_attempts, and run() prices it by "
        "doubling the single-chain estimate. This selection prices $0.9970 "
        "single-chain and $1.9940 doubled, so the old $1.00 ceiling refused "
        "it with a CostGateError before a single call. The doubling is REAL "
        "COST -- a second sampled draw that is actually paid for -- not an "
        "estimation artefact, so the answer is a ceiling that admits it and "
        "not a cheaper estimate. 2.00 exactly, NOT 2.50 and not 'with "
        "headroom': a ceiling with slack is a ceiling that has stopped being "
        "a constraint, and this one must still bite the next time the worst "
        "case moves (16 nodes already prices $2.1267 and is refused). "
        "Grounds and the measured figures: the 2026-08-15 chain-policy "
        "adversarial-review entry in EXPERIMENTS.md (finding P5), and the "
        "generator-erasure finding F-A in the same file."
    )
    cfg["cost"] = dict(cfg["cost"], _ceiling_note=_CEILING_NOTE,
                       max_cost_usd=2.00)
    # run-5 evidence: the residual failures are single-instance craft slips,
    # not classes; the honest lever is repair budget (each attempt costs
    # ~$0.001-0.004), not more prompt prose
    cfg["repair"] = dict(cfg["repair"], max_attempts=5)
    # run-7's l527_796_n022 died to a single truncated draw; the driver
    # measured truncation as per-draw stochastic on this provider
    cfg["model"] = dict(cfg["model"], resample_truncation=2)
    cfg["_graph_sample"] = ("Generated by node_corpus.py -- corpus and output "
                            "dirs repointed; prompts, model, gates untouched.")
    json.dump(cfg, open(os.path.join(HERE, "config_graph_nodes.json"), "w"),
              indent=1)
    print(f"{len(ids)} nodes -> node_corpus.json; config_graph_nodes.json "
          f"written. Ids: {', '.join(ids[:6])}...")


if __name__ == "__main__":
    main()
