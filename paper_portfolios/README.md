# Paper-trading portfolio configurations (PAPER-001)

This directory holds version-controlled, effective-dated configuration
files for every paper (simulated) portfolio in the project. Each file is
loaded by `src/paper_trading/config.py` and turned into a funded, but
not-yet-invested, `PaperPortfolio` via `build_portfolio()`.

## What a config is, and is not

A config declares a `target_allocation` (the intended split across
instruments) and a starting cash balance. **Loading a config never places
a trade.** `build_portfolio()` records only the initial cash deposit;
holdings and unit quantities are never generated here. This is
deliberate: a buy can only be recorded once an actual price observation
and a valuation timestamp exist, per PAPER-001's own requirement not to
assume a price. See `src/paper_trading/execution.py` for how a fill is
actually produced from such an observation.

## Portfolios

| Config | Mandate | Starting balance | Restricted |
|---|---|---:|---|
| `LT-BAL.json` | Long-term shadow comparison | A$50 | No |
| `LT-GROWTH.json` | Long-term shadow comparison | A$50 | No |
| `LT-EQUITY.json` | Long-term shadow comparison | A$50 | No |
| `LT-CASH.json` | Long-term cash benchmark | A$50 | No |
| `ST-PAPER.json` | Short-term experimental | A$20 | No |
| `RESERVE-CONTROL.json` | Protected-reserve control | A$30 | **Yes** |

The four `LT-*` portfolios are **independent model comparisons**, each
notionally funded with its own A$50 — they are not four slices of one
shared A$50 budget. This mirrors how the project's real capital allocation
works (a single A$50 long-term decision, not four), but keeping them
separate in the paper engine lets different model portfolios be compared
side by side without conflating real capital-allocation decisions with a
simulation convenience.

`RESERVE-CONTROL` sets `"restricted": true`, which `PaperPortfolio`
enforces at the code level (`RestrictedPortfolioError` on any attempted
buy, sell or withdrawal) — not just by convention. It exists to make the
"never touch the protected reserve" rule mechanically unbreakable within
this simulation, not merely documented.

## How genuine market observations will eventually be entered

This task (PAPER-001) does not download, acquire, or enter any real market
data; it builds the mechanism, not the data. When real observations are
entered in a future, separately authorised step, they must be:

1. Constructed as `src.paper_trading.ledger.PriceObservation` records,
   one per instrument/date/price-type, each carrying:
   - `source` (e.g. the data provider or exchange),
   - `retrieved_at` (when the observation was actually fetched — distinct
     from the market date),
   - `data_vintage` (an explicit vintage label; a later refresh of the
     same date from the same source is a new vintage, never treated as a
     reproduction, per this project's existing provenance convention in
     `src/download_data.py` and `data/provenance.json`),
   - `source_reference` (a checksum or stable reference to the file/page
     the price came from), and
   - `transformations` (e.g. if a price was adjusted for a split before
     being recorded here).
2. Passed explicitly to `src.paper_trading.execution.simulate_market_fill`
   (for a simulated trade) or `src.paper_trading.metrics.nav` /
   `allocation` (for valuation) — there is no implicit "current price"
   lookup anywhere in this package; every valuation and every fill
   requires the caller to supply the exact observations to use.
3. Never a NAV-type observation used to produce a simulated fill —
   `simulate_market_fill` raises `ExecutionError` if NAV is the only
   observation available, since NAV is a valuation concept, not an
   executable ASX price.
4. Never fabricated. Synthetic fixtures used in this project's test suite
   (`tests/test_paper_*.py`) are clearly labelled `source="synthetic-fixture"`
   and must never be confused with, or substituted for, an actual market
   observation in any report produced from this engine.

No broker connection, account, or data subscription is used or required to
enter observations this way — they can come from any source the project
owner chooses to type in or paste manually, exactly as experiment inputs
are already checksummed and recorded elsewhere in this repository.
