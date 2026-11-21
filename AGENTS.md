# Quant Research Engine: Project Instructions

## Purpose
Build a rigorous, educational and experimentally validated quantitative equity research engine. The objective is to investigate whether systematic strategies can generate repeatable returns after realistic costs and risk, not to assume profitability.

## Capital Constraints
- Initial capital: AUD $100.
- Long-term investment allocation: $50.
- Short-term experimental allocation: $20 maximum.
- Protected reserve: $30.
- The protected reserve must never be used to cover investment losses.
- No CFDs, leverage, margin, borrowing, options, or gambling-style speculation.
- No financial transactions without explicit user approval.

## Research Principles
- Treat profitability as an unproven hypothesis.
- Prioritise data quality and methodological integrity.
- Avoid look-ahead bias, survivorship bias, selection bias and data leakage.
- Account for brokerage, spreads, slippage and other relevant costs.
- Distinguish gross returns from net returns.
- Avoid fitting parameters to the testing period.
- Use out-of-sample evaluation where feasible.
- Compare strategies against appropriate benchmarks.
- Report limitations and uncertainty.
- Never fabricate data, results, tests or performance.

## Workflow
1. Research the hypothesis.
2. Establish data requirements.
3. Build the strategy.
4. Validate the implementation.
5. Backtest.
6. Evaluate costs, risks and benchmarks.
7. Perform robustness and out-of-sample testing.
8. Paper trade.
9. Review evidence.
10. Obtain explicit approval before any deployment involving actual capital.

## Collaboration
- Explain significant changes.
- Keep code modular, understandable and maintainable.
- Preserve existing files unless modification or deletion is justified.
- Test modifications where possible.
- Report actual test results.
- Clearly distinguish verified results from assumptions.
- Do not execute financial transactions.
- Do not introduce live-trading functionality without explicit discussion and approval.

## Current Project
We are developing an ASX-focused momentum research engine. The initial hypothesis uses a 126-trading-day momentum window excluding the most recent 21 trading days, selecting the top 5 stocks with equal weighting and monthly rebalancing.

This strategy is exploratory and has not been validated.