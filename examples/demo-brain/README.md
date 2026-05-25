# Demo Brain

Public-safe sample brain for the Crystallized Intelligence framework.

## Domains

| Domain | Purpose | Freshness |
|--------|---------|-----------|
| `specialty-coffee` | Minimal hello-world — layers, tiers, bootstrap | `low` |
| `b2b-discovery` | Comprehensive agent demo — qualification, tier conflict | `high` |

## What each domain teaches

**specialty-coffee** (6 files) — end-to-end pipeline in a neutral hobby domain.

**b2b-discovery** (11 files) — business-agent patterns:

- Tier **0** playbooks vs tier **3** blog vs tier **4** transcript (deliberate conflict)
- `_crystal/` with real distilled seed/principles/persona
- `examples/` checklists for operational workflows
- Fictional **Acme Analytics** ICP — no real companies or proprietary methods

## Quick start

```bash
export BRAIN_ROOT="$(pwd)"   # from examples/demo-brain/

# Minimal domain
python ../../tools/bin/brain.py bootstrap specialty-coffee

# Comprehensive domain
python ../../tools/bin/brain.py bootstrap b2b-discovery
python ../../tools/bin/brain.py expand b2b-discovery --query "disqualify" --max-tier 3
```

When tier-4 sources say "never disqualify," agents should prefer tier-0
`knowledge/frameworks/qualification-criteria.md`.

## Validate

```bash
python ../../tools/bin/verify.py --domain b2b-discovery --brain-root .
python ../../tools/bin/classify.py --domain b2b-discovery --summary --brain-root .
```
