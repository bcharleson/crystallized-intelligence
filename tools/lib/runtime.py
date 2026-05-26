"""Shared runtime checks for framework CLI tools."""

from __future__ import annotations

import sys

MIN_PYTHON = (3, 10)


def require_python(min_version: tuple[int, int] = MIN_PYTHON) -> None:
    """Exit with a clear message if the interpreter is too old."""
    if sys.version_info >= min_version:
        return
    major, minor = min_version
    found = f"{sys.version_info.major}.{sys.version_info.minor}"
    sys.stderr.write(
        f"Error: Python {major}.{minor}+ required (found {found}).\n"
        f"See README.md — core tools use modern type syntax and require 3.10+.\n"
    )
    raise SystemExit(1)
