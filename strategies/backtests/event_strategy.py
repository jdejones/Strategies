"""Event-aware backtrader strategy helper for date-driven entries."""

from __future__ import annotations

from datetime import date
from typing import Iterable

from strategies.backtests.strategy_base import BaseSignalStrategy


class EventDrivenStrategy(BaseSignalStrategy):
    """Executes entries on event dates while still supporting rule-based exits."""

    params = dict(event_dates=(), hold_bars=1, allow_long=True, allow_short=False)

    def __init__(self) -> None:
        self._event_dates: set[date] = {d if isinstance(d, date) else d.date() for d in self.p.event_dates}
        self._bars_since_entry = 0

    @staticmethod
    def normalize_dates(values: Iterable) -> tuple[date, ...]:
        normalized = []
        for value in values:
            normalized.append(value if isinstance(value, date) else value.date())
        return tuple(normalized)

    def signal_long(self) -> bool:
        current_date = self.datas[0].datetime.date(0)
        return current_date in self._event_dates

    def signal_exit(self) -> bool:
        if self.position:
            self._bars_since_entry += 1
        else:
            self._bars_since_entry = 0
        return self.position and self._bars_since_entry >= self.p.hold_bars
