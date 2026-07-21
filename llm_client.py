import json
import httpx
from typing import AsyncGenerator

# Pre-configured Provider Profiles
PROVIDERS = {
    "Local (Ollama)": {
        "base_url": "http://host.docker.internal:11434/v1](http://host.docker.internal:11434/v1",
        "requires_key": False,
        "default_model": "llama3"
    },
    "Local (KoboldCPP / vLLM)": {
        "base_url": "http://localhost:5001/v1",
        "requires_key": False,
        "default_model": "default"
    },
    "OpenRouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "requires_key": True,
        "default_model": "anthropic/claude-3.5-sonnet"
    },
    "OpenAI": {
        "base_url": "https://api.openai.com/v1",
        "requires_key": True,
        "default_model": "gpt-4o"
    }
}

async def stream_llm_response(
    provider_name: str,
    api_key: str,
    model_name: str,
    messages: list[dict],
    temperature: float = 0.7
) -> AsyncGenerator[str, None]:
    """Streams text back token-by-token from any OpenAI-compatible backend."""
    
    provider = PROVIDERS.get(provider_name, PROVIDERS["Local (Ollama)"])
    base_url = provider["base_url"].rstrip("/")
    url = f"{base_url}/chat/completions"
    
    headers = {"Content-Type": "application/json"}
    if provider["requires_key"] and api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    elif provider_name == "OpenRouter":
        headers["Authorization"] = f"Bearer {api_key}"
        headers["HTTP-Referer"] = "http://localhost:59056"
        headers["X-Title"] = "Mimir Engine"

    payload = {
        "model": model_name or provider["default_model"],
        "messages": messages,
        "temperature": temperature,
        "stream": True
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as response:
            if response.status_code != 200:
                err_body = await response.aread()
                yield f"[API Error {response.status_code}: {err_body.decode('utf-8')}]"
                return

            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    break
                
                try:
                    data = json.loads(data_str)
                    token = data["choices"][0]["delta"].get("content", "")
                    if token:
                        yield token
                except json.JSONDecodeError:
                    continue
