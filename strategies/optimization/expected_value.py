"""Expected-value analytics for backtest outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable, Mapping


@dataclass(frozen=True)
class ExpectedValueStats:
    """Expected-value summary for a collection of realized outcomes."""

    expected_value: float
    sample_size: int
    win_rate: float
    loss_rate: float
    avg_win: float
    avg_loss: float
    upside_probability: float
    downside_probability: float


def expected_value_from_outcomes(outcomes: Iterable[float]) -> ExpectedValueStats:
    """Compute expected value and related diagnostics from empirical outcomes."""

    values = [float(v) for v in outcomes]
    sample_size = len(values)
    if sample_size == 0:
        return ExpectedValueStats(
            expected_value=0.0,
            sample_size=0,
            win_rate=0.0,
            loss_rate=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            upside_probability=0.0,
            downside_probability=0.0,
        )

    wins = [v for v in values if v > 0]
    losses = [v for v in values if v < 0]
    win_rate = len(wins) / sample_size
    loss_rate = len(losses) / sample_size
    avg_win = mean(wins) if wins else 0.0
    avg_loss = mean(losses) if losses else 0.0

    # EV on an empirical distribution: sum(outcome * P(outcome)).
    # With observed samples, this equals the arithmetic mean.
    expected_value = float(mean(values))

    return ExpectedValueStats(
        expected_value=expected_value,
        sample_size=sample_size,
        win_rate=float(win_rate),
        loss_rate=float(loss_rate),
        avg_win=float(avg_win),
        avg_loss=float(avg_loss),
        upside_probability=float(win_rate),
        downside_probability=float(loss_rate),
    )


def pooled_expected_value_by_group(
    outcomes_by_group: Mapping[str, Iterable[float]],
) -> ExpectedValueStats:
    """Compute EV by pooling all outcomes from all groups together."""

    pooled: list[float] = []
    for values in outcomes_by_group.values():
        pooled.extend(float(v) for v in values)
    return expected_value_from_outcomes(pooled)
