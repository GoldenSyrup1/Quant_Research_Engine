# MICRO-002 — Audit of the MICRO-001 source register

**Verification date:** 24 November 2026.  **Historical access date preserved:**
23 November 2026.  “Resolves” means the URL returned successfully during this
review; it is separate from whether the source remains adequate for the recorded
claim.  No MICRO-001 conclusion has been silently rewritten.

| Original ID | Result | Claim support today | Action / caveat |
|---|---|---|---|
| S1 ASX cash-market trading hours | Resolves | Supports session phases and auction timing/windows. | Retain; not a matching-rule/order-type manual. |
| S2 ASX real-time data | Resolves | Supports real-time price, volume, depth, full order book and off-book report description. | Retain; no historical replay/price inference. |
| S3 ASX price-data page | Resolves | Supports MarketSource full-depth, order-book and trade-stamp description. | Retain; current product page, not a field specification. |
| S4 ASX research/analytics | Resolves | Supports long-history/research-product and Register-of-Sales description. | Retain; it does not prove MBO availability. |
| S5 ASIC equity-market hub | Resolves | Supports existence/scope of ASIC aggregate statistics. | Retain; no raw-feed implication. |
| S6 ASIC September 2026 release | Resolves | Supports period statistics and multi-venue framing. | Retain as period-specific evidence; do not generalise its values beyond the period. |
| S7 IBKR TWS API market-data guide | Resolves **but deprecated** | Its historic content supports the original broad subscription caveat. | Do not use as current API authority. Supersede current-use reference with IBKR Campus material [N11] and confirm specifics in current account terms. |
| S8 IBKR real-time data/API FAQ | Resolves | Supports subscription/licensing qualification. | Retain with access-date caveat; not a market-structure data specification. |
| S9 IBKR TWS API limitations | Resolves **but deprecated** | Supports historical statement about TWS automation/paper concept only. | Do not treat as current operational specification; use current Campus/account documentation before any future authorised review. |
| S10 ASIC INFO 177 methodology | Resolves | Supports quoted/effective-spread definitions and aggregate methodology. | Retain; it does not set execution costs. |
| S11 ASIC RG 172 | Resolves | Supports market-operator post-trade availability obligations. | Retain; obligations do not establish a purchasable historical product. |

## Material audit finding

The original `interactivebrokers.github.io/tws-api` documentation expressly
states it is deprecated and directs readers to IBKR Campus. [N10]  MICRO-001's
limited conclusion remains sound: broker API access must not be assumed to
provide event-level research data.  MICRO-002 does not rely on deprecated IBKR
documentation to establish a current capability.

## Source-review outcome

All eleven original URLs resolved in the 24 November check.  No link was removed
from the historical source register.  New sources are recorded separately in
MICRO-002's register, preserving the evidence trail and the prior dates.
