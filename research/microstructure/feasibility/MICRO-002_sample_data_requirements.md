# MICRO-002 — Sample-data requirements and acceptance specification

This is a written acceptance specification.  It authorises no download beyond a
provider's public sample, no account creation and no purchase.  It must be
applied to raw copies; anomalies are reported, never silently repaired or
discarded.

## Two distinct requirements

| Requirement | Tier A — seconds to minutes | Tier B — sub-second / order lifecycle |
|---|---|---|
| Intended questions | H2 trade flow, H3 liquidity shocks, quote changes, H5 execution-quality descriptions | H1 imbalance and H4 replenishment/event response; queue/lifecycle research |
| Minimum venues | ASX plus Cboe Australia where the instruments trade; retain venue identifier. A single-venue study must be labelled as such. | Same, with an ordered source per venue; cross-venue ordering limitations disclosed. |
| Trades | Exchange event time, instrument/venue ID, price, size, condition/correction flags; documented trade direction methodology. | Same, plus message/event sequence and execution semantics. |
| Quotes | Best bid/ask price and displayed size with source time/timezone; update versus snapshot clearly specified. | Sequenced MBP at enough depth for the hypothesis, or MBO. |
| Order data | Not mandatory for a descriptive Tier-A test. | Adds, modifies, cancels and executions; order identifiers or clearly documented aggregation; no asserted queue position without the necessary fields. |
| Time / ordering | Precision must be stated; chronology must be demonstrably usable at the proposed horizon. | Exchange/source timestamps, timezone, sequence scope, deterministic ordering, gap/recovery messages and session-state markers are mandatory. |
| Replay / reference | Trading-day coverage, corporate action/ticker mapping, session/auction states and raw-file provenance. | Same, plus delivery/recovery documentation and a reproducible venue-day replay convention. |

## Sample acceptance checklist

Record the provider, product/version, licence, retrieval/access date, sample
period, checksum, file size and untouched filename before parsing.  Then report:

1. **Integrity and schema:** checksum, compression/file integrity, encoding,
   field names/types, schema version, delimiter and documented null semantics.
2. **Identity:** stable instrument and venue IDs; mapping to display ticker;
   identifier changes, listings/delistings and reference-data source.
3. **Time:** parse timestamp precisely; record timezone/UTC offset; distinguish
   exchange event time, publisher time and local receipt time; test monotonicity
   within each documented sequence domain.
4. **Ordering:** examine sequence numbers, duplicate events, missing ranges,
   reset boundaries, snapshots/gap-fill messages and ordering of equal-time
   events.  Absence of sequence is a limitation, not permission to invent order.
5. **Economic validity:** reject neither nor repair automatically: flag invalid
   price/quantity, zero/negative values where invalid, crossed/locked quotes,
   stale quotes and trades outside contemporaneous quote bounds.
6. **Market semantics:** inspect trade-condition/correction fields, auction and
   session-state messages, halts, off-book/report messages, tick-size/reference
   fields and whether updates are complete, sampled or normalised.
7. **Coverage:** enumerate dates, instruments, venues, session intervals, gaps,
   volume/count discontinuities and multiple depth levels.  Compare against the
   provider's stated scope only; do not infer completeness from a small sample.
8. **Reproducibility:** preserve the raw sample, its terms, manifest and all
   scripts/results separately.  Derived data must remain within licence rights.

## What the verified Cboe PITCH sample can and cannot answer

Cboe's product page advertises a sample and says the dataset has order,
modification, cancellation and trade records. [N4]  It can therefore test
whether the available file has required fields, event ordering and session
semantics.  It cannot demonstrate ASX coverage, total Australian-market
coverage, historical completeness beyond its sample, or executable performance.

## Manual vendor enquiry template — do not send under MICRO-002

> Subject: Historical Australian equity data — research sample and specification
> request
>
> We are evaluating a research-only historical dataset and are not requesting
> live trading connectivity.  Please provide the current product specification,
> licence and quote for [ASX / Cboe / both] for a limited historical sample and
> an optional paid pilot.  Confirm: venues/facilities and off-book coverage;
> instruments and dates; trade, quote, MBP and MBO fields; exchange versus
> vendor timestamp, precision, timezone and sequence/recovery semantics;
> session/auction and condition codes; file format/delivery; historical
> retention; sample availability; internal-research, local-storage, derived-data
> and retention rights; all one-off, recurring, API/non-display and exchange
> charges.  Please state explicitly which details vary by entitlement.

The recipient and user must independently decide whether sending such an inquiry
is appropriate.  This repository must store any response with retrieval date and
the applicable terms, not just a summary.
