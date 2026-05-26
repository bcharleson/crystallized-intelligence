#!/usr/bin/env python3
"""
Generate MANIFEST.md — an auto-generated index of a brain repository.
Agents and humans can scan this to find relevant content quickly.

Requires Python 3.10+ (see README.md).
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

_TOOLS = Path(__file__).resolve().parent.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
from lib.runtime import require_python  # noqa: E402

require_python()

DEFAULT_BRAIN_ROOT = Path(__file__).resolve().parent.parent.parent

SKIP_DIRS = {".git", ".github", "__pycache__", ".vscode", ".cursor"}
SKIP_FILES = {".DS_Store", ".gitignore"}

SECTION_DESCRIPTIONS = {
    "corpus": "Domain-organized knowledge corpus with crystallized layers, sources, and examples",
    "private": "Protected client, strategy, brand, and internal operating material",
    "tools": "Framework tooling, schemas, and maintenance scripts",
    "open-source": "Public-repo extraction scaffold, templates, and export configuration",
    "skills": "Claude skill packages and related references",
}


def count_words(filepath: Path) -> int:
    """Count words in a text file."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="ignore")
        return len(text.split())
    except Exception:
        return 0


def format_size(size_bytes: int) -> str:
    """Format byte count to human-readable."""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}K"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}M"


def resolve_brain_root(explicit: Optional[str]) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("BRAIN_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return DEFAULT_BRAIN_ROOT


def brain_title(brain_root: Path) -> str:
    brain_yaml = brain_root / "brain.yaml"
    if brain_yaml.is_file():
        for line in brain_yaml.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("name:"):
                name = line.split(":", 1)[1].strip().strip('"').strip("'")
                if name:
                    return name
    return brain_root.name


def build_manifest(brain_root: Path):
    """Build the MANIFEST.md content."""
    lines = []
    lines.append(f"# MANIFEST — {brain_title(brain_root)} File Index")
    lines.append("")
    lines.append(f"Auto-generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    total_files = 0
    total_words = 0

    # Walk top-level directories in order
    top_dirs = sorted(
        [d for d in brain_root.iterdir() if d.is_dir() and d.name not in SKIP_DIRS],
        key=lambda d: d.name
    )

    for top_dir in top_dirs:
        dir_name = top_dir.name
        description = SECTION_DESCRIPTIONS.get(dir_name, "")

        # Collect all files recursively
        files = []
        for root, dirs, filenames in os.walk(top_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in sorted(filenames):
                if fname in SKIP_FILES:
                    continue
                fpath = Path(root) / fname
                rel = fpath.relative_to(brain_root)
                size = fpath.stat().st_size
                words = count_words(fpath) if fpath.suffix in (".md", ".txt", ".json") else 0
                files.append((str(rel), size, words))

        if not files:
            continue

        dir_files = len(files)
        dir_words = sum(w for _, _, w in files)
        dir_size = sum(s for _, s, _ in files)
        total_files += dir_files
        total_words += dir_words

        lines.append(f"## `{dir_name}/` ({dir_files} files, {format_size(dir_size)})")
        if description:
            lines.append(f"_{description}_")
        lines.append("")

        # Group by subdirectory
        current_subdir = None
        for rel_path, size, words in files:
            parts = Path(rel_path).parts
            subdir = "/".join(parts[1:-1]) if len(parts) > 2 else ""

            if subdir != current_subdir:
                current_subdir = subdir
                if subdir:
                    lines.append(f"### {dir_name}/{subdir}/")
                    lines.append("")

            word_str = f" ({words:,} words)" if words > 0 else ""
            lines.append(f"- `{rel_path}` [{format_size(size)}]{word_str}")

        lines.append("")

    # Summary
    lines.insert(3, f"**{total_files} files** | **{total_words:,} words** total")
    lines.insert(4, "")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate MANIFEST.md for a brain repo")
    parser.add_argument(
        "--brain-root",
        help="Brain directory (default: BRAIN_ROOT env or framework root)",
    )
    args = parser.parse_args()
    brain_root = resolve_brain_root(args.brain_root)
    if not (brain_root / "brain.yaml").is_file():
        print(f"Error: no brain.yaml at {brain_root}", flush=True)
        raise SystemExit(1)

    manifest = build_manifest(brain_root)
    manifest_path = brain_root / "MANIFEST.md"
    manifest_path.write_text(manifest, encoding="utf-8")
    print(f"Generated: {manifest_path}")
    print(f"Size: {format_size(len(manifest.encode()))}")


if __name__ == "__main__":
    main()
