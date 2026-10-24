import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

PROFILES_DIR = ROOT / "profiles"
REPORTS_DIR = ROOT / "reports"

# The agents may only read/write inside this folder (default: current directory).
WORKSPACE = Path(os.getenv("WORKSPACE_DIR", str(Path.cwd()))).resolve()
OUTPUTS_DIR = WORKSPACE / "outputs"

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini/gemini-2.5-flash")
