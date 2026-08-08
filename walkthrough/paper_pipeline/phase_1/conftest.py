"""Session-scoped guards for the phase_1 suite."""

import pathlib

import pytest

HERE = pathlib.Path(__file__).resolve().parent
REAL_GRAVEYARD = HERE / "repair_graveyard"


def _entries():
    return {d.name for d in REAL_GRAVEYARD.iterdir()} if REAL_GRAVEYARD.is_dir() \
        else set()


@pytest.fixture(scope="session", autouse=True)
def no_leak_into_the_repo_graveyard():
    """No test may write into the production graveyard.

    16 entries appeared there the first time the suite ran after the graveyard
    was wired in. Beyond the mess: the cap REFUSES TO START a run when the
    graveyard is full, so a suite could block real work with its own garbage.

    ⚠️ This is a session fixture and not a test on purpose. Written as a test it
    passed vacuously — pytest runs files alphabetically, so it checked before
    the file that leaked had run. A guard that runs before the thing it guards
    is indistinguishable from one that works.
    """
    before = _entries()
    yield
    leaked = sorted(_entries() - before)
    assert not leaked, (
        f"{len(leaked)} entries leaked into {REAL_GRAVEYARD}: {leaked[:4]}. "
        f"A test calling run() did not set cfg['graveyard']['dir'] to tmp_path")
