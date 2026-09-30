# Reliance Digital project metadata

Updated: 2026-09-29
Active root: D:\reliance-project
RAG data: D:\reliance-data
Ollama model store: D:\ollama-models
Verified original source/data backup: D:\reliance-backup-20260929
Original nested projects: D:\relience-project 222\reliance-project (preserved)

FastAPI + LangGraph backend, Next.js frontend, ChromaDB semantic retrieval.
Default chat provider: Auto. Available choices: Auto, Claude, ChatGPT, Ollama.
Auto prefers OpenAI for sales/orders/service tickets and Claude for knowledge/vision answers, with configured cloud alternate then Ollama fallback.
Gemini is limited to embeddings and image interpretation.
Data: 10 mock products, 5 mock service tickets, 4 mock orders.
Knowledge: 17 documents, 17 indexed chunks in the verified rebuilt collection.
The frontend fetches the product catalog from the backend.
The streaming endpoint buffers a complete model answer before sanitizing and delivering SSE chunks.

Use README.md for startup, credentials, data rebuild and verification commands.
Use REPAIR_REPORT.md for final validation results and limitations.
