# Crystallized Intelligence for Agents — Framework Specification

## 1. Vision

Crystallized Intelligence for Agents is a framework for building domain-mastery knowledge
bases, called **Brains**, for AI agents and humans.

The core idea is simple:

- a skill tells an agent **how** to perform a task
- a brain gives an agent **what it knows** about a domain

Most AI systems still treat knowledge as raw text to retrieve and reinterpret
on every query. This framework treats knowledge as something that can be
compiled into reusable layers of understanding.

## 2. Why Existing Approaches Fall Short

### Traditional RAG

RAG systems retrieve chunks and pass them into the model context at runtime.
That works, but it has predictable limits:

- retrieval is probabilistic
- chunks often lose context and hierarchy
- every query pays to re-interpret raw text
- trust and quality are rarely first-class
- the system does not know how much depth the task actually needs

### Knowledge Graphs

Knowledge graphs help with relationships, but they often struggle to preserve
explanatory depth:

- graphs can tell you that concepts are related
- they do not automatically provide the distilled understanding of why
- they are expensive to build and maintain well

### Full-Text Search

Full-text search is useful for lookup, but weak for mastery:

- it favors exact wording over conceptual relevance
- it returns documents, not pre-digested judgment
- it has no native sense of depth or trust

### Fine-Tuning

Fine-tuning can be powerful, but it is often too heavy for dynamic operational
knowledge:

- hard to update incrementally
- hard to inspect
- expensive relative to simpler context architectures

## 3. The Core Thesis

Instead of retrieving only raw knowledge at runtime, a Brain should expose
multiple **resolution layers** of the same domain.

That means the agent can start from a compressed representation of expertise and
expand only when needed.

This mirrors human learning:

- novices rely on full source material
- practitioners operate from principles and frameworks
- experts think from compressed heuristics and mental models

## 4. Multi-Resolution Model

The framework organizes knowledge into five layers:

```text
Layer 4: seed         domain DNA
Layer 3: principles   frameworks, heuristics, mistakes, decision trees
Layer 2: knowledge    curated guides, references, case studies
Layer 1: sources      transcripts, books, articles, raw evidence
Layer 0: raw          unprocessed scans, dumps, recordings
```

### Layer 4: Seed

The smallest possible useful representation of a domain.

Purpose:

- quick orientation
- low-token domain bootstrap
- cross-domain traversal

### Layer 3: Principles

A compressed operational model of the domain.

Purpose:

- everyday execution
- decision making
- framework loading before deeper reading

### Layer 2: Knowledge

Curated domain articles and reference material.

Purpose:

- deeper problem solving
- implementation detail
- validation against documented best practices

### Layer 1: Sources

Original source material and supporting evidence.

Purpose:

- provenance
- auditability
- deeper research

## 5. What Makes This Different

The framework is different from standard RAG in five ways:

1. **Pre-compiled understanding**
   Agents can load distilled expertise, not just raw evidence.
2. **Adaptive depth**
   The system can start at `seed` or `principles` and expand only as needed.
3. **Quality-weighted knowledge**
   Trust signals live with the content, not in a separate hidden layer.
4. **First-party prioritization**
   Original knowledge can be marked and weighted above generic external content.
5. **Git-native structure**
   Knowledge remains inspectable, portable, versioned, and auditable.

## 6. Quality And Provenance

Every document should carry provenance and quality metadata in frontmatter.

Important concepts:

- `source.type`
- `source.author`
- `source.author_authority`
- `quality.source_tier`
- `quality.verification`
- `quality.confidence`
- `freshness.sensitivity`

This allows a Brain to distinguish:

- original knowledge from external summaries
- authoritative material from low-signal content
- stable knowledge from fast-aging knowledge

## 7. Brain Structure

The canonical structure is:

```text
brain.yaml
corpus/
  {domain}/
    _domain.yaml
    _crystal/
      seed.md
      principles.md
      graph.yaml
      persona.md
    knowledge/
    sources/
    examples/
tools/
spec/
```

### `brain.yaml`

Defines:

- brain identity
- domain registry
- quality defaults
- crystallization settings

### `_domain.yaml`

Defines:

- domain description
- related domains
- crystal file locations
- reading order

## 8. Crystallization Pipeline

The `crystallize.py` tool reads a domain and produces:

- `seed.md`
- `principles.md`
- `graph.yaml`
- `persona.md`

It supports two modes:

- API-assisted generation
- local template generation

This makes the framework useful both with and without model APIs.

## 9. Agent Access Pattern

A typical agent bootstrap looks like this:

1. Read `brain.yaml`
2. Read `corpus/{domain}/_domain.yaml`
3. Read `corpus/{domain}/_crystal/seed.md`
4. Read `corpus/{domain}/_crystal/principles.md`
5. Expand to `knowledge/` or `sources/` only if the task demands it

This is the key behavioral difference from naive retrieval: the agent begins
from compressed expertise first, not from random chunks first.

## 10. Open Source Boundary

The framework is intended to be open source.

The **content** inside a private working brain does not need to be.

Recommended split:

- open source the framework, structure, schemas, and tooling
- keep proprietary domain content private
- keep compiled artifacts derived from proprietary knowledge private
- publish a sanitized demo brain for education and adoption

This enables both openness and defensibility.

## 11. Intended Outcomes

The framework is designed to produce:

- lower token usage for routine domain tasks
- better domain consistency across agents
- stronger provenance and inspectability
- reusable expert knowledge structures
- a cleaner separation between public framework and private moat

## 12. Positioning

The clearest short description is:

**A git-native framework for pre-compiling domain expertise into agent-readable knowledge layers.**

That is the central claim this repo should communicate.
