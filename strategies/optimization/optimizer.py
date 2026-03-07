"""Optimization helpers for ranking condition-set evaluations by expected value."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from strategies.backtests.sweep import ConditionSetEvaluation


@dataclass(frozen=True)
class RankedConditionSet:
    """Ranking entry for a condition set under a chosen expected-value objective."""

    rank: int
    set_id: str
    set_name: str
    objective_expected_value: float
    objective_sample_size: int
    overall_expected_value: float
    overall_sample_size: int
    total_trades: int


class ExpectedValueOptimizer:
    """Rank condition sets by expected value overall or per symbol."""

    def rank(
        self,
        evaluations: Iterable["ConditionSetEvaluation"],
        *,
        symbol: str | None = None,
        min_sample_size: int = 1,
        top_n: int | None = None,
    ) -> list[RankedConditionSet]:
        scored: list[tuple["ConditionSetEvaluation", float, int]] = []

        for evaluation in evaluations:
            if symbol is None:
                obj_ev = evaluation.overall_stats.expected_value
                obj_n = evaluation.overall_stats.sample_size
            else:
                symbol_stats = evaluation.per_symbol_stats.get(symbol)
                if symbol_stats is None:
                    continue
                obj_ev = symbol_stats.expected_value
                obj_n = symbol_stats.sample_size

            if obj_n < min_sample_size:
                continue

            scored.append((evaluation, obj_ev, obj_n))

        scored.sort(
            key=lambda row: (
                row[1],
                row[2],
                row[0].overall_stats.expected_value,
                row[0].overall_stats.sample_size,
            ),
            reverse=True,
        )

        if top_n is not None:
            scored = scored[:top_n]

        ranked: list[RankedConditionSet] = []
        for idx, (evaluation, obj_ev, obj_n) in enumerate(scored, start=1):
            ranked.append(
                RankedConditionSet(
                    rank=idx,
                    set_id=evaluation.condition_set.set_id,
                    set_name=evaluation.condition_set.name,
                    objective_expected_value=float(obj_ev),
                    objective_sample_size=int(obj_n),
                    overall_expected_value=float(evaluation.overall_stats.expected_value),
                    overall_sample_size=int(evaluation.overall_stats.sample_size),
                    total_trades=int(evaluation.total_trades),
                )
            )

        return ranked
