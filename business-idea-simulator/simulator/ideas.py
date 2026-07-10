"""The `BusinessIdea` shape shared by the generator, engine, and logger.

Concrete ideas are produced at runtime by `simulator.generator.IdeaGenerator`
from a combinatorial space of business-model archetypes, niches, and
monetization variants (see `data/archetypes.json`, `data/niches.json`,
`data/monetization.json`) - there is no fixed idea bank to load.

Automation-only rule: every archetype in that combinatorial space must be
something Claude Code (or an equivalent AI coding agent) can run and operate
end-to-end via code/APIs - content generation, listings, scheduling,
fulfillment routing, customer support - with no required physical presence
or manual human labor. This is enforced by curation of `data/archetypes.json`,
not by runtime validation: when adding a new archetype, only add one that
satisfies this rule.

Recognized trait keys (8): ad_dependency, market_volatility,
capital_intensity, supply_chain_risk, competitive_pressure,
regulatory_exposure, customer_concentration, platform_dependency.
`platform_dependency` covers the risk most central to an AI/API-run
business: a payment processor, ad network, marketplace, or API provider
suspending the account, revoking access, or changing terms without warning.
"""

from dataclasses import dataclass
from typing import Dict


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
