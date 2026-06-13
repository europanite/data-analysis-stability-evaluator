"""Data profile generation and comparison."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from data_analysis_stability_evaluator.compare import (
    ComparisonReport,
    MetricFinding,
    aggregate_risk,
    severity_from_score,
)
from data_analysis_stability_evaluator.metrics import (
    approximate_ks_statistic,
    clipped01,
    numeric_summary,
    relative_change,
    total_variation_distance,
    value_counts_distribution,
)


@dataclass(frozen=True)
class DataProfile:
    """A compact, serializable profile of a tabular dataset."""

    row_count: int
    column_count: int
    dtypes: dict[str, str]
    missing_rates: dict[str, float]
    numeric: dict[str, dict[str, float]]
    categorical: dict[str, dict[str, float]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "dtypes": self.dtypes,
            "missing_rates": self.missing_rates,
            "numeric": self.numeric,
            "categorical": self.categorical,
        }


class DataProfiler:
    """Create and compare tabular data profiles."""

    @staticmethod
    def profile(df: pd.DataFrame, *, max_categories: int = 30) -> DataProfile:
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
        missing = {col: float(df[col].isna().mean()) for col in df.columns}
        numeric: dict[str, dict[str, float]] = {}
        categorical: dict[str, dict[str, float]] = {}

        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                numeric[col] = numeric_summary(df[col])
            else:
                dist = value_counts_distribution(df[col])
                top = sorted(dist.items(), key=lambda kv: kv[1], reverse=True)[:max_categories]
                other = max(0.0, 1.0 - sum(v for _, v in top))
                categorical[col] = dict(top)
                if other > 0:
                    categorical[col]["<OTHER>"] = other

        return DataProfile(
            row_count=int(len(df)),
            column_count=int(len(df.columns)),
            dtypes=dtypes,
            missing_rates=missing,
            numeric=numeric,
            categorical=categorical,
        )

    @staticmethod
    def compare(
        baseline: pd.DataFrame,
        candidate: pd.DataFrame,
        *,
        schema_weight: float = 1.0,
        row_count_weight: float = 0.5,
        missing_weight: float = 1.0,
        numeric_weight: float = 1.0,
        categorical_weight: float = 1.0,
    ) -> ComparisonReport:
        """Compare two dataframes and return a stability report."""
        base_profile = DataProfiler.profile(baseline)
        cand_profile = DataProfiler.profile(candidate)
        findings: list[MetricFinding] = []
        scores: list[float] = []

        # Schema-level checks.
        base_cols = set(base_profile.dtypes)
        cand_cols = set(cand_profile.dtypes)
        missing_cols = sorted(base_cols - cand_cols)
        added_cols = sorted(cand_cols - base_cols)
        schema_score = clipped01((len(missing_cols) + len(added_cols)) / max(len(base_cols), 1))
        if schema_score > 0:
            weighted = clipped01(schema_score * schema_weight)
            findings.append(
                MetricFinding(
                    name="schema.columns",
                    baseline=sorted(base_cols),
                    candidate=sorted(cand_cols),
                    score=weighted,
                    severity=severity_from_score(weighted),
                    detail=f"missing={missing_cols}; added={added_cols}",
                )
            )
            scores.append(weighted)

        common_cols = sorted(base_cols & cand_cols)
        dtype_changes = [
            col
            for col in common_cols
            if _dtype_family(baseline[col]) != _dtype_family(candidate[col])
        ]
        if dtype_changes:
            dtype_score = clipped01(len(dtype_changes) / max(len(common_cols), 1) * schema_weight)
            findings.append(
                MetricFinding(
                    name="schema.dtypes",
                    baseline={c: base_profile.dtypes[c] for c in dtype_changes},
                    candidate={c: cand_profile.dtypes[c] for c in dtype_changes},
                    score=dtype_score,
                    severity=severity_from_score(dtype_score),
                    detail="dtype family changed columns",
                )
            )
            scores.append(dtype_score)

        row_score = clipped01(relative_change(base_profile.row_count, cand_profile.row_count) * row_count_weight)
        findings.append(
            MetricFinding(
                name="row_count",
                baseline=base_profile.row_count,
                candidate=cand_profile.row_count,
                score=row_score,
                severity=severity_from_score(row_score),
                detail="relative row-count change",
            )
        )
        scores.append(row_score)

        # Missingness checks.
        for col in common_cols:
            diff = abs(base_profile.missing_rates[col] - cand_profile.missing_rates[col])
            score = clipped01(diff * missing_weight)
            findings.append(
                MetricFinding(
                    name=f"missing_rate.{col}",
                    baseline=base_profile.missing_rates[col],
                    candidate=cand_profile.missing_rates[col],
                    score=score,
                    severity=severity_from_score(score),
                    detail="absolute missing-rate shift",
                )
            )
            scores.append(score)

        # Numeric checks.
        common_numeric = sorted(set(base_profile.numeric) & set(cand_profile.numeric))
        for col in common_numeric:
            mean_score = clipped01(
                relative_change(base_profile.numeric[col]["mean"], cand_profile.numeric[col]["mean"]) * numeric_weight
            )
            std_score = clipped01(
                relative_change(base_profile.numeric[col]["std"], cand_profile.numeric[col]["std"]) * numeric_weight
            )
            ks_score = clipped01(approximate_ks_statistic(baseline[col], candidate[col]) * numeric_weight)
            for metric, score, base_val, cand_val in [
                ("mean", mean_score, base_profile.numeric[col]["mean"], cand_profile.numeric[col]["mean"]),
                ("std", std_score, base_profile.numeric[col]["std"], cand_profile.numeric[col]["std"]),
                ("ks", ks_score, 0.0, ks_score),
            ]:
                findings.append(
                    MetricFinding(
                        name=f"numeric.{col}.{metric}",
                        baseline=base_val,
                        candidate=cand_val,
                        score=score,
                        severity=severity_from_score(score),
                        detail="numeric distribution stability",
                    )
                )
                scores.append(score)

        # Categorical checks.
        common_categorical = sorted(set(base_profile.categorical) & set(cand_profile.categorical))
        for col in common_categorical:
            tvd = clipped01(
                total_variation_distance(
                    base_profile.categorical[col],
                    cand_profile.categorical[col],
                )
                * categorical_weight
            )
            findings.append(
                MetricFinding(
                    name=f"categorical.{col}.tvd",
                    baseline=base_profile.categorical[col],
                    candidate=cand_profile.categorical[col],
                    score=tvd,
                    severity=severity_from_score(tvd),
                    detail="total variation distance",
                )
            )
            scores.append(tvd)

        return ComparisonReport(findings=tuple(findings), risk_score=aggregate_risk(scores))


def _dtype_family(series: pd.Series) -> str:
    """Return a semantic dtype family for stability checks.

    Exact pandas dtypes can change during harmless CSV round trips or when small
    missingness is injected, for example int64 becoming float64. For stability
    evaluation, numeric-to-numeric should not be treated as a schema break.
    """
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if isinstance(series.dtype, pd.CategoricalDtype):
        return "categorical"
    return "object"