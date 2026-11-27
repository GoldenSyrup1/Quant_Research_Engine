# UNIV-001 — point-in-time universe data schema (proposed, not implemented)

This is a specification only. No universe has been built, no data has been
acquired, and no code implementing this schema exists yet. It is written to
be the minimum field set this project would need from any vendor or
combination of vendors (see
[UNIV-001_source_register.md](UNIV-001_source_register.md)) before a
historical universe could be constructed and audited to the same standard
MOM-001 already applies to its price data.

## Design principle: effective-dated records, never overwritten

Every record below is **effective-dated**: it states what was true as of a
given date, and a later correction or update is added as a *new* record
with its own effective date and retrieval provenance, rather than
overwriting the earlier value in place. This mirrors MOM-001's own existing
discipline of never silently repairing or overwriting recorded
configuration and audit data, and is the only way to later prove that a
backtest's universe decisions did not use information unavailable at the
time.

## Minimum field set

### Security identity (one row per distinct security, not per ticker)

| Field | Description | Why it matters |
|---|---|---|
| `security_id` | A stable, vendor-independent identifier that does not change if the ticker changes | Without this, a ticker rename or relisting looks like a delisting plus a new, unrelated listing — silently breaking survivorship-bias correction |
| `issuer_id` | Identifier for the underlying issuing entity, distinct from the security (relevant for multiple share classes, or securities that change issuer via restructuring) | Needed to correctly interpret mergers/demergers as continuity events, not simple delistings |
| `exchange` | Listing venue (e.g. ASX) | This project is ASX-scoped, but the field should exist in case Cboe Australia or another venue is ever relevant (consistent with the independence already established between this momentum track and MICRO-00x) |
| `primary_ticker` | The security's ticker as of the record's effective date | Must be read together with `effective_date` — never treated as a fixed, current-day label |
| `ticker_aliases` | Historical ticker codes previously used by the same `security_id` | Required to resolve ticker-rename events without losing continuity |

### Listing lifecycle

| Field | Description | Why it matters |
|---|---|---|
| `listing_date` | Date the security was first listed/admitted to quotation | Needed to prevent a backtest from holding a security before it existed |
| `delisting_date` | Date the security was removed from official quotation | The core survivorship-bias field; must be populated even when the universe source is "currently listed" data, or the whole point of this schema is defeated |
| `delisting_reason` | Categorical: acquisition / scheme of arrangement / insolvency / voluntary deregistration / compliance removal / other (documented) | Determines which delisting-return treatment rule applies (below); must not be left as free text only, or downstream code cannot branch on it deterministically |
| `delisting_return_treatment` | Documented rule actually applied for this security's final return (e.g. cash-settlement amount, acquirer exchange ratio realised value, or a declared 100% loss for insolvency) | Flagged in the feasibility report (§4, §5) as unconfirmed for every vendor reviewed — this field must be populated from primary vendor documentation, never assumed, before any backtest uses it |
| `suspension_periods` | List of (start, end-or-ongoing) date ranges where trading was suspended but the listing was not removed | Needed so a suspended-but-not-delisted security is not mistaken for a delisted one (Premium Data's own FAQ makes exactly this distinction for its own data — see source register U4) |

### Index / universe membership (if approach A or a hybrid is used)

| Field | Description | Why it matters |
|---|---|---|
| `index_code` | Which index this membership record refers to (e.g. S&P/ASX 200, All Ordinaries) | A security can be in one index and not another at the same time |
| `membership_start_date` | Effective date membership began | Must be the *effective* date, not the announcement date — getting this wrong is the single most likely way this schema reintroduces look-ahead bias (flagged in the feasibility report §2, §4, §9) |
| `membership_end_date` | Effective date membership ended (open-ended if still a member) | Same effective-dating requirement as above |
| `membership_source` | Which vendor/document this membership record came from, and its retrieval date | Required for the same reason MOM-001 records data provenance for prices — membership claims must be traceable back to a specific, checkable source |

### Liquidity / market-cap filter inputs (if approach C is used)

| Field | Description | Why it matters |
|---|---|---|
| `market_cap_as_of_date` | Historical market capitalisation as of a specific date, not a current-day figure | A filter using today's market cap to decide a historical universe membership is a textbook look-ahead-bias bug |
| `traded_value_window` | Rolling traded value/volume statistic computed only from data available as of the decision date | Same look-ahead-bias concern as above, applied to liquidity rather than size |
| `filter_rule_version` | A version identifier for the exact filter rule applied (threshold, window length) | If the filter rule is ever changed, old universe snapshots must remain reproducible under the rule that was actually used to produce them, not silently reinterpreted under a newer rule |

### Corporate actions

| Field | Description | Why it matters |
|---|---|---|
| `action_type` | Split / consolidation / bonus issue / demerger / other | Determines which price-adjustment convention applies |
| `action_effective_date` | Date the action took effect | Must align with whatever price-adjustment series this universe is paired with |
| `adjustment_factor` | The multiplicative (or documented) adjustment applied | Needs to be independently checkable against the source exchange's own published factor (Premium Data's FAQ references ASX's own daily "dilution factors" as the authoritative source — see U4) — never trust a vendor's adjusted series without being able to trace the factor back to this kind of primary reference |

### Provenance (applies to every record above)

| Field | Description | Why it matters |
|---|---|---|
| `data_source` | Which vendor or document supplied this record | Required for the same reason every other dataset in this project records its source |
| `data_vintage` / `retrieved_at` | When this record was retrieved/generated | A later refresh from the same vendor is a new vintage, not a reproduction, per AGENTS.md's existing rule |
| `source_checksum_or_reference` | A checksum or stable reference to the exact source file/page this record was derived from, where feasible | Mirrors `data/provenance.json`'s existing per-ticker provenance pattern; without it, a future reviewer cannot verify a universe snapshot the way MICRO-003's closure audit verified MOM-001's price-data checksums |

## What this schema deliberately does not specify yet

- It does not specify a physical storage format (CSV, Parquet, database) —
  that is an implementation decision for a future milestone, not this
  feasibility task.
- It does not specify which vendor(s) will actually supply each field —
  no vendor has been selected, and §6 of the feasibility report concludes
  none is currently affordable within this project's capital constraints.
- It does not specify how MOM-001's existing experiment configuration
  format would reference a universe snapshot — that is explicitly excluded
  from this task (MOM-001 is not to be modified) and would be a design
  question for a future, explicitly authorised milestone.
