"""Shared runtime checks for framework CLI tools."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

MIN_PYTHON = (3, 9)


def require_python(min_version: tuple[int, int] = MIN_PYTHON) -> None:
    """Exit with a clear message if the interpreter is too old."""
    if sys.version_info >= min_version:
        return
    major, minor = min_version
    found = f"{sys.version_info.major}.{sys.version_info.minor}"
    sys.stderr.write(
        f"Error: Python {major}.{minor}+ required (found {found}).\n"
        f"See README.md — core tools require Python {major}.{minor}+.\n"
    )
    raise SystemExit(1)


def resolve_brain_root(explicit: Optional[str], default: Path) -> Path:
    """Resolve brain root from CLI flag, BRAIN_ROOT env, or default."""
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("BRAIN_ROOT", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return default
