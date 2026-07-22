from __future__ import annotations

import json
from typing import Any

from app.config import settings

GUARDRAILS = """
RETRIEVAL GUARDRAILS (runtime)

You are given retrieved library resources labeled with resource_id. Treat those bodies as your source of truth for method content.

- Answer using the retrieved library resources plus the always-on context and this family's plan/intake/log data.
- The FAMILY CONTEXT may include this child's personalized plan blocks (plan_blocks). Those blocks are part of THEIR plan — coach from them as primary for schedule, stage steps, and family-specific instructions.
- If the retrieved library does not cover the question and their plan blocks also do not, say you do not have specific Goodnight House guidance on that, and ask a clarifying question if needed. Do not invent sleep advice from general knowledge.
- Coach from the family's exact plan values when present. Do not invent schedule numbers or redesign their plan.
- If known_issues are listed (for example nap-count gate mismatches), acknowledge reality vs plan carefully and still lead with what their plan specifies unless troubleshooting says otherwise.
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

    # Prefer a readable packing order for large Wren-style payloads
    plan_blocks = family_context.get("plan_blocks")
    core = {k: v for k, v in family_context.items() if k not in ("plan_blocks", "plan_stages")}
    parts = ["### Core family / intake / schedule", json.dumps(core, indent=2, ensure_ascii=False)]

    if plan_blocks:
        parts.append("### Personalized plan blocks (coach from these)")
        for block in plan_blocks:
            bid = block.get("id", "unknown")
            stage = block.get("stage", "")
            card = block.get("card", "")
            body = (block.get("body") or "").strip()
            parts.append(f"----\n[plan_block={bid}] stage={stage} | card={card}\n{body}")

    return "\n\n".join(parts)


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
