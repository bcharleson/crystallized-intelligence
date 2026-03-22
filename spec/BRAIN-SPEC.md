# Brain Spec

A brain is a domain-organized knowledge base for agents and humans.

## Design Principles

- markdown is the source of truth
- knowledge is organized by domain, not file type
- quality and provenance travel with the content
- compiled layers reduce repeated interpretation work for agents
- the core framework should remain tool-agnostic

## Domain Layout

```text
corpus/{domain}/
├── _domain.yaml
├── _crystal/
│   ├── seed.md
│   ├── principles.md
│   ├── graph.yaml
│   └── persona.md
├── knowledge/
├── sources/
└── examples/
```

## Intended Flow

1. Add knowledge and source material to a domain
2. Assign provenance and quality metadata
3. Generate or refine crystallized layers
4. Load the appropriate layer for the task
