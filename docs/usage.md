# Usage guide

## 1. Decide what must be stable

For a general data analysis project, define the outputs that matter:

- total rows used in analysis
- missing-rate assumptions
- feature averages or medians
- group rankings
- correlations
- conversion rates
- model predictions
- final business recommendation flags

Then wrap those outputs in a Python function that returns a dictionary.

## 2. Run repeated perturbation checks

```python
from analysis_stability import PerturbationConfig, StabilityEvaluator

config = PerturbationConfig(
    row_drop_rate=0.02,
    missing_rate=0.01,
    numeric_noise_rate=0.02,
    random_seed=42,
)

evaluator = StabilityEvaluator(analysis_fn=my_analysis, config=config, n_runs=50)
report = evaluator.evaluate(df)
```

## 3. Interpret the risk score

The risk score is a diagnostic score, not a mathematical guarantee.

Recommended initial interpretation:

| Score | Meaning |
|---:|---|
| 0.00-0.05 | Stable under tested perturbations |
| 0.05-0.15 | Some sensitivity; review affected metrics |
| 0.15+ | Unstable; conclusions may depend on small input changes |

## 4. Review unstable metrics

```python
report.details.sort_values("score", ascending=False).head(20)
```

Focus on rows where `severity` is `medium` or `high`.
