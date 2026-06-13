"""Small dependency-light metrics used by stability reports."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd


def clipped01(value: float) -> float:
    """Clip a numeric score to the inclusive [0, 1] range."""
    if pd.isna(value):
        return 0.0
    return float(min(1.0, max(0.0, value)))


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert a value to float while avoiding NaN/inf propagation."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not np.isfinite(number):
        return default
    return number


def relative_change(baseline: float, candidate: float) -> float:
    """Return absolute relative change, with sane behavior around zero."""
    baseline = safe_float(baseline)
    candidate = safe_float(candidate)
    diff = abs(candidate - baseline)
    denom = abs(baseline)
    if denom == 0.0:
        return 0.0 if diff == 0.0 else diff
    return diff / denom


def numeric_summary(series: pd.Series) -> dict[str, float]:
    """Return compact numeric summary statistics for a pandas Series."""
    values = pd.to_numeric(series, errors="coerce")
    non_null = values.dropna()
    if non_null.empty:
        return {
            "mean": 0.0,
            "std": 0.0,
            "min": 0.0,
            "median": 0.0,
            "max": 0.0,
            "missing_rate": float(values.isna().mean()) if len(values) else 0.0,
        }
    return {
        "mean": safe_float(non_null.mean()),
        "std": safe_float(non_null.std(ddof=0)),
        "min": safe_float(non_null.min()),
        "median": safe_float(non_null.median()),
        "max": safe_float(non_null.max()),
        "missing_rate": float(values.isna().mean()) if len(values) else 0.0,
    }


def value_counts_distribution(series: pd.Series) -> dict[str, float]:
    """Return normalized value counts with string keys for JSON friendliness."""
    non_null = series.dropna()
    if non_null.empty:
        return {}
    counts = non_null.astype(str).value_counts(normalize=True, dropna=True)
    return {str(key): float(value) for key, value in counts.items()}


def total_variation_distance(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    """Compute total variation distance between two categorical distributions."""
    keys = set(left) | set(right)
    return clipped01(0.5 * sum(abs(float(left.get(k, 0.0)) - float(right.get(k, 0.0))) for k in keys))


def approximate_ks_statistic(left: pd.Series, right: pd.Series) -> float:
    """Compute a simple two-sample Kolmogorov-Smirnov statistic without SciPy."""
    a = pd.to_numeric(left, errors="coerce").dropna().to_numpy(dtype=float)
    b = pd.to_numeric(right, errors="coerce").dropna().to_numpy(dtype=float)
    if a.size == 0 and b.size == 0:
        return 0.0
    if a.size == 0 or b.size == 0:
        return 1.0

    values = np.sort(np.unique(np.concatenate([a, b])))
    a_sorted = np.sort(a)
    b_sorted = np.sort(b)
    a_cdf = np.searchsorted(a_sorted, values, side="right") / a_sorted.size
    b_cdf = np.searchsorted(b_sorted, values, side="right") / b_sorted.size
    return clipped01(float(np.max(np.abs(a_cdf - b_cdf))))
