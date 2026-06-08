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


def test_cli_perturb(tmp_path: Path):
    input_csv = tmp_path / "input.csv"
    out = tmp_path / "perturbed.csv"
    pd.DataFrame({"x": list(range(50)), "g": ["a", "b"] * 25}).to_csv(input_csv, index=False)
    code = main(["perturb", str(input_csv), "--out", str(out), "--row-drop-rate", "0.1"])
    assert code == 0
    assert out.exists()
