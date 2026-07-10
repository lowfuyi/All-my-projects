#!/usr/bin/env python3
"""Entry point for the Business Idea Simulator And Stress Test.

Runs the auto-iteration loop (rule 5): simulate one idea at a time from
default capital settings until it fails, run a root-cause analysis, pick a
new idea informed by the lessons learned, reset capital, and repeat - until
an idea reaches a sustained success streak or --max-ideas is hit.
"""

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from simulator.analysis import RootCauseAnalyzer
from simulator.config import SimulationConfig
from simulator.engine import SimulationEngine
from simulator.ideas import load_idea_bank
from simulator.logger import SimulationLogger
from simulator.selector import IdeaSelector

BASE_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Business Idea Simulator And Stress Test")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for reproducible runs")
    parser.add_argument("--max-ideas", type=int, default=10, help="Stop after this many ideas tried")
    parser.add_argument(
        "--starting-capital", type=float, default=500.0, help="Starting capital (SGD)"
    )
    parser.add_argument(
        "--monthly-injection", type=float, default=350.0, help="Monthly capital injection (SGD)"
    )
    parser.add_argument("--results-dir", type=str, default="results", help="Output directory")
    parser.add_argument(
        "--idea-bank",
        type=str,
        default=str(BASE_DIR / "data" / "idea_bank.json"),
        help="Path to the idea bank JSON file",
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
        idea_bank_path=args.idea_bank,
    )

    rng = random.Random(config.seed)
    idea_bank = load_idea_bank(config.idea_bank_path)
    if not idea_bank:
        raise SystemExit(f"No ideas found in idea bank: {config.idea_bank_path}")

    selector = IdeaSelector(rng)
    analyzer = RootCauseAnalyzer()
    logger = SimulationLogger(config.results_dir, config.currency)

    print(
        f"Starting capital: {config.currency} {config.starting_capital:,.2f} | "
        f"Monthly injection: {config.currency} {config.monthly_capital_injection:,.2f} | "
        f"Seed: {config.seed}"
    )

    tried_ids = []
    risk_tags_to_avoid = []
    current_idea = rng.choice(idea_bank)

    for iteration in range(1, config.max_ideas + 1):
        tried_ids.append(current_idea.id)

        logger.log_idea_start(iteration, current_idea)
        engine = SimulationEngine(config, current_idea, rng)
        outcome = engine.run()
        logger.log_idea_result(iteration, current_idea, outcome)

        if outcome.outcome == "success":
            logger.log_final_success(iteration, current_idea)
            return

        report = analyzer.analyze(current_idea, outcome)
        logger.log_root_cause(report)

        risk_tags_to_avoid = list(dict.fromkeys(risk_tags_to_avoid + report.risk_tags_to_avoid))[:5]
        current_idea = selector.select_next(idea_bank, tried_ids, risk_tags_to_avoid)
        logger.log_next_pick(current_idea)

    logger.log_exhausted(config.max_ideas)


if __name__ == "__main__":
    main()
