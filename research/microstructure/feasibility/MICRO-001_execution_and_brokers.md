# MICRO-001 execution and brokers

**Boundary:** this is a public-documentation review.  It did not create an
account, connect an API, request credentials, use paper trading or submit an
order.  It must not be read as broker selection or authority to trade.

## Candidate comparison

| Candidate | Documented public capability | Data distinction | Key unknowns / gate |
|---|---|---|---|
| Interactive Brokers (IBKR) | Its TWS API documentation describes programmatic market-data requests and an interface intended to automate TWS operations such as orders and account/position monitoring. [S7][S9] | IBKR says API market data requires relevant live subscriptions; a trading API is not evidence of a full historical MBO feed. [S7][S8] | Confirm Australian-resident eligibility, ASX equity support for the intended account, order types/conditions, routing, acknowledgements, partial fills/cancels, rate limits, current fees/minimums, and paper/live differences in current terms. |
| Other Australian brokers | Not assessed as a candidate because this review found no verified, official public API specification within scope. | No data capability inferred. | Identify candidates only after an official API specification confirms programmatic Australian-equity order workflow and terms. |

The intentionally short table avoids presenting retail platforms with
undocumented APIs as feasible candidates.  It is incomplete, not an endorsement
of IBKR.

## What IBKR documentation does and does not establish

IBKR's public material states that live top-of-book, depth-of-book and
historical market-data API requests require the relevant live market-data
subscriptions.  Its paper-trading material describes a simulated account, but
paper environments can differ from live execution and data entitlement; this
must be validated from current written terms before any future paper exercise.
[S7][S8][S9]

The reviewed material does not establish for MICRO-001: ASX-specific exchange
permissions, precise order routing, depth coverage, event timestamp quality,
queue position, exchange acknowledgement latency, historical event-data
retention, or total cost.  None may be assumed from a generic API description.

## Execution feasibility

| Use case | Current assessment | Reason |
|---|---|---|
| Millisecond passive/queue strategy | **Not feasible now** | Requires event-level data and realistic queue/fill/routing evidence absent from this review; API access alone does not supply either. |
| Seconds-to-minutes directional experiment | **Not authorised and not yet feasible** | Could be assessed later after data and cost gates, but there is no strategy implementation or approved execution environment. |
| Longer intraday execution study | **Research-only conditional** | May study realised-price benchmarks with suitable historical data; broker routing/fill details remain an external validation requirement. |

## Cost and operational cautions

Brokerage, exchange fees, minimum charges, bid–ask spread, market impact, tax,
data fees and failed/passive-order opportunity cost all matter.  No current
brokerage or minimum fee has been asserted because it must be verified in the
broker's current Australian schedule, for the specific account and venue.  This
is particularly important because the stated experimental allocation is AUD 20;
a minimum fee alone can dominate a small trade.

## Preconditions for any later broker evaluation

1. Written ASX-instrument, market-data and API entitlement confirmation.
2. Current fee schedule and minimum-order/lot constraints captured with access
   date and account assumptions.
3. Documented lifecycle test plan for acknowledgements, rejects, modifications,
   cancels, partial fills and reconciliation — **not executed under MICRO-001**.
4. Independent risk and governance approval before even paper trading.  Nothing
   in this report grants that approval.
