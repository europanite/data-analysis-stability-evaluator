# [data-analysis-stability-evaluator](https://github.com/europanite/data-analysis-stability-evaluator "data-analysis-stability-evaluator")

[![CI](https://github.com/europanite/data-analysis-stability-evaluator/actions/workflows/ci.yml/badge.svg)](https://github.com/europanite/data-analysis-stability-evaluator/actions/workflows/ci.yml)
[![CodeQL Advanced](https://github.com/europanite/data-analysis-stability-evaluator/actions/workflows/codeql.yml/badge.svg)](https://github.com/europanite/data-analysis-stability-evaluator/actions/workflows/codeql.yml)
[![pages-build-deployment](https://github.com/europanite/data-analysis-stability-evaluator/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/europanite/data-analysis-stability-evaluator/actions/workflows/pages/pages-build-deployment)
[![Publish Python package](https://github.com/europanite/data-analysis-stability-evaluator/actions/workflows/publish.yml/badge.svg)](https://github.com/europanite/data-analysis-stability-evaluator/actions/workflows/publish.yml)

`data-analysis-stability-evaluator` is a pip-installable Python package for checking whether a tabular data analysis project is stable under small data changes.

The package is designed for ordinary data-analysis repositories where the risk is not only model accuracy, but also whether conclusions, aggregate values, rankings, feature summaries, and prediction outputs change too much when the input data changes slightly.

## What it checks

The package supports four stability layers:

1. **Data profile stability**
   - schema changes
   - row-count changes
   - missingness shifts
   - numeric distribution shifts
   - categorical distribution shifts

2. **Perturbation-based sensitivity**
   - row removal
   - row duplication
   - missing-value injection
   - numeric noise injection
   - categorical value swaps

3. **Analysis-output stability**
   - run the same analysis function on baseline and perturbed data
   - compare scalar outputs, rankings, group means, rates, and other flattened results

4. **Prediction stability**
   - compare two prediction vectors
   - compute disagreement rate and numeric prediction drift

## Installation

From PyPI:

```bash
python -m pip install data-analysis-stability-evaluator
```

From this repository:

```bash
python3 -m venv env
source env/bin/activate
cd service
python -m pip install -e ".[dev,plots,sklearn]"
```

With development tools:

```bash
cd service
python -m pip install -e ".[dev,plots,sklearn]"
```

## CLI usage

Compare two CSV files:

```bash
analysis-stability profile data/baseline.csv data/candidate.csv --out reports/profile_stability.json
```

Create a small perturbed copy of a CSV file:

```bash
analysis-stability perturb data/baseline.csv --out data/perturbed.csv --row-drop-rate 0.02 --missing-rate 0.01 --numeric-noise-rate 0.02
```

Run the built-in example:

```bash
analysis-stability example --out reports/example
```

## Python API usage

```python
import pandas as pd
from data_analysis_stability_evaluator import (
    DataProfiler,
    StabilityEvaluator,
    PerturbationConfig,
    generate_perturbations,
)

baseline = pd.read_csv("data/baseline.csv")

# 1. Data profile stability
perturbed = baseline.sample(frac=0.98, random_state=7)
comparison = DataProfiler.compare(baseline, perturbed)
print(comparison.risk_score)
print(comparison.to_frame())

# 2. Analysis-output stability
def analysis(df: pd.DataFrame) -> dict:
    return {
        "row_count": len(df),
        "mean_revenue": df["revenue"].mean(),
        "conversion_rate": df["converted"].mean(),
    }

config = PerturbationConfig(
    row_drop_rate=0.02,
    missing_rate=0.01,
    numeric_noise_rate=0.02,
    random_seed=42,
)

evaluator = StabilityEvaluator(analysis_fn=analysis, config=config, n_runs=20)
report = evaluator.evaluate(baseline)
print(report.summary)
print(report.details.head())
```

### Deactivate environment

```bash
deactivate
```

## Docker Compose workflow

Run tests without relying on a local Python environment:

```bash
docker compose run --rm tests
```

Run the example:

```bash
docker compose run --rm example
```

Open a shell:

```bash
docker compose run --rm shell
```

## Design principle

The package is intentionally conservative. A small risk score does not prove that an analysis is correct. It only shows that the selected outputs were not very sensitive to the tested small input changes. The user should choose perturbation settings and thresholds that match the domain risk.

## CI and release pipeline

This repository uses GitHub Actions to run tests, lint the source, build the source distribution and wheel, and smoke-test the built wheel.

Package publishing is handled by `.github/workflows/publish.yml` with PyPI Trusted Publishing:

- manual workflow dispatch publishes to TestPyPI for rehearsal
- a published GitHub Release whose tag matches `v<pyproject version>` publishes to PyPI

See [`docs/release.md`](docs/release.md) for the full release procedure.
