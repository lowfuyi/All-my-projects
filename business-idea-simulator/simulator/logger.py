"""Console reporting plus JSON/CSV result logging."""

import csv
import json
from dataclasses import asdict
from pathlib import Path

from .ideas import BusinessIdea
from .models import IdeaOutcome, RootCauseReport


class SimulationLogger:
    def __init__(self, results_dir: str, currency: str):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.currency = currency
        self.master_csv_path = self.results_dir / "master_log.csv"

    def log_idea_start(self, iteration: int, idea: BusinessIdea) -> None:
        print(f"\n{'=' * 70}")
        print(f"Iteration {iteration}: Testing '{idea.name}' ({idea.category})")
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

    def log_final_success(self, iteration: int, idea: BusinessIdea) -> None:
        print(f"\n{'=' * 70}")
        print(
            f"SUCCESS after {iteration} idea(s): '{idea.name}' sustained "
            f"{idea.category} operations to a stable profit streak."
        )
        print(f"{'=' * 70}")

    def log_exhausted(self, max_ideas: int) -> None:
        print(f"\n{'=' * 70}")
        print(f"Reached max-ideas limit ({max_ideas}) without a sustained success.")
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
