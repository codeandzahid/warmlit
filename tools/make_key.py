"""Owner tool: make a Paid license key file for a buyer.

Usage: python3 tools/make_key.py --days 30 --out data/license.json
Set LICENSE_SECRET in .env first (owner-only, never share it).
Give the buyer the license.json file after payment. They put it in
their data/ folder. No card data ever touches this code.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.agent_core.models import load_dotenv  # noqa: E402
from packages.agent_core.plans import make_license  # noqa: E402


def main() -> int:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--out", default="data/license.json")
    args = ap.parse_args()
    lic = make_license(days=args.days)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(lic, indent=2), encoding="utf-8")
    print(f"Paid key written to {out} (expires {lic['expires']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
