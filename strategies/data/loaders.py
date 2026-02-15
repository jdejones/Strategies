"""Data loading utilities for local pickled market data."""

from __future__ import annotations

from pathlib import Path
import pickle
import sys
from typing import Any

from strategies.utils.config import RepositoryPaths


def add_market_data_to_syspath(paths: RepositoryPaths | None = None) -> Path:
    """Add the sibling market_data repository to ``sys.path`` for imports."""

    repo_paths = paths or RepositoryPaths.from_environment()
    market_data_path = repo_paths.market_data_root.resolve()
    path_str = str(market_data_path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
    return market_data_path


def load_pickled_variables(pickle_path: str | Path) -> Any:
    """Load any pickled object produced by the market_data preprocessing scripts."""

    data_path = Path(pickle_path)
    with data_path.open("rb") as handle:
        return pickle.load(handle)


def load_daily_variables(paths: RepositoryPaths | None = None, filename: str = "daily_variables.pkl") -> Any:
    """Convenience loader for daily-variable artifacts from market_data scripts."""

    repo_paths = paths or RepositoryPaths.from_environment()
    candidate = repo_paths.market_data_root / "scripts" / filename
    return load_pickled_variables(candidate)
