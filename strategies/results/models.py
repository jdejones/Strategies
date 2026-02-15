"""Result models for persisted backtest outputs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BacktestTrade:
    symbol: str
    entry_date: str
    exit_date: str
    size: float
    pnl: float


@dataclass
class BacktestResult:
    name: str
    symbols: list[str]
    strategy_class: str
    started_at: str
    finished_at: str
    initial_value: float
    final_value: float
    net_pnl: float
    trades: list[BacktestTrade] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
