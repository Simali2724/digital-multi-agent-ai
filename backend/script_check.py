"""Exact script check for replies that are expected to be English.

This is a targeted regression check, NOT a language detector and NOT a judge of correctness:

* It only looks for Devanagari characters (U+0900-U+097F). Romanized Hindi ("aapko kya chahiye"), Hinglish and
  other scripts pass it. llm.language.romanized_hindi() is a separate heuristic with its own limits.
* A reply can pass it and still be wrong, unsafe or off-topic, so its result is reported separately from
  factual or behavioral checks (see eval_live.py).
* Legitimate Devanagari (a quoted product label, or a customer who asked for a Hindi translation) is declared
  per fixture with `allow_devanagari: true`; such cases are reported as "skipped by fixture", not "passed".
"""

import re
from dataclasses import dataclass

DEVANAGARI = re.compile(r"[ऀ-ॿ]")


@dataclass(frozen=True)
class ScriptCheck:
    status: str  # pass | fail | skipped
    devanagari_chars: int
    sample: str = ""

    @property
    def passed(self) -> bool:
        return self.status != "fail"


def check_english_expected(reply: str, allow_devanagari: bool = False) -> ScriptCheck:
    matches = DEVANAGARI.findall(reply)
    if allow_devanagari:
        return ScriptCheck("skipped", len(matches))
    if not matches:
        return ScriptCheck("pass", 0)
    start = DEVANAGARI.search(reply).start()
    return ScriptCheck("fail", len(matches), reply[max(0, start - 20):start + 40])


def check_case(case: dict, reply: str) -> ScriptCheck | None:
    """Apply the check to a fixture. Returns None for cases that do not expect English."""
    if case.get("expect_language", "english") != "english":
        return None
    return check_english_expected(reply, bool(case.get("allow_devanagari", False)))
