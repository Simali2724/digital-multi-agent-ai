from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
from typing import Iterable

import chromadb
import pymupdf
from config import CHROMA_PATH, active_collection
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

from .multimodal import (
    GeminiMultimodal,
    extract_pdf_images,
    guess_mime_type,
)




SUPPORTED_TEXT_SUFFIXES = {
    ".txt",
    ".md",
}

SUPPORTED_IMAGE_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}

SUPPORTED_SUFFIXES = (
    SUPPORTED_TEXT_SUFFIXES
    | SUPPORTED_IMAGE_SUFFIXES
    | {".pdf"}
)


def _stable_id(
    *parts: str,
) -> str:
    """
    Generate a deterministic Chroma document ID.
    """

    combined = "||".join(
        parts
    )

    return hashlib.sha256(
        combined.encode(
            "utf-8",
            errors="ignore",
        )
    ).hexdigest()


class RAGIngestor:
    """
    Ingest:
    - PDF
    - TXT
    - Markdown
    - images

    into persistent ChromaDB.
    """

    def __init__(
        self,
    ) -> None:
        self.chroma_path = os.getenv(
            "CHROMA_PATH",
            r"D:\reliance-data\chroma_db",
        )

        self.collection_name = os.getenv('REBUILD_COLLECTION') or active_collection()

        Path(
            self.chroma_path
        ).mkdir(
            parents=True,
            exist_ok=True,
        )

        self.client = (
            chromadb.PersistentClient(
                path=self.chroma_path
            )
        )

        self.collection = (
            self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "hnsw:space": "cosine",
                },
            )
        )

        self.gemini = (
            GeminiMultimodal()
        )

        self.splitter = (
            RecursiveCharacterTextSplitter(
                chunk_size=int(
                    os.getenv(
                        "RAG_CHUNK_SIZE",
                        "1200",
                    )
                ),
                chunk_overlap=int(
                    os.getenv(
                        "RAG_CHUNK_OVERLAP",
                        "180",
                    )
                ),
                separators=[
                    "\n\n",
                    "\n",
                    ". ",
                    " ",
                    "",
                ],
            )
        )

    def reset(self) -> None:
        raise RuntimeError("Destructive reset disabled. Run python -m rag.rebuild to safely rebuild.")

    def _upsert(
        self,
        document: str,
        embedding: list[float],
        metadata: dict[
            str,
            str | int | float | bool,
        ],
        document_id: str,
    ) -> None:
        self.collection.upsert(
            ids=[
                document_id
            ],
            documents=[
                document
            ],
            embeddings=[
                embedding
            ],
            metadatas=[
                metadata
            ],
        )

    def ingest_text(
        self,
        text: str,
        source: str,
        page: int | None = None,
    ) -> int:
        """
        Split text and embed each chunk.
        """

        text = text.strip()

        if not text:
            return 0

        raw_chunks = (
            self.splitter.split_text(
                text
            )
        )

        chunks = [
            chunk.strip()
            for chunk in raw_chunks
            if chunk.strip()
        ]

        for (
            chunk_index,
            chunk,
        ) in enumerate(
            chunks,
            start=1,
        ):
            metadata: dict[
                str,
                str | int | float | bool,
            ] = {
                "source": source,
                "type": "text",
                "chunk": chunk_index,
            }

            if page is not None:
                metadata[
                    "page"
                ] = page

            document_id = (
                _stable_id(
                    source,
                    str(
                        page
                        if page is not None
                        else 0
                    ),
                    str(
                        chunk_index
                    ),
                    chunk,
                )
            )

            embedding = (
                self.gemini.embed_text(
                    chunk
                )
            )

            self._upsert(
                document=chunk,
                embedding=embedding,
                metadata=metadata,
                document_id=(
                    document_id
                ),
            )

        return len(
            chunks
        )

    def ingest_image_bytes(
        self,
        image_bytes: bytes,
        mime_type: str,
        source: str,
        page: int | None = None,
        image_index: int | None = None,
        description: str | None = None,
    ) -> str:
        """
        Describe image with Gemini Vision, then embed
        description + image into Gemini Embedding 2.
        """

        if description is None:
            description = (
                self.gemini
                .describe_image_bytes(
                    image_bytes,
                    mime_type,
                )
            )

        embedding = (
            self.gemini.embed_multimodal(
                description=description,
                image_bytes=image_bytes,
                mime_type=mime_type,
            )
        )

        metadata: dict[
            str,
            str | int | float | bool,
        ] = {
            "source": source,
            "type": "image",
            "mime_type": mime_type,
        }

        if page is not None:
            metadata[
                "page"
            ] = page

        if image_index is not None:
            metadata[
                "image_index"
            ] = image_index

        document_id = (
            _stable_id(
                source,
                str(
                    page
                    if page is not None
                    else 0
                ),
                str(
                    image_index
                    if image_index
                    is not None
                    else 0
                ),
                description,
            )
        )

        self._upsert(
            document=description,
            embedding=embedding,
            metadata=metadata,
            document_id=(
                document_id
            ),
        )

        return description

    def ingest_file(
        self,
        path: Path,
    ) -> dict[str, int]:
        """
        Ingest one supported file.
        """

        suffix = (
            path.suffix.lower()
        )

        counts = {
            "text_chunks": 0,
            "images": 0,
        }

        # ====================================================
        # TXT / Markdown
        # ====================================================

        if (
            suffix
            in SUPPORTED_TEXT_SUFFIXES
        ):
            text = (
                path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            )

            counts[
                "text_chunks"
            ] = self.ingest_text(
                text=text,
                source=str(
                    path
                ),
            )

            return counts

        # ====================================================
        # PDF
        # ====================================================

        if suffix == ".pdf":
            document = (
                pymupdf.open(
                    str(path)
                )
            )

            try:
                for page_index in range(
                    len(document)
                ):
                    page = document[
                        page_index
                    ]

                    text = (
                        page.get_text(
                            "text"
                        )
                        or ""
                    ).strip()

                    if text:
                        count = (
                            self.ingest_text(
                                text=text,
                                source=str(
                                    path
                                ),
                                page=(
                                    page_index
                                    + 1
                                ),
                            )
                        )

                        counts[
                            "text_chunks"
                        ] += count

            finally:
                document.close()

            # Extract images embedded in PDF.
            for (
                page_number,
                image_index,
                image_bytes,
                mime_type,
            ) in extract_pdf_images(
                path
            ):
                self.ingest_image_bytes(
                    image_bytes=(
                        image_bytes
                    ),
                    mime_type=(
                        mime_type
                    ),
                    source=str(
                        path
                    ),
                    page=(
                        page_number
                    ),
                    image_index=(
                        image_index
                    ),
                )

                counts[
                    "images"
                ] += 1

            return counts

        # ====================================================
        # Standalone image
        # ====================================================

        if (
            suffix
            in SUPPORTED_IMAGE_SUFFIXES
        ):
            image_bytes = (
                path.read_bytes()
            )

            mime_type = (
                guess_mime_type(
                    path
                )
            )

            self.ingest_image_bytes(
                image_bytes=(
                    image_bytes
                ),
                mime_type=(
                    mime_type
                ),
                source=str(
                    path
                ),
            )

            counts[
                "images"
            ] = 1

            return counts

        return counts

    def ingest_paths(
        self,
        paths: Iterable[
            Path
        ],
    ) -> dict[str, int]:
        """
        Ingest multiple files or folders.
        """

        totals = {
            "files": 0,
            "text_chunks": 0,
            "images": 0,
        }

        for supplied_path in paths:
            supplied_path = (
                supplied_path
                .expanduser()
                .resolve()
            )

            if not supplied_path.exists():
                print(
                    "Skipping missing path: "
                    + str(
                        supplied_path
                    )
                )

                continue

            if supplied_path.is_file():
                files = [
                    supplied_path
                ]

            else:
                files = [
                    file_path
                    for file_path
                    in supplied_path.rglob(
                        "*"
                    )
                    if (
                        file_path.is_file()
                        and (
                            file_path
                            .suffix
                            .lower()
                            in SUPPORTED_SUFFIXES
                        )
                    )
                ]

            for file_path in files:
                if (
                    file_path
                    .suffix
                    .lower()
                    not in SUPPORTED_SUFFIXES
                ):
                    continue

                print(
                    "Ingesting: "
                    + str(
                        file_path
                    )
                )

                result = (
                    self.ingest_file(
                        file_path
                    )
                )

                totals[
                    "files"
                ] += 1

                totals[
                    "text_chunks"
                ] += result[
                    "text_chunks"
                ]

                totals[
                    "images"
                ] += result[
                    "images"
                ]

                print(
                    "Completed: "
                    + str(
                        file_path
                    )
                    + " -> "
                    + str(
                        result
                    )
                )

        return totals


def main() -> None:
    parser = (
        argparse.ArgumentParser(
            description=(
                "Ingest Reliance Digital "
                "knowledge into ChromaDB."
            )
        )
    )

    parser.add_argument(
        "--path",
        action="append",
        required=True,
        help=(
            "File or folder path. "
            "Repeat --path for multiple locations."
        ),
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help=(
            "Delete the existing Chroma "
            "collection before ingestion."
        ),
    )

    args = parser.parse_args()

    ingestor = (
        RAGIngestor()
    )

    if args.reset:
        print(
            "Resetting Chroma collection..."
        )

        ingestor.reset()

    totals = (
        ingestor.ingest_paths(
            Path(
                path_string
            )
            for path_string
            in args.path
        )
    )

    print()
    print(
        "RAG ingestion complete."
    )
    print(
        json_summary(
            totals
        )
    )


def json_summary(
    totals: dict[str, int],
) -> str:
    return (
        "Files: "
        + str(
            totals["files"]
        )
        + " | Text chunks: "
        + str(
            totals[
                "text_chunks"
            ]
        )
        + " | Images: "
        + str(
            totals["images"]
        )
    )


if __name__ == "__main__":
    main()