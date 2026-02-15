"""Condition objects used for indicator-driven statistical analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd


_OPERATORS: dict[str, Callable[[pd.Series, float], pd.Series]] = {
    ">": lambda series, value: series > value,
    ">=": lambda series, value: series >= value,
    "<": lambda series, value: series < value,
    "<=": lambda series, value: series <= value,
    "==": lambda series, value: series == value,
    "!=": lambda series, value: series != value,
}


@dataclass(frozen=True)
class IndicatorCondition:
    """Represents one indicator comparison, such as RSI > 70."""

    indicator: str
    operator: str
    threshold: float

    def evaluate(self, frame: pd.DataFrame) -> pd.Series:
        if self.operator not in _OPERATORS:
            raise ValueError(f"Unsupported operator: {self.operator}")
        if self.indicator not in frame.columns:
            raise KeyError(f"Indicator '{self.indicator}' is not present in the dataset")
        return _OPERATORS[self.operator](frame[self.indicator], self.threshold).fillna(False)

    @property
    def label(self) -> str:
        return f"{self.indicator} {self.operator} {self.threshold}"
