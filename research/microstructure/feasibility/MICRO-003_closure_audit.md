# MICRO-003 closure audit — numerical reconciliation and Cboe permissions

**Audit date:** 24 November 2026. This is a closure audit of MICRO-003, not
MICRO-004. No further sample processing, purchases, subscriptions, vendor
contact, broker integration, or strategy work occurred. MOM-001, MICRO-001
and MICRO-002 were not touched.

## Status: **HOLD**

Further use of the Cboe sample (beyond what is already published in
MICRO-003) is placed on hold pending written clarification from Cboe. See
§C for reasoning and §E for the recommendation on the existing public
report. This is a precautionary judgement, not a legal conclusion — the
documents reviewed leave genuine, unresolved ambiguity rather than a clear
answer either way.

## A. Numerical reconciliation — **RESOLVED**

The original sample files were still present locally, unchanged (checksums
below match MICRO-003's recorded provenance exactly), so this was fully
resolvable without redownloading or repairing anything.

- Compressed sample SHA-256 (unchanged):
  `7de2c71cb46980d38a48d1be0948f97d711ac64010dc4f9097f2191aef7bbbfe`
- Decompressed sample SHA-256 (unchanged):
  `29d631c3ef7ae4a3c288bafc86e56a9cb43c60d50f06b046334e2a9f18dbb9c2`

Independent recount, cross-checked three separate ways:

| Quantity | Value | Method |
|---|---|---|
| Total Sequenced Unit Headers | 33,486 | header walk |
| Sum of `Hdr Count` field across all headers | 334,856 | header walk |
| Messages successfully parsed (loop iterations) | 334,856 | header walk |
| Sum of the message-type breakdown table | 334,856 | recount of the same table published in MICRO-003 §4 |
| First message sequence number | 1 | from first header's `Hdr Sequence` |
| Last header's starting `Hdr Sequence` | 334,851 | from last header |
| Last header's `Hdr Count` | 6 | from last header |
| Implied sequence number of the very last message (334,851 + 6 − 1) | **334,856** | arithmetic |
| Malformed/truncated messages | 0 | header walk |
| Gaps between consecutive header blocks | 0 | header walk |
| Overlapping/duplicated header blocks | 0 | header walk |

**All four independent counts — the message-type table, the sum of
declared `Hdr Count` values, the number of messages actually walked, and
the implied final sequence number arithmetic — agree exactly on
334,856.** This is the correct, internally consistent total for the file.
The message-type table published in MICRO-003 §4 was always correct (its
entries were never wrong); only the two prose sentences citing a total
were wrong, for two different reasons:

- **"334,546" (MICRO-003 §1, executive conclusion) was simply a
  transcription error.** No computation or data artefact reconstructs
  this number — it does not match the type-table sum, the header-count
  sum, the sequence-range arithmetic, or the sum of order-lifecycle
  message types alone (155,653 + 6,735 + 3,446 + 23,736 + 134,983 =
  324,553, also not 334,546). It was a typo introduced when the prose
  sentence was written, independent of the correct table immediately
  below it. **Correction applied to MICRO-003 §1**: "334,546" → "334,856".

- **"1 to 334,851" (MICRO-003 §3, under "Sequencing") was a real but
  different error: a category mistake, not a typo.** The original
  verification script printed the *range of header starting sequence
  numbers* (`min`/`max` of each header's own `Hdr Sequence` field) and
  this was reported as if it were the range of *individual message*
  sequence numbers. 334,851 is real and correctly computed — it is the
  starting sequence number of the **last** Sequenced Unit Header in the
  file — but that header itself carries 6 messages (334,851 through
  334,856), so the true upper bound of the message-level sequence range
  is 334,856, not 334,851. **Correction applied to MICRO-003 §3**:
  "running contiguously from 1 to 334,851" → "running contiguously from 1
  to 334,856 at the individual-message level (334,851 is the starting
  sequence number of the file's last Sequenced Unit Header, which itself
  carries 6 further messages)".

Both corrections are applied directly to
`MICRO-003_cboe_sample_inspection.md` in this same commit, each with this
document cited as the source of the correction, per the instruction not to
silently alter earlier findings. No other figure in MICRO-003 (message-type
table, referential-integrity results, timestamps, symbol counts, BHP trade
price findings) is affected — those were independently re-derivable from
the type-table counts, which were correct throughout, and from the separate
order-book reconstruction script, which was not re-run in this audit per
the processing safeguard in §C (it uses only the same already-recorded
figures from MICRO-003 itself).

Unsequenced/heartbeat messages: not applicable to this file — the walk
found 0 headers with `Hdr Count == 0` (no heartbeats were captured in this
single-session sample), so there is no special-case treatment to document.

## B. Cboe permissions audit — genuinely uncertain, not resolved

No definitive legal opinion is given, as instructed. This section quotes
the actual governing documents and distinguishes clearly-applicable text
from text whose application to an ungated evaluation sample is uncertain.

### Documents reviewed

| Document | Retrieved | Readable as text? |
|---|---|---|
| Cboe Australia Data Policies, v1.4, 1 Feb 2025 | 24 Nov 2026 | Yes, via local `pdftotext` extraction (WebFetch alone returned only compressed PDF bytes) |
| Cboe Australia Product Manual, v1.4 | 24 Nov 2026 | Yes, via local `pdftotext` extraction |
| `datashop.cboe.com/data-policies` | 24 Nov 2026 | Yes (HTML); itself just a links page |
| Cboe LiveVol DataShop Policies for Historical Data Services | 24 Nov 2026 | Yes, via local `pdftotext` extraction |
| **Cboe LiveVol DataShop License Agreement** | 24 Nov 2026 | Yes, via local `pdftotext` extraction — **this is the most directly relevant document**, since `datashop.cboe.com` is the exact site the PITCH sample was downloaded from |
| `www.cboe.com/use-of-content` | 24 Nov 2026 | Yes (HTML) |

Note on thoroughness: the DataShop License Agreement is 16 pages; targeted
sections were read in full (definitions, License Grant, License
Limitations, Redistribution of Historical Data, Software/API terms,
Survival), but the document was not read end-to-end line by line, so a
retention-period clause or other provision outside the sections quoted
below could exist unseen. This limitation is stated rather than papered
over.

### Findings, with exact quotes

**1. Whether downloading the ungated sample permits local evaluation —
genuinely unclear.** The DataShop License Agreement states up front:
*"SUBSCRIBER MUST READ AND AGREE BELOW TO THE TERMS AND CONDITIONS OF THIS
AGREEMENT IN ORDER TO RECEIVE AND USE THE DATA, SERVICES AND RELATED
INFORMATION MADE AVAILABLE BY CBOE LIVEVOL, LLC."* and its License Grant
clause is explicit: *"In consideration of Subscriber's payment of
applicable Fees, Cboe hereby grants to Subscriber a License to access and
use the Services as set forth in the applicable Order."* Both the
acceptance step and the licence grant are written around a paid
**Order**. No click-through acceptance screen was presented during the
actual sample download (confirmed in MICRO-003 — HTTP 200, direct file,
no redirect to a login or agreement page), and there is no Order for a
$0 sample. This cuts both ways: it is a real argument that the
Agreement's restrictions were never triggered for this download (no Order
exists for them to attach to) — but by the same logic, no licence was
affirmatively granted either. The separate "Cboe Australia Data Policies"
document (the Australia-specific, PITCH-feed-focused policy) independently
anchors its entire defined term "Data" to data *"sourced directly or
indirectly from Cboe pursuant to this Agreement"* — i.e., pursuant to the
Global Data Agreement that a "Data Recipient" signs — and that document's
glossary defines "Data Recipient" and related terms throughout by
reference to parties under that Agreement. **No document defines "sample"
or "evaluation data" as a distinct category with its own, lesser rule.**
This is a real gap in Cboe's published terms, not a resolved permission.

**2. Whether local binary parsing is permitted — not directly addressed.**
The only reverse-engineering restriction found, *"Subscriber shall not,
directly or indirectly, reverse engineer, disassemble or decompile any
component of the Software..."*, is explicitly scoped: *"In addition to the
terms set forth in Section I, the following additional terms apply only
to purchases of allaccess API subscriptions"* (Section IV, "Provisions
Applicable Only to Software Services, Including API Delivery"). Decoding
a flat data file's byte layout against Cboe's own **publicly published**
PITCH specification document is a different act from reverse-engineering
"Software" delivered under a paid API subscription, and this clause's own
scoping language supports that distinction — but no document affirmatively
says parsing a free sample is permitted either.

**3. Whether order-book reconstruction is permitted — not directly
addressed**, for the same reason as (2): no clause contemplates this
specific analytical activity on free sample data.

**4. Whether derived statistics and research reports may be created —
narrow support only for paying Subscribers, not established here.** The
License Grant clause permits a Subscriber to *"disclose nominal elements
or extracts of the applicable Data and/or Derived Data, relating to
particular transactions or situations occurring in the normal conduct of
Subscriber's business, in written materials and may transmit such
materials to Subscriber's customers and prospective customers."* This is
conditioned on being a Subscriber under an Order (not established here)
and is framed around ordinary business operations, not a published
research report. Separately, "Derived Data" has a strict definition in the
Australia Data Policies glossary: *"a work created using Data provided
always that: the Data is not directly or indirectly identifiable as part
of the Derived Data; the Derived Data is not in any way a substitute for
the Data or any part of it; the Derived Data cannot be reverse engineered
so that the Data is ascertainable directly or indirectly... Whether
something is Derived Data is determined by Cboe [emphasis added]."*
MICRO-003 as published quotes literal sample values (specific order IDs,
specific trade prices and quantities, specific timestamps) — this content
is plausibly *not* "Derived Data" under that strict test, since the
underlying Data is directly identifiable within it. This is a genuine,
concrete finding this audit surfaces as a risk, not a settled violation.

**5. Whether findings may be published in a public GitHub repository —
leans against, not established as permitted.** `cboe.com/use-of-content`
states without exception: *"In order to use any logo, data, photo/image or
other content contained in Cboe websites (collectively 'Cboe Content'),
you must receive approval in advance from Cboe,"* that approval is
*"contingent upon your execution of a license agreement,"* and that
*"Submitting a Request to Use Cboe Content in no way grants or implies
permission to use Cboe Content in any form."* No sample/evaluation/research
exception is stated anywhere in this policy. The DataShop Agreement's own
redistribution clause only ever activates *"where the option to
redistribute data is available on DataShop for a specific dataset, and
where Subscriber has selected such option in its Order"* — no Order exists
here, so no redistribution right has been granted under that document
either. Taken together, nothing reviewed supports public publication of
sample-derived findings; several things weigh against it.

**6. Whether the data may be used as an input to investment-strategy
research — explicitly restricted, if this Agreement is found to apply.**
This is the single most consequential clause found, and is directly on
point given this project's ultimate purpose: *"Unless explicitly provided
for in a separate written and executed agreement with Cboe and/or its
Affiliates, Subscriber shall not use, and shall prohibit its Affiliates
and any other third-party from using, the Data (and any methodology
associated therewith), in connection with (1) creating any index,
indicator, benchmark, investment strategy, or similar value (whether as an
input or otherwise), (2) performance benchmarking, (3) creating, offering,
selling, listing, trading, settling, or valuing of a financial/investment
product, and/or (4) creating Derived Data from any index-related data
provided under this Agreement"* (DataShop License Agreement, Section
I.1(e)(viii)). If this Agreement is read to govern the sample at all, this
clause squarely forbids using it (or methodology derived from it) as an
input to investment-strategy research without a separate signed
agreement — which would include any future MICRO-004-style strategy work
building on this sample. This should weigh heavily on any decision to
extend this research track using Cboe data, independent of the
publication question in (5).

**7. Whether local retention is permitted, and for how long — not found in
the sections reviewed.** No explicit retention-period clause for
free/sample data was located; a general retention clause could exist
elsewhere in the 16-page Agreement not covered by the targeted sections
read (see thoroughness note above). The unrelated Australia Data Policies
document does specify a 6-month retention limit, but only for data
obtained under its separate "Academic Purposes" licence programme for
accredited educational institutions — not applicable here and not
transferable to this situation by analogy.

**8. Whether written approval or a specific data licence is required —
yes, on the clearest reading of the documents, though whether that
requirement actually extends to a $0, no-Order sample remains the open
question running through every item above.** Both the general
`use-of-content` policy and the DataShop Agreement's own framing ("must
read and agree... in order to receive and use the Data") point toward
requiring approval/agreement for use of Cboe data generally; neither
document states whether an unauthenticated sample download is treated as
triggering that requirement or as falling outside it entirely.

### Clearly applies vs. uncertain — summary table

| Term | Clearly applies to a paying Subscriber/Data Recipient | Clearly does NOT apply (no Order/Agreement exists) | Application to the ungated sample |
|---|---|---|---|
| License Grant (payment-conditioned use rights) | Yes | — | Uncertain — no Order was ever placed |
| Investment-strategy-use restriction (I.1(e)(viii)) | Yes, binds any Subscriber | — | **Uncertain whether it binds a non-Subscriber — but prudent to treat as binding, given the stakes** |
| Redistribution permission (conditioned on a selected Order option) | Yes | Yes — no Order, so no redistribution right exists either way | Not available either way |
| Use-of-content prior-approval requirement | Applies to "Cboe Content" generally | — | Uncertain whether a public sample counts as "Content contained in Cboe websites" |
| Academic Purposes licence (6-month retention etc.) | Yes, only for approved institutions | Yes — this project has no such licence | Not applicable |
| Software reverse-engineering prohibition | Yes, for paid API/software subscriptions | Yes — no software subscription exists | Not applicable to file-format parsing against a public spec |

## C. Immediate safeguards — applied

- No further processing has been run against the sample in this audit
  beyond the counting/reconciliation in §A, which reused figures already
  computed and published in MICRO-003 plus simple arithmetic cross-checks
  against the untouched original files — no new derived outputs, statistics
  or analysis were created from the raw sample.
- No redistribution of the raw sample or the Cboe specification PDF has
  occurred; both remain local, outside Git, as before.
- No expansion of sample-derived findings beyond what MICRO-003 already
  published.
- The original sample and specification files, and their checksums, are
  preserved unchanged and verified identical in §A.
- Nothing has been deleted. The retention question in B.7 is unresolved,
  not acted on — the files are being kept pending a decision, which is
  itself documented here rather than decided unilaterally.

## D. Draft vendor clarification email (NOT sent)

> **Subject:** Clarification requested — free DataShop sample, Cboe
> Australia Equities Multicast PITCH
>
> Hello,
>
> We are a private, non-commercial research project evaluating ASX/CXA
> market microstructure data formats. Using the "Download sample" link on
> the Cboe Australia Equities Multicast PITCH product page
> (datashop.cboe.com/cboe-australia-equities-multicast-pitch), we
> downloaded the publicly offered sample file
> (`matching_01_mdm-pitch-20230123.dat.gz`) without creating an account or
> making any payment, as no such step was presented by the site.
>
> We would like to confirm, specifically for this already-downloaded free
> sample (not a paid subscription):
>
> 1. Does downloading this sample constitute acceptance of the Cboe
>    LiveVol DataShop License Agreement, or any other specific licence,
>    given that no Order was placed and no click-through acceptance screen
>    was presented during the download?
> 2. Is private, non-commercial technical inspection of this sample file
>    (binary parsing against your published PITCH specification, to
>    validate message framing and sequencing) permitted?
> 3. May we publish a written, non-commercial technical report describing
>    our parsing methodology and results — including illustrative excerpts
>    such as specific field values, counts, and summary statistics drawn
>    from the sample — in a public, non-commercial GitHub research
>    repository?
> 4. Is any further use of this sample, or of insights/methodology derived
>    from it, permitted as input to investment-strategy research, or does
>    Section I.1(e)(viii) of the DataShop License Agreement (restricting
>    use of "the Data... in connection with... creating any... investment
>    strategy... whether as an input or otherwise" absent a separate signed
>    agreement) apply to this situation?
> 5. How long may we retain a local copy of this sample, and must it be
>    deleted if we do not proceed to a paid subscription?
>
> We have not redistributed the raw sample file and have made no
> investment or trading use of it. We would appreciate written
> confirmation before proceeding further.
>
> Thank you,
> [name / project]

## E. Recommendation for the existing public MICRO-003 report

MICRO-003 (`research/microstructure/feasibility/MICRO-003_cboe_sample_inspection.md`)
is already committed to this repository's public Git history and, per the
project's standing workflow, pushed to GitHub. It contains:
- Literal sample field values (specific order IDs, timestamps, prices,
  quantities) — plausibly not "Derived Data" under Cboe's strict
  definition (§B.4).
- A technical conclusion ("CONDITIONAL GO for continued Cboe-only format/
  reconstruction work") that, read uncharitably, could be seen as oriented
  toward exactly the "investment strategy" use that §B.6's clause
  restricts — although the report itself is explicit that it is a
  format/data-quality investigation, not a strategy result, and recommends
  against any ASX-inclusive or trading use.

Given the genuine uncertainty in §B, **the responsible position is that
this report's continued public availability carries some unquantified
risk**, and that risk is not eliminated simply by refraining from further
processing going forward — the report, as already published, is the thing
in question. This audit does **not** change repository visibility or
rewrite Git history, per the explicit instruction in this task, and does
not take a position on which outcome is correct. The project owner should
decide, with the options being, roughly:

1. Leave MICRO-003 public as-is, accepting the residual uncertainty
   documented here (the report is framed conservatively, does not
   redistribute the raw sample, and states its own CONDITIONAL GO/NO GO
   limits clearly).
2. Make the repository (or just the MICRO-003 file's history) private or
   unlisted until Cboe responds to a clarification request, then decide
   whether to restore it, amend it to remove literal sample values, or
   leave it withdrawn.
3. Send (a version of) the draft clarification in §D to Cboe now, and hold
   the public-availability decision until a response arrives.

No action on any of these three has been taken; this is presented for the
project owner's decision only.

## Conclusion

- **Part A (numerical reconciliation): fully resolved.** All three
  disputed figures reconcile to a single, internally consistent total of
  334,856 messages; corrections have been applied to MICRO-003 with this
  document cited as the source.
- **Part B (permissions): genuinely unresolved by the published documents,
  not by omission of effort.** The clearest, most important finding is
  §B.6 — a specific contractual restriction on using Cboe data (or
  methodology derived from it) as an input to investment-strategy research
  without a separate signed agreement — which should inform any decision
  about whether to continue this research track with Cboe data at all.
- **Status: HOLD** on further sample use pending the project owner's
  review of §E, and ideally pending an actual response to a clarification
  request along the lines of §D.
