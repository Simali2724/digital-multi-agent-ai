# Reliance Digital project metadata

Updated: 2026-09-30

Active root: D:\reliance-project
RAG data: D:\reliance-data
Ollama model store: D:\ollama-models

Verified original source/data backup:
D:\reliance-backup-20260929

Original nested project:
D:\relience-project 222\reliance-project
Status: preserved until final verification is complete.

## Architecture

Backend:
FastAPI + LangGraph

Frontend:
Next.js 16

Knowledge retrieval:
ChromaDB semantic RAG with local keyword fallback support

Local LLM:
Ollama / llama3.2:3b

## Providers

Default provider:
Auto

Available frontend choices:

- Auto
- Claude
- ChatGPT
- Gemini
- Ollama

The backend supports automatic provider fallback.

Current Auto behavior prefers available Gemini text generation, then other configured cloud providers, and finally local Ollama.

Explicit cloud-provider requests can fall back to Ollama when the requested provider is unavailable.

Claude and ChatGPT remain supported even when API keys or credits are not currently configured.

Gemini is used for:

- Text generation
- Multimodal / image interpretation
- Embeddings

The frontend displays the requested provider and actual provider used, for example:

Auto -> Gemini

or:

Auto -> Ollama

## Agents

LangGraph routes requests to:

- sales_agent
- resq_agent
- rag_agent
- vision_agent

Sales Agent handles products, prices, warranties, orders and buying-related questions.

resQ Agent handles service tickets, technicians and repair/service requests.

Knowledge Support / RAG Agent handles manuals, troubleshooting, policies and knowledge-base questions.

Vision Agent handles image-based requests when multimodal Gemini access is available.

## Data

Structured mock data is stored in:

backend\data\products.json
backend\data\tickets.json
backend\data\orders.json

All customer, order, ticket, product, price and warranty information used in the demo is mock/synthetic data.

The frontend loads the product catalog from the backend.

## Knowledge Base

Knowledge root:

D:\reliance-data

Verified active Chroma collection:

reliance_knowledge_e2f0c44b0cb4

Verified active document count:

17

The older collection named:

reliance_knowledge

contains a legacy single-document index and is not the active collection.

The active collection is selected through:

D:\reliance-data\chroma_db\active_collection.txt

Internal source paths are hidden from normal chatbot responses.

## Verified End-to-End Flows

Product query:
P001 price and warranty
Result: Sales Agent
Verified warranty: 24 months

Knowledge query:
P002 Daikin AC warranty
Result: Knowledge Support
Verified warranty: 60 months

Service query:
SR-1001
Result: resQ Agent
Verified status: In Progress

Order query:
ORD-9001
Result: Sales Agent
Verified status: Delivered

Auto provider fallback to Ollama has been verified in the browser.

## Frontend Verification

Verified:

- ESLint passes
- Production build passes
- Markdown rendering works
- Requested -> actual provider badge works
- Image upload UI works

## Startup

Startup scripts:

start-ollama.ps1
start-backend.ps1
start-frontend.ps1

All three scripts detect already-running services to reduce duplicate-server and port-conflict errors.

## Test Payloads

Development smoke-test files are stored in:

D:\reliance-project\tests

Files:

- chat-test.json
- image-test.json
- ollama-generate-test.json

## Current Limitations

Vision architecture is implemented, but live image interpretation depends on Gemini multimodal quota availability.

Local llama3.2:3b is currently a text model and is not used as the image-understanding fallback.

OpenAI and Anthropic providers require valid API keys and available credits before direct use.

## Documentation

Use README.md for:

- Startup instructions
- Provider configuration
- RAG rebuild instructions
- Verification commands
- Demo flows
- Security notes
- Current project status