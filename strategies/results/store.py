"""JSON persistence and retrieval for backtest results."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from strategies.results.models import BacktestResult, BacktestTrade


class BacktestResultStore:
    """Stores and retrieves backtest results by test name, symbols, and attributes."""

    def __init__(self, store_path: str | Path = "results/backtests.json") -> None:
        self.store_path = Path(store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_raw(self) -> list[dict[str, Any]]:
        if not self.store_path.exists():
            return []
        with self.store_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _save_raw(self, payload: list[dict[str, Any]]) -> None:
        with self.store_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def save(self, result: BacktestResult, overwrite: bool = False) -> None:
        rows = self._load_raw()
        key = (result.name, tuple(sorted(result.symbols)))

        existing_index = None
        for idx, row in enumerate(rows):
            if row.get("name") == key[0] and tuple(sorted(row.get("symbols", []))) == key[1]:
                existing_index = idx
                break

        serialized = asdict(result)
        if existing_index is not None:
            if not overwrite:
                raise ValueError(
                    "Result already exists for this test name and symbol set; set overwrite=True to replace it"
                )
            rows[existing_index] = serialized
        else:
            rows.append(serialized)

        self._save_raw(rows)

    def list_all(self) -> list[BacktestResult]:
        return [self._to_result(row) for row in self._load_raw()]

    def get_by_name(self, name: str) -> list[BacktestResult]:
        return [result for result in self.list_all() if result.name == name]

    def get_by_symbol(self, symbol: str) -> list[BacktestResult]:
        return [result for result in self.list_all() if symbol in result.symbols]

    def filter_by_attributes(self, **attrs: Any) -> list[BacktestResult]:
        matching: list[BacktestResult] = []
        for result in self.list_all():
            if all(getattr(result, key, None) == value for key, value in attrs.items()):
                matching.append(result)
        return matching

    def trade_index(self) -> list[dict[str, Any]]:
        index: list[dict[str, Any]] = []
        for result in self.list_all():
            for trade in result.trades:
                index.append(
                    {
                        "test_name": result.name,
                        "strategy_class": result.strategy_class,
                        "symbol": trade.symbol,
                        "entry_date": trade.entry_date,
                        "exit_date": trade.exit_date,
                        "pnl": trade.pnl,
                    }
                )
        return index

    @staticmethod
    def _to_result(raw: dict[str, Any]) -> BacktestResult:
        trades = [BacktestTrade(**trade) for trade in raw.get("trades", [])]
        data = {k: v for k, v in raw.items() if k != "trades"}
        return BacktestResult(**data, trades=trades)
