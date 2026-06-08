"""Prediction stability helpers."""

from __future__ import annotations

from typing import Any

import numpy as np

from analysis_stability.metrics import clipped01, safe_float


def compare_predictions(baseline: Any, candidate: Any, *, classification: bool | None = None) -> dict[str, float]:
    """Compare two prediction vectors.

    For classification-like predictions, use disagreement rate. For numeric
    predictions, also compute mean absolute drift and RMSE drift.
    """
    base = np.asarray(baseline)
    cand = np.asarray(candidate)
    if base.shape != cand.shape:
        raise ValueError(f"prediction shapes differ: {base.shape} vs {cand.shape}")

    if base.size == 0:
        return {
            "n": 0.0,
            "disagreement_rate": 0.0,
            "mean_absolute_drift": 0.0,
            "rmse_drift": 0.0,
            "risk_score": 0.0,
        }

    if classification is None:
        classification = not (np.issubdtype(base.dtype, np.number) and np.issubdtype(cand.dtype, np.number))

    disagreement = float(np.mean(base != cand))
    if classification:
        mad = disagreement
        rmse = disagreement ** 0.5
    else:
        diff = cand.astype(float) - base.astype(float)
        mad = float(np.mean(np.abs(diff)))
        rmse = float(np.sqrt(np.mean(diff**2)))
        scale = max(float(np.std(base.astype(float))), abs(float(np.mean(base.astype(float)))), 1e-12)
        mad = mad / scale
        rmse = rmse / scale

    risk = clipped01(0.50 * safe_float(disagreement) + 0.30 * safe_float(mad) + 0.20 * safe_float(rmse))
    return {
        "n": float(base.size),
        "disagreement_rate": safe_float(disagreement),
        "mean_absolute_drift": safe_float(mad),
        "rmse_drift": safe_float(rmse),
        "risk_score": risk,
    }
