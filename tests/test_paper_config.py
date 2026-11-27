import unittest
from pathlib import Path

from src.paper_trading.config import ConfigError, build_portfolio, list_configs, load_portfolio_config

CONFIG_DIR = Path(__file__).resolve().parents[1] / "paper_portfolios"

EXPECTED_PORTFOLIOS = {
    "LT-BAL": 50.0,
    "LT-GROWTH": 50.0,
    "LT-EQUITY": 50.0,
    "LT-CASH": 50.0,
    "ST-PAPER": 20.0,
    "RESERVE-CONTROL": 30.0,
}


class ConfigDiscoveryTests(unittest.TestCase):
    def test_all_six_configs_are_present(self):
        configs = list_configs(CONFIG_DIR)
        ids = {load_portfolio_config(p)["portfolio_id"] for p in configs}
        self.assertEqual(ids, set(EXPECTED_PORTFOLIOS))

    def test_starting_balances_match_capital_constraints(self):
        for path in list_configs(CONFIG_DIR):
            config = load_portfolio_config(path)
            self.assertAlmostEqual(
                config["starting_balance_aud"], EXPECTED_PORTFOLIOS[config["portfolio_id"]]
            )

    def test_only_reserve_control_is_restricted(self):
        for path in list_configs(CONFIG_DIR):
            config = load_portfolio_config(path)
            expected = config["portfolio_id"] == "RESERVE-CONTROL"
            self.assertEqual(config["restricted"], expected)

    def test_target_allocation_weights_sum_to_one(self):
        for path in list_configs(CONFIG_DIR):
            config = load_portfolio_config(path)
            total = sum(e["weight"] for e in config["target_allocation"])
            self.assertAlmostEqual(total, 1.0)


class BuildPortfolioTests(unittest.TestCase):
    def test_build_portfolio_only_funds_cash_no_holdings(self):
        config = load_portfolio_config(CONFIG_DIR / "LT-BAL.json")
        portfolio = build_portfolio(config)
        self.assertAlmostEqual(portfolio.cash, 50.0)
        self.assertEqual(portfolio.holdings, {})
        # exactly one DEPOSIT transaction, no buys generated from the
        # declared target_allocation
        self.assertEqual(len(portfolio.transactions), 1)

    def test_reserve_control_portfolio_is_restricted(self):
        config = load_portfolio_config(CONFIG_DIR / "RESERVE-CONTROL.json")
        portfolio = build_portfolio(config)
        self.assertTrue(portfolio.restricted)
        self.assertAlmostEqual(portfolio.cash, 30.0)

    def test_malformed_config_rejected(self):
        bad_config_path = Path(__file__).parent / "_fixtures_malformed_portfolio.json"
        bad_config_path.write_text('{"portfolio_id": "BAD"}', encoding="utf-8")
        try:
            with self.assertRaises(ConfigError):
                load_portfolio_config(bad_config_path)
        finally:
            bad_config_path.unlink()


if __name__ == "__main__":
    unittest.main()
