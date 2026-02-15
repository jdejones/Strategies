"""Backtrader runner utilities for single/multi-symbol and event-driven tests."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Iterable, Mapping, Type

import backtrader as bt
import pandas as pd

from strategies.backtests.event_strategy import EventDrivenStrategy
from strategies.results.models import BacktestResult, BacktestTrade


class TradeCaptureAnalyzer(bt.Analyzer):
    """Collect closed-trade metadata for persistence and retrieval."""

    def start(self) -> None:
        self.trades: list[dict] = []

    def notify_trade(self, trade) -> None:
        if not trade.isclosed:
            return
        data_name = trade.data._name or "UNKNOWN"
        entry_dt = bt.num2date(trade.dtopen)
        exit_dt = bt.num2date(trade.dtclose)
        self.trades.append(
            {
                "symbol": data_name,
                "entry_date": entry_dt.isoformat(),
                "exit_date": exit_dt.isoformat(),
                "size": float(trade.size),
                "pnl": float(trade.pnlcomm),
            }
        )

    def get_analysis(self):
        return self.trades


class BacktestRunner:
    """Coordinates statistical-condition handoff into backtrader backtests."""

    def __init__(self, cash: float = 100_000.0, commission: float = 0.001) -> None:
        self.cash = cash
        self.commission = commission

    def _build_cerebro(self) -> bt.Cerebro:
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(self.cash)
        cerebro.broker.setcommission(commission=self.commission)
        cerebro.addanalyzer(TradeCaptureAnalyzer, _name="trade_capture")
        return cerebro

    def _add_datafeeds(self, cerebro: bt.Cerebro, data_by_symbol: Mapping[str, pd.DataFrame]) -> None:
        for symbol, frame in data_by_symbol.items():
            if not isinstance(frame.index, pd.DatetimeIndex):
                raise TypeError(f"Data for {symbol} must use a DatetimeIndex")
            feed = bt.feeds.PandasData(dataname=frame)
            cerebro.adddata(feed, name=symbol)

    def run(
        self,
        name: str,
        strategy_cls: Type[bt.Strategy],
        data_by_symbol: Mapping[str, pd.DataFrame],
        strategy_kwargs: dict | None = None,
        metadata: dict | None = None,
    ) -> BacktestResult:
        strategy_kwargs = strategy_kwargs or {}
        cerebro = self._build_cerebro()
        self._add_datafeeds(cerebro, data_by_symbol)
        cerebro.addstrategy(strategy_cls, **strategy_kwargs)
        starting_value = float(cerebro.broker.getvalue())
        run_results = cerebro.run()
        ending_value = float(cerebro.broker.getvalue())

        strategy = run_results[0]
        trade_data = strategy.analyzers.trade_capture.get_analysis()
        trades = [BacktestTrade(**trade) for trade in trade_data]
        symbols = sorted(list(data_by_symbol.keys()))

        return BacktestResult(
            name=name,
            symbols=symbols,
            strategy_class=strategy_cls.__name__,
            started_at=datetime.utcnow().isoformat(),
            finished_at=datetime.utcnow().isoformat(),
            initial_value=starting_value,
            final_value=ending_value,
            net_pnl=ending_value - starting_value,
            trades=trades,
            metadata=metadata or {},
        )

    def run_event_backtest(
        self,
        name: str,
        data_by_symbol: Mapping[str, pd.DataFrame],
        event_dates_by_symbol: Mapping[str, Iterable],
        hold_bars: int = 1,
        metadata: dict | None = None,
    ) -> BacktestResult:
        strategy_kwargs = {
            "event_dates": EventDrivenStrategy.normalize_dates(
                sorted({d for dates in event_dates_by_symbol.values() for d in dates})
            ),
            "hold_bars": hold_bars,
        }
        merged_metadata = {"event_dates_by_symbol": {k: [str(v) for v in vals] for k, vals in event_dates_by_symbol.items()}}
        if metadata:
            merged_metadata.update(metadata)
        return self.run(
            name=name,
            strategy_cls=EventDrivenStrategy,
            data_by_symbol=data_by_symbol,
            strategy_kwargs=strategy_kwargs,
            metadata=merged_metadata,
        )

    @staticmethod
    def to_dict(result: BacktestResult) -> dict:
        raw = asdict(result)
        raw["trades"] = [asdict(trade) for trade in result.trades]
        return raw
