# UNIV-002 — Norgate Data Australian Platinum: field-level verification

**Assessment date:** 27 November 2026. Follow-on to
[UNIV-001](UNIV-001_point_in_time_universe_feasibility.md) and its
[source register](UNIV-001_source_register.md), which this document does
not rewrite. No purchase, account creation, vendor contact, or data
download occurred. All findings below come from re-reading Norgate Data's
own public pages directly (`norgatedata.com`), not from third-party
commentary.

## Executive conclusion

**CONDITIONAL GO, narrowed further than UNIV-001.** Field-level
verification confirms Norgate's Australian Platinum tier is a real,
specific, well-documented product — not a vague marketing bundle — and
upgrades several items UNIV-001 could not confirm (volume data, the exact
set of included/excluded security types for delisted coverage, the precise
indices covered for "breadth" purposes). But it also surfaces a serious new
caveat that **must be resolved with primary documentation, not assumed,
before this candidate is trusted further**: one page's auto-generated
summary (not verbatim text) suggested that Norgate's pre-March-2000 ASX
index history may be **"synthetic"** rather than actual historical data.
This is exactly the kind of claim this project's standards require to be
either confirmed from primary text or explicitly flagged as unverified —
it is flagged here as **unverified and unrelied-upon**, not confirmed and
not dismissed. The Norgate/Premium Data relationship remains genuinely
unresolved (not merely under-investigated); this document treats it as an
open question per the task's explicit instruction not to resolve ambiguity
by assumption. Economics are unchanged from UNIV-001: still **NO GO on any
purchase** at this project's capital scale (see §Pricing).

## Exact product and package identity

- Confirmed, verbatim, from Norgate's own JustData-transition page: *"Our
  business has operated since 1992, with our first public market data
  service launched in 1999."* Norgate Data describes itself as *"an
  Australian-based market data provider."*
- The product in question is specifically the **"Platinum" tier of
  Norgate's "AU Stock Market" package**, confirmed from
  `norgatedata.com/prices.php` and `norgatedata.com/stockmarketpackages.php`
  (AUD 346.50 / 6 months or AUD 630 / 12 months, ex-GST — unchanged from
  UNIV-001, re-confirmed here).
- Confirmed, verbatim, from `data-content-tables.php`: *"AU Stock Market
  includes all ASX-listed securities, as sorted into 5 categories."*
  *"Price & Volume are as reported by the Australian Securities Exchange
  (ASX)."*
- "Extras" (a bullet listed for both Gold and Platinum tiers, not
  Platinum-exclusive as UNIV-001's lighter pass implied) is confirmed to
  mean a bundle of **separate reference series** — commodity, economic,
  FX, futures-continuous data, and ASX market-breadth indicators (e.g.
  Advance/Decline, New Highs/Lows, McClellan) across All Ordinaries and the
  S&P/ASX 50/100/200/300 universes — **not** additional per-security
  fundamental or corporate-action data. This corrects an ambiguity left
  open by UNIV-001's lighter-pass reading of the same bullet point.

## Field-level evidence matrix

| Requirement | Confirmed | Partial | Unknown |
|---|---|---|---|
| Historical Australian daily prices | | ✓ — "back to 1992" confirmed; which security types get this full depth vs. "currently-listed" depth is not fully disambiguated | |
| Delisted security history | | ✓ — Platinum-only inclusion confirmed, with an **explicit included/excluded security-type list** (below); no confirmed start date for delisted coverage specifically | |
| Delisted prices retained after removal | | ✓ — a specific delisted-symbol naming convention is confirmed (`ONE-200105.au`), implying retained historical records under a distinct identifier, but no page states explicitly that *full* price history (not just existence) is retained post-delisting | |
| Historical ticker and identifier mapping | | ✓ — the delisted-symbol suffix convention (ticker + delisting year/month) is confirmed, which is *some* mechanism for distinguishing a delisted security from a reused ticker | ✓ — whether a renamed-but-still-listed security keeps one stable identifier across the rename is not addressed anywhere |
| Historical index membership | | ✓ — "Historical index constituents" confirmed as a named Platinum feature | ✓ — the underlying effective-dating mechanism (announcement vs. effective date) is not documented |
| ASX 200 historical constituents | | ✓ — "S&P/ASX 200" named as a covered universe for breadth-indicator purposes; a claim that it is also covered for the separate "Historical Index Constituents" feature appears only in an **unverified auto-summary**, not confirmed verbatim text | |
| All Ordinaries historical constituents | | ✓ — "All Ordinaries" named for breadth-indicator purposes; its coverage under "Historical Index Constituents" specifically is likewise only in the **unverified summary**, not verbatim | |
| Effective membership dates | | | ✓ — not addressed in any verbatim text read |
| Listing and delisting dates | | ✓ — delisting is implied by the delisted-symbol naming convention | ✓ — an explicit listing-date field is not confirmed |
| Corporate-action history | | | ✓ — no AU-specific corporate-action dataset found in verbatim text; a general "Capital Event" indicator (splits/bonus issues) was mentioned only in the **unverified summary** |
| Adjusted and unadjusted prices | | | ✓ — not addressed in any verbatim text; only export-format text was found ("ASCII" / "MetaStock Legacy"), not an adjustment-methodology statement |
| Dividends and distributions | | | ✓ — a "FrankedPct" field (franking level of the most recent dividend, AU-specific) appears only in the **unverified summary**, not confirmed verbatim |
| Delisting returns / merger outcomes | | | ✓ — not addressed anywhere in verbatim text |
| Historical market capitalisation | | | ✓ — not found in verbatim text; the unverified summary says market cap is "used in index construction," which is not the same as a retrievable per-security field |
| Historical liquidity / traded value | ✓ — "Price & Volume are as reported by the Australian Securities Exchange (ASX)" is verbatim and confirms volume data is included | | ✓ — whether this is raw share volume, traded value (price × volume), or both is not disambiguated |
| Historical fundamentals | | ✓ — "Current Fundamentals" confirmed as a named feature | ✓ — the word "current" (not "historical") suggests this may be a current-snapshot field, not a historical time series; no page resolves this explicitly |
| Python integration and export options | ✓ — a dedicated `norgatedata` PyPI package is confirmed, linked directly from Norgate's own navigation; export to ASCII and MetaStock Legacy format is confirmed for price data | | ✓ — the Python package's actual field coverage (whether it exposes delisted securities, index constituents, etc., or only prices) is not documented on these pages |

**Reading the matrix:** 2 of 17 rows are fully Confirmed, 9 are Partial
(a real, verbatim, on-point fact exists but does not fully settle the
requirement), and 6 remain genuinely Unknown from Norgate's own public
pages. This is a meaningfully more precise picture than UNIV-001's lighter
pass, and it should replace that pass's conclusions on these specific
points — UNIV-001's narrative text is not being rewritten, but this table
supersedes it as the authoritative field-level record.

## Historical universe and delisted-security coverage

Confirmed, verbatim, delisted-security scope (Platinum tier only):

- **Included:** Operating Companies, Listed Investment Companies, Pooled
  Development Funds, and Exchange Traded Funds.
- **Explicitly excluded:** other ETPs, all debt securities, all hybrid
  securities, company options, rights, exchange-traded options, and
  warrants.

This is a materially useful, specific finding: a future universe built on
this data would be scoped to equity-like securities and LICs/ETFs, not a
genuinely complete historical security master of everything ASX ever
listed. For momentum/value/quality research on ordinary shares, this
exclusion list is plausibly acceptable; for any strategy intending to
include debt, hybrids, or derivative-linked instruments, it would not be.

The delisted-symbol identifier convention observed (`ONE-200105.au`)
appends what appears to be a delisting year-month to the base ticker. This
confirms *some* mechanism exists to keep a delisted security's historical
records addressable and distinguishable from a later, unrelated listing
reusing the same ticker — directly relevant to the "ticker alias"
requirement in UNIV-001's proposed schema — but it was not confirmed
whether this convention also correctly handles a security that is renamed
while remaining listed (as opposed to delisted).

## Corporate-action and delisting treatment

**Not confirmed from verbatim Norgate documentation.** This is the single
largest remaining gap relative to UNIV-001's proposed schema (§5 of the
feasibility report: delisting-return treatment, corporate-action
adjustment methodology). An auto-generated page summary mentioned a
general "Capital Event" indicator and a "FrankedPct" dividend-franking
field, but — per this investigation's own explicit reliability check on
that summary (it separately and verifiably claimed a section did not
exist when it did) — **these specific claims are not relied upon** and are
reported here only as unverified leads for a future, more careful direct
read of the same page, not as findings.

## Python/export capabilities

Confirmed: a dedicated `norgatedata` Python package exists and is
officially linked from Norgate's own site navigation (distinct from the
general third-party charting-platform plugins such as AmiBroker,
RightEdge, and Wealth-Lab, which were already noted in UNIV-001). Export
to flat-file formats (ASCII, MetaStock "Legacy") is confirmed, but
Norgate's own text states this export covers *"historical price data (but
not other data features)"* — meaning index-constituent history, delisted-
security flags, and fundamentals, even if present in the plugin/API
access, are not confirmed to be exportable to a flat file via this route.
This matters operationally: a future universe build would most likely need
the Python package (not flat-file export) to retrieve the
survivorship-relevant fields at all, and this investigation did not
confirm what the Python package itself actually exposes.

## Norgate / Premium Data reconciliation — still unresolved, not assumed

This investigation did **not** find a page stating that Norgate Data and
Premium Data (`premiumdata.net`) are the same company, divisions of the
same company, or formally related, and it is **not assumed** here. What
was found:

- Norgate's own `data-content-tables.php` page links directly to a file
  hosted at `premiumdata.net` (a futures-contract-details spreadsheet),
  treating it as if it were Norgate's own resource — suggestive that
  `premiumdata.net` is infrastructure Norgate uses or controls, but this
  is a single incidental link, not a statement of corporate relationship,
  and is reported here as **suggestive, not confirmed**.
- Separately, Norgate's "JustData Transition" page confirms Norgate has a
  documented history of **absorbing other legacy Australian market-data
  brands** on closure (JustData, "closing after more than 30 years,"
  converts its customers to Norgate's Gold package, with Norgate stating
  explicitly *"Norgate Data is not receiving any money from JustData"*).
  This establishes that this kind of multi-brand consolidation is a real,
  precedented pattern for Norgate — which makes a similar relationship
  with Premium Data *plausible*, but this is pattern-matching, not
  evidence, and is explicitly **not treated as confirming** the actual
  relationship.
- UNIV-001's original finding stands and is not contradicted: Premium
  Data's own public retail pricing page shows only "Currently-listed" ASX
  products, with no delisted-securities option visible — still in tension
  with Norgate's own Platinum-tier description, and still unresolved.

**This remains an open question requiring either direct vendor
documentation (not contact, per this task's safeguards) or a future
explicitly authorised vendor enquiry — not something this investigation
resolves.**

## Pricing and licensing caveats

- Numeric pricing is re-confirmed, unchanged from UNIV-001: AUD 346.50 (6
  months) or AUD 630 (12 months), ex-GST, for the AU Stock Market Platinum
  tier.
- Newly confirmed, verbatim: *"Access to the database is no longer
  possible if a subscription lapses"* — meaning this is not a one-time data
  purchase but a recurring access dependency; any future universe built on
  this data would need either a continuously maintained subscription or a
  one-time export (and export is confirmed to cover price data only, per
  §Python/export above) — a materially relevant distinction this project
  did not previously have confirmed.
- No new pricing information changes the economic conclusion from UNIV-001
  §6: at AUD 630/year, this remains roughly 6× the project's entire $100
  starting capital and well above the $20 short-term experimental
  allocation. Per this task's instruction, **no purchase is made or
  recommended**, and research-data expenditure continues to be treated as
  a decision separate from the $50/$20/$30 capital allocations, not funded
  from them.

## Remaining unknowns

- Whether the "Historical Index Constituents" feature actually covers the
  ASX 200 and All Ordinaries specifically (as opposed to only the general
  breadth-indicator universes, which are separately confirmed) — the only
  evidence for this is an unverified, previously-shown-unreliable page
  summary, not verbatim text.
- Whether pre-March-2000 ASX index history is "synthetic" (back-tested
  with assumptions) rather than actual historical data — **this specific
  claim came only from the same unreliable auto-summary and is explicitly
  not relied upon here**, but it is important enough that it should be
  re-verified with a direct, careful read of the relevant page section
  before this product is relied upon for any pre-2000 research.
- Whether delisting returns are treated as cash-settlement, acquirer
  exchange value, or a declared loss — not found anywhere.
- Whether corporate-action adjustments (splits, consolidations) are
  applied to the historical price series at all, and by what methodology.
- The exact start date for delisted-security coverage specifically (vs.
  the general "back to 1992" figure, which may describe currently-listed
  price depth rather than delisted-security depth).
- What the `norgatedata` Python package actually exposes, as distinct from
  the flat-file export (which is confirmed price-only).
- The true nature of any Norgate/Premium Data relationship.

## Recommendation

**CONDITIONAL GO**, narrower than UNIV-001's: continue treating Norgate's
Australian Platinum tier as the leading low-cost candidate, but do not
advance to any purchase decision until the pre-2000 "synthetic data"
question and the delisting-return/corporate-action treatment questions are
resolved from primary Norgate documentation (not summaries). **NO GO** on
any purchase at current pricing relative to this project's capital
constraints, and **NO GO**, independent of the above, on vendor contact,
account creation, data acquisition, or any change to MOM-001 or MICRO-003.
This task's findings supersede UNIV-001's field-level claims where the two
differ (per the matrix above), while UNIV-001's overall approach
comparison and schema design remain unchanged and are not rewritten here.
