#!/usr/bin/env python3
"""Situation-concept (atom) ontology — the act machinery generalized.

Differences from acts, deliberate: (1) situation concepts have GLOSSES
(2061/2065), so classification is meaning-based, not name-based; (2) there
is no natural small target set, so pass 1 DISCOVERS canonical concepts
bottom-up from the corpus (batched: each batch proposes canonical names for
its members, a merge step dedupes proposals into one canonical list), and
pass 2 assigns every concept to a canonical entry with `NEW:` allowed.
Bridges are generated beside the corpus (situation_bridges.lp), never
editing modules. Every call ledgered.

Output: situation_canon.json (canonical list with glosses),
        situation_bridges.json ({concept: {canonical, why}}),
        situation_bridges.lp  (canonical_concept(<canon>(X)) :- <bespoke>(X).)
Usage: .../.venv/bin/python classify_situation.py [discover|assign|bridges|all]
"""
import json, os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "..", ".."))
import live_pilot, translate

INV = json.load(open(os.path.join(HERE, "situation_concepts.json")))
CANON_P = os.path.join(HERE, "situation_canon.json"); BR_P = os.path.join(HERE, "situation_bridges.json")

DISCOVER = ("You are building a SHARED ontology of situation concepts for a policy document that has been decomposed into ~760 small logic modules, "
 "each of which coined its own predicate names for facts about the situation being judged (the request, the user, the content, the context). "
 "Given a batch of bespoke concepts (name, arity, gloss), propose the CANONICAL concepts they instantiate: a short snake_case name, an arity, "
 "argument sorts, and a one-sentence document-neutral gloss. Merge concepts that mean the same thing under one canonical name; keep genuinely "
 "distinct meanings distinct. Aim for canonical concepts a behavior author would recognize (e.g. request_is_ambiguous/1, user_indicates_illicit_intent/1, "
 "content_is_restricted/1, action_is_irreversible/1, party_is_third_party/1, setting_is_programmatic/0). Reply with JSON only: "
 "{\"canonical\": [{\"name\":..., \"arity\":..., \"args\":[...], \"gloss\":...}], \"members\": {\"<bespoke>\": \"<canonical name>\"}}.")
MERGE = ("You are given proposed canonical situation concepts (name /arity: gloss) with overlaps and near-duplicates. "
 "Return ONLY a merge mapping: for every proposed name, the name of the concept it should merge INTO (map a name to itself if it is the survivor). "
 "Merge by MEANING; keep genuinely distinct concepts distinct; prefer the clearest existing name as survivor. Do NOT restate glosses. "
 "JSON only, flat: {\"<proposed>\": \"<survivor>\", ...}.")
ASSIGN = ("Assign each bespoke situation concept (name, arity, gloss) to exactly ONE canonical concept from the list, judged by MEANING. "
 "If none fits, answer NEW:<snake_case> with a one-clause reason. JSON only: {\"<bespoke>\": {\"canonical\": ..., \"why\": ...}}.")


def _client(mt=4000):
    c = live_pilot.seat_client(max_tokens=mt); c.client.cfg["model"]["format_forcing"] = "json_object"; c.client.forcing = "json_object"
    translate.set_run_tag("situation_ontology"); return c


def _json(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    return json.loads(m.group(0)) if m else {}


def discover():
    complete = _client()
    names = sorted(INV); props, members = [], {}
    pp = os.path.join(HERE, "situation_proposals.json")
    if os.path.exists(pp):
        d = json.load(open(pp)); props, members = d["proposals"], d["members"]
        print(f"resuming from {len(props)} saved proposals (discovery already done)", flush=True); names = []
    for i in range(0, len(names), 40):
        b = names[i:i+40]
        user = "\n".join(f"- {n} /{INV[n]['arity']}: {INV[n]['gloss'][:160]}" for n in b) + "\n\nPropose canonical concepts and map each member. JSON only."
        try:
            d = _json(complete(DISCOVER, user).get("text", ""))
            props += d.get("canonical", []); members.update(d.get("members", {}))
        except Exception as ex: print("batch failed", i, repr(ex)[:100])
        if (i // 40) % 5 == 0: print(f"discover {min(i+40, len(names))}/{len(names)}; proposals {len(props)}; ${complete.client.spent_usd:.4f}", flush=True)
    json.dump({"proposals": props, "members": members}, open(os.path.join(HERE, "situation_proposals.json"), "w"), indent=1)
    # merge in chunks (proposals may number ~1000+): iterative pairwise-ish merge
    canon = props
    by_name = {c["name"]: c for c in canon if c.get("name")}
    for rnd in range(4):
        if len(by_name) <= 300: break
        names = sorted(by_name); mapping = {}
        # shuffle so near-duplicates from different discovery batches meet in one merge chunk
        import random as _r; _r.Random(rnd).shuffle(names)
        for i in range(0, len(names), 60):
            chunk = names[i:i+60]
            user = "\n".join(f"- {n} /{by_name[n].get('arity')}: {str(by_name[n].get('gloss',''))[:110]}" for n in chunk) + "\n\nMerge mapping. JSON only."
            try:
                d = _json(_client(6000)(MERGE, user).get("text", ""))
                for k, v in d.items():
                    if k in by_name and v in by_name: mapping[k] = v
            except Exception as ex: print("merge chunk failed", repr(ex)[:80], flush=True)
        # resolve chains, apply
        def root(x):
            seen = set()
            while mapping.get(x, x) != x and x not in seen: seen.add(x); x = mapping[x]
            return x
        survivors = {root(n) for n in by_name}
        for k, v in members.items(): members[k] = root(v) if v in by_name else v
        by_name = {n: by_name[n] for n in survivors}
        print(f"merge round {rnd}: {len(names)} -> {len(by_name)}; ${complete.client.spent_usd:.4f}", flush=True)
    canon = list(by_name.values())
    if False:  # final global merge disabled: a single call over the whole list truncates (measured)
        user = "\n".join(f"- {c.get('name')} /{c.get('arity')}: {str(c.get('gloss',''))[:100]}" for c in canon)
        try:
            d = _json(_client(8000)(MERGE, user + "\n\nMerge to the smallest faithful list. JSON only.").get("text", ""))
            if d.get("canonical"): 
                for k, v in members.items(): members[k] = d.get("merge", {}).get(v, v)
                canon = d["canonical"]
        except Exception as ex: print("final merge failed", repr(ex)[:100])
    # dedupe by name
    seen, out = set(), []
    for c in canon:
        n = str(c.get("name", "")).strip()
        if n and n not in seen: seen.add(n); out.append(c)
    json.dump({"canonical": out, "members_from_discovery": members}, open(CANON_P, "w"), indent=1)
    print(f"DISCOVER DONE: {len(out)} canonical concepts; ${complete.client.spent_usd:.4f}", flush=True)


def assign():
    canon = json.load(open(CANON_P))["canonical"]; names_c = {c["name"] for c in canon}
    prior = json.load(open(CANON_P)).get("members_from_discovery", {})
    out = json.load(open(BR_P)) if os.path.exists(BR_P) else {}
    complete = _client()
    clist = "\n".join(f"- {c['name']} /{c.get('arity')}: {str(c.get('gloss',''))[:110]}" for c in canon)
    todo = [n for n in sorted(INV) if n not in out]
    for i in range(0, len(todo), 30):
        b = todo[i:i+30]
        user = "CANONICAL CONCEPTS:\n" + clist + "\n\nBESPOKE CONCEPTS TO ASSIGN:\n" + "\n".join(f"- {n} /{INV[n]['arity']}: {INV[n]['gloss'][:140]}" for n in b) + "\n\nJSON only."
        try: d = _json(complete(ASSIGN, user).get("text", ""))
        except Exception as ex: print("assign batch failed", repr(ex)[:100]); d = {}
        for n in b:
            v = d.get(n) or {}; c = str(v.get("canonical", "")).strip()
            if c in names_c or c.startswith("NEW:"): out[n] = {"canonical": c, "why": str(v.get("why", ""))[:160]}
            elif prior.get(n) in names_c: out[n] = {"canonical": prior[n], "why": "from discovery"}
        json.dump(out, open(BR_P, "w"), indent=1)
        if (i // 30) % 5 == 0: print(f"assign {min(i+30, len(todo))}/{len(todo)}; ${complete.client.spent_usd:.4f}", flush=True)
    print(f"ASSIGN DONE: {len(out)}/{len(INV)} assigned; NEW {sum(1 for v in out.values() if v['canonical'].startswith('NEW:'))}", flush=True)


def bridges():
    br = json.load(open(BR_P)); canon = {c["name"]: c for c in json.load(open(CANON_P))["canonical"]}
    lines = ["% situation_bridges.lp — GENERATED (classify_situation.py). Bespoke situation concepts -> canonical concept ontology.",
             "% Never edits modules; loaded beside them. canonical_concept(<canon>(X..)) :- <bespoke>(X..). Arity per bespoke declaration."]
    for n, v in sorted(br.items()):
        c = v["canonical"]
        if c.startswith("NEW:"): continue
        ar = INV[n]["arity"] or 0
        if ar == 0: lines.append(f"canonical_concept({c}) :- {n}.")
        else:
            vs = ",".join(f"X{i}" for i in range(ar))
            lines.append(f"canonical_concept({c}({vs})) :- {n}({vs}).")
    open(os.path.join(HERE, "situation_bridges.lp"), "w").write("\n".join(lines) + "\n")
    print(f"BRIDGES DONE: {len(lines)-2} bridges to {len(canon)} canonical concepts", flush=True)


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    if step in ("discover", "all"): discover()
    if step in ("assign", "all"): assign()
    if step in ("bridges", "all"): bridges()
