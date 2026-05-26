---
title: "Incident Triage Checklist"
content_type: example
created: 2026-03-06
updated: 2026-03-06
domain: runbook-basics
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

# Incident Triage Checklist

1. Acknowledge the page and open the incident channel.
2. Confirm user impact (error rate, latency, support tickets).
3. Identify blast radius (one region vs global).
4. Check recent deploys and config changes in the last 2 hours.
5. Decide: mitigate now vs deep debug — default to mitigate when users are blocked.
6. Assign roles: incident commander, scribe, comms.
7. Set a 15-minute checkpoint to re-evaluate.
