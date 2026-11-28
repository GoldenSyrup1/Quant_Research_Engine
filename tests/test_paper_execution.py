import datetime as dt
import unittest

from src.paper_trading.execution import (
    TERMS_VERIFIED_AS_OF,
    ExecutionError,
    Order,
    betashares_direct_schedule,
    check_limit_touch,
    commsec_pocket_schedule,
    simulate_market_fill,
)
from src.paper_trading.ledger import OrderSide, OrderType, PriceObservation, PriceType

# All order timestamps in this file are on/after TERMS_VERIFIED_AS_OF so
# that brokerage-schedule lookups succeed; PAPER-002's backdating fix is
# tested explicitly in BrokerageScheduleBackdatingTests below.
D0 = dt.datetime.combine(TERMS_VERIFIED_AS_OF, dt.time(10, 0))


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
        order = Order("O1", "ABC", OrderSide.BUY, OrderType.MARKET, 10, D0)
        obs = [
            _obs("ABC", 5.00, PriceType.ASK, D0 - dt.timedelta(hours=1)),
            _obs("ABC", 5.05, PriceType.ASK, D0 - dt.timedelta(minutes=5)),
            _obs("ABC", 4.95, PriceType.BID, D0 - dt.timedelta(minutes=5)),
        ]
        fill = simulate_market_fill(order, obs, betashares_direct_schedule())
        self.assertAlmostEqual(fill.fill_price, 5.05)
        self.assertIs(fill.price_type_used, PriceType.ASK)
        self.assertFalse(fill.estimated)

    def test_sell_uses_latest_bid(self):
        order = Order("O2", "ABC", OrderSide.SELL, OrderType.MARKET, 10, D0)
        obs = [
            _obs("ABC", 4.90, PriceType.BID, D0 - dt.timedelta(hours=1)),
            _obs("ABC", 4.95, PriceType.BID, D0 - dt.timedelta(minutes=5)),
        ]
        fill = simulate_market_fill(order, obs, betashares_direct_schedule())
        self.assertAlmostEqual(fill.fill_price, 4.95)
        self.assertIs(fill.price_type_used, PriceType.BID)

    def test_ignores_observations_after_order_timestamp(self):
        order = Order("O3", "ABC", OrderSide.BUY, OrderType.MARKET, 10, D0)
        obs = [
            _obs("ABC", 5.00, PriceType.ASK, D0 - dt.timedelta(hours=1)),
            _obs("ABC", 6.00, PriceType.ASK, D0 + dt.timedelta(hours=1)),  # after order time
        ]
        fill = simulate_market_fill(order, obs, betashares_direct_schedule())
        self.assertAlmostEqual(fill.fill_price, 5.00)


class EstimatedSpreadTests(unittest.TestCase):
    def test_estimated_fill_when_no_bid_ask_available(self):
        order = Order("O4", "ABC", OrderSide.BUY, OrderType.MARKET, 10, D0)
        obs = [_obs("ABC", 5.00, PriceType.CLOSE, D0 - dt.timedelta(days=1))]
        fill = simulate_market_fill(order, obs, betashares_direct_schedule(), spread_bps=20)
        self.assertTrue(fill.estimated)
        self.assertGreater(fill.fill_price, 5.00)  # buy pays above mid

    def test_sell_estimated_fill_is_below_reference_price(self):
        order = Order("O5", "ABC", OrderSide.SELL, OrderType.MARKET, 10, D0)
        obs = [_obs("ABC", 5.00, PriceType.CLOSE, D0 - dt.timedelta(days=1))]
        fill = simulate_market_fill(order, obs, betashares_direct_schedule(), spread_bps=20)
        self.assertTrue(fill.estimated)
        self.assertLess(fill.fill_price, 5.00)

    def test_raises_without_spread_assumption_when_no_bid_ask(self):
        order = Order("O6", "ABC", OrderSide.BUY, OrderType.MARKET, 10, D0)
        obs = [_obs("ABC", 5.00, PriceType.CLOSE, D0 - dt.timedelta(days=1))]
        with self.assertRaises(ExecutionError):
            simulate_market_fill(order, obs, betashares_direct_schedule())


class NavIsNotExecutableTests(unittest.TestCase):
    def test_nav_only_observation_refuses_to_fill(self):
        order = Order("O7", "ABC", OrderSide.BUY, OrderType.MARKET, 10, D0)
        obs = [_obs("ABC", 5.00, PriceType.NAV, D0 - dt.timedelta(days=1))]
        with self.assertRaises(ExecutionError):
            simulate_market_fill(order, obs, betashares_direct_schedule(), spread_bps=20)

    def test_no_observation_at_all_raises(self):
        order = Order("O8", "ABC", OrderSide.BUY, OrderType.MARKET, 10, D0)
        with self.assertRaises(ExecutionError):
            simulate_market_fill(order, [], betashares_direct_schedule(), spread_bps=20)


class LimitOrderSafetyTests(unittest.TestCase):
    def test_limit_order_cannot_be_auto_filled(self):
        order = Order("O9", "ABC", OrderSide.BUY, OrderType.LIMIT, 10, D0, limit_price=5.00)
        obs = [_obs("ABC", 5.00, PriceType.ASK, D0 - dt.timedelta(hours=1))]
        with self.assertRaises(ExecutionError):
            simulate_market_fill(order, obs, betashares_direct_schedule())

    def test_limit_price_required_for_limit_orders(self):
        with self.assertRaises(ValueError):
            Order("O11", "ABC", OrderSide.BUY, OrderType.LIMIT, 10, D0)

    def test_limit_price_must_be_positive(self):
        with self.assertRaises(ValueError):
            Order("O11b", "ABC", OrderSide.BUY, OrderType.LIMIT, 10, D0, limit_price=-1.0)


class LimitTouchWindowAndSideTests(unittest.TestCase):
    """PAPER-002 correctness fix: a touch must be assessed on observations
    strictly AFTER placement (not before), only up to an optional expiry,
    and only on the side relevant to the order (ASK for a BUY limit, BID
    for a SELL limit) by default."""

    def test_touch_after_placement_is_detected(self):
        order = Order("L1", "ABC", OrderSide.BUY, OrderType.LIMIT, 10, D0, limit_price=5.00)
        after = [_obs("ABC", 4.99, PriceType.ASK, D0 + dt.timedelta(minutes=1))]
        self.assertTrue(check_limit_touch(order, after))

    def test_observation_before_placement_is_not_considered(self):
        order = Order("L2", "ABC", OrderSide.BUY, OrderType.LIMIT, 10, D0, limit_price=5.00)
        before = [_obs("ABC", 4.99, PriceType.ASK, D0 - dt.timedelta(minutes=1))]
        self.assertFalse(check_limit_touch(order, before))

    def test_observation_exactly_at_placement_time_is_not_considered(self):
        order = Order("L3", "ABC", OrderSide.BUY, OrderType.LIMIT, 10, D0, limit_price=5.00)
        at_placement = [_obs("ABC", 4.99, PriceType.ASK, D0)]
        self.assertFalse(check_limit_touch(order, at_placement))

    def test_buy_limit_only_considers_ask_side_by_default(self):
        order = Order("L4", "ABC", OrderSide.BUY, OrderType.LIMIT, 10, D0, limit_price=5.00)
        # A BID at or below the limit must NOT count as a touch for a BUY
        # limit -- a buyer pays the ask, not the bid.
        bid_only = [_obs("ABC", 4.50, PriceType.BID, D0 + dt.timedelta(minutes=1))]
        self.assertFalse(check_limit_touch(order, bid_only))

    def test_sell_limit_only_considers_bid_side_by_default(self):
        order = Order("L5", "ABC", OrderSide.SELL, OrderType.LIMIT, 10, D0, limit_price=5.00)
        ask_only = [_obs("ABC", 5.50, PriceType.ASK, D0 + dt.timedelta(minutes=1))]
        self.assertFalse(check_limit_touch(order, ask_only))

    def test_expiry_excludes_observations_after_it(self):
        expiry = D0 + dt.timedelta(days=1)
        order = Order("L6", "ABC", OrderSide.BUY, OrderType.LIMIT, 10, D0, limit_price=5.00, expiry=expiry)
        after_expiry = [_obs("ABC", 4.99, PriceType.ASK, expiry + dt.timedelta(minutes=1))]
        self.assertFalse(check_limit_touch(order, after_expiry))

    def test_expiry_boundary_is_inclusive(self):
        expiry = D0 + dt.timedelta(days=1)
        order = Order("L7", "ABC", OrderSide.BUY, OrderType.LIMIT, 10, D0, limit_price=5.00, expiry=expiry)
        at_expiry = [_obs("ABC", 4.99, PriceType.ASK, expiry)]
        self.assertTrue(check_limit_touch(order, at_expiry))

    def test_last_close_fallback_is_opt_in_only(self):
        order = Order("L8", "ABC", OrderSide.BUY, OrderType.LIMIT, 10, D0, limit_price=5.00)
        last_print = [_obs("ABC", 4.99, PriceType.LAST, D0 + dt.timedelta(minutes=1))]
        self.assertFalse(check_limit_touch(order, last_print))
        self.assertTrue(check_limit_touch(order, last_print, allow_last_close_fallback=True))

    def test_expiry_must_be_after_order_timestamp(self):
        with self.assertRaises(ValueError):
            Order("L9", "ABC", OrderSide.BUY, OrderType.LIMIT, 10, D0, limit_price=5.00, expiry=D0)


class QuoteFreshnessTests(unittest.TestCase):
    def test_fresh_quote_is_accepted(self):
        order = Order("F1", "ABC", OrderSide.BUY, OrderType.MARKET, 10, D0)
        obs = [_obs("ABC", 5.00, PriceType.ASK, D0 - dt.timedelta(minutes=1))]
        fill = simulate_market_fill(order, obs, betashares_direct_schedule(), max_quote_age=dt.timedelta(minutes=5))
        self.assertAlmostEqual(fill.fill_price, 5.00)

    def test_quote_exactly_at_freshness_boundary_is_accepted(self):
        order = Order("F2", "ABC", OrderSide.BUY, OrderType.MARKET, 10, D0)
        obs = [_obs("ABC", 5.00, PriceType.ASK, D0 - dt.timedelta(minutes=5))]
        fill = simulate_market_fill(order, obs, betashares_direct_schedule(), max_quote_age=dt.timedelta(minutes=5))
        self.assertAlmostEqual(fill.fill_price, 5.00)

    def test_stale_quote_is_rejected(self):
        order = Order("F3", "ABC", OrderSide.BUY, OrderType.MARKET, 10, D0)
        obs = [_obs("ABC", 5.00, PriceType.ASK, D0 - dt.timedelta(minutes=6))]
        with self.assertRaises(ExecutionError):
            simulate_market_fill(order, obs, betashares_direct_schedule(), max_quote_age=dt.timedelta(minutes=5))

    def test_missing_bid_ask_with_freshness_configured_falls_through_to_estimate_error(self):
        order = Order("F4", "ABC", OrderSide.BUY, OrderType.MARKET, 10, D0)
        obs = [_obs("ABC", 5.00, PriceType.CLOSE, D0 - dt.timedelta(days=1))]
        with self.assertRaises(ExecutionError):
            simulate_market_fill(order, obs, betashares_direct_schedule(), max_quote_age=dt.timedelta(minutes=5))

    def test_invalid_order_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            Order("F5", "ABC", OrderSide.BUY, OrderType.MARKET, 10, "2026-11-28")  # not a datetime


class BrokerageScheduleTests(unittest.TestCase):
    def test_betashares_direct_is_zero_fee_from_verification_date(self):
        schedule = betashares_direct_schedule()
        self.assertEqual(schedule.fee_for(1000.0, TERMS_VERIFIED_AS_OF), 0.0)
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
        order = Order("O12", "ABC", OrderSide.BUY, OrderType.MARKET, 100, D0 + dt.timedelta(days=200))
        obs = [_obs("ABC", 5.00, PriceType.ASK, D0 + dt.timedelta(days=200) - dt.timedelta(hours=1))]
        fill = simulate_market_fill(order, obs, commsec_pocket_schedule())
        self.assertEqual(fill.fee, 2.0)


class BrokerageScheduleBackdatingTests(unittest.TestCase):
    """PAPER-002 correctness fix: current/promotional terms must not be
    treated as if they applied historically before they were verified."""

    def test_betashares_direct_rejects_dates_before_verification(self):
        schedule = betashares_direct_schedule()
        with self.assertRaises(ExecutionError):
            schedule.fee_for(1000.0, TERMS_VERIFIED_AS_OF - dt.timedelta(days=1))
        with self.assertRaises(ExecutionError):
            schedule.fee_for(1000.0, dt.date(2000, 1, 1))

    def test_commsec_pocket_rejects_dates_before_verification(self):
        schedule = commsec_pocket_schedule()
        with self.assertRaises(ExecutionError):
            schedule.fee_for(500.0, TERMS_VERIFIED_AS_OF - dt.timedelta(days=1))
        with self.assertRaises(ExecutionError):
            schedule.fee_for(500.0, dt.date(2000, 1, 1))

    def test_historical_fill_before_verification_date_is_rejected(self):
        early_order_time = dt.datetime(2020, 1, 2, 10, 0)
        order = Order("O13", "ABC", OrderSide.BUY, OrderType.MARKET, 10, early_order_time)
        obs = [_obs("ABC", 5.00, PriceType.ASK, early_order_time - dt.timedelta(hours=1))]
        with self.assertRaises(ExecutionError):
            simulate_market_fill(order, obs, betashares_direct_schedule())


class ProvenanceTests(unittest.TestCase):
    def test_fill_carries_a_source_reference(self):
        order = Order("O14", "ABC", OrderSide.BUY, OrderType.MARKET, 10, D0)
        obs = [_obs("ABC", 5.00, PriceType.ASK, D0 - dt.timedelta(hours=1), source="asx-synthetic")]
        fill = simulate_market_fill(order, obs, betashares_direct_schedule())
        self.assertIsNotNone(fill.source_reference)
        self.assertIn("asx-synthetic", fill.source_reference)

    def test_invalid_price_observation_rejected(self):
        with self.assertRaises(ValueError):
            _obs("ABC", -1.0, PriceType.ASK, D0)
        with self.assertRaises(ValueError):
            _obs("ABC", float("nan"), PriceType.ASK, D0)

    def test_invalid_observation_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            PriceObservation(
                instrument="ABC",
                date=dt.date(2026, 11, 28),
                timestamp="2026-11-28",  # not a datetime
                price=5.0,
                price_type=PriceType.ASK,
                source="synthetic-fixture",
                retrieved_at=D0,
                data_vintage="synthetic-fixture-v1",
            )


if __name__ == "__main__":
    unittest.main()
