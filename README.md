🛡️ Mimir Engine
A containerized, high-speed hybrid memory system for local LLMs and AI frontends.

Mimir Engine bridges the gap between fast conversational UI and deep, persistent memory. By combining PostgreSQL + pgvector with a decoupled file-based logging pipeline, Mimir provides deterministic context recall without crippling your LLM’s generation speeds or polluting your prompt context.

Built from the ground up for power users, developers, and the self-hosted community.

💡 Why Mimir?
Standard vector databases drop raw message walls into context, leading to memory duplication, token bloat, and hallucinations. Mimir fixes this with a dual-tier indexing hierarchy:

Deterministic Traceability (DOCID & PARENT-ID): Every 300-token chunk is saved directly to local storage under a strict parent hierarchy (Character/World) and assigned a unique DOCID.

Hybrid Semantic Storage: Raw logs stay on disk, while an asynchronous middleware extracts atomic facts, keywords, and pgvector embeddings into PostgreSQL.

Low-Latency Retrieval: During chat, Mimir performs lightning-fast vector/keyword queries, injecting only the top relevant summaries into the prompt stack. The full raw transcript on disk is only accessed if deep recall is requested.

🏗️ Architecture Stack
   [ SillyTavern / Mobile UI ]
               │
               ▼  (HTTP REST / Webhook)
 ┌───────────────────────────────────┐
 │   Mimir Middleware (Websniffer)   │  <-- Asynchronous Processing
 └─────────┬───────────────┬─────────┘
           │               │
           ▼               ▼
┌───────────────────┐  ┌───────────────────────────────────┐
│ Storage Container │  │        Postgres Container         │
│ (Raw DOCID .txt)  │  │ (pgvector + Metadata & Keywords) │
└───────────────────┘  └───────────────────────────────────┘
Fully Containerized: Self-contained via docker-compose. Zero system bloat.

Isolated Environment: Runs internally with custom non-standard port defaults (59055+) to avoid local port conflicts with dev stacks or home lab hardware.

Client Agnostic: Standard REST API hooks cleanly into SillyTavern, custom web UI wrappers, or native mobile clients.

🚀 Quick Start
Ensure Docker Desktop is installed and running, then execute the launcher script for your platform:

Windows: Double-click Launch-Mimir.bat

Linux: Run ./Launch-Mimir.sh

Mac: Double-click Launch-Mimir.command

Bash
# Or launch directly via Docker Compose:
docker compose up -d
Access the services at your local endpoints:

UI Interface: http://localhost:59055

Mimir API Bridge: http://localhost:59056

PostgreSQL Engine: 127.0.0.1:59057

🤝 Community & Contributing
Mimir Engine is 100% open-source and built for the community. We welcome PRs, feature ideas, and feedback! Check out our open issues tagged good first issue to dive in.

License: MIT

Roadmap: Native Jetpack Compose Android Client, Automated Deduplication Sweeps, and Custom Embedding Model Switcher.
