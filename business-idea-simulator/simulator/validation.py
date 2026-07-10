"""Graduation: repeated-trial validation before crowning a final winner.

A single simulated run clearing the success bar could just be luck. Since
the winning idea here is meant to be taken into real life, this re-runs the
same idea `config.graduation_trials` more times (fresh capital/RNG each
trial, identical to a normal iteration) and only treats it as validated if
its empirical success rate clears `config.graduation_win_rate_threshold`.

Also tracks `avg_months_to_success` (mean months_survived across the trials
that succeeded) so the auto-iteration loop can favour whichever validated
idea gets to a proven, resilient profit fastest, rather than just the first
one that happens to clear the bar.
"""

import random
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional

from .config import SimulationConfig
from .engine import SimulationEngine
from .ideas import BusinessIdea
from .models import IdeaOutcome


@dataclass
class GraduationResult:
    idea_id: str
    trials_run: int
    successes: int
    win_rate: float
    passed: bool
    avg_months_to_success: Optional[float] = None
    outcome_breakdown: Counter = field(default_factory=Counter)
    failing_outcomes: List[IdeaOutcome] = field(default_factory=list)


class GraduationValidator:
    def __init__(self, rng: random.Random, config: SimulationConfig):
        self.rng = rng
        self.config = config

    def validate(self, idea: BusinessIdea) -> GraduationResult:
        cfg = self.config
        breakdown: Counter = Counter()
        failing_outcomes: List[IdeaOutcome] = []
        success_months: List[int] = []
        successes = 0

        for _ in range(cfg.graduation_trials):
            outcome = SimulationEngine(cfg, idea, self.rng).run()
            breakdown[outcome.outcome] += 1
            if outcome.outcome == "success":
                successes += 1
                success_months.append(outcome.months_survived)
            else:
                failing_outcomes.append(outcome)

        win_rate = successes / cfg.graduation_trials if cfg.graduation_trials else 0.0
        avg_months_to_success = (
            sum(success_months) / len(success_months) if success_months else None
        )

        return GraduationResult(
            idea_id=idea.id,
            trials_run=cfg.graduation_trials,
            successes=successes,
            win_rate=win_rate,
            passed=win_rate >= cfg.graduation_win_rate_threshold,
            avg_months_to_success=avg_months_to_success,
            outcome_breakdown=breakdown,
            failing_outcomes=failing_outcomes,
        )
