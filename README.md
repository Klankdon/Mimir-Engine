🛡️ Mimir Engine

An open-source, zero-client middleware proxy and long-term vector memory engine for local LLMs and chat UIs.

Mimir Engine sits transparently between your chat client (Agnaistic, SillyTavern, Open WebUI) and your backend inference server (KoboldCPP, vLLM, Ollama). By leveraging PostgreSQL + pgvector, Mimir intercepts prompt streams in real-time, injects relevant long-term context via cosine similarity search, and captures new memories without clogging your prompt stack or requiring custom mobile apps.

💡 Why Mimir Engine?Standard vector tools drop huge walls of raw chat history back into context, causing token bloat, high generation costs, and model hallucinations. Mimir solves this with a decoupled middleware proxy architecture:Zero-Mobile Overhead: Mobile users access Agnaistic or SillyTavern normally via web browser. Simply point the client's API/Proxy endpoint to your Mimir host instance—no local mobile apps, Termux, or nested virtual machines required.Deterministic Chunking & Traceability: Conversations are indexed into target token slices ($\sim300$ tokens) with structured parent tracking (Character, World, Session ID) and local disk backups.Non-Blocking Async Ingestion: Memory retrieval happens on prompt ingress. Assistant responses are flushed back via Server-Sent Events (SSE) immediately, while vector embeddings are generated and committed in background tasks.Built-in Svelte 5 "Geeks Dashboard": Monitor live vector storage, inspect cosine distance thresholds, inspect memory slices, and adjust proxy configurations in real-time.🏗️ Architecture Stack[ Agnaistic / SillyTavern / Web Client ]
                   │
                   ▼  (OpenAI / Kobold API Format)
┌─────────────────────────────────────────────────────┐
│          Mimir Engine Middleware Proxy              │
│       FastAPI + Uvicorn + Svelte 5 Dashboard        │
└──────────────┬──────────────────────┬───────────────┘
               │                      │
               ▼                      ▼
┌─────────────────────────────┐  ┌─────────────────────────────────┐
│     PostgreSQL + pgvector   │  │        Upstream LLM Host        │
│  (Cosine Vector Store DB)   │  │  (KoboldCPP / Ollama / vLLM)   │
└─────────────────────────────┘  └─────────────────────────────────┘
Backend API: FastAPI (Async proxy routing, OpenAI-compatible hooks, embedding ingestion).Database & Vector Store: PostgreSQL with pgvector extension.Dashboard Frontend: Svelte 5 + TypeScript + Tailwind CSS (Pre-compiled into static distribution).🚀 Quick Start & One-Click SetupMimir Engine features automatic environment creation, dependency resolution, and frontend compilation via cross-platform boot scripts.Option A: Standard Boot Script (Windows / Linux / macOS)Clone the Repository:Bashgit clone https://github.com/Klankdon/Mimir-Engine.git
cd Mimir-Engine
Run the One-Click Launcher:Windows: Double-click start.bat (or run in CMD):DOSstart.bat
Linux / macOS: Make executable and run:Bashchmod +x start.sh
./start.sh
The boot script automatically runs git pull, creates a Python virtual environment, installs dependencies, builds static assets, launches the proxy, and opens the dashboard at http://localhost:8000.
Option B: Docker Compose (Server & HomeLab Deployment)For containerized environments running Docker Desktop, Portainer, or headless Linux servers:Bash# 
1. Bring up PostgreSQL (pgvector) and Mimir Engine services
docker compose up -d

# 2. Access the live dashboard and proxy
http://localhost:8000
🔌 Connecting to Your Chat ClientPoint your web chat client (Agnaistic, SillyTavern, etc.) to Mimir Engine as an OpenAI-compatible proxy:
API Base URL: http://localhost:8000/v1 (or your host server IP)
API Key: (Any dummy string or your configured UPSTREAM_LLM_KEY)
Upstream LLM Mapping: Configurable inside the Geeks Dashboard under Settings -> Upstream LLM URL.

💬 Community & DiscussionsGitHub Discussions: Have a feature request, embedding benchmark, or configuration setup to share? [Join the Mimir Engine GitHub Discussions](https://www.google.com/search?q=https://github.com/Klankdon/Mimir-Engine/discussions).

Patreon: Want to support dedicated cloud testbeds, multi-model embedding pipelines, and open-source development? [Support Mimir Engine on Patreon](https://patreon.com/MIMIR_Engine?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLink).

📧 Licensing & InquiriesCommercial Inquiries: Contact jmcgehee@zohomail.com to discuss commercial licensing, custom integration pipelines, or enterprise deployments.
