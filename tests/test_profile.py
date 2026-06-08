import pandas as pd

from analysis_stability import DataProfiler


def test_profile_compare_identical_data_has_low_risk():
    df = pd.DataFrame({"x": [1, 2, 3], "group": ["a", "a", "b"]})
    report = DataProfiler.compare(df, df.copy())
    assert report.risk_score < 0.01
    assert not report.to_frame().empty


def test_profile_compare_detects_schema_change():
    base = pd.DataFrame({"x": [1, 2, 3], "group": ["a", "a", "b"]})
    cand = pd.DataFrame({"x": [1, 2, 3], "new_col": [1, 1, 1]})
    report = DataProfiler.compare(base, cand)
    assert report.risk_score > 0
    assert "schema.columns" in set(report.to_frame()["name"])
