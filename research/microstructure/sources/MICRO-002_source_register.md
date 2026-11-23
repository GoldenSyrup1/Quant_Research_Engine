# MICRO-002 source register

All sources below were accessed **24 November 2026**.  They support only the
claims stated in the linked feasibility reports.  A product webpage does not
grant rights, confirm an entitlement or supply a price unless it expressly says
so.

| ID | Provider/source | URL | What it supports / limitation |
|---|---|---|---|
| N1 | ASX MarketSource real-time data | [ASX real-time data](https://www.asx.com.au/connectivity-and-data/information-services/price-data/real-time-data) | Real-time best bid/offer, full depth, post-trade data, official prices and reference data; not a historical-product commitment. |
| N2 | ASX information services | [ASX market-information page](https://asxonline.com/content/asxonline/public/landing-pages/asx-market-information.html) | MarketSource scope, subscriber/distributor distinction and that detailed prices are available on request. |
| N3 | ASX research/analytics | [ASX research products](https://www.asxonline.com/public/landing-pages/asx-market-information/research-and-analytics-products.html?cq_ck=1542245555446) | Historical research products and Register of Sales; no inferred order-event coverage. |
| N4 | Cboe Australia DataShop | [Cboe Australia Multicast PITCH](https://datashop.cboe.com/cboe-australia-equities-multicast-pitch) | Sample availability; PITCH order/modification/cancellation/trade description; period from 27 Mar 2023; legacy USD 500/month statement. Current PITCH price is not publicly established here. |
| N5 | Cboe Australia Data Policies | [Data Policies PDF](https://cdn.cboe.com/resources/au/participant_resources/Cboe-Australia-Data-Policies-V1-3.pdf) | Defines data categories and indirect/internal subscriber terminology; current terms must be confirmed before use. |
| N6 | LSEG Tick History | [LSEG Tick History](https://www.lseg.com/en/data-analytics/market-data/data-feeds/tick-history) | Global trades/quotes/depth, raw/normalised delivery and general access methods; no verified ASX/CXA field/package entitlement. |
| N7 | LSEG developer documentation | [Tick History REST API](https://developers.lseg.com/en/api-catalog/refinitiv-tick-history/refinitiv-tick-history-rth-rest-api) | Client API, custom and Venue-by-Day extraction mechanics; access requires client entitlement. |
| N8 | ICE Data Services catalogue | [Cboe Australia catalogue](https://developer.ice.com/fixed-income-data-services/catalog/cboe-australia) | Cboe Australia streaming/history listing and delivery names; exact content/price remains unverified. |
| N9 | ASX Java Downloader guide | [ASX downloader guide](https://asxonline.com/content/asxonline/public/documents/market-information-application--mia----java-downloader-guide.html) | Entitled ASX Online users can download visible historical product files; does not identify which product supplies microstructure fields. |
| N10 | IBKR deprecated API guide | [IBKR Guide Updates](https://interactivebrokers.github.io/tws-api/guide_updates.html) | Official notice that this documentation is deprecated and points to IBKR Campus. |
| N11 | IBKR Campus | [Market-data subscriptions lesson](https://www.interactivebrokers.com/campus/trading-lessons/subscribing-to-data/) | Account subscription context and statement that trial accounts do not support APIs; not a research-data licence. |
| N12 | ASX Market Data Feed presentation | [ASX MDF overview](https://www.asx.com.au/content/dam/asx/markets/trade-our-cash-market/equity-markets-working-groups/asx-equity-market-working-group-august-2025.pdf) | Example ASX MDF fields: MBP five levels, event/state changes and recovery. It is a presentation, not an entitlement or current product contract. |

## Documentation status

Original MICRO-001 sources S1–S11 are audited in
[MICRO-002 source audit](../feasibility/MICRO-002_source_audit.md).  The
deprecated IBKR guide is retained as historical evidence but is not used for
current capability claims.  Publicly verified current pricing is limited to the
explicitly labelled Cboe legacy-data statement; all other commercial pricing is
recorded as **QUOTE REQUIRED**.
