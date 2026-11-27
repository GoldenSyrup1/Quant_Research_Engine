import datetime as dt
import unittest

from src.paper_trading.ledger import (
    DistributionEvent,
    DuplicateDistributionError,
    Fill,
    InsufficientCashError,
    InsufficientHoldingsError,
    OrderSide,
    PaperPortfolio,
    PriceType,
    RestrictedPortfolioError,
    UnknownDistributionError,
    holdings_asof,
)


def _fill(instrument, side, quantity, price, fee=0.0, timestamp=None, estimated=False, price_type=PriceType.CLOSE):
    return Fill(
        instrument=instrument,
        side=side,
        quantity=quantity,
        fill_price=price,
        price_type_used=price_type,
        estimated=estimated,
        fee=fee,
        timestamp=timestamp or dt.datetime(2026, 1, 2),
        source_reference="synthetic-fixture",
    )


class BuySellAccountingTests(unittest.TestCase):
    def test_buy_reduces_cash_and_adds_units(self):
        p = PaperPortfolio("TEST", starting_balance=100.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0, fee=1.0))
        self.assertAlmostEqual(p.cash, 100.0 - 50.0 - 1.0)
        self.assertAlmostEqual(p.units_held("ABC"), 10.0)
        self.assertAlmostEqual(p.average_cost("ABC"), (50.0 + 1.0) / 10.0)

    def test_sell_increases_cash_and_removes_units(self):
        p = PaperPortfolio("TEST", starting_balance=100.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0))
        p.sell(_fill("ABC", OrderSide.SELL, 4, 6.0, fee=0.5))
        self.assertAlmostEqual(p.units_held("ABC"), 6.0)
        # cash: 100 - 50 (buy) + (4*6 - 0.5) (sell)
        self.assertAlmostEqual(p.cash, 100.0 - 50.0 + (24.0 - 0.5))

    def test_realised_pl_uses_average_cost(self):
        p = PaperPortfolio("TEST", starting_balance=1000.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0))  # avg cost 5.0
        p.buy(_fill("ABC", OrderSide.BUY, 10, 7.0))  # avg cost -> (50+70)/20 = 6.0
        self.assertAlmostEqual(p.average_cost("ABC"), 6.0)
        txn = p.sell(_fill("ABC", OrderSide.SELL, 5, 9.0))
        # proceeds 45, cost basis 5*6.0=30 -> pl 15
        self.assertAlmostEqual(txn.realised_pl, 15.0)


class CashAndShortingSafetyTests(unittest.TestCase):
    def test_no_negative_cash_on_buy(self):
        p = PaperPortfolio("TEST", starting_balance=10.0)
        with self.assertRaises(InsufficientCashError):
            p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0))  # costs 50 > 10 cash
        self.assertAlmostEqual(p.cash, 10.0)
        self.assertEqual(p.units_held("ABC"), 0.0)

    def test_no_short_positions(self):
        p = PaperPortfolio("TEST", starting_balance=1000.0)
        with self.assertRaises(InsufficientHoldingsError):
            p.sell(_fill("ABC", OrderSide.SELL, 1, 5.0))

    def test_cannot_sell_more_than_held(self):
        p = PaperPortfolio("TEST", starting_balance=1000.0)
        p.buy(_fill("ABC", OrderSide.BUY, 5, 5.0))
        with self.assertRaises(InsufficientHoldingsError):
            p.sell(_fill("ABC", OrderSide.SELL, 6, 5.0))

    def test_withdrawal_cannot_exceed_cash(self):
        p = PaperPortfolio("TEST", starting_balance=10.0)
        with self.assertRaises(InsufficientCashError):
            p.withdraw(20.0, timestamp=dt.datetime(2026, 1, 1))


class FractionalUnitTests(unittest.TestCase):
    def test_fractional_buy_and_partial_sell(self):
        p = PaperPortfolio("TEST", starting_balance=100.0)
        p.buy(_fill("ABC", OrderSide.BUY, 3.333, 3.0))
        self.assertAlmostEqual(p.units_held("ABC"), 3.333)
        p.sell(_fill("ABC", OrderSide.SELL, 1.111, 3.5))
        self.assertAlmostEqual(p.units_held("ABC"), 3.333 - 1.111, places=6)


class BrokerageChargingTests(unittest.TestCase):
    def test_fee_is_deducted_from_cash_on_buy(self):
        p = PaperPortfolio("TEST", starting_balance=100.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0, fee=2.0))
        self.assertAlmostEqual(p.cash, 100.0 - 50.0 - 2.0)

    def test_fee_is_deducted_from_proceeds_on_sell(self):
        p = PaperPortfolio("TEST", starting_balance=100.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0))
        p.sell(_fill("ABC", OrderSide.SELL, 10, 5.0, fee=2.0))
        self.assertAlmostEqual(p.cash, 100.0 - 50.0 + (50.0 - 2.0))


class DistributionTests(unittest.TestCase):
    def _event(self, event_id="D1", instrument="ABC", amount=0.10):
        return DistributionEvent(
            event_id=event_id,
            instrument=instrument,
            record_date=dt.date(2026, 3, 1),
            pay_date=dt.date(2026, 3, 15),
            amount_per_unit=amount,
            source="synthetic-fixture",
            retrieved_at=dt.datetime(2026, 3, 15),
        )

    def test_distribution_credits_cash_per_unit_held(self):
        p = PaperPortfolio("TEST", starting_balance=100.0)
        p.buy(_fill("ABC", OrderSide.BUY, 20, 4.0))
        cash_before = p.cash
        p.apply_distribution(self._event(amount=0.10))
        self.assertAlmostEqual(p.cash, cash_before + 20 * 0.10)

    def test_distribution_cannot_be_applied_twice(self):
        p = PaperPortfolio("TEST", starting_balance=100.0)
        p.buy(_fill("ABC", OrderSide.BUY, 20, 4.0))
        event = self._event()
        p.apply_distribution(event)
        with self.assertRaises(DuplicateDistributionError):
            p.apply_distribution(event)

    def test_distribution_reinvestment_requires_prior_application(self):
        p = PaperPortfolio("TEST", starting_balance=100.0)
        p.buy(_fill("ABC", OrderSide.BUY, 20, 4.0))
        event = self._event()
        reinvest_fill = _fill("ABC", OrderSide.BUY, 2.5, 4.0)
        with self.assertRaises(UnknownDistributionError):
            p.reinvest_distribution(event, reinvest_fill)

    def test_distribution_reinvestment_buys_units_without_double_counting_units(self):
        p = PaperPortfolio("TEST", starting_balance=100.0)
        p.buy(_fill("ABC", OrderSide.BUY, 20, 4.0))
        event = self._event(amount=0.20)  # 20 units * 0.20 = 4.0 cash
        p.apply_distribution(event)
        reinvest_fill = _fill("ABC", OrderSide.BUY, 1.0, 4.0)  # 1 unit at 4.0 = 4.0
        p.reinvest_distribution(event, reinvest_fill)
        self.assertAlmostEqual(p.units_held("ABC"), 21.0)
        snapshot = holdings_asof(p, dt.datetime(2026, 3, 15, 23, 59))
        self.assertAlmostEqual(snapshot["units"]["ABC"], 21.0)

    def test_distribution_cannot_be_reinvested_twice(self):
        p = PaperPortfolio("TEST", starting_balance=100.0)
        p.buy(_fill("ABC", OrderSide.BUY, 20, 4.0))
        event = self._event(amount=0.20)
        p.apply_distribution(event)
        p.reinvest_distribution(event, _fill("ABC", OrderSide.BUY, 1.0, 4.0))
        with self.assertRaises(DuplicateDistributionError):
            p.reinvest_distribution(event, _fill("ABC", OrderSide.BUY, 1.0, 4.0))


class ImmutableHistoryTests(unittest.TestCase):
    def test_transactions_view_is_a_tuple_and_cannot_be_mutated_externally(self):
        p = PaperPortfolio("TEST", starting_balance=100.0)
        p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0))
        txns = p.transactions
        self.assertIsInstance(txns, tuple)
        with self.assertRaises(AttributeError):
            txns.append("not allowed")  # tuples have no append

    def test_correction_is_a_new_adjustment_entry_not_an_edit(self):
        p = PaperPortfolio("TEST", starting_balance=100.0)
        buy_txn = p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0))
        count_before = len(p.transactions)
        p.adjust(buy_txn.txn_id, cash_impact=-1.0, timestamp=dt.datetime(2026, 1, 3), note="fee correction")
        self.assertEqual(len(p.transactions), count_before + 1)
        # the original transaction is unchanged
        original = next(t for t in p.transactions if t.txn_id == buy_txn.txn_id)
        self.assertEqual(original, buy_txn)


class RestrictedPortfolioTests(unittest.TestCase):
    def test_restricted_portfolio_rejects_buy_sell_withdraw(self):
        p = PaperPortfolio("RESERVE-CONTROL", starting_balance=30.0, restricted=True)
        with self.assertRaises(RestrictedPortfolioError):
            p.buy(_fill("ABC", OrderSide.BUY, 1, 1.0))
        with self.assertRaises(RestrictedPortfolioError):
            p.withdraw(1.0, timestamp=dt.datetime(2026, 1, 1))
        # deposits (the initial funding mechanism) remain possible
        p.deposit(5.0, timestamp=dt.datetime(2026, 1, 1))
        self.assertAlmostEqual(p.cash, 35.0)

    def test_restricted_portfolio_rejects_sell_even_with_no_holdings(self):
        p = PaperPortfolio("RESERVE-CONTROL", starting_balance=30.0, restricted=True)
        with self.assertRaises(RestrictedPortfolioError):
            p.sell(_fill("ABC", OrderSide.SELL, 1, 1.0))


class DeterministicReproductionTests(unittest.TestCase):
    def test_identical_operations_produce_identical_state(self):
        def build():
            p = PaperPortfolio("TEST", starting_balance=100.0)
            p.buy(_fill("ABC", OrderSide.BUY, 10, 5.0, fee=1.0, timestamp=dt.datetime(2026, 1, 2)))
            p.sell(_fill("ABC", OrderSide.SELL, 4, 6.0, fee=0.5, timestamp=dt.datetime(2026, 1, 5)))
            return p

        p1, p2 = build(), build()
        self.assertEqual(p1.cash, p2.cash)
        self.assertEqual(p1.units_held("ABC"), p2.units_held("ABC"))
        self.assertEqual(
            [(t.txn_type, t.instrument, t.quantity, t.cash_impact, t.fee) for t in p1.transactions],
            [(t.txn_type, t.instrument, t.quantity, t.cash_impact, t.fee) for t in p2.transactions],
        )


if __name__ == "__main__":
    unittest.main()
