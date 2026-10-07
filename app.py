from dotenv import load_dotenv; load_dotenv()
import os
import json
import uuid
import logging
import httpx
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

import db
from db import init_db_and_storage, close_db, save_memory_chunk
from llm_client import inject_memory_context, get_embedding as generate_embedding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mimir-proxy")

http_client: httpx.AsyncClient = None
log_clients = set()

async def broadcast_log(level: str, message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = json.dumps({"timestamp": timestamp, "level": level, "message": message})
    for client_queue in list(log_clients):
        await client_queue.put(log_entry)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    logger.info("Starting Mimir Engine lifespan...")
    await init_db_and_storage()
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0))
    yield
    logger.info("Closing HTTP proxy pool and database connections...")
    await http_client.aclose()
    await close_db()

app = FastAPI(
    title="Mimir Engine // Middleware Proxy",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def verify_proxy_key(credentials: HTTPAuthorizationCredentials = None):
    # If no global proxy secret is enforced, pass through. 
    # Otherwise, validate credentials.credentials against your env/db secret.
    proxy_secret = os.getenv("MIMIR_PROXY_SECRET")
    if proxy_secret and (not credentials or credentials.credentials != proxy_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Mimir proxy API key",
        )
    return credentials

@app.get("/api/logs/stream")
async def stream_logs(request: Request):
    client_queue = asyncio.Queue()
    log_clients.add(client_queue)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                log_entry = await client_queue.get()
                yield f"data: {log_entry}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            log_clients.remove(client_queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/providers")
async def get_providers():
    if not db.db_pool:
        raise HTTPException(status_code=500, detail="Database pool not initialized")
    
    async with db.db_pool.acquire() as conn:
        query = """
            SELECT 
                p.id::text,
                p.name,
                p.base_url AS "baseUrl",
                p.api_key AS "apiKey",
                p.enabled,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'id', m.id::text, 
                            'modelName', m.model_name, 
                            'friendlyName', m.friendly_name,
                            'contextLength', m.context_length,
                            'isActive', m.is_active
                        )
                    ) FILTER (WHERE m.id IS NOT NULL), '[]'
                ) AS models
            FROM upstream_providers p
            LEFT JOIN upstream_models m ON p.id = m.provider_id
            GROUP BY p.id;
        """
        rows = await conn.fetch(query)
        return [dict(row) for row in rows]

@app.post("/api/providers")
async def add_provider(request: Request):
    if not db.db_pool:
        raise HTTPException(status_code=500, detail="Database pool not initialized")
    
    data = await request.json()
    
    async with db.db_pool.acquire() as conn:
        async with conn.transaction():
            provider_row = await conn.fetchrow("""
                INSERT INTO upstream_providers (name, base_url, api_key, enabled)
                VALUES ($1, $2, $3, $4)
                RETURNING id::text;
            """, data['name'], data['baseUrl'], data.get('apiKey', ''), data.get('enabled', True))
            
            provider_id = provider_row['id']
            
            if 'models' in data and isinstance(data['models'], list):
                for model in data['models']:
                    await conn.execute("""
                        INSERT INTO upstream_models (provider_id, model_name, friendly_name)
                        VALUES ($1::uuid, $2, $3)
                        ON CONFLICT (provider_id, model_name) DO UPDATE
                        SET friendly_name = EXCLUDED.friendly_name;
                    """, provider_id, model.get('modelName'), model.get('friendlyName', model.get('modelName')))

    logger.info(f"Registered upstream provider: {data.get('name')} ({provider_id})")
    return {"status": "success", "id": provider_id}

@app.delete("/api/providers/{provider_id}")
async def delete_provider(provider_id: str):
    if not db.db_pool:
        raise HTTPException(status_code=500, detail="Database pool not initialized")
        
    async with db.db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM upstream_providers WHERE id = $1::uuid;", provider_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Provider not found")

    return {"status": "deleted", "id": provider_id}

@app.get("/api/providers/{provider_id}/test")
async def test_provider_connection(provider_id: str):
    if not db.db_pool:
        raise HTTPException(status_code=500, detail="Database pool not initialized")
        
    async with db.db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT name, base_url, api_key 
            FROM upstream_providers 
            WHERE id = $1::uuid;
        """, provider_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="Provider not found")
            
    base_url = row["base_url"].rstrip("/")
    api_key = row["api_key"]
    
    if base_url.endswith("/v1"):
        target_url = f"{base_url}/models"
    elif base_url.endswith("/chat/completions"):
        target_url = base_url.replace("/chat/completions", "/models")
    else:
        target_url = f"{base_url}/v1/models"
        
    headers = {
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:59056",
        "X-Title": "Mimir Engine"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        
    try:
        response = await http_client.get(target_url, headers=headers, timeout=10.0)
        if response.status_code == 200:
            return {"status": "success", "message": f"Successfully connected to {row['name']}!"}
        else:
            return {"status": "error", "message": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        logger.error(f"Provider test connection failed for {row['name']}: {e}")
        return {"status": "error", "message": str(e)}
