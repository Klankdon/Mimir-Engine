import os
import json
import uuid
import aiosqlite

SYSTEM_DB_PATH = os.getenv("SYSTEM_DB_PATH", os.path.join(os.getcwd(), "system.db"))

async def get_system_db() -> aiosqlite.Connection:
    conn = await aiosqlite.connect(SYSTEM_DB_PATH)
    conn.row_factory = aiosqlite.Row
    return conn

async def init_system_db():
    async with await get_system_db() as conn:
        await conn.execute("PRAGMA foreign_keys = ON;")
        
        # Upstream Providers
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
        
        # Upstream Models
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
        
        # Background Agents
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
        await conn.commit()
