"""Extract every shape-flipping clause and its draws, for hand classification.

    ../../../../semi-formal-experiment/.venv/bin/python _debug_gen11/flip_classify/extract_flips.py

Run from phase_1/.  ZERO API spend: pure re-analysis of draws already on disk.
Reuses _debug_gen11/d1_recruit/census.py for collection and for the SHAPE
definition, so the 33/112 headline and this dump cannot drift apart.

Writes  _debug_gen11/flip_classify/flips.json   (machine)
        _debug_gen11/flip_classify/flips.txt    (the reading dump: span + draws)
"""
import os, sys, json, glob, collections

HERE = os.path.dirname(os.path.abspath(__file__))
P1 = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, P1)
sys.path.insert(0, os.path.join(P1, "_debug_gen11/d1_recruit"))
import census                                                    # noqa: E402


def shape(d):
    if d["n_hard"] and d["n_prefer"]:
        return "mixed"
    if d["n_hard"]:
        return "hard"
    if d["n_prefer"]:
        return "prefer"
    return "none"


def find_prompt(run, clause):
    p = os.path.join(P1, "resolve_runs/graph_v2/translation_sample/runs",
                     run, clause + ".prompt_user.txt")
    return open(p).read() if os.path.exists(p) else None


def main():
    draws = [census.measure(d) for d in
             census.collect_runs(census.RUNS_GLOB, "graph_v2") + census.collect_ab()]
    by_clause = collections.defaultdict(list)
    for d in draws:
        by_clause[d["clause"]].append(d)

    corpus = json.load(open(os.path.join(P1, "resolve_runs/graph_v2/node_corpus_all.json")))
    recs = corpus["clauses"] if isinstance(corpus, dict) else corpus
    quote = {r["id"]: r.get("quote", "") for r in recs}
    kind = {r["id"]: r.get("kind", "") for r in recs}
    secp = {r["id"]: r.get("section_path", "") for r in recs}

    flips, out = [], []
    for c in sorted(by_clause):
        v = [d for d in by_clause[c] if not d["unparsed"]]
        if len(v) < 2:
            continue
        shapes = [shape(d) for d in v]
        if len(set(shapes)) < 2:
            continue
        flips.append(c)
        rec = dict(clause=c, kind=kind.get(c), section=secp.get(c),
                   quote=quote.get(c, ""), quote_len=len(quote.get(c, "")),
                   shapes=shapes, draws=[])
        prompt = None
        for d in v:
            if prompt is None and d["source"] == "graph_v2":
                prompt = find_prompt(d["run"], c)
            o = d["obj"] or {}
            rec["draws"].append(dict(
                run=d.get("tag") or d["run"], source=d["source"],
                system_sha=d["system_sha"], user_sha=d["user_sha"],
                attempts=d["attempts"], shape=shape(d),
                outcome=o.get("outcome"),
                claims=o.get("claims"),
                asserts=[dict(status=a.get("status"), act=a.get("act"),
                              body=a.get("body"), read_back=a.get("read_back"),
                              bearer=a.get("bearer"))
                         for a in (o.get("asserts") or []) if isinstance(a, dict)],
                ontology=[dict(head=x.get("head"), body=x.get("body"),
                               read_back=x.get("read_back"))
                          for x in (o.get("ontology") or []) if isinstance(x, dict)],
                abstain_reason=o.get("abstain_reason") or o.get("reason"),
            ))
        rec["prompt_user"] = prompt
        out.append(rec)

    json.dump(dict(n_multi=sum(1 for c, v in by_clause.items()
                               if len([d for d in v if not d["unparsed"]]) >= 2),
                   n_flip=len(flips), flips=flips, records=out),
              open(os.path.join(HERE, "flips.json"), "w"), indent=1, default=str)

    with open(os.path.join(HERE, "flips.txt"), "w") as f:
        W = f.write
        W(f"SHAPE-FLIPPING CLAUSES: {len(flips)} of "
          f"{sum(1 for c, v in by_clause.items() if len([d for d in v if not d['unparsed']]) >= 2)}"
          " multi-draw clauses\n\n")
        for rec in out:
            W("=" * 100 + "\n")
            W(f"{rec['clause']}   kind={rec['kind']}   shapes={rec['shapes']}\n")
            W(f"section: {rec['section']}\n")
            body = rec['quote'] or (rec['prompt_user'] or '(no span on disk)')
            W(f"--- SPAN / NODE PROMPT ({len(body)} chars,"
              f" src={'corpus' if rec['quote'] else 'prompt_user'}) ---\n{body}\n")
            for d in rec["draws"]:
                W(f"\n  -- DRAW {d['run']} shape={d['shape']} outcome={d['outcome']}"
                  f" attempts={d['attempts']} sys={d['system_sha']} user={d['user_sha']}\n")
                if d["abstain_reason"]:
                    W(f"     abstain_reason: {d['abstain_reason']}\n")
                for cl in (d["claims"] or []):
                    W(f"     claim: {cl}\n")
                for a in d["asserts"]:
                    W(f"     ASSERT status={a['status']} act={a['act']} body={a['body']}\n")
                    W(f"            read_back: {a['read_back']}\n")
                for x in d["ontology"]:
                    W(f"     ONT  {x['head']} :- {x['body']}\n")
            W("\n")
    print(f"{len(flips)} flipping clauses; wrote flips.json + flips.txt")
    for c in flips:
        print("  ", c)


if __name__ == "__main__":
    main()
