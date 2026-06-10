"""Evaluate analysis-output stability under repeated perturbations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pandas as pd

from analysis_stability.compare import ComparisonReport, aggregate_risk, severity_from_score
from analysis_stability.flatten import flatten_output
from analysis_stability.metrics import clipped01, relative_change, safe_float
from analysis_stability.perturb import PerturbationConfig, generate_perturbations
from analysis_stability.profile import DataProfiler


@dataclass(frozen=True)
class AnalysisStabilityReport:
    """Output of repeated perturbation-based analysis evaluation."""

    baseline_output: dict[str, Any]
    details: pd.DataFrame
    summary: dict[str, Any]
    profile_reports: tuple[ComparisonReport, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "baseline_output": self.baseline_output,
            "summary": self.summary,
            "details": self.details.to_dict(orient="records"),
        }


class StabilityEvaluator:
    """Run a user-provided analysis function against perturbed datasets."""

    def __init__(
        self,
        analysis_fn: Callable[[pd.DataFrame], Any],
        *,
        config: PerturbationConfig | None = None,
        n_runs: int = 20,
        medium_threshold: float = 0.05,
        high_threshold: float = 0.15,
    ) -> None:
        if n_runs <= 0:
            raise ValueError("n_runs must be positive")
        self.analysis_fn = analysis_fn
        self.config = config or PerturbationConfig()
        self.n_runs = n_runs
        self.medium_threshold = medium_threshold
        self.high_threshold = high_threshold

    def evaluate(self, df: pd.DataFrame) -> AnalysisStabilityReport:
        baseline_raw = self.analysis_fn(df.copy(deep=True))
        baseline = flatten_output(baseline_raw)
        rows: list[dict[str, Any]] = []
        profile_reports: list[ComparisonReport] = []

        for run, perturbed in generate_perturbations(df, self.config, n_runs=self.n_runs):
            profile_report = DataProfiler.compare(df, perturbed)
            profile_reports.append(profile_report)
            candidate = flatten_output(self.analysis_fn(perturbed.copy(deep=True)))
            keys = sorted(set(baseline) | set(candidate))
            for key in keys:
                base_val = baseline.get(key)
                cand_val = candidate.get(key)
                if _is_number(base_val) and _is_number(cand_val):
                    score = clipped01(relative_change(safe_float(base_val), safe_float(cand_val)))
                    change_type = "numeric_relative_change"
                else:
                    score = 0.0 if base_val == cand_val else 1.0
                    change_type = "exact_match"
                rows.append(
                    {
                        "run": run,
                        "metric": key,
                        "baseline": base_val,
                        "candidate": cand_val,
                        "score": score,
                        "severity": severity_from_score(
                            score, medium=self.medium_threshold, high=self.high_threshold
                        ),
                        "change_type": change_type,
                        "profile_risk_score": profile_report.risk_score,
                    }
                )

        details = pd.DataFrame(rows)
        if details.empty:
            output_risk = 0.0
            unstable_metric_count = 0
            max_output_score = 0.0
        else:
            output_risk = aggregate_risk(details["score"].astype(float).tolist())
            per_metric = details.groupby("metric")["score"].max()
            unstable_metric_count = int((per_metric >= self.medium_threshold).sum())
            max_output_score = float(details["score"].max())

        profile_risk = aggregate_risk([r.risk_score for r in profile_reports])
        overall = clipped01(0.55 * output_risk + 0.45 * profile_risk)
        summary = {
            "overall_risk_score": overall,
            "output_risk_score": output_risk,
            "profile_risk_score": profile_risk,
            "max_output_score": max_output_score,
            "unstable_metric_count": unstable_metric_count,
            "n_runs": self.n_runs,
            "row_count": int(len(df)),
            "column_count": int(len(df.columns)),
        }
        return AnalysisStabilityReport(
            baseline_output=baseline,
            details=details,
            summary=summary,
            profile_reports=tuple(profile_reports),
        )


def _is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return pd.notna(number)