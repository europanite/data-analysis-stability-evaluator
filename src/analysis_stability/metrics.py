"""Small, dependency-light metrics used by the stability evaluator."""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd


def safe_float(value: object, default: float = 0.0) -> float:
    """Convert a value to a finite float."""
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    if math.isnan(number) or math.isinf(number):
        return default
    return number


def relative_change(baseline: float, candidate: float, *, eps: float = 1e-12) -> float:
    """Absolute relative change with a stable denominator."""
    baseline = safe_float(baseline)
    candidate = safe_float(candidate)
    return abs(candidate - baseline) / max(abs(baseline), eps)


def normalized_abs_change(baseline: float, candidate: float, *, scale: float | None = None) -> float:
    """Absolute change normalized to [0, inf), usually later clipped to [0, 1]."""
    baseline = safe_float(baseline)
    candidate = safe_float(candidate)
    denom = max(abs(scale if scale is not None else baseline), 1e-12)
    return abs(candidate - baseline) / denom


def clipped01(value: float) -> float:
    """Clip a numeric value into [0, 1]."""
    return float(min(1.0, max(0.0, safe_float(value))))


def total_variation_distance(left: Mapping[object, float], right: Mapping[object, float]) -> float:
    """Total variation distance between two discrete distributions."""
    keys = set(left) | set(right)
    return 0.5 * sum(abs(safe_float(left.get(k, 0.0)) - safe_float(right.get(k, 0.0))) for k in keys)


def value_counts_distribution(series: pd.Series, *, include_missing: bool = True) -> dict[str, float]:
    """Return normalized value counts as a string-keyed distribution."""
    if include_missing:
        values = series.astype("object").where(series.notna(), "<MISSING>")
    else:
        values = series.dropna()
    if len(values) == 0:
        return {}
    counts = values.astype(str).value_counts(normalize=True, dropna=False)
    return {str(k): float(v) for k, v in counts.items()}


def approximate_ks_statistic(left: pd.Series, right: pd.Series) -> float:
    """Approximate two-sample Kolmogorov-Smirnov statistic without scipy.

    The implementation compares empirical CDF values on the union of observed
    numeric values. It is sufficient for stability diagnostics and avoids a hard
    scipy dependency.
    """
    left_arr = pd.to_numeric(left, errors="coerce").dropna().to_numpy(dtype=float)
    right_arr = pd.to_numeric(right, errors="coerce").dropna().to_numpy(dtype=float)
    if left_arr.size == 0 or right_arr.size == 0:
        return 0.0
    grid = np.unique(np.concatenate([left_arr, right_arr]))
    left_sorted = np.sort(left_arr)
    right_sorted = np.sort(right_arr)
    left_cdf = np.searchsorted(left_sorted, grid, side="right") / left_arr.size
    right_cdf = np.searchsorted(right_sorted, grid, side="right") / right_arr.size
    return float(np.max(np.abs(left_cdf - right_cdf)))


def numeric_summary(series: pd.Series) -> dict[str, float]:
    """Return robust numeric summary values for a pandas Series."""
    values = pd.to_numeric(series, errors="coerce")
    if values.notna().sum() == 0:
        return {
            "mean": 0.0,
            "std": 0.0,
            "min": 0.0,
            "q25": 0.0,
            "median": 0.0,
            "q75": 0.0,
            "max": 0.0,
        }
    desc = values.quantile([0.25, 0.5, 0.75]).to_dict()
    return {
        "mean": safe_float(values.mean()),
        "std": safe_float(values.std(ddof=0)),
        "min": safe_float(values.min()),
        "q25": safe_float(desc.get(0.25)),
        "median": safe_float(desc.get(0.5)),
        "q75": safe_float(desc.get(0.75)),
        "max": safe_float(values.max()),
    }
