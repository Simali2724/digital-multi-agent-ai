
from __future__ import annotations

import asyncio
import logging
import os

from functools import lru_cache
from typing import Literal

from config import key_present
from privacy import public_answer
from .language import ReplyLanguage, language_mismatch, prepare_language

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama


# ============================================================
# SUPPORTED AI PROVIDERS
# ============================================================

Provider = Literal[
    "auto",
    "claude",
    "chatgpt",
    "gemini",
    "gemma",
    "ollama",
]


# ============================================================
# MODEL CONFIGURATION
# ============================================================

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
    "gemma": os.getenv(
        "GEMMA_MODEL",
        "gemma-4-26b-a4b-it",
    ),
    "ollama": os.getenv(
        "OLLAMA_MODEL",
        "llama3.2:3b",
    ),
}


# ============================================================
# API KEY ENVIRONMENT VARIABLES
# ============================================================

KEYS = {
    "claude": "ANTHROPIC_API_KEY",
    "chatgpt": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "gemma": "GOOGLE_API_KEY",
}


log = logging.getLogger(__name__)


# ============================================================
# PROVIDER ORDER AND AUTOMATIC FALLBACK
# ============================================================

def provider_order(
    provider: Provider,
    agent: str,
) -> list[str]:
    """
    Automatic provider order:

    1. Gemini API
    2. Gemma 4 Online
    3. Ollama local fallback
    4. ChatGPT
    5. Claude

    Cloud providers are included only when
    their API keys are configured.

    Explicit provider selections use only
    the selected provider.
    """

    if provider == "auto":
        google_providers = [
            name
            for name in ("gemini", "gemma")
            if key_present(KEYS[name])
        ]

        cloud_backups = [
            name
            for name in ("chatgpt", "claude")
            if key_present(KEYS[name])
        ]

        return (
            google_providers
            + ["ollama"]
            + cloud_backups
        )

    if provider not in MODEL_IDS:
        raise ValueError(
            f"Unsupported provider: {provider}"
        )

    return [provider]


# ============================================================
# PROVIDER ERROR HANDLING
# ============================================================

class ProviderUnavailable(RuntimeError):
    """Safe public error without exposing credentials."""

    def __init__(self, code):
        self.code = code

        super().__init__(
            f"No chat provider available ({code})."
        )


def failure_code(exc):
    status = (
        getattr(exc, "status_code", None)
        or getattr(exc, "code", None)
    )

    name = type(exc).__name__.lower()

    if status == "language_mismatch":
        return "language_mismatch"

    if (
        status in (401, 403)
        or "authentication" in name
        or "permissiondenied" in name
    ):
        return "authentication"

    if (
        status == 429
        or "ratelimit" in name
        or "resourceexhausted" in name
    ):
        return "rate_limit"

    if (
        isinstance(exc, TimeoutError)
        or "timeout" in name
    ):
        return "timeout"

    if (
        "connect" in name
        or status in (500, 502, 503, 504)
    ):
        return "temporary_connection"

    return "provider_error"


# ============================================================
# CREATE AI MODEL CLIENT
# ============================================================

@lru_cache(maxsize=10)
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

    # Check API key for cloud providers.
    if (
        provider in KEYS
        and not key_present(KEYS[provider])
    ):
        raise RuntimeError(
            f"{provider} is not configured"
        )

    # --------------------------------------------------------
    # CLAUDE
    # --------------------------------------------------------

    if provider == "claude":
        return ChatAnthropic(
            model=MODEL_IDS[provider],
            api_key=os.environ[KEYS[provider]],
            max_tokens=1600,
            timeout=timeout,
            max_retries=0,
            streaming=streaming,
        )

    # --------------------------------------------------------
    # OPENAI / CHATGPT
    # --------------------------------------------------------

    if provider == "chatgpt":
        return ChatOpenAI(
            model=MODEL_IDS[provider],
            api_key=os.environ[KEYS[provider]],
            use_responses_api=True,
            max_tokens=2000,
            timeout=timeout,
            max_retries=0,
            streaming=streaming,
        )

    # --------------------------------------------------------
    # GOOGLE GEMINI AND GEMMA ONLINE
    # --------------------------------------------------------

    if provider == "gemma":
        from .gemma_native import GemmaNative
        return GemmaNative(MODEL_IDS[provider], os.environ[KEYS[provider]], min(timeout, 60))

    if provider in ("gemini", "gemma"):
        return ChatOpenAI(
            model=MODEL_IDS[provider],
            api_key=os.environ[KEYS[provider]],
            base_url=(
                "https://generativelanguage.googleapis.com/"
                "v1beta/openai/"
            ),
            max_tokens=1800,
            reasoning_effort="minimal" if provider == "gemma" else None,
            timeout=min(timeout, 60),
            max_retries=0,
        )

    # --------------------------------------------------------
    # LOCAL OLLAMA
    # --------------------------------------------------------

    if provider == "ollama":
        return ChatOllama(
            model=MODEL_IDS[provider],
            base_url=os.getenv(
                "OLLAMA_BASE_URL",
                "http://127.0.0.1:11434",
            ),
            temperature=0.1,
            num_predict=int(
                os.getenv(
                    "OLLAMA_NUM_PREDICT",
                    "900",
                )
            ),
            num_ctx=int(
                os.getenv(
                    "OLLAMA_CONTEXT_LENGTH",
                    "4096",
                )
            ),
            num_batch=int(
                os.getenv(
                    "OLLAMA_NUM_BATCH",
                    "64",
                )
            ),
            client_kwargs={
                "timeout": timeout,
            },
        )

    raise ValueError(
        f"Unknown provider: {provider}"
    )


# ============================================================
# EXTRACT TEXT FROM MODEL RESPONSE
# ============================================================

def text_content(content) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if (
                isinstance(block, dict)
                and block.get("type") in (
                    "text",
                    "output_text",
                )
            )
        )

    return ""


# ============================================================
# RESPONSE WITH TOKEN USAGE METADATA
# ============================================================

class MeteredAnswer(tuple):
    """
    Preserve the existing (text, provider) interface
    while carrying optional token usage metadata.
    """

    def __new__(
        cls,
        text,
        provider,
        usage=None,
        model=None,
        complete=True,
    ):
        result = super().__new__(
            cls,
            (text, provider),
        )

        result.usage = usage
        result.model = model
        result.usage_complete = complete

        return result


# ============================================================
# TOKEN USAGE EXTRACTION - UPDATED
# ============================================================

def response_usage(response):
    """
    Extract actual token usage reported by the model.

    Supports:
    - Ollama usage_metadata
    - LangChain standard usage_metadata
    - OpenAI / Google token_usage

    Does not estimate token counts from visible text.
    """

    # --------------------------------------------------------
    # 1. LangChain standard metadata
    #    Used by Ollama and other chat models.
    # --------------------------------------------------------

    usage = getattr(
        response,
        "usage_metadata",
        None,
    )

    if isinstance(usage, dict):
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")

        if (
            isinstance(input_tokens, int)
            and isinstance(output_tokens, int)
        ):
            result = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }

            total_tokens = usage.get("total_tokens")

            if isinstance(total_tokens, int):
                result["total_tokens"] = total_tokens

            return result

    # --------------------------------------------------------
    # 2. Alternative provider response metadata
    #    Used by OpenAI-compatible APIs.
    # --------------------------------------------------------

    metadata = (
        getattr(
            response,
            "response_metadata",
            None,
        )
        or {}
    )

    if isinstance(metadata, dict):
        raw = metadata.get("token_usage")

        if isinstance(raw, dict):
            input_tokens = raw.get(
                "prompt_tokens",
                raw.get("input_tokens"),
            )

            output_tokens = raw.get(
                "completion_tokens",
                raw.get("output_tokens"),
            )

            if (
                isinstance(input_tokens, int)
                and isinstance(output_tokens, int)
            ):
                result = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                }

                total_tokens = raw.get("total_tokens")

                if isinstance(total_tokens, int):
                    result["total_tokens"] = total_tokens

                return result

    # Token usage was not provided by the model.
    return None


# ============================================================
# ANSWER WITH AUTOMATIC PROVIDER FALLBACK
# ============================================================

async def answer_with_fallback(
    provider: Provider,
    agent: str,
    messages,
    reply_language: ReplyLanguage = "auto",
):
    """
    Retry transient failures once.

    In auto mode, move to the next configured
    provider if the current provider fails.

    Explicit provider selection does not
    automatically switch models.

    Report usage for the successful provider.
    Mark usage as incomplete if earlier
    provider attempts failed.
    """

    last_code = "not_configured"
    had_failure = False
    original_messages = messages
    messages, target_language = prepare_language(messages, reply_language=reply_language)

    timeout = min(
        120,
        max(
            5,
            float(
                os.getenv(
                    "LLM_TIMEOUT_SECONDS",
                    "75",
                )
            ),
        ),
    )

    try:
        async with asyncio.timeout(timeout):

            for candidate in provider_order(
                provider,
                agent,
            ):

                for attempt in range(2):

                    try:
                        model = get_chat_model(candidate)

                        response = await model.ainvoke(
                            messages
                        )

                        text = text_content(
                            response.content
                        ).strip()

                        if not text:
                            raise ValueError(
                                "Empty model answer"
                            )

                        if language_mismatch(public_answer(text), target_language):
                            raise ProviderUnavailable("language_mismatch")

                        # ------------------------------------
                        # TOKEN REPORTING FIX
                        #
                        # Report usage of the successful model
                        # even when earlier providers failed.
                        # ------------------------------------

                        usage = response_usage(response)

                        return MeteredAnswer(
                            text,
                            candidate,
                            usage,
                            MODEL_IDS[candidate],
                            not had_failure,
                        )

                    except asyncio.CancelledError:
                        raise

                    except Exception as exc:
                        had_failure = True

                        last_code = failure_code(
                            exc
                        )

                        log.warning(
                            "Provider %s failed: %s "
                            "(attempt %s; type=%s)",
                            candidate,
                            last_code,
                            attempt + 1,
                            type(exc).__name__,
                        )

                        if (
                            attempt == 0
                            and last_code in (
                                "language_mismatch",
                                "rate_limit",
                                "temporary_connection",
                                "timeout",
                            )
                        ):
                            if last_code == "language_mismatch":
                                messages, _ = prepare_language(
                                    original_messages, retry=True, reply_language=reply_language,
                                    draft=public_answer(text),
                                )
                            else:
                                await asyncio.sleep(2)
                            continue

                        break

    except TimeoutError:
        last_code = "timeout"

    raise ProviderUnavailable(last_code)


# ============================================================
# AVAILABLE MODELS FOR FRONTEND
# ============================================================

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
                KEYS.get(provider, "")
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
