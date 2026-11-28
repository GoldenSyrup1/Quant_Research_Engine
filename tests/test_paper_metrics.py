import datetime as dt
import unittest

import pandas as pd

from src.paper_trading.ledger import (
    AmbiguousPriceBasisError,
    DistributionEvent,
    Fill,
    OrderSide,
    PaperPortfolio,
    PriceBasis,
    PriceObservation,
    PriceType,
)
from src.paper_trading.metrics import (
    MetricsError,
    allocation,
    benchmark_relative,
    drawdown,
    nav,
    realised_pl,
    time_weighted_return,
    unrealised_pl,
)


def _fill(instrument, side, quantity, price, fee=0.0, timestamp=None):
    return Fill(
        instrument=instrument,
        side=side,
        quantity=quantity,
        fill_price=price,
        price_type_used=PriceType.CLOSE,
        estimated=False,
        fee=fee,
        timestamp=timestamp or dt.datetime(2026, 1, 2),
        source_reference="synthetic-fixture",
    )


def _obs(instrument, price, timestamp, price_type=PriceType.CLOSE, price_basis=PriceBasis.UNADJUSTED):
    return PriceObservation(
        instrument=instrument,
        date=timestamp.date(),
        timestamp=timestamp,
        price=price,
        price_type=price_type,
        source="synthetic-fixture",
        retrieved_at=timestamp,
        data_vintage="synthetic-fixture-v1",
        price_basis=price_basis,
    )


class NavTests(unittest.TestCase):
    def test_nav_is_cash_plus_holdings_value(self):
        p = PaperPortfolio("TEST", starting_balance=100.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0, timestamp=dt.datetime(2026, 1, 2)))
        obs = [_obs("ABC", 6.0, dt.datetime(2026, 1, 5))]
        value = nav(p, obs, as_of=dt.datetime(2026, 1, 5, 23, 59))
        # cash: 100 - 50 = 50; holdings: 10 * 6.0 = 60; nav = 110
        self.assertAlmostEqual(value, 110.0)

    def test_nav_at_an_earlier_date_excludes_later_trades(self):
        p = PaperPortfolio("TEST", starting_balance=100.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0, timestamp=dt.datetime(2026, 1, 2)))
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0, timestamp=dt.datetime(2026, 1, 10)))
        obs = [_obs("ABC", 6.0, dt.datetime(2026, 1, 5))]
        value = nav(p, obs, as_of=dt.datetime(2026, 1, 5, 23, 59))
        self.assertAlmostEqual(value, 100.0 - 50.0 + 10 * 6.0)  # second buy not yet happened

    def test_nav_raises_on_missing_valuation_price(self):
        p = PaperPortfolio("TEST", starting_balance=100.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0, timestamp=dt.datetime(2026, 1, 2)))
        with self.assertRaises(MetricsError):
            nav(p, [], as_of=dt.datetime(2026, 1, 5))

    def test_nav_never_uses_bid_ask_for_valuation(self):
        p = PaperPortfolio("TEST", starting_balance=100.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0, timestamp=dt.datetime(2026, 1, 2)))
        obs = [_obs("ABC", 7.0, dt.datetime(2026, 1, 3), price_type=PriceType.BID)]
        with self.assertRaises(MetricsError):
            nav(p, obs, as_of=dt.datetime(2026, 1, 5))  # bid is not a valid valuation source here


class RealisedUnrealisedPlTests(unittest.TestCase):
    def test_realised_pl_sums_across_sells(self):
        p = PaperPortfolio("TEST", starting_balance=1000.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0))
        p.sell(_fill("ABC", OrderSide.SELL, 5, 7.0))
        p.sell(_fill("ABC", OrderSide.SELL, 5, 8.0))
        self.assertAlmostEqual(realised_pl(p), (5 * (7.0 - 5.0)) + (5 * (8.0 - 5.0)))

    def test_unrealised_pl_uses_current_valuation_price(self):
        p = PaperPortfolio("TEST", starting_balance=1000.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0))
        obs = [_obs("ABC", 6.0, dt.datetime(2026, 1, 5))]
        self.assertAlmostEqual(unrealised_pl(p, obs, dt.datetime(2026, 1, 5)), 10 * (6.0 - 5.0))


class AllocationTests(unittest.TestCase):
    def test_allocation_sums_to_one_including_cash(self):
        p = PaperPortfolio("TEST", starting_balance=100.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0, timestamp=dt.datetime(2026, 1, 2)))
        obs = [_obs("ABC", 5.0, dt.datetime(2026, 1, 5))]
        alloc = allocation(p, obs, as_of=dt.datetime(2026, 1, 5))
        self.assertAlmostEqual(sum(alloc.values()), 1.0)
        self.assertAlmostEqual(alloc["ABC"], 50.0 / 100.0)
        self.assertAlmostEqual(alloc["CASH"], 50.0 / 100.0)


class TimeWeightedReturnTests(unittest.TestCase):
    def test_twr_ignores_impact_of_a_mid_period_deposit(self):
        # Period 1: 100 -> 110 (10% return), then a 50 deposit.
        # Period 2: 160 -> 176 (10% return again).
        points = [
            (dt.datetime(2026, 1, 1), 100.0),
            (dt.datetime(2026, 2, 1), 110.0),
            (dt.datetime(2026, 3, 1), 176.0),
        ]
        flows = {dt.datetime(2026, 2, 1): 50.0}
        twr = time_weighted_return(points, flows)
        # (1.10)*(1.10) - 1 = 0.21
        self.assertAlmostEqual(twr, 0.21, places=6)

    def test_twr_requires_at_least_two_points(self):
        with self.assertRaises(MetricsError):
            time_weighted_return([(dt.datetime(2026, 1, 1), 100.0)], {})


class DrawdownTests(unittest.TestCase):
    def test_drawdown_of_a_known_series(self):
        series = [100.0, 110.0, 90.0, 95.0]
        # normalised: 1.0, 1.1, 0.9, 0.95 -> max drawdown from peak 1.1 to 0.9 = -0.1818...
        dd = drawdown(series)
        self.assertAlmostEqual(dd, (0.9 / 1.1) - 1.0, places=6)

    def test_drawdown_of_monotonically_increasing_series_is_zero(self):
        self.assertAlmostEqual(drawdown([100.0, 101.0, 105.0]), 0.0)


class BenchmarkAlignmentTests(unittest.TestCase):
    def test_benchmark_relative_aligns_on_common_dates_only(self):
        portfolio = pd.Series(
            [0.01, 0.02, 0.0, 0.015],
            index=pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-05"]),
        )
        benchmark = pd.Series(
            [0.005, 0.01, 0.02],
            index=pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-05"]),
        )
        result = benchmark_relative(portfolio, benchmark)
        self.assertEqual(result["aligned_observations"], 3)  # 01-03 dropped, no forward-fill
        expected_portfolio_total = (1.01 * 1.02 * 1.015) - 1.0
        expected_benchmark_total = (1.005 * 1.01 * 1.02) - 1.0
        self.assertAlmostEqual(result["portfolio_total_return"], expected_portfolio_total)
        self.assertAlmostEqual(result["benchmark_total_return"], expected_benchmark_total)
        self.assertAlmostEqual(
            result["excess_return"], expected_portfolio_total - expected_benchmark_total
        )

    def test_benchmark_relative_raises_without_overlap(self):
        portfolio = pd.Series([0.01], index=pd.to_datetime(["2026-01-01"]))
        benchmark = pd.Series([0.01], index=pd.to_datetime(["2026-02-01"]))
        with self.assertRaises(MetricsError):
            benchmark_relative(portfolio, benchmark)


class HistoricalUnrealisedPlTests(unittest.TestCase):
    """PAPER-002 correctness fix: unrealised_pl(as_of=X) must use the
    holdings and cost basis that existed at X, not the portfolio's current
    (possibly later) state."""

    def test_a_later_buy_does_not_change_an_earlier_unrealised_pl(self):
        p = PaperPortfolio("TEST", starting_balance=1000.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0, timestamp=dt.datetime(2026, 1, 2)))
        obs = [_obs("ABC", 6.0, dt.datetime(2026, 1, 5))]
        before_later_buy = unrealised_pl(p, obs, as_of=dt.datetime(2026, 1, 5))

        # A buy recorded AFTER the as_of date, at a different price, which
        # would change the live average cost if used.
        p.buy(_fill("ABC", OrderSide.BUY, 10, 9.0, timestamp=dt.datetime(2026, 2, 1)))
        after_later_buy = unrealised_pl(p, obs, as_of=dt.datetime(2026, 1, 5))

        self.assertAlmostEqual(before_later_buy, after_later_buy)
        self.assertAlmostEqual(after_later_buy, 10 * (6.0 - 5.0))

    def test_historical_reconstruction_uses_correct_units_and_cost_basis(self):
        p = PaperPortfolio("TEST", starting_balance=1000.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 4.0, timestamp=dt.datetime(2026, 1, 2)))  # avg cost 4.0
        p.buy(_fill("ABC", OrderSide.BUY, 10, 6.0, timestamp=dt.datetime(2026, 1, 10)))  # avg cost -> 5.0
        obs = [_obs("ABC", 7.0, dt.datetime(2026, 1, 4))]  # valid for both as_of queries below
        # As of 2026-01-05 (before the second buy), only 10 units at avg cost 4.0 existed.
        pl_before_second_buy = unrealised_pl(p, obs, as_of=dt.datetime(2026, 1, 5))
        self.assertAlmostEqual(pl_before_second_buy, 10 * (7.0 - 4.0))
        # As of 2026-01-15 (after both buys), 20 units at avg cost 5.0.
        pl_after_both_buys = unrealised_pl(p, obs, as_of=dt.datetime(2026, 1, 15))
        self.assertAlmostEqual(pl_after_both_buys, 20 * (7.0 - 5.0))

    def test_current_calculation_remains_correct(self):
        p = PaperPortfolio("TEST", starting_balance=1000.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0, timestamp=dt.datetime(2026, 1, 2)))
        obs = [_obs("ABC", 8.0, dt.datetime(2026, 6, 1))]
        self.assertAlmostEqual(unrealised_pl(p, obs, as_of=dt.datetime(2026, 6, 1)), 10 * (8.0 - 5.0))


class PriceBasisDoubleCountingTests(unittest.TestCase):
    def _distribution_event(self):
        return DistributionEvent(
            event_id="D1",
            instrument="ABC",
            record_date=dt.date(2026, 1, 1),
            pay_date=dt.date(2026, 1, 5),
            amount_per_unit=0.10,
            source="synthetic-fixture",
            retrieved_at=dt.datetime(2026, 1, 5),
        )

    def test_unadjusted_price_with_applied_distribution_is_valid(self):
        p = PaperPortfolio("TEST", starting_balance=1000.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0, timestamp=dt.datetime(2026, 1, 2)))
        p.apply_distribution(self._distribution_event())
        obs = [_obs("ABC", 6.0, dt.datetime(2026, 1, 10), price_basis=PriceBasis.UNADJUSTED)]
        # Should not raise.
        value = nav(p, obs, as_of=dt.datetime(2026, 1, 10))
        self.assertGreater(value, 0)

    def test_adjusted_total_return_price_with_no_distribution_is_valid(self):
        p = PaperPortfolio("TEST", starting_balance=1000.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0, timestamp=dt.datetime(2026, 1, 2)))
        obs = [_obs("ABC", 6.0, dt.datetime(2026, 1, 10), price_basis=PriceBasis.ADJUSTED_TOTAL_RETURN)]
        value = nav(p, obs, as_of=dt.datetime(2026, 1, 10))
        self.assertGreater(value, 0)

    def test_adjusted_total_return_price_combined_with_applied_distribution_is_rejected(self):
        p = PaperPortfolio("TEST", starting_balance=1000.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0, timestamp=dt.datetime(2026, 1, 2)))
        p.apply_distribution(self._distribution_event())
        obs = [_obs("ABC", 6.0, dt.datetime(2026, 1, 10), price_basis=PriceBasis.ADJUSTED_TOTAL_RETURN)]
        with self.assertRaises(AmbiguousPriceBasisError):
            nav(p, obs, as_of=dt.datetime(2026, 1, 10))

    def test_distribution_applied_after_the_adjusted_valuation_date_does_not_retroactively_break_it(self):
        p = PaperPortfolio("TEST", starting_balance=1000.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0, timestamp=dt.datetime(2026, 1, 2)))
        obs = [_obs("ABC", 6.0, dt.datetime(2026, 1, 3), price_basis=PriceBasis.ADJUSTED_TOTAL_RETURN)]
        # Valuing as of 2026-01-03, before any distribution has been applied, is fine...
        value = nav(p, obs, as_of=dt.datetime(2026, 1, 3))
        self.assertGreater(value, 0)
        # ...even after a distribution for the same instrument is later applied with a pay_date
        # after this valuation point -- distributed_instruments_asof must not see it retroactively.
        p.apply_distribution(self._distribution_event())
        value_again = nav(p, obs, as_of=dt.datetime(2026, 1, 3))
        self.assertAlmostEqual(value_again, value)


if __name__ == "__main__":
    unittest.main()
