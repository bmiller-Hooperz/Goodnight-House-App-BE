from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from app.config import settings
from app.library import Resource, load_library

COLLECTION = settings.chroma_collection


def _client(persist_dir: Path | None = None) -> chromadb.PersistentClient:
    path = persist_dir or settings.chroma_dir
    path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(path))


def _embedding_fn():
    # Local ONNX MiniLM — free, no API key
    return embedding_functions.DefaultEmbeddingFunction()


def get_collection(client: chromadb.PersistentClient | None = None):
    client = client or _client()
    return client.get_or_create_collection(
        name=COLLECTION,
        embedding_function=_embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )


def indexable(resources: dict[str, Resource]) -> list[Resource]:
    return [r for r in resources.values() if r.embed and r.embed_text]


def reindex(
    library_path: Path | None = None,
    persist_dir: Path | None = None,
) -> dict:
    library_path = library_path or settings.library_path
    resources = load_library(library_path)
    rows = indexable(resources)

    client = _client(persist_dir)
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    collection = client.get_or_create_collection(
        name=COLLECTION,
        embedding_function=_embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )

    batch_size = 64
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        collection.add(
            ids=[r.id for r in batch],
            documents=[r.embed_text for r in batch],
            metadatas=[r.metadata() for r in batch],
        )

    return {
        "indexed": len(rows),
        "library_total": len(resources),
        "skipped_no_embed": len(resources) - len(rows),
        "collection": COLLECTION,
        "persist_dir": str(persist_dir or settings.chroma_dir),
    }


if __name__ == "__main__":
    result = reindex()
    print(result)
