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


# ----------------------------------------------- ext_v1 surfaces + rechain

LONG = "shouldnot_judge__model_user_developer"
SHORT = "shouldnot_judge__model_user"
HELP_OLD = "must_advise_immediate_help__user"
HELP_NEW = "must_advise_immediate_help__model_user"


def _wjson_style(path, obj, ensure_ascii=False):
    blob = json.dumps(obj, indent=1, ensure_ascii=ensure_ascii)
    with open(path, "w", encoding="utf-8") as f:
        f.write(blob)
    return str(path)


def _ext_ann():
    a0 = _atom(LONG, "s1", "q one — with a dash", "m0170")
    a1 = _atom(LONG, "s2", "q two", "m0271")
    a2 = _atom(SHORT, "s3", "q three", "m0289")
    a3 = _atom(HELP_OLD, "s4", "q four", "m0276")
    a4 = _atom("helping_user", "s5", "q five", "m0170")
    return {
        "warnings": [],
        "provenance": {"model": "hand", "created": "fixed"},
        "atoms": [a0, a1, a2, a3, a4],
        "by_clause": {"m0170": [copy.deepcopy(a0), copy.deepcopy(a4)],
                      "m0271": [copy.deepcopy(a1)],
                      "m0289": [copy.deepcopy(a2)],
                      "m0276": [copy.deepcopy(a3)]},
        "vocabulary": {
            LONG: _vocab("act", ["m0170", "m0271"]),
            SHORT: _vocab("act", ["m0289"]),
            HELP_OLD: _vocab("act", ["m0276"]),
            "helping_user": _vocab("act", ["m0170"]),
        },
    }


@pytest.fixture
def ext_root(tmp_path):
    """The ext_v1 trio in its REAL shapes and styles: base (utf-8), patch
    (annotations-shaped, near-empty, by_clause keys with empty lists —
    exactly what the shipped patch holds for untouched clauses), merged
    (ascii-escaped, the shipped merged file's actual serialization), plus a
    behavior_atoms surface carrying the exact decorated names."""
    _wjson_style(tmp_path / "annotations_ext_v1.json", _ext_ann())
    _wjson_style(tmp_path / "annotations_ext_v1_merged.json", _ext_ann(),
                 ensure_ascii=True)
    _wjson_style(tmp_path / "annotations_ext_v1_patch.json",
                 {"warnings": [], "provenance": {"model": "hand"},
                  "atoms": [], "by_clause": {"m0271": []}, "vocabulary": {}})
    _wjson_style(tmp_path / "behavior_atoms_ext_v1.json",
                 {"beh1": {"atoms": [
                     {"name": HELP_OLD, "kind": "act", "gloss": "g",
                      "weight": 2, "source": "definition", "new": False},
                     {"name": LONG, "kind": "act", "gloss": "g",
                      "weight": 1, "source": "definition", "new": False}]},
                  "provenance": {"model": "hand"}})
    return str(tmp_path)


def test_surface_scan_includes_the_ext_v1_trio(ext_root):
    got = ar.surface_paths(ext_root)
    for n in ("annotations_ext_v1.json", "annotations_ext_v1_patch.json",
              "annotations_ext_v1_merged.json"):
        assert n in got, f"{n} is not a scanned surface"


def test_usages_sees_all_three_shapes_on_the_ext_surfaces(ext_root):
    got = ar.find_usages(LONG, root=ext_root)
    locs = {(u["file"], u["location"]) for u in got}
    for f in ("annotations_ext_v1.json", "annotations_ext_v1_merged.json"):
        assert (f, "atoms[0]") in locs
        assert (f, "by_clause.m0170[0]") in locs
        assert (f, "by_clause.m0271[0]") in locs
        assert (f, f"vocabulary.{LONG}") in locs
        assert (f, f"vocabulary.{SHORT}") in locs  # same stem family
    assert ("behavior_atoms_ext_v1.json", "beh1.atoms[1]") in locs


def test_ascii_escaped_artifact_is_accepted_and_style_preserved(ext_root):
    """The shipped merged file is serialized ensure_ascii=True. That is a
    per-file STYLE (like the trailing newline), not a canonicality defect:
    the tool must plan over it and write it back in its own style, while the
    utf-8 base keeps its bytes raw."""
    rc = ar.main(["rename", "helping_user", "assisting_user",
                  "--date", "2026-08-03", "--reason", "clearer stem",
                  "--root", ext_root, "--apply"])
    assert rc == 0
    raw = _read_bytes(ext_root, "annotations_ext_v1_merged.json")
    assert b"assisting_user" in raw
    assert raw.isascii(), "merged file lost its ascii-escaped style"
    raw2 = _read_bytes(ext_root, "annotations_ext_v1.json")
    assert b"assisting_user" in raw2
    assert "—".encode("utf-8") in raw2, "base file lost its utf-8 style"


def test_rename_still_refuses_the_chain_correction(ext_root):
    """THE MOTIVATING REFUSAL (green today, and stays green): the chain
    corrections are exact-name, stem-identical rewrites — rename cannot
    express them, by design. rechain exists to fill exactly this gap."""
    with pytest.raises(ar.NotAStemError):
        ar.plan_migration(ext_root, "rename", LONG, SHORT,
                          date="2026-08-03", reason="r")


def test_rechain_refuses_stem_or_polarity_change(ext_root):
    with pytest.raises(ar.StemChangedError):
        ar.plan_migration(ext_root, "rechain", LONG,
                          "shouldnot_mock__model_user",
                          date="2026-08-03", reason="r")
    with pytest.raises(ar.PolarityChangedError):
        ar.plan_migration(ext_root, "rechain", LONG,
                          "should_judge__model_user",
                          date="2026-08-03", reason="r")
    with pytest.raises(ar.NotAnExactNameError):
        ar.plan_migration(ext_root, "rechain", "must_", SHORT,
                          date="2026-08-03", reason="r")
    with pytest.raises(ar.NotAnExactNameError):
        ar.plan_migration(ext_root, "rechain", LONG,
                          "shouldnot_judge__wizard",
                          date="2026-08-03", reason="r")
    with pytest.raises(ar.RefactorError):  # self-rechain is a no-op
        ar.plan_migration(ext_root, "rechain", LONG, LONG,
                          date="2026-08-03", reason="r")


def test_rechain_refuses_unknown_source(ext_root):
    with pytest.raises(ar.UnknownAtomError):
        ar.plan_migration(ext_root, "rechain", "must_never_written__user",
                          "must_never_written__model_user",
                          date="2026-08-03", reason="r")


def test_rechain_refuses_existing_target_at_whole_artifact_scope(ext_root):
    with pytest.raises(ar.NameExistsError) as ei:
        ar.plan_migration(ext_root, "rechain", LONG, SHORT,
                          date="2026-08-03", reason="r")
    assert "--clause" in str(ei.value), (
        "the refusal must point at the clause-scoped escape hatch")


def test_rechain_is_dry_run_by_default(ext_root):
    before = _snapshot_all(ext_root)
    rc = ar.main(["rechain", HELP_OLD, HELP_NEW,
                  "--date", "2026-08-03", "--reason", "agent missing",
                  "--root", ext_root])
    assert rc == 0
    assert _snapshot_all(ext_root) == before
    assert not os.path.exists(os.path.join(ext_root,
                                           "vocabulary_migrations.json"))


def test_rechain_apply_rewrites_exact_usages_everywhere(ext_root):
    rc = ar.main(["rechain", HELP_OLD, HELP_NEW,
                  "--date", "2026-08-03", "--reason", "agent missing",
                  "--root", ext_root, "--apply"])
    assert rc == 0
    for f in ("annotations_ext_v1.json", "annotations_ext_v1_merged.json"):
        ann = _read_json(ext_root, f)
        assert ann["atoms"][3]["name"] == HELP_NEW
        assert [a["name"] for a in ann["by_clause"]["m0276"]] == [HELP_NEW]
        assert HELP_OLD not in ann["vocabulary"]
        assert ann["vocabulary"][HELP_NEW]["clauses"] == ["m0276"]
        # EXACTNESS: other decorated names, even of active stems, untouched
        assert ann["atoms"][0]["name"] == LONG
        assert ann["atoms"][2]["name"] == SHORT
    ba = _read_json(ext_root, "behavior_atoms_ext_v1.json")
    assert ba["beh1"]["atoms"][0]["name"] == HELP_NEW
    assert ba["beh1"]["atoms"][1]["name"] == LONG


def test_rechain_clause_scoped_folds_into_the_existing_key(ext_root):
    """The m0271 case in miniature: the long chain is unlicensed at ONE
    clause; the other keeps it. Vocabulary counts fold into the existing
    target key merge-style; the source key survives with its remaining
    clause."""
    rc = ar.main(["rechain", LONG, SHORT, "--clause", "m0271",
                  "--date", "2026-08-03", "--reason", "patient unlicensed",
                  "--root", ext_root, "--apply"])
    assert rc == 0
    for f in ("annotations_ext_v1.json", "annotations_ext_v1_merged.json"):
        ann = _read_json(ext_root, f)
        assert [a["name"] for a in ann["by_clause"]["m0271"]] == [SHORT]
        assert ann["by_clause"]["m0170"][0]["name"] == LONG
        assert ann["atoms"][1]["name"] == SHORT
        assert ann["atoms"][0]["name"] == LONG
        v = ann["vocabulary"]
        assert v[LONG]["clauses"] == ["m0170"]
        assert v[LONG]["n_clauses"] == 1
        assert v[SHORT]["clauses"] == ["m0271", "m0289"]
        assert v[SHORT]["n_clauses"] == 2
    # clause-blind surfaces carry no clause identity: scope leaves them alone
    ba = _read_json(ext_root, "behavior_atoms_ext_v1.json")
    assert ba["beh1"]["atoms"][1]["name"] == LONG
    log = _read_json(ext_root, "vocabulary_migrations.json")
    e = log["migrations"][0]
    assert e["op"] == "rechain"
    assert e["old"] == LONG and e["new"] == SHORT
    assert e["clauses"] == ["m0271"]


def test_rechain_scoped_drops_source_key_only_when_empty(ext_root):
    rc = ar.main(["rechain", LONG, SHORT,
                  "--clause", "m0271", "--clause", "m0170",
                  "--date", "2026-08-03", "--reason", "patient unlicensed",
                  "--root", ext_root, "--apply"])
    assert rc == 0
    ann = _read_json(ext_root, "annotations_ext_v1.json")
    assert LONG not in ann["vocabulary"]
    assert ann["vocabulary"][SHORT]["clauses"] == ["m0170", "m0271", "m0289"]
    assert ann["vocabulary"][SHORT]["n_clauses"] == 3


def test_rechain_leaves_unrelated_lines_byte_untouched(ext_root):
    before = _snapshot_all(ext_root)
    ar.main(["rechain", LONG, SHORT, "--clause", "m0271",
             "--date", "2026-08-03", "--reason", "patient unlicensed",
             "--root", ext_root, "--apply"])
    after = _snapshot_all(ext_root)
    allowed = (LONG, SHORT, '"n_clauses"', '"m0170"', '"m0271"', '"m0289"')
    for name in before:
        if name == "vocabulary_migrations.json":
            continue
        old = before[name].decode("utf-8").splitlines()
        new = after[name].decode("utf-8").splitlines()
        changed = [l for l in difflib.unified_diff(old, new, lineterm="", n=0)
                   if l[:1] in "+-" and l[:3] not in ("+++", "---")]
        for line in changed:
            assert any(tok in line for tok in allowed), (
                f"{name}: unrelated line changed: {line!r}")


def test_rechain_replays(ext_root):
    keep = os.path.join(ext_root, "old_copies")
    os.makedirs(keep)
    for rel in ("annotations_ext_v1.json", "annotations_ext_v1_merged.json"):
        with open(os.path.join(keep, rel), "wb") as f:
            f.write(_read_bytes(ext_root, rel))
    ar.main(["rechain", LONG, SHORT, "--clause", "m0271",
             "--date", "2026-08-03", "--reason", "patient unlicensed",
             "--root", ext_root, "--apply"])
    ar.main(["rechain", HELP_OLD, HELP_NEW,
             "--date", "2026-08-04", "--reason", "agent missing",
             "--root", ext_root, "--apply"])
    log = os.path.join(ext_root, "vocabulary_migrations.json")
    for rel in ("annotations_ext_v1.json", "annotations_ext_v1_merged.json"):
        migrated = ar.replay_artifact(os.path.join(keep, rel), log)
        assert migrated == _read_bytes(ext_root, rel), (
            f"replaying {rel} through the log does not reproduce the "
            "current bytes")


# ------------------------------------- surface-scoped entries (the S2 seam)

EXT_LINEAGE = ["annotations_ext_v1.json", "annotations_ext_v1_patch.json",
               "annotations_ext_v1_merged.json"]


def test_surface_scoped_entry_is_not_applied_to_an_unlisted_surface():
    """THE S2 BLOCKER (APPLY_HALT.md contract A, designer-ruled seam): a
    migration entry MAY carry `surfaces` — the artifact basenames it applies
    to — and an entry whose list does not name the artifact being rewritten
    must be SKIPPED for that artifact. The b8/legacy annotation surfaces are
    frozen chain-free; a backfill entry scoped to the ext_v1 lineage must
    leave them byte-for-byte alone while still rewriting a listed surface."""
    legacy = _ext_ann()  # annotations-shaped: stands in for annotations_b8
    entry = {"op": "rechain", "old": HELP_OLD, "new": HELP_NEW,
             "date": "2026-08-04", "reason": "r", "clauses": ["m0276"],
             "surfaces": list(EXT_LINEAGE)}
    new_data, n, touched = ar.transform_document(
        copy.deepcopy(legacy), "annotations", entry, "annotations_b8.json")
    assert n == 0 and new_data == legacy, (
        "a surface-scoped entry was applied to the b8 legacy surface it "
        "does not list")
    new_data, n, _ = ar.transform_document(
        copy.deepcopy(legacy), "annotations", entry,
        "annotations_ext_v1.json")
    assert n > 0, "the scoped entry no longer applies to a LISTED surface"


def test_surface_scoped_apply_records_the_scope_and_spares_b8(ext_root):
    """The apply path end to end: a rechain scoped to the ext_v1 lineage
    leaves an annotations_b8.json carrying the same licensed usage
    byte-untouched, records `surfaces` in the log entry, and replays the b8
    copy back to its own (unchanged) bytes."""
    _wjson_style(os.path.join(ext_root, "annotations_b8.json"), _ext_ann())
    b8_before = _read_bytes(ext_root, "annotations_b8.json")
    rc = ar.main(["rechain", HELP_OLD, HELP_NEW, "--clause", "m0276",
                  "--surface", "annotations_ext_v1.json",
                  "--surface", "annotations_ext_v1_patch.json",
                  "--surface", "annotations_ext_v1_merged.json",
                  "--date", "2026-08-04", "--reason", "agent missing",
                  "--root", ext_root, "--apply"])
    assert rc == 0
    assert _read_bytes(ext_root, "annotations_b8.json") == b8_before, (
        "the frozen b8 surface moved under an ext_v1-scoped rechain")
    for f in ("annotations_ext_v1.json", "annotations_ext_v1_merged.json"):
        ann = _read_json(ext_root, f)
        assert [a["name"] for a in ann["by_clause"]["m0276"]] == [HELP_NEW]
    log = _read_json(ext_root, "vocabulary_migrations.json")
    e = log["migrations"][0]
    assert e["surfaces"] == sorted(EXT_LINEAGE)
    assert "annotations_b8.json" not in e["artifacts"]
    # replay: the scoped entry is skipped for the b8 copy, applied to ext
    migrated = ar.replay_artifact(
        os.path.join(ext_root, "annotations_b8.json"),
        os.path.join(ext_root, "vocabulary_migrations.json"),
        as_rel="annotations_b8.json")
    assert migrated == b8_before


def test_replay_of_a_scoped_entry_needs_the_surface_identity(ext_root):
    """The split precedent: an old annotations copy under an arbitrary
    filename does not say which surface it is a copy of, so replaying a
    surface-scoped entry over it without --as is a NAMED refusal, never a
    guess."""
    _wjson_style(os.path.join(ext_root, "annotations_b8.json"), _ext_ann())
    ar.main(["rechain", HELP_OLD, HELP_NEW, "--clause", "m0276",
             "--surface", "annotations_ext_v1.json",
             "--date", "2026-08-04", "--reason", "agent missing",
             "--root", ext_root, "--apply"])
    with pytest.raises(ar.RefactorError) as ei:
        ar.replay_artifact(
            os.path.join(ext_root, "annotations_b8.json"),
            os.path.join(ext_root, "vocabulary_migrations.json"))
    assert "surface" in str(ei.value) and "--as" in str(ei.value)


def test_surface_scope_refuses_empty_and_unknown_lists(ext_root):
    with pytest.raises(ar.RefactorError):
        ar.plan_migration(ext_root, "rechain", HELP_OLD, HELP_NEW,
                          date="2026-08-04", reason="r",
                          clauses=["m0276"], surfaces=[])
    with pytest.raises(ar.RefactorError) as ei:
        ar.plan_migration(ext_root, "rechain", HELP_OLD, HELP_NEW,
                          date="2026-08-04", reason="r", clauses=["m0276"],
                          surfaces=["annotations_ext_v2.json"])
    assert "unknown surface" in str(ei.value)


def test_legacy_surface_denylist_is_the_frozen_chainfree_pair():
    """The deny-list is a CLOSED vocabulary, pinned in both directions:
    it may neither shrink (a legacy surface escaping the fence) nor grow
    (a live surface locked out of legitimate future scopes)."""
    assert set(ar.LEGACY_SURFACE_DENYLIST) == {
        "annotations.json", "annotations_b8.json"}


def test_new_scoped_entries_naming_legacy_surfaces_are_refused(ext_root):
    """F2 hardening: 'b8 frozen forever' becomes tool-enforced. A NEW
    surface-scoped entry naming a legacy frozen surface is refused at
    plan time — each legacy surface alone, and a mixed list that pairs
    one with the ext_v1 lineage (one legacy name taints the whole
    entry). Unscoped rechains are untouched by the deny-list, and the
    ext_v1 lineage remains a legal scope."""
    _wjson_style(os.path.join(ext_root, "annotations_b8.json"), _ext_ann())
    _wjson_style(os.path.join(ext_root, "annotations.json"), _ext_ann())
    for denied in ("annotations_b8.json", "annotations.json"):
        with pytest.raises(ar.LegacySurfaceError) as ei:
            ar.plan_migration(ext_root, "rechain", HELP_OLD, HELP_NEW,
                              date="2026-08-04", reason="r",
                              clauses=["m0276"], surfaces=[denied])
        assert denied in str(ei.value)
    with pytest.raises(ar.LegacySurfaceError):
        ar.plan_migration(ext_root, "rechain", HELP_OLD, HELP_NEW,
                          date="2026-08-04", reason="r", clauses=["m0276"],
                          surfaces=list(EXT_LINEAGE) + ["annotations_b8.json"])
    # nothing written by any refusal (planning refuses before any byte)
    assert not os.path.exists(
        os.path.join(ext_root, "vocabulary_migrations.json"))
    # the ext_v1 lineage remains a legal NEW scope
    entry, _ = ar.plan_migration(ext_root, "rechain", HELP_OLD, HELP_NEW,
                                 date="2026-08-04", reason="r",
                                 clauses=["m0276"],
                                 surfaces=list(EXT_LINEAGE))
    assert entry["surfaces"] == sorted(EXT_LINEAGE)
    # an UNSCOPED rechain still plans over every surface, legacy included:
    # the legacy all-surfaces semantics are untouched by the deny-list
    entry, changes = ar.plan_migration(ext_root, "rechain", HELP_OLD,
                                       HELP_NEW, date="2026-08-04",
                                       reason="r", clauses=["m0276"])
    assert "surfaces" not in entry
    assert "annotations_b8.json" in changes


def test_deny_list_gates_planning_only_replay_keeps_legacy_semantics(
        ext_root):
    """Legacy replay stays intact: the deny-list fences NEW entries at
    PLAN time; replay is surface-honoring and never re-checks it, so an
    entry ALREADY in a log (the pre-deny-list shape, scoped to a legacy
    surface) replays byte-identically — applied to the legacy surface it
    names, skipped on a surface it does not name. Grandfathering by the
    byte-identity replay contract, pinned against a live refusal of the
    identical NEW scope."""
    _wjson_style(os.path.join(ext_root, "annotations_b8.json"), _ext_ann())
    b8_before = _read_bytes(ext_root, "annotations_b8.json")
    ext_before = _read_bytes(ext_root, "annotations_ext_v1.json")
    entry = {"op": "rechain", "old": HELP_OLD, "new": HELP_NEW,
             "date": "2026-08-04", "reason": "r", "clauses": ["m0276"],
             "surfaces": ["annotations_b8.json"],
             "artifacts": {}}
    log_path = _wjson(os.path.join(ext_root, "vocabulary_migrations.json"),
                      {"artifact": "vocabulary_migrations", "version": 1,
                       "migrations": [entry]})
    # applied to the legacy surface the grandfathered entry names
    migrated = ar.replay_artifact(
        os.path.join(ext_root, "annotations_b8.json"), log_path,
        as_rel="annotations_b8.json")
    assert migrated != b8_before
    got = json.loads(migrated.decode("utf-8"))
    assert [a["name"] for a in got["by_clause"]["m0276"]] == [HELP_NEW]
    # skipped on a surface the entry does not name
    migrated_ext = ar.replay_artifact(
        os.path.join(ext_root, "annotations_ext_v1.json"), log_path,
        as_rel="annotations_ext_v1.json")
    assert migrated_ext == ext_before
    # while the identical NEW scope is refused at plan time
    with pytest.raises(ar.LegacySurfaceError):
        ar.plan_migration(ext_root, "rechain", HELP_OLD, HELP_NEW,
                          date="2026-08-04", reason="r",
                          clauses=["m0276"],
                          surfaces=["annotations_b8.json"])


def test_absent_surfaces_field_keeps_the_legacy_all_surfaces_semantics(
        ext_root):
    """An entry WITHOUT the field applies everywhere, exactly as before the
    seam — the byte-level guarantee that every pre-seam log entry means what
    it always meant."""
    _wjson_style(os.path.join(ext_root, "annotations_b8.json"), _ext_ann())
    ar.main(["rechain", HELP_OLD, HELP_NEW, "--clause", "m0276",
             "--date", "2026-08-04", "--reason", "agent missing",
             "--root", ext_root, "--apply"])
    for f in ("annotations_b8.json", "annotations_ext_v1.json",
              "annotations_ext_v1_merged.json"):
        ann = _read_json(ext_root, f)
        assert [a["name"] for a in ann["by_clause"]["m0276"]] == [HELP_NEW]
    e = _read_json(ext_root, "vocabulary_migrations.json")["migrations"][0]
    assert "surfaces" not in e


def test_shipped_log_replays_every_live_surface_byte_identically():
    """LEGACY REPLAY, PROVEN ON THE REAL REPO: the shipped migration log
    (5 chain-repair rechains at the S2 halt), replayed over every live
    surface, reproduces that surface's current bytes exactly. Every entry
    predates the surface seam, so the absent-field path IS the legacy path —
    this pins that the seam changed nothing about how the existing log
    replays."""
    log_path = os.path.join(HERE, ar.MIGRATIONS_NAME)
    if not os.path.exists(log_path):
        pytest.skip("shipped migration log not present")
    for rel in ar.surface_paths(HERE):
        path = os.path.join(HERE, rel)
        data, raw, _ = ar._load(path)
        if ar.detect_shape(data) is None:
            continue
        migrated = ar.replay_artifact(path, log_path, as_rel=rel)
        assert migrated == raw, (
            f"replaying the shipped log over live {rel} no longer "
            "reproduces its current bytes")


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
