#!/usr/bin/env python3
"""
classify.py — Auto-classify documents with quality metadata.

Reads files in the corpus and reports suggested YAML frontmatter fields:
  - source_tier (0-5) based on source type
  - freshness sensitivity based on domain
  - confidence based on word count and structure
  - crystal_layer assignment

Uses heuristics only — no LLM calls, no external dependencies.

Usage:
  python tools/bin/classify.py corpus/my-domain/knowledge/some-article.md
  python tools/bin/classify.py --domain my-domain --brain-root ~/my-brain
  python tools/bin/classify.py --all --brain-root ~/my-brain
  python tools/bin/classify.py --all --dry-run               # Preview changes

Requires Python 3.9+ (see README.md).
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
from lib.runtime import require_python  # noqa: E402

require_python()

DEFAULT_BRAIN_ROOT = Path(__file__).resolve().parent.parent.parent
BRAIN_ROOT = DEFAULT_BRAIN_ROOT
CORPUS_DIR = BRAIN_ROOT / "corpus"

# Source type → tier mapping
SOURCE_TIER = {
    # Tier 0
    "first_party": 0, "original_framework": 0,
    "proprietary_insight": 0, "lived_experience": 0,
    # Tier 1
    "book": 1, "academic_paper": 1, "official_docs": 1, "specification": 1,
    # Tier 2
    "conference_talk": 2, "workshop": 2, "whitepaper": 2, "technical_report": 2,
    # Tier 3
    "tutorial": 3, "course": 3, "technical_blog": 3, "case_study": 3,
    # Tier 4
    "podcast": 4, "interview": 4, "youtube_video": 4, "newsletter": 4,
    # Tier 5
    "social_media": 5, "forum_post": 5, "tweet_thread": 5, "reddit_comment": 5,
}

# Freshness sensitivity is configured per domain in corpus/{domain}/_domain.yaml
# using the `freshness_sensitivity` field (values: high, medium, low).
# High = ~90 days (fast-moving, e.g. AI tooling), Medium = ~180 days, Low = ~365 days.
# Falls back to "medium" if not configured.
_FRESHNESS_CACHE: dict[str, str] = {}

def get_domain_sensitivity(domain: str) -> str:
    """Read freshness_sensitivity from _domain.yaml, fall back to 'medium'."""
    if domain in _FRESHNESS_CACHE:
        return _FRESHNESS_CACHE[domain]
    import re as _re
    domain_yaml = CORPUS_DIR / domain / "_domain.yaml"
    sensitivity = "medium"
    if domain_yaml.exists():
        try:
            text = domain_yaml.read_text(encoding="utf-8")
            m = _re.search(r"^freshness_sensitivity:\s*(\w+)", text, _re.MULTILINE)
            if m and m.group(1).lower() in ("high", "medium", "low"):
                sensitivity = m.group(1).lower()
        except Exception:
            pass
    _FRESHNESS_CACHE[domain] = sensitivity
    return sensitivity

# Author authority → tier boost
AUTHORITY_TIER_BOOST = {
    "owner": -1,      # Push up one tier
    "creator": -1,
}


def parse_frontmatter(filepath: Path) -> tuple[dict, str, str]:
    """Parse YAML frontmatter from a markdown file.

    Returns (frontmatter_dict, frontmatter_raw, body).
    """
    text = filepath.read_text(encoding="utf-8", errors="ignore")

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if not match:
        return {}, "", text

    fm_raw = match.group(1)
    body = match.group(2)

    # Simple YAML parser (stdlib only, handles our schema)
    fm = {}
    current_key = None
    current_section = None

    for line in fm_raw.split("\n"):
        # Section headers (source:, quality:, freshness:, processing:)
        section_match = re.match(r"^(\w+):\s*$", line)
        if section_match:
            current_section = section_match.group(1)
            fm[current_section] = {}
            continue

        # Key-value in section
        if current_section:
            kv_match = re.match(r"^\s+(\w+):\s*(.+)$", line)
            if kv_match:
                key = kv_match.group(1)
                value = kv_match.group(2).strip().strip('"').strip("'")
                fm[current_section][key] = value
                continue

        # Top-level key-value
        kv_match = re.match(r"^(\w+):\s*(.+)$", line)
        if kv_match:
            key = kv_match.group(1)
            value = kv_match.group(2).strip().strip('"').strip("'")
            fm[key] = value
            current_section = None

    return fm, fm_raw, body


def classify_file(filepath: Path) -> dict:
    """Classify a file and return suggested metadata updates."""
    fm, fm_raw, body = parse_frontmatter(filepath)

    suggestions = {}

    # Determine domain from path
    rel = filepath.relative_to(CORPUS_DIR)
    domain = rel.parts[0] if rel.parts else "unknown"
    suggestions["domain"] = domain

    # Determine content_type from path
    parts = rel.parts
    if "_crystal" in parts:
        suggestions["content_type"] = "knowledge"
    elif "sources" in parts:
        suggestions["content_type"] = "source"
        if "books" in parts:
            suggestions["content_type"] = "book"
        elif "transcripts" in parts:
            suggestions["content_type"] = "source"
    elif "examples" in parts:
        suggestions["content_type"] = "example"
    elif "knowledge" in parts:
        suggestions["content_type"] = "knowledge"
    else:
        suggestions["content_type"] = fm.get("content_type", "knowledge")

    # Source tier
    source_type = fm.get("source", {}).get("type", "") if isinstance(fm.get("source"), dict) else ""
    if source_type:
        tier = SOURCE_TIER.get(source_type, 4)
    else:
        # Infer from filename and content
        name = filepath.name.lower()
        if re.match(r"\d{4}-\d{2}-\d{2}-\w{11}", name):
            tier = 4  # YouTube transcript
        elif filepath.suffix == ".json":
            tier = 3  # Reference data
        else:
            tier = 3  # Default to tutorial/blog level
    suggestions["source_tier"] = tier

    # Author authority boost
    authority = fm.get("source", {}).get("author_authority", "") if isinstance(fm.get("source"), dict) else ""
    if authority in AUTHORITY_TIER_BOOST:
        suggestions["source_tier"] = max(0, tier + AUTHORITY_TIER_BOOST[authority])

    # Freshness sensitivity — reads from _domain.yaml, falls back to "medium"
    suggestions["freshness_sensitivity"] = get_domain_sensitivity(domain)

    # Confidence based on word count and structure
    word_count = len(body.split())
    has_headers = bool(re.search(r"^##?\s", body, re.MULTILINE))
    has_code = bool(re.search(r"```", body))

    if word_count < 100:
        suggestions["confidence"] = "low"
    elif word_count < 500:
        suggestions["confidence"] = "medium"
    else:
        suggestions["confidence"] = "high"
    if has_headers and has_code and word_count > 1000:
        suggestions["confidence"] = "high"

    # Crystal layer
    if "_crystal" in str(rel):
        if "seed" in filepath.name:
            suggestions["crystal_layer"] = 4
        elif "principles" in filepath.name or "persona" in filepath.name:
            suggestions["crystal_layer"] = 3
        else:
            suggestions["crystal_layer"] = 3
    elif "sources" in parts:
        suggestions["crystal_layer"] = 1
    elif "knowledge" in parts:
        suggestions["crystal_layer"] = 2
    elif "examples" in parts:
        suggestions["crystal_layer"] = 2

    # Knowledge type inference
    if "knowledge" in parts:
        subparts = [p for p in parts if p not in (domain, "knowledge")]
        if "fundamentals" in subparts:
            suggestions["knowledge_type"] = "fundamental"
        elif "techniques" in subparts:
            suggestions["knowledge_type"] = "technique"
        elif "reference" in subparts:
            suggestions["knowledge_type"] = "reference"
        elif "case-studies" in subparts:
            suggestions["knowledge_type"] = "case_study"
        elif "opinions" in subparts:
            suggestions["knowledge_type"] = "opinion"

    suggestions["word_count"] = word_count
    suggestions["has_frontmatter"] = bool(fm_raw)

    return suggestions


def _display_path(filepath: Path) -> Path:
    """Path for display — relative to brain root when possible."""
    try:
        return filepath.relative_to(BRAIN_ROOT)
    except ValueError:
        return filepath


def print_classification(filepath: Path, suggestions: dict, verbose: bool = True):
    """Print classification results."""
    rel = _display_path(filepath)
    if verbose:
        print(f"\n  {rel}")
        print(f"    domain: {suggestions['domain']}")
        print(f"    content_type: {suggestions['content_type']}")
        print(f"    source_tier: {suggestions['source_tier']}")
        print(f"    freshness: {suggestions['freshness_sensitivity']}")
        print(f"    confidence: {suggestions['confidence']}")
        print(f"    words: {suggestions['word_count']}")
        if "crystal_layer" in suggestions:
            print(f"    crystal_layer: {suggestions['crystal_layer']}")
        if "knowledge_type" in suggestions:
            print(f"    knowledge_type: {suggestions['knowledge_type']}")
        print(f"    has_frontmatter: {suggestions['has_frontmatter']}")
    else:
        tier = suggestions['source_tier']
        conf = suggestions['confidence'][:1].upper()
        fresh = suggestions['freshness_sensitivity'][:1].upper()
        fm = "✓" if suggestions['has_frontmatter'] else "✗"
        print(f"  T{tier} {conf} {fresh} {fm}  {rel}")


def main():
    global BRAIN_ROOT, CORPUS_DIR

    parser = argparse.ArgumentParser(
        description="Auto-classify corpus documents with quality metadata"
    )
    parser.add_argument("file", nargs="?", help="Specific file to classify")
    parser.add_argument("--domain", help="Classify all files in a domain")
    parser.add_argument("--all", action="store_true", help="Classify all corpus files")
    parser.add_argument(
        "--brain-root",
        help="Brain root directory containing corpus/ (defaults to repository root)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--summary", action="store_true", help="Show summary statistics")
    args = parser.parse_args()

    if args.brain_root:
        BRAIN_ROOT = Path(args.brain_root).expanduser().resolve()
        CORPUS_DIR = BRAIN_ROOT / "corpus"
        _FRESHNESS_CACHE.clear()

    if not CORPUS_DIR.exists():
        print(f"Error: corpus directory not found at {CORPUS_DIR}", file=sys.stderr)
        sys.exit(1)

    if not args.file and not args.domain and not args.all:
        parser.error("Specify a file, --domain, or --all")

    # Collect files to classify
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

    print(f"Classifying {len(files)} files...")

    # Track statistics
    stats = {
        "total": 0, "with_frontmatter": 0, "without_frontmatter": 0,
        "by_tier": {}, "by_confidence": {}, "by_domain": {},
    }

    for filepath in files:
        if not filepath.exists():
            print(f"  SKIP (not found): {filepath}", file=sys.stderr)
            continue

        suggestions = classify_file(filepath)
        stats["total"] += 1
        if suggestions["has_frontmatter"]:
            stats["with_frontmatter"] += 1
        else:
            stats["without_frontmatter"] += 1

        tier = suggestions["source_tier"]
        stats["by_tier"][tier] = stats["by_tier"].get(tier, 0) + 1
        conf = suggestions["confidence"]
        stats["by_confidence"][conf] = stats["by_confidence"].get(conf, 0) + 1
        domain = suggestions["domain"]
        stats["by_domain"][domain] = stats["by_domain"].get(domain, 0) + 1

        print_classification(filepath, suggestions, verbose=args.verbose)

    if args.summary or len(files) > 5:
        print(f"\n{'═' * 50}")
        print(f"Classification Summary")
        print(f"{'═' * 50}")
        print(f"Total files: {stats['total']}")
        print(f"With frontmatter: {stats['with_frontmatter']}")
        print(f"Without frontmatter: {stats['without_frontmatter']}")
        print(f"\nBy tier:")
        for tier in sorted(stats["by_tier"]):
            print(f"  Tier {tier}: {stats['by_tier'][tier]} files")
        print(f"\nBy confidence:")
        for conf in ("high", "medium", "low"):
            if conf in stats["by_confidence"]:
                print(f"  {conf}: {stats['by_confidence'][conf]} files")
        print(f"\nBy domain:")
        for domain, count in sorted(stats["by_domain"].items(), key=lambda x: -x[1]):
            print(f"  {domain}: {count} files")


if __name__ == "__main__":
    main()
