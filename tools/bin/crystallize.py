#!/usr/bin/env python3
"""
crystallize.py — Multi-resolution knowledge distillation.

The core of the Crystallized Intelligence for Agents framework. Reads all knowledge
in a domain and produces:

  Layer 4: seed.md        (~200 tokens)  Domain DNA — core principles + heuristics
  Layer 3: principles.md  (~2K tokens)   Compressed rules, frameworks, relationships
  Layer 2: (existing)     (~20K tokens)  Full articles (tagged, not generated)
  Layer 1: (existing)     (~200K tokens) Raw transcripts, book chapters
  Layer 0: (existing)     (unlimited)    Unprocessed scans, dumps

Also generates:
  graph.yaml   — Crystal graph of concept connections
  persona.md   — Pre-compiled expert persona for agent system prompts

Usage:
  python tools/bin/crystallize.py --domain my-domain
  python tools/bin/crystallize.py --domain my-domain --dry-run
  python tools/bin/crystallize.py --all
  python tools/bin/crystallize.py --domain my-domain --local  # Heuristic distillation (no API)
  python tools/bin/crystallize.py --domain my-domain --local --force  # Overwrite existing _crystal/

Requires: ANTHROPIC_API_KEY environment variable for full AI crystallization.
Without it, --local distills heuristically from your knowledge files (no placeholders).

Requires Python 3.9+ (see README.md).
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional

_TOOLS = Path(__file__).resolve().parent.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
from lib.runtime import require_python, resolve_brain_root  # noqa: E402

require_python()

DEFAULT_BRAIN_ROOT = Path(__file__).resolve().parent.parent.parent
BRAIN_ROOT = DEFAULT_BRAIN_ROOT
CORPUS_DIR = BRAIN_ROOT / "corpus"


def get_brain_author() -> str:
    """Read the brain owner's name from brain.yaml, fall back to 'Brain Author'."""
    brain_yaml = BRAIN_ROOT / "brain.yaml"
    if brain_yaml.exists():
        try:
            text = brain_yaml.read_text(encoding="utf-8")
            m = re.search(r"maintainers:\s*\n\s*-\s*name:\s*[\"']?([^\"'\n]+)[\"']?", text)
            if m:
                return m.group(1).strip()
        except Exception:
            pass
    return "Brain Author"

# Target token counts (approximate, 1 token ≈ 4 chars)
SEED_TARGET_CHARS = 800       # ~200 tokens
PRINCIPLES_TARGET_CHARS = 8000  # ~2000 tokens
PERSONA_TARGET_CHARS = 12000    # ~3000 tokens


def count_tokens_approx(text: str) -> int:
    """Approximate token count (1 token ≈ 4 characters)."""
    return len(text) // 4


def read_domain_knowledge(domain: str) -> dict:
    """Read all knowledge files in a domain and return structured content."""
    domain_dir = CORPUS_DIR / domain
    if not domain_dir.exists():
        print(f"Error: Domain '{domain}' not found at {domain_dir}", file=sys.stderr)
        sys.exit(1)

    result = {
        "domain": domain,
        "knowledge_files": [],
        "source_files": [],
        "example_files": [],
        "total_words": 0,
        "domain_yaml": None,
    }

    # Read _domain.yaml
    domain_yaml = domain_dir / "_domain.yaml"
    if domain_yaml.exists():
        result["domain_yaml"] = domain_yaml.read_text(encoding="utf-8")

    # Walk the domain directory
    for fpath in sorted(domain_dir.rglob("*")):
        if not fpath.is_file():
            continue
        if fpath.name.startswith(".") or fpath.name.startswith("_"):
            continue
        if fpath.suffix not in (".md", ".txt"):
            continue

        try:
            content = fpath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        rel = fpath.relative_to(domain_dir)
        parts = rel.parts
        if parts and parts[0] == "_crystal":
            continue

        word_count = len(content.split())
        result["total_words"] += word_count

        entry = {
            "path": str(rel),
            "title": extract_title(content, fpath.name),
            "word_count": word_count,
            "content": content,
        }

        # Classify by location
        parts = rel.parts
        if len(parts) > 0 and parts[0] == "sources":
            result["source_files"].append(entry)
        elif len(parts) > 0 and parts[0] == "examples":
            result["example_files"].append(entry)
        else:
            result["knowledge_files"].append(entry)

    return result


def extract_title(content: str, filename: str) -> str:
    """Extract title from frontmatter or first heading."""
    # Try frontmatter
    match = re.search(r'^---\s*\n.*?title:\s*["\']?(.+?)["\']?\s*\n.*?---', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Try first heading
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    # Fallback to filename
    return filename.replace(".md", "").replace("-", " ").title()


def build_knowledge_summary(data: dict) -> str:
    """Build a summary of all knowledge in the domain for the LLM prompt."""
    lines = []
    lines.append(f"Domain: {data['domain']}")
    lines.append(f"Total files: {len(data['knowledge_files'])} knowledge, "
                 f"{len(data['source_files'])} sources, "
                 f"{len(data['example_files'])} examples")
    lines.append(f"Total words: {data['total_words']:,}")
    lines.append("")

    # Include full knowledge articles (they're the processed Layer 2)
    for entry in data["knowledge_files"]:
        lines.append(f"## {entry['title']}")
        lines.append(f"Path: {entry['path']} | Words: {entry['word_count']}")
        # Include content but cap at ~5000 words per article for the prompt
        content = entry["content"]
        words = content.split()
        if len(words) > 5000:
            content = " ".join(words[:5000]) + "\n\n[...truncated...]"
        lines.append(content)
        lines.append("")

    # Include source titles (not full content — too large)
    if data["source_files"]:
        lines.append("## Source Materials (titles only)")
        for entry in data["source_files"]:
            lines.append(f"- {entry['title']} ({entry['word_count']} words) — {entry['path']}")
        lines.append("")

    return "\n".join(lines)


def crystallize_with_api(domain: str, data: dict, api_key: str) -> dict:
    """Use Claude API to crystallize knowledge into layers."""
    import urllib.request

    knowledge_summary = build_knowledge_summary(data)

    # ── Generate Seed (Layer 4) ─────────────────────────────────────
    seed_prompt = f"""You are distilling the complete knowledge of the "{domain}" domain into its absolute essence — the "Domain DNA."

This seed must capture in ~200 tokens:
1. The 3-5 core principles that govern this domain
2. The key decision heuristics (if X, then Y)
3. The most critical insight that separates experts from novices

An agent reading ONLY this seed should immediately understand what this domain is about and how to think about problems in it.

Here is all the knowledge in this domain:

{knowledge_summary[:80000]}

Write the seed as a concise, information-dense paragraph. No headers, no bullets — just pure distilled understanding. Target: ~200 tokens."""

    # ── Generate Principles (Layer 3) ───────────────────────────────
    principles_prompt = f"""You are compressing the complete knowledge of the "{domain}" domain into a principles document (~2000 tokens).

This should contain:
1. **Core Frameworks**: The 3-5 most important frameworks/models in this domain (name + how they work in 2-3 sentences)
2. **Key Rules**: The 10-15 most important rules/principles that govern success in this domain
3. **Common Mistakes**: The 5-7 most common mistakes and how to avoid them
4. **Decision Tree**: A brief guide for "given situation X, the best approach is Y"
5. **Cross-Domain Links**: How this domain connects to related domains

An agent reading this after the seed should be able to handle 80% of tasks in this domain without needing to read full articles.

Here is all the knowledge:

{knowledge_summary[:80000]}

Write as structured markdown with clear sections. Target: ~2000 tokens."""

    # ── Generate Crystal Graph ──────────────────────────────────────
    graph_prompt = f"""You are mapping the concept relationships in the "{domain}" domain.

For each major concept/framework/technique in this domain, provide:
- A one-sentence "seed" description (10-50 tokens)
- Connections to other concepts with relationship type and weight (0.0-1.0)

Output as YAML:

```yaml
nodes:
  concept-slug:
    seed: "One-sentence distillation"
    connections:
      - target: other-concept-slug
        weight: 0.8
        relationship: "grounded-in"  # or: enables, constrained-by, derived-from, alternative-to, prerequisite-for
```

Here is all the knowledge:

{knowledge_summary[:80000]}

Identify the 10-20 most important concepts and map their connections. Output ONLY the YAML, no explanation."""

    # ── Generate Persona ────────────────────────────────────────────
    persona_prompt = f"""You are creating an expert persona system prompt for the "{domain}" domain.

This persona will be loaded into an AI agent's system prompt to give it domain mastery. It should:
1. Define the agent's expertise and perspective
2. Include the key principles and frameworks (embedded, not referenced)
3. Provide decision-making guidance for common scenarios
4. Include the voice/tone appropriate for this domain
5. Specify what the agent should ALWAYS do and NEVER do in this domain

The persona should be self-contained — an agent with this prompt and no other context should be able to operate as a competent domain expert for 80% of tasks.

Here is all the knowledge:

{knowledge_summary[:80000]}

Write as a system prompt. Target: ~3000 tokens. Start with "You are..."."""

    results = {}
    prompts = {
        "seed": seed_prompt,
        "principles": principles_prompt,
        "graph": graph_prompt,
        "persona": persona_prompt,
    }

    for name, prompt in prompts.items():
        print(f"  Crystallizing {name}...")
        body = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}]
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                response = json.loads(resp.read().decode("utf-8"))
                text = response["content"][0]["text"]
                results[name] = text
                tokens = count_tokens_approx(text)
                print(f"    → {tokens} tokens")
        except Exception as e:
            print(f"    ERROR: {e}", file=sys.stderr)
            results[name] = None

    return results


def strip_frontmatter(content: str) -> str:
    """Return markdown body without YAML frontmatter."""
    match = re.match(r"^---\s*\n.*?\n---\s*\n", content, re.DOTALL)
    return content[match.end() :] if match else content


def extract_bullets(body: str, limit: int = 40) -> list[str]:
    """Pull bullet and numbered list items from markdown body."""
    bullets: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        for pattern in (r"^[-*]\s+(.+)$", r"^\d+\.\s+(.+)$"):
            match = re.match(pattern, stripped)
            if match:
                text = match.group(1).strip()
                if len(text) > 12 and text not in bullets:
                    bullets.append(text)
                break
        if len(bullets) >= limit:
            break
    return bullets


def extract_h2_sections(body: str) -> list[tuple[str, str]]:
    """Split body into (heading, content) pairs for level-2 sections."""
    sections: list[tuple[str, str]] = []
    current_title: Optional[str] = None
    current_lines: list[str] = []
    for line in body.splitlines():
        match = re.match(r"^##\s+(.+)$", line)
        if match:
            if current_title:
                sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = match.group(1).strip()
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)
    if current_title:
        sections.append((current_title, "\n".join(current_lines).strip()))
    return sections


def first_sentences(text: str, max_sentences: int = 2) -> str:
    """Return the first few sentences from prose."""
    cleaned = re.sub(r"\s+", " ", text.strip())
    if not cleaned:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return " ".join(parts[:max_sentences]).strip()


def truncate_chars(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def slugify_concept(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "concept"


def _prioritize_knowledge(entries: list[dict]) -> list[dict]:
    """Prefer fundamentals / shorter guides for seed extraction."""

    def sort_key(entry: dict) -> tuple[int, int]:
        path = entry["path"].lower()
        priority = 0
        if "fundamental" in path or "basics" in path or "intro" in path:
            priority -= 2
        if "knowledge/" in path:
            priority -= 1
        return (priority, entry["word_count"])

    return sorted(entries, key=sort_key)


def crystal_is_placeholder(filepath: Path) -> bool:
    """True when an existing crystal file looks like an empty stub."""
    if not filepath.is_file():
        return True
    text = filepath.read_text(encoding="utf-8", errors="ignore")
    markers = (
        "Replace this template",
        "[SEED —",
        "[PRINCIPLES —",
        "[PERSONA —",
        "example-concept:",
        "[Replace with actual concepts",
    )
    return any(marker in text for marker in markers)


def generate_local_distillation(domain: str, data: dict) -> dict:
    """Distill crystal layers from corpus text without an LLM (stdlib heuristics)."""
    domain_label = domain.replace("-", " ").title()
    knowledge = _prioritize_knowledge(data["knowledge_files"])
    all_bullets: list[str] = []
    all_sections: list[tuple[str, str, str]] = []

    for entry in knowledge:
        body = strip_frontmatter(entry["content"])
        all_bullets.extend(extract_bullets(body))
        for title, section_body in extract_h2_sections(body):
            all_sections.append((entry["title"], title, section_body))

    seed_parts: list[str] = []
    for entry in knowledge[:8]:
        body = strip_frontmatter(entry["content"])
        prose = re.sub(r"^#.+$", "", body, flags=re.MULTILINE)
        prose = re.sub(r"^##.+$", "", prose, flags=re.MULTILINE)
        sentence = first_sentences(prose, max_sentences=2)
        if sentence:
            seed_parts.append(f"- **{entry['title']}**: {sentence}")
    if not seed_parts and all_bullets:
        seed_parts = [f"- {b}" for b in all_bullets[:6]]
    seed_body = truncate_chars(
        "\n".join(seed_parts) or f"Expert heuristics for {domain_label}.",
        SEED_TARGET_CHARS,
    )
    seed = seed_body + (
        "\n\n<!-- crystallize-local: heuristic distillation from corpus; "
        "re-run without --local after setting ANTHROPIC_API_KEY for AI synthesis -->\n"
    )

    principles_lines = [
        f"# {domain_label} — Principles",
        "",
        "## Core Frameworks",
    ]
    framework_count = 0
    for _file_title, section_title, section_body in all_sections[:12]:
        summary = first_sentences(section_body, max_sentences=2) or section_body[:200]
        principles_lines.append(f"### {section_title}")
        principles_lines.append(summary)
        principles_lines.append("")
        framework_count += 1
    if framework_count == 0 and knowledge:
        for entry in knowledge[:5]:
            principles_lines.append(f"### {entry['title']}")
            principles_lines.append(first_sentences(strip_frontmatter(entry["content"]), 3))
            principles_lines.append("")

    principles_lines.append("## Key Rules")
    rules = all_bullets[:15] or [
        f"Ground decisions in first-party knowledge under corpus/{domain}/knowledge/",
    ]
    for idx, rule in enumerate(rules, start=1):
        principles_lines.append(f"{idx}. {rule}")

    mistake_lines = [
        line for line in all_bullets if re.search(r"mistake|avoid|never|don't|do not", line, re.I)
    ]
    principles_lines.extend(["", "## Common Mistakes"])
    if mistake_lines:
        for idx, line in enumerate(mistake_lines[:8], start=1):
            principles_lines.append(f"{idx}. {line}")
    else:
        principles_lines.append("1. Skipping fundamentals before advanced technique.")

    principles_lines.extend(["", "## Decision Tree", "- If context is unclear, start from fundamentals and one variable at a time."])
    principles = truncate_chars("\n".join(principles_lines), PRINCIPLES_TARGET_CHARS)

    graph_lines = ["nodes:"]
    seen_slugs: set[str] = set()
    for _file_title, section_title, section_body in all_sections[:20]:
        slug = slugify_concept(section_title)
        if slug in seen_slugs:
            slug = f"{slug}-{len(seen_slugs)}"
        seen_slugs.add(slug)
        seed_line = first_sentences(section_body, 1) or section_title
        graph_lines.append(f"  {slug}:")
        graph_lines.append(f'    seed: "{seed_line.replace(chr(34), chr(39))}"')
        graph_lines.append("    connections: []")
    if len(graph_lines) == 1:
        graph_lines.extend(
            [
                f"  {slugify_concept(domain)}:",
                f'    seed: "Core concepts for {domain_label}"',
                "    connections: []",
            ]
        )
    graph = "\n".join(graph_lines) + "\n"

    persona_rules = "\n".join(f"- {b}" for b in rules[:10])
    persona = truncate_chars(
        f"""You are a world-class expert in {domain_label}.

## How you think
- Start from first principles, then apply domain-specific heuristics.
- Prefer concise, actionable guidance over generic advice.
- When uncertain, say what you would verify in the knowledge layer.

## Rules you always follow
{persona_rules or "- Apply the domain fundamentals before improvising."}

## Voice
Direct, practical, and specific to {domain_label}. Cite trade-offs when recommendations depend on context.
""",
        PERSONA_TARGET_CHARS,
    )

    return {
        "seed": seed,
        "principles": principles,
        "graph": graph,
        "persona": persona,
    }


def write_crystal_outputs(
    domain: str,
    results: dict,
    dry_run: bool = False,
    pipeline: str = "crystallize",
):
    """Write crystallization outputs to _crystal/ directory."""
    crystal_dir = CORPUS_DIR / domain / "_crystal"

    today = date.today().isoformat()
    brain_author = get_brain_author()

    files = {
        "seed.md": {
            "frontmatter": f"""---
title: "{domain.replace('-', ' ').title()} — Domain Seed"
content_type: knowledge
crystal_layer: 4
domain: {domain}
created: {today}
updated: {today}
quality:
  verification: self_verified
  confidence: high
source:
  type: first_party
  author: "{brain_author}"
  author_authority: owner
processing:
  status: processed
  pipeline: {pipeline}
---

""",
            "content": results.get("seed", ""),
        },
        "principles.md": {
            "frontmatter": f"""---
title: "{domain.replace('-', ' ').title()} — Principles"
content_type: knowledge
crystal_layer: 3
domain: {domain}
knowledge_type: fundamental
created: {today}
updated: {today}
quality:
  verification: self_verified
  confidence: high
source:
  type: first_party
  author: "{brain_author}"
  author_authority: owner
processing:
  status: processed
  pipeline: {pipeline}
---

""",
            "content": results.get("principles", ""),
        },
        "graph.yaml": {
            "frontmatter": "",
            "content": results.get("graph", ""),
        },
        "persona.md": {
            "frontmatter": f"""---
title: "{domain.replace('-', ' ').title()} — Expert Persona"
content_type: skill
crystal_layer: 3
domain: {domain}
created: {today}
updated: {today}
quality:
  verification: self_verified
  confidence: high
source:
  type: first_party
  author: "{brain_author}"
  author_authority: owner
processing:
  status: processed
  pipeline: {pipeline}
---

""",
            "content": results.get("persona", ""),
        },
    }

    for filename, data in files.items():
        filepath = crystal_dir / filename
        full_content = data["frontmatter"] + data["content"]

        if dry_run:
            tokens = count_tokens_approx(data["content"])
            print(f"  [dry-run] Would write: {filepath.relative_to(BRAIN_ROOT)} ({tokens} tokens)")
        else:
            crystal_dir.mkdir(parents=True, exist_ok=True)
            filepath.write_text(full_content, encoding="utf-8")
            tokens = count_tokens_approx(data["content"])
            print(f"  Written: {filepath.relative_to(BRAIN_ROOT)} ({tokens} tokens)")


def main():
    global BRAIN_ROOT, CORPUS_DIR

    parser = argparse.ArgumentParser(
        description="Crystallize domain knowledge into multi-resolution layers"
    )
    parser.add_argument("--domain", help="Domain to crystallize (e.g., my-domain)")
    parser.add_argument("--all", action="store_true", help="Crystallize all domains")
    parser.add_argument(
        "--brain-root",
        help="Brain root directory containing corpus/ (defaults to repository root)",
    )
    parser.add_argument("--local", action="store_true",
                        help="Heuristic distillation only (no API calls)")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing _crystal/ files")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without writing files")
    args = parser.parse_args()

    if not args.domain and not args.all:
        parser.error("Specify --domain or --all")

    BRAIN_ROOT = resolve_brain_root(args.brain_root, DEFAULT_BRAIN_ROOT)
    CORPUS_DIR = BRAIN_ROOT / "corpus"

    if not CORPUS_DIR.exists():
        print(f"Error: corpus directory not found at {CORPUS_DIR}", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    use_api = bool(api_key) and not args.local

    if not use_api:
        if args.local:
            print("Mode: local heuristic distillation (no API)")
        else:
            print("Mode: local heuristic distillation (ANTHROPIC_API_KEY not set)")
            print("  Set ANTHROPIC_API_KEY to enable AI-powered crystallization")
            print("  Or pass --local explicitly to distill from your knowledge files")
    else:
        print("Mode: API-powered crystallization (Claude Sonnet)")

    # Determine domains to process
    if args.all:
        domains = [d.name for d in sorted(CORPUS_DIR.iterdir())
                   if d.is_dir() and not d.name.startswith(".")]
    else:
        domains = [args.domain]

    for domain in domains:
        print(f"\n{'═' * 50}")
        print(f"Crystallizing: {domain}")
        print(f"{'═' * 50}")

        data = read_domain_knowledge(domain)
        print(f"  Knowledge files: {len(data['knowledge_files'])}")
        print(f"  Source files: {len(data['source_files'])}")
        print(f"  Example files: {len(data['example_files'])}")
        print(f"  Total words: {data['total_words']:,}")

        if data["total_words"] == 0:
            print(f"  Skipping: no content to crystallize")
            continue

        crystal_dir = CORPUS_DIR / domain / "_crystal"
        seed_path = crystal_dir / "seed.md"
        if (
            not args.force
            and not args.dry_run
            and seed_path.exists()
            and not crystal_is_placeholder(seed_path)
        ):
            print("  Skipping: _crystal/ already has distilled content (use --force to overwrite)")
            continue

        if use_api:
            results = crystallize_with_api(domain, data, api_key)
            pipeline = "crystallize"
        else:
            results = generate_local_distillation(domain, data)
            pipeline = "crystallize-local"

        write_crystal_outputs(domain, results, dry_run=args.dry_run, pipeline=pipeline)

    print(f"\nDone! Crystallized {len(domains)} domain(s).")
    if not use_api:
        print("\nNext steps:")
        print("  1. Review corpus/{domain}/_crystal/ and edit anything that needs refinement")
        print("  2. Set ANTHROPIC_API_KEY and re-run without --local for AI synthesis, OR")
        print("  3. Run: python tools/bin/brain.py verify --domain <domain>")


if __name__ == "__main__":
    main()
