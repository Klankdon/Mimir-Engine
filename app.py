import os
import logging
from contextlib import asynccontextmanager
import asyncpg
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mimir-proxy")

# Database Connection Pool Global
db_pool: asyncpg.Pool = None
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/mimir")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    logger.info("Initializing PostgreSQL pool and database schemas...")
    db_pool = await asyncpg.create_pool(DATABASE_URL)

    # Bootstrapping schema setup
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS upstream_providers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                base_url VARCHAR(512) NOT NULL,
                api_key TEXT DEFAULT '',
                enabled BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS upstream_models (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                provider_id UUID NOT NULL REFERENCES upstream_providers(id) ON DELETE CASCADE,
                model_name VARCHAR(255) NOT NULL,
                friendly_name VARCHAR(255),
                context_length INT DEFAULT 8192,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(provider_id, model_name)
            );
        """)

    yield  # Application runs here

    logger.info("Closing database connection pool...")
    await db_pool.close()


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

@app.get("/api/providers")
async def get_providers():
    async with db_pool.acquire() as conn:
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
    data = await request.json()
    
    async with db_pool.acquire() as conn:
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
    async with db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM upstream_providers WHERE id = $1::uuid;", provider_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Provider not found")
            
    return {"status": "deleted", "id": provider_id}


# Mount static assets/frontend AFTER API routes
if os.path.exists("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")
