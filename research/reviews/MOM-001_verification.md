# MOM-001 Independent Results Verification

**Review date:** 23 November 2026  
**Verdict:** **VERIFIED WITH LIMITATIONS**

## Summary

MOM-001's stored accounting and reported metrics reproduce from its saved weights, daily returns, turnover, costs, benchmark comparison, and unchanged input files. No calculation discrepancy was found beyond floating-point rounding. The review found no implementation defect that invalidates the recorded result.

The result remains exploratory. The historical universe is a small, current-stock sample, and the single chronological split is not sufficient evidence of a durable strategy effect.

## Inputs and configuration

The stored `configuration.json` fixes the approved specification:

- Eight-stock universe: BHP.AX, CBA.AX, CSL.AX, WES.AX, WOW.AX, MQG.AX, FMG.AX, and TLS.AX.
- 126-session momentum measurement, excluding the most recent 21 sessions.
- Top five eligible securities, equal-weighted, monthly at the final observed trading session.
- Signal at close, execution at the next session close, and a 10 bp cost per unit of one-way turnover.
- STW.AX benchmark and a 70/30 chronological split.

The experiment records nine SHA-256 input checksums, source provenance, retrieval parameters, and its data audit. Current input-file checksums matched those stored references during the experiment verification.

## Accounting verification

### Daily return, weights, cash, and missing observations

I independently calculated each close-to-close stock return from the stored CSV prices. For every date, I applied the previous close's stored portfolio weights to those returns. The maximum absolute difference from `daily_returns.csv` was `1.39e-17` for gross returns and `1.39e-17` for net returns, which is ordinary floating-point precision.

Weights drifted between trades as expected. On non-trade days, the maximum absolute difference between independently drifted weights and the saved next-close weights was `5.55e-17`. Risky weights summed from 0.0 during the formation period to 1.0000000000000007 thereafter; there were no negative holdings. No held asset had a missing return.

The first investment occurred on 1 September 2015 after the 31 August 2015 decision close. This is consistent with a 126-session lookback plus 21-session skip and next-session-close execution. The engine remained in cash before a valid first signal.

### Signal timing and look-ahead check

I recalculated momentum scores as `price[t-21] / price[t-147] - 1`, requiring all 127 observations spanning the 126 return intervals. For each of the 135 execution events, the stored holdings were the expected equal-weight top five from the immediately preceding decision close. There were zero ticker-selection or timing mismatches.

No score requires data after its decision close. New targets were applied only at the next observed session close, and their returns began in the following close-to-close interval. This review found no look-ahead bias in signal formation or execution timing.

### Turnover and costs

I independently reconstructed the pre-trade drifted portfolio, including residual cash, then calculated one-way turnover as half the absolute change across risky assets and cash. The maximum absolute difference from `turnover.csv` was `3.61e-16`.

- Initial cash-to-portfolio deployment: 1.0000 one-way turnover.
- Rebalance events: 135.
- Cumulative one-way turnover: 21.75367835.
- Maximum single-event one-way turnover: 1.0000.

I recalculated the cost as post-market portfolio growth times one-way turnover times 0.001. The maximum absolute difference from `transaction_costs.csv` was `3.79e-19`. The total of daily modeled cost-return contributions was 0.02179476, matching the saved net metric.

The reported `transaction_cost_cumulative_return_drag` is the arithmetic sum of daily cost-return contributions. It is useful for attribution but is not the compounded difference between gross and net terminal wealth; readers should not interpret it as that separate quantity.

## Metric verification

Independent calculations from saved daily returns matched `metrics.csv` exactly to displayed precision.

| Metric | Gross | Net |
|---|---:|---:|
| Total return | 6.44967120 | 6.28934020 |
| CAGR | 18.2887% | 18.0737% |
| Annualised volatility | 16.7643% | 16.7630% |
| Sharpe ratio, 0% risk-free rate | 1.08597 | 1.07518 |
| Maximum drawdown | -25.1472% | -25.1482% |
| Cumulative one-way turnover | 21.75367835 | 21.75367835 |
| Arithmetic sum of modeled cost returns | 0.00000000 | 2.179476% |

The independent formulas used 252 trading sessions per year, sample daily volatility (`ddof=1`), a zero risk-free rate, and drawdown from the running equity maximum. They reproduce the saved formulas.

## Train/test integrity

The split uses `int(3013 * 0.70) = 2109` daily observations:

| Period | Dates | Observations | Net total return | Net CAGR | Net Sharpe | Net maximum drawdown |
|---|---|---:|---:|---:|---:|---:|
| Train | 2015-01-02 to 2023-05-03 | 2,109 | 4.09546104 | 21.4786% | 1.16911 | -25.1482% |
| Test | 2023-05-04 to 2026-11-23 | 904 | 0.43055558 | 10.4965% | 0.81620 | -12.3958% |

The first test-day return uses the five holdings carried from the prior train close and has zero turnover. That is appropriate for a continuous chronological simulation: a live strategy would carry positions across the calendar boundary. Early test-period signals also use historical observations from before the split, as a rolling momentum strategy should. The review found no use of observations after each signal decision date.

The split should not be described as a fully independent parameter-selection exercise. No parameters were fitted in the train period; the split is a chronological performance partition of fixed rules. The test period is about 904 sessions, or roughly 3.6 years, which is useful but limited for a monthly strategy with 135 total rebalance events and a highly concentrated universe.

## Benchmark verification

I independently built STW.AX close-to-close returns on the union calendar, then retained only dates with both strategy net and benchmark returns. The reconstructed values exactly match `benchmark_comparison.csv`:

- Comparison period: 2015-01-05 to 2026-11-23.
- Common valid daily observations: 3,010.
- STW.AX total return: 1.50874483.
- STW.AX CAGR: 8.0048%.
- STW.AX annualised volatility: 14.5787%.
- STW.AX Sharpe ratio: 0.60153.
- STW.AX maximum drawdown: -34.3118%.

STW.AX has no stored observation on 24 October 2025. It is absent from the benchmark comparison, and 27 October 2025 is also excluded because a valid one-day return cannot be calculated across the missing close. No price was filled, fabricated, or converted into a multi-session daily return.

The comparison is mechanically fair on common valid dates and uses adjusted daily price series for both sides. It remains economically limited: it compares a small, equal-weighted current stock sample with a broad market ETF, excludes direct benchmark trading costs, and inherits the adjusted-price methodology and provider limitations of Yahoo Finance.

## Material limitations

1. **Survivorship and historical-universe bias:** the eight names are a current hand-selected sample, not point-in-time ASX constituents. Delisted, acquired, or historically ineligible securities are absent.
2. **Concentration:** five holdings are selected from only eight candidates. The result can be driven by a small number of names, sector exposures, and individual corporate events.
3. **Adjusted-price data:** Yahoo Finance auto-adjusted closes simplify splits and distributions but do not provide an independently validated corporate-action dataset, tax treatment, exact distribution timing, or tradable execution prices.
4. **Corporate-event sensitivity:** FMG.AX's genuine +23.69% move on 7 March 2016 remains in the data. A concentrated strategy can be materially affected by such events.
5. **Costs are incomplete:** the fixed 10 bp turnover model does not include brokerage minimums, bid-ask spread, market impact, taxes, liquidity constraints, or inability to trade at closing prices.
6. **Formation-period treatment:** the strategy is in cash before its first eligible signal, while the benchmark is invested over the broader comparison period. This is an explicit strategy-accounting choice, but it affects economic interpretation of relative results.
7. **Test evidence remains limited:** the 3.6-year test period and one static split do not establish robustness across regimes or validate future performance.

## Critical implementation issues

No critical defect was identified in the stored MOM-001 implementation or results. The cost-drag label and the train/test terminology should be read with the interpretation stated above. These are reporting and methodology limitations, not discrepancies in the stored calculations.

## Verdict

**VERIFIED WITH LIMITATIONS.** The saved MOM-001 outputs are internally consistent with the approved configuration and recorded input files. The result supports further research and robustness testing only; it does not establish profitability, tradability, or suitability for paper or live trading.
