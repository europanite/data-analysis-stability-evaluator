"""Result objects for stability comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class MetricFinding:
    """One stability finding for a metric, column, or output field."""

    name: str
    baseline: Any
    candidate: Any
    score: float
    severity: str
    detail: str = ""


@dataclass(frozen=True)
class ComparisonReport:
    """Collection of stability findings."""

    findings: tuple[MetricFinding, ...]
    risk_score: float

    @property
    def summary(self) -> dict[str, float | int]:
        counts = {"low": 0, "medium": 0, "high": 0}
        for finding in self.findings:
            counts[finding.severity] = counts.get(finding.severity, 0) + 1
        return {
            "risk_score": self.risk_score,
            "finding_count": len(self.findings),
            "low_count": counts.get("low", 0),
            "medium_count": counts.get("medium", 0),
            "high_count": counts.get("high", 0),
        }

    def to_frame(self) -> pd.DataFrame:
        """Convert the report to a pandas DataFrame."""
        return pd.DataFrame(
            [
                {
                    "name": f.name,
                    "baseline": f.baseline,
                    "candidate": f.candidate,
                    "score": f.score,
                    "severity": f.severity,
                    "detail": f.detail,
                }
                for f in self.findings
            ]
        )


def severity_from_score(score: float, *, medium: float = 0.05, high: float = 0.15) -> str:
    """Map a numeric risk score to a human-readable severity."""
    if score >= high:
        return "high"
    if score >= medium:
        return "medium"
    return "low"


def aggregate_risk(scores: list[float]) -> float:
    """Aggregate metric-level scores into one conservative risk score."""
    if not scores:
        return 0.0
    ordered = sorted(float(s) for s in scores)
    mean_score = sum(ordered) / len(ordered)
    p90_score = ordered[min(len(ordered) - 1, int(round(0.9 * (len(ordered) - 1))))]
    max_score = max(ordered)
    return float(min(1.0, 0.50 * mean_score + 0.35 * p90_score + 0.15 * max_score))
