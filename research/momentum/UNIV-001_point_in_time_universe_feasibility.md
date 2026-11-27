# UNIV-001 — ASX point-in-time universe feasibility

**Assessment date:** 27 November 2026. **Decision: CONDITIONAL GO** for a
narrowly scoped, lowest-cost survivorship-bias-aware universe build, gated
on confirming one vendor's exact delisted-security coverage before any
purchase. This is a research and feasibility document only. MOM-001 was
read but not modified, rerun, or re-optimised; no data was purchased, no
vendor was contacted, no broker was connected, and no new strategy or
backtesting engine was implemented. The Cboe PITCH sample was not used
(MICRO-003 remains on HOLD per its closure audit).

## 1. Executive feasibility assessment

MOM-001's own verification report already names the exact gap this task
investigates: *"the eight names are a current hand-selected sample, not
point-in-time ASX constituents. Delisted, acquired, or historically
ineligible securities are absent"* (`MOM-001_verification.md`), and the
README states plainly that *"current membership is not a
survivorship-bias-free historical universe"* and that the data source does
*"not fix survivorship, delisting, ticker-history, or provider data-quality
biases."* This is a real, previously-acknowledged limitation, not a new
concern invented for this task.

The central finding of this investigation: **a genuinely survivorship-
bias-free ASX universe is commercially available at retail/individual
researcher pricing, not just at institutional pricing** — specifically
Norgate Data's Australian "Platinum" tier (AUD 630/year, or AUD 346.50 for
a 6-month term, ex-GST), which explicitly advertises delisted-security
history back to 1992 and historical index constituents (§3, §6). This is
materially better news than the typical assumption that point-in-time
equity data is an institutional-only (Bloomberg/FactSet/LSEG-class)
expense. However, **that price still exceeds this project's entire data
budget capacity** under the current capital constraints (§6) — the
cheapest credible option found is still roughly 6× the project's $20
short-term experimental allocation and well above the full $100 starting
capital, before any consideration of whether data expenditure should come
from capital at all. No purchase is authorised by this task, and none
occurred.

A second important finding: Norgate's own retail-facing "Premium Data"
product page (a related but seemingly distinct branding of the same
underlying ASX dataset, at a different domain) advertises only
*currently-listed* ASX historical prices with no delisted-securities option
visible on that specific page — inconsistent with Norgate's own
"Platinum" tier description on `norgatedata.com` itself. This is flagged as
an open question (§9), not resolved here, since contacting either vendor
is explicitly excluded from this task.

## 2. Comparison of universe definitions

### A. Historical index membership (e.g. point-in-time S&P/ASX 200 or All Ordinaries)

- **Survivorship bias:** low, if genuine point-in-time constituent history
  is used (a stock that was added and later removed/delisted still
  appears for the period it was a member).
- **Look-ahead bias:** moderate risk if index *reconstitution effective
  dates* are not applied correctly — index providers often announce
  changes ahead of the effective date, and getting this wrong silently
  reintroduces look-ahead bias into an otherwise bias-aware universe.
- **Selection bias:** real and structural, not eliminated — the ASX 200 (or
  All Ordinaries) construction rule itself is a liquidity/market-cap
  filter chosen by S&P DJI, not by the researcher; a momentum strategy
  tested only on index members implicitly inherits S&P DJI's own
  eligibility rules (free float, liquidity screens) as part of its universe
  definition, which may or may not match the intended research question.
- **Liquidity/capacity:** good — index membership rules themselves tend to
  select for liquidity, so this universe is close to realistically
  tradeable for most strategies at this project's capital scale.
- **Historical coverage:** the S&P/ASX 200 replaced the All Ordinaries as
  the primary benchmark in April 2000; S&P DJI's own methodology states
  that *"any date or time period prior to the index's Launch Date are
  considered back-tested"* and that back-tested history uses actual
  historical constituent-level data where available, falling back to a
  documented "Backward Data Assumption" otherwise. This means genuine,
  non-back-tested point-in-time history is strongest from 2000 onward, with
  earlier periods requiring extra scrutiny of whether backward assumptions
  were used (§9).
- **Practical acquisition cost:** uncertain — S&P DJI publishes an
  "S&P/ASX Stock Selection Data Product" brochure, confirming the product
  exists, but its content, historical depth and pricing could not be read
  (the brochure returned HTTP 403 to automated fetching); this is recorded
  as **QUOTE REQUIRED**, not free, not priced.
- **Suitability:** good default for benchmark-relative, capacity-aware
  strategies; introduces S&P DJI's own eligibility criteria as an
  unavoidable part of the universe definition.

### B. Historical full-market universe (all listed securities meeting a predeclared eligibility rule)

- **Survivorship bias:** potentially the lowest of the three, if the
  listing/delisting dates themselves are accurate and complete — every
  security that ever traded on ASX under the eligibility rule is included
  for its actual listed lifetime.
- **Look-ahead bias:** low, provided eligibility is evaluated using only
  data available as of each historical decision date (not current-day
  classifications applied retroactively).
- **Selection bias:** lowest of the three in principle, since there is no
  index-committee judgement involved — but in practice, a "predeclared
  eligibility definition" still has to be chosen by the researcher (e.g. a
  minimum market cap or listing-age filter), so selection bias is
  relocated to that choice rather than eliminated.
- **Liquidity/capacity:** worst of the three without a liquidity filter —
  the full ASX list includes many micro-cap and illiquid securities that
  are not realistically tradeable at any capital scale, let alone this
  project's.
- **Historical coverage:** ASX's own information services state that
  *"most information is available with a minimum of 10 years' history,
  with price data available to 1985,"* but a genuine historical *security
  master* (every ticker that ever listed, with listing/delisting dates)
  is not shown as a free, official ASX product; third-party commercial
  databases (Morningstar DatAnalysis Premium) claim delisted-company
  coverage from 1989 or 1990 depending on source (§3).
- **Practical acquisition cost:** depends entirely on which vendor's
  security master is used; see §3/§6.
- **Suitability:** best academic/unbiased starting point, worst
  out-of-the-box liquidity realism; needs approach C's filtering layered on
  top to be usable for most strategies.

### C. Liquidity-filtered historical universe (full listing history + point-in-time liquidity/market-cap filter)

- **Survivorship bias:** low, same as B, provided the underlying listing
  history is complete and accurate.
- **Look-ahead bias:** the main engineering risk of this approach — the
  liquidity/market-cap filter must be evaluated using only information
  that was knowable *as of* each historical decision date, not
  current-day or full-sample statistics. Done correctly, this is the
  most defensible approach for strategies like momentum that explicitly
  care about realistic executability; done carelessly, it is the easiest
  approach to accidentally corrupt with look-ahead bias.
- **Selection bias:** present but transparent and researcher-controlled
  (the filter rule is explicit and can be stated, unlike an index
  committee's judgement-based inclusion rules).
- **Liquidity/capacity:** best of the three, if the filter threshold is
  chosen appropriately for this project's capital scale — since the
  project trades with a small protected allocation, a liquidity filter
  tuned to realistic micro-capital execution is arguably more relevant
  than an index-membership filter tuned to institutional capacity.
- **Historical coverage:** inherits approach B's coverage question (which
  vendor supplies the underlying listing/delisting history), plus requires
  historical market-cap and traded-value/volume fields at each date, which
  is a stronger data requirement than B alone.
- **Practical acquisition cost:** same vendor dependency as B, with an
  additional field requirement (historical market cap, traded value/volume)
  that not every "historical prices" product necessarily includes.
- **Suitability:** best fit for momentum/value/quality strategies run at
  this project's capital scale, provided the look-ahead-bias risk in the
  filter construction is taken seriously and tested (e.g. via a dedicated
  unit test asserting that no future information reaches a historical
  filter decision, in the same spirit as MOM-001's existing chronological
  train/test discipline).

### Recommendation among the three

**Approach C (liquidity-filtered historical universe), built from a
genuine listing/delisting security master, is the preferred target design**
for momentum-style research at this project's scale — not because it is
free of bias, but because its remaining biases are the most transparent
and the most alignable with the project's actual capital constraints.
Approach A (index membership) is a reasonable, cheaper-to-reason-about
fallback if a full security master cannot be affordably obtained, since
index-membership data is somewhat more likely to be available via a
documented, licensable S&P DJI product, even though pricing for it remains
unconfirmed. Approach B is best treated as an input/ingredient for C, not
an end state, because of its weak liquidity realism on its own. None of
these is claimed to be a perfect universe; each still carries the
selection-bias caveat described above.

## 3. Historical-data provider comparison

(Full citations, access dates and exact quotes are in
[UNIV-001_source_register.md](../UNIV-001_source_register.md). This
section summarises the comparison; it does not repeat every quote.)

| Provider | Point-in-time constituents | Delisted securities | Historical depth (ASX) | Public pricing found | Suitability for this project |
|---|---|---|---|---|---|
| **Norgate Data** (`norgatedata.com`) | Yes — "Platinum" ASX tier explicitly lists historical index constituents | Yes — explicitly listed, back to 1992 | Daily prices back to 1992 (Platinum tier) | **Yes, confirmed**: AUD 346.50 / 6 months or AUD 630 / 12 months, ex-GST | Best-documented, cheapest *confirmed-price* survivorship-bias-free option found; still exceeds this project's data budget (§6) |
| **Premium Data** (`premiumdata.net`) | Not shown on its public retail pricing page | Not shown as an option on its public retail pricing page (describes itself as "Currently-listed" only) | Up to 1992 as a paid add-on, but only for currently-listed securities per the page read | Yes: ~AUD 30/month + AUD 90/180 one-time fees | Appears to be a related but more limited product line to Norgate's own Platinum tier; the inconsistency is unresolved (§9) |
| **S&P Dow Jones Indices** | A dedicated "S&P/ASX Stock Selection Data Product" brochure exists, confirming such a product is offered | Implied by index-membership history, not separately confirmed | Index itself launched April 2000 (replacing the All Ordinaries as primary benchmark); pre-launch periods are explicitly "back-tested," using actual data where available and a documented "Backward Data Assumption" otherwise | **Not found — QUOTE REQUIRED** (brochure PDF could not be read; institutional distribution channel, no public retail price) | Methodology is well-documented and credible; commercial access terms unknown |
| **LSEG / Refinitiv (Datastream)** | Possible via "Datastream Navigator," but a practitioner forum post reports point-in-time constituent requests sometimes returning no data, with LSEG support needed to resolve | Not confirmed from available sources | Not confirmed | **Not found — QUOTE REQUIRED**; institutional subscription product, not retail | Credible institutional option; reliability and exact Australian coverage unconfirmed from public sources, access clearly priced for institutions |
| **Bloomberg** | Yes, on-Terminal via an "As Of" date field / `MEMB` function; off-Terminal programmatic access requires a separate Enterprise Data/Data License product | Implied via historical constituent changes, not separately confirmed for ASX | Not confirmed for ASX specifically | **Partially found, dated/third-party**: one 2026 source estimates USD ~31,980/year for a single Terminal; clearly **QUOTE REQUIRED** for the data-only licence | Institutional-grade, well outside this project's budget on Terminal cost alone, independent of data-licence cost |
| **FactSet** | Not confirmed from available sources for ASX specifically | Not confirmed | Not confirmed | **Not found — QUOTE REQUIRED**; one dated third-party estimate (~USD 12,000–25,000/year for "the full product," not ASX-specific or current) | Same institutional cost class as Bloomberg; no ASX-specific point-in-time capability was confirmed |
| **Morningstar (DatAnalysis Premium)** | Not separately confirmed (product is oriented toward company research, not an explicit point-in-time constituent export) | Yes — multiple university library guides describe coverage of ASX-listed companies plus those delisted since 1989 or 1990 (sources disagree on the exact year) | "All companies listed on ASX" plus delisted since ~1989/1990; updated daily from ASX announcements | **Not found** — access is overwhelmingly via university library subscriptions; no individual/retail price found | Strong delisted-company coverage claim, but access route (library-mediated) and exact field set for a point-in-time universe build are unclear |
| **ASX itself** | No free, official historical constituent product found | Only a rolling ~6-month list of recently delisted entities is shown on ASX's own public pages; a full historical register is not published by ASX directly | Price data to 1985; most information "at least 10 years"; "Register of Sales" (trade-by-trade history) exists as a named product | **Not found — contact-only** ("contact these vendors directly to obtain ASX price and reference data") | Primary source for official listing facts, but not a self-service historical universe product; likely most useful as a cross-check/reference rather than a primary data source |
| **Siblis Research** | Yes, for the equity indices it covers — but **ASX/Australian index coverage is not confirmed**; the product page names no Australian index | Implied for covered indices only | Not stated on the page | **Yes, confirmed, currency ambiguous ("$" only, not stated as USD or AUD)**: "History Licence: $378 once" or "Annual: $576/yr" | Cannot be relied on for this project until ASX coverage is confirmed directly; currently an **unverified lead**, not a usable finding |

No provider was found whose public documentation unambiguously states:
(a) a confirmed price, AND (b) confirmed ASX-specific point-in-time index
or full-market coverage, AND (c) confirmed delisted-security history, all
three at once. Norgate's Platinum tier comes closest (confirmed price,
explicit delisted-securities and historical-index-constituents claims for
Australian Stocks specifically), which is why it is highlighted as the
standout finding of this investigation, notwithstanding the budget
mismatch in §6.

## 4. Data-quality and survivorship-bias considerations

- **Vintage and provenance discipline must extend to universe data, not
  just price data.** MOM-001's existing provenance pattern (checksummed
  reference files, recorded retrieval dates, explicit "provider data can
  change" caveats) is the right template to extend to any future universe
  source — a universe snapshot is itself a dataset with a vintage, and a
  later refresh of the same vendor's data is a new vintage, not a
  reproduction of a prior result, exactly as AGENTS.md already states for
  price data generally.
- **"Historical index constituents" is a claim that needs field-level
  verification before being trusted**, not just a marketing bullet point.
  Two vendors (Norgate, and implicitly S&P DJI's own index methodology)
  use this phrase, but neither's exact effective-dating convention
  (inclusive/exclusive of the announcement date vs. the effective date)
  was confirmed from public sources in this investigation. Getting this
  wrong is exactly how a "bias-aware" universe quietly reintroduces
  look-ahead bias.
- **Delisting-date precision matters as much as delisting-inclusion.**
  Morningstar's own documented coverage start date is inconsistently
  reported across university library guides (1989 vs. 1990) even for the
  same underlying product — a reminder that secondary descriptions of a
  vendor's coverage should not be treated as authoritative; only the
  vendor's own current documentation, read directly, should be relied on
  before any purchase decision.
- **A security that delists is not simply "removed"** — how its final
  return is computed (cash settlement, acquirer share-exchange ratio, a
  zero/total-loss writedown for an insolvency) materially changes
  backtested performance and must be an explicit, documented rule, not an
  implicit default. No provider's documentation reviewed here stated its
  delisting-return convention explicitly; this is listed as an outstanding
  question (§9) that must be resolved with primary vendor documentation
  before any universe is built, not assumed.

## 5. Delisting and corporate-action requirements

Any future universe build needs, at minimum:
- A delisting/suspension date distinct from the last traded price date.
- A documented delisting reason category (acquisition, insolvency,
  voluntary deregistration, compliance removal) — ASX's own "Register of
  Sales" and delisted-entity pages exist, but do not appear to expose this
  categorisation as a bulk historical dataset; Class's monthly "Companies
  Delisted from ASX" notices do record a reason per company and could be a
  useful free cross-check source, though not a bulk historical API.
- A delisting-return treatment rule (see §4) applied consistently and
  documented alongside the universe, not decided ad hoc per security.
- Corporate-action adjustment factors (splits, consolidations, bonus
  issues, demergers) consistent with whichever price series is paired with
  the universe — Premium Data's own documentation states ASX data is
  *"adjusted for capital events as per the official 'dilution factors'
  issued daily by the exchange,"* which is a specific, checkable claim
  worth re-verifying directly against ASX's own dilution-factor
  publication before relying on any vendor's adjusted series.
- Ticker/identifier history (a security's ASX code can change on
  relisting, restructuring, or rebranding) — not explicitly confirmed as
  covered by any vendor reviewed here; flagged as an outstanding question.

## 6. Licensing and price considerations

The project's capital constraints are unchanged and were not modified by
this task: AUD $50 long-term allocation, AUD $20 maximum short-term
experimental allocation, AUD $30 protected reserve never used for data
costs or losses. **No subscription or purchase is authorised by this
task, and none occurred.**

Measured against these constraints, every provider identified falls into
one of two categories:

1. **Confirmed price, clearly exceeds the project's entire data budget:**
   Norgate Data's Platinum ASX tier (AUD 630/year, or AUD 346.50/6 months)
   is roughly **6× the $20 short-term experimental cap**, and more than
   **6× the entire $100 starting capital** on its own — a one-year
   subscription alone would consume more than the whole project's capital
   before a single trade. This is true even though it is, by a wide
   margin, the cheapest *confirmed-price, survivorship-bias-explicit*
   option found in this investigation.
2. **Institutional/enterprise pricing, QUOTE REQUIRED, and self-evidently
   out of scope:** S&P DJI's data product, LSEG/Refinitiv Datastream,
   Bloomberg, and FactSet all fall here. Bloomberg Terminal cost alone
   (~USD 31,980/year per the one dated estimate found) is roughly 320× the
   project's entire starting capital; this is not a close call.

A genuinely low-cost public/academic route (Morningstar DatAnalysis
Premium via a university library subscription) was identified as a
possibility, but this project has no stated university affiliation, and no
individual/retail price for this product was found in public sources —
this is recorded as **QUOTE REQUIRED / access route unclear**, not
free.

**Economic conclusion:** at the project's current capital scale, no
provider identified in this investigation can be purchased within budget.
The cheapest credible, best-documented option (Norgate Platinum) is a
realistic target *if and when* the project's data budget is reconsidered
separately from trading capital — consistent with MICRO-002's own
conclusion for a different data source, that *"the AUD 20 short-term
experimental allocation is not a data budget and cannot justify a
recurring data service by itself."* This project should not treat
trading capital and research-data budget as the same pool, and any future
decision to actually subscribe to a universe data source is a distinct
decision from this feasibility finding.

## 7. Proposed point-in-time data schema

See the dedicated schema document:
[UNIV-001_universe_specification.md](UNIV-001_universe_specification.md).

## 8. Recommended next milestone

Given the economic conclusion in §6, the recommended next milestone is
**not** a data purchase. It is a narrow, free/low-cost verification step:
confirm, directly from each vendor's own current documentation (Norgate's
own FAQ/specification pages, not third-party commentary), exactly what
Norgate's "historical index constituents" and "delisted securities back to
1992" fields contain at the record level (effective-dating convention,
delisting-return treatment, ticker-history handling) — the specific
unresolved items in §4/§9 — before any future decision to actually budget
for a subscription. This keeps the project's provenance/verification
discipline intact (never assume a vendor's marketing bullet matches its
actual field-level data) without spending anything.

## 9. Outstanding questions

- Does Norgate's Platinum tier's "historical index constituents" use
  announcement dates or effective dates for membership changes? Not
  stated in any source reviewed here.
- What is Norgate's documented delisting-return treatment (cash
  settlement, acquirer exchange ratio, total-loss writedown)? Not found.
- Why does Premium Data's own public retail pricing page show only
  "currently-listed" ASX data with no delisted-securities option, when
  Norgate's own site advertises exactly that capability under its
  "Platinum" tier for the same underlying Australian market? Is Premium
  Data a different (older/more limited) product line, a different pricing
  page for the same underlying data, or something else? Unresolved — not
  investigated further here since vendor contact is excluded.
- What does the S&P DJI "S&P/ASX Stock Selection Data Product" actually
  contain, and at what price? The brochure could not be read (HTTP 403);
  this is a real documented product, not a hypothetical one, and is worth
  revisiting with a different access method (e.g. a saved local copy) in a
  future session, without contacting S&P DJI.
- Does Siblis Research's historical constituent-change database cover any
  Australian index at all? Not stated on the page read; unconfirmed, so
  not relied upon in this feasibility assessment.
- Does LSEG/Refinitiv Datastream reliably return point-in-time Australian
  index constituents, given the one practitioner forum report of a failed
  / NA request for a historical constituent pull? Unconfirmed either way
  from public sources.
- What would Morningstar DatAnalysis Premium cost for non-university
  access, if that is even offered? Not found in public sources.

## Conclusion

**CONDITIONAL GO** — for continued free, documentation-level verification
of the Norgate Platinum product's exact field-level coverage (§8), and for
treating Approach C (liquidity-filtered historical universe, §2) as the
design target for if and when a universe source is actually budgeted.
**NO GO** on any purchase, subscription, vendor contact, or universe-data
acquisition at this time — every identified provider's cost either clearly
exceeds this project's entire capital base, or is undisclosed
institutional/QUOTE-REQUIRED pricing. **NO GO**, independent of the above,
on rerunning or reinterpreting MOM-001 against any new universe, on any
new strategy implementation, and on any trading or paper-trading activity.
UNIV-002 is not initiated; this is the project owner's decision, to be
made after reviewing this report.
