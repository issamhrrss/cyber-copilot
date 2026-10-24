import json
import re

from .llm import get_llm
from .loader import list_profiles


def route(request: str) -> dict:
    """Ask the LLM which profile fits the request and which inputs to use."""
    profiles = list_profiles()
    catalog = "\n".join(
        f"- {name}: {p['description']} | inputs: "
        + ", ".join(f"{k} ({v})" for k, v in p.get("inputs", {}).items())
        for name, p in profiles.items()
    )
    prompt = (
        "You are a request router. Choose the best profile for the user's request "
        "and extract its inputs.\n\n"
        f"Available profiles:\n{catalog}\n\n"
        f"User request: {request}\n\n"
        'Reply with ONLY a JSON object: {"profile": "<name or null>", '
        '"inputs": {"<input_name>": "<value>"}, "reason": "<one short sentence>"}\n'
        "Use null as profile if nothing fits. Never invent file paths."
    )
    raw = str(get_llm(temperature=0.0).call(prompt))
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        raise ValueError(f"Router returned no JSON: {raw[:200]}")
    return json.loads(match.group(0))
