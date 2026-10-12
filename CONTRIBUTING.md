Markdown
# Contributing to Mimir Engine

Thank you for your interest in contributing to Mimir Engine! Whether you are fixing bugs, improving documentation, adding new frontend HUD features, or optimizing backend context retrieval, your help is welcome.

---

## 🛠️ Local Development Setup

### Prerequisites
* **Git**
* **Docker & Docker Compose** (Recommended for local database setup)
* **Python 3.10+** (For backend development)
* **Node.js 20+** & **npm** (For Svelte 5 frontend development)

---

## 🚀 Getting Started

1. **Fork and clone the repository:**
   ```bash
   git clone [https://github.com/YOUR-USERNAME/Mimir-Engine.git](https://github.com/YOUR-USERNAME/Mimir-Engine.git)
   cd Mimir-Engine
Spin up the local PostgreSQL (pgvector) database:

Bash
docker compose up -d mimir_db
Set up the Python Backend Environment:

Bash
python -m venv venv
# Linux/macOS:
source venv/bin/activate
# Windows:
.\venv\Scripts\activate

pip install -r requirements.txt
Set up the Svelte Frontend:

Bash
cd mimir-desktop
npm install
npm run dev
💡 Key Areas for Contribution
Frontend (Svelte 5 / UI): Custom HUD themes, layout improvements, and LLM chat provider interface polish.

Backend (FastAPI & pgvector): API endpoint optimization, vector similarity tuning, and SillyTavern extension hook integrations.

Documentation & Launchers: Enhancing deployment scripts (start.bat, start.sh) and setup guides.

📋 Pull Request Process
Create a Feature Branch:

Bash
git checkout -b feature/your-feature-name
Commit Your Changes:
Keep commit messages clear and concise.

Bash
git commit -m "feat: add custom theme engine presets"
Test Locally:
Verify that docker compose up --build completes without errors and the FastAPI backend links cleanly with mimir_db.

Submit a PR:
Push your branch to GitHub and open a Pull Request against the main branch with a summary of your changes.
