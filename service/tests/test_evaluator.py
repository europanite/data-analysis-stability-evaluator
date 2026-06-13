import pandas as pd
from data_analysis_stability_evaluator import PerturbationConfig, StabilityEvaluator, perturb_dataframe


def analysis(df: pd.DataFrame) -> dict:
    return {
        "rows": len(df),
        "mean_x": df["x"].mean(),
        "group_share": df["group"].value_counts(normalize=True).to_dict(),
    }


def test_perturb_dataframe_preserves_columns():
    df = pd.DataFrame({"x": range(100), "group": ["a", "b"] * 50})
    out = perturb_dataframe(df, PerturbationConfig(row_drop_rate=0.1, missing_rate=0.01, random_seed=1))
    assert list(out.columns) == list(df.columns)
    assert len(out) > 0


def test_stability_evaluator_runs():
    df = pd.DataFrame({"x": range(100), "group": ["a", "b"] * 50})
    evaluator = StabilityEvaluator(
        analysis,
        config=PerturbationConfig(row_drop_rate=0.01, numeric_noise_rate=0.01, random_seed=1),
        n_runs=3,
    )
    report = evaluator.evaluate(df)
    assert report.summary["n_runs"] == 3
    assert "overall_risk_score" in report.summary
    assert not report.details.empty