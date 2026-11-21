"""Download auto-adjusted Yahoo Finance history for research inputs."""
import argparse
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def filename(ticker):
    return ticker.replace(".", "_") + ".csv"


def download(ticker, start):
    print(f"Downloading {ticker}")
    frame = yf.download(ticker, start=start, auto_adjust=True, progress=False, actions=False)
    if frame.empty:
        print(f"No data returned for {ticker}; no file written")
        return False
    if frame.index.has_duplicates:
        raise ValueError(f"Yahoo Finance returned duplicate dates for {ticker}")
    fields = frame.columns.get_level_values(0) if isinstance(frame.columns, pd.MultiIndex) else frame.columns
    if "Close" not in fields:
        raise ValueError(f"Yahoo Finance returned no Close field for {ticker}")
    frame.to_csv(DATA / filename(ticker))
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", nargs="+", required=True, help="ASX stock tickers, e.g. BHP.AX CBA.AX")
    parser.add_argument("--benchmark", default="STW.AX", help="Broad ASX benchmark ETF ticker (default: STW.AX)")
    parser.add_argument("--start", default="2015-01-01")
    args = parser.parse_args()
    DATA.mkdir(exist_ok=True)
    stock_successes = sum(download(ticker, args.start) for ticker in args.tickers)
    benchmark_success = download(args.benchmark, args.start)
    print(f"Downloaded {stock_successes}/{len(args.tickers)} stock series.")
    if not benchmark_success:
        print(f"Benchmark {args.benchmark} could not be retrieved. Backtest will report benchmark unavailable.")
    print("Inputs use Yahoo Finance auto-adjusted Close. Review data quality and survivorship limitations before interpreting results.")


if __name__ == "__main__":
    main()
