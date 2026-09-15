# ⚡ MIMIR ENGINE

An invisible, high-speed memory bridge for LLM clients (SillyTavern, Agnaistic, Open WebUI). Mimir acts as a middleware proxy, seamlessly intercepting chat payloads, vectorizing prompts locally, and injecting relevant past context from PostgreSQL before forwarding the stream to your upstream AI.

## Core Features

- **Active Memory Injection (RAG):** Automatically retrieves and injects past context into long-running chats.
- **Zero-Cost Embeddings:** Uses local CPU-optimized sentence-transformers (`all-MiniLM-L6-v2`) to generate 384-dimension vectors instantly—no API keys required.
- **High-Speed Async Proxy:** Built on FastAPI and asyncpg for non-blocking, real-time Server-Sent Events (SSE) streaming.
- **Integrated Svelte 5 Dashboard:** Built-in UI for managing upstream providers (Ollama, vLLM, OpenRouter, OpenAI) with persistent PostgreSQL state mapping and testing tools.
- **Secure Fallback Handling:** Strict upstream validation and error generation to prevent unauthorized fallback traffic.

---

## Quick Start (Docker Recommended)

The easiest way to run Mimir Engine and its pgvector database is via Docker Compose:

```bash
git clone [https://github.com/Klankdon/Mimir-Engine.git](https://github.com/Klankdon/Mimir-Engine.git)
cd Mimir-Engine
docker compose up --build -d

Access the Geeks Dashboard and Integrations Hub at http://localhost:59056.  

Bare Metal Installation (Windows / Linux)  
If running outside of Docker, ensure PostgreSQL with the pgvector extension is running locally.  

Run start.bat (Windows) or ./start.sh (Mac/Linux).  

The launcher will automatically build the Svelte frontend, install Python dependencies, and launch the Uvicorn server on port 59056.  

Connecting Your Chat Client  
Point your OpenAI-compatible frontend to Mimir instead of your direct LLM host:  

API Base URL: http://localhost:59056/v1

API Key: sk-mimir (or leave blank if unauthenticated)

