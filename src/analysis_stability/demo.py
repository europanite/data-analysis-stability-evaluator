"""Built-in demo workflow for generic tabular stability evaluation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from analysis_stability.evaluator import StabilityEvaluator
from analysis_stability.perturb import PerturbationConfig, perturb_dataframe
from analysis_stability.profile import DataProfiler
from analysis_stability.report import write_csv, write_json


def make_demo_data(n: int = 500, seed: int = 7) -> pd.DataFrame:
    """Generate a small business-analysis style tabular dataset."""
    rng = np.random.default_rng(seed)
    channel = rng.choice(["search", "social", "email", "direct"], size=n, p=[0.35, 0.25, 0.25, 0.15])
    region = rng.choice(["east", "west", "north", "south"], size=n)
    age = rng.normal(38, 11, size=n).clip(18, 75)
    visits = rng.poisson(3, size=n) + 1
    base_prob = 0.10 + 0.04 * (channel == "email") + 0.03 * (visits >= 4) - 0.02 * (channel == "social")
    converted = rng.binomial(1, np.clip(base_prob, 0.02, 0.40))
    revenue = converted * rng.gamma(shape=2.0, scale=60.0, size=n)
    return pd.DataFrame(
        {
            "channel": channel,
            "region": region,
            "age": age.round(1),
            "visits": visits,
            "converted": converted,
            "revenue": revenue.round(2),
        }
    )


def demo_analysis(df: pd.DataFrame) -> dict:
    """A compact example of analysis outputs that should be stability-checked."""
    by_channel = df.groupby("channel", dropna=False).agg(
        conversion_rate=("converted", "mean"),
        revenue_mean=("revenue", "mean"),
        visits_mean=("visits", "mean"),
    )
    top_channel = by_channel["conversion_rate"].idxmax()
    return {
        "row_count": len(df),
        "overall_conversion_rate": df["converted"].mean(),
        "mean_revenue": df["revenue"].mean(),
        "median_age": df["age"].median(),
        "top_channel_by_conversion": str(top_channel),
        "channel": by_channel.round(6).to_dict(),
    }


def run_example(out_dir: Path) -> dict:
    """Run the built-in demo and write report files."""
    out_dir.mkdir(parents=True, exist_ok=True)
    df = make_demo_data()
    data_dir = out_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    baseline_csv = data_dir / "baseline.csv"
    perturbed_csv = data_dir / "perturbed.csv"
    df.to_csv(baseline_csv, index=False)

    config = PerturbationConfig(
        row_drop_rate=0.02,
        row_duplicate_rate=0.01,
        missing_rate=0.01,
        numeric_noise_rate=0.03,
        numeric_noise_scale=0.03,
        categorical_swap_rate=0.01,
        random_seed=42,
    )
    perturbed = perturb_dataframe(df, config)
    perturbed.to_csv(perturbed_csv, index=False)

    profile_report = DataProfiler.compare(df, perturbed)
    evaluator = StabilityEvaluator(demo_analysis, config=config, n_runs=25)
    stability_report = evaluator.evaluate(df)

    write_csv(out_dir / "profile_findings.csv", profile_report.to_frame())
    write_csv(out_dir / "analysis_stability_details.csv", stability_report.details)
    summary = {
        "profile_summary": profile_report.summary,
        "summary": stability_report.summary,
        "baseline_output": stability_report.baseline_output,
    }
    write_json(out_dir / "summary.json", summary)
    return summary
