import os
import json
import logging
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mimir-proxy")

app = FastAPI(title="Mimir Engine // Middleware Proxy", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROVIDERS_FILE = Path("providers.json")

def load_providers():
    if PROVIDERS_FILE.exists():
        try:
            with open(PROVIDERS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load providers.json: {e}")
    return []

def save_providers(providers):
    try:
        with open(PROVIDERS_FILE, "w") as f:
            json.dump(providers, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save providers.json: {e}")

# --- REST API Endpoints (Must be registered BEFORE static mounts) ---

@app.get("/api/providers")
async def get_providers():
    return load_providers()

@app.post("/api/providers")
async def add_provider(request: Request):
    data = await request.json()
    providers = load_providers()
    providers = [p for p in providers if p.get("id") != data.get("id")]
    providers.append(data)
    save_providers(providers)
    logger.info(f"Registered upstream provider: {data.get('name')}")
    return {"status": "success", "provider": data}

@app.patch("/api/providers/{provider_id}")
async def update_provider(provider_id: str, request: Request):
    data = await request.json()
    providers = load_providers()
    for p in providers:
        if str(p.get("id")) == str(provider_id):
            p.update(data)
            break
    save_providers(providers)
    return {"status": "updated"}

@app.delete("/api/providers/{provider_id}")
async def delete_provider(provider_id: str):
    providers = load_providers()
    providers = [p for p in providers if str(p.get("id")) != str(provider_id)]
    save_providers(providers)
    return {"status": "deleted"}

# --- Static File SPA Fallback ---
STATIC_DIR = Path("mimir-desktop/dist")
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
else:
    logger.warning("⚠️ 'mimir-desktop/dist' directory missing! Run 'npm run build' inside mimir-desktop.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
