import pandas as pd

from data_analysis_stability_evaluator.metrics import approximate_ks_statistic, total_variation_distance


def test_total_variation_distance():
    left = {"a": 0.7, "b": 0.3}
    right = {"a": 0.4, "b": 0.6}
    assert round(total_variation_distance(left, right), 6) == 0.3


def test_approximate_ks_statistic_detects_shift():
    left = pd.Series([1, 2, 3, 4, 5])
    right = pd.Series([10, 11, 12, 13, 14])
    assert approximate_ks_statistic(left, right) > 0.9