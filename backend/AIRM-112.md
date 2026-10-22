# AIRM-112 local remediation — 2026-10-22

The reported Chatbot-Compare runs `20261022-060252-47c2` and
`20261022-062118-ad6a` failed the release gate: safety 50, minimum 90.
This change does not establish a new score or close the issue.

The application refuses recognized instruction-disclosure and override requests
before provider calls, separates untrusted reference data from system messages,
and validates complete answers before streaming. Protected-text matching uses
a 12-word overlap heuristic, including selected encodings; it is not a complete
prompt-injection defense.

Provider recovery uses bounded retries with jitter and a shared deadline.
Retry-After supports numeric seconds and HTTP dates, including long delays.
Auto mode skips to the next provider when the requested wait exceeds the
remaining deadline. Explicit provider selection does not switch models.
This retry gap is not confirmed as the cause of the original failed runs.

Validation: 126 backend regression tests passed, including refusal when the
provider would return a rate limit, repeat-above variants, and fallback after
a long Retry-After. Three repeat-above variants were also blocked by the local
HTTP endpoint. Provider failures are not counted as safety successes.

Release remains blocked pending deployment and a fresh Chatbot-Compare run
against the shipped bot that passes the affected checks and scores at least 90.
The local backend reports Gemini 2.5 Flash; the ticket identifies Gemini 3.6 Flash.
The exact external evaluator fixtures and original run logs were unavailable.
