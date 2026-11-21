"""Performance statistics for daily simple-return and equity-curve series."""
import numpy as np
import pandas as pd


def max_drawdown(equity_curve):
    curve = np.asarray(equity_curve, dtype=float)
    curve = curve[np.isfinite(curve)]
    if not curve.size or np.any(curve <= 0):
        return np.nan
    return float(np.min(curve / np.maximum.accumulate(curve) - 1.0))


def performance_metrics(daily_returns, equity_curve, one_way_turnover, cost_returns, periods_per_year=252):
    returns = pd.Series(daily_returns, dtype=float).replace([np.inf, -np.inf], np.nan).dropna()
    equity = pd.Series(equity_curve, dtype=float).replace([np.inf, -np.inf], np.nan).dropna()
    turnover = pd.Series(one_way_turnover, dtype=float).replace([np.inf, -np.inf], np.nan).dropna()
    costs = pd.Series(cost_returns, dtype=float).replace([np.inf, -np.inf], np.nan).dropna()
    n = len(returns)
    total = float(equity.iloc[-1] - 1.0) if len(equity) else np.nan
    cagr = float(equity.iloc[-1] ** (periods_per_year / n) - 1.0) if n and equity.iloc[-1] > 0 else np.nan
    volatility = float(returns.std(ddof=1) * np.sqrt(periods_per_year)) if n > 1 else np.nan
    std = returns.std(ddof=1)
    sharpe = float(returns.mean() / std * np.sqrt(periods_per_year)) if n > 1 and std > 0 else np.nan
    return {
        "total_return": total,
        "CAGR": cagr,
        "annualised_volatility": volatility,
        "Sharpe_ratio_rf_0": sharpe,
        "maximum_drawdown": max_drawdown(equity),
        "one_way_turnover_cumulative": float(turnover.sum()),
        "one_way_turnover_annualised": float(turnover.mean() * periods_per_year) if len(turnover) else np.nan,
        "transaction_cost_cumulative_return_drag": float(costs.sum()),
        "observations": n,
    }
