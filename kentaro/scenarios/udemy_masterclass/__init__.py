"""Synthetic banking scenario and course material for the Udemy Masterclass."""
from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

from kentaro.design.portfolio import migrate_portfolio


SCENARIO_ID = "udemy-masterclass"


def starting_portfolio() -> dict:
    """Return a migrated DesignPortfolio for the fictional banking course case."""
    source = files(__package__).joinpath("customer-risk-intelligence.json")
    return migrate_portfolio(json.loads(source.read_text(encoding="utf-8")))


def odps_fixture(repair: bool = False) -> Path:
    name = "customer-profile-repair.odps.yaml" if repair else "customer-profile.odps.yaml"
    return Path(files(__package__).joinpath(name))
