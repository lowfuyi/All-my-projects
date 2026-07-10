"""Business idea template definitions and the idea-bank loader.

Each BusinessIdea is a bootstrapped, shoestring-budget concept sized to
survive (or fail) on ~SGD 500 starting capital plus SGD 350/month, not a
venture-scale business. `risk_traits` are 0..1 weights that make certain
stress events more (or less) likely to hit this idea - see events.py.

Recognized trait keys: ad_dependency, market_volatility, capital_intensity,
supply_chain_risk, competitive_pressure, regulatory_exposure,
customer_concentration.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class BusinessIdea:
    id: str
    name: str
    category: str
    description: str
    unit_price: float
    starting_monthly_customers: float
    customer_growth_rate: float
    customer_variance: float
    cac: float
    churn_rate: float
    cogs_pct: float
    fixed_costs: float
    risk_traits: Dict[str, float]

    @classmethod
    def from_dict(cls, d: dict) -> "BusinessIdea":
        return cls(**d)


def load_idea_bank(path: str) -> List[BusinessIdea]:
    raw = json.loads(Path(path).read_text())
    return [BusinessIdea.from_dict(item) for item in raw]
