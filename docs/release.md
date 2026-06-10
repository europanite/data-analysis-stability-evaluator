# Release and PyPI publishing

This project publishes `analysis-stability-evaluator` as a Python package.

## Release flow

1. Update `version` in `pyproject.toml`.
2. Commit and push to `main`.
3. Confirm the `CI` workflow passes.
4. Run the `Publish Python package` workflow manually with `target=testpypi`.
5. Confirm TestPyPI installation works:

```bash
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ analysis-stability-evaluator
analysis-stability sample-data --out data
analysis-stability profile data/baseline.csv data/candidate.csv --out reports/profile_stability.json
```

6. Create a GitHub Release whose tag exactly matches the package version, for example `v0.1.1`.
7. After protected-environment approval, the workflow publishes the same checked distribution artifacts to PyPI.

## Trusted Publisher configuration

Configure pending publishers in PyPI and TestPyPI.

Use these values:

| Field | PyPI | TestPyPI |
|---|---|---|
| PyPI project name | `analysis-stability-evaluator` | `analysis-stability-evaluator` |
| Owner | `europanite` | `europanite` |
| Repository | `analysis-stability-evaluator` | `analysis-stability-evaluator` |
| Workflow file | `publish.yml` | `publish.yml` |
| Environment | `pypi` | `testpypi` |

No `PYPI_API_TOKEN` secret is required when Trusted Publishing is configured correctly.
