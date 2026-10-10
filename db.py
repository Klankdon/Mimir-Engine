from dotenv import load_dotenv; load_dotenv()

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import asyncpg

logger = logging.getLogger("mimir-db")

DB_HOST = os.getenv("DB_HOST", "mimir-db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "mimir_db")
DB_USER = os.getenv("DB_USER", "mimir_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mimir_secret_password")

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

STORAGE_DIR = os.path.join(os.getcwd(), "storage", "docids")
db_pool: Optional[asyncpg.Pool] = None


async def init_db_and_storage():
    """
    Initializes storage directory, creates connection pool, 
    and sets up database schema + migrations on app startup.
    """
    global db_pool
    
    os.makedirs(STORAGE_DIR, exist_ok=True)
    
    try:
        db_pool = await asyncpg.create_pool(
            dsn=DATABASE_URL,
            min_size=2,
            max_size=10,
            timeout=30.0
        )
        logger.info("Successfully connected to PostgreSQL connection pool.")
    except Exception as e:
        logger.error(f"Failed to connect to database at {DB_HOST}:{DB_PORT}: {e}")
        raise e

    async with db_pool.acquire() as conn:
        # 1. Enable vector extension for pgvector
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # 2. Vector memory table & indexes
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_db (
                doc_id          VARCHAR(64) PRIMARY KEY,
                parent_id       VARCHAR(64) NOT NULL,
                session_id      VARCHAR(64) NOT NULL,
                persona         VARCHAR(128) DEFAULT 'User',
                text_id         VARCHAR(64) NOT NULL,
                date_id         DATE DEFAULT CURRENT_DATE,
                time_id         TIME DEFAULT CURRENT_TIME,
                created_at      TIMESTAMPTZ DEFAULT NOW(),
                content         TEXT NOT NULL,
                embedding       vector(384),
                metadata        JSONB DEFAULT '{}'::jsonb
            );
            CREATE INDEX IF NOT EXISTS idx_memory_session ON memory_db(session_id);
            CREATE INDEX IF NOT EXISTS idx_memory_parent ON memory_db(parent_id);
            CREATE INDEX IF NOT EXISTS idx_memory_date ON memory_db(date_id);
        """)

        # 3. Upstream providers & target_role multi-model router tables
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
                target_role VARCHAR(32) DEFAULT 'chat',
                context_length INT DEFAULT 8192,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(provider_id, model_name)
            );

            ALTER TABLE upstream_models 
            ADD COLUMN IF NOT EXISTS target_role VARCHAR(32) DEFAULT 'chat';

            CREATE INDEX IF NOT EXISTS idx_upstream_models_role 
            ON upstream_models(target_role) 
            WHERE is_active = true;
        """)
        logger.info("Database schema and target_role indexes verified.")


async def get_upstream_by_role(role: str = "chat"):
    """
    Fetches active upstream provider configuration and model parameters 
    matching target_role ('chat', 'vibe', 'agent').
    Falls back to 'chat' role if requested target is unassigned.
    """
    if not db_pool:
        return None

    query = """
        SELECT 
            m.model_name,
            m.context_length,
            m.target_role,
            p.base_url,
            p.api_key
        FROM upstream_models m
        JOIN upstream_providers p ON m.provider_id = p.id
        WHERE m.target_role = $1 
          AND m.is_active = true 
          AND p.enabled = true
        ORDER BY m.created_at DESC
        LIMIT 1;
    """
    async with db_pool.acquire() as conn:
        record = await conn.fetchrow(query, role)
        
        if not record and role != "chat":
            record = await conn.fetchrow(query, "chat")
            
        return dict(record) if record else None


async def save_memory_chunk(
    doc_id: str, 
    parent_id: str, 
    session_id: str, 
    persona: str, 
    text_id: str, 
    content: str, 
    embedding: list[float], 
    metadata: dict = None
):
    """Saves text file to disk and inserts vector record into memory_db."""
    if not db_pool:
        raise RuntimeError("Database pool is not initialized.")

    file_path = os.path.join(STORAGE_DIR, f"{text_id}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    async with db_pool.acquire() as conn:
        now = datetime.now()
        vector_str = f"[{','.join(map(str, embedding))}]" if embedding else None
        
        insert_query = """
        INSERT INTO memory_db (
            doc_id, parent_id, session_id, persona, text_id,
            date_id, time_id, content, embedding, metadata
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::vector, $10::jsonb)
        ON CONFLICT (doc_id) DO UPDATE SET
            content = EXCLUDED.content,
            embedding = EXCLUDED.embedding;
        """
        await conn.execute(
            insert_query,
            doc_id, parent_id, session_id, persona, text_id,
            now.date(), now.time(), content, vector_str, json.dumps(metadata or {})
        )


async def query_similar_memories(session_id: str, query_embedding: list[float], limit: int = 5):
    """Executes pgvector cosine distance search against memory_db."""
    if not db_pool:
        return []

    async with db_pool.acquire() as conn:
        vector_str = f"[{','.join(map(str, query_embedding))}]"
        
        query = """
        SELECT doc_id, text_id, content, (1 - (embedding <=> $1::vector)) AS similarity
        FROM memory_db
        WHERE session_id = $2
        ORDER BY embedding <=> $1::vector ASC
        LIMIT $3;
        """
        rows = await conn.fetch(query, vector_str, session_id, limit)
        return [dict(row) for row in rows]


async def close_db():
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Closed PostgreSQL connection pool.")
