import unittest

import numpy as np
import pandas as pd

from src.robustness import cost_sensitivity, moving_block_bootstrap


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


if __name__ == "__main__":
    unittest.main()
