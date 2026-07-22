from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.config import settings
from app.indexer import get_collection
from app.library import Resource, load_library


@dataclass
class RetrievedChunk:
    id: str
    title: str
    body: str
    stage: str | None
    section: str | None
    content_type: str
    score: float | None
    gated: bool
    related: list[str]

    def as_prompt_block(self) -> str:
        return (
            f"[resource_id={self.id}]\n"
            f"title: {self.title}\n"
            f"{self.body.strip()}"
        )


class Retriever:
    def __init__(self) -> None:
        self.resources: dict[str, Resource] = load_library(settings.library_path)
        self.collection = get_collection()

    def reload(self) -> None:
        self.resources = load_library(settings.library_path)
        self.collection = get_collection()

    def _gate_ok(self, resource: Resource, family_context: dict[str, Any] | None) -> bool:
        if not resource.gated:
            return True
        if not family_context:
            return False
        earned = set(family_context.get("gates_earned") or [])
        flags = family_context.get("flags") or {}
        req = resource.gate_requires or ""
        if req and req in earned:
            return True
        if req and flags.get(req):
            return True
        return False

    def _stage_ok(self, resource: Resource, family_context: dict[str, Any] | None) -> bool:
        if not family_context:
            return True
        # Optional soft filter: if client sends allowed_stages, honor it
        allowed = family_context.get("allowed_stages")
        if not allowed:
            return True
        if not resource.stage:
            return True
        return resource.stage in allowed or any(
            str(a) in resource.stage for a in allowed
        )

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        family_context: dict[str, Any] | None = None,
        expand_related: bool = True,
    ) -> list[RetrievedChunk]:
        k = top_k or settings.chat_top_k
        # Over-fetch then filter
        n = min(max(k * 3, k), 24)
        result = self.collection.query(
            query_texts=[query],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )

        ids = (result.get("ids") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        chunks: list[RetrievedChunk] = []
        seen: set[str] = set()

        for i, rid in enumerate(ids):
            resource = self.resources.get(rid)
            if not resource:
                continue
            if resource.content_type == "audio_transcript":
                # Prefer parent-facing; transcripts only if nothing else later
                pass
            if not self._gate_ok(resource, family_context):
                continue
            if not self._stage_ok(resource, family_context):
                continue
            dist = distances[i] if i < len(distances) else None
            score = None if dist is None else max(0.0, 1.0 - float(dist))
            chunks.append(
                RetrievedChunk(
                    id=resource.id,
                    title=resource.title,
                    body=resource.body,
                    stage=resource.stage,
                    section=resource.section,
                    content_type=resource.content_type,
                    score=score,
                    gated=resource.gated,
                    related=list(resource.related),
                )
            )
            seen.add(resource.id)
            if len(chunks) >= k:
                break

        if expand_related and chunks:
            # Expand first hit's related resources (1-hop) if room
            related_ids = []
            for c in chunks[:2]:
                related_ids.extend(c.related)
            for rid in related_ids:
                if rid in seen:
                    continue
                resource = self.resources.get(rid)
                if not resource or not resource.body:
                    continue
                if not self._gate_ok(resource, family_context):
                    continue
                chunks.append(
                    RetrievedChunk(
                        id=resource.id,
                        title=resource.title,
                        body=resource.body,
                        stage=resource.stage,
                        section=resource.section,
                        content_type=resource.content_type,
                        score=None,
                        gated=resource.gated,
                        related=list(resource.related),
                    )
                )
                seen.add(rid)
                if len(chunks) >= k + 2:
                    break

        return chunks

    def format_for_prompt(self, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "(No library resources matched this question.)"
        return "\n\n---\n\n".join(c.as_prompt_block() for c in chunks)

    def to_public(self, chunks: list[RetrievedChunk]) -> list[dict[str, Any]]:
        out = []
        for c in chunks:
            d = asdict(c)
            # Don't dump full body in API response by default size; keep for debug
            d["body_preview"] = (c.body or "")[:240]
            del d["body"]
            out.append(d)
        return out
