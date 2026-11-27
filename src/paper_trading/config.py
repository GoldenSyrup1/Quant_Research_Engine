"""Loads version-controlled portfolio configurations from
`paper_portfolios/*.json` and constructs the corresponding (empty, funded,
but not yet invested) `PaperPortfolio`.

Loading a configuration never places a trade. A configuration's
`target_allocation` is a declared intent for a future, explicitly
timestamped buy, not a holding -- per PAPER-001 section 6, this module
must not generate holdings or unit quantities until a valid observation
price and valuation timestamp are supplied elsewhere.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .ledger import PaperPortfolio

DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[2] / "paper_portfolios"

REQUIRED_FIELDS = (
    "portfolio_id",
    "version",
    "created_at_utc",
    "mandate",
    "starting_balance_aud",
    "restricted",
    "target_allocation",
)


class ConfigError(Exception):
    pass


def load_portfolio_config(path: Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = [f for f in REQUIRED_FIELDS if f not in config]
    if missing:
        raise ConfigError(f"Portfolio configuration {path} is missing required fields: {missing}")
    weights = [entry["weight"] for entry in config["target_allocation"]]
    if abs(sum(weights) - 1.0) > 1e-9:
        raise ConfigError(
            f"Portfolio configuration {path} target_allocation weights sum to {sum(weights)}, not 1.0"
        )
    return config


def list_configs(config_dir: Optional[Path] = None) -> list:
    config_dir = config_dir or DEFAULT_CONFIG_DIR
    return sorted(config_dir.glob("*.json"))


def build_portfolio(config: dict) -> PaperPortfolio:
    """Construct a funded-but-not-yet-invested PaperPortfolio from a
    loaded configuration. Only the initial cash deposit is recorded; no
    instrument is bought here."""
    return PaperPortfolio(
        portfolio_id=config["portfolio_id"],
        starting_balance=config["starting_balance_aud"],
        restricted=config["restricted"],
    )
