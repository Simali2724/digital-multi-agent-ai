"""Limited keyword retrieval when cloud embeddings are unavailable; no fake vectors."""
import re
from config import DATA_ROOT

def search_local(query: str, k: int = 5) -> str:
    terms = set(re.findall(r'[a-z0-9]+', query.lower())) - {'the', 'what', 'is', 'of', 'to', 'a', 'and', 'in', 'my', 'how'}
    results = []
    for folder in ('product_manuals', 'warranty_policies', 'faqs', 'troubleshooting', 'service_guides'):
        for path in sorted((DATA_ROOT / folder).rglob('*')):
            if path.suffix.lower() not in ('.md', '.txt'):
                continue
            for chunk in re.split(r'\n(?=##? )', path.read_text(encoding='utf-8')):
                words = set(re.findall(r'[a-z0-9]+', chunk.lower()))
                matches = terms & words
                score = len(matches) + 5 * sum(bool(re.fullmatch(r'p\d{3}', w)) for w in matches)
                if score >= min(2, len(terms)) and matches:
                    results.append((score, chunk[:1600]))
    return '\n\n'.join(c for _, c in sorted(results, key=lambda x: x[0], reverse=True)[:k]) or 'No relevant information is available.'
