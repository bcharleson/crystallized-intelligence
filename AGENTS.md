# Agent Guide — Crystallized Intelligence for Agents

Open-source **framework** for pre-compiling domain expertise into agent-readable layers. This repo ships tooling and a demo brain; your proprietary content lives in a separate brain repo.

## Repo roles

| Artifact | Location | Purpose |
|----------|----------|---------|
| Framework | This repo (`tools/`, `spec/`, schemas) | classify, crystallize, verify, retrieve |
| Brain | Your fork's brain dir or sibling repo | `brain.yaml` + `corpus/{domain}/` |
| Skill | [skills/use-crystallized-brain/SKILL.md](skills/use-crystallized-brain/SKILL.md) | How agents retrieve without token burn |

## Quick start for agents

```bash
export BRAIN_ROOT=examples/demo-brain   # replace with your brain path
python tools/bin/brain.py bootstrap specialty-coffee
```

Prefer **MCP** when configured: tools `brain_bootstrap`, `brain_expand`, `brain_search`, `brain_get_document`. See [docs/AGENT-INTEGRATION.md](docs/AGENT-INTEGRATION.md).

## Operating rules

1. **Layer-first** — bootstrap (`seed` + `principles`) before reading `knowledge/` or `sources/`
2. **Trust-weighted** — lower `source_tier` wins on conflict (0 = first-party)
3. **Budgeted expand** — use `--max-tokens` and `--max-tier 3` by default
4. **No corpus dumps** — never load all of `sources/` into context
5. **Framework only here** — no hardcoded company domains or client content in this repo

Copy [skills/use-crystallized-brain/SKILL.md](skills/use-crystallized-brain/SKILL.md) into `.cursor/skills/` (or your agent's skill path) when working against a real brain.

## Fork → initialize → use

```bash
# Initialize a new brain (separate directory)
python tools/bin/brain.py init --path ~/my-brain --name "My Brain" --domains "ops"

export BRAIN_ROOT=~/my-brain
# Add corpus files with frontmatter → crystallize → verify
python tools/bin/brain.py crystallize --domain ops --local
python tools/bin/brain.py verify --domain ops
```

## Tools reference

| Command | Agent use? | Notes |
|---------|------------|-------|
| `brain bootstrap` | Yes | Always first |
| `brain expand` | Yes | Query + token budget |
| `brain search` | Yes | Paths + snippets |
| `brain get` | Yes | Single document |
| `brain domains` | Yes | Discovery |
| `classify` | Maintainer | Validate tiers |
| `crystallize` | Maintainer | Rebuild `_crystal/` |
| `verify` | Maintainer | Schema + structure |
| `freshness-audit` | Maintainer | Staleness report |

## Environment

| Variable | Meaning |
|----------|---------|
| `BRAIN_ROOT` | Directory containing `brain.yaml` (required for CLI/MCP) |

All corpus tools accept `--brain-root` when `BRAIN_ROOT` is unset.

## Further reading

- [README.md](README.md) — source ranking, crystallization, human docs
- [docs/AGENT-INTEGRATION.md](docs/AGENT-INTEGRATION.md) — MCP setup, JSON shapes
- [SPEC.md](SPEC.md) — full framework specification
