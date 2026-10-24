"""Central registry: tools register themselves, profiles reference them by name."""
TOOLS: dict = {}


def register(tool_obj, alias: str | None = None):
    TOOLS[alias or tool_obj.name] = tool_obj
    return tool_obj


def get_tool(name: str):
    if name not in TOOLS:
        raise KeyError(f"Unknown tool '{name}'. Available: {', '.join(sorted(TOOLS))}")
    return TOOLS[name]


def list_tools() -> dict:
    return dict(TOOLS)
