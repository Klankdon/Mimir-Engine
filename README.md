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


🧜‍♂️ MIMIR // ENGINE

An open-source, containerized AI narrative workspace and proxy engine built for dynamic context tracking, pgvector memory retrieval, multi-character story sessions, and custom glassmorphic HUD reskinning.
🛠️ Architecture Overview

    Frontend: Svelte + TypeScript + Tailwind CSS (Vite dev server)

    Backend API: FastAPI (OpenAI-compatible endpoints & asset ingestion)

    Database & Vectors: PostgreSQL with pgvector extension (384-dim embedding storage)

    Host Storage: Local raw text chunk backup (./storage/docids/)

🚀 Quick Start & Installation
Prerequisites

Make sure you have the following installed on your host system:

    Docker and Docker Compose

    Node.js (v18+ recommended) and npm

    Git

Step 1: Clone the Repository
Bash

git clone https://github.com/Klankdon/Mimir-Engine.git
cd Mimir-Engine

Step 2: Environment Configuration

Create a .env file in the project root if it doesn't already exist:
Code snippet

DB_HOST=mimir-db
DB_PORT=5432
DB_NAME=mimir_db
DB_USER=mimir_user
DB_PASSWORD=mimir_secret_password

Step 3: Spin Up Docker Services (Postgres + Backend)

Bring up the PostgreSQL container (with pgvector) and FastAPI services:
Bash

docker compose up -d

Verify that the containers are healthy:
Bash

docker ps

Step 4: Run the Svelte Desktop UI

Navigate to the frontend workspace and install dependencies:
Bash

cd mimir-desktop
npm install

Start the Vite development server:
Bash

npm run dev

Open your browser and navigate to:
Plaintext

http://localhost:5173

🎴 Key Features

    Glassmorphic Theme Engine: Dynamic JSON/image skin loading with instant CSS variable updates.

    Multi-Character Story Timelines: Switch active speakers, retain shared room memories via session_id, and manage room rosters.

    pgVector Memory Storage: Automatic similarity search (<=> cosine distance) backed by Docker Postgres.

    Chub/ST JSON Card Ingestion: Client-side in-memory JSON parsing for character cards, lorebooks, and embedded skins.

🧹 Git Hygiene Tip

Ensure your node_modules/ and build artifacts stay untracked:
Bash

echo "node_modules/" >> .gitignore
echo ".vite/" >> .gitignore
📧 **Commercial Inquiries:** Contact `jmcgehee@zohomail.com` to discuss commercial licensing options.

Roadmap: Native Jetpack Compose Android Client, Automated Deduplication Sweeps, and Custom Embedding Model Switcher.

https://patreon.com/MIMIR_Engine?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLink
