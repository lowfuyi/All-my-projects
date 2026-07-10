"""Plain data records produced by the simulation engine."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class TriggeredEvent:
    month: int
    name: str
    description: str
    trait_key: str


@dataclass
class MonthRecord:
    month: int
    customers: float
    revenue: float
    cogs: float
    fixed_costs: float
    cac_spend: float
    event_costs: float
    net_profit: float
    margin: float
    capital_injection: float
    cash_balance: float
    event_names: List[str] = field(default_factory=list)


@dataclass
class IdeaOutcome:
    idea_id: str
    idea_name: str
    idea_category: str
    outcome: str  # "bankrupt" | "negative_streak" | "success" | "timeout"
    months_survived: int
    failure_streak_threshold: int
    final_cash: float
    months: List[MonthRecord] = field(default_factory=list)
    triggered_event_names: List[str] = field(default_factory=list)


@dataclass
class RootCauseReport:
    idea_id: str
    idea_name: str
    outcome: str
    primary_causes: List[str]
    risk_tags_to_avoid: List[str]
    narrative: str
