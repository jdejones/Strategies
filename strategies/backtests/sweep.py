"""Condition-set sweep engine built on backtrader event-driven runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from statistics import mean
from typing import Any, Iterable, Mapping

import pandas as pd

from strategies.analysis import IndicatorCondition, ProbabilityAnalyzer
from strategies.backtests.runner import BacktestRunner
from strategies.optimization.expected_value import (
    ExpectedValueStats,
    expected_value_from_outcomes,
    pooled_expected_value_by_group,
)
from strategies.results import BacktestResultStore

_OPERATOR_SLUGS = {
    ">": "gt",
    ">=": "ge",
    "<": "lt",
    "<=": "le",
    "==": "eq",
    "!=": "ne",
}


@dataclass(frozen=True)
class ConditionVariant:
    """Single concrete condition generated from a template."""

    template_name: str
    condition: IndicatorCondition
    parameters: dict[str, Any]
    slug: str


@dataclass(frozen=True)
class ConditionTemplate:
    """Template used to generate condition variants across indicator presets."""

    name: str
    indicator_template: str
    operator: str
    threshold_values: tuple[float, ...]
    parameter_grid: Mapping[str, tuple[Any, ...]] = field(default_factory=dict)

    def expand(self) -> list[ConditionVariant]:
        """Expand template into concrete variants using the parameter grid."""

        keys = tuple(self.parameter_grid.keys())
        value_sets = tuple(self.parameter_grid[key] for key in keys)
        param_combos = product(*value_sets) if keys else [()]

        variants: list[ConditionVariant] = []
        op_slug = _OPERATOR_SLUGS.get(self.operator, self.operator)
        for combo in param_combos:
            params = {key: combo[idx] for idx, key in enumerate(keys)}
            indicator_name = self.indicator_template.format(**params)
            for threshold in self.threshold_values:
                condition = IndicatorCondition(indicator_name, self.operator, float(threshold))
                slug_parts = [self.name, indicator_name, op_slug, str(threshold)]
                for key, value in params.items():
                    slug_parts.append(f"{key}_{value}")
                slug = "_".join(str(part).replace(" ", "") for part in slug_parts)
                full_params = dict(params)
                full_params["threshold"] = float(threshold)
                variants.append(
                    ConditionVariant(
                        template_name=self.name,
                        condition=condition,
                        parameters=full_params,
                        slug=slug,
                    )
                )
        return variants


@dataclass(frozen=True)
class ConditionSet:
    """A concrete combination of conditions to backtest as one setup."""

    set_id: str
    name: str
    conditions: tuple[IndicatorCondition, ...]
    parameters: dict[str, Any]


@dataclass(frozen=True)
class ConditionSetEvaluation:
    """Backtest and expected-value comparison output for one condition set."""

    condition_set: ConditionSet
    overall_stats: ExpectedValueStats
    per_symbol_stats: dict[str, ExpectedValueStats]
    symbol_trade_counts: dict[str, int]
    total_trades: int
    mean_symbol_expected_value: float
    backtest_result_names: tuple[str, ...]


class ConditionSweepEngine:
    """Generate and evaluate condition-set sweeps across symbols."""

    def __init__(
        self,
        *,
        runner: BacktestRunner | None = None,
        result_store: BacktestResultStore | None = None,
        overwrite_results: bool = False,
    ) -> None:
        self.runner = runner or BacktestRunner()
        self.result_store = result_store
        self.overwrite_results = overwrite_results

    @staticmethod
    def generate_condition_sets(
        templates: Iterable[ConditionTemplate],
        *,
        set_name_prefix: str = "condition_set",
    ) -> list[ConditionSet]:
        """Build cartesian-product condition sets from template variants."""

        template_list = list(templates)
        expanded = [template.expand() for template in template_list]
        if not expanded:
            return []

        condition_sets: list[ConditionSet] = []
        for idx, combo in enumerate(product(*expanded), start=1):
            set_id = "__".join(variant.slug for variant in combo)
            name = f"{set_name_prefix}_{idx:04d}"
            conditions = tuple(variant.condition for variant in combo)
            parameters: dict[str, Any] = {}
            for variant in combo:
                for key, value in variant.parameters.items():
                    parameters[f"{variant.template_name}.{key}"] = value
            condition_sets.append(
                ConditionSet(
                    set_id=set_id,
                    name=name,
                    conditions=conditions,
                    parameters=parameters,
                )
            )
        return condition_sets

    def run_sweep(
        self,
        *,
        sweep_name: str,
        condition_sets: Iterable[ConditionSet],
        data_by_symbol: Mapping[str, pd.DataFrame],
        hold_bars: int = 1,
        close_column: str = "close",
        metadata: Mapping[str, Any] | None = None,
    ) -> list[ConditionSetEvaluation]:
        """Run all condition sets per symbol using backtrader event-driven backtests."""

        evaluations: list[ConditionSetEvaluation] = []
        shared_metadata = dict(metadata or {})

        for condition_set in condition_sets:
            outcomes_by_symbol: dict[str, list[float]] = {}
            per_symbol_stats: dict[str, ExpectedValueStats] = {}
            symbol_trade_counts: dict[str, int] = {}
            result_names: list[str] = []

            for symbol, frame in data_by_symbol.items():
                if not isinstance(frame.index, pd.DatetimeIndex):
                    raise TypeError(f"Data for {symbol} must use a DatetimeIndex")

                analyzer = ProbabilityAnalyzer(frame, close_column=close_column)
                mask = analyzer.build_mask(condition_set.conditions)
                event_dates = tuple(frame.index[mask.fillna(False)].date)

                outcomes: list[float] = []
                result_name = f"{sweep_name}:{condition_set.name}:{symbol}"
                if event_dates:
                    run_metadata = {
                        "sweep_name": sweep_name,
                        "condition_set_id": condition_set.set_id,
                        "condition_set_name": condition_set.name,
                        "condition_labels": [c.label for c in condition_set.conditions],
                        "condition_parameters": dict(condition_set.parameters),
                        "symbol": symbol,
                        **shared_metadata,
                    }
                    result = self.runner.run_event_backtest(
                        name=result_name,
                        data_by_symbol={symbol: frame},
                        event_dates_by_symbol={symbol: event_dates},
                        hold_bars=hold_bars,
                        metadata=run_metadata,
                    )
                    outcomes = [trade.pnl for trade in result.trades]
                    if self.result_store is not None:
                        self.result_store.save(result, overwrite=self.overwrite_results)

                outcomes_by_symbol[symbol] = outcomes
                per_symbol_stats[symbol] = expected_value_from_outcomes(outcomes)
                symbol_trade_counts[symbol] = len(outcomes)
                result_names.append(result_name)

            overall_stats = pooled_expected_value_by_group(outcomes_by_symbol)
            non_empty_symbol_evs = [
                stats.expected_value
                for stats in per_symbol_stats.values()
                if stats.sample_size > 0
            ]
            mean_symbol_ev = float(mean(non_empty_symbol_evs)) if non_empty_symbol_evs else 0.0

            evaluations.append(
                ConditionSetEvaluation(
                    condition_set=condition_set,
                    overall_stats=overall_stats,
                    per_symbol_stats=per_symbol_stats,
                    symbol_trade_counts=symbol_trade_counts,
                    total_trades=sum(symbol_trade_counts.values()),
                    mean_symbol_expected_value=mean_symbol_ev,
                    backtest_result_names=tuple(result_names),
                )
            )

        return evaluations
