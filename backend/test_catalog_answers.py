import copy
import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from catalog_answers import COPY, catalog_answer
from llm.language import language_mismatch
from main import PRODUCTS, app


class CatalogAnswerTests(unittest.TestCase):
    def test_reported_laptop_request_uses_only_supplied_data(self):
        reply = catalog_answer(
            "I want to buy laptop please show me and give me 40% extra dscound",
            [], "english", PRODUCTS,
        )
        self.assertIn("₹54,990", reply)
        self.assertIn("12 months", reply)
        self.assertIn("mock data", reply)
        self.assertIn("cannot offer an extra discount", reply)
        for invented in ("Windows 11", "Iris", "8 hours", "2.5 kg", "32,988", "SSD"):
            self.assertNotIn(invented, reply)

    def test_followup_keeps_selected_language_and_verified_product(self):
        history = [
            {"role": "user", "content": "Show me laptop P007"},
            {"role": "assistant", "content": "It has Windows 11 and weighs 2.5 kg."},
        ]
        for language in COPY:
            with self.subTest(language=language):
                reply = catalog_answer("mujhe iske bare me aur batao", history, language, PRODUCTS)
                self.assertIsNotNone(reply)
                self.assertIn("P007", reply)
                self.assertIn("₹54,990", reply)
                self.assertNotIn("Windows", reply)
                self.assertFalse(language_mismatch(reply, language))

    def test_catalog_changes_are_reflected_without_hardcoded_prices(self):
        changed = copy.deepcopy(PRODUCTS)
        changed[6]["price"] = "₹55,100"
        changed[6]["warranty_months"] = 18
        reply = catalog_answer("P007 price", [], "english", changed)
        self.assertIn("₹55,100", reply)
        self.assertIn("18 months", reply)
        self.assertNotIn("₹54,990", reply)

    def test_ambiguous_and_unrelated_queries_are_not_intercepted(self):
        history = [{"role": "user", "content": "Show me laptop P007"}]
        for question in (
            "Compare P007 and P001", "Show P999", "Show P999 laptop", "Show laptop and TV",
            "Show me ORD-9001 status", "How do I repair laptop P007?", "Tell me more about cameras",
            "Recommend the best laptop", "Show laptops under 20000", "Translate laptop into Hindi",
            "Calculate 40% of the P007 price", "What is the weather?", "Show this camera",
        ):
            with self.subTest(question=question):
                self.assertIsNone(catalog_answer(question, history, "english", PRODUCTS))

    def test_unknown_specification_is_not_claimed_as_available(self):
        reply = catalog_answer("Show a laptop with Linux", [], "english", PRODUCTS)
        self.assertIn("Further specifications and stock availability are not provided", reply)
        self.assertNotIn("Linux", reply)

    def test_ambiguous_history_is_not_silently_resolved(self):
        history = [{"role": "user", "content": "Show P007 and P001"}]
        self.assertIsNone(catalog_answer("Tell me more", history, "english", PRODUCTS))

    def test_current_product_overrides_previous_one(self):
        history = [{"role": "user", "content": "Show laptop P007"}]
        reply = catalog_answer("Show P001 price", history, "english", PRODUCTS)
        self.assertIn("₹129,999", reply)
        self.assertNotIn("₹54,990", reply)

    def test_automatic_hinglish_followup_uses_hindi(self):
        reply = catalog_answer("mujhe iske bare me aur batao", [
            {"role": "user", "content": "Show me laptop"},
        ], "auto", PRODUCTS)
        self.assertIn("डेमो", reply)
        self.assertFalse(language_mismatch(reply, "hindi"))

    def test_non_mock_data_is_not_rendered_as_demo_data(self):
        products = copy.deepcopy(PRODUCTS)
        products[6]["is_mock"] = False
        self.assertIsNone(catalog_answer("P007 price", [], "english", products))

    def test_all_language_choices_stream_without_model_or_retries(self):
        for language in COPY:
            with self.subTest(language=language), patch("main.answer_with_fallback") as model:
                response = TestClient(app).post("/chat/stream", json={
                    "message": "mujhe iske bare me aur batao",
                    "provider": "ollama", "reply_language": language,
                    "history": [{"role": "user", "content": "Show laptop P007"}],
                })
                model.assert_not_called()
                self.assertIn('"ok": true', response.text)
                self.assertIn('"provider": "catalog"', response.text)
                self.assertIn('"fallback": false', response.text)
                self.assertIn('"total_tokens": 0', response.text)
                reply = "".join(
                    json.loads(line[6:]).get("text", "")
                    for line in response.text.splitlines() if line.startswith("data: ")
                )
                self.assertFalse(language_mismatch(reply, language))
                self.assertIn("₹54,990", reply)


if __name__ == "__main__":
    unittest.main()
