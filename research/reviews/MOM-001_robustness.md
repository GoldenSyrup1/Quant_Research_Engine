# MOM-001 Robustness Assessment

**Review date:** 23 November 2026  
**Source:** immutable `experiments/MOM-001/` inputs and outputs  
**Scope:** post-experiment sensitivity analysis only; MOM-001 was not modified or overwritten.

## Executive summary

MOM-001's historical result remains positive under the tested 25, 50, and 100 bp one-way-turnover cost assumptions. It is nevertheless materially sensitive to the current selected universe and to the period examined. Removing FMG.AX produces the largest leave-one-out deterioration, and the 2023–2026 partial period is much weaker than 2019–2022.

The moving-block bootstrap of the saved net returns produces positive simulated CAGRs in all 2,000 paths. This result is conditional on resampling the observed return history under a stationarity assumption. It does not include survivorship bias, universe-selection uncertainty, execution frictions beyond the modeled costs, or future regime change.

The evidence is therefore **inconclusive regarding durability**. It supports further robustness research, not parameter selection, paper trading, or capital deployment.

## Methodology

All baseline calculations use recorded MOM-001 gross daily returns, net daily returns, one-way turnover, weights, source prices, and the stored STW.AX comparison. The analysis code is in `src/robustness.py`; it does not write into `experiments/MOM-001/`.

- **Costs:** saved gross daily return minus `((1 + gross return) * one-way turnover * cost rate)`, which is the recorded MOM-001 cost convention.
- **Leave-one-out:** remove one ticker from the eight-name current candidate universe at a time and apply the same fixed MOM-001 rules: 126/21 momentum, top five, equal weight, monthly rebalance, next-close execution, and 10 bp cost. These are current-universe sensitivity calculations, not point-in-time-universe backtests.
- **Periods:** three predeclared, non-overlapping calendar blocks: 2015–2018, 2019–2022, and 2023–2026 partial. They were not selected for performance.
- **Risk distribution:** saved net daily returns and monthly compounded net returns. Exposure statistics use stored post-close weights.
- **Bootstrap:** 2,000 seeded moving-block paths, 21 sessions per block, seed `20261123`, each with the same 3,013-session length as MOM-001.

## 1. Transaction-cost sensitivity

| One-way cost | Total return | CAGR | Sharpe | Maximum drawdown | Arithmetic cost-return sum |
|---:|---:|---:|---:|---:|---:|
| 10 bp | 628.93% | 18.07% | 1.075 | -25.15% | 2.18% |
| 25 bp | 605.52% | 17.75% | 1.059 | -25.15% | 5.45% |
| 50 bp | 568.14% | 17.22% | 1.032 | -25.15% | 10.90% |
| 100 bp | 499.13% | 16.15% | 0.977 | -25.16% | 21.79% |

Costs reduce returns and Sharpe smoothly. The modeled strategy remains historically positive at 100 bp, but this does not establish that 100 bp captures actual costs for this universe. The cost-return sum is an arithmetic daily attribution, not the compounded gross-to-net terminal-wealth difference.

Train and test cost sensitivity:

| Cost | Train net total / CAGR / Sharpe | Test net total / CAGR / Sharpe |
|---:|---|---|
| 10 bp | 409.55% / 21.48% / 1.169 | 43.06% / 10.50% / 0.816 |
| 25 bp | 397.67% / 21.14% / 1.154 | 41.77% / 10.22% / 0.797 |
| 50 bp | 378.47% / 20.57% / 1.128 | 39.64% / 9.75% / 0.766 |
| 100 bp | 342.22% / 19.44% / 1.075 | 35.48% / 8.83% / 0.702 |

## 2. Concentration and constituent sensitivity

| Excluded ticker | Net total return | CAGR | Sharpe | Maximum drawdown |
|---|---:|---:|---:|---:|
| None, MOM-001 baseline | 628.93% | 18.07% | 1.075 | -25.15% |
| BHP.AX | 471.88% | 15.70% | 0.987 | -25.15% |
| CBA.AX | 530.60% | 16.65% | 1.002 | -25.15% |
| CSL.AX | 485.86% | 15.94% | 0.957 | -29.42% |
| WES.AX | 519.42% | 16.48% | 0.984 | -26.13% |
| WOW.AX | 586.94% | 17.49% | 1.021 | -29.68% |
| MQG.AX | 481.97% | 15.87% | 0.980 | -22.14% |
| FMG.AX | 301.57% | 12.33% | 0.836 | -31.01% |
| TLS.AX | 530.23% | 16.65% | 0.973 | -25.15% |

Every leave-one-out result remains positive in this historical sample, but the variation is substantial. Excluding FMG.AX reduces CAGR by 5.74 percentage points and produces the lowest return and Sharpe. This is consistent with the independently approved 7 March 2016 FMG move being meaningful, and it demonstrates constituent dependence.

The arithmetic sum of daily gross-return contributions also places FMG.AX first at 0.7133, followed by CBA.AX at 0.3278 and BHP.AX at 0.2846. These are descriptive contributions, not compounded attribution, so they should not be added to infer terminal wealth.

Stored-weight exposure was generally close to the five-name equal-weight intent: mean active holdings 4.72 including the initial cash formation period, mean largest weight 19.72%, 95th-percentile largest weight 22.19%, and maximum largest weight 25.82% after drift. Mean HHI was 0.189 and the 95th percentile was 0.201.

## 3. Period sensitivity

| Fixed calendar period | Net total return | CAGR | Sharpe | Maximum drawdown | Annualised volatility |
|---|---:|---:|---:|---:|---:|
| 2015–2018 | 91.68% | 17.57% | 1.135 | -10.94% | 15.29% |
| 2019–2022 | 156.11% | 26.36% | 1.230 | -25.15% | 20.79% |
| 2023–2026 partial | 48.49% | 10.62% | 0.831 | -12.40% | 13.20% |

The result is positive across these fixed blocks, but the most recent partial block has substantially lower CAGR and Sharpe than the prior block. This weakens any claim that the full-period average is stable through time.

## 4. Risk and return distribution

The worst ten daily net returns were concentrated in March 2020. The worst was -7.11% on 27 March 2020; the next four were -6.53%, -6.40%, -6.34%, and -5.90%. The worst monthly net return was -11.29% in March 2020, followed by -9.52% in January 2022 and -6.99% in February 2020.

The longest consecutive underwater period was 319 trading sessions, and the series ended below its prior high-water mark. This duration measure is distinct from maximum drawdown depth.

As a descriptive tail-dependence test, setting the single best saved net daily return to zero lowers total return from 628.93% to 568.75%. Setting the five best days to zero lowers it to 408.53%; setting the ten best days to zero lowers it to 314.69%. This is not a tradable counterfactual and does not identify the source of those days, but it shows that the compounded outcome depends meaningfully on a small set of positive observations.

## 5. Benchmark and comparative analysis

The existing STW.AX comparison remains unchanged: 3,010 common valid daily return observations from 5 January 2015 through 23 November 2026. The 24 October 2025 STW.AX observation is absent and neither it nor the next session's unmeasurable one-day benchmark return was filled.

| Aligned-date metric | Strategy net | STW.AX |
|---|---:|---:|
| Total return | 628.54% | 150.87% |
| CAGR | 18.09% | 8.00% |
| Annualised volatility | 16.77% | 14.58% |
| Sharpe, 0% risk-free rate | 1.076 | 0.602 |
| Maximum drawdown | -25.15% | -34.31% |

The annualised mean active return was 9.27%, tracking error was 9.97%, and the historical information ratio was 0.930. These are descriptive aligned-date results. They do not correct the current-universe selection bias or make the small equal-weight stock sample economically identical to a broad ASX ETF.

## 6. Statistical uncertainty

The 21-session moving-block bootstrap preserved short-range daily dependence within each sampled block. Its 95% percentile intervals were:

| Statistic | 2.5th percentile | Median | 97.5th percentile |
|---|---:|---:|---:|
| Total return | 205.80% | 670.12% | 1,915.64% |
| CAGR | 9.80% | 18.62% | 28.56% |
| Sharpe | 0.627 | 1.118 | 1.622 |

All 2,000 sampled paths had positive total return, CAGR, and Sharpe. This is conditional evidence about the distribution represented by the observed history. It is not a probability of future profitability because the method assumes the observed blocks are representative and resamples neither ticker selection nor structural market changes. The survivorship and concentration limitations make the bootstrap notably more optimistic than a complete uncertainty assessment.

## Limitations and conclusion

This assessment does not eliminate the limitations already recorded for MOM-001: eight current selected tickers, five-name concentration, no point-in-time constituent history, adjusted Yahoo Finance prices, unmodeled taxes and liquidity costs, closing-price execution, and a single partial 3.6-year test period.

Cost sensitivity and fixed-period results add some support that the historical result is not dependent on the exact 10 bp assumption or one calendar block. Constituent sensitivity, especially the FMG.AX exclusion, and the lower recent-period performance weaken confidence in broad generalisation. The bootstrap is conditional and cannot overcome those design limitations.

**Conclusion:** the evidence remains **inconclusive**. It strengthens the case for pre-specified follow-up validation and broader point-in-time-universe research, while providing no basis for optimisation, paper trading, or deployment.
