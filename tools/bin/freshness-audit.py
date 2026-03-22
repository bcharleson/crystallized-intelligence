#!/usr/bin/env python3
"""
freshness-audit.py — Flag stale documents based on freshness sensitivity.

Reads corpus documents and checks their `updated` or `created` dates against
freshness thresholds defined per domain. Documents in fast-moving domains
go stale faster than stable ones. Sensitivity is configured per domain in
corpus/{domain}/_domain.yaml using the `freshness_sensitivity` field.

Thresholds:
  high:   90 days  — fast-moving domains (configure in _domain.yaml)
  medium: 180 days — moderate-velocity domains (default)
  low:    365 days — stable, evergreen domains

Usage:
  python tools/bin/freshness-audit.py --all
  python tools/bin/freshness-audit.py --domain my-domain
  python tools/bin/freshness-audit.py --all --stale-only
  python tools/bin/freshness-audit.py --all --format markdown > freshness-report.md

Uses only Python stdlib — no pip dependencies.
"""

import argparse
import re
import sys
from datetime import date, timedelta
from pathlib import Path

BRAIN_ROOT = Path(__file__).resolve().parent.parent.parent
CORPUS_DIR = BRAIN_ROOT / "corpus"

# Freshness sensitivity is configured per domain in corpus/{domain}/_domain.yaml
# using the `freshness_sensitivity` field (values: high, medium, low).
# Falls back to "medium" if not configured.
_SENSITIVITY_CACHE: dict[str, str] = {}

def get_domain_sensitivity(domain: str) -> str:
    """Read freshness_sensitivity from _domain.yaml, fall back to 'medium'."""
    if domain in _SENSITIVITY_CACHE:
        return _SENSITIVITY_CACHE[domain]
    domain_yaml = CORPUS_DIR / domain / "_domain.yaml"
    sensitivity = "medium"
    if domain_yaml.exists():
        try:
            text = domain_yaml.read_text(encoding="utf-8")
            m = re.search(r"^freshness_sensitivity:\s*(\w+)", text, re.MULTILINE)
            if m and m.group(1).lower() in STALE_THRESHOLDS:
                sensitivity = m.group(1).lower()
        except Exception:
            pass
    _SENSITIVITY_CACHE[domain] = sensitivity
    return sensitivity

# Thresholds in days (from brain.yaml auto_stale_days)
STALE_THRESHOLDS = {
    "high": 90,
    "medium": 180,
    "low": 365,
}


def parse_frontmatter(filepath: Path) -> dict:
    """Parse YAML frontmatter (simple stdlib parser)."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {}

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}

    fm_raw = match.group(1)
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

    return fm


def parse_date(date_str: str) -> date | None:
    """Parse a date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)."""
    if not date_str:
        return None
    # Handle ISO formats
    date_str = date_str.strip()[:10]
    try:
        parts = date_str.split("-")
        if len(parts) == 3:
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass
    return None


def get_document_date(fm: dict) -> date | None:
    """Get the most recent date from frontmatter (updated > created > date)."""
    for field in ("updated", "created", "date"):
        d = parse_date(fm.get(field, ""))
        if d:
            return d
    # Check freshness section
    if isinstance(fm.get("freshness"), dict):
        d = parse_date(fm["freshness"].get("valid_until", ""))
        if d:
            return d
    return None


def get_domain(filepath: Path) -> str:
    """Extract domain from file path."""
    try:
        rel = filepath.relative_to(CORPUS_DIR)
        return rel.parts[0] if rel.parts else "unknown"
    except ValueError:
        return "unknown"


def audit_file(filepath: Path, today: date) -> dict:
    """Audit a single file for staleness."""
    fm = parse_frontmatter(filepath)
    domain = get_domain(filepath)
    sensitivity = get_domain_sensitivity(domain)
    threshold_days = STALE_THRESHOLDS[sensitivity]

    doc_date = get_document_date(fm)
    result = {
        "filepath": filepath,
        "domain": domain,
        "title": fm.get("title", filepath.stem),
        "sensitivity": sensitivity,
        "threshold_days": threshold_days,
        "doc_date": doc_date,
        "age_days": None,
        "stale": False,
        "no_date": False,
    }

    if doc_date is None:
        result["no_date"] = True
        return result

    age = (today - doc_date).days
    result["age_days"] = age
    result["stale"] = age > threshold_days

    return result


def format_text(results: list[dict], stale_only: bool) -> str:
    """Format results as text output."""
    lines = []

    stale = [r for r in results if r["stale"]]
    no_date = [r for r in results if r["no_date"]]
    fresh = [r for r in results if not r["stale"] and not r["no_date"]]

    if stale:
        lines.append(f"\nSTALE ({len(stale)} documents)")
        lines.append("=" * 60)
        for r in sorted(stale, key=lambda x: -(x["age_days"] or 0)):
            rel = r["filepath"].relative_to(BRAIN_ROOT)
            age = r["age_days"]
            over = age - r["threshold_days"]
            lines.append(
                f"  {rel}\n"
                f"    {r['title'][:60]}\n"
                f"    Age: {age}d | Threshold: {r['threshold_days']}d ({r['sensitivity']}) | "
                f"Overdue: {over}d"
            )

    if no_date and not stale_only:
        lines.append(f"\nNO DATE ({len(no_date)} documents)")
        lines.append("=" * 60)
        for r in sorted(no_date, key=lambda x: str(x["filepath"])):
            rel = r["filepath"].relative_to(BRAIN_ROOT)
            lines.append(f"  {rel}")

    if not stale_only:
        lines.append(f"\nFRESH ({len(fresh)} documents)")
        lines.append("=" * 60)
        for r in sorted(fresh, key=lambda x: -(x["age_days"] or 0)):
            rel = r["filepath"].relative_to(BRAIN_ROOT)
            remaining = r["threshold_days"] - (r["age_days"] or 0)
            lines.append(f"  {rel}  ({remaining}d remaining)")

    lines.append(f"\n{'═' * 60}")
    lines.append("Freshness Audit Summary")
    lines.append(f"{'═' * 60}")
    lines.append(f"Total:    {len(results)}")
    lines.append(f"Fresh:    {len(fresh)}")
    lines.append(f"Stale:    {len(stale)}")
    lines.append(f"No date:  {len(no_date)}")

    # Per-domain breakdown
    domains = {}
    for r in results:
        d = r["domain"]
        if d not in domains:
            domains[d] = {"total": 0, "stale": 0, "no_date": 0}
        domains[d]["total"] += 1
        if r["stale"]:
            domains[d]["stale"] += 1
        if r["no_date"]:
            domains[d]["no_date"] += 1

    lines.append("\nBy domain:")
    for domain in sorted(domains):
        d = domains[domain]
        sens = DOMAIN_SENSITIVITY.get(domain, "low")
        lines.append(
            f"  {domain:20s} {d['total']:3d} total, "
            f"{d['stale']:3d} stale, {d['no_date']:3d} no date  "
            f"({sens}, {STALE_THRESHOLDS[sens]}d threshold)"
        )

    return "\n".join(lines)


def format_markdown(results: list[dict]) -> str:
    """Format results as markdown for reports."""
    lines = [
        f"# Freshness Audit Report",
        f"",
        f"Generated: {date.today().isoformat()}",
        f"",
    ]

    stale = [r for r in results if r["stale"]]
    no_date = [r for r in results if r["no_date"]]
    fresh = [r for r in results if not r["stale"] and not r["no_date"]]

    lines.append(f"## Summary")
    lines.append(f"")
    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total | {len(results)} |")
    lines.append(f"| Fresh | {len(fresh)} |")
    lines.append(f"| Stale | {len(stale)} |")
    lines.append(f"| No date | {len(no_date)} |")
    lines.append(f"")

    if stale:
        lines.append(f"## Stale Documents ({len(stale)})")
        lines.append(f"")
        lines.append(f"| File | Age | Threshold | Overdue |")
        lines.append(f"|------|-----|-----------|---------|")
        for r in sorted(stale, key=lambda x: -(x["age_days"] or 0)):
            rel = r["filepath"].relative_to(BRAIN_ROOT)
            over = r["age_days"] - r["threshold_days"]
            lines.append(f"| `{rel}` | {r['age_days']}d | {r['threshold_days']}d ({r['sensitivity']}) | {over}d |")
        lines.append(f"")

    if no_date:
        lines.append(f"## Missing Dates ({len(no_date)})")
        lines.append(f"")
        for r in sorted(no_date, key=lambda x: str(x["filepath"])):
            rel = r["filepath"].relative_to(BRAIN_ROOT)
            lines.append(f"- `{rel}`")
        lines.append(f"")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Audit corpus freshness")
    parser.add_argument("file", nargs="?", help="Specific file to audit")
    parser.add_argument("--domain", help="Audit a specific domain")
    parser.add_argument("--all", action="store_true", help="Audit all corpus files")
    parser.add_argument("--stale-only", action="store_true",
                        help="Only show stale documents")
    parser.add_argument("--format", choices=["text", "markdown"], default="text",
                        help="Output format (default: text)")
    parser.add_argument("--exit-code", action="store_true",
                        help="Exit 1 if any stale documents found")
    args = parser.parse_args()

    # Collect files
    files = []
    if args.file:
        files = [Path(args.file)]
    elif args.domain:
        domain_dir = CORPUS_DIR / args.domain
        if not domain_dir.exists():
            print(f"Error: Domain not found: {args.domain}", file=sys.stderr)
            sys.exit(1)
        files = sorted(f for f in domain_dir.rglob("*")
                       if f.is_file() and f.suffix in (".md", ".txt")
                       and not f.name.startswith("_") and not f.name.startswith("."))
    elif args.all:
        files = sorted(f for f in CORPUS_DIR.rglob("*")
                       if f.is_file() and f.suffix in (".md", ".txt")
                       and not f.name.startswith("_") and not f.name.startswith("."))
    else:
        parser.error("Specify a file, --domain, or --all")

    if not files:
        print("No files to audit.")
        return

    today = date.today()
    results = [audit_file(f, today) for f in files]

    if args.format == "markdown":
        print(format_markdown(results))
    else:
        print(format_text(results, args.stale_only))

    if args.exit_code:
        stale_count = sum(1 for r in results if r["stale"])
        if stale_count > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
