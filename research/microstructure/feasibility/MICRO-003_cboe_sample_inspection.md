# MICRO-003 — Inspection of the Cboe Australia PITCH sample

**Investigation date:** 24 November 2026. **Decision: CONDITIONAL GO**, narrowly
scoped to further single-venue (Cboe Australia / CXA) format and
reconstruction research. This is a data-format and data-quality
investigation only. No strategy, backtest, broker integration, live data
collection, paper trading, subscription or purchase occurred. MOM-001,
MICRO-001 and MICRO-002 were not inspected, changed or relied upon as
evidence here.

## 1. Executive conclusion

The publicly offered Cboe Australia Multicast PITCH sample is a genuine,
well-formed, single-day, single-matching-unit capture of the documented
PITCH protocol. It parses byte-for-byte against the official specification
with **zero malformed messages, zero sequence gaps, and zero order
cross-references to an Order Id that was never added**, across 334,856
sequenced messages (corrected from an earlier transcription error of
334,546 — see the [MICRO-003 closure audit](MICRO-003_closure_audit.md)
§A). This is materially stronger evidence than "the vendor's
marketing description matches the file": the message framing, field
offsets and semantics in Cboe's specification were independently applied to
the raw bytes and produced an internally consistent reconstruction.

This supports a narrow conclusion: the **sample format is trustworthy and
research-usable for Cboe Australia/CXA single-venue work**. It does **not**
establish ASX-wide coverage, current (2025–26) product behaviour, multi-day
continuity, or that trade prices can be used naively as a continuous price
series without first decoding the trade-type/designation flags (see §6).

## 2. Access and licence findings

- The "Download sample" link on the product page
  (`https://datashop.cboe.com/download/sample/227`) served the file directly
  over HTTPS with **no login, account creation, registration, or payment**
  (HTTP 200, `Content-Type: application/x-gzip`, `Content-Length: 3,227,946`
  bytes). No binding click-through or terms-acceptance step was presented.
- Cboe's general "Use of Cboe Content" page
  (`https://www.cboe.com/use_of_content/`) states that using "any Cboe...
  data... contained in Cboe websites" requires advance written approval and
  a signed licence, and that submitting a request "in no way grants or
  implies permission to use Cboe Content in any form." This is a genuine
  ambiguity: it is unclear whether a vendor-provided evaluation sample,
  explicitly placed on a commercial data-product page for prospective
  buyers to download without a gate, is "Cboe Content" in the sense that
  general policy addresses, or whether the sample itself constitutes the
  vendor's consent to local evaluation. The dedicated Cboe Australia
  data-policies page that might settle this (`https://www.cboe.com/data-policies`)
  returned **HTTP 404** and could not be read.
- **Resolution applied in this investigation:** given (a) the absence of any
  access gate on a page purpose-built for pre-purchase sample evaluation,
  and (b) explicit instruction from the project owner to proceed on this
  basis, the sample was downloaded and inspected **locally only**. The raw
  sample is **not committed to this repository** (see §9/provenance below)
  and no sample content has been or will be redistributed, republished, or
  used in any commercial context. No account was created, no purchase was
  made, and no vendor was contacted. This resolution is a judgement call,
  not a legal determination — if this research is ever extended,
  commercialised, or shared outside this private research journal, written
  confirmation from Cboe should be obtained first.
- Download provenance:
  - Source URL: `https://datashop.cboe.com/download/sample/227`
  - Retrieved: 24 November 2026
  - Server-reported filename: `matching_01_mdm-pitch-20230123.dat.gz`
  - Compressed file SHA-256: `7de2c71cb46980d38a48d1be0948f97d711ac64010dc4f9097f2191aef7bbbfe`
  - Decompressed file SHA-256: `29d631c3ef7ae4a3c288bafc86e56a9cb43c60d50f06b046334e2a9f18dbb9c2`
  - Decompressed size: 10,780,332 bytes
  - The raw sample and its decompressed form are kept outside Git, in a
    local, non-repository working directory. Only this document, its
    findings, and the checksums above are committed.
  - The CXA PITCH specification used to interpret the file was retrieved
    from `https://cdn.cboe.com/resources/membership/CXA_Multicast_PITCH_Specification.pdf`
    (Version 1.0.12, 21 March 2025), SHA-256
    `8bf2aba85d5932c8c2d661cda42924462f80e81116b1dc56549a32a3df524fc8`. This
    specification PDF is itself copyrighted Cboe material and is likewise
    kept local, not committed.

## 3. Sample contents and schema

- **Format:** binary flat file, PITCH wire protocol framed in "Sequenced
  Unit Header" blocks (8 bytes: 2-byte length, 1-byte message count, 1-byte
  unit, 4-byte starting sequence number), each followed by that many
  variable-length, self-describing messages (1-byte length + 1-byte type
  prefix per message), exactly as documented in the specification.
- **Coverage:** a single matching unit ("Hdr Unit = 1" throughout — the
  product page states CXA "currently" operates 2 matching units, so this
  sample covers one of them, not the whole Cboe Australia market).
- **Date/time range:** message timestamps (nanoseconds since the Unix
  epoch, decoded per spec) run from **2023-01-22 21:00:00.360 UTC** to
  **2023-01-23 09:54:55.071 UTC** — a single ASX trading session (Sydney
  local time, this spans roughly pre-market through the close and
  post-close period on 23 January 2023). Note this predates the "historical
  data available from 2023-03-27" statement on the DataShop product page;
  the free sample is evidently drawn from an earlier date than the
  currently-advertised purchasable historical range, which is worth noting
  as a minor inconsistency rather than a defect.
- **Sequencing:** 33,486 Sequenced Unit Headers, sequence numbers running
  contiguously from 1 to 334,856 at the individual-message level (334,851
  is the starting sequence number of the file's last Sequenced Unit
  Header, which itself carries 6 further messages — corrected from an
  earlier category error that reported the header-start range as if it
  were the message-level range; see the
  [MICRO-003 closure audit](MICRO-003_closure_audit.md) §A), with **no
  gaps detected** when accounting for each header's message count.
- **Instruments:** 58 distinct symbol codes observed (e.g. BHP, ANZ, FMG,
  A2M, CBTC, and others), consistent with a single matching unit covering a
  subset of CXA-traded securities, not the full ASX-equivalent universe.

## 4. Message interpretation

All byte offsets below were applied directly against the raw file using
the field tables in the CXA PITCH specification (§§3.1–3.9) and cross-
checked for internal consistency (see §5). Message type counts observed:

| Message type | Count |
|---|---|
| Add Order (0x37) | 155,653 |
| Delete Order (0x3C) | 134,983 |
| Order Executed (0x38) | 23,736 |
| Trading Status (0x3B) | 9,823 |
| Modify Order (0x3A) | 6,735 |
| Reduce Size (0x39) | 3,446 |
| Calculated Value (0xE3) | 267 |
| Trade (0x3D) | 210 |
| Trade Break (0x3E) | 2 |
| End of Session (0x2D) | 1 |

No Unit Clear, Order Executed at Price, Auction Update, or Auction Summary
messages were observed in this file — plausible given these correspond to
rarer recovery/auction-overlap events, but it means this single sample
cannot be used to validate those message types' byte layouts.

The complete set of core order-book lifecycle messages (Add, Modify,
Reduce, Executed, Delete) and execution/trade messages decoded cleanly, with
every field (order ID, side, quantity, symbol, price, timestamp) producing
plausible, internally consistent values (see §5 for the integrity test).

## 5. Sequence and reconstruction findings

Two independent verification scripts were run against the raw bytes:

1. **Full-file structural parse.** Walked every Sequenced Unit Header and
   every contained message for the entire file. Result: **0 malformed or
   truncated messages**, **0 unknown message type bytes**, and **0 sequence
   gaps** across all 33,486 headers.
2. **Order-book referential-integrity and reconstruction test.** Replayed
   Add/Modify/Reduce/Executed/Delete messages in sequence, maintaining a
   live order table keyed by Order Id and a live price-level book per side
   for a sample instrument (BHP). Result: of 155,653 Add, 6,735 Modify,
   3,446 Reduce, 23,736 Executed and 134,983 Delete messages, **zero**
   referenced an Order Id that had not been previously added within this
   file. 20,670 orders remained open (not deleted or fully executed) at the
   point the file ends — consistent with the specification's documented
   behaviour for multi-day (GTC/GTD) orders carried into the next session,
   not a defect.

This is strong evidence that (a) the documented wire format is correctly
specified and matches production output, and (b) a single matching unit's
displayed order book can be mechanically and correctly reconstructed from
this file alone, using only the publicly available specification — no
vendor support, undocumented reverse engineering, or guessing was required.

## 6. Data-quality anomalies

One genuine interpretive finding, not a parsing defect:

**Trade prices for a single symbol on a single day span a wide range** —
for BHP, executed/reported trade prices ranged from approximately $31.04 to
$49.40 within the session. Decoding the Trade message's type/designation
byte fields shows this is explained by the data, not by a decoding error:
trades flagged as ordinary on-exchange matching cluster tightly (~$31.04–
$32.50), while trades carrying different designation flags — consistent
with the specification's documented categories for block trades, large
portfolio trades, and other off-exchange-style reports — occur at
materially different prices ($40.62, $49.40, $31.54). This is expected
institutional behaviour (negotiated/reported trades need not reflect the
contemporaneous continuous-market price) but it is a **real trap for naive
use**: anyone treating the `Trade` message stream as a plain continuous
price series without first filtering by trade type/designation would
construct an economically meaningless and highly noisy "price" series.

One further honesty note: this investigation's byte-offset mapping for the
Trade message's `Trade Designation` versus `Trade Report Type` fields
(bytes 61 and 62) could not be disambiguated with full confidence from the
specification PDF's own table, because the PDF's table layout did not
survive plain-text extraction cleanly (columns were visibly interleaved in
the extracted text). The *combined* flag region reliably distinguishes
plain on-exchange executions from differently-priced reported trades (as
shown above), but which single byte carries which named enumeration should
be re-confirmed against the specification's worked examples (§7, "Order
Entry Examples") before this distinction is relied on in any future
quantitative work.

No other structural anomalies, missing fields, or inconsistent timestamps
were found.

## 7. Supported research applications

Given the single matching-unit, single-day, Cboe-only scope of this sample,
it can support, in principle, format validation and prototyping (not yet
strategy research) for:

- **H1 (order-book imbalance):** the sample demonstrably supports full
  order-book reconstruction (bid/ask price-level depth) for any symbol
  present, which is the minimum data requirement for this hypothesis — on
  a single-venue (CXA-only) basis.
- **H4 (order-book replenishment):** Add/Delete/Modify/Reduce sequencing
  with intact Order Ids supports order-lifecycle and replenishment-timing
  analysis on this venue.
- **H2 (trade-flow imbalance)** and **H5 (execution-quality
  description):** supported only after the trade type/designation
  decoding gap in §6 is resolved, since naive trade-flow statistics would
  otherwise be contaminated by non-continuous-market reports.
- **H3 (liquidity-shock reversal):** partially supported; the file has no
  Auction Update/Summary messages to examine, and only one trading day, so
  shock/reversal dynamics cannot be tested from this sample alone.

None of these are validated here — only the data's *structural capacity* to
support them, on a single venue, for one day, has been demonstrated.

## 8. Limitations of single-venue coverage

- **CXA is not ASX.** Cboe Australia is a secondary, competing execution
  venue. The large majority of ASX-listed security turnover executes on
  ASX's own Trade Match system, not CXA. A venue-complete picture of order
  flow, liquidity or price formation for any ASX-listed stock requires ASX
  data as well; MICRO-002 already established that no ASX historical
  MBO/MBP sample has been obtained or verified.
- **One matching unit only.** CXA "currently" runs 2 matching units per the
  product page; this sample is entirely from unit 1. Coverage of the
  second unit's instrument set is unverified.
- **One trading day.** No claim can be made about data continuity,
  schema stability, corporate-action handling, or typical-vs-atypical
  session behaviour from a single day.
- **Sample date predates the vendor's advertised historical start date**
  (see §3) — this specific file may not represent the current production
  product's exact current technical behaviour; the specification document
  (v1.0.12, March 2025) is more current than the sample file (January
  2023) by over two years, and message types could in principle have
  changed in that window (the spec text itself says Cboe "reserves the
  right to add message types... without notice").

## 9. Outstanding requirements for ASX plus Cboe research

- A written product/field/licence specification and quote from ASX
  Information Services (MarketSource), as already identified as the
  priority next step in MICRO-002, remains outstanding and is not advanced
  by this investigation.
- Written confirmation from Cboe (or legal advice) on whether the free
  sample's terms genuinely permit the kind of private research inspection
  performed here, versus requiring the advance-approval process described
  in Cboe's general content-use policy (§2) — needed before any further
  reliance on Cboe sample data beyond this one-off technical inspection, and
  certainly before any publication, sharing, or commercial use.
- Confirmation of the exact Trade Designation / Trade Report Type byte
  semantics (§6) against the specification's worked examples before trade
  data from either venue is used in any price-formation analysis.
- A current (not January 2023) sample, if one becomes available, to confirm
  today's production feed matches the March 2025 specification version
  used here.

## 10. Recommendation for the next milestone

**CONDITIONAL GO** for continued Cboe-only, documentation/prototyping-level
microstructure research (e.g., building a small, local, non-production
order-book reconstruction utility against this or a future Cboe sample, to
further test H1/H4 reconstruction mechanics). **NO GO** on any ASX-inclusive
or multi-venue quantitative research until a written ASX data specification
and licence position exists, consistent with MICRO-002's standing
conclusion. **NO GO**, independent of the above, on any live data purchase,
account creation, or trading-related activity — none of that is
contemplated by this investigation and none should be initiated without the
project owner's explicit, separate approval.

The next step is the project owner's decision, not an automatically
triggered MICRO-004. Candidates worth considering (not initiated here):
seeking written clarification from Cboe on sample-use terms; or deferring
further Cboe-side work and instead sending the written ASX MarketSource
enquiry template already drafted in MICRO-002's sample-data-requirements
document, since ASX coverage is the larger unresolved gap for any
economically meaningful ASX microstructure study.
