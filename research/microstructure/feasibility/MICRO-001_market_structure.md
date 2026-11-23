# MICRO-001 market structure

**Scope:** Australian cash equities; documentation review only.  Accessed 23
November 2026.  Reference identifiers are defined in the
[source register](../sources/source_register.md).

## Documented structure

ASX documents a pre-open, an opening single-price auction, continuous/normal
trading, a pre-closing phase, a closing single-price auction, post-close and
adjustment states.  Auction start windows are randomised.  A strategy whose
timestamp logic ignores these state transitions can accidentally mix auction
and continuous-market observations. [S1]

ASIC's quarterly data covers orders and trades in Australian equity market
products and reports activity at ASX and a competing market operator.  This is
evidence that a single-venue data feed is not necessarily a whole-market view;
it does not itself supply an event-replay dataset to this project. [S5][S6]

ASX Information Services says its real-time data products can include price,
volume, market depth, full order-book data and on-/off-book trade information.
The public descriptions do not, by themselves, establish a particular
historical format, event sequencing guarantee, retention period, or licence for
MICRO-001. [S2][S3]

## Implications by research horizon

| Topic | Milliseconds | Seconds–minutes | Longer intraday execution |
|---|---|---|---|
| Venue fragmentation | A consolidated, ordered view is essential; otherwise signal/event order is unknowable. | Include venue identifiers where available; test single-venue bias. | Measure at the venue/routing level where possible. |
| Auctions | Separate event class; do not extrapolate continuous-book models. | Treat opening/closing auctions as distinct regimes. | Explicitly decide whether execution may occur in an auction. |
| Time | Clock synchronisation and feed sequencing are prerequisites. | Record provider timezone, timestamp precision and session state. | Time stamps must still distinguish decision, order and fill. |
| Matching/queue | Queue position/fill probability is central and unavailable from simple bars. | Passive hypotheses require book and order-event detail. | Use conservative fill assumptions unless broker/exchange evidence supports more detail. |

## Matching rules, order types and tick sizes

This review deliberately does **not** assert a detailed TradeMatch matching
algorithm, order-condition catalogue, or tick-size table from memory.  They are
implementation-critical and must be transcribed from the current ASX operating
rules/procedures or technical manuals in the next gate, with version and
effective date.  A public trading-hours page alone is insufficient evidence for
those details. [S1]

That gap is material for H4 and H5: a displayed price change is not enough to
infer queue position, priority, cancellation semantics, or probable fill.

## Market participants and advantages

The following is an interpretation, not a count of participants or a claim of
profitability.  Firms with direct market-data infrastructure, low-latency
connectivity, synchronised clocks and sophisticated queue/fill models can react
before a retail API round trip.  That advantage matters most for displayed
liquidity and sub-second signals.  Institutional execution algorithms also
compete for available liquidity, while a smaller participant may avoid a pure
latency race by studying slower execution-quality or liquidity-regime questions.
ASIC's reported market-wide spreads/depth illustrate that immediate liquidity
has a measurable cost; they do not show that MICRO-001 can overcome it. [S5]

## Material market-structure risks

- A feed may cover ASX but not the competing venue or reported/off-book trades.
- Feed receive time is not exchange event time; the distinction must be retained.
- Auctions, halts, amendments and trade reports can invalidate naive time bars.
- A visible-book prediction is not an executable return after spread, queue,
  fees, routing and adverse selection.
- Current market documents and products can change; all future research must
  freeze document versions and data vintage.
