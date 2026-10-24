from pathlib import Path
from .config import WORKSPACE

MAX_CHARS = 30_000


def resolve_in_workspace(file_path: str) -> Path:
    """Resolve a path and make sure it stays inside the workspace."""
    path = Path(file_path).expanduser()
    if not path.is_absolute():
        path = WORKSPACE / path
    path = path.resolve()
    if not path.is_relative_to(WORKSPACE):
        raise PermissionError(f"Access denied (outside workspace): {file_path}")
    return path


def read_text_file(file_path: str) -> tuple[bool, str]:
    """Return (ok, content_or_error_message)."""
    try:
        path = resolve_in_workspace(file_path)
    except PermissionError as exc:
        return False, f"ERROR: {exc}"
    if not path.is_file():
        return False, f"ERROR: file not found: {file_path}"
    return True, path.read_text(encoding="utf-8", errors="replace")[:MAX_CHARS]
