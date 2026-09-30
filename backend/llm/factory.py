from __future__ import annotations

import asyncio
import logging
import os
from functools import lru_cache
from typing import Literal

from config import key_present

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama


Provider = Literal[
    "auto",
    "claude",
    "chatgpt",
    "gemini",
    "ollama",
]


MODEL_IDS = {
    "claude": os.getenv(
        "CLAUDE_MODEL",
        "claude-sonnet-5-5",
    ),
    "chatgpt": os.getenv(
        "OPENAI_MODEL",
        "gpt-6-astra",
    ),
    "gemini": os.getenv(
        "GEMINI_MODEL",
        os.getenv(
            "GEMINI_VISION_MODEL",
            "gemini-2.5-flash",
        ),
    ),
    "ollama": os.getenv(
        "OLLAMA_MODEL",
        "llama3.2:3b",
    ),
}


KEYS = {
    "claude": "ANTHROPIC_API_KEY",
    "chatgpt": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
}


log = logging.getLogger(__name__)


def provider_order(
    provider: Provider,
    agent: str,
) -> list[str]:
    """
    Auto provider routing.

    Current free-friendly strategy:

    RAG / Vision:
        Gemini -> ChatGPT -> Claude -> Ollama

    Sales / resQ:
        Gemini -> ChatGPT -> Claude -> Ollama

    Providers without configured keys are automatically skipped.
    """

    if provider == "auto":
        if agent in (
            "rag_agent",
            "vision_agent",
        ):
            preferred = [
                "gemini",
                "chatgpt",
                "claude",
            ]
        else:
            preferred = [
                "gemini",
                "chatgpt",
                "claude",
            ]

        available = [
            p
            for p in preferred
            if key_present(
                KEYS[p]
            )
        ]

        return (
            available
            + ["ollama"]
        )

    if provider not in MODEL_IDS:
        raise ValueError(
            f"Unsupported provider: {provider}"
        )

    if provider == "ollama":
        return [
            "ollama"
        ]

    return [
        provider,
        "ollama",
    ]


@lru_cache(
    maxsize=10
)
def get_chat_model(
    provider: str,
    streaming: bool = False,
):
    timeout = float(
        os.getenv(
            "LLM_TIMEOUT_SECONDS",
            "90",
        )
    )

    if (
        provider in KEYS
        and not key_present(
            KEYS[provider]
        )
    ):
        raise RuntimeError(
            f"{provider} is not configured"
        )

    if provider == "claude":
        return ChatAnthropic(
            model=MODEL_IDS[
                provider
            ],
            api_key=os.environ[
                KEYS[provider]
            ],
            max_tokens=1600,
            timeout=timeout,
            max_retries=0,
            streaming=streaming,
        )

    if provider == "chatgpt":
        return ChatOpenAI(
            model=MODEL_IDS[
                provider
            ],
            api_key=os.environ[
                KEYS[provider]
            ],
            use_responses_api=True,
            max_tokens=2000,
            timeout=timeout,
            max_retries=0,
            streaming=streaming,
        )

    if provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=MODEL_IDS[
                provider
            ],
            google_api_key=os.environ[
                KEYS[provider]
            ],
            temperature=0.2,
            max_output_tokens=1800,
            max_retries=0,
        )

    if provider == "ollama":
        return ChatOllama(
            model=MODEL_IDS[
                provider
            ],
            base_url=os.getenv(
                "OLLAMA_BASE_URL",
                "http://127.0.0.1:11434",
            ),
            temperature=0.1,
            num_predict=900,
            client_kwargs={
                "timeout": timeout
            },
        )

    raise ValueError(
        f"Unknown provider: {provider}"
    )


def text_content(
    content,
) -> str:
    if isinstance(
        content,
        str,
    ):
        return content

    if isinstance(
        content,
        list,
    ):
        return "".join(
            block.get(
                "text",
                "",
            )
            for block
            in content
            if isinstance(
                block,
                dict,
            )
            and block.get(
                "type"
            )
            in (
                "text",
                "output_text",
            )
        )

    return ""


async def answer_with_fallback(
    provider: Provider,
    agent: str,
    messages,
):
    """
    Try providers in order.

    If Gemini/OpenAI/Claude fails,
    automatically continue to the next provider.
    """

    for candidate in provider_order(
        provider,
        agent,
    ):
        try:
            response = (
                await asyncio.wait_for(
                    get_chat_model(
                        candidate
                    ).ainvoke(
                        messages
                    ),
                    timeout=float(
                        os.getenv(
                            "LLM_TIMEOUT_SECONDS",
                            "90",
                        )
                    ),
                )
            )

            text = text_content(
                response.content
            ).strip()

            if not text:
                raise ValueError(
                    "Empty model answer"
                )

            return (
                text,
                candidate,
            )

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            log.warning(
                "Provider %s failed (%s)",
                candidate,
                type(exc).__name__,
            )

    raise RuntimeError(
        "No chat provider is currently available. "
        "Please try again shortly."
    )


def model_catalog() -> list[dict]:
    catalog = [
        {
            "provider": "auto",
            "model": "Automatic routing",
            "configured": True,
        }
    ]

    for provider, model in MODEL_IDS.items():
        configured = (
            provider == "ollama"
            or key_present(
                KEYS.get(
                    provider,
                    "",
                )
            )
        )

        catalog.append(
            {
                "provider": provider,
                "model": model,
                "configured": configured,
            }
        )

    return catalog