"""Create immutable, reproducible outputs around the validated momentum backtest."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

try:
    from .backtest_momentum import (
        BENCHMARK, COST_BPS, LOOKBACK, N_HOLD, SKIP, build_backtest,
        out_of_sample_metrics, read_adjusted_close,
    )
    from .data_audit import audit_data_directory, data_references, write_json
except ImportError:  # pragma: no cover - command-line use
    from backtest_momentum import (
        BENCHMARK, COST_BPS, LOOKBACK, N_HOLD, SKIP, build_backtest,
        out_of_sample_metrics, read_adjusted_close,
    )
    from data_audit import audit_data_directory, data_references, write_json

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EXPERIMENTS = ROOT / "experiments"
EXECUTION = "signal at month-end close; target executes next session close; target earns following close-to-close return"


@dataclass
class ExperimentConfig:
    experiment_id: str
    strategy_name: str = "asx_monthly_momentum"
    universe: list[str] = field(default_factory=list)
    momentum_lookback_sessions: int = LOOKBACK
    skip_recent_sessions: int = SKIP
    number_of_holdings: int = N_HOLD
    weighting_method: str = "equal_weight"
    rebalancing_schedule: str = "monthly_last_observed_trading_session"
    execution_convention: str = EXECUTION
    transaction_cost_bps_per_one_way_turnover: int = COST_BPS
    benchmark: str = BENCHMARK
    train_test_split: float = 0.7
    data_directory: str = "data"
    data_references: list[dict] = field(default_factory=list)
    provenance_references: list[dict] = field(default_factory=list)

    def validate_strategy(self) -> None:
        expected = {
            "momentum_lookback_sessions": LOOKBACK,
            "skip_recent_sessions": SKIP,
            "number_of_holdings": N_HOLD,
            "weighting_method": "equal_weight",
            "rebalancing_schedule": "monthly_last_observed_trading_session",
            "execution_convention": EXECUTION,
            "transaction_cost_bps_per_one_way_turnover": COST_BPS,
        }
        for key, value in expected.items():
            if getattr(self, key) != value:
                raise ValueError(f"{key} must remain {value!r} for this validated strategy implementation")
        if not self.universe:
            raise ValueError("Experiment universe cannot be empty")
        if not 0 < self.train_test_split < 1:
            raise ValueError("train_test_split must be between 0 and 1")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", self.experiment_id):
            raise ValueError("experiment_id may contain letters, numbers, underscores, and hyphens")


def load_config(path: Path, experiment_id: str | None = None) -> ExperimentConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if experiment_id is not None:
        raw["experiment_id"] = experiment_id
    accepted = {item.name for item in fields(ExperimentConfig)}
    return ExperimentConfig(**{key: value for key, value in raw.items() if key in accepted})


def default_config(experiment_id: str, universe: list[str], benchmark: str = BENCHMARK) -> ExperimentConfig:
    return ExperimentConfig(experiment_id=experiment_id, universe=universe, benchmark=benchmark)


def _provenance(data_dir: Path) -> list[dict]:
    path = data_dir / "provenance.json"
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw.get("downloads", [])
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid provenance file {path}: {exc}") from exc


def _load_configured_prices(data_dir: Path, universe: list[str], benchmark: str):
    series = {}
    for ticker in universe:
        path = data_dir / f"{ticker.replace('.', '_')}.csv"
        series[ticker] = read_adjusted_close(path)
    prices = pd.DataFrame(series).sort_index()
    benchmark_series = read_adjusted_close(data_dir / f"{benchmark.replace('.', '_')}.csv")
    return prices, benchmark_series


def _verify_references(expected: list[dict], actual: list[dict]) -> None:
    if not expected:
        return
    expected_checksums = {item["ticker"]: item.get("checksum_sha256") for item in expected}
    actual_checksums = {item["ticker"]: item.get("checksum_sha256") for item in actual}
    mismatch = [ticker for ticker, checksum in expected_checksums.items() if actual_checksums.get(ticker) != checksum]
    if mismatch:
        raise ValueError(
            "Data checksum mismatch for " + ", ".join(mismatch) +
            ". The configured experiment cannot be reproduced from the current files."
        )


def run_experiment(config: ExperimentConfig, *, root: Path = ROOT) -> Path:
    """Audit inputs, run one backtest, and write a new immutable experiment directory."""
    config.validate_strategy()
    data_dir = (root / config.data_directory).resolve()
    audit = audit_data_directory(data_dir, universe=config.universe, benchmark=config.benchmark)
    references = data_references(audit)
    _verify_references(config.data_references, references)
    failures = [item["ticker"] for item in audit["files"] if item["status"] == "error"]
    if failures:
        raise ValueError("Data audit failed for: " + ", ".join(failures))
    output_dir = root / "experiments" / config.experiment_id
    if output_dir.exists():
        raise FileExistsError(f"Experiment output already exists: {output_dir}. Choose a new experiment ID.")
    output_dir.mkdir(parents=True)
    recorded = asdict(config)
    recorded["data_references"] = references
    recorded["provenance_references"] = _provenance(data_dir)
    recorded["created_at_utc"] = datetime.now(timezone.utc).isoformat()
    write_json(output_dir / "configuration.json", recorded)
    write_json(output_dir / "data_audit.json", audit)
    prices, benchmark = _load_configured_prices(data_dir, config.universe, config.benchmark)
    result = build_backtest(prices, benchmark)
    pd.DataFrame({"gross_equity": result.gross_equity, "net_equity": result.net_equity}).to_csv(
        output_dir / "equity_curves.csv", index_label="date"
    )
    pd.DataFrame({"gross_return": result.gross_returns, "net_return": result.net_returns}).to_csv(
        output_dir / "daily_returns.csv", index_label="date"
    )
    result.weights.to_csv(output_dir / "weights.csv", index_label="date")
    result.weights.gt(0.0).astype(int).to_csv(output_dir / "holdings.csv", index_label="date")
    pd.DataFrame({"one_way_turnover": result.one_way_turnover}).to_csv(
        output_dir / "turnover.csv", index_label="date"
    )
    pd.DataFrame({"transaction_cost_return": result.transaction_costs}).to_csv(
        output_dir / "transaction_costs.csv", index_label="date"
    )
    pd.DataFrame({"gross": result.gross_metrics, "net": result.net_metrics}).to_csv(output_dir / "metrics.csv")
    out_of_sample_metrics(result, config.train_test_split).to_csv(output_dir / "train_test_metrics.csv", index=False)
    comparison = result.benchmark_comparison
    if comparison is None:
        comparison = pd.DataFrame(columns=["strategy_net_return", "benchmark_return", "strategy_net_equity", "benchmark_equity"])
    comparison.to_csv(output_dir / "benchmark_comparison.csv", index_label="date")
    if result.benchmark_metrics is not None:
        pd.Series(result.benchmark_metrics, name="value").to_csv(output_dir / "benchmark_metrics.csv")
    (output_dir / "benchmark_status.txt").write_text(result.benchmark_status + "\n", encoding="utf-8")
    return output_dir


def main():
    parser = argparse.ArgumentParser(description="Run one reproducible momentum research experiment")
    parser.add_argument("--experiment-id", help="New, unique ID for this output directory")
    parser.add_argument("--config", type=Path, help="Prior configuration.json or user-authored config JSON")
    parser.add_argument("--tickers", nargs="+", help="Universe tickers when not using --config")
    parser.add_argument("--benchmark", default=BENCHMARK)
    args = parser.parse_args()
    if args.config:
        if not args.experiment_id:
            parser.error("--experiment-id is required with --config so prior outputs are never overwritten")
        config = load_config(args.config, args.experiment_id)
    else:
        if not args.experiment_id or not args.tickers:
            parser.error("--experiment-id and --tickers are required without --config")
        config = default_config(args.experiment_id, args.tickers, args.benchmark)
    output = run_experiment(config)
    print(f"Experiment complete: {output}")


if __name__ == "__main__":
    main()
