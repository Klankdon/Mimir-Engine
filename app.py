from dotenv import load_dotenv; load_dotenv()
import os
import json
import logging
import httpx
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import db
from db import init_db_and_storage, close_db
from llm_client import inject_memory_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mimir-proxy")

http_client: httpx.AsyncClient = None

# Global set to hold active SSE client queues for the dashboard
log_clients = set()

async def broadcast_log(level: str, message: str):
    """Pushes live log events to all connected UI clients."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = json.dumps({"timestamp": timestamp, "level": level, "message": message})
    
    # Broadcast to all active dashboard tabs
    for client_queue in list(log_clients):
        await client_queue.put(log_entry)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    logger.info("Starting Mimir Engine lifespan...")
    
    # Initialize Postgres schemas and asyncpg pool
    await init_db_and_storage()
    
    # Start HTTP Proxy Pool for upstream streaming
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0))

    yield  # Server execution block

    # Graceful shutdown
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


# --- REST API Endpoints ---

@app.get("/api/logs/stream")
async def stream_logs(request: Request):
    """SSE Endpoint for the Geeks Dashboard to listen to."""
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
            # 1. Insert Provider
            provider_row = await conn.fetchrow("""
                INSERT INTO upstream_providers (name, base_url, api_key, enabled)
                VALUES ($1, $2, $3, $4)
                RETURNING id::text;
            """, data['name'], data['baseUrl'], data.get('apiKey', ''), data.get('enabled', True))
            
            provider_id = provider_row['id']
            
            # 2. Insert any initially defined models
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
    
    # Intelligently resolve the /models endpoint based on the saved base_url
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
        # Ping the provider's /models endpoint to verify authentication and uptime
        response = await http_client.get(target_url, headers=headers, timeout=10.0)
        
        if response.status_code == 200:
            return {"status": "success", "message": f"Successfully connected to {row['name']}!"}
        else:
            return {"status": "error", "message": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        logger.error(f"Provider test connection failed for {row['name']}: {e}")
        return {"status": "error", "message": str(e)}
        
# --- OpenAI Compatible Proxy Routes ---

@app.api_route("/v1/{path:path}", methods=["GET", "POST"])
async def proxy_openai_routes(path: str, request: Request):
    # 1. Mock the models endpoint so Agnai / SillyTavern connection tests pass
    if path == "models" and request.method == "GET":
        return JSONResponse({
            "object": "list",
            "data": [{"id": "mimir-default", "object": "model", "created": 0, "owned_by": "mimir"}]
        })

    # 2. Intercept and inject vector memory for chat completions
    if path == "chat/completions" and request.method == "POST":
        payload = await request.json()
        
        # Broadcast Ingress
        await broadcast_log("INGRESS", "Payload intercepted from chat client.")
        
        # --- NEW: Extract and broadcast the active chat context ---
        messages = payload.get("messages", [])
        for msg in messages[-3:]:
            role = str(msg.get("role", "UNKNOWN")).upper()
            content = str(msg.get("content", ""))
            preview = (content[:150] + "...") if len(content) > 150 else content
            await broadcast_log("CHAT", f"[{role}] {preview}")
        # ----------------------------------------------------------
        
        # Inject Memory Context via local vector RAG
        session_id = payload.get("user", "default_session")
        
        # Broadcast Vector Activity
        await broadcast_log("VECTOR", f"Scanning pgvector for session: {session_id}")
        enriched_payload = await inject_memory_context(session_id, payload)
        
        await broadcast_log("INJECT", "Memory context woven into payload.")
        
        # Dynamically resolve enabled upstream provider from Postgres
        target_url = None
        api_key = ""
        
        if db.db_pool:
            async with db.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT base_url, api_key FROM upstream_providers 
                    WHERE enabled = true 
                    ORDER BY created_at DESC LIMIT 1;
                """)
                if row:
                    base_url = row["base_url"].rstrip("/")
                    if base_url.endswith("/chat/completions"):
                        target_url = base_url
                    elif base_url.endswith("/v1"):
                        target_url = f"{base_url}/chat/completions"
                    else:
                        target_url = f"{base_url}/v1/chat/completions"
                    api_key = row["api_key"]

        # Default fallback to OpenRouter if no active provider is saved in DB
        if not target_url:
            target_url = "https://openrouter.ai/api/v1/chat/completions"
            api_key = os.getenv("OPENROUTER_API_KEY", "")

        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:59056",
            "X-Title": "Mimir Engine"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        await broadcast_log("EGRESS", f"Forwarding payload to upstream: {target_url}")

        # Stream response chunks directly back to Agnai in real-time
        async def stream_generator():
            try:
                async with http_client.stream("POST", target_url, json=enriched_payload, headers=headers) as response:
                    async for chunk in response.aiter_bytes():
                        yield chunk
            except Exception as e:
                logger.error(f"Upstream streaming exception: {e}")
                await broadcast_log("ERROR", f"Upstream streaming exception: {str(e)}")
                err_payload = json.dumps({"error": str(e)}).encode("utf-8")
                yield f"data: {err_payload}\n\n".encode("utf-8")

        return StreamingResponse(stream_generator(), media_type="text/event-stream")

    return JSONResponse(status_code=404, content={"error": "Endpoint not found in Mimir Engine"})


# --- Static Assets & Frontend SPA Fallback ---

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = os.path.join("dist", full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse("dist/index.html")

if os.path.exists("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")
