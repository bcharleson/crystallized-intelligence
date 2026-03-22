# Crystallized Intelligence

**A git-native framework for pre-compiling domain expertise into agent-readable knowledge layers.**

Instead of dumping raw text into an LLM at runtime, Crystallized Intelligence gives your agents something better: pre-compiled understanding — organized into layers from dense compressed heuristics down to full source material. The agent loads only what the task needs.

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

A Skill says "write a cold email using the PVP framework." A Brain contains the complete understanding of what PVP is, why it works, when to use it vs. alternatives, what the failure modes are, and everything else that separates a generic output from an expert one.

---

## What Makes This Different

1. **Pre-compiled understanding** — Agents load distilled expertise, not just raw evidence
2. **Adaptive depth** — Start at `seed`, expand to `sources` only when the task demands it
3. **Quality-weighted knowledge** — Trust signals live in frontmatter alongside the content
4. **First-party prioritization** — Your original knowledge is marked and weighted above generic external content
5. **Git-native** — Everything is plain text, versioned, inspectable, portable, and auditable
6. **Zero dependencies for core tooling** — All scripts use Python stdlib only

---

## Quick Start

**Requirements:** Python 3.10+. No pip installs needed for core tools. An `ANTHROPIC_API_KEY` is optional — without it, the tool generates templates for manual editing.

```bash
# 1. Clone
git clone https://github.com/bcharleson/crystallized-intelligence
cd crystallized-intelligence

# 2. Try the demo brain (no API key needed)
python tools/bin/crystallize.py --brain-root examples/demo-brain --domain specialty-coffee --local
```

You will see the crystal layers generated for the `specialty-coffee` demo domain. Open `examples/demo-brain/corpus/specialty-coffee/_crystal/` to see `seed.md`, `principles.md`, `graph.yaml`, and `persona.md`.

---

## Build Your Own Brain

```bash
# 3. Initialize a new brain
python tools/bin/init-brain.py --path ~/my-brain --name "My Brain" --domains "my-domain"

# 4. Add knowledge
# Drop files into ~/my-brain/corpus/my-domain/knowledge/
# Add source material into ~/my-brain/corpus/my-domain/sources/
# Each file should have YAML frontmatter — see the schema below

# 5. Crystallize (local templates, no API)
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
  bin/
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

| Tier | Source Types | Weight |
|------|-------------|--------|
| 0 | first_party, original_framework, proprietary_insight, lived_experience | 1.0 |
| 1 | book, academic_paper, official_docs, specification | 1.0 |
| 2 | conference_talk, workshop, whitepaper, technical_report | 0.85 |
| 3 | tutorial, course, technical_blog, case_study | 0.70 |
| 4 | podcast, interview, youtube_video, newsletter | 0.55 |
| 5 | social_media, forum_post, tweet_thread, reddit_comment | 0.35 |

**Rule of thumb:** If a document would change how an agent behaves, its provenance should be obvious from the frontmatter alone.

---

## How Agents Use a Brain

The access pattern is the key behavioral difference from naive retrieval. The agent begins from compressed expertise, not from random chunks.

```
1. Read brain.yaml                              — understand the domain registry
2. Read corpus/{domain}/_domain.yaml            — understand what this domain covers
3. Read corpus/{domain}/_crystal/seed.md        — load domain DNA (~200 tokens)
4. Read corpus/{domain}/_crystal/principles.md  — load compressed framework (~2K tokens)
5. Expand to knowledge/ or sources/ only if the task demands deeper detail
```

For most routine tasks, steps 1–4 are sufficient. Steps 1–3 are sufficient for orientation and routing.

A working agent system prompt bootstrap looks like this:

```python
seed = open("corpus/my-domain/_crystal/seed.md").read()
principles = open("corpus/my-domain/_crystal/principles.md").read()

system_prompt = f"""
You are an expert in {domain}.

{seed}

{principles}

Expand to the knowledge/ directory only if the task requires implementation detail
beyond what the principles cover.
"""
```

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

Run `python tools/bin/freshness-audit.py --all` to surface stale documents before they mislead an agent.

---

## Tools Reference

| Tool | What it does |
|---|---|
| `init-brain.py` | Scaffold a new brain with correct directory structure |
| `crystallize.py` | Distill domain knowledge into seed, principles, persona, graph |
| `classify.py` | Auto-enrich document frontmatter with quality metadata |
| `freshness-audit.py` | Flag documents approaching or past their stale threshold |
| `verify.py` | Quality gate — checks frontmatter, deduplication, and safety (no PII/secrets) |
| `build-manifest.py` | Generate a `MANIFEST.md` index of all content in the brain |

---

## Why This Exists

Most AI knowledge systems are built for retrieval. This one is built for *mastery*.

The difference matters most when your agents need to operate with judgment, not just lookup. A retrieval system gives your agent the right paragraph from the right document. A Brain gives your agent the understanding to know which paragraphs matter and why — before it even looks at them.

This framework came out of building production AI agent systems for go-to-market operations. We needed agents that could carry deep domain expertise across hundreds of sessions without losing context, without re-interpreting the same raw material every time, and without trusting every source equally. Standard RAG wasn't enough. Fine-tuning was too heavy. This is what we built instead.

---

## Full Specification

See [SPEC.md](SPEC.md) for the complete framework specification, including the full multi-resolution model, crystallization pipeline details, agent access protocol, and design principles.

---

## License

MIT
