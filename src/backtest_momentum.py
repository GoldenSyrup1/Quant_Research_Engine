"""Close-based monthly momentum backtest. See README for timing and cost conventions."""
from pathlib import Path

import numpy as np
import pandas as pd
from metrics import performance_metrics

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
LOOKBACK = 126
SKIP = 21
N_HOLD = 5
COST_BPS = 10
BENCHMARK = "STW.AX"


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


def build_backtest(prices: pd.DataFrame, benchmark: pd.Series | None = None):
    if prices.empty or prices.columns.has_duplicates or prices.index.has_duplicates:
        raise ValueError("Prices must be non-empty with unique dates and tickers")
    prices = prices.sort_index().apply(pd.to_numeric, errors="coerce").astype(float)
    prices = prices.where(np.isfinite(prices) & (prices > 0))
    # A price cannot be carried forward: that creates stale valuations and false returns.
    returns = prices.pct_change(fill_method=None)
    signal = prices.shift(SKIP) / prices.shift(LOOKBACK + SKIP) - 1.0
    weights = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    targets = {}
    # Select the final actual trading date of each calendar month, not a synthetic month-end.
    month_ends = pd.Series(prices.index, index=prices.index).groupby(prices.index.to_period("M")).last()
    for decision_date in month_ends:
        scores = signal.loc[decision_date].dropna().sort_values(ascending=False, kind="stable")
        # Require a valid close on the decision date and a valid following close-to-close return.
        eligible = scores.index[prices.loc[decision_date, scores.index].notna()]
        selected = eligible[:N_HOLD]
        target = pd.Series(0.0, index=prices.columns)
        if len(selected):
            target.loc[selected] = 1.0 / len(selected)
        next_dates = prices.index[prices.index > decision_date]
        if len(next_dates):
            targets[next_dates[0]] = target

    current = pd.Series(0.0, index=prices.columns)
    for date in prices.index:
        if date in targets:
            current = targets[date]
        weights.loc[date] = current

    # Weight row t describes positions held at close t. Return on t is earned by
    # positions held at the prior close. A close signal is executed at next close,
    # so it first earns the subsequent close-to-close return.
    held = weights.shift(1).fillna(0.0)
    changes = weights.diff().fillna(weights.iloc[0])
    turnover_two_way = changes.abs().sum(axis=1)
    one_way_turnover = turnover_two_way / 2.0
    cost = one_way_turnover * (COST_BPS / 10000.0)
    active = held.ne(0)
    bad = active & returns.isna()
    if bad.to_numpy().any():
        date, ticker = np.argwhere(bad.to_numpy())[0]
        raise ValueError(f"Missing return for held asset {prices.columns[ticker]} on {prices.index[date].date()}; resolve data gap before relying on results")
    gross = (held * returns.fillna(0.0)).sum(axis=1)
    net = gross - cost
    equity = (1.0 + net).cumprod()
    metrics = performance_metrics(net, equity, one_way_turnover, cost)
    metrics["transaction_cost_bps_per_one_way_turnover"] = COST_BPS

    benchmark_curve = None
    benchmark_status = f"Benchmark unavailable: {BENCHMARK} data file not found or no series supplied."
    if benchmark is not None:
        benchmark = pd.to_numeric(benchmark, errors="coerce").astype(float).sort_index()
        if benchmark.index.has_duplicates:
            raise ValueError("Benchmark has duplicate dates")
        benchmark = benchmark.where(np.isfinite(benchmark) & (benchmark > 0)).reindex(prices.index)
        benchmark_returns = benchmark.pct_change(fill_method=None)
        # Align to dates with valid benchmark close-to-close observations; never fill gaps.
        benchmark_curve = (1.0 + benchmark_returns.fillna(0.0)).cumprod()
        benchmark_curve[benchmark_returns.isna()] = np.nan
        benchmark_status = f"Benchmark: {BENCHMARK} adjusted close, aligned by date; benchmark gaps remain missing."
    return weights, net, equity, benchmark_curve, metrics, benchmark_status


def main():
    OUT.mkdir(exist_ok=True)
    if not DATA.exists():
        raise SystemExit(f"Price directory not found: {DATA}. Run download_data.py first.")
    benchmark_path = DATA / f"{BENCHMARK.replace('.', '_')}.csv"
    prices = load_prices(DATA, exclude=benchmark_path.name)
    if len(prices.columns) < N_HOLD:
        raise SystemExit(f"Need at least {N_HOLD} stock files; found {len(prices.columns)}")
    benchmark = read_adjusted_close(benchmark_path) if benchmark_path.exists() else None
    weights, daily, equity, bench_curve, metrics, benchmark_status = build_backtest(prices, benchmark)
    curves = {"strategy_net": equity}
    if bench_curve is not None:
        curves[BENCHMARK.replace('.', '_') + "_buy_and_hold"] = bench_curve
    pd.DataFrame(curves).to_csv(OUT / "equity_curve.csv", index_label="date")
    pd.Series(metrics, name="value").to_csv(OUT / "metrics.csv")
    daily.rename("net_daily_return").to_csv(OUT / "daily_returns.csv", index_label="date")
    weights.to_csv(OUT / "weights.csv", index_label="date")
    (OUT / "benchmark_status.txt").write_text(benchmark_status + "\n", encoding="utf-8")
    print(pd.Series(metrics).to_string())
    print(benchmark_status)
    print("Execution: signal at month-end close; trade at next session close; resulting holdings earn returns from the following session.")


if __name__ == "__main__":
    main()
