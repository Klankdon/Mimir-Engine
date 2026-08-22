import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import execute_values, Json
from datetime import datetime

# DB Connection Config matching docker-compose env
DB_HOST = os.getenv("DB_HOST", "mimir-db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "mimir_db")
DB_USER = os.getenv("DB_USER", "mimir_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mimir_secret_password")

# Raw Text Chunk Directory on Host/Container
STORAGE_DIR = os.path.join(os.getcwd(), "storage", "docids")

# Global Connection Pool
db_pool = None

def init_db_and_storage():
    """Ensures local storage directory exists, creates pool, and initializes Postgres tables."""
    global db_pool
    os.makedirs(STORAGE_DIR, exist_ok=True)

    # Initialize Threaded Connection Pool (min 1, max 10 active connections)
    if db_pool is None:
        db_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )

    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Memory Table
        cursor.execute("""
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

        # Upstream Provider & Model Tables
        cursor.execute("""
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

        conn.commit()
        cursor.close()
    finally:
        db_pool.putconn(conn)

def save_memory_chunk(doc_id: str, parent_id: str, session_id: str, persona: str, text_id: str, content: str, embedding: list[float], metadata: dict = None):
    """
    1. Writes raw text chunk to disk: ./storage/docids/<text_id>.txt
    2. Writes structured record and vector array into Postgres using pooled connection.
    """
    # A. Write to local raw text folder
    file_path = os.path.join(STORAGE_DIR, f"{text_id}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    # B. Insert into Postgres
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        now = datetime.now()
        insert_query = """
        INSERT INTO memory_db (
            doc_id, parent_id, session_id, persona, text_id,
            date_id, time_id, content, embedding, metadata
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (doc_id) DO UPDATE SET
            content = EXCLUDED.content,
            embedding = EXCLUDED.embedding;
        """
        cursor.execute(insert_query, (
            doc_id, parent_id, session_id, persona, text_id,
            now.date(), now.time(), content, embedding, Json(metadata or {})
        ))
        conn.commit()
        cursor.close()
    finally:
        db_pool.putconn(conn)

def query_similar_memories(session_id: str, query_embedding: list[float], limit: int = 5):
    """Queries Postgres for closest vectors matching the session using pooled connection."""
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        query = """
        SELECT doc_id, text_id, content, (1 - (embedding <=> %s::vector)) AS similarity
        FROM memory_db
        WHERE session_id = %s
        ORDER BY embedding <=> %s::vector ASC
        LIMIT %s;
        """
        cursor.execute(query, (query_embedding, session_id, query_embedding, limit))
        results = cursor.fetchall()
        cursor.close()
        return results
    finally:
        db_pool.putconn(conn)
