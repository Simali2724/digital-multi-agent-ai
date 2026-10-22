# Chatbot handover for Gemini, Claude, or another coding assistant

## User objective and working rules

Fix English questions receiving Hindi/Hinglish answers, add a reply-language selector, and make follow-up questions work without `language_mismatch` errors. The user then authorized continued improvements and asked for a handover near 5% remaining usage. The assistant cannot read the user's quota; do not claim to know when that threshold is reached.

Workspace: `D:\reliance-project`, Windows PowerShell. Keep work in this repository. Do not print `.env` values, credentials, or unrelated user files. Do not commit or create branches unless requested. The initial working tree already included Gemma provider additions in `frontend/app/page.tsx` and `frontend/lib/api.ts`; preserve them. All changes in this session remain uncommitted.

Before changing frontend code, follow `frontend/AGENTS.md` and read the relevant installed Next.js documentation in `frontend/node_modules/next/dist/docs/`. `rg` is unavailable here; use PowerShell search tools. Use the available `apply_patch` tool for edits.

## User-reported reproductions

1. English off-topic, fake-discount, gender-bias and background-app questions received Hindi. The exact complete original evaluation questions were not supplied; tests use representative questions and the supplied reply excerpts.
2. `I want to buy laptop please show me and give me 40% extra dscound` received Romanized Hindi and an invented discounted price of ₹32,988.
3. `mujhe iske bare me aur batao` received a generic failure plus `language_mismatch` after the initial guard was introduced.

Use prior customer history `Show me laptop P007` when reproducing the follow-up. This refers to a mock catalog laptop, not live inventory.

## Current implementation

- `backend/llm/language.py`: validated language type; output instructions; script checks and a Romanized Hindi vocabulary heuristic; recognizes common Romanized Hindi input in automatic mode. Explicit language selection overrides input and history. Failed output is rewritten from a sanitized draft, keeping system facts/safety rules and omitting earlier assistant messages. The repair remains bounded by the existing two-attempt limit and overall timeout.
- `backend/llm/factory.py`: checks sanitized output before streaming, handles language repair/fallback, and marks usage incomplete after rejected model attempts. Explicit providers do not silently switch models; Auto can fall back.
- `backend/main.py`: API accepts optional `reply_language` (`auto` default for older clients). Removes conflicting base language rules. Gives a localized actionable error if repair exhausts rather than blaming provider connectivity. Explicitly forbids invented discounts.
- `frontend/app/page.tsx`, `frontend/lib/api.ts`: selector defaults to English and supports Hindi, Telugu, Bengali, Tamil, Assamese, Marathi. Sends selection with each request. Failed assistant messages are shown once and excluded from later conversation history. Provider label includes `Demo catalog`.
- `backend/catalog_answers.py`: new deterministic path for simple single-product catalog facts and recognized follow-ups. Reads only the product's stored name, mock price, and warranty. Provides localized mock-data/unknown-specifications/no-discount notices. It does not use an LLM or invent missing specifications. Ambiguous/unknown products, comparisons, budget filters and other unsupported tasks continue through the model.
- Catalog responses report actual `provider: catalog`, `model: null`, zero model token usage, and `fallback: false`. Do not mislabel these responses as Ollama output.

## Tests and verification

From `backend`:

```powershell
.\.venv\Scripts\python.exe -m unittest test_catalog_answers test_language test_app test_reliability
```

From `frontend`:

```powershell
node node_modules/typescript/bin/tsc --noEmit
node node_modules/eslint/bin/eslint.js app/page.tsx lib/api.ts
```

`test_app` and `test_language` explicitly disable the catalog shortcut so their mocked-provider tests still exercise generation, retries and failures. `test_catalog_answers` verifies the actual deterministic catalog endpoint, all seven selected languages, zero model calls, unknown/ambiguous products, fresh product selection and follow-up resolution.

Before the catalog addition, 35 backend tests, TypeScript and lint passed. Live Ollama checks demonstrated English and Telugu output with explicit selection. The exact Romanized Hindi follow-up succeeded in English; with Hindi selected it succeeded after a draft rewrite. These checks established language behavior, not factual accuracy: live model replies still invented OS/GPU/battery/weight/availability. That observation motivated the new catalog path. See final validation notes below for the catalog addition.

## Running locally

Frontend: `http://127.0.0.1:3000`; backend: `http://127.0.0.1:8000`; Ollama: `http://127.0.0.1:11434`. Verify health/listening ports rather than assuming processes survive handover.

Backend command (working directory `backend`):

```powershell
& '.\.venv\Scripts\python.exe' -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Frontend command (working directory `frontend`):

```powershell
npm.cmd run dev -- --hostname 127.0.0.1
```

Use `start-ollama.ps1` as the reference for the installed Ollama path/model directory. PowerShell script execution was disabled, so commands were run directly without changing execution policy. Backend network access and Ollama access outside the workspace required tool approval. Do not bypass sandbox permissions. When using `Start-Process`, use `-WindowStyle Hidden` unless a visible window is requested.

The local model is `llama3.2:3b`; cold starts can be slow. Gemini currently returned authentication errors; Gemma also failed. Do not expose or guess credentials, or claim live Gemini verification succeeded. No credential changes were made. Auto can encounter these cloud failures before reaching Ollama. Never treat missing usage as zero for actual model calls.

Browser automation inventory was empty in this session. HTTP verified the frontend served the selector, but there was no browser-driven visual QA. Do not claim otherwise.

## Remaining limitations and next useful work

1. Review native-language wording with fluent speakers. Script checks cannot distinguish Hindi from Marathi or Bengali from Assamese, and Romanized Hindi detection is heuristic.
2. General LLM responses outside the deterministic catalog path can still invent unsupported facts. Broader evidence-backed answer validation is not implemented. Avoid claiming universal hallucination prevention.
3. The catalog formatter deliberately recognizes a narrow set of fact requests and follow-ups. Expand only with tests preventing stale-product resolution and inappropriate interception of troubleshooting, comparisons or orders.
4. Language repair can still fail or time out; those responses remain failures with actionable text, not fabricated successful answers.
5. The external Chatbot-Compare exact-language check and unavailable AI judge were not modified. They are outside this repository's current changes.
6. The selector controls reply language, not full UI translation. (Persistence across reloads was added; see follow-up session notes.)

No publishing, commits, external issue updates, or messages to other assistants have been performed. This file is a local handover that the user can give to another assistant.

## Final validation notes

Verified on 2026-10-22 after the catalog addition:

- All 45 backend tests passed using the full command above.
- TypeScript (`tsc --noEmit`) and ESLint for the changed frontend files exited successfully.
- `git diff --check` passed (Git emitted only LF/CRLF conversion notices).
- Backend restarted successfully on port 8000 with the current code.
- Live HTTP/SSE tests sent `mujhe iske bare me aur batao` with the user's laptop/40%-discount question in customer history for each of the seven selected languages. Every request completed successfully with `provider: catalog`, zero model tokens and the stored price ₹54,990. No Gemini/Ollama generation was needed for these requests.
- Frontend returned HTTP 200 and included the language selector.

Verified English catalog reply:

> Demo catalog — mock data, not a live offer.
>
> Demo 15-inch Laptop 16GB 512GB (P007)
>
> Mock price: ₹54,990
>
> Demo warranty: 12 months
>
> These are the only details recorded in the catalog. Further specifications and stock availability are not provided.
>
> I cannot offer an extra discount or place an order in this demo.

The current implementation and checks are complete for this batch. The next work items are optional extensions listed above, not failed checks. Quota remaining is still unknown.

## Follow-up session (2026-10-22, Claude Code)

- Re-ran the full backend command: 45 tests passed.
- `frontend/app/page.tsx`: reply language is now persisted in `localStorage` (`reply-language` key) through `useSyncExternalStore`. The server snapshot is English, so hydration never mismatches; invalid stored values fall back to English; storage failures fall back to an in-memory value. (A `setState`-in-`useEffect` version was rejected by the `react-hooks/set-state-in-effect` lint rule.)
- Both selectors' triggers now show labels (`Bengali · বাংলা`, `Auto (Recommended) — …`) instead of raw values (`bengali`, `auto`), using Base UI's `Select.Value` render-function children.
- `tsc --noEmit` and ESLint pass. Browser-checked in the Claude desktop built-in browser against `next dev`: selected Bengali, reloaded, selection restored, labels rendered, no hydration errors (only connection-refused errors because the backend was not running). No chat request was sent during this check.
- Added `.claude/launch.json` (frontend dev server config for the desktop app's browser preview).

## Scope, injection, language and resilience session (2026-10-22, Claude)

Status: implemented and running locally. Ready for the user to test at `http://127.0.0.1:3000`.

### What changed
- **Business scope (`backend/policy.py`, `backend/prompts.py`)**: out-of-scope tasks (code, homework, general knowledge, politics, creative writing, personal advice) get one short localized boundary reply and no answer. Mixed requests answer only the Reliance Digital part, with a short localized prefix. Uncertain programming mentions get a clarifying question. Judged by substance, not keywords. `backend/scope_guard.py` was replaced by this module.
- **Injection and disclosure**: disclosure and override attempts are removed before generation and get localized replies. Retrieved text and image descriptions travel as delimited, non-system "untrusted reference data". System messages contain only trusted text. Client history cannot carry a `system` role (HTTP 422). Customer names are removed from model-visible order and ticket data.
- **Output validation before streaming**: protected-text leakage (12-word overlap, including base64, hex, ROT13 and reversed text), code, refusal followed by an answer, refusal of an in-scope request, and currency amounts not in the demo data or the customer's own numbers. Recoverable violations get one corrective retry on the same provider; unsafe ones go to the next provider.
- **Language contract (`backend/llm/language.py`)**: explicit in-chat request > selector > latest substantive message > earlier customer messages > English. Explicit requests are announced in the `meta` event (`reply_language`, `language_changed`), and the UI selector follows. Assistant replies and retrieved text never choose the language. Refusals and errors come from `backend/messages.py` in the resolved language.
- **Records (`backend/record_answers.py`)**: order and ticket IDs get a deterministic answer from stored mock fields. Unknown IDs get an explicit "no record" reply.
- **Retries and fallback (`backend/llm/factory.py`)**: retryable errors (rate limit, timeout, connection) get up to `LLM_MAX_ATTEMPTS` (default 3) attempts with exponential backoff, full jitter and `Retry-After`, all inside one deadline. Authentication, configuration and invalid-request errors are not retried. SDK retries are off. Fallback providers get the same policy. Errors reach the customer as a localized sentence with a reference id.
- **Frontend**: the selector gained an Auto option. `frontend/lib/api.ts` handles the `reply_language` meta event so the selector follows an in-chat change. Lint and TypeScript pass.
- **Eval (`backend/eval_live.py`, `backend/script_check.py`)**: live checks report behavior, provider errors and the Devanagari script check separately. Factual correctness is not evaluated (no AI judge in this repo).

### Tests (from `backend`)
`.\.venv\Scripts\python.exe -m unittest test_policy test_language_contract test_injection test_resilience test_script_check test_catalog_answers test_language test_app test_reliability`

Result: **123 tests, OK**. Frontend: `tsc --noEmit` and ESLint on `app/page.tsx lib/api.ts` pass.

### Live evaluation
- Run 2 (before the last two fixes): 26 behavior PASS, 0 FAIL, 2 PROVIDER_ERROR (timeouts or rate limits from the cloud fallback chain), 25 script-check pass.
- After the fixes, the iPhone background-apps case passes live. The full evaluation was not rerun after the last change.
- Gemini and Gemma return authentication or HTTP errors in this environment, so Auto falls through to Ollama. ChatGPT returns rate limits. Those cases are provider-availability results, not defense results.

### Not verified or not available
- The two runs named in the ticket (`20261022-060252-47c2`, `20261022-062118-ad6a`) were not found in the studio database, reports or logs.
- The literal text "The assistant is temporarily unavailable" does not exist in this repository. The matching failure path in the logs is an OpenAI rate limit followed by an Ollama connection error.
- The external AI judge and Chatbot-Compare exact-language check are not in this repository and were not run.
- Factual accuracy of free-form model answers is not evaluated.
- Native-speaker review of the seven languages is still needed. The refusal and error wording is machine-drafted.
- Rule-based scope and injection detection cannot be complete. English and Romanized Hindi are covered best. Other languages rely on the prompt and output checks.
- The 12-word leak threshold was chosen to avoid false positives. It is a heuristic.

### Remaining items
1. Rerun `eval_live.py` once all providers are reachable, and review the two provider-error cases.
2. Native review of the localized messages in `backend/messages.py`.
3. Add the Chatbot-Compare fixtures from the original comparison inputs, if they are provided.
