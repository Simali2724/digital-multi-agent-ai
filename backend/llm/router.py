
"""Local intent detection and agent routing without a paid classifier."""

import re


# ============================================================
# INTENT DETECTION - JIRA AIRM-47
# ============================================================

def detect_intent(message: str) -> str:
    query = message.lower().strip()

    # 1. Human handoff
    if re.search(
        r'\b(human|representative|real person|live agent|customer care)\b',
        query,
    ) or any(phrase in query for phrase in (
        'customer support',
        'speak to an agent',
        'talk to an agent',
        'connect me to an agent',
    )):
        return 'HUMAN_HANDOFF'

    # 2. Order status
    if re.search(r'\b(?:rd\d+|ord-\d+)\b', query):
        return 'ORDER_STATUS'

    if (
        re.search(r'\border\b', query)
        and re.search(
            r'\b(status|track|tracking|where|delivery)\b',
            query,
        )
    ):
        return 'ORDER_STATUS'

    # 3. Technical support
    if any(keyword in query for keyword in (
        'flicker',
        'not cooling',
        'not working',
        'troubleshoot',
        'error code',
        'screen issue',
        'display issue',
        'technical problem',
        'nahi chal',
        'thanda nahi',
    )):
        return 'TECHNICAL_SUPPORT'

    # 4. General questions
    return 'GENERAL_QUERY'


# ============================================================
# AGENT ROUTING
# ============================================================

def route_query(
    message: str,
    history: list[dict] | None = None,
) -> str:

    query = message.lower()

    intent = detect_intent(message)

    # --------------------------------------------------------
    # Human support -> resQ Agent
    # --------------------------------------------------------

    if intent == 'HUMAN_HANDOFF':
        return 'resq_agent'

    # --------------------------------------------------------
    # Order status -> Sales Agent
    # --------------------------------------------------------

    if intent == 'ORDER_STATUS':
        return 'sales_agent'

    # --------------------------------------------------------
    # Technical support -> Knowledge/RAG Agent
    # --------------------------------------------------------

    if intent == 'TECHNICAL_SUPPORT':
        return 'rag_agent'

    # --------------------------------------------------------
    # Service ticket tracking
    # --------------------------------------------------------

    if re.search(r'\b(?:sr|resq)-\d+\b', query):
        return 'resq_agent'

    # --------------------------------------------------------
    # Knowledge base and troubleshooting
    # --------------------------------------------------------

    if any(x in query for x in (
        'manual',
        'policy',
        'policies',
        'knowledge base',
        'according to',
        'troubleshoot',
        'how to',
        'guide',
    )):
        return 'rag_agent'

    # --------------------------------------------------------
    # Service and repair
    # --------------------------------------------------------

    if any(x in query for x in (
        'ticket',
        'technician',
        'repair',
        'service',
        'warranty claim',
        'resq',
    )):
        return 'resq_agent'

    # --------------------------------------------------------
    # Sales and product queries
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Short follow-up questions
    # --------------------------------------------------------

    if history and len(query.split()) <= 12:
        for item in reversed(history):
            if item.get('role') == 'user':
                return route_query(item['content'])

    # --------------------------------------------------------
    # Default agent
    # --------------------------------------------------------

    return 'sales_agent'
