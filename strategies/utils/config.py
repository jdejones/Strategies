"""Configuration helpers for local repository integration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class RepositoryPaths:
    """Path configuration shared across Strategies workflows."""

    strategies_root: Path
    shared_root: Path
    market_data_root: Path

    @classmethod
    def from_environment(cls, strategies_root: str | Path | None = None) -> "RepositoryPaths":
        root = Path(strategies_root) if strategies_root else Path.cwd()
        configured_shared = os.getenv("STRATEGIES_SHARED_ROOT", r"C:\Users\jdejo")
        shared_root = Path(configured_shared)
        market_data_root = Path(os.getenv("MARKET_DATA_ROOT", str(shared_root / "market_data")))
        return cls(strategies_root=root, shared_root=shared_root, market_data_root=market_data_root)
