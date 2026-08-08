#!/usr/bin/env python3
"""Experiment 3 — can a model RESOLVE the names we actually coined?

    THE ONE QUESTION: given the whole document and the predicates our modules
    really borrowed, can a model say WHERE each is defined — and correctly
    refuse the ones the document never defines?

⭐ WHY THIS AND NOT MORE PREDICTION. Two probes asked a model to PREDICT what
sections would need. `[RAN]` concept-level scored 1/32 against what our
translator actually coined; predicate-level scored **0/32** with 268 candidates
on the table. The pre-registration's falsifier fired: prediction is the wrong
direction, and the map's role is a RESOLUTION TARGET (Invariant 1 arm C — "a
lookup the model never sees") rather than prompt context (arm A).

So this probe reverses the direction. It supplies the names and asks only where
they live — which is the one question arm C has to answer, and the arm the
design calls "the most attractive and the least explored".

⭐ IT HAS GROUND TRUTH, which neither earlier probe had. `[RAN]` of the 14
symbols currently blocking a stage-4 read-back, SIX appear nowhere in the
document: policy_class, pasted_text, interactable_entity, interaction_entity,
delegated_authority_to_webpage, conflicts_with_later_same_authority. A correct
answer classifies those as `coinage`. That is an accuracy number, not a
plausibility judgement.

⛔ TWO ARMS, AND THE SPLIT IS THE POINT. `--gloss` supplies the borrowing
clause's own gloss alongside each name; `--no-gloss` supplies the bare name.
If resolution needs the gloss, the model is matching our wording rather than
reading the document — and a lookup that only works when we already wrote the
definition is not a lookup. Run both; the DIFFERENCE is the measurement.

    python3 resolve_probe.py --arm no-gloss          # DRY RUN
    python3 resolve_probe.py --arm gloss --live
"""

import argparse
import glob
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import translate as T  # noqa: E402

OUT_ROOT = os.path.join(HERE, "resolve_runs")
MAX_TOKENS = 32768

#: `[RAN]` These appear NOWHERE in the document — verified by searching every
#: clause for all the words of each name. A correct run calls them `coinage`.
#: They are the scoring key and are NEVER shown to the model.
KNOWN_COINAGES = {
    "policy_class", "pasted_text", "interactable_entity", "interaction_entity",
    "delegated_authority_to_webpage", "conflicts_with_later_same_authority",
}

SYSTEM = """You are resolving symbols against a specification document.

The document is given in full, divided by markers of the form

    ===== SECTION: <section_id> =====

Someone has translated individual clauses of this document into small logic
rules. Those rules test conditions written as predicates, and each translation
listed the predicates it BORROWED — conditions it uses but does not itself
define.

Your job is to say, for each borrowed predicate, WHERE in the document its
meaning is established. Nothing else. You are not judging the translation, not
rewriting it, and not inventing predicates.

Three answers are available, and the third is as important as the first:

  DOCUMENT   a section establishes this. Name it and quote the phrase.
  WORLD      no section establishes it because it comes from outside the
             document — a legal category, a factual matter, a technical term
             the document assumes its reader already knows.
  COINAGE    the translator invented a name the document does not use at all.
             No section defines it and none ever could.

⛔ DO NOT INVENT A DEFINING SECTION. A section that MENTIONS a term does not
establish it. If nothing in the document fixes what a name means, the honest
answers are WORLD or COINAGE, and getting those right matters more than a long
DOCUMENT list.

⚠️ These names were coined by a translator working one clause at a time. Some
are the document's own vocabulary; some are that translator's shorthand. Do not
assume a name is the document's just because it sounds like it could be."""

TURN_1 = """Below is the document, then the borrowed predicates.

For EVERY predicate listed, give exactly one verdict.

Return JSON only:

{"resolved": [{"predicate": "name/arity",
               "verdict": "document" | "world" | "coinage",
               "section_id": "<section_id>, or null unless verdict is document",
               "evidence": "a phrase appearing VERBATIM in that section, or null",
               "why": "one sentence"}]}

Every predicate in the list must appear exactly once in your answer."""

TURN_2 = """Now look again at everything you called `world` or `coinage`.

For each, say what the translation should have done instead:

{"remedies": [{"predicate": "name/arity",
               "verdict": "world" | "coinage",
               "remedy": "cite-a-section" | "mark-as-world" | "rename-to-document-term"
                         | "the-document-has-a-gap",
               "document_term": "the document's own wording for this idea, or null",
               "why": "one sentence"}]}

⭐ `rename-to-document-term` is the interesting one: the translator coined a name
for something the document already names differently. If so, give the document's
term — that is a concrete, checkable claim."""


def borrowed_predicates(cfg):
    """Every predicate our stored modules borrowed, across ALL versions.

    ⚠️ NOT the first version per clause. Deduping to the first run threw away 9
    of 40 borrowed symbols and 6 of the 14 that currently block a read-back —
    a property of how the set was built, not of the data.

    `defines` is included: `m0053`'s two coinages arrive there, not in
    `requires`/`inputs`, and an extractor that reads only the borrow lists
    cannot see them.
    """
    corpus = {c["id"]: c for c in T.load_corpus(cfg)}
    out = {}
    for p in sorted(glob.glob(os.path.join(HERE, "runs", "*", "m*.json"))):
        try:
            o = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(o, dict) or o.get("clause_id") not in corpus:
            continue
        cid = o["clause_id"]
        sec = corpus[cid]["section_id"]
        gl = {c["name"]: c.get("gloss") for c in (o.get("concepts") or [])
              if isinstance(c, dict) and c.get("name")}
        for sig in (o.get("requires") or []) + (o.get("inputs") or []):
            name = sig.split("/")[0]
            out.setdefault(sig, {"predicate": sig, "section_id": sec,
                                 "clause_id": cid, "gloss": gl.get(name)})
        for d in (o.get("defines") or []):
            if isinstance(d, dict) and d.get("term"):
                t = re.sub(r"\(.*", "", str(d["term"])).strip()
                if t:
                    out.setdefault(f"{t}/1", {
                        "predicate": f"{t}/1", "section_id": sec,
                        "clause_id": cid, "gloss": None})
    return sorted(out.values(), key=lambda r: r["predicate"])


def needs_block(rows, section_id, with_gloss, translated):
    """The predicates one section borrows, rendered AT that section.

    ⭐ ATTACHED TO THE SECTION, not listed separately. A flat alphabetical list
    divorces a predicate from the text that needs it, so the model must
    cross-reference 43 names against 78 sections from memory. Here the question
    sits next to the passage that raises it.

    ⛔ THREE STATES, NEVER TWO. `[RAN]` only 9 of 78 sections have a translated
    module, so a bare "none" would conflate "this section's rules borrow
    nothing" with "nobody has translated this section yet". Those are opposite
    facts and a resolver told the first when the second is true will reason from
    a false premise about the document's own completeness.
    """
    if section_id not in translated:
        return ("    [BORROWED PREDICATES: not applicable — no clause in this "
                "section has been translated yet, so nothing is claimed about "
                "what its rules would borrow.]")
    mine = [r for r in rows if r["section_id"] == section_id]
    if not mine:
        return ("    [BORROWED PREDICATES: none. This section HAS been "
                "translated, and its rules borrow no predicate from elsewhere.]")
    out = ["    [BORROWED PREDICATES — the rules written from this section test "
           "these, and do not define them. Where is each one established?]"]
    for r in sorted(mine, key=lambda r: r["predicate"]):
        out.append(f"      - {r['predicate']}")
        if with_gloss and r.get("gloss"):
            out.append(f"          the translator's note: {r['gloss']}")
    return "\n".join(out)


def build_document(cfg, rows=None, with_gloss=False):
    """The corpus, section-marked — with each section's borrowed predicates
    rendered immediately under its own marker when `rows` is supplied."""
    clauses = T.load_corpus(cfg)
    translated = {r["section_id"] for r in (rows or [])}
    if rows is not None:
        # a section counts as translated if any stored module came from it,
        # not merely if it borrowed something
        translated = {r["section_id"] for r in rows}
    out, seen = [], None
    for c in clauses:
        if c["section_id"] != seen:
            seen = c["section_id"]
            out.append(f"\n===== SECTION: {seen} =====")
            if rows is not None:
                out.append(needs_block(rows, seen, with_gloss, translated))
            out.append("")
        out.append(c["quote"])
    return "\n".join(out)


def _parse(raw):
    t = re.sub(r"^```(?:json)?\s*\n|```\s*$", "", raw.strip(), flags=re.M)
    try:
        return json.loads(t), None
    except json.JSONDecodeError as exc:
        return None, f"{type(exc).__name__}: {exc}"


def score(obj, rows):
    """⭐ Accuracy against KNOWN_COINAGES, plus the refusals we cannot key."""
    got = {r["predicate"]: r for r in (obj or {}).get("resolved", [])
           if isinstance(r, dict) and r.get("predicate")}
    asked = {r["predicate"] for r in rows}
    missing = asked - set(got)
    extra = set(got) - asked
    keyed = [(p, got[p].get("verdict")) for p in got
             if p.split("/")[0] in KNOWN_COINAGES]
    right = [p for p, v in keyed if v == "coinage"]
    return {"asked": len(asked), "answered": len(got),
            "missing": sorted(missing), "invented": sorted(extra),
            "known_coinages_in_set": len(keyed),
            "called_coinage_correctly": len(right),
            "verdicts": {v: sum(1 for r in got.values() if r.get("verdict") == v)
                         for v in ("document", "world", "coinage")}}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--arm", choices=("gloss", "no-gloss"), default="no-gloss")
    p.add_argument("--live", action="store_true")
    p.add_argument("--config", default=os.path.join(HERE, "config.json"))
    p.add_argument("--max-cost", type=float, default=0.25)
    a = p.parse_args(argv)

    cfg = T.load_config(a.config)
    cfg = {**cfg, "model": {**cfg["model"], "format_forcing": "json_object",
                            "max_tokens": MAX_TOKENS}}
    prov = T.resolve_provider(cfg, type("A", (), {
        "provider": None, "model": None, "max_tokens": None})())
    rows = borrowed_predicates(cfg)
    doc = build_document(cfg, rows, a.arm == "gloss")
    user1 = doc + "\n\n" + TURN_1

    cpt = float(cfg["cost"]["chars_per_token"])
    pin, pout = prov.price_per_mtok
    t1 = (len(SYSTEM) + len(user1)) / cpt
    t2 = t1 + MAX_TOKENS + len(TURN_2) / cpt
    worst = ((t1 + t2) / 1e6) * pin + ((2 * MAX_TOKENS) / 1e6) * pout
    keyed = [r for r in rows if r["predicate"].split("/")[0] in KNOWN_COINAGES]

    print(f"arm                : {a.arm}")
    print(f"predicates supplied: {len(rows)}   with a gloss: "
          f"{sum(1 for r in rows if r.get('gloss')) if a.arm=='gloss' else 0}")
    print(f"⭐ scoring key      : {len(keyed)} known coinages in the set "
          f"({', '.join(sorted(r['predicate'] for r in keyed))})")
    print(f"document           : {len(doc):,} chars")
    print(f"cost (worst case)  : ${worst:.4f}   ceiling ${a.max_cost:.2f}")
    if worst > a.max_cost:
        print("\n⛔ over the ceiling. Nothing sent.")
        return 2
    if not a.live:
        print("\nDRY RUN — nothing sent. Add --live to spend.\n")
        print("--- system block ---\n" + SYSTEM)
        for sec in ("scope_of_autonomy", "definitions"):
            m = re.search(r"===== SECTION: " + sec + r" =====\n(.*?)\n\n", doc, re.S)
            print(f"\n--- section marker as the model sees it: {sec} ---")
            print(m.group(0).strip() if m else "(not found)")
        print("\n--- turn 1 ---" + TURN_1)
        print("\n--- turn 2 ---" + TURN_2)
        return 0

    outdir = os.path.join(OUT_ROOT, time.strftime("%Y%m%d-%H%M%S") + "-" + a.arm)
    os.makedirs(outdir, exist_ok=True)
    client = T.make_client(prov, cfg)
    messages, spent, first = [{"role": "user", "content": user1}], 0.0, None
    for n, (label, follow) in enumerate([("resolve", None),
                                         ("remedy", TURN_2)], start=1):
        if follow:
            messages.append({"role": "user", "content": follow})
        try:
            env = client.complete_messages(SYSTEM, messages)
        except T.Phase1Error as exc:
            print(f"⛔ turn {n}: {type(exc).__name__}: {exc}")
            break
        raw = env["text"]
        with open(os.path.join(outdir, f"turn{n}.{label}.raw.txt"), "w",
                  encoding="utf-8") as fh:
            fh.write(raw)                      # raw FIRST, always
        messages.append({"role": "assistant", "content": raw})
        obj, err = _parse(raw)
        spent += (env.get("in", 0)/1e6)*pin + (env.get("out", 0)/1e6)*pout
        cap = env.get("out", 0) >= MAX_TOKENS - 64
        print(f"  turn {n} ({label}): {env.get('out',0):,} out-tok"
              + ("  ⛔ AT CAP" if cap else "") + (f"  ⚠️ {err}" if err else "  ✓"))
        if obj is not None:
            with open(os.path.join(outdir, f"turn{n}.{label}.json"), "w",
                      encoding="utf-8") as fh:
                json.dump(obj, fh, indent=1)
            if n == 1:
                first = obj
    sc = score(first, rows)
    print(f"\n  ⭐ known coinages called `coinage`: "
          f"{sc['called_coinage_correctly']}/{sc['known_coinages_in_set']}")
    print(f"  verdict split: {sc['verdicts']}")
    print(f"  unanswered: {len(sc['missing'])}   invented: {len(sc['invented'])}")
    with open(os.path.join(outdir, "run.json"), "w", encoding="utf-8") as fh:
        json.dump({"arm": a.arm, "model": prov.model, "supplied": len(rows),
                   "score": sc, "spent_usd": round(spent, 6),
                   "visible_to_spend_py": False}, fh, indent=1)
    print(f"\nwritten to {outdir}")
    print(T.spend_invisibility_warning(prov, spent, 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
