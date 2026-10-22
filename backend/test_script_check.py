import unittest

from script_check import check_case, check_english_expected


class ScriptCheckTests(unittest.TestCase):
    def test_devanagari_in_an_english_expected_reply_fails(self):
        result = check_english_expected("Sure! नमस्ते, the price is ₹54,990.")
        self.assertEqual(result.status, "fail")
        self.assertFalse(result.passed)
        self.assertGreater(result.devanagari_chars, 0)
        self.assertIn("नमस्ते", result.sample)

    def test_english_and_symbols_pass(self):
        self.assertEqual(check_english_expected("The demo laptop costs ₹54,990. I cannot offer discounts.").status, "pass")

    def test_fixture_can_allow_legitimate_devanagari_and_is_reported_as_skipped(self):
        result = check_case(
            {"expect_language": "english", "allow_devanagari": True},
            "In Hindi, hello is नमस्ते.",
        )
        self.assertEqual(result.status, "skipped")
        self.assertTrue(result.passed)

    def test_cases_that_do_not_expect_english_are_not_checked(self):
        self.assertIsNone(check_case({"expect_language": "hindi"}, "नमस्ते"))

    def test_known_limitation_romanized_hindi_is_not_detected(self):
        # Documented limitation: this is a script check, not a language detector.
        self.assertEqual(check_english_expected("Aapko laptop chahiye? Iski price 54990 hai.").status, "pass")


if __name__ == "__main__":
    unittest.main()
