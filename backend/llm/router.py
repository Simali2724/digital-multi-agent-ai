
"""Local routing without a paid classifier request."""

import re


def route_query(message: str, history: list[dict] | None = None) -> str:
    query = message.lower()

    # Human support requests
    if any(x in query for x in (
        'human',
        'real person',
        'customer care',
        'customer support',
        'representative',
        'speak to an agent',
        'talk to an agent',
    )):
        return 'resq_agent'

    # Order tracking
    if re.search(r'\bord-\d+\b', query):
        return 'sales_agent'

    # Service ticket tracking
    if re.search(r'\b(?:sr|resq)-\d+\b', query):
        return 'resq_agent'

    # Knowledge base and troubleshooting
    if any(x in query for x in (
        'manual',
        'policy',
        'policies',
        'knowledge base',
        'according to',
        'troubleshoot',
        'how to',
        'not cooling',
        'flicker',
        'not working',
        'nahi chal',
        'thanda nahi',
        'error code',
        'guide',
    )):
        return 'rag_agent'

    # Service and repair
    if any(x in query for x in (
        'ticket',
        'technician',
        'repair',
        'service',
        'warranty claim',
        'resq',
    )):
        return 'resq_agent'

    # Sales and product queries
    if (
        any(x in query for x in (
            'price',
            'buy',
            'compare',
            'order',
            'product',
            'warranty',
            'cost',
            'recommend',
            'budget',
        ))
        or re.search(r'\bp\d{3}\b', query)
    ):
        return 'sales_agent'

    # Short follow-up questions
    if history and len(query.split()) <= 12:
        for item in reversed(history):
            if item.get('role') == 'user':
                return route_query(item['content'])

    return 'sales_agent'
