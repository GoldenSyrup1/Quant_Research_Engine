"""Download auto-adjusted Yahoo Finance history for research inputs."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

try:
    from .data_audit import sha256_file
except ImportError:  # pragma: no cover - command-line use
    from data_audit import sha256_file

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def filename(ticker):
    return ticker.replace(".", "_") + ".csv"


def _record_provenance(ticker, start, path, frame):
    """Update a local manifest; it documents retrieval and never alters prices."""
    manifest_path = DATA / "provenance.json"
    manifest = {"downloads": []}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    close = frame["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    record = {
        "ticker": ticker,
        "source": "Yahoo Finance via yfinance",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "download_parameters": {"start": start, "auto_adjust": True, "actions": False},
        "data_range": {"start": close.index.min().date().isoformat(), "end": close.index.max().date().isoformat()},
        "observations": int(len(close)),
        "file": path.name,
        "checksum_sha256": sha256_file(path),
        "adjustments_and_limitations": (
            "Yahoo Finance auto_adjust=True adjusted Close; provider data can change and does not remove "
            "survivorship, delisting, ticker-history, or data-quality limitations."
        ),
    }
    manifest["downloads"] = [item for item in manifest.get("downloads", []) if item["ticker"] != ticker]
    manifest["downloads"].append(record)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    path = DATA / filename(ticker)
    frame.to_csv(path)
    _record_provenance(ticker, start, path, frame)
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
