from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.chat import ChatService
from app.config import has_openrouter_key, settings
from app.indexer import reindex
from app.retriever import Retriever

retriever: Retriever | None = None
chat_service: ChatService | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global retriever, chat_service
    # Ensure index exists
    try:
        collection = None
        from app.indexer import get_collection

        collection = get_collection()
        if collection.count() == 0:
            reindex()
    except Exception:
        reindex()
    retriever = Retriever()
    chat_service = ChatService(retriever)
    yield


app = FastAPI(title="Goodnight House Chat", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: str | None = None
    family_context: dict[str, Any] | None = None
    history: list[ChatMessage] | None = None
    top_k: int | None = None


class ChatResponse(BaseModel):
    reply: str
    citations: list[str]
    retrieved: list[dict[str, Any]]
    model: str | None = None
    refused_empty_retrieval: bool = False
    conversation_id: str | None = None


@app.get("/health")
def health():
    count = 0
    try:
        if retriever:
            count = retriever.collection.count()
    except Exception:
        count = -1
    return {
        "ok": True,
        "indexed_resources": count,
        "model": settings.openrouter_model,
        "has_api_key": has_openrouter_key(),
    }


@app.post("/admin/reindex")
def admin_reindex():
    global retriever, chat_service
    result = reindex()
    retriever = Retriever()
    chat_service = ChatService(retriever)
    return result


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not chat_service:
        raise HTTPException(status_code=503, detail="Chat service not ready")
    try:
        result = chat_service.chat(
            message=req.message,
            family_context=req.family_context,
            history=[m.model_dump() for m in (req.history or [])],
            top_k=req.top_k,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream model error: {e}") from e

    return ChatResponse(
        reply=result["reply"],
        citations=result["citations"],
        retrieved=result["retrieved"],
        model=result.get("model"),
        refused_empty_retrieval=result.get("refused_empty_retrieval", False),
        conversation_id=req.conversation_id,
    )
