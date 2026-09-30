from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal

import chromadb
import numpy as np
from config import CHROMA_PATH, active_collection

from .multimodal import (
    GeminiMultimodal,
)




@dataclass
class RetrievedChunk:
    document: str
    metadata: dict[str, Any]
    distance: float | None
    citation: str


def _cosine_similarity(
    vector_a: np.ndarray,
    vector_b: np.ndarray,
) -> float:
    denominator = float(
        np.linalg.norm(
            vector_a
        )
        * np.linalg.norm(
            vector_b
        )
    )

    if denominator == 0.0:
        return 0.0

    return float(
        np.dot(
            vector_a,
            vector_b,
        )
        / denominator
    )


def _first_result_row(
    result: dict[str, Any],
    key: str,
) -> list[Any]:
    """
    Chroma query results are nested:
    [[result1, result2, ...]]

    This helper avoids NumPy truth-value errors.
    """

    value = result.get(
        key
    )

    if value is None:
        return []

    try:
        if len(value) == 0:
            return []
    except TypeError:
        return []

    first = value[0]

    if first is None:
        return []

    try:
        return list(
            first
        )
    except TypeError:
        return [
            first
        ]


class RAGRetriever:
    def __init__(
        self,
    ) -> None:
        self.chroma_path = os.getenv(
            "CHROMA_PATH",
            r"D:\reliance-data\chroma_db",
        )

        self.collection_name = active_collection()

        self.client = (
            chromadb.PersistentClient(
                path=self.chroma_path
            )
        )

        self.collection = (
            self.client
            .get_collection(
                name=self.collection_name
            )
        )

        self.gemini = (
            GeminiMultimodal()
        )

    @staticmethod
    def _citation(
        metadata: dict[
            str,
            Any,
        ],
        citation_number: int,
    ) -> str:
        source = str(
            metadata.get(
                "source",
                "unknown source",
            )
        )

        page = metadata.get(
            "page"
        )

        image_index = (
            metadata.get(
                "image_index"
            )
        )

        details = ""

        if page is not None:
            details += (
                ", page "
                + str(
                    page
                )
            )

        if image_index is not None:
            details += (
                ", image "
                + str(
                    image_index
                )
            )

        return (
            "["
            + str(
                citation_number
            )
            + "] "
            + source
            + details
        )

    def search(
        self,
        query: str,
        k: int = 5,
        search_type: Literal[
            "semantic",
            "mmr",
        ] = "mmr",
        candidate_k: int = 12,
        lambda_mult: float = 0.72,
    ) -> list[
        RetrievedChunk
    ]:
        """
        Run semantic or MMR search.
        """

        query = query.strip()

        if not query:
            return []

        collection_count = (
            self.collection.count()
        )

        if collection_count <= 0:
            return []

        query_embedding = (
            self.gemini
            .embed_text(
                query
            )
        )

        if search_type == "mmr":
            desired_candidates = max(
                candidate_k,
                k,
            )
        else:
            desired_candidates = k

        n_results = min(
            collection_count,
            desired_candidates,
        )

        result = (
            self.collection.query(
                query_embeddings=[
                    query_embedding
                ],
                n_results=(
                    n_results
                ),
                include=[
                    "documents",
                    "metadatas",
                    "distances",
                    "embeddings",
                ],
            )
        )

        documents = (
            _first_result_row(
                result,
                "documents",
            )
        )

        metadatas = (
            _first_result_row(
                result,
                "metadatas",
            )
        )

        distances = (
            _first_result_row(
                result,
                "distances",
            )
        )

        embeddings = (
            _first_result_row(
                result,
                "embeddings",
            )
        )

        if not documents:
            return []

        # ====================================================
        # Semantic search
        # ====================================================

        if (
            search_type
            == "semantic"
            or not embeddings
            or len(documents)
            <= k
        ):
            selected_indices = list(
                range(
                    min(
                        k,
                        len(
                            documents
                        ),
                    )
                )
            )

        # ====================================================
        # MMR search
        # ====================================================

        else:
            query_vector = np.asarray(
                query_embedding,
                dtype=np.float32,
            )

            candidate_vectors: list[
                np.ndarray
            ] = [
                np.asarray(
                    embedding,
                    dtype=np.float32,
                )
                for embedding
                in embeddings
            ]

            relevance_scores = [
                _cosine_similarity(
                    query_vector,
                    candidate_vector,
                )
                for candidate_vector
                in candidate_vectors
            ]

            first_index = int(
                np.argmax(
                    relevance_scores
                )
            )

            selected_indices = [
                first_index
            ]

            target_count = min(
                k,
                len(
                    candidate_vectors
                ),
            )

            while (
                len(
                    selected_indices
                )
                < target_count
            ):
                best_index: (
                    int
                    | None
                ) = None

                best_score = (
                    -float(
                        "inf"
                    )
                )

                for (
                    candidate_index,
                    candidate_vector,
                ) in enumerate(
                    candidate_vectors
                ):
                    if (
                        candidate_index
                        in selected_indices
                    ):
                        continue

                    max_similarity_to_selected = max(
                        _cosine_similarity(
                            candidate_vector,
                            candidate_vectors[
                                selected_index
                            ],
                        )
                        for selected_index
                        in selected_indices
                    )

                    mmr_score = (
                        lambda_mult
                        * relevance_scores[
                            candidate_index
                        ]
                        - (
                            1.0
                            - lambda_mult
                        )
                        * max_similarity_to_selected
                    )

                    if (
                        mmr_score
                        > best_score
                    ):
                        best_score = (
                            mmr_score
                        )

                        best_index = (
                            candidate_index
                        )

                if best_index is None:
                    break

                selected_indices.append(
                    best_index
                )

        chunks: list[
            RetrievedChunk
        ] = []

        for (
            citation_number,
            result_index,
        ) in enumerate(
            selected_indices,
            start=1,
        ):
            raw_metadata: Any = {}

            if (
                result_index
                < len(
                    metadatas
                )
            ):
                raw_metadata = (
                    metadatas[
                        result_index
                    ]
                    or {}
                )

            metadata = (
                dict(
                    raw_metadata
                )
                if isinstance(
                    raw_metadata,
                    dict,
                )
                else {}
            )

            distance: (
                float
                | None
            ) = None

            if (
                result_index
                < len(
                    distances
                )
                and distances[
                    result_index
                ]
                is not None
            ):
                distance = float(
                    distances[
                        result_index
                    ]
                )

            document = str(
                documents[
                    result_index
                ]
            )

            citation = (
                self._citation(
                    metadata,
                    citation_number,
                )
            )

            chunks.append(
                RetrievedChunk(
                    document=(
                        document
                    ),
                    metadata=(
                        metadata
                    ),
                    distance=(
                        distance
                    ),
                    citation=(
                        citation
                    ),
                )
            )

        return chunks

    @staticmethod
    def format_context(
        chunks: list[
            RetrievedChunk
        ],
    ) -> tuple[
        str,
        list[
            dict[
                str,
                Any,
            ]
        ],
    ]:
        """
        Convert retrieval results into LLM context +
        frontend citation metadata.
        """

        if not chunks:
            return (
                (
                    "No matching documents were found "
                    "in the Reliance Digital knowledge base."
                ),
                [],
            )

        context_parts: list[
            str
        ] = []

        citations: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for chunk in chunks:
            context_parts.append(
    chunk.document
)

            citations.append(
                {
                    "label": (
                        chunk.citation
                    ),
                    "source": (
                        chunk.metadata.get(
                            "source",
                            "unknown source",
                        )
                    ),
                    "page": (
                        chunk.metadata.get(
                            "page"
                        )
                    ),
                    "type": (
                        chunk.metadata.get(
                            "type",
                            "text",
                        )
                    ),
                }
            )

        return (
            "\n\n".join(
                context_parts
            ),
            citations,
        )