🧜‍♂️ MIMIR // ENGINE
An open-source, containerized AI narrative workspace, middleware proxy, and context engine built around PostgreSQL + pgvector (384-dim embeddings via cosine distance). Designed for deep memory retention, multi-character story sessions, and seamless integration with external frontends like SillyTavern or Agnaistic.

🛠️ Architecture Overview
Frontend: Svelte 5 + TypeScript + Tailwind CSS (Vite Dev Server) with dedicated views:

ChatPage: Lightweight live console to monitor or smoke-test chat turns.

GeeksDashboard: Real-time telemetry, RAM/token meters, pgVector inspector, and a locked SubSurface SQL console.

IntegrationsHub: One-click endpoint switching (Cloudflare Tunnel, Tailscale, ngrok, Local Direct Binding).

Backend API: FastAPI + Uvicorn (app.py / OpenAI-compatible /v1/chat/completions endpoints & asset ingestion).

Database & Vectors: PostgreSQL with pgvector extension (384-dim embedding storage).

Host Storage: Local raw text chunk backup (./storage/docids/).

🚀 Quick Start & Installation
Prerequisites
Make sure you have the following installed on your host system:

Docker & Docker Compose

Node.js (v18+) & npm

Python 3.10+ (if running backend outside Docker)

Step 1: Clone the Repository & Configure Environment
Bash
git clone https://github.com/Klankdon/Mimir-Engine.git
cd Mimir-Engine
Create a .env file in the project root:

Code snippet
DB_HOST=mimir-db
DB_PORT=5432
DB_NAME=mimir_db
DB_USER=mimir_user
DB_PASSWORD=mimir_secret_password
Step 2: Boot Database & Backend Stack
Option A: Fully Containerized (Recommended)
Spin up PostgreSQL (pgvector) and the FastAPI backend together:

Bash
docker compose up -d
Verify that the containers are healthy:

Bash
docker ps
Option B: Local Uvicorn Development
If running the Python service directly on host while Postgres runs in Docker:

Bash
# 1. Start Docker Postgres container
docker compose up -d mimir-db

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Boot Uvicorn ASGI server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
Step 3: Boot Desktop Interface
Navigate to mimir-desktop, install dependencies, and start the Svelte 5 development server:

Bash
cd mimir-desktop
npm install
npm run dev
Open your browser and navigate to:

Plaintext
http://localhost:5173
🎴 Key Features & Interfaces
Proxy & Middleware Integrations (IntegrationsHub): Expose OpenAI-compatible completion endpoints (http://localhost:8000/v1) to SillyTavern or external clients via Cloudflare Tunnels, Tailscale, ngrok, or local binding.

Geeks Dashboard & SubSurface Console (GeeksDashboard): Guarded by an explicit warning confirmation before unlocking raw SQL query execution, vector index monitoring, and database table metrics.

Live Chat Stream (ChatPage): Test prompt ingestion and verify vector memory recalls directly from the UI.

pgVector Memory Storage: Dual-write pipeline storing raw .txt chunks on host storage while indexing 384-dim vector embeddings in Docker Postgres using cosine distance (<=>).

🧹 Maintenance & Git Hygiene
Keep build caches and node modules untracked:

Bash
echo "node_modules/" >> .gitignore
echo ".vite/" >> .gitignore
