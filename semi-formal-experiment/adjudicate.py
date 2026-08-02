"""Adjudication worksheet for the conflict delta (contract §4, Agent C).

Renders **deltas only** --- `tool_only` and `baseline_only`. Both-found items
are low information (§1) and are skipped.

Every item shows both provisions' **full clause text** with locators and ids.
Never a truncated span: the instrument experiment's single largest rater
correction came from reading the whole sentence a span had been cut from (§1).
Where the inventory carries a `marked_span`, it is shown *in addition to* the
full clause, as the anchor --- never in place of it.

Two modes:
    python adjudicate.py --tool ... --baseline ... --metrics delta_metrics.json \\
                         --out adjudication_worksheet.md
    python adjudicate.py --score adjudication_worksheet.md --out-json scores.json
"""
from __future__ import annotations

import argparse
import json
import os
import re

import delta

try:                    # Agent A owns the locator format; never re-synthesize it
    from inventory import asp_id as _asp_id, make_locator
except ImportError:     # standalone fallback, kept format-identical to A's
    SPEC_VERSION = "model_spec@2025-12-18"

    def _asp_id(focus_id):
        return "fa_" + focus_id

    def make_locator(section_path, line):
        return f"{SPEC_VERSION} > {' > '.join(section_path)} > L{line}"

HERE = os.path.dirname(os.path.abspath(__file__))
FOCUS_AREAS = os.path.join(HERE, "modelspec_focus_areas.json")

VERDICTS = ["REAL", "ARTIFACT", "RESOLVED ELSEWHERE", "OUT OF ENCODED SCOPE"]
SLOT_LABEL = {"ARTIFACT": "responsible atom or rule",
              "RESOLVED ELSEWHERE": "clause id",
              "OUT OF ENCODED SCOPE": "missing atom"}
FOUND_Q = "Would I have found this by reading the section carefully?"


# --------------------------------------------------------------------------
# inventory (Agent A owns the row shape; this reader is deliberately tolerant)
# --------------------------------------------------------------------------

def _norm_row(r):
    """Agent A's row: {id, source_id, locator, quote, marked_span, kind,
    modality, has_defeater}. Accept the raw focus-area shape too, so the
    worksheet is renderable before A lands."""
    rid = r.get("id") or r.get("focus_id") or ""
    rid = _prefix_id(rid)
    quote = r.get("quote") or r.get("text") or ""
    locator = r.get("locator")
    if not locator and r.get("section_path") and r.get("line"):
        # raw focus-area row: build the locator with A's function so worksheet
        # locators are byte-identical to the rest of the pipeline. Pass the
        # RAW focus id — make_locator applies the fa_ prefix itself, and the
        # id is required or locators collide (259 focus areas share only 158
        # bare line locators).
        locator = make_locator(r["section_path"], r["line"],
                               r.get("focus_id") or r.get("source_id") or "")
    return {"id": rid,
            "source_id": r.get("source_id") or r.get("focus_id") or "",
            "locator": locator or "",
            "quote": quote,
            "marked_span": r.get("marked_span") or "",
            "kind": r.get("kind", ""),
            "modality": r.get("modality", ""),
            "has_defeater": r.get("has_defeater", "")}


def _prefix_id(raw):
    raw = str(raw).strip()
    return raw if raw.startswith("fa_") or not raw else _asp_id(raw)


def load_inventory(path=FOCUS_AREAS, section="The chain of command"):
    """JSON list, JSONL, or {"rows"/"inventory": [...]}."""
    with open(path) as f:
        txt = f.read().strip()
    if txt.startswith("["):
        rows = json.loads(txt)
    elif txt.startswith("{"):
        try:
            obj = json.loads(txt)
            rows = obj.get("rows") or obj.get("inventory") or obj.get("focus_areas")
            if rows is None:
                raise ValueError(f"{path}: no rows/inventory/focus_areas key")
        except json.JSONDecodeError:
            rows = [json.loads(ln) for ln in txt.splitlines() if ln.strip()]
    else:
        rows = [json.loads(ln) for ln in txt.splitlines() if ln.strip()]
    if section and rows and "top_level_section" in rows[0]:
        rows = [r for r in rows if r.get("top_level_section") == section]
    return {r["id"]: r for r in (_norm_row(x) for x in rows) if r["id"]}


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------

STOP_RULES = """\
## Stop rules (contract §6 --- decided before results, read before you start)

- **Coverage < 70%** (fewer than 30 of 42 provisions encoded) --- stop; the
  loop would be measuring extraction gaps, not conflict quality.
- **`baseline_self_agreement` ~ 0** --- the comparator can't hold still.
  Report it and stop.
- **After 10 adjudications: ARTIFACT >= 6 and zero items marked REAL with
  "would not have found it"** --- noise without insight. Stop.
- **`attribution_rate` < 0.5** --- deltas don't localize; fixes are guesswork.
  Stop.
- **Fixes regress on most attempts** --- changes aren't local. Stop.

## How to adjudicate (§1)

The document is ground truth; the frontier model is a lead generator, never an
oracle. Ask **"which span licenses this, and does it assert more?"** --- never
"is this a real distinction?". The full clause is printed for exactly this
reason. A fix lands only when the source text says the tool was wrong.
"""


def _provision_block(fid, inv):
    row = inv.get(fid)
    if row is None:
        return (f"**`{fid}`** --- *not found in inventory*\n\n"
                "> (no clause text available --- resolve before adjudicating)\n")
    loc = row["locator"] or "(no locator)"
    quote = row["quote"].strip() or "(empty quote in inventory)"
    body = [f"**`{fid}`** --- `{loc}`"
            + (f" --- {row['kind']}" if row["kind"] else ""), ""]
    body += ["> " + ln for ln in quote.split("\n")]
    span = (row.get("marked_span") or "").strip()
    if span and span != quote.strip():
        body += ["", f"*anchor span:* “{span}”"]
    body.append("")
    return "\n".join(body)


def encoding_status(extraction, rejected=None):
    """provision id -> {state, detail}, over the tool's encoding.

    §7: "`C_baseline \\ C_tool` conflates tool bug with out-of-scope. The
    worksheet forces that call." It cannot force anything the adjudicator has
    no basis to decide, and on real data most baseline-only pairs cite
    provisions the tool never encoded at all. Four states:

      `encoded`   --- a rule survived validation and is in the program, so the
                      tool *could* have raised this pair; a miss is a candidate
                      defect.
      `rejected`  --- the extraction produced a rule but it failed validation
                      and never reached the solver. A coverage loss with a
                      named cause, distinct from never having been extracted.
      `unencoded` --- recorded in `extraction.unencoded` with a reason.
      `absent`    --- a conditional provision the extraction never mentions.

    A fifth state, `out_of_encodable_set`, is resolved at render time from the
    inventory's `kind`: only the 42 *conditional* provisions of the 62 are
    encodable at all (§2), so a baseline pair citing a `holistic` one is out of
    scope **by design**. Reporting that as `absent` reads as an extraction
    failure and charges design scope to the tool, which is precisely the
    conflation §7 warns about.
    """
    if isinstance(extraction, str):
        with open(extraction) as f:
            extraction = json.load(f)
    rejected_by_id = {r.get("id"): r for r in (rejected or [])
                      if r.get("kind") == "rule"}
    st = {}
    for u in extraction.get("unencoded") or []:
        if isinstance(u, dict) and u.get("focus_id"):
            st[_prefix_id(u["focus_id"])] = {
                "state": "unencoded",
                "detail": u.get("reason", "") or "(no reason recorded)"}
    for rid, r in rejected_by_id.items():
        st[rid] = {"state": "rejected",
                   "detail": r.get("reason", "") or "(no reason recorded)"}
    for r in extraction.get("rules") or []:
        if not isinstance(r, dict) or not r.get("id"):
            continue
        if r["id"] in rejected_by_id:
            continue
        st[r["id"]] = {"state": "encoded",
                       "detail": f"{r.get('modality', '?')} "
                                 f"{r.get('act', '?')}"}

    class _D(dict):
        def __missing__(self, k):
            return {"state": "absent",
                    "detail": "not mentioned by the extraction (neither a rule "
                              "nor an `unencoded` entry)"}
    return _D(st)


_STATE_LABEL = {"encoded": "encoded", "rejected": "REJECTED by validation",
                "unencoded": "unencoded", "absent": "absent from the extraction",
                "out_of_encodable_set": "out of the encodable set"}


def _refine(fid, st, inv):
    """`absent` + a non-conditional inventory kind = out of scope by design,
    not an extraction gap. Only the 42 conditional provisions are encodable."""
    if st["state"] != "absent":
        return st
    kind = (inv.get(fid) or {}).get("kind", "")
    if kind and kind != "conditional":
        return {"state": "out_of_encodable_set",
                "detail": f"not among the 42 conditional provisions "
                          f"(kind: {kind}) — out of scope by design (§2), "
                          f"not an extraction gap"}
    return st


def _encoding_block(pair, status, inv=None):
    a, b = pair
    inv = inv or {}
    sa, sb = _refine(a, status[a], inv), _refine(b, status[b], inv)
    L = ["**Encoding status.**",
         f"- `{a}`: {_STATE_LABEL[sa['state']]} --- {sa['detail']}",
         f"- `{b}`: {_STATE_LABEL[sb['state']]} --- {sb['detail']}"]
    states = {sa["state"], sb["state"]}
    if states == {"encoded"}:
        L.append("- **Both provisions are encoded**: the tool could have "
                 "raised this pair, so a miss here is a candidate defect "
                 "(name the missing atom, `incompat`, or condition) rather "
                 "than a coverage cost.")
    elif "encoded" not in states:
        L.append("- **Neither provision is encoded**: this pair lies entirely "
                 "outside the encoding, so the tool could not have raised it "
                 "whatever its logic. Default verdict OUT OF ENCODED SCOPE; "
                 "this is a coverage cost, not a conflict-detection failure.")
    else:
        L.append("- **One provision is outside the encoding**: the pair is "
                 "unreachable for the tool as encoded. Default verdict OUT OF "
                 "ENCODED SCOPE, naming the missing side.")
    L.append("")
    return "\n".join(L)


def _verdict_slots():
    L = ["Verdict --- check exactly one:", ""]
    for v in VERDICTS:
        lab = SLOT_LABEL.get(v)
        L.append(f"- [ ] {v}" + (f" --- {lab}: ____" if lab else ""))
    L += ["", f"{FOUND_Q}  Y / N  ->  answer: __", ""]
    return "\n".join(L)


def render_item(n, bucket, pair, inv, records, status=None):
    a, b = pair
    L = [f"<!-- ITEM {bucket} {a} {b} -->",
         f"### {n}. {bucket} --- `{a}` + `{b}`", "",
         _provision_block(a, inv), _provision_block(b, inv)]
    if status is not None:
        L += [_encoding_block(pair, status, inv)]
    prose = ""
    note = ""
    ctx = []
    runs = []
    for r in records:
        prose = prose or (r.get("witness_prose") or "")
        note = note or (r.get("note") or "")
        ctx = ctx or ((r.get("witness") or {}).get("ctx") or [])
        if r.get("run_id"):
            runs.append(r["run_id"])
    L.append(f"**Witness.** {prose.strip() or '(none given)'}")
    if bucket == "tool_only":
        L.append("")
        L.append("**Witness atoms (`ctx`).** "
                 + (", ".join(f"`{c}`" for c in ctx) if ctx else "(empty)"))
    if note.strip():
        L += ["", f"**Note.** {note.strip()}"]
    if runs:
        L += ["", f"*asserted by:* {', '.join(sorted(set(runs)))}"]
    L += ["", _verdict_slots(), "---", ""]
    return "\n".join(L)


def render_worksheet(metrics, inv, tool_docs, baseline_docs,
                     extraction=None, rejected=None):
    bk = metrics["buckets"]
    idx = delta.index_by_pair(list(tool_docs) + list(baseline_docs))
    status = (encoding_status(extraction, rejected)
              if extraction is not None else None)
    L = ["# Adjudication worksheet --- conflict delta", "",
         "Deltas only. Both-found items are skipped (§1: low information).", "",
         delta.metrics_table(metrics), ""]
    if metrics.get("degenerate"):
        L += [f"> **Degenerate comparison.** {metrics['degenerate_reason']}. "
              "Read the items below as *what the baseline asserted*, not as a "
              "disagreement between two populated conflict sets.", ""]
    ch = metrics.get("conflict_channels")
    if ch and not ch["any_channel_open"]:
        L += ["> **The tool's empty conflict set is not a solver finding.** "
              f"The extraction declared {ch['n_incompat']} `incompat` pairs "
              "and no act that is both obliged and forbidden, and those are "
              "the only two ways the emitted program derives a conflict. Zero "
              "follows from the extraction before the solver runs.", ""]
    L += [STOP_RULES, "",
          f"**{len(bk['tool_only'])} tool-only + {len(bk['baseline_only'])} "
          f"baseline-only = {len(bk['tool_only']) + len(bk['baseline_only'])} "
          f"items to adjudicate** ({len(bk['both'])} both-found skipped).", "",
          "---", ""]
    n = 0
    for bucket in ("tool_only", "baseline_only"):
        for pair in bk[bucket]:
            n += 1
            L.append(render_item(n, bucket, list(pair), inv,
                                 idx.get(delta.pair_key(pair), []),
                                 status=status))
    if n == 0:
        L.append("*No deltas: the two conflict sets are identical.*")
    return "\n".join(L)


# --------------------------------------------------------------------------
# scoring a filled worksheet
# --------------------------------------------------------------------------

ITEM_RE = re.compile(r"^<!-- ITEM (\S+) (\S+) (\S+) -->\s*$", re.MULTILINE)
CHECK_RE = re.compile(r"^-\s*\[([ xX])\]\s*(.+?)\s*$", re.MULTILINE)
ANSWER_RE = re.compile(re.escape(FOUND_Q) + r".*?answer:\s*([YyNn])?")


def _parse_item(bucket, a, b, body):
    verdicts, slots = [], {}
    for mark, rest in CHECK_RE.findall(body):
        label = rest.split("---")[0].strip()
        if label not in VERDICTS:
            continue
        if mark.strip().lower() == "x":
            verdicts.append(label)
            if "---" in rest:
                val = rest.split("---", 1)[1]
                val = val.split(":", 1)[1] if ":" in val else val
                val = re.sub(r"_{2,}", "", val).strip()   # drop the ____ blank
                slots[label] = val
    m = ANSWER_RE.search(body)
    found = (m.group(1) or "").upper() if m and m.group(1) else None
    return {"bucket": bucket, "pair": [a, b], "verdicts": verdicts,
            "verdict": verdicts[0] if len(verdicts) == 1 else None,
            "slot": slots.get(verdicts[0]) if len(verdicts) == 1 else None,
            "would_have_found": found}


def parse_worksheet(text):
    items, marks = [], list(ITEM_RE.finditer(text))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        items.append(_parse_item(m.group(1), m.group(2), m.group(3),
                                 text[m.end():end]))
    return items


def _single_name(s):
    """An attribution counts only if it names *one* atom or rule."""
    if not s:
        return False
    s = s.strip().strip(".")
    if not s or set(s) <= {"_", " "}:
        return False
    return not re.search(r",|\band\b|\bor\b|/|;|\+", s)


def score(items, metrics=None):
    dist, unfilled, ambiguous = {}, [], []
    for it in items:
        if it["verdict"] is None:
            (ambiguous if it["verdicts"] else unfilled).append(it["pair"])
            continue
        dist[it["verdict"]] = dist.get(it["verdict"], 0) + 1
    adjudicated = [i for i in items if i["verdict"]]

    tool_artifacts = [i for i in adjudicated
                      if i["bucket"] == "tool_only" and i["verdict"] == "ARTIFACT"]
    attributed = [i for i in tool_artifacts if _single_name(i["slot"])]
    attribution_rate = (len(attributed) / len(tool_artifacts)
                        if tool_artifacts else None)

    real_unfound = [i for i in adjudicated
                    if i["verdict"] == "REAL" and i["would_have_found"] == "N"]

    # Headline: the coverage cost expressed in *conflict* terms. A baseline-only
    # item ruled OUT OF ENCODED SCOPE is a real tension the tool cannot see
    # because it encodes only the 42 conditional provisions. This number does
    # not exist unless all 62 are sent to the baseline, and it must be kept
    # apart from ARTIFACTs (encoding defects) and from REALs (genuine misses).
    def _bo(v):
        return [i for i in adjudicated
                if i["bucket"] == "baseline_only" and i["verdict"] == v]

    out_of_scope = _bo("OUT OF ENCODED SCOPE")
    genuine_misses = _bo("REAL")
    baseline_only_n = sum(1 for i in adjudicated if i["bucket"] == "baseline_only")

    out = {
        "n_items": len(items),
        "n_adjudicated": len(adjudicated),
        "unfilled": unfilled,
        "ambiguous_multi_check": ambiguous,
        "verdict_distribution": dist,
        "verdict_distribution_by_bucket": {
            bkt: {v: sum(1 for i in adjudicated
                         if i["bucket"] == bkt and i["verdict"] == v)
                  for v in VERDICTS}
            for bkt in ("tool_only", "baseline_only")},
        "tool_only_artifacts": len(tool_artifacts),
        "attributed_to_single_name": len(attributed),
        "attribution_rate": attribution_rate,
        "real_and_would_not_have_found": len(real_unfound),
        # coverage cost in conflict terms --- reported separately from
        # ARTIFACT and from genuine misses
        "coverage_cost_conflicts": len(out_of_scope),
        "coverage_cost_pairs": [i["pair"] for i in out_of_scope],
        "baseline_only_genuine_misses": len(genuine_misses),
        "baseline_only_artifacts": len(_bo("ARTIFACT")),
        "baseline_only_resolved_elsewhere": len(_bo("RESOLVED ELSEWHERE")),
        "baseline_only_adjudicated": baseline_only_n,
    }
    out["stop_rules"] = check_stop_rules(out, metrics)
    out["any_stop_rule_fired"] = any(
        r["fired"] for r in out["stop_rules"].values())
    return out


def check_stop_rules(s, metrics=None):
    m = metrics or {}
    cov = (m.get("coverage") or {}).get("coverage")
    bsa = m.get("baseline_self_agreement")
    ar = s["attribution_rate"]
    rules = {
        "coverage_below_70pct": {
            "fired": cov is not None and cov < 0.70,
            "value": cov, "threshold": 0.70,
            "evaluated": cov is not None},
        "baseline_self_agreement_near_zero": {
            "fired": bsa is not None and bsa <= 0.05,
            "value": bsa, "threshold": 0.05,
            "evaluated": bsa is not None},
        "noise_without_insight": {
            "fired": (s["n_adjudicated"] >= 10
                      and s["verdict_distribution"].get("ARTIFACT", 0) >= 6
                      and s["real_and_would_not_have_found"] == 0),
            "value": {"n_adjudicated": s["n_adjudicated"],
                      "artifact": s["verdict_distribution"].get("ARTIFACT", 0),
                      "real_unfound": s["real_and_would_not_have_found"]},
            "threshold": "n>=10 and ARTIFACT>=6 and REAL-unfound==0",
            "evaluated": s["n_adjudicated"] >= 10},
        "attribution_rate_below_half": {
            "fired": ar is not None and ar < 0.5,
            "value": ar, "threshold": 0.5,
            "evaluated": ar is not None},
        "fixes_regress": {
            "fired": False, "value": None,
            "threshold": "most fix attempts regress",
            "evaluated": False,
            "note": "requires a recompute after fixes; not mechanical here"},
    }
    return rules


def score_markdown(s):
    L = ["# Adjudication scores", "",
         f"- items: {s['n_items']} (adjudicated {s['n_adjudicated']}, "
         f"unfilled {len(s['unfilled'])}, ambiguous {len(s['ambiguous_multi_check'])})",
         "", "| verdict | n |", "|---|---|"]
    L += [f"| {v} | {s['verdict_distribution'].get(v, 0)} |" for v in VERDICTS]
    L += ["",
          f"- `attribution_rate` = {delta._fmt(s['attribution_rate'])} "
          f"({s['attributed_to_single_name']}/{s['tool_only_artifacts']} "
          "tool-only ARTIFACTs traced to a single named atom or rule)",
          f"- REAL and \"would not have found it\": "
          f"{s['real_and_would_not_have_found']}",
          "", "## Coverage cost, in conflict terms", "",
          f"**{s['coverage_cost_conflicts']} of {s['baseline_only_adjudicated']} "
          "adjudicated baseline-only items are OUT OF ENCODED SCOPE** --- real "
          "tensions the tool cannot see because it encodes only the 42 "
          "conditional provisions of 62.", "",
          f"- genuine tool misses (baseline-only ruled REAL): "
          f"{s['baseline_only_genuine_misses']}",
          f"- baseline-only ruled ARTIFACT: {s['baseline_only_artifacts']}",
          f"- baseline-only ruled RESOLVED ELSEWHERE: "
          f"{s['baseline_only_resolved_elsewhere']}"]
    L += [f"- out-of-scope pair: `{p[0]}` + `{p[1]}`"
          for p in s["coverage_cost_pairs"]]
    L += ["", "## Stop rules", "", "| rule | evaluated | value | fired |",
          "|---|---|---|---|"]
    for name, r in s["stop_rules"].items():
        L.append(f"| {name} | {'yes' if r['evaluated'] else 'no'} | "
                 f"{delta._fmt(r['value']) if not isinstance(r['value'], dict) else r['value']} "
                 f"| {'**YES**' if r['fired'] else 'no'} |")
    L += ["", ("**At least one stop rule fired.**" if s["any_stop_rule_fired"]
               else "No stop rule fired."), ""]
    return "\n".join(L)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--score", default=None,
                    help="read a filled worksheet back and score it")
    ap.add_argument("--tool", nargs="*", default=[])
    ap.add_argument("--baseline", nargs="*", default=[])
    ap.add_argument("--metrics", default=None,
                    help="delta_metrics.json (recomputed if omitted)")
    ap.add_argument("--extraction", default=None)
    ap.add_argument("--rejections", default=None,
                    help="filter_extraction.py's report; lets each item say "
                         "whether its provisions are encoded, rejected or "
                         "unencoded (§7's out-of-scope vs tool-bug call)")
    ap.add_argument("--inventory", default=FOCUS_AREAS,
                    help="Agent A's inventory rows; falls back to the raw "
                         "focus areas")
    ap.add_argument("--out", default=None)
    ap.add_argument("--out-json", default=None)
    a = ap.parse_args(argv)

    if a.score:
        with open(a.score) as f:
            text = f.read()
        metrics = None
        if a.metrics:
            with open(a.metrics) as f:
                metrics = json.load(f)
        s = score(parse_worksheet(text), metrics)
        if a.out_json:
            with open(a.out_json, "w") as f:
                json.dump(s, f, indent=1)
            print(f"scores -> {a.out_json}")
        md = score_markdown(s)
        if a.out:
            with open(a.out, "w") as f:
                f.write(md)
            print(f"summary -> {a.out}")
        else:
            print(md)
        return 0

    tool = [delta.load_conflicts(p) for p in a.tool]
    base = [delta.load_conflicts(p) for p in a.baseline]
    rejected = None
    if a.rejections:
        with open(a.rejections) as f:
            rejected = json.load(f).get("rejected", [])
    if a.metrics:
        with open(a.metrics) as f:
            metrics = json.load(f)
    else:
        metrics = delta.compute(
            tool, base, extraction=a.extraction,
            rejected_rule_ids=[r["id"] for r in (rejected or [])
                               if r.get("kind") == "rule"])
    inv = load_inventory(a.inventory)
    ws = render_worksheet(metrics, inv, tool, base,
                          extraction=a.extraction, rejected=rejected)
    if a.out:
        with open(a.out, "w") as f:
            f.write(ws)
        print(f"worksheet -> {a.out} "
              f"({metrics['bucket_sizes']['tool_only']} tool-only, "
              f"{metrics['bucket_sizes']['baseline_only']} baseline-only)")
    else:
        print(ws)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
