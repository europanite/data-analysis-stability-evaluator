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


def test_numeric_dtype_roundtrip_is_not_schema_break():
    baseline = pd.DataFrame({"x": pd.Series([1, 2, 3], dtype="int64")})
    candidate = pd.DataFrame({"x": pd.Series([1.0, 2.0, float("nan")], dtype="float64")})
    report = DataProfiler.compare(baseline, candidate)
    assert "schema.dtypes" not in set(report.to_frame()["name"])
