#!/usr/bin/env python3
"""
Local MCP server for Crystallized Intelligence for Agents brains.

Exposes layer-first retrieval tools so agents can bootstrap cheaply and expand
on demand without loading the full corpus into context.

Requires: pip install mcp

Environment:
  BRAIN_ROOT  — path to brain directory (brain.yaml + corpus/)

Cursor / Claude Desktop config example: docs/mcp-config.example.json

Run:
  BRAIN_ROOT=~/my-brain python tools/bin/brain-mcp.py
  BRAIN_ROOT=examples/demo-brain python tools/bin/brain-mcp.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS_ROOT))

from lib.brain_reader import BrainReader  # noqa: E402
from lib.runtime import require_python  # noqa: E402

require_python()

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print(
        "Error: MCP Python SDK not installed.\n"
        "  pip install -r requirements-mcp.txt\n"
        "Then run this server again.",
        file=sys.stderr,
    )
    raise SystemExit(1)


def _reader() -> BrainReader:
    root = os.environ.get("BRAIN_ROOT", "").strip()
    if not root:
        raise ValueError(
            "Set BRAIN_ROOT to your brain directory (contains brain.yaml and corpus/)."
        )
    return BrainReader(Path(root))


mcp = FastMCP(
    "crystallized-intelligence",
    instructions=(
        "Crystallized Intelligence for Agents brain access. Always call brain_bootstrap first "
        "(~200-2K tokens). Call brain_expand or brain_get only when you need more detail. "
        "Lower source tier = higher trust (0 = first-party)."
    ),
)


@mcp.tool()
def brain_list_domains() -> str:
    """List domains registered in the brain (from corpus/ directories)."""
    return json.dumps(_reader().list_domains(), indent=2)


@mcp.tool()
def brain_bootstrap(
    domain: str,
    include_persona: bool = False,
    max_tokens: int = 4000,
) -> str:
    """
    Load pre-compiled crystal layers for a domain (seed + principles).
    Use this FIRST — typically ~200-2,000 tokens total. Avoid loading sources until needed.
    """
    return json.dumps(
        _reader().bootstrap(domain, include_persona=include_persona, max_tokens=max_tokens),
        indent=2,
    )


@mcp.tool()
def brain_expand(
    domain: str,
    layer: str = "knowledge",
    query: str = "",
    max_tokens: int = 8000,
    max_tier: int = 5,
    max_documents: int = 8,
) -> str:
    """
    Expand into knowledge/, examples/, or sources/ with trust-weighted ranking and a token budget.
    layer: knowledge | sources | all
    max_tier: skip documents above this tier (use 2-3 to exclude YouTube/social unless needed)
    """
    return json.dumps(
        _reader().expand(
            domain,
            layer=layer,
            query=query or None,
            max_tokens=max_tokens,
            max_tier=max_tier,
            max_documents=max_documents,
        ),
        indent=2,
    )


@mcp.tool()
def brain_search(
    domain: str,
    query: str,
    max_results: int = 5,
    max_tier: int = 5,
) -> str:
    """Search the brain by keyword. Returns snippets and paths — use brain_get for full text."""
    return json.dumps(
        _reader().search(domain, query, max_results=max_results, max_tier=max_tier),
        indent=2,
    )


@mcp.tool()
def brain_get_document(domain: str, path: str) -> str:
    """Fetch one document by corpus-relative path (e.g. knowledge/foo.md)."""
    return json.dumps(_reader().get_document(domain, path), indent=2)


if __name__ == "__main__":
    mcp.run()
