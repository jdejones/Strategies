# Strategies

A Python repository for indicator-driven statistical analysis and `backtrader`-based strategy validation.

Only run backtests using backtrader.

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


# Inter-day data for this repository must be imported using functions from \data.
- Data has already been processed and contains indicators in the respective dataframes
- symbols is a dictionary with symbols as keys and SymbolData objects as values
- Each symbol data object has a .df attribute that is the OHLCV data with indicator values


Refer to the jupyter notebooks(.ipynb files) prefixed by example_... for examples of how this repository is exepected to be used.

# Intra-day price data
- When able price data should be imported as a single API call using one of the following functions from price_data_import.py
## Intra-day data must be imported using the functions from price_data_import
- intraday_import
- nonconsecutive_intraday_import
- fragmented_intraday_import

