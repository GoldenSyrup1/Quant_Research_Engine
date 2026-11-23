# MICRO-001 candidate hypothesis register

These are research hypotheses, not strategies, recommendations or evidence of
profitability.  Rank reflects feasibility of *testing* after the data gate, not
expected return.  Every test must separate a mid-price prediction from an
executable, net-of-cost result.

| Rank | Hypothesis | Economic rationale and variables | Outcome / horizons | Minimum data | Main biases, competing explanations and execution obstacle | Falsification criterion |
|---:|---|---|---|---|---|---|
| 1 | H5: execution optimisation | Liquidity/spread/session state may affect realised execution quality. Variables: prevailing spread, depth, volatility, time and order size. | Arrival-price or midpoint shortfall; minutes / longer intraday. | Timestamped trade/quote data; order-book data improves inference. | Selection of favourable times, unobserved routing, fill assumptions, spread/impact/minimum fees. | Under predeclared costs and conservative fills, no alternative rule improves a fixed arrival-price benchmark out of sample. |
| 2 | H3: liquidity-shock reversal | Temporary depletion/widening may revert when liquidity normalises. Variables: spread, quoted depth, trade rate, volatility. | Future midpoint and executable return; 30 s to minutes. | Sequenced MBP or reliable quotes plus trades, session labels. | News/information shocks, stale quotes, selection after the event, crossing spread. | Conditional response is indistinguishable from zero or is consumed by a conservative execution-cost bound. |
| 3 | H2: trade-flow imbalance | Concentrated aggressive trade flow may move prices temporarily. Variables: signed volume proxy, trade rate, price response. | Midpoint/executable move; 1–30 s. | Trades with conditions and quotes; documented sign-classification rule. | Trade-sign error, hidden liquidity, venue fragmentation, autocorrelation and costs. | Predefined signed-flow measure has no stable association beyond spread/cost after out-of-sample testing. |
| 4 | H1: order-book imbalance | Uneven displayed depth may precede a local mid-price change. Variables: bid/ask depth by level, imbalance, spread, volatility. | Mid-price move; 100 ms–30 s. | Sequenced MBP at minimum; MBO preferred for sub-second work. | Queue changes, cancelled liquidity, feed latency, leakage from future book state and non-executable midpoint. | Association vanishes under strict event ordering or cannot exceed execution-cost bounds. |
| 5 | H4: order-book replenishment | Reappearance/disappearance after a trade may reveal supply/demand persistence. Variables: per-order adds/modifies/cancels/executions. | Mid-price/execution outcome; 100 ms–5 s. | High-quality MBO event feed with documented sequencing. | Hidden orders, order-ID semantics, queue position, timestamp ambiguity, adverse selection. | With a predeclared event definition, post-event outcome is unstable, null, or non-monetisable after costs. |

## Universal research design controls

- Freeze universe, dates, data vintage, clock convention, target, feature
  transformations, cost model and split before viewing results.
- Use exchange event time and sequence where available; never sort solely by a
  vendor receipt timestamp without documenting the limitation.
- Keep auctions, halts and special trade conditions as labelled regimes; do not
  silently discard them.
- Use chronological, embargoed train/validation/test periods appropriate to the
  horizon; avoid overlapping-label leakage.
- Report dependence across events and days, multiple-hypothesis risk, and the
  contribution of individual securities/periods.
- Define executable evaluation separately: marketable orders require spread and
  impact; passive orders require a pessimistic queue/fill model.  A mid-price
  result alone fails the economic test.
