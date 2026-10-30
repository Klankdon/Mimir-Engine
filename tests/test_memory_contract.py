"""Offline characterization of db.py; the driver below is not PostgreSQL."""

import contextlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch


def vector(first, second=0.0):
    return [first, second] + [0.0] * 382


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


class RecordingConnection:
    """Model only fixture row effects; reject SQL outside the declared contract."""

    def __init__(self):
        self.rows = {}
        self.execute_calls = []
        self.fetch_calls = []

    async def execute(self, statement, *args):
        sql = " ".join(statement.split())
        expect(sql.startswith("INSERT INTO memory_db ("), "expected memory insert")
        expect("ON CONFLICT (doc_id) DO UPDATE SET" in sql, "missing document upsert")
        expect("content = EXCLUDED.content" in sql, "upsert must replace current content")
        expect("embedding = EXCLUDED.embedding" in sql, "upsert must replace current vector")
        expect(len(args) == 10, "unexpected save bindings")
        self.execute_calls.append((sql, args))
        row = self.rows.setdefault(args[0], {
            "doc_id": args[0], "session_id": args[2], "text_id": args[4],
        })
        row.update(content=args[7], embedding=json.loads(args[8]) if args[8] else None)

    @staticmethod
    def cosine(left, right):
        denominator = math.sqrt(sum(x * x for x in left) * sum(x * x for x in right))
        expect(denominator > 0, "fixture vectors must be nonzero")
        return sum(x * y for x, y in zip(left, right)) / denominator

    async def fetch(self, statement, *args):
        sql = " ".join(statement.split())
        predicate = sql.partition(" WHERE ")[2].partition(" ORDER BY ")[0]
        expect(predicate == "session_id = $2", "exact session predicate is required")
        expect("ORDER BY embedding <=> $1::vector ASC" in sql, "expected cosine order")
        expect("LIMIT $3" in sql, "requested limit must be bound")
        expect(len(args) == 3, "unexpected query bindings")
        self.fetch_calls.append((sql, args))
        query, session, limit = json.loads(args[0]), args[1], args[2]
        scoped = [row for row in self.rows.values() if row["session_id"] == session]
        expect(all(row["embedding"] is not None for row in scoped),
            "NULL-vector/pruning behavior is outside this mock fixture"
        )
        ranked = sorted(scoped, key=lambda row: self.cosine(row["embedding"], query), reverse=True)
        return [types.MappingProxyType({"doc_id": row["doc_id"], "text_id": row["text_id"],
            "content": row["content"], "similarity": self.cosine(row["embedding"], query)})
            for row in ranked[:limit]]


class RecordingPool:
    def __init__(self, connection):
        self.connection = connection

    @contextlib.asynccontextmanager
    async def acquire(self):
        yield self.connection


class MemoryContractTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="mimir-contract-")
        self.addCleanup(temporary.cleanup)
        self.storage = Path(temporary.name)
        dotenv = types.ModuleType("dotenv")
        dotenv.load_dotenv = Mock(return_value=False)
        asyncpg = types.ModuleType("asyncpg")
        asyncpg.Pool = object
        asyncpg.create_pool = AsyncMock(side_effect=AssertionError("live pool creation forbidden"))
        self.modules = {
            "dotenv": dotenv,
            "asyncpg": asyncpg,
        }

    def load_db(self):
        with patch.dict(sys.modules, self.modules):
            spec = importlib.util.spec_from_file_location("db", Path("db.py"))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

    async def test_uninitialized_pool_raises(self):
        db = self.load_db()
        with self.assertRaises(RuntimeError):
            await db.query_similar_memories(vector(1.0), "session-a")

    async def test_upsert_replaces_content_and_vector(self):
        db = self.load_db()
        conn = RecordingConnection()
        db.pool = RecordingPool(conn)

        await db.save_memory_chunk(
            doc_id="doc-1", user_id="user-1", session_id="session-a",
            file_path=str(self.storage / "a.txt"), text_id="txt-1",
            chunk_index=0, total_chunks=1, content="Provider A selected",
            embedding=vector(1.0, 0.0), metadata={"provider": "A"}
        )
        await db.save_memory_chunk(
            doc_id="doc-1", user_id="user-1", session_id="session-a",
            file_path=str(self.storage / "a.txt"), text_id="txt-1",
            chunk_index=0, total_chunks=1, content="Provider B corrected",
            embedding=vector(0.0, 1.0), metadata={"provider": "B"}
        )

        results = await db.query_similar_memories(vector(0.0, 1.0), "session-a")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"], "Provider B corrected")

    async def test_session_isolation(self):
        db = self.load_db()
        conn = RecordingConnection()
        db.pool = RecordingPool(conn)

        await db.save_memory_chunk(
            doc_id="doc-a", user_id="user-1", session_id="session-a",
            file_path=str(self.storage / "a.txt"), text_id="txt-a",
            chunk_index=0, total_chunks=1, content="Session A context",
            embedding=vector(1.0, 0.0), metadata={}
        )
        await db.save_memory_chunk(
            doc_id="doc-b", user_id="user-1", session_id="session-b",
            file_path=str(self.storage / "b.txt"), text_id="txt-b",
            chunk_index=0, total_chunks=1, content="Session B context",
            embedding=vector(1.0, 0.0), metadata={}
        )

        results_a = await db.query_similar_memories(vector(1.0, 0.0), "session-a")
        results_b = await db.query_similar_memories(vector(1.0, 0.0), "session-b")

        self.assertEqual(len(results_a), 1)
        self.assertEqual(results_a[0]["doc_id"], "doc-a")
        self.assertEqual(len(results_b), 1)
        self.assertEqual(results_b[0]["doc_id"], "doc-b")


if __name__ == "__main__":
    unittest.main()