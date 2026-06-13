"""Flatten nested analysis outputs into comparable scalar metrics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd


def flatten_output(value: Any, *, prefix: str = "") -> dict[str, Any]:
    """Flatten dict/list/Series/DataFrame analysis output to dot-separated keys."""
    rows: dict[str, Any] = {}
    _flatten(value, prefix or "value", rows)
    if set(rows) == {"value"}:
        return rows
    return {key.removeprefix("value."): val for key, val in rows.items()}


def _flatten(value: Any, key: str, rows: dict[str, Any]) -> None:
    if isinstance(value, pd.DataFrame):
        for col in value.columns:
            for idx, item in value[col].items():
                _flatten(item, f"{key}.{col}.{idx}", rows)
        return
    if isinstance(value, pd.Series):
        for idx, item in value.items():
            _flatten(item, f"{key}.{idx}", rows)
        return
    if isinstance(value, Mapping):
        if not value:
            rows[key] = {}
        for child_key, child_value in value.items():
            _flatten(child_value, f"{key}.{child_key}", rows)
        return
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        if not value:
            rows[key] = []
        for idx, child_value in enumerate(value):
            _flatten(child_value, f"{key}.{idx}", rows)
        return
    if isinstance(value, np.generic):
        rows[key] = value.item()
        return
    rows[key] = value
