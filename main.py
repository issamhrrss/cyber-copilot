import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from crewai import Agent, Crew, LLM, Process, Task

from tools import read_code_file, static_pattern_scan

load_dotenv()

def build_llm() -> LLM:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        sys.exit("ERROR: GEMINI_API_KEY is not set (check your .env file).")
    
    raw_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    model_name = raw_model if raw_model.startswith("gemini/") else f"gemini/{raw_model}"

    return LLM(
        model=model_name,
        api_key=api_key,
        temperature=0.1,
    )

def build_crew(target_file: str, report_path: Path) -> Crew:
    llm = build_llm()

    auditor = Agent(
        role="Senior Application Security Auditor",
        goal="Find real security vulnerabilities in source code and explain them precisely.",
        backstory=(
            "You are an experienced AppSec engineer who performs secure code reviews "
            "following OWASP Top 10 and CWE. You avoid false positives and always "
            "cite the exact line numbers."
        ),
        tools=[read_code_file, static_pattern_scan],
        llm=llm,
        verbose=True,
    )

    patcher = Agent(
        role="Secure Coding Engineer",
        goal="Provide minimal, secure, production-ready fixes for identified vulnerabilities.",
        backstory=(
            "You write safe Python code. For each confirmed bug, you provide a clear "
            "before-and-after fix and explain why it resolves the root cause."
        ),
        llm=llm,
        verbose=True,
    )

    reporter = Agent(
        role="Security Report Writer",
        goal="Synthesize technical findings into a professional Markdown security report.",
        backstory=(
            "You compile executive summaries, vulnerability details, severity matrix, "
            "and remediation guidance into clear Markdown documents."
        ),
        llm=llm,
        verbose=True,
    )

    t1 = Task(
        description=(
            f"Perform a security code review of the file: {target_file}\n"
            "1. Read the file with read_code_file.\n"
            "2. Run static_pattern_scan and verify each hint manually (discard false positives).\n"
            "3. For every confirmed vulnerability give: title, CWE ID, OWASP category, "
            "severity (Critical/High/Medium/Low), exact line number(s), explanation, and a short attack scenario."
        ),
        expected_output="A structured list of confirmed vulnerabilities with evidence.",
        agent=auditor,
    )

    t2 = Task(
        description=(
            "Review the vulnerabilities found by the auditor and write secure patches.\n"
            "Provide both vulnerable snippet (BEFORE) and fixed code (AFTER) with explanations."
        ),
        expected_output="Clear secure code patches for each finding.",
        agent=patcher,
    )

    t3 = Task(
        description=(
            f"Write the final Markdown security review report and save it directly to: {report_path}\n"
            "Include: Title, Executive Summary, Table of Findings (Severity, CWE, Title), "
            "Detailed Findings with Patches, and General Security Recommendations."
        ),
        expected_output=f"A complete Markdown security report saved at {report_path}.",
        agent=reporter,
        output_file=str(report_path),
    )

    return Crew(
        agents=[auditor, patcher, reporter],
        tasks=[t1, t2, t3],
        process=Process.sequential,
        verbose=True,
    )

def main():
    parser = argparse.ArgumentParser(description="AI Cybersecurity Code Review Co-pilot")
    parser.add_argument("file", help="Path to the source code file to analyze")
    args = parser.parse_args()

    target = Path(args.file).expanduser().resolve()
    if not target.is_file():
        sys.exit(f"ERROR: File not found: {target}")

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = reports_dir / f"report_{target.stem}_{stamp}.md"

    print(f"[*] Starting security review for: {target}")
    crew = build_crew(str(target), report_path)
    crew.kickoff()
    print(f"[+] Review complete! Report generated at: {report_path}")

if __name__ == "__main__":
    main()
EOF
