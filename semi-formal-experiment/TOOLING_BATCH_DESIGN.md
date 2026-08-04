# Tooling batch — six queued instrument fixes (design, 2026-08-04)

Status: DESIGN — brief specs for the queued items from the CYCLE_DESIGN
amendments, the two cycle decision records, and the session reports. Each item:
one paragraph, acceptance criteria, test shape. All are instrument-side; none
touches a query, weight, threshold value, or vocabulary. Companions:
JOIN_INTEGRITY_DESIGN.md, SEGMENTATION_GAPS_DESIGN.md.

## 1. `audit_disagreements dossiers --overlay` + config identity in census headers

The census CLI builds a plain `relevance.RelevanceIndex` and cannot pass a
containment overlay or frozen-thresholds artifact, so it cannot audit the
actual shipped configuration (which snapshots build overlay-on with frozen
cuts); and `index.jsonl` has no header at all — `config_tag` is just two
basenames, violating amendment F2's requirement of FULL config identity
(input shas, overlay sha, pricing_version, threshold rule) with deltas
computed against a NAMED prior census. Spec: add `--overlay` and
`--thresholds` mirroring `snapshot.py`'s flags (ContainmentIndex when overlay
given; cuts from the artifact when given, `_cut_for` otherwise, recorded per
behaviour); emit a first header record in `index.jsonl` carrying the full
config identity in snapshot.py's exact key shape (explicit nulls for absent
overlay/thresholds), and teach `validate` and cycle.py's census phase to
refuse a headerless index. Acceptance: a census generated with the audit_v1
config + overlay reproduces the overlay snapshot's scores in its
discriminators (the 2026-08-03 dossier lesson: a plain-index rebuild of an
overlay config silently contradicts frozen scores); byte-determinism holds.
Test shape: unit — header present, sorted-key, null-when-absent; integration —
tiny fixture census with and without overlay produces differing
`distance_to_cut` and a differing header sha; refusal test — validate on a
headerless directory exits nonzero.

## 2. `snapshot --no-clobber`

`snapshot.write_snapshot` unconditionally overwrites `snapshots/<tag>.json`;
only cycle.py's driver refuses tag reuse (amendment F3), so a bare CLI call
can still destroy a baseline another cycle's dossiers depend on. Spec:
snapshot.py itself refuses when the target exists with DIFFERENT bytes
(byte-compare via `snapshot_bytes`, which is canonical); identical bytes is a
silent no-op success; `--force` (never used by the driver) is the only
override and prints both shas. Default ON — clobbering becomes impossible
without saying so. Acceptance: F3's guarantee holds with no driver in the
loop. Test shape: write tag, rebuild with a changed input → SystemExit naming
both shas and the tag; rebuild unchanged → exit 0, file mtime-only; `--force`
→ overwrite recorded on stdout.

## 3. Dossier A-side reconstruction via migration replay

`dossier._resolve_inputs` refuses (StaleConfigError) when a baseline
snapshot's recorded input sha mismatches disk — correct, but after an
artifact cycle with flips (e.g. chain-repair: `vocabulary_migrations.json`
rewrote `annotations_ext_v1_merged.json` in place, shas
bb6f7aec… → 9e7adc44…) the A side becomes permanently unbuildable, exactly
when flip dossiers are most needed. Spec: on sha mismatch, consult
`vocabulary_migrations.json`; if the recorded sha appears in the log's
per-artifact `sha_before`/`sha_after` chain AND the chain links it to the
current disk sha with no gaps, the mismatch is a LOGGED migration, and the
pre-change bytes are fetched **from a recorded pre-change copy** — primarily
git history (the repo is a git repo; the chain-repair review already
validated this path by replaying HEAD copies through
`atom_refactor.replay_artifact` to byte-identity), with
`cycles/<name>/pre_change/` copies captured at MEASURE as the non-git
fallback. Fetched bytes are sha-verified against the recorded sha before use,
loaded from a temp path, and the dossier records reconstruction provenance
(source, sha, migration entries spanned). **Reverse replay is rejected**:
merge/fold migrations are lossy — the m0271 fold merged
`shouldnot_judge__model_user_developer` into an existing key, and no inverse
can decide which post-fold instances were originally which name. Forward
replay from an older recorded copy (old bytes → replay → must equal disk) is
retained as the verification direction only, which is the contract
`replay_artifact` already states. Any sha not found in the chain remains a
hard StaleConfigError — reconstruction never launders corruption. Acceptance:
flip dossiers build against a pre-migration baseline with zero manual file
juggling; an unlogged mutation still refuses. Test shape: scratch artifact +
scratch migration log; apply a rename with `--apply`; build dossiers against
a snapshot recording the old sha → succeeds with provenance record;
corrupt one chain sha → StaleConfigError; delete git object and pre_change
copy → distinct "reconstruction source unavailable" error naming both.

## 4. Dry-run outputs to `<name>.dryrun.json` + non-stub overwrite refusal

`--dry-run` is the DEFAULT on both annotators, and both write their 0-atom
stub artifact to the same path a live run uses — `behavior_atoms.py` writes
to literal `behavior_atoms.json` when `--out` is omitted, which is how a
dry-run stub silently clobbered the shipped artifact (README incident;
restored; guard pending). Spec: when the assembled artifact will carry
`provenance.dry_run: true`, the default output path becomes
`<name>.dryrun.json` (explicit `--out` gets the same suffix inserted unless
it already ends in `.dryrun.json`); independently, ANY write path (dry or
live) refuses to overwrite an existing file whose parsed
`provenance.dry_run` is false — a non-stub artifact — without `--force`.
Two guards because they fail independently: the rename protects defaults,
the refusal protects explicit paths. Acceptance: the README incident is
mechanically impossible; live reruns onto shipped artifacts require `--force`.
Test shape: dry-run with default args in a tmpdir containing a live-shaped
`behavior_atoms.json` → that file byte-unchanged, `behavior_atoms.dryrun.json`
created; live-mode write (mocked client) onto same → refusal naming the path;
`--force` → overwrite; dry-run onto an existing dryrun stub → plain overwrite
(stubs may clobber stubs).

## 5. Dossier verdict-loader tolerance pinned by test

`dossier._load_verdict_records` is deliberately tolerant ("a list under any
key, like the repo's other loaders"), and amendment F9 hardcodes that the two
validators keep their differing flag spellings (`--verdict-file` vs
`--verdicts`) rather than being harmonized. Both facts are currently enforced
only by prose, so a well-meaning cleanup could narrow the loader and orphan
every historical verdict artifact, or harmonize the flags and break cycle.py's
hardcoded invocations. Spec: pin by test, changing no behavior. Acceptance:
the accepted-shape set (bare list; `{"verdicts": [...]}`; single-list-valued
key of any name) and the rejected set (no list anywhere; two candidate lists —
ambiguity must refuse, not guess, matching current behavior or tightening to
refusal if current behavior guesses) are each asserted, plus a test importing
both CLIs' parsers and asserting the two spellings exist and are distinct.
Test shape: pure-unit table test over fixture dicts; one argparse
introspection test; no fixtures on disk beyond tmpdir JSON.

## 6. `cycle.py` commit-at-CLOSE

CLOSE appends the one-line record to `cycles/CYCLE_LOG.jsonl` and stops; the
repo's commits (e.g. 3464ef7, the chain-repair KEEP) are hand-authored after
the fact, so a closed cycle can sit uncommitted while concurrent agents work —
the exact drift the sha-closure guard exists to catch. Spec: `_close`
additionally drafts a commit message from the log record — first line
`<cycle>: <decision> (<shape>, predictions <passed>/<total>)`, body from the
manifest's fix description and the decision's justification, plus the
standard co-author trailer — writes it to `cycles/<name>/commit_message.txt`,
and prints the message with the manifest-declared file list plus the cycle
directory as the suggested staging set. The driver NEVER runs git itself:
the coordinator confirms and executes (consistent with the standing policy of
committing each unit once its review resolves — the draft removes the
friction, the human/coordinator keeps the authority). Acceptance: every CLOSE
leaves a ready-to-use message; no git side effects from the driver. Test
shape: close a fixture cycle in tmpdir → `commit_message.txt` exists, first
line matches the log record's fields, staging list equals declared files ∪
cycle dir; assert no `.git` mutation by running CLOSE in a git-free tmpdir
(must not error — git absence is not a CLOSE failure).
