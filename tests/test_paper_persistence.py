import datetime as dt
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from src.paper_trading.ledger import Fill, OrderSide, PaperPortfolio, PriceType
from src.paper_trading.persistence import (
    PersistenceError,
    append_transaction,
    load_transactions,
    reconstruct_portfolio,
    serialise_transaction,
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
        timestamp=timestamp or dt.datetime(2026, 11, 28),
        source_reference="synthetic-fixture",
    )


class PersistenceRoundTripTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)
        self.path = self.tmp_dir / "TEST.jsonl"

    def _build_and_persist(self):
        portfolio = PaperPortfolio("TEST", starting_balance=100.0)
        for txn in portfolio.transactions:
            append_transaction(self.path, txn)
        buy_txn = portfolio.buy(_fill("ABC", OrderSide.BUY, 10, 5.0, fee=1.0, timestamp=dt.datetime(2026, 11, 28, 10)))
        append_transaction(self.path, buy_txn)
        sell_txn = portfolio.sell(_fill("ABC", OrderSide.SELL, 4, 6.0, fee=0.5, timestamp=dt.datetime(2026, 12, 1)))
        append_transaction(self.path, sell_txn)
        return portfolio

    def test_reconstructed_portfolio_matches_original_state(self):
        original = self._build_and_persist()
        result = reconstruct_portfolio(self.path, "TEST", restricted=False)
        self.assertEqual(result.warnings, [])
        reconstructed = result.portfolio
        self.assertAlmostEqual(reconstructed.cash, original.cash)
        self.assertAlmostEqual(reconstructed.units_held("ABC"), original.units_held("ABC"))
        self.assertAlmostEqual(reconstructed.average_cost("ABC"), original.average_cost("ABC"))
        self.assertEqual(len(reconstructed.transactions), len(original.transactions))

    def test_reconstruction_is_deterministic_across_reloads(self):
        self._build_and_persist()
        first = reconstruct_portfolio(self.path, "TEST", restricted=False).portfolio
        second = reconstruct_portfolio(self.path, "TEST", restricted=False).portfolio
        self.assertEqual(first.cash, second.cash)
        self.assertEqual(first.units_held("ABC"), second.units_held("ABC"))

    def test_loading_a_missing_file_returns_empty_not_an_error(self):
        result = load_transactions(self.tmp_dir / "does_not_exist.jsonl")
        self.assertEqual(result.transactions, [])
        self.assertEqual(result.warnings, [])

    def test_append_only_never_rewrites_earlier_lines(self):
        original = self._build_and_persist()
        before = self.path.read_text(encoding="utf-8")
        more = original.deposit(5.0, timestamp=dt.datetime(2026, 12, 2))
        append_transaction(self.path, more)
        after = self.path.read_text(encoding="utf-8")
        self.assertTrue(after.startswith(before))


class CorruptionDetectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)
        self.path = self.tmp_dir / "TEST.jsonl"

    def test_malformed_middle_line_raises_and_discards_nothing_silently(self):
        portfolio = PaperPortfolio("TEST", starting_balance=100.0)
        deposit_txn = portfolio.transactions[0]
        append_transaction(self.path, deposit_txn)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write("{not valid json\n")
        buy_txn = portfolio.buy(_fill("ABC", OrderSide.BUY, 10, 5.0))
        append_transaction(self.path, buy_txn)
        with self.assertRaises(PersistenceError):
            load_transactions(self.path)

    def test_malformed_trailing_line_is_a_warning_not_a_fatal_error(self):
        portfolio = PaperPortfolio("TEST", starting_balance=100.0)
        deposit_txn = portfolio.transactions[0]
        append_transaction(self.path, deposit_txn)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write('{"txn_id": "TEST-buy-000002", "txn_type": "buy", "timestamp"')  # simulated interrupted write
        result = load_transactions(self.path)
        self.assertEqual(len(result.transactions), 1)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("interrupted write", result.warnings[0])

    def test_missing_required_field_is_rejected(self):
        record = serialise_transaction(PaperPortfolio("TEST", starting_balance=10.0).transactions[0])
        del record["cash_impact"]
        self.path.write_text(json.dumps(record) + "\n", encoding="utf-8")
        with self.assertRaises(PersistenceError):
            load_transactions(self.path)

    def test_invalid_txn_type_is_rejected(self):
        record = serialise_transaction(PaperPortfolio("TEST", starting_balance=10.0).transactions[0])
        record["txn_type"] = "not_a_real_type"
        self.path.write_text(json.dumps(record) + "\n", encoding="utf-8")
        with self.assertRaises(PersistenceError):
            load_transactions(self.path)

    def test_non_finite_quantity_is_rejected(self):
        record = serialise_transaction(PaperPortfolio("TEST", starting_balance=10.0).transactions[0])
        record["quantity"] = float("nan")
        self.path.write_text(json.dumps(record) + "\n", encoding="utf-8")
        with self.assertRaises(PersistenceError):
            load_transactions(self.path)

    def test_negative_fee_is_rejected(self):
        record = serialise_transaction(PaperPortfolio("TEST", starting_balance=10.0).transactions[0])
        record["fee"] = -1.0
        self.path.write_text(json.dumps(record) + "\n", encoding="utf-8")
        with self.assertRaises(PersistenceError):
            load_transactions(self.path)


class RestrictedPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)
        self.path = self.tmp_dir / "RESERVE-CONTROL.jsonl"

    def test_restricted_flag_is_preserved_across_reload(self):
        portfolio = PaperPortfolio("RESERVE-CONTROL", starting_balance=30.0, restricted=True)
        for txn in portfolio.transactions:
            append_transaction(self.path, txn)
        result = reconstruct_portfolio(self.path, "RESERVE-CONTROL", restricted=True)
        self.assertTrue(result.portfolio.restricted)
        self.assertAlmostEqual(result.portfolio.cash, 30.0)


if __name__ == "__main__":
    unittest.main()
