"""Core month-by-month simulation loop for a single business idea.

Runs one idea (rule 2: single-idea focus) from the configured starting
capital until it either goes bankrupt, racks up a random-threshold streak
of consecutive negative operating-profit months, or survives long enough
to be declared a success (rule 4: failure conditions).

Capital injections are cash, not profit: they keep the business alive
longer but do NOT count toward the operating net-profit figure used to
detect the negative-profit failure streak - injecting money into a bad
business model just delays the reckoning, exactly like in real life.
"""

import random

from .config import SimulationConfig
from .events import StressEventEngine
from .ideas import BusinessIdea
from .models import IdeaOutcome, MonthRecord


class SimulationEngine:
    def __init__(self, config: SimulationConfig, idea: BusinessIdea, rng: random.Random):
        self.config = config
        self.idea = idea
        self.rng = rng
        self.event_engine = StressEventEngine(rng)

    def run(self) -> IdeaOutcome:
        cfg = self.config
        idea = self.idea

        cash = cfg.starting_capital
        failure_streak_threshold = self.rng.randint(
            cfg.min_failure_streak, cfg.max_failure_streak
        )
        consecutive_negative = 0
        consecutive_positive = 0
        customers = idea.starting_monthly_customers

        months = []
        triggered_event_names = []
        outcome = "timeout"
        month = 0

        for month in range(1, cfg.max_months_safety_cap + 1):
            cash += cfg.monthly_capital_injection

            customers_before = customers
            growth = self.rng.gauss(idea.customer_growth_rate, idea.customer_variance)
            gross_new_customers = max(0.0, customers_before * growth)
            retained_customers = customers_before * (1 - idea.churn_rate)
            customers = max(0.0, retained_customers + gross_new_customers)

            triggered = self.event_engine.roll_new_events(idea, month)
            triggered_event_names.extend(e.name for e in triggered)
            revenue_mult, cac_mult, event_costs = self.event_engine.apply_active_effects()

            revenue = customers * idea.unit_price * max(0.0, 1 + revenue_mult)
            cogs = revenue * idea.cogs_pct
            cac_spend = gross_new_customers * idea.cac * max(0.0, 1 + cac_mult)
            fixed_costs = idea.fixed_costs

            net_profit = revenue - cogs - cac_spend - fixed_costs - event_costs
            cash += net_profit

            months.append(
                MonthRecord(
                    month=month,
                    customers=round(customers, 2),
                    revenue=round(revenue, 2),
                    cogs=round(cogs, 2),
                    fixed_costs=round(fixed_costs, 2),
                    cac_spend=round(cac_spend, 2),
                    event_costs=round(event_costs, 2),
                    net_profit=round(net_profit, 2),
                    capital_injection=cfg.monthly_capital_injection,
                    cash_balance=round(cash, 2),
                    event_names=[e.name for e in triggered],
                )
            )

            if net_profit < 0:
                consecutive_negative += 1
                consecutive_positive = 0
            else:
                consecutive_positive += 1
                consecutive_negative = 0

            if cash <= 0:
                outcome = "bankrupt"
                break
            if consecutive_negative >= failure_streak_threshold:
                outcome = "negative_streak"
                break
            if consecutive_positive >= cfg.success_streak_months:
                outcome = "success"
                break

        return IdeaOutcome(
            idea_id=idea.id,
            idea_name=idea.name,
            idea_category=idea.category,
            outcome=outcome,
            months_survived=month,
            failure_streak_threshold=failure_streak_threshold,
            final_cash=round(cash, 2),
            months=months,
            triggered_event_names=triggered_event_names,
        )
