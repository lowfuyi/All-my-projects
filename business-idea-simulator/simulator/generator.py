"""Combinatorial idea generator (rule 2: unlimited automatable ideas).

Instead of a fixed idea bank, concrete `BusinessIdea` instances are sampled
at runtime from three axes - a business-model archetype, a niche/vertical,
and a monetization variant - each contributing numeric ranges/deltas that
get combined and perturbed via a shared `random.Random` stream. Given a
seed, the exact same sequence of draws reproduces the exact same ideas,
same as everything else in this codebase.

Archetypes encode `churn` and `net_edge` ranges rather than independent
`churn`/`growth` ranges: `growth = churn + edge`. This makes the customer
dynamics viability rule (growth must exceed churn for a baseline-viable
idea) structurally guaranteed by construction rather than something that
has to be checked after the fact - the mistake that broke every idea in an
earlier version of this bank is no longer expressible.
"""

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from .ideas import BusinessIdea

TRAIT_KEYS = (
    "ad_dependency",
    "market_volatility",
    "capital_intensity",
    "supply_chain_risk",
    "competitive_pressure",
    "regulatory_exposure",
    "customer_concentration",
    "platform_dependency",
)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


@dataclass
class Archetype:
    id: str
    label: str
    category: str
    description_template: str
    fragile: bool
    unit_price: Tuple[float, float]
    customers: Tuple[float, float]
    churn: Tuple[float, float]
    net_edge: Tuple[float, float]
    variance: Tuple[float, float]
    cac: Tuple[float, float]
    cogs_pct: Tuple[float, float]
    fixed_costs: Tuple[float, float]
    risk_traits: Dict[str, Tuple[float, float]]

    @classmethod
    def from_dict(cls, d: dict) -> "Archetype":
        return cls(
            id=d["id"],
            label=d["label"],
            category=d["category"],
            description_template=d["description_template"],
            fragile=d["fragile"],
            unit_price=tuple(d["unit_price"]),
            customers=tuple(d["customers"]),
            churn=tuple(d["churn"]),
            net_edge=tuple(d["net_edge"]),
            variance=tuple(d["variance"]),
            cac=tuple(d["cac"]),
            cogs_pct=tuple(d["cogs_pct"]),
            fixed_costs=tuple(d["fixed_costs"]),
            risk_traits={k: tuple(v) for k, v in d["risk_traits"].items()},
        )


@dataclass
class Niche:
    id: str
    display_name: str
    flavor_phrase: str
    price: float
    cac: float
    cogs_add: float
    fixed: float
    churn_add: float
    risk_traits: Dict[str, float]

    @classmethod
    def from_dict(cls, d: dict) -> "Niche":
        return cls(
            id=d["id"],
            display_name=d["display_name"],
            flavor_phrase=d["flavor_phrase"],
            price=d["price"],
            cac=d["cac"],
            cogs_add=d["cogs_add"],
            fixed=d["fixed"],
            churn_add=d["churn_add"],
            risk_traits=d["risk_traits"],
        )


@dataclass
class MonetizationVariant:
    id: str
    label: str
    flavor_sentence: str
    price: float
    churn_add: float
    edge_add: float
    cogs_add: float
    cac: float
    cust_mult: float
    risk_traits: Dict[str, float]

    @classmethod
    def from_dict(cls, d: dict) -> "MonetizationVariant":
        return cls(
            id=d["id"],
            label=d["label"],
            flavor_sentence=d["flavor_sentence"],
            price=d["price"],
            churn_add=d["churn_add"],
            edge_add=d["edge_add"],
            cogs_add=d["cogs_add"],
            cac=d["cac"],
            cust_mult=d["cust_mult"],
            risk_traits=d["risk_traits"],
        )


class IdeaGenerator:
    def __init__(self, data_dir: str):
        base = Path(data_dir)
        self.archetypes: List[Archetype] = [
            Archetype.from_dict(d) for d in json.loads((base / "archetypes.json").read_text())
        ]
        self.niches: List[Niche] = [
            Niche.from_dict(d) for d in json.loads((base / "niches.json").read_text())
        ]
        self.monetizations: List[MonetizationVariant] = [
            MonetizationVariant.from_dict(d)
            for d in json.loads((base / "monetization.json").read_text())
        ]
        self._archetypes_by_id = {a.id: a for a in self.archetypes}
        self._niches_by_id = {n.id: n for n in self.niches}
        self._monetizations_by_id = {m.id: m for m in self.monetizations}

    def all_archetype_ids(self) -> List[str]:
        return [a.id for a in self.archetypes]

    def all_niche_ids(self) -> List[str]:
        return [n.id for n in self.niches]

    def all_monetization_ids(self) -> List[str]:
        return [m.id for m in self.monetizations]

    def total_combo_count(self) -> int:
        return len(self.archetypes) * len(self.niches) * len(self.monetizations)

    def generate(
        self,
        archetype_id: str,
        niche_id: str,
        monetization_id: str,
        rng: random.Random,
        idx: int,
    ) -> BusinessIdea:
        a = self._archetypes_by_id[archetype_id]
        n = self._niches_by_id[niche_id]
        m = self._monetizations_by_id[monetization_id]

        churn = _clamp(rng.uniform(*a.churn) + n.churn_add + m.churn_add, 0.02, 0.85)
        edge = rng.uniform(*a.net_edge) + m.edge_add
        growth = _clamp(churn + edge, 0.02, 0.95)

        variance = rng.uniform(*a.variance)
        unit_price = rng.uniform(*a.unit_price) * n.price * m.price
        starting_customers = rng.uniform(*a.customers) * m.cust_mult
        cac = rng.uniform(*a.cac) * n.cac * m.cac
        cogs_pct = _clamp(rng.uniform(*a.cogs_pct) + n.cogs_add + m.cogs_add, 0.02, 0.85)
        fixed_costs = rng.uniform(*a.fixed_costs) * n.fixed

        risk_traits = {}
        for trait_key in TRAIT_KEYS:
            base_range = a.risk_traits.get(trait_key, (0.2, 0.4))
            value = rng.uniform(*base_range)
            value *= n.risk_traits.get(trait_key, 1.0)
            value *= m.risk_traits.get(trait_key, 1.0)
            risk_traits[trait_key] = round(_clamp(value, 0.02, 0.97), 3)

        idea_id = f"{a.id}__{n.id}__{m.id}__g{idx}"
        name = f"{n.display_name} {a.label} ({m.label})"
        description = f"{a.description_template.format(niche=n.flavor_phrase)} {m.flavor_sentence}"

        return BusinessIdea(
            id=idea_id,
            name=name,
            category=a.category,
            description=description,
            unit_price=round(unit_price, 2),
            starting_monthly_customers=round(starting_customers, 2),
            customer_growth_rate=round(growth, 4),
            customer_variance=round(variance, 4),
            cac=round(cac, 2),
            churn_rate=round(churn, 4),
            cogs_pct=round(cogs_pct, 4),
            fixed_costs=round(fixed_costs, 2),
            risk_traits=risk_traits,
        )
