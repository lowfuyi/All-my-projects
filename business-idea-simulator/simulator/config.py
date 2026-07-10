"""Global financial and simulation defaults."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SimulationConfig:
    currency: str = "SGD"

    # Financial Framework (rule 1): every test defaults to these values.
    starting_capital: float = 500.0
    monthly_capital_injection: float = 350.0

    # Failure Conditions (rule 4): negative-profit streak length is randomized
    # per idea within this inclusive range to model varying founder patience.
    min_failure_streak: int = 3
    max_failure_streak: int = 6

    # An idea "succeeds" (and the auto-iteration loop stops) after this many
    # consecutive months of positive operating net profit.
    success_streak_months: int = 12

    # Safety cap so a run can never loop forever even if it neither fails
    # nor hits the success streak (reported as outcome "timeout").
    max_months_safety_cap: int = 60

    # Auto-Iteration Loop (rule 5): stop after this many ideas have been
    # tried, win or lose.
    max_ideas: int = 10

    seed: Optional[int] = None
    results_dir: str = "results"
    idea_bank_path: str = "data/idea_bank.json"
