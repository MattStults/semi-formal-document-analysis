#!/usr/bin/env python3
"""Shared library for the panel pipeline: config, prompt builders, verdict parsing,
and the append-only/resumable run-log conventions.

Not a CLI. The executors are whole_doc.py (production, whole-document mode) and
run_rollout.py (the driver). Frozen rubric texts (v1 binary, v2 ternary+scope) are
kept verbatim because run-log rows and data provenance hashes key on them; v3 is
current (see compose_query).

Design rules every executor honors:
  * ONE uniform prompt per rubric for EVERY judge, reached through each provider
    OpenAI-compatible endpoint (openai SDK, swap base_url + key).
  * DURABLE: verdicts append to the run log the moment they arrive.
  * RESUMABLE: done_keys() lets a rerun skip any (behaviour, spec, model, locator)
    already recorded under the same rubric.
"""
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "spec-cite"))   # engine/panel -> engine/spec-cite
import cite  # noqa: E402

RUNLOG = HERE / "runlog.jsonl"
METRICS = HERE / "metrics.jsonl"   # per-call latency + token usage (for cost/time reporting)
SPECS = ("constitution", "model-spec")
BATCH = 40   # passages per prompt -- bounded output (compact format stays coherent)

# Providers/models/panels come from panel-config.json (credentials are env-var NAMES there,
# never values). The old hardcoded tables are gone; edit the config, not this file.
CONFIG = json.loads((HERE / "panel-config.json").read_text())
PROVIDERS = {name: (p["base_url"], p["key_env"]) for name, p in CONFIG["providers"].items()}
MODELS = {tag: (m["provider"], m["id"]) for tag, m in CONFIG["models"].items()}
PANELS = CONFIG.get("panels", {})

# v1: binary rubric (frozen -- the calibrated baseline; do not edit)
SYSTEM_V1 = ("You decide whether each spec passage is RELEVANT to a target behaviour. "
             "Mark 1 ONLY if the passage directly governs the SPECIFIC behaviour described -- it "
             "states, requires, or constrains that exact behaviour, such that you would cite this "
             "passage when assembling the spec's coverage of it. Being in the same topic area is "
             "NOT enough. Mark 0 for everything else, including passages that merely share "
             "vocabulary, sit near the topic, or describe the model's general goals, values, "
             "mission, helpfulness, trustworthiness, or good judgment without addressing THIS "
             "specific behaviour. The test: could a reader point to this passage as a rule the "
             "behaviour must follow? If not, mark 0. When in doubt, mark 0. "
             "Example -- behaviour 'do not endorse false claims': a passage requiring the model to "
             "correct a user's factual mistake = 1; a passage about being generally helpful or "
             "building user trust = 0, even though it is nearby in the document. "
             "For each passage, output one line: the passage number, a colon, then 1 (relevant) or "
             "0 (not). One line per passage, in order.{reason}")

# v2: ternary rubric (core / adjacent / neither) + per-behaviour Scope clause
# (frozen -- runlog v2 rows and export_coverage prompt hashes key on this exact text)
SYSTEM = ("You grade how each spec passage relates to a target behaviour, on a 3-point scale. "
          "2 = CORE: the passage directly governs the SPECIFIC behaviour described -- it "
          "states, requires, or constrains that exact behaviour, such that you would cite it "
          "when assembling the spec's coverage of the behaviour. "
          "1 = ADJACENT: the passage does not directly govern the behaviour, but materially "
          "bears on it -- it carries machinery the behaviour depends on, sets a boundary of "
          "it, or is a cross-reference a careful reader of this behaviour should see. "
          "0 = NEITHER: everything else, including passages that merely share vocabulary, sit "
          "near the topic, or describe the model's general goals, values, mission, or virtues "
          "without bearing on THIS specific behaviour -- UNLESS the target behaviour is itself "
          "about one of those general values, in which case passages that state, define, or "
          "give force to that value are CORE. "
          "Being in the same topic area alone is NOT enough for 1. When in doubt between 2 and "
          "1, mark 1; when in doubt between 1 and 0, mark 0. "
          "Example -- behaviour 'do not endorse false claims': a passage requiring the model "
          "to correct a user's factual mistake = 2; a passage on how confident assessments "
          "should be phrased = 1; a passage about being generally trustworthy = 0. "
          "For each passage, output one line: the passage number, a colon, then 2, 1, or 0. "
          "One line per passage, in order.{reason}")
# v3: coverage-report framing + labelled behaviour fields (current).
# Changes over v2: states WHY (the verdicts become a coverage report, so absence of
# findings is a valid result), names the input fields and how to use each, adds the
# partial-governance and Scope-exclusion rules, and demands independent per-passage grading.
SYSTEM_V3 = (
    "You are auditing how thoroughly an AI alignment document -- a model constitution or a "
    "model spec -- covers one target behaviour. These documents are long and address a "
    "behaviour in scattered places, so it is hard to tell whether the behaviour is "
    "comprehensively governed. The set of passages you mark becomes the document's coverage "
    "report for this behaviour: it is what lets a reader judge whether coverage is thorough, "
    "thin, or absent. "
    "The behaviour is described by four fields. Behaviour: its title. Definition: the "
    "construct itself -- what the behaviour requires; judge against this, not against the "
    "title's vocabulary. Clarifications (optional): notes resolving ambiguities. Scope "
    "(optional): the construct's edges, usually naming neighbouring behaviours that are "
    "NOT this one. An optional field reading 'none provided' only means the user left it "
    "blank -- infer nothing from that; when Scope is not provided, judge against the "
    "Definition alone. "
    "Grade every passage independently, on its own text (the § section path is context "
    "only), on a 3-point scale. "
    "2 = CORE: the passage directly governs the SPECIFIC behaviour described -- it states, "
    "requires, or constrains that exact behaviour, such that you would cite it when "
    "assembling the document's coverage of the behaviour. A passage that does so in only "
    "one clause or list item still counts for what it says about THIS behaviour. "
    "1 = ADJACENT: the passage does not directly govern the behaviour, but materially "
    "bears on it -- it carries machinery the behaviour depends on, sets a boundary of it, "
    "or is a cross-reference a careful reader of this behaviour should see. "
    "0 = NEITHER: everything else, including passages that merely share vocabulary, sit "
    "near the topic, or describe the model's general goals, values, mission, or virtues "
    "without bearing on THIS specific behaviour -- UNLESS the target behaviour is itself "
    "about one of those general values, in which case passages that state, define, or give "
    "force to that value are CORE. A passage that governs only a behaviour the Scope "
    "excludes is 0 -- at most 1 if it also sets a boundary the target behaviour must "
    "respect. "
    "Calibration: the document may cover the behaviour thoroughly, thinly, or not at all. "
    "Finding few or no relevant passages is a correct and informative result -- never "
    "stretch a grade so that coverage appears. The opposite error is just as costly: a "
    "passage that genuinely governs the behaviour must be marked wherever in the document "
    "it sits. Being in the same topic area alone is NOT enough for 1. When in doubt "
    "between 2 and 1, mark 1; when in doubt between 1 and 0, mark 0. "
    "Example -- behaviour 'do not endorse false claims': a passage requiring the model "
    "to correct a user's factual mistake = 2; a passage on how confident assessments "
    "should be phrased = 1; a passage about being generally trustworthy = 0. "
    "For each passage, output one line: the passage number, a colon, then 2, 1, or 0. "
    "One line per passage, in order.{reason}")

SYSTEMS = {"v1": SYSTEM_V1, "v2": SYSTEM, "v3": SYSTEM_V3}

# v3 behaviour block -- ONE variable per user-form field, fixed shape (no conditional
# lines): a form populates these four slots later. clarifications and scope are
# OPTIONAL -- an empty form field renders as FIELD_NONE, never an omitted line.
FIELD_NONE = "none provided"
BEHAVIOUR_TEMPLATE_V3 = ("Behaviour: {title}\n"
                         "Definition: {definition}\n"
                         "Clarifications (optional): {clarifications}\n"
                         "Scope (optional): {scope}")


def env(name):
    v = os.environ.get(name)
    if not v and (HERE / ".env").exists():
        for line in (HERE / ".env").read_text().splitlines():
            if line.strip().startswith(name + "="):
                v = line.split("=", 1)[1].strip().strip("\"'")
    return v


def client_for(provider):
    base, keyname = PROVIDERS[provider]
    key = env(keyname)
    if not key:
        sys.exit(f"no {keyname} in env/.env for provider {provider}")
    from openai import OpenAI
    return OpenAI(api_key=key, base_url=base) if base else OpenAI(api_key=key)


def passages(spec):
    """(locator, section, text) for every content paragraph, TOC-filtered -- reuses cite.py."""
    out = []
    version, sections, lines = cite.load_spec(spec, None)
    titles = {cite.normalize(s.path_str.split(" > ")[-1]) for s in sections}
    for sec in sections:
        ref = f"#{sec.anchor}" if (spec == "model-spec" and sec.anchor) else sec.path_str
        for i, raw in enumerate(cite.segment_blocks(lines, sec.start, sec.end), 1):
            t = cite.normalize(raw)
            if t.strip() and t not in titles:
                out.append((f"{spec}@{version} > {ref} > ¶{i}", sec.path_str, t))
    return out


def load_query(behaviour):
    b = json.loads((HERE / "behaviours.json").read_text())
    if behaviour not in b:
        sys.exit(f"unknown behaviour {behaviour!r} -- add it to behaviours.json (from behaviours-for-adria)")
    return b[behaviour]["query"]


def compose_query(behaviour, rubric):
    """The behaviour block of the user message -- the variable slot the tool user fills.

    v3 contract (what we ask the user for, via a form): title and definition required,
    clarifications and scope optional (blank -> FIELD_NONE). One variable per field,
    substituted into BEHAVIOUR_TEMPLATE_V3. behaviours.json fields: title (falls back
    to label) / query (query_v2 override) / clarifications / boundary.
    v1 and v2 render byte-identically to the pre-refactor paths (frozen).
    """
    query = load_query(behaviour)   # also validates the behaviour key
    beh = json.loads((HERE / "behaviours.json").read_text())[behaviour]
    if rubric == "v1":
        return f"Behaviour:\n{query}"
    if rubric == "v2":
        if not beh.get("boundary"):
            sys.exit(f"--v2: no boundary clause for {behaviour}")
        return f"Behaviour:\n{beh.get('query_v2', query)}\n\nScope: {beh['boundary']}"
    return BEHAVIOUR_TEMPLATE_V3.format(
        title=beh.get("title", beh["label"]),
        definition=beh.get("query_v2", query),
        clarifications=beh.get("clarifications") or FIELD_NONE,
        scope=beh.get("boundary") or FIELD_NONE)


def user_msg(qblock, batch):
    """Full user message: behaviour block + numbered passages + bounded output ask."""
    body = "\n".join(f"[{i+1}] (§ {sec}) {t}" for i, (_, sec, t) in enumerate(batch))
    return f"{qblock}\n\nPassages:\n{body}\n\nOutput {len(batch)} verdict lines."


def done_keys(rubric):
    """Resume keys include the rubric version -- a v2 rerun must not be satisfied by v1 rows."""
    if not RUNLOG.exists():
        return set()
    return {(d["behaviour"], d["spec"], d["model"], d["locator"])
            for d in (json.loads(l) for l in RUNLOG.read_text().splitlines() if l.strip())
            if d.get("rubric", "v1") == rubric}


def parse_verdicts(txt, n):
    """{index(1-based): 0/1/2}. First try 'N: V' lines; fall back to positional verdicts."""
    keyed = {}
    for line in txt.splitlines():
        m = re.match(r'\s*\[?(\d+)\]?\s*[:.\)\-]\s*([012])\b', line)
        if m:
            keyed[int(m.group(1))] = int(m.group(2))
    keyed = {k: v for k, v in keyed.items() if 1 <= k <= n}   # drop out-of-range indices
    if len(keyed) >= n * 0.9:
        return keyed
    # Positional fallback: verdicts live at the END of the output (reasoning may precede and
    # contain digits). Take the last n bare 0/1/2 tokens; if there aren't exactly enough clean
    # ones in the tail, refuse to guess -- unparsed items stay unparsed rather than misaligned.
    tail = txt.splitlines()[-(n + 5):]
    seq = re.findall(r'(?<![.\d\[])([012])(?![.\d\]])', "\n".join(tail))
    if len(seq) == n:
        return {i + 1: int(v) for i, v in enumerate(seq)}
    return keyed
