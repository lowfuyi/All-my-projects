"""Console reporting plus JSON/CSV result logging."""

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from .ideas import BusinessIdea
from .models import IdeaOutcome, RootCauseReport
from .validation import GraduationResult


class SimulationLogger:
    def __init__(self, results_dir: str, currency: str):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.currency = currency
        self.master_csv_path = self.results_dir / "master_log.csv"

    def log_idea_start(self, iteration: int, idea: BusinessIdea) -> None:
        print(f"\n{'=' * 70}")
        print(f"Iteration {iteration}: Testing '{idea.name}' ({idea.category})")
        print(idea.description)
        print(f"{'-' * 70}")

    def log_idea_result(self, iteration: int, idea: BusinessIdea, outcome: IdeaOutcome) -> None:
        print(
            f"Outcome: {outcome.outcome.upper()} after {outcome.months_survived} month(s) | "
            f"final cash: {self.currency} {outcome.final_cash:,.2f} | "
            f"failure threshold used: {outcome.failure_streak_threshold} consecutive months"
        )
        event_summary = ", ".join(sorted(set(outcome.triggered_event_names))) or "none"
        print(f"Stress events encountered: {event_summary}")

        self._write_idea_json(iteration, idea, outcome)
        self._write_month_csv(iteration, idea, outcome)
        self._append_master_log(iteration, idea, outcome)

    def log_root_cause(self, report: RootCauseReport) -> None:
        print(f"\nRoot-cause analysis for '{report.idea_name}':")
        for cause in report.primary_causes:
            print(f"  - {cause}")
        if report.risk_tags_to_avoid:
            print(f"  Lessons learned (traits to avoid next pick): {', '.join(report.risk_tags_to_avoid)}")

        path = self.results_dir / f"{report.idea_id}_root_cause.json"
        path.write_text(json.dumps(asdict(report), indent=2))

    def log_next_pick(self, next_idea: BusinessIdea) -> None:
        print(f"\nNext idea selected: '{next_idea.name}' ({next_idea.category})")

    def log_graduation_result(self, idea: BusinessIdea, grad: GraduationResult) -> None:
        print(
            f"\n'{idea.name}' cleared the single-run success bar - validating with "
            f"{grad.trials_run} repeated trials..."
        )
        breakdown = ", ".join(f"{count}x {name}" for name, count in grad.outcome_breakdown.most_common())
        print(f"  Graduation result: {grad.successes}/{grad.trials_run} succeeded ({grad.win_rate:.0%} win rate)")
        print(f"  Trial breakdown: {breakdown}")
        print(f"  {'PASSED' if grad.passed else 'DID NOT PASS'} the graduation threshold.")

        path = self.results_dir / f"{idea.id}_graduation.json"
        payload = {
            "idea": asdict(idea),
            "trials_run": grad.trials_run,
            "successes": grad.successes,
            "win_rate": grad.win_rate,
            "passed": grad.passed,
            "outcome_breakdown": dict(grad.outcome_breakdown),
        }
        path.write_text(json.dumps(payload, indent=2))

    def log_final_winner(self, iteration: int, idea: BusinessIdea, grad: GraduationResult) -> None:
        print(f"\n{'=' * 70}")
        print(
            f"WINNER after {iteration} idea(s): '{idea.name}' ({idea.category})\n"
            f"Validated across {grad.trials_run} repeated trials at a "
            f"{grad.win_rate:.0%} empirical success rate."
        )
        print(idea.description)
        print(f"{'=' * 70}")

        path = self.results_dir / "winner.json"
        path.write_text(
            json.dumps(
                {
                    "idea": asdict(idea),
                    "graduation": {
                        "trials_run": grad.trials_run,
                        "successes": grad.successes,
                        "win_rate": grad.win_rate,
                        "passed": grad.passed,
                    },
                },
                indent=2,
            )
        )

    def log_exhausted_with_best_candidate(
        self, max_ideas: int, best_candidate: Optional[dict]
    ) -> None:
        print(f"\n{'=' * 70}")
        print(f"Reached max-ideas limit ({max_ideas}) without any idea passing graduation.")
        if best_candidate:
            idea = best_candidate["idea"]
            print(
                f"NOT FULLY VALIDATED - strongest candidate observed: '{idea.name}' "
                f"({idea.category}), {best_candidate['win_rate']:.0%} win rate across "
                f"{best_candidate['trials_run']} trials. Treat this as a lead, not a "
                "proven winner."
            )
            path = self.results_dir / "best_candidate_not_validated.json"
            path.write_text(
                json.dumps(
                    {
                        "idea": asdict(idea),
                        "win_rate": best_candidate["win_rate"],
                        "trials_run": best_candidate["trials_run"],
                        "validated": False,
                    },
                    indent=2,
                )
            )
        else:
            print("No idea cleared even the single-run success bar in this run.")
        print(f"{'=' * 70}")

    def _write_idea_json(self, iteration: int, idea: BusinessIdea, outcome: IdeaOutcome) -> None:
        path = self.results_dir / f"{iteration:02d}_{idea.id}.json"
        payload = {
            "iteration": iteration,
            "idea": asdict(idea),
            "outcome": asdict(outcome),
        }
        path.write_text(json.dumps(payload, indent=2))

    def _write_month_csv(self, iteration: int, idea: BusinessIdea, outcome: IdeaOutcome) -> None:
        path = self.results_dir / f"{iteration:02d}_{idea.id}_months.csv"
        with path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "month",
                    "customers",
                    "revenue",
                    "cogs",
                    "fixed_costs",
                    "cac_spend",
                    "event_costs",
                    "net_profit",
                    "margin",
                    "capital_injection",
                    "cash_balance",
                    "events",
                ]
            )
            for m in outcome.months:
                writer.writerow(
                    [
                        m.month,
                        m.customers,
                        m.revenue,
                        m.cogs,
                        m.fixed_costs,
                        m.cac_spend,
                        m.event_costs,
                        m.net_profit,
                        m.margin,
                        m.capital_injection,
                        m.cash_balance,
                        "|".join(m.event_names),
                    ]
                )

    def _append_master_log(self, iteration: int, idea: BusinessIdea, outcome: IdeaOutcome) -> None:
        is_new = not self.master_csv_path.exists()
        with self.master_csv_path.open("a", newline="") as f:
            writer = csv.writer(f)
            if is_new:
                writer.writerow(
                    [
                        "iteration",
                        "idea_id",
                        "idea_name",
                        "category",
                        "outcome",
                        "months_survived",
                        "failure_streak_threshold",
                        "final_cash",
                    ]
                )
            writer.writerow(
                [
                    iteration,
                    idea.id,
                    idea.name,
                    idea.category,
                    outcome.outcome,
                    outcome.months_survived,
                    outcome.failure_streak_threshold,
                    outcome.final_cash,
                ]
            )
