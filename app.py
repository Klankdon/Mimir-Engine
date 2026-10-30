from dotenv import load_dotenv; load_dotenv()
import os
import json
import uuid
import logging
import httpx
import asyncio
import aiosqlite
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from importers import scan_directives_directory

security = HTTPBearer(auto_error=False)

import db
from db import init_db_and_storage, close_db, save_memory_chunk
from llm_client import inject_memory_context, get_embedding as generate_embedding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mimir-proxy")

SYSTEM_DB_PATH = os.getenv("SYSTEM_DB_PATH", os.path.join(os.getcwd(), "system.db"))
http_client: httpx.AsyncClient = None
log_clients = set()

# Mimir 3-Tier Multi-Target Route Mapping
MODEL_ROLE_MAP = {
    "mimir-proxy": "chat",
    "mimir-chat": "chat",
    "mimir-default": "chat",
    "mimir-vibe": "vibe",
    "vibe": "vibe",
    "mimir-agent": "agent",
    "agent": "agent",
}

async def get_system_db():
    conn = await aiosqlite.connect(SYSTEM_DB_PATH)
    conn.row_factory = aiosqlite.Row
    return conn

async def init_system_db():
    async with await get_system_db() as conn:
        await conn.execute("PRAGMA foreign_keys = ON;")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS upstream_providers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                base_url TEXT NOT NULL,
                api_key TEXT DEFAULT '',
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (DATETIME('now'))
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS upstream_models (
                id TEXT PRIMARY KEY,
                provider_id TEXT NOT NULL,
                model_name TEXT NOT NULL,
                friendly_name TEXT,
                target_role TEXT DEFAULT 'chat',
                context_length INTEGER DEFAULT 8192,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (DATETIME('now')),
                UNIQUE(provider_id, model_name),
                FOREIGN KEY(provider_id) REFERENCES upstream_providers(id) ON DELETE CASCADE
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT DEFAULT 'idle',
                description TEXT,
                config TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (DATETIME('now'))
            );
        """)
        # Workspace Persistence Table to prevent tab-switching state loss
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS workspace_sessions (
                session_key TEXT PRIMARY KEY,
                tab_name TEXT NOT NULL,
                state_data TEXT DEFAULT '{}',
                updated_at TEXT DEFAULT (DATETIME('now'))
            );
        """)
        await conn.commit()

    # Automatically scan /directives folder and sync agent JSON files into system.db
    directives = scan_directives_directory("directives")
    if directives:
        async with await get_system_db() as conn:
            for d in directives:
                await conn.execute("""
                    INSERT INTO agents (id, name, role, status, description, config)
                    VALUES (?, ?, ?, 'idle', ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        role = excluded.role,
                        description = excluded.description,
                        config = excluded.config;
                """, (
                    d["id"],
                    d["name"],
                    d["role"],
                    d["description"],
                    json.dumps(d["config"])
                ))
            await conn.commit()
        logger.info(f"Successfully synced {len(directives)} agent directives from /directives into system.db")

async def broadcast_log(level: str, message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = json.dumps({"timestamp": timestamp, "level": level, "message": message})
    for client_queue in list(log_clients):
        await client_queue.put(log_entry)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    logger.info("Starting Mimir Engine lifespan...")
    await init_system_db()
    await init_db_and_storage()
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0))
    yield
    logger.info("Closing HTTP proxy pool and database connections...")
    await http_client.aclose()
    await close_db()

app = FastAPI(
    title="Mimir Engine // Middleware Proxy",
    version="2.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def verify_proxy_key(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    proxy_secret = os.getenv("MIMIR_PROXY_SECRET")
    if proxy_secret and proxy_secret != "your_secure_proxy_key_here":
        if not credentials or credentials.credentials != proxy_secret:
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

# --- Workspace State Persistence Endpoints (Stops Tab-Switching Data Loss) ---

@app.get("/api/workspace/{session_key}")
async def get_workspace_state(session_key: str):
    async with await get_system_db() as conn:
        async with conn.execute("SELECT state_data FROM workspace_sessions WHERE session_key = ?;", (session_key,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return {"session_key": session_key, "state": {}}
            return {"session_key": session_key, "state": json.loads(row["state_data"])}

@app.post("/api/workspace/{session_key}")
async def save_workspace_state(session_key: str, request: Request):
    body = await request.json()
    tab_name = body.get("tabName", "vibe")
    state_payload = json.dumps(body.get("state", {}))
    
    async with await get_system_db() as conn:
        await conn.execute("""
            INSERT INTO workspace_sessions (session_key, tab_name, state_data, updated_at)
            VALUES (?, ?, ?, DATETIME('now'))
            ON CONFLICT(session_key) DO UPDATE SET
                tab_name = excluded.tab_name,
                state_data = excluded.state_data,
                updated_at = DATETIME('now');
        """, (session_key, tab_name, state_payload))
        await conn.commit()
        
    return {"status": "success", "session_key": session_key}

# --- Providers Endpoints ---

@app.get("/api/providers")
async def get_providers():
    async with await get_system_db() as conn:
        query = """
            SELECT 
                p.id,
                p.name,
                p.base_url AS baseUrl,
                p.api_key AS apiKey,
                p.enabled,
                COALESCE(
                    json_group_array(
                        json_object(
                            'id', m.id, 
                            'modelName', m.model_name, 
                            'friendlyName', m.friendly_name,
                            'targetRole', COALESCE(m.target_role, 'chat'),
                            'contextLength', m.context_length,
                            'isActive', m.is_active
                        )
                    ), '[]'
                ) AS models
            FROM upstream_providers p
            LEFT JOIN upstream_models m ON p.id = m.provider_id
            GROUP BY p.id;
        """
        async with conn.execute(query) as cursor:
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                item = dict(row)
                item['models'] = json.loads(item['models']) if item['models'] else []
                item['models'] = [m for m in item['models'] if m.get('id') is not None]
                results.append(item)
            return results

@app.post("/api/providers")
async def add_provider(request: Request):
    data = await request.json()
    provider_id = str(uuid.uuid4())
    
    async with await get_system_db() as conn:
        await conn.execute("""
            INSERT INTO upstream_providers (id, name, base_url, api_key, enabled)
            VALUES (?, ?, ?, ?, ?)
        """, (provider_id, data['name'], data['baseUrl'], data.get('apiKey', ''), 1 if data.get('enabled', True) else 0))
        
        if 'models' in data and isinstance(data['models'], list):
            for model in data['models']:
                model_id = str(uuid.uuid4())
                target_role = model.get('targetRole', 'chat').lower()
                if target_role not in ['chat', 'vibe', 'agent']:
                    target_role = 'chat'

                await conn.execute("""
                    INSERT INTO upstream_models (id, provider_id, model_name, friendly_name, target_role)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(provider_id, model_name) DO UPDATE SET
                        friendly_name = excluded.friendly_name,
                        target_role = excluded.target_role;
                """, (model_id, provider_id, model.get('modelName'), model.get('friendlyName', model.get('modelName')), target_role))

        await conn.commit()

    logger.info(f"Registered upstream provider: {data.get('name')} ({provider_id})")
    return {"status": "success", "id": provider_id}

@app.delete("/api/providers/{provider_id}")
async def delete_provider(provider_id: str):
    async with await get_system_db() as conn:
        cursor = await conn.execute("DELETE FROM upstream_providers WHERE id = ?;", (provider_id,))
        await conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Provider not found")

    return {"status": "deleted", "id": provider_id}

@app.get("/api/providers/{provider_id}/test")
async def test_provider_connection(provider_id: str):
    async with await get_system_db() as conn:
        async with conn.execute("SELECT name, base_url, api_key FROM upstream_providers WHERE id = ?;", (provider_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Provider not found")
            row_dict = dict(row)
            
    base_url = row_dict["base_url"].rstrip("/")
    api_key = row_dict["api_key"]
    
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
            return {"status": "success", "message": f"Successfully connected to {row_dict['name']}!"}
        else:
            return {"status": "error", "message": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        logger.error(f"Provider test connection failed for {row_dict['name']}: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/agents")
async def get_agents():
    async with await get_system_db() as conn:
        async with conn.execute("SELECT * FROM agents ORDER BY created_at DESC;") as cursor:
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                item = dict(row)
                item['config'] = json.loads(item['config']) if item['config'] else {}
                results.append(item)
            return results

@app.post("/api/agents")
async def create_agent(request: Request):
    data = await request.json()
    agent_id = str(uuid.uuid4())
    
    async with await get_system_db() as conn:
        await conn.execute("""
            INSERT INTO agents (id, name, role, status, description, config)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            agent_id,
            data.get('name'),
            data.get('role', 'janitor'),
            data.get('status', 'idle'),
            data.get('description', ''),
            json.dumps(data.get('config', {}))
        ))
        await conn.commit()
        
    return {"status": "success", "id": agent_id}

@app.post("/api/sql/query")
async def execute_raw_sql(request: Request):
    if not db.db_pool:
        raise HTTPException(status_code=500, detail="pgvector PostgreSQL pool not initialized")
    
    body = await request.json()
    sql_query = body.get("query", "").strip()
    
    if not sql_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    async with db.db_pool.acquire() as conn:
        try:
            if sql_query.lower().startswith("select") or sql_query.lower().startswith("with"):
                rows = await conn.fetch(sql_query)
                results = [dict(row) for row in rows]
                return {"status": "success", "columns": list(results[0].keys()) if results else [], "rows": results}
            else:
                status_tag = await conn.execute(sql_query)
                return {"status": "success", "message": f"Query executed successfully: {status_tag}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

@app.post("/v1/chat/completions")
async def proxy_chat_completions(request: Request, credentials: HTTPAuthorizationCredentials = Depends(verify_proxy_key)):
    payload = await request.json()
    requested_model = str(payload.get("model", "")).strip().lower()
    target_role = MODEL_ROLE_MAP.get(requested_model, "chat")
    
    await broadcast_log("INGRESS", f"Payload intercepted (Requested: '{requested_model}' -> Target Role: '{target_role}').")
    
    target_url = None
    api_key = ""
    upstream_model_name = None
    
    async with await get_system_db() as conn:
        async with conn.execute("""
            SELECT p.base_url, p.api_key, m.model_name
            FROM upstream_models m
            JOIN upstream_providers p ON m.provider_id = p.id
            WHERE m.target_role = ? AND m.is_active = 1 AND p.enabled = 1
            ORDER BY m.created_at DESC LIMIT 1;
        """, (target_role,)) as cursor:
            row = await cursor.fetchone()
            
        if not row and target_role != "chat":
            async with conn.execute("""
                SELECT p.base_url, p.api_key, m.model_name
                FROM upstream_models m
                JOIN upstream_providers p ON m.provider_id = p.id
                WHERE m.is_active = 1 AND p.enabled = 1
                ORDER BY m.created_at DESC LIMIT 1;
            """) as cursor:
                row = await cursor.fetchone()
                
        if not row:
            async with conn.execute("""
                SELECT base_url, api_key FROM upstream_providers 
                WHERE enabled = 1 
                ORDER BY created_at DESC LIMIT 1;
            """) as cursor:
                row = await cursor.fetchone()
                
        if row:
            row_dict = dict(row)
            base_url = row_dict["base_url"].rstrip("/")
            if base_url.endswith("/chat/completions"):
                target_url = base_url
            elif base_url.endswith("/v1"):
                target_url = f"{base_url}/chat/completions"
            else:
                target_url = f"{base_url}/v1/chat/completions"
            api_key = row_dict["api_key"]
            upstream_model_name = row_dict.get("model_name")

    if not target_url:
        err_msg = f"No active upstream provider configured for role '{target_role}'. Please add one in Integrations Hub."
        logger.error(err_msg)
        await broadcast_log("ERROR", err_msg)
        
        async def error_generator():
            yield f'data: {json.dumps({"error": err_msg})}\n\n'.encode("utf-8")
            
        return StreamingResponse(error_generator(), media_type="text/event-stream")

    if upstream_model_name:
        payload["model"] = upstream_model_name

    session_id = payload.get("user", "default_session")
    if not payload.get("model"):
        payload["model"] = "gpt-4o-mini"
    
    if target_role == "chat":
        await broadcast_log("VECTOR", f"Scanning pgvector for session: {session_id}")
        enriched_payload = await inject_memory_context(session_id, payload)
        await broadcast_log("INJECT", "Memory context woven into payload.")
    else:
        enriched_payload = payload

    headers = {
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:59056",
        "X-Title": "Mimir Engine"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    async def stream_generator():
        MAX_RETRIES = 2
        retry_count = 0
        success = False
        full_response_text = ""
        active_model = payload.get("model", "unknown-upstream")
        
        while retry_count <= MAX_RETRIES and not success:
            buffer = ""
            full_response_text = ""
            try:
                async with http_client.stream("POST", target_url, json=enriched_payload, headers=headers) as response:
                    if response.status_code >= 400:
                        error_body = await response.aread()
                        error_str = error_body.decode("utf-8", errors="ignore")
                        if "context_length_exceeded" in error_str or "exceeds" in error_str or response.status_code == 413:
                            if retry_count < MAX_RETRIES and len(enriched_payload.get("messages", [])) > 2:
                                enriched_payload["messages"].pop(1)
                                retry_count += 1
                                continue
                        raise HTTPException(status_code=response.status_code, detail=error_str)

                    success = True
                    async for chunk in response.aiter_bytes():
                        yield chunk
                        buffer += chunk.decode("utf-8", errors="ignore")
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if line.startswith("data: ") and line != "data: [DONE]":
                                try:
                                    data = json.loads(line[6:])
                                    delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    if delta:
                                        full_response_text += delta
                                except Exception:
                                    pass

                if full_response_text.strip() and target_role == "chat":
                    doc_id = str(uuid.uuid4())
                    text_id = f"msg_{int(datetime.now().timestamp())}"
                    embedding = await generate_embedding(full_response_text)
                    
                    await save_memory_chunk(
                        doc_id=doc_id,
                        parent_id=session_id,
                        session_id=session_id,
                        persona="Assistant",
                        text_id=text_id,
                        content=full_response_text,
                        embedding=embedding,
                        metadata={"source_model": active_model, "role": target_role}
                    )
            except Exception as e:
                if retry_count >= MAX_RETRIES or (isinstance(e, HTTPException) and e.status_code < 400):
                    break
                retry_count += 1
                await asyncio.sleep(1)

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

@app.api_route("/v1/{path:path}", methods=["GET", "POST"])
async def proxy_openai_routes(path: str, request: Request, credentials: HTTPAuthorizationCredentials = Depends(verify_proxy_key)):
    if path == "models" and request.method == "GET":
        return JSONResponse({
            "object": "list",
            "data": [
                {"id": "mimir-proxy", "object": "model", "created": 0, "owned_by": "mimir"},
                {"id": "mimir-vibe", "object": "model", "created": 0, "owned_by": "mimir"},
                {"id": "mimir-agent", "object": "model", "created": 0, "owned_by": "mimir"}
            ]
        })

    return JSONResponse(status_code=404, content={"error": "Endpoint not found in Mimir Engine"})

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = os.path.join("dist", full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse("dist/index.html")

if os.path.exists("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")
