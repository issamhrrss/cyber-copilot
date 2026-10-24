from datetime import datetime
from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task

import agenthub.tools  # noqa: F401  (triggers tool auto-discovery)
from .config import PROFILES_DIR, REPORTS_DIR
from .llm import get_llm
from .registry import TOOLS, get_tool


class ProfileError(Exception):
    pass


def validate_profile(name: str, data: dict) -> None:
    for key in ("description", "agents", "tasks"):
        if key not in data:
            raise ProfileError(f"[{name}] missing top-level key '{key}'")

    for key, agent in data["agents"].items():
        for field in ("role", "goal", "backstory"):
            if field not in agent:
                raise ProfileError(f"[{name}] agent '{key}' missing '{field}'")
        for tool_name in agent.get("tools", []):
            if tool_name not in TOOLS:
                raise ProfileError(
                    f"[{name}] agent '{key}' uses unknown tool '{tool_name}'. "
                    f"Available: {', '.join(sorted(TOOLS))}"
                )

    defined = set()
    for key, task in data["tasks"].items():
        for field in ("description", "expected_output", "agent"):
            if field not in task:
                raise ProfileError(f"[{name}] task '{key}' missing '{field}'")
        if task["agent"] not in data["agents"]:
            raise ProfileError(f"[{name}] task '{key}' uses unknown agent '{task['agent']}'")
        for ctx in task.get("context", []):
            if ctx not in defined:
                raise ProfileError(f"[{name}] task '{key}': context '{ctx}' must be defined before it")
        defined.add(key)


def list_profiles() -> dict[str, dict]:
    profiles = {}
    for path in sorted(PROFILES_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        data["name"] = path.stem
        profiles[path.stem] = data
    return profiles


def load_profile(name: str) -> dict:
    path = PROFILES_DIR / f"{name}.yaml"
    if not path.is_file():
        available = ", ".join(list_profiles()) or "(none)"
        raise ProfileError(f"Profile '{name}' not found. Available: {available}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    validate_profile(name, data)
    data["name"] = name
    return data


def build_crew(profile: dict, output_file: Path) -> Crew:
    agents = {}
    for key, spec in profile["agents"].items():
        agents[key] = Agent(
            role=spec["role"],
            goal=spec["goal"],
            backstory=spec["backstory"],
            tools=[get_tool(t) for t in spec.get("tools", [])],
            llm=get_llm(spec.get("model"), spec.get("temperature", 0.1)),
            allow_delegation=spec.get("allow_delegation", False),
            verbose=True,
        )

    task_specs = profile["tasks"]
    final_key = next((k for k, t in task_specs.items() if t.get("final")), list(task_specs)[-1])

    tasks = {}
    for key, spec in task_specs.items():
        kwargs = {}
        if spec.get("context"):
            kwargs["context"] = [tasks[c] for c in spec["context"]]
        if key == final_key:
            kwargs["output_file"] = str(output_file)
        tasks[key] = Task(
            description=spec["description"],
            expected_output=spec["expected_output"],
            agent=agents[spec["agent"]],
            **kwargs,
        )

    process = Process(profile.get("process", "sequential"))
    crew_kwargs = {}
    if process == Process.hierarchical:
        crew_kwargs["manager_llm"] = get_llm()

    return Crew(
        agents=list(agents.values()),
        tasks=list(tasks.values()),
        process=process,
        verbose=True,
        **crew_kwargs,
    )


def run_profile(name: str, inputs: dict[str, str]) -> Path:
    profile = load_profile(name)
    required = profile.get("inputs", {})

    missing = [k for k in required if k not in inputs]
    unknown = [k for k in inputs if k not in required]
    if missing:
        details = "; ".join(f"{k} ({required[k]})" for k in missing)
        raise ProfileError(f"Missing inputs for '{name}': {details}")
    if unknown:
        raise ProfileError(f"Unknown inputs for '{name}': {', '.join(unknown)}")

    REPORTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = REPORTS_DIR / f"{name}_{stamp}.md"

    crew = build_crew(profile, report)
    crew.kickoff(inputs=inputs)  # fills {placeholders} in tasks/agents
    return report
