import re
from crewai.tools import tool
from agenthub.registry import register
from agenthub.safeio import read_text_file

# (name, regex, severity)
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


@register
@tool("static_pattern_scan")
def static_pattern_scan(file_path: str) -> str:
    """Quick regex-based scan for common vulnerability patterns. Returns hints with line numbers, not proof."""
    ok, text = read_text_file(file_path)
    if not ok:
        return text
    findings = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, pattern, severity in PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                findings.append(f"[{severity}] line {lineno}: {name} -> {line.strip()}")
    return "\n".join(findings) if findings else "No suspicious patterns found."
