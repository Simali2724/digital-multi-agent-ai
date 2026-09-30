from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path
from typing import Iterator

import pymupdf
from config import CHROMA_PATH, active_collection
from google import genai
from google.genai import types




class GeminiMultimodal:
    """
    Gemini helper used for:

    1. Image understanding / description.
    2. Text embeddings.
    3. Multimodal image + text embeddings.
    """

    def __init__(self) -> None:
        api_key = os.getenv(
            "GOOGLE_API_KEY",
            "",
        ).strip()

        if not api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is required for "
                "Gemini vision and RAG embeddings."
            )

        self.client = genai.Client(
            api_key=api_key, http_options=types.HttpOptions(timeout=30000)
        )

        self.vision_model = os.getenv(
            "GEMINI_VISION_MODEL",
            os.getenv(
                "GEMINI_MODEL",
                "gemini-3.6-flash",
            ),
        )

        self.embedding_model = os.getenv(
            "GEMINI_EMBED_MODEL",
            "gemini-embedding-2",
        )

        self.embedding_dim = int(
            os.getenv(
                "GEMINI_EMBED_DIM",
                "768",
            )
        )

    @staticmethod
    def _embedding_values(
        response: object,
    ) -> list[float]:
        embeddings = getattr(
            response,
            "embeddings",
            None,
        )

        if not embeddings:
            raise RuntimeError(
                "Gemini returned no embedding."
            )

        values = getattr(
            embeddings[0],
            "values",
            None,
        )

        if values is None:
            raise RuntimeError(
                "Gemini embedding contains no values."
            )

        return [
            float(value)
            for value in values
        ]

    def describe_image_bytes(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str | None = None,
    ) -> str:
        """
        Describe an image using Gemini Vision.
        """

        if prompt is None:
            prompt = (
                "Describe this electronics-related image "
                "for a Reliance Digital support knowledge base. "
                "Include visible product labels, model numbers, "
                "ports, controls, status lights, error messages, "
                "physical damage and troubleshooting-relevant "
                "details. Do not guess anything that is not visible."
            )

        response = (
            self.client.models.generate_content(
                model=self.vision_model,
                contents=[
                    prompt,
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=mime_type,
                    ),
                ],
            )
        )

        text = getattr(
            response,
            "text",
            None,
        )

        if not text:
            return (
                "Gemini did not return a visual description."
            )

        return str(
            text
        ).strip()

    def embed_text(
        self,
        text: str,
    ) -> list[float]:
        """
        Embed plain text using Gemini Embedding 2.
        """

        text = text.strip()

        if not text:
            raise ValueError(
                "Cannot embed empty text."
            )

        response = (
            self.client.models.embed_content(
                model=self.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(
                    output_dimensionality=(
                        self.embedding_dim
                    )
                ),
            )
        )

        return self._embedding_values(
            response
        )

    def embed_multimodal(
        self,
        description: str,
        image_bytes: bytes,
        mime_type: str,
    ) -> list[float]:
        """
        Generate one multimodal embedding from:
        - text description
        - image
        """

        response = (
            self.client.models.embed_content(
                model=self.embedding_model,
                contents=[
                    description,
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=mime_type,
                    ),
                ],
                config=types.EmbedContentConfig(
                    output_dimensionality=(
                        self.embedding_dim
                    )
                ),
            )
        )

        return self._embedding_values(
            response
        )


def decode_data_url(
    data_url: str,
) -> tuple[bytes, str]:
    """
    Decode:

    data:image/png;base64,AAAA...

    into:
    - raw bytes
    - MIME type
    """

    if not data_url.startswith(
        "data:"
    ):
        raise ValueError(
            "Invalid image data URL."
        )

    if ";base64," not in data_url:
        raise ValueError(
            "Expected a base64 encoded data URL."
        )

    header, encoded = (
        data_url.split(
            ",",
            1,
        )
    )

    mime_type = (
        header[
            len("data:"):
        ].split(
            ";",
            1,
        )[0]
        or "application/octet-stream"
    )

    try:
        image_bytes = (
            base64.b64decode(
                encoded,
                validate=True,
            )
        )
    except Exception as exc:
        raise ValueError(
            "Invalid base64 image data."
        ) from exc

    return (
        image_bytes,
        mime_type,
    )


def guess_mime_type(
    path: Path,
) -> str:
    guessed, _ = (
        mimetypes.guess_type(
            str(path)
        )
    )

    return (
        guessed
        or "application/octet-stream"
    )


def extract_pdf_images(
    pdf_path: Path,
) -> Iterator[
    tuple[
        int,
        int,
        bytes,
        str,
    ]
]:
    """
    Extract unique images from a PDF.

    Yields:

    page_number,
    image_index,
    image_bytes,
    mime_type
    """

    document = pymupdf.open(
        str(pdf_path)
    )

    seen_xrefs: set[int] = set()

    try:
        for page_index in range(
            len(document)
        ):
            page = document[
                page_index
            ]

            images = page.get_images(
                full=True
            )

            for (
                image_index,
                image_info,
            ) in enumerate(
                images,
                start=1,
            ):
                xref = int(
                    image_info[0]
                )

                if xref in seen_xrefs:
                    continue

                seen_xrefs.add(
                    xref
                )

                extracted = (
                    document.extract_image(
                        xref
                    )
                )

                image_bytes = extracted[
                    "image"
                ]

                extension = str(
                    extracted.get(
                        "ext",
                        "png",
                    )
                ).lower()

                mime_type = {
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "png": "image/png",
                    "webp": "image/webp",
                    "bmp": "image/bmp",
                    "tiff": "image/tiff",
                }.get(
                    extension,
                    "image/"
                    + extension,
                )

                yield (
                    page_index + 1,
                    image_index,
                    image_bytes,
                    mime_type,
                )

    finally:
        document.close()