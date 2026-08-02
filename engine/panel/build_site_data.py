#!/usr/bin/env python3
"""Build site/llm-panel-review/data/behaviours.json from panel verdicts.

Implements the MVP display rules from panel-config.json `display`:
  - only the listed behaviours appear in the sidebar;
  - each passage gets score = sum over panel models of (core=2, related=1, unrelated=0);
  - every passage with score >= 1 is emitted as a citation (the page filters at
    render time via ?threshold= / ?solid= / ?related= URL params, defaults 6/6/1);
  - the citation `role` (shown when the reader clicks "?") lists each model's decision.

Behaviour names/definitions come from data/reader-test-coverage.json exactly as supplied
(no rewriting). Curated row-level verdict/depth/notes are carried through untouched.

  python3 build_site_data.py --runlog=<runlog> --rubric=v3w --panel=frontier
  (the shipped data: --runlog=runlog-v3.jsonl from the experiment branch, rubric v3w)
"""
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CONFIG = json.loads((HERE / "panel-config.json").read_text())
DISPLAY = CONFIG["display"]
LAB = {"constitution": "anthropic", "model-spec": "openai"}
VERDICT_WORD = {2: "core", 1: "related", 0: "unrelated"}
MODEL_LABEL = {"sol": "GPT-5.6 Sol", "fable": "Claude Fable 5", "qwen-max": "Qwen3.7-Max", "kimi": "Kimi-K3", "kimi-k2": "Kimi-K2.6", "qwen-big": "Qwen3-235B", "opus": "Claude Opus 4.8",
               "gpt-mini": "GPT-5 mini", "haiku": "Claude Haiku 4.5", "qwen-small": "Qwen3-32B"}
# panel behaviour keys -> site slugs
SLUGS = {"helpfulness": "helpfulness", "third-party-harm": "harm-avoidance-to-third-parties",
         "over-under-caution": "avoiding-over-and-under-caution",
         "harmlessness-to-user": "harmlessness-to-the-user",
         "proportionate-risk": "proportionate-risk-mitigation", "tradeoffs": "how-to-approach-tradeoffs",
         "objectivity": "objectivity-on-contested-questions", "user-autonomy": "user-autonomy",
         "general-welfare": "animal-welfare-impacts"}
SLUGS_EXTRA = {"general-welfare": ["general-welfare-impacts-strict"]}   # one run feeds both general-guidelines rows


def keeps_citation(score, n_votes, panel_size):
    """Pure: stray-vote guard -- scales to panel size so a 1-judge panel is legal."""
    return score >= 1 and n_votes >= min(2, panel_size)


def clean_quote(text):
    """Pure: strip bold markers -- mid-word bold in spec source breaks anchor matching."""
    return text.replace("**", "")


def citation_quote(text):
    """Pure: (quote, is_example_block). Fenced example blocks render as code the
    matcher cannot see, so -- like the curated data -- the quote is the caption
    line before the fence and the exampleBlock flag extends the highlight."""
    if "~~~" in text:
        caption = clean_quote(text.split("~~~")[0].strip())
        if caption:                       # a fence-leading passage has no caption --
            return caption, True          # an empty quote would anchor to the wrong block
    return clean_quote(text), False


def main():
    runlog = HERE / "runlog-v3.jsonl"   # same default as whole_doc.py and run_rollout.py
    rubric = CONFIG["rubric"]
    for a in sys.argv[1:]:
        if a.startswith("--runlog="):
            runlog = Path(a.split("=", 1)[1])
        elif a.startswith("--rubric="):
            rubric = a.split("=", 1)[1]
        elif a.startswith("--panel="):
            DISPLAY["panel"] = a.split("=", 1)[1]
    panel = set(CONFIG["panels"][DISPLAY["panel"]])
    votes = collections.defaultdict(dict)
    spec_of = {}
    for line in runlog.read_text().splitlines():
        d = json.loads(line)
        if d.get("rubric", "v1") != rubric or not d.get("parsed", True) or d["model"] not in panel:
            continue
        votes[(d["behaviour"], d["locator"])][d["model"]] = d.get("verdict", 0)
        spec_of[(d["behaviour"], d["locator"])] = d["spec"]

    import importlib.util
    sp = importlib.util.spec_from_file_location("h", HERE / "harness.py")
    h = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(h)
    text = {}
    for s in CONFIG["specs"]:
        for loc, sec, t in h.passages(s):
            text[loc] = t

    src = json.loads((ROOT / "data" / "reader-test-coverage.json").read_text())
    keep = DISPLAY["behaviours"]
    behaviours = [b for b in src["behaviours"] if b["slug"] in keep]
    by_slug_lab = {(e["behaviour_id"], e["lab_id"]): e for e in src["coverage"]}
    id_of = {b["slug"]: b["id"] for b in behaviours}

    out_behaviours = []
    for b in behaviours:
        cov = {}
        for spec_name, lab in LAB.items():
            src_entry = by_slug_lab.get((b["id"], lab), {})
            cits = []
            for (beh, loc), mv in votes.items():
                slug_matches = (SLUGS.get(beh) == b["slug"]
                                or b["slug"] in SLUGS_EXTRA.get(beh, []))
                if not slug_matches or spec_of[(beh, loc)] != spec_name:
                    continue
                if "fable" in mv and "opus" in mv:
                    mv = {m: v for m, v in mv.items() if m != "opus"}   # opus is fable's SUBSTITUTE, never an extra seat
                if "kimi" in mv and "kimi-k2" in mv:
                    mv = {m: v for m, v in mv.items() if m != "kimi-k2"}   # k2.6 is kimi's stand-in; k3 wins when present
                score = sum(mv.values())
                if not keeps_citation(score, len(mv), len(panel)):   # emit all scored; page filters by ?threshold=
                    continue
                SYM = {2: "\u2713", 1: "~", 0: "\u2717"}
                WORD = {2: "core", 1: "related", 0: "not relevant"}
                decisions = "\n".join(f"{SYM[v]} {MODEL_LABEL.get(m, m)} \u2014 {WORD[v]}"
                                      for m, v in sorted(mv.items(), key=lambda x: -x[1]))
                quote, is_example = citation_quote(text.get(loc, ""))
                cits.append({
                    "id": f"{lab}-{b['slug']}-panel-{len(cits)+1}",
                    "locator": loc, "quote": quote, "exampleBlock": is_example,
                    "role": f"Model determined relevance (score {score}/{2*len(mv)}):\n{decisions}",
                    "adjacent": score < DISPLAY["solid_threshold"],
                    "verdicts": dict(sorted(mv.items())), "score": score,
                })
            cits.sort(key=lambda c: (-c["score"], c["locator"]))
            cov[lab] = {"verdict": src_entry.get("verdict"), "depth": src_entry.get("depth_0_4"),
                        "note": src_entry.get("depth_note", ""),
                        "verifiedDate": src_entry.get("verified_date", ""),
                        "passages": cits}
        out_behaviours.append({"id": len(out_behaviours) + 1,   # renumber 01..N for display
                               "slug": b["slug"], "name": b["name"],
                               "definition": b["definition"], "category": b["category"],
                               "coverage": cov})
    from datetime import date
    seats = sorted({m for b_ in out_behaviours for cov in b_["coverage"].values()
                    for p in cov["passages"] for m in p.get("verdicts", {})})
    out = {"generatedFrom": [f"engine/panel/build_site_data.py ({rubric})"],
           "provenance": {
               "method": "llm-panel whole-document judging", "rubric": rubric,
               "panel_config": DISPLAY["panel"],
               "panel": ["sol (gpt-5.6-sol)", "fable (claude-fable-5)", "kimi (moonshotai/Kimi-K3)"]
                        if DISPLAY["panel"] == "frontier" else sorted(panel),
               "substitution": "opus (claude-opus-4-8) replaces fable on harm-to-third-parties x model-spec (fable output content-filtered, 3 attempts); kimi-k2 (Kimi-K2.6) replaces kimi on over-under-caution x model-spec (K3 exhausted a 65k output budget on reasoning without emitting verdicts, finish_reason length)",
               "judges_seen_in_data": seats,
               "runDate": str(date.today()),
               "scoring": "per passage: sum over judges of core=2/related=1/neither=0; display thresholds are client-side URL params"},
           "behaviours": out_behaviours}
    dest = ROOT / "site" / "llm-panel-review" / "data" / "behaviours.json"
    dest.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    n = sum(len(c["passages"]) for b in out_behaviours for c in b["coverage"].values())
    print(f"{dest.relative_to(ROOT)}: {len(out_behaviours)} behaviours, {n} citations "
          f"(threshold {DISPLAY['threshold']}, solid {DISPLAY['solid_threshold']})")


if __name__ == "__main__":
    main()
