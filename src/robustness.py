"""Deterministic post-experiment robustness calculations; does not write experiments."""
from __future__ import annotations

import numpy as np
import pandas as pd

try:
    from .backtest_momentum import build_backtest, read_adjusted_close
    from .metrics import performance_metrics
except ImportError:  # pragma: no cover
    from backtest_momentum import build_backtest, read_adjusted_close
    from metrics import performance_metrics


def metrics_for_returns(returns: pd.Series) -> dict:
    equity = (1.0 + returns).cumprod()
    zeros = pd.Series(0.0, index=returns.index)
    return performance_metrics(returns, equity, zeros, zeros)


def cost_sensitivity(gross_returns: pd.Series, turnover: pd.Series, cost_bps: list[int]) -> pd.DataFrame:
    """Reprice saved gross returns with the MOM-001 execution-cost convention."""
    rows = []
    for bps in cost_bps:
        costs = (1.0 + gross_returns) * turnover * (bps / 10_000.0)
        net = gross_returns - costs
        values = metrics_for_returns(net)
        rows.append({"cost_bps": bps, **values, "cost_return_sum": float(costs.sum())})
    return pd.DataFrame(rows).set_index("cost_bps")


def leave_one_out(prices: pd.DataFrame, benchmark: pd.Series) -> pd.DataFrame:
    """Run fixed MOM rules after removing each current-universe ticker in turn."""
    rows = []
    for excluded in prices.columns:
        result = build_backtest(prices.drop(columns=excluded), benchmark)
        rows.append({"excluded_ticker": excluded, **result.net_metrics})
    return pd.DataFrame(rows).set_index("excluded_ticker")


def fixed_calendar_periods(returns: pd.Series) -> pd.DataFrame:
    """Use predeclared non-overlapping calendar blocks, without choosing winners."""
    rows = []
    for name, start, end in (
        ("2015-2018", "2015-01-01", "2018-12-31"),
        ("2019-2022", "2019-01-01", "2022-12-31"),
        ("2023-2026_partial", "2023-01-01", "2026-12-31"),
    ):
        block = returns.loc[start:end]
        rows.append({"period": name, "start": block.index[0].date().isoformat(), "end": block.index[-1].date().isoformat(), **metrics_for_returns(block)})
    return pd.DataFrame(rows).set_index("period")


def drawdown_duration(returns: pd.Series) -> dict:
    equity = (1.0 + returns).cumprod()
    underwater = equity < equity.cummax()
    longest = current = 0
    for value in underwater:
        current = current + 1 if value else 0
        longest = max(longest, current)
    return {"longest_underwater_sessions": longest, "ends_underwater": bool(underwater.iloc[-1])}


def moving_block_bootstrap(
    returns: pd.Series, *, block_length: int = 21, samples: int = 2000, seed: int = 20261123
) -> pd.DataFrame:
    """Moving-block bootstrap retaining contiguous blocks of observed daily returns."""
    if block_length < 1 or block_length > len(returns):
        raise ValueError("block_length must be between 1 and the number of returns")
    rng = np.random.default_rng(seed)
    values = returns.to_numpy(dtype=float)
    starts = np.arange(len(values) - block_length + 1)
    rows = []
    for _ in range(samples):
        pieces = []
        while sum(len(piece) for piece in pieces) < len(values):
            start = int(rng.choice(starts))
            pieces.append(values[start:start + block_length])
        simulated = pd.Series(np.concatenate(pieces)[:len(values)])
        result = metrics_for_returns(simulated)
        rows.append({"total_return": result["total_return"], "CAGR": result["CAGR"], "Sharpe": result["Sharpe_ratio_rf_0"]})
    return pd.DataFrame(rows)


def load_prices(data_dir, tickers: list[str]) -> pd.DataFrame:
    return pd.DataFrame({
        ticker: read_adjusted_close(data_dir / f"{ticker.replace('.', '_')}.csv") for ticker in tickers
    }).sort_index()
