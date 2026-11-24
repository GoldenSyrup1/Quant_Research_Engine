# MICRO-002 — Market-data vendor assessment

**Assessment date:** 24 November 2026.  **Decision: CONDITIONAL GO** for a
no-purchase sample-format review only.  No provider has been contacted, no
account/data product has been created or purchased, and no live data has been
collected.  Sources and their limitations are in the [MICRO-002 source
register](../sources/MICRO-002_source_register.md).

## Executive recommendation

Investigate **Cboe Australia Equities Multicast PITCH** first, solely by
inspecting its publicly offered sample under its terms.  It explicitly describes
a tick-by-tick file containing orders, modifications, cancellations and trades,
and is the only identified candidate with a public sample and explicit
order-event description. [N4]  It is not a whole-market solution: it covers the
Cboe Australia/CXA platform, not ASX.  It can resolve format and acceptance-test
uncertainty, not market-wide price-formation uncertainty.

For credible Tier A research, the leading **commercial** route is a written
specification/quote request to ASX Information Services for MarketSource
historical trade-and-quote/depth content, combined with Cboe coverage or an
authorised redistributor.  ASX's public information confirms real-time full
order-book/trade information and ITCH/FIX delivery, but not a purchasable
historical event-replay bundle, retention or price. [N1][N2]

LSEG Tick History and ICE's Cboe-Australia catalogue are credible institutional
leads, not selected vendors.  Their public material documents broad tick/history
capabilities or Cboe access, respectively, but this review did not verify a
specific Australian venue package, field set, licence or price. [N6][N8]

## Ranked provider comparison

| Rank / provider | Verified coverage and access | Historical / live / granularity | MBP / MBO and timestamps | Sample / price | Suitability and unresolved requirement |
|---|---|---|---|---|---|
| 1. Cboe Australia, Equities Multicast PITCH | Cboe Australia/CXA only; DataShop page and PITCH specification are referenced. [N4] | Historical from 27 Mar 2023; live PITCH is separately described. Flat file per day per matching unit. | Explicitly states all orders, modifications, cancellations and executed trades. Treat detailed field/timestamp/sequence semantics as **confirm from current PITCH specification**. | Public “Download sample” link; current price not displayed: **QUOTE REQUIRED**. Cboe publishes a price of $500/month for legacy CHXMD data (Nov 2015–Feb 2022); the cited page does not specify the currency. This is not the current PITCH price. | Best format sample; Tier B single-venue only. Need licence, sample provenance, event spec and current cost. |
| 2. ASX Information Services, MarketSource / research products | ASX-operated markets; direct or vendor access. [N1][N2] | Real-time full-depth/order-book and trade description; research page describes trade-by-trade Register of Sales and historical products. [N1][N3] | ASX says ITCH/FIX formats; public pages do not establish historical MBO/MBP replay, timestamp precision or recovery semantics. | Product examples exist, but no verified MBO sample. **QUOTE REQUIRED**. | Strong source-authority candidate for ASX leg; Tier A/B only after written historical-product and licence confirmation. |
| 3. LSEG Tick History | Global archive; the public site does not enumerate the ASX/CXA package in the reviewed pages. [N6][N7] | Trades, quotes and market depth; custom extract, venue-by-day, API/cloud delivery documented. | Normalised/raw options are advertised; PCAP claims GPS-synchronised nanosecond capture. Exact Australian venue, event field, sequence and source-time semantics are **unverified**. | Tutorials are documentation, not a public Australian raw-data sample. **QUOTE REQUIRED**. | Potential Tier A; Tier B only if a written venue/field/sample confirmation proves needed event semantics. |
| 4. ICE Data Services, Cboe Australia catalogue | Cboe Australia native-feed access and consolidated history are described. [N8] | Streaming data and end-of-day/consolidated history are described. | Site refers to Level 1/2/3 historical tick data generally; exact product/event fields, timestamps and CXA history need confirmation. | No verified sample or price. **QUOTE REQUIRED**. | Possible Cboe venue lead; neither tier until a product specification and licence are supplied. |
| 5. IBKR API market data | Broker/API entitlement, not a dedicated historical microstructure vendor. [N10][N11] | Live subscription-dependent data; documentation confirms API requests need entitlements. | No verified complete ASX/CXA historical MBO replay, sequencing or research-storage licence. | No suitable sample; trial accounts do not support APIs. [N11] | Neither Tier A nor B as a primary research data source. |

## Historical versus live distinction

Live access is not evidence that a vendor supplies a reproducible historical
dataset.  Conversely, historical data must be assessed for feed capture time,
exchange event time, completeness, corrections, sequence recovery, retained
fields and licence.  Market-by-price aggregates cannot reconstruct individual
order lifecycle; trade-and-quote data cannot establish queue position.  These
distinctions are gating requirements, not implementation choices.

## Direct answers to the decision gate

1. **Useful seconds-to-minutes history?** Plausibly yes, conditional on an ASX
   and Cboe-inclusive trade/quote specification and licence.  No identified
   public source yet proves that complete package.
2. **Sufficient sub-second history?** Cboe PITCH plausibly meets the event-type
   requirement for Cboe only.  Whole-market Tier B remains unproven.
3. **Sample before payment?** Yes for the Cboe PITCH format sample; scope and
   licence must be read before local use.  No comparable ASX or LSEG sample was
   verified.
4. **Lowest credible cost?** The Cboe sample is the lowest-cost inspection path
   (no purchase represented).  For a usable multi-venue dataset, **QUOTE
   REQUIRED**; no cost can honestly be claimed from public pages.
5. **First vendor?** Cboe, to inspect the sample; ASX Information Services,
   next, for a written Tier-A historical-data specification.
6. **Evidence needed?** The exact checklist in the sample-data requirements,
   signed/dated vendor answers on coverage, field definitions, time/sequence,
   retention, permitted use/storage/derived data, and an all-in quote.

## Outstanding questions

- Does ASX sell or authorise historical, sequenced MBO/MBP replay at the desired
  scope, and which market facilities/off-book reports are included?
- What exact timestamp clock, timezone, precision, sequence domain and gap
  recovery applies to each candidate product?
- Can a single licence permit local storage and derived research outputs without
  data redistribution?
- Which present Cboe entity/product terms apply following market-operator
  changes, and are they still current at the time of inquiry?
- Can an affordable package cover both public venues and reference-data changes?
