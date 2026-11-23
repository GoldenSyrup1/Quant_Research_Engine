# MICRO-001 data availability

**Status:** no data has been acquired, downloaded or subscribed to.  Product
descriptions below are leads for a later written-specification exercise, not
approval or a recommendation.  Sources were accessed 23 November 2026; see the
[source register](../sources/source_register.md).

## Why granularity matters

| Data form | Can support | Cannot establish on its own |
|---|---|---|
| OHLCV/intraday bars | Coarse minute-regime descriptions | Spread, trade direction, queue position or intra-bar ordering |
| Sampled best bid/ask | Quoted-spread and coarse quote-change studies | Every quote change, displayed depth beyond best levels, order priority |
| Market-by-price (MBP) | Aggregated visible depth by price level | Individual order identity, add/cancel lifecycle, exact queue position |
| Market-by-order (MBO) events | Order additions, changes, cancellations and executions if fields/sequencing are complete | Executability without a matching/routing model; hidden liquidity may remain unobserved |
| Trade prints | Trade-price/volume activity and possible trade-flow models | Aggressor direction without a documented classification method; full displayed liquidity |

## Provider/data comparison

| Provider/product lead | Historical / live | Publicly documented coverage and granularity | Timestamp / sequencing | Access and licensing | Pricing / unresolved point |
|---|---|---|---|---|---|
| ASX Information Services real-time data | Live product description | ASX says feeds can contain price, volume, market depth, full order book, on-/off-book trade stamps. [S2][S3] | Not verified in reviewed public pages. | Commercial information service; licence/use terms require confirmation. | No price asserted; historical replay availability and entitlement must be obtained in writing. |
| ASX research and analytics products | Historical product family | ASX says research products include long history and share-price history. [S4] This does not prove event-level history. | Not verified. | Contact/product terms required. | Granularity, coverage, format and research redistribution rights unknown. |
| ASIC quarterly market statistics | Historical public aggregates | ASIC publishes market-characteristic, concentration and efficiency statistics from orders/trades. [S5][S6] | Aggregated statistics, not a replay feed. | Public regulatory publication. | Not suitable as H1–H5 raw input. |
| IBKR API market data | Live/API and limited historical API access described | Requires appropriate live subscriptions for requested instruments; documents mention top-of-book, depth and historical requests. [S7][S8] | Not verified as exchange-sequenced research feed. | Entitlements and vendor licences apply. | Not a substitute for independently specified event history; ASX product entitlement needs confirmation. |

No claim is made here that any one provider offers all ASX and competing-venue
events, a particular retention window, microsecond timestamps, or a licence
suitable for research storage.  Obtain those answers in a dated vendor response
before selecting a source.

## Minimum data specification for a viable pilot

For seconds/minutes research, request a small historical sample containing, at
minimum: instrument and venue identifiers; exchange event timestamp and timezone;
sequence number or documented ordering rule; trade price/size/conditions; best
bid/ask price/size; session-state/auction markers; and corporate-action/security
reference information.  Record raw-file checksums, licence, retrieval date,
coverage, and all transformations.

For sub-second H1–H4, add all visible depth levels or MBO event messages,
add/modify/cancel/execution semantics, sequencing/recovery rules, and a clear
statement of whether timestamps are source/exchange or vendor receipt times.
Without this, label the work *exploratory descriptive analysis*, not a
microstructure signal test.

## Data acceptance gates

Before analysis, audit the untouched raw sample for file checksum, schema,
duplicate messages, invalid prices/sizes, non-monotonic sequence/timestamps,
session/auction boundaries, crossed or locked quotes, gaps, mapping changes and
trade-condition fields.  Report anomalies; do not repair, interpolate or delete
them silently.  Preserve raw data and document any derived tables separately.

## Economic context

There is no public MICRO-001 quote for the required data.  At an AUD 20 maximum
experimental allocation, even a modest recurring data cost could dominate any
possible trading return.  That is an economic warning, not a quoted price.  A
research-only sample may still be worthwhile only after its cash cost and usage
rights are known, and never by using the AUD 30 protected reserve.
