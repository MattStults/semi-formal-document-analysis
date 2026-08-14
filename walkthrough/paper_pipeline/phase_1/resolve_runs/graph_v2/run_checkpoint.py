"""Periodic run checkpoints (Matt's directive 2026-08-14: "periodic stops
during long runs, more frequent rather than less").

A long paid run that only reports at the end is a run whose defects are
discovered after they have all been paid for. Every `checkpoint_every`
items the run STOPS TO SAY WHERE IT IS -- items done/remaining, spend so
far against the ceiling, failures by category, graveyard open entries --
on stdout and appended to the run's `health.jsonl`. With
`checkpoint_pause` true it stops there, cleanly and resumably.

⛔ A CHECKPOINT MUST NEVER LOSE WORK. It lands BETWEEN items, only after
the completed item's artifacts and the run's index file are written --
in translate_exec that is inside `RunContext.finish`, AFTER
`flush()`; in promise_repair it is after the report row is appended and
the graph copy holds the splice. Both pause paths therefore stop with a
directory that a resume can read.

Config (both keys optional, read from a stage section first and then the
config root, so one config can carry a global default and a per-stage
override):

    checkpoint_every : int, default 25   (0 or negative disables)
    checkpoint_pause : bool, default FALSE -- non-interactive runs must
                       not wedge waiting for a human; the pause is opt-in
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (PHASE1, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import translate as T          # noqa: E402

DEFAULT_EVERY = 25


class CheckpointPause(T.Phase1Error):
    """A clean, resumable stop at a checkpoint. Phase1Error so every
    existing stop path unwinds it the way it unwinds a cost gate --
    artifacts written, nothing half-said."""


def checkpoint_config(cfg, section=None):
    """(every, pause) from `cfg[section]` if present, else `cfg`."""
    src = (cfg.get(section) or {}) if section else {}
    every = src.get("checkpoint_every",
                    (cfg or {}).get("checkpoint_every", DEFAULT_EVERY))
    pause = src.get("checkpoint_pause",
                    (cfg or {}).get("checkpoint_pause", False))
    try:
        every = int(every)
    except (TypeError, ValueError):
        every = DEFAULT_EVERY
    return every, bool(pause)


class Checkpoint:
    """`tick(done, ...)` after each completed item. Fires when `done` is a
    positive multiple of `every`."""

    def __init__(self, every, pause, health_path, label, total=None,
                 ceiling_usd=None, resume_hint=""):
        self.every, self.pause = int(every or 0), bool(pause)
        self.health_path, self.label = health_path, label
        self.total, self.ceiling_usd = total, ceiling_usd
        self.resume_hint = resume_hint
        self.fired = []

    def due(self, done):
        return self.every > 0 and done > 0 and done % self.every == 0

    def record(self, done, spent_usd=0.0, failures=None,
               graveyard_open=None, paused=False, extra=None):
        rec = {"artifact": self.label, "kind": "checkpoint",
               "completed": int(done),
               "remaining": (None if self.total is None
                             else max(int(self.total) - int(done), 0)),
               "total": self.total,
               "spent_usd": round(float(spent_usd or 0.0), 6),
               "ceiling_usd": self.ceiling_usd,
               "failures": dict(failures or {}),
               "graveyard_open": graveyard_open,
               "paused": bool(paused)}
        if extra:
            rec.update(extra)
        if self.health_path:
            os.makedirs(os.path.dirname(os.path.abspath(self.health_path)),
                        exist_ok=True)
            with open(self.health_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
        self.fired.append(rec)
        fails = ", ".join(f"{k} {v}" for k, v in
                          sorted((failures or {}).items()) if v) or "none"
        print(f"\n⏱ checkpoint [{self.label}]: {rec['completed']} done"
              + (f", {rec['remaining']} remaining"
                 if rec["remaining"] is not None else "")
              + f" | spent ${rec['spent_usd']:.4f}"
              + (f" of ${float(self.ceiling_usd):.2f} ceiling"
                 if self.ceiling_usd is not None else "")
              + f" | failures: {fails}"
              + (f" | graveyard open: {graveyard_open}"
                 if graveyard_open is not None else ""))
        return rec

    def tick(self, done, spent_usd=0.0, failures=None, graveyard_open=None,
             extra=None):
        """Record a checkpoint if one is due; raise CheckpointPause when
        `checkpoint_pause` is set. Returns the record, or None."""
        if not self.due(done):
            return None
        rec = self.record(done, spent_usd=spent_usd, failures=failures,
                          graveyard_open=graveyard_open, paused=self.pause,
                          extra=extra)
        if self.pause:
            raise CheckpointPause(
                f"paused at checkpoint after {rec['completed']} item(s)"
                + (f" ({rec['remaining']} remaining)"
                   if rec["remaining"] is not None else "")
                + f"; every completed item's artifacts are written"
                + (f". {self.resume_hint}" if self.resume_hint else ""))
        return rec
