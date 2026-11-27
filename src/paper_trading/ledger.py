"""Core paper-trading data model: price observations, an immutable
transaction ledger, and a portfolio that applies simulated trades,
deposits, withdrawals and distributions to that ledger.

Nothing here executes a real order. A `Fill` is always the output of a
simulation function (see `execution.py`) or an explicit, manually recorded
confirmation (for limit orders) -- never inferred automatically from a
price merely touching a limit.
"""
from __future__ import annotations

import datetime as dt
import enum
from dataclasses import dataclass, field, replace
from typing import Optional


class PriceType(enum.Enum):
    CLOSE = "close"
    LAST = "last"
    BID = "bid"
    ASK = "ask"
    NAV = "nav"


class TransactionType(enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    BUY = "buy"
    SELL = "sell"
    DISTRIBUTION = "distribution"
    DISTRIBUTION_REINVEST = "distribution_reinvest"
    ADJUSTMENT = "adjustment"


class OrderSide(enum.Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(enum.Enum):
    MARKET = "market"
    LIMIT = "limit"


class PaperTradingError(Exception):
    """Base class for all paper-trading simulation errors."""


class InsufficientCashError(PaperTradingError):
    pass


class InsufficientHoldingsError(PaperTradingError):
    """Raised on any attempt to sell more units than are held (no shorting)."""


class RestrictedPortfolioError(PaperTradingError):
    """Raised on any attempt to buy, sell or withdraw from a restricted
    (e.g. protected-reserve) portfolio."""


class DuplicateDistributionError(PaperTradingError):
    pass


class UnknownDistributionError(PaperTradingError):
    pass


@dataclass(frozen=True)
class PriceObservation:
    """A single, provenanced price or distribution-input observation.

    `price_type` records whether this is a NAV, close, last-traded, bid or
    ask observation. Execution code (see `execution.py`) refuses to fill a
    simulated trade from a NAV observation -- NAV is a valuation concept,
    not an executable ASX price.
    """

    instrument: str
    date: dt.date
    timestamp: dt.datetime
    price: float
    price_type: PriceType
    source: str
    retrieved_at: dt.datetime
    data_vintage: str
    source_reference: Optional[str] = None
    transformations: tuple = ()

    def __post_init__(self):
        if self.price <= 0 or not _finite(self.price):
            raise ValueError(f"Price observation for {self.instrument} must be a positive, finite number")


@dataclass(frozen=True)
class DistributionEvent:
    """A per-unit distribution (dividend/distribution) event."""

    event_id: str
    instrument: str
    record_date: dt.date
    pay_date: dt.date
    amount_per_unit: float
    source: str
    retrieved_at: dt.datetime

    def __post_init__(self):
        if self.amount_per_unit <= 0 or not _finite(self.amount_per_unit):
            raise ValueError(f"Distribution amount for {self.event_id} must be a positive, finite number")


@dataclass(frozen=True)
class Fill:
    """The output of a simulated (or manually confirmed) execution."""

    instrument: str
    side: OrderSide
    quantity: float
    fill_price: float
    price_type_used: PriceType
    estimated: bool
    fee: float
    timestamp: dt.datetime
    source_reference: Optional[str] = None
    notes: str = ""

    @property
    def gross_value(self) -> float:
        return self.quantity * self.fill_price

    @property
    def net_cash_impact(self) -> float:
        """Cash change from the portfolio's perspective: negative for a
        buy (cash leaves, plus fee), positive for a sell (cash arrives,
        minus fee)."""
        if self.side is OrderSide.BUY:
            return -(self.gross_value + self.fee)
        return self.gross_value - self.fee


@dataclass(frozen=True)
class Transaction:
    """One immutable, append-only ledger entry. Corrections are new
    `ADJUSTMENT` entries referencing `reference_txn_id`, never edits."""

    txn_id: str
    txn_type: TransactionType
    timestamp: dt.datetime
    instrument: Optional[str]
    quantity: float
    cash_impact: float
    fee: float
    price_type_used: Optional[PriceType]
    estimated: bool
    source_reference: Optional[str]
    reference_event_id: Optional[str] = None
    reference_txn_id: Optional[str] = None
    realised_pl: Optional[float] = None
    notes: str = ""


def _finite(x: float) -> bool:
    return x == x and x not in (float("inf"), float("-inf"))


@dataclass
class _Lot:
    units: float
    average_cost: float


class PaperPortfolio:
    """A single paper portfolio: cash balance, holdings, and an
    append-only transaction log. All monetary state is derived only from
    replaying `transactions`, so the log is the single source of truth.
    """

    def __init__(self, portfolio_id: str, starting_balance: float, restricted: bool = False):
        if starting_balance < 0 or not _finite(starting_balance):
            raise ValueError("starting_balance must be a non-negative, finite number")
        self.portfolio_id = portfolio_id
        self.restricted = restricted
        self.cash: float = 0.0
        self.holdings: dict[str, _Lot] = {}
        self._transactions: list[Transaction] = []
        self._applied_distribution_ids: set[str] = set()
        self._reinvested_distribution_ids: set[str] = set()
        self._next_txn_seq = 0
        if starting_balance > 0:
            self.deposit(starting_balance, timestamp=_epoch(), note="initial funding")

    # -- read-only views -------------------------------------------------

    @property
    def transactions(self) -> tuple:
        return tuple(self._transactions)

    def units_held(self, instrument: str) -> float:
        lot = self.holdings.get(instrument)
        return lot.units if lot else 0.0

    def average_cost(self, instrument: str) -> Optional[float]:
        lot = self.holdings.get(instrument)
        return lot.average_cost if lot else None

    # -- internal -----------------------------------------------------------

    def _next_id(self, prefix: str) -> str:
        self._next_txn_seq += 1
        return f"{self.portfolio_id}-{prefix}-{self._next_txn_seq:06d}"

    def _append(self, **kwargs) -> Transaction:
        txn = Transaction(txn_id=self._next_id(kwargs["txn_type"].value), **kwargs)
        self._transactions.append(txn)
        return txn

    def _require_unrestricted(self):
        if self.restricted:
            raise RestrictedPortfolioError(
                f"Portfolio {self.portfolio_id} is restricted and must never be allocated, "
                "withdrawn from, or used to cover losses or expenditure."
            )

    # -- cash movements ----------------------------------------------------

    def deposit(self, amount: float, timestamp: dt.datetime, note: str = "") -> Transaction:
        if amount <= 0 or not _finite(amount):
            raise ValueError("deposit amount must be a positive, finite number")
        self.cash += amount
        return self._append(
            txn_type=TransactionType.DEPOSIT,
            timestamp=timestamp,
            instrument=None,
            quantity=0.0,
            cash_impact=amount,
            fee=0.0,
            price_type_used=None,
            estimated=False,
            source_reference=None,
            notes=note,
        )

    def withdraw(self, amount: float, timestamp: dt.datetime, note: str = "") -> Transaction:
        self._require_unrestricted()
        if amount <= 0 or not _finite(amount):
            raise ValueError("withdrawal amount must be a positive, finite number")
        if amount > self.cash:
            raise InsufficientCashError(
                f"Cannot withdraw {amount} from portfolio {self.portfolio_id} with cash balance {self.cash}"
            )
        self.cash -= amount
        return self._append(
            txn_type=TransactionType.WITHDRAWAL,
            timestamp=timestamp,
            instrument=None,
            quantity=0.0,
            cash_impact=-amount,
            fee=0.0,
            price_type_used=None,
            estimated=False,
            source_reference=None,
            notes=note,
        )

    # -- trades --------------------------------------------------------------

    def buy(self, fill: Fill, note: str = "") -> Transaction:
        self._require_unrestricted()
        if fill.side is not OrderSide.BUY:
            raise ValueError("buy() requires a Fill with side=BUY")
        required_cash = fill.gross_value + fill.fee
        if required_cash > self.cash + 1e-9:
            raise InsufficientCashError(
                f"Buying {fill.quantity} {fill.instrument} at {fill.fill_price} "
                f"(+fee {fill.fee}) costs {required_cash}, exceeding cash balance {self.cash} "
                f"in portfolio {self.portfolio_id}"
            )
        self.cash += fill.net_cash_impact
        lot = self.holdings.get(fill.instrument, _Lot(units=0.0, average_cost=0.0))
        new_units = lot.units + fill.quantity
        new_cost_basis = lot.units * lot.average_cost + fill.gross_value + fill.fee
        lot = _Lot(units=new_units, average_cost=new_cost_basis / new_units if new_units else 0.0)
        self.holdings[fill.instrument] = lot
        return self._append(
            txn_type=TransactionType.BUY,
            timestamp=fill.timestamp,
            instrument=fill.instrument,
            quantity=fill.quantity,
            cash_impact=fill.net_cash_impact,
            fee=fill.fee,
            price_type_used=fill.price_type_used,
            estimated=fill.estimated,
            source_reference=fill.source_reference,
            notes=note or fill.notes,
        )

    def sell(self, fill: Fill, note: str = "") -> Transaction:
        self._require_unrestricted()
        if fill.side is not OrderSide.SELL:
            raise ValueError("sell() requires a Fill with side=SELL")
        lot = self.holdings.get(fill.instrument)
        held = lot.units if lot else 0.0
        if fill.quantity > held + 1e-9:
            raise InsufficientHoldingsError(
                f"Cannot sell {fill.quantity} {fill.instrument}; only {held} held "
                f"in portfolio {self.portfolio_id} (no short positions)"
            )
        cost_basis_sold = fill.quantity * lot.average_cost
        proceeds_net_of_fee = fill.gross_value - fill.fee
        realised_pl = proceeds_net_of_fee - cost_basis_sold
        remaining_units = held - fill.quantity
        if remaining_units <= 1e-12:
            self.holdings.pop(fill.instrument, None)
        else:
            self.holdings[fill.instrument] = _Lot(units=remaining_units, average_cost=lot.average_cost)
        self.cash += fill.net_cash_impact
        return self._append(
            txn_type=TransactionType.SELL,
            timestamp=fill.timestamp,
            instrument=fill.instrument,
            quantity=fill.quantity,
            cash_impact=fill.net_cash_impact,
            fee=fill.fee,
            price_type_used=fill.price_type_used,
            estimated=fill.estimated,
            source_reference=fill.source_reference,
            realised_pl=realised_pl,
            notes=note or fill.notes,
        )

    # -- distributions -------------------------------------------------------

    def apply_distribution(self, event: DistributionEvent, units_at_record_date: Optional[float] = None) -> Transaction:
        if event.event_id in self._applied_distribution_ids:
            raise DuplicateDistributionError(f"Distribution {event.event_id} already applied")
        units = self.units_held(event.instrument) if units_at_record_date is None else units_at_record_date
        amount = units * event.amount_per_unit
        self._applied_distribution_ids.add(event.event_id)
        if amount <= 0:
            # No units held at the record date: still record the event as
            # applied (to make double-application impossible later) but
            # with a zero cash impact.
            return self._append(
                txn_type=TransactionType.DISTRIBUTION,
                timestamp=dt.datetime.combine(event.pay_date, dt.time()),
                instrument=event.instrument,
                quantity=0.0,
                cash_impact=0.0,
                fee=0.0,
                price_type_used=None,
                estimated=False,
                source_reference=event.source,
                reference_event_id=event.event_id,
                notes="no units held at record date",
            )
        self.cash += amount
        return self._append(
            txn_type=TransactionType.DISTRIBUTION,
            timestamp=dt.datetime.combine(event.pay_date, dt.time()),
            instrument=event.instrument,
            quantity=units,
            cash_impact=amount,
            fee=0.0,
            price_type_used=None,
            estimated=False,
            source_reference=event.source,
            reference_event_id=event.event_id,
        )

    def reinvest_distribution(self, event: DistributionEvent, fill: Fill, note: str = "") -> Transaction:
        self._require_unrestricted()
        if event.event_id not in self._applied_distribution_ids:
            raise UnknownDistributionError(
                f"Distribution {event.event_id} must be applied via apply_distribution() before it can be reinvested"
            )
        if event.event_id in self._reinvested_distribution_ids:
            raise DuplicateDistributionError(f"Distribution {event.event_id} already reinvested")
        if fill.side is not OrderSide.BUY:
            raise ValueError("reinvest_distribution() requires a Fill with side=BUY")
        buy_txn = self.buy(fill, note=note or f"reinvestment of {event.event_id}")
        self._reinvested_distribution_ids.add(event.event_id)
        # Record the reinvestment as its own linked ledger entry so the
        # distribution -> reinvestment chain is auditable without having
        # mutated the original BUY transaction.
        return self._append(
            txn_type=TransactionType.DISTRIBUTION_REINVEST,
            timestamp=fill.timestamp,
            instrument=fill.instrument,
            quantity=fill.quantity,
            cash_impact=0.0,
            fee=0.0,
            price_type_used=fill.price_type_used,
            estimated=fill.estimated,
            source_reference=fill.source_reference,
            reference_event_id=event.event_id,
            reference_txn_id=buy_txn.txn_id,
            notes=note,
        )

    # -- adjustments -----------------------------------------------------

    def adjust(self, reference_txn_id: str, cash_impact: float, timestamp: dt.datetime, note: str) -> Transaction:
        """Record a correction as a brand-new entry. The original
        transaction is never edited or removed."""
        if not any(t.txn_id == reference_txn_id for t in self._transactions):
            raise ValueError(f"Unknown reference_txn_id {reference_txn_id}")
        self.cash += cash_impact
        return self._append(
            txn_type=TransactionType.ADJUSTMENT,
            timestamp=timestamp,
            instrument=None,
            quantity=0.0,
            cash_impact=cash_impact,
            fee=0.0,
            price_type_used=None,
            estimated=False,
            source_reference=None,
            reference_txn_id=reference_txn_id,
            notes=note,
        )

    # -- limit orders: never auto-filled -------------------------------------

    def manually_confirm_limit_fill(self, fill: Fill, note: str = "") -> Transaction:
        """The only way a LIMIT order can become a transaction. There is
        deliberately no automatic path from "price touched the limit" to a
        recorded fill -- see `execution.check_limit_touch`."""
        if fill.side is OrderSide.BUY:
            return self.buy(fill, note=note or "manually confirmed limit buy")
        return self.sell(fill, note=note or "manually confirmed limit sell")


def _epoch() -> dt.datetime:
    return dt.datetime(1970, 1, 1)


def holdings_asof(portfolio: PaperPortfolio, as_of: dt.datetime) -> dict:
    """Reconstruct cash and per-instrument unit holdings as of a given
    timestamp, purely by replaying the immutable transaction log up to
    that point. Does not mutate `portfolio`."""
    cash = 0.0
    units: dict[str, float] = {}
    for txn in portfolio.transactions:
        if txn.timestamp > as_of:
            continue
        cash += txn.cash_impact
        # DISTRIBUTION_REINVEST is an audit-trail annotation linking a
        # distribution to the BUY transaction it funded; the unit increase
        # itself is already fully recorded by that paired BUY, so it must
        # not be counted again here.
        if txn.instrument is not None and txn.txn_type in (TransactionType.BUY, TransactionType.SELL):
            sign = -1.0 if txn.txn_type is TransactionType.SELL else 1.0
            units[txn.instrument] = units.get(txn.instrument, 0.0) + sign * txn.quantity
    return {"cash": cash, "units": units}
