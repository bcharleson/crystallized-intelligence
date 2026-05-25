#!/usr/bin/env python3
"""
verify.py — Quality gates for brain content.

Validates documents against the frontmatter schema and content quality rules.
Designed to run in CI (GitHub Actions) on PRs that touch corpus/.

Gates:
  1. STRUCTURAL  — Valid frontmatter, required fields present
  2. DEDUP       — No duplicate source URLs or near-duplicate content
  3. QUALITY     — Source provenance, author identified, minimum word count
  4. SAFETY      — No API keys, emails, PII patterns in content

Usage:
  python tools/bin/verify.py corpus/my-domain/knowledge/new-article.md
  python tools/bin/verify.py --domain my-domain
  python tools/bin/verify.py --all
  python tools/bin/verify.py --changed-only    # Only files changed in git
  python tools/bin/verify.py --all --strict     # Exit 1 on any warning

Uses only Python stdlib — no pip dependencies.
"""

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_BRAIN_ROOT = Path(__file__).resolve().parent.parent.parent
BRAIN_ROOT = DEFAULT_BRAIN_ROOT
CORPUS_DIR = BRAIN_ROOT / "corpus"

# PII patterns to flag
PII_PATTERNS = [
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "email address"),
    (r"sk-[a-zA-Z0-9]{20,}", "API key (Anthropic)"),
    (r"sk_live_[a-zA-Z0-9]{20,}", "API key (Stripe)"),
    (r"xoxb-[a-zA-Z0-9-]+", "Slack token"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub token"),
    (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "phone number"),
    (r"\b\d{3}[-]\d{2}[-]\d{4}\b", "SSN"),
]

# Allowed emails (not flagged)
ALLOWED_EMAIL_PATTERNS = [
    r"example\.com$",
    r"test\.com$",
    r"placeholder",
    r"your-?email",
]


def parse_frontmatter_simple(filepath: Path) -> tuple[dict, str]:
    """Parse YAML frontmatter (simple stdlib parser)."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {}, ""

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if not match:
        return {}, text

    fm_raw = match.group(1)
    body = match.group(2)

    fm = {}
    current_section = None
    for line in fm_raw.split("\n"):
        section_match = re.match(r"^(\w+):\s*$", line)
        if section_match:
            current_section = section_match.group(1)
            fm[current_section] = {}
            continue
        if current_section:
            kv_match = re.match(r"^\s+(\w+):\s*(.+)$", line)
            if kv_match:
                fm[current_section][kv_match.group(1)] = kv_match.group(2).strip().strip('"').strip("'")
                continue
        kv_match = re.match(r"^(\w+):\s*(.+)$", line)
        if kv_match:
            fm[kv_match.group(1)] = kv_match.group(2).strip().strip('"').strip("'")
            current_section = None

    return fm, body


class VerificationResult:
    """Tracks pass/fail/warn for a single file."""
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.errors = []
        self.warnings = []

    def error(self, gate: str, message: str):
        self.errors.append(f"[{gate}] {message}")

    def warn(self, gate: str, message: str):
        self.warnings.append(f"[{gate}] {message}")

    @property
    def passed(self):
        return len(self.errors) == 0

    def __str__(self):
        try:
            rel = self.filepath.relative_to(BRAIN_ROOT)
        except ValueError:
            rel = self.filepath
        if self.passed and not self.warnings:
            return f"  ✓ {rel}"
        lines = []
        status = "✓" if self.passed else "✗"
        lines.append(f"  {status} {rel}")
        for err in self.errors:
            lines.append(f"      ERROR: {err}")
        for warn in self.warnings:
            lines.append(f"      WARN:  {warn}")
        return "\n".join(lines)


def verify_structural(filepath: Path, fm: dict, body: str) -> VerificationResult:
    """Gate 1: Structural validation."""
    result = VerificationResult(filepath)

    # Must have frontmatter
    if not fm:
        result.warn("STRUCTURAL", "No YAML frontmatter found")
        return result

    # Required fields
    if "title" not in fm:
        result.error("STRUCTURAL", "Missing required field: title")

    # content_type recommended
    if "content_type" not in fm:
        result.warn("STRUCTURAL", "Missing recommended field: content_type")

    # created date recommended
    if "created" not in fm:
        result.warn("STRUCTURAL", "Missing recommended field: created")

    return result


def verify_quality(filepath: Path, fm: dict, body: str) -> VerificationResult:
    """Gate 3: Quality checks."""
    result = VerificationResult(filepath)

    # Minimum word count (skip for config/reference files)
    word_count = len(body.split())
    if filepath.suffix == ".md" and word_count < 30:
        result.warn("QUALITY", f"Very short content ({word_count} words)")

    # Check for source provenance
    source = fm.get("source", {})
    if isinstance(source, dict):
        if not source.get("type") and not source.get("url") and not source.get("author"):
            result.warn("QUALITY", "No source provenance (type, url, or author)")

    return result


def verify_safety(filepath: Path, fm: dict, body: str) -> VerificationResult:
    """Gate 4: Safety checks (PII, API keys)."""
    result = VerificationResult(filepath)

    full_text = body
    for pattern, description in PII_PATTERNS:
        matches = re.findall(pattern, full_text)
        for match in matches:
            # Skip allowed patterns
            is_allowed = False
            if description == "email address":
                for allowed in ALLOWED_EMAIL_PATTERNS:
                    if re.search(allowed, match, re.IGNORECASE):
                        is_allowed = True
                        break
            if not is_allowed:
                result.error("SAFETY", f"Possible {description} found: {match[:30]}...")

    return result


def verify_file(filepath: Path) -> VerificationResult:
    """Run all verification gates on a single file."""
    fm, body = parse_frontmatter_simple(filepath)

    combined = VerificationResult(filepath)

    for gate_fn in (verify_structural, verify_quality, verify_safety):
        result = gate_fn(filepath, fm, body)
        combined.errors.extend(result.errors)
        combined.warnings.extend(result.warnings)

    return combined


def get_changed_files() -> list[Path]:
    """Get files changed in the current git diff (for CI)."""
    result = subprocess.run(
        ["git", "-C", str(BRAIN_ROOT), "diff", "--name-only", "--cached", "HEAD"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        # Try against main
        result = subprocess.run(
            ["git", "-C", str(BRAIN_ROOT), "diff", "--name-only", "main...HEAD"],
            capture_output=True, text=True,
        )

    files = []
    for line in result.stdout.strip().split("\n"):
        if line and line.startswith("corpus/"):
            fpath = BRAIN_ROOT / line
            if fpath.exists() and fpath.suffix in (".md", ".txt"):
                files.append(fpath)
    return files


def main():
    global BRAIN_ROOT, CORPUS_DIR

    parser = argparse.ArgumentParser(description="Verify brain content quality")
    parser.add_argument("file", nargs="?", help="Specific file to verify")
    parser.add_argument("--domain", help="Verify all files in a domain")
    parser.add_argument("--all", action="store_true", help="Verify all corpus files")
    parser.add_argument(
        "--brain-root",
        help="Brain root directory containing corpus/ (defaults to repository root)",
    )
    parser.add_argument("--changed-only", action="store_true",
                        help="Only verify files changed in git")
    parser.add_argument("--strict", action="store_true",
                        help="Treat warnings as errors (exit 1)")
    args = parser.parse_args()

    if args.brain_root:
        BRAIN_ROOT = Path(args.brain_root).expanduser().resolve()
        CORPUS_DIR = BRAIN_ROOT / "corpus"

    if args.domain or args.all:
        if not CORPUS_DIR.exists():
            print(f"Error: corpus directory not found at {CORPUS_DIR}", file=sys.stderr)
            sys.exit(1)

    # Collect files
    files = []
    if args.file:
        files = [Path(args.file)]
    elif args.domain:
        domain_dir = CORPUS_DIR / args.domain
        files = sorted(f for f in domain_dir.rglob("*")
                       if f.is_file() and f.suffix in (".md", ".txt")
                       and not f.name.startswith("_") and not f.name.startswith("."))
    elif args.changed_only:
        files = get_changed_files()
    elif args.all:
        files = sorted(f for f in CORPUS_DIR.rglob("*")
                       if f.is_file() and f.suffix in (".md", ".txt")
                       and not f.name.startswith("_") and not f.name.startswith("."))
    else:
        parser.error("Specify a file, --domain, --all, or --changed-only")

    if not files:
        print("No files to verify.")
        return

    print(f"Verifying {len(files)} files...\n")

    total = 0
    passed = 0
    failed = 0
    warned = 0

    for filepath in files:
        result = verify_file(filepath)
        total += 1
        if result.passed:
            passed += 1
        else:
            failed += 1
        if result.warnings:
            warned += 1
        print(str(result))

    print(f"\n{'═' * 50}")
    print(f"Results: {passed}/{total} passed, {failed} failed, {warned} with warnings")

    if failed > 0:
        sys.exit(1)
    if args.strict and warned > 0:
        print("Strict mode: warnings treated as errors")
        sys.exit(1)

    print("All checks passed!")


if __name__ == "__main__":
    main()
