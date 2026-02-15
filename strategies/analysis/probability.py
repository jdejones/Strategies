"""Probability and outcome-distribution analysis built around indicator conditions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from strategies.analysis.conditions import IndicatorCondition


@dataclass
class ProbabilitySummary:
    condition_labels: list[str]
    sample_size: int
    occurrence_rate: float
    forward_return_probabilities: dict[str, float]
    forward_return_medians: dict[str, float]


class ProbabilityAnalyzer:
    """Computes occurrence probabilities and conditional forward-return outcomes."""

    def __init__(self, frame: pd.DataFrame, close_column: str = "close") -> None:
        if close_column not in frame.columns:
            raise KeyError(f"'{close_column}' must be present in the input DataFrame")
        self.frame = frame.copy()
        self.close_column = close_column

    def build_mask(self, conditions: Iterable[IndicatorCondition]) -> pd.Series:
        conditions = list(conditions)
        if not conditions:
            return pd.Series(True, index=self.frame.index)
        mask = pd.Series(True, index=self.frame.index)
        for condition in conditions:
            mask &= condition.evaluate(self.frame)
        return mask

    def summarize(
        self,
        conditions: Iterable[IndicatorCondition],
        horizons: Iterable[int] = (1, 5),
    ) -> ProbabilitySummary:
        condition_list = list(conditions)
        mask = self.build_mask(condition_list)
        sample_size = int(mask.sum())
        occurrence_rate = float(mask.mean())

        forward_positive: dict[str, float] = {}
        forward_medians: dict[str, float] = {}
        for horizon in horizons:
            pct_returns = self.frame[self.close_column].shift(-horizon) / self.frame[self.close_column] - 1
            conditioned = pct_returns[mask].dropna()
            key = f"t_plus_{horizon}"
            if conditioned.empty:
                forward_positive[key] = 0.0
                forward_medians[key] = 0.0
            else:
                forward_positive[key] = float((conditioned > 0).mean())
                forward_medians[key] = float(conditioned.median())

        return ProbabilitySummary(
            condition_labels=[c.label for c in condition_list],
            sample_size=sample_size,
            occurrence_rate=occurrence_rate,
            forward_return_probabilities=forward_positive,
            forward_return_medians=forward_medians,
        )
