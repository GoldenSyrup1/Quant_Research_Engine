# MICRO-001 source register

All sources below were accessed **23 November 2026**.  The register records what
each source supports, not claims beyond it.  Product pages are not contracts;
current commercial terms, licences and specifications must be requested before
any acquisition or use.

| ID | Primary source | URL | Supported claim / limitation |
|---|---|---|---|
| S1 | ASX, Cash market trading hours | [ASX trading phases](https://www.asx.com.au/markets/market-resources/trading-hours-calendar/cash-market-trading-hours) | Documents pre-open, opening auction, normal trading, CSPA and related session timings/randomised windows. Does not provide the full current order-rule specification. |
| S2 | ASX Information Services, Real time data | [ASX real-time data](https://www.asx.com.au/connectivity-and-data/information-services/real-time-data) | Describes ASX real-time feeds with price, volume, depth, full order book and on-/off-book trade information. Does not establish MICRO-001 historical product scope or licence. |
| S3 | ASX Information Services, Price data | [ASX price-data page](https://www.asx.com.au/connectivity-and-data/information-services/price-data/real-time-data) | Describes full-depth electronic order book and on-/off-book trade stamps. No inferred timestamp/sequence guarantee. |
| S4 | ASX Information Services, Research and Analytics | [ASX research products](https://www.asxonline.com/public/landing-pages/asx-market-information/research-and-analytics-products.html?cq_ck=1542245555446) | States that historical/research products include long history and share-price history. Does not prove raw event availability. |
| S5 | ASIC, Equity market data | [ASIC market-data hub](https://www.asic.gov.au/regulatory-resources/markets/market-structure/equity-market-data) | Explains ASIC's recurring market statistics coverage. It is aggregate regulatory publication, not a raw event feed. |
| S6 | ASIC, September 2026 equity market data | [ASIC September 2026 data](https://www.asic.gov.au/regulatory-resources/markets/market-structure/equity-market-data/2026/equity-market-data-for-quarter-ending-september-2026) | Current venue/spread/depth/turnover statistics and terminology. Values are period aggregates, not inputs to a signal. |
| S7 | Interactive Brokers, TWS API streaming market data | [IBKR API market data](https://interactivebrokers.github.io/tws-api/market_data.html) | Says suitable live market-data subscriptions are required for top-of-book, depth and historical market-data API requests. Not an ASX-specific entitlement confirmation. |
| S8 | Interactive Brokers FAQ | [IBKR real-time data/API](https://www.interactivebrokers.com/support/faq/content/1491287373) | Says API real-time data generally requires at least a Level 1 subscription and licensing can vary. No event-history guarantee. |
| S9 | Interactive Brokers, TWS API limitations | [IBKR API limitations](https://www.interactivebrokers.com/docs/tws-api/doc/notes-limitations/tws-api-limitations) | Describes TWS API's automation role and paper-trading concept. Does not establish equivalence of paper and live execution. |
| S10 | ASIC, cash-equity methodology | [ASIC INFO 177](https://www.asic.gov.au/regulatory-resources/markets/market-structure/equity-market-data/quarterly-cash-equity-market-data-release-methodology-and-definitions) | Defines quoted/effective spread and coverage concepts. It supports cost awareness, not transaction-cost estimates for a particular strategy. |
| S11 | ASIC, Regulatory Guide 172 | [ASIC RG 172](https://download.asic.gov.au/media/w02b4nsv/rg172-published-21-september-2026.pdf) | Describes market-operator post-trade information/data availability obligations. Does not give the price or entitlement for a usable historical feed. |

## Source-quality notes

- ASX and ASIC are primary for market structure, official products and Australian
  regulatory statistics.
- IBKR documentation is primary for IBKR's stated API behaviour, but cannot
  establish another provider's feed, exchange-level timestamps or actual fills.
- No source in this register verifies a commercial price for the required
  historical MBP/MBO data.  The report deliberately records that as unknown.
