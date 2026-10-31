"""Shared setup for the tests: the repository on sys.path and the --update-snapshots option."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
for p in (REPO, REPO / "tools"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def pytest_addoption(parser):
    parser.addoption("--update-snapshots", action="store_true",
                     help="rewrite tests/snapshots/ with the HTML the exporter makes now")
