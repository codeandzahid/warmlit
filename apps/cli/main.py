"""Chat CLI. Run: python3 apps/cli/main.py --demo"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from packages.agent_core import Agent, EchoModel, MemoryStore, default_tools  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="run a one-line demo and exit")
    ap.add_argument("--data", default="data", help="data folder for memory/workspace")
    args = ap.parse_args()

    data = Path(args.data)
    agent = Agent(
        model=EchoModel(),
        memory=MemoryStore(data / "memory"),
        tools=default_tools(data / "workspace"),
    )
    if args.demo:
        print(agent.chat("hello"))
        agent.memory.remember("demo ran ok")
        print("memory search:", agent.memory.search("demo"))
        return 0

    print("Warmlit CLI (demo model). Type 'quit' to exit.")
    while True:
        try:
            line = input("you> ").strip()
        except EOFError:
            break
        if line.lower() in {"quit", "exit"}:
            break
        if line:
            print("agent>", agent.chat(line))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
