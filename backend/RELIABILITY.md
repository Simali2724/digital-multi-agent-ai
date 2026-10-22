# Reliability corrections — 2026-10-13

## Grounded catalog replies (2026-10-22)

Straightforward requests about one identifiable mock catalog product now use `catalog_answers.py` to render the stored name, price and warranty with localized labels in all seven supported languages. Replies explicitly identify mock data, say further specifications and stock availability are unknown, and decline discounts and checkout. They do not infer an OS, GPU, battery life, weight or storage technology from product names or prior assistant claims.

The reported laptop/40%-discount request and `mujhe iske bare me aur batao` follow-up use this path when a single product can be resolved. Follow-ups resolve only from customer history, and ambiguous/unknown IDs are not guessed. Comparisons, troubleshooting, order tracking, recommendations, budget filters and unsupported requests retain the model path. This is intentionally a narrow catalog formatter, not a general grounding guarantee for all LLM answers. Native-language wording has not had a human linguistic review.

SSE metadata truthfully reports `provider: catalog`, `model: null`, zero model tokens and `fallback: false`; the UI labels this `Demo catalog`. An explicit model selection still applies to requests requiring model generation. Provider/language tests disable this shortcut to exercise the LLM path; `test_catalog_answers` separately verifies the real catalog/SSE path without a model.

Full backend verification: `.\.venv\Scripts\python.exe -m unittest test_catalog_answers test_language test_app test_reliability` from `backend`.

Verification after the catalog addition: 45 backend tests, TypeScript and changed-file ESLint checks passed. The restarted backend served the reported laptop follow-up successfully in all seven selected languages via live HTTP/SSE, with the catalog price ₹54,990 and zero model tokens. Frontend HTTP returned 200 with the language selector present. Detailed transfer notes are in `AI_HANDOVER.md` at the repository root.

## Reply language (2026-10-22)

Follow-up correction: selected languages no longer compete with a base instruction to match the input language. A mismatch now triggers a focused rewrite of the sanitized draft, retaining system facts and safety rules but omitting earlier assistant replies, within the existing two-attempt limit. Automatic mode recognizes common Romanized Hindi inputs such as `mujhe iske bare me aur batao`. Explicit language choices remain authoritative. If repair still fails, the UI displays one actionable language-specific failure message instead of a generic provider error; failed assistant messages are excluded from future conversation history. Output checks remain enabled and failed repairs are not reported as successful answers.

Follow-up verification: all 35 backend tests and frontend TypeScript/lint checks passed. Live Ollama answered `mujhe iske bare me aur batao` with laptop history in English when English was selected. With Hindi selected, the first draft failed validation and the focused rewrite returned Hindi script successfully (`usage_complete: false` correctly reflects the discarded attempt). These checks verify language handling, not factual accuracy of every model-generated specification.

The chat UI now defaults to English and offers Hindi, Telugu, Bengali, Tamil, Assamese and Marathi. Requests carry an optional validated `reply_language` field. An explicit selection overrides the question and history for that turn; older API clients without the field retain automatic behavior. Selected Indian languages require their native script, with product names and numbers allowed in Latin characters.

The output check now also catches common Romanized Hindi/Hinglish word patterns (including the reported laptop response). English replies are checked for non-Latin script; other selected languages are checked for their expected script. These are conservative heuristics, not full linguistic identification: Hindi/Marathi and Bengali/Assamese share scripts and cannot be distinguished by script alone. Romanized Hindi vocabulary is not exhaustive. Failed checks get a corrective retry in the selected language and never stream the rejected answer. Discount instructions explicitly disallow offering an unapproved discount or quoting a calculated discounted amount as a real deal.

In automatic mode, agents prioritize the latest customer's language over assistant history and retrieved text. An explicit selector choice takes priority over the input language. English output requires English greetings, refusals and answers. Hindi questions and explicit requests for another language remain supported.

Before streaming, the provider layer checks the sanitized reply for Devanagari letters. For an English-default turn, a share above 10% of alphabetic characters triggers one corrective retry within the existing attempt limit and overall timeout. Repeated mismatches use the next provider in Auto mode; explicit provider selections return `language_mismatch` instead of streaming the wrong-language answer. Usage remains marked incomplete after rejected attempts.

In automatic mode, ASCII-letter questions default to English unless they contain a recognized `in/into <language>` request or common Romanized Hindi word patterns. Brief non-Latin quotations below the threshold are allowed. The guard does not validate every possible output language. Regression tests cover the four original reply excerpts and the reported Romanized Hindi laptop response, all seven selector values, language switching, Hindi requests, retry exhaustion, fallback and the SSE boundary without an AI judge. The original complete evaluation questions were not supplied, so those four tests use representative English questions.

Run from `backend`: `.\.venv\Scripts\python.exe -m unittest test_language test_app test_reliability`.

Follow-up verification: 32 backend tests passed, including mocked streams for all seven language choices. A live Ollama run with the reported English laptop question and Romanized Hindi assistant history returned English, refused the extra 40% discount and kept the catalog price of ₹54,990. A separate English question with Telugu selected returned Telugu script. These live checks establish those two examples only, not translation quality across all seven languages. Gemini live verification is still blocked by authentication.

Explicit cloud selections no longer silently fall back to Ollama. Auto mode tries configured Gemini, then Gemma, then local Ollama, followed by configured ChatGPT and Claude. Transient connection, rate-limit and timeout exceptions are retried once, within a bounded overall deadline. Authentication and generic errors are not retried. Public stream errors contain only a safe diagnostic code, never upstream exception text or credentials.

Verification (2026-10-14): 20 backend unit tests passed (test_app and test_reliability). Live Gemma returned the expected mock product answer with thought tags removed. Live Ollama reported input, output and total tokens. Simulated Gemini/Gemma quota failures successfully fell back to Ollama. Live Gemini remains intermittent; no full evaluation score is established. After fallback, reported usage covers the successful provider only, and failed attempts may have unknown token usage.

Studio: allows up to 120 seconds per request; conservative verification uses 90 seconds and one request at a time. Unknown billing still pauses the budget guard; the reason now explicitly says this does not mean the budget was spent. Do not disable this guard or treat unknown billing as zero.
