import asyncio
import sys
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm.factory import answer_with_fallback, provider_order, ProviderUnavailable, MeteredAnswer, response_usage


class ReliabilityTests(unittest.TestCase):
    def test_usage_preserves_provider_counts(self):
        usage = {'prompt_tokens': 123, 'completion_tokens': 17, 'total_tokens': 140}
        response = SimpleNamespace(response_metadata={'token_usage': usage})
        result = MeteredAnswer('answer', 'gemini', response_usage(response), 'test-model')
        self.assertEqual(tuple(result), ('answer', 'gemini'))
        self.assertEqual(result.usage, {
            'input_tokens': 123,
            'output_tokens': 17,
            'total_tokens': 140,
        })
        self.assertTrue(result.usage_complete)

    def test_missing_usage_is_not_fabricated(self):
        self.assertIsNone(response_usage(SimpleNamespace(response_metadata={})))

    def test_explicit_provider_does_not_fallback(self):
        self.assertEqual(provider_order('gemini', 'sales_agent'), ['gemini'])

    def test_transient_retry_succeeds(self):
        model = SimpleNamespace(ainvoke=AsyncMock(side_effect=[ConnectionError('private'), SimpleNamespace(content='answer')]))
        with patch('llm.factory.get_chat_model', return_value=model), patch('llm.factory.asyncio.sleep', new_callable=AsyncMock):
            self.assertEqual(asyncio.run(answer_with_fallback('gemini', 'sales_agent', [])), ('answer', 'gemini'))
        self.assertEqual(model.ainvoke.await_count, 2)

    def test_auth_failure_not_retried_or_exposed(self):
        class AuthenticationError(Exception):
            status_code = 401
        model = SimpleNamespace(ainvoke=AsyncMock(side_effect=AuthenticationError('secret-value')))
        with patch('llm.factory.get_chat_model', return_value=model):
            with self.assertRaises(ProviderUnavailable) as failure:
                asyncio.run(answer_with_fallback('gemini', 'sales_agent', []))
        self.assertEqual(failure.exception.code, 'authentication')
        self.assertNotIn('secret-value', str(failure.exception))
        self.assertEqual(model.ainvoke.await_count, 1)

    def test_empty_answer_is_not_success(self):
        with patch('llm.factory.get_chat_model', return_value=SimpleNamespace(ainvoke=AsyncMock(return_value=SimpleNamespace(content='')))):
            with self.assertRaises(ProviderUnavailable):
                asyncio.run(answer_with_fallback('gemini', 'sales_agent', []))


if __name__ == '__main__':
    unittest.main()
