# Contributing

Thanks for improving Crystallized Intelligence. This repo is the **public framework** — keep domain-specific content in your own brain repo or in `examples/demo-brain/` (public-safe demos only).

## Development setup

```bash
git clone https://github.com/bcharleson/crystallized-intelligence
cd crystallized-intelligence
python3 tools/bin/brain.py try                    # smoke test, no config
export BRAIN_ROOT=examples/demo-brain
python3 tools/bin/brain.py doctor
```

**Requirements:** Python 3.9+. Core tools use stdlib only. MCP server needs `pip install -r requirements-mcp.txt`.

## Project layout

| Path | Purpose |
|------|---------|
| `tools/bin/` | CLI entrypoints (`brain.py`, `crystallize.py`, `classify.py`, …) |
| `tools/lib/` | Shared library code (`brain_reader.py`, `runtime.py`) |
| `examples/demo-brain/` | Public demo corpus (three domains) |
| `docs/` | Agent integration, MCP setup, assets |

## Making changes

1. **Framework code** — match existing style; no hardcoded client/domain names in tools (use config from `brain.yaml` / `_domain.yaml`).
2. **Breaking CLI or schema changes** — note migration impact in the PR; downstream brain repos may depend on stable flags.
3. **Demo content** — fictional companies only; no proprietary TOFU or client references.
4. **Tests** — CI runs `verify`, `classify`, and `brain bootstrap/expand/search/get/doctor` on each demo domain for Python 3.9, 3.10, and 3.12.

Run locally before opening a PR:

```bash
export BRAIN_ROOT=examples/demo-brain
for d in specialty-coffee b2b-discovery runbook-basics; do
  python3 tools/bin/verify.py --domain "$d" --brain-root examples/demo-brain
  python3 tools/bin/brain.py bootstrap "$d" --brain-root examples/demo-brain
done
python3 tools/bin/brain.py try
```

## Pull requests

- One focused change per PR when possible.
- Update README / `docs/` if behavior or onboarding changes.
- Do not commit secrets or real customer content.

## Questions

Open a GitHub issue for bugs, docs gaps, or design discussion. For the broader TOFU autoresearch initiative context, this repo intentionally stays generic and public.
