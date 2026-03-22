#!/usr/bin/env python3
"""
Initialize a new brain directory from the public framework template.

Usage:
  python tools/bin/init-brain.py --path /tmp/my-brain --name "My Brain" --domains "sales,ops"
  python tools/bin/init-brain.py --path /tmp/my-brain --name "Coffee Brain" --domains "specialty-coffee"
"""

import argparse
import shutil
import sys
from pathlib import Path


FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE_PATH = FRAMEWORK_ROOT / "brain.yaml.template"


def slugify(value: str) -> str:
    """Create a filesystem-safe slug."""
    cleaned = []
    for char in value.lower().strip():
        if char.isalnum():
            cleaned.append(char)
        elif char in {" ", "-", "_"}:
            cleaned.append("-")
    slug = "".join(cleaned)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def replace_template_fields(text: str, brain_name: str, domains: list[str]) -> str:
    """Fill the small number of template placeholders for a new brain."""
    domain_lines = []
    for domain in domains:
        domain_lines.extend(
            [
                f"    - id: {domain}",
                f'      name: "{domain.replace("-", " ").title()}"',
                f'      description: "{domain.replace("-", " ").title()} domain"',
                "      maturity: developing",
            ]
        )

    domain_block = "\n".join(domain_lines) if domain_lines else (
        "    - id: example-domain\n"
        '      name: "Example Domain"\n'
        '      description: "Replace this with your domain description"\n'
        "      maturity: developing"
    )

    text = text.replace('name: "Example Brain"', f'name: "{brain_name}"')
    text = text.replace(
        "A Crystallized Intelligence brain that compiles domain expertise into\n    agent-readable knowledge layers.",
        f"{brain_name} built on the Crystallized Intelligence framework.",
    )
    start = text.index("  domains:\n")
    end = text.index("\n  quality:\n")
    replacement = f"  domains:\n{domain_block}\n"
    return text[:start] + replacement + text[end:]


def write_domain_stub(brain_root: Path, domain: str) -> None:
    """Create a minimal domain layout so the framework works immediately."""
    domain_dir = brain_root / "corpus" / domain
    (domain_dir / "_crystal").mkdir(parents=True, exist_ok=True)
    (domain_dir / "knowledge").mkdir(parents=True, exist_ok=True)
    (domain_dir / "sources").mkdir(parents=True, exist_ok=True)
    (domain_dir / "examples").mkdir(parents=True, exist_ok=True)

    domain_yaml = domain_dir / "_domain.yaml"
    if not domain_yaml.exists():
        domain_yaml.write_text(
            "\n".join(
                [
                    f"domain: {domain}",
                    f'name: "{domain.replace("-", " ").title()}"',
                    'description: "Replace with your domain description"',
                    "",
                    "related_domains: []",
                    "",
                    "skills: []",
                    "",
                    "reading_order:",
                    "  bootstrap: []",
                    "",
                    "crystal:",
                    "  seed: _crystal/seed.md",
                    "  principles: _crystal/principles.md",
                    "  graph: _crystal/graph.yaml",
                    "  persona: _crystal/persona.md",
                    "",
                ]
            ),
            encoding="utf-8",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a new brain")
    parser.add_argument("--path", required=True, help="Directory for the new brain")
    parser.add_argument("--name", required=True, help="Brain name")
    parser.add_argument(
        "--domains",
        required=True,
        help="Comma-separated list of domain ids (e.g. sales,customer-support)",
    )
    args = parser.parse_args()

    brain_root = Path(args.path).expanduser().resolve()
    domains = [slugify(item) for item in args.domains.split(",") if slugify(item)]
    if not domains:
        print("Error: at least one valid domain is required", file=sys.stderr)
        sys.exit(1)

    if brain_root.exists() and any(brain_root.iterdir()):
        print(f"Error: target directory is not empty: {brain_root}", file=sys.stderr)
        sys.exit(1)

    brain_root.mkdir(parents=True, exist_ok=True)

    if not TEMPLATE_PATH.exists():
        print(f"Error: template not found: {TEMPLATE_PATH}", file=sys.stderr)
        sys.exit(1)

    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    brain_yaml = replace_template_fields(template_text, args.name, domains)
    (brain_root / "brain.yaml").write_text(brain_yaml, encoding="utf-8")

    for domain in domains:
        write_domain_stub(brain_root, domain)

    readme_path = brain_root / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                f"# {args.name}",
                "",
                "Initialized with Crystallized Intelligence.",
                "",
                "## Next Steps",
                "",
                "1. Add content under `corpus/{domain}/knowledge/`, `sources/`, and `examples/`.",
                "2. Run the crystallizer in local mode first.",
                "3. Replace the generated templates with real distilled knowledge.",
                "",
                "Example:",
                "",
                "```bash",
                f'python /path/to/crystallized-intelligence/tools/bin/crystallize.py --brain-root "{brain_root}" --domain {domains[0]} --local',
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(f"Initialized brain at {brain_root}")
    print(f"Domains: {', '.join(domains)}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
init-brain.py — Scaffold a new Crystallized Intelligence brain.

Creates the full directory structure, brain.yaml, domain configs,
and starter files for a new brain project.

Usage:
  python tools/bin/init-brain.py \
    --name "DevOps Mastery" \
    --domains "kubernetes,docker,ci-cd,monitoring" \
    --output ~/my-brain

  python tools/bin/init-brain.py \
    --name "Marketing Brain" \
    --domains "seo,content,social-media,email-marketing,analytics" \
    --owner "Jane Smith" \
    --output ./marketing-brain

Uses only Python stdlib — no pip dependencies.
"""

import argparse
import re
import sys
from pathlib import Path


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def titleize(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").title()


def generate_brain_yaml(name: str, domains: list[str], owner: str) -> str:
    domain_entries = []
    for d in domains:
        domain_entries.append(
            f"    - id: {d}\n"
            f"      name: \"{titleize(d)}\"\n"
            f"      description: \"\"\n"
            f"      maturity: nascent"
        )

    return f"""brain:
  name: "{name}"
  version: "1.0.0"
  description: >
    A Crystallized Intelligence brain for {name.lower()}.
    Multi-resolution knowledge distillation for agents and humans.
  framework_version: "1.0.0"

  maintainers:
    - name: "{owner}"
      role: owner

  domains:
{chr(10).join(domain_entries)}

  quality:
    source_weights:
      first_party: 1.0
      original_framework: 1.0
      lived_experience: 1.0
      book: 1.0
      academic_paper: 1.0
      official_docs: 1.0
      conference_talk: 0.85
      workshop: 0.85
      tutorial: 0.70
      course: 0.70
      technical_blog: 0.70
      podcast: 0.55
      youtube_video: 0.55
      social_media: 0.35
      forum_post: 0.35
      tweet_thread: 0.35

    override_rules:
      - if: {{ author_authority: "owner" }}
        weight_boost: 0.25
        note: "Brain owner's first-party knowledge"

    require_provenance: true
    min_source_tier: 5

    auto_stale_days:
      high: 90
      medium: 180
      low: 365

  crystal:
    layers:
      - name: seed
        target_tokens: 200
        description: "Domain DNA — core principles and decision heuristics"
      - name: principles
        target_tokens: 2000
        description: "Compressed rules, frameworks, key relationships"
      - name: knowledge
        target_tokens: 20000
        description: "Full articles, techniques, case studies"
      - name: sources
        target_tokens: 200000
        description: "Raw transcripts, book chapters, articles"
      - name: raw
        target_tokens: null
        description: "Unprocessed scans, dumps, recordings"

  access:
    default: public
    private_paths:
      - private/
"""


def generate_domain_yaml(domain: str) -> str:
    return f"""domain:
  id: {domain}
  name: "{titleize(domain)}"
  description: ""
  maturity: nascent

  related_domains: []

  reading_order:
    - _crystal/seed.md
    - _crystal/principles.md

  skills: []
"""


def generate_gitignore() -> str:
    return """# Crystallized Intelligence Brain

# Private content (proprietary)
# private/

# Book full-text (copyrighted)
**/full-text.md

# Local state
.brain/

# Scan staging
**/tofu-brain-scans/

# OS files
.DS_Store
Thumbs.db

# Editor
.vscode/
.idea/
*.swp
*.swo
"""


def generate_readme(name: str, domains: list[str], owner: str) -> str:
    domain_rows = "\n".join(f"| `{d}` | |" for d in domains)

    return f"""# {name}

A **Crystallized Intelligence** knowledge base — multi-resolution, quality-weighted domain mastery for AI agents and humans.

## Structure

```
brain.yaml              Brain manifest
corpus/                 All knowledge content, organized by domain
  {{domain}}/
    _domain.yaml        Domain config
    _crystal/           Pre-compiled layers (seed, principles, graph, persona)
    knowledge/          Layer 2: Processed articles
    sources/            Layer 1: Raw inputs (transcripts, books, articles)
    examples/           Working examples, templates
private/                Proprietary content (gitignored)
```

## Domains

| Domain | Description |
|--------|-------------|
{domain_rows}

## For Agents

```
1. Read brain.yaml                           → what domains exist
2. Read corpus/{{domain}}/_domain.yaml         → domain overview + reading order
3. Read corpus/{{domain}}/_crystal/seed.md     → 200-token domain DNA
4. Read corpus/{{domain}}/_crystal/principles.md → 2K-token compressed frameworks
5. Expand to knowledge/ or sources/ as needed
```

## Quality System

| Tier | Sources | Weight |
|------|---------|--------|
| 0 | First-party, original frameworks, lived experience | 1.25 |
| 1 | Books, academic papers, official docs | 1.0 |
| 2 | Conference talks, workshops, whitepapers | 0.85 |
| 3 | Tutorials, courses, technical blogs | 0.70 |
| 4 | Podcasts, YouTube videos, newsletters | 0.55 |
| 5 | Social media, forum posts, tweets | 0.35 |

## Getting Started

1. Add knowledge to `corpus/{{domain}}/knowledge/`
2. Add raw sources to `corpus/{{domain}}/sources/`
3. Run crystallization to generate seed + principles layers

Maintained by {owner}.
"""


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a new Crystallized Intelligence brain"
    )
    parser.add_argument("--name", required=True, help="Brain name")
    parser.add_argument("--domains", required=True,
                        help="Comma-separated domain IDs")
    parser.add_argument("--owner", default="Anonymous",
                        help="Brain owner name")
    parser.add_argument("--output", required=True,
                        help="Output directory")
    args = parser.parse_args()

    domains = [slugify(d.strip()) for d in args.domains.split(",") if d.strip()]
    if not domains:
        print("Error: At least one domain is required.", file=sys.stderr)
        sys.exit(1)

    output = Path(args.output).resolve()

    if output.exists() and any(output.iterdir()):
        print(f"Error: Output directory is not empty: {output}", file=sys.stderr)
        sys.exit(1)

    print(f"Creating brain: {args.name}")
    print(f"Domains: {', '.join(domains)}")
    print(f"Output: {output}")
    print()

    # Create root files
    output.mkdir(parents=True, exist_ok=True)
    (output / "brain.yaml").write_text(
        generate_brain_yaml(args.name, domains, args.owner)
    )
    (output / ".gitignore").write_text(generate_gitignore())
    (output / "README.md").write_text(
        generate_readme(args.name, domains, args.owner)
    )

    # Create corpus structure
    for domain in domains:
        domain_dir = output / "corpus" / domain
        domain_dir.mkdir(parents=True, exist_ok=True)

        # _domain.yaml
        (domain_dir / "_domain.yaml").write_text(generate_domain_yaml(domain))

        # _crystal directory with placeholders
        crystal_dir = domain_dir / "_crystal"
        crystal_dir.mkdir(exist_ok=True)
        (crystal_dir / ".gitkeep").write_text("")

        # Content directories
        for subdir in ("knowledge", "sources", "examples"):
            d = domain_dir / subdir
            d.mkdir(exist_ok=True)
            (d / ".gitkeep").write_text("")

        print(f"  Created: corpus/{domain}/")

    # Create private directory
    private_dir = output / "private"
    private_dir.mkdir(exist_ok=True)
    (private_dir / ".gitkeep").write_text("")

    print(f"\nBrain scaffolded at: {output}")
    print(f"\nNext steps:")
    print(f"  1. cd {output}")
    print(f"  2. git init && git add -A && git commit -m 'init brain'")
    print(f"  3. Add knowledge to corpus/{{domain}}/knowledge/")
    print(f"  4. Run crystallization when ready")


if __name__ == "__main__":
    main()
