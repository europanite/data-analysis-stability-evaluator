"""Comparison report types and scoring helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class MetricFinding:
    """One stability finding for a profile or output metric."""

    name: str
    baseline: Any
    candidate: Any
    score: float
    severity: str
    detail: str = ""


@dataclass(frozen=True)
class ComparisonReport:
    """Collection of metric findings plus an aggregate risk score."""

    findings: tuple[MetricFinding, ...]
    risk_score: float

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([finding.__dict__ for finding in self.findings])

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "risk_score": self.risk_score,
            "findings": [finding.__dict__ for finding in self.findings],
        }


def severity_from_score(score: float, *, medium: float = 0.05, high: float = 0.15) -> str:
    """Map a score to a human-readable severity bucket."""
    if score >= high:
        return "high"
    if score >= medium:
        return "medium"
    return "low"


def aggregate_risk(scores: list[float] | tuple[float, ...]) -> float:
    """Aggregate metric scores while keeping the maximum score influential."""
    clean = [float(score) for score in scores if pd.notna(score)]
    if not clean:
        return 0.0
    mean_score = sum(clean) / len(clean)
    max_score = max(clean)
    return float(min(1.0, max(0.0, 0.5 * mean_score + 0.5 * max_score)))
