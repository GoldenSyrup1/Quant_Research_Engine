import unittest

import numpy as np
import pandas as pd

from src.robustness import (
    drawdown_duration, exposure_statistics, fixed_calendar_periods,
    cost_sensitivity, moving_block_bootstrap, tail_day_sensitivity,
)


class RobustnessTests(unittest.TestCase):
    def test_cost_sensitivity_uses_post_market_cost_convention(self):
        dates = pd.date_range("2024-01-01", periods=2, freq="B")
        gross = pd.Series([0.10, 0.0], index=dates)
        turnover = pd.Series([1.0, 0.0], index=dates)
        result = cost_sensitivity(gross, turnover, [10])
        expected_first_net = 0.10 - 1.10 * 0.001
        self.assertAlmostEqual(result.loc[10, "total_return"], expected_first_net)
        self.assertAlmostEqual(result.loc[10, "cost_return_sum"], 0.0011)

    def test_moving_block_bootstrap_is_deterministic(self):
        returns = pd.Series(np.linspace(-0.01, 0.02, 40))
        first = moving_block_bootstrap(returns, block_length=5, samples=20, seed=7)
        second = moving_block_bootstrap(returns, block_length=5, samples=20, seed=7)
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(len(first), 20)

    def test_exposure_statistics_excludes_cash(self):
        weights = pd.DataFrame([[.2] * 5, [1, 0, 0, 0, 0], [0] * 5], columns=list("ABCDE"))
        result = exposure_statistics(weights)
        self.assertAlmostEqual(result["mean_active_holdings"], 2)
        self.assertAlmostEqual(result["mean_largest_risky_weight"], .4)
        self.assertAlmostEqual(result["mean_risky_hhi"], (.2 + 1) / 3)
        with self.assertRaises(ValueError):
            exposure_statistics(pd.DataFrame())

    def test_tail_day_sensitivity_preserves_dates_and_breaks_ties_by_date(self):
        dates = pd.date_range("2024-01-01", periods=4, freq="B")
        returns = pd.Series([.1, .1, -.02, .03], index=dates)
        summary, selected = tail_day_sensitivity(returns, (1, 2))
        self.assertEqual(selected[selected["n"] == 1].iloc[0]["date"], dates[0])
        self.assertAlmostEqual(summary.loc[0, "total_return"], (1.1 * 1.1 * .98 * 1.03) - 1)
        self.assertLess(summary.loc[2, "total_return"], summary.loc[1, "total_return"])
        with self.assertRaises(ValueError):
            tail_day_sensitivity(pd.Series([np.nan], index=[dates[0]]))

    def test_periods_and_drawdown(self):
        dates = pd.bdate_range("2015-01-02", "2026-01-02")
        returns = pd.Series(0.0, index=dates)
        periods = fixed_calendar_periods(returns)
        self.assertEqual(list(periods.index), ["2015-2018", "2019-2022", "2023-2026_partial"])
        self.assertEqual(int(periods.loc["2015-2018", "observations"]), len(returns.loc["2015":"2018"]))
        duration = drawdown_duration(pd.Series([.1, -.2, .0, .3]))
        self.assertEqual(duration["longest_underwater_sessions"], 2)


if __name__ == "__main__":
    unittest.main()
