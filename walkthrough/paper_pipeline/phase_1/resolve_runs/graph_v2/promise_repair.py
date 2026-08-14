#!/usr/bin/env python3
"""Promise-repair stage (item A, Matt 2026-08-14; scope extended per the
k3_validity_report + delta_investigation): targeted regeneration of a
run's missing provides exports, in TWO classes:

  (a) PROMISE breaks -- <run>/fixup_queue.json broken_promise items the
      frontier rejected (note: the ds7 first-slice K3 "confirmations" of
      this kind were evidence-free defaults, k3_validity_report; the
      class stands on the division's own recorded promise, not on them);
  (b) UNDER-EXPORT -- the deterministic scan over the root graph's
      danglings (delta_investigation cause 3, ds7's one real defect: 92
      exported provides names vs the golden's 230): a dangling need whose
      establishing content already EXISTS as a node -- establishes-prose
      token overlap >= 0.25 with the need prose, or spans containing the
      name's seeded established_around -- becomes a repair candidate
      aimed at that node, with the SAME must-provide-or-explain redraw
      and the same decline path.

Input: <run>/fixup_queue.json, the run's root_graph.json, and its cached
division/leaf artifacts. For each item:

  1. locate the promised name's seed entry (name + prose +
     established_around) in the responsible division.json;
  2. descend the cached division tree to the LEAF whose span covers
     established_around;
  3. re-dispatch THAT LEAF ONLY (Driver.leaf semantics: the same prompt
     via leaf_dispatch/dispatch_block, the same validators including
     coverage and coinage, PLUS an appended promise instruction and the
     item-B promise-delivery enforcement with its judgment_calls escape
     hatch) into a scratch dir under <run>/promise_repair/;
  4. MERGE mechanically: if the redraw provides the promised name at the
     establishment lines, splice ONLY the new provides entry (and any new
     needs the validator accepted) onto the existing node(s) covering
     those lines in a COPY of the graph -> <run>/root_graph.repaired.json
     (never in place; a provenance note per repair rides in the artifact
     and a summary line in health.jsonl). If the redraw DECLINES (a
     judgment_calls reason naming the seed), the promise is recorded as
     honestly-undeliverable in <run>/promise_repair_report.json.

PREP GUARDS (2026-08-14, ruling in EXPERIMENTS "OPUS RECHECK"; grounds in
opus_recheck_report.md -- the stage does NOT run until prep has all
three, because 5/9 promise plans and 1 under-export plan were misaimed):

  1. SAME-REFERENT already-provided (`skipped_same_referent`) -- the
     exact-name filter extended to the referent: an existing provides
     entry whose prose overlaps the seed's by >= 0.5 tokens
     (risk_queue.sim) or contains it verbatim already exports the
     concept, so a redraw would duplicate it
     (authority_level_ordering -> authority_levels_hierarchy).
  2. CITATION-SITE re-aim -- an established_around line that CITES the
     seed's own anchor (`see [?](#avoid_overstepping)`) is not an
     establishment site; the plan is re-derived from that anchor's own
     section heading (ea 1422 -> L3239), or skipped
     (`skipped_citation_site_unresolved`) when the document has no such
     heading.
  3. SECTION-HEADING fallback -- a seed with no usable
     established_around (the `*_section` names) derives one by slugging
     its own name and locating that section's heading
     (refusal_style_section -> #refusal_style at L4073).

THE SPLICE SEAT (2026-08-14, repaired_verification.md): every guard
above answers WHERE to aim a splice; NONE asked whether the receiving
node's content ESTABLISHES the concept, and 4 of ds7's 26 splices were
wrong claims (one asserting the NEGATION of the document's principle).
`splice_seat.py` adjudicates concept prose vs the receiving node,
BLIND ON THE NAME, as the last gate before the graph is touched --
`rejected_by_splice_seat` rows carry the grounds and change nothing.
Config `promise_repair.splice_seat` DEFAULTS TO TRUE (a correctness
gate, not a flag); the calls ride the stage's own client and budget.

Two smaller findings from the same verification, both mechanical:
NARRATION MISMATCH -- a redraw whose judgment_calls reason says it will
add the entry and then does not is booked `narration_mismatch` and
counted as a FAILED repair, never as an honest decline; and SELF-LOOPS
-- a receiving node's need for the name it now provides is dropped (a
node cannot depend on itself), with a graph-level self-loop census in
the report.

Optional config `promise_repair.opus_verdicts` (a path; absent by
default and then behaviour is unchanged): intersects the broken_promise
rows with that file's `opus_decision == "reject"` names, so the repair
scope is the evidence-confirmed set rather than the reject-default queue.

The danglings computation re-runs after all repairs and the report says
how many needers resolved. The stage is budget-gated up front
(promise_repair.max_cost_usd, default 0.25 -- ~40 leaf redraws at ~$0.002)
and requires --yes: it spends real money.

    python promise_repair.py runs/ds7 --yes
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (PHASE1, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import translate as T          # noqa: E402
import recurse_driver as R     # noqa: E402
import splice_seat as SS       # noqa: E402
import run_checkpoint as CK    # noqa: E402

DEFAULT_BUDGET = 0.40    # matches config (re-review 5 + final 1c note)


def _safe(s):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s or "x")


def broken_promises_to_repair(run_dir):
    """The frontier-confirmed queue rows this stage owns."""
    q = json.load(open(os.path.join(run_dir, "fixup_queue.json")))
    return [it for it in q.get("items", [])
            if it.get("kind") == "broken_promise"
            and it.get("verdict") == "reject"]


def opus_confirmed_names(path):
    """The evidence-confirmed defect names from an `opus_verdicts` file
    (opus_recheck.json shape: rows with kind / detail / opus_decision).

    Ruling (EXPERIMENTS 2026-08-14, OPUS RECHECK): the repair scope is the
    14 evidence-confirmed broken promises, not the 45 reject-default queue
    rows. A `reject` from the evidence recheck means "the promise really
    is broken"; `uphold` means the concept is in the graph already. This
    file NEVER invents a verdict -- it only intersects, and the key is
    optional so an absent config leaves behaviour byte-identical."""
    d = json.load(open(path))
    rows = d.get("items", []) if isinstance(d, dict) else (d or [])
    return {(r.get("detail") or {}).get("name") for r in rows
            if isinstance(r, dict) and r.get("kind") == "broken_promise"
            and r.get("opus_decision") == "reject"
            and (r.get("detail") or {}).get("name")}


# ---------------------------------------------------------------- guards
#: a markdown cross-reference: `[?](#anchor)`, `[overstepping](#anchor)`.
XREF_RE = re.compile(r"\[[^\]\n]*\]\(#([A-Za-z0-9_-]+)\)")
#: a section heading carrying its own anchor: `## Title {#slug authority=x}`
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+.*\{#([A-Za-z0-9_-]+)[ }]")


def concept_slug(name):
    """The document anchor a seed name refers to. The graph's own naming
    convention appends `_section` to a seed that names a whole section
    (`refusal_style_section` -> `#refusal_style`); everything else is
    already the slug. GENERAL -- no name is hardcoded anywhere."""
    name = name or ""
    return name[:-len("_section")] if name.endswith("_section") else name


def heading_line_for_slug(lines, slug):
    """1-based line number of the section HEADING that owns `slug`, or
    None. First match wins (a document has one heading per anchor)."""
    if not slug:
        return None
    for i, ln in enumerate(lines or (), 1):
        m = HEADING_RE.match(ln or "")
        if m and m.group(1) == slug:
            return i
    return None


def is_citation_site(lines, line_no, name):
    """GUARD 2 test: the document line at `line_no` CITES the seed's own
    concept (`... see [?](#refusal_style) ...`) instead of establishing
    it. Real ds7 cases (opus_recheck_report §4): avoid_overstepping ea
    1422 cites `(#avoid_overstepping)` whose section is L3239;
    sexual_content_involving_minors_section ea 4576 cites the U18
    section's pointer at the prohibition established at L826.

    Deliberately NARROW: the cross-reference must name the SEED's own
    slug. A line that merely happens to cite some other section still
    counts as an establishment site -- this file must not make a content
    judgment about which of several anchors a passage is "really" about."""
    if not lines or not isinstance(line_no, int):
        return False
    if not 1 <= line_no <= len(lines):
        return False
    ln = lines[line_no - 1] or ""
    if HEADING_RE.match(ln):
        return False          # the heading itself IS the establishment
    return concept_slug(name) in set(XREF_RE.findall(ln))


#: cap on a re-derived section body (convergence review B2a). A heading
#: whose section runs longer than this is truncated: the establishment of
#: a section's substance is at its top, and an uncapped range would let
#: max-overlap ranking reach halfway across the document.
SECTION_MAX_LINES = 120


def heading_level(line):
    """Markdown depth of an anchored heading line, or None."""
    if not HEADING_RE.match(line or ""):
        return None
    return len((line or "").lstrip()) - len((line or "").lstrip().lstrip("#"))


def section_span(lines, heading_line, cap=SECTION_MAX_LINES):
    """The BODY of the section a heading opens: [heading, last line before
    the next heading of the same-or-higher level], capped at `cap`.

    Convergence review B2a: a bare [heading, heading] establishment made
    `_select_target` pick whatever node's span IS the heading line -- in
    this graph the authority-ASSIGNMENT node ("Rules in the #X section
    carry Y authority"), never the node establishing the section's
    substance. A body range lets the selector see the substantive nodes,
    and -- just as important -- EXCLUDES the commentary node two lines
    ABOVE the heading that graph order was handing back (risk_taxonomy
    heading 53 was selecting L1-170_n032 at line 51)."""
    if not lines or not heading_line:
        return None
    lvl = heading_level(lines[heading_line - 1]) or 6
    end = min(len(lines), heading_line + cap - 1)
    for i in range(heading_line + 1, min(len(lines), heading_line + cap)):
        h = heading_level(lines[i - 1])
        if h is not None and h <= lvl:
            end = i - 1
            break
    return [heading_line, max(heading_line, end)]


def resolve_establishment(seed, lines):
    """THE ONE establishment-line resolver -- guards 2 and 3 both live
    here, and BOTH plan classes call it (the coherence lesson: two
    resolution rules drift).

    Returns (ea, kind, why):
      * (ea, None, None)                     -- the seed's own ea stands;
      * (ea, "reaimed_citation_site", why)   -- guard 2: the ea line cited
        the concept; ea re-derived from the anchor's own SECTION BODY;
      * (None, "skipped_citation_site_unresolved", why) -- guard 2 with no
        heading for the slug: the plan is dropped, unpaid;
      * (ea, "section_heading_fallback", why) -- guard 3: no usable ea at
        all, so the seed name's slug locates the section body;
      * (None, "no_establishment", None)     -- guard 3 found no heading
        either; the caller keeps its existing failure path.

    A re-derived ea is a section BODY range, never the bare heading line
    (review B2a); callers mark those plans `section=True` so the ONE
    selector ranks them in section mode."""
    name = seed.get("name") or ""
    ea = seed.get("established_around")
    usable = isinstance(ea, (list, tuple)) and len(ea) >= 2
    if not usable:
        # GUARD 3 (opus_recheck_report §4 "Confirmed defects with NO
        # plan": control_side_effects_section, risk_taxonomy_section,
        # red_line_principles_section, refusal_style_section all failed
        # prep with "no usable established_around")
        hl = heading_line_for_slug(lines, concept_slug(name))
        if hl is None:
            return None, "no_establishment", None
        body = section_span(lines, hl)
        return body, "section_heading_fallback", (
            f"seed '{name}' carries no established_around; the section "
            f"#{concept_slug(name)} opens at line {hl} and its body runs "
            f"{body}")
    if not is_citation_site(lines, ea[0], name):
        return list(ea[:2]), None, None
    # GUARD 2
    slug = concept_slug(name)
    hl = heading_line_for_slug(lines, slug)
    if hl is None:
        return None, "skipped_citation_site_unresolved", (
            f"established_around {list(ea[:2])} is a cross-reference to "
            f"#{slug}, not an establishment site, and no section heading "
            f"in the document carries that anchor")
    body = section_span(lines, hl)
    return body, "reaimed_citation_site", (
        f"established_around {list(ea[:2])} cites #{slug}; re-aimed at "
        f"that section, which opens at line {hl} with body {body}")


def _norm_prose(s):
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def same_referent_provider(prose, g, ea, threshold=0.5, tol=2):
    """GUARD 1: an EXISTING provides entry that already exports this
    referent under a different NAME. Returns
    (name, node_id, how, score) or None.

    Two admissible signals (opus_recheck_report §2b, 15 of the 29 flipped
    items): >= `threshold` token overlap between the seed prose and the
    existing entry's prose -- scored by `risk_queue.sim`, THE one source,
    imported not reimplemented -- or the seed prose contained VERBATIM
    (case/whitespace-normalised) in the existing prose. Flagship: seed
    `authority_level_ordering`'s prose is verbatim the prose of
    `authority_levels_hierarchy` on L1-170_n042. A redraw for these buys
    a duplicate export, not a repair.

    LOCALITY IS REQUIRED (convergence review B1 -- this guard produced a
    FALSE SKIP of an evidence-confirmed defect): the providing NODE must
    cover the seed's establishment lines (the shared +-`tol` tolerance).
    Ground: the document states per-section authority in a fixed TEMPLATE
    ("Rules in the #X section carry Y-level instruction authority"), so
    `risk_queue.sim` scores 0.545 for ANY two such claims regardless of
    section -- the threshold has no discriminating power on that shape.
    `user_authority_section_rules` (ea 3150, the #avoid_errors heading)
    was skipped against `user_authority` on L3239-3382_n001, a DIFFERENT
    section 89 lines away, while Opus lists it as a confirmed defect.
    Both correct skips already satisfy locality: L1-170_n042 covers
    `authority_level_ordering`'s ea 69, L3505-3953_n001 covers
    `section_authority_level`'s ea 3506. Without a usable ea there is no
    locality to test and the guard declines to fire -- it must never skip
    a real defect on prose resemblance alone."""
    import risk_queue as RQ
    if not (isinstance(ea, (list, tuple)) and len(ea) >= 2):
        return None
    tgt = _norm_prose(prose)
    best = None
    for n in g.get("nodes", []):
        if not _node_covers(n, ea, tol):
            continue
        for p in n.get("provides", []):
            if not isinstance(p, dict) or not p.get("name"):
                continue
            pp = p.get("prose", "")
            verbatim = bool(tgt) and tgt in _norm_prose(pp)
            s = RQ.sim(prose, pp)
            if not verbatim and s < threshold:
                continue
            key = (1 if verbatim else 0, s)
            if best is None or key > best[0]:
                best = (key, (p["name"], n.get("id"),
                              "verbatim" if verbatim else "token-overlap",
                              round(s, 3)))
    return best[1] if best else None


def _clip_ea(seed, lo, hi):
    """Clip a re-derived SECTION BODY establishment to the redraw leaf.
    A body range can outrun the leaf that covers its heading, and a seed
    whose ea straddles the leaf boundary is owed by NO leaf
    (validate_leaf's boundary ruling) -- the redraw would never be told
    it owes the promise. The heading itself is always inside the leaf,
    since that leaf was descended from it."""
    ea = seed.get("established_around")
    if not (isinstance(ea, (list, tuple)) and len(ea) >= 2):
        return seed
    return dict(seed, established_around=[max(ea[0], lo), min(ea[1], hi)])


def seed_entry(unwind_dir, name):
    """The responsible division's own seed row for `name`, or None."""
    d = json.load(open(os.path.join(unwind_dir, "division.json")))
    return next((s for s in d.get("seed_vocabulary", [])
                 if isinstance(s, dict) and s.get("name") == name), None)


def _unwind_dir(run_dir, art):
    """health.jsonl's `artifact` field as recorded at build time -- may be
    absolute, run-relative, or the run dir itself."""
    for cand in (art or "", os.path.join(run_dir, art or ""), run_dir):
        if cand and os.path.exists(os.path.join(cand, "division.json")):
            return cand
    return None


def _descend(unwind_dir, line):
    """Descend the cached division tree to the leaf whose span covers
    `line`. Returns ((lo, hi, leaf_wdir, inherited_seeds), None) or
    (None, reason). No model call."""
    d = json.load(open(os.path.join(unwind_dir, "division.json")))
    wdir = unwind_dir
    while True:
        seeds = d.get("seed_vocabulary", [])
        idx = clo = chi = None
        for i, c in enumerate(d.get("children", []), 1):
            sp = c.get("span") if isinstance(c, dict) else None
            if (isinstance(sp, (list, tuple)) and len(sp) == 2
                    and sp[0] <= line <= sp[1]):
                idx, (clo, chi) = i, sp
                break
        if idx is None:
            return None, f"no child span covers line {line} under {wdir}"
        cdir = os.path.join(wdir, f"c{idx}")
        sub = os.path.join(cdir, "division.json")
        if os.path.exists(sub):
            d2 = json.load(open(sub))
            if d2.get("decision") == "divide":
                wdir, d = cdir, d2
                continue
        return (clo, chi, cdir, seeds), None


def locate_leaf(unwind_dir, name, seed=None):
    """(seed, lo, hi, leaf_wdir, inherited_seeds) for the promised name,
    or (None, reason). Descends cached divisions only -- no model call.

    `seed`: the caller's already-resolved seed (run_repair passes the one
    `resolve_establishment` re-aimed). Absent, the division's own row is
    read -- the pre-guard behaviour, unchanged."""
    if seed is None:
        seed = seed_entry(unwind_dir, name)
    ea = (seed or {}).get("established_around")
    if not (isinstance(ea, (list, tuple)) and len(ea) >= 2):
        return None, (f"seed '{name}' has no usable established_around in "
                      f"{unwind_dir}/division.json")
    located, why = _descend(unwind_dir, ea[0])
    if located is None:
        return None, why
    lo, hi, leaf_wdir, seeds = located
    return (seed, lo, hi, leaf_wdir, seeds), None


def _all_division_seeds(run_dir):
    """name -> seed entry, from every cached division.json under the run
    (first wins, the validator's own convention)."""
    import glob
    out = {}
    for p in sorted(glob.glob(os.path.join(run_dir, "**", "division.json"),
                              recursive=True)):
        try:
            for s in json.load(open(p)).get("seed_vocabulary", []):
                if isinstance(s, dict) and s.get("name"):
                    out.setdefault(s["name"], s)
        except Exception:               # noqa: BLE001
            pass
    return out


def _covers(sp, ea, tol=2):
    """Span-coherence test with tolerance (re-review 1c): a span counts as
    covering the establishment when it contains ANY line of [ea0, ea1] or
    sits within +-2 lines of it. Ground: the flagship
    interactive_vs_programmatic case -- seed established_around
    [3384, 3386], the establishing nodes START at 3386; exact-containment
    of ea[0] alone called that infeasible."""
    if not (isinstance(sp, (list, tuple)) and len(sp) == 2
            and isinstance(ea, (list, tuple)) and len(ea) >= 2):
        return False
    return not (sp[1] < ea[0] - tol or sp[0] > ea[1] + tol)


def _node_covers(node, ea, tol=2):
    return any(isinstance(sp, dict)
               and _covers(sp.get("lines"), ea, tol)
               for sp in (node or {}).get("spans", []))


def is_authority_export(name):
    """An authority-CLASS export name. ONE source: recurse_driver's own
    `AUTHORITY_CANONICAL` + `is_authority_coinage` -- the constants the
    validator and the autofix already share."""
    return (isinstance(name, str)
            and (name in R.AUTHORITY_CANONICAL
                 or R.is_authority_coinage(name)))


def _is_authority_assignment(node):
    """A node that does nothing but ASSIGN an authority level to a
    section (`provides: [user_authority]` on the heading line). The
    repo's standing ruling -- assignment and definition are DISTINCT
    (the 16/16 dropped_merge upholds) -- forbids splicing a section's
    substance onto one."""
    names = [R.nm(p) for p in (node or {}).get("provides", [])]
    return bool(names) and all(is_authority_export(n) for n in names)


def _exports_substance(node):
    """The node already exports a NON-authority name -- i.e. it is not one
    of the empty-provides nodes the under-export class exists to fill."""
    names = [R.nm(p) for p in (node or {}).get("provides", [])]
    return any(not is_authority_export(n) for n in names)


def _select_target(nodes, ea, tol=2, section=False):
    """THE ONE splice-target selector (final re-review 1c displacement;
    both the prep feasibility check and splice's promise-class branch
    call this -- the coherence lesson: two selection rules drift).

    SECTION MODE (`section=True`, convergence review B2b) -- used when the
    establishment was re-derived from a section HEADING, so `ea` is that
    section's BODY range rather than a pointer at establishing lines. The
    ranking above is wrong for that shape: max-overlap picks the widest
    node in the section (a worked example), and the +-2 tolerance reaches
    BACKWARDS past the heading into the previous section's commentary.
    Section mode instead:
      1. admits only nodes whose span STARTS inside the body range -- no
         tolerance, so the commentary two lines above the heading is out
         (risk_taxonomy heading 53 was selecting L1-170_n032 at line 51);
      2. DECLINES an authority-assignment node (`_is_authority_assignment`)
         -- splicing a section's substance onto its authority label merges
         assignment with definition, which this repo has ruled distinct;
      3. ranks by EARLIEST span start, then narrowest: the node that
         establishes a section's substance is the first substantive claim
         under its heading (avoid_overstepping -> L3239-3382_n002, not the
         `user_authority` node n001; red_line_principles -> n017 "Human
         safety and human rights are paramount"; risk_taxonomy -> n033
         "three broad categories of risk").
    No admissible candidate returns None -- the caller reports rather than
    splicing onto the wrong node.

    Default (point/near-point ea) ranking, NEVER graph order:
      1. EXACT-cover nodes first -- a span containing ANY line of
         [ea0, ea1], no tolerance;
      2. only if none exist, the +-2 tolerance fallback;
      3. among matches: maximum line-overlap with [ea0, ea1], then the
         narrowest span.
    Ground (ds7 flagship): ea [3384, 3386] with the adjacent worked-
    example node L3239-3382_n017 (spans to 3382, inside tolerance)
    present must select L3383-3501_n001 -- first-cover-in-graph-order
    displaced the splice onto the neighbour."""
    if not (isinstance(ea, (list, tuple)) and len(ea) >= 2):
        return None
    best_node, best_key = None, None
    for n in nodes:
        if section and _is_authority_assignment(n):
            continue                      # B2b: assignment != definition
        for sp in n.get("spans", []):
            ln = sp.get("lines") if isinstance(sp, dict) else None
            if not (isinstance(ln, (list, tuple)) and len(ln) == 2):
                continue
            if section:
                if not ea[0] <= ln[0] <= ea[1]:
                    continue              # must START inside the body
                key = (-ln[0], -(ln[1] - ln[0]))       # earliest, narrowest
            else:
                if not _covers(ln, ea, tol):
                    continue
                exact = not (ln[1] < ea[0] or ln[0] > ea[1])
                ov = max(0, min(ln[1], ea[1]) - max(ln[0], ea[0]) + 1)
                key = (1 if exact else 0, ov, -(ln[1] - ln[0]))
            if best_key is None or key > best_key:
                best_key, best_node = key, n
    return best_node


def underexport_candidates(run_dir, g):
    """The deterministic scan (item A extension; delta_investigation
    cause 3 -- ds7's one real defect: 92 exported provides names vs the
    golden's 230, with ~50 of the 64 near-miss danglings naming content
    that EXISTS as nodes with empty provides). For each dangling need:
    the best existing node whose establishes has >= 0.25 token overlap
    with the need prose, or whose spans contain the name's seed
    established_around (when any cached division seeded it). Emits one
    candidate per dangling name."""
    import risk_queue as RQ
    provides = {R.nm(p) for n in g.get("nodes", [])
                for p in n.get("provides", [])}
    seeds = _all_division_seeds(run_dir)
    cands = {}
    for n in g.get("nodes", []):
        for d in n.get("needs", []):
            name = R.nm(d)
            if name in provides or not isinstance(d, dict):
                continue
            if name in cands:
                continue
            prose = d.get("prose", "")
            ea = (seeds.get(name) or {}).get("established_around")
            best, best_sim, via = None, 0.0, None
            for cand in g.get("nodes", []):
                if cand is n:
                    continue
                s = RQ.sim(prose, cand.get("establishes", ""))
                if s >= 0.25 and s > best_sim:
                    best, best_sim, via = cand, s, "establishes-overlap"
                if (best is None and isinstance(ea, (list, tuple))
                        and len(ea) >= 2
                        and any(isinstance(sp, dict)
                                and (sp.get("lines") or [0, -1])[0]
                                <= ea[0]
                                <= (sp.get("lines") or [0, -1])[1]
                                for sp in cand.get("spans", []))):
                    best, via = cand, "established_around"
            if best is None:
                continue
            a = (best.get("spans") or [{}])[0].get("lines") or [None, None]
            if a[0] is None:
                continue
            # re-review 1b (target/ea coherence; 4/23 ds7 candidates
            # incoherent): when the target was picked by establishes
            # OVERLAP, the redraw location derives FROM THE TARGET's own
            # span and the (possibly stale) seed ea is dropped -- never
            # redraw an ea leaf to splice a distant node. Only an
            # ea-picked target (which covers ea by construction) keeps
            # the seed's established_around.
            if via == "establishes-overlap" or not (
                    isinstance(ea, (list, tuple)) and len(ea) >= 2):
                ea_out = [a[0], a[1]]
            else:
                ea_out = list(ea[:2])
            cands[name] = {
                "name": name, "prose": prose, "needer": n.get("id"),
                "target_id": best.get("id"), "via": via,
                "sim": round(best_sim, 3),
                "established_around": ea_out}
    return list(cands.values())


def promise_extra(seed):
    ea = seed["established_around"]
    return (f"\n⚠️ PROMISE REPAIR: the inherited seed '{seed['name']}' "
            f"({seed.get('prose', '')}) is established around lines "
            f"{ea[0]}-{ea[1]} inside your span; if your span genuinely "
            f"establishes it you MUST include a provides entry with "
            f"exactly this name; if it does NOT, say why in "
            f"judgment_calls.")


def redraw_leaf(drv, seed, lo, hi, seeds, scratch_wdir):
    """Driver.leaf semantics, promise-instrumented: same prompt
    construction (leaf_dispatch + dispatch_block), same validators, plus
    the appended instruction and item B's deliver-or-explain enforcement
    scoped to THIS seed."""
    extra, schema, derive = R.leaf_dispatch(lo, hi, drv.cfg)
    extra += promise_extra(seed)
    if not any(isinstance(s, dict) and s.get("name") == seed["name"]
               for s in seeds):
        seeds = list(seeds) + [seed]
    g = drv.call(drv.dispatch_block("L", lo, hi, seeds, extra),
                 lambda o: R.validate_leaf(
                     o, lo, hi, drv.lines, derive_uncovered=derive,
                     seeds=[seed], enforce_promise_delivery=True),
                 schema=schema)
    os.makedirs(scratch_wdir, exist_ok=True)
    R.write_json(os.path.join(scratch_wdir, "graph.json"), g)
    return g


#: FIX 2 (repaired_verification.md §1e): phrasings by which a redraw's
#: judgment_calls text ASSERTS that it delivered (or is about to deliver)
#: the provides entry. ds7 booked "I will add a provides entry to n007
#: for 'support_mental_health' ... to satisfy the promise repair" as an
#: HONEST DECLINE -- the reply announced compliance and then emitted
#: nothing, and the stage's own report overstated its declines by one.
_DELIVERY_VERB = (r"(?:add|adding|added|includ(?:e|ing|ed)|"
                  r"provid(?:e|es|ing|ed)|emit(?:ting|ted)?|"
                  r"creat(?:e|ing|ed)|insert(?:ing|ed)?|"
                  r"suppl(?:y|ying|ied)|writ(?:e|ing)|wrote)")
_NEGATION = re.compile(r"\b(?:not|never|n't|cannot|can't|won't|wont|"
                       r"refuse[sd]?|declin(?:e|es|ed)|unable|"
                       r"should\s+not|must\s+not|no)\b", re.I)
#: "I will add ...", "we have included ...", "I am adding ..."
_ACTIVE_DELIVERY = re.compile(
    r"\b(?:i|we)\b(?P<mid>(?:'(?:ll|ve|d|m))?(?:\s+[\w']+){0,3}?)\s+"
    + _DELIVERY_VERB + r"\b", re.I)
#: "a provides entry will be added", "the entry has been included"
_PASSIVE_DELIVERY = re.compile(
    r"\b(?:will\s+be|has\s+been|have\s+been|is\s+being)\s+"
    r"(?:added|included|provided|emitted|created|inserted)\b", re.I)


def asserts_delivery(text, name=""):
    """True when `text` claims the provides entry was or will be
    delivered. Scoped SENTENCE-BY-SENTENCE and required to be about the
    entry (the sentence mentions `provides`/`entry` or the seed's own
    name), so "I will explain in judgment_calls" is not a delivery
    claim; negated forms ("I will NOT add", "cannot provide") are not
    either -- a decline that says what it declines to do stays an
    honest decline."""
    for sent in re.split(r"[.;\n]+", str(text or "")):
        low = sent.lower()
        if not ("provides" in low or "provide entry" in low
                or "entry" in low or (name and R.name_mentioned(name,
                                                               sent))):
            continue
        m = _ACTIVE_DELIVERY.search(sent)
        if m and not _NEGATION.search(m.group("mid") or ""):
            return True
        if _PASSIVE_DELIVERY.search(sent):
            return True
    return False


def self_loops(g):
    """(node id, name) pairs where a node NEEDS a name it PROVIDES.
    A node cannot depend on itself: the 'resolution' of such a need is
    degenerate (repaired_verification.md: ds7's repair took self-loops
    16 -> 19 and 3 of 43 'resolved' needers resolved onto themselves)."""
    out = set()
    for n in g.get("nodes", []):
        prov = {R.nm(p) for p in n.get("provides", [])}
        for d in n.get("needs", []):
            if R.nm(d) in prov:
                out.add((n.get("id"), R.nm(d)))
    return out


def splice(g, seed, redraw, unwind_art, scratch_wdir, target_id=None,
           section=False, seat=None):
    """The mechanical merge: ONLY the new provides entry (and any new
    needs the validator accepted on the providing node) reach the graph
    copy. `target_id` (the under-export class): the scan already named
    the node that owns the establishment lines.

    ⛔ `seat` (FIX 1, repaired_verification.md) is the MANDATORY meaning
    gate in production: after the redraw has delivered the entry and
    EVERY mechanical check has passed, a splice_seat.Seat adjudicates
    the concept's prose against the RECEIVING NODE's own content, blind
    on the name. Only "establishes" splices; anything else returns
    `rejected_by_splice_seat` with the seat's grounds and leaves the
    graph untouched. The four ds7 wrong splices all reached this point
    with every mechanical guard satisfied. `seat=None` skips the gate --
    the mechanical-unit path only; `run_repair` builds one whenever
    `promise_repair.splice_seat` is true, which is the DEFAULT."""
    name, ea = seed["name"], seed["established_around"]
    prov_node = prov_entry = None
    for n in redraw.get("nodes", []):
        for p in n.get("provides", []):
            if isinstance(p, dict) and p.get("name") == name:
                prov_node, prov_entry = n, p
                break
        if prov_entry:
            break
    if prov_entry is None:
        # re-review 2-note: word-boundary match, never substring -- a
        # judgment_calls entry naming support_mental_health_rule must not
        # count as a decline of support_mental_health
        named = next((j for j in redraw.get("judgment_calls", [])
                      if isinstance(j, str)
                      and R.name_mentioned(name, j)), None)
        reason = named or ("(declined without a judgment_calls reason -- "
                           "validator accepted the reply, treat as "
                           "decline)")
        # FIX 2: a reason that ANNOUNCES the entry it never emitted is a
        # NARRATION MISMATCH, not an honest decline. An honest decline
        # names the seed AND emits no entry AND does not claim to have.
        if named is not None and asserts_delivery(named, name):
            return "narration_mismatch", (
                f"the redraw's reason asserts it delivers the provides "
                f"entry and no such entry exists in the reply -- a "
                f"non-delivery, NOT an honest decline: {named}")
        return "declined", reason
    if not _node_covers(prov_node, ea):
        return "failed", (f"redraw provides '{name}' but not at the "
                          f"establishment lines {list(ea[:2])} "
                          f"(+-2 tolerance)")
    if target_id is not None:
        target = next((n for n in g.get("nodes", [])
                       if n.get("id") == target_id), None)
    else:
        target = _select_target(g.get("nodes", []), ea, section=section)
    if target is None:
        return "failed", (f"no root-graph node covers the establishment "
                          f"lines {list(ea[:2])}"
                          + (" that is not an authority-assignment node"
                             if section else "")
                          if target_id is None
                          else f"scan target {target_id!r} vanished from "
                               f"the root graph")
    # ⛔ FIX 1: THE MEANING GATE, last thing before the graph is touched.
    # Blind on the name: the seat sees the concept's PROSE and the
    # target's own establishes + span text. Nothing below this line runs
    # on a "does_not_establish".
    verdict = None
    if seat is not None:
        verdict = seat.adjudicate(prov_entry.get("prose")
                                  or seed.get("prose", ""), target)
        if verdict["verdict"] != "establishes":
            return "rejected_by_splice_seat", (
                f"the splice seat judged that {target.get('id')} does "
                f"not establish the concept: {verdict['grounds']}")
    have_p = {R.nm(p) for p in target.get("provides", [])}
    if name not in have_p:
        target.setdefault("provides", []).append(dict(prov_entry))
    have_n = {R.nm(d) for d in target.get("needs", [])}
    # FIX 3: a node cannot depend on itself. The name it now PROVIDES is
    # dropped from its own needs (ds7 made 3 such self-loops, and each
    # counted as a "resolved" needer), and no new self-need is spliced in.
    dropped_self = [R.nm(d) for d in target.get("needs", [])
                    if R.nm(d) == name]
    if dropped_self:
        target["needs"] = [d for d in target.get("needs", [])
                           if R.nm(d) != name]
        have_n.discard(name)
    new_needs = [dict(d) for d in prov_node.get("needs", [])
                 if isinstance(d, dict) and d.get("name") not in have_n
                 and d.get("name") != name]
    target.setdefault("needs", []).extend(new_needs)
    g.setdefault("promise_repairs", []).append({
        "name": name, "unwind": unwind_art, "target": target.get("id"),
        "established_around": list(ea[:2]),
        "redraw_artifact": os.path.relpath(scratch_wdir),
        "spliced_needs": [d.get("name") for d in new_needs],
        "dropped_self_needs": dropped_self,
        "splice_seat": verdict})
    g.setdefault("driver_autofixes", []).append(
        f"promise_repair: spliced provides '{name}' onto "
        f"{target.get('id')} from the targeted leaf redraw "
        f"(established_around {list(ea[:2])})"
        + (f"; dropped the node's self-need '{name}'"
           if dropped_self else ""))
    return "repaired", target.get("id")


def danglings(g):
    provides = {R.nm(p) for n in g.get("nodes", [])
                for p in n.get("provides", [])}
    return {(n.get("id"), R.nm(d)) for n in g.get("nodes", [])
            for d in n.get("needs", []) if R.nm(d) not in provides}


def run_repair(run_dir, cfg, client, lines):
    """The whole stage. `client` and `lines` are injected: pins run it
    with a MockClient for $0; main() wires the live GraphClient."""
    items = broken_promises_to_repair(run_dir)
    #: optional evidence intersection (absent => behaviour unchanged).
    #: A path relative to this directory or absolute.
    pr_cfg = cfg.get("promise_repair") or {}
    confirmed = None
    if pr_cfg.get("opus_verdicts"):
        vp = pr_cfg["opus_verdicts"]
        if not os.path.isabs(vp):
            vp = os.path.join(HERE, vp)
        confirmed = opus_confirmed_names(vp)
    g = json.load(open(os.path.join(run_dir, "root_graph.json")))
    g = json.loads(json.dumps(g))              # NEVER in place
    before = danglings(g)
    scratch_root = os.path.join(run_dir, "promise_repair")
    drv = R.Driver(cfg, client, lines, scratch_root)
    #: names already provided ANYWHERE in the root graph (re-review 1a;
    #: ds7 real case: scope_of_autonomy already provided by L461-608_n002
    #: -- 3/26 queue names were stale): a redraw for these buys nothing
    provided_now = {R.nm(p) for n in g.get("nodes", [])
                    for p in n.get("provides", [])}
    # -- deterministic prep first: locate every leaf, THEN gate, THEN spend
    plans, report_items = [], []
    seen_promise = set()          # re-review 1d: one plan per name, max
    for it in items:
        det = it.get("detail") or {}
        name = det.get("name")
        if name in seen_promise:
            continue              # 1d (chain_of_command_principle x6 ->
        seen_promise.add(name)    #     one plan)
        if confirmed is not None and name not in confirmed:
            report_items.append({"name": name, "unwind": det.get("unwind"),
                                 "class": "promise",
                                 "status": "skipped_not_opus_confirmed",
                                 "why": "the evidence recheck upheld this "
                                        "row: the concept is in the graph, "
                                        "so the promise is not broken"})
            continue
        if name in provided_now:
            report_items.append({"name": name, "unwind": det.get("unwind"),
                                 "class": "promise",
                                 "status": "skipped_already_provided",
                                 "why": "the name is already provided in "
                                        "the root graph (stale queue row)"})
            continue
        udir = _unwind_dir(run_dir, det.get("unwind"))
        if udir is None:
            report_items.append({"name": name, "unwind": det.get("unwind"),
                                 "class": "promise", "status": "failed",
                                 "why": "unwind artifact dir not found"})
            continue
        # -- GUARDS 2 + 3 run FIRST: guard 1's locality test (review B1)
        # needs the RESOLVED establishment, not the raw seed's.
        # The note rides ON THE PLAN (never a second report row -- one row
        # per name is the 1d invariant the counters depend on).
        seed0 = seed_entry(udir, name)
        seed_r, note, section = seed0, None, False
        if seed0 is not None:
            ea_r, kind, why_r = resolve_establishment(seed0, lines)
            if kind == "skipped_citation_site_unresolved":
                report_items.append({"name": name,
                                     "unwind": det.get("unwind"),
                                     "class": "promise", "status": kind,
                                     "why": why_r})
                continue
            if ea_r is not None and kind is not None:
                seed_r = dict(seed0, established_around=ea_r)
                note = {"establishment": kind, "establishment_why": why_r}
                section = True
        # -- GUARD 1: same referent under a different exported name, at
        # the establishment (review B1: locality is required)
        match = same_referent_provider((seed_r or {}).get("prose", ""), g,
                                       (seed_r or {}).get(
                                           "established_around"))
        if match is not None:
            mname, mnode, how, msim = match
            report_items.append(dict({
                "name": name, "unwind": det.get("unwind"),
                "class": "promise",
                "status": "skipped_same_referent",
                "matched_name": mname, "matched_node": mnode,
                "match_kind": how, "sim": msim,
                "why": f"the referent is already exported as '{mname}' on "
                       f"{mnode} ({how}, sim {msim}) at the establishment "
                       f"lines; a redraw would duplicate the export"},
                **(note or {})))
            continue
        # A RE-DERIVED establishment (guard 2 or 3) points at wherever the
        # DOCUMENT establishes the concept -- routinely outside the
        # promising unwind's own span (avoid_overstepping: promised under
        # the [1368, 1541] unwind, established at L3239). Descend the RUN
        # ROOT for those, or the descent fails with "no child span covers
        # line N" and the guard buys nothing. The seed's own ea keeps the
        # pre-guard behaviour: its unwind promised it there.
        base = udir
        if note and os.path.exists(os.path.join(run_dir, "division.json")):
            base = run_dir
        located, why = locate_leaf(base, name, seed=seed_r)
        if located is None:
            report_items.append(dict({"name": name,
                                      "unwind": det.get("unwind"),
                                      "class": "promise",
                                      "status": "failed",
                                      "why": why}, **(note or {})))
            continue
        seed, lo, hi, leaf_wdir, seeds = located
        seed = _clip_ea(seed, lo, hi) if section else seed
        plans.append({"class": "promise", "seed": seed, "lo": lo, "hi": hi,
                      "seeds": seeds, "unwind": det.get("unwind"),
                      "target_id": None, "note": note, "section": section,
                      "scratch": os.path.join(scratch_root,
                                              _safe(name))})
    # -- class (b), the under-export scan (item A extension,
    # delta_investigation cause 3): danglings whose establishing content
    # already EXISTS as a node with empty provides get the SAME
    # must-provide-or-explain leaf redraw, aimed at that node's span
    planned = {p["seed"]["name"] for p in plans}
    if os.path.exists(os.path.join(run_dir, "division.json")):
        for c in underexport_candidates(run_dir, g):
            if c["name"] in planned:
                continue                 # the promise class owns this name
            # a synthetic seed: the dangling's own prose is the promise
            seed_c = {"name": c["name"], "prose": c["prose"],
                      "established_around": c["established_around"]}
            # GUARD 2 applies to THIS class too (opus_recheck_report §4:
            # sexual_content_involving_minors_section ea 4576 is the U18
            # section's cross-reference to the L826 prohibition -- the
            # splice would have landed ~3750 lines from the text). The
            # re-aim drops the scan's target_id with the stale ea: the
            # heading line elects its own target via _select_target.
            ea_c, kind, why_c = resolve_establishment(seed_c, lines)
            note, section = None, False
            if kind == "skipped_citation_site_unresolved":
                report_items.append({"name": c["name"],
                                     "class": "underexport",
                                     "status": kind, "why": why_c})
                continue
            if ea_c is not None and kind is not None:
                seed_c["established_around"] = ea_c
                c = dict(c, target_id=None)
                note = {"establishment": kind, "establishment_why": why_c}
                section = True
            # GUARD 1 for THIS class too (review B3, non-blocking): the
            # scan aims at a node with EMPTY provides, but the referent
            # can still be exported by a NEIGHBOURING node at the same
            # establishment -- `sexual_content_involving_minors_section`
            # re-aims onto L826 where `sexual_content_minors_prohibition`
            # already exports it. Same locality-constrained test, one
            # function, so the two classes cannot drift.
            match = same_referent_provider(seed_c["prose"], g,
                                           seed_c["established_around"])
            if match is not None:
                mname, mnode, how, msim = match
                report_items.append(dict({
                    "name": c["name"], "class": "underexport",
                    "status": "skipped_same_referent",
                    "matched_name": mname, "matched_node": mnode,
                    "match_kind": how, "sim": msim,
                    "why": f"the referent is already exported as "
                           f"'{mname}' on {mnode} ({how}, sim {msim}) at "
                           f"the establishment lines; a redraw would "
                           f"duplicate the export"}, **(note or {})))
                continue
            located, why = _descend(run_dir, seed_c["established_around"][0])
            if located is None:
                report_items.append(dict({"name": c["name"],
                                          "class": "underexport",
                                          "status": "failed", "why": why},
                                         **(note or {})))
                continue
            lo, hi, leaf_wdir, seeds = located
            if section:
                seed_c = _clip_ea(seed_c, lo, hi)
            plans.append({"class": "underexport", "seed": seed_c,
                          "lo": lo, "hi": hi, "seeds": seeds,
                          "unwind": f"(scan: {c['via']}, "
                                    f"target {c['target_id']})",
                          "target_id": c["target_id"], "note": note,
                          "section": section,
                          "scratch": os.path.join(
                              scratch_root, "underexport_"
                              + _safe(c["name"]))})
    # -- re-review 1c: prep-time splice feasibility, BEFORE spending.
    # Redraw side: the leaf must cover the establishment lines (with the
    # +-2 tolerance) or the redraw can never provide there. Target side:
    # a root-graph node must exist at those lines (the scan's target for
    # class b; any covering node for class a). Infeasible plans become
    # report rows and cost nothing.
    feasible = []
    for p in plans:
        ea = p["seed"]["established_around"]
        if not _covers([p["lo"], p["hi"]], ea):
            report_items.append(dict({"name": p["seed"]["name"],
                                      "class": p["class"],
                                      "unwind": p["unwind"],
                                      "status": "infeasible",
                                      "why": f"redraw leaf [{p['lo']}, "
                                             f"{p['hi']}] does not cover "
                                             f"established_around "
                                             f"{list(ea[:2])} (+-2)"},
                                     **(p.get("note") or {})))
            continue
        if p["target_id"] is not None:
            tgt = next((n for n in g.get("nodes", [])
                        if n.get("id") == p["target_id"]), None)
        else:
            tgt = _select_target(g.get("nodes", []), ea,
                                 section=p.get("section", False))
        if tgt is None:
            report_items.append(dict({"name": p["seed"]["name"],
                                      "class": p["class"],
                                      "unwind": p["unwind"],
                                      "status": "infeasible",
                                      "why": f"no splice target at "
                                             f"{list(ea[:2])}"
                                             + (" that is not an "
                                                "authority-assignment node"
                                                if p.get("section")
                                                else " (+-2)")},
                                     **(p.get("note") or {})))
            continue
        # -- review B3, second arm: the UNDER-EXPORT class is DEFINED (see
        # the module docstring and delta_investigation cause 3) as a
        # dangling whose establishing content exists as a node with EMPTY
        # provides. When the elected target already exports substance, the
        # redraw writes a SECOND name for a referent the graph carries --
        # the duplicate export Opus upheld at
        # `sexual_content_involving_minors_section` (target L797-830_n014
        # already exports `sexual_content_minors_prohibition`), which the
        # prose test cannot see: that pair scores 0.364 against the 0.5
        # threshold. REJECTED ALTERNATIVE, by name: lowering the prose
        # threshold to ~0.36 to catch it -- tuning a floor until one case
        # passes is what produced review finding B1's false skip of an
        # evidence-confirmed defect. This arm reads the class's own
        # written contract instead, and is scoped to that class: the
        # promise class stands on a recorded division promise, and its
        # targets legitimately export adjacent names (`refusal_style_section`
        # aims at a node exporting `safe_complete_rule`, and Opus confirms
        # nothing refusal-style is exported).
        if p["class"] == "underexport" and _exports_substance(tgt):
            names = [R.nm(x) for x in tgt.get("provides", [])]
            report_items.append(dict({
                "name": p["seed"]["name"], "class": p["class"],
                "unwind": p["unwind"],
                "status": "skipped_same_referent",
                "matched_name": next(n for n in names
                                     if not is_authority_export(n)),
                "matched_node": tgt.get("id"),
                "match_kind": "target-already-exports",
                "why": f"the under-export class targets nodes with EMPTY "
                       f"provides; {tgt.get('id')} already exports "
                       f"{names}, so a redraw would add a duplicate name "
                       f"for a referent the graph already carries"},
                **(p.get("note") or {})))
            continue
        feasible.append(p)
    plans = feasible
    # -- budget gate BEFORE any call (worst case: full prompt in at the
    # configured rate, the leaf phase cap out; no cache credit).
    # Re-review 5: repair rounds are NOT multiplied into this gate --
    # documented rationale: the gate prices the expected path (one draw
    # per plan); repair-round overruns are backstopped by the MEASURED
    # ceiling main() sets (client.max_cost_usd = the stage budget), which
    # GraphClient/Client._log_usage enforces after every billed call
    # (routing-gap F2), so the stage can never spend past the budget
    # however many repair rounds the draws take.
    budget = float((cfg.get("promise_repair") or {})
                   .get("max_cost_usd", DEFAULT_BUDGET))
    price = cfg.get("price_per_mtok")
    if price and plans:
        pin, pout = price
        cap = cfg.get("phase_max_tokens",
                      R.Driver.PHASE_MAX_TOKENS).get("leaf_graph", 24576)
        worst = 0.0
        for p in plans:
            extra, _sch, _d = R.leaf_dispatch(p["lo"], p["hi"], cfg)
            prompt = drv.dispatch_block("L", p["lo"], p["hi"], p["seeds"],
                                        extra + promise_extra(p["seed"]))
            worst += ((len(drv.brief) + len(prompt)) / 3.5 / 1e6 * pin
                      + cap / 1e6 * pout)
        if worst > budget:
            raise T.CostGateError(
                f"promise repair worst case ${worst:.2f} over "
                f"{len(plans)} leaf redraw(s) exceeds "
                f"promise_repair.max_cost_usd ${budget:.2f}. Repair in "
                f"slices or raise the budget deliberately.")
    # -- FIX 1: the splice seat rides the stage's OWN client and budget
    # (one extra small call per delivered redraw, inside the ceiling
    # main() already set on the client). Default TRUE: it is a
    # correctness gate, not a feature flag; setting it false is a
    # deliberate, recorded choice to splice unadjudicated.
    seat = None
    if pr_cfg.get("splice_seat", True):
        slot = (lambda sch: setattr(client, "reply_schema", sch)) \
            if hasattr(client, "reply_schema") else None
        seat = SS.Seat(client.complete, lines, schema_slot=slot)
    # -- FIX 4: periodic checkpoints over the plan list
    ckpt_every, ckpt_pause = CK.checkpoint_config(cfg, "promise_repair")
    ckpt = CK.Checkpoint(
        ckpt_every, ckpt_pause, os.path.join(run_dir, "health.jsonl"),
        "promise_repair", total=len(plans), ceiling_usd=budget,
        resume_hint="re-run promise_repair.py on the same run dir: the "
                    "prep is deterministic and the already-repaired "
                    "names are skipped as already provided")
    # -- spend: one targeted leaf redraw per plan
    n_rep = n_dec = 0
    repaired_names = {"promise": set(), "underexport": set()}
    paused = None
    for i, p in enumerate(plans):
        seed = p["seed"]
        try:
            redraw = redraw_leaf(drv, seed, p["lo"], p["hi"], p["seeds"],
                                 p["scratch"])
        except T.Phase1Error as exc:
            report_items.append(dict({"name": seed["name"],
                                      "class": p["class"],
                                      "unwind": p["unwind"],
                                      "status": "failed",
                                      "why": f"redraw failed: {exc}"},
                                     **(p.get("note") or {})))
            continue
        status, detail = splice(g, seed, redraw, p["unwind"], p["scratch"],
                                target_id=p.get("target_id"),
                                section=p.get("section", False),
                                seat=seat)
        n_rep += status == "repaired"
        n_dec += status == "declined"
        if status == "repaired":
            repaired_names[p["class"]].add(seed["name"])
        report_items.append(dict({"name": seed["name"],
                                  "class": p["class"],
                                  "unwind": p["unwind"],
                                  "span": [p["lo"], p["hi"]],
                                  "status": status,
                                  ("target" if status == "repaired"
                                   else "why"): detail},
                                 **(p.get("note") or {})))
        # the checkpoint lands HERE: the report row is booked and the
        # graph copy holds this plan's splice, so a pause loses nothing
        try:
            ckpt.tick(i + 1,
                      spent_usd=getattr(client, "spent_usd", 0.0),
                      failures={
                          k: sum(1 for r in report_items
                                 if r["status"] == k)
                          for k in ("failed", "narration_mismatch",
                                    "rejected_by_splice_seat",
                                    "declined")})
        except CK.CheckpointPause as exc:
            paused = str(exc)
            break
    if seat is not None and hasattr(client, "reply_schema"):
        client.reply_schema = None
    after = danglings(g)
    resolved = len(before - after)
    # resolved-needer count PER CLASS (the item's own asked-for number):
    # a before-dangling resolves to a class when its name was repaired by
    # that class's redraws
    by_class = {}
    for cls in ("promise", "underexport"):
        rows = [r for r in report_items if r.get("class") == cls]
        by_class[cls] = {
            "planned": len(rows),
            "repaired": sum(1 for r in rows if r["status"] == "repaired"),
            "declined": sum(1 for r in rows if r["status"] == "declined"),
            "failed": sum(1 for r in rows if r["status"] == "failed"),
            # FIX 2 / FIX 1: neither is an honest decline. A narration
            # mismatch is a NON-DELIVERY (counted as a failed repair
            # below); a seat rejection is the gate working.
            "narration_mismatch": sum(
                1 for r in rows if r["status"] == "narration_mismatch"),
            "rejected_by_splice_seat": sum(
                1 for r in rows
                if r["status"] == "rejected_by_splice_seat"),
            "skipped_already_provided": sum(
                1 for r in rows
                if r["status"] == "skipped_already_provided"),
            # the 2026-08-14 guards, each counted on its own line
            "skipped_same_referent": sum(
                1 for r in rows if r["status"] == "skipped_same_referent"),
            "skipped_citation_site_unresolved": sum(
                1 for r in rows
                if r["status"] == "skipped_citation_site_unresolved"),
            "skipped_not_opus_confirmed": sum(
                1 for r in rows
                if r["status"] == "skipped_not_opus_confirmed"),
            "reaimed_citation_site": sum(
                1 for r in rows
                if r.get("establishment") == "reaimed_citation_site"),
            "section_heading_fallback": sum(
                1 for r in rows
                if r.get("establishment") == "section_heading_fallback"),
            "infeasible": sum(1 for r in rows
                              if r["status"] == "infeasible"),
            "needers_resolved": len(
                {(nid, nm) for nid, nm in (before - after)
                 if nm in repaired_names[cls]})}
    n_mis = sum(1 for r in report_items
                if r["status"] == "narration_mismatch")
    n_seat = sum(1 for r in report_items
                 if r["status"] == "rejected_by_splice_seat")
    #: FIX 2: a narration mismatch is a FAILED repair, never a decline
    n_fail = sum(1 for r in report_items
                 if r["status"] == "failed") + n_mis
    #: FIX 3: the graph-level self-loop census, before and after
    loops_before, loops_after = self_loops(
        json.load(open(os.path.join(run_dir, "root_graph.json")))), \
        self_loops(g)
    dropped_self = [d for pr in g.get("promise_repairs", [])
                    for d in (pr.get("dropped_self_needs") or [])]
    R.write_json(os.path.join(run_dir, "root_graph.repaired.json"), g)
    report = {"run": run_dir, "items": report_items,
              "repaired": n_rep, "declined_honestly": n_dec,
              "failed": n_fail,
              "narration_mismatch": n_mis,
              "rejected_by_splice_seat": n_seat,
              "splice_seat": ("on" if seat is not None else "off"),
              "splice_seat_calls": getattr(seat, "calls", 0),
              "by_class": by_class,
              "danglings_before": len(before),
              "danglings_after": len(after),
              "self_loops_before": len(loops_before),
              "self_loops_after": len(loops_after),
              "self_needs_dropped": len(dropped_self),
              "needers_resolved": resolved,
              "checkpoints": ckpt.fired,
              "paused": paused,
              "plans": len(plans),
              "spent_usd": round(getattr(client, "spent_usd", 0.0), 6)}
    R.write_json(os.path.join(run_dir, "promise_repair_report.json"),
                 report)
    with open(os.path.join(run_dir, "health.jsonl"), "a") as f:
        f.write(json.dumps({"artifact": "promise_repair",
                            "kind": "promise_repair",
                            "repaired": n_rep, "declined": n_dec,
                            "failed": n_fail,
                            "narration_mismatch": n_mis,
                            "rejected_by_splice_seat": n_seat,
                            "self_loops_after": len(loops_after),
                            "paused": paused,
                            "by_class": {c: by_class[c]["needers_resolved"]
                                         for c in by_class},
                            "needers_resolved": resolved}) + "\n")
    print(f"promise repair: {n_rep} repaired, {n_dec} honestly "
          f"undeliverable, {n_fail} failed ({n_mis} narration "
          f"mismatch), {n_seat} rejected by the splice seat; danglings "
          f"{len(before)} -> {len(after)}; self-loops "
          f"{len(loops_before)} -> {len(loops_after)} ({resolved} "
          f"needer(s) resolved: promise "
          f"{by_class['promise']['needers_resolved']}, underexport "
          f"{by_class['underexport']['needers_resolved']}) -> "
          f"root_graph.repaired.json"
          + (f"\n⏸ {paused}" if paused else ""))
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run", help="run directory, e.g. runs/ds7")
    ap.add_argument("--config", default=os.path.join(HERE,
                                                     "driver_config.json"))
    ap.add_argument("--yes", action="store_true",
                    help="required: this stage spends real money")
    args = ap.parse_args(argv)
    if not args.yes:
        print("refusing to spend without --yes")
        return 2
    cfg = json.load(open(args.config))
    doc = os.path.join(PHASE1, "..", "..", "..", cfg["doc_path"])
    lines = R.load_doc(doc)
    prov = T.Provider(
        name="promise-repair", kind="openai-compatible",
        model=cfg["model"]["model"], base_url=cfg["model"]["base_url"],
        api_key_env=cfg["model"]["api_key_env"],
        temperature=cfg["model"].get("temperature", 0.0),
        max_tokens=cfg["model"].get("max_tokens", 16384),
        price_per_mtok=cfg["price_per_mtok"])
    client = R.GraphClient(prov, {"model": dict(
        cfg["model"], format_forcing="json_object",
        usage_log=cfg["model"].get("usage_log", "DEFAULT"))})
    client.max_cost_usd = float((cfg.get("promise_repair") or {})
                                .get("max_cost_usd", DEFAULT_BUDGET))
    try:
        run_repair(args.run, cfg, client, lines)
    except T.Phase1Error as exc:
        print(f"⛔ {type(exc).__name__}: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
