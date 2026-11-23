# MICRO-001 — ASX market-microstructure feasibility

**Status:** documentation-first feasibility assessment, 23 November 2026.  No
data service, broker account, API credential, paper-trading system, strategy, or
order has been created as part of MICRO-001.

## Executive assessment

**Conclusion: CONDITIONAL GO.**  It is reasonable to advance to a tightly
scoped *data-reconnaissance* milestone, not to implementation or trading.  The
next milestone must establish whether appropriately licensed, timestamped ASX
and competing-venue historical data can be obtained at a justifiable research
cost.  It must also document coverage and ordering guarantees before any signal
research is attempted.

The evidence does **not** support pursuing a millisecond latency race at the
project's AUD 20 maximum experimental allocation.  ASX operates auctions and
continuous trading, and Australian equity trading is fragmented across ASX and
a competing venue; a partial venue view can be misleading.  Official sources
describe full-depth/order-book real-time products, but this review did not
verify a publicly priced historical, replayable, market-by-order event dataset.
That unresolved requirement is decisive for H1–H4 at sub-second horizons.

The core daily-price momentum programme, including MOM-001, is independent and
was not inspected, changed, or used as evidence here.

## Feasibility by horizon

| Horizon | Data and infrastructure needed | Assessment | Why |
|---|---|---|---|
| Milliseconds | Sequenced market-by-order events across venues, precise clocks, low-latency feed handling and realistic queue/fill modelling | **No go now** | These prerequisites are not available in the repository and the economic case is implausible at the stated capital scale. |
| Seconds | Timestamped trades plus best bid/ask or market-by-price across relevant venues; careful event ordering and execution-cost model | **Conditional** | Historical data scope, licensing, timestamps and cost must first be verified. |
| Minutes | Reliable intraday bars or sampled quotes/trades, explicit gap handling and conservative execution assumptions | **Conditional** | A research-only study may be practical if documented data coverage can be acquired without implying executable profitability. |
| Longer intraday execution | Quote/trade data appropriate to the execution question and a broker-capability review | **Conditional** | The question is execution quality, not a latency advantage; broker routing and order handling require written confirmation. |

## Required gate before further work

1. Obtain written product specifications and quotes (without buying anything)
   from ASX Information Services and, if applicable, the competing venue or an
   authorised redistributor.
2. Confirm: venue coverage, securities, historical period, raw versus sampled
   data, timestamp timezone/precision, sequence semantics, corporate-action
   handling, redistribution/research licence, and total cost.
3. Define a small data-quality acceptance test on a free vendor sample or
   documented sample only.  It must test monotonic sequence/timestamps,
   crossed/locked quotes, session boundaries, auctions, duplicates, gaps, and
   trade-condition fields.  It must not turn into a trading system.
4. Reassess feasibility against the protected-reserve rule.  Research-data cost
   and execution capital are separate decisions; neither is approved by this
   report.

## Documents

- [Market structure](feasibility/MICRO-001_market_structure.md)
- [Data availability](feasibility/MICRO-001_data_availability.md)
- [Execution and brokers](feasibility/MICRO-001_execution_and_brokers.md)
- [Competitive landscape](feasibility/MICRO-001_competitive_landscape.md)
- [Candidate hypotheses](hypotheses/candidate_hypotheses.md)
- [Source register](sources/source_register.md)

All external factual claims are tied to the source register.  “Unknown” means
the review did not verify the fact from a public primary source; it is not a
negative claim about the provider.
