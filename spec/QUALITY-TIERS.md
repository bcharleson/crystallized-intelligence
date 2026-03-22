# Quality Tiers

Every document should carry provenance and trust metadata.

## Tiers

- Tier 0: first-party or original knowledge
- Tier 1: books, papers, official docs, specifications
- Tier 2: talks, workshops, whitepapers, technical reports
- Tier 3: tutorials, courses, blogs, case studies
- Tier 4: podcasts, interviews, videos, newsletters
- Tier 5: social content and forum posts

## Recommended Metadata

- `source.type`
- `source.author`
- `source.author_authority`
- `quality.source_tier`
- `quality.verification`
- `quality.confidence`
- `freshness.sensitivity`

## Rule Of Thumb

If a document would change how an agent behaves, its provenance should be
obvious from the frontmatter alone.
