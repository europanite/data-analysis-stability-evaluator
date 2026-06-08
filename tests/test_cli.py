from pathlib import Path

import pandas as pd

from analysis_stability.cli import main


def test_cli_profile(tmp_path: Path):
    baseline = tmp_path / "baseline.csv"
    candidate = tmp_path / "candidate.csv"
    out = tmp_path / "report.json"
    pd.DataFrame({"x": [1, 2, 3], "g": ["a", "a", "b"]}).to_csv(baseline, index=False)
    pd.DataFrame({"x": [1, 2, 4], "g": ["a", "b", "b"]}).to_csv(candidate, index=False)
    code = main(["profile", str(baseline), str(candidate), "--out", str(out)])
    assert code == 0
    assert out.exists()


def test_cli_profile_missing_file_returns_clear_error(tmp_path: Path, capsys):
    out = tmp_path / "report.json"
    code = main(["profile", "data/missing-baseline.csv", "data/missing-candidate.csv", "--out", str(out)])
    captured = capsys.readouterr()
    assert code == 2
    assert "baseline_csv not found" in captured.err
    assert "analysis-stability sample-data --out data" in captured.err
    assert not out.exists()


def test_cli_perturb(tmp_path: Path):
    input_csv = tmp_path / "input.csv"
    out = tmp_path / "perturbed.csv"
    pd.DataFrame({"x": list(range(50)), "g": ["a", "b"] * 25}).to_csv(input_csv, index=False)
    code = main(["perturb", str(input_csv), "--out", str(out), "--row-drop-rate", "0.1"])
    assert code == 0
    assert out.exists()


def test_cli_sample_data_then_profile(tmp_path: Path):
    data_dir = tmp_path / "data"
    reports_dir = tmp_path / "reports"
    code = main([
        "sample-data",
        "--out",
        str(data_dir),
        "--rows",
        "80",
        "--row-drop-rate",
        "0.02",
        "--missing-rate",
        "0.01",
        "--numeric-noise-rate",
        "0.02",
    ])
    assert code == 0
    assert (data_dir / "baseline.csv").exists()
    assert (data_dir / "candidate.csv").exists()

    profile_code = main([
        "profile",
        str(data_dir / "baseline.csv"),
        str(data_dir / "candidate.csv"),
        "--out",
        str(reports_dir / "profile_stability.json"),
    ])
    assert profile_code == 0
    assert (reports_dir / "profile_stability.json").exists()
