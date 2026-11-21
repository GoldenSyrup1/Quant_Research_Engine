"""Close-based monthly momentum backtest; no live-trading functionality."""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

try:  # Support both ``python src/backtest_momentum.py`` and package imports.
    from .metrics import performance_metrics
except ImportError:  # pragma: no cover - exercised by the command-line entry point
    from metrics import performance_metrics

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
LOOKBACK = 126
SKIP = 21
N_HOLD = 5
COST_BPS = 10
BENCHMARK = "STW.AX"


@dataclass
class BacktestResult:
    weights: pd.DataFrame
    gross_returns: pd.Series
    net_returns: pd.Series
    gross_equity: pd.Series
    net_equity: pd.Series
    one_way_turnover: pd.Series
    transaction_costs: pd.Series
    gross_metrics: dict
    net_metrics: dict
    benchmark_comparison: pd.DataFrame | None
    benchmark_metrics: dict | None
    benchmark_status: str


def calculate_momentum_signal(prices: pd.DataFrame, lookback=LOOKBACK, skip=SKIP) -> pd.DataFrame:
    """Compute return over `lookback` price intervals ending `skip` sessions ago.

    Every close in the 127-point measurement window must be valid: 126 intervals
    require 127 observed prices. No values are interpolated or carried forward.
    """
    if lookback < 1 or skip < 0:
        raise ValueError("lookback must be positive and skip cannot be negative")
    clean = prices.apply(pd.to_numeric, errors="coerce").astype(float)
    clean = clean.where(np.isfinite(clean) & (clean > 0))
    complete = clean.notna().rolling(lookback + 1, min_periods=lookback + 1).sum().shift(skip)
    signal = clean.shift(skip).div(clean.shift(lookback + skip)).sub(1.0)
    return signal.where(complete.eq(lookback + 1))


def month_end_dates(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Return the last observed date in each calendar month."""
    if index.has_duplicates:
        raise ValueError("Date index must be unique")
    ordered = index.sort_values()
    return pd.DatetimeIndex(pd.Series(ordered, index=ordered).groupby(ordered.to_period("M")).last().to_numpy())


def cash_inclusive_turnover(old_weights: pd.Series, new_weights: pd.Series) -> float:
    """One-way turnover including residual cash as a portfolio asset.

    Weights are fractions of NAV. Cash weight is 1 minus risky weights. The
    one-way traded fraction is half the L1 change across risky assets and cash.
    """
    tickers = old_weights.index.union(new_weights.index)
    old = pd.to_numeric(old_weights.reindex(tickers, fill_value=0.0), errors="coerce").fillna(0.0)
    new = pd.to_numeric(new_weights.reindex(tickers, fill_value=0.0), errors="coerce").fillna(0.0)
    if (old < -1e-12).any() or (new < -1e-12).any():
        raise ValueError("Long-only turnover weights cannot be negative")
    if old.sum() > 1 + 1e-9 or new.sum() > 1 + 1e-9:
        raise ValueError("Risky weights cannot exceed 100% of NAV")
    old_all = np.append(old.to_numpy(), max(0.0, 1.0 - old.sum()))
    new_all = np.append(new.to_numpy(), max(0.0, 1.0 - new.sum()))
    return float(np.abs(new_all - old_all).sum() / 2.0)


def chronological_split(series: pd.Series, train_fraction=0.7):
    """Split in time order; callers must set parameters before evaluating test."""
    if not 0.0 < train_fraction < 1.0:
        raise ValueError("train_fraction must be strictly between 0 and 1")
    split_at = int(len(series) * train_fraction)
    if split_at < 1 or split_at >= len(series):
        raise ValueError("At least two observations are required for a train/test split")
    return series.iloc[:split_at], series.iloc[split_at:]


def read_adjusted_close(path: Path) -> pd.Series:
    """Read Close from yfinance auto_adjust=True output, supporting CSV layouts."""
    frame = pd.read_csv(path, header=[0, 1], index_col=0, parse_dates=True)
    if isinstance(frame.columns, pd.MultiIndex):
        fields = frame.columns.get_level_values(0)
        if "Close" not in fields:
            raise ValueError(f"{path.name}: adjusted Close column not found")
        close = frame.xs("Close", axis=1, level=0)
        if isinstance(close, pd.DataFrame):
            if close.shape[1] != 1:
                raise ValueError(f"{path.name}: expected one ticker, found multiple")
            close = close.iloc[:, 0]
    else:
        frame = pd.read_csv(path, index_col=0, parse_dates=True)
        if "Close" not in frame:
            raise ValueError(f"{path.name}: adjusted Close column not found")
        close = frame["Close"]
    close = pd.to_numeric(close, errors="coerce")
    close.index = pd.to_datetime(close.index, errors="coerce")
    if close.index.isna().any():
        raise ValueError(f"{path.name}: invalid dates")
    if close.index.has_duplicates:
        raise ValueError(f"{path.name}: duplicate dates")
    close = close.sort_index().astype(float)
    if np.isinf(close.dropna()).any() or (close.dropna() <= 0).any():
        raise ValueError(f"{path.name}: prices must be finite and positive")
    return close


def load_prices(directory: Path, exclude: str | None = None) -> pd.DataFrame:
    series = {}
    for path in sorted(directory.glob("*.csv")):
        if exclude and path.name.lower() == exclude.lower():
            continue
        try:
            series[path.stem.replace("_AX", "").replace("_", ".")] = read_adjusted_close(path)
        except ValueError as exc:
            raise ValueError(f"Invalid price file {path.name}: {exc}") from exc
    if not series:
        raise ValueError(f"No valid price files found in {directory}")
    prices = pd.concat(series, axis=1).sort_index()
    prices.columns.name = "ticker"
    return prices


def _comparison(strategy_returns: pd.Series, benchmark_prices: pd.Series):
    benchmark_prices = pd.to_numeric(benchmark_prices, errors="coerce").astype(float)
    if benchmark_prices.index.has_duplicates:
        raise ValueError("Benchmark has duplicate dates")
    benchmark_prices = benchmark_prices.sort_index().where(
        np.isfinite(benchmark_prices) & (benchmark_prices > 0)
    )
    # Reindex closes before pct_change. A missing common-session close then makes
    # both affected daily returns missing instead of creating a multi-day return.
    aligned_closes = benchmark_prices.reindex(strategy_returns.index)
    benchmark_returns = aligned_closes.pct_change(fill_method=None)
    comparison = pd.concat(
        [strategy_returns.rename("strategy_net_return"), benchmark_returns.rename("benchmark_return")],
        axis=1,
    ).dropna()
    if comparison.empty:
        return comparison, None, "No overlapping valid daily returns for strategy and STW.AX."
    comparison["strategy_net_equity"] = (1.0 + comparison["strategy_net_return"]).cumprod()
    comparison["benchmark_equity"] = (1.0 + comparison["benchmark_return"]).cumprod()
    count = len(comparison)
    benchmark_metrics = {
        "comparison_start": comparison.index[0].date().isoformat(),
        "comparison_end": comparison.index[-1].date().isoformat(),
        "observations": count,
    }
    for name, column in (("strategy", "strategy_net_return"), ("benchmark", "benchmark_return")):
        returns = comparison[column]
        curve = (1.0 + returns).cumprod()
        benchmark_metrics.update(
            {f"{name}_{key}": value for key, value in performance_metrics(
                returns, curve, pd.Series(0.0, index=returns.index), pd.Series(0.0, index=returns.index)
            ).items()}
        )
    status = (
        f"Common-date comparison: {benchmark_metrics['comparison_start']} to "
        f"{benchmark_metrics['comparison_end']} inclusive; {count} daily return observations."
    )
    return comparison, benchmark_metrics, status


def build_backtest(prices: pd.DataFrame, benchmark: pd.Series | None = None) -> BacktestResult:
    if prices.empty or prices.columns.has_duplicates or prices.index.has_duplicates:
        raise ValueError("Prices must be non-empty with unique dates and tickers")
    prices = prices.sort_index().apply(pd.to_numeric, errors="coerce").astype(float)
    prices = prices.where(np.isfinite(prices) & (prices > 0))
    returns = prices.pct_change(fill_method=None)
    signal = calculate_momentum_signal(prices)
    weights = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    targets = {}
    for decision_date in month_end_dates(prices.index):
        scores = signal.loc[decision_date].dropna().sort_values(ascending=False, kind="stable")
        eligible = scores.index[prices.loc[decision_date, scores.index].notna()]
        selected = eligible[:N_HOLD]
        target = pd.Series(0.0, index=prices.columns)
        if len(selected):
            target.loc[selected] = 1.0 / len(selected)
        following = prices.index[prices.index > decision_date]
        if len(following):
            targets[following[0]] = target

    # Actual weights drift with returns between execution closes. This avoids
    # accidentally modeling a daily rebalance while charging turnover monthly.
    gross_returns = pd.Series(0.0, index=prices.index, name="gross_return")
    one_way_turnover = pd.Series(0.0, index=prices.index)
    transaction_costs = pd.Series(0.0, index=prices.index, name="transaction_cost_return")
    net_returns = pd.Series(0.0, index=prices.index, name="net_return")
    current = pd.Series(0.0, index=prices.columns)
    for date in prices.index:
        day_returns = returns.loc[date]
        missing = current.ne(0) & day_returns.isna()
        if missing.any():
            ticker = missing.index[missing][0]
            raise ValueError(
                f"Missing return for held asset {ticker} on {date.date()}; "
                "resolve data gap before relying on results"
            )
        asset_returns = day_returns.fillna(0.0)
        gross = float(current.dot(asset_returns))
        gross_returns.loc[date] = gross
        growth = 1.0 + gross
        drifted = current * (1.0 + asset_returns) / growth
        if date in targets:
            target = targets[date]
            one_way_turnover.loc[date] = cash_inclusive_turnover(drifted, target)
            cost_fraction = one_way_turnover.loc[date] * COST_BPS / 10000.0
            # Turnover is measured against post-return NAV at this close, so
            # translate that execution cost back to the session's starting NAV.
            transaction_costs.loc[date] = growth * cost_fraction
            current = target.copy()
        else:
            current = drifted
        weights.loc[date] = current
        net_returns.loc[date] = gross - transaction_costs.loc[date]

    net_returns = net_returns.rename("net_return")
    transaction_costs = transaction_costs.rename("transaction_cost_return")
    gross_returns = gross_returns.rename("gross_return")
    gross_equity = (1.0 + gross_returns).cumprod().rename("gross_equity")
    net_equity = (1.0 + net_returns).cumprod().rename("net_equity")
    gross_metrics = performance_metrics(
        gross_returns, gross_equity, one_way_turnover, pd.Series(0.0, index=prices.index)
    )
    net_metrics = performance_metrics(net_returns, net_equity, one_way_turnover, transaction_costs)
    for metrics in (gross_metrics, net_metrics):
        metrics["transaction_cost_bps_per_one_way_turnover"] = COST_BPS

    comparison = benchmark_metrics = None
    if benchmark is None:
        benchmark_status = f"Benchmark unavailable: {BENCHMARK} data file not found or no series supplied."
    else:
        comparison, benchmark_metrics, benchmark_status = _comparison(net_returns, benchmark)
    return BacktestResult(
        weights, gross_returns, net_returns, gross_equity, net_equity,
        one_way_turnover, transaction_costs, gross_metrics, net_metrics,
        comparison, benchmark_metrics, benchmark_status,
    )


def out_of_sample_metrics(result: BacktestResult, train_fraction=0.7):
    """Summarize fixed strategy results in chronological train and held-out test periods."""
    gross_train, gross_test = chronological_split(result.gross_returns, train_fraction)
    net_train, net_test = chronological_split(result.net_returns, train_fraction)
    turnover_train, turnover_test = chronological_split(result.one_way_turnover, train_fraction)
    cost_train, cost_test = chronological_split(result.transaction_costs, train_fraction)
    rows = []
    for label, gross, net, turnover, costs in (
        ("train", gross_train, net_train, turnover_train, cost_train),
        ("test", gross_test, net_test, turnover_test, cost_test),
    ):
        for gross_net, returns, cost_series in (
            ("gross", gross, pd.Series(0.0, index=gross.index)),
            ("net", net, costs),
        ):
            equity = (1.0 + returns).cumprod()
            values = performance_metrics(returns, equity, turnover, cost_series)
            rows.append({
                "period": label,
                "return_type": gross_net,
                "start": returns.index[0].date().isoformat(),
                "end": returns.index[-1].date().isoformat(),
                **values,
            })
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(exist_ok=True)
    if not DATA.exists():
        raise SystemExit(f"Price directory not found: {DATA}. Run download_data.py first.")
    benchmark_path = DATA / f"{BENCHMARK.replace('.', '_')}.csv"
    prices = load_prices(DATA, exclude=benchmark_path.name)
    if len(prices.columns) < N_HOLD:
        raise SystemExit(f"Need at least {N_HOLD} stock files; found {len(prices.columns)}")
    benchmark = read_adjusted_close(benchmark_path) if benchmark_path.exists() else None
    result = build_backtest(prices, benchmark)
    pd.DataFrame({
        "gross_equity": result.gross_equity,
        "net_equity": result.net_equity,
    }).to_csv(OUT / "equity_curve.csv", index_label="date")
    pd.DataFrame({
        "gross_return": result.gross_returns,
        "net_return": result.net_returns,
    }).to_csv(OUT / "daily_returns.csv", index_label="date")
    result.weights.to_csv(OUT / "weights.csv", index_label="date")
    pd.DataFrame({
        "one_way_turnover": result.one_way_turnover,
        "cost_bps_per_turnover": COST_BPS,
        "transaction_cost_return": result.transaction_costs,
        "gross_return": result.gross_returns,
        "net_return": result.net_returns,
    }).to_csv(OUT / "transaction_cost_attribution.csv", index_label="date")
    pd.DataFrame({"gross": result.gross_metrics, "net": result.net_metrics}).to_csv(OUT / "metrics.csv")
    oos = out_of_sample_metrics(result)
    oos.to_csv(OUT / "out_of_sample_metrics.csv", index=False)
    if result.benchmark_comparison is not None:
        result.benchmark_comparison.to_csv(OUT / "benchmark_comparison.csv", index_label="date")
    if result.benchmark_metrics is not None:
        pd.Series(result.benchmark_metrics, name="value").to_csv(OUT / "benchmark_metrics.csv")
    (OUT / "benchmark_status.txt").write_text(result.benchmark_status + "\n", encoding="utf-8")
    print("Gross metrics:\n" + pd.Series(result.gross_metrics).to_string())
    print("\nNet metrics:\n" + pd.Series(result.net_metrics).to_string())
    print("\n" + result.benchmark_status)
    print("Out-of-sample split: chronological 70/30; keep all parameter choices fixed before evaluating test metrics.")


if __name__ == "__main__":
    main()
