#!/usr/bin/env python3
"""
brain — Unified CLI for Crystallized Intelligence brains.

Layer-first retrieval for agents: bootstrap (low tokens) then expand on demand.

Usage:
  export BRAIN_ROOT=~/my-brain   # or pass --brain-root on every command

  brain init --path ~/my-brain --name "Acme Brain" --domains "ops,sales"
  brain domains
  brain bootstrap specialty-coffee
  brain expand specialty-coffee --query "grind" --max-tokens 4000
  brain search specialty-coffee "extraction"
  brain get specialty-coffee knowledge/fundamentals/dialing-in-basics.md

Pipeline commands delegate to existing tools:
  brain classify --domain my-domain
  brain crystallize --domain my-domain --local
  brain verify --domain my-domain
  brain freshness --domain my-domain
  brain doctor
  brain demo
  brain try
  brain setup-mcp
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Union

TOOLS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS_ROOT))

from lib.brain_reader import BrainReader, DomainNotFoundError  # noqa: E402
from lib.runtime import require_python, resolve_brain_root as _resolve_brain_root  # noqa: E402

require_python()

BIN_DIR = Path(__file__).resolve().parent
DEFAULT_BRAIN_ROOT = Path(__file__).resolve().parent.parent.parent
DEMO_BRAIN_ROOT = (DEFAULT_BRAIN_ROOT / "examples" / "demo-brain").resolve()

WELCOME = """
Crystallized Intelligence — layer-first knowledge for AI agents

  Pre-compiled expertise in ~200–2K tokens (bootstrap), expand only when needed.

  First time here?
    python tools/bin/brain.py try              # 60-second demo, zero setup

  Demo brain (no config):
    python tools/bin/brain.py demo             # bootstrap JSON (~365 tokens)
    python tools/bin/brain.py doctor --brain-root examples/demo-brain

  Your own brain:
    export BRAIN_ROOT=~/my-brain
    python tools/bin/brain.py bootstrap <domain>
    python tools/bin/brain.py expand <domain> --query "..." --max-tier 3

  Commands: init, domains, bootstrap, expand, search, get, classify,
            crystallize, verify, freshness, doctor, demo, setup-mcp, try

  Run: python tools/bin/brain.py <command> --help
  Docs: README.md · docs/AGENT-INTEGRATION.md
"""


def resolve_brain_root(explicit: Optional[str]) -> Path:
    return _resolve_brain_root(explicit, DEFAULT_BRAIN_ROOT)


def ensure_brain_root(path: Path) -> Path:
    """Fail fast when BRAIN_ROOT does not look like a brain directory."""
    brain_yaml = path / "brain.yaml"
    corpus = path / "corpus"
    if brain_yaml.is_file() and corpus.is_dir():
        return path

    lines = [f"Error: brain not found at {path}", "  Expected brain.yaml and corpus/ under BRAIN_ROOT."]
    if not os.environ.get("BRAIN_ROOT") and path.resolve() == DEFAULT_BRAIN_ROOT.resolve():
        lines.extend(
            [
                "  The framework repo root is not a brain.",
                "  Try: export BRAIN_ROOT=examples/demo-brain",
                "  Or:  python tools/bin/brain.py demo",
                "  Run: python tools/bin/brain.py doctor",
            ]
        )
    else:
        lines.append("  Set BRAIN_ROOT or pass --brain-root to your brain directory.")
    print("\n".join(lines), file=sys.stderr)
    raise SystemExit(1)


def print_domain_error(exc: DomainNotFoundError) -> None:
    print(f"Error: domain '{exc.domain}' not found.", file=sys.stderr)
    if exc.available:
        print(f"  Available domains: {', '.join(exc.available)}", file=sys.stderr)
    else:
        print("  No domains under corpus/. Run: brain init --path ~/my-brain ...", file=sys.stderr)
    print("  List domains: brain domains --brain-root $BRAIN_ROOT", file=sys.stderr)
    raise SystemExit(1)


def run_reader_command(reader: BrainReader, args: argparse.Namespace) -> None:
    try:
        args.func(reader, args)
    except DomainNotFoundError as exc:
        print_domain_error(exc)


def emit(data: Union[dict, list], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, indent=2))
    else:
        print(json.dumps(data, indent=2))


def cmd_init(args: argparse.Namespace) -> None:
    script = BIN_DIR / "init-brain.py"
    cmd = [
        sys.executable,
        str(script),
        "--path",
        args.path,
        "--name",
        args.name,
        "--domains",
        args.domains,
    ]
    subprocess.run(cmd, check=True)


def cmd_domains(reader: BrainReader, args: argparse.Namespace) -> None:
    emit(reader.list_domains(), args.format)


def cmd_bootstrap(reader: BrainReader, args: argparse.Namespace) -> None:
    emit(
        reader.bootstrap(
            args.domain,
            include_persona=args.persona,
            max_tokens=args.max_tokens,
        ),
        args.format,
    )


def cmd_expand(reader: BrainReader, args: argparse.Namespace) -> None:
    emit(
        reader.expand(
            args.domain,
            layer=args.layer,
            query=args.query,
            max_tokens=args.max_tokens,
            max_tier=args.max_tier,
            max_documents=args.max_documents,
        ),
        args.format,
    )


def cmd_search(reader: BrainReader, args: argparse.Namespace) -> None:
    emit(
        reader.search(
            args.domain,
            args.query,
            max_results=args.max_results,
            max_tier=args.max_tier,
        ),
        args.format,
    )


def cmd_get(reader: BrainReader, args: argparse.Namespace) -> None:
    emit(reader.get_document(args.domain, args.path), args.format)


def cmd_doctor(args: argparse.Namespace) -> None:
    """Check environment and brain layout for first-time setup."""
    brain_root = resolve_brain_root(args.brain_root)
    checks: list[dict] = []

    py_ok = sys.version_info >= (3, 9)
    checks.append(
        {
            "name": "python",
            "ok": py_ok,
            "detail": f"{sys.version_info.major}.{sys.version_info.minor}",
        }
    )

    brain_yaml = brain_root / "brain.yaml"
    corpus = brain_root / "corpus"
    brain_ok = brain_yaml.is_file() and corpus.is_dir()
    checks.append(
        {
            "name": "brain_root",
            "ok": brain_ok,
            "path": str(brain_root),
            "detail": "brain.yaml + corpus/" if brain_ok else "missing brain.yaml or corpus/",
        }
    )

    domains: list[str] = []
    crystals: dict[str, list[str]] = {}
    if brain_ok:
        for domain_dir in sorted(corpus.iterdir()):
            if not domain_dir.is_dir() or domain_dir.name.startswith("."):
                continue
            domains.append(domain_dir.name)
            crystal_dir = domain_dir / "_crystal"
            if crystal_dir.is_dir():
                crystals[domain_dir.name] = sorted(p.name for p in crystal_dir.iterdir() if p.is_file())

    checks.append({"name": "domains", "ok": bool(domains), "count": len(domains), "ids": domains})

    demo_root = (DEFAULT_BRAIN_ROOT / "examples" / "demo-brain").resolve()
    if not brain_ok and demo_root.is_dir():
        checks.append(
            {
                "name": "demo_brain",
                "ok": True,
                "path": str(demo_root),
                "detail": "Run: export BRAIN_ROOT=examples/demo-brain && brain demo",
            }
        )

    report = {
        "ok": all(c.get("ok", True) for c in checks if c["name"] != "demo_brain"),
        "checks": checks,
        "crystals": crystals,
        "hints": [],
    }
    if not brain_ok:
        report["hints"].append("export BRAIN_ROOT=examples/demo-brain  # try the demo brain")
        report["hints"].append("brain init --path ~/my-brain --name 'My Brain' --domains 'my-domain'")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        report["hints"].append("ANTHROPIC_API_KEY unset — use crystallize --local for heuristic distillation")
    emit(report, args.format)


def _require_demo_brain() -> Path:
    if not (DEMO_BRAIN_ROOT / "brain.yaml").is_file():
        print(f"Error: demo brain not found at {DEMO_BRAIN_ROOT}", file=sys.stderr)
        raise SystemExit(1)
    return DEMO_BRAIN_ROOT


def cmd_demo(args: argparse.Namespace) -> None:
    """Run bootstrap against the bundled demo brain (no setup required)."""
    reader = BrainReader(_require_demo_brain())
    domain = args.domain or "specialty-coffee"
    try:
        payload = reader.bootstrap(domain, include_persona=False, max_tokens=args.max_tokens)
    except DomainNotFoundError as exc:
        print_domain_error(exc)
    payload["brain_root"] = str(DEMO_BRAIN_ROOT)
    payload["hint"] = "export BRAIN_ROOT=examples/demo-brain to use the demo brain for all commands"
    emit(payload, args.format)


def _excerpt(text: str, max_len: int = 220) -> str:
    one_line = " ".join(text.split())
    if len(one_line) <= max_len:
        return one_line
    return one_line[: max_len - 3].rstrip() + "..."


def cmd_try(args: argparse.Namespace) -> None:
    """Human-readable 60-second demo: bootstrap + expand, zero configuration."""
    reader = BrainReader(_require_demo_brain())
    domain = args.domain or "specialty-coffee"
    query = args.query or "grind"
    try:
        boot = reader.bootstrap(domain, max_tokens=4000)
        expand = reader.expand(domain, query=query, max_tokens=2500, max_tier=3, max_documents=3)
    except DomainNotFoundError as exc:
        print_domain_error(exc)

    total = boot["tokens_approx"] + expand["tokens_approx"]
    seed = boot.get("layers", {}).get("seed", {})
    seed_text = seed.get("content", "")

    print("Crystallized Intelligence — 60-second demo")
    print("=" * 48)
    print()
    print(f"Domain: {domain}  (demo brain, no BRAIN_ROOT needed)")
    print()
    print(f"1) bootstrap  →  {boot['tokens_approx']} tokens (crystal layers only)")
    if seed_text:
        print(f'   seed: "{_excerpt(seed_text)}"')
    print()
    print(f'2) expand --query "{query}"  →  {expand["tokens_approx"]} tokens (ranked knowledge)')
    for doc in expand.get("documents", []):
        print(f"   · {doc['title']}  (tier {doc['tier']}, ~{doc['tokens_approx']} tok)")
    print()
    print(f"Total context used: ~{total} tokens")
    print("Naive RAG often loads dozens of files (50K–100K+ tokens) per question.")
    print()
    print("Next steps:")
    print("  export BRAIN_ROOT=examples/demo-brain")
    print("  python tools/bin/brain.py doctor")
    print("  python tools/bin/brain.py bootstrap b2b-discovery")
    print("  Docs: README.md")


def cmd_setup_mcp(args: argparse.Namespace) -> None:
    """Print MCP config JSON with absolute paths for Cursor / Claude Desktop."""
    explicit = getattr(args, "brain_root", None)
    if explicit:
        brain_root = Path(explicit).expanduser().resolve()
    elif os.environ.get("BRAIN_ROOT", "").strip():
        brain_root = Path(os.environ["BRAIN_ROOT"]).expanduser().resolve()
    else:
        brain_root = (DEFAULT_BRAIN_ROOT / "examples" / "demo-brain").resolve()
    mcp_script = (BIN_DIR / "brain-mcp.py").resolve()
    config = {
        "mcpServers": {
            "crystallized-intelligence": {
                "command": sys.executable,
                "args": [str(mcp_script)],
                "env": {"BRAIN_ROOT": str(brain_root)},
            }
        }
    }
    output = getattr(args, "output", "text")
    if output == "json":
        print(json.dumps(config, indent=2))
    else:
        print("# Add to Cursor MCP settings (merge into mcpServers):")
        print(json.dumps(config, indent=2))
        print("\nThen restart Cursor. See docs/MCP-SETUP.md for details.")


def _delegate_tool(tool: str, brain_root: Path, extra: list[str]) -> None:
    script = BIN_DIR / f"{tool}.py"
    cmd = [sys.executable, str(script), "--brain-root", str(brain_root), *extra]
    result = subprocess.run(cmd)
    raise SystemExit(result.returncode)


def main() -> None:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--brain-root",
        help="Brain directory (brain.yaml + corpus/). Defaults to $BRAIN_ROOT or framework root.",
    )
    parent.add_argument(
        "--format",
        choices=("json",),
        default="json",
        help="Output format (json only for now)",
    )

    parser = argparse.ArgumentParser(
        description="Layer-first access to pre-compiled domain brains for AI agents.",
        epilog="Tip: run without a command for a quick overview, or `try` for a zero-setup demo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="Initialize a new brain directory", parents=[parent])
    p_init.add_argument("--path", required=True)
    p_init.add_argument("--name", required=True)
    p_init.add_argument("--domains", required=True, help="Comma-separated domain ids")
    p_init.set_defaults(func=cmd_init)

    p_domains = sub.add_parser("domains", help="List domains in the brain", parents=[parent])
    p_domains.set_defaults(func=cmd_domains)

    p_boot = sub.add_parser(
        "bootstrap",
        help="Load crystal layers only (~200-2K tokens) — use this first",
        parents=[parent],
    )
    p_boot.add_argument("domain")
    p_boot.add_argument("--persona", action="store_true", help="Include persona.md")
    p_boot.add_argument("--max-tokens", type=int, default=4000)
    p_boot.set_defaults(func=cmd_bootstrap)

    p_exp = sub.add_parser(
        "expand",
        help="Load knowledge/examples/sources with tier ranking and token budget",
        parents=[parent],
    )
    p_exp.add_argument("domain")
    p_exp.add_argument("--layer", choices=("knowledge", "sources", "all"), default="knowledge")
    p_exp.add_argument("--query", help="Optional keyword filter / ranking boost")
    p_exp.add_argument("--max-tokens", type=int, default=8000)
    p_exp.add_argument("--max-tier", type=int, default=5, help="Ignore docs above this tier")
    p_exp.add_argument("--max-documents", type=int, default=10)
    p_exp.set_defaults(func=cmd_expand)

    p_search = sub.add_parser(
        "search", help="Find documents by keyword (metadata only + snippet)", parents=[parent]
    )
    p_search.add_argument("domain")
    p_search.add_argument("query")
    p_search.add_argument("--max-results", type=int, default=5)
    p_search.add_argument("--max-tier", type=int, default=5)
    p_search.set_defaults(func=cmd_search)

    p_get = sub.add_parser("get", help="Fetch one document by corpus-relative path", parents=[parent])
    p_get.add_argument("domain")
    p_get.add_argument("path", help="e.g. knowledge/fundamentals/dialing-in-basics.md")
    p_get.set_defaults(func=cmd_get)

    p_classify = sub.add_parser("classify", help="Run classify.py on a domain", parents=[parent])
    p_classify.add_argument("--domain", required=True)
    p_classify.add_argument("--summary", action="store_true")

    p_cryst = sub.add_parser("crystallize", help="Run crystallize.py on a domain", parents=[parent])
    p_cryst.add_argument("--domain", required=True)
    p_cryst.add_argument("--local", action="store_true")
    p_cryst.add_argument("--force", action="store_true", help="Overwrite existing _crystal/ files")

    p_verify = sub.add_parser("verify", help="Run verify.py on a domain", parents=[parent])
    p_verify.add_argument("--domain", required=True)

    p_fresh = sub.add_parser(
        "freshness", help="Run freshness-audit.py on a domain", parents=[parent]
    )
    p_fresh.add_argument("--domain", required=True)
    p_fresh.add_argument("--stale-only", action="store_true")

    p_doctor = sub.add_parser(
        "doctor",
        help="Check Python version, BRAIN_ROOT, domains, and crystal files",
        parents=[parent],
    )
    p_doctor.set_defaults(func=cmd_doctor)

    p_demo = sub.add_parser(
        "demo",
        help="Bootstrap from examples/demo-brain without configuring BRAIN_ROOT",
        parents=[parent],
    )
    p_demo.add_argument(
        "domain",
        nargs="?",
        default="specialty-coffee",
        help="Demo domain (default: specialty-coffee)",
    )
    p_demo.add_argument("--max-tokens", type=int, default=4000)
    p_demo.set_defaults(func=cmd_demo)

    p_try = sub.add_parser(
        "try",
        help="Zero-setup demo: bootstrap + expand with human-readable output",
    )
    p_try.add_argument(
        "domain",
        nargs="?",
        default="specialty-coffee",
        help="Demo domain (default: specialty-coffee)",
    )
    p_try.add_argument(
        "--query",
        default="grind",
        help='Keyword for expand step (default: "grind")',
    )
    p_try.set_defaults(func=cmd_try)

    p_mcp = sub.add_parser(
        "setup-mcp",
        help="Print MCP server config JSON with absolute paths",
    )
    p_mcp.add_argument(
        "--brain-root",
        help="Brain directory for BRAIN_ROOT in MCP env (defaults to $BRAIN_ROOT or demo brain)",
    )
    p_mcp.add_argument(
        "--output",
        choices=("json", "text"),
        default="text",
        help="Output format",
    )
    p_mcp.set_defaults(func=cmd_setup_mcp)

    args = parser.parse_args()

    if not args.command:
        print(WELCOME.strip())
        raise SystemExit(0)

    brain_root = resolve_brain_root(getattr(args, "brain_root", None))

    if args.command == "init":
        cmd_init(args)
        return

    if args.command == "doctor":
        cmd_doctor(args)
        return

    if args.command == "demo":
        cmd_demo(args)
        return

    if args.command == "try":
        cmd_try(args)
        return

    if args.command == "setup-mcp":
        cmd_setup_mcp(args)
        return

    if args.command == "classify":
        ensure_brain_root(brain_root)
        extra = ["--domain", args.domain] + (["--summary"] if args.summary else [])
        _delegate_tool("classify", brain_root, extra)
        return

    if args.command == "crystallize":
        ensure_brain_root(brain_root)
        extra = ["--domain", args.domain]
        if args.local:
            extra.append("--local")
        if args.force:
            extra.append("--force")
        _delegate_tool("crystallize", brain_root, extra)
        return

    if args.command == "verify":
        ensure_brain_root(brain_root)
        _delegate_tool("verify", brain_root, ["--domain", args.domain])
        return

    if args.command == "freshness":
        ensure_brain_root(brain_root)
        extra = ["--domain", args.domain]
        if args.stale_only:
            extra.append("--stale-only")
        _delegate_tool("freshness-audit", brain_root, extra)
        return

    ensure_brain_root(brain_root)
    reader = BrainReader(brain_root)
    run_reader_command(reader, args)


if __name__ == "__main__":
    main()
