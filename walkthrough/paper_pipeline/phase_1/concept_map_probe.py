#!/usr/bin/env python3
"""One-off: can a model read the WHOLE document and map its concept graph?

    THE ONE QUESTION: given every section at once, can a model say what each
    section NEEDS from elsewhere, and what each section PRODUCES that others
    need — well enough to be statically checked against the document?

⭐ WHY THIS EXISTS, and it is a specific measured failure, not a hunch.
`OPEN_QUESTIONS.md` Q-6: 14 symbols block 7 of 19 stored modules from reaching
any stage-4 seat, and NOT ONE is glossed by any module we translated. Every one
is a predicate a module BORROWS. The contract demands a gloss for names a clause
introduces and nothing for names it borrows, so the concept dictionary the
design assumes accumulates has no source.

⛔ AND GROWTH WILL NOT FIX IT. `[RAN]` of those 14, six appear NOWHERE in the
document — `policy_class`, `pasted_text`, `interactable_entity`,
`interaction_entity`, `delegated_authority_to_webpage`,
`conflicts_with_later_same_authority`. Those are coinages, not borrowings.
`DEFERRED.md` D-3's "it resolves itself as the corpus grows" holds for the
borrowings and fails for the coinages.

⚠️ THIS IS A PROBE, NOT A PHASE. It answers whether the artifact is obtainable
at all. It is deliberately NOT wired into the pipeline, produces nothing any
other module reads, and its output is evidence for a design decision Matt has
not yet made — Invariant 1's A/B/C arms are still open, and open question 2's
"run both arms on the same clauses" is unrunnable today precisely because
neither arm has a dictionary.

WHAT IT IS EVIDENCE ABOUT, stated so the result cannot be over-read:
  * it CAN show a model produces a plausible, checkable input/output map;
  * it CANNOT show that supplying that map to a translator helps. Invariant 1
    records contrary published evidence for arm A — supplying a model its own
    accumulated atom list INCREASED hallucination — and this probe does not
    test delivery at all.

    python3 concept_map_probe.py            # DRY RUN: prompt, sizes, cost
    python3 concept_map_probe.py --live     # spends
"""

import argparse
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import translate as T  # noqa: E402

OUT_ROOT = os.path.join(HERE, "concept_map_runs")

#: Generous. The reply enumerates every section, and `README.md` records that
#: this provider returns `finish_reason: null`, so the truncation guard CANNOT
#: fire — a cut-off reply arrives as a JSON parse error attributed to the wrong
#: cause. Over-provisioning the cap is the only defence available.
MAX_TOKENS = 32768

SYSTEM = """You are analysing a specification document to map its concept graph.

The document is given in full, divided into sections by markers of the form

    ===== SECTION: <section_id> =====

Your job is to describe, per section, the concepts that cross section boundaries.
You are NOT translating anything into logic and NOT judging the document.

A CONCEPT here is a thing the document reasons about and can name: a category of
material, an act, a role, a status, a property. Not a sentence, not a rule.

Two kinds, and the distinction is the whole point:

  INPUT   a concept the section USES but does not itself establish. Reading the
          section alone, you would have to be told what it means — either by
          another section, or from outside the document entirely.
  OUTPUT  a concept the section ESTABLISHES — defines, names, or fixes the
          extension of — which other sections then rely on.

⭐ A concept can be an input to one section and an output of another. That pairing
is what the map is for.

⚠️ Be conservative about OUTPUT. A section mentioning a term does not establish
it. Ask: if every other section vanished, would this section still tell you what
the term means? If not, it is an INPUT, not an OUTPUT.

⛔ Mark a concept `world` when NO section establishes it and it comes from
outside the document — legal categories, factual knowledge, technical terms the
document assumes. Do not invent a producing section for these."""

TURN_1 = """Read the whole document above.

For EVERY section, list its INPUT concepts — the concepts that section needs from
the rest of the document, or from the world, in order to make sense on its own.

Return JSON only:

{"sections": [{"section_id": "...",
               "inputs": [{"concept": "short_snake_case_name",
                           "gloss": "what it means, in the document's own terms",
                           "why_needed": "what the section does with it",
                           "source": "document" | "world"}]}]}

A section with no inputs gets an empty list — say so rather than omitting it."""

TURN_2 = """Now the other half.

For every INPUT you listed as `source: "document"`, identify which section is its
OUTPUT — the section that actually establishes that concept.

Return JSON only:

{"resolved": [{"concept": "...", "produced_by": "<section_id>",
               "consumed_by": ["<section_id>", ...],
               "evidence": "the phrase in the producing section that establishes it"}],
 "unresolved": [{"concept": "...", "consumed_by": ["..."],
                 "why": "why no section establishes it"}]}

⭐ `unresolved` is the important half, so do not pad `resolved` to look complete.
An input that NO section establishes is either a `world` concept you mis-filed,
or a real gap in the document — both are findings. `evidence` must be a phrase
that appears verbatim in the producing section, so this can be checked."""


def build_document(cfg):
    """The whole corpus, section-marked, in document order."""
    rows, out, seen = T.load_corpus(cfg), [], None
    for c in rows:
        if c["section_id"] != seen:
            seen = c["section_id"]
            out.append(f"\n===== SECTION: {seen} =====\n")
        out.append(c["quote"])
    return "\n".join(out), rows


def _parse(raw):
    """Best-effort. A failure is REPORTED, never silently an empty result."""
    t = re.sub(r"^```(?:json)?\s*\n|```\s*$", "", raw.strip(), flags=re.M)
    try:
        return json.loads(t), None
    except json.JSONDecodeError as exc:
        return None, f"{type(exc).__name__}: {exc}"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true")
    p.add_argument("--config", default=os.path.join(HERE, "config.json"))
    p.add_argument("--max-cost", type=float, default=0.25)
    a = p.parse_args(argv)

    cfg = T.load_config(a.config)
    cfg = {**cfg, "model": {**cfg["model"], "format_forcing": "json_object",
                            "max_tokens": MAX_TOKENS}}
    prov = T.resolve_provider(cfg, type("A", (), {
        "provider": None, "model": None, "max_tokens": None})())
    doc, rows = build_document(cfg)
    user1 = doc + "\n\n" + TURN_1

    cpt = float(cfg["cost"]["chars_per_token"])
    pin, pout = prov.price_per_mtok
    t1_in = (len(SYSTEM) + len(user1)) / cpt
    t2_in = t1_in + MAX_TOKENS + len(TURN_2) / cpt      # transcript accumulates
    worst = ((t1_in + t2_in) / 1e6) * pin + ((2 * MAX_TOKENS) / 1e6) * pout

    print(f"clauses / sections : {len(rows)} / "
          f"{len({r['section_id'] for r in rows})}")
    print(f"document           : {len(doc):,} chars (~{int(len(doc)/cpt):,} tok)")
    print(f"model              : {prov.model}")
    print(f"turns              : 2, ONE accumulating transcript")
    print(f"cost (worst case)  : ${worst:.4f}   ceiling ${a.max_cost:.2f}")

    if worst > a.max_cost:
        print(f"\n⛔ over the ceiling. Nothing sent.")
        return 2
    if not a.live:
        print("\nDRY RUN — nothing sent. Add --live to spend.")
        print(f"\n--- system block ---\n{SYSTEM[:600]}\n…")
        print(f"\n--- turn 1 tail ---\n…{user1[-700:]}")
        return 0

    outdir = os.path.join(OUT_ROOT, time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(outdir, exist_ok=True)
    client = T.make_client(prov, cfg)
    messages, results, spent = [{"role": "user", "content": user1}], [], 0.0

    for n, (label, follow) in enumerate(
            [("inputs", None), ("outputs", TURN_2)], start=1):
        if follow:
            messages.append({"role": "user", "content": follow})
        try:
            env = client.complete_messages(SYSTEM, messages)
        except T.Phase1Error as exc:
            print(f"\n⛔ turn {n} ({label}): {type(exc).__name__}: {exc}")
            break
        raw = env["text"]
        # ⭐ RAW FIRST, ALWAYS. `eval.py` made 36 paid calls and kept only
        # finding strings; that defect is recorded in this repo.
        with open(os.path.join(outdir, f"turn{n}.{label}.raw.txt"), "w",
                  encoding="utf-8") as fh:
            fh.write(raw)
        messages.append({"role": "assistant", "content": raw})
        obj, err = _parse(raw)
        spent += (env.get("in", 0) / 1e6) * pin + (env.get("out", 0) / 1e6) * pout
        near_cap = env.get("out", 0) >= MAX_TOKENS - 64
        print(f"  turn {n} ({label}): {env.get('out',0):,} out-tokens"
              + ("  ⛔ AT THE CAP — suspect truncation" if near_cap else "")
              + (f"  ⚠️ unparseable: {err}" if err else "  ✓ parsed"))
        results.append({"turn": n, "label": label, "out_tokens": env.get("out"),
                        "parsed": obj is not None, "parse_error": err,
                        "near_cap": near_cap})
        if obj is not None:
            with open(os.path.join(outdir, f"turn{n}.{label}.json"), "w",
                      encoding="utf-8") as fh:
                json.dump(obj, fh, indent=1)

    with open(os.path.join(outdir, "run.json"), "w", encoding="utf-8") as fh:
        json.dump({"model": prov.model, "max_tokens": MAX_TOKENS,
                   "document_chars": len(doc), "sections":
                       len({r["section_id"] for r in rows}),
                   "turns": results, "spent_usd": round(spent, 6),
                   "visible_to_spend_py": False}, fh, indent=1)
    print(f"\nwritten to {outdir}")
    print(T.spend_invisibility_warning(prov, spent, len(results)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
