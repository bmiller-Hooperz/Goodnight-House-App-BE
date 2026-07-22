from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Resource:
    id: str
    title: str
    body: str
    retrieve_when: str
    stage: str | None
    section: str | None
    content_type: str
    embed: bool
    gated: bool
    gate_requires: str | None
    related: list[str] = field(default_factory=list)
    backs_block: str | None = None
    word_count: int = 0
    is_parent: bool = False
    has_children: bool = False

    @property
    def embed_text(self) -> str:
        parts = [self.title.strip(), (self.retrieve_when or "").strip()]
        return "\n\n".join(p for p in parts if p)

    def metadata(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "stage": self.stage or "",
            "section": self.section or "",
            "content_type": self.content_type or "",
            "gated": self.gated,
            "gate_requires": self.gate_requires or "",
            "embed": self.embed,
        }


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def load_library(path: Path) -> dict[str, Resource]:
    resources: dict[str, Resource] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            rid = raw["id"]
            resources[rid] = Resource(
                id=rid,
                title=raw.get("title") or rid,
                body=raw.get("body") or "",
                retrieve_when=raw.get("retrieve_when") or "",
                stage=raw.get("stage"),
                section=raw.get("section"),
                content_type=raw.get("content_type") or "parent_facing",
                embed=bool(raw.get("embed", True)),
                gated=bool(raw.get("gated", False)),
                gate_requires=raw.get("gate_requires"),
                related=_as_list(raw.get("related")),
                backs_block=raw.get("backs_block"),
                word_count=int(raw.get("word_count") or 0),
                is_parent=bool(raw.get("is_parent", False)),
                has_children=bool(raw.get("has_children", False)),
            )
    return resources
