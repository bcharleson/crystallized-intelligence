"""
Layer-first, trust-weighted brain access for CLI and MCP.

Returns document bodies without YAML frontmatter to minimize token burn.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

SOURCE_TIER: dict[str, int] = {
    "first_party": 0,
    "original_framework": 0,
    "proprietary_insight": 0,
    "lived_experience": 0,
    "book": 1,
    "academic_paper": 1,
    "official_docs": 1,
    "specification": 1,
    "conference_talk": 2,
    "workshop": 2,
    "whitepaper": 2,
    "technical_report": 2,
    "tutorial": 3,
    "course": 3,
    "technical_blog": 3,
    "case_study": 3,
    "podcast": 4,
    "interview": 4,
    "youtube_video": 4,
    "newsletter": 4,
    "social_media": 5,
    "forum_post": 5,
    "tweet_thread": 5,
    "reddit_comment": 5,
}

AUTHORITY_TIER_BOOST = {"owner": -1, "creator": -1}

VERIFICATION_RANK = {
    "canonical": 0,
    "expert_verified": 1,
    "community_verified": 2,
    "self_verified": 3,
    "unverified": 4,
}

CONFIDENCE_RANK = {"high": 0, "medium": 1, "low": 2}


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if not match:
        return {}, text

    fm_raw, body = match.group(1), match.group(2)
    fm: dict = {}
    section: Optional[str] = None
    for line in fm_raw.split("\n"):
        section_match = re.match(r"^(\w+):\s*$", line)
        if section_match:
            section = section_match.group(1)
            fm[section] = {}
            continue
        if section:
            kv = re.match(r"^\s+(\w+):\s*(.+)$", line)
            if kv:
                fm[section][kv.group(1)] = kv.group(2).strip().strip('"').strip("'")
                continue
        kv = re.match(r"^(\w+):\s*(.+)$", line)
        if kv:
            fm[kv.group(1)] = kv.group(2).strip().strip('"').strip("'")
            section = None
    return fm, body


def effective_tier(fm: dict) -> int:
    quality = fm.get("quality", {}) if isinstance(fm.get("quality"), dict) else {}
    source = fm.get("source", {}) if isinstance(fm.get("source"), dict) else {}

    if "source_tier" in quality:
        try:
            tier = int(quality["source_tier"])
        except (TypeError, ValueError):
            tier = 4
    else:
        source_type = source.get("type", "")
        tier = SOURCE_TIER.get(source_type, 4)

    authority = source.get("author_authority", "")
    if authority in AUTHORITY_TIER_BOOST:
        tier = max(0, tier + AUTHORITY_TIER_BOOST[authority])
    return tier


@dataclass
class BrainDocument:
    path: str
    layer: str
    tier: int
    title: str
    body: str
    source_type: str = ""
    verification: str = ""
    confidence: str = ""
    tokens: int = 0
    score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "layer": self.layer,
            "tier": self.tier,
            "title": self.title,
            "source_type": self.source_type,
            "verification": self.verification,
            "confidence": self.confidence,
            "tokens_approx": self.tokens,
            "content": self.body,
        }


@dataclass
class BrainReader:
    brain_root: Path

    def __post_init__(self) -> None:
        self.brain_root = self.brain_root.expanduser().resolve()
        self.corpus_dir = self.brain_root / "corpus"

    def _require_corpus(self) -> None:
        if not self.corpus_dir.is_dir():
            raise FileNotFoundError(f"corpus/ not found under {self.brain_root}")

    def _domain_dir(self, domain: str) -> Path:
        self._require_corpus()
        domain_dir = self.corpus_dir / domain
        if not domain_dir.is_dir():
            raise FileNotFoundError(f"Domain not found: {domain}")
        return domain_dir

    def list_domains(self) -> list[dict]:
        self._require_corpus()
        domains = []
        for path in sorted(self.corpus_dir.iterdir()):
            if not path.is_dir() or path.name.startswith("."):
                continue
            domain_yaml = path / "_domain.yaml"
            name = path.name
            description = ""
            if domain_yaml.exists():
                text = domain_yaml.read_text(encoding="utf-8", errors="ignore")
                m = re.search(r'^name:\s*["\']?(.+?)["\']?\s*$', text, re.MULTILINE)
                if m:
                    name = m.group(1).strip()
                d = re.search(r"^description:\s*>\s*\n\s*(.+)", text, re.MULTILINE)
                if d:
                    description = d.group(1).strip()
            domains.append({"id": path.name, "name": name, "description": description})
        return domains

    def _layer_for_path(self, rel: Path) -> str:
        parts = rel.parts
        if "_crystal" in parts:
            return "crystal"
        if parts and parts[0] == "sources":
            return "sources"
        if parts and parts[0] == "examples":
            return "examples"
        return "knowledge"

    def _load_file(self, domain_dir: Path, rel: Path) -> Optional[BrainDocument]:
        fpath = domain_dir / rel
        if not fpath.is_file() or fpath.suffix not in (".md", ".txt"):
            return None
        raw = fpath.read_text(encoding="utf-8", errors="ignore")
        fm, body = parse_frontmatter(raw)
        quality = fm.get("quality", {}) if isinstance(fm.get("quality"), dict) else {}
        source = fm.get("source", {}) if isinstance(fm.get("source"), dict) else {}
        title = fm.get("title", "")
        if not title:
            hm = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
            title = hm.group(1).strip() if hm else fpath.name
        body_stripped = body.strip()
        return BrainDocument(
            path=str(rel).replace("\\", "/"),
            layer=self._layer_for_path(rel),
            tier=effective_tier(fm),
            title=title,
            body=body_stripped,
            source_type=source.get("type", ""),
            verification=quality.get("verification", ""),
            confidence=quality.get("confidence", ""),
            tokens=approx_tokens(body_stripped),
        )

    def bootstrap(
        self,
        domain: str,
        *,
        include_persona: bool = False,
        max_tokens: int = 4000,
    ) -> dict:
        """Load crystal layers only — default ~2.2K tokens before persona."""
        domain_dir = self._domain_dir(domain)
        crystal = domain_dir / "_crystal"
        order = ["seed.md", "principles.md"]
        if include_persona:
            order.append("persona.md")

        layers: dict[str, dict] = {}
        total_tokens = 0
        for name in order:
            fpath = crystal / name
            if not fpath.exists():
                continue
            doc = self._load_file(domain_dir, Path("_crystal") / name)
            if not doc:
                continue
            if total_tokens + doc.tokens > max_tokens:
                break
            layers[name.replace(".md", "")] = doc.to_dict()
            total_tokens += doc.tokens

        return {
            "brain_root": str(self.brain_root),
            "domain": domain,
            "mode": "bootstrap",
            "tokens_approx": total_tokens,
            "max_tokens": max_tokens,
            "layers": layers,
            "hint": "Call expand() only if bootstrap content is insufficient.",
        }

    def _collect_expandable(
        self,
        domain: str,
        *,
        layer: str = "knowledge",
        max_tier: int = 5,
    ) -> list[BrainDocument]:
        domain_dir = self._domain_dir(domain)
        docs: list[BrainDocument] = []
        allowed_roots: set[str] = set()
        if layer in ("knowledge", "all"):
            allowed_roots.update({"knowledge", "examples"})
        if layer in ("sources", "all"):
            allowed_roots.add("sources")

        for fpath in sorted(domain_dir.rglob("*")):
            if not fpath.is_file() or fpath.suffix not in (".md", ".txt"):
                continue
            rel = fpath.relative_to(domain_dir)
            if rel.parts and rel.parts[0].startswith("_"):
                continue
            if rel.parts and rel.parts[0] not in allowed_roots:
                continue
            doc = self._load_file(domain_dir, rel)
            if doc and doc.tier <= max_tier:
                docs.append(doc)
        return docs

    def _rank_docs(self, docs: list[BrainDocument], query: Optional[str]) -> list[BrainDocument]:
        q = (query or "").lower().strip()
        for doc in docs:
            score = 0.0
            if q:
                hay = f"{doc.title} {doc.body}".lower()
                if q in hay:
                    score += 10.0
                for term in q.split():
                    if term and term in hay:
                        score += 2.0
            score -= doc.tier * 2.0
            score -= VERIFICATION_RANK.get(doc.verification, 4) * 0.25
            score -= CONFIDENCE_RANK.get(doc.confidence, 2) * 0.15
            doc.score = score
        return sorted(docs, key=lambda d: (-d.score, d.tier, d.path))

    def expand(
        self,
        domain: str,
        *,
        layer: str = "knowledge",
        query: Optional[str] = None,
        max_tokens: int = 8000,
        max_tier: int = 5,
        max_documents: int = 10,
    ) -> dict:
        docs = self._rank_docs(self._collect_expandable(domain, layer=layer, max_tier=max_tier), query)

        selected: list[dict] = []
        total = 0
        for doc in docs[: max_documents * 3]:
            if len(selected) >= max_documents:
                break
            if total + doc.tokens > max_tokens:
                continue
            selected.append(
                {
                    "path": doc.path,
                    "tier": doc.tier,
                    "title": doc.title,
                    "tokens_approx": doc.tokens,
                    "source_type": doc.source_type,
                    "content": doc.body,
                }
            )
            total += doc.tokens

        return {
            "brain_root": str(self.brain_root),
            "domain": domain,
            "mode": "expand",
            "layer": layer,
            "query": query,
            "tokens_approx": total,
            "max_tokens": max_tokens,
            "documents": selected,
        }

    def search(
        self,
        domain: str,
        query: str,
        *,
        max_results: int = 5,
        max_tier: int = 5,
    ) -> dict:
        docs = self._rank_docs(
            self._collect_expandable(domain, layer="all", max_tier=max_tier),
            query,
        )
        hits = []
        for doc in docs[:max_results]:
            hits.append(
                {
                    "path": doc.path,
                    "tier": doc.tier,
                    "title": doc.title,
                    "layer": doc.layer,
                    "tokens_approx": doc.tokens,
                    "snippet": doc.body[:280].replace("\n", " "),
                }
            )
        return {
            "brain_root": str(self.brain_root),
            "domain": domain,
            "query": query,
            "results": hits,
        }

    def get_document(self, domain: str, rel_path: str) -> dict:
        domain_dir = self._domain_dir(domain)
        rel = Path(rel_path.lstrip("/"))
        doc = self._load_file(domain_dir, rel)
        if not doc:
            raise FileNotFoundError(f"Document not found: {rel_path}")
        return doc.to_dict()
