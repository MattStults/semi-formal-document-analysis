"""Turn a real tool run into a CONFLICT-panel input file + its side-car.

    .venv/bin/python conflict_adapter.py \\
        --conduct-file conducts.json \\
        --out conflict_panel_input.json \\
        --sidecar conflict_panel_sidecar.json

`conflict_output.py` fixes the file format for priority 2 (which passages does
a described behaviour VIOLATE) and `make_conflict_sample.py` fills it with six
hand-picked findings that are, by its own docstring, "not a tool run". This
module is the missing adapter: conduct vignettes in, `ConflictFinding` objects
out, `emit_pair()` in the middle, a blinded judging copy and a side-car on
disk. Nothing else in the repo constructs a `ConflictFinding` from the tool.

=============================================================================
WHAT `conflictScore` ACTUALLY MEANS -- READ THIS BEFORE COLLECTING A PANEL
=============================================================================
It is a RELEVANCE score. It is not a violation score, and this module has no
violation detector in it.

`relevance.RelevanceIndex.rank()` answers "does this passage BEAR ON this
query" -- lexical similarity, ontology-atom overlap, a section-level boost. It
was built, swept and benchmarked against the priority-1 RELEVANCE panel. There
is no component anywhere in this repo that reads a passage and a conduct and
decides whether one breaches the other. So what this adapter emits is:

    the top-k passages RANKED BY RELEVANCE to the conduct sentence,
    presented to the panel as conflict candidates.

Under the panel's own rubric a relevant-but-not-violated passage scores 0 --
that is calibration example 3, and it is the mistake the rubric is built to
prevent. The tool's candidate list cannot avoid that class of error, because
relevance is exactly what it is ranking. Concretely:

  * The panel MEASURES: precision of a relevance-ranked candidate list under a
    conflict rubric -- "when the tool's top-8 relevant passages for this
    conduct are judged for violation, how many are violations?" -- plus an
    inverse-probability estimate of what such a list misses.
  * The panel DOES NOT MEASURE: the accuracy of a conflict detector, because
    there is no conflict detector. A low number is a fact about ranking by
    relevance, not evidence that a (nonexistent) violation model is bad.

That is a weaker claim than "the tool detects conflicts", and it is the claim
the collected panel will support. It is still worth collecting: it is the
first measurement of how far relevance ranking gets you on priority 2, it
gives the prevalence and difficulty numbers a real conflict scorer would have
to beat, and every negative it draws is reusable when one exists.

`rationale` on every finding says this in the file itself, so an analyst who
opens the side-car a month from now cannot mistake the number for a violation
strength. The judging copy, of course, contains none of it (`emit_pair()`).

EXPECT A LOW NUMBER, AND KNOW THAT BEFORE JUDGING. A cheap diagnostic: take
the six passages `make_conflict_sample.py` hand-picked as plausible
violations of its three vignettes and ask where this adapter ranks them for
the same vignettes. Under the default mode: ranks 10, 43, 89, 190, 224, 289
of 593 -- none inside a top-8 candidate list, though three of the six land
inside the 136-clause near-miss band the negatives are drawn from, which is
exactly the band doing its job. Those six are illustrative, not a reference (n=6,
hand-written by an earlier agent, never judged), so nothing here is tuned to
them and no precision figure should be quoted from them. Read it only as: the
panel is likely to score many candidates 0, and that is a finding about
relevance ranking on priority 2, not a broken run.

=============================================================================
THE CONDUCT IS THE QUERY (and what that costs)
=============================================================================
Input is `{slug: conduct sentence(s)}`, never the behaviour's abstract
`definition`: "does helpfulness violate this passage" is not a question with
an answer. The conduct text is the lexical query.

The ontology channel is more awkward, and `--atom-channel` exposes the choice:

  * `conduct` (DEFAULT) -- the behaviour's atoms, KEPT ONLY where the
    conduct's own words support them (token overlap between the conduct and
    the atom's name + gloss). Offline arithmetic over existing artifacts; no
    model call, nothing fitted.
  * `behaviour` -- all of the behaviour's atoms, i.e. the tool exactly as
    benchmarked. MEASURED PROBLEM: the atom channel then dominates and the
    candidate list stops depending on the conduct. On two unrelated
    helpfulness vignettes (a CSV cleanup, a contract summary) this mode
    returns the SAME top-10 clauses, 10 of 10; `conduct` mode returns
    disjoint lists, 0 of 10. A conduct-invariant candidate list cannot
    support a per-conduct panel, which is why it is not the default.
  * `off` -- lexical only. `relevance.py` will warn loudly that the scores are
    a lexical baseline, which is exactly right.

There is no conduct-level atom artifact and producing one would require a
model call at query time, which invariant 8 forbids. Whichever mode is used is
recorded in the side-car with the atom names actually selected.

=============================================================================
THE NEAR-MISS STRATUM IS REAL HERE
=============================================================================
`make_conflict_sample.py` stands a keyword count in for the tool's ranking,
so `estimate()`'s inverse-probability weighting measured a keyword list rather
than the tool. This adapter passes `SamplingFrame` the tool's OWN
sub-threshold ranking: every clause the tool scored > 0 for this conduct that
did not make the candidate cut, highest first, capped at `--near-pool`. So
`negative-near` really is "the tool ranked this and left it out", a found
violation there really is a near miss, and recall becomes estimable.

The frame is per (behaviour, spec) because the ranking is per conduct, and
`emit()` takes one frame per call -- so this module emits one pair per
behaviour and merges them (`_merge_pairs`, which refuses to merge anything
whose provenance, seed or passage ids disagree).

=============================================================================
TWO LEAKS FIXED
=============================================================================
1:1 CANDIDATES:NEGATIVES. `CONFLICT_PANEL_README.md` states and argues for
1:1 (it is the composition a judge who guesses the mix learns least from);
the shipped sample is 1:2. Here `n_near + n_field == n_candidates` per cell,
split as evenly as possible with the odd draw going to the near band, and
`_check_ratio()` re-counts the emitted side-car and REFUSES to write if the
realised ratio is not 1:1 -- a stratum smaller than requested silently
degrades the ratio otherwise.

`adjacent` IS CONSTANT FALSE ON EVERY PASSAGE. In the sample, candidates vary
and negatives are uniformly False, so anyone reading the JSON can separate
them by eye -- the blinding is gone for a human judge. It cannot be omitted
(`conflict_output._PASSAGE_KEYS` requires it), and setting it True on
negatives to match would be inventing data. So it is False everywhere: in the
relevance panel `adjacent` marks a "Related" rather than "Core" passage, a
judge-supplied display distinction that this tool has no basis to assert and
that the conflict rubric never asks about. A field with one value across the
file carries no information, so it cannot be used to identify negatives.

=============================================================================
INVARIANTS
=============================================================================
No model call at query time (the only imports are stdlib + this repo's offline
modules; there is no network client anywhere in the call graph). Nothing is
fitted to panel labels: the weights are `relevance.Weights` defaults, the
threshold defaults to `relevance.DEFAULT_THRESHOLD` (swept against the
RELEVANCE panel, never against conflict judgements -- which do not exist yet),
and no conflict label is read anywhere.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field

import conflict_output as co
import measure_join
import relevance

HERE = os.path.dirname(os.path.abspath(__file__))

CLAUSES_JSON = os.path.join(HERE, "modelspec_clauses.json")
ANNOTATIONS_JSON = os.path.join(HERE, "annotations_b8.json")
BEHAVIOUR_ATOMS_JSON = os.path.join(HERE, "behavior_atoms_b8.json")

#: README's "recommended" size: 8 candidates + 8 negatives per (behaviour,
#: spec) cell.
DEFAULT_CANDIDATES = 8

#: The relevance tool's own operating point. Swept against the RELEVANCE
#: panel (relevance.py), never against conflict labels -- there are none.
DEFAULT_THRESHOLD = relevance.DEFAULT_THRESHOLD

#: How much of the sub-threshold ranking counts as "near miss". 136 of 593 is
#: the arithmetic CONFLICT_PANEL_README.md quotes (~6% inclusion at 8 draws
#: from the near band, ~2% from the ~455-clause field).
DEFAULT_NEAR_POOL = 136

ATOM_MODES = ("conduct", "behaviour", "off")
DEFAULT_ATOM_MODE = "conduct"

SPEC = "openai"

#: Repeated verbatim into every finding's rationale. The side-car is the only
#: place the tool's claims survive, so the caveat has to travel with them.
SCORE_CAVEAT = (
    "RELEVANCE-RANKED CANDIDATE, NOT A VIOLATION CLAIM: this score is "
    "relevance.RelevanceIndex.rank() -- 'does this passage BEAR ON the "
    "conduct' -- and the tool has no violation detector. A passage that is "
    "relevant but not violated scores 0 under the panel rubric, so these "
    "candidates measure precision of a RELEVANCE-ranked list judged for "
    "conflict, which is a weaker claim than conflict detection.")

SCORE_MEANING = {
    "scale": "0..1, the corpus-normalised relevance rank score",
    "means": "relevance of the passage to the conduct text",
    "doesNotMean": ("strength of violation; there is no violation model in "
                    "this repo"),
    "producedBy": "relevance.RelevanceIndex.rank() via conflict_adapter.py",
    "caveat": SCORE_CAVEAT,
}

#: The relevance panel's own frontier trio, so the two panels are comparable
#: judge-for-judge. WHO JUDGES IS A DECISION, not a default -- `main()` says so
#: on stderr whenever this is used unedited.
DEFAULT_PANEL = [
    co.Judge("sol", "GPT-5.6 Sol", "model", model="gpt-5.6-sol"),
    co.Judge("kimi", "Kimi-K3", "model", model="moonshotai/Kimi-K3"),
    co.Judge("fable", "Claude Fable 5", "model", model="claude-fable-5"),
]

_SENTENCE = re.compile(r"(?<=[.!?])\s+")


# ---- inputs ----------------------------------------------------------------

def load_conducts(path: str) -> dict:
    """`{slug: conduct}` from a JSON file. Keys starting `_` are comments.

    A conduct is one or two sentences of CONCRETE described behaviour. The
    abstract definition is not a conduct and is never substituted for one --
    `conflict_output` introduced the field precisely because "does helpfulness
    violate this passage" has no answer.
    """
    with open(path) as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError(
            f"{path}: expected a JSON object mapping behaviour slug -> conduct "
            f"sentence(s), got {type(raw).__name__}")
    out = {}
    for slug, text in raw.items():
        if slug.startswith("_"):
            continue
        if not (isinstance(text, str) and text.strip()):
            raise ValueError(
                f"{path}: conduct for {slug!r} must be a non-empty string "
                f"describing what the assistant actually did")
        out[slug] = text.strip()
    if not out:
        raise ValueError(f"{path}: no conducts found")
    return out


def load_panel(path: str = None) -> list:
    if not path:
        return list(DEFAULT_PANEL)
    with open(path) as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        raw = raw.get("panel") or raw.get("judges")
    if not isinstance(raw, list):
        raise ValueError(
            f"{path}: expected a JSON list of judge objects "
            f"{{id, displayName, kind: human|model, model?}}")
    return [dict(j) for j in raw]


def file_digest(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# ---- the query -------------------------------------------------------------

def select_atoms(conduct: str, atoms, mode: str = DEFAULT_ATOM_MODE) -> list:
    """The query atoms for one conduct, under one `--atom-channel` mode.

    `conduct` mode keeps a behaviour atom only when the conduct's own words
    reach it: a stemmed token shared between the conduct and the atom's name
    or gloss. That is a lexical gate over artifacts already on disk -- no model
    call, no panel label, nothing fitted. It exists because `behaviour` mode
    makes the candidate list a function of the behaviour rather than of the
    conduct (see the module docstring for the measurement).
    """
    if mode not in ATOM_MODES:
        raise ValueError(f"unknown atom mode {mode!r}; expected one of "
                         f"{list(ATOM_MODES)}")
    atoms = list(atoms or [])
    if mode == "off":
        return []
    if mode == "behaviour":
        return atoms
    ct = relevance.tokens(conduct)
    out = []
    for a in atoms:
        text = f"{str(a.get('name', '')).replace('_', ' ')} {a.get('gloss', '')}"
        if relevance.tokens(text) & ct:
            out.append(a)
    return out


def conduct_query(slug: str, conduct: str, atoms=None,
                  mode: str = DEFAULT_ATOM_MODE) -> relevance.Behaviour:
    """The conduct as a `relevance.Behaviour` query.

    `name` is left empty and `definition` carries the CONDUCT: the abstract
    behaviour text must not enter the lexical query, or the ranking drifts back
    to "passages about helpfulness" and stops being about what was done.
    """
    return relevance.Behaviour(slug=slug, name="", definition=conduct,
                               atoms=select_atoms(conduct, atoms, mode))


# ---- evidence for one candidate --------------------------------------------

def cited_spans(explained: dict, quote: str, limit: int = 3) -> list:
    """The substrings of `quote` the ranking actually leaned on.

    Atom spans first (they are the annotation's own verbatim slice of this
    clause, so they name the concept that matched), then, if none matched, the
    sentence of the quote carrying the most weight from the query's top lexical
    terms. Everything returned is checked to be a literal substring of `quote`
    -- `ConflictFinding.cited_spans` promises that and a caller quoting a
    non-substring back at a judge would be quoting something the document does
    not say.
    """
    out = []
    for m in explained.get("matched_atoms") or []:
        span = (m.get("quote") or "").strip()
        if span and span in quote and span not in out:
            out.append(span)
        if len(out) >= limit:
            return out
    if out:
        return out
    terms = [t for t, _ in (explained.get("top_lexical_terms") or [])[:8]]
    if not terms:
        return out
    best, best_hits = None, 0
    for sent in _SENTENCE.split(quote):
        s = sent.strip()
        if not s:
            continue
        stems = {relevance.stem(w) for w in relevance.tokens(s)}
        hits = sum(1 for t in terms if t in stems)
        if hits > best_hits:
            best, best_hits = s, hits
    return [best] if best else []


def rationale(slug: str, rank_pos: int, n_ranked: int, score: float,
              threshold: float, explained: dict, atom_mode: str) -> str:
    """Why this clause is on the list, in the tool's own terms, with the
    caveat attached. Side-car only -- no judge ever reads this."""
    ch = explained.get("channels") or {}
    chan = ", ".join(f"{k} {ch.get(k, 0.0):.3f}"
                     for k in ("lex", "atom", "kind", "section"))
    names = [m["name"] for m in (explained.get("matched_atoms") or [])]
    seen, atoms = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            atoms.append(n)
    terms = ", ".join(t for t, _ in (explained.get("top_lexical_terms")
                                     or [])[:5])
    bits = [
        f"Ranked {rank_pos} of {n_ranked} clauses for this conduct "
        f"(relevance {score:.3f}, threshold {threshold:g}).",
        f"Channels: {chan}.",
        (f"Query atoms matched ({atom_mode} mode): {', '.join(atoms[:6])}."
         if atoms else
         f"No query atom matched this clause ({atom_mode} mode); the score is "
         f"lexical and sectional."),
    ]
    if terms:
        bits.append(f"Top shared terms: {terms}.")
    bits.append(SCORE_CAVEAT)
    return " ".join(bits)


# ---- the adapter -----------------------------------------------------------

@dataclass
class Adapter:
    """One offline tool run, reusable across conducts.

    Build once (the index is ~0.2 s over 593 clauses), then call
    `findings_for()` per conduct.
    """
    index: relevance.RelevanceIndex
    behaviour_atoms: dict = field(default_factory=dict)
    threshold: float = DEFAULT_THRESHOLD
    n_candidates: int = DEFAULT_CANDIDATES
    atom_mode: str = DEFAULT_ATOM_MODE
    spec: str = SPEC

    @classmethod
    def from_files(cls, clauses_path: str = CLAUSES_JSON,
                   annotations_path: str = ANNOTATIONS_JSON,
                   behaviour_atoms_path: str = BEHAVIOUR_ATOMS_JSON,
                   **kw) -> "Adapter":
        index = relevance.RelevanceIndex(
            measure_join.clause_rows(clauses_path),
            relevance.load_annotations(annotations_path))
        return cls(index=index,
                   behaviour_atoms=relevance.load_behaviour_atoms(
                       behaviour_atoms_path),
                   **kw)

    # -- ranking

    def query(self, slug: str, conduct: str) -> relevance.Behaviour:
        return conduct_query(slug, conduct, self.behaviour_atoms.get(slug),
                             self.atom_mode)

    def ranking(self, slug: str, conduct: str) -> list:
        """`[(clause_id, score)]` descending -- the whole corpus, one run."""
        return self.index.rank(self.query(slug, conduct))

    def findings_for(self, slug: str, conduct: str):
        """`(findings, subthreshold_scores, stats)` for one conduct.

        `findings` are the top `n_candidates` clauses at or above `threshold`.
        `subthreshold_scores` is `{clause_id: score}` for EVERY clause the tool
        ranked above zero and did not select -- the real near-miss band, handed
        straight to `SamplingFrame`. `stats` records the shape of the run.
        """
        behaviour = self.query(slug, conduct)
        ranked = self.ranking(slug, conduct)
        n_ranked = sum(1 for _, s in ranked if s > 0)
        picked = [(cid, s) for cid, s in ranked
                  if s > 0 and s >= self.threshold][:self.n_candidates]
        chosen = {cid for cid, _ in picked}

        findings = []
        for i, (cid, score) in enumerate(picked, start=1):
            clause = self.index.by_id[cid]
            quote = clause.get("quote", "")
            ex = self.index.explain(behaviour, cid)
            findings.append(co.ConflictFinding(
                behaviour_slug=slug,
                spec=self.spec,
                clause_id=cid,
                locator=clause.get("locator", ""),
                quote=quote,
                conflict_score=round(float(score), 6),
                rationale=rationale(slug, i, n_ranked, score, self.threshold,
                                    ex, self.atom_mode),
                cited_spans=cited_spans(ex, quote),
                example_block=bool(clause.get("in_example_block")),
                # Constant across the whole file; see the module docstring.
                adjacent=False))

        sub = {cid: round(float(s), 6) for cid, s in ranked
               if s > 0 and cid not in chosen}
        stats = {
            "atomMode": self.atom_mode,
            "queryAtoms": sorted({a["name"] for a in behaviour.norm_atoms}),
            "queryAtomsAvailable": len(self.behaviour_atoms.get(slug) or []),
            "atomChannelLive": bool(behaviour.norm_atoms),
            "threshold": self.threshold,
            "clausesRanked": len(ranked),
            "clausesScoredAboveZero": n_ranked,
            "clausesAtOrAboveThreshold": sum(
                1 for _, s in ranked if s > 0 and s >= self.threshold),
            "candidatesRequested": self.n_candidates,
            "candidatesSelected": len(findings),
            "subThresholdBand": len(sub),
            "candidateScoreRange": ([picked[0][1], picked[-1][1]]
                                    if picked else []),
        }
        return findings, sub, stats


# ---- assembling the pair ---------------------------------------------------

def split_negatives(n: int) -> tuple:
    """`(n_near, n_field)` summing to `n` -- the README's 1:1 composition.

    The odd draw goes to the near band: that is where misses concentrate, and
    it is the stratum whose inclusion probability is high enough for a single
    hit to mean something.
    """
    near = math.ceil(n / 2)
    return near, n - near


def _merge_pairs(pairs: list):
    """Merge per-behaviour `(judging, sidecar)` pairs into one of each.

    One `emit()` call takes one `SamplingFrame`, but the near-miss band is per
    conduct, so each behaviour is emitted with its own frame. Merging is
    therefore load-bearing and is checked hard: identical provenance, identical
    seed, disjoint slugs, disjoint passage ids. A silent merge failure would
    show up as a broken re-join or a wrong recall denominator hours later.
    """
    if not pairs:
        raise ValueError("no behaviours emitted: nothing to merge")
    judging = copy.deepcopy(pairs[0][0])
    side = copy.deepcopy(pairs[0][1])
    seen_slugs = {b["slug"] for b in judging["behaviours"]}
    for j, s in pairs[1:]:
        if j["provenance"] != judging["provenance"]:
            raise ValueError(
                "cannot merge: two behaviours were emitted with different "
                "provenance (roster, judge prompt or run date differ); they "
                "are not one panel")
        if s["sampling"]["seed"] != side["sampling"]["seed"]:
            raise ValueError("cannot merge: the behaviours were sampled under "
                             "different seeds")
        for b in j["behaviours"]:
            if b["slug"] in seen_slugs:
                raise ValueError(
                    f"cannot merge: behaviour {b['slug']!r} appears twice; "
                    f"every consumer keys on slug and one copy would be "
                    f"silently dropped")
            seen_slugs.add(b["slug"])
            judging["behaviours"].append(b)
        dup = set(s["passages"]) & set(side["passages"])
        if dup:
            raise ValueError(
                f"cannot merge: duplicate passage id(s) {sorted(dup)[:3]}; "
                f"the side-car join would reassign verdicts")
        side["passages"].update(s["passages"])
        side["sampling"]["frames"].update(s["sampling"]["frames"])
    return judging, side


def _check_ratio(sidecar: dict) -> list:
    """Errors if any cell is not 1:1 candidates:negatives.

    Re-counted from the EMITTED side-car rather than from the request, because
    `SamplingFrame` silently draws `min(n, len(stratum))`: an exhausted
    stratum turns a 1:1 request into whatever fitted, which is exactly how the
    shipped sample came to be 1:2 against its own README.
    """
    cells = {}
    for pid, rec in sidecar.get("passages", {}).items():
        key = f"{rec['behaviour']}/{rec['spec']}"
        c = cells.setdefault(key, {"candidate": 0, "negative": 0})
        c["candidate" if rec["origin"] == "candidate" else "negative"] += 1
    out = []
    for key, c in sorted(cells.items()):
        if c["candidate"] != c["negative"]:
            out.append(
                f"sampling: cell {key} emitted {c['candidate']} candidate(s) "
                f"and {c['negative']} negative(s); CONFLICT_PANEL_README.md "
                f"states and argues for 1:1 (it is the composition a judge who "
                f"guesses the mix learns least from). A stratum was smaller "
                f"than the draw requested -- lower --candidates or raise "
                f"--near-pool")
    return out


def _check_adjacent(judging: dict) -> list:
    """`adjacent` must not separate candidates from negatives.

    It is emitted constant-False; if that ever stops being true the field
    becomes a tell that a human judge can read straight off the JSON, and the
    blinding this module exists to preserve is gone.
    """
    vals = {p["adjacent"] for b in judging["behaviours"]
            for cov in b["coverage"].values() for p in cov["passages"]}
    if len(vals) > 1:
        return ["passages: `adjacent` takes more than one value in this file; "
                "in the emitter it is True only on tool candidates, so a human "
                "judge could separate candidates from negatives by eye. It "
                "must be constant across the file"]
    return []


def build(conducts: dict, adapter: Adapter = None, *, panel=None,
          seed: int = co.DEFAULT_SEED, run_date: str = None,
          near_pool: int = DEFAULT_NEAR_POOL, clauses_path: str = CLAUSES_JSON,
          generated_from=None, sources: dict = None):
    """`(judging_copy, side_car)` for a whole set of conducts.

    Deterministic given `(conducts, artifacts, seed, run_date)`: the ranking is
    arithmetic and the negative draw is seeded per (seed, behaviour, spec).
    """
    adapter = adapter or Adapter.from_files()
    roster = list(panel if panel is not None else DEFAULT_PANEL)
    pool = co.load_clause_pool(adapter.spec, clauses_path)

    runs, pairs = {}, []
    for slug in sorted(conducts):
        conduct = conducts[slug]
        findings, sub, stats = adapter.findings_for(slug, conduct)
        if not findings:
            raise ValueError(
                f"{slug}: the tool ranked no clause at or above threshold "
                f"{adapter.threshold} for this conduct, so there is nothing to "
                f"judge. Lower --threshold or check the conduct text is "
                f"describing what the assistant did")
        n_near, n_field = split_negatives(len(findings))
        frame = co.SamplingFrame(
            rows=[dict(r, toolScore=sub.get(r["clauseId"])) for r in pool],
            n_near=n_near, n_field=n_field, near_pool=near_pool, seed=seed)
        stats["negativesRequested"] = {"near": n_near, "field": n_field}
        stats["nearPoolCap"] = near_pool
        runs[slug] = stats
        pairs.append(co.emit_pair(
            findings, conduct={slug: conduct}, panel=roster, negatives=frame,
            run_date=run_date,
            generated_from=list(generated_from or [
                "conflict_adapter.py over modelspec_clauses.json",
                "how these passages were selected is recorded in the side-car, "
                "not here"]),
            coverage_notes={slug: {adapter.spec: {
                "verdict": "pending", "depth": None, "verifiedDate": None,
                "note": "conflict panel input; per-judge slots empty for the "
                        "panel to fill"}}}))

    judging, side = _merge_pairs(pairs)
    side["generatedFrom"] = [
        "conflict_output.emit_pair() over modelspec_clauses.json",
        "candidates: relevance.RelevanceIndex.rank() over the CONDUCT text "
        "(conflict_adapter.py) -- a RELEVANCE ranking, not a violation model",
        "near-miss stratum: the tool's own sub-threshold ranking for the same "
        "conduct (NOT a keyword stand-in)",
    ]
    side["scoreMeaning"] = copy.deepcopy(SCORE_MEANING)
    side["tool"] = {
        "module": "conflict_adapter.py",
        "ranker": "relevance.RelevanceIndex.rank()",
        "atomMode": adapter.atom_mode,
        "threshold": adapter.threshold,
        "candidatesPerCell": adapter.n_candidates,
        "nearPoolCap": near_pool,
        "weights": vars(adapter.index.weights),
        "sources": dict(sources or {}),
        "runs": runs,
        "queryNote": ("the lexical query is the CONDUCT text alone; the "
                      "behaviour's name and abstract definition are not in it"),
        "offline": ("no model call at query time; ranking is arithmetic over "
                    "modelspec_clauses.json + the annotation artifacts"),
    }
    return judging, side


def check(judging: dict, side: dict, *, check_spec: bool = True) -> list:
    """Everything that must hold before either file is written."""
    errs = [f"<judging> {m}" for m in
            co.validate(judging, mode="input", check_spec=check_spec)]
    errs += [f"<sidecar> {m}" for m in co.validate_sidecar(side, judging)]
    errs += [f"<pair> {m}" for m in _check_ratio(side)]
    errs += [f"<pair> {m}" for m in _check_adjacent(judging)]
    return errs


# ---- cli -------------------------------------------------------------------

def _summary(judging: dict, side: dict) -> str:
    lines = []
    for b in judging["behaviours"]:
        for spec, cov in b["coverage"].items():
            ids = [p["id"] for p in cov["passages"]]
            recs = [side["passages"][i] for i in ids]
            cands = sum(1 for r in recs if r["origin"] == "candidate")
            near = sum(1 for r in recs if r["origin"] == "negative-near")
            fld = sum(1 for r in recs if r["origin"] == "negative-field")
            frame = side["sampling"]["frames"].get(f"{b['slug']}/{spec}", {})
            p_near = (frame.get("negative-near") or {}).get(
                "inclusionProbability", 0.0)
            p_field = (frame.get("negative-field") or {}).get(
                "inclusionProbability", 0.0)
            lines.append(
                f"  {b['slug']}/{spec}: {len(ids)} passages "
                f"({cands} candidates, {near} near @p={p_near:.3f}, "
                f"{fld} field @p={p_field:.3f})")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Build a blinded conflict-panel input file and its "
                    "side-car from a real (offline) tool run.",
        epilog="The conflict score is a RELEVANCE score; see the module "
               "docstring before drawing conclusions from the panel.")
    ap.add_argument("--conduct-file",
                    help="JSON {behaviour slug: conduct sentence(s)}")
    ap.add_argument("--conduct", action="append", default=[],
                    metavar="SLUG=TEXT",
                    help="a conduct inline; repeatable")
    ap.add_argument("--out", default=None,
                    help="the BLINDED judging copy to write")
    ap.add_argument("--sidecar", default=None,
                    help="the side-car (never show it to a judge)")
    ap.add_argument("--seed", type=int, default=co.DEFAULT_SEED)
    ap.add_argument("--candidates", type=int, default=DEFAULT_CANDIDATES,
                    help=f"candidates per cell (default {DEFAULT_CANDIDATES}); "
                         f"an equal number of negatives is drawn")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    ap.add_argument("--near-pool", type=int, default=DEFAULT_NEAR_POOL,
                    help="size of the sub-threshold near-miss band")
    ap.add_argument("--atom-channel", default=DEFAULT_ATOM_MODE,
                    choices=ATOM_MODES,
                    help="conduct = behaviour atoms the conduct's own words "
                         "support (default); behaviour = all of them, which "
                         "makes the list conduct-invariant; off = lexical only")
    ap.add_argument("--clauses", default=CLAUSES_JSON)
    ap.add_argument("--annotations", default=ANNOTATIONS_JSON)
    ap.add_argument("--behaviour-atoms", default=BEHAVIOUR_ATOMS_JSON)
    ap.add_argument("--judges", default=None,
                    help="JSON list of judge objects; default is the relevance "
                         "panel's model trio")
    ap.add_argument("--run-date", default=None,
                    help="YYYY-MM-DD recorded in both files (default: today)")
    ap.add_argument("--dry-run", action="store_true",
                    help="build and validate, write nothing")
    args = ap.parse_args(argv)

    conducts = {}
    if args.conduct_file:
        conducts.update(load_conducts(args.conduct_file))
    for item in args.conduct:
        if "=" not in item:
            print(f"--conduct expects SLUG=TEXT, got {item!r}", file=sys.stderr)
            return 2
        slug, text = item.split("=", 1)
        conducts[slug.strip()] = text.strip()
    if not conducts:
        print("nothing to do: pass --conduct-file FILE or --conduct SLUG=TEXT",
              file=sys.stderr)
        return 2
    if not args.dry_run and not (args.out and args.sidecar):
        print("--out and --sidecar are both required (the judging copy is "
              "useless without the side-car that scores it); or use --dry-run",
              file=sys.stderr)
        return 2

    known = {b["slug"] for b in co.load_behaviour_metadata()}
    unknown = sorted(set(conducts) - known)
    if unknown:
        print(f"unknown behaviour slug(s) {unknown}; the reference panel "
              f"defines {sorted(known)}", file=sys.stderr)
        return 2

    if not args.judges:
        print("NOTE: using the default roster (Sol / Kimi-K3 / Fable 5, "
              "kind=model). Who judges is part of the instrument -- pass "
              "--judges FILE if this panel is judged by humans, and decide it "
              "BEFORE collecting, not after.", file=sys.stderr)

    adapter = Adapter.from_files(
        clauses_path=args.clauses, annotations_path=args.annotations,
        behaviour_atoms_path=args.behaviour_atoms,
        threshold=args.threshold, n_candidates=args.candidates,
        atom_mode=args.atom_channel)
    run_date = args.run_date or datetime.date.today().isoformat()
    judging, side = build(
        conducts, adapter, panel=load_panel(args.judges), seed=args.seed,
        run_date=run_date, near_pool=args.near_pool, clauses_path=args.clauses,
        sources={k: {"path": os.path.basename(p), "sha256": file_digest(p)}
                 for k, p in (("clauses", args.clauses),
                              ("annotations", args.annotations),
                              ("behaviourAtoms", args.behaviour_atoms))
                 if os.path.exists(p)})

    errs = check(judging, side)
    if errs:
        print(f"{len(errs)} problem(s); NOTHING WRITTEN:")
        for m in errs[:40]:
            print(f"  - {m}")
        if len(errs) > 40:
            print(f"  ... and {len(errs) - 40} more")
        return 1

    print(f"seed {args.seed}, run date {run_date}, atom channel "
          f"{args.atom_channel}, threshold {args.threshold:g}")
    print(_summary(judging, side))
    print("conflictScore is a RELEVANCE score: the panel measures precision "
          "of a relevance-ranked list judged for conflict, not the accuracy "
          "of a conflict detector (see conflict_adapter.__doc__).")
    if args.dry_run:
        print("--dry-run: validated, nothing written")
        return 0
    co.write(args.out, judging)
    co.write(args.sidecar, side)
    print(f"wrote {args.out} (blinded judging copy) and {args.sidecar} "
          f"(NEVER show this to a judge)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
