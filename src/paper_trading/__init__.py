"""Deterministic, auditable paper-trading infrastructure (PAPER-001).

No module in this package connects to a broker, moves real money, or
downloads data. Price and distribution observations must be supplied by
the caller; synthetic fixtures used in tests must never be presented as
real market observations.
"""
