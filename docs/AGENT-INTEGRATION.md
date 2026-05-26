# Agent Integration

How to fork the framework, initialize a company brain, and give agents **low-token access** via CLI or MCP.

## Mental model

| Piece | Role |
|-------|------|
| **This repo** | Framework + tools + demo brain |
| **Your brain repo** | `brain.yaml` + `corpus/` (private or public) |
| **`brain` CLI** | Scriptable layer-first retrieval (JSON) |
| **MCP server** | Same retrieval as Cursor/Claude Desktop tools |

Agents should **bootstrap** (`seed` + `principles`) first, then **expand** only when needed. Never dump all of `sources/` into context by default.

## Fork workflow

```bash
# 1. Fork / clone the framework
git clone https://github.com/bcharleson/crystallized-intelligence
cd crystallized-intelligence

# 2. Initialize your brain (separate directory or sibling repo)
python tools/bin/brain.py init \
  --path ~/acme-brain \
  --name "Acme Brain" \
  --domains "product,engineering"

# 3. Add content under ~/acme-brain/corpus/{domain}/knowledge|sources|examples
#    Tag every file with source.type and quality.source_tier (see README)

# 4. Crystallize + verify + freshness
export BRAIN_ROOT=~/acme-brain
python tools/bin/brain.py crystallize --domain product --local
python tools/bin/brain.py verify --domain product
python tools/bin/brain.py freshness --domain product
```

Point `BRAIN_ROOT` at your brain forever after — typically a separate directory or sibling repo from this framework clone.

## CLI (`brain`)

Set once:

```bash
export BRAIN_ROOT=~/acme-brain
# or: export BRAIN_ROOT=/path/to/crystallized-intelligence/examples/demo-brain
```

Commands:

```bash
# List domains
python tools/bin/brain.py domains

# ~200-2K tokens — always start here
python tools/bin/brain.py bootstrap specialty-coffee
python tools/bin/brain.py bootstrap b2b-discovery   # richer sales demo

# Expand with budget + trust filter (tier 0 beats tier 4)
python tools/bin/brain.py expand b2b-discovery --query "qualify" --max-tokens 4000 --max-tier 3

# Search without loading full bodies
python tools/bin/brain.py search specialty-coffee "extraction"

# Single document
python tools/bin/brain.py get specialty-coffee knowledge/fundamentals/dialing-in-basics.md
```

All retrieval commands output **JSON** with `tokens_approx` so agents can budget context.

Optional: symlink or add `tools/bin` to `PATH` and alias `brain=brain.py`.

## MCP server (local)

Install once:

```bash
pip install -r requirements-mcp.txt
```

Run:

```bash
export BRAIN_ROOT=~/acme-brain
python tools/bin/brain-mcp.py
```

### Tools exposed

| Tool | Purpose |
|------|---------|
| `brain_list_domains` | Domain registry |
| `brain_bootstrap` | seed + principles (+ optional persona) |
| `brain_expand` | Tier-ranked, token-budgeted knowledge/sources |
| `brain_search` | Snippets + paths |
| `brain_get_document` | One file by path |

### Cursor configuration

Run from the framework repo:

```bash
python tools/bin/brain.py setup-mcp
```

Or copy [mcp-config.example.json](mcp-config.example.json) into your Cursor MCP settings. Set absolute paths for:

- `args[0]` → `brain-mcp.py` in your framework clone
- `env.BRAIN_ROOT` → your brain directory

Full walkthrough: [MCP-SETUP.md](MCP-SETUP.md).

Install the retrieval skill: copy [skills/use-crystallized-brain/SKILL.md](../skills/use-crystallized-brain/SKILL.md) into your agent's skill directory (e.g. `.cursor/skills/use-crystallized-brain/`). See also [AGENTS.md](../AGENTS.md).

## Agent skill / rules snippet

Add to `AGENTS.md` or project rules:

```markdown
## Brain (Crystallized Intelligence)

When BRAIN_ROOT is configured or MCP server `crystallized-intelligence` is available:

1. Call `brain_bootstrap(domain)` or `brain bootstrap {domain}` before any deep read.
2. Only call `brain_expand` / `brain_get_document` if bootstrap is insufficient.
3. Prefer lower `tier` documents on conflict (0 = first-party).
4. Use `max_tier=3` unless you explicitly need transcripts or social sources.
5. Never read entire `sources/` trees into context.
```

## Token budget guide

| Operation | Typical tokens |
|-----------|----------------|
| `bootstrap` | 200 – 2,500 |
| `expand --max-tokens 4000` | ≤ 4,000 |
| `search` | snippets only |
| `get` one knowledge file | varies |

Compare to naive RAG: loading 50 source files can be 100K+ tokens. Bootstrap-first keeps routine tasks in the low thousands.
