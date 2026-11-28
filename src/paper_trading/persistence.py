"""Durable, append-only local persistence for a PaperPortfolio's
transaction log, as JSON Lines (one Transaction per line).

Design:
- Append-only. There is no "rewrite" or "update" operation anywhere in
  this module -- a correction is just another transaction (typically an
  ADJUSTMENT) appended like any other, exactly as `PaperPortfolio.adjust`
  already models at the ledger level.
- Loading validates every record and reconstructs portfolio state purely
  by replaying it (`PaperPortfolio.from_transactions`), the same
  single-source-of-truth principle the in-memory ledger already uses.
- A malformed record in the middle of the file is corruption and raises.
  A malformed *last* record is treated as a possible interrupted write
  (e.g. the process was killed mid-`write()`) and is reported as a
  warning with the valid records still returned, rather than discarding
  the whole file or silently hiding the problem.

This module performs no network access and makes no assumption about
*where* the caller stores files beyond what it's given -- callers in this
project must point it at the `paper_state/` directory (gitignored; see
`DEFAULT_STATE_DIR`), never at a tracked, public research path. This file
is infrastructure; it does not create or touch any actual portfolio state
on import.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .ledger import PaperPortfolio, PriceType, Transaction, TransactionType

DEFAULT_STATE_DIR = Path(__file__).resolve().parents[2] / "paper_state"

_REQUIRED_FIELDS = (
    "txn_id",
    "txn_type",
    "timestamp",
    "instrument",
    "quantity",
    "cash_impact",
    "fee",
    "price_type_used",
    "estimated",
    "source_reference",
)


class PersistenceError(Exception):
    pass


@dataclass
class LoadResult:
    transactions: List[Transaction]
    warnings: List[str]


@dataclass
class PortfolioLoadResult:
    portfolio: PaperPortfolio
    warnings: List[str]


def _serialise_enum(value):
    return value.value if value is not None else None


def serialise_transaction(txn: Transaction) -> dict:
    return {
        "txn_id": txn.txn_id,
        "txn_type": txn.txn_type.value,
        "timestamp": txn.timestamp.isoformat(),
        "instrument": txn.instrument,
        "quantity": txn.quantity,
        "cash_impact": txn.cash_impact,
        "fee": txn.fee,
        "price_type_used": _serialise_enum(txn.price_type_used),
        "estimated": txn.estimated,
        "source_reference": txn.source_reference,
        "reference_event_id": txn.reference_event_id,
        "reference_txn_id": txn.reference_txn_id,
        "realised_pl": txn.realised_pl,
        "notes": txn.notes,
    }


def _validate_record(record: dict, context: str) -> None:
    if not isinstance(record, dict):
        raise PersistenceError(f"{context}: record is not a JSON object")
    missing = [f for f in _REQUIRED_FIELDS if f not in record]
    if missing:
        raise PersistenceError(f"{context}: missing required fields {missing}")
    try:
        TransactionType(record["txn_type"])
    except ValueError as exc:
        raise PersistenceError(f"{context}: invalid txn_type {record['txn_type']!r}") from exc
    if record["price_type_used"] is not None:
        try:
            PriceType(record["price_type_used"])
        except ValueError as exc:
            raise PersistenceError(f"{context}: invalid price_type_used {record['price_type_used']!r}") from exc
    for numeric_field in ("quantity", "cash_impact", "fee"):
        value = record[numeric_field]
        if not isinstance(value, (int, float)) or value != value or value in (float("inf"), float("-inf")):
            raise PersistenceError(f"{context}: field {numeric_field!r} is not a finite number: {value!r}")
    if record["fee"] < 0:
        raise PersistenceError(f"{context}: fee must be non-negative, got {record['fee']}")


def deserialise_transaction(record: dict, context: str) -> Transaction:
    _validate_record(record, context)
    try:
        timestamp = dt.datetime.fromisoformat(record["timestamp"])
    except (TypeError, ValueError) as exc:
        raise PersistenceError(f"{context}: invalid timestamp {record['timestamp']!r}") from exc
    price_type_used = PriceType(record["price_type_used"]) if record["price_type_used"] is not None else None
    return Transaction(
        txn_id=record["txn_id"],
        txn_type=TransactionType(record["txn_type"]),
        timestamp=timestamp,
        instrument=record["instrument"],
        quantity=record["quantity"],
        cash_impact=record["cash_impact"],
        fee=record["fee"],
        price_type_used=price_type_used,
        estimated=record["estimated"],
        source_reference=record["source_reference"],
        reference_event_id=record.get("reference_event_id"),
        reference_txn_id=record.get("reference_txn_id"),
        realised_pl=record.get("realised_pl"),
        notes=record.get("notes", ""),
    )


def append_transaction(path: Path, txn: Transaction) -> None:
    """Appends one transaction as a single JSON line. Opens, writes,
    flushes and fsyncs on every call rather than buffering, so a crash
    immediately after this call leaves at most this one line at risk, and
    never corrupts any earlier line."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(serialise_transaction(txn), sort_keys=True)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


def append_transactions(path: Path, transactions) -> None:
    for txn in transactions:
        append_transaction(path, txn)


def load_transactions(path: Path) -> LoadResult:
    """Reads and validates every line. A malformed line before the last
    line is treated as corruption and raises `PersistenceError`
    immediately (no transactions are silently discarded in that case --
    the caller gets nothing rather than a silently-incomplete history). A
    malformed *last* line is treated as a possible interrupted write: it
    is reported in `warnings` and excluded, while every earlier,
    successfully parsed transaction is still returned."""
    path = Path(path)
    if not path.exists():
        return LoadResult(transactions=[], warnings=[])
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    lines = [(i, line) for i, line in enumerate(raw_lines) if line.strip() != ""]
    transactions: List[Transaction] = []
    warnings: List[str] = []
    for position, (line_no, line) in enumerate(lines):
        is_last = position == len(lines) - 1
        context = f"{path}:{line_no + 1}"
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            # Truncated/non-JSON bytes are the signature of a write that
            # was interrupted mid-flush -- lenient, but ONLY for the very
            # last line; the same failure earlier in the file is real
            # corruption, not an interruption artifact.
            if is_last:
                warnings.append(
                    f"Trailing record at {context} is not valid JSON ({exc}); treated as a "
                    "possible interrupted write and excluded. All earlier records were loaded "
                    "normally."
                )
                continue
            raise PersistenceError(f"Corrupt (non-JSON) record at {context}: {exc}") from exc
        # A record that parses as JSON but fails validation (missing
        # field, invalid enum value, non-finite number, negative fee) is a
        # different failure mode from a truncated write -- it is a fully
        # formed but wrong record, so it always raises, regardless of its
        # position in the file.
        txn = deserialise_transaction(record, context)
        transactions.append(txn)
    return LoadResult(transactions=transactions, warnings=warnings)


def reconstruct_portfolio(path: Path, portfolio_id: str, restricted: bool) -> PortfolioLoadResult:
    """Loads the JSONL log and reconstructs a `PaperPortfolio` from it,
    carrying forward any load warnings (e.g. a trailing interrupted
    write) for the caller to surface rather than discard."""
    result = load_transactions(path)
    portfolio = PaperPortfolio.from_transactions(portfolio_id, restricted, result.transactions)
    return PortfolioLoadResult(portfolio=portfolio, warnings=result.warnings)
