import logging
from db import query_similar_memories

logger = logging.getLogger("mimir-injector")

async def get_embedding(text: str) -> list[float]:
    """
    Generate a 384-dimension vector for the incoming prompt.
    NOTE: Replace this placeholder with your actual embedding logic 
    (e.g., calling a local SentenceTransformer like all-MiniLM-L6-v2, 
    or an external embedding API).
    """
    return [0.0] * 384  # Placeholder matching pgvector(384)


async def inject_memory_context(session_id: str, payload: dict) -> dict:
    """
    Intercepts the OpenAI-formatted payload, queries pgvector for relevant
    past context, and injects it into the messages array before sending upstream.
    """
    messages = payload.get("messages", [])
    if not messages:
        return payload

    # Extract the latest user query
    latest_user_msg = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"), 
        None
    )
    
    if not latest_user_msg:
        return payload
        
    # 1. Vectorize the incoming prompt
    query_vector = await get_embedding(latest_user_msg)

    # 2. Fetch similar past memories from pgvector (db.py)
    memories = await query_similar_memories(session_id, query_vector, limit=3)

    if memories:
        # 3. Format the retrieved memories
        context_blocks = "\n".join([f"[{m['text_id']}]: {m['content']}" for m in memories])
        system_injection = {
            "role": "system",
            "content": f"Context recalled from past interactions:\n{context_blocks}\n\nUse this context to inform your response."
        }
        
        # 4. Inject the system prompt right before the latest user message
        messages.insert(-1, system_injection)
        payload["messages"] = messages
        
        logger.info(f"SubSurface Vector: Injected {len(memories)} memories into payload for session {session_id}")

    return payload
