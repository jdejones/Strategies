"""Base strategy definitions built on backtrader strategy objects."""

from __future__ import annotations

import backtrader as bt


class BaseSignalStrategy(bt.Strategy):
    """Simple base class for long and short signal strategies."""

    params = dict(allow_long=True, allow_short=False)

    def signal_long(self) -> bool:
        return False

    def signal_short(self) -> bool:
        return False

    def signal_exit(self) -> bool:
        return False

    def next(self) -> None:
        if not self.position:
            if self.p.allow_long and self.signal_long():
                self.buy()
            elif self.p.allow_short and self.signal_short():
                self.sell()
        elif self.signal_exit():
            self.close()
