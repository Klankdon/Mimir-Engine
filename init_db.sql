-- Enable the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Main Memory Storage Table
CREATE TABLE IF NOT EXISTS memory_db (
    doc_id          VARCHAR(64) PRIMARY KEY,
    parent_id       VARCHAR(64) NOT NULL,          -- Character ID or group container
    session_id      VARCHAR(64) NOT NULL,          -- Specific chat thread/branch
    persona         VARCHAR(128) DEFAULT 'User',   -- Active chatter persona
    text_id         VARCHAR(64) NOT NULL,          -- Local text file reference/filename
    date_id         DATE DEFAULT CURRENT_DATE,     -- Easy date filtering (e.g. WHERE date_id >= '2026-07-01')
    time_id         TIME DEFAULT CURRENT_TIME,     -- Time of chunk creation
    created_at      TIMESTAMPTZ DEFAULT NOW(),     -- Full precise timestamp
    content         TEXT NOT NULL,                 -- Extracted text chunk
    embedding       vector(384),                   -- Vector representation (384 dimensions)
    metadata        JSONB DEFAULT '{}'::jsonb      -- Flexible metadata tag storage
);

-- Index for high-speed vector similarity queries (Cosine Distance)
CREATE INDEX IF NOT EXISTS idx_memory_embedding 
ON memory_db 
USING hnsw (embedding vector_cosine_ops);

-- B-tree indexes for fast filtering by session, parent, and dates
CREATE INDEX IF NOT EXISTS idx_memory_session ON memory_db(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_parent ON memory_db(parent_id);
CREATE INDEX IF NOT EXISTS idx_memory_date ON memory_db(date_id);
