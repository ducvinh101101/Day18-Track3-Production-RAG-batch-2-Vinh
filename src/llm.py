import os
import sys
import httpx
from langchain_openai import ChatOpenAI

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LLM_KEY, LLM_URL, LLM_MODEL

def get_llm(max_tokens: int = None) -> ChatOpenAI:
    """
    Get ChatOpenAI instance configured for the custom LLM gateway.
    Uses custom http_client to avoid gateway blocking the default OpenAI SDK User-Agent.
    """
    api_key = LLM_KEY if LLM_KEY else "not-needed"
    kwargs = {
        "model": LLM_MODEL,
        "api_key": api_key,
        "base_url": LLM_URL,
        "http_client": httpx.Client(
            headers={"User-Agent": "python-httpx/0.27.0"},
            timeout=10.0
        ),
        "max_retries": 0,
        "timeout": 10.0,
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    return ChatOpenAI(**kwargs)
