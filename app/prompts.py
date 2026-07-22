from __future__ import annotations

import json
from typing import Any

from app.config import settings

GUARDRAILS = """
RETRIEVAL GUARDRAILS (runtime)

You are given retrieved library resources labeled with resource_id. Treat those bodies as your source of truth for method content.

- Answer using only the retrieved library resources plus the always-on context and this family's plan/intake/log data.
- If the retrieved library does not cover the question, say you do not have specific Goodnight House guidance on that, and ask a clarifying question if needed. Do not invent sleep advice from general knowledge.
- Coach from the family's exact plan values when present. Do not invent schedule numbers or redesign their plan.
- Prefer warmth and Jessie's voice rules already stated above.
- When you use a library resource, keep the guidance faithful to that resource.
""".strip()


def load_text(path) -> str:
    return path.read_text(encoding="utf-8").strip()


def build_system_message() -> str:
    system = load_text(settings.system_prompt_path)
    always_on = load_text(settings.always_on_path)
    return (
        f"{system}\n\n"
        f"ALWAYS-ON CONTEXT\n\n{always_on}\n\n"
        f"{GUARDRAILS}"
    )


def format_family_context(family_context: dict[str, Any] | None) -> str:
    if not family_context:
        return "No personalized family plan payload was provided for this turn."
    return json.dumps(family_context, indent=2, ensure_ascii=False)


def build_user_message(
    message: str,
    family_context: dict[str, Any] | None,
    library_block: str,
) -> str:
    return (
        "FAMILY CONTEXT (structured; coach from these values)\n"
        f"{format_family_context(family_context)}\n\n"
        "RETRIEVED LIBRARY RESOURCES\n"
        f"{library_block}\n\n"
        "PARENT MESSAGE\n"
        f"{message.strip()}"
    )
