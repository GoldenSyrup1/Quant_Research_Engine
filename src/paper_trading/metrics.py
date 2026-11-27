"""Valuation and performance statistics for a PaperPortfolio.

Reuses `src.metrics.max_drawdown` rather than reimplementing drawdown
maths, consistent with this project's existing convention of one
drawdown implementation shared across experiments.
"""
from __future__ import annotations

import datetime as dt
from typing import Mapping, Optional, Sequence

import numpy as np
import pandas as pd

from ..metrics import max_drawdown  # src/metrics.py, the existing project module
from .ledger import PaperPortfolio, PriceObservation, PriceType, holdings_asof

VALUATION_PRICE_PREFERENCE = (PriceType.CLOSE, PriceType.LAST, PriceType.NAV)


class MetricsError(Exception):
    pass


def _valuation_price(observations: Sequence[PriceObservation], instrument: str, as_of: dt.datetime) -> Optional[float]:
    """Pick the latest-available valuation price at/before `as_of`,
    preferring CLOSE, then LAST, then NAV. Bid/ask are deliberately never
    used for valuation (a one-sided quote is not a settled reference
    price)."""
    best = None
    for price_type in VALUATION_PRICE_PREFERENCE:
        candidates = [
            o for o in observations
            if o.instrument == instrument and o.price_type is price_type and o.timestamp <= as_of
        ]
        if candidates:
            best = max(candidates, key=lambda o: o.timestamp)
            break
    return best.price if best is not None else None


def nav(portfolio: PaperPortfolio, price_observations: Sequence[PriceObservation], as_of: dt.datetime) -> float:
    """Net asset value: cash plus the value of each holding at the latest
    available valuation price at/before `as_of`, reconstructed purely from
    the immutable transaction log (does not depend on live portfolio
    state, so NAV can be computed for any historical date)."""
    snapshot = holdings_asof(portfolio, as_of)
    value = snapshot["cash"]
    missing = []
    for instrument, units in snapshot["units"].items():
        if abs(units) < 1e-12:
            continue
        price = _valuation_price(price_observations, instrument, as_of)
        if price is None:
            missing.append(instrument)
            continue
        value += units * price
    if missing:
        raise MetricsError(
            f"No valuation price observation available for {missing} at or before {as_of}; "
            "refusing to compute a NAV from incomplete prices rather than treating missing "
            "holdings as zero-valued."
        )
    return value


def holdings_value(portfolio: PaperPortfolio, price_observations: Sequence[PriceObservation], as_of: dt.datetime) -> dict:
    snapshot = holdings_asof(portfolio, as_of)
    values = {}
    for instrument, units in snapshot["units"].items():
        if abs(units) < 1e-12:
            continue
        price = _valuation_price(price_observations, instrument, as_of)
        if price is None:
            raise MetricsError(f"No valuation price observation available for {instrument} at or before {as_of}")
        values[instrument] = units * price
    return values


def allocation(portfolio: PaperPortfolio, price_observations: Sequence[PriceObservation], as_of: dt.datetime) -> dict:
    """Per-instrument and cash allocation as a fraction of NAV."""
    snapshot = holdings_asof(portfolio, as_of)
    values = holdings_value(portfolio, price_observations, as_of)
    total = snapshot["cash"] + sum(values.values())
    if total <= 0:
        raise MetricsError(f"Cannot compute allocation for portfolio {portfolio.portfolio_id}: NAV is non-positive")
    result = {instrument: v / total for instrument, v in values.items()}
    result["CASH"] = snapshot["cash"] / total
    return result


def realised_pl(portfolio: PaperPortfolio) -> float:
    return float(sum(t.realised_pl for t in portfolio.transactions if t.realised_pl is not None))


def unrealised_pl(portfolio: PaperPortfolio, price_observations: Sequence[PriceObservation], as_of: dt.datetime) -> float:
    total = 0.0
    for instrument, lot in portfolio.holdings.items():
        price = _valuation_price(price_observations, instrument, as_of)
        if price is None:
            raise MetricsError(f"No valuation price observation available for {instrument} at or before {as_of}")
        total += lot.units * (price - lot.average_cost)
    return total


def time_weighted_return(valuation_points: Sequence[tuple], external_flows: Mapping[dt.datetime, float]) -> float:
    """Classic chain-linked time-weighted return.

    `valuation_points` is a chronologically ordered sequence of
    (timestamp, nav) pairs, each the NAV immediately *before* any external
    flow booked at that same timestamp is applied. `external_flows` maps a
    timestamp to a signed external cash flow (deposits positive,
    withdrawals negative) that occurs at that valuation point; internal
    buys/sells/distributions/reinvestments are not external flows and must
    not appear here.

    Returns the geometric total return over the whole series as a
    fraction (0.05 == +5%).
    """
    if len(valuation_points) < 2:
        raise MetricsError("time_weighted_return requires at least two valuation points")
    compounded = 1.0
    for (t0, v0), (t1, v1) in zip(valuation_points[:-1], valuation_points[1:]):
        flow_at_start = external_flows.get(t0, 0.0)
        base = v0 + flow_at_start
        if base <= 0:
            raise MetricsError(f"Non-positive base NAV ({base}) between {t0} and {t1}; cannot compute a sub-period return")
        sub_period_return = (v1 / base) - 1.0
        compounded *= (1.0 + sub_period_return)
    return compounded - 1.0


def drawdown(nav_series: Sequence[float]) -> float:
    """Maximum drawdown of a NAV series, expressed as a negative fraction
    (e.g. -0.10 for a 10% peak-to-trough decline). Delegates to the
    project's existing `max_drawdown`, normalising the series to start at
    1.0 so it behaves like an equity curve."""
    series = np.asarray(list(nav_series), dtype=float)
    series = series[np.isfinite(series)]
    if series.size == 0 or np.any(series <= 0):
        return float("nan")
    return max_drawdown(series / series[0])


def benchmark_relative(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> dict:
    """Aligns two simple-return series on their common dates (no
    forward-fill across gaps, mirroring MOM-001's benchmark-comparison
    convention) and reports total-return comparison statistics."""
    aligned = pd.concat(
        {"portfolio": portfolio_returns, "benchmark": benchmark_returns}, axis=1, join="inner"
    ).dropna()
    if aligned.empty:
        raise MetricsError("No overlapping observations between portfolio and benchmark return series")
    portfolio_total = float((1.0 + aligned["portfolio"]).prod() - 1.0)
    benchmark_total = float((1.0 + aligned["benchmark"]).prod() - 1.0)
    return {
        "portfolio_total_return": portfolio_total,
        "benchmark_total_return": benchmark_total,
        "excess_return": portfolio_total - benchmark_total,
        "aligned_observations": int(len(aligned)),
    }
