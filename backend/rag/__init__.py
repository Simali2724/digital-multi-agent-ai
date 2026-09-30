from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .ingest import RAGIngestor
    from .retriever import RAGRetriever, RetrievedChunk


def __getattr__(name: str) -> Any:
    if name == "RAGIngestor":
        from .ingest import RAGIngestor

        return RAGIngestor

    if name == "RAGRetriever":
        from .retriever import RAGRetriever

        return RAGRetriever

    if name == "RetrievedChunk":
        from .retriever import RetrievedChunk

        return RetrievedChunk

    raise AttributeError(
        f"module 'rag' has no attribute {name!r}"
    )


__all__ = [
    "RAGIngestor",
    "RAGRetriever",
    "RetrievedChunk",
]