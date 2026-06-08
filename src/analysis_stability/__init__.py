"""Stability evaluation toolkit for tabular data analysis projects."""

from analysis_stability.compare import ComparisonReport, MetricFinding
from analysis_stability.evaluator import AnalysisStabilityReport, StabilityEvaluator
from analysis_stability.model import compare_predictions
from analysis_stability.perturb import PerturbationConfig, generate_perturbations, perturb_dataframe
from analysis_stability.profile import DataProfile, DataProfiler

__all__ = [
    "AnalysisStabilityReport",
    "ComparisonReport",
    "DataProfile",
    "DataProfiler",
    "MetricFinding",
    "PerturbationConfig",
    "StabilityEvaluator",
    "compare_predictions",
    "generate_perturbations",
    "perturb_dataframe",
]
