#!/usr/bin/env python3
"""Recursive document-graph builder on the phase_1 provider harness (DeepSeek).

Runs the RECURSE_PROMPT.md protocol (divide -> leaves -> unwind) as plain API
calls instead of tool-using agents:

  - Phase D and Phase L are single completions: the span text is IN the prompt.
  - Phase U's mechanical half (concatenate, provides index, dangling report,
    duplicate-provider report) is CODE; the model only returns decisions
    (resolutions, renames, merges, structure nodes), which code applies and
    re-verifies. This is deliberate: the 2026-08-10 subagent build showed the
    mechanical parts are where models economize, and the decisions are small.

Caching: the system prompt is RECURSE_PROMPT.md verbatim, byte-identical on
every call, so the provider's prefix cache covers it; all per-call content
(dispatch, span text, reports) goes in the user turn. Cache hits are read back
from each response and reported at the end.

Provider, key resolution, cost measurement and the spend ledger are reused
from phase_1/translate.py (openai-compatible, stdlib urllib, TOGETHER_API_KEY
by default -- see driver_config.json). Every live run is gated: it prints a
worst-case estimate and refuses to spend without --yes.

Usage:
  python3 recurse_driver.py --mock            # free end-to-end on the toy doc
  python3 recurse_driver.py --dry-run         # plan + cost estimate, no calls
  python3 recurse_driver.py --yes --out runs/ds1   # live build (spends money)
  python3 recurse_driver.py --yes --out runs/ds1   # again: resumes from disk

Resumability: each tree node's artifacts (division.json / graph.json) are the
state; a re-run skips finished directories, so a crash or a killed run loses
at most one call.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)
# translate._resolve_key falls back to semi-formal-experiment/providers.py's
# rc-file parser for the API key; make that import resolvable from this
# entry point too (found live 2026-08-10: env var only exists in login shells)
sys.path.append(os.path.abspath(os.path.join(
    HERE, "..", "..", "..", "..", "..", "semi-formal-experiment")))

import translate as T  # noqa: E402  (phase_1 harness: Provider, Client, cost)

BRIEF_PATH = os.path.join(HERE, "RECURSE_PROMPT.md")
LEAF_MAX_LINES = 300      # spans at or under this go straight to Phase L
DEPTH_MAX = 8             # hard stop against runaway division


# ----------------------------------------------------------------- utilities
def sha16(blob):
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def write_json(path, obj):
    """Atomic write: tmp + rename, so a killed run never leaves half a file
    that wedges resume (review F13)."""
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1)
    os.replace(tmp, path)


def load_doc(path):
    raw = open(path).read()
    lines = raw.splitlines()          # true line count (trailing-newline safe:
    return lines                      # the 4691-vs-4692 lesson lives here)


def numbered(lines, lo, hi):
    return "\n".join(f"L{i:04d}  {lines[i - 1]}" for i in range(lo, hi + 1))


def normalise(s):
    """Quote-verification normaliser (ported from graph_check, incl. links)."""
    s = re.sub(r"\[\^[^\]]+\]", "", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = s.replace("**", "").replace("*", "")
    s = (s.replace("“", '"').replace("”", '"')
          .replace("’", "'").replace("‘", "'"))
    return re.sub(r"\s+", " ", s).strip().lower()


def nm(x):
    return x if isinstance(x, str) else x["name"]


def parse_json_reply(text):
    """Model replies must be one JSON object; tolerate a ```json fence."""
    t = text.strip()
    try:                                    # forced json_object: usually clean
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", t, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    start = t.find("{")
    if start < 0:
        raise ValueError("no JSON object in reply")
    return json.loads(t[start:t.rfind("}") + 1])


# ------------------------------------------------------------- validation
def autofix_division(d, inherited=()):
    """Deterministic consistency repair, run BEFORE validation (2026-08-10,
    live root failure): the model states established_around correctly and
    then names a provider child whose span does not contain it. The right
    provider child is DERIVABLE -- the child containing established_around --
    so code fixes the link instead of spending a repair round asking the
    model to. Only the provider ASSIGNMENT is touched; established_around
    itself is never altered, so a genuinely misplaced seed still fails
    validation. Fixes are logged into the artifact."""
    if d.get("decision") != "divide":
        return d
    # F17 carriage autofix (ds4 live 2026-08-12, 4 repair rounds): an
    # inherited seed established in-span was dropped from seed_vocabulary.
    # Carriage is COPYING a known entry through -- no judgment; restore it.
    lo0, hi0 = d.get("_span_lo"), d.get("_span_hi")
    if lo0 is not None and hi0 is not None:
        have = {s.get("name") for s in d.get("seed_vocabulary", [])
                if isinstance(s, dict)}
        for s in inherited:
            ea = s.get("established_around") if isinstance(s, dict) else None
            if (isinstance(ea, list) and len(ea) >= 2 and lo0 <= ea[0]
                    and ea[1] <= hi0 and s.get("name") not in have):
                d.setdefault("seed_vocabulary", []).append(dict(s))
                d.setdefault("driver_autofixes", []).append(
                    f"restored dropped inherited seed '{s['name']}' "
                    f"(carriage: established in-span at {ea[:2]})")
    # -- contiguity repair (2026-08-11 live: "last child ends 4089, span
    # ends 4692" survived 4 repair rounds). EXTEND-ONLY, because an
    # oversized child is re-divided at the next recursion level, so no cut
    # information is lost -- while a gap aborts the build. Overlaps are NOT
    # touched: two children claiming one line is a real ambiguity the model
    # must resolve. lo/hi are attached by the caller (divide()).
    lo, hi = d.get("_span_lo"), d.get("_span_hi")
    ch = [c for c in d.get("children", []) if isinstance(c, dict)
          and isinstance(c.get("span"), list) and len(c["span"]) == 2]
    if lo is not None and hi is not None and ch:
        if ch[0]["span"][0] > lo:
            d.setdefault("driver_autofixes", []).append(
                f"first child start {ch[0]['span'][0]} -> {lo}")
            ch[0]["span"][0] = lo
        for a, b in zip(ch, ch[1:]):
            if b["span"][0] > a["span"][1] + 1:
                gap = b["span"][0] - 1 - a["span"][1]
                d.setdefault("driver_autofixes", []).append(
                    (f"LARGE-GAP ({gap} lines) closed -- dropped-child-"
                     f"shaped (review F8): " if gap > 10 else "gap closed: ")
                    + f"child ending {a['span'][1]} extended to "
                      f"{b['span'][0] - 1}")
                a["span"][1] = b["span"][0] - 1
        if ch[-1]["span"][1] < hi:
            d.setdefault("driver_autofixes", []).append(
                f"last child end {ch[-1]['span'][1]} -> {hi}")
            ch[-1]["span"][1] = hi
    spans = [c.get("span") for c in d.get("children", [])
             if isinstance(c, dict)]
    # FIRST-wins on duplicate seed names (ds5 live 2026-08-12: the model
    # legitimately seeded chain_of_command at two establishment sites; the
    # validator's provenance check consults the FIRST entry, and this dict
    # was last-wins -- autofix and validator disagreed about which seed to
    # read, making the link unfixable by construction). Coherence demands
    # both read the same entry.
    seeds = {}
    for s in d.get("seed_vocabulary", []):
        if isinstance(s, dict):
            seeds.setdefault(s.get("name"), s)
    for x in d.get("expected_cross_links", []):
        if not isinstance(x, dict):
            continue
        # provides_side_child 0 is NEVER a valid index; it is the model's
        # encoding of "no child provides this" (ds3 live, twice -- the first
        # fix was gated on seed metadata absent for inherited seeds).
        # Provided-elsewhere is encoded by ABSENCE: drop unconditionally.
        if x.get("provides_side_child") == 0:
            d.setdefault("driver_autofixes", []).append(
                f"dropped cross-link '{x.get('name')}': "
                f"provides_side_child 0 means no child provides it -- "
                f"provided-elsewhere is encoded by absence")
            x["_dropped"] = True
            continue
        seed = seeds.get(x.get("name"))
        ea = (seed or {}).get("established_around")
        if not (isinstance(ea, list) and len(ea) >= 2):
            continue
        owner = next((i + 1 for i, sp in enumerate(spans)
                      if isinstance(sp, (list, tuple)) and len(sp) == 2
                      and sp[0] <= ea[0] <= sp[1]), None)
        pi = x.get("provides_side_child")
        # ds3 live failure 2026-08-11: for INHERITED seeds established
        # outside this span the model encodes "provided by neither child"
        # as provides_side_child 0. The correct encoding of provided-
        # elsewhere is ABSENCE (the need dangles and escalates, per
        # protocol), so the mis-encoded entry is dropped -- deterministic-
        # safe: its correct form carries no information.
        if owner is None and pi in (0, None):
            d.setdefault("driver_autofixes", []).append(
                f"dropped cross-link '{x.get('name')}': seed established "
                f"outside the span ({ea[:2]}) and no child provides it -- "
                f"provided-elsewhere is encoded by absence")
            x["_dropped"] = True
            continue
        if owner is not None and pi != owner:
            d.setdefault("driver_autofixes", []).append(
                f"cross-link '{x.get('name')}': provides_side_child "
                f"{pi} -> {owner} (child containing established_around "
                f"{ea[:2]})")
            x["provides_side_child"] = owner
    return d


def validate_division(d, lo, hi, inherited=(), leaf_max=LEAF_MAX_LINES):
    errs = []
    if d.get("decision") not in ("divide", "leaf"):
        errs.append("decision must be 'divide' or 'leaf'")
    if d.get("decision") != "divide":
        # the leaf dodge (root probe 2026-08-10): DeepSeek declared the whole
        # 4692-line document "one cohesive unit" and validated clean. A leaf
        # claim is only plausible near leaf scale.
        if d.get("decision") == "leaf" and (hi - lo + 1) > 2 * leaf_max:
            errs.append(
                f"span of {hi - lo + 1} lines declared leaf; a span over "
                f"{2 * leaf_max} lines must divide (decision: 'divide', "
                f"2-3 children)")
        return errs
    ch = d.get("children", [])
    if not 2 <= len(ch) <= 3:
        errs.append(f"need 2-3 children, got {len(ch)}")
    spans = []
    for c in ch:
        sp = c.get("span") if isinstance(c, dict) else None
        if (not isinstance(sp, (list, tuple)) or len(sp) != 2
                or not all(isinstance(v, int) for v in sp)):
            errs.append(f"child span must be [a, b] ints, got {sp!r}")
            return errs
        a, b = sp
        if not (lo <= a <= b <= hi):
            errs.append(f"child span [{a},{b}] empty or outside [{lo},{hi}]")
        spans.append((a, b))
    if spans:
        if spans[0][0] != lo:
            errs.append(f"first child starts {spans[0][0]}, span starts {lo}")
        if spans[-1][1] != hi:
            errs.append(f"last child ends {spans[-1][1]}, span ends {hi}")
        for (a1, b1), (a2, b2) in zip(spans, spans[1:]):
            if a2 != b1 + 1:
                errs.append(f"gap/overlap between {b1} and {a2}")
    seed_names = {s.get("name") for s in d.get("seed_vocabulary", [])
                  if isinstance(s, dict)}
    d["expected_cross_links"] = [
        x for x in d.get("expected_cross_links", [])
        if not (isinstance(x, dict) and x.get("_dropped"))]
    for x in d.get("expected_cross_links", []):
        if not isinstance(x, dict):
            errs.append(f"cross-link entries must be objects, got {x!r:.40}")
            continue
        if x.get("name") not in seed_names:
            errs.append(f"cross-link '{x.get('name')}' not in seed_vocabulary")
        for side in ("provides_side_child", "needs_side_child"):     # F7
            v = x.get(side)
            if isinstance(v, int) and not (1 <= v <= max(len(spans), 1)):
                errs.append(f"cross-link '{x.get('name')}': {side} {v} "
                            f"outside 1..{len(spans)}")
        # provenance (review F17): a concept established OUTSIDE a child's
        # span must not be predicted as provided by that child
        seed = next((s for s in d.get("seed_vocabulary", [])
                     if isinstance(s, dict) and s.get("name") == x.get("name")
                     and isinstance(s.get("established_around"), list)), None)
        pi = x.get("provides_side_child")
        if seed and isinstance(pi, int) and 1 <= pi <= len(spans):
            ea_lo, ea_hi = seed["established_around"][:2]
            ca, cb = spans[pi - 1]
            if lo <= ea_lo and ea_hi <= hi and not (ca <= ea_lo <= cb):
                errs.append(
                    f"cross-link '{x['name']}': provider child {pi} "
                    f"[{ca},{cb}] does not contain established_around "
                    f"[{ea_lo},{ea_hi}]")
    # F3a (driver-layer review): a division-coined seed whose
    # established_around is outside this span is a hallucination -- coined
    # seeds derive from the parent's own text. Inherited seeds may point
    # outside; they are distinguished by name.
    inherited_names = {s.get("name") for s in inherited
                       if isinstance(s, dict)}
    for s in d.get("seed_vocabulary", []):
        ea = s.get("established_around") if isinstance(s, dict) else None
        if (isinstance(ea, list) and len(ea) >= 2
                and s.get("name") not in inherited_names
                and not (lo <= ea[0] <= hi)):
            errs.append(f"seed '{s.get('name')}': established_around "
                        f"{ea[:2]} outside [{lo},{hi}] and not inherited -- "
                        f"a coined seed cannot be established where this "
                        f"division cannot see")
    # inherited-seed carriage (review F17): an inherited seed established
    # inside some child's span must be visible to that child
    child_seed_names = seed_names
    for s in inherited:
        ea = s.get("established_around") if isinstance(s, dict) else None
        if (isinstance(ea, list) and len(ea) >= 2 and lo <= ea[0] and
                ea[1] <= hi and s.get("name") not in child_seed_names):
            errs.append(f"inherited seed '{s['name']}' (established in-span "
                        f"at {ea[:2]}) dropped from seed_vocabulary")
    return errs


def dedupe_nodes(g):
    """Drop nodes whose (establishes, spans, needs, provides) are EXACT
    duplicates of an earlier node -- the 2026-08-11 degenerate-loop finding:
    one leaf reply carried 969 byte-identical copies of a single node under
    distinct ids, and every id-based check passed. Removing an exact copy
    cannot lose content; anything less than exact is left for validation.
    Returns the number removed and logs into the graph."""
    seen, kept, dropped = set(), [], 0
    for n in g.get("nodes", []):
        key = (n.get("establishes"),
               json.dumps(n.get("spans"), sort_keys=True),
               json.dumps(n.get("needs"), sort_keys=True),
               json.dumps(n.get("provides"), sort_keys=True))
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        kept.append(n)
    if dropped:
        g["nodes"] = kept
        g.setdefault("driver_autofixes", []).append(
            f"deduped {dropped} exact duplicate node(s)")
    return dropped


# ----------------------------------------------- derived uncovered (ds3 flag)
# HEADINGISH-style classifier (sweep_headings.py's HEADINGISH, split into
# named reasons): the formatting classes a leaf may leave uncovered without
# the model saying anything about them. Everything else is CONTENT.
_FMT_HEADING = re.compile(r"#{1,6}(\s|$)")
_FMT_BOLDLINE = re.compile(r"\*\*[^*]+\*\*")
_FMT_RULE = re.compile(r"[-=~_*]{3,}")


def formatting_reason(line):
    """Reason label when a line is pure formatting; None for content."""
    s = line.strip()
    if not s:
        return "blank"
    if _FMT_HEADING.match(s) or _FMT_BOLDLINE.fullmatch(s):
        return "heading"
    if s.startswith("```") or s.startswith("~~~"):
        return "fence"
    if re.fullmatch(r"</?[a-z_]+(\s+[a-z_]+=\"[^\"]*\")*\s*/?>", s):
        # bare example-markup tags (<comparison>, </assistant>, ...) -- ds4
        # live 2026-08-12: structural wrappers like fences. A tag line WITH
        # content on it stays content.
        return "example-markup"
    if s.startswith("!!!"):
        # admonition markers (`!!! meta "Commentary"`) -- ds4 live
        # 2026-08-12: the marker LINE is structure, like a heading; the
        # commentary content below it stays content
        return "admonition-marker"
    if _FMT_RULE.fullmatch(s):
        return "horizontal-rule"
    return None


#: Density band for a leaf, in nodes per span line. Golden-graph leaves sit
#: at 0.13-0.35; the degenerate draws sat at 5.3. The ceiling is generous
#: (2x the healthy top) because a legitimately list-like region is denser
#: than prose -- this exists to catch runaway replies, not style.
LEAF_DENSITY_MAX = 0.7


_AUTH_LABEL = re.compile(r"authority\s*=\s*(root|system|developer|user|"
                         r"guideline)")

#: The five canonical level names plus the hierarchy node -- the ONLY lawful
#: spellings of the authority dependency. Never treated as coinages.
AUTHORITY_CANONICAL = frozenset((
    "root_authority", "system_authority", "developer_authority",
    "user_authority", "guideline_authority", "authority_levels_hierarchy"))

#: Widened coinage pattern (ds7 acceptance RESIDUALS (a), 2026-08-14): the
#: literal "section_authority" substring check missed VARIANT coinages of
#: the "X_section_<level>_authority" shape (live escape:
#: "ask_clarifying_questions_section_guideline_authority"). Any name with
#: "section_" followed anywhere later by "authority" is a coinage. ONE
#: compiled constant consulted by BOTH autofix_authority_coinages and
#: validate_leaf -- the duplicate-seed lesson: one source both consult, so
#: the validator and the autofix cannot drift.
_AUTH_COINAGE = re.compile(r"section_.*authority")


def is_authority_coinage(name):
    return (isinstance(name, str)
            and name not in AUTHORITY_CANONICAL
            and bool(_AUTH_COINAGE.search(name)))


def autofix_authority_coinages(g, lines):
    """Deterministic canonicalization (Matt-approved restructure,
    2026-08-13): a per-section authority coinage (`X_section_authority`)
    whose node's span contains the document's own `authority=LEVEL` label
    is mechanically renamed to the canonical `LEVEL_authority` -- the
    document names the level; code only reads it. Unmappable coinages are
    left for validate_leaf to reject (repair loop). Prose is kept."""
    for n in g.get("nodes", []):
        # the node's SECTION label = the nearest authority= label at or
        # ABOVE its first span line (pre-ds7 review finding 3: an in-span
        # scan canonicalized to the NEXT section's label when a span ran
        # over an adjacent heading; sectioning truth reads upward)
        spans = n.get("spans", [])
        if not spans:
            continue
        start = min((s.get("lines") or [10**9])[0] for s in spans)
        level = None
        for ln in range(min(start, len(lines)), 0, -1):
            m = _AUTH_LABEL.search(lines[ln - 1])
            if m:
                level = m.group(1)
                break
        if level is None:
            continue                     # no label above: validator's
        canon = f"{level}_authority"     # problem, not autofix's
        for key in ("needs", "provides"):
            for d in n.get(key, []):
                name = d.get("name") if isinstance(d, dict) else None
                if is_authority_coinage(name):
                    d["name"] = canon
                    g.setdefault("driver_autofixes", []).append(
                        f"{n.get('id')}: authority coinage '{name}' -> "
                        f"'{canon}' (span's own authority= label)")
    return g


def validate_leaf(g, lo, hi, lines, derive_uncovered=False, seeds=(),
                  enforce_promise_delivery=False):
    """Leaf checks. `derive_uncovered` (ds3 flag, default OFF) switches the
    coverage tail: instead of trusting a model-emitted `uncovered` and
    failing on the identity, code DERIVES uncovered as the coverage
    complement, auto-labels formatting runs, and errors only on uncovered
    CONTENT lines (cover-or-explain). Default False is the pinned ds2
    behavior, byte-identical.

    `enforce_promise_delivery` (item B, Matt 2026-08-14; ds8 prevention of
    the ds7 broken-promise class -- 45 promised names no child delivered):
    an inherited seed whose established_around falls INSIDE [lo, hi] must
    either be provided under exactly its name or be declined in
    judgment_calls naming the seed -- cover-or-explain, the ds3
    uncovered-content pattern exactly. Default False for byte-parity with
    every pinned build."""
    errs = []
    dedupe_nodes(g)
    autofix_authority_coinages(g, lines)
    if enforce_promise_delivery and seeds:
        jcs = " ".join(j for j in g.get("judgment_calls", [])
                       if isinstance(j, str))
        provided = {nm(p) for n in g.get("nodes", [])
                    for p in n.get("provides", [])}
        for s in seeds:
            ea = s.get("established_around") if isinstance(s, dict) else None
            name = s.get("name") if isinstance(s, dict) else None
            if not (name and isinstance(ea, (list, tuple)) and len(ea) >= 2
                    and lo <= ea[0] and ea[1] <= hi):
                continue                 # established elsewhere: not owed
            if name in provided or name in jcs:
                continue
            errs.append(
                f"the inherited seed '{name}' ({s.get('prose', '')}) is "
                f"established around L{ea[0]}-{ea[1]} INSIDE your span, "
                f"but your reply provides no entry with that name. If "
                f"this span genuinely establishes it, add a provides "
                f"entry named exactly '{name}'; if it does NOT, say why "
                f"in judgment_calls naming '{name}'")
    # Matt-approved restructure 2026-08-13 (ENFORCED, not prose: the leaf
    # extra has carried the convention since 08-11 and ds6 still emitted
    # 283 coinages): any surviving per-section authority coinage is an
    # error the repair loop must fix -- the canonical names are the ONLY
    # lawful spelling of this dependency.
    for n in g.get("nodes", []):
        for key in ("needs", "provides"):
            for d in n.get(key, []):
                name = d.get("name") if isinstance(d, dict) else d
                if is_authority_coinage(name):
                    errs.append(
                        f"{n.get('id')}: '{name}' is a per-section "
                        f"authority coinage -- FORBIDDEN by the authority "
                        f"convention. Use the canonical level name "
                        f"(root/system/developer/user/guideline_authority) "
                        f"or authority_levels_hierarchy")
    span_lines = hi - lo + 1
    if len(g.get("nodes", [])) > max(LEAF_DENSITY_MAX * span_lines, 8):
        errs.append(
            f"{len(g['nodes'])} nodes for a {span_lines}-line span "
            f"(density {len(g['nodes']) / span_lines:.2f}/line). A node is "
            f"one CLAIM, typically one per 3-5 content lines; do not split "
            f"every sentence into its own node and do not repeat nodes")
    ids = [n.get("id") for n in g.get("nodes", [])]
    if len(set(ids)) != len(ids):
        errs.append("duplicate node ids")
    want = f"L{lo}-{hi}_"
    for i in ids:
        if not (isinstance(i, str) and i.startswith(want)):
            errs.append(f"node id {i!r} must start with {want!r} "
                        f"(cross-sibling collision guard)")
    covered = set()
    for n in g.get("nodes", []):
        for f in ("needs", "provides"):
            for x in n.get(f, []):
                if not (isinstance(x, dict) and x.get("name") and x.get("prose")):
                    errs.append(f"{n.get('id')}: {f} entry must be "
                                f"{{name, prose}}, got {x!r:.60}")
        for sp in n.get("spans", []):
            a, b = sp.get("lines", (0, 0))
            if not (lo <= a <= b <= hi):
                errs.append(f"{n.get('id')}: span [{a},{b}] outside [{lo},{hi}]")
                continue
            covered.update(range(a, b + 1))
            q = sp.get("quote")
            if q and normalise(q) not in normalise(
                    " ".join(lines[a - 1:b])):
                # show the REAL text (meltdown_analysis.md: repair feedback
                # never revealed the line, so the model re-fabricated from
                # memory -- it cannot copy what it cannot see)
                actual = " ".join(lines[a - 1:b])[:200]
                errs.append(f"{n.get('id')}: quote not verbatim on L{a}-{b}: "
                            f"{q[:60]!r}. The ACTUAL text is: {actual!r} -- "
                            f"copy from it character-for-character or omit "
                            f"the quote")
    if not g.get("nodes"):
        errs.append("nodes list is empty — a span always establishes "
                    "something (review F6)")
    if derive_uncovered:
        # ds3 determinization (EXPERIMENTS.md, RULINGS + DETERMINIZATION
        # WAVE 2026-08-11): uncovered is the coverage COMPLEMENT, computed
        # here, so the gap-arithmetic / coverage-identity failure class
        # cannot occur. Formatting runs are auto-labeled by regex; the one
        # residue that still needs the model is an uncovered CONTENT line,
        # which errors with a cover-or-explain ask. An explanation is a
        # judgment_calls entry naming the line (e.g. "L0042 ...").
        jcs = [j for j in g.get("judgment_calls", []) if isinstance(j, str)]

        def _explained(i):
            pat = re.compile(rf"\bL0*{i}\b|\bline\s+0*{i}\b", re.I)
            return any(pat.search(j) for j in jcs)

        derived, residue = [], []
        for i in range(lo, hi + 1):
            if i in covered:
                continue
            reason = formatting_reason(lines[i - 1])
            if reason is None:
                if _explained(i):
                    reason = "explained in judgment_calls"
                else:
                    residue.append(i)
                    continue
            if (derived and derived[-1]["reason"] == reason
                    and derived[-1]["lines"][1] == i - 1):
                derived[-1]["lines"][1] = i
            else:
                derived.append({"lines": [i, i], "reason": reason})
        if 0 < len(residue) <= 2:
            # ds4 live 2026-08-12 (L201: model covered to L199 and stopped,
            # 4 rounds, zero discharges): a TINY residue is recorded
            # honestly as unclaimed rather than blocking the build --
            # visible in uncovered, health rows, and every audit surface.
            # The alternative (code extending an adjacent node's span) was
            # REJECTED: ownership attachment is a content judgment.
            # >2 residue lines remain a hard failure below.
            for i in residue:
                derived.append({"lines": [i, i],
                                "reason": "unclaimed-content (autofixed "
                                          "after repair non-convergence)"})
            g.setdefault("driver_autofixes", []).append(
                f"recorded {len(residue)} unclaimed content line(s) as "
                f"uncovered: {[f'L{i}' for i in residue]}")
            residue = []
        for i in residue[:10]:
            errs.append(
                f"uncovered content line L{i:04d} "
                f"({lines[i - 1].strip()[:60]!r}) is not formatting and "
                f"belongs to no node -- either extend/add a node to cover "
                f"it, or explain it in judgment_calls naming L{i:04d}. "
                f"⚠️ Example dialogue (<user>/<assistant> lines, ~~~ block "
                f"contents) belongs to the SPAN of the node that interprets "
                f"the example -- extend that node's span over the whole "
                f"example block")
        if len(residue) > 10:
            errs.append(f"...and {len(residue) - 10} more uncovered "
                        f"content lines")
        g["uncovered"] = derived        # model-emitted uncovered is ignored
        return errs
    unc = set()
    for u in g.get("uncovered", []):
        ab = u.get("lines", (0, 0)) if isinstance(u, dict) else (0, 0)
        if len(ab) != 2 or not (lo <= ab[0] <= ab[1] <= hi):
            errs.append(f"uncovered range {ab} outside span [{lo},{hi}]")
            continue
        a, b = ab
        unc.update(range(a, b + 1))
    missing = [i for i in range(lo, hi + 1)
               if lines[i - 1].strip() and i not in covered and i not in unc]
    if missing:
        errs.append(f"coverage identity fails: {len(missing)} unaccounted "
                    f"lines, first {missing[:5]}")
    return errs


MERGE_EL = re.compile(r"\((\d)\)\s*([^;.,:(]{3,60})|"
                      r"\b([A-Z][a-z]+(?: [A-Z][a-z]+)+)\b|\"([^\"]{3,40})\"")


def merge_loss(survivor_blob, retired_text):
    """Elements of the retired establishes absent from the survivor (heuristic;
    RED-verified against the n028/n008 tier loss)."""
    missing = []
    els = list(MERGE_EL.finditer(retired_text))
    for m in els:
        el = m.group(2) or m.group(3) or m.group(4)   # never the enum digit
        if el and el.strip().lower() not in survivor_blob.lower():
            missing.append(el.strip())
    if not els:
        # F2 (driver-layer review): the element regexes see only enumerated/
        # Capitalized items, so an all-lowercase claim could vanish in a
        # merge unseen. Floor: content words of the retired text must
        # substantially appear in the survivor. Adds a trigger; lowers none.
        words = [w for w in re.findall(r"[a-z]{5,}",
                                       retired_text.lower())]
        if words:
            hit = sum(1 for w in set(words)
                      if w in survivor_blob.lower())
            if hit / len(set(words)) < 0.6:
                missing.append(f"(lowercase content: only {hit}/"
                               f"{len(set(words))} content words survive)")
    return sorted(set(missing))


# ------------------------------------------------------------- unwind (code)
def unwind_mechanics(children_graphs):
    nodes, uncovered = [], []
    for g in children_graphs:
        nodes.extend(g.get("nodes", []))
        uncovered.extend(g.get("uncovered", []))
    provides = {}
    for n in nodes:
        for p in n.get("provides", []):
            provides.setdefault(nm(p), []).append(n["id"])
    dangling = [{"needer": n["id"], "name": nm(d),
                 "prose": d.get("prose", "") if isinstance(d, dict) else ""}
                for n in nodes for d in n.get("needs", [])
                if nm(d) not in provides]
    dup = {k: v for k, v in provides.items() if len(v) > 1}
    return nodes, uncovered, provides, dangling, dup


# ------------------------------------------- rename pre-matching (ds3 flag)
_CONTENT_WORD = re.compile(r"[a-z0-9]{4,}")


def _content_words(text):
    return set(_CONTENT_WORD.findall(normalise(text or "")))


def rename_candidates(dangling, nodes, top=3):
    """ds3 `rename_candidates` determinization: for each dangling need, the
    top-`top` provided names ranked by normalized content-word overlap
    (Jaccard) between the need's PROSE and each provides entry's PROSE.
    Plain code, no model call; deterministic (score desc, then name).
    This only orders the model's reading -- the decision loop is unchanged,
    and the prompt tells the model to judge on MEANING, never on rank or
    name similarity."""
    prose_words = {}
    for n in nodes:
        for p in n.get("provides", []):
            if isinstance(p, dict) and p.get("name"):
                prose_words.setdefault(p["name"], set()).update(
                    _content_words(p.get("prose", "")))
    out = []
    for d in dangling:
        need = _content_words(d.get("prose") or d.get("name", ""))
        scored = []
        for name, words in prose_words.items():
            union = need | words
            score = len(need & words) / len(union) if union else 0.0
            if score > 0:
                scored.append((-score, name))
        scored.sort()
        out.append({"needer": d.get("needer"), "name": d.get("name"),
                    "candidates": [{"name": name, "overlap": round(-s, 3)}
                                   for s, name in scored[:top]]})
    return out


def apply_decisions(nodes, decisions, provides, lo=None, hi=None, lines=None):
    """Apply the model's unwind decisions; every application is checked.
    Structure nodes get full leaf-grade validation when lines are supplied
    (review F5); merges check absorption BEFORE mutating (F19) and union
    the retired node's needs (F4); a resolution matching no needs entry is
    an error, not a no-op (F20)."""
    by_id = {}
    for n in nodes:
        if n["id"] in by_id:
            return [], [f"duplicate node id across children: {n['id']}"]
        by_id[n["id"]] = n
    log, errs = [], []
    for r in decisions.get("resolutions", []):
        if not isinstance(r, dict):
            errs.append(f"resolution must be an object: {r!r:.60}")
            continue
        n = by_id.get(r.get("needer"))
        if not n:
            errs.append(f"resolution names unknown needer {r.get('needer')}")
            continue
        newname = r.get("rename_to") or r.get("name")
        if newname not in provides:
            errs.append(f"resolution to unprovided name {newname!r}")
            continue
        if set(provides.get(newname, [])) == {n["id"]}:
            # SET comparison (delta review D4, probe P3): a node providing
            # the target name TWICE gave provides[name] == [id, id] != [id],
            # bypassing the list-equality guard and resolving the need
            # against its own node -- exactly what F5 exists to stop.
            # F5, promoted to AUTOFIX-DROP 2026-08-11: the model proposed
            # self-satisfying resolutions for 4 straight repair rounds. The
            # correct disposition of a provably-nonsense resolution IS to
            # not apply it -- the need stays dangling and escalates upward,
            # which is what the protocol says should happen. Dropping loses
            # nothing; paying rounds bought nothing.
            log.append(f"DROPPED self-satisfying resolution: {newname!r} "
                       f"sole-provided by its needer {n['id']}")
            continue
        hits = 0
        for d in n.get("needs", []):
            if nm(d) == r.get("name") and isinstance(d, dict):
                d["name"] = newname
                hits += 1
                log.append(f"resolved {n['id']}.{r['name']} -> {newname}")
        if not hits:
            errs.append(f"resolution matched no needs entry {r.get('name')!r} "
                        f"on {n['id']}")
    for m in decisions.get("merges", []):
        if isinstance(m, dict) and m.get("survivor") == m.get("retired"):
            errs.append(f"merge names the same node twice: {m}")     # F1
            continue
        s = by_id.get(m.get("survivor")) if isinstance(m, dict) else None
        r = by_id.get(m.get("retired")) if isinstance(m, dict) else None
        if not (s and r) or "establishes" not in (r or {}):
            errs.append(f"merge names unknown/malformed node(s): {m}")
            continue
        blob = (s.get("establishes", "") + " " + " ".join(
            p.get("prose", "") for p in s.get("provides", [])
            if isinstance(p, dict)))
        lost = merge_loss(blob, r["establishes"])
        if lost:                        # check BEFORE mutating (F19)
            errs.append(f"merge {r['id']}->{s['id']} loses content: {lost}")
            continue
        s["spans"] = s.get("spans", []) + r.get("spans", [])
        for field in ("provides", "needs"):        # union BOTH (F4)
            seen = {nm(p) for p in s.get(field, [])}
            s.setdefault(field, []).extend(
                p for p in r.get(field, []) if nm(p) not in seen)
        nodes.remove(r)
        log.append(f"merged {r['id']} into {s['id']}")
    sns = decisions.get("structure_nodes", [])
    if sns and lines is not None:
        probe = {"nodes": sns, "uncovered": [{"lines": [lo, hi]}]}
        for e in validate_leaf(probe, lo, hi, lines):
            if "coverage identity" not in e and "must start with" not in e:
                errs.append(f"structure node invalid: {e}")
    for sn in sns:
        if not isinstance(sn, dict) or not sn.get("id") or sn["id"] in by_id:
            errs.append(f"structure node bad/duplicate id: "
                        f"{sn.get('id') if isinstance(sn, dict) else sn!r}")
            continue
        if not errs:
            nodes.append(sn)
            by_id[sn["id"]] = sn     # F4: a second copy now collides
            log.append(f"added structure node {sn['id']}")
    return log, errs


# ---------------------------------------------------- reply schemas (forcing)
# Per-phase json_schema response_format: the SAME endpoint accepts strict
# json_schema in translate.py, so the graph build gets the same protection --
# type-level shape errors (span as "1-3", bare-string provides, missing
# fields) die at decode time instead of costing a repair round-trip.
# Non-strict deliberately: our validators are the semantic authority, and a
# strict grammar that rejects a fixable reply outright would replace a cheap
# in-band repair with an opaque API error.
_NAME_PROSE = {"type": "object",
               "properties": {"name": {"type": "string"},
                              "prose": {"type": "string"}},
               "required": ["name", "prose"]}
_LINES2 = {"type": "array", "items": {"type": "integer"},
           "minItems": 2, "maxItems": 2}
_NODE = {"type": "object",
         "properties": {
             "id": {"type": "string"},
             "establishes": {"type": "string"},
             "needs": {"type": "array", "items": _NAME_PROSE},
             "provides": {"type": "array", "items": _NAME_PROSE},
             "spans": {"type": "array", "items": {
                 "type": "object",
                 "properties": {"lines": _LINES2, "quote": {"type": "string"}},
                 "required": ["lines"]}}},
         "required": ["id", "establishes", "needs", "provides", "spans"]}
_STR_LIST = {"type": "array", "items": {"type": "string"}}
DIVISION_SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {"type": "string", "enum": ["divide", "leaf"]},
        "children": {"type": "array", "minItems": 2, "maxItems": 3,
                     "_": "2-3 children is the recursion protocol's core "
                          "discipline, and the 2026-08-10 root probe showed "
                          "DeepSeek ignoring the prose (47 and 191 children); "
                          "the grammar states it where prose failed",
                     "items": {
            "type": "object",
            "properties": {"span": _LINES2,
                           "why_this_cut": {"type": "string"}},
            "required": ["span"]}},
        "seed_vocabulary": {"type": "array", "items": {
            "type": "object",
            "properties": {"name": {"type": "string"},
                           "prose": {"type": "string"},
                           "established_around": _LINES2},
            "required": ["name", "prose"]}},
        "expected_cross_links": {"type": "array", "items": {
            "type": "object",
            "properties": {"name": {"type": "string"},
                           "needs_side_child": {"type": "integer"},
                           "provides_side_child": {"type": "integer"},
                           "evidence": {"type": "string"}},
            "required": ["name"]}},
        "judgment_calls": _STR_LIST},
    # ds4 live 2026-08-12: with per-request schema enforcement on the batch
    # path, the model LAWFULLY omitted non-required fields -- complete
    # well-formed divisions with no `children` at all, 4 repair rounds.
    # A divide without children is not a division; required in the grammar.
    # (A "leaf" declaration emits empty arrays for these -- harmless, the
    # leaf path never reads them.)
    "required": ["decision", "children", "seed_vocabulary",
                 "expected_cross_links"]}
LEAF_SCHEMA = {
    "type": "object",
    "properties": {
        "nodes": {"type": "array", "items": _NODE},
        "uncovered": {"type": "array", "items": {
            "type": "object",
            "properties": {"lines": _LINES2, "reason": {"type": "string"}},
            "required": ["lines"]}},
        "judgment_calls": _STR_LIST},
    "required": ["nodes", "uncovered"]}
#: ds3 `derive_uncovered` variant: the model must NOT emit `uncovered`
#: (code derives it), so the schema neither requires nor describes it.
LEAF_SCHEMA_DERIVED = {
    "type": "object",
    "properties": {"nodes": LEAF_SCHEMA["properties"]["nodes"],
                   "judgment_calls": _STR_LIST},
    "required": ["nodes"]}
UNWIND_SCHEMA = {
    "type": "object",
    "properties": {
        "resolutions": {"type": "array", "items": {
            "type": "object",
            "properties": {"needer": {"type": "string"},
                           "name": {"type": "string"},
                           "rename_to": {"type": "string"}},
            "required": ["needer", "name"]}},
        "merges": {"type": "array", "items": {
            "type": "object",
            "properties": {"survivor": {"type": "string"},
                           "retired": {"type": "string"}},
            "required": ["survivor", "retired"]}},
        "structure_nodes": {"type": "array", "items": _NODE},
        "cross_link_report": {"type": "array", "items": {
            "type": "object",
            "properties": {"expected": {"type": "string"},
                           "outcome": {"type": "string"}}}},
        "judgment_calls": _STR_LIST},
    "required": ["resolutions", "merges", "structure_nodes"]}


# ------------------------------------------------------------- model clients
def divide_extra():
    """THE Phase D dispatch extra -- single source (delta_review_driver.md
    D1/D7: this string existed in THREE copies -- Driver.divide,
    Driver.unwind's continuity reconstruction, and the core's
    Scheduler._want_division -- and drift between the first two silently
    breaks the reconstructed transcript's byte-identity: no error, just a
    cache-missing, subtly diverged replay. Same lesson as leaf_extra."""
    return ("Reply with the Phase D division.json object "
            "(decision/children/seed_vocabulary/expected_cross_links/"
            "judgment_calls). Declaring {\"decision\": \"leaf\"} is "
            "allowed when the whole span is one cohesive unit. "
            "⚠️ EXACTLY 2 OR 3 children -- never more. You are one "
            "level of a recursion; your children will divide further. "
            "Do NOT segment the span finely.")


def leaf_extra(lo, hi):
    """THE leaf dispatch extra -- single source of truth (the quote-rule
    meltdown hid in a drifted copy of this string; three copies existed)."""
    return ("Reply with the Phase L graph.json object "
            "(nodes/uncovered/judgment_calls). Node ids are prefixed "
            f"L{lo}-{hi}_. Include `quote` only when you are copying "
            "the text character-for-character from the numbered span "
            "above; otherwise simply omit it -- quotes are optional. "
            "A quote may never span a [?](#...) cross-reference: quote "
            "a fragment that stops before the reference, or omit. "
            "AUTHORITY CONVENTION (EVERY node's needs, not only "
            "headings): any node leaning on a section's authority level "
            "carries a needs entry naming the SHARED canonical "
            "authority-level concept (root_authority / system_authority / "
            "developer_authority / user_authority / guideline_authority, "
            "or authority_levels_hierarchy for the ordering) -- never a "
            "per-section coinage like X_section_authority (now also "
            "ENFORCED by validator). "
            "OBLIGATION STRENGTH: state each obligation at the "
            "passage's own strength -- must/never stays mandatory, "
            "should stays should, may stays optional. Do not flatten, "
            "strengthen, or weaken (measured drift class, 2026-08-13).")


def leaf_schema(lo, hi):
    """LEAF_SCHEMA with a dynamic maxItems on nodes: the density band moved
    INTO the grammar so a repetition loop cannot emit node N+1 at all
    (Matt's format-level question, 2026-08-11). Bound mirrors
    LEAF_DENSITY_MAX with the same +8 floor as validate_leaf."""
    import copy
    sch = copy.deepcopy(LEAF_SCHEMA)
    span = hi - lo + 1
    sch["properties"]["nodes"]["maxItems"] = int(
        max(LEAF_DENSITY_MAX * span, 8))
    return ("leaf_graph", sch)


def unwind_schema(n_dangling, n_nodes, provided_names=None, node_ids=None,
                  dangling_names=None):
    """UNWIND_SCHEMA with dynamic maxItems (2026-08-11: the unwind was the
    one reply shape left grammar-unbounded -- Matt's catch during the long
    root draw). Bounds are protocol-derived: resolutions cannot exceed the
    dangling count the driver itself computed; judgment_calls economy is
    ~10 by the brief. Strings stay uncappable; the validator remains the
    semantic authority.

    ENUM FORCING (Matt's plan, 2026-08-12): when the option pools are
    supplied, the decision fields become per-dispatch ENUMS of only the
    valid options -- rename_to from the names actually provided, needer /
    survivor / retired from the actual node ids, name from the actual
    dangling names. Measured pools are small (<=123 names graph-wide,
    median seed pool 34.5), so the grammar itself now rules out the
    rename-to-nothing class that burned four repair rounds on ds5. Pools
    omitted -> byte-identical to the ungated schema (flag-off parity)."""
    import copy
    sch = copy.deepcopy(UNWIND_SCHEMA)
    p = sch["properties"]
    p["resolutions"]["maxItems"] = max(n_dangling, 1)
    p["merges"]["maxItems"] = max(n_nodes // 2, 4)
    p["structure_nodes"]["maxItems"] = 8
    p["cross_link_report"]["maxItems"] = max(n_dangling + 10, 20)
    p["judgment_calls"]["maxItems"] = 12
    res = p["resolutions"]["items"]["properties"]
    mrg = p["merges"]["items"]["properties"]
    if provided_names:
        res["rename_to"]["enum"] = sorted(set(provided_names))
    if node_ids:
        ids = sorted(set(node_ids))
        res["needer"]["enum"] = ids
        mrg["survivor"]["enum"] = ids
        mrg["retired"]["enum"] = ids
    if dangling_names:
        res["name"]["enum"] = sorted(set(dangling_names))
    return ("unwind_decisions", sch)


def leaf_dispatch(lo, hi, cfg):
    """THE leaf (extra, schema, derive-flag) construction -- single source
    for Driver.leaf AND the core's _want_leaf (delta_review_driver.md D1:
    the derive_uncovered variant lived only in Driver.leaf, so a core-mode
    ds3 build silently ran ds2 validation semantics -- the model was never
    told not to emit `uncovered` and the wrong grammar was pinned).
    RULING (recorded here, not transcript-only): BOTH variants ride the
    grammar-capped leaf_schema nodes bound. Driver.leaf had drifted back to
    the uncapped static LEAF_SCHEMA while the core and the instruments used
    leaf_schema(lo, hi) -- 'the grammar the pipeline uses'
    (authority_convention.md). Rejected alternative, by name: replicating
    the static schema into the core would have single-sourced the DRIFT
    instead of the design (the cap exists so a repetition loop cannot emit
    node N+1 at all; dropping it from either path re-opens that hole)."""
    extra = leaf_extra(lo, hi)
    name, sch = leaf_schema(lo, hi)
    derive = bool(cfg.get("derive_uncovered"))   # ds3 flag, default off
    if derive:
        extra += (" ⚠️ ds3: do NOT emit `uncovered` -- the driver "
                  "derives it from your nodes' spans and auto-labels "
                  "formatting lines (headings, blanks, fences, "
                  "horizontal rules). Cover every CONTENT line with a "
                  "node; a content line that genuinely establishes "
                  "nothing must be explained in judgment_calls naming "
                  "its line number (e.g. \"L0042: ...\").")
        name, sch = "leaf_graph_derived", {
            "type": "object",
            "properties": {"nodes": sch["properties"]["nodes"],
                           "judgment_calls": _STR_LIST},
            "required": ["nodes"]}
    return extra, (name, sch), derive


def resolution_schema(n_dangling, n_nodes, **pools):
    """The unwind grammar with merges/structure_nodes CLOSED
    (delta_review_driver.md D3): the resolution pass's ONLY job is
    resolutions. A structure node admitted here would be appended with
    lo/hi/lines all None -- skipping leaf-grade validation entirely (the
    ghost-node hole, probe P6) -- and a merge would run with no unwind
    context. Keeps the 'unwind_decisions' schema name so the per-phase
    output cap still keys on it."""
    name, sch = unwind_schema(n_dangling, n_nodes, **pools)
    p = sch["properties"]
    p["merges"]["maxItems"] = 0
    p["structure_nodes"]["maxItems"] = 0
    return (name, sch)


def classify_cap_overflow(partial_text):
    """D6 stage 1 (Matt-approved bisect mechanism, 2026-08-11): decide
    whether a truncated-at-cap leaf reply is DENSE (genuinely too much
    clean content -- the only state where bisection is the remedy) or a
    MALFUNCTION (dup-loop / degenerate repetition -- bisecting a
    malfunction yields two malfunctions; the existing failure path owns
    it). Deliberately conservative: anything not clearly dense is a
    malfunction. Wired into nothing until stage 3."""
    import collections
    ids = re.findall(r'"id"\s*:\s*"(L\d+-\d+_n\d+)"', partial_text)
    est = re.findall(r'"establishes"\s*:\s*"([^"]{0,80})', partial_text)
    if not ids or not est:
        return "malfunction"          # not even node-shaped content
    if len(set(ids)) < len(ids) * 0.9:
        return "malfunction"          # id repetition
    top = collections.Counter(est).most_common(1)[0][1]
    if top > max(3, len(est) * 0.2):
        return "malfunction"          # establishes repetition (the 969 class)
    return "dense"


def autofix_unwind_merges(o, nodes, provides, lo=None, hi=None, lines=None):
    """Drop merges the validator rejects for content loss, recorded --
    never repaired (ds6 2026-08-12: two unwinds burned 4 repair rounds
    each re-proposing loses-content merges; the identical-reply restart
    fired and the fresh draws re-proposed them too, so the recorded
    reconsideration trigger for this EXACT alternative has fired --
    EXPERIMENTS.md 'rejected alternative, by name', now adopted). A merge
    is an OPTIONAL dedupe: the un-merged graph is the valid pre-merge
    state, so declining a rejected merge makes no content decision; the
    validator's own content-loss finding is the deterministic signal.
    Only loses-content rejections are dropped -- every other error class
    still repairs."""
    if not isinstance(o, dict) or not o.get("merges"):
        return o
    import copy as _c
    _log, errs = apply_decisions(_c.deepcopy(nodes), _c.deepcopy(o),
                                 provides, lo, hi, lines)
    bad = set()
    for e in errs:
        m = re.match(r"merge (\S+)->(\S+) loses content", str(e))
        if m:
            bad.add((m.group(1), m.group(2)))
    if bad:
        o["merges"] = [
            mg for mg in o["merges"]
            if not (isinstance(mg, dict)
                    and (mg.get("retired"), mg.get("survivor")) in bad)]
        o.setdefault("_dropped_merges", []).extend(
            sorted(f"{a}->{b}" for a, b in bad))
    return o


def enum_pools(cfg, nodes, provides, dangling):
    """The per-dispatch option pools for unwind_schema's enum forcing --
    single source for Driver.unwind, the core's _want_unwind and the
    resolution pass. `enum_decisions` off -> {} -> byte-identical schema
    (flag-off parity, same discipline as every other ds3+ flag)."""
    if not cfg.get("enum_decisions"):
        return {}
    # ds6 lesson (2026-08-13 ruling): the RENAME enums are OFF for good --
    # a closed menu of valid targets made wrong-but-valid the model's path
    # of least resistance (31% mismatched edges). Only the ID enums stay:
    # needer/survivor/retired are pure syntax (a wrong id is never a
    # plausible-but-wrong content decision, just an error the validator
    # catches). Renames are adjudicated by the seat instead.
    return {"node_ids": [n["id"] for n in nodes]}


def broken_promises(division, children_graphs):
    """Promise-vs-delivery check (Matt-approved, ds5 2026-08-12): a division
    PROMISES cross-links via expected_cross_links, and nothing verified
    delivery -- ds5's c3/c2 promised `chain_of_command` that no leaf of any
    child ever provided, discovered only as 24 danglings in the final graph.
    Returns the promised names no child's nodes provide. Code only OBSERVES
    and records (health.jsonl); having the driver ADD the missing provides
    would be a content decision -- rejected by name (EXPERIMENTS.md)."""
    provided = set()
    for g in children_graphs:
        for n in g.get("nodes", []):
            for p in n.get("provides", []):
                provided.add(nm(p))
    out = []
    for x in division.get("expected_cross_links", []) or []:
        name = x.get("name") if isinstance(x, dict) else None
        if name and name not in provided:
            out.append(name)
    return out


def unwind_inputs(division, children, lo, hi, cfg):
    """Unwind mechanics + THE unwind user prompt -- single source, shared
    with the smoke test (Matt 2026-08-11: root-unwind per-model fixture)."""
    nodes, uncovered, provides, dangling, dup = unwind_mechanics(children)
    involved = {d["needer"] for d in dangling}
    involved |= {i for v in dup.values() for i in v}
    context = [{k: n.get(k) for k in
                ("id", "establishes", "needs", "provides", "spans")}
               for n in nodes if n["id"] in involved]
    # every node, compactly, so restatement pairs under DIFFERENT names
    # and rename targets can be judged on prose, not name similarity
    # (review F7/F8)
    summaries = [{"id": n["id"], "establishes": n.get("establishes", ""),
                  "provides": [{"name": nm(p),
                                "prose": p.get("prose", "")
                                if isinstance(p, dict) else ""}
                               for p in n.get("provides", [])]}
                 for n in nodes]
    cand_block = ""                        # ds3 flag, default off: the
    if cfg.get("rename_candidates") and dangling:   # off path is
        cand_block = (                     # byte-identical ("" insert)
            "CANDIDATES (lexical suggestions ONLY; measured on the golden the "
            "TRUE provider is ABSENT ~1 in 10 -- ALWAYS scan the full "
            "summaries too; judge on MEANING, never name similarity):\n"
            + json.dumps(rename_candidates(dangling, nodes), indent=1)
            + "\n")
    user = (f"YOUR DISPATCH\nPhase: U\nSpan: lines {lo}-{hi}\n"
            "The mechanical merge is DONE in code. Decide only what "
            "follows, from the reports below. NEVER resolve a need "
            "against a node that merely mentions the concept; needs no "
            "child provides stay dangling (omit them from resolutions). "
            "MERGES: nodes about DIFFERENT sections are never "
            "restatements, however similar their template (a "
            "section-authority claim for section X and one for section Y "
            "are two facts); prefer keeping both nodes over any merge "
            "that would blur which section a claim belongs to.\n"
            f"Your division (with its expected_cross_links):\n"
            f"{json.dumps(division, indent=1)}\n"
            f"DANGLING NEEDS:\n{json.dumps(dangling, indent=1)}\n"
            f"{cand_block}"
            f"DUPLICATE PROVIDERS (restatement-merge candidates):\n"
            f"{json.dumps(dup, indent=1)}\n"
            f"PROVIDED NAMES:\n{json.dumps(sorted(provides), indent=1)}\n"
            f"NODES INVOLVED (full):\n{json.dumps(context, indent=1)}\n"
            f"ALL NODES (id, establishes, provides w/ prose -- use these "
            f"to find restatements under different names and to judge "
            f"renames on PROSE, never name similarity):\n"
            f"{json.dumps(summaries, indent=1)}\n"
            "⚠️ REPLY SIZE CONTRACT: your reply is DECISIONS ONLY and "
            "should be well under 2000 tokens. NEVER re-emit node "
            "content, summaries, or the reports above. A dangling need "
            "with no clear provider among the summaries is LEFT ALONE "
            "-- danglings are an expected, recorded outcome, not a "
            "failure to fix. An empty resolutions list is a legitimate "
            "reply. judgment_calls: decision CLASSES only, max ~10.\n"
            "Reply with ONE JSON object: {\"resolutions\": [{\"needer\", "
            "\"name\", \"rename_to\" (a provided name)}], \"merges\": "
            "[{\"survivor\", \"retired\"}], \"structure_nodes\": [full "
            "node objects, id prefixed L" + f"{lo}-{hi}" + "_], "
            "\"cross_link_report\": [...], \"judgment_calls\": [...]}")
    return nodes, uncovered, provides, dangling, dup, user


def continuity_transcript(drv, division, lo, hi, seeds, u_user):
    """THE [D-user, D-reply, U-user] reconstruction (transcript_continuity):
    single source for Driver.unwind AND the core's _want_unwind
    (delta_review_driver.md D1: the core sent a bare U string while serial
    sent the three-message transcript -- the restored architecture did not
    exist on the default execution path). The divide exchange is
    deterministic + stored, so the transcript is rebuilt byte-identically;
    the prefix cache already holds brief + D-user from the divide call."""
    d_user = drv.dispatch_block("D", lo, hi, list(seeds), divide_extra())
    stored = {k: v for k, v in division.items() if not k.startswith("_")}
    return [{"role": "user", "content": d_user},
            {"role": "assistant", "content": json.dumps(stored)},
            {"role": "user", "content": u_user}]


class GraphClient(T.Client):
    """phase_1 Client with per-call json_schema forcing (falling back to
    json_object if the endpoint rejects response_format -- same downgrade
    translate.py performs). Set `reply_schema` before a call; None means
    json_object.
    `_log_usage` sees the FULL normalized envelope (with cached-token counts)
    that `_send` does not return (review F9) -- stash it for the tally, and
    enforce the run's spend ceiling here, on measured dollars (review F10)."""

    max_cost_usd = None
    last_usage = None
    max_tokens_override = None   # per-phase cap, set per call
    reply_schema = None          # (name, schema) tuple, set per call
    _schema_rejected = False     # endpoint said no once -> json_object forever

    def _body(self, system, user):
        body = super()._body(system, user)
        if self.max_tokens_override:
            body["max_tokens"] = self.max_tokens_override
        if self.reply_schema and not self._schema_rejected:
            name, sch = self.reply_schema
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": name, "strict": False,
                                "schema": sch}}
        else:
            body["response_format"] = {"type": "json_object"}
        return body

    def _log_usage(self, env):
        self.last_usage = env.get("usage") or {}
        super()._log_usage(env)
        if self.max_cost_usd and self.spent_usd > self.max_cost_usd:
            raise T.CostGateError(
                f"measured spend ${self.spent_usd:.2f} exceeds the run "
                f"ceiling ${self.max_cost_usd:.2f} (cost.max_cost_usd) -- "
                f"artifacts so far are kept; resume raises again unless the "
                f"ceiling is raised")


class MockClient:
    """Free stand-in: replays canned replies for the toy-document test."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls, self.spent_usd = 0, 0.0

    def complete(self, system, user):
        self.calls += 1
        return {"text": json.dumps(self.replies.pop(0)), "usage": {}}

    def complete_messages(self, system, messages):
        return self.complete(system, "")


# ------------------------------------------------------------- driver
class Driver:
    def __init__(self, cfg, client, lines, out):
        self.cfg, self.client, self.lines, self.out = cfg, client, lines, out
        self.leaf_max = cfg.get("leaf_max_lines", LEAF_MAX_LINES)
        self.brief = open(BRIEF_PATH).read()
        self.brief_sha = sha16(self.brief)
        self.cache_hits = self.cache_misses = 0

    # -- one validated model call with a single repair retry ---------------
    def _attempt(self, env, validate):
        try:
            obj = parse_json_reply(env["text"])
            return obj, validate(obj)
        except Exception as exc:            # noqa: BLE001  (review F12: any
            return None, [f"reply failed to parse/validate: {exc!r:.200}"]

    def _bury(self, user, text, errs):
        """Failed replies are evidence, not garbage (review F25)."""
        d = os.path.join(self.out, "failed")
        os.makedirs(d, exist_ok=True)
        stamp = f"{int(time.time() * 1000)}"
        write_json(os.path.join(d, stamp + ".json"),
                   {"errors": [str(e) for e in errs],
                    "reply": text, "user_head": user[:2000]})

    def _complete(self, method, *args):
        """One completion, with two bounded recoveries:
        - json_schema rejected by the endpoint -> downgrade to json_object
          (mirrors translate.py's fallback);
        - TRUNCATED at max_tokens -> resample up to twice. Live finding
          2026-08-10: the reasoning channel's length is stochastic -- the
          same root dispatch truncated at 32K twice and completed in 8K
          on the third draw. A truncation is a bad DRAW, not a bad prompt;
          aborting a multi-hour build on one wastes everything after it."""
        for attempt in range(7):
            try:
                return method(*args)
            except Exception as exc:        # noqa: BLE001
                detail = str(exc)
                if (getattr(self.client, "reply_schema", None)
                        and not getattr(self.client, "_schema_rejected", True)
                        and ("response_format" in detail
                             or "json_schema" in detail)):
                    self.client._schema_rejected = True
                    continue
                transient = ("TRUNCATED" in detail or "timed out" in detail
                             or "HTTP 5" in detail    # 500/502/503/529
                             or "HTTP 402" in detail  # credit propagation
                             or "HTTP 429" in detail  # rate limit
                             or "Connection" in detail
                             or "unavailable" in detail
                             or "urlopen error" in detail   # DNS/route loss
                             or "Errno" in detail           # (sleep/wake)
                             or "empty response" in detail)  # F6: bad draw
                # 402 short ladder -- mirrored in dispatch_core._ladder
                # (steps-1-4 audit 2026-08-12, BUG 2): ride out a credit
                # propagation flap, fail fast on real exhaustion. F1/F6
                # (routing-gap audit 2026-08-14): TRUNCATED and empty
                # replies ride the same short ladder -- the identical-retry
                # seam guard varies the bytes on each retry, and after two
                # varied tries the failure routes to call()'s fresh-restart
                # path or raises, instead of six byte-identical redraws.
                if (attempt >= 2 and ("HTTP 402" in detail
                                      or "TRUNCATED" in detail
                                      or "empty response" in detail)):
                    transient = False
                if transient and attempt < 6:
                    wait = min(30 * (attempt + 1), 180)
                    print(f"    (transient [{detail[:50]}], retry "
                          f"{attempt + 1}/6 in {wait}s)")
                    time.sleep(wait)
                    continue
                raise

    #: Per-phase output caps (Matt 2026-08-11: fail-and-fix beats
    #: burn-and-wait; forensics showed no hidden reasoning channel, so the
    #: 131K headroom only slowed diagnosis). Generous multiples of healthy.
    #: `leaf_graph_derived` is the SAME leaf phase under its ds3 schema name
    #: (found by the D1 flags-on equivalence pin: the cap lookup keys on the
    #: schema name, so the derived variant ran UNCAPPED on every path -- the
    #: caps-never-engaged defect class, one more name deep).
    PHASE_MAX_TOKENS = {"division": 16384, "leaf_graph": 24576,
                        "leaf_graph_derived": 24576,
                        "unwind_decisions": 8192}

    def call(self, user, validate, schema=None, _restarted=False):
        if hasattr(self.client, "reply_schema"):
            self.client.reply_schema = schema
        if schema and hasattr(self.client, "max_tokens_override"):
            self.client.max_tokens_override = self.cfg.get(
                "phase_max_tokens", self.PHASE_MAX_TOKENS).get(schema[0])
        # per-dispatch spend budget (Matt's ruling 2026-08-11): retries and
        # repair rounds for ONE dispatch may not spend more than this; the
        # overnight failure mode was a single leaf redrawing at $0.055/draw
        # with only an aggregate ceiling watching. Checked between draws on
        # MEASURED spend; the dispatch fails loudly (resumable) at the cap.
        budget = self.cfg.get("per_dispatch_usd", 0.30)
        spent0 = getattr(self.client, "spent_usd", 0.0)

        def _over():
            used = getattr(self.client, "spent_usd", 0.0) - spent0
            if used > budget:
                raise T.Phase1Error(
                    f"dispatch exceeded its spend budget "
                    f"(${used:.2f} > ${budget:.2f} per_dispatch_usd). "
                    f"Repeated expensive draws mean this dispatch needs a "
                    f"DIAGNOSIS, not more retries -- see health.jsonl and "
                    f"the failed/ dir")
        if isinstance(user, list):
            env = self._complete(self.client.complete_messages, self.brief,
                                 list(user))
        else:
            env = self._complete(self.client.complete, self.brief, user)
        _over()
        self._tally(env)
        obj, errs = self._attempt(env, validate)
        if not errs:
            return obj
        # F5 (routing-gap audit 2026-08-14): the oversize threshold uses the
        # ENGAGED cap -- the schema-keyed per-phase cap when one applies,
        # model.max_tokens otherwise. Phase-capped replies are bounded below
        # model.max_tokens, so the old threshold made the D6 dense/
        # malfunction machinery unreachable whenever phase caps engaged.
        out_cap = None
        if schema:
            out_cap = self.cfg.get("phase_max_tokens",
                                   self.PHASE_MAX_TOKENS).get(schema[0])
        if not out_cap:
            out_cap = self.cfg.get("model", {}).get("max_tokens", 16384)
        if len(env["text"]) > out_cap * 3:   # ~chars/token floor (review F11)
            self._bury(user, env["text"], errs)
            # D6 stage 1 wired live (ds5 2026-08-12, mirrored in
            # dispatch_core.feed): a MALFUNCTION (dup-loop) resamples fresh
            # once; only a DENSE span fails -- retrying THAT at the same cap
            # would overflow again
            if (classify_cap_overflow(env["text"]) == "malfunction"
                    and not _restarted):
                print("    (oversize first draw is a MALFUNCTION, not "
                      "dense; one fresh resample)")
                return self.call(user, validate, schema, _restarted=True)
            raise T.Phase1Error(
                "oversize first draw (dense span, or malfunction resample "
                "already spent) at max_tokens; reduce leaf_max_lines "
                "or raise model.max_tokens rather than retrying")
        # up to cfg `max_repairs` (default 2) ACCUMULATING repair rounds:
        # the 2026-08-10 translation sample needed 2-3 attempts routinely,
        # and a 1-repair driver would abort a multi-hour build on failures
        # that fix in one more round
        transcript = (list(user) if isinstance(user, list)
                      else [{"role": "user", "content": user}])
        max_repairs = self.cfg.get("max_repairs", 2)
        for rnd in range(1, max_repairs + 1):
            transcript.append({"role": "assistant", "content": env["text"]})
            transcript.append({"role": "user", "content":
                               ("Your reply failed mechanical checks:\n- "
                                + "\n- ".join(str(e) for e in errs)
                                + "\nReturn the corrected COMPLETE JSON "
                                  "object and nothing else.")})
            try:
                env = self._complete(self.client.complete_messages,
                                     self.brief, transcript)
            except T.ProviderError as exc:
                # persistent truncation in a repair round: the transcript
                # itself inflates the reasoning burn. A FRESH dispatch draw
                # completes where the laden one cannot (measured 2026-08-10:
                # same dispatch, 3x truncated with transcript, 8K clean
                # without). One whole-call restart, then give up loudly.
                if "TRUNCATED" in str(exc) and not _restarted:
                    print("    (repair transcript truncating; restarting "
                          "dispatch fresh)")
                    return self.call(user, validate, schema, _restarted=True)
                raise
            self._tally(env)
            _over()
            obj, errs = self._attempt(env, validate)
            if not errs:
                return obj
            self._bury(user, env["text"], [f"repair round {rnd}"]
                       + [str(e) for e in errs])
            # byte-identical to the reply it was asked to correct: the
            # transcript adds no information (ds5 2026-08-12, mirrored in
            # dispatch_core.feed); fresh restart, once
            if (env["text"] == transcript[-2]["content"]
                    and not _restarted):
                print("    (repair reply byte-identical to the previous; "
                      "restarting dispatch fresh)")
                return self.call(user, validate, schema, _restarted=True)
        raise T.Phase1Error(f"call failed after {max_repairs} repair "
                            "round(s): " + "; ".join(str(e)
                                                     for e in errs[:5]))

    def _tally(self, env):
        u = (env.get("usage") or
             getattr(self.client, "last_usage", None) or {})
        cached = u.get("cached_input_tokens") or 0
        prompt = u.get("prompt_tokens") or 0
        self.cache_hits += cached
        self.cache_misses += max(prompt - cached, 0)

    # -- phases ------------------------------------------------------------
    def dispatch_block(self, phase, lo, hi, seeds, extra=""):
        return (f"YOUR DISPATCH\nPhase: {phase}\nSpan: lines {lo}-{hi}\n"
                f"Inherited seed vocabulary (fixed names):\n"
                f"{json.dumps(seeds, indent=1)}\n{extra}\n"
                f"Reply with ONE JSON object only.\n\n"
                f"THE SPAN, LINE-NUMBERED:\n{numbered(self.lines, lo, hi)}")

    def divide(self, lo, hi, seeds, wdir):
        art = os.path.join(wdir, "division.json")
        if os.path.exists(art):
            return json.load(open(art))
        extra = divide_extra()
        def _fix(o):
            if isinstance(o, dict):
                o["_span_lo"], o["_span_hi"] = lo, hi
            return autofix_division(o, seeds)
        d = self.call(self.dispatch_block("D", lo, hi, seeds, extra),
                      lambda o: validate_division(_fix(o), lo, hi, seeds),
                      schema=("division", DIVISION_SCHEMA))
        os.makedirs(wdir, exist_ok=True)
        write_json(art, d)
        return d

    def _health(self, g, lo, hi, kind, wdir, promises=None):
        """Golden-free build telemetry (Matt's Q3, 2026-08-11): the failure
        we shipped tonight was detectable WITHOUT a reference graph -- 969
        duplicate nodes, 5.3 nodes/line, and zero needs are all absolute
        signals. Metrics land in <out>/health.jsonl per artifact; warnings
        print immediately so a watcher (human or monitor) can stop early."""
        n = len(g.get("nodes", []))
        span = hi - lo + 1
        needs = sum(len(x.get("needs", [])) for x in g.get("nodes", []))
        unclaimed = sum(1 for u in g.get("uncovered", [])
                        if isinstance(u, dict) and str(u.get("reason", ""))
                        .startswith("unclaimed-content"))
        row = {"artifact": wdir, "kind": kind, "span": [lo, hi],
               "unclaimed": unclaimed,
               "nodes": n, "density": round(n / max(span, 1), 3),
               "needs": needs,
               "autofixes": g.get("driver_autofixes", [])}
        if promises is not None:
            row["broken_promises"] = promises
        with open(os.path.join(self.out, "health.jsonl"), "a") as f:
            f.write(json.dumps(row) + "\n")
        warns = []
        if n and needs == 0 and span > 80:
            warns.append("ZERO needs in a large span -- linkage may not be "
                         "transferring")
        if unclaimed:
            warns.append(f"{unclaimed} unclaimed content line(s) recorded "
                         f"(prerun review F3: watch the aggregate)")
        if row["density"] > 0.5:
            warns.append(f"density {row['density']}/line above healthy band")
        if promises:
            warns.append(f"division promised cross-link name(s) no child "
                         f"delivered: {promises} -- these will surface as "
                         f"danglings (or worse, silently vanish) at the root")
        for w in warns:
            print(f"  !! health [{wdir}]: {w}")

    def leaf(self, lo, hi, seeds, wdir):
        art = os.path.join(wdir, "graph.json")
        if os.path.exists(art):
            return json.load(open(art))
        extra, schema, derive = leaf_dispatch(lo, hi, self.cfg)   # D1 source
        g = self.call(self.dispatch_block("L", lo, hi, seeds, extra),
                      lambda o: validate_leaf(
                          o, lo, hi, self.lines, derive_uncovered=derive,
                          # item B: the seeds this dispatch inherited ARE
                          # its promise obligations when the flag is on
                          seeds=seeds,
                          enforce_promise_delivery=self.cfg.get(
                              "enforce_promise_delivery", False)),
                      schema=schema)
        os.makedirs(wdir, exist_ok=True)
        write_json(art, g)
        self._health(g, lo, hi, "leaf", wdir)
        return g

    def unwind(self, division, children, lo, hi, wdir, seeds=()):
        art = os.path.join(wdir, "graph.json")
        if os.path.exists(art):
            return json.load(open(art))
        (nodes, uncovered, provides, dangling, dup,
         user) = unwind_inputs(division, children, lo, hi, self.cfg)
        # Matt's architecture (restored 2026-08-11): the SAME instance that
        # divided later links. The divide exchange is deterministic + stored,
        # so the transcript is RECONSTRUCTED [D-user, D-reply, U-user]; the
        # prefix cache already holds brief+D-user from the divide call.
        if self.cfg.get("transcript_continuity"):
            user = continuity_transcript(self, division, lo, hi, seeds, user)
        dec = self.call(user, lambda o: apply_decisions(
            json.loads(json.dumps(nodes)),
            autofix_unwind_merges(o, nodes, provides, lo, hi, self.lines),
            provides, lo, hi, self.lines)[1],
            schema=unwind_schema(len(dangling), len(nodes),
                                 **enum_pools(self.cfg, nodes, provides,
                                              dangling)))
        meta = {}
        dec["resolutions"] = adjudicate_resolutions(
            self, dec.get("resolutions"), nodes, meta,
            context=f"unwind L{lo}-{hi}")
        log, errs = apply_decisions(nodes, dec, provides, lo, hi, self.lines)
        if errs:
            raise T.Phase1Error("unwind decision application failed: "
                                + "; ".join(errs[:5]))
        g = {"nodes": nodes, "uncovered": uncovered,
             "judgment_calls": dec.get("judgment_calls", []),
             "cross_link_report": dec.get("cross_link_report", []),
             "unwind_log": log, "brief_sha": self.brief_sha}
        g.update(meta)
        if dec.get("_dropped_merges"):
            g["dropped_merges"] = dec["_dropped_merges"]
        os.makedirs(wdir, exist_ok=True)
        write_json(art, g)
        self._health(g, lo, hi, "unwind", wdir,          # review F6
                     promises=broken_promises(division, children))
        return g

    # -- tree --------------------------------------------------------------
    def build(self, lo, hi, seeds, wdir, depth=0):
        if depth > DEPTH_MAX:
            raise T.Phase1Error(
                f"depth {depth} exceeds DEPTH_MAX at {lo}-{hi}; the divisions "
                f"leading here are cached -- delete {wdir} to re-divide")
        if (hi - lo + 1) <= self.leaf_max:
            try:
                return self.leaf(lo, hi, seeds, wdir)  # no Phase D needed
            except T.Phase1Error as exc:
                if "dense span" not in str(exc):
                    raise
                # Matt's ruling 2026-08-12: a leaf whose content overflows
                # the cap re-enters the NORMAL division path -- the same
                # machinery that handles every other big span, connectivity
                # covered by the ordinary unwind. Rejected by name: the D6
                # stages 2-3 mechanical boundary bisect (a second splitting
                # mechanism to test and trust, replaced by one we already
                # trust). A model that answers decision="leaf" here fails
                # loudly on the leaf redraw rather than looping.
                print(f"    (dense leaf {lo}-{hi}: recursing via Phase D)")
        d = self.divide(lo, hi, seeds, wdir)
        if d.get("decision") == "leaf":
            return self.leaf(lo, hi, seeds, wdir)
        kids = []
        for i, c in enumerate(d["children"], 1):
            clo, chi = c["span"]
            child_seeds = d.get("seed_vocabulary", [])
            kids.append(self.build(clo, chi, child_seeds,
                                   os.path.join(wdir, f"c{i}"), depth + 1))
        return self.unwind(d, kids, lo, hi, wdir, seeds)


# ------------------------------------------------------------- entry point
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(HERE,
                                                     "driver_config.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "runs", "ds1"))
    ap.add_argument("--doc")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--leaf-max", type=int)
    ap.add_argument("--yes", action="store_true",
                    help="required to spend money on a live run")
    ap.add_argument("--exec-mode", choices=["serial", "concurrent", "batch"],
                    help="execution core (dispatch_core.py); default serial "
                         "runs this file's reference path untouched")
    ap.add_argument("--golden", default=None,
                    help="golden graph path (overrides config golden_graph):"
                         " post_build_checks additionally runs the "
                         "deterministic quality instruments against it "
                         "(graph_compare, repair_census, edge similarity). "
                         "Offline, $0.")
    args = ap.parse_args()
    cfg = json.load(open(args.config))
    if args.leaf_max:
        cfg["leaf_max_lines"] = args.leaf_max
    doc = args.doc or os.path.join(PHASE1, "..", "..", "..",
                                   cfg["doc_path"])
    lines = load_doc(doc)
    lo, hi = 1, len(lines)

    brief = open(BRIEF_PATH).read()
    # WORST-CASE estimate (review F1/F2): effective leaf size, DEPTH_MAX
    # document passes, full max_tokens output, and a repair retry on every
    # call (which re-sends the prompt plus the failed completion). Billed at
    # the full input rate -- no cache credit claimed. Overstating is
    # survivable; understating is how a hard cap gets passed.
    cpt = 3.5                       # chars/token, same source as config.json
    leaf_max = cfg.get("leaf_max_lines", LEAF_MAX_LINES)
    doc_toks = sum(len(l) + 8 for l in lines) / cpt
    brief_toks = len(brief) / cpt
    max_out = cfg["model"].get("max_tokens", 16384)
    n_leaves = max(1, -(-len(lines) // leaf_max))
    est_calls = n_leaves + 2 * max(1, n_leaves // 2)     # leaves + D&U layers
    retries = 2                                          # every call repaired
    in_toks = (doc_toks * DEPTH_MAX + brief_toks * est_calls
               + est_calls * max_out) * retries / 2 * 2
    out_toks = est_calls * max_out * retries
    pin, pout = cfg["price_per_mtok"]
    est = in_toks / 1e6 * pin + out_toks / 1e6 * pout
    expected = est / 6              # typical run: no repairs, shallow depth
    print(f"plan: {len(lines)} lines, leaf_max {leaf_max}, up to "
          f"~{est_calls * retries} calls; expected ~${expected:.2f}, "
          f"worst-case ceiling ~${est:.2f} ({cfg['model']['model']})")
    ceiling = cfg.get("cost", {}).get("max_cost_usd")
    if ceiling and est > ceiling:
        print(f"  ⚠️ worst case exceeds cost.max_cost_usd ${ceiling:.2f}; "
              f"the run aborts at the ceiling on MEASURED spend")
    if args.dry_run:
        return

    # resume fingerprint (review F3): artifacts are only reusable under the
    # same brief, document, model, and leaf size
    meta = {"brief_sha": sha16(brief),
            "doc_sha": sha16("\n".join(lines)),
            "model": cfg["model"]["model"], "leaf_max_lines": leaf_max}
    meta_path = os.path.join(args.out, "run_meta.json")
    if os.path.exists(meta_path):
        old = json.load(open(meta_path))
        diff = {k: (old.get(k), v) for k, v in meta.items()
                if old.get(k) != v}
        if diff:    # compare FINGERPRINT fields only: a stored artifact may
                    # carry extra keys (e.g. a documented migration note)
            print(f"refusing to resume: run_meta mismatch {diff}\n"
                  f"use a fresh --out (or delete {args.out} to rebuild)")
            sys.exit(2)
    else:
        os.makedirs(args.out, exist_ok=True)
        write_json(meta_path, meta)

    if args.mock:
        client = MockClient(json.load(open(
            os.path.join(HERE, "mock_replies.json"))))
    else:
        if not args.yes:
            print("refusing to spend without --yes"); sys.exit(2)
        prov = T.Provider(
            name="graph-build", kind="openai-compatible",
            model=cfg["model"]["model"], base_url=cfg["model"]["base_url"],
            api_key_env=cfg["model"]["api_key_env"],
            temperature=cfg["model"].get("temperature", 0.0),
            max_tokens=cfg["model"].get("max_tokens", 16384),
            price_per_mtok=cfg["price_per_mtok"])
        client = GraphClient(prov, {"model": dict(
            cfg["model"], format_forcing="json_object",
            usage_log=cfg["model"].get("usage_log", "DEFAULT"))})
        client.max_cost_usd = cfg.get("cost", {}).get("max_cost_usd")

    drv = Driver(cfg, client, lines, args.out)
    t0 = time.time()
    mode = args.exec_mode or cfg.get("execution", {}).get("mode", "serial")
    if mode == "concurrent" and cfg.get("rename_seat"):
        # pre-ds7 review finding 4: the seat's schema_slot writes the
        # one-slot client grammar OUTSIDE _body_lock -- a worker's leaf
        # body can ship with the verdict grammar. Refuse loudly until the
        # slot is thread-safe; batch and serial are unaffected.
        raise T.Phase1Error(
            "rename_seat + concurrent executor is a known schema-slot "
            "race (pre-ds7 review finding 4): use --exec-mode batch or "
            "serial, or disable rename_seat")
    if mode != "serial":
        # shared execution core (dispatch_core.py): same dispatches, same
        # artifacts, scheduled through the ready-queue design instead of
        # this file's recursion (BATCH_DESIGN.md post-review resolution)
        import dispatch_core
        g = dispatch_core.run_build(drv, lo, hi, cfg.get("root_seeds", []),
                                    args.out, mode)
    else:
        g = drv.build(lo, hi, cfg.get("root_seeds", []), args.out)
    dt = time.time() - t0
    total = drv.cache_hits + drv.cache_misses
    rate = drv.cache_hits / total if total else 0.0
    print(f"done: {len(g['nodes'])} nodes in {dt:.0f}s, "
          f"{client.calls} calls, ${getattr(client, 'spent_usd', 0):.4f} "
          f"measured, cache hit rate {rate:.0%} "
          f"({drv.cache_hits}/{total} prompt tokens)")
    g = run_resolution_pass(drv, g, args.out)
    write_json(os.path.join(args.out, "root_graph.json"), g)
    # item 14 (Matt 2026-08-14): deterministic golden-quality checks are a
    # FLAG -- CLI --golden wins, config golden_graph is the standing value;
    # relative paths resolve against this file's directory
    golden = args.golden or cfg.get("golden_graph")
    if golden and not os.path.isabs(golden):
        golden = os.path.join(HERE, golden)
    post_build_checks(args.out, golden=golden, doc_path=doc)
    if not args.mock:
        T.spend_invisibility_warning(client.p, client.spent_usd,
                                     client.calls)


def resolution_pass_user(dangling, nodes):
    """THE dedicated resolution-pass prompt -- verified 2026-08-11
    (115/119 resolved, $0.007). Deliberately OPPOSITE emphasis to the
    unwind's anti-grind contract: v1 borrowed that contract and resolved
    ZERO. Single source; resolve_pass.py and the post-build stage share it."""
    summaries = [{"id": n["id"], "establishes": n.get("establishes", ""),
                  "provides": [{"name": nm(p), "prose": p.get("prose", "")
                                if isinstance(p, dict) else ""}
                               for p in n.get("provides", [])]}
                 for n in nodes if n.get("provides")]
    return ("YOUR DISPATCH\nPhase: RESOLUTION PASS\n"
            "Your ONLY job: connect the DANGLING NEEDS below to providers "
            "that already exist in this graph. A dangling need and a "
            "provides entry describing the SAME concept in different words "
            "should be connected by renaming the need to the provider's "
            "exact name (judge on the prose MEANING, never name "
            "similarity). Be thorough: most of these danglings DO have a "
            "matching provider under a different name. Only leave a need "
            "dangling if NO provider's prose describes its concept. "
            "CANDIDATES below are lexical suggestions ONLY (the true "
            "provider is absent ~1 in 10 -- scan all providers).\n"
            f"DANGLING NEEDS:\n{json.dumps(dangling, indent=1)}\n"
            f"CANDIDATES:\n"
            f"{json.dumps(rename_candidates(dangling, nodes), indent=1)}\n"
            f"ALL PROVIDERS:\n{json.dumps(summaries, indent=1)}\n"
            "Reply with ONE JSON object: {\"resolutions\": [{\"needer\", "
            "\"name\", \"rename_to\" (an existing provided name)}], "
            "\"merges\": [], \"structure_nodes\": [], "
            "\"judgment_calls\": [...max 10, decision classes only]}")


EMBED_MODEL = "intfloat/multilingual-e5-large-instruct"


def _embed_texts(texts, api_key):
    """Embedding vectors via curl (together's WAF 403s stdlib urllib).
    Returns None on ANY failure -- the descend is an optional recall
    booster and must never break a finished build."""
    import subprocess
    import tempfile
    out = []
    try:
        for i in range(0, len(texts), 64):
            body = json.dumps({"model": EMBED_MODEL,
                               "input": texts[i:i + 64]}).encode()
            with tempfile.NamedTemporaryFile("wb", suffix=".json",
                                             delete=False) as tf:
                tf.write(body)
                name = tf.name
            try:
                p = subprocess.run(
                    ["curl", "-sS",
                     "https://api.together.xyz/v1/embeddings",
                     "-H", "Authorization: Bearer " + api_key,
                     "-H", "Content-Type: application/json",
                     "--data-binary", "@" + name],
                    capture_output=True, text=True, timeout=180)
            finally:
                os.unlink(name)          # review finding 6: no temp leak
            r = json.loads(p.stdout)
            out += [d["embedding"] for d in r["data"]]
        return out
    except Exception:                            # noqa: BLE001
        return None


def greedy_rename_descend(drv, g, record):
    """Recall booster (Matt-approved architecture, 2026-08-13): for each
    dangling that SURVIVES the pass, rank all providers by embedding
    cosine on enriched prose (measured 82% recall@10 on golden; the
    canonical-card variant measured WORSE and was declined), walk the top
    5 through the rename seat, apply the first same_concept verdict.
    Below-threshold danglings keep their ranked near-misses on the
    artifact for the risk queue. Skipped cleanly (recorded) when
    embeddings or the seat are unavailable."""
    if not (drv.cfg.get("greedy_rename_descend")
            and drv.cfg.get("rename_seat")):
        return
    import rename_seat as RS
    nodes = g["nodes"]
    provides = {}
    prov_prose, prov_node = {}, {}
    for n in nodes:
        for p in n.get("provides", []):
            provides.setdefault(nm(p), []).append(n["id"])
            if isinstance(p, dict):
                prov_prose.setdefault(p["name"], p.get("prose", ""))
                prov_node.setdefault(p["name"], n)
    dangling, _seen_pairs = [], set()
    for n in nodes:
        for d in n.get("needs", []):
            # DEDUPE on (needer, name) -- pre-ds7 review finding 2
            # (repro'd): a node with two same-named dangling needs would
            # yield two accepted entries, the second of which errors
            # "matched no needs entry" and kills the finished build.
            # apply_decisions renames every matching entry at once, so
            # one resolution per pair is both sufficient and safe.
            if (isinstance(d, dict) and nm(d) not in provides
                    and (n["id"], nm(d)) not in _seen_pairs):
                _seen_pairs.add((n["id"], nm(d)))
                dangling.append((n, d))
    if not dangling:
        return
    cands = sorted(prov_prose)
    key = getattr(drv.client, "key", None) or os.environ.get(
        "TOGETHER_API_KEY", "")
    ctexts = [prov_prose[c] + " || " + prov_node[c].get("establishes", "")
              for c in cands]
    qtexts = [(d.get("prose", "") + " || " + n.get("establishes", ""))
              for n, d in dangling]
    vecs = _embed_texts(ctexts + qtexts, key)
    if vecs is None:
        record.setdefault("driver_autofixes", []).append(
            "greedy descend SKIPPED: embedding call failed (danglings "
            "stay; rerun the pass to retry)")
        return
    import math

    def cos(a, b):
        d = sum(x * y for x, y in zip(a, b))
        return d / (math.sqrt(sum(x * x for x in a))
                    * math.sqrt(sum(x * x for x in b)) + 1e-9)
    cvecs, qvecs = vecs[:len(cands)], vecs[len(cands):]
    accepted = []
    seen_verdicts = {}
    # hard call cap (finding 1): the pre-registered call band is now a
    # MECHANISM -- past the cap, remaining danglings stay honest with
    # their ranked candidates recorded, and the run says so
    budget_calls = int(drv.cfg.get("descend_max_calls", 600))
    calls_made = 0
    for (n, d), qv in zip(dangling, qvecs):
        ranked = sorted(((cos(qv, cv), c) for cv, c in zip(cvecs, cands)),
                        reverse=True)[:5]
        hit = None
        if calls_made >= budget_calls:
            record.setdefault("descend_near_misses", []).append(
                {"needer": n["id"], "name": nm(d), "capped": True,
                 "candidates": [{"name": c, "sim": round(s, 3)}
                                for s, c in ranked]})
            continue
        for s, cand in ranked:
            vk = (d.get("prose", ""), cand)
            if vk in seen_verdicts:
                v = seen_verdicts[vk]
            else:
                calls_made += 1
                prompt = RS.build_prompt(d.get("prose", ""), n,
                                         prov_prose.get(cand, ""),
                                         prov_node.get(cand), drv.lines)
                slot = (lambda sch: setattr(drv.client, "reply_schema",
                                            sch)) \
                    if hasattr(drv.client, "reply_schema") else None
                v = RS.judge(drv.client.complete, prompt, schema_slot=slot)
                seen_verdicts[vk] = v
                record.setdefault("rename_seat_verdicts", []).append(
                    {"proposal": {"needer": n["id"], "name": nm(d),
                                  "rename_to": cand},
                     "verdict": v["verdict"], "grounds": v["grounds"],
                     "where": "greedy descend"})
            if v["verdict"] == "same_concept":
                hit = cand
                break
        if hit:
            accepted.append({"needer": n["id"], "name": nm(d),
                             "rename_to": hit})
        else:
            record.setdefault("descend_near_misses", []).append(
                {"needer": n["id"], "name": nm(d),
                 "candidates": [{"name": c, "sim": round(s, 3)}
                                for s, c in ranked]})
    if hasattr(drv.client, "reply_schema"):
        drv.client.reply_schema = None
    if accepted:
        log, errs = apply_decisions(nodes, {"resolutions": accepted},
                                    provides)
        if errs:
            raise T.Phase1Error("greedy descend application failed: "
                                + "; ".join(str(e) for e in errs[:5]))
        record.setdefault("driver_autofixes", []).append(
            f"greedy descend: {len(accepted)} seat-confirmed rename(s) "
            f"of {len(dangling)} dangling(s)")
    print(f"  greedy descend: {len(accepted)}/{len(dangling)} danglings "
          f"seat-confirmed")


def adjudicate_resolutions(drv, resolutions, nodes, record, context=""):
    """THE one choke point every proposed rename passes through (Matt's
    2026-08-13 ruling: renames are adjudicated WHEREVER proposed -- unwind
    or final pass; ds6 measured 417 unadjudicated unwind renames at 31%
    mismatch). Gate prefilter (>=0.25 prose sim auto-accepts), rename seat
    on the rest; verdicts + gate notes land on `record`. Returns the
    accepted list; everything else stays dangling honestly."""
    prov_prose, prov_node = {}, {}
    by_id = {n["id"]: n for n in nodes}
    for n in nodes:
        for p in n.get("provides", []):
            if isinstance(p, dict):
                prov_prose.setdefault(p["name"], p.get("prose", ""))
                prov_node.setdefault(p["name"], n)
    need_prose = {}
    for n in nodes:
        for d in n.get("needs", []):
            if isinstance(d, dict):
                need_prose.setdefault((n["id"], d.get("name")),
                                      d.get("prose", ""))

    def _sim(a, b):
        ta = {w for w in re.findall(r"[a-z]{4,}", (a or "").lower())}
        tb = {w for w in re.findall(r"[a-z]{4,}", (b or "").lower())}
        return len(ta & tb) / max(len(ta | tb), 1)

    kept, gated = [], []
    for r in resolutions or []:
        if not isinstance(r, dict):
            continue
        np = need_prose.get((r.get("needer"), r.get("name")), "")
        pp = prov_prose.get(r.get("rename_to") or r.get("name"), "")
        if _sim(np, pp) >= 0.25:
            kept.append(r)
            # gate passes are RECORDED (pre-ds7 review finding 5: the
            # acceptance criterion "every applied rename carries a
            # verdict or gate pass ON THE ARTIFACT" was unverifiable)
            record.setdefault("rename_seat_verdicts", []).append(
                {"proposal": r, "verdict": "gate_pass",
                 "grounds": f"prose similarity >= 0.25",
                 "where": context})
        else:
            gated.append(r)
    if gated and drv.cfg.get("rename_seat"):
        import rename_seat as RS
        still = []
        for r in gated:
            name = r.get("rename_to") or r.get("name")
            prompt = RS.build_prompt(
                need_prose.get((r.get("needer"), r.get("name")), ""),
                by_id.get(r.get("needer")),
                prov_prose.get(name, ""), prov_node.get(name), drv.lines)
            slot = (lambda sch: setattr(drv.client, "reply_schema", sch)) \
                if hasattr(drv.client, "reply_schema") else None
            v = RS.judge(drv.client.complete, prompt, schema_slot=slot)
            record.setdefault("rename_seat_verdicts", []).append(
                {"proposal": r, "verdict": v["verdict"],
                 "grounds": v["grounds"], "where": context})
            (kept if v["verdict"] == "same_concept" else still).append(r)
        gated = still
        if hasattr(drv.client, "reply_schema"):
            drv.client.reply_schema = None    # review finding 5
    if gated:
        record.setdefault("driver_autofixes", []).append(
            f"{context or 'resolution pass'}: {len(gated)} rename(s) "
            f"gated, left dangling")
    return kept


def run_resolution_pass(drv, g, out_dir):
    """Post-build stage (Matt-approved integration 2026-08-11): resolve
    the finished graph's danglings as a dedicated pass. Applies to the
    graph IN PLACE with a backup; genuine danglings survive."""
    nodes = g["nodes"]
    provides = {}
    for n in nodes:
        for p in n.get("provides", []):
            provides.setdefault(nm(p), []).append(n["id"])
    dangling = [{"needer": n["id"], "name": nm(d),
                 "prose": d.get("prose", "") if isinstance(d, dict) else ""}
                for n in nodes for d in n.get("needs", [])
                if nm(d) not in provides]
    if not dangling:
        print("resolution pass: no danglings")
        return g
    user = resolution_pass_user(dangling, nodes)
    stripped = []

    def _resolutions_only(o):
        # delta review D3: apply_decisions with lo=hi=lines=None skips
        # leaf-grade structure-node validation but still APPENDS -- a
        # hallucinated node (span outside the document, fabricated quote)
        # sailed into the final graph (probe P6), and a merge here would
        # run with no unwind context. The grammar (resolution_schema) caps
        # both at 0, but strict=False means a model can still emit them:
        # STRIP, never apply -- this pass's only job is resolutions, so a
        # stripped entry carries nothing the pass may add.
        if isinstance(o, dict) and (o.get("merges")
                                    or o.get("structure_nodes")):
            stripped[:] = [
                f"resolution pass: stripped {len(o.get('merges') or [])} "
                f"merge(s) + {len(o.get('structure_nodes') or [])} "
                f"structure_node(s) -- this pass admits resolutions ONLY"]
            o["merges"], o["structure_nodes"] = [], []
        return o

    dec = drv.call(user, lambda o: apply_decisions(
        json.loads(json.dumps(nodes)), _resolutions_only(o), provides)[1],
        schema=resolution_schema(len(dangling), len(nodes),
                                 **enum_pools(drv.cfg, nodes, provides,
                                              dangling)))
    # ds4_divergence_analysis.md 2026-08-12: ungated, this pass renamed
    # stay_in_bounds_content_categories -> content_definition and attached
    # 38 edges to the WRONG concept. The shared choke point (gate prefilter
    # + rename seat, Matt's option c) now filters here AND at both unwind
    # sites -- absence > wrong, everywhere a rename is proposed.
    dec["resolutions"] = adjudicate_resolutions(
        drv, dec.get("resolutions"), nodes, g, context="resolution pass")
    shutil_path = os.path.join(out_dir, "root_graph.pre_resolution.json")
    write_json(shutil_path, g)
    log, errs = apply_decisions(nodes, dec, provides)
    if errs:
        # D3 secondary: the real apply's errors were silently discarded --
        # deterministically empty today (validate ran the same call on a
        # deep copy) but one refactor from a masked failure. Loud, always.
        raise T.Phase1Error("resolution pass application failed: "
                            + "; ".join(str(e) for e in errs[:5]))
    for line in stripped:
        print("  " + line)
        g.setdefault("driver_autofixes", []).append(line)
    g.setdefault("driver_autofixes", []).append(
        f"resolution pass: {len([l for l in log if l.startswith('resolved')])}"
        f" resolved, {len(dangling)} danglings before")
    print(f"resolution pass: {len(log)} actions on {len(dangling)} danglings")
    greedy_rename_descend(drv, g, g)
    return g


def edge_similarity_report(g, out_path):
    """Name-prose similarity histogram over every surviving edge (Matt's
    directive 2026-08-14, item 14c): token-Jaccard between each need's
    prose and its provider's prose -- the recorded probe arithmetic
    (risk_queue.sim is THE one source, imported not copied) -- bucketed
    <0.1 / 0.1-0.25 / >=0.25. Offline, deterministic."""
    import risk_queue as RQ
    prov_prose = {}
    for n in g.get("nodes", []):
        for p in n.get("provides", []):
            if isinstance(p, dict):
                prov_prose.setdefault(p["name"], p.get("prose", ""))
    buckets = {"lt_0.10": 0, "0.10_0.25": 0, "gte_0.25": 0}
    low = []
    total = 0
    for n in g.get("nodes", []):
        for d in n.get("needs", []):
            if not isinstance(d, dict):
                continue
            pp = prov_prose.get(d.get("name"))
            if pp is None:
                continue                    # dangling: no edge to score
            total += 1
            s = RQ.sim(d.get("prose", ""), pp)
            if s < 0.1:
                buckets["lt_0.10"] += 1
                low.append({"needer": n.get("id"), "name": d.get("name"),
                            "sim": round(s, 3)})
            elif s < 0.25:
                buckets["0.10_0.25"] += 1
            else:
                buckets["gte_0.25"] += 1
    out = {"total_edges": total, "buckets": buckets, "low_sim_edges": low}
    write_json(out_path, out)
    return out


def post_build_checks(out_dir, golden=None, doc_path=None):
    """Auto-run the mechanical quality instruments on the finished graph
    (Matt's ruling 2026-08-10: detection is built into the pipeline, no
    separate step). graph_check = hard mechanical defects; the two sweeps =
    adjudication CANDIDATES (the Haiku golden's repair loop starts from
    these reports). All output lands in the run dir.

    `golden` (Matt's directive 2026-08-14, item 14: config `golden_graph`
    or --golden) additionally runs the deterministic quality instruments:
    graph_compare against the golden, repair_census over this run, and the
    edge name-prose similarity histogram. All offline, $0."""
    import subprocess
    gp = os.path.join(out_dir, "root_graph.json")
    if not os.path.exists(gp):
        print("post-build checks skipped: no root_graph.json")
        return
    jobs = [
        ("graph_check", [sys.executable,
                         os.path.join(HERE, "graph_check.py"), gp]),
        ("sweep_modals", [sys.executable,
                          os.path.join(HERE, "sweep_modals.py"),
                          "--graph", gp, "--report",
                          os.path.join(out_dir, "sweep_modals_report.json")]),
        ("sweep_headings", [sys.executable,
                            os.path.join(HERE, "sweep_headings.py"),
                            "--graph", gp, "--report",
                            os.path.join(out_dir,
                                         "sweep_headings_report.json")]),
        # Matt's frontier-dispatch design (2026-08-13, wired per pre-ds7
        # review finding 8c): every build emits its ranked review queue
        ("risk_queue", [sys.executable,
                        os.path.join(HERE, "risk_queue.py"), out_dir]),
    ]
    if golden:
        cmd = [sys.executable, os.path.join(HERE, "graph_compare.py"),
               "--a", golden, "--b", gp,
               "--out", os.path.join(out_dir, "compare_vs_golden.json")]
        if doc_path:
            cmd += ["--doc", doc_path]
        jobs.append(("compare_vs_golden", cmd))
        jobs.append(("repair_census", [sys.executable,
                                       os.path.join(HERE,
                                                    "repair_census.py"),
                                       out_dir]))
    print("---- post-build checks " + "-" * 40)
    for name, cmd in jobs:
        r = subprocess.run(cmd, capture_output=True, text=True)
        blob = r.stdout + r.stderr
        with open(os.path.join(out_dir, f"postbuild_{name}.txt"), "w") as f:
            f.write(blob)
        head = "; ".join(l for l in blob.splitlines()
                         if l.strip())[:160] or f"(exit {r.returncode})"
        flag = "OK " if r.returncode == 0 else "!! "
        print(f"  {flag}{name}: {head}")
    if golden:
        rep = edge_similarity_report(
            json.load(open(gp)),
            os.path.join(out_dir, "edge_similarity.json"))
        b = rep["buckets"]
        print(f"  OK edge_similarity: {rep['total_edges']} edge(s) -- "
              f"<0.1: {b['lt_0.10']}, 0.1-0.25: {b['0.10_0.25']}, "
              f">=0.25: {b['gte_0.25']}")
    print("  full reports in", out_dir)


if __name__ == "__main__":
    main()
