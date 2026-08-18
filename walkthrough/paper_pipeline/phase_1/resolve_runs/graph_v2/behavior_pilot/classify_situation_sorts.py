#!/usr/bin/env python3
"""Situation ontology, take 2 — a TYPED HIERARCHY, not a flat collapse.

Measured (2026-08-18): discovery over 2065 situation concepts produced 1959
proposals and merge collapsed only 6 — the corpus's situation vocabulary is
genuinely SPECIFIC (response_acknowledges_censorship vs
response_includes_disclaimer are different facts), unlike acts, which
collapse to a dozen verbs. Forcing "a few hundred canonicals" would erase
real distinctions. What behaviors and mutation testing need is:
  (1) a SORT for every concept (what kind of thing its first argument is),
      from a small fixed set — request, response, user, content, action,
      instruction, party, setting, information, assistant, tool, other;
  (2) a small set of SHARED SCOPE DIMENSIONS behaviors mutate along, each
      with canonically-distinct values (party: user|third_party|developer;
      intent: benign|ambiguous|illicit; setting: interactive|programmatic|
      agentic; reversibility: reversible|irreversible; content_class:
      permitted|restricted|prohibited) — assigned where a concept EXPRESSES
      a value on a dimension;
  (3) near-duplicate merge ONLY (same meaning, different name), by
      light-stem + gloss check.
Bridges: canonical_concept(<sort>(X)) :- <bespoke>(X).   and
         scope(<dim>, <value>, X) :- <bespoke>(X).   for concepts that
         express a dimension value. Generated beside the corpus.
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "..", ".."))
import live_pilot, translate
INV = json.load(open(os.path.join(HERE, "situation_concepts.json")))
SORTS = ["request", "response", "user", "content", "action", "instruction", "party", "setting", "information", "assistant", "tool", "other"]
DIMS = {"party": ["user", "third_party", "developer", "minor", "society"], "intent": ["benign", "ambiguous", "illicit"],
        "setting": ["interactive", "programmatic", "agentic"], "reversibility": ["reversible", "irreversible"],
        "content_class": ["permitted", "sensitive", "restricted", "prohibited"], "stakes": ["low", "high"]}
BRIEF = ("You type situation concepts from a policy-document translation. For each bespoke concept (name /arity: gloss) give: "
 "\"sort\" — the kind of thing its FIRST argument is, one of " + ", ".join(SORTS) + "; "
 "\"dims\" — an object of scope-dimension values the concept EXPRESSES (only when it clearly does), dimensions and allowed values: "
 + "; ".join(f"{k}: {'|'.join(v)}" for k, v in DIMS.items()) + "; "
 "\"same_as\" — if this concept means the SAME thing as another concept in this batch, that other name, else null. "
 "JSON only: {\"<name>\": {\"sort\": ..., \"dims\": {...}, \"same_as\": null|\"<name>\"}}.")

def main():
    out_p = os.path.join(HERE, "situation_types.json"); out = json.load(open(out_p)) if os.path.exists(out_p) else {}
    complete = live_pilot.seat_client(max_tokens=4000); complete.client.cfg["model"]["format_forcing"] = "json_object"; complete.client.forcing = "json_object"
    translate.set_run_tag("situation_ontology_sorts")
    todo = [n for n in sorted(INV) if n not in out]
    for i in range(0, len(todo), 30):
        b = todo[i:i+30]
        user = "\n".join(f"- {n} /{INV[n]['arity']}: {INV[n]['gloss'][:130]}" for n in b) + "\n\nJSON only."
        try:
            m = re.search(r"\{.*\}", complete(BRIEF, user).get("text", ""), re.S); d = json.loads(m.group(0)) if m else {}
        except Exception as ex: print("batch failed", repr(ex)[:80], flush=True); d = {}
        for n in b:
            v = d.get(n) or {}
            if str(v.get("sort")) in SORTS:
                dims = {k: val for k, val in (v.get("dims") or {}).items() if k in DIMS and val in DIMS[k]}
                out[n] = {"sort": v["sort"], "dims": dims, "same_as": v.get("same_as") if v.get("same_as") in INV else None}
        json.dump(out, open(out_p, "w"), indent=1)
        if (i // 30) % 10 == 0: print(f"typed {min(i+30, len(todo))}/{len(todo)}; ${complete.client.spent_usd:.4f}", flush=True)
    # bridges
    lines = ["% situation_bridges.lp — GENERATED (classify_situation_sorts.py). Typed hierarchy: sort + scope-dimension values.",
             "% canonical_concept(<sort>(X..)) :- <bespoke>(X..).   scope(<dim>,<value>,X) :- <bespoke>(X..)."]
    for n, v in sorted(out.items()):
        ar = INV[n]["arity"] or 0
        vs = ",".join(f"X{i}" for i in range(ar)) if ar else ""
        head = f"{n}({vs})" if ar else n
        lines.append(f"canonical_concept({v['sort']}({'X0' if ar else 'unit'})) :- {head}.")
        for dim, val in v["dims"].items():
            lines.append(f"scope({dim},{val},{'X0' if ar else 'unit'}) :- {head}.")
    open(os.path.join(HERE, "situation_bridges.lp"), "w").write("\n".join(lines) + "\n")
    from collections import Counter
    print(f"DONE: {len(out)} typed; sorts {dict(Counter(v['sort'] for v in out.values()))}; with dims {sum(1 for v in out.values() if v['dims'])}; same_as {sum(1 for v in out.values() if v['same_as'])}; bridges {len(lines)-2}", flush=True)
if __name__ == "__main__": main()
