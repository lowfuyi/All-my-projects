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

    # An idea clears the single-run success bar after this many consecutive
    # months that are BOTH profitable and above success_min_margin, with cash
    # reaching success_min_cash_multiple x fixed_costs. Raised from an earlier
    # 12-month/no-margin-floor bar: since a "winning" idea here is meant to be
    # taken into real life, a single easy-to-scrape-by pass isn't enough
    # evidence on its own - see graduation_trials/graduation_win_rate_threshold
    # below for the repeated-trial validation layered on top of this.
    success_streak_months: int = 18
    success_min_margin: float = 0.15
    success_min_cash_multiple: float = 3.0

    # Safety cap so a run can never loop forever even if it neither fails
    # nor hits the success streak (reported as outcome "timeout"). Extended
    # alongside success_streak_months so the cap still comfortably absorbs
    # the longer streak requirement.
    max_months_safety_cap: int = 78

    # Auto-Iteration Loop (rule 5): stop after this many ideas have been
    # tried, win or lose.
    max_ideas: int = 10

    # Graduation (repeated-trial validation): once an idea clears the
    # single-run success bar above, it's re-simulated this many more times
    # (fresh capital/RNG each trial) and only crowned the final winner if its
    # empirical win rate clears graduation_win_rate_threshold.
    graduation_trials: int = 40
    graduation_win_rate_threshold: float = 0.80

    # How many candidate archetype/niche/monetization combos the selector
    # samples per pick before scoring and choosing one.
    candidate_batch_size: int = 24

    seed: Optional[int] = None
    results_dir: str = "results"
    data_dir: str = "data"
