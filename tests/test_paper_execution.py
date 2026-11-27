import datetime as dt
import unittest

from src.paper_trading.execution import (
    ExecutionError,
    Order,
    betashares_direct_schedule,
    check_limit_touch,
    commsec_pocket_schedule,
    simulate_market_fill,
)
from src.paper_trading.ledger import OrderSide, OrderType, PriceObservation, PriceType


def _obs(instrument, price, price_type, timestamp, source="synthetic-fixture"):
    return PriceObservation(
        instrument=instrument,
        date=timestamp.date(),
        timestamp=timestamp,
        price=price,
        price_type=price_type,
        source=source,
        retrieved_at=timestamp,
        data_vintage="synthetic-fixture-v1",
        source_reference=f"{source}:{instrument}:{timestamp.isoformat()}",
    )


class BidAskFillTests(unittest.TestCase):
    def test_buy_uses_latest_ask(self):
        order = Order("O1", "ABC", OrderSide.BUY, OrderType.MARKET, 10, dt.datetime(2026, 1, 2, 10, 0))
        obs = [
            _obs("ABC", 5.00, PriceType.ASK, dt.datetime(2026, 1, 2, 9, 0)),
            _obs("ABC", 5.05, PriceType.ASK, dt.datetime(2026, 1, 2, 9, 55)),
            _obs("ABC", 4.95, PriceType.BID, dt.datetime(2026, 1, 2, 9, 55)),
        ]
        fill = simulate_market_fill(order, obs, betashares_direct_schedule())
        self.assertAlmostEqual(fill.fill_price, 5.05)
        self.assertIs(fill.price_type_used, PriceType.ASK)
        self.assertFalse(fill.estimated)

    def test_sell_uses_latest_bid(self):
        order = Order("O2", "ABC", OrderSide.SELL, OrderType.MARKET, 10, dt.datetime(2026, 1, 2, 10, 0))
        obs = [
            _obs("ABC", 4.90, PriceType.BID, dt.datetime(2026, 1, 2, 9, 0)),
            _obs("ABC", 4.95, PriceType.BID, dt.datetime(2026, 1, 2, 9, 55)),
        ]
        fill = simulate_market_fill(order, obs, betashares_direct_schedule())
        self.assertAlmostEqual(fill.fill_price, 4.95)
        self.assertIs(fill.price_type_used, PriceType.BID)

    def test_ignores_observations_after_order_timestamp(self):
        order = Order("O3", "ABC", OrderSide.BUY, OrderType.MARKET, 10, dt.datetime(2026, 1, 2, 10, 0))
        obs = [
            _obs("ABC", 5.00, PriceType.ASK, dt.datetime(2026, 1, 2, 9, 0)),
            _obs("ABC", 6.00, PriceType.ASK, dt.datetime(2026, 1, 2, 11, 0)),  # after order time
        ]
        fill = simulate_market_fill(order, obs, betashares_direct_schedule())
        self.assertAlmostEqual(fill.fill_price, 5.00)


class EstimatedSpreadTests(unittest.TestCase):
    def test_estimated_fill_when_no_bid_ask_available(self):
        order = Order("O4", "ABC", OrderSide.BUY, OrderType.MARKET, 10, dt.datetime(2026, 1, 2, 10, 0))
        obs = [_obs("ABC", 5.00, PriceType.CLOSE, dt.datetime(2026, 1, 1))]
        fill = simulate_market_fill(order, obs, betashares_direct_schedule(), spread_bps=20)
        self.assertTrue(fill.estimated)
        self.assertGreater(fill.fill_price, 5.00)  # buy pays above mid

    def test_sell_estimated_fill_is_below_reference_price(self):
        order = Order("O5", "ABC", OrderSide.SELL, OrderType.MARKET, 10, dt.datetime(2026, 1, 2, 10, 0))
        obs = [_obs("ABC", 5.00, PriceType.CLOSE, dt.datetime(2026, 1, 1))]
        fill = simulate_market_fill(order, obs, betashares_direct_schedule(), spread_bps=20)
        self.assertTrue(fill.estimated)
        self.assertLess(fill.fill_price, 5.00)

    def test_raises_without_spread_assumption_when_no_bid_ask(self):
        order = Order("O6", "ABC", OrderSide.BUY, OrderType.MARKET, 10, dt.datetime(2026, 1, 2, 10, 0))
        obs = [_obs("ABC", 5.00, PriceType.CLOSE, dt.datetime(2026, 1, 1))]
        with self.assertRaises(ExecutionError):
            simulate_market_fill(order, obs, betashares_direct_schedule())


class NavIsNotExecutableTests(unittest.TestCase):
    def test_nav_only_observation_refuses_to_fill(self):
        order = Order("O7", "ABC", OrderSide.BUY, OrderType.MARKET, 10, dt.datetime(2026, 1, 2, 10, 0))
        obs = [_obs("ABC", 5.00, PriceType.NAV, dt.datetime(2026, 1, 1))]
        with self.assertRaises(ExecutionError):
            simulate_market_fill(order, obs, betashares_direct_schedule(), spread_bps=20)

    def test_no_observation_at_all_raises(self):
        order = Order("O8", "ABC", OrderSide.BUY, OrderType.MARKET, 10, dt.datetime(2026, 1, 2, 10, 0))
        with self.assertRaises(ExecutionError):
            simulate_market_fill(order, [], betashares_direct_schedule(), spread_bps=20)


class LimitOrderSafetyTests(unittest.TestCase):
    def test_limit_order_cannot_be_auto_filled(self):
        order = Order("O9", "ABC", OrderSide.BUY, OrderType.LIMIT, 10, dt.datetime(2026, 1, 2, 10, 0), limit_price=5.00)
        obs = [_obs("ABC", 5.00, PriceType.ASK, dt.datetime(2026, 1, 2, 9, 0))]
        with self.assertRaises(ExecutionError):
            simulate_market_fill(order, obs, betashares_direct_schedule())

    def test_limit_touch_is_informational_only(self):
        order = Order("O10", "ABC", OrderSide.BUY, OrderType.LIMIT, 10, dt.datetime(2026, 1, 2, 10, 0), limit_price=5.00)
        touched = [_obs("ABC", 4.99, PriceType.ASK, dt.datetime(2026, 1, 2, 9, 0))]
        not_touched = [_obs("ABC", 5.50, PriceType.ASK, dt.datetime(2026, 1, 2, 9, 0))]
        self.assertTrue(check_limit_touch(order, touched))
        self.assertFalse(check_limit_touch(order, not_touched))

    def test_limit_price_required_for_limit_orders(self):
        with self.assertRaises(ValueError):
            Order("O11", "ABC", OrderSide.BUY, OrderType.LIMIT, 10, dt.datetime(2026, 1, 2, 10, 0))


class BrokerageScheduleTests(unittest.TestCase):
    def test_betashares_direct_is_always_zero_fee(self):
        schedule = betashares_direct_schedule()
        self.assertEqual(schedule.fee_for(1000.0, dt.date(2026, 1, 1)), 0.0)
        self.assertEqual(schedule.fee_for(1000.0, dt.date(2030, 1, 1)), 0.0)

    def test_commsec_pocket_is_free_before_promotion_end(self):
        schedule = commsec_pocket_schedule()
        self.assertEqual(schedule.fee_for(500.0, dt.date(2027, 3, 31)), 0.0)

    def test_commsec_pocket_charges_two_dollars_after_promotion(self):
        schedule = commsec_pocket_schedule()
        self.assertEqual(schedule.fee_for(500.0, dt.date(2027, 4, 1)), 2.0)
        self.assertEqual(schedule.fee_for(1000.0, dt.date(2027, 4, 1)), 2.0)

    def test_commsec_pocket_fee_unmodelled_above_threshold(self):
        schedule = commsec_pocket_schedule()
        with self.assertRaises(ExecutionError):
            schedule.fee_for(1500.0, dt.date(2027, 4, 1))

    def test_fee_applied_during_simulated_fill_uses_order_date(self):
        order = Order("O12", "ABC", OrderSide.BUY, OrderType.MARKET, 100, dt.datetime(2027, 4, 2, 10, 0))
        obs = [_obs("ABC", 5.00, PriceType.ASK, dt.datetime(2027, 4, 2, 9, 0))]
        fill = simulate_market_fill(order, obs, commsec_pocket_schedule())
        self.assertEqual(fill.fee, 2.0)


class ProvenanceTests(unittest.TestCase):
    def test_fill_carries_a_source_reference(self):
        order = Order("O13", "ABC", OrderSide.BUY, OrderType.MARKET, 10, dt.datetime(2026, 1, 2, 10, 0))
        obs = [_obs("ABC", 5.00, PriceType.ASK, dt.datetime(2026, 1, 2, 9, 0), source="asx-synthetic")]
        fill = simulate_market_fill(order, obs, betashares_direct_schedule())
        self.assertIsNotNone(fill.source_reference)
        self.assertIn("asx-synthetic", fill.source_reference)

    def test_invalid_price_observation_rejected(self):
        with self.assertRaises(ValueError):
            _obs("ABC", -1.0, PriceType.ASK, dt.datetime(2026, 1, 2))
        with self.assertRaises(ValueError):
            _obs("ABC", float("nan"), PriceType.ASK, dt.datetime(2026, 1, 2))


if __name__ == "__main__":
    unittest.main()
