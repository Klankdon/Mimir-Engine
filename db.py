import os
import json
from datetime import datetime
import aiosqlite

DB_PATH = os.getenv("DB_PATH", os.path.join(os.getcwd(), "mimir.db"))
STORAGE_DIR = os.path.join(os.getcwd(), "storage", "docids")


async def get_db_connection() -> aiosqlite.Connection:
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    return conn


async def init_db_and_storage():
    os.makedirs(STORAGE_DIR, exist_ok=True)

    async with await get_db_connection() as conn:
        await conn.execute("PRAGMA foreign_keys = ON;")

        # Memory storage table
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS memory_db (
            doc_id      TEXT PRIMARY KEY,
            parent_id   TEXT NOT NULL,
            session_id  TEXT NOT NULL,
            persona     TEXT DEFAULT 'User',
            text_id     TEXT NOT NULL,
            date_id     TEXT DEFAULT (DATE('now')),
            time_id     TEXT DEFAULT (TIME('now')),
            created_at  TEXT DEFAULT (DATETIME('now')),
            content     TEXT NOT NULL,
            embedding   TEXT,
            metadata    TEXT DEFAULT '{}'
        );
        """)

        await conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_session ON memory_db(session_id);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_parent ON memory_db(parent_id);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_date ON memory_db(date_id);")

        # Upstream Providers
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS upstream_providers (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            base_url    TEXT NOT NULL,
            api_key     TEXT DEFAULT '',
            enabled     INTEGER DEFAULT 1,
            created_at  TEXT DEFAULT (DATETIME('now'))
        );
        """)

        # Upstream Models
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS upstream_models (
            id             TEXT PRIMARY KEY,
            provider_id    TEXT NOT NULL,
            model_name     TEXT NOT NULL,
            friendly_name  TEXT,
            context_length INTEGER DEFAULT 8192,
            is_active      INTEGER DEFAULT 1,
            created_at     TEXT DEFAULT (DATETIME('now')),
            UNIQUE(provider_id, model_name),
            FOREIGN KEY(provider_id) REFERENCES upstream_providers(id) ON DELETE CASCADE
        );
        """)

        await conn.commit()


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
    file_path = os.path.join(STORAGE_DIR, f"{text_id}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    embedding_json = json.dumps(embedding)
    metadata_json = json.dumps(metadata or {})

    async with await get_db_connection() as conn:
        insert_query = """
        INSERT INTO memory_db (
            doc_id, parent_id, session_id, persona, text_id,
            date_id, time_id, content, embedding, metadata
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(doc_id) DO UPDATE SET
            content = excluded.content,
            embedding = excluded.embedding,
            metadata = excluded.metadata;
        """
        await conn.execute(
            insert_query,
            (
                doc_id, parent_id, session_id, persona, text_id,
                date_str, time_str, content, embedding_json, metadata_json
            )
        )
        await conn.commit()


def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5
    if not magnitude1 or not magnitude2:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)


async def query_similar_memories(session_id: str, query_embedding: list[float], limit: int = 5):
    async with await get_db_connection() as conn:
        query = """
        SELECT doc_id, text_id, content, embedding
        FROM memory_db
        WHERE session_id = ?;
        """
        async with conn.execute(query, (session_id,)) as cursor:
            rows = await cursor.fetchall()

        results = []
        for row in rows:
            row_dict = dict(row)
            stored_embedding = json.loads(row_dict["embedding"]) if row_dict["embedding"] else []
            similarity = _cosine_similarity(query_embedding, stored_embedding) if stored_embedding else 0.0
            
            results.append({
                "doc_id": row_dict["doc_id"],
                "text_id": row_dict["text_id"],
                "content": row_dict["content"],
                "similarity": similarity
            })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]


async def close_db():
    pass
