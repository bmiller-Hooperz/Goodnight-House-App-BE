from __future__ import annotations

import re
from typing import Any

from openai import OpenAI

from app.config import has_openrouter_key, settings
from app.prompts import build_system_message, build_user_message
from app.retriever import Retriever

_SAFETY_ONLY = re.compile(
    r"^\s*(user\s*safety|response\s*safety)\s*:\s*\w+\s*"
    r"(response\s*safety|user\s*safety)?\s*:\s*\w+\s*$",
    re.IGNORECASE,
)


def _looks_like_safety_label(text: str) -> bool:
    cleaned = (text or "").strip()
    if not cleaned:
        return True
    if _SAFETY_ONLY.match(cleaned):
        return True
    # Short replies that are only safety boilerplate
    lower = cleaned.lower()
    if "user safety" in lower and "response safety" in lower and len(cleaned) < 80:
        return True
    return False


class ChatService:
    def __init__(self, retriever: Retriever | None = None) -> None:
        self.retriever = retriever or Retriever()
        self._system = build_system_message()

    def reload_prompts(self) -> None:
        self._system = build_system_message()

    def _client(self) -> OpenAI:
        if not has_openrouter_key():
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. Add your OpenRouter key to .env"
            )
        return OpenAI(
            api_key=settings.openrouter_api_key.strip(),
            base_url=settings.openrouter_base_url,
        )

    def _complete(self, client: OpenAI, model: str, messages: list[dict[str, str]]):
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.4,
        )
        reply = (completion.choices[0].message.content or "").strip()
        used = getattr(completion, "model", None) or model
        return reply, used

    def chat(
        self,
        message: str,
        family_context: dict[str, Any] | None = None,
        history: list[dict[str, str]] | None = None,
        top_k: int | None = None,
    ) -> dict[str, Any]:
        chunks = self.retriever.retrieve(
            query=message,
            top_k=top_k,
            family_context=family_context,
        )
        library_block = self.retriever.format_for_prompt(chunks)
        user_content = build_user_message(message, family_context, library_block)

        messages: list[dict[str, str]] = [{"role": "system", "content": self._system}]
        for turn in history or []:
            role = turn.get("role")
            content = (turn.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_content})

        if not chunks:
            reply = (
                "I want to stay inside Goodnight House guidance for you, and I do not "
                "have a clear library match for that yet. Can you tell me a bit more about "
                "what is going on, and where you are in your plan right now?"
            )
            return {
                "reply": reply,
                "citations": [],
                "retrieved": [],
                "model": None,
                "refused_empty_retrieval": True,
            }

        client = self._client()
        primary = settings.openrouter_model
        reply, used_model = self._complete(client, primary, messages)

        if _looks_like_safety_label(reply):
            fallback = settings.openrouter_fallback_model
            if fallback and fallback != primary:
                reply, used_model = self._complete(client, fallback, messages)
            if _looks_like_safety_label(reply):
                reply = (
                    "I hit a glitch getting a coaching reply just now. "
                    "Could you send that last update one more time?"
                )

        citations = [c.id for c in chunks]

        return {
            "reply": reply,
            "citations": citations,
            "retrieved": self.retriever.to_public(chunks),
            "model": used_model,
            "refused_empty_retrieval": False,
        }
