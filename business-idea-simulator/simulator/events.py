"""Stress-testing event library (rule 3: dynamically introduce realistic
real-world problems).

Each StressEvent has a monthly base probability that gets scaled up by how
strongly the idea being tested carries the event's associated risk trait -
e.g. an idea with high `ad_dependency` is far more likely to get hit by a
"CAC Spike" event than one that relies on referrals. Once triggered, an
event's effects (revenue/CAC multipliers, extra costs) persist for a random
number of months before wearing off.
"""

import random
from dataclasses import dataclass
from typing import List, Tuple

from .models import TriggeredEvent


@dataclass
class StressEvent:
    name: str
    description: str
    base_probability: float
    trait_key: str
    trait_multiplier_strength: float
    revenue_impact_range: Tuple[float, float]
    cac_impact_range: Tuple[float, float]
    extra_cost_range: Tuple[float, float]
    duration_months_range: Tuple[int, int]


EVENT_LIBRARY: List[StressEvent] = [
    StressEvent(
        name="Ad Platform CAC Spike",
        description="Rising ad auction prices make paid acquisition sharply more expensive.",
        base_probability=0.12,
        trait_key="ad_dependency",
        trait_multiplier_strength=2.0,
        revenue_impact_range=(0.0, 0.0),
        cac_impact_range=(0.3, 0.9),
        extra_cost_range=(0.0, 0.0),
        duration_months_range=(1, 3),
    ),
    StressEvent(
        name="Sudden Market Demand Shift",
        description="Consumer trends move away from the product/service faster than expected.",
        base_probability=0.1,
        trait_key="market_volatility",
        trait_multiplier_strength=2.5,
        revenue_impact_range=(-0.4, -0.1),
        cac_impact_range=(0.0, 0.0),
        extra_cost_range=(0.0, 0.0),
        duration_months_range=(1, 2),
    ),
    StressEvent(
        name="Supplier Price Hike / Shortage",
        description="A key supplier raises prices or runs short, disrupting cost structure.",
        base_probability=0.11,
        trait_key="supply_chain_risk",
        trait_multiplier_strength=2.0,
        revenue_impact_range=(-0.15, 0.0),
        cac_impact_range=(0.0, 0.0),
        extra_cost_range=(30.0, 150.0),
        duration_months_range=(1, 2),
    ),
    StressEvent(
        name="New Competitor Entry",
        description="A well-funded competitor enters the market and undercuts on price or reach.",
        base_probability=0.11,
        trait_key="competitive_pressure",
        trait_multiplier_strength=1.8,
        revenue_impact_range=(-0.25, -0.05),
        cac_impact_range=(0.1, 0.3),
        extra_cost_range=(0.0, 0.0),
        duration_months_range=(2, 4),
    ),
    StressEvent(
        name="Regulatory / Compliance Cost",
        description="New licensing, safety, or compliance requirements add unplanned costs.",
        base_probability=0.06,
        trait_key="regulatory_exposure",
        trait_multiplier_strength=2.5,
        revenue_impact_range=(0.0, 0.0),
        cac_impact_range=(0.0, 0.0),
        extra_cost_range=(50.0, 200.0),
        duration_months_range=(1, 2),
    ),
    StressEvent(
        name="Key Customer Loss",
        description="A disproportionately large customer or account churns out.",
        base_probability=0.08,
        trait_key="customer_concentration",
        trait_multiplier_strength=3.0,
        revenue_impact_range=(-0.3, -0.1),
        cac_impact_range=(0.0, 0.0),
        extra_cost_range=(0.0, 0.0),
        duration_months_range=(1, 2),
    ),
    StressEvent(
        name="Equipment Breakdown",
        description="Essential equipment fails and needs urgent repair or replacement.",
        base_probability=0.08,
        trait_key="capital_intensity",
        trait_multiplier_strength=2.2,
        revenue_impact_range=(-0.1, 0.0),
        cac_impact_range=(0.0, 0.0),
        extra_cost_range=(60.0, 180.0),
        duration_months_range=(1, 1),
    ),
    StressEvent(
        name="Seasonal Demand Dip",
        description="A predictable but painful seasonal lull in buying activity.",
        base_probability=0.15,
        trait_key="market_volatility",
        trait_multiplier_strength=1.0,
        revenue_impact_range=(-0.2, -0.05),
        cac_impact_range=(0.0, 0.0),
        extra_cost_range=(0.0, 0.0),
        duration_months_range=(1, 2),
    ),
    StressEvent(
        name="Viral Demand Spike",
        description="Organic buzz drives a surge of cheap, high-intent demand.",
        base_probability=0.04,
        trait_key="ad_dependency",
        trait_multiplier_strength=1.0,
        revenue_impact_range=(0.2, 0.6),
        cac_impact_range=(-0.2, -0.05),
        extra_cost_range=(0.0, 0.0),
        duration_months_range=(1, 2),
    ),
    StressEvent(
        name="Payment Processor Holds Funds",
        description="A payment processor freezes a portion of working capital pending review.",
        base_probability=0.05,
        trait_key="capital_intensity",
        trait_multiplier_strength=1.5,
        revenue_impact_range=(0.0, 0.0),
        cac_impact_range=(0.0, 0.0),
        extra_cost_range=(40.0, 100.0),
        duration_months_range=(1, 1),
    ),
    StressEvent(
        name="Cash Flow Crisis",
        description="A major one-off liability hits at once - e.g. a lawsuit, theft, lease "
        "default, or emergency repair - large enough to threaten outright bankruptcy.",
        base_probability=0.02,
        trait_key="capital_intensity",
        trait_multiplier_strength=2.5,
        revenue_impact_range=(-0.15, 0.0),
        cac_impact_range=(0.0, 0.0),
        extra_cost_range=(400.0, 900.0),
        duration_months_range=(1, 1),
    ),
]


class StressEventEngine:
    """Rolls new stress events each month and tracks their lingering effects."""

    def __init__(self, rng: random.Random):
        self.rng = rng
        self._active_effects: List[dict] = []

    def roll_new_events(self, idea, month: int) -> List[TriggeredEvent]:
        triggered: List[TriggeredEvent] = []
        for event in EVENT_LIBRARY:
            trait_weight = idea.risk_traits.get(event.trait_key, 0.3)
            probability = event.base_probability * (
                1 + trait_weight * event.trait_multiplier_strength
            )
            probability = min(probability, 0.9)
            if self.rng.random() < probability:
                revenue_delta = self.rng.uniform(*event.revenue_impact_range)
                cac_delta = self.rng.uniform(*event.cac_impact_range)
                extra_cost = self.rng.uniform(*event.extra_cost_range)
                duration = self.rng.randint(*event.duration_months_range)
                self._active_effects.append(
                    {
                        "revenue_delta": revenue_delta,
                        "cac_delta": cac_delta,
                        "extra_cost": extra_cost,
                        "remaining_months": duration,
                    }
                )
                triggered.append(
                    TriggeredEvent(
                        month=month,
                        name=event.name,
                        description=event.description,
                        trait_key=event.trait_key,
                    )
                )
        return triggered

    def apply_active_effects(self) -> Tuple[float, float, float]:
        """Sums this month's cumulative revenue/CAC multipliers and extra
        costs across all currently-active effects, then ages them out."""
        revenue_mult = 0.0
        cac_mult = 0.0
        extra_cost = 0.0
        still_active = []
        for effect in self._active_effects:
            revenue_mult += effect["revenue_delta"]
            cac_mult += effect["cac_delta"]
            extra_cost += effect["extra_cost"]
            effect["remaining_months"] -= 1
            if effect["remaining_months"] > 0:
                still_active.append(effect)
        self._active_effects = still_active
        return revenue_mult, cac_mult, extra_cost
