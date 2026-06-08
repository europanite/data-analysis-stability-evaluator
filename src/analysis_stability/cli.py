"""Command line interface for analysis-stability-evaluator."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from analysis_stability.evaluator import StabilityEvaluator
from analysis_stability.perturb import PerturbationConfig, perturb_dataframe
from analysis_stability.profile import DataProfiler
from analysis_stability.report import write_csv, write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="analysis-stability")
    sub = parser.add_subparsers(dest="command", required=True)

    profile_parser = sub.add_parser("profile", help="Compare two CSV files by data-profile stability metrics.")
    profile_parser.add_argument("baseline_csv")
    profile_parser.add_argument("candidate_csv")
    profile_parser.add_argument("--out", default="reports/profile_stability.json")
    profile_parser.add_argument("--csv-out", default=None)

    perturb_parser = sub.add_parser("perturb", help="Create a perturbed CSV file.")
    perturb_parser.add_argument("input_csv")
    perturb_parser.add_argument("--out", required=True)
    _add_perturbation_args(perturb_parser)

    example_parser = sub.add_parser("example", help="Run a built-in generic tabular stability example.")
    example_parser.add_argument("--out", default="reports/example")

    args = parser.parse_args(argv)

    if args.command == "profile":
        baseline = pd.read_csv(args.baseline_csv)
        candidate = pd.read_csv(args.candidate_csv)
        report = DataProfiler.compare(baseline, candidate)
        write_json(args.out, {"summary": report.summary, "findings": report.to_frame().to_dict(orient="records")})
        if args.csv_out:
            write_csv(args.csv_out, report.to_frame())
        print(f"risk_score={report.risk_score:.6f}")
        print(f"wrote {args.out}")
        return 0

    if args.command == "perturb":
        df = pd.read_csv(args.input_csv)
        config = _config_from_args(args)
        out = perturb_dataframe(df, config)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(args.out, index=False)
        print(f"wrote {args.out}")
        return 0

    if args.command == "example":
        from analysis_stability.demo import run_example

        result = run_example(Path(args.out))
        print(f"overall_risk_score={result['summary']['overall_risk_score']:.6f}")
        print(f"wrote {args.out}")
        return 0

    raise AssertionError(f"unknown command: {args.command}")


def _add_perturbation_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--row-drop-rate", type=float, default=0.01)
    parser.add_argument("--row-duplicate-rate", type=float, default=0.00)
    parser.add_argument("--missing-rate", type=float, default=0.00)
    parser.add_argument("--numeric-noise-rate", type=float, default=0.00)
    parser.add_argument("--numeric-noise-scale", type=float, default=0.05)
    parser.add_argument("--categorical-swap-rate", type=float, default=0.00)
    parser.add_argument("--seed", type=int, default=42)


def _config_from_args(args: argparse.Namespace) -> PerturbationConfig:
    return PerturbationConfig(
        row_drop_rate=args.row_drop_rate,
        row_duplicate_rate=args.row_duplicate_rate,
        missing_rate=args.missing_rate,
        numeric_noise_rate=args.numeric_noise_rate,
        numeric_noise_scale=args.numeric_noise_scale,
        categorical_swap_rate=args.categorical_swap_rate,
        random_seed=args.seed,
    )


if __name__ == "__main__":
    raise SystemExit(main())
