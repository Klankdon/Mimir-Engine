import logging
from sentence_transformers import SentenceTransformer
from db import query_similar_memories

logger = logging.getLogger("mimir-injector")

# Load the model into memory once when the app starts
# This specific model outputs the exact 384-dimension vector your database expects
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

async def get_embedding(text: str) -> list[float]:
    """
    Converts raw text into a 384-dimension vector array using a local CPU-optimized model.
    """
    # encode() returns a numpy array, we convert it to a standard Python list of floats
    vector = embedding_model.encode(text)
    return vector.tolist()


async def inject_memory_context(session_id: str, payload: dict) -> dict:
    """
    Intercepts the OpenAI-formatted payload, vectorizes the prompt, 
    queries pgvector for relevant context, and injects it.
    """
    messages = payload.get("messages", [])
    if not messages:
        return payload

    latest_user_msg = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"), 
        None
    )
    
    if not latest_user_msg:
        return payload
        
    # 1. Math conversion: Text -> 384 floats
    query_vector = await get_embedding(latest_user_msg)

    # 2. Vector distance search in Postgres
    memories = await query_similar_memories(session_id, query_vector, limit=3)

    if memories:
        context_blocks = "\n".join([f"- {m['content']}" for m in memories])
        system_injection = {
            "role": "system",
            "content": f"Context recalled from past interactions:\n{context_blocks}\n\nUse this context to inform your response."
        }
        
        messages.insert(-1, system_injection)
        payload["messages"] = messages
        
        logger.info(f"Injected {len(memories)} memories into payload for session {session_id}")

    return payload
