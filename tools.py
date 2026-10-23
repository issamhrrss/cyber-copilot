# tools.py
import re
from pathlib import Path
from crewai.tools import tool

MAX_CHARS = 30_000

# (اسم الثغرة, النمط, الخطورة)
PATTERNS = [
    ("SQL Injection", r"execute\(\s*(f[\"']|[\"'].*[\"']\s*(%|\+|\.format))", "HIGH"),
    ("SQL Injection (concat)", r"(SELECT|INSERT|UPDATE|DELETE).*(\+\s*\w+|\{\w+\})", "HIGH"),
    ("XSS", r"(render_template_string|Markup\(|\|\s*safe|innerHTML)", "HIGH"),
    ("Command Injection", r"(os\.system|os\.popen|subprocess\.\w+\(.*shell\s*=\s*True)", "CRITICAL"),
    ("Code Execution", r"\b(eval|exec)\(", "CRITICAL"),
    ("Insecure Deserialization", r"(pickle\.loads?|yaml\.load\((?!.*Loader=yaml\.SafeLoader))", "HIGH"),
    ("Hardcoded Secret", r"(password|passwd|secret|api_key|token)\s*=\s*[\"'][^\"']{4,}[\"']", "HIGH"),
    ("Weak Hash", r"hashlib\.(md5|sha1)\(", "MEDIUM"),
    ("Debug Mode Enabled", r"debug\s*=\s*True", "MEDIUM"),
    ("TLS Verification Disabled", r"verify\s*=\s*False", "MEDIUM"),
    ("Path Traversal (possible)", r"open\(\s*(request\.|f[\"']|.*\+)", "MEDIUM"),
]


def _safe_read(file_path: str) -> tuple[Path | None, str]:
    p = Path(file_path).expanduser().resolve()
    if not p.is_file():
        return None, f"ERROR: file not found: {file_path}"
    return p, p.read_text(encoding="utf-8", errors="replace")[:MAX_CHARS]


@tool("read_code_file")
def read_code_file(file_path: str) -> str:
    """Read a source code file and return its content with line numbers."""
    p, content = _safe_read(file_path)
    if p is None:
        return content
    lines = content.splitlines()
    return "\n".join(f"{i:>4}: {line}" for i, line in enumerate(lines, 1))


@tool("static_pattern_scan")
def static_pattern_scan(file_path: str) -> str:
    """Run a quick regex-based scan for common vulnerability patterns.
    Returns suspicious lines with line numbers. Results are hints, not proof."""
    p, content = _safe_read(file_path)
    if p is None:
        return content
    findings = []
    for lineno, line in enumerate(content.splitlines(), 1):
        for name, pattern, severity in PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                findings.append(f"[{severity}] line {lineno}: {name} -> {line.strip()}")
    return "\n".join(findings) if findings else "No suspicious patterns found."
