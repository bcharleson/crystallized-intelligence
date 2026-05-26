---
title: "Runbook Anatomy"
content_type: knowledge
created: 2026-03-06
updated: 2026-03-06
domain: runbook-basics
knowledge_type: framework
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

# Runbook Anatomy

## Recommended sections

1. **Summary** — one paragraph, service owner, severity guidance.
2. **Triggers** — alerts, customer reports, dashboard links.
3. **Prerequisites** — access, tools, feature flags.
4. **Triage** — confirm impact; collect logs/metrics.
5. **Mitigation** — numbered steps with verification.
6. **Rollback** — how to undo each mutating step.
7. **Escalation** — who, when, and what to include in the handoff.
8. **Follow-up** — post-incident doc and runbook update checklist.

## Anti-patterns

- Steps that say "investigate" without defining done.
- Copy-pasted shell commands with environment-specific hostnames.
- Missing last-reviewed metadata.
