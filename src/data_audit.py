"""Read-only data quality checks and provenance helpers for price inputs."""
from __future__ import annotations

import hashlib
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .backtest_momentum import read_adjusted_close
except ImportError:  # pragma: no cover - command-line use
    from backtest_momentum import read_adjusted_close

DEFAULT_EXTREME_RETURN = 0.20


def sha256_file(path: Path) -> str:
    """Return the SHA-256 checksum of a file without modifying it."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ticker_from_path(path: Path) -> str:
    return path.stem.replace("_AX", ".AX").replace("_", ".")


def _missing_weekdays(index: pd.DatetimeIndex) -> list[str]:
    if len(index) < 2:
        return []
    weekdays = pd.bdate_range(index.min(), index.max())
    return [date.date().isoformat() for date in weekdays.difference(index)]


def audit_price_file(
    path: Path,
    *,
    required_observations: int = 148,
    extreme_return_threshold: float = DEFAULT_EXTREME_RETURN,
) -> dict:
    """Audit one CSV. Suspicious observations are reported, never repaired."""
    report = {
        "file": path.name,
        "ticker": ticker_from_path(path),
        "exists": path.exists(),
        "file_checksum_sha256": sha256_file(path) if path.exists() else None,
        "file_integrity": {"readable": False, "close_column": False, "error": None},
        "start_date": None,
        "end_date": None,
        "observations": 0,
        "duplicate_dates": 0,
        "invalid_dates": 0,
        "date_index_sorted": True,
        "missing_values": 0,
        "invalid_or_non_positive_prices": 0,
        "missing_weekday_sessions": [],
        "missing_weekday_session_count": 0,
        "extreme_daily_returns": [],
        "insufficient_history": True,
        "status": "error",
    }
    if not path.exists():
        report["file_integrity"]["error"] = "File does not exist"
        return report
    try:
        raw = pd.read_csv(path, index_col=0, header=[0, 1])
        fields = raw.columns.get_level_values(0)
        if "Close" not in fields:
            raise ValueError("Adjusted Close column not found")
        close = raw.xs("Close", axis=1, level=0)
        if isinstance(close, pd.DataFrame):
            if close.shape[1] != 1:
                raise ValueError("Expected one ticker in the Close column")
            close = close.iloc[:, 0]
        dates = pd.to_datetime(close.index, errors="coerce")
        prices = pd.to_numeric(close, errors="coerce")
        report["file_integrity"].update({"readable": True, "close_column": True})
        report["invalid_dates"] = int(dates.isna().sum())
        valid_dates = pd.DatetimeIndex(dates[~dates.isna()])
        report["duplicate_dates"] = int(valid_dates.duplicated().sum())
        report["date_index_sorted"] = bool(valid_dates.is_monotonic_increasing)
        report["observations"] = int(len(prices))
        report["start_date"] = valid_dates.min().date().isoformat() if len(valid_dates) else None
        report["end_date"] = valid_dates.max().date().isoformat() if len(valid_dates) else None
        report["missing_values"] = int(prices.isna().sum())
        report["invalid_or_non_positive_prices"] = int((prices.dropna() <= 0).sum())
        valid_indexed_prices = pd.Series(prices.to_numpy(), index=dates).loc[lambda s: ~s.index.isna()]
        missing = _missing_weekdays(valid_indexed_prices.index.drop_duplicates().sort_values())
        report["missing_weekday_sessions"] = missing
        report["missing_weekday_session_count"] = len(missing)
        returns = valid_indexed_prices.sort_index().pct_change(fill_method=None)
        flagged = returns[returns.abs() > extreme_return_threshold].dropna()
        report["extreme_daily_returns"] = [
            {"date": date.date().isoformat(), "return": float(value)} for date, value in flagged.items()
        ]
        report["insufficient_history"] = len(prices) < required_observations
        report["status"] = "warning" if (
            report["missing_values"] or report["missing_weekday_session_count"]
            or report["extreme_daily_returns"] or report["insufficient_history"]
            or report["duplicate_dates"] or report["invalid_dates"]
            or report["invalid_or_non_positive_prices"] or not report["date_index_sorted"]
        ) else "ok"
        return report
    except Exception as exc:  # Audit should report bad input rather than hide it.
        report["file_integrity"]["error"] = str(exc)
        # A malformed index may still be diagnosable from the raw frame.
        return report


def audit_data_directory(
    data_dir: Path,
    *,
    universe: list[str],
    benchmark: str,
    required_observations: int = 148,
    extreme_return_threshold: float = DEFAULT_EXTREME_RETURN,
) -> dict:
    """Audit configured universe and benchmark files, not unrelated CSVs."""
    tickers = [*universe, benchmark]
    reports = []
    for ticker in tickers:
        path = data_dir / f"{ticker.replace('.', '_')}.csv"
        report = audit_price_file(
            path,
            required_observations=required_observations,
            extreme_return_threshold=extreme_return_threshold,
        )
        report["ticker"] = ticker
        report["role"] = "benchmark" if ticker == benchmark else "universe"
        reports.append(report)
    benchmark_report = next(item for item in reports if item["role"] == "benchmark")
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "required_observations": required_observations,
        "extreme_return_threshold": extreme_return_threshold,
        "data_directory": str(data_dir.resolve()),
        "files": reports,
        "benchmark_coverage": {
            "ticker": benchmark,
            "available": benchmark_report["status"] != "error",
            "start_date": benchmark_report["start_date"],
            "end_date": benchmark_report["end_date"],
            "observations": benchmark_report["observations"],
        },
    }


def data_references(audit_report: dict) -> list[dict]:
    """Extract stable file references for a reproducible experiment record."""
    return [
        {
            "ticker": item["ticker"],
            "role": item["role"],
            "file": item["file"],
            "checksum_sha256": item["file_checksum_sha256"],
            "start_date": item["start_date"],
            "end_date": item["end_date"],
            "observations": item["observations"],
        }
        for item in audit_report["files"]
    ]


def write_json(path: Path, content: dict) -> None:
    path.write_text(json.dumps(content, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Audit downloaded price data without changing it")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--tickers", nargs="+", required=True)
    parser.add_argument("--benchmark", default="STW.AX")
    parser.add_argument("--output", type=Path, default=Path("data") / "audit_report.json")
    args = parser.parse_args()
    report = audit_data_directory(args.data_dir, universe=args.tickers, benchmark=args.benchmark)
    write_json(args.output, report)
    statuses = ", ".join(f"{item['ticker']}: {item['status']}" for item in report["files"])
    print(f"Wrote {args.output}: {statuses}")


if __name__ == "__main__":
    main()

