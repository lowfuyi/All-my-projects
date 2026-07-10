#!/usr/bin/env python3
"""Entry point for the Business Idea Simulator And Stress Test.

Runs the auto-iteration loop (rule 5): generate one idea at a time from
default capital settings, simulate it until it fails or clears the success
bar, and on failure run a root-cause analysis, pick a new idea informed by
the lessons learned, reset capital, and repeat.

Clearing the single-run success bar isn't the end: since a "winning" idea
here is meant to be taken into real life, it's re-simulated `graduation_trials`
more times and only crowned the final winner if it clears
`graduation_win_rate_threshold` empirically. If `--max-ideas` is exhausted
without any idea graduating, the strongest observed candidate is reported,
clearly labeled as not fully validated.
"""

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from simulator.analysis import RootCauseAnalyzer
from simulator.config import SimulationConfig
from simulator.engine import SimulationEngine
from simulator.generator import IdeaGenerator
from simulator.logger import SimulationLogger
from simulator.selector import IdeaSelector
from simulator.validation import GraduationValidator

BASE_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Business Idea Simulator And Stress Test")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for reproducible runs")
    parser.add_argument("--max-ideas", type=int, default=30, help="Stop after this many ideas tried")
    parser.add_argument(
        "--starting-capital", type=float, default=500.0, help="Starting capital (SGD)"
    )
    parser.add_argument(
        "--monthly-injection", type=float, default=350.0, help="Monthly capital injection (SGD)"
    )
    parser.add_argument("--results-dir", type=str, default="results", help="Output directory")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(BASE_DIR / "data"),
        help="Directory containing archetypes.json, niches.json, monetization.json",
    )
    parser.add_argument(
        "--graduation-trials",
        type=int,
        default=100,
        help="Repeated trials used to validate a single-run winner",
    )
    parser.add_argument(
        "--graduation-threshold",
        type=float,
        default=0.95,
        help="Empirical win rate (0-1) required to graduate a candidate to final winner",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = SimulationConfig(
        starting_capital=args.starting_capital,
        monthly_capital_injection=args.monthly_injection,
        max_ideas=args.max_ideas,
        seed=args.seed,
        results_dir=str(BASE_DIR / args.results_dir),
        data_dir=args.data_dir,
        graduation_trials=args.graduation_trials,
        graduation_win_rate_threshold=args.graduation_threshold,
    )

    rng = random.Random(config.seed)
    generator = IdeaGenerator(config.data_dir)

    selector = IdeaSelector(rng, generator, batch_size=config.candidate_batch_size)
    analyzer = RootCauseAnalyzer()
    logger = SimulationLogger(config.results_dir, config.currency)

    print(
        f"Starting capital: {config.currency} {config.starting_capital:,.2f} | "
        f"Monthly injection: {config.currency} {config.monthly_capital_injection:,.2f} | "
        f"Idea pool size: {generator.total_combo_count():,} combos | "
        f"Seed: {config.seed}"
    )

    tried_combos = set()
    risk_tags_to_avoid = []
    best_candidate = None  # {"idea": ..., "win_rate": ..., "trials_run": ...}
    current_idea = selector.select_next(tried_combos, risk_tags_to_avoid)

    for iteration in range(1, config.max_ideas + 1):
        logger.log_idea_start(iteration, current_idea)
        engine = SimulationEngine(config, current_idea, rng)
        outcome = engine.run()
        logger.log_idea_result(iteration, current_idea, outcome)

        if outcome.outcome == "success":
            validator = GraduationValidator(rng, config)
            grad = validator.validate(current_idea)
            logger.log_graduation_result(current_idea, grad)

            if best_candidate is None or grad.win_rate > best_candidate["win_rate"]:
                best_candidate = {
                    "idea": current_idea,
                    "win_rate": grad.win_rate,
                    "trials_run": grad.trials_run,
                }

            if grad.passed:
                logger.log_final_winner(iteration, current_idea, grad)
                return

            report = analyzer.analyze_batch(current_idea, grad.failing_outcomes)
            logger.log_root_cause(report)
            risk_tags_to_avoid = list(
                dict.fromkeys(risk_tags_to_avoid + report.risk_tags_to_avoid)
            )[:5]
        else:
            report = analyzer.analyze(current_idea, outcome)
            logger.log_root_cause(report)
            risk_tags_to_avoid = list(
                dict.fromkeys(risk_tags_to_avoid + report.risk_tags_to_avoid)
            )[:5]

        current_idea = selector.select_next(tried_combos, risk_tags_to_avoid)
        logger.log_next_pick(current_idea)

    logger.log_exhausted_with_best_candidate(config.max_ideas, best_candidate)


if __name__ == "__main__":
    main()
