import os
from datetime import datetime
import psycopg2
from psycopg2.extras import Json, execute_values

# DB Connection Config matching docker-compose env
DB_HOST = os.getenv("DB_HOST", "mimir-db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "mimir_db")
DB_USER = os.getenv("DB_USER", "mimir_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mimir_secret_password")

# Raw Text Chunk Directory on Host/Container
STORAGE_DIR = os.path.join(os.getcwd(), "storage", "docids")


def get_db_connection():
  """Helper to create a fresh PostgreSQL connection."""
  return psycopg2.connect(
      host=DB_HOST,
      port=DB_PORT,
      dbname=DB_NAME,
      user=DB_USER,
      password=DB_PASSWORD,
  )


def init_db_and_storage():
  """Ensures local storage directory exists and initializes Postgres table."""
  # 1. Create text file directory
  os.makedirs(STORAGE_DIR, exist_ok=True)

  # 2. Initialize Postgres Table & pgvector extension
  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
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
  conn.commit()
  cursor.close()
  conn.close()


def save_memory_chunk(
    doc_id: str,
    parent_id: str,
    session_id: str,
    persona: str,
    text_id: str,
    content: str,
    embedding: list[float],
    metadata: dict = None,
):
  """1. Writes raw text chunk to disk: ./storage/docids/<text_id>.txt

  2. Writes structured record and vector array into Postgres.
  """
  # A. Write to local raw text folder
  file_path = os.path.join(STORAGE_DIR, f"{text_id}.txt")
  with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

  # B. Insert into Postgres
  conn = get_db_connection()
  cursor = conn.cursor()

  now = datetime.now()
  insert_query = """
        INSERT INTO memory_db (
            doc_id, parent_id, session_id, persona, text_id, 
            date_id, time_id, content, embedding, metadata
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (doc_id) DO UPDATE SET
            content = EXCLUDED.content,
            embedding = EXCLUDED.embedding;
    """

  cursor.execute(
      insert_query,
      (
          doc_id,
          parent_id,
          session_id,
          persona,
          text_id,
          now.date(),
          now.time(),
          content,
          embedding,
          Json(metadata or {}),
      ),
  )

  conn.commit()
  cursor.close()
  conn.close()


def query_similar_memories(
    session_id: str, query_embedding: list[float], limit: int = 5
):
  """Queries Postgres for closest vectors matching the session."""
  conn = get_db_connection()
  cursor = conn.cursor()

  # Uses pgvector's cosine distance operator (<=>)
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
  conn.close()
  return results


# ==========================================
# NEW HELPER FUNCTIONS FOR TELEMETRY & CHAT RECOVERY
# ==========================================


def get_db_telemetry() -> dict:
  """Fetches live DB statistics for the Dashboard HUD gauges."""
  try:
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Total DOCIDs (rows in memory_db)
    cursor.execute("SELECT COUNT(*) FROM memory_db;")
    doc_count = cursor.fetchone()[0]

    # 2. Database size on disk in Megabytes
    cursor.execute(
        "SELECT pg_database_size(%s) / (1024.0 * 1024.0);", (DB_NAME,)
    )
    db_size_mb = round(cursor.fetchone()[0], 2)

    cursor.close()
    conn.close()

    return {
        "doc_count": doc_count,
        "db_size_mb": db_size_mb,
        "status": "connected",
    }
  except Exception as e:
    return {"doc_count": 0, "db_size_mb": 0.0, "status": f"error: {str(e)}"}


def fetch_session_history(session_id: str) -> list[dict]:
  """Retrieves past messages for a given session_id to restore chat on refresh."""
  conn = get_db_connection()
  cursor = conn.cursor()

  query = """
        SELECT persona, content, created_at, metadata
        FROM memory_db
        WHERE session_id = %s
        ORDER BY created_at ASC;
    """

  cursor.execute(query, (session_id,))
  rows = cursor.fetchall()

  history = []
  for row in rows:
    persona, content, created_at, metadata = row
    is_user = persona.lower() in ["user", "you", "engineer"]
    history.append({
        "sender": persona,
        "text": content,
        "is_user": is_user,
        "timestamp": created_at.isoformat() if created_at else None,
    })

  cursor.close()
  conn.close()
  return history


def get_all_sessions() -> list[str]:
  """Lists all unique session IDs stored in memory_db."""
  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute(
      "SELECT DISTINCT session_id FROM memory_db ORDER BY session_id DESC;"
  )
  sessions = [r[0] for r in cursor.fetchall()]

  cursor.close()
  conn.close()
  return sessions
