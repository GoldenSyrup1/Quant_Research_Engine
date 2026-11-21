import unittest

import numpy as np
import pandas as pd

from src.backtest_momentum import (
    COST_BPS,
    LOOKBACK,
    SKIP,
    build_backtest,
    calculate_momentum_signal,
    cash_inclusive_turnover,
    chronological_split,
    month_end_dates,
)
from src.metrics import max_drawdown, performance_metrics


def synthetic_prices(rows=600):
    dates = pd.bdate_range("2018-01-02", periods=rows)
    rates = np.array([0.0001, 0.0002, 0.0003, 0.0004, 0.0005])
    values = 100 * (1 + rates[np.newaxis, :]) ** np.arange(rows)[:, np.newaxis]
    return pd.DataFrame(values, index=dates, columns=[f"S{i}" for i in range(5)])


class MomentumSignalTests(unittest.TestCase):
    def test_signal_uses_126_intervals_and_skips_latest_21_sessions(self):
        prices = synthetic_prices(220)[["S4"]]
        final = len(prices) - 1
        signal = calculate_momentum_signal(prices).iloc[final, 0]
        expected = prices.iloc[final - SKIP, 0] / prices.iloc[final - SKIP - LOOKBACK, 0] - 1
        self.assertAlmostEqual(signal, expected)

        modified = prices.copy()
        modified.iloc[-SKIP:, 0] *= np.linspace(2, 4, SKIP)
        modified_signal = calculate_momentum_signal(modified).iloc[final, 0]
        self.assertAlmostEqual(modified_signal, signal)

    def test_a_missing_price_inside_measurement_window_invalidates_signal(self):
        prices = synthetic_prices(220)[["S4"]]
        final = len(prices) - 1
        prices.iloc[final - 100, 0] = np.nan
        self.assertTrue(np.isnan(calculate_momentum_signal(prices).iloc[final, 0]))


class ScheduleAndExecutionTests(unittest.TestCase):
    def test_monthly_rebalance_dates_are_last_observed_dates(self):
        dates = pd.bdate_range("2023-01-01", "2023-04-30")
        observed = dates.delete([12, 42])
        month_ends = month_end_dates(observed)
        expected = pd.DatetimeIndex([observed[observed.to_period("M") == month].max()
                                     for month in observed.to_period("M").unique()])
        pd.testing.assert_index_equal(month_ends, expected)

    def test_execution_is_next_session_close_and_weights_persist(self):
        prices = synthetic_prices()
        result = build_backtest(prices)
        first_invested = result.weights.index[result.weights.sum(axis=1) > 0][0]
        previous = result.weights.index[result.weights.index.get_loc(first_invested) - 1]
        self.assertEqual(result.weights.loc[previous].sum(), 0.0)
        self.assertGreater(result.weights.loc[first_invested].sum(), 0.0)
        later = result.weights.index[result.weights.index.get_loc(first_invested) + 1]
        self.assertEqual(result.one_way_turnover.loc[later], 0.0)
        self.assertEqual(result.gross_returns.loc[first_invested], 0.0)
        asset_returns = prices.pct_change(fill_method=None).loc[later]
        prior_weights = result.weights.loc[first_invested]
        expected_next_return = float((prior_weights * asset_returns).sum())
        self.assertAlmostEqual(result.gross_returns.loc[later], expected_next_return)
        expected_drift = prior_weights * (1 + asset_returns) / (1 + expected_next_return)
        pd.testing.assert_series_equal(result.weights.loc[later], expected_drift, check_names=False)


class TurnoverAndCostTests(unittest.TestCase):
    def test_cash_inclusive_turnover_edge_cases(self):
        cash = pd.Series(dtype=float)
        fully_invested_a = pd.Series({"A": 1.0})
        fully_invested_b = pd.Series({"B": 1.0})
        split_a = pd.Series({"A": 0.5, "B": 0.5})
        split_b = pd.Series({"A": 0.5, "C": 0.5})
        self.assertEqual(cash_inclusive_turnover(cash, fully_invested_a), 1.0)
        self.assertEqual(cash_inclusive_turnover(fully_invested_a, fully_invested_b), 1.0)
        self.assertEqual(cash_inclusive_turnover(split_a, split_a), 0.0)
        self.assertEqual(cash_inclusive_turnover(split_a, split_b), 0.5)
        self.assertEqual(cash_inclusive_turnover(fully_invested_a, cash), 1.0)

    def test_initial_deployment_cost_is_10_bps_on_100_percent_turnover(self):
        result = build_backtest(synthetic_prices())
        invested_date = result.weights.index[result.weights.sum(axis=1) > 0][0]
        self.assertAlmostEqual(result.one_way_turnover.loc[invested_date], 1.0)
        self.assertAlmostEqual(result.transaction_costs.loc[invested_date], COST_BPS / 10000)
        pd.testing.assert_series_equal(
            result.net_returns,
            (result.gross_returns - result.transaction_costs).rename("net_return"),
        )
        self.assertLessEqual(result.net_metrics["total_return"], result.gross_metrics["total_return"])

    def test_missing_return_for_held_asset_stops_backtest(self):
        prices = synthetic_prices()
        first = build_backtest(prices).weights
        invested = first.index[first.sum(axis=1) > 0][0]
        next_date = first.index[first.index.get_loc(invested) + 1]
        ticker = first.loc[invested].idxmax()
        prices.loc[next_date, ticker] = np.nan
        with self.assertRaisesRegex(ValueError, "Missing return for held asset"):
            build_backtest(prices)


class MetricsAndEvaluationTests(unittest.TestCase):
    def test_drawdown_and_metrics(self):
        self.assertAlmostEqual(max_drawdown([1.0, 1.2, 0.9, 1.1]), -0.25)
        returns = pd.Series([0.1, -0.1])
        equity = (1 + returns).cumprod()
        metrics = performance_metrics(returns, equity, [0.0, 0.0], [0.0, 0.0])
        self.assertAlmostEqual(metrics["total_return"], -0.01)
        self.assertEqual(metrics["observations"], 2)
        self.assertAlmostEqual(metrics["maximum_drawdown"], -0.1)

    def test_benchmark_comparison_uses_only_common_valid_dates(self):
        prices = synthetic_prices()
        benchmark = pd.Series(np.linspace(50, 80, len(prices)), index=prices.index, name="STW.AX")
        prior_date = prices.index[0] - pd.offsets.BDay(1)
        benchmark.loc[prior_date] = benchmark.iloc[0] * 0.999
        missing_date = prices.index[200]
        benchmark = benchmark.drop(missing_date)
        result = build_backtest(prices, benchmark)
        comparison = result.benchmark_comparison
        self.assertNotIn(missing_date, comparison.index)
        self.assertNotIn(prices.index[201], comparison.index)
        self.assertEqual(comparison.index[0], prices.index[0])
        self.assertEqual(len(comparison), len(prices) - 2)
        self.assertEqual(result.benchmark_metrics["observations"], len(comparison))
        self.assertEqual(result.benchmark_metrics["comparison_start"], comparison.index[0].date().isoformat())
        self.assertEqual(result.benchmark_metrics["comparison_end"], comparison.index[-1].date().isoformat())
        self.assertTrue(result.benchmark_status.startswith("Common-date comparison:"))

    def test_chronological_split_preserves_order(self):
        series = pd.Series(range(10), index=pd.date_range("2020-01-01", periods=10))
        train, test = chronological_split(series, 0.7)
        self.assertEqual(train.iloc[-1], 6)
        self.assertEqual(test.iloc[0], 7)
        self.assertLess(train.index[-1], test.index[0])


if __name__ == "__main__":
    unittest.main()
