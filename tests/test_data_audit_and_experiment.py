import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.data_audit import audit_data_directory, audit_price_file, data_references, sha256_file
from src.experiment import ExperimentConfig, load_config, run_experiment


def write_price_csv(path: Path, prices: pd.Series):
    columns = pd.MultiIndex.from_tuples([("Close", path.stem.replace("_", "."))])
    pd.DataFrame(prices.to_numpy(), index=prices.index, columns=columns).to_csv(path)


def prices(rows=250, rate=0.0005):
    index = pd.bdate_range("2019-01-02", periods=rows)
    return pd.Series(100 * (1 + rate) ** np.arange(rows), index=index)


class DataAuditTests(unittest.TestCase):
    def test_audit_reports_file_integrity_provenance_fields_and_anomalies(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "AAA_AX.csv"
            series = prices(160)
            series.iloc[10] = np.nan
            series.iloc[30] = series.iloc[29] * 1.5
            write_price_csv(path, series)
            report = audit_price_file(path, required_observations=200, extreme_return_threshold=0.2)
            self.assertEqual(report["file_checksum_sha256"], sha256_file(path))
            self.assertTrue(report["file_integrity"]["readable"])
            self.assertEqual(report["observations"], 160)
            self.assertEqual(report["missing_values"], 1)
            self.assertTrue(report["insufficient_history"])
            self.assertEqual(len(report["extreme_daily_returns"]), 2)
            self.assertEqual(report["status"], "warning")

    def test_audit_reports_missing_file_as_an_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = audit_price_file(Path(temporary) / "MISSING_AX.csv")
            self.assertEqual(report["status"], "error")
            self.assertFalse(report["file_integrity"]["readable"])

    def test_directory_audit_marks_benchmark_and_produces_references(self):
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            write_price_csv(data_dir / "AAA_AX.csv", prices())
            write_price_csv(data_dir / "STW_AX.csv", prices(rate=0.0002))
            audit = audit_data_directory(data_dir, universe=["AAA.AX"], benchmark="STW.AX")
            self.assertTrue(audit["benchmark_coverage"]["available"])
            refs = data_references(audit)
            self.assertEqual({item["role"] for item in refs}, {"universe", "benchmark"})
            self.assertTrue(all(item["checksum_sha256"] for item in refs))


class ExperimentTests(unittest.TestCase):
    def _make_data(self, root: Path):
        data_dir = root / "data"
        data_dir.mkdir()
        tickers = ["S0.AX", "S1.AX", "S2.AX", "S3.AX", "S4.AX"]
        for index, ticker in enumerate(tickers):
            write_price_csv(data_dir / f"{ticker.replace('.', '_')}.csv", prices(rate=0.0002 + index * 0.0001))
        write_price_csv(data_dir / "STW_AX.csv", prices(rate=0.00015))
        return tickers

    def test_experiment_writes_immutable_reproducible_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tickers = self._make_data(root)
            config = ExperimentConfig(experiment_id="offline-baseline", universe=tickers)
            output = run_experiment(config, root=root)
            expected = {
                "configuration.json", "data_audit.json", "equity_curves.csv", "daily_returns.csv",
                "weights.csv", "holdings.csv", "turnover.csv", "transaction_costs.csv", "metrics.csv",
                "train_test_metrics.csv", "benchmark_comparison.csv", "benchmark_metrics.csv",
                "benchmark_status.txt",
            }
            self.assertTrue(expected.issubset({path.name for path in output.iterdir()}))
            recorded = json.loads((output / "configuration.json").read_text(encoding="utf-8"))
            self.assertEqual(recorded["momentum_lookback_sessions"], 126)
            self.assertEqual(len(recorded["data_references"]), 6)
            self.assertEqual(recorded["data_references"][0]["checksum_sha256"].__len__(), 64)
            with self.assertRaises(FileExistsError):
                run_experiment(config, root=root)

    def test_reproduction_rejects_changed_input_checksum(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tickers = self._make_data(root)
            first = run_experiment(ExperimentConfig(experiment_id="source", universe=tickers), root=root)
            series = prices(rate=0.009)
            write_price_csv(root / "data" / "S0_AX.csv", series)
            with self.assertRaisesRegex(ValueError, "Data checksum mismatch"):
                run_experiment(load_config(first / "configuration.json", "reproduction"), root=root)

    def test_strategy_parameter_changes_are_rejected(self):
        config = ExperimentConfig(experiment_id="bad-parameter", universe=["S0.AX"])
        config.momentum_lookback_sessions = 100
        with self.assertRaisesRegex(ValueError, "momentum_lookback_sessions"):
            config.validate_strategy()


if __name__ == "__main__":
    unittest.main()
