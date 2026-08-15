#!/usr/bin/env python3
"""translation_repair_census.py -- mine every translation run on disk for repair rounds.

NEW FILE. Read-only over runs/ and repair_graveyard/. No network, no spend.

WHAT IT MEASURES
----------------
translate.py's repair loop re-prompts the model with a message of the shape

    attempt N failed these checks:
      - [check_id] where: message
      ...
    Fix every one of them. Return the corrected module, complete.

Each such user message is exactly one PAID EXTRA CALL (the assistant turn that
follows it). So the census counts repair ROUNDS, attributes each round to the
class(es) of finding that caused it, and prices the round from the recorded
usage rows.

Attribution rule: a round is CAUSED BY every class present in it, but its cost
is split evenly across the distinct classes in that round, so the class cost
column sums to the total repair spend (no double counting).

Sources (all read-only):
  phase_1/runs/*/                                     -- flat-clause runs
  phase_1/repair_graveyard/*/                         -- flat-clause graveyard
  .../graph_v2/translation_sample/runs/*/             -- graph-node runs
  .../graph_v2/translation_sample/repair_graveyard/*/ -- graph-node graveyard

Graveyard transcripts are copies of run transcripts; deduplicated by content hash.

Usage:
    .venv/bin/python translation_repair_census.py            # table to stdout
    .venv/bin/python translation_repair_census.py --json     # machine readable
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
USAGE = os.path.join(REPO, "semi-formal-experiment", "usage.jsonl")

# price per Mtok (input, output) -- the rate recorded on every priced usage row
PRICE_IN, PRICE_OUT = 0.14, 0.28

RUN_GLOBS = [
    "runs/*/*.transcript.json",
    "resolve_runs/graph_v2/translation_sample/runs/*/*.transcript.json",
]
GRAVE_GLOBS = [
    "repair_graveyard/*/transcript.json",
    "resolve_runs/graph_v2/translation_sample/repair_graveyard/*/transcript.json",
]

REPAIR_HEAD = re.compile(r"^attempt (\d+) failed these checks:")
FINDING = re.compile(r"^\s*-\s*\[([^\]]+)\]\s*([^:]*):\s*(.*)$")

# ---------------------------------------------------------------------------
# taxonomy -- built from the ACTUAL message shapes observed on disk, not guessed.
# Order matters: first match wins.
# ---------------------------------------------------------------------------
# (family, class, regex). Order matters: first match wins.
TAXONOMY = [
    ("SAFETY", "unsafe-variable",
     r"carries the variable '[^']+'( and there are no conditions to bind it|"
     r" but the body never mentions it)"),
    ("DECLARE", "undeclared-body-name",
     r"body references `[^`]+` but nothing declares it"),
    ("READBACK", "readback-slot-arity",
     r"read_back has \d+ `%` slot\(s\) but \d+ slot entr"),
    ("SYNTAX", "asp-syntax-refused",
     r"clingo refused this program"),
    ("SYNTAX", "asp-body-unparseable",
     r"is not ASP that clingo can parse"),
    ("IDFORM", "concept-name-carries-arity",
     r"concept name '[^']+' is not a predicate name"),
    ("IDFORM", "inputs-entry-not-name-arity",
     r"inputs entry '[^']+' is not name/arity"),
    ("IDFORM", "forbid-body-not-bare-name",
     r"forbid_body `(head|banned)` .* is not a bare predicate name"),
    ("IDFORM", "not-a-term",
     r"is not a term\. It must be a functor"),
    ("ACTS", "act-not-in-acts",
     r"assertion names act '[^']+', which is not in `acts`"),
    ("GLOSS", "borrowed-without-gloss",
     r"is borrowed but has no gloss"),
    ("CLOSURE", "closure-missing",
     r"(no default-closure declaration for act class|"
     r"with no `%% closure:` declaration)"),
    ("CLOSURE", "closure-ungoverned",
     r"closure declared for act class\(es\) .* the module does not govern"),
    ("PROV", "citation-not-in-corpus",
     r"which is not a clause in this corpus"),
    ("PROV", "clause-id-mismatch",
     r"module says clause_id '[^']+' but it was asked to translate"),
    ("MINOR", "empty-body-not-null",
     r"body is present but empty"),
    ("MINOR", "requires-inputs-overlap",
     r"appear in BOTH `requires` and `inputs`"),
    ("MINOR", "abstain-with-content",
     r"abstained but `(claims|concepts)` is non-empty"),
    ("MINOR", "empty-translation",
     r"translated but emitted no assertion, definition, superiority or ontology fact"),
    ("MINOR", "toggleable-licence-mismatch",
     r"(licence `world` but not toggleable|toggleable is for `world` facts only)"),
    ("LINK", "requires-unprovided",
     r"is declared in `%% requires:` and no module in this link scope defines it"),
    ("LINK", "unresolved-reference",
     r"used in a body, defined nowhere in this link scope"),
    ("SYNTAX", "body-prose-connective",
     r"ontology '[^']+': '[^']*'"),
]

CLASS_FAMILY = {c: f for f, c, _ in TAXONOMY}


def classify(check_id: str, message: str) -> str:
    for _fam, name, pat in TAXONOMY:
        if re.search(pat, message):
            return name
    return "OTHER:" + check_id


# ---------------------------------------------------------------------------


def _run_id_from_path(path: str) -> str:
    parts = path.split(os.sep)
    for p in parts:
        if re.match(r"^\d{8}-\d{6}-", p):
            return p
    return parts[-2]


def prompt_generations(root: str):
    """run id -> generation number, keyed on the SYSTEM BLOCK ACTUALLY SENT.

    ⭐ WHY THIS AND NOT git log. The trend that matters is "did the instruction
    change stop the failure", and the instruction as SENT is a concatenation of
    several prompt files chosen by a run's own config. Two runs on the same
    commit can send different system blocks, and a run can be replayed against
    an older prompt. `prompt_system.txt` in the run directory is the bytes the
    model saw; hashing it groups runs by what they were actually told.
    """
    seen, gen = {}, {}
    paths = sorted(glob.glob(os.path.join(root, "runs/*/prompt_system.txt")))
    paths += sorted(glob.glob(os.path.join(
        root, "resolve_runs/graph_v2/translation_sample/runs/*/prompt_system.txt")))
    for p in sorted(paths, key=lambda x: os.path.basename(os.path.dirname(x))):
        run = os.path.basename(os.path.dirname(p))
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:8]
        if h not in seen:
            seen[h] = len(seen) + 1
        gen[run] = seen[h]
    return gen, {v: k for k, v in seen.items()}


def _system_chars(root: str, run: str) -> int:
    """Size of the SYSTEM block actually sent on that run. Every call -- first
    attempt and every repair -- resends it, so it dominates the input side."""
    for base in ("runs", "resolve_runs/graph_v2/translation_sample/runs"):
        p = os.path.join(root, base, run, "prompt_system.txt")
        if os.path.exists(p):
            return len(open(p, encoding="utf-8").read())
    return 36000  # observed median across runs


def collect_rounds(root: str):
    """Return list of round dicts, deduplicated across run/graveyard copies."""
    seen_transcripts = set()
    rounds = []
    clauses = {}  # (run, clause) -> {'attempts': n}
    first_calls = []  # the attempt-1 call for every clause (the unavoidable one)

    paths = []
    for g in RUN_GLOBS:
        paths += [(p, "run") for p in sorted(glob.glob(os.path.join(root, g)))]
    for g in GRAVE_GLOBS:
        paths += [(p, "graveyard") for p in sorted(glob.glob(os.path.join(root, g)))]

    for path, origin in paths:
        try:
            msgs = json.load(open(path))
        except Exception:
            continue
        blob = json.dumps(msgs, sort_keys=True).encode()
        h = hashlib.sha256(blob).hexdigest()
        if h in seen_transcripts:
            continue
        seen_transcripts.add(h)

        run = _run_id_from_path(path)
        if origin == "graveyard":
            ent = os.path.join(os.path.dirname(path), "entry.json")
            if os.path.exists(ent):
                e = json.load(open(ent))
                run = e.get("run", run)
                clause = e.get("clause_id", "?")
            else:
                clause = os.path.basename(os.path.dirname(path))
        else:
            clause = os.path.basename(path)[: -len(".transcript.json")]

        n_calls = sum(1 for m in msgs if m["role"] == "assistant")
        clauses[(run, clause)] = {"attempts": n_calls, "origin": origin}
        sys_chars = _system_chars(root, run)
        if msgs and msgs[0]["role"] == "user":
            first_calls.append({
                "run": run, "clause": clause,
                "prompt_chars": sys_chars + len(msgs[0]["content"]),
                "completion_chars": len(msgs[1]["content"]) if len(msgs) > 1 else 0,
            })

        for i, m in enumerate(msgs):
            if m["role"] != "user" or i == 0:
                continue
            head = REPAIR_HEAD.match(m["content"].strip())
            if not head:
                continue
            attempt = int(head.group(1))
            findings = []
            for line in m["content"].splitlines():
                fm = FINDING.match(line)
                if fm:
                    findings.append({
                        "check_id": fm.group(1),
                        "where": fm.group(2).strip(),
                        "message": fm.group(3).strip(),
                        "class": classify(fm.group(1), fm.group(3).strip()),
                    })
            # completion chars of the retry this round bought
            reply = msgs[i + 1]["content"] if i + 1 < len(msgs) else ""
            prompt_chars = sys_chars + sum(len(x["content"]) for x in msgs[: i + 1])
            rounds.append({
                "run": run,
                "clause": clause,
                "failed_attempt": attempt,
                "round_index": attempt,  # round N repairs attempt N
                "findings": findings,
                "classes": sorted({f["class"] for f in findings}),
                "prompt_chars": prompt_chars,
                "completion_chars": len(reply),
                # the MODULE that failed -- the assistant turn this round repairs.
                # Kept so the census can be replayed through the live checks.
                "failing_raw": msgs[i - 1]["content"],
            })
    return rounds, clauses, first_calls


# ---------------------------------------------------------------------------
# cost model
# ---------------------------------------------------------------------------

def usage_rows():
    if not os.path.exists(USAGE):
        return []
    out = []
    for line in open(USAGE):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("provider") == "together-deepseek-v4-flash":
            out.append(r)
    return out


def calibrate(rows):
    """chars-per-token, from the recorded rows. Returns (in_cpt, out_cpt, mean_cost)."""
    # completion side: content_chars / completion_tokens on non-truncated rows
    ratios = [r["content_chars"] / r["completion_tokens"]
              for r in rows
              if r.get("completion_tokens") and r.get("content_chars")]
    out_cpt = sorted(ratios)[len(ratios) // 2] if ratios else 3.6
    costed = [r["cost_usd"] for r in rows if r.get("cost_usd")]
    mean_cost = sum(costed) / len(costed) if costed else 0.0
    # cached-input share -- repair rounds resend the whole transcript, and the
    # system block is cached; measure the empirical cached fraction.
    cached = [r.get("cached_input_tokens", 0) for r in rows if r.get("cost_usd")]
    prompt = [r.get("prompt_tokens", 0) for r in rows if r.get("cost_usd")]
    cached_share = (sum(cached) / sum(prompt)) if sum(prompt) else 0.0
    return out_cpt, mean_cost, cached_share, len(costed)


def price_round(rnd, in_cpt, out_cpt, cached_share):
    """Model the paid cost of one repair round from its own transcript size.

    Together bills cached input at the same $0.14/Mtok on this account (every
    recorded row prices prompt_tokens whole -- see cost_usd vs prompt_tokens),
    so cached_share is reported but not discounted.
    """
    p_tok = rnd["prompt_chars"] / in_cpt
    c_tok = rnd["completion_chars"] / out_cpt
    return (p_tok * PRICE_IN + c_tok * PRICE_OUT) / 1e6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--root", default=HERE)
    ap.add_argument("--gen", type=int, default=None,
                    help="restrict to one prompt generation (see --list-gens); "
                         "-1 means the newest")
    ap.add_argument("--list-gens", action="store_true")
    args = ap.parse_args()

    rounds, clauses, first_calls = collect_rounds(args.root)
    gens, hashes = prompt_generations(args.root)
    for r in rounds:
        r["gen"] = gens.get(r["run"])
    for f in first_calls:
        f["gen"] = gens.get(f["run"])

    if args.list_gens:
        for g in sorted(hashes):
            rs = sorted(r for r, v in gens.items() if v == g)
            n_cl = sum(1 for (run, _c) in clauses if gens.get(run) == g)
            n_rd = sum(1 for r in rounds if r["gen"] == g)
            print(f"gen {g:2} {hashes[g]}  runs={len(rs):2} clauses={n_cl:3} "
                  f"rounds={n_rd:3} "
                  f"rounds/clause={n_rd/n_cl if n_cl else 0:.2f}  "
                  f"{rs[0]} .. {rs[-1]}")
        return

    if args.gen is not None:
        g = max(hashes) if args.gen == -1 else args.gen
        rounds = [r for r in rounds if r["gen"] == g]
        first_calls = [f for f in first_calls if f["gen"] == g]
        clauses = {k: v for k, v in clauses.items() if gens.get(k[0]) == g}
        print(f"### RESTRICTED TO PROMPT GENERATION {g} ({hashes[g]}) ###\n")
    rows = usage_rows()
    out_cpt, mean_cost, cached_share, n_costed = calibrate(rows)
    in_cpt = out_cpt  # same tokenizer both directions

    total_rounds = len(rounds)
    for r in rounds:
        r["cost"] = price_round(r, in_cpt, out_cpt, cached_share)
    for f in first_calls:
        f["cost"] = price_round(f, in_cpt, out_cpt, cached_share)

    # --- VALIDATION of the cost model against the recorded rows ------------
    # Modelled cost of every call we can see == recorded cost of the deepseek
    # rows in the same window. Reported so the price column can be trusted.
    modelled_all = sum(r["cost"] for r in rounds) + sum(f["cost"] for f in first_calls)
    n_calls_seen = len(rounds) + len(first_calls)
    modelled_mean = modelled_all / n_calls_seen if n_calls_seen else 0.0

    by_class = defaultdict(lambda: {"rounds": 0, "findings": 0, "cost": 0.0,
                                    "runs": Counter(), "clauses": set()})
    for r in rounds:
        n = len(r["classes"]) or 1
        for c in r["classes"]:
            b = by_class[c]
            b["rounds"] += 1
            b["cost"] += r["cost"] / n
            b["runs"][r["run"]] += 1
            b["clauses"].add((r["run"], r["clause"]))
        for f in r["findings"]:
            by_class[f["class"]]["findings"] += 1

    total_cost = sum(r["cost"] for r in rounds)
    first_cost = sum(f["cost"] for f in first_calls)

    by_family = defaultdict(lambda: {"rounds": set(), "cost": 0.0})
    for r in rounds:
        n = len(r["classes"]) or 1
        for c in r["classes"]:
            fam = CLASS_FAMILY.get(c, "OTHER")
            by_family[fam]["rounds"].add((r["run"], r["clause"], r["round_index"]))
            by_family[fam]["cost"] += r["cost"] / n

    if args.json:
        print(json.dumps({
            "total_rounds": total_rounds,
            "total_repair_cost_usd": total_cost,
            "first_call_cost_usd": first_cost,
            "clauses_seen": len(clauses),
            "calibration": {"chars_per_token": out_cpt,
                            "mean_recorded_call_cost_usd": mean_cost,
                            "modelled_mean_call_cost_usd": modelled_mean,
                            "cached_input_share": cached_share,
                            "priced_rows": n_costed},
            "families": {f: {"rounds": len(v["rounds"]), "cost_usd": v["cost"]}
                         for f, v in by_family.items()},
            "classes": {
                c: {"family": CLASS_FAMILY.get(c, "OTHER"),
                    "rounds": v["rounds"], "findings": v["findings"],
                    "cost_usd": v["cost"],
                    "share_of_rounds": v["rounds"] / total_rounds,
                    "runs": dict(v["runs"])}
                for c, v in by_class.items()},
            "rounds": [{k: v for k, v in r.items() if k not in ("findings", "failing_raw")} for r in rounds],
        }, indent=1))
        return

    print(f"transcripts deduped; clauses seen: {len(clauses)}; "
          f"total calls seen: {n_calls_seen}")
    print(f"repair rounds (= paid EXTRA calls): {total_rounds} "
          f"({total_rounds/n_calls_seen:.0%} of all calls)")
    print(f"calibration: {out_cpt:.2f} chars/token (median of {n_costed} priced rows); "
          f"cached input share {cached_share:.0%}")
    print(f"COST MODEL CHECK: modelled mean call ${modelled_mean:.5f} "
          f"vs recorded mean call ${mean_cost:.5f} "
          f"({modelled_mean/mean_cost:.2f}x)" if mean_cost else "")
    print(f"modelled first-attempt spend: ${first_cost:.4f}")
    print(f"modelled REPAIR spend:        ${total_cost:.4f}  "
          f"({total_cost/(total_cost+first_cost):.0%} of translation spend is repair)")
    print()
    hdr = (f"{'family':9} {'class':30} {'rounds':>7} {'share':>7} "
           f"{'findings':>9} {'cost$':>9} {'clauses':>8}")
    print(hdr)
    print("-" * len(hdr))
    for c, v in sorted(by_class.items(), key=lambda kv: -kv[1]["cost"]):
        print(f"{CLASS_FAMILY.get(c,'OTHER'):9} {c:30} {v['rounds']:7d} "
              f"{v['rounds']/total_rounds:6.1%} "
              f"{v['findings']:9d} {v['cost']:9.4f} {len(v['clauses']):8d}")
    print()
    print(f"{'FAMILY ROLLUP':40} {'rounds':>7} {'share':>7} {'cost$':>9}")
    for f, v in sorted(by_family.items(), key=lambda kv: -kv[1]["cost"]):
        print(f"{f:40} {len(v['rounds']):7d} "
              f"{len(v['rounds'])/total_rounds:6.1%} {v['cost']:9.4f}")
    print()
    print("TREND (rounds per class per run, chronological)")
    runs = sorted({r["run"] for r in rounds})
    for c, v in sorted(by_class.items(), key=lambda kv: -kv[1]["cost"]):
        cells = " ".join(f"{v['runs'].get(rn,0):>3}" for rn in runs)
        print(f"{c:30} {cells}")
    print()
    for i, rn in enumerate(runs):
        print(f"  col {i+1}: {rn}")


if __name__ == "__main__":
    main()
