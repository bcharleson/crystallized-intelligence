#!/usr/bin/env python3
"""
Initialize a new brain directory from the public framework template.

Usage:
  python tools/bin/init-brain.py --path /tmp/my-brain --name "My Brain" --domains "sales,ops"
  python tools/bin/init-brain.py --path /tmp/my-brain --name "Coffee Brain" --domains "specialty-coffee"

Requires Python 3.9+ (see README.md).
"""

import argparse
import shutil
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
from lib.runtime import require_python  # noqa: E402

require_python()


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
                f'export BRAIN_ROOT="{brain_root}"',
                f'python /path/to/crystallized-intelligence/tools/bin/brain.py bootstrap {domains[0]}',
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
