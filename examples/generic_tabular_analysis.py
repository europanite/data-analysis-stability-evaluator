"""Run the package built-in generic tabular stability example."""

from __future__ import annotations

import argparse
from pathlib import Path

from analysis_stability.demo import run_example


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="reports/example")
    args = parser.parse_args()
    result = run_example(Path(args.out))
    print("Example completed")
    print(result["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
