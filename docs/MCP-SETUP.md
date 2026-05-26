# MCP Setup

Connect Cursor (or Claude Desktop) to your brain via the bundled MCP server.

## One-command config

From the framework repo root:

```bash
# Demo brain (default)
python tools/bin/brain.py setup-mcp

# Your brain
export BRAIN_ROOT=~/my-brain
python tools/bin/brain.py setup-mcp --output json
```

Copy the printed JSON into your MCP settings under `mcpServers`.

## Install dependency

```bash
pip install -r requirements-mcp.txt
```

## Manual configuration

See [mcp-config.example.json](mcp-config.example.json). Replace:

- `args[0]` → absolute path to `tools/bin/brain-mcp.py`
- `env.BRAIN_ROOT` → your brain directory (or `examples/demo-brain`)

Use the same Python interpreter you used for `pip install` as the `command` value.

## Verify

Restart Cursor, then ask the agent to call `brain_list_domains` or run locally:

```bash
export BRAIN_ROOT=examples/demo-brain
python tools/bin/brain-mcp.py  # stdio server — usually launched by the IDE
```

For CLI-only workflows you do not need MCP — use `brain bootstrap/expand/search/get` directly.

See also [AGENT-INTEGRATION.md](AGENT-INTEGRATION.md).
