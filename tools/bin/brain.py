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

from lib.brain_reader import BrainReader  # noqa: E402
from lib.runtime import require_python  # noqa: E402

require_python()

BIN_DIR = Path(__file__).resolve().parent
DEFAULT_BRAIN_ROOT = Path(__file__).resolve().parent.parent.parent


def resolve_brain_root(explicit: Optional[str]) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("BRAIN_ROOT", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return DEFAULT_BRAIN_ROOT


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
                "  Or:  python tools/bin/brain.py bootstrap specialty-coffee --brain-root examples/demo-brain",
            ]
        )
    else:
        lines.append("  Set BRAIN_ROOT or pass --brain-root to your brain directory.")
    print("\n".join(lines), file=sys.stderr)
    raise SystemExit(1)


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
        description="Crystallized Intelligence brain CLI (layer-first agent access)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

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

    p_verify = sub.add_parser("verify", help="Run verify.py on a domain", parents=[parent])
    p_verify.add_argument("--domain", required=True)

    p_fresh = sub.add_parser(
        "freshness", help="Run freshness-audit.py on a domain", parents=[parent]
    )
    p_fresh.add_argument("--domain", required=True)
    p_fresh.add_argument("--stale-only", action="store_true")

    args = parser.parse_args()
    brain_root = resolve_brain_root(args.brain_root)

    if args.command == "init":
        cmd_init(args)
        return

    if args.command == "classify":
        ensure_brain_root(brain_root)
        extra = ["--domain", args.domain] + (["--summary"] if args.summary else [])
        _delegate_tool("classify", brain_root, extra)
        return

    if args.command == "crystallize":
        ensure_brain_root(brain_root)
        extra = ["--domain", args.domain] + (["--local"] if args.local else [])
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
    args.func(reader, args)


if __name__ == "__main__":
    main()
