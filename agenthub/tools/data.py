import csv
import statistics
from collections import Counter
from itertools import islice
from crewai.tools import tool
from agenthub.registry import register
from agenthub.safeio import resolve_in_workspace

MAX_ROWS = 100_000


def _to_float(value: str):
    try:
        return float(value)
    except ValueError:
        return None


@register
@tool("csv_summary")
def csv_summary(file_path: str) -> str:
    """Summarize a CSV file: row count, columns, missing values, numeric statistics, top categories and sample rows."""
    try:
        path = resolve_in_workspace(file_path)
    except PermissionError as exc:
        return f"ERROR: {exc}"
    if not path.is_file():
        return f"ERROR: file not found: {file_path}"

    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        rows = list(islice(reader, MAX_ROWS))
    if not columns or not rows:
        return "The CSV file is empty."

    out = [f"Rows: {len(rows)}", f"Columns: {', '.join(columns)}", ""]
    for col in columns:
        values = [(r.get(col) or "").strip() for r in rows]
        non_empty = [v for v in values if v]
        missing = len(values) - len(non_empty)
        numbers = [n for n in (_to_float(v) for v in non_empty) if n is not None]
        if non_empty and len(numbers) >= 0.8 * len(non_empty):
            out.append(
                f"- {col} (numeric): missing={missing}, min={min(numbers):.2f}, "
                f"max={max(numbers):.2f}, mean={statistics.mean(numbers):.2f}, "
                f"median={statistics.median(numbers):.2f}, sum={sum(numbers):.2f}"
            )
        else:
            top = Counter(non_empty).most_common(3)
            out.append(f"- {col} (text): missing={missing}, unique={len(set(non_empty))}, top={top}")
    out.append("\nSample rows:")
    out.extend(str(r) for r in rows[:5])
    return "\n".join(out)
