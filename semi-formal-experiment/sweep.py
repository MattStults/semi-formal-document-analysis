"""Expressibility sweep harness (prototype plan step 1).

Usage:
  .venv/bin/python sweep.py --inventory behaviors.jsonl --vocab vocabulary_pilot.json \
      --providers providers.json --provider kimi [--live] [--out sweep_report.md]

Inventory format (JSONL): {"name": ..., "definition": ...} per line.

Default is DRY RUN: prompts are written to prompt_log/ and the report counts
what WOULD be sent. Live runs require --live plus a resolvable key for the
chosen provider. With --self-check, runs the checker over hand-authored
definitions in a JSON file instead of calling any LLM (used for testing the
harness itself).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dsl import Vocabulary, DerivedPredicate
from checker import check_definition
from providers import ProviderConfig, make_client
from translate import translate_behavior


def classify(defn: DerivedPredicate, verdict):
    unmapped = [c for c, a in defn.concept_map.items() if a is None]
    mapped = [c for c, a in defn.concept_map.items() if a]
    if not mapped:
        return "INEXPRESSIBLE"
    if unmapped:
        return "PARTIAL"
    return "EXPRESSIBLE" if verdict.ok else "DEGENERATE"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory")
    ap.add_argument("--vocab", default="vocabulary_pilot.json")
    ap.add_argument("--providers", default="providers.json")
    ap.add_argument("--provider")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--self-check", help="JSON file of hand-authored definitions; no LLM")
    ap.add_argument("--out", default="sweep_report.md")
    ap.add_argument("--json-out", help="machine-readable results for downstream joins")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    vocab = Vocabulary.load(os.path.join(here, args.vocab)
                            if not os.path.isabs(args.vocab) else args.vocab)
    vocab_errs = vocab.validate()
    if vocab_errs:
        print("VOCABULARY INVALID:")
        for e in vocab_errs:
            print(" -", e)
        sys.exit(1)

    rows = []
    if args.self_check:
        with open(args.self_check) as f:
            for d in json.load(f):
                defn = DerivedPredicate(name=d["name"], expr=d["expr"],
                                        concept_map=d.get("concept_map", {}))
                verdict = check_definition(defn, vocab)
                rows.append((defn.name, classify(defn, verdict), defn, verdict, []))
    else:
        providers = ProviderConfig.load_all(args.providers)
        prov = next((p for p in providers if p.name == args.provider), None)
        if prov is None:
            print(f"unknown provider {args.provider!r}; available: "
                  f"{[p.name for p in providers]}")
            sys.exit(1)
        client = make_client(prov, live=args.live,
                             log_dir=os.path.join(here, "prompt_log"))
        with open(args.inventory) as f:
            inventory = [json.loads(line) for line in f if line.strip()]
        for item in inventory:
            r = translate_behavior(client, vocab, item["name"], item["definition"])
            if r.dry_run:
                rows.append((item["name"], "DRY-RUN", None, None, []))
            else:
                rows.append((item["name"], classify(r.obj, r.verdict),
                             r.obj, r.verdict, r.escalations))

    counts = Counter(status for _, status, *_ in rows)
    lines = ["# Expressibility sweep report", "",
             f"vocabulary: {args.vocab} ({len(vocab.atoms)} atoms, "
             f"{len(vocab.axioms)} axioms)", "",
             "| status | count |", "|---|---|"]
    for status, n in counts.most_common():
        lines.append(f"| {status} | {n} |")
    lines.append("")
    for name, status, defn, verdict, escal in rows:
        lines.append(f"## {name}: {status}")
        if defn is not None:
            unmapped = [c for c, a in defn.concept_map.items() if a is None]
            if unmapped:
                lines.append("unmapped concepts (deterministic signal):")
                for c in unmapped:
                    lines.append(f"  - {c}")
            if verdict and verdict.witness:
                lines.append(f"witness world: `{', '.join(verdict.witness)}`")
            if verdict and verdict.errors:
                lines.append(f"errors: {verdict.errors}")
        if escal:
            lines.append(f"escalations proposed: {escal}")
        lines.append("")
    out = os.path.join(here, args.out) if not os.path.isabs(args.out) else args.out
    with open(out, "w") as f:
        f.write("\n".join(lines))

    if args.json_out:
        jpath = (os.path.join(here, args.json_out)
                 if not os.path.isabs(args.json_out) else args.json_out)
        payload = {"vocabulary": args.vocab,
                   "source": args.self_check or f"{args.provider}"
                             + ("(live)" if args.live else "(dry)"),
                   "results": []}
        for name, status, defn, verdict, escal in rows:
            payload["results"].append({
                "name": name, "status": status,
                "concept_map": defn.concept_map if defn else None,
                "expr": defn.expr if defn else None,
                "atoms_used": sorted(set(defn.atoms_used())) if defn else [],
                "witness": verdict.witness if verdict else None,
                "escalations": escal,
            })
        with open(jpath, "w") as f:
            json.dump(payload, f, indent=1)
        print(f"json -> {jpath}")
    print(f"{len(rows)} behaviors, {dict(counts)} -> {out}")


if __name__ == "__main__":
    main()
