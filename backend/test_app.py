
import asyncio
import json
import os
import tempfile
import unittest

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from langchain_core.messages import HumanMessage

from llm.factory import answer_with_fallback, provider_order
from llm.router import detect_intent, route_query
from privacy import public_answer
from main import app


class AppTests(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    # ========================================================
    # 1. HEALTH AND DEMO DATA TESTS
    # ========================================================

    def test_health_and_data_integrity(self):
        health = self.client.get('/health').json()

        self.assertEqual(
            health['default_provider'],
            'auto',
        )

        self.assertEqual(
            [model['provider'] for model in health['models']],
            ['auto', 'claude', 'chatgpt', 'gemini', 'ollama'],
        )

        products = self.client.get('/products').json()

        self.assertEqual(len(products), 10)

        self.assertTrue(
            all(product['is_mock'] for product in products)
        )

        self.assertEqual(
            len(self.client.get('/tickets').json()),
            5,
        )

        self.assertEqual(
            len(self.client.get('/orders').json()),
            4,
        )

    # ========================================================
    # 2. EXISTING AGENT ROUTING TESTS
    # ========================================================

    def test_routes_and_followup(self):
        cases = [
            ('Track ORD-9001', 'sales_agent'),
            ('SR-1001 status', 'resq_agent'),
            ('AC not cooling', 'rag_agent'),
            ('manual for TV', 'rag_agent'),
            ('P001 price', 'sales_agent'),
        ]

        for message, expected_agent in cases:
            with self.subTest(message=message):
                self.assertEqual(
                    route_query(message),
                    expected_agent,
                )

        history = [
            {
                'role': 'user',
                'content': 'AC not cooling',
            }
        ]

        self.assertEqual(
            route_query('What next?', history),
            'rag_agent',
        )

    # ========================================================
    # 3. JIRA AIRM-47: INTENT DETECTION TEST
    # ========================================================

    def test_airm47_intent_routing(self):
        cases = [
            (
                'Screen has started flickering',
                'TECHNICAL_SUPPORT',
                'rag_agent',
            ),
            (
                'Status of order RD9999999',
                'ORDER_STATUS',
                'sales_agent',
            ),
            (
                'Connect me to a human',
                'HUMAN_HANDOFF',
                'resq_agent',
            ),
        ]

        for message, expected_intent, expected_agent in cases:
            with self.subTest(message=message):
                actual_intent = detect_intent(message)
                actual_agent = route_query(message)

                self.assertEqual(
                    actual_intent,
                    expected_intent,
                )

                self.assertEqual(
                    actual_agent,
                    expected_agent,
                )

    # ========================================================
    # 4. JIRA AIRM-47: API STREAM METADATA TEST
    # ========================================================

    def test_airm47_stream_metadata(self):

        async def fake_graph(data):
            return {
                'agent': route_query(data['message']),
                'system_prompt': 'Test prompt',
            }

        async def fake_answer(*args):
            return 'Test response', 'ollama'

        cases = [
            (
                'Screen has started flickering',
                'TECHNICAL_SUPPORT',
                'rag_agent',
            ),
            (
                'Status of order RD9999999',
                'ORDER_STATUS',
                'sales_agent',
            ),
            (
                'Connect me to a human',
                'HUMAN_HANDOFF',
                'resq_agent',
            ),
        ]

        with (
            patch(
                'main.GRAPH.ainvoke',
                side_effect=fake_graph,
            ),
            patch(
                'main.answer_with_fallback',
                side_effect=fake_answer,
            ),
        ):

            for message, expected_intent, expected_agent in cases:

                with self.subTest(message=message):

                    response = self.client.post(
                        '/chat/stream',
                        json={'message': message},
                    )

                    self.assertEqual(
                        response.status_code,
                        200,
                    )

                    events = []
                    event_type = None

                    for line in response.text.splitlines():

                        if line.startswith('event: '):
                            event_type = line[7:]

                        elif line.startswith('data: '):
                            data = json.loads(line[6:])
                            events.append((event_type, data))

                    meta_events = [
                        data
                        for name, data in events
                        if name == 'meta'
                    ]

                    done_events = [
                        data
                        for name, data in events
                        if name == 'done'
                    ]

                    # API should send intent and agent.
                    self.assertGreaterEqual(
                        len(meta_events),
                        1,
                    )

                    for metadata in meta_events:
                        self.assertEqual(
                            metadata.get('intent'),
                            expected_intent,
                        )

                        self.assertEqual(
                            metadata.get('agent'),
                            expected_agent,
                        )

                    # Successful completion should contain
                    # the same intent and agent.
                    self.assertTrue(
                        any(
                            event.get('ok') is True
                            and event.get('intent') == expected_intent
                            and event.get('agent') == expected_agent
                            for event in done_events
                        )
                    )

    # ========================================================
    # 5. LLM PROVIDER SELECTION TESTS
    # ========================================================

    def test_provider_order(self):

        with patch.dict(
            os.environ,
            {
                'OPENAI_API_KEY': 'test-openai',
                'ANTHROPIC_API_KEY': 'test-anthropic',
                'GOOGLE_API_KEY': 'test-google',
            },
        ):

            self.assertEqual(
                provider_order('auto', 'sales_agent'),
                ['gemini', 'chatgpt', 'claude', 'ollama'],
            )

            self.assertEqual(
                provider_order('auto', 'rag_agent'),
                ['gemini', 'chatgpt', 'claude', 'ollama'],
            )

        self.assertEqual(
            provider_order('claude', 'sales_agent'),
            ['claude', 'ollama'],
        )

    def test_missing_keys(self):

        with patch.dict(
            os.environ,
            {
                'OPENAI_API_KEY': 'your_key_here',
                'ANTHROPIC_API_KEY': '',
                'GOOGLE_API_KEY': '',
            },
        ):

            self.assertEqual(
                provider_order('auto', 'rag_agent'),
                ['ollama'],
            )

    # ========================================================
    # 6. CLOUD PROVIDER FALLBACK TESTS
    # ========================================================

    def test_cloud_failure_uses_ollama(self):

        calls = []

        class Model:

            def __init__(self, provider):
                self.provider = provider

            async def ainvoke(self, messages):
                calls.append(self.provider)

                if self.provider != 'ollama':
                    raise RuntimeError('private failure')

                return SimpleNamespace(
                    content='Safe answer'
                )

        with patch(
            'llm.factory.get_chat_model',
            side_effect=Model,
        ):

            result = asyncio.run(
                answer_with_fallback(
                    'claude',
                    'rag_agent',
                    [HumanMessage(content='test')],
                )
            )

            self.assertEqual(
                result,
                ('Safe answer', 'ollama'),
            )

        self.assertEqual(
            calls,
            ['claude', 'ollama'],
        )

    def test_all_providers_fail(self):

        with patch(
            'llm.factory.get_chat_model',
            side_effect=RuntimeError('private error'),
        ):

            with self.assertRaisesRegex(
                RuntimeError,
                'No chat provider',
            ):

                asyncio.run(
                    answer_with_fallback(
                        'chatgpt',
                        'sales_agent',
                        [],
                    )
                )

    # ========================================================
    # 7. SERVER-SENT EVENTS AND PRIVACY TESTS
    # ========================================================

    def test_sse_sanitizes_and_has_no_sources(self):

        async def answer(*args):
            return (
                'Demo price ₹129,999 [1].\n'
                'D:\\reliance-data\\private.md\n\n'
                'Sources\nprivate.md',
                'ollama',
            )

        with patch(
            'main.answer_with_fallback',
            side_effect=answer,
        ):

            response = self.client.post(
                '/chat/stream',
                json={'message': 'P001 price'},
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            '₹129,999',
            response.text,
        )

        for private in (
            'private.md',
            'reliance-data',
            'event: sources',
            '[1]',
        ):

            self.assertNotIn(
                private,
                response.text,
            )

        self.assertIn(
            '"ok": true',
            response.text,
        )

    def test_error_does_not_leak(self):

        async def fail(*args):
            raise RuntimeError(
                r'api-key secret D:\private\file.json'
            )

        with patch(
            'main.answer_with_fallback',
            side_effect=fail,
        ):

            response = self.client.post(
                '/chat/stream',
                json={'message': 'P001 price'},
            )

        self.assertIn(
            '"ok": false',
            response.text,
        )

        self.assertNotIn(
            'private',
            response.text,
        )

        self.assertNotIn(
            'secret',
            response.text,
        )

    def test_relative_paths_and_inline_sources(self):

        text = public_answer(
            'Answer.\n'
            'product_manuals/private.md\n'
            '\\\\server\\private\\manual.pdf\n'
            'Sources: hidden.pdf'
        )

        self.assertEqual(
            text,
            'Answer.',
        )

    # ========================================================
    # 8. API REQUEST VALIDATION TESTS
    # ========================================================

    def test_invalid_requests(self):

        invalid_requests = (
            {
                'message': ' ',
            },
            {
                'message': 'test',
                'provider': 'invalid-provider',
            },
            {
                'message': 'test',
                'history': [
                    {
                        'role': 'system',
                        'content': 'x',
                    }
                ],
            },
        )

        for request in invalid_requests:

            with self.subTest(request=request):

                response = self.client.post(
                    '/chat/stream',
                    json=request,
                )

                self.assertEqual(
                    response.status_code,
                    422,
                )

    # ========================================================
    # 9. RAG FALLBACK AND INDEX SAFETY TESTS
    # ========================================================

    def test_keyword_fallback(self):

        async def answer(provider, agent, messages):

            self.assertEqual(
                agent,
                'rag_agent',
            )

            self.assertIn(
                'cooling',
                messages[0].content,
            )

            self.assertNotIn(
                'SECRET_PATH',
                messages[0].content,
            )

            return 'Check cooling mode.', 'ollama'

        with (
            patch(
                'main.RAGRetriever',
                side_effect=RuntimeError('SECRET_PATH'),
            ),
            patch(
                'main.answer_with_fallback',
                side_effect=answer,
            ),
        ):

            response = self.client.post(
                '/chat/stream',
                json={'message': 'AC not cooling'},
            )

        self.assertIn(
            '"retrieval_mode": "keyword"',
            response.text,
        )

        self.assertIn(
            '"ok": true',
            response.text,
        )

    def test_failed_rebuild_preserves_active_index(self):

        from rag.rebuild import rebuild

        with tempfile.TemporaryDirectory() as folder:

            pointer = (
                Path(folder) / 'active_collection.txt'
            )

            pointer.write_text(
                'previous_verified_collection',
                encoding='utf-8',
            )

            with (
                patch(
                    'rag.rebuild.CHROMA_PATH',
                    Path(folder),
                ),
                patch(
                    'rag.rebuild.RAGIngestor',
                    side_effect=RuntimeError('provider failed'),
                ),
            ):

                with self.assertRaises(RuntimeError):
                    rebuild()

            self.assertEqual(
                pointer.read_text(
                    encoding='utf-8'
                ),
                'previous_verified_collection',
            )


if __name__ == '__main__':
    unittest.main(verbosity=2)
