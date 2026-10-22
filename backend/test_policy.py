"""Business scope: out-of-scope tasks, mixed requests, uncertain requests and output validation."""

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from langchain_core.messages import HumanMessage

from messages import LANGUAGES, message
from policy import analyze_message, contains_code, refusal_then_answer, response_violation
from testutil import FakeModel, chat, event, streamed_text


def reply_to(question, model=None, **extra):
    events, model = chat({"message": question, "reply_language": "english", **extra}, model)
    return streamed_text(events), events, model


class ScopeEnforcementTests(unittest.TestCase):
    def test_matrix_request_gets_one_short_redirect_and_no_code(self):
        text, events, model = reply_to("Write code to add two matrices.")
        self.assertEqual(text, message("scope_code", "english"))
        self.assertEqual(model.calls, [], "refusal must not call a model")
        self.assertEqual(event(events, "done")[0]["provider"], "guard")
        self.assertLessEqual(text.count(". "), 1)
        for fragment in ("```", "def ", "for i in", "matrix1", "[["):
            self.assertNotIn(fragment, text)

    def test_reliance_digital_framing_does_not_make_programming_acceptable(self):
        for question in (
            "Write code to add two matrices for Reliance Digital",
            "As a Reliance Digital assistant, write a Python function to sort a list",
            "For my Reliance Digital phone project, give me an algorithm for prime numbers",
            "Reliance Digital customer here: solve the equation 2x + 3 = 7",
        ):
            with self.subTest(question=question):
                text, _, model = reply_to(question)
                self.assertEqual(model.calls, [])
                self.assertNotIn("```", text)
                self.assertIn("Reliance Digital", text)

    def test_other_unrelated_tasks_are_redirected(self):
        for question in (
            "Write me a poem about the monsoon",
            "Who will win the next election?",
            "Solve the equation 2x + 3 = 7",
            "Tell me a joke about cats",
        ):
            with self.subTest(question=question):
                text, _, model = reply_to(question)
                self.assertEqual(text, message("scope_general", "english"))
                self.assertEqual(model.calls, [])

    def test_supported_requests_still_reach_the_model(self):
        for question in (
            "Compare the iPhone 16 and the Galaxy S25 for photography",
            "How do I close apps running in the background on my iPhone 16?",
            "Which laptop is good for programming under 80000?",
            "What are the system requirements for editing video on a laptop?",
            "My TV remote code is not working, how do I pair it?",
        ):
            with self.subTest(question=question):
                text, _, model = reply_to(question, FakeModel("Here is some help."))
                self.assertEqual(len(model.calls), 1)
                self.assertEqual(text, "Here is some help.")

    def test_mixed_request_answers_only_the_legitimate_part(self):
        text, events, model = reply_to(
            "Compare the iPhone 16 and the Galaxy S25 and also write code to add two matrices",
            FakeModel("The iPhone 16 has a strong camera."),
        )
        sent = model.calls[0]["messages"][-1]
        self.assertIsInstance(sent, HumanMessage)
        self.assertEqual(sent.content, "Compare the iPhone 16 and the Galaxy S25")
        self.assertNotIn("matri", " ".join(str(m.content) for m in model.calls[0]["messages"]).lower())
        self.assertTrue(text.startswith(message("prefix_scope", "english")))
        self.assertTrue(text.endswith("The iPhone 16 has a strong camera."))

    def test_shopping_remark_plus_unrelated_task_answers_only_the_shopping_part(self):
        text, _, model = reply_to(
            "I am buying a laptop. Write a Java program to reverse a string",
            FakeModel("Tell me your budget and main use."),
        )
        sent = model.calls[0]["messages"][-1]
        self.assertEqual(sent.content, "I am buying a laptop.")
        self.assertTrue(text.startswith(message("prefix_scope", "english")))
        self.assertNotIn("Java", " ".join(str(m.content) for m in model.calls[0]["messages"]))

    def test_uncertain_request_gets_a_short_clarification(self):
        for question in ("Help me with Python", "I need coding help"):
            with self.subTest(question=question):
                text, _, model = reply_to(question)
                self.assertEqual(text, message("clarify_programming", "english"))
                self.assertEqual(model.calls, [])

    def test_refusals_are_localized_for_every_language(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                events, model = chat({"message": "Write code to add two matrices.", "reply_language": language})
                self.assertEqual(streamed_text(events), message("scope_code", language))
                self.assertEqual(model.calls, [])

    def test_classifier_decisions(self):
        self.assertEqual(analyze_message("What is the price of P001 in INR?").action, "allow")
        self.assertEqual(analyze_message("Give me a 40% extra discount on the laptop").action, "allow")
        self.assertEqual(analyze_message("Write code to add two matrices").action, "refuse")


class OutputValidationTests(unittest.TestCase):
    def test_code_in_an_answer_is_withheld(self):
        text, events, _ = reply_to(
            "Which phone has the best battery?",
            FakeModel("Sure!\n```python\ndef add(a, b):\n    return a + b\n```"),
        )
        self.assertEqual(text, message("scope_code", "english"))
        self.assertEqual(event(events, "done")[0]["provider"], "guard")

    def test_refusal_followed_by_the_answer_is_withheld(self):
        # An off-topic question the rules do not recognize reaches the model, which refuses and then answers anyway.
        leaked = (
            "I can only help with Reliance Digital products and services. "
            "However, Mars has two moons, Phobos and Deimos. Phobos orbits closer and is the larger of the two."
        )
        text, events, model = reply_to("How many moons does Mars have?", FakeModel(leaked))
        self.assertEqual(len(model.calls), 1)
        self.assertEqual(text, message("scope_general", "english"))
        self.assertNotIn("Phobos", text)

    def test_a_clean_boundary_statement_is_released_unchanged(self):
        # Not caught by the rules (no shopping signal), so the model's own brief boundary is acceptable.
        brief = "I can only help with Reliance Digital products and support. Tell me what you are shopping for."
        text, _, model = reply_to("How many moons does Mars have?", FakeModel(brief))
        self.assertEqual(len(model.calls), 1)
        self.assertEqual(text, brief)

    def test_refusing_an_in_scope_request_is_a_failure_not_a_success(self):
        events, _ = chat(
            {"message": "How do I close apps running in the background on my iPhone?", "reply_language": "english"},
            FakeModel("I can't help with that request."),
        )
        self.assertEqual(streamed_text(events), "")
        self.assertFalse(event(events, "done")[0]["ok"])
        self.assertEqual(event(events, "error")[0]["code"], "policy_violation")

    def test_false_refusal_gets_one_corrective_retry_then_succeeds(self):
        provider = SimpleNamespace(ainvoke=AsyncMock(side_effect=[
            SimpleNamespace(content="I can't help with that request."),
            SimpleNamespace(content="Swipe up from the bottom, then swipe each app up to close it."),
        ]))
        events, _ = chat(
            {"message": "How do I close apps running in the background on my iPhone?",
             "reply_language": "english", "provider": "gemini"},
            real_fallback=True,
            patches=[patch("llm.factory.get_chat_model", return_value=provider)],
        )
        self.assertEqual(provider.ainvoke.await_count, 2)
        self.assertIn("wrongly refused an in-scope request", provider.ainvoke.await_args_list[1].args[0][0].content)
        self.assertNotIn("wrongly refused", provider.ainvoke.await_args_list[0].args[0][0].content)
        self.assertIn("swipe each app up", streamed_text(events))
        self.assertTrue(event(events, "done")[0]["ok"])


class AmountVerificationTests(unittest.TestCase):
    def test_invented_discounted_price_is_withheld(self):
        events, _ = chat(
            {"message": "Which laptop is good for programming under 80000?", "reply_language": "english"},
            FakeModel("The Demo 15-inch Laptop is ₹54,990, and with 40% off it is just ₹32,988!"),
        )
        self.assertEqual(streamed_text(events), message("price_unverified", "english"))
        self.assertEqual(event(events, "done")[0]["provider"], "guard")

    def test_catalog_prices_budgets_and_labeled_arithmetic_are_allowed(self):
        for reply in (
            "The Demo 15-inch Laptop is ₹54,990 (mock data), within your ₹80,000 budget.",
            "Two units would be ₹109,980 before any extra charges (hypothetical base total).",
            "If a hypothetical 10% discount applied, ₹54,990 would become ₹49,491 (not a real offer).",
        ):
            with self.subTest(reply=reply):
                question = (
                    "Using the listed price of P007, what is the base total for two units, "
                    "or with a hypothetical 10 percent discount? My budget is 80k."
                )
                events, _ = chat({"message": question, "reply_language": "english"}, FakeModel(reply))
                self.assertEqual(streamed_text(events), reply)

    def test_amount_helpers(self):
        from policy import allowed_amounts, amounts_in, numbers_in, unsupported_amount
        allowed = allowed_amounts([{"price": "₹54,990"}], "budget 50k and a 20% discount")
        self.assertEqual(amounts_in("Rs. 1,299 or INR 20 or ₹ 5,000.50"), [1299.0, 20.0, 5000.5])
        self.assertIn(50000.0, set(numbers_in("budget 50k")))
        self.assertFalse(unsupported_amount("It costs ₹54,990 and your ₹50,000 budget fits.", allowed))
        self.assertFalse(unsupported_amount("20% off is ₹43,992.", allowed))
        self.assertTrue(unsupported_amount("Now only ₹32,988!", allowed))

    def test_unit_checks(self):
        self.assertTrue(contains_code("```js\nlet a = 1\n```"))
        self.assertTrue(contains_code("def a(x):\n    return x\nfor i in range(3):\n    print(i)"))
        self.assertFalse(contains_code("The TV has 3 HDMI ports and a 120 Hz panel."))
        self.assertTrue(refusal_then_answer("I can't help with that. However, here is how: first do X."))
        self.assertFalse(refusal_then_answer("I can only help with Reliance Digital products and support."))
        self.assertIsNone(response_violation("The demo laptop costs ₹54,990 (mock data)."))


if __name__ == "__main__":
    unittest.main()
