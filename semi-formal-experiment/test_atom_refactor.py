"""Tests for atom_refactor.py — rename / merge / split with migrations (Unit 3).

What is being pinned, and why each pin exists:

  * FIND-REFERENCES IS COMPLETE — `usages` must see every surface an atom
    name lives on: annotations (atoms list, by_clause, the vocabulary KEY),
    behavior_atoms* query configs, golden_translations entries, containment
    edges (child AND parent), behaviours_query if it ever carries atoms. A
    surface it cannot see is a surface a rename silently breaks.
  * STEM-LEVEL IDENTITY — a usage of `mustnot_X__model_user` IS a usage of
    stem X (grammar.stem_of is the join key), and a rewrite preserves the
    decoration: only the stem moves. Names whose stem differs are the
    IDENTITY under rewrite — pinned over the real b8 vocabulary, stem_of
    style, because rewriting an unrelated join key is the invisible failure.
  * DRY-RUN BY DEFAULT — a migration tool that writes on its happy path is
    one typo away from corrupting ten artifacts. Nothing on disk moves, and
    no log entry appears, unless --apply / apply=True is passed.
  * THE LOG IS THE CONTRACT — every applied migration appends one entry to
    vocabulary_migrations.json with op/old/new/date/reason and per-artifact
    sha before/after. `replay` applies the log in order to an OLD copy and
    must reproduce the CURRENT bytes — that is backwards compatibility as a
    testable property, not a promise.
  * DETERMINISM — the date is caller-supplied (--date), never wall clock,
    so the same migration applied twice yields byte-identical artifacts and
    log entries (sandwich rule leg 1).
  * GOLDEN STAYS FROZEN — a migration touching golden_translations.json
    re-freezes its sha (golden.load must succeed afterwards) and appends a
    review record to each touched entry following the file's own in-file
    convention. An unrecorded edit to the reference is exactly what
    golden.py exists to prevent.
  * SPLIT IS NOT MECHANICAL — it emits a per-usage worklist (clause text +
    gloss + quote, stable ids, closed assignment vocabulary) and only a
    complete, validated worklist applies: full coverage, no dupes, no
    unknown ids, assignments from the closed set, and CONSISTENT assignment
    for the same underlying record (atoms[] vs by_clause mirror). Mirrors
    dossier.py's validate discipline, one named test per violation class.
  * REFUSALS ARE NAMED — rename onto an existing name, merge into a missing
    destination, an artifact whose bytes this tool cannot reproduce
    canonically, and a merge that would collapse a containment edge into a
    self-loop each raise their own exception class.
  * PANEL-BLIND — this module's own source is held to the same FORBIDDEN
    static scan as the query modules, even though it is a maintenance tool
    and not in QUERY_MODULES.

All fixtures are synthetic and tiny, built in tmp_path with the repo's real
serialization (indent=1, ensure_ascii=False) so byte-level pins are honest.
"""
from __future__ import annotations

import copy
import difflib
import json
import os
import re

import pytest

import atom_refactor as ar
import golden
import grammar

HERE = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------- fixtures

def _wjson(path, obj, trailing_nl=False):
    blob = json.dumps(obj, indent=1, ensure_ascii=False)
    if trailing_nl:
        blob += "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(blob)
    return str(path)


def _atom(name, span, quote, cid):
    return {"name": name, "kind": "act", "gloss": f"gloss of {name}",
            "span_id": span, "quote": quote, "clause_id": cid,
            "locator": f"spec > {cid}"}


def _vocab(kind, clauses):
    return {"kind": kind, "gloss": "g", "n_clauses": len(clauses),
            "clauses": list(clauses)}


@pytest.fixture
def root(tmp_path):
    """A miniature repo: every usage surface carries the stem `deceive_user`
    somewhere — bare, polarity-decorated, and as a containment child."""
    a0 = _atom("helping_user", "s1", "q one", "m0001")
    a1 = _atom("mustnot_deceive_user__model_user", "s2", "q two", "m0001")
    a2 = _atom("deceive_user", "s3", "q three", "m0002")
    a3 = _atom("user_task", "s4", "q four", "m0002")
    ann = {
        "warnings": [],
        "provenance": {"model": "hand", "created": "fixed"},
        "atoms": [a0, a1, a2, a3],
        "by_clause": {"m0001": [copy.deepcopy(a0), copy.deepcopy(a1)],
                      "m0002": [copy.deepcopy(a2), copy.deepcopy(a3)]},
        "vocabulary": {
            "helping_user": _vocab("act", ["m0001"]),
            "mustnot_deceive_user__model_user": _vocab("act", ["m0001"]),
            "deceive_user": _vocab("act", ["m0002"]),
            "user_task": _vocab("situation", ["m0002"]),
        },
    }
    _wjson(tmp_path / "annotations.json", ann)

    batoms = {
        "beh1": {"atoms": [
            {"name": "deceive_user", "kind": "act", "gloss": "g",
             "weight": 2, "source": "definition", "new": False},
            {"name": "helping_user", "kind": "act", "gloss": "g",
             "weight": 1, "source": "definition", "new": False},
        ]},
        "provenance": {"model": "hand"},
        "_warnings": [],
    }
    _wjson(tmp_path / "behavior_atoms_b8.json", batoms)

    gpayload = {
        "artifact": "golden_translations",
        "version": 1,
        "spec": "toy@1",
        "split": {"dev": ["m0001"], "held_out": ["m0002"]},
        "entries": [
            {"clause_id": "m0001", "locator": "spec > m0001",
             "quote": "clause one full text", "split": "dev",
             "atoms": [
                 {"name": "mustnot_deceive_user__model_user", "kind": "act",
                  "gloss": "does not deceive", "span_id": "s2",
                  "role": "consequent", "quote": "q two"}]},
            {"clause_id": "m0002", "locator": "spec > m0002",
             "quote": "clause two full text", "split": "held_out",
             "atoms": [
                 {"name": "user_task", "kind": "situation",
                  "gloss": "a task", "span_id": "s4", "quote": "q four"}]},
        ],
    }
    gpayload["sha256"] = golden.compute_sha256(gpayload)
    _wjson(tmp_path / "golden_translations.json", gpayload)

    cont = {
        "artifact": "containment",
        "version": 1,
        "edges": [
            {"child": "deceive_user", "parent": "deception",
             "license": "shared_head", "note": "toy edge"},
            {"child": "trick_user", "parent": "deception",
             "license": "shared_head", "note": "toy sibling"},
        ],
        "provenance": {"date": "2026-08-03"},
    }
    _wjson(tmp_path / "containment.json", cont, trailing_nl=True)

    _wjson(tmp_path / "behaviours_query.json",
           {"_comment": "toy", "behaviours": [
               {"slug": "beh1", "name": "B", "definition": "d"}]})
    return str(tmp_path)


def _read_bytes(root_dir, name):
    with open(os.path.join(root_dir, name), "rb") as f:
        return f.read()


def _read_json(root_dir, name):
    with open(os.path.join(root_dir, name), encoding="utf-8") as f:
        return json.load(f)


def _snapshot_all(root_dir):
    return {n: _read_bytes(root_dir, n) for n in sorted(os.listdir(root_dir))
            if n.endswith(".json")}


# ------------------------------------------------------------------ usages

def test_usages_finds_every_surface(root):
    got = ar.find_usages("deceive_user", root=root)
    locs = {(u["file"], u["location"]) for u in got}
    assert ("annotations.json", "atoms[1]") in locs
    assert ("annotations.json", "atoms[2]") in locs
    assert ("annotations.json", "by_clause.m0001[1]") in locs
    assert ("annotations.json", "by_clause.m0002[0]") in locs
    assert ("annotations.json",
            "vocabulary.mustnot_deceive_user__model_user") in locs
    assert ("annotations.json", "vocabulary.deceive_user") in locs
    assert ("behavior_atoms_b8.json", "beh1.atoms[0]") in locs
    assert ("golden_translations.json", "entries[0].atoms[0]") in locs
    assert ("containment.json", "edges[0].child") in locs
    assert len(got) == 9


def test_usages_reports_exact_vs_stem(root):
    got = ar.find_usages("deceive_user", root=root)
    by_loc = {u["location"]: u for u in got}
    assert by_loc["atoms[2]"]["match"] == "exact"
    assert by_loc["atoms[1]"]["match"] == "stem"
    assert by_loc["atoms[1]"]["name"] == "mustnot_deceive_user__model_user"
    assert all(u["stem"] == "deceive_user" for u in got)


def test_usages_of_a_decorated_name_are_stem_level(root):
    got = ar.find_usages("mustnot_deceive_user__model_user", root=root)
    assert len(got) == 9  # same stem family
    exact = [u for u in got if u["match"] == "exact"]
    assert {u["location"] for u in exact} == {
        "atoms[1]", "by_clause.m0001[1]",
        "vocabulary.mustnot_deceive_user__model_user", "entries[0].atoms[0]"}


def test_usages_sees_parent_side_of_edges(root):
    got = ar.find_usages("deception", root=root)
    locs = {u["location"] for u in got}
    assert locs == {"edges[0].parent", "edges[1].parent"}


# --------------------------------------------------------------- rewrite

def test_rewrite_name_moves_only_the_stem():
    assert ar.rewrite_name("deceive_user", "deceive_user",
                           "mislead_user") == "mislead_user"
    assert (ar.rewrite_name("mustnot_deceive_user__model_user",
                            "deceive_user", "mislead_user")
            == "mustnot_mislead_user__model_user")


def test_rewrite_name_is_identity_on_unrelated_names(root):
    for name in ("helping_user", "user_task", "mustnot_other__model",
                 "must_"):  # last one is unparseable — never rewritten
        assert ar.rewrite_name(name, "deceive_user", "mislead_user") == name


def test_rewrite_identity_over_the_real_b8_vocabulary():
    """stem_of-style pin on the REAL artifact: a rename of a stem nobody
    uses touches zero shipped names."""
    path = os.path.join(HERE, "annotations_b8.json")
    if not os.path.exists(path):
        pytest.skip("real artifact not present")
    with open(path, encoding="utf-8") as f:
        vocab = json.load(f)["vocabulary"]
    for name in vocab:
        assert ar.rewrite_name(name, "zzz_unused_stem", "q") == name


# ---------------------------------------------------------------- rename

def test_rename_is_dry_run_by_default(root):
    before = _snapshot_all(root)
    rc = ar.main(["rename", "deceive_user", "mislead_user",
                  "--date", "2026-08-03", "--reason", "clearer stem",
                  "--root", root])
    assert rc == 0
    assert _snapshot_all(root) == before
    assert not os.path.exists(os.path.join(root,
                                           "vocabulary_migrations.json"))


def test_rename_apply_rewrites_every_usage(root):
    rc = ar.main(["rename", "deceive_user", "mislead_user",
                  "--date", "2026-08-03", "--reason", "clearer stem",
                  "--root", root, "--apply"])
    assert rc == 0
    assert ar.find_usages("deceive_user", root=root) == []
    got = ar.find_usages("mislead_user", root=root)
    assert len(got) == 9
    ann = _read_json(root, "annotations.json")
    assert ann["atoms"][1]["name"] == "mustnot_mislead_user__model_user"
    assert ann["atoms"][2]["name"] == "mislead_user"
    assert "mislead_user" in ann["vocabulary"]
    assert "mustnot_mislead_user__model_user" in ann["vocabulary"]
    cont = _read_json(root, "containment.json")
    assert cont["edges"][0]["child"] == "mislead_user"


def test_rename_leaves_unrelated_lines_byte_untouched(root):
    before = _snapshot_all(root)
    ar.main(["rename", "deceive_user", "mislead_user",
             "--date", "2026-08-03", "--reason", "clearer stem",
             "--root", root, "--apply"])
    after = _snapshot_all(root)
    for name in before:
        if name == "vocabulary_migrations.json":
            continue
        old = before[name].decode("utf-8").splitlines()
        new = after[name].decode("utf-8").splitlines()
        changed = [l for l in difflib.unified_diff(old, new, lineterm="", n=0)
                   if l[:1] in "+-" and l[:3] not in ("+++", "---")]
        for line in changed:
            assert ("deceive_user" in line or "mislead_user" in line
                    or '"sha256"' in line
                    # golden's appended review block, and the lines JSON
                    # re-punctuates around the insertion point:
                    or name == "golden_translations.json"), (
                f"{name}: unrelated line changed: {line!r}")


def test_rename_appends_a_replayable_log_entry(root):
    shas_before = {n: ar.sha256_bytes(b)
                   for n, b in _snapshot_all(root).items()}
    ar.main(["rename", "deceive_user", "mislead_user",
             "--date", "2026-08-03", "--reason", "clearer stem",
             "--root", root, "--apply"])
    log = _read_json(root, "vocabulary_migrations.json")
    assert log["artifact"] == "vocabulary_migrations"
    assert len(log["migrations"]) == 1
    e = log["migrations"][0]
    assert e["op"] == "rename"
    assert e["old"] == "deceive_user" and e["new"] == "mislead_user"
    assert e["date"] == "2026-08-03"
    assert e["reason"] == "clearer stem"
    touched = e["artifacts"]
    assert set(touched) == {"annotations.json", "behavior_atoms_b8.json",
                            "golden_translations.json", "containment.json"}
    for name, rec in touched.items():
        assert rec["sha_before"] == shas_before[name]
        assert rec["sha_after"] == ar.sha256_bytes(_read_bytes(root, name))
        assert rec["n_rewritten"] > 0


def test_rename_refuses_existing_target(root):
    with pytest.raises(ar.NameExistsError):
        ar.plan_migration(root, "rename", "deceive_user", "helping_user",
                          date="2026-08-03", reason="r")


def test_rename_refuses_unknown_source(root):
    with pytest.raises(ar.UnknownAtomError):
        ar.plan_migration(root, "rename", "never_written", "x",
                          date="2026-08-03", reason="r")


def test_rename_refuses_decorated_arguments(root):
    with pytest.raises(ar.NotAStemError):
        ar.plan_migration(root, "rename", "mustnot_deceive_user__model_user",
                          "x", date="2026-08-03", reason="r")
    with pytest.raises(ar.NotAStemError):
        ar.plan_migration(root, "rename", "deceive_user", "must_x",
                          date="2026-08-03", reason="r")


def test_rename_requires_a_reason_and_a_date(root):
    with pytest.raises(SystemExit):
        ar.main(["rename", "deceive_user", "mislead_user", "--root", root,
                 "--date", "2026-08-03"])
    with pytest.raises(SystemExit):
        ar.main(["rename", "deceive_user", "mislead_user", "--root", root,
                 "--reason", "r"])
    with pytest.raises(ar.RefactorError):
        ar.plan_migration(root, "rename", "deceive_user", "mislead_user",
                          date="today", reason="r")  # wall-clock words ≠ date


def test_rename_refuses_a_non_canonical_artifact(root):
    path = os.path.join(root, "annotations.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)  # not the repo serialization
    with pytest.raises(ar.NonCanonicalArtifactError):
        ar.plan_migration(root, "rename", "deceive_user", "mislead_user",
                          date="2026-08-03", reason="r")


# ----------------------------------------------------------------- merge

def test_merge_requires_destination_exists(root):
    with pytest.raises(ar.UnknownAtomError):
        ar.plan_migration(root, "merge", "deceive_user", "never_written",
                          date="2026-08-03", reason="r")


def test_merge_rewrites_and_unions_vocabulary(root):
    ar.main(["merge", "helping_user", "user_task",
             "--date", "2026-08-03", "--reason", "same concept",
             "--root", root, "--apply"])
    ann = _read_json(root, "annotations.json")
    assert "helping_user" not in ann["vocabulary"]
    v = ann["vocabulary"]["user_task"]
    assert v["clauses"] == ["m0001", "m0002"]
    assert v["n_clauses"] == 2
    # the DESTINATION's kind survives the union, not the source's
    assert v["kind"] == "situation"
    assert ar.find_usages("helping_user", root=root) == []
    log = _read_json(root, "vocabulary_migrations.json")
    assert log["migrations"][0]["op"] == "merge"


def test_merge_refuses_a_self_looping_edge(root):
    # deceive_user ⊑ deception; merging child into parent would leave
    # deception ⊑ deception, which no mechanical rewrite may create.
    with pytest.raises(ar.EdgeConflictError):
        ar.plan_migration(root, "merge", "deceive_user", "deception",
                          date="2026-08-03", reason="r")


def test_merge_refuses_a_duplicate_edge(root):
    # deceive_user and trick_user both ⊑ deception: merging one into the
    # other would leave two identical edges.
    with pytest.raises(ar.EdgeConflictError):
        ar.plan_migration(root, "merge", "deceive_user", "trick_user",
                          date="2026-08-03", reason="r")


# ---------------------------------------------------------------- golden

def test_golden_is_refrozen_and_review_appended(root):
    ar.main(["rename", "deceive_user", "mislead_user",
             "--date", "2026-08-03", "--reason", "clearer stem",
             "--root", root, "--apply"])
    g = golden.load(os.path.join(root, "golden_translations.json"))
    e0 = g.entries[0]
    assert (e0["atoms"][0]["name"]
            == "mustnot_mislead_user__model_user")
    assert "review" in e0, "touched entry got no review record"
    rec = e0["review"][-1]
    assert set(rec) >= {"by", "change", "why"}
    assert "atom_refactor" in rec["by"]
    assert "deceive_user" in rec["change"] and "mislead_user" in rec["change"]
    assert rec["why"] == "clearer stem"
    # the UNtouched entry gains nothing
    assert "review" not in g.entries[1]


def test_migration_is_deterministic(root, tmp_path_factory):
    """Same fixture, same migration, byte-identical results — no wall clock
    anywhere in the write path."""
    import shutil
    clone = str(tmp_path_factory.mktemp("clone"))
    for n in os.listdir(root):
        shutil.copy(os.path.join(root, n), os.path.join(clone, n))
    args = ["rename", "deceive_user", "mislead_user",
            "--date", "2026-08-03", "--reason", "clearer stem", "--apply"]
    ar.main(args + ["--root", root])
    ar.main(args + ["--root", clone])
    assert _snapshot_all(root) == _snapshot_all(clone)


# ---------------------------------------------------------------- replay

def test_replay_reproduces_current_bytes(root):
    old_ann = _read_bytes(root, "annotations.json")
    old_gold = _read_bytes(root, "golden_translations.json")
    old_cont = _read_bytes(root, "containment.json")
    keep = os.path.join(root, "old_copies")
    os.makedirs(keep)
    for name, blob in (("ann.json", old_ann), ("gold.json", old_gold),
                       ("cont.json", old_cont)):
        with open(os.path.join(keep, name), "wb") as f:
            f.write(blob)
    ar.main(["rename", "deceive_user", "mislead_user",
             "--date", "2026-08-03", "--reason", "clearer stem",
             "--root", root, "--apply"])
    ar.main(["merge", "helping_user", "user_task",
             "--date", "2026-08-04", "--reason", "same concept",
             "--root", root, "--apply"])
    log = os.path.join(root, "vocabulary_migrations.json")
    for name, current in (("ann.json", "annotations.json"),
                          ("gold.json", "golden_translations.json"),
                          ("cont.json", "containment.json")):
        migrated = ar.replay_artifact(os.path.join(keep, name), log)
        assert migrated == _read_bytes(root, current), (
            f"replaying {name} through the log does not reproduce the "
            f"current {current}")


def test_replay_cli_writes_the_migrated_copy(root, capsys):
    old = os.path.join(root, "old_ann.json")
    with open(old, "wb") as f:
        f.write(_read_bytes(root, "annotations.json"))
    ar.main(["rename", "deceive_user", "mislead_user",
             "--date", "2026-08-03", "--reason", "clearer stem",
             "--root", root, "--apply"])
    out = os.path.join(root, "replayed.json")
    rc = ar.main(["replay", old, "--root", root, "--out", out])
    assert rc == 0
    with open(out, "rb") as f:
        assert f.read() == _read_bytes(root, "annotations.json")


# ----------------------------------------------------------------- split

def _worklist(root):
    out = os.path.join(root, "wl.json")
    rc = ar.main(["split", "deceive_user", "mislead_user,withhold_info",
                  "--root", root, "--out", out])
    assert rc == 0
    with open(out, encoding="utf-8") as f:
        return json.load(f), out


ASSIGN = {  # by location; m0001 family → mislead, m0002 → withhold
    "annotations.json#atoms[1]": "mislead_user",
    "annotations.json#by_clause.m0001[1]": "mislead_user",
    "annotations.json#atoms[2]": "withhold_info",
    "annotations.json#by_clause.m0002[0]": "withhold_info",
    "behavior_atoms_b8.json#beh1.atoms[0]": "withhold_info",
    "golden_translations.json#entries[0].atoms[0]": "mislead_user",
    "containment.json#edges[0].child": "mislead_user",
}


def _fill(wl, assign=ASSIGN):
    for u in wl["usages"]:
        u["assign"] = assign.get(u["usage_id"], u.get("assign"))
    return wl


def test_split_emits_a_complete_worklist(root):
    wl, _ = _worklist(root)
    assert wl["artifact"] == "split_worklist"
    assert wl["atom"] == "deceive_user"
    assert wl["into"] == ["mislead_user", "withhold_info"]
    ids = [u["usage_id"] for u in wl["usages"]]
    assert sorted(ids) == sorted(ASSIGN)  # vocabulary keys are EXCLUDED
    assert len(ids) == len(set(ids))
    for u in wl["usages"]:
        assert u["assign"] is None  # judgment not pre-filled
        assert u["name"], u
    # the judgment interface carries what the brief needs: text, gloss, quote
    by_id = {u["usage_id"]: u for u in wl["usages"]}
    g = by_id["golden_translations.json#entries[0].atoms[0]"]
    assert g["clause_text"] == "clause one full text"
    assert g["gloss"] == "does not deceive"
    assert g["quote"] == "q two"
    a = by_id["annotations.json#atoms[1]"]
    assert a["gloss"] and a["quote"] and a["clause_id"] == "m0001"


def test_split_refuses_colliding_targets(root):
    with pytest.raises(ar.NameExistsError):
        ar.build_worklist(root, "deceive_user",
                          ["helping_user", "withhold_info"])
    with pytest.raises(ar.RefactorError):
        ar.build_worklist(root, "deceive_user", ["same", "same"])


def test_split_apply_refuses_incomplete_worklist(root):
    wl, path = _worklist(root)
    _fill(wl)
    wl["usages"][0]["assign"] = None
    _wjson(path, wl)
    before = _snapshot_all(root)
    rc = ar.main(["split-apply", "--worklist", path, "--root", root,
                  "--date", "2026-08-03", "--reason", "r", "--apply"])
    assert rc != 0
    assert _snapshot_all(root) == before


def test_split_apply_refuses_unknown_and_duplicate_ids(root):
    wl, path = _worklist(root)
    _fill(wl)
    wl["usages"].append(dict(wl["usages"][0]))  # duplicate
    _wjson(path, wl)
    ok, summary = ar.validate_worklist(root, wl)
    assert not ok and summary["duplicated"]
    wl, path = _worklist(root)
    _fill(wl)
    wl["usages"][0]["usage_id"] = "nowhere.json#atoms[9]"
    ok, summary = ar.validate_worklist(root, wl)
    assert not ok and summary["unknown"] and summary["never_assigned"]


def test_split_apply_refuses_assignment_outside_the_closed_set(root):
    wl, path = _worklist(root)
    _fill(wl)
    wl["usages"][0]["assign"] = "some_third_thing"
    ok, summary = ar.validate_worklist(root, wl)
    assert not ok and summary["bad_target"]


def test_split_apply_refuses_inconsistent_mirror_assignments(root):
    # atoms[1] and by_clause.m0001[1] are the SAME record (clause m0001,
    # span s2) — assigning them different halves is a contradiction.
    wl, path = _worklist(root)
    _fill(wl)
    for u in wl["usages"]:
        if u["usage_id"] == "annotations.json#by_clause.m0001[1]":
            u["assign"] = "withhold_info"
    ok, summary = ar.validate_worklist(root, wl)
    assert not ok and summary["inconsistent"]


def test_split_apply_applies_a_valid_worklist(root):
    wl, path = _worklist(root)
    _fill(wl)
    _wjson(path, wl)
    rc = ar.main(["split-apply", "--worklist", path, "--root", root,
                  "--date", "2026-08-03", "--reason", "two concepts",
                  "--apply"])
    assert rc == 0
    assert ar.find_usages("deceive_user", root=root) == []
    ann = _read_json(root, "annotations.json")
    assert ann["atoms"][1]["name"] == "mustnot_mislead_user__model_user"
    assert ann["atoms"][2]["name"] == "withhold_info"
    # the vocabulary is REBUILT: decorated key follows its clause's half,
    # the bare key follows the other half, no stale key survives
    assert "deceive_user" not in ann["vocabulary"]
    assert "mustnot_deceive_user__model_user" not in ann["vocabulary"]
    assert ann["vocabulary"]["mustnot_mislead_user__model_user"][
        "clauses"] == ["m0001"]
    assert ann["vocabulary"]["withhold_info"]["clauses"] == ["m0002"]
    cont = _read_json(root, "containment.json")
    assert cont["edges"][0]["child"] == "mislead_user"
    g = golden.load(os.path.join(root, "golden_translations.json"))
    assert g.entries[0]["atoms"][0]["name"] == \
        "mustnot_mislead_user__model_user"
    log = _read_json(root, "vocabulary_migrations.json")
    e = log["migrations"][0]
    assert e["op"] == "split"
    assert e["new"] == ["mislead_user", "withhold_info"]
    assert e["assignments"]["containment.json"]["edges[0].child"] == \
        "mislead_user"


def test_split_replays(root):
    old = os.path.join(root, "old_ann.json")
    with open(old, "wb") as f:
        f.write(_read_bytes(root, "annotations.json"))
    wl, path = _worklist(root)
    _fill(wl)
    _wjson(path, wl)
    ar.main(["split-apply", "--worklist", path, "--root", root,
             "--date", "2026-08-03", "--reason", "two concepts", "--apply"])
    log = os.path.join(root, "vocabulary_migrations.json")
    migrated = ar.replay_artifact(old, log, as_rel="annotations.json")
    assert migrated == _read_bytes(root, "annotations.json")


def test_split_apply_is_dry_run_by_default(root):
    wl, path = _worklist(root)
    _fill(wl)
    _wjson(path, wl)
    before = _snapshot_all(root)
    rc = ar.main(["split-apply", "--worklist", path, "--root", root,
                  "--date", "2026-08-03", "--reason", "two concepts"])
    assert rc == 0
    assert _snapshot_all(root) == before


# ------------------------------------------------------------ panel fence

def test_atom_refactor_source_is_panel_blind():
    """The same FORBIDDEN scan the query modules face, applied to this
    maintenance tool's own source — it is not in QUERY_MODULES (it answers
    no query), but nothing in it may name the panel either."""
    import inspect
    from test_no_reference_leak import FORBIDDEN
    src = inspect.getsource(ar)
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r"#.*", "", src)
    hits = [tok for tok in FORBIDDEN if tok in src]
    assert not hits, f"atom_refactor.py names the panel: {hits}"


def test_atom_refactor_reads_only_its_declared_surfaces(root):
    """No file outside the surface list + clause corpora is ever opened by a
    scan — above all not any panel artifact."""
    opened = []
    real_open = open

    import builtins
    def spy(path, *a, **kw):
        opened.append(os.path.basename(str(path)))
        return real_open(path, *a, **kw)
    builtins.open = spy
    try:
        ar.find_usages("deceive_user", root=root)
    finally:
        builtins.open = real_open
    allowed = set(ar.surface_paths(root)) | set(ar.CLAUSE_CORPORA)
    assert set(opened) <= allowed, sorted(set(opened) - allowed)
