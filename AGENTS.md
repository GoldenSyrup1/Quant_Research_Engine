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
- Define chronological train/test periods before reviewing results; never tune strategy choices on the held-out test period.
- Keep deterministic implementation tests independent of network services and live data providers.
- Preserve data provenance, file checksums, audit results, and immutable experiment configurations for every reported backtest.
- Treat refreshed provider data as a new data vintage; do not describe a run as reproduced unless recorded input checksums match.
- Report data anomalies for review. Do not silently interpolate, remove, or repair suspicious observations.
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

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
