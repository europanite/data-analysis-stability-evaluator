"""Command line interface for data-analysis-stability-evaluator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from data_analysis_stability_evaluator.demo import make_sample_data, run_example
from data_analysis_stability_evaluator.perturb import PerturbationConfig, perturb_dataframe
from data_analysis_stability_evaluator.profile import DataProfiler


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _sample_data(args: argparse.Namespace) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    baseline = make_sample_data()
    candidate = perturb_dataframe(
        baseline,
        PerturbationConfig(row_drop_rate=0.1, missing_rate=0.02, numeric_noise_rate=0.1, random_seed=11),
    )
    baseline.to_csv(out / "baseline.csv", index=False)
    candidate.to_csv(out / "candidate.csv", index=False)
    print(f"Wrote sample CSV files to {out}")
    return 0


def _profile(args: argparse.Namespace) -> int:
    baseline = pd.read_csv(args.baseline_csv)
    candidate = pd.read_csv(args.candidate_csv)
    report = DataProfiler.compare(baseline, candidate)
    _write_json(Path(args.out), report.to_json_dict())
    print(f"Wrote profile report to {args.out}")
    return 0


def _perturb(args: argparse.Namespace) -> int:
    df = pd.read_csv(args.input_csv)
    config = PerturbationConfig(
        row_drop_rate=args.row_drop_rate,
        row_duplicate_rate=args.row_duplicate_rate,
        missing_rate=args.missing_rate,
        numeric_noise_rate=args.numeric_noise_rate,
        numeric_noise_scale=args.numeric_noise_scale,
        categorical_swap_rate=args.categorical_swap_rate,
        random_seed=args.random_seed,
    )
    out = perturb_dataframe(df, config)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    print(f"Wrote perturbed CSV to {out_path}")
    return 0


def _example(args: argparse.Namespace) -> int:
    result = run_example(Path(args.out))
    print("Example completed")
    print(result["summary"])
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="analysis-stability")
    sub = parser.add_subparsers(dest="command", required=True)

    sample = sub.add_parser("sample-data", help="Create baseline.csv and candidate.csv sample inputs.")
    sample.add_argument("--out", default="data")
    sample.set_defaults(func=_sample_data)

    profile = sub.add_parser("profile", help="Compare two CSV files and write a JSON profile report.")
    profile.add_argument("baseline_csv")
    profile.add_argument("candidate_csv")
    profile.add_argument("--out", default="reports/profile_stability.json")
    profile.set_defaults(func=_profile)

    perturb = sub.add_parser("perturb", help="Create a perturbed copy of a CSV file.")
    perturb.add_argument("input_csv")
    perturb.add_argument("--out", required=True)
    perturb.add_argument("--row-drop-rate", type=float, default=0.01)
    perturb.add_argument("--row-duplicate-rate", type=float, default=0.0)
    perturb.add_argument("--missing-rate", type=float, default=0.0)
    perturb.add_argument("--numeric-noise-rate", type=float, default=0.0)
    perturb.add_argument("--numeric-noise-scale", type=float, default=0.05)
    perturb.add_argument("--categorical-swap-rate", type=float, default=0.0)
    perturb.add_argument("--random-seed", type=int, default=42)
    perturb.set_defaults(func=_perturb)

    example = sub.add_parser("example", help="Run the built-in example workflow.")
    example.add_argument("--out", default="reports/example")
    example.set_defaults(func=_example)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
