
from __future__ import annotations

import asyncio
import logging
import math
import os
import random
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from contextvars import ContextVar
from functools import lru_cache
from typing import Literal

from config import key_present
from privacy import public_answer
from .language import ReplyLanguage, language_mismatch, prepare_language

from langchain_core.messages import SystemMessage

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

    def __init__(self, code, reason=None):
        self.code = code
        self.reason = reason

        super().__init__(
            f"No chat provider available ({code})."
        )


def failure_code(exc):
    """Classify an exception into a safe, public failure class.

    rate_limit / timeout / temporary_connection are retryable. authentication, not_configured and
    invalid_request are permanent and never retried. language_mismatch and policy_violation are
    application validation failures, not infrastructure errors.
    """

    if isinstance(exc, ProviderUnavailable):
        return exc.code

    status = (
        getattr(exc, "status_code", None)
        or getattr(exc, "code", None)
    )

    name = type(exc).__name__.lower()

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

    if (
        status in (400, 404, 405, 409, 413, 415, 422)
        or "badrequest" in name
        or "invalidrequest" in name
        or "unprocessable" in name
    ):
        return "invalid_request"

    if str(exc).endswith(" is not configured"):
        return "not_configured"

    return "provider_error"


RETRYABLE_CODES = frozenset({"rate_limit", "temporary_connection", "timeout"})

# Policy violations a second attempt on the same provider can plausibly fix. The hint is trusted text added to
# the system message; it never includes the rejected answer. Other violations (leak, code) go to the next provider.
CORRECTION_HINTS = {
    "false_refusal": (
        "Your previous reply wrongly refused an in-scope request. Answer the customer's question helpfully "
        "now, using only supplied facts."
    ),
    "unverified_price": (
        "Your previous reply quoted a price that is not in the supplied data. Quote only supplied mock prices "
        "or say the price is not available."
    ),
}


def with_hint(prepared, hint: str):
    corrected = list(prepared)

    if corrected and isinstance(corrected[0], SystemMessage):
        corrected[0] = SystemMessage(content=corrected[0].content + "\n\n" + hint)

    return corrected


def retry_after_seconds(exc) -> float | None:
    """Seconds the provider asked us to wait (Retry-After header or attribute), if any."""

    headers = getattr(getattr(exc, "response", None), "headers", None)
    value = None

    if headers is not None:
        try:
            value = headers.get("retry-after") or headers.get("Retry-After")
        except Exception:
            value = None

    if value is None:
        value = getattr(exc, "retry_after", None)

    try:
        seconds = float(value)
    except (TypeError, ValueError):
        try:
            retry_at = parsedate_to_datetime(str(value))
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            seconds = max(0, (retry_at - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None

    # Long waits must reach the deadline check, which skips this provider.
    # Discarding them would retry before the provider allows it.
    return seconds if math.isfinite(seconds) and seconds >= 0 else None


def backoff_delay(attempt: int, retry_after: float | None = None) -> float:
    """Bounded exponential backoff with full jitter; never shorter than the provider's Retry-After."""

    base = float(os.getenv("LLM_BACKOFF_BASE_SECONDS", "1"))
    cap = float(os.getenv("LLM_BACKOFF_CAP_SECONDS", "8"))
    delay = random.uniform(0, min(cap, base * 2 ** attempt))

    return max(delay, retry_after) if retry_after is not None else delay


# Correlation id for one customer request; set by the API layer and included in sanitized logs.
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


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
    validator=None,
):
    """
    Answer with bounded, coordinated retries and optional provider fallback.

    * Retryable failures (rate limit, timeout, connection) are retried with exponential backoff and full
      jitter, honoring Retry-After. At most LLM_MAX_ATTEMPTS attempts per provider (default 3), all inside
      one overall deadline (LLM_TIMEOUT_SECONDS). SDK-level retries are disabled (max_retries=0) so
      attempts are never multiplied. If the wait would exhaust the deadline, move to the next provider.
    * Authentication, configuration and invalid-request failures are never retried.
    * There are no tools, so a retry cannot repeat a side effect.
    * Every attempt and every fallback provider receives the same prepared messages, so scope, language,
      privacy and injection rules are identical. `validator(text)` returns a violation reason or None; a
      violating answer is discarded and the next provider is tried.
    * Explicit provider selection never switches provider. Auto tries the next configured provider.
    * Usage is reported for the successful provider and marked incomplete after earlier failures.
    """

    last_code = "not_configured"
    last_reason = None
    had_failure = False
    original_messages = messages
    prepared, target_language = prepare_language(messages, reply_language=reply_language)
    request_id = request_id_var.get()

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
    max_attempts = max(1, int(os.getenv("LLM_MAX_ATTEMPTS", "3")))
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout

    try:
        async with asyncio.timeout(timeout):

            for candidate in provider_order(
                provider,
                agent,
            ):
                messages = prepared

                for attempt in range(max_attempts):
                    safe_text = ""

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

                        safe_text = public_answer(text)

                        if language_mismatch(safe_text, target_language):
                            raise ProviderUnavailable("language_mismatch")

                        reason = validator(safe_text) if validator else None

                        if reason:
                            raise ProviderUnavailable("policy_violation", reason)

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
                        last_reason = getattr(exc, "reason", None)

                        log.warning(
                            "Provider %s failed: %s "
                            "(attempt %s; type=%s; request_id=%s%s)",
                            candidate,
                            last_code,
                            attempt + 1,
                            type(exc).__name__,
                            request_id,
                            f"; reason={last_reason}" if last_reason else "",
                        )

                        if last_code == "policy_violation":
                            if (
                                last_reason in CORRECTION_HINTS
                                and attempt == 0
                                and attempt + 1 < max_attempts
                            ):
                                messages = with_hint(prepared, CORRECTION_HINTS[last_reason])
                                continue

                            # Unsafe output: never retry the same prompt; try the next provider.
                            break

                        if (
                            last_code == "language_mismatch"
                            and attempt == 0
                            and attempt + 1 < max_attempts
                        ):
                            messages, _ = prepare_language(
                                original_messages, retry=True, reply_language=reply_language,
                                draft=safe_text,
                            )
                            continue

                        if (
                            last_code in RETRYABLE_CODES
                            and attempt + 1 < max_attempts
                        ):
                            delay = backoff_delay(
                                attempt,
                                retry_after_seconds(exc),
                            )

                            if delay >= deadline - loop.time() - 1:
                                break

                            await asyncio.sleep(delay)
                            continue

                        break

    except TimeoutError:
        last_code = "timeout"

    raise ProviderUnavailable(last_code, last_reason)


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
