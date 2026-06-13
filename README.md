# [data-analysis-stability-evaluator](https://github.com/europanite/data-analysis-stability-evaluator "data-analysis-stability-evaluator")

[![CI](https://github.com/europanite/data-analysis-stability-evaluator/actions/workflows/ci.yml/badge.svg)](https://github.com/europanite/data-analysis-stability-evaluator/actions/workflows/ci.yml)
[![CodeQL Advanced](https://github.com/europanite/data-analysis-stability-evaluator/actions/workflows/codeql.yml/badge.svg)](https://github.com/europanite/data-analysis-stability-evaluator/actions/workflows/codeql.yml)
[![pages-build-deployment](https://github.com/europanite/data-analysis-stability-evaluator/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/europanite/data-analysis-stability-evaluator/actions/workflows/pages/pages-build-deployment)
[![Publish Python package](https://github.com/europanite/data-analysis-stability-evaluator/actions/workflows/publish.yml/badge.svg)](https://github.com/europanite/data-analysis-stability-evaluator/actions/workflows/publish.yml)

`data-analysis-stability-evaluator` is a Python package for data analysis stability evaluation against small data changes.

It is designed for practical data analysis projects where the risk is not only model accuracy, but also whether conclusions, aggregate values, rankings, feature summaries, profile reports, and prediction outputs change too much when the input data changes slightly.

## Why this package exists

Small data changes can unexpectedly change analysis results.

Examples:

- a few rows are removed
- missing values slightly increase
- numeric values contain small noise
- categorical values shift
- input data distribution changes
- analysis outputs depend too strongly on fragile assumptions

This package helps detect those risks by comparing baseline data, perturbed data, and analysis outputs.

A low risk score does not prove that an analysis is correct. It only means that the selected outputs were not highly sensitive to the tested perturbations.

## What it checks

The package supports four stability layers.

### 1. Data profile stability

- schema changes
- row-count changes
- missingness shifts
- numeric distribution shifts
- categorical distribution shifts

### 2. Perturbation-based sensitivity

- row removal
- row duplication
- missing-value injection
- numeric noise injection
- categorical value swaps

### 3. Analysis-output stability

- run the same analysis function on baseline and perturbed data
- flatten nested outputs into comparable scalar metrics
- compare numbers, rates, group summaries, rankings, and flags

### 4. Prediction stability

- compare prediction vectors
- compute disagreement rate
- compute numeric prediction drift

## Installation

From PyPI:

```bash
python -m pip install data-analysis-stability-evaluator
```

From TestPyPI:

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  data-analysis-stability-evaluator
```

## Quick start

Create sample CSV files:

```bash
analysis-stability sample-data --out data
```

This writes:

```text
data/baseline.csv
data/candidate.csv
```

Compare the two CSV files:

```bash
analysis-stability profile data/baseline.csv data/candidate.csv --out reports/profile_stability.json
```

Create a perturbed copy of a CSV file:

```bash
analysis-stability perturb data/baseline.csv \
  --out data/perturbed.csv \
  --row-drop-rate 0.02 \
  --missing-rate 0.01 \
  --numeric-noise-rate 0.02
```

Run the built-in example:

```bash
analysis-stability example --out reports/example
```

## Python API example

```python
import pandas as pd

from data_analysis_stability_evaluator import (
    DataProfiler,
    PerturbationConfig,
    StabilityEvaluator,
    perturb_dataframe,
)

baseline = pd.read_csv("data/baseline.csv")

perturbed = perturb_dataframe(
    baseline,
    PerturbationConfig(
        row_drop_rate=0.02,
        missing_rate=0.01,
        numeric_noise_rate=0.02,
        random_seed=42,
    ),
)

profile_report = DataProfiler.compare(baseline, perturbed)
print(profile_report.risk_score)
print(profile_report.to_frame())
```

You can also test whether your own analysis function is stable.

```python
import pandas as pd

from data_analysis_stability_evaluator import PerturbationConfig, StabilityEvaluator

df = pd.read_csv("data/baseline.csv")


def analysis(data: pd.DataFrame) -> dict:
    return {
        "row_count": len(data),
        "mean_revenue": data["revenue"].mean(),
        "conversion_rate": data["converted"].mean(),
        "segment_share": data["segment"].value_counts(normalize=True).to_dict(),
    }


config = PerturbationConfig(
    row_drop_rate=0.02,
    missing_rate=0.01,
    numeric_noise_rate=0.02,
    random_seed=42,
)

evaluator = StabilityEvaluator(
    analysis_fn=analysis,
    config=config,
    n_runs=20,
)

report = evaluator.evaluate(df)

print(report.summary)
print(report.details.sort_values("score", ascending=False).head())
```

## Risk score interpretation

The risk score is a diagnostic score, not a mathematical guarantee.

Recommended initial interpretation:

| Score | Meaning |
|---:|---|
| 0.00-0.05 | Stable under tested perturbations |
| 0.05-0.15 | Some sensitivity; review affected metrics |
| 0.15+ | Unstable; conclusions may depend on small input changes |

Users should choose perturbation settings and thresholds that match their own domain risk.

The repository root contains project-level files such as GitHub Actions, Docker Compose, documentation, and repository metadata.

The `service/` directory is the Python package project root. Build, test, lint, and package commands are run from `service/`.

## Local development

Create and activate a virtual environment from the repository root:

```bash
python3 -m venv env
source env/bin/activate
python -m pip install --upgrade pip
```

Install the package in editable mode with development tools:

```bash
cd service
python -m pip install -e ".[dev]"
```

Run tests and lint:

```bash
pytest
ruff check src tests examples
```

## Docker Compose workflow

Docker Compose commands are run from the repository root.

Run tests:

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

The Docker build context is `./service`, and the container working directory is `/workspace/service`.

## Requirements management

Runtime dependencies are defined in `service/requirements.in`.

Development and release dependency inputs are:

```text
service/requirements-dev.in
service/requirements-release.in
```

Pinned requirement files are generated with:

```bash
./scripts/freeze-requirements.sh
```

Install the pinned release environment:

```bash
python -m pip install -r service/requirements-release.txt
```

## Build a local distribution

From the repository root:

```bash
source env/bin/activate
python -m pip install --upgrade -r service/requirements-release.txt

cd service
pytest
ruff check src tests examples

rm -rf dist build *.egg-info src/*.egg-info
python -m build
python -m twine check dist/*
```

Expected output:

```text
dist/data_analysis_stability_evaluator-<version>.tar.gz
dist/data_analysis_stability_evaluator-<version>-py3-none-any.whl
```

Inspect the wheel:

```bash
python -m zipfile -l dist/*.whl | grep -E 'data_analysis_stability_evaluator|entry_points|METADATA'
```

## Test the wheel in a clean environment

From `service/`:

```bash
python3 -m venv /tmp/dase-wheel-test
source /tmp/dase-wheel-test/bin/activate

python -m pip install --upgrade pip
python -m pip install dist/*.whl

analysis-stability --help
analysis-stability sample-data --out /tmp/dase-data
analysis-stability profile /tmp/dase-data/baseline.csv /tmp/dase-data/candidate.csv --out /tmp/dase-report.json

python - <<'PY'
from data_analysis_stability_evaluator import DataProfiler, StabilityEvaluator, PerturbationConfig
print("import ok")
PY

deactivate
```

If this passes, the local wheel is installable and the CLI entry point works.

## TestPyPI publishing

This project uses PyPI Trusted Publishing through GitHub Actions.

No local API token is required when Trusted Publishing is configured correctly.

The workflow file is:

```text
.github/workflows/publish.yml
```

The Python package project is:

```text
service/pyproject.toml
```

```text
Actions
→ Publish Python package
→ Run workflow
→ target: testpypi
```

After publishing to TestPyPI, verify installation:

```bash
python3 -m venv /tmp/dase-testpypi
source /tmp/dase-testpypi/bin/activate

python -m pip install --upgrade pip
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  data-analysis-stability-evaluator

analysis-stability --help
analysis-stability sample-data --out /tmp/dase-testpypi-data
analysis-stability profile /tmp/dase-testpypi-data/baseline.csv /tmp/dase-testpypi-data/candidate.csv --out /tmp/dase-testpypi-report.json

deactivate
```

Then run the workflow with:

```text
target: pypi
```

or publish through the release process described in `docs/release.md`.

## Versioning note

Package versions cannot be uploaded twice to PyPI or TestPyPI.

## License

Apache License 2.0.