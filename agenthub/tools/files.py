from pathlib import Path
from crewai.tools import tool
from agenthub.config import OUTPUTS_DIR
from agenthub.registry import register
from agenthub.safeio import read_text_file, resolve_in_workspace


@register
@tool("read_code_file")
def read_code_file(file_path: str) -> str:
    """Read a source code file (inside the workspace) and return it with line numbers."""
    ok, text = read_text_file(file_path)
    if not ok:
        return text
    return "\n".join(f"{i:>4}: {line}" for i, line in enumerate(text.splitlines(), 1))


@register
@tool("list_files")
def list_files(directory: str) -> str:
    """List files and folders inside a workspace directory (non-recursive, max 200 entries)."""
    try:
        path = resolve_in_workspace(directory)
    except PermissionError as exc:
        return f"ERROR: {exc}"
    if not path.is_dir():
        return f"ERROR: not a directory: {directory}"
    entries = sorted(path.iterdir())[:200]
    return "\n".join(f"{'[DIR] ' if e.is_dir() else '      '}{e.name}" for e in entries) or "(empty)"


@register
@tool("write_output_file")
def write_output_file(filename: str, content: str) -> str:
    """Write text to a file inside the 'outputs' folder. Only the file name is used."""
    name = Path(filename).name
    if name in ("", ".", ".."):
        return "ERROR: invalid filename"
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    target = OUTPUTS_DIR / name
    target.write_text(content, encoding="utf-8")
    return f"Saved: {target}"
