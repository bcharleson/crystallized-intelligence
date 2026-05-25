---
name: use-crystallized-brain
description: >-
  Layer-first retrieval from a Crystallized Intelligence brain via CLI or MCP.
  Use when BRAIN_ROOT is set, brain MCP tools are available, or the user asks
  to query/bootstrap/expand a domain brain without loading the full corpus.
---

# Use Crystallized Brain

Procedure for agents. The brain holds mastery; this skill holds **how to retrieve it cheaply**.

## When to use

- User or project has `BRAIN_ROOT` pointing at a brain (`brain.yaml` + `corpus/`)
- MCP server exposes `brain_bootstrap`, `brain_expand`, `brain_search`, `brain_get_document`
- Domain question needs curated knowledge, not a repo-wide file dump

## Setup (once per machine)

```bash
export BRAIN_ROOT=/path/to/your-brain   # or examples/demo-brain in this repo
```

MCP: see [docs/AGENT-INTEGRATION.md](../../docs/AGENT-INTEGRATION.md) and [docs/mcp-config.example.json](../../docs/mcp-config.example.json).

## Retrieval protocol (always follow)

1. **Bootstrap first** — `brain bootstrap <domain>` or `brain_bootstrap(domain)`
   - Loads `_crystal/seed.md` + `principles.md` (~200–2.5K tokens)
   - Enough for orientation and most routine answers

2. **Expand only if needed** — `brain expand <domain> --query "..." --max-tokens 4000 --max-tier 3`
   - Tier-ranked: lower `source_tier` wins (0 = first-party)
   - Default `max_tier=3` unless user explicitly wants transcripts/social (4–5)

3. **Search for paths** — `brain search <domain> "keyword"` when you need filenames, not full bodies

4. **Get one file** — `brain get <domain> <relative-path>` for a single document

5. **Never** read entire `sources/` trees or bulk-load `corpus/` into context

## Conflict resolution

When documents disagree:

1. Lower `quality.source_tier` (from frontmatter) wins
2. Higher `quality.verification` wins (`canonical` > `expert_verified` > …)
3. Higher `quality.confidence` wins
4. Prefer `_crystal/` over `knowledge/` over `sources/` for operational answers

## CLI examples

```bash
python tools/bin/brain.py domains
python tools/bin/brain.py bootstrap specialty-coffee
python tools/bin/brain.py bootstrap b2b-discovery
python tools/bin/brain.py expand b2b-discovery --query "disqualify" --max-tokens 4000 --max-tier 3
python tools/bin/brain.py search b2b-discovery "qualification"
```

All retrieval commands emit JSON with `tokens_approx` — stay within budget.

## MCP tool mapping

| Step | MCP tool |
|------|----------|
| List domains | `brain_list_domains` |
| Bootstrap | `brain_bootstrap` |
| Expand | `brain_expand` |
| Search | `brain_search` |
| Single doc | `brain_get_document` |

## Maintainer vs consumer

| Role | Action |
|------|--------|
| **Consumer agent** | Bootstrap → expand → get only |
| **Maintainer** | Edit corpus, run `classify`, `crystallize`, `verify` (see README) |

Do not crystallize or rewrite corpus unless the user is maintaining the brain.

## Token budget

| Operation | Typical tokens |
|-----------|----------------|
| bootstrap | 200 – 2,500 |
| expand (max 4000) | ≤ 4,000 |
| search | snippets only |
| get | one file |

If bootstrap + one expand is insufficient, ask the user to narrow the question or add curated `knowledge/` — do not escalate to full-corpus reads.
