"""Chat CLI. Run: python3 apps/cli/main.py --demo"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from packages.agent_core import Agent, ApprovalGate, MemoryStore, Scheduler, default_tools, pick_model  # noqa: E402


def cli_approve(action: str) -> bool:
    try:
        return input(f"Approve {action}? [y/N] ").strip().lower() == "y"
    except EOFError:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="run a one-line demo and exit")
    ap.add_argument("--data", default="data", help="data folder for memory/workspace")
    args = ap.parse_args()

    data = Path(args.data)
    scheduler = Scheduler(store=data / "jobs.json")
    agent = Agent(
        model=pick_model(),
        memory=MemoryStore(data / "memory"),
        tools=default_tools(data / "workspace"),
        approvals=ApprovalGate(approve=cli_approve),
        scheduler=scheduler,
    )
    if args.demo:
        print(agent.chat("hello"))
        print(agent.chat("/remember demo ran ok"))
        print(agent.chat("/search demo"))
        print(agent.chat("/tools"))
        return 0

    scheduler.start(agent, data / "jobs.log")
    print(f"Warmlit CLI (model: {agent.model.name}). Type /tools or 'quit'.")
    while True:
        try:
            line = input("you> ").strip()
        except EOFError:
            break
        if line.lower() in {"quit", "exit"}:
            break
        if line:
            print("agent>", agent.chat(line))
    scheduler.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
