Markdown
# Mimir Engine 🛡️🧠

**Mimir Engine** is a high-performance, containerized middleware proxy and persistent memory framework built for advanced local and cloud-backed LLM roleplay, coding assistance, and autonomous background agents.

---

## Architecture & Core Features

* **3-Tier Multi-Role Router**: Intentionally separates execution pipelines across specialized roles:
  * **Chat (Primary Narrative)**: Dedicated conversational runtime with persistent `pgvector` memory chunking and automated context injection.
  * **Vibe (Code & Terminal)**: Optimized interactive stream channel for code generation, debugging, and workspace tools.
  * **Agent (Background Tasks)**: Asynchronous target allocation for web sniffers, indexers, and vector chunking tasks.
* **Database & Vector Pipeline**: Powered by PostgreSQL container instance (`mimir_db`) utilizing the `pgvector` extension for semantic embedding searches across 384-dimensional state vectors.
* **Integrations Hub**: Universal upstream provider registration supporting OpenAI-compatible endpoints (Ollama, LM Studio, OpenRouter, Google Gemini, and custom proxies) with dynamic active model fallback mapping.
* **Real-Time Telemetry Stream**: Live WebSocket/SSE event broadcast console for ingress payload tracking, vector scan matching, and upstream egress metrics.

---

## Quick Start Guide

1. **Clone and Configure**:
   ```bash
   git clone [https://github.com/mimir-engine/mimir-engine.git](https://github.com/mimir-engine/mimir-engine.git)
   cd mimir-engine
   cp .env.example .env
Spin Up Containers:

Bash
docker compose up --build -d
Access Dashboard:
Open your browser and navigate to http://localhost:59056 to configure upstream targets in the Integrations Hub and spin up live narrative sessions.


---

### ## GitHub Discussions / Community Update

**Title:** 🚀 Milestone Update: 3-Tier Multi-Role Routing, Dynamic Provider Resolution, & Full PGVector Memory Pipelines Live!

Hey everyone,

We just hit a massive development milestone on Mimir Engine. Thanks to some heavy lifting under the hood, we've officially ironed out the proxy routing pipeline, cleaned up database string handling, and locked in seamless multi-provider support.

#### What’s New:
1. **Dynamic Integrations Hub Mapping**: You no longer need to hardcode model strings in frontend code bundles. The proxy now inspects incoming ingress payloads and dynamically resolves the active upstream provider and model based on your assigned target role (`chat`, `vibe`, or `agent`).
2. **Expanded Database Precision**: Resolved text-buffer truncation issues across PostgreSQL and vector storage queries, ensuring long generated blocks, code scripts, and lore chunks return 100% intact.
3. **Multi-Endpoint Compatibility**: Verified smooth, zero-latency handoffs across local Ollama instances, OpenRouter, and Google Gemini endpoints with automated context-length retry guardrails.

Jump into the [Geeks Dashboard](http://localhost:59056/) to test out the query console and drop your feedback or feature requests below!
