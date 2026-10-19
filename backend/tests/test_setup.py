"""Smoke test: proves pytest runs and we are on the Python version we pinned."""

import sys


def test_python_version_is_3_13() -> None:
    # LangGraph supports up to 3.13, so the project must run on exactly that minor version.
    assert sys.version_info[:2] == (3, 13)
