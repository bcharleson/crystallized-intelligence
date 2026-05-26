# Crystallized Intelligence

**A git-native framework for pre-compiling domain expertise into agent-readable knowledge layers.**

Instead of dumping raw text into an LLM at runtime, Crystallized Intelligence gives your agents something better: pre-compiled understanding — organized into layers from dense compressed heuristics down to full source material. The agent loads only what the task needs.

## Status

**Beta — framework and demo brain are public and usable.** Core CLI tools (`brain`, `classify`, `crystallize`, `verify`, `freshness-audit`) run on **Python 3.9+** with no pip dependencies. The bundled `examples/demo-brain` works end-to-end without an API key.

| Area | State |
|------|--------|
| Layer-first retrieval (`brain bootstrap/expand/search/get`) | Stable |
| Heuristic crystallization (`crystallize --local`) | Usable — distills from your corpus; AI mode needs `ANTHROPIC_API_KEY` |
| MCP server | Manual setup — run `brain setup-mcp` for a ready-made config |
| Your private brain repo | You bring content; this repo ships the framework only |

**Roadmap:** richer MCP onboarding, more example domains, optional pip package for `brain` on PATH.

### This repo vs your brain

| | **This repo (framework)** | **Your brain repo** |
|---|---------------------------|---------------------|
| Contains | Tools, schemas, docs, demo content | Your `brain.yaml` + `corpus/` |
| Visibility | Public | Usually private |
| Clone once | Yes — fork or vendor the framework | One per team/product/domain |

Set `BRAIN_ROOT` to point tools at your brain directory (or use `--brain-root`). The framework never ships your proprietary content.

---

## The Problem

Most teams give AI agents knowledge in one of four ways, and all four have real limits:

| Approach | The limit |
|---|---|
| **RAG** | Retrieval is probabilistic. Chunks lose context and hierarchy. Every query re-interprets raw text. Trust is not first-class. |
| **Knowledge graphs** | Good for relationships, bad for explanatory depth. Expensive to build and maintain. |
| **Full-text search** | Favors exact wording over conceptual relevance. Returns documents, not judgment. |
| **Fine-tuning** | Powerful, but hard to update incrementally, hard to inspect, and expensive for operational knowledge. |

The gap in all of them: they treat knowledge as something to retrieve, not something to *understand in advance*.

---

## The Idea

A Brain has five resolution layers. The agent starts at the top and expands only when the task demands it.

```
Layer 4: seed         ~200 tokens    Domain DNA — core heuristics, compressed principles
Layer 3: principles   ~2,000 tokens  Frameworks, decision trees, common mistakes
Layer 2: knowledge    ~20,000 tokens Curated guides, references, case studies
Layer 1: sources      ~200K tokens   Transcripts, books, articles, raw evidence
Layer 0: raw          unlimited      Unprocessed source material
```

This mirrors how human expertise actually works:
- **Novices** rely on full source material
- **Practitioners** operate from principles and frameworks
- **Experts** think from compressed heuristics and mental models

A Brain gives your agents the expert layer first, with the full library behind it if needed.

---

## Skill vs. Brain

These are two different things and both matter:

- A **Skill** tells an agent *how* to do something
- A **Brain** tells an agent *what it knows* about a domain

A Skill says "run the pour-over checklist and format the output." A Brain contains the extraction theory, the trade-offs between grind and contact time, when to change one variable at a time, and everything else that separates a generic answer from an expert one.

**Do not bloat skills with domain knowledge.** Keep skills thin (procedure, tools, output shape). Put mastery in the Brain.

---

## What Makes This Different

1. **Pre-compiled understanding** — Agents load distilled expertise, not just raw evidence
2. **Adaptive depth** — Start at `seed`, expand to `sources` only when the task demands it
3. **Quality-weighted knowledge** — Trust signals live in frontmatter alongside the content ([source tiers](#source-quality-tiers), [agent trust rules](#2-trust-weighted-selection-source-of-truth))
4. **First-party prioritization** — Your original knowledge is marked and weighted above generic external content
5. **Git-native** — Everything is plain text, versioned, inspectable, portable, and auditable
6. **Zero dependencies for core tooling** — All scripts use Python stdlib only

---

## Quick Start

**Requirements:** **Python 3.9+** (stdlib-only core tools; tested on 3.9, 3.10, and 3.12 in CI). No pip installs needed for core tools. An `ANTHROPIC_API_KEY` is optional — without it, `crystallize --local` heuristically distills crystal layers from your knowledge files.

On macOS, the system `python3` may be older than 3.9 — use `python3.10` from Homebrew or [python.org](https://www.python.org/downloads/) if commands exit with a version error.

```bash
# 1. Clone
git clone https://github.com/bcharleson/crystallized-intelligence
cd crystallized-intelligence

# 2. Zero-config demo (no BRAIN_ROOT export needed)
python tools/bin/brain.py demo specialty-coffee

# 3. Full demo brain workflow
export BRAIN_ROOT=examples/demo-brain
python tools/bin/brain.py doctor
python tools/bin/brain.py bootstrap specialty-coffee
python tools/bin/brain.py expand specialty-coffee --query "grind" --max-tier 3
```

To build crystal layers without an API key, add knowledge under `corpus/{domain}/knowledge/` then run:

```bash
python tools/bin/crystallize.py --brain-root examples/demo-brain --domain specialty-coffee --local
```

Local mode extracts headings, bullets, and summaries from your articles — it does **not** overwrite an existing good `_crystal/` unless you pass `--force`. Inspect `examples/demo-brain/corpus/specialty-coffee/_crystal/` for the shipped demo crystals.

---

## Build Your Own Brain

```bash
# 3. Initialize a new brain
python tools/bin/brain.py init --path ~/my-brain --name "My Brain" --domains "my-domain"

# 4. Add knowledge
# Drop files into ~/my-brain/corpus/my-domain/knowledge/
# Add source material into ~/my-brain/corpus/my-domain/sources/
# Each file should have YAML frontmatter — see the schema below

# 5. Crystallize (local heuristic distillation, no API)
python tools/bin/crystallize.py --brain-root ~/my-brain --domain my-domain --local

# 5a. Crystallize with AI assistance (requires ANTHROPIC_API_KEY)
ANTHROPIC_API_KEY=sk-... python tools/bin/crystallize.py --brain-root ~/my-brain --domain my-domain
```

After crystallization, your brain has:
- `_crystal/seed.md` — the ~200-token domain DNA
- `_crystal/principles.md` — the ~2,000-token compressed framework
- `_crystal/persona.md` — a pre-compiled expert persona for agent system prompts
- `_crystal/graph.yaml` — concept relationships

---

## Directory Structure

```
brain.yaml                        Brain identity, domain registry, quality config
corpus/
  {domain}/
    _domain.yaml                  Domain description, reading order, related domains
    _crystal/
      seed.md                     Layer 4 — domain DNA (~200 tokens)
      principles.md               Layer 3 — frameworks and heuristics (~2K tokens)
      graph.yaml                  Concept relationship graph
      persona.md                  Pre-compiled expert persona
    knowledge/                    Layer 2 — curated articles and references
    sources/                      Layer 1 — transcripts, books, raw evidence
    examples/                     Worked examples for this domain
tools/
  lib/
    brain_reader.py             Layer-first retrieval (shared by CLI + MCP)
  bin/
    brain.py                    Unified CLI — bootstrap, expand, search, init
    brain-mcp.py                Local MCP server (optional: pip install -r requirements-mcp.txt)
    init-brain.py                 Scaffold a new brain
    crystallize.py                Run the crystallization pipeline
    classify.py                   Auto-classify documents with quality metadata
    freshness-audit.py            Flag stale documents by domain sensitivity
    verify.py                     Quality gates for CI (no secrets, valid frontmatter)
    build-manifest.py             Generate a MANIFEST.md index of all content
  schemas/
    frontmatter.schema.json       JSON schema for document metadata
spec/
  BRAIN-SPEC.md                   Brain structure specification
  CRYSTALLIZATION.md              Crystallization pipeline reference
  QUALITY-TIERS.md                Source tier definitions
examples/
  demo-brain/                     A fully sanitized sample brain (specialty coffee)
docs/
  AGENT-INTEGRATION.md            Fork, CLI, MCP setup for agents
  mcp-config.example.json         Cursor MCP configuration template
skills/
  use-crystallized-brain/SKILL.md   Agent skill — bootstrap/expand protocol
AGENTS.md                         Agent operating guide (start here)
requirements-mcp.txt              Optional dependency for brain-mcp.py
LICENSE                           MIT
```

---

## Document Frontmatter

Every knowledge file carries provenance and quality metadata. This is how the system knows what to trust.

```yaml
---
title: "Your Document Title"
content_type: knowledge          # knowledge | source | example | book
crystal_layer: 2                 # 0-4
domain: my-domain
knowledge_type: fundamental      # fundamental | tactical | reference | case_study
created: 2026-01-01
updated: 2026-01-01
quality:
  source_tier: 1                 # 0 (first-party) to 5 (social/forum)
  verification: self_verified    # self_verified | peer_reviewed | unverified
  confidence: high               # high | medium | low
source:
  type: first_party              # See quality tiers below
  author: "Your Name"
  author_authority: owner        # owner | creator | expert | unknown
freshness:
  sensitivity: medium            # high | medium | low
  valid_until: 2026-12-31
---

Your content here.
```

### Source Quality Tiers

Every document gets a **tier** (0 = highest trust, 5 = lowest). Tier comes from `source.type` and can be adjusted by `source.author_authority` and `brain.yaml` policy.

| Tier | `source.type` values | Default weight | What it represents |
|------|---------------------|----------------|--------------------|
| **0** | `first_party`, `original_framework`, `proprietary_insight`, `lived_experience` | 1.0 | **Your core knowledge** — playbooks, frameworks you built, lived experience |
| **1** | `book`, `academic_paper`, `official_docs`, `specification` | 1.0 | **Canonical external sources** — textbooks, papers, vendor docs |
| **2** | `conference_talk`, `workshop`, `whitepaper`, `technical_report` | 0.85 | Professional secondary sources |
| **3** | `tutorial`, `course`, `technical_blog`, `case_study` | 0.70 | Curated how-to and practitioner writeups |
| **4** | `podcast`, `interview`, `youtube_video`, `newsletter` | 0.55 | **YouTube channels, podcasts, newsletters** — useful, but verify |
| **5** | `social_media`, `forum_post`, `tweet_thread`, `reddit_comment` | 0.35 | Low-signal social and forum content |

**Authority boost:** If `source.author_authority` is `owner` or `creator` (typically you), treat the document as **one tier higher** (minimum tier 0). Your own notes from a YouTube workflow still belong in tier 0 if they are `first_party` + `owner`.

**Rule of thumb:** If a document would change how an agent behaves, its provenance must be obvious from the frontmatter alone — not inferred from the prose.

See [spec/QUALITY-TIERS.md](spec/QUALITY-TIERS.md) for the full reference.

---

## Source Ranking in Practice

The framework separates **where knowledge came from** from **how deep the agent reads**. Both matter.

### Map your inputs to frontmatter

| You have… | Put it in… | Set `source.type` | Typical tier |
|-----------|------------|-------------------|--------------|
| Your operating playbook | `knowledge/` or `examples/` | `first_party` | 0 |
| Framework you invented | `knowledge/` | `original_framework` | 0 |
| Book chapter / PDF notes | `sources/` or `knowledge/` | `book` | 1 |
| Official product docs | `sources/` | `official_docs` | 1 |
| YouTube transcript | `sources/transcripts/` | `youtube_video` | 4 |
| Blog post you saved | `sources/` | `technical_blog` | 3 |
| Twitter / Reddit thread | `sources/` | `social_media` / `forum_post` | 5 |

The demo brain includes two domains in `examples/demo-brain/`:

| Domain | Files | Teaches |
|--------|-------|---------|
| `specialty-coffee` | ~6 | Minimal hello-world — tiers and layers in a neutral domain |
| `b2b-discovery` | ~11 | Full agent demo — ICP, qualification, **tier conflict** (synthetic Acme Analytics) |

**specialty-coffee** tier spread:

- `examples/brew-checklist.md` — tier **0** (`first_party`, `author_authority: owner`)
- `knowledge/fundamentals/dialing-in-basics.md` — tier **3** (`tutorial`)
- `sources/transcripts/2026-03-06-public-coffee-demo.md` — tier **4** (`youtube_video`)

**b2b-discovery** tier conflict (agents should prefer tier 0):

- `knowledge/frameworks/qualification-criteria.md` — tier **0** (disqualify when BANT weak)
- `sources/articles/outbound-persistence-blog.md` — tier **3** (never stop sequences)
- `sources/transcripts/synthetic-coaching-call.md` — tier **4** ("never disqualify" — wrong on purpose)

### Brain-level trust policy (`brain.yaml`)

Each brain declares default weights and overrides. Agents and maintainers should read this before trusting content.

```yaml
quality:
  source_weights:
    first_party: 1.0
    book: 1.0
    youtube_video: 0.55
    social_media: 0.35
  override_rules:
    - if: { author_authority: "owner" }
      weight_boost: 0.25
    - if: { source_type: "first_party" }
      weight_boost: 0.25
  require_provenance: true   # flag docs missing source metadata
```

When two documents disagree, **lower tier number wins** (0 beats 4). If tiers tie, prefer higher `quality.verification` and `quality.confidence`, then newer `updated` dates (after checking freshness).

### Audit tiers before you crystallize

```bash
# Preview suggested tiers for every file in a domain (no writes)
python tools/bin/classify.py --domain specialty-coffee --summary \
  --brain-root examples/demo-brain

# Classify a single new file
python tools/bin/classify.py my-brain/corpus/my-domain/knowledge/new-article.md
```

`classify.py` maps `source.type` → tier using the table above and applies the owner/creator boost. Use it while building the brain to catch missing or wrong provenance **before** crystallization.

---

## How Agents Use a Brain

Agents must follow two protocols: **layer-first loading** (how deep to read) and **trust-weighted selection** (which sources to believe).

### 1. Layer-first loading (resolution)

Start at the smallest useful layer. Expand only when the task needs more detail.

```
1. Read brain.yaml                              — domain registry + quality policy
2. Read corpus/{domain}/_domain.yaml            — scope, reading order, freshness
3. Read corpus/{domain}/_crystal/seed.md        — domain DNA (~200 tokens)
4. Read corpus/{domain}/_crystal/principles.md  — compressed framework (~2K tokens)
5. Expand to knowledge/ only if implementation detail is still missing
6. Expand to sources/ only for provenance, quotes, or resolving a conflict
7. Never start at sources/ or raw/ for routine tasks
```

For most tasks, steps 1–4 are enough. Steps 1–3 are enough for orientation and routing.

### 2. Trust-weighted selection (source of truth)

When reading `knowledge/` or `sources/`, agents **must**:

1. **Read frontmatter before body text** — use `quality.source_tier`, `source.type`, and `source.author_authority`
2. **Prefer lower tiers** — tier 0 (your knowledge) overrides tier 4 (YouTube) on conflict
3. **Respect verification** — `canonical` / `expert_verified` > `self_verified` > `unverified`
4. **Check freshness** — honor `freshness.valid_until` and domain `freshness_sensitivity`; deprioritize stale tier-4 sources
5. **Cite provenance** — when an answer depends on a specific doc, name the file and tier

When crystallizing or summarizing a domain, **weight higher-trust material more heavily** when building `_crystal/seed.md` and `_crystal/principles.md`. The crystal layers should reflect *your* source of truth, not the noisiest transcript.

### 3. Copy-paste agent instructions

Add this block to your agent config (`AGENTS.md`, `CLAUDE.md`, Cursor rules, or system prompt):

```markdown
## Brain access protocol

When this project includes a Crystallized Intelligence brain:

1. Load `brain.yaml`, then `corpus/{domain}/_domain.yaml`.
2. Always read `_crystal/seed.md` and `_crystal/principles.md` before deeper files.
3. Expand to `knowledge/` only when principles are insufficient.
4. Expand to `sources/` only for evidence, quotes, or conflict resolution.
5. Trust order: lower `quality.source_tier` wins (0 = first-party highest).
6. On conflict: tier → verification → confidence → recency (if fresh).
7. Never treat tier 4–5 sources as canonical without corroboration from tier 0–2.
8. When adding or editing brain content, set YAML frontmatter with `source.type`,
   `quality.source_tier`, and `source.author_authority`. Run classify.py to verify.
```

### 4. Programmatic bootstrap (system prompt)

```python
seed = open("corpus/my-domain/_crystal/seed.md").read()
principles = open("corpus/my-domain/_crystal/principles.md").read()

system_prompt = f"""
You are an expert in {domain}. This brain is your source of truth.

{seed}

{principles}

Rules:
- Prefer crystal layers over raw sources.
- When expanding, rank documents by quality.source_tier (lower = more trusted).
- first_party / owner content overrides youtube_video and social sources on conflict.
- State which brain files you relied on when the answer depends on specific knowledge.
"""
```

---

## Working on a Brain (maintainer workflow)

Use this loop when building or extending a brain — human or agent:

```bash
BRAIN=~/my-brain
DOMAIN=my-domain
export BRAIN_ROOT="$BRAIN"

# 1. Scaffold (once)
python tools/bin/brain.py init --path "$BRAIN" --name "My Brain" --domains "$DOMAIN"

# 2. Add content with frontmatter (knowledge/, sources/, examples/)
#    Tag source.type, tier, and author_authority on every file that matters.

# 3. Audit classification
python tools/bin/brain.py classify --domain "$DOMAIN" --summary

# 4. Crystallize distilled layers
python tools/bin/brain.py crystallize --domain "$DOMAIN" --local

# 5. Quality gates
python tools/bin/brain.py freshness --domain "$DOMAIN"
python tools/bin/brain.py verify --domain "$DOMAIN"
```

**Agent maintainers:** when ingesting a YouTube transcript, book summary, or internal doc, always write frontmatter first, run `brain classify` (or `classify.py`) to validate the tier, then place the file in the correct directory (`sources/` for raw captures, `knowledge/` for curated writeups).

---

## CLI & MCP for Agents

Forkers can initialize a brain and give agents **layer-first retrieval** without burning context on the full corpus.

| Surface | Best for |
|---------|----------|
| **`brain` CLI** | Scripts, CI, shell agents, JSON pipelines |
| **MCP server** | Cursor, Claude Desktop, any MCP client |

```bash
# Initialize (once)
python tools/bin/brain.py init --path ~/acme-brain --name "Acme" --domains "ops"

# Point all tools at your brain
export BRAIN_ROOT=~/acme-brain

# Low-token bootstrap (~200-2K tokens) — agents call this FIRST
python tools/bin/brain.py bootstrap ops

# Expand only when needed (tier-ranked, token budget)
python tools/bin/brain.py expand ops --query "deploy" --max-tokens 4000 --max-tier 3

# Search / single-doc fetch
python tools/bin/brain.py search ops "rollback"
python tools/bin/brain.py get ops knowledge/runbooks/deploy.md
```

**MCP (optional):** `pip install -r requirements-mcp.txt`, set `BRAIN_ROOT`, run `python tools/bin/brain-mcp.py`. Tools: `brain_bootstrap`, `brain_expand`, `brain_search`, `brain_get_document`, `brain_list_domains`.

Full setup: [docs/AGENT-INTEGRATION.md](docs/AGENT-INTEGRATION.md) · Cursor config: [docs/mcp-config.example.json](docs/mcp-config.example.json) · Agent skill: [skills/use-crystallized-brain/SKILL.md](skills/use-crystallized-brain/SKILL.md) · [AGENTS.md](AGENTS.md)

**Token discipline:** bootstrap → expand → get. Never load all of `sources/` into context. Lower `source_tier` wins on conflict.

---

## The Open Source Boundary

This framework is open source. The *content* inside your Brain does not need to be.

Recommended split:

- **Open source:** this framework, the tools, the schemas, the demo brain
- **Private:** your domain knowledge, your crystallized artifacts, your proprietary insights

This design enables both openness and defensibility. The framework is the gift. The knowledge is your moat.

---

## Domain Freshness

Not all knowledge ages at the same rate. Configure `freshness_sensitivity` in each domain's `_domain.yaml`:

```yaml
freshness_sensitivity: high    # 90 days — fast-moving domains (AI tooling, APIs)
freshness_sensitivity: medium  # 180 days — moderate velocity (default)
freshness_sensitivity: low     # 365 days — stable, evergreen domains
```

Run `python tools/bin/brain.py freshness --domain my-domain --brain-root ~/my-brain` to surface stale documents before they mislead an agent.

---

## Tools Reference

All corpus tools accept `--brain-root` pointing at a brain directory (the folder that contains `brain.yaml` and `corpus/`). Default is this framework repository root.

| Tool | What it does |
|---|---|
| **`brain.py`** | **Primary entrypoint** — retrieval (`bootstrap`, `expand`, `search`, `get`, `domains`) plus `init`, `classify`, `crystallize`, `verify`, `freshness` |
| `crystallize.py` | Distill domain knowledge into seed, principles, persona, graph (also via `brain crystallize`) |
| `classify.py` | Preview suggested tiers and metadata from `source.type` and path heuristics |
| `freshness-audit.py` | Flag documents approaching or past their stale threshold (also via `brain freshness`) |
| `verify.py` | Quality gate — checks frontmatter, deduplication, and safety (no PII/secrets) |
| `init-brain.py` | Scaffold a new brain (also via `brain init`) |
| `build-manifest.py` | Generate a `MANIFEST.md` index of all content in the brain |
| `brain-mcp.py` | **Local MCP server** — same retrieval for Cursor / Claude Desktop |

Example against the demo brain:

```bash
export BRAIN_ROOT=examples/demo-brain

# Minimal domain
python tools/bin/brain.py bootstrap specialty-coffee
python tools/bin/brain.py expand specialty-coffee --query "grind" --max-tier 3

# Comprehensive domain (sales fundamentals, tier conflict)
python tools/bin/brain.py bootstrap b2b-discovery
python tools/bin/brain.py expand b2b-discovery --query "disqualify" --max-tier 3

python tools/bin/verify.py --domain b2b-discovery
python tools/bin/classify.py --domain b2b-discovery --summary
```

---

## Why This Exists

Most AI knowledge systems are built for retrieval. This one is built for *mastery*.

The difference matters most when your agents need to operate with judgment, not just lookup. A retrieval system gives your agent the right paragraph from the right document. A Brain gives your agent the understanding to know which paragraphs matter and why — before it even looks at them.

This framework came out of building production AI agent systems that need durable domain judgment, not one-off lookups. We needed agents that could carry deep expertise across hundreds of sessions without losing context, without re-interpreting the same raw material every time, and without trusting every source equally. Standard RAG wasn't enough. Fine-tuning was too heavy. This is what we built instead.

---

## Full Specification

See [SPEC.md](SPEC.md) for the complete framework specification, including the full multi-resolution model, crystallization pipeline details, agent access protocol, and design principles.

---

## License

MIT — see [LICENSE](LICENSE).
