"""Regenerate MOM-001 robustness tables without changing the immutable experiment."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.robustness import (  # noqa: E402
    cost_sensitivity, drawdown_duration, exposure_statistics, fixed_calendar_periods,
    leave_one_out, load_prices, metrics_for_returns, moving_block_bootstrap, tail_day_sensitivity,
)

EXPERIMENT_ID = "MOM-001"
REQUIRED_FILES = ("configuration.json", "daily_returns.csv", "turnover.csv", "weights.csv", "benchmark_comparison.csv")


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(frame: pd.DataFrame | pd.Series, path: Path) -> None:
    if isinstance(frame, pd.Series):
        frame = frame.to_frame()
    frame.to_csv(path, float_format="%.17g", index_label=frame.index.name or "index")


def load_inputs(root: Path, experiment_id: str):
    experiment = root / "experiments" / experiment_id
    missing = [name for name in REQUIRED_FILES if not (experiment / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing required experiment files: {', '.join(missing)}")
    config = json.loads((experiment / "configuration.json").read_text(encoding="utf-8"))
    if config.get("experiment_id") != experiment_id:
        raise ValueError("Configuration experiment_id does not match requested experiment")
    references = config.get("data_references", [])
    if not references:
        raise ValueError("Configuration has no recorded data references")
    data_dir = root / config.get("data_directory", "data")
    for ref in references:
        path = data_dir / ref["file"]
        if not path.is_file():
            raise FileNotFoundError(f"Missing recorded input: {path}")
        if checksum(path) != ref.get("checksum_sha256"):
            raise ValueError(f"Checksum mismatch for recorded input {ref['ticker']}")
    daily = pd.read_csv(experiment / "daily_returns.csv", index_col="date", parse_dates=True)
    turnover = pd.read_csv(experiment / "turnover.csv", index_col="date", parse_dates=True).iloc[:, 0]
    weights = pd.read_csv(experiment / "weights.csv", index_col="date", parse_dates=True)
    comparison = pd.read_csv(experiment / "benchmark_comparison.csv", index_col="date", parse_dates=True)
    if not daily.index.equals(turnover.index) or not daily.index.equals(weights.index):
        raise ValueError("Saved daily returns, turnover, and weights have inconsistent dates")
    if daily.isna().any().any() or turnover.isna().any() or weights.isna().any().any():
        raise ValueError("Saved MOM-001 inputs contain missing values")
    return experiment, data_dir, config, daily, turnover, weights, comparison


def generate(root: Path = ROOT, output: Path | None = None, experiment_id: str = EXPERIMENT_ID) -> Path:
    experiment, data_dir, config, daily, turnover, weights, comparison = load_inputs(root, experiment_id)
    output = output or root / "research" / "results" / "MOM-001-robustness"
    output.mkdir(parents=True, exist_ok=True)
    gross, net = daily["gross_return"], daily["net_return"]
    split = int(len(daily) * config["train_test_split"])

    write_csv(cost_sensitivity(gross, turnover, [10, 25, 50, 100]), output / "cost_sensitivity.csv")
    train = cost_sensitivity(gross.iloc[:split], turnover.iloc[:split], [10, 25, 50, 100]).add_prefix("train_")
    test = cost_sensitivity(gross.iloc[split:], turnover.iloc[split:], [10, 25, 50, 100]).add_prefix("test_")
    write_csv(train.join(test), output / "cost_sensitivity_train_test.csv")

    prices = load_prices(data_dir, config["universe"])
    benchmark = load_prices(data_dir, [config["benchmark"]]).iloc[:, 0]
    baseline = pd.DataFrame([{"excluded_ticker": "NONE", **metrics_for_returns(net)}]).set_index("excluded_ticker")
    write_csv(pd.concat([baseline, leave_one_out(prices, benchmark)]), output / "leave_one_out.csv")
    write_csv(fixed_calendar_periods(net), output / "fixed_calendar_periods.csv")

    duration = pd.DataFrame([drawdown_duration(net)])
    write_csv(duration, output / "drawdown_duration.csv")
    write_csv(net.nsmallest(10).rename("net_return"), output / "worst_daily_returns.csv")
    monthly = ((1.0 + net).resample("ME").prod() - 1.0).rename("net_return")
    write_csv(monthly.nsmallest(10), output / "worst_monthly_returns.csv")
    write_csv(pd.DataFrame([exposure_statistics(weights)]), output / "exposure_statistics.csv")
    tail_summary, tail_selected = tail_day_sensitivity(net)
    write_csv(tail_summary, output / "tail_day_sensitivity.csv")
    write_csv(tail_selected.set_index(["n", "rank"]), output / "tail_day_selected_dates.csv")

    bootstrap = moving_block_bootstrap(net, block_length=21, samples=2000, seed=20261123)
    bootstrap.index.name = "path"
    write_csv(bootstrap, output / "bootstrap_paths.csv")
    summary = bootstrap.quantile([0.025, 0.5, 0.975])
    summary.index.name = "quantile"
    write_csv(summary, output / "bootstrap_summary.csv")
    benchmark_metrics = pd.DataFrame({"strategy_net": metrics_for_returns(comparison["strategy_net_return"]), "benchmark": metrics_for_returns(comparison["benchmark_return"])}).T
    write_csv(benchmark_metrics, output / "benchmark_metrics_recalculated.csv")

    output_checksums = {path.name: checksum(path) for path in sorted(output.glob("*.csv"))}
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_experiment": str(experiment.relative_to(root)),
        "configuration_checksum_sha256": checksum(experiment / "configuration.json"),
        "input_data_references": config["data_references"],
        "source_output_checksums": {name: checksum(experiment / name) for name in REQUIRED_FILES},
        "calculation_settings": {"cost_bps": [10, 25, 50, 100], "calendar_periods": ["2015-2018", "2019-2022", "2023-2026_partial"], "bootstrap_block_length": 21, "bootstrap_samples": 2000, "bootstrap_seed": 20261123, "tail_n_values": [1, 5, 10]},
        "output_checksums": output_checksums,
        "software_versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="Directory for reproducible CSV results")
    args = parser.parse_args()
    print(generate(output=args.output))


if __name__ == "__main__":
    main()
