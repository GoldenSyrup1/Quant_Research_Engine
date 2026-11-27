"""Simulated order execution: turns an order + price observations into a
`Fill`, applying a configurable, effective-dated brokerage schedule.

Design rules enforced here, not just documented:
- A simulated fill is never derived from a NAV-type price observation.
  NAV is a valuation concept; it is not an executable ASX price.
- A LIMIT order is never auto-filled by this module. `simulate_market_fill`
  refuses any order whose `order_type` is not MARKET. The only path from a
  limit order to a recorded transaction is
  `PaperPortfolio.manually_confirm_limit_fill`, which requires the caller
  to supply the fill explicitly.
- When no bid/ask observation is available, a fill can still be produced
  from a configurable spread assumption around a CLOSE/LAST price, but the
  resulting Fill is always marked `estimated=True`.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from .ledger import Fill, OrderSide, OrderType, PriceObservation, PriceType


class ExecutionError(Exception):
    pass


@dataclass(frozen=True)
class Order:
    order_id: str
    instrument: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    timestamp: dt.datetime
    limit_price: Optional[float] = None

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Order quantity must be positive")
        if self.order_type is OrderType.LIMIT and self.limit_price is None:
            raise ValueError("A LIMIT order requires limit_price")


@dataclass(frozen=True)
class BrokerageRule:
    effective_from: dt.date
    fee_fn: Callable[[float], float]
    description: str
    effective_to: Optional[dt.date] = None

    def covers(self, as_of: dt.date) -> bool:
        if as_of < self.effective_from:
            return False
        if self.effective_to is not None and as_of > self.effective_to:
            return False
        return True


@dataclass(frozen=True)
class BrokerageSchedule:
    name: str
    rules: tuple

    def fee_for(self, trade_value: float, as_of: dt.date) -> float:
        matching = [r for r in self.rules if r.covers(as_of)]
        if not matching:
            raise ExecutionError(
                f"Brokerage schedule '{self.name}' has no rule covering {as_of}; "
                "configure an explicit rule rather than assuming a fee."
            )
        if len(matching) > 1:
            raise ExecutionError(
                f"Brokerage schedule '{self.name}' has overlapping rules covering {as_of}: "
                f"{[r.description for r in matching]}"
            )
        return matching[0].fee_fn(trade_value)


def betashares_direct_schedule() -> BrokerageSchedule:
    """$0 brokerage, as currently advertised by Betashares Direct, subject
    to its applicable terms. Modelled from a nominal epoch date since no
    end date is currently known; this is a scenario assumption, not a
    platform selection."""
    return BrokerageSchedule(
        name="Betashares Direct (modelled, $0, subject to applicable terms)",
        rules=(
            BrokerageRule(
                effective_from=dt.date(2000, 1, 1),
                effective_to=None,
                fee_fn=lambda trade_value: 0.0,
                description="$0 brokerage",
            ),
        ),
    )


def _commsec_pocket_standard_fee(trade_value: float) -> float:
    if trade_value <= 1000:
        return 2.0
    raise ExecutionError(
        "CommSec Pocket's standard A$2 brokerage is only modelled for trades up to A$1,000; "
        "no public fee schedule for larger trades was found, so none is assumed here."
    )


def commsec_pocket_schedule() -> BrokerageSchedule:
    """$0 promotional brokerage until 2027-03-31, then the standard A$2
    flat fee for trades up to A$1,000 (CommSec Pocket's own stated
    promotion end date)."""
    promotion_end = dt.date(2027, 3, 31)
    return BrokerageSchedule(
        name="CommSec Pocket (modelled)",
        rules=(
            BrokerageRule(
                effective_from=dt.date(2000, 1, 1),
                effective_to=promotion_end,
                fee_fn=lambda trade_value: 0.0,
                description="$0 promotion until 2027-03-31",
            ),
            BrokerageRule(
                effective_from=promotion_end + dt.timedelta(days=1),
                effective_to=None,
                fee_fn=_commsec_pocket_standard_fee,
                description="standard A$2 brokerage for trades up to A$1,000",
            ),
        ),
    )


def _latest(observations: Sequence[PriceObservation], instrument: str, price_type: PriceType, as_of: dt.datetime):
    candidates = [
        o for o in observations
        if o.instrument == instrument and o.price_type is price_type and o.timestamp <= as_of
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda o: o.timestamp)


def simulate_market_fill(
    order: Order,
    price_observations: Sequence[PriceObservation],
    brokerage_schedule: BrokerageSchedule,
    spread_bps: Optional[float] = None,
) -> Fill:
    """Simulate a MARKET order's execution.

    For a BUY, uses the latest available ASK observation at/before the
    order timestamp; for a SELL, the latest BID. If neither is available,
    `spread_bps` must be supplied (a conservative assumed half-spread,
    in basis points, applied around the latest CLOSE/LAST observation),
    and the resulting Fill is marked `estimated=True`. NAV observations
    are never used to produce a fill.
    """
    if order.order_type is not OrderType.MARKET:
        raise ExecutionError(
            "simulate_market_fill only fills MARKET orders. A LIMIT order must never be "
            "auto-filled merely because a recorded price touched its limit -- use "
            "PaperPortfolio.manually_confirm_limit_fill with an explicitly supplied Fill."
        )

    quote_type = PriceType.ASK if order.side is OrderSide.BUY else PriceType.BID
    quote = _latest(price_observations, order.instrument, quote_type, order.timestamp)
    estimated = False
    if quote is not None:
        fill_price = quote.price
        price_type_used = quote_type
        source_reference = quote.source_reference or quote.source
    else:
        reference = _latest(price_observations, order.instrument, PriceType.CLOSE, order.timestamp) or \
            _latest(price_observations, order.instrument, PriceType.LAST, order.timestamp)
        if reference is None:
            nav_only = _latest(price_observations, order.instrument, PriceType.NAV, order.timestamp)
            if nav_only is not None:
                raise ExecutionError(
                    f"Only a NAV observation is available for {order.instrument} at {order.timestamp}; "
                    "NAV must never be treated as an executable ASX price. Supply a bid/ask or "
                    "close/last observation instead."
                )
            raise ExecutionError(
                f"No usable price observation for {order.instrument} at or before {order.timestamp}"
            )
        if spread_bps is None:
            raise ExecutionError(
                f"No bid/ask observation for {order.instrument} at {order.timestamp}; "
                "a spread_bps assumption must be supplied to estimate a fill price."
            )
        half_spread = reference.price * (spread_bps / 10_000.0) / 2.0
        fill_price = reference.price + half_spread if order.side is OrderSide.BUY else reference.price - half_spread
        price_type_used = reference.price_type
        source_reference = reference.source_reference or reference.source
        estimated = True

    trade_value = order.quantity * fill_price
    fee = brokerage_schedule.fee_for(trade_value, order.timestamp.date())
    return Fill(
        instrument=order.instrument,
        side=order.side,
        quantity=order.quantity,
        fill_price=fill_price,
        price_type_used=price_type_used,
        estimated=estimated,
        fee=fee,
        timestamp=order.timestamp,
        source_reference=source_reference,
        notes=f"simulated market fill via {brokerage_schedule.name}" + (" (estimated spread)" if estimated else ""),
    )


def check_limit_touch(order: Order, price_observations: Sequence[PriceObservation]) -> bool:
    """Reports only whether recorded price data touched/crossed the
    order's limit price. This is informational only -- it never produces
    or implies a fill. A touch does not account for queue priority, so a
    real order could easily have gone unfilled even on a genuine touch."""
    if order.order_type is not OrderType.LIMIT:
        raise ExecutionError("check_limit_touch is only meaningful for LIMIT orders")
    relevant = [
        o for o in price_observations
        if o.instrument == order.instrument
        and o.price_type in (PriceType.BID, PriceType.ASK, PriceType.LAST, PriceType.CLOSE)
        and o.timestamp <= order.timestamp
    ]
    if order.side is OrderSide.BUY:
        return any(o.price <= order.limit_price for o in relevant)
    return any(o.price >= order.limit_price for o in relevant)
