"""Data loading utilities for local pickled market data."""

from __future__ import annotations

from pathlib import Path
import pickle
import runpy
import sys
from typing import Any

from strategies.utils.config import RepositoryPaths


def add_market_data_to_syspath(paths: RepositoryPaths | None = None) -> Path:
    """Add the sibling market_data repository to ``sys.path`` for imports."""

    repo_paths = paths or RepositoryPaths.from_environment()
    market_data_root = repo_paths.market_data_root.resolve()
    # To `import market_data`, sys.path must contain the *parent* of the package dir.
    # If MARKET_DATA_ROOT points directly at the `market_data/` package, use its parent.
    if (market_data_root / "__init__.py").exists():
        sys_path_target = market_data_root.parent
    else:
        sys_path_target = market_data_root

    path_str = str(sys_path_target)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
    return market_data_root


def load_pickled_variables(pickle_path: str | Path) -> Any:
    """Load any pickled object produced by the market_data preprocessing scripts."""

    data_path = Path(pickle_path)
    with data_path.open("rb") as handle:
        return pickle.load(handle)


def load_daily_variables(
    paths: RepositoryPaths | None = None,
    filename: str = "daily_variables.pkl",
    *,
    script_filename: str = "load_daily_variables.py",
    return_key: str = "symbols",
) -> Any:
    """Load the daily variables produced by the sibling `market_data` repo.

    Behavior:
    - If `MARKET_DATA_ROOT/scripts/<filename>` exists, unpickle it directly.
    - Otherwise, execute `MARKET_DATA_ROOT/scripts/<script_filename>` as `__main__`
      (so it can import the required `market_data.*` classes) and return the
      requested object from its globals (defaults to `symbols`).
    """

    repo_paths = paths or RepositoryPaths.from_environment()
    market_data_root = repo_paths.market_data_root
    scripts_dir = market_data_root / "scripts"

    # Ensure `market_data` imports (and pickled class resolution) can work.
    add_market_data_to_syspath(repo_paths)

    candidate_pickle = scripts_dir / filename
    if candidate_pickle.exists():
        return load_pickled_variables(candidate_pickle)

    script_path = scripts_dir / script_filename
    if not script_path.exists():
        raise FileNotFoundError(
            f"Neither pickle nor loader script found.\n"
            f"- Missing pickle: {candidate_pickle}\n"
            f"- Missing script: {script_path}\n"
            f"Set DAILY_VARIABLES_PATH to a known pickle, or fix MARKET_DATA_ROOT."
        )

    # Execute the external script in-process so we can retrieve the loaded objects.
    # `run_name="__main__"` is critical: that script imports required classes only
    # in its `if __name__ == '__main__'` block.
    globals_after_run = runpy.run_path(str(script_path), run_name="__main__")

    if return_key in globals_after_run:
        return globals_after_run[return_key]

    loaded = globals_after_run.get("loaded")
    if isinstance(loaded, dict) and return_key in loaded:
        return loaded[return_key]

    available_keys = sorted([k for k in globals_after_run.keys() if not k.startswith("__")])
    raise KeyError(
        f"Executed {script_path} but could not find {return_key!r} in its globals.\n"
        f"Available keys (sample): {available_keys[:50]}"
    )
