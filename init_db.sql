-- Enable the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Main Memory Storage Table
CREATE TABLE IF NOT EXISTS memory_db (
    doc_id          VARCHAR(64) PRIMARY KEY,
    parent_id       VARCHAR(64) NOT NULL,          -- Character ID or group container
    session_id      VARCHAR(64) NOT NULL,          -- Specific chat thread/branch
    persona         VARCHAR(128) DEFAULT 'User',   -- Active chatter persona
    text_id         VARCHAR(64) NOT NULL,          -- Local text file reference/filename
    date_id         DATE DEFAULT CURRENT_DATE,     -- Easy date filtering
    time_id         TIME DEFAULT CURRENT_TIME,     -- Time of chunk creation
    created_at      TIMESTAMPTZ DEFAULT NOW(),     -- Full precise timestamp
    content         TEXT NOT NULL,                 -- Extracted text chunk
    embedding       vector(384),                   -- Vector representation (384 dimensions)
    metadata        JSONB DEFAULT '{}'::jsonb      -- Flexible metadata tag storage
);

-- 2. Session State Persistence Table (For restoring active chats/cards on refresh)
CREATE TABLE IF NOT EXISTS mimir_sessions (
    session_id      VARCHAR(64) PRIMARY KEY,
    character_name  VARCHAR(128) NOT NULL,
    active_skin     VARCHAR(64) DEFAULT 'default',
    system_prompt   TEXT,
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    session_data    JSONB DEFAULT '{}'::jsonb
);

-- 3. HNSW Index for High-Speed Cosine Vector Queries
CREATE INDEX IF NOT EXISTS idx_memory_embedding 
ON memory_db 
USING hnsw (embedding vector_cosine_ops);

-- 4. B-Tree Indexes for Relational Filters
CREATE INDEX IF NOT EXISTS idx_memory_session ON memory_db(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_parent ON memory_db(parent_id);
CREATE INDEX IF NOT EXISTS idx_memory_date ON memory_db(date_id);

-- 5. GIN Index for High-Performance JSONB Metadata Searches
CREATE INDEX IF NOT EXISTS idx_memory_metadata ON memory_db USING gin (metadata);
