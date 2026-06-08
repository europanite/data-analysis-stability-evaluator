"""Flatten nested analysis outputs into comparable key-value pairs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd


def flatten_output(value: Any, *, prefix: str = "") -> dict[str, Any]:
    """Flatten dicts, pandas objects, numpy arrays, and simple sequences."""
    if isinstance(value, pd.DataFrame):
        records: dict[str, Any] = {}
        for col in value.columns:
            if pd.api.types.is_numeric_dtype(value[col]):
                records[f"{prefix}{col}.mean"] = float(value[col].mean())
                records[f"{prefix}{col}.sum"] = float(value[col].sum())
            else:
                for key, count in value[col].astype(str).value_counts(normalize=True).items():
                    records[f"{prefix}{col}.share.{key}"] = float(count)
        return records

    if isinstance(value, pd.Series):
        return flatten_output(value.to_dict(), prefix=prefix)

    if isinstance(value, np.ndarray):
        return flatten_output(value.tolist(), prefix=prefix)

    if isinstance(value, Mapping):
        records = {}
        for key, item in value.items():
            child_prefix = f"{prefix}{key}." if prefix else f"{key}."
            records.update(flatten_output(item, prefix=child_prefix))
        return records

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        records = {}
        for i, item in enumerate(value):
            records.update(flatten_output(item, prefix=f"{prefix}{i}."))
        return records

    name = prefix[:-1] if prefix.endswith(".") else prefix or "value"
    return {name: value}
