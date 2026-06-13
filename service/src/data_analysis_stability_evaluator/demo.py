"""Built-in demonstration workflow for the CLI and Docker Compose example."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from data_analysis_stability_evaluator.evaluator import StabilityEvaluator
from data_analysis_stability_evaluator.perturb import PerturbationConfig, perturb_dataframe
from data_analysis_stability_evaluator.profile import DataProfiler


def make_sample_data() -> pd.DataFrame:
    """Create a deterministic sample dataset for smoke tests and demos."""
    return pd.DataFrame(
        {
            "revenue": [100, 120, 90, 130, 80, 160, 110, 105, 95, 150],
            "converted": [1, 1, 0, 1, 0, 1, 1, 0, 0, 1],
            "segment": ["a", "a", "b", "a", "b", "c", "a", "b", "b", "c"],
        }
    )


def sample_analysis(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "row_count": len(df),
        "mean_revenue": df["revenue"].mean(),
        "conversion_rate": df["converted"].mean(),
        "segment_share": df["segment"].value_counts(normalize=True).to_dict(),
    }


def run_example(out_dir: Path) -> dict[str, Any]:
    """Run a small end-to-end example and write JSON reports."""
    out_dir.mkdir(parents=True, exist_ok=True)
    baseline = make_sample_data()
    candidate = perturb_dataframe(
        baseline,
        PerturbationConfig(row_drop_rate=0.1, numeric_noise_rate=0.2, random_seed=7),
    )
    profile_report = DataProfiler.compare(baseline, candidate)
    evaluator = StabilityEvaluator(
        sample_analysis,
        config=PerturbationConfig(row_drop_rate=0.1, numeric_noise_rate=0.1, random_seed=42),
        n_runs=5,
    )
    stability_report = evaluator.evaluate(baseline)

    result = {
        "profile": profile_report.to_json_dict(),
        "summary": stability_report.summary,
    }
    (out_dir / "example_report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
