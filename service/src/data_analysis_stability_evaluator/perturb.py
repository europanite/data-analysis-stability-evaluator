"""Data perturbation utilities."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, replace

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PerturbationConfig:
    """Configuration for small data changes.

    All rates are fractions in [0, 1]. They are intentionally explicit so the
    perturbation policy is visible in code reviews and reports.
    """

    row_drop_rate: float = 0.01
    row_duplicate_rate: float = 0.00
    missing_rate: float = 0.00
    numeric_noise_rate: float = 0.00
    numeric_noise_scale: float = 0.05
    categorical_swap_rate: float = 0.00
    random_seed: int | None = 42

    def with_seed(self, seed: int | None) -> PerturbationConfig:
        return replace(self, random_seed=seed)


def _check_rate(name: str, value: float) -> None:
    if value < 0 or value > 1:
        raise ValueError(f"{name} must be in [0, 1], got {value}")


def validate_config(config: PerturbationConfig) -> None:
    for field in [
        "row_drop_rate",
        "row_duplicate_rate",
        "missing_rate",
        "numeric_noise_rate",
        "numeric_noise_scale",
        "categorical_swap_rate",
    ]:
        _check_rate(field, float(getattr(config, field)))


def perturb_dataframe(df: pd.DataFrame, config: PerturbationConfig) -> pd.DataFrame:
    """Return a perturbed copy of a dataframe."""
    validate_config(config)
    rng = np.random.default_rng(config.random_seed)
    out = df.copy(deep=True)

    # Drop rows.
    if config.row_drop_rate > 0 and len(out) > 0:
        keep_mask = rng.random(len(out)) >= config.row_drop_rate
        if keep_mask.sum() == 0:
            keep_mask[rng.integers(0, len(out))] = True
        out = out.loc[keep_mask].copy()

    # Duplicate rows.
    if config.row_duplicate_rate > 0 and len(out) > 0:
        n_dup = int(round(len(out) * config.row_duplicate_rate))
        if n_dup > 0:
            dup_idx = rng.choice(out.index.to_numpy(), size=n_dup, replace=True)
            out = pd.concat([out, out.loc[dup_idx]], ignore_index=True)
        else:
            out = out.reset_index(drop=True)
    else:
        out = out.reset_index(drop=True)

    # Inject missing values.
    if config.missing_rate > 0 and len(out) > 0 and len(out.columns) > 0:
        mask = rng.random(out.shape) < config.missing_rate
        for j, col in enumerate(out.columns):
            if mask[:, j].any():
                out.loc[mask[:, j], col] = np.nan

    # Numeric noise.
    numeric_cols = [c for c in out.columns if pd.api.types.is_numeric_dtype(out[c])]
    if config.numeric_noise_rate > 0 and numeric_cols and len(out) > 0:
        for col in numeric_cols:
            values = pd.to_numeric(out[col], errors="coerce")
            std = float(values.std(ddof=0)) if values.notna().any() else 0.0
            if std == 0.0:
                std = max(abs(float(values.mean())) if values.notna().any() else 1.0, 1.0)
            mask = rng.random(len(out)) < config.numeric_noise_rate
            if mask.any():
                # Numeric noise may turn integer columns into floats. Cast the
                # working column explicitly to avoid pandas dtype warnings and
                # make the perturbation behavior deterministic.
                out[col] = values.astype(float)
                noise = rng.normal(loc=0.0, scale=std * config.numeric_noise_scale, size=len(out))
                out.loc[mask, col] = values.loc[mask].astype(float) + noise[mask]

    # Categorical swaps.
    categorical_cols = [c for c in out.columns if not pd.api.types.is_numeric_dtype(out[c])]
    if config.categorical_swap_rate > 0 and categorical_cols and len(out) > 1:
        for col in categorical_cols:
            mask = rng.random(len(out)) < config.categorical_swap_rate
            source_values = out[col].dropna().to_numpy()
            if source_values.size > 0 and mask.any():
                out.loc[mask, col] = rng.choice(source_values, size=int(mask.sum()), replace=True)

    return out


def generate_perturbations(
    df: pd.DataFrame,
    config: PerturbationConfig,
    *,
    n_runs: int,
) -> Iterator[tuple[int, pd.DataFrame]]:
    """Yield multiple perturbed dataframes with deterministic derived seeds."""
    base_seed = 0 if config.random_seed is None else int(config.random_seed)
    for run in range(n_runs):
        seed = None if config.random_seed is None else base_seed + run
        yield run, perturb_dataframe(df, config.with_seed(seed))