# Quant Research Engine v1

An educational, research-first ASX momentum backtest. It has no live trading functionality. Results are exploratory and depend on the quality and historical coverage of the input data.

## Setup

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Phase 2: reproducible research workflow

Use a new experiment ID for every run. The engine refuses to overwrite an existing experiment directory.

1. Download the universe and benchmark. This also writes `data/provenance.json`, recording the source, retrieval time, parameters, range, checksum, adjustment setting, and provider limitations for every successful download.

   ```bash
   python src/download_data.py --tickers BHP.AX CBA.AX CSL.AX WES.AX WOW.AX MQG.AX FMG.AX TLS.AX --start 2015-01-01
   ```

2. Audit the downloaded files. The audit is read-only: it reports rather than repairs missing data, suspect returns, duplicate or invalid dates, invalid prices, incomplete history, checksums, and reasonably detectable weekday gaps. Public holidays are included in the gap report because the audit does not have an exchange holiday calendar; review those dates before treating them as data problems.

   ```bash
   python src/data_audit.py --tickers BHP.AX CBA.AX CSL.AX WES.AX WOW.AX MQG.AX FMG.AX TLS.AX --benchmark STW.AX
   ```

   This writes `data/audit_report.json`.

3. Run a named experiment. Its configuration fixes the existing strategy definition: 126-session lookback, 21-session skip, five equal-weight holdings, monthly rebalancing, next-session-close execution, and 10 bps per one-way turnover.

   ```bash
   python src/experiment.py --experiment-id asx-momentum-20261123 --tickers BHP.AX CBA.AX CSL.AX WES.AX WOW.AX MQG.AX FMG.AX TLS.AX --benchmark STW.AX
   ```

4. Find the complete run in `experiments/asx-momentum-20261123/`. It contains `configuration.json`, `data_audit.json`, gross and net curves and returns, weights, turnover, costs, metrics, benchmark comparison, and chronological train/test results.

5. Reproduce a prior experiment with its recorded configuration and a new ID. The engine verifies every recorded input checksum and stops if any file changed.

   ```bash
   python src/experiment.py --config experiments/asx-momentum-20261123/configuration.json --experiment-id asx-momentum-20261123-reproduction
   ```

   The recorded `data_references` make this a same-input reproduction. Downloading refreshed provider data changes checksums, so it is a new data vintage rather than a reproduction of the earlier result.

The downloader requests Yahoo Finance history with `auto_adjust=True`; `Close` is therefore the adjusted price series used for returns. It also requests `STW.AX`, the State Street SPDR S&P/ASX 200 ETF, as the broad-market comparison. STW seeks to track the S&P/ASX 200 index ([fund description](https://www.ssga.com/au/en_gb/individual/etfs/state-street-spdr-spasx-200-etf-stw)). Yahoo Finance retrieval is not guaranteed. If its file is absent, the backtest records that the benchmark is unavailable and does not substitute a proxy. The ETF benchmark starts only where its downloaded history is available; align comparisons over common dates before interpreting relative results.

## Strategy and timing

- Sample ASX universe from the tickers supplied by the user; current membership is not a survivorship-bias-free historical universe.
- Momentum score at decision close `t`: adjusted close at `t-21` divided by adjusted close at `t-147`, minus one (126 trading-day measurement window with the most recent 21 sessions skipped).
- On the final observed trading date of each calendar month, rank eligible stocks by score and target equal weights in up to five names. A ticker must have a valid decision-date close and complete lookback data to rank.
- **Execution convention:** decisions use data through the month-end close. Target weights are implemented at the next observed session's close. Daily close-to-close returns through that execution date belong to the prior holdings; the new target first earns the following close-to-close return. This conservative one-session delay avoids crediting a close-based signal with a return earned before it could be executed.
- Holdings remain invested between monthly executions and actual portfolio weights drift with each asset's returns. The backtest does not reset weights daily to monthly targets.
- Weight is not carried through a missing price by forward-fill. If an asset being held has a missing daily return, the run stops with an explicit error because its return cannot be measured reliably.
- If fewer than five stocks have valid scores, the portfolio equally weights the available names; if none qualify, it remains in cash until the next valid rebalance.

## Turnover and costs

At each execution close, turnover compares the target weights with the actual pre-trade holdings after that session's market move. It includes cash as a portfolio asset with weight `1 - sum(risky weights)`. One-way turnover is `0.5 * sum(abs(new_weight - old_weight))` across all risky assets and cash. Thus cash to fully invested is 100%, a fully invested swap from portfolio A to disjoint portfolio B is 100%, fully invested to cash is 100%, and unchanged holdings are 0%. The 10 bp assumption is charged once per unit of one-way turnover: `cost_fraction = one_way_turnover * 0.001`. Cost is deducted on the execution close's post-market portfolio value and translated to a return contribution on the daily starting NAV. Gross returns exclude this cost; net returns deduct it. The daily attribution output records turnover, cost return, gross return, and net return. This simple model omits commissions, bid-ask spread, market impact, taxes, and fund fees.

## Evaluation periods and benchmark comparison

The engine reports gross and net daily returns, gross and net equity curves, and separate gross and net performance metrics. It also makes a chronological 70/30 train/test split of the daily return series and writes `out_of_sample_metrics.csv`. The test period is held out for evaluation: do not use test results to tune lookback, skip, portfolio size, costs, or other choices. This split is an evaluation aid, not evidence the strategy is profitable or validated. Fix all research choices before examining test-period performance.

The STW.AX comparison is computed only on dates where both the strategy net return and an observed STW.AX close-to-close return exist. Benchmark closes are reindexed to the strategy's dates before returns are calculated, so gaps are not forward-filled and gap-spanning multi-session returns are not treated as daily returns. `benchmark_metrics.csv` reports the exact inclusive start and end dates and common observation count; `benchmark_comparison.csv` contains the matched daily returns and rebased curves. If there are no overlapping valid returns, the comparison is empty and the status file says so.

## Data checks and limitations

The loader rejects duplicate dates, non-positive or infinite prices, and malformed price files. Missing prices are not filled. A momentum score is eligible only when every close in its full 127-observation measurement window (126 intervals) is valid; insufficient or incomplete history produces no score. Missing returns for held assets stop the backtest rather than being treated as zero. Different start/end dates are retained, with the benchmark comparison restricted to actual overlapping valid daily observations. Yahoo Finance adjusted data and the selected current sample do not fix survivorship, delisting, ticker-history, or provider data-quality biases.

The original `src/backtest_momentum.py` command remains available for exploratory use. Prefer `src/experiment.py` for research results because it preserves an audit and configuration with each output. Metrics include cumulative return, CAGR based on 252 sessions per year, annualised sample volatility, zero-risk-free-rate Sharpe, maximum drawdown, one-way turnover, and modeled transaction-cost drag. Risk-free interest on uninvested cash is assumed to be zero. Run deterministic offline tests with `python -m unittest discover -s tests -v`.

Do not tune parameters against the evaluation period. Use point-in-time constituents, out-of-sample evaluation, data validation, and robustness checks before drawing conclusions. No financial transactions are made by this project.
