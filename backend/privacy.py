
"""Sanitize a complete answer before it crosses the SSE boundary."""

import os
import re


def public_answer(text: str) -> str:
    # --------------------------------------------------------
    # 1. Remove internal AI reasoning from Gemma and
    #    other models using think/thought tags.
    # --------------------------------------------------------

    text = re.sub(
        r"(?is)<\s*(?:thought|think)\b[^>]*>.*?"
        r"<\s*/\s*(?:thought|think)\s*>",
        "",
        text,
    )

    # Remove incomplete reasoning blocks as well.
    # Never expose unfinished internal reasoning.
    text = re.sub(
        r"(?is)<\s*(?:thought|think)\b[^>]*>.*\Z",
        "",
        text,
    )

    # --------------------------------------------------------
    # 2. Hide API keys
    # --------------------------------------------------------

    for name in (
        "GOOGLE_API_KEY",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "MOONSHOT_API_KEY",
    ):
        value = os.getenv(name, "")

        if len(value) > 8:
            text = text.replace(value, "[redacted]")

    # --------------------------------------------------------
    # 3. Remove source/reference sections
    # --------------------------------------------------------

    text = re.sub(
        r"(?im)^\s{0,3}(?:#{1,6}\s*)?"
        r"(?:\*\*)?"
        r"(?:sources|references|citations)"
        r"(?:\s*:[^\n]*|\s*(?:\*\*)?\s*$)"
        r"[\s\S]*",
        "",
        text,
    )

    # Remove numeric citation markers.
    text = re.sub(
        r"\[[\d,\s-]+\]",
        "",
        text,
    )

    # --------------------------------------------------------
    # 4. Remove private filenames and paths
    # --------------------------------------------------------

    private_pattern = (
        r"(?i)(?:"
        r"[a-z]:[\\/]"
        r"|\\\\[\w.-]+\\"
        r"|file://"
        r"|/(?:home|users|tmp|var|mnt)/"
        r"|(?:product_manuals|warranty_policies|"
        r"service_guides|troubleshooting|faqs)[\\/]"
        r"|chroma_db"
        r"|reliance-data"
        r"|chat-upload:"
        r")"
    )

    lines = [
        line
        for line in text.splitlines()
        if not re.search(private_pattern, line)
    ]

    text = "\n".join(lines)

    # --------------------------------------------------------
    # 5. Hide internal document filenames
    # --------------------------------------------------------

    text = re.sub(
        r"(?i)\b[\w.-]+\."
        r"(?:md|txt|pdf|json|sqlite3|py)\b",
        "reference material",
        text,
    )

    # --------------------------------------------------------
    # 6. Return safe customer-facing answer
    # --------------------------------------------------------

    return (
        text.strip()
        or "I could not prepare a suitable answer. "
           "Please rephrase your question."
    )
