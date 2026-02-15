# Strategies

A Python repository for indicator-driven statistical analysis and `backtrader`-based strategy validation.

## What this repo now provides

- A `strategies` package with clear modules for:
  - statistical condition definitions and probability analysis,
  - backtesting runners and base strategy objects rooted in `backtrader`,
  - JSON persistence and retrieval of backtest results,
  - local integration helpers for sibling `market_data` repository loading.

## Package layout

- `strategies/analysis`
  - `IndicatorCondition`: reusable condition object (e.g., RSI > 70)
  - `ProbabilityAnalyzer`: occurrence and forward-return distribution summaries
- `strategies/backtests`
  - `BaseSignalStrategy`: common long/short signal skeleton inheriting from `bt.Strategy`
  - `EventDrivenStrategy`: date-driven entries for event-based testing
  - `BacktestRunner`: single/multi-symbol run orchestration + trade capture
- `strategies/results`
  - `BacktestResult`: normalized result model
  - `BacktestResultStore`: JSON persistence/retrieval with overwrite control
- `strategies/data`
  - `add_market_data_to_syspath`: local import path helper for sibling repo
  - `load_daily_variables` / `load_pickled_variables`: direct loading of preprocessed pickles

## Result storage behavior

Backtest results are stored in JSON and can be:

- named (`BacktestResult.name`),
- accessed by test name and symbols,
- overwritten intentionally with `overwrite=True`,
- queried by attributes,
- flattened to a trade index containing symbol and entry/exit dates.

## Quick usage

```python
from strategies.analysis import IndicatorCondition, ProbabilityAnalyzer
from strategies.results import BacktestResultStore

conditions = [
    IndicatorCondition("rsi", ">", 70),
    IndicatorCondition("rvol", ">", 2),
]

summary = ProbabilityAnalyzer(df, close_column="close").summarize(conditions, horizons=(1, 5, 10))

store = BacktestResultStore("results/backtests.json")
store.save(backtest_result, overwrite=True)
hot_setups = store.get_by_symbol("AAPL")
```

## Notes

- The package is notebook-friendly and importable from scripts/CLI.
- By default, `market_data` path integration expects a shared root at `C:\Users\jdejo` and can be overridden with:
  - `STRATEGIES_SHARED_ROOT`
  - `MARKET_DATA_ROOT`
