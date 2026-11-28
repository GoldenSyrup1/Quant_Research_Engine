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

Execution-model limitation (PAPER-002 section 5): every fill in this
module is simulated as a *full-quantity execution at the top of book* --
the order's entire requested quantity fills at a single observed bid/ask
(or estimated-spread) price. This is a simplified assumption suitable only
for small, infrequent paper-trading experiments in liquid, slow-moving
ETFs, where order size relative to visible liquidity is immaterial. It is
**not** a market-impact model, **not** a partial-fill model, and **not** a
queue-position model -- a real order of any meaningful size relative to
displayed depth would not actually fill this way. This system must not be
extended to microstructure-sensitive or size-sensitive strategies without
building a materially different execution model first.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from .ledger import Fill, OrderSide, OrderType, PriceObservation, PriceType
from .ledger import _finite  # shared finiteness check, kept in one place


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
    expiry: Optional[dt.datetime] = None

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Order quantity must be positive")
        if not isinstance(self.timestamp, dt.datetime):
            raise ValueError(f"Order timestamp is invalid: {self.timestamp!r}")
        if self.expiry is not None:
            if not isinstance(self.expiry, dt.datetime):
                raise ValueError(f"Order expiry is invalid: {self.expiry!r}")
            if self.expiry <= self.timestamp:
                raise ValueError("Order expiry must be after its timestamp")
        if self.order_type is OrderType.LIMIT:
            if self.limit_price is None:
                raise ValueError("A LIMIT order requires limit_price")
            if self.limit_price <= 0 or not _finite(self.limit_price):
                raise ValueError("limit_price must be a positive, finite number")


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


# The date these promotional/current brokerage terms were last verified
# against the vendor's own stated terms. Neither schedule below claims to
# know what fee, if any, applied *before* this date -- a promotion is a
# current, not necessarily historical, fact, and backdating it to an
# arbitrary early date would assert something never verified. Any fee
# lookup for a date before this is rejected by `fee_for` (no rule covers
# it) rather than silently assumed to be the current promotional rate.
TERMS_VERIFIED_AS_OF = dt.date(2026, 11, 28)


def betashares_direct_schedule() -> BrokerageSchedule:
    """$0 brokerage, as currently advertised by Betashares Direct, subject
    to its applicable terms. This is a scenario assumption, not a platform
    selection, and is explicitly NOT assumed to be permanent: it is
    modelled only from `TERMS_VERIFIED_AS_OF` forward, with no stated end
    date because none is currently known -- that absence should be
    revisited, not treated as a guarantee of permanence."""
    return BrokerageSchedule(
        name="Betashares Direct (modelled, $0, subject to applicable terms, unverified for permanence)",
        rules=(
            BrokerageRule(
                effective_from=TERMS_VERIFIED_AS_OF,
                effective_to=None,
                fee_fn=lambda trade_value: 0.0,
                description="$0 brokerage (verified current as of TERMS_VERIFIED_AS_OF only)",
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
    """$0 promotional brokerage from `TERMS_VERIFIED_AS_OF` until
    2027-03-31 (CommSec Pocket's own stated promotion end date), then the
    standard A$2 flat fee for trades up to A$1,000. The promotion is
    explicitly NOT backdated to any date before it was actually verified --
    a historical simulation for an earlier date must fail rather than
    silently assume this promotional rate applied in the past too."""
    promotion_end = dt.date(2027, 3, 31)
    return BrokerageSchedule(
        name="CommSec Pocket (modelled)",
        rules=(
            BrokerageRule(
                effective_from=TERMS_VERIFIED_AS_OF,
                effective_to=promotion_end,
                fee_fn=lambda trade_value: 0.0,
                description="$0 promotion until 2027-03-31 (verified current as of TERMS_VERIFIED_AS_OF only)",
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
    max_quote_age: Optional[dt.timedelta] = None,
) -> Fill:
    """Simulate a MARKET order's execution.

    For a BUY, uses the latest available ASK observation at/before the
    order timestamp; for a SELL, the latest BID. If neither is available,
    `spread_bps` must be supplied (a conservative assumed half-spread,
    in basis points, applied around the latest CLOSE/LAST observation),
    and the resulting Fill is marked `estimated=True`. NAV observations
    are never used to produce a fill.

    `max_quote_age`, if supplied, rejects a bid/ask observation older than
    that, relative to the order timestamp, rather than silently filling
    against an arbitrarily stale quote. An observation exactly `max_quote_age`
    old is still accepted (the boundary is inclusive); only strictly older
    observations are rejected.
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
        age = order.timestamp - quote.timestamp
        if max_quote_age is not None and age > max_quote_age:
            raise ExecutionError(
                f"{quote_type.value} quote for {order.instrument} is stale: observed at "
                f"{quote.timestamp}, order at {order.timestamp} (age {age}), exceeds "
                f"max_quote_age {max_quote_age}"
            )
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


def check_limit_touch(
    order: Order,
    price_observations: Sequence[PriceObservation],
    allow_last_close_fallback: bool = False,
) -> bool:
    """Reports only whether recorded price data touched/crossed the
    order's limit price *after* the order was placed and *before* its
    expiry (if any). This is informational only -- it never produces or
    implies a fill, and a touch does not account for queue priority, so a
    real order could easily have gone unfilled even on a genuine touch.

    By default this respects the relevant market side strictly: a BUY
    limit is only assessed against ASK-side observations (what a buyer
    would actually have to pay), and a SELL limit only against BID-side
    observations (what a seller would actually receive). Blending in
    LAST/CLOSE prints is a different, trade-through-style assumption; it
    is never applied silently -- set `allow_last_close_fallback=True`
    explicitly to opt into it, and treat its result as a looser, less
    conservative signal than the default BID/ASK-only check.
    """
    if order.order_type is not OrderType.LIMIT:
        raise ExecutionError("check_limit_touch is only meaningful for LIMIT orders")
    window_start = order.timestamp
    window_end = order.expiry if order.expiry is not None else dt.datetime.max
    side_price_type = PriceType.ASK if order.side is OrderSide.BUY else PriceType.BID
    eligible_types = (side_price_type, PriceType.LAST, PriceType.CLOSE) if allow_last_close_fallback else (side_price_type,)
    relevant = [
        o for o in price_observations
        if o.instrument == order.instrument
        and o.price_type in eligible_types
        and window_start < o.timestamp <= window_end
    ]
    if order.side is OrderSide.BUY:
        return any(o.price <= order.limit_price for o in relevant)
    return any(o.price >= order.limit_price for o in relevant)
