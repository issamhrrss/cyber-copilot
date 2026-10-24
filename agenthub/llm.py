import os
from functools import lru_cache
from crewai import LLM
from .config import DEFAULT_MODEL


@lru_cache(maxsize=None)
def get_llm(model: str | None = None, temperature: float = 0.1) -> LLM:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set (check your .env file).")
    return LLM(
    model=f"gemini/{(model or DEFAULT_MODEL).removeprefix('gemini/')}",
    api_key=api_key,
    temperature=temperature,
)
