"""Sanitize a complete answer before it crosses the SSE boundary."""
import os
import re

def public_answer(text: str) -> str:
    for name in ('GOOGLE_API_KEY', 'ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'MOONSHOT_API_KEY'):
        value = os.getenv(name, '')
        if len(value) > 8:
            text = text.replace(value, '[redacted]')
    text = re.sub(r'(?im)^\s{0,3}(?:#{1,6}\s*)?(?:\*\*)?(?:sources|references|citations)(?:\s*:[^\n]*|\s*(?:\*\*)?\s*$)[\s\S]*', '', text)
    text = re.sub(r'\[[\d,\s-]+\]', '', text)
    lines = [line for line in text.splitlines() if not re.search(r'(?i)(?:[a-z]:[\\/]|\\\\[\w.-]+\\|file://|/(?:home|users|tmp|var|mnt)/|(?:product_manuals|warranty_policies|service_guides|troubleshooting|faqs)[\\/]|chroma_db|reliance-data|chat-upload:)', line)]
    text = '\n'.join(lines)
    text = re.sub(r'(?i)\b[\w.-]+\.(?:md|txt|pdf|json|sqlite3|py)\b', 'reference material', text)
    return text.strip() or 'I could not prepare a suitable answer. Please rephrase your question.'
