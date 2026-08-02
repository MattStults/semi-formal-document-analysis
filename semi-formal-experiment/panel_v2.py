"""The SECOND panel — 9 behaviours x 2 specs, judged by SMALL models.

WHAT THIS IS, AND WHAT IT IS NOT
--------------------------------
`data/panel-coverage.json` is a second panel-of-judges run: **9 behaviours**
scored against **both** specs (OpenAI model spec + Anthropic constitution), 18
cells, 4,314 published citations. That is six times the 3-behaviour panel this
project has been reasoning from, and it is the fix for the binding constraint
on every claim here — n=3.

It is **NOT a new bar.** Its judges are `gpt-mini`, `haiku`, `qwen-small` —
small models. The question the project is actually asking is "is this tool as
good as just asking a FRONTIER model", and the frontier panel
(`behaviours.json`: sol / kimi / fable / opus / kimi-k2) remains the only thing
that answers it. This panel buys STATISTICAL POWER and GENERALISATION: does an
effect that shows up on 3 behaviours and one spec survive 9 behaviours and two?

That distinction is made structural, not narrated. Every behaviour loaded here
carries `behaviour["panel"]` naming the tier (`small`) and the roster, and
`benchmark.check_bar_provenance` refuses to let a report quote a bar off these
behaviours without naming the roster and disclaiming the tier.

THE UNIVERSE IS TRUNCATED — WORSE THAN THE FIRST PANEL
------------------------------------------------------
Observed summed-score distribution over all 4,314 rows:

    {2: 1309, 3: 1145, 4: 741, 5: 583, 6: 536}

There is **no score 0 and no score 1**. So the export kept `score >= 2` where
`build_site_data.keeps_citation` kept `score >= 1`. Two consequences, and only
the first is repairable:

  * SCORE 0 (every judge said "not related") is recoverable, exactly as in
    `panel_universe`: those passages are gold-negative by construction and
    unanimously predicted negative, so restoring them restores true-negative
    credit the judges earned rather than inventing any. This module reconstructs
    the FULL universe (589 model-spec / 374 constitution passages, via
    `panel_universe.spec_passages` — the same function the panel prompt used)
    and gives every absent passage verdict 0 from EVERY judge.

  * SCORE 1 IS IRRECOVERABLE. A passage where exactly one judge said
    "tangentially related" (1) and the other two said "not related" (0) summed
    to 1 and was dropped. It comes back from this file as ALL-ZERO, which is
    wrong: a real `tangentially related` judgement has been silently converted
    into `not related`, and nothing in the file distinguishes it from a passage
    no judge flagged at all. **This is a known, stated limitation of this
    panel and it cannot be repaired from this file** — only a re-export from
    `experiments/panel-judges/runlog-v2.jsonl` could repair it.

    `truncation_cost()` quantifies what that costs, by applying the SAME
    `score >= 2` rule to the frontier panel (where score-1 rows ARE present) on
    the three overlapping behaviours and measuring how much the judges' own
    numbers move. See `truncation_block()` for the rendered answer.

WHY EVERY QUOTE IS RE-DERIVED FROM THE UNIVERSE TEXT
----------------------------------------------------
The published rows in this file carry the RAW passage text (`**bold**` markers
intact, fenced example blocks inlined); `panel_universe`'s recovered rows carry
the publisher's cleaned citation quote. Mixing the two would make the
clause join behave systematically differently on published rows than on
recovered rows — a bias that runs exactly along the gold axis, since published
== "some judge saw relevance". So EVERY row's `quote` is re-derived here with
`panel_universe.citation_quote()` from the universe text, and the file's own
string is kept as `raw_quote` for provenance. 1,027 of 2,632 model-spec rows
and 306 of 1,682 constitution rows differ between the two.

VERDICT PARSING
---------------
`verdicts` is a mapping `{judge: 0|1|2}` (2 = relevant, 1 = tangentially
related, 0 = not related — the same three-point scale as the frontier panel's
core / related / not-relevant). Some exports of this file stringify it as a
Python dict repr (`"{'gpt-mini': 2, ...}"`). Both shapes are accepted;
`parse_verdicts` uses `ast.literal_eval` and **never `eval`** —
`test_panel_v2.py` scans this module's source to prove it.

Spec-swappability is the point: `spec_key` is a parameter everywhere, and the
`anthropic` side loads through the identical code path. Nothing here calls a
model.
"""
from __future__ import annotations

import ast
import json
import os
from collections import Counter

import panel_universe

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.abspath(os.path.join(HERE, ".."))

#: The 9-behaviour, 2-spec panel export.
PANEL_V2 = os.path.join(INDEX, "data", "panel-coverage.json")

#: Behaviour name/definition/category. The coverage export carries only
#: `behaviour_slug`, and `relevance.Behaviour` queries off `name` + `definition`
#: — loading without them yields an EMPTY query and a silently de-behaviourised
#: score, so a missing entry is a hard error (`MissingBehaviourMetadata`).
BEHAVIOUR_META = os.path.join(INDEX, "site", "spec-reader-test", "data",
                              "behaviours.json")

#: What this panel IS, carried on every behaviour it loads so no downstream
#: report can lose track of it.
PANEL_ID = "small-model-panel-v2"
TIER = "small"
JUDGE_ROSTER = ("gpt-mini", "haiku", "qwen-small")
BAR_LABEL = ("small-model panel (gpt-mini / haiku / qwen-small) — "
             "NOT the frontier bar")

#: The frontier panel, named here only so the contrast can be printed.
FRONTIER_PANEL_ID = "frontier-panel"
FRONTIER_TIER = "frontier"

#: The lowest summed score present in the export. Rows below it were dropped:
#: 0 is recoverable (all-zero is the truth), 1 IS NOT (see module docstring).
KEPT_MIN_SCORE = 2
IRRECOVERABLE_SCORES = (1,)

VALID_VERDICTS = (0, 1, 2)


class MalformedVerdicts(Exception):
    """A `verdicts` cell that cannot be trusted: not a mapping, a non-integer
    or out-of-range value, or a row missing a judge the rest of the cell has.
    Any of these would silently become a 0 — a fabricated 'not related'."""


class MissingBehaviourMetadata(Exception):
    """A coverage entry whose slug has no name/definition. Loading it would
    hand `relevance` an empty query, which scores like a broken tool rather
    than like a missing input."""


# ------------------------------------------------------------------ parsing

def parse_verdicts(raw) -> dict:
    """`{judge: 0|1|2}` from either a mapping or its Python-repr string.

    `ast.literal_eval`, never `eval`: this file is data written by another
    pipeline, and `eval` on it would execute whatever it contained.
    `test_verdict_parsing_never_uses_eval` proves the ban by reading this
    module's own source.
    """
    if isinstance(raw, str):
        try:
            raw = ast.literal_eval(raw)
        except (ValueError, SyntaxError) as e:
            raise MalformedVerdicts(f"unparseable verdicts string {raw!r}: {e}")
    if not isinstance(raw, dict) or not raw:
        raise MalformedVerdicts(f"verdicts is not a non-empty mapping: {raw!r}")
    out = {}
    for k, v in raw.items():
        if isinstance(v, bool) or not isinstance(v, int) or v not in VALID_VERDICTS:
            raise MalformedVerdicts(
                f"verdict {k}={v!r} is not one of {VALID_VERDICTS}")
        out[str(k)] = int(v)
    return out


def load_raw(path: str = PANEL_V2) -> dict:
    with open(path) as f:
        return json.load(f)


def behaviour_meta(path: str = BEHAVIOUR_META) -> dict:
    """`{slug: {name, definition, category}}`."""
    with open(path) as f:
        data = json.load(f)
    rows = data["behaviours"] if isinstance(data, dict) else data
    return {b["slug"]: {"name": b.get("name") or "",
                        "definition": b.get("definition") or "",
                        "category": b.get("category") or ""}
            for b in rows if b.get("slug")}


def cells(raw=None) -> list:
    """`[(slug, spec_key)]` — the 18 cells, sorted."""
    raw = raw if raw is not None else load_raw()
    return sorted((e["behaviour_slug"], e["lab_id"]) for e in raw["coverage"])


def score_histogram(raw=None) -> dict:
    """Summed-score distribution over every published citation. The evidence
    for the truncation claim, computed rather than asserted."""
    raw = raw if raw is not None else load_raw()
    return dict(Counter(sum(parse_verdicts(c["verdicts"]).values())
                        for e in raw["coverage"] for c in e["citations"]))


# ---------------------------------------------------------- reconstruction

def role_text(verdicts: dict) -> str:
    """The `role` free text the frontier panel publishes, synthesised.

    This file's `role` is literally `None` on all 4,314 rows, but
    `benchmark.panel_judge_names` / `verify_role_parse` read judges out of it as
    a cross-check on the structured `verdicts`. A row with no role would make
    that cross-check silently vacuous, so it is rebuilt in the publisher's
    format from the verdicts themselves — with the judge KEY as the display
    name, because this export carries no display names to read.
    """
    lines = "\n".join(f"{panel_universe.SYM[v]} {m} — {panel_universe.WORD[v]}"
                      for m, v in sorted(verdicts.items(), key=lambda x: -x[1]))
    return (f"Model determined relevance (score {sum(verdicts.values())}/"
            f"{2 * len(verdicts)}):\n{lines}")


def recover_cell(entry: dict) -> tuple:
    """`(rows, provenance)` for one `(behaviour, spec)` cell on the FULL universe.

    Published rows are joined by locator; every universe passage the export does
    not mention is synthesised with verdict 0 from every judge. Refuses (rather
    than dropping a judged verdict) on a duplicate locator or a locator that
    joins to nothing — the two failure modes `panel_universe` was written for.
    """
    slug, spec_key = entry["behaviour_slug"], entry["lab_id"]
    spec = panel_universe.spec_for_key(spec_key)
    universe = panel_universe.spec_passages(spec)
    text_of = {loc: text for loc, _sec, text in universe}
    cites = list(entry.get("citations") or [])

    dupes = sorted(l for l, n in Counter(c.get("locator") for c in cites).items()
                   if n > 1)
    if dupes:
        raise panel_universe.UnjoinablePassage(
            f"{slug}/{spec_key}: {len(dupes)} locator(s) appear on more than "
            f"one citation, so a judged verdict would be silently overwritten. "
            f"First: {dupes[:3]}")

    unjoined = sorted({c.get("locator") for c in cites
                       if c.get("locator") not in text_of})
    if unjoined:
        raise panel_universe.UnjoinablePassage(
            f"{slug}/{spec_key}: {len(unjoined)} of {len(cites)} citations join "
            f"to no passage in the {spec} universe ({len(universe)}). First: "
            f"{unjoined[:3]}. Refusing to reconstruct — an unjoined citation is "
            f"a judged verdict about to be dropped.")

    verdicts_of = {c["locator"]: parse_verdicts(c["verdicts"]) for c in cites}
    judge_keys = sorted({j for v in verdicts_of.values() for j in v})
    ragged = sorted(l for l, v in verdicts_of.items()
                    if sorted(v) != judge_keys)
    if ragged:
        raise MalformedVerdicts(
            f"{slug}/{spec_key}: {len(ragged)} citation(s) do not carry every "
            f"judge in {judge_keys} — the missing judge would read as a "
            f"fabricated 0. First: {ragged[:3]}")
    raw_quote_of = {c["locator"]: c.get("quote") for c in cites}
    adjacent_of = {c["locator"]: c.get("adjacent") for c in cites}

    zero = {j: 0 for j in judge_keys}
    rows = []
    for loc, _sec, text in universe:
        v = verdicts_of.get(loc)
        recovered = v is None
        v = dict(zero) if recovered else dict(v)
        # THE QUOTE IS RE-DERIVED FOR EVERY ROW, published or recovered — see
        # the module docstring. Using the export's raw text on published rows
        # and the cleaned quote on recovered ones would bias the clause join
        # along the gold axis.
        quote, is_example = panel_universe.citation_quote(text)
        rows.append({
            "id": loc, "locator": loc, "published_id": None,
            "quote": quote, "raw_quote": raw_quote_of.get(loc),
            "exampleBlock": is_example,
            "adjacent": adjacent_of.get(loc, True),
            "verdicts": v, "score": sum(v.values()),
            "role": role_text(v), "recovered": recovered,
        })

    hist = dict(Counter(sum(v.values()) for v in verdicts_of.values()))
    prov = {
        "slug": slug, "spec_key": spec_key, "spec": spec,
        "panel": PANEL_ID, "tier": TIER, "judges": judge_keys,
        "universe": len(universe), "published": len(cites),
        "recovered_zero": len(universe) - len(cites),
        "join_rate": 1.0 if not cites else
                     (len(cites) - len(unjoined)) / len(cites),
        "unjoined": unjoined,
        "score_histogram": hist,
        "min_published_score": min(hist) if hist else None,
        "score_1_present": 1 in hist,
        "score_1_irrecoverable": 1 not in hist,
    }
    return rows, prov


def load_panel(path: str = PANEL_V2, spec_keys=("openai", "anthropic"),
               meta_path: str = BEHAVIOUR_META, with_provenance: bool = False):
    """`{slug: behaviour}` on the TRUE universe, in the shape `benchmark` reads.

    `spec_keys` is a parameter and both sides go through the identical code
    path: the constitution (`anthropic`, 374 passages) is not a special case,
    which is the spec-swappability claim this project has made and never
    exercised end to end.
    """
    raw = load_raw(path)
    meta = behaviour_meta(meta_path)
    out, prov = {}, {}
    for entry in sorted(raw["coverage"],
                        key=lambda e: (e["behaviour_slug"], e["lab_id"])):
        slug, key = entry["behaviour_slug"], entry["lab_id"]
        if key not in spec_keys:
            continue
        if slug not in meta:
            raise MissingBehaviourMetadata(
                f"{slug}: no name/definition in {meta_path}. Loading it would "
                f"give relevance an empty query — refusing.")
        rows, p = recover_cell(entry)
        b = out.setdefault(slug, {
            "slug": slug, **meta[slug], "coverage": {},
            "panel": {"id": PANEL_ID, "tier": TIER,
                      "models": list(JUDGE_ROSTER), "label": BAR_LABEL,
                      "source": os.path.basename(path)},
        })
        b["coverage"][key] = {"passages": rows, "universe": "true",
                              "panel": PANEL_ID}
        prov[(slug, key)] = p
    return (out, prov) if with_provenance else out


def published_panel(panel: dict) -> dict:
    """The same behaviours confined to the export's OWN citation list.

    Exists only so the truncated number can be printed beside the true one with
    the delta stated — the pairing `benchmark.check_universe_pairing` enforces.
    Never a headline on its own: it is the broken denominator.
    """
    out = {}
    for slug, b in panel.items():
        nb = dict(b)
        nb["coverage"] = {}
        for key, cov in (b.get("coverage") or {}).items():
            nc = dict(cov)
            nc["passages"] = [p for p in cov.get("passages") or []
                              if not p.get("recovered")]
            nc["universe"] = "published"
            nb["coverage"][key] = nc
        out[slug] = nb
    return out


# --------------------------------------------- what the truncation costs us

TRUNCATION_SLUGS = ("helpfulness", "harm-avoidance-to-third-parties",
                    "avoiding-over-and-under-caution")


def apply_v2_truncation(behaviour: dict, spec_key: str) -> dict:
    """A copy of `behaviour` with this panel's export rule applied to `spec_key`:
    every passage whose summed score is below `KEPT_MIN_SCORE` is zeroed out.

    This is the simulation that makes the score-1 loss measurable. It is applied
    to the FRONTIER panel (whose score-1 rows survive) so the cost can be read
    off real judgements rather than assumed.
    """
    out = dict(behaviour)
    out["coverage"] = {k: dict(v) for k, v in (behaviour.get("coverage") or {}).items()}
    cov = dict(out["coverage"].get(spec_key) or {})
    rows = []
    for p in cov.get("passages") or []:
        if p.get("score", 0) >= KEPT_MIN_SCORE:
            rows.append(p)
            continue
        q = dict(p)
        q["verdicts"] = {j: 0 for j in (p.get("verdicts") or {})}
        q["score"] = 0
        q["role"] = role_text(q["verdicts"]) if q["verdicts"] else p.get("role")
        q["truncated"] = True
        rows.append(q)
    cov["passages"] = rows
    out["coverage"][spec_key] = cov
    return out


def truncation_cost(behaviours=None, spec_keys=("openai", "anthropic"),
                    threshold: int = 1) -> dict:
    """`{(slug, spec_key): row}` — what `score >= 2` costs, on the frontier panel.

    Measured, per cell:
      `n_score_1`        passages whose summed score was exactly 1;
      `class_changed`    passages that change relevance class for at least one
                         judge (i.e. the 1 becomes a 0);
      `gold_changed`     passages entering/leaving a pair-gold at `threshold`;
      `judge_mcc_*`      each judge's mean LOO MCC before and after, and the
                         delta — the number to quote.
    """
    import benchmark
    if behaviours is None:
        behaviours = benchmark.load_true_panel()
    out = {}
    for slug in sorted(behaviours):
        b = behaviours[slug]
        for key in spec_keys:
            if key not in (b.get("coverage") or {}):
                continue
            ps = benchmark.passages(b, key)
            trunc = apply_v2_truncation(b, key)
            n1 = sum(1 for p in ps if p.get("score", 0) == 1)
            changed = sum(1 for p in ps
                          if 0 < p.get("score", 0) < KEPT_MIN_SCORE)
            universe = {p["id"] for p in ps}
            before = benchmark.pair_targets(b, threshold, key)
            after = benchmark.pair_targets(trunc, threshold, key)
            gold_changed = sum(len(before[j]["gold"] ^ after[j]["gold"])
                               for j in before)
            def judge_mcc(bb, tt):
                vals = [benchmark.mcc(t["pred"], t["gold"], universe)
                        for t in tt.values()]
                return sum(vals) / len(vals) if vals else 0.0
            m0, m1 = judge_mcc(b, before), judge_mcc(trunc, after)
            out[(slug, key)] = {
                "n_passages": len(ps), "n_score_1": n1,
                "class_changed": changed,
                "class_changed_frac": changed / len(ps) if ps else 0.0,
                "gold_changed": gold_changed,
                "judge_mcc_before": m0, "judge_mcc_after": m1,
                "judge_mcc_delta": m1 - m0,
            }
    return out


def truncation_block(cost: dict) -> str:
    """Markdown. The stated, quantified limitation — never omitted."""
    lines = [
        "## What the score-1 truncation costs (LIMITATION, quantified)", "",
        f"`{os.path.basename(PANEL_V2)}` keeps only `score >= {KEPT_MIN_SCORE}`. "
        "Score-0 passages are recoverable — all-zero IS the truth for them — "
        "but **score-1 passages are IRRECOVERABLE**: a real "
        "`tangentially related` judgement by one judge comes back as "
        "`not related` and is indistinguishable from a passage no judge "
        "flagged. Nothing in the file can undo that; only a re-export from the "
        "run log could.",
        "",
        "Measured by applying the SAME rule to the FRONTIER panel, where "
        "score-1 rows survive:",
        "",
        "| behaviour | spec | passages | score==1 | class changed | gold "
        "changed | judge MCC before | after | delta |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for (slug, key), r in sorted(cost.items()):
        lines.append(
            f"| {slug} | {key} | {r['n_passages']} | {r['n_score_1']} "
            f"| {r['class_changed']} ({r['class_changed_frac']:.1%}) "
            f"| {r['gold_changed']} | {r['judge_mcc_before']:+.3f} "
            f"| {r['judge_mcc_after']:+.3f} | {r['judge_mcc_delta']:+.3f} |")
    if cost:
        n = len(cost)
        lines.append(
            f"| **mean** | | | "
            f"{sum(r['n_score_1'] for r in cost.values()) / n:.1f} | | | "
            f"{sum(r['judge_mcc_before'] for r in cost.values()) / n:+.3f} | "
            f"{sum(r['judge_mcc_after'] for r in cost.values()) / n:+.3f} | "
            f"**{sum(r['judge_mcc_delta'] for r in cost.values()) / n:+.3f}** |")
    lines.append("")
    return "\n".join(lines)


# ------------------------------------------------------------- provenance

def provenance_block(prov: dict) -> str:
    """Markdown. Every number a reader needs to check the reconstruction, plus
    the panel's tier — which is printed here rather than in a footnote because
    a reader who takes these judges for the bar has misread the whole table."""
    lines = [
        "## Panel v2 — 9 behaviours x 2 specs (SMALL-MODEL judges)", "",
        f"**{BAR_LABEL}.** Judges: `{'`, `'.join(JUDGE_ROSTER)}`. This panel is "
        "here for STATISTICAL POWER and GENERALISATION (does an effect hold "
        "across 9 behaviours and both specs?). The bar this project must clear "
        "is 'as good as asking a FRONTIER model', which only the frontier panel "
        "(sol / kimi / fable / opus / kimi-k2) can measure. Judge agreement "
        "computed here is the SMALL-MODEL panel's agreement and must never be "
        "quoted as the bar.",
        "",
        "The export dropped every passage scoring below "
        f"{KEPT_MIN_SCORE}; the full universe is reconstructed with "
        "`panel_universe.spec_passages` (the same passage list the panel prompt "
        "contained) and every absent passage carries verdict 0 from every "
        "judge. Score-1 rows come back as all-zero and CANNOT be recovered — "
        "see the truncation table.",
        "",
        "| behaviour | spec | universe | published | recovered as 0 | join rate "
        "| min score present | score-1 recoverable |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for (slug, key), p in sorted(prov.items()):
        lines.append(
            f"| {slug} | {p['spec']} ({key}) | {p['universe']} | "
            f"{p['published']} | {p['recovered_zero']} "
            f"({p['recovered_zero'] / p['universe']:.0%}) | "
            f"{p['join_rate']:.3f} | {p['min_published_score']} | "
            f"{'yes' if p['score_1_present'] else '**NO**'} |")
    bad = {k: p["unjoined"] for k, p in prov.items() if p["unjoined"]}
    lines.append("")
    lines.append(f"unjoined citations: **{sum(len(v) for v in bad.values())}**"
                 + (f" — {bad}" if bad else " (every citation joins)"))
    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    panel, prov = load_panel(with_provenance=True)
    print(provenance_block(prov))
    print(truncation_block(truncation_cost()))


if __name__ == "__main__":
    main()
