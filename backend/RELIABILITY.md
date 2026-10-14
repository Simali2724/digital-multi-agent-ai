# Reliability corrections — 2026-10-13

Explicit cloud selections no longer silently fall back to Ollama. Auto mode tries configured Gemini, then Gemma, then local Ollama, followed by configured ChatGPT and Claude. Transient connection, rate-limit and timeout exceptions are retried once, within a bounded overall deadline. Authentication and generic errors are not retried. Public stream errors contain only a safe diagnostic code, never upstream exception text or credentials.

Verification (2026-10-14): 20 backend unit tests passed (test_app and test_reliability). Live Gemma returned the expected mock product answer with thought tags removed. Live Ollama reported input, output and total tokens. Simulated Gemini/Gemma quota failures successfully fell back to Ollama. Live Gemini remains intermittent; no full evaluation score is established. After fallback, reported usage covers the successful provider only, and failed attempts may have unknown token usage.

Studio: allows up to 120 seconds per request; conservative verification uses 90 seconds and one request at a time. Unknown billing still pauses the budget guard; the reason now explicitly says this does not mean the budget was spent. Do not disable this guard or treat unknown billing as zero.
