---
title: "Runbook Basics — Principles"
content_type: knowledge
crystal_layer: 3
domain: runbook-basics
knowledge_type: fundamental
created: 2026-03-06
updated: 2026-03-06
quality:
  source_tier: 0
  verification: self_verified
  confidence: high
source:
  type: first_party
  author: "Crystallized Intelligence Demo"
  author_authority: owner
processing:
  status: processed
  pipeline: demo
---

# Runbook Basics — Principles

## Core Framework

Runbooks are decision support under time pressure. Structure: trigger → triage →
mitigate → verify → escalate → follow-up. Each phase has entry criteria and exit
criteria so operators know when to advance or stop.

## Key Rules

- Start with "when to use this" and "when NOT to use this."
- One action per step; link to deeper docs instead of nesting procedures.
- State blast radius and required permissions before destructive commands.
- Include verification after every mutating step.
- Name an owner and last-reviewed date in frontmatter.

## Common Mistakes

1. Writing architecture essays instead of executable steps.
2. Missing rollback paths for irreversible actions.
3. Assuming on-call knows tribal context from six months ago.
4. Never updating after drills or incidents.

## Decision Tree

- User impact unclear: triage checklist first, escalate if SLO burn is ambiguous.
- Known fix with low risk: run mitigation steps, verify metrics, document timeline.
- Unknown root cause: stabilize, preserve evidence, hand off to incident commander.
