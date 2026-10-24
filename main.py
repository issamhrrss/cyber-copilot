import ast
if not hasattr(ast, 'NameConstant'):
    ast.NameConstant = lambda value, **kwargs: ast.Constant(value=value, **kwargs)

import argparse
import sys

from agenthub.loader import ProfileError, list_profiles, run_profile
from agenthub.registry import list_tools
from agenthub.router import route
import agenthub.tools  # noqa: F401


def parse_inputs(pairs: list[str] | None) -> dict[str, str]:
    result = {}
    for item in pairs or []:
        if "=" not in item:
            sys.exit(f"Invalid input '{item}'. Use key=value")
        key, value = item.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def cmd_list(_args):
    print("Profiles:")
    for name, p in list_profiles().items():
        print(f"  {name}\n    {p['description']}")
        for k, v in p.get("inputs", {}).items():
            print(f"    - input {k}: {v}")
    print("\nTools:")
    for name, t in sorted(list_tools().items()):
        first_line = (t.description or "").strip().splitlines()[0] if t.description else ""
        print(f"  {name}: {first_line[:90]}")


def cmd_run(args):
    report = run_profile(args.profile, parse_inputs(args.input))
    print(f"\n✅ Report saved to: {report}")


def cmd_ask(args):
    decision = route(args.request)
    profile = decision.get("profile")
    if not profile:
        sys.exit(f"No matching profile. {decision.get('reason', '')}")
    print(f"\nProfile : {profile}\nInputs  : {decision.get('inputs', {})}\nReason  : {decision.get('reason', '')}")
    if input("\nRun this? [y/N]: ").strip().lower() != "y":
        sys.exit("Cancelled.")
    report = run_profile(profile, decision.get("inputs", {}))
    print(f"\n✅ Report saved to: {report}")


def main():
    parser = argparse.ArgumentParser(prog="agent-hub", description="Extensible multi-agent assistant")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List profiles and tools").set_defaults(func=cmd_list)

    run_p = sub.add_parser("run", help="Run a profile")
    run_p.add_argument("profile")
    run_p.add_argument("-i", "--input", action="append", help="key=value (repeatable)")
    run_p.set_defaults(func=cmd_run)

    ask_p = sub.add_parser("ask", help="Describe the task in free text; the router picks the profile")
    ask_p.add_argument("request")
    ask_p.set_defaults(func=cmd_ask)

    args = parser.parse_args()
    try:
        args.func(args)
    except (ProfileError, RuntimeError) as exc:
        sys.exit(f"ERROR: {exc}")


if __name__ == "__main__":
    main()
