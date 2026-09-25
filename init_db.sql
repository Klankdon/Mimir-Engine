CREATE EXTENSION IF NOT EXISTS vector;

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

CREATE INDEX IF NOT EXISTS idx_memory_embedding 
ON memory_db 
USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_memory_session ON memory_db(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_parent ON memory_db(parent_id);
CREATE INDEX IF NOT EXISTS idx_memory_date ON memory_db(date_id);
