"""Frontier-model baseline for the conflict-delta spike (contract §4, Agent C).

Gives a frontier model the *same* question the solver answers --- "which
provisions in this section can conflict, and in what situation?" --- over the
62 focus areas of "The chain of command", and emits `conflicts.json` in the
frozen §3 shape so `delta.py` can compare it against the tool's output.

k=3 independent runs, each with its own run_id, so the baseline's own
self-stability is measurable (§5 `baseline_self_agreement`).

DRY-RUN IS THE DEFAULT. `providers.make_client(..., live=False)` records the
prompt under prompt_log/ and returns None; no network call happens. Live calls
require the explicit `--live` flag *and* a resolvable API key.

Usage:
    python baseline_conflicts.py --provider claude            # dry run
    python baseline_conflicts.py --provider claude --live     # real calls
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys

import providers

try:                       # Agent A's uniform prefixer, once inventory.py lands
    from inventory import asp_id as _asp_id
except ImportError:        # standalone fallback: same rule, "fa_" on every id
    def _asp_id(focus_id):
        return "fa_" + focus_id

HERE = os.path.dirname(os.path.abspath(__file__))
FOCUS_AREAS = os.path.join(HERE, "modelspec_focus_areas.json")
PROVIDERS = os.path.join(HERE, "providers.json")
SECTION = "The chain of command"

ID_PREFIX = "fa_"


def prefix_id(raw: str) -> str:
    """Agent A prefixes the 13 digit-initial focus ids so they are legal ASP
    constants; the frozen conflicts.json shape uses the prefixed form."""
    raw = str(raw).strip()
    return raw if raw.startswith(ID_PREFIX) else _asp_id(raw)


def load_focus_areas(path=FOCUS_AREAS, section=SECTION):
    with open(path) as f:
        rows = json.load(f)
    rows = [r for r in rows if r.get("top_level_section") == section]
    rows.sort(key=lambda r: r.get("line", 0))
    return rows


# --------------------------------------------------------------------------
# prompt construction
# --------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are analyzing a normative specification for internal conflicts. "
    "You reason only from the text you are given: never invent provisions, "
    "never appeal to outside knowledge of the document. You answer with a "
    "single JSON object and nothing else."
)


def render_provisions(rows) -> str:
    """The whole section, in document order, with each provision tagged by the
    id that conflicts.json must cite. Subsection headings are reproduced so the
    text reads as the section it is."""
    out = []
    current = None
    for r in rows:
        path = r.get("section_path") or []
        sub = path[1] if len(path) > 1 else path[0] if path else ""
        if sub != current:
            current = sub
            out.append(f"\n## {sub}\n")
        out.append(f"[{prefix_id(r['focus_id'])}] {r['text']}")
    return "\n".join(out).strip()


USER_TEMPLATE = """\
Below is the complete text of the section "The chain of command" from the \
OpenAI Model Spec. It contains {n} provisions. Each is tagged with its \
identifier in square brackets at the start of the line, like [fa_8ep1]. \
Markers of the form [^xxxx] inside the text are source anchors in the \
original document; ignore them.

The question is exactly this:

    Which provisions in this section can conflict, and in what situation?

Two provisions conflict when there is a situation the section itself admits in \
which following one requires not following the other --- one obliges or permits \
an action the other forbids, or they demand incompatible actions. The situation \
must be one this text actually allows; do not invent facts the section rules \
out. Ground every claim in what these provisions say. Do not report a pair \
merely because it is thematically related or restates another provision; report \
a pair only if you can state the concrete situation in which they pull apart.

Report every such pair you can find. Do not pad the list, and do not stop \
early: completeness and groundedness both matter.

Return a single JSON object, no prose outside it, no markdown fences:

{{"conflicts": [
  {{"pair": ["fa_aaaa", "fa_bbbb"],
   "witness_prose": "one sentence describing the situation in which they conflict",
   "note": "why these two collide"}}
]}}

Rules for the output:
- "pair" holds exactly two distinct identifiers, both taken verbatim from the \
tags below, sorted in ascending string order.
- List each pair at most once.
- "witness_prose" is one sentence describing a concrete situation.
- If you find no conflicts, return {{"conflicts": []}}.

=== BEGIN SECTION ===

{provisions}

=== END SECTION ===
"""


def build_prompt(rows):
    return SYSTEM_PROMPT, USER_TEMPLATE.format(
        n=len(rows), provisions=render_provisions(rows))


# --------------------------------------------------------------------------
# response parsing
# --------------------------------------------------------------------------

def _extract_json_object(text: str):
    """First balanced {...} in the response, fences tolerated."""
    text = re.sub(r"^\s*```(?:json)?|```\s*$", "", text.strip(),
                  flags=re.MULTILINE)
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object in response")
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError("unbalanced JSON object in response")


def parse_response(text: str, valid_ids):
    """-> (conflicts, errors). Malformed items are recorded, never raised."""
    errors = []
    try:
        obj = _extract_json_object(text)
    except Exception as e:                                  # noqa: BLE001
        return [], [f"unparseable response: {e}"]
    items = obj.get("conflicts")
    if not isinstance(items, list):
        return [], ["response has no 'conflicts' list"]

    valid = set(valid_ids)
    seen, out = set(), []
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            errors.append(f"item {i}: not an object")
            continue
        pair = it.get("pair")
        if not isinstance(pair, list) or len(pair) != 2:
            errors.append(f"item {i}: pair is not a 2-element list ({pair!r})")
            continue
        pair = [prefix_id(p) for p in pair]
        bad = [p for p in pair if p not in valid]
        if bad:
            errors.append(f"item {i}: unknown focus id(s) {bad}")
            continue
        if pair[0] == pair[1]:
            errors.append(f"item {i}: self-pair {pair[0]}")
            continue
        key = tuple(sorted(pair))
        if key in seen:
            errors.append(f"item {i}: duplicate pair {list(key)}")
            continue
        seen.add(key)
        prose = it.get("witness_prose") or ""
        if not isinstance(prose, str) or not prose.strip():
            errors.append(f"item {i}: empty witness_prose for {list(key)}")
        out.append({
            "pair": list(key),
            "witness": {"ctx": []},            # §3: baseline ctx is always []
            "witness_prose": prose.strip() if isinstance(prose, str) else "",
            "note": (it.get("note") or "").strip()
            if isinstance(it.get("note"), str) else "",
        })
    return out, errors


def conflicts_doc(model, run_id, conflicts):
    return {"source": "baseline", "model": model, "run_id": run_id,
            "conflicts": conflicts}


# --------------------------------------------------------------------------
# runner
# --------------------------------------------------------------------------

def run(provider_name, k=3, live=False, out_dir=HERE, providers_path=PROVIDERS,
        focus_path=FOCUS_AREAS, log_dir=None, stamp=None,
        max_tokens=None, temperature=None):
    cfgs = {p.name: p for p in providers.ProviderConfig.load_all(providers_path)}
    if provider_name not in cfgs:
        raise SystemExit(f"unknown provider {provider_name!r}; "
                         f"known: {sorted(cfgs)}")
    cfg = cfgs[provider_name]
    # In-process overrides only; providers.json is Agent-shared and not edited.
    if max_tokens is not None:
        cfg.max_tokens = max_tokens
    if temperature is not None:
        cfg.temperature = temperature
    rows = load_focus_areas(focus_path)
    valid_ids = [prefix_id(r["focus_id"]) for r in rows]
    system, user = build_prompt(rows)
    log_dir = log_dir or os.path.join(out_dir, "prompt_log")
    stamp = stamp or datetime.datetime.now().strftime("%Y%m%dT%H%M%S")

    client = providers.make_client(cfg, live=live, log_dir=log_dir)
    written = []
    for i in range(1, k + 1):
        run_id = f"baseline-{provider_name}-{stamp}-r{i}"
        text = client.complete(system, user)
        if text is None:
            print(f"[dry-run] {run_id}: prompt logged to {log_dir} "
                  f"({len(system) + len(user)} chars), no call made")
            continue
        conflicts, errors = parse_response(text, valid_ids)
        doc = conflicts_doc(cfg.model, run_id, conflicts)
        path = os.path.join(out_dir, f"conflicts_baseline_run{i}.json")
        with open(path, "w") as f:
            json.dump(doc, f, indent=1)
        written.append(path)
        if errors:
            epath = path + ".parse_errors.json"
            with open(epath, "w") as f:
                json.dump({"run_id": run_id, "errors": errors,
                           "raw": text}, f, indent=1)
            print(f"{run_id}: {len(conflicts)} conflicts, "
                  f"{len(errors)} parse issues -> {epath}")
        else:
            print(f"{run_id}: {len(conflicts)} conflicts -> {path}")
    return written


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--provider", required=True,
                    help="provider name from providers.json")
    ap.add_argument("--k", type=int, default=3,
                    help="independent runs (contract: 3)")
    ap.add_argument("--live", action="store_true",
                    help="make real API calls (default: dry run)")
    ap.add_argument("--out-dir", default=HERE)
    ap.add_argument("--providers", default=PROVIDERS)
    ap.add_argument("--focus-areas", default=FOCUS_AREAS)
    ap.add_argument("--log-dir", default=None)
    ap.add_argument("--max-tokens", type=int, default=None,
                    help="override providers.json (default 4096 is tight for "
                         "a long conflict list)")
    ap.add_argument("--temperature", type=float, default=None,
                    help="override providers.json (default 0.2; the k=3 "
                         "self-agreement number is relative to this)")
    ap.add_argument("--print-prompt", action="store_true",
                    help="print the exact prompt and exit without any client")
    a = ap.parse_args(argv)

    if a.print_prompt:
        system, user = build_prompt(load_focus_areas(a.focus_areas))
        sys.stdout.write("### SYSTEM\n" + system + "\n\n### USER\n" + user + "\n")
        return 0
    run(a.provider, k=a.k, live=a.live, out_dir=a.out_dir,
        providers_path=a.providers, focus_path=a.focus_areas,
        log_dir=a.log_dir, max_tokens=a.max_tokens,
        temperature=a.temperature)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
