Markdown
# Mimir Engine 🛡️🧠

*Mimir Engine* is a high-performance, containerized middleware proxy and persistent memory framework built for advanced local and cloud-backed LLM vibe-coding, RAG memory retrieval, and autonomous background agents.

## Architecture & Core Features

- **3-Tier Multi-Role Router**: Intentionally separates execution pipelines across specialized roles:
  - **Chat (Primary Narrative)**: Dedicated conversational runtime with persistent pgvector memory chunking and automated context injection.
  - **Vibe (Code & Terminal)**: Optimized interactive stream channel for code generation, debugging, and workspace tools with dynamic model selection.
  - **Agent (Background Tasks)**: Asynchronous target allocation for instruction directives and code maintenance.
- **Dual-Database Architecture**:
  - **`system.db` (SQLite)**: Manages the local control plane, upstream providers, custom model nodes, workspace states, and agent configuration stasis.
  - **`mimir_db` (PostgreSQL + `pgvector`)**: Handles heavy vector storage, 384-dimensional state embeddings (`vector(384)`), and semantic RAG memory similarity searches.
- **Agent Directives (`/directives`)**: Drop-in JSON instruction files (such as code janitor rules) that automatically sync into the system control plane on boot via `importers.py`.
- **Integrations Hub**: Universal upstream provider registration supporting OpenAI-compatible endpoints (Ollama, LM Studio, OpenRouter, Google Gemini, and custom proxies) with dynamic active model fallback mapping and custom friendly IDs.
- **Persistent Workspace Tabs**: CSS-driven view states that eliminate tab-switching data loss across the Vibe workspace and Geeks Dashboard.

## Quick Start Guide

Pull the package:
```bash
docker pull ghcr.io/klankdon/mimir-engine:latest
Or run locally via Docker Compose:

Clone and Configure:

Bash
git clone [https://github.com/Klankdon/Mimir-Engine.git](https://github.com/Klankdon/Mimir-Engine.git)
cd Mimir-Engine
cp .env.example .env
Spin Up Containers:

Bash
docker compose up --build -d
Access Dashboard:
Open your browser and navigate to http://localhost:59056 to configure upstream targets in the Integrations Hub and spin up live sessions.
