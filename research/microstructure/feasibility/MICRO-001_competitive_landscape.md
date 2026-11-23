# MICRO-001 competitive landscape

## Evidence and interpretation

ASIC publishes market-wide statistics from orders and trades and reports both
ASX and another public equity-market operator in its venue breakdowns.  Its
statistics show that spreads, depth and venue share are empirical properties of
the Australian market, not free assumptions. [S5][S6]  They do **not** identify
specific firms' strategies, profitability or latency.

The following table is a reasoned interpretation of documented market structure,
not a claim about the number, identity or returns of participants.

| Participant type | Likely relevant advantage or role | Implication for MICRO-001 |
|---|---|---|
| High-frequency / proprietary firms | May operate with direct data/connectivity and sophisticated models. | Do not treat a retail API receive timestamp as competitive at sub-second horizons. |
| Market makers | Supply and update displayed liquidity while managing adverse selection. | Apparent depth can disappear; passive fills can be selected against. |
| Institutional execution algorithms | Split/rout parent orders and seek liquidity across venues. | Observed trades may reflect execution objectives rather than a standalone predictive signal. |
| Independent systematic researchers | Can study slower, well-defined questions without competing solely on speed. | Focus first on falsifiable, cost-aware seconds/minutes or execution-quality research. |
| Retail algorithmic participants | Usually face broker, data and routing constraints. | Must model minimum costs, partial fills and operational limits before inference. |

## Competition and adverse selection

Milliseconds: priority, message handling and feed latency can determine whether a
displayed order is still available.  Without colocation-grade infrastructure and
event-level observations, an apparent backtest fill would be especially
vulnerable to queue-priority and adverse-selection bias.

Seconds/minutes: latency matters less than in a queue race but spread, temporary
liquidity, venue coverage and trade classification still matter.  A predictive
mid-price move is not proof that a marketable or passive order could capture it
net of costs.

Smaller and less-liquid instruments may have wider spreads, shallower displayed
depth and discontinuous trading.  They can be useful for descriptive liquidity
research but are not an assumed opportunity: execution risk, stale quotes and
price impact may increase at least as quickly as any apparent signal.

## Competitive conclusion

MICRO-001 should not attempt to compete in pure latency.  A defensible next
research question is whether documented, slower liquidity/execution effects
survive conservative spread and fill assumptions on a specified historical
dataset.  The answer remains unknown until the data gate is passed.
